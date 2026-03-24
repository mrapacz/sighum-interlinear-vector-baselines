#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "polars>=1.0",
#     "numpy>=1.26",
#     "scikit-learn>=1.4",
#     "pyarrow>=15.0",
#     "typer>=0.12",
#     "loguru>=0.7",
# ]
# ///
"""
Compute intervention vectors and PCA from raw embeddings.

Reads per-language chapter embeddings (Qwen3-Embedding-8B, 4096-dim)
assembled by ``00_fetch_data.py`` and computes:
1. Intervention vectors (translation − interlinear baseline)
2. Distances to interlinear (L2 norm)
3. PCA projections (2D)

Outputs:
- HF repo: intervention_by_chapter.parquet, intervention_summary.parquet
- GH repo: chapter_level_intervention.tsv, pca_projections.tsv, translations_metadata.tsv
"""

from pathlib import Path

import numpy as np
import polars as pl
import typer
from loguru import logger
from sklearn.decomposition import PCA

# Strategy order for consistent output
STRATEGY_ORDER = ["Literal", "Formal", "Dynamic", "Paraphrase"]
# Language order: lexicographical by full name (English, French, Italian, Polish, Spanish)
LANGUAGE_ORDER = ["eng", "fra", "ita", "pol", "spa"]

app = typer.Typer()


def get_interlinear_id(df: pl.DataFrame) -> str:
    """
    Identify the interlinear translation ID.

    Interlinears have 'interlinear' in their translation_id.
    """
    interlinear_ids = (
        df.filter(pl.col("translation_id").str.contains("interlinear"))[
            "translation_id"
        ]
        .unique()
        .to_list()
    )

    if len(interlinear_ids) == 0:
        raise ValueError("No interlinear translation found")

    if len(interlinear_ids) > 1:
        logger.warning(
            f"Multiple interlinear IDs found: {interlinear_ids}. Using first."
        )

    return interlinear_ids[0]


def process_language(lang: str, hf_dir: Path) -> tuple[pl.DataFrame, pl.DataFrame]:
    """
    Process a single language: compute intervention vectors and PCA.

    Args:
        lang: Language ISO code (e.g., 'eng', 'fra')
        hf_dir: Path to HuggingFace dataset directory

    Returns:
        (chapter_df, summary_df): Chapter-level and translation-level dataframes

    """
    logger.info(f"Processing {lang}...")

    # Load embeddings for this language
    embeddings_file = hf_dir / f"embeddings_{lang}.parquet"
    df_lang = pl.read_parquet(embeddings_file)

    logger.info(f"Loaded {len(df_lang)} embedding rows")

    # Identify interlinear
    interlinear_id = get_interlinear_id(df_lang)
    logger.info(f"Interlinear: {interlinear_id}")

    # Split into interlinear and other translations
    df_interlinear = df_lang.filter(pl.col("translation_id") == interlinear_id)
    df_others = df_lang.filter(pl.col("translation_id") != interlinear_id)

    if df_others.height == 0:
        logger.warning(f"No other translations found for {lang}")
        return None, None

    # Prepare reference (interlinear) vectors
    df_ref = df_interlinear.select(
        [
            pl.col("key"),
            pl.col("vector").alias("vector_interlinear"),
        ]
    )

    # Join translations with interlinear on chapter key
    df_joined = df_others.join(df_ref, on="key", how="inner")

    if df_joined.height == 0:
        logger.warning(f"No matching chapters found for {lang}")
        return None, None

    logger.info(f"Matched {len(df_joined)} chapter-translation pairs")

    # Convert to numpy arrays for computation
    vectors = np.stack(df_joined["vector"].to_numpy())
    vectors_ref = np.stack(df_joined["vector_interlinear"].to_numpy())

    # Compute intervention vectors
    intervention_vectors = vectors - vectors_ref

    # Compute distances (Euclidean norm)
    dist_interlinear = np.linalg.norm(intervention_vectors, axis=1)

    # PCA: fit on intervention vectors + zero vectors (for interlinear)
    # This ensures interlinear is at origin after recentering
    n_chapters = len(df_ref)
    n_dim = intervention_vectors.shape[1]

    interlinear_zeros = np.zeros((n_chapters, n_dim))
    combined_for_pca = np.vstack([intervention_vectors, interlinear_zeros])

    pca = PCA(n_components=2)
    pca.fit(combined_for_pca)

    # Transform intervention vectors
    pca_coords = pca.transform(intervention_vectors)

    # Transform zero vector (interlinear position)
    interlinear_pca = pca.transform(np.zeros((1, n_dim)))

    # Recenter so interlinear is at (0, 0)
    pca_coords = pca_coords - interlinear_pca

    logger.info(f"PCA explained variance: {pca.explained_variance_ratio_}")

    # Create chapter-level dataframe
    df_chapter = df_joined.select(["translation_id", "key"]).with_columns(
        [
            pl.lit(lang).alias("language"),
            pl.Series(name="dist_interlinear", values=dist_interlinear),
            pl.Series(name="pca_x", values=pca_coords[:, 0]),
            pl.Series(name="pca_y", values=pca_coords[:, 1]),
        ]
    )

    # Aggregate to translation-level summary
    df_summary = df_chapter.group_by("translation_id").agg(
        [
            pl.col("language").first(),
            pl.col("dist_interlinear").mean().alias("mean_dist_interlinear"),
            pl.col("dist_interlinear").std().alias("std_dist_interlinear"),
            pl.col("pca_x").mean().alias("pca_x"),
            pl.col("pca_y").mean().alias("pca_y"),
        ]
    )

    logger.info(
        f"Generated {len(df_chapter)} chapter rows, {len(df_summary)} translation rows"
    )

    return df_chapter, df_summary


