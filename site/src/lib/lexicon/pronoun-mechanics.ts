/**
 * Ukrainian Pronoun Deep Mechanics Practice Engine (Займенник).
 *
 * Implements Ukrainian Pravopys 2019 (§§ 39, 108–114) and Academic Grammar rules for:
 *   1. Epenthetic [n-] in 3rd-Person Pronouns (§ 108):
 *      - Compulsory epenthetic n- after prepositions: до нього, біля неї, про них, на ньому
 *      - Absence of n- in direct case government: бачу його, чую її, зустрів їх, дав йому
 *      - Omnipresent n- in Instrumental case: з ним / пишатися ним, з нею / захоплюватися нею, з ними / пишатися ними
 *      - Absence of n- after derivative dative prepositions: завдяки йому, наперекір їй, всупереч їм
 *   2. Orthography of Indefinite and Negative Pronouns (§ 39):
 *      - Solid writing with prefixes де-, аби-, ані- and suffix -сь: дехто, абихто, хтось, щось
 *      - Hyphenated writing with particles будь-, -небудь, казна-, хтозна-, бозна-: будь-хто, хто-небудь, казна-що
 *      - Split three-word writing when preposition intervenes: будь у кого, будь з ким, хтозна з ким, аби перед ким
 *      - Solid writing of negative pronouns with prefix ні-: ніхто, ніщо, ніякий, нічий
 *      - Split three-word writing of negative pronouns with prepositions: ні про що, ні з ким, ні до кого, ні за яких
 *   3. Declension Paradigms (§§ 109–113):
 *      - Reflexive pronoun себе: defective paradigm without Nominative; Dative собі, Instrumental собою, Locative на собі
 *      - Pronoun весь: Instrumental plural всіма (not *всьома, not *всеми)
 *      - Demonstrative pronouns цей / той: цими, тими, цього, тому, цьому
 *      - Interrogative pronouns хто, що, чий: кого, чого; кому, чому; ким, чим; чийого, чиєму, чиїм, чиїми
 *   4. Stylistics & Semantic Distinctions:
 *      - сам (personally, unassisted) vs самий (identity: той самий; limit: з самого ранку; anti-calque *самий кращий -> найкращий)
 *      - Possessive modifier їхній (їхнього, їхньому, їхнім, їхніми) vs 3rd-person personal pronoun after prepositions до них
 */

export const PRONOUN_MECHANICS_CATEGORY_KEYS = [
  'epenthetic_n_prepositional',
  'epenthetic_n_absence_direct',
  'epenthetic_n_instrumental_omnipresent',
  'epenthetic_n_derivative_prepositions',
  'orthography_indefinite_together',
  'orthography_indefinite_hyphen',
  'orthography_indefinite_split_preposition',
  'orthography_negative_together',
  'orthography_negative_split_preposition',
  'reflexive_sebe_paradigm',
  'declension_ves_alternation',
  'declension_tsyey_toy',
  'interrogative_chyi_khto_shcho',
  'semantic_sam_vs_samyi',
  'possessive_yikhniy_vs_yikh',
] as const;

export type PronounMechanicsCategoryKey =
  (typeof PRONOUN_MECHANICS_CATEGORY_KEYS)[number];

export const PRONOUN_MECHANICS_INTERFERENCE_KEYS = [
  'spurious_epenthetic_n',
  'missing_epenthetic_n',
  'corrupted_instrumental_form',
  'wrongly_attached_derivative_n',
  'hyphenated_indefinite_calque',
  'separate_indefinite_calque',
  'solid_written_hyphen_particle',
  'separate_written_hyphen_particle',
  'hyphenated_split_preposition',
  'solid_split_preposition',
  'external_preposition_russian_calque',
  'separate_negative_pronoun',
  'hyphenated_negative_pronoun',
  'defective_refl_nominative',
  'corrupted_declension_stem',
  'confusion_sam_vs_samyi',
  'confusion_possessive_vs_personal',
] as const;

