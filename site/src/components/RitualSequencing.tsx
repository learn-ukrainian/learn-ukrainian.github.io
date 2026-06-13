import React, { useMemo, useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { shuffleNotCorrect, parseMarkdown } from './utils';

interface RitualSequencingProps {
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
   * @schemaDescription Ordered or shuffled rite steps shown to the learner.
   * @ukrainianText true
   */
  steps: string[];
  /**
   * @schemaDescription Zero-based order indices for the correct ritual sequence.
   * @ukrainianText false
   */
  correctOrder: number[];
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

export default function RitualSequencing({
  title,
  instruction,
  steps,
  correctOrder,
  modelAnswer,
  isUkrainian
}: RitualSequencingProps) {
  const correctSequence = useMemo(() => correctOrder.map(index => steps[index]), [steps, correctOrder]);
  const shuffled = useMemo(() => {
    const shuffledSteps = shuffleNotCorrect(steps, correctSequence);
    return shuffledSteps.map((text, index) => ({ id: `ritual-step-${index}`, text }));
  }, [steps, correctSequence]);

  const [available, setAvailable] = useState(shuffled);
  const [selected, setSelected] = useState<typeof shuffled>([]);
  const [submitted, setSubmitted] = useState(false);
  const [showModel, setShowModel] = useState(false);

  const moveStep = (step: typeof shuffled[0], fromSelected: boolean) => {
    if (submitted) return;
    if (fromSelected) {
      setSelected(prev => prev.filter(item => item.id !== step.id));
      setAvailable(prev => [...prev, step]);
    } else {
      setAvailable(prev => prev.filter(item => item.id !== step.id));
      setSelected(prev => [...prev, step]);
    }
  };

  const reset = () => {
    setAvailable(shuffled);
    setSelected([]);
    setSubmitted(false);
    setShowModel(false);
  };

  const isCorrect = selected.map(item => item.text).join('\n') === correctSequence.join('\n');
  const headerLabel = isUkrainian ? 'Послідовність обряду' : 'Ritual Sequencing';
  const checkLabel = isUkrainian ? 'Перевірити' : 'Check';
  const retryLabel = isUkrainian ? 'Спробувати знову' : 'Try Again';
  const bankLabel = isUkrainian ? 'Етапи обряду' : 'Rite steps';
  const answerLabel = isUkrainian ? 'Ваша послідовність' : 'Your sequence';
  const placeholder = isUkrainian ? 'Натисніть етапи у правильному порядку...' : 'Click the steps in order...';
  const modelLabel = isUkrainian ? (showModel ? 'Приховати зразок' : 'Показати зразок') : (showModel ? 'Hide model' : 'Show model');

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={`${styles.exerciseBadge} ${styles.badgeRitual}`}>#42</span>
        <span>{title || headerLabel}</span>
        <ActivityHelp activityType="ritual-sequencing" isUkrainian={isUkrainian} />
      </div>
      <div className={styles.activityContent}>
        {instruction && <p className={styles.instruction}><strong>{instruction}</strong></p>}

        <div className={styles.ritualSequencingGrid}>
          <div>
            <div className={styles.inputLabel}>{bankLabel}</div>
            <div className={styles.ritualTimeline}>
              {available.map(step => (
                <button
                  key={step.id}
                  type="button"
                  className={styles.ritualStepButton}
                  onClick={() => moveStep(step, false)}
                  disabled={submitted}
                >
                  {step.text}
                </button>
              ))}
            </div>
          </div>

          <div>
            <div className={styles.inputLabel}>{answerLabel}</div>
            <div className={`${styles.ritualTimeline} ${styles.ritualAnswerZone} ${submitted ? (isCorrect ? styles.correct : styles.incorrect) : ''}`}>
              {selected.length === 0 ? (
                <span className={styles.placeholder}>{placeholder}</span>
              ) : selected.map(step => (
                <button
                  key={step.id}
                  type="button"
                  className={styles.ritualStepButton}
                  onClick={() => moveStep(step, true)}
                  disabled={submitted}
                >
                  {step.text}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className={styles.buttonRow}>
          {!submitted ? (
            <button className={styles.submitButton} onClick={() => setSubmitted(true)} disabled={available.length > 0}>
              {checkLabel}
            </button>
          ) : (
            <button className={styles.resetButton} onClick={reset}>{retryLabel}</button>
          )}
          {modelAnswer && (
            <button className={styles.secondaryButton} onClick={() => setShowModel(!showModel)}>
              {modelLabel}
            </button>
          )}
        </div>

        {submitted && (
          <div className={`${styles.feedback} ${isCorrect ? styles.feedbackCorrect : styles.feedbackIncorrect}`}>
            {isCorrect ? (isUkrainian ? 'Правильно.' : 'Correct.') : (
              <div>
                <p>{isUkrainian ? 'Правильний порядок:' : 'Correct order:'}</p>
                {correctSequence.map((step, index) => <p key={index}>{index + 1}. {step}</p>)}
              </div>
            )}
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
