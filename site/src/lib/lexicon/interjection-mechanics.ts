/**
 * Ukrainian Interjection and Onomatopoeia Deep Mechanics Practice Engine (Вигук та Звуконаслідування).
 *
 * Implements Ukrainian Pravopys 2019 (§ 46) and Academic Grammar rules for:
 *   1. Semantic Classification:
 *      - Emotional Interjections (емоційні вигуки):
 *        * Joy, delight, surprise, admiration (ура, ах, ох, леле, овва)
 *        * Sorrow, grief, pain, fear, indignation (ой, ай, лишенько, пхе, тьху)
 *      - Volitional / Imperative Interjections (спонукальні / волевиявні вигуки):
 *        * Commands, calls to action, prohibitions, silence (гайда, марш, годі, геть, цить)
 *        * Animal calls and driving (киць-киць, киш, тпру, но, вйо)
 *      - Speech Etiquette Formulas (вигуки мовленнєвого етикету per § 46, п. 2):
 *        * Greetings and farewells (добрий день, добрий вечір, до побачення, на добраніч, бувайте)
 *        * Gratitude, apology, politeness (будь ласка, дякую, пробачте, перепрошую, вибачте)
 *   2. Onomatopoeic Words (звуконаслідувальні слова per § 46, п. 1, а)):
 *      - Inanimate nature, water, machinery, clocks, bells (дзень-дзелень, тік-так, крап-крап, хлюп-хлюп, цок-цок)
 *      - Animals and birds (гав-гав, няв-няв, ку-ку, кар-кар, ква-ква)
 *   3. Orthography of Interjections per § 46:
 *      - Hyphenated spelling (§ 46, п. 1):
 *        * Repeated or echoed interjections and onomatopoeias (ой-ой-ой, ха-ха-ха, ай-яй-яй, дзень-дзелень, тук-тук) per п. 1, а)
 *        * Interjections with enclitic particles -бо, -но, -то (годі-бо, ну-бо, давай-но) per п. 1, б)
 *        * Fixed idioms (їй-богу, їй-право) per п. 1, в)
 *      - Separate spelling (§ 46, п. 2):
 *        * Multi-word interjections & etiquette expressions (будь ласка, до побачення, на добраніч, о господи, от тобі й маєш)
 *   4. Syntax & Punctuation Rules:
 *      - Comma isolation for calm intonation: «Ох, як солодко пахне...»
 *      - Exclamation mark isolation for strong expressive stress: «Леле! Що це за диво?»
 *      - Crucial Diagnostic: Vocative particle О / Ой before an address takes NO comma:
 *        «О краю мій, люблю тебе безтямно!» (particle: no comma between «о» and «краю»)
 *        «Ой Дніпре, мій брате широкий!» (particle: no comma between «ой» and «Дніпре»)
 *        vs Independent emotional interjection requiring comma:
 *        «О, краю мій, як довго я тебе шукав!» (interjection with pause: comma required)
 */

export const INTERJECTION_MECHANICS_CATEGORY_KEYS = [
  'interjection_emotional_positive',
  'interjection_emotional_negative',
  'interjection_volitional_imperative',
  'interjection_volitional_animal',
  'interjection_etiquette_greeting_farewell',
  'interjection_etiquette_gratitude_apology',
  'interjection_onomatopoeia_nature_mechanics',
  'interjection_onomatopoeia_animal_sounds',
  'interjection_spelling_hyphen_repeated',
  'interjection_spelling_particles_hyphen',
  'interjection_spelling_multiword_separate',
  'interjection_syntax_punctuation_particle',
] as const;

export type InterjectionMechanicsCategoryKey = (typeof INTERJECTION_MECHANICS_CATEGORY_KEYS)[number];

export const INTERJECTION_MECHANICS_INTERFERENCE_KEYS = [
  'HYPHEN_OMISSION',
  'HYPHEN_SEPARATION',
  'UNWARRANTED_HYPHEN',
  'UNWARRANTED_FUSION',
  'PARTICLE_HYPHEN_OMISSION',
  'IDIOM_HYPHEN_OMISSION',
  'PUNCTUATION_COMMA_OMISSION',
  'PUNCTUATION_UNWARRANTED_COMMA_PARTICLE',
  'PUNCTUATION_EXCLAMATION_OMISSION',
  'PUNCTUATION_WRONG_DELIMITER',
  'RUSSIANISM_CALQUE',
  'INCORRECT_EMOTIONAL_TONE',
  'INCORRECT_VOLITIONAL_COMMAND',
  'INCORRECT_SOUND_SOURCE',
  'CORRUPTED_ADVERB_FORM',
] as const;

export type InterjectionMechanicsInterferenceKey = (typeof INTERJECTION_MECHANICS_INTERFERENCE_KEYS)[number];

export interface InterjectionMechanicsDistractor {
  text: string;
  interference_key?: InterjectionMechanicsInterferenceKey;
  interference_type?: InterjectionMechanicsInterferenceKey;
  explanation: {
    ua: string;
    en: string;
  };
}

