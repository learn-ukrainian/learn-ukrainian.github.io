import { describe, expect, test } from 'vitest';
import {
  boundEvidence,
  cardHeadwordMatches,
  isNormativeLocator,
  modernHeadwordLabels,
  namesHeadword,
  normativeCitations,
  resolveHeritageBoxes,
  resolveUsageLabel,
  sharesReferent,
  type LexiconEntryForSeverity,
} from '@site/src/lib/lexicon/heritage-severity';

const SUM20_VOZNYI = 'ВО́ЗНИЙ, ного, ч., іст. Судовий урядовець у Польщі (до XIX ст.).';
const SUM20_DYVAN_SENSE = 'ДИВА́Н, у, ч. 1. іст. Дорадчий орган у султанській Туреччині. 2. М’який меблевий виріб.';
const SUM20_HOMONYM = 'ДИВА́Н ² , у, ч., іст. Дорадчий орган у султанській Туреччині.';
const SUM20_ATTACHED_HOMONYM = 'ДИВА́Н², у, ч., іст. Дорадчий орган у султанській Туреччині.';
const SUM20_HOROD = 'ГОРО́Д, а, ч. Ділянка землі, перев. при садибі, для вирощування овочів.';
const VTS_KRYN = 'крин -у, ч. , заст. Лілея.';
// Real excerpts (sources MCP: style_guide id 44 / antonenko p031; heritage_pairs normativeSupport).
const MIRO_SUPPORT = {
  locator: 'antonenko-davydovych-yak-my-hovorymo_p031',
  passage:
    '"У нас провели такі міроприємства" і под. Такого слова не було й нема в українській мові, його наспіх склепали ті, що не знали багатства нашої мови.',
};
// Stored Atlas DB evidence: it names the Russian etymon and the replacement, not the headword.
const MIRO_STORED_EVIDENCE = 'Антоненко-Давидович: Відповідником до російських мера, мероприятие є захід, а в множині — заходи';
const SLID_STORED_EVIDENCE =
  '9-klas-ukrajinska-mova-voron-2017_s0232: следующий — тут: наступний; Як правильно перекласти ... следующий? ... наступний';
const BAZH_EVIDENCE = 'antonenko-davydovych-yak-my-hovorymo_p099: Бажаючий – що (котрий, який) бажає – охочий';
const ESUM_HRYD = {
  source: 'esum',
  ref: 'гридь:1:592',
  word: 'гридь',
  detail: 'гридь (іст.) «нижча верхівка княжої дружини», грйдень «охоронець князя» Ж; — р. (іст.) гридь',
};
const HRYD_GLOSS = 'У стародавній Русі — нижча верства княжої дружини.';

