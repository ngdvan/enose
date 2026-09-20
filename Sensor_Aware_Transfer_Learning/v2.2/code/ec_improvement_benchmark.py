#!/usr/bin/env python3
"""Leakage-safe five-fold improvement benchmarks for the CO/ethylene dataset."""

from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cross_decomposition import PLSRegression
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler, StandardScaler
from xgboost import XGBRegressor

from importlib.util import spec_from_file_location, module_from_spec


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "ec_improvements"


def load_converter():
    spec = spec_from_file_location("ec_converter", ROOT / "split-to-5-lstm-co-ethy.py")
    module = module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def seed_all(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def prepare_cache(data_path: Path, cache: Path, seed: int = 42) -> dict:
    ec = load_converter()
    df, prep = ec.preprocess(ec.load_data(data_path))
    split_map = ec.assign_splits(df["Label"].unique(), seed)
    sequences, targets, groups, folds, offsets = [], [], [], [], []
    for label, group in df.groupby("Label", sort=False):
        values = group[ec.SENSORS].to_numpy(np.float32)
        for offset in (0, 20, 40, 60, 80):
            seq = values[offset:6400 + offset:100]
            if seq.shape == (64, 16):
                sequences.append(seq)
                targets.append(group[ec.TARGETS].iloc[0].to_numpy(np.float32))
                groups.append(int(label))
                folds.append(split_map[int(label)])
                offsets.append(offset)
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, sequences=np.asarray(sequences), targets=np.asarray(targets),
                        groups=np.asarray(groups), folds=np.asarray(folds), offsets=np.asarray(offsets))
    return {**prep, "samples": len(sequences), "cache": str(cache)}


def features(x: np.ndarray, mode: str) -> np.ndarray:
    if mode == "flat":
        return x.reshape(len(x), -1)
    t = np.arange(x.shape[1], dtype=np.float32)
    tc = t - t.mean()
    slope = np.einsum("t,ntc->nc", tc, x) / np.sum(tc ** 2)
    blocks = [x.mean(1), x.std(1), x.min(1), x.max(1), x[:, 0], x[:, -1],
              x[:, -1] - x[:, 0], slope, np.trapezoid(x, axis=1) / (x.shape[1] - 1)]
    if mode == "physics":
        baseline = x[:, :5].mean(1)
        blocks.extend([(x.mean(1) - baseline),
                       (x.mean(1) - baseline) / (np.abs(baseline) + 1e-6),
                       np.diff(x, axis=1).mean(1), np.diff(x, axis=1).std(1)])
    return np.concatenate(blocks, axis=1)


def score(y: np.ndarray, pred: np.ndarray) -> dict:
    out = {}
    for j, gas in enumerate(("CO", "Ethylene")):
        err = np.abs(y[:, j] - pred[:, j])
        rmse = np.sqrt(mean_squared_error(y[:, j], pred[:, j]))
        out[gas] = {"mae": float(err.mean()), "rmse": float(rmse),
                    "r2": float(r2_score(y[:, j], pred[:, j])),
                    "p90_abs": float(np.quantile(err, .9)),
                    "bias": float(np.mean(pred[:, j] - y[:, j])),
                    "nrmse_sd": float(rmse / np.std(y[:, j]))}
    return out


def models(seed: int):
    return {
        "ridge": make_pipeline(StandardScaler(), Ridge(alpha=10.0)),
        "pls": make_pipeline(StandardScaler(), PLSRegression(n_components=12, scale=False, max_iter=1000)),
        "random_forest": RandomForestRegressor(n_estimators=400, min_samples_leaf=2,
                                                max_features=.7, n_jobs=-1, random_state=seed),
        "extra_trees": ExtraTreesRegressor(n_estimators=400, min_samples_leaf=2,
                                            max_features=.8, n_jobs=-1, random_state=seed),
        "xgboost": XGBRegressor(n_estimators=800, max_depth=3, learning_rate=.03,
                                subsample=.8, colsample_bytree=.8, objective="reg:squarederror",
                                n_jobs=-1, random_state=seed),
    }


def classical_cv(data: dict, feature_mode: str, seed: int) -> list[dict]:
    x, y, groups, folds, offsets = (data[k] for k in ("sequences", "targets", "groups", "folds", "offsets"))
    f = features(x, feature_mode)
    rows = []
    for fold in range(1, 6):
        train = folds != fold
        # Primary evaluation has one independent observation per held-out run.
        test = (folds == fold) & (offsets == 0)
        for name, model in models(seed).items():
            started = time.perf_counter()
            model.fit(f[train], y[train])
            pred = np.asarray(model.predict(f[test])).reshape((-1, 2))
            row = {"family": "classical", "features": feature_mode, "model": name,
                   "fold": fold, "train_samples": int(train.sum()), "test_samples": int(test.sum()),
                   "seconds": time.perf_counter() - started, "metrics": score(y[test], pred)}
            rows.append(row)
            print(json.dumps(row))
    return rows


