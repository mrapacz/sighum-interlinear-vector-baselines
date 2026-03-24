// ============================================================
// Poster: "Degree Zero of Translation"
// LREC-COLING 2026 — A0 Portrait (841mm × 1189mm)
// ============================================================
//
// All constants live in the config block below — no hardcoded
// values in the content section.  Edit constants to iterate.
//
// Compile:
//   just typst-poster
//   just typst-poster --input grid=true


// ═══════════════════════════════════════════════════════════════
//  CONSTANTS
// ═══════════════════════════════════════════════════════════════


// ─── Config ──────────────────────────────────────────────────
#let show-grid = sys.inputs.at("grid", default: "false") == "true"

// ─── Page & Layout ───────────────────────────────────────────
#let page-w            = 841mm
#let page-h            = 1189mm
#let page-margin       = 25mm
#let bw                = page-w - 2 * page-margin   // 791mm
#let bh                = page-h - 2 * page-margin   // 1139mm

#let col-left-w        = 34       // left column width (%)
#let col-divider-x     = 35.5     // vertical divider x (%)
#let col-right-x       = 38       // right column start (%)
#let col-right-w       = 62       // right column width (%)

// ─── Colors ──────────────────────────────────────────────────
// Strategy
#let c-blue            = rgb("#185FA5")
#let c-teal            = rgb("#0F6E56")
#let c-amber           = rgb("#BA7517")
#let c-coral           = rgb("#D85A30")
#let c-purple          = rgb("#534AB7")
// Surfaces
#let c-bg              = rgb("#FAFAF7")
#let c-panel           = rgb("#F7F7F3")
#let c-border          = rgb("#D3D1C7")
#let c-qr-bg           = rgb("#F1EFE8")
// Text
#let c-dark            = rgb("#2C2C2A")
#let c-body            = rgb("#444441")
#let c-mid             = rgb("#5F5E5A")
#let c-light           = rgb("#888780")
#let c-faint           = rgb("#B4B2A9")
// Pill backgrounds / foregrounds
#let c-lit-bg          = rgb("#E6F1FB");  #let c-lit-fg = rgb("#0C447C")
#let c-for-bg          = rgb("#E1F5EE");  #let c-for-fg = rgb("#085041")
#let c-dyn-bg          = rgb("#FAEEDA");  #let c-dyn-fg = rgb("#633806")
#let c-par-bg          = rgb("#FAECE7");  #let c-par-fg = rgb("#712B13")
#let c-acc-bg          = rgb("#EEEDFE");  #let c-acc-fg = rgb("#3C3489")

// ─── Typography ──────────────────────────────────────────────
#let font-sans         = "DM Sans"
// Font sizes (largest → smallest)
#let fs-headline       = 80pt
#let fs-stat           = 56pt
#let fs-section        = 48pt
#let fs-title          = 44pt
#let fs-formula-op     = 36pt
#let fs-subtitle       = 32pt
#let fs-body-lg        = 28pt     // author line, spectrum body
#let fs-body-md        = 26pt     // findings, source text
#let fs-body           = 24pt     // standard body
#let fs-body-sm        = 22pt     // stat labels, pills, legend, examples
#let fs-caption        = 20pt     // annotations, ack header
#let fs-caption-sm     = 18pt     // group-significance label
#let fs-footer         = 14pt     // footer grant text
#let fs-footer-sm      = 12pt     // QR URL
// Font weights
#let fw-bold           = 700
#let fw-medium         = 500
#let fw-regular        = 400
// Tracking
#let tracking-section  = 3pt
#let tracking-ack      = 2pt

