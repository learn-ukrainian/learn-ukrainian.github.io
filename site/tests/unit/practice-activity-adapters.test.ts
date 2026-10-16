import { describe, expect, test } from 'vitest';
import {
  heritageToErrorCorrection,
  heritageToFillIn,
  heritageToMarkTheWords,
  heritageToMatchUp,
  heritageToUnjumble,
  selectHeritagePracticePresentation,
  type HeritagePracticeContext,
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
  test('#10705 P14 baseline: unknown and disallowed contexts exclude sentence ordering', () => {
    for (const context of [{ source: 'unknown' }, { source: 'stored', level: 'B2' }] as const) {
      const kinds = new Set(Array.from({ length: 64 }, (_, seed) =>
        selectHeritagePracticePresentation(heritage(), seed, [], context).kind));
      expect(kinds).toEqual(new Set(['mc', 'error-correction', 'fill-in', 'mark-the-words']));
    }
  });
  test.each(['A1', 'A2', 'B1'] as const)('#10705 preserves literal allowed-context seed choices for %s', (level) => {
    const context: HeritagePracticeContext = { source: 'stored', level };
    expect(Array.from({ length: 16 }, (_, seed) =>
      selectHeritagePracticePresentation(heritage(), seed, [], context).kind)).toEqual([
      'fill-in', 'unjumble', 'unjumble', 'mc',
      'mark-the-words', 'unjumble', 'fill-in', 'mark-the-words',
      'mc', 'mark-the-words', 'fill-in', 'error-correction',
      'mark-the-words', 'error-correction', 'unjumble', 'mc',
    ]);
    expect(selectHeritagePracticePresentation(heritage(), 1, [], context)).toEqual({
      kind: 'unjumble',
      item: {
        words: 'дім / щодня. / бачу / Я',
        answer: 'Я бачу дім щодня.',
        hint: 'Потрібне питоме українське слово.',
        wordsAreJumbled: true,
      },
    });
  });

  test.each(['B2', 'C1', 'C2', null] as const)('#10705 filters before modulo for %s and retains every alternative', (level) => {
    const context: HeritagePracticeContext = level === null
      ? { source: 'unknown' } : { source: 'stored', level };
    expect(Array.from({ length: 16 }, (_, seed) =>
      selectHeritagePracticePresentation(heritage(), seed, [], context).kind)).toEqual([
      'error-correction', 'mc', 'mark-the-words', 'mc',
      'mark-the-words', 'fill-in', 'mark-the-words', 'mark-the-words',
      'mark-the-words', 'error-correction', 'error-correction', 'mc',
      'fill-in', 'fill-in', 'mc', 'fill-in',
    ]);
    const companions = [heritage(), heritage({
      heritageId: 'heritage-adapter-fixture-2', lemmaId: 'knyha', srsKey: cardKey('knyha', 'heritage'),
      prompt: 'Я читаю ___ щодня.', answer: 'книгу', calque: 'кнігу',
      options: [{ label: 'книгу' }, { label: 'кнігу' }, { label: 'газету' }],
    })];
    expect(new Set(Array.from({ length: 128 }, (_, seed) =>
      selectHeritagePracticePresentation(companions[0]!, seed, companions, context).kind)))
      .toEqual(new Set(['mc', 'error-correction', 'fill-in', 'match-up', 'mark-the-words']));
    expect(selectHeritagePracticePresentation(heritage({ prompt: '___ і ___' }), 1, [], context))
      .toEqual({ kind: 'mc' });
  });

  test('#10705 explicit context never overrides structural eligibility and default context fails closed', () => {
    for (let seed = 0; seed < 64; seed += 1) {
      expect(selectHeritagePracticePresentation(heritage({ prompt: 'Це ___.' }), seed, [],
        { source: 'local', level: 'A1' }).kind).not.toBe('unjumble');
      expect(selectHeritagePracticePresentation(heritage(), seed).kind).not.toBe('unjumble');
    }
  });

  test('#10705 conditional resume uses the same context and presentation inputs', () => {
    const item = heritage();
    const context: HeritagePracticeContext = { source: 'local', level: 'A2' };
    expect(selectHeritagePracticePresentation(item, 1, [], context))
      .toEqual(selectHeritagePracticePresentation({ ...item }, 1, [], { ...context }));
    expect(selectHeritagePracticePresentation(item, 1, [], { source: 'unknown' }))
      .toEqual({ kind: 'mc' });
    expect(selectHeritagePracticePresentation({ ...item, prompt: 'Це ___.', }, 1, [], context).kind)
      .not.toBe('unjumble');
    expect(item.srsKey).toBe('dim::heritage');
  });

  // Exact source frames from registry/lexicon/heritage_pairs.yaml at issue #7769.
  test.each([
    ["Ти вже хочби пильнував вилову, а ___ розтрусив на подвір'ї найліпшу рибу.", 'тим', 'то'],
    ['___ ви хочете і звідки ви? — Наша батьківщина Рука так далеко звідси, що навряд чи вістка про неї дійшла сюди.', 'Чим', 'Що'],
    ['а ___ розтрусив', 'тим', 'то'],
    ['___ ви хочете', 'Чим', 'Що'],
  ])('refuses isolated function-word corrections in %s', (prompt, calque, answer) => {
    const item = heritage({ prompt, calque, answer, options: [{ label: answer }, { label: calque }] });
    expect(heritageToErrorCorrection(item)).toBeNull();
    expect(heritageToFillIn(item)).toBeNull();
    expect(heritageToMarkTheWords(item)).toBeNull();
    expect(heritageToMatchUp(item, [item, heritage()], 42)).toBeNull();
    for (let seed = 0; seed < 64; seed += 1) {
      expect(['mc', 'unjumble']).toContain(
        selectHeritagePracticePresentation(item, seed, [item, heritage()], { source: 'stored', level: 'A2' }).kind,
      );
    }
  });

  test.each(['чим', 'тим', 'що', 'то', 'так', 'як', 'чи', 'би', 'та', 'ЧИМ', 'ти́м'])(
    'fails closed for the isolated function-word target %s', (calque) => {
      const item = heritage({ calque });
      expect(heritageToErrorCorrection(item)).toBeNull();
      expect(heritageToFillIn(item)).toBeNull();
      expect(heritageToMarkTheWords(item)).toBeNull();
    },
  );

  test.each([
    ['___ більше, тим краще.', 'Чим', 'Що', true, false],
    ['Чим більше, ___ краще.', 'тим', 'то', true, false],
    ['___ більше, то краще.', 'Чим', 'Що', false, true],
    ['Що більше, ___ краще.', 'тим', 'то', false, true],
  ])('requires the pair in the displayed frame: %s', (prompt, calque, answer, errorAllowed, markAllowed) => {
    const item = heritage({ prompt, calque, answer, options: [{ label: answer }, { label: calque }] });
    expect(heritageToErrorCorrection(item) !== null).toBe(errorAllowed);
    expect(heritageToFillIn(item)).not.toBeNull();
    expect(heritageToMarkTheWords(item) !== null).toBe(markAllowed);
    // Even a complete source frame is lost on a match-up board.
    expect(heritageToMatchUp(item, [item, heritage()], 42)).toBeNull();
  });

  test.each([
    'Тим краще, ___ більше.',
    '___ більше. Тим краще.',
    '___ більше, тимчасом краще.',
    '___ ви хочете? Чим більше, тим краще.',
  ])('does not accept reversed, substring, or unrelated pairs: %s', (prompt) => {
    const item = heritage({ prompt, calque: 'Чим', answer: 'Що', options: [{ label: 'Що' }, { label: 'Чим' }] });
    expect(heritageToErrorCorrection(item)).toBeNull();
    expect(heritageToFillIn(item)).toBeNull();
    expect(heritageToMarkTheWords(item)).toBeNull();
  });

  test('excludes isolated function-word companions from match-up boards', () => {
    const item = heritage();
    const companion = heritage({ heritageId: 'isolated', calque: 'тим', answer: 'то', options: [{ label: 'то' }] });
    expect(heritageToMatchUp(item, [item, companion], 42)).toBeNull();
  });

  // Authored span frames from registry/lexicon/heritage_pairs.yaml for «чим … тим» -> «що … то».
  test.each([
    ['___ більше деформоване тіло, тим більшими є сили пружності.', 'Чим', 'Що'],
    ['Чим більше деформоване тіло, ___ більшими є сили пружності.', 'тим', 'то'],
    ['___ більше набігали татари, тим далі посувався на північ український люд.', 'Чим', 'Що'],
    ['Чим більше набігали татари, ___ далі посувався на північ український люд.', 'тим', 'то'],
  ])('allows error-correction and fill-in for authored span frame: %s', (prompt, calque, answer) => {
    const item = heritage({ prompt, calque, answer, options: [{ label: answer }, { label: calque }] });
    const ec = heritageToErrorCorrection(item);
    expect(ec).not.toBeNull();
    expect(ec?.errorWord).toBe(calque);
    expect(ec?.correctForm).toBe(answer);
    expect(heritageToFillIn(item)).not.toBeNull();
    // Function-word targets must never be presented on a contextless match-up board.
    expect(heritageToMatchUp(item, [item, heritage()], 42)).toBeNull();
  });

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
        (_unused, seed) => selectHeritagePracticePresentation(heritage(), seed, [], { source: 'stored', level: 'A2' }).kind,
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
          selectHeritagePracticePresentation(companions[0]!, seed, companions, { source: 'stored', level: 'A2' }).kind,
      ),
    );
    expect(kinds).toContain('match-up');
  });
});
