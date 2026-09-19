import { useMemo, useState } from 'react';
import type { NormalizedMechanicsCard, MechanicsDeckMeta } from '../../lib/lexicon/mechanics-deck-loader';

export interface MechanicsPracticeProps {
  meta: MechanicsDeckMeta;
  cards: NormalizedMechanicsCard[];
  onBackToTracks: () => void;
  chromeLocale?: 'uk' | 'en';
}

interface CardEvaluation {
  selectedOption: string;
  isCorrect: boolean;
  feedback: string;
  ruleCitation: string;
  ruleSummary: string;
}

export default function MechanicsPractice({
  meta,
  cards,
  onBackToTracks,
  chromeLocale = 'uk',
}: MechanicsPracticeProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [evaluation, setEvaluation] = useState<CardEvaluation | null>(null);
  const [history, setHistory] = useState<Array<{ card: NormalizedMechanicsCard; eval: CardEvaluation }>>([]);
  const [completed, setCompleted] = useState(false);

  const currentCard = cards[currentIndex] ?? null;

  const handleSelectOption = (opt: string) => {
    if (selectedOption !== null || !currentCard) return;
    setSelectedOption(opt);
    const result = currentCard.evaluate(opt, chromeLocale);
    const cardEval: CardEvaluation = {
      selectedOption: opt,
      isCorrect: result.isCorrect,
      feedback: result.feedback,
      ruleCitation: result.ruleCitation,
      ruleSummary: result.ruleSummary,
    };
    setEvaluation(cardEval);
    setHistory((prev) => [...prev, { card: currentCard, eval: cardEval }]);
  };

  const handleNext = () => {
    if (currentIndex + 1 < cards.length) {
      setCurrentIndex((i) => i + 1);
      setSelectedOption(null);
      setEvaluation(null);
    } else {
      setCompleted(true);
    }
  };

  const handleRestart = () => {
    setCurrentIndex(0);
    setSelectedOption(null);
    setEvaluation(null);
    setHistory([]);
    setCompleted(false);
  };

  const correctCount = useMemo(
    () => history.filter((h) => h.eval.isCorrect).length,
    [history],
  );

  if (!currentCard || completed) {
    const total = history.length || cards.length;
    const scorePct = total > 0 ? Math.round((correctCount / total) * 100) : 0;
    const misses = history.filter((h) => !h.eval.isCorrect);

    return (
      <div className="lexicon-practice-stage-shell" data-testid="practice-mechanics-summary">
        <div className="lexicon-practice-stage-bar">
          <button
            type="button"
            className="stage-back"
            data-testid="practice-mechanics-back-button"
            onClick={onBackToTracks}
          >
            {chromeLocale === 'uk' ? '← До треків' : '← Back to tracks'}
          </button>
          <h2>{chromeLocale === 'uk' ? meta.titleUk : meta.titleEn} · {chromeLocale === 'uk' ? 'Підсумок' : 'Summary'}</h2>
        </div>

        <div className="practice-summary-card" data-testid="mechanics-summary-content" style={{ padding: '1.5rem', maxWidth: '640px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
            <span style={{ fontSize: '3rem', fontWeight: 'bold', color: scorePct >= 80 ? 'var(--sl-color-green)' : 'var(--sl-color-accent)' }}>
              {scorePct}%
            </span>
            <p style={{ marginTop: '0.5rem', fontSize: '1.1rem' }}>
              {chromeLocale === 'uk'
                ? `Правильних відповідей: ${correctCount} із ${total}`
                : `Correct answers: ${correctCount} of ${total}`}
            </p>
          </div>

          {misses.length > 0 ? (
            <div style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem' }}>
                {chromeLocale === 'uk' ? 'Варто повторити:' : 'Needs review:'}
              </h3>
              <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {misses.map((m, idx) => (
                  <li
                    key={m.card.id || idx}
                    style={{
                      padding: '0.75rem',
                      background: 'rgba(239, 68, 68, 0.1)',
                      borderLeft: '3px solid #ef4444',
                      borderRadius: '4px',
                      fontSize: '0.9rem',
                    }}
                  >
                    <div><strong>{m.card.prompt.replace('___', `[${m.card.correctAnswer}]`)}</strong></div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--sl-color-gray-3)', marginTop: '0.25rem' }}>
                      {m.eval.feedback}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <div style={{ textAlign: 'center', marginBottom: '1.5rem', color: 'var(--sl-color-green)' }}>
              {chromeLocale === 'uk' ? '🎉 Відмінний результат! Усі завдання виконано бездоганно.' : '🎉 Perfect score! All tasks answered correctly.'}
            </div>
          )}

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
            <button
              type="button"
              className="btn btn-accent"
              data-testid="practice-mechanics-restart"
              onClick={handleRestart}
            >
              {chromeLocale === 'uk' ? 'Спробувати ще раз' : 'Try again'}
            </button>
            <button
              type="button"
              className="btn"
              onClick={onBackToTracks}
            >
              {chromeLocale === 'uk' ? 'Повернутися до треків' : 'Return to tracks'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  const promptParts = currentCard.prompt.split('___');

  return (
    <div className="lexicon-practice-stage-shell" data-testid="practice-mechanics-session">
      <div className="lexicon-practice-stage-bar">
        <button
          type="button"
          className="stage-back"
          data-testid="practice-mechanics-back-button"
          onClick={onBackToTracks}
        >
          {chromeLocale === 'uk' ? '← До треків' : '← Back to tracks'}
        </button>
        <h2>
          {chromeLocale === 'uk' ? meta.titleUk : meta.titleEn}
          {currentCard.ruleCitation ? (
            <span style={{ fontSize: '0.8rem', fontWeight: 'normal', opacity: 0.75, marginLeft: '0.5rem' }}>
              ({currentCard.ruleCitation})
            </span>
          ) : null}
        </h2>
        <span className="queue-pill" data-testid="practice-mechanics-counter">
          {currentIndex + 1} / {cards.length}
        </span>
      </div>

      <div className="lexicon-practice-stage" tabIndex={-1} style={{ maxWidth: '640px', margin: '0 auto', padding: '1rem' }}>
        {/* Prompt with styled blank */}
        <div
          className="k3-mechanics-prompt-box"
          data-testid="practice-mechanics-prompt"
          style={{
            fontSize: '1.35rem',
            lineHeight: 1.6,
            padding: '1.25rem',
            borderRadius: '8px',
            background: 'var(--sl-color-gray-6, rgba(255,255,255,0.05))',
            marginBottom: '1.5rem',
            textAlign: 'center',
          }}
        >
          {promptParts[0]}
          <span
            data-testid="practice-mechanics-blank"
            style={{
              display: 'inline-block',
              minWidth: '60px',
              padding: '0 0.5rem',
              borderBottom: '2px solid var(--sl-color-accent)',
              fontWeight: 'bold',
              color: selectedOption ? (evaluation?.isCorrect ? 'var(--sl-color-green, #10b981)' : 'var(--sl-color-red, #ef4444)') : 'var(--sl-color-accent)',
            }}
          >
            {selectedOption ?? '____'}
          </span>
          {promptParts[1] ?? ''}
        </div>

        {/* Options grid */}
        <div
          className="mc-options"
          data-testid="practice-mechanics-options"
          style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem', marginBottom: '1.25rem' }}
        >
          {currentCard.options.map((opt) => {
            const isSelected = selectedOption === opt;
            const isTarget = opt === currentCard.correctAnswer;
            const isLocked = selectedOption !== null;

            let btnClass = 'mc-opt';
            if (isLocked) {
              if (isTarget) btnClass += ' correct';
              else if (isSelected) btnClass += ' wrong';
            }

            return (
              <button
                key={opt}
                type="button"
                className={btnClass}
                data-testid={`practice-mechanics-opt-${opt}`}
                data-selected={isSelected ? 'true' : undefined}
                data-correct={isLocked && isTarget ? 'true' : undefined}
                data-wrong={isLocked && isSelected && !isTarget ? 'true' : undefined}
                disabled={isLocked}
                onClick={() => handleSelectOption(opt)}
                style={{
                  padding: '1rem',
                  fontSize: '1.1rem',
                  borderRadius: '6px',
                  cursor: isLocked ? 'default' : 'pointer',
                }}
              >
                {opt}
              </button>
            );
          })}
        </div>

        {/* Feedback Panel */}
        {evaluation ? (
          <div
            className="k3-feedback-panel"
            data-testid="practice-mechanics-feedback"
            style={{
              padding: '1rem',
              borderRadius: '8px',
              background: evaluation.isCorrect ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)',
              borderLeft: `4px solid ${evaluation.isCorrect ? '#10b981' : '#ef4444'}`,
              marginBottom: '1.25rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ fontWeight: 'bold', fontSize: '1rem', color: evaluation.isCorrect ? '#10b981' : '#ef4444' }}>
                {evaluation.isCorrect
                  ? (chromeLocale === 'uk' ? '✓ Правильно!' : '✓ Correct!')
                  : (chromeLocale === 'uk' ? '✗ Неправильно' : '✗ Incorrect')}
              </span>
              {evaluation.ruleCitation ? (
                <span
                  style={{
                    fontSize: '0.8rem',
                    background: 'rgba(255,255,255,0.1)',
                    padding: '0.15rem 0.5rem',
                    borderRadius: '4px',
                  }}
                >
                  {evaluation.ruleCitation}
                </span>
              ) : null}
            </div>
            <p style={{ margin: 0, fontSize: '0.95rem', lineHeight: 1.5 }}>
              {evaluation.feedback}
            </p>
          </div>
        ) : null}

        {/* Navigation Action */}
        {selectedOption !== null ? (
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button
              type="button"
              className="btn btn-accent"
              data-testid="practice-mechanics-next"
              onClick={handleNext}
              style={{ minWidth: '120px' }}
            >
              {currentIndex + 1 < cards.length
                ? (chromeLocale === 'uk' ? 'Далі →' : 'Next →')
                : (chromeLocale === 'uk' ? 'Завершити' : 'Finish')}
            </button>
          </div>
        ) : null}
      </div>
    </div>
  );
}