export type PronounMechanicsInterferenceKey =
  (typeof PRONOUN_MECHANICS_INTERFERENCE_KEYS)[number];

export interface PronounMechanicsDistractor {
  text: string;
  interference_type: PronounMechanicsInterferenceKey;
  explanation: {
    ua: string;
    en: string;
  };
}

export interface PracticePronounMechanicsCard {
  card_id: string;
  category: PronounMechanicsCategoryKey;
  cefr_level: string;
  prompt_sentence: string;
  blank_target: string;
  correct_answer: string;
  options: string[];
  distractors: PronounMechanicsDistractor[];
  pravopys_section: string;
  rule_summary: {
    ua: string;
    en: string;
  };
}

export interface PronounMechanicsDeckPayload {
  schema_version: string;
  title: string;
  card_count: number;
  categories: PronounMechanicsCategoryKey[];
  cards: PracticePronounMechanicsCard[];
}

export interface PronounMechanicsFeedbackResult {
  isCorrect: boolean;
  feedback: string;
  ruleCitation: string;
  ruleSummary: string;
}

/**
 * Evaluates learner selection against card expectations and produces targeted pedagogical feedback.
 */
export function pronounMechanicsFeedbackFor(
  card: PracticePronounMechanicsCard,
  selectedOption: string,
  locale: 'ua' | 'en' = 'ua',
): PronounMechanicsFeedbackResult {
  const normSelected = (selectedOption ?? '').trim();
  const normCorrect = (card.correct_answer ?? (card as any).correctAnswer ?? '').trim();
  const ruleUa = card.rule_summary?.ua ?? (card as any).ruleSummary?.uk ?? '';
  const ruleEn = card.rule_summary?.en ?? (card as any).ruleSummary?.en ?? '';
  const citation =
    card.pravopys_section ?? (card as any).rule_citation ?? (card as any).ruleCitation ?? '';

  if (normSelected === normCorrect) {
    const successMsg =
      locale === 'ua'
        ? `Правильно! ${ruleUa}`
        : `Correct! ${ruleEn}`;
    return {
      isCorrect: true,
      feedback: successMsg,
      ruleCitation: citation,
      ruleSummary: locale === 'ua' ? ruleUa : ruleEn,
    };
  }

  const matchedDistractor = card.distractors?.find(
    (d) => (d.text ?? (d as any).form ?? '').trim() === normSelected,
  );
  if (matchedDistractor) {
    const explanation =
      locale === 'ua'
        ? (matchedDistractor.explanation?.ua ?? (matchedDistractor as any).explanationUa ?? '')
        : (matchedDistractor.explanation?.en ?? (matchedDistractor as any).explanationEn ?? '');
    return {
      isCorrect: false,
      feedback: explanation,
      ruleCitation: citation,
      ruleSummary: locale === 'ua' ? ruleUa : ruleEn,
    };
  }

  const fallback =
    locale === 'ua'
      ? `Неправильно. Правильна форма: «${normCorrect}». ${ruleUa}`
      : `Incorrect. The correct form is "${normCorrect}". ${ruleEn}`;

  return {
    isCorrect: false,
    feedback: fallback,
    ruleCitation: citation,
    ruleSummary: locale === 'ua' ? ruleUa : ruleEn,
  };
}

/**
 * Resolves epenthetic n- rule per Правопис 2019 § 108.
 */
