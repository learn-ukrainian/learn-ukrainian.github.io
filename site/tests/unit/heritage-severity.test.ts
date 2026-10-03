import { describe, expect, test } from 'vitest';
import {
  modernHeadwordLabels,
  normativeCitations,
  resolveHeritageBoxes,
  resolveUsageLabel,
  type LexiconEntryForSeverity,
} from '@site/src/lib/lexicon/heritage-severity';

const SUM20_VOZNYI = 'ВО́ЗНИЙ, ного, ч., іст. Судовий урядовець у Польщі (до XIX ст.).';
const SUM20_DYVAN_SENSE = 'ДИВА́Н, у, ч. 1. іст. Дорадчий орган у султанській Туреччині. 2. М’який меблевий виріб.';
const SUM20_HOMONYM = 'ДИВА́Н ² , у, ч., іст. Дорадчий орган у султанській Туреччині.';
const SUM20_HOROD = 'ГОРО́Д, а, ч. Ділянка землі, перев. при садибі, для вирощування овочів.';
const VTS_KRYN = 'крин -у, ч. , заст. Лілея.';

describe('resolveHeritageBoxes', () => {
  test.each([
    {
      name: 'авось (surzhyk-to-avoid provenance) resolves to RED and parses avoid gloss alternatives',
      entry: {
        gloss: 'avoid: ану ж / а може',
        primary_source: 'surzhyk_to_avoid',
        heritage_status: {
          classification: 'unknown',
          is_russianism: true,
          russian_shadow: true,
          vesum_attested: false,
          warning_severity: 'russianism_red',
          attestations: [],
        },
      },
      expected: { red: true, yellow: false, green: false, blue: false },
      alternatives: ['ану ж', 'а може'],
    },
    {
      name: 'named lexical calque resolves to YELLOW',
      entry: {
        gloss: 'acting',
        heritage_status: {
          classification: 'unknown',
          warning_severity: 'calque_yellow',
          calque_warning: {
            kind: 'participle',
            citations: ['antonenko-p144'],
            detail: 'Калька з російської активної дієприкметникової моделі.',
            standard_alternatives: ['чинний'],
          },
          attestations: [],
        },
      },
      expected: { red: false, yellow: true, green: false, blue: false },
      alternatives: ['чинний'],
    },
    {
      name: 'dialect labelled on the СУМ-20 headword resolves to GREEN',
      entry: {
        lemma: 'ґазда',
        heritage_status: {
          classification: 'dialect',
          is_russianism: false,
          russian_shadow: true,
          vesum_attested: false,
          attestations: [],
        },
        enrichment: { definition_cards: [{ id: 'sum20', definitions: ['ҐАЗДА́, и́, ч., діал. Господар.'] }] },
      },
      expected: { red: false, yellow: false, green: true, blue: false },
    },
    {
      name: 'прапор sovietized definition resolves to BLUE',
      entry: {
        heritage_status: {
          classification: 'standard',
          is_russianism: false,
          russian_shadow: false,
          attestations: [],
        },
        enrichment: {
          definition_cards: [{ id: 'sum11-flagged-прапор', sovietization_risk: 2 }],
        },
      },
      expected: { red: false, yellow: false, green: false, blue: true },
    },
    {
      name: 'russian_shadow with VESUM and no alternative resolves to no box',
      entry: {
        heritage_status: {
          classification: 'unknown',
          is_russianism: false,
          russian_shadow: true,
          vesum_attested: true,
          attestations: [{ source: 'VESUM', ref: 'форма' }],
        },
      },
      expected: { red: false, yellow: false, green: false, blue: false },
    },
    {
      name: 'russian_shadow plus standard classification is not RED',
      entry: {
        heritage_status: {
          classification: 'standard',
          is_russianism: true,
          russian_shadow: true,
          vesum_attested: false,
          attestations: [],
        },
      },
      expected: { red: false, yellow: false, green: false, blue: false },
    },
    {
      // #9603: a Russian morphological shadow alone is never normative authority.
      name: 'russian_shadow-only unknown word with stale RED severity resolves to no box',
      entry: {
        heritage_status: {
          classification: 'unknown',
          is_russianism: false,
          russian_shadow: true,
          vesum_attested: false,
          warning_severity: 'russianism_red',
          attestations: [],
        },
      },
      expected: { red: false, yellow: false, green: false, blue: false },
    },
  ])('$name', ({ entry, expected, alternatives }) => {
    const boxes = resolveHeritageBoxes(entry as LexiconEntryForSeverity);

    expect(Boolean(boxes.red)).toBe(expected.red);
    expect(Boolean(boxes.yellow)).toBe(expected.yellow);
    expect(Boolean(boxes.green)).toBe(expected.green);
    expect(Boolean(boxes.blue)).toBe(expected.blue);

    if (alternatives) {
      expect((boxes.red ?? boxes.yellow)?.alternatives).toEqual(alternatives);
    }
  });

  // agy off-seat review #3759: the green-box body must not assert a russian
  // morphological shadow when the word has none.
  test('green body omits the russian-shadow clause when russian_shadow is false', () => {
    const noShadow = resolveHeritageBoxes({
      heritage_status: {
        classification: 'dialect',
        is_russianism: false,
        russian_shadow: false,
        vesum_attested: true,
        attestations: [{ source: 'grinchenko_1907', ref: 'x' }],
      },
    } as LexiconEntryForSeverity);
    expect(noShadow.green?.body).toContain('підтвердження');
    expect(noShadow.green?.body).not.toContain('тінь');
  });

  // #7982: Pre-Soviet false-positive defenses for convergence calques
  test('мисль resolves to yellow calque box with думка alternative and Ukrainian rationale', () => {
    const boxes = resolveHeritageBoxes({
      heritage_status: {
        classification: 'calque',
        warning_severity: 'calque_yellow',
        is_russianism: false,
        vesum_attested: true,
        calque_warning: {
          kind: 'lexical',
          citations: ['antonenko:Як ми говоримо'],
          noteUk: 'У сучасній українській літературній мові нормативним і нейтральним відповідником є «думка».',
          standard_alternatives: ['думка'],
        },
        attestations: [{ source: 'VESUM', ref: 'мисль' }],
      },
    } as LexiconEntryForSeverity);

    expect(boxes.yellow).toBeDefined();
    expect(boxes.yellow?.scope).toBe('lemma');
    expect(boxes.yellow?.title).toBe('Калькове застереження');
    expect(boxes.yellow?.body).toContain('antonenko:Як ми говоримо');
    expect(boxes.yellow?.alternatives).toEqual(['думка']);
    expect(boxes.yellow?.detail).toContain('нормативним і нейтральним відповідником є «думка»');
    expect(boxes.inline?.label).toBe('Калькове застереження');
    expect(boxes.green).toBeUndefined();
  });

  test('глагол (Грінченко archaism with named calque record) resolves to a lemma calque caveat', () => {
    const boxes = resolveHeritageBoxes({
      heritage_status: {
        classification: 'authentic-archaism',
        warning_severity: 'calque_yellow',
        is_russianism: false,
        vesum_attested: true,
        calque_warning: {
          kind: 'lexical',
          citations: ['antonenko:Як ми говоримо', 'grinchenko:глагол'],
          noteUk: 'У нейтральному сучасному вжитку слід послуговуватися «дієслово» або «слово».',
          standard_alternatives: ['дієслово', 'слово'],
        },
        attestations: [{ source: 'grinchenko_1907', ref: '9370' }],
      },
    } as LexiconEntryForSeverity);

    expect(boxes.yellow).toBeDefined();
    expect(boxes.yellow?.scope).toBe('lemma');
    expect(boxes.usageLabel.authority).toEqual(['antonenko:Як ми говоримо']);
    expect(boxes.yellow?.alternatives).toEqual(['дієслово', 'слово']);
    expect(boxes.green).toBeUndefined();
  });

  test('вилка (sense-restricted calque) stays a contextual caveat without a headword badge', () => {
    const boxes = resolveHeritageBoxes({
      heritage_status: {
        classification: 'standard',
        warning_severity: 'calque_yellow',
        is_russianism: false,
        vesum_attested: true,
        calque_warning: {
          kind: 'sense_restricted',
          noteUk: 'Столовий прибор для їжі в українській мові називається винятково «виделка».',
          standard_alternatives: ['виделка'],
          calque_sense: 'столовий прибор',
          authentic_sense: 'технічна деталь або шаховий термін',
        },
        attestations: [{ source: 'VESUM', ref: 'вилка' }],
      },
    } as LexiconEntryForSeverity);

    expect(boxes.yellow).toBeDefined();
    expect(boxes.yellow?.scope).toBe('sense');
    expect(boxes.yellow?.title).toBe('Калькове застереження щодо окремого значення');
    expect(boxes.yellow?.body).toContain('«столовий прибор»');
    expect(boxes.yellow?.body).toContain('а не слова загалом');
    expect(boxes.yellow?.alternatives).toEqual(['виделка']);
    expect(boxes.inline).toBeUndefined();
    expect(boxes.green).toBeUndefined();
  });
});

