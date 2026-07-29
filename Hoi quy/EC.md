# Analytics Report: `split-to-5-lstm-co-ethy.ipynb`

## Executive summary

The notebook builds a two-output gas-concentration regressor for CO and ethylene from 16 metal-oxide sensor streams. Its principal pipeline removes zero-gas intervals, identifies contiguous concentration runs, converts each run into augmented 64 × 64 grayscale matrices, compresses them with a convolutional autoencoder (AE), reshapes the 256-dimensional latent vector to a 16-step sequence, and predicts both concentrations with a two-layer LSTM.

The local conversion is `split-to-5-lstm-co-ethy.py`. Full local preprocessing ran successfully and exactly reproduced the notebook's important counts. Neural training could not be rerun because TensorFlow is not installed in the local Python 3.13 environment. Consequently, metrics below are clearly separated into (a) independently reproduced preprocessing facts and (b) results stored in the notebook, which were not independently reproduced locally.

## 1. Pipeline overview

```text
ethylene_CO.txt (4,208,261 × 19)
  → remove missing rows and intervals where both gases are zero
  → identify contiguous constant-concentration measurement runs
  → remove runs shorter than 6,400 samples (~64 s at ~100 Hz)
  → randomly assign 245 retained runs to five disjoint splits
  → Min-Max normalize 16 sensor channels within each split
  → sample 64 readings, one per ~1 s, from every run
  → repeat 16 sensor columns four times → 64 × 64 grayscale image
  → create five offset variants per run → 1,225 images
  → hold out one split; use the other four for training
  → convolutional AE: 64 × 64 × 1 → 256 latent variables
  → reshape latent vector: 256 → 16 timesteps × 16 features
  → two-layer LSTM → normalized [CO, ethylene]
  → inverse scaling → ppm → MAE/MSE/RMSE/NRMSE/R²
```

The notebook also experiments with AE + XGBoost, AE + MLP, direct CNN, a network called “ResNet-8”, SimpleRNN, direct LSTM, patch LSTM, and a Transformer. These are exploratory branches, not one coherent sequential pipeline. The filename emphasizes LSTM, and the most developed five-fold result block is the AE + LSTM branch.

## 2. Processing steps

### 2.1 Input and validation

The local source file is `ethylene_CO.txt` (approximately 643 MB). It contains time, two targets, and 16 sensor readings. The notebook names the first target `CO2 conc (ppm)`, although the dataset filename, plots, and commentary describe it as CO. The local script uses `CO conc (ppm)` to remove this chemical-label ambiguity.

Independent local chunked inspection produced:

| Property                        |  Local result |
| ------------------------------- | ------------: |
| Raw rows                        |     4,208,261 |
| Columns                         |            19 |
| Rows containing a missing value |             0 |
| Both-gases-zero rows            |     1,249,996 |
| Active-gas rows                 |     2,958,265 |
| CO range                        | 0–533.33 ppm |
| Ethylene range                  |     0–20 ppm |

### 2.2 Run construction and filtering

A new run begins whenever either concentration differs from the preceding row. This is the intended meaning of the notebook's `Label`: it identifies a contiguous exposure episode rather than merely a unique concentration pair.

The notebook initially finds 277 active runs and removes 32 runs shorter than 6,400 rows. The threshold assumes approximately 100 samples/s, so 6,400 rows represent roughly 64 seconds. After relabeling, 245 runs and 2,843,566 rows remain. The local preprocessing run reproduced all of these values and the same 32 discarded labels.

One subtlety is important: after short runs are removed, adjacent retained runs with the same concentration can be merged during relabeling. This did not change the reported final count beyond the notebook's observed 245, but a more robust implementation should preserve original episode IDs and avoid silently merging across removed intervals.

### 2.3 Five-way split

The notebook shuffles the 245 run IDs and divides them into five groups of 49. This is better than splitting individual rows because all samples from one exposure episode stay together. The original notebook does not set a random seed, so its split assignment is not reproducible. The converted script uses seed 42.

The notebook calls the groups equal-sized, but they are equal only in number of runs, not duration: the saved notebook shows split row counts from 529,317 to 614,595. Each split nevertheless produces 49 × 5 = 245 augmented images.

### 2.4 Normalization

For each split, the notebook fits a separate Min-Max scaler to all 16 sensor channels:

\[
x'_{s,j}=\frac{x_{s,j}-\min(x_{s,j})}{\max(x_{s,j})-\min(x_{s,j})}.
\]

This maps sensor values to approximately [0, 1]. The approach is problematic for deployment and evaluation because the held-out split supplies its own minima and maxima. It therefore leaks test-distribution information into preprocessing and means identical physical readings can map to different normalized values depending on split.

For targets, the notebook fits `MinMaxScaler` independently to training and test targets, then later inverse-transforms predictions with the test-fitted scaler. A model predicts in the training scaler's coordinate system, so decoding with a different test scaler is mathematically invalid unless both ranges happen to be identical. The local script fixes target scaling by fitting on training targets only and applying that same scaler to validation, test, predictions, and inverse transformation.

### 2.5 Image construction and augmentation

For every retained run, the notebook selects 64 rows with stride 100, yielding a 64 × 16 time-by-sensor matrix spanning about 64 seconds. It repeats each of the 16 sensor columns four times to obtain width 64, quantizes to 8-bit grayscale, and saves a PNG.

Five variants begin at offsets 0, 20, 40, 60, and 80 rows. At approximately 100 Hz these correspond to 0, 0.2, 0.4, 0.6, and 0.8 seconds. Thus the five images overlap almost completely. This is temporal phase-shift augmentation, not five independent observations.

The fourfold column repetition contains no new information; it exists only to make a square image. A 64 × 16 tensor or a sequence model operating directly on time × sensors would be more natural and would avoid artificial spatial correlations.

Local preparation generated `ec_run/prepared.npz` with shape `(1225, 64, 64, 1)`, exactly 245 images per split, plus `ec_run/sample.png` and `ec_run/run_summary.json`.

### 2.6 Train/validation/test handling

In the saved main example, split 4 is the test set and splits 1, 2, 3, and 5 form training, giving 980 training images and 245 test images. The notebook repeatedly uses the test split as `validation_data` and for early stopping. That selects epochs using test performance and makes final test metrics optimistically biased.

The converted script instead takes a seeded 10% validation subset from training and leaves the selected test split untouched until final evaluation. However, a random image-level validation split can still place near-duplicate augmented siblings from one run on both sides. The recommended fix is a group-aware validation split by run ID.

## 3. Model configuration

### 3.1 Convolutional autoencoder

The encoder is:

| Stage        | Output         | Main setting              |
| ------------ | -------------- | ------------------------- |
| Input        | 64 × 64 × 1  | grayscale sensor matrix   |
| Conv + pool  | 32 × 32 × 32 | 32 filters, 3 × 3, ReLU  |
| Conv + pool  | 16 × 16 × 64 | 64 filters, 3 × 3, ReLU  |
| Conv + pool  | 8 × 8 × 128  | 128 filters, 3 × 3, ReLU |
| Flatten      | 8,192          | —                        |
| Dense latent | 256            | ReLU                      |

The decoder mirrors this structure with a dense 8 × 8 × 128 representation, three transpose-convolution/upsampling stages, and a sigmoid one-channel output. It has 4,535,553 trainable parameters, uses Adam and pixel-wise MSE, and is trained for 30 epochs with batch size 32 in the notebook.

The notebook prints an average reconstruction MSE of 0.07234932, but that calculation is defective: only three reconstructed sample images exist at that point, so it compares just the first three test images, not the complete test set. It is also inconsistent with the much lower validation losses displayed during AE training. This value should not be treated as a reliable full-test reconstruction score.

### 3.2 Latent LSTM regressor

The selected LSTM reshapes each 256-element latent vector arbitrarily into `(16, 16)` and applies:

| Layer   | Configuration                     |
| ------- | --------------------------------- |
| LSTM 1  | 128 units, tanh, return sequences |
| Dropout | 0.2                               |
| LSTM 2  | 64 units, tanh                    |
| Dropout | 0.2                               |
| Dense   | 32 units, ReLU                    |
| Output  | 2 linear units: CO and ethylene   |

It has approximately 125,794 trainable parameters, uses Adam with learning rate 0.002, MSE loss, MAE monitoring, batch size 32, up to 1,000 epochs, and early stopping patience 50.

The reshape does not create a physically meaningful temporal sequence: neighboring latent variables are simply neighboring dense-layer coordinates. Consequently, the LSTM's recurrence is imposed on an arbitrary ordering rather than actual time. This weakens the mathematical rationale for using an LSTM after a flattened dense bottleneck.

### 3.3 Other notebook branches

- AE + XGBoost searches 144 hyperparameter combinations with 3-fold CV (432 fits). The stored best configuration is 1,000 trees, depth 3, learning rate 0.02, subsample 0.8, and column sample 0.7.
- AE + MLP uses dense layers 128 and 64, dropout 0.3, and learning rate 0.02.
- Direct CNN, pseudo-ResNet-8, RNN, image-row LSTM, 16 × 16 patch LSTM, and four-block Transformer definitions appear later.
- The “ResNet-8” has no residual/skip connections, so it is a plain deep CNN and should not be called ResNet.
- Several comments incorrectly mention NH3/H2S, evidently copied from the companion notebook.

## 4. Result analysis

### 4.1 Stored AE + LSTM five-split results

The notebook records the following results, apparently using each split once as holdout. They are historical notebook outputs, not locally reproduced metrics:

|        Test split |            CO MAE |           CO RMSE |           CO R² |     Ethylene MAE |    Ethylene RMSE |     Ethylene R² |
| ----------------: | ----------------: | ----------------: | ---------------: | ---------------: | ---------------: | ---------------: |
|                 5 |           14.4610 |           22.1726 |           0.9830 |           0.3984 |           0.5568 |           0.9904 |
|                 1 |           21.9753 |           30.0317 |           0.9662 |           0.8409 |           1.5516 |           0.8999 |
|                 2 |           14.2897 |           20.2838 |           0.9790 |           0.4639 |           0.7700 |           0.9783 |
|                 3 |           14.4531 |           21.7021 |           0.9815 |           0.9944 |           1.2064 |           0.9411 |
|                 4 |           14.8889 |           21.2878 |           0.9859 |           0.4876 |           0.7221 |           0.9833 |
| Mean ± sample SD | 16.0136 ± 3.3401 | 23.0956 ± 3.9395 | 0.9791 ± 0.0076 | 0.6370 ± 0.2639 | 0.9614 ± 0.4080 | 0.9586 ± 0.0380 |

On these stored values, CO prediction is consistently strong, while ethylene is much less stable between splits: ethylene R² ranges from 0.8999 to 0.9904. The variance matters more than the best fold and suggests sensitivity to which concentration episodes are held out.

The notebook contains several additional, sometimes conflicting AE + LSTM result blocks for split 4. Because cells were run out of order and variables were overwritten, there is no experiment manifest tying each metric block to a seed, model checkpoint, augmentation setting, or exact split assignment. The five-fold table above is the most complete coherent block, not necessarily the final or most trustworthy run.

### 4.2 Other stored model comparisons

One later markdown comparison reports:

| Model           | CO MAE / R²     | Ethylene MAE / R² |
| --------------- | ---------------- | ------------------ |
| Plain CNN       | 46.2468 / 0.8346 | 2.1780 / 0.7038    |
| Pseudo-ResNet   | 14.9502 / 0.9822 | 0.6617 / 0.9729    |
| SimpleRNN       | 23.6308 / 0.9597 | 1.5184 / 0.8429    |
| Direct row LSTM | 19.9426 / 0.9630 | 1.5593 / 0.8228    |
| Patch LSTM      | 11.2317 / 0.9895 | 1.6995 / 0.8101    |
| Transformer     | 18.5196 / 0.9709 | 0.8768 / 0.8929    |

These comparisons are not controlled experiments: test split, seed, early stopping, scaler state, and even the active `model` variable can differ. Patch LSTM's excellent CO score but poor ethylene score also illustrates why a joint summary or task-balanced loss is needed. These numbers are descriptive only and do not establish model superiority.

### 4.3 Metric issues

The notebook uses two incompatible NRMSE formulas:

\[
\mathrm{NRMSE}_{mean}=\frac{\mathrm{RMSE}}{\bar y}, \qquad
\mathrm{NRMSE}_{range}=\frac{\mathrm{RMSE}}{y_{max}-y_{min}}.
\]

Values from these definitions cannot be compared directly. Mean-normalized RMSE is also unstable when mean concentration is near zero. The report should choose one definition, label it explicitly, and preferably add scale-independent MAE divided by target range or standard deviation.

