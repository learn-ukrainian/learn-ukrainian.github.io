import React, { useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';

interface ErrorCorrectionItemProps {
  sentence: string;
  errorWord: string | null;  // null = no error
  correctForm: string;
  options: string[];
  explanation: string;
}

type Step = 'identify' | 'fix' | 'complete';

export function ErrorCorrectionItem({
  sentence,
  errorWord,
  correctForm,
  options,
  explanation,
}: ErrorCorrectionItemProps) {
  const [step, setStep] = useState<Step>('identify');
  const [selectedWord, setSelectedWord] = useState<string | null>(null);
  const [selectedFix, setSelectedFix] = useState<string | null>(null);
  const [wrongAttempts, setWrongAttempts] = useState<string[]>([]);

  // Split sentence into words while preserving punctuation
  const words = sentence.match(/[\wа-яіїєґА-ЯІЇЄҐ']+|[^\s\wа-яіїєґА-ЯІЇЄҐ']+|\s+/gi) || [];

  const handleWordClick = (word: string) => {
    if (step !== 'identify') return;

    // Clean word for comparison (remove punctuation)
    const cleanWord = word.replace(/[^\wа-яіїєґА-ЯІЇЄҐ']/gi, '');

    if (errorWord && cleanWord.toLowerCase() === errorWord.toLowerCase()) {
      // Correct word identified
      setSelectedWord(cleanWord);
      setStep('fix');
    } else if (cleanWord.trim()) {
      // Wrong word selected
      setWrongAttempts(prev => [...prev, cleanWord]);
    }
  };

  const handleNoError = () => {
    if (step !== 'identify') return;

    if (errorWord === null) {
      // Correct - there was no error
      setStep('complete');
    } else {
      // Wrong - there was an error
      setWrongAttempts(prev => [...prev, '__no_error__']);
    }
  };

  const handleFixSelect = (fix: string) => {
    if (step !== 'fix') return;

    setSelectedFix(fix);
    setStep('complete');
  };

  const handleReset = () => {
    setStep('identify');
    setSelectedWord(null);
    setSelectedFix(null);
    setWrongAttempts([]);
  };

  const isFixCorrect = selectedFix === correctForm;
  const isNoErrorCorrect = errorWord === null && step === 'complete';

  return (
    <div className={styles.errorCorrectionItem}>
      {/* Step indicator */}
      <div className={styles.stepIndicator}>
        {step === 'identify' && <span className={styles.stepBadge}>Step 1: Find the error</span>}
        {step === 'fix' && <span className={styles.stepBadge}>Step 2: Choose the correct form</span>}
        {step === 'complete' && <span className={styles.stepBadgeComplete}>Complete</span>}
      </div>

      {/* Sentence with clickable words */}
      <p className={styles.errorSentence}>
        {words.map((word, idx) => {
          const cleanWord = word.replace(/[^\wа-яіїєґА-ЯІЇЄҐ']/gi, '');
          const isError = errorWord && cleanWord.toLowerCase() === errorWord.toLowerCase();
          const isWrongAttempt = wrongAttempts.includes(cleanWord);
          const isSelected = selectedWord && cleanWord.toLowerCase() === selectedWord.toLowerCase();

          // Non-word tokens (punctuation, spaces)
          if (!cleanWord) {
            return <span key={idx}>{word}</span>;
          }

          return (
            <span
              key={idx}
              className={`
                ${styles.clickableWord}
                ${step === 'identify' ? styles.wordHoverable : ''}
                ${isWrongAttempt ? styles.wordWrong : ''}
                ${isSelected && step !== 'identify' ? styles.wordSelected : ''}
                ${step === 'complete' && isError ? styles.wordError : ''}
              `}
              onClick={() => handleWordClick(word)}
            >
              {step === 'complete' && isError && selectedFix ? (
                <span className={styles.correctedWord}>
                  <s>{word}</s> {selectedFix}
                </span>
              ) : (
                word
              )}
            </span>
          );
        })}
      </p>

      {/* No Error button - only in identify step */}
      {step === 'identify' && (
        <button
          className={`${styles.noErrorButton} ${wrongAttempts.includes('__no_error__') ? styles.noErrorWrong : ''}`}
          onClick={handleNoError}
        >
          ✓ No error in this sentence
        </button>
      )}

      {/* Options - only in fix step */}
      {step === 'fix' && options.length > 0 && (
        <div className={styles.fixOptions}>
          <p className={styles.fixPrompt}>Choose the correct form for "<strong>{selectedWord}</strong>":</p>
          <div className={styles.optionChips}>
            {options.map((option, idx) => (
              <button
                key={idx}
                className={styles.chip}
                onClick={() => handleFixSelect(option)}
              >
                {option}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Result feedback */}
      {step === 'complete' && (
        <>
          <div className={`${styles.feedback} ${(isFixCorrect || isNoErrorCorrect) ? styles.feedbackCorrect : styles.feedbackIncorrect}`}>
            {isNoErrorCorrect ? (
              '✓ Correct! There was no error in this sentence.'
            ) : isFixCorrect ? (
              `✓ Correct! "${errorWord}" → "${correctForm}"`
            ) : (
              `✗ The correct answer is: "${errorWord}" → "${correctForm}"`
            )}
            {explanation && (
              <div className={styles.explanation}>{explanation}</div>
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

interface ErrorCorrectionProps {
  children: React.ReactNode;
}

export default function ErrorCorrection({ children }: ErrorCorrectionProps) {
  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>🔍</span>
        <span>Find and Fix</span>
        <ActivityHelp activityType="error-correction" />
      </div>
      <div className={styles.activityContent}>
        {children}
      </div>
    </div>
  );
}
