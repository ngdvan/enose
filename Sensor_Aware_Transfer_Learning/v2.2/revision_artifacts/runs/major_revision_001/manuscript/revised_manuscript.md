# Sensor-Aware Self-Supervised Transfer Learning for Label-Efficient Multigas Electronic Nose Calibration

## Abstract

We study reduced labeled-calibration requirements for same-system multigas electronic-nose recalibration using masked reconstruction of sensor responses. Pretraining withholds existing exposure labels and does not demonstrate reduced gas-generation cost. A shared temporal encoder, sensor-identity embeddings, and cross-sensor attention are evaluated using a predefined fine-tuned transfer policy and 10 seeds. Primary evidence comes from six held-partition NH3/H2 folds and three chronological CO/ethylene folds. CO: relative MAE change favoring fine-tuning = 27.50%. Ethylene: relative MAE change favoring fine-tuning = 25.73%. H2: relative MAE change favoring fine-tuning = 21.49%. NH3: relative MAE change favoring fine-tuning = 13.91%. Paired uncertainty is reported in Table 1. Fixed-split budgets, random calibration design, classical regression, a PatchTST-style generic SSL control, and window sensitivity qualify the results. Sensor_Drift concentration regression is oracle-class conditional; partition 10 is interpreted using paired uncertainty. The experiments do not establish cross-device transfer or uniformly monotonic budget effects.

Keywords: electronic nose; concentration regression; self-supervised learning; sensor drift; calibration design; transfer learning.

## I. Introduction

Controlled multigas exposures provide quantitative calibration data, but collecting them remains an experimental burden. This study asks whether a previously acquired pool of responses can reduce the number of concentration labels used during later same-system calibration. The pretraining exposures were originally controlled and labeled; withholding their labels is a representation-learning experiment, not evidence that those exposures can be generated more cheaply. The contribution is evaluated through independent adaptation-label budgets and held-out exposure groups. We distinguish representation transfer, calibration-pair design, and chronological robustness.

## II. Related Work

Electronic-nose semi-supervised recognition includes M-Training [1] and M-S4VMs [2]. Drift work spans domain adaptation, few-shot learning, graph-based methods, and meta-learning [3] [4] [5] [6] [7]. Quantitative gas estimation has used dynamic models and temporal feature fusion [8] [9] [10], as well as small-data and cross-gas transfer [11] [12]. Time-series SSL covers several pretext-task families [13]. PatchTST uses shared channel-independent patch Transformers and masked pretraining [18]; TST uses a Transformer representation-learning framework [19], whereas TS2Vec learns hierarchical contrastive representations [20]. We implement a compact PatchTST-style control rather than treating internal sensor-ID ablation as the generic SSL baseline.

Classical controls include partial least-squares regression [21], support-vector regression [22], Extra Trees [26], and XGBoost [27]. Minimal-experiment sensor-array calibration [14] and space-covering experimental design [23] motivate the farthest-point control. Conformal prediction under nonexchangeability [24] and covariate shift [25] explain why ordinary split-conformal guarantees cannot be transferred directly to the present chronological deployment setting.

## III. Method

For a 64-by-S response window X, the same dilated temporal CNN processes each sensor signal and observation mask. Three convolutional layers have widths 24, 32, and 32, kernels 5, 5, and 3, and dilations 1, 2, and 4. Mean and maximum temporal pooling are concatenated and projected to a 32-dimensional token. A learned physical channel embedding is added before two four-head cross-sensor Transformer layers with 96-unit feed-forward sublayers. The supervised head maps flattened sensor tokens through widths 128 and 32 to two concentration outputs.

The pretext loss is masked-entry MSE plus 0.05 times visible-entry MSE. Masking removes temporal spans and entire sensor channels. AdamW uses 60 pretraining epochs for raw responses. Supervised adaptation uses 120 epochs and Huber loss on fixed-scale targets, with delta 0.1. Scratch starts with a random encoder; frozen transfer updates only the head; fine-tuning uses encoder and head learning rates of 0.00008 and 0.0008. Fine-tuning is predefined as the primary transfer policy for every gas. Each seed selects a common exposure-group adaptation holdout; only that holdout selects checkpoints.

