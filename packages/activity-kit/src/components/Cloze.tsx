import React, { useState, useMemo } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { shuffle } from './utils';

export interface ClozeBlank {
  /**
   * @schemaDescription Index value consumed by this component.
   * @ukrainianText false
   */
  index: number;
  /**
   * @schemaDescription Answer options shown to the learner.
   * @ukrainianText true
   */
  options: string[];
  /**
   * @schemaDescription Correct answer used for validation and feedback.
   * @ukrainianText true
   */
  answer: string;
}

export interface ClozePassageProps {
  /**
   * @schemaDescription Text passage shown to the learner.
   * @ukrainianText true
   */
  text: string;  // Text with [___:N] markers
  /**
   * @schemaDescription Blanks value consumed by this component.
   * @ukrainianText true
   */
  blanks: ClozeBlank[];
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
  onComplete?: () => void;
}

export function ClozePassage({ text, blanks, isUkrainian, onComplete }: ClozePassageProps) {
  // Pre-shuffle options for each blank on mount
  const shuffledBlanks = useMemo(() =>
    blanks.map(blank => ({
      ...blank,
      options: shuffle([...blank.options])
    })),
    [blanks]
  );

  const [selections, setSelections] = useState<Map<number, string>>(new Map());
  const [submitted, setSubmitted] = useState(false);

  const handleSelect = (index: number, value: string) => {
    if (submitted) return;
    const newSelections = new Map(selections);
    newSelections.set(index, value);
    setSelections(newSelections);
  };

  const handleSubmit = () => {
    setSubmitted(true);
    onComplete?.();
  };

  const handleReset = () => {
    setSelections(new Map());
    setSubmitted(false);
  };

  // Check if all answers are correct
  const allCorrect = blanks.every(blank =>
    selections.get(blank.index)?.toLowerCase().trim() === blank.answer.toLowerCase().trim()
  );

  // Parse text and replace [___:N] with select elements
  const renderText = () => {
    const parts: React.ReactNode[] = [];
    let lastIndex = 0;
    const regex = /\[___:(\d+)\]/g;
    let match;

    while ((match = regex.exec(text)) !== null) {
      // Add text before this blank
      if (match.index > lastIndex) {
        parts.push(text.slice(lastIndex, match.index));
      }

      const optionIndex = parseInt(match[1], 10);
      const blank = shuffledBlanks.find(b => b.index === optionIndex); // 1-based: [___:1] matches option "1." (#1191)

      if (blank) {
        const selected = selections.get(blank.index);
        const isCorrect = submitted && selected?.toLowerCase().trim() === blank.answer.toLowerCase().trim();
        const isIncorrect = submitted && selected && !isCorrect;

        parts.push(
          <select
            key={blank.index}
            className={`${styles.clozeSelect} ${isCorrect ? styles.correct : ''} ${isIncorrect ? styles.incorrect : ''}`}
            data-activity="cloze-blank"
            data-blank-index={blank.index}
            value={selected || ''}
            onChange={(e) => handleSelect(blank.index, e.target.value)}
            disabled={submitted}
          >
            <option value="">---</option>
            {blank.options.map((opt, idx) => (
              <option key={idx} value={opt}>{opt}</option>
            ))}
          </select>
        );
      }

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex));
    }

    return parts;
  };

  const allFilled = blanks.every(b => selections.has(b.index) && selections.get(b.index) !== '');

  const checkBtnLabel = isUkrainian ? 'Перевірити' : 'Check Answers';
  const retryBtnLabel = isUkrainian ? 'Спробувати знову' : 'Try Again';
  const successLabel = isUkrainian ? '✓ Всі відповіді правильні!' : '✓ All answers are correct!';
  const errorLabel = isUkrainian ? '✗ Деякі відповіді неправильні. Правильні відповіді:' : '✗ Some answers are incorrect. Correct answers:';

  return (
    <div data-activity="cloze-passage">
      <p className={styles.clozePassage}>
        {renderText()}
      </p>

      {!submitted && (
        <div className={styles.buttonRow}>
          <button
            className={styles.submitButton}
            onClick={handleSubmit}
            disabled={!allFilled}
          >
            {checkBtnLabel}
          </button>
        </div>
      )}

      {submitted && (
        <>
          <div
            className={`${styles.feedback} ${allCorrect ? styles.feedbackCorrect : styles.feedbackIncorrect}`}
            data-activity="cloze-feedback"
            data-correct={allCorrect ? 'true' : 'false'}
          >
            {allCorrect ? (
              successLabel
            ) : (
              <>
                {errorLabel}{' '}
                {blanks.map((b, i) => (
                  <span key={i}>
                    {i > 0 && ', '}
                    <strong>{b.answer}</strong>
                  </span>
                ))}
              </>
            )}
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

export interface ClozeProps {
  /**
   * @schemaDescription Passage value consumed by this component.
   * @ukrainianText true
   */
  passage?: string;  // MDX generator sends passage with embedded options
  /**
   * @schemaDescription Blanks value consumed by this component.
   * @ukrainianText true
   */
  blanks?: ClozeBlank[];
  /**
   * @schemaDescription Instruction shown to the learner above the activity.
   * @ukrainianText true
   */
  instruction?: string;
  /**
   * @schemaDescription Nested MDX content rendered inside the component.
   * @ukrainianText false
   */
  children?: React.ReactNode;
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
  onComplete?: () => void;
}

// Parse passage format with embedded numbered options:
// "Text [___:1] more text\n\n1. opt1 | opt2\n   > [!answer] opt1"
function parsePassageWithEmbeddedOptions(passage: string): { text: string; blanks: ClozeBlank[] } {
  const blanks: ClozeBlank[] = [];

  const blocks = passage.split('\n\n');
  const firstOptionBlock = blocks.findIndex((block) => {
    const separatorIndex = block.indexOf('.');
    const numberText = block.slice(0, separatorIndex);
    return numberText.length > 0 && [...numberText].every((character) => {
      const code = character.charCodeAt(0);
      return code >= 48 && code <= 57;
    });
  });
  const text = firstOptionBlock === -1 ? passage : blocks.slice(0, firstOptionBlock).join('\n\n');
  const optionLines = blocks.slice(Math.max(firstOptionBlock, 0)).join('\n\n').split('\n');

  // Parse numbered options (1. opt1 | opt2\n   > [!answer] correct) without
  // repeatedly applying a backtracking expression to untrusted lesson text.
  for (let lineIndex = 0; lineIndex < optionLines.length - 1; lineIndex += 1) {
    const optionLine = optionLines[lineIndex].trimStart();
    const separatorIndex = optionLine.indexOf('.');
    const numberText = optionLine.slice(0, separatorIndex);
    const hasNumber = numberText.length > 0 && [...numberText].every((character) => {
      const code = character.charCodeAt(0);
      return code >= 48 && code <= 57;
    });

    if (!hasNumber) continue;

    const answerLine = optionLines[lineIndex + 1].trimStart();
    if (!answerLine.startsWith('>')) continue;

    const answerText = answerLine.slice(1).trimStart();
    if (!answerText.startsWith('[!answer]')) continue;

    const answerToken = answerText.slice('[!answer]'.length).trimStart();
    const answerEnd = [...answerToken].findIndex((character) => character === ' ' || character === '\t');
    const answer = answerEnd === -1 ? answerToken : answerToken.slice(0, answerEnd);
    if (!answer) continue;

    const options = optionLine.slice(separatorIndex + 1).trim().split('|').map((option) => option.trim());
    blanks.push({ index: Number(numberText), options, answer });
    lineIndex += 1;
  }

  return { text, blanks };
}

export default function Cloze({ passage, blanks = [], instruction, children, isUkrainian, onComplete }: ClozeProps) {
  // Parse passage if provided with embedded options
  const parsedData = useMemo(() => {
    if (passage) {
      if (blanks.length > 0) {
        // Use provided blanks directly
        return { text: passage, blanks };
      }
      // Parse embedded options from passage
      return parsePassageWithEmbeddedOptions(passage);
    }
    return null;
  }, [passage, blanks]);

  const headerLabel = isUkrainian ? 'Заповніть текст' : 'Complete the Passage';

  return (
    <div className={styles.activityContainer} data-activity="cloze">
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>📝</span>
        <span>{headerLabel}</span>
        <ActivityHelp activityType="cloze" isUkrainian={isUkrainian} />
      </div>
      {instruction && (
        <p className={styles.instruction}><strong>{instruction}</strong></p>
      )}
      <div className={styles.activityContent}>
        {parsedData ? (
          <ClozePassage
            text={parsedData.text}
            blanks={parsedData.blanks}
            isUkrainian={isUkrainian}
            onComplete={onComplete}
          />
        ) : children}
      </div>
    </div>
  );
}
