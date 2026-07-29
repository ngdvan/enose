# Master Plan: IEEE-Style Sensor-Aware Transfer-Learning Report

## 1. Purpose and deliverables

This folder will contain a self-contained, IEEE-style Markdown paper describing and evaluating sensor-aware, same-device self-supervised transfer learning for multigas electronic-nose regression. The completed deliverables will be:

1. `sensor_aware_transfer_learning_report.md`: the paper, written in formal scientific English and organized like an IEEE conference/journal manuscript.
2. `figures/*.svg`: every figure in editable vector format. Markdown will reference only these SVG files.
3. `figure_manifest.md`: a traceability table connecting each figure to its source data, generation method, and paper location.
4. Reproducibility/support scripts, if needed, used only to extract existing results and generate SVG figures. No metric will be fabricated or inferred without an explicit formula and source artifact.

The paper will distinguish measured experimental results from proposed future experiments. Results will be sourced from the JSON and CSV artifacts under `../results/`; dataset and method details will be checked against `../README.md`, `../reports/`, and `../code/`.

## 2. IEEE paper structure

### Title, authorship placeholder, abstract, and index terms

- Use a concise technical title emphasizing sensor-aware self-supervised transfer, label-efficient calibration, and cross-system validation.
- Leave author names and affiliations as explicit placeholders because they are not available in the repository.
- Abstract structure: problem, proposed method, two-system protocol, principal full-budget and low-label findings, and limitations.
- Index terms: electronic nose, transfer learning, self-supervised learning, gas sensing, sensor arrays, domain adaptation, regression.

### I. Introduction

The introduction will explain:

- Why electronic-nose calibration is costly: labels require controlled gas preparation, repeated exposures, and recalibration under drift/session changes.
- Why ordinary supervised models are label-hungry and why cross-device/cross-gas transfer can fail when sensor identities and response physics differ.
- The motivation for exploiting abundant unlabeled signals from the *same physical sensor system*.
- The research hypothesis: masked reconstruction that preserves sensor identity and models cross-sensor interactions yields a reusable representation and improves label efficiency.
- The study contributions:
  1. a shared temporal CNN plus learned sensor-identity embeddings and cross-sensor Transformer;
  2. sensor-aware masked pretraining with temporal-span and complete-channel masking;
  3. leakage-controlled adaptation and chronological/session holdout validation;
  4. evaluation on public CO/ethylene and private NH3/H2 datasets with different gases and array sizes;
  5. comparisons with scratch, frozen transfer, fine-tuned transfer, physics-feature tree models, label-budget studies, and available ablations.

The introduction will avoid claiming universal transfer across arbitrary devices. The evidence supports repeatability across two sensor systems/datasets, with same-system pretraining and adaptation in each.

### II. Methodology

#### A. Problem formulation

- Define one exposure as a multivariate sequence \(X_i\in\mathbb{R}^{T\times S}\), with \(T=64\) and system-dependent sensor count \(S\in\{16,20\}\).
- Define the two-gas target \(y_i\in\mathbb{R}^{2}\).
- Define disjoint unlabeled pretraining set \(\mathcal U\), labeled adaptation set \(\mathcal A_K\) with budget \(K\), and untouched test set \(\mathcal T\).
- State the objective: learn encoder \(f_\theta\) from \(\mathcal U\), then regressor \(g_\phi\) from a small \(\mathcal A_K\), minimizing held-out two-target prediction error without using test samples in scaling, pretraining, model selection, or fitting.

#### B. Preprocessing and calibration-pair selection

- Explain exposure segmentation, 64-sample windows, per-dataset offsets, and why augmented windows from one exposure never cross task boundaries.
- Describe robust per-sensor scaling fit exclusively on pretraining data.
- Formalize seeded farthest-point sampling in normalized concentration space for representative low-budget calibration pairs.

#### C. Sensor-aware encoder

- Shared dilated temporal CNN per sensor: captures response dynamics while sharing statistical strength.
- Mean/max temporal pooling and projection into 32-dimensional tokens.
- Learned physical sensor identity embeddings: preserve channel semantics.
- Two-layer, four-head Transformer: captures cross-sensor selectivity and interactions.
- Multilayer, two-output regression head.
- Include parameter/configuration table based on executable code and recorded configuration.

