/**
 * Ukrainian Adverb Deep Mechanics Practice Engine (Прислівник).
 *
 * Implements Ukrainian Pravopys 2019 (§ 41, §§ 110–111) and Academic Grammar rules for:
 *   1. Semantic Classification:
 *      - Manner & Qualitative (способу дії та якісно-означувальні: як? яким способом?)
 *      - Time (часу: коли? відколи? доки?)
 *      - Place & Direction (місця та напрямку: де? куди? звідки?)
 *      - Measure & Degree (міри й ступеня: скільки? наскільки? якою мірою?)
 *      - Cause & Purpose (причини й мети: чому? навіщо?)
 *   2. Orthography:
 *      - Hyphenated spelling (§ 41, п. 2):
 *        * Prefix по- with suffixes -ому, -ему, -и, -ськи, -цьки (по-українськи, по-новому, по-батьківськи, по-моєму) per п. 2 а
 *        * Particles будь-, -небудь, казна-, хтозна-, бозна-, -таки, -то (будь-де, як-небудь, хтозна-як, казна-коли) per п. 2 б
 *        * Reduplication, synonymous & paired compounds (віч-на-віч, пліч-о-пліч, тишком-нишком, ледве-ледве, давним-давно) per п. 2 в
 *      - One-word fused spelling (§ 41, п. 1):
 *        * Preposition + noun/numeral/pronoun fusion (спочатку, вперше, спідлоба, навшпиньки, насторожі)
 *      - Homophone discrimination (§ 41, п. 1 vs п. 3):
 *        * Fused adverbs vs prepositional noun phrases (напам'ять vs на пам'ять, вдень vs в день, додому vs до дому, згори vs з гори, назустріч vs на зустріч)
 *      - Separate spelling (§ 41, п. 3):
 *        * Adverbial prepositional phrases (на жаль, до речі, без сумніву, день у день, до побачення)
 *   3. Degrees of Comparison (§§ 110–111):
 *      - Synthetic comparative (-ше, -іше) and suppletive roots (швидше, тепліше, глибше; краще, гірше) per § 110
 *      - Superlative degree with prefix най- and intensifying prefixes як-, що- (найкраще, якнайшвидше, щонайдовше, найвище) per § 111
 *      - Anti-calques: *самий краще* ❌ -> найкраще ✅, *більш краще* ❌ -> краще ✅
 *   4. Anti-Calques & Speech Culture:
 *      - насамперед (not *в першу чергу* ❌)
 *      - навряд чи (not *вряд ли* ❌)
 *      - переважно (not *в основному* ❌)
 *      - принаймні (not *по крайній мірі* ❌)
 *      - у крайньому разі (not *в крайньому випадку* ❌)
 */

export const ADVERB_MECHANICS_CATEGORY_KEYS = [
  'adverb_semantic_manner_action',
  'adverb_semantic_time',
  'adverb_semantic_place_direction',
  'adverb_semantic_measure_degree',
  'adverb_semantic_cause_purpose',
  'adverb_spelling_prefix_po',
  'adverb_spelling_particles_hyphen',
  'adverb_spelling_reduplication',
  'adverb_spelling_together_fused',
  'adverb_homophone_napamyat_vden_dodomu',
  'adverb_homophone_zgory_nazustrich_ubik',
  'adverb_spelling_separate',
  'adverb_comparison_synthetic',
  'adverb_comparison_superlative',
  'adverb_anti_calque',
] as const;

export type AdverbMechanicsCategoryKey = (typeof ADVERB_MECHANICS_CATEGORY_KEYS)[number];

export const ADVERB_MECHANICS_INTERFERENCE_KEYS = [
  'HYPHEN_OMISSION',
  'HYPHEN_SEPARATION',
  'UNWARRANTED_HYPHEN',
  'UNWARRANTED_FUSION',
  'UNWARRANTED_SEPARATION',
  'HOMOPHONE_NOUN_PREP_CONFUSION',
  'HOMOPHONE_ADVERB_CONFUSION',
  'COMPARATIVE_COMPOUND_CALQUE',
  'COMPARATIVE_RUSSIAN_SUFFIX',
  'SUPERLATIVE_CALQUE_SAMYI',
  'SUPERLATIVE_HYPHEN_ERROR',
  'RUSSIANISM_CALQUE',
  'CORRUPTED_ADVERB_FORM',
  'INCORRECT_QUESTION_CATEGORY',
] as const;

export type AdverbMechanicsInterferenceKey = (typeof ADVERB_MECHANICS_INTERFERENCE_KEYS)[number];

export interface AdverbMechanicsDistractor {
  text: string;
  interference_key?: AdverbMechanicsInterferenceKey;
  interference_type?: AdverbMechanicsInterferenceKey;
  explanation: {
    ua: string;
    en: string;
  };
}

