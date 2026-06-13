import React, { useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';

interface MorphemeItem {
  /**
   * @schemaDescription Ukrainian word shown to the learner.
   * @ukrainianText true
   */
  word: string;        // The full word: "прийшов"
  /**
   * @schemaDescription Morpheme value consumed by this component.
   * @ukrainianText true
   */
  morpheme: string;    // The part to highlight: "при"
  /**
   * @schemaDescription Type value consumed by this component.
   * @ukrainianText false
   */
  type?: 'prefix' | 'root' | 'suffix';  // Optional classification
}

interface HighlightMorphemesActivityProps {
  /**
   * @schemaDescription Instruction shown to the learner above the activity.
   * @ukrainianText true
   */
  instruction?: string;
  /**
   * @schemaDescription Text passage shown to the learner.
   * @ukrainianText true
   */
  text: string;
  /**
   * @schemaDescription Morphemes value consumed by this component.
   * @ukrainianText true
   */
  morphemes: MorphemeItem[];
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
}

export function HighlightMorphemesActivity({
  instruction,
  text,
  morphemes,
  isUkrainian
}: HighlightMorphemesActivityProps) {
  // Track clicks by token INDEX, not word text (fixes duplicate word bug)
  const [clickedIndices, setClickedIndices] = useState<Set<number>>(new Set());
  const [submitted, setSubmitted] = useState(false);

  // Create a map of word -> morpheme for quick lookup
  const wordToMorpheme = new Map<string, MorphemeItem>();
  morphemes.forEach(m => {
    const normalizedWord = m.word.toLowerCase().trim();
    wordToMorpheme.set(normalizedWord, m);
  });

  // Split text into tokens (words, punctuation, spaces)
  const tokens: string[] = text.match(/[\wа-яіїєґА-ЯІЇЄҐ']+|[^\s\wа-яіїєґА-ЯІЇЄҐ']+|\s+/gi) || [];

  const handleWordClick = (idx: number, word: string) => {
    if (submitted) return;

    const cleanWord = word.replace(/[^\wа-яіїєґА-ЯІЇЄҐ']/gi, '');
    if (!cleanWord) return;

    // Toggle click by INDEX (not word text) to handle duplicates
    const newClicked = new Set(clickedIndices);
    if (newClicked.has(idx)) {
      newClicked.delete(idx);
    } else {
      newClicked.add(idx);
    }
    setClickedIndices(newClicked);
  };

  const handleSubmit = () => {
    setSubmitted(true);
  };

  const handleReset = () => {
    setClickedIndices(new Set());
    setSubmitted(false);
  };

  const renderWord = (token: string, idx: number) => {
    const cleanWord = token.replace(/[^\wа-яіїєґА-ЯІЇЄҐ']/gi, '');
    if (!cleanWord) {
      return <span key={idx}>{token}</span>;
    }

    const normalizedWord = cleanWord.toLowerCase();
    const morphemeItem = wordToMorpheme.get(normalizedWord);

    // Check if THIS specific token (by index) was clicked
    const isClicked = clickedIndices.has(idx);

    // ALL words are clickable, but only morpheme words show highlighting
    if (!morphemeItem) {
      // Non-morpheme word - clickable but shows as wrong when clicked
      let wordClass = styles.markableWord;

      if (submitted && isClicked) {
        // They clicked a wrong word
        wordClass += ` ${styles.wrongMark}`;
      } else if (isClicked && !submitted) {
        wordClass += ` ${styles.marked}`;
      }

      return (
        <span
          key={idx}
          className={wordClass}
          onClick={() => handleWordClick(idx, token)}
        >
          {token}
        </span>
      );
    }

    const shouldShowMorpheme = isClicked || submitted;

    // Find the morpheme within the word (case-insensitive)
    const wordLower = token.toLowerCase();
    const morphemeLower = morphemeItem.morpheme.toLowerCase();
    const morphemeStart = wordLower.indexOf(morphemeLower);

    if (morphemeStart === -1) {
      // Morpheme not found in word (shouldn't happen with valid data)
      return <span key={idx}>{token}</span>;
    }

    const morphemeEnd = morphemeStart + morphemeItem.morpheme.length;

    // Split the word into: before | morpheme | after
    const before = token.slice(0, morphemeStart);
    const morphemePart = token.slice(morphemeStart, morphemeEnd);
    const after = token.slice(morphemeEnd);

    // Determine styling based on state
    let wordClass = styles.markableWord;
    let morphemeClass = '';

    if (submitted) {
      // After submission, show if they got it right
      if (isClicked) {
        wordClass += ` ${styles.correctMark}`;
        morphemeClass = styles.morphemeHighlighted;
      } else {
        wordClass += ` ${styles.missedMark}`;
        morphemeClass = styles.morphemeHighlighted;
      }
    } else if (isClicked) {
      // Before submission, show they clicked it
      wordClass += ` ${styles.marked}`;
      morphemeClass = styles.morphemeHighlighted;
    }

    return (
      <span
        key={idx}
        className={wordClass}
        onClick={() => handleWordClick(idx, token)}
      >
        {shouldShowMorpheme ? (
          <>
            <span>{before}</span>
            <span className={morphemeClass}>{morphemePart}</span>
            <span>{after}</span>
          </>
        ) : (
          token
        )}
      </span>
    );
  };

  // Calculate score by counting token indices
  // Find which token indices should be clicked (tokens that match morpheme words)
  const expectedIndices = new Set<number>();
  tokens.forEach((token, idx) => {
    const cleanWord = token.replace(/[^\wа-яіїєґА-ЯІЇЄҐ']/gi, '');
    if (cleanWord && wordToMorpheme.has(cleanWord.toLowerCase())) {
      expectedIndices.add(idx);
    }
  });

  const correctClicks = Array.from(clickedIndices).filter(idx => expectedIndices.has(idx)).length;
  const wrongClicks = Array.from(clickedIndices).filter(idx => !expectedIndices.has(idx)).length;
  const totalExpected = expectedIndices.size;
  const isFullyCorrect = correctClicks === totalExpected && wrongClicks === 0;

  const checkBtnLabel = isUkrainian ? 'Перевірити' : 'Check Answer';
  const retryBtnLabel = isUkrainian ? 'Спробувати знову' : 'Try Again';
  const successLabel = isUkrainian ? '✓ Чудово! Ви правильно знайшли всі частини слів.' : '✓ Perfect! You found all the word parts correctly.';
  const correctLabel = isUkrainian ? 'правильно' : 'correct';
  const incorrectSelectionsLabel = isUkrainian ? 'неправильних варіантів' : 'incorrect selection(s)';

  return (
    <div>
      {instruction && <p className={styles.activityInstruction}>{instruction}</p>}
      <p className={styles.markWordsText}>
        {tokens.map((token, idx) => renderWord(token, idx))}
      </p>

      {!submitted && (
        <div className={styles.buttonRow}>
          <button
            className={styles.submitButton}
            onClick={handleSubmit}
          >
            {checkBtnLabel}
          </button>
        </div>
      )}

      {submitted && (
        <>
          <div className={`${styles.feedback} ${isFullyCorrect ? styles.feedbackCorrect : styles.feedbackIncorrect}`}>
            {isFullyCorrect ? (
              successLabel
            ) : (
              <>
                <span>✓ {correctClicks} / {totalExpected} {correctLabel}. </span>
                {wrongClicks > 0 && (
                  <span>{wrongClicks} {incorrectSelectionsLabel}.</span>
                )}
              </>
            )}
          </div>
          <div className={styles.buttonRow}>
            <button className={styles.resetButton} onClick={handleReset}>
              {retryBtnLabel}
            </button>
          </div>
        </>
      )}
    </div>
  );
}

interface HighlightMorphemesProps {
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

export default function HighlightMorphemes({ children, isUkrainian }: HighlightMorphemesProps) {
  const headerLabel = isUkrainian ? 'Знайдіть частини слова' : 'Find Word Parts';

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>🔍</span>
        <span>{headerLabel}</span>
        <ActivityHelp activityType="highlight-morphemes" isUkrainian={isUkrainian} />
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
