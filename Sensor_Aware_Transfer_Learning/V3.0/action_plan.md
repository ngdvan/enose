# V3.0 revision action plan

**Execution status:** the local revision is complete. See [REVISION_STATUS.md](REVISION_STATUS.md) for all 18 item dispositions, deliverables, new analyses, validation and remaining scientific limitations. The task checkboxes below retain the planning record; the execution ledger supersedes prospective wording.

## Objective and source baseline

Address all 10 numbered comments and all 8 smaller points in [Comments to Author-250926.pdf](Comments%20to%20Author-250926.pdf), using the supplied V2.2 submission as the baseline:

- [Clean manuscript](Base%20v2.2/IEEE_Full_Revision_Clean.pdf), 9 pages.
- [Highlighted manuscript](Base%20v2.2/IEEE_Full_Revision_Highlighted.pdf), 9 pages; extracted text matches the clean version.
- [Supplementary evidence](Base%20v2.2/SUPPLEMENTARY_EVIDENCE.pdf), 14 pages.
- [Previous response to reviewers](Base%20v2.2/RESPONSE_TO_REVIEWERS.pdf), 6 pages. Use as revision history, not as the response to the new comments.

This document records the agreed revision plan. Execution and completed edits are documented separately in REVISION_STATUS.md. Numbers below are from the supplied PDFs unless explicitly identified as derived. Acquisition facts added under R1/R4 come from the author clarification in this conversation, not an independent log audit. Preserve Base v2.2 as the reference submission. No new physical measurements are requested. Following the author clarification, a reliable leave-one-day-out rerun is not planned because the available mixture records do not support exposure-to-day assignments.

Priority: **P0** resolves protocol validity; **P1** addresses scientific claims and evidence; **P2** completes presentation and reproducibility. Suggested roles are acquisition lead, analysis lead, and manuscript lead; these are responsibilities to assign, not named assignees.

## Execution order

1. Recover editable manuscript/supplement sources, analysis scripts, unrounded predictions, split manifests, acquisition metadata, and training logs corresponding to the supplied PDFs. Verify provenance before reusing older repository artifacts.
2. Incorporate the confirmed six-day acquisition, partitions not designed as day splits, missing day-by-day mixture logs (R1), and absence of temperature/humidity control (R4). Incorporate the confirmed absence of environmental measurements, gas-onset alignment, 180-s exposure plus 700-s recovery, and configured 2.0-s sampling interval (R10). Actual timestamp availability remains unspecified.
3. Retain the identifier-based protocol and explicitly limit its interpretation: it does not establish between-day generalization. Do not infer day labels or promise a leave-one-day-out rerun without reliable exposure-to-day records.
4. Produce label-budget comparisons and statistical sensitivity results (R3, R8), then reconcile all affected tables and claims.
5. Revise interpretation (R2, R5–R9), equations and presentation (S1–S8). Finalize the abstract after results are fixed.
6. Generate clean/highlighted manuscripts, updated supplement, and a new point-by-point response; complete the consistency checks below.

## Numbered reviewer comments

### R1 - Disclose why leave-one-day-out evaluation cannot be reconstructed

**P0 | Manuscript lead + analysis lead | Locations:** Section IV-A, Section IV-D, Table I, Table S1, supplementary acquisition protocol, abstract and conclusion.

**Author clarification:** acquisition took place over six days. The partitions were not intended as day-based splits. Day-by-day mixture details were not logged, so those records do not support reliable assignment of individual exposures to acquisition days. Temperature and humidity were not controlled (also addressed under R4).

**Decision:** use the reviewer's permitted explicit-limitation route. Retain the identifier-based analysis; do not relabel it as leave-one-day-out or infer day membership from consecutive identifiers or equal partition sizes. The planning decision is resolved; manuscript and response edits remain pending.

