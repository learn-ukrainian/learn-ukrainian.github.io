import React, { useState } from 'react';
import styles from './Activities.module.css';

interface OddOneOutProps {
  /**
   * @schemaDescription Instruction shown to the learner above the activity.
   * @ukrainianText true
   */
  instruction?: string;
  items: {
    /**
     * @schemaDescription Words shown to the learner.
     * @ukrainianText true
     */
    words: string[];
    /**
     * @schemaDescription Correct value consumed by this component.
     * @ukrainianText false
     */
    correct: number;
    /**
     * @schemaDescription Feedback explanation shown after the learner answers.
     * @ukrainianText true
     */
    explanation: string;
  }[];
}

/**
 * Четверте «зайве» — Odd One Out
 * Show 4 words, learner picks the one that doesn't belong.
 * Ukrainian textbook exercise pattern (МійКлас Grade 5).
 */
export default function OddOneOut({ instruction, items }: OddOneOutProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [score, setScore] = useState(0);
  const [completed, setCompleted] = useState(false);

  if (!items || items.length === 0) return null;

  const current = items[currentIndex];
  const isCorrect = selected === current.correct;

  const handleSelect = (idx: number) => {
    if (showResult) return;
    setSelected(idx);
    setShowResult(true);
    if (idx === current.correct) {
      setScore(s => s + 1);
    }
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
          <span className={styles.activityIcon}>🎯</span>
          <span className={styles.activityTitle}>Четверте «зайве»</span>
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
        <span className={styles.activityIcon}>🎯</span>
        <span className={styles.activityTitle}>Четверте «зайве»</span>
      </div>

      {instruction && (
        <div className={styles.instruction}>
          <p>{instruction}</p>
        </div>
      )}

      <p style={{ margin: '0.5rem 0 1rem', fontSize: '0.875rem', color: 'var(--co-gray-600, #5F6368)' }}>
        {currentIndex + 1} / {items.length}
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '1rem' }}>
        {current.words.map((word, idx) => {
          let bg = '';
          let border = '2px solid var(--co-gray-200, #E8EAED)';
          if (showResult) {
            if (idx === current.correct) {
              bg = 'var(--co-success-bg, rgba(52, 168, 83, 0.1))';
              border = '2px solid var(--co-success, #34A853)';
            } else if (idx === selected && !isCorrect) {
              bg = 'var(--co-error-bg, rgba(234, 67, 53, 0.1))';
              border = '2px solid var(--co-error, #EA4335)';
            }
          } else if (idx === selected) {
            border = '2px solid var(--co-blue-deep, #0057B7)';
          }

          return (
            <button
              key={idx}
              onClick={() => handleSelect(idx)}
              style={{
                padding: '1rem',
                fontSize: '1.2rem',
                fontWeight: 600,
                background: bg || 'var(--co-gray-50, #FAFBFC)',
                border,
                borderRadius: '10px',
                cursor: showResult ? 'default' : 'pointer',
                transition: 'all 0.2s',
              }}
            >
              {word}
            </button>
          );
        })}
      </div>

      {showResult && (
        <div style={{
          padding: '0.75rem 1rem',
          background: isCorrect ? 'var(--co-success-bg)' : 'var(--co-error-bg)',
          borderRadius: '8px',
          marginBottom: '1rem',
        }}>
          <p style={{ margin: 0, fontWeight: 600 }}>
            {isCorrect ? '✅ Правильно!' : '❌ Неправильно'}
          </p>
          <p style={{ margin: '0.25rem 0 0', fontSize: '0.9rem' }}>
            {current.explanation}
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
