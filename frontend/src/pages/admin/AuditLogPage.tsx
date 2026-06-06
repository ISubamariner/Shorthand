import { useEffect, useState } from "react";
import { adminApi } from "../../api/admin";
import type { AuditLogEntry, PaginatedResponse } from "../../types/admin";

export function AuditLogPage() {
  const [data, setData] = useState<PaginatedResponse<AuditLogEntry> | null>(null);
  const [actionFilter, setActionFilter] = useState("");
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    adminApi.auditLog
      .list({ action: actionFilter || undefined, page })
      .then(setData)
      .catch(() => setError("Failed to load audit log"));
  }, [actionFilter, page]);

  return (
    <div>
      <h1 className="admin-page-title">Audit Log</h1>
      <input
        className="admin-search"
        placeholder="Filter by action (e.g. user.update)..."
        value={actionFilter}
        onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}
      />
      {error && <p style={{ color: "var(--accent)" }}>{error}</p>}
      {data && (
        <>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Target</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {data.results.map((entry) => (
                <tr key={entry.id}>
                  <td>{new Date(entry.created_at).toLocaleString()}</td>
                  <td>{entry.actor_username || "System"}</td>
                  <td><code style={{ fontSize: 11 }}>{entry.action}</code></td>
                  <td>{entry.target_type}:{entry.target_id.slice(0, 8)}</td>
                  <td>
                    <details>
                      <summary style={{ cursor: "pointer", fontSize: 11, color: "var(--muted)" }}>View</summary>
                      <pre style={{ fontSize: 10, maxWidth: 400, overflow: "auto", marginTop: 4 }}>
                        {JSON.stringify(entry.details, null, 2)}
                      </pre>
                    </details>
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
    </div>
  );
}
