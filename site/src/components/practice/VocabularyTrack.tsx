import type { ReactNode } from 'react';
import type { PracticeModeFilter } from '../../lib/lexicon/srs';
import type { WeakArea } from '../../lib/lexicon/weak-areas';

export interface VocabularyTrackProps {
  chromeLocale: 'uk' | 'en';
  weakChips: WeakArea[];
  onStartWeakAreaFocus: (weakness: WeakArea) => void;
  renderModeCard: (mode: PracticeModeFilter, isRecommended?: boolean) => ReactNode;
}

export const VOCAB_PRIMARY_MODES: PracticeModeFilter[] = ['mixed', 'flashcards', 'cloze'];
export const LEXICAL_RELATIONS_MODES: PracticeModeFilter[] = [
  'synonym',
  'antonym',
  'paronym',
  'homonym',
  'heritage',
];

export default function VocabularyTrack({
  chromeLocale,
  weakChips,
  onStartWeakAreaFocus,
  renderModeCard,
}: VocabularyTrackProps) {
  return (
    <section className="k3-track k3-track-vocab" aria-labelledby="track-vocab-title" data-testid="practice-track-vocab">
      {/* Weak Areas Banner (if any) */}
      {weakChips.length > 0 ? (
        <div className="lexicon-weak-areas" data-testid="practice-weak-areas" style={{ marginBottom: '1.25rem' }}>
          <div
            className="lexicon-weak-chips"
            role="group"
            aria-label={chromeLocale === 'uk' ? 'Слабкі місця для повторення' : 'Weak areas for review'}
            style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}
          >
            {weakChips.map((weakness) => (
              <button
                type="button"
                key={`${weakness.dimension}:${weakness.key}`}
                className="lexicon-weak-chip"
                data-testid={`practice-weak-chip-${weakness.key}`}
                onClick={() => onStartWeakAreaFocus(weakness)}
              >
                {weakness.label}
              </button>
            ))}
          </div>
        </div>
      ) : null}

      <div className="k3-track-header">
        <div className="k3-track-title-row">
          <h3 id="track-vocab-title" className="k3-track-title">
            {chromeLocale === 'uk' ? '📖 Словниковий запас' : '📖 Vocabulary'}
          </h3>
          <span className="k3-track-badge">{chromeLocale === 'uk' ? 'Трек 1' : 'Track 1'}</span>
        </div>
        <p className="k3-track-desc">
          {chromeLocale === 'uk'
            ? 'Опанування слів, значень, контексту та лексичних зв’язків'
            : 'Master words, meanings, context, and lexical relations'}
        </p>
      </div>

      {/* Primary Vocabulary Modes Grid */}
      <div
        className="k3-mode-grid"
        role="group"
        aria-label={chromeLocale === 'uk' ? 'Словниковий запас' : 'Vocabulary modes'}
      >
        {VOCAB_PRIMARY_MODES.map((mode) => renderModeCard(mode, mode === 'mixed'))}
      </div>

      {/* Expandable Lexical Relations Group */}
      <details className="k3-track-subgroup" style={{ marginTop: '1rem' }}>
        <summary style={{ cursor: 'pointer', userSelect: 'none', fontWeight: 600 }}>
          <span>
            {chromeLocale === 'uk'
              ? '🔗 Лексичні зв’язки (синоніми, пароніми, омоніми, питома лексика)'
              : '🔗 Lexical Relations (synonyms, paronyms, homonyms, heritage)'}
          </span>
        </summary>
        <div
          className="k3-mode-grid"
          role="group"
          aria-label={chromeLocale === 'uk' ? 'Лексичні зв’язки' : 'Lexical relations'}
          style={{ marginTop: '0.75rem' }}
        >
          {LEXICAL_RELATIONS_MODES.map((mode) => renderModeCard(mode, false))}
        </div>
      </details>
    </section>
  );
}