Farthest-point calibration design sequentially maximizes minimum distance in normalized concentration coordinates. The initial pair is seeded randomly, and both farthest and random designs select unique concentration pairs. These coordinates are assumed known during experimental design. The procedure is not label acquisition from an unknown concentration pool. Random design uses the same budgets and seed list. Both designs are evaluated with scratch and fine-tuned training to separate design and transfer effects.

## IV. Data and Evaluation Protocol

The private NH3/H2 workbook contains 20 response channels, 378 exposure identifiers, and six consecutive partitions inferred from groups of 63 identifiers. These partitions must not be called verified acquisition days. The primary protocol holds out each partition in turn, uses its preceding cyclic partition for adaptation, and uses the remaining four for label-free pretraining. This evaluates held-partition generalization; some pretraining partitions occur after the held-out partition, so the six-fold analysis is not a prospective forecasting experiment. The secondary fixed split uses partitions 1–4, 5, and 6 for pretraining, adaptation, and test. Budgets are 5, 10, 20, 40, and 57 pairs.

The public dynamic gas mixture dataset [15] supplies 16 channels and 245 cached exposure groups. The primary protocol divides acquisition order into seven blocks and uses three rolling pretrain–adapt–test folds, with three pretraining blocks followed by one adaptation and one test block. Full coverage is the number of available unique adaptation pairs in each fold. The secondary five-block protocol uses the first three blocks, fourth block, and fifth block respectively; budgets are 5, 10, 20, and 24 pairs.

Pretraining robust scalers use response values only. All five offset windows from each fitting exposure remain in the same role, and tests use one window per exposure. Every adaptation budget includes both fitting and held-out labels. An audit of 623 identified exposures/windows found no identical signal fingerprints and no exposure-ID overlap in 11 split definitions. Distinct identifiers do not independently verify physical acquisition independence; laboratory logs remain necessary. The CO/ethylene fingerprint audit covers cached windows, not complete raw traces.

The private-array manufacturer, sensing material, heater settings, physical baseline convention, sampling rate, chamber/flow details, ambient temperature, relative humidity and its control, and concentration-reference accuracy were unavailable in the inspected acquisition records. This limits reproducibility and precludes attributing sensor-ID effects to sensing chemistry. Sample count is not converted into elapsed seconds. The 0–500 ppm calibration setting is not validation of low-concentration ambient environmental monitoring.

The Sensor_Drift concentration dataset [16] and drift-compensation literature [17] motivate the descriptor extension. Pretraining uses partitions 1–6, adaptation uses partition 7, and tests are partitions 8–10. Six concentration heads are selected by the true gas identity. This oracle-class conditional problem does not include gas-classification error. The constant control predicts the per-gas fitting-subset mean. Budgets are 1, 2, 5, 10, and 20 labels/gas. One label/gas uses a fixed final checkpoint because no disjoint holdout is possible. Smaller budgets use log1p targets divided by log1p(1000), a predefined unit scale. At 20 labels/gas, the historical per-gas fitting-subset log standardization is compared with fixed-log scaling, linear targets divided by 1000 with Huber loss, and the same linear scale with MAE loss.

All principal experiments use 10 seeds: 42, 142, 242, 342, 442, 542, 642, 742, 842, and 942. Pretraining is rerun per seed. We report MAE, RMSE, R2, and Q0.9 of absolute errors. Per-gas drift NMAE is MAE divided by the historical concentration range in partitions 1–6; these reference labels are used only for reporting, not pretraining, fitting or selection. Some test-partition gas ranges are zero, so a fixed historical reference permits normalization of all six gases. MacroMAE and macro-NMAE weight gases equally. Paired 95% bootstrap intervals resample seed and fold indices independently with equal fold weights, using 5000 replicates. They are conditional on observed test exposures; shared training partitions and the small number of folds limit population inference. We do not pool repeated predictions as independent observations.

## V. Results

### V.A. Self-Supervised Pretraining

Reconstruction curves are supporting optimization diagnostics, not evidence of concentration accuracy. Figure 3 shows mean loss with one seed standard deviation; the architecture and split schematic from the supplied Figure 2 is preserved.

