"""
Shared constants, config, and data loading for poster figures.

This module centralizes all reusable pieces so each figure script
stays short and focused on its own plot.

Colors are loaded from a TOML palette file (see palettes/).
Set POSTER_PALETTE env var to override (default: palettes/current.toml).
"""

from __future__ import annotations

import logging
import os
import sys
import tomllib
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from loguru import logger
from matplotlib.colors import LinearSegmentedColormap, ListedColormap

# Suppress harmless fontTools warnings from DM Sans metadata quirks
# (fontTools uses Python logging, not the warnings module)
logging.getLogger("fontTools.ttLib.tables._h_e_a_d").setLevel(logging.ERROR)
logging.getLogger("fontTools.ttLib.tables._p_o_s_t").setLevel(logging.ERROR)

# ── Path resolution ──────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent.parent  # public/sighum
DEFAULT_HF_DIR = PROJECT_DIR / ".cache" / "hf-data"
DEFAULT_FIGURES_DIR = PROJECT_DIR / "figures" / "poster"

# ── Load palette from TOML ───────────────────────────────────

_PALETTE_PATH = Path(
    os.environ.get("POSTER_PALETTE", str(PROJECT_DIR / "palettes" / "current.toml"))
)
if not _PALETTE_PATH.is_absolute():
    _PALETTE_PATH = PROJECT_DIR / _PALETTE_PATH

with _PALETTE_PATH.open("rb") as _f:
    _PAL = tomllib.load(_f)

# ── Semantic color constants (from palette) ──────────────────

# Surface
POSTER_BG = _PAL["surface"]["background"]
PANEL_BG = _PAL["surface"]["panel"]

# Text tiers
TEXT_HEADING = _PAL["text"]["heading"]
TEXT_BODY = _PAL["text"]["body"]
TEXT_CAPTION = _PAL["text"]["caption"]
TEXT_RULE = _PAL["text"]["rule"]

# Accent
ACCENT_PRIMARY = _PAL["accent"]["primary"]

# Gradients
GRADIENT_START = _PAL["gradient"]["start"]
GRADIENT_END = _PAL["gradient"]["end"]

# Heatmap significance ramp
HEATMAP_P001 = _PAL["heatmap"]["p001"]
HEATMAP_P01 = _PAL["heatmap"]["p01"]
HEATMAP_P05 = _PAL["heatmap"]["p05"]
HEATMAP_NS = _PAL["heatmap"]["ns"]

# Figure elements
FIGURE_FILL = _PAL["figure"]["fill"]
FIGURE_SCATTER = _PAL["figure"]["scatter"]

# Strategy colors (monochrome by default, can be per-strategy)
STRATEGY_COLORS = _PAL["strategy"]

# Legacy aliases (so existing code keeps working during migration)
GRAPHITE = TEXT_HEADING
STORMY_TEAL = GRADIENT_END
WHITE = GRADIENT_START
ALABASTER_GREY = TEXT_RULE
YALE_BLUE = ACCENT_PRIMARY

# ── Strategy & language constants ────────────────────────────

STRATEGY_ORDER: list[str] = ["Literal", "Formal", "Dynamic", "Paraphrase"]

LANGUAGE_ORDER: list[str] = ["eng", "fra", "ita", "pol", "spa"]

ISO_LABELS: dict[str, str] = {
    "eng": "English",
    "fra": "French",
    "ita": "Italian",
    "pol": "Polish",
    "spa": "Spanish",
}

# Uniform font size for language titles across all composite figures
LANG_TITLE_FONTSIZE = 18

# ── Heatmap color scale (significance ramp from palette) ─────

HEATMAP_CMAP = ListedColormap(
    [
        HEATMAP_P001,  # p < 0.001 (darkest)
        HEATMAP_P01,  # p < 0.01
        HEATMAP_P05,  # p < 0.05
        HEATMAP_NS,  # n.s.      (lightest)
    ]
)
HEATMAP_CMAP.set_bad(color=POSTER_BG)

# ── PCA color scale (gradient from palette) ──────────────────

PCA_CMAP = LinearSegmentedColormap.from_list("gradient", [GRADIENT_START, GRADIENT_END])

# ── Matplotlib RC for poster-quality output ──────────────────