// #9603 negative controls: stored records keep the scope of their source.
describe('resolveUsageLabel', () => {
  test('a reverse calque never brands its recommended replacement (бути)', () => {
    const status = {
      classification: 'standard',
      attestations: [{ source: 'VESUM', ref: 'бути' }],
      is_russianism: false,
      russian_shadow: false,
      vesum_attested: true,
      warning_severity: 'calque_yellow' as const,
      reverse_calques: [{ calque: 'являтися', kind: 'sense_restricted', source: ['avramenko-9'] }],
    };
    expect(resolveUsageLabel(status, { headword: 'бути' })).toEqual({
      code: null,
      scope: 'reverse',
      authority: [],
      evidence: null,
      reason: 'reverse',
    });
    const boxes = resolveHeritageBoxes({ lemma: 'бути', heritage_status: status });
    expect(boxes.yellow).toBeUndefined();
    expect(boxes.red).toBeUndefined();
    expect(boxes.green?.title).toBe('Питома українська лексика');
  });

  test('a stale reconciled Russianism with only a replacement is unresolved (другий)', () => {
    const status = {
      classification: 'russianism',
      attestations: [
        { source: 'VESUM', ref: 'другий' },
        { source: 'standard_alternative', ref: 'інший' },
      ],
      is_russianism: true,
      russian_shadow: true,
      vesum_attested: true,
      calque_warning: { standard_alternatives: ['інший'] },
      warning_severity: 'russianism_red' as const,
    };
    expect(resolveUsageLabel(status).scope).toBe('unresolved');
    const boxes = resolveHeritageBoxes({ lemma: 'другий', heritage_status: status });
    expect(boxes.red).toBeUndefined();
    expect(boxes.yellow).toBeUndefined();
    expect(boxes.inline).toBeUndefined();
  });

  test('a named lexical Russianism stays a lemma warning (міроприємство)', () => {
    const status = {
      classification: 'russianism',
      is_russianism: true,
      curated_calque: { kind: 'lexical', corrections: ['захід'], source: ['antonenko-p044', 'glazova-10'] },
    };
    expect(resolveUsageLabel(status)).toMatchObject({ code: 'rus', scope: 'lemma', authority: ['antonenko-p044', 'glazova-10'] });
    const boxes = resolveHeritageBoxes({ lemma: 'міроприємство', heritage_status: status });
    expect(boxes.red?.body).toContain('antonenko-p044');
    expect(boxes.inline?.severity).toBe('red');
  });

  test('a curated record without a named normative authority is unresolved', () => {
    for (const source of [['ua-gec:F/Calque n=2'], ['grinchenko'], ['slovnyk:foreign_shtepa'], []]) {
      const label = resolveUsageLabel({ classification: 'calque', curated_calque: { kind: 'lexical', source } });
      expect(label.code).toBeNull();
      expect(label.reason).toBe('curated_record_without_named_authority');
    }
  });

  test('a phrasal calque is contextual', () => {
    expect(resolveUsageLabel({ calque_warning: { kind: 'phrasal', citations: ['antonenko-p091'] } }).scope).toBe('phrase');
  });

  test.each([
    { name: 'СУМ-20 headword label binds', status: { classification: 'historism' }, card: ['sum20', SUM20_VOZNYI], code: 'hist' },
    { name: 'label on one sense only (диван)', status: { classification: 'historism' }, card: ['sum20', SUM20_DYVAN_SENSE], code: null },
    { name: 'homonym-indexed card', status: { classification: 'historism' }, card: ['sum20', SUM20_HOMONYM], code: null },
    { name: 'modern headword unlabelled (город)', status: { classification: 'authentic-archaism' }, card: ['sum20', SUM20_HOROD], code: null },
    { name: 'ВТС fallback binds', status: { classification: 'authentic-archaism' }, card: ['vts', VTS_KRYN], code: 'arch' },
    {
      name: 'ЕСУМ cognate marker without a modern dictionary (або)',
      status: {
        classification: 'dialect',
        attestations: [{ source: 'esum', ref: 'або:1:37', word: 'або', detail: 'або «чи»; — п. діал. «елементарний»' }],
      },
      card: null,
      code: null,
    },
  ])('treasured label: $name', ({ status, card, code }) => {
    const definitionCards = card ? [{ id: card[0], definitions: [card[1]] }] : null;
    const label = resolveUsageLabel(status, { headword: 'слово', definitionCards });
    expect(label.code).toBe(code);
    const boxes = resolveHeritageBoxes({ lemma: 'слово', heritage_status: status, enrichment: { definition_cards: definitionCards } });
    if (code === 'hist') expect(boxes.green?.title).toBe('Історизм у сучасному вжитку');
    if (code === null) expect(boxes.green?.title ?? 'Питома українська лексика').toBe('Питома українська лексика');
  });

  test('borrowing binds only through ЕСУМ etymology of the headword', () => {
    const status = {
      classification: 'borrowing',
      attestations: [{ source: 'esum', ref: 'диван:2:63', word: 'диван', detail: 'диван «канапа» — запозичення з турецької' }],
    };
    expect(resolveUsageLabel(status, { headword: 'диван' }).code).toBe('borr');
    expect(resolveUsageLabel(status, { headword: 'канапа' }).code).toBeNull();
  });
});

