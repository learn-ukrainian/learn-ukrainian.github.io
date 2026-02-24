import React, { useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { parseMarkdown } from './utils';

interface EssayResponseProps {
  title: string;
  prompt: string;
  modelAnswer?: string;
  rubric?: string;
  isUkrainian?: boolean;
}

export default function EssayResponse({ 
  title, 
  prompt, 
  modelAnswer, 
  rubric, 
  isUkrainian 
}: EssayResponseProps) {
  const [response, setResponse] = useState('');
  const [showModel, setShowModel] = useState(false);
  const [showRubric, setShowRubric] = useState(false);

  const wordCount = response.trim() ? response.trim().split(/\s+/).length : 0;

  const headerLabel = isUkrainian ? 'Есе-відповідь' : 'Essay Response';
  const yourResponseLabel = isUkrainian ? 'Ваша відповідь:' : 'Your Response:';
  const wordCountLabel = isUkrainian ? 'Слів:' : 'Word count:';
  const modelAnswerBtnLabel = isUkrainian ? 
    (showModel ? 'Приховати зразок' : 'Показати зразок') : 
    (showModel ? 'Hide Model Answer' : 'Show Model Answer');
  const rubricBtnLabel = isUkrainian ? 
    (showRubric ? 'Приховати критерії' : 'Показати критерії') : 
    (showRubric ? 'Hide Rubric' : 'Show Rubric');
  const placeholderText = isUkrainian ? 'Пишіть тут...' : 'Type your essay here...';

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>✍️</span>
        <span>{title || headerLabel}</span>
        <ActivityHelp activityType="essay-response" isUkrainian={isUkrainian} />
      </div>
      <div className={styles.activityContent}>
        <div className={styles.essayPrompt}>
          {parseMarkdown(prompt)}
        </div>

        <div className={styles.essayInputArea}>
          <label className={styles.inputLabel}>{yourResponseLabel}</label>
          <textarea
            className={styles.essayTextarea}
            value={response}
            onChange={(e) => setResponse(e.target.value)}
            placeholder={placeholderText}
            rows={10}
          />
          <div className={styles.wordCounter}>
            {wordCountLabel} {wordCount}
          </div>
        </div>

        <div className={styles.buttonRow}>
          {rubric && (
            <button 
              className={styles.secondaryButton}
              onClick={() => setShowRubric(!showRubric)}
            >
              {rubricBtnLabel}
            </button>
          )}
          {modelAnswer && (
            <button 
              className={styles.submitButton}
              onClick={() => setShowModel(!showModel)}
            >
              {modelAnswerBtnLabel}
            </button>
          )}
        </div>

        {showRubric && rubric && (
          <div className={styles.rubricContainer}>
            <div className={styles.collapsibleHeader}>{isUkrainian ? 'Критерії оцінювання' : 'Rubric'}</div>
            <div className={styles.rubricContent}>
              {parseMarkdown(rubric)}
            </div>
          </div>
        )}

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
