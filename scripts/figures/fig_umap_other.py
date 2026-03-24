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
#     "umap-learn>=0.5",
# ]
# ///
"""Figures: UMAP scatter plots for non-English languages (4 small)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from figures import (
    LANGUAGE_ORDER,
    STRATEGY_COLORS,
    apply_rc,
    load_data,
    pl,
    plt,
    resolve_paths,
    save_figure,
)
from figures.fig_umap_eng import compute_umap_for_lang


def main() -> None:
    apply_rc()
    hf_dir, figures_dir = resolve_paths()
    df, _, _ = load_data(hf_dir)

    for lang in LANGUAGE_ORDER:
        if lang == "eng":
            continue

        df_umap = compute_umap_for_lang(hf_dir, lang)

        lang_means = (
            df.filter(pl.col("language") == lang)
            .group_by("translation_id")
            .agg(pl.col("mode").first())
        )
        lang_umap = df_umap.join(
            lang_means.select(["translation_id", "mode"]),
            on="translation_id",
        )

        fig, ax = plt.subplots(figsize=(7, 6))

        shuffled = lang_umap.sample(
            fraction=1.0,
            shuffle=True,
            seed=42,
        ).to_pandas()
        colors = shuffled["mode"].map(dict(STRATEGY_COLORS))
        ax.scatter(
            shuffled["umap_x"],
            shuffled["umap_y"],
            c=colors,
            s=20,
            alpha=0.5,
        )
        for mode, color in STRATEGY_COLORS.items():
            ax.scatter([], [], c=color, s=20, alpha=0.5, label=mode)

        ax.set_xlabel("UMAP 1", fontsize=14)
        ax.set_ylabel("UMAP 2", fontsize=14)
        ax.legend(frameon=False, fontsize=11)

        save_figure(fig, figures_dir / f"umap_{lang}.pdf")


if __name__ == "__main__":
    main()