// ─── Sizing ──────────────────────────────────────────────────
// Dots & rings
#let dot-size          = 5mm
#let dot-size-sm       = 4mm
#let ring-stroke-w     = 0.7mm
// Panels
#let panel-radius      = 4mm
#let panel-radius-sm   = 2mm
#let accent-border-w   = 3mm
#let stroke-thin       = 0.5pt
// Pills
#let pill-radius       = 20mm
#let pill-inset-x      = 10mm
#let pill-inset-y      = 3mm
// Gaps
#let formula-gap       = 3mm
#let source-gap        = 5mm
// Figure widths (%)
#let fig-violin-w      = 42
#let fig-group-w       = 8
#let fig-big-w         = 25
#let fig-small-w       = 12
#let fig-logo-w        = 7
// Panel dimensions (%)
#let stat-panel-w      = 16
#let stat-panel-h      = 4
#let finding-h         = 3
#let example-panel-h   = 6.5
#let accent-bar-w      = 9
#let accent-bar-h      = 0.35
#let callout-h         = 4.5
#let qr-w              = 7
#let qr-h              = 4

// ─── Assets ──────────────────────────────────────────────────
#let dir-figs          = "../figures/poster/"
#let dir-logos         = "../assets/"
#let langs             = ("eng", "fra", "ita", "pol", "spa")
// Image paths
#let img-violin        = dir-figs + "anchor_violin_strip.png"
#let img-group(lang)   = dir-figs + "group_heatmap_" + lang + ".png"
#let img-heatmap(lang) = dir-figs + "heatmap_" + lang + ".png"
#let img-pca(lang)     = dir-figs + "pca_" + lang + ".png"
#let img-agh           = dir-logos + "AGH-logotype.jpg"
#let img-plgrid        = dir-logos + "PLGrid-logotype.png"

// ─── Strings ─────────────────────────────────────────────────

// Section labels
#let sec-background    = [Background]
#let sec-idea          = [The Idea]
#let sec-method        = [Method]
#let sec-dataset       = [Dataset]
#let sec-findings      = [Key Findings]
#let sec-spectrum      = [Spectrum Recovery]
#let sec-pairwise      = [Pairwise]
#let sec-topology      = [Topology]

// Banner
#let str-headline      = [The translator's signal, measured]
#let str-paper-title   = [Degree Zero of Translation]
#let str-subtitle      = [Using Interlinear Baselines to Quantify Translator Intervention]
#let str-authors       = [Maciej Rapacz · Aleksander Smywiński-Pohl · AGH University of Kraków]

// Background
#let str-bg-body = [
  Translation is an act of rewriting. Current metrics either score
  quality (BLEU, COMET) or identify authorship (stylometry) ---
  neither quantifies the translator's departure from the source.
]
#let str-bg-callout = [
  We propose an *unsupervised method* that recovers the translation
  spectrum using interlinear translation as a baseline ---
  a translational "Degree Zero."
]

// The Idea
#let str-idea-body = [
  An interlinear translation maps target words directly onto source
  syntax --- a "colourless" mode with minimal adaptation.
]

// Method
#let str-v-trans       = [_V_#sub[trans]]
#let str-v-base        = [_V_#sub[base]]
#let str-v-int         = [_V_#sub[int]]
#let str-method-note = [
  $||V_"int"||$ = magnitude of intervention\
  Qwen3-Embedding-8B · chapter-level · 260 units
]

// Dataset
#let str-stat-1-num    = [5]
#let str-stat-1-lbl    = [languages]
#let str-stat-2-num    = [\~50]
#let str-stat-2-lbl    = [translations]
#let str-stat-3-num    = [260]
#let str-stat-3-lbl    = [chapters each]
#let str-stat-4-num    = [5]
#let str-stat-4-lbl    = [interlinear baselines]
#let str-dataset-body = [
  _targum_ corpus --- multilingual NT translations (post-1900),
  each labeled with a strategy category.
]

// Key Findings
#let str-finding-1 = [
  *1.* $||V_"int"||$ *recovers the translation spectrum*
  without supervision
]
#let str-finding-2 = [
  *2.* Pairwise discrimination: #text(fill: c-purple)[*90%*] in English
]
#let str-finding-3 = [
  *3.* Topology reveals distinct intervention "arms" ---
  magnitude alone is insufficient
]

