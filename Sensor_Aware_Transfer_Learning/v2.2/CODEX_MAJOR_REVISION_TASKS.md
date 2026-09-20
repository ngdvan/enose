# Codex Task Plan — IEEE Sensors Major Revision

**Manuscript:** *Sensor-Aware Self-Supervised Transfer Learning for Label-Efficient Multigas Electronic Nose Calibration*  
**Basis:** reviewer comments in `Comments to the Author.pdf` and current manuscript `Sensor-Aware Self-Supervised Transfer Learning IEEE_V2.2.pdf`

## Goal

Implement the experiments, analysis, code cleanup, and manuscript changes needed to answer the reviewer comments. Do not overwrite old experiment outputs. Create versioned revision artifacts so every new table and figure can be traced to source results.

## Revision rules

- Claim **reduced labeled-calibration requirements**, not reduced gas-generation cost, unless genuinely unlabeled exposures are added.
- Never select frozen vs. fine-tuned transfer from test MAE.
- Treat multi-fold validation as the main generalization evidence.
- Treat Sensor_Drift partition 10 conservatively; do not call a small mean difference a meaningful gain unless uncertainty supports it.
- Add direct controls for generic SSL, classical regression, constant prediction, and random calibration-pair design.
- Preserve the distinction between same-system transfer and cross-device transfer.

---

# 0. Freeze the Current State

- [ ] Create branch/tag `major_revision_start`.
- [ ] Save current commit hash and environment.
- [ ] Export Python/package versions.
- [ ] Save current configs and current V2.2 result CSVs.

Create:

```text
revision_artifacts/
  environment/
    current_commit.txt
    requirements_major_revision.txt
    environment_summary.md
```

**Done when:** current V2.2 results can be reproduced without touching the new revision outputs.

---

# 1. Fix Adaptation-Policy Selection

## Problem

The reviewer objects to the current `Best policy` reporting because frozen is used for CO while fine-tuning is used elsewhere. A policy cannot be chosen from the test set.

## Tasks

- [ ] Remove any test-based `Best policy` logic from analysis scripts.
- [ ] Use one of these valid strategies:
  - **Preferred:** predefine one primary policy for all targets, e.g. fine-tuning.
  - **Alternative:** select frozen/fine-tuned using only an adaptation-validation split.
- [ ] Continue reporting scratch, frozen, and fine-tuned separately.
- [ ] Recompute all headline gains using only the valid primary/selected policy.
- [ ] Remove `Best policy` from the main table unless selection is adaptation-validation only.

Save:

```text
revision_artifacts/policy_selection/
  all_policy_results.csv
  primary_policy_results.csv
  policy_selection_notes.md
```

**Acceptance:** no test-set metric is used to choose the reported main transfer model.

---

# 2. Increase Main Experiments to At Least 10 Seeds

Use a central list, for example:

```python
SEEDS = [42, 142, 242, 342, 442, 542, 642, 742, 842, 942]
```

## Raw-response experiments

### NH3/H2 budgets

- [ ] 5 pairs
- [ ] 10 pairs
- [ ] 20 pairs
- [ ] 40 pairs
- [ ] 57 pairs

### CO/ethylene budgets

- [ ] 5 pairs
- [ ] 10 pairs
- [ ] 20 pairs
- [ ] 24 pairs

Run for:

- [ ] scratch
- [ ] frozen transfer
- [ ] fine-tuned transfer

## Sensor_Drift

Run partitions 8, 9, 10 for:

- [ ] scratch
- [ ] frozen
- [ ] fine-tuned
- [ ] constant predictor baseline

For every configuration save:

- MAE
- RMSE
- \(R^2\)
- \(Q_{0.9}\)
- seed
- split/fold
- policy

Create:

```text
revision_artifacts/10_seed_runs/
  raw_response_all_runs.csv
  sensor_drift_all_runs.csv
  summary_raw_response.csv
  summary_sensor_drift.csv
```

**Acceptance:** all important tables and plots have uncertainty from at least 10 repeats.

---

