import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { adminApi } from "../../api/admin";
import { ActionConfirm } from "../../components/admin/ActionConfirm";
import type { AdminUser } from "../../types/admin";

export function UserDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [user, setUser] = useState<AdminUser | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confirm, setConfirm] = useState<{ action: string; field: string; value: boolean } | null>(null);

  useEffect(() => {
    if (!id) return;
    adminApi.users
      .get(Number(id))
      .then(setUser)
      .catch(() => setError("Failed to load user"));
  }, [id]);

  const handleToggle = async (field: "is_active" | "is_staff", value: boolean) => {
    if (!id) return;
    try {
      const updated = await adminApi.users.update(Number(id), { [field]: value });
      setUser(updated);
      setConfirm(null);
    } catch {
      setError("Failed to update user");
    }
  };

  if (error) return <p style={{ color: "var(--accent)" }}>{error}</p>;
  if (!user) return <p style={{ color: "var(--muted)", fontSize: 12 }}>Loading...</p>;

  return (
    <div>
      <button className="admin-btn" onClick={() => navigate("/admin/users")} style={{ marginBottom: 16 }}>
        Back to Users
      </button>
      <h1 className="admin-page-title">{user.username}</h1>
      <table className="admin-table" style={{ maxWidth: 500 }}>
        <tbody>
          <tr><td>Email</td><td>{user.email}</td></tr>
          <tr><td>Joined</td><td>{new Date(user.date_joined).toLocaleDateString()}</td></tr>
          <tr><td>Last Login</td><td>{user.last_login ? new Date(user.last_login).toLocaleString() : "Never"}</td></tr>
          <tr>
            <td>Active</td>
            <td>
              <button
                className={`admin-btn ${user.is_active ? "danger" : ""}`}
                onClick={() =>
                  setConfirm({
                    action: user.is_active ? "Deactivate" : "Activate",
                    field: "is_active",
                    value: !user.is_active,
                  })
                }
              >
                {user.is_active ? "Deactivate" : "Activate"}
              </button>
            </td>
          </tr>
          <tr>
            <td>Admin</td>
            <td>
              <button
                className={`admin-btn ${user.is_staff ? "danger" : ""}`}
                onClick={() =>
                  setConfirm({
                    action: user.is_staff ? "Remove admin" : "Make admin",
                    field: "is_staff",
                    value: !user.is_staff,
                  })
                }
              >
                {user.is_staff ? "Remove admin" : "Make admin"}
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      {confirm && (
        <ActionConfirm
          title={`${confirm.action} user`}
          message={`Are you sure you want to ${confirm.action.toLowerCase()} ${user.username}?`}
          confirmLabel={confirm.action}
          onConfirm={() => handleToggle(confirm.field as "is_active" | "is_staff", confirm.value)}
          onCancel={() => setConfirm(null)}
        />
      )}
    </div>
  );
}
