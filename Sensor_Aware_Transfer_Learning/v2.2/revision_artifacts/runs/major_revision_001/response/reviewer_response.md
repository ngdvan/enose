# Point-by-point reviewer response

Status: full rerun artifacts available; hardware metadata and journal layout still require author review.

Comment summaries below paraphrase the supplied reviewer PDF. Original text is preserved in the environment snapshot.

### Major 1

> The premise is not tested; drop language implying reduced calibration cost.

**Response:**
We restrict the claim to reduced labeled-calibration requirements. Existing labels are withheld during SSL; reduced exposure-generation cost is not demonstrated.

**Changes made:**
- We restrict the claim to reduced labeled-calibration requirements. Existing labels are withheld during SSL; reduced exposure-generation cost is not demonstrated.

**New result / status:**
Scope correction; no cost experiment is claimed.

**Location in manuscript:**
Abstract; I; VI

### Major 2

> Pre-register one adaptation policy or select it using adaptation validation.

**Response:**
Fine-tuning is predefined for every target. All policies share the same adaptation holdout, and scratch/frozen/fine-tuned results are retained separately.

**Changes made:**
- Fine-tuning is predefined for every target. All policies share the same adaptation holdout, and scratch/frozen/fine-tuned results are retained separately.

**New result / status:**
See Table 1 and policy_selection/primary_policy_results.csv.

**Location in manuscript:**
III; V.B; Tables 1–2

### Major 3

> Use at least 10 seeds and error bars on budget and ablation results.

**Response:**
The revised protocol uses independent pretraining and adaptation for all ten seeds; budget, baseline, and ablation tables report seed SD.

**Changes made:**
- The revised protocol uses independent pretraining and adaptation for all ten seeds; budget, baseline, and ablation tables report seed SD.

**New result / status:**
See tables and protocol.json; partial runs are not final evidence.

**Location in manuscript:**
IV; V.C; V.F; Tables 2, 4–5

### Major 4

> Promote multi-fold validation to the primary result.

**Response:**
Six held-partition NH3/H2 folds and three rolling chronological CO/ethylene folds lead the Results. The paired bootstrap resamples seed/fold effects instead of pooling repeated predictions.

**Changes made:**
- Six held-partition NH3/H2 folds and three rolling chronological CO/ethylene folds lead the Results. The paired bootstrap resamples seed/fold effects instead of pooling repeated predictions.

**New result / status:**
Table 1 supplies differences, intervals, relative changes, across-fold SD, and paired counts.

**Location in manuscript:**
Abstract; V.B; Table 1

### Major 5

> Partition 10 may be a null; add a fitting-mean constant predictor.

**Response:**
We add a constant predictor fitted only on the adaptation fitting labels, per-gas and macro normalized errors, and paired partition-10 intervals. Wording follows the interval rather than a small mean difference.

**Changes made:**
- We add a constant predictor fitted only on the adaptation fitting labels, per-gas and macro normalized errors, and paired partition-10 intervals. Wording follows the interval rather than a small mean difference.

**New result / status:**
See Table 8 and sensor_drift/partition10_statistics.csv.

**Location in manuscript:**
V.G; Tables 7–8

### Major 6

> Add a sensor-agnostic SSL and a chemometric baseline; define tree features.

**Response:**
We implement a compact PatchTST-style masked channel-independent Transformer without sensor-ID embeddings, plus adaptation-tuned PLSR and RBF SVR. Trees are rerun with explicit flattened-window inputs.

**Changes made:**
- We implement a compact PatchTST-style masked channel-independent Transformer without sensor-ID embeddings, plus adaptation-tuned PLSR and RBF SVR. Trees are rerun with explicit flattened-window inputs.

**New result / status:**
See Table 4, ssl_baselines/proposed_vs_generic_ssl.csv, and baseline feature documentation.

**Location in manuscript:**
II; V.E; Table 4

### Major 7

> The selection is calibration design; add random selection.

**Response:**
We use the term farthest-point calibration design and cross random/farthest designs with scratch/fine-tuned training over all fixed-split budgets.

**Changes made:**
- We use the term farthest-point calibration design and cross random/farthest designs with scratch/fine-tuned training over all fixed-split budgets.

**New result / status:**
See Table 3 and calibration_design/paired_design_statistics.csv.

**Location in manuscript:**
III; V.D; Table 3

### Major 8

> State sensor-ID array dependence and cross-device limitation.

