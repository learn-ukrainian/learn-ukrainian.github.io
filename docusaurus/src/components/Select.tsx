import React, { useState, useMemo } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';

interface SelectQuestionProps {
  question: string;
  options: string[];
  correctAnswers: string[];
  explanation?: string;
}

export function SelectQuestion({ question, options, correctAnswers, explanation }: SelectQuestionProps) {
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [submitted, setSubmitted] = useState(false);

  // Normalize correct answers for comparison
  const normalizedCorrect = useMemo(() =>
    new Set(correctAnswers.map(a => a.toLowerCase().trim())),
    [correctAnswers]
  );

  const handleToggle = (option: string) => {
    if (submitted) return;

    const newSelected = new Set(selected);
    if (newSelected.has(option)) {
      newSelected.delete(option);
    } else {
      newSelected.add(option);
    }
    setSelected(newSelected);
  };

  const handleSubmit = () => {
    setSubmitted(true);
  };

  const handleReset = () => {
    setSelected(new Set());
    setSubmitted(false);
  };

  const isCorrectOption = (option: string) =>
    normalizedCorrect.has(option.toLowerCase().trim());

  const isFullyCorrect = submitted &&
    correctAnswers.length === selected.size &&
    correctAnswers.every(a => selected.has(a));

  const getOptionClass = (option: string) => {
    if (!submitted) {
      return selected.has(option) ? styles.checked : '';
    }

    const isSelected = selected.has(option);
    const isCorrect = isCorrectOption(option);

    if (isSelected && isCorrect) return styles.correctAnswer;
    if (isSelected && !isCorrect) return styles.wrongAnswer;
    if (!isSelected && isCorrect) return styles.missedAnswer;
    return '';
  };

  return (
    <div className={styles.selectQuestion}>
      <p className={styles.questionText}>{question}</p>

      <div className={styles.checkboxOptions}>
        {options.map((option, idx) => (
          <div
            key={idx}
            className={`${styles.checkboxOption} ${getOptionClass(option)}`}
            onClick={() => handleToggle(option)}
          >
            <div className={`${styles.checkbox} ${selected.has(option) ? styles.checked : ''}`}>
              {selected.has(option) && '✓'}
            </div>
            <span className={styles.checkboxLabel}>{option}</span>
          </div>
        ))}
      </div>

      {!submitted && (
        <div className={styles.buttonRow} style={{ marginTop: '1rem' }}>
          <button
            className={styles.submitButton}
            onClick={handleSubmit}
            disabled={selected.size === 0}
          >
            Check Answer
          </button>
        </div>
      )}

      {submitted && (
        <>
          <div className={`${styles.feedback} ${isFullyCorrect ? styles.feedbackCorrect : styles.feedbackIncorrect}`}>
            {isFullyCorrect ? (
              '✓ Correct! You selected all the right answers.'
            ) : (
              `✗ The correct answers are: ${correctAnswers.join(', ')}`
            )}
            {explanation && <p className={styles.explanation}>{explanation}</p>}
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

interface SelectProps {
  children: React.ReactNode;
}

export default function Select({ children }: SelectProps) {
  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>☑️</span>
        <span>Select All That Apply</span>
        <ActivityHelp activityType="select" />
      </div>
      <div className={styles.activityContent}>
        {children}
      </div>
    </div>
  );
}
