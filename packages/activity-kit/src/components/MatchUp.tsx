import React, { useEffect, useMemo, useRef, useState } from 'react';
import styles from './Activities.module.css';
import { parseMarkdown, shuffle } from './utils';
import ActivityHelp from './ActivityHelp';

export interface MatchPair {
  /**
   * @schemaDescription Left value consumed by this component.
   * @ukrainianText true
   */
  left: string;
  /**
   * @schemaDescription Right value consumed by this component.
   * @ukrainianText true
   */
  right: string;
  lemmaId?: string;
}

export interface MatchUpProps {
  /**
   * @schemaDescription Pairs value consumed by this component.
   * @ukrainianText true
   */
  pairs: MatchPair[];
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
  onComplete?: () => void;
  onMatch?: (pairIndex: number, rating: 'again' | 'hard' | 'good') => void;
}


const MATCH_PAIR_HUES = [
  199, 32, 262, 174, 239, 92, 286, 151, 215, 49,
  271, 188, 230, 108, 300, 164, 206, 67, 253, 181,
  222, 132, 288, 192, 243, 78, 278, 142, 218, 58,
] as const;
const MATCH_PAIR_COLOR_COUNT = MATCH_PAIR_HUES.length;

type MatchPairStyle = React.CSSProperties & {
  '--match-pair-hue': string;
};

const getMatchedPairStyle = (index: number, isMatched: boolean): MatchPairStyle | undefined => {
  if (!isMatched) return undefined;
  return { '--match-pair-hue': String(MATCH_PAIR_HUES[index % MATCH_PAIR_COLOR_COUNT]) };
};

export default function MatchUp({ pairs, instruction, isUkrainian, onComplete, onMatch }: MatchUpProps) {
  const [selectedLeft, setSelectedLeft] = useState<number | null>(null);
  const [matched, setMatched] = useState<Set<number>>(new Set());
  const matchedRef = useRef<Set<number>>(new Set());
  const [wrongPair, setWrongPair] = useState<{ left: number; right: number } | null>(null);
  const [misses, setMisses] = useState<Record<number, number>>({});
  const completedRef = useRef(false);

  // Reset state when pairs change (attempt counting resets between boards)
  useEffect(() => {
    setSelectedLeft(null);
    setMatched(new Set());
    matchedRef.current = new Set();
    setWrongPair(null);
    setMisses({});
    completedRef.current = false;
  }, [pairs]);

  // Shuffle right side (deterministic — seeded by content)
  const shuffledRight = useMemo(() => {
    const indices = pairs.map((_, i) => i);
    return shuffle(indices);
  }, [pairs]);

  const handleLeftClick = (index: number) => {
    if (matchedRef.current.has(index) || wrongPair) return;
    setSelectedLeft(index);
    setWrongPair(null);
  };

  const handleRightClick = (originalIndex: number) => {
    if (selectedLeft === null || matchedRef.current.has(originalIndex) || wrongPair) return;

    if (selectedLeft === originalIndex) {
      // Correct match
      matchedRef.current.add(originalIndex);
      const currentMisses = misses[selectedLeft] || 0;
      const rating = currentMisses === 0 ? 'good' : currentMisses === 1 ? 'hard' : 'again';
      onMatch?.(selectedLeft, rating);

      setMatched(new Set(matchedRef.current));
      setSelectedLeft(null);
    } else {
      // Wrong match
      setMisses((prev) => ({
        ...prev,
        [selectedLeft]: (prev[selectedLeft] || 0) + 1,
      }));
      setWrongPair({ left: selectedLeft, right: originalIndex });
      setTimeout(() => {
        setWrongPair(null);
        setSelectedLeft(null);
      }, 800);
    }
  };


  const allMatched = matched.size === pairs.length;

  useEffect(() => {
    if (allMatched && !completedRef.current) {
      completedRef.current = true;
      onComplete?.();
    }
    if (!allMatched) completedRef.current = false;
  }, [allMatched, onComplete]);
  const headerLabel = isUkrainian ? 'Знайдіть пару' : 'Match Up';
  const successLabel = isUkrainian ? '✓ Все з’єднано правильно!' : '✓ All matched correctly!';

  return (
    <div className={styles.activityContainer} data-activity="match-up">
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>🔗</span>
        <span>{headerLabel}</span>
        <ActivityHelp activityType="match-up" isUkrainian={isUkrainian} />
      </div>
      {instruction && (
        <p className={styles.instruction}><strong>{instruction}</strong></p>
      )}
      <div className={styles.matchUpContainer}>
        <div className={styles.matchColumn} data-activity="match-left-column">
          {pairs.map((pair, index) => (
            <button
              key={`left-${index}`}
              className={`${styles.matchItem} ${matched.has(index) ? styles.matched : ''
                } ${selectedLeft === index ? styles.selected : ''} ${wrongPair?.left === index ? styles.wrong : ''
                }`}
              data-activity="match-left-tile"
              data-matched={matched.has(index) ? 'true' : 'false'}
              data-pair-color={matched.has(index) ? index % MATCH_PAIR_COLOR_COUNT : undefined}
              data-selected={selectedLeft === index ? 'true' : 'false'}
              style={getMatchedPairStyle(index, matched.has(index))}
              onClick={() => handleLeftClick(index)}
              disabled={matched.has(index)}
            >
              {parseMarkdown(pair.left)}
            </button>
          ))}
        </div>
        <div className={styles.matchColumn} data-activity="match-right-column">
          {shuffledRight.map((originalIndex, displayIndex) => (
            <button
              key={`right-${displayIndex}`}
              className={`${styles.matchItem} ${matched.has(originalIndex) ? styles.matched : ''
                } ${wrongPair?.right === originalIndex ? styles.wrong : ''}`}
              data-activity="match-right-tile"
              data-matched={matched.has(originalIndex) ? 'true' : 'false'}
              data-original-index={originalIndex}
              data-pair-color={matched.has(originalIndex) ? originalIndex % MATCH_PAIR_COLOR_COUNT : undefined}
              style={getMatchedPairStyle(originalIndex, matched.has(originalIndex))}
              onClick={() => handleRightClick(originalIndex)}
              disabled={matched.has(originalIndex)}
            >
              {parseMarkdown(pairs[originalIndex].right)}
            </button>
          ))}
        </div>
      </div>
      {allMatched && (
        <div
          className={`${styles.feedback} ${styles.feedbackCorrect}`}
          data-activity="match-feedback"
          data-correct="true"
        >
          {successLabel}
        </div>
      )}
    </div>
  );
}
