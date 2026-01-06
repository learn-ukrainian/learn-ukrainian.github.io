import React, { useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { parseMarkdown } from './utils';

interface CriticalAnalysisProps {
  title: string;
  context: string;
  question: string;
  modelAnswer: string;
  isUkrainian?: boolean;
}

export default function CriticalAnalysis({
  title,
  context,
  question,
  modelAnswer,
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
        <div className={styles.readingContext}>
           {parseMarkdown(context)}
        </div>
        
        <div className={styles.readingContext} style={{ borderLeftColor: 'var(--ifm-color-warning)' }}>
           <strong>{isUkrainian ? 'Питання:' : 'Question:'}</strong>
           <br/>
           {parseMarkdown(question)}
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
