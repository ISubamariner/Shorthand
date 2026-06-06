import { useEffect, useState } from "react";
import { adminApi } from "../../api/admin";
import { ActionConfirm } from "../../components/admin/ActionConfirm";
import type { AdminJob, PaginatedResponse } from "../../types/admin";

export function JobsPage() {
  const [data, setData] = useState<PaginatedResponse<AdminJob> | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [action, setAction] = useState<{ type: "retry" | "cancel"; job: AdminJob } | null>(null);

  const loadJobs = () => {
    adminApi.jobs
      .list({ status: statusFilter || undefined, page })
      .then(setData)
      .catch(() => setError("Failed to load jobs"));
  };

  useEffect(loadJobs, [statusFilter, page]);

  const handleAction = async () => {
    if (!action) return;
    try {
      if (action.type === "retry") {
        await adminApi.jobs.retry(action.job.id);
      } else {
        await adminApi.jobs.cancel(action.job.id);
      }
      setAction(null);
      loadJobs();
    } catch {
      setError(`Failed to ${action.type} job`);
    }
  };

  return (
    <div>
      <h1 className="admin-page-title">Jobs</h1>
      <select
        className="admin-search"
        style={{ width: "auto" }}
        value={statusFilter}
        onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
      >
        <option value="">All statuses</option>
        <option value="pending">Pending</option>
        <option value="running">Running</option>
        <option value="completed">Completed</option>
        <option value="failed">Failed</option>
        <option value="dead">Dead</option>
      </select>
      {error && <p style={{ color: "var(--accent)" }}>{error}</p>}
      {data && (
        <>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Status</th>
                <th>Attempts</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.results.map((job) => (
                <tr key={job.id}>
                  <td>{job.type}</td>
                  <td><span className={`admin-badge ${job.status}`}>{job.status}</span></td>
                  <td>{job.attempts}/{job.max_attempts}</td>
                  <td>{new Date(job.created_at).toLocaleString()}</td>
                  <td className="admin-actions">
                    {(job.status === "failed" || job.status === "dead") && (
                      <button className="admin-btn" onClick={() => setAction({ type: "retry", job })}>
                        Retry
                      </button>
                    )}
                    {job.status === "pending" && (
                      <button className="admin-btn danger" onClick={() => setAction({ type: "cancel", job })}>
                        Cancel
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="admin-pagination">
            <button className="admin-btn" disabled={!data.previous} onClick={() => setPage((p) => p - 1)}>Previous</button>
            <span>Page {page}</span>
            <button className="admin-btn" disabled={!data.next} onClick={() => setPage((p) => p + 1)}>Next</button>
          </div>
        </>
      )}

      {action && (
        <ActionConfirm
          title={`${action.type === "retry" ? "Retry" : "Cancel"} job`}
          message={`Are you sure you want to ${action.type} job "${action.job.type}" (${action.job.id.slice(0, 8)}...)?`}
          confirmLabel={action.type === "retry" ? "Retry" : "Cancel Job"}
          onConfirm={handleAction}
          onCancel={() => setAction(null)}
        />
      )}
    </div>
  );
}
