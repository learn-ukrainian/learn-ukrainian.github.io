import React, { useState, useMemo } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';

// Generate consistent colors for words
const WORD_COLORS = [
  '#E53935', '#D81B60', '#8E24AA', '#5E35B1', '#3949AB',
  '#1E88E5', '#039BE5', '#00ACC1', '#00897B', '#43A047',
  '#7CB342', '#FB8C00', '#F4511E', '#6D4C41'
];

function getWordColor(word: string, index: number): string {
  const charSum = word.split('').reduce((sum, char) => sum + char.charCodeAt(0), 0);
  return WORD_COLORS[(charSum + index) % WORD_COLORS.length];
}

interface GroupSortProps {
  groups: { [key: string]: string[] };
  isUkrainian?: boolean;
}

export default function GroupSort({ groups, isUkrainian }: GroupSortProps) {
  const groupNames = Object.keys(groups);

  // Flatten and shuffle all items with colors
  const allItems = useMemo(() => {
    const items: { id: string; word: string; correctGroup: string; color: string }[] = [];
    let idx = 0;
    for (const [group, words] of Object.entries(groups)) {
      for (const word of words) {
        items.push({
          id: `item-${idx}`,
          word,
          correctGroup: group,
          color: getWordColor(word, idx)
        });
        idx++;
      }
    }
    // Shuffle
    for (let i = items.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [items[i], items[j]] = [items[j], items[i]];
    }
    return items;
  }, [groups]);

  const [sorted, setSorted] = useState<{ [key: string]: typeof allItems }>(() => {
    const initial: { [key: string]: typeof allItems } = {};
    for (const name of groupNames) {
      initial[name] = [];
    }
    return initial;
  });

  const [remaining, setRemaining] = useState(allItems);
  const [showResult, setShowResult] = useState(false);
  const [draggedItem, setDraggedItem] = useState<string | null>(null);
  const [dragOverGroup, setDragOverGroup] = useState<string | null>(null);

  const handleDragStart = (e: React.DragEvent, itemId: string) => {
    setDraggedItem(itemId);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent, groupName?: string) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverGroup(groupName || null);
  };

  const handleDragLeave = () => {
    setDragOverGroup(null);
  };

  const handleDropOnGroup = (e: React.DragEvent, targetGroup: string) => {
    e.preventDefault();
    if (!draggedItem || showResult) return;

    // Find item in remaining pool or other groups
    let item = remaining.find(i => i.id === draggedItem);
    let fromGroup: string | null = null;

    if (!item) {
      // Check if it's in another group
      for (const [group, items] of Object.entries(sorted)) {
        const found = items.find(i => i.id === draggedItem);
        if (found) {
          item = found;
          fromGroup = group;
          break;
        }
      }
    }

    if (item) {
      // Remove from source
      if (fromGroup) {
        setSorted(prev => ({
          ...prev,
          [fromGroup!]: prev[fromGroup!].filter(i => i.id !== draggedItem),
          [targetGroup]: [...prev[targetGroup], item!]
        }));
      } else {
        setRemaining(prev => prev.filter(i => i.id !== draggedItem));
        setSorted(prev => ({
          ...prev,
          [targetGroup]: [...prev[targetGroup], item!]
        }));
      }
    }

    setDraggedItem(null);
    setDragOverGroup(null);
  };

  const handleDropOnPool = (e: React.DragEvent) => {
    e.preventDefault();
    if (!draggedItem || showResult) return;

    // Find item in groups
    for (const [group, items] of Object.entries(sorted)) {
      const item = items.find(i => i.id === draggedItem);
      if (item) {
        setSorted(prev => ({
          ...prev,
          [group]: prev[group].filter(i => i.id !== draggedItem)
        }));
        setRemaining(prev => [...prev, item]);
        break;
      }
    }

    setDraggedItem(null);
    setDragOverGroup(null);
  };

  const handleDragEnd = () => {
    setDraggedItem(null);
    setDragOverGroup(null);
  };

  const handleCheck = () => {
    setShowResult(true);
  };

  const handleReset = () => {
    setRemaining(allItems);
    const initial: { [key: string]: typeof allItems } = {};
    for (const name of groupNames) {
      initial[name] = [];
    }
    setSorted(initial);
    setShowResult(false);
  };

  const isAllCorrect = () => {
    for (const [group, items] of Object.entries(sorted)) {
      for (const item of items) {
        if (item.correctGroup !== group) return false;
      }
    }
    return remaining.length === 0;
  };

  const headerLabel = isUkrainian ? 'Розподіліть за категоріями' : 'Group Sort';
  const poolEmptyLabel = isUkrainian ? 'Всі слова розподілено!' : 'All words sorted!';
  const bucketPlaceholderLabel = isUkrainian ? 'Перетягніть слова сюди' : 'Drop words here';
  const checkBtnLabel = isUkrainian ? 'Перевірити' : 'Check Answers';
  const retryBtnLabel = isUkrainian ? 'Спробувати знову' : 'Try Again';
  const successLabel = isUkrainian ? '✓ Все розподілено правильно!' : '✓ All sorted correctly!';
  const errorLabel = isUkrainian ? '✗ Деякі слова в неправильних групах.' : '✗ Some items are in the wrong group.';

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>📊</span>
        <span>{headerLabel}</span>
        <ActivityHelp activityType="group-sort" isUkrainian={isUkrainian} />
      </div>

      <div className={styles.groupSortContainer}>
        {/* Word pool - draggable items */}
        <div
          className={`${styles.wordPool} ${dragOverGroup === '__pool__' ? styles.dropTarget : ''}`}
          onDragOver={(e) => handleDragOver(e, '__pool__')}
          onDragLeave={handleDragLeave}
          onDrop={handleDropOnPool}
        >
          {remaining.length > 0 ? (
            remaining.map((item) => (
              <button
                key={item.id}
                className={styles.wordTile}
                style={{
                  backgroundColor: item.color,
                  color: 'white',
                  cursor: showResult ? 'default' : 'grab'
                }}
                draggable={!showResult}
                onDragStart={(e) => handleDragStart(e, item.id)}
                onDragEnd={handleDragEnd}
              >
                {item.word}
              </button>
            ))
          ) : (
            <span className={styles.poolEmpty}>{poolEmptyLabel}</span>
          )}
        </div>

        {/* Group containers / buckets */}
        <div className={styles.groupContainers}>
          {groupNames.map(groupName => (
            <div
              key={groupName}
              className={`${styles.groupBucket} ${dragOverGroup === groupName ? styles.dropTarget : ''}`}
              onDragOver={(e) => handleDragOver(e, groupName)}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDropOnGroup(e, groupName)}
            >
              <h4 className={styles.groupTitle}>{groupName}</h4>
              <div className={styles.groupItems}>
                {sorted[groupName].map((item) => {
                  const isCorrect = item.correctGroup === groupName;
                  return (
                    <button
                      key={item.id}
                      className={`${styles.wordTile} ${
                        showResult ? (isCorrect ? styles.correct : styles.incorrect) : ''
                      }`}
                      style={{
                        backgroundColor: showResult ? undefined : item.color,
                        color: showResult ? undefined : 'white',
                        cursor: showResult ? 'default' : 'grab'
                      }}
                      draggable={!showResult}
                      onDragStart={(e) => handleDragStart(e, item.id)}
                      onDragEnd={handleDragEnd}
                    >
                      {item.word}
                    </button>
                  );
                })}
                {sorted[groupName].length === 0 && !showResult && (
                  <span className={styles.bucketPlaceholder}>{bucketPlaceholderLabel}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className={styles.buttonRow}>
        {remaining.length === 0 && !showResult && (
          <button className={styles.submitButton} onClick={handleCheck}>
            {checkBtnLabel}
          </button>
        )}
        {showResult && (
          <button className={styles.resetButton} onClick={handleReset}>
            {retryBtnLabel}
          </button>
        )}
      </div>

      {showResult && (
        <div className={`${styles.feedback} ${isAllCorrect() ? styles.feedbackCorrect : styles.feedbackIncorrect}`}>
          {isAllCorrect() ? successLabel : errorLabel}
        </div>
      )}
    </div>
  );
}
