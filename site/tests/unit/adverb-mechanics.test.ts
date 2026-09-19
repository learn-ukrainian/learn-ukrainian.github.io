import { describe, expect, it } from 'vitest';
import {
  ADVERB_MECHANICS_CATEGORY_KEYS,
  ADVERB_MECHANICS_INTERFERENCE_KEYS,
  adverbMechanicsFeedbackFor,
  resolveMannerActionRule,
  resolveTimeRule,
  resolvePlaceDirectionRule,
  resolveMeasureDegreeRule,
  resolveCausePurposeRule,
  resolvePrefixPoRule,
  resolveParticlesHyphenRule,
  resolveReduplicationRule,
  resolveTogetherFusedRule,
  resolveHomophone1Rule,
  resolveHomophone2Rule,
  resolveSeparatePhrasesRule,
  resolveComparisonSyntheticRule,
  resolveComparisonSuperlativeRule,
  resolveAntiCalqueRule,
  type PracticeAdverbMechanicsCard,
  type AdverbMechanicsDeckPayload,
} from '../../src/lib/lexicon/adverb-mechanics';
import * as fs from 'fs';
import * as path from 'path';

describe('adverb-mechanics', () => {
  it('defines all 15 adverb categories and 14 interference keys', () => {
    expect(ADVERB_MECHANICS_CATEGORY_KEYS).toHaveLength(15);
    expect(ADVERB_MECHANICS_INTERFERENCE_KEYS).toHaveLength(14);
    expect(ADVERB_MECHANICS_CATEGORY_KEYS).toContain('adverb_semantic_manner_action');
    expect(ADVERB_MECHANICS_CATEGORY_KEYS).toContain('adverb_spelling_prefix_po');
    expect(ADVERB_MECHANICS_CATEGORY_KEYS).toContain('adverb_homophone_napamyat_vden_dodomu');
    expect(ADVERB_MECHANICS_CATEGORY_KEYS).toContain('adverb_anti_calque');
  });

  it('resolves adverb rules accurately per §§ 40–45', () => {
    const rules = [
      resolveMannerActionRule(),
      resolveTimeRule(),
      resolvePlaceDirectionRule(),
      resolveMeasureDegreeRule(),
      resolveCausePurposeRule(),
      resolvePrefixPoRule(),
      resolveParticlesHyphenRule(),
      resolveReduplicationRule(),
      resolveTogetherFusedRule(),
      resolveHomophone1Rule(),
      resolveHomophone2Rule(),
      resolveSeparatePhrasesRule(),
      resolveComparisonSyntheticRule(),
      resolveComparisonSuperlativeRule(),
      resolveAntiCalqueRule(),
    ];

    expect(rules).toHaveLength(15);
    for (const r of rules) {
      expect(r.citation).toContain('Правопис');
      expect(r.ruleUa.length).toBeGreaterThan(20);
      expect(r.ruleEn.length).toBeGreaterThan(20);
    }
  });

  it('correctly provides feedback for correct selections', () => {
    const sampleCard: PracticeAdverbMechanicsCard = {
      id: 'adverb_card_01',
      category: 'adverb_semantic_manner_action',
      prompt: 'Студент вивчив вірш _______.',
      target_token: "напам'ять",
      correct_answer: "напам'ять",
      options: ["напам'ять", "на пам'ять", "на-пам'ять", "по пам'яті"],
      distractors: [
        {
          text: "на пам'ять",
          interference_key: 'HOMOPHONE_NOUN_PREP_CONFUSION',
          explanation: {
            ua: "«На пам'ять» окремо є іменником з прийменником.",
            en: "'На пам'ять' separately is a noun with preposition.",
          },
        },
      ],
      rule_citation: 'Правопис 2019 § 43',
      rule_summary: {
        ua: "Прислівник напам'ять пишеться разом.",
        en: "Adverb напам'ять is spelled as one word.",
      },
    };

    const evalResult = adverbMechanicsFeedbackFor(sampleCard, "напам'ять");
    expect(evalResult.isCorrect).toBe(true);
    expect(evalResult.feedbackUa).toContain('Чудово! Правильно: «напам\'ять»');
    expect(evalResult.feedbackEn).toContain('Excellent! Correct: "напам\'ять"');
    expect(evalResult.ruleCitation).toBe('Правопис 2019 § 43');
  });

  it('correctly provides feedback for distractors with misconception explanations', () => {
    const sampleCard: PracticeAdverbMechanicsCard = {
      id: 'adverb_card_56',
      category: 'adverb_spelling_separate',
      prompt: 'Ми, _______, не зможемо прийти.',
      target_token: 'на жаль',
      correct_answer: 'на жаль',
      options: ['на жаль', 'нажаль', 'на-жаль', 'к жалю'],
      distractors: [
        {
          text: 'нажаль',
          interference_key: 'UNWARRANTED_FUSION',
          explanation: {
            ua: 'Прислівникове сполучення «на жаль» пишеться строго окремо.',
            en: "Phrase 'на жаль' is written strictly separately.",
          },
        },
      ],
      rule_citation: 'Правопис 2019 § 45',
      rule_summary: {
        ua: 'Прислівникові сполучення пишуться окремо.',
        en: 'Adverbial phrases are written separately.',
      },
    };

    const evalResult = adverbMechanicsFeedbackFor(sampleCard, 'нажаль');
    expect(evalResult.isCorrect).toBe(false);
    expect(evalResult.feedbackUa).toContain('Неправильно: «нажаль»');
    expect(evalResult.feedbackUa).toContain('строго окремо');
    expect(evalResult.feedbackEn).toContain('strictly separately');
    expect(evalResult.misconceptionType).toBe('UNWARRANTED_FUSION');
  });

  it('evaluates all 75 committed cards across all 4 options without throwing', () => {
    const deckPath = path.resolve(__dirname, '../../../data/practice/adverb_mechanics_deck.json');
    expect(fs.existsSync(deckPath)).toBe(true);

    const rawData = fs.readFileSync(deckPath, 'utf-8');
    const deck = JSON.parse(rawData) as AdverbMechanicsDeckPayload;

    expect(deck.card_count).toBe(75);
    expect(deck.categories).toHaveLength(15);
    expect(deck.cards).toHaveLength(75);

    let totalEvaluations = 0;
    let correctCount = 0;

    for (const card of deck.cards) {
      expect(card.options).toHaveLength(4);
      expect(card.distractors).toHaveLength(3);

      for (const option of card.options) {
        const evaluation = adverbMechanicsFeedbackFor(card, option);
        totalEvaluations += 1;

        if (option === card.correct_answer) {
          expect(evaluation.isCorrect).toBe(true);
          correctCount += 1;
        } else {
          expect(evaluation.isCorrect).toBe(false);
          expect(evaluation.misconceptionType).toBeDefined();
        }
      }
    }

    expect(totalEvaluations).toBe(300);
    expect(correctCount).toBe(75);
  });
});
