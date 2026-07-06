import type { PracticeLexeme } from '../lib/lexicon/srs';

export interface SessionSummaryStats {
  correct: number;
  lapsed: number;
  advancedToReview: string[];
  streak: number;
  nextDueLabel: string | null;
  deferredLemmas: PracticeLexeme[];
}

interface PracticeSessionSummaryProps {
  stats: SessionSummaryStats;
  showEnglishSubtitles: boolean;
  onAnotherSession(): void;
  onDone(): void;
}

export default function PracticeSessionSummary({
  stats,
  showEnglishSubtitles,
  onAnotherSession,
  onDone,
}: PracticeSessionSummaryProps) {
  return (
    <div className="lexicon-session-summary" data-testid="practice-session-summary">
      <h2 className="lexicon-session-summary-title">Сесія завершена</h2>
      {showEnglishSubtitles ? (
        <p className="lexicon-session-summary-sub">Session complete</p>
      ) : null}
      <dl className="lexicon-session-summary-stats">
        <div>
          <dt>Правильно</dt>
          <dd>{stats.correct}</dd>
        </div>
        <div>
          <dt>З lapses</dt>
          <dd>{stats.lapsed}</dd>
        </div>
        <div>
          <dt>Серія</dt>
          <dd>🔥 {stats.streak}</dd>
        </div>
      </dl>
      {stats.advancedToReview.length > 0 ? (
        <section className="lexicon-session-advanced">
          <h3>Перейшли до Review</h3>
          <ul>
            {stats.advancedToReview.map((lemma) => (
              <li key={lemma}>{lemma}</li>
            ))}
          </ul>
        </section>
      ) : null}
      {stats.nextDueLabel ? (
        <p className="lexicon-session-next-due" data-testid="practice-next-due">
          {stats.nextDueLabel}
        </p>
      ) : null}
      {stats.deferredLemmas.length > 0 ? (
        <section className="lexicon-session-deferred" data-testid="practice-deferred-list">
          <h3>повторимо наступного разу</h3>
          <ul>
            {stats.deferredLemmas.map((lemma) => (
              <li key={lemma.lemmaId}>{lemma.lemma}</li>
            ))}
          </ul>
        </section>
      ) : null}
      <div className="lexicon-session-summary-actions">
        <button type="button" className="btn btn-accent" onClick={onAnotherSession}>
          Ще одна сесія
          {showEnglishSubtitles ? <span className="btn-sub">Another session</span> : null}
        </button>
        <button type="button" className="btn" onClick={onDone}>
          Готово
          {showEnglishSubtitles ? <span className="btn-sub">Done</span> : null}
        </button>
      </div>
    </div>
  );
}
