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
  exchanges?: DialogueExchange[];
  /**
   * @schemaDescription Legacy Ukrainian line consumed by generated MDX.
   * @ukrainianText true
   */
  uk?: string;
  /**
   * @schemaDescription Legacy English gloss consumed by generated MDX.
   * @ukrainianText false
   */
  en?: string;
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
  uk,
  en,
  title,
  isUkrainian = true,
}: DialogueBoxProps) {
  const usesLegacyLine = (!exchanges || exchanges.length === 0) && Boolean(uk);
  const normalizedExchanges = exchanges && exchanges.length > 0
    ? exchanges
    : uk
      ? [legacyLineToExchange(uk)]
      : [];

  if (normalizedExchanges.length === 0) return null;

  const headerLabel =
    title || (isUkrainian ? 'Діалог' : 'Dialogue');

  return (
    <div className={directStyles.dialogueContainer}>
      {!usesLegacyLine && <h3 className={directStyles.dialogueTitle}>{headerLabel}</h3>}
      <div className={directStyles.dialogueExchanges}>
        {normalizedExchanges.map((ex, i) => {
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
              {en && <div className={directStyles.dialogueTranslation}>{en}</div>}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function legacyLineToExchange(line: string): DialogueExchange {
  const [speaker, ...rest] = line.split(':');
  const text = rest.join(':').trim();
  if (!text) {
    return { speaker: '', text: line };
  }
  return { speaker: speaker.trim(), text };
}