Because each run creates five nearly identical images with the same target, image-level metrics over 245 test images overweight each physical run five times. Point estimates remain similar when every run has exactly five variants, but confidence intervals must be computed at run level, not image level.

## 5. Strengths and weaknesses

### Strengths

- Splitting by measurement episode avoids the severe leakage caused by random row-level train/test splitting.
- Both gases are predicted jointly, allowing shared sensor features to represent cross-gas response.
- The 64-second window captures transient sensor response rather than using one instantaneous reading.
- Five held-out groups provide a better view of robustness than one train/test split.
- MAE, RMSE, R², prediction plots, and residual CDFs provide multiple error perspectives.
- The local conversion adds deterministic seeds, local paths, a CLI, reusable intermediate arrays, train-only target scaling, and a validation set separate from test.

### Weaknesses and reproducibility defects

- The notebook is not executable top-to-bottom: `EC4` is undefined; later cells report undefined `model`, `history`, and `results`; and model variables are repeatedly overwritten.
- Absolute Kaggle paths prevent local execution.
- No seed is set for run shuffling, TensorFlow, or random visualization choices.
- Test-fitted sensor and target scalers leak information and make target inverse transformation inconsistent.
- The test split is used for early stopping and model selection.
- Random validation over augmented images can leak near-duplicate variants of a run.
- Quantizing normalized sensor data to uint8 discards precision; saving/reloading PNG is unnecessary for numeric modeling.
- Repeating every sensor four times creates an artificial image geometry.
- A dense AE bottleneck destroys explicit time ordering before the vector is arbitrarily reshaped for LSTM.
- The autoencoder objective minimizes pixel reconstruction, not concentration prediction; it may preserve nuisance variation while discarding target-relevant features.
- Five offset windows differ by only 0.2 seconds and provide little independent augmentation.
- Equal run counts do not ensure balanced concentration combinations or balanced run duration.
- GridSearchCV uses ordinary folds, not group-aware folds, and multi-output support/version behavior is not documented.
- NRMSE definitions change across cells, and several result blocks lack provenance.
- No uncertainty intervals, per-concentration error breakdown, zero-vs-mixture analysis, sensor ablation, or external-day validation are provided.

## 6. Insights for improvement

### 6.1 Correct the evaluation mathematics first

1. Fit every scaler on training data only. For sensor channel \(j\), store training \(a_j=\min x_j\) and \(b_j=\max x_j\), then apply the same transformation to validation, test, and deployment data. Fit a single training target scaler and use it for inverse transformation.
2. Use nested, group-aware cross-validation. The outer loop estimates generalization by held-out exposure run/session; the inner loop selects architecture and hyperparameters. All augmented variants of a run must remain in the same fold. Report mean, sample standard deviation, and a run-level bootstrap 95% confidence interval.
3. Standardize metrics. Report ppm MAE and RMSE, R², and one declared normalized metric such as

\[
\mathrm{NRMSE}_{\sigma}=\frac{\sqrt{\frac{1}{n}\sum_i(y_i-\hat y_i)^2}}{s_y}.
\]

Also report per-gas median absolute error, 90th/95th percentile absolute error, signed bias, and errors stratified by true concentration and mixture composition.

4. Balance the multi-task loss. CO spans 0–533.33 ppm while ethylene spans 0–20 ppm. Even after normalization, their noise and difficulty differ. Use a weighted Huber loss,

\[
L=\sum_{g\in\{CO,C_2H_4\}} w_g\,\mathrm{Huber}_{\delta_g}(y_g-\hat y_g),
\]

with weights selected only on inner validation, or learn homoscedastic uncertainty weights:

\[
L=\sum_g \left(\frac{L_g}{2\sigma_g^2}+\log\sigma_g\right).
\]

This reduces domination by one task and is more robust to outliers than MSE.

### 6.2 Use the real time-series structure

The strongest architectural correction is to keep the input as `(time=64, sensors=16)` in float32. Good candidates are:

- A 1D temporal convolutional network with dilated residual blocks, followed by attention/global pooling and two regression heads.
- A GRU/LSTM directly over 64 actual timesteps, optionally preceded by a learned linear sensor embedding.
- A compact temporal Transformer with positional encoding and sensor-channel embeddings.
- A CNN-LSTM where 1D convolutions extract local sensor dynamics and the LSTM models actual temporal evolution.

These models preserve physical sequence order, avoid square-image fabrication, and usually require fewer parameters than the 4.5-million-parameter AE.

If representation learning is useful, train it jointly with regression:

\[
L = \lambda_{rec}L_{reconstruction}+\lambda_{reg}L_{gas},
\]

or use supervised contrastive learning where windows with the same/nearby concentrations are positives. A joint encoder is encouraged to preserve concentration-relevant information rather than merely reconstruct sensor pixels.

### 6.3 Improve features and sensor physics

- Add baseline-corrected response \(\Delta R=R_t-R_0\) or relative response \((R_t-R_0)/(R_0+\epsilon)\), using a pre-exposure baseline when available.
- Add first differences, response slope, peak, area under response, rise time, decay constant, rolling variance, and cross-sensor ratios.
- Include elapsed time within exposure and environmental covariates such as temperature/humidity if available.
- Test log or robust transformations for heavy-tailed sensor amplitudes; use median/IQR scaling when extreme drift is present.
- Run sensor ablation or permutation importance to identify redundant or unstable channels.
- Model calibration drift explicitly with session/day identifiers or domain-adversarial training, then validate on a later acquisition period.

### 6.4 Improve augmentation and sampling

Replace five almost identical fixed offsets with physically plausible training-only augmentation: random temporal crop, small time warp, amplitude scaling within calibration tolerance, additive noise estimated from baseline, channel dropout, and sensor drift perturbation. Never augment validation/test data for the primary metric; optionally average predictions over deterministic test-time windows and report that protocol separately.

Stratify group assignment by the joint `(CO, ethylene)` concentration pair so every fold covers the concentration space as evenly as possible. If the goal is interpolation, ensure each concentration combination occurs in train and test but with different episodes. If the goal is extrapolation, explicitly hold out concentration levels and report that harder task separately.

### 6.5 Establish trustworthy baselines and experiment tracking

Before deep models, evaluate ridge/elastic-net regression, partial least squares, random forest, and XGBoost on engineered time-series summaries. A deep model should beat these under the same group folds to justify its complexity.

For every run, save the seed, exact run-to-fold mapping, preprocessing parameters, package versions, model summary, epoch selected, learning curves, predictions with run IDs, and metrics JSON. This will eliminate the notebook's current ambiguity between repeated result blocks and make comparisons statistically defensible.

## Local conversion and execution record

Converted script:

```powershell
python split-to-5-lstm-co-ethy.py --stage inspect
python split-to-5-lstm-co-ethy.py --stage prepare --output ec_run
python split-to-5-lstm-co-ethy.py --stage full --quick
```

Observed locally on 2026-07-16:

| Check                                | Outcome                                                         |
| ------------------------------------ | --------------------------------------------------------------- |
| Python syntax compilation            | Passed                                                          |
| Chunked raw-data inspection          | Passed in ~30.5 s                                               |
| Full preprocessing/image preparation | Passed in ~38.1 s                                               |
| Counts compared with notebook        | Exact match on raw, active, retained rows/runs and images       |
| Full neural smoke training           | Blocked before data loading:`ModuleNotFoundError: tensorflow` |

At the time of the first audit, the environment had NumPy 2.3.0, pandas 2.3.0, scikit-learn 1.8.0, Pillow 11.2.1, XGBoost 3.2.0, Matplotlib 3.10.9, and seaborn 0.13.2; TensorFlow and OpenCV were absent. They were installed and validated during the improvement work documented in Section 7. The notebook's stored results remain labeled historical because the corrected evaluation protocol is materially different.

## 7. Improvement implementation and measured results

### 7.1 What was implemented

The recommendations from Section 6 were converted into `ec_improvement_benchmark.py`. The benchmark uses the following fixed protocol:

- Seed 42 and the same 245 episode IDs divided into five outer folds of 49 runs.
- All five offset windows of an outer-training run may be used for training.
- Only offset 0 is evaluated, so every test episode contributes one independent observation rather than five near-duplicates.
- No held-out run contributes to model fitting or scaler fitting.
- Classical preprocessing is contained inside the training pipeline.
- Neural sensor scaling uses a training-only robust scaler; target scaling uses a training-only standard scaler.
- Neural validation consists of complete held-out training-run IDs, not randomly selected augmented images.
- Final metrics are calculated in physical ppm and use one consistent definition. Alongside MAE, RMSE, and R², raw JSON includes signed bias, 90th-percentile absolute error, and RMSE divided by target standard deviation.
- Every fold's configuration, sample counts, runtime, and metrics are stored as JSON and Joblib artifacts under `ec_improvements/`.

The raw cache contains 1,225 unquantized float32 sequences with shape 64 × 16, their gas targets, episode IDs, fold IDs, and augmentation offsets. This removes the PNG round trip, uint8 precision loss, artificial 64-column repetition, split-fitted image scaling, and arbitrary AE-latent temporal ordering from the new benchmarks.

### 7.2 Dependency installation

OpenCV 5.0.0 installed in the normal Python 3.13 user environment. TensorFlow 2.21.0 supports Python 3.13, but the system drive had only about 370 MB free and the first installation attempt stopped with `OSError: [Errno 28] No space left on device`. After purging 430.5 MB of disposable pip cache, capacity was still marginal. TensorFlow and its dependencies were therefore installed under the workspace-local `.deps2` directory on drive E, with temporary extraction also redirected to drive E. Both imports were then verified:

```text
tensorflow 2.21.0
opencv 5.0.0
```

The converted script automatically adds `.deps2` before importing TensorFlow. TensorFlow 2.21 uses CPU on native Windows; PyTorch 2.12.1 detected and used the NVIDIA GeForce RTX 3060 for the GRU and TCN experiments.

### 7.3 Feature and baseline tests

Three input representations were tested with Ridge, partial least squares (PLS), Random Forest, Extra Trees, and XGBoost:

- `summary` (144 features): per-sensor mean, standard deviation, minimum, maximum, first value, final value, delta, linear slope, and time-normalized area.
- `physics` (208 features): all summary features plus baseline-corrected mean response, relative response, mean derivative, and derivative variation.
- `flat` (1,024 features): the unrolled 64 × 16 raw sequence, included as an ablation.

Values are the mean ± sample standard deviation across five episode-disjoint test folds.

| Features          | Model             |                    CO MAE |                   CO RMSE |                     CO R² |             Ethylene MAE |            Ethylene RMSE |               Ethylene R² |
| ----------------- | ----------------- | ------------------------: | ------------------------: | -------------------------: | -----------------------: | -----------------------: | -------------------------: |
| Summary           | Ridge             |           20.679 ± 1.958 |           28.303 ± 4.774 |           0.9692 ± 0.0078 |           0.868 ± 0.140 |           1.211 ± 0.214 |           0.9455 ± 0.0204 |
| Summary           | PLS               |           23.914 ± 1.331 |           32.349 ± 4.260 |           0.9594 ± 0.0113 |           1.100 ± 0.156 |           1.397 ± 0.231 |           0.9275 ± 0.0267 |
| Summary           | Random Forest     |           15.622 ± 7.180 |          28.226 ± 15.532 |           0.9600 ± 0.0503 |           0.985 ± 0.214 |           1.839 ± 0.575 |           0.8671 ± 0.0788 |
| Summary           | Extra Trees       |           14.799 ± 4.318 |          25.636 ± 10.224 |           0.9703 ± 0.0296 |           0.966 ± 0.243 |           1.753 ± 0.583 |           0.8790 ± 0.0795 |
| Summary           | XGBoost           |           15.167 ± 2.931 |           30.058 ± 8.483 |           0.9614 ± 0.0261 |           0.451 ± 0.179 |           0.805 ± 0.544 |           0.9676 ± 0.0419 |
| Physics           | Ridge             |           19.246 ± 3.287 |          31.710 ± 14.678 |           0.9546 ± 0.0472 |           0.911 ± 0.204 |           1.642 ± 1.006 |           0.8863 ± 0.1322 |
| Physics           | PLS               |           24.485 ± 3.781 |          40.015 ± 19.681 |           0.9262 ± 0.0819 |           1.360 ± 0.370 |           2.488 ± 2.156 |           0.6882 ± 0.5001 |
| Physics           | Random Forest     |           15.149 ± 7.747 |          27.017 ± 15.109 |           0.9632 ± 0.0474 |           1.002 ± 0.257 |           1.860 ± 0.649 |           0.8602 ± 0.0943 |
| Physics           | Extra Trees       |           14.236 ± 4.334 |           24.410 ± 9.539 |           0.9732 ± 0.0261 |           0.955 ± 0.239 |           1.741 ± 0.578 |           0.8803 ± 0.0770 |
| **Physics** | **XGBoost** | **14.604 ± 3.613** | **27.135 ± 8.275** | **0.9681 ± 0.0243** | **0.443 ± 0.178** | **0.815 ± 0.546** | **0.9670 ± 0.0424** |
| Flat              | Ridge             |           20.149 ± 4.349 |           32.587 ± 9.768 |           0.9587 ± 0.0193 |           0.774 ± 0.137 |           1.154 ± 0.229 |           0.9505 ± 0.0190 |
| Flat              | PLS               |           22.527 ± 3.353 |           35.267 ± 8.173 |           0.9514 ± 0.0198 |           1.451 ± 0.240 |           1.865 ± 0.389 |           0.8727 ± 0.0418 |
| Flat              | Random Forest     |           19.122 ± 5.498 |          36.174 ± 12.090 |           0.9452 ± 0.0362 |           1.244 ± 0.312 |           2.161 ± 0.634 |           0.8176 ± 0.1150 |
| Flat              | Extra Trees       |           17.940 ± 5.269 |          31.714 ± 13.741 |           0.9546 ± 0.0449 |           1.109 ± 0.293 |           1.960 ± 0.562 |           0.8530 ± 0.0728 |
| Flat              | XGBoost           |           20.198 ± 4.270 |          35.195 ± 10.311 |           0.9492 ± 0.0324 |           0.555 ± 0.180 |           1.006 ± 0.477 |           0.9564 ± 0.0388 |

