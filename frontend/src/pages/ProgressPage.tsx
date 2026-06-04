import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { Progress } from "../types";

const ALL_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

export function ProgressPage() {
  const navigate = useNavigate();
  const [progress, setProgress] = useState<Progress[]>([]);
  const [streak, setStreak] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.progress
      .get()
      .then((data) => {
        setProgress(data.symbols);
        setStreak(data.current_streak);
      })
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

  if (totalAttempts === 0) {
    return (
      <div className="main">
        <div className="eyebrow">Your Progress</div>
        <div className="section-title" style={{ marginBottom: 24 }}>
          Symbol <span className="accent">Accuracy</span>
        </div>
        <div className="card" style={{ textAlign: "center", padding: "40px 20px" }}>
          <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 16 }}>
            No attempts yet. Start practicing to see your progress here.
          </div>
          <button className="btn btn-primary" onClick={() => navigate("/")}>
            Start Practicing
          </button>
        </div>
      </div>
    );
  }

  const sorted = ALL_LETTERS.map((letter) => ({
    letter,
    progress: getSymbolProgress(letter),
  })).sort((a, b) => {
    const aHas = a.progress && a.progress.total > 0;
    const bHas = b.progress && b.progress.total > 0;
    if (!aHas && !bHas) return 0;
    if (!aHas) return 1;
    if (!bHas) return -1;
    const aPct = a.progress!.correct / a.progress!.total;
    const bPct = b.progress!.correct / b.progress!.total;
    return aPct - bPct;
  });

  const weakestLetters = new Set(
    sorted
      .filter((s) => s.progress && s.progress.total > 0)
      .slice(0, 5)
      .map((s) => s.letter)
  );

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
          <div className="stat-value">{streak}</div>
          <div className="stat-label">Streak</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{progress.length}</div>
          <div className="stat-label">Practiced</div>
        </div>
      </div>

      {/* Weakest symbols callout */}
      {weakestLetters.size > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div className="eyebrow" style={{ marginBottom: 8 }}>Focus on these</div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {[...weakestLetters].map((letter) => (
              <button
                key={letter}
                className="btn btn-retry"
                style={{ padding: "4px 10px", fontSize: 11 }}
                onClick={() => navigate(`/?symbol=${letter}`)}
              >
                {letter}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Per-symbol bars */}
      <div className="symbol-bars">
        {sorted.map(({ letter, progress: p }) => {
          const pct = p && p.total > 0 ? (p.correct / p.total) * 100 : 0;
          const hasData = p && p.total > 0;
          const isWeak = weakestLetters.has(letter);
          const barClass = !hasData ? "none" : pct >= 70 ? "good" : "weak";

          return (
            <div
              className={`symbol-bar-row ${hasData ? "clickable" : ""} ${isWeak ? "highlight" : ""}`}
              key={letter}
              onClick={() => hasData && navigate(`/?symbol=${letter}`)}
              role={hasData ? "button" : undefined}
              tabIndex={hasData ? 0 : undefined}
            >
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
