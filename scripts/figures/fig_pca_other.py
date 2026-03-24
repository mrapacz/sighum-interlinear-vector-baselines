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
"""Figures: PCA scatter plots for non-English languages (4 small)."""

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


def main() -> None:
    apply_rc()
    hf_dir, figures_dir = resolve_paths()
    df, _, _ = load_data(hf_dir)

    for lang in LANGUAGE_ORDER:
        if lang == "eng":
            continue

        lang_df = df.filter(pl.col("language") == lang)
        lang_means = lang_df.group_by("translation_id").agg(
            pl.col("mode").first(),
        )
        lang_pca = lang_df.select(["translation_id", "key", "pca_x", "pca_y"]).join(
            lang_means.select(["translation_id", "mode"]),
            on="translation_id",
        )

        fig, ax = plt.subplots(figsize=(7, 6))

        shuffled = lang_pca.sample(
            fraction=1.0,
            shuffle=True,
            seed=42,
        ).to_pandas()
        colors = shuffled["mode"].map(dict(STRATEGY_COLORS))
        ax.scatter(
            shuffled["pca_x"],
            shuffled["pca_y"],
            c=colors,
            s=20,
            alpha=0.5,
        )
        for mode, color in STRATEGY_COLORS.items():
            ax.scatter([], [], c=color, s=20, alpha=0.5, label=mode)

        ax.axhline(0, color="k", linestyle="--", alpha=0.3, linewidth=0.5)
        ax.axvline(0, color="k", linestyle="--", alpha=0.3, linewidth=0.5)
        ax.set_xlabel("PC 1", fontsize=14)
        ax.set_ylabel("PC 2", fontsize=14)
        ax.legend(frameon=False, fontsize=11)

        save_figure(fig, figures_dir / f"pca_{lang}.pdf")


if __name__ == "__main__":
    main()
