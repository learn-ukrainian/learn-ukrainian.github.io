import { describe, expect, test } from 'vitest';
import {
  heritageToErrorCorrection,
  heritageToUnjumble,
  selectHeritagePracticePresentation,
} from '@site/src/lib/lexicon/practice-activity-adapters';
import { cardKey, type PracticeHeritageItem } from '@site/src/lib/lexicon/srs';

function heritage(overrides: Partial<PracticeHeritageItem> = {}): PracticeHeritageItem {
  return {
    heritageId: 'heritage-adapter-fixture',
    lemmaId: 'dim',
    srsKey: cardKey('dim', 'heritage'),
    lemma: 'дім',
    nativeLemma: 'дім',
    kind: 'lexical',
    severity: 'russianism',
    prompt: 'Я бачу ___ щодня.',
    answer: 'дім',
    calque: 'дом',
    cefr: 'A2',
    options: [{ label: 'дім' }, { label: 'дом' }, { label: 'хата' }, { label: 'місто' }],
    rationale: 'Потрібне питоме українське слово.',
    rationaleUk: 'Потрібне питоме українське слово.',
    citations: ['fixture'],
    corrections: ['дім'],
    ...overrides,
  };
}

describe('heritage practice activity adapters', () => {
  test('adapts a full heritage frame into exact ErrorCorrection props', () => {
    expect(heritageToErrorCorrection(heritage())).toEqual({
      sentence: 'Я бачу дом щодня.',
      errorWord: 'дом',
      correctForm: 'дім',
      options: ['дім', 'дом', 'хата', 'місто'],
      explanation: 'Потрібне питоме українське слово.',
    });
  });

  test.each([
    ['multiple blanks', { prompt: 'Я бачу ___ і ___ щодня.' }],
    ['repeated calque span', { prompt: 'Дом стоїть біля ___.', calque: 'дом' }],
    ['missing correct source option', { options: [{ label: 'дом' }, { label: 'хата' }] }],
  ])('keeps %s in heritage MC', (_reason, overrides) => {
    expect(heritageToErrorCorrection(heritage(overrides))).toBeNull();
  });

  test('rejects a multi-word calque from ErrorCorrection', () => {
    expect(heritageToErrorCorrection(heritage({ calque: 'так як' }))).toBeNull();
  });

  test('adapts a full source sentence into a deterministic non-trivial unjumble question', () => {
    const question = heritageToUnjumble(heritage(), 42);
    expect(question).toMatchObject({
      answer: 'Я бачу дім щодня.',
      hint: 'Потрібне питоме українське слово.',
      wordsAreJumbled: true,
    });
    expect(question?.words.split(' / ')).toHaveLength(4);
    expect(new Set(question?.words.split(' / '))).toEqual(new Set(['Я', 'бачу', 'дім', 'щодня.']));
    expect(heritageToUnjumble(heritage(), 42)).toEqual(question);
  });

  test('skips short and punctuation-only unjumble sources', () => {
    expect(heritageToUnjumble(heritage({ prompt: 'Це ___.' }), 42)).toBeNull();
    expect(heritageToUnjumble(heritage({ prompt: '___ — ! ? …' }), 42)).toBeNull();
  });

  test('selects only reproducible presentation variants and preserves MC fallback', () => {
    const kinds = new Set(
      Array.from({ length: 64 }, (_unused, seed) =>
        selectHeritagePracticePresentation(heritage(), seed).kind,
      ),
    );
    expect(kinds).toEqual(new Set(['mc', 'error-correction', 'unjumble']));
    expect(selectHeritagePracticePresentation(heritage({ prompt: '___ і ___' }), 42)).toEqual({ kind: 'mc' });
  });
});
