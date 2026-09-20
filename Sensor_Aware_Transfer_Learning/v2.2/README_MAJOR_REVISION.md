# IEEE Sensors major revision

## Active project after cleanup (2026-09-20)

This is the only maintained implementation. See [CLEANUP.md](CLEANUP.md) for removed material and retained dependencies, [GRAPHICS.md](GRAPHICS.md) for final graphics and regeneration, and `requirements.txt` for focused dependencies. Historical delivery checks below describe the original handoff; the latest cleanup verification is recorded in `cleanup_validation.json`.

The original data paths and hashed experiment code are preserved. Frozen evidence snapshots retain historical code for provenance. Use the full-revision commands below; the minimal-document helper module is retained because the full builder imports its formatting functions.

## Full revision delivered (2026-09-19)

The full immutable matrix is complete: 1,390 raw-response jobs and 290 drift jobs,
with all ten seeds in every configuration. The experiment consistency gate and
independent checks of all ten final DOCX tables pass. The full original-format
manuscript, highlighted comparison, response and supplement are in
[`author_review/full_revision_001`](author_review/full_revision_001/DETAILED_SUMMARY.md).
Both main documents were rendered and visually proofed with an isolated local
LibreOffice renderer after Word PDF automation stalled. Reference [28] now adds
the author-supplied sensor-design chapter, and the companion dataset description
documents 20 Nano MEMS channels. Dataset-specific hardware and environmental
settings remain unverified.

Full-document authoring and verification, after the result exports below:

```powershell
python Sensor_Aware_Transfer_Learning/v2.2/scripts/analyze_seed_stability.py
python Sensor_Aware_Transfer_Learning/v2.2/scripts/build_full_revision_docx.py
python Sensor_Aware_Transfer_Learning/v2.2/scripts/verify_full_revision.py
python Sensor_Aware_Transfer_Learning/v2.2/scripts/check_full_revision_render.py
python Sensor_Aware_Transfer_Learning/v2.2/scripts/write_full_revision_handoff.py
```

The render checker consumes the four already exported PDF proofs; regeneration
uses the isolated LibreOffice `soffice.com --headless --convert-to pdf` command.
The seed audit distinguishes weaker secondary fixed-split gains from the more
stable primary multi-fold results. See `SEED_STABILITY.md` in the handoff folder.

All revision code, checkpoints, logs, manuscripts, and results are contained in this v2.2 directory. Original data are read from the existing repository; no source dataset or earlier result is overwritten.

## Run and reproduce

From the repository root:

```powershell
python Sensor_Aware_Transfer_Learning/v2.2/scripts/test_revision_protocol.py
python Sensor_Aware_Transfer_Learning/v2.2/code/run_major_revision.py --run-id major_revision_001 --suite all
python Sensor_Aware_Transfer_Learning/v2.2/scripts/export_revision_results.py --run-id major_revision_001
python Sensor_Aware_Transfer_Learning/v2.2/scripts/build_revision_manuscript.py --run-id major_revision_001
python Sensor_Aware_Transfer_Learning/v2.2/scripts/check_paper_consistency.py --run-id major_revision_001
```

The full run uses 10 independently seeded pretraining and adaptation repeats (42, 142, ..., 942), 60 raw-response pretraining epochs, 40 drift pretraining epochs, and 120 supervised epochs. Fine-tuning is the predefined primary policy for every target. Test results never choose a policy, checkpoint, or baseline hyperparameter. Frozen and scratch results remain separate.

Jobs are atomic JSON files under `revision_artifacts/runs/<run-id>/jobs` and `drift_jobs`. Repeating a command resumes completed jobs only when the code/input/configuration hashes match. Use a new run ID after changing code or settings. Do not run two writers with the same run ID simultaneously. Exported tables are under that run's `exports/` directory, preserving provenance and earlier outputs. Smoke results use separate IDs and cannot pass the manuscript gate.

The copied historical modules provide data loading and model definitions; the authoritative revision entry point is `code/run_major_revision.py`. Do not use the historical modules' standalone main functions to generate revision tables.

## Statistical and scientific boundaries

- Multi-fold validation is primary: six held-partition NH3/H2 folds and three chronological rolling CO/ethylene folds, at full available calibration coverage. Fixed-split budget experiments are secondary.
- Adaptation fitting/validation splits are identical across policies and group all offset windows by exposure. The reported budget includes held-out adaptation labels, not just fitting labels.
- Bootstrap intervals resample paired seed and fold MAEs with equal fold weights. They are conditional on observed test exposures. Overlapping training folds and only three/six held-out blocks limit population inference. Repeated predictions are not treated as independent exposures.
- Drift regression is conditional on oracle gas identity. The job-level test-range NMAE is retained as a diagnostic, but some gas/partition ranges are zero. Final exports therefore use each gas's historical concentration range in partitions 1–6 **only for reporting**, allowing macro-NMAE to weight all six gases equally. Historical reference labels never enter pretraining, fitting or selection. Both definitions and reference ranges are retained for traceability.
- One label/gas uses a predefined final-epoch checkpoint; there is no disjoint holdout at that budget. Budgets below 20 use fixed log scaling. The 20-label loss/scaling experiment retains the historical log standardization and compares fixed-log, fixed-linear Huber, and fixed-linear MAE. Fixed scaling uses 1000 ppm as a unit, not as a claimed physical maximum.
- Repeated concentration coordinates are audited separately from duplicated signals. Physical independence is not asserted without acquisition records.
- Evidence concerns reduced labeled-calibration requirements and same-system recalibration. It does not demonstrate reduced gas-generation costs or cross-device transfer.
- Missing private-array hardware/environment details are explicitly listed in the hardware record. Author confirmation is necessary before claiming those details are known.

## Artifacts

`revision_artifacts/environment/` preserves the initial commit, dirty-worktree status, code, earlier result JSON/CSV files, original manuscript DOCX, extracted PDFs, runtime packages, and source hashes. Git tag `major_revision_start` marks the initial committed state; the copied files also preserve uncommitted source code/results.

The first smoke run was archived outside the active repository during cleanup. Smoke epoch counts and seed counts are deliberately insufficient for scientific conclusions; new smoke runs must use a separate run ID.

The consistency checker fails for incomplete experiment suites, missing ten-seed evidence, changed code, prediction/metric discrepancies, exposure leakage, unsupported manuscript claims, or missing citation/claim provenance. Passing does not replace author review of hardware provenance and IEEE layout.
