import React, { useState } from 'react';
import styles from './Activities.module.css';
import directStyles from './Direct.module.css';

interface WatchAndRepeatItem {
  /**
   * @schemaDescription Video value consumed by this component.
   * @ukrainianText false
   */
  video: string;
  /**
   * @schemaDescription Letter value consumed by this component.
   * @ukrainianText false
   */
  letter?: string;
  /**
   * @schemaDescription Ukrainian word shown to the learner.
   * @ukrainianText true
   */
  word?: string;
  /**
   * @schemaDescription Note value consumed by this component.
   * @ukrainianText false
   */
  note?: string;
}

interface WatchAndRepeatProps {
  /**
   * @schemaDescription Array of activity items rendered by the component.
   * @ukrainianText true
   */
  items: WatchAndRepeatItem[];
  /**
   * @schemaDescription Display title shown above the component.
   * @ukrainianText true
   */
  title?: string;
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
}

function extractVideoId(url: string): string | null {
  const match = url.match(/(?:v=|\/embed\/|youtu\.be\/)([A-Za-z0-9_-]{11})/);
  return match ? match[1] : null;
}

export default function WatchAndRepeat({
  items,
  title,
  isUkrainian = true,
}: WatchAndRepeatProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  // Only load iframe after user clicks play — avoids YouTube bot detection
  const [playing, setPlaying] = useState(false);

  if (!items || items.length === 0) return null;

  const item = items[currentIndex];
  const videoId = extractVideoId(item.video);
  const total = items.length;

  const prevLabel = isUkrainian ? '← Назад' : '← Back';
  const nextLabel = isUkrainian ? 'Далі →' : 'Next →';
  const repeatLabel = isUkrainian ? 'Повтори!' : 'Repeat!';
  const playLabel = isUkrainian ? '▶ Дивитись відео' : '▶ Play video';
  const headerLabel = title || (isUkrainian ? 'Дивись і повторюй' : 'Watch and Repeat');

  const goTo = (idx: number) => {
    setCurrentIndex(idx);
    setPlaying(false); // reset to thumbnail when switching items
  };

  return (
    <div
      className={styles.activityContainer}
      data-activity="watch-and-repeat"
      data-current-index={currentIndex}
      data-total={total}
    >
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>🔊</span>
        <span>{headerLabel}</span>
      </div>

      <div className={directStyles.warProgress} data-activity="war-progress">
        <span>
          {currentIndex + 1} / {total}
        </span>
        <div className={directStyles.warProgressBar}>
          <div
            className={directStyles.warProgressFill}
            style={{ width: `${((currentIndex + 1) / total) * 100}%` }}
          />
        </div>
      </div>

      <div className={directStyles.warCard} data-activity="war-card">
        {item.letter && (
          <div className={directStyles.warLetterDisplay}>{item.letter}</div>
        )}
        {item.word && !item.letter && (
          <div className={directStyles.warWordDisplay}>{item.word}</div>
        )}

        {videoId ? (
          playing ? (
            <div className={directStyles.warVideoWrapper} data-activity="war-video">
              <iframe
                key={videoId}
                src={`https://www.youtube.com/embed/${videoId}?rel=0&autoplay=1`}
                title={item.letter || item.word || 'Video'}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                className={directStyles.warVideo}
              />
            </div>
          ) : (
            <button
              className={directStyles.warThumbnailBtn}
              data-activity="war-thumbnail"
              onClick={() => setPlaying(true)}
              aria-label={playLabel}
            >
              <img
                src={`https://img.youtube.com/vi/${videoId}/hqdefault.jpg`}
                alt={item.letter || item.word || 'Video thumbnail'}
                className={directStyles.warThumbnail}
                loading="lazy"
              />
              <span className={directStyles.warPlayIcon}>▶</span>
            </button>
          )
        ) : (
          <p style={{ color: 'var(--ifm-color-emphasis-500)' }}>
            Video unavailable
          </p>
        )}

        <div className={directStyles.warRepeatPrompt}>{repeatLabel}</div>

        {item.note && (
          <p className={directStyles.warNote}>{item.note}</p>
        )}
      </div>

      <div className={directStyles.warNav} data-activity="war-nav">
        <button
          className={directStyles.warNavButton}
          data-activity="war-prev"
          onClick={() => goTo(Math.max(0, currentIndex - 1))}
          disabled={currentIndex === 0}
        >
          {prevLabel}
        </button>
        <button
          className={directStyles.warNavButton}
          data-activity="war-next"
          onClick={() => goTo(Math.min(total - 1, currentIndex + 1))}
          disabled={currentIndex === total - 1}
        >
          {nextLabel}
        </button>
      </div>
    </div>
  );
}
