# Server & Database Monitoring Dashboard — Design Spec

## Overview

An admin-only monitoring page that shows live server health metrics and database size information, with historical snapshots stored every 5 minutes and retained for 7 days. Provides trend charts and a table-level size breakdown.

## Data Model

New Django app: `monitoring`.

### `SystemSnapshot`

| Field | Type | Notes |
|---|---|---|
| `id` | AutoField | PK |
| `timestamp` | DateTimeField | indexed, auto_now_add |
| `cpu_percent` | FloatField | 0–100 |
| `memory_percent` | FloatField | 0–100 |
| `memory_used_mb` | FloatField | |
| `memory_total_mb` | FloatField | |
| `disk_percent` | FloatField | 0–100 |
| `disk_used_gb` | FloatField | |
| `disk_total_gb` | FloatField | |
| `process_uptime_seconds` | FloatField | Django process uptime |
| `db_size_mb` | FloatField | total database size |
| `db_connections` | IntegerField | active connections |
| `table_stats` | JSONField | `[{name, row_count, size_mb}]` |

One row every 5 minutes. Rows older than 7 days are pruned on each collection cycle.

## Backend

### New app: `monitoring/`

```
backend/monitoring/
├── __init__.py
├── apps.py              # MonitoringConfig — starts collector thread
├── models.py            # SystemSnapshot
├── collector.py         # metric collection functions
├── worker.py            # background thread (5-min loop)
├── migrations/
│   └── 0001_initial.py
```

### Collector (`collector.py`)

Functions that gather metrics:

- `collect_server_metrics()` — uses `psutil` for CPU (1-second sample), memory, disk. Uses `time.time() - START_TIME` for process uptime (module-level constant set at import).
- `collect_db_metrics()` — raw SQL queries against Postgres:
  - `SELECT pg_database_size(current_database())` for total DB size
  - `SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()` for connections
  - Per-table stats via `pg_total_relation_size` and `pg_class`/`pg_stat_user_tables` join for row counts and sizes
- `collect_snapshot()` — combines both, returns a dict ready for `SystemSnapshot.objects.create()`.

### Background Worker (`worker.py`)

- Daemon thread started in `MonitoringConfig.ready()`
- Guarded by `DISABLE_MONITORING_WORKER` env var (set in test settings)
- Also guarded by `RUN_MAIN` check to avoid double-start in Django's auto-reloader
- Loop: collect snapshot → save to DB → prune rows older than 7 days → sleep 300 seconds
- Catches and logs exceptions per cycle (never crashes the thread)

### API Endpoints

Added to `admin_api/urls.py` under `/api/admin/monitoring/`:

| Method | Path | Description |
|---|---|---|
| GET | `/current/` | Live snapshot (collected on request, not persisted) |
| GET | `/history/?range=24h\|7d` | Historical snapshots for charting |
| GET | `/table-stats/` | Latest table-level size breakdown |

All use `IsAdminUser` permission.

**`/current/`** — calls `collect_snapshot()` directly and returns the result. No DB write.

**`/history/?range=24h|7d`** — queries `SystemSnapshot` filtered by timestamp. For 7d range, downsamples to ~1 point per 30 minutes (every 6th row) to keep payload reasonable. Returns array of `{timestamp, cpu_percent, memory_percent, disk_percent, db_size_mb, db_connections}`.

**`/table-stats/`** — returns the `table_stats` JSON from the most recent snapshot, or collects live if no snapshots exist.

### Views Structure

New file: `admin_api/views/monitoring.py` — three `APIView` classes following the existing admin view pattern.

### Dependencies

Add `psutil` to backend requirements. Already pure-Python with prebuilt wheels, no compilation needed.

## Frontend

### New Page: `MonitoringPage`

Path: `frontend/src/pages/admin/MonitoringPage.tsx`

**Layout (top to bottom):**

1. **Status cards row** — 6 cards showing current values:
   - CPU % (with color: green < 60, yellow < 85, red >= 85)
   - Memory % (same thresholds)
   - Disk % (same thresholds)
   - Uptime (formatted as "Xd Xh Xm")
   - Database size (formatted as MB/GB)
   - Active connections

2. **Time range toggle** — "24h" / "7d" pill toggle

3. **Charts section** — 2x2 grid of line/area charts:
   - CPU usage over time
   - Memory usage over time
   - Disk usage over time
   - Database size over time

4. **Table stats section** — sortable table:
   - Columns: Table Name, Row Count, Size (MB)
   - Default sort by size descending

### Charting Library

Add `recharts` to frontend dependencies. React-native, lightweight, good line/area chart support.

### Data Fetching

- On mount: fetch `/current/` and `/table-stats/` in parallel
- On mount + range change: fetch `/history/?range=<selected>`
- Auto-refresh current stats every 30 seconds while page is visible
- Use existing `adminApi` client from `api/admin.ts`

### Navigation

Add "Monitoring" link to the admin sidebar/nav in `AdminLayout`. Place it after "Settings" as the last item — it's an operational tool, not a daily-use page.

### Styling

Follow existing admin page patterns (card components, table styling). Use Tailwind classes consistent with the rest of the admin UI.

## Settings

- `DISABLE_MONITORING_WORKER=1` — prevents background thread from starting (added to test settings alongside `DISABLE_JOB_WORKERS`)
- `MONITORING_INTERVAL_SECONDS` — optional override, defaults to 300
- `MONITORING_RETENTION_DAYS` — optional override, defaults to 7

## Testing

### Backend

- Unit tests for `collector.py` — mock `psutil` and DB cursor, verify dict shape
- Endpoint smoke tests for all three monitoring endpoints (added to existing test suite)
- Background worker is disabled in test settings

### Frontend

- No new frontend tests (consistent with existing admin pages)

## Migration

Single migration: `0001_initial.py` creating the `SystemSnapshot` table with index on `timestamp`.

## File Changes Summary

### New files
- `backend/monitoring/__init__.py`
- `backend/monitoring/apps.py`
- `backend/monitoring/models.py`
- `backend/monitoring/collector.py`
- `backend/monitoring/worker.py`
- `backend/monitoring/migrations/__init__.py`
- `backend/monitoring/migrations/0001_initial.py`
- `backend/admin_api/views/monitoring.py`
- `frontend/src/pages/admin/MonitoringPage.tsx`

### Modified files
- `backend/config/settings/base.py` — add `monitoring` to `INSTALLED_APPS`
- `backend/config/settings/test.py` — add `DISABLE_MONITORING_WORKER=1`
- `backend/admin_api/urls.py` — add monitoring URL patterns
- `frontend/src/App.tsx` — add lazy route for MonitoringPage
- `frontend/src/components/admin/AdminLayout.tsx` — add Monitoring nav link
- `frontend/src/api/admin.ts` — add monitoring API functions
- `backend/requirements.txt` (or equivalent) — add `psutil`
- `frontend/package.json` — add `recharts`
