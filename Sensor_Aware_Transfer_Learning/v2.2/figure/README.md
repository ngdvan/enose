# Bilingual manuscript figures

This folder contains the four figures from the authoritative v2.2 clean manuscript.

- `en/`: English PNG assets extracted byte-for-byte from the DOCX. These are the exact images embedded in the manuscript.
- `vn/`: Vietnamese editions with the same scientific data, colors, panel order, axes, geometry, and pixel dimensions. Only visible prose labels are translated.
- `manifest.json`: dimensions, hashes, bilingual captions, and source information.

All files are publication-resolution PNGs. Figures 1 and 2 retain their manuscript dimensions of 7419 × 2444 and 4152 × 1444 pixels. Figures 3 and 4 retain their 400 dpi manuscript dimensions of 1380 × 1680 and 1380 × 1420 pixels.

Regenerate the complete folder from the repository root:

```powershell
python Sensor_Aware_Transfer_Learning/v2.2/scripts/generate_bilingual_manuscript_figures.py
```

The English regeneration source is `author_review/full_revision_001/IEEE_Full_Revision_Clean.docx`. The plotted Vietnamese figures use the same completed checkpoint histories and prediction CSV as the manuscript.
