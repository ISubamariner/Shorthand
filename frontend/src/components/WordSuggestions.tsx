import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { WordSuggestion } from "../types";

interface WordSuggestionsProps {
  groupings: string[];
  onSelectWord?: (wordId: string) => void;
}

export function WordSuggestions({ groupings, onSelectWord }: WordSuggestionsProps) {
  const [suggestions, setSuggestions] = useState<WordSuggestion[]>([]);
  const [error, setError] = useState(false);

  const prefixKey = groupings.join("-");

  useEffect(() => {
    if (groupings.length === 0) {
      setSuggestions([]);
      setError(false);
      return;
    }
    setError(false);
    api.wordSuggest.byPrefix(prefixKey).then(setSuggestions).catch(() => {
      console.error("Failed to fetch word suggestions");
      setSuggestions([]);
      setError(true);
    });
  }, [prefixKey]);

  if (groupings.length === 0) return null;

  return (
    <div className="word-suggestions">
      <h4>Matching Words</h4>
      {error ? (
        <p className="error">Failed to load suggestions</p>
      ) : suggestions.length === 0 ? (
        <p className="empty-state">No matching words found</p>
      ) : (
        <div className="suggestion-list">
          {suggestions.map((s) => (
            <button
              key={s.word_id}
              className="suggestion-item"
              onClick={() => onSelectWord?.(s.word_id)}
              type="button"
            >
              <span className="suggestion-text">{s.text}</span>
              <span className="suggestion-skeleton">{s.teeline_skeleton}</span>
              <span className="suggestion-difficulty">{s.difficulty}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
