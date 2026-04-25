import React, { useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { parseMarkdown } from './utils';

interface ReadingProps {
  /**
   * @schemaDescription Display title shown above the component.
   * @ukrainianText true
   */
  title: string;
  /**
   * @schemaDescription Context value consumed by this component.
   * @ukrainianText true
   */
  context?: string;
  /**
   * @schemaDescription Text passage shown to the learner.
   * @ukrainianText true
   */
  text?: string;  // Seminar: inline primary source text
  /**
   * @schemaDescription Source value consumed by this component.
   * @ukrainianText false
   */
  source?: string;  // Seminar: attribution (e.g., 'Тарас Шевченко (1845)')
  resource?: {
    /**
     * @schemaDescription Type value consumed by this component.
     * @ukrainianText false
     */
    type?: string;
    /**
     * @schemaDescription External URL for the embedded or linked resource.
     * @ukrainianText false
     */
    url?: string;
    /**
     * @schemaDescription Display title shown above the component.
     * @ukrainianText true
     */
    title?: string;
  };
  /**
   * @schemaDescription Tasks value consumed by this component.
   * @ukrainianText true
   */
  tasks: string[];
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
}

export default function ReadingActivity({
  title,
  context = '',
  text = '',
  source = '',
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
          {text ? (
            // Seminar mode: inline primary source text
            <div className={styles.primarySource}>
              {parseMarkdown(text)}
              {source && (
                <p className={styles.sourceAttribution}>
                  <em>— {source}</em>
                </p>
              )}
            </div>
          ) : context ? (
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
