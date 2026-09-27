#!/usr/bin/env python3
"""Contrastive sensor-aware transfer experiments for both ENose datasets."""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
PROJECT = PACKAGE.parent
BASE_CODE = PROJECT / "Sensor_Aware_Transfer_Learning" / "code"
sys.path.insert(0, str(BASE_CODE))

import same_device_session_transfer as core  # noqa: E402
import co_ethylene_session_transfer as co_study  # noqa: E402


class ContrastiveAutoencoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = core.SensorAwareEncoder()
        self.decoder = nn.Sequential(
            nn.Linear(core.TOKEN, 96), nn.GELU(), nn.Linear(96, core.STEPS)
        )
        self.projector = nn.Sequential(
            nn.Linear(core.N_SENSORS * core.TOKEN, 256),
            nn.BatchNorm1d(256), nn.GELU(), nn.Linear(256, 128),
        )

    def forward(self, x: torch.Tensor, observed: torch.Tensor):
        token = self.encoder(x, observed)
        reconstruction = self.decoder(token).transpose(1, 2)
        projection = self.projector(token.flatten(1))
        return reconstruction, token, projection


def augment(x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """A concentration-preserving view plus its observed-value mask."""
    batch, _, sensors = x.shape
    gain = 1 + 0.02 * torch.randn(batch, 1, sensors, device=x.device)
    baseline = 0.015 * torch.randn(batch, 1, sensors, device=x.device)
    noise = 0.01 * torch.randn_like(x)
    view = x * gain + baseline + noise
    observed = core.random_mask(view)
    return view, observed


def reconstruction_loss(pred: torch.Tensor, target: torch.Tensor,
                        observed: torch.Tensor) -> torch.Tensor:
    hidden = 1 - observed
    masked = ((pred - target).square() * hidden).sum() / hidden.sum().clamp_min(1)
    visible = ((pred - target).square() * observed).sum() / observed.sum()
    return masked + 0.05 * visible


def off_diagonal(x: torch.Tensor) -> torch.Tensor:
    n = x.shape[0]
    return x.flatten()[:-1].view(n - 1, n + 1)[:, 1:].flatten()


def vicreg_loss(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    invariance = nn.functional.mse_loss(a, b)
    a = a - a.mean(0)
    b = b - b.mean(0)
    std_a = torch.sqrt(a.var(0, unbiased=False) + 1e-4)
    std_b = torch.sqrt(b.var(0, unbiased=False) + 1e-4)
    variance = torch.relu(1 - std_a).mean() + torch.relu(1 - std_b).mean()
    denom = max(1, len(a) - 1)
    cov_a = (a.T @ a) / denom
    cov_b = (b.T @ b) / denom
    covariance = (
        off_diagonal(cov_a).square().sum()
        + off_diagonal(cov_b).square().sum()
    ) / a.shape[1]
    return 25 * invariance + 25 * variance + covariance


def ntxent_loss(a: torch.Tensor, b: torch.Tensor,
                temperature: float = 0.1) -> torch.Tensor:
    batch = len(a)
    z = nn.functional.normalize(torch.cat([a, b], dim=0), dim=1)
    logits = z @ z.T / temperature
    logits.fill_diagonal_(-torch.inf)
    labels = torch.cat([
        torch.arange(batch, 2 * batch, device=z.device),
        torch.arange(0, batch, device=z.device),
    ])
    return nn.functional.cross_entropy(logits, labels)


def pretrain(x: np.ndarray, variant: str, epochs: int, seed: int):
    core.seed_all(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = ContrastiveAutoencoder().to(device)
    loader = DataLoader(
        TensorDataset(torch.from_numpy(x)), batch_size=64, shuffle=True,
        drop_last=True, generator=torch.Generator().manual_seed(seed),
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=8e-4, weight_decay=1e-4)
    history = []
    for epoch in range(epochs):
        model.train()
        totals = {"loss": 0.0, "reconstruction": 0.0,
                  "contrastive": 0.0, "sensor_consistency": 0.0}
        count = 0
        for (xb,) in loader:
            xb = xb.to(device)
            view_a, mask_a = augment(xb)
            view_b, mask_b = augment(xb)
            rec_a, token_a, proj_a = model(view_a, mask_a)
            rec_b, token_b, proj_b = model(view_b, mask_b)
            rec = 0.5 * (
                reconstruction_loss(rec_a, xb, mask_a)
                + reconstruction_loss(rec_b, xb, mask_b)
            )
            contrast = (
                vicreg_loss(proj_a, proj_b)
                if variant == "vicreg"
                else ntxent_loss(proj_a, proj_b)
            )
            sensor = nn.functional.mse_loss(token_a, token_b)
            contrast_weight = 0.05 if variant == "vicreg" else 0.15
            loss = rec + contrast_weight * contrast + 0.02 * sensor
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 2.0)
            optimizer.step()
            n = len(xb)
            totals["loss"] += float(loss.detach()) * n
            totals["reconstruction"] += float(rec.detach()) * n
            totals["contrastive"] += float(contrast.detach()) * n
            totals["sensor_consistency"] += float(sensor.detach()) * n
            count += n
        row = {"epoch": epoch + 1}
        row.update({k: v / count for k, v in totals.items()})
        history.append(row)
        if (epoch + 1) % 10 == 0:
            print(json.dumps({"stage": "pretrain", "variant": variant, **row}),
                  flush=True)
    return deepcopy(model.encoder.state_dict()), history


def metric_dict(y: np.ndarray, pred: np.ndarray, gases: list[str],
                target_scale: np.ndarray) -> dict:
    output = {}
    for j, gas in enumerate(gases):
        mae = mean_absolute_error(y[:, j], pred[:, j])
        output[gas] = {
            "mae_ppm": float(mae),
            "rmse_ppm": float(np.sqrt(mean_squared_error(y[:, j], pred[:, j]))),
            "r2": float(r2_score(y[:, j], pred[:, j])),
            "mae_percent_test_mean": float(100 * mae / y[:, j].mean()),
            "mae_percent_full_scale": float(100 * mae / target_scale[j]),
        }
    return output


def prepare_nh3_h2():
    core.N_SENSORS = 20
    core.TARGETS = ["NH3", "H2"]
    core.TARGET_SCALE = np.asarray([500.0, 500.0], np.float32)
    source, audit = core.load_exposures(
        PROJECT / "2407" / "TONG_NH3H2_CHUAN.xlsx"
    )
    pre_idx = np.flatnonzero(source["sessions"] <= 4)
    adapt_idx = np.flatnonzero(source["sessions"] == 5)
    test_idx = np.flatnonzero(source["sessions"] == 6)
    pre_raw, _, _ = core.make_windows(source, pre_idx)
    scaler = core.SensorScaler().fit(pre_raw)
    pre_x = scaler.transform(pre_raw)
    test_raw, test_y, test_groups = core.make_windows(
        source, test_idx, offsets=[0]
    )
    adapt_targets = source["targets"][adapt_idx]

    def select_train(seed: int, budget: int):
        local = core.farthest_subset(adapt_targets, len(np.unique(
            adapt_targets, axis=0)), seed)
        chosen = adapt_idx[local[:budget]]
        raw, y, _ = core.make_windows(source, chosen)
        return scaler.transform(raw), y

    return {
        "dataset": "nh3_h2", "gases": ["NH3", "H2"],
        "scale": core.TARGET_SCALE.copy(), "pre_x": pre_x,
        "test_x": scaler.transform(test_raw), "test_y": test_y,
        "test_groups": test_groups, "budgets": [5, 10, 20, 40, 57],
        "select_train": select_train, "audit": audit,
        "protocol": {
            "pretraining": "sessions 1-4", "adaptation": "session 5",
            "test": "untouched session 6",
        },
    }


def prepare_co_ethylene():
    core.N_SENSORS = 16
    core.TARGETS = ["CO", "Ethylene"]
    core.TARGET_SCALE = np.asarray([533.33, 20.0], np.float32)
    data, audit = co_study.load_data(
        PROJECT / "Hoi quy" / "ec_improvements" / "raw_sequences.npz"
    )
    pre = data["blocks"] <= 3
    adapt_zero = (data["blocks"] == 4) & (data["offsets"] == 0)
    test = (data["blocks"] == 5) & (data["offsets"] == 0)
    scaler = core.SensorScaler().fit(data["x"][pre])
    adapt_y0, adapt_g0 = data["y"][adapt_zero], data["groups"][adapt_zero]

    def select_train(seed: int, budget: int):
        order = co_study.farthest_order(adapt_y0, seed)
        selected = adapt_g0[order[:budget]]
        train = (data["blocks"] == 4) & np.isin(data["groups"], selected)
        return scaler.transform(data["x"][train]), data["y"][train]

    return {
        "dataset": "co_ethylene", "gases": ["CO", "Ethylene"],
        "scale": core.TARGET_SCALE.copy(),
        "pre_x": scaler.transform(data["x"][pre]),
        "test_x": scaler.transform(data["x"][test]),
        "test_y": data["y"][test], "test_groups": data["groups"][test],
        "budgets": [5, 10, 20, 24], "select_train": select_train,
        "audit": audit,
        "protocol": {
            "pretraining": "chronological blocks 1-3",
            "adaptation": "chronological block 4",
            "test": "untouched chronological block 5",
            "warning": "The source has no explicit session identifiers.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=["nh3_h2", "co_ethylene"],
                        required=True)
    parser.add_argument("--variant", choices=["vicreg", "ntxent"], required=True)
    parser.add_argument("--pretrain-epochs", type=int, default=60)
    parser.add_argument("--finetune-epochs", type=int, default=120)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    started = time.perf_counter()
    data = prepare_nh3_h2() if args.dataset == "nh3_h2" else prepare_co_ethylene()
    output = args.output or PACKAGE / "results" / args.dataset / args.variant
    output.mkdir(parents=True, exist_ok=True)

    state, history = pretrain(
        data["pre_x"], args.variant, args.pretrain_epochs, args.seed
    )
    torch.save(state, output / "pretrained_encoder.pt")
    rows, predictions = [], []
    for repeat in range(args.repeats):
        repeat_seed = args.seed + 100 * repeat
        for budget in data["budgets"]:
            train_x, train_y = data["select_train"](repeat_seed, budget)
            for mode, frozen, add in (
                ("frozen_transfer", True, 1),
                ("finetuned_transfer", False, 2),
            ):
                model = core.fit_neural(
                    train_x, train_y, state, frozen, args.finetune_epochs,
                    repeat_seed + budget + add,
                )
                pred = core.predict(model, data["test_x"])
                row = {
                    "repeat": repeat + 1, "seed": repeat_seed,
                    "budget": budget, "model": mode,
                    "metrics": metric_dict(
                        data["test_y"], pred, data["gases"], data["scale"]
                    ),
                }
                rows.append(row)
                print(json.dumps(row), flush=True)
                predictions.extend({
                    "repeat": repeat + 1, "budget": budget, "model": mode,
                    "group": int(group),
                    f"{data['gases'][0]}_true": float(y[0]),
                    f"{data['gases'][1]}_true": float(y[1]),
                    f"{data['gases'][0]}_pred": float(p[0]),
                    f"{data['gases'][1]}_pred": float(p[1]),
                } for group, y, p in zip(
                    data["test_groups"], data["test_y"], pred
                ))
    result = {
        "experiment": f"{args.variant} plus masked reconstruction sensor-aware transfer",
        "dataset": args.dataset, "protocol": data["protocol"],
        "architecture": "temporal CNN + sensor identities + cross-sensor Transformer",
        "objective": {
            "reconstruction": "masked temporal spans and complete sensors",
            "contrastive": args.variant,
            "augmentations": "offset windows, mild gain, baseline drift, noise, masks, sensor dropout",
        },
        "settings": {
            "seed": args.seed, "repeats": args.repeats,
            "pretrain_epochs": args.pretrain_epochs,
            "finetune_epochs": args.finetune_epochs,
            "budgets": data["budgets"],
        },
        "data_audit": data["audit"], "pretraining_history": history,
        "runs": rows, "summary": core.aggregate(rows),
        "elapsed_seconds": time.perf_counter() - started,
    }
    (output / "results.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    pd.DataFrame(predictions).to_csv(output / "predictions.csv", index=False)
    print(json.dumps({"dataset": args.dataset, "variant": args.variant,
                      "elapsed_seconds": result["elapsed_seconds"]}), flush=True)


if __name__ == "__main__":
    main()