Figure 3. Masked-reconstruction pretraining with 10 seeds; 60 epochs for raw responses and 40 for Sensor_Drift. Shading denotes seed SD. Vector PDF/SVG use print-size labels.

### V.B. Primary Multi-Fold Validation

Table 1 is the primary generalization evidence. Positive differences favor the predefined fine-tuned policy. Across-fold SD describes variation of fold means, and paired-prediction counts include repeated seeds rather than claiming that all repetitions are independent exposures.

Table 1. Primary multi-fold results (ppm).

| Gas | Scratch MAE | Fine-tuned MAE | Paired difference | Relative difference (%) | 95% CI lower | 95% CI upper | Across-fold SD | Paired predictions |
|---|---|---|---|---|---|---|---|---|
| CO | 89.95 | 65.22 | 24.74 | 27.50 | 12.85 | 37.53 | 14.71 | 1050 |
| Ethylene | 2.61 | 1.94 | 0.67 | 25.73 | 0.25 | 1.14 | 0.45 | 1050 |
| H2 | 49.20 | 38.63 | 10.58 | 21.49 | 3.57 | 18.78 | 10.59 | 3780 |
| NH3 | 31.01 | 26.69 | 4.31 | 13.91 | 0.38 | 8.30 | 11.07 | 3780 |

### V.C. Fixed-Split Label-Budget Analysis

Table 2 reports all policies without selecting among them using test errors. Means and SD quantify variation across 10 seeds. Label-budget effects need not be monotonic for each gas, and the fixed split is secondary to Table 1.

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

### V.D. Calibration-Design Control

Both random and farthest-point designs are crossed with scratch and fine-tuned training. The factorial summary and paired design statistics are supplied with all budgets in the reproducibility artifacts. Table 3 shows the low-budget control; the design intervention requires known concentration coordinates and does not establish active selection of unlabeled ambient observations.

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

### V.E. Baseline Comparison

Table 4 reports full-budget results; the supplement includes every low and medium budget. PLSR, RBF SVR, Extra Trees, and XGBoost receive flattened scaled 64-sample windows (1280 or 1024 features). PLSR and SVR additionally standardize fitting features and tune hyperparameters using adaptation-only validation. The revised tree comparison is rerun with this explicit common representation, rather than reusing historical engineered-feature scores. The generic control is a compact PatchTST-style reimplementation with eight length-8 patches, a shared channel-independent encoder, temporal positions, and no physical sensor embeddings. Three patches per channel are masked. A matched supervised head retains channel ordering. It is not an exact reproduction of published forecasting settings; instance normalization is omitted to match preprocessing and preserve absolute response information. Encoder capacity differs and is reported in the model-size artifact.

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

### V.F. Ablation and Window Sensitivity

Table 5 gives full-budget architectural ablations with seed uncertainty. Gas-dependent sensor-identity effects may reflect selectivity, sampling variability, or both; the current design cannot separate these explanations. Early, middle, late, and full-exposure-resampled 64-sample definitions are compared in Table 6 under fixed exposure roles and full calibration budgets. The early window remains the predefined primary protocol; the sensitivity study does not retroactively select a test-optimal window.

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

### V.G. Long-Term Drift

Table 7 gives per-gas errors and normalized errors for the 20-label historical target transform, including the constant fitting-mean control. All budgets, macro errors, and loss/scaling comparisons are supplied as CSVs. The loss/scaling study is a sensitivity analysis, not test-based selection of a replacement primary model. A mean difference alone is insufficient to establish useful transfer under severe drift.

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

For partition 10, the paired interval includes zero: **no clear improvement**.

### V.H. Tail Error, Model Size, and Uncertainty

Q0.9 is reported for scratch, frozen, and fine-tuned policies in the accompanying statistics CSV, alongside total, encoder, head, and trainable parameter counts and parameters per fitting exposure. Five overlapping windows do not multiply the effective independent supervised sample count. CO remains a particularly important quantitative limitation: evaluate its R2 and tail error alongside MAE, rather than equating an average relative gain with adequate calibration accuracy.

Standard split-conformal coverage relies on exchangeability between calibration and test residuals. The chronological/session shift in this study violates that assumption. Intervals from the earlier split-conformal analysis are therefore diagnostic rather than guaranteed coverage intervals under deployment shift. The revision does not present the earlier coverage percentages as new 10-seed measurements; shift-aware methods [24] [25] remain future work.

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

