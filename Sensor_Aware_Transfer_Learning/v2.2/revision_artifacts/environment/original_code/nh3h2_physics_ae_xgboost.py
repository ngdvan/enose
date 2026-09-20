#!/usr/bin/env python3
"""Physics-supervised temporal autoencoder + XGBoost on DATA_H2_NH3.xlsx.

The workbook provides 35 independent exposure classes. Five offset windows are used
for outer-training and only offset zero is scored for each held-out exposure.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold
from sklearn.preprocessing import RobustScaler
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from xgboost import XGBRegressor


ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = ROOT / "DATA_H2_NH3.xlsx"
DEFAULT_OUT = ROOT / "nh3h2_physics_ae_xgboost"
SENSORS = [f"feature {i}" for i in range(1, 11)]
TARGETS = ["Gas A", "Gas B"]


def seed_all(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    if torch.backends.cudnn.is_available():
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True


def load_windows(path: Path) -> dict[str, np.ndarray]:
    df = pd.read_excel(path, sheet_name="test")
    required = {"class", "feature time", *SENSORS, *TARGETS}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing workbook columns: {sorted(missing)}")
    if df[list(required)].isna().any().any():
        raise ValueError("Required workbook columns contain missing values")

    sequences, times, targets, groups, offsets = [], [], [], [], []
    for group_id, group in df.groupby("class", sort=True):
        group = group.sort_values("feature time")
        if group[TARGETS].nunique().max() != 1:
            raise ValueError(f"Targets change within class {group_id}")
        values = group[SENSORS].to_numpy(np.float32)
        stamp = group["feature time"].to_numpy(np.float32)
        for offset in (0, 1, 2, 3, 4):
            index = offset + np.arange(64) * 5
            if index[-1] < len(group):
                sequences.append(values[index])
                elapsed = stamp[index] - stamp[index[0]]
                times.append(elapsed)
                targets.append(group[TARGETS].iloc[0].to_numpy(np.float32))
                groups.append(int(group_id))
                offsets.append(offset)
    return {
        "sequences": np.asarray(sequences, dtype=np.float32),
        "times": np.asarray(times, dtype=np.float32),
        "targets": np.asarray(targets, dtype=np.float32),
        "groups": np.asarray(groups, dtype=np.int32),
        "offsets": np.asarray(offsets, dtype=np.int32),
    }


def _linear_slope(x: np.ndarray, t: np.ndarray) -> np.ndarray:
    tc = t - t.mean(axis=1, keepdims=True)
    den = np.sum(tc * tc, axis=1, keepdims=True)
    return np.einsum("nt,ntc->nc", tc, x) / np.maximum(den, 1e-8)


def physics_features(x: np.ndarray, t: np.ndarray) -> tuple[np.ndarray, list[str]]:
    """Return deterministic physical descriptors; shape is samples x features."""
    n, steps, channels = x.shape
    baseline = np.median(x[:, :5], axis=1)
    response = x - baseline[:, None, :]
    scale = np.ptp(response, axis=1) + 1e-6
    dt = np.diff(t, axis=1)
    deriv = np.diff(response, axis=1) / np.maximum(dt[:, :, None], 1e-8)
    second = np.diff(deriv, axis=1) / np.maximum(dt[:, 1:, None], 1e-8)

    whole_slope = _linear_slope(response, t)
    early_slope = _linear_slope(response[:, :16], t[:, :16])
    middle_slope = _linear_slope(response[:, 16:40], t[:, 16:40])
    late_slope = _linear_slope(response[:, 40:], t[:, 40:])
    auc = np.trapezoid(response, x=t[:, :, None], axis=1)
    abs_auc = np.trapezoid(np.abs(response), x=t[:, :, None], axis=1)
    duration = np.maximum(t[:, -1:] - t[:, :1], 1e-8)

    peak_idx = np.argmax(np.abs(response), axis=1)
    peak = np.take_along_axis(response, peak_idx[:, None, :], axis=1)[:, 0]
    time_to_peak = np.take_along_axis(t[:, :, None], peak_idx[:, None, :], axis=1)[:, 0]
    peak_boundary = ((peak_idx == 0) | (peak_idx == steps - 1)).astype(np.float32)

    rise_times, reached_flags = [], []
    signed = response * np.where(peak >= 0, 1.0, -1.0)[:, None, :]
    for fraction in (0.1, 0.5, 0.9):
        crossed = signed >= fraction * np.abs(peak)[:, None, :]
        reached = crossed.any(axis=1)
        first = crossed.argmax(axis=1)
        rise = np.take_along_axis(t[:, :, None], first[:, None, :], axis=1)[:, 0]
        rise = np.where(reached, rise, duration)
        rise_times.append(rise)
        reached_flags.append(reached.astype(np.float32))

    # Stable onset: 8-step window, slope <2% of response range per median time
    # step and MAD <3% of response range, both for three consecutive windows.
    stable_found = np.zeros((n, channels), dtype=np.float32)
    stable_idx = np.full((n, channels), steps - 8, dtype=np.int32)
    median_dt = np.median(np.maximum(dt, 1e-8), axis=1)[:, None]
    slope_threshold = 0.02 * scale / median_dt
    noise_threshold = 0.03 * scale
    condition = np.zeros((n, steps - 7, channels), dtype=bool)
    for end in range(7, steps):
        window = response[:, end - 7:end + 1]
        window_t = t[:, end - 7:end + 1]
        slope = np.abs(_linear_slope(window, window_t))
        med = np.median(window, axis=1)
        mad = np.median(np.abs(window - med[:, None, :]), axis=1)
        condition[:, end - 7] = (slope < slope_threshold) & (mad < noise_threshold)
    for i in range(n):
        for c in range(channels):
            hits = np.convolve(condition[i, :, c].astype(np.int8), np.ones(3, dtype=np.int8), mode="valid")
            valid = np.flatnonzero(hits == 3)
            if len(valid):
                stable_found[i, c] = 1.0
                stable_idx[i, c] = int(valid[0])

    stable_stats = {name: np.empty((n, channels), dtype=np.float32)
                    for name in ("mean", "median", "min", "max", "std")}
    stable_time = np.empty((n, channels), dtype=np.float32)
    for i in range(n):
        for c in range(channels):
            start = int(stable_idx[i, c])
            segment = response[i, start:, c]
            stable_stats["mean"][i, c] = segment.mean()
            stable_stats["median"][i, c] = np.median(segment)
            stable_stats["min"][i, c] = segment.min()
            stable_stats["max"][i, c] = segment.max()
            stable_stats["std"][i, c] = segment.std()
            stable_time[i, c] = t[i, start]
    stable_range = stable_stats["max"] - stable_stats["min"]
    stable_cv = stable_stats["std"] / (np.abs(stable_stats["mean"]) + 1e-6)
    overshoot = (peak - stable_stats["median"]) / (np.abs(stable_stats["median"]) + 1e-6)

    arrays = [
        response[:, 0], response[:, -1], response[:, -1] - response[:, 0],
        whole_slope, early_slope, middle_slope, late_slope, late_slope - early_slope,
        np.mean(np.abs(deriv), axis=1), np.max(np.abs(deriv), axis=1),
        np.mean(np.abs(second), axis=1), np.max(np.abs(second), axis=1),
        auc, abs_auc, auc / duration, response.min(axis=1), response.max(axis=1), peak,
        time_to_peak, peak_boundary, *rise_times, *reached_flags,
        stable_found, stable_time, stable_stats["mean"], stable_stats["median"],
        stable_stats["min"], stable_stats["max"], stable_range, stable_stats["std"],
        stable_cv, overshoot, deriv.std(axis=1),
    ]
    base_names = [
        "initial", "final", "delta", "slope_all", "slope_early", "slope_middle",
        "slope_late", "slope_change", "mean_abs_derivative", "max_abs_derivative",
        "mean_abs_curvature", "max_abs_curvature", "auc", "abs_auc", "auc_per_time",
        "minimum", "maximum", "signed_peak", "time_to_peak", "peak_at_boundary",
        "rise_time_10", "rise_time_50", "rise_time_90", "reached_10", "reached_50",
        "reached_90", "stable_found", "stable_onset", "stable_mean", "stable_median",
        "stable_min", "stable_max", "stable_range", "stable_std", "stable_cv",
        "overshoot", "derivative_std",
    ]
    names = [f"sensor_{c + 1}_{name}" for name in base_names for c in range(channels)]
    result = np.concatenate(arrays, axis=1).astype(np.float32)
    result = np.nan_to_num(result, nan=0.0, posinf=1e6, neginf=-1e6)
    return result, names


class PhysicsAE(nn.Module):
    def __init__(self, channels: int, physics_dim: int, latent_dim: int, supervised: bool):
        super().__init__()
        self.supervised = supervised
        self.encoder_conv = nn.Sequential(
            nn.Conv1d(channels, 64, 5, padding=2), nn.GELU(),
            nn.Conv1d(64, 64, 3, padding=2, dilation=2), nn.GELU(),
            nn.Conv1d(64, 32, 3, padding=4, dilation=4), nn.GELU(),
        )
        self.to_latent = nn.Sequential(nn.Linear(64, 64), nn.GELU(), nn.Linear(64, latent_dim))
        self.decoder = nn.Sequential(nn.Linear(latent_dim, 256), nn.GELU(), nn.Linear(256, 64 * channels))
        self.physics_head = nn.Sequential(nn.Linear(latent_dim, 128), nn.GELU(),
                                          nn.Linear(128, physics_dim)) if supervised else None
        self.channels = channels

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        h = self.encoder_conv(x.transpose(1, 2))
        pooled = torch.cat([h.mean(dim=2), h.amax(dim=2)], dim=1)
        return self.to_latent(pooled)

    def forward(self, x: torch.Tensor):
        z = self.encode(x)
        reconstruction = self.decoder(z).reshape(-1, 64, self.channels)
        physics = self.physics_head(z) if self.physics_head is not None else None
        return reconstruction, physics, z


def ae_loss(model: PhysicsAE, x: torch.Tensor, p: torch.Tensor, supervised: bool) -> torch.Tensor:
    reconstruction, predicted_physics, _ = model(x)
    rec = nn.functional.huber_loss(reconstruction, x)
    derivative = nn.functional.huber_loss(reconstruction[:, 1:] - reconstruction[:, :-1],
                                           x[:, 1:] - x[:, :-1])
    physics = nn.functional.huber_loss(predicted_physics, p) if supervised else x.new_tensor(0.0)
    return rec + 0.25 * derivative + physics


def train_once(x: np.ndarray, p: np.ndarray, supervised: bool, seed: int, epochs: int,
               val: tuple[np.ndarray, np.ndarray] | None = None) -> tuple[PhysicsAE, int, float]:
    seed_all(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = PhysicsAE(x.shape[2], p.shape[1], 32, supervised).to(device)
    loader = DataLoader(TensorDataset(torch.from_numpy(x), torch.from_numpy(p)),
                        batch_size=32, shuffle=True,
                        generator=torch.Generator().manual_seed(seed))
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    best_state, best_epoch, best_loss, stale = None, epochs, math.inf, 0
    for epoch in range(1, epochs + 1):
        model.train()
        for xb, pb in loader:
            xb, pb = xb.to(device), pb.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = ae_loss(model, xb, pb, supervised)
            loss.backward()
            optimizer.step()
        if val is not None:
            model.eval()
            with torch.no_grad():
                xv = torch.from_numpy(val[0]).to(device)
                pv = torch.from_numpy(val[1]).to(device)
                current = float(ae_loss(model, xv, pv, supervised).cpu())
            if current < best_loss - 1e-5:
                best_loss, best_epoch = current, epoch
                best_state, stale = deepcopy(model.state_dict()), 0
            else:
                stale += 1
                if stale >= 25:
                    break
    if best_state is not None:
        model.load_state_dict(best_state)
    return model, best_epoch, best_loss


def encode(model: PhysicsAE, x: np.ndarray) -> np.ndarray:
    device = next(model.parameters()).device
    model.eval()
    output = []
    with torch.no_grad():
        for start in range(0, len(x), 256):
            output.append(model.encode(torch.from_numpy(x[start:start + 256]).to(device)).cpu().numpy())
    return np.concatenate(output).astype(np.float32)


def fit_ae_for_fold(x: np.ndarray, p: np.ndarray, groups: np.ndarray, supervised: bool,
                    seed: int, max_epochs: int) -> tuple[PhysicsAE, int, float]:
    unique = np.unique(groups)
    rng = np.random.default_rng(seed)
    val_groups = rng.choice(unique, size=max(1, len(unique) // 5), replace=False)
    val_mask = np.isin(groups, val_groups)
    _, best_epoch, val_loss = train_once(x[~val_mask], p[~val_mask], supervised, seed,
                                         max_epochs, (x[val_mask], p[val_mask]))
    final_model, _, _ = train_once(x, p, supervised, seed + 1000, best_epoch, None)
    return final_model, best_epoch, val_loss


def xgb_predict(train_x: np.ndarray, train_y: np.ndarray, test_x: np.ndarray, seed: int) -> np.ndarray:
    predictions = []
    for target in range(train_y.shape[1]):
        model = XGBRegressor(n_estimators=500, max_depth=3, learning_rate=0.03,
                             min_child_weight=2, subsample=0.8, colsample_bytree=0.8,
                             reg_lambda=1.0, objective="reg:squarederror", n_jobs=-1,
                             random_state=seed + target)
        model.fit(train_x, train_y[:, target])
        predictions.append(model.predict(test_x))
    return np.column_stack(predictions)


def metrics(y: np.ndarray, prediction: np.ndarray) -> dict:
    result = {}
    for j, gas in enumerate(TARGETS):
        residual = prediction[:, j] - y[:, j]
        absolute = np.abs(residual)
        result[gas] = {
            "mae": float(mean_absolute_error(y[:, j], prediction[:, j])),
            "rmse": float(np.sqrt(mean_squared_error(y[:, j], prediction[:, j]))),
            "r2": float(r2_score(y[:, j], prediction[:, j])),
            "bias": float(residual.mean()),
            "p90_abs": float(np.quantile(absolute, 0.9)),
        }
    return result


def pooled_and_bootstrap(predictions: list[dict], seed: int, draws: int = 10000) -> tuple[dict, dict]:
    frame = pd.DataFrame(predictions).sort_values(["model", "group"])
    pooled = {}
    for name, part in frame.groupby("model"):
        truth = part[["true_gas_a", "true_gas_b"]].to_numpy()
        estimate = part[["pred_gas_a", "pred_gas_b"]].to_numpy()
        pooled[name] = metrics(truth, estimate)

    control = frame[frame["model"] == "physics_only"].set_index("group").sort_index()
    comparisons = {}
    rng = np.random.default_rng(seed + 9000)
    groups = control.index.to_numpy()
    indices = rng.integers(0, len(groups), size=(draws, len(groups)))
    for name in sorted(set(frame["model"]) - {"physics_only"}):
        candidate = frame[frame["model"] == name].set_index("group").loc[groups]
        comparisons[name] = {}
        for gas, truth_col, pred_col in (
            ("Gas A", "true_gas_a", "pred_gas_a"), ("Gas B", "true_gas_b", "pred_gas_b")
        ):
            truth = control[truth_col].to_numpy()
            control_error = np.abs(control[pred_col].to_numpy() - truth)
            candidate_error = np.abs(candidate[pred_col].to_numpy() - truth)
            paired = candidate_error - control_error
            boot = paired[indices].mean(axis=1)
            comparisons[name][gas] = {
                "mae_difference_candidate_minus_physics": float(paired.mean()),
                "paired_bootstrap_95_ci": [float(np.quantile(boot, 0.025)),
                                            float(np.quantile(boot, 0.975))],
                "bootstrap_probability_candidate_better": float(np.mean(boot < 0)),
                "bootstrap_draws": draws,
            }
    return pooled, comparisons


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--epochs", type=int, default=200)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    seed_all(args.seed)
    data = load_windows(args.data)
    physical, feature_names = physics_features(data["sequences"], data["times"])
    unique_groups = np.unique(data["groups"])
    splitter = KFold(n_splits=5, shuffle=True, random_state=args.seed)
    group_fold = {}
    for fold, (_, test_index) in enumerate(splitter.split(unique_groups), start=1):
        for group in unique_groups[test_index]:
            group_fold[int(group)] = fold

    fold_rows, predictions = [], []
    started_all = time.perf_counter()
    for fold in range(1, 6):
        train = np.array([group_fold[int(g)] != fold for g in data["groups"]])
        test = np.array([(group_fold[int(g)] == fold and o == 0)
                         for g, o in zip(data["groups"], data["offsets"])])
        sensor_scaler = RobustScaler().fit(data["sequences"][train].reshape(-1, len(SENSORS)))
        x_train = sensor_scaler.transform(data["sequences"][train].reshape(-1, len(SENSORS))).reshape(-1, 64, len(SENSORS)).astype(np.float32)
        x_test = sensor_scaler.transform(data["sequences"][test].reshape(-1, len(SENSORS))).reshape(-1, 64, len(SENSORS)).astype(np.float32)

        physics_scaler = RobustScaler().fit(physical[train])
        p_train = np.clip(physics_scaler.transform(physical[train]), -20, 20).astype(np.float32)
        p_test = np.clip(physics_scaler.transform(physical[test]), -20, 20).astype(np.float32)
        nonconstant = np.ptp(p_train, axis=0) > 1e-8
        p_train, p_test = p_train[:, nonconstant], p_test[:, nonconstant]

        ordinary, ordinary_epoch, ordinary_val = fit_ae_for_fold(
            x_train, p_train, data["groups"][train], False, args.seed + fold * 10, args.epochs)
        supervised, supervised_epoch, supervised_val = fit_ae_for_fold(
            x_train, p_train, data["groups"][train], True, args.seed + fold * 10 + 1, args.epochs)
        ordinary_train, ordinary_test = encode(ordinary, x_train), encode(ordinary, x_test)
        supervised_train, supervised_test = encode(supervised, x_train), encode(supervised, x_test)

        representations = {
            "physics_only": (p_train, p_test),
            "ordinary_ae_latent": (ordinary_train, ordinary_test),
            "physics_supervised_ae_latent": (supervised_train, supervised_test),
            "physics_supervised_ae_latent_plus_physics":
                (np.concatenate([supervised_train, p_train], axis=1),
                 np.concatenate([supervised_test, p_test], axis=1)),
        }
        for name, (train_rep, test_rep) in representations.items():
            pred = xgb_predict(train_rep, data["targets"][train], test_rep, args.seed + fold)
            row = {"fold": fold, "model": name, "train_windows": int(train.sum()),
                   "test_exposures": int(test.sum()), "metrics": metrics(data["targets"][test], pred)}
            fold_rows.append(row)
            predictions.extend({"fold": fold, "model": name, "group": int(group),
                                "true_gas_a": float(true[0]), "true_gas_b": float(true[1]),
                                "pred_gas_a": float(estimate[0]), "pred_gas_b": float(estimate[1])}
                               for group, true, estimate in zip(data["groups"][test], data["targets"][test], pred))
            print(json.dumps(row), flush=True)
        fold_rows[-1]["ae_training"] = {
            "ordinary_best_epoch": ordinary_epoch, "ordinary_validation_loss": ordinary_val,
            "supervised_best_epoch": supervised_epoch, "supervised_validation_loss": supervised_val,
        }

    summary = {}
    for name in sorted({row["model"] for row in fold_rows}):
        subset = [row for row in fold_rows if row["model"] == name]
        summary[name] = {}
        for gas in TARGETS:
            summary[name][gas] = {}
            for metric in ("mae", "rmse", "r2", "bias", "p90_abs"):
                values = np.asarray([row["metrics"][gas][metric] for row in subset])
                summary[name][gas][metric] = {"mean": float(values.mean()), "sd": float(values.std(ddof=1))}

    pooled, paired_comparisons = pooled_and_bootstrap(predictions, args.seed)
    result = {
        "experiment": "NH3/H2 physics-supervised AE + XGBoost",
        "target_mapping_warning": "Workbook identifies concentrations only as Gas A and Gas B; NH3/H2 order is not asserted.",
        "protocol": {
            "independent_exposures": int(len(unique_groups)), "outer_folds": 5,
            "training_augmentation": "five offsets (0..4 rows), stride 5, 64 timesteps",
            "test_sampling": "offset 0 only", "seed": args.seed, "max_ae_epochs": args.epochs,
            "validation_scope": "held-out mixture combinations in the same workbook; not independent sessions/devices",
        },
        "data": {"workbook": str(args.data), "sensor_count": len(SENSORS),
                 "windows": int(len(data["sequences"])), "physics_features": int(len(feature_names)),
                 "target_ranges": {TARGETS[j]: [float(data["targets"][:, j].min()),
                                                 float(data["targets"][:, j].max())] for j in range(2)}},
        "fold_results": fold_rows, "summary": summary, "pooled_metrics": pooled,
        "paired_bootstrap_vs_physics_only": paired_comparisons,
        "predictions": predictions, "feature_names": feature_names,
        "elapsed_seconds": time.perf_counter() - started_all,
    }
    (args.output / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    pd.DataFrame(predictions).to_csv(args.output / "predictions.csv", index=False)
    print(json.dumps({"summary": summary, "elapsed_seconds": result["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
