/**
 * Ukrainian Numeral Deep Mechanics Practice Engine (Числівник).
 *
 * Implements Ukrainian Pravopys 2019 (§§ 105–107) and Academic Grammar rules for:
 *   1. Decades 50–80 Inflection (§ 105.4):
 *      - Only the second root declines (-десят -> -десяти/-десятьох, -десятьма/-десятьома)
 *      - The first root remains invariant (п'ят-, шіст-, сім-, вісім-)
 *      - Anti-calques: *п'ятидесяти* ❌ -> п'ятдесяти ✅, *шестидесятьма* ❌ -> шістдесятьма ✅
 *   2. Hundreds 200–900 Declension (§ 105.5):
 *      - Both roots decline:
 *        * Genitive: двохсот, трьохсот, п'ятисот, шестисот (anti-calque: *п'ятиста* ❌)
 *        * Dative: двомстам, трьомстам, п'ятистам (ending -стам)
 *        * Instrumental: двомастами, трьомастами, чотирмастами, п'ятьмастами (ending -стами; anti-calque: *п'ятистами* ❌)
 *        * Locative: на двохстах, на трьохстах, на чотирьохстах, на п'ятистах (ending -стах)
 *   3. Paradigms 40, 90, 100 (§ 105.7):
 *      - Only two forms: -о in Nom/Acc (сорок, дев'яносто, сто) and -а in all oblique cases (сорока, дев'яноста, ста)
 *   4. Numeral + Noun Case Government:
 *      - 2, 3, 4 govern Nominative plural: два брати, три олівці, чотири студенти (anti-calque *два брата* ❌)
 *      - 5+ govern Genitive plural: п'ять братів, десять рулонів
 *      - Compound numerals: government is determined strictly by the last numeral (двадцять один день, двадцять два дні, двадцять п'ять днів)
 *   5. Collective Numerals (§ 105.6):
 *      - двоє, троє, четверо... combine with male animates (двоє братів), pluralia tantum (двоє дверей, троє ножиць), and young beings (четверо каченят)
 *      - Strictly inadmissible with adult female persons (*двоє жінок* ❌ -> дві жінки ✅)
 *   6. Fractional Numerals (§ 107):
 *      - півтора (masc/neut) vs півтори (fem); govern Genitive singular (півтора року, півтори доби, півтора місяця)
 *   7. Ordinal Compound Declension (§ 106.2):
 *      - Only the last word declines: у дві тисячі двадцять четвертому році (not *у двох тисячах* ❌)
 *   8. Authentic Time & Approximate Quantity Constructions:
 *      - о десятій годині, чверть на одинадцяту, пів на дванадцяту, за двадцять третя
 *      - Approximation via inversion (років п'ять, хвилин двадцять) or prepositions (близько ста, понад двісті, з десяток; not *біля ста* ❌)
 */

export const NUMERAL_MECHANICS_CATEGORY_KEYS = [
  'cardinal_50_80_inflection',
  'cardinal_200_900_genitive',
  'cardinal_200_900_dative_locative',
  'cardinal_200_900_instrumental',
  'cardinal_40_90_100_paradigm',
  'government_2_3_4_nominative_plural',
  'government_5_plus_genitive_plural',
  'government_compound_last_digit',
  'collective_masculine_animate',
  'collective_restriction_feminine',
  'collective_pluralia_tantum_neuter',
  'fractional_pivtora_government',
  'ordinal_compound_declension',
  'time_expressions_anti_calque',
  'approximate_numerical_constructions',
] as const;

export type NumeralMechanicsCategoryKey = (typeof NUMERAL_MECHANICS_CATEGORY_KEYS)[number];

export const NUMERAL_MECHANICS_INTERFERENCE_KEYS = [
  'inflected_first_root_50_80',
  'uninflected_base_form',
  'corrupted_ending_200_900',
  'russianism_genitive_hundreds',
  'russianism_instrumental_hundreds',
  'case_confusion_dative_locative',
  'wrong_stem_40_90_100',
  'russianism_genitive_singular_calque',
  'wrong_case_government_5_plus',
  'compound_global_misagreement',
  'collective_with_adult_female',
  'cardinal_with_pluralia_tantum',
  'fractional_plural_government',
  'fractional_gender_mismatch',
  'declining_previous_ordinal_components',
  'time_expression_russian_calque',
  'improper_approximation_preposition',
] as const;

