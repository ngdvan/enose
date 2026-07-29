#!/usr/bin/env python3
"""Frozen physics-XGBoost augmentation and sensor-drop ablations."""
from __future__ import annotations
import json, time
from pathlib import Path
import numpy as np
from xgboost import XGBRegressor
import ec_improvement_benchmark as bench

ROOT = Path(__file__).resolve().parent
data = dict(np.load(ROOT / "ec_improvements" / "raw_sequences.npz"))
x, y, folds, offsets = (data[k] for k in ("sequences", "targets", "folds", "offsets"))

def model():
    return XGBRegressor(n_estimators=300, max_depth=3, learning_rate=.03,
        subsample=.8, colsample_bytree=.8, objective="reg:squarederror", n_jobs=-1, random_state=42)

rows=[]
for drop in [None] + list(range(16)):
    keep = np.ones(16, dtype=bool)
    if drop is not None: keep[drop] = False
    f = bench.features(x[:,:,keep], "physics")
    for fold in range(1,6):
        train, test = folds != fold, (folds == fold) & (offsets == 0)
        started=time.perf_counter(); m=model().fit(f[train],y[train]); pred=m.predict(f[test])
        row={"test":"sensor_drop", "dropped_sensor": None if drop is None else drop+1,
             "fold":fold,"seconds":time.perf_counter()-started,"metrics":bench.score(y[test],pred)}
        rows.append(row); print(json.dumps(row))

# Isolate the effect of augmented training windows with the same model/features/folds.
f=bench.features(x,"physics")
for fold in range(1,6):
    train=(folds != fold) & (offsets == 0); test=(folds == fold) & (offsets == 0)
    started=time.perf_counter(); m=model().fit(f[train],y[train]); pred=m.predict(f[test])
    row={"test":"no_training_augmentation","dropped_sensor":None,"fold":fold,
         "seconds":time.perf_counter()-started,"metrics":bench.score(y[test],pred)}
    rows.append(row); print(json.dumps(row))

(ROOT / "ec_improvements" / "ablation_results.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
