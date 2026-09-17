/**
 * Ukrainian Euphony & Stem Alternations Model and Evaluation Engine.
 *
 * Implements Ukrainian Pravopys 2019 (§ 20–24, § 70–74):
 * - Preposition euphony: у vs в, з vs із vs зі
 * - Conjunction euphony: і vs й
 * - Vowel alternations: [о], [е] <-> [і] in open vs closed syllables
 * - Second palatalization: г -> з', к -> ц', х -> с' in Dative/Locative
 * - First palatalization: г -> ж, к -> ч, х -> ш in Vocative
 * - Verb iotation: Epenthetic -л- and dental shifts in 1st person singular
 */

export type EuphonyCategoryKey =
  | 'preposition_u_v'
  | 'conjunction_i_y'
  | 'preposition_z_iz_zi'
  | 'vowel_shift_o_e_i'
  | 'second_palatalization'
  | 'first_palatalization_vocative'
  | 'verb_iotation';

export type EuphonyInterferenceKey =
  | 'hiatus_consonant_clash'
  | 'hiatus_vowel_clash'
  | 'sibilant_cluster_clash'
  | 'non_alternating_stem'
  | 'first_for_second_palatalization'
  | 'missing_epenthetic_l'
  | 'non_alternating_dental'
  | 'russian_closed_syllable_calque';

export interface EuphonyDistractor {
  form: string;
  interferenceType: EuphonyInterferenceKey;
  explanationUa: string;
  explanationEn: string;
}

export interface PracticeEuphonyCard {
  id: string;
  category: EuphonyCategoryKey;
  promptUa: string;
  promptEn: string;
  targetDisplay: string;
  correctAnswer: string;
  options: string[];
  distractors: EuphonyDistractor[];
  pedagogicalRuleUa: string;
  pedagogicalRuleEn: string;
  pravopysRef: string;
}

export interface EuphonyFeedback {
  isCorrect: boolean;
  explanationUa: string;
  explanationEn: string;
  ruleUa: string;
  ruleEn: string;
  interferenceType?: EuphonyInterferenceKey;
}

const VOWELS = new Set('аеєиіїоуюя');
const SIBILANTS = new Set('жчшщзсц');
const SIBILANT_CLUSTERS = new Set([
  'зб',
  'зд',
  'зг',
  'зм',
  'зн',
  'зр',
  'зв',
  'зл',
  'сн',
  'ст',
  'ск',
  'сп',
  'см',
  'шв',
  'шк',
  'шп',
]);