// Translation Samples — legend
#let str-leg-interlinear = [Interlinear]
#let str-leg-literal     = [Literal]
#let str-leg-formal      = [Formal]
#let str-leg-dynamic     = [Dynamic]
#let str-leg-paraphrase  = [Paraphrase]

// Translation Samples — example verse
#let str-source-text = [Ἐγειρε ἆρον τὸν κράβαττόν σου καὶ περιπάτει]
#let str-source-ref  = [↑ source (Greek) --- John 5:8]
#let str-ex-interlinear = [*Interlinear* --- "Arise take up the mat of you and walk"]
#let str-ex-literal     = [*Literal* --- "Arise, take up your mat, and walk."]
#let str-ex-formal      = [*Formal* --- "Stand up, take your mat and walk."]
#let str-ex-dynamic     = [*Dynamic* --- "Stand up, pick up your mat, and walk!"]
#let str-ex-paraphrase  = [*Paraphrase* --- "Get up, take your bedroll, start walking."]
#let str-intervention   = [→ increasing intervention from source]

// Spectrum Recovery
#let str-spectrum-body = [
  $||V_"int"||$ *ranks translations from literal to paraphrase
  --- without supervision.*
]
#let str-group-sig-label = [Group\ significance]
#let str-en-stat-num     = [90%]
#let str-en-stat-lbl     = [EN pairs significant]
#let str-order-stat-num  = [4/4]
#let str-order-stat-lbl  = [EN, FR strict ordering]
#let str-other-stat-num  = [51–69%]
#let str-other-stat-lbl  = [other languages]
#let str-stats-note = [
  Mann–Whitney U, Bonferroni-corrected.
  EN, FR: Lit\<For\<Dyn\<Par (all _p_\<0.001).
]

// Pairwise
#let str-pairwise-body = [
  Individual translations are distinguishable ---
  not just strategy groups.
]

// Topology
#let str-topology-body = [
  Two distinct "arms": *OJB* and *FNV* ---
  high intervention, orthogonal directions.
]

// Footer
#let str-ack-header    = [Acknowledgments]
#let str-ack-body = [
  Supported by NCN Preludium (2025/57/N/HS2/04961).
  PLGrid / Cyfronet (PLG/2026/019145).
]
#let str-qr-placeholder = [QR]
#let str-qr-url        = [eacl2026.mrapacz.com]

// Grid overlay
#let grid-color        = rgb(0, 0, 255, 40)
#let grid-color-faint  = rgb(0, 0, 255, 20)
#let grid-label-color  = rgb(0, 0, 255, 90)
#let grid-label-faint  = rgb(0, 0, 255, 55)
#let grid-line-w       = 0.3pt
#let grid-fs           = 14pt
#let grid-fs-sm        = 11pt
#let grid-label-dx     = -20mm
#let grid-label-dy     = -15mm
#let grid-label-nudge  = 5pt


// ═══════════════════════════════════════════════════════════════
//  HELPERS
// ═══════════════════════════════════════════════════════════════


// ─── Positioning ─────────────────────────────────────────────

#let px(v) = v / 100 * bw
#let py(v) = v / 100 * bh

#let at(x, y, w: 100, body) = place(
  top + left, dx: px(x), dy: py(y),
  box(width: px(w), body),
)

#let hline(x, y, len, color: c-border, thick: stroke-thin) = place(
  top + left, dx: px(x), dy: py(y),
  line(length: px(len), stroke: thick + color),
)

#let vline(x, y, len, color: c-border, thick: stroke-thin) = place(
  top + left, dx: px(x), dy: py(y),
  line(length: py(len), angle: 90deg, stroke: thick + color),
)

#let panel(x, y, w, h, fill: c-panel, radius: panel-radius, stroke: none) = place(
  top + left, dx: px(x), dy: py(y),
  rect(width: px(w), height: py(h), fill: fill, radius: radius, stroke: stroke),
)

