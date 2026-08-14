import ChromeText, { ChromeDual } from '../lib/i18n/ChromeText';
import { CHROME_STRINGS, type ChromeLocale } from '../lib/i18n/chrome';
import type { PracticeLexeme } from '../lib/lexicon/srs';

/**
 * #6722: one wrong answer from the session, kept for the results-screen review
 * list — the correct pairing (attested deck gloss, never invented) plus a link
 * onward instead of a dead end.
 */
export interface SessionMissItem {
  lemmaId: string;
  lemma: string;
  gloss: string;
}

export interface SessionSummaryStats {
  correct: number;
  lapsed: number;
  /**
   * #6720: the frozen session target planned at round start. The score ratio uses
   * this one denominator so the summary agrees with the in-session progress badge
   * (lapsed-card re-serves extend the round but never move the denominator).
   */
  roundSize: number;
  advancedToReview: string[];
  streak: number;
  nextDueLabel: { uk: string; en: string } | null;
  deferredLemmas: PracticeLexeme[];
  /** #6722: every lemma missed this session, deduplicated, most recent last. */
  misses: SessionMissItem[];
}

interface PracticeSessionSummaryProps {
  stats: SessionSummaryStats;
  /** Pure chrome locale — summary UI never slash-duals (#5503). */
  chromeLocale: ChromeLocale;
  /**
   * #6722 miss review is UA lemma + Atlas link always; the English gloss only
   * renders where the level already carries content glosses (A1, or EN chrome) —
   * max-immersion levels never get English raised back up via the results screen.
   */
  showMissGloss: boolean;
  onAnotherSession(): void;
  onDone(): void;
}

export default function PracticeSessionSummary({
  stats,
  chromeLocale,
  showMissGloss,
  onAnotherSession,
  onDone,
}: PracticeSessionSummaryProps) {
  // Score against the frozen round size, not raw rating counts: re-served lapsed
  // cards earn a second correct rating, so `correct` can exceed the round size.
  // chromeLocale drives miss-list Atlas aria-labels (same openInAtlasTab pattern
  // as in-session links); ChromeText/ChromeDual still dual-render for CSS locale.
  const scoreCorrect = Math.min(stats.correct, stats.roundSize);
  return (
    <div className="lexicon-session-summary" data-testid="practice-session-summary">
      <h2 className="lexicon-session-summary-title">
        <ChromeText k="practice.sessionComplete" />
      </h2>
      <dl className="lexicon-session-summary-stats">
        <div>
          <dt>
            <ChromeText k="practice.correctCount" />
          </dt>
          <dd>{stats.correct}</dd>
        </div>
        <div>
          <dt>
            <ChromeText k="practice.lapsedCount" />
          </dt>
          <dd>{stats.lapsed}</dd>
        </div>
        <div>
          <dt>
            <ChromeText k="practice.streak" />
          </dt>
          <dd>🔥 {stats.streak}</dd>
        </div>
        <div className="session-score">
          <dt>
            <ChromeText k="practice.score" />
          </dt>
          <dd>
            {scoreCorrect}/{stats.roundSize}
          </dd>
        </div>
      </dl>
      {stats.advancedToReview.length > 0 ? (
        <section className="lexicon-session-advanced">
          <h3>
            <ChromeText k="practice.advancedToReview" />
          </h3>
          <ul>
            {stats.advancedToReview.map((lemma) => (
              <li key={lemma}>{lemma}</li>
            ))}
          </ul>
        </section>
      ) : null}
      {stats.nextDueLabel ? (
        <p className="lexicon-session-next-due" data-testid="practice-next-due">
          <ChromeDual uk={stats.nextDueLabel.uk} en={stats.nextDueLabel.en} />
        </p>
      ) : null}
      {stats.misses.length > 0 ? (
        <section className="lexicon-session-misses" data-testid="practice-session-misses">
          <h3>
            <ChromeText k="practice.reviewMisses" />
          </h3>
          <ul>
            {stats.misses.map((miss) => (
              <li key={miss.lemmaId}>
                <span lang="uk">{miss.lemma}</span>
                {showMissGloss ? (
                  <span className="lexicon-session-miss-gloss"> — {miss.gloss}</span>
                ) : null}
                <a
                  href={`/lexicon/${encodeURIComponent(miss.lemmaId)}/`}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={CHROME_STRINGS[chromeLocale]['practice.openInAtlasTab']}
                >
                  <ChromeText k="practice.openInAtlasArrow" />
                </a>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      {stats.deferredLemmas.length > 0 ? (
        <section className="lexicon-session-deferred" data-testid="practice-deferred-list">
          <h3>
            <ChromeText k="practice.willRepeatNext" />
          </h3>
          <ul>
            {stats.deferredLemmas.map((lemma) => (
              <li key={lemma.lemmaId}>{lemma.lemma}</li>
            ))}
          </ul>
        </section>
      ) : null}
      <div className="lexicon-session-summary-actions">
        <button type="button" className="btn btn-accent" onClick={onAnotherSession}>
          <ChromeText k="practice.anotherSession" />
        </button>
        <button type="button" className="btn" onClick={onDone}>
          <ChromeText k="practice.done" />
        </button>
      </div>
      <nav className="lexicon-session-continue" data-testid="practice-session-continue-links">
        <span className="lexicon-session-continue-label">
          <ChromeText k="practice.continueLearning" />
        </span>
        <a href="/lexicon/">
          <ChromeText k="nav.atlas" />
        </a>
        <a href="/words-of-the-day/">
          <ChromeText k="nav.dailyWords" />
        </a>
      </nav>
      <figure className="lexicon-session-proverb">
        <blockquote lang="uk">«Терпи, козаче — отаманом будеш.»</blockquote>
        <figcaption lang="uk">Українське прислів&apos;я</figcaption>
      </figure>
    </div>
  );
}
