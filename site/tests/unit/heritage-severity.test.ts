// @vitest-environment node
import { describe, expect, test } from 'vitest';
import {
  atlasNoteDetail,
  cardHeadwordMatches,
  displayGloss,
  modernHeadwordLabels,
  resolveHeritageBoxes,
  resolveUsageLabel,
  sharesReferent,
  usageSourceProof,
  type LexiconEntryForSeverity,
  type UsageLabel,
  type UsageSourceProof,
} from '@site/src/lib/lexicon/heritage-severity';
import { articleProps } from '../helpers/word-atlas-record';

const SUM20_VOZNYI = 'ВО́ЗНИЙ, ного, ч., іст. Судовий урядовець у Польщі (до XIX ст.).';
const SUM20_DYVAN_SENSE = 'ДИВА́Н, у, ч. 1. іст. Дорадчий орган у султанській Туреччині. 2. М’який меблевий виріб.';
const SUM20_HOMONYM = 'ДИВА́Н ² , у, ч., іст. Дорадчий орган у султанській Туреччині.';
const SUM20_ATTACHED_HOMONYM = 'ДИВА́Н², у, ч., іст. Дорадчий орган у султанській Туреччині.';
const SUM20_HOROD = 'ГОРО́Д, а, ч. Ділянка землі, перев. при садибі, для вирощування овочів.';
const VTS_KRYN = 'крин -у, ч. , заст. Лілея.';
// Real passage (heritage_pairs normativeSupport p031; sources MCP style_guide id 44).
const MIRO_PASSAGE =
  '"У нас провели такі міроприємства" і под. Такого слова не було й нема в українській мові, його наспіх склепали ті, що не знали багатства нашої мови.';
// Current curated proof as projected into browse meta: a reviewed judgment rejecting the headword.
const MIRO_PROOF: UsageSourceProof = {
  kind: 'lexical',
  corrections: ['захід'],
  sense: 'an organized charitable event',
  citations: [],
  judgments: [
    {
      locator: 'antonenko-davydovych-yak-my-hovorymo_p031',
      passage: MIRO_PASSAGE,
      passageSha256: 'fixture',
      rejectedForm: 'міроприємство',
      endorsedForm: 'захід',
      sense: 'an organized charitable event',
    },
  ],
};
// Stored Atlas DB evidence: it names the Russian etymon and the replacement, not the headword.
const MIRO_STORED_EVIDENCE = 'Антоненко-Давидович: Відповідником до російських мера, мероприятие є захід, а в множині — заходи';
const SLID_STORED_EVIDENCE =
  '9-klas-ukrajinska-mova-voron-2017_s0232: следующий — тут: наступний; Як правильно перекласти ... следующий? ... наступний';
// The round-3 counterexample: a normative locator and the headword, but no correction.
const GENERIC_PARAGRAPH =
  'antonenko-davydovych-yak-my-hovorymo_p031: Учні переписали слово міроприємство до зошита та прочитали наступне речення.';
