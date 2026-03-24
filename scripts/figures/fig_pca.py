#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "polars>=1.0",
#     "numpy>=1.26",
#     "matplotlib>=3.8",
#     "pyarrow>=15.0",
#     "loguru>=0.7",
# ]
# ///
"""PCA scatter plots — uniform yale-blue, despined (subfigures + assembled)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matplotlib.patches import Ellipse

from figures import (
    ISO_LABELS,
    LANG_TITLE_FONTSIZE,
    LANGUAGE_ORDER,
    YALE_BLUE,
    apply_rc,
    load_data,
    pl,
    plt,
    resolve_paths,
    save_figure,
)

WIDTH_SCALE = 1.0
HEIGHT_SCALE = 0.75


def _draw_pca(
    ax: plt.Axes,
    pca_df: pl.DataFrame,
    *,
    point_size: int = 20,
    show_ellipses: bool = False,
) -> None:
    """Draw a PCA scatter panel."""
    shuffled = pca_df.sample(fraction=1.0, shuffle=True, seed=42)

    ax.scatter(
        shuffled["pca_x"].to_numpy(),
        shuffled["pca_y"].to_numpy(),
        c=YALE_BLUE,
        s=point_size,
        alpha=0.6,
        edgecolors="none",
    )

    if show_ellipses:
        _add_ellipses(ax, pca_df)

    ax.axhline(0, color="k", linestyle="--", alpha=0.3, linewidth=0.5)
    ax.axvline(0, color="k", linestyle="--", alpha=0.3, linewidth=0.5)
    ax.set_xlabel("PC 1", fontsize=16)
    ax.set_ylabel("PC 2", fontsize=16)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)


def _add_ellipses(ax: plt.Axes, pca_df: pl.DataFrame) -> None:
    """Add dashed ellipses + labels around FNV and OJB translation clusters."""
    highlights = {
        "orthodox-jewish-bible": ("OJB", (0.08, 0.08)),
        "first-nations-version": ("FNV", (0.92, 0.08)),
    }
    for tid, (label, text_pos) in highlights.items():
        tid_data = pca_df.filter(pl.col("translation_id") == tid)
        if tid_data.is_empty():
            continue
        xs = tid_data["pca_x"].to_numpy()
        ys = tid_data["pca_y"].to_numpy()
        cx, cy = xs.mean(), ys.mean()
        w = max(xs.std() * 4, 0.01)
        h = max(ys.std() * 4, 0.01)
        ellipse = Ellipse(
            (cx, cy),
            width=w,
            height=h,
            fill=False,
            edgecolor="black",
            linewidth=2,
            linestyle="--",
            alpha=0.8,
        )
        ax.add_patch(ellipse)
        ax.annotate(
            label,
            xy=(cx, cy),
            xytext=text_pos,
            textcoords="axes fraction",
            fontsize=16,
            fontweight="bold",
            color="black",
            ha="center",
            va="center",
            arrowprops={
                "arrowstyle": "-|>",
                "color": "black",
                "linewidth": 2,
                "connectionstyle": "arc3,rad=0.15",
            },
        )


def main() -> None:
    apply_rc()
    hf_dir, figures_dir = resolve_paths()
    df, _, _ = load_data(hf_dir)

    pca_dir = figures_dir / "figure-group-pca"
    pca_dir.mkdir(parents=True, exist_ok=True)

    # ── Individual subfigures ────────────────────────────────
    for lang in LANGUAGE_ORDER:
        is_eng = lang == "eng"
        fig, ax = plt.subplots(
            figsize=(10 * WIDTH_SCALE, 8 * HEIGHT_SCALE)
            if is_eng
            else (7 * WIDTH_SCALE, 6 * HEIGHT_SCALE)
        )
        lang_df = df.filter(pl.col("language") == lang)

        _draw_pca(ax, lang_df, show_ellipses=is_eng)
        ax.set_title(ISO_LABELS[lang], fontsize=LANG_TITLE_FONTSIZE, fontweight="bold")

        save_figure(fig, pca_dir / f"pca_{lang}.pdf")

    # ── Assembled: EN large LEFT, 2x2 RIGHT (horizontal) ────
    fig_asm = plt.figure(figsize=(20 * WIDTH_SCALE, 10 * HEIGHT_SCALE))
    gs = fig_asm.add_gridspec(
        2,
        3,
        width_ratios=[1.2, 1, 1],
        hspace=0.08,
        wspace=0.08,
    )

    # EN: left column spanning both rows
    ax_eng = fig_asm.add_subplot(gs[:, 0])
    eng_df = df.filter(pl.col("language") == "eng")
    _draw_pca(ax_eng, eng_df, show_ellipses=True)
    ax_eng.set_title("English", fontsize=LANG_TITLE_FONTSIZE, fontweight="bold")

    # 2x2 on the right — no axis labels
    other_langs = [lang for lang in LANGUAGE_ORDER if lang != "eng"]
    positions = [(0, 1), (0, 2), (1, 1), (1, 2)]
    for lang, (row, col) in zip(other_langs, positions, strict=False):
        ax = fig_asm.add_subplot(gs[row, col])
        lang_df = df.filter(pl.col("language") == lang)
        _draw_pca(ax, lang_df, point_size=15)
        ax.set_title(ISO_LABELS[lang], fontsize=LANG_TITLE_FONTSIZE, fontweight="bold")
        ax.set_xlabel("")
        ax.set_ylabel("")

    save_figure(fig_asm, figures_dir / "figure-pca.pdf")


if __name__ == "__main__":
    main()
