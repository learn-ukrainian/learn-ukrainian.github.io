import { useMemo, useState } from 'react';
import type {
  DailyPracticeDeckSnapshot,
  DailyPracticeRowState,
  PracticeLexeme,
} from '../lib/lexicon/srs';
import { formatLastSeenAgo, stripStressMarks } from '../lib/lexicon/srs';
import { CHROME_STRINGS, type ChromeLocale, type ChromeKey } from '../lib/i18n/chrome';
import ChromeText, { ChromeDual } from '../lib/i18n/ChromeText';
import type { CefrLevel } from '../lib/lexicon/levels';

export interface PracticeDailyDeckProps {
  snapshot: DailyPracticeDeckSnapshot;
  rows: {
    pendingDue: DailyPracticeRowState[];
    pendingNew: DailyPracticeRowState[];
    done: DailyPracticeRowState[];
  };
  lexemes: Map<string, PracticeLexeme>;
  atlasLemmaHref: (lemmaId: string) => string;
  chromeLocale: ChromeLocale;
  learnerLevel: CefrLevel;
}

const STATUS_META = {
  due: { glyph: '✦', labelKey: 'practice.statusDue' as const, colorVar: 'var(--lu-yellow-dark)' },
  new: { glyph: '↻', labelKey: 'practice.statusNew' as const, colorVar: 'var(--lu-blue)' },
  done: { glyph: '✓', labelKey: 'practice.statusDone' as const, colorVar: 'var(--lu-green)' },
};

function chromeString(locale: ChromeLocale, key: ChromeKey): string {
  return CHROME_STRINGS[locale][key];
}

