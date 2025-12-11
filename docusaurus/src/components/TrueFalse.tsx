import React, { useState } from 'react';
import styles from './Activities.module.css';
import { parseMarkdown } from './utils';

interface TrueFalseQuestionProps {
  statement: string;
  isTrue: boolean;
  explanation?: string;
}

export function TrueFalseQuestion({ statement, isTrue, explanation }: TrueFalseQuestionProps) {
  const [answer, setAnswer] = useState<boolean | null>(null);
  const [showResult, setShowResult] = useState(false);

  const handleAnswer = (value: boolean) => {
    if (showResult) return;
    setAnswer(value);
    setShowResult(true);
  };

  const isCorrect = answer === isTrue;

  return (
    <div className={styles.trueFalseQuestion}>
      <p className={styles.statementText}>{parseMarkdown(statement)}</p>
      <div className={styles.trueFalseButtons}>
        <button
          className={`${styles.tfButton} ${styles.trueButton} ${showResult && isTrue ? styles.correct : ''
            } ${showResult && answer === true && !isTrue ? styles.incorrect : ''}`}
          onClick={() => handleAnswer(true)}
          disabled={showResult}
        >
          True
        </button>
        <button
          className={`${styles.tfButton} ${styles.falseButton} ${showResult && !isTrue ? styles.correct : ''
            } ${showResult && answer === false && isTrue ? styles.incorrect : ''}`}
          onClick={() => handleAnswer(false)}
          disabled={showResult}
        >
          False
        </button>
      </div>
      {showResult && (
        <div className={`${styles.feedback} ${isCorrect ? styles.feedbackCorrect : styles.feedbackIncorrect}`}>
          {isCorrect ? '✓ Correct!' : `✗ The statement is ${isTrue ? 'true' : 'false'}.`}
          {explanation && <p className={styles.explanation}>{explanation}</p>}
        </div>
      )}
    </div>
  );
}

interface TrueFalseProps {
  children: React.ReactNode;
}

export default function TrueFalse({ children }: TrueFalseProps) {
  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>✓✗</span>
        <span>True or False</span>
      </div>
      <div className={styles.activityContent}>
        {children}
      </div>
    </div>
  );
}
