#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "polars>=1.0",
#     "pyarrow>=15.0",
#     "numpy>=1.26",
#     "rich>=13.0",
#     "httpx>=0.27",
#     "typer>=0.15",
#     "huggingface-hub>=0.20",
#     "pyyaml>=6.0",
# ]
# ///
"""
Find monotonic NT verses where intervention magnitude increases
strictly across translation strategies (Literal < Formal < Dynamic
< Paraphrase), ranked by spread.

Verse-level embeddings are downloaded from the targum-corpus HF dataset
(specified via translations_manifest.yaml) and L2 distances to the
interlinear baseline are computed on-the-fly.  Results are cached in
``.cache/verse-8b-cache/``.

Usage (from repo root):
    uv run scripts/04_find_example_verse.py [OPTIONS]

Examples:
    # Show 20 monotonic verses (default: 10)
    uv run scripts/04_find_example_verse.py --top 20

    # Inspect a single verse
    uv run scripts/04_find_example_verse.py --verse "MAT 12:30"

    # Show Greek source text alongside translations
    uv run scripts/04_find_example_verse.py --greek

    # Save examples to a text file
    uv run scripts/04_find_example_verse.py --save-examples
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated

import httpx
import numpy as np
import polars as pl
import typer
import yaml
from huggingface_hub import hf_hub_download
from rich.console import Console
from rich.table import Table

# ── Defaults ──────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
MANIFEST_PATH = REPO_ROOT / "translations_manifest.yaml"
CACHE_DIR = REPO_ROOT / ".cache" / "verse-8b-cache"

STRATEGY_ORDER = ["Literal", "Formal", "Dynamic", "Paraphrase"]
MODE_REMAP = {"Formal/Standard": "Formal", "Paraphrase/Cultural": "Paraphrase"}

HF_EMBEDDINGS_PREFIX = "embeddings"

# ── SBLGNT Greek NT data ──────────────────────────────────────────

SBLGNT_BASE_URL = (
    "https://raw.githubusercontent.com/Faithlife/SBLGNT/master/data/sblgnt/text"
)

SBLGNT_FILES: list[tuple[str, str]] = [
    ("Matt.txt", "MAT"),
    ("Mark.txt", "MRK"),
    ("Luke.txt", "LUK"),
    ("John.txt", "JHN"),
    ("Acts.txt", "ACT"),
    ("Rom.txt", "ROM"),
    ("1Cor.txt", "1CO"),
    ("2Cor.txt", "2CO"),
    ("Gal.txt", "GAL"),
    ("Eph.txt", "EPH"),
    ("Phil.txt", "PHP"),
    ("Col.txt", "COL"),
    ("1Thess.txt", "1TH"),
    ("2Thess.txt", "2TH"),
    ("1Tim.txt", "1TI"),
    ("2Tim.txt", "2TI"),
    ("Titus.txt", "TIT"),
    ("Phlm.txt", "PHM"),
    ("Heb.txt", "HEB"),
    ("Jas.txt", "JAS"),
    ("1Pet.txt", "1PE"),
    ("2Pet.txt", "2PE"),
    ("1John.txt", "1JN"),
    ("2John.txt", "2JN"),
    ("3John.txt", "3JN"),
    ("Jude.txt", "JUD"),
    ("Rev.txt", "REV"),
]


def _clean_greek_word(token: str) -> str:
    return "".join(
        c
        for c in token
        if (0x0370 <= ord(c) <= 0x03FF) or (0x1F00 <= ord(c) <= 0x1FFF)
    )


def fetch_greek_verses(console: Console) -> dict[str, str]:
    """Download SBLGNT and return {ref_key: greek_text} for every verse."""
    greek: dict[str, str] = {}
    with httpx.Client(timeout=30) as client:
        for filename, usfm in SBLGNT_FILES:
            console.print(f"  Fetching {usfm}...", style="dim")
            resp = client.get(f"{SBLGNT_BASE_URL}/{filename}")
            resp.raise_for_status()
            for line in resp.text.splitlines():
                if "\t" not in line:
                    continue
                ref_part, text = line.split("\t", 1)
                match = re.match(r".*\s+(\d+):(\d+)", ref_part)
                if not match:
                    continue
                chapter = int(match.group(1))
                verse = match.group(2)
                ref_key = f"{usfm} {chapter}:{verse}"
                words = [
                    w for token in text.split() if (w := _clean_greek_word(token))
                ]
                greek[ref_key] = " ".join(words)
    return greek


# ── Data loading from HuggingFace ─────────────────────────────────


def _load_manifest() -> dict:
    return yaml.safe_load(MANIFEST_PATH.read_text())


def _hf_verse_path(manifest: dict, entry: dict) -> str:
    """Build the HF repo path for a verse-level parquet file."""
    model_dir = manifest["hf_model_dir"]
    lang = entry["language"]
    site = entry["hf_site"]
    tid = entry["hf_translation_id"]
    return (
        f"{HF_EMBEDDINGS_PREFIX}/{model_dir}"
        f"/language={lang}/site={site}"
        f"/translation={tid}/granularity=verse/data.parquet"
    )


def _download_verse_embeddings(
    manifest: dict, lang: str, console: Console
) -> pl.DataFrame:
    """Download verse-level embeddings for all translations in a language."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    combined_cache = CACHE_DIR / f"all_{lang}_verse_8b.parquet"

    if combined_cache.exists():
        console.print(f"  Using cached [dim]{combined_cache}[/dim]")
        return pl.read_parquet(combined_cache)

    source_repo = manifest["source_repo"]
    entries = [
        e for e in manifest["translations"] if e["language"] == lang
    ]

    frames = []
    for entry in entries:
        cid = entry["canonical_id"]
        cache_file = CACHE_DIR / f"{cid}.parquet"

        if cache_file.exists():
            console.print(f"  Cached: {cid}", style="dim")
            df = pl.read_parquet(cache_file)
        else:
            hf_path = _hf_verse_path(manifest, entry)
            console.print(f"  Downloading: {cid}...")
            local = hf_hub_download(
                repo_id=source_repo,
                filename=hf_path,
                repo_type="dataset",
            )
            df = pl.read_parquet(local)
            df.write_parquet(cache_file)

        df = df.with_columns(pl.lit(cid).alias("translation_id"))
        frames.append(df)

    combined = pl.concat(frames)
    combined.write_parquet(combined_cache)
    console.print(
        f"  Combined: {combined.shape[0]} rows, "
        f"{combined['translation_id'].n_unique()} translations"
    )
    return combined


