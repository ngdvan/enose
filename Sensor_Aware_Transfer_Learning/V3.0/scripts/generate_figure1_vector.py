"""Rebuild V3 Figure 1 as true vector SVG and a PNG preview.
Derived from v2.2/scripts/generate_figure_1.py; English labels match V3.
Run: python Sensor_Aware_Transfer_Learning/V3.0/scripts/generate_figure1_vector.py
"""
from __future__ import annotations
import argparse
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch, Rectangle
import numpy as np
from PIL import Image
BLUE = '#24476B'
GREEN = '#006B4F'
AMBER = '#8B5200'
RED = '#B2182B'

def setup_canvas(width: int, height: int, dpi: int=300):
    fig = plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi, facecolor='white')
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 33)
    ax.axis('off')
    return (fig, ax)

def rounded_box(ax, xy, width, height, text, face, edge, fontsize=10.5, weight='normal'):
    box = FancyBboxPatch(xy, width, height, boxstyle='round,pad=0.03,rounding_size=0.22', facecolor=face, edgecolor=edge, linewidth=1.4)
    ax.add_patch(box)
    ax.text(xy[0] + width / 2, xy[1] + height / 2, text, ha='center', va='center', fontsize=fontsize, fontweight=weight, linespacing=1.12)

def arrow(ax, start, end, color='#222222', mutation=15, width=1.2):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle='-|>', mutation_scale=mutation, linewidth=width, color=color, shrinkA=1, shrinkB=1))

