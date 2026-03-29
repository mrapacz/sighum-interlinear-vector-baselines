#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "polars>=1.0",
#     "numpy>=1.26",
#     "matplotlib>=3.8",
#     "scikit-learn>=1.4",
#     "pypdf>=4.0",
# ]
# ///
"""
Generate all PCA-interpretability figures and combine into a single PDF.

Reads pre-computed PCA projections from data/pca_projections.tsv and
translations_metadata.tsv.  Scatter plots shuffle point order to avoid
overplotting bias.

Usage:
    uv run scripts/09_interpretability_figures.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from pypdf import PdfWriter

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DATA_DIR = REPO_ROOT / "data"
CACHE_DIR = REPO_ROOT / ".cache" / "hf-data"
OUT_DIR = REPO_ROOT / "docs" / "pca-interpretability-figures"

LANGUAGES = ["pol", "spa", "ita", "eng", "fra"]
LANGUAGE_NAMES = {
    "pol": "Polish", "spa": "Spanish", "ita": "Italian",
    "eng": "English", "fra": "French",
}
STRATEGY_ORDER = ["Literal", "Formal", "Dynamic", "Paraphrase"]

GENRES = {
    "MAT": "gospel", "MRK": "gospel", "LUK": "gospel", "JHN": "gospel",
    "ACT": "acts",
    "ROM": "pauline", "1CO": "pauline", "2CO": "pauline", "GAL": "pauline",
    "EPH": "pauline", "PHP": "pauline", "COL": "pauline",
    "1TH": "pauline", "2TH": "pauline", "1TI": "pauline", "2TI": "pauline",
    "TIT": "pauline", "PHM": "pauline",
    "HEB": "hebrews",
    "JAS": "general_epistle", "1PE": "general_epistle", "2PE": "general_epistle",
    "1JN": "general_epistle", "2JN": "general_epistle", "3JN": "general_epistle",
    "JUD": "general_epistle",
    "REV": "revelation",
}

GENRE_COLORS = {
    "gospel": "#4477AA", "acts": "#66CCEE", "pauline": "#228833",
    "general_epistle": "#CCBB44", "hebrews": "#EE6677", "revelation": "#AA3377",
    "unknown": "#BBBBBB",
}

MODE_COLORS = {
    "Literal": "#117733", "Formal": "#4477AA",
    "Dynamic": "#DDCC77", "Paraphrase": "#CC6677",
}

RNG = np.random.default_rng(42)
DPI = 300
PAD = 0.1


def _shuffle_arrays(*arrays: np.ndarray) -> list[np.ndarray]:
    """Shuffle multiple arrays in unison."""
    idx = RNG.permutation(len(arrays[0]))
    return [a[idx] for a in arrays]


def _load_data() -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    pca_df = pl.read_csv(DATA_DIR / "pca_projections.tsv", separator="\t")
    meta_df = pl.read_csv(DATA_DIR / "translations_metadata.tsv", separator="\t")

    chapter_means = (
        pca_df.group_by(["language", "chapter"])
        .agg([
            pl.col("pca_x").mean().alias("mean_x"),
            pl.col("pca_y").mean().alias("mean_y"),
        ])
        .with_columns([
            (pl.col("mean_x") ** 2 + pl.col("mean_y") ** 2).sqrt().alias("dist_from_origin"),
            pl.col("chapter").str.extract(r"^(\w+)").alias("book"),
        ])
    )
    chapter_means = chapter_means.with_columns(
        pl.col("book").replace_strict(GENRES, default="unknown").alias("genre"),
    )
    return pca_df, meta_df, chapter_means


# ── Figure 01: PCA scatter colored by genre (chapter means) ──────

def fig_01_pca_scatter_by_genre(chapter_means: pl.DataFrame) -> plt.Figure:
    fig, axes = plt.subplots(1, 5, figsize=(25, 5))
    for ax, lang in zip(axes, LANGUAGES):
        ldf = chapter_means.filter(pl.col("language") == lang)
        x = ldf["mean_x"].to_numpy()
        y = ldf["mean_y"].to_numpy()
        genres = ldf["genre"].to_list()
        colors = np.array([GENRE_COLORS.get(g, "#BBBBBB") for g in genres])
        x, y, colors = _shuffle_arrays(x, y, colors)
        ax.scatter(x, y, c=colors, s=12, alpha=0.7, edgecolors="none")
        ax.axhline(0, color="grey", lw=0.5, ls="--")
        ax.axvline(0, color="grey", lw=0.5, ls="--")
        ax.set_title(LANGUAGE_NAMES[lang], fontsize=12)
        ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
        ax.set_aspect("equal")
    # Legend
    for genre, color in GENRE_COLORS.items():
        if genre != "unknown":
            axes[-1].scatter([], [], c=color, s=30, label=genre)
    axes[-1].legend(fontsize=7, loc="upper right")
    fig.suptitle("PCA scatter by genre (chapter means)", fontsize=14)
    fig.tight_layout()
    return fig


# ── Figure 02: PCA scatter all points (per-chapter, per-translation) ──

def fig_02_pca_scatter_all_points(pca_df: pl.DataFrame) -> plt.Figure:
    fig, axes = plt.subplots(1, 5, figsize=(25, 5))
    for ax, lang in zip(axes, LANGUAGES):
        ldf = pca_df.filter(pl.col("language") == lang)
        x = ldf["pca_x"].to_numpy()
        y = ldf["pca_y"].to_numpy()
        books = ldf["chapter"].str.extract(r"^(\w+)").to_list()
        genres = [GENRES.get(b, "unknown") for b in books]
        colors = np.array([GENRE_COLORS.get(g, "#BBBBBB") for g in genres])
        x, y, colors = _shuffle_arrays(x, y, colors)
        ax.scatter(x, y, c=colors, s=2, alpha=0.15, edgecolors="none")
        ax.axhline(0, color="grey", lw=0.5, ls="--")
        ax.axvline(0, color="grey", lw=0.5, ls="--")
        ax.set_title(LANGUAGE_NAMES[lang], fontsize=12)
        ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
        ax.set_aspect("equal")
    for genre, color in GENRE_COLORS.items():
        if genre != "unknown":
            axes[-1].scatter([], [], c=color, s=30, label=genre)
    axes[-1].legend(fontsize=7, loc="upper right")
    fig.suptitle("PCA scatter — all translation×chapter points", fontsize=14)
    fig.tight_layout()
    return fig


# ── Figure 03: Genre centroid arrows ──────────────────────────────

def fig_03_genre_centroid_arrows(chapter_means: pl.DataFrame) -> plt.Figure:
    fig, axes = plt.subplots(1, 5, figsize=(25, 5))
    for ax, lang in zip(axes, LANGUAGES):
        ldf = chapter_means.filter(pl.col("language") == lang)
        x = ldf["mean_x"].to_numpy()
        y = ldf["mean_y"].to_numpy()
        genres = ldf["genre"].to_list()
        colors = np.array([GENRE_COLORS.get(g, "#BBBBBB") for g in genres])
        x_s, y_s, colors_s = _shuffle_arrays(x, y, colors)
        ax.scatter(x_s, y_s, c=colors_s, s=8, alpha=0.4, edgecolors="none")
        # Genre centroids with arrows from origin
        gm = ldf.group_by("genre").agg([
            pl.col("mean_x").mean().alias("gx"),
            pl.col("mean_y").mean().alias("gy"),
        ])
        for row in gm.iter_rows(named=True):
            gc = GENRE_COLORS.get(row["genre"], "#888")
            ax.annotate("", xy=(row["gx"], row["gy"]), xytext=(0, 0),
                        arrowprops=dict(arrowstyle="->", color=gc, lw=2))
            ax.text(row["gx"], row["gy"], row["genre"], fontsize=7,
                    color=gc, fontweight="bold", ha="center", va="bottom")
        ax.axhline(0, color="grey", lw=0.5, ls="--")
        ax.axvline(0, color="grey", lw=0.5, ls="--")
        ax.set_title(LANGUAGE_NAMES[lang], fontsize=12)
        ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
        ax.set_aspect("equal")
    fig.suptitle("Genre centroid arrows from origin", fontsize=14)
    fig.tight_layout()
    return fig


# ── Figure 07: PCA scatter by translation mode ───────────────────

def fig_07_pca_scatter_by_mode(pca_df: pl.DataFrame) -> plt.Figure:
    fig, axes = plt.subplots(1, 5, figsize=(25, 5))
    for ax, lang in zip(axes, LANGUAGES):
        ldf = pca_df.filter(pl.col("language") == lang)
        x = ldf["pca_x"].to_numpy()
        y = ldf["pca_y"].to_numpy()
        modes = ldf["mode"].to_list()
        colors = np.array([MODE_COLORS.get(str(m), "#888888") for m in modes])
        x, y, colors = _shuffle_arrays(x, y, colors)
        ax.scatter(x, y, c=colors, s=2, alpha=0.15, edgecolors="none")
        ax.axhline(0, color="grey", lw=0.5, ls="--")
        ax.axvline(0, color="grey", lw=0.5, ls="--")
        ax.set_title(LANGUAGE_NAMES[lang], fontsize=12)
        ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
        ax.set_aspect("equal")
    for mode, color in MODE_COLORS.items():
        axes[-1].scatter([], [], c=color, s=30, label=mode)
    axes[-1].legend(fontsize=7, loc="upper right")
    fig.suptitle("PCA scatter by translation strategy", fontsize=14)
    fig.tight_layout()
    return fig


# ── Figure 08: English per-translation scatter ────────────────────

def fig_08_english_per_translation(pca_df: pl.DataFrame) -> plt.Figure:
    HIGHLIGHT = {
        "first-nations-version": ("FNV", "#CC3311"),
        "orthodox-jewish-bible": ("OJB", "#0077BB"),
        "complete-jewish-bible": ("CJB", "#009988"),
        "the-message-bible": ("MSG", "#EE7733"),
        "easyenglish-bible": ("EASY", "#33BBEE"),
    }
    eng = pca_df.filter(pl.col("language") == "eng")
    trans_ids = eng["translation_id"].unique().sort().to_list()

    fig, ax = plt.subplots(figsize=(8, 7))
    # Background translations first (shuffled)
    bg = eng.filter(~pl.col("translation_id").is_in(list(HIGHLIGHT.keys())))
    bx, by = bg["pca_x"].to_numpy(), bg["pca_y"].to_numpy()
    bx, by = _shuffle_arrays(bx, by)
    ax.scatter(bx, by, c="#BBBBBB", s=3, alpha=0.1, edgecolors="none")
    # Highlighted translations (each shuffled)
    for tid in trans_ids:
        if tid not in HIGHLIGHT:
            continue
        abbr, color = HIGHLIGHT[tid]
        tdf = eng.filter(pl.col("translation_id") == tid)
        tx, ty = tdf["pca_x"].to_numpy(), tdf["pca_y"].to_numpy()
        tx, ty = _shuffle_arrays(tx, ty)
        ax.scatter(tx, ty, c=color, s=6, alpha=0.3, edgecolors="none", label=abbr)
        mx, my = tdf["pca_x"].mean(), tdf["pca_y"].mean()
        ax.scatter([mx], [my], c=color, s=100, edgecolors="black",
                   linewidths=1, zorder=5, marker="D")
        ax.annotate(abbr, (mx, my), textcoords="offset points",
                    xytext=(8, 5), fontsize=9, fontweight="bold", color=color)
    ax.axhline(0, color="grey", lw=0.5, ls="--")
    ax.axvline(0, color="grey", lw=0.5, ls="--")
    ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
    ax.set_title("English: Translation outliers")
    ax.legend(fontsize=8, loc="upper left")
    ax.set_aspect("equal")
    fig.tight_layout()
    return fig


# ── Figure 09: English FNV/OJB by genre ──────────────────────────

def fig_09_english_fnv_ojb_genre(pca_df: pl.DataFrame) -> plt.Figure:
    FOCUS = {
        "first-nations-version": ("FNV", "#CC3311"),
        "orthodox-jewish-bible": ("OJB", "#0077BB"),
    }
    eng = pca_df.filter(pl.col("language") == "eng")
    fig, axes = plt.subplots(1, 2, figsize=(14, 7))
    for ax, (tid, (abbr, color)) in zip(axes, FOCUS.items()):
        tdf = eng.filter(pl.col("translation_id") == tid)
        books = tdf["chapter"].str.extract(r"^(\w+)").to_list()
        genres = [GENRES.get(b, "unknown") for b in books]
        x = tdf["pca_x"].to_numpy()
        y = tdf["pca_y"].to_numpy()
        gc = np.array([GENRE_COLORS.get(g, "#BBBBBB") for g in genres])
        x, y, gc = _shuffle_arrays(x, y, gc)
        ax.scatter(x, y, c=gc, s=15, alpha=0.6, edgecolors="none")
        ax.axhline(0, color="grey", lw=0.5, ls="--")
        ax.axvline(0, color="grey", lw=0.5, ls="--")
        ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
        ax.set_title(f"{abbr}: chapters by genre")
        ax.set_aspect("equal")
    for genre, gc in GENRE_COLORS.items():
        if genre != "unknown":
            axes[-1].scatter([], [], c=gc, s=30, label=genre)
    axes[-1].legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    return fig


# ── Figure 10: French per-translation scatter ─────────────────────

def fig_10_french_per_translation(pca_df: pl.DataFrame) -> plt.Figure:
    HIGHLIGHT = {
        "parole-de-vie": ("PDV", "#CC3311"),
        "parole-vivante": ("PVV", "#EE7733"),
        "bible-francais-courant": ("BFC", "#009988"),
        "french-king-james-bible": ("KJF", "#0077BB"),
        "segond-21": ("S21", "#AA3377"),
    }
    fra = pca_df.filter(pl.col("language") == "fra")
    trans_ids = fra["translation_id"].unique().sort().to_list()

    fig, ax = plt.subplots(figsize=(8, 7))
    bg = fra.filter(~pl.col("translation_id").is_in(list(HIGHLIGHT.keys())))
    bx, by = bg["pca_x"].to_numpy(), bg["pca_y"].to_numpy()
    bx, by = _shuffle_arrays(bx, by)
    ax.scatter(bx, by, c="#BBBBBB", s=3, alpha=0.1, edgecolors="none")
    for tid in trans_ids:
        if tid not in HIGHLIGHT:
            continue
        abbr, color = HIGHLIGHT[tid]
        tdf = fra.filter(pl.col("translation_id") == tid)
        tx, ty = tdf["pca_x"].to_numpy(), tdf["pca_y"].to_numpy()
        tx, ty = _shuffle_arrays(tx, ty)
        ax.scatter(tx, ty, c=color, s=6, alpha=0.3, edgecolors="none", label=abbr)
        mx, my = tdf["pca_x"].mean(), tdf["pca_y"].mean()
        ax.scatter([mx], [my], c=color, s=100, edgecolors="black",
                   linewidths=1, zorder=5, marker="D")
        ax.annotate(abbr, (mx, my), textcoords="offset points",
                    xytext=(8, 5), fontsize=9, fontweight="bold", color=color)
    ax.axhline(0, color="grey", lw=0.5, ls="--")
    ax.axvline(0, color="grey", lw=0.5, ls="--")
    ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
    ax.set_title("French: Translation outliers")
    ax.legend(fontsize=8, loc="lower left")
    ax.set_aspect("equal")
    fig.tight_layout()
    return fig


# ── Figure 04: Feature correlation heatmap ────────────────────────

def fig_04_feature_correlation_heatmap(
    chapter_means: pl.DataFrame,
) -> plt.Figure:
    from collections import Counter
    import re

    def compute_text_features(verses_text: str) -> dict:
        words = re.findall(r"\b\w+\b", verses_text.lower())
        sents = [s.strip() for s in re.split(r"[.!?]+", verses_text) if s.strip()]
        n_w = len(words)
        n_u = len(set(words))
        n_s = max(len(sents), 1)
        hapax = sum(1 for _, c in Counter(words).items() if c == 1)
        sent_lens = [len(re.findall(r"\b\w+\b", s)) for s in sents]
        return {
            "ttr": n_u / max(n_w, 1),
            "hapax_ratio": hapax / max(n_u, 1),
            "avg_word_length": float(np.mean([len(w) for w in words])) if words else 0.0,
            "mean_sentence_length": float(np.mean(sent_lens)) if sent_lens else 0.0,
            "words_per_verse": 0.0,  # placeholder — needs verse count
        }

    # We need the loader for interlinear text features
    try:
        from loader import Loader
        loader = Loader()
    except ImportError:
        print("  ⚠ loader not available — skipping feature correlation heatmap")
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, "Requires loader package", ha="center", va="center")
        return fig

    feature_cols = [
        "n_words", "ttr", "hapax_ratio", "avg_word_length",
        "mean_sentence_length", "words_per_verse",
    ]

    all_corrs: dict[str, dict[str, list[float]]] = {}
    for lang in LANGUAGES:
        try:
            inter = loader.interlinear_translation(lang)
        except Exception:
            continue
        corpus = inter.load_corpus()
        feat_rows = []
        for ch_verses in corpus.iter_chapters():
            if not ch_verses:
                continue
            bk = ch_verses[0].book
            cn = ch_verses[0].chapter
            key = f"{bk} {cn}"
            full = " ".join(v.text for v in ch_verses if v.text)
            words = re.findall(r"\b\w+\b", full.lower())
            sents = [s.strip() for s in re.split(r"[.!?]+", full) if s.strip()]
            n_w = len(words)
            n_u = len(set(words))
            hapax = sum(1 for _, c in Counter(words).items() if c == 1)
            sent_lens = [len(re.findall(r"\b\w+\b", s)) for s in sents]
            feat_rows.append({
                "chapter": key,
                "n_words": n_w,
                "ttr": n_u / max(n_w, 1),
                "hapax_ratio": hapax / max(n_u, 1),
                "avg_word_length": float(np.mean([len(w) for w in words])) if words else 0.0,
                "mean_sentence_length": float(np.mean(sent_lens)) if sent_lens else 0.0,
                "words_per_verse": n_w / max(len(ch_verses), 1),
            })
        fdf = pl.DataFrame(feat_rows)
        lm = chapter_means.filter(pl.col("language") == lang)
        merged = lm.join(fdf, on="chapter", how="inner")

        lang_corrs: dict[str, list[float]] = {}
        for fc in feature_cols:
            vals = merged[fc].to_numpy().astype(float)
            mx = merged["mean_x"].to_numpy()
            my = merged["mean_y"].to_numpy()
            valid = ~np.isnan(vals)
            if valid.sum() < 5:
                lang_corrs[fc] = [0.0, 0.0]
                continue
            rx = np.corrcoef(vals[valid], mx[valid])[0, 1]
            ry = np.corrcoef(vals[valid], my[valid])[0, 1]
            lang_corrs[fc] = [float(rx), float(ry)]
        all_corrs[lang] = lang_corrs

    # Build heatmap matrix: rows = features, cols = lang×PC
    col_labels = []
    for lang in LANGUAGES:
        if lang in all_corrs:
            col_labels.extend([f"{LANGUAGE_NAMES[lang]} PC1", f"{LANGUAGE_NAMES[lang]} PC2"])
    matrix = []
    for fc in feature_cols:
        row = []
        for lang in LANGUAGES:
            if lang in all_corrs:
                row.extend(all_corrs[lang].get(fc, [0.0, 0.0]))
        matrix.append(row)

    fig, ax = plt.subplots(figsize=(12, 5))
    im = ax.imshow(matrix, cmap="RdBu_r", vmin=-0.6, vmax=0.6, aspect="auto")
    ax.set_xticks(range(len(col_labels)))
    ax.set_xticklabels(col_labels, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(feature_cols)))
    ax.set_yticklabels(feature_cols, fontsize=9)
    for i in range(len(feature_cols)):
        for j in range(len(col_labels)):
            ax.text(j, i, f"{matrix[i][j]:.2f}", ha="center", va="center", fontsize=7)
    plt.colorbar(im, ax=ax, label="Pearson r")
    ax.set_title("Surface feature correlation with PCA coordinates")
    fig.tight_layout()
    return fig


# ── Figure 05: Probe alignment heatmap ────────────────────────────

def fig_05_probe_alignment_heatmap(pca_df: pl.DataFrame) -> plt.Figure:
    from sklearn.decomposition import PCA
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score

    probe_definitions = {
        "is_pauline": lambda b: 1 if GENRES.get(b) == "pauline" else 0,
        "is_revelation": lambda b: 1 if GENRES.get(b) == "revelation" else 0,
        "is_gospel": lambda b: 1 if GENRES.get(b) == "gospel" else 0,
        "is_epistle": lambda b: 1 if GENRES.get(b) in ("pauline", "general_epistle", "hebrews") else 0,
        "is_narrative": lambda b: 1 if GENRES.get(b) in ("gospel", "acts") else 0,
        "is_apocalyptic": lambda b: 1 if GENRES.get(b) in ("revelation", "hebrews") else 0,
    }

    # Recompute PCA from raw embeddings
    pca_objects = {}
    intervention_data = {}
    for lang in LANGUAGES:
        emb_path = CACHE_DIR / f"embeddings_{lang}.parquet"
        if not emb_path.exists():
            continue
        df = pl.read_parquet(emb_path)
        inter_ids = [tid for tid in df["translation_id"].unique().to_list() if "interlinear" in tid]
        if not inter_ids:
            continue
        inter_id = inter_ids[0]
        inter_df = df.filter(pl.col("translation_id") == inter_id)
        inter_vecs = {r["key"]: np.array(r["vector"]) for r in inter_df.iter_rows(named=True)}
        inter_mean = np.mean(list(inter_vecs.values()), axis=0)

        non_inter = df.filter(pl.col("translation_id") != inter_id)
        vecs, keys = [], []
        for r in non_inter.iter_rows(named=True):
            if r["key"] in inter_vecs:
                iv = r["key"]
                vecs.append(np.array(r["vector"]) - inter_vecs[iv])
                keys.append(r["key"])
        vecs = np.array(vecs)
        zeros = np.zeros_like(vecs[:len(inter_vecs)])
        combined = np.vstack([vecs, zeros])
        pca = PCA(n_components=2)
        pca.fit(combined)
        pca_objects[lang] = pca
        intervention_data[lang] = {"vectors": vecs, "keys": keys, "interlinear_mean": inter_mean}

    probe_names = list(probe_definitions.keys())
    col_labels = []
    for lang in LANGUAGES:
        if lang in pca_objects:
            col_labels.extend([f"{LANGUAGE_NAMES[lang]} PC1", f"{LANGUAGE_NAMES[lang]} PC2"])

    matrix = []
    for pname in probe_names:
        row = []
        pfn = probe_definitions[pname]
        for lang in LANGUAGES:
            if lang not in pca_objects:
                continue
            data = intervention_data[lang]
            vecs = data["vectors"]
            books = [k.split()[0] for k in data["keys"]]
            y = np.array([pfn(b) for b in books])
            pca = pca_objects[lang]
            pc1, pc2 = pca.components_[0], pca.components_[1]

            if y.sum() < 10 or (len(y) - y.sum()) < 10:
                row.extend([0.0, 0.0])
                continue
            clf = LogisticRegression(max_iter=1000, C=1.0, solver="lbfgs")
            clf.fit(vecs, y)
            w = clf.coef_[0]
            proj1 = np.dot(w, pc1) / (np.linalg.norm(w) * np.linalg.norm(pc1))
            proj2 = np.dot(w, pc2) / (np.linalg.norm(w) * np.linalg.norm(pc2))
            row.extend([abs(float(proj1)), abs(float(proj2))])
        matrix.append(row)

    fig, ax = plt.subplots(figsize=(12, 5))
    im = ax.imshow(matrix, cmap="YlOrRd", vmin=0, vmax=0.8, aspect="auto")
    ax.set_xticks(range(len(col_labels)))
    ax.set_xticklabels(col_labels, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(probe_names)))
    ax.set_yticklabels(probe_names, fontsize=9)
    for i in range(len(probe_names)):
        for j in range(len(col_labels)):
            ax.text(j, i, f"{matrix[i][j]:.2f}", ha="center", va="center", fontsize=7)
    plt.colorbar(im, ax=ax, label="|cos alignment|")
    ax.set_title("Probe weight → PCA axis alignment")
    fig.tight_layout()
    return fig


# ── Main ──────────────────────────────────────────────────────────

FIGURE_ORDER = [
    ("01_pca_scatter_by_genre.pdf", fig_01_pca_scatter_by_genre),
    ("02_pca_scatter_all_points.pdf", fig_02_pca_scatter_all_points),
    ("03_genre_centroid_arrows.pdf", fig_03_genre_centroid_arrows),
    ("07_pca_scatter_by_mode.pdf", fig_07_pca_scatter_by_mode),
    ("08_english_per_translation.pdf", fig_08_english_per_translation),
    ("09_english_fnv_ojb_genre.pdf", fig_09_english_fnv_ojb_genre),
    ("10_french_per_translation.pdf", fig_10_french_per_translation),
    ("04_feature_correlation_heatmap.pdf", fig_04_feature_correlation_heatmap),
    ("05_probe_alignment_heatmap.pdf", fig_05_probe_alignment_heatmap),
]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pca_df, meta_df, chapter_means = _load_data()

    # Dispatch table: figure functions that need different args
    needs_chapter_means = {"fig_01", "fig_03", "fig_04"}
    needs_pca_df = {"fig_02", "fig_07", "fig_08", "fig_09", "fig_10", "fig_05"}

    saved_paths = []
    for name, func in FIGURE_ORDER:
        print(f"  Generating {name}...")
        fname = func.__name__
        if "chapter_means" in fname or fname in (
            "fig_01_pca_scatter_by_genre",
            "fig_03_genre_centroid_arrows",
        ):
            fig = func(chapter_means)
        elif fname == "fig_04_feature_correlation_heatmap":
            fig = func(chapter_means)
        else:
            fig = func(pca_df)
        out_path = OUT_DIR / name
        fig.savefig(out_path, bbox_inches="tight", pad_inches=PAD, dpi=DPI)
        plt.close(fig)
        saved_paths.append(out_path)

    # Combine into single PDF
    print("\n  Combining into single PDF...")
    writer = PdfWriter()
    for p in saved_paths:
        writer.append(str(p))
    combined = OUT_DIR / "combined_interpretability_figures.pdf"
    writer.write(str(combined))
    writer.close()
    print(f"  ✓ {combined}")


if __name__ == "__main__":
    main()
