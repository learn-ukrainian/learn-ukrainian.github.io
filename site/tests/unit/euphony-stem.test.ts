import { describe, expect, it } from 'vitest';
import {
  euphonyFeedbackFor,
  type PracticeEuphonyCard,
  resolveIYRules,
  resolveUVRules,
  resolveZIzZiRules,
} from '../../src/lib/lexicon/euphony-stem';

describe('euphony-stem', () => {
  it('resolves preposition У vs В accurately', () => {
    // Between consonants -> у
    expect(resolveUVRules('день', 'школі').choice).toBe('у');
    expect(resolveUVRules('він', 'лісі').choice).toBe('у');

    // Between vowels -> в
    expect(resolveUVRules('була', 'Одесі').choice).toBe('в');

    // Before в, ф, or clusters -> у
    expect(resolveUVRules('була', 'Франції').choice).toBe('у');
    expect(resolveUVRules('поїхав', 'Львів').choice).toBe('у');
    expect(resolveUVRules('він пірнув', 'воду').choice).toBe('у');

    // Start of sentence before consonant -> у, before vowel -> в
    expect(resolveUVRules(null, 'Києві').choice).toBe('у');
    expect(resolveUVRules(null, 'очах').choice).toBe('в');
  });

  it('resolves conjunction І vs Й accurately', () => {
    // Between consonants -> і
    expect(resolveIYRules('брат', 'сестра').choice).toBe('і');

    // Between vowels -> й
    expect(resolveIYRules('мама', 'Ольга').choice).toBe('й');

    // After vowel before consonant -> й
    expect(resolveIYRules('весна', 'літо').choice).toBe('й');

    // After consonant before vowel -> і
    expect(resolveIYRules('дуб', 'ясен').choice).toBe('і');

    // Start of sentence -> і
    expect(resolveIYRules(null, 'день').choice).toBe('і');
  });

  it('resolves preposition З vs ІЗ vs ЗІ accurately', () => {
    // Before pronoun «мною» -> зі
    expect(resolveZIzZiRules(null, 'мною').choice).toBe('зі');

    // Before sibilant clusters -> зі
    expect(resolveZIzZiRules('прокинувся', 'сну').choice).toBe('зі');
    expect(resolveZIzZiRules('вийшов', 'школи').choice).toBe('зі');

    // Before vowel -> з
    expect(resolveZIzZiRules('зустрівся', 'артистом').choice).toBe('з');

    // Before single consonant -> з
    expect(resolveZIzZiRules('приїхали', 'братом').choice).toBe('з');

    // Between consonants to avoid heavy clusters -> із
    expect(resolveZIzZiRules('лист', 'Бразилії').choice).toBe('із');
  });

  it('provides targeted feedback for correct and distractor choices', () => {
    const card: PracticeEuphonyCard = {
      id: 'test-second-palat',
      category: 'second_palatalization',
      promptUa: 'У мене в (рука) був квиток.',
      promptEn: 'Choose the correct form for (рука):',
      targetDisplay: 'руці',
      correctAnswer: 'руці',
      options: ['руці', 'рукі', 'ручі', 'руку'],
      distractors: [
        {
          form: 'рукі',
          interferenceType: 'non_alternating_stem',
          explanationUa: 'Форма «рукі» є калькою. В українській мові к чергується з ц: «руці».',
          explanationEn: "The form 'рукі' is a calque. In Ukrainian, к alternates with ц: 'руці'.",
        },
      ],
      pedagogicalRuleUa: 'Друга палаталізація: г, к, х чергуються із з, ц, с.',
      pedagogicalRuleEn: 'Second palatalization: г, к, х shift to з, ц, с.',
      pravopysRef: "Академічна граматика: друга палаталізація (г, к, х ➔ з', ц', с')",
    };

    const correctRes = euphonyFeedbackFor(card, 'руці');
    expect(correctRes.isCorrect).toBe(true);
    expect(correctRes.explanationUa).toContain('Правильно!');

    const wrongRes = euphonyFeedbackFor(card, 'рукі');
    expect(wrongRes.isCorrect).toBe(false);
    expect(wrongRes.interferenceType).toBe('non_alternating_stem');
    expect(wrongRes.explanationUa).toContain('калькою');
  });
});
