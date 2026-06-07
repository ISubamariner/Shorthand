# Monitoring Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an admin monitoring page that shows live server/DB health metrics with 7-day historical snapshots and trend charts.

**Architecture:** New `monitoring` Django app with a `SystemSnapshot` model, a background collector thread (5-min interval), and three admin API endpoints. Frontend page uses Recharts for trend lines and the existing StatCard/admin table patterns.

**Tech Stack:** psutil (server metrics), Postgres system catalog queries (DB metrics), Recharts (frontend charts), existing DRF + React patterns.

---

## File Structure

### New files
| File | Responsibility |
|---|---|
| `backend/monitoring/__init__.py` | Package init |
| `backend/monitoring/apps.py` | AppConfig — starts collector thread |
| `backend/monitoring/models.py` | `SystemSnapshot` model |
| `backend/monitoring/collector.py` | Metric collection functions (psutil + SQL) |
| `backend/monitoring/worker.py` | Background thread with 5-min loop |
| `backend/monitoring/migrations/0001_initial.py` | Auto-generated migration |
| `backend/admin_api/views/monitoring.py` | Three API views (current, history, table-stats) |
| `frontend/src/pages/admin/MonitoringPage.tsx` | Full monitoring page with cards, charts, table |

### Modified files
| File | Change |
|---|---|
| `backend/requirements.txt` | Add `psutil` |
| `backend/config/settings/base.py` | Add `monitoring` to `INSTALLED_APPS` |
| `backend/config/settings/test.py` | Add `DISABLE_MONITORING_WORKER=1` |
| `backend/admin_api/urls.py` | Add 3 monitoring URL patterns |
| `frontend/package.json` | Add `recharts` dependency |
| `frontend/src/types/admin.ts` | Add monitoring type interfaces |
| `frontend/src/api/admin.ts` | Add monitoring API functions |
| `frontend/src/App.tsx` | Add lazy route for MonitoringPage |
| `frontend/src/pages/admin/AdminLayout.tsx` | Add Monitoring nav item |

---

### Task 1: Install dependencies

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `frontend/package.json`

- [ ] **Step 1: Add psutil to backend requirements**

Add to `backend/requirements.txt` after the `numpy` line:

```
psutil>=5.9,<7.0
```

- [ ] **Step 2: Install backend dependency**

Run:
```bash
cd backend && .venv/Scripts/pip.exe install psutil
```
Expected: Successfully installed psutil

- [ ] **Step 3: Add recharts to frontend**

Run:
```bash
cd frontend && npm install recharts
```
Expected: added 1 package (recharts has zero peer deps beyond react/react-dom which are already installed)

- [ ] **Step 4: Commit**

```bash
git add backend/requirements.txt frontend/package.json frontend/package-lock.json
git commit -m "chore: add psutil and recharts dependencies"
```

---

### Task 2: Create monitoring app — model and migration

**Files:**
- Create: `backend/monitoring/__init__.py`
- Create: `backend/monitoring/apps.py`
- Create: `backend/monitoring/models.py`
- Modify: `backend/config/settings/base.py`
- Modify: `backend/config/settings/test.py`

- [ ] **Step 1: Create the monitoring app directory and __init__.py**

Create empty file `backend/monitoring/__init__.py`.

- [ ] **Step 2: Create apps.py**

Create `backend/monitoring/apps.py`:

```python
import os

from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "monitoring"

    def ready(self):
        if os.environ.get("DISABLE_MONITORING_WORKER"):
            return
        if os.environ.get("RUN_MAIN") in (None, "true"):
            from .worker import start_collector

            start_collector()
```

- [ ] **Step 3: Create models.py**

Create `backend/monitoring/models.py`:

```python
from django.db import models


class SystemSnapshot(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    cpu_percent = models.FloatField()
    memory_percent = models.FloatField()
    memory_used_mb = models.FloatField()
    memory_total_mb = models.FloatField()
    disk_percent = models.FloatField()
    disk_used_gb = models.FloatField()
    disk_total_gb = models.FloatField()
    process_uptime_seconds = models.FloatField()
    db_size_mb = models.FloatField()
    db_connections = models.IntegerField()
    table_stats = models.JSONField(default=list)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Snapshot {self.timestamp:%Y-%m-%d %H:%M}"
```

