import React, { useState, useMemo, useCallback } from 'react';
import styles from './Activities.module.css';
import directStyles from './Direct.module.css';
import { shuffle } from './utils';

interface ClassifyCategory {
  /**
   * @schemaDescription Short label for a UI or source item.
   * @ukrainianText true
   */
  label: string;
  /**
   * @schemaDescription Symbol Hint value consumed by this component.
   * @ukrainianText true
   */
  symbolHint?: string;
  /**
   * @schemaDescription Array of activity items rendered by the component.
   * @ukrainianText true
   */
  items: string[];
}

/**
 * @deprecated Deprecated; subsumed by group-sort.
 */
interface ClassifyProps {
  /**
   * @schemaDescription Categories value consumed by this component.
   * @ukrainianText true
   */
  categories: ClassifyCategory[];
  /**
   * @schemaDescription Display title shown above the component.
   * @ukrainianText true
   */
  title?: string;
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

export default function Classify({
  categories,
  title,
  instruction,
  isUkrainian = true,
}: ClassifyProps) {
  // Build correct answer map: item -> category label
  const answerMap = useMemo(() => {
    const map: Record<string, string> = {};
    for (const cat of categories) {
      for (const item of cat.items) {
        map[item] = cat.label;
      }
    }
    return map;
  }, [categories]);

  // All items shuffled
  const allItems = useMemo(() => {
    const items = categories.flatMap((c) => c.items);
    return shuffle(items);
  }, [categories]);

  // Track which items are placed and in which bin
  const [placed, setPlaced] = useState<Record<string, string>>({});
  // Track feedback flash per item: item -> 'correct' | 'incorrect'
  const [feedback, setFeedback] = useState<Record<string, string>>({});
  // Selected item (for tap-to-place on mobile)
  const [selected, setSelected] = useState<string | null>(null);

  const remaining = allItems.filter((item) => !placed[item]);
  const isComplete = remaining.length === 0;

  const correctCount = Object.entries(placed).filter(
    ([item, label]) => answerMap[item] === label
  ).length;

  const headerLabel =
    title || (isUkrainian ? 'Розподіли' : 'Classify');
  const doneLabel = isUkrainian ? 'Готово!' : 'Done!';
  const scoreLabel = isUkrainian ? 'Правильно' : 'Correct';

  const handleDrop = useCallback(
    (categoryLabel: string, item: string) => {
      const isCorrect = answerMap[item] === categoryLabel;
      if (isCorrect) {
        setPlaced((prev) => ({ ...prev, [item]: categoryLabel }));
        setFeedback((prev) => ({ ...prev, [item]: 'correct' }));
      } else {
        setFeedback((prev) => ({ ...prev, [item]: 'incorrect' }));
        // Clear incorrect feedback after animation
        setTimeout(() => {
          setFeedback((prev) => {
            const next = { ...prev };
            delete next[item];
            return next;
          });
        }, 600);
      }
      setSelected(null);
    },
    [answerMap]
  );

  const handleItemClick = (item: string) => {
    if (placed[item]) return;
    setSelected(selected === item ? null : item);
  };

  const handleBinClick = (categoryLabel: string) => {
    if (selected && !placed[selected]) {
      handleDrop(categoryLabel, selected);
    }
  };

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>📦</span>
        <span>{headerLabel}</span>
      </div>

      {instruction && (
        <p className={styles.instruction}>
          <strong>{instruction}</strong>
        </p>
      )}

      {/* Category bins */}
      <div className={directStyles.classifyBins}>
        {categories.map((cat) => {
          const placedInBin = Object.entries(placed)
            .filter(([, label]) => label === cat.label)
            .map(([item]) => item);

          return (
            <div
              key={cat.label}
              className={directStyles.classifyBin}
              onClick={() => handleBinClick(cat.label)}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                const item = e.dataTransfer.getData('text/plain');
                if (item) handleDrop(cat.label, item);
              }}
            >
              <div className={directStyles.classifyBinLabel}>
                {cat.symbolHint === 'vowel' && (
                  <span className={directStyles.classifyBinIcon}>●</span>
                )}
                {cat.symbolHint === 'consonant' && (
                  <span className={directStyles.classifyBinIcon}>━</span>
                )}
                <span>{cat.label}</span>
              </div>
              <div className={directStyles.classifyBinItems}>
                {placedInBin.map((item) => (
                  <span key={item} className={directStyles.classifyPlacedItem}>
                    {item}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Remaining items to sort */}
      {!isComplete && (
        <div className={directStyles.classifyPool}>
          {remaining.map((item) => (
            <button
              key={item}
              className={`${directStyles.classifyTile} ${
                selected === item ? directStyles.classifyTileSelected : ''
              } ${
                feedback[item] === 'correct'
                  ? directStyles.classifyTileCorrect
                  : ''
              } ${
                feedback[item] === 'incorrect'
                  ? directStyles.classifyTileIncorrect
                  : ''
              }`}
              draggable
              onDragStart={(e) => {
                e.dataTransfer.setData('text/plain', item);
                e.dataTransfer.effectAllowed = 'move';
              }}
              onClick={() => handleItemClick(item)}
            >
              {item}
            </button>
          ))}
        </div>
      )}

      {/* Completion */}
      {isComplete && (
        <div
          className={`${styles.feedback} ${styles.feedbackCorrect}`}
          style={{ textAlign: 'center', marginTop: '1rem' }}
        >
          {doneLabel} {scoreLabel}: {correctCount}/{allItems.length}
        </div>
      )}
    </div>
  );
}
