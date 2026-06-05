import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { LeaderboardEntry } from "../types";

export function LeaderboardPage() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.leaderboard
      .get()
      .then(setEntries)
      .catch(() => setError("Failed to load leaderboard"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="main">
      <div className="eyebrow">Global</div>
      <div className="section-title" style={{ marginBottom: 24 }}>
        Leaderboard
      </div>

      {loading && <p style={{ textAlign: "center", color: "var(--muted)", fontSize: 12 }}>Loading...</p>}
      {error && <p style={{ textAlign: "center", color: "var(--accent)", fontSize: 12 }}>{error}</p>}

      {!loading && !error && entries.length === 0 && (
        <p style={{ textAlign: "center", color: "var(--muted)", fontSize: 12 }}>
          No scores yet. Be the first!
        </p>
      )}

      {entries.length > 0 && (
        <div className="leaderboard-table">
          <div className="leaderboard-header">
            <span className="lb-rank">#</span>
            <span className="lb-name">Name</span>
            <span className="lb-score">Score</span>
            <span className="lb-streak">Streak</span>
          </div>
          {entries.map((entry) => (
            <div
              key={entry.rank}
              className={`leaderboard-row${entry.is_current_user ? " is-you" : ""}`}
            >
              <span className="lb-rank">{entry.rank}</span>
              <span className="lb-name">
                {entry.display_name}
                {entry.is_current_user && <span className="you-badge">you</span>}
              </span>
              <span className="lb-score">{entry.total_score}</span>
              <span className="lb-streak">{entry.best_streak}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
