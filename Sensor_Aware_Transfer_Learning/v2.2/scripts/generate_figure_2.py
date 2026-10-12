"""Draw manuscript Figure 2 independently (Vietnamese labels).

Requires: python -m pip install matplotlib numpy pillow
Run: python generate_figure_2.py
No manuscript, experiment data, or other project scripts are required.
Edit SETTINGS below and the drawing function to customize the figure.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch, Rectangle
import numpy as np
from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
VN = SCRIPT_DIR / "generated_manuscript_figures" / "vn"

# Sizes are in inches; DPI controls the PNG pixel resolution.
# Defaults preserve the original manuscript dimensions.
SETTINGS = {
    "size_scale": 1.0,
    "font_scale": 1.0,
    "background": "white",
    "color_replacements": {},  # e.g. {"#24476b": "#305080"}
    "extra_formats": [],  # e.g. ["svg", "pdf"]
    "figures": {
        "figure_02_evaluation_protocol.png": {
            "size_inches": [13.84, 4.8133333333333335],
            "dpi": 300,
            "metadata_dpi": 600,
        }
    },
}

BLUE = "#24476B"
GREEN = "#006B4F"
AMBER = "#8B5200"
RED = "#B2182B"

def set_png_dpi(path: Path, dpi: int) -> None:
    """Update print-resolution metadata without changing pixel dimensions."""
    with Image.open(path) as image:
        image.save(path, dpi=(dpi, dpi))


def vietnamese_figure_2() -> None:
    width, height, dpi = 4152, 1444, 300
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"]})
    fig = plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi, facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 30)
    ax.axis("off")
    rows = [
        ("(a)  NH$_3$/H$_2$  (dữ liệu riêng, chuỗi thời gian thô)", 23.0, (66.7, 16.7, 16.6), ("P1–P4", "P5", "P6")),
        ("(b)  Hỗn hợp khí động  (CO / etylen, chuỗi thời gian thô)", 14.1, (60.0, 20.0, 20.0), ("P1–P3", "P4", "P5")),
        ("(c)  Độ trôi cảm biến  (36 tháng, đặc trưng thiết kế)", 5.2, (60.0, 10.0, 30.0), ("P1–P6", "P7", "P8–P10")),
    ]
    colors = ("#178B62", "#E8A600", "#CB402B")
    names = ("Tiền huấn luyện", "Thích nghi", "Kiểm thử")
    for title, y, widths, partitions in rows:
        ax.text(0.4, y + 5.2, title, fontsize=12.2, fontweight="bold", va="center")
        x = 0.5
        for w, color, name, part in zip(widths, colors, names, partitions):
            ax.add_patch(Rectangle((x, y), w - 0.2, 4.4, facecolor=color, edgecolor="white", linewidth=1.0))
            ax.text(x + (w - 0.2) / 2, y + 2.7, name, color="white", ha="center", va="center", fontsize=11.2, fontweight="bold")
            ax.text(x + (w - 0.2) / 2, y + 1.0, part, color="white", ha="center", va="center", fontsize=9.2)
            x += w
        barrier = 0.5 + widths[0] + widths[1]
        ax.plot([barrier, barrier], [y - 0.55, y + 5.0], color="#8B0000", linestyle="--", linewidth=2.0)
    ax.text(83.3, 29.1, "ranh giới chống rò rỉ", color="#8B0000", fontsize=9.4, ha="right")
    handles = [
        Patch(facecolor=colors[0], label="Tiền huấn luyện không nhãn"),
        Patch(facecolor=colors[1], label="Thích nghi có nhãn"),
        Patch(facecolor=colors[2], label="Tập kiểm thử không can thiệp"),
        Line2D([], [], color="#8B0000", linestyle="--", linewidth=2.0, label="Ranh giới chống rò rỉ"),
    ]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.005), ncol=4, frameon=False, fontsize=8.8, handlelength=1.4, columnspacing=1.15)
    target = VN / "figure_02_evaluation_protocol.png"
    save_figure(fig, target, dpi, 600)
    plt.close(fig)


def save_figure(fig, target: Path, default_dpi: int, metadata_dpi=None) -> None:
    """Apply editable settings consistently to all redrawn figures."""
    from matplotlib.text import Text
    options = SETTINGS.get("figures", {}).get(target.name, {})
    scale = options.get("size_scale", SETTINGS.get("size_scale", 1.0))
    fig.set_size_inches(np.asarray(options.get("size_inches", fig.get_size_inches())) * scale)
    font_scale = options.get("font_scale", SETTINGS.get("font_scale", 1.0))
    font_family = SETTINGS.get("font_family")
    colors = SETTINGS.get("color_replacements", {})
    for artist in fig.findobj():
        if isinstance(artist, Text):
            artist.set_fontsize(artist.get_fontsize() * font_scale)
            if font_family:
                artist.set_fontfamily(font_family)
        for attribute in ("color", "facecolor", "edgecolor"):
            getter = getattr(artist, "get_" + attribute, None)
            setter = getattr(artist, "set_" + attribute, None)
            if getter and setter:
                value = getter()
                try:
                    key = matplotlib.colors.to_hex(value).lower()
                except (ValueError, TypeError):
                    continue
                if key in colors:
                    setter(colors[key])
    dpi = options.get("dpi", SETTINGS.get("dpi", default_dpi))
    fig.savefig(target, dpi=dpi, facecolor=SETTINGS.get("background", "white"))
    if metadata_dpi is not None:
        set_png_dpi(target, options.get("metadata_dpi", dpi if "dpi" in options or "dpi" in SETTINGS else metadata_dpi))
    for extension in SETTINGS.get("extra_formats", []):
        if extension not in ("svg", "pdf"):
            raise ValueError("extra_formats supports only svg and pdf")
        fig.savefig(target.with_suffix("." + extension), facecolor=SETTINGS.get("background", "white"))


def main() -> None:
    global VN
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=VN)
    parser.add_argument("--dpi", type=int, help="Override PNG rendering DPI")
    parser.add_argument("--size", type=float, nargs=2, metavar=("WIDTH", "HEIGHT"), help="Figure size in inches")
    parser.add_argument("--font-scale", type=float, help="Multiply all font sizes")
    parser.add_argument("--format", choices=("svg", "pdf"), action="append", default=[], help="Also export a vector file; may be repeated")
    args = parser.parse_args()
    if args.dpi is not None and args.dpi <= 0:
        parser.error("--dpi must be positive")
    if args.size is not None and any(value <= 0 for value in args.size):
        parser.error("--size values must be positive")
    if args.font_scale is not None and args.font_scale <= 0:
        parser.error("--font-scale must be positive")
    VN = args.output_dir.resolve()
    VN.mkdir(parents=True, exist_ok=True)
    options = next(iter(SETTINGS["figures"].values()))
    if args.dpi is not None:
        options["dpi"] = args.dpi
        options["metadata_dpi"] = args.dpi
    if args.size is not None:
        options["size_inches"] = args.size
    if args.font_scale is not None:
        SETTINGS["font_scale"] = args.font_scale
    SETTINGS["extra_formats"] = list(dict.fromkeys(SETTINGS["extra_formats"] + args.format))
    vietnamese_figure_2()
    print(f"Generated Figure 2 in {VN}")


if __name__ == "__main__":
    main()
