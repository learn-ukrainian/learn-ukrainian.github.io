import React, { useState } from 'react';
import styles from './Activities.module.css';

interface PickSyllablesProps {
  instruction?: string;
  syllables: string[];
  correctIndices: number[];
  category: string; // e.g. "закриті" or "відкриті"
  explanation?: string;
}

/**
 * Вибери закриті/відкриті склади — Pick Syllables
 * Show a list of syllables, learner selects all that match a criteria.
 * Multi-select with check button.
 * Ukrainian textbook exercise pattern (МійКлас Grade 5).
 */
export default function PickSyllables({
  instruction,
  syllables,
  correctIndices,
  category,
  explanation,
}: PickSyllablesProps) {
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [showResult, setShowResult] = useState(false);

  if (!syllables || syllables.length === 0) return null;

  const correctSet = new Set(correctIndices);
  const isFullyCorrect =
    selected.size === correctSet.size &&
    [...selected].every(s => correctSet.has(s));

  const toggleSelect = (idx: number) => {
    if (showResult) return;
    const next = new Set(selected);
    if (next.has(idx)) {
      next.delete(idx);
    } else {
      next.add(idx);
    }
    setSelected(next);
  };

  const reset = () => {
    setSelected(new Set());
    setShowResult(false);
  };

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>🔍</span>
        <span className={styles.activityTitle}>Вибери {category} склади</span>
      </div>

      {instruction && (
        <div className={styles.instruction}>
          <p>{instruction}</p>
        </div>
      )}

      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '10px',
        justifyContent: 'center',
        margin: '1.5rem 0',
      }}>
        {syllables.map((syl, idx) => {
          const isSelected = selected.has(idx);
          const isCorrectItem = correctSet.has(idx);

          let bg = 'var(--co-gray-50, #FAFBFC)';
          let border = '2px solid var(--co-gray-200, #E8EAED)';

          if (showResult) {
            if (isSelected && isCorrectItem) {
              bg = 'var(--co-success-bg, rgba(52, 168, 83, 0.1))';
              border = '2px solid var(--co-success, #34A853)';
            } else if (isSelected && !isCorrectItem) {
              bg = 'var(--co-error-bg, rgba(234, 67, 53, 0.1))';
              border = '2px solid var(--co-error, #EA4335)';
            } else if (!isSelected && isCorrectItem) {
              bg = 'rgba(255, 193, 7, 0.1)';
              border = '2px dashed var(--co-warning, #FBBC04)';
            }
          } else if (isSelected) {
            bg = 'rgba(0, 87, 183, 0.1)';
            border = '2px solid var(--co-blue-deep, #0057B7)';
          }

          return (
            <button
              key={idx}
              onClick={() => toggleSelect(idx)}
              style={{
                padding: '0.75rem 1.25rem',
                fontSize: '1.2rem',
                fontWeight: 600,
                background: bg,
                border,
                borderRadius: '10px',
                cursor: showResult ? 'default' : 'pointer',
                transition: 'all 0.15s',
                minWidth: '80px',
              }}
            >
              {syl}
            </button>
          );
        })}
      </div>

      {showResult && (
        <div style={{
          padding: '0.75rem 1rem',
          background: isFullyCorrect ? 'var(--co-success-bg)' : 'var(--co-error-bg)',
          borderRadius: '8px',
          marginBottom: '1rem',
          textAlign: 'center',
        }}>
          <p style={{ margin: 0, fontWeight: 600 }}>
            {isFullyCorrect
              ? '✅ Правильно!'
              : `❌ Правильні ${category} склади: ${correctIndices.map(i => syllables[i]).join(', ')}`}
          </p>
          {explanation && (
            <p style={{ margin: '0.25rem 0 0', fontSize: '0.9rem' }}>{explanation}</p>
          )}
        </div>
      )}

      {!showResult ? (
        <button
          className={styles.submitButton}
          onClick={() => setShowResult(true)}
          disabled={selected.size === 0}
        >
          Перевірити
        </button>
      ) : (
        <button className={styles.submitButton} onClick={reset}>
          Ще раз
        </button>
      )}
    </div>
  );
}
