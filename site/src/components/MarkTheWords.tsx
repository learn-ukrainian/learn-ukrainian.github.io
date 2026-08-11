import React, { useRef, useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';

export interface MarkTheWordsActivityProps {
  /**
   * @schemaDescription Text passage shown to the learner.
   * @ukrainianText true
   */
  text: string;
  /**
   * @schemaDescription Correct Words value consumed by this component.
   * @ukrainianText true
   */
  correctWords: string[];
  /**
   * @schemaDescription Instruction shown to the learner above the activity.
   * @ukrainianText true
   */
  instruction?: string;
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
  /** Called once when the learner checks the marked words. */
  onComplete?: (correct: boolean) => void;
  /** Lets a host lock the activity after it has recorded the result. */
  disabled?: boolean;
}

export function MarkTheWordsActivity({
  text,
  correctWords,
  instruction,
  isUkrainian,
  onComplete,
  disabled = false,
}: MarkTheWordsActivityProps) {
  const [markedIndices, setMarkedIndices] = useState<Set<number>>(new Set());
  const [submitted, setSubmitted] = useState(false);
  const completionReportedRef = useRef(false);

  // Split text into words while preserving punctuation and spaces
  const tokens = text.match(/[\wа-яіїєґА-ЯІЇЄҐ'-]+|[^\s\wа-яіїєґА-ЯІЇЄҐ'-]+|\s+/gi) || [];

  // Normalize for comparison
  const normalizedCorrect = correctWords.map((w) => w.toLowerCase().trim());

  const handleWordClick = (idx: number) => {
    if (disabled || submitted) return;

    const token = tokens[idx];
    const cleanWord = token.replace(/[^\wа-яіїєґА-ЯІЇЄҐ'-]/gi, '');
    if (!cleanWord) return;

    const newMarked = new Set(markedIndices);
    if (newMarked.has(idx)) {
      newMarked.delete(idx);
    } else {
      newMarked.add(idx);
    }
    setMarkedIndices(newMarked);
  };

  const handleSubmit = () => {
    if (disabled || submitted) return;
    setSubmitted(true);
    if (!completionReportedRef.current) {
      completionReportedRef.current = true;
      onComplete?.(isFullyCorrect);
    }
  };

  const handleReset = () => {
    if (disabled) return;
    setMarkedIndices(new Set());
    setSubmitted(false);
    completionReportedRef.current = false;
  };

  const isWordCorrect = (word: string) => {
    const cleanWord = word.replace(/[^\wа-яіїєґА-ЯІЇЄҐ'-]/gi, '').toLowerCase();
    return normalizedCorrect.includes(cleanWord);
  };

  const getWordClass = (token: string, idx: number) => {
    const cleanWord = token.replace(/[^\wа-яіїєґА-ЯІЇЄҐ'-]/gi, '');
    if (!cleanWord) return '';

    const isMarked = markedIndices.has(idx);
    const isCorrect = isWordCorrect(token);

    if (!submitted) {
      return isMarked ? styles.marked : '';
    }

    // After submission
    if (isMarked && isCorrect) return styles.correctMark;
    if (isMarked && !isCorrect) return styles.wrongMark;
    if (!isMarked && isCorrect) return styles.missedMark;
    return '';
  };

  // Calculate score
  const markedArray = Array.from(markedIndices);
  const correctMarks = markedArray.filter((idx) => isWordCorrect(tokens[idx])).length;
  const wrongMarks = markedArray.filter((idx) => !isWordCorrect(tokens[idx])).length;

  // Total instances of correct words available in the text
  const totalCorrectInstances = tokens.filter((t) => {
    const clean = t.replace(/[^\wа-яіїєґА-ЯІЇЄҐ'-]/gi, '');
    return clean && isWordCorrect(t);
  }).length;

  const missedMarks = totalCorrectInstances - correctMarks;

  const isFullyCorrect = correctMarks === totalCorrectInstances && wrongMarks === 0;

  const checkBtnLabel = isUkrainian ? 'Перевірити' : 'Check Answer';
  const retryBtnLabel = isUkrainian ? 'Спробувати знову' : 'Try Again';
  const successLabel = isUkrainian
    ? '✓ Чудово! Ви знайшли всі правильні слова.'
    : '✓ Perfect! You found all the correct words.';
  const correctPlural = isUkrainian ? 'правильно' : 'correct';
  const incorrectPlural = isUkrainian ? 'неправильно' : 'incorrect';
  const missedLabel = isUkrainian ? 'Пропущено' : 'Missed';
  const correctWordsLabel = isUkrainian ? 'Правильні слова:' : 'Correct words:';

  return (
    <div>
      {instruction && (
        <p className={styles.instruction}>
          <strong>{instruction}</strong>
        </p>
      )}
      <p className={styles.markWordsText}>
        {tokens.map((token, idx) => {
          const cleanWord = token.replace(/[^\wа-яіїєґА-ЯІЇЄҐ'-]/gi, '');

          // Non-word tokens (punctuation, spaces)
          if (!cleanWord) {
            return <span key={idx}>{token}</span>;
          }

          return (
            <span
              key={idx}
              className={`${styles.markableWord} ${getWordClass(token, idx)}`}
              onClick={() => handleWordClick(idx)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault();
                  handleWordClick(idx);
                }
              }}
              role="button"
              tabIndex={disabled || submitted ? -1 : 0}
              aria-pressed={markedIndices.has(idx)}
              aria-disabled={disabled || submitted}
            >
              {token}
            </span>
          );
        })}
      </p>

      {!submitted && (
        <div className={styles.buttonRow}>
          <button className={styles.submitButton} onClick={handleSubmit} disabled={disabled}>
            {checkBtnLabel}
          </button>
        </div>
      )}

      {submitted && (
        <>
          <div
            className={`${styles.feedback} ${isFullyCorrect ? styles.feedbackCorrect : styles.feedbackIncorrect}`}
          >
            {isFullyCorrect ? (
              successLabel
            ) : (
              <>
                {correctMarks > 0 && (
                  <span>
                    ✓ {correctMarks} {correctPlural}.{' '}
                  </span>
                )}
                {wrongMarks > 0 && (
                  <span>
                    ✗ {wrongMarks} {incorrectPlural}.{' '}
                  </span>
                )}
                {missedMarks > 0 && (
                  <span>
                    {missedLabel}: {missedMarks}.{' '}
                  </span>
                )}
                <br />
                <span>
                  {correctWordsLabel} <strong>{correctWords.join(', ')}</strong>
                </span>
              </>
            )}
          </div>
          <div className={styles.buttonRow}>
            <button className={styles.resetButton} onClick={handleReset} disabled={disabled}>
              {retryBtnLabel}
            </button>
          </div>
        </>
      )}
    </div>
  );
}

interface MarkTheWordsProps {
  /**
   * @schemaDescription Nested MDX content rendered inside the component.
   * @ukrainianText false
   */
  children: React.ReactNode;
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
}

export default function MarkTheWords({ children, isUkrainian }: MarkTheWordsProps) {
  const headerLabel = isUkrainian ? 'Відмітьте слова' : 'Mark the Words';

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>🎯</span>
        <span>{headerLabel}</span>
        <ActivityHelp activityType="mark-the-words" isUkrainian={isUkrainian} />
      </div>
      <div className={styles.activityContent}>
        {React.Children.map(children, (child) => {
          if (React.isValidElement(child)) {
            return React.cloneElement(child as React.ReactElement<any>, { isUkrainian });
          }
          return child;
        })}
      </div>
    </div>
  );
}
