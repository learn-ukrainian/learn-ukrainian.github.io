import React, { useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { parseMarkdown } from './utils';

interface CriticalAnalysisProps {
  /**
   * @schemaDescription Display title shown above the component.
   * @ukrainianText true
   */
  title: string;
  /**
   * @schemaDescription Context value consumed by this component.
   * @ukrainianText true
   */
  context?: string;
  /**
   * @schemaDescription Question value consumed by this component.
   * @ukrainianText true
   */
  question?: string;
  /**
   * @schemaDescription Model answer for review or self-check.
   * @ukrainianText true
   */
  modelAnswer?: string;
  // Seminar mode fields
  /**
   * @schemaDescription Target Text value consumed by this component.
   * @ukrainianText true
   */
  targetText?: string;
  /**
   * @schemaDescription Array of questions rendered by the component.
   * @ukrainianText true
   */
  questions?: string[];
  /**
   * @schemaDescription Model answers for review or self-check.
   * @ukrainianText true
   */
  modelAnswers?: string[];
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
}

export default function CriticalAnalysis({
  title,
  context = '',
  question = '',
  modelAnswer = '',
  targetText = '',
  questions = [],
  modelAnswers = [],
  isUkrainian
}: CriticalAnalysisProps) {
  const [showModel, setShowModel] = useState(false);

  const headerLabel = isUkrainian ? 'Критичний аналіз' : 'Critical Analysis';
  const modelAnswerBtnLabel = isUkrainian ?
    (showModel ? 'Приховати аналіз' : 'Показати аналіз') :
    (showModel ? 'Hide Analysis' : 'Show Analysis');

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>🧐</span>
        <span>{title || headerLabel}</span>
        <ActivityHelp activityType="critical-analysis" isUkrainian={isUkrainian} />
      </div>
      <div className={styles.activityContent}>
        {/* Show targetText (seminar) or context (legacy) */}
        {(targetText || context) && (
          <div className={styles.readingContext}>
            {parseMarkdown(targetText || context)}
          </div>
        )}

        {/* Seminar mode: multiple questions */}
        {questions && questions.length > 0 ? (
          <div className={styles.readingContext} style={{ borderLeftColor: 'var(--ifm-color-warning)' }}>
            <strong>{isUkrainian ? 'Питання для аналізу:' : 'Questions for Analysis:'}</strong>
            <ol>
              {questions.map((q, i) => (
                <li key={i}>{parseMarkdown(q)}</li>
              ))}
            </ol>
          </div>
        ) : question && (
          <div className={styles.readingContext} style={{ borderLeftColor: 'var(--ifm-color-warning)' }}>
            <strong>{isUkrainian ? 'Питання:' : 'Question:'}</strong>
            <br/>
            {parseMarkdown(question)}
          </div>
        )}

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
               {/* Seminar mode: multiple model answers */}
               {modelAnswers && modelAnswers.length > 0 ? (
                 <ol>
                   {modelAnswers.map((a, i) => (
                     <li key={i}>{parseMarkdown(a)}</li>
                   ))}
                 </ol>
               ) : (
                 parseMarkdown(modelAnswer)
               )}
             </div>
          </div>
        )}
      </div>
    </div>
  );
}
