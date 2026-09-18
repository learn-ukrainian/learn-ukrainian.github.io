/**
 * Ukrainian Numeral + Noun Agreement Model and Feedback Helpers.
 *
 * Grounded in Ukrainian Pravopys 2019 (§ 105–107) rules:
 * - Tier 1: Ends in 1 (except 11) -> Nominative singular (§ 105)
 * - Tier 2: Ends in 2, 3, 4 (except 12–14) -> Nominative plural (anti-calque focus; dropping -ин takes Gen Sg) (§ 105)
 * - Tier 3: 5–20, 30, and teens 11–14 -> Genitive plural (§ 105)
 * - Tier 4: Fractional (півтора / півтори / decimals) -> Genitive singular (§ 107)
 * - Tier 5: Collective (двоє, троє, четверо...) -> Genitive plural (§ 105)
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
 * Ingestion adapter that normalizes either camelCase or snake_case inputs
 * into a strongly typed PracticeNumeralItem.
 */
export function normalizeNumeralItem(raw: unknown): PracticeNumeralItem {
  if (!raw || typeof raw !== 'object') {
    throw new TypeError('Invalid numeral item: expected an object');
  }
  const r = raw as Record<string, any>;
  const rawDistractors = Array.isArray(r.distractors) ? r.distractors : [];
  const distractors: NumeralDistractor[] = rawDistractors.map((d: any) => ({
    form: String(d.form ?? ''),
    interferenceType: (d.interferenceType ?? d.interference_type ?? 'overgeneralized_plural') as InterferenceTypeKey,
    explanationUa: String(d.explanationUa ?? d.explanation_ua ?? ''),
    explanationEn: String(d.explanationEn ?? d.explanation_en ?? ''),
  }));

  return {
    id: String(r.id ?? ''),
    tier: (r.tier ?? 'tier_3_plural_5_plus') as NumeralTierKey,
    numeralDisplay: String(r.numeralDisplay ?? r.numeral_display ?? ''),
    numeralWords: String(r.numeralWords ?? r.numeral_words ?? ''),
    lemma: String(r.lemma ?? ''),
    gender: (r.gender ?? 'm') as 'm' | 'f' | 'n',
    isAnim: Boolean(r.isAnim ?? r.is_anim ?? false),
    cefrLevel: String(r.cefrLevel ?? r.cefr_level ?? 'A1'),
    targetCase: String(r.targetCase ?? r.target_case ?? ''),
    targetNumber: (r.targetNumber ?? r.target_number ?? 'singular') as 'singular' | 'plural',
    correctForm: String(r.correctForm ?? r.correct_form ?? ''),
    options: Array.isArray(r.options) ? r.options.map(String) : [],
    distractors,
    promptUa: String(r.promptUa ?? r.prompt_ua ?? ''),
    promptEn: String(r.promptEn ?? r.prompt_en ?? ''),
    pedagogicalRuleUa: String(r.pedagogicalRuleUa ?? r.pedagogical_rule_ua ?? ''),
    pedagogicalRuleEn: String(r.pedagogicalRuleEn ?? r.pedagogical_rule_en ?? ''),
    pravopysRef: String(r.pravopysRef ?? r.pravopys_ref ?? 'Правопис 2019, § 105–107'),
  };
}

/**
 * Generate targeted pedagogical feedback for a user's selection on a numeral card.
 * Accepts either strongly-typed PracticeNumeralItem or raw JSON cards from Python engine.
 */
export function numeralFeedbackFor(
  item: PracticeNumeralItem | Record<string, any>,
  selectedOption: string,
): NumeralFeedback {
  const normItem = normalizeNumeralItem(item);
  const normSelected = (selectedOption ?? '').trim().toLowerCase();
  const normCorrect = normItem.correctForm.trim().toLowerCase();

  if (normSelected === normCorrect) {
    return {
      isCorrect: true,
      explanationUa: `Правильно! «${normItem.numeralDisplay} ${normItem.correctForm}» — правильна форма (${normItem.targetCase} відмінок ${normItem.targetNumber === 'singular' ? 'однини' : 'множини'}).`,
      explanationEn: `Correct! '${normItem.numeralDisplay} ${normItem.correctForm}' is the correct form (${normItem.targetCase} ${normItem.targetNumber}).`,
      ruleUa: normItem.pedagogicalRuleUa,
      ruleEn: normItem.pedagogicalRuleEn,
    };
  }

  // Look for specific distractor explanation
  const distractor = normItem.distractors.find((d) => (d.form ?? '').trim().toLowerCase() === normSelected);

  if (distractor) {
    return {
      isCorrect: false,
      explanationUa: distractor.explanationUa,
      explanationEn: distractor.explanationEn,
      ruleUa: normItem.pedagogicalRuleUa,
      ruleEn: normItem.pedagogicalRuleEn,
      interferenceType: distractor.interferenceType,
    };
  }

  // Generic fallback feedback
  return {
    isCorrect: false,
    explanationUa: `Неправильно. Для «${normItem.numeralDisplay} (${normItem.lemma})» правильною є форма «${normItem.correctForm}».`,
    explanationEn: `Incorrect. For '${normItem.numeralDisplay} (${normItem.lemma})', the correct form is '${normItem.correctForm}'.`,
    ruleUa: normItem.pedagogicalRuleUa,
    ruleEn: normItem.pedagogicalRuleEn,
  };
}

/**
 * Filter items by numeral tier and CEFR level.
 */
export function matchesNumeralFilter(
  item: PracticeNumeralItem | Record<string, any>,
  filter: NumeralFilter,
): boolean {
  const normItem = normalizeNumeralItem(item);
  if (filter.tiers && filter.tiers.length > 0) {
    if (!filter.tiers.includes(normItem.tier)) {
      return false;
    }
  }
  if (filter.cefrLevels && filter.cefrLevels.length > 0) {
    if (!filter.cefrLevels.includes(normItem.cefrLevel)) {
      return false;
    }
  }
  return true;
}