**Response:**
We explicitly limit scope to same-system transfer. No compatible cross-device acquisition was established, so we do not force an invalid array-remapping experiment.

**Changes made:**
- We explicitly limit scope to same-system transfer. No compatible cross-device acquisition was established, so we do not force an invalid array-remapping experiment.

**New result / status:**
No cross-device result is claimed.

**Location in manuscript:**
VI

### Major 9

> Characterize the private array, environmental conditions, and window placement.

**Response:**
We document every unavailable hardware/environment field without inventing values. Four 64-sample window definitions are evaluated. Laboratory metadata and acquisition independence still require author-supplied records.

**Changes made:**
- We document every unavailable hardware/environment field without inventing values. Four 64-sample window definitions are evaluated. Laboratory metadata and acquisition independence still require author-supplied records.

**New result / status:**
Table 6 gives sensitivity; hardware completeness remains unresolved.

**Location in manuscript:**
IV; V.F; Table 6; hardware/private_array_metadata.md

### Moderate: CO

> Acknowledge weak CO quantitative performance.

**Response:**
We retain CO R2 and tail error and explicitly distinguish average relative improvement from adequate quantitative accuracy.

**Changes made:**
- We retain CO R2 and tail error and explicitly distinguish average relative improvement from adequate quantitative accuracy.

**New result / status:**
See the raw-response summary and statistics/q90_all_policies.csv.

**Location in manuscript:**
V.H

### Moderate: conformal

> State the exchangeability violation or use a shift-aware method.

**Response:**
We explicitly state that chronological/session shift violates exchangeability and interpret earlier intervals as diagnostic. Earlier coverage percentages are not presented as rerun evidence.

**Changes made:**
- We explicitly state that chronological/session shift violates exchangeability and interpret earlier intervals as diagnostic. Earlier coverage percentages are not presented as rerun evidence.

**New result / status:**
No new guaranteed coverage result is claimed.

**Location in manuscript:**
V.H

### Moderate: component variability

> Explain sensor-identity variability and add error bars.

**Response:**
The component comparison includes seed SD; gas-dependent effects cannot distinguish sensing selectivity from sampling variability.

**Changes made:**
- The component comparison includes seed SD; gas-dependent effects cannot distinguish sensing selectivity from sampling variability.

**New result / status:**
See Table 5.

**Location in manuscript:**
V.F; VI; Table 5

### Moderate: normalization and target loss

> Report normalized errors and compare log-target versus linear-target objectives.

**Response:**
Per-gas and macro NMAE accompany MAE. The 20-label control compares historical log-Huber, fixed-log Huber, fixed-linear Huber, and fixed-linear MAE; tiny budgets use fixed scaling.

**Changes made:**
- Per-gas and macro NMAE accompany MAE. The 20-label control compares historical log-Huber, fixed-log Huber, fixed-linear Huber, and fixed-linear MAE; tiny budgets use fixed scaling.

**New result / status:**
See sensor_drift_loss/target_transform_comparison.csv and scaling_sensitivity.csv.

**Location in manuscript:**
IV; V.G

### Moderate: size and repeated exposures

> Report parameter counts, effective samples, repeated exposures, and scratch Q0.9.

**Response:**
Every neural job records parameter counts and fitting exposure counts, and every policy records Q0.9. Exposure IDs and signal fingerprints are audited; physical independence remains unverified without logs.

**Changes made:**
- Every neural job records parameter counts and fitting exposure counts, and every policy records Q0.9. Exposure IDs and signal fingerprints are audited; physical independence remains unverified without logs.

**New result / status:**
623 exposure/window fingerprints audited; zero identical fingerprints and zero ID overlap across 11 split definitions.

**Location in manuscript:**
IV; V.H

### Moderate: competing methods and literature

> Reimplement a competing method or published split; expand references.

**Response:**
The PatchTST-style reimplementation is described with its deviations from the published forecasting setup. Ten relevant sources extend the bibliography to 27 references.

**Changes made:**
- The PatchTST-style reimplementation is described with its deviations from the published forecasting setup. Ten relevant sources extend the bibliography to 27 references.

**New result / status:**
The comparison is a matched gas-regression implementation, not a claim of reproducing forecasting scores.

**Location in manuscript:**
II; V.E; References

### Presentation

> Correct wording, keywords, duplicate tables, and unreadable Fig. 3.

**Response:**
The rewritten review draft uses a single all-policy budget table, corrected language and keywords, and vector reconstruction figures with readable fonts; the supplied Fig. 2 is preserved.

