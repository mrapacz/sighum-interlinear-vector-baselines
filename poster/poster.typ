// Poster: Degree Zero of Translation
// SigHum @ EACL 2026, Rabat
// Layout: Asymmetric two-column (35% text / 65% evidence)
// Format: A0 portrait (841 × 1189 mm)

// === PALETTE (from TOML) ===
#let palette-path = sys.inputs.at("palette", default: "/palettes/current.toml")
#let pal = toml(palette-path)

#let bg             = rgb(pal.surface.background)
#let panel-bg       = rgb(pal.surface.panel)
#let text-primary   = rgb(pal.text.heading)
#let text-secondary = rgb(pal.text.body)
#let text-tertiary  = rgb(pal.text.caption)
#let rule-color     = rgb(pal.text.rule)
#let accent         = rgb(pal.accent.primary)
#let callout-bg     = panel-bg

// === PAGE SETUP ===
#set page(
  width: 841mm,
  height: 1189mm,
  margin: (top: 40mm, bottom: 20mm, left: 40mm, right: 40mm),
  fill: bg,
)

// === FONTS ===
#let sans-font = "DM Sans"
#let serif-font = "Newsreader"

#set text(font: sans-font, size: 24pt, fill: text-primary)

// === HELPERS ===
#let section-label(body) = {
  text(
    font: sans-font,
    size: 18pt,
    weight: "bold",
    fill: text-secondary,
    tracking: 2pt,
    upper(body)
  )
}

#let thin-rule() = {
  line(length: 100%, stroke: 0.5pt + rule-color)
}

#let stat-number(num) = {
  text(font: sans-font, size: 56pt, weight: "bold", fill: text-primary, num)
}

#let stat-caption(body) = {
  text(size: 20pt, fill: text-secondary, body)
}

// ============================================================
// TITLE BLOCK (full width) — text left, QR right
// ============================================================
#grid(
  columns: (1fr, auto),
  gutter: 12mm,
  align: (left + horizon, right + horizon),

  // Left: title text
  [
    #text(
      font: sans-font,
      size: 85pt,
      weight: "bold",
      fill: text-primary,
      [The translator's signal, measured]
    )

    #text(
      font: sans-font,
      size: 44pt,
      fill: text-secondary,
      [Degree Zero of Translation: Using Interlinear Baselines \ to Quantify Translator Intervention]
    )

    #text(
      size: 24pt,
      fill: text-secondary,
      [*Maciej Rapacz* · *Aleksander Smywiński-Pohl*]
    )

    #text(
      size: 22pt,
      fill: text-secondary,
      [AGH University of Kraków]
    )
  ],

  // Right: QR code
  [
    #image("../figures/poster/qr.png", width: 100mm)
    #align(center, text(size: 22pt, fill: text-secondary)[mrapacz.com/eacl2026])
  ],
)

#v(6mm)
#thin-rule()
#v(6mm)

// ============================================================
// MAIN BODY: ASYMMETRIC TWO-COLUMN
// ============================================================

#let text-rail-width = 35%
#let gutter = 5%
#let evidence-rail-width = 60%

