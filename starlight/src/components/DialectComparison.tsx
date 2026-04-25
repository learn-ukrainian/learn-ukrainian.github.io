import React, { useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { parseMarkdown } from './utils';

interface Feature {
  /**
   * @schemaDescription Feature Name value consumed by this component.
   * @ukrainianText true
   */
  featureName: string;
  /**
   * @schemaDescription Value A value consumed by this component.
   * @ukrainianText true
   */
  valueA: string;
  /**
   * @schemaDescription Value B value consumed by this component.
   * @ukrainianText true
   */
  valueB: string;
  /**
   * @schemaDescription Feedback explanation shown after the learner answers.
   * @ukrainianText true
   */
  explanation: string;
}

interface DialectComparisonProps {
  /**
   * @schemaDescription Display title shown above the component.
   * @ukrainianText true
   */
  title: string;
  /**
   * @schemaDescription Instruction shown to the learner above the activity.
   * @ukrainianText true
   */
  instruction?: string;
  /**
   * @schemaDescription Text A value consumed by this component.
   * @ukrainianText maybe
   */
  textA: string;
  /**
   * @schemaDescription Text B value consumed by this component.
   * @ukrainianText maybe
   */
  textB: string;
  /**
   * @schemaDescription Label A value consumed by this component.
   * @ukrainianText false
   */
  labelA?: string;
  /**
   * @schemaDescription Label B value consumed by this component.
   * @ukrainianText false
   */
  labelB?: string;
  /**
   * @schemaDescription Features value consumed by this component.
   * @ukrainianText true
   */
  features: Feature[];
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
}

export default function DialectComparison({
  title,
  instruction,
  textA,
  textB,
  labelA,
  labelB,
  features,
  isUkrainian = true
}: DialectComparisonProps) {
  const [selectedFeature, setSelectedFeature] = useState<number | null>(null);
  const [showAllFeatures, setShowAllFeatures] = useState(false);

  const headerLabel = isUkrainian ? 'Порівняння діалектів' : 'Dialect Comparison';
  const defaultLabelA = isUkrainian ? 'Текст А' : 'Text A';
  const defaultLabelB = isUkrainian ? 'Текст Б' : 'Text B';
  const showFeaturesLabel = isUkrainian ? 'Показати відмінності' : 'Show Differences';
  const hideFeaturesLabel = isUkrainian ? 'Сховати відмінності' : 'Hide Differences';
  const featureLabel = isUkrainian ? 'Особливість' : 'Feature';
  const explanationLabel = isUkrainian ? 'Пояснення' : 'Explanation';

  const highlightText = (text: string, values: string[]) => {
    let highlighted = text;
    values.forEach(value => {
      if (value) {
        const regex = new RegExp(`(${value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        highlighted = highlighted.replace(regex, `<mark class="${styles.dialectHighlight}">$1</mark>`);
      }
    });
    return highlighted;
  };

  const valuesA = features.map(f => f.valueA);
  const valuesB = features.map(f => f.valueB);

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>🔀</span>
        <span>{title || headerLabel}</span>
        <ActivityHelp activityType="dialect-comparison" isUkrainian={isUkrainian} />
      </div>
      <div className={styles.activityContent}>
        {instruction && (
          <div className={styles.readingContext}>
            {parseMarkdown(instruction)}
          </div>
        )}

        {/* Split-screen text comparison */}
        <div className={styles.dialectSplit}>
          <div className={styles.dialectPane}>
            <h4 className={styles.dialectLabel}>{labelA || defaultLabelA}</h4>
            <div
              className={styles.dialectText}
              dangerouslySetInnerHTML={{
                __html: showAllFeatures ? highlightText(textA, valuesA) : textA
              }}
            />
          </div>
          <div className={styles.dialectDivider} />
          <div className={styles.dialectPane}>
            <h4 className={styles.dialectLabel}>{labelB || defaultLabelB}</h4>
            <div
              className={styles.dialectText}
              dangerouslySetInnerHTML={{
                __html: showAllFeatures ? highlightText(textB, valuesB) : textB
              }}
            />
          </div>
        </div>

        {/* Feature comparison table */}
        {showAllFeatures && (
          <div className={styles.featureTable}>
            <table>
              <thead>
                <tr>
                  <th>{featureLabel}</th>
                  <th>{labelA || defaultLabelA}</th>
                  <th>{labelB || defaultLabelB}</th>
                  <th>{explanationLabel}</th>
                </tr>
              </thead>
              <tbody>
                {features.map((feature, index) => (
                  <tr
                    key={index}
                    className={selectedFeature === index ? styles.featureSelected : ''}
                    onClick={() => setSelectedFeature(index)}
                  >
                    <td><strong>{feature.featureName}</strong></td>
                    <td className={styles.dialectValueA}>{feature.valueA}</td>
                    <td className={styles.dialectValueB}>{feature.valueB}</td>
                    <td>{parseMarkdown(feature.explanation)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className={styles.buttonRow}>
          <button
            className={styles.submitButton}
            onClick={() => setShowAllFeatures(!showAllFeatures)}
          >
            {showAllFeatures ? hideFeaturesLabel : showFeaturesLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
