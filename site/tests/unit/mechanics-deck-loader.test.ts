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
    'loads and normalizes %s mechanics deck correctly',
    async (pos: MechanicsPosKey) => {
      const cards = await loadMechanicsDeck(pos);
      expect(cards.length).toBeGreaterThanOrEqual(40);

      const firstCard = cards[0];
      expect(firstCard.id).toBeTruthy();
      expect(firstCard.pos).toBe(pos);
      expect(firstCard.prompt).toContain('___');
      expect(firstCard.options.length).toBeGreaterThanOrEqual(3);
      expect(firstCard.options).toContain(firstCard.correctAnswer);

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