export interface PracticeInterjectionMechanicsCard {
  id: string;
  category: InterjectionMechanicsCategoryKey;
  prompt: string;
  target_token: string;
  correct_answer: string;
  options: string[];
  distractors: InterjectionMechanicsDistractor[];
  rule_citation: string;
  rule_summary: {
    ua: string;
    en: string;
  };
}

export interface InterjectionMechanicsDeckPayload {
  schema_version: string;
  title: string;
  card_count: number;
  categories: InterjectionMechanicsCategoryKey[];
  cards: PracticeInterjectionMechanicsCard[];
}

export interface InterjectionMechanicsEvaluation {
  isCorrect: boolean;
  selectedOption: string;
  correctAnswer: string;
  feedbackUa: string;
  feedbackEn: string;
  ruleCitation: string;
  misconceptionType?: InterjectionMechanicsInterferenceKey;
}

export interface InterjectionRuleResolution {
  citation: string;
  ruleUa: string;
  ruleEn: string;
}

export function resolveEmotionalPositiveRule(): InterjectionRuleResolution {
  return {
    citation: 'Правопис 2019 § 46; Академічна граматика; СУМ-20',
    ruleUa:
      'Емоційні вигуки виражають почуття радості, задоволення, здивування, захоплення або полегшення (ура, ах, ох, леле, овва, слава богу, чудово). Вони не називають почуттів, а лише безпосередньо сигналізують про емоційний стан мовця.',
    ruleEn:
      'Emotional interjections express feelings of joy, delight, surprise, admiration, or relief (ура, ах, ох, леле, овва, слава богу, чудово). They do not name emotions but directly signal the speaker’s emotional state.',
  };
}

export function resolveEmotionalNegativeRule(): InterjectionRuleResolution {
  return {
    citation: 'Правопис 2019 § 46; Академічна граматика; СУМ-20',
    ruleUa:
      'Емоційні вигуки негативного спектра передають сум, біль, жаль, переляк, обурення, огиду або досаду (ой, ай, лишенько, пхе, тьху, жаль). На письмі вони виділяються комами або знаком оклику.',
    ruleEn:
      'Negative emotional interjections convey sorrow, pain, grief, fear, indignation, disgust, or vexation (ой, ай, лишенько, пхе, тьху, жаль). In writing, they are set off by commas or an exclamation mark.',
  };
}

export function resolveVolitionalImperativeRule(): InterjectionRuleResolution {
  return {
    citation: 'Правопис 2019 § 46; Академічна граматика; СУМ-20',
    ruleUa:
      'Спонукальні (волевиявні) вигуки виражають заклик до дії, наказ, заборону, вимогу тиші або привертання уваги (гайда, марш, годі, геть, цить, ша, агов, вйо). Вони спонукають адресата до певної реакції.',
    ruleEn:
      'Volitional (imperative) interjections express calls to action, commands, prohibitions, demands for silence, or attention calls (гайда, марш, годі, геть, цить, ша, агов, вйо). They prompt the addressee into a specific action.',
  };
}

export function resolveVolitionalAnimalRule(): InterjectionRuleResolution {
  return {
    citation: 'Правопис 2019 § 46; Академічна граматика; СУМ-20',
    ruleUa:
      'Волевиявні вигуки для тварин слугують для підкликання або відгону свійських тварин і птахів (киць-киць — підкликання котів, киш — відгін птахів, тпру — зупинка коней, но — рух коней уперед, вйо — поганяння упряжі).',
    ruleEn:
      'Volitional animal interjections serve to call or drive domestic animals and birds (киць-киць for cats, киш for driving birds, тпру to halt horses, но to urge horses forward, вйо to urge draught animals).',
  };
}

export function resolveEtiquetteGreetingFarewellRule(): InterjectionRuleResolution {
  return {
    citation: 'Правопис 2019 § 46, п. 2; СУМ-20',
    ruleUa:
      'Формули мовленнєвого етикету для привітання та прощання (добрий день, добрий вечір, до побачення, на добраніч, бувайте, ласкаво просимо) функціонують як вигуки. Багатослівні етикетні сполуки пишуться окремо per § 46, п. 2.',
    ruleEn:
      'Speech etiquette formulas for greetings and farewells (добрий день, добрий вечір, до побачення, на добраніч, бувайте, ласкаво просимо) function as interjections. Multi-word etiquette phrases are spelled separately per § 46, p. 2.',
  };
}

export function resolveEtiquetteGratitudeApologyRule(): InterjectionRuleResolution {
  return {
    citation: 'Правопис 2019 § 46, п. 2; СУМ-20',
    ruleUa:
      'Етикетні вигуки вдячності, вибачення та ввічливості (будь ласка, дякую, щиро дякую, пробачте, перепрошую, вибачте) регулюють соціальну взаємодію. Сполука «будь ласка» пишеться окремо без дефіса per § 46, п. 2.',
    ruleEn:
      'Etiquette interjections of gratitude, apology, and politeness (будь ласка, дякую, щиро дякую, пробачте, перепрошую, вибачте) regulate social interaction. The polite phrase \'будь ласка\' is spelled separately without hyphen per § 46, p. 2.',
  };
}

