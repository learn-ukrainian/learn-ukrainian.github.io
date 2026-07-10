import { type CSSProperties, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import MatchUp from './MatchUp';
import PracticeErrorBoundary from './PracticeErrorBoundary';
import PracticeFlashcard from './PracticeFlashcard';
import PracticeSessionSummary, { type SessionSummaryStats } from './PracticeSessionSummary';
import {
  DEFAULT_NEW_PER_DAY,
  PUBLISHED_PRACTICE_LEVELS,
  SRS_STORAGE_FULL_WARNING,
  buildSessionPoolConstraintState,
  combinePracticeShards,
  extendWithLowerDecks,
  itemIdPresentInDeck,
  computeSessionScope,
  computeTodayRingDenominator,
  countDueReviewCards,
  czNorm,
  isPracticeNewCard,
  isPracticeSessionResumable,
  isWrongCaseAnswer,
  loadState,
  masteredCount,
  nextDuePreviewTime,
  parseCardKey,
  previewRatingIntervals,
  rateCard,
  resolveSessionCompletion,
  readNewCardsDailyState,
  readPracticeSessionSnapshot,
  selectNextPracticeItem,
  seededAnswerIndex,
  sessionPoolAllowsCandidate,
  uaPlural,
  validateClozeOptions,
  writeNewCardsDailyState,
  writePracticeSessionSnapshot,
  type ChoicePolarity,
  type PracticeClozeItem,
  type PracticeDeckData,
  type PracticeHeritageItem,
  type PracticeHeritageShard,
  type PracticeIndexItem,
  type PracticeIndexShard,
  type PracticeLexeme,
  type PracticeLexemeShard,
  type PracticeModeFilter,
  type PracticeRating,
  type PracticeSelection,
  type PracticeSessionSnapshot,
  type ReviewLogEntry,
  type SelectionHistoryItem,
  type SessionBudget,
  type SessionScopeStats,
  type PracticeClassifySet,
} from '../lib/lexicon/srs';
import {
  focusModeForWeakness,
  matchesWeakness,
  weakCaseChips,
  type WeakArea,
} from '../lib/lexicon/weak-areas';
import {
  CEFR_LEVELS,
  LEARNER_LEVEL_STORAGE_KEY,
  normalizeCefrLevel,
  type CefrLevel,
} from '../lib/lexicon/levels';

interface LexiconPracticeProps {
  deckLevel?: string;
  shardBaseUrl?: string;
  initialDeck?: PracticeDeckData | PracticeLexeme[];
  initialMode?: PracticeModeFilter;
  autoStart?: boolean;
  advanceDelayMs?: number;
}

interface StreakState {
  version: 1;
  current: number;
  lastPracticeDate: string | null;
}

interface ChoiceOption {
  label: string;
  correct: boolean;
  kind?: 'answer' | 'calque' | 'distractor';
}

interface HeritageFeedback {
  kind: 'correct' | 'calque' | 'wrong';
  text: string;
  citations?: string[];
}

interface ClozeFeedback {
  kind: 'correct' | 'case-miss' | 'wrong-word';
  text: string;
}

/** Result of scoring an item, carried until the learner completes/advances it. */
interface CompletionOutcome {
  nextUnresolved: Set<string>;
  nextDeferred: PracticeLexeme[];
}

const STREAK_KEY = 'lu-lexicon-practice-streak';
const MASTERED_THRESHOLD = 21;
type SessionPhase = 'idle' | 'active' | 'summary';

const SESSION_LABELS_A1: Record<string, string> = {
  startSession: 'Start session',
  continueSession: 'Continue session',
  focusPractice: 'Focus practice',
  budget10: 'Quick (10)',
  budget20: 'Standard (20)',
  budgetZero: 'Until clear',
  newToday: 'New today',
  dueReviews: 'Due for review',
};

function makePracticeSessionSeed(): number {
  return (Date.now() ^ Math.floor(Math.random() * 4294967296)) >>> 0;
}

const RATING_LABELS: Record<PracticeRating, string> = {
  again: 'Ще раз',
  hard: 'Важко',
  good: 'Добре',
  easy: 'Легко',
};

type VisiblePracticeModeFilter = Extract<
  PracticeModeFilter,
  | 'mixed'
  | 'flashcards'
  | 'matching'
  | 'choice'
  | 'cloze'
  | 'stress'
  | 'classify'
  | 'paradigm'
  | 'synonym'
  | 'heritage'
>;

const MODE_LABELS: Record<VisiblePracticeModeFilter, string> = {
  mixed: 'Mixed',
  flashcards: 'Flashcards',
  matching: 'Matching',
  choice: 'Choice',
  cloze: 'Cloze',
  stress: 'Stress',
  classify: 'Classify',
  paradigm: 'Paradigm',
  synonym: 'Synonym',
  heritage: 'Спадщина',
};

const MODE_CARD_ORDER: VisiblePracticeModeFilter[] = [
  'mixed',
  'flashcards',
  'matching',
  'choice',
  'cloze',
  'stress',
  'classify',
  'paradigm',
  'synonym',
  'heritage',
];

const MODE_META: Record<
  VisiblePracticeModeFilter,
  {
    title: string;
    en: string;
    description: string;
    step: string;
    accent: 'blue' | 'teal' | 'purple' | 'orange';
  }
> = {
  mixed: {
    title: 'Мікс',
    en: 'Mixed',
    description: 'Чергуйте картки, добір, вибір і пропуски, щоб не звикати до одного типу підказки.',
    step: 'Змішана сесія',
    accent: 'orange',
  },
  flashcards: {
    title: 'Флешкартки',
    en: 'Flashcards',
    description: 'Картка за карткою з інтервальним повторенням. Згадайте значення, тоді оцініть відповідь.',
    step: 'Розпізнавання',
    accent: 'blue',
  },
  matching: {
    title: 'Добір пар',
    en: 'Matching',
    description: 'З’єднайте українські слова з їхніми значеннями для швидкого закріплення зв’язків.',
    step: 'Зіставлення',
    accent: 'teal',
  },
  choice: {
    title: 'Вибір',
    en: 'Choice',
    description: 'Оберіть правильне значення або слово серед близьких варіантів з цієї ж колоди.',
    step: 'Перевірка',
    accent: 'purple',
  },
  cloze: {
    title: 'Пропуск',
    en: 'Cloze',
    description: 'Впишіть слово у потрібній формі. Відмінок має збігатися з реченням.',
    step: 'Відмінювання',
    accent: 'orange',
  },
  stress: {
    title: 'Наголос',
    en: 'Stress',
    description: 'Оберіть голосну, на яку падає наголос у слові.',
    step: 'Форма слова',
    accent: 'teal',
  },
  classify: {
    title: 'Група',
    en: 'Classify',
    description: 'Визначте граматичну групу слова за даними VESUM.',
    step: 'Морфологія',
    accent: 'purple',
  },
  paradigm: {
    title: 'Форма',
    en: 'Paradigm',
    description: 'Оберіть форму слова для потрібного відмінка й числа.',
    step: 'Парадигма',
    accent: 'blue',
  },
  synonym: {
    title: 'Синоніми',
    en: 'Synonyms',
    description: 'Доберіть синонім або антонім до українського слова.',
    step: 'Лексика',
    accent: 'orange',
  },
  heritage: {
    title: 'Спадщина',
    en: 'Heritage',
    description: 'Оберіть питоме українське слово.',
    step: 'Питома лексика',
    accent: 'teal',
  },
};

function visiblePracticeMode(mode: PracticeModeFilter): VisiblePracticeModeFilter {
  return mode in MODE_META ? (mode as VisiblePracticeModeFilter) : 'mixed';
}

const HERITAGE_COLORS: Record<string, string> = {
  native: 'var(--lu-teal)',
  inherited: 'var(--lu-teal)',
  borrowed: 'var(--lu-purple)',
  loanword: 'var(--lu-purple)',
  calque: 'var(--lu-orange)',
  avoid: 'var(--lu-red)',
};

const MEANING_MC_MAX_WORDS = 4;
const MEANING_MC_MAX_CHARS = 32;
const FUNCTION_POS = new Set([
  'adp',
  'conj',
  'conjunction',
  'det',
  'determiner',
  'interj',
  'interjection',
  'particle',
  'prep',
  'preposition',
  'pron',
  'pronoun',
  'sconj',
]);
const FUNCTION_GLOSS_HEADWORDS = new Set([
  'and',
  'because',
  'but',
  'if',
  'nor',
  'or',
  'than',
  'that',
  'though',
  'unless',
  'until',
  'when',
  'where',
  'whether',
  'while',
  'yet',
]);

function cleanGloss(gloss: string): string {
  return gloss.split(/[;,]/, 1)[0].replace(/\s+/g, ' ').trim();
}

function glossLabel(entry: PracticeLexeme): string {
  return entry.glossClean?.trim() || cleanGloss(entry.gloss);
}

function glossHeadword(entry: PracticeLexeme): string {
  return glossLabel(entry).toLocaleLowerCase('en-US').split(/\s+/)[0] ?? '';
}

function isPhraseGloss(label: string): boolean {
  const clean = label.replace(/\s+/g, ' ').trim();
  // Count alphanumeric tokens (ignoring standalone punctuation) to match the
  // Python deck generator's `_meaning_label_word_count` regex exactly, so the
  // served deck and this runtime guard never disagree on eligibility.
  const wordCount = clean ? (clean.match(/[^\W_]+(?:[-'][^\W_]+)?/gu) || []).length : 0;
  return (
    !clean ||
    clean.length > MEANING_MC_MAX_CHARS ||
    wordCount > MEANING_MC_MAX_WORDS ||
    clean.includes('?') ||
    clean.includes('(') ||
    clean.includes(')')
  );
}

function isMeaningMcEligible(entry: PracticeLexeme): boolean {
  const label = glossLabel(entry);
  if (entry.meaningMcEligible === false) return false;
  // Judge the CLEAN first-sense label, not the raw multi-sense gloss: a word like
  // "dog; hound" has a perfectly concise glossClean ("dog") and must stay eligible.
  if (isPhraseGloss(label)) return false;
  if (FUNCTION_GLOSS_HEADWORDS.has(glossHeadword(entry))) return false;
  if (entry.pos && FUNCTION_POS.has(entry.pos.toLocaleLowerCase('en-US'))) return false;
  return entry.meaningMcEligible ?? true;
}

function todayKey(date = new Date()): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function previousDayKey(date = new Date()): string {
  const previous = new Date(date);
  previous.setDate(previous.getDate() - 1);
  return todayKey(previous);
}

function readStreak(): StreakState {
  try {
    const raw = window.localStorage.getItem(STREAK_KEY);
    if (!raw) return { version: 1, current: 0, lastPracticeDate: null };
    const parsed = JSON.parse(raw) as Partial<StreakState>;
    if (parsed.version !== 1 || typeof parsed.current !== 'number') {
      return { version: 1, current: 0, lastPracticeDate: null };
    }
    return {
      version: 1,
      current: parsed.current,
      lastPracticeDate: parsed.lastPracticeDate ?? null,
    };
  } catch {
    return { version: 1, current: 0, lastPracticeDate: null };
  }
}

function writeStreak(streak: StreakState): void {
  try {
    window.localStorage.setItem(STREAK_KEY, JSON.stringify(streak));
  } catch {
    // SRS storage warning is handled by the caller.
  }
}

function recordStreak(date = new Date()): StreakState {
  const current = readStreak();
  const today = todayKey(date);
  if (current.lastPracticeDate === today) return current;
  const nextCount = current.lastPracticeDate === previousDayKey(date) ? current.current + 1 : 1;
  const next = { version: 1 as const, current: nextCount, lastPracticeDate: today };
  writeStreak(next);
  return next;
}

function heritageTagColor(heritage: string | null): string | undefined {
  if (!heritage) return undefined;
  return HERITAGE_COLORS[heritage.toLowerCase()] ?? 'var(--lu-text-muted)';
}

function cardData(entry: PracticeLexeme) {
  return {
    front: entry.lemma,
    back: entry.gloss,
    subtitle: entry.ipa ?? entry.pos ?? undefined,
    tag: entry.cefr ?? undefined,
    tagColor: heritageTagColor(entry.heritage),
  };
}

function ModeIcon({ mode }: { mode: VisiblePracticeModeFilter }) {
  if (mode === 'matching') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M8.5 7.5h7" />
        <path d="M8.5 16.5h7" />
        <circle cx="5" cy="7.5" r="2" />
        <circle cx="19" cy="7.5" r="2" />
        <circle cx="5" cy="16.5" r="2" />
        <circle cx="19" cy="16.5" r="2" />
      </svg>
    );
  }

  if (mode === 'choice') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M5 6.5h14" />
        <path d="M5 12h14" />
        <path d="M5 17.5h8" />
        <path d="m15.5 16.5 1.7 1.7 3.3-3.9" />
      </svg>
    );
  }

  if (mode === 'cloze') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M4 7h7" />
        <path d="M15 7h5" />
        <path d="M4 17h16" />
        <path d="M12.5 7h1" />
        <path d="M10 13h4" />
      </svg>
    );
  }

  if (mode === 'heritage') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M12 4 5 7.5v5.2c0 3.9 2.6 6.2 7 7.3 4.4-1.1 7-3.4 7-7.3V7.5L12 4Z" />
        <path d="M9 12.2 11.1 14l4-4.6" />
      </svg>
    );
  }

  if (mode === 'mixed') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M7 4h8l2 2v12a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z" />
        <path d="M15 4v4h4" />
        <path d="M8 11h8" />
        <path d="M8 15h5" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <rect x="6" y="5" width="12" height="14" rx="2" />
      <path d="M9 9h6" />
      <path d="M9 13h4" />
    </svg>
  );
}

