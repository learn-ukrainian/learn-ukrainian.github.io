import React, { useState, useMemo } from 'react';
import styles from './Activities.module.css';
import { parseMarkdown, shuffle } from './utils';
import ActivityHelp from './ActivityHelp';

interface MatchPair {
  left: string;
  right: string;
}

interface MatchUpProps {
  pairs: MatchPair[];
  instruction?: string;
  isUkrainian?: boolean;
}

export default function MatchUp({ pairs, instruction, isUkrainian }: MatchUpProps) {
  const [selectedLeft, setSelectedLeft] = useState<number | null>(null);
  const [matched, setMatched] = useState<Set<number>>(new Set());
  const [wrongPair, setWrongPair] = useState<{ left: number; right: number } | null>(null);

  // Shuffle right side (deterministic — seeded by content)
  const shuffledRight = useMemo(() => {
    const indices = pairs.map((_, i) => i);
    return shuffle(indices);
  }, [pairs]);

  const handleLeftClick = (index: number) => {
    if (matched.has(index)) return;
    setSelectedLeft(index);
    setWrongPair(null);
  };

  const handleRightClick = (originalIndex: number) => {
    if (selectedLeft === null || matched.has(originalIndex)) return;

    if (selectedLeft === originalIndex) {
      // Correct match
      setMatched(new Set([...matched, originalIndex]));
      setSelectedLeft(null);
    } else {
      // Wrong match
      setWrongPair({ left: selectedLeft, right: originalIndex });
      setTimeout(() => {
        setWrongPair(null);
        setSelectedLeft(null);
      }, 800);
    }
  };

  const allMatched = matched.size === pairs.length;
  const headerLabel = isUkrainian ? 'Знайдіть пару' : 'Match Up';
  const successLabel = isUkrainian ? '✓ Все з’єднано правильно!' : '✓ All matched correctly!';

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>🔗</span>
        <span>{headerLabel}</span>
        <ActivityHelp activityType="match-up" isUkrainian={isUkrainian} />
      </div>
      {instruction && (
        <p className={styles.instruction}><strong>{instruction}</strong></p>
      )}
      <div className={styles.matchUpContainer}>
        <div className={styles.matchColumn}>
          {pairs.map((pair, index) => (
            <button
              key={`left-${index}`}
              className={`${styles.matchItem} ${matched.has(index) ? styles.matched : ''
                } ${selectedLeft === index ? styles.selected : ''} ${wrongPair?.left === index ? styles.wrong : ''
                }`}
              onClick={() => handleLeftClick(index)}
              disabled={matched.has(index)}
            >
              {parseMarkdown(pair.left)}
            </button>
          ))}
        </div>
        <div className={styles.matchColumn}>
          {shuffledRight.map((originalIndex, displayIndex) => (
            <button
              key={`right-${displayIndex}`}
              className={`${styles.matchItem} ${matched.has(originalIndex) ? styles.matched : ''
                } ${wrongPair?.right === originalIndex ? styles.wrong : ''}`}
              onClick={() => handleRightClick(originalIndex)}
              disabled={matched.has(originalIndex)}
            >
              {parseMarkdown(pairs[originalIndex].right)}
            </button>
          ))}
        </div>
      </div>
      {allMatched && (
        <div className={`${styles.feedback} ${styles.feedbackCorrect}`}>
          {successLabel}
        </div>
      )}
    </div>
  );
}
