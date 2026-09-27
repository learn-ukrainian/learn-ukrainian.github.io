import React, { useState, useMemo, useRef, useEffect } from 'react';
import styles from './Activities.module.css';
import { shuffle } from './utils';
import ActivityHelp from './ActivityHelp';
import {
  chromeFacingBilingual,
  useActivityIsUkrainian,
  useChromeLocale,
} from '../lib/i18n/useChromeLocale';

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

/**
 * A group entry is a plain string on every existing module, or a
 * `{text, record, why}` object in fresh drafts — `why` explains a wrong
 * placement of this entry.
 */
type GroupSortEntry = string | { text: string; record?: string; why?: string };

function entryText(entry: GroupSortEntry): string {
  return typeof entry === 'string' ? entry : entry.text;
}

function entryWhy(entry: GroupSortEntry): string | undefined {
  return typeof entry === 'string' ? undefined : entry.why;
}

interface GroupSortProps {
  /**
   * @schemaDescription Groups value consumed by this component.
   * @ukrainianText true
   */
  groups: { [key: string]: GroupSortEntry[] };
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

export default function GroupSort({ groups, instruction, isUkrainian: bakedIsUkrainian }: GroupSortProps) {
  const isUkrainian = useActivityIsUkrainian(bakedIsUkrainian);
  const locale = useChromeLocale();
  const groupNames = Object.keys(groups);

  // Flatten and shuffle all items with colors
  const allItems = useMemo(() => {
    const items: { id: string; word: string; why?: string; correctGroup: string; color: string }[] = [];
    let idx = 0;
    for (const [group, entries] of Object.entries(groups)) {
      for (const entry of entries) {
        const word = entryText(entry);
        items.push({
          id: `item-${idx}`,
          word,
          why: entryWhy(entry),
          correctGroup: group,
          color: getWordColor(word, idx)
        });
        idx++;
      }
    }
    // Shuffle (deterministic — seeded by content)
    return shuffle(items);
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
  // Keyboard path (no native HTML5 drag-and-drop keyboard support exists):
  // Tab/Enter to select a tile, then Tab/Enter one of the group-choice
  // buttons that appear. Mirrors Order.tsx's click-to-place pattern.
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  // After a keyboard placement, the tile and chooser that had focus are
  // gone from the DOM — this carries the id of whatever should receive
  // focus next so it never falls back to document.body.
  const [pendingFocusId, setPendingFocusId] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const hasAnyWhy = allItems.some((item) => item.why);

  useEffect(() => {
    if (!pendingFocusId) return;
    const el = containerRef.current?.querySelector<HTMLElement>(`[data-focus-id="${pendingFocusId}"]`);
    el?.focus();
    setPendingFocusId(null);
  }, [pendingFocusId]);

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
    setSelectedItemId(null);
  };

  const handleTileSelect = (itemId: string) => {
    if (showResult) return;
    setSelectedItemId((prev) => (prev === itemId ? null : itemId));
  };

  // Keyboard equivalent of a drag-and-drop: moves the selected tile into
  // `target` (a group name, or '__pool__' to return it to the pool).
  const handlePlaceSelected = (target: string) => {
    if (!selectedItemId || showResult) return;
    const poolItem = remaining.find((i) => i.id === selectedItemId);
    if (poolItem) {
      if (target !== '__pool__') {
        const nextRemaining = remaining.filter((i) => i.id !== selectedItemId);
        setRemaining(nextRemaining);
        setSorted((prev) => ({ ...prev, [target]: [...prev[target], poolItem] }));
        setPendingFocusId(nextRemaining[0]?.id ?? 'group-sort-check');
      }
      setSelectedItemId(null);
      return;
    }
    let sourceGroup: string | null = null;
    let found: (typeof allItems)[number] | undefined;
    for (const [group, groupItems] of Object.entries(sorted)) {
      const hit = groupItems.find((i) => i.id === selectedItemId);
      if (hit) {
        sourceGroup = group;
        found = hit;
        break;
      }
    }
    if (found && sourceGroup && sourceGroup !== target) {
      const movedItem = found;
      const fromGroup = sourceGroup;
      setSorted((prev) => {
        const next = { ...prev, [fromGroup]: prev[fromGroup].filter((i) => i.id !== selectedItemId) };
        if (target !== '__pool__') next[target] = [...prev[target], movedItem];
        return next;
      });
      if (target === '__pool__') {
        setRemaining((prev) => [...prev, movedItem]);
        // The placed tile itself re-enters the pool as the next reachable
        // unplaced tile when there's nothing already ahead of it there.
        setPendingFocusId(remaining[0]?.id ?? selectedItemId);
      } else {
        setPendingFocusId(remaining[0]?.id ?? 'group-sort-check');
      }
    }
    setSelectedItemId(null);
  };

  const isAllCorrect = () => {
    for (const [group, items] of Object.entries(sorted)) {
      for (const item of items) {
        if (item.correctGroup !== group) return false;
      }
    }
    return remaining.length === 0;
  };

  // Renders the group-choice buttons for the currently selected tile. Called
  // inline right after that tile (in the pool or in its bucket) so Tab
  // reaches it immediately after the tile, instead of after every other tile
  // in the activity.
  const renderChooser = (itemId: string) => (
    <div
      role="group"
      aria-label={isUkrainian ? 'Виберіть групу' : 'Choose a group'}
      data-activity="group-sort-chooser"
      style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', margin: '0.5rem 0', flexBasis: '100%' }}
    >
      {!remaining.some((i) => i.id === itemId) && (
        <button
          type="button"
          className={styles.resetButton}
          data-activity="group-sort-choice"
          data-target="__pool__"
          onClick={() => handlePlaceSelected('__pool__')}
        >
          {isUkrainian ? '↩ Повернути до набору' : '↩ Return to pool'}
        </button>
      )}
      {groupNames.map((name) => (
        <button
          key={name}
          type="button"
          className={styles.submitButton}
          data-activity="group-sort-choice"
          data-target={name}
          onClick={() => handlePlaceSelected(name)}
        >
          {isUkrainian ? `Помістити в «${name}»` : `Place in "${name}"`}
        </button>
      ))}
    </div>
  );

  const headerLabel = isUkrainian ? 'Розподіліть за категоріями' : 'Group Sort';
  const poolEmptyLabel = isUkrainian ? 'Всі слова розподілено!' : 'All words sorted!';
  const bucketPlaceholderLabel = isUkrainian ? 'Перетягніть слова сюди' : 'Drop words here';
  const checkBtnLabel = isUkrainian ? 'Перевірити' : 'Check Answers';
  const retryBtnLabel = isUkrainian ? 'Спробувати знову' : 'Try Again';
  const successLabel = isUkrainian ? '✓ Все розподілено правильно!' : '✓ All sorted correctly!';
  const errorLabel = isUkrainian ? '✗ Деякі слова в неправильних групах.' : '✗ Some items are in the wrong group.';

  return (
    <div className={styles.activityContainer} data-activity="group-sort" ref={containerRef}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>📊</span>
        <span>{headerLabel}</span>
        <ActivityHelp activityType="group-sort" isUkrainian={isUkrainian} />
      </div>
      {chromeFacingBilingual(instruction, locale) && (
        <p className={styles.instruction}><strong>{chromeFacingBilingual(instruction, locale)}</strong></p>
      )}

      <div className={styles.groupSortContainer}>
        {/* Word pool - draggable items */}
        <div
          className={`${styles.wordPool} ${dragOverGroup === '__pool__' ? styles.dropTarget : ''}`}
          data-activity="group-sort-pool"
          onDragOver={(e) => handleDragOver(e, '__pool__')}
          onDragLeave={handleDragLeave}
          onDrop={handleDropOnPool}
        >
          {remaining.length > 0 ? (
            remaining.map((item) => {
              const isSelected = selectedItemId === item.id;
              return (
                <React.Fragment key={item.id}>
                  <button
                    className={`${styles.wordTile} ${isSelected ? styles.selectedWord : ''}`}
                    style={{
                      backgroundColor: isSelected ? undefined : item.color,
                      color: isSelected ? undefined : 'white',
                      cursor: showResult ? 'default' : 'grab'
                    }}
                    draggable={!showResult}
                    onDragStart={(e) => handleDragStart(e, item.id)}
                    onDragEnd={handleDragEnd}
                    onClick={() => handleTileSelect(item.id)}
                    data-focus-id={item.id}
                    {...(isSelected ? { 'aria-pressed': true } : {})}
                  >
                    {item.word}
                  </button>
                  {isSelected && !showResult && renderChooser(item.id)}
                </React.Fragment>
              );
            })
          ) : (
            <span className={styles.poolEmpty}>{poolEmptyLabel}</span>
          )}
        </div>

        {/* Group containers / buckets */}
        <div className={styles.groupContainers} data-activity="group-sort-buckets">
          {groupNames.map(groupName => (
            <div
              key={groupName}
              className={`${styles.groupBucket} ${dragOverGroup === groupName ? styles.dropTarget : ''}`}
              data-activity="group-sort-bucket"
              data-group-name={groupName}
              onDragOver={(e) => handleDragOver(e, groupName)}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDropOnGroup(e, groupName)}
            >
              <h4 className={styles.groupTitle}>{groupName}</h4>
              <div className={styles.groupItems}>
                {sorted[groupName].map((item) => {
                  const isCorrect = item.correctGroup === groupName;
                  const isSelected = selectedItemId === item.id;
                  const tile = (
                    <button
                      className={`${styles.wordTile} ${
                        showResult ? (isCorrect ? styles.correct : styles.incorrect) : (isSelected ? styles.selectedWord : '')
                      }`}
                      style={{
                        backgroundColor: showResult || isSelected ? undefined : item.color,
                        color: showResult || isSelected ? undefined : 'white',
                        cursor: showResult ? 'default' : 'grab'
                      }}
                      draggable={!showResult}
                      onDragStart={(e) => handleDragStart(e, item.id)}
                      onDragEnd={handleDragEnd}
                      onClick={() => handleTileSelect(item.id)}
                      data-focus-id={item.id}
                      {...(isSelected ? { 'aria-pressed': true } : {})}
                    >
                      {item.word}
                    </button>
                  );
                  const chooser = isSelected && !showResult ? renderChooser(item.id) : null;
                  // Only wrap in an extra element (and gain the why paragraph)
                  // when this entry actually carries a `why` — legacy
                  // string entries render the bare tile, exactly as on main.
                  if (item.why === undefined) {
                    return (
                      <React.Fragment key={item.id}>
                        {tile}
                        {chooser}
                      </React.Fragment>
                    );
                  }
                  return (
                    <div key={item.id} style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                      {tile}
                      {chooser}
                      {showResult && !isCorrect && (
                        <p
                          className={styles.explanation}
                          data-activity="group-sort-entry-why"
                          role="status"
                          aria-live="polite"
                        >
                          {item.why}
                        </p>
                      )}
                    </div>
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
          <button className={styles.submitButton} onClick={handleCheck} data-focus-id="group-sort-check">
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
        <div
          className={`${styles.feedback} ${isAllCorrect() ? styles.feedbackCorrect : styles.feedbackIncorrect}`}
          data-activity="group-sort-feedback"
          data-correct={isAllCorrect() ? 'true' : 'false'}
          {...(hasAnyWhy ? { role: 'status' as const, 'aria-live': 'polite' as const } : {})}
        >
          {isAllCorrect() ? successLabel : errorLabel}
        </div>
      )}
    </div>
  );
}
