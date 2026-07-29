#!/usr/bin/env python3
"""Train/evaluate on CO/ethylene, then transfer the physics AE to NH3/H2."""

from __future__ import annotations

import argparse
import json
import random
import time
from copy import deepcopy
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold
from sklearn.preprocessing import RobustScaler
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from xgboost import XGBRegressor

import nh3h2_physics_ae_xgboost as nh


ROOT = Path(__file__).resolve().parent
SOURCE_CACHE = ROOT / "ec_improvements" / "raw_sequences.npz"
TARGET_DATA = ROOT / "DATA_H2_NH3.xlsx"
OUT = ROOT / "ec_to_nh3h2_transfer"
MAX_SENSORS = 16
LATENT = 16
PHYS_PER_SENSOR = 37


def seed_all(seed: int) -> None:
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    if torch.backends.cudnn.is_available():
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True


def load_source() -> dict[str, np.ndarray]:
    z = np.load(SOURCE_CACHE)
    x = z["sequences"].astype(np.float32)
    t = np.broadcast_to(np.arange(64, dtype=np.float32), (len(x), 64)).copy()
    return {k: z[k] for k in ("targets", "groups", "folds", "offsets")} | {"sequences": x, "times": t}


def physical_by_sensor(x: np.ndarray, t: np.ndarray) -> np.ndarray:
    flat, _ = nh.physics_features(x, t)
    return flat.reshape(len(x), PHYS_PER_SENSOR, x.shape[2]).transpose(0, 2, 1).astype(np.float32)


class SharedSensorAE(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(1, 32, 5, padding=2), nn.GELU(),
            nn.Conv1d(32, 32, 3, padding=2, dilation=2), nn.GELU(),
            nn.Conv1d(32, 16, 3, padding=4, dilation=4), nn.GELU())
        self.latent = nn.Sequential(nn.Linear(32, 32), nn.GELU(), nn.Linear(32, LATENT))
        self.decoder = nn.Sequential(nn.Linear(LATENT, 64), nn.GELU(), nn.Linear(64, 64))
        self.physics = nn.Sequential(nn.Linear(LATENT, 64), nn.GELU(), nn.Linear(64, PHYS_PER_SENSOR))

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        h = self.conv(x[:, None, :])
        return self.latent(torch.cat([h.mean(2), h.amax(2)], dim=1))

    def forward(self, x: torch.Tensor):
        z = self.encode(x)
        return self.decoder(z), self.physics(z), z


def fit_scalers(x: np.ndarray, p: np.ndarray) -> tuple[RobustScaler, RobustScaler]:
    # One amplitude scaler is deliberately shared across sensor examples; each
    # dataset/fold gets its own training-only fit before using shared weights.
    xs = RobustScaler().fit(x.reshape(-1, 1))
    ps = RobustScaler().fit(p.reshape(-1, PHYS_PER_SENSOR))
    return xs, ps


def transform(x: np.ndarray, p: np.ndarray, xs: RobustScaler, ps: RobustScaler):
    n, steps, channels = x.shape
    xt = xs.transform(x.transpose(0, 2, 1).reshape(-1, 1)).reshape(n, channels, steps)
    pt = ps.transform(p.reshape(-1, PHYS_PER_SENSOR)).reshape(n, channels, PHYS_PER_SENSOR)
    return np.clip(xt, -20, 20).astype(np.float32), np.clip(pt, -20, 20).astype(np.float32)


def train_ae(x: np.ndarray, p: np.ndarray, seed: int, epochs: int,
             initial: dict | None = None) -> SharedSensorAE:
    seed_all(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = SharedSensorAE().to(device)
    if initial is not None: model.load_state_dict(initial)
    xf, pf = x.reshape(-1, 64), p.reshape(-1, PHYS_PER_SENSOR)
    loader = DataLoader(TensorDataset(torch.from_numpy(xf), torch.from_numpy(pf)),
                        batch_size=256, shuffle=True,
                        generator=torch.Generator().manual_seed(seed))
    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-4 if initial else 1e-3,
                                  weight_decay=1e-4)
    for _ in range(epochs):
        model.train()
        for xb, pb in loader:
            xb, pb = xb.to(device), pb.to(device)
            rec, phys, _ = model(xb)
            loss = (nn.functional.huber_loss(rec, xb)
                    + .25 * nn.functional.huber_loss(rec[:, 1:] - rec[:, :-1], xb[:, 1:] - xb[:, :-1])
                    + nn.functional.huber_loss(phys, pb))
            optimizer.zero_grad(set_to_none=True); loss.backward(); optimizer.step()
    return model


