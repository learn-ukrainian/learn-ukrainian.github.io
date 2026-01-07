import React, { useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { parseMarkdown } from './utils';

interface ReadingProps {
  title: string;
  context?: string;
  resource?: {
    type?: string;
    url?: string;
    title?: string;
  };
  tasks: string[];
  isUkrainian?: boolean;
}

export default function ReadingActivity({
  title,
  context = '',
  resource,
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
          {context ? (
            parseMarkdown(context)
          ) : resource?.url ? (
            <div className={styles.externalResource}>
              <p>
                {isUkrainian ? 'Прочитайте матеріал за посиланням:' : 'Read the material at the link:'}
              </p>
              <a href={resource.url} target="_blank" rel="noopener noreferrer" className={styles.resourceLink}>
                📄 {resource.title || resource.url}
              </a>
              {resource.type && (
                <p className={styles.resourceType}>
                  <em>({resource.type})</em>
                </p>
              )}
            </div>
          ) : (
            <p className={styles.emptyContext}>
              {isUkrainian ? 'Немає тексту для читання' : 'No reading text provided'}
            </p>
          )}
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
