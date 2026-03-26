import React, { useState } from 'react';
import styles from './Activities.module.css';

interface CountSyllablesItem {
  word: string;
  correct: number;
  translation?: string;
}

interface CountSyllablesProps {
  instruction?: string;
  items: CountSyllablesItem[];
  maxCount?: number;
}

/**
 * Один, два, три, чотири, п'ять — Count Syllables
 * Given a word, learner picks the syllable count.
 * Ukrainian textbook exercise pattern (МійКлас Grade 5).
 */
export default function CountSyllables({ instruction, items, maxCount = 6 }: CountSyllablesProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [score, setScore] = useState(0);
  const [completed, setCompleted] = useState(false);

  if (!items || items.length === 0) return null;

  const current = items[currentIndex];
  const isCorrect = selected === current.correct;

  const handleSelect = (n: number) => {
    if (showResult) return;
    setSelected(n);
    setShowResult(true);
    if (n === current.correct) setScore(s => s + 1);
  };

  const handleNext = () => {
    if (currentIndex + 1 < items.length) {
      setCurrentIndex(i => i + 1);
      setSelected(null);
      setShowResult(false);
    } else {
      setCompleted(true);
    }
  };

  if (completed) {
    return (
      <div className={styles.activityContainer}>
        <div className={styles.activityHeader}>
          <span className={styles.activityIcon}>🔢</span>
          <span className={styles.activityTitle}>Порахуй склади</span>
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
              setSelected(null);
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
        <span className={styles.activityIcon}>🔢</span>
        <span className={styles.activityTitle}>Порахуй склади</span>
      </div>

      {instruction && (
        <div className={styles.instruction}>
          <p>{instruction}</p>
        </div>
      )}

      <p style={{ margin: '0.5rem 0 0.5rem', fontSize: '0.875rem', color: 'var(--co-gray-600, #5F6368)' }}>
        {currentIndex + 1} / {items.length}
      </p>

      <div style={{ textAlign: 'center', margin: '1.5rem 0' }}>
        <p style={{ fontSize: '2.5rem', fontWeight: 800, margin: '0 0 0.25rem' }}>
          {current.word}
        </p>
        {current.translation && (
          <p style={{ fontSize: '0.9rem', color: 'var(--co-gray-600)', margin: 0, fontStyle: 'italic' }}>
            {current.translation}
          </p>
        )}
      </div>

      <div style={{
        display: 'flex',
        justifyContent: 'center',
        gap: '8px',
        marginBottom: '1rem',
      }}>
        {Array.from({ length: maxCount }, (_, i) => i + 1).map(n => {
          let bg = 'var(--co-gray-50, #FAFBFC)';
          let border = '2px solid var(--co-gray-200, #E8EAED)';
          let color = 'inherit';

          if (showResult) {
            if (n === current.correct) {
              bg = 'var(--co-success, #34A853)';
              border = '2px solid var(--co-success)';
              color = 'white';
            } else if (n === selected && !isCorrect) {
              bg = 'var(--co-error, #EA4335)';
              border = '2px solid var(--co-error)';
              color = 'white';
            }
          } else if (n === selected) {
            border = '2px solid var(--co-blue-deep, #0057B7)';
            bg = 'rgba(0, 87, 183, 0.1)';
          }

          return (
            <button
              key={n}
              onClick={() => handleSelect(n)}
              style={{
                width: '48px',
                height: '48px',
                fontSize: '1.25rem',
                fontWeight: 700,
                background: bg,
                border,
                borderRadius: '50%',
                cursor: showResult ? 'default' : 'pointer',
                color,
                transition: 'all 0.15s',
              }}
            >
              {n}
            </button>
          );
        })}
      </div>

      {showResult && (
        <div style={{
          textAlign: 'center',
          padding: '0.5rem',
          marginBottom: '0.5rem',
        }}>
          <p style={{ margin: 0, fontWeight: 600 }}>
            {isCorrect ? '✅' : '❌'} {current.correct} {current.correct === 1 ? 'склад' : current.correct < 5 ? 'склади' : 'складів'}
          </p>
        </div>
      )}

      {showResult && (
        <button className={styles.submitButton} onClick={handleNext}>
          {currentIndex + 1 < items.length ? 'Далі →' : 'Результат'}
        </button>
      )}
    </div>
  );
}