Physics-feature XGBoost is the best balanced classical model: it has the lowest mean ethylene MAE (0.443 ppm) and competitive CO MAE (14.604 ppm). Extra Trees with physics features has slightly lower CO MAE (14.236 ppm), but much worse ethylene error. The raw flat representation is consistently inferior to compact summaries, showing that feature dimension alone does not improve episode-level generalization.

Baseline/delta features help the nonlinear models modestly but destabilize linear PLS and Ridge, especially on the difficult fold. Relative response can explode when the five-sample baseline is near zero; a future version should clip or log-transform this term and should use a true pre-exposure baseline rather than the first five active-exposure readings.

### 7.4 Time-series neural tests

Two models used the real 64-step × 16-sensor sequence:

- GRU: two 64-unit recurrent layers with dropout, a 32-unit head, AdamW, and Huber loss.
- TCN: three temporal convolutions with dilation 1, 2, and 4, global average pooling, a 32-unit head, AdamW, and Huber loss.

Both used complete-run validation groups and early stopping patience 20. Results:

| Model         |                    CO MAE |                    CO RMSE |                     CO R² |             Ethylene MAE |            Ethylene RMSE |               Ethylene R² |
| ------------- | ------------------------: | -------------------------: | -------------------------: | -----------------------: | -----------------------: | -------------------------: |
| **GRU** | **14.511 ± 7.589** | **29.958 ± 19.935** | **0.9512 ± 0.0669** | **0.580 ± 0.336** | **1.185 ± 0.778** | **0.9319 ± 0.0704** |
| TCN           |          22.904 ± 10.824 |           37.144 ± 22.244 |           0.9275 ± 0.0912 |           0.797 ± 0.362 |           1.338 ± 0.725 |           0.9189 ± 0.0780 |

The GRU is competitive on CO MAE but less stable and inferior to XGBoost on ethylene. The small dataset—196 outer-training runs before validation removal—is a better match for engineered-feature boosting than for end-to-end deep learning. Fold 4 remains difficult: GRU CO MAE is 26.95 ppm there versus 8.80–16.25 ppm on the other folds. This variation is hidden by any single-split result and confirms the need for group cross-validation.

The TCN underperforms the GRU and classical models. Its receptive field and global average pooling may be too coarse for transient response timing, and no inner-fold hyperparameter tuning was performed. Adding residual connections, normalization, and task-weight tuning is justified only after expanding the number of independent exposure episodes.

### 7.5 Corrected AE + LSTM rerun

The converted TensorFlow pipeline was rerun end-to-end after installing TensorFlow. It fits the target scaler on training data only and uses a separate validation subset instead of the outer test fold.

| Run           | AE epochs | LSTM epochs | CO MAE / RMSE / R²        | Ethylene MAE / RMSE / R² | Purpose                            |
| ------------- | --------: | ----------: | -------------------------- | ------------------------- | ---------------------------------- |
| Smoke         |         2 |           3 | 101.246 / 128.161 / 0.2915 | 2.487 / 3.571 / 0.5420    | Dependency and pipeline check only |
| Full, split 4 |        30 |         300 | 40.123 / 60.302 / 0.8432   | 1.650 / 2.248 / 0.8186    | Corrected measured result          |

The full corrected result is substantially worse than the notebook's historical split-4 AE + LSTM values. This is not evidence of a software failure: AE reconstruction converged from validation MSE 0.0459 to approximately 0.0002, and LSTM validation loss also converged. The difference is consistent with removal of target-scaler/test-validation leakage, a deterministic but different split assignment, and the fact that excellent reconstruction does not guarantee a concentration-discriminative latent space.

This rerun still retains the notebook's per-split sensor scaling and random image-level validation inside the AE/LSTM conversion for structural comparability. Therefore it is a corrected intermediate reference, not the preferred final model. The group-safe raw-sequence benchmarks are methodologically stronger.

### 7.6 Direct comparison with historical notebook claims

The historical five-fold AE + LSTM block reported mean CO MAE 16.014 ppm and ethylene MAE 0.637 ppm. Those values used unseeded folds and an invalid target-scaling/test-selection path. Under the stricter new protocol:

- Physics XGBoost improves the historical mean CO MAE by about 8.8%: `(16.014 − 14.604) / 16.014`.
- Physics XGBoost improves historical mean ethylene MAE by about 30.4%: `(0.637 − 0.443) / 0.637`.
- These percentage comparisons are informative but not paired statistical tests because the historical fold assignment is unknown.
- The corrected TensorFlow split-4 run shows why historical notebook metrics should not be used as the reproducible baseline.

### 7.7 Conclusions and next experimental priorities

The recommended current model is physics-feature XGBoost, with Extra Trees as the CO-focused alternative and GRU as the strongest tested sequence model. XGBoost is faster to train, more stable than the neural models, avoids image fabrication, and gives the best two-gas balance.

The next highest-value tests are now narrower than the original broad list:

1. Replace random fold assignment with concentration-pair-stratified group assignment and rerun the same frozen configurations. This will separate fold-composition variance from model variance.
2. Collect or identify true pre-exposure baselines and environmental variables; the current first-five-active-samples proxy is physically weak.
3. Tune a multi-output ensemble that combines physics XGBoost for ethylene with physics Extra Trees or GRU for CO, using only inner-group validation.
4. Add repeated group-fold seeds and run-level bootstrap confidence intervals. Five folds quantify some variability but do not isolate split randomness.
5. Validate on a chronologically later acquisition session. Random episode folds measure interpolation within this dataset, not long-term drift robustness.

All raw fold results are retained in `ec_improvements/summary_results.json`, `physics_results.json`, `flat_results.json`, `gru_results.json`, and `tcn_results.json`. TensorFlow run summaries are in `ec_run_improved_quick/run_summary.json` and `ec_run_improved_full/run_summary.json`.

### 7.8 Augmentation and sensor ablations

A final frozen ablation used the same physics features and five folds with a 300-tree XGBoost model. The smaller tree count made 90 fits practical; its all-sensor reference is therefore compared only with this ablation, not substituted for the 800-tree principal result.

Training on all five offset windows reduced mean CO MAE from 16.370 to 15.006 ppm (8.3%) and ethylene MAE from 0.562 to 0.452 ppm (19.5%) relative to training on only offset 0. Test evaluation remained one base window per run in both cases. The highly overlapping windows therefore provide useful small phase-shift regularization, even though they are not independent observations.

| Sensor removed |           CO MAE |    Ethylene MAE | Interpretation                                     |
| -------------: | ---------------: | --------------: | -------------------------------------------------- |
|           None |           15.006 |           0.452 | Frozen 300-tree reference                          |
|              1 |           26.761 |           0.513 | Critical sensor; removal severely harms both tasks |
|              2 |           14.502 |           0.438 | Mild improvement                                   |
|              3 |           14.642 |           0.437 | Mild improvement                                   |
|              4 |           14.310 |           0.436 | Helpful removal                                    |
|              5 | **14.064** | **0.436** | Best CO removal and tied-best ethylene             |
|              6 |           14.614 |           0.442 | Mild improvement                                   |
|              7 |           14.483 |           0.467 | CO improves, ethylene worsens                      |
|              8 |           14.603 |           0.448 | Near neutral                                       |
|              9 |           14.795 |           0.444 | Near neutral                                       |
|             10 |           14.108 |           0.457 | Strong CO improvement, small ethylene cost         |
|             11 |           14.605 |           0.445 | Mild improvement                                   |
|             12 |           14.462 |           0.443 | Mild improvement                                   |
|             13 |           14.562 |           0.444 | Mild improvement                                   |
|             14 |           14.449 |           0.447 | Mild improvement                                   |
|             15 |           14.434 |           0.456 | CO improves, ethylene slightly worsens             |
|             16 |           14.511 |           0.452 | CO improves, ethylene neutral                      |

Sensor 1 is uniquely essential. Removing many other single sensors slightly improves mean error, consistent with redundancy or sensor-specific noise. Sensor 5 removal is the best single-channel ablation, improving CO MAE by 6.3% and ethylene MAE by 3.5% relative to the 300-tree reference. This does not prove Sensor 5 is intrinsically harmful: correlated predictors can redistribute tree splits, and repeated group-fold testing is needed before hardware removal. The next model iteration should compare the frozen 15-sensor (drop Sensor 5) configuration against all sensors with the full 800-tree setting and repeated seeds.

Detailed fold results are stored in `ec_improvements/ablation_results.json`; the captured execution log is `ec_improvements/ablation_run.log`.

### 7.9 Sensor-order sensitivity test

The AE–LSTM's sensitivity to sensor column order was measured directly using the corrected split-4 pipeline. All tests used the same prepared samples, outer test split, target scaler, seed 42, and evaluation code. The existing-model tests loaded the exact saved encoder and LSTM from `ec_run_improved_full`. Each retraining test initialized a new AE and LSTM, trained the AE for 30 epochs and the LSTM for 300 epochs, and saved the resulting models.

The tested fixed random order was:

```text
S7, S16, S12, S11, S10, S4, S1, S8, S13, S6, S3, S5, S15, S2, S14, S9
```

The correlation order was computed using only outer-training raw sequences. Sensors were clustered with average linkage and distance \(d_{ij}=1-|\rho_{ij}|\), producing:

```text
S2, S9, S10, S15, S7, S8, S3, S4, S16, S11, S12, S1, S13, S14, S5, S6
```

| Test                                    |           CO MAE |          CO RMSE |           CO R² | Ethylene MAE |   Ethylene RMSE |     Ethylene R² |
| --------------------------------------- | ---------------: | ---------------: | ---------------: | -----------: | --------------: | ---------------: |
| Existing model, original order          |           40.123 |           60.302 |           0.8432 |        1.650 |           2.248 |           0.8186 |
| Existing model, fixed random order      |          192.343 |          228.453 |          -1.2512 |        3.359 |           4.616 |           0.2348 |
| Existing model, random order per sample |          163.053 |          205.119 |          -0.8148 |        3.963 |           5.330 |          -0.0203 |
| Retrained, fixed random order           | **29.768** | **48.584** | **0.8982** |        1.738 |           2.519 |           0.7721 |
| Retrained, correlation order            |           33.595 |           59.078 |           0.8495 |        1.775 | **2.236** | **0.8205** |

#### Applying the original trained model

A fixed unseen permutation increased CO MAE by 379% (4.79×) and ethylene MAE by 104% (2.04×). CO R² became negative, meaning its predictions were worse than predicting the test-set mean. This confirms that sensor position is part of the learned input schema; the network does not recognize a sensor independently of its column location.

Changing the permutation independently for every sample also caused failure: CO R² was −0.8148 and ethylene R² was −0.0203. Its CO MAE happens to be lower than the one fixed-permutation case, but both are unusable and the relative ordering has no practical significance. Random per-sample order destroys every stable convolutional neighborhood and latent distribution.

The failure is not caused merely by information loss—exactly the same sensor readings remain present. It is a representation-distribution shift. The existing convolutional filters expect learned four-column sensor blocks at exact horizontal positions, and the LSTM expects the encoder's corresponding latent distribution.

#### Retraining after switching sensors