#### D. Self-supervised masked reconstruction

- Define visibility mask \(M\), three random temporal spans, and masking of one to three complete sensors.
- State that the network receives both corrupted values and visibility indicators.
- Present the hidden-sample reconstruction MSE plus 0.05-weighted visible-sample MSE.
- Explain the inductive purpose of span masking and complete-sensor masking.

#### E. Adaptation policies and baselines

- Scratch: identical architecture trained without pretrained weights.
- Frozen: pretrained encoder fixed; only regression head trained.
- Fine-tuned: pretrained encoder updated with a smaller learning rate than the head.
- Physics-feature baselines: Extra Trees and/or matched XGBoost, with dataset-specific descriptor counts exactly as recorded.
- Identify which comparisons exist for each dataset and do not imply a baseline was run where no artifact exists.

#### F. Metrics and statistical reporting

For gas target \(j\), define:

- \(\mathrm{MAE}_j=N^{-1}\sum_i|y_{ij}-\hat y_{ij}|\).
- \(\mathrm{RMSE}_j=\sqrt{N^{-1}\sum_i(y_{ij}-\hat y_{ij})^2}\).
- \(R_j^2=1-\sum_i(y_{ij}-\hat y_{ij})^2/\sum_i(y_{ij}-\bar y_j)^2\).
- 90th-percentile absolute error \(Q_{0.9,j}\), computed directly from held-out prediction CSVs when predictions for the applicable run/model are present.
- Relative MAE versus test mean and versus full scale where saved.
- Mean and standard deviation across seeds 42, 142, and 242.
- Percentage improvement relative to scratch or baseline: \(100(E_b-E_p)/E_b\).

If a requested metric cannot be reconstructed from saved artifacts, the paper will say so explicitly rather than manufacture it.

#### G. Validation protocol

- NH3/H2: sessions 1--4 pretraining, session 5 adaptation, session 6 test.
- CO/ethylene: chronological blocks 1--3 pretraining, block 4 adaptation, block 5 future test.
- Explain raw-exposure independence, augmentation controls, scaler isolation, and use of a single offset-zero test window.
- Explain the three repeated seeded calibration selections and model initializations.
- State that CO/ethylene blocks are chronological proxies because documented session IDs are unavailable.

#### H. Full-method diagram

Create `figures/method_pipeline.svg` showing the complete flow: raw exposures -> task split -> pretraining-only scaler -> windowing -> sensor-aware masked autoencoder -> adaptation policy branches -> two-gas predictions -> held-out metrics. It will visually mark leakage barriers and the distinction between unlabeled and labeled stages.

### III. Data and Experiments

#### A. CO/ethylene public dataset

- Identify it as the established public CO/ethylene electronic-nose benchmark, but avoid an external bibliographic claim until a reliable source/citation is supplied or verified.
- Report 245 chronological exposures, 16 channels, five 64-sample windows per exposure, 1,225 prepared windows, and 24 unique pairs in the adaptation block.
- Explain contiguous 49-exposure blocks and task allocation.
- Describe target units/ranges only where confirmed by repository artifacts.

#### B. Private NH3/H2 dataset

- Clearly label it private.
- Report 162,404 rows, 378 exposures, six sessions of 63 exposures, 20 channels, and 57 unique concentration pairs per session.
- Explain five offset windows for pretraining/adaptation, a single offset-zero window for testing, and modal correction of 11 transition-row labels.
- State data-access limitations appropriate for a private dataset.

#### C. Cross-system role of the two datasets

- Explain that they differ in gases, sensor counts, acquisition organization, and concentration scale.
- Frame replication across both as evidence that the method is not tied to one gas pair or one array dimensionality.
- Avoid claiming direct source-to-target transfer between the two systems; each uses same-system unlabeled pretraining.

#### D. Experimental settings

- Tables for dataset splits, labeled budgets, model architecture, training epochs, optimizers, learning rates, weight decay, loss, batch size, clipping, and masking settings.
- State all budgets: NH3/H2 \(K=5,10,20,40,57\); CO/ethylene \(K=5,10,20,24\).
- Explain the test unit (one independent exposure, not augmented windows).

#### E. Dataset/protocol figures

