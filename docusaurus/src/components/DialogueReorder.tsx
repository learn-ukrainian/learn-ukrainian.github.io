import React, { useState, useMemo } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';

interface DialogueLine {
  speaker: string;
  line: string;
}

interface DialogueReorderActivityProps {
  lines: DialogueLine[];  // correct order
}

function shuffleArray<T>(array: T[]): T[] {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
}

export function DialogueReorderActivity({ lines }: DialogueReorderActivityProps) {
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
            Check Order
          </button>
        </div>
      )}

      {submitted && (
        <>
          <div className={`${styles.feedback} ${isCorrect ? styles.feedbackCorrect : styles.feedbackIncorrect}`}>
            {isCorrect ? (
              '✓ Correct! The dialogue is in the right order.'
            ) : (
              '✗ The order is not quite right. Try again!'
            )}
          </div>
          <div className={styles.buttonRow}>
            <button className={styles.resetButton} onClick={handleReset}>
              Try Again
            </button>
          </div>
        </>
      )}
    </div>
  );
}

interface DialogueReorderProps {
  children: React.ReactNode;
}

export default function DialogueReorder({ children }: DialogueReorderProps) {
  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>💬</span>
        <span>Put the Dialogue in Order</span>
        <ActivityHelp activityType="dialogue-reorder" />
      </div>
      <div className={styles.activityContent}>
        {children}
      </div>
    </div>
  );
}
