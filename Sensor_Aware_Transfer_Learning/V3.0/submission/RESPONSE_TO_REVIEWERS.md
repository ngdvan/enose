# Response to reviewers — Revision 3.0

We thank the reviewer for the detailed assessment. This revision clarifies the acquisition limitations, makes label-budget comparisons explicit, narrows the title and full-budget claims, and adds uncertainty and compute evidence. Existing predictive results are retained; additional statistical analyses and representative timing runs are identified separately. Responses below address Comments to Author-250926 and the additional title/abstract explanation supplied by the author. Locations use section and table identifiers to remain stable across document renderers.

## R1. Acquisition days and evaluation partitions

**Comment summary:** Clarify whether the six partitions are the six measurement days; rerun leave-one-day-out if day labels permit, or state directly why they do not.

**Response:** Acquisition took place over six days, but the six evaluation partitions were constructed from consecutive Combination identifiers and were not intended as day splits. Day-by-day mixture details were not logged, so we cannot reliably map exposures to days or construct a defensible leave-one-day-out evaluation. We have stated this directly and restricted the interpretation to held-out identifier partitions within the acquired dataset. Training and test partitions may share days; neither overlap nor independence can be established from these records. Existing exposure-level separation checks are retained, and numerical results are unchanged. Temperature and humidity were also neither controlled nor measured, as now disclosed under R4. We do not claim that the identifier folds test between-day or environmental robustness.

**Location:** Abstract; Sections IV-A, IV-D and VI; supplementary acquisition protocol and “Acquisition independence and environmental limitations.”

## R2. Full-budget competing baselines

**Comment summary:** State that the model is not best on any target at full budget and explain the large CO gap to PLSR.

**Response:** The abstract and conclusion now explicitly state that the proposed model is not the best full-budget baseline on any of the four targets. Section V-E reports all four comparisons: generic SSL leads on NH3 (16.13 versus 17.36 ppm), SVR on H2 (31.37 versus 31.60), Extra Trees on ethylene (1.398 versus 1.627), and PLSR on CO (25.57 versus 47.45). Proposed CO MAE is 1.86 times PLSR MAE. We suggest that the lower-complexity latent linear model may suit this small calibration set and response representation, identifying this as a hypothesis rather than an established mechanism. Mean rankings and overlapping SDs are not treated as equivalence tests.

**Location:** Abstract; Section V-E/Table IV; Section VI.

## R3. Label efficiency in labels

**Comment summary:** Show the calibration-pair counts required for approximately comparable error, rather than only percentage MAE reductions.

**Response:** New Table IIa compares fine-tuning at 10 labeled pairs against scratch at 20, using the existing farthest-point fixed split and ten seeds. MAEs are NH3 38.92 versus 36.84 ppm, H2 81.88 versus 70.73, CO 80.99 versus 89.30, and ethylene 2.418 versus 2.465, with SDs included. Thus NH3 and ethylene are approximately comparable, CO has lower mean error, and H2 does not match the 20-pair scratch mean. Pair counts include fitting and validation labels. We explicitly distinguish pairs, exposure records and augmented windows and do not claim formal equivalence or universal 50% label savings.

**Location:** Abstract; Section V-C/Table IIa; Section VI; evidence/label_efficiency.csv.

## R4. Humidity and temperature

**Comment summary:** State whether temperature and humidity were controlled or recorded and discuss environmental confounding.

**Response:** The acquisition team confirms that temperature and relative humidity were neither controlled nor measured/recorded. We now state this explicitly in the main text and supplement. Their variation and influence cannot be quantified retrospectively, and environmental confounding cannot be excluded. Future experiments will include environmental measurements; exposure-linked day/session logs are also needed for day-held-out evaluation. These are future improvements, not new evidence for the present dataset.

**Location:** Sections IV-D and VI; supplementary acquisition protocol and environmental limitations.

## R5. Five-pair NH3 failure

**Comment summary:** Discuss the negligible five-pair NH3 benefit and the quantitative usefulness of an approximately 86-ppm error.

**Response:** Section V-C now states that 86.39 ± 36.11 to 86.02 ± 34.16 ppm is essentially no observed benefit at five pairs. Approximately 86 ppm is 17.2% of the 0–500 ppm range and does not demonstrate useful precise quantitative calibration. Sparse calibration coverage and training variability are discussed as possible contributors, without claiming an identified mechanism. We connect this finding to the weak NH3 primary interval and component evidence.

