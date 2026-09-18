import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import {
  ADJECTIVE_MECHANICS_CATEGORY_KEYS,
  ADJECTIVE_MECHANICS_INTERFERENCE_KEYS,
  adjectiveMechanicsFeedbackFor,
  type PracticeAdjectiveMechanicsCard,
  resolveDegreeComparisonRule,
  resolveDerivationalSuffixMutationRule,
  resolvePossessiveSuffixRule,
  resolveSoftDeclensionInstrumentalRule,
} from '../../src/lib/lexicon/adjective-mechanics';

describe('adjective-mechanics', () => {
  it('resolves degrees of comparison rules accurately per §§ 110, 111', () => {
    // -zhch- mutation
    const zhch = resolveDegreeComparisonRule('comp_synthetic_mutation_zhch');
    expect(zhch.indicator).toBe('-жч-');
    expect(zhch.ruleUa).toContain('-жч-');
    expect(zhch.ruleEn).toContain('-zhch-');

    // -shch- mutation
    const shch = resolveDegreeComparisonRule('comp_synthetic_mutation_shch');
    expect(shch.indicator).toBe('-щ-');
    expect(shch.ruleUa).toContain('-щ-');
    expect(shch.ruleEn).toContain('-shch-');

    // -ish- suffix
    const ish = resolveDegreeComparisonRule('comp_synthetic_ish');
    expect(ish.indicator).toBe('-іш-');
    expect(ish.ruleUa).toContain('-іш-');
    expect(ish.ruleEn).toContain('-ish-');

    // Suppletive
    const sup = resolveDegreeComparisonRule('comp_suppletive');
    expect(sup.indicator).toContain('Суплетивна');
    expect(sup.ruleUa).toContain('інших основ');

    // Analytic
    const an = resolveDegreeComparisonRule('comp_analytic_formation');
    expect(an.indicator).toContain('більш / менш');
    expect(an.ruleUa).toContain('початковою формою');

    // Superlative synthetic
    const supSyn = resolveDegreeComparisonRule('super_synthetic_prefix');
    expect(supSyn.indicator).toContain('най-');
    expect(supSyn.ruleUa).toContain('най-');

    // Superlative emphatic
    const emph = resolveDegreeComparisonRule('super_emphatic_prefix');
    expect(emph.indicator).toContain('якнай-');
    expect(emph.ruleUa).toContain('разом');
  });

  it('resolves soft group Instrumental singular ending accurately per § 108', () => {
    const inst = resolveSoftDeclensionInstrumentalRule();
    expect(inst.ending).toBe('-ім');
    expect(inst.ruleUa).toContain('закінчення -ім');
    expect(inst.ruleEn).toContain('ending -im');
  });

  it('resolves possessive adjective suffix rules accurately per § 107', () => {
    // 1st declension
    const decl1 = resolvePossessiveSuffixRule(1);
    expect(decl1.suffix).toContain('-ин');
    expect(decl1.ruleUa).toContain('Ольжин');
    expect(decl1.ruleEn).toContain('-yn');

    // 2nd declension
    const decl2 = resolvePossessiveSuffixRule(2);
    expect(decl2.suffix).toContain('-ів');
    expect(decl2.ruleUa).toContain('батьків');
    expect(decl2.ruleEn).toContain('-iv');
  });

  it('resolves derivational suffix -ськ- mutations accurately per § 22', () => {
    // Velars (h, zh, z) -> -zk-
    const velar = resolveDerivationalSuffixMutationRule('velar');
    expect(velar.suffix).toBe('-зьк-');
    expect(velar.ruleUa).toContain('празький');

    // Dentals (k, ch, ts) -> -tsk-
    const dental = resolveDerivationalSuffixMutationRule('dental');
    expect(dental.suffix).toBe('-цьк-');
    expect(dental.ruleUa).toContain('козацький');

    // Sibilants (kh, sh, s) -> -skyi
    const sibilant = resolveDerivationalSuffixMutationRule('sibilant');
    expect(sibilant.suffix).toBe('-ськ-');
    expect(sibilant.ruleUa).toContain('чеський');
  });

  it('produces targeted feedback for learner responses', () => {
    const sampleCard: PracticeAdjectiveMechanicsCard = {
      card_id: 'test_adj_1',
      category: 'decl_soft_instrumental_im',
      cefr_level: 'A2',
      prompt_sentence: 'Діти милувалися ___ вечірнім небом.',
      blank_target: 'синім',
      correct_answer: 'синім',
      options: ['синім', 'синим', 'синьому', 'синього'],
      distractors: [
        {
          text: 'синим',
          interference_type: 'false_soft_instrumental_ym',
          explanation: {
            ua: 'М\'яка група вимагає закінчення -ім, а не -им.',
            en: 'Soft group requires -im, not -ym.',
          },
        },
        {
          text: 'синьому',
          interference_type: 'false_soft_dative_hard_ending',
          explanation: {
            ua: 'Давальний/місцевий відмінок замість орудного.',
            en: 'Dative/locative instead of instrumental.',
          },
        },
        {
          text: 'синього',
          interference_type: 'false_soft_genitive_hard_ending',
          explanation: {
            ua: 'Родовий відмінок замість орудного.',
            en: 'Genitive instead of instrumental.',
          },
        },
      ],
      pravopys_section: '§ 108',
      rule_summary: {
        ua: "М'яка група прикметників в орудному відмінку має -ім.",
        en: 'Soft adjectives take -im in the instrumental.',
      },
    };

    // Correct selection
    const correctRes = adjectiveMechanicsFeedbackFor(sampleCard, 'синім', 'ua');
    expect(correctRes.isCorrect).toBe(true);
    expect(correctRes.feedback).toContain('Правильно');

    // Distractor selection
    const distRes = adjectiveMechanicsFeedbackFor(sampleCard, 'синим', 'ua');
    expect(distRes.isCorrect).toBe(false);
    expect(distRes.feedback).toBe("М'яка група вимагає закінчення -ім, а не -им.");

    // Fallback unknown selection
    const fallbackRes = adjectiveMechanicsFeedbackFor(sampleCard, 'синій', 'en');
    expect(fallbackRes.isCorrect).toBe(false);
    expect(fallbackRes.feedback).toContain('Incorrect');
  });

  it('validates committed adjective mechanics deck parity and type adherence', () => {
    const candidates = [
      resolve(__dirname, '../../../data/practice/adjective_mechanics_deck.json'),
      resolve(process.cwd(), '../data/practice/adjective_mechanics_deck.json'),
      resolve(process.cwd(), 'data/practice/adjective_mechanics_deck.json'),
    ];
    const deckPath = candidates.find((p) => existsSync(p));
    expect(deckPath).toBeDefined();

    const raw = readFileSync(deckPath!, 'utf-8');
    const parsed = JSON.parse(raw);

    expect(parsed.version).toBe('1.0.0');
    expect(parsed.card_count).toBeGreaterThanOrEqual(60);
    expect(parsed.cards).toHaveLength(parsed.card_count);

    const validCategories = new Set<string>(ADJECTIVE_MECHANICS_CATEGORY_KEYS);
    const validInterferences = new Set<string>(ADJECTIVE_MECHANICS_INTERFERENCE_KEYS);

    for (const card of parsed.cards as PracticeAdjectiveMechanicsCard[]) {
      expect(validCategories.has(card.category)).toBe(true);
      expect(card.options).toHaveLength(4);
      expect(card.distractors).toHaveLength(3);
      expect(card.options).toContain(card.correct_answer);

      for (const distractor of card.distractors) {
        expect(validInterferences.has(distractor.interference_type)).toBe(true);
        expect(distractor.explanation.ua).toBeTruthy();
        expect(distractor.explanation.en).toBeTruthy();
      }
    }
  });
});