def neural_cv(data: dict, architecture: str, seed: int, epochs: int) -> list[dict]:
    import torch
    from torch import nn
    from torch.utils.data import DataLoader, TensorDataset

    x, y, groups, folds, offsets = (data[k] for k in ("sequences", "targets", "groups", "folds", "offsets"))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    class GRU(nn.Module):
        def __init__(self):
            super().__init__(); self.rnn = nn.GRU(16, 64, 2, batch_first=True, dropout=.2)
            self.head = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 2))
        def forward(self, z): return self.head(self.rnn(z)[0][:, -1])

    class TCN(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(nn.Conv1d(16, 64, 5, padding=2), nn.ReLU(),
                nn.Conv1d(64, 64, 5, padding=4, dilation=2), nn.ReLU(),
                nn.Conv1d(64, 64, 5, padding=8, dilation=4), nn.ReLU())
            self.head = nn.Sequential(nn.AdaptiveAvgPool1d(1), nn.Flatten(), nn.Linear(64, 32),
                                      nn.ReLU(), nn.Linear(32, 2))
        def forward(self, z): return self.head(self.net(z.transpose(1, 2)))

    rows = []
    for fold in range(1, 6):
        outer_train_groups = np.unique(groups[folds != fold])
        rng = np.random.default_rng(seed + fold); rng.shuffle(outer_train_groups)
        val_groups = set(outer_train_groups[:max(1, len(outer_train_groups)//10)].tolist())
        train = (folds != fold) & ~np.isin(groups, list(val_groups))
        val = (folds != fold) & np.isin(groups, list(val_groups)) & (offsets == 0)
        test = (folds == fold) & (offsets == 0)
        sx = RobustScaler().fit(x[train].reshape(-1, 16)); sy = StandardScaler().fit(y[train])
        tx = lambda m: sx.transform(x[m].reshape(-1,16)).reshape((-1,64,16)).astype("float32")
        ty = lambda m: sy.transform(y[m]).astype("float32")
        train_loader = DataLoader(TensorDataset(torch.from_numpy(tx(train)), torch.from_numpy(ty(train))),
                                  batch_size=64, shuffle=True)
        xv, yv = torch.from_numpy(tx(val)).to(device), torch.from_numpy(ty(val)).to(device)
        xt = torch.from_numpy(tx(test)).to(device)
        model = (GRU() if architecture == "gru" else TCN()).to(device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
        loss_fn = nn.HuberLoss(delta=1.0)
        best, best_state, patience = np.inf, None, 20
        started = time.perf_counter()
        for epoch in range(epochs):
            model.train()
            for xb, yb in train_loader:
                xb, yb = xb.to(device), yb.to(device); optimizer.zero_grad(set_to_none=True)
                loss = loss_fn(model(xb), yb); loss.backward(); optimizer.step()
            model.eval()
            with torch.no_grad(): v = float(loss_fn(model(xv), yv).cpu())
            if v < best - 1e-5:
                best, patience = v, 20
                best_state = {k: p.detach().cpu().clone() for k,p in model.state_dict().items()}
            else:
                patience -= 1
                if patience == 0: break
        model.load_state_dict(best_state); model.eval()
        with torch.no_grad(): pred = model(xt).cpu().numpy()
        pred = sy.inverse_transform(pred)
        row = {"family": "neural", "features": "raw_64x16_float32", "model": architecture,
               "fold": fold, "epochs": epoch + 1, "device": str(device),
               "train_samples": int(train.sum()), "test_samples": int(test.sum()),
               "seconds": time.perf_counter() - started, "metrics": score(y[test], pred)}
        rows.append(row); print(json.dumps(row))
    return rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", type=Path, default=ROOT / "ethylene_CO.txt")
    p.add_argument("--cache", type=Path, default=RESULTS / "raw_sequences.npz")
    p.add_argument("--prepare", action="store_true")
    p.add_argument("--classical", choices=("summary", "physics", "flat"))
    p.add_argument("--neural", choices=("gru", "tcn"))
    p.add_argument("--epochs", type=int, default=150)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args(); seed_all(args.seed); RESULTS.mkdir(exist_ok=True)
    if args.prepare or not args.cache.exists():
        print(json.dumps(prepare_cache(args.data, args.cache, args.seed), indent=2))
    data = dict(np.load(args.cache))
    rows = classical_cv(data, args.classical, args.seed) if args.classical else neural_cv(data, args.neural, args.seed, args.epochs)
    path = RESULTS / f"{args.classical or args.neural}_results.json"
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    joblib.dump({"seed": args.seed, "results": rows}, RESULTS / f"{args.classical or args.neural}_results.joblib")


if __name__ == "__main__": main()
