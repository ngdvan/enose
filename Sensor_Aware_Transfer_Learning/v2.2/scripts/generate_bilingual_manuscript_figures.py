"""Export exact English manuscript figures and matching Vietnamese versions.

English PNG files are copied byte-for-byte from the authoritative clean DOCX.
Vietnamese figures preserve the data, colors, panel order, geometry, and pixel
dimensions while translating only visible prose labels.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch, Rectangle
import numpy as np
import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "author_review/full_revision_001/IEEE_Full_Revision_Clean.docx"
OUT = ROOT / "figure"
EN = OUT / "en"
VN = OUT / "vn"
RUN = ROOT / "revision_artifacts/runs/major_revision_001"
EVIDENCE = ROOT / "author_review/full_revision_001/evidence/exports"

BLUE = "#24476B"
GREEN = "#006B4F"
AMBER = "#8B5200"
RED = "#B2182B"

MEDIA = {
    "figure_01_pipeline.png": "word/media/image3.png",
    "figure_02_evaluation_protocol.png": "word/media/image4.png",
    "figure_03_pretraining_loss.png": "word/media/image5.png",
    "figure_04_prediction_scatter.png": "word/media/image6.png",
}

CAPTIONS = {
    "figure_01_pipeline.png": {
        "en": "Full sensor-aware pretraining and adaptation pipeline.",
        "vn": "Quy trình tiền huấn luyện và thích nghi đầy đủ có nhận biết cảm biến.",
    },
    "figure_02_evaluation_protocol.png": {
        "en": "Leakage-controlled secondary fixed splits and chronological drift roles; the primary multi-fold protocols are specified in Section IV.",
        "vn": "Các phép chia cố định thứ cấp có kiểm soát rò rỉ và vai trò theo thời gian trong đánh giá độ trôi; các giao thức đa nếp chính được trình bày trong Mục IV.",
    },
    "figure_03_pretraining_loss.png": {
        "en": "Reconstruction loss over 10 seeds: blue line, mean; orange band, mean ± one seed SD. Raw-response pretraining uses 60 epochs; descriptor pretraining uses 40.",
        "vn": "Mất mát tái tạo trên 10 hạt giống: đường xanh là trung bình; dải cam là trung bình ± một độ lệch chuẩn giữa các hạt giống. Tiền huấn luyện đáp ứng thô dùng 60 vòng; tiền huấn luyện đặc trưng dùng 40 vòng.",
    },
    "figure_04_prediction_scatter.png": {
        "en": "Secondary full-budget predictions from all 10 seeds: gray circles, Scratch; blue squares, Frozen; orange triangles, Fine-tuned. Points repeat test exposures across seeds; the dashed line is identity, not a fitted trend.",
        "vn": "Dự đoán thứ cấp ở toàn bộ ngân sách từ cả 10 hạt giống: hình tròn xám là huấn luyện từ đầu; hình vuông xanh là đóng băng; tam giác cam là tinh chỉnh. Các điểm lặp lại lần phơi nhiễm kiểm thử theo hạt giống; đường đứt nét là đường đồng nhất, không phải xu hướng khớp dữ liệu.",
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def set_png_dpi(path: Path, dpi: int) -> None:
    """Update print-resolution metadata without changing pixel dimensions."""
    with Image.open(path) as image:
        image.save(path, dpi=(dpi, dpi))


def exact_english_exports() -> None:
    EN.mkdir(parents=True, exist_ok=True)
    with ZipFile(DOCX) as archive:
        for output_name, media_name in MEDIA.items():
            (EN / output_name).write_bytes(archive.read(media_name))


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
    fig.savefig(target, dpi=300, facecolor="white")
    plt.close(fig)
    set_png_dpi(target, 600)


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
    fig.savefig(target, dpi=dpi, facecolor="white")
    plt.close(fig)
    set_png_dpi(target, 600)


def vietnamese_figure_3() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "DejaVu Sans"],
            "font.size": 8,
            "axes.titlesize": 9,
            "axes.labelsize": 8,
            "legend.fontsize": 7.2,
        }
    )
    fig, axes = plt.subplots(3, 1, figsize=(3.45, 4.2))
    for ax, title, pattern in zip(
        axes,
        ["NH3/H2", "CO/etylen", "Độ trôi cảm biến"],
        ["nh3_h2_f0_early_s*_full.json", "co_ethylene_f0_early_s*_full.json", "drift_s*.json"],
    ):
        histories = np.array([json.loads(path.read_text())["loss"] for path in sorted((RUN / "checkpoints").glob(pattern))])
        assert len(histories) == 10
        x = np.arange(1, histories.shape[1] + 1)
        mean = histories.mean(0)
        sd = histories.std(0, ddof=1)
        ax.fill_between(x, mean - sd, mean + sd, facecolor="#E69F00", alpha=0.68, edgecolor="#B56B00", linewidth=0.55, zorder=2)
        ax.plot(x, mean, color="#164B75", linewidth=1.05, zorder=3)
        ax.set(title=title, xlabel="Vòng huấn luyện", ylabel="Hàm mất mát")
        ax.grid(alpha=0.14, zorder=0)
        ax.tick_params(labelsize=7.5)
    handles = [
        Line2D([], [], color="#164B75", lw=1.4, label="Trung bình"),
        Patch(facecolor="#E69F00", edgecolor="#B56B00", alpha=0.68, label="Trung bình ± 1 ĐLC"),
    ]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0), ncol=2, frameon=False, handlelength=2, handleheight=1.15, prop={"size": 7.2, "weight": "bold"})
    fig.tight_layout(pad=0.65, rect=[0, 0.065, 1, 1])
    fig.savefig(VN / "figure_03_pretraining_loss.png", dpi=400, facecolor="white")
    plt.close(fig)


def vietnamese_figure_4() -> None:
    predictions = pd.read_csv(EVIDENCE / "predictions/raw_response_predictions.csv")
    fig, axes = plt.subplots(2, 2, figsize=(3.45, 3.55))
    gases = ["NH3", "H2", "CO", "Ethylene"]
    titles = ["NH3", "H2", "CO", "Etylen"]
    policies = ["scratch", "frozen", "fine_tuned"]
    colors = ["#555555", "#0072B2", "#D55E00"]
    markers = ["o", "s", "^"]
    for ax, gas, title in zip(axes.flat, gases, titles):
        data = predictions[(predictions.gas == gas) & (predictions.fold == 0) & (predictions.design == "farthest") & (predictions.window == "early")]
        data = data[(data.budget == data.budget.max()) & data.policy.isin(policies)]
        for policy, color, marker in zip(policies, colors, markers):
            rows = data[data.policy == policy]
            ax.scatter(rows.true, rows.prediction, s=4, alpha=0.42, color=color, marker=marker, linewidths=0, rasterized=True)
        limit = 20 if gas == "Ethylene" else 533.33 if gas == "CO" else 500
        ax.plot([0, limit], [0, limit], "k--", lw=0.7)
        ax.set(title=title, xlabel="Tham chiếu (ppm)", ylabel="Dự đoán (ppm)", xlim=(0, limit), ylim=(0, limit))
        ax.tick_params(labelsize=6.5)
    labels = ["Từ đầu", "Đóng băng", "Tinh chỉnh"]
    handles = [Line2D([], [], linestyle="none", marker=marker, markersize=7, markerfacecolor=color, markeredgecolor=color, label=label) for label, color, marker in zip(labels, colors, markers)]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.005), ncol=3, frameon=True, edgecolor="#777777", framealpha=1, handlelength=0.75, handletextpad=0.3, columnspacing=0.65, borderpad=0.5, prop={"size": 6.7, "weight": "bold"})
    fig.tight_layout(pad=0.55, rect=[0, 0.10, 1, 1])
    fig.savefig(VN / "figure_04_prediction_scatter.png", dpi=400, facecolor="white")
    plt.close(fig)


def write_manifest() -> None:
    items = []
    for language, folder in [("en", EN), ("vn", VN)]:
        for name in MEDIA:
            path = folder / name
            with Image.open(path) as image:
                size = list(image.size)
                dpi = list(image.info.get("dpi", ()))
            items.append(
                {
                    "language": language,
                    "file": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "pixels": size,
                    "dpi_metadata": dpi,
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                    "caption": CAPTIONS[name][language],
                    "english_source": "byte-for-byte DOCX media export" if language == "en" else "translated redraw with unchanged scientific data and manuscript geometry",
                }
            )
    (OUT / "manifest.json").write_text(json.dumps({"source_manuscript": str(DOCX.relative_to(ROOT)).replace("\\", "/"), "figures": items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    EN.mkdir(parents=True, exist_ok=True)
    VN.mkdir(parents=True, exist_ok=True)
    exact_english_exports()
    vietnamese_figure_1()
    vietnamese_figure_2()
    vietnamese_figure_3()
    vietnamese_figure_4()
    write_manifest()
    print(f"Generated bilingual manuscript figures in {OUT}")


if __name__ == "__main__":
    main()
