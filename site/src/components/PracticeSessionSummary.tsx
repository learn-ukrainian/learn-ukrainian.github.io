import ChromeText, { ChromeDual } from '../lib/i18n/ChromeText';
import type { ChromeLocale } from '../lib/i18n/chrome';
import type { PracticeLexeme } from '../lib/lexicon/srs';

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
}

interface PracticeSessionSummaryProps {
  stats: SessionSummaryStats;
  /** Pure chrome locale — summary UI never slash-duals (#5503). */
  chromeLocale: ChromeLocale;
  onAnotherSession(): void;
  onDone(): void;
}

export default function PracticeSessionSummary({
  stats,
  chromeLocale,
  onAnotherSession,
  onDone,
}: PracticeSessionSummaryProps) {
  // chromeLocale is the caller's pure-locale contract; ChromeText/ChromeDual
  // render both locales and CSS on html[data-chrome-locale] shows one.
  void chromeLocale;
  // Score against the frozen round size, not raw rating counts: re-served lapsed
  // cards earn a second correct rating, so `correct` can exceed the round size.
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
      <figure className="lexicon-session-proverb">
        <blockquote lang="uk">«Терпи, козаче — отаманом будеш.»</blockquote>
        <figcaption lang="uk">Українське прислів&apos;я</figcaption>
      </figure>
    </div>
  );
}