export type NumeralMechanicsInterferenceKey = (typeof NUMERAL_MECHANICS_INTERFERENCE_KEYS)[number];

export interface NumeralMechanicsDistractor {
  text: string;
  interference_type: NumeralMechanicsInterferenceKey;
  explanation: {
    ua: string;
    en: string;
  };
}

export interface PracticeNumeralMechanicsCard {
  card_id: string;
  category: NumeralMechanicsCategoryKey;
  cefr_level: string;
  prompt_sentence: string;
  blank_target: string;
  correct_answer: string;
  options: string[];
  distractors: NumeralMechanicsDistractor[];
  pravopys_section: string;
  rule_summary: {
    ua: string;
    en: string;
  };
}

export interface NumeralMechanicsDeckPayload {
  schema_version: string;
  title: string;
  card_count: number;
  categories: NumeralMechanicsCategoryKey[];
  cards: PracticeNumeralMechanicsCard[];
}

export interface NumeralMechanicsEvaluation {
  isCorrect: boolean;
  selectedOption: string;
  correctAnswer: string;
  feedbackUa: string;
  feedbackEn: string;
  ruleCitation: string;
  misconceptionType?: NumeralMechanicsInterferenceKey;
}

/**
 * Evaluates learner choice for numeral mechanics card and provides bilingual feedback.
 */
export function numeralMechanicsFeedbackFor(
  card: PracticeNumeralMechanicsCard,
  selectedOption: string,
): NumeralMechanicsEvaluation {
  const normalizedSelection = selectedOption.trim();
  const normalizedTarget = card.correct_answer.trim();

  if (normalizedSelection === normalizedTarget) {
    return {
      isCorrect: true,
      selectedOption: card.correct_answer,
      correctAnswer: card.correct_answer,
      feedbackUa: `Чудово! Правильно: «${card.correct_answer}». ${card.rule_summary.ua}`,
      feedbackEn: `Excellent! Correct: "${card.correct_answer}". ${card.rule_summary.en}`,
      ruleCitation: card.pravopys_section,
    };
  }

  const matchedDistractor = card.distractors.find((d) => d.text.trim() === normalizedSelection);

  if (matchedDistractor) {
    return {
      isCorrect: false,
      selectedOption: matchedDistractor.text,
      correctAnswer: card.correct_answer,
      feedbackUa: `Неправильно: «${matchedDistractor.text}». ${matchedDistractor.explanation.ua} Правильна форма: «${card.correct_answer}».`,
      feedbackEn: `Incorrect: "${matchedDistractor.text}". ${matchedDistractor.explanation.en} Correct form: "${card.correct_answer}".`,
      ruleCitation: card.pravopys_section,
      misconceptionType: matchedDistractor.interference_type,
    };
  }

  return {
    isCorrect: false,
    selectedOption: selectedOption,
    correctAnswer: card.correct_answer,
    feedbackUa: `Неправильно. Правильна форма: «${card.correct_answer}». ${card.rule_summary.ua}`,
    feedbackEn: `Incorrect. Correct form: "${card.correct_answer}". ${card.rule_summary.en}`,
    ruleCitation: card.pravopys_section,
  };
}

/**
 * Checks if a given number ending governs Nominative plural (2, 3, 4 paucal tier).
 */
export function isPaucalTierEnding(numeralValue: number): boolean {
  const mod100 = numeralValue % 100;
  const mod10 = numeralValue % 10;
  if (mod100 >= 11 && mod100 <= 14) {
    return false;
  }
  return mod10 >= 2 && mod10 <= 4;
}

/**
 * Checks if a given number ending governs Genitive plural (5+ tier or 11–14).
 */
export function isGenitivePluralTierEnding(numeralValue: number): boolean {
  const mod100 = numeralValue % 100;
  const mod10 = numeralValue % 10;
  if (mod100 >= 11 && mod100 <= 14) {
    return true;
  }
  return mod10 === 0 || mod10 >= 5;
}

export interface NumeralRuleResolution {
  citation: string;
  ruleUa: string;
  ruleEn: string;
}

