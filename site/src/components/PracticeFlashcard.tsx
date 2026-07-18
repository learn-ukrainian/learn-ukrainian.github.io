import { useEffect, useState } from 'react';
import { CHROME_STRINGS } from '../lib/i18n/chrome';
import type { ChromeLocale } from '../lib/i18n/chrome';
import type { PracticeRating } from '../lib/lexicon/srs';

export interface PracticeFlashcardData {
  front: string;
  back: string;
  subtitle?: string;
  tag?: string;
  tagColor?: string;
}

interface PracticeFlashcardProps {
  card: PracticeFlashcardData;
  ratingLabels: Record<PracticeRating, { uk: string; en: string }>;
  intervalPreviews: Record<PracticeRating, string>;
  onRate(rating: PracticeRating): void;
  showEnglishSubtitles: boolean;
  chromeLocale: ChromeLocale;
}

const RATING_ORDER: PracticeRating[] = ['again', 'hard', 'good', 'easy'];

export default function PracticeFlashcard({
  card,
  ratingLabels,
  intervalPreviews,
  onRate,
  showEnglishSubtitles,
  chromeLocale,
}: PracticeFlashcardProps) {
  const [flipped, setFlipped] = useState(false);
  const [rated, setRated] = useState(false);

  useEffect(() => {
    setFlipped(false);
    setRated(false);
  }, [card.front, card.back]);

  const tapLabel = CHROME_STRINGS[chromeLocale]['practice.tapToFlip'];
  const rateRecallLabel = CHROME_STRINGS[chromeLocale]['practice.rateRecall'];

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (rated) return;
      if (event.altKey || event.ctrlKey || event.metaKey) return;
      // Never steal keys from text-entry controls (typing 'a' must not rate).
      const target = event.target as HTMLElement | null;
      if (target?.closest?.('input, textarea, select, [contenteditable="true"]')) return;
      const key = event.key.toLowerCase();
      // Space/Enter activate whatever control holds focus (button, link, the card
      // itself) — let that native activation happen instead of double-handling it here.
      const activatesControl = key === ' ' || key === 'enter';
      if (activatesControl && target?.closest?.('button, a, [role="button"], [role="link"]')) return;
      if (!flipped && (key === ' ' || key === 'enter')) {
        event.preventDefault();
        setFlipped(true);
        return;
      }
      if (!flipped) return;
      const rating =
        key === 'a' || key === '1'
          ? 'again'
          : key === 'h' || key === '2'
            ? 'hard'
            : key === 'g' || key === '3'
              ? 'good'
              : key === 'e' || key === '4'
                ? 'easy'
                : null;
      if (!rating) return;
      event.preventDefault();
      setRated(true);
      onRate(rating);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [flipped, rated, onRate]);

  const handleFlip = () => {
    if (rated) return;
    setFlipped((value) => !value);
  };

  const handleRate = (rating: PracticeRating) => {
    if (!flipped || rated) return;
    setRated(true);
    onRate(rating);
  };

  return (
    <>
      <div
        className={`flashcard${flipped ? ' flipped' : ''}`}
        data-activity="flashcard"
        data-flipped={flipped ? 'true' : 'false'}
        data-rated={rated ? 'true' : 'false'}
        onClick={handleFlip}
        onKeyDown={(event) => {
          if (rated) return;
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            handleFlip();
          }
        }}
        role="button"
        tabIndex={rated ? -1 : 0}
        aria-label={flipped ? `${card.back} — ${tapLabel}` : `${card.front} — ${tapLabel}`}
      >
        <div className="flashcard-inner">
          <div className="flashcard-front">
            <span className="flashcard-word">{card.front}</span>
            {card.subtitle && <span className="flashcard-subtitle">{card.subtitle}</span>}
            {card.tag && (
              <span
                className="flashcard-tag"
                style={card.tagColor ? { background: card.tagColor, color: 'white' } : undefined}
              >
                {card.tag}
              </span>
            )}
          </div>
          <div className="flashcard-back">
            <span className="flashcard-word">{card.back}</span>
            {card.subtitle && <span className="flashcard-subtitle">{card.subtitle}</span>}
          </div>
        </div>
      </div>
      <div
        className="lexicon-rating-bar rating-bar"
        role="group"
        aria-label={rateRecallLabel}
        data-revealed={flipped ? 'true' : 'false'}
        data-locked={rated ? 'true' : 'false'}
      >
        {RATING_ORDER.map((rating, index) => (
          <button
            type="button"
            key={rating}
            className="rate-btn"
            data-rate={rating}
            aria-keyshortcuts={String(index + 1)}
            disabled={!flipped || rated}
            aria-disabled={!flipped || rated}
            onClick={() => handleRate(rating)}
          >
            <span className="rk">{index + 1}</span>
            <span className="rt">
              <span lang="uk">{ratingLabels[rating].uk}</span>
              {showEnglishSubtitles ? (
                <span className="btn-sub" lang="en">{ratingLabels[rating].en}</span>
              ) : null}
            </span>
            {flipped ? <span className="ri">‹{intervalPreviews[rating]}›</span> : null}
          </button>
        ))}
      </div>
    </>
  );
}
