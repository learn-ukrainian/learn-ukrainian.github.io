import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import {
  type PracticeNumeralMechanicsCard,
  NUMERAL_MECHANICS_CATEGORY_KEYS,
  NUMERAL_MECHANICS_INTERFERENCE_KEYS,
  isGenitivePluralTierEnding,
  isPaucalTierEnding,
  numeralMechanicsFeedbackFor,
  resolveApproximateConstructionsRule,
  resolveCardinal200900DativeLocativeRule,
  resolveCardinal200900GenitiveRule,
  resolveCardinal200900InstrumentalRule,
  resolveCardinal4090100Rule,
  resolveCardinal5080Rule,
  resolveCollectiveFeminineRestrictionRule,
  resolveCollectiveMasculineRule,
  resolveCollectivePluraliaNeuterRule,
  resolveFractionalPivtoraRule,
  resolveGovernment234Rule,
  resolveGovernment5PlusRule,
  resolveGovernmentCompoundLastDigitRule,
  resolveOrdinalCompoundDeclensionRule,
  resolveTimeExpressionsRule,
} from '../../src/lib/lexicon/numeral-mechanics';

describe('numeral-mechanics', () => {
  it('defines all 15 numeral categories and 17 interference keys', () => {
    expect(NUMERAL_MECHANICS_CATEGORY_KEYS).toHaveLength(15);
    expect(NUMERAL_MECHANICS_INTERFERENCE_KEYS).toHaveLength(17);

    expect(NUMERAL_MECHANICS_CATEGORY_KEYS).toContain('cardinal_50_80_inflection');
    expect(NUMERAL_MECHANICS_CATEGORY_KEYS).toContain('cardinal_200_900_genitive');
    expect(NUMERAL_MECHANICS_CATEGORY_KEYS).toContain('cardinal_200_900_dative_locative');
    expect(NUMERAL_MECHANICS_CATEGORY_KEYS).toContain('cardinal_200_900_instrumental');
    expect(NUMERAL_MECHANICS_CATEGORY_KEYS).toContain('cardinal_40_90_100_paradigm');
    expect(NUMERAL_MECHANICS_CATEGORY_KEYS).toContain('government_2_3_4_nominative_plural');
    expect(NUMERAL_MECHANICS_CATEGORY_KEYS).toContain('government_5_plus_genitive_plural');
    expect(NUMERAL_MECHANICS_CATEGORY_KEYS).toContain('government_compound_last_digit');
    expect(NUMERAL_MECHANICS_CATEGORY_KEYS).toContain('collective_masculine_animate');
    expect(NUMERAL_MECHANICS_CATEGORY_KEYS).toContain('collective_restriction_feminine');
    expect(NUMERAL_MECHANICS_CATEGORY_KEYS).toContain('collective_pluralia_tantum_neuter');
    expect(NUMERAL_MECHANICS_CATEGORY_KEYS).toContain('fractional_pivtora_government');
    expect(NUMERAL_MECHANICS_CATEGORY_KEYS).toContain('ordinal_compound_declension');
    expect(NUMERAL_MECHANICS_CATEGORY_KEYS).toContain('time_expressions_anti_calque');
    expect(NUMERAL_MECHANICS_CATEGORY_KEYS).toContain('approximate_numerical_constructions');

    expect(NUMERAL_MECHANICS_INTERFERENCE_KEYS).toContain('inflected_first_root_50_80');
    expect(NUMERAL_MECHANICS_INTERFERENCE_KEYS).toContain('russianism_genitive_hundreds');
    expect(NUMERAL_MECHANICS_INTERFERENCE_KEYS).toContain('russianism_instrumental_hundreds');
    expect(NUMERAL_MECHANICS_INTERFERENCE_KEYS).toContain('russianism_genitive_singular_calque');
    expect(NUMERAL_MECHANICS_INTERFERENCE_KEYS).toContain('collective_with_adult_female');
  });

  it('resolves cardinal declension rules accurately per § 105', () => {
    const r50 = resolveCardinal5080Rule();
    expect(r50.citation).toContain('§ 105.4');
    expect(r50.ruleUa).toContain("п'ятдесяти");
    expect(r50.ruleEn).toContain('invariant');

    const r200g = resolveCardinal200900GenitiveRule();
    expect(r200g.citation).toContain('§ 105.5');
    expect(r200g.ruleUa).toContain('двохсот');
    expect(r200g.ruleEn).toContain('Genitive');

    const r200d = resolveCardinal200900DativeLocativeRule();
    expect(r200d.citation).toContain('§ 105.5');
    expect(r200d.ruleUa).toContain('-стам');
    expect(r200d.ruleEn).toContain('Locative');

    const r200i = resolveCardinal200900InstrumentalRule();
    expect(r200i.citation).toContain('§ 105.5');
    expect(r200i.ruleUa).toContain('-стами');
    expect(r200i.ruleEn).toContain('Instrumental');

    const r40 = resolveCardinal4090100Rule();
    expect(r40.citation).toContain('§ 105.7');
    expect(r40.ruleUa).toContain("сорока, дев'яноста, ста");
  });

  it('resolves government and collective rules accurately', () => {
    const g234 = resolveGovernment234Rule();
    expect(g234.ruleUa).toContain('називного');
    expect(g234.ruleEn).toContain('Nominative plural');

    const g5 = resolveGovernment5PlusRule();
    expect(g5.ruleUa).toContain('родового');
    expect(g5.ruleEn).toContain('Genitive plural');

    const gComp = resolveGovernmentCompoundLastDigitRule();
    expect(gComp.ruleUa).toContain('останнім словом');

    const cMasc = resolveCollectiveMasculineRule();
    expect(cMasc.citation).toContain('Синтаксичні норми');
    expect(cMasc.citation).toContain('105');
    expect(cMasc.ruleUa).toContain('троє друзів');

    const cFem = resolveCollectiveFeminineRestrictionRule();
    expect(cFem.citation).toContain('Синтаксичні норми');
    expect(cFem.ruleUa).toContain('НЕ вживаються');

    const cPlur = resolveCollectivePluraliaNeuterRule();
    expect(cPlur.citation).toContain('Синтаксичні норми');
    expect(cPlur.citation).toContain('105');
    expect(cPlur.ruleUa).toContain('двоє дверей');

    const frac = resolveFractionalPivtoraRule();
    expect(frac.citation).toContain('§ 107');
    expect(frac.ruleUa).toContain('родового відмінка ОДНИНИ');

    const ord = resolveOrdinalCompoundDeclensionRule();
    expect(ord.citation).toContain('§ 106.2');
    expect(ord.ruleUa).toContain('ЛИШЕ ОСТАННЄ');

    const time = resolveTimeExpressionsRule();
    expect(time.ruleUa).toContain('о десятій годині');

    const approx = resolveApproximateConstructionsRule();
    expect(approx.ruleUa).toContain('інверсією');
  });

  it('validates number tier classification helpers', () => {
    expect(isPaucalTierEnding(2)).toBe(true);
    expect(isPaucalTierEnding(3)).toBe(true);
    expect(isPaucalTierEnding(4)).toBe(true);
    expect(isPaucalTierEnding(22)).toBe(true);
    expect(isPaucalTierEnding(34)).toBe(true);
    expect(isPaucalTierEnding(12)).toBe(false);
    expect(isPaucalTierEnding(14)).toBe(false);
    expect(isPaucalTierEnding(5)).toBe(false);

    expect(isGenitivePluralTierEnding(5)).toBe(true);
    expect(isGenitivePluralTierEnding(6)).toBe(true);
    expect(isGenitivePluralTierEnding(10)).toBe(true);
    expect(isGenitivePluralTierEnding(11)).toBe(true);
    expect(isGenitivePluralTierEnding(12)).toBe(true);
    expect(isGenitivePluralTierEnding(14)).toBe(true);
    expect(isGenitivePluralTierEnding(25)).toBe(true);
    expect(isGenitivePluralTierEnding(21)).toBe(false);
    expect(isGenitivePluralTierEnding(22)).toBe(false);
  });

  it('correctly provides feedback for correct selections', () => {
    const sampleCard: PracticeNumeralMechanicsCard = {
      card_id: 'numeral_01',
      category: 'cardinal_50_80_inflection',
      cefr_level: 'A2',
      prompt_sentence: 'У конференції взяли участь понад _______ делегатів.',
      blank_target: "п'ятдесят",
      correct_answer: "п'ятдесят",
      options: ["п'ятдесят", "п'ятидесят", "п'ятидесяти", "п'ятьдесят"],
      distractors: [
        {
          text: "п'ятидесят",
          interference_type: 'inflected_first_root_50_80',
          explanation: {
            ua: 'Перша частина не відмінюється.',
            en: 'First root does not inflect.',
          },
        },
      ],
      pravopys_section: 'Правопис 2019 § 107',
      rule_summary: {
        ua: 'Відмінюється лише друга частина.',
        en: 'Only the second root inflects.',
      },
    };

    const evalResult = numeralMechanicsFeedbackFor(sampleCard, "п'ятдесят");
    expect(evalResult.isCorrect).toBe(true);
    expect(evalResult.selectedOption).toBe("п'ятдесят");
    expect(evalResult.feedbackUa).toContain('Чудово! Правильно');
    expect(evalResult.feedbackEn).toContain('Excellent! Correct');
    expect(evalResult.ruleCitation).toBe('Правопис 2019 § 107');
  });

  it('correctly provides feedback for distractors with misconception explanations', () => {
    const sampleCard: PracticeNumeralMechanicsCard = {
      card_id: 'numeral_26',
      category: 'government_2_3_4_nominative_plural',
      cefr_level: 'A1',
      prompt_sentence: 'У моєму дворі ростуть три високі _______.',
      blank_target: 'дуби',
      correct_answer: 'дуби',
      options: ['дуби', 'дуба', 'дубів', 'дубові'],
      distractors: [
        {
          text: 'дуба',
          interference_type: 'russianism_genitive_singular_calque',
          explanation: {
            ua: 'Форма родового однини є калькою.',
            en: 'Genitive singular is a calque.',
          },
        },
      ],
      pravopys_section: 'Синтаксичні норми',
      rule_summary: {
        ua: 'Керують називним множини.',
        en: 'Govern Nominative plural.',
      },
    };

    const evalResult = numeralMechanicsFeedbackFor(sampleCard, 'дуба');
    expect(evalResult.isCorrect).toBe(false);
    expect(evalResult.selectedOption).toBe('дуба');
    expect(evalResult.misconceptionType).toBe('russianism_genitive_singular_calque');
    expect(evalResult.feedbackUa).toContain('Неправильно: «дуба»');
    expect(evalResult.feedbackUa).toContain('Форма родового однини є калькою');
    expect(evalResult.feedbackEn).toContain('Genitive singular is a calque');
  });

  it('evaluates all 75 committed cards across all 4 options without throwing', () => {
    const deckPath = resolve(__dirname, '../../../data/practice/numeral_mechanics_deck.json');
    expect(existsSync(deckPath)).toBe(true);

    const content = readFileSync(deckPath, 'utf-8');
    const deck = JSON.parse(content);

    expect(deck.card_count).toBe(75);
    expect(deck.cards).toHaveLength(75);

    let totalEvaluated = 0;
    for (const card of deck.cards as PracticeNumeralMechanicsCard[]) {
      expect(card.options).toHaveLength(4);

      // Test correct answer
      const correctEval = numeralMechanicsFeedbackFor(card, card.correct_answer);
      expect(correctEval.isCorrect).toBe(true);
      expect(correctEval.feedbackUa).toContain('Чудово');
      totalEvaluated += 1;

      // Test each distractor
      for (const d of card.distractors) {
        const distEval = numeralMechanicsFeedbackFor(card, d.text);
        expect(distEval.isCorrect).toBe(false);
        expect(distEval.selectedOption).toBe(d.text);
        expect(distEval.misconceptionType).toBe(d.interference_type);
        expect(distEval.feedbackUa).toContain(d.text);
        totalEvaluated += 1;
      }
    }

    expect(totalEvaluated).toBe(75 * 4); // 300 evaluations
  });

  it('ensures register clarity and unambiguous distractors for approximate constructions', () => {
    const deckPath = resolve(__dirname, '../../../data/practice/numeral_mechanics_deck.json');
    const content = readFileSync(deckPath, 'utf-8');
    const deck = JSON.parse(content);

    const card71 = deck.cards.find((c: PracticeNumeralMechanicsCard) => c.card_id === 'numeral_71');
    expect(card71.prompt_sentence.toLowerCase()).toContain('офіційному');

    const card75 = deck.cards.find((c: PracticeNumeralMechanicsCard) => c.card_id === 'numeral_75');
    expect(card75.correct_answer).toBe('роки три');
    const distractorTexts = card75.distractors.map((d: { text: string }) => d.text);
    expect(distractorTexts).not.toContain('біля трьох років');
    expect(distractorTexts).toContain('порядка трьох років');
  });
});