- [x] Record the author's confirmation of six acquisition days and the missing day-by-day mixture log.
- [ ] Explain that six measurement days do not establish six day-isolated evaluation folds.
- [ ] State directly that a defensible leave-one-day-out split cannot be constructed with the available exposure-to-day information. Revisit this only if reliable contemporaneous records become available.
- [ ] Describe the evaluation as held-out identifier partitions within the acquired dataset. Training and test partitions may share acquisition days; their day/session overlap cannot be determined. Do not claim either verified day independence or proven day overlap.
- [ ] Retain exposure-level separation and digital overlap checks, while explaining that these do not establish session independence. Keep complete exposures together before window extraction and exclude test exposures from preprocessing fits, SSL, calibration design, supervised fitting, and checkpoint selection.
- [ ] Limit NH3/H2 conclusions to the observed dataset and partitioning protocol. Remove implications that these folds demonstrate between-day robustness or resistance to environmental variation. Keep the separate chronological CO/ethylene protocol accurately described.
- [ ] Align the main text, supplement, abstract, conclusion, and reviewer response. Existing numerical results need not change solely because this metadata limitation is clarified.

**Proposed manuscript wording:**

> The NH3/H2 measurements were acquired over six days. The six evaluation partitions were constructed from consecutive Combination identifiers and were not designed to represent individual acquisition days. Day-by-day mixture details were not logged, preventing reliable reconstruction of an exposure-to-day mapping and a defensible leave-one-day-out evaluation. Although exposure identifiers are separated across the evaluation roles, acquisition days may be shared between training and test partitions. These results therefore describe generalization across held-out identifier partitions within the acquired dataset and do not establish between-day generalization. Temperature and humidity were not controlled, so environmental confounding cannot be excluded.

**Proposed reviewer-response wording (use after the corresponding edits):**

> Thank you for highlighting this distinction. Acquisition took place over six days, but the six evaluation partitions were not intended as day-based splits. We did not log the day-by-day mixture details needed to map individual exposures reliably to acquisition days. We therefore cannot construct a defensible leave-one-day-out evaluation from the available records. We have clarified this limitation and restricted our interpretation to held-out identifier partitions; we do not claim day-independent validation. We have also stated that temperature and humidity were not controlled and that environmental confounding cannot be excluded.

**Completion evidence:** consistent disclosure of the author-confirmed acquisition history and missing day mapping, accurate exposure-level split description, appropriately limited claims, and a direct response explaining why day-held-out analysis is unavailable.

### R2 — State the full-budget baseline ranking plainly

**P1 | Manuscript lead | Locations:** abstract, Section V-E, Table IV, conclusion.

- [ ] State that the proposed model has the lowest mean MAE on **none of the four targets in the secondary full-budget baseline comparison**.
- [ ] Include all four comparisons, retaining the distinction between descriptive mean rankings and paired statistical evidence:

| Target | Best reported baseline | Baseline MAE (ppm) | Proposed MAE (ppm) |
|---|---|---:|---:|
| NH3 | Generic SSL | 16.13 ± 1.23 | 17.36 ± 1.54 |
| H2 | SVR | 31.37 ± 4.53 | 31.60 ± 2.29 |
| CO | PLSR | 25.57 ± 8.48 | 47.45 ± 7.38 |
| Ethylene | Extra Trees | 1.398 ± 0.197 | 1.627 ± 0.275 |

- [ ] Explain that the CO error ratio is approximately 1.86 (proposed/PLSR); improvement against scratch is not superiority over the best competing model. Do not mix this fixed-split comparison with the primary multi-fold CO gain.
- [ ] Offer a cautious interpretation: a lower-complexity linear latent-variable model may suit this small calibration set and response representation. Mark this as a hypothesis, not an established physical or causal explanation.
- [ ] Do not call close means statistical ties merely because SDs overlap. Existing Table S4 already reports a paired generic-SSL advantage on NH3.

**Completion evidence:** explicit scope sentence in both abstract and conclusion, plus a complete four-target discussion and qualified CO explanation.

### R3 — Express label efficiency in calibration-pair counts

