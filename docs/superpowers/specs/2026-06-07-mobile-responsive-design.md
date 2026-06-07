# Mobile Responsive Design Spec

Make the frontend mobile-friendly across both user-facing and admin pages.

## Breakpoints

Two breakpoints divide three tiers:

| Tier    | Range       | Primary targets          |
|---------|-------------|--------------------------|
| Phone   | <= 480px    | iPhone SE through iPhone |
| Tablet  | 481–768px   | iPad Mini, small tablets |
| Desktop | > 768px     | Current behavior         |

## Responsive Strategy

CSS container queries for component-level responsiveness, viewport media queries for shell-level layout (nav, admin sidebar). All responsive rules live in a new `frontend/src/styles/responsive.css` — existing CSS files are unchanged except for adding `container-type: inline-size` declarations to key layout wrappers.

### Container query targets

- `.main` — user-facing content wrapper (560px max-width)
- `.admin-content` — admin content area
- `.auth-container` — login/register forms

### Viewport media query targets

- Header hamburger menu toggle (<=768px)
- Admin sidebar collapse (<=768px)

## User Navigation: Hamburger Menu

**Trigger**: Viewport <= 768px.

**Behavior**:
- Horizontal `.tabs` bar is hidden via `display: none`
- A hamburger button (CSS-only three-line icon) appears in `.header-top`, next to the logo
- Clicking the hamburger toggles a full-width vertical dropdown below the header containing all nav links
- The user dropdown (username, Settings, Logout) moves into the bottom of the mobile menu, separated by a divider
- Menu closes on route change (`useLocation` watch)
- Desktop (>768px): hamburger hidden, tabs visible — no change from current behavior

**Implementation**:
- Add `menuOpen` boolean state + toggle handler to `Header.tsx`
- Render a `<button className="hamburger">` with three `<span>` lines (CSS-only icon, no SVG)
- Render a `<nav className="mobile-menu">` containing the same tab links + user actions
- Show/hide via CSS class toggle (`.mobile-menu.open { display: block }`)
- No animation — simple show/hide

## Drawing Canvas

**Current**: Fixed 320x320px with `max-width: 100%`.

**Change**:
- Remove fixed `height: 320px`, add `aspect-ratio: 1` to maintain square
- `width: 320px` and `max-width: 100%` stay — canvas shrinks below 320px only on screens narrower than ~360px
- The HTML `<canvas>` element reads its container dimensions for coordinate mapping (existing behavior)
- ML model input normalization happens at capture time — display size has no effect on recognition

**Phone (<=480px)**: Reduce `.main` padding from `32px 24px` to `16px 12px` to maximize canvas drawing area.

## Admin Panel: Collapsible Sidebar

**Trigger**: Viewport <= 768px.

**Behavior**:
- `.admin-sidebar` hidden by default (`transform: translateX(-100%)`, `position: fixed`, full height, `z-index` above content)
- Hamburger button appears on the left side of `.admin-topbar`
- Clicking slides sidebar in; a semi-transparent backdrop overlay appears behind it
- Clicking backdrop or navigating closes the sidebar
- `.admin-main` takes full width when sidebar is collapsed
- Desktop (>768px): sidebar always visible, hamburger hidden

**Implementation**:
- Add `sidebarOpen` boolean state + toggle handler to `AdminLayout.tsx`
- Render a backdrop `<div>` when open
- Close on route change

### Admin tables on phone (<=480px)

- Wrap `.admin-table` in a horizontal-scroll container (`overflow-x: auto`)
- `.admin-search` goes full width (`width: 100%` instead of fixed 300px)
- `.admin-stats-grid` already uses `auto-fill, minmax(200px, 1fr)` — stacks to 1 column naturally

## Page-Specific Adjustments

### Progress page
- `.progress-stats` (flex row of stat cards): switch to 2-column grid on phone (<=480px) so cards don't get crushed

### Leaderboard
- Hide `.lb-streak` column on phone (<=480px) to save horizontal space
- Rank, name, and score columns are sufficient on small screens

### Auth pages
- Already 360px max-width — works on mobile as-is
- Reduce top margin from 60px to 24px on phone

### About / Credits
- Reduce heading sizes slightly on phone
- Adjust padding — content is already single-column

### Settings / Word Practice
- No structural changes — forms and canvas follow the same patterns above

## Touch and Mobile UX

- **Touch targets**: Ensure 44px minimum touch target height for mobile menu links and buttons. Current `.tab` is ~28px, `.btn` is ~32px — add `min-height: 44px` in mobile contexts.
- **Viewport meta**: Already correct (`width=device-width, initial-scale=1.0`). No change.
- **Canvas touch**: Already has `touch-action: none`. No change.
- **Horizontal overflow**: Add `overflow-x: hidden` on `body` as a safety net.

## Files Changed

| File | Change |
|------|--------|
| `frontend/src/styles/responsive.css` | **New** — all media queries and container queries |
| `frontend/src/styles/tokens.css` | Add `overflow-x: hidden` to `body` |
| `frontend/src/styles/components.css` | Add `aspect-ratio: 1`, remove fixed height on `.canvas-box` |
| `frontend/src/styles/layout.css` | Add `container-type: inline-size` to `.main` |
| `frontend/src/styles/admin.css` | Add `container-type: inline-size` to `.admin-content` |
| `frontend/src/components/Header.tsx` | Add hamburger toggle state + mobile menu markup |
| `frontend/src/pages/admin/AdminLayout.tsx` | Add sidebar toggle state + backdrop markup |
| `frontend/src/main.tsx` (or CSS import) | Import `responsive.css` **after** other stylesheets so overrides take precedence |

## No New Dependencies

Zero new packages. Plain CSS container queries + media queries. Hamburger icon is CSS-only (three spans). State management uses existing React useState hooks.
