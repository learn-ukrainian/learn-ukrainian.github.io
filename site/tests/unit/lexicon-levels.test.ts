import { describe, expect, test } from 'vitest';
import {
  filterByCumulativeLevel,
  filterRowsByLevel,
  populatedUkrainianLetters,
  prioritizeByLearnerLevel,
} from '@site/src/lib/lexicon/levels';

describe('prioritizeByLearnerLevel', () => {
  const rows = [
    { lemma: 'ранок', cefr: 'A1' },
    { lemma: 'площа', cefr: 'A2' },
    { lemma: 'громада', cefr: 'B1' },
    { lemma: 'відтінок', cefr: 'B2' },
    { lemma: 'невідоме' },
  ];

  test('defaults invalid or missing selections to an A1 preference without excluding rows', () => {
    const expected = ['ранок', 'площа', 'громада', 'відтінок', 'невідоме'];
    expect(prioritizeByLearnerLevel(rows, undefined).map((row) => row.lemma)).toEqual(expected);
    expect(prioritizeByLearnerLevel(rows, 'C0').map((row) => row.lemma)).toEqual(expected);
  });

  test('prefers the selected level and keeps higher and unlevelled rows eligible', () => {
    expect(prioritizeByLearnerLevel(rows, 'B1').map((row) => row.lemma)).toEqual([
      'громада',
      'площа',
      'відтінок',
      'ранок',
      'невідоме',
    ]);
  });
});

describe('filterByCumulativeLevel (#6727 exact CEFR filter)', () => {
  const rows = [
    { lemma: 'ранок', cefr: 'A1' },
    { lemma: 'площа', cefr: 'A2' },
    { lemma: 'громада', cefr: 'B1' },
    { lemma: 'відтінок', cefr: 'B2' },
    { lemma: 'архітектоніка', cefr: 'C1' },
    { lemma: 'невідоме' },
  ];

  test('keeps only rows at the selected CEFR — does not re-rank the full pool', () => {
    expect(filterByCumulativeLevel(rows, 'B2').map((row) => row.lemma)).toEqual(['відтінок']);
    expect(filterByCumulativeLevel(rows, 'A1').map((row) => row.lemma)).toEqual(['ранок']);
    expect(filterByCumulativeLevel(rows, 'C1').map((row) => row.lemma)).toEqual(['архітектоніка']);
  });

  test('excludes unknown CEFR and returns empty when the level is absent from the pool', () => {
    expect(filterByCumulativeLevel(rows, 'C2')).toEqual([]);
    expect(filterByCumulativeLevel(rows, 'B2').every((row) => row.cefr === 'B2')).toBe(true);
  });

  test('normalizes invalid selections to A1 without admitting other levels', () => {
    expect(filterByCumulativeLevel(rows, 'C0').map((row) => row.lemma)).toEqual(['ранок']);
  });
});

describe('populatedUkrainianLetters', () => {
  test('returns populated Ukrainian alphabet letters in А-Я order', () => {
    const rows = [
      { l: 'їжа' },
      { l: 'ґанок' },
      { l: 'ЄС' },
      { l: 'Іван' },
      { l: 'автобус' },
      { l: 'coffee' },
    ];

    expect(populatedUkrainianLetters(rows)).toEqual(['А', 'Ґ', 'Є', 'І', 'Ї']);
  });
});

describe('filterRowsByLevel', () => {
  const rows = [
    { l: 'ранок', c: 'A1' },
    { l: 'площа', c: 'A2' },
    { l: 'громада', c: 'B1' },
    { l: 'слово' },
  ];

  test('keeps all rows for the all-level browse filter', () => {
    expect(filterRowsByLevel(rows, 'all')).toEqual(rows);
  });

  test('narrows browse rows to the exact selected CEFR level', () => {
    expect(filterRowsByLevel(rows, 'A2')).toEqual([{ l: 'площа', c: 'A2' }]);
  });
});
