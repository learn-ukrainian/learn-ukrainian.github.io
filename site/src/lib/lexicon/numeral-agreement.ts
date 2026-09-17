/**
 * Ukrainian Numeral + Noun Agreement Model and Feedback Helpers.
 *
 * Grounded in Ukrainian Pravopys 2019 (§ 108–111) rules:
 * - Tier 1: Ends in 1 (except 11) -> Nominative singular
 * - Tier 2: Ends in 2, 3, 4 (except 12–14) -> Nominative plural (anti-calque focus)
 * - Tier 3: 5–20, 30, and teens 11–14 -> Genitive plural
 * - Tier 4: Fractional (півтора / півтори / decimals) -> Genitive singular
 * - Tier 5: Collective (двоє, троє, четверо...) -> Genitive plural
 */

export type NumeralTierKey =
  | 'tier_1_ends_in_1'
  | 'tier_2_ends_in_2_3_4'
  | 'tier_3_plural_5_plus'
  | 'tier_4_fractional'
  | 'tier_5_collective';

export type InterferenceTypeKey =
  | 'russianism_calque'
  | 'teen_tier_violation'
  | 'compound_last_word_misagreement'
  | 'nominative_singular_bias'
  | 'collective_case_violation'
  | 'fractional_case_violation'
  | 'oblique_plural_confusion'
  | 'overgeneralized_plural';

export interface NumeralDistractor {
  form: string;
  interferenceType: InterferenceTypeKey;
  explanationUa: string;
  explanationEn: string;
}

export interface PracticeNumeralItem {
  id: string;
  tier: NumeralTierKey;
  numeralDisplay: string;
  numeralWords: string;
  lemma: string;
  gender: 'm' | 'f' | 'n';
  isAnim: boolean;
  cefrLevel: string;
  targetCase: string;
  targetNumber: 'singular' | 'plural';
  correctForm: string;
  options: string[];
  distractors: NumeralDistractor[];
  promptUa: string;
  promptEn: string;
  pedagogicalRuleUa: string;
  pedagogicalRuleEn: string;
  pravopysRef: string;
}

export interface NumeralFeedback {
  isCorrect: boolean;
  explanationUa: string;
  explanationEn: string;
  ruleUa: string;
  ruleEn: string;
  interferenceType?: InterferenceTypeKey;
}

export interface NumeralFilter {
  tiers?: NumeralTierKey[];
  cefrLevels?: string[];
}

export const NUMERAL_TIER_META: Record<
  NumeralTierKey,
  { ua: string; en: string; descriptionUa: string; descriptionEn: string }
> = {
  tier_1_ends_in_1: {
    ua: 'Закінчуються на 1',
    en: 'Ends in 1',
    descriptionUa: '1, 21, 31... вимагають називного відмінка однини',
    descriptionEn: '1, 21, 31... govern Nominative singular',
  },
  tier_2_ends_in_2_3_4: {
    ua: '2, 3, 4 (паукальні)',
    en: '2, 3, 4 (Paucal)',
    descriptionUa: '2, 3, 4 вимагають називного відмінка множини (не родового однини!)',
    descriptionEn: '2, 3, 4 govern Nominative plural (anti-calque)',
  },
  tier_3_plural_5_plus: {
    ua: '5+ та 11–14',
    en: '5+ and teens 11–14',
    descriptionUa: '5–20, 30, 11–14 вимагають родового відмінка множини',
    descriptionEn: '5–20, 30, teens 11–14 govern Genitive plural',
  },
  tier_4_fractional: {
    ua: 'Дробові (півтора / півтори)',
    en: 'Fractions (півтора / півтори)',
    descriptionUa: 'Півтора / півтори керують родовим відмінком однини',
    descriptionEn: 'Півтора / півтори govern Genitive singular',
  },
  tier_5_collective: {
    ua: 'Збірні (двоє, троє...)',
    en: 'Collective numerals',
    descriptionUa: 'Двоє, троє... сполучаються з родовим множини (чол. істоти та сер. рід)',
    descriptionEn: 'Двоє, троє... govern Genitive plural with animates & neuters',
  },
};

