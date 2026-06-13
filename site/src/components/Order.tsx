import React, { useState, useMemo } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { shuffleNotCorrect } from './utils';

interface OrderProps {
  /**
   * @schemaDescription Array of activity items rendered by the component.
   * @ukrainianText true
   */
  items: string[];
  /**
   * @schemaDescription Zero-based order indices for the correct sequence.
   * @ukrainianText false
   */
  correct_order: number[];
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

export default function Order({ items, correct_order, instruction, isUkrainian }: OrderProps) {
  const correctSequence = useMemo(() => correct_order.map(i => items[i]), [items, correct_order]);

  const shuffled = useMemo(() => {
    const indexed = items.map((text, i) => ({ text, origIdx: i }));
    const shuffledItems = shuffleNotCorrect(
      indexed.map(x => x.text),
      correctSequence
    );
    return shuffledItems.map((text, i) => ({ id: `line-${i}`, text }));
  }, [items, correctSequence]);

  const [available, setAvailable] = useState(shuffled);
  const [selected, setSelected] = useState<typeof shuffled>([]);
  const [showResult, setShowResult] = useState(false);

  const handleClick = (item: typeof shuffled[0], fromSelected: boolean) => {
    if (showResult) return;
    if (fromSelected) {
      setSelected(prev => prev.filter(x => x.id !== item.id));
      setAvailable(prev => [...prev, item]);
    } else {
      setAvailable(prev => prev.filter(x => x.id !== item.id));
      setSelected(prev => [...prev, item]);
    }
  };

  const handleCheck = () => setShowResult(true);

  const handleReset = () => {
    setAvailable(shuffled);
    setSelected([]);
    setShowResult(false);
  };

  const isCorrect = selected.map(s => s.text).join('\n') === correctSequence.join('\n');

  const headerLabel = isUkrainian ? 'Розставте в правильному порядку' : 'Put in the Correct Order';
  const checkLabel = isUkrainian ? 'Перевірити' : 'Check';
  const retryLabel = isUkrainian ? 'Спробувати знову' : 'Try Again';
  const correctMsg = isUkrainian ? '✓ Правильно!' : '✓ Correct!';
  const incorrectMsg = isUkrainian ? '✗ Правильний порядок:' : '✗ Correct order:';

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>📋</span>
        <span>{headerLabel}</span>
        <ActivityHelp activityType="order" isUkrainian={isUkrainian} />
      </div>
      {instruction && (
        <p className={styles.instruction}><strong>{instruction}</strong></p>
      )}
      <div className={styles.activityContent}>
        {/* Selected (answer) zone */}
        <div
          className={`${styles.sentenceBuilder} ${showResult ? (isCorrect ? styles.correct : styles.incorrect) : ''}`}
          style={{ minHeight: '80px', flexDirection: 'column', gap: '0.4rem' }}
        >
          {selected.length > 0 ? (
            selected.map((item, idx) => (
              <button
                key={item.id}
                className={styles.wordTile}
                style={{ width: '100%', textAlign: 'left', padding: '0.5rem 0.75rem', cursor: showResult ? 'default' : 'pointer' }}
                onClick={() => handleClick(item, true)}
                disabled={showResult}
              >
                {idx + 1}. {item.text}
              </button>
            ))
          ) : (
            <span className={styles.placeholder}>
              {isUkrainian ? 'Натисніть на рядки, щоб розставити їх у порядку...' : 'Click lines to arrange them in order...'}
            </span>
          )}
        </div>

        {/* Available lines */}
        <div className={styles.wordBank} style={{ flexDirection: 'column', gap: '0.4rem' }}>
          {available.map((item) => (
            <button
              key={item.id}
              className={styles.wordTile}
              style={{ width: '100%', textAlign: 'left', padding: '0.5rem 0.75rem', cursor: showResult ? 'default' : 'pointer' }}
              onClick={() => handleClick(item, false)}
              disabled={showResult}
            >
              {item.text}
            </button>
          ))}
        </div>

        <div className={styles.buttonRow}>
          {!showResult ? (
            <button
              className={styles.submitButton}
              onClick={handleCheck}
              disabled={available.length > 0}
            >
              {checkLabel}
            </button>
          ) : (
            <button className={styles.resetButton} onClick={handleReset}>
              {retryLabel}
            </button>
          )}
        </div>

        {showResult && (
          <div
            className={`${styles.feedback} ${isCorrect ? styles.feedbackCorrect : styles.feedbackIncorrect}`}
          >
            {isCorrect ? correctMsg : (
              <div>
                <p>{incorrectMsg}</p>
                {correctSequence.map((line, i) => (
                  <p key={i}>{i + 1}. {line}</p>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
