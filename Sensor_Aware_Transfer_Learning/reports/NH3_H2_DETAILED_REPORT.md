# Same-device sensor-aware transfer learning for NH3/H2

## Executive summary

This experiment tested whether unlabeled recordings from the same 20-sensor
electronic nose can provide a useful transferable signal representation.
Sessions 1–4 were used for self-supervised pretraining without gas labels,
session 5 supplied a limited number of labeled concentration pairs, and session
6 was kept completely untouched for testing.

The result is positive. Fine-tuned transfer outperformed training the identical
architecture from scratch at every tested label budget. With all 57 unique
adaptation pairs, transfer reduced mean absolute error (MAE):

- NH3: from 18.47 to **14.92 ppm**, a 19.2% reduction.
- H2: from 36.60 to **29.16 ppm**, a 20.3% reduction.

At 20 labeled pairs, the frozen transferred representation was particularly
effective: 26.61 ppm NH3 MAE and 40.93 ppm H2 MAE, compared with 31.33 and
53.79 ppm from scratch. Thus, same-device representation transfer is useful,
especially when labels are scarce.

## Research question

Can an encoder learn reusable temporal and cross-sensor structure from
unlabeled measurements made by the same device, then adapt to NH3/H2
concentration regression using only a small labeled calibration set?

This differs from the earlier CO/ethylene transfer experiment. The source
signals here come from the same 20 physical sensor channels and acquisition
process as the target session, reducing domain mismatch.

## Dataset audit

The workbook contains:

| Property | Value |
|---|---:|
| Rows | 162,404 |
| Sensor channels | 20 |
| Exposures | 378 |
| Measurement sessions | 6 |
| Exposures per session | 63 |
| Unique concentration pairs per session | 57 |
| Concentration range | 0–500 ppm |
| Corrected transition-label rows | 11 |

The six sessions were identified from the documented sequence of six repeated
measurement rounds: combinations 1–63, 64–126, ..., 316–378. Each session
contains the same set of 57 unique `(NH3, H2)` pairs. Some pure-gas
concentrations are repeated within a session, explaining the difference
between 63 exposures and 57 unique pairs.

Eleven rows at exposure transitions carried the adjacent exposure's label.
Each exposure's modal `(NH3, H2)` pair was used as its label. Sensor values
were never used to perform this correction.

## Leakage-controlled experimental design

| Stage | Data | Labels used? |
|---|---|---|
| Self-supervised pretraining | Sessions 1–4 | No |
| Small-set adaptation | Session 5 | Yes |
| Final evaluation | Session 6 | No; held out |

Session 6 was excluded from preprocessing fits, representation learning,
model selection, and supervised training. The per-sensor robust scaler was
fit only on sessions 1–4.

For pretraining and adaptation, five 64-sample windows starting at offsets
0–4 were used for augmentation. Only the offset-zero window was evaluated in
the test session, giving one prediction per independent exposure.

The labeled budgets were 5, 10, 20, 40, and 57 unique concentration pairs.
Farthest-point sampling in normalized NH3/H2 concentration space selected
well-spread calibration pairs. The study was repeated with three subset and
training seeds.

## Model

### Sensor-aware encoder

The encoder has three components:

1. A shared dilated temporal CNN converts every 64-point sensor response into
   a compact token.
2. A learned identity embedding is added for each of the 20 sensors, preserving
   the distinction between channels.
3. A two-layer, four-head Transformer models interactions among all sensor
   tokens.

Unlike a purely shared per-sensor encoder, this design can learn that a
particular temporal response has different meaning on Response1 versus
Response20 and can combine selective responses across sensors.

### Self-supervised objective

During pretraining, the input was corrupted by:

- masking three randomly located temporal spans;
- masking each span on a random subset of sensors; and
- completely hiding one to three sensor channels.

The network reconstructed the missing response values. Complete-sensor
masking forces it to use relationships among sensors, while temporal masking
forces it to learn response-curve dynamics.

The reconstruction loss decreased from 2.160 in epoch 1 to 0.076 in epoch 60,
indicating successful learning of the unlabeled signal structure.

### Supervised strategies

Four methods were compared:

- **Scratch:** randomly initialized encoder and regression head.
- **Frozen transfer:** pretrained encoder fixed; only the regression head trained.
- **Fine-tuned transfer:** pretrained encoder updated at a lower learning rate
  than the regression head.
- **Physics + Extra Trees:** deterministic temporal descriptors with a
  non-neural tree ensemble.

The neural models were otherwise identical and received the same labeled
windows.

## Results

Values below are mean MAE in ppm across three repeated runs. Parentheses show
the standard deviation.

### NH3

| Labeled pairs | Scratch | Frozen transfer | Fine-tuned transfer | Physics baseline |
|---:|---:|---:|---:|---:|
| 5 | 52.87 (7.88) | 47.85 (4.72) | **46.16 (5.19)** | 48.28 (5.91) |
| 10 | 43.46 (8.07) | 38.78 (6.15) | 38.39 (4.02) | **37.41 (3.89)** |
| 20 | 31.33 (0.80) | **26.61 (0.84)** | 27.54 (1.06) | 32.96 (3.19) |
| 40 | 29.35 (1.66) | 23.58 (1.20) | **22.71 (0.67)** | 24.64 (0.59) |
| 57 | 18.47 (3.95) | 17.57 (0.48) | **14.92 (0.57)** | 17.70 (0.24) |

