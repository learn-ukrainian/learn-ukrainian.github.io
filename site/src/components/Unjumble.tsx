import React, { useRef, useState, useMemo } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import {
  chromeFacingBilingual,
  useActivityIsUkrainian,
  useChromeLocale,
} from '../lib/i18n/useChromeLocale';
import { shuffleNotCorrect } from './utils';

/** Letter-tile word builders (answer has no spaces) vs sentence builders. */
export function isWordUnjumbleAnswer(answer: string): boolean {
  return answer.trim().length > 0 && !/\s/.test(answer.trim());
}

// Generate consistent colors for words
const WORD_COLORS = [
  '#E53935', '#D81B60', '#8E24AA', '#5E35B1', '#3949AB',
  '#1E88E5', '#039BE5', '#00ACC1', '#00897B', '#43A047',
  '#7CB342', '#FB8C00', '#F4511E', '#6D4C41'
];

function getWordColor(word: string, index: number): string {
  const charSum = word.split('').reduce((sum, char) => sum + char.charCodeAt(0), 0);
  return WORD_COLORS[(charSum + index) % WORD_COLORS.length];
}

// Tiles never carry punctuation, but the YAML `answer` field can include a
// terminal `.`/`?`/`!` or clause commas — normalize both sides before
// comparing so those don't cause false negatives.
// Stress marks are teaching notation, not letters: tiles `б/у/р/я/к` must match
// the answer `буря́к`. Covers the combining acute (U+0301) and the precomposed
// stressed vowels (á é í ó ú ý and Cyrillic ѓ ќ, which decompose to base + U+0301).
function stripStress(text: string): string {
  return text.normalize('NFD').replace(/\u0301/g, '').normalize('NFC');
}

