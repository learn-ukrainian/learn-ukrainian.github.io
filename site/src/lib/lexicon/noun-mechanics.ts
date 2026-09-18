/**
 * Ukrainian Noun Deep Mechanics Practice Engine (Іменник).
 *
 * Implements Ukrainian Pravopys 2019 (§§ 68, 73, 80, 82, 87) and Academic Grammar rules for:
 *   1. II Declension Genitive Singular Endings (-а/-я vs -у/-ю) [§ 82]:
 *      - Beings, persons, concrete objects, settlements, measures -> -а/-я
 *      - Substances, materials, mass terms, collective nouns, abstract processes, territories -> -у/-ю
 *      - Semantic homonym pairs distinguishing meaning (каменя/каменю, листопада/листопаду, апарата/апарату, терміна/терміну)
 *   2. Vocative Case Endings (-е, -у, -ю, -о) [§§ 73, 87]:
 *      - Hard stems with consonant mutation (г->ж, к->ч, х->ш) -> -е
 *      - Suffixes -ник, -ак, -ок and hard velars -> -у
 *      - Soft stems and hypocoristics -> -ю
 *      - 1st declension hard stems -> -о, soft stems -> -е/-є, affectionates -> -ю
 *   3. Instrumental Case Mixed Sibilant Stems (-ем vs -ом) [§ 80]:
 *      - Sibilant stems (ж, ч, ш, щ) strictly take -ем (ножем, товаришем, плащем, мечем)
 *   4. Animacy in Masculine Accusative:
 *      - Animate beings take Genitive form (Acc = Gen)
 *      - Inanimate objects strictly take Nominative form (Acc = Nom)
 */

export const NOUN_MECHANICS_CATEGORY_KEYS = [
  'gen_ii_being_concrete',
  'gen_ii_settlement_measure',
  'gen_ii_substance_mass',
  'gen_ii_abstract_process',
  'gen_ii_collective_territory',
  'gen_ii_homonym_pair',
  'voc_ii_hard_e',
  'voc_ii_velar_suffix_u',
  'voc_ii_soft_yu',
  'voc_i_hard_o',
  'voc_i_soft_ye_yu',
  'inst_ii_mixed_sibilant_em',
  'animacy_accusative',
] as const;

export type NounMechanicsCategoryKey = (typeof NOUN_MECHANICS_CATEGORY_KEYS)[number];

export const NOUN_MECHANICS_INTERFERENCE_KEYS = [
  'false_genitive_a_for_abstract_mass',
  'false_genitive_u_for_concrete_being',
  'false_genitive_u_for_settlement',
  'false_genitive_a_for_collective',
  'homonym_genitive_meaning_mismatch',
  'false_nominative_for_genitive',
  'false_instrumental_for_genitive',
  'false_dative_for_genitive',
  'false_vocative_nominative',
  'false_vocative_u_for_hard_e',
  'false_vocative_e_for_suffix_u',
  'false_vocative_e_for_soft_yu',
  'false_vocative_yu_for_hard_e',
  'false_vocative_o_for_soft',
  'false_mutation_missing',
  'false_instrumental_om_for_sibilant',
  'false_instrumental_im_for_noun',
  'false_nominative_for_instrumental',
  'false_instrumental_em_for_hard',
  'false_animacy_accusative_inanimate',
  'false_animacy_accusative_animate',
  'false_instrumental_for_accusative',
  'false_dative_for_accusative',
  'russian_declension_interference',
] as const;

export type NounMechanicsInterferenceKey = (typeof NOUN_MECHANICS_INTERFERENCE_KEYS)[number];

export interface NounMechanicsDistractor {
  text: string;
  interference_type: NounMechanicsInterferenceKey;
  explanation: {
    ua: string;
    en: string;
  };
}

export interface PracticeNounMechanicsCard {
  card_id: string;
  category: NounMechanicsCategoryKey;
  cefr_level: string;
  prompt_sentence: string;
  blank_target: string;
  correct_answer: string;
  options: string[];
  distractors: NounMechanicsDistractor[];
  pravopys_section: string;
  rule_summary: {
    ua: string;
    en: string;
  };
}

