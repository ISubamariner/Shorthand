# Admin Panel Design

## Overview

Admin panel for the Shorthand app with two-tier RBAC (Admin / User). Admin views live at `/admin` in the browser with a dedicated dashboard-style layout. Backend exposes custom DRF endpoints under `/api/admin/` in a new `admin_api` Django app.

## Authentication & Authorization

### RBAC Model

Two tiers using Django's built-in `is_staff` field on the User model:

- **Admin** (`is_staff=True`): Full access to all admin endpoints and UI
- **User** (`is_staff=False`): No admin access; redirected to `/` if they hit `/admin/*`

No migrations needed — `is_staff` already exists on Django's User model.

### Backend Permission

All admin API endpoints use DRF's built-in `rest_framework.permissions.IsAdminUser` permission class, which checks `request.user.is_staff`. Applied at the viewset level.

### Frontend Guard

An `AdminRoute` component wraps the `/admin/*` route tree. It checks `is_staff` from the auth context (returned by `/api/auth/me/`) and redirects non-admins to `/`.

### Granting Admin Access

Via Django management command (`python manage.py make_admin <username>`) or Django shell. The command sets `is_staff=True` on the given user and confirms the change. No self-service admin promotion.

### Jobs Integration

The existing `jobs` app has a `Job` model with status tracking (PENDING, RUNNING, COMPLETED, FAILED, DEAD), retry logic, and error logging. The admin panel reads this model directly — no new job models needed. The admin Jobs page is the first UI for this system.

## Frontend Architecture

### Layout

A separate `AdminLayout` component with:

- **Sidebar**: Dashboard, Users, Content, Analytics, Jobs, Audit Log, Settings
- **Topbar**: Current admin user, link back to main app, logout

This is a completely different layout from the main app's `Header` component.

### Routes

```
/admin            → DashboardPage    (overview stats)
/admin/users      → UsersPage        (user list)
/admin/users/:id  → UserDetailPage   (single user view/edit)
/admin/content    → ContentPage      (symbols & words CRUD)
/admin/analytics  → AnalyticsPage    (usage charts & stats)
/admin/jobs       → JobsPage         (background job queue)
/admin/audit-log  → AuditLogPage     (admin action history)
/admin/settings   → SettingsPage     (system configuration)
```

### File Organization

```
frontend/src/pages/admin/
├── AdminLayout.tsx
├── DashboardPage.tsx
├── UsersPage.tsx
├── UserDetailPage.tsx
├── ContentPage.tsx
├── AnalyticsPage.tsx
├── JobsPage.tsx
├── AuditLogPage.tsx
└── SettingsPage.tsx

frontend/src/components/admin/
├── AdminRoute.tsx        # Auth guard + lazy loader
├── Sidebar.tsx           # Navigation sidebar
├── DataTable.tsx         # Reusable sortable/filterable table
├── StatCard.tsx          # Dashboard stat display
├── Pagination.tsx        # Shared pagination controls
└── ActionConfirm.tsx     # Confirmation modal for destructive actions
```

### Lazy Loading

The entire admin route tree is lazy-loaded via `React.lazy()` in `App.tsx`. Admin code is not included in the main bundle — it's fetched only when an admin navigates to `/admin`.

### State Management

No global state library. Follows the existing app pattern: each page fetches its own data via API calls with local component state. `DataTable` handles client-side sort/filter on the current page; the API handles server-side pagination and search.

Destructive actions (deactivate user, delete content, cancel job) require confirmation via `ActionConfirm` modal.

## Backend API Design

### Django App

New `admin_api` app — keeps admin endpoints isolated from `checker` and `accounts`.

### URL Prefix

`/api/admin/` — all endpoints require JWT auth + `is_staff`.

### Endpoints