@app.command()
def main(
    hf_dir: Path = typer.Option(
        None,
        help="Path to HuggingFace dataset directory",
    ),
    gh_data_dir: Path = typer.Option(
        None,
        help="Path to GitHub data output directory",
    ),
):
    """Compute intervention vectors and PCA from raw embeddings."""
    # Paths relative to script location
    script_dir = Path(__file__).parent

    if hf_dir is None:
        hf_dir = script_dir.parent / ".cache" / "hf-data"
    if gh_data_dir is None:
        gh_data_dir = script_dir.parent / "data"

    # Create output directories
    gh_data_dir.mkdir(parents=True, exist_ok=True)

    # Load metadata index
    logger.info("Loading metadata index...")
    index_file = hf_dir / "index.parquet"
    df_index = pl.read_parquet(index_file)

    logger.info(f"Loaded metadata for {len(df_index)} translations")

    # Process each language in lexicographical order (by full name)
    logger.info(f"Languages: {LANGUAGE_ORDER}")

    # Process each language
    chapter_results = []
    summary_results = []

    for lang in LANGUAGE_ORDER:
        df_chapter, df_summary = process_language(lang, hf_dir)

        if df_chapter is not None:
            chapter_results.append(df_chapter)
        if df_summary is not None:
            summary_results.append(df_summary)

    if not chapter_results:
        logger.error("No results generated!")
        return

    # Combine all languages
    logger.info("Combining results...")
    df_chapter_all = pl.concat(chapter_results)
    df_summary_all = pl.concat(summary_results)

    logger.info(
        f"Total: {len(df_chapter_all)} chapter rows, {len(df_summary_all)} translation rows"
    )

    # Output 1: HF repo - intervention_by_chapter.parquet
    hf_chapter_file = hf_dir / "intervention_by_chapter.parquet"
    df_chapter_all.write_parquet(hf_chapter_file)
    logger.info(f"Wrote {hf_chapter_file}")

    # Output 2: HF repo - intervention_summary.parquet
    hf_summary_file = hf_dir / "intervention_summary.parquet"
    df_summary_all.write_parquet(hf_summary_file)
    logger.info(f"Wrote {hf_summary_file}")

    # Join with metadata for GitHub exports
    df_chapter_meta = df_chapter_all.join(
        df_index.select(["translation_id", "language", "mode"]),
        on=["translation_id", "language"],
        how="left",
    )

    df_summary_meta = df_summary_all.join(
        df_index, on=["translation_id", "language"], how="left"
    )

    # Output 3: GH repo - chapter_level_intervention.tsv
    gh_chapter_file = gh_data_dir / "chapter_level_intervention.tsv"
    df_chapter_meta.select(
        [
            "language",
            "translation_id",
            pl.col("key").alias("chapter"),
            "mode",
            "dist_interlinear",
        ]
    ).sort(["language", "translation_id", "chapter"]).write_csv(
        gh_chapter_file, separator="\t"
    )
    logger.info(f"Wrote {gh_chapter_file}")

    # Output 4: GH repo - pca_projections.tsv
    gh_pca_file = gh_data_dir / "pca_projections.tsv"
    df_chapter_meta.select(
        [
            "language",
            "translation_id",
            pl.col("key").alias("chapter"),
            "pca_x",
            "pca_y",
            "mode",
        ]
    ).sort(["language", "translation_id", "chapter"]).write_csv(
        gh_pca_file, separator="\t"
    )
    logger.info(f"Wrote {gh_pca_file}")

    # Output 5: GH repo - translations_metadata.tsv
    gh_meta_file = gh_data_dir / "translations_metadata.tsv"
    df_summary_meta.select(
        [
            "language",
            "translation_id",
            "full_name",
            "abbreviation",
            "year",
            "mode",
        ]
    ).sort(["language", "translation_id"]).write_csv(gh_meta_file, separator="\t")
    logger.info(f"Wrote {gh_meta_file}")

    logger.info("Processing complete!")


if __name__ == "__main__":
    app()
