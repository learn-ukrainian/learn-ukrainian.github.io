import React, { useState } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import { parseMarkdown } from './utils';

interface VariantItem {
  /**
   * @schemaDescription Display label for one regional or textual variant.
   * @ukrainianText true
   */
  label: string;
  /**
   * @schemaDescription Variant excerpt or description.
   * @ukrainianText true
   */
  text?: string;
  /**
   * @schemaDescription Region associated with this variant.
   * @ukrainianText true
   */
  region?: string;
  /**
   * @schemaDescription Source label for this variant.
   * @ukrainianText false
   */
  source?: string;
}

interface VariantComparisonProps {
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
   * @schemaDescription Regional or textual variants to compare.
   * @ukrainianText true
   */
  variants: VariantItem[];
  /**
   * @schemaDescription Feature rows learners compare across variants.
   * @ukrainianText true
   */
  features: string[];
  /**
   * @schemaDescription Prompt shown to guide the learner response.
   * @ukrainianText true
   */
  prompt?: string;
  /**
   * @schemaDescription Model answer for review or self-check.
   * @ukrainianText true
   */
  modelAnswer?: string;
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
}

export default function VariantComparison({
  title,
  instruction,
  variants,
  features,
  prompt,
  modelAnswer,
  isUkrainian
}: VariantComparisonProps) {
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [showModel, setShowModel] = useState(false);

  const headerLabel = isUkrainian ? 'Порівняння варіантів' : 'Variant Comparison';
  const promptLabel = isUkrainian ? 'Завдання:' : 'Task:';
  const placeholder = isUkrainian ? 'Ваша ознака...' : 'Your note...';
  const modelLabel = isUkrainian ? (showModel ? 'Приховати зразок' : 'Показати зразок') : (showModel ? 'Hide model' : 'Show model');

  const updateCell = (feature: string, label: string, value: string) => {
    setResponses(prev => ({ ...prev, [`${feature}::${label}`]: value }));
  };

  return (
    <div className={styles.activityContainer}>
      <div className={styles.activityHeader}>
        <span className={`${styles.exerciseBadge} ${styles.badgeVariant}`}>#43</span>
        <span>{title || headerLabel}</span>
        <ActivityHelp activityType="variant-comparison" isUkrainian={isUkrainian} />
      </div>
      <div className={styles.activityContent}>
        {instruction && <p className={styles.instruction}><strong>{instruction}</strong></p>}

        <div className={styles.variantCards}>
          {variants.map(variant => (
            <div className={styles.variantCard} key={variant.label}>
              <div className={styles.variantLabel}>{variant.label}</div>
              {variant.region && <div className={styles.variantMeta}>{variant.region}</div>}
              {variant.text && <div className={styles.variantText}>{parseMarkdown(variant.text)}</div>}
              {variant.source && <div className={styles.variantSource}>{variant.source}</div>}
            </div>
          ))}
        </div>

        {prompt && <div className={styles.essayPrompt}><strong>{promptLabel}</strong> {parseMarkdown(prompt)}</div>}

        <div className={styles.variantTableWrap}>
          <table className={styles.variantTable}>
            <thead>
              <tr>
                <th>{isUkrainian ? 'Ознака' : 'Feature'}</th>
                {variants.map(variant => <th key={variant.label}>{variant.label}</th>)}
              </tr>
            </thead>
            <tbody>
              {features.map(feature => (
                <tr key={feature}>
                  <td><strong>{feature}</strong></td>
                  {variants.map(variant => (
                    <td key={`${feature}-${variant.label}`}>
                      <input
                        value={responses[`${feature}::${variant.label}`] || ''}
                        onChange={event => updateCell(feature, variant.label, event.target.value)}
                        placeholder={placeholder}
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {modelAnswer && (
          <div className={styles.buttonRow}>
            <button className={styles.submitButton} onClick={() => setShowModel(!showModel)}>
              {modelLabel}
            </button>
          </div>
        )}

        {showModel && modelAnswer && (
          <div className={`${styles.feedback} ${styles.modelAnswer}`}>
            {parseMarkdown(modelAnswer)}
          </div>
        )}
      </div>
    </div>
  );
}