export function normalizeUnjumbleAnswer(text: string): string {
  return stripStress(text)
    .trim()
    .replace(/[.?!]+$/, '')
    .replace(/,/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase();
}

export interface UnjumbleQuestionProps {
  /**
   * @schemaDescription Words shown to the learner.
   * @ukrainianText true
   */
  words: string;
  /**
   * @schemaDescription Correct answer used for validation and feedback.
   * @ukrainianText true
   */
  answer: string;
  /**
   * @schemaDescription Hint value consumed by this component.
   * @ukrainianText true
   */
  hint?: string;
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
  /** Skip the legacy shuffle when a host provides deterministic jumbled tokens. */
  wordsAreJumbled?: boolean;
  /** Called once when the learner checks a complete sentence. */
  onComplete?: (correct: boolean) => void;
  /** Lets a host lock retry after it has recorded the result. */
  disabled?: boolean;
}

export function UnjumbleQuestion({
  words,
  answer,
  hint,
  isUkrainian,
  wordsAreJumbled = false,
  onComplete,
  disabled = false,
}: UnjumbleQuestionProps) {
  // Preserve punctuation inside already-jumbled slash-delimited tokens while
  // retaining the legacy separators used by lesson MDX inputs.
  const wordList = useMemo(() => {
    const rawWords = (
      wordsAreJumbled ? words.split(' / ') : words.split(/[\/|,]\s*/)
    ).map(w => w.trim());
    const correctOrder = answer.split(/\s+/);

    // Shuffle ensuring words are NOT in the correct answer order
    const shuffled = wordsAreJumbled ? rawWords : shuffleNotCorrect(rawWords, correctOrder);

    return shuffled.map((word, idx) => ({
      id: `word-${idx}`,
      text: word,
      color: getWordColor(word, idx)
    }));
  }, [words, answer, wordsAreJumbled]);

  const [availableWords, setAvailableWords] = useState(wordList);
  const [selectedWords, setSelectedWords] = useState<typeof wordList>([]);
  const [showResult, setShowResult] = useState(false);
  const [draggedWord, setDraggedWord] = useState<string | null>(null);
  const completionReportedRef = useRef(false);

  const handleWordClick = (word: typeof wordList[0], fromSelected: boolean) => {
    if (disabled || showResult) return;

    if (fromSelected) {
      // Move back to available
      setSelectedWords(prev => prev.filter(w => w.id !== word.id));
      setAvailableWords(prev => [...prev, word]);
    } else {
      // Move to selected
      setAvailableWords(prev => prev.filter(w => w.id !== word.id));
      setSelectedWords(prev => [...prev, word]);
    }
  };

  const handleDragStart = (e: React.DragEvent, wordId: string) => {
    setDraggedWord(wordId);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDropOnSentence = (e: React.DragEvent) => {
    e.preventDefault();
    if (!draggedWord || disabled || showResult) return;

    const word = availableWords.find(w => w.id === draggedWord);
    if (word) {
      setAvailableWords(prev => prev.filter(w => w.id !== draggedWord));
      setSelectedWords(prev => [...prev, word]);
    }
    setDraggedWord(null);
  };

  const handleDropOnBank = (e: React.DragEvent) => {
    e.preventDefault();
    if (!draggedWord || disabled || showResult) return;

    const word = selectedWords.find(w => w.id === draggedWord);
    if (word) {
      setSelectedWords(prev => prev.filter(w => w.id !== draggedWord));
      setAvailableWords(prev => [...prev, word]);
    }
    setDraggedWord(null);
  };

  // Allow reordering within selected words
  const handleDropOnWord = (e: React.DragEvent, targetIndex: number) => {
    e.preventDefault();
    e.stopPropagation();
    if (!draggedWord || disabled || showResult) return;

    const draggedFromSelected = selectedWords.find(w => w.id === draggedWord);
    const draggedFromAvailable = availableWords.find(w => w.id === draggedWord);

    if (draggedFromSelected) {
      // Reorder within selected
      const currentIndex = selectedWords.findIndex(w => w.id === draggedWord);
      if (currentIndex !== targetIndex) {
        const newSelected = [...selectedWords];
        const [removed] = newSelected.splice(currentIndex, 1);
        newSelected.splice(targetIndex, 0, removed);
        setSelectedWords(newSelected);
      }
    } else if (draggedFromAvailable) {
      // Move from available to specific position
      setAvailableWords(prev => prev.filter(w => w.id !== draggedWord));
      const newSelected = [...selectedWords];
      newSelected.splice(targetIndex, 0, draggedFromAvailable);
      setSelectedWords(newSelected);
    }
    setDraggedWord(null);
  };

  const handleCheck = () => {
    if (disabled || showResult) return;
    setShowResult(true);
    if (!completionReportedRef.current) {
      completionReportedRef.current = true;
      onComplete?.(isCorrect);
    }
  };

  const handleReset = () => {
    if (disabled) return;
    setAvailableWords(wordList);
    setSelectedWords([]);
    setShowResult(false);
    completionReportedRef.current = false;
  };

  const joiner = /\s/.test(answer.trim()) ? ' ' : '';
  const userAnswer = selectedWords.map(w => w.text).join(joiner);
  const isCorrect = normalizeUnjumbleAnswer(userAnswer) === normalizeUnjumbleAnswer(answer);
  const wordMode = isWordUnjumbleAnswer(answer);

  const placeholderLabel = wordMode
    ? (isUkrainian ? 'Перетягніть літери сюди, щоб скласти слово...' : 'Drag letters here to form the word...')
    : (isUkrainian ? 'Перетягніть слова сюди, щоб скласти речення...' : 'Drag words here to build the sentence...');
  const checkBtnLabel = isUkrainian ? 'Перевірити' : 'Check Answer';
  const retryBtnLabel = isUkrainian ? 'Спробувати знову' : 'Try Again';
  const correctLabel = isUkrainian ? '✓ Правильно!' : '✓ Correct!';
  const incorrectLabel = wordMode
    ? (isUkrainian ? '✗ Правильне слово:' : '✗ The correct word is:')
    : (isUkrainian ? '✗ Правильне речення:' : '✗ The correct sentence is:');

  return (
    <div className={styles.unjumbleQuestion} data-activity="unjumble-question">
      {hint && <p className={styles.hint}>💡 {hint}</p>}
      {/* Sentence Builder Zone */}
      <div
        className={`${styles.sentenceBuilder} ${showResult ? (isCorrect ? styles.correct : styles.incorrect) : ''}`}
        data-activity="sentence-builder"
        onDragOver={handleDragOver}
        onDrop={handleDropOnSentence}
      >
        {selectedWords.length > 0 ? (
          selectedWords.map((word, index) => (
            <button
              key={word.id}
              className={styles.wordTile}
              style={{
                backgroundColor: word.color,
                color: 'white',
                cursor: showResult ? 'default' : 'grab'
              }}
              draggable={!showResult && !disabled}
              onDragStart={(e) => handleDragStart(e, word.id)}
              onDragOver={handleDragOver}
              onDrop={(e) => handleDropOnWord(e, index)}
              onClick={() => handleWordClick(word, true)}
              disabled={showResult || disabled}
            >
              {word.text}
            </button>
          ))
        ) : (
          <span className={styles.placeholder}>{placeholderLabel}</span>
        )}
      </div>

      {/* Word Bank */}
      <div
        className={styles.wordBank}
        data-activity="word-bank"
        onDragOver={handleDragOver}
        onDrop={handleDropOnBank}
      >
        {availableWords.map((word) => (
          <button
            key={word.id}
            className={styles.wordTile}
            style={{
              backgroundColor: word.color,
              color: 'white',
              cursor: showResult ? 'default' : 'grab'
            }}
            draggable={!showResult && !disabled}
            onDragStart={(e) => handleDragStart(e, word.id)}
            onClick={() => handleWordClick(word, false)}
            disabled={showResult || disabled}
          >
            {word.text}
          </button>
        ))}
      </div>

      <div className={styles.buttonRow}>
        {!showResult ? (
          <button
            className={styles.submitButton}
            onClick={handleCheck}
            disabled={availableWords.length > 0 || disabled}
          >
            {checkBtnLabel}
          </button>
        ) : (
          <button className={styles.resetButton} onClick={handleReset} disabled={disabled}>
            {retryBtnLabel}
          </button>
        )}
      </div>

      {showResult && (
        <div
          className={`${styles.feedback} ${isCorrect ? styles.feedbackCorrect : styles.feedbackIncorrect}`}
          data-activity="feedback"
          data-correct={isCorrect ? 'true' : 'false'}
        >
          {isCorrect ? correctLabel : `${incorrectLabel} ${answer}`}
        </div>
      )}
    </div>
  );
}

interface UnjumbleItem {
  /**
   * @schemaDescription Words shown to the learner.
   * @ukrainianText true
   */
  words?: string;
  /**
   * @schemaDescription Jumbled value consumed by this component.
   * @ukrainianText true
   */
  jumbled?: string;  // Alternative field name from MDX generator
  /**
   * @schemaDescription Correct answer used for validation and feedback.
   * @ukrainianText true
   */
  answer: string;
  /**
   * @schemaDescription Hint value consumed by this component.
   * @ukrainianText true
   */
  hint?: string;
}

interface UnjumbleProps {
  /**
   * @schemaDescription Array of activity items rendered by the component.
   * @ukrainianText true
   */
  items?: UnjumbleItem[];
  /**
   * @schemaDescription Instruction shown to the learner above the activity.
   * @ukrainianText true
   */
  instruction?: string;
  /**
   * @schemaDescription Nested MDX content rendered inside the component.
   * @ukrainianText false
   */
  children?: React.ReactNode;
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
}

export default function Unjumble({ items, instruction, children, isUkrainian: bakedIsUkrainian }: UnjumbleProps) {
  const isUkrainian = useActivityIsUkrainian(bakedIsUkrainian);
  const locale = useChromeLocale();
  const wordMode = Boolean(items?.length) && items!.every((item) => isWordUnjumbleAnswer(item.answer));
  const headerLabel = wordMode
    ? (isUkrainian ? 'Складіть слово' : 'Build the Word')
    : (isUkrainian ? 'Складіть речення' : 'Build the Sentence');
  const shownInstruction = chromeFacingBilingual(instruction, locale);

  return (
    <div className={styles.activityContainer} data-activity="unjumble" data-mode={wordMode ? 'word' : 'sentence'}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>🧩</span>
        <span>{headerLabel}</span>
        <ActivityHelp activityType="unjumble" isUkrainian={isUkrainian} />
      </div>
      {shownInstruction && (
        <p className={styles.instruction}><strong>{shownInstruction}</strong></p>
      )}
      <div className={styles.activityContent}>
        {items ? items.map((item, index) => (
          <UnjumbleQuestion
            key={index}
            words={item.words || item.jumbled || ''}
            answer={item.answer}
            hint={item.hint}
            isUkrainian={isUkrainian}
          />
        )) : children}
      </div>
    </div>
  );
}