- `figures/dataset_splits.svg`: side-by-side session/block timelines with counts and leakage barriers.
- `figures/dataset_structure.svg`: compact comparison of gases, sensors, exposures, windows, budgets, and holdout types.

### IV. Results and Discussion

#### A. Self-supervised training behavior

- Plot all available 60-epoch pretraining-loss histories for both datasets.
- Discuss convergence and late-epoch behavior without treating training loss as validation loss.
- Explicitly state that supervised epoch-level training/validation loss was not persisted by the current scripts; therefore no such curve can honestly be shown from existing artifacts.
- Figure: `figures/pretraining_loss.svg`.

#### B. Label-efficiency results

- Report MAE across all budgets for every neural policy and gas.
- Emphasize transfer-vs-scratch changes and uncertainty across three repeats.
- Figures: `figures/nh3_h2_label_efficiency.svg` and `figures/co_ethylene_label_efficiency.svg`, with error bars where standard deviations exist.

#### C. Full-budget accuracy and tail error

- Present MAE, RMSE, \(R^2\), and computable 90th-percentile absolute error for scratch, frozen, fine-tuned, and relevant physics baselines.
- Separate targets because ppm scales differ substantially.
- Include mean +/- standard deviation across repeats; make clear when percentile values are pooled or per-run summaries.
- Figure: `figures/full_budget_metrics.svg`.

#### D. Comparison with traditional methods

- NH3/H2: compare best transfer with physics + Extra Trees and matched physics + XGBoost at identical budgets.
- CO/ethylene: compare best transfer with matched physics + XGBoost at identical budgets.
- Discuss where tree baselines remain competitive (notably CO near 20/full budget) and where transfer is strongest (low-label regimes and ethylene/H2 patterns).
- Figure: `figures/baseline_comparison.svg`.

#### E. Fine-tuning analysis

- Compare frozen and fine-tuned transfer at every budget/target.
- Discuss the bias-variance interpretation: freezing may protect representations under scarce labels, whereas cautious fine-tuning can help with sufficient adaptation coverage.
- Figure: `figures/freeze_vs_finetune.svg`.

#### F. Ablation study

- Search all existing sensor-aware and supporting experiment artifacts for executable, protocol-compatible ablations.
- Include only ablations sharing comparable splits and evaluation units. Candidate factors: pretraining versus scratch; frozen versus fine-tuned; sensor-aware representation variants; masking/objective variants if recorded.
- Treat scratch/frozen/fine-tuned as controlled policy ablations even if no additional architectural ablation is compatible.
- Clearly separate incompatible exploratory results in an appendix or omit them.
- Figure: `figures/ablation.svg` if sufficient compatible results exist.

#### G. Prediction behavior

- Use saved held-out predictions to produce measured-versus-predicted and/or absolute-error distribution views for representative full-budget runs when model/run identifiers are sufficient.
- Figures: `figures/prediction_scatter.svg` and `figures/error_distribution.svg` if traceable.

#### H. Discussion, limitations, and threats to validity

- Interpret label efficiency, sensor-identity inductive bias, and gas/system consistency.
- Discuss target-dependent behavior and why transfer does not dominate every classical baseline comparison.
- Limitations: one held-out NH3/H2 session, chronological proxy rather than documented CO/ethylene sessions, only three repeats, no saved supervised validation histories, no uncertainty calibration, and private-data reproducibility constraints.
- Avoid causal claims that are not isolated by an architectural ablation.
- State future work: leave-one-session-out evaluation, rolling chronological evaluation, missing-sensor robustness, uncertainty/conformal prediction, broader devices, and persistent train/validation histories.

### V. Conclusion

- Concisely answer the research question using the strongest supported numerical results.
- Restate applicability boundaries: validated within two sensor systems and gas pairs using same-system unlabeled pretraining, not universal cross-device transfer.

### References

- Use IEEE numbered citation style.
- Cite foundational Transformer, masked modeling/self-supervision, XGBoost, Extra Trees, and electronic-nose literature only when bibliographic details can be verified.
- The public CO/ethylene dataset citation must be verified from a primary dataset or original-paper source before inclusion. If internet/source verification is not performed, leave a clearly labeled citation placeholder rather than invent metadata.

### Appendix / reproducibility statement

