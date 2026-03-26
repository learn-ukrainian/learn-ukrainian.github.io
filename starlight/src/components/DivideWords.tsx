import React, { useState } from 'react';
import styles from './Activities.module.css';

interface DivideWordsItem {
  word: string;
  answer: string; // correct division, e.g. "мо-ло-ко"
  hint?: string;
}

interface DivideWordsProps {
  instruction?: string;
  items: DivideWordsItem[];
}

/**
 * Поділи слова на склади — Divide Words into Syllables
 * Learner taps between letters to insert hyphens, then checks.
 * Ukrainian textbook exercise pattern (МійКлас Grade 5).
 */
export default function DivideWords({ instruction, items }: DivideWordsProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [splits, setSplits] = useState<Set<number>>(new Set());
  const [showResult, setShowResult] = useState(false);
  const [score, setScore] = useState(0);
  const [completed, setCompleted] = useState(false);

  if (!items || items.length === 0) return null;

  const current = items[currentIndex];
  const letters = current.word.split('');

  // Parse correct split positions from answer like "мо-ло-ко"
  const getCorrectSplits = (): Set<number> => {
    const result = new Set<number>();
    let pos = 0;
    for (const ch of current.answer) {
      if (ch === '-') {
        result.add(pos);
      } else {
        pos++;
      }
    }
    return result;
  };

  const correctSplits = getCorrectSplits();

  const toggleSplit = (afterIndex: number) => {
    if (showResult) return;
    const next = new Set(splits);
    if (next.has(afterIndex)) {
      next.delete(afterIndex);
    } else {
      next.add(afterIndex);
    }
    setSplits(next);
  };

  const checkAnswer = () => {
    setShowResult(true);
    // Check if splits match exactly
    const isCorrect =
      splits.size === correctSplits.size &&
      [...splits].every(s => correctSplits.has(s));
    if (isCorrect) setScore(s => s + 1);
  };

  const handleNext = () => {
    if (currentIndex + 1 < items.length) {
      setCurrentIndex(i => i + 1);
      setSplits(new Set());
      setShowResult(false);
    } else {
      setCompleted(true);
    }
  };

  const isCorrect =
    splits.size === correctSplits.size &&
    [...splits].every(s => correctSplits.has(s));

  if (completed) {
    return (
      <div className={styles.activityContainer}>
        <div className={styles.activityHeader}>
          <span className={styles.activityIcon}>✂️</span>
          <span className={styles.activityTitle}>Поділи на склади</span>
        </div>
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <p style={{ fontSize: '1.5rem', fontWeight: 700 }}>
            {score}/{items.length}
          </p>
          <p>{score === items.length ? 'Чудово! 🎉' : 'Спробуй ще раз!'}</p>
          <button
            className={styles.submitButton}
            onClick={() => {
              setCurrentIndex(0);
              setSplits(new Set());
              setShowResult(false);
              setScore(0);
              setCompleted(false);
            }}
          >
            Ще раз
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>✂️</span>
        <span className={styles.activityTitle}>Поділи на склади</span>
      </div>

      {instruction && (
        <div className={styles.instruction}>
          <p>{instruction}</p>
        </div>
      )}

      <p style={{ margin: '0.5rem 0 1rem', fontSize: '0.875rem', color: 'var(--co-gray-600, #5F6368)' }}>
        {currentIndex + 1} / {items.length} — Натисни між літерами, щоб розділити на склади
      </p>

      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '0',
        flexWrap: 'wrap',
        margin: '1.5rem 0',
      }}>
        {letters.map((letter, idx) => (
          <React.Fragment key={idx}>
            <span style={{
              fontSize: '2rem',
              fontWeight: 700,
              padding: '0.25rem 0.15rem',
              userSelect: 'none',
            }}>
              {letter}
            </span>
            {idx < letters.length - 1 && (
              <button
                onClick={() => toggleSplit(idx + 1)}
                style={{
                  width: '24px',
                  height: '40px',
                  border: 'none',
                  background: 'transparent',
                  cursor: showResult ? 'default' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: 0,
                  fontSize: '1.5rem',
                  color: splits.has(idx + 1)
                    ? showResult
                      ? correctSplits.has(idx + 1)
                        ? 'var(--co-success, #34A853)'
                        : 'var(--co-error, #EA4335)'
                      : 'var(--co-blue-deep, #0057B7)'
                    : showResult && correctSplits.has(idx + 1)
                      ? 'var(--co-error, #EA4335)'
                      : 'var(--co-gray-300, #DADCE0)',
                  fontWeight: 700,
                  transition: 'all 0.15s',
                }}
                aria-label={`Split after ${letter}`}
              >
                {splits.has(idx + 1) ? '-' : '·'}
              </button>
            )}
          </React.Fragment>
        ))}
      </div>

      {showResult && (
        <div style={{
          padding: '0.75rem 1rem',
          background: isCorrect ? 'var(--co-success-bg)' : 'var(--co-error-bg)',
          borderRadius: '8px',
          marginBottom: '1rem',
          textAlign: 'center',
        }}>
          <p style={{ margin: 0, fontWeight: 600 }}>
            {isCorrect ? '✅ Правильно!' : `❌ Правильно: ${current.answer}`}
          </p>
          {current.hint && (
            <p style={{ margin: '0.25rem 0 0', fontSize: '0.9rem' }}>{current.hint}</p>
          )}
        </div>
      )}

      {!showResult ? (
        <button
          className={styles.submitButton}
          onClick={checkAnswer}
          disabled={splits.size === 0}
        >
          Перевірити
        </button>
      ) : (
        <button className={styles.submitButton} onClick={handleNext}>
          {currentIndex + 1 < items.length ? 'Далі →' : 'Результат'}
        </button>
      )}
    </div>
  );
}