**P1 | Analysis lead + manuscript lead | Locations:** Section V-C, Table II, new compact table or budget-curve figure.

- [ ] Define the unit: a labeled two-gas concentration pair, including fitting and validation labels. Distinguish unique pairs from exposure records, scalar target values, and augmented windows. Retain the exclusion of candidate-pool quantification costs.
- [ ] Add scratch and fine-tuned MAE versus pair-count curves with seed variability, or a compact comparison table. Use the existing farthest-point fixed-split data and label this as secondary evidence.
- [ ] Include the following directly observed comparison; these are descriptive comparisons, not equivalence tests:

| Target | Fine-tuned at 10 pairs, MAE (ppm) | Scratch at 20 pairs, MAE (ppm) | Interpretation |
|---|---:|---:|---|
| NH3 | 38.92 ± 4.56 | 36.84 ± 7.89 | Similar mean error, slightly worse with transfer |
| H2 | 81.88 ± 19.54 | 70.73 ± 30.45 | Transfer does not match the 20-pair scratch mean |
| CO | 80.99 ± 27.98 | 89.30 ± 39.24 | Lower mean error at half the pair budget |
| Ethylene | 2.418 ± 0.484 | 2.465 ± 0.745 | Similar mean error at half the pair budget |

- [ ] If reporting labels saved at a fixed error, define the error threshold and comparison rule, use measured budget points first, and clearly label any interpolation. Do not force monotonic curves or extrapolate beyond evaluated budgets. Quantify uncertainty from underlying outputs where available.
- [ ] Avoid a universal “50% fewer labels” claim: NH3 is only approximately comparable and H2 falls short at this comparison point.

**Completion evidence:** a reproducible table/figure that states pair counts, uncertainty, design, split, and the limits of approximate error matching.

### R4 — Report humidity and temperature status explicitly

**P0 | Acquisition lead | Locations:** Section IV-A/IV-D, supplementary acquisition details, limitations.

**Author-confirmed status:** temperature and humidity were neither controlled nor measured/recorded during the six-day acquisition. The author plans to improve environmental measurement in future experiments; this is future work, not evidence for the current dataset.

- [x] Record the confirmed absence of temperature/humidity control and measurements.
- [ ] State explicitly in the manuscript and supplement that neither temperature nor humidity was controlled or measured/recorded.
- [ ] Explain that environmental variation across the six acquisition days cannot be quantified or excluded as a confound; do not invent ranges, setpoints, or retrospective environmental corrections.
- [ ] Distinguish missing ambient/chamber environmental measurements from sensor operating temperature and electrical supply settings.
- [ ] Add future measurement and recording of temperature and humidity to the experimental-improvement plan. Recommend exposure-linked day/session logs for future evaluation; do not imply these already exist or promise environmental control unless adopted.

**Proposed manuscript wording:**

> Temperature and relative humidity were neither controlled nor measured during the six-day acquisition. Their variation and contribution to sensor-response differences therefore cannot be quantified retrospectively. Future experiments will include environmental measurements; exposure-linked acquisition-day records are also needed to support day-held-out evaluation.

**Completion evidence:** explicit disclosure of absent control and measurement, its implications for interpretation, and clearly identified future work.

### R5 — Explain the five-pair NH3 limitation

**P1 | Manuscript lead | Locations:** Section V-C, limitations/conclusion.

- [ ] State that 86.39 ± 36.11 to 86.02 ± 34.16 ppm is essentially no observed NH3 benefit at five pairs (0.37 ppm mean reduction).
- [ ] State that roughly 86 ppm is about 17.2% of the 0–500 ppm range and does not demonstrate useful precise quantitative calibration at this budget.
- [ ] Discuss sparse calibration coverage and training variability as possible explanations. Table S8 shows four distinct fitting records at the five-pair setting for seed 42; verify all seeds before generalizing that count.
- [ ] Connect this result with NH3's marginal primary interval and lack of sensor-ID/attention benefit. Avoid assigning a chemical mechanism without evidence.