- Map claims and tables to source JSON/CSV files.
- State software/configuration details from the repository.
- Document unavailable artifacts and exactly which requested analyses could not be reproduced.

## 3. Planned tables

1. Dataset characteristics and split protocol.
2. Sensor-aware architecture and optimization settings.
3. Full-budget metrics (MAE, RMSE, \(R^2\), and 90th-percentile absolute error where derivable).
4. Label-budget results with mean +/- standard deviation.
5. Matched traditional-baseline comparison.
6. Ablation/freeze-fine-tune comparison.
7. Threats to validity and mitigation.

## 4. Planned vector figures

All figures will be standalone SVG with readable fonts, accessible colors, consistent gas/model encodings, explicit units, and captions in the paper.

1. `method_pipeline.svg` -- full proposed method and validation flow.
2. `dataset_splits.svg` -- leakage-controlled session/block allocation.
3. `dataset_structure.svg` -- two-dataset structural comparison.
4. `pretraining_loss.svg` -- complete saved pretraining histories.
5. `nh3_h2_label_efficiency.svg` -- held-out MAE versus labeled-pair budget.
6. `co_ethylene_label_efficiency.svg` -- future-block MAE versus labeled-pair budget.
7. `baseline_comparison.svg` -- transfer versus matched tree baselines.
8. `freeze_vs_finetune.svg` -- adaptation-policy comparison.
9. `full_budget_metrics.svg` -- normalized or faceted full-budget summary.
10. `ablation.svg` -- only if compatible ablation data are available.
11. `prediction_scatter.svg` and `error_distribution.svg` -- only if prediction CSV schemas allow unambiguous reconstruction.

## 5. Evidence and quality-control procedure

1. Inventory report, code, JSON, CSV, and dataset metadata artifacts.
2. Extract metrics programmatically; never transcribe large result tables manually when a source JSON exists.
3. Recompute MAE, RMSE, \(R^2\), and 90th-percentile absolute error from predictions where possible and reconcile them with JSON summaries.
4. Verify split counts, budgets, model dimensions, and hyperparameters against executable code.
5. Generate every plot as SVG and add it to the manifest with source paths.
6. Check that every numeric claim in the paper appears in a source table or figure-generation input.
7. Check Markdown links and SVG XML validity.
8. Review IEEE-like organization, equation notation, figure/table numbering, reference numbering, limitations, and terminology consistency.
9. Clearly label missing evidence, non-comparable experiments, and proposed future validation.

## 6. Completion criteria

The report is complete when it contains all requested major sections, mathematical formulation, a full-method diagram, dataset structure and usage for both public and private data, leakage-controlled validation, MAE/RMSE/90th-percentile error where derivable, method comparisons, compatible ablations, training-loss evidence, fine-tuning analysis, vector-only figures, source traceability, and an explicit limitations discussion. No placeholder result value or unsupported performance claim may remain.

## 7. Further Actions and Research Roadmap

The current report documents the experiments that can be supported by saved artifacts. The following work should be performed next. Items are ordered by priority and distinguish submission-critical evidence from broader extensions.

### Execution status (completed 2026-07-29)

The eight-step immediate execution sequence at the end of this roadmap has now been completed:

1. Both training implementations persist epoch-level supervised training and adaptation-validation histories, selected epochs, and validation-selected checkpoints.
2. Five component variants were implemented: full model, no sensor identities, no attention, no complete-sensor masking, and no temporal-span masking.
3. A two-dataset smoke suite verified mask variants, leakage boundaries, schemas, histories, prediction output, and conformal fields.
4. Full 60-epoch pretraining and 120-epoch supervised ablations were run at the 5-pair and full budgets with three repeats on both datasets (60 run summaries total).
5. Six leave-one-session-out NH3/H2 folds were run at all five budgets, with scratch and transfer over three repeats (180 run summaries).
6. The public CO/ethylene source was confirmed to be a continuous acquisition without defensible session IDs; three rolling chronological folds over seven contiguous blocks were run instead (72 run summaries).
7. Paired exposure-level bootstrap 95% intervals and adaptation-only split-conformal 90% intervals were computed. The observed conformal undercoverage is reported rather than hidden.
8. The report and 13 SVG figures were regenerated. Every 2×2 figure uses enlarged vertical subplot spacing, and visual inspection confirmed that upper x-axis text does not overlap lower panels.

