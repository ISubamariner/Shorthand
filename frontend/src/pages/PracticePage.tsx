import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { DrawingCanvas } from "../components/DrawingCanvas";
import { FeedbackPanel } from "../components/FeedbackPanel";
import { useJobPoller } from "../hooks/useJobPoller";
import type { Attempt, Symbol } from "../types";

function pickRandom(syms: Symbol[], exclude?: Symbol | null): Symbol {
  const pool = exclude ? syms.filter((s) => s.letter !== exclude.letter) : syms;
  const source = pool.length ? pool : syms;
  return source[Math.floor(Math.random() * source.length)]!;
}

export function PracticePage() {
  const [searchParams] = useSearchParams();
  const [symbols, setSymbols] = useState<Symbol[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState<Symbol | null>(null);
  const [randomMode, setRandomMode] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [canvasResetKey, setCanvasResetKey] = useState(0);
  const [streak, setStreak] = useState(0);
  const [score, setScore] = useState(0);
  const [streakMilestone, setStreakMilestone] = useState(0);
  const scoredAttempts = useRef(new Set<string>());

  const fetchAttempt = useCallback((id: string) => api.attempts.get(id), []);
  const poller = useJobPoller<Attempt>(fetchAttempt);

  useEffect(() => {
    api.symbols.list().then((syms) => {
      setSymbols(syms);
      const preselect = searchParams.get("symbol");
      if (preselect) {
        const match = syms.find((s) => s.letter === preselect.toUpperCase());
        if (match) {
          setSelectedSymbol(match);
          setRandomMode(false);
          return;
        }
      }
      if (syms.length) setSelectedSymbol(pickRandom(syms));
    }).catch(() => setSubmitError("Failed to load symbols"));

    api.progress.get().then((p) => {
      setStreak(p.current_streak);
      setScore(p.total_score);
    }).catch(() => {});
  }, [searchParams]);

  async function handleExport(imageData: string) {
    if (!selectedSymbol) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const attempt = await api.attempts.create({
        symbol_letter: selectedSymbol.letter,
        image_data: imageData,
      });
      poller.startPolling(attempt.id);
    } catch {
      setSubmitError("Failed to submit drawing");
    } finally {
      setSubmitting(false);
    }
  }

  function handleNext() {
    if (!symbols.length || !selectedSymbol) return;
    if (randomMode) {
      setSelectedSymbol(pickRandom(symbols, selectedSymbol));
    } else {
      const idx = symbols.findIndex((s) => s.letter === selectedSymbol.letter);
      setSelectedSymbol(symbols[(idx + 1) % symbols.length]!);
    }
    poller.stopPolling();
    setCanvasResetKey((k) => k + 1);
  }

  function handleRetry() {
    poller.stopPolling();
    setCanvasResetKey((k) => k + 1);
  }

  const currentAttempt = poller.data;
  const isProcessing = submitting || (!poller.isComplete && poller.status !== "");

  useEffect(() => {
    if (
      poller.data?.status === "completed" &&
      poller.data.is_correct !== null &&
      poller.data.id &&
      !scoredAttempts.current.has(poller.data.id)
    ) {
      scoredAttempts.current.add(poller.data.id);
      if (poller.data.is_correct) {
        setStreak((prev) => {
          const next = prev + 1;
          if (next % 5 === 0) {
            setStreakMilestone(next);
            setTimeout(() => setStreakMilestone(0), 2000);
          }
          return next;
        });
        setScore((s) => s + poller.data!.points);
      } else {
        setStreak(0);
      }
    }
  }, [poller.data?.id, poller.data?.status]);

  return (
    <div className="main">
      {/* Streak & Score bar */}
      <div style={{ display: "flex", justifyContent: "center", gap: 24, marginBottom: 16 }}>
        <div className="stat-badge">
          <span className="stat-icon">*</span> Streak: {streak}
        </div>
        <div className="stat-badge">
          Score: {score}
        </div>
      </div>
      {streakMilestone > 0 && (
        <div className="streak-milestone">
          {streakMilestone} streak!
        </div>
      )}
      {/* Symbol header */}
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 24 }}>
        {selectedSymbol && (
          <div className="sample-box">
            {[20, 40, 70, 90].map((pct) => (
              <div
                key={pct}
                className={`sample-guide${pct === 70 ? " sample-guide--baseline" : ""}`}
                style={{ top: `${pct}%` }}
              />
            ))}
            <img
              src={selectedSymbol.reference_image_url || `/symbols/${selectedSymbol.letter.toLowerCase()}.svg`}
              alt={`Teeline symbol for ${selectedSymbol.letter}`}
              className="sample-img"
            />
          </div>
        )}
        <div style={{ flex: 1 }}>
          <div className="eyebrow">
            {selectedSymbol ? "Draw this symbol" : "Select a symbol"}
          </div>
          <div className="section-title">
            {selectedSymbol ? (
              <>
                <span className="accent">{selectedSymbol.letter}</span> — {selectedSymbol.name}
              </>
            ) : (
              "Practice"
            )}
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <button
            className={`btn ${randomMode ? "btn-success" : "btn-retry"}`}
            style={{ fontSize: 12, padding: "6px 12px", whiteSpace: "nowrap" }}
            onClick={() => {
              setRandomMode((prev) => !prev);
              if (!randomMode && symbols.length) {
                setSelectedSymbol(pickRandom(symbols, selectedSymbol));
                poller.stopPolling();
                setCanvasResetKey((k) => k + 1);
              }
            }}
          >
            {randomMode ? "Random" : "Sequential"}
          </button>
          <select
            className="select"
            value={selectedSymbol?.letter ?? ""}
            onChange={(e) => {
              const s = symbols.find((sym) => sym.letter === e.target.value);
              setSelectedSymbol(s ?? null);
              setRandomMode(false);
              poller.stopPolling();
              setCanvasResetKey((k) => k + 1);
            }}
          >
            <option value="">Choose...</option>
            {symbols.map((s) => (
              <option key={s.letter} value={s.letter}>
                {s.letter} — {s.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Canvas */}
      {selectedSymbol && <DrawingCanvas onExport={handleExport} resetKey={canvasResetKey} />}

      {/* Processing state */}
      {isProcessing && (
        <div className="card processing-card">
          <div className="processing-pulse" />
          <span>Analyzing your drawing...</span>
        </div>
      )}

      {/* Errors */}
      {submitError && (
        <p style={{ textAlign: "center", color: "var(--accent)", fontSize: 12, marginTop: 16 }}>
          {submitError}
        </p>
      )}
      {poller.error && (
        <p style={{ textAlign: "center", color: "var(--accent)", fontSize: 12, marginTop: 16 }}>
          {poller.error}
        </p>
      )}

      {/* Failed prediction */}
      {currentAttempt && currentAttempt.status === "failed" && (
        <div className="card result-card incorrect" style={{ marginTop: 24 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
            <span style={{ fontSize: 18 }}>!</span>
            <span className="eyebrow" style={{ color: "var(--accent)" }}>
              Analysis failed — please try again
            </span>
          </div>
          <div style={{ display: "flex", justifyContent: "center", marginTop: 12 }}>
            <button className="btn btn-retry" onClick={handleRetry}>
              Try Again
            </button>
          </div>
        </div>
      )}

      {/* Results */}
      {currentAttempt && currentAttempt.status === "completed" && selectedSymbol && (
        <div style={{ marginTop: 24 }}>
          <FeedbackPanel
            attempt={currentAttempt}
            expectedLetter={selectedSymbol.letter}
            onNext={handleNext}
            onRetry={handleRetry}
          />
        </div>
      )}
    </div>
  );
}