export interface PracticeAdverbMechanicsCard {
  id: string;
  category: AdverbMechanicsCategoryKey;
  prompt: string;
  target_token: string;
  correct_answer: string;
  options: string[];
  distractors: AdverbMechanicsDistractor[];
  rule_citation: string;
  rule_summary: {
    ua: string;
    en: string;
  };
}

export interface AdverbMechanicsDeckPayload {
  schema_version: string;
  title: string;
  card_count: number;
  categories: AdverbMechanicsCategoryKey[];
  cards: PracticeAdverbMechanicsCard[];
}

export interface AdverbMechanicsEvaluation {
  isCorrect: boolean;
  selectedOption: string;
  correctAnswer: string;
  feedbackUa: string;
  feedbackEn: string;
  ruleCitation: string;
  misconceptionType?: AdverbMechanicsInterferenceKey;
}

/**
 * Evaluates learner choice for adverb mechanics card and provides bilingual feedback.
 */
export function adverbMechanicsFeedbackFor(
  card: PracticeAdverbMechanicsCard,
  selectedOption: string,
): AdverbMechanicsEvaluation {
  const normalizedSelection = selectedOption.trim();
  const normalizedTarget = card.correct_answer.trim();

  if (normalizedSelection === normalizedTarget) {
    return {
      isCorrect: true,
      selectedOption: card.correct_answer,
      correctAnswer: card.correct_answer,
      feedbackUa: `Чудово! Правильно: «${card.correct_answer}». ${card.rule_summary.ua}`,
      feedbackEn: `Excellent! Correct: "${card.correct_answer}". ${card.rule_summary.en}`,
      ruleCitation: card.rule_citation,
    };
  }

  const matchedDistractor = card.distractors.find((d) => d.text.trim() === normalizedSelection);

  if (matchedDistractor) {
    const interferenceKey = matchedDistractor.interference_key || matchedDistractor.interference_type;
    return {
      isCorrect: false,
      selectedOption: matchedDistractor.text,
      correctAnswer: card.correct_answer,
      feedbackUa: `Неправильно: «${matchedDistractor.text}». ${matchedDistractor.explanation.ua} Правильна форма: «${card.correct_answer}».`,
      feedbackEn: `Incorrect: "${matchedDistractor.text}". ${matchedDistractor.explanation.en} Correct form: "${card.correct_answer}".`,
      ruleCitation: card.rule_citation,
      misconceptionType: interferenceKey,
    };
  }

  return {
    isCorrect: false,
    selectedOption: selectedOption,
    correctAnswer: card.correct_answer,
    feedbackUa: `Неправильно. Правильна форма: «${card.correct_answer}». ${card.rule_summary.ua}`,
    feedbackEn: `Incorrect. Correct form: "${card.correct_answer}". ${card.rule_summary.en}`,
    ruleCitation: card.rule_citation,
  };
}

export interface AdverbRuleResolution {
  citation: string;
  ruleUa: string;
  ruleEn: string;
}

export function resolveMannerActionRule(): AdverbRuleResolution {
  return {
    citation: 'Правопис 2019 § 41, п. 1; Академічна граматика; СУМ-20',
    ruleUa:
      "Прислівники способу дії відповідають на питання 'як?', 'яким способом?' і характеризують якість або спосіб протікання дії (напам'ять, вголос, пішки, пошепки, навпомацки). Більшість таких прислівників, утворених від прийменників та іменників, пишуться разом.",
    ruleEn:
      "Adverbs of manner answer 'how?' or 'in what manner?' and describe how an action is performed (напам'ять, вголос, пішки, пошепки, навпомацки). Most formed by fusion of prepositions and nominal stems are spelled as one word.",
  };
}

export function resolveTimeRule(): AdverbRuleResolution {
  return {
    citation: 'Правопис 2019 § 41, п. 1; Академічна граматика; СУМ-20',
    ruleUa:
      "Прислівники часу відповідають на питання 'коли?', 'відколи?', 'доки?' (вдень, влітку, щодня, зранку, допізна). Складні прислівники з префіксами в-, з-, до- та часткою що- пишуться разом.",
    ruleEn:
      "Adverbs of time answer 'when?', 'since when?', 'until when?' (вдень, влітку, щодня, зранку, допізна). Compound adverbs formed with prefixes в-, з-, до- and particle що- are spelled as one word.",
  };
}

