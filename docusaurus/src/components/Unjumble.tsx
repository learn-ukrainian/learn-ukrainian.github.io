import React, { useState, useMemo } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { shuffleNotCorrect } from './utils';

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

interface UnjumbleQuestionProps {
  words: string;
  answer: string;
  hint?: string;
}

export function UnjumbleQuestion({ words, answer, hint }: UnjumbleQuestionProps) {
  // Parse words (can be separated by /, |, or ,) and shuffle so they're never in correct order
  const wordList = useMemo(() => {
    const rawWords = words.split(/[\/|,]\s*/).map(w => w.trim());
    const correctOrder = answer.split(/\s+/);

    // Shuffle ensuring words are NOT in the correct answer order
    const shuffled = shuffleNotCorrect(rawWords, correctOrder);

    return shuffled.map((word, idx) => ({
      id: `word-${idx}`,
      text: word,
      color: getWordColor(word, idx)
    }));
  }, [words, answer]);

  const [availableWords, setAvailableWords] = useState(wordList);
  const [selectedWords, setSelectedWords] = useState<typeof wordList>([]);
  const [showResult, setShowResult] = useState(false);
  const [draggedWord, setDraggedWord] = useState<string | null>(null);

  const handleWordClick = (word: typeof wordList[0], fromSelected: boolean) => {
    if (showResult) return;

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
    if (!draggedWord || showResult) return;

    const word = availableWords.find(w => w.id === draggedWord);
    if (word) {
      setAvailableWords(prev => prev.filter(w => w.id !== draggedWord));
      setSelectedWords(prev => [...prev, word]);
    }
    setDraggedWord(null);
  };

  const handleDropOnBank = (e: React.DragEvent) => {
    e.preventDefault();
    if (!draggedWord || showResult) return;

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
    if (!draggedWord || showResult) return;

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
    setShowResult(true);
  };

  const handleReset = () => {
    setAvailableWords(wordList);
    setSelectedWords([]);
    setShowResult(false);
  };

  const userAnswer = selectedWords.map(w => w.text).join(' ');
  const isCorrect = userAnswer.toLowerCase().trim() === answer.toLowerCase().trim();

  return (
    <div className={styles.unjumbleQuestion}>
      {hint && <p className={styles.hint}>💡 {hint}</p>}

      {/* Sentence Builder Zone */}
      <div
        className={`${styles.sentenceBuilder} ${showResult ? (isCorrect ? styles.correct : styles.incorrect) : ''}`}
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
              draggable={!showResult}
              onDragStart={(e) => handleDragStart(e, word.id)}
              onDragOver={handleDragOver}
              onDrop={(e) => handleDropOnWord(e, index)}
              onClick={() => handleWordClick(word, true)}
              disabled={showResult}
            >
              {word.text}
            </button>
          ))
        ) : (
          <span className={styles.placeholder}>Drag words here to build the sentence...</span>
        )}
      </div>

      {/* Word Bank */}
      <div
        className={styles.wordBank}
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
            draggable={!showResult}
            onDragStart={(e) => handleDragStart(e, word.id)}
            onClick={() => handleWordClick(word, false)}
            disabled={showResult}
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
            disabled={availableWords.length > 0}
          >
            Check Answer
          </button>
        ) : (
          <button className={styles.resetButton} onClick={handleReset}>
            Try Again
          </button>
        )}
      </div>

      {showResult && (
        <div className={`${styles.feedback} ${isCorrect ? styles.feedbackCorrect : styles.feedbackIncorrect}`}>
          {isCorrect ? '✓ Correct!' : `✗ The correct sentence is: ${answer}`}
        </div>
      )}
    </div>
  );
}

interface UnjumbleProps {
  children: React.ReactNode;
}

export default function Unjumble({ children }: UnjumbleProps) {
  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>🧩</span>
        <span>Build the Sentence</span>
        <ActivityHelp activityType="unjumble" />
      </div>
      <div className={styles.activityContent}>
        {children}
      </div>
    </div>
  );
}