- [ ] **Step 4: Add monitoring to INSTALLED_APPS**

In `backend/config/settings/base.py`, add `"monitoring"` to the `INSTALLED_APPS` list after `"admin_api"`:

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    # Local
    "accounts",
    "checker",
    "jobs",
    "admin_api",
    "monitoring",
]
```

- [ ] **Step 5: Disable monitoring worker in test settings**

In `backend/config/settings/test.py`, add after the existing `DISABLE_JOB_WORKERS` line:

```python
os.environ["DISABLE_MONITORING_WORKER"] = "1"
```

- [ ] **Step 6: Generate and verify migration**

Run:
```bash
cd backend && .venv/Scripts/python.exe manage.py makemigrations monitoring --settings=config.settings.test
```
Expected: `migrations/0001_initial.py` created with the `SystemSnapshot` model.

- [ ] **Step 7: Run migration in test DB to verify**

Run:
```bash
cd backend && .venv/Scripts/python.exe manage.py migrate --settings=config.settings.test
```
Expected: Applies `monitoring.0001_initial`

- [ ] **Step 8: Commit**

```bash
git add backend/monitoring/ backend/config/settings/base.py backend/config/settings/test.py
git commit -m "feat(monitoring): add SystemSnapshot model and monitoring app"
```

---

### Task 3: Create the metric collector

**Files:**
- Create: `backend/monitoring/collector.py`

- [ ] **Step 1: Write collector tests**

Create `backend/monitoring/tests.py`:

```python
from unittest.mock import MagicMock, patch

from django.test import TestCase


class CollectorServerMetricsTest(TestCase):

    @patch("monitoring.collector.psutil")
    def test_collect_server_metrics_returns_expected_keys(self, mock_psutil):
        mock_psutil.cpu_percent.return_value = 42.5
        mem = MagicMock()
        mem.percent = 65.0
        mem.used = 4 * 1024 * 1024 * 1024  # 4 GB in bytes
        mem.total = 16 * 1024 * 1024 * 1024
        mock_psutil.virtual_memory.return_value = mem
        disk = MagicMock()
        disk.percent = 55.0
        disk.used = 100 * 1024 * 1024 * 1024
        disk.total = 500 * 1024 * 1024 * 1024
        mock_psutil.disk_usage.return_value = disk

        from monitoring.collector import collect_server_metrics

        result = collect_server_metrics()

        self.assertAlmostEqual(result["cpu_percent"], 42.5)
        self.assertAlmostEqual(result["memory_percent"], 65.0)
        self.assertAlmostEqual(result["memory_used_mb"], 4096.0)
        self.assertAlmostEqual(result["memory_total_mb"], 16384.0)
        self.assertAlmostEqual(result["disk_percent"], 55.0)
        self.assertAlmostEqual(result["disk_used_gb"], 100.0)
        self.assertAlmostEqual(result["disk_total_gb"], 500.0)
        self.assertIn("process_uptime_seconds", result)
        self.assertGreater(result["process_uptime_seconds"], 0)


class CollectorSnapshotTest(TestCase):

    @patch("monitoring.collector.collect_db_metrics")
    @patch("monitoring.collector.collect_server_metrics")
    def test_collect_snapshot_combines_server_and_db(self, mock_server, mock_db):
        mock_server.return_value = {
            "cpu_percent": 10.0,
            "memory_percent": 20.0,
            "memory_used_mb": 2048.0,
            "memory_total_mb": 8192.0,
            "disk_percent": 30.0,
            "disk_used_gb": 50.0,
            "disk_total_gb": 200.0,
            "process_uptime_seconds": 3600.0,
        }
        mock_db.return_value = {
            "db_size_mb": 150.5,
            "db_connections": 5,
            "table_stats": [{"name": "auth_user", "row_count": 10, "size_mb": 0.1}],
        }

        from monitoring.collector import collect_snapshot

        result = collect_snapshot()

        self.assertEqual(result["cpu_percent"], 10.0)
        self.assertEqual(result["db_size_mb"], 150.5)
        self.assertEqual(result["db_connections"], 5)
        self.assertEqual(len(result["table_stats"]), 1)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd backend && .venv/Scripts/python.exe manage.py test monitoring.tests --settings=config.settings.test -v2
