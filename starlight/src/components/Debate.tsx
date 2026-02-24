import React, { useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { parseMarkdown } from './utils';

interface Position {
  name: string;
  proponents: string;
  argument: string;
  evidence?: string[];
  weaknesses?: string[];
}

interface DebateProps {
  title: string;
  debateQuestion: string;
  historicalContext?: string;
  positions: Position[];
  analysisTasks?: string[];
  modelAnalysis?: string;
  instruction?: string;
  isUkrainian?: boolean;
}

export default function Debate({
  title,
  debateQuestion,
  historicalContext = '',
  positions = [],
  analysisTasks = [],
  modelAnalysis = '',
  instruction = '',
  isUkrainian = true
}: DebateProps) {
  const [showModel, setShowModel] = useState(false);
  const [userResponse, setUserResponse] = useState('');
  const [expandedPosition, setExpandedPosition] = useState<number | null>(null);

  const headerLabel = isUkrainian ? 'Історіографічна дискусія' : 'Historiographical Debate';
  const modelAnswerBtnLabel = isUkrainian
    ? (showModel ? 'Приховати аналіз' : 'Показати зразок аналізу')
    : (showModel ? 'Hide Analysis' : 'Show Model Analysis');

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>⚔️</span>
        <span>{title || headerLabel}</span>
        <ActivityHelp activityType="debate" isUkrainian={isUkrainian} />
      </div>
      <div className={styles.activityContent}>
        {instruction && (
          <div className={styles.essayPrompt}>
            {parseMarkdown(instruction)}
          </div>
        )}

        {/* Debate Question */}
        <div className={styles.debateQuestion}>
          <strong>{isUkrainian ? 'Дискусійне питання:' : 'Debate Question:'}</strong>
          <p className={styles.questionText}>{parseMarkdown(debateQuestion)}</p>
        </div>

        {/* Historical Context */}
        {historicalContext && (
          <div className={styles.readingContext} style={{ borderLeftColor: 'var(--ifm-color-secondary)' }}>
            <strong>{isUkrainian ? 'Історичний контекст:' : 'Historical Context:'}</strong>
            <p>{parseMarkdown(historicalContext)}</p>
          </div>
        )}

        {/* Positions */}
        <div className={styles.positionsContainer}>
          <strong>{isUkrainian ? 'Позиції в дискусії:' : 'Debate Positions:'}</strong>
          {positions.map((position, i) => (
            <div key={i} className={styles.positionCard}>
              <div
                className={styles.positionHeader}
                onClick={() => setExpandedPosition(expandedPosition === i ? null : i)}
                style={{ cursor: 'pointer' }}
              >
                <span className={styles.positionNumber}>{i + 1}</span>
                <span className={styles.positionName}>{position.name}</span>
                <span className={styles.expandIcon}>
                  {expandedPosition === i ? '▼' : '▶'}
                </span>
              </div>

              <div className={styles.positionProponents}>
                <em>{isUkrainian ? 'Представники:' : 'Proponents:'}</em> {position.proponents}
              </div>

              <div className={styles.positionArgument}>
                <strong>{isUkrainian ? 'Аргумент:' : 'Argument:'}</strong>
                <p>{parseMarkdown(position.argument)}</p>
              </div>

              {expandedPosition === i && (
                <div className={styles.positionDetails}>
                  {position.evidence && position.evidence.length > 0 && (
                    <div className={styles.positionEvidence}>
                      <strong>{isUkrainian ? 'Докази:' : 'Evidence:'}</strong>
                      <ul>
                        {position.evidence.map((e, j) => (
                          <li key={j}>{parseMarkdown(e)}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {position.weaknesses && position.weaknesses.length > 0 && (
                    <div className={styles.positionWeaknesses}>
                      <strong>{isUkrainian ? 'Критика:' : 'Weaknesses:'}</strong>
                      <ul>
                        {position.weaknesses.map((w, j) => (
                          <li key={j}>{parseMarkdown(w)}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Analysis Tasks */}
        {analysisTasks && analysisTasks.length > 0 && (
          <div className={styles.readingContext} style={{ borderLeftColor: 'var(--ifm-color-warning)' }}>
            <strong>{isUkrainian ? 'Завдання для аналізу:' : 'Analysis Tasks:'}</strong>
            <ol>
              {analysisTasks.map((task, i) => (
                <li key={i}>{parseMarkdown(task)}</li>
              ))}
            </ol>
          </div>
        )}

        {/* User Response Area */}
        <div className={styles.essayInputArea}>
          <label className={styles.inputLabel}>
            {isUkrainian ? 'Ваш аналіз дискусії:' : 'Your Debate Analysis:'}
          </label>
          <textarea
            className={styles.essayTextarea}
            value={userResponse}
            onChange={(e) => setUserResponse(e.target.value)}
            placeholder={isUkrainian
              ? 'Проаналізуйте позиції та напишіть свій висновок...'
              : 'Analyze the positions and write your conclusion...'}
            rows={10}
          />
        </div>

        {/* Show Model Button */}
        <div className={styles.buttonRow}>
          {modelAnalysis && (
            <button
              className={styles.submitButton}
              onClick={() => setShowModel(!showModel)}
            >
              {modelAnswerBtnLabel}
            </button>
          )}
        </div>

        {/* Model Analysis */}
        {showModel && modelAnalysis && (
          <div className={`${styles.feedback} ${styles.modelAnswer}`}>
            <div className={styles.collapsibleHeader}>
              {isUkrainian ? 'Зразок аналізу' : 'Model Analysis'}
            </div>
            <div className={styles.modelContent}>
              {parseMarkdown(modelAnalysis)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