**Completion evidence:** explicit smallest-budget limitation with absolute error and a clearly qualified explanation.

### R6 — Connect the H2 headline to window placement

**P1 | Analysis lead + manuscript lead | Locations:** abstract, Section IV-D, Section V-F, Table VI.

- [ ] State that the primary 21.5% H2 reduction uses the predefined early window.
- [ ] Correctly distinguish protocols: Table VI's fixed-split early-window values, 41.20 to 31.60 ppm, imply approximately **23.3%**, not 21.5%. The latter comes from Table I's multi-fold analysis.
- [ ] Report the fixed-split middle-window reversal (33.99 to 35.60 ppm; approximately −4.7% gain) and full-window improvement (38.36 to 35.75 ppm; approximately 6.8%). Note that window placement substantially changes absolute errors and transfer effects.
- [ ] Retain early-window predefinition; do not select a new window using test performance. Describe what “full-exposure” actually spans in the implementation, including whether recovery is included.

**Completion evidence:** accurate cross-reference between the headline and sensitivity study without conflating the two evaluation protocols.

### R7 — Identify the calibration design and its budget dependence

**P1 | Manuscript lead | Locations:** Table II caption, Section V-D, Table S3.

- [ ] Add “farthest-point calibration-pair design” to Table II's caption and the new label-efficiency display.
- [ ] Describe the design effect as both target- and budget-dependent; retain the known-concentration requirement.
- [ ] Identify the reviewer's quoted 40-pair differences as **scratch** results: random minus farthest-point is NH3 −4.46 ppm [−6.35, −1.66] and H2 −8.32 ppm [−11.53, −4.60].
- [ ] Also report the corresponding fine-tuned differences: NH3 −3.37 ppm [−5.50, −1.12] and H2 −4.89 ppm [−7.31, −2.45]. Negative values favor random design. Label these intervals exploratory and unadjusted.

**Completion evidence:** correct caption, sign convention, policy attribution, and balanced low-/higher-budget interpretation.

### R8 — Qualify multiplicity and the small number of folds

**P1 | Analysis lead | Locations:** Section IV-E, Section V-B, Table I, abstract, conclusion.

- [ ] Explicitly label all four primary 95% intervals as unadjusted. NH3 [0.38, 8.30] ppm is the weakest primary case and may not remain positive after multiplicity adjustment.
- [ ] Add a prespecified sensitivity analysis using unrounded paired seed/fold outputs, for example Bonferroni 98.75% marginal bootstrap intervals for a four-comparison family. Retain the paired/crossed resampling structure and equal fold weighting; use enough resamples to assess tail stability.
- [ ] Report the computed outcome rather than assuming NH3 loses significance or that the other targets survive. If raw outputs cannot be recovered, state the limitation and do not manufacture adjusted intervals from rounded endpoints.
- [ ] Mark CO/ethylene intervals as **indicative**, based on only three chronological test folds. Retain the overlapping-training-fold and observed-exposure conditioning limitations; ten seeds do not create ten independent acquisition campaigns.
- [ ] Apply this analysis to the retained identifier-fold primary results. Statistical adjustment does not resolve the missing day mapping or establish session independence.

**Completion evidence:** explicit multiplicity scope and three-fold limitation, with a reproducible sensitivity result if inputs are recoverable.

### R9 — Acknowledge fold-4 negative transfer

**P1 | Analysis lead + manuscript lead | Locations:** Section V-B, Table S1, discussion.

- [ ] State the existing fold-4 reversals: NH3 16.22 to 18.83 ppm and H2 25.70 to 26.36 ppm.
- [ ] Inspect per-seed paired differences, concentration coverage, and available session/environment metadata to distinguish descriptive patterns from plausible explanations.
- [ ] Explain that aggregate benefit does not imply benefit in every held-out partition. If no supported cause is identifiable, say so; do not remove the fold or change policy after inspecting it.
- [ ] Do not attribute fold 4 to a particular day or environmental condition without supporting records; its acquisition-day composition is unknown under R1.

