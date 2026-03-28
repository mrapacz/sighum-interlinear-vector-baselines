#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo>=0.19",
#     "polars>=1.0",
#     "numpy>=1.26",
#     "matplotlib>=3.8",
#     "seaborn>=0.13",
#     "scipy>=1.12",
#     "pypalettes>=0.1",
#     "pyarrow>=15.0",
#     "loguru>=0.7",
# ]
# ///
"""
Generate figures and statistical data for SIGHUM paper.

This marimo notebook generates all publication figures and statistical analyses
from the HuggingFace dataset.

Outputs:
- Figures (PDF): dist_to_interlinear_by_strategy_chapter_level.pdf, pca_per_language.pdf,
  pairwise_mannwhitney_groups_chapter_by_language_bonferroni.pdf,
  pairwise_mannwhitney_chapter_{lang}_bonferroni.pdf (5 files)
- Statistical data (TSV): pairwise_mannwhitney_groups.tsv, pairwise_mannwhitney_translations.tsv
"""

import marimo

__generated_with = "0.19.9"
app = marimo.App()


@app.cell
def _():
    """Import dependencies."""
    from pathlib import Path

    import matplotlib.pyplot as plt
    import numpy as np
    import polars as pl
    import seaborn as sns
    from loguru import logger
    from matplotlib.colorbar import ColorbarBase
    from matplotlib.colors import ListedColormap, Normalize
    from pypalettes import load_cmap, load_palette
    from scipy.stats import mannwhitneyu

    return (
        ColorbarBase,
        ListedColormap,
        Normalize,
        Path,
        load_cmap,
        load_palette,
        logger,
        mannwhitneyu,
        np,
        pl,
        plt,
        sns,
    )


@app.cell
def _(Path):
    """Define paths."""
    import sys

    script_dir = Path(__file__).parent

    # Parse CLI args if running as script
    _hf_dir = None
    _gh_figures_dir = None
    _gh_data_dir = None

    if "--hf-dir" in sys.argv:
        _idx = sys.argv.index("--hf-dir")
        _hf_dir = Path(sys.argv[_idx + 1])
    if "--gh-figures-dir" in sys.argv:
        _idx = sys.argv.index("--gh-figures-dir")
        _gh_figures_dir = Path(sys.argv[_idx + 1])
    if "--gh-data-dir" in sys.argv:
        _idx = sys.argv.index("--gh-data-dir")
        _gh_data_dir = Path(sys.argv[_idx + 1])

    hf_dir = _hf_dir or script_dir.parent / ".cache" / "hf-data"
    gh_figures_dir = _gh_figures_dir or script_dir.parent / "figures"
    gh_data_dir = _gh_data_dir or script_dir.parent / "data"

    # Create output directories
    gh_figures_dir.mkdir(parents=True, exist_ok=True)
    gh_data_dir.mkdir(parents=True, exist_ok=True)

    return gh_data_dir, gh_figures_dir, hf_dir, script_dir


@app.cell
def _(hf_dir, pl):
    """Load data from HuggingFace repo."""
    df_chapter = pl.read_parquet(hf_dir / "intervention_by_chapter.parquet")
    df_index = pl.read_parquet(hf_dir / "index.parquet")

    # Join chapter data with metadata
    df_chapter_meta = df_chapter.join(
        df_index.select(
            ["translation_id", "language", "mode", "full_name", "abbreviation"]
        ),
        on=["translation_id", "language"],
        how="left",
    )

    return df_chapter, df_chapter_meta, df_index


@app.cell
def _():
    """Define constants."""
    STRATEGY_ORDER = ["Literal", "Formal", "Dynamic", "Paraphrase"]
    # Language order: lexicographical by full name (English, French, Italian, Polish, Spanish)
    LANGUAGE_ORDER = ["eng", "fra", "ita", "pol", "spa"]
    ISO_REPLACEMENTS = {
        "eng": "English",
        "fra": "French",
        "ita": "Italian",
        "pol": "Polish",
        "spa": "Spanish",
    }
    return ISO_REPLACEMENTS, LANGUAGE_ORDER, STRATEGY_ORDER