export function resolvePlaceDirectionRule(): AdverbRuleResolution {
  return {
    citation: 'Правопис 2019 § 41, п. 1; Академічна граматика; СУМ-20',
    ruleUa:
      "Прислівники місця та напрямку відповідають на питання 'де?', 'куди?', 'звідки?' (додому, вгору, донизу, вперед, ззаду). Вони пишуться разом, коли утворені злиттям прийменників з іменниковими основами без пояснювальних слів.",
    ruleEn:
      "Adverbs of place and direction answer 'where?', 'where to?', 'where from?' (додому, вгору, донизу, вперед, ззаду). They are spelled as a single word when fused from prepositions and nominal stems without dependents.",
  };
}

export function resolveMeasureDegreeRule(): AdverbRuleResolution {
  return {
    citation: 'Правопис 2019 § 41, п. 1; Академічна граматика; СУМ-20',
    ruleUa:
      "Прислівники міри й ступеня відповідають на питання 'скільки?', 'наскільки?', 'якою мірою?' (наполовину, дощенту, зовсім, набагато, вкрай). Пишуться разом за правилом злиття прийменників з іменниками, числівниками або займенниками.",
    ruleEn:
      "Adverbs of measure and degree answer 'how much?', 'to what extent?' (наполовину, дощенту, зовсім, набагато, вкрай). They are written as one word per the fusion rule of prepositions with nouns, numerals, or pronouns.",
  };
}

export function resolveCausePurposeRule(): AdverbRuleResolution {
  return {
    citation: 'Правопис 2019 § 41, п. 1; Академічна граматика; СУМ-20',
    ruleUa:
      "Прислівники причини й мети відповідають на питання 'чому?', 'з якої причини?', 'навіщо?', 'з якою метою?' (зопалу, згарячу, навмисне, напоказ, наперекір). Зрощені префіксально-суфіксальні форми пишуться разом.",
    ruleEn:
      "Adverbs of cause and purpose answer 'why?', 'for what reason?', 'for what purpose?' (зопалу, згарячу, навмисне, напоказ, наперекір). Fused prefixal-suffixal derivatives are written as one word.",
  };
}

export function resolvePrefixPoRule(): AdverbRuleResolution {
  return {
    citation: 'Правопис 2019 § 41, п. 2 а; СУМ-20',
    ruleUa:
      'Прислівники з префіксом по-, утворені від прикметників і займенників із суфіксами -ому, -ему, -и, -ськи, -цьки, пишуться через дефіс: по-українськи, по-новому, по-батьківськи, по-моєму, по-дитячому.',
    ruleEn:
      'Adverbs with the prefix по- formed from adjectives and pronouns with suffixes -ому, -ему, -и, -ськи, -цьки are hyphenated: по-українськи, по-новому, по-батьківськи, по-моєму, по-дитячому.',
  };
}

export function resolveParticlesHyphenRule(): AdverbRuleResolution {
  return {
    citation: 'Правопис 2019 § 41, п. 2 б; СУМ-20',
    ruleUa:
      'Прислівники з частками будь-, -небудь, казна-, хтозна-, бозна-, -таки, -то пишуться через дефіс: будь-де, як-небудь, хтозна-як, казна-коли, бозна-як, так-таки.',
    ruleEn:
      'Adverbs with particles будь-, -небудь, казна-, хтозна-, бозна-, -таки, -то are hyphenated: будь-де, як-небудь, хтозна-як, казна-коли, бозна-як, так-таки.',
  };
}

export function resolveReduplicationRule(): AdverbRuleResolution {
  return {
    citation: 'Правопис 2019 § 41, п. 2 в; СУМ-20',
    ruleUa:
      'Прислівники, утворені повторенням того самого слова, поєднанням синонімів або антонімів, а також парних слів з прийменником між ними, пишуться через дефіс: віч-на-віч, пліч-о-пліч, тишком-нишком, ледве-ледве, давним-давно.',
    ruleEn:
      'Adverbs formed by reduplication of identical words, synonymous pairs, or identical roots connected by a preposition are hyphenated: віч-на-віч, пліч-о-пліч, тишком-нишком, ледве-ледве, давним-давно.',
  };
}

export function resolveTogetherFusedRule(): AdverbRuleResolution {
  return {
    citation: 'Правопис 2019 § 41, п. 1; СУМ-20',
    ruleUa:
      'Складні прислівники, утворені злиттям прийменників з іменниками, числівниками чи займенниками, коли вони втратили значення окремих частин мови, пишуться разом: спочатку, вперше, спідлоба, навшпиньки, насторожі.',
    ruleEn:
      'Compound adverbs formed by the complete fusion of prepositions with nominal bases, where individual syntactic independence is lost, are spelled as one word: спочатку, вперше, спідлоба, навшпиньки, насторожі.',
  };
}

