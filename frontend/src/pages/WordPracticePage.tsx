import { useEffect, useState } from "react";
import { api } from "../api/client";
import { DrawingCanvas } from "../components/DrawingCanvas";
import { FeedbackPanel } from "../components/FeedbackPanel";
import { LetterCard } from "../components/LetterCard";
import { WordReference } from "../components/WordReference";
import { useJobPoller } from "../hooks/useJobPoller";
import type {
  Symbol,
  Word,
  WordListItem,
  WordSession,
  WordTopic,
} from "../types";

type LetterStatus = "pending" | "correct" | "incorrect";

export function WordPracticePage() {
  const [topics, setTopics] = useState<WordTopic[]>([]);
  const [words, setWords] = useState<WordListItem[]>([]);
  const [symbols, setSymbols] = useState<Symbol[]>([]);
  const [selectedTopic, setSelectedTopic] = useState("");
  const [selectedDifficulty, setSelectedDifficulty] = useState("");
  const [selectedWord, setSelectedWord] = useState<Word | null>(null);
  const [session, setSession] = useState<WordSession | null>(null);
  const [activePosition, setActivePosition] = useState<number | null>(null);
  const [letterStatuses, setLetterStatuses] = useState<Record<number, LetterStatus>>({});
  const [canvasResetKey, setCanvasResetKey] = useState(0);
  const [submitError, setSubmitError] = useState("");

  const { data: attempt, startPolling, stopPolling } = useJobPoller(api.attempts.get);

  useEffect(() => {
    api.symbols.list().then(setSymbols);
    api.words.topics().then(setTopics);
  }, []);

  useEffect(() => {
    api.words
      .list({
        difficulty: selectedDifficulty || undefined,
        topic: selectedTopic || undefined,
      })
      .then((res) => setWords(res.results));
  }, [selectedDifficulty, selectedTopic]);

  async function handleSelectWord(wordId: string) {
    const word = await api.words.get(wordId);
    setSelectedWord(word);
    const newSession = await api.wordSessions.create(wordId);
    setSession(newSession);
    setLetterStatuses({});
    setActivePosition(null);
    stopPolling();
    setCanvasResetKey((k) => k + 1);
  }

  async function handleExport(base64: string) {
    if (!selectedWord || !session || activePosition === null) return;
    const component = selectedWord.components[activePosition];
    if (!component) return;
    setSubmitError("");
    try {
      const created = await api.attempts.create({
        symbol_letter: component.letter,
        image_data: base64,
        word_session: session.id,
        word_position: activePosition,
      });
      startPolling(created.id);
    } catch {
      setSubmitError("Failed to submit. Try again.");
    }
  }

  useEffect(() => {
    if (attempt?.status === "completed" && activePosition !== null) {
      setLetterStatuses((prev) => ({
        ...prev,
        [activePosition]: attempt.is_correct ? "correct" : "incorrect",
      }));
    }
  }, [attempt?.status, attempt?.is_correct, activePosition]);

  const allDone =
    selectedWord &&
    selectedWord.components.length > 0 &&
    selectedWord.components.every((_, i) => letterStatuses[i] === "correct" || letterStatuses[i] === "incorrect");

  async function handleComplete() {
    if (!session) return;
    const updated = await api.wordSessions.complete(session.id);
    setSession(updated);
    setActivePosition(null);
    stopPolling();
  }

  function handleNextLetter() {
    stopPolling();
    setCanvasResetKey((k) => k + 1);
    if (!selectedWord) return;
    const next = selectedWord.components.find(
      (_, i) => !letterStatuses[i]
    );
    if (next) {
      setActivePosition(next.position);
    }
  }

  function handleRetry() {
    stopPolling();
    setCanvasResetKey((k) => k + 1);
  }

  return (
    <div className="page">
      <h1>Word Practice</h1>

      <div className="word-filters">
        <select
          value={selectedDifficulty}
          onChange={(e) => setSelectedDifficulty(e.target.value)}
        >
          <option value="">All Difficulties</option>
          <option value="beginner">Beginner</option>
          <option value="intermediate">Intermediate</option>
          <option value="advanced">Advanced</option>
        </select>

        <select
          value={selectedTopic}
          onChange={(e) => setSelectedTopic(e.target.value)}
        >
          <option value="">All Topics</option>
          {topics.map((t) => (
            <option key={t.slug} value={t.slug}>
              {t.name}
            </option>
          ))}
        </select>

        <select
          value={selectedWord?.id || ""}
          onChange={(e) => {
            if (e.target.value) handleSelectWord(e.target.value);
          }}
        >
          <option value="">Select a word...</option>
          {words.map((w) => (
            <option key={w.id} value={w.id}>
              {w.text} ({w.teeline_letters})
            </option>
          ))}
        </select>
      </div>

      {selectedWord && (
        <>
          <div className="word-practice-layout">
            <div className="word-practice-left">
              <h3>
                "{selectedWord.text}" → {selectedWord.teeline_letters}
              </h3>
              <WordReference
                components={selectedWord.components}
                symbols={symbols}
              />
            </div>

            <div className="word-practice-right">
              <div className="letter-cards">
                {selectedWord.components.map((comp) => (
                  <LetterCard
                    key={comp.position}
                    component={comp}
                    symbol={symbols.find((s) => s.letter === comp.letter)}
                    status={letterStatuses[comp.position] || "pending"}
                    isActive={activePosition === comp.position}
                    onClick={() => {
                      setActivePosition(comp.position);
                      stopPolling();
                      setCanvasResetKey((k) => k + 1);
                    }}
                  />
                ))}
              </div>
            </div>
          </div>

          {activePosition !== null && !attempt && selectedWord.components[activePosition] && (
            <div className="canvas-section">
              <p>
                Draw letter: <strong>{selectedWord.components[activePosition]!.letter}</strong>
              </p>
              <DrawingCanvas
                resetKey={canvasResetKey}
                onExport={handleExport}
              />
              {submitError && <p className="error">{submitError}</p>}
            </div>
          )}

          {attempt && activePosition !== null && selectedWord.components[activePosition] && (
            <FeedbackPanel
              attempt={attempt}
              expectedLetter={selectedWord.components[activePosition]!.letter}
              onRetry={handleRetry}
              onNext={handleNextLetter}
            />
          )}

          {allDone && session?.status !== "completed" && (
            <button className="btn btn-primary" onClick={handleComplete}>
              Complete Word
            </button>
          )}

          {session?.status === "completed" && (
            <div className="word-summary">
              <h3>Word Complete!</h3>
              <p>
                {session.letters_correct} / {session.letters_total} correct
              </p>
              <p>Points earned: {session.points_awarded}</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