```
Expected: FAIL — `monitoring.collector` doesn't exist yet.

- [ ] **Step 3: Implement collector.py**

Create `backend/monitoring/collector.py`:

```python
import time

import psutil
from django.db import connection

_START_TIME = time.time()


def collect_server_metrics():
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "cpu_percent": cpu,
        "memory_percent": mem.percent,
        "memory_used_mb": round(mem.used / (1024 * 1024), 1),
        "memory_total_mb": round(mem.total / (1024 * 1024), 1),
        "disk_percent": disk.percent,
        "disk_used_gb": round(disk.used / (1024 ** 3), 1),
        "disk_total_gb": round(disk.total / (1024 ** 3), 1),
        "process_uptime_seconds": round(time.time() - _START_TIME, 1),
    }


def collect_db_metrics():
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_database_size(current_database())")
        db_size_bytes = cursor.fetchone()[0]

        cursor.execute(
            "SELECT count(*) FROM pg_stat_activity "
            "WHERE datname = current_database()"
        )
        db_connections = cursor.fetchone()[0]

        cursor.execute("""
            SELECT
                c.relname AS name,
                COALESCE(s.n_live_tup, 0) AS row_count,
                pg_total_relation_size(c.oid) AS size_bytes
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            LEFT JOIN pg_stat_user_tables s ON s.relid = c.oid
            WHERE n.nspname = 'public'
              AND c.relkind = 'r'
            ORDER BY pg_total_relation_size(c.oid) DESC
        """)
        table_stats = [
            {
                "name": row[0],
                "row_count": row[1],
                "size_mb": round(row[2] / (1024 * 1024), 3),
            }
            for row in cursor.fetchall()
        ]

    return {
        "db_size_mb": round(db_size_bytes / (1024 * 1024), 2),
        "db_connections": db_connections,
        "table_stats": table_stats,
    }


def collect_snapshot():
    data = collect_server_metrics()
    data.update(collect_db_metrics())
    return data
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd backend && .venv/Scripts/python.exe manage.py test monitoring.tests --settings=config.settings.test -v2
```
Expected: 2 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/monitoring/collector.py backend/monitoring/tests.py
git commit -m "feat(monitoring): add metric collector with psutil and Postgres queries"
```

---

### Task 4: Create the background worker

**Files:**
- Create: `backend/monitoring/worker.py`

- [ ] **Step 1: Create worker.py**

Create `backend/monitoring/worker.py`:

```python
import atexit
import logging
import os
import threading

import django.db

logger = logging.getLogger(__name__)

_shutdown = threading.Event()


def _collect_loop(interval: float, retention_days: int) -> None:
    from datetime import timedelta

    from django.utils import timezone

    from .collector import collect_snapshot
    from .models import SystemSnapshot

    logger.info(
        "Monitoring collector started (interval=%ds, retention=%dd)",
        interval,
        retention_days,
    )

    while not _shutdown.is_set():
        try:
            django.db.close_old_connections()
            data = collect_snapshot()
            SystemSnapshot.objects.create(**data)

            cutoff = timezone.now() - timedelta(days=retention_days)
            deleted, _ = SystemSnapshot.objects.filter(timestamp__lt=cutoff).delete()
            if deleted:
                logger.info("Pruned %d old snapshots", deleted)

        except Exception:
            logger.exception("Monitoring collector error")

        _shutdown.wait(interval)


def start_collector() -> None:
    interval = int(os.environ.get("MONITORING_INTERVAL_SECONDS", "300"))
    retention_days = int(os.environ.get("MONITORING_RETENTION_DAYS", "7"))

    t = threading.Thread(
        target=_collect_loop,
        args=(interval, retention_days),
        daemon=True,
    )
    t.start()
    atexit.register(stop_collector)
    logger.info("Monitoring collector thread started")


def stop_collector() -> None:
    _shutdown.set()
    logger.info("Monitoring collector shutting down")
```

- [ ] **Step 2: Verify the app starts without errors**

Run:
```bash
cd backend && DISABLE_MONITORING_WORKER=1 .venv/Scripts/python.exe manage.py check --settings=config.settings.test
```
Expected: `System check identified no issues.`

