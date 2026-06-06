import { useEffect, useState } from "react";
import { adminApi } from "../../api/admin";
import { StatCard } from "../../components/admin/StatCard";
import type { RetentionStats, UsageStats } from "../../types/admin";

export function AnalyticsPage() {
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [retention, setRetention] = useState<RetentionStats | null>(null);
  const [days, setDays] = useState(30);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([adminApi.analytics.usage(days), adminApi.analytics.retention(days)])
      .then(([u, r]) => { setUsage(u); setRetention(r); })
      .catch(() => setError("Failed to load analytics"));
  }, [days]);

  if (error) return <p style={{ color: "var(--accent)" }}>{error}</p>;
  if (!usage || !retention) return <p style={{ color: "var(--muted)", fontSize: 12 }}>Loading...</p>;

  return (
    <div>
      <h1 className="admin-page-title">Analytics</h1>
      <div style={{ marginBottom: 16 }}>
        <select
          className="admin-search"
          style={{ width: "auto" }}
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>
      <div className="admin-stats-grid">
        <StatCard label="Total Attempts" value={usage.total} />
        <StatCard label="Total Users" value={retention.total_users} />
        <StatCard label="Active Users" value={retention.active_users} />
        <StatCard label="Retention Rate" value={`${retention.retention_rate}%`} />
      </div>

      <h2 style={{ fontFamily: "'Syne', sans-serif", fontSize: 16, margin: "24px 0 12px" }}>
        Daily Attempts
      </h2>
      <table className="admin-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Attempts</th>
          </tr>
        </thead>
        <tbody>
          {usage.daily.map((row) => (
            <tr key={row.date}>
              <td>{row.date}</td>
              <td>{row.count}</td>
            </tr>
          ))}
          {usage.daily.length === 0 && (
            <tr><td colSpan={2} style={{ textAlign: "center", color: "var(--muted)" }}>No data</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
