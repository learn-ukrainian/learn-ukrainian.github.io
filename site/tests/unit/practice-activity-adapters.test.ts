import { describe, expect, test } from 'vitest';
import {
  heritageToErrorCorrection,
  heritageToFillIn,
  heritageToMarkTheWords,
  heritageToMatchUp,
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

  test('adapts a reviewed single blank and its source choices into FillIn props', () => {
    expect(heritageToFillIn(heritage())).toEqual({
      sentence: 'Я бачу ___ щодня.',
      answer: 'дім',
      options: ['дім', 'дом', 'хата', 'місто'],
    });
    expect(heritageToFillIn(heritage({ prompt: 'Я бачу ___ і ___ щодня.' }))).toBeNull();
  });

  test('marks only the exact reviewed replacement span in a corrected frame', () => {
    expect(heritageToMarkTheWords(heritage())).toEqual({
      text: 'Я бачу дім щодня.',
      correctWords: ['дім'],
      instruction: 'Позначте питоме українське слово або сполуку.',
    });
    expect(heritageToMarkTheWords(heritage({ prompt: 'Я бачу ___ і ___ щодня.' }))).toBeNull();
    expect(
      heritageToMarkTheWords(
        heritage({
          prompt: 'Я бачу ___, бо мій сад поруч.',
          answer: 'мій дім',
          calque: 'мой дом',
          options: [{ label: 'мій дім' }, { label: 'мой дом' }],
        }),
      ),
    ).toBeNull();
  });

  test('builds a distinct, source-backed match-up board that includes the scheduled card', () => {
    const companions = [
      heritage(),
      heritage({
        heritageId: 'heritage-adapter-fixture-2',
        lemmaId: 'knyha',
        srsKey: cardKey('knyha', 'heritage'),
        prompt: 'Я читаю ___ щодня.',
        answer: 'книгу',
        calque: 'кнігу',
        options: [{ label: 'книгу' }, { label: 'кнігу' }, { label: 'газету' }],
      }),
      heritage({
        heritageId: 'heritage-adapter-fixture-3',
        lemmaId: 'oselia',
        srsKey: cardKey('oselia', 'heritage'),
        prompt: 'Вона повернулася до ___ ввечері.',
        answer: 'оселі',
        calque: 'дому',
        options: [{ label: 'оселі' }, { label: 'дому' }, { label: 'школи' }],
      }),
    ];
    expect(heritageToMatchUp(companions[0]!, companions, 42)).toEqual({
      pairs: [
        { left: 'дом', right: 'дім', lemmaId: 'dim' },
        { left: 'дому', right: 'оселі', lemmaId: 'oselia' },
        { left: 'кнігу', right: 'книгу', lemmaId: 'knyha' },
      ],
    });
    expect(heritageToMatchUp(heritage(), [heritage()], 42)).toBeNull();
  });

  test('selects only reproducible presentation variants and preserves MC fallback', () => {
    const kinds = new Set(
      Array.from(
        { length: 64 },
        (_unused, seed) => selectHeritagePracticePresentation(heritage(), seed).kind,
      ),
    );
    expect(kinds).toEqual(
      new Set(['mc', 'error-correction', 'unjumble', 'fill-in', 'mark-the-words']),
    );
    expect(selectHeritagePracticePresentation(heritage({ prompt: '___ і ___' }), 42)).toEqual({
      kind: 'mc',
    });
  });

  test('selects match-up only when the source set can form a real board', () => {
    const companions = [
      heritage(),
      heritage({
        heritageId: 'heritage-adapter-fixture-2',
        lemmaId: 'knyha',
        srsKey: cardKey('knyha', 'heritage'),
        prompt: 'Я читаю ___ щодня.',
        answer: 'книгу',
        calque: 'кнігу',
        options: [{ label: 'книгу' }, { label: 'кнігу' }, { label: 'газету' }],
      }),
    ];
    const kinds = new Set(
      Array.from(
        { length: 128 },
        (_unused, seed) =>
          selectHeritagePracticePresentation(companions[0]!, seed, companions).kind,
      ),
    );
    expect(kinds).toContain('match-up');
  });
});
