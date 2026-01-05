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
  isUkrainian?: boolean;
}

export function TranslateItem({
  source,
  answer,
  alternatives = [],
  explanation,
  options = [],
  isUkrainian,
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

  const correctLabel = isUkrainian ? '✓ Правильно!' : '✓ Correct!';
  const incorrectLabel = isUkrainian ? '✗ Правильний переклад:' : '✗ The correct translation is:';
  const alsoAcceptedLabel = isUkrainian ? 'також приймається:' : 'also accepted:';
  const retryBtnLabel = isUkrainian ? 'Спробувати знову' : 'Try Again';

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
              correctLabel
            ) : (
              <>
                {incorrectLabel} <strong>{answer}</strong>
                {alternatives.length > 0 && (
                  <span> ({alsoAcceptedLabel} {alternatives.join(', ')})</span>
                )}
              </>
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

// Generator format question
interface GeneratorTranslateQuestion {
  source: string;
  options: Array<{ text: string; correct: boolean }>;
  explanation?: string;
}

interface TranslateProps {
  questions?: GeneratorTranslateQuestion[];
  direction?: 'to-uk' | 'to-en';
  children?: React.ReactNode;
  isUkrainian?: boolean;
}

export default function Translate({ questions, direction = 'to-uk', children, isUkrainian }: TranslateProps) {
  let title = direction === 'to-uk' ? 'Translate to Ukrainian' : 'Translate to English';
  if (isUkrainian) {
    title = direction === 'to-uk' ? 'Перекладіть на українську' : 'Перекладіть на англійську';
  }
  const icon = direction === 'to-uk' ? '🇺🇦' : '🇬🇧';

  // Transform generator format to TranslateItem props
  const transformedItems = useMemo(() => {
    if (!questions) return null;

    return questions.map(q => {
      // Find correct answer
      const correctOption = q.options.find(o => o.correct);
      const answer = correctOption?.text || '';

      // Get all options as string array
      const options = q.options.map(o => o.text);

      return {
        source: q.source,
        answer,
        options,
        explanation: q.explanation
      };
    });
  }, [questions]);

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>{icon}</span>
        <span>{title}</span>
        <ActivityHelp activityType="translate" isUkrainian={isUkrainian} />
      </div>
      <div className={styles.activityContent}>
        {transformedItems ? transformedItems.map((item, idx) => (
          <TranslateItem
            key={idx}
            source={item.source}
            answer={item.answer}
            options={item.options}
            explanation={item.explanation}
            isUkrainian={isUkrainian}
          />
        )) : children}
      </div>
    </div>
  );
}
