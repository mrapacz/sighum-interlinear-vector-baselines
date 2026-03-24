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
"""Figure: English UMAP scatter plot with FNV / OJB ellipses."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from matplotlib.patches import Ellipse
from umap import UMAP

from figures import (
    ACCENT_PURPLE,
    STRATEGY_COLORS,
    apply_rc,
    load_data,
    logger,
    pl,
    plt,
    resolve_paths,
    save_figure,
)

HIGHLIGHT_TRANSLATIONS = {
    "orthodox-jewish-bible": ("OJB", (0.08, 0.08)),
    "first-nations-version": ("FNV", (0.92, 0.08)),
}


def compute_umap_for_lang(hf_dir, lang: str) -> pl.DataFrame:
    """Compute UMAP projection for a single language."""
    emb = pl.read_parquet(hf_dir / f"embeddings_{lang}.parquet")

    interlinear_id = (
        emb.filter(pl.col("translation_id").str.contains("interlinear"))[
            "translation_id"
        ]
        .unique()
        .to_list()[0]
    )
    df_ref = emb.filter(pl.col("translation_id") == interlinear_id).select(
        [pl.col("key"), pl.col("vector").alias("vector_interlinear")]
    )
    df_others = emb.filter(pl.col("translation_id") != interlinear_id)

    joined = df_others.join(df_ref, on="key", how="inner")
    vectors = np.stack(joined["vector"].to_numpy())
    vectors_ref = np.stack(joined["vector_interlinear"].to_numpy())
    intervention = vectors - vectors_ref

    n_chapters = len(df_ref)
    zeros = np.zeros((n_chapters, intervention.shape[1]))
    combined = np.vstack([intervention, zeros])

    reducer = UMAP(
        n_components=2,
        random_state=42,
        n_neighbors=15,
        min_dist=0.1,
    )
    all_coords = reducer.fit_transform(combined)

    umap_coords = all_coords[: len(intervention)]
    interlinear_centroid = all_coords[len(intervention) :].mean(axis=0)
    umap_coords = umap_coords - interlinear_centroid

    frame = joined.select(["translation_id", "key"]).with_columns(
        [
            pl.lit(lang).alias("language"),
            pl.Series(name="umap_x", values=umap_coords[:, 0]),
            pl.Series(name="umap_y", values=umap_coords[:, 1]),
        ]
    )
    logger.info(f"UMAP computed for {lang}: {frame.height} points")
    return frame


def main() -> None:
    apply_rc()
    hf_dir, figures_dir = resolve_paths()
    df, _, _ = load_data(hf_dir)

    df_umap = compute_umap_for_lang(hf_dir, "eng")

    eng_means = (
        df.filter(pl.col("language") == "eng")
        .group_by("translation_id")
        .agg(
            pl.col("mode").first(),
            pl.col("abbreviation").first(),
            pl.col("full_name").first(),
        )
    )

    eng_umap = df_umap.join(
        eng_means.select(["translation_id", "mode", "abbreviation", "full_name"]),
        on="translation_id",
    )

    fig, ax = plt.subplots(figsize=(10, 8))

    shuffled = eng_umap.sample(
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

    # Ellipses
    for tid, (label, text_pos) in HIGHLIGHT_TRANSLATIONS.items():
        tid_data = eng_umap.filter(pl.col("translation_id") == tid)
        if tid_data.is_empty():
            continue
        xs = tid_data["umap_x"].to_numpy()
        ys = tid_data["umap_y"].to_numpy()
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

    ax.set_xlabel("UMAP 1", fontsize=16)
    ax.set_ylabel("UMAP 2", fontsize=16)
    ax.legend(frameon=False, fontsize=13, loc="upper right")

    save_figure(fig, figures_dir / "umap_eng.pdf")


if __name__ == "__main__":
    main()
