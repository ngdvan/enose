# Sensor-aware transfer learning for CO and ethylene

## Executive summary

The same-device self-supervised transfer approach was applied to the
16-sensor CO/ethylene dataset. The dataset has no explicit session identifier,
so its 245 chronological exposure runs were divided into five contiguous
49-run acquisition blocks:

- blocks 1–3: unlabeled representation pretraining;
- block 4: small labeled adaptation subsets;
- block 5: untouched future-block evaluation.

Transfer improved both gases at every label budget. With all 24 unique
adaptation concentration pairs:

| Target | Scratch MAE | Best transfer MAE | Reduction |
|---|---:|---:|---:|
| CO | 65.00 ppm | **46.16 ppm** (frozen) | **29.0%** |
| Ethylene | 1.99 ppm | **1.37 ppm** (fine-tuned) | **31.2%** |

The optimal adaptation policy is target-dependent. Freezing the pretrained
encoder is safer for CO, while mild fine-tuning gives the best ethylene result.

## Dataset and chronological protocol

| Property | Value |
|---|---:|
| Exposure runs | 245 |
| Augmented sequence windows | 1,225 |
| Sensor channels | 16 |
| Sequence length | 64 |
| Chronological blocks | 5 |
| Exposures per block | 49 |
| CO range | 0–533.33 ppm |
| Ethylene range | 0–20 ppm |

The existing sequence preparation contributes five windows per exposure,
sampled at offsets 0, 20, 40, 60, and 80. All five were allowed in unlabeled
pretraining and labeled adaptation. Only offset zero was scored for each of the
49 held-out block-5 exposures.

The number of unique `(CO, ethylene)` pairs varies by chronological block:

| Block | Unique pairs | Role |
|---:|---:|---|
| 1 | 26 | Unlabeled pretraining |
| 2 | 27 | Unlabeled pretraining |
| 3 | 31 | Unlabeled pretraining |
| 4 | 24 | Labeled adaptation |
| 5 | 26 | Untouched testing |

This is a future-block forecasting design. The held-out block was not used to
fit sensor scaling, pretrain the representation, select calibration pairs, or
train regression heads.

## Model and training

The model is the same sensor-aware architecture used for NH3/H2, configured
for 16 channels:

1. A shared dilated temporal CNN extracts a token from each sensor curve.
2. Learned sensor identity embeddings preserve channel-specific meaning.
3. A two-layer, four-head Transformer models cross-sensor interactions.
4. A multilayer regression head predicts CO and ethylene jointly.

### Self-supervised pretraining

The model was trained without concentration labels on 735 windows from
chronological blocks 1–3. It reconstructed:

- randomly masked temporal spans;
- spans masked on random subsets of sensors; and
- one to three completely hidden sensor channels.

The masked reconstruction loss decreased from 1.950 at epoch 1 to a minimum of
0.165 at epoch 51. The epoch-60 stochastic masked loss was 0.302. Because a new
random mask is drawn each epoch, this training loss is noisy and the last value
need not be the minimum.

### Adaptation strategies

Four supervised approaches received the same labeled block-4 data:

- **Scratch:** randomly initialized encoder and regression head.
- **Frozen transfer:** pretrained encoder fixed; regression head trained.
- **Fine-tuned transfer:** pretrained encoder updated at a lower learning rate.
- **Physics + Extra Trees:** deterministic response descriptors and a tree
  ensemble.

Calibration budgets of 5, 10, 20, and all 24 unique concentration pairs were
tested. Farthest-point sampling in concentration space selected broadly spread
pairs. Three subset/training seeds were evaluated.

## Main results

Values are mean MAE across three repeated runs; parentheses contain standard
deviation.

### CO MAE (ppm)

