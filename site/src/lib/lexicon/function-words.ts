/**
 * Ukrainian Function Words Practice Engine (Службові частини мови).
 *
 * Implements Ukrainian Pravopys 2019 (§§ 42–44) and Academic Grammar rules for:
 *   1. Prepositions (Прийменники):
 *      - Hyphenated with з-/із- (§ 42, п. 1: з-під, з-за, із-за, з-поміж, з-понад)
 *      - Solid compounds (§ 42, п. 2: посеред, задля, заради, внаслідок, напередодні)
 *      - Multi-word locutions (§ 42, п. 3: згідно з, відповідно до, під час)
 *      - Anti-calque & government norms (по vs о/з/за/на, завдяки vs через, протягом vs на протязі)
 *   2. Conjunctions (Сполучники):
 *      - Homophone disambiguation (§ 43: проте/зате vs про те/за те, щоб vs що б,
 *        якби vs як би, якщо vs як що, також/теж vs так же/те ж)
 *   3. Particles (Частки):
 *      - Orthography of не and ні (§ 44, п. 1: разом vs окремо for nouns, adjectives,
 *        verbs, gerunds, participles with or without dependents, contrast with 'а')
 *      - Enclitics and prefixes (§ 44, п. 2: -бо, -но, -то, -от, -таки vs таки пішов;
 *        будь-, казна-, хтозна- vs будь у кого)
 */

export type FunctionWordCategoryKey =
  | 'preposition_hyphenated'
  | 'preposition_compound_solid'
  | 'preposition_locution_separate'
  | 'preposition_government_po'
  | 'preposition_zavdyaky_vs_cherez'
  | 'preposition_protyahom_vs_na_protyazi'
  | 'conjunction_prote_zate'
  | 'conjunction_shchob'
  | 'conjunction_yakby'
  | 'conjunction_yakshcho'
  | 'conjunction_takozh_tezh'
  | 'particle_ne_solid'
  | 'particle_ne_contrast_separate'
  | 'particle_ne_verb_separate'
  | 'particle_ne_participle'
  | 'particle_hyphenated_enclitics'
  | 'particle_prefix_split';

export type FunctionWordInterferenceKey =
  | 'missing_hyphen_preposition'
  | 'false_separate_preposition'
  | 'false_solid_preposition'
  | 'false_hyphen_preposition'
  | 'false_solid_locution'
  | 'false_hyphen_locution'
  | 'russian_calque_po'
  | 'russian_calque_general'
  | 'lexical_semantic_confusion'
  | 'mismatched_causal_consequence'
  | 'air_draft_calque_for_duration'
  | 'homophone_conjunction_for_pronoun'
  | 'homophone_pronoun_for_conjunction'
  | 'homophone_adverb_for_conjunction'
  | 'false_hyphen_conjunction'
  | 'false_solid_ne_contrast'
  | 'false_separate_ne_noun_adj'
  | 'false_solid_ne_verb'
  | 'false_solid_ne_participle_with_dependents'
  | 'false_separate_ne_participle_isolated'
  | 'missing_hyphen_particle'
  | 'false_hyphen_particle'
  | 'false_hyphen_prepositional_split'
  | 'false_solid_particle'
  | 'false_hyphen_inverted_taky';

export interface FunctionWordDistractor {
  form: string;
  interferenceType: FunctionWordInterferenceKey;
  explanationUa: string;
  explanationEn: string;
}

export interface PracticeFunctionWordCard {
  id: string;
  category: FunctionWordCategoryKey;
  cefrLevel: string;
  prompt: string;
  fullSentence: string;
  sentenceBefore: string;
  sentenceAfter: string;
  correctAnswer: string;
  options: string[];
  distractors: FunctionWordDistractor[];
  ruleCitation: string;
  ruleSummary: {
    uk: string;
    en: string;
  };
}