Completed evidence is stored under `../results/advanced_validation/`. Environment and source checksums are in `reproducibility_manifest.json`. The remaining Priority 2–4 items below require new physical-device data, deployment hardware, or broader research scope and are not implied to have been completed by the current datasets.

### Priority 1 — Required before a strong paper submission

#### 1. Run component-level architectural ablations

The present scratch/frozen/fine-tuned comparison establishes a pretraining and adaptation-policy effect, but it does not isolate the contribution of the sensor-aware components. Add controlled runs using exactly the existing splits, seeds, budgets, training epochs, and test units:

1. Full proposed model.
2. Without learned sensor-identity embeddings.
3. Without the cross-sensor Transformer, using independent or pooled sensor tokens.
4. Without complete-sensor masking, retaining temporal-span masking.
5. Without temporal-span masking, retaining complete-sensor masking.
6. No masked pretraining (existing scratch control).
7. Optional shared-CNN versus sensor-specific temporal encoders.

Required outputs:

- `results/<dataset>/ablation_results.json` containing per-seed MAE, RMSE, R2, and predictions;
- `results/<dataset>/ablation_predictions.csv`;
- persisted training histories;
- an updated vector `figures/ablation.svg` and paper ablation table.

The principal comparison should use a representative low-label budget and the full budget on both datasets. If compute permits, run every existing budget.

#### 2. Persist supervised training and validation histories

Modify both transfer scripts so every repeat, budget, and policy saves:

- epoch-level training loss;
- validation loss on an adaptation-only validation subset;
- best epoch and stopping criterion;
- learning rates for encoder and head;
- selected checkpoint identifier;
- training duration and random seed.

The validation subset must come only from the adaptation partition, grouped by raw exposure or concentration pair. The untouched test partition must not be used for early stopping or checkpoint selection. After rerunning, replace the current limitation statement with genuine training/validation curves in vector format.

#### 3. Strengthen session-level validation

For private NH3/H2, run six leave-one-session-out evaluations. In each fold:

- hold out one session for testing;
- use a different session for labeled adaptation;
- use the remaining four sessions for unlabeled pretraining;
- fit scaling only on the pretraining sessions;
- retain the same label budgets and seeded coverage selection.

Report macro-average and between-session standard deviation, alongside per-session results. This is more persuasive than testing only session 6 and reveals whether gains depend on a favorable session choice.

For CO/ethylene, first attempt to recover acquisition metadata such as experiment day, restart, chamber-cleaning, or sensor-reset boundaries. If genuine sessions cannot be reconstructed, use rolling chronological folds rather than a single fixed block split. Each fold must preserve pretrain-before-adapt-before-test order.

#### 4. Add uncertainty and statistical comparisons

Three seeds sharing one test partition do not provide independent dataset-level replication. For every matched model comparison:

- compute paired exposure-level error differences;
- report bootstrap 95% confidence intervals for MAE improvement;
- use session/fold-level estimates when the expanded validation is available;
- report median absolute error and 90th/95th-percentile absolute error;
- avoid treating optimization seeds as independent measurement sessions.

Add prediction intervals using deep ensembles or conformal calibration fitted exclusively within the adaptation data. Report empirical coverage and interval width per gas.

#### 5. Reconcile and freeze the reproducibility package

Create one canonical experiment entry point and configuration file for each dataset. The package should record:

- input file checksum and dataset version;
- preprocessing and label-correction version;
- exact raw-exposure identifiers in each split;
- environment/package versions;
- model parameter count and checkpoint checksum;
- seed, budget, selected concentration pairs, and run duration;
- commands required to regenerate every result table and SVG.

Add automated checks that recompute MAE, RMSE, R2, and quantiles from prediction CSVs and compare them with JSON summaries within a numeric tolerance.

### Priority 2 — Important robustness and deployment evidence

#### 6. Evaluate sensor failure and missing-channel robustness

At test time, simulate:

- one missing sensor;
- multiple missing sensors;
- additive noise and gain shifts;
- stuck-at-zero or saturated sensors;
- sensor-specific drift.

Compare the proposed complete-sensor masking against models trained without it. This experiment is especially important because missing-sensor reconstruction is a central motivation for the self-supervised objective.