| Labeled pairs | Scratch | Frozen transfer | Fine-tuned transfer | Physics baseline |
|---:|---:|---:|---:|---:|
| 5 | 179.17 (55.77) | 93.99 (8.71) | **93.79 (7.68)** | 105.77 (17.58) |
| 10 | 115.06 (27.75) | **59.27 (7.41)** | 68.42 (13.24) | 86.84 (14.78) |
| 20 | 72.11 (6.45) | **46.06 (2.91)** | 49.27 (3.46) | 71.92 (4.85) |
| 24 | 65.00 (9.96) | **46.16 (4.58)** | 51.07 (3.37) | 76.58 (0.83) |

### Ethylene MAE (ppm)

| Labeled pairs | Scratch | Frozen transfer | Fine-tuned transfer | Physics baseline |
|---:|---:|---:|---:|---:|
| 5 | 3.255 (0.979) | 2.407 (0.160) | **2.352 (0.618)** | 3.440 (0.419) |
| 10 | 3.422 (0.489) | 2.391 (0.459) | **2.301 (0.500)** | 3.469 (0.195) |
| 20 | 1.934 (0.273) | **1.424 (0.137)** | 1.507 (0.052) | 2.609 (0.053) |
| 24 | 1.992 (0.222) | 1.503 (0.138) | **1.371 (0.025)** | 2.692 (0.006) |

## Relative improvement over scratch

The best transferred variant for each gas and budget gives:

| Labeled pairs | CO MAE reduction | Ethylene MAE reduction |
|---:|---:|---:|
| 5 | 47.7% | 27.7% |
| 10 | 48.5% | 32.8% |
| 20 | 36.1% | 26.4% |
| 24 | 29.0% | 31.2% |

Transfer is most valuable for CO in the extremely low-label regime. With only
10 concentration pairs, the frozen representation nearly halves CO MAE from
115.06 to 59.27 ppm.

## Matched comparison with physics + XGBoost

A separate physics + XGBoost benchmark was run on exactly the same calibration
subsets and untouched chronological test block. It used 13 deterministic
temporal/physics descriptors per sensor and XGBoost with 800 trees, depth 3,
and learning rate 0.03.

The table compares the strongest transfer choice for each target with XGBoost.

| Labels | CO transfer | CO XGBoost | Ethylene transfer | Ethylene XGBoost |
|---:|---:|---:|---:|---:|
| 5 | **93.79** | 126.87 | **2.352** | 3.516 |
| 10 | **59.27** | 85.21 | **2.301** | 2.595 |
| 20 | 46.06 | **40.29** | **1.424** | 1.937 |
| 24 | **46.16** | 46.44 | **1.371** | 2.015 |

All values are MAE in ppm and are means over the same three calibration
selections.

The comparison shows:

- At 5 labels, transfer reduces MAE relative to XGBoost by 26.1% for CO and
  33.1% for ethylene.
- At 10 labels, transfer reduces MAE by 30.4% for CO and 11.3% for ethylene.
- At 20 labels, XGBoost is 12.5% better for CO, while transfer is 26.5% better
  for ethylene.
- At 24 labels, frozen transfer and XGBoost are effectively tied for CO
  (46.16 versus 46.44 ppm), while fine-tuned transfer is 32.0% better for
  ethylene.

Therefore, physics + XGBoost is competitive for CO once approximately 20
representative labeled pairs are available. The transferred encoder is
decisively more label-efficient at 5–10 pairs and consistently stronger for
ethylene.

### Why the older XGBoost benchmark appears much better

The project's earlier random five-fold physics + XGBoost benchmark reported
approximately 14.60 ppm CO MAE and 0.443 ppm ethylene MAE. Those results used
about 196 labeled exposure runs (980 augmented windows) in every training fold
and randomly distributed chronological runs among folds.

The current comparison uses only 5–24 unique labeled pairs from one later
chronological block and tests on the subsequent future block. The older scores
answer a high-label random-group generalization question; the current scores
answer a low-label future-block calibration question. They should not be
presented as a direct model ranking.

## Error magnitude in context

The untouched test block has mean concentrations of:

