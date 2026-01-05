import React, { useState, useMemo } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';

interface DialogueLine {
  speaker: string;
  line: string;
}

interface DialogueReorderActivityProps {
  lines: DialogueLine[];  // correct order
  isUkrainian?: boolean;
}

function shuffleArray<T>(array: T[]): T[] {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
}

export function DialogueReorderActivity({ lines, isUkrainian }: DialogueReorderActivityProps) {
  // Create shuffled order with indices
  const shuffledIndices = useMemo(() => {
    const indices = lines.map((_, i) => i);
    return shuffleArray(indices);
  }, [lines]);

  const [currentOrder, setCurrentOrder] = useState<number[]>(shuffledIndices);
  const [submitted, setSubmitted] = useState(false);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);

  const handleDragStart = (e: React.DragEvent, index: number) => {
    setDraggedIndex(index);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent, targetIndex: number) => {
    e.preventDefault();
    if (draggedIndex === null || draggedIndex === targetIndex) return;

    const newOrder = [...currentOrder];
    const draggedItem = newOrder[draggedIndex];
    newOrder.splice(draggedIndex, 1);
    newOrder.splice(targetIndex, 0, draggedItem);
    setCurrentOrder(newOrder);
    setDraggedIndex(targetIndex);
  };

  const handleDragEnd = () => {
    setDraggedIndex(null);
  };

  const handleSubmit = () => {
    setSubmitted(true);
  };

  const handleReset = () => {
    setCurrentOrder(shuffleArray(lines.map((_, i) => i)));
    setSubmitted(false);
  };

  // Check if order is correct (0, 1, 2, 3, ...)
  const isCorrect = currentOrder.every((idx, pos) => idx === pos);

  const getLineClass = (originalIndex: number, position: number) => {
    if (!submitted) return '';
    return originalIndex === position ? styles.correct : styles.incorrect;
  };

  const checkBtnLabel = isUkrainian ? 'Перевірити' : 'Check Order';
  const retryBtnLabel = isUkrainian ? 'Спробувати знову' : 'Try Again';
  const successLabel = isUkrainian ? '✓ Правильно! Діалог у правильному порядку.' : '✓ Correct! The dialogue is in the right order.';
  const errorLabel = isUkrainian ? '✗ Порядок не зовсім правильний. Спробуйте ще раз!' : '✗ The order is not quite right. Try again!';

  return (
    <div>
      <div className={styles.dialogueContainer}>
        {currentOrder.map((originalIndex, position) => (
          <div
            key={originalIndex}
            className={`${styles.dialogueLine} ${getLineClass(originalIndex, position)} ${draggedIndex === position ? styles.dragging : ''}`}
            draggable={!submitted}
            onDragStart={(e) => handleDragStart(e, position)}
            onDragOver={(e) => handleDragOver(e, position)}
            onDragEnd={handleDragEnd}
          >
            <span className={styles.orderNumber}>{position + 1}</span>
            <span className={styles.speakerLabel}>{lines[originalIndex].speaker}</span>
            <span className={styles.dialogueText}>{lines[originalIndex].line}</span>
          </div>
        ))}
      </div>

      {!submitted && (
        <div className={styles.buttonRow}>
          <button className={styles.submitButton} onClick={handleSubmit}>
            {checkBtnLabel}
          </button>
        </div>
      )}

      {submitted && (
        <>
          <div className={`${styles.feedback} ${isCorrect ? styles.feedbackCorrect : styles.feedbackIncorrect}`}>
            {isCorrect ? successLabel : errorLabel}
          </div>
          <div className={styles.buttonRow}>
            <button className={styles.resetButton} onClick={handleReset}>
              {retryBtnLabel}
            </button>
          </div>
        </>
      )}
    </div>
  );
}

// Generator format with {text, order}
interface GeneratorDialogueLine {
  text: string;
  order: number;
  speaker?: string;
}

interface DialogueReorderProps {
  lines?: GeneratorDialogueLine[];
  children?: React.ReactNode;
  isUkrainian?: boolean;
}

export default function DialogueReorder({ lines, children, isUkrainian }: DialogueReorderProps) {
  // Transform generator format {text, order} to activity format {speaker, line}
  const transformedLines = useMemo(() => {
    if (!lines) return null;

    // Sort by order to get correct sequence, then convert format
    const sorted = [...lines].sort((a, b) => a.order - b.order);
    return sorted.map((item, idx) => ({
      speaker: item.speaker || String.fromCharCode(65 + (idx % 2)), // A, B, A, B...
      line: item.text
    }));
  }, [lines]);

  const headerLabel = isUkrainian ? 'Впорядкуйте діалог' : 'Put the Dialogue in Order';

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>💬</span>
        <span>{headerLabel}</span>
        <ActivityHelp activityType="dialogue-reorder" isUkrainian={isUkrainian} />
      </div>
      <div className={styles.activityContent}>
        {transformedLines ? (
          <DialogueReorderActivity lines={transformedLines} isUkrainian={isUkrainian} />
        ) : children}
      </div>
    </div>
  );
}
