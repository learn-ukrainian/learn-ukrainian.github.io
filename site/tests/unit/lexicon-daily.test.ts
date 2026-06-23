import { describe, expect, test } from 'vitest';
import { dateSeed, pickDaily } from '@site/src/lib/lexicon/daily';

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