#let dot(x, y, color: c-blue, size: dot-size) = place(
  top + left, dx: px(x), dy: py(y),
  circle(radius: size / 2, fill: color),
)

#let ring(x, y, color: c-light, size: dot-size) = place(
  top + left, dx: px(x), dy: py(y),
  circle(radius: size / 2, fill: none, stroke: ring-stroke-w + color),
)

#let fig(x, y, w, path) = place(
  top + left, dx: px(x), dy: py(y),
  image(path, width: px(w)),
)

// ─── Text styles ─────────────────────────────────────────────

#let section-label(body) = text(
  font: font-sans, size: fs-section, fill: c-light,
  tracking: tracking-section, upper(body),
)

#let body-text(body) = text(
  font: font-sans, size: fs-body, fill: c-body, body,
)

#let body-small(body) = text(
  font: font-sans, size: fs-body, fill: c-light, body,
)

#let stat-number(body) = text(
  font: font-sans, size: fs-stat, weight: fw-medium, fill: c-purple, body,
)

#let stat-lbl(body) = text(
  font: font-sans, size: fs-body-sm, fill: c-light, body,
)

#let pill(body, bg, fg) = box(
  fill: bg, radius: pill-radius, inset: (x: pill-inset-x, y: pill-inset-y),
  text(font: font-sans, size: fs-body-sm, weight: fw-medium, fill: fg, body),
)

// Accent-left border used by callouts and findings
#let accent-stroke = (
  left: accent-border-w + c-purple,
  top: none, right: none, bottom: none,
)


// ═══════════════════════════════════════════════════════════════
//  PAGE SETUP
// ═══════════════════════════════════════════════════════════════

#set page(width: page-w, height: page-h, margin: page-margin, fill: c-bg)
#set text(font: font-sans, fill: c-dark)


// ═══════════════════════════════════════════════════════════════
//  POSTER CONTENT
// ═══════════════════════════════════════════════════════════════


// ─── BANNER  (y ≈ 0–8%) ─────────────────────────────────────

#panel(0, 0, accent-bar-w, accent-bar-h, fill: c-purple, radius: panel-radius-sm)

#at(0, 0.8, w: 100)[
  #text(font: font-sans, size: fs-headline, weight: fw-bold)[#str-headline]
]

#at(0, 4.2, w: 100)[
  #text(font: font-sans, size: fs-title, weight: fw-medium, fill: c-mid)[#str-paper-title]
]

#at(0, 5.8, w: 100)[
  #text(font: font-sans, size: fs-subtitle, weight: fw-regular, fill: c-light)[#str-subtitle]
]

#at(0, 7.2, w: 94)[
  #text(size: fs-body-lg, fill: c-mid)[#str-authors]
]

#hline(0, 8.5, 100)


// ─── COLUMN DIVIDER ──────────────────────────────────────────

#vline(col-divider-x, 8.5, 86.5)


// ═══════════════════════════════════════════════════════════════
//  LEFT COLUMN  (x = 0–34%)
// ═══════════════════════════════════════════════════════════════


// ─── BACKGROUND  (y ≈ 9–21%) ────────────────────────────────

#at(0, 9.5, w: col-left-w)[#section-label(sec-background)]

#at(0, 12, w: col-left-w)[#body-text[#str-bg-body]]

#panel(0, 16, col-left-w, callout-h, stroke: accent-stroke)
#at(1.5, 16.5, w: 32)[#body-text[#str-bg-callout]]

#hline(0, 21.5, col-left-w)


// ─── THE IDEA  (y ≈ 22–27%) ─────────────────────────────────

#at(0, 22, w: col-left-w)[#section-label(sec-idea)]

#at(0, 24, w: col-left-w)[#body-small[#str-idea-body]]

#hline(0, 27, col-left-w)