export interface FunctionWordFeedback {
  isCorrect: boolean;
  explanationUa: string;
  explanationEn: string;
  ruleCitation: string;
  ruleUa: string;
  ruleEn: string;
  interferenceType?: FunctionWordInterferenceKey;
}

/**
 * Determine if a compound preposition requires a hyphen per Правопис 2019 (§ 42, п. 1 та 2).
 */
export function resolvePrepositionHyphenationRule(prep: string): {
  requiresHyphen: boolean;
  ruleUa: string;
  ruleEn: string;
} {
  const norm = prep.trim().toLowerCase();
  if (norm.startsWith('з-') || norm.startsWith('із-')) {
    return {
      requiresHyphen: true,
      ruleUa:
        'Складні прийменники з першою частиною «з-», «із-» пишуться через дефіс: з-під, з-за, із-за, з-поміж (Правопис 2019, § 42, п. 2).',
      ruleEn:
        'Compound prepositions with initial z-/iz- are hyphenated: з-під, з-за, із-за, з-поміж (Pravopys 2019, § 42, item 2).',
    };
  }
  return {
    requiresHyphen: false,
    ruleUa:
      'Складні прийменники без «з-», «із-» пишуться разом: посеред, задля, внаслідок (Правопис 2019, § 42, п. 1).',
    ruleEn:
      'Compound prepositions without initial z-/iz- are written solid: посеред, задля, внаслідок (Pravopys 2019, § 42, item 1).',
  };
}

/**
 * Determine correct causal preposition (завдяки vs через) based on semantic polarity.
 */
export function resolveCausalPrepositionRule(isPositiveFactor: boolean): {
  choice: 'завдяки' | 'через';
  ruleUa: string;
  ruleEn: string;
} {
  if (isPositiveFactor) {
    return {
      choice: 'завдяки',
      ruleUa:
        '«Завдяки» вживаємо лише з давальним відмінком для вираження позитивних, сприятливих чинників.',
      ruleEn:
        "Use 'завдяки' (+ Dative) exclusively for positive or favorable factors.",
    };
  }
  return {
    choice: 'через',
    ruleUa:
      '«Через» вживаємо зі знахідним відмінком для небажаних, шкідливих або нейтральних причин.',
    ruleEn:
      "Use 'через' (+ Accusative) for adverse, undesirable, or neutral causes.",
  };
}

/**
 * Determine duration preposition: 'протягом' vs 'на протязі'.
 */
export function resolveDurationPrepositionRule(isTimeDuration: boolean): {
  choice: 'протягом' | 'на протязі';
  ruleUa: string;
  ruleEn: string;
} {
  if (isTimeDuration) {
    return {
      choice: 'протягом',
      ruleUa: 'На позначення тривалості в часі вживаємо «протягом» або «упродовж».',
      ruleEn: "Use 'протягом' or 'упродовж' to express duration in time.",
    };
  }
  return {
    choice: 'на протязі',
    ruleUa:
      'Вислів «на протязі» вживається лише в прямому значенні струменя повітря між відчиненими вікнами чи дверима.',
    ruleEn:
      "The phrase 'на протязі' refers strictly to being in an air draft between open doors or windows.",
  };
}

/**
 * Distinguish conjunction from homophonous pronoun/particle sequences per Правопис 2019 (§ 43, п. 1 та примітка).
 */
