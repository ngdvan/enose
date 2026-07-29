# CO/Ethylene Contrastive-Learning Results

## Protocol

Chronological blocks 1–3 were used for unlabeled pretraining, block 4 for
labeled adaptation, and block 5 for untouched future-block testing. The file
does not contain true session IDs.

## Best adaptation result within each objective

### CO MAE (ppm)

| Labels | Reconstruction | VICReg | NT-Xent |
|---:|---:|---:|---:|
| 5 | 93.79 | **91.89** | 97.55 |
| 10 | **59.27** | 83.74 | 70.15 |
| 20 | **46.06** | 59.28 | 46.15 |
| 24 | 46.16 | 62.33 | **43.16** |

### Ethylene MAE (ppm)

| Labels | Reconstruction | VICReg | NT-Xent |
|---:|---:|---:|---:|
| 5 | **2.352** | 3.077 | 2.833 |
| 10 | **2.301** | 2.872 | 2.566 |
| 20 | **1.424** | 1.797 | 1.781 |
| 24 | **1.371** | 1.644 | 1.758 |

## Conclusion

Fine-tuned NT-Xent provides the new best full-budget CO model at 43.16 ppm,
6.5% better than reconstruction-only transfer and 7.1% better than matched
physics + XGBoost. Reconstruction-only remains the clear choice for ethylene.
The five-label VICReg CO improvement is small and should be validated on
additional chronological blocks.

