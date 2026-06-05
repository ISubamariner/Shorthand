import type { TeelineComponent, Symbol } from "../types";

interface LetterCardProps {
  component: TeelineComponent;
  symbol: Symbol | undefined;
  status: "pending" | "correct" | "incorrect";
  isActive: boolean;
  onClick: () => void;
}

export function LetterCard({ component, symbol, status, isActive, onClick }: LetterCardProps) {
  const statusClass =
    status === "correct" ? "card-correct" :
    status === "incorrect" ? "card-incorrect" :
    "";

  return (
    <button
      className={`letter-card ${statusClass} ${isActive ? "card-active" : ""}`}
      onClick={onClick}
      type="button"
    >
      <div className="letter-card-letter">{component.letter}</div>
      {symbol?.reference_image_url && (
        <img
          className="letter-card-img"
          src={symbol.reference_image_url}
          alt={`Teeline ${component.letter}`}
        />
      )}
      {component.blend_with && (
        <div className="letter-card-badge">blend: {component.blend_with}</div>
      )}
      {component.is_doubled_for_r && (
        <div className="letter-card-badge">+ R (lengthen)</div>
      )}
      <div className="letter-card-status">
        {status === "correct" ? "✓" : status === "incorrect" ? "✗" : "—"}
      </div>
    </button>
  );
}
