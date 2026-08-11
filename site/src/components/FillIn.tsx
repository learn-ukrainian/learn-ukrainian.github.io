import React, { useRef, useState, useMemo } from 'react';
import styles from './Activities.module.css';
import { parseMarkdown, shuffle } from './utils';
import ActivityHelp from './ActivityHelp';

// Generate consistent colors for option chips
const CHIP_COLORS = [
  '#E53935',
  '#D81B60',
  '#8E24AA',
  '#5E35B1',
  '#3949AB',
  '#1E88E5',
  '#039BE5',
  '#00ACC1',
  '#00897B',
  '#43A047',
  '#7CB342',
  '#FB8C00',
  '#F4511E',
  '#6D4C41',
];

function getChipColor(text: string, index: number): string {
  const charSum = text.split('').reduce((sum, char) => sum + char.charCodeAt(0), 0);
  return CHIP_COLORS[(charSum + index) % CHIP_COLORS.length];
}

export interface FillInQuestionProps {
  /**
   * @schemaDescription Sentence shown to the learner.
   * @ukrainianText true
   */
  sentence: string;
  /**
   * @schemaDescription Correct answer used for validation and feedback.
   * @ukrainianText true
   */
  answer: string;
  /**
   * @schemaDescription Answer options shown to the learner.
   * @ukrainianText true
   */
  options?: string[];
  /**
   * UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
  /** Called once when the learner locks an answer. */
  onComplete?: (correct: boolean) => void;
  /** Lets a host lock this item after it has recorded the result. */
  disabled?: boolean;
}

export function FillInQuestion({
  sentence,
  answer,
  options = [],
  isUkrainian,
  onComplete,
  disabled = false,
}: FillInQuestionProps) {
  const [selected, setSelected] = useState<string | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [draggedOption, setDraggedOption] = useState<string | null>(null);
  const [typedAnswer, setTypedAnswer] = useState('');
  const completionReportedRef = useRef(false);

  // Shuffle and create colored option chips
  const coloredOptions = useMemo(() => {
    const shuffled = shuffle([...options]);
    return shuffled.map((opt, idx) => ({
      text: opt,
      color: getChipColor(opt, idx),
    }));
  }, [options]);

  const complete = (value: string) => {
    if (disabled || showResult) return;
    const correct = value === answer;
    setSelected(value);
    setShowResult(true);
    if (!completionReportedRef.current) {
      completionReportedRef.current = true;
      onComplete?.(correct);
    }
  };

  const handleSelect = (option: string) => {
    if (disabled || showResult) return;
    complete(option);
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
    if (draggedOption && !showResult && !disabled) {
      complete(draggedOption);
    }
    setDraggedOption(null);
  };

  const handleReset = () => {
    if (disabled) return;
    setSelected(null);
    setShowResult(false);
    setTypedAnswer('');
    completionReportedRef.current = false;
  };

  const isCorrect = selected === answer;

  // Parse sentence - look for ___ or [blank]
  const parts = sentence.split(/___|\\[blank\\]/);
  const selectedColor = coloredOptions.find((o) => o.text === selected)?.color;
  const dragHereLabel = isUkrainian ? 'перетягніть сюди' : 'drag here';
  const retryLabel = isUkrainian ? 'Спробувати знову' : 'Try Again';
  const correctLabel = isUkrainian ? '✓ Правильно!' : '✓ Correct!';
  const answerLabel = isUkrainian ? '✗ Правильна відповідь:' : '✗ The answer is:';
  const checkLabel = isUkrainian ? 'Перевірити' : 'Check Answer';

  return (
    <div className={styles.fillInQuestion} data-activity="fillin-question">
      <p className={styles.sentenceWithBlank}>
        {parseMarkdown(parts[0])}
        <span
          className={`${styles.blankDropZone} ${showResult ? (isCorrect ? styles.correct : styles.incorrect) : ''}`}
          data-activity="fillin-blank"
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          style={
            selected && selectedColor
              ? {
                  backgroundColor: selectedColor,
                  color: 'white',
                  borderStyle: 'solid',
                }
              : undefined
          }
        >
          {options.length === 0 && !showResult ? (
            <input
              aria-label={isUkrainian ? 'Ваша відповідь' : 'Your answer'}
              className={styles.fillInSelect}
              value={typedAnswer}
              onChange={(event) => setTypedAnswer(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && typedAnswer.trim()) complete(typedAnswer.trim());
              }}
              disabled={disabled}
            />
          ) : (
            selected || dragHereLabel
          )}
        </span>
        {parseMarkdown(parts[1] || '')}
      </p>

      {options.length > 0 && !showResult && (
        <div className={styles.optionChips} data-activity="fillin-chips">
          {coloredOptions.map((option, index) => (
            <button
              key={index}
              className={styles.chipDraggable}
              style={{
                backgroundColor: option.color,
                color: 'white',
              }}
              draggable
              onDragStart={(e) => handleDragStart(e, option.text)}
              onClick={() => handleSelect(option.text)}
              disabled={disabled}
            >
              {option.text}
            </button>
          ))}
        </div>
      )}

      {options.length === 0 && !showResult && (
        <div className={styles.buttonRow}>
          <button
            className={styles.submitButton}
            onClick={() => complete(typedAnswer.trim())}
            disabled={disabled || !typedAnswer.trim()}
          >
            {checkLabel}
          </button>
        </div>
      )}

      {showResult && (
        <div className={styles.buttonRow}>
          <button className={styles.resetButton} onClick={handleReset} disabled={disabled}>
            {retryLabel}
          </button>
        </div>
      )}

      {showResult && (
        <div
          className={`${styles.feedback} ${isCorrect ? styles.feedbackCorrect : styles.feedbackIncorrect}`}
          data-activity="fillin-feedback"
          data-correct={isCorrect ? 'true' : 'false'}
        >
          {isCorrect ? correctLabel : `${answerLabel} ${answer}`}
        </div>
      )}
    </div>
  );
}

interface FillInItem {
  /**
   * @schemaDescription Sentence shown to the learner.
   * @ukrainianText true
   */
  sentence: string;
  /**
   * @schemaDescription Correct answer used for validation and feedback.
   * @ukrainianText true
   */
  answer: string;
  /**
   * @schemaDescription Answer options shown to the learner.
   * @ukrainianText true
   */
  options?: string[];
}

interface FillInProps {
  /**
   * @schemaDescription Array of activity items rendered by the component.
   * @ukrainianText true
   */
  items: FillInItem[];
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
    <div className={styles.activityContainer} data-activity="fill-in">
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>✍️</span>
        <span>{headerLabel}</span>
        <ActivityHelp activityType="fill-in" isUkrainian={isUkrainian} />
      </div>
      {instruction && (
        <p className={styles.instruction}>
          <strong>{instruction}</strong>
        </p>
      )}
      <div className={styles.activityContent}>
        {items.map((item, index) => {
          const parts = item.sentence.split(/_{3,}/); // Match 3+ underscores
          const isCorrect = answers[index] === item.answer;

          return (
            <div key={index} className={styles.fillInRow} data-activity="fillin-row">
              <span className={styles.fillInText}>
                {parseMarkdown(parts[0])}
                <select
                  className={`${styles.fillInSelect} ${
                    showResults ? (isCorrect ? styles.correct : styles.incorrect) : ''
                  }`}
                  value={answers[index] || ''}
                  onChange={(e) => handleSelect(index, e.target.value)}
                  disabled={showResults}
                >
                  <option value=""></option>
                  {shuffle(item.options || []).map((opt, i) => (
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
