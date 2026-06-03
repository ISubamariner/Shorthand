import type { Attempt } from "../types";

interface FeedbackPanelProps {
  attempt: Attempt;
  expectedLetter: string;
  onNext: () => void;
  onRetry: () => void;
}

export function FeedbackPanel({
  attempt,
  expectedLetter,
  onNext,
  onRetry,
}: FeedbackPanelProps) {
  const isCorrect = attempt.is_correct;
  const confidence = attempt.confidence ?? 0;

  return (
    <div>
      <div className={`card result-card ${isCorrect ? "correct" : "incorrect"}`}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
          <span style={{ fontSize: 18 }}>{isCorrect ? "✓" : "✗"}</span>
          <span
            className="eyebrow"
            style={{ color: isCorrect ? "var(--success)" : "var(--accent)" }}
          >
            {isCorrect ? "Correct" : `Incorrect — Expected ${expectedLetter}`}
          </span>
        </div>

        <div style={{ display: "flex", gap: 16, alignItems: "center", marginTop: 10 }}>
          <div>
            <div className="label-row" style={{ justifyContent: "flex-start" }}>
              Predicted
            </div>
            <div
              style={{
                fontFamily: "var(--font-heading)",
                fontSize: 20,
                fontWeight: 700,
              }}
            >
              {attempt.predicted_label}
            </div>
          </div>
          <div style={{ flex: 1 }}>
            <div className="label-row">
              <span>Confidence</span>
              <span>{(confidence * 100).toFixed(1)}%</span>
            </div>
            <div className="confidence-bar-track">
              <div
                className={`confidence-bar-fill ${isCorrect ? "success" : "error"}`}
                style={{ width: `${confidence * 100}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      <div style={{ display: "flex", gap: 8, justifyContent: "center", marginTop: 16 }}>
        {isCorrect && (
          <button className="btn btn-success" onClick={onNext}>
            Next Symbol →
          </button>
        )}
        <button className="btn btn-retry" onClick={onRetry}>
          Try Again
        </button>
      </div>
    </div>
  );
}
