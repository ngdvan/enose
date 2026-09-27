#!/usr/bin/env python3
"""Fair same-split comparison: NH3/H2 transfer vs physics + XGBoost."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from xgboost import XGBRegressor

import same_device_session_transfer as study


ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = ROOT.parent
OUT = PACKAGE_ROOT / "results" / "nh3_h2"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=study.DATA)
    parser.add_argument("--output", type=Path, default=OUT)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    data, _ = study.load_exposures(args.data)
    pre_idx = np.flatnonzero(data["sessions"] <= 4)
    adapt_idx = np.flatnonzero(data["sessions"] == 5)
    test_idx = np.flatnonzero(data["sessions"] == 6)

    pre_x_raw, _, _ = study.make_windows(data, pre_idx)
    scaler = study.SensorScaler().fit(pre_x_raw)
    test_raw, test_y, _ = study.make_windows(data, test_idx, offsets=[0])
    test_features = study.descriptors(scaler.transform(test_raw))

    existing = json.loads((args.output / "results.json").read_text(encoding="utf-8"))
    budgets = existing["protocol"]["label_budgets_unique_concentration_pairs"]
    repeats = existing["protocol"]["repeats"]
    rows = []

    for repeat in range(repeats):
        repeat_seed = args.seed + repeat * 100
        local = study.farthest_subset(
            data["targets"][adapt_idx], max(budgets), repeat_seed
        )
        ordered_adapt = adapt_idx[local]
        for budget in budgets:
            chosen = ordered_adapt[:budget]
            train_raw, train_y, _ = study.make_windows(data, chosen)
            train_features = study.descriptors(scaler.transform(train_raw))
            model = XGBRegressor(
                n_estimators=800,
                max_depth=3,
                learning_rate=0.03,
                subsample=0.8,
                colsample_bytree=0.8,
                objective="reg:squarederror",
                n_jobs=-1,
                random_state=repeat_seed + budget,
            )
            model.fit(train_features, train_y)
            prediction = np.clip(model.predict(test_features), 0, study.TARGET_SCALE)
            row = {
                "repeat": repeat + 1,
                "seed": repeat_seed,
                "budget": budget,
                "model": "physics_xgboost",
                "metrics": study.metric_dict(test_y, prediction),
            }
            rows.append(row)
            print(json.dumps(row), flush=True)

    result = {
        "protocol": {
            "features": "37 deterministic temporal/physics descriptors per sensor",
            "model": "XGBoost, 800 trees, depth 3, learning rate 0.03",
            "split": (
                "identical calibration subsets and untouched session 6 test set "
                "as the NH3/H2 transfer study"
            ),
        },
        "runs": rows,
        "summary": study.aggregate(rows),
    }
    (args.output / "physics_xgboost_comparison.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
