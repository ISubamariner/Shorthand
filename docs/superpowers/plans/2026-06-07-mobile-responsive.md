# Mobile Responsive Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the entire frontend (user-facing and admin pages) mobile-friendly with two breakpoints (480px, 768px).

**Architecture:** CSS container queries for component-level responsiveness, viewport media queries for shell-level nav/sidebar. All responsive rules in a single new `responsive.css`. Two React components get state for mobile menu toggles.

**Tech Stack:** Plain CSS (container queries, media queries), React useState/useEffect, React Router useLocation.

---

### Task 1: Canvas fluid sizing

**Files:**
- Modify: `frontend/src/styles/components.css:113-122`

- [ ] **Step 1: Update `.canvas-box` to use aspect-ratio instead of fixed height**

In `frontend/src/styles/components.css`, replace the `.canvas-box` rule:

```css
.canvas-box {
  width: 320px;
  height: 320px;
  max-width: 100%;
  background: var(--surface);
  border: 2px solid var(--ink);
  border-radius: 3px;
  cursor: crosshair;
  touch-action: none;
}
```

with:

```css
.canvas-box {
  width: 320px;
  max-width: 100%;
  aspect-ratio: 1;
  background: var(--surface);
  border: 2px solid var(--ink);
  border-radius: 3px;
  cursor: crosshair;
  touch-action: none;
}
```

- [ ] **Step 2: Verify canvas still renders as a square**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/styles/components.css
git commit -m "feat(responsive): use aspect-ratio for fluid canvas sizing"
```

---

### Task 2: Base responsive setup (tokens + container types + responsive.css scaffold)

**Files:**
- Modify: `frontend/src/styles/tokens.css:16-23`
- Modify: `frontend/src/styles/layout.css:112-117`
- Modify: `frontend/src/styles/admin.css:84-88`
- Create: `frontend/src/styles/responsive.css`
- Modify: `frontend/src/App.tsx:3-6`

- [ ] **Step 1: Add `overflow-x: hidden` to body in tokens.css**

In `frontend/src/styles/tokens.css`, change the `body` rule from:

```css
body {
  background: var(--paper);
  color: var(--ink);
  font-family: var(--font-body);
  min-height: 100vh;
  position: relative;
}
```

to:

```css
body {
  background: var(--paper);
  color: var(--ink);
  font-family: var(--font-body);
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
}
```

- [ ] **Step 2: Add `container-type: inline-size` to `.main` in layout.css**

In `frontend/src/styles/layout.css`, change the `.main` rule from:

```css
.main {
  max-width: 560px;
  margin: 0 auto;
  padding: 32px 24px 60px;
}
```

to:

```css
.main {
  max-width: 560px;
  margin: 0 auto;
  padding: 32px 24px 60px;
  container-type: inline-size;
}
```

- [ ] **Step 3: Add `container-type: inline-size` to `.admin-content` in admin.css**

In `frontend/src/styles/admin.css`, change the `.admin-content` rule from:

```css
.admin-content {
  flex: 1;
  padding: 24px;
  max-width: 1200px;
}
```

to:

```css
.admin-content {
  flex: 1;
  padding: 24px;
  max-width: 1200px;
  container-type: inline-size;
}
```

- [ ] **Step 4: Create `responsive.css` with phone/tablet media queries for `.main` padding and touch targets**

Create `frontend/src/styles/responsive.css`:

```css
/* ===== Phone (<=480px) ===== */
@media (max-width: 480px) {
  .main {
    padding: 16px 12px 40px;
  }

  .btn {
    min-height: 44px;
  }
}

/* ===== Tablet and below (<=768px) ===== */
@media (max-width: 768px) {
  body {
    -webkit-text-size-adjust: 100%;
  }
}
```

- [ ] **Step 5: Import `responsive.css` in App.tsx after other stylesheets**

In `frontend/src/App.tsx`, change:

```typescript
import "./styles/tokens.css";
import "./styles/components.css";
import "./styles/layout.css";
import "./styles/admin.css";
```

to:

```typescript
import "./styles/tokens.css";
import "./styles/components.css";
import "./styles/layout.css";
import "./styles/admin.css";
import "./styles/responsive.css";
```

- [ ] **Step 6: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/styles/tokens.css frontend/src/styles/layout.css frontend/src/styles/admin.css frontend/src/styles/responsive.css frontend/src/App.tsx
git commit -m "feat(responsive): add responsive scaffold, container types, overflow guard"
```

