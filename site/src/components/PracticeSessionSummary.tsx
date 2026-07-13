import type { PracticeLexeme } from '../lib/lexicon/srs';

export interface SessionSummaryStats {
  correct: number;
  lapsed: number;
  advancedToReview: string[];
  streak: number;
  nextDueLabel: { uk: string; en: string } | null;
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
      <h2 className="lexicon-session-summary-title">
        <span lang="uk">Сесія завершена</span>
      </h2>
      {showEnglishSubtitles ? (
        <p className="lexicon-session-summary-sub" lang="en">Session complete</p>
      ) : null}
      <dl className="lexicon-session-summary-stats">
        <div>
          <dt>
            <span lang="uk">Правильно</span>
            {showEnglishSubtitles ? (
              <span className="btn-sub" lang="en">/ Correct</span>
            ) : null}
          </dt>
          <dd>{stats.correct}</dd>
        </div>
        <div>
          <dt>
            <span lang="uk">З lapses</span>
            {showEnglishSubtitles ? (
              <span className="btn-sub" lang="en">/ Lapsed</span>
            ) : null}
          </dt>
          <dd>{stats.lapsed}</dd>
        </div>
        <div>
          <dt>
            <span lang="uk">Серія</span>
            {showEnglishSubtitles ? (
              <span className="btn-sub" lang="en">/ Streak</span>
            ) : null}
          </dt>
          <dd>🔥 {stats.streak}</dd>
        </div>
      </dl>
      {stats.advancedToReview.length > 0 ? (
        <section className="lexicon-session-advanced">
          <h3>
            <span lang="uk">Перейшли до Review</span>
            {showEnglishSubtitles ? (
              <span className="btn-sub" lang="en">/ Advanced to Review</span>
            ) : null}
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
          <span lang="uk">{stats.nextDueLabel.uk}</span>
          {showEnglishSubtitles ? (
            <span className="btn-sub" lang="en">/ {stats.nextDueLabel.en}</span>
          ) : null}
        </p>
      ) : null}
      {stats.deferredLemmas.length > 0 ? (
        <section className="lexicon-session-deferred" data-testid="practice-deferred-list">
          <h3>
            <span lang="uk">повторимо наступного разу</span>
            {showEnglishSubtitles ? (
              <span className="btn-sub" lang="en">/ will repeat next time</span>
            ) : null}
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
          <span lang="uk">Ще одна сесія</span>
          {showEnglishSubtitles ? <span className="btn-sub" lang="en">Another session</span> : null}
        </button>
        <button type="button" className="btn" onClick={onDone}>
          <span lang="uk">Готово</span>
          {showEnglishSubtitles ? <span className="btn-sub" lang="en">Done</span> : null}
        </button>
      </div>
    </div>
  );
}