function hasLoadedDrillShards(deck: PracticeDeckData | null): boolean {
  return Boolean(
    deck &&
      (deck.cloze.length > 0 ||
        (deck.stress?.length ?? 0) > 0 ||
        (deck.classify?.length ?? 0) > 0 ||
        (deck.paradigm?.length ?? 0) > 0 ||
        (deck.synonym?.length ?? 0) > 0 ||
        (deck.heritage?.length ?? 0) > 0),
  );
}

function normalizeInitialDeck(initialDeck?: PracticeDeckData | PracticeLexeme[]): PracticeDeckData | null {
  if (!initialDeck) return null;
  if (!Array.isArray(initialDeck)) return initialDeck;
  const lexemes = initialDeck.map((entry) => {
    const legacy = entry as PracticeLexeme & { slug?: string; example?: string | null };
    const lemmaId = legacy.lemmaId ?? legacy.slug ?? legacy.lemma;
    const glossClean = legacy.glossClean ?? cleanGloss(legacy.gloss);
    const meaningMcEligible = legacy.meaningMcEligible ?? !isPhraseGloss(glossClean);
    return {
      ...entry,
      lemmaId,
      lemmaPlain: legacy.lemmaPlain ?? czNorm(legacy.lemma),
      glossClean,
      meaningMcEligible,
      severity: legacy.severity ?? null,
      paradigm: legacy.paradigm ?? { cases: {} },
    };
  });
  return {
    deckVersion: 'test-fixture',
    level: lexemes[0]?.cefr ?? 'A1',
    index: lexemes.map((entry, index) => ({
      lemmaId: entry.lemmaId,
      lemma: entry.lemma,
      cefr: entry.cefr ?? 'A1',
      modes: entry.meaningMcEligible ? ['flashcards', 'matching', 'choice'] : ['flashcards'],
      hasCloze: false,
      clozeIds: [],
      newOrder: index,
    })),
    lexemes,
    cloze: [],
    stress: [],
    classify: [],
    paradigm: [],
    synonym: [],
  };
}

function historyFromSelection(selection: PracticeSelection): SelectionHistoryItem {
  return {
    itemId: selection.itemId,
    lemmaId: selection.lemma.lemmaId,
    mode: selection.mode,
    clozeId: selection.cloze?.clozeId,
    sentenceFrameId: selection.cloze?.sentenceFrameId,
    blankCase: selection.cloze?.blankCase,
    classifySetId: selection.classifySetId,
    heritageId: selection.heritage?.heritageId,
    recallDirection: selection.recallDirection,
    choicePolarity: selection.choicePolarity,
    lapsed: selection.lapsed,
  };
}

function reviewLemmaId(selection: PracticeSelection): string {
  const parsed = parseCardKey(selection.cardKey);
  if (!parsed.quarantined && parsed.mode === selection.mode) return parsed.lemmaId;
  return selection.lemma.lemmaId;
}

function orderedChoiceOptions(
  selection: PracticeSelection,
  deck: PracticeDeckData,
  polarity: ChoicePolarity,
  sessionSeed: number,
): ChoiceOption[] {
  if (!isMeaningMcEligible(selection.lemma)) return [];
  const distractors = meaningDistractors(selection.lemma, deck, 3);
  if (distractors.length < 3) return [];
  const answer = polarity === 'word-to-meaning' ? glossLabel(selection.lemma) : selection.lemma.lemma;
  const options = [
    { label: answer, correct: true },
    ...distractors.map((entry) => ({
      label: polarity === 'word-to-meaning' ? glossLabel(entry) : entry.lemma,
      correct: false,
    })),
  ];
  const answerIndex = seededAnswerIndex(sessionSeed, selection.itemId, options.length);
  const [first] = options.splice(0, 1);
  options.splice(answerIndex, 0, first);
  return options;
}

function meaningDistractors(
  answer: PracticeLexeme,
  deck: PracticeDeckData,
  limit: number,
): PracticeLexeme[] {
  const answerHeadword = glossHeadword(answer);
  const answerLength = glossLabel(answer).length;
  const candidatePool = deck.lexemes.filter(
    (candidate) =>
      candidate.lemmaId !== answer.lemmaId &&
      isMeaningMcEligible(candidate) &&
      glossHeadword(candidate) !== answerHeadword,
  );
  const sameLevel = candidatePool.filter((candidate) => candidate.cefr === answer.cefr);
  const candidates =
    sameLevel.length >= limit
      ? sameLevel
      : [
        ...sameLevel,
        ...candidatePool.filter((candidate) => candidate.cefr !== answer.cefr),
      ];
  // PRIORITIZE same-POS + comparable gloss length via sort keys — never hard-filter
  // the candidate pool down to a subset, which would starve distractors when a word
  // has fewer than 3 same-POS peers even though hundreds of valid candidates exist.
  const seenLabels = new Set<string>();
  return candidates
    .sort((left, right) => {
      const leftPos = left.pos === answer.pos ? 0 : 1;
      const rightPos = right.pos === answer.pos ? 0 : 1;
      if (leftPos !== rightPos) return leftPos - rightPos;
      const leftLen = Math.abs(glossLabel(left).length - answerLength);
      const rightLen = Math.abs(glossLabel(right).length - answerLength);
      return leftLen - rightLen || left.lemmaId.localeCompare(right.lemmaId);
    })
    .filter((entry) => {
      const key = glossLabel(entry).toLocaleLowerCase('en-US');
      if (seenLabels.has(key)) return false;
      seenLabels.add(key);
      return true;
    })
    .slice(0, limit);
}

function matchingPairs(selection: PracticeSelection, deck: PracticeDeckData) {
  if (!isMeaningMcEligible(selection.lemma)) return [];
  const distractors = meaningDistractors(selection.lemma, deck, 5);
  if (distractors.length < 2) return [];
  return [selection.lemma, ...distractors].map((entry) => ({
    left: entry.lemma,
    right: glossLabel(entry),
    lemmaId: entry.lemmaId,
  }));
}

function choicePrompt(selection: PracticeSelection): string {
  if (selection.choicePolarity === 'word-to-meaning') {
    return `Що означає «${selection.lemma.lemma}»?`;
  }
  return `Яке слово означає «${glossLabel(selection.lemma)}»?`;
}

function classifySet(selection: PracticeSelection): PracticeClassifySet | null {
  const sets = selection.classify?.sets ?? [];
  if (!sets.length) return null;
  return sets.find((set) => set.setId === selection.classifySetId) ?? sets[0] ?? null;
}

function drillChoiceOptions(selection: PracticeSelection): ChoiceOption[] | null {
  if (selection.stress) {
    return selection.stress.nuclei.map((nucleus) => ({
      label: nucleus.label,
      correct: nucleus.index === selection.stress?.stressIndex,
    }));
  }
  const selectedSet = classifySet(selection);
  if (selectedSet) {
    return selectedSet.options.map((option) => ({
      label: option.labelEn ? `${option.labelUk} (${option.labelEn})` : option.labelUk,
      correct: option.value === selectedSet.answer,
    }));
  }
  if (selection.paradigm) {
    return selection.paradigm.options.map((option) => ({
      label: option.label,
      correct: option.kind === 'answer',
    }));
  }
  if (selection.synonym) {
    return selection.synonym.options.map((option) => ({
      label: option.label,
      correct: option.kind === 'answer',
    }));
  }
  return null;
}

function heritageOptions(item: PracticeHeritageItem): ChoiceOption[] {
  const answer = czNorm(item.answer);
  const calque = czNorm(item.calque);
  return item.options.map((option) => {
    const label = czNorm(option.label);
    const correct = label === answer;
    return {
      label: option.label,
      correct,
      kind: correct ? 'answer' : label === calque ? 'calque' : 'distractor',
    };
  });
}

function heritageFeedbackFor(item: PracticeHeritageItem, option: ChoiceOption): HeritageFeedback {
  if (option.correct) {
    return {
      kind: 'correct',
      text: 'Правильно',
    };
  }
  if (option.kind === 'calque') {
    return {
      kind: 'calque',
      text: item.rationaleUk ? `⚠️ калька; ${item.rationaleUk}` : '⚠️ калька',
      citations: item.citations,
    };
  }
  return {
    kind: 'wrong',
    text: 'Ще раз',
  };
}

