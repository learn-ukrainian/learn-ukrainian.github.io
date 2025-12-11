import React, { useState, useMemo } from 'react';
import styles from './Activities.module.css';
import { parseMarkdown } from './utils';

interface MatchPair {
  left: string;
  right: string;
}

interface MatchUpProps {
  pairs: MatchPair[];
}

export default function MatchUp({ pairs }: MatchUpProps) {
  const [selectedLeft, setSelectedLeft] = useState<number | null>(null);
  const [matched, setMatched] = useState<Set<number>>(new Set());
  const [wrongPair, setWrongPair] = useState<{ left: number; right: number } | null>(null);

  // Shuffle right side
  const shuffledRight = useMemo(() => {
    const indices = pairs.map((_, i) => i);
    for (let i = indices.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [indices[i], indices[j]] = [indices[j], indices[i]];
    }
    return indices;
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

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>🔗</span>
        <span>Match Up</span>
      </div>
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
          ✓ All matched correctly!
        </div>
      )}
    </div>
  );
}
