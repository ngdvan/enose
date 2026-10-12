# Revision 3.0 — completed local revision

The revised title is **Self-Supervised Transfer Learning for Label-Efficient Multigas Electronic Nose Calibration**. The result-led abstract has **230 whitespace-delimited words**, or 246 when hyphenated terms and decimal components are split; both counts are below 250.

## Review files

| Deliverable | Editable source | PDF proof |
|---|---|---|
| Clean manuscript | [Word](submission/IEEE_Revision_3.0_Clean.docx) | [PDF](submission/IEEE_Revision_3.0_Clean.pdf) |
| Highlighted manuscript | [Word](submission/IEEE_Revision_3.0_Highlighted.docx) | [PDF](submission/IEEE_Revision_3.0_Highlighted.pdf) |
| Supplement | [Word](submission/SUPPLEMENTARY_EVIDENCE.docx) | [PDF](submission/SUPPLEMENTARY_EVIDENCE.pdf) |
| New reviewer response | [Word](submission/RESPONSE_TO_REVIEWERS.docx) | [PDF](submission/RESPONSE_TO_REVIEWERS.pdf) |

The response also has a [Markdown version](submission/RESPONSE_TO_REVIEWERS.md); the [abstract](submission/ABSTRACT.md) is available separately. Highlights identify changed paragraphs/equations and the new table relative to the recovered V2.2 clean source; they are not Word tracked changes. Deletions and replacements are recorded in [document_changes.json](evidence/document_changes.json).

## Reviewer-item disposition

| Item | Implemented revision |
|---|---|
| R1 | Explicit six-day acquisition and identifier-partition distinction; missing mixture/day logs prevent defensible leave-one-day-out evaluation. Claims narrowed, no invented day split. |
| R2 | Abstract, baseline discussion and conclusion explicitly state that no target has the best full-budget mean; all four leaders and the 1.86 CO/PLSR error ratio are reported. |
| R3 | New Table IIa compares 10 transfer pairs with 20 scratch pairs; fitting/validation labels are included and approximate matching is distinguished from equivalence. |
| R4 | Temperature and humidity were neither controlled nor measured; environmental confounding is acknowledged and future measurements are identified. |
| R5 | Negligible five-pair NH3 benefit and approximately 17.2%-of-range error are stated. Possible causes are qualified. |
| R6 | Early-window condition attached to the headline; 21.5% multi-fold gain distinguished from 23.3% fixed-split gain. “Full” corrected to “full-cycle,” including recovery. |
| R7 | Table II/IIa identify farthest-point design; budget dependence and scratch versus fine-tuned 40-pair contrasts clarified. |
| R8 | Original intervals labeled unadjusted; new 200,000-draw multiplicity sensitivity and second-RNG stability check. NH3 includes zero after adjustment; three-fold CO/ethylene inference is indicative. |
| R9 | Fold-4 adverse results acknowledged without assigning unsupported day/environment causes. |
| R10 | Configured 2.0-s sampling, gas-onset alignment and 880-s cycle stated; approximate 128/131-s early duration and exact index definitions supplied. |
| S1 | Mask participation renamed B; indices and span start defined. |
| S2 | Eq. (14) and versioned raw-response code guard both denominators. Existing mask guarantees a nonempty visible set, so reported losses/results are unchanged. |
| S3 | Supplementary-reference placeholder removed. |
| S4 | First-person author voice and grammar corrected. |
| S5 | Title revised; abstract shortened to below 250 words and led by findings. |
| S6 | CO-specific uncertainty discussed with paired intervals. Temporal masking includes zero; attention does not in the exploratory conditional analysis. The response explains why SD alone does not establish a statistical null. |
| S7 | Data/code availability statement added; repository link moved out of biographies. |
| S8 | Representative seed-42 pretraining measured on an RTX 3060: 38.8 s NH3/H2 and 19.9 s CO/ethylene, with scope and software recorded. |

## New evidence and qualifications

The four-comparison Bonferroni sensitivity uses 98.75% marginal percentile intervals, preserving the original paired seed/fold resampling structure and equal fold weights:

| Gas | Scratch minus transfer MAE (ppm) | Adjusted interval (ppm) |
|---|---:|---:|
| NH3 | 4.31 | [−0.60, 9.46] |
| H2 | 10.58 | [2.08, 21.54] |
| CO | 24.74 | [8.63, 41.71] |
| Ethylene | 0.672 | [0.167, 1.249] |

These intervals remain conditional on observed exposures. Multiplicity adjustment does not establish acquisition independence. The original ten predictive-result tables were retained; the timing reruns did not replace any performance estimates or select models.

CO ablations need a distinction from the reviewer's suggested blanket null interpretation: the attention interval is [2.68, 16.94] ppm, whereas the temporal-mask interval is [−0.33, 17.00] ppm. Both are exploratory and variable. Full numerical outputs and provenance are in [evidence](evidence).

Actual timestamp availability is unspecified; the physical duration uses author-confirmed nominal timing plus an aggregate consistency calculation. Environmental measurements and reliable mixture-to-day logs do not exist. Historical total campaign runtime and descriptor-pretraining wall time were not reconstructed; the compute statement covers representative raw-response pretraining only.

## Validation and provenance

- Preserved all ten original numerical tables, all 64 editable equation objects, references and embedded media; added Table IIa and supplementary Tables S9/S10.
- Clean and highlighted Word XML/PDF text agree apart from highlighting.
- Automated checks cover abstract length, table preservation, finite guarded-loss arithmetic, paired interval conclusions, blank pages and text outside page bounds.
- PDF proofs and page contact sheets were reviewed, including equations, the new table, supplement additions, and reviewer response. A biography photo was kept with its text, and inherited equation tokens were repaired for PDF rendering without changing their meaning.
- The supplied Base v2.2 PDFs remain the authoritative reference. Editable files were recovered from `../v2.2/author_review/full_revision_001`; source hashes and the document-change log are retained. The supplementary source PDF is byte-identical to the supplied baseline; the main PDF differs in rendering, and its prose/results were reconciled against the supplied baseline.
- The existing [study repository](https://github.com/ngdvan/Transfer-learning-Enose) was reachable during revision. No files were uploaded or published there.

See [validation.json](evidence/validation.json) for automated checks. PDFs were rendered with the existing archived LibreOffice installation; Word/publisher pagination may differ. Final source and proof files are ready for author review.

## Reproduction in this checkout

Run these commands from the ENose repository root:

```powershell
python Sensor_Aware_Transfer_Learning/V3.0/scripts/analyze_revision.py
# Optional: remeasure compute; this changes timing values and requires original data/GPU.
python Sensor_Aware_Transfer_Learning/V3.0/scripts/measure_compute.py
python Sensor_Aware_Transfer_Learning/V3.0/scripts/build_revision.py
python Sensor_Aware_Transfer_Learning/V3.0/scripts/build_response.py
& Sensor_Aware_Transfer_Learning/V3.0/scripts/render_revision.ps1
python Sensor_Aware_Transfer_Learning/V3.0/scripts/validate_revision.py
```

The build uses retained V2.2 editable sources and exports in this checkout. The renderer path in `render_revision.ps1` points to the existing local archive. Raw datasets and historical model checkpoints are not duplicated into V3.0; the versioned code and exported results are included. The inherited code variable `sessions` denotes identifier partitions, not recorded measurement days.
