import { describe, expect, it } from 'vitest';
import {
  classifyNumeralTier,
  matchesNumeralFilter,
  normalizeNumeralItem,
  numeralFeedbackFor,
  NUMERAL_TIER_META,
  type PracticeNumeralItem,
} from '../../src/lib/lexicon/numeral-agreement';

describe('numeral-agreement', () => {
  it('classifies numeral values across all five tiers', () => {
    // Tier 1: Ends in 1 (except 11)
    expect(classifyNumeralTier(1)).toBe('tier_1_ends_in_1');
    expect(classifyNumeralTier(21)).toBe('tier_1_ends_in_1');
    expect(classifyNumeralTier(101)).toBe('tier_1_ends_in_1');
    expect(classifyNumeralTier('41')).toBe('tier_1_ends_in_1');

    // Tier 2: Ends in 2, 3, 4 (except 12-14)
    expect(classifyNumeralTier(2)).toBe('tier_2_ends_in_2_3_4');
    expect(classifyNumeralTier(3)).toBe('tier_2_ends_in_2_3_4');
    expect(classifyNumeralTier(4)).toBe('tier_2_ends_in_2_3_4');
    expect(classifyNumeralTier(22)).toBe('tier_2_ends_in_2_3_4');
    expect(classifyNumeralTier(33)).toBe('tier_2_ends_in_2_3_4');
    expect(classifyNumeralTier('104')).toBe('tier_2_ends_in_2_3_4');

    // Tier 3: 5+, and teens 11-14
    expect(classifyNumeralTier(5)).toBe('tier_3_plural_5_plus');
    expect(classifyNumeralTier(11)).toBe('tier_3_plural_5_plus');
    expect(classifyNumeralTier(12)).toBe('tier_3_plural_5_plus');
    expect(classifyNumeralTier(13)).toBe('tier_3_plural_5_plus');
    expect(classifyNumeralTier(14)).toBe('tier_3_plural_5_plus');
    expect(classifyNumeralTier(20)).toBe('tier_3_plural_5_plus');
    expect(classifyNumeralTier(114)).toBe('tier_3_plural_5_plus');

    // Tier 4: Fractions and decimals
    expect(classifyNumeralTier('півтора')).toBe('tier_4_fractional');
    expect(classifyNumeralTier('півтори')).toBe('tier_4_fractional');
    expect(classifyNumeralTier(2.5)).toBe('tier_4_fractional');
    expect(classifyNumeralTier('0.5')).toBe('tier_4_fractional');

    // Tier 5: Collectives
    expect(classifyNumeralTier('двоє')).toBe('tier_5_collective');
    expect(classifyNumeralTier('троє')).toBe('tier_5_collective');
    expect(classifyNumeralTier('четверо')).toBe('tier_5_collective');
  });

  it('provides Russianism anti-calque feedback for Tier 2 false Genitive singular choices', () => {
    const item: PracticeNumeralItem = {
      id: 'numeral-tier_2-zhurnal-2',
      tier: 'tier_2_ends_in_2_3_4',
      numeralDisplay: '2',
      numeralWords: 'два',
      lemma: 'журнал',
      gender: 'm',
      isAnim: false,
      cefrLevel: 'A2',
      targetCase: 'називний',
      targetNumber: 'plural',
      correctForm: 'журнали',
      options: ['журнали', 'журналу', 'журналів', 'журнал'],
      distractors: [
        {
          form: 'журналу',
          interferenceType: 'russianism_calque',
          explanationUa:
            'У родовому відмінку однини іменники після 2, 3, 4 вживаються в російській мові («два журнала»). В українській мові після 2, 3, 4 потрібен називний відмінок множини: «2 журнали».',
          explanationEn:
            "Using Genitive singular after 2, 3, 4 is a Russianism calque. Ukrainian requires Nominative plural: '2 журнали'.",
        },
        {
          form: 'журналів',
          interferenceType: 'overgeneralized_plural',
          explanationUa: 'Родовий відмінок множини вживається після 5+.',
          explanationEn: 'Genitive plural is used after 5+.',
        },
        {
          form: 'журнал',
          interferenceType: 'nominative_singular_bias',
          explanationUa: 'Початкова словникова форма не вживається після 2.',
          explanationEn: 'Base form is not used after 2.',
        },
      ],
      promptUa: '2 (журнал) ➔ 2 …',
      promptEn: 'Choose the correct form for: 2 (журнал)',
      pedagogicalRuleUa: 'Числівники 2, 3, 4 керують називним відмінком множини.',
      pedagogicalRuleEn: 'Numerals 2, 3, 4 govern Nominative plural.',
      pravopysRef: "Академічна граматика: сполучення числівників 2, 3, 4 з іменником (Волкова, Масло 2012, с. 91)",
    };

    // Correct choice
    const correctFeedback = numeralFeedbackFor(item, 'журнали');
    expect(correctFeedback.isCorrect).toBe(true);
    expect(correctFeedback.explanationUa).toContain('Правильно!');

    // Russianism calque choice
    const calqueFeedback = numeralFeedbackFor(item, 'журналу');
    expect(calqueFeedback.isCorrect).toBe(false);
    expect(calqueFeedback.interferenceType).toBe('russianism_calque');
    expect(calqueFeedback.explanationUa).toContain('російській мові');
    expect(calqueFeedback.explanationEn).toContain('Russianism');

    // Overgeneralized plural choice
    const pluralFeedback = numeralFeedbackFor(item, 'журналів');
    expect(pluralFeedback.isCorrect).toBe(false);
    expect(pluralFeedback.interferenceType).toBe('overgeneralized_plural');
  });

  it('filters items correctly by tier and CEFR level', () => {
    const item: PracticeNumeralItem = {
      id: 'test-item',
      tier: 'tier_2_ends_in_2_3_4',
      numeralDisplay: '4',
      numeralWords: 'чотири',
      lemma: 'будинок',
      gender: 'm',
      isAnim: false,
      cefrLevel: 'A2',
      targetCase: 'називний',
      targetNumber: 'plural',
      correctForm: 'будинки',
      options: ['будинки', 'будинку', 'будинків', 'будинок'],
      distractors: [],
      promptUa: '',
      promptEn: '',
      pedagogicalRuleUa: '',
      pedagogicalRuleEn: '',
      pravopysRef: '',
    };

    expect(matchesNumeralFilter(item, {})).toBe(true);
    expect(matchesNumeralFilter(item, { tiers: ['tier_2_ends_in_2_3_4'] })).toBe(true);
    expect(matchesNumeralFilter(item, { tiers: ['tier_1_ends_in_1'] })).toBe(false);
    expect(matchesNumeralFilter(item, { cefrLevels: ['A2', 'B1'] })).toBe(true);
    expect(matchesNumeralFilter(item, { cefrLevels: ['B2', 'C1'] })).toBe(false);
  });

  it('exposes comprehensive tier metadata for UI labels and tooltips', () => {
    expect(NUMERAL_TIER_META.tier_1_ends_in_1.ua).toBe('Закінчуються на 1');
    expect(NUMERAL_TIER_META.tier_2_ends_in_2_3_4.ua).toContain('2, 3, 4');
    expect(NUMERAL_TIER_META.tier_4_fractional.ua).toContain('півтора');
    expect(NUMERAL_TIER_META.tier_5_collective.ua).toContain('Збірні');
  });

  it('normalizes snake_case Python engine card output and generates feedback without error', () => {
    const rawPythonCard = {
      id: 'numeral-tier_2_ends_in_2_3_4-hromadianyn-2',
      tier: 'tier_2_ends_in_2_3_4',
      numeral_display: '2',
      numeral_words: 'два',
      lemma: 'громадянин',
      gender: 'm',
      is_anim: true,
      cefr_level: 'B1',
      target_case: 'родовий',
      target_number: 'singular',
      correct_form: 'громадянина',
      options: ['громадянина', 'громадяни', 'громадян', 'громадянин'],
      distractors: [
        {
          form: 'громадяни',
          interference_type: 'overgeneralized_plural',
          explanation_ua: 'Форма «громадяни» є називним відмінком множини.',
          explanation_en: "'громадяни' is Nominative plural.",
        },
        {
          form: 'громадян',
          interference_type: 'overgeneralized_plural',
          explanation_ua: 'Форма «громадян» — це родовий відмінок множини.',
          explanation_en: "'громадян' is Genitive plural.",
        },
        {
          form: 'громадянин',
          interference_type: 'nominative_singular_bias',
          explanation_ua: 'Початкова словникова форма не вживається.',
          explanation_en: 'Dictionary singular is not used.',
        },
      ],
      prompt_ua: '2 (громадянин) ➔ 2 …',
      prompt_en: 'Choose the correct form for: 2 (громадянин)',
      pedagogical_rule_ua: 'Іменники на -ин вживаються у формі родового відмінка однини.',
      pedagogical_rule_en: 'Nouns in -ин take Genitive singular.',
      pravopys_ref: 'Морфологія української мови (Волкова, Масло 2012, с. 91)',
    };

    const normalized = normalizeNumeralItem(rawPythonCard);
    expect(normalized.correctForm).toBe('громадянина');
    expect(normalized.numeralDisplay).toBe('2');
    expect(normalized.distractors).toHaveLength(3);
    expect(normalized.distractors[0].explanationUa).toBe('Форма «громадяни» є називним відмінком множини.');

    // Pipe raw python card directly into numeralFeedbackFor
    const feedbackCorrect = numeralFeedbackFor(rawPythonCard, 'громадянина');
    expect(feedbackCorrect.isCorrect).toBe(true);
    expect(feedbackCorrect.explanationUa).toContain('громадянина');

    const feedbackDistractor = numeralFeedbackFor(rawPythonCard, 'громадяни');
    expect(feedbackDistractor.isCorrect).toBe(false);
    expect(feedbackDistractor.interferenceType).toBe('overgeneralized_plural');
    expect(feedbackDistractor.explanationUa).toContain('називним відмінком');
  });
});
