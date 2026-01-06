import React, { useState, useMemo } from 'react';
import styles from './Activities.module.css';
import { parseMarkdown, shuffle } from './utils';
import ActivityHelp from './ActivityHelp';

interface QuizQuestionProps {
  question: string;
  options: string[];
  correctIndex: number;
  explanation?: string;
  isUkrainian?: boolean;
}

export function QuizQuestion({ question, options, correctIndex, explanation, isUkrainian }: QuizQuestionProps) {
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

  const correctLabel = isUkrainian ? '✓ Правильно!' : '✓ Correct!';
  const incorrectLabel = isUkrainian ? '✗ Неправильно. Відповідь:' : '✗ Incorrect. The answer is:';

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
          {isCorrect ? correctLabel : `${incorrectLabel} ${options[correctIndex]}`}
          {explanation && <p className={styles.explanation}>{explanation}</p>}
        </div>
      )}
    </div>
  );
}

interface QuizQuestionItem {
  question: string;
  options: Array<{ text: string; correct: boolean }>;
}

interface QuizProps {
  questions?: QuizQuestionItem[];
  instruction?: string;
  children?: React.ReactNode;
  isUkrainian?: boolean;
}

export default function Quiz({ questions, instruction, children, isUkrainian }: QuizProps) {
  const headerLabel = isUkrainian ? 'Тест' : 'Quiz';

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>📝</span>
        <span>{headerLabel}</span>
        <ActivityHelp activityType="quiz" isUkrainian={isUkrainian} />
      </div>
      {instruction && (
        <p className={styles.instruction}><strong>{instruction}</strong></p>
      )}
      <div className={styles.activityContent}>
        {questions ? questions.map((item, index) => {
          // Transform options format: {text, correct} -> string[] + correctIndex
          const optionTexts = item.options.map(o => o.text);
          const correctIndex = item.options.findIndex(o => o.correct);
          return (
            <QuizQuestion
              key={index}
              question={item.question}
              options={optionTexts}
              correctIndex={correctIndex >= 0 ? correctIndex : 0}
              isUkrainian={isUkrainian}
            />
          );
        }) : children}
      </div>
    </div>
  );
}
