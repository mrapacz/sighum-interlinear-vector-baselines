#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pypdf>=4.0",
# ]
# ///
"""
Combine individual PCA-interpretability figure PDFs into a single file.

Reads from docs/pca-interpretability-figures/ and writes a combined PDF
to the same directory.  The page order is chosen to match the narrative
flow of the analysis (scatter plots first, deep-dives in the middle,
heatmaps at the end).

Usage:
    uv run scripts/08_combine_interpretability_figures.py
"""

from pathlib import Path

from pypdf import PdfWriter

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
FIGURES_DIR = REPO_ROOT / "docs" / "pca-interpretability-figures"

# Ordered list of figures to include.
# 11_english_magnitude_bar.pdf and 12_french_magnitude_bar.pdf are excluded.
FIGURE_ORDER = [
    "01_pca_scatter_by_genre.pdf",
    "02_pca_scatter_all_points.pdf",
    "03_genre_centroid_arrows.pdf",
    "07_pca_scatter_by_mode.pdf",
    "08_english_per_translation.pdf",
    "09_english_fnv_ojb_genre.pdf",
    "10_french_per_translation.pdf",
    "04_feature_correlation_heatmap.pdf",
    "05_probe_alignment_heatmap.pdf",
]

OUTPUT = FIGURES_DIR / "combined_interpretability_figures.pdf"


def main() -> None:
    writer = PdfWriter()
    for name in FIGURE_ORDER:
        path = FIGURES_DIR / name
        if not path.exists():
            print(f"  ⚠ Missing: {name}")
            continue
        writer.append(str(path))
        print(f"  ✓ {name}")

    writer.write(str(OUTPUT))
    writer.close()
    print(f"\nCombined {len(FIGURE_ORDER)} figures → {OUTPUT}")


if __name__ == "__main__":
    main()
