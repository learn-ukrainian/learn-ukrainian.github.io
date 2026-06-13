import React, { useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { parseMarkdown } from './utils';

interface PerformanceActivityProps {
  /**
   * @schemaDescription Display title shown above the component.
   * @ukrainianText true
   */
  title: string;
  /**
   * @schemaDescription Instruction shown to the learner above the activity.
   * @ukrainianText true
   */
  instruction?: string;
  /**
   * @schemaDescription Prompt shown to guide the learner performance.
   * @ukrainianText true
   */
  prompt: string;
  /**
   * @schemaDescription Fragment to recite, chant, or perform.
   * @ukrainianText true
   */
  fragment?: string;
  /**
   * @schemaDescription Self-check criteria for the learner.
   * @ukrainianText true
   */
  selfCheck?: string[];
  /**
   * @schemaDescription Whether to display the record-style action button.
   * @ukrainianText false
   */
  showRecordButton?: boolean;
  /**
   * @schemaDescription Model answer for review or self-check.
   * @ukrainianText true
   */
  modelAnswer?: string;
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
}

export default function PerformanceActivity({
  title,
  instruction,
  prompt,
  fragment,
  selfCheck = [],
  showRecordButton = true,
  modelAnswer,
  isUkrainian
}: PerformanceActivityProps) {
  const [checked, setChecked] = useState<Set<number>>(new Set());
  const [recordMarked, setRecordMarked] = useState(false);
  const [showModel, setShowModel] = useState(false);

  const headerLabel = isUkrainian ? 'Виконання' : 'Performance';
  const fragmentLabel = isUkrainian ? 'Фрагмент:' : 'Fragment:';
  const selfCheckLabel = isUkrainian ? 'Самоперевірка' : 'Self-check';
  const recordLabel = isUkrainian ? 'Записати виконання' : 'Record performance';
  const markedLabel = isUkrainian ? 'Позначено для самоперевірки' : 'Marked for self-check';
  const modelLabel = isUkrainian ? (showModel ? 'Приховати зразок' : 'Показати зразок') : (showModel ? 'Hide model' : 'Show model');

  const toggleCheck = (index: number) => {
    setChecked(prev => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={`${styles.exerciseBadge} ${styles.badgePerform}`}>#45</span>
        <span>{title || headerLabel}</span>
        <ActivityHelp activityType="performance" isUkrainian={isUkrainian} />
      </div>
      <div className={styles.activityContent}>
        {instruction && <p className={styles.instruction}><strong>{instruction}</strong></p>}

        <div className={styles.essayPrompt}>{parseMarkdown(prompt)}</div>

        {fragment && (
          <div className={styles.performanceFragment}>
            <strong>{fragmentLabel}</strong>
            <blockquote>{parseMarkdown(fragment)}</blockquote>
          </div>
        )}

        {showRecordButton && (
          <button className={styles.recButton} type="button" onClick={() => setRecordMarked(!recordMarked)}>
            <span aria-hidden="true">&#x25CF;</span>
            {recordMarked ? markedLabel : recordLabel}
          </button>
        )}

        {selfCheck.length > 0 && (
          <div className={styles.performanceChecklist}>
            <div className={styles.inputLabel}>{selfCheckLabel}</div>
            {selfCheck.map((item, index) => (
              <label key={`${item}-${index}`} className={styles.performanceCheckItem}>
                <input
                  type="checkbox"
                  checked={checked.has(index)}
                  onChange={() => toggleCheck(index)}
                />
                <span>{item}</span>
              </label>
            ))}
          </div>
        )}

        {modelAnswer && (
          <div className={styles.buttonRow}>
            <button className={styles.submitButton} onClick={() => setShowModel(!showModel)}>
              {modelLabel}
            </button>
          </div>
        )}

        {showModel && modelAnswer && (
          <div className={`${styles.feedback} ${styles.modelAnswer}`}>
            {parseMarkdown(modelAnswer)}
          </div>
        )}
      </div>
    </div>
  );
}