export default function PracticeDailyDeck({
  snapshot,
  rows,
  lexemes,
  atlasLemmaHref,
  chromeLocale,
  learnerLevel,
}: PracticeDailyDeckProps) {
  const [previewIndex, setPreviewIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [detailsOpen, setDetailsOpen] = useState(false);

  const orderedRows = useMemo(
    () => [...rows.pendingDue, ...rows.pendingNew, ...rows.done],
    [rows],
  );

  const total = snapshot.items.length;
  const currentItem = orderedRows[previewIndex]?.item ?? null;
  const currentLemmaId = currentItem?.lemmaId ?? null;
  // The practice-lexemes map is OPTIONAL ENRICHMENT ONLY (ipa, an extra pos
  // tag) — most daily-pool picks are not in this much smaller map, so the
  // card must never depend on a hit here to render (#5852).
  const currentLexeme = currentLemmaId ? lexemes.get(currentLemmaId) ?? null : null;

  const handlePrevious = () => {
    setFlipped(false);
    setPreviewIndex((index) => (index > 0 ? index - 1 : total - 1));
  };

  const handleNext = () => {
    setFlipped(false);
    setPreviewIndex((index) => (index < total - 1 ? index + 1 : 0));
  };

  const handleFlip = () => {
    setFlipped((value) => !value);
  };

  const displayGloss = currentItem?.gloss ?? currentLexeme?.gloss ?? null;
  const displayCefr = currentItem?.cefr ?? currentLexeme?.cefr ?? null;
  const frontSubtitle = currentItem
    ? [currentLexeme?.ipa, currentLexeme?.pos, displayCefr].filter(Boolean).join(' · ')
    : '';
  const showStressMarks = learnerLevel === 'A1';
  const displayLemma = (lemma: string) => (showStressMarks ? lemma : stripStressMarks(lemma));
  const currentExample = currentLexeme?.example?.trim() || currentItem?.example?.trim() || null;
  const currentExampleEn = showStressMarks
    ? currentLexeme?.exampleEn?.trim() || currentItem?.exampleEn?.trim() || null
    : null;

  return (
    <div className="practice-daily-deck" data-testid="practice-daily-deck">
      <div className="daily-deck-header">
        <h2>
          <ChromeText k="practice.wordsTitle" />
        </h2>
        <span className="daily-deck-position" aria-live="polite">
          <ChromeDual
            uk={`${previewIndex + 1} з ${total}`}
            en={`${previewIndex + 1} / ${total}`}
          />
        </span>
      </div>

      <div className="daily-deck-preview-shell">
        <button
          type="button"
          className="daily-deck-nav"
          aria-label={chromeString(chromeLocale, 'label.previous')}
          onClick={handlePrevious}
        >
          ‹
        </button>

        <div
          className={`flashcard daily-preview-card${flipped ? ' flipped' : ''}`}
          data-flipped={flipped ? 'true' : 'false'}
          onClick={handleFlip}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              handleFlip();
            }
          }}
          role="button"
          tabIndex={0}
          aria-label={chromeString(chromeLocale, 'practice.tapToFlip')}
        >
          <div className="flashcard-inner">
            <div className="flashcard-front">
              {currentItem ? (
                <>
                  <span className="flashcard-word">{displayLemma(currentItem.lemma)}</span>
                  {frontSubtitle && <span className="flashcard-subtitle">{frontSubtitle}</span>}
                </>
              ) : (
                <span className="flashcard-word">—</span>
              )}
            </div>
            <div className="flashcard-back">
              {currentItem ? (
                <>
                  <span className="flashcard-word">{displayGloss ?? '—'}</span>
                  {currentLexeme?.pos && (
                    <span className="flashcard-subtitle">{currentLexeme.pos}</span>
                  )}
                  {currentExample ? (
                    <p className="daily-deck-example" data-testid="practice-daily-example" lang="uk">
                      {currentExample}
                      {currentExampleEn ? (
                        <span className="daily-deck-example-en" data-testid="practice-daily-example-en" lang="en">
                          {currentExampleEn}
                        </span>
                      ) : null}
                    </p>
                  ) : null}
                </>
              ) : (
                <span className="flashcard-word">—</span>
              )}
            </div>
          </div>
        </div>

        <button
          type="button"
          className="daily-deck-nav"
          aria-label={chromeString(chromeLocale, 'label.next')}
          onClick={handleNext}
        >
          ›
        </button>
      </div>

      <div className="daily-deck-preview-actions">
        {currentLemmaId && (
          <a
            href={atlasLemmaHref(currentLemmaId)}
            className="daily-deck-atlas-link"
            data-testid="practice-preview-atlas-link"
          >
            <ChromeText k="practice.openInAtlas" /> →
          </a>
        )}
        <div className="daily-deck-voice-slot" role="status" aria-live="polite">
          <span aria-hidden="true">🎙</span>
          <ChromeText k="practice.voiceSlot" />
        </div>
      </div>

      <details
        className="daily-deck-details"
        data-testid="practice-daily-details"
        open={detailsOpen}
        onToggle={(event) => setDetailsOpen(event.currentTarget.open)}
      >
        <summary data-testid="practice-daily-summary" aria-expanded={detailsOpen} aria-controls="daily-deck-rows">
          <ChromeText k={detailsOpen ? 'practice.hideWords' : 'practice.showWords'} />
          <span className="daily-deck-counters">
            <span className="counter due">
              {rows.pendingDue.length}
            </span>
            <span className="counter new">
              {rows.pendingNew.length}
            </span>
            <span className="counter done">
              {rows.done.length}
            </span>
          </span>
        </summary>

        <ol className="daily-deck-rows" id="daily-deck-rows">
          {orderedRows.map((row, index) => {
            const meta = STATUS_META[row.state];
            const entry = lexemes.get(row.item.lemmaId);
            const rowLemma = row.item.lemma || entry?.lemma || row.item.lemmaId;
            const rowGloss = row.item.gloss ?? entry?.gloss ?? null;
            const lastSeen = row.lastSeenAt === null ? null : formatLastSeenAgo(row.lastSeenAt);
            const why =
              row.state === 'due'
                ? {
                    uk: lastSeen ? `До повторення · ${lastSeen.uk}` : 'До повторення',
                    en: lastSeen ? `For review · ${lastSeen.en}` : 'For review',
                  }
                : row.state === 'new'
                  ? { uk: 'Нове слово', en: 'New word' }
                  : { uk: 'Вивчено · сьогодні', en: 'Done · today' };
            return (
              <li
                key={row.item.lemmaId}
                className={`daily-deck-row state-${row.state}`}
                data-state={row.state}
                style={{ '--row-accent': meta.colorVar } as React.CSSProperties}
              >
                <a
                  href={atlasLemmaHref(row.item.lemmaId)}
                  className="daily-deck-row-link"
                >
                  <span className="row-marker" aria-hidden="true">
                    {meta.glyph}
                  </span>
                  <span className="row-number">{index + 1}</span>
                  <span className="row-identity">
                    <span className="row-lemma">{displayLemma(rowLemma)}</span>
                    {rowGloss ? <span className="row-gloss">{rowGloss}</span> : null}
                    <span className="row-why" data-testid={`practice-daily-why-${row.item.lemmaId}`}>
                      <ChromeDual uk={why.uk} en={why.en} />
                    </span>
                  </span>
                  <span className="row-status">
                    <ChromeText k={meta.labelKey} />
                  </span>
                </a>
              </li>
            );
          })}
        </ol>
      </details>
    </div>
  );
}