**Changes made:**
- The rewritten review draft uses a single all-policy budget table, corrected language and keywords, and vector reconstruction figures with readable fonts; the supplied Fig. 2 is preserved.

**New result / status:**
Final IEEE two-column typesetting and visual proof review remain an author production step.

**Location in manuscript:**
Abstract; V; Figure 3

## Numerical evidence for major comments

Table 1. Primary multi-fold results (ppm).

| Gas | Scratch MAE | Fine-tuned MAE | Paired difference | Relative difference (%) | 95% CI lower | 95% CI upper | Across-fold SD | Paired predictions |
|---|---|---|---|---|---|---|---|---|
| CO | 89.95 | 65.22 | 24.74 | 27.50 | 12.85 | 37.53 | 14.71 | 1050 |
| Ethylene | 2.61 | 1.94 | 0.67 | 25.73 | 0.25 | 1.14 | 0.45 | 1050 |
| H2 | 49.20 | 38.63 | 10.58 | 21.49 | 3.57 | 18.78 | 10.59 | 3780 |
| NH3 | 31.01 | 26.69 | 4.31 | 13.91 | 0.38 | 8.30 | 11.07 | 3780 |

Table 2. Fixed-split calibration budgets (ppm).

| Gas | Pairs | Policy | MAE mean | MAE SD |
|---|---|---|---|---|
| CO | 5 | fine_tuned | 111.46 | 23.96 |
| Ethylene | 5 | fine_tuned | 3.47 | 1.25 |
| CO | 5 | frozen | 125.10 | 34.73 |
| Ethylene | 5 | frozen | 3.92 | 1.68 |
| CO | 5 | scratch | 163.06 | 47.96 |
| Ethylene | 5 | scratch | 5.23 | 1.47 |
| CO | 10 | fine_tuned | 80.99 | 27.98 |
| Ethylene | 10 | fine_tuned | 2.42 | 0.48 |
| CO | 10 | frozen | 77.08 | 25.00 |
| Ethylene | 10 | frozen | 2.45 | 0.46 |
| CO | 10 | scratch | 156.04 | 27.60 |
| Ethylene | 10 | scratch | 3.61 | 1.42 |
| CO | 20 | fine_tuned | 47.42 | 7.79 |
| Ethylene | 20 | fine_tuned | 1.84 | 0.51 |
| CO | 20 | frozen | 49.96 | 8.66 |
| Ethylene | 20 | frozen | 1.88 | 0.53 |
| CO | 20 | scratch | 89.30 | 39.24 |
| Ethylene | 20 | scratch | 2.47 | 0.74 |
| CO | 24 | fine_tuned | 47.45 | 7.38 |
| Ethylene | 24 | fine_tuned | 1.63 | 0.28 |
| CO | 24 | frozen | 46.81 | 9.60 |
| Ethylene | 24 | frozen | 1.67 | 0.24 |
| CO | 24 | scratch | 63.63 | 10.68 |
| Ethylene | 24 | scratch | 2.15 | 0.36 |
| H2 | 5 | fine_tuned | 128.91 | 16.84 |
| NH3 | 5 | fine_tuned | 86.02 | 34.16 |
| H2 | 5 | frozen | 129.17 | 12.17 |
| NH3 | 5 | frozen | 82.85 | 31.89 |
| H2 | 5 | scratch | 161.51 | 22.40 |
| NH3 | 5 | scratch | 86.39 | 36.11 |
| H2 | 10 | fine_tuned | 81.88 | 19.54 |
| NH3 | 10 | fine_tuned | 38.92 | 4.56 |
| H2 | 10 | frozen | 78.73 | 18.12 |
| NH3 | 10 | frozen | 41.08 | 7.01 |
| H2 | 10 | scratch | 124.16 | 28.13 |
| NH3 | 10 | scratch | 67.52 | 40.50 |
| H2 | 20 | fine_tuned | 48.38 | 9.70 |
| NH3 | 20 | fine_tuned | 29.53 | 2.38 |
| H2 | 20 | frozen | 48.04 | 8.65 |
| NH3 | 20 | frozen | 31.10 | 2.80 |
| H2 | 20 | scratch | 70.73 | 30.45 |
| NH3 | 20 | scratch | 36.84 | 7.89 |
| H2 | 40 | fine_tuned | 41.67 | 2.75 |
| NH3 | 40 | fine_tuned | 25.22 | 2.10 |
| H2 | 40 | frozen | 41.26 | 2.34 |
| NH3 | 40 | frozen | 25.09 | 2.01 |
| H2 | 40 | scratch | 51.53 | 6.60 |
| NH3 | 40 | scratch | 29.86 | 2.74 |
| H2 | 57 | fine_tuned | 31.60 | 2.29 |
| NH3 | 57 | fine_tuned | 17.36 | 1.54 |
| H2 | 57 | frozen | 34.77 | 2.70 |
| NH3 | 57 | frozen | 19.26 | 1.76 |
| H2 | 57 | scratch | 41.20 | 4.27 |
| NH3 | 57 | scratch | 21.59 | 3.25 |

