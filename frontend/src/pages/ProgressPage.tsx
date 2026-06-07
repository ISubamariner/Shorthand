import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { Progress, Symbol, WordProgress } from "../types";

export function ProgressPage() {
  const navigate = useNavigate();
  const [symbols, setSymbols] = useState<Symbol[]>([]);
  const [progress, setProgress] = useState<Progress[]>([]);
  const [wordProgress, setWordProgress] = useState<WordProgress[]>([]);
  const [streak, setStreak] = useState(0);
  const [bestStreak, setBestStreak] = useState(0);
  const [totalScore, setTotalScore] = useState(0);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"symbols" | "words">("symbols");
  const [symbolTypeFilter, setSymbolTypeFilter] = useState<"all" | "letter" | "grouping">("all");

  useEffect(() => {
    Promise.all([
      api.symbols.list(),
      api.progress.get(),
      api.wordProgress.get(),
    ])
      .then(([syms, prog, wp]) => {
        setSymbols(syms);
        setProgress(prog.symbols);
        setStreak(prog.current_streak);
        setBestStreak(prog.best_streak);
        setTotalScore(prog.total_score);
        setWordProgress(wp);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const totalAttempts = progress.reduce((sum, p) => sum + p.total, 0);
  const totalCorrect = progress.reduce((sum, p) => sum + p.correct, 0);
  const overallAccuracy = totalAttempts > 0 ? (totalCorrect / totalAttempts) * 100 : 0;

  const filteredSymbols = symbolTypeFilter === "all"
    ? symbols
    : symbols.filter((s) => s.symbol_type === symbolTypeFilter);

  function getSymbolProgress(letter: string) {
    return progress.find((p) => p.symbol_letter === letter);
  }

  const sorted = filteredSymbols.map((sym) => ({
    letter: sym.letter,
    progress: getSymbolProgress(sym.letter),
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

  const weakestSymbols = new Set(
    sorted
      .filter((s) => s.progress && s.progress.total > 0)
      .slice(0, 5)
      .map((s) => s.letter)
  );

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

  return (
    <div className="main">
      <div className="eyebrow">Your Progress</div>
      <div className="section-title" style={{ marginBottom: 24 }}>
        Symbol <span className="accent">Accuracy</span>
      </div>

      <div className="progress-tabs">
        <button
          className={`tab ${activeTab === "symbols" ? "active" : ""}`}
          onClick={() => setActiveTab("symbols")}
        >
          Symbols
        </button>
        <button
          className={`tab ${activeTab === "words" ? "active" : ""}`}
          onClick={() => setActiveTab("words")}
        >
          Words
        </button>
      </div>

      {activeTab === "symbols" && (
        <>
          {/* Stats row */}
          <div className="progress-stats">
        <div className="stat-card">
          <div className="stat-value">{totalScore}</div>
          <div className="stat-label">Score</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{streak}</div>
          <div className="stat-label">Streak</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{bestStreak}</div>
          <div className="stat-label">Best Streak</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{overallAccuracy.toFixed(0)}%</div>
          <div className="stat-label">Accuracy</div>
        </div>
      </div>

      {/* Symbol type filter */}
      <div className="progress-tabs" style={{ marginBottom: 12 }}>
        {(["all", "letter", "grouping"] as const).map((f) => (
          <button
            key={f}
            className={`tab ${symbolTypeFilter === f ? "active" : ""}`}
            onClick={() => setSymbolTypeFilter(f)}
          >
            {f === "all" ? `All (${symbols.length})` : f === "letter" ? `Letters (${symbols.filter(s => s.symbol_type === "letter").length})` : `Groupings (${symbols.filter(s => s.symbol_type === "grouping").length})`}
          </button>
        ))}
      </div>

      {/* Weakest symbols callout */}
      {weakestSymbols.size > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div className="eyebrow" style={{ marginBottom: 8 }}>Focus on these</div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {[...weakestSymbols].map((letter) => (
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
          const isWeak = weakestSymbols.has(letter);
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
        </>
      )}

      {activeTab === "words" && (
        <div className="word-progress-section">
          <div className="stat-cards">
            <div className="stat-card">
              <div className="stat-value">{wordProgress.length}</div>
              <div className="stat-label">Words Practiced</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">
                {wordProgress.filter(w => w.perfect_sessions > 0).length}
              </div>
              <div className="stat-label">Words Mastered</div>
            </div>
          </div>
          <div className="progress-list">
            {wordProgress.map((wp) => (
              <div key={wp.word_id} className="progress-bar-row">
                <span className="progress-label">{wp.word_text}</span>
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${wp.accuracy * 100}%` }}
                  />
                </div>
                <span className="progress-value">
                  {Math.round(wp.accuracy * 100)}%
                </span>
              </div>
            ))}
            {wordProgress.length === 0 && (
              <p className="empty-state">No word practice yet. Try the Words tab!</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
