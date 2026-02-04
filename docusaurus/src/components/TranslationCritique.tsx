import React, { useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { parseMarkdown } from './utils';

interface Translation {
  translator: string;
  text: string;
  accuracyScore: number;
  notes: string;
}

interface TranslationCritiqueProps {
  title: string;
  instruction?: string;
  original: string;
  translations: Translation[];
  focusPoints?: string[];
  isUkrainian?: boolean;
}

export default function TranslationCritique({
  title,
  instruction,
  original,
  translations,
  focusPoints = [],
  isUkrainian = true
}: TranslationCritiqueProps) {
  const [selectedTranslation, setSelectedTranslation] = useState<number | null>(null);
  const [showExpertVerdict, setShowExpertVerdict] = useState<Record<number, boolean>>({});
  const [showAllVerdicts, setShowAllVerdicts] = useState(false);

  const headerLabel = isUkrainian ? 'Критика перекладу' : 'Translation Critique';
  const originalLabel = isUkrainian ? 'Оригінал' : 'Original';
  const translationsLabel = isUkrainian ? 'Переклади' : 'Translations';
  const showVerdictLabel = isUkrainian ? 'Показати оцінку' : 'Show Verdict';
  const hideVerdictLabel = isUkrainian ? 'Сховати оцінку' : 'Hide Verdict';
  const showAllLabel = isUkrainian ? 'Показати всі оцінки' : 'Show All Verdicts';
  const accuracyLabel = isUkrainian ? 'Точність' : 'Accuracy';
  const focusPointsLabel = isUkrainian ? 'Ключові слова для аналізу:' : 'Focus points:';
  const expertNotesLabel = isUkrainian ? 'Експертна оцінка:' : 'Expert notes:';

  const toggleVerdict = (index: number) => {
    setShowExpertVerdict({
      ...showExpertVerdict,
      [index]: !showExpertVerdict[index]
    });
  };

  const revealAll = () => {
    const allVerdicts: Record<number, boolean> = {};
    translations.forEach((_, i) => {
      allVerdicts[i] = true;
    });
    setShowExpertVerdict(allVerdicts);
    setShowAllVerdicts(true);
  };

  const getScoreColor = (score: number) => {
    if (score >= 8) return styles.scoreHigh;
    if (score >= 5) return styles.scoreMedium;
    return styles.scoreLow;
  };

  const highlightFocusPoints = (text: string) => {
    let highlighted = text;
    focusPoints.forEach(point => {
      if (point) {
        const regex = new RegExp(`(${point.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        highlighted = highlighted.replace(regex, `<mark class="${styles.focusHighlight}">$1</mark>`);
      }
    });
    return highlighted;
  };

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>🔍</span>
        <span>{title || headerLabel}</span>
        <ActivityHelp activityType="translation-critique" isUkrainian={isUkrainian} />
      </div>
      <div className={styles.activityContent}>
        {instruction && (
          <div className={styles.readingContext}>
            {parseMarkdown(instruction)}
          </div>
        )}

        {/* Original text */}
        <div className={styles.originalTextSection}>
          <h4>{originalLabel}</h4>
          <div
            className={styles.archaicText}
            dangerouslySetInnerHTML={{
              __html: focusPoints.length > 0 ? highlightFocusPoints(original) : original
            }}
          />
        </div>

        {/* Focus points */}
        {focusPoints.length > 0 && (
          <div className={styles.focusPointsSection}>
            <strong>{focusPointsLabel}</strong>
            <div className={styles.focusPointsList}>
              {focusPoints.map((point, i) => (
                <span key={i} className={styles.focusPointTag}>{point}</span>
              ))}
            </div>
          </div>
        )}

        {/* Translations */}
        <div className={styles.translationsSection}>
          <h4>{translationsLabel}</h4>
          <div className={styles.translationCards}>
            {translations.map((translation, index) => (
              <div
                key={index}
                className={`${styles.translationCard} ${selectedTranslation === index ? styles.translationSelected : ''}`}
                onClick={() => setSelectedTranslation(index)}
              >
                <div className={styles.translationHeader}>
                  <span className={styles.translatorName}>{translation.translator}</span>
                  {(showExpertVerdict[index] || showAllVerdicts) && (
                    <span className={`${styles.accuracyScore} ${getScoreColor(translation.accuracyScore)}`}>
                      {accuracyLabel}: {translation.accuracyScore}/10
                    </span>
                  )}
                </div>
                <div
                  className={styles.translationText}
                  dangerouslySetInnerHTML={{
                    __html: focusPoints.length > 0 ? highlightFocusPoints(translation.text) : translation.text
                  }}
                />
                {(showExpertVerdict[index] || showAllVerdicts) && (
                  <div className={styles.expertVerdict}>
                    <strong>{expertNotesLabel}</strong>
                    <p>{parseMarkdown(translation.notes)}</p>
                  </div>
                )}
                <button
                  className={styles.secondaryButton}
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleVerdict(index);
                  }}
                >
                  {showExpertVerdict[index] ? hideVerdictLabel : showVerdictLabel}
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className={styles.buttonRow}>
          <button className={styles.submitButton} onClick={revealAll}>
            {showAllLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
