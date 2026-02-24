import React, { useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { parseMarkdown } from './utils';

interface Hotspot {
  x: number;
  y: number;
  label: string;
  explanation: string;
}

interface PaleographyAnalysisProps {
  title: string;
  instruction?: string;
  imageUrl: string;
  hotspots: Hotspot[];
  options?: string[];
  isUkrainian?: boolean;
}

export default function PaleographyAnalysis({
  title,
  instruction,
  imageUrl,
  hotspots,
  options = [],
  isUkrainian = true
}: PaleographyAnalysisProps) {
  const [selectedHotspot, setSelectedHotspot] = useState<number | null>(null);
  const [userAnswers, setUserAnswers] = useState<Record<number, string>>({});
  const [showResults, setShowResults] = useState<Record<number, boolean>>({});
  const [revealedAll, setRevealedAll] = useState(false);

  const headerLabel = isUkrainian ? 'Палеографічний аналіз' : 'Paleography Analysis';
  const selectFeatureLabel = isUkrainian ? 'Оберіть тип:' : 'Select feature type:';
  const checkLabel = isUkrainian ? 'Перевірити' : 'Check';
  const showAllLabel = isUkrainian ? 'Показати всі' : 'Show All';
  const correctLabel = isUkrainian ? 'Правильно!' : 'Correct!';
  const incorrectLabel = isUkrainian ? 'Неправильно' : 'Incorrect';
  const clickHotspotLabel = isUkrainian ? 'Натисніть на позначку для аналізу' : 'Click a hotspot to analyze';

  const handleHotspotClick = (index: number) => {
    setSelectedHotspot(index);
  };

  const handleAnswer = (index: number, answer: string) => {
    setUserAnswers({ ...userAnswers, [index]: answer });
  };

  const checkAnswer = (index: number) => {
    setShowResults({ ...showResults, [index]: true });
  };

  const isCorrect = (index: number) => {
    const userAnswer = userAnswers[index]?.toLowerCase().trim();
    const correctAnswer = hotspots[index].label.toLowerCase().trim();
    return userAnswer === correctAnswer;
  };

  const revealAll = () => {
    setRevealedAll(true);
    const allResults: Record<number, boolean> = {};
    hotspots.forEach((_, i) => {
      allResults[i] = true;
    });
    setShowResults(allResults);
  };

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>📜</span>
        <span>{title || headerLabel}</span>
        <ActivityHelp activityType="paleography-analysis" isUkrainian={isUkrainian} />
      </div>
      <div className={styles.activityContent}>
        {instruction && (
          <div className={styles.readingContext}>
            {parseMarkdown(instruction)}
          </div>
        )}

        {/* Manuscript image with hotspots */}
        <div className={styles.paleographyContainer}>
          <div className={styles.manuscriptWrapper}>
            <img
              src={imageUrl}
              alt="Manuscript"
              className={styles.manuscriptImage}
            />
            {hotspots.map((hotspot, index) => (
              <button
                key={index}
                className={`${styles.hotspot} ${selectedHotspot === index ? styles.hotspotActive : ''} ${showResults[index] ? (isCorrect(index) || revealedAll ? styles.hotspotCorrect : styles.hotspotIncorrect) : ''}`}
                style={{ left: `${hotspot.x}%`, top: `${hotspot.y}%` }}
                onClick={() => handleHotspotClick(index)}
                title={`Hotspot ${index + 1}`}
              >
                {index + 1}
              </button>
            ))}
          </div>
        </div>

        {/* Selected hotspot analysis panel */}
        {selectedHotspot !== null && (
          <div className={styles.hotspotPanel}>
            <h4>{isUkrainian ? `Позначка ${selectedHotspot + 1}` : `Hotspot ${selectedHotspot + 1}`}</h4>

            {!showResults[selectedHotspot] && !revealedAll ? (
              <>
                <p>{selectFeatureLabel}</p>
                {options.length > 0 ? (
                  <select
                    value={userAnswers[selectedHotspot] || ''}
                    onChange={(e) => handleAnswer(selectedHotspot, e.target.value)}
                    className={styles.featureSelect}
                  >
                    <option value="">{isUkrainian ? '-- Оберіть --' : '-- Select --'}</option>
                    {options.map((opt, i) => (
                      <option key={i} value={opt}>{opt}</option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="text"
                    value={userAnswers[selectedHotspot] || ''}
                    onChange={(e) => handleAnswer(selectedHotspot, e.target.value)}
                    placeholder={isUkrainian ? 'Введіть назву елемента' : 'Enter feature name'}
                    className={styles.featureInput}
                  />
                )}
                <button
                  className={styles.submitButton}
                  onClick={() => checkAnswer(selectedHotspot)}
                  disabled={!userAnswers[selectedHotspot]}
                >
                  {checkLabel}
                </button>
              </>
            ) : (
              <div className={`${styles.feedback} ${isCorrect(selectedHotspot) || revealedAll ? styles.success : styles.error}`}>
                {!revealedAll && (isCorrect(selectedHotspot) ? correctLabel : incorrectLabel)}
                <div className={styles.hotspotExplanation}>
                  <strong>{hotspots[selectedHotspot].label}</strong>
                  <p>{parseMarkdown(hotspots[selectedHotspot].explanation)}</p>
                </div>
              </div>
            )}
          </div>
        )}

        {selectedHotspot === null && (
          <p className={styles.instructionText}>{clickHotspotLabel}</p>
        )}

        <div className={styles.buttonRow}>
          <button className={styles.secondaryButton} onClick={revealAll}>
            {showAllLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
