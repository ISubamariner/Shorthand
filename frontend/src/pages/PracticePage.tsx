import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import { DrawingCanvas } from "../components/DrawingCanvas";
import { FeedbackPanel } from "../components/FeedbackPanel";
import { useJobPoller } from "../hooks/useJobPoller";
import type { Attempt, Symbol } from "../types";

export function PracticePage() {
  const [symbols, setSymbols] = useState<Symbol[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState<Symbol | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const fetchAttempt = useCallback((id: string) => api.attempts.get(id), []);
  const poller = useJobPoller<Attempt>(fetchAttempt);

  useEffect(() => {
    api.symbols.list().then(setSymbols).catch(() => setSubmitError("Failed to load symbols"));
  }, []);

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
    const idx = symbols.findIndex((s) => s.letter === selectedSymbol.letter);
    const next = symbols[(idx + 1) % symbols.length];
    setSelectedSymbol(next ?? null);
    poller.stopPolling();
  }

  function handleRetry() {
    poller.stopPolling();
  }

  const currentAttempt = poller.data;
  const isProcessing = submitting || (!poller.isComplete && poller.status !== "");

  return (
    <div className="main">
      {/* Symbol header */}
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 24 }}>
        {selectedSymbol && (
          <div
            style={{
              width: 56,
              height: 56,
              background: "var(--surface)",
              border: "1.5px solid var(--line)",
              borderRadius: 3,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <span
              style={{
                fontSize: 32,
                color: "var(--accent)",
                fontStyle: "italic",
                fontFamily: "var(--font-heading)",
              }}
            >
              {selectedSymbol.letter.toLowerCase()}
            </span>
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
        <select
          className="select"
          value={selectedSymbol?.letter ?? ""}
          onChange={(e) => {
            const s = symbols.find((sym) => sym.letter === e.target.value);
            setSelectedSymbol(s ?? null);
            poller.stopPolling();
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

      {/* Canvas */}
      {selectedSymbol && <DrawingCanvas onExport={handleExport} />}

      {/* Processing state */}
      {isProcessing && (
        <p style={{ textAlign: "center", color: "var(--muted)", fontSize: 12, marginTop: 16 }}>
          Analyzing your drawing...
        </p>
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
