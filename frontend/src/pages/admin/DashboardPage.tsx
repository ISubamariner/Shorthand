import { useEffect, useState } from "react";
import { adminApi } from "../../api/admin";
import { StatCard } from "../../components/admin/StatCard";
import type { DashboardStats } from "../../types/admin";

export function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    adminApi.dashboard
      .stats()
      .then(setStats)
      .catch(() => setError("Failed to load dashboard stats"));
  }, []);

  if (error) return <p style={{ color: "var(--accent)" }}>{error}</p>;
  if (!stats) return <p style={{ color: "var(--muted)", fontSize: 12 }}>Loading...</p>;

  return (
    <div>
      <h1 className="admin-page-title">Dashboard</h1>
      <div className="admin-stats-grid">
        <StatCard label="Total Users" value={stats.user_count} />
        <StatCard label="Total Attempts" value={stats.attempt_count} />
        <StatCard label="Active Today" value={stats.active_today} />
        <StatCard label="Pending Jobs" value={stats.pending_jobs} />
        <StatCard label="Failed Jobs" value={stats.failed_jobs} />
      </div>
    </div>
  );
}
