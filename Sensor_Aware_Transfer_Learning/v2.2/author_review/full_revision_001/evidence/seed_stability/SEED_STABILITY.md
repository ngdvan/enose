# Seed-count stability audit

All ten predefined seeds remain the reporting set. Prefixes use 42, 142, ..., 942 in that order. The first three here are from the revised, matched-holdout protocol, not the historical manuscript. Differences from the original publication cannot be attributed to seed count alone.

Positive reduction favors fine-tuning. Primary multi-fold results weight folds equally. Bootstrap intervals resample paired seeds and folds, conditional on the observed exposures. The random-order envelope is a subset/order diagnostic, not a confidence interval. No seed count or model is selected from this audit.

| Analysis | Gas | First 3 reduction (%) | All 10 reduction (%) | Later 7 reduction (%) | Positive seeds / 10 |
|---|---|---:|---:|---:|---:|
| primary_multifold | CO | 28.48 | 27.50 | 27.06 | 10 |
| primary_multifold | Ethylene | 26.09 | 25.73 | 25.57 | 9 |
| primary_multifold | H2 | 18.40 | 21.49 | 22.72 | 10 |
| primary_multifold | NH3 | 13.30 | 13.91 | 14.15 | 9 |
| fixed_split | CO | 27.23 | 25.43 | 24.71 | 10 |
| fixed_split | Ethylene | 31.14 | 24.31 | 21.01 | 9 |
| fixed_split | H2 | 27.22 | 23.29 | 21.52 | 10 |
| fixed_split | NH3 | 32.44 | 19.59 | 12.96 | 9 |
| drift_partition_8 | MacroMAE | 25.61 | 18.80 | 15.63 | 9 |
| drift_partition_9 | MacroMAE | 17.97 | 18.35 | 18.52 | 9 |
| drift_partition_10 | MacroMAE | -11.95 | -0.50 | 4.17 | 6 |

Adding seeds changes the estimated average; it does not degrade a trained model. Read the change in relative reduction together with absolute scratch/fine-tuned errors and paired uncertainty. Ten seeds characterize training variability, but do not create additional independent physical test exposures.