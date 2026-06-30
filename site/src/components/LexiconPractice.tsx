import { type CSSProperties, useEffect, useMemo, useRef, useState } from 'react';
import FlashcardDeck from './FlashcardDeck';
import MatchUp from './MatchUp';
import {
  combinePracticeShards,
  czNorm,
  getDueQueue,
  isWrongCaseAnswer,
  loadState,
  masteredCount,
  rateCard,
  selectNextPracticeItem,
  uaPlural,
  validateClozeOptions,
  type ChoicePolarity,
  type PracticeClozeItem,
  type PracticeDeckData,
  type PracticeIndexItem,
  type PracticeIndexShard,
  type PracticeLexeme,
  type PracticeLexemeShard,
  type PracticeModeFilter,
  type PracticeRating,
  type PracticeSelection,
  type SelectionHistoryItem,
} from '../lib/lexicon/srs';
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
}

interface ClozeFeedback {
  kind: 'correct' | 'case-miss' | 'wrong-word';
  text: string;
}

const STREAK_KEY = 'lu-lexicon-practice-streak';
const MASTERED_THRESHOLD = 21;

const RATING_LABELS: Record<PracticeRating, string> = {
  again: 'Ще раз',
  hard: 'Важко',
  good: 'Добре',
  easy: 'Легко',
};

const MODE_LABELS: Record<PracticeModeFilter, string> = {
  mixed: 'Mixed',
  flashcards: 'Flashcards',
  matching: 'Matching',
  choice: 'Choice',
  cloze: 'Cloze',
};

const MODE_CARD_ORDER: PracticeModeFilter[] = ['mixed', 'flashcards', 'matching', 'choice', 'cloze'];

const MODE_META: Record<
  PracticeModeFilter,
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
};

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

function ModeIcon({ mode }: { mode: PracticeModeFilter }) {
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
    recallDirection: selection.recallDirection,
    choicePolarity: selection.choicePolarity,
    lapsed: selection.lapsed,
  };
}

function orderedChoiceOptions(
  selection: PracticeSelection,
  deck: PracticeDeckData,
  polarity: ChoicePolarity,
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
  const answerIndex = selection.itemId.length % options.length;
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
  }));
}

function choicePrompt(selection: PracticeSelection): string {
  if (selection.choicePolarity === 'word-to-meaning') {
    return `Що означає «${selection.lemma.lemma}»?`;
  }
  return `Яке слово означає «${glossLabel(selection.lemma)}»?`;
}

function clozeParts(item: PracticeClozeItem): [string, string] {
  const [before, ...after] = item.sentence.split('___');
  return [before, after.join('___')];
}

function shouldLoadCloze(mode: PracticeModeFilter): boolean {
  return mode === 'mixed' || mode === 'cloze';
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
  return {
    deckVersion: decks[0]?.deckVersion ?? `cumulative-${level}`,
    level,
    index: decks.flatMap((deck) => deck.index),
    lexemes: decks.flatMap((deck) => deck.lexemes),
    cloze: decks.flatMap((deck) => deck.cloze),
  };
}

