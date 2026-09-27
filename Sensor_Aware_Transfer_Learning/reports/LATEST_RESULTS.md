# Latest Sensor-Aware Transfer-Learning Results

## Status

These are the current latest validated results for the sensor-aware
self-supervised transfer-learning studies. All values are means over three
supervised subset/training seeds. Errors are measured on untouched target
sessions or future chronological blocks.

## NH3/H2: independent held-out session

### Protocol

- Unlabeled pretraining: sessions 1–4.
- Labeled adaptation: session 5.
- Untouched testing: session 6.
- Sensors: 20.
- Test exposures: 63.
- Labeled budgets: 5, 10, 20, 40, and 57 unique concentration pairs.

### MAE by label budget

| Pairs | NH3 scratch | NH3 frozen | NH3 fine-tuned | H2 scratch | H2 frozen | H2 fine-tuned |
|---:|---:|---:|---:|---:|---:|---:|
| 5 | 52.87 | 47.85 | **46.16** | 143.82 | 102.36 | **96.43** |
| 10 | 43.46 | 38.78 | **38.39** | 103.62 | 76.41 | **70.36** |
| 20 | 31.33 | **26.61** | 27.54 | 53.79 | **40.93** | 41.23 |
| 40 | 29.35 | 23.58 | **22.71** | 46.42 | 39.52 | **38.62** |
| 57 | 18.47 | 17.57 | **14.92** | 36.60 | 32.61 | **29.16** |

All values are ppm.

### Full-budget magnitude

| Gas | Best MAE | Mean test concentration | Error / mean | Error / full scale |
|---|---:|---:|---:|---:|
| NH3 | 14.92 ppm | 157.14 ppm | 9.49% | 2.98% |
| H2 | 29.16 ppm | 186.51 ppm | 15.63% | 5.83% |

Fine-tuned transfer improves on scratch by 19.2% for NH3 and 20.3% for H2.

## CO/ethylene: untouched future chronological block

### Protocol

- Unlabeled pretraining: chronological blocks 1–3.
- Labeled adaptation: block 4.
- Untouched testing: block 5.
- Sensors: 16.
- Test exposures: 49.
- Labeled budgets: 5, 10, 20, and 24 unique concentration pairs.

The source has no explicit session IDs, so these results demonstrate
chronological block transfer, not confirmed cross-session transfer.

### Transfer versus scratch

| Pairs | CO scratch | CO best transfer | Ethylene scratch | Ethylene best transfer |
|---:|---:|---:|---:|---:|
| 5 | 179.17 | **93.79** | 3.255 | **2.352** |
| 10 | 115.06 | **59.27** | 3.422 | **2.301** |
| 20 | 72.11 | **46.06** | 1.934 | **1.424** |
| 24 | 65.00 | **46.16** | 1.992 | **1.371** |

All values are ppm. Frozen transfer supplies the best CO result at 10–24
pairs. Fine-tuning supplies the best full-budget ethylene result.

### Matched physics + XGBoost comparison

| Pairs | CO best transfer | CO physics + XGB | Ethylene best transfer | Ethylene physics + XGB |
|---:|---:|---:|---:|---:|
| 5 | **93.79** | 126.87 | **2.352** | 3.516 |
| 10 | **59.27** | 85.21 | **2.301** | 2.595 |
| 20 | 46.06 | **40.29** | **1.424** | 1.937 |
| 24 | **46.16** | 46.44 | **1.371** | 2.015 |

At the full budget, transfer and XGBoost are tied for CO, while transfer is
32.0% better for ethylene. At 5–10 labels, transfer is more label-efficient
for both targets.

### Full-budget magnitude

| Target and strategy | MAE | Mean test concentration | Error / mean | Error / full scale |
|---|---:|---:|---:|---:|
| CO, frozen transfer | 46.16 ppm | 145.31 ppm | 31.76% | 8.65% |
| Ethylene, fine-tuned transfer | 1.371 ppm | 7.86 ppm | 17.45% | 6.86% |

## Current model-selection recommendation

| Situation | Recommended model |
|---|---|
| NH3/H2, 5–20 labeled pairs | Frozen or lightly fine-tuned transferred encoder |
| NH3/H2, 40–57 pairs | Fine-tuned transferred encoder |
| CO, 5–10 pairs | Frozen transferred encoder |
| CO, 20+ pairs | Compare frozen transfer with physics + XGBoost |
| Ethylene, any tested budget | Transferred encoder |
| One joint CO/ethylene model | Frozen transferred encoder for stability |

## Important comparison warning

The earlier random five-fold CO/ethylene physics + XGBoost result—approximately
14.60 ppm CO MAE and 0.443 ppm ethylene MAE—uses about 196 labeled exposures
per training fold. It is not directly comparable to the present low-label
future-block experiment using 5–24 labeled pairs.

## Artifact references

- NH3/H2 complete results: `../results/nh3_h2/results.json`
- NH3/H2 predictions: `../results/nh3_h2/predictions.csv`
- CO/ethylene complete results: `../results/co_ethylene/results.json`
- CO/ethylene predictions: `../results/co_ethylene/predictions.csv`
- Matched XGBoost results:
  `../results/co_ethylene/physics_xgboost_comparison.json`

