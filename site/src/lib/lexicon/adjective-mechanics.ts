/**
 * Ukrainian Adjective Deep Mechanics Practice Engine (Прикметник).
 *
 * Implements Ukrainian Pravopys 2019 (§§ 22, 106–114) and Academic Grammar rules for:
 *   1. Degrees of Comparison (Ступені порівняння прикметників) [§§ 110–113]:
 *      - Simple synthetic comparative (-іш- vs -ш- with root consonant alternations) [§ 110]:
 *        * г, ж, з + -ш- -> -жч- (дорожчий, нижчий, ближчий, вужчий, важчий)
 *        * к, с + -ш- -> -щ- (вищий, товщий, кращий)
 *        * standard suffix -іш- (новіший, тепліший, розумніший)
 *      - Suppletive comparative stems (великий -> більший, малий -> менший, поганий -> гірший)
 *      - Compound analytic comparative: більш / менш + positive form (більш зручний, not *більш зручніший)
 *      - Superlative (Найвищий ступінь) [§ 111]:
 *        * Simple synthetic: prefix най- + comparative (найкращий, найвищий; anti-calque: *самий кращий)
 *        * Emphatic prefixes: якнай-, щонай- (якнайшвидший, щонайкращий)
 *        * Compound analytic: найбільш / найменш + positive base form
 *      - Uncomparable adjectives (absolute qualities, materials, time: дерев'яний, босий, сліпий, вчорашній)
 *   2. Declension Groups: Hard vs Soft (Тверда та м'яка групи прикметників) [§§ 106–109]:
 *      - High-error focus: masculine/neuter soft instrumental singular ending is strictly -ім
 *        (синім, літнім, осіннім, раннім, давнім, крайнім), NOT *-им*.
 *      - Soft Genitive/Dative: -ього / -ьому (синього, літнього, давнього).
 *   3. Possessive Adjectives & Morphophonemic Suffixation [§§ 22, 107]:
 *      - Suffix -ів (-ова, -еве) from II declension nouns (батьків, Шевченків, Василів).
 *      - Suffix -ин (-ина, -ине) with historical alternations:
 *        * г -> ж: Ольга -> Ольжин
 *        * к -> ч: дочка -> доччин, тітка -> тітчин
 *        * х -> ш: Солоха -> Солошин, мачуха -> мачушин
 *      - Derivational suffixes -ськ-, -цьк-, -зьк- (§ 22):
 *        * г, ж, з + -ськ- -> -зьк- (Прага -> празький)
 *        * к, ч, ц + -ськ- -> -цьк- (козак -> козацький)
 *        * х, ш, с + -ськ- -> -ськ- (чех -> чеський)
 */

export const ADJECTIVE_MECHANICS_CATEGORY_KEYS = [
  'comp_synthetic_mutation_zhch',
  'comp_synthetic_mutation_shch',
  'comp_synthetic_sh_dropping_k',
  'comp_synthetic_ish',
  'comp_suppletive',
  'comp_analytic_formation',
  'super_synthetic_prefix',
  'super_emphatic_prefix',
  'decl_soft_instrumental_im',
  'decl_soft_genitive_dative',
  'possessive_iv_declension',
  'possessive_yn_mutation',
  'suffix_derivation_mutation',
  'anti_calque_uncomparable',
] as const;

export type AdjectiveMechanicsCategoryKey = (typeof ADJECTIVE_MECHANICS_CATEGORY_KEYS)[number];

export const ADJECTIVE_MECHANICS_INTERFERENCE_KEYS = [
  'false_synthetic_missing_mutation',
  'false_sh_dropping_k_missing_drop',
  'false_comparative_ish_for_sh',
  'false_comparative_sh_for_ish',
  'false_suppletive_regularized',
  'false_double_comparative',
  'russian_calque_samyi',
  'false_superlative_prefix_separated',
  'false_superlative_analytic_double',
  'false_soft_instrumental_ym',
  'false_soft_genitive_hard_ending',
  'false_soft_dative_hard_ending',
  'false_possessive_missing_mutation',
  'false_possessive_iv_suffix_vowel',
  'false_derivation_missing_mutation',
  'false_comparison_of_uncomparable',
  'false_relational_for_possessive',
] as const;