describe('scope helpers', () => {
  test.each([
    [SUM20_VOZNYI, ['historism'], false],
    [SUM20_DYVAN_SENSE, [], false],
    [SUM20_HOMONYM, ['historism'], true],
    [SUM20_HOROD, [], false],
    [VTS_KRYN, ['authentic-archaism'], false],
    ['ХВІСТ, хвоста́, ч. Задня частина тіла.', [], false],
  ])('modernHeadwordLabels(%s)', (definition, classes, ambiguous) => {
    const result = modernHeadwordLabels(definition as string);
    expect([...result.classes]).toEqual(classes);
    expect(result.ambiguous).toBe(ambiguous);
  });

  test('normativeCitations matches the Python contract', () => {
    expect(normativeCitations(['antonenko-p044', 'glazova-10', 'ua-gec', 'grinchenko', 'sum-11', 'grok-3098'])).toEqual([
      'antonenko-p044',
      'glazova-10',
    ]);
    expect(normativeCitations(['slovnyk:davydov', 'slovnyk:foreign_shtepa', 'state-standard', 'state-standard:avramenko-7'])).toEqual([
      'slovnyk:davydov',
      'state-standard:avramenko-7',
    ]);
    expect(normativeCitations('antonenko-p091')).toEqual(['antonenko-p091']);
    expect(normativeCitations(undefined)).toEqual([]);
  });
});