export function resolveHomophone1Rule(): AdverbRuleResolution {
  return {
    citation: 'Правопис 2019 § 41, п. 1, п. 3; СУМ-20',
    ruleUa:
      "Слід чітко розрізняти прислівники, що пишуться разом, та омонімічні іменникові сполуки з прийменниками, що пишуться окремо: вивчити напам'ять (як?) vs подарувати на пам'ять (на що? на пам'ять про подію); спати вдень (коли?) vs у цей пам'ятний день (у що?); іти додому (куди?) vs підійти до дому лісника (до якої споруди?).",
    ruleEn:
      "Distinguish fused adverbs (spelled as one word) from homophonous prepositional phrases with nouns (spelled separately): вивчити напам'ять (manner) vs на пам'ять (as a keepsake); спати вдень (time) vs в день народження (on the day of); іти додому (direction) vs підійти до дому (to the house of).",
  };
}

export function resolveHomophone2Rule(): AdverbRuleResolution {
  return {
    citation: 'Правопис 2019 § 41, п. 1, п. 3; СУМ-20',
    ruleUa:
      'Прислівники напрямку пишуться разом (згори вниз, бігти назустріч, відійти вбік), тоді як сполуки прийменника з іменником за наявності залежних слів пишуться окремо (спускатися з високої гори, вирушити на зустріч із друзями, поглянути у правий бік вулиці).',
    ruleEn:
      'Directional adverbs are written as one word (згори, назустріч, вбік), whereas preposition + noun phrases with dependent words are written separately (з гори, на зустріч, у бік).',
  };
}

export function resolveSeparatePhrasesRule(): AdverbRuleResolution {
  return {
    citation: 'Правопис 2019 § 41, п. 3; СУМ-20',
    ruleUa:
      'Прислівникові сполучення, утворені з прийменника та іменника, що зберігають відмінкову самостійність, пишуться окремо: на жаль, до речі, без сумніву, день у день, до побачення. Написання їх разом (*нажаль, *доречі, *допобачення) є грубою помилкою.',
    ruleEn:
      'Adverbial expressions consisting of a preposition and a noun that retain grammatical independence are spelled separately: на жаль, до речі, без сумніву, день у день, до побачення. Writing them as single words (*нажаль, *доречі) is a serious error.',
  };
}

export function resolveComparisonSyntheticRule(): AdverbRuleResolution {
  return {
    citation: 'Правопис 2019 § 110; СУМ-20',
    ruleUa:
      "Вищий ступінь порівняння якісних прислівників на -о, -е утворюється за допомогою суфіксів -ше, -іше (швидко -> швидше, тепло -> тепліше, глибоко -> глибше) або суплетивно (добре/гарно -> краще, погано -> гірше). Змішування слів 'більш' із синтетичною формою (*більш краще) є неприпустимим.",
    ruleEn:
      "The comparative degree of qualitative adverbs ending in -о, -е is formed synthetically with suffixes -ше, -іше (швидше, тепліше, глибше) or suppletively (краще, гірше). Mixing 'більш' with synthetic forms (*більш краще) is grammatically invalid.",
  };
}

export function resolveComparisonSuperlativeRule(): AdverbRuleResolution {
  return {
    citation: 'Правопис 2019 § 111; СУМ-20',
    ruleUa:
      "Найвищий ступінь порівняння утворюється додаванням префікса най- до форми вищого ступеня (найкраще, найвище). Значення можна посилити префіксами як-, що-, які пишуться разом: якнайшвидше, щонайдовше. Використання частки 'самий' (*самий краще) є російською калькою.",
    ruleEn:
      "The superlative degree is formed by prefixing най- to the comparative form (найкраще, найвище). Intensifying prefixes як-, що- are attached as single words (якнайшвидше, щонайдовше). Using 'самий' (*самий краще) is an ungrammatical calque.",
  };
}

export function resolveAntiCalqueRule(): AdverbRuleResolution {
  return {
    citation: 'Правопис 2019; Антоненко-Давидович «Як ми говоримо»; СУМ-20',
    ruleUa:
      "Слід уникати калькованих канцеляризмів та суржику: вживайте 'насамперед / передусім' замість 'в першу чергу'; 'навряд чи' замість 'вряд ли'; 'переважно / здебільшого' замість 'в основному'; 'принаймні' замість 'по крайній мірі'; 'у крайньому разі' замість 'в крайньому випадку'.",
    ruleEn:
      "Avoid Russian bureaucratic calques and Surzhyk: use 'насамперед' instead of *в першу чергу*; 'навряд чи' instead of *вряд ли*; 'переважно' instead of *в основному*; 'принаймні' instead of *по крайній мірі*; 'у крайньому разі' instead of *в крайньому випадку*.",
  };
}