### H2

| Labeled pairs | Scratch | Frozen transfer | Fine-tuned transfer | Physics baseline |
|---:|---:|---:|---:|---:|
| 5 | 143.82 (25.57) | 102.36 (9.67) | **96.43 (3.25)** | 158.35 (23.51) |
| 10 | 103.62 (4.78) | 76.41 (25.64) | **70.36 (20.43)** | 104.37 (14.89) |
| 20 | 53.79 (1.54) | **40.93 (1.56)** | 41.23 (1.10) | 57.89 (6.73) |
| 40 | 46.42 (2.92) | 39.52 (1.96) | **38.62 (1.04)** | 39.83 (0.97) |
| 57 | 36.60 (4.20) | 32.61 (1.81) | **29.16 (1.10)** | 33.00 (0.32) |

### Relative improvement over scratch

| Labeled pairs | NH3 reduction | H2 reduction |
|---:|---:|---:|
| 5 | 12.7% | 33.0% |
| 10 | 11.7% | 32.1% |
| 20 | 12.1% | 23.3% |
| 40 | 22.6% | 16.8% |
| 57 | 19.2% | 20.3% |

The table compares fine-tuned transfer with scratch. At 20 pairs, frozen
transfer was marginally better than fine-tuning for both gases; this suggests
that limiting encoder updates can reduce overfitting at intermediate label
budgets.

## Error magnitude in concentration context

The untouched test session has:

- mean NH3 concentration: 157.14 ppm;
- mean H2 concentration: 186.51 ppm; and
- full measurement range: 0–500 ppm.

For the best full-budget fine-tuned model:

| Gas | MAE | MAE / mean concentration | MAE / 500 ppm full scale | R² |
|---|---:|---:|---:|---:|
| NH3 | **14.92 ppm** | **9.49%** | **2.98%** | 0.985 |
| H2 | **29.16 ppm** | **15.63%** | **5.83%** | 0.941 |

The error percentage relative to mean concentration is the more practical
normalization. Full-scale percentages appear smaller because many evaluated
concentrations are well below 500 ppm. Conventional MAPE was not used because
the dataset contains zero-concentration targets.

At the full budget, averaged across repeats:

- mixed-gas exposures: 15.44 ppm NH3 and 33.87 ppm H2 MAE;
- pure-gas exposures: 13.80 ppm NH3 and 19.03 ppm H2 MAE.

H2 prediction is therefore more difficult in mixtures than in pure-gas
measurements.

## Interpretation

### Transfer is most valuable for label efficiency

The central benefit is not merely the final full-data score. With only 20 of
57 possible labeled pairs, the frozen representation achieved:

- 26.61 ppm NH3 MAE, or 16.93% of the test mean;
- 40.93 ppm H2 MAE, or 21.94% of the test mean.

This is substantially better than scratch at the same budget and approaches
the performance obtained with many more labels.

### Frozen versus fine-tuned transfer

Fine-tuning is preferable at 5, 10, 40, and 57 pairs. Frozen transfer is
slightly better at 20 pairs. A practical training policy is:

- freeze most or all of the encoder below approximately 20 labeled pairs;
- progressively unfreeze the encoder once 40 or more calibration pairs are
  available.

### Same-device pretraining solves the earlier mismatch

Frozen CO/ethylene representations previously worsened NH3/H2 error. Here,
frozen transfer generally improves it. The important difference is that the
self-supervised source recordings use the same 20 sensors, channel identities,
normalization, and acquisition dynamics as the target session.

## Limitations

1. Only session 6 served as the final test session. The experiment establishes
   transfer to that session, not every possible future session.
2. Three repeated subset/training seeds quantify some variability, but they
   are not six independent held-out-session trials.
3. Session boundaries were inferred from the documented six repetitions and
   sequential combination IDs; the workbook has no explicit session column.
4. The first 64 samples were used. Longer windows or response/recovery phases
   may improve H2 prediction.
5. Farthest-point selection assumes the calibration concentrations can be
   chosen deliberately. Randomly available labels may perform worse,
   particularly at budgets of 5 or 10.
6. The study estimates error for a new measurement session from the same
   device. Transfer to another physical device requires a separate
   device-domain evaluation.

## Recommended next experiment

Run leave-one-session-out evaluation six times:

1. hold one complete session out for testing;
2. pretrain without labels on four of the remaining sessions;
3. adapt on a small labeled subset from the fifth session; and
4. repeat until every session has been the test session.

This would separate the transfer benefit from the difficulty of a particular
session and provide six independent session-level results. For deployment, use
the frozen encoder around a 20-pair calibration budget and fine-tune it when
40–57 representative calibration pairs are available.

## Reproducibility

- Random base seed: 42
- Repeated-run seeds: 42, 142, 242
- Pretraining epochs: 60
- Supervised epochs: 120
- Pretraining data: 1,260 augmented unlabeled windows
- Test data: 63 independent offset-zero exposure windows
- Runtime: 295.5 seconds
- Pretrained weights: `pretrained_encoder.pt`
- Scaling parameters: `scaler.npz`
- Complete numeric results: `results.json`
- Per-exposure predictions: `predictions.csv`
- Executable experiment: `same_device_session_transfer.py`
