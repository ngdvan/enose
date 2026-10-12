# Independent diagram scripts

`generate_figure_1.py` draws the pipeline; `generate_figure_2.py` draws the evaluation protocol. Each script is self-contained: copy either Python file to another folder or computer and run it there. No experiment data, DOCX, style JSON, or project imports are needed. Labels are Vietnamese, matching the existing redraws.

Install dependencies once:

```powershell
python -m pip install matplotlib numpy pillow
```

Run from this folder:

```powershell
python generate_figure_1.py
python generate_figure_2.py
```

PNG files go to `generated_manuscript_figures/vn` beside the scripts by default. Paths do not depend on the working directory.

Customize `SETTINGS` near the top of either script: `size_inches`, rendering `dpi`, print `metadata_dpi`, `font_scale`, `font_family` (optional), `background`, `color_replacements`, and `extra_formats`. Edit the drawing function for labels, positions, box sizes, arrows, and individual text sizes. Figure 1 also exposes BLUE, GREEN, AMBER, RED color constants.

Command-line overrides:

```powershell
python generate_figure_1.py --size 18 6 --dpi 300 --font-scale 0.9 --format svg --output-dir ./my_figures
python generate_figure_2.py --size 12 4.2 --format pdf
```

Changing only `metadata_dpi` changes print metadata without changing pixels. Changing `size_inches` or rendering `dpi` changes pixel dimensions; tune `font_scale` after changing size to keep text comfortable.

`generate_bilingual_manuscript_figures.py` remains available for the full four-figure export and uses `manuscript_figure_data` and `manuscript_figure_style.json` beside it. Its English outputs are exact bundled manuscript PNGs, so drawing-style edits apply to Vietnamese redraws.