Retraining both the AE and LSTM recovered positive, strong R² values. The fixed random order improved CO MAE by 25.8% relative to the original-order retrained baseline, from 40.123 to 29.768 ppm, while ethylene MAE worsened by 5.4%. The correlation order improved CO MAE by 16.3%; for ethylene it slightly improved RMSE and R² but worsened MAE by 7.6%.

These results demonstrate that a consistent switched order is learnable, but they do not establish that random ordering is inherently better. Each configuration was trained once, and AE–LSTM training is stochastic. The original, random, and correlation runs would need repeated seeds and preferably five complete outer folds for an order-ranking claim. The safe conclusion is narrower: retraining is mandatory, and sensor order changes the optimization outcome because 2D convolution imposes an artificial sensor-neighborhood geometry.

Low validation losses did not guarantee superior held-out concentration results. The random-order AE ended at reconstruction validation MSE 0.000250 and the correlation-order AE at 0.000202, yet their gas metrics differed by target. This again shows that reconstruction quality is not a sufficient proxy for regression usefulness.

#### Operational rule

The deployed model must store and validate this exact schema:

```text
Sensor1, Sensor2, ..., Sensor16
```

If physical wiring, dataframe column order, or preprocessing order changes, software should remap readings back to the training schema before scaling and inference. If reliable remapping is impossible, both the AE and LSTM must be retrained; retraining only the LSTM does not restore the encoder's expected spatial input distribution. A per-sample schema hash or explicit sensor-name assertion should fail closed rather than silently issue incorrect gas estimates.

The reproducible test harness is `ec_sensor_order_test.py`. Exact permutations, metrics, epochs, validation losses, and timings are stored in `ec_sensor_order/sensor_order_results.json`; trained variant models and the execution log are stored in the same directory.

## 8. Next experiment program

The next phase should test generalization properties rather than add unconstrained architecture comparisons. The ordered program is: (1) concentration-pair-held-out evaluation, (2) leave-one-concentration-level-out interpolation and extrapolation, (3) chronological pseudo-domain evaluation, (4) self-supervised masked sensor/time pretraining, (5) calibrated group-conformal uncertainty, (6) joint sensor-count and observation-time optimization, and (7) permutation-aware sensor-set learning. Experiment 7 is specified and initially tested below because Section 7.9 demonstrated a severe sensor-order failure in the image-based AE-LSTM.

### 8.1 Experiment 7: permutation-aware models

#### Research question and required invariance

The research question is whether gas regression can be made invariant to dataframe or wiring column order while retaining the physical identity of every sensor. For a sample (X), sensor-identity vector (I), and common permutation (P), the desired property is

\[
f(PX,PI)=f(X,I).
\]

This is not the same as requiring (f(PX,I)=f(X,I)). The latter assigns each reading to the wrong physical sensor and should normally change the prediction. A valid model must therefore be order-invariant but identity-aware.

#### Model plan

Each of the 16 sensors is processed independently by the same temporal encoder: two one-dimensional convolutions over the 64 real timesteps, GELU activations, and global temporal pooling produce a 32-dimensional token. This shared encoder prevents array position from selecting a different temporal feature extractor.

Three models form the controlled comparison:

1. **Identity-aware Deep Sets.** Concatenate a learned 16-dimensional sensor-ID embedding to each temporal token, project the token, apply a shared nonlinear map, mean-pool the set, and regress both gases. This is the smallest proposed model and is invariant by construction.
2. **Identity-aware Set Transformer.** Use the same sensor tokens and identities, followed by two four-head self-attention layers before mean pooling. This tests whether explicit sensor-to-sensor interactions improve regression.
3. **Identity-free Deep Sets control.** Omit sensor IDs. This model is invariant even when readings are assigned to the wrong identities, but it tests the accuracy lost when the model cannot distinguish physical sensor types.

Future extensions should add a graph model with sensor IDs as nodes and training-fold-only correlations as edges, mask-aware pooling for missing channels, sensor-dropout augmentation, and an explicit identity-schema assertion at input. These extensions should be accepted only if they improve held-out-run accuracy or fault robustness without weakening aligned-permutation invariance.

#### Evaluation plan

- Use the existing five outer run folds. All five offset windows from a run remain together.
- Within each outer-training partition, reserve 10% of run IDs for early stopping. Use all five offsets for training but only offset 0 for validation and testing.
- Fit the robust sensor scaler and target standardizer on the training partition only.
- Train with Huber loss, AdamW, at most 150 epochs, and patience 20.
- Evaluate one base window per held-out run under three test conditions: original order; one fixed permutation applied jointly to readings and IDs; and the same permutation applied only to readings, deliberately producing an identity mismatch.
- The primary correctness test is the maximum absolute prediction difference between original and aligned-permutation output. The acceptance threshold is (10^{-3}) ppm.
- Secondary outcomes are five-fold mean MAE, RMSE, and R-squared for each gas, parameter count, and the degradation caused by identity mismatch.
- After model selection, repeat at least five training seeds and add run-level bootstrap confidence intervals. The single-seed results below establish feasibility but are not a final ranking.

#### Initial five-fold results

The frozen permutation was `S7, S16, S12, S11, S10, S4, S1, S8, S13, S6, S3, S5, S15, S2, S14, S9`. All aligned permutations passed the numerical-invariance threshold; the largest prediction difference was only (6.10\times10^{-5}) ppm.

| Model                      | Parameters | Condition             |           CO MAE |          CO RMSE |     CO R-squared |    Ethylene MAE |   Ethylene RMSE | Ethylene R-squared |
| -------------------------- | ---------: | --------------------- | ---------------: | ---------------: | ---------------: | --------------: | --------------: | -----------------: |
| Deep Sets + identity       |     13,586 | Original              | **22.050** | **30.423** | **0.9608** | **0.746** | **1.063** |   **0.9542** |
| Deep Sets + identity       |     13,586 | Aligned permutation   |           22.050 |           30.423 |           0.9608 |           0.746 |           1.063 |             0.9542 |
| Deep Sets + identity       |     13,586 | Mismatched identity   |          125.839 |          159.197 |           0.0166 |           3.707 |           4.708 |             0.1870 |
| Set Transformer + identity |     76,370 | Original              |           31.143 |           55.913 |           0.8733 |           1.144 |           1.917 |             0.8506 |
| Set Transformer + identity |     76,370 | Aligned permutation   |           31.143 |           55.913 |           0.8733 |           1.144 |           1.917 |             0.8506 |
| Set Transformer + identity |     76,370 | Mismatched identity   |          144.361 |          185.062 |          -0.3163 |           4.365 |           5.702 |            -0.3000 |
| Deep Sets, no identity     |     12,306 | Original              |           61.109 |           81.697 |           0.7326 |           1.606 |           2.262 |             0.8009 |
| Deep Sets, no identity     |     12,306 | Aligned or mismatched |           61.109 |           81.697 |           0.7326 |           1.606 |           2.262 |             0.8009 |

Values are unweighted means of the five outer-fold metrics. The identity-aware Deep Sets model is the best permutation-aware candidate: it is exactly invariant for valid schema reordering and substantially more accurate than the larger Set Transformer. The attention model appears too flexible for only 245 independent runs. Removing identities makes arbitrary data-only permutation harmless, but increases CO MAE by 177% and ethylene MAE by 115% relative to identity-aware Deep Sets. Sensor identity is therefore essential information.

The deliberate mismatch test increased identity-aware Deep Sets MAE from 22.050 to 125.839 ppm for CO and from 0.746 to 3.707 ppm for ethylene. This is desirable diagnostic behavior: the architecture removes dependence on storage position but does not pretend that readings from different physical sensors are interchangeable. Production input must pass sensor names alongside readings and should reject missing, duplicated, or unknown IDs.

For context, the previously tested GRU remains better in mean MAE (14.511 ppm CO and 0.580 ppm ethylene), while identity-aware Deep Sets is better than the tested TCN (22.904 ppm CO and 0.797 ppm ethylene) on MAE. These are architectural trade-offs under one seed, not statistical superiority claims. The next iteration should combine the GRU's temporal capacity with identity-aware set pooling, repeat five seeds, and test missing-sensor masks before deciding whether permutation awareness is worth the accuracy cost.

The reproducible implementation is `ec_permutation_aware.py`. Complete fold-level outputs and protocol metadata are stored in `ec_permutation_aware/results.json`; the captured run output is `ec_permutation_aware_run.log`.

### 8.2 Experiment 8: distributional VAE representations on 16 x 64 sensor images

#### Motivation and design

The deterministic autoencoder in the original notebook learns one unconstrained point representation and operates on an artificial 64 x 64 image made by repeating every sensor four times. Experiment 8 replaces it with a variational autoencoder (VAE) operating on the natural 16-sensor x 64-timestep matrix. No sensor columns are repeated and no PNG quantization is used.

The encoder uses two strided two-dimensional convolutions and produces a 64-dimensional Gaussian posterior,

\[
q_\phi(z\mid X)=\mathcal{N}\left(\mu_\phi(X),\operatorname{diag}(\sigma_\phi^2(X))\right).
\]

Training uses reparameterized samples (z=\mu+\sigma\odot\epsilon) and the beta-VAE objective

\[
L_{VAE}=\operatorname{MSE}(X,\hat X)+\beta D_{KL}\left(q_\phi(z\mid X)\Vert\mathcal{N}(0,I)\right),
\]

with latent dimension 64 and β = (10^{-4}). The small KL weight was selected as an initial feasibility setting because robust-scaled sensor reconstruction has a much larger numeric scale. It is a frozen configuration, not a tuned optimum.

Four downstream paths provide the necessary controls:

1. **VAE-LSTM:** reshape the posterior mean from 64 values to 8 x 8 and feed it to a two-layer LSTM. The mean is used for deterministic evaluation; posterior samples remain available for later uncertainty experiments.
2. **VAE-XGBoost:** predict concentration from the 64 posterior means alone.
3. **Physics XGBoost matched control:** use only the established physics features under exactly the same reduced training/validation partition as the VAE models.
4. **VAE + physics XGBoost:** concatenate the 64 posterior means with the physics features. Comparison with the matched control isolates the incremental value of the VAE representation.

The five-fold protocol is group-safe. Ten percent of outer-training run IDs are reserved for early stopping; all five temporal offsets are used during training, and only offset 0 is evaluated for validation and test. Robust sensor scaling and target standardization are fitted on training data only. The VAE is never fitted on validation or test samples.

#### Initial results

| Model | CO MAE | CO RMSE | CO R-squared | Ethylene MAE | Ethylene RMSE | Ethylene R-squared |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Physics XGBoost, matched control | **16.060** | **29.191** | **0.9641** | **0.478** | **0.847** | **0.9653** |
| VAE + physics XGBoost | 17.297 | 30.473 | 0.9610 | 0.525 | 0.940 | 0.9577 |
| VAE-LSTM | 26.060 | 54.298 | 0.8673 | 0.715 | 1.397 | 0.9205 |
| VAE-XGBoost | 40.295 | 68.857 | 0.8112 | 0.974 | 1.715 | 0.8837 |

Values are unweighted means of the five outer-fold metrics from the final seed-42 run. The VAE trained for a mean of 76 epochs. Mean validation reconstruction MSE was 2.133 and mean KL divergence was 18.221, so the KL term was active and the posterior had not simply collapsed to the prior.

The initial hypothesis is not supported by this configuration. Adding VAE features to physics XGBoost worsened CO MAE by 7.7% and ethylene MAE by 10.0% relative to the exactly matched physics-only control. The latent-only XGBoost result shows that an unsupervised reconstruction distribution does not retain concentration information as effectively as the engineered response statistics. VAE-LSTM improves substantially over latent-only XGBoost, but it remains worse than the physics control. Moreover, reshaping an unordered 64-dimensional latent mean to 8 x 8 does not create genuine time order, so recurrence in this VAE-LSTM has the same conceptual weakness as the original AE-LSTM.

These results do not establish that every VAE is unsuitable. They reject only the tested unsupervised 64-dimensional beta-VAE configuration. A justified second-stage study should run the following ablations:

- β in {0, (10^{-6}), (10^{-5}), (10^{-4}), (10^{-3}), (10^{-2})} and latent dimensions in {16, 32, 64, 128}, selected inside group-held-out validation.
- A supervised VAE with (L=L_{VAE}+\lambda L_{gas}), so the latent distribution is explicitly concentration-relevant.
- A sequential VAE whose latent variables remain indexed by real time, followed by a GRU/TCN, instead of arbitrarily reshaping a global latent vector.
- Monte Carlo posterior prediction, reporting predictive interval coverage and whether posterior variance rises for held-out concentration combinations.
- Conditional and mixture-prior VAEs to reflect the structured two-gas concentration space.
- Repeated seeds, run-level bootstrap intervals, and paired fold comparisons against the matched physics-only control.

