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
  const [stale, setStale] = useState(false);
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
      adminApi.monitoring
        .current()
        .then((c) => {
          setCurrent(c);
          setStale(false);
        })
        .catch(() => setStale(true));
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
      {stale && (
        <p style={{ color: "var(--accent)", fontSize: 12, marginBottom: 12 }}>
          Auto-refresh failed — showing stale data
        </p>
      )}

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