def _compute_distances(
    df: pl.DataFrame, manifest: dict, lang: str
) -> pl.DataFrame:
    """Compute L2 distances from each translation to the interlinear baseline."""
    entries = {
        e["canonical_id"]: e
        for e in manifest["translations"]
        if e["language"] == lang
    }
    inter_ids = [
        cid for cid, e in entries.items() if e["mode"] == "Literal" and "interlinear" in cid
    ]
    if not inter_ids:
        raise SystemExit("No interlinear translation found in manifest")

    inter_id = inter_ids[0]
    inter_df = df.filter(pl.col("translation_id") == inter_id)
    inter_vecs = {
        row["key"]: np.array(row["value"])
        for row in inter_df.iter_rows(named=True)
    }

    rows = []
    non_inter = df.filter(pl.col("translation_id") != inter_id)
    for row in non_inter.iter_rows(named=True):
        key = row["key"]
        if key not in inter_vecs:
            continue
        vec = np.array(row["value"])
        dist = float(np.linalg.norm(vec - inter_vecs[key]))
        entry = entries.get(row["translation_id"], {})
        mode_raw = entry.get("mode", "?")
        mode = MODE_REMAP.get(mode_raw, mode_raw)
        rows.append(
            {
                "verse": key,
                "translation_id": row["translation_id"],
                "abbreviation": entry.get("abbreviation", "?"),
                "mode": mode,
                "dist": dist,
            }
        )

    return pl.DataFrame(rows)


