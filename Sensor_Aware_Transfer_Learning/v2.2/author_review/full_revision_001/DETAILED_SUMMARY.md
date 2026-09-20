Latest wording update: third-person author wording applied throughout submission documents; PDFs and ZIP synchronized. Manuscripts remain 10 pages.

Current submission: the authoritative highlighted manuscript and synchronized clean manuscript render to 10 pages. Earlier nine-page records describe the layout before the author's Table IV placement change.

# Full revision handoff

Current submission: clean and highlighted manuscripts each render to 10 pages. All five DOCX/PDF pairs and the existing ZIP are synchronized.

Completed: 2026-09-19T09:23:58.073565+00:00

## Deliverables

- `IEEE_Full_Revision_Clean.docx`: full revised manuscript in the original IEEE document, without highlighting.
- `IEEE_Full_Revision_Highlighted.docx`: identical content/layout with yellow highlighting of revised and inserted text/values; this is not Word tracked changes.
- `RESPONSE_TO_REVIEWERS.docx` and `.md`: nine major, eleven moderate and six presentation points, with manuscript locations and all main numerical tables.
- `SUPPLEMENTARY_EVIDENCE.docx`: fold-level results, all-budget baselines, paired generic/design comparisons, all-policy per-gas and normalized drift, small budgets, target/loss controls, capacity and seed sensitivity.
- `SEED_STABILITY.docx` and `.md`: direct answer to the seed-count question, with both same-protocol and explicitly noncomparable historical comparisons.
- `evidence/`: frozen unrounded CSVs, predictions, audit/normalization records, protocol, source hashes and generating scripts.

## Work completed

Resumed the unchanged major_revision_001 run from 1,369/1,390 raw jobs and no completed drift jobs. Completed all 1,390 raw-response jobs and 290 drift jobs across eight suites. Every one of the 139 raw configurations and 29 drift configurations contains the ten predefined seeds. Raw pretraining uses 60 epochs, drift pretraining 40, and adaptation 120. No test-based policy, checkpoint, seed count, or transform selection was introduced.

Promoted six NH3/H2 and three chronological CO/ethylene folds; completed generic SSL, PLSR/SVR/tree, random-design, architectural ablation, early/middle/late/full window, tiny drift budget, constant-predictor and target/loss comparisons. Added normalized per-gas and macro error, scratch tail metrics, parameter/sample counts and explicit uncertainty limitations. The manuscript is result-grounded and retains adverse/null results.

## What the results now support

The research motivation is inexpensive mixture recording without carefully controlled ppm, reserving costly precise concentration labels for a small calibration set. Existing controlled datasets with pretraining labels withheld test this learning premise retrospectively. Actual savings and transfer from a prospectively acquired unquantified mixture pool remain untested. Known-coordinate farthest-point selection is a calibration-design control; its selected-pair budget excludes the cost of quantifying the candidate pool.

Primary multi-fold MAE reductions are 13.9% NH3, 21.5% H2, 27.5% CO and 25.7% ethylene. Nominal paired seed/fold intervals exclude zero, but are conditional on observed exposures and few partly overlapping folds. The sensor-aware model is not universally superior: generic SSL and classical baselines outperform it on some targets.

Adding seeds weakens secondary full-budget fixed-split gains (NH3 32.4%→19.6%, H2 27.2%→23.3%, CO 27.2%→25.4%, ethylene 31.1%→24.3%). Primary multi-fold gains are more stable. Partition-10 primary drift macro-MAE is 142.34±11.06 ppm scratch versus 143.05±12.49 ppm fine-tuned; paired difference −0.71 ppm, 95% interval [−8.40, 6.91]: no clear improvement.

## Verification

- All source data hashes, including all ten drift partitions, match the frozen input manifest
- 139 raw-response configurations have ten distinct seeds and common policy holdouts
- 29 drift configurations have ten seeds; fitting is partition 7 only; test identities/labels and shared holdouts verified
- All ten delivered DOCX tables independently match final CSVs or recomputed paired ablation differences
- Response covers nine major, eleven moderate and six presentation points; its numerical tables match the manuscript
- All 30 references are cited; no undefined citations
- All 64 original main-document OMML equation objects, author text, Fig. 2 bitmap and page/column settings are preserved.
- Clean and highlighted document XML is identical after removing highlight elements. All ten main tables are independently checked against final results; response tables match exactly.
- Seven protocol tests pass. Full experiment/manuscript consistency gate passes. The checker was corrected to reproduce NumPy float32 Q0.9 arithmetic instead of pandas float64 interpolation; all 42 flagged discrepancies reproduced exactly in float32, with maximum absolute float64 difference below 0.0006 ppm. No training results were changed.
- Rendering: PASS: rendered PDF checks and page proof. See `render_validation.json` for proof coverage and renderer limitations.

## Explicitly unresolved / scope limits

Reference [28] adds the author-supplied published sensor-design context. The companion NH3/H2 description establishes 20 Nano MEMS channels. The cited chapter concerns VOC mixtures; equivalence of the NH3/H2 configuration and dataset-specific acquisition settings remain unverified. Physical acquisition independence cannot be proved without acquisition records; the digital audit establishes identifier separation and no identical stored signal fingerprints, not laboratory independence. No compatible cross-device experiment or shift-aware conformal guarantee is claimed. These limits are stated in the manuscript and response.

## Reproduction

