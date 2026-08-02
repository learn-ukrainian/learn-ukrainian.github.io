import { describe, expect, test } from 'vitest';
import {
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