export default function LexiconPractice({
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
    return Boolean(normalized && normalized.cloze.length > 0);
  });
  const [started, setStarted] = useState(autoStart);
  const [mode, setMode] = useState<PracticeModeFilter>(initialMode);
  const [learnerLevel, setLearnerLevel] = useState<CefrLevel>(() =>
    readLearnerLevel(normalizeCefrLevel(deckLevel)),
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState('');
  const [revision, setRevision] = useState(0);
  const [history, setHistory] = useState<SelectionHistoryItem[]>([]);
  const [answerLocked, setAnswerLocked] = useState(false);
  const [streak, setStreak] = useState<StreakState>({
    version: 1,
    current: 0,
    lastPracticeDate: null,
  });
  const [mastered, setMastered] = useState(0);
  const [correctToday, setCorrectToday] = useState(0);
  const [storageWarning, setStorageWarning] = useState<string | null>(null);
  const [clozeInput, setClozeInput] = useState('');
  const [clozeFeedback, setClozeFeedback] = useState<ClozeFeedback | null>(null);
  const [clozeAttemptRecorded, setClozeAttemptRecorded] = useState(false);
  // Lightweight per-level index used to show the due-count on the home BEFORE a mode
  // is started. Superseded by `deck.index` once a full deck loads.
  const [dueIndex, setDueIndex] = useState<PracticeIndexItem[] | null>(null);
  const stageRef = useRef<HTMLDivElement | null>(null);
  // Monotonic id so a slow earlier deck fetch can't overwrite a newer one (rapid level switches).
  const deckRequestId = useRef(0);

  useEffect(() => {
    const state = loadState();
    setStreak(readStreak());
    setMastered(masteredCount(MASTERED_THRESHOLD));
    if (state.flags.corrupt || state.flags.migrationFailed) {
      setStorageWarning('Прогрес призупинено, доки сховище браузера не стане доступним.');
    } else if (state.flags.clockJump) {
      setStorageWarning('Час повторення може бути неточним: змінився годинник пристрою.');
    }
  }, []);

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
            const response = await fetch(`${shardBaseUrl}/practice-index.${shardLevel}.json`);
            if (!response.ok) return [];
            const shard = (await response.json()) as PracticeIndexShard;
            return shard.items ?? [];
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

  const selection = useMemo(() => {
    if (!deck) return null;
    return selectNextPracticeItem(deck, {
      history,
      modeFilter: mode,
      now: new Date(),
    });
  }, [deck, history, mode, revision]);

  useEffect(() => {
    setAnswerLocked(false);
    setClozeInput('');
    setClozeFeedback(null);
    setClozeAttemptRecorded(false);
    if (selection) {
      window.setTimeout(() => stageRef.current?.focus(), 0);
    }
  }, [selection?.itemId]);

  useEffect(() => {
    if (!started) return;
    document.title = `${MODE_LABELS[mode]} Practice - Words of the Day`;
  }, [mode, started]);

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
      if (!nextDeck) {
        // Load every CEFR shard at or below the learner level and merge them, so an
        // A1 learner only ever practices A1 words while a B1 learner gets A1+A2+B1.
        const perLevel = await Promise.all(
          levels.map(async (shardLevel) => {
            const [indexResponse, lexemeResponse] = await Promise.all([
              fetch(`${shardBaseUrl}/practice-index.${shardLevel}.json`),
              fetch(`${shardBaseUrl}/practice-lexemes.${shardLevel}.json`),
            ]);
            // A level shard may not be published yet (e.g. C2); skip it gracefully.
            if (!indexResponse.ok || !lexemeResponse.ok) return null;
            const indexShard = (await indexResponse.json()) as PracticeIndexShard;
            const lexemeShard = (await lexemeResponse.json()) as PracticeLexemeShard;
            return combinePracticeShards(indexShard, lexemeShard);
          }),
        );
        const loaded = perLevel.filter((entry): entry is PracticeDeckData => entry !== null);
        if (loaded.length === 0) {
          throw new Error('Practice shard request failed');
        }
        nextDeck = mergeDecks(loaded, level);
      }
      if (includeCloze && (force || !clozeLoaded)) {
        const clozeBatches = await Promise.all(
          levels.map(async (shardLevel) => {
            const clozeResponse = await fetch(`${shardBaseUrl}/practice-cloze.${shardLevel}.json`);
            if (!clozeResponse.ok) return [];
            const clozeShard = (await clozeResponse.json()) as { cloze: PracticeClozeItem[] };
            return clozeShard.cloze ?? [];
          }),
        );
        nextDeck = { ...nextDeck, cloze: clozeBatches.flat() };
        nextClozeLoaded = true;
      }
      // Ignore the result if a newer fetch (e.g. a later level switch) has superseded this one.
      if (deckRequestId.current !== requestId) return nextDeck;
      setDeck(nextDeck);
      setClozeLoaded(nextClozeLoaded);
      return nextDeck;
    } catch {
      if (deckRequestId.current === requestId) setError('Не вдалося завантажити колоду для практики.');
      return null;
    } finally {
      if (deckRequestId.current === requestId) setLoading(false);
    }
  }

  async function start(nextMode: PracticeModeFilter = mode) {
    setMode(nextMode);
    setStarted(true);
    await ensureDeck(shouldLoadCloze(nextMode));
  }

  async function changeLevel(nextLevel: CefrLevel) {
    if (nextLevel === learnerLevel) return;
    setLearnerLevel(nextLevel);
    writeLearnerLevel(nextLevel);
    // The pool changed: drop the loaded deck + per-session history and, if a session is
    // already running, immediately reload the cumulative pool for the new level.
    setClozeLoaded(false);
    setHistory([]);
    if (started) {
      await ensureDeck(shouldLoadCloze(mode), { level: nextLevel, force: true });
    } else {
      setDeck(null);
    }
  }

  function refreshProgress() {
    const state = loadState();
    setMastered(masteredCount(MASTERED_THRESHOLD));
    if (state.flags.corrupt || state.flags.migrationFailed) {
      setStorageWarning('Прогрес призупинено, доки сховище браузера не стане доступним.');
    }
    setRevision((value) => value + 1);
  }

  function completeSelection(current: PracticeSelection) {
    setHistory((items) => [...items.slice(-49), historyFromSelection(current)]);
    refreshProgress();
  }

  function recordReview(current: PracticeSelection, rating: PracticeRating) {
    try {
      rateCard(current.lemma.lemmaId, current.mode, rating, new Date());
      setStreak(recordStreak());
      if (rating === 'good' || rating === 'easy') {
        setCorrectToday((value) => value + 1);
      }
      setFeedback(`${current.lemma.lemma}: ${RATING_LABELS[rating]}`);
    } catch {
      setStorageWarning('Прогрес призупинено, доки сховище браузера не стане доступним.');
    }
  }

  function rateAndComplete(current: PracticeSelection, rating: PracticeRating) {
    recordReview(current, rating);
    completeSelection(current);
  }

  useEffect(() => {
    if (!started || !selection || selection.mode !== 'flashcards') return undefined;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.altKey || event.ctrlKey || event.metaKey) return;
      const key = event.key.toLowerCase();
      const rating =
        key === 'a' || key === '1'
          ? 'again'
          : key === 'h' || key === '2'
            ? 'hard'
            : key === 'g' || key === '3'
              ? 'good'
              : key === 'e' || key === '4'
                ? 'easy'
                : null;
      if (!rating) return;
      event.preventDefault();
      rateAndComplete(selection, rating);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [started, selection]);

  function handleChoice(option: ChoiceOption) {
    if (!selection || answerLocked) return;
    const rating = option.correct ? 'good' : 'again';
    recordReview(selection, rating);
    setAnswerLocked(true);
    setFeedback(
      option.correct ? `${selection.lemma.lemma}: Правильно` : `${selection.lemma.lemma}: Ще раз`,
    );
    window.setTimeout(() => {
      setAnswerLocked(false);
      completeSelection(selection);
    }, advanceDelayMs);
  }

  function submitCloze(value: string, source: 'typed' | 'chip') {
    if (!selection?.cloze || answerLocked) return;
    const answer = value.trim();
    if (!answer) return;
    const cloze = selection.cloze;
    const correct = czNorm(answer) === czNorm(cloze.form);
    const caseMiss = isWrongCaseAnswer(answer, selection.lemma, cloze);

    if (correct) {
      if (!clozeAttemptRecorded) {
        recordReview(selection, 'good');
      }
      setClozeFeedback({
        kind: 'correct',
        text: `✓ ${cloze.form} (${cloze.caseRule.caseLabel})`,
      });
      setAnswerLocked(true);
      window.setTimeout(() => {
        setAnswerLocked(false);
        completeSelection(selection);
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
      recordReview(selection, 'again');
      setClozeAttemptRecorded(true);
    }
    setClozeFeedback({ kind: 'wrong-word', text: '✗ Не те слово' });
    if (source === 'chip') {
      setAnswerLocked(true);
      window.setTimeout(() => {
        setAnswerLocked(false);
        completeSelection(selection);
      }, advanceDelayMs);
    }
  }

  // Prefer the full deck's index once loaded; otherwise fall back to the eager
  // index so the due-count is live on the home before any mode starts.
  const dueNow = useMemo(() => {
    const entries = deck ? deck.index : dueIndex;
    return entries ? getDueQueue(entries, new Date()).length : 0;
  }, [correctToday, deck, dueIndex, revision]);
  const todayWorkload = correctToday + dueNow;
  const todayPct =
    todayWorkload > 0 ? Math.min(100, (correctToday / todayWorkload) * 100) : correctToday > 0 ? 100 : 0;
  const todayRingStyle = { '--pct': String(todayPct) } as CSSProperties;
  const stageMode: PracticeModeFilter = selection?.mode ?? mode;
  const stageTitle =
    mode === 'mixed' && selection ? `Мікс · ${MODE_META[stageMode].title}` : MODE_META[stageMode].title;
  const correctLabel = `${correctToday} ${uaPlural(correctToday)}`;

  return (
    <section className="lexicon-practice" aria-label="Практика слів дня">
      <p className="lexicon-practice-status" aria-live="polite">
        {feedback || (started ? 'Готово до вправи' : 'Оберіть режим практики')}
      </p>

      {storageWarning && <p className="lexicon-practice-warning">{storageWarning}</p>}

      {!started && (
        <div className="lexicon-practice-home">
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
            <div className="pstat" aria-label={`${dueNow} до повторення`}>
              <span className="val">{deck || dueIndex ? dueNow : '—'}</span>
              <span className="lab">До повторення</span>
            </div>
            <div className="pstat" aria-label={`${mastered} опановано`}>
              <span className="val">{mastered}</span>
              <span className="lab">Опановано</span>
            </div>
            <div className="pstat today">
              <div
                className="ring"
                role="img"
                aria-label={`Сьогодні виконано ${correctToday} із ${todayWorkload}`}
                style={todayRingStyle}
              >
                <b>
                  {correctToday}/{todayWorkload}
                </b>
              </div>
              <div>
                <span className="lab">Сьогодні</span>
              </div>
            </div>
          </div>

          <div className="lexicon-practice-levels">
            <div
              className="lexicon-practice-levels-row"
              role="group"
              aria-label="Рівень учня — практика охоплює цей рівень і нижчі"
            >
              <span className="lexicon-practice-levels-label">Рівень</span>
              {CEFR_LEVELS.map((level) => (
                <button
                  type="button"
                  key={level}
                  className={learnerLevel === level ? 'active' : ''}
                  aria-pressed={learnerLevel === level}
                  onClick={() => void changeLevel(level)}
                >
                  {level}
                </button>
              ))}
            </div>
            <p className="lexicon-practice-muted lexicon-practice-levels-hint">
              Практика обмежена вашим рівнем і нижчими (накопичувально).
            </p>
          </div>

          <div className="mode-grid">
            {MODE_CARD_ORDER.map((practiceMode) => {
              const meta = MODE_META[practiceMode];
              return (
                <button
                  type="button"
                  key={practiceMode}
                  className="mode-card"
                  data-mode={practiceMode}
                  data-accent={meta.accent}
                  aria-pressed={mode === practiceMode}
                  onClick={() => void start(practiceMode)}
                >
                  <div className="mc-top">
                    <span className="mc-ico">
                      <ModeIcon mode={practiceMode} />
                    </span>
                    <span>
                      <span className="mc-title">{meta.title}</span>
                      <span className="mc-en">{meta.en}</span>
                    </span>
                  </div>
                  <span className="mc-desc">{meta.description}</span>
                  <span className="mc-meta">
                    <span className="mc-step">{meta.step}</span>
                    <span className="mc-arrow" aria-hidden="true">
                      →
                    </span>
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {loading && <p className="lexicon-practice-muted">Завантажуємо…</p>}
      {error && <p className="lexicon-practice-warning">{error}</p>}
      {started && (
        <div className="lexicon-practice-stage-shell">
          <div className="lexicon-practice-stage-bar">
            <button type="button" className="stage-back" onClick={() => setStarted(false)}>
              ← Режими
            </button>
            <h2>{stageTitle}</h2>
            <span className="queue-pill" aria-label={correctLabel}>
              {correctLabel}
            </span>
          </div>

          {deck && deck.index.length === 0 && (
            <p className="lexicon-practice-muted">Поки що немає карток для практики.</p>
          )}

          {deck && deck.index.length > 0 && (
        <div className="lexicon-practice-stage" ref={stageRef} tabIndex={-1}>
          {selection ? (
            <PracticeItem
              selection={selection}
              deck={deck}
              answerLocked={answerLocked}
              clozeInput={clozeInput}
              clozeFeedback={clozeFeedback}
                onClozeInput={setClozeInput}
                onFlashcardRating={(rating) => rateAndComplete(selection, rating)}
                onChoice={handleChoice}
                onMatchingComplete={() => rateAndComplete(selection, 'good')}
                onClozeSubmit={submitCloze}
              />
          ) : mode === 'cloze' && deck.cloze.length === 0 ? (
              // Cloze is fail-closed until reviewed sentences are authored (#3797).
              <p className="lexicon-practice-muted" data-testid="practice-cloze-empty">
                Вправи з пропусками для цього рівня ще готуються. Спробуйте флешкартки, добір пар або вибір.
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

function PracticeItem({
  selection,
  deck,
  answerLocked,
  clozeInput,
  clozeFeedback,
  onClozeInput,
  onFlashcardRating,
  onChoice,
  onMatchingComplete,
  onClozeSubmit,
}: {
  selection: PracticeSelection;
  deck: PracticeDeckData;
  answerLocked: boolean;
  clozeInput: string;
  clozeFeedback: ClozeFeedback | null;
  onClozeInput(value: string): void;
  onFlashcardRating(rating: PracticeRating): void;
  onChoice(option: ChoiceOption): void;
  onMatchingComplete(): void;
  onClozeSubmit(value: string, source: 'typed' | 'chip'): void;
}) {
  if (selection.mode === 'flashcards') {
    return (
      <>
        <FlashcardDeck key={selection.itemId} cards={[cardData(selection.lemma)]} />
        <div className="lexicon-rating-bar rating-bar" role="group" aria-label="Оцініть, наскільки легко згадалось">
        {(['again', 'hard', 'good', 'easy'] as const).map((rating, index) => (
          <button
            type="button"
            key={rating}
            className="rate-btn"
            data-rate={rating}
            aria-keyshortcuts={String(index + 1)}
            onClick={() => onFlashcardRating(rating)}
          >
            <span className="rk">{index + 1}</span>
            <span className="rt">{RATING_LABELS[rating]}</span>
          </button>
        ))}
        </div>
      </>
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

  if (selection.mode === 'matching') {
    const pairs = matchingPairs(selection, deck);
    if (!pairs.length) {
      return <p className="lexicon-practice-muted">Зараз немає карток для добору пар.</p>;
    }
    return (
      <div data-testid="practice-matching">
        <MatchUp
          pairs={pairs}
          instruction={`Доберіть пару для «${selection.lemma.lemma}»`}
          onComplete={onMatchingComplete}
        />
      </div>
    );
  }

  const options = orderedChoiceOptions(selection, deck, selection.choicePolarity);
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
          <li key={option.label}>
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
        <p
          className={`lexicon-cloze-feedback ${feedback.kind}`}
          role={feedback.kind === 'wrong-word' ? 'alert' : 'status'}
          aria-live="polite"
        >
          {feedback.text}
        </p>
      )}
    </div>
  );
}
