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
import { usablePracticeSentenceEnglish } from '../lib/lexicon/practice-sentence-en';

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
  /** D10: independently localized active-deck titles, or undefined for All Words. */
  deckTitleUk?: string | null;
  deckTitleEn?: string | null;
  /** #6132: re-draw today's pick set without waiting for the calendar day to change. */
  onReRoll?: () => void;
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
  deckTitleUk = null,
  deckTitleEn = null,
  onReRoll,
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
  // The practice-lexemes map is OPTIONAL ENRICHMENT ONLY (ipa, and pos/example
  // when the pick payload itself lacks them) — most daily-pool picks are not
  // in this much smaller map, so the card must never depend on a hit here to
  // render (#5852), nor let a map hit override the pick's own data (#5856).
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
  // The pick payload's own pos wins wherever it exists; the lexeme map fills the
  // gap only when the payload has none (#5856 — same precedence as gloss/cefr).
  const displayPos = currentItem?.pos ?? currentLexeme?.pos ?? null;
  const frontSubtitle = currentItem
    ? [currentLexeme?.ipa, displayPos, displayCefr].filter(Boolean).join(' · ')
    : '';
  const showStressMarks = learnerLevel === 'A1';
  const displayLemma = (lemma: string) => (showStressMarks ? lemma : stripStressMarks(lemma));
  const currentExample = currentItem?.example?.trim() || currentLexeme?.example?.trim() || null;
  const currentExampleEn = usablePracticeSentenceEnglish(currentItem?.exampleEn || currentLexeme?.exampleEn);

  return (
    <div className="practice-daily-deck" data-testid="practice-daily-deck">
      <div className="daily-deck-header">
        <h2 data-testid="practice-daily-deck-title">
          {deckTitleUk && deckTitleEn ? (
            <ChromeDual
              uk={`Слова дня — ${deckTitleUk}`}
              en={`Words of the day — ${deckTitleEn}`}
            />
          ) : (
            <ChromeText k="practice.wordsTitle" />
          )}
        </h2>
        <span className="daily-deck-position" aria-live="polite">
          <ChromeDual
            uk={`${previewIndex + 1} з ${total}`}
            en={`${previewIndex + 1} / ${total}`}
          />
        </span>
        {onReRoll ? (
          <button
            type="button"
            className="daily-deck-reroll"
            data-testid="practice-daily-reroll"
            onClick={() => {
              setPreviewIndex(0);
              setFlipped(false);
              onReRoll();
            }}
          >
            <span aria-hidden="true">🔀</span> <ChromeText k="practice.reRoll" />
          </button>
        ) : null}
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
                  {displayPos && (
                    <span className="flashcard-subtitle">{displayPos}</span>
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
        {currentLemmaId && currentItem?.hasAtlasEntry !== false && (
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
              <span aria-hidden="true">{STATUS_META.due.glyph}</span> {rows.pendingDue.length}{' '}
              <ChromeText k={STATUS_META.due.labelKey} />
            </span>
            <span className="counter new">
              <span aria-hidden="true">{STATUS_META.new.glyph}</span> {rows.pendingNew.length}{' '}
              <ChromeText k={STATUS_META.new.labelKey} />
            </span>
            <span className="counter done">
              <span aria-hidden="true">{STATUS_META.done.glyph}</span> {rows.done.length}{' '}
              <ChromeText k={STATUS_META.done.labelKey} />
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
            const rowContent = (
              <>
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
              </>
            );
            return (
              <li
                key={row.item.lemmaId}
                className={`daily-deck-row state-${row.state}`}
                data-state={row.state}
                style={{ '--row-accent': meta.colorVar } as React.CSSProperties}
              >
                {row.item.hasAtlasEntry !== false ? (
                  <a
                    href={atlasLemmaHref(row.item.lemmaId)}
                    className="daily-deck-row-link"
                  >
                    {rowContent}
                  </a>
                ) : (
                  <div className="daily-deck-row-link">
                    {rowContent}
                  </div>
                )}
              </li>
            );
          })}
        </ol>
      </details>
    </div>
  );
}
