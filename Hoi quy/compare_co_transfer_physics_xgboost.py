#!/usr/bin/env python3
"""Fair same-split comparison: transfer learning vs physics + XGBoost."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from xgboost import XGBRegressor

import co_ethylene_session_transfer as study
from ec_improvement_benchmark import features


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "co_ethylene_session_transfer"


def main() -> None:
    data, _ = study.load_data(study.CACHE)
    adapt_zero = (data["blocks"] == 4) & (data["offsets"] == 0)
    test = (data["blocks"] == 5) & (data["offsets"] == 0)
    adapt_y0 = data["y"][adapt_zero]
    adapt_g0 = data["groups"][adapt_zero]
    test_x = features(data["x"][test], "physics")
    test_y = data["y"][test]
    existing = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
    budgets = existing["protocol"]["label_budgets_unique_pairs"]
    rows = []
    for repeat in range(existing["protocol"]["repeats"]):
        repeat_seed = 42 + repeat * 100
        order = study.farthest_order(adapt_y0, repeat_seed)
        ordered_groups = adapt_g0[order]
        for budget in budgets:
            selected = ordered_groups[:budget]
            train = (data["blocks"] == 4) & np.isin(data["groups"], selected)
            model = XGBRegressor(
                n_estimators=800, max_depth=3, learning_rate=.03,
                subsample=.8, colsample_bytree=.8,
                objective="reg:squarederror", n_jobs=-1,
                random_state=repeat_seed + budget,
            )
            model.fit(features(data["x"][train], "physics"), data["y"][train])
            pred = np.clip(model.predict(test_x), 0, study.TARGET_SCALE)
            row = {
                "repeat": repeat + 1, "seed": repeat_seed, "budget": budget,
                "model": "physics_xgboost", "metrics": study.metrics(test_y, pred),
            }
            rows.append(row)
            print(json.dumps(row), flush=True)
    result = {
        "protocol": {
            "features": "13 deterministic temporal/physics descriptors per sensor",
            "model": "XGBoost, 800 trees, depth 3, learning rate 0.03",
            "split": "identical calibration subsets and chronological test block as transfer study",
        },
        "runs": rows,
        "summary": study.core.aggregate(rows),
    }
    (OUT / "physics_xgboost_comparison.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
