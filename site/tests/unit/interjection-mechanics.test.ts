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
    expect(INTERJECTION_MECHANICS_CATEGORY_KEYS).toContain(
      'interjection_spelling_multiword_separate',
    );
    expect(INTERJECTION_MECHANICS_CATEGORY_KEYS).toContain(
      'interjection_syntax_punctuation_particle',
    );
  });

  it('resolves interjection rules accurately per Правопис 2019', () => {
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
      expect(r.citation.length).toBeGreaterThan(5);
      expect(r.ruleUa.length).toBeGreaterThan(20);
      expect(r.ruleEn.length).toBeGreaterThan(20);
    }

    expect(resolveSpellingHyphenRepeatedRule().citation).toContain('§ 35, п. 5, 4)');
    expect(resolveSpellingParticlesHyphenRule().citation).toContain('§ 44, п. 3, 1)');
    expect(resolveSpellingMultiwordSeparateRule().citation).toContain('§ 41, п. 2');
    expect(resolveSyntaxPunctuationParticleRule().citation).toContain('§ 158, п. 9');
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
      rule_citation: 'Академічна граматика; СУМ-20; Правопис 2019 § 157, п. 3, § 158, п. 9',
      rule_summary: {
        ua: 'Емоційні вигуки виражають почуття радості або захоплення.',
        en: 'Emotional interjections express feelings of joy or admiration.',
      },
    };

    const evalResult = interjectionMechanicsFeedbackFor(sampleCard, 'Ура');
    expect(evalResult.isCorrect).toBe(true);
    expect(evalResult.feedbackUa).toContain('Чудово! Правильно: «Ура»');
    expect(evalResult.feedbackEn).toContain('Excellent! Correct: "Ура"');
    expect(evalResult.ruleCitation).toBe(
      'Академічна граматика; СУМ-20; Правопис 2019 § 157, п. 3, § 158, п. 9',
    );
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
            ua: 'Слова «будь ласка» пишуться строго окремо без дефіса per § 41, п. 2.',
            en: "Words 'будь ласка' are spelled strictly separately without hyphen per § 41, p. 2.",
          },
        },
      ],
      rule_citation: 'Правопис 2019 § 41, п. 2, § 53; СУМ-20; Авраменко § 88',
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
    const deckPath = path.resolve(
      __dirname,
      '../../../registry/practice/interjection_mechanics_deck.json',
    );
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

  it('verifies Card 45 does not reject valid interjection Стук-стук and correctly evaluates Тік-так', () => {
    const deckPath = path.resolve(
      __dirname,
      '../../../registry/practice/interjection_mechanics_deck.json',
    );
    const rawData = fs.readFileSync(deckPath, 'utf-8');
    const deck = JSON.parse(rawData) as InterjectionMechanicsDeckPayload;

    const card45 = deck.cards.find((c) => c.id === 'interjection_card_45');
    expect(card45).toBeDefined();
    expect(card45!.correct_answer).toBe('Тук-тук');

    const distractorTexts = card45!.distractors.map((d) => d.text);
    expect(distractorTexts).not.toContain('Стук-стук');
    expect(distractorTexts).toContain('Тік-так');

    const evalResult = interjectionMechanicsFeedbackFor(card45!, 'Тік-так');
    expect(evalResult.isCorrect).toBe(false);
    expect(evalResult.misconceptionType).toBe('INCORRECT_SOUND_SOURCE');
    expect(evalResult.feedbackUa).toContain('годинника');
  });

  it('verifies Card 33 feedback and Nature Mechanics rule teach кап-кап and not stale крап-крап', () => {
    const natureRule = resolveOnomatopoeiaNatureMechanicsRule();
    expect(natureRule.ruleUa).toContain('кап-кап');
    expect(natureRule.ruleEn).toContain('кап-кап');
    expect(natureRule.ruleUa).not.toContain('крап-крап');
    expect(natureRule.ruleEn).not.toContain('крап-крап');

    const deckPath = path.resolve(
      __dirname,
      '../../../registry/practice/interjection_mechanics_deck.json',
    );
    const rawData = fs.readFileSync(deckPath, 'utf-8');
    const deck = JSON.parse(rawData) as InterjectionMechanicsDeckPayload;

    const card33 = deck.cards.find((c) => c.id === 'interjection_card_33');
    expect(card33).toBeDefined();
    expect(card33!.correct_answer).toBe('Кап-кап');
    expect(card33!.target_token).toBe('кап-кап');
    expect(card33!.rule_summary.ua).toContain('кап-кап');
    expect(card33!.rule_summary.en).toContain('кап-кап');
    expect(card33!.rule_summary.ua).not.toContain('крап-крап');
    expect(card33!.rule_summary.en).not.toContain('крап-крап');

    const evalResult = interjectionMechanicsFeedbackFor(card33!, 'Кап-кап');
    expect(evalResult.isCorrect).toBe(true);
    expect(evalResult.feedbackUa).toContain('Кап-кап');

    const natureCards = deck.cards.filter(
      (c) => c.category === 'interjection_onomatopoeia_nature_mechanics',
    );
    expect(natureCards).toHaveLength(5);
    for (const card of natureCards) {
      expect(card.rule_summary.ua).toContain('кап-кап');
      expect(card.rule_summary.en).toContain('кап-кап');
      expect(card.rule_summary.ua).not.toContain('крап-крап');
      expect(card.rule_summary.en).not.toContain('крап-крап');
    }
  });
});