def _local_corpus_path(entry: dict, data_dir: Path) -> Path | None:
    """Resolve the local JSONL corpus file for a manifest entry."""
    lang = entry["language"]
    site = entry["hf_site"]
    tid = entry["hf_translation_id"]
    cid = entry["canonical_id"]

    # Interlinear lives in a separate directory with a verse-level variant
    if "interlinear" in cid:
        interlinear_dir = data_dir / "interlinear" / "export"
        verses_file = interlinear_dir / f"interlinear-{site}.verses.jsonl"
        if verses_file.exists():
            return verses_file
        return None

    corpus_dir = data_dir / "bible" / "exporter" / "full" / "corpora"
    return corpus_dir / site / lang / f"{tid}.jsonl"


def _load_verse_texts(
    manifest: dict, lang: str, console: Console
) -> dict[tuple[str, str], str]:
    """Load verse texts from local targum data directory.

    Uses $TARGUM_BASE_DATA_DIR (default: ./data) to find JSONL corpus files.
    These include copyrighted texts not available on HuggingFace — intended
    for local analysis only, not for redistribution.
    """
    import json
    import os

    TEXT_CACHE_DIR = REPO_ROOT / ".cache" / "verse-texts"
    TEXT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = TEXT_CACHE_DIR / f"texts_{lang}.json"

    if cache_file.exists():
        console.print(f"  Using cached texts [dim]{cache_file}[/dim]")
        raw = json.loads(cache_file.read_text())
        return {tuple(k.split("|", 1)): v for k, v in raw.items()}

    data_dir = Path(os.environ.get("TARGUM_BASE_DATA_DIR", "data"))
    entries = [
        e for e in manifest["translations"] if e["language"] == lang
    ]

    texts: dict[tuple[str, str], str] = {}
    for entry in entries:
        cid = entry["canonical_id"]
        local_path = _local_corpus_path(entry, data_dir)
        if local_path is None or not local_path.exists():
            console.print(f"  [yellow]Not found: {cid} ({local_path})[/yellow]")
            continue
        console.print(f"  Loading: {cid}", style="dim")
        for line in local_path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            ref = f"{rec['book']} {rec['chapter']}:{rec['verse']}"
            texts[(ref, cid)] = rec.get("text", "")

    # Cache as flat dict with "ref|cid" keys
    serializable = {f"{ref}|{cid}": t for (ref, cid), t in texts.items()}
    cache_file.write_text(json.dumps(serializable, ensure_ascii=False))
    console.print(f"  Cached {len(texts)} verse texts ({len(entries)} translations)")
    return texts


# ── Display helpers ───────────────────────────────────────────────


def _print_verse_detail(
    ref: str,
    dist_df: pl.DataFrame,
    console: Console,
    *,
    greek_text: str | None = None,
    spread: float | None = None,
) -> None:
    """Pretty-print a single verse across all loaded translations."""
    console.print(f"\n[cyan bold]── {ref} ──[/cyan bold]")
    if spread is not None:
        console.print(f"  Spread: [green]{spread:.3f}[/green]")
    if greek_text:
        console.print(f"  [italic]Greek: {greek_text}[/italic]")

    verse_data = dist_df.filter(pl.col("verse") == ref).sort("dist")
    for strategy in STRATEGY_ORDER:
        group = verse_data.filter(pl.col("mode") == strategy)
        for row in group.iter_rows(named=True):
            abbr = row["abbreviation"]
            dist = row["dist"]
            console.print(
                f"  [bold]{strategy}[/bold] ({abbr}): [green]{dist:.3f}[/green]"
            )


# ── CLI ───────────────────────────────────────────────────────────

app = typer.Typer(add_completion=False)