---

### Task 3: Hamburger menu (Header.tsx)

**Files:**
- Modify: `frontend/src/components/Header.tsx`
- Modify: `frontend/src/styles/responsive.css`

- [ ] **Step 1: Add mobile menu state and markup to Header.tsx**

Replace the entire content of `frontend/src/components/Header.tsx` with:

```tsx
import { useEffect, useRef, useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { api, getAccessToken } from "../api/client";

export function Header() {
  const isLoggedIn = getAccessToken() !== null;
  const [username, setUsername] = useState<string | null>(null);
  const [isStaff, setIsStaff] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (isLoggedIn) {
      api.auth.me().then((u) => {
        setUsername(u.username);
        setIsStaff(u.is_staff);
      }).catch(() => {});
    }
  }, [isLoggedIn]);

  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    if (dropdownOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [dropdownOpen]);

  const navLinks = (
    <>
      <NavLink to="/" className={({ isActive }) => `tab ${isActive ? "active" : ""}`} end>
        Practice
      </NavLink>
      <NavLink to="/words" className={({ isActive }) => `tab ${isActive ? "active" : ""}`}>
        Words
      </NavLink>
      <NavLink to="/progress" className={({ isActive }) => `tab ${isActive ? "active" : ""}`}>
        Progress
      </NavLink>
      <NavLink to="/leaderboard" className={({ isActive }) => `tab ${isActive ? "active" : ""}`}>
        Leaderboard
      </NavLink>
      <NavLink to="/about" className={({ isActive }) => `tab ${isActive ? "active" : ""}`}>
        About
      </NavLink>
      <NavLink to="/credits" className={({ isActive }) => `tab ${isActive ? "active" : ""}`}>
        Credits
      </NavLink>
      {isStaff && (
        <NavLink to="/admin" className={({ isActive }) => `tab ${isActive ? "active" : ""}`}>
          Admin
        </NavLink>
      )}
    </>
  );

  return (
    <div className="header">
      <div className="header-top">
        <div className="logo">
          Teeline <span className="accent">ML</span>
        </div>
        <button
          className={`hamburger ${menuOpen ? "open" : ""}`}
          onClick={() => setMenuOpen((v) => !v)}
          aria-label="Toggle navigation menu"
          aria-expanded={menuOpen}
        >
          <span />
          <span />
          <span />
        </button>
        <div className="user-info">
          {isLoggedIn && username ? (
            <div className="user-dropdown" ref={dropdownRef}>
              <button
                className="user-dropdown-toggle"
                onClick={() => setDropdownOpen((v) => !v)}
              >
                {username} <span className="user-dropdown-caret">&#9662;</span>
              </button>
              {dropdownOpen && (
                <div className="user-dropdown-menu">
                  <button
                    className="user-dropdown-item"
                    onClick={() => { setDropdownOpen(false); navigate("/settings"); }}
                  >
                    Settings
                  </button>
                  <button
                    className="user-dropdown-item"
                    onClick={async () => {
                      setDropdownOpen(false);
                      await api.auth.logout();
                      window.location.href = "/";
                    }}
                  >
                    Logout
                  </button>
                </div>
              )}
            </div>
          ) : (
            <NavLink to="/login">login</NavLink>
          )}
        </div>
      </div>
      <div className="tabs">
        {navLinks}
      </div>
      <nav className={`mobile-menu ${menuOpen ? "open" : ""}`}>
        <div className="mobile-menu-nav">
          {navLinks}
        </div>
        {isLoggedIn && username && (
          <>
            <div className="mobile-menu-divider" />
            <div className="mobile-menu-user">
              <button
                className="mobile-menu-item"
                onClick={() => navigate("/settings")}
              >
                Settings
              </button>
              <button
                className="mobile-menu-item"
                onClick={async () => {
                  await api.auth.logout();
                  window.location.href = "/";
                }}
              >
                Logout
              </button>
            </div>
          </>
        )}
        {!isLoggedIn && (
          <>
            <div className="mobile-menu-divider" />
            <div className="mobile-menu-user">
              <NavLink to="/login" className="mobile-menu-item">Login</NavLink>
            </div>
          </>
        )}
      </nav>
    </div>
  );
}
```

- [ ] **Step 2: Add hamburger and mobile menu styles to responsive.css**

Append to `frontend/src/styles/responsive.css`:

```css
/* ===== Hamburger button ===== */
.hamburger {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  flex-direction: column;
  gap: 5px;
  z-index: 10;
}

.hamburger span {
  display: block;
  width: 22px;
  height: 2px;
  background: var(--ink);
  transition: transform 0.2s, opacity 0.2s;
}

.hamburger.open span:nth-child(1) {
  transform: translateY(7px) rotate(45deg);
}

.hamburger.open span:nth-child(2) {
  opacity: 0;
}

.hamburger.open span:nth-child(3) {
  transform: translateY(-7px) rotate(-45deg);
}

/* ===== Mobile menu ===== */
.mobile-menu {
  display: none;
}

.mobile-menu-nav {
  display: flex;
  flex-direction: column;
}

.mobile-menu-nav .tab {
  padding: 12px 24px;
  min-height: 44px;
  display: flex;
  align-items: center;
  border-radius: 0;
}

.mobile-menu-nav .tab.active {
  border-radius: 0;
}

.mobile-menu-divider {
  height: 1px;
  background: var(--line);
  margin: 4px 0;
}

.mobile-menu-user {
  display: flex;
  flex-direction: column;
}

.mobile-menu-item {
  display: flex;
  align-items: center;
  padding: 12px 24px;
  min-height: 44px;
  font-size: 11px;
  font-family: var(--font-body);
  font-weight: 500;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
  background: none;
  border: none;
  cursor: pointer;
  text-decoration: none;
}

.mobile-menu-item:hover {
  color: var(--ink);
}

@media (max-width: 768px) {
  .hamburger {
    display: flex;
  }

  .tabs {
    display: none;
  }

  .user-info {
    display: none;
  }

  .mobile-menu.open {
    display: block;
    border-top: 1px solid var(--line);
  }
}
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/Header.tsx frontend/src/styles/responsive.css
git commit -m "feat(responsive): add hamburger menu and mobile navigation"
```

---

### Task 4: Admin collapsible sidebar (AdminLayout.tsx)

**Files:**
- Modify: `frontend/src/pages/admin/AdminLayout.tsx`
- Modify: `frontend/src/styles/responsive.css`

- [ ] **Step 1: Add sidebar toggle state and backdrop to AdminLayout.tsx**

Replace the entire content of `frontend/src/pages/admin/AdminLayout.tsx` with:

```tsx
import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { api } from "../../api/client";

const NAV_ITEMS = [
  { to: "/admin", label: "Dashboard", end: true },
  { to: "/admin/users", label: "Users" },
  { to: "/admin/content", label: "Content" },
  { to: "/admin/analytics", label: "Analytics" },
  { to: "/admin/jobs", label: "Jobs" },
  { to: "/admin/audit-log", label: "Audit Log" },
  { to: "/admin/settings", label: "Settings" },
  { to: "/admin/monitoring", label: "Monitoring" },
];

export function AdminLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  return (
    <div className="admin-shell">
      {sidebarOpen && (
        <div
          className="admin-sidebar-backdrop"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      <aside className={`admin-sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="admin-sidebar-logo">
          Teeline <span className="accent">ML</span>
          <div style={{ fontSize: 10, opacity: 0.5, marginTop: 4 }}>Admin</div>
        </div>
        <nav className="admin-nav">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="admin-main">
        <div className="admin-topbar">
          <button
            className="admin-hamburger"
            onClick={() => setSidebarOpen((v) => !v)}
            aria-label="Toggle sidebar"
            aria-expanded={sidebarOpen}
          >
            <span />
            <span />
            <span />
          </button>
          <div className="admin-topbar-links">
            <a href="/">Back to app</a>
            <a
              href="#"
              onClick={async (e) => {
                e.preventDefault();
                await api.auth.logout();
                window.location.href = "/";
              }}
            >
              Logout
            </a>
          </div>
        </div>
        <div className="admin-content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Add admin topbar links wrapper style to admin.css**

In `frontend/src/styles/admin.css`, change the `.admin-topbar` rule from:

```css
.admin-topbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
  padding: 12px 24px;
  border-bottom: 1px solid var(--rule);
  font-size: 12px;
  font-family: "DM Mono", monospace;
  color: var(--muted);
}
```

to:

```css
.admin-topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 24px;
  border-bottom: 1px solid var(--rule);
  font-size: 12px;
  font-family: "DM Mono", monospace;
  color: var(--muted);
}

.admin-topbar-links {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-left: auto;
}
```

- [ ] **Step 3: Add admin sidebar responsive styles to responsive.css**

