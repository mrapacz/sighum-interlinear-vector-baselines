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
"""Figure: English PCA scatter plot with FNV / OJB ellipses."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matplotlib.patches import Ellipse

from figures import (
    ACCENT_PURPLE,
    STRATEGY_COLORS,
    apply_rc,
    load_data,
    pl,
    plt,
    resolve_paths,
    save_figure,
)

HIGHLIGHT_TRANSLATIONS = {
    "orthodox-jewish-bible": ("OJB", (0.08, 0.08)),
    "first-nations-version": ("FNV", (0.92, 0.08)),
}


def main() -> None:
    apply_rc()
    hf_dir, figures_dir = resolve_paths()
    df, _, _ = load_data(hf_dir)

    eng_df = df.filter(pl.col("language") == "eng")

    eng_means = eng_df.group_by("translation_id").agg(
        pl.col("dist_interlinear").mean().alias("mean_dist"),
        pl.col("mode").first(),
        pl.col("full_name").first(),
        pl.col("abbreviation").first(),
    )

    eng_pca = eng_df.select(["translation_id", "key", "pca_x", "pca_y"]).join(
        eng_means.select(["translation_id", "mode", "abbreviation", "full_name"]),
        on="translation_id",
    )

    fig, ax = plt.subplots(figsize=(10, 8))

    # Randomize drawing order
    shuffled = eng_pca.sample(fraction=1.0, shuffle=True, seed=42).to_pandas()
    colors = shuffled["mode"].map(dict(STRATEGY_COLORS))
    ax.scatter(shuffled["pca_x"], shuffled["pca_y"], c=colors, s=20, alpha=0.5)

    # Manual legend
    for mode, color in STRATEGY_COLORS.items():
        ax.scatter([], [], c=color, s=20, alpha=0.5, label=mode)

    # Ellipses
    for tid, (label, text_pos) in HIGHLIGHT_TRANSLATIONS.items():
        tid_data = eng_pca.filter(pl.col("translation_id") == tid)
        if tid_data.is_empty():
            continue
        xs = tid_data["pca_x"].to_numpy()
        ys = tid_data["pca_y"].to_numpy()
        cx, cy = xs.mean(), ys.mean()
        w = max(xs.std() * 4, 0.01)
        h = max(ys.std() * 4, 0.01)
        ax.add_patch(
            Ellipse(
                (cx, cy),
                width=w,
                height=h,
                fill=False,
                edgecolor=ACCENT_PURPLE,
                linewidth=2,
                linestyle="--",
                alpha=0.8,
            )
        )
        ax.annotate(
            label,
            xy=(cx, cy),
            xytext=text_pos,
            textcoords="axes fraction",
            fontsize=16,
            fontweight="bold",
            color=ACCENT_PURPLE,
            ha="center",
            va="center",
            arrowprops={
                "arrowstyle": "-|>",
                "color": ACCENT_PURPLE,
                "linewidth": 2,
                "connectionstyle": "arc3,rad=0.15",
            },
        )

    ax.axhline(0, color="k", linestyle="--", alpha=0.3, linewidth=0.5)
    ax.axvline(0, color="k", linestyle="--", alpha=0.3, linewidth=0.5)
    ax.set_xlabel("PC 1", fontsize=16)
    ax.set_ylabel("PC 2", fontsize=16)
    ax.legend(frameon=False, fontsize=13, loc="upper right")

    save_figure(fig, figures_dir / "pca_eng.pdf")


if __name__ == "__main__":
    main()
