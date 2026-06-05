import type { TeelineComponent, Symbol } from "../types";

interface WordReferenceProps {
  components: TeelineComponent[];
  symbols: Symbol[];
}

export function WordReference({ components, symbols }: WordReferenceProps) {
  const symbolMap = new Map(symbols.map(s => [s.letter, s]));

  return (
    <div className="word-reference">
      {components.map((comp) => {
        const sym = symbolMap.get(comp.letter);
        return (
          <div key={comp.position} className="word-reference-letter">
            {sym?.reference_image_url ? (
              <img
                src={sym.reference_image_url}
                alt={comp.letter}
                className="word-reference-img"
              />
            ) : (
              <div className="word-reference-placeholder">{comp.letter}</div>
            )}
            {comp.blend_with && <div className="word-reference-blend" />}
          </div>
        );
      })}
    </div>
  );
}