- [ ] **Step 3: Commit**

```bash
git add backend/monitoring/worker.py
git commit -m "feat(monitoring): add background collector thread with auto-prune"
```

---

### Task 5: Create admin API endpoints

**Files:**
- Create: `backend/admin_api/views/monitoring.py`
- Modify: `backend/admin_api/urls.py`

- [ ] **Step 1: Write endpoint tests**

Add to `backend/monitoring/tests.py`:

```python
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth.models import User


class MonitoringEndpointsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user("monitoradmin", "ma@test.com", "pass12345")
        cls.admin.is_staff = True
        cls.admin.save()
        cls.user = User.objects.create_user("regularuser", "ru@test.com", "pass12345")

    def setUp(self):
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin)
        self.auth_client = APIClient()
        self.auth_client.force_authenticate(user=self.user)
        self.anon_client = APIClient()

    @patch("monitoring.collector.psutil")
    def test_current_returns_200_for_admin(self, mock_psutil):
        mock_psutil.cpu_percent.return_value = 10.0
        mem = MagicMock()
        mem.percent = 20.0
        mem.used = 1024 * 1024 * 1024
        mem.total = 4 * 1024 * 1024 * 1024
        mock_psutil.virtual_memory.return_value = mem
        disk = MagicMock()
        disk.percent = 30.0
        disk.used = 50 * 1024 ** 3
        disk.total = 200 * 1024 ** 3
        mock_psutil.disk_usage.return_value = disk

        r = self.admin_client.get("/api/admin/monitoring/current/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("cpu_percent", r.data)
        self.assertIn("db_size_mb", r.data)

    def test_current_forbidden_for_non_admin(self):
        r = self.auth_client.get("/api/admin/monitoring/current/")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_current_unauthorized_for_anon(self):
        r = self.anon_client.get("/api/admin/monitoring/current/")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_history_returns_200(self):
        r = self.admin_client.get("/api/admin/monitoring/history/?range=24h")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIsInstance(r.data, list)

    def test_history_7d_returns_200(self):
        r = self.admin_client.get("/api/admin/monitoring/history/?range=7d")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_table_stats_returns_200(self):
        r = self.admin_client.get("/api/admin/monitoring/table-stats/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIsInstance(r.data, list)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd backend && .venv/Scripts/python.exe manage.py test monitoring.tests.MonitoringEndpointsTest --settings=config.settings.test -v2
```
Expected: FAIL — URL not found (404).

- [ ] **Step 3: Create the monitoring views**

Create `backend/admin_api/views/monitoring.py`:

```python
from datetime import timedelta

from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_api.permissions import IsAdminUser
from monitoring.collector import collect_snapshot
from monitoring.models import SystemSnapshot


class MonitoringCurrentView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        data = collect_snapshot()
        return Response(data)


class MonitoringHistoryView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        range_param = request.query_params.get("range", "24h")
        if range_param == "7d":
            cutoff = timezone.now() - timedelta(days=7)
        else:
            cutoff = timezone.now() - timedelta(hours=24)

        snapshots = SystemSnapshot.objects.filter(
            timestamp__gte=cutoff
        ).order_by("timestamp")

        if range_param == "7d":
            snapshot_list = list(snapshots)
            snapshots_sampled = snapshot_list[::6]
        else:
            snapshots_sampled = list(snapshots)

        data = [
            {
                "timestamp": s.timestamp.isoformat(),
                "cpu_percent": s.cpu_percent,
                "memory_percent": s.memory_percent,
                "disk_percent": s.disk_percent,
                "db_size_mb": s.db_size_mb,
                "db_connections": s.db_connections,
            }
            for s in snapshots_sampled
        ]
        return Response(data)


class MonitoringTableStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        latest = SystemSnapshot.objects.first()
        if latest:
            return Response(latest.table_stats)
        data = collect_snapshot()
        return Response(data.get("table_stats", []))
```

- [ ] **Step 4: Add URL patterns**

In `backend/admin_api/urls.py`, add the imports at the top with the other view imports:

```python
from .views.monitoring import (
    MonitoringCurrentView,
    MonitoringHistoryView,
    MonitoringTableStatsView,
)
```

Add these paths to the `urlpatterns` list at the end:

```python
    path("monitoring/current/", MonitoringCurrentView.as_view(), name="admin-monitoring-current"),
    path("monitoring/history/", MonitoringHistoryView.as_view(), name="admin-monitoring-history"),
    path("monitoring/table-stats/", MonitoringTableStatsView.as_view(), name="admin-monitoring-table-stats"),
```

- [ ] **Step 5: Run tests to verify they pass**

Run:
```bash
cd backend && .venv/Scripts/python.exe manage.py test monitoring.tests --settings=config.settings.test -v2
```
Expected: All 8 tests pass (2 collector + 6 endpoint).

- [ ] **Step 6: Run full endpoint test suite to check for regressions**

Run:
```bash
cd backend && .venv/Scripts/python.exe manage.py test tests.test_endpoints --settings=config.settings.test
```
Expected: All 71 existing tests still pass.

- [ ] **Step 7: Commit**

```bash
git add backend/monitoring/tests.py backend/admin_api/views/monitoring.py backend/admin_api/urls.py
git commit -m "feat(monitoring): add current, history, and table-stats admin endpoints"
```

---

### Task 6: Add frontend types and API client

**Files:**
- Modify: `frontend/src/types/admin.ts`
- Modify: `frontend/src/api/admin.ts`

- [ ] **Step 1: Add monitoring types**

Add to the end of `frontend/src/types/admin.ts`:

```typescript
export interface MonitoringSnapshot {
  cpu_percent: number;
  memory_percent: number;
  memory_used_mb: number;
  memory_total_mb: number;
  disk_percent: number;
  disk_used_gb: number;
  disk_total_gb: number;
  process_uptime_seconds: number;
  db_size_mb: number;
  db_connections: number;
  table_stats: MonitoringTableStat[];
}

export interface MonitoringHistoryPoint {
  timestamp: string;
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
  db_size_mb: number;
  db_connections: number;
}

export interface MonitoringTableStat {
  name: string;
  row_count: number;
  size_mb: number;
}
```

- [ ] **Step 2: Add monitoring API functions**

Add the `monitoring` namespace to the `adminApi` object in `frontend/src/api/admin.ts`. Add the import for the new types at the top:

```typescript
import type {
  // ... existing imports ...
  MonitoringSnapshot,
  MonitoringHistoryPoint,
  MonitoringTableStat,
} from "../types/admin";
```

Add inside the `adminApi` object, after the `settings` section:

```typescript
  monitoring: {
    current(): Promise<MonitoringSnapshot> {
      return adminRequest("/monitoring/current/");
    },
    history(range: "24h" | "7d" = "24h"): Promise<MonitoringHistoryPoint[]> {
      return adminRequest(`/monitoring/history/?range=${range}`);
    },
    tableStats(): Promise<MonitoringTableStat[]> {
      return adminRequest("/monitoring/table-stats/");
    },
  },
```

- [ ] **Step 3: Verify TypeScript compiles**

Run:
```bash
cd frontend && npx tsc --noEmit
```
Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types/admin.ts frontend/src/api/admin.ts
git commit -m "feat(monitoring): add frontend API client and types"
```

---

### Task 7: Create the MonitoringPage component

**Files:**
- Create: `frontend/src/pages/admin/MonitoringPage.tsx`

- [ ] **Step 1: Create MonitoringPage.tsx**

Create `frontend/src/pages/admin/MonitoringPage.tsx`:

```tsx
import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { adminApi } from "../../api/admin";
import { StatCard } from "../../components/admin/StatCard";
import type {
  MonitoringHistoryPoint,
  MonitoringSnapshot,
  MonitoringTableStat,
} from "../../types/admin";

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}d ${h}h ${m}m`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

function formatSize(mb: number): string {
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`;
  return `${mb.toFixed(1)} MB`;
}

