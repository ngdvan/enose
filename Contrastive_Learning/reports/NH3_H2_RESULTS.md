# NH3/H2 Contrastive-Learning Results

## Protocol

Unlabeled sessions 1–4 were used for pretraining, labeled subsets of session 5
for adaptation, and session 6 for untouched testing. Results are mean MAE
across three seeds.

## Best adaptation result within each objective

### NH3 MAE (ppm)

| Labels | Reconstruction | VICReg | NT-Xent |
|---:|---:|---:|---:|
| 5 | 46.16 | 50.27 | **43.17** |
| 10 | 38.39 | 46.39 | **35.85** |
| 20 | **26.61** | 32.80 | 28.18 |
| 40 | **22.71** | 28.13 | 24.72 |
| 57 | **14.92** | 17.47 | 16.01 |

### H2 MAE (ppm)

| Labels | Reconstruction | VICReg | NT-Xent |
|---:|---:|---:|---:|
| 5 | 96.43 | 97.95 | **82.29** |
| 10 | 70.36 | 78.88 | **65.53** |
| 20 | **40.93** | 54.48 | 43.55 |
| 40 | **38.62** | 42.80 | 39.80 |
| 57 | **29.16** | 31.10 | 29.35 |

## Conclusion

NT-Xent is recommended only in the 5–10-pair regime. Reconstruction-only
pretraining is superior once 20 or more labeled concentration pairs are
available. VICReg is not competitive under the tested weighting.

