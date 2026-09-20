# Point-by-point response to reviewers

The authors have completed the revised ten-seed experiment matrix, predefined fine-tuning as the primary policy, promoted multi-fold validation and added the requested controls. In the supplementary information, the authors describe their NH3/H2 sensor array, gas chamber and acquisition protocol, with a system schematic and photographs of the experimental hardware. Yellow highlighting identifies revised or inserted manuscript content, not Word tracked changes. The manuscript is condensed to ten pages by removing repeated background and discussion. All four figures, ten main tables, 30 references and mathematical equations are retained; detailed seed sensitivity and generic-SSL comparisons remain in the supplementary tables.

## Major comment 1

> The premise is not tested. Pretraining reuses controlled exposures with labels withheld, so the labels already exist. The real cost in this field is generating the exposure, not annotating it. Either pretrain on genuinely unlabeled data (ambient, disjoint concentration regime, or a different array) or drop all language implying reduced calibration cost.

**Response:** The authors clarify that the research motivation is the expense of precise concentration control and labeling: mixtures without carefully controlled ppm can provide inexpensive unlabeled response recordings. The intended workflow pretrains on such recordings and reserves precise labels for a small calibration set. The revised Abstract, Introduction, problem formulation and Discussion preserve this motivation while identifying the present controlled-dataset experiments as a retrospective label-withholding test. They support label efficiency, but do not measure cost savings or demonstrate prospective learning from a cheaply acquired unquantified pool. The authors also distinguish the known-coordinate calibration-design control from label-free pretraining and from a total acquisition-cost budget.

**Location:** Abstract; Sections I, III.A, VI

**Status:** Addressed

## Major comment 2

> The "Best policy" column in Table I selects between frozen and fine-tuned transfer on the test partition (frozen for CO, fine-tuned elsewhere), contradicting the statement in Section V.B. All four abstract gains inherit this. Pre-register one policy, or select on the adaptation- only validation split, and recompute the abstract.

**Response:** Fine-tuning is predefined for every target. Scratch, frozen and fine-tuned models share a group-disjoint adaptation holdout; only adaptation validation selects checkpoints. The authors removed the test-selected summary and recomputed the primary abstract: NH3: scratch 31.01 → fine-tuned 26.69 ppm; reduction 13.9%; paired interval [0.38, 8.30] ppm; H2: scratch 49.20 → fine-tuned 38.63 ppm; reduction 21.5%; paired interval [3.57, 18.78] ppm; CO: scratch 89.95 → fine-tuned 65.22 ppm; reduction 27.5%; paired interval [12.85, 37.53] ppm; Ethylene: scratch 2.611 → fine-tuned 1.939 ppm; reduction 25.7%; paired interval [0.247, 1.143] ppm.

**Location:** Abstract; Sections III.F, IV, V.B; Table I

**Status:** Addressed

## Major comment 3

> Three seeds is not enough. NH3 and H2 scratch and transfer distributions overlap at about one standard deviation, no hypothesis tests are given, and Table III has no error bars and is non-monotonic in several places (CO 20 vs 24 pairs, ethylene 5 vs 10 pairs). Use at least 10 seeds with error bars on Tables III and IV.

**Response:** All principal configurations now contain the ten seeds 42, 142, …, 942, including seed-specific pretraining. Budget, baseline, ablation, window and drift tables report SD, and paired comparisons report seed/fold bootstrap intervals. The 1,680 completed jobs retain predictions and identities. Seed accumulation does not show uniform erosion: first three → all ten primary reductions are NH3: 13.3% → 13.9%; H2: 18.4% → 21.5%; CO: 28.5% → 27.5%; Ethylene: 26.1% → 25.7%; however, secondary full-budget fixed-split gains attenuate from 32.4% to 19.6% (NH3), 27.2% to 23.3% (H2), 27.2% to 25.4% (CO), and 31.1% to 24.3% (ethylene). Nonmonotonic budget behavior is retained.

**Location:** Sections IV, V.B–H; Tables I–X; Supplementary Table S2 and Fig. S1

**Status:** Addressed

## Major comment 4