Table 3. Five-pair calibration design (ppm).

| Gas | Pair design | Training | MAE mean | MAE SD |
|---|---|---|---|---|
| CO | farthest | fine_tuned | 111.46 | 23.96 |
| Ethylene | farthest | fine_tuned | 3.47 | 1.25 |
| CO | farthest | scratch | 163.06 | 47.96 |
| Ethylene | farthest | scratch | 5.23 | 1.47 |
| CO | random | fine_tuned | 143.07 | 22.16 |
| Ethylene | random | fine_tuned | 4.32 | 1.68 |
| CO | random | scratch | 179.22 | 31.43 |
| Ethylene | random | scratch | 4.89 | 1.84 |
| H2 | farthest | fine_tuned | 128.91 | 16.84 |
| NH3 | farthest | fine_tuned | 86.02 | 34.16 |
| H2 | farthest | scratch | 161.51 | 22.40 |
| NH3 | farthest | scratch | 86.39 | 36.11 |
| H2 | random | fine_tuned | 143.53 | 30.16 |
| NH3 | random | fine_tuned | 89.75 | 29.49 |
| H2 | random | scratch | 159.51 | 12.93 |
| NH3 | random | scratch | 98.51 | 29.07 |

Table 4. Full-budget baseline comparison (ppm).

| Gas | Model | MAE mean | MAE SD |
|---|---|---|---|
| CO | extra_trees | 90.46 | 7.17 |
| Ethylene | extra_trees | 1.40 | 0.20 |
| CO | fine_tuned | 47.45 | 7.38 |
| Ethylene | fine_tuned | 1.63 | 0.28 |
| CO | generic_ssl | 52.52 | 12.59 |
| Ethylene | generic_ssl | 1.44 | 0.27 |
| CO | plsr | 25.57 | 8.48 |
| Ethylene | plsr | 1.99 | 0.38 |
| CO | scratch | 63.63 | 10.68 |
| Ethylene | scratch | 2.15 | 0.36 |
| CO | svr | 53.01 | 7.26 |
| Ethylene | svr | 2.01 | 0.23 |
| CO | xgboost | 55.90 | 11.13 |
| Ethylene | xgboost | 2.49 | 0.35 |
| H2 | extra_trees | 37.33 | 2.04 |
| NH3 | extra_trees | 21.63 | 1.73 |
| H2 | fine_tuned | 31.60 | 2.29 |
| NH3 | fine_tuned | 17.36 | 1.54 |
| H2 | generic_ssl | 35.18 | 2.74 |
| NH3 | generic_ssl | 16.13 | 1.23 |
| H2 | plsr | 75.50 | 18.25 |
| NH3 | plsr | 28.44 | 4.76 |
| H2 | scratch | 41.20 | 4.27 |
| NH3 | scratch | 21.59 | 3.25 |
| H2 | svr | 31.37 | 4.53 |
| NH3 | svr | 20.74 | 1.62 |
| H2 | xgboost | 48.65 | 2.38 |
| NH3 | xgboost | 26.96 | 4.61 |

Table 5. Ablation (ppm).

