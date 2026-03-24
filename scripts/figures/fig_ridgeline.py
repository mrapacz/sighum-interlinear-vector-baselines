#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "polars>=1.0",
#     "numpy>=1.26",
#     "matplotlib>=3.8",
#     "scipy>=1.12",
#     "pyarrow>=15.0",
#     "loguru>=0.7",
#     "pandas",
# ]
# ///
"""Ridgeline (joy) plots — horizontal KDE per translation strategy group."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.stats import gaussian_kde

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from figures import (
    GRAPHITE,
    ISO_LABELS,
    LANG_TITLE_FONTSIZE,
    LANGUAGE_ORDER,
    STRATEGY_ORDER,
    apply_rc,
    load_data,
    pl,
    plt,
    resolve_paths,
    save_figure,
)

# Per-strategy fill colors: graphite with decreasing opacity
_RIDGE_ALPHAS = [0.85, 0.65, 0.45, 0.30]
# Actually same alpha seems better.
# _RIDGE_ALPHAS = [0.85, 0.85, 0.85, 0.85]


WIDTH_SCALE = 1
HEIGHT_SCALE = 0.5


def _draw_ridgeline(
    ax: plt.Axes,
    lang_pd,
    *,
    show_xlabel: bool = True,
    show_ylabel: bool = True,
) -> None:
    """Draw a ridgeline plot with one KDE ridge per strategy group."""
    n_groups = len(STRATEGY_ORDER)
    overlap = 0.55
    x_grid = np.linspace(
        lang_pd["dist_interlinear"].min(), lang_pd["dist_interlinear"].max(), 512
    )

    for i, strategy in enumerate(reversed(STRATEGY_ORDER)):
        subset = lang_pd[lang_pd["mode"] == strategy]["dist_interlinear"].values
        if len(subset) < 2:
            continue

        kde = gaussian_kde(subset, bw_method="scott")
        density = kde(x_grid)
        density = density / density.max()

        y_offset = i * (1 - overlap)

        ax.fill_between(
            x_grid,
            y_offset,
            y_offset + density,
            color=GRAPHITE,
            alpha=_RIDGE_ALPHAS[n_groups - 1 - i],
            linewidth=0,
        )
        ax.plot(x_grid, y_offset + density, color=GRAPHITE, linewidth=1.0)

    # Y-axis: strategy labels centered on each ridge
    yticks = [(n_groups - 1 - i) * (1 - overlap) + 0.3 for i in range(n_groups)]
    if show_ylabel:
        ax.set_yticks(yticks)
        ax.set_yticklabels(STRATEGY_ORDER, fontsize=16)
    else:
        ax.set_yticks([])

    ax.set_xlabel(
        r"$\|V_{\mathrm{intervention}}\|$" if show_xlabel else "",
        fontsize=16,
    )
    ax.set_xlim(x_grid[0], x_grid[-1])
    ax.set_ylim(0, (n_groups - 1) * (1 - overlap) + 1.15)
    ax.spines["left"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(left=False)
    ax.grid(axis="x", alpha=0.2, linewidth=0.4)
    ax.set_axisbelow(True)


def main() -> None:
    apply_rc()
    hf_dir, figures_dir = resolve_paths()
    df, _, _ = load_data(hf_dir)

    ridge_dir = figures_dir / "figure-group-ridgeline"
    ridge_dir.mkdir(parents=True, exist_ok=True)

    plot_df = df.filter(
        pl.col("mode").is_not_null() & pl.col("mode").is_in(STRATEGY_ORDER)
    )

    # ── Individual subfigures ────────────────────────────────
    for lang in LANGUAGE_ORDER:
        is_eng = lang == "eng"
        fig, ax = plt.subplots(
            figsize=(10 * WIDTH_SCALE, 5 * HEIGHT_SCALE)
            if is_eng
            else (8 * WIDTH_SCALE, 4 * HEIGHT_SCALE)
        )
        lang_pd = plot_df.filter(pl.col("language") == lang).to_pandas()
        _draw_ridgeline(ax, lang_pd)
        ax.set_title(ISO_LABELS[lang], fontsize=LANG_TITLE_FONTSIZE, fontweight="bold")
        save_figure(fig, ridge_dir / f"ridgeline_{lang}.pdf")

    # ── Assembled: EN large LEFT, gutter, 2x2 RIGHT (horizontal) ────
    fig_asm = plt.figure(figsize=(20 * WIDTH_SCALE, 10 * HEIGHT_SCALE))
    gs = fig_asm.add_gridspec(
        2,
        5,
        width_ratios=[44, 10, 22, 2, 22],
        hspace=0.08,
        wspace=0,
    )

    # EN: left column spanning both rows
    ax_eng = fig_asm.add_subplot(gs[:, 0])
    eng_pd = plot_df.filter(pl.col("language") == "eng").to_pandas()
    _draw_ridgeline(ax_eng, eng_pd)
    ax_eng.set_title("English", fontsize=LANG_TITLE_FONTSIZE, fontweight="bold")

    # 2x2 on the right — no labels
    other_langs = [lang for lang in LANGUAGE_ORDER if lang != "eng"]
    positions = [(0, 2), (0, 4), (1, 2), (1, 4)]
    for lang, (row, col) in zip(other_langs, positions, strict=False):
        ax = fig_asm.add_subplot(gs[row, col])
        lang_pd = plot_df.filter(pl.col("language") == lang).to_pandas()
        _draw_ridgeline(ax, lang_pd, show_xlabel=False, show_ylabel=False)
        ax.set_title(ISO_LABELS[lang], fontsize=LANG_TITLE_FONTSIZE, fontweight="bold")
        ax.set_xticklabels([])

    save_figure(fig_asm, figures_dir / "figure-ridgeline.pdf")


if __name__ == "__main__":
    main()