export type AdjectiveMechanicsInterferenceKey =
  (typeof ADJECTIVE_MECHANICS_INTERFERENCE_KEYS)[number];

export interface AdjectiveMechanicsDistractor {
  text: string;
  interference_type: AdjectiveMechanicsInterferenceKey;
  explanation: {
    ua: string;
    en: string;
  };
}

export interface PracticeAdjectiveMechanicsCard {
  card_id: string;
  category: AdjectiveMechanicsCategoryKey;
  cefr_level: string;
  prompt_sentence: string;
  blank_target: string;
  correct_answer: string;
  options: string[];
  distractors: AdjectiveMechanicsDistractor[];
  pravopys_section: string;
  rule_summary: {
    ua: string;
    en: string;
  };
}

export interface AdjectiveMechanicsDeckPayload {
  version: string;
  title: string;
  description: string;
  card_count: number;
  cards: PracticeAdjectiveMechanicsCard[];
}

export interface AdjectiveMechanicsFeedbackResult {
  isCorrect: boolean;
  feedback: string;
  pravopysSection: string;
  ruleSummary: string;
}

/**
 * Evaluates learner selection against card expectations and produces targeted pedagogical feedback.
 */
export function adjectiveMechanicsFeedbackFor(
  card: PracticeAdjectiveMechanicsCard,
  selectedOption: string,
  locale: 'ua' | 'en' = 'ua',
): AdjectiveMechanicsFeedbackResult {
  const normSelected = selectedOption.trim();
  const normCorrect = card.correct_answer.trim();

  if (normSelected === normCorrect) {
    const successMsg =
      locale === 'ua'
        ? `Правильно! ${card.rule_summary.ua}`
        : `Correct! ${card.rule_summary.en}`;
    return {
      isCorrect: true,
      feedback: successMsg,
      pravopysSection: card.pravopys_section,
      ruleSummary: locale === 'ua' ? card.rule_summary.ua : card.rule_summary.en,
    };
  }

  const matchedDistractor = card.distractors.find((d) => d.text.trim() === normSelected);
  if (matchedDistractor) {
    const explanation =
      locale === 'ua'
        ? matchedDistractor.explanation.ua
        : matchedDistractor.explanation.en;
    return {
      isCorrect: false,
      feedback: explanation,
      pravopysSection: card.pravopys_section,
      ruleSummary: locale === 'ua' ? card.rule_summary.ua : card.rule_summary.en,
    };
  }

  const fallback =
    locale === 'ua'
      ? `Неправильно. Правильна форма: «${card.correct_answer}». ${card.rule_summary.ua}`
      : `Incorrect. The correct form is "${card.correct_answer}". ${card.rule_summary.en}`;

  return {
    isCorrect: false,
    feedback: fallback,
    pravopysSection: card.pravopys_section,
    ruleSummary: locale === 'ua' ? card.rule_summary.ua : card.rule_summary.en,
  };
}

/**
 * Resolves degree of comparison rule per Правопис 2019 §§ 110, 111.
 */