export function resolveConjunctionHomophoneRule(
  pair: string,
  isConjunction: boolean,
): { choice: string; ruleUa: string; ruleEn: string } {
  const p = pair.trim().toLowerCase();
  if (p === 'prote' || p === 'проте' || p === 'zate' || p === 'зате') {
    const isZate = p === 'zate' || p === 'зате';
    if (isConjunction) {
      return {
        choice: isZate ? 'зате' : 'проте',
        ruleUa: 'Сполучники «проте», «зате» (= але) пишуться разом (Правопис 2019, § 43, п. 1 та примітка).',
        ruleEn: "Conjunctions 'проте', 'зате' (= but, however) are written solid (Pravopys 2019, § 43, item 1 and note).",
      };
    }
    return {
      choice: isZate ? 'за те' : 'про те',
      ruleUa: 'Прийменник із вказівним займенником «про те», «за те» пишеться окремо (про що? — про те; за що? — за те).',
      ruleEn:
        "Preposition with demonstrative pronoun 'про те', 'за те' is written separately.",
    };
  }
  if (p === 'shchob' || p === 'щоб') {
    if (isConjunction) {
      return {
        choice: 'щоб',
        ruleUa: "Сполучник мети та з'ясувальний «щоб» пишеться разом (Правопис 2019, § 43, п. 1 та примітка).",
        ruleEn: "Purpose and explanatory conjunction 'щоб' is written solid (Pravopys 2019, § 43, item 1 and note).",
      };
    }
    return {
      choice: 'що б',
      ruleUa: 'Займенник «що» з часткою «б» пишеться окремо (частку можна переставити).',
      ruleEn: "Interrogative/relative pronoun 'що' with particle 'б' is written separately.",
    };
  }
  if (p === 'yakby' || p === 'якби') {
    if (isConjunction) {
      return {
        choice: 'якби',
        ruleUa: 'Умовний сполучник «якби» (= якщо б) пишеться разом (Правопис 2019, § 43, п. 1 та примітка).',
        ruleEn: "Conditional conjunction 'якби' (= if) is written solid (Pravopys 2019, § 43, item 1 and note).",
      };
    }
    return {
      choice: 'як би',
      ruleUa: 'Прислівник способу дії «як» із часткою «би» пишеться окремо.',
      ruleEn: "Adverb of manner 'як' with modal particle 'би' is written separately.",
    };
  }
  if (p === 'yakshcho' || p === 'якщо') {
    if (isConjunction) {
      return {
        choice: 'якщо',
        ruleUa: 'Умовний сполучник «якщо» пишеться разом (Правопис 2019, § 43, п. 1 та примітка).',
        ruleEn: "Conditional conjunction 'якщо' (= if) is written solid (Pravopys 2019, § 43, item 1 and note).",
      };
    }
    return {
      choice: 'як що',
      ruleUa: 'Прислівник «як» із займенником «що» пишуться окремо, коли кожне слово має самостійне значення й відповідає на окреме питання.',
      ruleEn: "Adverb 'як' and pronoun 'що' are written separately when each preserves independent syntactic function.",
    };
  }
  if (p === 'takozh' || p === 'також' || p === 'tezh' || p === 'теж') {
    const isTezh = p === 'tezh' || p === 'теж';
    if (isConjunction) {
      return {
        choice: isTezh ? 'теж' : 'також',
        ruleUa: 'Приєднувальні сполучники «також», «теж» пишуться разом (Академічна граматика; СУМ-20; Правопис 2019, § 44, п. 1).',
        ruleEn: "Joining conjunctions 'також', 'теж' are written solid (Academic Grammar; SUM-20; Pravopys 2019, § 44, item 1).",
      };
    }
    return {
      choice: isTezh ? 'те ж' : 'так же',
      ruleUa: 'Займенник «те» / прислівник «так» із часткою «ж / же» пишеться окремо.',
      ruleEn: "Pronoun 'те' or adverb 'так' with particle 'ж / же' is written separately.",
    };
  }
  throw new Error(`Unknown conjunction homophone pair: ${pair}`);
}

/**
 * Orthography of 'не' per Правопис 2019 (§ 44, п. 1 та 2).
 */
