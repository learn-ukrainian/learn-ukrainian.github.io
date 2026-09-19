import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import {
  type PracticePronounMechanicsCard,
  PRONOUN_MECHANICS_CATEGORY_KEYS,
  PRONOUN_MECHANICS_INTERFERENCE_KEYS,
  pronounMechanicsFeedbackFor,
  resolveDeclensionVesRule,
  resolveDemonstrativeRule,
  resolveEpenthesisRule,
  resolveInterrogativeRule,
  resolveOrthographyRule,
  resolvePossessiveYikhniyRule,
  resolveReflexiveSebeRule,
  resolveSamVsSamyiRule,
} from '../../src/lib/lexicon/pronoun-mechanics';

describe('pronoun-mechanics', () => {
  it('defines all 15 pronoun categories and 17 interference keys', () => {
    expect(PRONOUN_MECHANICS_CATEGORY_KEYS).toHaveLength(15);
    expect(PRONOUN_MECHANICS_INTERFERENCE_KEYS).toHaveLength(17);

    expect(PRONOUN_MECHANICS_CATEGORY_KEYS).toContain('epenthetic_n_prepositional');
    expect(PRONOUN_MECHANICS_CATEGORY_KEYS).toContain('epenthetic_n_absence_direct');
    expect(PRONOUN_MECHANICS_CATEGORY_KEYS).toContain('epenthetic_n_instrumental_omnipresent');
    expect(PRONOUN_MECHANICS_CATEGORY_KEYS).toContain('epenthetic_n_derivative_prepositions');
    expect(PRONOUN_MECHANICS_CATEGORY_KEYS).toContain('orthography_indefinite_together');
    expect(PRONOUN_MECHANICS_CATEGORY_KEYS).toContain('orthography_indefinite_hyphen');
    expect(PRONOUN_MECHANICS_CATEGORY_KEYS).toContain('orthography_indefinite_split_preposition');
    expect(PRONOUN_MECHANICS_CATEGORY_KEYS).toContain('orthography_negative_together');
    expect(PRONOUN_MECHANICS_CATEGORY_KEYS).toContain('orthography_negative_split_preposition');
    expect(PRONOUN_MECHANICS_CATEGORY_KEYS).toContain('reflexive_sebe_paradigm');
    expect(PRONOUN_MECHANICS_CATEGORY_KEYS).toContain('declension_ves_alternation');
    expect(PRONOUN_MECHANICS_CATEGORY_KEYS).toContain('declension_tsyey_toy');
    expect(PRONOUN_MECHANICS_CATEGORY_KEYS).toContain('interrogative_chyi_khto_shcho');
    expect(PRONOUN_MECHANICS_CATEGORY_KEYS).toContain('semantic_sam_vs_samyi');
    expect(PRONOUN_MECHANICS_CATEGORY_KEYS).toContain('possessive_yikhniy_vs_yikh');

    expect(PRONOUN_MECHANICS_INTERFERENCE_KEYS).toContain('spurious_epenthetic_n');
    expect(PRONOUN_MECHANICS_INTERFERENCE_KEYS).toContain('missing_epenthetic_n');
    expect(PRONOUN_MECHANICS_INTERFERENCE_KEYS).toContain('corrupted_instrumental_form');
    expect(PRONOUN_MECHANICS_INTERFERENCE_KEYS).toContain('external_preposition_russian_calque');
    expect(PRONOUN_MECHANICS_INTERFERENCE_KEYS).toContain('confusion_sam_vs_samyi');
  });

  it('resolves epenthetic n- rules accurately per § 116', () => {
    const prep = resolveEpenthesisRule('epenthetic_n_prepositional');
    expect(prep.citation).toContain('§ 116');
    expect(prep.ruleUa).toContain('до нього');
    expect(prep.ruleEn).toContain('oblique cases');

    const dir = resolveEpenthesisRule('epenthetic_n_absence_direct');
    expect(dir.ruleUa).toContain('бачу його');
    expect(dir.ruleEn).toContain('direct case government');

    const ins = resolveEpenthesisRule('epenthetic_n_instrumental_omnipresent');
    expect(ins.ruleUa).toContain('ним, нею, ними');
    expect(ins.ruleEn).toContain('Instrumental');

    const der = resolveEpenthesisRule('epenthetic_n_derivative_prepositions');
    expect(der.ruleUa).toContain('завдяки йому');
    expect(der.ruleEn).toContain('derivative prepositions');

    expect(() => resolveEpenthesisRule('orthography_indefinite_together' as any)).toThrow(
      /not an epenthesis category/,
    );
  });

  it('resolves orthography rules accurately per § 42', () => {
    const tog = resolveOrthographyRule('orthography_indefinite_together');
    expect(tog.citation).toContain('§ 42');
    expect(tog.ruleUa).toContain('дехто, абихто');
    expect(tog.ruleEn).toContain('single word');

    const hyph = resolveOrthographyRule('orthography_indefinite_hyphen');
    expect(hyph.ruleUa).toContain('будь-хто');
    expect(hyph.ruleEn).toContain('hyphen');

    const splitIndef = resolveOrthographyRule('orthography_indefinite_split_preposition');
    expect(splitIndef.ruleUa).toContain('будь у кого');
    expect(splitIndef.ruleEn).toContain('three words');

    const negTog = resolveOrthographyRule('orthography_negative_together');
    expect(negTog.ruleUa).toContain('ніхто, ніщо');
    expect(negTog.ruleEn).toContain('prefix ні-');

    const splitNeg = resolveOrthographyRule('orthography_negative_split_preposition');
    expect(splitNeg.ruleUa).toContain('ні про що');
    expect(splitNeg.ruleEn).toContain('split');

    expect(() => resolveOrthographyRule('reflexive_sebe_paradigm' as any)).toThrow(
      /not an orthography category/,
    );
  });

  it('resolves paradigm and stylistic rules accurately', () => {
    const refl = resolveReflexiveSebeRule();
    expect(refl.citation).toContain('§ 117');
    expect(refl.ruleUa).toContain('собі');
    expect(refl.ruleEn).toContain('Reflexive');

    const ves = resolveDeclensionVesRule();
    expect(ves.citation).toContain('§ 119');
    expect(ves.ruleUa).toContain('всіма');
    expect(ves.ruleEn).toContain('-іма');

    const dem = resolveDemonstrativeRule();
    expect(dem.citation).toContain('§ 119');
    expect(dem.ruleUa).toContain('цими, тими');

    const int = resolveInterrogativeRule();
    expect(int.citation).toContain('§§ 120–121');
    expect(int.ruleUa).toContain('хто, що, чий');

    const sam = resolveSamVsSamyiRule();
    expect(sam.ruleUa).toContain('той самий');
    expect(sam.ruleEn).toContain('identity');

    const poss = resolvePossessiveYikhniyRule();
    expect(poss.citation).toContain('§ 118');
    expect(poss.ruleUa).toContain('до них');
  });

  it('evaluates feedback correctly for correct, distractor, and fallback choices', () => {
    const card: PracticePronounMechanicsCard = {
      card_id: 'test_pron_card',
      category: 'epenthetic_n_prepositional',
      cefr_level: 'A2',
      sentence_before: 'Я зайшов',
      sentence_after: 'у гості.',
      prompt_display: 'Я зайшов _______ у гості.',
      full_sentence: 'Я зайшов до нього у гості.',
      correct_answer: 'до нього',
      options: ['до нього', 'до його', 'до йому', 'до нему'],
      distractors: [
        {
          text: 'до його',
          interference_type: 'missing_epenthetic_n',
          explanation: {
            ua: 'Після прийменника обов’язковий приставний н-: до нього.',
            en: 'After preposition, epenthetic n- is compulsory: до нього.',
          },
        },
        {
          text: 'до йому',
          interference_type: 'corrupted_declension_stem',
          explanation: {
            ua: 'Потрібен родовий відмінок: до нього.',
            en: 'Genitive case is required: до нього.',
          },
        },
        {
          text: 'до нему',
          interference_type: 'corrupted_declension_stem',
          explanation: {
            ua: 'Ненормативна форма: до нього.',
            en: 'Non-standard form: до нього.',
          },
        },
      ],
      rule_citation: 'Правопис 2019 § 116',
      rule_summary: {
        ua: 'Обов’язковий приставний н- після прийменників.',
        en: 'Compulsory epenthetic n- after prepositions.',
      },
    };

    // Correct
    const correctResUa = pronounMechanicsFeedbackFor(card, 'до нього', 'ua');
    expect(correctResUa.isCorrect).toBe(true);
    expect(correctResUa.feedback).toContain('Правильно!');

    const correctResEn = pronounMechanicsFeedbackFor(card, 'до нього', 'en');
    expect(correctResEn.isCorrect).toBe(true);
    expect(correctResEn.feedback).toContain('Correct!');

    // Known distractor
    const distResUa = pronounMechanicsFeedbackFor(card, 'до його', 'ua');
    expect(distResUa.isCorrect).toBe(false);
    expect(distResUa.feedback).toContain('приставний н-');

    const distResEn = pronounMechanicsFeedbackFor(card, 'до його', 'en');
    expect(distResEn.isCorrect).toBe(false);
    expect(distResEn.feedback).toContain('epenthetic n-');

    // Fallback unrecognized option
    const fallbackResUa = pronounMechanicsFeedbackFor(card, 'щось інше', 'ua');
    expect(fallbackResUa.isCorrect).toBe(false);
    expect(fallbackResUa.feedback).toContain('Неправильно. Правильна форма: «до нього»');

    const fallbackResEn = pronounMechanicsFeedbackFor(card, 'something else', 'en');
    expect(fallbackResEn.isCorrect).toBe(false);
    expect(fallbackResEn.feedback).toContain('Incorrect. The correct form is "до нього"');
  });

  it('validates canonical pronoun mechanics deck file', () => {
    const deckPath = resolve(__dirname, '../../../data/practice/pronoun_mechanics_deck.json');
    expect(existsSync(deckPath)).toBe(true);

    const raw = readFileSync(deckPath, 'utf-8');
    const deck = JSON.parse(raw);

    expect(deck.version).toBe('1.0');
    expect(deck.title).toContain('Займенник');
    expect(deck.total_cards).toBe(75);
    expect(deck.cards).toHaveLength(75);

    const categoryCounts: Record<string, number> = {};
    for (const c of deck.cards) {
      categoryCounts[c.category] = (categoryCounts[c.category] ?? 0) + 1;

      expect(c.options).toHaveLength(4);
      expect(new Set(c.options).size).toBe(4);
      expect(c.options).toContain(c.correctAnswer);
      expect(c.prompt).toContain('_______');
      expect(c.distractors).toHaveLength(3);

      for (const d of c.distractors) {
        expect(d.form).not.toBe(c.correctAnswer);
        expect(c.options).toContain(d.form);
        expect(d.explanationUa.length).toBeGreaterThan(10);
        expect(d.explanationEn.length).toBeGreaterThan(10);
      }
    }

    expect(Object.keys(categoryCounts)).toHaveLength(15);
    for (const [cat, count] of Object.entries(categoryCounts)) {
      expect(count).toBe(5);
    }
  });
});
