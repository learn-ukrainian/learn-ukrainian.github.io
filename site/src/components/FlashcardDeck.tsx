import React, { useState } from 'react';

interface FlashcardData {
  /**
   * @schemaDescription Front value consumed by this component.
   * @ukrainianText true
   */
  front: string;
  /**
   * @schemaDescription Back value consumed by this component.
   * @ukrainianText true
   */
  back: string;
  /**
   * @schemaDescription Subtitle value consumed by this component.
   * @ukrainianText true
   */
  subtitle?: string;
  /**
   * @schemaDescription Tag value consumed by this component.
   * @ukrainianText true
   */
  tag?: string;
  /**
   * @schemaDescription Tag Color value consumed by this component.
   * @ukrainianText false
   */
  tagColor?: string;
}

interface FlashcardDeckProps {
  /**
   * @schemaDescription Cards value consumed by this component.
   * @ukrainianText true
   */
  cards: FlashcardData[];
}

function Flashcard({ card }: { card: FlashcardData }) {
  const [flipped, setFlipped] = useState(false);

  return (
    <div
      className={`flashcard${flipped ? ' flipped' : ''}`}
      data-activity="flashcard"
      data-flipped={flipped ? 'true' : 'false'}
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
    <div className="flashcards" data-activity="flashcard-deck">
      {cards.map((card, i) => (
        <Flashcard key={`${card.front}-${i}`} card={card} />
      ))}
    </div>
  );
}
