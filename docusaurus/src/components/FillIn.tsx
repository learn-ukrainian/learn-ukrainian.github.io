import React, { useState, useMemo } from 'react';
import styles from './Activities.module.css';
import { parseMarkdown, shuffle } from './utils';
import ActivityHelp from './ActivityHelp';

// Generate consistent colors for option chips
const CHIP_COLORS = [
  '#E53935', '#D81B60', '#8E24AA', '#5E35B1', '#3949AB',
  '#1E88E5', '#039BE5', '#00ACC1', '#00897B', '#43A047',
  '#7CB342', '#FB8C00', '#F4511E', '#6D4C41'
];

function getChipColor(text: string, index: number): string {
  const charSum = text.split('').reduce((sum, char) => sum + char.charCodeAt(0), 0);
  return CHIP_COLORS[(charSum + index) % CHIP_COLORS.length];
}

interface FillInQuestionProps {
  sentence: string;
  answer: string;
  options?: string[];
}

export function FillInQuestion({ sentence, answer, options = [] }: FillInQuestionProps) {
  const [selected, setSelected] = useState<string | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [draggedOption, setDraggedOption] = useState<string | null>(null);

  // Shuffle and create colored option chips
  const coloredOptions = useMemo(() => {
    const shuffled = shuffle([...options]);
    return shuffled.map((opt, idx) => ({
      text: opt,
      color: getChipColor(opt, idx)
    }));
  }, [options]);

  const handleSelect = (option: string) => {
    if (showResult) return;
    setSelected(option);
    setShowResult(true);
  };

  const handleDragStart = (e: React.DragEvent, option: string) => {
    setDraggedOption(option);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (draggedOption && !showResult) {
      setSelected(draggedOption);
      setShowResult(true);
    }
    setDraggedOption(null);
  };

  const handleReset = () => {
    setSelected(null);
    setShowResult(false);
  };

  const isCorrect = selected === answer;

  // Parse sentence - look for ___ or [blank]
  const parts = sentence.split(/___|\\[blank\\]/);
  const selectedColor = coloredOptions.find(o => o.text === selected)?.color;

  return (
    <div className={styles.fillInQuestion}>
      <p className={styles.sentenceWithBlank}>
        {parseMarkdown(parts[0])}
        <span
          className={`${styles.blankDropZone} ${showResult ? (isCorrect ? styles.correct : styles.incorrect) : ''}`}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          style={selected && selectedColor ? {
            backgroundColor: selectedColor,
            color: 'white',
            borderStyle: 'solid'
          } : undefined}
        >
          {selected || 'drag here'}
        </span>
        {parseMarkdown(parts[1] || '')}
      </p>

      {options.length > 0 && !showResult && (
        <div className={styles.optionChips}>
          {coloredOptions.map((option, index) => (
            <button
              key={index}
              className={styles.chipDraggable}
              style={{
                backgroundColor: option.color,
                color: 'white'
              }}
              draggable
              onDragStart={(e) => handleDragStart(e, option.text)}
              onClick={() => handleSelect(option.text)}
            >
              {option.text}
            </button>
          ))}
        </div>
      )}

      {showResult && (
        <div className={styles.buttonRow}>
          <button className={styles.resetButton} onClick={handleReset}>
            Try Again
          </button>
        </div>
      )}

      {showResult && (
        <div className={`${styles.feedback} ${isCorrect ? styles.feedbackCorrect : styles.feedbackIncorrect}`}>
          {isCorrect ? '✓ Correct!' : `✗ The answer is: ${answer}`}
        </div>
      )}
    </div>
  );
}

interface FillInItem {
  sentence: string;
  answer: string;
  options?: string[];
}

interface FillInProps {
  items: FillInItem[];
  instruction?: string;
  isUkrainian?: boolean;
}

export default function FillIn({ items, instruction, isUkrainian }: FillInProps) {
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [showResults, setShowResults] = useState(false);

  const handleSelect = (index: number, value: string) => {
    setAnswers({ ...answers, [index]: value });
  };

  const allAnswered = Object.keys(answers).length === items.length;
  const headerLabel = isUkrainian ? 'Заповніть пропуски' : 'Fill in the Blank';
  const checkBtnLabel = isUkrainian ? 'Перевірити' : 'Check Answers';
  const retryBtnLabel = isUkrainian ? 'Спробувати знову' : 'Try Again';

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>✍️</span>
        <span>{headerLabel}</span>
        <ActivityHelp activityType="fill-in" isUkrainian={isUkrainian} />
      </div>
      {instruction && (
        <p className={styles.instruction}><strong>{instruction}</strong></p>
      )}
      <div className={styles.activityContent}>
        {items.map((item, index) => {
          const parts = item.sentence.split('___');
          const isCorrect = answers[index] === item.answer;

          return (
            <div key={index} className={styles.fillInRow}>
              <span className={styles.fillInText}>
                {parseMarkdown(parts[0])}
                <select
                  className={`${styles.fillInSelect} ${showResults ? (isCorrect ? styles.correct : styles.incorrect) : ''
                    }`}
                  value={answers[index] || ''}
                  onChange={(e) => handleSelect(index, e.target.value)}
                  disabled={showResults}
                >
                  <option value=""></option>
                  {shuffle(item.options).map((opt, i) => (
                    <option key={i} value={opt}>
                      {opt}
                    </option>
                  ))}
                </select>
                {parseMarkdown(parts[1])}
              </span>
              {showResults && !isCorrect && (
                <span className={styles.correctHint}>
                  {isUkrainian ? 'Правильно:' : 'Correct:'} {item.answer}
                </span>
              )}
            </div>
          );
        })}

        <div className={styles.controls}>
          {!showResults ? (
            <button
              className={styles.checkButton}
              onClick={() => setShowResults(true)}
              disabled={!allAnswered}
            >
              {checkBtnLabel}
            </button>
          ) : (
            <button
              className={styles.retryButton}
              onClick={() => {
                setShowResults(false);
                setAnswers({});
              }}
            >
              {retryBtnLabel}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
