import React, { useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { parseMarkdown } from './utils';

interface ReadingProps {
  title: string;
  context: string;
  tasks: string[];
  isUkrainian?: boolean;
}

export default function ReadingActivity({
  title,
  context,
  tasks,
  isUkrainian
}: ReadingProps) {
  const [showTasks, setShowTasks] = useState(false);

  const headerLabel = isUkrainian ? 'Читання' : 'Reading';
  const showTasksLabel = isUkrainian ? 
    (showTasks ? 'Приховати завдання' : 'Показати завдання') : 
    (showTasks ? 'Hide Tasks' : 'Show Tasks');

  // If no title provided, use default
  const displayTitle = title || headerLabel;

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>📖</span>
        <span>{displayTitle}</span>
        <ActivityHelp activityType="reading" isUkrainian={isUkrainian} />
      </div>
      <div className={styles.activityContent}>
        <div className={styles.readingContext}>
           {parseMarkdown(context)}
        </div>

        <div className={styles.buttonRow}>
            <button
              className={styles.submitButton}
              onClick={() => setShowTasks(!showTasks)}
            >
              {showTasksLabel}
            </button>
        </div>

        {showTasks && (
          <div className={styles.readingTasks}>
            <ul className={styles.taskList}>
              {tasks.map((task, index) => (
                <li key={index} className={styles.taskItem}>
                  {parseMarkdown(task)}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
