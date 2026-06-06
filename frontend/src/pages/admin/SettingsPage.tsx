import { useEffect, useState } from "react";
import { adminApi } from "../../api/admin";
import type { SystemSetting } from "../../types/admin";

export function SettingsPage() {
  const [settings, setSettings] = useState<SystemSetting[]>([]);
  const [edited, setEdited] = useState<Record<string, unknown>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    adminApi.settings
      .list()
      .then(setSettings)
      .catch(() => setError("Failed to load settings"));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccess(false);
    try {
      const updates = Object.entries(edited).map(([key, value]) => ({ key, value }));
      const updated = await adminApi.settings.update(updates);
      setSettings(updated);
      setEdited({});
      setSuccess(true);
    } catch {
      setError("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const hasChanges = Object.keys(edited).length > 0;

  return (
    <div>
      <h1 className="admin-page-title">Settings</h1>
      {error && <p style={{ color: "var(--accent)", marginBottom: 12 }}>{error}</p>}
      {success && <p style={{ color: "#065f46", marginBottom: 12 }}>Settings saved.</p>}

      {settings.length === 0 && !error && (
        <p style={{ color: "var(--muted)", fontSize: 12 }}>
          No settings configured. Use Django shell to create SystemSetting entries.
        </p>
      )}

      {settings.length > 0 && (
        <>
          <table className="admin-table" style={{ maxWidth: 600 }}>
            <thead>
              <tr>
                <th>Key</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {settings.map((s) => (
                <tr key={s.key}>
                  <td><code style={{ fontSize: 12 }}>{s.key}</code></td>
                  <td>
                    {typeof s.value === "boolean" ? (
                      <button
                        className="admin-btn"
                        onClick={() => {
                          const current = edited[s.key] ?? s.value;
                          setEdited({ ...edited, [s.key]: !current });
                        }}
                      >
                        {String(edited[s.key] ?? s.value)}
                      </button>
                    ) : (
                      <input
                        className="admin-search"
                        style={{ width: "auto", marginBottom: 0 }}
                        value={String(edited[s.key] ?? s.value)}
                        onChange={(e) => setEdited({ ...edited, [s.key]: e.target.value })}
                      />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {hasChanges && (
            <button
              className="admin-btn"
              style={{ marginTop: 12 }}
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? "Saving..." : "Save Changes"}
            </button>
          )}
        </>
      )}
    </div>
  );
}