**Location:** Section V-C; Section VI.

## R6. H2 window dependence

**Comment summary:** Connect the headline H2 gain to the predefined early window and the middle/full-window sensitivity results.

**Response:** The abstract and conclusion now identify the early-window condition. We distinguish the primary multi-fold H2 reduction of 21.5% from the fixed-split early-window reduction of 23.3% implied by Table VI (41.20 to 31.60 ppm). The middle window reverses the gain (33.99 to 35.60 ppm, −4.7%), and full-cycle resampling gives 6.8% (38.36 to 35.75). The code audit established that “full” spans the complete exposure-plus-recovery record, so we renamed it “full-cycle” and supplied exact definitions. No test-selected window change was made.

**Location:** Abstract; Sections IV-D, V-F/Table VI and VI; supplementary timing/window definitions.

## R7. Calibration design and budget dependence

**Comment summary:** Identify Table II’s farthest-point design and discuss the random-design advantage at 40 pairs.

**Response:** Table II and the new Table IIa name the farthest-point calibration-pair design. Section V-D now describes effects as both target- and budget-dependent. The quoted 40-pair differences of −4.46 ppm for NH3 and −8.32 ppm for H2 belong to scratch training in Table S3. We also report the corresponding fine-tuned differences, −3.37 and −4.89 ppm. All four exploratory intervals exclude zero and negative values favor random design. Known candidate concentrations remain required; no active acquisition of unknown labels is claimed.

**Location:** Tables II and IIa; Section V-D; Supplementary Table S3.

## R8. Multiplicity and few-fold uncertainty

**Comment summary:** Acknowledge the unadjusted four-target intervals, weak NH3 evidence, and indicative CO/ethylene intervals based on three folds.

**Response:** Table I explicitly labels the original intervals as unadjusted. We added a four-comparison Bonferroni sensitivity using 98.75% marginal percentile intervals from 200,000 crossed seed/fold resamples. Scratch-minus-transfer intervals are NH3 [−0.60, 9.46], H2 [2.08, 21.54], CO [8.63, 41.71], and ethylene [0.167, 1.249] ppm. NH3 includes zero after adjustment and is identified as the weakest case. A second random-number seed gives the same zero-inclusion conclusions, with endpoint differences below 0.15 ppm. CO/ethylene intervals are explicitly indicative with only three folds. The analysis remains conditional on observed exposures and does not establish independent acquisition-day inference.

**Location:** Section IV-E; Section V-B/Table I; Section VI; Supplementary Table S9; evidence/multiplicity_sensitivity.csv.

## R9. Fold-4 negative transfer

**Comment summary:** Acknowledge the fold-4 reversals and provide any supported explanation.

**Response:** We now explicitly report NH3 increasing from 16.22 to 18.83 ppm and H2 from 25.70 to 26.36 ppm in identifier fold 4. The text explains that aggregate gains do not imply benefit in every partition. Available records do not establish a day-specific or environmental cause; we avoid assigning a causal explanation. The adverse fold remains in all aggregates and in Table S1.

**Location:** Section V-B; Supplementary Table S1.

## R10. Sampling interval and physical window duration

**Comment summary:** Use the nominal interval and aggregate counts to describe the early window physically.

**Response:** The acquisition team confirms a configured 2.0-s interval, the first sample at gas-delivery onset, and complete 180-s exposure plus 700-s recovery records. We replaced the blanket claim that timing cannot be interpreted. The main text describes approximately 128 s nominally or 131 s from aggregate counts, about 71–73% of the 180-s exposure. The supplement shows 162,404/378 ≈ 429.64 observations per sequence and 880/429.64 ≈ 2.048 s per observation. It distinguishes this approximate consistency calculation from timestamp verification and notes that 64 timestamps span 63 intervals (126 s at nominal cadence). Exact window indices and full-cycle recovery inclusion are now provided.

**Location:** Section IV-D; supplementary acquisition protocol and physical timing/window definitions.

## S1. Mask notation and undefined indices

**Comment summary:** Resolve the Z collision and define span start a_k and batch index b.