> The multi-fold results in Section V.D are the most credible in the paper and are currently subordinated. They show smaller gains (16.4 percent for NH3, 14.5 percent for ethylene) and roughly double the absolute error, with an across-fold standard deviation of 17.81 ppm. The paired bootstrap intervals all exclude zero and are a defensible result. Promote this analysis to primary and demote the single-split tables.

**Response:** The primary quantitative result now leads with six NH3/H2 held-partition folds and three chronological CO/ethylene rolling folds. The authors replaced the historical results and its repeated-prediction bootstrap with equally weighted crossed seed-and-fold resampling. NH3: scratch 31.01 → fine-tuned 26.69 ppm; reduction 13.9%; paired interval [0.38, 8.30] ppm; H2: scratch 49.20 → fine-tuned 38.63 ppm; reduction 21.5%; paired interval [3.57, 18.78] ppm; CO: scratch 89.95 → fine-tuned 65.22 ppm; reduction 27.5%; paired interval [12.85, 37.53] ppm; Ethylene: scratch 2.611 → fine-tuned 1.939 ppm; reduction 25.7%; paired interval [0.247, 1.143] ppm. Intervals are conditional on observed exposures, and overlapping training partitions limit population inference.

**Location:** Abstract; Section V.B; Table I; Supplementary Table S1

**Status:** Addressed

## Major comment 5

> Drift partition 10 (146.95 plus or minus 8.71 against 142.78 plus or minus 1.13) is a null, not a 2.8 percent gain, and should be stated as such. This section also needs a constant- predictor control emitting the per-gas mean from the adaptation set.

**Response:** The authors added a per-gas constant fitted only to the adaptation fitting subset, with matched subsets across policies, all ten seeds, per-gas normalized errors and paired partition-specific intervals. Partition-10 scratch minus fine-tuned macro-MAE is -0.71 ppm, with paired seed interval [-8.40, 6.91] ppm. The interpretation follows this revised interval; the former small-gain claim is removed. The new protocol should not be conflated with the old unmatched-holdout three-repeat estimate.

**Location:** Section V.G; Tables VII–IX; Supplementary Tables S5–S7

**Status:** Addressed

## Major comment 6

> The sensor-aware claim needs a sensor-agnostic masked self-supervised baseline (for example TST, TS2Vec, or PatchTST). Internal ablations do not establish it. The feature representation given to Extra Trees and XGBoost is never stated, and a PLSR or SVR chemometric baseline is missing.

**Response:** The authors added a compact PatchTST-style masked, shared channel-independent Transformer without physical sensor-ID embeddings, evaluated at every fixed-split budget. Its departures from the forecasting configuration and differing capacity are stated. PLSR and RBF SVR use adaptation-only tuning; trees use flattened scaled windows (1,280/1,024 features). Full-budget paired generic comparisons are NH3: generic minus proposed -1.23 ppm [-2.46, -0.16]; H2: generic minus proposed 3.58 ppm [1.53, 5.40]; CO: generic minus proposed 5.08 ppm [-2.31, 12.72]; Ethylene: generic minus proposed -0.189 ppm [-0.336, -0.034]. These mixed results explicitly limit the superiority claim.

**Location:** Sections II, IV, V.E; Table IV; Supplementary Tables S4, S4a, S8

**Status:** Addressed

## Major comment 7

> Equation (16) selects calibration pairs using the concentration labels it is meant to economize, so it is a design-of-experiments choice, not label selection. A random-selection control is also absent.

**Response:** Equation (16) is now described as coverage-based calibration-pair design using known concentrations. Random and farthest-point designs are crossed with scratch and fine-tuning at every budget and all ten seeds. Table III shows the five-pair experiment; Supplementary Table S3 reports every paired design contrast and interval. No claim of generic label acquisition remains.

**Location:** Section III.F; Section V.D; Table III; Supplementary Table S3

**Status:** Addressed

## Major comment 8

> Learned per-channel identity embeddings bind the encoder to one array and preclude cross- device transfer. State this limitation, and ideally test pretrain on array A, adapt on array B.

**Response:** The authors explicitly state that learned channel identities depend on array layout. The evidence concerns same-system recalibration. A valid cross-device test needs compatible arrays and documented correspondence; no such matched acquisition is established here, so no cross-device performance is claimed.

**Location:** Sections III.C and VI

**Status:** Addressed by scope limitation; optional cross-device experiment not performed

