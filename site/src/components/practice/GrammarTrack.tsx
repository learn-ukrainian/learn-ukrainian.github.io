import type { ReactNode } from 'react';
import type { PracticeModeFilter } from '../../lib/lexicon/srs';
import {
  MECHANICS_DECK_META,
  type MechanicsPosKey,
} from '../../lib/lexicon/mechanics-deck-loader';

export interface GrammarTrackProps {
  chromeLocale: 'uk' | 'en';
  onSelectMechanicsMode: (pos: MechanicsPosKey) => void;
  renderBaseModeCard?: (mode: PracticeModeFilter) => ReactNode;
  caseSelectorNode?: ReactNode;
}

const ALL_MECHANICS_POS_KEYS: MechanicsPosKey[] = [
  'noun',
  'adjective',
  'verb',
  'pronoun',
  'numeral',
  'adverb',
  'function_words',
  'interjection',
];

export default function GrammarTrack({
  chromeLocale,
  onSelectMechanicsMode,
  renderBaseModeCard,
  caseSelectorNode,
}: GrammarTrackProps) {
  return (
    <section
      className="k3-track k3-track-grammar"
      aria-labelledby="track-grammar-title"
      data-testid="practice-track-grammar"
    >
      <div className="k3-track-header">
        <div className="k3-track-title-row">
          <h3 id="track-grammar-title" className="k3-track-title">
            {chromeLocale === 'uk' ? '🧩 Граматика та частини мови' : '🧩 Grammar & Parts of Speech'}
          </h3>
          <span className="k3-track-badge">{chromeLocale === 'uk' ? 'Трек 2' : 'Track 2'}</span>
        </div>
        <p className="k3-track-desc">
          {chromeLocale === 'uk'
            ? 'Відмінювання, форми слів, 10 частин мови та наголошування'
            : 'Declension, word forms, 10 parts of speech, and accentuation'}
        </p>
      </div>

      {/* Subgroup 1: 10 Parts of Speech Deep Mechanics Interactive Cards */}
      <div className="k3-pos-mechanics-section" style={{ marginBottom: '1.25rem' }}>
        <h4
          style={{
            fontSize: '1rem',
            fontWeight: 600,
            marginBottom: '0.75rem',
            color: 'var(--sl-color-gray-2)',
          }}
        >
          {chromeLocale === 'uk'
            ? '🎯 Тренажери 10 частин мови (Правопис 2019)'
            : '🎯 10 Parts of Speech Drills (Pravopys 2019)'}
        </h4>

        <div
          className="k3-mode-grid"
          role="group"
          aria-label={chromeLocale === 'uk' ? 'Частини мови' : 'Parts of speech drills'}
          data-testid="practice-pos-mechanics-grid"
        >
          {ALL_MECHANICS_POS_KEYS.map((posKey) => {
            const meta = MECHANICS_DECK_META[posKey];
            return (
              <button
                key={posKey}
                type="button"
                className="k3-mode-card"
                data-mechanics-mode={posKey}
                data-pos-mechanics={posKey}
                data-accent={meta.accent}
                data-mode-count={meta.itemCount}
                data-testid={`practice-card-mechanics-${posKey}`}
                onClick={() => onSelectMechanicsMode(posKey)}
              >
                <span className="k3-mode-title">
                  {chromeLocale === 'uk' ? meta.titleUk : meta.titleEn}
                </span>
                <span className="k3-mode-step">
                  {chromeLocale === 'uk' ? 'Частина мови' : 'Part of Speech'}
                </span>
                <span className="k3-mode-desc">
                  {chromeLocale === 'uk' ? meta.descriptionUk : meta.descriptionEn}
                </span>
                <span
                  className="k3-mode-count"
                  data-testid={`practice-mode-count-mechanics-${posKey}`}
                >
                  <span aria-hidden="true">{meta.itemCount}</span>
                  <span className="sr-only">
                    {chromeLocale === 'uk' ? `${meta.itemCount} завдань` : `${meta.itemCount} items`}
                  </span>
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Subgroup 2: Core Grammar & Accentuation Drills (Classify, Stress, Paradigm, Imperative) */}
      {renderBaseModeCard ? (
        <div className="k3-base-grammar-section" style={{ marginBottom: '1.25rem' }}>
          <h4
            style={{
              fontSize: '1rem',
              fontWeight: 600,
              marginBottom: '0.75rem',
              color: 'var(--sl-color-gray-2)',
            }}
          >
            {chromeLocale === 'uk'
              ? '⚡ Додаткові граматичні тренажери'
              : '⚡ Additional Grammar Drills'}
          </h4>
          <div
            className="k3-mode-grid"
            role="group"
            aria-label={chromeLocale === 'uk' ? 'Додаткові тренажери' : 'Additional drills'}
          >
            {renderBaseModeCard('classify')}
            {renderBaseModeCard('stress')}
            {renderBaseModeCard('paradigm')}
            {renderBaseModeCard('imperative')}
          </div>
        </div>
      ) : null}

      {/* Case filter for noun declension */}
      {caseSelectorNode ? (
        <div className="k3-case-selector-container" style={{ marginTop: '1rem' }}>
          <div className="k3-case-selector-intro" style={{ marginBottom: '0.5rem' }}>
            <span className="k3-case-selector-title" style={{ fontWeight: 600 }}>
              {chromeLocale === 'uk' ? 'Фільтр відмінків для іменників:' : 'Case filter for noun drills:'}
            </span>{' '}
            <span className="k3-case-selector-subtitle" style={{ fontSize: '0.85rem', color: 'var(--sl-color-gray-3)' }}>
              {chromeLocale === 'uk' ? 'Оберіть відмінки для фокусного тренування парадигм' : 'Select cases to focus on in paradigm drills'}
            </span>
          </div>
          {caseSelectorNode}
        </div>
      ) : null}
    </section>
  );
}