@app.cell
def _(ListedColormap, load_palette):
    """Create significance color palette."""
    fall_palette = load_palette("Fall")
    sig_palette = ListedColormap(
        [fall_palette[0], fall_palette[1], fall_palette[2], fall_palette[-1]]
    )
    sig_palette.set_bad(color="white")
    return fall_palette, sig_palette


@app.cell
def _(plt):
    """Set matplotlib style."""
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans", "Liberation Sans"]


@app.cell
def _(
    ISO_REPLACEMENTS,
    LANGUAGE_ORDER,
    STRATEGY_ORDER,
    df_chapter_meta,
    gh_figures_dir,
    pl,
    plt,
    sns,
):
    """Figure 1: Violin plot - distance to interlinear by strategy and language."""
    chapter_plot_df = (
        df_chapter_meta.filter(pl.col("mode").is_not_null())
        .filter(pl.col("mode").is_in(STRATEGY_ORDER))
        .select(["language", "mode", "dist_interlinear"])
    )

    # Use strategy order as-is (seaborn plots in order from top to bottom)
    grid = sns.catplot(
        data=chapter_plot_df,
        x="dist_interlinear",
        y="mode",
        col="language",
        order=STRATEGY_ORDER,
        col_order=LANGUAGE_ORDER,
        kind="violin",
        legend=False,
        aspect=0.8,
        height=2,
        color="#555555",
    )

    grid.set_xlabels("Distance to interlinear translation")
    grid.set_ylabels("Strategy")

    for _ax in grid.axes.flat:
        _current_title = _ax.get_title() or ""
        _lang = ISO_REPLACEMENTS.get(
            _current_title.split("language = ")[1].split(",")[0].strip(),
            _current_title,
        )
        _ax.set_title(_lang)
        _ax.set_xlabel("")

    plt.tight_layout()
    grid.figure.supxlabel(
        "Distance to interlinear translation",
        y=-0.03,
    )

    violin_fig_path = (
        gh_figures_dir / "dist_to_interlinear_by_strategy_chapter_level.pdf"
    )
    grid.figure.savefig(
        violin_fig_path,
        dpi=300,
        bbox_inches="tight",
    )
    logger.info(f"Saved {violin_fig_path}")

    violin_fig = grid.fig
    return chapter_plot_df, grid, violin_fig, violin_fig_path


@app.cell
def _(
    ISO_REPLACEMENTS,
    LANGUAGE_ORDER,
    df_chapter_meta,
    df_index,
    gh_figures_dir,
    load_cmap,
    pl,
    plt,
    sns,
):
    """Figure 2: PCA scatter plots per language."""
    # Get mean distance per translation for coloring
    mean_dist = df_chapter_meta.group_by(["translation_id", "language"]).agg(
        pl.col("dist_interlinear").mean().alias("mean_dist")
    )

    pca_plot_df = df_chapter_meta.join(
        mean_dist,
        on=["translation_id", "language"],
        how="inner",
    )

    cmap = load_cmap("Sunset", cmap_type="continuous")
    isos = LANGUAGE_ORDER
    n_cols = len(isos)

    fig_pca, axes_pca = plt.subplots(1, n_cols, figsize=(2 * n_cols, 2))
    if n_cols == 1:
        axes_pca = [axes_pca]

    for _ax, _iso in zip(axes_pca, isos, strict=False):
        _data = pca_plot_df.filter(pl.col("language") == _iso)
        sns.scatterplot(
            data=_data,
            x="pca_x",
            y="pca_y",
            hue="mean_dist",
            ax=_ax,
            palette=cmap,
            s=25,
            alpha=0.8,
            legend=False,
        )
        _ax.set_title(ISO_REPLACEMENTS.get(_iso, _iso))
        _ax.set_xlabel("PCA 1")
        _ax.set_ylabel("")
        _ax.axhline(0, color="k", linestyle="--", alpha=0.4)
        _ax.axvline(0, color="k", linestyle="--", alpha=0.4)

    fig_pca.supylabel("PCA 2", x=0.02)
    plt.tight_layout()

    pca_fig_path = gh_figures_dir / "pca_per_language.pdf"
    fig_pca.savefig(pca_fig_path, dpi=300, bbox_inches="tight")
    logger.info(f"Saved {pca_fig_path}")

    return axes_pca, cmap, fig_pca, isos, mean_dist, n_cols, pca_fig_path, pca_plot_df


