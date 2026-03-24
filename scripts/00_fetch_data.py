#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "huggingface-hub>=0.20",
#     "polars>=1.0",
#     "pyarrow>=15.0",
#     "pyyaml>=6.0",
#     "typer>=0.12",
#     "loguru>=0.7",
#     "tqdm>=4.66",
# ]
# ///
"""
Fetch 8B chapter-level embeddings from HuggingFace (mrapacz/targum-corpus).

Reads ``translations_manifest.yaml`` to determine which translations belong
to the experiment subset, downloads their per-translation parquet files from
the Hive-partitioned ``mrapacz/targum-corpus`` dataset, and assembles them
into per-language embeddings files for downstream processing by
``01_compute_vectors.py``.

Outputs (written to ``--cache-dir``, default ``.cache/hf-data/``):
  - ``embeddings_{lang}.parquet``  — columns: translation_id, key, vector
  - ``index.parquet``              — translation metadata
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import typer
import yaml
from huggingface_hub import hf_hub_download
from loguru import logger
from tqdm import tqdm

app = typer.Typer()

LANGUAGE_ORDER = ["eng", "fra", "ita", "pol", "spa"]


def load_manifest(manifest_path: Path) -> dict:
    """Load the translations manifest YAML."""
    with manifest_path.open() as f:
        return yaml.safe_load(f)


def download_translation(
    *,
    repo_id: str,
    model_dir: str,
    language: str,
    site: str,
    translation_id: str,
    granularity: str,
    cache_dir: Path,
) -> Path:
    """Download a single translation's embedding parquet from HF."""
    hf_path = (
        f"embeddings/{model_dir}"
        f"/language={language}"
        f"/site={site}"
        f"/translation={translation_id}"
        f"/granularity={granularity}"
        f"/data.parquet"
    )
    return Path(
        hf_hub_download(
            repo_id=repo_id,
            filename=hf_path,
            repo_type="dataset",
            local_dir=cache_dir / "_raw",
        )
    )


@app.command()
def main(
    cache_dir: Path = typer.Option(
        None,
        help="Local directory to store assembled output files",
    ),
    manifest: Path = typer.Option(
        None,
        help="Path to translations_manifest.yaml",
    ),
    force: bool = typer.Option(
        False,
        help="Re-download and reassemble even if output files exist",
    ),
    granularity: str = typer.Option(
        "chapter",
        help="Embedding granularity to fetch (chapter or verse)",
    ),
):
    """Fetch embeddings from mrapacz/targum-corpus and assemble per-language parquets."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    if cache_dir is None:
        cache_dir = project_root / ".cache" / "hf-data"
    if manifest is None:
        manifest = project_root / "translations_manifest.yaml"

    cache_dir.mkdir(parents=True, exist_ok=True)

    # Check if all output files already exist
    if not force:
        all_exist = all(
            (cache_dir / f"embeddings_{lang}.parquet").exists()
            for lang in LANGUAGE_ORDER
        )
        if all_exist and (cache_dir / "index.parquet").exists():
            logger.info("All output files already exist. Use --force to re-download.")
            return

    # Load manifest
    logger.info(f"Loading manifest: {manifest}")
    cfg = load_manifest(manifest)
    repo_id = cfg["source_repo"]
    model_dir = cfg["hf_model_dir"]
    translations = cfg["translations"]

    logger.info(
        f"Source: {repo_id}, model: {cfg['model']}, "
        f"{len(translations)} translations"
    )

    # Download and assemble per-language
    for lang in LANGUAGE_ORDER:
        output_file = cache_dir / f"embeddings_{lang}.parquet"
        lang_translations = [t for t in translations if t["language"] == lang]

        if not lang_translations:
            logger.warning(f"No translations for {lang}")
            continue

        logger.info(f"Fetching {len(lang_translations)} translations for {lang}...")
        frames = []

        for t in tqdm(lang_translations, desc=lang, leave=False):
            try:
                parquet_path = download_translation(
                    repo_id=repo_id,
                    model_dir=model_dir,
                    language=lang,
                    site=t["hf_site"],
                    translation_id=t["hf_translation_id"],
                    granularity=granularity,
                    cache_dir=cache_dir,
                )
                df = pl.read_parquet(parquet_path).select(
                    [
                        pl.lit(t["canonical_id"]).alias("translation_id"),
                        pl.col("key"),
                        pl.col("value").alias("vector"),
                    ]
                )
                frames.append(df)
            except Exception:
                logger.exception(
                    f"Failed to download {t['canonical_id']} "
                    f"({t['hf_site']}/{t['hf_translation_id']})"
                )

        if frames:
            df_lang = pl.concat(frames)
            df_lang.write_parquet(output_file)
            logger.success(
                f"Wrote {output_file.name}: "
                f"{len(frames)} translations, {df_lang.height} rows"
            )
        else:
            logger.error(f"No data assembled for {lang}")

    # Create index.parquet from manifest metadata
    index_records = []
    for t in translations:
        index_records.append(
            {
                "translation_id": t["canonical_id"],
                "language": t["language"],
                "full_name": t.get("full_name"),
                "abbreviation": t.get("abbreviation"),
                "mode": t.get("mode"),
                "year": None,
            }
        )

    df_index = pl.DataFrame(index_records)
    index_path = cache_dir / "index.parquet"
    df_index.write_parquet(index_path)
    logger.success(f"Wrote {index_path.name}: {df_index.height} entries")

    logger.success("Done.")


if __name__ == "__main__":
    app()
