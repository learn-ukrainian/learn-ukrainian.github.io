import React, { useState, useMemo } from 'react';
import styles from './Activities.module.css';
import directStyles from './Direct.module.css';
import { shuffle } from './utils';

interface ImageToLetterItem {
  emoji: string;
  answer: string;
  distractors: string[];
  note?: string;
}

interface ImageToLetterProps {
  items: ImageToLetterItem[];
  title?: string;
  isUkrainian?: boolean;
}

export default function ImageToLetter({
  items,
  title,
  isUkrainian = true,
}: ImageToLetterProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [wrongCount, setWrongCount] = useState(0);
  const [showHint, setShowHint] = useState(false);
  const [answered, setAnswered] = useState(false);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [completedCount, setCompletedCount] = useState(0);

  if (!items || items.length === 0) return null;

  const item = items[currentIndex];
  const total = items.length;
  const isComplete = completedCount >= total;

  // Shuffle options for each item
  const options = useMemo(() => {
    return shuffle([item.answer, ...item.distractors]);
  }, [currentIndex, item.answer, item.distractors]);

  const headerLabel =
    title || (isUkrainian ? 'Яка перша буква?' : 'Which first letter?');
  const doneLabel = isUkrainian ? 'Вправу завершено!' : 'Exercise complete!';

  const handleOptionClick = (option: string) => {
    if (answered) return;

    setSelectedAnswer(option);

    if (option === item.answer) {
      setAnswered(true);
      setCompletedCount((c) => c + 1);
      // Auto-advance after 1s
      setTimeout(() => {
        if (currentIndex < total - 1) {
          setCurrentIndex((i) => i + 1);
          setAnswered(false);
          setSelectedAnswer(null);
          setWrongCount(0);
          setShowHint(false);
        }
      }, 1000);
    } else {
      const newWrong = wrongCount + 1;
      setWrongCount(newWrong);
      if (newWrong >= 2) {
        setShowHint(true);
      }
      // Clear wrong selection after shake animation
      setTimeout(() => setSelectedAnswer(null), 400);
    }
  };

  if (isComplete) {
    return (
      <div className={styles.activityContainer}>
        <div className={styles.activityHeader}>
          <span className={styles.activityIcon}>🖼️</span>
          <span>{headerLabel}</span>
        </div>
        <div
          className={`${styles.feedback} ${styles.feedbackCorrect}`}
          style={{ textAlign: 'center' }}
        >
          {doneLabel} ✓
        </div>
      </div>
    );
  }

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>🖼️</span>
        <span>{headerLabel}</span>
      </div>

      {/* Progress bar */}
      <div className={directStyles.warProgress}>
        <span>
          {completedCount + 1} / {total}
        </span>
        <div className={directStyles.warProgressBar}>
          <div
            className={directStyles.warProgressFill}
            style={{ width: `${(completedCount / total) * 100}%` }}
          />
        </div>
      </div>

      <div className={directStyles.itlCard}>
        {/* Large emoji */}
        <div className={directStyles.itlEmoji}>{item.emoji}</div>

        {/* Hint: show the correct answer highlighted */}
        {showHint && (
          <div className={directStyles.itlHint}>
            {isUkrainian ? 'Підказка: ' : 'Hint: '}
            <strong>{item.answer}</strong>
          </div>
        )}

        {/* Letter options */}
        <div className={directStyles.itlOptions}>
          {options.map((option) => {
            let className = directStyles.itlOption;
            if (answered && option === item.answer) {
              className += ` ${directStyles.itlOptionCorrect}`;
            } else if (selectedAnswer === option && option !== item.answer) {
              className += ` ${directStyles.itlOptionWrong}`;
            }

            return (
              <button
                key={option}
                className={className}
                onClick={() => handleOptionClick(option)}
                disabled={answered}
              >
                {option}
              </button>
            );
          })}
        </div>

        {/* Note shown after correct answer */}
        {answered && item.note && (
          <p className={directStyles.warNote}>{item.note}</p>
        )}
      </div>
    </div>
  );
}
