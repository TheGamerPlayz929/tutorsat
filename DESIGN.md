# DESIGN.md: Instrument Panel design system

The UI is built as a *calibrated measurement instrument*, not a consumer quiz app.
This document is the single source of truth for that visual language, so future
changes cannot silently drift: the same role ARCHITECTURE.md plays for code.
Every rule here traces back to one principle: **nothing decorative**. If an element
does not represent measured state or a real control, it does not ship.

## 1. Token system (`web/styles.css`, `:root`)

| Token | Value | Role |
|-------|-------|------|
| `--ink` | `#14181C` | Text, structural rules, bracket frames |
| `--ink-strong` | `#000000` | Hover-darkened commit button only |
| `--paper` | `#EFEDE6` | Page background ("scantron paper", not editorial cream) |
| `--panel` | `#FFFFFF` | Readout surfaces: question cards, charts, dials |
| `--signal` | `#2B6E5E` | The ONLY live/active accent: progress ticks, θ values, selected/correct states, range marks |
| `--alert` | `#B4442E` | Incorrect/error states ONLY (never decorative, never a chart series color) |
| `--graphite` | `#5B6470` | Secondary text, dividers' base, inactive states |

Structural tokens: `--hairline` / `--hairline-soft` dividers, `--bracket` arm length,
`--bracket-w` stroke, `--pad-panel` (single source of truth for panel padding).

Derived tints are rgba mixes of ink/signal/alert only. An audit (Phase 2 §5)
confirmed no other color families exist outside `:root`.

## 2. Type roles (3 faces, strictly separated)

- **Display: Archivo**: nameplate, panel headings, buttons-as-labels. Tight
  tracking, uppercase where structural.
- **Body: IBM Plex Sans**: question text and prose. Legibility over personality.
- **Utility/data: IBM Plex Mono**: any number or identifier that comes *from the
  instrument*: seeds, θ ± sd, percentages, timers, session ids, axis numerals,
  verdict labels (`CORRECT` / `INCORRECT: SEE BELOW`). This mono/body split is the
  signature move: it visually separates "measured" from "written". Tabular figures
  (`font-variant-numeric: tabular-nums`) keep columns aligned.

## 3. Structural grammar

### Corner-bracket panels (`.panel`)
Four L-shaped brackets (eight linear-gradient backgrounds) replace rounded-corner +
drop-shadow cards everywhere. Brackets mark "this surface is a live readout".
No `border-radius` exists in the stylesheet except an explicit `border-radius: 0`
reset on form controls.

### Tick marks: the one grammar for "measured quantity"
All progress/measurement indicators are rows of discrete rectangular ticks:
- Calibration strip ticks: answered items of the active session (omitted when no
  session is live: functional, never decorative; decision recorded in
  `calTicksTrack()` in `app.js`)
- In-card question tickbars (practice + mock modules)
- Score scales: printed-axis language: thin axis, tick marks per 100 points,
  bracketed signal-colored range, mono end labels. Bands are always ranges; a
  single celebratory score number would overstate the model's precision and is
  forbidden.
Smooth gradient bars, rings, and pie-style indicators must not be introduced.

### State markers on answers
Selected = 3px inset signal bar + faint signal tint. Correct/incorrect after submit =
same inset mechanism in signal/alert + square tab recolor. The technique uses
`box-shadow: inset` deliberately (no layout shift); these are structural state
markers, not shadows.

## 4. Motion (exactly three animations)

1. θ-readout pulse: 200ms background-color keyframe, no movement
2. Module-transition interstitial fade-in: 300ms opacity
3. Tick fill transitions ≤150ms

`prefers-reduced-motion: reduce` disables all animation and transition globally.
When in doubt, cut the animation. A scoring instrument does not cheer.

## 5. Accessibility floor

- Global `:focus-visible`: 2px signal outline (offset −2px inside dense rows)
- Answer rows expose selection via `aria-pressed`
- All text pairs meet WCAG AA against both `--paper` and `--panel`
  (graphite-on-paper ≈ 4.9:1, signal-on-white ≈ 5.6:1)
- Calibration strip collapses to seed + θ under 640px (`.cal-optional`)
- Empty states speak in the instrument's voice and invite action
  (e.g. `NO RESPONSES YET: START ADAPTIVE PRACTICE TO BEGIN CALIBRATION`)

## 6. Copy rules

- Name actions by what the student controls: "Start adaptive practice",
  "Begin full mock"
- Outcomes stated plainly: "Correct" / "Incorrect: see below"; never praise
- Mechanism copy uses the models' real vocabulary (θ, Fisher information,
  blueprint, calibrated): set in `<code>`/mono when naming a mechanism
- Attribution `made_by_jayaditya` + build marker live in the footer and in the
  About dialog; the College Board disclaimer is legal text and is never shortened
  or restyled

## 7. Chart styling (`drawThetaChart`)

Single-weight lines (1.5px × devicePixelRatio), hairline grid, mono-face axis
labels. Series colors are read from the CSS tokens at draw time
(`--signal`, `--ink`, `--graphite`) with globalAlpha stepping for additional
series, so charts re-theme without code changes; alert red is explicitly excluded.
No gradients, no fills, no drop shadows.

## 8. Themes (light / dark)

The entire palette lives in `:root` tokens plus alpha mixes of `--line-rgb`;
the dark theme is a single `[data-theme="dark"]` token override block and zero
component-level rules:

| Token | Light | Dark |
|-------|-------|------|
| `--paper` | `#EFEDE6` | `#17181B` |
| `--panel` | `#FFFFFF` | `#202329` |
| `--ink` | `#14181C` | `#E9E6DE` (warm off-white) |
| `--graphite` | `#5B6470` | `#9AA0AB` |
| `--signal` | `#2B6E5E` | `#5BA894` |
| `--alert` | `#B4442E` | `#D2735C` |

Rules:
- Dark is a night shift of the same instrument: warm off-white ink on deep
  graphite, not a generic near-black/neon look; signal and alert lighten just
  enough to hold WCAG AA against `--panel`.
- Any new style MUST use tokens (`var(--…)`, `rgba(var(--line-rgb), a)`,
  `var(--wash)`); hardcoded hexes/rgba in components are how themes break.
- Selection: `data-theme` on `<html>`; default follows
  `prefers-color-scheme`, manual choice persists to `localStorage`
  (`satprep_theme`). The header toggle shows the mode it switches TO.
- Canvas code reads tokens via `getComputedStyle` per draw; the app re-renders
  on toggle so charts repaint in-theme.

## 9. About dialog

The nameplate dial/wordmark is a button opening a modal (`#about-backdrop`,
`role="dialog"`): what the instrument is, pointers to README/ARCHITECTURE/
DESIGN.md, the full non-affiliation disclaimer, and the mono attribution +
build marker. Esc, backdrop click, and the Close button dismiss it; focus moves
into the dialog on open and returns to the nameplate on close.
