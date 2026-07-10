import { useState } from 'react';
import styles from './Activities.module.css';

interface ActivityHelpProps {
  activityType: 'true-false' | 'cloze' | 'match-up';
  isUkrainian?: boolean;
}

const HELP_TEXT = {
  'match-up': {
    title: 'Match the Pairs',
    description: 'Connect items from the left column with their matching items on the right by clicking them.',
  },
  'true-false': {
    title: 'True or False',
    description: 'Decide whether each statement is true or false based on what you have learned.',
  },
  cloze: {
    title: 'Complete the Passage',
    description: 'Read the passage and fill in each blank by selecting the correct word.',
  },
} as const;

const HELP_TEXT_UA = {
  'match-up': {
    title: 'Знайдіть пару',
    description: "З'єднайте елементи лівої колонки з відповідними елементами праворуч, натискаючи на них.",
  },
  'true-false': {
    title: 'Правда чи хибність',
    description: 'Визначте, чи є кожне твердження правдивим чи хибним на основі вивченого матеріалу.',
  },
  cloze: {
    title: 'Заповніть текст',
    description: 'Прочитайте текст і заповніть пропуски, вибираючи правильне слово.',
  },
} as const;

export default function ActivityHelp({ activityType, isUkrainian }: ActivityHelpProps) {
  const [isOpen, setIsOpen] = useState(false);
  const help = isUkrainian ? HELP_TEXT_UA[activityType] : HELP_TEXT[activityType];
  const buttonTitle = isUkrainian ? 'Як працює ця вправа?' : 'How does this activity work?';

  return (
    <div className={styles.helpContainer}>
      <button
        className={styles.helpButton}
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Activity help"
        title={buttonTitle}
      >
        ?
      </button>
      {isOpen && (
        <>
          <div className={styles.helpOverlay} onClick={() => setIsOpen(false)} />
          <div className={styles.helpTooltip}>
            <div className={styles.helpTitle}>{help.title}</div>
            <div className={styles.helpDescription}>{help.description}</div>
          </div>
        </>
      )}
    </div>
  );
}