| Gas | Variant | MAE mean | MAE SD |
|---|---|---|---|
| CO | fine_tuned | 47.45 | 7.38 |
| Ethylene | fine_tuned | 1.63 | 0.28 |
| CO | no_attention | 57.72 | 6.41 |
| Ethylene | no_attention | 1.49 | 0.22 |
| CO | no_sensor_ids | 52.61 | 10.20 |
| Ethylene | no_sensor_ids | 1.72 | 0.32 |
| CO | no_sensor_mask | 49.28 | 7.96 |
| Ethylene | no_sensor_mask | 1.65 | 0.26 |
| CO | no_temporal_mask | 55.38 | 18.19 |
| Ethylene | no_temporal_mask | 1.61 | 0.47 |
| H2 | fine_tuned | 31.60 | 2.29 |
| NH3 | fine_tuned | 17.36 | 1.54 |
| H2 | no_attention | 33.59 | 2.48 |
| NH3 | no_attention | 14.35 | 1.06 |
| H2 | no_sensor_ids | 36.33 | 3.02 |
| NH3 | no_sensor_ids | 17.30 | 1.85 |
| H2 | no_sensor_mask | 35.95 | 2.69 |
| NH3 | no_sensor_mask | 16.58 | 3.20 |
| H2 | no_temporal_mask | 33.34 | 3.32 |
| NH3 | no_temporal_mask | 19.47 | 2.56 |

Table 6. Window-position sensitivity (ppm).

| Gas | Window | Training | MAE mean | MAE SD |
|---|---|---|---|---|
| H2 | early | fine_tuned | 31.60 | 2.29 |
| NH3 | early | fine_tuned | 17.36 | 1.54 |
| H2 | early | scratch | 41.20 | 4.27 |
| NH3 | early | scratch | 21.59 | 3.25 |
| H2 | full | fine_tuned | 35.75 | 2.46 |
| NH3 | full | fine_tuned | 18.05 | 2.48 |
| H2 | full | scratch | 38.36 | 2.56 |
| NH3 | full | scratch | 20.24 | 1.76 |
| H2 | late | fine_tuned | 51.28 | 4.89 |
| NH3 | late | fine_tuned | 54.75 | 4.40 |
| H2 | late | scratch | 52.12 | 7.87 |
| NH3 | late | scratch | 56.71 | 5.88 |
| H2 | middle | fine_tuned | 35.60 | 3.08 |
| NH3 | middle | fine_tuned | 29.60 | 3.23 |
| H2 | middle | scratch | 33.99 | 4.10 |
| NH3 | middle | scratch | 34.55 | 5.01 |

Table 7. Oracle-class conditional drift regression.