export function resolveOnomatopoeiaNatureMechanicsRule(): InterjectionRuleResolution {
  return {
    citation: 'Правопис 2019 § 46, п. 1, а); СУМ-20',
    ruleUa:
      'Звуконаслідувальні слова відтворюють звуки неживої природи, води, механізмів, годинників чи дзвоників (дзень-дзелень, тік-так, крап-крап, хлюп-хлюп, цок-цок). Повторювані або відлунні звуконаслідування пишуться через дефіс per § 46, п. 1, а).',
    ruleEn:
      'Onomatopoeic words imitate sounds of inanimate nature, water, machinery, clocks, or bells (дзень-дзелень, тік-так, крап-крап, хлюп-хлюп, цок-цок). Repeated or echoic onomatopoeias are spelled with a hyphen per § 46, p. 1, a).',
  };
}

export function resolveOnomatopoeiaAnimalSoundsRule(): InterjectionRuleResolution {
  return {
    citation: 'Правопис 2019 § 46, п. 1, а); СУМ-20',
    ruleUa:
      'Звуконаслідування голосів тварин і птахів імітують гавкіт, нявчання, кування зозулі, каркання, квакання (гав-гав, няв-няв, ку-ку, кар-кар, ква-ква). Повторювані звуки пишуться через дефіс per § 46, п. 1, а).',
    ruleEn:
      'Animal and bird sound onomatopoeias imitate barking, meowing, cuckoo calls, croaking, or quacking (гав-гав, няв-няв, ку-ку, кар-кар, ква-ква). Repeated sounds are hyphenated per § 46, p. 1, a).',
  };
}

export function resolveSpellingHyphenRepeatedRule(): InterjectionRuleResolution {
  return {
    citation: 'Правопис 2019 § 46, п. 1, а); СУМ-20',
    ruleUa:
      'Через дефіс пишуться повторювані або відлунні вигуки та звуконаслідувальні слова: ой-ой-ой, ха-ха-ха, ай-яй-яй, дзень-дзелень, тук-тук per § 46, п. 1, а).',
    ruleEn:
      'Repeated or echoic interjections and onomatopoeic words are spelled with a hyphen per § 46, p. 1, a): ой-ой-ой, ха-ха-ха, ай-яй-яй, дзень-дзелень, тук-тук.',
  };
}

export function resolveSpellingParticlesHyphenRule(): InterjectionRuleResolution {
  return {
    citation: 'Правопис 2019 § 46, п. 1, б), в); СУМ-20',
    ruleUa:
      'Через дефіс пишуться вигуки з постпозитивними частками -бо, -но, -то (годі-бо, ну-бо, давай-но) per § 46, п. 1, б), а також усталені вигукові ідіоми їй-богу, їй-право per § 46, п. 1, в).',
    ruleEn:
      'Interjections with enclitic particles -бо, -но, -то (годі-бо, ну-бо, давай-но) are spelled with a hyphen per § 46, p. 1, b), as are fixed interjection idioms їй-богу, їй-право per § 46, p. 1, c).',
  };
}

export function resolveSpellingMultiwordSeparateRule(): InterjectionRuleResolution {
  return {
    citation: 'Правопис 2019 § 46, п. 2; СУМ-20',
    ruleUa:
      'Окремо пишуться складні вигуки та мовленнєві етикетні звороти, що складаються з кількох слів: будь ласка, до побачення, на добраніч, о господи, от тобі й маєш per § 46, п. 2. Написання через дефіс або разом є грубою орфографічною помилкою.',
    ruleEn:
      'Multi-word interjections and speech etiquette phrases consisting of several words are spelled separately: будь ласка, до побачення, на добраніч, о господи, от тобі й маєш per § 46, p. 2. Writing them with hyphens or fused is an orthographic error.',
  };
}

export function resolveSyntaxPunctuationParticleRule(): InterjectionRuleResolution {
  return {
    citation: 'Правопис 2019 § 46; Академічний синтаксис; Авраменко § 88',
    ruleUa:
      'Вигуки відокремлюються комами або знаком оклику. Проте слова «о», «ой», ужиті перед звертанням як підсилювальні або кличні частки, НЕ відокремлюються комою від наступного іменника: «О краю мій!», «Ой Дніпре мій!». Якщо ж «о», «ой» є самостійними емоційними вигуками, кома ставиться: «О, краю мій, як довго я тебе шукав!» per § 46.',
    ruleEn:
      'Interjections are set off by commas or an exclamation mark. However, words \'о\', \'ой\' used before an address as intensifying or vocative particles are NOT separated by a comma from the following noun: \'О краю мій!\', \'Ой Дніпре мій!\'. If \'о\', \'ой\' are independent emotional interjections, a comma is required: \'О, краю мій, як довго...\' per § 46.',
  };
}

/**
 * Evaluates learner choice for interjection mechanics card and provides bilingual feedback.
 */
export function interjectionMechanicsFeedbackFor(
  card: PracticeInterjectionMechanicsCard,
  selectedOption: string,
): InterjectionMechanicsEvaluation {
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
