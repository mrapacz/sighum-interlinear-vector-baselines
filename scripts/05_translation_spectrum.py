#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "matplotlib>=3.8",
#     "polars>=1.0",
#     "pyarrow>=15.0",
#     "loguru>=0.7",
# ]
# ///
"""
Translation Spectrum Figure for Academic Poster
================================================
Renders a Greek source verse with interlinear gloss and ranked translations,
grouped by translation philosophy (literal → paraphrastic).

To swap the verse, edit the DATA dict at the bottom of the constants section.

Font notes:
    - Install DM Sans (https://fonts.google.com/specimen/DM+Sans) for the
      sans-serif labels. If missing, matplotlib falls back to its default sans.
    - GFS Porson ships with texlive / is available at
      https://www.greekfontsociety-gfs.gr/typefaces/GFS_Porson
    - TeX Gyre Pagella ships with texlive or install from GUST.
"""

import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", message="Glyph .* missing from font")
warnings.filterwarnings("ignore", message="findfont: Font family.*not found")

import logging

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

from figures import POSTER_BG, TEXT_BODY, TEXT_CAPTION, TEXT_HEADING, TEXT_RULE

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FONT FAMILIES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Change these to match what's installed on your system.
# The SANS_FONT is used for all UI chrome (labels, scores, group headings).
# The SERIF_FONT is used for the English translation text.
# The GREEK_FONT is used for the polytonic Greek source.

SANS_FONT = "DM Sans"  # poster sans-serif (labels, scores, groups)
SERIF_FONT = "TeX Gyre Pagella"  # translation text (Palatino-like)
GREEK_FONT = "GFS Porson"  # polytonic Greek source text

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FONT SIZES (pt)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Sized to match poster.typ conventions (A0 poster, ~1 m reading distance).
#   fs-body-lg  = 28pt   (Greek source, spectrum body)
#   fs-body     = 24pt   (standard body — translation text)
#   fs-body-sm  = 22pt   (abbreviations, scores)
#   fs-caption  = 20pt   (glosses)
#   fs-caption-sm = 18pt (group headers, column headers, source label)

