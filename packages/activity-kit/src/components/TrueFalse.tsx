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
   * Feedback for the learner's pick: `[why_if_true, why_if_false]`. The
   * entry for the correct value doubles as the explanation. Absent on every
   * existing module, which keeps the single `explanation`.
   * @schemaDescription Feedback for each true/false pick.
   * @ukrainianText true
   */
  optionWhy?: [string, string];
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
}

export function TrueFalseQuestion({ statement, isTrue, explanation, optionWhy, isUkrainian }: TrueFalseQuestionProps) {
  const [answer, setAnswer] = useState<boolean | null>(null);
  const [showResult, setShowResult] = useState(false);

  const handleAnswer = (value: boolean) => {
    if (showResult) return;
    setAnswer(value);
    setShowResult(true);
  };

  const isCorrect = answer === isTrue;
  const chosenWhy = answer !== null ? optionWhy?.[answer ? 0 : 1] : undefined;
  const correctWhy = optionWhy?.[isTrue ? 0 : 1];

  // Labels mirror the wrapper below — previously this single-statement
  // variant hardcoded English, which broke immersion when used inside
  // isUkrainian={true} modules. (#1082 review r1 blocker)
  const trueLabel = isUkrainian ? 'Правда' : 'True';
  const falseLabel = isUkrainian ? 'Неправда' : 'False';
  // Same verdict shell as Quiz (`✓ Correct!` / `✗ Incorrect` + explanation).
  const correctLabel = isUkrainian ? '✓ Правильно!' : '✓ Correct!';
  const wrongLabel = isUkrainian ? '✗ Неправильно' : '✗ Incorrect';

  return (
    <div className={styles.quizQuestion} data-activity="tf-question">
      <p className={styles.questionText}>{parseMarkdown(statement)}</p>
      <div className={styles.options} data-activity="tf-buttons">
        <button
          className={`${styles.option} ${showResult && isTrue ? styles.correct : ''
            } ${showResult && answer === true && !isTrue ? styles.incorrect : ''
            } ${answer === true ? styles.selected : ''}`}
          onClick={() => handleAnswer(true)}
          disabled={showResult}
        >
          {trueLabel}
        </button>
        <button
          className={`${styles.option} ${showResult && !isTrue ? styles.correct : ''
            } ${showResult && answer === false && isTrue ? styles.incorrect : ''
            } ${answer === false ? styles.selected : ''}`}
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
          role="status"
          aria-live="polite"
        >
          {isCorrect ? correctLabel : wrongLabel}
          {optionWhy ? (
            <>
              {chosenWhy && <p className={styles.explanation} data-activity="tf-option-why">{chosenWhy}</p>}
              {!isCorrect && correctWhy && (
                <p className={styles.explanation} data-activity="tf-correct-why">{correctWhy}</p>
              )}
            </>
          ) : (
            explanation && <p className={styles.explanation}>{explanation}</p>
          )}
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
  /**
   * Feedback for the learner's pick: `[why_if_true, why_if_false]`. Absent
   * on every existing module, which keeps the single `explanation`.
   * @schemaDescription Feedback for each true/false pick.
   * @ukrainianText true
   */
  optionWhy?: [string, string];
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
  const correctLabel = isUkrainian ? '✓ Правильно!' : '✓ Correct!';
  const wrongLabel = isUkrainian ? '✗ Неправильно' : '✗ Incorrect';
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
          const pick = selections[index];
          const chosenWhy = answered ? item.optionWhy?.[pick ? 0 : 1] : undefined;
          const correctWhy = item.optionWhy?.[item.isTrue ? 0 : 1];

          return (
            <div key={index} className={styles.quizQuestion} data-activity="tf-row">
              <p className={styles.questionText}>{parseMarkdown(item.statement)}</p>
              <div className={styles.options} data-activity="tf-buttons">
                <button
                  className={`${styles.option} ${selections[index] === true ? styles.selected : ''
                    } ${answered && item.isTrue ? styles.correct : ''} ${answered && selections[index] === true && !item.isTrue ? styles.incorrect : ''
                    }`}
                  onClick={() => handleSelect(index, true)}
                  disabled={answered}
                >
                  {trueLabel}
                </button>
                <button
                  className={`${styles.option} ${selections[index] === false ? styles.selected : ''
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
                  role="status"
                  aria-live="polite"
                >
                  {isCorrect ? correctLabel : wrongLabel}
                  {item.optionWhy ? (
                    <>
                      {chosenWhy && (
                        <p className={styles.explanation} data-activity="tf-row-option-why">{chosenWhy}</p>
                      )}
                      {!isCorrect && correctWhy && (
                        <p className={styles.explanation} data-activity="tf-row-correct-why">{correctWhy}</p>
                      )}
                    </>
                  ) : (
                    item.explanation && (
                      <p className={styles.explanation}>{item.explanation}</p>
                    )
                  )}
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