const ESUM_TIUN = {
  source: 'esum',
  ref: 'тіун:5:580',
  word: 'тіун',
  detail: 'тіун (іст.) (назва ряду службових осіб на Русі ХІ-- ХМІЇ ст. управитель княжим або панським господарством, суддя нижчої категорії тощо); «(наглядач Кузі»',
};
const TIUN_GLOSS = 'У Київській Русі … — господарський управитель князя, бояр...';
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
      name: 'avoid-listed word with a reviewed judgment on the headword is RED (міроприємство)',
      entry: {
        lemma: 'міроприємство',
        primary_source: 'surzhyk_to_avoid',
        heritage_status: {
          classification: 'russianism',
          is_russianism: true,
          curated_calque: { kind: 'lexical', corrections: ['захід', 'заходи'], evidence: [MIRO_STORED_EVIDENCE] },
        },
      },
      proof: MIRO_PROOF,
      expected: { red: true, yellow: false, green: false, blue: false },
      alternatives: ['захід'],
    },
    {
      name: 'the same stored record without current proof is not RED',
      entry: {
        lemma: 'міроприємство',
        primary_source: 'surzhyk_to_avoid',
        heritage_status: {
          classification: 'russianism',
          is_russianism: true,
          curated_calque: { kind: 'lexical', corrections: ['захід'], evidence: [MIRO_STORED_EVIDENCE, GENERIC_PARAGRAPH] },
        },
      },
      proof: null,
      expected: { red: false, yellow: false, green: false, blue: false },
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
      name: 'lexical calque with a reviewed judgment on the headword is YELLOW',
      entry: {
        lemma: 'міроприємство',
        heritage_status: { classification: 'calque', calque_warning: { kind: 'lexical', standard_alternatives: ['заходи'] } },
      },
      proof: MIRO_PROOF,
      expected: { red: false, yellow: true, green: false, blue: false },
      alternatives: ['захід'],
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
  ])('$name', ({ entry, expected, alternatives, proof }) => {
    const boxes = resolveHeritageBoxes(entry as LexiconEntryForSeverity, (proof ?? null) as UsageSourceProof | null);

    expect(Boolean(boxes.red)).toBe(expected.red);
    expect(Boolean(boxes.yellow)).toBe(expected.yellow);
    expect(Boolean(boxes.green)).toBe(expected.green);
    expect(Boolean(boxes.blue)).toBe(expected.blue);
    if (!expected.red) expect(boxes.inline?.severity).not.toBe('red');

    if (alternatives) {
      expect((boxes.red ?? boxes.yellow)?.alternatives).toEqual(alternatives);
    }
  });

  test('actual stored міроприємство is RED through the projected judgment, quoting its passage', () => {
    // Stored DB shape: its own excerpt names only the etymon and the replacement.
    const boxes = resolveHeritageBoxes({
      lemma: 'міроприємство',
      primary_source: 'surzhyk_to_avoid',
      heritage_status: {
        classification: 'russianism',
        is_russianism: true,
        curated_calque: { kind: 'lexical', corrections: ['захід', 'заходи'], evidence: [MIRO_STORED_EVIDENCE] },
      },
    } as LexiconEntryForSeverity);
    expect(boxes.usageLabel).toMatchObject({ code: 'rus', scope: 'lemma' });
    expect(boxes.red?.body).toContain('antonenko-davydovych-yak-my-hovorymo_p031');
    expect(boxes.red?.body).toContain('11-klas-ukrajinska-mova-glazova-2019_s0263');
    expect(boxes.red?.body).toContain('Витяг: «"У нас провели такі міроприємства" і под. Такого слова не було й нема');
    expect(boxes.red?.body).toContain('перелік суржику');
    expect(boxes.red?.alternatives).toEqual(['захід']);
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
    } as LexiconEntryForSeverity, null);

    expect(boxes.yellow).toBeDefined();
    expect(boxes.yellow?.scope).toBe('sense');
    expect(boxes.yellow?.title).toBe('Калькове застереження щодо окремого значення');
    expect(boxes.yellow?.body).toContain('«столовий прибор»');
    expect(boxes.yellow?.body).toContain('а не слова загалом');
    expect(boxes.yellow?.body).toContain('Перевіреного витягу з нормативного джерела запис не містить.');
    expect(boxes.yellow?.alternatives).toEqual(['виделка']);
    expect(boxes.yellow?.body).toContain('У цьому вжитку Атлас пропонує (без звірки з джерелом): виделка.');
    // Stored Atlas prose is commentary, never a source excerpt.
    expect(boxes.yellow?.detail).toBe(
      'Примітка Атласу, не підтверджена витягом із джерела: Столовий прибор для їжі в українській мові називається винятково «виделка».',
    );
    expect(boxes.inline).toBeUndefined();
    expect(boxes.green).toBeUndefined();
  });

  test('actual stored являтися cites the projected s0159 correction, never the stored s0162', () => {
    const boxes = resolveHeritageBoxes({
      lemma: 'являтися',
      heritage_status: {
        classification: 'standard',
        warning_severity: 'calque_yellow',
        curated_calque: {
          kind: 'sense_restricted',
          corrections: ['бути', 'є'],
          calque_sense: "to be / constitute (рос. являться = 'to be')",
          evidence: ['9-klas-ukrajinska-mova-avramenko-2017_s0162: Неправильно: являтися переможцем; Правильно: бути переможцем'],
        },
      },
    } as LexiconEntryForSeverity);
    expect(boxes.usageLabel).toMatchObject({ scope: 'sense', authority: ['9-klas-ukrajinska-mova-avramenko-2017_s0159'] });
    expect(boxes.yellow?.body).toContain('У цьому вжитку джерело радить: бути. Джерело: 9-klas-ukrajinska-mova-avramenko-2017_s0159.');
    expect(boxes.yellow?.alternatives).toEqual(['бути']);
    expect(boxes.yellow?.body).not.toContain('s0162');
    expect(boxes.inline).toBeUndefined();
  });

  test('неділя keeps its duration caution; the stored «лише» prose is Atlas commentary', () => {
    const boxes = resolveHeritageBoxes({
      lemma: 'неділя',
      heritage_status: {
        classification: 'standard',
        curated_calque: {
          kind: 'sense_restricted',
          corrections: ['тиждень'],
          calque_sense: 'week / a seven-day period (рос. неделя)',
          noteUk: 'В українській мові слово "неділя" означає лише сьомий день тижня.',
        },
      },
    } as LexiconEntryForSeverity);
    expect(boxes.yellow?.body).toContain('«week / a seven-day period (рос. неделя)»');
    expect(boxes.yellow?.body).toContain('Джерело: 10-klas-ukrmova-glazova-2018_s0075.');
    expect(boxes.yellow?.detail).toMatch(/^Примітка Атласу, не підтверджена витягом із джерела: /u);
    expect(atlasNoteDetail('  ')).toBeUndefined();
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
    const stale = resolveHeritageBoxes({ lemma: 'другий', heritage_status: status }, null);
    expect(stale.red).toBeUndefined();
    expect(stale.yellow).toBeUndefined();
    expect(stale.inline).toBeUndefined();
    // Current proof (Антоненко-Давидович p107) keeps a sense caution, never a word badge.
    const boxes = resolveHeritageBoxes({ lemma: 'другий', heritage_status: status });
    expect(boxes.red).toBeUndefined();
    expect(boxes.yellow?.scope).toBe('sense');
    expect(boxes.yellow?.body).toContain('antonenko-davydovych-yak-my-hovorymo_p107');
    expect(boxes.yellow?.alternatives).toEqual(['інший']);
    expect(boxes.inline).toBeUndefined();
  });

  test('a lexical Russianism needs a reviewed judgment rejecting the headword (міроприємство)', () => {
    const status = {
      classification: 'russianism',
      is_russianism: true,
      curated_calque: { kind: 'lexical', corrections: ['захід'], evidence: [MIRO_STORED_EVIDENCE] },
    };
    const label = resolveUsageLabel(status, { headword: 'міроприємство', sourceProof: MIRO_PROOF });
    expect(label).toMatchObject({ code: 'rus', scope: 'lemma', authority: ['antonenko-davydovych-yak-my-hovorymo_p031'] });
    expect(label.evidence).toBe(MIRO_PASSAGE);
    const long = { ...MIRO_PROOF, judgments: [{ ...MIRO_PROOF.judgments[0], passage: 'слово '.repeat(60) }] };
    expect(resolveUsageLabel(status, { headword: 'міроприємство', sourceProof: long }).evidence?.endsWith('…')).toBe(true);
    // The replacement side, another headword or no headword binds nothing.
    expect(resolveUsageLabel(status, { headword: 'захід', sourceProof: MIRO_PROOF }).scope).toBe('unresolved');
    expect(resolveUsageLabel(status, { sourceProof: MIRO_PROOF }).scope).toBe('unresolved');
    // Without current proof the stored excerpt binds nothing.
    expect(resolveUsageLabel(status, { headword: 'міроприємство' }).reason).toBe('no_headword_bound_evidence');
    expect(resolveUsageLabel({ ...status, is_russianism: false, classification: 'calque' }, { headword: 'міроприємство', sourceProof: MIRO_PROOF }).code).toBe('calq');
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
      name: 'a generic paragraph naming the headword from a normative locator (round 3)',
      headword: 'міроприємство',
      record: { kind: 'lexical', corrections: ['захід'], evidence: [GENERIC_PARAGRAPH] },
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
    { name: 'nested explanation', headword: 'тіун', gloss: TIUN_GLOSS, attestations: [{ ...ESUM_TIUN, detail: 'тіун (іст.) (управитель (княжий) двору)' }], cards: null },
    { name: 'modern card with several senses', headword: 'гридь', gloss: HRYD_GLOSS, attestations: [ESUM_HRYD], cards: [{ id: 'sum20', definitions: ['ГРИДЬ, і, ж. 1. Нижча верства княжої дружини. 2. Приміщення.'] }] },
  ])('ЕСУМ marker does not bind: $name', ({ headword, gloss, attestations, cards }) => {
    const label = resolveUsageLabel({ classification: 'historism', attestations }, { headword, gloss, definitionCards: cards });
    expect(label.code).toBeNull();
    expect(label.scope).toBe('unresolved');
  });

  test('ЕСУМ marker followed by a parenthetical explanation binds (тіун)', () => {
    const status = { classification: 'historism', attestations: [ESUM_TIUN] };
    const label = resolveUsageLabel(status, { headword: 'тіун', gloss: TIUN_GLOSS });
    expect(label).toMatchObject({ code: 'hist', scope: 'lemma', authority: ['ЕСУМ, т. 5, с. 580'] });
    expect(label.evidence).toMatch(/^тіун \(іст\.\) \(назва ряду службових осіб на Русі/u);
    const boxes = resolveHeritageBoxes({ lemma: 'тіун', gloss: TIUN_GLOSS, heritage_status: status });
    expect(boxes.green?.title).toBe('Історизм');
    expect(boxes.green?.body).toContain('ЕСУМ, т. 5, с. 580');
  });

  test('an unlabelled modern card keeps a historism but decides current register (гридь, платівка)', () => {
    const vts = [{ id: 'vts', definitions: ['гридь -і, ж., збірн. Нижча верства княжої дружини.'] }];
    expect(resolveUsageLabel({ classification: 'historism', attestations: [ESUM_HRYD] }, { headword: 'гридь', gloss: HRYD_GLOSS, definitionCards: vts }).code).toBe('hist');
    const status = {
      classification: 'authentic-archaism',
      attestations: [{ source: 'esum', ref: 'платівка:4:431', word: 'платівка', detail: 'платівка (заст.) «пластинка»; утворено від' }],
    };
    const definitionCards = [{ id: 'sum20', definitions: ['ПЛАТІ́ВКА, и, ж. Те саме, що пласти́нка 1–3. Патефонна платівка.'] }];
    const label = resolveUsageLabel(status, { headword: 'платівка', gloss: 'Те саме, що пласти́нка 1-3.', definitionCards });
    expect(label).toEqual({
      code: null,
      scope: 'unresolved',
      authority: ['ЕСУМ, т. 4, с. 431'],
      evidence: 'платівка (заст.) «пластинка»',
      reason: 'source_marker_not_whole_word',
    });
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
    const boxes = resolveHeritageBoxes(
      {
        lemma: 'міроприємство',
        heritage_status: { classification: 'russianism', is_russianism: true, curated_calque: { kind: 'lexical' } },
      } as LexiconEntryForSeverity,
      { ...MIRO_PROOF, corrections: [] },
    );
    expect(boxes.red?.body).toContain('antonenko-davydovych-yak-my-hovorymo_p031');
    expect(boxes.red?.body).not.toContain('перелік суржику');
    expect(boxes.red?.body).toContain('Перевіряйте рекомендовані відповідники');
  });

  test('a lemma-bound calque offers the source-recommended forms, never «neutral» ones', () => {
    const entry = {
      lemma: 'міроприємство',
      heritage_status: { classification: 'calque', is_russianism: false, curated_calque: { kind: 'lexical' } },
    } as LexiconEntryForSeverity;
    const boxes = resolveHeritageBoxes(entry, MIRO_PROOF);
    expect(boxes.yellow?.scope).toBe('lemma');
    expect(boxes.yellow?.body).toBe('Рекомендовані відповідники: захід. Джерело: antonenko-davydovych-yak-my-hovorymo_p031.');
    expect(resolveHeritageBoxes(entry, { ...MIRO_PROOF, corrections: [] }).yellow?.body).toContain('Перевіряйте відповідники в джерелах.');
  });

  test('a contextual caution without alternatives names no adviser', () => {
    const boxes = resolveHeritageBoxes({
      lemma: 'вилка',
      heritage_status: { classification: 'standard', calque_warning: { kind: 'sense_restricted', calque_sense: 'столовий прибор' } },
    } as LexiconEntryForSeverity, null);
    expect(boxes.yellow?.body).toBe(
      'Застереження стосується окремого значення («столовий прибор»), а не слова загалом. Перевіреного витягу з нормативного джерела запис не містить.',
    );
  });

  test('a phrasal caution is titled for the collocation and lists record references', () => {
    const boxes = resolveHeritageBoxes({
      lemma: 'приймати',
      heritage_status: {
        classification: 'standard',
        calque_warning: { kind: 'phrasal', citations: ['antonenko-p091'], standard_alternatives: ['брати участь'] },
      },
    } as LexiconEntryForSeverity, null);
    expect(boxes.yellow?.title).toBe('Калькове застереження щодо сполучення');
    expect(boxes.yellow?.body).toContain('Посилання запису Атласу, не звірені з джерелом: antonenko-p091.');
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

  test('usageSourceProof reads the committed projection by headword', () => {
    const miro = usageSourceProof('міроприємство');
    expect(miro?.kind).toBe('lexical');
    expect(miro?.judgments.map((item) => [item.locator, item.rejectedForm, item.endorsedForm])).toContainEqual([
      'antonenko-davydovych-yak-my-hovorymo_p031',
      'міроприємство',
      'захід',
    ]);
    expect(usageSourceProof('Являтися')?.citations.map((item) => item.locator)).toEqual(['9-klas-ukrajinska-mova-avramenko-2017_s0159']);
    // Recommended replacements and words that are only another record's surface get no proof.
    for (const headword of ['бути', 'є', 'захід', 'наступний', 'голова', undefined]) {
      expect(usageSourceProof(headword)).toBeNull();
    }
  });

  test('sharesReferent compares content words only', () => {
    expect(sharesReferent('нижча верхівка княжої дружини', HRYD_GLOSS)).toBe(true);
    expect(sharesReferent('нижча верхівка княжої дружини', 'sofa')).toBe(false);
    expect(sharesReferent('у на до', 'у на до')).toBe(false);
    expect(sharesReferent('дружини', null)).toBe(false);
  });
});

// #9603 b0 blocker 2: editorial gloss metadata must not bypass the resolved scope.
describe('displayGloss', () => {
  const label = (scope: UsageLabel['scope'], code: UsageLabel['code'] = null): UsageLabel => ({
    code,
    scope,
    authority: [],
    evidence: null,
    reason: scope,
  });
  const NOTE = 'примітка Атласу: радять «наступний»; обсяг застереження не встановлено';

  test('keeps a lemma-bound Russianism or calque gloss verbatim (міроприємство)', () => {
    expect(displayGloss('avoid: захід', label('lemma', 'rus'))).toEqual({ text: 'avoid: захід', note: false });
    expect(displayGloss('avoid: захід', label('lemma', 'calq'))).toEqual({ text: 'avoid: захід', note: false });
  });

  test.each(['unresolved', 'none', 'sense', 'phrase', 'reverse'] as const)('qualifies avoid: metadata under %s scope', (scope) => {
    expect(displayGloss('avoid: наступний', label(scope))).toEqual({ text: NOTE, note: true });
  });

  test('a lemma register label is no licence for a word-wide avoid instruction', () => {
    expect(displayGloss('avoid: наступний', label('lemma', 'hist'))).toEqual({ text: NOTE, note: true });
  });

  test('qualifies rus:/calque: metadata and preserves the stored suggestion', () => {
    expect(displayGloss(' RUS:  інший ', label('unresolved'))?.text).toBe(
      'примітка Атласу: русизм — «інший»; обсяг застереження не встановлено',
    );
    expect(displayGloss('calque: брати участь', label('none'))?.text).toBe(
      'примітка Атласу: калька — «брати участь»; обсяг застереження не встановлено',
    );
  });

  const SWITCH = 'to switch over (Russian calque; standard Ukrainian: перемкнути)';
  const SWITCH_NOTE =
    'to switch over (примітка Атласу: «Russian calque; standard Ukrainian: перемкнути»; обсяг застереження не встановлено)';

  test.each(['unresolved', 'none', 'sense', 'phrase', 'reverse'] as const)('qualifies an embedded norm clause under %s scope', (scope) => {
    expect(displayGloss(SWITCH, label(scope))).toEqual({ text: SWITCH_NOTE, note: true });
    expect(displayGloss('enlightener (a Russianism) or (surzhyk)', label(scope))?.text).toBe(
      'enlightener (примітка Атласу: «a Russianism»; обсяг застереження не встановлено) or (примітка Атласу: «surzhyk»; обсяг застереження не встановлено)',
    );
  });

  test('keeps an embedded norm clause verbatim only for a lemma-bound Russianism or calque', () => {
    expect(displayGloss(SWITCH, label('lemma', 'calq'))).toEqual({ text: SWITCH, note: false });
    expect(displayGloss(SWITCH, label('lemma', 'hist'))).toEqual({ text: SWITCH_NOTE, note: true });
  });

  test('ordinary parentheticals naming Russia or avoidance are meaning, not norm claims', () => {
    for (const gloss of [
      'Moscow (a federal city, the capital of Russia)',
      'RF (Russian Federation) (proper noun)',
      'to save, to economize (store unspent; avoid the expenditure of)',
      'calque',
    ]) {
      expect(displayGloss(gloss, label('unresolved'))).toEqual({ text: gloss, note: false });
    }
  });

  test('ordinary, prefixed-elsewhere and empty glosses are unchanged', () => {
    expect(displayGloss('next', label('unresolved'))).toEqual({ text: 'next', note: false });
    expect(displayGloss('to avoid: dodge', label('none'))).toEqual({ text: 'to avoid: dodge', note: false });
    expect(displayGloss('avoid:', label('none'))).toEqual({ text: 'avoid:', note: false });
    expect(displayGloss('', label('none'))).toBeNull();
    expect(displayGloss(null, label('none'))).toBeNull();
  });
});

// #9603: the route <meta name="description"> reads the same scoped gloss projection as the article.
describe('lexicon route description', () => {
  const route = (extra: Record<string, unknown>, heritage_status: Record<string, unknown> = {}) =>
    articleProps({ lemma: 'переключити', url_slug: 'переключити', gloss: 'gloss', entry_type: 'lemma', pos: 'verb',
      ipa: null, primary_source: 'course', course_usage: [], heritage_status, ...extra } as never);

  async function description(props: ReturnType<typeof route>): Promise<string | undefined> {
    const { experimental_AstroContainer: AstroContainer } = await import('astro/container');
    const { default: reactRenderer } = await import('@astrojs/react/server.js');
    const { default: Page } = (await import('@site/src/pages/lexicon/[lemma].astro')) as never;
    const container = await AstroContainer.create();
    container.addServerRenderer({ renderer: reactRenderer });
    const html = await container.renderToString(Page, { props: { ...props, generatedAt: 'test', manifestVersion: '0.1' } });
    return html.match(/<meta name="description" content="([^"]*)"/)?.[1];
  }

  test('lemma route qualifies unscoped editorial glosses and keeps bound or ordinary ones', async () => {
    expect(await description(route({ gloss: 'to switch over (Russian calque; standard Ukrainian: перемкнути)' }, { classification: 'russianism', is_russianism: true }))).toBe(
      'переключити — to switch over (примітка Атласу: «Russian calque; standard Ukrainian: перемкнути»; обсяг застереження не встановлено)',
    );
    expect(await description(route({ lemma: 'слідуючий', url_slug: 'слідуючий', gloss: 'avoid: наступний', primary_source: 'surzhyk_to_avoid' }, { classification: 'russianism', is_russianism: true }))).toBe(
      'слідуючий — примітка Атласу: радять «наступний»; обсяг застереження не встановлено',
    );
    expect(
      await description(
        route(
          { lemma: 'міроприємство', url_slug: 'міроприємство', gloss: 'avoid: захід', primary_source: 'surzhyk_to_avoid' },
          { classification: 'russianism', is_russianism: true, curated_calque: { kind: 'lexical', corrections: ['захід'] } },
        ),
      ),
    ).toBe('міроприємство — avoid: захід');
    expect(await description(route({ gloss: 'to switch over' }))).toBe('переключити — to switch over');
  }, 60_000);

  test('form route keeps its form-of description', async () => {
    const props = route({ lemma: 'переключив', url_slug: 'переключив', gloss: 'avoid: x', form_of: { url_slug: 'переключити', lemma: 'переключити' } });
    expect(await description(props)).toBe('переключив — форма слова «переключити»');
  }, 60_000);
});
