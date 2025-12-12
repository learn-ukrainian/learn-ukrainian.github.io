import React, { useState, useMemo } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { shuffle } from './utils';

interface TranslateItemProps {
  source: string;
  answer: string;
  alternatives?: string[];
  explanation?: string;
  options?: string[];  // For selection-based (no free typing)
}

export function TranslateItem({
  source,
  answer,
  alternatives = [],
  explanation,
  options = [],
}: TranslateItemProps) {
  const [selected, setSelected] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  // Generate options if not provided: correct answer + alternatives + distractors
  // Then shuffle so correct answer isn't always first
  const displayOptions = useMemo(() => {
    const opts = options.length > 0 ? options : [answer, ...alternatives];
    return shuffle([...opts]);
  }, [options, answer, alternatives]);

  const handleSelect = (option: string) => {
    if (submitted) return;
    setSelected(option);
    setSubmitted(true);
  };

  const handleReset = () => {
    setSelected(null);
    setSubmitted(false);
  };

  const allCorrectAnswers = [answer, ...alternatives];
  const isCorrect = selected && allCorrectAnswers.some(
    a => a.toLowerCase().trim() === selected.toLowerCase().trim()
  );

  const getOptionClass = (option: string) => {
    if (!submitted) return '';

    const isThisCorrect = allCorrectAnswers.some(
      a => a.toLowerCase().trim() === option.toLowerCase().trim()
    );
    const isSelected = selected === option;

    if (isSelected && isThisCorrect) return styles.correct;
    if (isSelected && !isThisCorrect) return styles.incorrect;
    if (!isSelected && isThisCorrect && !isCorrect) return styles.correct; // show correct if user was wrong
    return '';
  };

  return (
    <div className={styles.translateItem}>
      <div className={styles.sourceText}>
        {source}
      </div>

      <div className={styles.translateOptions}>
        {displayOptions.map((option, idx) => (
          <button
            key={idx}
            className={`${styles.translateOption} ${getOptionClass(option)}`}
            onClick={() => handleSelect(option)}
            disabled={submitted}
          >
            {option}
          </button>
        ))}
      </div>

      {submitted && (
        <>
          <div className={`${styles.feedback} ${isCorrect ? styles.feedbackCorrect : styles.feedbackIncorrect}`}>
            {isCorrect ? (
              '✓ Correct!'
            ) : (
              <>
                ✗ The correct translation is: <strong>{answer}</strong>
                {alternatives.length > 0 && (
                  <span> (also accepted: {alternatives.join(', ')})</span>
                )}
              </>
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

interface TranslateProps {
  children: React.ReactNode;
  direction?: 'to-uk' | 'to-en';
}

export default function Translate({ children, direction = 'to-uk' }: TranslateProps) {
  const title = direction === 'to-uk' ? 'Translate to Ukrainian' : 'Translate to English';
  const icon = direction === 'to-uk' ? '🇺🇦' : '🇬🇧';

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>{icon}</span>
        <span>{title}</span>
        <ActivityHelp activityType="translate" />
      </div>
      <div className={styles.activityContent}>
        {children}
      </div>
    </div>
  );
}
