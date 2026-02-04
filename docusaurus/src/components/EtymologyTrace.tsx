import React, { useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { parseMarkdown } from './utils';

interface EtymologyItem {
  word: string;
  modern: string;
  evolution: string;
}

interface EtymologyTraceProps {
  title: string;
  instruction?: string;
  items: EtymologyItem[];
  isUkrainian?: boolean;
}

export default function EtymologyTrace({
  title,
  instruction,
  items,
  isUkrainian = true
}: EtymologyTraceProps) {
  const [revealedItems, setRevealedItems] = useState<Set<number>>(new Set());

  const toggleReveal = (index: number) => {
    const newRevealed = new Set(revealedItems);
    if (newRevealed.has(index)) {
      newRevealed.delete(index);
    } else {
      newRevealed.add(index);
    }
    setRevealedItems(newRevealed);
  };

  const revealAll = () => {
    setRevealedItems(new Set(items.map((_, i) => i)));
  };

  const headerLabel = isUkrainian ? 'Етимологічний слід' : 'Etymology Trace';
  const showAllLabel = isUkrainian ? 'Показати всі' : 'Show All';
  const originalLabel = isUkrainian ? 'Давня форма' : 'Original';
  const modernLabel = isUkrainian ? 'Сучасна форма' : 'Modern';
  const evolutionLabel = isUkrainian ? 'Еволюція' : 'Evolution';

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>📜</span>
        <span>{title || headerLabel}</span>
        <ActivityHelp activityType="etymology-trace" isUkrainian={isUkrainian} />
      </div>
      <div className={styles.activityContent}>
        {instruction && (
          <div className={styles.readingContext}>
            {parseMarkdown(instruction)}
          </div>
        )}

        <div className={styles.etymologyList}>
          {items.map((item, index) => (
            <div key={index} className={styles.etymologyItem}>
              <div className={styles.etymologyHeader}>
                <div className={styles.etymologyWords}>
                  <span className={styles.etymologyOriginal}>
                    <strong>{originalLabel}:</strong> {item.word}
                  </span>
                  <span className={styles.etymologyArrow}>→</span>
                  <span className={styles.etymologyModern}>
                    <strong>{modernLabel}:</strong> {item.modern}
                  </span>
                </div>
                <button
                  className={styles.revealButton}
                  onClick={() => toggleReveal(index)}
                >
                  {revealedItems.has(index)
                    ? (isUkrainian ? 'Сховати' : 'Hide')
                    : (isUkrainian ? 'Пояснення' : 'Explain')}
                </button>
              </div>
              {revealedItems.has(index) && (
                <div className={styles.etymologyEvolution}>
                  <strong>{evolutionLabel}:</strong>
                  <div>{parseMarkdown(item.evolution)}</div>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className={styles.buttonRow}>
          <button className={styles.submitButton} onClick={revealAll}>
            {showAllLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