Progression criteria should be strict: a VAE variant must improve the matched physics baseline on both gases or provide demonstrably calibrated uncertainty at comparable point accuracy. Lower reconstruction loss alone is not evidence of a better gas regressor.

The reproducible implementation is `ec_vae_benchmark.py`. The 20 fold/model results and VAE diagnostics are stored in `ec_vae/results.json`; execution timing is captured in `ec_vae_run.log`.

### 8.3 Experiment 9: seeded VAE variants and adversarial latent learning

#### Purpose and reproducibility

Experiment 8 used one VAE configuration and one seed. Experiment 9 tests whether its negative result is caused by KL strength, latent capacity, lack of target supervision, or the Gaussian KL mechanism itself. Every configuration was evaluated with master seeds 42, 123, and 2026 across the same five outer run folds, giving 15 fold-seed evaluations per model path. A deterministic run seed is derived from master seed, fold, and configuration. NumPy, Python, PyTorch CPU, and PyTorch CUDA generators are seeded before model creation.

Each outer-training partition reserves 10% of run IDs for validation. Training uses all five offsets; validation and testing use offset 0 only. Scaling, representation learning, and XGBoost fitting use training data only. The matched physics-only XGBoost control is refitted on every one of the same 15 partitions.

The tested representation settings are:

1. beta-VAE, 64 latent variables, beta = (10^{-5}): weak prior regularization.
2. beta-VAE, 64 latent variables, beta = (10^{-3}): stronger prior regularization.
3. beta-VAE, 32 latent variables, beta = (10^{-4}): compressed posterior.
4. Supervised VAE, 64 latent variables, beta = (10^{-4}), plus 0.2 times a two-gas Huber loss from the posterior mean.
5. Adversarial autoencoder (AAE), 64 latent variables: a discriminator distinguishes encoded samples from a standard Gaussian, and the encoder is trained adversarially with weight (10^{-3}). This is the tested GAN-family variation; it regularizes latent space without generating synthetic labelled exposures.

All representations use the natural float32 16 x 64 sensor-time matrix. XGBoost is tested on the learned latent alone and on latent plus physics features. The supervised VAE also has a direct regression-head result.

#### Repeated-seed results

| Representation and downstream model | CO MAE | CO RMSE | CO R-squared | Ethylene MAE | Ethylene RMSE | Ethylene R-squared |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Physics XGBoost matched control | 15.888 +/- 3.627 | 29.227 +/- 8.594 | 0.963 +/- 0.027 | **0.488 +/- 0.184** | **0.883 +/- 0.503** | **0.963 +/- 0.041** |
| beta-VAE (10^{-5}), latent + physics | 15.935 +/- 3.994 | 28.348 +/- 10.329 | 0.964 +/- 0.032 | 0.537 +/- 0.203 | 0.953 +/- 0.490 | 0.959 +/- 0.041 |
| beta-VAE (10^{-3}), latent + physics | **15.619 +/- 4.189** | **28.298 +/- 10.675** | **0.964 +/- 0.033** | 0.545 +/- 0.205 | 0.976 +/- 0.489 | 0.957 +/- 0.042 |
| beta-VAE (10^{-4}), z = 32, latent + physics | 16.035 +/- 3.646 | 28.915 +/- 10.084 | 0.963 +/- 0.030 | 0.527 +/- 0.191 | 0.946 +/- 0.485 | 0.959 +/- 0.041 |
| Supervised VAE, latent + physics | 16.512 +/- 4.221 | 29.663 +/- 10.121 | 0.962 +/- 0.030 | 0.540 +/- 0.181 | 0.966 +/- 0.458 | 0.958 +/- 0.037 |
| AAE, latent + physics | 16.645 +/- 5.379 | 30.241 +/- 12.235 | 0.958 +/- 0.041 | 0.545 +/- 0.177 | 0.974 +/- 0.434 | 0.960 +/- 0.036 |

Values are mean +/- sample standard deviation over 15 fold-seed results. The fold results within one seed share training data and should not be interpreted as 15 fully independent physical experiments.

Latent-only results remained substantially weaker. Their CO/ethylene MAEs were 36.939/1.192 for beta (10^{-5}), 35.954/1.091 for beta (10^{-3}), 41.273/1.198 for the 32-dimensional VAE, 31.342/1.052 for the supervised VAE, and 34.205/1.125 for the AAE. The supervised head itself reached 29.709/0.918 ppm MAE. Target supervision improves the representation relative to several unsupervised variants, but it does not approach the physics baseline.

#### Paired analysis and conclusion

The apparently best CO setting, beta (10^{-3}), reduces mean CO MAE by only 0.269 ppm relative to its partition-matched control. A paired fold-seed bootstrap 95% interval for that change is -1.057 to +0.542 ppm and includes zero; it wins 8 of 15 comparisons. Its ethylene MAE increases by 0.058 ppm, with bootstrap interval +0.028 to +0.089, and wins only 3 of 15 comparisons.

Every learned latent-plus-physics variant increases mean ethylene MAE. The paired ethylene degradation intervals exclude zero for all five settings. No configuration satisfies the predeclared progression rule of improving both gases or providing a separately validated uncertainty benefit. Physics XGBoost therefore remains preferred.

The AAE result also argues against using an unconditional GAN merely to generate more samples. The dataset has only 245 independent labelled runs, and a GAN can reproduce their concentration distribution without creating new physical sensor/device conditions. Synthetic augmentation should be pursued only with a conditional time-series generator and strict tests for memorization, distribution fidelity, and downstream benefit on untouched real runs.

A final distribution-learning study would be justified only if it changes the objective: a sequential supervised VAE preserving real timestep-indexed latents, or a conditional VAE evaluated for calibrated posterior intervals on held-out concentration pairs. Further unsupervised global-latent tuning is low priority given the consistent repeated-seed evidence.

The experiment is implemented in `ec_vae_variations.py`. All 180 saved records--165 representation/downstream results and 15 matched controls--are in `ec_vae_variations/results.json`; the training log is `ec_vae_variations_run.log`.

### 8.4 Experiment 10: generate seconds 9-16 from seconds 1-8, then use XGBoost

This experiment asks whether a generative temporal model can shorten the physical observation period. A conditional VAE (CVAE) and a conditional GAN (cGAN) observe the first 8 seconds of all 16 sensors and forecast the next 8 seconds. The generated continuation is appended to the observed prefix, physics features are extracted from the resulting 16-second sequence, and XGBoost predicts CO and ethylene concentration.

The experiment must distinguish useful forecasting from information fabrication. It therefore compares four matched paths:

1. **Observed 8 s XGBoost:** physics features from only the measured prefix. This is the deployment baseline with the same acquisition time.
2. **CVAE-generated 16 s XGBoost:** the measured 8 s plus the Monte Carlo mean of CVAE continuations.
3. **cGAN-generated 16 s XGBoost:** the measured 8 s plus the Monte Carlo mean of conditional GAN continuations.
4. **Oracle real 16 s XGBoost:** physics features from 16 genuinely measured seconds. This is an upper-reference acquisition path, not an available input to the generators.

Both generators are conditional on the observed sensor prefix. The CVAE learns a context-dependent latent prior and a training-time posterior conditioned on the real future; inference samples only from the learned prior. The cGAN discriminator receives both prefix and continuation, while an L1 forecasting term stabilizes training. Averaging 16 generated continuations gives deterministic downstream features and reduces sampling noise.

Evaluation uses the existing five run-group outer folds. Generator fitting, sensor scaling, and XGBoost fitting occur inside each outer-training partition; validation groups are disjoint, and validation/test use only offset 0. No generated test continuation is used to refit either generator or XGBoost. Report both downstream gas metrics and direct continuation MAE/RMSE on untouched real futures. Repeated seeds and a paired run-level bootstrap are required before accepting a gain.

The progression criterion is stricter than beating the 16-second oracle: generated-16-second XGBoost must improve both gases over the **observed 8-second** baseline on held-out real runs. It must also remain stable across seeds and pass nearest-neighbor/memorization checks. If it does not, generation adds model assumptions but no new measured information, and the observed-prefix XGBoost should be retained. The oracle quantifies the remaining value of physically waiting eight more seconds.

#### Initial five-fold results

The frozen seed-42 run used 100 maximum generator epochs, 16 Monte Carlo continuation samples, and 800-tree XGBoost models. The CVAE stopped after 100, 100, 22, 44, and 49 epochs across folds (mean 63); the cGAN ran for 100, 100, 100, 80, and 100 epochs (mean 96). These epoch counts indicate that the cGAN validation objective usually continued improving until the configured limit, so the result should not be read as a converged architecture comparison.

| XGBoost input | CO MAE | CO RMSE | CO R-squared | Ethylene MAE | Ethylene RMSE | Ethylene R-squared |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Observed first 8 s | 107.055 +/- 8.248 | 136.958 +/- 8.619 | 0.278 +/- 0.115 | 3.690 +/- 0.379 | 5.060 +/- 0.466 | 0.076 +/- 0.158 |
| CVAE: observed 8 s + generated 8 s | 112.648 +/- 10.024 | 143.624 +/- 10.380 | 0.195 +/- 0.195 | 3.503 +/- 0.364 | 4.911 +/- 0.552 | 0.132 +/- 0.145 |
| **cGAN: observed 8 s + generated 8 s** | **105.564 +/- 6.787** | **137.316 +/- 9.365** | **0.270 +/- 0.146** | **3.471 +/- 0.508** | **4.731 +/- 0.710** | **0.196 +/- 0.163** |
| Oracle real first 16 s | 83.426 +/- 7.073 | 113.345 +/- 10.769 | 0.504 +/- 0.106 | 2.772 +/- 0.475 | 3.826 +/- 0.548 | 0.471 +/- 0.119 |

Values are unweighted mean +/- sample standard deviation over the five outer folds. They are substantially worse than the 64-second models elsewhere in this report because the early sensor transient contains much less concentration information. The correct comparison for this experiment is therefore the matched observed-8-second baseline, not the principal 64-second physics XGBoost result.

Relative to observed-8-second XGBoost, the CVAE worsened mean CO MAE by 5.2% (+5.592 ppm) but improved ethylene MAE by 5.1% (-0.187 ppm). It improved ethylene in all five folds but improved CO in only one. The cGAN reduced mean CO MAE by 1.4% (-1.491 ppm) and ethylene MAE by 5.9% (-0.219 ppm), winning four of five fold comparisons for each gas. Its CO RMSE nevertheless increased slightly, from 136.958 to 137.316 ppm, and its mean CO R-squared decreased from 0.278 to 0.270. The CO gain is therefore confined to average absolute error and is too small to establish a robust advantage.

The real-16-second oracle improved CO MAE by 22.1% and ethylene MAE by 24.9% relative to eight seconds, winning all five folds for both gases. The large gap between the oracle and either generator shows that seconds 9-16 contain useful physical information that cannot currently be recovered reliably from the prefix. Generation recovers only a small fraction of the downstream benefit of waiting for the real measurements.

#### Forecast fidelity

Direct continuation errors were calculated in raw sensor-response units across all sensors and future timesteps:

| Future predictor | Sensor MAE | Sensor RMSE |
| --- | ---: | ---: |
| Persistence: repeat the last observed value | **30.368** | **131.575** |
| cGAN Monte Carlo mean | 54.258 | 214.099 |
| CVAE Monte Carlo mean | 125.105 | 362.902 |

The persistence reference was evaluated on the same five offset-0 test folds. Both learned generators forecast the raw continuation worse than simply holding the eighth-second value constant; the cGAN is materially closer than the CVAE but still weak. Because sensor scales differ, these aggregate raw-unit errors should also be supplemented by per-sensor normalized MAE in a follow-up run.

This mismatch is important: the cGAN's small downstream XGBoost improvement does not demonstrate an accurate simulation of the future. Its generated trajectory may act as a nonlinear, smoothed transformation of the observed prefix that happens to change tree features beneficially. Calling those values predicted measurements would overstate the evidence. A direct learned feature transform or supervised temporal encoder could provide the same regularization with fewer generative assumptions.

#### Conclusion and progression decision

The single-seed cGAN provisionally meets the point-MAE part of the progression rule, improving both targets against the observed-8-second baseline, but it does not yet meet the full acceptance rule. The CO effect is small, not consistent across all metrics, and the generated future fails the persistence forecast control. The CVAE is rejected in its current configuration because it sacrifices CO accuracy and has the poorest continuation fidelity.

Before any deployment claim, repeat the cGAN over at least five seeds, report paired run-level bootstrap intervals, add persistence and deterministic MLP/TCN forecasters as mandatory controls, calculate per-sensor scale-normalized errors, and test nearest-neighbor distances against training continuations. The recommended operational choice remains to measure the real 16 seconds when latency permits. If only eight seconds are available, observed-prefix XGBoost is the conservative baseline; the cGAN path is an experimental candidate rather than a validated replacement.

