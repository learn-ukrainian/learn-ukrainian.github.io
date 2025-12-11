import React, { useState } from 'react';
import styles from './Activities.module.css';
import { parseMarkdown } from './utils';

interface QuizQuestionProps {
  question: string;
  options: string[];
  correctIndex: number;
  explanation?: string;
}

export function QuizQuestion({ question, options, correctIndex, explanation }: QuizQuestionProps) {
  const [selected, setSelected] = useState<number | null>(null);
  const [showResult, setShowResult] = useState(false);

  const handleSelect = (index: number) => {
    if (showResult) return;
    setSelected(index);
    setShowResult(true);
  };

  const isCorrect = selected === correctIndex;

  return (
    <div className={styles.quizQuestion}>
      <p className={styles.questionText}>{parseMarkdown(question)}</p>
      <div className={styles.options}>
        {options.map((option, index) => (
          <button
            key={index}
            className={`${styles.option} ${showResult
              ? index === correctIndex
                ? styles.correct
                : index === selected
                  ? styles.incorrect
                  : ''
              : ''
              } ${selected === index ? styles.selected : ''}`}
            onClick={() => handleSelect(index)}
            disabled={showResult}
          >
            {parseMarkdown(option)}
          </button>
        ))}
      </div>
      {showResult && (
        <div className={`${styles.feedback} ${isCorrect ? styles.feedbackCorrect : styles.feedbackIncorrect}`}>
          {isCorrect ? '✓ Correct!' : `✗ Incorrect. The answer is: ${options[correctIndex]}`}
          {explanation && <p className={styles.explanation}>{explanation}</p>}
        </div>
      )}
    </div>
  );
}

interface QuizProps {
  children: React.ReactNode;
}

export default function Quiz({ children }: QuizProps) {
  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>📝</span>
        <span>Quiz</span>
      </div>
      <div className={styles.activityContent}>
        {children}
      </div>
    </div>
  );
}
