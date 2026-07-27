import { describe, expect, test } from 'vitest';
import { dateSeed, deckSeed, pickDaily } from '@site/src/lib/lexicon/daily';

describe('dateSeed', () => {
  test('uses the local calendar date', () => {
    const morning = new Date(2026, 5, 23, 8, 0, 0);
    const evening = new Date(2026, 5, 23, 22, 30, 0);

    expect(dateSeed(morning)).toBe(20260623);
    expect(dateSeed(evening)).toBe(dateSeed(morning));
    expect(dateSeed(new Date(2026, 5, 24))).not.toBe(dateSeed(morning));
  });
});

describe('pickDaily', () => {
  test('is deterministic for a fixed pool, seed, and count', () => {
    const pool = ['авось', 'баба', 'дім', 'добрий день', 'мова'];
    const first = pickDaily(pool, 20260623, 3);
    const second = pickDaily(pool, 20260623, 3);

    expect(second).toEqual(first);
    expect(first).toHaveLength(3);
    expect(first.every((item) => pool.includes(item))).toBe(true);
  });

  test('caps the count at the pool length', () => {
    const pool = [{ slug: 'a' }, { slug: 'b' }];

    expect(pickDaily(pool, 20260623, 24)).toHaveLength(pool.length);
  });
});

describe('deckSeed', () => {
  test('is deterministic and varies by deck id', () => {
    expect(deckSeed('virtual_teacher_lesson')).toBe(deckSeed('virtual_teacher_lesson'));
    expect(deckSeed('set_alpha')).not.toBe(deckSeed('set_beta'));
    expect(deckSeed('all')).not.toBe(deckSeed('virtual_teacher_lesson'));
  });

  test('combined with dateSeed, draws different sets for different decks on the same day', () => {
    const pool = Array.from({ length: 30 }, (_, i) => `word-${i}`);
    const day = dateSeed(new Date(2026, 5, 23));

    const deckA = pickDaily(pool, day + deckSeed('set_alpha'), 12);
    const deckB = pickDaily(pool, day + deckSeed('set_beta'), 12);

    expect(deckA).not.toEqual(deckB);
  });

  test('combined with dateSeed, is stable for the same deck and day but rotates across days', () => {
    const pool = Array.from({ length: 30 }, (_, i) => `word-${i}`);
    const day1 = dateSeed(new Date(2026, 5, 23));
    const day2 = dateSeed(new Date(2026, 5, 24));
    const seed = deckSeed('set_alpha');

    expect(pickDaily(pool, day1 + seed, 12)).toEqual(pickDaily(pool, day1 + seed, 12));
    expect(pickDaily(pool, day1 + seed, 12)).not.toEqual(pickDaily(pool, day2 + seed, 12));
  });
});
