# Teeline ML Checker — Branding & Design Spec

**Date:** 2026-06-03
**Status:** Approved
**Goal:** Apply a cohesive "Stationery Notebook" design system to all frontend pages.

---

## Design Decisions

| Decision | Choice |
|----------|--------|
| Direction | Notebook — warm paper, ruled lines, ink-on-paper |
| Palette | Stationery — deep red brand, green correct, red incorrect |
| Practice layout | Stacked center — reference header, canvas centered, results below |
| Navigation | Header + Tabs — logo/user top, notebook-divider tabs below |

---

## Design Tokens (CSS Custom Properties)

```css
:root {
  --ink: #1a1a1a;
  --paper: #f7f3eb;
  --accent: #b5350f;
  --success: #1d6b3a;
  --info: #2a5f8f;
  --muted: #8a7a68;
  --line: #e8dfd0;
  --surface: #ffffff;
}
```

## Typography

- **Headings**: `'Syne', sans-serif` — weight 800, letter-spacing -0.01em
- **Body/UI**: `'DM Mono', monospace` — weight 400 (body), 500 (labels/buttons)
- **Google Fonts import**: `Syne:wght@400;600;700;800` + `DM Mono:wght@300;400;500`

| Element | Font | Size | Weight | Extras |
|---------|------|------|--------|--------|
| Page title | Syne | 22-28px | 800 | — |
| Section heading | Syne | 18-20px | 700 | — |
| Eyebrow/label | DM Mono | 10-11px | 500 | uppercase, letter-spacing 0.25em |
| Body text | DM Mono | 12px | 400 | line-height 1.7 |
| Button | DM Mono | 11px | 500 | uppercase, letter-spacing 0.08em |
| Tab | DM Mono | 11px | 500 | uppercase, letter-spacing 0.08em |

## Background Texture

Ruled-line overlay on body using `::before` pseudo-element:
```css
body::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image: repeating-linear-gradient(
    transparent, transparent 31px, var(--line) 31px, var(--line) 32px
  );
  opacity: 0.2;
  pointer-events: none;
  z-index: 0;
}
```

## Components

### Header + Tabs
- Header: paper background, 2px ink bottom border
- Top line: logo left (Syne 800, "Teeline" ink + "ML" accent), user info right (11px muted)
- Tab bar below: DM Mono 11px uppercase, active = ink bg + paper text + rounded top corners, inactive = muted text

### Buttons
- Default: transparent bg, 1.5px ink border, 2px radius, uppercase DM Mono 11px
- Primary: ink bg, paper text
- Success: success border + text, hover fills success bg
- Retry/Error: accent border + text, hover fills accent bg
- Disabled: opacity 0.35, no pointer
- Hover default: fills ink bg

### Cards (result cards, stat cards)
- White background, 1.5px line border, 3px radius
- Result correct: 2px success border
- Result incorrect: 2px accent border

### Canvas
- 320x320px (responsive via max-width: 100%), white bg, 2px ink border, 3px radius
- Cursor: crosshair
- Faded reference symbol as watermark (optional, 0.3 opacity)

### Symbol Header (Practice page)
- Flex row: reference thumbnail (56x56, white bg, line border, accent italic character) + info column (eyebrow + title) + dropdown selector
- Dropdown: DM Mono 11px, 1.5px ink border, paper bg, 2px radius

### Confidence Bar
- 6px height, line bg, 3px radius
- Fill: success color for correct, accent for incorrect
- Label row above: "Confidence" left, "94.2%" right, both 10px muted uppercase

### Select/Dropdown
- DM Mono 11px, 1.5px ink border, paper bg, 2px radius

---

## Pages

### Practice Page (Stacked Center)
1. Symbol header: reference + name + selector
2. Canvas area: centered 320px canvas
3. Action buttons: Submit (primary), Undo, Clear
4. Result card: appears after prediction — correct (green) or incorrect (red), shows predicted letter + confidence bar
5. Next actions: "Next Symbol" (success) / "Try Again" (retry)

### Progress Page
1. Overall stats row: total attempts, overall accuracy, current streak
2. Per-symbol accuracy: 26 horizontal bars (A-Z), bar fill = accuracy %, color coded (green >70%, accent <70%, muted if no data)
3. Weakest 5 section: highlights lowest-accuracy symbols for focused practice

### Login Page
1. Centered card on paper background (max-width 360px)
2. Logo centered at top
3. Username + password inputs (DM Mono, 1.5px ink border, paper bg)
4. Login button (primary), Register link below
5. Registration form: same card, username + email + password fields

---

## Anti-Scope

- No dark mode
- No animations beyond hover transitions (0.15s)
- No custom fonts beyond Syne + DM Mono
- No CSS framework (Tailwind, etc.) — vanilla CSS custom properties
- No responsive breakpoints beyond max-width centering (mobile works via stacked layout naturally)

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `frontend/src/styles/tokens.css` | Create — CSS custom properties + base styles + ruled-line texture |
| `frontend/src/styles/components.css` | Create — button, card, tab, confidence bar, canvas styles |
| `frontend/src/styles/layout.css` | Create — header, main, footer layout |
| `frontend/src/components/Header.tsx` | Create — logo + user info + tab navigation |
| `frontend/src/components/FeedbackPanel.tsx` | Create — result card with prediction + confidence bar |
| `frontend/src/App.tsx` | Modify — add Header, import styles, add routes for Progress + Login |
| `frontend/src/pages/PracticePage.tsx` | Modify — apply stacked center layout, symbol header, styled canvas |
| `frontend/src/pages/LoginPage.tsx` | Create — login/register forms |
| `frontend/src/pages/ProgressPage.tsx` | Create — per-symbol accuracy bars + stats |
| `frontend/src/components/DrawingCanvas.tsx` | Modify — apply canvas styles from design system |
| `frontend/index.html` | Modify — add Google Fonts link |