# 3. Promote Multi-Fold Validation to the Primary Result

## NH3/H2

- [ ] Keep/rerun six leave-one-partition-out folds.
- [ ] One partition = test.
- [ ] Previous partition = adaptation.
- [ ] Remaining four = unlabeled pretraining.

## Dynamic gas mixture

- [ ] Keep/rerun rolling chronological pretrain-adapt-test folds.

## Report for each gas

- [ ] scratch mean MAE
- [ ] transfer mean MAE
- [ ] paired mean improvement
- [ ] relative improvement
- [ ] 95% paired bootstrap CI
- [ ] across-fold SD
- [ ] number of paired predictions
- [ ] fold-level values

Create:

```text
revision_artifacts/multifold/
  nh3_h2_fold_results.csv
  co_ethylene_fold_results.csv
  paired_bootstrap_summary.csv
  fold_level_summary.csv
```

## Manuscript change

Recommended Results order:

1. SSL reconstruction
2. **Primary multi-fold validation**
3. Fixed-split label-budget analysis
4. Calibration-design control
5. Baseline comparison
6. Ablation
7. Sensor_Drift
8. Uncertainty

**Acceptance:** Abstract and Discussion lead with multi-fold evidence rather than the most favorable single split.

---

# 4. Improve Sensor_Drift Analysis

## 4.1 Constant-predictor baseline

For each gas, predict the mean concentration computed from the adaptation fitting subset only.

- [ ] Per-gas MAE
- [ ] MacroMAE
- [ ] normalized error

Do not use test labels to fit the constant.

## 4.2 Per-gas normalized error

Implement at least:

\[
\mathrm{NMAE}_r = \frac{\mathrm{MAE}_r}{c_{r,\max}-c_{r,\min}}
\]

Also optionally report normalized RMSE.

- [ ] per-gas MAE
- [ ] per-gas NMAE
- [ ] macro-NMAE

## 4.3 Partition 10 statistical check

Current means are close under severe drift.

- [ ] Bootstrap/paired comparison scratch vs. frozen/fine-tuned.
- [ ] Report CI for the difference.
- [ ] If CI includes zero, write **no clear improvement** rather than `2.8% gain`.

## 4.4 Smaller adaptation budgets

Run:

- [ ] 1 label/gas
- [ ] 2 labels/gas
- [ ] 5 labels/gas
- [ ] 10 labels/gas
- [ ] 20 labels/gas

If per-gas mean/std scaling is unstable at tiny budgets, replace it with a predefined safe scaling strategy and document it.

Create:

```text
revision_artifacts/sensor_drift/
  constant_baseline.csv
  per_gas_error.csv
  normalized_error.csv
  partition10_statistics.csv
  label_budget_sensor_drift.csv
```

**Acceptance:** partition 10 is not oversold and Sensor_Drift results are not dominated by ppm scale differences across gases.

---

# 5. Add a Sensor-Agnostic SSL Baseline

## Goal

Test whether the proposed **sensor-aware** SSL design adds value beyond generic time-series SSL.

## Preferred baseline

- [ ] PatchTST with masked pretraining

Alternative if easier in the current codebase:

- [ ] TST
- [ ] TS2Vec

## Fairness requirements

Use the same:

- pretraining data
- adaptation/test split
- label budgets
- target preprocessing
- seed list
- supervised adaptation labels

The generic baseline should **not** use physical sensor-ID embeddings.

At minimum compare at:

- low budget
- medium budget
- full budget

Create:

```text
revision_artifacts/ssl_baselines/
  generic_ssl_results.csv
  proposed_vs_generic_ssl.csv
  generic_ssl_config.md
```

**Acceptance:** paper can answer whether explicit sensor identity/structure helps beyond generic masked SSL.

---

# 6. Add Classical Chemometric Baselines

## PLSR

- [ ] Implement `PLSRegression`.
- [ ] Choose component count using adaptation-only validation/CV.

## SVR

- [ ] Implement RBF SVR, one model per target.
- [ ] Tune \(C\), \(\gamma\), and \(\epsilon\) using adaptation-only validation/CV.

