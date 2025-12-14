import React, { useState, useMemo } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { shuffle } from './utils';

interface ClozeBlank {
  index: number;
  options: string[];
  answer: string;
}

interface ClozePassageProps {
  text: string;  // Text with [___:N] markers
  blanks: ClozeBlank[];
}

export function ClozePassage({ text, blanks }: ClozePassageProps) {
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
      const blank = shuffledBlanks.find(b => b.index === optionIndex - 1); // Convert 1-based to 0-based

      if (blank) {
        const selected = selections.get(blank.index);
        const isCorrect = submitted && selected?.toLowerCase().trim() === blank.answer.toLowerCase().trim();
        const isIncorrect = submitted && selected && !isCorrect;

        parts.push(
          <select
            key={blank.index}
            className={`${styles.clozeSelect} ${isCorrect ? styles.correct : ''} ${isIncorrect ? styles.incorrect : ''}`}
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

  return (
    <div>
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
            Check Answers
          </button>
        </div>
      )}

      {submitted && (
        <>
          <div className={`${styles.feedback} ${allCorrect ? styles.feedbackCorrect : styles.feedbackIncorrect}`}>
            {allCorrect ? (
              '✓ All answers are correct!'
            ) : (
              <>
                ✗ Some answers are incorrect. Correct answers:{' '}
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
              Try Again
            </button>
          </div>
        </>
      )}
    </div>
  );
}

interface ClozeProps {
  passage?: string;  // MDX generator sends passage with embedded options
  blanks?: ClozeBlank[];
  children?: React.ReactNode;
}

// Parse passage format with embedded numbered options:
// "Text [___:1] more text\n\n1. opt1 | opt2\n   > [!answer] opt1"
function parsePassageWithEmbeddedOptions(passage: string): { text: string; blanks: ClozeBlank[] } {
  const blanks: ClozeBlank[] = [];

  // Split into main text and options section
  const parts = passage.split(/\n\n(?=\d+\.)/);
  const text = parts[0];

  // Parse numbered options (1. opt1 | opt2\n   > [!answer] correct)
  const optionPattern = /(\d+)\.\s*([^\n]+)\n\s*>\s*\[!answer\]\s*(\S+)/g;
  let match;

  const fullText = parts.join('\n\n');
  while ((match = optionPattern.exec(fullText)) !== null) {
    const index = parseInt(match[1], 10) - 1; // Convert to 0-based
    const optionsStr = match[2];
    const answer = match[3];
    const options = optionsStr.split('|').map(o => o.trim());

    blanks.push({ index, options, answer });
  }

  return { text, blanks };
}

export default function Cloze({ passage, blanks = [], children }: ClozeProps) {
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

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>📝</span>
        <span>Complete the Passage</span>
        <ActivityHelp activityType="cloze" />
      </div>
      <div className={styles.activityContent}>
        {parsedData ? (
          <ClozePassage text={parsedData.text} blanks={parsedData.blanks} />
        ) : children}
      </div>
    </div>
  );
}