| Partition | Gas | Policy | MAE mean | MAE SD | NMAE mean | NMAE SD |
|---|---|---|---|---|---|---|
| 8 | Acetaldehyde | constant | 11.79 | 7.58 | 0.04 | 0.03 |
| 8 | Acetone | constant | 57.28 | 12.80 | 0.12 | 0.03 |
| 8 | Ammonia | constant | 17.06 | 4.97 | 0.02 | 0.01 |
| 8 | Ethanol | constant | 77.11 | 7.16 | 0.13 | 0.01 |
| 8 | Ethylene | constant | 94.67 | 11.81 | 0.33 | 0.04 |
| 8 | Toluene | constant | 59.57 | 6.19 | 0.63 | 0.07 |
| 8 | Acetaldehyde | fine_tuned | 16.40 | 7.04 | 0.06 | 0.02 |
| 8 | Acetone | fine_tuned | 33.23 | 1.62 | 0.07 | 0.00 |
| 8 | Ammonia | fine_tuned | 31.75 | 8.84 | 0.03 | 0.01 |
| 8 | Ethanol | fine_tuned | 2.87 | 3.09 | 0.00 | 0.01 |
| 8 | Ethylene | fine_tuned | 14.63 | 4.06 | 0.05 | 0.01 |
| 8 | Toluene | fine_tuned | 17.82 | 7.90 | 0.19 | 0.08 |
| 8 | Acetaldehyde | frozen | 13.44 | 3.77 | 0.05 | 0.01 |
| 8 | Acetone | frozen | 31.53 | 1.41 | 0.06 | 0.00 |
| 8 | Ammonia | frozen | 30.10 | 8.50 | 0.03 | 0.01 |
| 8 | Ethanol | frozen | 3.48 | 3.28 | 0.01 | 0.01 |
| 8 | Ethylene | frozen | 16.43 | 3.21 | 0.06 | 0.01 |
| 8 | Toluene | frozen | 19.55 | 6.72 | 0.21 | 0.07 |
| 8 | Acetaldehyde | scratch | 20.21 | 11.03 | 0.07 | 0.04 |
| 8 | Acetone | scratch | 32.11 | 1.93 | 0.07 | 0.00 |
| 8 | Ammonia | scratch | 38.91 | 12.96 | 0.04 | 0.01 |
| 8 | Ethanol | scratch | 6.22 | 3.63 | 0.01 | 0.01 |
| 8 | Ethylene | scratch | 17.30 | 5.68 | 0.06 | 0.02 |
| 8 | Toluene | scratch | 28.96 | 6.90 | 0.30 | 0.07 |
| 9 | Acetaldehyde | constant | 10.05 | 7.51 | 0.03 | 0.03 |
| 9 | Acetone | constant | 24.91 | 13.28 | 0.05 | 0.03 |
| 9 | Ammonia | constant | 10.50 | 6.96 | 0.01 | 0.01 |
| 9 | Ethanol | constant | 77.11 | 7.16 | 0.13 | 0.01 |
| 9 | Ethylene | constant | 94.67 | 11.81 | 0.33 | 0.04 |
| 9 | Toluene | constant | 59.57 | 6.19 | 0.63 | 0.07 |
| 9 | Acetaldehyde | fine_tuned | 29.07 | 8.48 | 0.10 | 0.03 |
| 9 | Acetone | fine_tuned | 22.19 | 6.21 | 0.05 | 0.01 |
| 9 | Ammonia | fine_tuned | 16.53 | 9.71 | 0.02 | 0.01 |
| 9 | Ethanol | fine_tuned | 2.39 | 2.65 | 0.00 | 0.00 |
| 9 | Ethylene | fine_tuned | 12.28 | 4.36 | 0.04 | 0.02 |
| 9 | Toluene | fine_tuned | 28.65 | 11.03 | 0.30 | 0.12 |
| 9 | Acetaldehyde | frozen | 29.77 | 4.49 | 0.10 | 0.02 |
| 9 | Acetone | frozen | 23.19 | 5.32 | 0.05 | 0.01 |
| 9 | Ammonia | frozen | 17.62 | 8.69 | 0.02 | 0.01 |
| 9 | Ethanol | frozen | 2.44 | 2.87 | 0.00 | 0.00 |
| 9 | Ethylene | frozen | 12.71 | 3.98 | 0.04 | 0.01 |
| 9 | Toluene | frozen | 27.73 | 7.11 | 0.29 | 0.07 |
| 9 | Acetaldehyde | scratch | 30.22 | 8.42 | 0.10 | 0.03 |
| 9 | Acetone | scratch | 22.35 | 4.69 | 0.05 | 0.01 |
| 9 | Ammonia | scratch | 21.34 | 13.22 | 0.02 | 0.01 |
| 9 | Ethanol | scratch | 2.00 | 2.16 | 0.00 | 0.00 |
| 9 | Ethylene | scratch | 13.59 | 5.25 | 0.05 | 0.02 |
| 9 | Toluene | scratch | 46.58 | 13.62 | 0.49 | 0.14 |
| 10 | Acetaldehyde | constant | 76.54 | 2.66 | 0.26 | 0.01 |
| 10 | Acetone | constant | 408.40 | 8.85 | 0.84 | 0.02 |
| 10 | Ammonia | constant | 415.97 | 7.50 | 0.44 | 0.01 |
| 10 | Ethanol | constant | 78.13 | 2.39 | 0.13 | 0.00 |
| 10 | Ethylene | constant | 74.27 | 1.49 | 0.26 | 0.01 |
| 10 | Toluene | constant | 33.02 | 2.06 | 0.35 | 0.02 |
| 10 | Acetaldehyde | fine_tuned | 70.15 | 6.78 | 0.24 | 0.02 |
| 10 | Acetone | fine_tuned | 298.21 | 62.08 | 0.61 | 0.13 |
| 10 | Ammonia | fine_tuned | 341.99 | 29.11 | 0.36 | 0.03 |
| 10 | Ethanol | fine_tuned | 63.48 | 5.29 | 0.11 | 0.01 |
| 10 | Ethylene | fine_tuned | 63.00 | 10.18 | 0.22 | 0.04 |
| 10 | Toluene | fine_tuned | 21.48 | 4.35 | 0.23 | 0.05 |
| 10 | Acetaldehyde | frozen | 72.39 | 4.36 | 0.25 | 0.02 |
| 10 | Acetone | frozen | 285.49 | 63.18 | 0.59 | 0.13 |
| 10 | Ammonia | frozen | 316.10 | 48.02 | 0.33 | 0.05 |
| 10 | Ethanol | frozen | 65.16 | 5.24 | 0.11 | 0.01 |
| 10 | Ethylene | frozen | 59.67 | 5.23 | 0.21 | 0.02 |
| 10 | Toluene | frozen | 25.75 | 6.08 | 0.27 | 0.06 |
| 10 | Acetaldehyde | scratch | 64.32 | 10.02 | 0.22 | 0.03 |
| 10 | Acetone | scratch | 318.77 | 21.20 | 0.65 | 0.04 |
| 10 | Ammonia | scratch | 341.17 | 47.66 | 0.36 | 0.05 |
| 10 | Ethanol | scratch | 62.47 | 9.20 | 0.11 | 0.02 |
| 10 | Ethylene | scratch | 51.07 | 7.13 | 0.18 | 0.02 |
| 10 | Toluene | scratch | 16.23 | 4.84 | 0.17 | 0.05 |

