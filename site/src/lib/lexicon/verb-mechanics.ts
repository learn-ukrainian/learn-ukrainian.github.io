/**
 * Ukrainian Verb Deep Mechanics Practice Engine (Дієслово).
 *
 * Implements Ukrainian Pravopys 2019 (§§ 115–120) and Academic Grammar rules for:
 *   1. Conjugation Classes I vs II (Дієвідміни I vs II) [§ 115]:
 *      - Class I: personal endings with vowel -е- (-є-), 3rd person plural -уть / -ють (пишеш, чуєш, борються, мелють)
 *      - Class II: personal endings with vowel -и- (-ї-), 3rd person plural -ать / -ять (летиш, сидить, клеїш, стоять, біжать)
 *   2. Stem Morphophonemic Alternations in Conjugation [§ 115]:
 *      - Epenthetic [л'] after labials (б, п, в, м, ф) in 1sg and 3pl Class II (любити -> люблю, люблять; спати -> сплю, сплять)
 *      - Dental/alveolar mutations in 1sg Class II: д->дж (ходжу), т->ч (лечу), с->ш (прошу), з->ж (вожу), ст->щ (чищу), зд->ждж (їжджу)
 *      - Class I present stem mutations: с->ш (пишу), к->ч (печеш), г->ж (можеш), root ablaut (брати -> беру, терти -> тру)
 *   3. Aspectual Pairs & Derivation (Видові пари) [§ 115]:
 *      - Prefixation: писати <-> написати, робити <-> зробити, читати <-> прочитати
 *      - Suffixation & ablaut: переписати <-> переписувати, відкрити <-> відкривати, допомогти <-> допомагати (о <-> а)
 *      - Suppletive pairs: брати <-> взяти, говорити <-> сказати, ловити <-> піймати, класти <-> покласти
 *   4. Imperative Mood Nuances & Anti-Calques [§ 116]:
 *      - Synthetic 2sg/2pl endings: -и / -іть vs - / -те (роби/робіть vs читай/читайте, стань/станьте)
 *      - 1st person plural inclusive encouragement: -мо / -імо (ходімо, робімо, читаймо, працюймо)
 *      - Eradication of Russian calques: *давай підемо / *давайте зробимо -> ходімо, зробімо
 *   5. Verbals: Participles & Gerunds [§§ 119–120]:
 *      - Passive participles in -ний / -тий [§ 119] (написаний, зроблений, розбитий, відкритий)
 *      - Adjectival status of -ачий/-учий forms and eradication of active Russian-calqued participles [§ 119] (*бажаючий -> охочий, *діючий -> чинний)
 *      - Impersonal predicate forms in -но / -то [§ 119] (виконано, прийнято, відкрито)
 *      - Gerunds (дієприслівник) [§ 120]: imperfective simultaneous in -учи/-ючи, -ачи/-ячи vs perfective prior in -вши/-ши
 */

export const VERB_MECHANICS_CATEGORY_KEYS = [
  'conj_class_i_vowel_e_ye',
  'conj_class_ii_vowel_y_yi',
  'conj_labial_epenthesis_l',
  'conj_dental_mutation_1sg',
  'conj_stem_mutation_class_i',
  'aspect_prefixation',
  'aspect_suffixation_ablaut',
  'aspect_suppletive',
  'imperative_synthetic_endings',
  'imperative_inclusive_1pl',
  'imperative_anti_calque_davai',
  'participle_passive_formation',
  'participle_anti_calque_active',
  'participle_impersonal_no_to',
  'gerund_formation_aspect',
] as const;

export type VerbMechanicsCategoryKey = (typeof VERB_MECHANICS_CATEGORY_KEYS)[number];

export const VERB_MECHANICS_INTERFERENCE_KEYS = [
  'false_conjugation_class_i_for_ii',
  'false_conjugation_class_ii_for_i',
  'false_labial_missing_epenthesis_l',
  'false_dental_missing_mutation_1sg',
  'false_stem_mutation_class_i',
  'false_aspect_prefix_confusion',
  'false_aspect_imperfectivation_ablaut',
  'false_aspect_suppletive_regularized',
  'false_imperative_missing_y_ending',
  'false_imperative_excessive_y_ending',
  'false_imperative_1pl_russian_te',
  'false_imperative_indicative_confusion',
  'russian_calque_davai_imperative',
  'false_participle_suffix_nyi_tyi',
  'russian_calque_active_participle',
  'false_impersonal_forms_agreement',
  'false_gerund_aspect_suffix',
] as const;

export type VerbMechanicsInterferenceKey =
  (typeof VERB_MECHANICS_INTERFERENCE_KEYS)[number];

export interface VerbMechanicsDistractor {
  text: string;
  interference_type: VerbMechanicsInterferenceKey;
  explanation: {
    ua: string;
    en: string;
  };
}

