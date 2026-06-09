import React, { useMemo, useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { parseMarkdown } from './utils';

interface FormulaItem {
  /**
   * @schemaDescription Formula or motif text the learner identifies in the passage.
   * @ukrainianText true
   */
  text: string;
  /**
   * @schemaDescription Short label for the formula or motif.
   * @ukrainianText true
   */
  label?: string;
  /**
   * @schemaDescription Explanation shown after the learner selects the formula.
   * @ukrainianText true
   */
  explanation?: string;
}

interface MotifFormulaProps {
  /**
   * @schemaDescription Display title shown above the component.
   * @ukrainianText true
   */
  title: string;
  /**
   * @schemaDescription Instruction shown to the learner above the activity.
   * @ukrainianText true
   */
  instruction?: string;
  /**
   * @schemaDescription Text passage shown to the learner.
   * @ukrainianText true
   */
  passage: string;
  /**
   * @schemaDescription Formula or motif answers embedded in the passage.
   * @ukrainianText true
   */
  formulas: FormulaItem[];
  /**
   * @schemaDescription Prompt shown to guide the learner response.
   * @ukrainianText true
   */
  prompt?: string;
  /**
   * @schemaDescription Model answer for review or self-check.
   * @ukrainianText true
   */
  modelAnswer?: string;
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
}

interface PassageSegment {
  text: string;
  formulaIndex?: number;
}

function buildSegments(passage: string, formulas: FormulaItem[]): PassageSegment[] {
  const segments: PassageSegment[] = [];
  let cursor = 0;

  while (cursor < passage.length) {
    let matchIndex = -1;
    let matchFormulaIndex = -1;
    let matchText = '';
    formulas.forEach((formula, formulaIndex) => {
      const index = passage.indexOf(formula.text, cursor);
      if (index === -1) return;
      if (matchIndex === -1 || index < matchIndex || (index === matchIndex && formula.text.length > matchText.length)) {
        matchIndex = index;
        matchFormulaIndex = formulaIndex;
        matchText = formula.text;
      }
    });

    if (matchIndex === -1) {
      segments.push({ text: passage.slice(cursor) });
      break;
    }
    if (matchIndex > cursor) {
      segments.push({ text: passage.slice(cursor, matchIndex) });
    }
    segments.push({ text: matchText, formulaIndex: matchFormulaIndex });
    cursor = matchIndex + matchText.length;
  }

  return segments;
}

export default function MotifFormula({
  title,
  instruction,
  passage,
  formulas,
  prompt,
  modelAnswer,
  isUkrainian
}: MotifFormulaProps) {
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [showModel, setShowModel] = useState(false);
  const segments = useMemo(() => buildSegments(passage, formulas), [passage, formulas]);

  const headerLabel = isUkrainian ? 'Мотив / формула' : 'Motif / Formula';
  const promptLabel = isUkrainian ? 'Завдання:' : 'Task:';
  const selectedLabel = isUkrainian ? 'Ви позначили:' : 'Selected:';
  const modelLabel = isUkrainian ? (showModel ? 'Приховати зразок' : 'Показати зразок') : (showModel ? 'Hide model' : 'Show model');

  const toggleFormula = (formulaIndex: number) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(formulaIndex)) {
        next.delete(formulaIndex);
      } else {
        next.add(formulaIndex);
      }
      return next;
    });
  };

  const selectedFormulas = formulas.filter((_, index) => selected.has(index));

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={`${styles.exerciseBadge} ${styles.badgeMotif}`}>#44</span>
        <span>{title || headerLabel}</span>
        <ActivityHelp activityType="motif-formula" isUkrainian={isUkrainian} />
      </div>
      <div className={styles.activityContent}>
        {instruction && <p className={styles.instruction}><strong>{instruction}</strong></p>}
        {prompt && <div className={styles.essayPrompt}><strong>{promptLabel}</strong> {parseMarkdown(prompt)}</div>}

        <div className={styles.motifPassage}>
          {segments.map((segment, index) => {
            if (segment.formulaIndex === undefined) {
              return <span key={index}>{segment.text}</span>;
            }
            const isSelected = selected.has(segment.formulaIndex);
            return (
              <button
                key={index}
                type="button"
                className={`${styles.formula} ${isSelected ? styles.formulaSelected : ''}`}
                onClick={() => toggleFormula(segment.formulaIndex as number)}
              >
                {segment.text}
              </button>
            );
          })}
        </div>

        {selectedFormulas.length > 0 && (
          <div className={`${styles.feedback} ${styles.feedbackCorrect}`}>
            <strong>{selectedLabel}</strong>
            {selectedFormulas.map((formula, index) => (
              <div key={`${formula.text}-${index}`}>
                {formula.label && <strong>{formula.label}: </strong>}
                {formula.text}
                {formula.explanation && <div>{parseMarkdown(formula.explanation)}</div>}
              </div>
            ))}
          </div>
        )}

        {modelAnswer && (
          <div className={styles.buttonRow}>
            <button className={styles.submitButton} onClick={() => setShowModel(!showModel)}>
              {modelLabel}
            </button>
          </div>
        )}

        {showModel && modelAnswer && (
          <div className={`${styles.feedback} ${styles.modelAnswer}`}>
            {parseMarkdown(modelAnswer)}
          </div>
        )}
      </div>
    </div>
  );
}