@app.command()
def main(
    top: Annotated[
        int, typer.Option(help="Number of top monotonic verses to display.")
    ] = 10,
    verse: Annotated[
        str | None,
        typer.Option(
            help='Inspect a specific verse, e.g. "MAT 12:30" or "ROM 8:28".'
        ),
    ] = None,
    greek: Annotated[
        bool, typer.Option(help="Fetch and display Greek source text (SBLGNT).")
    ] = True,
    book: Annotated[
        str | None,
        typer.Option(help="Filter to a specific book, e.g. JHN, ROM, GAL."),
    ] = None,
    lang: Annotated[str, typer.Option(help="Language ISO code.")] = "eng",
    save_examples: Annotated[
        bool,
        typer.Option(help="Save examples to data/monotonic_examples.txt."),
    ] = False,
) -> None:
    """Find monotonic NT verses (Literal < Formal < Dynamic < Paraphrase)."""
    console = Console()
    manifest = _load_manifest()

    # ── Download verse-level embeddings ───────────────────────────
    console.print("[bold]Loading verse-level embeddings…[/bold]")
    df = _download_verse_embeddings(manifest, lang, console)

    # ── Compute distances ─────────────────────────────────────────
    console.print("[bold]Computing distances to interlinear…[/bold]")
    dist_df = _compute_distances(df, manifest, lang)
    console.print(f"  {len(dist_df)} distance pairs")

    # ── Load verse texts ──────────────────────────────────────────
    console.print("[bold]Loading verse texts…[/bold]")
    verse_texts = _load_verse_texts(manifest, lang, console)

    # ── Single verse mode ─────────────────────────────────────────
    if verse is not None:
        verse_data = dist_df.filter(pl.col("verse") == verse)
        if verse_data.height == 0:
            console.print(f"[red]No data found for {verse}[/red]")
            raise typer.Exit(1)
        greek_text = None
        if greek:
            console.print("[bold]Fetching Greek source text…[/bold]")
            greek_verses = fetch_greek_verses(console)
            greek_text = greek_verses.get(verse)
        spread = verse_data["dist"].max() - verse_data["dist"].min()
        _print_verse_detail(
            verse, dist_df, console, greek_text=greek_text, spread=spread
        )
        return

    # ── Find monotonic verses ─────────────────────────────────────
    console.print("[bold]Finding monotonic verses…[/bold]")

    group_means = dist_df.group_by(["verse", "mode"]).agg(
        pl.col("dist").mean().alias("mean_dist")
    )
    pivoted = group_means.pivot(on="mode", index="verse", values="mean_dist")

    for col in STRATEGY_ORDER:
        if col not in pivoted.columns:
            console.print(f"[red]Missing strategy group: {col}[/red]")
            raise typer.Exit(1)

    pivoted = pivoted.drop_nulls(subset=STRATEGY_ORDER)
    monotonic = (
        pivoted.filter(
            (pl.col("Literal") < pl.col("Formal"))
            & (pl.col("Formal") < pl.col("Dynamic"))
            & (pl.col("Dynamic") < pl.col("Paraphrase"))
        )
        .with_columns(
            (pl.col("Paraphrase") - pl.col("Literal")).alias("spread")
        )
        .sort("spread", descending=True)
    )

    if book:
        monotonic = monotonic.filter(
            pl.col("verse").str.starts_with(book.upper() + " ")
        )

    console.print(
        f"  {len(monotonic)} monotonic verses "
        f"(out of {len(pivoted)} with all 4 groups)"
    )

    # ── Greek text (always fetched — used for sorting by length) ──
    console.print("[bold]Fetching Greek source text (SBLGNT)…[/bold]")
    greek_verses = fetch_greek_verses(console)

    # ── Sort: shortest Greek first, then by spread ────────────────
    monotonic = monotonic.with_columns(
        pl.col("verse")
        .map_elements(
            lambda v: len(greek_verses.get(v, "")), return_dtype=pl.Int64
        )
        .alias("greek_len")
    ).sort(["greek_len", "spread"], descending=[False, True])

    # Drop verses with no Greek text (SBLGNT numbering gaps)
    monotonic = monotonic.filter(pl.col("greek_len") > 0)

    # ── Display top N ─────────────────────────────────────────────
    top_df = monotonic.head(top)

    table = Table(
        title=f"Top {top} monotonic verses — shortest Greek, then spread (8B)",
        show_lines=True,
    )
    table.add_column("Rank", style="bold", width=4)
    table.add_column("Ref", style="cyan bold", width=12)
    table.add_column("Len", style="yellow", width=4)
    table.add_column("Spread", style="green", width=8)
    table.add_column("Group Means", width=40)
    if greek:
        table.add_column("Greek", style="italic", width=50)
    table.add_column("Translations", width=80)

    for rank, row in enumerate(top_df.iter_rows(named=True), 1):
        ref = row["verse"]
        greek_text = greek_verses.get(ref, "")

        means_str = (
            f"L={row['Literal']:.3f}  F={row['Formal']:.3f}  "
            f"D={row['Dynamic']:.3f}  P={row['Paraphrase']:.3f}"
        )

        verse_data = dist_df.filter(pl.col("verse") == ref).sort("dist")
        trans_lines = []
        for strategy in STRATEGY_ORDER:
            group = verse_data.filter(pl.col("mode") == strategy)
            for vrow in group.iter_rows(named=True):
                abbr = vrow["abbreviation"]
                tid = vrow["translation_id"]
                dist = vrow["dist"]
                text = verse_texts.get((ref, tid), "")
                line = f"{strategy} ({abbr}) {dist:.3f}"
                if text:
                    line += f": {text}"
                trans_lines.append(line)

        cells = [
            str(rank),
            ref,
            str(row["greek_len"]),
            f"{row['spread']:.3f}",
            means_str,
        ]
        if greek:
            cells.append(greek_text)
        cells.append("\n".join(trans_lines))
        table.add_row(*cells)

    console.print(table)

    # ── Save examples ─────────────────────────────────────────────
    if save_examples:
        output_dir = REPO_ROOT / "data"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "monotonic_examples.txt"

        lines = [
            "# Monotonic Verse Examples (8B model)",
            "# Monotonic = group means: Literal < Formal < Dynamic < Paraphrase",
            "# Sorted by: shortest Greek text first, then by spread",
            f"# {len(monotonic)} total monotonic verses",
            "# Regenerate: uv run scripts/04_find_example_verse.py "
            "--save-examples --top N",
            "",
        ]
        for rank, row in enumerate(top_df.iter_rows(named=True), 1):
            ref = row["verse"]
            gk = greek_verses.get(ref, "(not available)")
            lines.append("=" * 80)
            lines.append(
                f"#{rank}  {ref}  "
                f"(greek_len: {row['greek_len']}, spread: {row['spread']:.3f})"
            )
            lines.append(
                f"  Group means: Literal={row['Literal']:.3f}  "
                f"Formal={row['Formal']:.3f}  Dynamic={row['Dynamic']:.3f}  "
                f"Paraphrase={row['Paraphrase']:.3f}"
            )
            lines.append("=" * 80)
            gk = greek_verses.get(ref, "(not available)")
            lines.append(f"  GREEK: {gk}")
            lines.append("")

            verse_data = dist_df.filter(pl.col("verse") == ref).sort("dist")
            for strategy in STRATEGY_ORDER:
                group = verse_data.filter(pl.col("mode") == strategy)
                for vrow in group.iter_rows(named=True):
                    abbr = vrow["abbreviation"]
                    tid = vrow["translation_id"]
                    dist = vrow["dist"]
                    text = verse_texts.get((ref, tid), "")
                    lines.append(
                        f"  [{strategy:12s}] {abbr:8s} (d={dist:.3f}): {text}"
                    )
            lines.append("")

        output_path.write_text("\n".join(lines))
        console.print(f"\nExamples saved to [cyan]{output_path}[/cyan]")


if __name__ == "__main__":
    app()
