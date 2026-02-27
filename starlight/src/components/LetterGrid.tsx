import React from 'react';
import directStyles from './Direct.module.css';

interface LetterEntry {
  upper: string;
  lower: string;
  emoji: string;
  key_word: string;
  note?: string;
  sound_type?: string;
}

interface LetterGridProps {
  letters: LetterEntry[];
  title?: string;
}

export default function LetterGrid({ letters, title }: LetterGridProps) {
  if (!letters || letters.length === 0) return null;

  return (
    <div className={directStyles.letterGridContainer}>
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
