#!/usr/bin/env python3
"""Blocked-time AE-LSTM experiment on ordered CO/ethylene exposure episodes.

This is an exploratory chronology test, not a deployment validation: the public
recording has no independent session/device IDs and the existing raw cache has
already removed joint-zero baseline intervals.  Every outer fold is one
contiguous block of episodes; no model sequence crosses a split boundary.
"""

from __future__ import annotations

import argparse
import json
import random
import time
from copy import deepcopy
from pathlib import Path

import numpy as np
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import RobustScaler, StandardScaler


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "ec_chronological_ae_lstm"
GASES = ("CO", "Ethylene")


def seed_all(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    import torch
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def ordered_episodes(cache: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    d = np.load(cache)
    keep = d["offsets"] == 0
    order = np.argsort(d["groups"][keep])
    return d["sequences"][keep][order], d["targets"][keep][order], d["groups"][keep][order]


def contiguous_runs(mask: np.ndarray) -> list[np.ndarray]:
    ids = np.flatnonzero(mask)
    if not len(ids):
        return []
    cuts = np.flatnonzero(np.diff(ids) != 1) + 1
    return [a for a in np.split(ids, cuts) if len(a)]


def sequence_indices(mask: np.ndarray, length: int) -> np.ndarray:
    rows = []
    for run in contiguous_runs(mask):
        if len(run) >= length:
            rows.extend(run[i - length + 1:i + 1] for i in range(length - 1, len(run)))
    return np.asarray(rows, dtype=np.int64)


def split_masks(n: int, fold: int, folds: int, val_size: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    blocks = np.array_split(np.arange(n), folds)
    test_ids = blocks[fold]
    # Validation is a separate contiguous block next to, but never overlapping,
    # the test interval. Alternate sides to avoid always validating on the future.
    if fold % 2 and test_ids[0] >= val_size:
        val_ids = np.arange(test_ids[0] - val_size, test_ids[0])
    elif test_ids[-1] + val_size < n:
        val_ids = np.arange(test_ids[-1] + 1, test_ids[-1] + 1 + val_size)
    else:
        val_ids = np.arange(test_ids[0] - val_size, test_ids[0])
    test = np.zeros(n, bool); test[test_ids] = True
    val = np.zeros(n, bool); val[val_ids] = True
    train = ~(test | val)
    return train, val, test


def metrics(y: np.ndarray, pred: np.ndarray) -> dict:
    out = {}
    thresholds = (1.0, 0.25)
    for j, gas in enumerate(GASES):
        err = pred[:, j] - y[:, j]
        rmse = float(np.sqrt(mean_squared_error(y[:, j], pred[:, j])))
        dy, dp = np.diff(y[:, j]), np.diff(pred[:, j])
        true_dir = np.where(dy > thresholds[j], 1, np.where(dy < -thresholds[j], -1, 0))
        pred_dir = np.where(dp > thresholds[j], 1, np.where(dp < -thresholds[j], -1, 0))
        changed = true_dir != 0
        out[gas] = {
            "mae": float(np.mean(np.abs(err))), "rmse": rmse,
            "r2": float(r2_score(y[:, j], pred[:, j])), "bias": float(np.mean(err)),
            "p90_abs": float(np.quantile(np.abs(err), .9)),
            "direction_accuracy_all": float(np.mean(pred_dir == true_dir)),
            "direction_accuracy_changed": float(np.mean(pred_dir[changed] == true_dir[changed])) if changed.any() else None,
            "n_changes": int(changed.sum()),
        }
    return out


def train_neural(x, y, train_mask, val_mask, test_mask, seq_len, model_kind, seed, epochs, batch_size):
    import torch
    from torch import nn
    from torch.utils.data import DataLoader, TensorDataset

    seed_all(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    sx = RobustScaler().fit(x[train_mask].reshape(-1, x.shape[-1]))
    sy = StandardScaler().fit(y[train_mask])
    xs = sx.transform(x.reshape(-1, x.shape[-1])).reshape(x.shape).astype(np.float32)
    ys = sy.transform(y).astype(np.float32)
    tr, va, te = (sequence_indices(m, seq_len) for m in (train_mask, val_mask, test_mask))

    class TemporalAE(nn.Module):
        def __init__(self, recurrent: bool):
            super().__init__()
            self.encoder = nn.Sequential(nn.Flatten(), nn.Linear(64 * 16, 256), nn.ReLU(),
                                         nn.Dropout(.1), nn.Linear(256, 32))
            self.decoder = nn.Sequential(nn.Linear(32, 256), nn.ReLU(), nn.Linear(256, 64 * 16))
            self.recurrent = recurrent
            if recurrent:
                self.temporal = nn.LSTM(32, 64, num_layers=1, batch_first=True)
                self.head = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 2))
            else:
                self.head = nn.Sequential(nn.Linear(32, 32), nn.ReLU(), nn.Linear(32, 2))

        def forward(self, z):
            b, s, t, c = z.shape
            latent = self.encoder(z.reshape(b * s, t, c)).reshape(b, s, -1)
            recon = self.decoder(latent.reshape(b * s, -1)).reshape(b, s, t, c)
            state = self.temporal(latent)[0] if self.recurrent else latent
            return self.head(state), recon

    def arrays(idx):
        return torch.from_numpy(xs[idx]), torch.from_numpy(ys[idx])

    train_loader = DataLoader(TensorDataset(*arrays(tr)), batch_size=batch_size, shuffle=True)
    xv, yv = (q.to(device) for q in arrays(va))
    xt, _ = arrays(te); xt = xt.to(device)
    model = TemporalAE(model_kind == "ae_lstm").to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=8e-4, weight_decay=1e-4)
    huber = nn.HuberLoss(delta=1.0)
    best, state, patience = np.inf, None, 30
    started = time.perf_counter()
    for epoch in range(epochs):
        model.train()
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad(set_to_none=True)
            yp, recon = model(xb)
            absolute = huber(yp, yb)
            trend = huber(yp[:, 1:] - yp[:, :-1], yb[:, 1:] - yb[:, :-1])
            loss = absolute + .30 * trend + .10 * torch.mean((recon - xb) ** 2)
            loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 5.0); opt.step()
        model.eval()
        with torch.no_grad():
            yp, recon = model(xv)
            v = float((huber(yp, yv) + .30 * huber(yp[:, 1:] - yp[:, :-1],
                                                   yv[:, 1:] - yv[:, :-1]) +
                       .10 * torch.mean((recon - xv) ** 2)).cpu())
        if v < best - 1e-5:
            best, state, patience = v, deepcopy(model.state_dict()), 30
        else:
            patience -= 1
            if patience == 0:
                break
    model.load_state_dict(state); model.eval()
    with torch.no_grad(): pred = model(xt)[0][:, -1].cpu().numpy()
    pred = sy.inverse_transform(pred)
    target_ids = te[:, -1]
    return {
        "model": model_kind, "epochs": epoch + 1, "best_validation_loss": best,
        "device": str(device), "seconds": time.perf_counter() - started,
        "train_sequences": len(tr), "validation_sequences": len(va), "test_sequences": len(te),
        "test_episode_ids": target_ids.tolist(), "metrics": metrics(y[target_ids], pred),
    }, target_ids, pred


