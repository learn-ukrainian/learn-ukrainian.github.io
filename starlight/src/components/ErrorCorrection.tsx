import React, { useState, useMemo } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { shuffle } from './utils';

interface ErrorCorrectionItemProps {
  sentence: string;
  errorWord: string | null;  // null = no error
  correctForm: string;
  options: string[];
  explanation: string;
  isUkrainian?: boolean;
}

type Step = 'identify' | 'fix' | 'complete';

export function ErrorCorrectionItem({
  sentence,
  errorWord,
  correctForm,
  options,
  explanation,
  isUkrainian
}: ErrorCorrectionItemProps) {
  // Shuffle options on mount
  const shuffledOptions = useMemo(() => shuffle([...options]), [options]);

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

    if (errorWord) {
      // For multi-word errors, check if the clicked word is part of the error phrase
      const errorWords = errorWord.split(/\s+/);
      const cleanErrorWords = errorWords.map(w => w.replace(/[^\wа-яіїєґА-ЯІЇЄҐ']/gi, '').toLowerCase());

      if (cleanErrorWords.includes(cleanWord.toLowerCase())) {
        // Correct word/phrase identified
        setSelectedWord(errorWord); // Store the full error phrase
        setStep('fix');
      } else if (cleanWord.trim()) {
        // Wrong word selected
        setWrongAttempts(prev => [...prev, cleanWord]);
      }
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

  const step1Label = isUkrainian ? 'Крок 1: Знайдіть помилку' : 'Step 1: Find the error';
  const step2Label = isUkrainian ? 'Крок 2: Оберіть правильну форму' : 'Step 2: Choose the correct form';
  const completeLabel = isUkrainian ? 'Завершено' : 'Complete';
  const noErrorLabel = isUkrainian ? '✓ У цьому реченні немає помилок' : '✓ No error in this sentence';
  const fixPromptLabel = isUkrainian ? 'Оберіть правильну форму для' : 'Choose the correct form for';
  const retryBtnLabel = isUkrainian ? 'Спробувати знову' : 'Try Again';

  return (
    <div className={styles.errorCorrectionItem}>
      {/* Step indicator */}
      <div className={styles.stepIndicator}>
        {step === 'identify' && <span className={styles.stepBadge}>{step1Label}</span>}
        {step === 'fix' && <span className={styles.stepBadge}>{step2Label}</span>}
        {step === 'complete' && <span className={styles.stepBadgeComplete}>{completeLabel}</span>}
      </div>

      {/* Sentence with clickable words */}
      <p className={styles.errorSentence}>
        {words.map((word, idx) => {
          const cleanWord = word.replace(/[^\wа-яіїєґА-ЯІЇЄҐ']/gi, '');

          // Check if this word is part of a multi-word error
          const errorWords = errorWord ? errorWord.split(/\s+/).map(w => w.replace(/[^\wа-яіїєґА-ЯІЇЄҐ']/gi, '').toLowerCase()) : [];
          const isError = errorWords.includes(cleanWord.toLowerCase());
          const isWrongAttempt = wrongAttempts.includes(cleanWord);
          const isSelected = selectedWord && errorWords.includes(cleanWord.toLowerCase()) && step !== 'identify';

          // Non-word tokens (punctuation, spaces)
          if (!cleanWord) {
            return <span key={idx}>{word}</span>;
          }

          // For complete step, show strikethrough for all error words, replacement after last error word
          const isLastErrorWord = errorWord && isError && idx === words.findLastIndex(w => {
            const cw = w.replace(/[^\wа-яіїєґА-ЯІЇЄҐ']/gi, '');
            return errorWords.includes(cw.toLowerCase());
          });

          return (
            <span
              key={idx}
              className={`
                ${styles.clickableWord}
                ${step === 'identify' ? styles.wordHoverable : ''}
                ${isWrongAttempt ? styles.wordWrong : ''}
                ${isSelected ? styles.wordSelected : ''}
                ${step === 'complete' && isError ? styles.wordError : ''}
              `}
              onClick={() => handleWordClick(word)}
            >
              {step === 'complete' && isError ? (
                <>
                  <s>{word}</s>
                  {isLastErrorWord && selectedFix ? ` ${selectedFix}` : ''}
                </>
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
          {noErrorLabel}
        </button>
      )}

      {/* Options - only in fix step */}
      {step === 'fix' && shuffledOptions.length > 0 && (
        <div className={styles.fixOptions}>
          <p className={styles.fixPrompt}>{fixPromptLabel} "<strong>{errorWord}</strong>":</p>
          <div className={styles.optionChips}>
            {shuffledOptions.map((option, idx) => (
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
              isUkrainian ? '✓ Правильно! У цьому реченні не було помилок.' : '✓ Correct! There was no error in this sentence.'
            ) : isFixCorrect ? (
              `✓ ${isUkrainian ? 'Правильно!' : 'Correct!'} "${errorWord}" → "${correctForm}"`
            ) : (
              `${isUkrainian ? '✗ Правильна відповідь:' : '✗ The correct answer is:'} "${errorWord}" → "${correctForm}"`
            )}
            {explanation && (
              <div className={styles.explanation}>{explanation}</div>
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

interface ErrorCorrectionItemData {
  sentence: string;
  errorWord: string | null;
  correctForm: string;
  options: string[];
  explanation: string;
}

interface ErrorCorrectionProps {
  items?: ErrorCorrectionItemData[];
  children?: React.ReactNode;
  instruction?: string;
  isUkrainian?: boolean;
}

export default function ErrorCorrection({ items, children, instruction, isUkrainian }: ErrorCorrectionProps) {
  const headerLabel = isUkrainian ? 'Знайдіть і виправте помилку' : 'Find and Fix';

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>🔍</span>
        <span>{headerLabel}</span>
        <ActivityHelp activityType="error-correction" isUkrainian={isUkrainian} />
      </div>
      {instruction && (
        <p className={styles.instruction}><strong>{instruction}</strong></p>
      )}
      <div className={styles.activityContent}>
        {items ? items.map((item, index) => (
          <ErrorCorrectionItem
            key={index}
            sentence={item.sentence}
            errorWord={item.errorWord}
            correctForm={item.correctForm}
            options={item.options}
            explanation={item.explanation}
            isUkrainian={isUkrainian}
          />
        )) : React.Children.map(children, (child) => {
          if (React.isValidElement(child)) {
            return React.cloneElement(child as React.ReactElement<any>, { isUkrainian });
          }
          return child;
        })}
      </div>
    </div>
  );
}