// ─── METHOD  (y ≈ 27.5–36%) ────────────────────────────────

#at(0, 27.5, w: col-left-w)[#section-label(sec-method)]

#at(0, 30, w: col-left-w)[
  #set align(center)
  #pill(str-v-trans, c-lit-bg, c-lit-fg)
  #h(formula-gap)
  #text(font: font-sans, size: fs-formula-op)[−]
  #h(formula-gap)
  #pill(str-v-base, c-for-bg, c-for-fg)
  #h(formula-gap)
  #text(font: font-sans, size: fs-formula-op)[=]
  #h(formula-gap)
  #pill(str-v-int, c-acc-bg, c-acc-fg)
]

#at(0, 33, w: col-left-w)[
  #set align(center)
  #body-small[#str-method-note]
]

#hline(0, 36, col-left-w)


// ─── TARGUM DATASET  (y ≈ 36.5–50%) ────────────────────────

#at(0, 36.5, w: col-left-w)[#section-label(sec-dataset)]

// Stats grid 2×2
#panel(0, 39, stat-panel-w, stat-panel-h)
#at(0, 39.2, w: stat-panel-w)[#set align(center); #stat-number[#str-stat-1-num]]
#at(0, 41.5, w: stat-panel-w)[#set align(center); #stat-lbl[#str-stat-1-lbl]]

#panel(17.5, 39, stat-panel-w, stat-panel-h)
#at(17.5, 39.2, w: stat-panel-w)[#set align(center); #stat-number[#str-stat-2-num]]
#at(17.5, 41.5, w: stat-panel-w)[#set align(center); #stat-lbl[#str-stat-2-lbl]]

#panel(0, 43.5, stat-panel-w, stat-panel-h)
#at(0, 43.7, w: stat-panel-w)[#set align(center); #stat-number[#str-stat-3-num]]
#at(0, 46, w: stat-panel-w)[#set align(center); #stat-lbl[#str-stat-3-lbl]]

#panel(17.5, 43.5, stat-panel-w, stat-panel-h)
#at(17.5, 43.7, w: stat-panel-w)[#set align(center); #stat-number[#str-stat-4-num]]
#at(17.5, 46, w: stat-panel-w)[#set align(center); #stat-lbl[#str-stat-4-lbl]]

#at(0, 48, w: col-left-w)[#body-small[#str-dataset-body]]

#hline(0, 51, col-left-w)


// ─── KEY FINDINGS  (x = 0–34%, y ≈ 51.5–65%) ───────────────

#at(0, 51.5, w: col-left-w)[#section-label(sec-findings)]

#panel(0, 54, col-left-w, finding-h, stroke: accent-stroke)
#at(1.5, 54.5, w: 31)[
  #text(font: font-sans, size: fs-body-md)[#str-finding-1]
]

#panel(0, 57.5, col-left-w, finding-h, stroke: accent-stroke)
#at(1.5, 58, w: 31)[
  #text(font: font-sans, size: fs-body-md)[#str-finding-2]
]

#panel(0, 61, col-left-w, finding-h, stroke: accent-stroke)
#at(1.5, 61.5, w: 31)[
  #text(font: font-sans, size: fs-body-md)[#str-finding-3]
]


// ═══════════════════════════════════════════════════════════════
//  RIGHT COLUMN  (x = 38–100%)
// ═══════════════════════════════════════════════════════════════


// ─── TRANSLATION SAMPLES  (y ≈ 9–18%) ──────────────────────

// Strategy legend
#ring(col-right-x, 10)
#at(39.2, 9.8, w: 6)[#text(size: fs-body-sm, fill: c-mid)[#str-leg-interlinear]]
#dot(46, 10, color: c-blue)
#at(47.2, 9.8, w: 5)[#text(size: fs-body-sm, fill: c-mid)[#str-leg-literal]]
#dot(53, 10, color: c-teal)
#at(54.2, 9.8, w: 5)[#text(size: fs-body-sm, fill: c-mid)[#str-leg-formal]]
#dot(60, 10, color: c-amber)
#at(61.2, 9.8, w: 6)[#text(size: fs-body-sm, fill: c-mid)[#str-leg-dynamic]]
#dot(68, 10, color: c-coral)
#at(69.2, 9.8, w: 6)[#text(size: fs-body-sm, fill: c-mid)[#str-leg-paraphrase]]