def draw_figure_1() -> None:
    width, height = (7419, 2444)
    plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'], 'mathtext.fontset': 'dejavuserif'})
    fig, ax = setup_canvas(width, height)
    ax.text(1.0, 26.3, '(a) Structured masking of one exposure', fontsize=18, fontweight='bold')
    left, right, bottom, top = (3.1, 21.4, 9.1, 23.8)
    ax.plot([left, left], [bottom, top], color='#222222', lw=1.2)
    ax.plot([left, right], [bottom, bottom], color='#222222', lw=1.2)
    time = np.linspace(0, 1, 140)
    colors = ['#2166AC', '#4393C3', '#92C5DE', '#FDAE61', '#F46D43', '#B2182B']
    offsets = np.linspace(10.1, 20.6, 6)
    for sensor, (offset, color) in enumerate(zip(offsets, colors), 1):
        response = 0.35 + 1.05 * (1 - np.exp(-5.2 * time)) + 0.14 * np.sin((sensor + 1) * np.pi * time)
        response *= 0.72 + sensor * 0.07
        ax.plot(left + time * (right - left), offset + response, color=color, lw=2.0, solid_capstyle='round')
        ax.text(left - 0.45, offset + 0.55, f'S{sensor}', ha='right', va='center', fontsize=13)
    x0, x1 = (10.4, 12.8)
    ax.add_patch(Rectangle((x0, bottom), x1 - x0, top - bottom, facecolor=RED, alpha=0.16, edgecolor=RED, linewidth=1.0, hatch='////'))
    hidden_y = offsets[3] + 0.6
    ax.plot([left, right], [hidden_y, hidden_y], color=RED, lw=4.0, alpha=0.82, linestyle=(0, (2, 1)))
    ax.annotate('masked time span', xy=((x0 + x1) / 2, 21.8), xytext=(7.7, 23.7), fontsize=13, color=RED, ha='center', arrowprops=dict(arrowstyle='->', lw=1.0, color=RED))
    ax.annotate('complete sensor channel masked', xy=(18.9, hidden_y), xytext=(17.7, 20.7), fontsize=13, color=RED, ha='center', arrowprops=dict(arrowstyle='->', lw=1.0, color=RED))
    ax.text((left + right) / 2, 7.8, 'Time sample, $t$', ha='center', fontsize=14)
    ax.text(1.15, (bottom + top) / 2, 'Physical sensor channel, $s$', rotation=90, ha='center', va='center', fontsize=14)
    arrow(ax, (23.2, 14.5), (27.5, 14.5), mutation=18, width=1.1)
    ax.text(30.1, 24.6, '(b) Sensor-aware encoder $f_\\theta$', fontsize=18, fontweight='bold', color=BLUE)
    items = [(30.3, 6.4, 'Masked\nmultichannel\nwindow $\\widetilde{X}$', 14.0), (38.0, 5.5, 'Shared CNN\nper sensor', 12.5), (44.6, 5.5, 'Mean + max\npooling', 14.0), (51.2, 5.5, 'Sensor-ID\nembedding $e_s$', 14.0), (57.8, 4.2, 'Cross-\nsensor\nattention', 13.0)]
    y, h = (12.0, 4.6)
    for x, w, label, fontsize in items:
        rounded_box(ax, (x, y), w, h, label, '#E8F1FA', BLUE, fontsize=fontsize)
    for (x, w, _, _), (nx, _, _, _) in zip(items[:-1], items[1:]):
        arrow(ax, (x + w, y + h / 2), (nx, y + h / 2), BLUE, mutation=14, width=1.25)
    ax.text(46.2, 9.65, 'Output: contextual representation $Z$ for all physical sensors', ha='center', fontsize=18, color=BLUE, fontweight='bold')
    arrow(ax, (62.7, 14.4), (69.4, 22.1), mutation=18, width=1.0)
    arrow(ax, (62.7, 14.4), (69.4, 6.1), mutation=18, width=1.0)
    ax.text(70.2, 31.2, '(c) Unlabeled self-supervised pretraining', fontsize=18, fontweight='bold', color=GREEN)
    rounded_box(ax, (70.5, 25.1), 6.3, 3.2, 'Encoder\n$f_\\theta(\\widetilde{X})$', '#DDF3E4', GREEN, 14)
    rounded_box(ax, (78.3, 25.1), 6.2, 3.2, 'Reconstruction\ndecoder', '#DDF3E4', GREEN, 14)
    rounded_box(ax, (86.0, 25.1), 9.4, 3.2, 'Reconstructed\nmasked values\n$\\widehat{X}_{mask}$', '#DDF3E4', GREEN, 13.5)
    arrow(ax, (76.8, 26.7), (78.3, 26.7), GREEN, mutation=14, width=1.25)
    arrow(ax, (84.5, 26.7), (86.0, 26.7), GREEN, mutation=14, width=1.25)
    ax.text(82.7, 23.3, '$\\mathcal{L}_{SSL}(X,\\widehat{X})$ updates the encoder', ha='center', fontsize=13.5, color=GREEN)
    arrow(ax, (82.7, 22.9), (82.7, 21.4), GREEN, mutation=14, width=1.2)
    rounded_box(ax, (77.9, 18.2), 9.6, 3.0, 'Transferable output\npretrained weights $\\theta_{SSL}$', '#CDEEDB', GREEN, 14)
    arrow(ax, (82.7, 18.1), (82.7, 16.5), mutation=16, width=1.0)
    ax.text(71.3, 14.1, '(d) Label-efficient concentration adaptation', fontsize=18, fontweight='bold', color=AMBER)
    ax.text(75.0, 12.1, 'Small labeled calibration set $\\mathcal{A}_K$', ha='center', fontsize=13, color=AMBER, fontweight='bold')
    arrow(ax, (75.0, 11.7), (75.0, 10.4), AMBER, mutation=14, width=1.2)
    rounded_box(ax, (71.4, 6.0), 8.0, 4.2, 'Encoder policy\nScratch\nFrozen $\\theta_{SSL}$\nFine-tuned $\\theta_{SSL}$', '#FFF2CC', '#9A6700', 13)
    rounded_box(ax, (81.1, 6.5), 7.0, 3.2, 'Regression head\n$g_\\phi$', '#FCE4D6', '#A34100', 14)
    rounded_box(ax, (89.8, 6.5), 8.3, 3.2, 'Concentration output\n$[\\widehat{c}_1,\\widehat{c}_2]$ ppm', '#FCE4D6', '#A34100', 13.5)
    arrow(ax, (79.4, 8.1), (81.1, 8.1), AMBER, mutation=14, width=1.2)
    arrow(ax, (88.1, 8.1), (89.8, 8.1), AMBER, mutation=14, width=1.2)
    ax.text(84.7, 3.6, 'Unlabeled training supplies $\\theta_{SSL}$ before concentration labels are used', ha='center', fontsize=13, color=BLUE, fontweight='bold')
    target = VN / 'Figure1_vector.png'
    save_figure(fig, target, 300, 600)
    plt.close(fig)

VN = Path(__file__).resolve().parents[1] / "submission"

def save_figure(fig, target, dpi, metadata_dpi=None):
    from matplotlib.text import Text
    # Increase small body labels for print readability; preserve diagram geometry.
    for artist in fig.findobj(Text):
        if artist.get_fontsize() < 14:
            artist.set_fontsize(14)
    fig.savefig(target.with_suffix(".svg"), facecolor="white", bbox_inches="tight", pad_inches=0.12)
    fig.savefig(target, dpi=160, facecolor="white", bbox_inches="tight", pad_inches=0.12)

if __name__ == "__main__":
    VN.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"svg.fonttype": "none", "svg.hashsalt": "enose-v3-figure1", "font.family": "serif"})
    draw_figure_1()