## Major comment 9

> The private array is not characterized: no sensing material, operating temperature, sampling rate, baseline convention, or humidity and temperature conditions. Humidity in particular cannot be omitted for MOX sensors. Also, only about 68 of roughly 430 samples per exposure are used, with no justification for the window placement, and the 0 to 500 ppm NH3 range does not match the environmental monitoring framing.

**Response:** The authors provide additional details of their NH3/H2 apparatus and acquisition protocol in Supplementary "NH3/H2 dataset and acquisition details". The authors describe the 20-channel MEMS SnO2 array with Pt/Ag modification, electrical supply settings, mass-flow-controlled gas delivery, switching valve, chamber and exhaust. Each programmed condition uses 180 s of exposure followed by 700 s of recovery, with a nominal 2.0-s sampling setting. Figure S2 presents the system schematic and Fig. S3 shows the sensor devices, chamber and mass-flow-controller installation. The existing window-sensitivity analysis remains in Section V.F and Table VI. These additional apparatus and protocol details are supplied in the supplement; the main paper is unchanged.

**Location:** Supplementary "NH3/H2 dataset and acquisition details", Figs. S2-S3; existing Section V.F and Table VI

**Status:** Partly addressed: sensor/chamber descriptions, acquisition protocol and hardware images supplied; complete environmental and calibration characterization is not provided

## Moderate comment 1: CO accuracy

> CO performance is weak and should be acknowledged as such.

**Response:** The authors explicitly report the remaining CO quantitative limitation and include scratch, frozen and fine-tuned R², RMSE and Q0.9. The table retains absolute errors, not just relative gains.

**Location:** Section V.H; Table X

**Status:** Addressed

## Moderate comment 2: Conformal assumption

> The conformal coverage failure needs either a shift-aware variant or an explicit statement of the violated assumption.

**Response:** The authors state that chronological/session shift violates the exchangeability assumption needed for standard split-conformal coverage guarantees. Earlier coverage percentages are not presented as new ten-seed evidence. The authors take the reviewer’s permitted explicit-limitation route; the authors do not claim to have implemented a shift-aware method.

**Location:** Section V.H; references [24], [25]

**Status:** Addressed

## Moderate comment 3: Ablation uncertainty

> Table IV needs error bars.

**Response:** The new Table V reports mean ± SD of within-seed ablation-minus-full-model MAE over ten repeats. All raw variant results remain available, including adverse effects and low-budget runs.

**Location:** Section V.F; Table V; evidence/ablation_paired_differences.csv

**Status:** Addressed

## Moderate comment 4: Sensor-ID variability

> The spread in the sensor identity effect between H2 and NH3 needs explanation or attribution to noise.

**Response:** Sensor-ID effects are gas-dependent and may reflect sampling/optimization variation as well as selectivity. The authors' array uses SnO2 with Pt/Ag modification, but array-level material information does not establish a chemistry-based causal explanation for the ablation differences. The authors therefore retain a cautious interpretation.

**Location:** Sections V.F and VI

**Status:** Addressed

## Moderate comment 5: Normalized drift errors

> MacroMAE in ppm is dominated by high-concentration analytes; report per-gas normalized error.

**Response:** The authors report all six per-gas MAEs/NMAEs and macro-NMAE. The denominator is each gas’s historical partitions-1–6 range, used only for reporting, because some test-partition ranges are zero. Each gas receives equal weight; the original test-range diagnostic is preserved separately.

**Location:** Section IV; Table VIII; Supplementary Table S5 and S5a

**Status:** Addressed

## Moderate comment 6: Drift target and scaling

> The log-target Huber optimum is biased for linear-space MAE and per-gas scaling is estimated from only 16 records.

**Response:** The authors explicitly distinguish the objectives and run historical fitted-log Huber, fixed-log Huber, linear Huber and linear MAE at 20 labels/gas for all neural policies. Smaller budgets use a fixed log scale; one label/gas uses the final checkpoint without a validation split. The authors do not choose the primary transform using test performance.

**Location:** Section IV; Table IX; Supplementary Tables S6–S7

**Status:** Addressed

## Moderate comment 7: Model size

> Please report parameter counts against effective sample size.