def encode(model: SharedSensorAE, x: np.ndarray) -> np.ndarray:
    device = next(model.parameters()).device
    n, channels, _ = x.shape
    flat = x.reshape(-1, 64)
    parts = []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(flat), 1024):
            parts.append(model.encode(torch.from_numpy(flat[start:start + 1024]).to(device)).cpu().numpy())
    z = np.concatenate(parts).reshape(n, channels, LATENT)
    padded = np.zeros((n, MAX_SENSORS, LATENT), dtype=np.float32)
    padded[:, :channels] = z
    return padded.reshape(n, -1)


def pad_physics(p: np.ndarray) -> np.ndarray:
    padded = np.zeros((len(p), MAX_SENSORS, PHYS_PER_SENSOR), dtype=np.float32)
    padded[:, :p.shape[1]] = p
    return padded.reshape(len(p), -1)


def predict_xgb(train_x: np.ndarray, train_y: np.ndarray, test_x: np.ndarray, seed: int) -> np.ndarray:
    out = []
    for j in range(2):
        model = XGBRegressor(n_estimators=500, max_depth=3, learning_rate=.03,
                             min_child_weight=2, subsample=.8, colsample_bytree=.8,
                             objective="reg:squarederror", n_jobs=-1, random_state=seed + j)
        model.fit(train_x, train_y[:, j]); out.append(model.predict(test_x))
    return np.column_stack(out)


def metrics(y: np.ndarray, pred: np.ndarray, names: tuple[str, str]) -> dict:
    result = {}
    for j, name in enumerate(names):
        error = pred[:, j] - y[:, j]
        result[name] = {"mae": float(mean_absolute_error(y[:, j], pred[:, j])),
                        "rmse": float(np.sqrt(mean_squared_error(y[:, j], pred[:, j]))),
                        "r2": float(r2_score(y[:, j], pred[:, j])),
                        "bias": float(error.mean())}
    return result


def evaluate_source(data: dict, physics: np.ndarray, epochs: int, seed: int):
    rows, predictions = [], []
    for fold in range(1, 6):
        train, test = data["folds"] != fold, (data["folds"] == fold) & (data["offsets"] == 0)
        xs, ps = fit_scalers(data["sequences"][train], physics[train])
        xt, pt = transform(data["sequences"][train], physics[train], xs, ps)
        xv, pv = transform(data["sequences"][test], physics[test], xs, ps)
        ae = train_ae(xt, pt, seed + fold, epochs)
        zt, zv = encode(ae, xt), encode(ae, xv)
        reps = {"physics_only": (pad_physics(pt), pad_physics(pv)),
                "source_ae_latent": (zt, zv),
                "source_ae_latent_plus_physics":
                    (np.concatenate([zt, pad_physics(pt)], 1), np.concatenate([zv, pad_physics(pv)], 1))}
        for name, (a, b) in reps.items():
            pred = predict_xgb(a, data["targets"][train], b, seed + fold)
            row = {"domain": "CO/ethylene", "fold": fold, "model": name,
                   "metrics": metrics(data["targets"][test], pred, ("CO", "Ethylene"))}
            rows.append(row); print(json.dumps(row), flush=True)
            predictions.extend({"domain": "CO/ethylene", "fold": fold, "model": name,
                                "group": int(g), "true_1": float(y[0]), "true_2": float(y[1]),
                                "pred_1": float(q[0]), "pred_2": float(q[1])}
                               for g, y, q in zip(data["groups"][test], data["targets"][test], pred))
    # Final source representation for target transfer. All source data are allowed;
    # target folds remain entirely unseen.
    xs, ps = fit_scalers(data["sequences"], physics)
    xa, pa = transform(data["sequences"], physics, xs, ps)
    final = train_ae(xa, pa, seed + 100, epochs)
    return rows, predictions, deepcopy(final.state_dict())


