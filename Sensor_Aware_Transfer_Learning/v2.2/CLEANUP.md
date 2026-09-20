# v2.2 cleanup — 2026-09-20

The active repository retains the completed v2.2 full revision, graphics, experiment code, source data, and numerical evidence. The original experiment code and protocol hashes are unchanged.

Removed material is recoverable at `E:/projects/ENose_cleanup_archive_2026-09-20`, outside the repository. This includes uncommitted older work. [cleanup_manifest.json](cleanup_manifest.json) lists all 114 moved paths; paths are relative to the repository root and retain that layout in the archive. Moving these files reduces the active project size but does not reclaim disk space from the archive.

Removed categories:

- Previous research implementations, notebooks, result folders, manuscript drafts, and superseded graphics.
- Duplicate reconstruction and UCI submission packages; the NH3/H2 companion description is retained under `revision_artifacts/hardware/`.
- Bundled LibreOffice installation and profiles, old local Python dependencies, caches, and temporary files.
- The first smoke run, partial-run logs, superseded minimal-review outputs, and one-time shutdown/citation automation.

Retained dependencies:

- `2407/`: source NH3/H2 workbook and original description.
- `Hoi quy/ec_improvements/raw_sequences.npz`: hashed input cache used by the completed experiments. The unused 613 MiB `ethylene_CO.txt` source trace is in the recovery archive.
- `sensor_drift/`: original drift data and source archive.
- All 1,390 raw-response and 290 drift jobs, model checkpoints, export tables, final documents, and final graphics.
- Frozen environment and evidence snapshots, including historical results used to distinguish old and revised claims. These are provenance records, not maintained alternate versions.
- `scripts/build_minimal_revision_docx.py`: shared formatting/equation-preservation helpers imported by the full builder. Its legacy standalone entry point is not the supported workflow.
- All experiment modules in `code/`: the completed protocol fingerprints these files, and several historical-looking modules supply imported model/data functions.

The historical comparison CSV formerly inside the minimal-review package is now `revision_artifacts/environment/historical_multifold_recomputed_statistics.csv`; the full handoff builder uses that location. The original frozen script snapshots remain unchanged as records of how the delivered documents were produced.

Maintenance changes add a root entry point, focused requirements, a graphics guide and regeneration command, portable manuscript-render output paths, and ignores for local renderer installations. No scientific results or manuscript claims were changed.

The validated 30-reference full-revision delivery was restored from its archived ZIP after later active document copies failed the clean/highlighted structure and reviewer-table checks. Those later copies remain recoverable under `post_delivery_active_2026-09-20/` in the archive. The authoritative builder and verifier were promoted from the evidence snapshot. See [cleanup_validation.json](cleanup_validation.json) for final sizes and checks; all protocol, consistency, document, render, and graphics checks pass.
