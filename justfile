# SIGHUM 2026 — reproducibility scripts and poster

# Display available recipes
default:
    @just --list

# Set up development environment
dev:
    uv sync
    uv run prek install
    @echo "Development environment ready!"

# Run linters on all files
lint:
    uv run prek run --all-files

# Clean up generated files
clean:
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
    rm -rf .git/hooks/pre-commit

### DATA ###

# Download data from HuggingFace (~360 MB)
fetch-data *args:
    uv run scripts/00_fetch_data.py {{args}}

### PAPER FIGURES ###

# Reproduce the full analysis (compute vectors + generate figures)
reproduce:
    @echo "Running processing pipeline..."
    uv run scripts/01_compute_vectors.py
    uv run scripts/02_generate_figures.py
    @echo "Pipeline complete!"

# Compute intervention vectors from raw embeddings
compute-vectors:
    uv run scripts/01_compute_vectors.py

# Generate paper figures from precomputed data
generate-figures:
    uv run scripts/02_generate_figures.py

### POSTER ###

# Download poster fonts (DM Sans + Newsreader) if not present
fetch-fonts:
    #!/usr/bin/env bash
    set -euo pipefail
    font_dir=".cache/fonts"
    if [[ -d "$font_dir" ]] && ls "$font_dir"/*.ttf &>/dev/null; then
        echo "Fonts already present in $font_dir"
        exit 0
    fi
    mkdir -p "$font_dir"
    echo "Downloading DM Sans..."
    curl -sL "https://fonts.google.com/download?family=DM+Sans" -o /tmp/dm-sans.zip
    unzip -qo /tmp/dm-sans.zip -d /tmp/dm-sans
    find /tmp/dm-sans -name "*.ttf" ! -name "*Italic*" -exec cp {} "$font_dir/" \;
    rm -rf /tmp/dm-sans /tmp/dm-sans.zip
    echo "Downloading Newsreader..."
    curl -sL "https://fonts.google.com/download?family=Newsreader" -o /tmp/newsreader.zip
    unzip -qo /tmp/newsreader.zip -d /tmp/newsreader
    find /tmp/newsreader -name "*.ttf" ! -name "*Italic*" -exec cp {} "$font_dir/" \;
    rm -rf /tmp/newsreader /tmp/newsreader.zip
    echo "Fonts downloaded to $font_dir"

# Generate poster figures (violin+strip, heatmaps, PCA)
generate-poster-figures:
    cd scripts && uv run -m figures

# ── Individual figure recipes ──

# Render: violin plots (all 5 languages — subfigures + assembled)
render-figure-violins:
    cd scripts && uv run figures/fig_violin_strip.py

# Render: PCA scatter plots (all 5 languages — subfigures + assembled)
render-figure-pca:
    cd scripts && uv run figures/fig_pca.py

# Render: pairwise significance heatmaps (EN large left + 4 small right)
render-figure-heatmaps:
    cd scripts && uv run figures/fig_heatmaps.py

# Render: group-level significance heatmaps (subfigures + assembled row)
render-figure-group-heatmaps:
    cd scripts && uv run figures/fig_group_heatmaps.py

# Render: ridgeline plots (all 5 languages — subfigures + assembled)
render-figure-ridgeline:
    cd scripts && uv run figures/fig_ridgeline.py

# Render translation diagram figure (interlinear + ranked translations)
render-diagram-translation-spectrum:
    uv run scripts/05_translation_spectrum.py

# Render poster (regenerates all figures + compiles Typst)
# Usage:
#   just render-poster                   use palettes/current.toml
#   just render-poster --just-pdf        skip figure regeneration
render-poster *args: fetch-fonts
    #!/usr/bin/env bash
    set -euo pipefail
    rest_args=()
    just_pdf=false
    for arg in {{args}}; do
        if [[ "$arg" == "--just-pdf" ]]; then
            just_pdf=true
        else
            rest_args+=("$arg")
        fi
    done
    export POSTER_PALETTE="palettes/current.toml"
    if [[ "$just_pdf" == "false" ]]; then
        (cd scripts && uv run -m figures)
        uv run scripts/05_translation_spectrum.py
        uv run scripts/06_render_qr_code.py
    fi
    typst compile poster/poster.typ poster/poster.pdf \
        --root . --font-path .cache/fonts/ \
        --input palette="/palettes/current.toml" "${rest_args[@]}"
    typst compile poster/poster.typ poster/poster-grid.pdf \
        --root . --font-path .cache/fonts/ \
        --input grid=true --input palette="/palettes/current.toml" "${rest_args[@]}"
    echo "Poster → poster/poster.pdf"
    echo "Poster (grid) → poster/poster-grid.pdf"

# Generate QR code for the poster
render-qr-code *args:
    uv run scripts/06_render_qr_code.py {{args}}