#### 7. Test calibration efficiency under operational constraints

Compare farthest-point sampling with:

- random pair selection;
- grid/stratified coverage;
- uncertainty-based active learning;
- diversity plus uncertainty selection;
- constrained selection that limits the number or concentration of calibration gases.

Report the concentration-preparation cost required to reach a target MAE, not only MAE at a fixed number of pairs.

#### 8. Evaluate transfer across physical devices

The current evidence uses same-system pretraining. To support a stronger transfer claim, collect or obtain data from another physical e-nose unit with compatible sensors. Evaluate:

1. same-device pretraining and adaptation;
2. source-device pretraining followed by target-device adaptation;
3. source plus unlabeled target pretraining;
4. sensor-ID alignment or permutation handling when channel layouts differ.

Keep a completely untouched target-device session for final testing. Until this experiment is complete, retain the paper’s bounded “same-system transfer” wording.

#### 9. Measure deployment cost

Record model size, parameter count, peak memory, preprocessing cost, and per-exposure inference latency on the intended edge/desktop hardware. Compare these with Extra Trees and XGBoost. Establish whether the accuracy improvement justifies operational complexity.

### Priority 3 — Method extensions

#### 10. Compare alternative self-supervised objectives

Under identical encoders and splits, compare masked reconstruction with:

- contrastive learning between windows from the same exposure;
- future-response prediction from early response segments;
- sensor-dropout consistency;
- denoising with realistic noise and drift;
- multi-resolution reconstruction;
- combinations of reconstruction and contrastive objectives.

Hyperparameter selection must use only pretraining/adaptation validation data, never the final test set.

#### 11. Optimize the unfreezing schedule

Evaluate head-only training, Transformer-only unfreezing, upper temporal-layer unfreezing, full fine-tuning, discriminative learning rates, gradual unfreezing, and regularization toward pretrained weights. Use adaptation-only validation to select the policy automatically rather than choosing the better test result per target after evaluation.

This point is important: the current “best transfer” curves are retrospective envelopes over frozen and fine-tuned test results. A deployable method needs a policy selected without consulting the test set.

#### 12. Expand gases, concentration regimes, and response windows

Validate additional gas pairs, pure-versus-mixed exposures, low-concentration regimes, and longer response/recovery windows. Analyze error by concentration range and mixture composition to identify where the model fails despite acceptable aggregate MAE.

### Priority 4 — Manuscript completion and release

#### 13. Update the report after new experiments

After Priorities 1–3 are run:

1. regenerate all numerical tables from machine-readable summaries;
2. add the true architectural ablation table and SVG;
3. add supervised training/validation curves;
4. replace the single-session results with multi-session/fold estimates;
5. add statistical confidence intervals and uncertainty coverage;
6. revise the abstract and conclusion using only the final locked protocol;
7. update the limitations so resolved issues are removed and remaining ones remain explicit.

#### 14. Prepare an IEEE submission package

- Convert the Markdown manuscript to the required IEEE LaTeX template.
- Replace author and affiliation placeholders.
- Confirm title, abstract length, index terms, figure sizing, and reference format against the selected venue.
- Export or convert SVG figures to venue-compatible vector PDF/EPS when required; keep SVG as the editable source.
- Obtain permission and an availability statement for the private NH3/H2 dataset.
- Add ethics, funding, conflict-of-interest, and data/code availability statements as required.
- Perform a final independent numerical audit before submission.

### Recommended immediate execution order

The next concrete sequence should be:

1. Update experiment scripts to save supervised train/validation histories and checkpoints.
2. Implement the five essential component ablations: full model, no sensor IDs, no attention, no sensor masking, and no temporal masking.
3. Run a small smoke test to validate result schemas and leakage controls.
4. Run the full three-seed ablation matrix on both datasets at one low-label and one full-label budget.
5. Implement and run six-fold NH3/H2 session validation.
6. Recover CO/ethylene session metadata or run rolling chronological folds.
7. Add paired bootstrap intervals and uncertainty calibration.
8. Regenerate the report and figures from the locked final results.

Priorities 1–5 are the minimum recommended work before presenting the current study as a strong research-paper submission. Priorities 6–12 increase practical and scientific scope; Priorities 13–14 prepare the final publication artifact.