**Completion evidence:** a brief main-text acknowledgment and evidence-based or explicitly unresolved interpretation.

### R10 — Give the early window a physical duration

**P1 | Acquisition lead + analysis lead | Locations:** Section IV-A/IV-D, supplementary acquisition protocol, window definitions.

**Author-confirmed acquisition details:** the first sample of each sequence corresponds to the start of gas delivery. Each complete sequence contains 180 s of gas exposure followed by 700 s of recovery (880 s total). The configured sampling interval was 2.0 s. Availability of actual timestamps has not been specified.

- [x] Record the confirmed onset alignment, full-cycle duration, and configured sampling interval.
- [ ] Report 2.0 s as the configured interval. If timestamps are available, use them to check effective cadence and missing samples; do not present an aggregate estimate as timestamp verification.
- [ ] Record the reviewer's aggregate consistency calculation: 162,404 / 378 ≈ 429.64 observations per sequence; 880 / 429.64 ≈ 2.048 s per observation; 64 × 2.048 ≈ 131 s, approximately 73% of the stated 180-s gas exposure.
- [ ] Replace the blanket statement that no duration interpretation is possible with an approximate physical description supported by the nominal setting and aggregate counts. Describe 131 s as an estimate, not a directly verified timestamp interval.
- [ ] Use the confirmed onset alignment to describe the early window physically: 64 sample periods correspond nominally to about 128 s (71% of the 180-s exposure); the aggregate-count estimate gives about 131 s (73%). Present these as approximate descriptions, distinguishing configured cadence from the count-derived estimate. The elapsed span from the first to the 64th timestamp is 63 intervals (126 s at the nominal cadence).
- [ ] State that the 880-s full sequence includes recovery. Verify what the implementation calls the full-exposure window; do not imply that the entire recorded cycle is gas exposure. Document training offsets 0-4 separately from the offset-zero test window.
- [ ] Supply exact early/middle/late/full index definitions; the main manuscript promises these, but they were not found in the supplied supplement's extracted text.

**Completion evidence:** consistent approximate timing, onset alignment, and window definitions; no unsupported exact sampling-frequency claim.

## Smaller points

IDs S1–S8 follow the order of the eight bullets on reviewer-comment page 2.

| ID / priority | Action | Location and completion check |
|---|---|---|
| S1 / P2 | Keep Z for sensor tokens and rename the mask-participation indicator, e.g. B. Define batch index b, span index k, span start a_k, its allowed range/distribution, and mask convention consistently with code. | Eqs. (8), (11)–(13) and nearby prose; one meaning per symbol and all indices defined. |
| S2 / P1 | Guard the visible-value denominator in Eq. (14), e.g. max(1, sum M), and check the implementation. If code already guards it, correct the equation only. If not, determine whether an empty-visible mask occurred and whether results are affected. | Eq. (14), SSL loss implementation; finite loss for empty-mask edge cases and disclosure/rerun if an actual implementation defect changes outputs. |
| S3 / P2 | Replace the literal question-mark placeholder with a stable supplementary section reference. | Manuscript p. 4; reference resolves in final PDFs. |
| S4 / P2 | Use “we” consistently for the research team, or consistent passive voice where appropriate; replace “avoids need for” with “avoids the need for.” | Manuscript, supplement, new response; preserve third-person references to other researchers and biographies where appropriate. |
| S5 / P1 | Rewrite the abstract around the result and protocol, following the detailed title/abstract action below. The reviewer says the roughly 290-word abstract overcorrects toward disclaimers; the author agrees. Lead with the main finding, explain the method and evaluation briefly, and retain only one or two essential scope sentences. Move detailed qualifications to the discussion. Keep the abstract strictly below 250 words (maximum 249 words), as required by the author. | Abstract; finalize after R1/R8, verify word count and numbers, and ensure the main result is immediately understandable. |
| S6 / P1 | Explicitly describe CO ablation effects as uncertain/consistent with no clear benefit, including no-attention 10.27 ± 12.18 and no-time-mask 7.93 ± 14.86 ppm. Check paired intervals before making formal significance claims; SD is not a CI. | Section V-F, Table V; CO-specific qualification rather than only a generic cross-gas caveat. |
| S7 / P2 | Move the existing repository link from after the biographies into a dedicated data and code availability statement. Describe which datasets, code, split manifests, and outputs are actually accessible, and any restrictions. Verify the destination before submission. | Availability statement and biographies; valid link and accurate access description. |
| S8 / P1 | Report pretraining hardware, device count, relevant software, epochs, batch size, and measured wall time per run/dataset; distinguish per-model cost from the total ten-seed/fold campaign. Recover logs first; if absent, time a representative rerun and label it accordingly. Explain checkpoint reuse/amortization without claiming unmeasured financial savings. | Section IV-D or a concise compute table in the supplement referenced once in the main text; measured cost accompanies label savings. |