export function resolveCardinal5080Rule(): NumeralRuleResolution {
  return {
    citation: 'Правопис 2019 § 105.4',
    ruleUa:
      "У числівниках на позначення десятків 50–80 (п'ятдесят — вісімдесят) відмінюється лише друга частина (-десят); перша частина ніколи не змінюється: п'ятдесяти (не *п'ятидесяти*), шістдесятьма (не *шестидесятьма*).",
    ruleEn:
      "In numerals 50–80 (п'ятдесят — вісімдесят), only the second root declines (-десят); the first root remains invariant: п'ятдесяти (not *п'ятидесяти*), шістдесятьма (not *шестидесятьма*).",
  };
}

export function resolveCardinal200900GenitiveRule(): NumeralRuleResolution {
  return {
    citation: 'Правопис 2019 § 105.5',
    ruleUa:
      "У числівниках на позначення сотень 200–900 у родовому відмінку відмінюються обидві частини, і друга частина має закінчення -сот: двохсот, трьохсот, чотирьохсот, п'ятисот, шестисот (не *п'ятиста*).",
    ruleEn:
      "In numerals 200–900 in the Genitive case, both roots decline and the second root ends in -сот: двохсот, трьохсот, п'ятисот, шестисот (not *п'ятиста*).",
  };
}

export function resolveCardinal200900DativeLocativeRule(): NumeralRuleResolution {
  return {
    citation: 'Правопис 2019 § 105.5',
    ruleUa:
      "У давальному відмінку числівники 200–900 мають закінчення -стам (двомстам, трьомстам, п'ятистам), а в місцевому — -стах (на двохстах, на трьохстах, на п'ятистах).",
    ruleEn:
      "In the Dative case, numerals 200–900 end in -стам (двомстам, п'ятистам); in the Locative case, they end in -стах (на двохстах, на п'ятистах).",
  };
}

export function resolveCardinal200900InstrumentalRule(): NumeralRuleResolution {
  return {
    citation: 'Правопис 2019 § 105.5',
    ruleUa:
      "В орудному відмінку числівники 200–900 мають закінчення -стами: двомастами, трьомастами, чотирмастами, п'ятьмастами (не *п'ятистами*).",
    ruleEn:
      "In the Instrumental case, numerals 200–900 end in -стами: двомастами, трьомастами, чотирмастами, п'ятьмастами (not *п'ятистами*).",
  };
}

export function resolveCardinal4090100Rule(): NumeralRuleResolution {
  return {
    citation: 'Правопис 2019 § 105.7',
    ruleUa:
      "Числівники сорок, дев'яносто, сто мають лише дві форми: закінчення -о в називному й знахідному відмінках та закінчення -а в усіх непрямих відмінках (сорока, дев'яноста, ста).",
    ruleEn:
      "Numerals сорок, дев'яносто, сто have only two forms: ending -о in Nominative/Accusative and ending -а in all oblique cases (сорока, дев'яноста, ста).",
  };
}

export function resolveGovernment234Rule(): NumeralRuleResolution {
  return {
    citation: 'Синтаксичні норми української мови / Правопис 2019',
    ruleUa:
      'Числівники два, три, чотири керують іменниками у формі називного відмінка множини: два брати, три олівці, чотири студенти (калька родового відмінка *два брата* неприпустима).',
    ruleEn:
      'Numerals два, три, чотири govern nouns in the Nominative plural: два брати, три олівці, чотири студенти (calque *два брата* is incorrect).',
  };
}

export function resolveGovernment5PlusRule(): NumeralRuleResolution {
  return {
    citation: 'Синтаксичні норми української мови',
    ruleUa:
      "Числівники від п'яти й більше (п'ять, шість, десять, двадцять тощо) у називному відмінку керують іменниками у формі родового відмінка множини: п'ять братів, десять рулонів, сім книжок.",
    ruleEn:
      "Numerals from five onwards (п'ять, шість, десять...) in the Nominative govern nouns in the Genitive plural: п'ять братів, десять рулонів, сім книжок.",
  };
}

export function resolveGovernmentCompoundLastDigitRule(): NumeralRuleResolution {
  return {
    citation: 'Синтаксичні норми української мови',
    ruleUa:
      "У складених числівниках форма іменника визначається винятково останнім словом: на один — називний однини (двадцять один день), на два, три, чотири — називний множини (тридцять два дні), на п'ять і більше — родовий множини (сорок п'ять днів).",
    ruleEn:
      'In compound numerals, noun agreement is determined strictly by the last numeral: ending in один -> Nom sing, ending in два/три/чотири -> Nom plur, ending in 5+ -> Gen plur.',
  };
}

