import { describe, expect, it } from 'vitest';
import {
  INTERJECTION_MECHANICS_CATEGORY_KEYS,
  INTERJECTION_MECHANICS_INTERFERENCE_KEYS,
  interjectionMechanicsFeedbackFor,
  resolveEmotionalPositiveRule,
  resolveEmotionalNegativeRule,
  resolveVolitionalImperativeRule,
  resolveVolitionalAnimalRule,
  resolveEtiquetteGreetingFarewellRule,
  resolveEtiquetteGratitudeApologyRule,
  resolveOnomatopoeiaNatureMechanicsRule,
  resolveOnomatopoeiaAnimalSoundsRule,
  resolveSpellingHyphenRepeatedRule,
  resolveSpellingParticlesHyphenRule,
  resolveSpellingMultiwordSeparateRule,
  resolveSyntaxPunctuationParticleRule,
  type PracticeInterjectionMechanicsCard,
  type InterjectionMechanicsDeckPayload,
} from '../../src/lib/lexicon/interjection-mechanics';
import * as fs from 'fs';
import * as path from 'path';

describe('interjection-mechanics', () => {
  it('defines all 12 interjection categories and 15 interference keys', () => {
    expect(INTERJECTION_MECHANICS_CATEGORY_KEYS).toHaveLength(12);
    expect(INTERJECTION_MECHANICS_INTERFERENCE_KEYS).toHaveLength(15);
    expect(INTERJECTION_MECHANICS_CATEGORY_KEYS).toContain('interjection_emotional_positive');
    expect(INTERJECTION_MECHANICS_CATEGORY_KEYS).toContain('interjection_volitional_animal');
    expect(INTERJECTION_MECHANICS_CATEGORY_KEYS).toContain('interjection_spelling_multiword_separate');
    expect(INTERJECTION_MECHANICS_CATEGORY_KEYS).toContain('interjection_syntax_punctuation_particle');
  });

  it('resolves interjection rules accurately per Правопис 2019 § 46', () => {
    const rules = [
      resolveEmotionalPositiveRule(),
      resolveEmotionalNegativeRule(),
      resolveVolitionalImperativeRule(),
      resolveVolitionalAnimalRule(),
      resolveEtiquetteGreetingFarewellRule(),
      resolveEtiquetteGratitudeApologyRule(),
      resolveOnomatopoeiaNatureMechanicsRule(),
      resolveOnomatopoeiaAnimalSoundsRule(),
      resolveSpellingHyphenRepeatedRule(),
      resolveSpellingParticlesHyphenRule(),
      resolveSpellingMultiwordSeparateRule(),
      resolveSyntaxPunctuationParticleRule(),
    ];

    expect(rules).toHaveLength(12);
    for (const r of rules) {
      expect(r.citation).toContain('Правопис');
      expect(r.citation).toContain('§ 46');
      expect(r.ruleUa.length).toBeGreaterThan(20);
      expect(r.ruleEn.length).toBeGreaterThan(20);
    }

    expect(resolveSpellingHyphenRepeatedRule().citation).toContain('§ 46, п. 1, а)');
    expect(resolveSpellingParticlesHyphenRule().citation).toContain('§ 46, п. 1, б), в)');
    expect(resolveSpellingMultiwordSeparateRule().citation).toContain('§ 46, п. 2');
  });

  it('correctly provides feedback for correct selections', () => {
    const sampleCard: PracticeInterjectionMechanicsCard = {
      id: 'interjection_card_01',
      category: 'interjection_emotional_positive',
      prompt: '«_______! Наша футбольна збірна здобула перемогу!»',
      target_token: 'ура',
      correct_answer: 'Ура',
      options: ['Ура', 'Ой', 'Тьху', 'Цить'],
      distractors: [
        {
          text: 'Ой',
          interference_key: 'INCORRECT_EMOTIONAL_TONE',
          explanation: {
            ua: 'Вигук «ой» виражає біль або сум, а не тріумф.',
            en: "Interjection 'ой' expresses pain or grief, not triumph.",
          },
        },
      ],
      rule_citation: 'Правопис 2019 § 46; Академічна граматика; СУМ-20',
      rule_summary: {
        ua: 'Емоційні вигуки виражають почуття радості або захоплення.',
        en: 'Emotional interjections express feelings of joy or admiration.',
      },
    };

    const evalResult = interjectionMechanicsFeedbackFor(sampleCard, 'Ура');
    expect(evalResult.isCorrect).toBe(true);
    expect(evalResult.feedbackUa).toContain('Чудово! Правильно: «Ура»');
    expect(evalResult.feedbackEn).toContain('Excellent! Correct: "Ура"');
    expect(evalResult.ruleCitation).toBe('Правопис 2019 § 46; Академічна граматика; СУМ-20');
  });

  it('correctly provides feedback for distractors with misconception explanations', () => {
    const sampleCard: PracticeInterjectionMechanicsCard = {
      id: 'interjection_card_26',
      category: 'interjection_etiquette_gratitude_apology',
      prompt: 'Допоможіть мені, _______, з цією валізою.',
      target_token: 'будь ласка',
      correct_answer: 'будь ласка',
      options: ['будь ласка', 'будь-ласка', 'будьласка', 'пожалуста'],
      distractors: [
        {
          text: 'будь-ласка',
          interference_key: 'UNWARRANTED_HYPHEN',
          explanation: {
            ua: 'Слова «будь ласка» пишуться строго окремо без дефіса per § 46, п. 2.',
            en: "Words 'будь ласка' are spelled strictly separately without hyphen per § 46, p. 2.",
          },
        },
      ],
      rule_citation: 'Правопис 2019 § 46, п. 2; СУМ-20',
      rule_summary: {
        ua: 'Етикетний зворот «будь ласка» пишеться окремо.',
        en: "Etiquette phrase 'будь ласка' is written separately.",
      },
    };

    const evalResult = interjectionMechanicsFeedbackFor(sampleCard, 'будь-ласка');
    expect(evalResult.isCorrect).toBe(false);
    expect(evalResult.feedbackUa).toContain('Неправильно: «будь-ласка»');
    expect(evalResult.feedbackUa).toContain('строго окремо');
    expect(evalResult.feedbackEn).toContain('strictly separately');
    expect(evalResult.misconceptionType).toBe('UNWARRANTED_HYPHEN');
  });

  it('evaluates all 60 committed cards across all 4 options without throwing', () => {
    const deckPath = path.resolve(__dirname, '../../../data/practice/interjection_mechanics_deck.json');
    expect(fs.existsSync(deckPath)).toBe(true);

    const rawData = fs.readFileSync(deckPath, 'utf-8');
    const deck = JSON.parse(rawData) as InterjectionMechanicsDeckPayload;

    expect(deck.card_count).toBe(60);
    expect(deck.categories).toHaveLength(12);
    expect(deck.cards).toHaveLength(60);

    let totalEvaluations = 0;
    let correctCount = 0;

    for (const card of deck.cards) {
      expect(card.options).toHaveLength(4);
      expect(card.distractors).toHaveLength(3);

      for (const option of card.options) {
        const evaluation = interjectionMechanicsFeedbackFor(card, option);
        totalEvaluations += 1;

        if (option === card.correct_answer) {
          expect(evaluation.isCorrect).toBe(true);
          correctCount += 1;
        } else {
          expect(evaluation.isCorrect).toBe(false);
          expect(evaluation.misconceptionType).toBeDefined();
        }

        expect(evaluation.feedbackUa).toBeTruthy();
        expect(evaluation.feedbackEn).toBeTruthy();
        expect(evaluation.ruleCitation).toBeTruthy();
      }
    }

    // 60 cards * 4 options = 240 evaluations
    expect(totalEvaluations).toBe(240);
    expect(correctCount).toBe(60);
  });
});