export function resolveParticleNeRule(params: {
  pos: string;
  hasContrast?: boolean;
  hasDependentWords?: boolean;
  cannotStandWithoutNe?: boolean;
  formsNewConcept?: boolean;
}): { orthography: 'разом' | 'окремо'; ruleUa: string; ruleEn: string } {
  const pos = params.pos.trim().toLowerCase();

  if (params.cannotStandWithoutNe) {
    return {
      orthography: 'разом',
      ruleUa:
        'Слова, які без «не» не вживаються, завжди пишуться разом: ненавидіти, нехтувати, неволити, негайний (Правопис 2019, § 44, п. 2.5).',
      ruleEn:
        "Words that cannot stand without 'не' are always written solid: ненавидіти, нехтувати (Pravopys 2019, § 44, item 2.5).",
    };
  }

  if (params.hasContrast) {
    return {
      orthography: 'окремо',
      ruleUa:
        'Частка «не» пишеться окремо, якщо є протиставлення зі сполучником «а»: не глибока, а мілка річка (Правопис 2019, § 44, п. 1.4).',
      ruleEn:
        "Particle 'не' is written separately when an explicit contrast with 'а' is present: не глибока, а мілка.",
    };
  }

  if (pos === 'verb' || pos === 'дієслово' || pos === 'gerund' || pos === 'дієприслівник') {
    return {
      orthography: 'окремо',
      ruleUa:
        'Частка «не» з дієсловами та дієприслівниками пишеться окремо: не знаю, не пишучи (Правопис 2019, § 44, п. 1.1 та 1.2).',
      ruleEn:
        "Particle 'не' is written separately with verbs and gerunds: не знаю, не пишучи.",
    };
  }

  if (pos === 'participle' || pos === 'дієприкметник') {
    if (params.hasDependentWords) {
      return {
        orthography: 'окремо',
        ruleUa:
          'Частка «не» з дієприкметниками пишеться окремо, якщо при них є пояснювальні (залежні) слова: ще не прочитана книга (Правопис 2019, § 44, п. 1.3).',
        ruleEn:
          "Particle 'не' is written separately with participles having dependent modifying words: ще не прочитана книга.",
      };
    }
    return {
      orthography: 'разом',
      ruleUa:
        'Одиничний дієприкметник без залежних слів, що виступає означенням, пишеться з «не» разом: непрочитана книга (Правопис 2019, § 44, п. 2.8).',
      ruleEn:
        "An isolated participle without dependent words acting as an attribute is written solid: непрочитана книга.",
    };
  }

  if (
    pos === 'noun' ||
    pos === 'іменник' ||
    pos === 'adj' ||
    pos === 'adjective' ||
    pos === 'прикметник' ||
    pos === 'adv' ||
    pos === 'adverb' ||
    pos === 'прислівник'
  ) {
    if (params.formsNewConcept !== false) {
      return {
        orthography: 'разом',
        ruleUa:
          'З іменниками, прикметниками та прислівниками «не» пишеться разом, коли утворює нове поняття (можна замінити синонімом: неправда — брехня) (Правопис 2019, § 44, п. 2.7).',
        ruleEn:
          "With nouns, adjectives, and adverbs, 'не' is written solid when forming a new concept (replaceable with a synonym).",
      };
    }
    return {
      orthography: 'окремо',
      ruleUa:
        'Якщо слово з «не» не утворює нового поняття і лише заперечує ознаку, воно пишеться окремо (Правопис 2019, § 44, п. 1.4).',
      ruleEn:
        "If 'не' merely negates without forming a unified lexical concept, it is written separately.",
    };
  }

  return {
    orthography: 'окремо',
    ruleUa: 'За загальним правилом частка «не» пишеться окремо (Правопис 2019, § 44, п. 1).',
    ruleEn: "As a general rule, particle 'не' is written separately.",
  };
}

/**
 * Orthography of particles per Правопис 2019 (§ 44, п. 1 та 3).
 */
