import React, { useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { parseMarkdown } from './utils';

interface ComparativeStudyProps {
  title: string;
  content: string; // The comparison table or text
  task: string;
  modelAnswer?: string;
  isUkrainian?: boolean;
}

export default function ComparativeStudy({ 
  title, 
  content, 
  task, 
  modelAnswer, 
  isUkrainian 
}: ComparativeStudyProps) {
  const [response, setResponse] = useState('');
  const [showModel, setShowModel] = useState(false);

  const headerLabel = isUkrainian ? 'Порівняльний аналіз' : 'Comparative Study';
  const analysisLabel = isUkrainian ? 'Ваш аналіз:' : 'Your Analysis:';
  const modelAnswerBtnLabel = isUkrainian ? 
    (showModel ? 'Приховати зразок' : 'Показати зразок') : 
    (showModel ? 'Hide Model Answer' : 'Show Model Answer');
  const placeholderText = isUkrainian ? 'Напишіть свій аналіз тут...' : 'Type your analysis here...';

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>⚖️</span>
        <span>{title || headerLabel}</span>
        <ActivityHelp activityType="comparative-study" isUkrainian={isUkrainian} />
      </div>
      <div className={styles.activityContent}>
        <div className={styles.comparisonContent}>
          {parseMarkdown(content)}
        </div>

        <div className={styles.essayPrompt}>
          <strong>{isUkrainian ? 'Завдання:' : 'Task:'}</strong> {parseMarkdown(task)}
        </div>

        <div className={styles.essayInputArea}>
          <label className={styles.inputLabel}>{analysisLabel}</label>
          <textarea
            className={styles.essayTextarea}
            value={response}
            onChange={(e) => setResponse(e.target.value)}
            placeholder={placeholderText}
            rows={8}
          />
        </div>

        <div className={styles.buttonRow}>
          {modelAnswer && (
            <button 
              className={styles.submitButton}
              onClick={() => setShowModel(!showModel)}
            >
              {modelAnswerBtnLabel}
            </button>
          )}
        </div>

        {showModel && modelAnswer && (
          <div className={`${styles.feedback} ${styles.modelAnswer}`}>
            <div className={styles.collapsibleHeader}>{isUkrainian ? 'Зразок відповіді' : 'Model Answer'}</div>
            <div className={styles.modelContent}>
              {parseMarkdown(modelAnswer)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
