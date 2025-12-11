import React, { useState, useMemo } from 'react';
import styles from './Activities.module.css';

interface GroupSortProps {
  groups: { [key: string]: string[] };
}

export default function GroupSort({ groups }: GroupSortProps) {
  const groupNames = Object.keys(groups);

  // Flatten and shuffle all items
  const allItems = useMemo(() => {
    const items: { word: string; group: string }[] = [];
    for (const [group, words] of Object.entries(groups)) {
      for (const word of words) {
        items.push({ word, group });
      }
    }
    // Shuffle
    for (let i = items.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [items[i], items[j]] = [items[j], items[i]];
    }
    return items;
  }, [groups]);

  const [sorted, setSorted] = useState<{ [key: string]: string[] }>(() => {
    const initial: { [key: string]: string[] } = {};
    for (const name of groupNames) {
      initial[name] = [];
    }
    return initial;
  });

  const [remaining, setRemaining] = useState<{ word: string; group: string }[]>(allItems);
  const [showResult, setShowResult] = useState(false);

  const handleDrop = (word: string, correctGroup: string, targetGroup: string) => {
    setRemaining(remaining.filter(item => item.word !== word));
    setSorted({
      ...sorted,
      [targetGroup]: [...sorted[targetGroup], word],
    });
  };

  const handleCheck = () => {
    setShowResult(true);
  };

  const isAllCorrect = () => {
    for (const [group, words] of Object.entries(sorted)) {
      for (const word of words) {
        const correctGroup = allItems.find(item => item.word === word)?.group;
        if (correctGroup !== group) return false;
      }
    }
    return remaining.length === 0;
  };

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>📊</span>
        <span>Group Sort</span>
      </div>

      <div className={styles.groupSortContainer}>
        {/* Remaining items to sort */}
        {remaining.length > 0 && (
          <div className={styles.itemPool}>
            {remaining.map((item, index) => (
              <div key={index} className={styles.sortableItem}>
                {item.word}
                <div className={styles.groupButtons}>
                  {groupNames.map(groupName => (
                    <button
                      key={groupName}
                      className={styles.groupButton}
                      onClick={() => handleDrop(item.word, item.group, groupName)}
                    >
                      → {groupName}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Group containers */}
        <div className={styles.groupContainers}>
          {groupNames.map(groupName => (
            <div key={groupName} className={styles.groupBox}>
              <h4 className={styles.groupTitle}>{groupName}</h4>
              <div className={styles.groupItems}>
                {sorted[groupName].map((word, index) => {
                  const correctGroup = allItems.find(item => item.word === word)?.group;
                  const isCorrect = correctGroup === groupName;
                  return (
                    <span
                      key={index}
                      className={`${styles.sortedItem} ${
                        showResult ? (isCorrect ? styles.correct : styles.incorrect) : ''
                      }`}
                    >
                      {word}
                    </span>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {remaining.length === 0 && !showResult && (
        <button className={styles.submitButton} onClick={handleCheck}>
          Check Answers
        </button>
      )}

      {showResult && (
        <div className={`${styles.feedback} ${isAllCorrect() ? styles.feedbackCorrect : styles.feedbackIncorrect}`}>
          {isAllCorrect() ? '✓ All sorted correctly!' : '✗ Some items are in the wrong group.'}
        </div>
      )}
    </div>
  );
}
