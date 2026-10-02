import React, { useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { parseMarkdown } from './utils';

interface ObserveProps {
  /**
   * @schemaDescription Instruction shown to the learner above the activity.
   * @ukrainianText true
   */
  instruction?: string;
  /**
   * @schemaDescription Examples value consumed by this component.
   * @ukrainianText true
   */
  examples: string[];
  /**
   * @schemaDescription Prompt shown to guide the learner response.
   * @ukrainianText true
   */
  prompt?: string;
  /**
   * @schemaDescription Nested MDX content rendered inside the component.
   * @ukrainianText false
   */
  children?: React.ReactNode;
}

export function ObserveActivity({ examples, prompt = "What pattern do you notice?", instruction }: ObserveProps) {
  const [revealed, setRevealed] = useState(false);

  return (
    <div className={styles.observeContainer}>
      {instruction && (
        <p className={styles.instruction}>
          <strong>{instruction}</strong>
        </p>
      )}
      <div className={styles.observeExamples}>
        {examples.map((example, idx) => (
          <div key={idx} className={styles.observeExample}>
            <span className={styles.exampleNumber}>{idx + 1}.</span>
            <span>{parseMarkdown(example)}</span>
          </div>
        ))}
      </div>

      <div className={styles.observePrompt}>
        <span className={styles.observeIcon}>🔎</span>
        <span>{prompt}</span>
      </div>

      {!revealed && (
        <button
          className={styles.revealButton}
          onClick={() => setRevealed(true)}
        >
          Show Pattern
        </button>
      )}
    </div>
  );
}

interface ObserveBlockProps {
  /**
   * @schemaDescription Instruction shown to the learner above the activity.
   * @ukrainianText true
   */
  instruction?: string;
  /**
   * @schemaDescription Examples value consumed by this component.
   * @ukrainianText true
   */
  examples?: string[];
  /**
   * @schemaDescription Prompt shown to guide the learner response.
   * @ukrainianText true
   */
  prompt?: string;
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
}

export default function Observe({ examples, prompt, instruction, children, isUkrainian }: ObserveBlockProps) {
  const headerLabel = isUkrainian ? 'Спостережіть' : 'Observe First';

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>🔎</span>
        <span>{headerLabel}</span>
        <ActivityHelp activityType="observe" isUkrainian={isUkrainian} />
      </div>
      <div className={styles.activityContent}>
        {examples ? (
          <ObserveActivity examples={examples} instruction={instruction} prompt={prompt || (isUkrainian ? 'Який шаблон ви помітили?' : 'What pattern do you notice?')} />
        ) : (
          <>
            {instruction && (
              <p className={styles.instruction}>
                <strong>{instruction}</strong>
              </p>
            )}
            {children}
          </>
        )}
      </div>
    </div>
  );
}