export function endsWithVowel(word: string): boolean {
  const clean = word.replace(/[.,;:!?»"')\s]/g, '');
  return clean.length > 0 && VOWELS.has(clean[clean.length - 1].toLowerCase());
}

export function startsWithVowel(word: string): boolean {
  const clean = word.replace(/[«"'((\s]/g, '');
  return clean.length > 0 && VOWELS.has(clean[0].toLowerCase());
}

/**
 * Determine correct preposition У vs В per Правопис 2019 (§ 20–22).
 */
export function resolveUVRules(
  prevWord: string | null,
  nextWord: string,
): { choice: 'у' | 'в'; ruleUa: string; ruleEn: string } {
  const nextClean = nextWord.replace(/[«"'((\s]/g, '').toLowerCase();
  const prevClean = prevWord ? prevWord.replace(/[.,;:!?»"')\s]/g, '').toLowerCase() : null;

  // Before в, ф or clusters with в/ф
  if (
    nextClean.startsWith('в') ||
    nextClean.startsWith('ф') ||
    nextClean.startsWith('льв') ||
    nextClean.startsWith('хв') ||
    nextClean.startsWith('св') ||
    nextClean.startsWith('тв')
  ) {
    return {
      choice: 'у',
      ruleUa: 'Перед в, ф або буквосполученнями льв, хв, св, тв завжди вживається «у».',
      ruleEn:
        "Always use 'у' before 'в', 'ф', or clusters like 'льв', 'хв' to avoid consonant clash.",
    };
  }

  // Beginning of sentence or after pause
  if (!prevClean) {
    if (startsWithVowel(nextWord)) {
      return {
        choice: 'в',
        ruleUa: 'На початку речення перед голосним уживається «в».',
        ruleEn: "At the start of a sentence before a vowel, use 'в'.",
      };
    }
    return {
      choice: 'у',
      ruleUa: 'На початку речення перед приголосним уживається «у».',
      ruleEn: "At the start of a sentence before a consonant, use 'у'.",
    };
  }

  // Between consonants
  if (!endsWithVowel(prevClean) && !startsWithVowel(nextClean)) {
    return {
      choice: 'у',
      ruleUa: 'Між приголосними завжди вживається «у» для милозвучності.',
      ruleEn: "Between consonants, use 'у' for euphony.",
    };
  }

  // Between vowels
  if (endsWithVowel(prevClean) && startsWithVowel(nextClean)) {
    return {
      choice: 'в',
      ruleUa: 'Між голосними вживається «в» для уникнення збігу голосних.',
      ruleEn: "Between vowels, use 'в' to prevent vowel hiatus.",
    };
  }

  // After vowel before consonant
  if (endsWithVowel(prevClean) && !startsWithVowel(nextClean)) {
    return {
      choice: 'в',
      ruleUa: 'Після голосного перед приголосним уживається «в».',
      ruleEn: "After a vowel before a consonant, use 'в'.",
    };
  }

  // After consonant before vowel
  return {
    choice: 'в',
    ruleUa: 'Після приголосного перед голосним уживається «в».',
    ruleEn: "After a consonant before a vowel, use 'в'.",
  };
}

/**
 * Determine correct conjunction І vs Й per Правопис 2019 (§ 23).
 */
export function resolveIYRules(
  prevWord: string | null,
  nextWord: string,
): { choice: 'і' | 'й'; ruleUa: string; ruleEn: string } {
  const nextClean = nextWord.replace(/[«"'((\s]/g, '').toLowerCase();
  const prevClean = prevWord ? prevWord.replace(/[.,;:!?»"')\s]/g, '').toLowerCase() : null;

  if (!prevClean) {
    return {
      choice: 'і',
      ruleUa: 'На початку речення зазвичай уживається сполучник «і».',
      ruleEn: "At the beginning of a sentence, use 'і'.",
    };
  }

  if (!endsWithVowel(prevClean) && !startsWithVowel(nextClean)) {
    return {
      choice: 'і',
      ruleUa: 'Між приголосними вживається сполучник «і».',
      ruleEn: "Between consonants, use 'і'.",
    };
  }

  if (endsWithVowel(prevClean) && startsWithVowel(nextClean)) {
    return {
      choice: 'й',
      ruleUa: 'Між голосними вживається сполучник «й».',
      ruleEn: "Between vowels, use 'й'.",
    };
  }

  if (endsWithVowel(prevClean) && !startsWithVowel(nextClean)) {
    return {
      choice: 'й',
      ruleUa: 'Після голосного перед приголосним уживається сполучник «й».',
      ruleEn: "After a vowel before a consonant, use 'й'.",
    };
  }

  return {
    choice: 'і',
    ruleUa: 'Після приголосного перед голосним уживається «і».',
    ruleEn: "After a consonant before a vowel, use 'і'.",
  };
}

/**
 * Determine correct preposition З vs ІЗ vs ЗІ per Правопис 2019 (§ 24).
 */
export function resolveZIzZiRules(
  prevWord: string | null,
  nextWord: string,
): { choice: 'з' | 'із' | 'зі'; ruleUa: string; ruleEn: string } {
  const nextClean = nextWord.replace(/[«"'((\s]/g, '').toLowerCase();
  const prevClean = prevWord ? prevWord.replace(/[.,;:!?»"')\s]/g, '').toLowerCase() : null;

  if (nextClean.startsWith('мн')) {
    return {
      choice: 'зі',
      ruleUa: 'Перед займенником «мною» завжди вживається «зі».',
      ruleEn: "Before 'мною', always use 'зі'.",
    };
  }

  for (const cluster of SIBILANT_CLUSTERS) {
    if (nextClean.startsWith(cluster)) {
      return {
        choice: 'зі',
        ruleUa: 'Перед збігом приголосних із свистячими чи шиплячими уживається «зі».',
        ruleEn: 'Before sibilant consonant clusters, use «зі».',
      };
    }
  }

  if (nextClean.length >= 2 && SIBILANTS.has(nextClean[0]) && !VOWELS.has(nextClean[1])) {
    return {
      choice: 'зі',
      ruleUa: 'Перед сполученням кількох приголосних уживається «зі».',
      ruleEn: 'Before consonant clusters, use «зі».',
    };
  }

  if (startsWithVowel(nextClean)) {
    return {
      choice: 'з',
      ruleUa: 'Перед голосним завжди вживається «з».',
      ruleEn: "Before a vowel, always use 'з'.",
    };
  }

  if (prevClean && !endsWithVowel(prevClean) && SIBILANTS.has(nextClean[0])) {
    return {
      choice: 'із',
      ruleUa: 'Між свистячими/шиплячими після приголосного вживається «із».',
      ruleEn: 'Between sibilants after a consonant, use «із».',
    };
  }

  return {
    choice: 'з',
    ruleUa: 'Перед поодиноким приголосним уживається «з».',
    ruleEn: "Before a single consonant, use 'з'.",
  };
}

/**
 * Generate targeted pedagogical feedback for a user's selection on a euphony card.
 */
export function euphonyFeedbackFor(
  card: PracticeEuphonyCard,
  selectedOption: string,
): EuphonyFeedback {
  const normSelected = selectedOption.trim().toLowerCase();
  const normCorrect = card.correctAnswer.trim().toLowerCase();

  if (normSelected === normCorrect) {
    return {
      isCorrect: true,
      explanationUa: `Правильно! «${card.correctAnswer}» — правильний варіант.`,
      explanationEn: `Correct! '${card.correctAnswer}' is the correct choice.`,
      ruleUa: card.pedagogicalRuleUa,
      ruleEn: card.pedagogicalRuleEn,
    };
  }

  const distractor = card.distractors.find((d) => d.form.trim().toLowerCase() === normSelected);

  if (distractor) {
    return {
      isCorrect: false,
      explanationUa: distractor.explanationUa,
      explanationEn: distractor.explanationEn,
      ruleUa: card.pedagogicalRuleUa,
      ruleEn: card.pedagogicalRuleEn,
      interferenceType: distractor.interferenceType,
    };
  }

  return {
    isCorrect: false,
    explanationUa: `Неправильно. Правильний варіант: «${card.correctAnswer}».`,
    explanationEn: `Incorrect. The correct answer is '${card.correctAnswer}'.`,
    ruleUa: card.pedagogicalRuleUa,
    ruleEn: card.pedagogicalRuleEn,
  };
}
