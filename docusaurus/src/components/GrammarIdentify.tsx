import React, { useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { parseMarkdown } from './utils';

interface GrammarItem {
  text: string;
  form: string;
  answer: string;
}

interface GrammarIdentifyProps {
  title: string;
  instruction?: string;
  items: GrammarItem[];
  isUkrainian?: boolean;
}

export default function GrammarIdentify({
  title,
  instruction,
  items,
  isUkrainian = true
}: GrammarIdentifyProps) {
  const [userAnswers, setUserAnswers] = useState<string[]>(items.map(() => ''));
  const [showResults, setShowResults] = useState(false);
  const [results, setResults] = useState<boolean[]>([]);

  const headerLabel = isUkrainian ? 'Визначення граматичних форм' : 'Grammar Identification';
  const checkLabel = isUkrainian ? 'Перевірити' : 'Check';
  const showAnswersLabel = isUkrainian ? 'Показати відповіді' : 'Show Answers';
  const textLabel = isUkrainian ? 'Текст' : 'Text';
  const taskLabel = isUkrainian ? 'Визначити' : 'Identify';
  const yourAnswerLabel = isUkrainian ? 'Ваша відповідь' : 'Your answer';
  const correctAnswerLabel = isUkrainian ? 'Правильна відповідь' : 'Correct answer';

  const handleInputChange = (index: number, value: string) => {
    const newAnswers = [...userAnswers];
    newAnswers[index] = value;
    setUserAnswers(newAnswers);
    setShowResults(false);
  };

  const checkAnswers = () => {
    const newResults = items.map((item, index) => {
      const userAnswer = userAnswers[index].toLowerCase().trim();
      const correctAnswer = item.answer.toLowerCase().trim();
      // Flexible matching - check if user answer contains key parts
      return correctAnswer.includes(userAnswer) || userAnswer.includes(correctAnswer) ||
             userAnswer.split(/\s+/).some(word => correctAnswer.includes(word));
    });
    setResults(newResults);
    setShowResults(true);
  };

  const showAllAnswers = () => {
    setUserAnswers(items.map(item => item.answer));
    setResults(items.map(() => true));
    setShowResults(true);
  };

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>🔍</span>
        <span>{title || headerLabel}</span>
        <ActivityHelp activityType="grammar-identify" isUkrainian={isUkrainian} />
      </div>
      <div className={styles.activityContent}>
        {instruction && (
          <div className={styles.readingContext}>
            {parseMarkdown(instruction)}
          </div>
        )}

        <div className={styles.grammarList}>
          {items.map((item, index) => (
            <div key={index} className={styles.grammarItem}>
              <div className={styles.grammarText}>
                <strong>{textLabel}:</strong> <span className={styles.oesText}>{item.text}</span>
              </div>
              <div className={styles.grammarTask}>
                <strong>{taskLabel}:</strong> {item.form}
              </div>
              <div className={styles.grammarInput}>
                <input
                  type="text"
                  value={userAnswers[index]}
                  onChange={(e) => handleInputChange(index, e.target.value)}
                  placeholder={yourAnswerLabel}
                  className={showResults ? (results[index] ? styles.correct : styles.incorrect) : ''}
                />
                {showResults && !results[index] && (
                  <div className={styles.correctAnswer}>
                    <strong>{correctAnswerLabel}:</strong> {item.answer}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className={styles.buttonRow}>
          <button className={styles.submitButton} onClick={checkAnswers}>
            {checkLabel}
          </button>
          <button className={styles.secondaryButton} onClick={showAllAnswers}>
            {showAnswersLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