#### Dashboard

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/admin/dashboard/stats/` | User count, attempt count, active today, etc. |

#### Users

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/admin/users/` | Paginated user list (search, filter by active/staff) |
| GET | `/api/admin/users/:id/` | User detail + stats |
| PATCH | `/api/admin/users/:id/` | Edit user (is_active, is_staff) |
| POST | `/api/admin/users/:id/reset-password/` | Trigger password reset |

#### Content

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/admin/content/symbols/` | Symbol list with attempt counts |
| POST | `/api/admin/content/symbols/` | Create symbol |
| PATCH | `/api/admin/content/symbols/:id/` | Edit symbol |
| DELETE | `/api/admin/content/symbols/:id/` | Delete symbol |
| GET | `/api/admin/content/words/` | Word list with topic info |
| POST | `/api/admin/content/words/` | Create word |
| PATCH | `/api/admin/content/words/:id/` | Edit word |
| DELETE | `/api/admin/content/words/:id/` | Delete word |

#### Analytics

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/admin/analytics/usage/` | Attempts over time (daily/weekly) |
| GET | `/api/admin/analytics/leaderboard/` | Leaderboard with admin controls |
| GET | `/api/admin/analytics/retention/` | User retention stats |

#### Jobs

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/admin/jobs/` | Paginated job list (filter by status) |
| GET | `/api/admin/jobs/:id/` | Job detail with logs |
| POST | `/api/admin/jobs/:id/retry/` | Retry failed job |
| POST | `/api/admin/jobs/:id/cancel/` | Cancel pending job |

#### Audit Log

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/admin/audit-log/` | Paginated, filterable (actor, action, date range) |

#### Settings

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/admin/settings/` | Current system settings |
| PATCH | `/api/admin/settings/` | Update settings |

### Permission Pattern

A single `IsAdminUser` permission class applied at the viewset level. No per-action granularity needed since there is only one admin role.

Audit logging helper called in `perform_create`, `perform_update`, `perform_destroy` on each viewset.

## Data Models

Two new models in the `admin_api` app. Both follow the project's existing `TimestampedModel` pattern (UUID primary key).

### AuditLog

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| actor | FK → User | Admin who performed the action |
| action | CharField | Action identifier (e.g. `user.deactivate`, `content.symbol.create`) |
| target_type | CharField | Entity type (e.g. `user`, `symbol`, `word`, `setting`) |
| target_id | CharField | UUID or PK of the target entity (string for flexibility) |
| details | JSONField | Before/after snapshots, contextual data |
| created_at | DateTimeField | Auto-set on creation |

**Action format:** `{domain}.{entity}.{verb}` — e.g. `content.symbol.delete`, `user.deactivate`, `settings.update`.

**Details format:**
- Edits: `{"before": {...}, "after": {...}}`
- Creates/deletes: `{"data": {...}}`

Audit entries are immutable — no update or delete endpoints. Entries persist even if the target entity is deleted (no cascade).

### SystemSetting

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| key | CharField (unique) | Setting identifier (e.g. `maintenance_mode`, `leaderboard_enabled`) |
| value | JSONField | Flexible type — bool, string, number, object |
| updated_at | DateTimeField | Auto-set on save |
| updated_by | FK → User | Admin who last changed the setting |

### Existing Models

No changes to existing models. The admin panel reads `User`, `Symbol`, `Word`, `Attempt`, `UserStats`, `WordAttemptSession`, and job models as-is.

## Auth Context Changes

The `/api/auth/me/` response is extended to include `is_staff`. The frontend stores `isAdmin` alongside existing auth state.

### Admin API Client

New `frontend/src/api/admin.ts` file following the existing `api.*` namespace pattern from `client.ts`:

- `api.admin.dashboard` — dashboard stats
- `api.admin.users` — user CRUD
- `api.admin.content` — symbol/word CRUD
- `api.admin.analytics` — usage/retention queries
- `api.admin.jobs` — job queue management
- `api.admin.auditLog` — audit log queries
- `api.admin.settings` — system settings