## Title and abstract revision - additional reviewer explanation

**Priority P1 | Manuscript lead | Source:** additional reviewer wording supplied by the author in this conversation. The author agrees that the current abstract is overly precautionary. This supplements S5 and the title recommendation; it does not replace the numbered comments.

**Reviewer concern:** the roughly 290-word abstract is dominated by scope disclaimers, making the result difficult to extract. The title foregrounds "Sensor-Aware" even though Table V does not support a benefit from sensor identity or attention for NH3. The revision should foreground the demonstrated contribution and present limitations in proportion to the findings.

**Evidence to represent accurately:** Table V reports ablation-minus-full-model differences. Removing sensor identity changes NH3 MAE by -0.06 +/- 1.66 ppm, effectively no clear benefit from identity; removing attention changes it by -3.01 +/- 1.49 ppm, favoring the model without attention. The reviewer describes the components as supported for H2 and CO. Retain the target-specific interpretation, but also preserve S6: CO component estimates have substantial uncertainty, so do not turn the reviewer's wording into an unqualified statistical claim. Mean +/- SD is not a confidence interval.

### Title action

**Recommended title:** Self-Supervised Transfer Learning for Label-Efficient Multigas Electronic Nose Calibration

- [ ] Remove "Sensor-Aware" from the title to foreground the evaluated transfer-learning approach and calibration task, rather than imply broadly established benefits from the sensor-aware components.
- [ ] Retain sensor identity and cross-sensor attention as precise method descriptions. Explain their target-dependent ablation results in Section V-F and the discussion.
- [ ] Support "Label-Efficient" with explicit calibration-pair comparisons (R3), without implying a benefit at every budget or on every target.
- [ ] Confirm the final title and synchronize clean/highlighted manuscripts, response, and submission metadata. The replacement remains a recommendation until selected by the author.

**More conservative alternative:** Evaluating Self-Supervised Transfer Learning for Multigas Electronic Nose Calibration

Use the alternative if the final emphasis is the controlled evaluation and mixed findings rather than the label-efficiency result. Neither title implies acquisition-day independence or environmental robustness.

### Abstract action