/**
 * Classify a numeral value or string into its agreement tier.
 */
export function classifyNumeralTier(value: number | string): NumeralTierKey {
  if (typeof value === 'string') {
    const s = value.trim().toLowerCase();
    if (s === 'півтора' || s === 'півтори' || s.includes('.')) {
      return 'tier_4_fractional';
    }
    if (
      s === 'двоє' ||
      s === 'троє' ||
      s === 'четверо' ||
      s === "п'ятеро" ||
      s === 'шестеро' ||
      s === 'семеро' ||
      s === 'восьмеро' ||
      s === "дев'ятеро" ||
      s === 'десятеро'
    ) {
      return 'tier_5_collective';
    }
    const parsed = parseInt(s, 10);
    if (!Number.isNaN(parsed)) {
      return classifyNumeralTier(parsed);
    }
    return 'tier_3_plural_5_plus';
  }

  if (!Number.isInteger(value)) {
    return 'tier_4_fractional';
  }

  const v = Math.abs(value);
  const lastTwo = v % 100;
  const lastOne = v % 10;

  if (lastTwo >= 11 && lastTwo <= 14) {
    return 'tier_3_plural_5_plus';
  }
  if (lastOne === 1) {
    return 'tier_1_ends_in_1';
  }
  if (lastOne >= 2 && lastOne <= 4) {
    return 'tier_2_ends_in_2_3_4';
  }
  return 'tier_3_plural_5_plus';
}

/**
 * Generate targeted pedagogical feedback for a user's selection on a numeral card.
 */
export function numeralFeedbackFor(
  item: PracticeNumeralItem,
  selectedOption: string,
): NumeralFeedback {
  const normSelected = selectedOption.trim().toLowerCase();
  const normCorrect = item.correctForm.trim().toLowerCase();

  if (normSelected === normCorrect) {
    return {
      isCorrect: true,
      explanationUa: `Правильно! «${item.numeralDisplay} ${item.correctForm}» — правильна форма (${item.targetCase} відмінок ${item.targetNumber === 'singular' ? 'однини' : 'множини'}).`,
      explanationEn: `Correct! '${item.numeralDisplay} ${item.correctForm}' is the correct form (${item.targetCase} ${item.targetNumber}).`,
      ruleUa: item.pedagogicalRuleUa,
      ruleEn: item.pedagogicalRuleEn,
    };
  }

  // Look for specific distractor explanation
  const distractor = item.distractors.find((d) => d.form.trim().toLowerCase() === normSelected);

  if (distractor) {
    return {
      isCorrect: false,
      explanationUa: distractor.explanationUa,
      explanationEn: distractor.explanationEn,
      ruleUa: item.pedagogicalRuleUa,
      ruleEn: item.pedagogicalRuleEn,
      interferenceType: distractor.interferenceType,
    };
  }

  // Generic fallback feedback
  return {
    isCorrect: false,
    explanationUa: `Неправильно. Для «${item.numeralDisplay} (${item.lemma})» правильною є форма «${item.correctForm}».`,
    explanationEn: `Incorrect. For '${item.numeralDisplay} (${item.lemma})', the correct form is '${item.correctForm}'.`,
    ruleUa: item.pedagogicalRuleUa,
    ruleEn: item.pedagogicalRuleEn,
  };
}

/**
 * Filter items by numeral tier and CEFR level.
 */
export function matchesNumeralFilter(item: PracticeNumeralItem, filter: NumeralFilter): boolean {
  if (filter.tiers && filter.tiers.length > 0) {
    if (!filter.tiers.includes(item.tier)) {
      return false;
    }
  }
  if (filter.cefrLevels && filter.cefrLevels.length > 0) {
    if (!filter.cefrLevels.includes(item.cefrLevel)) {
      return false;
    }
  }
  return true;
}