@app.cell
def _(
    ColorbarBase,
    ISO_REPLACEMENTS,
    LANGUAGE_ORDER,
    Normalize,
    STRATEGY_ORDER,
    df_chapter_meta,
    gh_data_dir,
    gh_figures_dir,
    mannwhitneyu,
    np,
    pl,
    plt,
    sig_palette,
    sns,
):
    """Figure 3: Strategy-group pairwise heatmap + statistics."""
    # Aggregate chapter-level distances by language and mode
    chapter_by_lang_mode = (
        df_chapter_meta.filter(pl.col("mode").is_not_null())
        .filter(pl.col("mode").is_in(STRATEGY_ORDER))
        .group_by("language", "mode")
        .agg(pl.col("dist_interlinear").implode().alias("dists"))
    )

    n_langs = len(LANGUAGE_ORDER)
    fig_groups, axes_groups = plt.subplots(3, 2, figsize=(6, 6), squeeze=False)
    axes_groups = axes_groups.flat

    # Store statistical results
    group_stats = []

    for idx, lang_g in enumerate(LANGUAGE_ORDER):
        ax_g = axes_groups[idx]
        lang_df_g = chapter_by_lang_mode.filter(pl.col("language") == lang_g)

        modes_g = sorted(
            lang_df_g["mode"].to_list(),
            key=lambda m: (
                STRATEGY_ORDER.index(m) if m in STRATEGY_ORDER else len(STRATEGY_ORDER),
                m,
            ),
        )

        dists_map_g = dict(zip(lang_df_g["mode"], lang_df_g["dists"], strict=False))
        n_modes = len(modes_g)
        p_matrix_g = np.full((n_modes, n_modes), np.nan)

        for i, mode_i in enumerate(modes_g):
            for j, mode_j in enumerate(modes_g):
                if i == j:
                    continue
                d_i = dists_map_g[mode_i]
                d_j = dists_map_g[mode_j]
                u, p_raw = mannwhitneyu(d_i, d_j, alternative="less")
                p_matrix_g[i, j] = p_raw

                # Store for TSV (only upper triangle to avoid duplicates)
                if i < j:
                    n_comp = n_modes * (n_modes - 1)
                    p_bonf = min(p_raw * n_comp, 1.0)
                    group_stats.append(
                        {
                            "language": lang_g,
                            "group_a": mode_i,
                            "group_b": mode_j,
                            "U": u,
                            "p_raw": p_raw,
                            "p_bonferroni": p_bonf,
                        }
                    )

        # Bonferroni correction
        n_comp_g = n_modes * (n_modes - 1)
        p_adj_g = np.where(
            np.isnan(p_matrix_g),
            np.nan,
            np.minimum(p_matrix_g * n_comp_g, 1.0),
        )

        # Significance annotations
        annot_arr_g = np.where(
            np.isnan(p_adj_g),
            "",
            np.where(
                p_adj_g < 0.001,
                "***",
                np.where(
                    p_adj_g < 0.01,
                    "**",
                    np.where(p_adj_g < 0.05, "*", ""),
                ),
            ),
        )

        # Color matrix
        color_matrix_g = np.where(
            np.isnan(p_adj_g),
            np.nan,
            np.where(
                p_adj_g < 0.001,
                0,
                np.where(
                    p_adj_g < 0.01,
                    1,
                    np.where(p_adj_g < 0.05, 2, 3),
                ),
            ),
        )

        sns.heatmap(
            color_matrix_g,
            ax=ax_g,
            xticklabels=modes_g,
            yticklabels=modes_g,
            annot=annot_arr_g,
            fmt="",
            cmap=sig_palette,
            vmin=0,
            vmax=3,
            square=True,
            cbar=False,
        )
        ax_g.set_title(ISO_REPLACEMENTS.get(lang_g, lang_g))

    # Add shared colorbar to 6th subplot
    axes_groups[5].axis("off")
    cbar_ax_g = axes_groups[5].inset_axes([0.3, 0.2, 0.4, 0.6])
    norm_g = Normalize(vmin=0, vmax=4)
    cbar_g = ColorbarBase(
        cbar_ax_g,
        cmap=sig_palette,
        norm=norm_g,
        orientation="vertical",
        ticks=[
            3 / 4 - 3 / 8,
            6 / 4 - 3 / 8,
            9 / 4 - 3 / 8,
            12 / 4 - 3 / 8,
        ],
    )
    cbar_g.ax.set_yticklabels(["*** (p<0.001)", "** (p<0.01)", "* (p<0.05)", "n.s."])
    cbar_g.set_label("Significance (row < col, Bonferroni)", rotation=270, labelpad=20)

    plt.tight_layout()

    groups_fig_path = (
        gh_figures_dir
        / "pairwise_mannwhitney_groups_chapter_by_language_bonferroni.pdf"
    )
    fig_groups.savefig(groups_fig_path, dpi=300, bbox_inches="tight")
    logger.info(f"Saved {groups_fig_path}")

    # Save statistics
    df_group_stats = pl.DataFrame(group_stats)
    groups_stats_file = gh_data_dir / "pairwise_mannwhitney_groups.tsv"
    df_group_stats.write_csv(groups_stats_file, separator="\t")
    logger.info(f"Saved {groups_stats_file}")

    return (
        annot_arr_g,
        ax_g,
        axes_groups,
        cbar_ax_g,
        cbar_g,
        chapter_by_lang_mode,
        color_matrix_g,
        d_i,
        d_j,
        df_group_stats,
        dists_map_g,
        fig_groups,
        group_stats,
        groups_fig_path,
        groups_stats_file,
        i,
        idx,
        j,
        lang_df_g,
        lang_g,
        mode_i,
        mode_j,
        modes_g,
        n_comp_g,
        n_langs,
        n_modes,
        norm_g,
        p_adj_g,
        p_bonf,
        p_matrix_g,
        p_raw,
        u,
    )


