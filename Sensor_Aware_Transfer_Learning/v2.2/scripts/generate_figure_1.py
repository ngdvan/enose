"""Draw manuscript Figure 1 independently (Vietnamese labels).

Requires: python -m pip install matplotlib numpy pillow
Run: python generate_figure_1.py
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
        "figure_01_pipeline.png": {
            "size_inches": [24.73, 8.146666666666667],
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


def setup_canvas(width: int, height: int, dpi: int = 300):
    fig = plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi, facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 33)
    ax.axis("off")
    return fig, ax


def rounded_box(ax, xy, width, height, text, face, edge, fontsize=10.5, weight="normal"):
    box = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.03,rounding_size=0.22",
        facecolor=face,
        edgecolor=edge,
        linewidth=1.4,
    )
    ax.add_patch(box)
    ax.text(
        xy[0] + width / 2,
        xy[1] + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        fontweight=weight,
        linespacing=1.12,
    )


def arrow(ax, start, end, color="#222222", mutation=15, width=1.2):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=mutation,
            linewidth=width,
            color=color,
            shrinkA=1,
            shrinkB=1,
        )
    )


def vietnamese_figure_1() -> None:
    width, height = 7419, 2444
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif"],
            "mathtext.fontset": "dejavuserif",
        }
    )
    fig, ax = setup_canvas(width, height)

    # (a) Structured masking: same curves, colors, masking geometry and ordering.
    ax.text(1.0, 26.3, "(a) Che có cấu trúc cho một lần phơi nhiễm", fontsize=18, fontweight="bold")
    left, right, bottom, top = 3.1, 21.4, 9.1, 23.8
    ax.plot([left, left], [bottom, top], color="#222222", lw=1.2)
    ax.plot([left, right], [bottom, bottom], color="#222222", lw=1.2)
    time = np.linspace(0, 1, 140)
    colors = ["#2166AC", "#4393C3", "#92C5DE", "#FDAE61", "#F46D43", "#B2182B"]
    offsets = np.linspace(10.1, 20.6, 6)
    for sensor, (offset, color) in enumerate(zip(offsets, colors), 1):
        response = 0.35 + 1.05 * (1 - np.exp(-5.2 * time)) + 0.14 * np.sin((sensor + 1) * np.pi * time)
        response *= 0.72 + sensor * 0.07
        ax.plot(left + time * (right - left), offset + response, color=color, lw=2.0, solid_capstyle="round")
        ax.text(left - 0.45, offset + 0.55, f"S{sensor}", ha="right", va="center", fontsize=13)
    x0, x1 = 10.4, 12.8
    ax.add_patch(Rectangle((x0, bottom), x1 - x0, top - bottom, facecolor=RED, alpha=0.16, edgecolor=RED, linewidth=1.0, hatch="////"))
    hidden_y = offsets[3] + 0.6
    ax.plot([left, right], [hidden_y, hidden_y], color=RED, lw=4.0, alpha=0.82, linestyle=(0, (2, 1)))
    ax.annotate("khoảng thời gian bị che", xy=((x0 + x1) / 2, 21.8), xytext=(7.7, 23.7), fontsize=13, color=RED, ha="center", arrowprops=dict(arrowstyle="->", lw=1.0, color=RED))
    ax.annotate("che toàn bộ kênh cảm biến", xy=(18.9, hidden_y), xytext=(17.7, 20.7), fontsize=13, color=RED, ha="center", arrowprops=dict(arrowstyle="->", lw=1.0, color=RED))
    ax.text((left + right) / 2, 7.8, "Mẫu thời gian, $t$", ha="center", fontsize=14)
    ax.text(1.15, (bottom + top) / 2, "Kênh cảm biến vật lý, $s$", rotation=90, ha="center", va="center", fontsize=14)

    arrow(ax, (23.2, 14.5), (27.5, 14.5), mutation=18, width=1.1)

    # (b) Sensor-aware encoder.
    ax.text(30.1, 24.6, "(b) Bộ mã hóa nhận biết cảm biến $f_\\theta$", fontsize=18, fontweight="bold", color=BLUE)
    items = [
        (30.3, 6.4, "Cửa sổ đa kênh\nđã che $\\widetilde{X}$", 14.0),
        (38.0, 5.5, "CNN dùng chung\ncho từng\ncảm biến", 12.5),
        (44.6, 5.5, "Gộp trung bình\n+ cực đại", 14.0),
        (51.2, 5.5, "Nhúng định danh\ncảm biến $e_s$", 14.0),
        (57.8, 4.2, "Attention\nliên cảm biến", 13.0),
    ]
    y, h = 12.0, 4.6
    for x, w, label, fontsize in items:
        rounded_box(ax, (x, y), w, h, label, "#E8F1FA", BLUE, fontsize=fontsize)
    for (x, w, _, _), (nx, _, _, _) in zip(items[:-1], items[1:]):
        arrow(ax, (x + w, y + h / 2), (nx, y + h / 2), BLUE, mutation=14, width=1.25)
    ax.text(46.2, 9.65, "Đầu ra: biểu diễn ngữ cảnh $Z$ cho mọi cảm biến vật lý", ha="center", fontsize=18, color=BLUE, fontweight="bold")

    # Fork to pretraining and adaptation branches.
    arrow(ax, (62.7, 14.4), (69.4, 22.1), mutation=18, width=1.0)
    arrow(ax, (62.7, 14.4), (69.4, 6.1), mutation=18, width=1.0)

    # (c) Self-supervised pretraining.
    ax.text(70.2, 31.2, "(c) Tiền huấn luyện tự giám sát không nhãn", fontsize=18, fontweight="bold", color=GREEN)
    rounded_box(ax, (70.5, 25.1), 6.3, 3.2, "Bộ mã hóa\n$f_\\theta(\\widetilde{X})$", "#DDF3E4", GREEN, 14)
    rounded_box(ax, (78.3, 25.1), 6.2, 3.2, "Bộ giải mã\ntái tạo", "#DDF3E4", GREEN, 14)
    rounded_box(ax, (86.0, 25.1), 9.4, 3.2, "Giá trị bị che\nđược tái tạo\n$\\widehat{X}_{mask}$", "#DDF3E4", GREEN, 13.5)
    arrow(ax, (76.8, 26.7), (78.3, 26.7), GREEN, mutation=14, width=1.25)
    arrow(ax, (84.5, 26.7), (86.0, 26.7), GREEN, mutation=14, width=1.25)
    ax.text(82.7, 23.3, "$\\mathcal{L}_{SSL}(X,\\widehat{X})$ cập nhật bộ mã hóa", ha="center", fontsize=13.5, color=GREEN)
    arrow(ax, (82.7, 22.9), (82.7, 21.4), GREEN, mutation=14, width=1.2)
    rounded_box(ax, (77.9, 18.2), 9.6, 3.0, "Trọng số tiền huấn luyện\ncó thể chuyển giao $\\theta_{SSL}$", "#CDEEDB", GREEN, 14)
    arrow(ax, (82.7, 18.1), (82.7, 16.5), mutation=16, width=1.0)

    # (d) Label-efficient adaptation.
    ax.text(71.3, 14.1, "(d) Thích nghi nồng độ tiết kiệm nhãn", fontsize=18, fontweight="bold", color=AMBER)
    ax.text(75.0, 12.1, "Tập hiệu chuẩn có nhãn nhỏ $\\mathcal{A}_K$", ha="center", fontsize=13, color=AMBER, fontweight="bold")
    arrow(ax, (75.0, 11.7), (75.0, 10.4), AMBER, mutation=14, width=1.2)
    rounded_box(ax, (71.4, 6.0), 8.0, 4.2, "Chính sách bộ mã hóa\nHuấn luyện từ đầu\nĐóng băng $\\theta_{SSL}$\nTinh chỉnh $\\theta_{SSL}$", "#FFF2CC", "#9A6700", 13)
    rounded_box(ax, (81.1, 6.5), 7.0, 3.2, "Đầu hồi quy\n$g_\\phi$", "#FCE4D6", "#A34100", 14)
    rounded_box(ax, (89.8, 6.5), 8.3, 3.2, "Đầu ra nồng độ\n$[\\widehat{c}_1,\\widehat{c}_2]$ ppm", "#FCE4D6", "#A34100", 13.5)
    arrow(ax, (79.4, 8.1), (81.1, 8.1), AMBER, mutation=14, width=1.2)
    arrow(ax, (88.1, 8.1), (89.8, 8.1), AMBER, mutation=14, width=1.2)
    ax.text(84.7, 3.6, "Huấn luyện không nhãn cung cấp $\\theta_{SSL}$ trước khi dùng nhãn nồng độ", ha="center", fontsize=13, color=BLUE, fontweight="bold")

    target = VN / "figure_01_pipeline.png"
    save_figure(fig, target, 300, 600)
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
    vietnamese_figure_1()
    print(f"Generated Figure 1 in {VN}")


if __name__ == "__main__":
    main()
