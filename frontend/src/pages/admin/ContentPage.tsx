import { useEffect, useState } from "react";
import { adminApi } from "../../api/admin";
import { ActionConfirm } from "../../components/admin/ActionConfirm";
import type { AdminSymbol, AdminWord } from "../../types/admin";

export function ContentPage() {
  const [symbols, setSymbols] = useState<AdminSymbol[]>([]);
  const [words, setWords] = useState<AdminWord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<{ type: "symbol" | "word"; id: number | string; name: string } | null>(null);

  const loadData = () => {
    Promise.all([adminApi.content.symbols.list(), adminApi.content.words.list()])
      .then(([s, w]) => { setSymbols(s); setWords(w); })
      .catch(() => setError("Failed to load content"));
  };

  useEffect(loadData, []);

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      if (deleteTarget.type === "symbol") {
        await adminApi.content.symbols.delete(deleteTarget.id as number);
      } else {
        await adminApi.content.words.delete(deleteTarget.id as string);
      }
      setDeleteTarget(null);
      loadData();
    } catch {
      setError("Failed to delete");
    }
  };

  return (
    <div>
      <h1 className="admin-page-title">Content</h1>
      {error && <p style={{ color: "var(--accent)" }}>{error}</p>}

      <h2 style={{ fontFamily: "'Syne', sans-serif", fontSize: 16, marginBottom: 12 }}>
        Symbols ({symbols.length})
      </h2>
      <table className="admin-table" style={{ marginBottom: 32 }}>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Name</th>
            <th>Type</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {symbols.map((s) => (
            <tr key={s.id}>
              <td>{s.letter}</td>
              <td>{s.name}</td>
              <td>{s.symbol_type}</td>
              <td>
                <button
                  className="admin-btn danger"
                  onClick={() => setDeleteTarget({ type: "symbol", id: s.id, name: s.letter })}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2 style={{ fontFamily: "'Syne', sans-serif", fontSize: 16, marginBottom: 12 }}>
        Words ({words.length})
      </h2>
      <table className="admin-table">
        <thead>
          <tr>
            <th>Text</th>
            <th>Teeline</th>
            <th>Difficulty</th>
            <th>Topic</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {words.map((w) => (
            <tr key={w.id}>
              <td>{w.text}</td>
              <td>{w.teeline_letters}</td>
              <td>{w.difficulty}</td>
              <td>{w.topic_name}</td>
              <td>
                <button
                  className="admin-btn danger"
                  onClick={() => setDeleteTarget({ type: "word", id: w.id, name: w.text })}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {deleteTarget && (
        <ActionConfirm
          title={`Delete ${deleteTarget.type}`}
          message={`Are you sure you want to delete "${deleteTarget.name}"? This cannot be undone.`}
          confirmLabel="Delete"
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  );
}
