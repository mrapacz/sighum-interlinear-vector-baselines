#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "polars>=1.0",
#     "numpy>=1.26",
#     "matplotlib>=3.8",
#     "seaborn>=0.13",
#     "scipy>=1.12",
#     "pyarrow>=15.0",
#     "loguru>=0.7",
# ]
# ///
"""Pairwise significance heatmaps — EN large left + 4 small right (horizontal)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matplotlib.patches import Patch

from figures import (
    HEATMAP_NS,
    HEATMAP_P001,
    HEATMAP_P01,
    HEATMAP_P05,
    ISO_LABELS,
    LANG_TITLE_FONTSIZE,
    LANGUAGE_ORDER,
    TEXT_RULE,
    apply_rc,
    draw_heatmap,
    load_data,
    pl,
    plt,
    resolve_paths,
    save_figure,
)

WIDTH_SCALE = 0.8
HEIGHT_SCALE = 0.5

# ── Assembled layout ratios ──────────────────────────────────
# Columns: EN | gutter | legend | gutter | small_left | small_gap | small_right
EN_RATIO = 44
GUTTER_LEFT = 4
LEGEND_RATIO = 6
GUTTER_RIGHT = 4
SMALL_COL = 22
SMALL_GAP = 2

# 2x2 grid spacing
HSPACE_2x2 = 0.05  # vertical gap between 2x2 rows
WSPACE = 0  # handled by ratio columns, keep at 0

# Legend swatch colors (matching HEATMAP_CMAP order)
_LEGEND_ITEMS = [
    (HEATMAP_NS, "n.s."),
    (HEATMAP_P05, "< 0.05"),
    (HEATMAP_P01, "< 0.01"),
    (HEATMAP_P001, "< 0.001"),
]


def _add_legend(ax: plt.Axes) -> None:
    """Draw a vertical legend in the given axes."""
    ax.axis("off")
    legend_elements = [
        Patch(facecolor=color, edgecolor=TEXT_RULE, label=label)
        for color, label in _LEGEND_ITEMS
    ]
    leg = ax.legend(
        handles=legend_elements,
        loc="center",
        ncol=1,
        frameon=False,
        fontsize=16,
        handlelength=1.8,
        handleheight=1.8,
        labelspacing=1.2,
    )
    leg.set_title(
        "Significance level\n(p-value)",
        prop={"size": 16, "weight": "bold"},
    )


def main() -> None:
    apply_rc()
    hf_dir, figures_dir = resolve_paths()
    df, _, _ = load_data(hf_dir)

    heatmap_dir = figures_dir / "figure-group-heatmaps-pairwise"
    heatmap_dir.mkdir(parents=True, exist_ok=True)

    # ── Individual subfigures ────────────────────────────────
    for lang in LANGUAGE_ORDER:
        is_eng = lang == "eng"
        fig, ax = plt.subplots(
            figsize=(6 * WIDTH_SCALE, 10 * HEIGHT_SCALE)
            if is_eng
            else (5 * WIDTH_SCALE, 5 * HEIGHT_SCALE),
        )
        lang_df = df.filter(pl.col("language") == lang)
        pct = draw_heatmap(
            ax,
            lang_df,
            tick_fontsize=11 if is_eng else 9,
        )
        title = (
            f"{ISO_LABELS[lang]} — {pct:.0f}% sig." if is_eng else f"{pct:.0f}% sig."
        )
        ax.set_title(title, fontsize=LANG_TITLE_FONTSIZE, fontweight="bold")
        save_figure(fig, heatmap_dir / f"heatmap_{lang}.pdf")

    # ── Assembled: EN | legend | 2x2 (horizontal) ────
    fig_asm = plt.figure(figsize=(20 * WIDTH_SCALE, 10 * HEIGHT_SCALE))
    gs = fig_asm.add_gridspec(
        2,
        7,
        width_ratios=[
            EN_RATIO,
            GUTTER_LEFT,
            LEGEND_RATIO,
            GUTTER_RIGHT,
            SMALL_COL,
            SMALL_GAP,
            SMALL_COL,
        ],
        hspace=HSPACE_2x2,
        wspace=WSPACE,
    )

    # EN: left column spanning both rows
    ax_eng = fig_asm.add_subplot(gs[:, 0])
    eng_df = df.filter(pl.col("language") == "eng")
    pct_eng = draw_heatmap(ax_eng, eng_df, tick_fontsize=11)
    ax_eng.set_title(
        f"English — {pct_eng:.0f}% significant (p < 0.001)",
        fontsize=LANG_TITLE_FONTSIZE,
        fontweight="bold",
    )

    # Legend: center column spanning both rows
    ax_legend = fig_asm.add_subplot(gs[:, 2])
    _add_legend(ax_legend)

    # 2x2 grid on the right — no tick labels, just title
    other_langs = [lang for lang in LANGUAGE_ORDER if lang != "eng"]
    positions = [(0, 4), (0, 6), (1, 4), (1, 6)]
    for lang, (row, col) in zip(other_langs, positions, strict=False):
        ax = fig_asm.add_subplot(gs[row, col])
        lang_df = df.filter(pl.col("language") == lang)
        pct = draw_heatmap(
            ax,
            lang_df,
            show_tick_labels=False,
        )
        ax.set_title(
            f"{ISO_LABELS[lang]} — {pct:.0f}%",
            fontsize=LANG_TITLE_FONTSIZE,
            fontweight="bold",
        )

    save_figure(fig_asm, figures_dir / "figure-heatmaps.pdf")


if __name__ == "__main__":
    main()
