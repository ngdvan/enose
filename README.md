# ENose v2.2

The maintained project is [Sensor-Aware Transfer Learning v2.2](Sensor_Aware_Transfer_Learning/v2.2/README_MAJOR_REVISION.md).

- [Full revision and author handoff](Sensor_Aware_Transfer_Learning/v2.2/author_review/full_revision_001/DETAILED_SUMMARY.md)
- [Clean manuscript (DOCX)](Sensor_Aware_Transfer_Learning/v2.2/author_review/full_revision_001/IEEE_Full_Revision_Clean.docx)
- [Clean manuscript (PDF)](Sensor_Aware_Transfer_Learning/v2.2/author_review/full_revision_001/IEEE_Full_Revision_Clean.pdf)
- [Graphics and regeneration](Sensor_Aware_Transfer_Learning/v2.2/GRAPHICS.md)
- [Bilingual manuscript figures](Sensor_Aware_Transfer_Learning/v2.2/figure/README.md)
- [Cleanup record](Sensor_Aware_Transfer_Learning/v2.2/CLEANUP.md)

Only v2.2 is maintained. The `2407/`, `Hoi quy/`, and `sensor_drift/` directories retain source data at the paths recorded by the completed experiments. They are data dependencies, not alternate implementations. `Hoi quy/` now contains only the frozen response cache used by v2.2; its unused 613 MiB text source was archived. The frozen experiment code, jobs, checkpoints, exports, and evidence remain available for verification and reproduction.

Install the focused requirements with `python -m pip install -r Sensor_Aware_Transfer_Learning/v2.2/requirements.txt`. For GPU training, install a compatible CUDA-enabled PyTorch build separately; the original environment is recorded under `revision_artifacts/environment/`.

Run from this repository root:

```powershell
python Sensor_Aware_Transfer_Learning/v2.2/scripts/test_revision_protocol.py
python Sensor_Aware_Transfer_Learning/v2.2/scripts/check_paper_consistency.py --run-id major_revision_001
python Sensor_Aware_Transfer_Learning/v2.2/scripts/verify_full_revision.py
python Sensor_Aware_Transfer_Learning/v2.2/scripts/check_full_revision_render.py
```