## Existing Extra Trees / XGBoost

- [ ] Explicitly document their input feature representation.
- [ ] State whether the input is flattened raw windows, engineered statistics, pooled features, etc.

Final baseline table should include:

- scratch neural model
- Extra Trees
- XGBoost
- PLSR
- SVR
- generic SSL baseline
- proposed sensor-aware SSL

Create:

```text
revision_artifacts/baselines/
  plsr_results.csv
  svr_results.csv
  tree_baseline_features.md
  baseline_summary.csv
```

---

# 7. Random vs. Farthest-Point Calibration Design

## Terminology fix

Replace `label selection` with:

- `coverage-based calibration-pair design`, or
- `farthest-point calibration design`.

The method uses known concentration coordinates, so it is a design-of-experiments choice rather than generic label acquisition.

## Experiment

At each budget, compare:

| Pair design | Training |
|---|---|
| Random | Scratch |
| Random | Transfer |
| Farthest-point | Scratch |
| Farthest-point | Transfer |

Run random pair selection at least 10 times.

Key budgets:

- [ ] 5
- [ ] 10
- [ ] 20

Add higher/full budgets if practical.

Create:

```text
revision_artifacts/calibration_design/
  random_vs_farthest.csv
  factorial_summary.csv
```

**Acceptance:** low-label improvement can be separated into benefits from SSL and benefits from concentration-space coverage.

---

# 8. State the Same-System / Cross-Device Limitation Clearly

- [ ] Add explicit text that sensor-ID embeddings are tied to the array layout.
- [ ] State that current evidence supports **same-system transfer/recalibration** only.
- [ ] Do not imply cross-device transfer.

## Optional cross-device test

Only run if there are genuinely compatible arrays with meaningful sensor correspondence.

Possible experiment:

- pretrain array A
- reinitialize/remap sensor IDs
- adapt array B
- test array B

If no valid data exist, document this as future work instead of forcing an invalid experiment.

---

# 9. Complete Private NH3/H2 Hardware Characterization

Gather from authoritative experiment records only:

- [ ] sensor manufacturer/model
- [ ] sensing material/technology
- [ ] number/type of each sensor
- [ ] operating/heater temperature
- [ ] acquisition circuit
- [ ] sampling frequency
- [ ] chamber volume
- [ ] gas source
- [ ] flow controller
- [ ] flow rate
- [ ] carrier/baseline gas
- [ ] baseline convention
- [ ] exposure duration
- [ ] purge duration
- [ ] ambient temperature
- [ ] relative humidity
- [ ] whether humidity was controlled
- [ ] reference gas/concentration accuracy

**Never invent unavailable metadata.** If unavailable, state that explicitly as a limitation.

---

# 10. Justify the 64-Sample Window

The reviewer notes that only a small portion of each long exposure is used.

Run a sensitivity study:

- [ ] early 64-sample window
- [ ] middle 64-sample window
- [ ] late 64-sample window
- [ ] full exposure resampled/downsampled to 64 samples, if feasible

Keep training protocol fixed.

Create:

```text
revision_artifacts/window_sensitivity/
  window_definition.md
  window_position_results.csv
  window_position_plot.pdf
```

**Acceptance:** the chosen window has either an empirical or physically justified basis.

---

# 11. Improve Statistical Reporting

## Error bars / uncertainty

Add mean ± SD or 95% CI to:

- [ ] label-budget table
- [ ] ablation table
- [ ] baseline table
- [ ] Sensor_Drift table

## Paired statistics

Use paired bootstrap CI for:

- [ ] scratch vs. transfer
- [ ] generic SSL vs. proposed SSL
- [ ] random vs. farthest-point design

Optional: Wilcoxon signed-rank test when assumptions and sample units are appropriate.

## Add scratch tail error

Report \(Q_{0.9}\) for:

- [ ] scratch
- [ ] frozen
- [ ] fine-tuned

## Model size

Report:

- [ ] total parameters
- [ ] trainable parameters
- [ ] encoder parameters
- [ ] head parameters
- [ ] parameter count relative to effective supervised sample count

Optional:

- FLOPs
- latency
- memory

Create:

```text
revision_artifacts/statistics/
  paired_tests.csv
  q90_all_policies.csv
  model_size.csv
```

---

# 12. Clarify Conformal Prediction Limitation

Add this idea explicitly to the manuscript:

> Standard split-conformal coverage relies on exchangeability between calibration and test residuals. The chronological/session shift in this study violates this assumption. Therefore, the reported intervals are diagnostic rather than guaranteed coverage intervals under deployment shift.

Optional only if time permits:

- weighted conformal
- adaptive conformal
- covariate-shift conformal

The reviewer allows an explicit assumption statement as an alternative to implementing a new conformal method.

---

# 13. Check Sensor_Drift Loss/Target Transformation

Reviewer notes that the model optimizes Huber loss in log-concentration space but is evaluated by linear-space MAE.

Compare:

1. current log target + Huber
2. linear normalized target + Huber
3. linear normalized target + MAE/other robust loss

Also investigate whether estimating per-gas mean/std from only 16 fitting samples is unstable.

Possible safer scaling:

- known physical concentration range
- fixed scale
- robust scale independent of tiny adaptation subset

Create:

```text
revision_artifacts/sensor_drift_loss/
  target_transform_comparison.csv
  scaling_sensitivity.csv
```

---

# 14. Audit Repeated Exposures and Leakage

Determine whether repeated concentration pairs in test are:

- independent physical exposures
- duplicate rows
- augmented windows

Document clearly.

If true, add wording such as:

> Repeated concentration pairs correspond to independently acquired exposures. No raw exposure or augmented window is shared across adaptation and test partitions.

Create:

```text
revision_artifacts/leakage_audit/
  repeated_exposure_audit.csv
  leakage_statement.md
```

---

# 15. Expand the Literature

Increase references from the current small set to roughly 25–35 strong, relevant sources.

Add literature on:

- masked time-series SSL
- PatchTST / TST / TS2Vec
- e-nose drift compensation
- quantitative gas regression
- PLSR / SVR chemometrics
- calibration design / minimal experiments
- uncertainty under distribution shift

Do not add citations only to increase the count.

---

# 16. Rewrite Results Structure

Recommended order:

## V.A Self-Supervised Pretraining

Keep short; reconstruction loss is supporting evidence only.

## V.B Primary Multi-Fold Validation

Main scientific evidence.

## V.C Label-Budget Analysis

Controlled fixed-split analysis of label efficiency.

## V.D Calibration-Design Control

Random vs. farthest-point.

## V.E Baseline Comparison

Include PLSR, SVR, trees, generic SSL, proposed SSL.

## V.F Ablation

Keep compact.

## V.G Long-Term Drift

Include constant baseline, normalized per-gas error, 10-seed results, and conservative partition-10 interpretation.

## V.H Tail Error / Uncertainty

Keep concise.

---

# 17. Rewrite the Abstract Only After Final Reruns

Final Abstract must:

- [ ] say **reduced labeled-calibration requirements**
- [ ] not claim reduced gas-generation cost
- [ ] use a predefined/validation-selected transfer policy
- [ ] emphasize multi-fold evidence
- [ ] avoid implying label-budget improvement is monotonic for every target
- [ ] describe Sensor_Drift partition 10 conservatively
- [ ] state that Sensor_Drift concentration regression is oracle-class conditional
- [ ] avoid cross-device claims

---

# 18. Discussion Changes

## CO weakness

Explicitly acknowledge:

- lower \(R^2\)
- high \(Q_{0.9}\)
- weaker quantitative performance than the other targets

## Sensor-ID variability

Use cautious wording, e.g.:

> The much larger sensor-identity effect for H2 than NH3 suggests that channel identity may carry gas-dependent information. The current experiments cannot separate sensor selectivity from sampling variability, so this result should be interpreted cautiously.

## Drift

State:

- partitions 8–9 show useful transfer
- partition 10 shows no clear benefit if CI crosses zero
- explicit domain alignment is needed for more severe drift

## Scope

Repeat clearly:

- same-system transfer only
- no demonstrated cross-device transfer

---

# 19. Presentation and Language Cleanup

Fix reviewer-noted errors:

- [ ] `overal` → `overall`
- [ ] `trainning` → `training`
- [ ] `comparision` → `comparison`
- [ ] `Multif-fold` → `Multi-fold`
- [ ] `increase MAE significantly` → `decrease MAE` or rewrite

## Tables

- [ ] Remove duplicated summary/full-budget tables.
- [ ] Keep one main table with scratch, frozen, fine-tuned, uncertainty.
- [ ] Remove test-selected `Best policy`.

## Figures

### Fig. 3

- [ ] enlarge axis fonts
- [ ] enlarge legend
- [ ] simplify annotations
- [ ] verify readability at IEEE print size
- [ ] export vector PDF/SVG

### Fig. 2

- [ ] keep; only minor cleanup if needed

## Template

- [ ] confirm proper keywords
- [ ] remove any placeholder such as `SYST`

---

# 20. Create a Point-by-Point Reviewer Response

Create:

```text
revision_artifacts/response/reviewer_response.md
```

Use this pattern for every comment:

```markdown
### Comment X

> Reviewer comment

**Response:**
Thank you for this comment. We agree that ...

**Changes made:**
- ...
- ...

**New result:**
- ...

**Location in manuscript:**
- Section ...
- Table ...
- Figure ...
```

For major comments, always include the new numerical result and manuscript location.

---

# 21. Automated Consistency Check

Create:

```text
scripts/check_paper_consistency.py
```

It should check:

- [ ] Abstract metrics match result CSVs.
- [ ] Table values match result CSVs.
- [ ] Discussion percentages match tables.
- [ ] Correct number of seeds is stated.
- [ ] No obsolete 3-seed headline remains after 10-seed reruns.
- [ ] No obsolete drift numbers remain.
- [ ] No test-selected `best policy` remains.
- [ ] Partition 10 is not called a significant gain without support.
- [ ] Figure captions match current protocols.
- [ ] Every citation exists in References.
- [ ] Every reference is cited.
- [ ] No `TODO`, `SYST`, placeholder values, or old numbering remains.

Expected final output:

```text
PASS: manuscript numbers consistent with final experiment artifacts
```

---

# Minimal Must-Do Set Before Resubmission

If time is limited, prioritize these:

1. [ ] Remove test-based best-policy selection.
2. [ ] Run at least 10 seeds.
3. [ ] Promote multi-fold validation to the primary result.
4. [ ] Add Sensor_Drift constant predictor.
5. [ ] Add normalized per-gas Sensor_Drift errors.
6. [ ] Treat partition 10 as no clear improvement unless statistics support otherwise.
7. [ ] Add one generic sensor-agnostic SSL baseline.
8. [ ] Add PLSR and/or SVR.
9. [ ] Add random vs. farthest-point calibration-design control.
10. [ ] Add private-array hardware/environment details.
11. [ ] Justify/test the 64-sample window.
12. [ ] Add scratch \(Q_{0.9}\) and model parameter counts.
13. [ ] Clarify the conformal exchangeability violation.
14. [ ] Clean wording, duplicated tables, figure readability, and reviewer-noted typos.
15. [ ] Produce a detailed point-by-point reviewer response.

---

# Definition of Done

The revision is ready for author review when:

- model/policy selection does not use test results;
- main experiments have at least 10 seeds;
- multi-fold validation is the primary generalization evidence;
- a generic SSL baseline and classical chemometric baselines are included;
- farthest-point calibration design is compared against random selection;
- Sensor_Drift has constant and normalized-error baselines;
- partition 10 is interpreted conservatively;
- hardware and windowing choices are documented;
- same-system scope and cross-device limitation are explicit;
- manuscript claims exactly match the experiment evidence;
- every reviewer comment has a point-by-point response;
- the automated consistency script passes.
