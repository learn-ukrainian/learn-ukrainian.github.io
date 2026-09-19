import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import {
  type PracticeVerbMechanicsCard,
  resolveConjugationClassRule,
  resolveDentalMutationRule,
  resolveEpenthesisRule,
  resolveGerundAspectRule,
  resolveImperativeRule,
  resolveImpersonalFormRule,
  resolveParticipleAntiCalqueRule,
  VERB_MECHANICS_CATEGORY_KEYS,
  VERB_MECHANICS_INTERFERENCE_KEYS,
  verbMechanicsFeedbackFor,
} from '../../src/lib/lexicon/verb-mechanics';

describe('verb-mechanics', () => {
  it('defines all 15 verb categories and 17 interference keys', () => {
    expect(VERB_MECHANICS_CATEGORY_KEYS).toHaveLength(15);
    expect(VERB_MECHANICS_INTERFERENCE_KEYS).toHaveLength(17);
    expect(VERB_MECHANICS_CATEGORY_KEYS).toContain('conj_class_i_vowel_e_ye');
    expect(VERB_MECHANICS_CATEGORY_KEYS).toContain('conj_class_ii_vowel_y_yi');
    expect(VERB_MECHANICS_CATEGORY_KEYS).toContain('conj_labial_epenthesis_l');
    expect(VERB_MECHANICS_CATEGORY_KEYS).toContain('conj_dental_mutation_1sg');
    expect(VERB_MECHANICS_CATEGORY_KEYS).toContain('conj_stem_mutation_class_i');
    expect(VERB_MECHANICS_CATEGORY_KEYS).toContain('aspect_prefixation');
    expect(VERB_MECHANICS_CATEGORY_KEYS).toContain('aspect_suffixation_ablaut');
    expect(VERB_MECHANICS_CATEGORY_KEYS).toContain('aspect_suppletive');
    expect(VERB_MECHANICS_CATEGORY_KEYS).toContain('imperative_synthetic_endings');
    expect(VERB_MECHANICS_CATEGORY_KEYS).toContain('imperative_inclusive_1pl');
    expect(VERB_MECHANICS_CATEGORY_KEYS).toContain('imperative_anti_calque_davai');
    expect(VERB_MECHANICS_CATEGORY_KEYS).toContain('participle_passive_formation');
    expect(VERB_MECHANICS_CATEGORY_KEYS).toContain('participle_anti_calque_active');
    expect(VERB_MECHANICS_CATEGORY_KEYS).toContain('participle_impersonal_no_to');
    expect(VERB_MECHANICS_CATEGORY_KEYS).toContain('gerund_formation_aspect');
    expect(VERB_MECHANICS_INTERFERENCE_KEYS).toContain('false_imperative_indicative_confusion');
  });

  it('resolves conjugation class rules accurately per § 115', () => {
    const classI = resolveConjugationClassRule('conj_class_i_vowel_e_ye');
    expect(classI.indicator).toContain('-е- / -є-');
    expect(classI.ruleUa).toContain('-уть/-ють');
    expect(classI.ruleEn).toContain('-ut/-yut');

    const classII = resolveConjugationClassRule('conj_class_ii_vowel_y_yi');
    expect(classII.indicator).toContain('-и- / -ї-');
    expect(classII.ruleUa).toContain('-ать/-ять');
    expect(classII.ruleEn).toContain('-at/-iat');
  });

  it('resolves epenthesis rules accurately per § 115', () => {
    const ep = resolveEpenthesisRule();
    expect(ep.indicator).toBe("[л']");
    expect(ep.ruleUa).toContain('після губних');
    expect(ep.ruleEn).toContain('Epenthetic');
  });

  it('resolves dental/alveolar consonant alternation rules for 1sg per § 115', () => {
    const cases = [
      { key: 'd_dzh', expectedMut: 'д -> дж', expectedEx: 'ходжу' },
      { key: 't_ch', expectedMut: 'т -> ч', expectedEx: 'лечу' },
      { key: 's_sh', expectedMut: 'с -> ш', expectedEx: 'прошу' },
      { key: 'z_zh', expectedMut: 'з -> ж', expectedEx: 'вожу' },
      { key: 'st_shch', expectedMut: 'ст -> щ', expectedEx: 'мощу' },
      { key: 'zd_zhdzh', expectedMut: 'зд -> ждж', expectedEx: 'їжджу' },
    ];
    for (const c of cases) {
      const res = resolveDentalMutationRule(c.key);
      expect(res.mutation).toBe(c.expectedMut);
      expect(res.ruleUa).toContain(c.expectedEx);
    }
  });

  it('resolves imperative mood rules accurately per § 116', () => {
    const str = resolveImperativeRule('stressed_or_cluster');
    expect(str.indicator).toBe('-и / -іть');
    expect(str.ruleUa).toContain('наголосом');

    const vow = resolveImperativeRule('vowel_or_soft');
    expect(vow.indicator).toContain('нульове');
    expect(vow.ruleUa).toContain('читай');

    const inc = resolveImperativeRule('inclusive_1pl');
    expect(inc.indicator).toBe('-мо / -імо');
    expect(inc.ruleUa).toContain('заклик до спільної дії');
  });

  it('resolves participle and gerund rules accurately per §§ 119–120', () => {
    const partAnti = resolveParticipleAntiCalqueRule();
    expect(partAnti.indicator).toContain('активних');
    expect(partAnti.ruleUa).toContain('охочий, чинний');

    const imp = resolveImpersonalFormRule();
    expect(imp.indicator).toBe('-но / -то');
    expect(imp.ruleUa).toContain('безособових');

    const gerundImp = resolveGerundAspectRule('imperfective');
    expect(gerundImp.indicator).toContain('-учи/-ючи');
    expect(gerundImp.ruleUa).toContain('одночасної дії');

    const gerundPerf = resolveGerundAspectRule('perfective');
    expect(gerundPerf.indicator).toContain('-вши / -ши');
    expect(gerundPerf.ruleUa).toContain('передуючої');
  });

  it('throws error for unsupported conjugation category or unknown dental mutation', () => {
    // @ts-expect-error test invalid category
    expect(() => resolveConjugationClassRule('invalid_cat')).toThrow(/not a primary conjugation/);
    expect(() => resolveDentalMutationRule('unknown_key')).toThrow(/Unknown dental mutation key/);
    expect(() => resolveDentalMutationRule('constructor')).toThrow(/Unknown dental mutation key/);
    expect(() => resolveDentalMutationRule('toString')).toThrow(/Unknown dental mutation key/);
    expect(() => resolveDentalMutationRule('__proto__')).toThrow(/Unknown dental mutation key/);
  });

  it('produces targeted feedback for learner responses', () => {
    const mockCard: PracticeVerbMechanicsCard = {
      card_id: 'test_card_1',
      category: 'conj_class_i_vowel_e_ye',
      cefr_level: 'A2',
      prompt_sentence: 'Вони мужньо ___ за свободу.',
      blank_target: 'борються',
      correct_answer: 'борються',
      options: ['боряться', 'борються', 'боряються', 'борять'],
      distractors: [
        {
          text: 'боряться',
          interference_type: 'false_conjugation_class_i_for_ii',
          explanation: {
            ua: 'Помилка дієвідміни: дієслова I дієвідміни мають закінчення -уть/-ють.',
            en: 'Conjugation class error: Class I verbs take -ut/-yut in 3pl.',
          },
        },
      ],
      pravopys_section: 'Правопис 2019 § 116',
      rule_summary: {
        ua: 'Дієслово боротися належить до I дієвідміни: борються.',
        en: 'The verb borotysia belongs to Class I: boriutsia.',
      },
    };

    // Correct response (UA)
    const resCorrectUa = verbMechanicsFeedbackFor(mockCard, 'борються', 'ua');
    expect(resCorrectUa.isCorrect).toBe(true);
    expect(resCorrectUa.feedback).toContain('Правильно!');
    expect(resCorrectUa.feedback).toContain('борються');

    // Correct response (EN)
    const resCorrectEn = verbMechanicsFeedbackFor(mockCard, 'борються', 'en');
    expect(resCorrectEn.isCorrect).toBe(true);
    expect(resCorrectEn.feedback).toContain('Correct!');

    // Distractor match (UA)
    const resDistUa = verbMechanicsFeedbackFor(mockCard, 'боряться', 'ua');
    expect(resDistUa.isCorrect).toBe(false);
    expect(resDistUa.feedback).toContain('Помилка дієвідміни');

    // Distractor match (EN)
    const resDistEn = verbMechanicsFeedbackFor(mockCard, 'боряться', 'en');
    expect(resDistEn.isCorrect).toBe(false);
    expect(resDistEn.feedback).toContain('Conjugation class error');

    // Fallback unknown distractor
    const resFallback = verbMechanicsFeedbackFor(mockCard, 'невідомо', 'ua');
    expect(resFallback.isCorrect).toBe(false);
    expect(resFallback.feedback).toContain('Неправильно. Правильна форма: «борються»');
  });

  it('validates the pre-compiled practice deck file', () => {
    const deckPath = resolve(__dirname, '../../../data/practice/verb_mechanics_deck.json');
    expect(existsSync(deckPath)).toBe(true);

    const raw = readFileSync(deckPath, 'utf-8');
    const payload = JSON.parse(raw);

    expect(payload.schema_version).toBe('1.0');
    expect(payload.card_count).toBeGreaterThanOrEqual(75);
    expect(payload.cards).toHaveLength(payload.card_count);

    const categoriesInDeck = new Set<string>();
    for (const card of payload.cards) {
      categoriesInDeck.add(card.category);
      expect(card.prompt_sentence).toContain('___');
      expect(card.options).toHaveLength(4);
      expect(card.options).toContain(card.correct_answer);
      expect(card.distractors).toHaveLength(3);
      expect(new Set(card.options).size).toBe(4);
    }
    expect(categoriesInDeck.size).toBe(15);
  });

  it('provides specific non-ablaut feedback for suffixation and aspectual distractors', () => {
    const deckPath = resolve(__dirname, '../../../data/practice/verb_mechanics_deck.json');
    const payload = JSON.parse(readFileSync(deckPath, 'utf-8'));

    const chytatyCard = payload.cards.find(
      (c: any) => c.card_id === 'verb_aspect_pref_chytaty_perf',
    );
    expect(chytatyCard).toBeDefined();
    const fbProchytavavUa = verbMechanicsFeedbackFor(chytatyCard, 'прочитавав', 'ua');
    const fbProchytavavEn = verbMechanicsFeedbackFor(chytatyCard, 'прочитавав', 'en');
    expect(fbProchytavavUa.isCorrect).toBe(false);
    expect(fbProchytavavUa.feedback).toContain('нарощенням суфікса');
    expect(fbProchytavavEn.feedback).toContain('spurious suffix lengthening');
    expect(fbProchytavavEn.feedback).not.toContain('Missing root vowel ablaut');

    const buduvatyCard = payload.cards.find(
      (c: any) => c.card_id === 'verb_aspect_pref_buduvaty_perf',
    );
    expect(buduvatyCard).toBeDefined();
    const fbZbudovuvalyUa = verbMechanicsFeedbackFor(buduvatyCard, 'збудовували', 'ua');
    const fbZbudovuvalyEn = verbMechanicsFeedbackFor(buduvatyCard, 'збудовували', 'en');
    expect(fbZbudovuvalyUa.isCorrect).toBe(false);
    expect(fbZbudovuvalyUa.feedback).toContain('недоконаного виду');
    expect(fbZbudovuvalyEn.feedback).toContain('imperfective form');
    expect(fbZbudovuvalyEn.feedback).not.toContain('Missing root vowel ablaut');
  });
});
