import React, { useRef, useState } from 'react';
import styles from './Activities.module.css';
import { parseMarkdown } from './utils';
import ActivityHelp from './ActivityHelp';

export interface TrueFalseQuestionProps {
  /**
   * @schemaDescription Statement the learner marks true or false.
   * @ukrainianText true
   */
  statement: string;
  /**
   * @schemaDescription Is True value consumed by this component.
   * @ukrainianText false
   */
  isTrue: boolean;
  /**
   * @schemaDescription Feedback explanation shown after the learner answers.
   * @ukrainianText true
   */
  explanation?: string;
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
}

export function TrueFalseQuestion({ statement, isTrue, explanation, isUkrainian }: TrueFalseQuestionProps) {
  const [answer, setAnswer] = useState<boolean | null>(null);
  const [showResult, setShowResult] = useState(false);

  const handleAnswer = (value: boolean) => {
    if (showResult) return;
    setAnswer(value);
    setShowResult(true);
  };

  const isCorrect = answer === isTrue;

  // Labels mirror the wrapper below — previously this single-statement
  // variant hardcoded English, which broke immersion when used inside
  // isUkrainian={true} modules. (#1082 review r1 blocker)
  const trueLabel = isUkrainian ? 'Правда' : 'True';
  const falseLabel = isUkrainian ? 'Неправда' : 'False';
  const correctLabel = isUkrainian ? '✓ Правильно!' : '✓ Correct!';
  const wrongLabel = isUkrainian
    ? `✗ Це твердження ${isTrue ? 'правдиве' : 'хибне'}.`
    : `✗ The statement is ${isTrue ? 'true' : 'false'}.`;

  return (
    <div className={styles.trueFalseQuestion} data-activity="tf-question">
      <p className={styles.statementText}>{parseMarkdown(statement)}</p>
      <div className={styles.trueFalseButtons} data-activity="tf-buttons">
        <button
          className={`${styles.tfButton} ${styles.trueButton} ${showResult && isTrue ? styles.correct : ''
            } ${showResult && answer === true && !isTrue ? styles.incorrect : ''}`}
          onClick={() => handleAnswer(true)}
          disabled={showResult}
        >
          {trueLabel}
        </button>
        <button
          className={`${styles.tfButton} ${styles.falseButton} ${showResult && !isTrue ? styles.correct : ''
            } ${showResult && answer === false && isTrue ? styles.incorrect : ''}`}
          onClick={() => handleAnswer(false)}
          disabled={showResult}
        >
          {falseLabel}
        </button>
      </div>
      {showResult && (
        <div
          className={`${styles.feedback} ${isCorrect ? styles.feedbackCorrect : styles.feedbackIncorrect}`}
          data-activity="tf-feedback"
          data-correct={isCorrect ? 'true' : 'false'}
        >
          {isCorrect ? correctLabel : wrongLabel}
          {explanation && <p className={styles.explanation}>{explanation}</p>}
        </div>
      )}
    </div>
  );
}

export interface TrueFalseItem {
  /**
   * @schemaDescription Statement the learner marks true or false.
   * @ukrainianText true
   */
  statement: string;
  /**
   * @schemaDescription Is True value consumed by this component.
   * @ukrainianText false
   */
  isTrue: boolean;
  /**
   * @schemaDescription Feedback explanation shown after the learner answers.
   * @ukrainianText true
   */
  explanation?: string;
}

export interface TrueFalseProps {
  /**
   * @schemaDescription Array of activity items rendered by the component.
   * @ukrainianText true
   */
  items: TrueFalseItem[];
  /**
   * @schemaDescription Instruction shown to the learner above the activity.
   * @ukrainianText true
   */
  instruction?: string;
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
  onComplete?: () => void;
}

export default function TrueFalse({ items, instruction, isUkrainian, onComplete }: TrueFalseProps) {
  const [selections, setSelections] = useState<Record<number, boolean>>({});
  const completedRef = useRef(false);

  // Each row shows its own result on the click, like the single-statement
  // component. A row locks once answered; other rows stay untouched.
  const handleSelect = (index: number, value: boolean) => {
    if (index in selections) return;
    const next = { ...selections, [index]: value };
    setSelections(next);
    if (!completedRef.current && Object.keys(next).length === items.length) {
      completedRef.current = true;
      onComplete?.();
    }
  };

  const headerLabel = isUkrainian ? 'Правда чи хибність' : 'True or False';
  const trueLabel = isUkrainian ? 'Правда' : 'True';
  const falseLabel = isUkrainian ? 'Неправда' : 'False';
  const retryBtnLabel = isUkrainian ? 'Спробувати знову' : 'Try Again';
  const anyAnswered = Object.keys(selections).length > 0;

  return (
    <div className={styles.activityContainer} data-activity="true-false">
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
          const answered = index in selections;
          const isCorrect = selections[index] === item.isTrue;

          return (
            <div key={index} className={styles.trueFalseRow} data-activity="tf-row">
              <p className={styles.statementText}>{parseMarkdown(item.statement)}</p>
              <div className={styles.trueFalseButtons}>
                <button
                  className={`${styles.tfButton} ${selections[index] === true ? styles.selected : ''
                    } ${answered && item.isTrue ? styles.correct : ''} ${answered && selections[index] === true && !item.isTrue ? styles.incorrect : ''
                    }`}
                  onClick={() => handleSelect(index, true)}
                  disabled={answered}
                >
                  {trueLabel}
                </button>
                <button
                  className={`${styles.tfButton} ${selections[index] === false ? styles.selected : ''
                    } ${answered && !item.isTrue ? styles.correct : ''} ${answered && selections[index] === false && item.isTrue ? styles.incorrect : ''
                    }`}
                  onClick={() => handleSelect(index, false)}
                  disabled={answered}
                >
                  {falseLabel}
                </button>
              </div>
              {answered && (
                <div
                  className={`${styles.feedback} ${isCorrect ? styles.feedbackCorrect : styles.feedbackIncorrect}`}
                  data-activity="tf-row-feedback"
                  data-correct={isCorrect ? 'true' : 'false'}
                >
                  {isCorrect ? '✓' : '✗'} {item.explanation}
                </div>
              )}
            </div>
          );
        })}

        {anyAnswered && (
          <div className={styles.controls}>
            <button
              className={styles.retryButton}
              onClick={() => {
                completedRef.current = false;
                setSelections({});
              }}
            >
              {retryBtnLabel}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