function drillChoicePrompt(selection: PracticeSelection): { prompt: string; subtitle: string } | null {
  if (selection.stress) {
    return {
      prompt: `Де наголос у слові «${selection.stress.unstressed}»?`,
      subtitle: 'Оберіть наголошену голосну',
    };
  }
  const selectedSet = classifySet(selection);
  if (selectedSet) {
    const setLabel = selectedSet.setLabelEn
      ? `${selectedSet.setLabelUk} (${selectedSet.setLabelEn})`
      : selectedSet.setLabelUk;
    return {
      prompt: `До якої групи належить «${selection.lemma.lemma}»?`,
      subtitle: setLabel,
    };
  }
  if (selection.paradigm) {
    const slot = selection.paradigm.slot.labelEn
      ? `${selection.paradigm.slot.labelUk} (${selection.paradigm.slot.labelEn})`
      : selection.paradigm.slot.labelUk;
    return {
      prompt: `Яка форма від «${selection.lemma.lemma}»?`,
      subtitle: slot,
    };
  }
  if (selection.synonym) {
    return {
      prompt:
        selection.synonym.polarity === 'antonym'
          ? `Оберіть антонім до «${selection.synonym.prompt}»`
          : `Оберіть синонім до «${selection.synonym.prompt}»`,
      subtitle: 'Оберіть правильну відповідь',
    };
  }
  return null;
}

function clozeParts(item: PracticeClozeItem): [string, string] {
  const [before, ...after] = item.sentence.split('___');
  return [before, after.join('___')];
}

function slotPromptParts(prompt: string): [string, string] {
  const [before, ...after] = prompt.split('___');
  return [before, after.join('___')];
}

function shouldLoadCloze(mode: PracticeModeFilter): boolean {
  return ['mixed', 'cloze', 'stress', 'classify', 'paradigm', 'synonym', 'heritage'].includes(mode);
}

function sessionScopeIndexForMode(
  index: PracticeIndexItem[],
  modeFilter: PracticeModeFilter,
): PracticeIndexItem[] {
  if (modeFilter === 'mixed') return index;
  return index
    .filter((item) => item.modes.includes(modeFilter))
    .map((item) => ({ ...item, modes: [modeFilter] }));
}

function shouldShowFocusModeCard(
  practiceMode: VisiblePracticeModeFilter,
  deck: PracticeDeckData | null,
  indexForStats: PracticeIndexItem[],
): boolean {
  if (practiceMode !== 'heritage') return true;
  if (deck) return (deck.heritage?.length ?? 0) > 0;
  return indexForStats.some((item) => item.modes.includes('heritage'));
}

/** Learner level persisted in the shared `lu-learner-level` key (also used by Words of the Day). */
function readLearnerLevel(fallback: CefrLevel): CefrLevel {
  if (typeof window === 'undefined') return fallback;
  try {
    return normalizeCefrLevel(window.localStorage.getItem(LEARNER_LEVEL_STORAGE_KEY), fallback);
  } catch {
    return fallback;
  }
}

function writeLearnerLevel(level: CefrLevel): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, level);
  } catch {
    // Persisting the preference is best-effort; the in-memory selection still applies.
  }
}

/** CEFR levels at or below `level` (cumulative: B1 -> A1, A2, B1). */
function levelsUpTo(level: CefrLevel): CefrLevel[] {
  const cap = CEFR_LEVELS.indexOf(level);
  return CEFR_LEVELS.slice(0, cap + 1);
}

/** Concatenate per-level decks into one cumulative deck (CEFR shards are disjoint). */
function mergeDecks(decks: PracticeDeckData[], level: CefrLevel): PracticeDeckData {
  if (decks.length === 0) throw new Error('mergeDecks called with no decks');
  // Delegate to the shared extend for consistency (new deck identity for selector cache).
  const [first, ...rest] = decks;
  const base = { ...first, level };
  return extendWithLowerDecks(base, rest);
}

/** Deduped fetch for a practice shard JSON by URL. Concurrent or repeated callers share the promise. */
async function getShardJson<T>(url: string, cache: Map<string, Promise<unknown>>): Promise<T> {
  let p = cache.get(url) as Promise<T> | undefined;
  if (!p) {
    p = fetch(url).then((res) => {
      if (!res.ok) throw new Error(`Shard fetch failed: ${url}`);
      return res.json() as Promise<T>;
    });
    // On failure allow retry next time
    p = p.catch((err) => {
      cache.delete(url);
      throw err;
    });
    cache.set(url, p);
  }
  return p;
}

export default function LexiconPractice(props: LexiconPracticeProps) {
  return (
    <PracticeErrorBoundary>
      <LexiconPracticeIsland {...props} />
    </PracticeErrorBoundary>
  );
}