**Response:** The main text reports total/encoder/head/trainable counts and parameter-to-distinct-fitting-exposure ratios. The supplement gives low/full budgets and drift. Five windows from one exposure are not counted as five independent exposures.

**Location:** Section V.H; Supplementary Table S8

**Status:** Addressed

## Moderate comment 8: Repeated exposures

> Clarify whether repeated exposures appear in the test partition.

**Response:** The authors repeat the acquisition protocol on separate measurement days and retain exposure identifiers when constructing the evaluation splits. Repeated concentration settings are distinct from duplicated response records. The digital audit checks identifier separation and stored-signal fingerprints; these checks alone do not establish physical independence of the exposures. CO/ethylene checks remain limited to cached windows.

**Location:** Supplementary "NH3/H2 dataset and acquisition details"; evidence/leakage_audit

**Status:** Acquisition protocol described; digital separation verified; physical independence not inferred from identifiers alone

## Moderate comment 9: Scratch tail error

> Add scratch Q0.9 values.

**Response:** Table X reports scratch, frozen and fine-tuned Q0.9 alongside RMSE and R². Job-level raw-response and drift tail errors remain in the evidence CSVs.

**Location:** Section V.H; Table X

**Status:** Addressed

## Moderate comment 10: Competing method

> Either reimplement one competing method or evaluate on a published split.

**Response:** The authors implement the compact PatchTST-style matched SSL control and state the deviations from the official forecasting model, including token width, input patches, head and omitted instance normalization. This is not a reproduction of published forecasting scores, and the gas-regression partitions are not claimed to be an official PatchTST benchmark.

**Location:** Section IV; Section V.E; Supplementary Table S4

**Status:** Addressed

## Moderate comment 11: References

> Seventeen references is thin.

**Response:** Thirteen references on masked/contrastive time-series learning, chemometrics, experimental design, tree models, nonexchangeable uncertainty, sensor-array design, the NH3/H2 dataset, and related image-based mixed-gas estimation extend the bibliography to 30. Each is cited in context; citations do not substitute for the new direct baseline experiment.

**Location:** Sections II and IV; References [18]–[28]

**Status:** Addressed

## Presentation comment 1: Sign error

> Section V.B states “increase MAE significantly” where “decrease” is meant.

**Response:** The authors replaced this sentence with result-grounded paired comparisons. Positive scratch-minus-transfer differences are explicitly defined as reduced MAE.

**Location:** Section V.B; Table I

**Status:** Addressed

## Presentation comment 2: Typos

> Correct “overal”, “trainning”, “comparision”, and “Multif-fold”.

**Response:** The revised text corrects these terms, and a document-wide text check rejects the obsolete tokens.

**Location:** Throughout

**Status:** Addressed

## Presentation comment 3: Keywords

> The Keywords field contains only “SYST”.

**Response:** The supplied editable DOCX already contained substantive Index Terms. The authors retain valid electronic-nose, self-supervised-learning and calibration keywords and verify no SYST placeholder remains.

**Location:** Front matter

**Status:** Addressed

## Presentation comment 4: Duplicate tables

> Tables I and II largely duplicate each other.

**Response:** The test-selected floating summary and duplicated full-budget-only table are removed. New Table I is the primary multi-fold comparison; Table II is the single all-policy budget table.

**Location:** Tables I–II

**Status:** Addressed

## Presentation comment 5: Figure 3

> Fig. 3 labels are unreadable at print size.

**Response:** Figure 3 uses a contrasting orange mean-plus/minus-one-SD band with outlined bounds, a thinner blue mean line and a larger explicit legend. Figure 4 uses larger opaque legend symbols and bold labels for Scratch, Frozen and Fine-tuned, with distinct gray circles, blue squares and orange triangles. Numerical values and uncertainty bounds are unchanged; vector PDF/SVG and high-resolution PNG versions are supplied.

**Location:** Fig. 3; figures/fig3_pretraining.pdf

**Status:** Addressed

## Presentation comment 6: Figure 2

> Fig. 2 is clear and should be kept.

**Response:** The supplied Fig. 2 image is retained unchanged. Its caption now identifies the secondary fixed splits; the newly primary cyclic/rolling folds are specified in the protocol text.

**Location:** Fig. 2; Section IV

**Status:** Addressed