@app.cell
def _(
    LANGUAGE_ORDER,
    STRATEGY_ORDER,
    df_chapter_meta,
    gh_data_dir,
    gh_figures_dir,
    mannwhitneyu,
    np,
    pl,
    plt,
    sig_palette,
    sns,
):
    """Figure 4: Per-language pairwise heatmaps + statistics."""
    # Get annotated translations with mode information
    annotated = (
        df_chapter_meta.filter(pl.col("mode").is_not_null())
        .select(["translation_id", "full_name", "abbreviation", "language", "mode"])
        .unique()
    )

    # Aggregate chapter-level distances by language and translation
    _annotated_ids = annotated["translation_id"].unique().to_list()
    chapter_by_id = (
        df_chapter_meta.filter(pl.col("translation_id").is_in(_annotated_ids))
        .group_by("language", "translation_id")
        .agg(pl.col("dist_interlinear").implode().alias("dists"))
    )

    # Store per-translation statistics
    translation_stats = []

    for _lang_t in LANGUAGE_ORDER:
        _lang_df_t = chapter_by_id.filter(pl.col("language") == _lang_t)
        _mode_df = annotated.filter(pl.col("language") == _lang_t)

        _id_to_mode = dict(
            zip(_mode_df["translation_id"], _mode_df["mode"], strict=False)
        )
        _id_to_label = {}
        for _row in _mode_df.iter_rows(named=True):
            _tid = _row["translation_id"]
            _abbr = _row["abbreviation"]
            _fname = _row["full_name"]
            _id_to_label[_tid] = _abbr or _fname

        def _sort_key(_cid):
            _m = _id_to_mode.get(_cid)
            _pos = (
                STRATEGY_ORDER.index(_m)
                if _m in STRATEGY_ORDER
                else len(STRATEGY_ORDER)
            )
            return (_pos, _cid)

        _ids_t = sorted(_lang_df_t["translation_id"].to_list(), key=_sort_key)
        _dists_map_t = dict(
            zip(_lang_df_t["translation_id"], _lang_df_t["dists"], strict=False)
        )

        _n_t = len(_ids_t)
        _p_matrix_t = np.full((_n_t, _n_t), np.nan)

        for _i_t, _id_i in enumerate(_ids_t):
            for _j_t, _id_j in enumerate(_ids_t):
                if _i_t == _j_t:
                    continue
                _d_i_t = _dists_map_t[_id_i]
                _d_j_t = _dists_map_t[_id_j]
                _u_t, _p_raw_t = mannwhitneyu(_d_i_t, _d_j_t, alternative="less")
                _p_matrix_t[_i_t, _j_t] = _p_raw_t

                # Store for TSV (only upper triangle)
                if _i_t < _j_t:
                    _n_comp_t = _n_t * (_n_t - 1)
                    _p_bonf_t = min(_p_raw_t * _n_comp_t, 1.0)
                    translation_stats.append(
                        {
                            "language": _lang_t,
                            "translation_a": _id_i,
                            "translation_b": _id_j,
                            "U": _u_t,
                            "p_raw": _p_raw_t,
                            "p_bonferroni": _p_bonf_t,
                        }
                    )

        # Bonferroni correction
        _n_comp_t = _n_t * (_n_t - 1)
        _p_adj_t = np.where(
            np.isnan(_p_matrix_t),
            np.nan,
            np.minimum(_p_matrix_t * _n_comp_t, 1.0),
        )

        # Significance annotations
        _annot_arr_t = np.where(
            np.isnan(_p_adj_t),
            "",
            np.where(
                _p_adj_t < 0.001,
                "***",
                np.where(
                    _p_adj_t < 0.01,
                    "**",
                    np.where(_p_adj_t < 0.05, "*", ""),
                ),
            ),
        )

        # Color matrix
        _color_matrix_t = np.where(
            np.isnan(_p_adj_t),
            np.nan,
            np.where(
                _p_adj_t < 0.001,
                0,
                np.where(
                    _p_adj_t < 0.01,
                    1,
                    np.where(_p_adj_t < 0.05, 2, 3),
                ),
            ),
        )

        # Create figure
        _fig_t, _ax_t = plt.subplots(figsize=(max(6, _n_t * 0.5), max(6, _n_t * 0.5)))

        _labels_t = [_id_to_label.get(_tid, _tid) for _tid in _ids_t]

        sns.heatmap(
            _color_matrix_t,
            ax=_ax_t,
            xticklabels=_labels_t,
            yticklabels=_labels_t,
            annot=_annot_arr_t,
            fmt="",
            cmap=sig_palette,
            vmin=0,
            vmax=3,
            square=True,
            cbar_kws={
                "label": "Significance (row < col, Bonferroni)",
                "ticks": [3 / 4 - 3 / 8, 6 / 4 - 3 / 8, 9 / 4 - 3 / 8, 12 / 4 - 3 / 8],
            },
        )

        _cbar = _ax_t.collections[0].colorbar
        _cbar.ax.set_yticklabels(["*** (p<0.001)", "** (p<0.01)", "* (p<0.05)", "n.s."])

        _ax_t.set_title(f"Pairwise Mann-Whitney U tests ({_lang_t})")
        plt.xticks(rotation=45, ha="right")
        plt.yticks(rotation=0)
        plt.tight_layout()

        _lang_fig_path = (
            gh_figures_dir / f"pairwise_mannwhitney_chapter_{_lang_t}_bonferroni.pdf"
        )
        _fig_t.savefig(_lang_fig_path, dpi=300, bbox_inches="tight")
        logger.info(f"Saved {_lang_fig_path}")

        plt.close(_fig_t)

    # Save translation-level statistics
    df_translation_stats = pl.DataFrame(translation_stats)
    translation_stats_file = gh_data_dir / "pairwise_mannwhitney_translations.tsv"
    df_translation_stats.write_csv(translation_stats_file, separator="\t")
    logger.info(f"Saved {translation_stats_file}")

    return (
        annotated,
        chapter_by_id,
        df_translation_stats,
        translation_stats,
        translation_stats_file,
    )


@app.cell
def _(logger):
    """Display completion message."""
    logger.info("All figures and statistical data generated successfully!")


if __name__ == "__main__":
    app.run()
