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
  instruction?: React.ReactNode;
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
  /**
   * @schemaDescription Optional practice-only pair-coding mode.
   * @ukrainianText false
   */
  matchedPairCoding?: 'semantic-four';
  onComplete?: () => void;
  onMatch?: (pairIndex: number, rating: 'again' | 'hard' | 'good') => void;
}


const MATCH_PAIR_HUES = [
  199, 32, 262, 174, 239, 92, 286, 151, 215, 49,
  271, 188, 230, 108, 300, 164, 206, 67, 253, 181,
  222, 132, 288, 192, 243, 78, 278, 142, 218, 58,
] as const;
const MATCH_PAIR_COLOR_COUNT = MATCH_PAIR_HUES.length;

const SEMANTIC_FOUR_TOKENS = [
  { name: 'teal' },
  { name: 'orange' },
  { name: 'purple' },
  { name: 'yellow' },
] as const;

const PAIR_CODING_CLASS = 'match-pair-coded';

const MISSHAKE_TIMEOUT_MS = 240;

/** Convert a 1-based match order to a circled digit string. Supports 1–50. */
function circledNumber(n: number): string {
  if (n >= 1 && n <= 20) return String.fromCodePoint(0x245f + n);
  if (n >= 21 && n <= 35) return String.fromCodePoint(0x3250 + n);
  if (n >= 36 && n <= 50) return String.fromCodePoint(0x32a0 + n);
  return String(n);
}

type MatchPairStyle = React.CSSProperties & {
  '--match-pair-hue': string;
};

const getMatchedPairStyle = (index: number, isMatched: boolean): MatchPairStyle | undefined => {
  if (!isMatched) return undefined;
  return { '--match-pair-hue': String(MATCH_PAIR_HUES[index % MATCH_PAIR_COLOR_COUNT]) };
};

const getSemanticTokenStyle = (pairIndex: number): React.CSSProperties | undefined => {
  const token = SEMANTIC_FOUR_TOKENS[pairIndex % SEMANTIC_FOUR_TOKENS.length];
  if (!token) return undefined;
  return {
    '--match-pair-token': token.name,
  } as React.CSSProperties;
};

