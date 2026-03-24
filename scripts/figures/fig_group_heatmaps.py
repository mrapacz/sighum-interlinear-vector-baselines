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
"""Group-level significance heatmaps (strategy x strategy, 5 langs, subfigures + assembled)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import seaborn as sns
from scipy.stats import mannwhitneyu

from figures import (
    HEATMAP_CMAP,
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

# Short labels for compact 4x4 cells
_SHORT = {"Literal": "Lit", "Formal": "Form", "Dynamic": "Dyn", "Paraphrase": "Para"}


def _draw_group_heatmap(ax: plt.Axes, lang_grp: pl.DataFrame) -> None:
    """Draw a strategy-group significance heatmap on the given axes."""
    modes = [m for m in STRATEGY_ORDER if m in lang_grp["mode"].to_list()]
    dists_map = dict(zip(lang_grp["mode"], lang_grp["dists"], strict=False))
    n = len(modes)
    p_matrix = np.full((n, n), np.nan)

    for i, mi in enumerate(modes):
        for j, mj in enumerate(modes):
            if i == j:
                continue
            _, p_raw = mannwhitneyu(dists_map[mi], dists_map[mj], alternative="less")
            p_matrix[i, j] = p_raw

    n_comp = n * (n - 1)
    p_adj = np.where(np.isnan(p_matrix), np.nan, np.minimum(p_matrix * n_comp, 1.0))

    annot_arr = np.where(
        np.isnan(p_adj),
        "",
        np.where(
            p_adj < 0.001,
            "***",
            np.where(p_adj < 0.01, "**", np.where(p_adj < 0.05, "*", "")),
        ),
    )

    color_matrix = np.where(
        np.isnan(p_adj),
        np.nan,
        np.where(
            p_adj < 0.001,
            0,
            np.where(p_adj < 0.01, 1, np.where(p_adj < 0.05, 2, 3)),
        ),
    )

    short_labels = [_SHORT.get(m, m) for m in modes]
    sns.heatmap(
        color_matrix,
        ax=ax,
        xticklabels=short_labels,
        yticklabels=short_labels,
        annot=annot_arr,
        fmt="",
        annot_kws={"fontsize": 9},
        cmap=HEATMAP_CMAP,
        vmin=0,
        vmax=3,
        square=True,
        cbar=False,
    )
    ax.tick_params(labelsize=10)


def main() -> None:
    apply_rc()
    hf_dir, figures_dir = resolve_paths()
    df, _, _ = load_data(hf_dir)

    group_dir = figures_dir / "figure-group-heatmaps"
    group_dir.mkdir(parents=True, exist_ok=True)

    chapter_by_lang_mode = (
        df.filter(pl.col("mode").is_not_null() & pl.col("mode").is_in(STRATEGY_ORDER))
        .group_by("language", "mode")
        .agg(pl.col("dist_interlinear").implode().alias("dists"))
    )

    # ── Individual subfigures ────────────────────────────────
    for lang in LANGUAGE_ORDER:
        fig, ax = plt.subplots(figsize=(4, 4))
        lang_grp = chapter_by_lang_mode.filter(pl.col("language") == lang)
        _draw_group_heatmap(ax, lang_grp)
        ax.set_title(ISO_LABELS[lang], fontsize=LANG_TITLE_FONTSIZE, fontweight="bold")
        save_figure(fig, group_dir / f"group_heatmap_{lang}.pdf")

    # ── Assembled: 5 languages in a row ──────────────────────
    fig_asm, axes = plt.subplots(1, 5, figsize=(22, 4.5))
    for ax, lang in zip(axes, LANGUAGE_ORDER, strict=False):
        lang_grp = chapter_by_lang_mode.filter(pl.col("language") == lang)
        _draw_group_heatmap(ax, lang_grp)
        ax.set_title(ISO_LABELS[lang], fontsize=LANG_TITLE_FONTSIZE, fontweight="bold")

    save_figure(fig_asm, figures_dir / "figure-group-heatmaps.pdf")


if __name__ == "__main__":
    main()