- [ ] Replace the acquisition-cost motivation and disclaimer-heavy opening with the central result and evaluation setting. Present the existing primary relative MAE reductions against scratch (NH3 13.9%, H2 21.5%, CO 27.5%, ethylene 25.7%) prominently, subject to final numerical/statistical checks.
- [ ] Name the comparator explicitly: these are gains against matched scratch training, not against the best classical or generic-SSL baseline.
- [ ] Briefly describe masked self-supervised pretraining followed by predefined fine-tuning, ten seeds, six NH3/H2 identifier-based folds, and three chronological CO/ethylene folds. Use accurate protocol names rather than adding several sentences of defensive explanation.
- [ ] Attach the early-window condition directly to the NH3/H2 result or protocol description, including the 21.5% H2 headline, without reproducing the full window-sensitivity discussion.
- [ ] Include one concrete label-budget finding from R3 if space permits. Do not generalize approximate 10-versus-20-pair matching to all four targets or claim formal equivalence.
- [ ] Keep one or two concise scope sentences that plainly state the proposed model is not the best full-budget baseline on any target and that the evidence concerns same-system calibration, with NH3/H2 day independence unverified. Integrate scope naturally rather than append a catalogue of caveats.
- [ ] Move detailed multiplicity discussion, three-fold bootstrap limitations, five-pair NH3 failure, component ablations, environmental-recording limitations, candidate-pool quantification costs, and prospective acquisition-cost questions to their relevant results/discussion sections. Keep all required disclosures in the paper.
- [ ] Include the drift extension only if needed to represent the paper's scope within the word budget. If mentioned, state known-gas-identity conditioning and the lack of clear benefit in partition 10 concisely; do not headline the favorable drift results alone.
- [ ] Avoid an abstract-wide claim of statistically established gains for all targets before R8 is resolved. Report effect sizes directly; use uncertainty wording consistent with the final analysis.
- [ ] Keep the abstract strictly below 250 words (maximum 249 words). Verify the final word count after all edits. Make every sentence contribute a result, essential protocol detail, method explanation, or necessary scope statement.

**Proposed abstract structure:** main result and comparator; brief method and evaluation protocol; concrete label-budget finding; concise full-budget ranking and scope. Do not open with speculative cost savings or end with a long future-work list.

**Completion evidence:** a verified abstract word count of at most 249 words; a shorter, result-led abstract in which readers can identify the finding, comparator, and evaluation setting on first reading; a title consistent with mixed component evidence; and a reviewer response explaining that detailed qualifications were relocated rather than omitted.

## Required revision outputs

- [ ] Updated clean manuscript and highlighted manuscript generated from the same final source.
- [ ] Updated supplement with explicit inability to reconstruct the day mapping, label-budget evidence, statistical sensitivity, acquisition conditions, timing/window definitions, and compute reporting as applicable.
- [ ] A new response covering R1–R10 and S1–S8 individually: reviewer concern, action taken, result or limitation, and final section/table/page location. Explain source-based numerical distinctions respectfully for R6 and R7.
- [ ] Reproducible evidence exports and scripts for every new analysis, with a provenance record linking them to final tables. Clearly distinguish retained V2.2 results from new statistical or descriptive analyses; do not label retained folds as day-held-out.

## Final acceptance checks

- [ ] Every reviewer item has an explicit response; unresolved metadata are described honestly rather than presented as completed experiments.
- [ ] Fold means reproduce aggregate tables; gains and differences are calculated from unrounded values; SDs and CIs have distinct labels and consistent signs.
- [ ] Abstract, main text, tables, supplement, and response agree on the primary split, budgets, window, seeds, and inferential scope.
- [ ] No test-based policy/window/budget selection is introduced; paired comparisons retain matched data assignments.
- [ ] Label-efficiency claims count fitting plus validation labels and do not turn retrospective label withholding into demonstrated acquisition-cost savings.
- [ ] Adverse and null results remain visible: five-pair NH3, full-budget competing baselines, fold 4, middle-window H2, uncertain CO ablations, and drift partition 10.
- [ ] Retain established scope limits: same-system recalibration, known gas identity for drift regression, and no established cross-device transfer.
- [ ] Inspect final PDFs for equations, table fit, figure readability, links, placeholders, and cross-references; confirm clean/highlighted numerical consistency.

The R1 decision is to disclose the unavailable day mapping and retain the identifier-based evaluation with narrower claims. Proceed with the revision on that basis. R4 is resolved factually: temperature and humidity were neither controlled nor measured/recorded. R10 now has author-confirmed gas-onset alignment, cycle duration, and configured sampling interval; actual timestamp availability remains unspecified.
