import React, { useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';

interface MarkTheWordsActivityProps {
  text: string;
  correctWords: string[];
}

export function MarkTheWordsActivity({ text, correctWords }: MarkTheWordsActivityProps) {
  const [markedWords, setMarkedWords] = useState<Set<string>>(new Set());
  const [submitted, setSubmitted] = useState(false);

  // Split text into words while preserving punctuation and spaces
  const tokens = text.match(/[\wа-яіїєґА-ЯІЇЄҐ']+|[^\s\wа-яіїєґА-ЯІЇЄҐ']+|\s+/gi) || [];

  const handleWordClick = (word: string) => {
    if (submitted) return;

    const cleanWord = word.replace(/[^\wа-яіїєґА-ЯІЇЄҐ']/gi, '');
    if (!cleanWord) return;

    const newMarked = new Set(markedWords);
    if (newMarked.has(cleanWord)) {
      newMarked.delete(cleanWord);
    } else {
      newMarked.add(cleanWord);
    }
    setMarkedWords(newMarked);
  };

  const handleSubmit = () => {
    setSubmitted(true);
  };

  const handleReset = () => {
    setMarkedWords(new Set());
    setSubmitted(false);
  };

  // Normalize for comparison
  const normalizedCorrect = correctWords.map(w => w.toLowerCase().trim());

  const getWordClass = (word: string) => {
    const cleanWord = word.replace(/[^\wа-яіїєґА-ЯІЇЄҐ']/gi, '');
    if (!cleanWord) return '';

    const isMarked = markedWords.has(cleanWord);
    const isCorrect = normalizedCorrect.includes(cleanWord.toLowerCase());

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
  const markedArray = Array.from(markedWords);
  const correctMarks = markedArray.filter(w =>
    normalizedCorrect.includes(w.toLowerCase())
  ).length;
  const wrongMarks = markedArray.filter(w =>
    !normalizedCorrect.includes(w.toLowerCase())
  ).length;
  const missedMarks = correctWords.filter(w =>
    !markedWords.has(w) && !markedWords.has(w.toLowerCase())
  ).length;

  const isFullyCorrect = correctMarks === correctWords.length && wrongMarks === 0;

  return (
    <div>
      <p className={styles.markWordsText}>
        {tokens.map((token, idx) => {
          const cleanWord = token.replace(/[^\wа-яіїєґА-ЯІЇЄҐ']/gi, '');

          // Non-word tokens (punctuation, spaces)
          if (!cleanWord) {
            return <span key={idx}>{token}</span>;
          }

          return (
            <span
              key={idx}
              className={`${styles.markableWord} ${getWordClass(token)}`}
              onClick={() => handleWordClick(token)}
            >
              {token}
            </span>
          );
        })}
      </p>

      {!submitted && (
        <div className={styles.buttonRow}>
          <button
            className={styles.submitButton}
            onClick={handleSubmit}
          >
            Check Answer
          </button>
        </div>
      )}

      {submitted && (
        <>
          <div className={`${styles.feedback} ${isFullyCorrect ? styles.feedbackCorrect : styles.feedbackIncorrect}`}>
            {isFullyCorrect ? (
              '✓ Perfect! You found all the correct words.'
            ) : (
              <>
                {correctMarks > 0 && <span>✓ {correctMarks} correct. </span>}
                {wrongMarks > 0 && <span>✗ {wrongMarks} incorrect. </span>}
                {missedMarks > 0 && <span>Missed: {missedMarks}. </span>}
                <br />
                <span>Correct words: <strong>{correctWords.join(', ')}</strong></span>
              </>
            )}
          </div>
          <div className={styles.buttonRow}>
            <button className={styles.resetButton} onClick={handleReset}>
              Try Again
            </button>
          </div>
        </>
      )}
    </div>
  );
}

interface MarkTheWordsProps {
  children: React.ReactNode;
}

export default function MarkTheWords({ children }: MarkTheWordsProps) {
  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>🎯</span>
        <span>Mark the Words</span>
        <ActivityHelp activityType="mark-the-words" />
      </div>
      <div className={styles.activityContent}>
        {children}
      </div>
    </div>
  );
}
