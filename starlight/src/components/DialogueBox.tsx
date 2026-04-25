import React from 'react';
import directStyles from './Direct.module.css';

interface DialogueExchange {
  /**
   * @schemaDescription Speaker value consumed by this component.
   * @ukrainianText true
   */
  speaker: string;
  /**
   * @schemaDescription Text passage shown to the learner.
   * @ukrainianText true
   */
  text: string;
  /**
   * @schemaDescription Emoji value consumed by this component.
   * @ukrainianText false
   */
  emoji?: string;
}

interface DialogueBoxProps {
  /**
   * @schemaDescription Exchanges value consumed by this component.
   * @ukrainianText true
   */
  exchanges: DialogueExchange[];
  /**
   * @schemaDescription Display title shown above the component.
   * @ukrainianText true
   */
  title?: string;
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
}

export default function DialogueBox({
  exchanges,
  title,
  isUkrainian = true,
}: DialogueBoxProps) {
  if (!exchanges || exchanges.length === 0) return null;

  const headerLabel =
    title || (isUkrainian ? 'Діалог' : 'Dialogue');

  return (
    <div className={directStyles.dialogueContainer}>
      <h3 className={directStyles.dialogueTitle}>{headerLabel}</h3>
      <div className={directStyles.dialogueExchanges}>
        {exchanges.map((ex, i) => {
          const isEven = i % 2 === 0;
          return (
            <div
              key={i}
              className={`${directStyles.dialogueBubble} ${
                isEven
                  ? directStyles.dialogueBubbleLeft
                  : directStyles.dialogueBubbleRight
              }`}
            >
              <div className={directStyles.dialogueSpeaker}>
                {ex.emoji && <span>{ex.emoji} </span>}
                {ex.speaker}
              </div>
              <div className={directStyles.dialogueText}>{ex.text}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