function LexiconPracticeIsland({
  deckLevel = 'A1',
  shardBaseUrl = '/lexicon',
  initialDeck,
  initialMode = 'mixed',
  autoStart = false,
  advanceDelayMs = 650,
}: LexiconPracticeProps) {
  const [deck, setDeck] = useState<PracticeDeckData | null>(() => normalizeInitialDeck(initialDeck));
  const [clozeLoaded, setClozeLoaded] = useState(() => {
    const normalized = normalizeInitialDeck(initialDeck);
    return hasLoadedDrillShards(normalized);
  });
  const [sessionPhase, setSessionPhase] = useState<SessionPhase>(autoStart ? 'active' : 'idle');
  const [sessionSeed, setSessionSeed] = useState(() => makePracticeSessionSeed());
  const [mode, setMode] = useState<PracticeModeFilter>(initialMode);
  const [sessionBudget, setSessionBudget] = useState<SessionBudget>(20);
  const [sessionPlan, setSessionPlan] = useState<SessionScopeStats | null>(null);
  const [plannedReviews, setPlannedReviews] = useState(0);
  const [plannedTotal, setPlannedTotal] = useState(0);
  const [sessionCompleted, setSessionCompleted] = useState(0);
  const [reviewsCompleted, setReviewsCompleted] = useState(0);
  const [sessionNewIntroduced, setSessionNewIntroduced] = useState(0);
  const [extensionUsed, setExtensionUsed] = useState(0);
  const [unresolvedCardKeys, setUnresolvedCardKeys] = useState<Set<string>>(() => new Set());
  const [deferredLemmas, setDeferredLemmas] = useState<PracticeLexeme[]>([]);
  const [sessionCorrect, setSessionCorrect] = useState(0);
  const [sessionLapsed, setSessionLapsed] = useState(0);
  const [advancedToReview, setAdvancedToReview] = useState<string[]>([]);
  const [resumeSnapshot, setResumeSnapshot] = useState<PracticeSessionSnapshot | null>(null);
  const [learnerLevel, setLearnerLevel] = useState<CefrLevel>(() =>
    readLearnerLevel(normalizeCefrLevel(deckLevel)),
  );
  const [focusedLemmaId, setFocusedLemmaId] = useState<string | null>(null);
  // §6b weak-area focus: when set, the session poolFilter is narrowed to this weakness.
  const [focusWeakness, setFocusWeakness] = useState<WeakArea | null>(null);
  const [reviewLog, setReviewLog] = useState<ReviewLogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState('');
  const [revision, setRevision] = useState(0);
  const [history, setHistory] = useState<SelectionHistoryItem[]>([]);
  const [answerLocked, setAnswerLocked] = useState(false);
  // A WRONG answer parks its scored outcome here instead of auto-advancing, so the
  // feedback panel (e.g. the §9.5 cited calque correction) dwells until the learner
  // explicitly moves on via «Далі →» or Enter. Correct answers never set this.
  const [pendingOutcome, setPendingOutcome] = useState<CompletionOutcome | null>(null);
  const [streak, setStreak] = useState<StreakState>({
    version: 1,
    current: 0,
    lastPracticeDate: null,
  });
  const [, setMastered] = useState(0);
  const [completedToday, setCompletedToday] = useState(0);
  const [dailyNewCount, setDailyNewCount] = useState(0);
  const [storageWarning, setStorageWarning] = useState<string | null>(null);
  const [clozeInput, setClozeInput] = useState('');
  const [clozeFeedback, setClozeFeedback] = useState<ClozeFeedback | null>(null);
  const [clozeAttemptRecorded, setClozeAttemptRecorded] = useState(false);
  const [heritageFeedback, setHeritageFeedback] = useState<HeritageFeedback | null>(null);
  const [dueIndex, setDueIndex] = useState<PracticeIndexItem[] | null>(null);
  const [publishedLevels] = useState<Set<CefrLevel>>(
    () => new Set(PUBLISHED_PRACTICE_LEVELS as unknown as CefrLevel[]),
  );
  const stageRef = useRef<HTMLDivElement | null>(null);
  const deckRequestId = useRef(0);
  const sessionStartedAtRef = useRef(Date.now());
  const didInitRef = useRef(false);
  // Consumption source of truth for the parked wrong-answer outcome. `advancePending`
  // claims it via this ref (not the closed-over `pendingOutcome` state) so a rapid
  // double-advance (double-Enter, or Enter+click) before React re-renders resolves to
  // exactly ONE `completeSelection` — the second call reads a null ref and no-ops.
  const pendingOutcomeRef = useRef<CompletionOutcome | null>(null);
  // Selection ref used to stabilize the in-flight item across live deck merges (pool growth from
  // background lower-level shards). While history length is unchanged we keep returning the
  // prior selection object so a B1 card is not yanked when an A1/A2 shard lands mid-item.
  const committedSelectionRef = useRef<{ selection: PracticeSelection; historyLen: number } | null>(null);
  // Deduping cache for shard JSON fetches (by full URL) so index shards fetched by the eager
  // due-count effect are not re-fetched by ensure, and no shard is fetched twice.
  const shardJsonCacheRef = useRef(new Map<string, Promise<unknown>>());
  const showEnglishSubtitles = learnerLevel === 'A1';

  const matchedSelectedRatingRef = useRef<PracticeRating | null>(null);
  const matchingTargetOutcomeRef = useRef<CompletionOutcome | null>(null);

  // Reset all per-item feedback/lock state. Shared by the selection-change effect and
  // `advancePending` so a wrong answer that re-surfaces the SAME item (a lapsed card the
  // selector picks again — same `itemId`, so the effect does not re-fire) still starts
  // clean: no stale lock, cloze input/feedback, or parked outcome.
  const resetItemFeedback = useCallback(() => {
    setAnswerLocked(false);
    setClozeInput('');
    setClozeFeedback(null);
    setClozeAttemptRecorded(false);
    setHeritageFeedback(null);
    setPendingOutcome(null);
    pendingOutcomeRef.current = null;
    matchedSelectedRatingRef.current = null;
    matchingTargetOutcomeRef.current = null;
  }, []);

  useEffect(() => {
    if (didInitRef.current) return;
    didInitRef.current = true;

    const state = loadState();
    setStreak(readStreak());
    setMastered(masteredCount(MASTERED_THRESHOLD));
    setDailyNewCount(readNewCardsDailyState().count);
    setReviewLog([...state.reviews]);

    if (state.flags.storageFull) {
      setStorageWarning(SRS_STORAGE_FULL_WARNING);
    } else if (state.flags.storageWriteFailed || state.flags.corrupt || state.flags.migrationFailed) {
      setStorageWarning('Прогрес призупинено, доки сховище браузера не стане доступним.');
    } else if (state.flags.clockJump) {
      setStorageWarning('Час повторення може бути неточним: змінився годинник пристрою.');
    }

    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const target = params.get('lemmaId');
      if (target) {
        // Clear snapshot and resume state
        writePracticeSessionSnapshot(null);
        setResumeSnapshot(null);

        setFocusedLemmaId(target);
        setMode('mixed');
        setSessionBudget(10);
        setSessionPhase('active');
        void ensureDeck(shouldLoadCloze('mixed'));
      } else {
        const snapshot = readPracticeSessionSnapshot();
        setResumeSnapshot(isPracticeSessionResumable(snapshot) ? snapshot : null);
      }
    }
  }, []);

  useEffect(() => {
    const normalized = normalizeInitialDeck(initialDeck);
    if (normalized) {
      setDeck(normalized);
      setClozeLoaded(hasLoadedDrillShards(normalized));
    }
  }, [initialDeck]);

  useEffect(() => {
    const isAutoStartTrigger = autoStart || Boolean(focusedLemmaId);
    if (!isAutoStartTrigger || !deck || plannedTotal > 0) return;

    if (focusedLemmaId && deck.index.some((item) => item.lemmaId !== focusedLemmaId)) {
      const filtered = {
        ...deck,
        index: deck.index.filter((item) => item.lemmaId === focusedLemmaId),
      };
      setDeck(filtered);
      return;
    }

    const plan = computeSessionScope(sessionScopeIndexForMode(deck.index, mode), sessionBudget, {
      dailyNewCount,
    });
    resetSessionTracking(plan, sessionBudget);

    // Persist an initial snapshot for this newly started session so it is resumable.
    const nextSeed = makePracticeSessionSeed();
    setSessionSeed(nextSeed);
    sessionStartedAtRef.current = Date.now();
    setHistory([]);
    const reviewSlots = sessionBudget === 'until-zero' ? plan.dueReviews : Math.min(plan.dueReviews, sessionBudget);
    writePracticeSessionSnapshot({
      sessionSeed: nextSeed,
      history: [],
      budget: sessionBudget,
      completed: 0,
      modeFilter: mode,
      level: learnerLevel,
      startedAt: sessionStartedAtRef.current,
      extensionUsed: 0,
      sessionNewIntroduced: 0,
      plannedReviews: reviewSlots,
      plannedNew: plan.plannedNew,
      plannedTotal: plan.plannedTotal,
      reviewsCompleted: 0,
      unresolvedCardKeys: [],
    });
  }, [autoStart, focusedLemmaId, dailyNewCount, deck, mode, plannedTotal, sessionBudget, learnerLevel]);

  useEffect(() => {
    const page = document.querySelector('.lexicon-practice-page');
    if (!page) return undefined;
    if (sessionPhase === 'active') {
      page.setAttribute('data-in-session', 'true');
    } else {
      page.removeAttribute('data-in-session');
    }
    return () => page.removeAttribute('data-in-session');
  }, [sessionPhase]);

  // §6b: the weak-area chips are derived from `reviewLog` and only surface on the idle
  // home. Re-derive the log from storage every time we (re)enter idle so the chips reflect
  // the JUST-finished session's ratings — the in-session `refreshProgress` updates apply to
  // the active React tree, but a return to idle from summary/«Додому» must re-read the
  // persisted log so a newly-fixed (or newly-weak) case is shown or dropped immediately.
  useEffect(() => {
    if (!didInitRef.current || sessionPhase !== 'idle') return;
    setReviewLog([...loadState().reviews]);
  }, [sessionPhase]);

  // Eager-load ONLY the lightweight per-level index shards on mount (and on a
  // pre-session level change) so the «До повторення» tile + today ring reflect the
  // learner's real SRS due-count immediately — the most motivating number on the
  // home, and the reason a returning learner opens this page. The heavy
  // lexeme/cloze shards stay lazy until a mode actually starts (ensureDeck). Once a
  // full deck is loaded its own `index` supersedes this. The `cancelled` flag drops
  // a stale fetch when the learner switches level before it resolves.
  useEffect(() => {
    if (deck) {
      setDueIndex(null);
      return;
    }
    let cancelled = false;
    void (async () => {
      try {
        const batches = await Promise.all(
          levelsUpTo(learnerLevel).map(async (shardLevel) => {
            const url = `${shardBaseUrl}/practice-index.${shardLevel}.json`;
            try {
              const shard = await getShardJson<PracticeIndexShard>(url, shardJsonCacheRef.current);
              return shard.items ?? [];
            } catch {
              return [];
            }
          }),
        );
        if (!cancelled) setDueIndex(batches.flat());
      } catch {
        if (!cancelled) setDueIndex(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [deck, learnerLevel, shardBaseUrl]);


  const indexForStats = (deck?.index ?? dueIndex ?? []).filter(
    (item) => !focusedLemmaId || item.lemmaId === focusedLemmaId
  );

  const sessionPoolConstraints = useMemo(
    () =>
      buildSessionPoolConstraintState({
        plannedReviews,
        reviewsCompleted,
        sessionNewIntroduced,
        dailyNewCount,
      }),
    [dailyNewCount, plannedReviews, reviewsCompleted, sessionNewIntroduced],
  );

  const poolFilter = useCallback(
    (candidate: PracticeSelection) => {
      if (!sessionPoolAllowsCandidate(candidate, sessionPoolConstraints)) return false;
      // A weak-area focus session narrows the pool to items matching the tapped
      // weakness on top of the normal §6b session constraints (no parallel path).
      if (focusWeakness && !matchesWeakness(candidate, focusWeakness)) return false;
      return true;
    },
    [focusWeakness, sessionPoolConstraints],
  );

  const weakChips = useMemo(() => weakCaseChips(reviewLog), [reviewLog]);

  const selection = useMemo(() => {
    if (!deck || sessionPhase !== 'active') return null;
    const fresh = selectNextPracticeItem(deck, {
      history,
      modeFilter: mode,
      now: new Date(),
      sessionSeed,
      poolFilter: sessionPhase === 'active' ? poolFilter : undefined,
    });
    // Stabilize in-flight selection across live merges from background lower-level shards.
    // The selector cache (per deck identity) produces a new pool, but we keep the exact
    // prior selection object (for same history length) so the user is not yanked mid-item
    // and #4740/#4744 flows are unperturbed. Once history advances on complete, fresh pick
    // uses the grown pool.
    const committed = committedSelectionRef.current;
    if (
      committed &&
      committed.historyLen === history.length &&
      fresh &&
      fresh.itemId !== committed.selection.itemId &&
      itemIdPresentInDeck(deck, committed.selection.itemId)
    ) {
      return committed.selection;
    }
    return fresh;
  }, [deck, history, mode, poolFilter, revision, sessionPhase, sessionSeed]);

  // Pin the board for the life of the selection to avoid mid-board changes.
  const pairsRef = useRef<{ itemId: string; pairs: ReturnType<typeof matchingPairs> } | null>(null);
  const pairs = useMemo(() => {
    if (!selection || selection.mode !== 'matching' || !deck) return [];
    if (pairsRef.current && pairsRef.current.itemId === selection.itemId) {
      return pairsRef.current.pairs;
    }
    const computed = matchingPairs(selection, deck);
    pairsRef.current = { itemId: selection.itemId, pairs: computed };
    return computed;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selection?.itemId]);

  useEffect(() => {
    resetItemFeedback();
    if (selection) {
      // Record for stabilization across future deck swaps (bg merges).
      committedSelectionRef.current = { selection, historyLen: history.length };
      window.setTimeout(() => stageRef.current?.focus(), 0);
    }
  }, [selection?.itemId, resetItemFeedback]);

  // Rate the selected lemma if matched but never completed (due to session abort/unmount)
  useEffect(() => {
    const prevSelection = selection;
    return () => {
      if (matchedSelectedRatingRef.current && prevSelection) {
        try {
          rateCard(
            prevSelection.lemma.lemmaId,
            prevSelection.mode,
            matchedSelectedRatingRef.current,
            new Date(),
            {
              blankCase: prevSelection.cloze?.blankCase,
              heritageKind: prevSelection.heritage?.kind,
            }
          );
        } catch (e) {
          // ignore or handle storage warning
        }
        matchedSelectedRatingRef.current = null;
      }
    };
  }, [selection]);

  const handleMatchingMatch = useCallback((pairIndex: number, rating: PracticeRating) => {
    const pair = pairs[pairIndex];
    if (!pair || !pair.lemmaId) return;

    if (pairIndex === 0) {
      if (sessionCompleted === 0) {
        matchedSelectedRatingRef.current = rating;
      } else {
        if (selection) {
          const outcome = recordReview(selection, rating);
          matchingTargetOutcomeRef.current = outcome;
        }
      }
    } else {
      try {
        rateCard(pair.lemmaId, 'matching', rating, new Date());
      } catch (e) {
        setStorageWarning('Прогрес призупинено, доки сховище браузера не стане доступним.');
      }
    }
  }, [pairs, selection, sessionCompleted]);

  // While a wrong answer dwells, Enter is a second way to advance (alongside the
  // «Далі →» button) — the disabled option buttons blur to <body>, so we listen at
  // the window level rather than on the stage.
  useEffect(() => {
    if (!pendingOutcome) return undefined;
    const handleEnter = (event: KeyboardEvent) => {
      if (event.key !== 'Enter') return;
      event.preventDefault();
      advancePending();
    };
    window.addEventListener('keydown', handleEnter);
    return () => window.removeEventListener('keydown', handleEnter);
  }, [pendingOutcome, selection]);

  useEffect(() => {
    if (sessionPhase !== 'active') return;
    document.title = `${MODE_LABELS[visiblePracticeMode(mode)]} Practice - Words of the Day`;
  }, [mode, sessionPhase]);

  async function ensureDeck(
    includeCloze = shouldLoadCloze(mode),
    options: { level?: CefrLevel; force?: boolean } = {},
  ): Promise<PracticeDeckData | null> {
    // `level`/`force` are passed explicitly on a level change so we don't read the
    // stale `learnerLevel`/`deck` closures before their state updates have flushed.
    const level = options.level ?? learnerLevel;
    const force = options.force ?? false;
    const current = force ? null : deck;
    if (current && (!includeCloze || clozeLoaded)) return current;
    const requestId = ++deckRequestId.current;
    setLoading(true);
    setError(null);
    try {
      let nextDeck = current;
      let nextClozeLoaded = clozeLoaded;
      const levels = levelsUpTo(level);
      const targetLevel = level;
      const lowerLevels = levels.slice(0, -1);
      const needDrills = includeCloze && (force || !clozeLoaded);

      if (!nextDeck) {
        // PROGRESSIVE: Load the SELECTED level's core shards (index + lexemes) FIRST.
        // The session can start on this deck immediately; lower levels are backgrounded.
        // This eliminates the 21-shard/8.9MB wait for B1 (and general multi-level).
        // A1 is unaffected (no lower levels).
        const indexUrl = `${shardBaseUrl}/practice-index.${targetLevel}.json`;
        const lexUrl = `${shardBaseUrl}/practice-lexemes.${targetLevel}.json`;
        const [indexShard, lexemeShard] = await Promise.all([
          getShardJson<PracticeIndexShard>(indexUrl, shardJsonCacheRef.current),
          getShardJson<PracticeLexemeShard>(lexUrl, shardJsonCacheRef.current),
        ]);
        nextDeck = combinePracticeShards(indexShard, lexemeShard);
        // Set early so that beginSession proceeds and first item can render from the
        // selected level alone.
        if (deckRequestId.current === requestId) {
          setDeck(nextDeck);
        }

        // Fire-and-forget background load of lower-level *cores*. Merge into live pool
        // as they arrive; selector cache per deck identity (#4656) receives the new deck
        // object and recomputes candidates for the grown pool on next select (stabilized
        // for in-flight item).
        if (lowerLevels.length > 0) {
          void (async () => {
            const bgId = deckRequestId.current;
            const lowerCores = (
              await Promise.all(
                lowerLevels.map(async (lv) => {
                  try {
                    const iUrl = `${shardBaseUrl}/practice-index.${lv}.json`;
                    const lUrl = `${shardBaseUrl}/practice-lexemes.${lv}.json`;
                    const [i, l] = await Promise.all([
                      getShardJson<PracticeIndexShard>(iUrl, shardJsonCacheRef.current),
                      getShardJson<PracticeLexemeShard>(lUrl, shardJsonCacheRef.current),
                    ]);
                    return combinePracticeShards(i, l);
                  } catch {
                    // Failed background shard degrades gracefully; session continues.
                    return null;
                  }
                }),
              )
            ).filter((d): d is PracticeDeckData => d !== null);
            if (deckRequestId.current !== bgId || lowerCores.length === 0) return;
            setDeck((prev) => {
              if (!prev) return mergeDecks(lowerCores, level);
              return extendWithLowerDecks(prev, lowerCores);
            });
          })();
        }
      }

      if (needDrills) {
        // Load drill shards for the *selected* level (may block this call if mode requires
        // them, e.g. initialMode=cloze or mixed). Lower drill shards are always background.
        // This also defers drill-kind shards for basic modes (flashcards etc) until a
        // drill mode surfaces (optional path kept clean).
        const drillUrls = [
          `${shardBaseUrl}/practice-cloze.${targetLevel}.json`,
          `${shardBaseUrl}/practice-stress.${targetLevel}.json`,
          `${shardBaseUrl}/practice-classify.${targetLevel}.json`,
          `${shardBaseUrl}/practice-paradigm.${targetLevel}.json`,
          `${shardBaseUrl}/practice-synonym.${targetLevel}.json`,
          `${shardBaseUrl}/practice-heritage.${targetLevel}.json`,
        ];
        const drillResults = await Promise.all(
          drillUrls.map((u) =>
            getShardJson<any>(u, shardJsonCacheRef.current).catch(() => ({})),
          ),
        );
        const [clozeR, stressR, classifyR, paradigmR, synonymR, heritageR] = drillResults;
        nextDeck = {
          ...nextDeck!,
          cloze: [...(nextDeck!.cloze ?? []), ...((clozeR as { cloze?: PracticeClozeItem[] }).cloze ?? [])],
          stress: [...(nextDeck!.stress ?? []), ...((stressR as { stress?: any[] }).stress ?? [])],
          classify: [...(nextDeck!.classify ?? []), ...((classifyR as { classify?: any[] }).classify ?? [])],
          paradigm: [...(nextDeck!.paradigm ?? []), ...((paradigmR as { paradigm?: any[] }).paradigm ?? [])],
          synonym: [...(nextDeck!.synonym ?? []), ...((synonymR as { synonym?: any[] }).synonym ?? [])],
          heritage: [...(nextDeck!.heritage ?? []), ...((heritageR as { heritage?: any[] }).heritage ?? [])],
        };
        nextClozeLoaded = true;
        if (deckRequestId.current === requestId) {
          setDeck(nextDeck);
          setClozeLoaded(true);
        }

        // Background lower drills (merge live when they land).
        if (lowerLevels.length > 0) {
          void (async () => {
            const bgId = deckRequestId.current;
            const lowerDrillBatches = await Promise.all(
              lowerLevels.map(async (lv) => {
                const urls = [
                  `${shardBaseUrl}/practice-cloze.${lv}.json`,
                  `${shardBaseUrl}/practice-stress.${lv}.json`,
                  `${shardBaseUrl}/practice-classify.${lv}.json`,
                  `${shardBaseUrl}/practice-paradigm.${lv}.json`,
                  `${shardBaseUrl}/practice-synonym.${lv}.json`,
                  `${shardBaseUrl}/practice-heritage.${lv}.json`,
                ];
                const rs = await Promise.all(
                  urls.map((u) => getShardJson<any>(u, shardJsonCacheRef.current).catch(() => ({}))),
                );
                return {
                  cloze: (rs[0] as { cloze?: PracticeClozeItem[] }).cloze ?? [],
                  stress: (rs[1] as { stress?: any[] }).stress ?? [],
                  classify: (rs[2] as { classify?: any[] }).classify ?? [],
                  paradigm: (rs[3] as { paradigm?: any[] }).paradigm ?? [],
                  synonym: (rs[4] as { synonym?: any[] }).synonym ?? [],
                  heritage: (rs[5] as { heritage?: any[] }).heritage ?? [],
                };
              }),
            );
            if (deckRequestId.current !== bgId) return;
            setDeck((prev) => {
              if (!prev) return prev;
              return {
                ...prev,
                cloze: [...(prev.cloze ?? []), ...lowerDrillBatches.flatMap((b) => b.cloze)],
                stress: [...(prev.stress ?? []), ...lowerDrillBatches.flatMap((b) => b.stress)],
                classify: [...(prev.classify ?? []), ...lowerDrillBatches.flatMap((b) => b.classify)],
                paradigm: [...(prev.paradigm ?? []), ...lowerDrillBatches.flatMap((b) => b.paradigm)],
                synonym: [...(prev.synonym ?? []), ...lowerDrillBatches.flatMap((b) => b.synonym)],
                heritage: [...(prev.heritage ?? []), ...lowerDrillBatches.flatMap((b) => b.heritage)],
              };
            });
          })();
        }
      }

      // Ignore the result if a newer fetch (e.g. a later level switch) has superseded this one.
      if (deckRequestId.current !== requestId) return nextDeck!;
      setDeck(nextDeck!);
      setClozeLoaded(nextClozeLoaded);
      return nextDeck!;
    } catch {
      if (deckRequestId.current === requestId) {
        setError('Не вдалося завантажити колоду для практики.');
      }
      return null;
    } finally {
      if (deckRequestId.current === requestId) setLoading(false);
    }
  }

  function resetSessionTracking(plan: SessionScopeStats, budget: SessionBudget) {
    const reviewSlots =
      budget === 'until-zero' ? plan.dueReviews : Math.min(plan.dueReviews, budget);
    setSessionPlan(plan);
    setPlannedReviews(reviewSlots);
    setPlannedTotal(plan.plannedTotal);
    setSessionCompleted(0);
    setReviewsCompleted(0);
    setSessionNewIntroduced(0);
    setExtensionUsed(0);
    setUnresolvedCardKeys(new Set());
    setDeferredLemmas([]);
    setSessionCorrect(0);
    setSessionLapsed(0);
    setAdvancedToReview([]);
  }

  function buildSessionSnapshot(
    overrides: Partial<PracticeSessionSnapshot> = {},
  ): PracticeSessionSnapshot {
    return {
      sessionSeed,
      history,
      budget: sessionBudget,
      completed: sessionCompleted,
      modeFilter: mode,
      level: learnerLevel,
      startedAt: sessionStartedAtRef.current,
      extensionUsed,
      sessionNewIntroduced,
      plannedReviews,
      plannedNew: sessionPlan?.plannedNew ?? 0,
      plannedTotal,
      reviewsCompleted,
      unresolvedCardKeys: [...unresolvedCardKeys],
      ...overrides,
    };
  }

  function persistSessionSnapshot(
    overrides: Partial<PracticeSessionSnapshot> = {},
    options: { force?: boolean } = {},
  ) {
    if (!options.force && sessionPhase !== 'active') return;
    writePracticeSessionSnapshot(buildSessionSnapshot(overrides));
  }

  function effectiveSessionTarget(): number {
    return plannedTotal + extensionUsed;
  }

  function openSummary(deferred: PracticeLexeme[] = deferredLemmas) {
    if (deferred.length) setDeferredLemmas(deferred);
    writePracticeSessionSnapshot(null);
    setResumeSnapshot(null);
    setSessionPhase('summary');
  }

  async function beginSession(
    nextMode: PracticeModeFilter = 'mixed',
    budget: SessionBudget = sessionBudget,
    resume?: PracticeSessionSnapshot,
    // §6b: the weak-area focus is passed EXPLICITLY here (never read from `focusWeakness`
    // setState timing before the call) so the empty-pool probe below and the session's
    // `poolFilter` see the same, deterministic value. A resumed session passes no focus,
    // so `focusWeakness` is always cleared on resume — the focus is session-transient by
    // design and is intentionally NOT persisted to `PracticeSessionSnapshot`.
    focus: WeakArea | null = null,
  ) {
    setMode(nextMode);
    setSessionBudget(budget);
    setError(null);
    let loadedDeck = await ensureDeck(shouldLoadCloze(nextMode));
    if (!loadedDeck) return;
    if (focusedLemmaId) {
      loadedDeck = {
        ...loadedDeck,
        index: loadedDeck.index.filter((item) => item.lemmaId === focusedLemmaId),
      };
      setDeck(loadedDeck);
    }
    // A focus session must never strand the learner in an itemless «active» phase. Probe
    // the loaded deck under the SAME combined filter the session would apply (weakness +
    // §6b pool constraints); if nothing matches, clear the focus, surface the idle notice,
    // and stay on the home rather than opening an empty session.
    if (
      focus &&
      !selectNextPracticeItem(loadedDeck, {
        modeFilter: nextMode,
        now: new Date(),
        sessionSeed: makePracticeSessionSeed(),
        poolFilter: (candidate) =>
          sessionPoolAllowsCandidate(candidate, sessionPoolConstraints) &&
          matchesWeakness(candidate, focus),
      })
    ) {
      setFocusWeakness(null);
      setFeedback('Немає вправ для цього фокуса — колода оновиться після практики');
      writePracticeSessionSnapshot(null);
      setResumeSnapshot(null);
      setSessionPhase('idle');
      return;
    }
    setFocusWeakness(focus);
    // A session is starting for real — drop any stale idle notice (e.g. the empty-focus
    // message) so the active status line reads «Сесія …» cleanly.
    setFeedback('');
    const index = sessionScopeIndexForMode(loadedDeck.index, nextMode);
    const plan = computeSessionScope(index, budget, { dailyNewCount });
    const nextSeed = resume?.sessionSeed ?? makePracticeSessionSeed();
    if (resume) {
      sessionStartedAtRef.current = resume.startedAt;
      setSessionSeed(nextSeed);
      setHistory(resume.history);
      setSessionCompleted(resume.completed);
      setPlannedReviews(resume.plannedReviews ?? plan.dueReviews);
      setPlannedTotal(resume.plannedTotal ?? plan.plannedTotal);
      setReviewsCompleted(resume.reviewsCompleted ?? 0);
      setSessionNewIntroduced(resume.sessionNewIntroduced ?? 0);
      setExtensionUsed(resume.extensionUsed ?? 0);
      setUnresolvedCardKeys(new Set(resume.unresolvedCardKeys ?? []));
      setSessionPlan(plan);
    } else {
      sessionStartedAtRef.current = Date.now();
      setSessionSeed(nextSeed);
      setHistory([]);
      resetSessionTracking(plan, budget);
    }
    setSessionPhase('active');
    const reviewSlots = budget === 'until-zero' ? plan.dueReviews : Math.min(plan.dueReviews, budget);
    writePracticeSessionSnapshot({
      sessionSeed: nextSeed,
      history: resume?.history ?? [],
      budget,
      completed: resume?.completed ?? 0,
      modeFilter: nextMode,
      level: learnerLevel,
      startedAt: sessionStartedAtRef.current,
      extensionUsed: resume?.extensionUsed ?? 0,
      sessionNewIntroduced: resume?.sessionNewIntroduced ?? 0,
      plannedReviews: resume?.plannedReviews ?? reviewSlots,
      plannedNew: plan.plannedNew,
      plannedTotal: resume?.plannedTotal ?? plan.plannedTotal,
      reviewsCompleted: resume?.reviewsCompleted ?? 0,
      unresolvedCardKeys: resume?.unresolvedCardKeys ?? [],
    });
  }

  async function startSession(
    budget: SessionBudget = 20,
    nextMode: PracticeModeFilter = 'mixed',
    focus: WeakArea | null = null,
  ) {
    writePracticeSessionSnapshot(null);
    setResumeSnapshot(null);
    await beginSession(nextMode, budget, undefined, focus);
  }

  async function resumeSession() {
    if (!resumeSnapshot) return;
    // A resumed session starts with NO focus: the weakness is session-transient (never
    // persisted to the snapshot), so `beginSession(..., focus=null)` clears `focusWeakness`.
    await beginSession(resumeSnapshot.modeFilter, resumeSnapshot.budget, resumeSnapshot, null);
  }

  async function startFocusMode(nextMode: PracticeModeFilter) {
    await startSession(sessionBudget, nextMode, null);
  }

  /**
   * §6b: tapping a weak-area chip starts a focus session filtered to that weakness.
   * The weakness is passed EXPLICITLY through `startSession` → `beginSession` (not via a
   * pre-start `setFocusWeakness`), so the empty-pool probe and the session `poolFilter`
   * share one deterministic value and an itemless focus never strands the learner.
   */
  async function startWeakAreaFocus(weakness: WeakArea) {
    await startSession(sessionBudget, focusModeForWeakness(weakness), weakness);
  }

  function clearFocus() {
    setFocusedLemmaId(null);
    setFocusWeakness(null);
    setDeck(null);
    setDueIndex(null);
    committedSelectionRef.current = null;
    writePracticeSessionSnapshot(null);
    setResumeSnapshot(null);
    setSessionPhase('idle');
  }

  async function changeLevel(nextLevel: CefrLevel) {
    if (nextLevel === learnerLevel || !publishedLevels.has(nextLevel)) return;
    setLearnerLevel(nextLevel);
    writeLearnerLevel(nextLevel);
    setClozeLoaded(false);
    setHistory([]);
    committedSelectionRef.current = null;
    writePracticeSessionSnapshot(null);
    setResumeSnapshot(null);
    if (sessionPhase === 'active') {
      await ensureDeck(shouldLoadCloze(mode), { level: nextLevel, force: true });
    } else {
      setDeck(null);
      setSessionPhase('idle');
    }
  }

  function refreshProgress() {
    const state = loadState();
    setMastered(masteredCount(MASTERED_THRESHOLD));
    setReviewLog([...state.reviews]);
    if (state.flags.storageFull) {
      setStorageWarning(SRS_STORAGE_FULL_WARNING);
    } else if (state.flags.storageWriteFailed || state.flags.corrupt || state.flags.migrationFailed) {
      setStorageWarning('Прогрес призупинено, доки сховище браузера не стане доступним.');
    } else if (storageWarning === SRS_STORAGE_FULL_WARNING) {
      setStorageWarning(null);
    }
    setRevision((value) => value + 1);
  }

  function recordReview(
    current: PracticeSelection,
    rating: PracticeRating,
  ): { nextUnresolved: Set<string>; nextDeferred: PracticeLexeme[] } {
    const wasNew = isPracticeNewCard(current.cardState);
    const nextUnresolved = new Set(unresolvedCardKeys);
    let nextDeferred = [...deferredLemmas];
    try {
      rateCard(reviewLemmaId(current), current.mode, rating, new Date(), {
        blankCase: current.cloze?.blankCase,
        heritageKind: current.heritage?.kind,
      });
      setStreak(recordStreak());
      if (rating === 'good' || rating === 'easy') {
        setSessionCorrect((value) => value + 1);
      }
      if (rating === 'again') {
        setSessionLapsed((value) => value + 1);
      }
      if (wasNew && rating !== 'again') {
        const daily = readNewCardsDailyState();
        const nextDaily = { date: daily.date, count: daily.count + 1 };
        writeNewCardsDailyState(nextDaily);
        setDailyNewCount(nextDaily.count);
        setSessionNewIntroduced((value) => value + 1);
      }
      if (!wasNew) {
        setReviewsCompleted((value) => value + 1);
      }
      if (wasNew && (rating === 'good' || rating === 'easy')) {
        setAdvancedToReview((items) =>
          items.includes(current.lemma.lemma) ? items : [...items, current.lemma.lemma],
        );
      }
      if (rating === 'again') {
        nextUnresolved.add(current.cardKey);
        if (!nextDeferred.some((entry) => entry.lemmaId === current.lemma.lemmaId)) {
          nextDeferred = [...nextDeferred, current.lemma];
        }
      } else if (rating === 'good' || rating === 'easy') {
        if (nextUnresolved.delete(current.cardKey)) {
          nextDeferred = nextDeferred.filter((entry) => entry.lemmaId !== current.lemma.lemmaId);
        }
      }
      setUnresolvedCardKeys(nextUnresolved);
      setDeferredLemmas(nextDeferred);
      setFeedback(`${current.lemma.lemma}: ${RATING_LABELS[rating]}`);
    } catch {
      setStorageWarning('Прогрес призупинено, доки сховище браузера не стане доступним.');
    }
    return { nextUnresolved, nextDeferred };
  }

  function completeSelection(
    current: PracticeSelection,
    outcome: { nextUnresolved: Set<string>; nextDeferred: PracticeLexeme[] },
  ) {
    setHistory((items) => [...items.slice(-49), historyFromSelection(current)]);
    const nextCompleted = sessionCompleted + 1;
    setSessionCompleted(nextCompleted);
    setCompletedToday((value) => value + 1);
    refreshProgress();
    persistSessionSnapshot({ completed: nextCompleted });
    const decision = resolveSessionCompletion({
      completed: nextCompleted,
      plannedTotal,
      extensionUsed,
      unresolvedCount: outcome.nextUnresolved.size,
    });
    if (decision === 'continue') return;
    if (decision === 'extend') {
      setExtensionUsed((value) => value + 1);
      return;
    }
    if (decision === 'summary-with-deferred') {
      openSummary(outcome.nextDeferred);
      return;
    }
    openSummary();
  }

  function rateAndComplete(current: PracticeSelection, rating: PracticeRating) {
    const outcome = recordReview(current, rating);
    completeSelection(current, outcome);
  }

  /** Complete the parked (wrong-answer) selection once the learner chooses to advance. */
  function advancePending() {
    // Claim the outcome via the ref FIRST so a second synchronous invocation (a rapid
    // double-Enter, or Enter racing a «Далі» click) reads null and no-ops — the closed-over
    // `pendingOutcome` state is stale within the same tick and cannot guard against this.
    const outcome = pendingOutcomeRef.current;
    if (!outcome || !selection) return;
    pendingOutcomeRef.current = null;
    resetItemFeedback();
    completeSelection(selection, outcome);
  }

  function handleChoice(option: ChoiceOption) {
    if (!selection || answerLocked) return;
    const rating = option.correct ? 'good' : 'again';
    const outcome = recordReview(selection, rating);
    const nextHeritageFeedback = selection.heritage
      ? heritageFeedbackFor(selection.heritage, option)
      : null;
    setAnswerLocked(true);
    setHeritageFeedback(nextHeritageFeedback);
    setFeedback(
      option.correct ? `${selection.lemma.lemma}: Правильно` : `${selection.lemma.lemma}: Ще раз`,
    );
    if (option.correct) {
      window.setTimeout(() => {
        setAnswerLocked(false);
        completeSelection(selection, outcome);
      }, advanceDelayMs);
      return;
    }
    // WRONG answer: dwell so the cited correction stays readable; the learner
    // advances explicitly via «Далі →» / Enter (see advancePending). The ref mirrors
    // the state so advancePending can claim the outcome race-free.
    pendingOutcomeRef.current = outcome;
    setPendingOutcome(outcome);
  }

  function submitCloze(value: string, source: 'typed' | 'chip') {
    if (!selection?.cloze || answerLocked) return;
    const answer = value.trim();
    if (!answer) return;
    const cloze = selection.cloze;
    const correct = czNorm(answer) === czNorm(cloze.form);
    const caseMiss = isWrongCaseAnswer(answer, selection.lemma, cloze);

    if (correct) {
      const outcome = clozeAttemptRecorded
        ? { nextUnresolved: new Set(unresolvedCardKeys), nextDeferred: [...deferredLemmas] }
        : recordReview(selection, 'good');
      setClozeFeedback({
        kind: 'correct',
        text: `✓ ${cloze.form} (${cloze.caseRule.caseLabel})`,
      });
      setAnswerLocked(true);
      window.setTimeout(() => {
        setAnswerLocked(false);
        completeSelection(selection, outcome);
      }, advanceDelayMs);
      return;
    }

    if (caseMiss) {
      if (!clozeAttemptRecorded) {
        recordReview(selection, 'hard');
        setClozeAttemptRecorded(true);
      }
      setClozeInput('');
      setClozeFeedback({
        kind: 'case-miss',
        text: `→ Правильне слово. Тепер постав його у ${cloze.caseRule.caseLabel}: ${cloze.caseRule.feedback}`,
      });
      return;
    }

    if (!clozeAttemptRecorded) {
      const outcome = recordReview(selection, 'again');
      setClozeAttemptRecorded(true);
      setClozeFeedback({ kind: 'wrong-word', text: '✗ Не те слово' });
      if (source === 'chip') {
        // Wrong chip pick is a wrong answer: dwell rather than auto-advance so the
        // learner can read the correction before «Далі →» / Enter.
        setAnswerLocked(true);
        pendingOutcomeRef.current = outcome;
        setPendingOutcome(outcome);
      }
      return;
    }

    setClozeFeedback({ kind: 'wrong-word', text: '✗ Не те слово' });
    if (source === 'chip') {
      setAnswerLocked(true);
      const outcome = {
        nextUnresolved: new Set(unresolvedCardKeys),
        nextDeferred: [...deferredLemmas],
      };
      pendingOutcomeRef.current = outcome;
      setPendingOutcome(outcome);
    }
  }

  const dueReviews = useMemo(
    () => (indexForStats.length ? countDueReviewCards(indexForStats, new Date()) : 0),
    [completedToday, dailyNewCount, indexForStats, revision],
  );
  const homeScope = useMemo(
    () =>
      indexForStats.length
        ? computeSessionScope(indexForStats, sessionBudget, { dailyNewCount })
        : null,
    [dailyNewCount, indexForStats, sessionBudget],
  );
  const todayDenominator = useMemo(
    () =>
      indexForStats.length
        ? computeTodayRingDenominator(indexForStats, { dailyNewCount })
        : 0,
    [completedToday, dailyNewCount, indexForStats, revision],
  );
  const todayPct =
    todayDenominator > 0
      ? Math.min(100, (completedToday / todayDenominator) * 100)
      : completedToday > 0
        ? 100
        : 0;
  const todayRingStyle = { '--pct': String(todayPct) } as CSSProperties;
  const stageMode: PracticeModeFilter = selection?.mode ?? mode;
  const visibleStageMode = visiblePracticeMode(stageMode);
  const stageTitle =
    mode === 'mixed' && selection && visibleStageMode !== 'mixed'
      ? `Мікс · ${MODE_META[visibleStageMode].title}`
      : MODE_META[visibleStageMode].title;
  const progressLabel = `${sessionCompleted}/${effectiveSessionTarget()}`;
  const summaryStats: SessionSummaryStats = {
    correct: sessionCorrect,
    lapsed: sessionLapsed,
    advancedToReview,
    streak: streak.current,
    nextDueLabel: formatNextDueLabel(nextDuePreviewTime()),
    deferredLemmas,
  };

  function finishPractice() {
    setSessionPhase('idle');
    setFocusWeakness(null);
    setHistory([]);
    setDeck(null);
    setClozeLoaded(false);
    writePracticeSessionSnapshot(null);
  }

  return (
    <section className="lexicon-practice" aria-label="Практика слів дня">
      <p className="lexicon-practice-status" aria-live="polite">
        {feedback ||
          (sessionPhase === 'active'
            ? `Сесія ${progressLabel}`
            : sessionPhase === 'summary'
              ? 'Сесію завершено'
              : 'Оберіть сесію практики')}
      </p>

      {storageWarning && <p className="lexicon-practice-warning">{storageWarning}</p>}

      {sessionPhase === 'idle' && (
        <div className="lexicon-practice-home">
          {focusedLemmaId && (
            <div
              className="focused-lemma-banner"
              style={{
                background: 'var(--lu-surface-raised)',
                border: '1px solid var(--lu-teal, #146e78)',
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                color: 'var(--lu-text)',
                marginBottom: '0.5rem'
              }}
            >
              <span>
                🎯 <strong>Фокусне тренування:</strong> «{focusedLemmaId}»
              </span>
              <button
                type="button"
                onClick={clearFocus}
                style={{
                  minHeight: '24px',
                  height: '24px',
                  lineHeight: '24px',
                  padding: '0 8px',
                  fontSize: '0.8rem',
                  border: '1px solid var(--lu-border)',
                  borderRadius: '4px',
                  background: 'var(--lu-surface)',
                  color: 'var(--lu-text-muted)',
                  cursor: 'pointer'
                }}
              >
                Скинути фокус ×
              </button>
            </div>
          )}
          <div className="lexicon-practice-progress" role="group" aria-label="Сьогоднішній прогрес">
            <div
              className="pstat streak"
              aria-label={`${streak.current} ${uaPlural(streak.current, {
                one: 'день',
                few: 'дні',
                many: 'днів',
              })} поспіль`}
            >
              <span className="val">🔥 {streak.current}</span>
              <span className="lab">Днів поспіль</span>
            </div>
            <div className="pstat" aria-label={`${dueReviews} до повторення`}>
              <span className="val">{indexForStats.length ? dueReviews : '—'}</span>
              <span className="lab">До повторення</span>
              {showEnglishSubtitles ? (
                <span className="lab-sub">{SESSION_LABELS_A1.dueReviews}</span>
              ) : null}
            </div>
            <div className="pstat" aria-label={`Нові сьогодні ${dailyNewCount}/${DEFAULT_NEW_PER_DAY}`}>
              <span className="val">
                {dailyNewCount}/{DEFAULT_NEW_PER_DAY}
              </span>
              <span className="lab">Нові сьогодні</span>
              {showEnglishSubtitles ? (
                <span className="lab-sub">{SESSION_LABELS_A1.newToday}</span>
              ) : null}
            </div>
            <div className="pstat today">
              <div
                className="ring"
                role="img"
                aria-label={`Сьогодні виконано ${completedToday} із ${todayDenominator}`}
                style={todayRingStyle}
                data-testid="practice-today-ring"
              >
                <b>
                  {completedToday}/{todayDenominator}
                </b>
              </div>
              <div>
                <span className="lab">Сьогодні</span>
              </div>
            </div>
          </div>

          <div className="lexicon-practice-session-start">
            {homeScope ? (
              <p className="lexicon-session-scope" data-testid="practice-session-scope">
                {homeScope.dueReviews} до повторення + {homeScope.plannedNew} нових ≈{' '}
                {homeScope.estimatedMinutes} хв
              </p>
            ) : null}
            <div className="lexicon-session-budgets" role="group" aria-label="Розмір сесії">
              {([10, 20, 'until-zero'] as const).map((budget) => (
                <button
                  key={String(budget)}
                  type="button"
                  className={sessionBudget === budget ? 'active' : ''}
                  aria-pressed={sessionBudget === budget}
                  onClick={() => setSessionBudget(budget)}
                >
                  {budget === 10 ? '10' : budget === 20 ? '20' : 'до нуля'}
                </button>
              ))}
            </div>
            <button
              type="button"
              className="btn btn-accent lexicon-session-primary"
              data-testid="practice-start-session"
              onClick={() => {
                setFocusWeakness(null);
                void startSession(sessionBudget, 'mixed');
              }}
            >
              Почати сесію
              {showEnglishSubtitles ? (
                <span className="btn-sub">{SESSION_LABELS_A1.startSession}</span>
              ) : null}
            </button>
            {resumeSnapshot ? (
              <button
                type="button"
                className="btn lexicon-session-resume"
                data-testid="practice-resume-session"
                onClick={() => void resumeSession()}
              >
                Продовжити сесію ({resumeSnapshot.completed}/{resumeSnapshot.plannedTotal ?? resumeSnapshot.budget})
                {showEnglishSubtitles ? (
                  <span className="btn-sub">{SESSION_LABELS_A1.continueSession}</span>
                ) : null}
              </button>
            ) : null}
          </div>

          <div className="lexicon-practice-levels">
            <div
              className="lexicon-practice-levels-row"
              role="group"
              aria-label="Рівень учня — практика охоплює цей рівень і нижчі"
            >
              <span className="lexicon-practice-levels-label">Рівень</span>
              {CEFR_LEVELS.map((level) => {
                const published = publishedLevels.has(level);
                return (
                  <button
                    type="button"
                    key={level}
                    className={learnerLevel === level ? 'active' : ''}
                    aria-pressed={learnerLevel === level}
                    disabled={!published}
                    title={published ? undefined : 'скоро'}
                    onClick={() => void changeLevel(level)}
                  >
                    {level}
                    {!published ? <span className="level-soon">скоро</span> : null}
                  </button>
                );
              })}
            </div>
            <p className="lexicon-practice-muted lexicon-practice-levels-hint">
              Практика обмежена вашим рівнем і нижчими (накопичувально).
            </p>
          </div>

          {weakChips.length > 0 ? (
            <div className="lexicon-weak-areas" data-testid="practice-weak-areas">
              <h3>Ваші слабкі відмінки</h3>
              <div
                className="lexicon-weak-chips"
                role="group"
                aria-label="Ваші слабкі відмінки — почати фокусне тренування"
              >
                {weakChips.map((weakness) => (
                  <button
                    type="button"
                    key={`${weakness.dimension}:${weakness.key}`}
                    className="lexicon-weak-chip"
                    data-testid={`practice-weak-chip-${weakness.key}`}
                    onClick={() => void startWeakAreaFocus(weakness)}
                  >
                    {weakness.label}
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          <div className="lexicon-focus-practice">
            <h3>
              Фокус-практика
              {showEnglishSubtitles ? (
                <span className="heading-sub">{SESSION_LABELS_A1.focusPractice}</span>
              ) : null}
            </h3>
            <div className="mode-grid mode-grid-focus">
              {MODE_CARD_ORDER.filter(
                (practiceMode) =>
                  practiceMode !== 'mixed' &&
                  shouldShowFocusModeCard(practiceMode, deck, indexForStats),
              ).map((practiceMode) => {
                const meta = MODE_META[practiceMode];
                return (
                  <button
                    type="button"
                    key={practiceMode}
                    className="mode-card"
                    data-mode={practiceMode}
                    data-accent={meta.accent}
                    onClick={() => void startFocusMode(practiceMode)}
                  >
                    <div className="mc-top">
                      <span className="mc-ico">
                        <ModeIcon mode={practiceMode} />
                      </span>
                      <span>
                        <span className="mc-title">{meta.title}</span>
                        {showEnglishSubtitles ? <span className="mc-en">{meta.en}</span> : null}
                      </span>
                    </div>
                    <span className="mc-desc">{meta.description}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {loading && <p className="lexicon-practice-muted">Завантажуємо…</p>}
      {error && (
        <div className="lexicon-practice-fallback" data-testid="practice-fetch-error">
          <p className="lexicon-practice-warning">{error}</p>
          <button type="button" className="btn btn-accent" onClick={() => window.location.reload()}>
            Спробувати ще раз
          </button>
        </div>
      )}

      {sessionPhase === 'summary' && (
        <PracticeSessionSummary
          stats={summaryStats}
          showEnglishSubtitles={showEnglishSubtitles}
          onAnotherSession={() => {
            // A fresh «another session» is never a focus session — startSession(focus=null)
            // clears any weakness so the next session is the full pool for `mode`.
            void startSession(sessionBudget, mode, null);
          }}
          onDone={finishPractice}
        />
      )}

      {sessionPhase === 'active' && (
        <div className="lexicon-practice-stage-shell">
          <div className="lexicon-practice-stage-bar">
            <button type="button" className="stage-back" onClick={finishPractice}>
              ← Додому
            </button>
            <h2>{stageTitle}</h2>
            <span className="queue-pill" aria-label={`Прогрес ${progressLabel}`} data-testid="practice-session-progress">
              {progressLabel}
            </span>
          </div>

          {deck && deck.index.length === 0 && (
            <p className="lexicon-practice-muted">Поки що немає карток для практики.</p>
          )}

          {deck && deck.index.length > 0 && (
            <div className="lexicon-practice-stage" ref={stageRef} tabIndex={-1}>
              {selection ? (
                <>
                  <PracticeItem
                    selection={selection}
                    deck={deck}
                    pairs={pairs}
                    sessionSeed={sessionSeed}
                    answerLocked={answerLocked}
                    clozeInput={clozeInput}
                    clozeFeedback={clozeFeedback}
                    heritageFeedback={heritageFeedback}
                    onClozeInput={setClozeInput}
                    onFlashcardRating={(rating) => rateAndComplete(selection, rating)}
                    onChoice={handleChoice}
                    onMatchingComplete={() => {
                      if (sessionCompleted === 0) {
                        const rating = matchedSelectedRatingRef.current || 'good';
                        matchedSelectedRatingRef.current = null;
                        rateAndComplete(selection, rating);
                      } else {
                        const outcome = matchingTargetOutcomeRef.current || recordReview(selection, 'good');
                        matchingTargetOutcomeRef.current = null;
                        completeSelection(selection, outcome);
                      }
                    }}
                    onMatchingMatch={handleMatchingMatch}
                    onClozeSubmit={submitCloze}
                  />
                  {pendingOutcome ? (
                    <div className="lexicon-practice-advance" data-testid="practice-advance">
                      <button
                        type="button"
                        className="btn btn-accent lexicon-practice-advance-btn"
                        data-testid="practice-advance-button"
                        onClick={advancePending}
                      >
                        Далі →
                      </button>
                    </div>
                  ) : null}
                </>
              ) : mode === 'cloze' && deck.cloze.length === 0 ? (
                <p className="lexicon-practice-muted" data-testid="practice-cloze-empty">
                  Вправи з пропусками для цього рівня ще готуються. Спробуйте флешкартки, добір пар або вибір.
                </p>
              ) : mode === 'heritage' && (deck.heritage?.length ?? 0) === 0 ? (
                <p className="lexicon-practice-muted" data-testid="practice-heritage-empty">
                  Вправи зі спадщини для цього рівня ще готуються.
                </p>
              ) : (
                <p className="lexicon-practice-muted">Усі картки на зараз повторено.</p>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

function formatNextDueLabel(nextDue: Date | null): string | null {
  if (!nextDue) return null;
  const hours = nextDue.getHours().toString().padStart(2, '0');
  const minutes = nextDue.getMinutes().toString().padStart(2, '0');
  const remainingMs = nextDue.getTime() - Date.now();
  const remaining = Math.max(1, Math.ceil(remainingMs / (60 * 60 * 1000)));
  return `ще ${remaining} о ${hours}:${minutes}`;
}

function PracticeItem({
  selection,
  deck,
  pairs,
  sessionSeed,
  answerLocked,
  clozeInput,
  clozeFeedback,
  heritageFeedback,
  onClozeInput,
  onFlashcardRating,
  onChoice,
  onMatchingComplete,
  onMatchingMatch,
  onClozeSubmit,
}: {
  selection: PracticeSelection;
  deck: PracticeDeckData;
  pairs: ReturnType<typeof matchingPairs>;
  sessionSeed: number;
  answerLocked: boolean;
  clozeInput: string;
  clozeFeedback: ClozeFeedback | null;
  heritageFeedback: HeritageFeedback | null;
  onClozeInput(value: string): void;
  onFlashcardRating(rating: PracticeRating): void;
  onChoice(option: ChoiceOption): void;
  onMatchingComplete(): void;
  onMatchingMatch?: (pairIndex: number, rating: PracticeRating) => void;
  onClozeSubmit(value: string, source: 'typed' | 'chip'): void;
}) {
  if (selection.mode === 'flashcards') {
    const intervalPreviews = previewRatingIntervals(
      selection.lemma.lemmaId,
      selection.mode,
      new Date(),
    );
    return (
      <PracticeFlashcard
        card={cardData(selection.lemma)}
        ratingLabels={RATING_LABELS}
        intervalPreviews={intervalPreviews}
        onRate={onFlashcardRating}
      />
    );
  }

  if (selection.mode === 'cloze' && selection.cloze) {
    return (
      <PracticeCloze
        selection={selection}
        input={clozeInput}
        feedback={clozeFeedback}
        answerLocked={answerLocked}
        onInput={onClozeInput}
        onSubmit={onClozeSubmit}
      />
    );
  }

  if (selection.mode === 'heritage' && selection.heritage) {
    return (
      <PracticeHeritage
        item={selection.heritage}
        feedback={heritageFeedback}
        answerLocked={answerLocked}
        onChoice={onChoice}
      />
    );
  }

  const drillOptions = drillChoiceOptions(selection);
  const drillPrompt = drillChoicePrompt(selection);
  if (drillOptions && drillPrompt) {
    return (
      <div className="lexicon-choice" data-testid={`practice-${selection.mode}`}>
        <p className="lexicon-choice-prompt mc-q">{drillPrompt.prompt}</p>
        <p className="mc-sub">{drillPrompt.subtitle}</p>
        <ul className="lexicon-option-list mc-options">
          {drillOptions.map((option, index) => (
            <li key={`${option.label}-${index}`}>
              <button
                className={`mc-opt${answerLocked && option.correct ? ' correct' : ''}`}
                type="button"
                disabled={answerLocked}
                onClick={() => onChoice(option)}
              >
                <span className="mc-key">{index + 1}</span>
                <span>{option.label}</span>
              </button>
            </li>
          ))}
        </ul>
      </div>
    );
  }

  if (selection.mode === 'matching') {
    if (!pairs.length) {
      return <p className="lexicon-practice-muted">Зараз немає карток для добору пар.</p>;
    }
    return (
      <div data-testid="practice-matching">
        <MatchUp
          key={selection.cardKey}
          pairs={pairs}
          instruction={`Доберіть пару для «${selection.lemma.lemma}»`}
          onComplete={onMatchingComplete}
          onMatch={onMatchingMatch}
        />
      </div>
    );
  }

  const options = orderedChoiceOptions(selection, deck, selection.choicePolarity, sessionSeed);
  if (!options.length) {
    return <p className="lexicon-practice-muted">Зараз немає карток для вибору відповіді.</p>;
  }
  const prompt = choicePrompt(selection);
  return (
    <div className="lexicon-choice" data-testid={`practice-${selection.mode}`}>
      <p className="lexicon-choice-prompt mc-q">{prompt}</p>
      <p className="mc-sub">Оберіть правильну відповідь</p>
      <ul className="lexicon-option-list mc-options">
        {options.map((option, index) => (
          <li key={`${option.label}-${index}`}>
            <button
              className={`mc-opt${answerLocked && option.correct ? ' correct' : ''}`}
              type="button"
              disabled={answerLocked}
              onClick={() => onChoice(option)}
            >
              <span className="mc-key">{index + 1}</span>
              <span>{option.label}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

function PracticeHeritage({
  item,
  feedback,
  answerLocked,
  onChoice,
}: {
  item: PracticeHeritageItem;
  feedback: HeritageFeedback | null;
  answerLocked: boolean;
  onChoice(option: ChoiceOption): void;
}) {
  const [before, after] = slotPromptParts(item.prompt);
  const options = heritageOptions(item);
  const slotText = feedback?.kind === 'correct' ? item.answer : '___';
  return (
    <div className="lexicon-heritage" data-testid="practice-heritage">
      <p className="heritage-task">Оберіть питоме українське слово.</p>
      <p className="heritage-sentence">
        <span>{before}</span>
        <span className={feedback?.kind === 'correct' ? 'heritage-slot filled' : 'heritage-slot'}>
          {slotText}
        </span>
        <span>{after}</span>
      </p>
      <ul className="lexicon-option-list mc-options">
        {options.map((option, index) => (
          <li key={`${option.label}-${index}`}>
            <button
              className={`mc-opt${answerLocked && option.correct ? ' correct' : ''}`}
              type="button"
              disabled={answerLocked}
              onClick={() => onChoice(option)}
            >
              <span>{option.label}</span>
            </button>
          </li>
        ))}
      </ul>
      {feedback ? (
        <div
          className={`heritage-feedback ${feedback.kind}`}
          role={feedback.kind === 'wrong' ? 'alert' : 'status'}
          aria-live="polite"
          data-testid="practice-heritage-feedback"
        >
          <p>{feedback.text}</p>
          {feedback.kind === 'calque' && feedback.citations?.length ? (
            <p className="heritage-citation">Джерело: {feedback.citations.join('; ')}</p>
          ) : null}
          <div style={{ marginTop: '0.4rem' }}>
            <a
              href={`/lexicon/${item.lemmaId}/`}
              target="_blank"
              rel="noopener noreferrer"
              style={{ fontSize: '0.85rem', textDecoration: 'underline', color: 'inherit', fontWeight: 'bold' }}
            >
              Відкрити в Атласі →
            </a>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function PracticeCloze({
  selection,
  input,
  feedback,
  answerLocked,
  onInput,
  onSubmit,
}: {
  selection: PracticeSelection;
  input: string;
  feedback: ClozeFeedback | null;
  answerLocked: boolean;
  onInput(value: string): void;
  onSubmit(value: string, source: 'typed' | 'chip'): void;
}) {
  const cloze = selection.cloze;
  if (!cloze) return null;
  const [before, after] = clozeParts(cloze);
  const optionErrors = validateClozeOptions(cloze);
  const blankText = feedback?.kind === 'correct' ? cloze.form : input.trim() || '?';
  const blankClass = [
    'cz-blank',
    blankText !== '?' ? 'filled' : '',
    feedback?.kind === 'wrong-word' ? 'bad' : '',
    feedback?.kind === 'case-miss' ? 'case-miss' : '',
  ]
    .filter(Boolean)
    .join(' ');
  return (
    <div className="lexicon-cloze" data-testid="practice-cloze">
      <p className="cz-task">Поставте пропущене слово у правильному відмінку.</p>
      <p className="cz-sentence">
        <span>{before}</span>
        <span className={blankClass}>{blankText}</span>
        <span>{after}</span>
      </p>
      <p className="lexicon-cloze-translation cz-translate">{cloze.clozeEn}</p>
      {cloze.attribution ? (
        <p className="lexicon-cloze-attribution">
          Sentences from{' '}
          {cloze.attribution.sourceUrl ? (
            <a href={cloze.attribution.sourceUrl}>{cloze.attribution.source}</a>
          ) : (
            cloze.attribution.source
          )}
          : {cloze.attribution.uk.author} ({cloze.attribution.uk.license}) /{' '}
          {cloze.attribution.en.author} ({cloze.attribution.en.license})
        </p>
      ) : null}
      <form
        className="lexicon-cloze-row cz-input-row"
        onSubmit={(event) => {
          event.preventDefault();
          onSubmit(input, 'typed');
        }}
      >
        <input
          className="cz-input"
          value={input}
          disabled={answerLocked}
          placeholder="наберіть слово у потрібній формі…"
          autoComplete="off"
          aria-label={`Відповідь у ${cloze.caseRule.caseLabel}`}
          onChange={(event) => onInput(event.currentTarget.value)}
        />
        <button className="btn btn-accent" type="submit" disabled={answerLocked}>
          Перевірити
        </button>
      </form>
      {optionErrors.length > 0 ? (
        <p className="lexicon-practice-warning">Варіанти для пропуску не пройшли перевірку.</p>
      ) : (
        <>
          <div className="cz-or">Або оберіть</div>
          <ul className="lexicon-option-list lexicon-cloze-options cz-options">
          {cloze.options.map((option) => (
            <li key={option.optionId}>
              <button
                type="button"
                className={`cz-chip${answerLocked && option.label === cloze.form ? ' correct' : ''}`}
                disabled={answerLocked}
                onClick={() => onSubmit(option.label, 'chip')}
              >
                {option.label}
              </button>
            </li>
          ))}
          </ul>
        </>
      )}
      {feedback && (
        <div>
          <p
            className={`lexicon-cloze-feedback ${feedback.kind}`}
            role={feedback.kind === 'wrong-word' ? 'alert' : 'status'}
            aria-live="polite"
          >
            {feedback.text}
          </p>
          <div style={{ marginTop: '0.4rem' }}>
            <a
              href={`/lexicon/${selection.lemma.lemmaId}/`}
              target="_blank"
              rel="noopener noreferrer"
              style={{ fontSize: '0.85rem', textDecoration: 'underline', color: 'inherit', fontWeight: 'bold' }}
            >
              Відкрити в Атласі →
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