export function resolveEpenthesisRule(category: PronounMechanicsCategoryKey): {
  citation: string;
  ruleUa: string;
  ruleEn: string;
} {
  const citation = 'Правопис 2019 § 108';
  if (category === 'epenthetic_n_prepositional') {
    return {
      citation,
      ruleUa:
        "Після прийменників у формах непрямих відмінків 3-ї особи обов'язково з'являється приставний [н-]: до нього, біля неї, про них, на ньому.",
      ruleEn:
        'After prepositions in oblique cases of 3rd-person pronouns, epenthetic [n-] is compulsory: до нього, біля неї, про них, на ньому.',
    };
  }
  if (category === 'epenthetic_n_absence_direct') {
    return {
      citation,
      ruleUa:
        'Без прийменників у прямому керуванні (родовий, знахідний, давальний) приставний [н-] не вживається: бачу його, чую її, зустрів їх, дав йому.',
      ruleEn:
        'Without prepositions in direct case government (Gen/Acc/Dat), epenthetic [n-] is not used: бачу його, чую її, зустрів їх, дав йому.',
    };
  }
  if (category === 'epenthetic_n_instrumental_omnipresent') {
    return {
      citation,
      ruleUa:
        'В орудному відмінку 3-ї особи звук [н] присутній завжди (як з прийменником, так і без нього): ним, нею, ними.',
      ruleEn:
        'In the Instrumental case of 3rd-person pronouns, [n-] is always present (both with and without prepositions): ним, нею, ними.',
    };
  }
  if (category === 'epenthetic_n_derivative_prepositions') {
    return {
      citation,
      ruleUa:
        "Після похідних прийменників, що керують давальним відмінком (завдяки, наперекір, всупереч), приставний [н-] не з'являється: завдяки йому, наперекір їй.",
      ruleEn:
        'After derivative prepositions governing Dative (завдяки, наперекір, всупереч), epenthetic [n-] is not attached: завдяки йому, наперекір їй.',
    };
  }
  throw new Error(`Category ${category} is not an epenthesis category.`);
}

/**
 * Resolves pronoun orthography rule per Правопис 2019 § 39.
 */
export function resolveOrthographyRule(category: PronounMechanicsCategoryKey): {
  citation: string;
  ruleUa: string;
  ruleEn: string;
} {
  const citation = 'Правопис 2019 § 39';
  if (category === 'orthography_indefinite_together') {
    return {
      citation,
      ruleUa:
        'Неозначені займенники з частками-префіксами де-, аби-, ані- та суфіксом -сь пишуться разом: дехто, абихто, хтось, щось.',
      ruleEn:
        'Indefinite pronouns with prefixes де-, аби-, ані- and suffix -сь are written as a single word: дехто, абихто, хтось, щось.',
    };
  }
  if (category === 'orthography_indefinite_hyphen') {
    return {
      citation,
      ruleUa:
        'Неозначені займенники з частками будь-, -небудь, казна-, хтозна-, бозна- пишуться через дефіс: будь-хто, хто-небудь, казна-що, хтозна-який.',
      ruleEn:
        'Indefinite pronouns with particles будь-, -небудь, казна-, хтозна-, бозна- are written with a hyphen: будь-хто, хто-небудь, казна-що, хтозна-який.',
    };
  }
  if (category === 'orthography_indefinite_split_preposition') {
    return {
      citation,
      ruleUa:
        'Якщо між часткою (будь, хтозна, казна, бозна, аби, де) та займенником стоїть прийменник, уся сполука пишеться окремо трьома словами: будь у кого, будь з ким, хтозна з ким.',
      ruleEn:
        'When a preposition intervenes between the particle (будь, хтозна, казна, бозна, аби, де) and the pronoun, all three words are written separately: будь у кого, будь з ким, хтозна з ким.',
    };
  }
  if (category === 'orthography_negative_together') {
    return {
      citation,
      ruleUa:
        'Заперечні займенники з префіксом ні- без прийменників пишуться разом: ніхто, ніщо, ніякий, нічий.',
      ruleEn:
        'Negative pronouns with prefix ні- without prepositions are written as a single word: ніхто, ніщо, ніякий, нічий.',
    };
  }
  if (category === 'orthography_negative_split_preposition') {
    return {
      citation,
      ruleUa:
        'За наявності прийменника заперечний займенник розпадається на три окремих слова (ні + прийменник + форма займенника): ні про що, ні з ким, ні до кого.',
      ruleEn:
        'When a preposition is present, negative pronouns split into three separate words (ні + preposition + pronoun): ні про що, ні з ким, ні до кого.',
    };
  }
  throw new Error(`Category ${category} is not an orthography category.`);
}

