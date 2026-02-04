import React, { useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { parseMarkdown } from './utils';

// Historical Cyrillic characters that are difficult to type on modern keyboards
const HISTORICAL_CHARS = [
  { char: 'ѣ', name: 'yat' },
  { char: 'ѫ', name: 'big yus' },
  { char: 'ѧ', name: 'small yus' },
  { char: 'ѯ', name: 'ksi' },
  { char: 'ѱ', name: 'psi' },
  { char: 'ѳ', name: 'fita' },
  { char: 'ѵ', name: 'izhitsa' },
  { char: 'ъ', name: 'hard sign' },
  { char: 'ь', name: 'soft sign' },
  { char: 'ѹ', name: 'uk' },
  { char: 'ꙋ', name: 'monograph uk' },
  { char: 'і', name: 'decimal i' },
  { char: 'ї', name: 'yi' },
  { char: 'ѡ', name: 'omega' },
  { char: 'ꙁ', name: 'zelo' },
];

interface TranscriptionProps {
  title: string;
  instruction?: string;
  original: string;
  answer: string;
  hints?: string[];
  isUkrainian?: boolean;
}

export default function Transcription({
  title,
  instruction,
  original,
  answer,
  hints = [],
  isUkrainian = true
}: TranscriptionProps) {
  const [userAnswer, setUserAnswer] = useState('');
  const [showResult, setShowResult] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);
  const [showHints, setShowHints] = useState(false);
  const [inputRef, setInputRef] = useState<HTMLTextAreaElement | null>(null);

  const headerLabel = isUkrainian ? 'Транскрипція' : 'Transcription';
  const checkLabel = isUkrainian ? 'Перевірити' : 'Check';
  const showAnswerLabel = isUkrainian ? 'Показати відповідь' : 'Show Answer';
  const hintsLabel = isUkrainian ? 'Підказки' : 'Hints';
  const correctLabel = isUkrainian ? 'Правильно!' : 'Correct!';
  const incorrectLabel = isUkrainian ? 'Спробуйте ще раз' : 'Try again';
  const yourTranscriptionLabel = isUkrainian ? 'Ваша транскрипція' : 'Your transcription';
  const historicalCharsLabel = isUkrainian ? 'Історичні символи:' : 'Historical characters:';

  const normalizeText = (text: string): string => {
    // Normalize for comparison: lowercase, remove extra spaces, handle titlo marks
    return text
      .toLowerCase()
      .replace(/\s+/g, ' ')
      .trim();
  };

  const checkAnswer = () => {
    const normalizedUser = normalizeText(userAnswer);
    const normalizedAnswer = normalizeText(answer);
    const correct = normalizedUser === normalizedAnswer;
    setIsCorrect(correct);
    setShowResult(true);
  };

  const showCorrectAnswer = () => {
    setUserAnswer(answer);
    setIsCorrect(true);
    setShowResult(true);
  };

  const insertChar = (char: string) => {
    if (inputRef) {
      const start = inputRef.selectionStart || 0;
      const end = inputRef.selectionEnd || 0;
      const newValue = userAnswer.slice(0, start) + char + userAnswer.slice(end);
      setUserAnswer(newValue);
      setShowResult(false);
      // Restore focus and cursor position
      setTimeout(() => {
        inputRef.focus();
        inputRef.setSelectionRange(start + char.length, start + char.length);
      }, 0);
    } else {
      setUserAnswer(userAnswer + char);
      setShowResult(false);
    }
  };

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>📜</span>
        <span>{title || headerLabel}</span>
        <ActivityHelp activityType="transcription" isUkrainian={isUkrainian} />
      </div>
      <div className={styles.activityContent}>
        {instruction && (
          <div className={styles.readingContext}>
            {parseMarkdown(instruction)}
          </div>
        )}

        {/* Original archaic text display */}
        <div className={styles.transcriptionOriginal}>
          <div className={styles.archaicText}>
            {original}
          </div>
        </div>

        {/* Historical character keyboard */}
        <div className={styles.historicalKeyboard}>
          <span className={styles.keyboardLabel}>{historicalCharsLabel}</span>
          <div className={styles.charButtons}>
            {HISTORICAL_CHARS.map(({ char, name }) => (
              <button
                key={char}
                className={styles.charButton}
                onClick={() => insertChar(char)}
                title={name}
                type="button"
              >
                {char}
              </button>
            ))}
          </div>
        </div>

        {/* User input area */}
        <div className={styles.transcriptionInput}>
          <textarea
            ref={setInputRef}
            value={userAnswer}
            onChange={(e) => {
              setUserAnswer(e.target.value);
              setShowResult(false);
            }}
            placeholder={yourTranscriptionLabel}
            className={showResult ? (isCorrect ? styles.correct : styles.incorrect) : ''}
            rows={3}
          />
        </div>

        {/* Result feedback */}
        {showResult && (
          <div className={`${styles.feedback} ${isCorrect ? styles.success : styles.error}`}>
            {isCorrect ? correctLabel : incorrectLabel}
            {!isCorrect && (
              <div className={styles.correctAnswer}>
                <strong>{isUkrainian ? 'Правильна відповідь:' : 'Correct answer:'}</strong> {answer}
              </div>
            )}
          </div>
        )}

        {/* Hints section */}
        {hints.length > 0 && (
          <>
            <button
              className={styles.secondaryButton}
              onClick={() => setShowHints(!showHints)}
              style={{ marginBottom: '0.5rem' }}
            >
              {showHints ? (isUkrainian ? 'Сховати підказки' : 'Hide hints') : hintsLabel}
            </button>
            {showHints && (
              <div className={styles.hintsList}>
                <ul>
                  {hints.map((hint, index) => (
                    <li key={index}>{parseMarkdown(hint)}</li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}

        <div className={styles.buttonRow}>
          <button className={styles.submitButton} onClick={checkAnswer}>
            {checkLabel}
          </button>
          <button className={styles.secondaryButton} onClick={showCorrectAnswer}>
            {showAnswerLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
