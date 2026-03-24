# Degree Zero of Translation

**Using Interlinear Baselines to Quantify Translator Intervention**

Maciej Rapacz and Aleksander Smywiński-Pohl — AGH University of Kraków

Published at the [10th Joint SIGHUM Workshop](https://sighum.wordpress.com/events/latech-clfl-2026/) @ [EACL 2026](https://2026.eacl.org/) (Rabat, Morocco)

[📄 Paper (ACL Anthology)](https://aclanthology.org/2026.latechclfl-1.22/) · [🪧 Poster](poster/poster.pdf) · [📊 Embeddings (HuggingFace)](https://huggingface.co/datasets/mrapacz/sighum-interlinear-vector-baselines) · [📚 Targum Corpus (GitHub)](https://github.com/mrapacz/targum-corpus) · [📚 Targum Corpus (HuggingFace)](https://huggingface.co/datasets/mrapacz/targum-corpus)

---

This repository contains code, data, and poster materials for the paper *"Degree Zero of Translation: Using Interlinear Baselines to Quantify Translator Intervention"*.

We propose measuring translator intervention by computing the semantic distance between a literary translation and its interlinear (word-for-word) counterpart in embedding space. We validate this on 74 translations of the Greek New Testament across 5 languages.

## Repository Structure

```
scripts/
  00_fetch_data.py          # Download data from HuggingFace
  01_compute_vectors.py     # Compute intervention vectors + PCA
  02_generate_figures.py    # Generate all paper figures + statistics
  figures/                  # Poster figure generators
data/                       # Processed TSV files + statistical results
figures/                    # Publication-quality PDF figures
poster/
  poster.typ                # Poster source (Typst)
  poster.pdf                # Rendered poster
```

## Quick Start

All scripts are self-contained with [inline dependency metadata](https://packaging.python.org/en/latest/specifications/inline-script-metadata/) and can be run with [`uv`](https://docs.astral.sh/uv/).

```bash
# 1. Download data from HuggingFace (~360 MB)
uv run scripts/00_fetch_data.py

# 2. Compute intervention vectors and PCA
uv run scripts/01_compute_vectors.py

# 3. Generate paper figures and statistics
uv run scripts/02_generate_figures.py
```

Or use the task runner:

```bash
just fetch-data      # step 1
just reproduce       # steps 2 + 3
```

## Reproducing the Analysis

### 1. Fetch Data

```bash
uv run scripts/00_fetch_data.py
```

Downloads raw embeddings and metadata from the [HuggingFace dataset](https://huggingface.co/datasets/mrapacz/sighum-interlinear-vector-baselines) and caches them in `.cache/hf-data/`.

### 2. Compute Intervention Vectors

```bash
uv run scripts/01_compute_vectors.py
```

Computes intervention vectors (translation − interlinear baseline), Euclidean distances, and PCA projections (2D, per language). Outputs TSV files to `data/`.

### 3. Generate Figures and Statistics

```bash
uv run scripts/02_generate_figures.py
```

Generates all publication figures and statistical analyses (Mann-Whitney U tests).

### 4. Render the Poster (optional)

```bash
just render-poster
```

Compiles the Typst poster source. Fonts are downloaded automatically on first run.

## Data Files

### Processed Data

| File | Description |
|---|---|
| `data/chapter_level_intervention.tsv` | Chapter-level intervention distances per translation |
| `data/pca_projections.tsv` | PCA coordinates for intervention vectors (2D per language) |
| `data/translations_metadata.tsv` | Metadata for all 74 translations in the experiment |

### Statistical Results

| File | Description |
|---|---|
| `data/pairwise_mannwhitney_groups.tsv` | Mann-Whitney U between strategy groups (Bonferroni-corrected) |
| `data/pairwise_mannwhitney_translations.tsv` | Mann-Whitney U between individual translations (Bonferroni-corrected) |

### Figures

| File | Description |
|---|---|
| `dist_to_interlinear_by_strategy_chapter_level.pdf` | Violin plots of chapter-level distances by strategy |
| `pca_per_language.pdf` | PCA scatter plots of intervention vectors |
| `pairwise_mannwhitney_groups_chapter_by_language_bonferroni.pdf` | Strategy-group significance heatmap |
| `pairwise_mannwhitney_chapter_{lang}_bonferroni.pdf` (×5) | Per-language translation significance heatmaps |

## Raw Embeddings

The complete dataset is available on HuggingFace: **[mrapacz/sighum-interlinear-vector-baselines](https://huggingface.co/datasets/mrapacz/sighum-interlinear-vector-baselines)**

| File | Description |
|---|---|
| `embeddings_{lang}.parquet` (×5) | Raw 4096-dim chapter embeddings (Qwen3-Embedding-8B) |
| `index.parquet` | Translation metadata (name, abbreviation, year, strategy) |
| `intervention_by_chapter.parquet` | Chapter-level intervention vectors and distances |
| `intervention_summary.parquet` | Translation-level summary statistics |

These embeddings were computed from the [Targum Corpus](https://github.com/mrapacz/targum-corpus), a multilingual New Testament translation corpus with 651 translations across 5 languages.

## Citation

```bibtex
@inproceedings{rapacz-smywinski-pohl-2026-degree-zero,
    title = "Degree Zero of Translation: Using Interlinear Baselines to Quantify Translator Intervention",
    author = "Rapacz, Maciej  and
      Smywi{\'n}ski-Pohl, Aleksander",
    editor = "Alves, Diego  and
      Bizzoni, Yuri  and
      Degaetano-Ortlieb, Stefania  and
      Kazantseva, Anna  and
      Pagel, Janis  and
      Szpakowicz, Stan",
    booktitle = "Proceedings of the 10th Joint {SIGHUM} Workshop on Computational Linguistics for Cultural Heritage, Social Sciences, Humanities and Literature 2026",
    month = mar,
    year = "2026",
    address = "Rabat, Morocco",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2026.latechclfl-1.22/",
    pages = "227--240",
    ISBN = "979-8-89176-373-9",
}
```

## License

Code is released under the [MIT License](LICENSE). Data files (TSV, parquet) are released under [CC-BY 4.0](LICENSE-DATA).