## VI. Discussion and Limitations

The primary evidence is the multi-fold comparison with a single predefined fine-tuned policy. Single-split improvements and favorable target-specific frozen scores must not replace that evidence. The added generic SSL control tests whether the particular sensor-aware architecture is useful beyond masked patch learning; it does not isolate sensor identity alone because the encoders differ. The ablation supplies the narrower component control. Low-budget outcomes must be interpreted jointly with calibration design and the number of actual fitting exposures.

Physical sensor embeddings are tied to the array layout. These experiments support evaluation of same-system recalibration only and do not demonstrate cross-device transfer. A valid future cross-device experiment would require compatible arrays, meaningful channel correspondence, and a documented embedding-remapping or reinitialization strategy. Missing hardware/environment records restrict mechanistic interpretation. The same limitation applies to larger apparent H2 identity effects relative to NH3: sampling variability is an alternative explanation.

Severe drift can erase or reverse transfer advantages. Partition-specific intervals and the fitting-mean control should govern interpretation, especially in partition 10. Domain alignment and shift-aware uncertainty are hypotheses for future evaluation, not demonstrated remedies in this experiment. The work measures requirements for labels used in adaptation, not savings in physical gas generation.

## References

[1] P. Jia, T. Huang, S. Duan, L. Ge, J. Yan, and L. Wang, “A novel semi-supervised electronic nose learning technique: M-Training,” Sensors, vol. 16, no. 3, Art. no. 370, 2016, doi: 10.3390/s16030370.

[2] T. Huang, P. Jia, P. He, S. Duan, J. Yan, and L. Wang, “A novel semi-supervised method of electronic nose for indoor pollution detection trained by M-S4VMs,” Sensors, vol. 16, no. 9, Art. no. 1462, 2016, doi: 10.3390/s16091462.

[3] Y. Zhang et al., “TDACNN: Target-domain-free domain adaptation convolutional neural network for drift compensation in gas sensors,” Sensors and Actuators B: Chemical, vol. 361, Art. no. 131739, 2022, doi: 10.1016/j.snb.2022.131739.

[4] Y. Tian et al., “Metric Network for E-Nose Drift Compensation: Few-Shot Learning for Robust Gas Sensing,” IEEE Sensors Journal, vol. 25, no. 9, 2025, doi: 10.1109/JSEN.2025.3553376.

[5] Y. Heng et al., “An electronic nose drift compensation algorithm based on semi-supervised adversarial domain adaptive convolutional neural network,” Sensors and Actuators B: Chemical, vol. 422, Art. no. 136642, 2025, doi: 10.1016/j.snb.2024.136642.

[6] Y. Tian, Y. Sun, and S. Zhang, “CEGNN: Contrastive edge labeling graph neural network for sensor drift adaptation in electronic noses,” Sensors and Actuators B: Chemical, vol. 445, Art. no. 138470, 2025, doi: 10.1016/j.snb.2025.138470.

[7] V. K. Gupta et al., “Target-Domain Data Free Model-Agnostic-Meta-Learning Framework for Time-Varying Drift Correction for E-Nose,” IEEE Sensors Letters, vol. 9, no. 8, 2025, doi: 10.1109/LSENS.2025.3591494.

[8] J. Fonollosa, S. Sheik, R. Huerta, and S. Marco, “Reservoir computing compensates slow response of chemosensor arrays exposed to fast varying gas concentrations in continuous monitoring,” Sensors and Actuators B: Chemical, vol. 215, pp. 618–629, 2015, doi: 10.1016/j.snb.2015.03.028.

[9] W. Ni et al., “Multi-task deep learning model for quantitative volatile organic compounds analysis by feature fusion of electronic nose sensing,” Sensors and Actuators B: Chemical, vol. 417, Art. no. 136206, 2024, doi: 10.1016/j.snb.2024.136206.

[10] Z. Tang et al., “Discrimination of VOCs with e-nose consisting of a single MEMS sensor using lightweight deep learning model based on SqueezeNet,” Sensors and Actuators B: Chemical, vol. 422, Art. no. 136640, 2025, doi: 10.1016/j.snb.2024.136640.

