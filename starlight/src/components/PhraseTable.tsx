import React from 'react';
import directStyles from './Direct.module.css';

interface Phrase {
  phrase: string;
  context?: string;
  emoji?: string;
}

interface PhraseGroup {
  function: string;
  phrases: Phrase[];
}

interface PhraseTableProps {
  groups: PhraseGroup[];
  title?: string;
  isUkrainian?: boolean;
}

export default function PhraseTable({
  groups,
  title,
  isUkrainian = true,
}: PhraseTableProps) {
  if (!groups || groups.length === 0) return null;

  const headerLabel =
    title || (isUkrainian ? 'Фрази' : 'Phrases');

  return (
    <div className={directStyles.phraseTableContainer}>
      <h3 className={directStyles.phraseTableTitle}>{headerLabel}</h3>
      {groups.map((group) => (
        <div key={group.function} className={directStyles.phraseGroup}>
          <h4 className={directStyles.phraseGroupLabel}>{group.function}</h4>
          <div className={directStyles.phraseList}>
            {group.phrases.map((p, i) => (
              <div key={i} className={directStyles.phraseItem}>
                {p.emoji && (
                  <span className={directStyles.phraseEmoji}>{p.emoji}</span>
                )}
                <span className={directStyles.phraseText}>{p.phrase}</span>
                {p.context && (
                  <span className={directStyles.phraseContext}>
                    {p.context}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