The reproducible implementation is `ec_forecast_xgboost.py`. All 20 fold/model results and 10 generator-forecast records are stored in `ec_forecast_xgboost/results.json`; the captured training log is `ec_forecast_xgboost_run.log`.

### 8.5 Experiment 11: gas-specific expert branches

#### Motivation and architecture

A shared two-output model uses the same feature representation, sensor set, and hyperparameters for CO and ethylene even though the two targets respond differently to sensors and model families. Experiment 11 tests a target-specific mixture-of-experts design. It does not try to suppress the physical concentration of one gas; it minimizes prediction error for each gas independently and joins the two scalar predictions at the output interface.

```text
64 x 16 sensor sequence
  |-- CO branch:       selected features + selected sensor subset + selected regressor --> CO
  `-- Ethylene branch: selected features + selected sensor subset + selected regressor --> C2H4
```

Each gas branch can select summary or physics features; Ridge, Random Forest, Extra Trees, or XGBoost with depth 2, 3, or 4; and either all sensors or one sensor removed. To limit selection cost without touching the outer test fold, the search is sequential:

1. Select model family and feature representation using all sensors.
2. Holding that choice fixed, select all sensors or one of the 16 single-sensor removals.
3. Refit the selected branch on all outer-training samples and predict its one target.
4. Concatenate the independent CO and ethylene predictions for joint scoring.

Selection uses two inner episode-group folds, all five offset windows for fitting, and only offset 0 for inner validation. Tree screening uses 100 trees. A selected XGBoost expert is refitted with 800 trees and a selected forest with 500 trees. Final testing remains the same five untouched outer episode folds with offset 0 only. This nested design prevents the outer test results from choosing a gas branch or sensor removal.

#### Selected experts

| Outer fold | CO expert | CO sensor removed | Ethylene expert | Ethylene sensor removed |
| ---: | --- | ---: | --- | ---: |
| 1 | Summary Extra Trees | 6 | Physics Extra Trees | 14 |
| 2 | Physics Extra Trees | 7 | Physics Extra Trees | 14 |
| 3 | Summary Random Forest | 14 | Summary Extra Trees | 9 |
| 4 | Summary Extra Trees | 10 | Physics Extra Trees | 11 |
| 5 | Physics Extra Trees | 16 | Physics Random Forest | 13 |

Extra Trees was selected in four of five CO folds and four of five ethylene folds. Feature selection was less stable: CO chose summary features in three folds and physics in two, while ethylene chose physics in four folds. No gas selected the same sensor removal across all folds. Ethylene removed Sensor 14 twice; every other choice occurred once. This instability suggests substantial redundancy and a shallow inner-selection surface rather than one reproducible gas-specific hardware layout.

#### Outer-fold results

| Branch | CO MAE | CO RMSE | CO R-squared | Ethylene MAE | Ethylene RMSE | Ethylene R-squared |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **Shared physics XGBoost control** | **13.967 +/- 4.003** | 26.430 +/- 9.179 | **0.968 +/- 0.026** | **0.460 +/- 0.169** | **0.848 +/- 0.520** | **0.966 +/- 0.043** |
| Gas-specific experts | 14.813 +/- 4.996 | **26.153 +/- 11.494** | **0.968 +/- 0.034** | 0.490 +/- 0.172 | 0.909 +/- 0.435 | 0.964 +/- 0.032 |

Values are unweighted mean +/- sample standard deviation across five outer folds. The control is the same physics-XGBoost architecture refitted alongside the experts; its deterministic fold-specific seeds make its mean differ slightly from the earlier fixed-seed principal result of 14.604 ppm CO and 0.443 ppm ethylene. Conclusions are based on the paired control from this experiment.

The specialist system increased CO MAE by 0.846 ppm (6.1%) and ethylene MAE by 0.030 ppm (6.5%). It beat the shared control on CO MAE in only one of five folds and on ethylene MAE in two of five. CO RMSE decreased slightly by 0.277 ppm, but its fold variability increased, and this isolated RMSE change does not offset worse MAE for both targets. The specialized branches therefore fail the primary objective.

#### Interpretation and generalization to more gases

The negative result is informative. Independent output trees in multi-output XGBoost already give each gas target-specific split structures; separating the estimators adds less specialization than it first appears. The shared physics representation is also strong enough that inner selection among many similar sensor subsets overfits which episodes happen to be in two inner folds. The selected sensor removals changing almost every outer fold is direct evidence of this selection variance.

Physics XGBoost remains the best current balanced system. The gas-specific architecture should not replace it. For a future system with more gases, the useful scalable design is a shared feature extractor plus one calibrated output head per gas, but branch creation should be regularized: require repeated nested folds, prefer stable sensor masks, and accept a specialized head only when its paired confidence interval improves that gas without degrading calibration. A multi-objective selector can then minimize a weighted vector of per-gas errors, with weights set by application cost, rather than searching a large independent branch for every target on only 245 runs.

The reproducible implementation is `ec_gas_specific_experts.py`. Ten outer-fold result records and all inner model/sensor rankings are stored in `ec_gas_specific_experts/results.json`; the execution log is `ec_gas_specific_experts_run.log`.

### 8.6 Experiment 12: chronological AE-LSTM for concentration changes

#### Question and data limitation

This experiment tests whether an AE-LSTM benefits from the order of successive fixed-concentration exposures and can recognize increasing or decreasing mixture concentration. It is deliberately different from the original AE-LSTM: the original model reshapes one 256-value encoding into 16 nominal LSTM positions, which are not real time steps. Here, each recurrent step is a real, chronologically later exposure episode.

The available cache contains 245 ordered nonzero exposure episodes, each represented by one unquantized 64 x 16 offset-0 sensor window. It does **not** provide independent session, day, device, or ramp identifiers. Moreover, the cache was produced after removing intervals where both gases were zero. Two adjacent retained episodes can therefore have an unobserved baseline/recovery interval between them. The results below are an exploratory blocked-time comparison on one recording, not evidence of new-session or real-environment generalization.

#### Causal representation and models

Each example contains six consecutive retained exposure episodes:

```text
six ordered 64 x 16 windows
  -> shared encoder (1024 -> 256 -> 32 latent values per episode)
  -> either LSTM across the six real episode latents or an episode-wise MLP
  -> CO and ethylene estimates at every episode step