describe('resolveHeritageBoxes', () => {
  test.each([
    {
      // #9603 D01: the avoid list is provenance, not authority.
      name: 'авось (surzhyk-to-avoid provenance, no bound evidence) is not RED',
      entry: {
        lemma: 'авось',
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
      expected: { red: false, yellow: false, green: false, blue: false },
    },
    {
      name: 'avoid-listed word with headword-bound normative evidence is RED (міроприємство)',
      entry: {
        lemma: 'міроприємство',
        primary_source: 'surzhyk_to_avoid',
        heritage_status: {
          classification: 'russianism',
          is_russianism: true,
          curated_calque: { kind: 'lexical', corrections: ['захід'], source: ['antonenko-p044'], normative_support: [MIRO_SUPPORT] },
        },
      },
      expected: { red: true, yellow: false, green: false, blue: false },
      alternatives: ['захід'],
    },
    {
      // #9603 D05: ``participle`` is a word-formation type, not a scope; a citation is not evidence.
      name: 'participle calque with a citation only resolves to no box',
      entry: {
        lemma: 'діючий',
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
      expected: { red: false, yellow: false, green: false, blue: false },
    },
    {
      name: 'lexical calque bound by an excerpt naming the headword is YELLOW (бажаючий)',
      entry: {
        lemma: 'бажаючий',
        heritage_status: {
          classification: 'calque',
          calque_warning: { kind: 'lexical', evidence: [BAZH_EVIDENCE], standard_alternatives: ['охочий'] },
          attestations: [],
        },
      },
      expected: { red: false, yellow: true, green: false, blue: false },
      alternatives: ['охочий'],
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
    if (!expected.red) expect(boxes.inline?.severity).not.toBe('red');

    if (alternatives) {
      expect((boxes.red ?? boxes.yellow)?.alternatives).toEqual(alternatives);
    }
  });

  test('a bound avoid-list warning names its locator and the list', () => {
    const boxes = resolveHeritageBoxes({
      lemma: 'міроприємство',
      primary_source: 'surzhyk_to_avoid',
      heritage_status: {
        classification: 'russianism',
        is_russianism: true,
        curated_calque: { kind: 'lexical', corrections: ['захід'], normative_support: [MIRO_SUPPORT] },
      },
    } as LexiconEntryForSeverity);
    expect(boxes.red?.body).toContain('antonenko-davydovych-yak-my-hovorymo_p031');
    expect(boxes.red?.body).toContain('перелік суржику');
    expect(boxes.inline?.severity).toBe('red');
  });

  // agy off-seat review #3759: the green-box body must not assert a russian
  // morphological shadow when the word has none. #9603 D06: attestation is not
  // an origin or normativity claim.
  test('green body names the attesting source role and omits the russian-shadow clause', () => {
    const noShadow = resolveHeritageBoxes({
      heritage_status: {
        classification: 'dialect',
        is_russianism: false,
        russian_shadow: false,
        vesum_attested: true,
        attestations: [{ source: 'grinchenko_1907', ref: 'x' }],
      },
    } as LexiconEntryForSeverity);
    expect(noShadow.green?.title).toBe('Засвідчена українська форма');
    expect(noShadow.green?.body).toContain('Словник Грінченка');
    expect(noShadow.green?.body).toContain('не визначає походження');
    expect(noShadow.green?.body).not.toContain('тінь');
  });

  test('VESUM-only standard word is an attested form, never «питома» (D06)', () => {
    const boxes = resolveHeritageBoxes({
      lemma: 'стіл',
      heritage_status: {
        classification: 'standard',
        russian_shadow: true,
        vesum_attested: true,
        attestations: [{ source: 'VESUM', ref: 'стіл', detail: 'lemma match' }],
      },
    } as LexiconEntryForSeverity);
    const text = `${boxes.green?.title} ${boxes.green?.body} ${boxes.inline?.label}`;
    expect(text).not.toMatch(/[Пп]итома/u);
    expect(boxes.green?.title).toBe('Засвідчена українська форма');
    expect(boxes.green?.body).toContain('VESUM (морфологічна фіксація форми)');
    expect(boxes.green?.body).toContain('тінь');
    expect(boxes.inline?.label).toBe('✓ Засвідчена українська форма');
  });

  // #7982 / #9603: a citation-only lexical record (no excerpt) states no bound scope.
  test('мисль with a citation-only calque record is unresolved, not a lemma caveat', () => {
    const boxes = resolveHeritageBoxes({
      lemma: 'мисль',
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

    expect(boxes.usageLabel).toMatchObject({ scope: 'unresolved', reason: 'no_headword_bound_evidence' });
    expect(boxes.yellow).toBeUndefined();
    expect(boxes.inline).toBeUndefined();
  });

  // #7982 / #9603: an unresolved calque claim is neutral — neither a warning nor a green defence.
  test('глагол (Грінченко archaism, citation-only calque record) gets no calque box and no green box', () => {
    const boxes = resolveHeritageBoxes({
      lemma: 'глагол',
      heritage_status: {
        classification: 'authentic-archaism',
        warning_severity: 'calque_yellow',
        is_russianism: false,
        vesum_attested: true,
        calque_warning: {
          kind: 'lexical',
          citations: ['antonenko:Як ми говоримо', 'grinchenko:глагол'],
          standard_alternatives: ['дієслово', 'слово'],
        },
        attestations: [{ source: 'grinchenko_1907', ref: '9370' }],
      },
    } as LexiconEntryForSeverity);

    expect(boxes.yellow).toBeUndefined();
    expect(boxes.usageLabel.scope).toBe('unresolved');
    expect(boxes.green).toBeUndefined();
    expect(boxes.inline).toBeUndefined();
  });

  test('вилка (sense-restricted calque) stays a contextual caveat without a headword badge', () => {
    const boxes = resolveHeritageBoxes({
      lemma: 'вилка',
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
    expect(boxes.yellow?.body).toContain('Нормативного джерела, що прямо стосується цього слова, запис не містить.');
    expect(boxes.yellow?.alternatives).toEqual(['виделка']);
    expect(boxes.inline).toBeUndefined();
    expect(boxes.green).toBeUndefined();
  });
});

// #9603 negative and positive controls: stored records keep the scope of their source.
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
    expect(boxes.green?.title).toBe('Засвідчена українська форма');
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
    expect(resolveUsageLabel(status, { headword: 'другий' }).scope).toBe('unresolved');
    const boxes = resolveHeritageBoxes({ lemma: 'другий', heritage_status: status });
    expect(boxes.red).toBeUndefined();
    expect(boxes.yellow).toBeUndefined();
    expect(boxes.inline).toBeUndefined();
  });

  test('a lexical Russianism bound by a passage naming the headword stays a lemma warning (міроприємство)', () => {
    const status = {
      classification: 'russianism',
      is_russianism: true,
      curated_calque: { kind: 'lexical', corrections: ['захід'], source: ['antonenko-p044'], normative_support: [MIRO_SUPPORT] },
    };
    expect(resolveUsageLabel(status, { headword: 'міроприємство' })).toMatchObject({
      code: 'rus',
      scope: 'lemma',
      authority: ['antonenko-davydovych-yak-my-hovorymo_p031'],
    });
    expect(resolveUsageLabel(status, { headword: 'міроприємство' }).evidence).toContain('Такого слова не було');
    // Without a headword nothing binds.
    expect(resolveUsageLabel(status).scope).toBe('unresolved');
  });

  test.each([
    {
      name: 'stored міроприємство evidence names the etymon, not the headword',
      headword: 'міроприємство',
      record: { kind: 'lexical', source: ['antonenko-p044', 'glazova-10'], evidence: [MIRO_STORED_EVIDENCE] },
      reason: 'no_headword_bound_evidence',
    },
    {
      name: 'stored слідуючий evidence is a translation drill about следующий (D01)',
      headword: 'слідуючий',
      record: { kind: 'lexical', source: ['voron-9', 'zabolotnyi-5'], evidence: [SLID_STORED_EVIDENCE] },
      reason: 'no_headword_bound_evidence',
    },
    {
      name: 'unrecognised kind with a normative citation (D05)',
      headword: 'слово',
      record: { kind: 'unspecified', source: ['antonenko-p001'] },
      reason: 'curated_kind_without_scope',
    },
    {
      name: 'lexical kind with null evidence (D05)',
      headword: 'слово',
      record: { kind: 'lexical', source: ['antonenko-p001'], evidence: null },
      reason: 'no_headword_bound_evidence',
    },
    {
      name: 'bare citation is not an excerpt',
      headword: 'бажаючий',
      record: { kind: 'lexical', evidence: ['antonenko:Бажаючий', 'antonenko:153 Крокувати, простувати, іти'] },
      reason: 'no_headword_bound_evidence',
    },
    {
      name: 'excerpt naming the headword from a non-normative source',
      headword: 'бажаючий',
      record: { kind: 'lexical', evidence: ['ua-gec-annotation: тут слово бажаючий виправлено на охочий'] },
      reason: 'no_headword_bound_evidence',
    },
    {
      name: 'a normative excerpt bound to another headword',
      headword: 'бажаний',
      record: { kind: 'lexical', evidence: [BAZH_EVIDENCE] },
      reason: 'no_headword_bound_evidence',
    },
  ])('curated record stays unresolved: $name', ({ headword, record, reason }) => {
    const label = resolveUsageLabel({ classification: 'russianism', is_russianism: true, curated_calque: record as never }, { headword });
    expect(label).toMatchObject({ code: null, scope: 'unresolved', reason });
  });

  test('a curated record citing only non-normative sources is unresolved', () => {
    for (const source of [['ua-gec:F/Calque n=2'], ['grinchenko'], ['slovnyk:foreign_shtepa'], []]) {
      const label = resolveUsageLabel({ classification: 'calque', curated_calque: { kind: 'lexical', source } }, { headword: 'слово' });
      expect(label.code).toBeNull();
      expect(label.reason).toBe('no_headword_bound_evidence');
    }
  });

  test('a phrasal calque is contextual and keeps only bound authority', () => {
    expect(resolveUsageLabel({ calque_warning: { kind: 'phrasal', citations: ['antonenko-p091'] } })).toMatchObject({
      scope: 'phrase',
      authority: [],
    });
  });

  test.each([
    { name: 'СУМ-20 headword label binds', headword: 'возний', card: ['sum20', SUM20_VOZNYI], classification: 'historism', code: 'hist' },
    { name: 'label on one sense only (диван)', headword: 'диван', card: ['sum20', SUM20_DYVAN_SENSE], classification: 'historism', code: null },
    { name: 'homonym-indexed card', headword: 'диван', card: ['sum20', SUM20_HOMONYM], classification: 'historism', code: null },
    { name: 'attached homonym index (ДИВАН²)', headword: 'диван', card: ['sum20', SUM20_ATTACHED_HOMONYM], classification: 'historism', code: null },
    { name: 'modern headword unlabelled (город)', headword: 'город', card: ['sum20', SUM20_HOROD], classification: 'authentic-archaism', code: null },
    { name: 'ВТС fallback binds', headword: 'крин', card: ['vts', VTS_KRYN], classification: 'authentic-archaism', code: 'arch' },
    // D04: a card for another headword never authorises this one.
    { name: 'mismatched headword (живий vs ВОЗНИЙ)', headword: 'живий', card: ['sum20', SUM20_VOZNYI], classification: 'historism', code: null },
    { name: 'malformed card text', headword: 'слово', card: ['sum20', 'garbage діал.'], classification: 'dialect', code: null },
    { name: 'no headword', headword: undefined, card: ['sum20', SUM20_VOZNYI], classification: 'historism', code: null },
  ])('register label: $name', ({ headword, card, classification, code }) => {
    const status = { classification };
    const definitionCards = [{ id: card[0], definitions: [card[1]] }];
    expect(resolveUsageLabel(status, { headword, definitionCards }).code).toBe(code);
    const boxes = resolveHeritageBoxes({ lemma: headword, heritage_status: status, enrichment: { definition_cards: definitionCards } });
    if (code === 'hist') expect(boxes.green?.title).toBe('Історизм');
    if (code === 'arch') expect(boxes.green?.title).toBe('Архаїзм');
    if (code === null) expect(boxes.green?.title).toBe('Засвідчена українська форма');
  });

  test('ЕСУМ headword marker with the same referent binds a historical label (гридь, D02)', () => {
    const status = { classification: 'historism', attestations: [ESUM_HRYD] };
    const label = resolveUsageLabel(status, { headword: 'гридь', gloss: HRYD_GLOSS });
    expect(label).toMatchObject({ code: 'hist', scope: 'lemma', authority: ['ЕСУМ, т. 1, с. 592'] });
    expect(label.evidence).toBe('гридь (іст.) «нижча верхівка княжої дружини»');
    const boxes = resolveHeritageBoxes({ lemma: 'гридь', gloss: HRYD_GLOSS, heritage_status: status });
    expect(boxes.green?.title).toBe('Історизм');
    expect(boxes.green?.body).toContain('ЕСУМ, т. 1, с. 592');
  });

  test.each([
    { name: 'another referent', headword: 'гридь', gloss: 'sofa; couch', attestations: [ESUM_HRYD], cards: null },
    { name: 'marker on a derivative only', headword: 'гридь', gloss: HRYD_GLOSS, attestations: [{ ...ESUM_HRYD, detail: 'гридь «нижча верхівка княжої дружини», гридниця (іст.) «приміщення»' }], cards: null },
    { name: 'attestation of another word', headword: 'гридня', gloss: HRYD_GLOSS, attestations: [ESUM_HRYD], cards: null },
    { name: 'cognate marker (або)', headword: 'або', gloss: 'or', attestations: [{ source: 'esum', ref: 'або:1:37', word: 'або', detail: 'або «чи»; — п. діал. «елементарний»' }], cards: null },
    { name: 'modern card for the headword is unlabelled', headword: 'гридь', gloss: HRYD_GLOSS, attestations: [ESUM_HRYD], cards: [{ id: 'vts', definitions: ['гридь -і, ж., збірн. Нижча верства княжої дружини.'] }] },
  ])('ЕСУМ marker does not bind: $name', ({ headword, gloss, attestations, cards }) => {
    const label = resolveUsageLabel({ classification: 'historism', attestations }, { headword, gloss, definitionCards: cards });
    expect(label.code).toBeNull();
    expect(label.scope).toBe('unresolved');
  });

  test('borrowing binds only through ЕСУМ etymology of the headword', () => {
    const status = {
      classification: 'borrowing',
      attestations: [{ source: 'esum', ref: 'диван:2:63', word: 'диван', detail: 'диван «канапа» — запозичення з турецької' }],
    };
    expect(resolveUsageLabel(status, { headword: 'диван' })).toMatchObject({ code: 'borr', authority: ['ЕСУМ, т. 2, с. 63'] });
    expect(resolveUsageLabel(status, { headword: 'канапа' }).code).toBeNull();
  });
});

describe('scoped boxes: remaining branches', () => {
  test('a bound lexical Russianism outside the avoid list is RED with its locator', () => {
    const boxes = resolveHeritageBoxes({
      lemma: 'міроприємство',
      heritage_status: {
        classification: 'russianism',
        is_russianism: true,
        curated_calque: { kind: 'lexical', normative_support: [MIRO_SUPPORT] },
      },
    } as LexiconEntryForSeverity);
    expect(boxes.red?.body).toContain('antonenko-davydovych-yak-my-hovorymo_p031');
    expect(boxes.red?.body).not.toContain('перелік суржику');
    expect(boxes.red?.body).toContain('Перевіряйте рекомендовані відповідники');
  });

  test('a phrasal caution is titled for the collocation and lists record references', () => {
    const boxes = resolveHeritageBoxes({
      lemma: 'приймати',
      heritage_status: {
        classification: 'standard',
        calque_warning: { kind: 'phrasal', citations: ['antonenko-p091'], standard_alternatives: ['брати участь'] },
      },
    } as LexiconEntryForSeverity);
    expect(boxes.yellow?.title).toBe('Калькове застереження щодо сполучення');
    expect(boxes.yellow?.body).toContain('Посилання запису (без витягу з джерела): antonenko-p091.');
  });

  test('form_of entries get the label but no boxes', () => {
    const boxes = resolveHeritageBoxes({ lemma: 'вози', form_of: 'віз', heritage_status: { classification: 'standard' } });
    expect(boxes).toEqual({ usageLabel: { code: null, scope: 'none', authority: [], evidence: null, reason: 'none' } });
  });

  test('green body names literary attestations and a dialect register bound by СУМ-20', () => {
    const literary = resolveHeritageBoxes({
      lemma: 'слово',
      heritage_status: { classification: 'standard', attestations: [{ source: 'literary_fts', ref: 'x' }] },
    } as LexiconEntryForSeverity);
    expect(literary.green?.body).toContain('художні тексти');
    const dialect = resolveHeritageBoxes({
      lemma: 'ґазда',
      heritage_status: { classification: 'dialect' },
      enrichment: { definition_cards: [{ id: 'sum20', definitions: ['ҐАЗДА́, и́, ч., діал. Господар.'] }] },
    } as LexiconEntryForSeverity);
    expect(dialect.green?.title).toBe('Діалектне слово');
    expect(dialect.green?.body).toContain('ҐАЗДА');
    expect(dialect.inline?.label).toBe('✓ Засвідчена українська форма');
  });

  test('ЕСУМ marker of another register class does not bind; II marks a homonym card', () => {
    expect(
      resolveUsageLabel({ classification: 'dialect', attestations: [ESUM_HRYD] }, { headword: 'гридь', gloss: HRYD_GLOSS }).code,
    ).toBeNull();
    expect(modernHeadwordLabels('СТАН, у, ч. заст. Тулуб. II СТАН, у, ч. Становище.').ambiguous).toBe(true);
    expect(cardHeadwordMatches('«ГОРОД», а, ч. Ділянка.', 'город')).toBe(true);
  });
});

describe('scope helpers', () => {
  test.each([
    [SUM20_VOZNYI, ['historism'], false],
    [SUM20_DYVAN_SENSE, [], false],
    [SUM20_HOMONYM, ['historism'], true],
    [SUM20_ATTACHED_HOMONYM, ['historism'], true],
    [SUM20_HOROD, [], false],
    [VTS_KRYN, ['authentic-archaism'], false],
    ['ХВІСТ, хвоста́, ч. Задня частина тіла.', [], false],
  ])('modernHeadwordLabels(%s)', (definition, classes, ambiguous) => {
    const result = modernHeadwordLabels(definition as string);
    expect([...result.classes]).toEqual(classes);
    expect(result.ambiguous).toBe(ambiguous);
  });

  test('cardHeadwordMatches binds a card to its own headword only', () => {
    expect(cardHeadwordMatches(SUM20_VOZNYI, 'возний')).toBe(true);
    expect(cardHeadwordMatches(SUM20_VOZNYI, 'живий')).toBe(false);
    expect(cardHeadwordMatches(SUM20_ATTACHED_HOMONYM, 'диван')).toBe(true);
    expect(cardHeadwordMatches(VTS_KRYN, 'крин')).toBe(true);
    expect(cardHeadwordMatches('garbage діал.', 'слово')).toBe(false);
    expect(cardHeadwordMatches('БРА́ТИ УЧА́СТЬ, у чому. Бути учасником.', 'брати участь')).toBe(true);
    expect(cardHeadwordMatches(SUM20_VOZNYI, '')).toBe(false);
  });

  test('namesHeadword allows inflection only for longer single words', () => {
    expect(namesHeadword(MIRO_SUPPORT.passage, 'міроприємство')).toBe(true);
    expect(namesHeadword(SLID_STORED_EVIDENCE, 'слідуючий')).toBe(false);
    expect(namesHeadword('Вид — це не тип.', 'вид')).toBe(true);
    expect(namesHeadword('Види бувають різні.', 'вид')).toBe(false);
    expect(namesHeadword('Тут треба брати участь у грі.', 'брати участь')).toBe(true);
    expect(namesHeadword('Тут треба брати у грі участь.', 'брати участь')).toBe(false);
    expect(namesHeadword('будь-що', undefined)).toBe(false);
  });

  test('isNormativeLocator recognises style guides and textbook chunks only', () => {
    expect(isNormativeLocator('antonenko-davydovych-yak-my-hovorymo_p031')).toBe(true);
    expect(isNormativeLocator('Антоненко-Давидович')).toBe(true);
    expect(isNormativeLocator('11-klas-ukrajinska-mova-avramenko-2019_s0074')).toBe(true);
    expect(isNormativeLocator('voron-9')).toBe(false);
    expect(isNormativeLocator('ua-gec')).toBe(false);
    expect(isNormativeLocator('5-klas-istoriya-hisem-2022_s0001')).toBe(false);
  });

  test('boundEvidence keeps only normative excerpts that name the headword', () => {
    expect(boundEvidence({ evidence: [BAZH_EVIDENCE, MIRO_STORED_EVIDENCE] }, 'бажаючий')).toEqual([
      ['antonenko-davydovych-yak-my-hovorymo_p099', 'Бажаючий – що (котрий, який) бажає – охочий'],
    ]);
    expect(boundEvidence({ normativeSupport: [MIRO_SUPPORT, { locator: '', passage: 'x' }] }, 'міроприємство')).toHaveLength(1);
    expect(boundEvidence({}, 'слово')).toEqual([]);
  });

  test('sharesReferent compares content words only', () => {
    expect(sharesReferent('нижча верхівка княжої дружини', HRYD_GLOSS)).toBe(true);
    expect(sharesReferent('нижча верхівка княжої дружини', 'sofa')).toBe(false);
    expect(sharesReferent('у на до', 'у на до')).toBe(false);
    expect(sharesReferent('дружини', null)).toBe(false);
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
