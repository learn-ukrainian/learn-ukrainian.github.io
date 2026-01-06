import React, { useState } from 'react';
import styles from './Activities.module.css';
import { parseMarkdown } from './utils';
import ActivityHelp from './ActivityHelp';

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

interface TrueFalseItem {
  statement: string;
  isTrue: boolean;
  explanation?: string;
}

interface TrueFalseProps {
  items: TrueFalseItem[];
  instruction?: string;
  isUkrainian?: boolean;
}

export default function TrueFalse({ items, instruction, isUkrainian }: TrueFalseProps) {
  const [selections, setSelections] = useState<Record<number, boolean>>({});
  const [showResults, setShowResults] = useState(false);

  const handleSelect = (index: number, value: boolean) => {
    if (showResults) return;
    setSelections({ ...selections, [index]: value });
  };

  const headerLabel = isUkrainian ? 'Правда чи хибність' : 'True or False';
  const trueLabel = isUkrainian ? 'Правда' : 'True';
  const falseLabel = isUkrainian ? 'Хибність' : 'False';
  const checkBtnLabel = isUkrainian ? 'Перевірити' : 'Check Answers';
  const retryBtnLabel = isUkrainian ? 'Спробувати знову' : 'Try Again';

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>⚖️</span>
        <span>{headerLabel}</span>
        <ActivityHelp activityType="true-false" isUkrainian={isUkrainian} />
      </div>
      {instruction && (
        <p className={styles.instruction}><strong>{instruction}</strong></p>
      )}
      <div className={styles.activityContent}>
        {items.map((item, index) => {
          const isCorrect = selections[index] === item.isTrue;

          return (
            <div key={index} className={styles.trueFalseRow}>
              <p className={styles.statementText}>{parseMarkdown(item.statement)}</p>
              <div className={styles.trueFalseButtons}>
                <button
                  className={`${styles.tfButton} ${selections[index] === true ? styles.selected : ''
                    } ${showResults && item.isTrue ? styles.correct : ''} ${showResults && selections[index] === true && !item.isTrue ? styles.incorrect : ''
                    }`}
                  onClick={() => handleSelect(index, true)}
                  disabled={showResults}
                >
                  {trueLabel}
                </button>
                <button
                  className={`${styles.tfButton} ${selections[index] === false ? styles.selected : ''
                    } ${showResults && !item.isTrue ? styles.correct : ''} ${showResults && selections[index] === false && item.isTrue ? styles.incorrect : ''
                    }`}
                  onClick={() => handleSelect(index, false)}
                  disabled={showResults}
                >
                  {falseLabel}
                </button>
              </div>
              {showResults && (
                <div className={`${styles.feedback} ${isCorrect ? styles.feedbackCorrect : styles.feedbackIncorrect}`}>
                  {isCorrect ? '✓' : '✗'} {item.explanation}
                </div>
              )}
            </div>
          );
        })}

        <div className={styles.controls}>
          {!showResults ? (
            <button
              className={styles.checkButton}
              onClick={() => setShowResults(true)}
              disabled={Object.keys(selections).length === 0}
            >
              {checkBtnLabel}
            </button>
          ) : (
            <button
              className={styles.retryButton}
              onClick={() => {
                setShowResults(false);
                setSelections({});
              }}
            >
              {retryBtnLabel}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
