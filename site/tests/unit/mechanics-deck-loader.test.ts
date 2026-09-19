import { describe, it, expect } from 'vitest';
import {
  ALL_MECHANICS_POS_KEYS,
  MECHANICS_DECK_META,
  loadMechanicsDeck,
  type MechanicsPosKey,
} from '../../src/lib/lexicon/mechanics-deck-loader';

describe('mechanics-deck-loader', () => {
  it('defines metadata for all 8 deep mechanics parts of speech', () => {
    expect(ALL_MECHANICS_POS_KEYS).toHaveLength(8);
    for (const pos of ALL_MECHANICS_POS_KEYS) {
      const meta = MECHANICS_DECK_META[pos];
      expect(meta).toBeDefined();
      expect(meta.titleUk).toBeTruthy();
      expect(meta.titleEn).toBeTruthy();
      expect(meta.descriptionUk).toBeTruthy();
      expect(meta.descriptionEn).toBeTruthy();
      expect(meta.itemCount).toBeGreaterThan(0);
      expect(['blue', 'teal', 'purple', 'orange']).toContain(meta.accent);
    }
  });

  it.each(ALL_MECHANICS_POS_KEYS)(
    'loads and normalizes %s mechanics deck correctly with exact count and valid sentence blanks',
    async (pos: MechanicsPosKey) => {
      const cards = await loadMechanicsDeck(pos);
      const meta = MECHANICS_DECK_META[pos];

      // Exact count agreement with metadata
      expect(cards.length).toBe(meta.itemCount);

      // Verify EVERY card in the deck has normalized prompt and does not drop text
      for (const card of cards) {
        expect(card.id).toBeTruthy();
        expect(card.pos).toBe(pos);
        expect(card.prompt).toBeTruthy();
        expect(card.prompt).not.toMatch(/_{4,}/); // No unnormalized underscore runs
        expect(card.options.length).toBeGreaterThanOrEqual(3);
        expect(card.options).toContain(card.correctAnswer);

        if (card.prompt.includes('___')) {
          const blankIdx = card.prompt.indexOf('___');
          expect(blankIdx).toBeGreaterThanOrEqual(0);
        }
      }

      const firstCard = cards[0];
      // Verify evaluation: correct pick
      const correctEval = firstCard.evaluate(firstCard.correctAnswer, 'uk');
      expect(correctEval.isCorrect).toBe(true);
      expect(correctEval.feedback).toBeTruthy();

      // Verify evaluation: wrong pick
      const wrongOption = firstCard.options.find((opt) => opt !== firstCard.correctAnswer)!;
      const wrongEval = firstCard.evaluate(wrongOption, 'uk');
      expect(wrongEval.isCorrect).toBe(false);
      expect(wrongEval.feedback).toBeTruthy();
    },
  );
});
