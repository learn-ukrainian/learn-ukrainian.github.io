import { describe, expect, test } from 'vitest';
import { filterTeacherClozeItems } from '@site/src/lib/lexicon/custom-decks';

describe('teacher cloze overrides', () => {
  test('never returns excluded cards with an English placeholder lemma', () => {
    const cards = [
      { clozeId: 'teacher_cloze_57', lemma: 'English placeholder' },
      { clozeId: 'teacher_cloze_581', lemma: 'English placeholder' },
      { clozeId: 'teacher_cloze_1521', lemma: 'English placeholder' },
      { clozeId: 'teacher_cloze_safe', lemma: 'слово' },
    ];

    expect(filterTeacherClozeItems(cards)).toEqual([
      { clozeId: 'teacher_cloze_safe', lemma: 'слово' },
    ]);
  });
});