export function resolveDegreeComparisonRule(
  category: AdjectiveMechanicsCategoryKey,
): { indicator: string; ruleUa: string; ruleEn: string } {
  switch (category) {
    case 'comp_synthetic_mutation_zhch':
      return {
        indicator: '-жч-',
        ruleUa:
          'При творенні вищого ступеня приголосні г, ж, з разом із суфіксом -ш- переходять у -жч- (Правопис 2019 § 110, п. 1 б: дорожчий, ближчий, вужчий).',
        ruleEn:
          'In comparative formation, stems ending in h, zh, z fuse with suffix -sh- to form -zhch- (Pravopys 2019 § 110, item 1 b: dorozhchyi, blyzhchyi, vuzhchyi).',
      };
    case 'comp_synthetic_mutation_shch':
      return {
        indicator: '-щ-',
        ruleUa:
          'При творенні вищого ступеня приголосні к, с разом із суфіксом -ш- переходять у -щ- (Правопис 2019 § 110, п. 1 б: вищий, товщий, кращий).',
        ruleEn:
          'In comparative formation, stems ending in k, s fuse with suffix -sh- to form -shch- (Pravopys 2019 § 110, item 1 b: vyshchyi, tovshchyi).',
      };
    case 'comp_synthetic_sh_dropping_k':
      return {
        indicator: '-ш- (випадання -к-/-ок-)',
        ruleUa:
          'При творенні вищого ступеня за допомогою суфікса -ш- суфікси -к-, -ок- випадають (Правопис 2019 § 110, п. 1 а: швидкий -> швидший, широкий -> ширший, глибокий -> глибший, короткий -> коротший).',
        ruleEn:
          'When forming the comparative with suffix -sh-, suffixes -k- and -ok- drop (Pravopys 2019 § 110, item 1 a: shvydkyi -> shvydshyi, shyrokyi -> shyrshyi, hlybokyi -> hlybshyi).',
      };
    case 'comp_synthetic_ish':
      return {
        indicator: '-іш-',
        ruleUa:
          'Більшість якісних прикметників утворюють вищий ступінь за допомогою суфікса -іш- (Правопис 2019 § 110, п. 1 а: новіший, тепліший, розумніший).',
        ruleEn:
          'Most qualitative adjectives form the comparative with suffix -ish- (Pravopys 2019 § 110, item 1 a: novishyi, teplishyi).',
      };
    case 'comp_suppletive':
      return {
        indicator: 'Суплетивна основа',
        ruleUa:
          'Деякі якісні прикметники утворюють ступені від інших основ (Правопис 2019 § 110, п. 1 в: великий -> більший, малий -> менший, поганий -> гірший, добрий -> кращий).',
        ruleEn:
          'Suppletive adjectives use entirely different stems for comparison (Pravopys 2019 § 110, item 1 c: velykyi -> bilshyi, malyi -> menshyi).',
      };
    case 'comp_analytic_formation':
      return {
        indicator: 'більш / менш + звичайна форма',
        ruleUa:
          'Складена форма вищого ступеня утворюється сполученням слів «більш / менш» із початковою формою (Правопис 2019 § 110, п. 2: більш зручний, не *більш зручніший).',
        ruleEn:
          'Analytic comparatives are formed by adding "bilsh / mensh" to the positive base adjective (Pravopys 2019 § 110, item 2).',
      };
    case 'super_synthetic_prefix':
      return {
        indicator: 'най- + вищий ступінь',
        ruleUa:
          'Найвищий ступінь утворюється додаванням префікса най- до форми вищого ступеня (Правопис 2019 § 111, п. 1: найкращий, найвищий; ніколи не *самий кращий).',
        ruleEn:
          'Synthetic superlatives add prefix nay- to the comparative form (Pravopys 2019 § 111, item 1; never *samyi krashchyi).',
      };
    case 'super_emphatic_prefix':
      return {
        indicator: 'якнай- / щонай-',
        ruleUa:
          'Для підсилення значення найвищого ступеня вживаються префікси якнай-, щонай-, що пишуться разом (Правопис 2019 § 111, п. 1 б: якнайшвидший, щонайкращий).',
        ruleEn:
          'Emphatic prefixes yaknay- and shchonay- are written solid to intensify the superlative (Pravopys 2019 § 111, item 1 b).',
      };
    default:
      return {
        indicator: 'нормативна форма',
        ruleUa: 'Нормативне творення прикметника.',
        ruleEn: 'Standard adjective formation.',
      };
  }
}