Table 8. Partition 10 paired seed uncertainty (ppm).

| Policy | MacroMAE difference | 95% CI lower | 95% CI upper |
|---|---|---|---|
| frozen | 4.91 | -2.47 | 12.41 |
| fine_tuned | -0.71 | -8.40 | 6.91 |

Table 9. Full-budget quantitative and tail metrics (errors in ppm).

| Gas | Policy | Mean R2 | Mean RMSE | Mean Q0.9 |
|---|---|---|---|---|
| CO | fine_tuned | 0.78 | 72.93 | 109.51 |
| Ethylene | fine_tuned | 0.74 | 2.48 | 4.13 |
| CO | frozen | 0.77 | 73.58 | 110.76 |
| Ethylene | frozen | 0.75 | 2.46 | 3.70 |
| CO | scratch | 0.62 | 94.89 | 162.79 |
| Ethylene | scratch | 0.56 | 3.26 | 5.77 |
| H2 | fine_tuned | 0.93 | 42.90 | 74.15 |
| NH3 | fine_tuned | 0.98 | 23.29 | 38.11 |
| H2 | frozen | 0.93 | 46.01 | 78.41 |
| NH3 | frozen | 0.97 | 25.57 | 44.64 |
| H2 | scratch | 0.88 | 57.78 | 96.54 |
| NH3 | scratch | 0.96 | 31.16 | 48.79 |

Table 10. Model size and effective supervised sample count; seed 42 exemplifies the fixed architecture and holdout sizes.

| Dataset | Pairs | Model | Total parameters | Trainable parameters | Encoder | Head | Fitting exposures | Parameters/exposure |
|---|---|---|---|---|---|---|---|---|
| co_ethylene | 24 | fine_tuned | 101002 | 101002 | 31144 | 69858 | 19 | 5315.89 |
| co_ethylene | 24 | frozen | 101002 | 69858 | 31144 | 69858 | 19 | 5315.89 |
| co_ethylene | 24 | generic_ssl | 91714 | 91714 | 21856 | 69858 | 19 | 4827.05 |
| co_ethylene | 24 | scratch | 101002 | 101002 | 31144 | 69858 | 19 | 5315.89 |
| co_ethylene | 5 | fine_tuned | 101002 | 101002 | 31144 | 69858 | 4 | 25250.50 |
| co_ethylene | 5 | frozen | 101002 | 69858 | 31144 | 69858 | 4 | 25250.50 |
| co_ethylene | 5 | generic_ssl | 91714 | 91714 | 21856 | 69858 | 4 | 22928.50 |
| co_ethylene | 5 | scratch | 101002 | 101002 | 31144 | 69858 | 4 | 25250.50 |
| nh3_h2 | 57 | fine_tuned | 117514 | 117514 | 31272 | 86242 | 46 | 2554.65 |
| nh3_h2 | 57 | frozen | 117514 | 86242 | 31272 | 86242 | 46 | 2554.65 |
| nh3_h2 | 57 | generic_ssl | 108098 | 108098 | 21856 | 86242 | 46 | 2349.96 |
| nh3_h2 | 57 | scratch | 117514 | 117514 | 31272 | 86242 | 46 | 2554.65 |
| nh3_h2 | 5 | fine_tuned | 117514 | 117514 | 31272 | 86242 | 4 | 29378.50 |
| nh3_h2 | 5 | frozen | 117514 | 86242 | 31272 | 86242 | 4 | 29378.50 |
| nh3_h2 | 5 | generic_ssl | 108098 | 108098 | 21856 | 86242 | 4 | 27024.50 |
| nh3_h2 | 5 | scratch | 117514 | 117514 | 31272 | 86242 | 4 | 29378.50 |