#grid(
  columns: (text-rail-width, gutter, evidence-rail-width),
  gutter: 0mm,

  // ===================== LEFT COLUMN: TEXT RAIL =====================
  [
    // --- BACKGROUND ---
    #section-label[Background]
    #v(6mm)

    Literary translation is an act of rewriting: every translator restructures, shifts meaning, and adapts style. Translation studies classifies these choices qualitatively — literal, formal, dynamic, paraphrase — but existing approaches lack a scalable method to measure how far a translation departs from its source.

    #v(8mm)
    #thin-rule()
    #v(8mm)

    // --- METHOD ---
    #section-label[Method]
    #v(6mm)

    An interlinear translation — a word-for-word gloss preserving source syntax — serves as our baseline of zero intervention. We embed each chapter of a translation and its interlinear counterpart using Qwen3-Embedding-8B, then compute the Intervention Vector:

    #v(6mm)

    #align(center,
      text(font: sans-font, size: 32pt, fill: text-primary,
        [$ bold(V)_"intervention" = bold(V)_"translation" - bold(V)_"interlinear" $]
      )
    )

    #v(6mm)

    Its magnitude (L2 norm) measures the extent of departure: small for literal renderings, large for paraphrases.

    #v(8mm)
    #thin-rule()
    #v(8mm)

    // --- DATASET ---
    #section-label[Dataset]
    #v(6mm)

    74 New Testament translations from the _targum_ corpus, across 5 languages, each aligned chapter-by-chapter (260 chapters) with a language-specific interlinear baseline.

    #v(6mm)

    #set text(size: 20pt)
    #align(center, block(width: 80%,
      table(
        columns: (1fr, auto, auto, auto, auto, auto),
        align: (left, center, center, center, center, center),
        stroke: none,
        inset: (x: 6pt, y: 5pt),
        table.hline(stroke: 0.5pt + rule-color),
        [*Language*], [*Literal*], [*Formal*], [*Dynamic*], [*Paraphrastic*], [*Total*],
        table.hline(stroke: 0.5pt + rule-color),
        [English],  [3], [4], [7], [2], [16],
        [French],   [1], [6], [4], [3], [14],
        [Italian],  [4], [4], [2], [2], [12],
        [Polish],   [4], [7], [2], [3], [16],
        [Spanish],  [3], [2], [5], [6], [16],
        table.hline(stroke: 0.5pt + rule-color),
        [*Total*],  [*15*], [*23*], [*20*], [*16*], [*74*],
        table.hline(stroke: 0.5pt + rule-color),
      )
    ))
    #set text(size: 24pt)

    #v(8mm)
    #thin-rule()
    #v(8mm)

    // --- KEY CONTRIBUTION (callout box) ---
    #block(
      width: 100%,
      inset: 16pt,
      radius: 4pt,
      stroke: 1pt + accent,
      fill: callout-bg,
      {
        section-label[Key contribution]
        v(6mm)
        text(size: 22pt, fill: text-primary)[
          An unsupervised, reference-free method that recovers the translation strategy spectrum using interlinear translation as baseline.
        ]
      }
    )

    #v(8mm)
    #thin-rule()
    #v(8mm)

    // --- KEY FINDINGS ---
    #section-label[Key findings]
    #v(8mm)

    // Finding 1
    #text(size: 20pt, weight: "bold", fill: accent)[Spectrum recovery]
    #v(4mm)
    Across all 5 languages, literal and formal strategies yield significantly shorter vectors than dynamic and paraphrase. In English and French, all four groups separate fully ($p < 0.001$).

    #v(12mm)
    #thin-rule()
    #v(12mm)

    // Finding 2
    #text(size: 20pt, weight: "bold", fill: accent)[Pairwise sensitivity]
    #v(4mm)
    At the individual translation level, 87% of English pairs show significant differences in intervention magnitude (63% French, 41% Polish, 36% Italian, 35% Spanish).

    #v(12mm)
    #thin-rule()
    #v(12mm)

    // Finding 3
    #text(size: 20pt, weight: "bold", fill: accent)[Topology]
    #v(4mm)
    PCA projections reveal that translations with similar magnitude can depart in different directions. In English, the First Nations Version and the Orthodox Jewish Bible both show high intervention but along orthogonal axes — one domesticating, the other foreignizing:

    #v(4mm)
    #text(size: 20pt, fill: text-secondary)[Acts 17:33]
    #v(2mm)
    _Interlinear: Thus Paul went out from the midst of them_ \
    _FNV: So Small Man went on his way._ \
    _OJB: Thus did Rav Sha'ul go out from the midst of them._
  ],

  // ===================== GUTTER =====================
  [],

  // ===================== RIGHT COLUMN: EVIDENCE RAIL =====================
  [
    // --- THE TRANSLATION SPECTRUM ---
    #section-label[The translation spectrum]
    #v(2mm)

    The same verse at four levels of intervention:

    #v(2mm)

    #image("../figures/poster/translation_diagram.pdf", width: 100%)

    #v(6mm)
    #thin-rule()
    #v(6mm)

    // --- VIOLIN / RIDGELINE PLOT ---
    #section-label[Distribution of intervention magnitudes]
    #v(3mm)

    The intervention magnitude increases along the expected spectrum from literal to paraphrase:

    #v(2mm)
    #image("../figures/poster/figure-ridgeline.pdf", width: 100%)

    #v(2mm)
    #text(size: 18pt, fill: text-secondary)[Distribution of $||bold(V)_"intervention"||$ per strategy group. Literal strategies cluster low; paraphrases extend further.]

    #v(6mm)
    #thin-rule()
    #v(6mm)

    // --- SIGNIFICANCE HEATMAPS ---
    #section-label[Pairwise significance]
    #v(3mm)

    At the level of individual translations, most pairs show significant differences in intervention magnitude:

    #v(2mm)
    #image("../figures/poster/figure-heatmaps.pdf", width: 100%)

    #v(2mm)
    #text(size: 18pt, fill: text-secondary)[Mann–Whitney U (one-sided, Bonferroni-corrected). Color intensity indicates significance level.]

    #v(6mm)
    #thin-rule()
    #v(6mm)

    // --- PCA PROJECTIONS ---
    #section-label[Topology of intervention]
    #v(3mm)

    Projecting the intervention vectors onto a plane reveals that direction, not just magnitude, varies across translations:

    #v(2mm)
    #image("../figures/poster/figure-pca.pdf", width: 100%)

    #v(2mm)
    #text(size: 18pt, fill: text-secondary)[PCA of intervention vectors. Baseline at origin. FNV and OJB depart along orthogonal axes.]
  ],
)

// ============================================================
// FOOTER
// ============================================================
#v(1fr) // push footer to bottom

#thin-rule()

#v(4mm)
#grid(
  columns: (1fr, auto),
  gutter: 16mm,
  align: (left + horizon, right + horizon),

  // Left: acknowledgment text + conference info
  [
    #text(size: 16pt, fill: text-secondary)[
      The research was supported by the National Science Centre, Poland under the project number 2025/57/N/HS2/04961.
    ]
    #v(2mm)
    #text(size: 16pt, fill: text-secondary)[
      We gratefully acknowledge Polish high-performance computing infrastructure PLGrid (HPC Center: ACK Cyfronet AGH) for providing computer facilities and support within computational grant no. PLG/2026/019145.
    ]
    #v(4mm)
    #text(size: 16pt, weight: "bold", fill: text-secondary)[
      SIGHUM \@ EACL 2026 · Rabat, Morocco · March 28–29, 2026
    ]
  ],

  // Right: logos side by side
  [
    #box(image("../assets/AGH-logotype.jpg", height: 24mm))
    #h(12mm)
    #box(image("../assets/PLGrid-logotype.png", height: 24mm))
    #h(12mm)
    #box(image("../assets/NCN-logotype.png", height: 24mm))
  ],
)
