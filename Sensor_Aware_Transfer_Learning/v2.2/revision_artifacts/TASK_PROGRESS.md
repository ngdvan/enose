# Revision task ledger

**Final update, 2026-09-19:** All eight experiment suites are complete, comprising
1,390 raw-response jobs and 290 drift jobs with ten seeds per configuration.
The full consistency gate, all ten final DOCX table checks, input/holdout audits,
28-reference checks, 64-equation preservation checks, and rendered page proofs
pass. Clean/highlighted full manuscripts, response, supplement and seed audit are
delivered at `../author_review/full_revision_001/DETAILED_SUMMARY.md` relative to
this file.
A published sensor-design reference and the companion description of Nano MEMS
technology are included. Dataset-specific hardware/environment settings remain
unverified. Physical acquisition independence cannot be established without
laboratory records. The implementation-stage ledger below is retained as history;
its earlier pending-run statements are superseded by this update and
`../REVISION_STATUS.md`.

This ledger distinguishes implementation from completed scientific evidence. Live run completion is recorded in `../../REVISION_STATUS.md` and the run's suite markers. Final tables must come from a full run, never from smoke artifacts or this progress summary.

| Task | Implementation/artifact status | Scientific completion requirement |
|---|---|---|
| 0 Freeze state | Complete: Git tag, commit, dirty status, original code/results/DOCX, environment and source hashes | Historical outputs preserved |
| 1 Policy selection | Complete in revision runner: fine-tuning predefined; common adaptation holdout; separate policies | Full neural reruns still required |
| 2 Ten seeds | Central ten-seed protocol implemented; full run launched | Every full-suite marker and expected job count |
| 3 Primary multi-fold | Six NH3/H2 folds and three chronological folds implemented; primary manuscript table and bootstrap export | Full multi-fold reruns |
| 4 Drift controls | Constant fitting mean, per-gas/macro NMAE, five budgets, paired partition-10 statistics implemented and smoke-tested | Full drift reruns |
| 5 Generic SSL | Compact PatchTST-style reimplementation, documented deviations, matching data/seeds/budgets; smoke-tested | Full generic reruns |
| 6 Chemometric baselines | PLSR, SVR, Extra Trees, XGBoost; 360 full jobs completed across ten seeds | Complete; comparison with neural models awaits their results |
| 7 Calibration design | Random/farthest crossed with scratch/fine-tuning; paired design statistics implemented | Full design reruns |
| 8 Transfer scope | Same-system/cross-device limitations written | No compatible cross-device test is asserted |
| 9 Hardware records | Missing-field record created; author asked for authoritative acquisition records | Unavailable fields remain explicitly unknown |
| 10 Window sensitivity | Early/middle/late/full definitions implemented and documented; full-budget ten-seed runner | Full sensitivity reruns |
| 11 Statistics | MAE/RMSE/R2/Q90, seed SD, crossed bootstrap, parameter counts/effective exposure counts implemented | Full exports and interpretation |
| 12 Conformal | Exchangeability violation explicit; historical coverage not presented as new measurements | Wording addressed; no shift-aware method claimed |
| 13 Drift loss/scaling | Historical log-Huber, fixed-log Huber, fixed-linear Huber and MAE implemented; tiny-budget fixed scaling | Full loss/scaling reruns |
| 14 Exposure audit | Complete: 623 records, no identical fingerprints, no ID overlap in 11 split definitions | Physical independence still requires laboratory logs |
| 15 Literature | Ten relevant primary-source additions; 27-reference draft builder | Author bibliographic/style proof review |
| 16 Results structure | Requested section order implemented in result-grounded draft builder | Final manuscript generation after reruns |
| 17 Abstract | Final abstract deliberately gated on full reruns and generated from CSV values | Not final while run remains incomplete |
| 18 Discussion | CO, identity variability, drift, same-system limitations incorporated | Final numerical interpretation after reruns |
| 19 Presentation | Typos/keywords corrected in new review draft; native DOCX tables; vector Fig. 3; Fig. 2 preserved | Final IEEE layout and print proof review |
| 20 Reviewer response | Point-by-point builder covers nine major comments, moderate subcomments, presentation; numerical tables embedded when available | Final response after full reruns; author hardware response |
| 21 Consistency gate | Implemented; rejects smoke, partial suites, changed code, leakage, unsupported claims, citation mismatches | Must pass on full final artifacts |

Seven protocol tests passed. The complete smoke matrix passed execution, exports, and draft generation. Its publication gate deliberately failed because smoke artifacts have insufficient repeats/epochs and the initial smoke preceded two final code fixes. The full run began after those fixes and records its exact code hashes.

No task that requires full neural results is marked scientifically complete merely because its code is implemented.
