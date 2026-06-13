import React, { useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { parseMarkdown } from './utils';

interface SourceMetadata {
  /**
   * @schemaDescription Author value consumed by this component.
   * @ukrainianText false
   */
  author?: string;
  /**
   * @schemaDescription Date value consumed by this component.
   * @ukrainianText false
   */
  date?: string;
  /**
   * @schemaDescription Type value consumed by this component.
   * @ukrainianText false
   */
  type?: string;
  /**
   * @schemaDescription Context value consumed by this component.
   * @ukrainianText true
   */
  context?: string;
}

interface SourceEvaluationProps {
  /**
   * @schemaDescription Display title shown above the component.
   * @ukrainianText true
   */
  title: string;
  /**
   * @schemaDescription Source Text value consumed by this component.
   * @ukrainianText maybe
   */
  sourceText: string;
  /**
   * @schemaDescription Source Metadata value consumed by this component.
   * @ukrainianText false
   */
  sourceMetadata?: SourceMetadata;
  /**
   * @schemaDescription Evaluation Criteria value consumed by this component.
   * @ukrainianText true
   */
  evaluationCriteria?: string[];
  /**
   * @schemaDescription Guiding Questions value consumed by this component.
   * @ukrainianText true
   */
  guidingQuestions?: string[];
  /**
   * @schemaDescription Model Evaluation value consumed by this component.
   * @ukrainianText true
   */
  modelEvaluation?: string;
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
}

const CRITERIA_LABELS: Record<string, { uk: string; en: string }> = {
  authorship: { uk: 'Авторство', en: 'Authorship' },
  date_and_context: { uk: 'Дата і контекст', en: 'Date & Context' },
  intended_audience: { uk: 'Цільова аудиторія', en: 'Intended Audience' },
  purpose_and_bias: { uk: 'Мета та упередження', en: 'Purpose & Bias' },
  omissions: { uk: 'Що опущено', en: 'Omissions' },
  reliability: { uk: 'Достовірність', en: 'Reliability' },
  corroboration: { uk: 'Підтвердження', en: 'Corroboration' },
  perspective: { uk: 'Перспектива', en: 'Perspective' },
};

export default function SourceEvaluation({
  title,
  sourceText,
  sourceMetadata,
  evaluationCriteria = [],
  guidingQuestions = [],
  modelEvaluation = '',
  instruction = '',
  isUkrainian = true
}: SourceEvaluationProps) {
  const [showModel, setShowModel] = useState(false);
  const [userResponse, setUserResponse] = useState('');

  const headerLabel = isUkrainian ? 'Оцінка джерела' : 'Source Evaluation';
  const modelAnswerBtnLabel = isUkrainian
    ? (showModel ? 'Приховати аналіз' : 'Показати зразок аналізу')
    : (showModel ? 'Hide Analysis' : 'Show Model Analysis');

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>🔍</span>
        <span>{title || headerLabel}</span>
        <ActivityHelp activityType="source-evaluation" isUkrainian={isUkrainian} />
      </div>
      <div className={styles.activityContent}>
        {instruction && (
          <div className={styles.essayPrompt}>
            {parseMarkdown(instruction)}
          </div>
        )}

        {/* Source Text */}
        <div className={styles.readingContext} style={{ borderLeftColor: 'var(--ifm-color-primary)' }}>
          <strong>{isUkrainian ? 'Джерело для аналізу:' : 'Source for Analysis:'}</strong>
          <blockquote style={{ marginTop: '0.5rem', fontStyle: 'italic' }}>
            {parseMarkdown(sourceText)}
          </blockquote>
        </div>

        {/* Source Metadata */}
        {sourceMetadata && Object.keys(sourceMetadata).length > 0 && (
          <div className={styles.metadataBox}>
            <strong>{isUkrainian ? 'Відома інформація про джерело:' : 'Known Source Information:'}</strong>
            <table className={styles.metadataTable}>
              <tbody>
                {sourceMetadata.author && (
                  <tr>
                    <td><strong>{isUkrainian ? 'Автор' : 'Author'}:</strong></td>
                    <td>{sourceMetadata.author}</td>
                  </tr>
                )}
                {sourceMetadata.date && (
                  <tr>
                    <td><strong>{isUkrainian ? 'Дата' : 'Date'}:</strong></td>
                    <td>{sourceMetadata.date}</td>
                  </tr>
                )}
                {sourceMetadata.type && (
                  <tr>
                    <td><strong>{isUkrainian ? 'Тип' : 'Type'}:</strong></td>
                    <td>{sourceMetadata.type}</td>
                  </tr>
                )}
                {sourceMetadata.context && (
                  <tr>
                    <td><strong>{isUkrainian ? 'Контекст' : 'Context'}:</strong></td>
                    <td>{sourceMetadata.context}</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Evaluation Criteria */}
        {evaluationCriteria && evaluationCriteria.length > 0 && (
          <div className={styles.criteriaBox}>
            <strong>{isUkrainian ? 'Критерії для оцінки:' : 'Evaluation Criteria:'}</strong>
            <div className={styles.criteriaTags}>
              {evaluationCriteria.map((criterion, i) => (
                <span key={i} className={styles.criteriaTag}>
                  {CRITERIA_LABELS[criterion]?.[isUkrainian ? 'uk' : 'en'] || criterion}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Guiding Questions */}
        {guidingQuestions && guidingQuestions.length > 0 && (
          <div className={styles.readingContext} style={{ borderLeftColor: 'var(--ifm-color-warning)' }}>
            <strong>{isUkrainian ? 'Питання для аналізу:' : 'Guiding Questions:'}</strong>
            <ol>
              {guidingQuestions.map((q, i) => (
                <li key={i}>{parseMarkdown(q)}</li>
              ))}
            </ol>
          </div>
        )}

        {/* User Response Area */}
        <div className={styles.essayInputArea}>
          <label className={styles.inputLabel}>
            {isUkrainian ? 'Ваша оцінка джерела:' : 'Your Source Evaluation:'}
          </label>
          <textarea
            className={styles.essayTextarea}
            value={userResponse}
            onChange={(e) => setUserResponse(e.target.value)}
            placeholder={isUkrainian
              ? 'Напишіть вашу оцінку джерела тут, використовуючи критерії та питання вище...'
              : 'Write your source evaluation here, using the criteria and questions above...'}
            rows={10}
          />
        </div>

        {/* Show Model Button */}
        <div className={styles.buttonRow}>
          {modelEvaluation && (
            <button
              className={styles.submitButton}
              onClick={() => setShowModel(!showModel)}
            >
              {modelAnswerBtnLabel}
            </button>
          )}
        </div>

        {/* Model Evaluation */}
        {showModel && modelEvaluation && (
          <div className={`${styles.feedback} ${styles.modelAnswer}`}>
            <div className={styles.collapsibleHeader}>
              {isUkrainian ? 'Зразок оцінки' : 'Model Evaluation'}
            </div>
            <div className={styles.modelContent}>
              {parseMarkdown(modelEvaluation)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
