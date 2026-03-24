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
"""Figure: English pairwise significance heatmap (large)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from figures import (
    LANG_TITLE_FONTSIZE,
    apply_rc,
    build_heatmap,
    load_data,
    pl,
    resolve_paths,
    save_figure,
)


def main() -> None:
    apply_rc()
    hf_dir, figures_dir = resolve_paths()
    df, _, _ = load_data(hf_dir)

    eng_df = df.filter(pl.col("language") == "eng")
    fig, ax, pct = build_heatmap(
        eng_df,
        figsize=(10, 10),
        tick_fontsize=11,
        annot_fontsize=9,
    )
    ax.set_title(
        f"English — {pct:.0f}% significant (p < 0.001)",
        fontsize=LANG_TITLE_FONTSIZE,
        fontweight="bold",
    )

    save_figure(fig, figures_dir / "heatmap_eng.pdf")


if __name__ == "__main__":
    main()