Append to `frontend/src/styles/responsive.css`:

```css
/* ===== Admin hamburger ===== */
.admin-hamburger {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  flex-direction: column;
  gap: 5px;
}

.admin-hamburger span {
  display: block;
  width: 20px;
  height: 2px;
  background: var(--ink);
}

/* ===== Admin sidebar backdrop ===== */
.admin-sidebar-backdrop {
  display: none;
}

@media (max-width: 768px) {
  .admin-hamburger {
    display: flex;
  }

  .admin-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 200;
    transform: translateX(-100%);
    transition: transform 0.2s ease;
  }

  .admin-sidebar.open {
    transform: translateX(0);
  }

  .admin-sidebar-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    z-index: 199;
  }
}

/* ===== Admin phone adjustments ===== */
@media (max-width: 480px) {
  .admin-content {
    padding: 16px;
  }

  .admin-search {
    width: 100%;
  }

  .admin-table {
    display: block;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
}
```

- [ ] **Step 4: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/admin/AdminLayout.tsx frontend/src/styles/admin.css frontend/src/styles/responsive.css
git commit -m "feat(responsive): add collapsible admin sidebar with backdrop"
```

---

### Task 5: Page-specific responsive adjustments

**Files:**
- Modify: `frontend/src/styles/responsive.css`

- [ ] **Step 1: Add all page-specific container queries and media queries**

Append to `frontend/src/styles/responsive.css`:

```css
/* ===== Progress page: stat cards ===== */
@container (max-width: 480px) {
  .progress-stats {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
  }
}

/* ===== Leaderboard: hide streak on phone ===== */
@container (max-width: 480px) {
  .lb-streak {
    display: none;
  }

  .leaderboard-header .lb-streak {
    display: none;
  }
}

/* ===== Auth: reduce top margin on phone ===== */
@media (max-width: 480px) {
  .auth-container {
    margin-top: 24px;
  }

  .auth-container.auth-centered {
    min-height: calc(100vh - 60px);
  }
}

/* ===== About page: tighter on phone ===== */
@media (max-width: 480px) {
  .about-hero .section-title {
    font-size: 24px;
  }

  .about-heading {
    font-size: 17px;
  }

  .about-page {
    max-width: 100%;
  }
}

/* ===== Credits page: tighter on phone ===== */
@media (max-width: 480px) {
  .credits-page {
    padding: 20px 12px 40px;
  }

  .credits-hero h1 {
    font-size: 1.5rem;
  }

  .credits-card {
    padding: 16px;
  }

  .credits-deps {
    padding: 12px 16px;
  }
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/styles/responsive.css
git commit -m "feat(responsive): add page-specific mobile adjustments"
```

---

### Task 6: Visual verification in browser

**Files:** None (testing only)

- [ ] **Step 1: Start the frontend dev server**

Run: `cd frontend && npm run dev`

- [ ] **Step 2: Open browser and test at desktop width (>768px)**

Verify:
- Header tabs display horizontally as before
- Hamburger button is NOT visible
- Admin sidebar is always visible
- Canvas is 320x320
- All pages look unchanged from current behavior

- [ ] **Step 3: Test at tablet width (481-768px)**

Resize browser to ~600px wide. Verify:
- Hamburger button appears, tabs are hidden
- Clicking hamburger opens vertical mobile menu with all nav links
- User dropdown (Settings/Logout) appears at bottom of mobile menu
- Menu closes on navigation
- Admin: sidebar is hidden, hamburger in topbar opens it as overlay
- Admin: backdrop appears behind sidebar, clicking it closes sidebar
- Canvas still displays at 320px (fits within 600px viewport)

- [ ] **Step 4: Test at phone width (<=480px)**

Resize browser to ~375px wide. Verify:
- All tablet behavior still works
- `.main` padding is reduced (more room for canvas)
- Canvas shrinks if viewport is very narrow (<360px)
- Buttons have 44px min touch target height
- Progress stat cards show in 2-column grid
- Leaderboard hides streak column
- Auth page margin is reduced
- About/Credits headings are smaller
- Admin tables scroll horizontally if wider than viewport
- Admin search input is full width
- No horizontal scrollbar on any page

- [ ] **Step 5: Fix any issues found during testing**

Address any visual issues discovered in steps 2-4.

- [ ] **Step 6: Commit any fixes**

```bash
git add -u
git commit -m "fix(responsive): address visual issues from browser testing"
```
