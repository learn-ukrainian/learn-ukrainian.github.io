import React, { useState } from 'react';

interface FlashcardData {
  front: string;
  back: string;
  subtitle?: string;
  tag?: string;
  tagColor?: string;
}

interface FlashcardDeckProps {
  cards: FlashcardData[];
}

function Flashcard({ card }: { card: FlashcardData }) {
  const [flipped, setFlipped] = useState(false);

  return (
    <div
      className={`flashcard${flipped ? ' flipped' : ''}`}
      onClick={() => setFlipped(!flipped)}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setFlipped(!flipped); } }}
      role="button"
      tabIndex={0}
      aria-label={flipped ? `${card.back} — click to flip` : `${card.front} — click to flip`}
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
  );
}

/**
 * Interactive flashcard deck with flip animation.
 * Cards display a Ukrainian word on front, English translation on back.
 *
 * Usage in MDX:
 *   <FlashcardDeck cards={[
 *     { front: "стіл", back: "table", subtitle: "мій стіл", tag: "м", tagColor: "#0057B8" },
 *     { front: "книга", back: "book", tag: "ж", tagColor: "#C2185B" },
 *   ]} />
 */
export default function FlashcardDeck({ cards }: FlashcardDeckProps) {
  if (!cards || cards.length === 0) return null;

  return (
    <div className="flashcards">
      {cards.map((card, i) => (
        <Flashcard key={`${card.front}-${i}`} card={card} />
      ))}
    </div>
  );
}