// Example panel
#panel(col-right-x, 11.5, col-right-w, example-panel-h)

#at(39, 11.8, w: 60)[
  #text(font: font-sans, size: fs-body-md, style: "italic", fill: c-purple)[#str-source-text]
  #h(source-gap)
  #text(size: fs-caption, style: "italic", fill: c-light)[#str-source-ref]
]

#hline(39, 13, 60)

#ring(39.2, 13.5, size: dot-size-sm)
#at(40.5, 13.3, w: 20)[
  #text(size: fs-body-sm, fill: c-mid)[#str-ex-interlinear]
]

#dot(60.2, 13.5, color: c-blue, size: dot-size-sm)
#at(61.5, 13.3, w: 20)[
  #text(size: fs-body-sm, fill: c-mid)[#str-ex-literal]
]

#dot(39.2, 14.7, color: c-teal, size: dot-size-sm)
#at(40.5, 14.5, w: 20)[
  #text(size: fs-body-sm, fill: c-mid)[#str-ex-formal]
]

#dot(60.2, 14.7, color: c-amber, size: dot-size-sm)
#at(61.5, 14.5, w: 20)[
  #text(size: fs-body-sm, fill: c-mid)[#str-ex-dynamic]
]

#dot(39.2, 15.9, color: c-coral, size: dot-size-sm)
#at(40.5, 15.7, w: 20)[
  #text(size: fs-body-sm, fill: c-mid)[#str-ex-paraphrase]
]

#at(61, 16.5, w: col-right-x)[
  #set align(right)
  #text(size: fs-caption, style: "italic", fill: c-light)[#str-intervention]
]

#hline(col-right-x, 18.5, col-right-w)


// ─── SPECTRUM RECOVERY  (y ≈ 19–60%) ────────────────────────

#at(col-right-x, 19, w: col-right-w)[#section-label(sec-spectrum)]

#at(col-right-x, 21.5, w: col-right-w)[
  #text(font: font-sans, size: fs-body-lg, fill: c-body)[#str-spectrum-body]
]

// Anchor figure: violin/swarm plot
#fig(col-right-x, 23.5, fig-violin-w, img-violin)

// Group heatmaps (stacked alongside)
#at(82, 23.5, w: 12)[
  #set align(center)
  #text(size: fs-caption-sm, fill: c-light)[#str-group-sig-label]
]

#fig(83, 26.5, fig-group-w, img-group("eng"))
#fig(83, 32,   fig-group-w, img-group("fra"))
#fig(83, 37.5, fig-group-w, img-group("ita"))
#fig(83, 43,   fig-group-w, img-group("pol"))
#fig(83, 48.5, fig-group-w, img-group("spa"))

// Stats row
#at(col-right-x, 53.5, w: 15)[#set align(center); #stat-number[#str-en-stat-num]]
#at(col-right-x, 57, w: 15)[#set align(center); #stat-lbl[#str-en-stat-lbl]]

#at(55, 53.5, w: 15)[
  #set align(center)
  #text(font: font-sans, size: fs-stat, weight: fw-medium, fill: c-teal)[#str-order-stat-num]
]
#at(55, 57, w: 15)[#set align(center); #stat-lbl[#str-order-stat-lbl]]

#at(72, 53.5, w: 20)[
  #set align(center)
  #text(font: font-sans, size: fs-stat, weight: fw-medium, fill: c-amber)[#str-other-stat-num]
]
#at(72, 57, w: 20)[#set align(center); #stat-lbl[#str-other-stat-lbl]]