/**
 * Resolves soft group instrumental singular ending per Правопис 2019 § 108.
 */
export function resolveSoftDeclensionInstrumentalRule(): {
  ending: string;
  ruleUa: string;
  ruleEn: string;
} {
  return {
    ending: '-ім',
    ruleUa:
      "Прикметники м'якої групи чоловічого та середнього роду в орудному відмінку однини мають закінчення -ім (Правопис 2019 § 108: синім, літнім, осіннім, раннім), а не тверде -им.",
    ruleEn:
      'Soft group masculine and neuter adjectives in the instrumental singular strictly take ending -im (Pravopys 2019 § 108: synim, litnim, osinnim, rannim), not hard -ym.',
  };
}

/**
 * Resolves possessive adjective suffix rules per Правопис 2019 § 107.
 */
export function resolvePossessiveSuffixRule(baseNounDeclension: 1 | 2): {
  suffix: string;
  ruleUa: string;
  ruleEn: string;
} {
  if (baseNounDeclension === 1) {
    return {
      suffix: '-ин / -їн з чергуванням г->ж, к->ч, х->ш',
      ruleUa:
        'Присвійні прикметники від іменників I відміни утворюються за допомогою суфікса -ин (після голосних -їн), при цьому приголосні г, к, х чергуються на ж, ч, ш (Правопис 2019 § 107: Ольга -> Ольжин, дочка -> доччин, мачуха -> мачушин).',
      ruleEn:
        'Possessive adjectives from 1st declension nouns take suffix -yn with consonant mutations h->zh, k->ch, kh->sh (Pravopys 2019 § 107).',
    };
  }
  return {
    suffix: '-ів (-ова, -еве)',
    ruleUa:
      'Присвійні прикметники від іменників II відміни утворюються за допомогою суфікса -ів (у непрямих відмінках -ов- після твердих, -ев-/-єв- після м\'яких: батьків/батькова, Василів/Василева) (Правопис 2019 § 107).',
    ruleEn:
      'Possessive adjectives from 2nd declension nouns take suffix -iv (with -ov- / -ev- in inflected forms) (Pravopys 2019 § 107).',
  };
}

/**
 * Resolves derivational suffix -ськ- mutations per Правопис 2019 § 22.
 */
export function resolveDerivationalSuffixMutationRule(
  stemConsonantGroup: 'velar' | 'dental' | 'sibilant',
): { suffix: string; ruleUa: string; ruleEn: string } {
  if (stemConsonantGroup === 'velar') {
    return {
      suffix: '-зьк-',
      ruleUa:
        'При творенні прикметників за допомогою суфікса -ськ- приголосні г, ж, з змінюються на -зьк- (Правопис 2019 § 22: Прага -> празький, Запоріжжя -> запорізький).',
      ruleEn:
        'Stems in h, zh, z + -sk- mutate into -zk- (Pravopys 2019 § 22: Praha -> prazkyi).',
    };
  }
  if (stemConsonantGroup === 'dental') {
    return {
      suffix: '-цьк-',
      ruleUa:
        'При творенні прикметників за допомогою суфікса -ськ- приголосні к, ч, ц змінюються на -цьк- (Правопис 2019 § 22: козак -> козацький, ткач -> ткацький).',
      ruleEn:
        'Stems in k, ch, ts + -sk- mutate into -tsk- (Pravopys 2019 § 22: kozak -> kozatskyi).',
    };
  }
  return {
    suffix: '-ськ-',
    ruleUa:
      'При творенні прикметників за допомогою суфікса -ськ- приголосні х, ш, с зберігаються: -ськ- (Правопис 2019 § 22: чех -> чеський, товариш -> товариський).',
    ruleEn:
      'Stems in kh, sh, s + -sk- form -skyi (Pravopys 2019 § 22: chekh -> cheskyi).',
  };
}
