import { describe, expect, test } from 'vitest';
import { dateSeed, deckSeed, pickDaily, reRollSeed, type DailyWord } from '@site/src/lib/lexicon/daily';
import { pickDailyForLevel } from '@site/src/lib/lexicon/daily-card';
import { prioritizeByLearnerLevel } from '@site/src/lib/lexicon/levels';

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

describe('pickDailyForLevel (#6727 filter-not-reshuffle)', () => {
  const pool: DailyWord[] = (
    [
      ['A1', 73],
      ['A2', 75],
      ['B1', 72],
      ['B2', 40],
      ['C1', 40],
    ] as const
  ).flatMap(([level, n]) =>
    Array.from({ length: n }, (_, i) => ({
      lemma: `слово-${level}-${i}`,
      slug: `${level}-${i}`,
      gloss: `gloss ${level} ${i}`,
      cefr: level,
    })),
  );

  test('B2 draws only B2 rows — does not reshuffle the whole 300', () => {
    const seed = dateSeed(new Date(2026, 7, 13));
    const picks = pickDailyForLevel(pool, 'B2', seed, 12);

    expect(picks).toHaveLength(12);
    expect(picks.every((word) => word.cefr === 'B2')).toBe(true);

    // Contrast: soft re-rank + full-pool shuffle admits other levels (the #6727 bug).
    const reshuffledWholePool = pickDaily(prioritizeByLearnerLevel(pool, 'B2'), seed, 12);
    expect(reshuffledWholePool.some((word) => word.cefr !== 'B2')).toBe(true);
  });

  test('A1/A2/B1/C1 each stay within their own CEFR band', () => {
    const seed = dateSeed(new Date(2026, 7, 13));
    for (const level of ['A1', 'A2', 'B1', 'C1'] as const) {
      const picks = pickDailyForLevel(pool, level, seed, 12);
      expect(picks).toHaveLength(12);
      expect(picks.every((word) => word.cefr === level)).toBe(true);
    }
  });

  test('C2 with an empty band returns no cards (honest empty — #6728 residual)', () => {
    expect(pickDailyForLevel(pool, 'C2', dateSeed(new Date(2026, 7, 13)), 12)).toEqual([]);
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

describe('reRollSeed', () => {
  test('is zero for the default (un-re-rolled) draw', () => {
    expect(reRollSeed(0)).toBe(0);
  });

  test('#6132: re-rolling draws a different set without changing the day', () => {
    const pool = Array.from({ length: 30 }, (_, i) => `word-${i}`);
    const day = dateSeed(new Date(2026, 5, 23));

    const first = pickDaily(pool, day + reRollSeed(0), 12);
    const second = pickDaily(pool, day + reRollSeed(1), 12);
    const third = pickDaily(pool, day + reRollSeed(2), 12);

    expect(second).not.toEqual(first);
    expect(third).not.toEqual(first);
    expect(third).not.toEqual(second);
  });

  test('is deterministic for a given count, so the same re-roll replays identically', () => {
    const pool = Array.from({ length: 30 }, (_, i) => `word-${i}`);
    const day = dateSeed(new Date(2026, 5, 23));

    expect(pickDaily(pool, day + reRollSeed(3), 12)).toEqual(pickDaily(pool, day + reRollSeed(3), 12));
  });
});