export interface NounMechanicsDeckPayload {
  version: string;
  title: string;
  description: string;
  card_count: number;
  cards: PracticeNounMechanicsCard[];
}

export interface NounMechanicsFeedbackResult {
  isCorrect: boolean;
  feedback: string;
  pravopysSection: string;
  ruleSummary: string;
}

/**
 * Evaluates learner selection against card expectations and produces targeted pedagogical feedback.
 */
export function nounMechanicsFeedbackFor(
  card: PracticeNounMechanicsCard,
  selectedOption: string,
  locale: 'ua' | 'en' = 'ua',
): NounMechanicsFeedbackResult {
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
 * Resolves II declension Genitive ending rule per Правопис 2019 § 82.
 */
export function resolveNounGenitiveRule(
  isConcreteOrBeing: boolean,
  isSettlementOrMeasure = false,
): { ending: string; ruleUa: string; ruleEn: string } {
  if (isConcreteOrBeing || isSettlementOrMeasure) {
    return {
      ending: '-а / -я',
      ruleUa:
        'Іменники II відміни чоловічого роду, що означають істот, конкретні предмети, міста або міри, мають закінчення -а/-я (Правопис 2019 § 82, п. 1).',
      ruleEn:
        'Second declension masculine nouns denoting beings, concrete countable objects, settlements, or units of measure take ending -a/-ya (Pravopys 2019 § 82, item 1).',
    };
  }
  return {
    ending: '-у / -ю',
    ruleUa:
      'Іменники II відміни чоловічого роду, що означають речовини, матеріали, збірні поняття, абстрактні явища або території, мають закінчення -у/-ю (Правопис 2019 § 82, п. 2).',
    ruleEn:
      'Second declension masculine nouns denoting substances, mass terms, collective entities, abstract concepts, or territories take ending -u/-yu (Pravopys 2019 § 82, item 2).',
  };
}

/**
 * Resolves Vocative case ending rule per Правопис 2019 §§ 73, 87.
 */
export function resolveNounVocativeRule(
  declension: 1 | 2,
  stemGroup: 'hard' | 'soft' | 'mixed',
  hasVelarOrDiminutive = false,
  isSoftHypocoristic = false,
): { ending: string; ruleUa: string; ruleEn: string } {
  if (declension === 1) {
    if (stemGroup === 'hard') {
      return {
        ending: '-о',
        ruleUa:
          'Іменники I відміни твердої групи у кличному відмінку мають закінчення -о (Правопис 2019 § 73, п. 1: мамо, сестро, Миколо).',
        ruleEn: 'First declension hard stem nouns take vocative ending -o (Pravopys 2019 § 73, item 1).',
      };
    }
    if (isSoftHypocoristic) {
      return {
        ending: '-ю',
        ruleUa:
          'Пестливі іменники I відміни м\'якої групи у кличному відмінку мають закінчення -ю (Правопис 2019 § 73, п. 2: доню, бабусю).',
        ruleEn: 'Affectionate 1st declension soft stem nouns take vocative ending -yu (Pravopys 2019 § 73, item 2).',
      };
    }
    return {
      ending: '-е / -є',
      ruleUa:
        'Іменники I відміни м\'якої групи у кличному відмінку мають закінчення -е (після голосного -є) (Правопис 2019 § 73, п. 2: земле, Маріє).',
      ruleEn: 'First declension soft stem nouns take vocative ending -e / -ye (Pravopys 2019 § 73, item 2).',
    };
  }

  // Declension 2
  if (stemGroup === 'hard') {
    if (hasVelarOrDiminutive) {
      return {
        ending: '-у',
        ruleUa:
          'Іменники II відміни на задньоязиковий або з суфіксами -ник, -ак, -ок у кличному відмінку мають закінчення -у (Правопис 2019 § 87, п. 2: батьку, синку).',
        ruleEn:
          'Second declension nouns ending in velars or with suffixes -nyk, -ak, -ok take vocative ending -u (Pravopys 2019 § 87, item 2).',
      };
    }
    return {
      ending: '-е',
      ruleUa:
        'Іменники II відміни твердої групи у кличному відмінку мають закінчення -е з історичним чергуванням г->ж, к->ч, х->ш (Правопис 2019 § 87, п. 1: друже, козаче, брате).',
      ruleEn:
        'Second declension hard stem nouns take vocative ending -e with historical consonant mutation (Pravopys 2019 § 87, item 1).',
    };
  }
  if (stemGroup === 'soft') {
    return {
      ending: '-ю',
      ruleUa:
        'Іменники II відміни м\'якої групи у кличному відмінку мають закінчення -ю (Правопис 2019 § 87, п. 3: вчителю, Василю, бійцю, Андрію).',
      ruleEn: 'Second declension soft stem nouns take vocative ending -yu (Pravopys 2019 § 87, item 3).',
    };
  }
  return {
    ending: '-е',
    ruleUa:
      'Іменники II відміни мішаної групи з основою на шиплячий у кличному відмінку мають закінчення -е (Правопис 2019 § 87, п. 1: юначе, школяре).',
    ruleEn: 'Second declension mixed sibilant stem nouns take vocative ending -e (Pravopys 2019 § 87, item 1).',
  };
}

/**
 * Resolves II declension Instrumental singular ending per Правопис 2019 § 80.
 */
export function resolveInstrumentalSingularRule(stemGroup: 'hard' | 'soft' | 'mixed'): {
  ending: string;
  ruleUa: string;
  ruleEn: string;
} {
  if (stemGroup === 'hard') {
    return {
      ending: '-ом',
      ruleUa:
        'Іменники II відміни твердої групи в орудному відмінку однини мають закінчення -ом (Правопис 2019 § 80: столом, братом).',
      ruleEn: 'Second declension hard stem nouns take instrumental ending -om (Pravopys 2019 § 80).',
    };
  }
  if (stemGroup === 'mixed') {
    return {
      ending: '-ем',
      ruleUa:
        'Іменники II відміни мішаної групи (з основою на шиплячий ж, ч, ш, щ) в орудному відмінку обов\'язково мають закінчення -ем, а не -ом (Правопис 2019 § 80: ножем, товаришем, плащем).',
      ruleEn:
        'Second declension mixed sibilant stem nouns (zh, ch, sh, shch) strictly take ending -em, not -om, in the instrumental (Pravopys 2019 § 80).',
    };
  }
  return {
    ending: '-ем / -єм',
    ruleUa:
      'Іменники II відміни м\'якої групи в орудному відмінку мають закінчення -ем (після голосного -єм) (Правопис 2019 § 80: конем, краєм, бійцем).',
    ruleEn: 'Second declension soft stem nouns take instrumental ending -em / -yem (Pravopys 2019 § 80).',
  };
}

/**
 * Resolves masculine Accusative case animacy distinction.
 */
export function resolveAnimacyAccusativeRule(isAnimate: boolean): {
  caseForm: string;
  ruleUa: string;
  ruleEn: string;
} {
  if (isAnimate) {
    return {
      caseForm: 'Родовий відмінок (-а/-я)',
      ruleUa:
        'Іменники чоловічого роду — назви істот — у знахідному відмінку однини мають форму, спільну з родовим відмінком (зустрів студента, бачу вовка).',
      ruleEn:
        'Masculine animate nouns (beings) in the accusative singular take the genitive form (e.g. zustriv studenta).',
    };
  }
  return {
    caseForm: 'Називний відмінок (без закінчення)',
    ruleUa:
      'Іменники чоловічого роду — назви неістот — у знахідному відмінку однини мають форму, спільну з називним відмінком (купив новий стіл, поклав олівець).',
    ruleEn:
      'Masculine inanimate nouns in the accusative singular strictly take the nominative form (e.g. kupyv stil, not *stola).',
  };
}
