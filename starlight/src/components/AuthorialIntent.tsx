import React, { useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { parseMarkdown } from './utils';

interface AuthorialIntentProps {
  /**
   * @schemaDescription Display title shown above the component.
   * @ukrainianText true
   */
  title: string;
  /**
   * @schemaDescription Excerpt value consumed by this component.
   * @ukrainianText true
   */
  excerpt: string;
  /**
   * @schemaDescription Array of questions rendered by the component.
   * @ukrainianText true
   */
  questions: string[];
  /**
   * @schemaDescription Model answer for review or self-check.
   * @ukrainianText true
   */
  modelAnswer: string;
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
}

export default function AuthorialIntent({
  title,
  excerpt,
  questions,
  modelAnswer,
  isUkrainian
}: AuthorialIntentProps) {
  const [showModel, setShowModel] = useState(false);

  const headerLabel = isUkrainian ? 'Авторський задум' : 'Authorial Intent';
  const modelAnswerBtnLabel = isUkrainian ?
    (showModel ? 'Приховати розбір' : 'Показати розбір') :
    (showModel ? 'Hide Analysis' : 'Show Analysis');

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>🖋️</span>
        <span>{title || headerLabel}</span>
        <ActivityHelp activityType="authorial-intent" isUkrainian={isUkrainian} />
      </div>
      <div className={styles.activityContent}>
        <div className={styles.readingContext}>
           {parseMarkdown(excerpt)}
        </div>
        
        <div className={styles.readingTasks}>
           <strong>{isUkrainian ? 'Питання:' : 'Questions:'}</strong>
           <ul className={styles.taskList}>
             {questions.map((q, i) => (
               <li key={i} className={styles.taskItem}>{parseMarkdown(q)}</li>
             ))}
           </ul>
        </div>

        <div className={styles.buttonRow}>
            <button
              className={styles.submitButton}
              onClick={() => setShowModel(!showModel)}
            >
              {modelAnswerBtnLabel}
            </button>
        </div>

        {showModel && (
          <div className={`${styles.feedback} ${styles.modelAnswer}`}>
             <div className={styles.modelContent}>
               {parseMarkdown(modelAnswer)}
             </div>
          </div>
        )}
      </div>
    </div>
  );
}