**Response:** We retain Z for the sensor-token matrix and use B for the mask-participation indicator in Eqs. (11) and (13). Section III-E defines b, t, s and k, and specifies the uniform integer span start from 0 through T − w_k, sampled separately for each example with its example index suppressed.

**Location:** Section III-E; Eqs. (11)–(13).

## S2. Visible-loss denominator

**Comment summary:** Guard the second denominator in Eq. (14).

**Response:** Both denominators are now guarded. The V3.0 raw-response implementation adds clamp_min(1) to the visible denominator. Under the reported mask, three spans cover at most 48 of 64 positions and at most three entire channels are hidden, so visible entries always remain on the other 13 or 17 channels. The added guard therefore does not change the reported protocol’s loss or require replacement of the historical results. We retain the original results and document the defensive correction.

**Location:** Eq. (14); Section III-E; supplementary loss-guard note; code/same_device_session_transfer.py.

## S3. Supplementary-reference placeholder

**Comment summary:** Remove the literal placeholder on page 4.

**Response:** The placeholder is replaced with a direct reference to Supplementary “NH3/H2 dataset and acquisition details.” Its acquisition facts now agree with the main text.

**Location:** Section IV-D.

## S4. Author voice and grammar

**Comment summary:** Replace awkward self-reference as “the authors” and correct “avoids need for.”

**Response:** We use first-person author voice in the manuscript and supplement, and correct the phrase to “avoids the need for.” References to other researchers and author biographies are retained appropriately.

**Location:** Throughout; Section III-E.

## S5. Title and result-led abstract

**Comment summary:** Shorten the disclaimer-dominated abstract and align the “Sensor-Aware” title with mixed component evidence; the author requires fewer than 250 words.

**Response:** The title is now “Self-Supervised Transfer Learning for Label-Efficient Multigas Electronic Nose Calibration.” The abstract is 230 whitespace-delimited words, presents the approach and primary gains against scratch in connected prose, and gives the protocol and a concrete pair-count comparison. It retains concise full-budget and day-independence scope statements, while detailed statistical, acquisition and cost qualifications remain in the methods/discussion. Sensor identity and attention remain precise architectural descriptions, without a title-level implication of uniformly demonstrated benefit.

**Location:** Title; abstract; Sections V-F and VI; ABSTRACT.md.

## S6. CO-specific ablation uncertainty

**Comment summary:** Discuss the large CO ablation variability and possible null effects.

**Response:** We added a CO-specific paragraph and paired-seed sensitivity table. Removing attention gives 10.27 ± 12.18 ppm, with exploratory unadjusted 95% bootstrap interval [2.68, 16.94]; removing temporal masking gives 7.93 ± 14.86 ppm, interval [−0.33, 17.00]. The latter is compatible with no effect. The attention interval is positive in this conditional analysis, so calling it a statistical null solely because the SD exceeds the mean would be inaccurate. We emphasize the large variability of both estimates and avoid claiming a robust universal component advantage. These additional intervals are explicitly exploratory.

**Location:** Section V-F; Supplementary Table S10; evidence/co_ablation_sensitivity.csv.

## S7. Data and code availability

**Comment summary:** Move the repository link from the biographies into a data and code availability statement.

**Response:** A dedicated Data and Code Availability statement now precedes the references and contains the existing repository link and dataset identifiers. The redundant link after the biographies is removed. Revision evidence and scripts accompany the package; the statement explicitly identifies absent exposure-to-day logs and environmental measurements.

**Location:** Data and Code Availability statement.

## S8. Pretraining compute cost

**Comment summary:** Report pretraining compute cost so readers can weigh labels saved against compute.

**Response:** We measured representative seed-42 fixed-split pretraining reruns on one NVIDIA GeForce RTX 3060: 38.8 s for NH3/H2 (1,260 windows) and 19.9 s for CO/ethylene (735 windows), each for 60 epochs with batch size 64. Timings include initialization and optimization, exclude loading/scaling/checkpoint writes, and do not replace historical performance outputs. Hardware/software, measurement scope and hashes are supplied. These are per-model measurements, not the historical ten-seed/multi-fold campaign cost. We explain checkpoint reuse across calibration budgets and do not claim unmeasured monetary savings.

**Location:** Section IV-D; supplementary representative compute section; evidence/compute_measurement.json.
