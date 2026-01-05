import React, { useState } from 'react';
import styles from './Activities.module.css';

interface ActivityHelpProps {
  activityType: string;
  isUkrainian?: boolean;
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
  'essay-response': {
    title: 'Essay Response',
    description: 'Write a structured essay in response to the prompt. Use the rubric to guide your writing and compare with the model answer.',
  },
  'comparative-study': {
    title: 'Comparative Study',
    description: 'Analyze and compare the provided materials. Identify similarities, differences, and patterns.',
  },
};

const HELP_TEXT_UA: Record<string, { title: string; description: string }> = {
  'quiz': {
    title: 'Вибір відповіді',
    description: 'Виберіть правильну відповідь із запропонованих варіантів. Лише одна відповідь є правильною.',
  },
  'fill-in': {
    title: 'Заповніть пропуски',
    description: 'Виберіть правильне слово або фразу з випадаючого списку, щоб доповнити речення.',
  },
  'match-up': {
    title: 'Знайдіть пару',
    description: 'З’єднайте елементи з лівої колонки з відповідними елементами праворуч, натискаючи на них.',
  },
  'true-false': {
    title: 'Правда чи хибність',
    description: 'Визначте, чи є кожне твердження правдивим чи хибним на основі вивченого матеріалу.',
  },
  'anagram': {
    title: 'Переставте літери',
    description: 'Переставте переплутані літери, щоб утворити правильне українське слово.',
  },
  'unjumble': {
    title: 'Складіть речення',
    description: 'Натискайте на слова, щоб розташувати їх у правильному порядку та утворити граматично правильне речення.',
  },
  'group-sort': {
    title: 'Розподіліть за категоріями',
    description: 'Перетягніть або натисніть на кожне слово, щоб помістити його у відповідний кошик категорії.',
  },
  'error-correction': {
    title: 'Знайдіть і виправте помилку',
    description: 'Кожне речення містить помилку. Знайдіть неправильне слово та виберіть правильну форму з варіантів.',
  },
  'cloze': {
    title: 'Заповніть текст',
    description: 'Прочитайте текст і заповніть пропуски, вибираючи правильне слово з кожного випадаючого списку.',
  },
  'mark-the-words': {
    title: 'Відмітьте слова',
    description: 'Натисніть на всі слова в тексті, які відповідають заданим критеріям (наприклад, іменники, дієслова, певний відмінок).',
  },
  'dialogue-reorder': {
    title: 'Впорядкуйте діалог',
    description: 'Розташуйте репліки розмови в правильному порядку, щоб створити природний діалог.',
  },
  'select': {
    title: 'Виберіть усі варіанти',
    description: 'Виберіть УСІ правильні відповіді. Правильних варіантів може бути декілька.',
  },
  'translate': {
    title: 'Виберіть переклад',
    description: 'Виберіть правильний переклад поданого речення або фрази.',
  },
  'observe': {
    title: 'Спостереження за мовою',
    description: 'Уважно вивчіть приклади та спробуйте самостійно знайти граматичну закономірність. Звертайте увагу на закінчення слів, структуру або значення.',
  },
  'essay-response': {
    title: 'Есе-відповідь',
    description: 'Напишіть структуроване есе у відповідь на завдання. Використовуйте критерії оцінювання та порівняйте свою відповідь зі зразком.',
  },
  'comparative-study': {
    title: 'Порівняльний аналіз',
    description: 'Проаналізуйте та порівняйте надані матеріали. Визначте схожості, відмінності та закономірності.',
  },
};

export default function ActivityHelp({ activityType, isUkrainian }: ActivityHelpProps) {
  const [isOpen, setIsOpen] = useState(false);

  const help = isUkrainian ? HELP_TEXT_UA[activityType] : HELP_TEXT[activityType];
  if (!help) return null;

  const btnTitle = isUkrainian ? 'Як працює ця вправа?' : 'How does this activity work?';

  return (
    <div className={styles.helpContainer}>
      <button
        className={styles.helpButton}
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Activity help"
        title={btnTitle}
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