[11] X. Xia et al., “The parameter-feature-based transfer learning for mixed gas monitoring under small datasets,” Sensors and Actuators B: Chemical, vol. 441, Art. no. 137975, 2025, doi: 10.1016/j.snb.2025.137975.

[12] H. Mei et al., “A semi-supervised domain adaptation for cross-gas concentration prediction with multi-target and bidirectional transfer for E-nose system,” Sensors and Actuators B: Chemical, vol. 450, Art. no. 139242, 2026, doi: 10.1016/j.snb.2025.139242.

[13] K. Zhang et al., “Self-Supervised Learning for Time Series Analysis: Taxonomy, Progress, and Prospects,” IEEE Transactions on Pattern Analysis and Machine Intelligence, vol. 46, no. 10, pp. 6775–6794, 2024, doi: 10.1109/TPAMI.2024.3387317.

[14] I. Rodriguez-Lujan, J. Fonollosa, A. Vergara, M. L. Homer, and R. Huerta, “On the calibration of sensor arrays for pattern recognition using the minimal number of experiments,” Chemometrics and Intelligent Laboratory Systems, vol. 130, pp. 123–134, 2014, doi: 10.1016/j.chemolab.2013.10.012.

[15] J. Fonollosa, “Gas sensor array under dynamic gas mixtures,” UCI Machine Learning Repository, 2015, doi: 10.24432/C5WP4C.

[16] A. Vergara, “Gas Sensor Array Drift at Different Concentrations,” UCI Machine Learning Repository, 2012, doi: 10.24432/C5MK6M.

[17] A. Vergara, S. Vembu, T. Ayhan, M. A. Ryan, M. L. Homer, and R. Huerta, “Chemical gas sensor drift compensation using classifier ensembles,” Sensors and Actuators B: Chemical, vols. 166–167, pp. 320–329, 2012, doi: 10.1016/j.snb.2012.01.074.

[18] Y. Nie, N. H. Nguyen, P. Sinthong, and J. Kalagnanam, "A Time Series is Worth 64 Words: Long-term Forecasting with Transformers," ICLR, 2023. https://arxiv.org/abs/2211.14730

[19] G. Zerveas, S. Jayaraman, D. Patel, A. Bhamidipaty, and C. Eickhoff, "A Transformer-based Framework for Multivariate Time Series Representation Learning," KDD, 2021. https://arxiv.org/abs/2010.02803

[20] Z. Yue et al., "TS2Vec: Towards Universal Representation of Time Series," AAAI, 2022. https://arxiv.org/abs/2106.10466

[21] S. Wold, M. Sjostrom, and L. Eriksson, "PLS-regression: a basic tool of chemometrics," Chemometrics and Intelligent Laboratory Systems, vol. 58, pp. 109–130, 2001. https://doi.org/10.1016/S0169-7439(01)00155-1

[22] A. J. Smola and B. Scholkopf, "A tutorial on support vector regression," Statistics and Computing, vol. 14, pp. 199–222, 2004. https://doi.org/10.1023/B:STCO.0000035301.49549.88

[23] R. W. Kennard and L. A. Stone, "Computer Aided Design of Experiments," Technometrics, vol. 11, pp. 137–148, 1969. https://doi.org/10.1080/00401706.1969.10490666

[24] R. F. Barber, E. J. Candes, A. Ramdas, and R. J. Tibshirani, "Conformal prediction beyond exchangeability," Annals of Statistics, vol. 51, 2023. https://arxiv.org/abs/2202.13415

[25] R. J. Tibshirani, R. F. Barber, E. J. Candes, and A. Ramdas, "Conformal Prediction Under Covariate Shift," NeurIPS, 2019. https://arxiv.org/abs/1904.06019

[26] P. Geurts, D. Ernst, and L. Wehenkel, "Extremely randomized trees," Machine Learning, vol. 63, pp. 3–42, 2006. https://doi.org/10.1007/s10994-006-6226-1

[27] T. Chen and C. Guestrin, "XGBoost: A Scalable Tree Boosting System," KDD, pp. 785–794, 2016. https://arxiv.org/abs/1603.02754