export default function MatchUp({
  pairs,
  instruction,
  isUkrainian,
  matchedPairCoding,
  onComplete,
  onMatch,
}: MatchUpProps) {
  const [selectedLeft, setSelectedLeft] = useState<number | null>(null);
  const [matched, setMatched] = useState<Set<number>>(new Set());
  const matchedRef = useRef<Set<number>>(new Set());
  const [matchedOrder, setMatchedOrder] = useState<Map<number, number>>(new Map());
  const matchedOrderRef = useRef<Map<number, number>>(new Map());
  const [wrongPair, setWrongPair] = useState<{ left: number; right: number } | null>(null);
  const [misses, setMisses] = useState<Record<number, number>>({});
  const completedRef = useRef(false);

  // Reset state when pairs change (attempt counting resets between boards)
  useEffect(() => {
    setSelectedLeft(null);
    setMatched(new Set());
    matchedRef.current = new Set();
    setMatchedOrder(new Map());
    matchedOrderRef.current = new Map();
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
      const nextOrder = matchedRef.current.size;
      matchedOrderRef.current = new Map(matchedOrderRef.current).set(originalIndex, nextOrder);

      const currentMisses = misses[selectedLeft] || 0;
      const rating = currentMisses === 0 ? 'good' : currentMisses === 1 ? 'hard' : 'again';
      onMatch?.(selectedLeft, rating);

      setMatched(new Set(matchedRef.current));
      setMatchedOrder(new Map(matchedOrderRef.current));
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
      }, MISSHAKE_TIMEOUT_MS);
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

  const pairTag = (originalIndex: number): string | null => {
    if (matchedPairCoding !== 'semantic-four') return null;
    const order = matchedOrder.get(originalIndex);
    if (order === undefined) return null;
    return circledNumber(order);
  };

  const pairAccessibleName = (originalIndex: number, side: 'left' | 'right'): string | undefined => {
    if (matchedPairCoding !== 'semantic-four' || !matched.has(originalIndex)) return undefined;
    const pair = pairs[originalIndex];
    if (!pair) return undefined;
    const order = matchedOrder.get(originalIndex);
    const tag = order ? circledNumber(order) : '';
    const partner = side === 'left' ? pair.right : pair.left;
    if (isUkrainian) {
      return `${pair.left} — ${pair.right}, пара ${tag}, з’єднано з ${partner}`;
    }
    return `${pair.left} — ${pair.right}, pair ${tag}, matched with ${partner}`;
  };

  const instructionId = `match-up-instruction-${Math.random().toString(36).slice(2)}`;
  const progressRegionId = `match-up-progress-${Math.random().toString(36).slice(2)}`;

  const headerLabel = isUkrainian ? (
    <span lang="uk">Знайдіть пару</span>
  ) : (
    <>
      <span lang="uk">Знайдіть пару</span>
      {' / '}
      <span style={{ fontSize: '0.8rem', opacity: 0.8 }} lang="en">Match Up</span>
    </>
  );
  const successLabel = isUkrainian ? (
    <span lang="uk">✓ Все з’єднано правильно!</span>
  ) : (
    <>
      <span lang="uk">✓ Все з’єднано правильно!</span>
      {' / '}
      <span style={{ fontSize: '0.9rem', opacity: 0.8 }} lang="en">All matched correctly!</span>
    </>
  );

  return (
    <div className={styles.activityContainer} data-activity="match-up">
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>🔗</span>
        <span>{headerLabel}</span>
        <ActivityHelp activityType="match-up" isUkrainian={isUkrainian} />
      </div>
      {instruction && (
        <p
          id={instructionId}
          className={styles.instruction}
          aria-live={matchedPairCoding === 'semantic-four' ? 'polite' : undefined}
        >
          <strong>{instruction}</strong>
        </p>
      )}
      {matchedPairCoding === 'semantic-four' && (
        <div
          id={progressRegionId}
          aria-live="polite"
          style={{
            position: 'absolute',
            width: '1px',
            height: '1px',
            padding: 0,
            margin: '-1px',
            overflow: 'hidden',
            clip: 'rect(0, 0, 0, 0)',
            whiteSpace: 'nowrap',
            border: 0,
          }}
        >
          {isUkrainian
            ? `З’єднано ${matched.size} з ${pairs.length}`
            : `Matched ${matched.size} of ${pairs.length}`}
        </div>
      )}
      <div className="matchUpContainer" data-pair-coding={matchedPairCoding}>
        <div className="matchColumn" data-activity="match-left-column">
          {pairs.map((pair, index) => (
            <button
              key={`left-${index}`}
              className={`matchItem ${matched.has(index) ? 'matched' : ''} ${
                selectedLeft === index ? 'selected' : ''
              } ${wrongPair?.left === index ? 'wrong' : ''} ${
                matchedPairCoding === 'semantic-four' && matched.has(index) ? PAIR_CODING_CLASS : ''
              }`}
              data-activity="match-left-tile"
              data-matched={matched.has(index) ? 'true' : 'false'}
              data-pair-color={matched.has(index) ? index % MATCH_PAIR_COLOR_COUNT : undefined}
              data-pair-coding={matchedPairCoding}
              data-pair-token={matchedPairCoding === 'semantic-four' ? index % SEMANTIC_FOUR_TOKENS.length : undefined}
              data-selected={selectedLeft === index ? 'true' : 'false'}
              data-original-index={index}
              aria-pressed={selectedLeft === index}
              aria-label={pairAccessibleName(index, 'left')}
              style={
                matchedPairCoding === 'semantic-four'
                  ? getSemanticTokenStyle(index)
                  : getMatchedPairStyle(index, matched.has(index))
              }
              onClick={() => handleLeftClick(index)}
              disabled={matched.has(index)}
            >
              {parseMarkdown(pair.left)}
              {matchedPairCoding === 'semantic-four' && pairTag(index) ? (
                <span className="matchPairTag" aria-hidden="true">{pairTag(index)}</span>
              ) : null}
            </button>
          ))}
        </div>
        <div className="matchColumn" data-activity="match-right-column">
          {shuffledRight.map((originalIndex, displayIndex) => (
            <button
              key={`right-${displayIndex}`}
              className={`matchItem ${matched.has(originalIndex) ? 'matched' : ''} ${
                wrongPair?.right === originalIndex ? 'wrong' : ''
              } ${
                matchedPairCoding === 'semantic-four' && matched.has(originalIndex) ? PAIR_CODING_CLASS : ''
              }`}
              data-activity="match-right-tile"
              data-matched={matched.has(originalIndex) ? 'true' : 'false'}
              data-original-index={originalIndex}
              data-pair-color={matched.has(originalIndex) ? originalIndex % MATCH_PAIR_COLOR_COUNT : undefined}
              data-pair-coding={matchedPairCoding}
              data-pair-token={matchedPairCoding === 'semantic-four' ? originalIndex % SEMANTIC_FOUR_TOKENS.length : undefined}
              style={
                matchedPairCoding === 'semantic-four'
                  ? getSemanticTokenStyle(originalIndex)
                  : getMatchedPairStyle(originalIndex, matched.has(originalIndex))
              }
              aria-label={pairAccessibleName(originalIndex, 'right')}
              onClick={() => handleRightClick(originalIndex)}
              disabled={matched.has(originalIndex)}
            >
              {parseMarkdown(pairs[originalIndex].right)}
              {matchedPairCoding === 'semantic-four' && pairTag(originalIndex) ? (
                <span className="matchPairTag" aria-hidden="true">{pairTag(originalIndex)}</span>
              ) : null}
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