def evaluate_target(data: dict, physics: np.ndarray, source_state: dict, epochs: int, seed: int):
    unique = np.unique(data["groups"])
    fold_map = {}
    for fold, (_, idx) in enumerate(KFold(5, shuffle=True, random_state=seed).split(unique), 1):
        fold_map.update({int(unique[i]): fold for i in idx})
    rows, predictions = [], []
    for fold in range(1, 6):
        train = np.array([fold_map[int(g)] != fold for g in data["groups"]])
        test = np.array([fold_map[int(g)] == fold and o == 0 for g, o in zip(data["groups"], data["offsets"])])
        xs, ps = fit_scalers(data["sequences"][train], physics[train])
        xt, pt = transform(data["sequences"][train], physics[train], xs, ps)
        xv, pv = transform(data["sequences"][test], physics[test], xs, ps)
        frozen = SharedSensorAE().to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))
        frozen.load_state_dict(source_state)
        scratch = train_ae(xt, pt, seed + fold * 10, epochs)
        tuned = train_ae(xt, pt, seed + fold * 10 + 1, max(10, epochs // 2), source_state)
        phys_train, phys_test = pad_physics(pt), pad_physics(pv)
        reps = {"physics_only": (phys_train, phys_test)}
        for prefix, model in (("scratch", scratch), ("frozen_transfer", frozen), ("finetuned_transfer", tuned)):
            a, b = encode(model, xt), encode(model, xv)
            reps[prefix + "_latent"] = (a, b)
            reps[prefix + "_latent_plus_physics"] = (np.concatenate([a, phys_train], 1),
                                                       np.concatenate([b, phys_test], 1))
        for name, (a, b) in reps.items():
            pred = predict_xgb(a, data["targets"][train], b, seed + fold)
            row = {"domain": "NH3/H2 workbook", "fold": fold, "model": name,
                   "metrics": metrics(data["targets"][test], pred, ("Gas A", "Gas B"))}
            rows.append(row); print(json.dumps(row), flush=True)
            predictions.extend({"domain": "NH3/H2 workbook", "fold": fold, "model": name,
                                "group": int(g), "true_1": float(y[0]), "true_2": float(y[1]),
                                "pred_1": float(q[0]), "pred_2": float(q[1])}
                               for g, y, q in zip(data["groups"][test], data["targets"][test], pred))
    return rows, predictions


def summarize(rows: list[dict]) -> dict:
    output = {}
    for domain in sorted({r["domain"] for r in rows}):
        output[domain] = {}
        dr = [r for r in rows if r["domain"] == domain]
        for model in sorted({r["model"] for r in dr}):
            output[domain][model] = {}
            mr = [r for r in dr if r["model"] == model]
            for target in mr[0]["metrics"]:
                output[domain][model][target] = {}
                for metric in ("mae", "rmse", "r2", "bias"):
                    v = np.array([r["metrics"][target][metric] for r in mr])
                    output[domain][model][target][metric] = {"mean": float(v.mean()), "sd": float(v.std(ddof=1))}
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=True)
    seed_all(args.seed); started = time.perf_counter()
    source = load_source(); source_p = physical_by_sensor(source["sequences"], source["times"])
    target = nh.load_windows(TARGET_DATA); target_p = physical_by_sensor(target["sequences"], target["times"])
    source_rows, source_pred, state = evaluate_source(source, source_p, args.epochs, args.seed)
    target_rows, target_pred = evaluate_target(target, target_p, state, args.epochs, args.seed)
    rows, predictions = source_rows + target_rows, source_pred + target_pred
    result = {"experiment": "CO/ethylene pretraining followed by NH3/H2 representation transfer",
              "protocol": {"seed": args.seed, "epochs": args.epochs,
                           "source_exposures": 245, "target_exposures": 35,
                           "source_sensors": 16, "target_sensors": 10,
                           "encoder": "shared sensor-wise temporal AE; 16 latent values per sensor",
                           "transfer": "pretrained AE weights; new XGBoost heads for target gases",
                           "target_mapping_warning": "Workbook does not identify Gas A/B as NH3/H2."},
              "fold_results": rows, "summary": summarize(rows), "predictions": predictions,
              "elapsed_seconds": time.perf_counter() - started}
    (args.output / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    import pandas as pd
    pd.DataFrame(predictions).to_csv(args.output / "predictions.csv", index=False)
    torch.save(state, args.output / "source_pretrained_ae.pt")
    print(json.dumps({"summary": result["summary"], "elapsed_seconds": result["elapsed_seconds"]}, indent=2))


if __name__ == "__main__": main()
