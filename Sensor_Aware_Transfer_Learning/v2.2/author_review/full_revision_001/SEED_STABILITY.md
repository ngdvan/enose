# Does the result weaken with more seeds?

**Partly.** The secondary fixed-split benefits become smaller with ten seeds, especially NH3. The primary multi-fold results do not weaken systematically: NH3/H2 improve slightly, while CO/ethylene attenuate slightly. Drift partition 8 weakens, partition 9 is stable, and partition 10 has no clear ten-seed transfer benefit.

These comparisons use prefixes of the same corrected protocol in the predefined order 42, 142, …, 942. They do not compare a favorable selected three-seed subset against ten seeds. Positive percentages mean reduced MAE versus scratch. All ten seeds remain in the final report.

| Evaluation | Gas | First 3 reduction | All 10 reduction | Later 7 reduction |
|---|---|---:|---:|---:|
| primary_multifold | CO | 28.48% | 27.50% | 27.06% |
| primary_multifold | Ethylene | 26.09% | 25.73% | 25.57% |
| primary_multifold | H2 | 18.40% | 21.49% | 22.72% |
| primary_multifold | NH3 | 13.30% | 13.91% | 14.15% |
| fixed_split | CO | 27.23% | 25.43% | 24.71% |
| fixed_split | Ethylene | 31.14% | 24.31% | 21.01% |
| fixed_split | H2 | 27.22% | 23.29% | 21.52% |
| fixed_split | NH3 | 32.44% | 19.59% | 12.96% |
| drift_partition_8 | MacroMAE | 25.61% | 18.80% | 15.63% |
| drift_partition_9 | MacroMAE | 17.97% | 18.35% | 18.52% |
| drift_partition_10 | MacroMAE | -11.95% | -0.50% | 4.17% |

## Primary uncertainty after ten seeds

| Gas | Paired MAE reduction (ppm) | 95% seed/fold interval (ppm) |
|---|---:|---:|
| CO | 24.737 | [12.850, 37.527] |
| Ethylene | 0.672 | [0.247, 1.143] |
| H2 | 10.575 | [3.566, 18.776] |
| NH3 | 4.312 | [0.381, 8.305] |

All four primary intervals exclude zero, with NH3 closest to zero. They resample paired seeds and folds, condition on the observed exposures, and do not create independent acquisition evidence. The full-prefix CSV and random-order envelope show variability at every count; the envelope is an order/subset diagnostic, not a population confidence interval.

## Comparison with the historical manuscript

| Gas | Historical 3-repeat reduction | Revised 10-seed reduction |
|---|---:|---:|
| CO | 20.41% | 27.50% |
| Ethylene | 14.55% | 25.73% |
| H2 | 20.11% | 21.49% |
| NH3 | 16.39% | 13.91% |

This historical comparison is **not a seed-only experiment**. The revision changes policy reporting, uses matched fitting/validation holdouts, and uses full available adaptation coverage in rolling folds. Thus the same-protocol prefix comparison above is the appropriate test of adding seeds. More seeds characterize initialization, training, calibration-design and holdout variability; they cannot compensate for a small number of independently acquired test partitions.