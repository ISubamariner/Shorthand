import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { adminApi } from "../../api/admin";
import type { AdminUser, PaginatedResponse } from "../../types/admin";

export function UsersPage() {
  const [data, setData] = useState<PaginatedResponse<AdminUser> | null>(null);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    adminApi.users
      .list({ search: search || undefined, page })
      .then(setData)
      .catch(() => setError("Failed to load users"));
  }, [search, page]);

  return (
    <div>
      <h1 className="admin-page-title">Users</h1>
      <input
        className="admin-search"
        placeholder="Search by username or email..."
        value={search}
        onChange={(e) => {
          setSearch(e.target.value);
          setPage(1);
        }}
      />
      {error && <p style={{ color: "var(--accent)" }}>{error}</p>}
      {data && (
        <>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Email</th>
                <th>Staff</th>
                <th>Active</th>
                <th>Joined</th>
              </tr>
            </thead>
            <tbody>
              {data.results.map((user) => (
                <tr key={user.id}>
                  <td>
                    <Link to={`/admin/users/${user.id}`} style={{ color: "var(--ink)" }}>
                      {user.username}
                    </Link>
                  </td>
                  <td>{user.email}</td>
                  <td>{user.is_staff ? "Yes" : "No"}</td>
                  <td>{user.is_active ? "Yes" : "No"}</td>
                  <td>{new Date(user.date_joined).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="admin-pagination">
            <button
              className="admin-btn"
              disabled={!data.previous}
              onClick={() => setPage((p) => p - 1)}
            >
              Previous
            </button>
            <span>Page {page}</span>
            <button
              className="admin-btn"
              disabled={!data.next}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}
