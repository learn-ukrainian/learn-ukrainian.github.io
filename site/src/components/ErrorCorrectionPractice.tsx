import { useCallback, useEffect, useMemo, useState } from 'react';
import { cardKey, loadState, rateCard, type PracticeRating } from '../lib/lexicon/srs';
import { ErrorCorrectionItem } from './ErrorCorrection';

export interface ErrorCorrectionDrill {
  id: string;
  sentence: string;
  errorWord: string;
  correctForm: string;
  options: string[];
  explanation: string;
  isUkrainian: boolean;
  source: string;
}

export interface ErrorCorrectionPracticeProps {
  items: readonly ErrorCorrectionDrill[];
  onBackToDecks: () => void;
  chromeLocale?: 'uk' | 'en';
}

function dayKey(now = new Date()): string {
  return now.toISOString().slice(0, 10);
}

function hashSeed(input: string): number {
  let hash = 2166136261;
  for (let i = 0; i < input.length; i += 1) {
    hash ^= input.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

export function nextDueErrorCorrectionItem(
  items: readonly ErrorCorrectionDrill[],
  currentId: string | null,
): ErrorCorrectionDrill | null {
  if (!items.length) return null;
  const now = Date.now();
  const cards = loadState().cards;
  const seedDay = dayKey();
  return (
    [...items]
      .filter((item) => item.id !== currentId || items.length === 1)
      .sort((left, right) => {
        const leftDue = cards.get(cardKey(left.id, 'choice'))?.due ?? 0;
        const rightDue = cards.get(cardKey(right.id, 'choice'))?.due ?? 0;
        const leftPriority = leftDue <= now ? 0 : 1;
        const rightPriority = rightDue <= now ? 0 : 1;
        if (leftPriority !== rightPriority) return leftPriority - rightPriority;
        if (leftDue !== rightDue) return leftDue - rightDue;
        return hashSeed(`${seedDay}:${left.id}`) - hashSeed(`${seedDay}:${right.id}`);
      })[0] ?? null
  );
}

export default function ErrorCorrectionPractice({
  items = [],
  onBackToDecks,
  chromeLocale = 'uk',
}: ErrorCorrectionPracticeProps) {
  const [currentId, setCurrentId] = useState<string | null>(() => items[0]?.id ?? null);
  const [rated, setRated] = useState(false);
  const [sessionStats, setSessionStats] = useState({ answered: 0, correct: 0 });

  const currentItem = useMemo(
    () => items.find((it) => it.id === currentId) ?? nextDueErrorCorrectionItem(items, null),
    [items, currentId],
  );

  const handleComplete = useCallback(
    (correct: boolean) => {
      if (!currentItem || rated) return;
      const rating: PracticeRating = correct ? 'good' : 'again';
      rateCard(currentItem.id, 'choice', rating);
      setRated(true);
      setSessionStats((prev) => ({
        answered: prev.answered + 1,
        correct: prev.correct + (correct ? 1 : 0),
      }));
    },
    [currentItem, rated],
  );

  const handleNext = useCallback(() => {
    if (!currentItem) return;
    const next = nextDueErrorCorrectionItem(items, currentItem.id);
    setCurrentId(next?.id ?? null);
    setRated(false);
  }, [items, currentItem]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (rated && (e.key === 'Enter' || e.key === ' ')) {
        e.preventDefault();
        handleNext();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [rated, handleNext]);

  if (!currentItem) {
    return (
      <div className="error-correction-empty" data-testid="error-correction-empty">
        <p>
          {chromeLocale === 'uk'
            ? 'Усі завдання на сьогодні виконано!'
            : 'All exercises for today completed!'}
        </p>
        <button type="button" className="btn btn-accent" onClick={onBackToDecks}>
          {chromeLocale === 'uk' ? 'Повернутися до вибору' : 'Back to Decks'}
        </button>
      </div>
    );
  }

  return (
    <div className="error-correction-practice-view" data-testid="error-correction-practice-view">
      <div className="error-correction-header-meta">
        <div className="error-correction-badges">
          <span className="error-correction-source-badge" data-testid="drill-source-badge">
            📚 {currentItem.source}
          </span>
          <span className="error-correction-counter-badge" data-testid="drill-counter-badge">
            {chromeLocale === 'uk'
              ? `Виконано: ${sessionStats.answered} (правильно: ${sessionStats.correct})`
              : `Done: ${sessionStats.answered} (correct: ${sessionStats.correct})`}
          </span>
        </div>
        <p className="error-correction-instruction">
          {chromeLocale === 'uk'
            ? 'Знайдіть помилку в реченні (натисніть на неї) та виправте її:'
            : 'Find the error in the sentence (tap it) and correct it:'}
        </p>
      </div>

      <div className="error-correction-card-body" key={currentItem.id}>
        <ErrorCorrectionItem
          sentence={currentItem.sentence}
          errorWord={currentItem.errorWord}
          correctForm={currentItem.correctForm}
          options={currentItem.options}
          explanation={currentItem.explanation}
          isUkrainian={chromeLocale === 'uk'}
          onComplete={handleComplete}
        />
      </div>

      {rated && (
        <div className="error-correction-action-footer">
          <button
            type="button"
            className="btn btn-accent error-correction-next-btn"
            data-testid="error-correction-next-btn"
            onClick={handleNext}
          >
            {chromeLocale === 'uk' ? 'Наступне завдання →' : 'Next Exercise →'}
          </button>
        </div>
      )}
    </div>
  );
}