Training code and source data remain unchanged. Use README_MAJOR_REVISION.md for the immutable experiment command, then run export_revision_results.py, build_revision_manuscript.py and check_paper_consistency.py with --run-id major_revision_001. Run analyze_seed_stability.py, build_full_revision_docx.py, verify_full_revision.py and write_full_revision_handoff.py for this full author package. Earlier minimal-review copies and historical outputs are preserved.

Dataset-description update: The NH3/H2 dataset is cited as Harvard Dataverse, doi: 10.7910/DVN/LWUSKO, reference [29]. Its metadata matches 162,404 observations, 20 channels and 378 sequences. The main description is shortened; split/leakage rules remain in the paper. Acquisition limitations and exact sensitivity-window definitions are retained in the existing supplement. Dataset-specific acquisition settings and physical independence remain unverified. Numerical results and figures are unchanged. The pre-citation backup, quoted reviewer comments and historical experiment records remain historical. The archived full-document generator contains the updated text; scripts outside this delivery folder have not been modified.

Validation of this update: all 30 references are cited; clean/highlighted XML differs only by highlighting; all ten numerical tables, 64 equation objects, figures and section settings are unchanged. Updated PDFs have no blank pages or out-of-page text. Main manuscripts remain 11 pages; response is 10 pages and supplement is 14 pages. The 8?9-page target still requires the broader proposed reductions. Existing proof images and ZIP contents have been refreshed in place.

Windowing citation update: Reference [30], doi: 10.1109/JSEN.2025.3642226, is added beside the NH3/H2 64-sample extraction protocol and in supplementary window details. Bibliographic metadata is verified (IEEE Sensors Journal 26(3), 4739-4748, February 2026). Full text was inaccessible; the citation establishes related work, not verification of an exact prior 64-sample cut or an optimal window. All 30 references are cited. Numerical tables and original equations are unchanged.

Figure readability update: Fig. 3 now uses contrasting orange one-SD shading with outlined bounds and a larger explicit legend. Fig. 4 has bold 8.5-point legend labels and opaque 7-point gray-circle/blue-square/orange-triangle symbols, with larger, clearer scatter points. Original figure dimensions, ten-seed data, means, SD bounds and prediction values are unchanged. Existing figure assets, manuscripts, response and supplement are updated in place.

Figure-update validation: refreshed clean/highlighted PDFs remain 11 pages, response 10 pages, supplement 14 pages. All ten numerical tables match the existing manifest. Clean content and formatting are synchronized to the current highlighted manuscript with highlights removed. Figure pages 6 and 7 were visually checked; PDF bounds and clean/highlighted text checks pass.

Section VI now discusses the study as a whole: primary outcomes, competitive baselines, drift behavior, statistical/acquisition limitations, cost motivation and prospective validation. Revision-history and three-versus-ten-seed narrative are removed from the conclusion. Numerical findings and scientific qualifications are retained.

Acquisition-documentation update (supplement/response only): The newly supplied Vietnamese acquisition account reports 20 MEMS SnO2 channels with Pt/Ag modification, 3.0-3.4 V settings, MFC-based gas delivery, 180-s exposure and 700-s recovery, nominal 2-s sampling, a distinct 175-SPS setting, and six measurement days. The supplement records conflicting environment values, 60-versus-57 unique-pair counts, the 13-versus-23 field inconsistency, timing/row-count and MFC-mapping ambiguities, and missing per-channel/heater/flow/reference-calibration metadata. These details supersede earlier statements that no acquisition account was available; they do not independently verify every setting. Main manuscript DOCX/PDF files and scientific results are unchanged. Reviewer responses to acquisition characterization, sensor-ID interpretation and repeated exposures are updated.

Supplementary presentation update: The acquisition section now uses the authors' perspective and describes only the sensor array, gas chamber/delivery apparatus and acquisition protocol. Figure S2 contains the system schematic; Figure S3 contains the sensor, chamber and MFC photographs. Acquisition sample-count and conflicting-setting commentary, source-translation framing and Reproduction and scope are removed. Existing result tables are retained. The main paper remains byte-for-byte unchanged.

Submission synchronization: The latest highlighted manuscript formatting is propagated to the clean manuscript without changing the text. All five submission DOCX files (clean, highlighted, reviewer response, supplementary information, seed stability) are freshly rendered to their existing PDFs. The Vietnamese acquisition DOCX remains a source document and is not a submission DOCX/PDF pair. The existing submission ZIP is refreshed after validation.

Paragraph-layout optimization: Removed two empty body spacers; normalized body paragraph spacing to zero and heading spacing to 6/3 pt before main/subheadings and 1 pt after; released figure captions from following sections/tables while keeping figure-caption pairs together. Author biography groups stay with their photos. Text, all 64 equations, numerical tables, graphic assets, font sizes, margins and column settings are unchanged. The clean manuscript follows the latest highlighted version.

Nine-page compression: Removed 1,418 words of repeated introductory, related-work, method-motivation, seed/generic-control commentary and discussion prose. All four figures, ten main tables, 30 references, author biographies and 64 equation objects are retained. No font-size, margin, column or graphic-size reduction was applied. Detailed seed and generic-control comparisons remain in the existing supplement. The conclusion remains study-focused and retains adverse/null findings, conditional inference, cost and transfer limitations.

Authoritative-source synchronization: The current IEEE_Full_Revision_Highlighted.docx is retained unchanged. Table IV follows the baseline-comparison discussion. Clean manuscript, PDFs, text audit, proofs, generation code, validation records and ZIP are synchronized with that placement. Numerical tables and supporting-document content are unchanged.