```

The decoder maps every 32-value latent back to its 64 x 16 sensor window. The two models use the same encoder, decoder, regression head width, preprocessing, batches, optimizer, and losses; their only intended difference is the LSTM temporal-memory layer. The AE-MLP control predicts from each episode latent independently. A previous-true-ppm persistence reference is also reported, but it is not deployable unless the preceding concentration was independently measured.

Sensor channels use a training-only `RobustScaler`, and the two targets use a training-only `StandardScaler`. The joint training loss is

\[
L = L_{\mathrm{Huber}}(\hat y,y)
  + 0.30 L_{\mathrm{Huber}}(\Delta\hat y,\Delta y)
  + 0.10 L_{\mathrm{MSE}}(\hat x,x).
\]

The change term teaches increases and decreases without imposing monotonic growth. It uses predicted differences between adjacent real episode steps. No current or future true ppm is an input to either neural model.

#### Blocked-time evaluation

The 245 episodes remain in original order and are divided into five contiguous 49-episode outer test blocks. Fourteen other contiguous episodes are reserved for early stopping in each fold, alternating before or after the test block where possible. A six-step sequence is retained only if all six episodes belong to the same train, validation, or test partition. Thus, no sequence crosses a boundary. The first five episodes of every test block supply causal context but are not scored, leaving 44 predictions per fold and 220 pooled held-out predictions.

This protocol prevents overlapping sequence leakage across partitions, but it cannot manufacture independent experimental sessions from the single recording. Because temporal drift can differ between contiguous blocks, blocked-fold variability is part of the result rather than noise to hide.

#### Results

| Model | CO MAE (ppm) | CO RMSE | CO R-squared | Ethylene MAE (ppm) | Ethylene RMSE | Ethylene R-squared |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| AE-MLP control | **31.124** | **58.248** | **0.872** | **1.193** | 2.234 | 0.828 |
| Chronological AE-LSTM | 34.718 | 76.260 | 0.781 | 1.231 | **2.163** | **0.839** |
| Previous-true-ppm persistence | 126.667 | 187.026 | -0.318 | 3.940 | 6.176 | -0.314 |

These are pooled predictions, so MAE and RMSE weight every evaluated episode equally. Relative to the matched AE-MLP, the AE-LSTM increased CO MAE by 11.5%, CO RMSE by 30.9%, and ethylene MAE by 3.2%. It reduced ethylene RMSE by 3.2%. The LSTM has a -12.212 ppm CO bias versus +4.865 ppm for the MLP; its CO 90th-percentile absolute error is 70.151 ppm versus 52.747 ppm.

| Model | CO direction, all transitions | CO direction when changed | Ethylene direction, all transitions | Ethylene direction when changed |
| --- | ---: | ---: | ---: | ---: |
| AE-MLP control | 58.6% | 94.6% | 66.5% | **98.3%** |
| Chronological AE-LSTM | **61.4%** | **96.1%** | **67.4%** | 97.5% |
| Previous-true-ppm persistence | 48.8% | 31.8% | 48.4% | 23.1% |

Direction is rising, stable, or falling based on consecutive predictions, with deadbands of 1 ppm for CO and 0.25 ppm for ethylene. Fold boundaries are excluded. There are 129 true CO-change transitions and 121 true ethylene-change transitions. High changed-transition accuracy does not mean the next concentration was forecast in advance: the model observes the current episode's sensor window before classifying its change from the previous episode. The lower all-transition accuracy shows that both neural models often predict small movements during truly stable transitions.

| Fold | AE-MLP CO MAE | AE-LSTM CO MAE | AE-MLP ethylene MAE | AE-LSTM ethylene MAE |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 41.997 | 95.098 | 2.656 | 2.674 |
| 2 | 22.570 | 16.555 | 0.919 | 0.957 |
| 3 | 35.402 | 16.220 | 0.927 | 0.806 |
| 4 | 28.913 | 23.960 | 0.592 | 0.648 |
| 5 | 26.740 | 21.755 | 0.871 | 1.070 |

The AE-LSTM improves CO MAE in four folds but fails severely in fold 1, producing much worse pooled CO RMSE and high variability. Mean +/- sample standard deviation of fold CO MAE is 34.718 +/- 33.918 ppm for the LSTM and 31.124 +/- 7.645 ppm for the MLP. Temporal context is therefore not reliably beneficial under the available chronology.

#### Decision and required follow-up

The chronological AE-LSTM is **not accepted as a replacement** for the current physics-XGBoost baseline or even its matched AE-MLP control. The experiment shows that real recurrent steps are technically feasible and can slightly improve direction recognition, but it does not show a robust concentration-accuracy gain. It also remains materially worse than the earlier group-safe physics-XGBoost result, although the split protocols are different and should not be treated as a direct paired comparison.

A deployment-oriented repeat requires separately recorded sessions containing baseline, rise, plateau, decrease, and recovery; independently varied CO/ethylene ratios; different ramp rates; humidity and temperature variation; interferent gases; and preferably different days and devices. Entire sessions must be assigned to train, validation, or test. Baseline intervals must remain in the sequence, and a causal online evaluation should score latency after a change as well as ppm error, false trend alarms, calibration, and out-of-range detection. With those data, the next comparison should include absolute-plus-delta heads, GRU and LSTM variants, the memoryless control, physics-XGBoost, and at least five training seeds.

The reproducible implementation is `ec_chronological_ae_lstm.py`. Full fold predictions, metrics, configuration, and the protocol warning are stored in `ec_chronological_ae_lstm/results.json`; console output is stored in `ec_chronological_ae_lstm/run.log`.

### 8.7 Experiment 13: denoising AE, physics features, and residual correction

#### Purpose and leakage-safe design

This experiment tests whether an unsupervised denoising front end can improve the established physics-XGBoost model. It separates three possible effects: replacing raw signals with reconstructed signals, adding reconstruction-derived information to the raw physics representation, and correcting the remaining hybrid-model error with a second XGBoost stage.

The five existing episode-group outer folds are retained. All five offset windows from an outer-training episode are available for DAE and XGBoost fitting, while only offset 0 is evaluated for each held-out episode. Every `RobustScaler`, DAE, base XGBoost model, and residual model is fitted without outer-test data.

Residual stacking uses an additional nested procedure. Within each outer-training partition, three group folds create out-of-fold hybrid predictions. The DAE is refitted using only the corresponding inner-training groups, so even the unsupervised transform does not see inner-validation signals. Residual targets are

\[
r_i = y_i - \hat y_i^{\mathrm{OOF}}.
\]

A second three-fold group split of this meta-dataset selects a correction multiplier independently for CO and ethylene from `0, 0.25, 0.5, 0.75, 1.0`. Allowing zero is a safety mechanism: when residual learning is not repeatable, the pipeline retains the base prediction rather than forcing a correction selected on in-sample errors.

#### DAE and feature construction

The DAE processes a scaled 64 x 16 sensor window through a `1024 -> 256 -> 64 -> 256 -> 1024` multilayer encoder-decoder. It is trained for 100 epochs to reconstruct the clean training window after simulated calibration-like corruption:

- Gaussian point noise with standard deviation 0.05 in robust-scaled units.
- Per-sensor multiplicative gain noise with standard deviation 0.02.
- Per-sensor baseline displacement with standard deviation 0.03.
- Two-percent probability of dropping an entire sensor channel for a training example.

These values are frozen feasibility settings rather than noise estimates measured from independent calibration trials. Four downstream representations are compared with an otherwise identical 500-tree depth-3 XGBoost configuration:

1. `raw_physics`: the 208 established physics features from the original window.
2. `denoised_physics`: the same 208 features calculated only from DAE reconstruction.
3. `hybrid_physics`: raw physics, denoised physics, their difference, and 16 per-sensor reconstruction errors.
4. `hybrid_residual`: hybrid prediction plus the nested out-of-fold residual correction.

The residual models use 200 depth-2 trees and receive hybrid features plus the two base predictions.

#### Five-fold results

| Model | CO MAE | CO RMSE | CO R-squared | Ethylene MAE | Ethylene RMSE | Ethylene R-squared |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **Raw physics control** | **14.376 +/- 3.679** | **25.333 +/- 9.313** | **0.971 +/- 0.026** | **0.464 +/- 0.187** | **0.848 +/- 0.542** | **0.965 +/- 0.045** |
| Denoised physics | 33.883 +/- 9.992 | 67.009 +/- 24.116 | 0.818 +/- 0.102 | 0.969 +/- 0.291 | 1.671 +/- 0.653 | 0.892 +/- 0.067 |
| Hybrid physics | 18.565 +/- 3.714 | 33.883 +/- 10.301 | 0.953 +/- 0.029 | 0.597 +/- 0.203 | 1.030 +/- 0.480 | 0.955 +/- 0.040 |
| Hybrid + residual | 18.565 +/- 3.714 | 33.883 +/- 10.301 | 0.953 +/- 0.029 | 0.595 +/- 0.205 | 1.014 +/- 0.494 | 0.955 +/- 0.040 |

Values are unweighted mean +/- sample standard deviation across the same five outer folds. The raw control differs slightly from the earlier 14.604/0.443 ppm result because this experiment freezes a 500-tree histogram configuration and refits it alongside every ablation; conclusions use this paired control.

| Fold | Raw CO MAE | Denoised CO | Hybrid CO | Raw ethylene MAE | Denoised ethylene | Hybrid ethylene |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | **11.881** | 35.770 | 14.764 | **0.283** | 1.197 | 0.421 |
| 2 | **13.191** | 22.077 | 15.981 | **0.415** | 0.625 | 0.509 |
| 3 | **14.562** | 25.686 | 17.004 | **0.350** | 0.688 | 0.423 |
| 4 | **20.616** | 39.398 | 22.673 | **0.763** | 1.237 | 0.803 |
| 5 | **11.632** | 46.485 | 22.404 | **0.511** | 1.098 | 0.828 |

Raw physics wins both target MAEs in every fold. Denoising alone increases mean CO MAE by 135.7% and ethylene MAE by 108.7%. Adding raw features back in limits the damage, but the hybrid still increases CO MAE by 29.1% and ethylene MAE by 28.6%. Reconstruction therefore removes or distorts concentration-relevant variation that the raw physics features and trees already use effectively. The larger hybrid feature set also introduces many correlated, lower-quality predictors on a dataset with only 245 independent episodes.

#### Residual behavior and decision

The selected CO correction multiplier is zero in all five outer folds. For ethylene it is 0.25 in fold 1 and zero in folds 2-5. Consequently, residual correction leaves every CO prediction unchanged and changes only one fold of ethylene, reducing overall ethylene MAE from 0.597 to 0.595 ppm. This is not a meaningful improvement over hybrid physics, and both remain worse than raw physics. The zero selections are useful negative evidence: nested validation correctly detects that the residual pattern is not stable enough to apply outside its training folds.

Experiment 13 is rejected as an accuracy upgrade. Raw physics-XGBoost remains the recommended model. This does not establish that denoising is universally harmful; it establishes that this synthetic corruption model and reconstruction objective do not improve clean controlled-test accuracy. A future denoising study is justified only after collecting paired clean/corrupted measurements or independent environmental sessions with measured drift, humidity, temperature, and interference. Those data could support corruption magnitudes grounded in measurement, sensor-specific noise models, and a supervised denoising loss that explicitly preserves concentration-sensitive slopes and deltas.

The reproducible implementation is `ec_dae_physics_residual.py`. All 20 outer-fold result records, predictions, residual multipliers, DAE losses, and summary statistics are stored in `ec_dae_physics_residual/results.json`; console output is stored in `ec_dae_physics_residual/run.log`.

### 8.8 Experiment 14: physics-supervised AE representations with XGBoost

#### Motivation

The raw 64-timestep response contains more information than its instantaneous amplitudes. Each gas-mixture exposure also has a physically interpretable shape: how quickly each sensor changes, the integrated response, when it reaches a peak or plateau, and the level and noise during the plateau. The next experiment should therefore make the autoencoder preserve both the complete sensor sequence and these response-shape descriptors, then use XGBoost for concentration regression.

This is different from calculating physics features after an ordinary reconstruction-only AE. A reconstruction loss can give little weight to short but concentration-relevant transitions. Here, an auxiliary physics head explicitly predicts the engineered descriptors from the bottleneck, so the latent vector is penalized when it discards them.

```text
64 x 16 float32 sensor response
  -> baseline correction and training-only robust scaling
  -> temporal encoder -> latent vector z
       |-> decoder -> reconstructed 64 x 16 response
       `-> physics head -> predicted response-shape features

XGBoost input = latent z [+ measured physics features]
  -> independent CO and ethylene concentration predictions
```

#### Physical representation of one exposure

Features must be calculated from the natural `64 timesteps x 16 sensors` array before column repetition, image conversion, or uint8 quantization. Let \(x_{t,s}\) be sensor \(s\)'s response at timestep \(t\), and let \(b_s\) be its pre-exposure baseline. Prefer a real baseline segment; if none exists, the median of the first \(k=5\) exposure samples is only a documented proxy. Define

\[
r_{t,s}=x_{t,s}-b_s, \qquad
r^{rel}_{t,s}=\frac{x_{t,s}-b_s}{|b_s|+\epsilon}.
\]

For each of the 16 sensors, calculate the following descriptors on both the absolute and, where meaningful, relative response:

| Feature group | Definition or recommended calculation |
| --- | --- |
| Initial/final response | first value, last value, and final-minus-initial change |
| Overall slope | least-squares slope of response against elapsed time over all 64 steps |
| Local slopes | slopes over early (steps 0-15), middle (16-39), and late (40-63) intervals |
| Slope change | late slope minus early slope; also maximum and mean absolute first derivative |
| Curvature | mean and maximum absolute second difference, which describe bending toward a plateau |
| Area under curve | trapezoidal integral \(AUC_s=\sum_t (r_{t,s}+r_{t+1,s})\Delta t/2\); also absolute AUC and AUC divided by duration |
| Extrema | minimum, maximum, peak magnitude, peak prominence, and their timestep indices |
| Time to peak | elapsed time from exposure start to the maximum absolute baseline-corrected response |
| Rise times | time to first cross 10%, 50%, and 90% of the signed peak excursion |
| Plateau/stable onset | earliest timestep after which a rolling-window slope and variability remain below training-derived thresholds for at least \(m\) consecutive steps |
| Stable level | mean, median, minimum, maximum, range, standard deviation, and coefficient of variation from stable onset through step 63 |
| Overshoot | signed peak minus stable median, divided by absolute stable median plus \(\epsilon\) |
| Dynamic noise | residual RMSE around the late-window linear fit and mean rolling standard deviation |

The sampling interval must come from timestamps rather than assuming exactly one second. Derivatives are divided by the actual \(\Delta t\), and AUC is expressed in response-seconds. If timestamps are irregular, use their real values directly in the regression slopes and trapezoidal integral.

Plateau detection requires a deterministic definition. A suitable starting rule uses an 8-step trailing window and declares stability when both

\[
|\operatorname{slope}(w)| < \tau_{slope,s}, \qquad
\operatorname{MAD}(w) < \tau_{noise,s}
\]

hold for three consecutive windows. Thresholds are estimated from late windows in the **outer-training episodes only**, separately per sensor. If no plateau is detected, do not pretend that the response stabilized: set a `stable_found` indicator to zero, set `stable_onset` to the window end for fixed-shape computation, and include the indicator so XGBoost and the AE can distinguish a censored value from a real plateau. Time-to-peak and rise-time features likewise need `peak_at_boundary` and `threshold_reached` indicators when the 64-step window ends too soon.

In addition to per-sensor descriptors, add compact mixture-level interactions: pairwise response correlations, the mean and dispersion of sensor slopes/AUCs, the number of sensors reaching a plateau, and selected sensor-response ratios. Ratios require a signed epsilon and clipping thresholds learned from training data to prevent numerical explosions. Keep an explicit feature-name manifest and remove constant or non-finite features using training data only.

#### Physics-supervised autoencoder

Use a temporal encoder rather than the previous square-image convolution. A practical small-data architecture is:

```text
Input (64, 16)
  -> Conv1D(64, kernel 5) + normalization + GELU
  -> two residual/dilated Conv1D blocks
  -> global average pool + global max pool
  -> Dense latent z (32 or 64 values)
```

The decoder reconstructs the `64 x 16` float32 sequence. A second MLP head predicts the standardized physical feature vector \(p\) from \(z\). Train with

\[
L = \lambda_{rec} L_{Huber}(x,\hat{x})
  + \lambda_{phys} L_{Huber}(\tilde p,\hat{\tilde p})
  + \lambda_{deriv} L_{Huber}(\Delta x,\Delta\hat{x}),
\]

where every physics feature is median/IQR standardized using outer-training episodes. The derivative term prevents an apparently smooth reconstruction from erasing slope changes. Begin with `lambda_rec=1.0`, `lambda_phys=1.0`, and `lambda_deriv=0.25`, but select these weights only inside grouped inner validation. Apply masks to undefined/censored continuous targets and use binary cross-entropy for `stable_found`, `threshold_reached`, and similar indicators.

Concentration labels are not needed for AE pretraining, but the engineered descriptor targets are derived from each input response. The auxiliary task therefore injects a physical inductive bias without leaking gas concentration into representation learning. Fit the input scaler, physics-feature scaler, plateau thresholds, AE, and every feature filter using outer-training episodes only.

#### XGBoost regression and required ablations

After AE training, freeze the encoder and extract one latent vector per exposure window. Train one XGBoost regressor for CO and one for ethylene; separate estimators allow gas-specific trees, hyperparameters, and feature importances. Compare four representations under exactly the same episode-group folds:

1. **Physics-only XGBoost:** measured engineered descriptors; this remains the mandatory interpretable control.
2. **Ordinary AE latent + XGBoost:** reconstruction/derivative AE without the physics head; this isolates the value of physics supervision.
3. **Physics-supervised AE latent + XGBoost:** latent vector \(z\) only; this tests whether the AE actually internalizes a compact physical representation.
4. **Physics-supervised AE latent + measured physics + XGBoost:** concatenate \(z\) with the descriptors; this tests whether the learned latent contributes information beyond the explicit features.

Do not append the AE's predicted physics vector to the measured physics vector: it is mostly a noisier duplicate. It can be useful at deployment only when the explicit feature calculation is unavailable, in which case it must be evaluated as a separate ablation.

Hyperparameters such as tree depth, learning rate, number of trees, row/column subsampling, latent width, and AE loss weights are selected in inner `GroupKFold` splits by exposure/run ID. All five offset variants from one physical exposure remain in the same partition. Fit augmented offsets only in training; report the primary test metric on offset 0 so nearly identical windows do not inflate the apparent sample size.

#### Evaluation and acceptance criteria

