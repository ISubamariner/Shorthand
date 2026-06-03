import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import { DrawingCanvas } from "../components/DrawingCanvas";
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

  const currentAttempt = poller.data;
  const isProcessing = submitting || (!poller.isComplete && poller.status !== "");

  return (
    <div>
      <h2>Practice</h2>

      <div style={{ marginBottom: 16 }}>
        <label>Select a symbol to practice: </label>
        <select
          value={selectedSymbol?.letter ?? ""}
          onChange={(e) => {
            const s = symbols.find((sym) => sym.letter === e.target.value);
            setSelectedSymbol(s ?? null);
            poller.stopPolling();
          }}
        >
          <option value="">-- Choose --</option>
          {symbols.map((s) => (
            <option key={s.letter} value={s.letter}>
              {s.letter} — {s.name}
            </option>
          ))}
        </select>
      </div>

      {selectedSymbol && (
        <>
          <p>
            Draw the Teeline symbol for: <strong>{selectedSymbol.letter}</strong>
          </p>
          <DrawingCanvas onExport={handleExport} />
        </>
      )}

      {isProcessing && <p>Analyzing your drawing...</p>}

      {submitError && <p style={{ color: "red" }}>{submitError}</p>}
      {poller.error && <p style={{ color: "red" }}>{poller.error}</p>}

      {currentAttempt && currentAttempt.status === "completed" && (
        <div
          style={{
            marginTop: 16,
            padding: 16,
            border: "1px solid #ccc",
            borderRadius: 4,
          }}
        >
          <h3>Result</h3>
          <p>
            Predicted: <strong>{currentAttempt.predicted_label}</strong>{" "}
            ({((currentAttempt.confidence ?? 0) * 100).toFixed(1)}% confidence)
          </p>
          <p>
            {currentAttempt.is_correct
              ? "✓ Correct!"
              : `✗ Expected ${selectedSymbol?.letter}`}
          </p>
        </div>
      )}
    </div>
  );
}
