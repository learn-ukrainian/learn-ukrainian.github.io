import React, { useState, useMemo, useCallback } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { shuffleNotCorrect } from './utils';

// Generate consistent colors for letters
const LETTER_COLORS = [
  '#E53935', '#D81B60', '#8E24AA', '#5E35B1', '#3949AB',
  '#1E88E5', '#039BE5', '#00ACC1', '#00897B', '#43A047',
  '#7CB342', '#C0CA33', '#FDD835', '#FFB300', '#FB8C00',
  '#F4511E', '#6D4C41', '#546E7A'
];

function getLetterColor(letter: string, index: number): string {
  const charCode = letter.toLowerCase().charCodeAt(0);
  return LETTER_COLORS[(charCode + index) % LETTER_COLORS.length];
}

interface AnagramQuestionProps {
  scrambled: string;
  answer: string;
  hint?: string;
  isUkrainian?: boolean;
}

export function AnagramQuestion({ scrambled, answer, hint, isUkrainian }: AnagramQuestionProps) {
  // Parse scrambled letters (space-separated) and shuffle so they're never in correct order
  const letters = useMemo(() => {
    const rawLetters = scrambled.split(' ').filter(l => l.trim());
    const correctOrder = answer.split('');

    // Shuffle ensuring letters are NOT in the correct answer order
    const shuffled = shuffleNotCorrect(rawLetters, correctOrder);

    return shuffled.map((letter, idx) => ({
      id: `letter-${idx}`,
      char: letter,
      color: getLetterColor(letter, idx)
    }));
  }, [scrambled, answer]);

  const [availableLetters, setAvailableLetters] = useState(letters);
  const [selectedLetters, setSelectedLetters] = useState<typeof letters>([]);
  const [showResult, setShowResult] = useState(false);
  const [draggedLetter, setDraggedLetter] = useState<string | null>(null);

  const handleLetterClick = (letter: typeof letters[0], fromSelected: boolean) => {
    if (showResult) return;

    if (fromSelected) {
      // Move back to available
      setSelectedLetters(prev => prev.filter(l => l.id !== letter.id));
      setAvailableLetters(prev => [...prev, letter]);
    } else {
      // Move to selected
      setAvailableLetters(prev => prev.filter(l => l.id !== letter.id));
      setSelectedLetters(prev => [...prev, letter]);
    }
  };

  const handleDragStart = (e: React.DragEvent, letterId: string) => {
    setDraggedLetter(letterId);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDropOnAnswer = (e: React.DragEvent) => {
    e.preventDefault();
    if (!draggedLetter || showResult) return;

    const letter = availableLetters.find(l => l.id === draggedLetter);
    if (letter) {
      setAvailableLetters(prev => prev.filter(l => l.id !== draggedLetter));
      setSelectedLetters(prev => [...prev, letter]);
    }
    setDraggedLetter(null);
  };

  const handleDropOnBank = (e: React.DragEvent) => {
    e.preventDefault();
    if (!draggedLetter || showResult) return;

    const letter = selectedLetters.find(l => l.id === draggedLetter);
    if (letter) {
      setSelectedLetters(prev => prev.filter(l => l.id !== draggedLetter));
      setAvailableLetters(prev => [...prev, letter]);
    }
    setDraggedLetter(null);
  };

  const handleCheck = () => {
    setShowResult(true);
  };

  const handleReset = () => {
    setAvailableLetters(letters);
    setSelectedLetters([]);
    setShowResult(false);
  };

  const userAnswer = selectedLetters.map(l => l.char).join('');
  const isCorrect = userAnswer.toLowerCase() === answer.toLowerCase();

  const placeholderLabel = isUkrainian ? 'Перетягніть літери сюди, щоб скласти слово...' : 'Drag letters here to form the word...';
  const checkBtnLabel = isUkrainian ? 'Перевірити' : 'Check Answer';
  const retryBtnLabel = isUkrainian ? 'Спробувати знову' : 'Try Again';
  const correctLabel = isUkrainian ? '✓ Правильно!' : '✓ Correct!';
  const incorrectLabel = isUkrainian ? '✗ Неправильно. Відповідь:' : '✗ The answer is:';

  return (
    <div className={styles.anagramQuestion}>
      {/* Answer Zone */}
      <div
        className={`${styles.answerZone} ${showResult ? (isCorrect ? styles.correct : styles.incorrect) : ''}`}
        onDragOver={handleDragOver}
        onDrop={handleDropOnAnswer}
      >
        {selectedLetters.length > 0 ? (
          selectedLetters.map((letter) => (
            <button
              key={letter.id}
              className={styles.letterTile}
              style={{
                backgroundColor: letter.color,
                color: 'white',
                cursor: showResult ? 'default' : 'grab'
              }}
              draggable={!showResult}
              onDragStart={(e) => handleDragStart(e, letter.id)}
              onClick={() => handleLetterClick(letter, true)}
              disabled={showResult}
            >
              {letter.char}
            </button>
          ))
        ) : (
          <span className={styles.placeholder}>{placeholderLabel}</span>
        )}
      </div>

      {/* Letter Bank */}
      <div
        className={styles.letterBank}
        onDragOver={handleDragOver}
        onDrop={handleDropOnBank}
      >
        {availableLetters.map((letter) => (
          <button
            key={letter.id}
            className={styles.letterTile}
            style={{
              backgroundColor: letter.color,
              color: 'white',
              cursor: showResult ? 'default' : 'grab'
            }}
            draggable={!showResult}
            onDragStart={(e) => handleDragStart(e, letter.id)}
            onClick={() => handleLetterClick(letter, false)}
            disabled={showResult}
          >
            {letter.char}
          </button>
        ))}
      </div>

      <div className={styles.buttonRow}>
        {!showResult ? (
          <button
            className={styles.submitButton}
            onClick={handleCheck}
            disabled={availableLetters.length > 0}
          >
            {checkBtnLabel}
          </button>
        ) : (
          <button className={styles.resetButton} onClick={handleReset}>
            {retryBtnLabel}
          </button>
        )}
      </div>

      {showResult && (
        <div className={`${styles.feedback} ${isCorrect ? styles.feedbackCorrect : styles.feedbackIncorrect}`}>
          {isCorrect ? correctLabel : `${incorrectLabel} ${answer}`}
        </div>
      )}
    </div>
  );
}

interface AnagramItem {
  scrambled: string;
  answer: string;
  hint?: string;
}

interface AnagramProps {
  items?: AnagramItem[];
  children?: React.ReactNode;
  isUkrainian?: boolean;
}

export default function Anagram({ items, children, isUkrainian }: AnagramProps) {
  const headerLabel = isUkrainian ? 'Переставте літери' : 'Unscramble the Letters';

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>🔤</span>
        <span>{headerLabel}</span>
        <ActivityHelp activityType="anagram" isUkrainian={isUkrainian} />
      </div>
      <div className={styles.activityContent}>
        {items ? items.map((item, index) => (
          <AnagramQuestion
            key={index}
            scrambled={item.scrambled}
            answer={item.answer}
            hint={item.hint}
            isUkrainian={isUkrainian}
          />
        )) : children}
      </div>
    </div>
  );
}