POSTER_RC: dict = {
    "font.family": "sans-serif",
    "font.sans-serif": ["DM Sans", "Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 14,
    "axes.labelsize": 16,
    "axes.titlesize": 18,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 13,
    "lines.linewidth": 1.5,
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "xtick.major.size": 4,
    "ytick.major.size": 4,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
    "savefig.facecolor": POSTER_BG,
    "savefig.transparent": False,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "figure.constrained_layout.use": True,
    "figure.facecolor": POSTER_BG,
    "axes.facecolor": POSTER_BG,
}


def apply_rc() -> None:
    """Apply poster matplotlib RC params."""
    plt.rcParams.update(POSTER_RC)


# ── Path helpers ─────────────────────────────────────────────


def _cli_path(flag: str) -> Path | None:
    if flag in sys.argv:
        idx = sys.argv.index(flag)
        return Path(sys.argv[idx + 1])
    return None


def resolve_paths() -> tuple[Path, Path]:
    """Return (hf_dir, figures_dir) from CLI args or defaults."""
    hf_dir = _cli_path("--hf-dir") or DEFAULT_HF_DIR
    figures_dir = _cli_path("--figures-dir") or DEFAULT_FIGURES_DIR
    figures_dir.mkdir(parents=True, exist_ok=True)
    return hf_dir, figures_dir


# ── Data loading ─────────────────────────────────────────────


def load_data(hf_dir: Path) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """
    Load and join chapter-level intervention data with metadata.

    Returns (df_joined, df_chapter_raw, df_index).
    """
    df_chapter = pl.read_parquet(hf_dir / "intervention_by_chapter.parquet")
    df_index = pl.read_parquet(hf_dir / "index.parquet")

    df = df_chapter.join(
        df_index.select(
            [
                "translation_id",
                "language",
                "mode",
                "full_name",
                "abbreviation",
            ]
        ),
        on=["translation_id", "language"],
        how="left",
    )
    return df, df_chapter, df_index


# ── Figure saving helper ─────────────────────────────────────


def save_figure(fig: plt.Figure, path: Path) -> None:
    """Save figure as both PDF and PNG, then log."""
    fig.savefig(path)
    fig.savefig(path.with_suffix(".png"), dpi=300)
    logger.info(f"Saved {path} (+.png)")
    plt.close(fig)


# ── Heatmap builder ──────────────────────────────────────────


def _compute_heatmap_matrices(
    df_lang: pl.DataFrame,
) -> tuple[np.ndarray, np.ndarray, list[str], float]:
    """Compute significance matrices for a pairwise heatmap."""
    from scipy.stats import mannwhitneyu

    annotated = (
        df_lang.filter(pl.col("mode").is_not_null())
        .select(["translation_id", "full_name", "abbreviation", "mode"])
        .unique()
    )
    chapter_by_id = (
        df_lang.filter(
            pl.col("translation_id").is_in(
                annotated["translation_id"].unique().to_list()
            )
        )
        .group_by("translation_id")
        .agg(pl.col("dist_interlinear").implode().alias("dists"))
    )

    id_to_mode = dict(zip(annotated["translation_id"], annotated["mode"], strict=False))
    id_to_label: dict[str, str] = {}
    for row in annotated.iter_rows(named=True):
        id_to_label[row["translation_id"]] = row["abbreviation"] or row["full_name"]

    def sort_key(cid: str) -> tuple[int, str]:
        m = id_to_mode.get(cid)
        pos = STRATEGY_ORDER.index(m) if m in STRATEGY_ORDER else len(STRATEGY_ORDER)
        return (pos, cid)

    ids = sorted(chapter_by_id["translation_id"].to_list(), key=sort_key)
    dists_map = dict(
        zip(chapter_by_id["translation_id"], chapter_by_id["dists"], strict=False)
    )

    n = len(ids)
    p_matrix = np.full((n, n), np.nan)

    for i, id_i in enumerate(ids):
        for j, id_j in enumerate(ids):
            if i == j:
                continue
            _, p_raw = mannwhitneyu(
                dists_map[id_i], dists_map[id_j], alternative="less"
            )
            p_matrix[i, j] = p_raw

    # Bonferroni correction
    n_comp = n * (n - 1)
    p_adj = np.where(np.isnan(p_matrix), np.nan, np.minimum(p_matrix * n_comp, 1.0))

    annot_arr = np.where(
        np.isnan(p_adj),
        "",
        np.where(
            p_adj < 0.001,
            "***",
            np.where(p_adj < 0.01, "**", np.where(p_adj < 0.05, "*", "")),
        ),
    )

    color_matrix = np.where(
        np.isnan(p_adj),
        np.nan,
        np.where(
            p_adj < 0.001, 0, np.where(p_adj < 0.01, 1, np.where(p_adj < 0.05, 2, 3))
        ),
    )

    labels = [id_to_label.get(tid, tid) for tid in ids]

    # Count pairs significant in either direction (full matrix),
    # denominator = unique pairs (upper triangle count).
    mask = ~np.isnan(p_adj)
    n_sig = int(np.sum(mask & (p_adj < 0.001)))
    n_pairs = n * (n - 1) // 2
    pct_sig = n_sig / n_pairs * 100 if n_pairs > 0 else 0

    return color_matrix, annot_arr, labels, float(pct_sig)


def draw_heatmap(
    ax: plt.Axes,
    df_lang: pl.DataFrame,
    *,
    tick_fontsize: int = 12,
    show_tick_labels: bool = True,
) -> float:
    """Draw a pairwise significance heatmap on the given axes. Returns pct_significant."""
    import seaborn as sns

    color_matrix, _annot_arr, labels, pct_sig = _compute_heatmap_matrices(df_lang)

    sns.heatmap(
        color_matrix,
        ax=ax,
        xticklabels=labels if show_tick_labels else False,
        yticklabels=labels if show_tick_labels else False,
        annot=False,
        cmap=HEATMAP_CMAP,
        vmin=0,
        vmax=3,
        square=True,
        cbar=False,
    )
    if show_tick_labels:
        ax.tick_params(labelsize=tick_fontsize)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
    else:
        ax.tick_params(left=False, bottom=False)

    return pct_sig


def build_heatmap(
    df_lang: pl.DataFrame,
    figsize: tuple[float, float],
    tick_fontsize: int = 12,
) -> tuple[plt.Figure, plt.Axes, float]:
    """Build a pairwise significance heatmap as a standalone figure."""
    fig, ax = plt.subplots(figsize=figsize)
    pct_sig = draw_heatmap(ax, df_lang, tick_fontsize=tick_fontsize)
    return fig, ax, float(pct_sig)