export function resolveCollectiveMasculineRule(): NumeralRuleResolution {
  return {
    citation: 'Правопис 2019 § 105.6',
    ruleUa:
      "Збірні числівники (двоє, троє, четверо, п'ятеро тощо) природно вживаються з іменниками чоловічого роду — назвами осіб: двоє братів, троє друзів, четверо хлопців.",
    ruleEn:
      'Collective numerals (двоє, троє, четверо...) naturally combine with masculine animate nouns denoting persons: двоє братів, троє друзів, четверо хлопців.',
  };
}

export function resolveCollectiveFeminineRestrictionRule(): NumeralRuleResolution {
  return {
    citation: 'Правопис 2019 § 105.6',
    ruleUa:
      'Збірні числівники НЕ вживаються з іменниками жіночого роду на позначення дорослих осіб: вживаються лише власне кількісні числівники — дві жінки (не *двоє жінок*), три сестри (не *троє сестер*).',
    ruleEn:
      'Collective numerals are NOT used with feminine nouns denoting adult persons: only cardinal numerals are admissible — дві жінки (not *двоє жінок*), три сестри (not *троє сестер*).',
  };
}

export function resolveCollectivePluraliaNeuterRule(): NumeralRuleResolution {
  return {
    citation: 'Правопис 2019 § 105.6',
    ruleUa:
      "Збірні числівники обов'язково вживаються з іменниками, що мають лише форму множини (pluralia tantum: двоє дверей, троє ножиць, двоє саней), а також із назвами малят (четверо каченят).",
    ruleEn:
      'Collective numerals are mandatory with pluralia tantum nouns (двоє дверей, троє ножиць, двоє саней) and neuter nouns denoting young animals/beings (четверо каченят).',
  };
}

export function resolveFractionalPivtoraRule(): NumeralRuleResolution {
  return {
    citation: 'Правопис 2019 § 107',
    ruleUa:
      'Дробові числівники півтора (для чоловічого та середнього роду) і півтори (для жіночого роду) завжди керують іменниками у формі родового відмінка ОДНИНИ: півтора року, півтори доби, півтора місяця.',
    ruleEn:
      'Fractional numerals півтора (masc/neut) and півтори (fem) always govern nouns in the Genitive SINGULAR: півтора року, півтори доби, півтора місяця.',
  };
}

export function resolveOrdinalCompoundDeclensionRule(): NumeralRuleResolution {
  return {
    citation: 'Правопис 2019 § 106.2',
    ruleUa:
      'У складених порядкових числівниках відмінюється ЛИШЕ ОСТАННЄ слово; усі попередні слова зберігають початкову форму називного відмінка: у дві тисячі двадцять четвертому році (не *у двох тисячах*).',
    ruleEn:
      'In compound ordinal numerals, ONLY the last word inflects; all preceding words remain in the Nominative: у дві тисячі двадцять четвертому році (not *у двох тисячах*).',
  };
}

export function resolveTimeExpressionsRule(): NumeralRuleResolution {
  return {
    citation: 'Культура мовлення / Автентичні синтаксичні норми',
    ruleUa:
      "Для позначення точного часу в українській мові вживають прийменник 'о' / 'об' із порядковим числівником (о десятій годині), форми 'чверть на одинадцяту', 'пів на дванадцяту', 'за двадцять третя' (кальки *в десять годин*, *без двадцяти* неприпустимі).",
    ruleEn:
      "Authentic Ukrainian time expressions use 'о' + ordinal numeral (о десятій годині), 'чверть на одинадцяту', 'пів на дванадцяту', 'за двадцять третя' (calques *в десять годин*, *без двадцяти* are errors).",
  };
}

export function resolveApproximateConstructionsRule(): NumeralRuleResolution {
  return {
    citation: 'Культура мовлення / Синтаксис',
    ruleUa:
      "Приблизну кількість в українській мові позначають інверсією іменника й числівника (років п'ять, хвилин двадцять) або прийменниками близько, понад, з (близько ста; прийменник 'біля' позначає просторову близькість, а не кількість).",
    ruleEn:
      "Approximate quantities in Ukrainian are expressed via noun-numeral inversion (років п'ять, хвилин двадцять) or prepositions близько, понад, з (близько ста; 'біля' denotes physical proximity, not quantity).",
  };
}
