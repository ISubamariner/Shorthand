import { useEffect, useState } from "react";
import { api } from "../api/client";
import { DrawingCanvas } from "./DrawingCanvas";
import { WordSuggestions } from "./WordSuggestions";
import { useJobPoller } from "../hooks/useJobPoller";

interface WordDrawingModeProps {
  onSelectWord?: (wordId: string) => void;
}

export function WordDrawingMode({ onSelectWord }: WordDrawingModeProps) {
  const [recognizedGroupings, setRecognizedGroupings] = useState<string[]>([]);
  const [canvasResetKey, setCanvasResetKey] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const { data: attempt, startPolling, stopPolling } = useJobPoller(api.attempts.get);

  async function handleExport(base64: string) {
    setSubmitting(true);
    setError("");
    try {
      // Submit with a placeholder letter — the ML model determines the actual grouping
      const created = await api.attempts.create({
        symbol_letter: "A",
        image_data: base64,
      });
      startPolling(created.id);
    } catch (err) {
      console.error("Failed to submit drawing", err);
      setSubmitting(false);
      setError("Failed to submit drawing. Please try again.");
    }
  }

  useEffect(() => {
    if (attempt?.status === "completed" && attempt.predicted_label) {
      setRecognizedGroupings((prev) => [...prev, attempt.predicted_label!]);
      setSubmitting(false);
      stopPolling();
      setCanvasResetKey((k) => k + 1);
    } else if (attempt?.status === "failed") {
      setSubmitting(false);
      stopPolling();
    }
  }, [attempt?.status, attempt?.predicted_label, stopPolling]);

  function handleUndo() {
    setRecognizedGroupings((prev) => prev.slice(0, -1));
  }

  function handleClear() {
    setRecognizedGroupings([]);
    stopPolling();
    setCanvasResetKey((k) => k + 1);
  }

  return (
    <div className="word-drawing-mode">
      <div className="recognized-groupings">
        <h4>Recognized Groupings</h4>
        <div className="grouping-badges">
          {recognizedGroupings.length === 0 ? (
            <span className="empty-state">Draw a grouping to start...</span>
          ) : (
            recognizedGroupings.map((g, i) => (
              <span key={i} className="grouping-badge">{g}</span>
            ))
          )}
        </div>
        <div className="grouping-actions">
          <button
            className="btn btn-secondary btn-sm"
            onClick={handleUndo}
            disabled={recognizedGroupings.length === 0}
            type="button"
          >
            Undo
          </button>
          <button
            className="btn btn-secondary btn-sm"
            onClick={handleClear}
            disabled={recognizedGroupings.length === 0}
            type="button"
          >
            Clear
          </button>
        </div>
      </div>

      <div className="canvas-section">
        <p>Draw the next grouping:</p>
        <DrawingCanvas
          resetKey={canvasResetKey}
          onExport={handleExport}
        />
        {submitting && <p className="status-text">Recognizing...</p>}
        {error && <p className="error">{error}</p>}
      </div>

      <WordSuggestions
        groupings={recognizedGroupings}
        onSelectWord={onSelectWord}
      />
    </div>
  );
}