#at(col-right-x, 59, w: 55)[#body-small[#str-stats-note]]

#hline(col-right-x, 61, col-right-w)


// ─── PAIRWISE SENSITIVITY  (x = 38–64%, y ≈ 61.5–96%) ──────

#at(col-right-x, 61.5, w: 27)[#section-label(sec-pairwise)]

#at(col-right-x, 64, w: 27)[#body-text[#str-pairwise-body]]

#fig(col-right-x, 66.5, fig-big-w, img-heatmap("eng"))

// Small heatmaps 2×2
#fig(col-right-x, 82, fig-small-w, img-heatmap("fra"))
#fig(51,           82, fig-small-w, img-heatmap("ita"))
#fig(col-right-x, 91, fig-small-w, img-heatmap("pol"))
#fig(51,           91, fig-small-w, img-heatmap("spa"))


// ─── TOPOLOGY  (x = 67–100%, y ≈ 61.5–90%) ─────────────────

#at(67, 61.5, w: 33)[#section-label(sec-topology)]

#at(67, 64, w: 33)[#body-text[#str-topology-body]]

#fig(67, 66.5, fig-big-w, img-pca("eng"))

// Small PCAs 2×2
#fig(67, 77, fig-small-w, img-pca("fra"))
#fig(80, 77, fig-small-w, img-pca("ita"))
#fig(67, 85, fig-small-w, img-pca("pol"))
#fig(80, 85, fig-small-w, img-pca("spa"))


// ─── FOOTER  (y = 95–100%, ≤5% of body height) ─────────────

#hline(0, 95, col-divider-x)

#at(0, 95.3, w: col-left-w)[#text(
  font: font-sans, size: fs-caption, fill: c-light,
  tracking: tracking-ack, upper[#str-ack-header],
)]

#fig(0, 96.5, fig-logo-w, img-agh)
#fig(8, 96.5, fig-logo-w, img-plgrid)

#at(16, 96.2, w: 19.5)[
  #text(size: fs-footer, fill: c-mid)[#str-ack-body]
]

// QR placeholder
#panel(28, 96, qr-w, qr-h, fill: c-qr-bg, stroke: stroke-thin + c-border)
#at(28, 96.3, w: qr-w)[
  #set align(center)
  #text(size: fs-body-sm, fill: c-faint)[#str-qr-placeholder]
]
#at(28, 99, w: qr-w)[
  #set align(center)
  #text(size: fs-footer-sm, fill: c-faint)[#str-qr-url]
]


// ═══════════════════════════════════════════════════════════════
//  COORDINATE GRID OVERLAY  (toggle with --input grid=true)
// ═══════════════════════════════════════════════════════════════

#if show-grid {
  // Major lines every 10%
  for i in range(0, 101, step: 10) {
    let v = float(i)
    hline(0, v, 100, color: grid-color, thick: grid-line-w)
    vline(v, 0, 100, color: grid-color, thick: grid-line-w)
    place(top + left, dx: grid-label-dx, dy: py(v) - grid-label-nudge,
      text(size: grid-fs, fill: grid-label-color, str(i)))
    place(top + left, dx: px(v) - grid-label-nudge, dy: grid-label-dy,
      text(size: grid-fs, fill: grid-label-color, str(i)))
  }

  // Minor lines every 5% (with labels)
  for i in range(5, 100, step: 10) {
    let v = float(i)
    hline(0, v, 100, color: grid-color-faint, thick: grid-line-w)
    vline(v, 0, 100, color: grid-color-faint, thick: grid-line-w)
    place(top + left, dx: grid-label-dx, dy: py(v) - grid-label-nudge,
      text(size: grid-fs-sm, fill: grid-label-faint, str(i)))
    place(top + left, dx: px(v) - grid-label-nudge, dy: grid-label-dy,
      text(size: grid-fs-sm, fill: grid-label-faint, str(i)))
  }
}