function statusColor(pct: number): string {
  if (pct >= 85) return "#dc2626";
  if (pct >= 60) return "#d97706";
  return "#16a34a";
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

const CHART_STYLE = {
  fontSize: 11,
  fontFamily: "'DM Mono', monospace",
};

function MetricChart({
  data,
  dataKey,
  title,
  color,
  unit,
}: {
  data: MonitoringHistoryPoint[];
  dataKey: keyof MonitoringHistoryPoint;
  title: string;
  color: string;
  unit: string;
}) {
  return (
    <div style={{ marginBottom: 24 }}>
      <h3
        style={{
          fontFamily: "'Syne', sans-serif",
          fontSize: 14,
          fontWeight: 600,
          marginBottom: 8,
          color: "var(--ink)",
        }}
      >
        {title}
      </h3>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data} style={CHART_STYLE}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--rule)" />
          <XAxis
            dataKey="timestamp"
            tickFormatter={formatTime}
            stroke="var(--muted)"
            tick={{ fontSize: 10 }}
          />
          <YAxis stroke="var(--muted)" tick={{ fontSize: 10 }} unit={unit} />
          <Tooltip
            labelFormatter={(v) => new Date(v as string).toLocaleString()}
            contentStyle={{
              background: "var(--paper)",
              border: "1px solid var(--rule)",
              fontSize: 12,
              fontFamily: "'DM Mono', monospace",
            }}
          />
          <Area
            type="monotone"
            dataKey={dataKey}
            stroke={color}
            fill={color}
            fillOpacity={0.1}
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

type SortKey = "name" | "row_count" | "size_mb";

export function MonitoringPage() {
  const [current, setCurrent] = useState<MonitoringSnapshot | null>(null);
  const [history, setHistory] = useState<MonitoringHistoryPoint[]>([]);
  const [tableStats, setTableStats] = useState<MonitoringTableStat[]>([]);
  const [range, setRange] = useState<"24h" | "7d">("24h");
  const [error, setError] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("size_mb");
  const [sortAsc, setSortAsc] = useState(false);

  useEffect(() => {
    Promise.all([adminApi.monitoring.current(), adminApi.monitoring.tableStats()])
      .then(([c, t]) => {
        setCurrent(c);
        setTableStats(t);
      })
      .catch(() => setError("Failed to load monitoring data"));
  }, []);

  useEffect(() => {
    adminApi.monitoring
      .history(range)
      .then(setHistory)
      .catch(() => setError("Failed to load history"));
  }, [range]);

  useEffect(() => {
    const interval = setInterval(() => {
      adminApi.monitoring.current().then(setCurrent).catch(() => {});
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(key === "name");
    }
  };

  const sortedTables = [...tableStats].sort((a, b) => {
    const av = a[sortKey];
    const bv = b[sortKey];
    if (typeof av === "string" && typeof bv === "string") {
      return sortAsc ? av.localeCompare(bv) : bv.localeCompare(av);
    }
    return sortAsc ? (av as number) - (bv as number) : (bv as number) - (av as number);
  });

  if (error) return <p style={{ color: "var(--accent)" }}>{error}</p>;
  if (!current)
    return (
      <p style={{ color: "var(--muted)", fontSize: 12 }}>Loading...</p>
    );

  return (
    <div>
      <h1 className="admin-page-title">Monitoring</h1>

      <div className="admin-stats-grid">
        <StatCard
          label="CPU"
          value={`${current.cpu_percent.toFixed(1)}%`}
        />
        <StatCard
          label="Memory"
          value={`${current.memory_percent.toFixed(1)}%`}
        />
        <StatCard
          label="Disk"
          value={`${current.disk_percent.toFixed(1)}%`}
        />
        <StatCard
          label="Uptime"
          value={formatUptime(current.process_uptime_seconds)}
        />
        <StatCard label="DB Size" value={formatSize(current.db_size_mb)} />
        <StatCard label="Connections" value={current.db_connections} />
      </div>

      <div style={{ marginBottom: 16, display: "flex", gap: 8 }}>
        {(["24h", "7d"] as const).map((r) => (
          <button
            key={r}
            className="admin-btn"
            style={
              range === r
                ? { background: "var(--ink)", color: "var(--paper)" }
                : undefined
            }
            onClick={() => setRange(r)}
          >
            {r}
          </button>
        ))}
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 24,
          marginBottom: 32,
        }}
      >
        <MetricChart
          data={history}
          dataKey="cpu_percent"
          title="CPU Usage"
          color="#3b82f6"
          unit="%"
        />
        <MetricChart
          data={history}
          dataKey="memory_percent"
          title="Memory Usage"
          color="#8b5cf6"
          unit="%"
        />
        <MetricChart
          data={history}
          dataKey="disk_percent"
          title="Disk Usage"
          color="#f59e0b"
          unit="%"
        />
        <MetricChart
          data={history}
          dataKey="db_size_mb"
          title="Database Size"
          color="#10b981"
          unit=" MB"
        />
      </div>

      <h2
        style={{
          fontFamily: "'Syne', sans-serif",
          fontSize: 16,
          margin: "24px 0 12px",
        }}
      >
        Table Sizes
      </h2>
      <table className="admin-table">
        <thead>
          <tr>
            <th
              style={{ cursor: "pointer" }}
              onClick={() => handleSort("name")}
            >
              Table Name {sortKey === "name" ? (sortAsc ? "↑" : "↓") : ""}
            </th>
            <th
              style={{ cursor: "pointer" }}
              onClick={() => handleSort("row_count")}
            >
              Row Count{" "}
              {sortKey === "row_count" ? (sortAsc ? "↑" : "↓") : ""}
            </th>
            <th
              style={{ cursor: "pointer" }}
              onClick={() => handleSort("size_mb")}
            >
              Size (MB) {sortKey === "size_mb" ? (sortAsc ? "↑" : "↓") : ""}
            </th>
          </tr>
        </thead>
        <tbody>
          {sortedTables.map((t) => (
            <tr key={t.name}>
              <td>{t.name}</td>
              <td>{t.row_count.toLocaleString()}</td>
              <td>{t.size_mb.toFixed(3)}</td>
            </tr>
          ))}
          {sortedTables.length === 0 && (
            <tr>
              <td
                colSpan={3}
                style={{ textAlign: "center", color: "var(--muted)" }}
              >
                No data
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

Run:
```bash
cd frontend && npx tsc --noEmit
```
Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/admin/MonitoringPage.tsx
git commit -m "feat(monitoring): add MonitoringPage with charts, cards, and table stats"
```

---

### Task 8: Wire up routing and navigation

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/pages/admin/AdminLayout.tsx`

- [ ] **Step 1: Add lazy import and route in App.tsx**

In `frontend/src/App.tsx`, add the lazy import after the `SettingsPage` lazy import:

```tsx
const MonitoringPage = lazy(() =>
  import("./pages/admin/MonitoringPage").then((m) => ({ default: m.MonitoringPage }))
);
```

Add the route inside the `<Route element={<AdminLayout />}>` block, after the settings route:

```tsx
                    <Route path="monitoring" element={<MonitoringPage />} />
```

- [ ] **Step 2: Add nav item in AdminLayout**

In `frontend/src/pages/admin/AdminLayout.tsx`, add to the `NAV_ITEMS` array after the Settings entry:

```tsx
  { to: "/admin/monitoring", label: "Monitoring" },
```

- [ ] **Step 3: Verify TypeScript compiles**

Run:
```bash
cd frontend && npx tsc --noEmit
```
Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.tsx frontend/src/pages/admin/AdminLayout.tsx
git commit -m "feat(monitoring): wire up admin routing and navigation"
```

---

### Task 9: Integration test — start dev server and verify in browser

- [ ] **Step 1: Start the full stack**

Run:
```bash
docker compose up -d
```

- [ ] **Step 2: Apply migration**

Run:
```bash
cd backend && docker compose exec backend python manage.py migrate
```

- [ ] **Step 3: Navigate to the monitoring page**

Open `http://localhost:5173/admin/monitoring` in the browser (must be logged in as admin).

Verify:
- 6 stat cards render with live values (CPU, Memory, Disk, Uptime, DB Size, Connections)
- 24h/7d toggle buttons appear and are clickable
- Charts section renders (may be empty if no history yet — that's fine on first load)
- Table stats table shows all database tables with row counts and sizes
- Clicking column headers sorts the table
- "Monitoring" appears in the admin sidebar nav and highlights when active

- [ ] **Step 4: Run full backend test suite**

Run:
```bash
cd backend && .venv/Scripts/python.exe manage.py test tests.test_endpoints monitoring.tests --settings=config.settings.test
```
Expected: All tests pass (71 existing + 8 new monitoring tests).

- [ ] **Step 5: Commit any fixes if needed**
