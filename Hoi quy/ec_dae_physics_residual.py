#!/usr/bin/env python3
"""Nested-CV denoising-AE physics features and residual XGBoost benchmark."""
from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

import numpy as np
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import RobustScaler
from xgboost import XGBRegressor

import ec_improvement_benchmark as bench

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "ec_dae_physics_residual"


def seed_all(seed: int) -> None:
    import torch
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)


def xgb(seed: int, residual: bool = False) -> XGBRegressor:
    return XGBRegressor(
        n_estimators=200 if residual else 500, max_depth=2 if residual else 3,
        learning_rate=.02 if residual else .03, subsample=.8, colsample_bytree=.8,
        min_child_weight=3 if residual else 1, reg_lambda=2 if residual else 1,
        objective="reg:squarederror", tree_method="hist", max_bin=128,
        n_jobs=-1, random_state=seed,
    )


class DAEWrapper:
    def __init__(self, seed: int, epochs: int): self.seed, self.epochs = seed, epochs

    def fit(self, x: np.ndarray) -> "DAEWrapper":
        import torch
        from torch import nn
        from torch.utils.data import DataLoader, TensorDataset
        seed_all(self.seed); self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.scaler = RobustScaler().fit(x.reshape(-1, 16))
        clean = self.scaler.transform(x.reshape(-1, 16)).reshape(x.shape).astype("float32")

        class DAE(nn.Module):
            def __init__(self):
                super().__init__()
                self.encoder = nn.Sequential(nn.Flatten(), nn.Linear(64 * 16, 256), nn.ReLU(),
                                             nn.Linear(256, 64), nn.ReLU())
                self.decoder = nn.Sequential(nn.Linear(64, 256), nn.ReLU(), nn.Linear(256, 64 * 16))
            def forward(self, z): return self.decoder(self.encoder(z)).reshape(-1, 64, 16)

        self.model = DAE().to(self.device)
        loader = DataLoader(TensorDataset(torch.from_numpy(clean)), batch_size=64, shuffle=True)
        opt = torch.optim.AdamW(self.model.parameters(), lr=1e-3, weight_decay=1e-4)
        generator = torch.Generator(device=self.device); generator.manual_seed(self.seed + 991)
        self.loss_history = []
        for _ in range(self.epochs):
            self.model.train(); total = count = 0
            for (xb,) in loader:
                xb = xb.to(self.device); opt.zero_grad(set_to_none=True)
                # Calibration-like corruption: white noise, channel baseline/gain drift,
                # and occasional complete-channel dropout.
                noisy = xb + .05 * torch.randn(xb.shape, generator=generator, device=self.device)
                noisy = noisy * (1 + .02 * torch.randn((len(xb), 1, 16), generator=generator, device=self.device))
                noisy = noisy + .03 * torch.randn((len(xb), 1, 16), generator=generator, device=self.device)
                mask = torch.rand((len(xb), 1, 16), generator=generator, device=self.device) < .02
                noisy = torch.where(mask, torch.zeros_like(noisy), noisy)
                pred = self.model(noisy); loss = torch.mean((pred - xb) ** 2)
                loss.backward(); nn.utils.clip_grad_norm_(self.model.parameters(), 5); opt.step()
                total += float(loss.detach()) * len(xb); count += len(xb)
            self.loss_history.append(total / count)
        return self

    def transform(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        import torch
        scaled = self.scaler.transform(x.reshape(-1, 16)).reshape(x.shape).astype("float32")
        self.model.eval()
        parts = []
        with torch.no_grad():
            for start in range(0, len(x), 256):
                parts.append(self.model(torch.from_numpy(scaled[start:start + 256]).to(self.device)).cpu().numpy())
        den_scaled = np.concatenate(parts)
        den = self.scaler.inverse_transform(den_scaled.reshape(-1, 16)).reshape(x.shape).astype("float32")
        reconstruction_error = np.mean(np.abs(den_scaled - scaled), axis=1)
        return den, reconstruction_error.astype("float32")


def representations(x: np.ndarray, dae: DAEWrapper) -> dict[str, np.ndarray]:
    den, recon_error = dae.transform(x)
    raw = bench.features(x, "physics").astype("float32")
    denf = bench.features(den, "physics").astype("float32")
    return {
        "raw_physics": raw,
        "denoised_physics": denf,
        "hybrid_physics": np.concatenate([raw, denf, raw - denf, recon_error], axis=1),
    }


def meta_features(rep: np.ndarray, base_pred: np.ndarray) -> np.ndarray:
    return np.concatenate([rep, np.asarray(base_pred).reshape(-1, 2)], axis=1)


def choose_shrinkage(meta: np.ndarray, residual: np.ndarray, base: np.ndarray,
                     y: np.ndarray, groups: np.ndarray, seed: int) -> list[float]:
    candidates = np.asarray([0., .25, .5, .75, 1.], dtype=float)
    correction = np.zeros_like(residual)
    splitter = GroupKFold(n_splits=3)
    for k, (tr, va) in enumerate(splitter.split(meta, residual, groups)):
        for gas in range(2):
            m = xgb(seed + 700 + 10 * k + gas, residual=True).fit(meta[tr], residual[tr, gas])
            correction[va, gas] = m.predict(meta[va])
    alpha = []
    for gas in range(2):
        errors = [np.mean(np.abs(y[:, gas] - (base[:, gas] + a * correction[:, gas]))) for a in candidates]
        alpha.append(float(candidates[int(np.argmin(errors))]))
    return alpha


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--cache", type=Path, default=ROOT / "ec_improvements" / "raw_sequences.npz")
    p.add_argument("--output", type=Path, default=OUT / "results.json")
    p.add_argument("--dae-epochs", type=int, default=100)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args(); OUT.mkdir(exist_ok=True)
    d = dict(np.load(args.cache)); x, y, groups, folds, offsets = (d[k] for k in
        ("sequences", "targets", "groups", "folds", "offsets"))
    rows = []
    for fold in range(1, 6):
        started = time.perf_counter(); outer_train = folds != fold
        meta_mask = outer_train & (offsets == 0); test = (folds == fold) & (offsets == 0)
        meta_ids = np.flatnonzero(meta_mask); test_ids = np.flatnonzero(test)
        oof_base = np.zeros((len(meta_ids), 2), dtype=float)
        oof_hybrid = None
        inner = GroupKFold(n_splits=3)
        for inner_fold, (itr_local, iva_local) in enumerate(inner.split(meta_ids, y[meta_ids], groups[meta_ids])):
            inner_train_groups = groups[meta_ids[itr_local]]
            inner_train = outer_train & np.isin(groups, inner_train_groups)
            iva_ids = meta_ids[iva_local]
            dae_i = DAEWrapper(args.seed + 1000 * fold + inner_fold, args.dae_epochs).fit(x[inner_train])
            rep_train = representations(x[inner_train], dae_i)["hybrid_physics"]
            rep_val = representations(x[iva_ids], dae_i)["hybrid_physics"]
            base_i = xgb(args.seed + 100 * fold + inner_fold).fit(rep_train, y[inner_train])
            pred_i = base_i.predict(rep_val)
            oof_base[iva_local] = pred_i
            if oof_hybrid is None: oof_hybrid = np.zeros((len(meta_ids), rep_val.shape[1]), np.float32)
            oof_hybrid[iva_local] = rep_val

        residual = y[meta_ids] - oof_base
        meta = meta_features(oof_hybrid, oof_base)
        alpha = choose_shrinkage(meta, residual, oof_base, y[meta_ids], groups[meta_ids],
                                 args.seed + 5000 * fold)
        residual_models = [xgb(args.seed + 6000 * fold + gas, residual=True).fit(meta, residual[:, gas])
                           for gas in range(2)]

        dae = DAEWrapper(args.seed + fold, args.dae_epochs).fit(x[outer_train])
        train_rep = representations(x[outer_train], dae)
        test_rep = representations(x[test_ids], dae)
        predictions = {}; fitted = {}
        for name in ("raw_physics", "denoised_physics", "hybrid_physics"):
            model = xgb(args.seed + fold).fit(train_rep[name], y[outer_train])
            fitted[name] = model
            predictions[name] = model.predict(test_rep[name])
        base_test = predictions["hybrid_physics"]
        test_meta = meta_features(test_rep["hybrid_physics"], base_test)
        correction = np.column_stack([m.predict(test_meta) for m in residual_models])
        predictions["hybrid_residual"] = base_test + np.asarray(alpha) * correction

        for name, pred in predictions.items():
            row = {"fold": fold, "model": name, "seed": args.seed, "dae_epochs": args.dae_epochs,
                   "train_samples": int(outer_train.sum()), "test_samples": int(test.sum()),
                   "residual_alpha": alpha if name == "hybrid_residual" else None,
                   "dae_final_train_mse": dae.loss_history[-1], "seconds_fold_total": time.perf_counter() - started,
                   "metrics": bench.score(y[test_ids], pred), "test_predictions": pred.tolist()}
            rows.append(row); print(json.dumps(row))

    summary = {}
    for name in sorted(set(r["model"] for r in rows)):
        rr = [r for r in rows if r["model"] == name]
        summary[name] = {}
        for gas in ("CO", "Ethylene"):
            summary[name][gas] = {}
            for metric in ("mae", "rmse", "r2", "bias", "p90_abs"):
                values = np.asarray([r["metrics"][gas][metric] for r in rr])
                summary[name][gas][metric] = {"mean": float(values.mean()), "sd": float(values.std(ddof=1)),
                                              "folds": values.tolist()}
    result = {"experiment": "dae_physics_residual", "protocol": {
        "outer_folds": 5, "inner_base_oof_folds": 3, "residual_shrinkage_folds": 3,
        "dae_fit_scope": "refit inside every outer and inner training partition",
        "training_offsets": [0, 20, 40, 60, 80], "test_offsets": [0],
        "noise": {"gaussian_sd": .05, "gain_sd": .02, "baseline_sd": .03, "channel_dropout": .02}},
        "rows": rows, "summary": summary}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__": main()
