import React from 'react';
import directStyles from './Direct.module.css';

interface LetterEntry {
  /**
   * @schemaDescription Upper value consumed by this component.
   * @ukrainianText true
   */
  upper: string;
  /**
   * @schemaDescription Lower value consumed by this component.
   * @ukrainianText true
   */
  lower: string;
  /**
   * @schemaDescription Emoji value consumed by this component.
   * @ukrainianText false
   */
  emoji: string;
  /**
   * @schemaDescription Key word value consumed by this component.
   * @ukrainianText true
   */
  key_word: string;
  /**
   * @schemaDescription Note value consumed by this component.
   * @ukrainianText false
   */
  note?: string;
  /**
   * @schemaDescription Sound type value consumed by this component.
   * @ukrainianText false
   */
  sound_type?: string;
}

interface LetterGridProps {
  /**
   * @schemaDescription Letters value consumed by this component.
   * @ukrainianText true
   */
  letters: LetterEntry[];
  /**
   * @schemaDescription Display title shown above the component.
   * @ukrainianText true
   */
  title?: string;
}

export default function LetterGrid({ letters, title }: LetterGridProps) {
  if (!letters || letters.length === 0) return null;

  return (
    <div className={directStyles.letterGridContainer} data-activity="letter-grid">
      {title && <h3 className={directStyles.letterGridTitle}>{title}</h3>}
      <div className={directStyles.letterGrid}>
        {letters.map((letter) => (
          <div
            key={letter.upper}
            className={`${directStyles.letterCard} ${
              letter.sound_type === 'vowel'
                ? directStyles.letterCardVowel
                : letter.sound_type === 'special'
                ? directStyles.letterCardSpecial
                : directStyles.letterCardConsonant
            }`}
            data-activity="letter-card"
            data-upper={letter.upper}
            data-sound-type={letter.sound_type || 'consonant'}
          >
            <div className={directStyles.letterCardUpper}>{letter.upper}</div>
            <div className={directStyles.letterCardLower}>{letter.lower}</div>
            <div className={directStyles.letterCardEmoji}>{letter.emoji}</div>
            <div className={directStyles.letterCardWord}>{letter.key_word}</div>
            {letter.note && (
              <div className={directStyles.letterCardNote}>{letter.note}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