export interface PracticeVerbMechanicsCard {
  card_id: string;
  category: VerbMechanicsCategoryKey;
  cefr_level: string;
  prompt_sentence: string;
  blank_target: string;
  correct_answer: string;
  options: string[];
  distractors: VerbMechanicsDistractor[];
  pravopys_section: string;
  rule_summary: {
    ua: string;
    en: string;
  };
}

export interface VerbMechanicsDeckPayload {
  schema_version: string;
  card_count: number;
  cards: PracticeVerbMechanicsCard[];
}

export interface VerbMechanicsFeedbackResult {
  isCorrect: boolean;
  feedback: string;
  pravopysSection: string;
  ruleSummary: string;
}

/**
 * Evaluates learner selection against card expectations and produces targeted pedagogical feedback.
 */
export function verbMechanicsFeedbackFor(
  card: PracticeVerbMechanicsCard,
  selectedOption: string,
  locale: 'ua' | 'en' = 'ua',
): VerbMechanicsFeedbackResult {
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
 * Resolves conjugation class rule per Правопис 2019 § 115.
 */
export function resolveConjugationClassRule(
  category: VerbMechanicsCategoryKey,
): { indicator: string; ruleUa: string; ruleEn: string } {
  if (category === 'conj_class_i_vowel_e_ye') {
    return {
      indicator: '-е- / -є- (-уть / -ють)',
      ruleUa:
        'I дієвідміна: дієслова мають закінчення 3-ї особи множини -уть/-ють та голосний -е-/-є- в особових закінченнях (пишеш, знаєш, борються, мелють).',
      ruleEn:
        'Conjugation Class I: 3rd person plural ends in -ut/-yut and personal endings take -e-/-ye- (pyshesh, znaiesh, boriutsia, meliut).',
    };
  }
  if (category === 'conj_class_ii_vowel_y_yi') {
    return {
      indicator: '-и- / -ї- (-ать / -ять)',
      ruleUa:
        'II дієвідміна: дієслова мають закінчення 3-ї особи множини -ать/-ять та голосний -и-/-ї- в особових закінченнях (летиш, сидить, стоїмо, біжать).',
      ruleEn:
        'Conjugation Class II: 3rd person plural ends in -at/-iat and personal endings take -y-/-yi- (letysh, sydyt, stoimo, bizhat).',
    };
  }
  throw new Error(`Category ${category} is not a primary conjugation class category.`);
}

/**
 * Resolves epenthesis indicator and explanation per Правопис 2019 § 115.
 */
export function resolveEpenthesisRule(): {
  indicator: string;
  ruleUa: string;
  ruleEn: string;
} {
  return {
    indicator: "[л']",
    ruleUa:
      "Вставний [л'] після губних приголосних б, п, в, м, ф перед голосними в 1 ос. однини та 3 ос. множини II дієвідміни (любити -> люблю, люблять; спати -> сплю, сплять).",
    ruleEn:
      "Epenthetic [l'] after labials b, p, v, m, f in 1sg and 3pl of Class II verbs (liubyty -> liubliu, liubliat; spaty -> spliu, spliat).",
  };
}

/**
 * Resolves dental/alveolar consonant alternation rule for 1sg per Правопис 2019 § 115.
 */
export function resolveDentalMutationRule(mutationKey: string): {
  mutation: string;
  ruleUa: string;
  ruleEn: string;
} {
  const mapping: Record<string, { mutation: string; ruleUa: string; ruleEn: string }> = {
    d_dzh: {
      mutation: 'д -> дж',
      ruleUa: 'д чергується з дж: ходити -> ходжу, садити -> саджу.',
      ruleEn: 'd alternates with dzh: khodyty -> khodzhy.',
    },
    t_ch: {
      mutation: 'т -> ч',
      ruleUa: 'т чергується з ч: летіти -> лечу, платити -> плачу.',
      ruleEn: 't alternates with ch: letity -> lechu.',
    },
    s_sh: {
      mutation: 'с -> ш',
      ruleUa: 'с чергується з ш: просити -> прошу, косити -> кошу.',
      ruleEn: 's alternates with sh: prosyty -> proshu.',
    },
    z_zh: {
      mutation: 'з -> ж',
      ruleUa: 'з чергується з ж: возити -> вожу, морозити -> морожу.',
      ruleEn: 'z alternates with zh: vozyty -> vozhu.',
    },
    st_shch: {
      mutation: 'ст -> щ',
      ruleUa: 'ст чергується зі щ: мостити -> мощу, чистити -> чищу.',
      ruleEn: 'st alternates with shch: mostyty -> moshchu.',
    },
    zd_zhdzh: {
      mutation: 'зд -> ждж',
      ruleUa: 'зд чергується з ждж: їздити -> їжджу.',
      ruleEn: 'zd alternates with zhdzh: yizdyty -> yizhdzhu.',
    },
  };
  const res = mapping[mutationKey];
  if (!res) {
    throw new Error(`Unknown dental mutation key: ${mutationKey}`);
  }
  return res;
}

/**
 * Resolves imperative mood ending rule per Правопис 2019 § 116.
 */
export function resolveImperativeRule(stemType: 'stressed_or_cluster' | 'vowel_or_soft' | 'inclusive_1pl'): {
  indicator: string;
  ruleUa: string;
  ruleEn: string;
} {
  if (stemType === 'stressed_or_cluster') {
    return {
      indicator: '-и / -іть',
      ruleUa:
        'Під наголосом або після збігу приголосних закінчення -и у 2-й особі однини та -іть у множині (роби, робіть; пиши, пишіть; пор. винятки чисть, морщ).',
      ruleEn:
        'Under stress or following consonant clusters, ending is generally -y (2sg) and -it (2pl) (roby, robit; pyshy, pyshit; cf. exceptions like chyst, morshch).',
    };
  }
  if (stemType === 'vowel_or_soft') {
    return {
      indicator: 'нульове / -те',
      ruleUa:
        "Після голосних та м'яких приголосних без кінцевого наголосу виступає нульове закінчення у 2-й особі однини та -те у множині (читай, читайте; стань, станьте).",
      ruleEn:
        'After vowels or non-final-stressed soft consonants, zero ending in 2sg and -te in 2pl (chytai, chytaite; stan, stante).',
    };
  }
  return {
    indicator: '-мо / -імо',
    ruleUa:
      'Форми 1-ї особи множини наказового способу (заклик до спільної дії) мають нормативні закінчення -мо або -імо (ходімо, робімо, читаймо).',
    ruleEn:
      '1st person plural imperative (encouragement to joint action) takes native endings -mo or -imo (khodimo, robimo, chytaimo).',
  };
}

/**
 * Resolves active participle anti-calque rule per НУШ / Правопис 2019 § 119.
 */
export function resolveParticipleAntiCalqueRule(): {
  indicator: string;
  ruleUa: string;
  ruleEn: string;
} {
  return {
    indicator: 'Подолання активних дієприкметників',
    ruleUa:
      'В українській мові форми на -ачий/-учий функціонують переважно як прикметники або іменники (квітучий, живучий, стоячий). Активні дієприкметники теперішнього часу на позначення процесу замінюються прикметниками, іменниками чи підрядними реченнями (охочий, чинний, початківець).',
    ruleEn:
      'In Ukrainian, forms in -achy/-uchy predominantly function as lexical adjectives or nouns (kvituchyi, zhyvuchyi). Active present participles expressing ongoing action are replaced with proper adjectives, agent nouns, or subordinate clauses (okhochyi, chynnyi, pochatkivets).',
  };
}

/**
 * Resolves impersonal predicate form rule per Правопис 2019 § 119.
 */
export function resolveImpersonalFormRule(): {
  indicator: string;
  ruleUa: string;
  ruleEn: string;
} {
  return {
    indicator: '-но / -то',
    ruleUa:
      "У безособових реченнях присудок виражається незмінюваними дієслівними формами на -но / -то із прямим додатком у знахідному відмінку (роботу виконано, закон прийнято).",
    ruleEn:
      'Impersonal state predicates require invariant verbal forms ending in -no / -to with the direct object in the accusative (robotu vykonano, zakon pryiniato).',
  };
}

/**
 * Resolves gerund aspect suffix rule per Правопис 2019 § 120.
 */
export function resolveGerundAspectRule(aspect: 'imperfective' | 'perfective'): {
  indicator: string;
  ruleUa: string;
  ruleEn: string;
} {
  if (aspect === 'imperfective') {
    return {
      indicator: '-учи/-ючи / -ачи/-ячи',
      ruleUa:
        'Дієприслівники недоконаного виду для одночасної дії творяться за допомогою суфіксів -учи/-ючи (I дієвідміна) або -ачи/-ячи (II дієвідміна) (читаючи, сидячи).',
      ruleEn:
        'Imperfective gerunds for simultaneous action take suffixes -uchy/-iuchy (Class I) or -achy/-iachy (Class II) (chytaiuchy, sydyachy).',
    };
  }
  return {
    indicator: '-вши / -ши',
    ruleUa:
      'Дієприслівники доконаного виду для передуючої завершеної дії творяться за допомогою суфіксів -вши (після голосних) та -ши (після приголосних) (прочитавши, принісши).',
    ruleEn:
      'Perfective gerunds for prior completed action take suffixes -vshy (after vowels) and -shy (after consonants) (prochytaffshy, prynisshy).',
  };
}