GREEK_SIZE = 28  # Greek source words          (fs-body-lg)
GLOSS_SIZE = 20  # interlinear English glosses  (fs-caption)
TRANSLATION_SIZE = 24  # English translation text     (fs-body)
ABBREV_SIZE = 22  # translation abbreviation     (fs-body-sm)
SCORE_SIZE = 22  # distance score values        (fs-body-sm)
GROUP_LABEL_SIZE = 18  # group category headers       (fs-caption-sm)
HEADER_SIZE = 18  # column header ("Dist.")      (fs-caption-sm)
SOURCE_LABEL_SIZE = 18  # top-line source citation     (fs-caption-sm)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COLORS (aligned with poster palette from figures/__init__.py)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TEXT_PRIMARY = TEXT_HEADING  # Greek source, translation text
TEXT_SECONDARY = TEXT_BODY  # glosses
TEXT_TERTIARY = TEXT_CAPTION  # labels, scores, group headings
RULE_COLOR = TEXT_RULE  # horizontal rules
GROUP_RULE_COLOR = TEXT_RULE  # thin rules between groups

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIGURE DIMENSIONS & SCALING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WIDTH_SCALE = 1.0
HEIGHT_SCALE = 1.0
FIG_WIDTH = 16  # base figure width in inches (scaled by WIDTH_SCALE)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HORIZONTAL LAYOUT (x-axis, in 0–1 figure coords)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LEFT_MARGIN = 0.04  # left edge of content
ABBREV_X = 0.04  # left-align anchor for abbreviations
TEXT_X = 0.14  # left edge of translation text
SCORE_X = 0.96  # right-align anchor for scores

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VERTICAL SPACING (in inches — directly maps to y-axis)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SOURCE_LABEL_TOP_PAD = (
    0.25  # space above the source label (positive = pushes content down)
)
SOURCE_LABEL_TO_GREEK = 0.6  # gap between source label and Greek text
GREEK_TO_GLOSS = 0.42  # vertical distance: Greek baseline → gloss baseline
GLOSS_TO_RULE = 0.30  # gap below glosses to the horizontal rule
RULE_TO_DIST_HEADER = 0.30  # gap below rule to "Dist." column header
DIST_HEADER_TO_FIRST_GROUP = 0.10  # gap below "Dist." to first group label
GROUP_LABEL_HEIGHT = 0.35  # vertical space consumed by a group label row
TX_ROW_HEIGHT = 0.48  # vertical space consumed by a translation row
GROUP_GAP = 0.12  # extra vertical gap between groups
BOTTOM_PAD = 0.15  # padding below last translation
MAIN_RULE_WIDTH = 1.5  # stroke width of the main horizontal rule
GROUP_RULE_WIDTH = 0.8  # stroke width of inter-group rules
SAVE_PAD_INCHES = 0.10  # padding around figure when saving
SAVE_DPI = 300  # output resolution

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATA — edit this section to swap the verse
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DATA = {
    "reference": "Matthew 13:9",
    "source_edition": "SBLGNT",
    # Interlinear: list of (greek_word, english_gloss) pairs
    "interlinear": [
        ("ὁ", "The [one]"),
        ("ἔχων", "having"),
        ("ὦτα", "ears"),
        ("ἀκουέτω", "let him hear"),
    ],
    # Groups: list of (group_name, [(abbreviation, full_text, score), ...])
    # Each group can contain multiple translations.
    # Scores are embedding-based intervention vector magnitudes
    # (L2 distance to interlinear, Qwen3-Embedding-8B, verse-level)
    "groups": [
        (
            "Literal",
            [
                ("DLNT", 'Let the one having ears, hear".', 0.547),
            ],
        ),
        (
            "Formal",
            [
                ("NRSVue", 'Let anyone with ears listen!"', 0.647),
            ],
        ),
        (
            "Dynamic",
            [
                (
                    "NLT",
                    'Anyone with ears to hear should listen and understand."',
                    0.656,
                ),
            ],
        ),
        (
            "Paraphrastic",
            [
                (
                    "MSG",
                    '"Are you listening to this? Really listening?"',
                    0.903,
                ),
            ],
        ),
    ],
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RENDERING — no magic numbers below this line
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _build_fonts():
    """Construct FontProperties objects from the constants above."""
    return {
        "greek": FontProperties(family=GREEK_FONT, size=GREEK_SIZE),
        "gloss": FontProperties(family=SANS_FONT, size=GLOSS_SIZE, style="italic"),
        "translation": FontProperties(family=SERIF_FONT, size=TRANSLATION_SIZE),
        "abbrev": FontProperties(family=SANS_FONT, size=ABBREV_SIZE),
        "score": FontProperties(family=SANS_FONT, size=SCORE_SIZE),
        "group_label": FontProperties(
            family=SANS_FONT, size=GROUP_LABEL_SIZE, weight="bold"
        ),
        "header": FontProperties(family=SANS_FONT, size=HEADER_SIZE),
        "source_label": FontProperties(family=SANS_FONT, size=SOURCE_LABEL_SIZE),
    }


def _compute_height(data):
    """Calculate total figure height in inches from the data and spacing constants."""
    n_rows = sum(len(txs) for _, txs in data["groups"])
    n_groups = len(data["groups"])

    return (
        SOURCE_LABEL_TOP_PAD
        + SOURCE_LABEL_TO_GREEK
        + GREEK_TO_GLOSS
        + GLOSS_TO_RULE
        + RULE_TO_DIST_HEADER
        + DIST_HEADER_TO_FIRST_GROUP
        + n_groups * GROUP_LABEL_HEIGHT
        + n_rows * TX_ROW_HEIGHT
        + max(0, n_groups - 1) * GROUP_GAP
        + BOTTOM_PAD
    )


def render_figure(data=DATA):
    """
    Render the translation spectrum figure and return the Figure object.

    Parameters
    ----------
    data : dict
        Verse data in the format of the DATA constant above.

    Returns
    -------
    matplotlib.figure.Figure

    """
    fonts = _build_fonts()
    total_h = _compute_height(data)

    fig, ax = plt.subplots(figsize=(FIG_WIDTH * WIDTH_SCALE, total_h * HEIGHT_SCALE))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, total_h)
    ax.axis("off")

    # Background
    fig.patch.set_facecolor(POSTER_BG)
    ax.set_facecolor(POSTER_BG)

    y = total_h  # cursor starts at top

    # ── Source label ──────────────────────────
    y -= SOURCE_LABEL_TOP_PAD
    ax.text(
        LEFT_MARGIN,
        y,
        f"Greek source  ·  {data['source_edition']}  ·  {data['reference']}",
        fontproperties=fonts["source_label"],
        color=TEXT_TERTIARY,
        va="top",
        ha="left",
    )

    # ── Interlinear: Greek + gloss ───────────
    y -= SOURCE_LABEL_TO_GREEK

    pairs = data["interlinear"]
    n_words = len(pairs)
    avail_width = SCORE_X - LEFT_MARGIN
    col_width = avail_width / n_words

    greek_y = y
    gloss_y = greek_y - GREEK_TO_GLOSS

    for i, (greek, gloss) in enumerate(pairs):
        cx = LEFT_MARGIN + col_width * (i + 0.5)

        ax.text(
            cx,
            greek_y,
            greek,
            fontproperties=fonts["greek"],
            color=TEXT_PRIMARY,
            va="center",
            ha="center",
        )
        ax.text(
            cx,
            gloss_y,
            gloss,
            fontproperties=fonts["gloss"],
            color=TEXT_SECONDARY,
            va="center",
            ha="center",
        )

    y = gloss_y

    # ── Main horizontal rule ─────────────────
    y -= GLOSS_TO_RULE
    ax.plot(
        [LEFT_MARGIN, SCORE_X],
        [y, y],
        color=RULE_COLOR,
        linewidth=MAIN_RULE_WIDTH,
        solid_capstyle="round",
    )

    # ── "Dist." column header ────────────────
    y -= RULE_TO_DIST_HEADER
    ax.text(
        SCORE_X,
        y,
        "Dist.",
        fontproperties=fonts["header"],
        color=TEXT_TERTIARY,
        va="center",
        ha="right",
    )

    y -= DIST_HEADER_TO_FIRST_GROUP

    # ── Groups and translation rows ──────────
    for gi, (group_name, translations) in enumerate(data["groups"]):
        # Inter-group separator (skip before first group)
        if gi > 0:
            y -= GROUP_GAP * 0.4
            ax.plot(
                [LEFT_MARGIN, SCORE_X],
                [y, y],
                color=GROUP_RULE_COLOR,
                linewidth=GROUP_RULE_WIDTH,
                solid_capstyle="round",
            )
            y -= GROUP_GAP * 0.6

        # Group label
        y -= GROUP_LABEL_HEIGHT * 0.55
        ax.text(
            LEFT_MARGIN,
            y,
            group_name.upper(),
            fontproperties=fonts["group_label"],
            color=TEXT_TERTIARY,
            va="center",
            ha="left",
        )
        y -= GROUP_LABEL_HEIGHT * 0.45

        # Translation rows within this group
        for abbrev, text, score in translations:
            y -= TX_ROW_HEIGHT * 0.5

            ax.text(
                ABBREV_X,
                y,
                abbrev,
                fontproperties=fonts["abbrev"],
                color=TEXT_TERTIARY,
                va="center",
                ha="left",
            )
            ax.text(
                TEXT_X,
                y,
                text,
                fontproperties=fonts["translation"],
                color=TEXT_PRIMARY,
                va="center",
                ha="left",
            )
            ax.text(
                SCORE_X,
                y,
                f"{score:.3f}",
                fontproperties=fonts["score"],
                color=TEXT_TERTIARY,
                va="center",
                ha="right",
            )

            y -= TX_ROW_HEIGHT * 0.5

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    return fig


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    fig = render_figure()

    out_dir = Path(__file__).resolve().parent.parent / "figures" / "poster"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "translation_diagram.pdf"

    fig.savefig(out_path, bbox_inches="tight", pad_inches=SAVE_PAD_INCHES, dpi=SAVE_DPI)
    fig.savefig(
        out_path.with_suffix(".png"),
        bbox_inches="tight",
        pad_inches=SAVE_PAD_INCHES,
        dpi=SAVE_DPI,
    )

    from loguru import logger

    logger.info(f"Saved {out_path} (+.png)")
    plt.close(fig)