def persistence_result(y, test_mask, seq_len):
    te = sequence_indices(test_mask, seq_len)
    ids = te[:, -1]
    pred = y[ids - 1]
    return {"model": "previous_true_ppm_persistence", "test_sequences": len(ids),
            "test_episode_ids": ids.tolist(), "metrics": metrics(y[ids], pred)}, ids, pred


def aggregate(rows: list[dict], y: np.ndarray) -> dict:
    out = {}
    for model in sorted(set(r["model"] for r in rows)):
        chosen = [r for r in rows if r["model"] == model]
        ids = np.concatenate([np.asarray(r["test_episode_ids"], int) for r in chosen])
        pred = np.concatenate([np.asarray(r["predictions"], float) for r in chosen])
        order = np.argsort(ids)
        pooled = metrics(y[ids[order]], pred[order])
        # Direction comparisons must stay inside each held-out block; otherwise
        # sorting pooled predictions invents four transitions across fold gaps.
        for gas in GASES:
            all_den = sum(max(0, r["test_sequences"] - 1) for r in chosen)
            changed_den = sum(r["metrics"][gas]["n_changes"] for r in chosen)
            pooled[gas]["direction_accuracy_all"] = float(sum(
                r["metrics"][gas]["direction_accuracy_all"] * max(0, r["test_sequences"] - 1)
                for r in chosen) / all_den)
            pooled[gas]["direction_accuracy_changed"] = float(sum(
                r["metrics"][gas]["direction_accuracy_changed"] * r["metrics"][gas]["n_changes"]
                for r in chosen) / changed_den)
            pooled[gas]["n_changes"] = int(changed_den)
        out[model] = {"evaluated_episodes": len(ids), "metrics": pooled}
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--cache", type=Path, default=ROOT / "ec_improvements" / "raw_sequences.npz")
    p.add_argument("--output", type=Path, default=OUT / "results.json")
    p.add_argument("--sequence-length", type=int, default=6)
    p.add_argument("--folds", type=int, default=5)
    p.add_argument("--validation-episodes", type=int, default=14)
    p.add_argument("--epochs", type=int, default=250)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    x, y, groups = ordered_episodes(args.cache)
    rows = []
    for fold in range(args.folds):
        train, val, test = split_masks(len(x), fold, args.folds, args.validation_episodes)
        for kind in ("ae_mlp", "ae_lstm"):
            row, ids, pred = train_neural(x, y, train, val, test, args.sequence_length,
                                          kind, args.seed + fold, args.epochs, args.batch_size)
            row.update({"fold": fold + 1, "train_episodes": int(train.sum()),
                        "validation_episodes": int(val.sum()), "test_episodes": int(test.sum())})
            row["predictions"] = pred.tolist(); rows.append(row); print(json.dumps(row))
        row, ids, pred = persistence_result(y, test, args.sequence_length)
        row.update({"fold": fold + 1, "predictions": pred.tolist()}); rows.append(row); print(json.dumps(row))
    result = {
        "experiment": "chronological_ae_lstm", "seed": args.seed,
        "sequence_length": args.sequence_length, "folds": args.folds,
        "episodes": len(x), "episode_groups": groups.tolist(),
        "protocol_warning": "One recording, no independent session IDs; joint-zero baselines were removed by the source cache.",
        "rows": rows, "aggregate": aggregate(rows, y),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["aggregate"], indent=2))


if __name__ == "__main__":
    main()