Report CO and ethylene MAE, RMSE, signed bias, 90th-percentile absolute error, and R-squared in physical ppm for every outer fold. Also report physics-head MAE per descriptor family, plateau-detection precision/recall, time-to-peak error in seconds, and reconstruction errors for both amplitude and first derivative. Use run-level paired bootstrap confidence intervals to compare each new representation with physics-only XGBoost.

The physics-supervised AE should be accepted only if it improves held-out concentration error consistently across folds or achieves statistically equivalent error with a materially smaller representation. A lower AE reconstruction loss is not sufficient. Feature attribution should also be checked with XGBoost gain/SHAP summaries to verify whether slopes, AUC, rise/plateau timing, and stable levels contribute consistently rather than merely encoding episode or drift artifacts.

Given the current 245 independent episodes, the expected strongest first candidate remains the hybrid `latent + measured physics` model, while physics-only XGBoost is likely to remain difficult to beat. The experiment is nevertheless valuable because it directly tests the requested hypothesis: whether an AE forced to encode response dynamics can add useful nonlinear information beyond hand-engineered physical descriptors.

#### NH3/H2 validation result

The proposed pipeline was implemented and evaluated on `DATA_H2_NH3.xlsx`. The workbook contains 35 independent exposure classes, 1,500 readings per exposure, 10 sensor channels, and two concentration columns spanning 0-350 ppm. The concentration columns are named only `Gas A` and `Gas B`; the workbook and companion notebook do not provide a verified mapping from those columns to NH3 and H2. Results therefore retain the source names instead of guessing the gas order.

For every exposure, five 64-step windows were sampled at row offsets 0-4 with stride 5. In each of five seeded outer folds, all windows from 28 exposure classes were used for training and the offset-0 window from seven untouched classes was used for testing. Input scaling, physics scaling, constant-feature removal, AE validation, AE fitting, and XGBoost fitting excluded the outer-test classes. The AE epoch was selected using an exposure-group validation subset of the outer training fold and the model was then refitted on all outer-training exposures for that epoch count. Deterministic PyTorch/CuDNN execution was enabled.

The feasibility implementation produces 370 physical descriptors: 37 descriptors for each of 10 sensors. They include overall/early/middle/late slope, slope change, derivatives, curvature, signed and absolute AUC, extrema, time to peak, 10/50/90% rise time and reached flags, stability detection and onset, stable mean/median/minimum/maximum/range/standard deviation/CV, overshoot, and boundary/censoring indicators. Because the workbook has no independently identified stable calibration segments, this run uses a frozen relative plateau rule of 2% response range per median time step for slope and 3% response range for rolling MAD. These thresholds are feasibility assumptions, not experimentally calibrated sensor limits.

| XGBoost representation | Gas A MAE | Gas A RMSE | Gas A R-squared | Gas B MAE | Gas B RMSE | Gas B R-squared |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Physics features only | 27.435 | 35.269 | 0.876 | **13.589** | **17.135** | **0.971** |
| Ordinary AE latent | **24.097** | 36.121 | 0.870 | 21.105 | 32.536 | 0.896 |
| Physics-supervised AE latent | 34.223 | 60.648 | 0.634 | 23.925 | 34.700 | 0.881 |
| Physics-supervised latent + physics | 24.888 | **32.676** | **0.894** | 13.830 | 19.125 | 0.964 |

The table reports pooled predictions for all 35 held-out exposures. The unweighted five-fold mean +/- sample SD of hybrid MAE is 24.888 +/- 9.414 ppm for Gas A and 13.830 +/- 4.086 ppm for Gas B. The corresponding physics-only values are 27.435 +/- 7.429 and 13.589 +/- 1.756 ppm.

A 10,000-resample paired exposure-level bootstrap compared each model with physics-only XGBoost:

| Candidate | Target | MAE difference, candidate minus physics | Paired 95% interval | Probability candidate is better |
| --- | --- | ---: | ---: | ---: |
| Ordinary AE latent | Gas A | -3.338 ppm | [-13.478, 8.182] | 74.1% |
| Ordinary AE latent | Gas B | +7.516 ppm | [0.642, 15.755] | 1.3% |
| Physics-supervised latent | Gas A | +6.788 ppm | [-7.654, 24.827] | 21.7% |
| Physics-supervised latent | Gas B | +10.336 ppm | [3.692, 17.702] | 0.1% |
| Physics-supervised latent + physics | Gas A | -2.547 ppm | [-7.637, 2.048] | 84.9% |
| Physics-supervised latent + physics | Gas B | +0.241 ppm | [-2.815, 3.388] | 44.1% |

The hybrid representation gives a promising but inconclusive 9.3% reduction in Gas A MAE and no meaningful Gas B improvement. Its confidence intervals cross zero for both targets. The latent-only physics-supervised model is rejected: it is worse on both pooled target MAEs and suffers a severe Gas A failure in outer fold 4. The ordinary AE latent also cannot replace the physics control because its possible Gas A improvement is uncertain and its Gas B degradation is supported by the paired interval.

Physics-only XGBoost therefore remains the accepted balanced model for this dataset. The hybrid should be treated as an experimental Gas A candidate, not a validated upgrade. With only 35 unique mixture exposures and no repeated sessions, days, devices, temperature/humidity conditions, or verified NH3/H2 column mapping, these results validate interpolation to held-out mixture combinations in this workbook only. They do not establish real-world NH3/H2 generalization. A stronger follow-up requires repeated exposures and entire-session outer folds, then multiple neural seeds and plateau thresholds calibrated from measured stable periods.

The reproducible implementation is `nh3h2_physics_ae_xgboost.py`. Complete fold metrics, pooled metrics, 10,000-draw paired bootstrap results, feature names, and all 140 held-out model predictions are stored in `nh3h2_physics_ae_xgboost/results.json`; the flat prediction table is `nh3h2_physics_ae_xgboost/predictions.csv`.

### 8.9 Experiment 15: CO/ethylene pretraining and transfer to NH3/H2

#### Corrected experiment order

Experiment 14 above trains the AE directly on the NH3/H2 workbook and is a target-only feasibility test. It does not answer the transfer-learning question. The corrected experiment first trains and evaluates the representation on CO/ethylene, then fits a final source representation on all CO/ethylene exposures, transfers its weights to the NH3/H2 pipeline, and trains new target-specific XGBoost regressors.

The two datasets have different input widths: CO/ethylene has 16 sensors and NH3/H2 has 10. A conventional Conv1D layer that treats sensors as input channels cannot be transferred directly. Experiment 15 therefore uses one temporal encoder shared across individual sensor traces:

```text
each 64-step sensor trace
  -> shared temporal Conv1D encoder
  -> 16-value sensor latent
  -> concatenate sensor latents in declared sensor order
  -> zero-pad unused positions to 16 sensors
  -> gas-specific XGBoost
```

The decoder and 37-output physics head are shared in the same way. The physics head predicts slope, derivatives, curvature, AUC, peak/rise/plateau timing, stable statistics, overshoot, and censoring indicators for each sensor. This makes every neural weight structurally compatible with either 16 or 10 sensors while retaining sensor position for the downstream tree model. Only the representation is transferred. The CO/ethylene XGBoost model is not transferred because NH3/H2 has different target variables and sensor identities.

#### Source-domain training and evaluation

The source evaluation uses the existing five episode-group folds over 245 CO/ethylene exposures. Five offset windows from outer-training episodes are fitted, and only offset 0 is scored for each held-out episode. Each source-fold AE and both XGBoost heads exclude that fold. After evaluation, a separate final AE is fitted on all source exposures to create the transfer checkpoint.

| Source representation | CO MAE | CO RMSE | CO R-squared | Ethylene MAE | Ethylene RMSE | Ethylene R-squared |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Transfer-compatible physics only | 36.656 +/- 3.812 | 59.208 +/- 10.075 | 0.858 +/- 0.062 | 1.523 +/- 0.244 | 2.503 +/- 0.359 | 0.767 +/- 0.080 |
| **Source AE latent** | **14.586 +/- 3.439** | 24.903 +/- 7.735 | **0.974 +/- 0.015** | **0.621 +/- 0.278** | **1.154 +/- 0.505** | **0.944 +/- 0.048** |
| Source AE latent + physics | 14.613 +/- 2.300 | **24.898 +/- 6.324** | **0.975 +/- 0.015** | 0.658 +/- 0.326 | 1.213 +/- 0.565 | 0.937 +/- 0.054 |

Values are unweighted mean +/- sample standard deviation across five held-out source folds. The transferable AE latent clearly learns a useful CO/ethylene representation before target transfer. Its source results are not directly comparable with the earlier optimized 208-feature physics baseline because this experiment deliberately uses a sensor-wise shared architecture and a padded 16-sensor representation to make cross-dataset transfer possible.

#### Target-domain transfer protocol

NH3/H2 retains the same five outer folds of seven held-out mixture exposures. Target sensor and physics scalers are fitted from each outer-training partition. A new target XGBoost model is always fitted because the gas targets differ. Seven target representations are compared:

1. Physics only.
2. Target AE trained from scratch: latent and latent + physics.
3. Frozen CO/ethylene encoder: latent and latent + physics.
4. CO/ethylene encoder fine-tuned for 40 epochs on target outer-training responses: latent and latent + physics.

No NH3/H2 outer-test response or concentration is used for target scaling, AE fine-tuning, or XGBoost fitting. Source pretraining may use all CO/ethylene data because it is a distinct domain with no shared exposure records. Neural execution is deterministic.

| NH3/H2 representation | Gas A MAE | Gas A RMSE | Gas A R-squared | Gas B MAE | Gas B RMSE | Gas B R-squared |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Physics only | 25.167 +/- 5.985 | 31.317 +/- 8.328 | 0.755 +/- 0.216 | 15.944 +/- 5.581 | 19.591 +/- 7.662 | 0.946 +/- 0.041 |
| Target scratch latent | 19.483 +/- 3.562 | 25.030 +/- 4.917 | 0.789 +/- 0.241 | 20.719 +/- 8.024 | 25.428 +/- 9.805 | 0.858 +/- 0.208 |
| **Target scratch latent + physics** | **18.456 +/- 3.990** | **22.177 +/- 5.648** | 0.805 +/- 0.244 | 15.368 +/- 4.749 | 19.745 +/- 6.572 | 0.927 +/- 0.091 |
| Frozen source latent | 23.672 +/- 5.058 | 29.757 +/- 7.292 | 0.795 +/- 0.169 | 14.105 +/- 2.704 | 16.873 +/- 2.593 | 0.963 +/- 0.024 |
| Frozen source latent + physics | 23.594 +/- 4.922 | 29.733 +/- 7.141 | 0.784 +/- 0.183 | 13.346 +/- 0.891 | 16.930 +/- 2.227 | 0.951 +/- 0.058 |
| Fine-tuned source latent | 24.028 +/- 10.021 | 30.535 +/- 11.448 | 0.791 +/- 0.172 | **11.446 +/- 2.125** | 14.782 +/- 2.826 | 0.970 +/- 0.024 |
| Fine-tuned source latent + physics | 22.881 +/- 9.567 | 29.162 +/- 11.723 | **0.823 +/- 0.142** | 11.520 +/- 2.185 | **14.781 +/- 3.461** | **0.971 +/- 0.022** |

Transfer is target-dependent. Relative to physics-only XGBoost, fine-tuned latent + physics reduces Gas A MAE by 2.286 ppm and Gas B MAE by 4.423 ppm. A 10,000-resample paired exposure bootstrap gives intervals of [-9.211, 5.346] ppm for Gas A and [-7.371, -1.736] ppm for Gas B. Thus the Gas B transfer benefit is supported on this workbook, while the Gas A benefit is uncertain.

Relative to the stronger target-scratch latent + physics control, fine-tuned transfer is worse by 4.425 ppm for Gas A, with interval [-1.865, 11.391], but better by 3.847 ppm for Gas B, with interval [-6.767, -1.037]. The pretrained source representation therefore transfers useful dynamics for Gas B but is not a universal improvement. A gas-specific target system would select scratch latent + physics for Gas A and fine-tuned transfer latent or latent + physics for Gas B, with that selection performed inside nested target validation rather than from the outer results reported here.

The corrected conclusion is that CO/ethylene pretraining **does transfer**, but selectively: it materially improves Gas B and does not reliably improve Gas A over training the same representation from scratch. Deployment is still unsupported because the target workbook has only 35 unique mixture exposures, no repeated sessions/devices/environmental conditions, and no verified mapping of `Gas A` and `Gas B` to NH3 and H2.

The implementation is `ec_to_nh3h2_transfer.py`. Full source and target fold metrics and predictions are stored in `ec_to_nh3h2_transfer/results.json` and `ec_to_nh3h2_transfer/predictions.csv`. The transferable source checkpoint is `ec_to_nh3h2_transfer/source_pretrained_ae.pt`.
