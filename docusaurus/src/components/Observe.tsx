import React, { useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';

interface ObserveProps {
  examples: string[];
  prompt?: string;
  children?: React.ReactNode;
}

export function ObserveActivity({ examples, prompt = "What pattern do you notice?" }: ObserveProps) {
  const [revealed, setRevealed] = useState(false);

  return (
    <div className={styles.observeContainer}>
      <div className={styles.observeExamples}>
        {examples.map((example, idx) => (
          <div key={idx} className={styles.observeExample}>
            <span className={styles.exampleNumber}>{idx + 1}.</span>
            <span dangerouslySetInnerHTML={{ __html: example }} />
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
  children: React.ReactNode;
}

export default function Observe({ children }: ObserveBlockProps) {
  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>🔎</span>
        <span>Observe First</span>
        <ActivityHelp activityType="observe" />
      </div>
      <div className={styles.activityContent}>
        {children}
      </div>
    </div>
  );
}
