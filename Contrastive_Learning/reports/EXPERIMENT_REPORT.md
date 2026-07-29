# Contrastive Sensor-Aware Transfer: Experiment Report

## Research question

Does adding exposure-level contrastive learning to masked signal
reconstruction produce a more transferable electronic-nose representation?

## Experimental controls

The architecture, data partitions, labeled-pair selection, downstream
training, seeds, and evaluation metrics are held constant. Only the
self-supervised objective changes:

1. reconstruction-only;
2. reconstruction + VICReg;
3. reconstruction + NT-Xent.

The reconstruction-only scores come from the immediately preceding
sensor-aware transfer study. VICReg and NT-Xent were newly trained and
evaluated with the same three downstream seeds.

## Leakage control

### NH3/H2

- Pretraining: unlabeled sessions 1–4.
- Adaptation: labeled subsets from session 5.
- Testing: untouched session 6.

### CO/ethylene

- Pretraining: unlabeled chronological blocks 1–3.
- Adaptation: labeled subsets from block 4.
- Testing: untouched chronological block 5.

The CO/ethylene source does not contain true session IDs, so its result is a
future-block experiment rather than confirmed cross-session transfer.

## Best objective by setting

| Dataset | Labels | Target | Best objective | Adaptation | MAE |
|---|---:|---|---|---|---:|
| NH3/H2 | 5 | NH3 | NT-Xent | Frozen | 43.17 ppm |
| NH3/H2 | 5 | H2 | NT-Xent | Frozen | 82.29 ppm |
| NH3/H2 | 10 | NH3 | NT-Xent | Fine-tuned | 35.85 ppm |
| NH3/H2 | 10 | H2 | NT-Xent | Frozen | 65.53 ppm |
| NH3/H2 | 20 | NH3 | Reconstruction | Frozen | 26.61 ppm |
| NH3/H2 | 20 | H2 | Reconstruction | Frozen | 40.93 ppm |
| NH3/H2 | 40 | NH3 | Reconstruction | Fine-tuned | 22.71 ppm |
| NH3/H2 | 40 | H2 | Reconstruction | Fine-tuned | 38.62 ppm |
| NH3/H2 | 57 | NH3 | Reconstruction | Fine-tuned | 14.92 ppm |
| NH3/H2 | 57 | H2 | Reconstruction | Fine-tuned | 29.16 ppm |
| CO/ethylene | 5 | CO | VICReg | Frozen | 91.89 ppm |
| CO/ethylene | 5 | Ethylene | Reconstruction | Fine-tuned | 2.352 ppm |
| CO/ethylene | 10 | CO | Reconstruction | Frozen | 59.27 ppm |
| CO/ethylene | 10 | Ethylene | Reconstruction | Fine-tuned | 2.301 ppm |
| CO/ethylene | 20 | CO | Reconstruction | Frozen | 46.06 ppm |
| CO/ethylene | 20 | Ethylene | Reconstruction | Frozen | 1.424 ppm |
| CO/ethylene | 24 | CO | NT-Xent | Fine-tuned | **43.16 ppm** |
| CO/ethylene | 24 | Ethylene | Reconstruction | Fine-tuned | **1.371 ppm** |

## Where contrastive learning helped

### Low-label NH3/H2

At five labeled pairs, frozen NT-Xent improves over the strongest
reconstruction-only choice:

| Gas | Reconstruction | NT-Xent | Improvement |
|---|---:|---:|---:|
| NH3 | 46.16 ppm | 43.17 ppm | 6.5% |
| H2 | 96.43 ppm | 82.29 ppm | 14.7% |

At ten pairs:

| Gas | Reconstruction | NT-Xent | Improvement |
|---|---:|---:|---:|
| NH3 | 38.39 ppm | 35.85 ppm | 6.6% |
| H2 | 70.36 ppm | 65.53 ppm | 6.9% |

This is the clearest evidence for contrastive learning: exposure identity
provides a useful supervisory signal when concentration labels are extremely
scarce.

### Full-budget CO

Fine-tuned NT-Xent achieves 43.16 ppm CO MAE versus 46.16 ppm from the best
reconstruction-only transfer model, a 6.5% reduction. It also improves on the
matched physics + XGBoost score of 46.44 ppm by 7.1%.

## Where contrastive learning did not help

Reconstruction-only remains best:

- for NH3/H2 at 20, 40, and 57 labeled pairs;
- for ethylene at every tested budget;
- for CO at 10 and 20 pairs.

At the full NH3/H2 budget, NT-Xent nearly matches H2 but not NH3:

| Gas | Reconstruction | NT-Xent |
|---|---:|---:|
| NH3 | **14.92 ppm** | 16.01 ppm |
| H2 | **29.16 ppm** | 29.35 ppm |

VICReg does not consistently outperform reconstruction. Its only new best is
the five-label CO setting, where frozen VICReg gives 91.89 ppm versus 93.79
ppm for the best reconstruction-only model—a modest 2.0% gain.

## Interpretation

### Why NT-Xent helps with very few labels

Offset windows and corrupted views of the same exposure share gas composition,
sensor condition, and response kinetics. Pulling those views together makes
the downstream head less sensitive to noise and window selection. This
invariance is valuable when labeled calibration cannot teach it reliably.

### Why it can hurt with more labels

NT-Xent treats every other exposure as a negative. Exposures with nearby gas
concentrations are therefore false negatives: their embeddings are pushed
apart despite representing chemically similar conditions. With enough
labeled data, reconstruction preserves continuous response magnitude better
than this hard instance-discrimination objective.

### Why ethylene is especially sensitive

Ethylene spans only 0–20 ppm. Mild gain and baseline augmentations occupy a
larger fraction of its predictive signal than they do for CO. Contrastive
invariance may suppress precisely the small amplitude differences required
for accurate ethylene regression.

### Why VICReg was not consistently better

VICReg avoids false negatives but its variance/covariance constraints compete
with a strongly structured reconstruction task. The current loss weight was
stable, but it may be too strong for concentration-sensitive embeddings or
may need a lower-dimensional projection head.

## Recommended model policy

- NH3/H2 with 5–10 labels: use frozen NT-Xent; fine-tune NH3 at 10 pairs if
  validation data are available.
- NH3/H2 with 20–57 labels: use reconstruction-only transfer.
- CO with 5 labels: VICReg and reconstruction are close; prefer VICReg only
  after confirming on another chronological block.
- CO with 10–20 labels: use reconstruction-only frozen transfer.
- CO with all 24 labels: use fine-tuned NT-Xent.
- Ethylene: use reconstruction-only transfer at every tested budget.

## Future experiments

1. Replace hard NT-Xent negatives with concentration-distance-weighted soft
   negatives during supervised adaptation.
2. Test VICReg weights of 0.01, 0.02, and 0.05 and smaller projectors.
3. Restrict amplitude and baseline augmentation for ethylene.
4. Use nearest-concentration exposures as weak positives rather than
   negatives.
5. Compare non-contrastive Barlow Twins and BYOL-style objectives.
6. Run leave-one-session-out NH3/H2 evaluation and rolling CO chronological
   blocks before treating the observed gains as deployment-stable.

## Runtime and outputs

| Dataset | Objective | Runtime |
|---|---|---:|
| NH3/H2 | VICReg | 490.6 s |
| NH3/H2 | NT-Xent | 489.2 s |
| CO/ethylene | VICReg | 277.6 s |
| CO/ethylene | NT-Xent | 287.7 s |

Complete metrics, all 6,132 held-out predictions across the four studies, and
pretrained encoder weights are stored under `results/`.