/**
 * Resolves reflexive pronoun себе rule per Правопис 2019 § 109.
 */
export function resolveReflexiveSebeRule(): {
  citation: string;
  ruleUa: string;
  ruleEn: string;
} {
  return {
    citation: 'Правопис 2019 § 109',
    ruleUa:
      "Зворотний займенник 'себе' не має називного відмінка; давальний відмінок — собі, орудний — собою, місцевий — на собі (при собі).",
    ruleEn:
      "Reflexive pronoun 'себе' lacks Nominative; Dative is собі, Instrumental is собою, Locative is на собі (при собі).",
  };
}

/**
 * Resolves pronoun весь rule per Правопис 2019 § 113.
 */
export function resolveDeclensionVesRule(): {
  citation: string;
  ruleUa: string;
  ruleEn: string;
} {
  return {
    citation: 'Правопис 2019 § 113',
    ruleUa:
      "Займенник 'весь' в орудному відмінку множини має нормативне закінчення -іма: всіма (форми *всьома чи *всеми є ненормативними).",
    ruleEn:
      "The pronoun 'весь' in Instrumental plural takes ending -іма: всіма (forms *всьома and *всеми are ungrammatical).",
  };
}

/**
 * Resolves demonstrative pronouns цей and той rule per Правопис 2019 § 111.
 */
export function resolveDemonstrativeRule(): {
  citation: string;
  ruleUa: string;
  ruleEn: string;
} {
  return {
    citation: 'Правопис 2019 § 111',
    ruleUa:
      "Вказівні займенники 'цей' та 'той' у формах множини та непрямих відмінків однини відмінюються за твердим чи м'яким типом: цими, тими, цього, тому.",
    ruleEn:
      "Demonstrative pronouns 'цей' and 'той' decline according to hard/soft pronominal patterns: цими, тими, цього, тому.",
  };
}

/**
 * Resolves interrogative pronouns хто, що, чий rule per Правопис 2019 § 112.
 */
export function resolveInterrogativeRule(): {
  citation: string;
  ruleUa: string;
  ruleEn: string;
} {
  return {
    citation: 'Правопис 2019 § 112',
    ruleUa:
      'Питально-відносні займенники хто, що, чий змінюються за відмінками (кого, чого; кому, чому; ким, чим; чийого, чиєму, чиїм, чиїми).',
    ruleEn:
      'Interrogative-relative pronouns хто, що, чий decline according to pronominal paradigms (кого, чого; кому, чому; ким, чим; чийого, чиєму, чиїм, чиїми).',
  };
}

/**
 * Resolves semantic distinction сам vs самий rule.
 */
export function resolveSamVsSamyiRule(): {
  citation: string;
  ruleUa: string;
  ruleEn: string;
} {
  return {
    citation: 'Академічна стилістика та Правопис 2019 § 113',
    ruleUa:
      "'Сам' означає дію суб'єкта без сторонньої допомоги або особисто; 'самий' вказує на тотожність (той самий) чи просторову/часову межу (з самого ранку).",
    ruleEn:
      "'Сам' expresses unassisted or personal action; 'самий' expresses identity (той самий) or spatial/temporal boundary (з самого ранку).",
  };
}

/**
 * Resolves possessive pronoun їхній vs personal їх rule per Правопис 2019 § 110.
 */
export function resolvePossessiveYikhniyRule(): {
  citation: string;
  ruleUa: string;
  ruleEn: string;
} {
  return {
    citation: 'Правопис 2019 § 110',
    ruleUa:
      "Присвійний займенник 'їхній' узгоджується з іменником за зразком м'якої групи прикметників; після прийменників з особовим значенням вживається форма 'до них'.",
    ruleEn:
      "Possessive pronoun 'їхній' declines like soft-stem adjectives; after prepositions in personal reference, 3rd-person 'до них' is used.",
  };
}
