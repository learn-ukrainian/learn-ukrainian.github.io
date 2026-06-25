import { describe, expect, test } from 'vitest';
import {
  filterByCumulativeLevel,
  filterRowsByLevel,
  populatedUkrainianLetters,
} from '@site/src/lib/lexicon/levels';

describe('filterByCumulativeLevel', () => {
  const rows = [
    { lemma: 'ранок', cefr: 'A1' },
    { lemma: 'площа', cefr: 'A2' },
    { lemma: 'громада', cefr: 'B1' },
    { lemma: 'відтінок', cefr: 'B2' },
    { lemma: 'невідоме' },
  ];

  test('defaults invalid or missing selections to the A1 floor', () => {
    expect(filterByCumulativeLevel(rows, undefined).map((row) => row.lemma)).toEqual([
      'ранок',
    ]);
    expect(filterByCumulativeLevel(rows, 'C0').map((row) => row.lemma)).toEqual([
      'ранок',
    ]);
  });

  test('includes all lower levels through the selected cap', () => {
    expect(filterByCumulativeLevel(rows, 'B1').map((row) => row.lemma)).toEqual([
      'ранок',
      'площа',
      'громада',
    ]);
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
