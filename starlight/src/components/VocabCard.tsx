import React, { useState } from 'react';
import directStyles from './Direct.module.css';

interface VocabEntry {
  /**
   * @schemaDescription Ukrainian word shown to the learner.
   * @ukrainianText true
   */
  word: string;
  /**
   * @schemaDescription Emoji value consumed by this component.
   * @ukrainianText false
   */
  emoji?: string;
  /**
   * @schemaDescription Image url value consumed by this component.
   * @ukrainianText false
   */
  image_url?: string | null;
  /**
   * @schemaDescription Pronunciation video value consumed by this component.
   * @ukrainianText false
   */
  pronunciation_video?: string;
  /**
   * @schemaDescription Examples value consumed by this component.
   * @ukrainianText true
   */
  examples: string[];
  /**
   * @schemaDescription Category label used by the activity.
   * @ukrainianText true
   */
  category?: string;
  /**
   * @schemaDescription Question value consumed by this component.
   * @ukrainianText true
   */
  question?: string;
}

interface VocabCardProps {
  /**
   * @schemaDescription Words shown to the learner.
   * @ukrainianText true
   */
  words: VocabEntry[];
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

function SingleVocabCard({
  entry,
  isUkrainian,
}: {
  entry: VocabEntry;
  isUkrainian: boolean;
}) {
  const [showVideo, setShowVideo] = useState(false);
  const videoId = entry.pronunciation_video
    ? extractVideoId(entry.pronunciation_video)
    : null;

  const listenLabel = isUkrainian ? '🔊 Послухати' : '🔊 Listen';

  return (
    <div className={directStyles.vocabCard}>
      <div className={directStyles.vocabCardVisual}>
        {entry.image_url ? (
          <img
            src={entry.image_url}
            alt={entry.word}
            className={directStyles.vocabCardImage}
            loading="lazy"
          />
        ) : entry.emoji ? (
          <span className={directStyles.vocabCardEmoji}>{entry.emoji}</span>
        ) : null}
      </div>

      <div className={directStyles.vocabCardContent}>
        <div className={directStyles.vocabCardWord}>{entry.word}</div>

        {entry.question && (
          <span className={directStyles.vocabCardQuestion}>
            {entry.question}
          </span>
        )}

        {videoId && (
          <button
            className={directStyles.vocabCardPlayBtn}
            onClick={() => setShowVideo(!showVideo)}
          >
            {listenLabel}
          </button>
        )}

        {showVideo && videoId && (
          <div className={directStyles.vocabCardVideoWrapper}>
            <iframe
              src={`https://www.youtube.com/embed/${videoId}?rel=0&autoplay=1`}
              title={entry.word}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope"
              allowFullScreen
              loading="lazy"
              className={directStyles.vocabCardVideo}
            />
          </div>
        )}

        {entry.examples.length > 0 && (
          <ul className={directStyles.vocabCardExamples}>
            {entry.examples.map((ex, i) => (
              <li key={i}>{ex}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default function VocabCard({
  words,
  title,
  isUkrainian = true,
}: VocabCardProps) {
  if (!words || words.length === 0) return null;

  const headerLabel =
    title || (isUkrainian ? 'Нові слова' : 'New Words');

  return (
    <div className={directStyles.vocabCardsContainer}>
      <h3 className={directStyles.vocabCardsTitle}>{headerLabel}</h3>
      <div className={directStyles.vocabCards}>
        {words.map((entry) => (
          <SingleVocabCard
            key={entry.word}
            entry={entry}
            isUkrainian={isUkrainian}
          />
        ))}
      </div>
    </div>
  );
}
