#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "polars>=1.0",
#     "numpy>=1.26",
#     "matplotlib>=3.8",
#     "seaborn>=0.13",
#     "pyarrow>=15.0",
#     "loguru>=0.7",
# ]
# ///
"""Violin plots with graphite color, vertical orientation (subfigures + assembled)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import seaborn as sns

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


def _draw_violin(ax: plt.Axes, lang_pd, *, show_ylabel: bool = True) -> None:
    """Draw a single violin panel on the given axes."""
    sns.violinplot(
        data=lang_pd,
        x="mode",
        y="dist_interlinear",
        order=STRATEGY_ORDER,
        orient="v",
        ax=ax,
        inner="box",
        linewidth=0.8,
        color=GRAPHITE,
        saturation=0.7,
        cut=0,
    )
    ax.set_xlabel("")
    ax.set_ylabel(
        r"$\|V_{\mathrm{int}}\|$" if show_ylabel else "",
        fontsize=16,
    )
    ax.grid(axis="y", alpha=0.2, linewidth=0.4)
    ax.set_axisbelow(True)


def main() -> None:
    apply_rc()
    hf_dir, figures_dir = resolve_paths()
    df, _, _ = load_data(hf_dir)

    violin_dir = figures_dir / "figure-group-violins"
    violin_dir.mkdir(parents=True, exist_ok=True)

    plot_df = df.filter(
        pl.col("mode").is_not_null() & pl.col("mode").is_in(STRATEGY_ORDER)
    )

    # ── Individual subfigures ────────────────────────────────
    for lang in LANGUAGE_ORDER:
        is_eng = lang == "eng"
        fig, ax = plt.subplots(figsize=(8, 5) if is_eng else (6, 4))
        lang_pd = plot_df.filter(pl.col("language") == lang).to_pandas()
        _draw_violin(ax, lang_pd)
        ax.set_title(ISO_LABELS[lang], fontsize=LANG_TITLE_FONTSIZE, fontweight="bold")
        save_figure(fig, violin_dir / f"violin_{lang}.pdf")

    # ── Assembled: EN large LEFT, 2x2 RIGHT (horizontal) ────
    fig_asm = plt.figure(figsize=(20, 10))
    gs = fig_asm.add_gridspec(
        2,
        3,
        width_ratios=[1.2, 1, 1],
        hspace=0.08,
        wspace=0.08,
    )

    # EN: left column spanning both rows
    ax_eng = fig_asm.add_subplot(gs[:, 0])
    eng_pd = plot_df.filter(pl.col("language") == "eng").to_pandas()
    _draw_violin(ax_eng, eng_pd)
    ax_eng.set_title("English", fontsize=LANG_TITLE_FONTSIZE, fontweight="bold")

    # 2x2 on the right — no axis labels or tick labels
    other_langs = [lang for lang in LANGUAGE_ORDER if lang != "eng"]
    positions = [(0, 1), (0, 2), (1, 1), (1, 2)]
    for lang, (row, col) in zip(other_langs, positions, strict=False):
        ax = fig_asm.add_subplot(gs[row, col])
        lang_pd = plot_df.filter(pl.col("language") == lang).to_pandas()
        _draw_violin(ax, lang_pd, show_ylabel=False)
        ax.set_title(ISO_LABELS[lang], fontsize=LANG_TITLE_FONTSIZE, fontweight="bold")
        ax.set_xticklabels([])
        ax.set_yticklabels([])

    save_figure(fig_asm, figures_dir / "figure-violins.pdf")


if __name__ == "__main__":
    main()
