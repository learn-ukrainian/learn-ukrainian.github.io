import { describe, expect, test } from 'vitest';
import { resolveHeritageBoxes, type LexiconEntryForSeverity } from '@site/src/lib/lexicon/heritage-severity';

describe('resolveHeritageBoxes', () => {
  test.each([
    {
      name: 'авось resolves to RED and parses avoid gloss alternatives',
      entry: {
        gloss: 'avoid: ану ж / а може',
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
      name: 'calque with a standard alternative resolves to YELLOW',
      entry: {
        gloss: 'acting',
        heritage_status: {
          classification: 'unknown',
          warning_severity: 'calque_yellow',
          calque_warning: {
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
      name: 'dialect classification resolves to GREEN',
      entry: {
        heritage_status: {
          classification: 'dialect',
          is_russianism: false,
          russian_shadow: true,
          vesum_attested: false,
          attestations: [],
        },
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
});
