import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Progress } from "../types";

const ALL_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

export function ProgressPage() {
  const [progress, setProgress] = useState<Progress[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.progress
      .get()
      .then(setProgress)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const totalAttempts = progress.reduce((sum, p) => sum + p.total, 0);
  const totalCorrect = progress.reduce((sum, p) => sum + p.correct, 0);
  const overallAccuracy = totalAttempts > 0 ? (totalCorrect / totalAttempts) * 100 : 0;

  function getSymbolProgress(letter: string) {
    return progress.find((p) => p.symbol_letter === letter);
  }

  if (loading) {
    return (
      <div className="main">
        <p style={{ textAlign: "center", color: "var(--muted)", fontSize: 12 }}>
          Loading progress...
        </p>
      </div>
    );
  }

  return (
    <div className="main">
      <div className="eyebrow">Your Progress</div>
      <div className="section-title" style={{ marginBottom: 24 }}>
        Symbol <span className="accent">Accuracy</span>
      </div>

      {/* Stats row */}
      <div className="progress-stats">
        <div className="stat-card">
          <div className="stat-value">{totalAttempts}</div>
          <div className="stat-label">Attempts</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{overallAccuracy.toFixed(0)}%</div>
          <div className="stat-label">Accuracy</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{progress.length}</div>
          <div className="stat-label">Practiced</div>
        </div>
      </div>

      {/* Per-symbol bars */}
      <div className="symbol-bars">
        {ALL_LETTERS.map((letter) => {
          const p = getSymbolProgress(letter);
          const pct = p ? (p.correct / p.total) * 100 : 0;
          const hasData = p && p.total > 0;
          const barClass = !hasData ? "none" : pct >= 70 ? "good" : "weak";

          return (
            <div className="symbol-bar-row" key={letter}>
              <div className="symbol-bar-letter">{letter}</div>
              <div className="symbol-bar-track">
                <div
                  className={`symbol-bar-fill ${barClass}`}
                  style={{ width: hasData ? `${Math.max(pct, 3)}%` : "3%" }}
                />
              </div>
              <div className="symbol-bar-pct">
                {hasData ? `${pct.toFixed(0)}%` : "—"}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
