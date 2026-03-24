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
"""Run all poster figure scripts."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from figures.fig_group_heatmaps import main as group_heatmaps
from figures.fig_heatmaps import main as heatmaps
from figures.fig_pca import main as pca
from figures.fig_ridgeline import main as ridgeline
from figures.fig_violin_strip import main as violins

ALL_FIGURES = [
    ("violins", violins),
    ("ridgeline", ridgeline),
    ("pca", pca),
    ("heatmaps", heatmaps),
    ("group_heatmaps", group_heatmaps),
]


def main() -> None:
    from loguru import logger

    for name, fn in ALL_FIGURES:
        logger.info(f"── {name} ──")
        fn()
    logger.info("All poster figures generated.")


if __name__ == "__main__":
    main()
