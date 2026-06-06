import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError, getAccessToken } from "../api/client";

export function SettingsPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [username, setUsername] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!getAccessToken()) {
      navigate("/login");
      return;
    }
    api.auth.me().then((u) => {
      setUsername(u.username);
      setEmail(u.email);
    }).catch(() => navigate("/login"));
  }, [navigate]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setFieldErrors({});
    setSuccess(null);
    setLoading(true);

    try {
      const payload: Record<string, string> = { email };
      if (newPassword) {
        payload.current_password = currentPassword;
        payload.new_password = newPassword;
      }
      await api.auth.updateMe(payload);
      setSuccess("Settings saved.");
      setCurrentPassword("");
      setNewPassword("");
    } catch (err) {
      if (err instanceof ApiError) {
        const body = err.body as Record<string, unknown>;
        if (typeof body.fields === "object" && body.fields !== null) {
          const fields = body.fields as Record<string, string | string[]>;
          const parsed: Record<string, string> = {};
          for (const [key, val] of Object.entries(fields)) {
            parsed[key] = Array.isArray(val) ? val[0] ?? val.join(", ") : val;
          }
          setFieldErrors(parsed);
        }
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="main">
      <div className="section-title" style={{ marginBottom: 24 }}>
        <span className="accent">{username}</span> — Settings
      </div>

      <form onSubmit={handleSave}>
        <div className="settings-section">
          <div className="eyebrow" style={{ marginBottom: 12 }}>Email</div>
          <input
            className={`input ${fieldErrors.email ? "input-error" : ""}`}
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
          {fieldErrors.email && <div className="field-error">{fieldErrors.email}</div>}
        </div>

        <div className="settings-section" style={{ marginTop: 24 }}>
          <div className="eyebrow" style={{ marginBottom: 12 }}>Change Password</div>
          <input
            className={`input ${fieldErrors.current_password ? "input-error" : ""}`}
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            placeholder="Current password"
            style={{ marginBottom: 8 }}
          />
          {fieldErrors.current_password && (
            <div className="field-error">{fieldErrors.current_password}</div>
          )}
          <input
            className={`input ${fieldErrors.new_password ? "input-error" : ""}`}
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="New password"
            minLength={8}
          />
          {fieldErrors.new_password && (
            <div className="field-error">{fieldErrors.new_password}</div>
          )}
        </div>

        {success && (
          <div style={{ color: "var(--success)", fontSize: 12, marginTop: 12 }}>{success}</div>
        )}

        <div style={{ marginTop: 24 }}>
          <button className="btn btn-primary" type="submit" disabled={loading}>
            {loading ? "Saving..." : "Save"}
          </button>
        </div>
      </form>
    </div>
  );
}
