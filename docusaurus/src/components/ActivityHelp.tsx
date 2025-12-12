import React, { useState } from 'react';
import styles from './Activities.module.css';

interface ActivityHelpProps {
  activityType: string;
}

const HELP_TEXT: Record<string, { title: string; description: string }> = {
  'quiz': {
    title: 'Multiple Choice',
    description: 'Select the correct answer from the options provided. Only one answer is correct.',
  },
  'fill-in': {
    title: 'Fill in the Blank',
    description: 'Choose the correct word or phrase to complete each sentence from the dropdown options.',
  },
  'match-up': {
    title: 'Match the Pairs',
    description: 'Connect items from the left column with their matching items on the right by clicking or dragging.',
  },
  'true-false': {
    title: 'True or False',
    description: 'Decide whether each statement is true or false based on what you\'ve learned.',
  },
  'anagram': {
    title: 'Unscramble the Letters',
    description: 'Rearrange the scrambled letters to form the correct Ukrainian word.',
  },
  'unjumble': {
    title: 'Build the Sentence',
    description: 'Drag or click the words to arrange them in the correct order to form a grammatically correct sentence.',
  },
  'group-sort': {
    title: 'Sort into Groups',
    description: 'Drag each word from the pool into the correct category bucket. You can also drag words between buckets to change your answer.',
  },
  'error-correction': {
    title: 'Find & Fix the Error',
    description: 'Each sentence contains an error. Find the incorrect word and select the correct form from the options.',
  },
  'cloze': {
    title: 'Complete the Passage',
    description: 'Read the passage and fill in the blanks by selecting the correct word from each dropdown.',
  },
  'mark-the-words': {
    title: 'Mark the Words',
    description: 'Click on all the words in the text that match the given criteria (e.g., nouns, verbs, specific case).',
  },
  'dialogue-reorder': {
    title: 'Order the Dialogue',
    description: 'Arrange the conversation lines in the correct order to create a natural dialogue flow.',
  },
  'select': {
    title: 'Select All That Apply',
    description: 'Choose ALL correct answers. Multiple options may be correct.',
  },
  'translate': {
    title: 'Choose the Translation',
    description: 'Select the correct translation of the given sentence or phrase.',
  },
  'observe': {
    title: 'Observe the Pattern',
    description: 'Study the examples carefully and try to discover the grammar pattern before it\'s explained. Look for similarities in word endings, structure, or meaning.',
  },
};

export default function ActivityHelp({ activityType }: ActivityHelpProps) {
  const [isOpen, setIsOpen] = useState(false);

  const help = HELP_TEXT[activityType];
  if (!help) return null;

  return (
    <div className={styles.helpContainer}>
      <button
        className={styles.helpButton}
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Activity help"
        title="How does this activity work?"
      >
        ?
      </button>

      {isOpen && (
        <>
          <div
            className={styles.helpOverlay}
            onClick={() => setIsOpen(false)}
          />
          <div className={styles.helpTooltip}>
            <div className={styles.helpTitle}>{help.title}</div>
            <div className={styles.helpDescription}>{help.description}</div>
          </div>
        </>
      )}
    </div>
  );
}