- CO: 145.31 ppm;
- ethylene: 7.86 ppm.

At the full adaptation budget:

| Target and strategy | MAE | % of test mean | % of full scale | R² |
|---|---:|---:|---:|---:|
| CO, frozen encoder | **46.16 ppm** | **31.76%** | **8.65%** | 0.776 |
| Ethylene, fine-tuned encoder | **1.371 ppm** | **17.45%** | **6.86%** | 0.802 |

For a single joint model rather than target-specific models, the full-budget
frozen model gives 46.16 ppm CO MAE and 1.503 ppm ethylene MAE. Both remain
better than scratch.

MAPE is not reported because zero-concentration targets make it undefined or
misleading. MAE relative to the nonzero overall scale and the test mean is
reported instead.

## Interpretation

### The representation transfers successfully

Unlike cross-gas transfer from a different sensor setup, this pretraining uses
the same 16 named sensor channels and the same acquisition stream. Even though
no concentration labels from blocks 1–3 are used, the encoder learns reusable
response dynamics and sensor relationships.

### Freezing is preferable for CO

Frozen transfer beats fine-tuning for CO at budgets of 10, 20, and 24 pairs.
CO has a large 0–533 ppm range and relatively few calibration pairs in block 4.
Updating the encoder can specialize it too strongly to that small block.

### Ethylene benefits from mild adaptation

Fine-tuning is best for ethylene at 5, 10, and 24 pairs, although frozen
transfer is slightly better at 20. Ethylene's response representation appears
to benefit from block-specific adjustment, but the differences between frozen
and fine-tuned transfer are much smaller than their advantage over scratch.

### Recommended deployment policy

If one joint model is required, use the frozen encoder for stability. If
separate target heads or models are acceptable:

- CO: keep the encoder frozen and train a CO-specific head;
- ethylene: fine-tune with the encoder learning rate substantially below the
  head learning rate.

## Important limitations

1. **These are not documented sessions.** The source is one continuous time
   series with no session IDs or timestamp resets. The five contiguous blocks
   are chronological acquisition partitions, not confirmed independent days
   or experiments.
2. Only the last chronological block was used for final testing. Results may
   depend on the particular concentration distribution or drift in that block.
3. Block 4 has only 24 unique pairs and block 5 has 26; their concentration
   grids are not identical.
4. Three repeated calibration selections quantify subset and training
   variability but do not replace multiple independent test sessions.
5. The final pretraining checkpoint was used. Saving the checkpoint with the
   best validation reconstruction loss could improve stability, but would
   require a pretraining-only validation split.
6. This protocol tests future acquisition-block transfer on the same physical
   device, not transfer to another e-nose unit.

## Recommended next study

Use rolling chronological evaluation:

- pretrain on blocks preceding the adaptation block;
- adapt on the next block;
- test on the immediately following block;
- repeat for all feasible chronological triplets.

This would reveal whether the transfer benefit is consistent through time.
If acquisition-day metadata can be recovered, replace chronological blocks
with true day/session IDs and repeat the leave-one-session-out design used for
NH3/H2.

## Reproducibility

| Setting | Value |
|---|---|
| Base seed | 42 |
| Repeated-run seeds | 42, 142, 242 |
| Pretraining epochs | 60 |
| Supervised epochs | 120 |
| Unlabeled pretraining windows | 735 |
| Test exposures | 49 |
| Runtime | 140.7 seconds |
| Encoder | CNN + sensor IDs + Transformer |
| SSL task | Masked time/sensor reconstruction |

Generated artifacts:

- `results.json`: full protocol, per-run metrics, and summaries;
- `physics_xgboost_comparison.json`: matched-split physics + XGBoost results;
- `predictions.csv`: every held-out prediction;
- `pretrained_encoder.pt`: unlabeled pretrained encoder;
- `scaler.npz`: training-block sensor scaling parameters;
- `co_ethylene_session_transfer.py`: executable experiment.