export function resolveParticleHyphenationRule(params: {
  particle: string;
  positionAfterWord?: boolean;
  hasInterveningPreposition?: boolean;
}): { orthography: 'дефіс' | 'окремо'; ruleUa: string; ruleEn: string } {
  const pNorm = params.particle.trim().toLowerCase().replace(/-/g, '');

  if (pNorm === 'будь' || pNorm === 'казна' || pNorm === 'хтозна') {
    if (params.hasInterveningPreposition) {
      return {
        orthography: 'окремо',
        ruleUa:
          'Якщо між частками «будь-», «казна-», «хтозна-» та займенником стоїть прийменник, усі три слова пишуться окремо: будь у кого, хтозна з ким (Правопис 2019, § 44, п. 1; § 34).',
        ruleEn:
          'When a preposition intervenes between будь-, казна-, хтозна- and a pronoun, all three words are written separately: будь у кого.',
      };
    }
    return {
      orthography: 'дефіс',
      ruleUa:
        'Частки «будь-», «казна-», «хтозна-» з іншими словами пишуться через дефіс: будь-хто, хтозна-де (Правопис 2019, § 44, п. 3.2).',
      ruleEn: 'Particles будь-, казна-, хтозна- are hyphenated: будь-хто, хтозна-де.',
    };
  }

  if (pNorm === 'таки') {
    if (params.positionAfterWord !== false) {
      return {
        orthography: 'дефіс',
        ruleUa:
          'Частка «таки» пишеться через дефіс, коли стоїть ПІСЛЯ слова, яке виділяє: прийшов-таки, знав-таки (Правопис 2019, § 44, п. 3.1).',
        ruleEn:
          "Particle 'таки' is hyphenated when standing AFTER the word it emphasizes: прийшов-таки.",
      };
    }
    return {
      orthography: 'окремо',
      ruleUa:
        'Частка «таки» пишеться окремо, коли стоїть ПЕРЕД словом: таки прийшов, таки переміг (Правопис 2019, § 44, п. 3.1, прим. 2).',
      ruleEn:
        "Particle 'таки' is written separately when standing BEFORE the word: таки прийшов.",
    };
  }

  if (pNorm === 'бо' || pNorm === 'но' || pNorm === 'то' || pNorm === 'от') {
    return {
      orthography: 'дефіс',
      ruleUa: `Частки «-${pNorm}» після слів, які вони виділяють, пишуться через дефіс (Правопис 2019, § 44, п. 3.1).`,
      ruleEn: `Particles '-${pNorm}' are hyphenated when following the emphasized word.`,
    };
  }

  return {
    orthography: 'окремо',
    ruleUa: 'Частка пишеться окремо (Правопис 2019, § 44, п. 1).',
    ruleEn: 'Particle is written separately.',
  };
}

/**
 * Generate targeted pedagogical feedback for a user's selection on a function word card.
 */
export function functionWordFeedbackFor(
  card: PracticeFunctionWordCard,
  selectedOption: string,
): FunctionWordFeedback {
  const normSelected = selectedOption.trim();
  const normCorrect = card.correctAnswer.trim();

  if (normSelected === normCorrect) {
    return {
      isCorrect: true,
      explanationUa: `Правильно! «${card.correctAnswer}» — нормативний варіант.`,
      explanationEn: `Correct! '${card.correctAnswer}' is the normative choice.`,
      ruleCitation: card.ruleCitation,
      ruleUa: card.ruleSummary.uk,
      ruleEn: card.ruleSummary.en,
    };
  }

  const distractor = card.distractors.find((d) => d.form.trim() === normSelected);

  if (distractor) {
    return {
      isCorrect: false,
      explanationUa: distractor.explanationUa,
      explanationEn: distractor.explanationEn,
      ruleCitation: card.ruleCitation,
      ruleUa: card.ruleSummary.uk,
      ruleEn: card.ruleSummary.en,
      interferenceType: distractor.interferenceType,
    };
  }

  return {
    isCorrect: false,
    explanationUa: `Неправильно. Нормативний варіант: «${card.correctAnswer}».`,
    explanationEn: `Incorrect. The normative choice is '${card.correctAnswer}'.`,
    ruleCitation: card.ruleCitation,
    ruleUa: card.ruleSummary.uk,
    ruleEn: card.ruleSummary.en,
  };
}
