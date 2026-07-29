#!/usr/bin/env python3
"""Transfer a sensor-wise temporal encoder to TONG_NH3H2_CHUAN.xlsx.

All repeats of the same (NH3, H2) pair stay in one outer fold.  This is a
deliberately strict test: no exact test concentration pair occurs in training.
"""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import KFold

import ec_to_nh3h2_transfer as tl


ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = ROOT.parent / "2407" / "TONG_NH3H2_CHUAN.xlsx"
DEFAULT_SOURCE = ROOT / "ec_to_nh3h2_transfer" / "source_pretrained_ae.pt"
DEFAULT_OUT = ROOT / "tong_nh3h2_transfer"
SENSORS = [f"Response{i}" for i in range(1, 21)]
TARGETS = ["NH3", "H2"]


def load_windows(path: Path) -> tuple[dict[str, np.ndarray], dict]:
    df = pd.read_excel(path)
    required = {*SENSORS, *TARGETS, "Combination"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing workbook columns: {sorted(missing)}")
    if df[list(required)].isna().any().any():
        raise ValueError("Required workbook columns contain missing values")

    sequences, times, targets, groups, offsets, pairs = [], [], [], [], [], []
    corrected_rows = 0
    for group_id, group in df.groupby("Combination", sort=True):
        # A few transition rows can carry the next exposure's label.  The modal
        # pair is the exposure label and is determined without sensor values.
        label_counts = Counter(map(tuple, group[TARGETS].to_numpy()))
        label = max(label_counts, key=label_counts.get)
        corrected_rows += len(group) - label_counts[label]
        values = group[SENSORS].to_numpy(np.float32)
        for offset in range(5):
            index = offset + np.arange(64)
            if index[-1] >= len(values):
                continue
            sequences.append(values[index])
            times.append(np.arange(64, dtype=np.float32))
            targets.append(label)
            groups.append(int(group_id))
            offsets.append(offset)
            pairs.append(label)
    data = {
        "sequences": np.asarray(sequences, np.float32),
        "times": np.asarray(times, np.float32),
        "targets": np.asarray(targets, np.float32),
        "groups": np.asarray(groups, np.int32),
        "offsets": np.asarray(offsets, np.int32),
        "pairs": np.asarray(pairs, np.int32),
    }
    audit = {
        "workbook_rows": int(len(df)),
        "exposures": int(df["Combination"].nunique()),
        "unique_concentration_pairs": int(len(set(map(tuple, data["pairs"])))),
        "label_transition_rows_corrected": int(corrected_rows),
        "windows": int(len(data["sequences"])),
    }
    return data, audit


def pair_folds(data: dict, seed: int) -> np.ndarray:
    unique_pairs = np.unique(data["pairs"], axis=0)
    mapping = {}
    for fold, (_, test_idx) in enumerate(
        KFold(5, shuffle=True, random_state=seed).split(unique_pairs), 1
    ):
        mapping.update({tuple(unique_pairs[i]): fold for i in test_idx})
    return np.asarray([mapping[tuple(pair)] for pair in data["pairs"]], np.int32)


def encode(model: tl.SharedSensorAE, x: np.ndarray) -> np.ndarray:
    """Encode every target sensor without the source script's 16-sensor pad."""
    device = next(model.parameters()).device
    n, channels, steps = x.shape
    flat = x.reshape(-1, steps)
    parts = []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(flat), 1024):
            batch = torch.from_numpy(flat[start:start + 1024]).to(device)
            parts.append(model.encode(batch).cpu().numpy())
    return np.concatenate(parts).reshape(n, channels * tl.LATENT)


def evaluate(data: dict, source_state: dict, epochs: int, seed: int):
    physics = tl.physical_by_sensor(data["sequences"], data["times"])
    folds = pair_folds(data, seed)
    rows, predictions = [], []
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    for fold in range(1, 6):
        train = folds != fold
        test = (folds == fold) & (data["offsets"] == 0)
        xs, ps = tl.fit_scalers(data["sequences"][train], physics[train])
        xt, pt = tl.transform(data["sequences"][train], physics[train], xs, ps)
        xv, pv = tl.transform(data["sequences"][test], physics[test], xs, ps)

        frozen = tl.SharedSensorAE().to(device)
        frozen.load_state_dict(source_state)
        scratch = tl.train_ae(xt, pt, seed + fold * 10, epochs)
        tuned = tl.train_ae(
            xt, pt, seed + fold * 10 + 1, max(10, epochs // 2), source_state
        )
        phys_train = pt.reshape(len(pt), -1)
        phys_test = pv.reshape(len(pv), -1)
        reps = {"physics_only": (phys_train, phys_test)}
        for prefix, model in (
            ("scratch", scratch),
            ("frozen_transfer", frozen),
            ("finetuned_transfer", tuned),
        ):
            a, b = encode(model, xt), encode(model, xv)
            reps[prefix + "_latent"] = (a, b)
            reps[prefix + "_latent_plus_physics"] = (
                np.concatenate([a, phys_train], axis=1),
                np.concatenate([b, phys_test], axis=1),
            )

        for name, (train_x, test_x) in reps.items():
            pred = tl.predict_xgb(
                train_x, data["targets"][train], test_x, seed + fold
            )
            row = {
                "fold": fold,
                "model": name,
                "n_train_windows": int(train.sum()),
                "n_test_exposures": int(test.sum()),
                "metrics": tl.metrics(data["targets"][test], pred, ("NH3", "H2")),
            }
            rows.append(row)
            print(json.dumps(row), flush=True)
            predictions.extend(
                {
                    "fold": fold,
                    "model": name,
                    "combination": int(group),
                    "NH3_true": float(y[0]),
                    "H2_true": float(y[1]),
                    "NH3_pred": float(p[0]),
                    "H2_pred": float(p[1]),
                }
                for group, y, p in zip(
                    data["groups"][test], data["targets"][test], pred
                )
            )
    return rows, predictions


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    tl.seed_all(args.seed)
    started = time.perf_counter()
    data, audit = load_windows(args.data)
    source_state = torch.load(args.source, map_location="cpu", weights_only=True)
    rows, predictions = evaluate(data, source_state, args.epochs, args.seed)
    result = {
        "experiment": "CO/ethylene pretrained sensor encoder transferred to TONG_NH3H2_CHUAN",
        "protocol": {
            "seed": args.seed,
            "epochs_scratch": args.epochs,
            "epochs_finetune": max(10, args.epochs // 2),
            "window": "first 64 samples; offsets 0..4 train augmentation; offset 0 test",
            "outer_split": "5-fold by unique (NH3,H2) pair; all six repeats kept together",
            "source": str(args.source),
            "sensors": len(SENSORS),
        },
        "data_audit": audit,
        "fold_results": rows,
        "summary": tl.summarize(
            [{"domain": "TONG_NH3H2_CHUAN", **row} for row in rows]
        )["TONG_NH3H2_CHUAN"],
        "elapsed_seconds": time.perf_counter() - started,
    }
    (args.output / "results.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    pd.DataFrame(predictions).to_csv(args.output / "predictions.csv", index=False)
    print(json.dumps({"summary": result["summary"],
                      "elapsed_seconds": result["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
