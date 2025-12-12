import React, { useState, useMemo } from 'react';
import styles from './Activities.module.css';
import { parseMarkdown, shuffle } from './utils';
import ActivityHelp from './ActivityHelp';

interface QuizQuestionProps {
  question: string;
  options: string[];
  correctIndex: number;
  explanation?: string;
}

export function QuizQuestion({ question, options, correctIndex, explanation }: QuizQuestionProps) {
  // Shuffle options on mount, tracking original indices
  const shuffledOptions = useMemo(() => {
    const indexed = options.map((opt, i) => ({ opt, originalIndex: i }));
    return shuffle(indexed);
  }, [options]);

  const [selected, setSelected] = useState<number | null>(null);
  const [showResult, setShowResult] = useState(false);

  const handleSelect = (shuffledIndex: number) => {
    if (showResult) return;
    setSelected(shuffledIndex);
    setShowResult(true);
  };

  // Find the shuffled index of the correct answer
  const correctShuffledIndex = shuffledOptions.findIndex(o => o.originalIndex === correctIndex);
  const isCorrect = selected === correctShuffledIndex;

  return (
    <div className={styles.quizQuestion}>
      <p className={styles.questionText}>{parseMarkdown(question)}</p>
      <div className={styles.options}>
        {shuffledOptions.map((item, index) => (
          <button
            key={index}
            className={`${styles.option} ${showResult
              ? index === correctShuffledIndex
                ? styles.correct
                : index === selected
                  ? styles.incorrect
                  : ''
              : ''
              } ${selected === index ? styles.selected : ''}`}
            onClick={() => handleSelect(index)}
            disabled={showResult}
          >
            {parseMarkdown(item.opt)}
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
        <ActivityHelp activityType="quiz" />
      </div>
      <div className={styles.activityContent}>
        {children}
      </div>
    </div>
  );
}
