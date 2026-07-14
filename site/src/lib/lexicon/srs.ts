import {
  createEmptyCard,
  fsrs,
  Rating,
  State,
  type Card as FsrsCard,
  type FSRSParameters,
  type Grade,
  type RecordLogItem,
} from 'ts-fsrs';

export const SRS_STORAGE_KEY = 'lu-lexicon-srs';
export const SRS_SETTINGS_KEY = 'lu-lexicon-srs-settings';
export const SRS_BACKUP_KEY = 'lu-lexicon-srs.backup';
export const PRACTICE_NEW_CARDS_KEY = 'lu-practice-newcards';
export const PRACTICE_SESSION_STORAGE_KEY = 'lu-practice-session';
export const DEFAULT_NEW_PER_SESSION = 8;
export const DEFAULT_NEW_PER_DAY = 20;
export const SESSION_CLOSURE_EXTENSION_MAX = 5;
export const SESSION_ITEM_ESTIMATE_SEC = 20;
/** Levels with published practice shards (C2 ships «скоро» until deck exists). */
export const PUBLISHED_PRACTICE_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1'] as const;

const CURRENT_VERSION = 4;
const SETTINGS_VERSION = 1;
/** Bound synchronous localStorage writes while retaining recent fitting history. */
export const MAX_RAW_REVIEW_LOG_ENTRIES = 2_000;
const RECOVERY_RAW_REVIEW_LOG_ENTRIES = 0;
export const SRS_STORAGE_FULL_WARNING = 'Прогрес не зберігається — сховище переповнене';
const HOUR_MS = 60 * 60 * 1000;
const DAY_MS = 24 * 60 * 60 * 1000;
export const SESSION_RESUME_MAX_MS = 6 * HOUR_MS;
const WIDENED_DUE_WINDOW_MS = 6 * HOUR_MS;
const MIN_WORD_REPEAT_WINDOW = 8;
const DEFAULT_RECOGNITION_STABILITY = 3;

export type PracticeRating = 'again' | 'hard' | 'good' | 'easy';
export const PRACTICE_MODE_DECK_VERSION = 3;
export const PRACTICE_MODES = [
  'flashcards',
  'matching',
  'choice',
  'cloze',
  // Spec v5 (§9, PR #4503) union: all six approved modes are VALID card modes now, so deck
  // rollouts never need another srs.ts change and older clients never quarantine newer-mode
  // cards. Wave-1 decks: paradigm/stress/synonym/classify; heritage/paronym ship fail-closed
  // as curated pairs land. idiom/listening stay out (not approved card modes).
  'paradigm',
  'stress',
  'heritage',
  'synonym',
  'classify',
  'paronym',
] as const;
const PRACTICE_MODE_SET = new Set<string>(PRACTICE_MODES);

export type PracticeMode = (typeof PRACTICE_MODES)[number];
export type PracticeModeFilter = PracticeMode | 'mixed';
export type RecallDirection = 'uk-to-meaning' | 'meaning-to-uk';
export type ChoicePolarity = 'word-to-meaning' | 'meaning-to-word';

export interface PracticeParadigm {
  cases: Record<string, Partial<Record<'singular' | 'plural', string>>>;
}

export interface PracticeLexeme {
  lemmaId: string;
  lemma: string;
  lemmaPlain: string;
  ipa: string | null;
  gloss: string;
  glossClean?: string;
  meaningMcEligible?: boolean;
  pos: string | null;
  cefr: string | null;
  heritage: string | null;
  severity: string | null;
  paradigm: PracticeParadigm;
  semanticBucket?: string | null;
}

export interface PracticeDeckEntry extends PracticeLexeme {
  slug?: string;
  example?: string | null;
  audioKey?: null;
}

export interface PracticeIndexItem {
  lemmaId: string;
  lemma: string;
  cefr: string;
  modes: PracticeMode[];
  hasCloze: boolean;
  clozeIds: string[];
  newOrder: number;
}

export interface PracticeClozeOption {
  optionId: string;
  label: string;
  lemmaId: string;
  kind: 'answer' | 'same-root-lemma' | 'decoy-lemma' | 'decoy-oblique' | string;
  case?: string;
  pos?: string;
  strategy?: string;
}

export interface PracticeCaseRule {
  ruleId: string;
  case: string;
  caseLabel: string;
  trigger: string;
  triggerLabel: string;
  feedback: string;
}

export interface PracticeClozeAttributionSentence {
  sentenceId: string | number;
  author: string;
  license: string;
}

export interface PracticeClozeAttribution {
  source: string;
  sourceUrl?: string;
  uk: PracticeClozeAttributionSentence;
  en: PracticeClozeAttributionSentence;
}

export interface PracticeClozeItem {
  clozeId: string;
  lemmaId: string;
  sentenceFrameId: string;
  sentence: string;
  blankCase: string;
  form: string;
  lemma?: string;
  acceptedAlt?: string[];
  caseRule: PracticeCaseRule;
  clozeEn: string;
  options: PracticeClozeOption[];
  attribution?: PracticeClozeAttribution;
}

export interface PracticeStressItem {
  stressId: string;
  lemmaId: string;
  lemma: string;
  stressed: string;
  unstressed: string;
  stressIndex: number;
  nuclei: { index: number; label: string }[];
  source: string;
}

export interface PracticeClassifyOption {
  value: string;
  labelUk: string;
  labelEn?: string;
}

export interface PracticeClassifySet {
  setId: 'gender' | 'aspect' | 'declension' | 'pos' | string;
  setLabelUk: string;
  setLabelEn?: string;
  answer: string;
  answerLabelUk: string;
  answerLabelEn?: string;
  options: PracticeClassifyOption[];
}

export interface PracticeClassifyItem {
  classifyId: string;
  lemmaId: string;
  lemma: string;
  sets: PracticeClassifySet[];
  source: string;
}

export interface PracticeParadigmItem {
  paradigmId: string;
  lemmaId: string;
  lemma: string;
  slot: {
    case: string;
    number: 'singular' | 'plural';
    labelUk: string;
    labelEn?: string;
  };
  form: string;
  options: { label: string; kind: 'answer' | 'same-paradigm' | string }[];
}

export interface PracticeSynonymItem {
  synonymId: string;
  lemmaId: string;
  targetLemmaId: string;
  polarity: 'synonym' | 'antonym';
  prompt: string;
  answer: string;
  options: { label: string; lemmaId: string; kind: 'answer' | 'distractor' | string }[];
  source: string;
}

export interface PracticeHeritageOption {
  label: string;
}

export interface PracticeHeritageItem {
  heritageId: string;
  lemmaId: string;
  srsKey: string;
  lemma?: string;
  nativeLemma?: string;
  calqueLabel?: string;
  kind: 'lexical' | 'sense_restricted' | string;
  prompt: string;
  answer: string;
  calque: string;
  origin?: string;
  frameIndex?: number;
  cefr: string;
  options: PracticeHeritageOption[];
  rationale: string;
  rationaleUk?: string;
  citations: string[];
  corrections: string[];
  sourceFamily?: string;
  calqueSense?: string;
  authenticSense?: string;
}

export interface PracticeParonymOption {
  label: string;
}

export interface PracticeParonymItem {
  paronymId: string;
  lemmaId: string;
  srsKey: string;
  lemma: string;
  confusable: string;
  distinction_gloss_uk: string;
  frameIndex: number;
  cefr: string;
  prompt: string;
  answer: string;
  options: PracticeParonymOption[];
  origin?: string;
  citations?: string[];
}

export interface PracticeShardMeta {
  schema: string;
  schemaVersion: number;
  deckVersion: string;
  level: string;
  source: string;
  fixtureNote?: string;
}

export interface PracticeIndexShard extends PracticeShardMeta {
  items: PracticeIndexItem[];
  counts: {
    lexemes: number;
    cloze: number;
    clozeEligibleLexemes: number;
    clozeCoverage: number;
  };
}

export interface PracticeLexemeShard extends PracticeShardMeta {
  lexemes: PracticeLexeme[];
}

export interface PracticeClozeShard extends PracticeShardMeta {
  cloze: PracticeClozeItem[];
}

export interface PracticeStressShard extends PracticeShardMeta {
  stress: PracticeStressItem[];
}

export interface PracticeClassifyShard extends PracticeShardMeta {
  classify: PracticeClassifyItem[];
}

export interface PracticeParadigmShard extends PracticeShardMeta {
  paradigm: PracticeParadigmItem[];
}

export interface PracticeSynonymShard extends PracticeShardMeta {
  synonym: PracticeSynonymItem[];
}

export interface PracticeHeritageShard extends PracticeShardMeta {
  heritage: PracticeHeritageItem[];
}

export interface PracticeParonymShard extends PracticeShardMeta {
  paronym: PracticeParonymItem[];
}

export interface PracticeDeckData {
  deckVersion: string;
  level: string;
  index: PracticeIndexItem[];
  lexemes: PracticeLexeme[];
  cloze: PracticeClozeItem[];
  stress?: PracticeStressItem[];
  classify?: PracticeClassifyItem[];
  paradigm?: PracticeParadigmItem[];
  synonym?: PracticeSynonymItem[];
  paronym?: PracticeParonymItem[];
  heritage?: PracticeHeritageItem[];
  fixtureNote?: string;
}

export interface CardState {
  due: number;
  stability: number;
  difficulty: number;
  elapsed_days: number;
  scheduled_days: number;
  learning_steps: number;
  reps: number;
  lapses: number;
  state: State;
  last_review?: number;
}

export interface ReviewLogEntry {
  cardKey: string;
  lemmaId: string;
  mode: PracticeMode;
  rating: PracticeRating;
  state: State;
  due: number;
  stability: number;
  difficulty: number;
  elapsed_days: number;
  last_elapsed_days: number;
  scheduled_days: number;
  learning_steps: number;
  review: number;
  /**
   * §6b weak-area telemetry. Optional, mode-scoped: `blankCase` is the grammatical
   * case of a cloze blank (e.g. `genitive`); `heritageKind` is the heritage-item kind
   * (e.g. `lexical`). Absent for modes that carry no such dimension. Persisted so the
   * client can compute per-case / per-heritage-kind lapse rates without a server.
   */
  blankCase?: string;
  heritageKind?: string;
}

/**
 * Summary retained when raw review entries age out of the bounded fitting window.
 * The key in `reviewAggregates` is the card key; the aggregate deliberately keeps
 * the rating distribution and temporal span needed for future parameter fitting.
 */
export interface ReviewLogAggregate {
  ratings: Record<PracticeRating, number>;
  firstReview: number;
  lastReview: number;
}

/** Optional per-review dimension metadata threaded from the active selection. */
export interface ReviewMeta {
  blankCase?: string;
  heritageKind?: string;
}

export interface SrsSettings {
  version: typeof SETTINGS_VERSION;
  params: FSRSParameters;
}

export interface SrsFlags {
  corrupt: boolean;
  migrationFailed: boolean;
  migrated: boolean;
  backupWritten: boolean;
  storageWriteFailed: boolean;
  storageFull: boolean;
  settingsCorrupt: boolean;
  clockJump: ClockJump | null;
}

export interface ClockJump {
  direction: 'forward' | 'backward';
  deltaDays: number;
}

export interface LoadedSrsState {
  version: typeof CURRENT_VERSION;
  cards: Map<string, CardState>;
  reviews: ReviewLogEntry[];
  reviewAggregates: Record<string, ReviewLogAggregate>;
  settings: SrsSettings;
  flags: SrsFlags;
  raw: string | null;
}

export interface SelectionHistoryItem {
  itemId: string;
  lemmaId: string;
  mode: PracticeMode;
  clozeId?: string;
  sentenceFrameId?: string;
  blankCase?: string;
  classifySetId?: string;
  heritageId?: string;
  recallDirection?: RecallDirection;
  choicePolarity?: ChoicePolarity;
  lapsed?: boolean;
}

export interface PracticeSelection {
  itemId: string;
  lemma: PracticeLexeme;
  indexItem: PracticeIndexItem;
  mode: PracticeMode;
  cardKey: string;
  cardState: CardState | null;
  due: number;
  lapsed: boolean;
  cloze?: PracticeClozeItem;
  stress?: PracticeStressItem;
  classify?: PracticeClassifyItem;
  classifySetId?: string;
  paradigm?: PracticeParadigmItem;
  synonym?: PracticeSynonymItem;
  paronym?: PracticeParonymItem;
  heritage?: PracticeHeritageItem;
  recallDirection: RecallDirection;
  choicePolarity: ChoicePolarity;
}

export type SessionBudget = number | 'until-zero';

export interface PracticeSessionSnapshot {
  sessionSeed: number;
  history: SelectionHistoryItem[];
  budget: SessionBudget;
  completed: number;
  modeFilter: PracticeModeFilter;
  level: string;
  startedAt: number;
  /** Resume helpers — not part of selector state; safe to persist for closure rule. */
  extensionUsed?: number;
  sessionNewIntroduced?: number;
  plannedReviews?: number;
  plannedNew?: number;
  plannedTotal?: number;
  reviewsCompleted?: number;
  unresolvedCardKeys?: string[];
}

/**
 * Unfinished sessions are isolated by mode. This prevents the selection, history, and
 * progress of one drill from being restored into another drill's session.
 */
export type PracticeSessionSnapshots = Partial<Record<PracticeModeFilter, PracticeSessionSnapshot>>;

interface PersistedPracticeSessionSnapshots {
  version: 1;
  byMode: PracticeSessionSnapshots;
}

export interface NewCardsDailyState {
  date: string;
  count: number;
}

export interface SessionScopeStats {
  dueReviews: number;
  plannedNew: number;
  plannedTotal: number;
  estimatedMinutes: number;
}

export interface SessionPoolConstraintState {
  allowNewInPool: boolean;
  newRemainingSession: number;
  newRemainingDaily: number;
  sessionNewIntroduced: number;
}

export interface SelectPracticeOptions {
  now?: Date | number;
  history?: SelectionHistoryItem[];
  modeFilter?: PracticeModeFilter;
  minRecognitionStability?: number;
  clozeSoftCap?: number;
  dueWindowMs?: number;
  wordRepeatWindow?: number;
  sessionSeed?: number;
  /** §6b session pool constraint — eligibility filter only; ordering unchanged. */
  poolFilter?: (candidate: PracticeSelection) => boolean;
}

interface PersistedSrsSchemaV4 {
  version: typeof CURRENT_VERSION;
  cards: Record<string, CardState>;
  reviews?: ReviewLogEntry[];
  reviewAggregates?: Record<string, ReviewLogAggregate>;
  lastSavedAt?: number;
}

interface StorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

export type ParsedCardKey =
  | { lemmaId: string; mode: PracticeMode; quarantined: false }
  | { lemmaId: string; mode: null; rawMode: string; quarantined: true };

const FSRS6_DEFAULT_PARAMS: FSRSParameters = {
  request_retention: 0.9,
  maximum_interval: 36500,
  w: [
    0.212, 1.2931, 2.3065, 8.2956, 6.4133, 0.8334, 3.0194, 0.001, 1.8722,
    0.1666, 0.796, 1.4835, 0.0614, 0.2629, 1.6483, 0.6014, 1.8729, 0.5425,
    0.0912, 0.0658, 0.1542,
  ],
  enable_fuzz: false,
  enable_short_term: true,
  learning_steps: ['1m', '10m'],
  relearning_steps: ['10m'],
};

const RATING_TO_FSRS: Record<PracticeRating, Grade> = {
  again: Rating.Again,
  hard: Rating.Hard,
  good: Rating.Good,
  easy: Rating.Easy,
};

function hashString(value: string): number {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function mulberry32(seed: number): () => number {
  let value = seed >>> 0;
  return () => {
    value = (value + 0x6d2b79f5) >>> 0;
    let result = Math.imul(value ^ (value >>> 15), 1 | value);
    result ^= result + Math.imul(result ^ (result >>> 7), 61 | result);
    return ((result ^ (result >>> 14)) >>> 0) / 4294967296;
  };
}

export function seededPracticeHash(sessionSeed: number | undefined, value: string): number {
  const seed = (Number.isFinite(sessionSeed) ? sessionSeed : 0) as number;
  return Math.floor(mulberry32((seed >>> 0) ^ hashString(value))() * 4294967296);
}

export function seededAnswerIndex(
  sessionSeed: number | undefined,
  itemId: string,
  optionCount: number,
): number {
  if (optionCount <= 0) return 0;
  return seededPracticeHash(sessionSeed, `choice:${itemId}`) % optionCount;
}

const memoryStore = new Map<string, string>();
const memoryStorage: StorageLike = {
  getItem: (key) => memoryStore.get(key) ?? null,
  setItem: (key, value) => {
    memoryStore.set(key, value);
  },
  removeItem: (key) => {
    memoryStore.delete(key);
  },
};

let activeState: LoadedSrsState | null = null;
let activeStorage: StorageLike | null = null;

function resolveStorage(): StorageLike {
  if (typeof window === 'undefined') return memoryStorage;
  try {
    return window.localStorage;
  } catch {
    return memoryStorage;
  }
}

function currentStorage(): StorageLike {
  return activeStorage ?? resolveStorage();
}

function emptyFlags(clockJump: ClockJump | null = null): SrsFlags {
  return {
    corrupt: false,
    migrationFailed: false,
    migrated: false,
    backupWritten: false,
    storageWriteFailed: false,
    storageFull: false,
    settingsCorrupt: false,
    clockJump,
  };
}

function cloneParams(params: FSRSParameters = FSRS6_DEFAULT_PARAMS): FSRSParameters {
  return {
    ...params,
    w: [...params.w],
    learning_steps: [...params.learning_steps],
    relearning_steps: [...params.relearning_steps],
  };
}

function defaultSettings(): SrsSettings {
  return {
    version: SETTINGS_VERSION,
    params: cloneParams(),
  };
}

function loadSettings(storage: StorageLike): { settings: SrsSettings; corrupt: boolean } {
  const raw = storage.getItem(SRS_SETTINGS_KEY);
  if (!raw) return { settings: defaultSettings(), corrupt: false };
  try {
    const parsed = JSON.parse(raw) as Partial<SrsSettings>;
    if (parsed.version !== SETTINGS_VERSION || typeof parsed.params !== 'object') {
      return { settings: defaultSettings(), corrupt: true };
    }
    return {
      settings: {
        version: SETTINGS_VERSION,
        params: cloneParams({ ...FSRS6_DEFAULT_PARAMS, ...parsed.params }),
      },
      corrupt: false,
    };
  } catch {
    return { settings: defaultSettings(), corrupt: true };
  }
}

function toTime(value: Date | number | string | undefined | null): number | null {
  if (value === undefined || value === null) return null;
  const time = value instanceof Date ? value.getTime() : new Date(value).getTime();
  return Number.isFinite(time) ? time : null;
}

function finiteNumber(value: unknown, fallback: number): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

function normalizeStateValue(value: unknown): State {
  return value === State.Learning || value === State.Review || value === State.Relearning
    ? value
    : State.New;
}

function normalizeCard(raw: unknown): CardState | null {
  if (!raw || typeof raw !== 'object') return null;
  const source = raw as Record<string, unknown>;
  const due = toTime(source.due as Date | number | string | undefined);
  if (due === null) return null;
  const lastReview = toTime(source.last_review as Date | number | string | undefined);
  return {
    due,
    stability: finiteNumber(source.stability, 0),
    difficulty: finiteNumber(source.difficulty, 0),
    elapsed_days: finiteNumber(source.elapsed_days, 0),
    scheduled_days: finiteNumber(source.scheduled_days, 0),
    learning_steps: finiteNumber(source.learning_steps, 0),
    reps: finiteNumber(source.reps, 0),
    lapses: finiteNumber(source.lapses, 0),
    state: normalizeStateValue(source.state),
    ...(lastReview === null ? {} : { last_review: lastReview }),
  };
}

function normalizeCards(rawCards: unknown, migrateLegacyKeys = false): Map<string, CardState> | null {
  if (!rawCards || typeof rawCards !== 'object' || Array.isArray(rawCards)) return null;
  const cards = new Map<string, CardState>();
  for (const [rawKey, rawCard] of Object.entries(rawCards as Record<string, unknown>)) {
    const normalized = normalizeCard(rawCard);
    if (!normalized) return null;
    const key = migrateLegacyKeys && !rawKey.includes('::') ? cardKey(rawKey, 'flashcards') : rawKey;
    cards.set(key, normalized);
  }
  return cards;
}

function isPracticeRating(value: unknown): value is PracticeRating {
  return value === 'again' || value === 'hard' || value === 'good' || value === 'easy';
}

export function isPracticeMode(value: unknown): value is PracticeMode {
  return typeof value === 'string' && PRACTICE_MODE_SET.has(value);
}

export function parseCardKey(key: string): ParsedCardKey {
  const separatorIndex = key.indexOf('::');
  if (separatorIndex < 0) {
    return {
      lemmaId: key,
      mode: 'flashcards',
      quarantined: false,
    };
  }
  const lemmaId = key.slice(0, separatorIndex) || key;
  const rawMode = key.slice(separatorIndex + 2);
  if (!isPracticeMode(rawMode)) {
    return {
      lemmaId,
      mode: null,
      rawMode,
      quarantined: true,
    };
  }
  return {
    lemmaId,
    mode: rawMode,
    quarantined: false,
  };
}

function normalizeReview(raw: unknown): ReviewLogEntry | null {
  if (!raw || typeof raw !== 'object') return null;
  const source = raw as Record<string, unknown>;
  const due = toTime(source.due as Date | number | string | undefined);
  const review = toTime(source.review as Date | number | string | undefined);
  if (due === null || review === null) return null;
  const rating = source.rating;
  if (!isPracticeRating(rating)) return null;
  const legacySlug = typeof source.slug === 'string' ? source.slug : null;
  const lemmaId = typeof source.lemmaId === 'string' ? source.lemmaId : legacySlug;
  if (!lemmaId) return null;
  const mode = isPracticeMode(source.mode) ? source.mode : 'flashcards';
  const key = typeof source.cardKey === 'string' ? source.cardKey : cardKey(lemmaId, mode);
  return {
    cardKey: key,
    lemmaId,
    mode,
    rating,
    state: normalizeStateValue(source.state),
    due,
    stability: finiteNumber(source.stability, 0),
    difficulty: finiteNumber(source.difficulty, 0),
    elapsed_days: finiteNumber(source.elapsed_days, 0),
    last_elapsed_days: finiteNumber(source.last_elapsed_days, 0),
    scheduled_days: finiteNumber(source.scheduled_days, 0),
    learning_steps: finiteNumber(source.learning_steps, 0),
    review,
    ...(typeof source.blankCase === 'string' ? { blankCase: source.blankCase } : {}),
    ...(typeof source.heritageKind === 'string' ? { heritageKind: source.heritageKind } : {}),
  };
}

function normalizeReviews(rawReviews: unknown): ReviewLogEntry[] | null {
  if (rawReviews === undefined) return [];
  if (!Array.isArray(rawReviews)) return null;
  const reviews: ReviewLogEntry[] = [];
  for (const raw of rawReviews) {
    const review = normalizeReview(raw);
    if (!review) return null;
    reviews.push(review);
  }
  return reviews;
}

function emptyRatingCounts(): Record<PracticeRating, number> {
  return { again: 0, hard: 0, good: 0, easy: 0 };
}

function normalizeReviewAggregate(raw: unknown): ReviewLogAggregate | null {
  if (!raw || typeof raw !== 'object') return null;
  const source = raw as Record<string, unknown>;
  const ratings = source.ratings;
  const firstReview = toTime(source.firstReview as Date | number | string | undefined);
  const lastReview = toTime(source.lastReview as Date | number | string | undefined);
  if (!ratings || typeof ratings !== 'object' || firstReview === null || lastReview === null) return null;
  const sourceRatings = ratings as Record<string, unknown>;
  const normalizedRatings = emptyRatingCounts();
  for (const rating of Object.keys(normalizedRatings) as PracticeRating[]) {
    const value = sourceRatings[rating];
    if (typeof value !== 'number' || !Number.isSafeInteger(value) || value < 0) return null;
    normalizedRatings[rating] = value;
  }
  return { ratings: normalizedRatings, firstReview, lastReview };
}

function normalizeReviewAggregates(raw: unknown): Record<string, ReviewLogAggregate> | null {
  if (raw === undefined) return {};
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return null;
  const aggregates: Record<string, ReviewLogAggregate> = {};
  for (const [key, value] of Object.entries(raw as Record<string, unknown>)) {
    if (!key) return null;
    const aggregate = normalizeReviewAggregate(value);
    if (!aggregate) return null;
    aggregates[key] = aggregate;
  }
  return aggregates;
}

function addReviewToAggregates(
  review: ReviewLogEntry,
  reviewAggregates: Record<string, ReviewLogAggregate>,
): void {
  const aggregate = reviewAggregates[review.cardKey];
  if (aggregate) {
    aggregate.ratings[review.rating] += 1;
    aggregate.firstReview = Math.min(aggregate.firstReview, review.review);
    aggregate.lastReview = Math.max(aggregate.lastReview, review.review);
    return;
  }
  const ratings = emptyRatingCounts();
  ratings[review.rating] = 1;
  reviewAggregates[review.cardKey] = {
    ratings,
    firstReview: review.review,
    lastReview: review.review,
  };
}

function compactReviewHistory(
  reviews: ReviewLogEntry[],
  reviewAggregates: Record<string, ReviewLogAggregate>,
  maximumRawEntries: number,
): boolean {
  const entriesToCompact = Math.max(0, reviews.length - maximumRawEntries);
  if (entriesToCompact === 0) return false;
  for (const review of reviews.splice(0, entriesToCompact)) {
    addReviewToAggregates(review, reviewAggregates);
  }
  return true;
}

function hydrateStore(
  store: PersistedSrsSchemaV4,
  settings: SrsSettings,
  raw: string | null,
  flags: SrsFlags,
): LoadedSrsState | null {
  const cards = normalizeCards(store.cards);
  const reviews = normalizeReviews(store.reviews);
  const reviewAggregates = normalizeReviewAggregates(store.reviewAggregates);
  if (!cards || !reviews || !reviewAggregates) return null;
  return {
    version: CURRENT_VERSION,
    cards,
    reviews,
    reviewAggregates,
    settings,
    flags,
    raw,
  };
}

function migrateToCurrent(parsed: Record<string, unknown>): PersistedSrsSchemaV4 | null {
  if (parsed.version === CURRENT_VERSION) return parsed as unknown as PersistedSrsSchemaV4;
  if (parsed.version !== 1 && parsed.version !== 2 && parsed.version !== 3) return null;
  const cards = normalizeCards(parsed.cards, true);
  const reviews = normalizeReviews(parsed.reviews);
  const reviewAggregates = normalizeReviewAggregates(parsed.reviewAggregates);
  if (!cards || !reviews || !reviewAggregates) return null;
  compactReviewHistory(reviews, reviewAggregates, MAX_RAW_REVIEW_LOG_ENTRIES);
  return {
    version: CURRENT_VERSION,
    cards: Object.fromEntries(cards),
    reviews,
    reviewAggregates,
    lastSavedAt: Date.now(),
  };
}

function serializeState(state: LoadedSrsState, savedAt: number): string {
  const store: PersistedSrsSchemaV4 = {
    version: CURRENT_VERSION,
    cards: Object.fromEntries(state.cards),
    reviews: state.reviews,
    reviewAggregates: state.reviewAggregates,
    lastSavedAt: savedAt,
  };
  return JSON.stringify(store);
}

function serializeSettings(settings: SrsSettings): string {
  return JSON.stringify({
    version: SETTINGS_VERSION,
    params: settings.params,
  });
}

export function detectClockJump(
  previous: Date | number | string | undefined,
  now: Date | number = Date.now(),
): ClockJump | null {
  const previousTime = toTime(previous);
  const nowTime = toTime(now);
  if (previousTime === null || nowTime === null) return null;
  const delta = nowTime - previousTime;
  if (Math.abs(delta) <= 7 * DAY_MS) return null;
  return {
    direction: delta > 0 ? 'forward' : 'backward',
    deltaDays: Math.round(Math.abs(delta) / DAY_MS),
  };
}

export function loadState(
  storage: StorageLike = resolveStorage(),
  now: Date | number = Date.now(),
): LoadedSrsState {
  const raw = storage.getItem(SRS_STORAGE_KEY);
  if (
    activeState?.flags.storageWriteFailed &&
    activeStorage === storage &&
    activeState.raw === raw
  ) {
    return activeState;
  }

  activeStorage = storage;
  const { settings, corrupt: settingsCorrupt } = loadSettings(storage);
  if (!raw) {
    activeState = {
      version: CURRENT_VERSION,
      cards: new Map(),
      reviews: [],
      reviewAggregates: {},
      settings,
      flags: { ...emptyFlags(), settingsCorrupt },
      raw: null,
    };
    return activeState;
  }

  let parsed: Record<string, unknown>;
  try {
    parsed = JSON.parse(raw) as Record<string, unknown>;
  } catch {
    activeState = {
      version: CURRENT_VERSION,
      cards: new Map(),
      reviews: [],
      reviewAggregates: {},
      settings,
      flags: { ...emptyFlags(), corrupt: true, settingsCorrupt },
      raw,
    };
    return activeState;
  }

  if (parsed.version === CURRENT_VERSION) {
    const state = hydrateStore(parsed as unknown as PersistedSrsSchemaV4, settings, raw, {
      ...emptyFlags(),
      settingsCorrupt,
      clockJump: detectClockJump((parsed as unknown as PersistedSrsSchemaV4).lastSavedAt, now),
    });
    if (state) {
      if (compactReviewHistory(state.reviews, state.reviewAggregates, MAX_RAW_REVIEW_LOG_ENTRIES)) {
        persistWithQuotaRecovery(state, storage, toTime(now) ?? Date.now());
      }
      activeState = state;
      return state;
    }
    activeState = {
      version: CURRENT_VERSION,
      cards: new Map(),
      reviews: [],
      reviewAggregates: {},
      settings,
      flags: { ...emptyFlags(), corrupt: true, settingsCorrupt },
      raw,
    };
    return activeState;
  }

  try {
    const migrated = migrateToCurrent(parsed);
    if (!migrated) throw new Error('unsupported SRS schema');
    const state = hydrateStore(migrated, settings, raw, {
      ...emptyFlags(),
      migrated: true,
      settingsCorrupt,
      clockJump: detectClockJump(migrated.lastSavedAt, now),
    });
    if (!state) throw new Error('migrated SRS schema is invalid');
    activeState = state;
    persistWithQuotaRecovery(state, storage, toTime(now) ?? Date.now());
    return state;
  } catch {
    activeState = {
      version: CURRENT_VERSION,
      cards: new Map(),
      reviews: [],
      reviewAggregates: {},
      settings,
      flags: { ...emptyFlags(), migrationFailed: true, settingsCorrupt },
      raw,
    };
    return activeState;
  }
}

function currentState(): LoadedSrsState {
  return activeState ?? loadState();
}

export function saveState(
  state: LoadedSrsState = currentState(),
  storage: StorageLike = resolveStorage(),
  savedAt: number = Date.now(),
): { ok: boolean; error?: unknown } {
  if (state.flags.corrupt || state.flags.migrationFailed) {
    return { ok: false, error: new Error('SRS storage is corrupt') };
  }
  const previousRaw = state.raw;
  let nextRaw: string;
  try {
    nextRaw = serializeState(state, savedAt);
  } catch (error) {
    return { ok: false, error };
  }
  try {
    storage.setItem(SRS_STORAGE_KEY, nextRaw);
  } catch (error) {
    return { ok: false, error };
  }

  state.raw = nextRaw;
  activeState = state;
  activeStorage = storage;
  state.flags.backupWritten = false;

  try {
    storage.setItem(SRS_SETTINGS_KEY, serializeSettings(state.settings));
  } catch {
    // Scheduling state is already durable. Settings are unchanged during ratings and can retry later.
  }

  if (previousRaw && previousRaw !== nextRaw) {
    try {
      storage.setItem(SRS_BACKUP_KEY, previousRaw);
      state.flags.backupWritten = true;
    } catch {
      // A backup must never turn a successful primary write into lost progress.
    }
  }
  return { ok: true };
}

function isQuotaExceededError(error: unknown): boolean {
  if (!error || typeof error !== 'object') return false;
  const candidate = error as { name?: unknown; code?: unknown };
  return (
    candidate.name === 'QuotaExceededError' ||
    candidate.name === 'NS_ERROR_DOM_QUOTA_REACHED' ||
    candidate.code === 22 ||
    candidate.code === 1014
  );
}

function persistWithQuotaRecovery(
  state: LoadedSrsState,
  storage: StorageLike,
  savedAt: number,
): { ok: boolean; error?: unknown } {
  let result = saveState(state, storage, savedAt);
  if (result.ok) {
    state.flags.storageWriteFailed = false;
    state.flags.storageFull = false;
    return result;
  }
  if (!isQuotaExceededError(result.error)) {
    state.flags.storageWriteFailed = true;
    activeState = state;
    return result;
  }

  try {
    storage.removeItem(SRS_BACKUP_KEY);
  } catch {
    // Continue to the retry; a storage implementation may allow writes despite a failed removal.
  }
  result = saveState(state, storage, savedAt);
  if (result.ok) {
    state.flags.storageWriteFailed = false;
    state.flags.storageFull = false;
    return result;
  }
  if (!isQuotaExceededError(result.error)) {
    state.flags.storageWriteFailed = true;
    activeState = state;
    return result;
  }

  compactReviewHistory(state.reviews, state.reviewAggregates, RECOVERY_RAW_REVIEW_LOG_ENTRIES);
  result = saveState(state, storage, savedAt);
  if (result.ok) {
    state.flags.storageWriteFailed = false;
    state.flags.storageFull = false;
    return result;
  }

  state.flags.storageWriteFailed = true;
  if (isQuotaExceededError(result.error)) {
    state.flags.storageFull = true;
    activeState = state;
  }
  return result;
}

function fsrsCardFromState(card: CardState): FsrsCard {
  return {
    due: new Date(card.due),
    stability: card.stability,
    difficulty: card.difficulty,
    elapsed_days: card.elapsed_days,
    scheduled_days: card.scheduled_days,
    learning_steps: card.learning_steps,
    reps: card.reps,
    lapses: card.lapses,
    state: card.state,
    ...(card.last_review === undefined ? {} : { last_review: new Date(card.last_review) }),
  };
}

function stateFromFsrsCard(card: FsrsCard): CardState {
  return {
    due: card.due.getTime(),
    stability: card.stability,
    difficulty: card.difficulty,
    elapsed_days: card.elapsed_days,
    scheduled_days: card.scheduled_days,
    learning_steps: card.learning_steps,
    reps: card.reps,
    lapses: card.lapses,
    state: card.state,
    ...(card.last_review ? { last_review: card.last_review.getTime() } : {}),
  };
}

function serializeReview(
  key: string,
  lemmaId: string,
  mode: PracticeMode,
  rating: PracticeRating,
  record: RecordLogItem,
  meta?: ReviewMeta,
): ReviewLogEntry {
  return {
    cardKey: key,
    lemmaId,
    mode,
    rating,
    state: record.log.state,
    due: record.log.due.getTime(),
    stability: record.log.stability,
    difficulty: record.log.difficulty,
    elapsed_days: record.log.elapsed_days,
    last_elapsed_days: record.log.last_elapsed_days,
    scheduled_days: record.log.scheduled_days,
    learning_steps: record.log.learning_steps,
    review: record.log.review.getTime(),
    ...(meta?.blankCase ? { blankCase: meta.blankCase } : {}),
    ...(meta?.heritageKind ? { heritageKind: meta.heritageKind } : {}),
  };
}

export function cardKey(lemmaId: string, mode: PracticeMode): string {
  return `${lemmaId}::${mode}`;
}

export function rateCard(
  lemmaId: string,
  rating: PracticeRating,
  reviewDate?: Date | number,
): CardState;
export function rateCard(
  lemmaId: string,
  mode: PracticeMode,
  rating: PracticeRating,
  reviewDate?: Date | number,
  meta?: ReviewMeta,
): CardState;
export function rateCard(
  lemmaId: string,
  modeOrRating: PracticeMode | PracticeRating,
  ratingOrDate?: PracticeRating | Date | number,
  maybeDate?: Date | number,
  meta?: ReviewMeta,
): CardState {
  const mode = isPracticeRating(modeOrRating) ? 'flashcards' : modeOrRating;
  const rating = isPracticeRating(modeOrRating) ? modeOrRating : ratingOrDate;
  if (!isPracticeRating(rating)) {
    throw new Error('rating is required');
  }
  const rawDate = isPracticeRating(modeOrRating) ? ratingOrDate : maybeDate;
  const reviewDate = rawDate instanceof Date ? rawDate : new Date(rawDate ?? Date.now());
  const state = currentState();
  const scheduler = fsrs(state.settings.params);
  const key = cardKey(lemmaId, mode);
  const currentCard = state.cards.get(key);
  const fsrsCard = currentCard ? fsrsCardFromState(currentCard) : createEmptyCard(reviewDate);
  const record = scheduler.next(fsrsCard, reviewDate, RATING_TO_FSRS[rating]);
  const next = stateFromFsrsCard(record.card);
  state.cards.set(key, next);
  state.reviews.push(serializeReview(key, lemmaId, mode, rating, record, meta));
  compactReviewHistory(state.reviews, state.reviewAggregates, MAX_RAW_REVIEW_LOG_ENTRIES);
  persistWithQuotaRecovery(state, currentStorage(), reviewDate.getTime());
  return next;
}

export function masteredCount(threshold = 21, mode: PracticeMode = 'flashcards'): number {
  const state = currentState();
  let count = 0;
  for (const [key, card] of state.cards.entries()) {
    const parsed = parseCardKey(key);
    if (!parsed.quarantined && parsed.mode === mode && card.stability >= threshold) count += 1;
  }
  return count;
}

function lexemeId(entry: Pick<PracticeLexeme, 'lemmaId'> | { slug?: string; lemma?: string }): string {
  if ('lemmaId' in entry && entry.lemmaId) return entry.lemmaId;
  const fallback = entry as { slug?: string; lemma?: string };
  return fallback.slug ?? fallback.lemma ?? '';
}

export function getDueQueue<T extends Pick<PracticeLexeme, 'lemmaId'> | PracticeDeckEntry>(
  entries: T[],
  now: Date | number = Date.now(),
  mode: PracticeMode = 'flashcards',
): T[] {
  const state = currentState();
  const nowTime = toTime(now) ?? Date.now();
  return [...entries]
    .filter((entry) => {
      const key = cardKey(lexemeId(entry), mode);
      const card = state.cards.get(key);
      return !card || card.due <= nowTime;
    })
    .sort((left, right) => {
      const leftCard = state.cards.get(cardKey(lexemeId(left), mode));
      const rightCard = state.cards.get(cardKey(lexemeId(right), mode));
      const leftDue = leftCard?.due ?? 0;
      const rightDue = rightCard?.due ?? 0;
      return leftDue - rightDue || lexemeId(left).localeCompare(lexemeId(right));
    });
}

interface DeckMaps {
  lexemes: Map<string, PracticeLexeme>;
  cloze: Map<string, PracticeClozeItem>;
  stress: Map<string, PracticeStressItem>;
  classify: Map<string, PracticeClassifyItem>;
  paradigm: Map<string, PracticeParadigmItem[]>;
  synonym: Map<string, PracticeSynonymItem[]>;
  paronym: Map<string, PracticeParonymItem[]>;
  heritage: Map<string, PracticeHeritageItem[]>;
}

const deckMapsCache = new WeakMap<PracticeDeckData, DeckMaps>();
const staticCandidateCache = new WeakMap<PracticeDeckData, Map<PracticeModeFilter, PracticeSelection[]>>();

function deckMaps(deck: PracticeDeckData): DeckMaps {
  const cached = deckMapsCache.get(deck);
  if (cached) return cached;
  const groupByLemma = <T extends { lemmaId: string }>(items: T[] | undefined) => {
    const grouped = new Map<string, T[]>();
    for (const item of items ?? []) {
      const bucket = grouped.get(item.lemmaId) ?? [];
      bucket.push(item);
      grouped.set(item.lemmaId, bucket);
    }
    return grouped;
  };
  const maps = {
    lexemes: new Map(deck.lexemes.map((lexeme) => [lexeme.lemmaId, lexeme])),
    cloze: new Map(deck.cloze.map((item) => [item.clozeId, item])),
    stress: new Map((deck.stress ?? []).map((item) => [item.lemmaId, item])),
    classify: new Map((deck.classify ?? []).map((item) => [item.lemmaId, item])),
    paradigm: groupByLemma(deck.paradigm),
    synonym: groupByLemma(deck.synonym),
    paronym: groupByLemma(deck.paronym),
    heritage: groupByLemma(deck.heritage),
  };
  deckMapsCache.set(deck, maps);
  return maps;
}

function recognitionMastered(
  lemmaId: string,
  state: LoadedSrsState,
  threshold: number,
): boolean {
  return (['flashcards', 'matching'] as PracticeMode[]).some((mode) => {
    const card = state.cards.get(cardKey(lemmaId, mode));
    return Boolean(card && card.stability >= threshold);
  });
}

function makeItemId(lemmaId: string, mode: PracticeMode, clozeId?: string): string {
  return clozeId ? `${lemmaId}:${mode}:${clozeId}` : `${lemmaId}:${mode}`;
}

function lastRecallDirection(history: SelectionHistoryItem[]): RecallDirection | undefined {
  for (let index = history.length - 1; index >= 0; index -= 1) {
    const direction = history[index].recallDirection;
    if (direction) return direction;
  }
  return undefined;
}

function directionFor(candidateKey: string, last: RecallDirection | undefined): RecallDirection {
  if (last === 'uk-to-meaning') return 'meaning-to-uk';
  if (last === 'meaning-to-uk') return 'uk-to-meaning';
  return candidateKey.length % 2 === 0 ? 'uk-to-meaning' : 'meaning-to-uk';
}

function lastChoicePolarity(history: SelectionHistoryItem[]): ChoicePolarity | undefined {
  for (let index = history.length - 1; index >= 0; index -= 1) {
    const polarity = history[index].choicePolarity;
    if (polarity) return polarity;
  }
  return undefined;
}

function polarityFor(candidateKey: string, last: ChoicePolarity | undefined): ChoicePolarity {
  if (last === 'word-to-meaning') return 'meaning-to-word';
  if (last === 'meaning-to-word') return 'word-to-meaning';
  return candidateKey.length % 2 === 0 ? 'word-to-meaning' : 'meaning-to-word';
}

function sessionCounts(history: SelectionHistoryItem[]): Record<PracticeMode, number> {
  const counts = Object.fromEntries(PRACTICE_MODES.map((mode) => [mode, 0])) as Record<PracticeMode, number>;
  for (const item of history) {
    counts[item.mode] += 1;
  }
  return counts;
}

interface CandidatePenaltyContext {
  counts: Record<PracticeMode, number>;
  availableModes: Set<PracticeMode>;
  recent: SelectionHistoryItem[];
  lastThreeModes: Set<PracticeMode>;
  candidateCases: Set<string>;
  recentCases: Set<string>;
  last: SelectionHistoryItem | undefined;
  expectedModeCount: number;
}

function candidatePenaltyContext(
  candidates: PracticeSelection[],
  history: SelectionHistoryItem[],
): CandidatePenaltyContext {
  const availableModes = new Set<PracticeMode>();
  const candidateCases = new Set<string>();
  for (const candidate of candidates) {
    availableModes.add(candidate.mode);
    if (candidate.cloze) candidateCases.add(candidate.cloze.blankCase);
  }
  const recent = history.slice(-12);
  const recentCases = new Set<string>();
  for (const item of history.slice(-8)) {
    if (item.mode === 'cloze' && item.blankCase) recentCases.add(item.blankCase);
  }
  const total = Math.max(1, history.length);
  return {
    counts: sessionCounts(history),
    availableModes,
    recent,
    lastThreeModes: new Set(history.slice(-3).map((item) => item.mode)),
    candidateCases,
    recentCases,
    last: history.at(-1),
    expectedModeCount: total / Math.max(1, availableModes.size),
  };
}

function candidatePenalty(
  candidate: PracticeSelection,
  context: CandidatePenaltyContext,
  historyLength: number,
  clozeSoftCap: number,
  nowTime: number,
): number {
  if (candidate.lapsed) return -100_000;
  let penalty = 0;
  if (context.lastThreeModes.has(candidate.mode)) penalty += 18;
  if (historyLength < 8 && !context.counts[candidate.mode] && context.availableModes.size > 1) {
    penalty -= 45;
  }
  penalty -= Math.max(0, context.expectedModeCount - context.counts[candidate.mode]) * 3;

  if (candidate.mode === 'cloze' && context.recent.length >= 4) {
    const clozeRatio =
      context.recent.filter((item) => item.mode === 'cloze').length / context.recent.length;
    if (clozeRatio >= clozeSoftCap && candidate.due > nowTime) penalty += 35;
  }

  if (candidate.cloze) {
    if (context.candidateCases.size >= 3 && context.recentCases.size < 3) {
      penalty += context.recentCases.has(candidate.cloze.blankCase) ? 16 : -12;
    }
    if (context.last?.sentenceFrameId === candidate.cloze.sentenceFrameId) penalty += 60;
  }
  return penalty;
}

function applySpacingFilters(
  pool: PracticeSelection[],
  history: SelectionHistoryItem[],
  wordRepeatWindow: number,
): PracticeSelection[] {
  const last = history.at(-1);
  let filtered = pool.filter(
    (candidate) => candidate.lapsed || !last || candidate.itemId !== last.itemId,
  );
  filtered = filtered.filter(
    (candidate) =>
      candidate.lapsed ||
      !candidate.cloze ||
      !last?.sentenceFrameId ||
      candidate.cloze.sentenceFrameId !== last.sentenceFrameId,
  );
  const wordSpaced = filtered.filter(
    (candidate) =>
      candidate.lapsed ||
      !history.slice(-wordRepeatWindow).some((item) => item.lemmaId === candidate.lemma.lemmaId),
  );
  return wordSpaced.length > 0 ? wordSpaced : filtered;
}

function urgencyBucket(candidate: PracticeSelection, nowTime: number): number {
  if (candidate.lapsed) return -1_000_000_000;
  if (!candidate.cardState) return 1;
  return Math.floor((candidate.due - nowTime) / HOUR_MS);
}

function levelMatchBias(candidate: PracticeSelection, deckLevel: string): number {
  if (candidate.cardState) return 0;
  return candidate.indexItem.cefr === deckLevel ? 0 : 1;
}

function applyPoolFilter(
  pool: PracticeSelection[],
  poolFilter?: (candidate: PracticeSelection) => boolean,
): PracticeSelection[] {
  if (!poolFilter) return pool;
  return pool.filter(poolFilter);
}

function rankCandidates(
  pool: PracticeSelection[],
  history: SelectionHistoryItem[],
  clozeSoftCap: number,
  nowTime: number,
  deckLevel: string,
  sessionSeed: number | undefined,
): PracticeSelection | null {
  // Urgency is the PRIMARY sort key (lapsed first, then most-overdue); the soft
  // anti-monotony penalty is only a TIEBREAK within the same urgency bucket. Adding the
  // penalty to the urgency score (as before) let a +18–60 penalty leak across hour-buckets
  // and overtake a genuinely-more-due card — variety must never delay a due/lapsed card.
  const context = candidatePenaltyContext(pool, history);
  const ranked = pool.map((candidate) => ({
    candidate,
    urgency: urgencyBucket(candidate, nowTime),
    penalty: candidatePenalty(candidate, context, history.length, clozeSoftCap, nowTime),
    levelBias: levelMatchBias(candidate, deckLevel),
    seedHash: seededPracticeHash(sessionSeed, candidate.itemId),
  }));
  return (
    ranked.sort((left, right) => {
      return (
        left.urgency - right.urgency ||
        left.penalty - right.penalty ||
        left.levelBias - right.levelBias ||
        left.seedHash - right.seedHash ||
        left.candidate.itemId.localeCompare(right.candidate.itemId)
      );
    })[0]?.candidate ?? null
  );
}

function cachedSelection(
  selection: Omit<PracticeSelection, 'cardState' | 'due' | 'lapsed' | 'recallDirection' | 'choicePolarity'>,
): PracticeSelection {
  return {
    ...selection,
    cardState: null,
    due: 0,
    lapsed: false,
    recallDirection: 'uk-to-meaning',
    choicePolarity: 'word-to-meaning',
  };
}

function selectionSnapshot(selection: PracticeSelection): PracticeSelection {
  return { ...selection };
}

function buildStaticCandidates(deck: PracticeDeckData, modeFilter: PracticeModeFilter): PracticeSelection[] {
  const maps = deckMaps(deck);
  const candidates: PracticeSelection[] = [];

  for (const indexItem of deck.index) {
    const lemma = maps.lexemes.get(indexItem.lemmaId);
    if (!lemma) continue;
    const modes = indexItem.modes.filter(
      (mode): mode is PracticeMode =>
        isPracticeMode(mode) && (modeFilter === 'mixed' || mode === modeFilter),
    );
    for (const mode of modes) {
      if (mode === 'cloze') {
        for (const clozeId of indexItem.clozeIds) {
          const cloze = maps.cloze.get(clozeId);
          if (!cloze) continue;
          const key = cardKey(indexItem.lemmaId, 'cloze');
          candidates.push(
            cachedSelection({
              itemId: makeItemId(indexItem.lemmaId, mode, clozeId),
              lemma,
              indexItem,
              mode,
              cardKey: key,
              cloze,
            }),
          );
        }
        continue;
      }
      if (mode === 'stress') {
        const stress = maps.stress.get(indexItem.lemmaId);
        if (!stress) continue;
        const key = cardKey(indexItem.lemmaId, mode);
        candidates.push(
          cachedSelection({
            itemId: makeItemId(indexItem.lemmaId, mode, stress.stressId),
            lemma,
            indexItem,
            mode,
            cardKey: key,
            stress,
          }),
        );
        continue;
      }
      if (mode === 'classify') {
        const classify = maps.classify.get(indexItem.lemmaId);
        if (!classify || classify.sets.length === 0) continue;
        const key = cardKey(indexItem.lemmaId, mode);
        for (const set of classify.sets) {
          candidates.push(
            cachedSelection({
              itemId: makeItemId(indexItem.lemmaId, mode, `${classify.classifyId}:${set.setId}`),
              lemma,
              indexItem,
              mode,
              cardKey: key,
              classify,
              classifySetId: set.setId,
            }),
          );
        }
        continue;
      }
      if (mode === 'paradigm') {
        const items = maps.paradigm.get(indexItem.lemmaId) ?? [];
        for (const paradigm of items) {
          const key = cardKey(indexItem.lemmaId, mode);
          candidates.push(
            cachedSelection({
              itemId: makeItemId(indexItem.lemmaId, mode, paradigm.paradigmId),
              lemma,
              indexItem,
              mode,
              cardKey: key,
              paradigm,
            }),
          );
        }
        continue;
      }
      if (mode === 'synonym') {
        const items = maps.synonym.get(indexItem.lemmaId) ?? [];
        for (const synonym of items) {
          const key = cardKey(indexItem.lemmaId, mode);
          candidates.push(
            cachedSelection({
              itemId: makeItemId(indexItem.lemmaId, mode, synonym.synonymId),
              lemma,
              indexItem,
              mode,
              cardKey: key,
              synonym,
            }),
          );
        }
        continue;
      }
      if (mode === 'heritage') {
        const items = maps.heritage.get(indexItem.lemmaId) ?? [];
        for (const heritage of items) {
          candidates.push(
            cachedSelection({
              itemId: makeItemId(indexItem.lemmaId, mode, heritage.heritageId),
              lemma,
              indexItem,
              mode,
              cardKey: heritage.srsKey,
              heritage,
            }),
          );
        }
        continue;
      }
      if (mode === 'paronym') {
        const items = maps.paronym.get(indexItem.lemmaId) ?? [];
        for (const paronym of items) {
          candidates.push(
            cachedSelection({
              itemId: makeItemId(indexItem.lemmaId, mode, paronym.paronymId),
              lemma,
              indexItem,
              mode,
              cardKey: paronym.srsKey,
              paronym,
            }),
          );
        }
        continue;
      }
      const key = cardKey(indexItem.lemmaId, mode);
      candidates.push(
        cachedSelection({
          itemId: makeItemId(indexItem.lemmaId, mode),
          lemma,
          indexItem,
          mode,
          cardKey: key,
        }),
      );
    }
  }

  return candidates;
}

function staticCandidatesFor(deck: PracticeDeckData, modeFilter: PracticeModeFilter): PracticeSelection[] {
  let byMode = staticCandidateCache.get(deck);
  if (!byMode) {
    byMode = new Map();
    staticCandidateCache.set(deck, byMode);
  }
  const cached = byMode.get(modeFilter);
  if (cached) return cached;
  const candidates = buildStaticCandidates(deck, modeFilter);
  byMode.set(modeFilter, candidates);
  return candidates;
}

function refreshedCandidates(
  deck: PracticeDeckData,
  state: LoadedSrsState,
  history: SelectionHistoryItem[],
  modeFilter: PracticeModeFilter,
  minRecognitionStability: number,
  nowTime: number,
): PracticeSelection[] {
  const candidates: PracticeSelection[] = [];
  const staticCandidates = staticCandidatesFor(deck, modeFilter);
  const clozeRecognition = new Map<string, boolean>();
  const recallDirection = lastRecallDirection(history);
  const choicePolarity = lastChoicePolarity(history);

  for (const candidate of staticCandidates) {
    if (candidate.mode === 'cloze' && modeFilter !== 'cloze') {
      let mastered = clozeRecognition.get(candidate.indexItem.lemmaId);
      if (mastered === undefined) {
        mastered = recognitionMastered(candidate.indexItem.lemmaId, state, minRecognitionStability);
        clozeRecognition.set(candidate.indexItem.lemmaId, mastered);
      }
      if (!mastered) continue;
    }
    const card = state.cards.get(candidate.cardKey) ?? null;
    candidate.cardState = card;
    candidate.due = card?.due ?? 0;
    candidate.lapsed = Boolean(card && card.lapses > 0 && card.due <= nowTime);
    candidate.recallDirection = directionFor(candidate.cardKey, recallDirection);
    candidate.choicePolarity = polarityFor(candidate.cardKey, choicePolarity);
    candidates.push(candidate);
  }

  return candidates;
}

export function selectNextPracticeItem(
  deck: PracticeDeckData,
  options: SelectPracticeOptions = {},
): PracticeSelection | null {
  const state = currentState();
  const nowTime = toTime(options.now ?? Date.now()) ?? Date.now();
  const history = options.history ?? [];
  const modeFilter = options.modeFilter ?? 'mixed';
  const minRecognitionStability = options.minRecognitionStability ?? DEFAULT_RECOGNITION_STABILITY;
  const clozeSoftCap = options.clozeSoftCap ?? 0.25;
  const dueWindowMs = options.dueWindowMs ?? 0;
  const wordRepeatWindow = Math.max(
    MIN_WORD_REPEAT_WINDOW,
    options.wordRepeatWindow ?? MIN_WORD_REPEAT_WINDOW,
  );
  const candidates = refreshedCandidates(
    deck,
    state,
    history,
    modeFilter,
    minRecognitionStability,
    nowTime,
  );

  const overduePool = applyPoolFilter(
    candidates.filter((candidate) => candidate.due <= nowTime),
    options.poolFilter,
  );
  const windowPool = applyPoolFilter(
    candidates.filter((candidate) => candidate.due <= nowTime + Math.max(dueWindowMs, WIDENED_DUE_WINDOW_MS)),
    options.poolFilter,
  );
  let scheduledPool = overduePool.length ? overduePool : windowPool;
  scheduledPool = applySpacingFilters(scheduledPool, history, wordRepeatWindow);
  if (!scheduledPool.length && windowPool.length) scheduledPool = windowPool;
  if (!scheduledPool.length) {
    const borrowedPool = applyPoolFilter(
      candidates
        .filter((candidate) => candidate.due > nowTime)
        .sort((left, right) => left.due - right.due)
        .slice(0, Math.max(1, Math.min(4, candidates.length))),
      options.poolFilter,
    );
    scheduledPool = applySpacingFilters(borrowedPool, history, wordRepeatWindow);
    if (!scheduledPool.length) scheduledPool = borrowedPool;
  }
  if (!scheduledPool.length) return null;

  const selection = rankCandidates(scheduledPool, history, clozeSoftCap, nowTime, deck.level, options.sessionSeed);
  return selection ? selectionSnapshot(selection) : null;
}

export function czNorm(value: string): string {
  return value
    .normalize('NFD')
    .replace(/\u0301/g, '')
    .replace(/[’ʼ`]/g, "'")
    .trim()
    .toLocaleLowerCase('uk-UA');
}

export function isWrongCaseAnswer(value: string, lemma: PracticeLexeme, cloze: PracticeClozeItem): boolean {
  const normalized = czNorm(value);
  if (!normalized || normalized === czNorm(cloze.form)) return false;
  if (normalized === czNorm(lemma.lemma)) return true;
  for (const caseForms of Object.values(lemma.paradigm.cases)) {
    for (const form of Object.values(caseForms)) {
      if (form && czNorm(form) === normalized && normalized !== czNorm(cloze.form)) return true;
    }
  }
  return false;
}

export function validateClozeOptions(cloze: PracticeClozeItem): string[] {
  const errors: string[] = [];
  if (cloze.options.length < 4) {
    errors.push('option set must contain at least four options');
  }
  const labels = cloze.options.map((option) => option.label);
  const normalized = labels.map(czNorm);
  if (new Set(normalized).size !== normalized.length) {
    errors.push('option labels must be unique after normalization');
  }
  const answerCount = normalized.filter((label) => label === czNorm(cloze.form)).length;
  if (answerCount !== 1) {
    errors.push('answer form must be present exactly once');
  }
  const accepted = new Set(
    [cloze.form, ...(cloze.acceptedAlt ?? [])]
      .filter((value): value is string => Boolean(value))
      .map(czNorm),
  );
  const distractorLeak = cloze.options.some(
    (option) => option.kind !== 'answer' && accepted.has(czNorm(option.label)),
  );
  if (distractorLeak) {
    errors.push('accepted alternate must not equal a distractor');
  }
  const obliqueTotal = cloze.options.filter((option) => option.case && option.case !== 'nominative').length;
  const obliqueDistractors = cloze.options.filter(
    (option) => option.kind !== 'answer' && option.case && option.case !== 'nominative',
  ).length;
  if (obliqueTotal < 2 || obliqueDistractors < 1) {
    errors.push('option set must contain the answer plus at least one oblique distractor');
  }
  const posValues = new Set(cloze.options.map((option) => option.pos).filter(Boolean));
  if (posValues.size > 1) {
    errors.push('option set must stay within one POS bucket');
  }
  const rootCounts = new Map<string, number>();
  for (const option of cloze.options) {
    rootCounts.set(option.lemmaId, (rootCounts.get(option.lemmaId) ?? 0) + 1);
  }
  const pairCount = [...rootCounts.values()].filter((count) => count >= 2).length;
  if (pairCount === 1) {
    errors.push('option set must not contain exactly one same-root pair');
  }
  const lengths = labels.map((label) => label.length);
  if (lengths.length && Math.max(...lengths) - Math.min(...lengths) > 12) {
    errors.push('option label lengths exceed bounded distribution');
  }
  return errors;
}

export function uaPlural(
  count: number,
  forms: { one: string; few: string; many: string } = {
    one: 'правильна',
    few: 'правильні',
    many: 'правильних',
  },
): string {
  const abs = Math.abs(count);
  const mod10 = abs % 10;
  const mod100 = abs % 100;
  if (mod100 >= 11 && mod100 <= 14) return forms.many;
  if (mod10 === 1) return forms.one;
  if (mod10 >= 2 && mod10 <= 4) return forms.few;
  return forms.many;
}

export function combinePracticeShards(
  indexShard: PracticeIndexShard,
  lexemeShard: PracticeLexemeShard,
  clozeShard?: PracticeClozeShard,
  modeShards: {
    stress?: PracticeStressShard;
    classify?: PracticeClassifyShard;
    paradigm?: PracticeParadigmShard;
    synonym?: PracticeSynonymShard;
    paronym?: PracticeParonymShard;
    heritage?: PracticeHeritageShard;
  } = {},
): PracticeDeckData {
  return {
    deckVersion: indexShard.deckVersion,
    level: indexShard.level,
    index: indexShard.items,
    lexemes: lexemeShard.lexemes,
    cloze: clozeShard?.cloze ?? [],
    stress: modeShards.stress?.stress ?? [],
    classify: modeShards.classify?.classify ?? [],
    paradigm: modeShards.paradigm?.paradigm ?? [],
    synonym: modeShards.synonym?.synonym ?? [],
    paronym: modeShards.paronym?.paronym ?? [],
    heritage: modeShards.heritage?.heritage ?? [],
    fixtureNote: indexShard.fixtureNote,
  };
}

/**
 * Extend a base deck (initially the selected level only) with lower-level decks.
 * Produces a new deck object so WeakMap selector caches (#4656) key off the new identity.
 */
export function extendWithLowerDecks(base: PracticeDeckData, lowers: PracticeDeckData[]): PracticeDeckData {
  if (!lowers.length) return base;
  return {
    deckVersion: base.deckVersion || lowers[0]?.deckVersion || `cumulative-${base.level}`,
    level: base.level,
    index: [...base.index, ...lowers.flatMap((d) => d.index)],
    lexemes: [...base.lexemes, ...lowers.flatMap((d) => d.lexemes)],
    cloze: [...(base.cloze ?? []), ...lowers.flatMap((d) => d.cloze ?? [])],
    stress: [...(base.stress ?? []), ...lowers.flatMap((d) => d.stress ?? [])],
    classify: [...(base.classify ?? []), ...lowers.flatMap((d) => d.classify ?? [])],
    paradigm: [...(base.paradigm ?? []), ...lowers.flatMap((d) => d.paradigm ?? [])],
    synonym: [...(base.synonym ?? []), ...lowers.flatMap((d) => d.synonym ?? [])],
    paronym: [...(base.paronym ?? []), ...lowers.flatMap((d) => d.paronym ?? [])],
    heritage: [...(base.heritage ?? []), ...lowers.flatMap((d) => d.heritage ?? [])],
    fixtureNote: base.fixtureNote ?? lowers.find((d) => d.fixtureNote)?.fixtureNote,
  };
}

/** Returns whether an itemId built from a prior selection is still present after a live pool merge. */
export function itemIdPresentInDeck(deck: PracticeDeckData, itemId: string): boolean {
  if (!itemId) return false;
  const parts = itemId.split(':');
  const lemmaId = parts[0];
  const mode = parts[1] as PracticeMode | undefined;
  const idxItem = deck.index.find((i) => i.lemmaId === lemmaId);
  if (!idxItem || !mode) return false;
  if (mode === 'cloze') {
    return !!idxItem.hasCloze || (idxItem.clozeIds?.length ?? 0) > 0;
  }
  return idxItem.modes.includes(mode);
}

export function isPracticeNewCard(card: CardState | null | undefined): boolean {
  if (!card) return true;
  return card.reps === 0 && card.state === State.New;
}

export function isDueReviewCard(card: CardState | null | undefined, nowTime: number): boolean {
  if (!card || isPracticeNewCard(card)) return false;
  return card.due <= nowTime;
}

export function countDueReviewCards(
  index: PracticeIndexItem[],
  now: Date | number = Date.now(),
): number {
  const state = currentState();
  const nowTime = toTime(now) ?? Date.now();
  let count = 0;
  for (const item of index) {
    for (const mode of item.modes) {
      if (!isPracticeMode(mode)) continue;
      const card = state.cards.get(cardKey(item.lemmaId, mode));
      if (isDueReviewCard(card, nowTime)) count += 1;
    }
  }
  return count;
}

export function countAvailableNewCards(
  index: PracticeIndexItem[],
  now: Date | number = Date.now(),
): number {
  const state = currentState();
  const nowTime = toTime(now) ?? Date.now();
  let count = 0;
  for (const item of index) {
    for (const mode of item.modes) {
      if (!isPracticeMode(mode)) continue;
      const card = state.cards.get(cardKey(item.lemmaId, mode));
      if (isPracticeNewCard(card) && (!card || card.due <= nowTime)) count += 1;
    }
  }
  return count;
}

export function readNewCardsDailyState(
  storage: StorageLike = resolveStorage(),
  dateKey = todayDateKey(),
): NewCardsDailyState {
  try {
    const raw = storage.getItem(PRACTICE_NEW_CARDS_KEY);
    if (!raw) return { date: dateKey, count: 0 };
    const parsed = JSON.parse(raw) as Partial<NewCardsDailyState>;
    if (parsed.date !== dateKey || typeof parsed.count !== 'number') {
      return { date: dateKey, count: 0 };
    }
    return { date: dateKey, count: parsed.count };
  } catch {
    return { date: dateKey, count: 0 };
  }
}

export function writeNewCardsDailyState(
  state: NewCardsDailyState,
  storage: StorageLike = resolveStorage(),
): void {
  try {
    storage.setItem(PRACTICE_NEW_CARDS_KEY, JSON.stringify(state));
  } catch {
    // Best-effort persistence.
  }
}

function todayDateKey(date = new Date()): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function computeSessionScope(
  index: PracticeIndexItem[],
  budget: SessionBudget,
  options: {
    now?: Date | number;
    newPerSession?: number;
    newPerDay?: number;
    dailyNewCount?: number;
  } = {},
): SessionScopeStats {
  const now = options.now ?? Date.now();
  const newPerSession = options.newPerSession ?? DEFAULT_NEW_PER_SESSION;
  const newPerDay = options.newPerDay ?? DEFAULT_NEW_PER_DAY;
  const dailyNewCount = options.dailyNewCount ?? readNewCardsDailyState(resolveStorage(), todayDateKey(new Date(now))).count;
  const dueReviews = countDueReviewCards(index, now);
  const availableNew = countAvailableNewCards(index, now);
  const remainingDailyNew = Math.max(0, newPerDay - dailyNewCount);
  const maxNew = Math.min(newPerSession, remainingDailyNew, availableNew);
  if (budget === 'until-zero') {
    const plannedTotal = dueReviews + maxNew;
    return {
      dueReviews,
      plannedNew: maxNew,
      plannedTotal,
      estimatedMinutes: Math.max(1, Math.ceil((plannedTotal * SESSION_ITEM_ESTIMATE_SEC) / 60)),
    };
  }
  const reviewSlots = Math.min(dueReviews, budget);
  const newSlots = Math.min(maxNew, Math.max(0, budget - reviewSlots));
  const plannedTotal = reviewSlots + newSlots;
  return {
    dueReviews,
    plannedNew: newSlots,
    plannedTotal,
    estimatedMinutes: Math.max(1, Math.ceil((plannedTotal * SESSION_ITEM_ESTIMATE_SEC) / 60)),
  };
}

export function computeTodayRingDenominator(
  index: PracticeIndexItem[],
  options: {
    now?: Date | number;
    newPerDay?: number;
    dailyNewCount?: number;
  } = {},
): number {
  const now = options.now ?? Date.now();
  const newPerDay = options.newPerDay ?? DEFAULT_NEW_PER_DAY;
  const dailyNewCount = options.dailyNewCount ?? readNewCardsDailyState(resolveStorage(), todayDateKey(new Date(now))).count;
  const dueReviews = countDueReviewCards(index, now);
  const availableNew = countAvailableNewCards(index, now);
  const remainingDailyNew = Math.max(0, newPerDay - dailyNewCount);
  return dueReviews + Math.min(remainingDailyNew, availableNew);
}

export function buildSessionPoolConstraintState(options: {
  plannedReviews: number;
  reviewsCompleted: number;
  sessionNewIntroduced: number;
  newPerSession?: number;
  newPerDay?: number;
  dailyNewCount?: number;
}): SessionPoolConstraintState {
  const newPerSession = options.newPerSession ?? DEFAULT_NEW_PER_SESSION;
  const newPerDay = options.newPerDay ?? DEFAULT_NEW_PER_DAY;
  const dailyNewCount = options.dailyNewCount ?? 0;
  const newRemainingSession = Math.max(0, newPerSession - options.sessionNewIntroduced);
  const newRemainingDaily = Math.max(0, newPerDay - dailyNewCount);
  const reviewsSatisfied =
    options.plannedReviews <= 0 || options.reviewsCompleted >= options.plannedReviews;
  return {
    allowNewInPool: reviewsSatisfied && newRemainingSession > 0 && newRemainingDaily > 0,
    newRemainingSession,
    newRemainingDaily,
    sessionNewIntroduced: options.sessionNewIntroduced,
  };
}

export function sessionPoolAllowsCandidate(
  candidate: PracticeSelection,
  constraints: SessionPoolConstraintState,
): boolean {
  if (!isPracticeNewCard(candidate.cardState)) return true;
  if (!constraints.allowNewInPool) return false;
  if (constraints.newRemainingDaily <= 0) return false;
  if (constraints.newRemainingSession <= 0) return false;
  return true;
}

export function formatFsrsIntervalUk(from: Date, to: Date): string {
  const deltaMs = Math.max(0, to.getTime() - from.getTime());
  const minutes = Math.max(1, Math.round(deltaMs / (60 * 1000)));
  if (minutes < 60) return `${minutes} хв`;
  const days = Math.max(1, Math.round(deltaMs / DAY_MS));
  if (days < 30) return `${days} д`;
  const months = Math.max(1, Math.round(days / 30));
  return `${months} міс`;
}

const FSRS_RATING_ORDER: PracticeRating[] = ['again', 'hard', 'good', 'easy'];

export function previewRatingIntervals(
  lemmaId: string,
  mode: PracticeMode,
  now: Date | number = Date.now(),
): Record<PracticeRating, string> {
  const reviewDate = now instanceof Date ? now : new Date(now);
  const state = currentState();
  const scheduler = fsrs(state.settings.params);
  const existing = state.cards.get(cardKey(lemmaId, mode));
  const fsrsCard = existing ? fsrsCardFromState(existing) : createEmptyCard(reviewDate);
  const records = scheduler.repeat(fsrsCard, reviewDate);
  const previews = {} as Record<PracticeRating, string>;
  for (const rating of FSRS_RATING_ORDER) {
    const grade = RATING_TO_FSRS[rating];
    const record = records[grade];
    previews[rating] = formatFsrsIntervalUk(reviewDate, record.card.due);
  }
  return previews;
}

function isPracticeModeFilter(value: unknown): value is PracticeModeFilter {
  return value === 'mixed' || isPracticeMode(value);
}

function parsePracticeSessionSnapshot(value: unknown): PracticeSessionSnapshot | null {
  try {
    const parsed = value as Partial<PracticeSessionSnapshot>;
    if (
      !parsed ||
      typeof parsed !== 'object' ||
      typeof parsed.sessionSeed !== 'number' ||
      !Array.isArray(parsed.history) ||
      (typeof parsed.budget !== 'number' && parsed.budget !== 'until-zero') ||
      typeof parsed.completed !== 'number' ||
      !isPracticeModeFilter(parsed.modeFilter) ||
      typeof parsed.level !== 'string' ||
      typeof parsed.startedAt !== 'number'
    ) {
      return null;
    }
    return parsed as PracticeSessionSnapshot;
  } catch {
    return null;
  }
}

/**
 * Read the mode-indexed session store. A pre-mode-scoping legacy snapshot is accepted
 * and placed under its own stored mode; the next write upgrades it to the v1 envelope.
 */
export function readPracticeSessionSnapshots(
  storage: StorageLike = resolveStorage(),
): PracticeSessionSnapshots {
  try {
    const raw = storage.getItem(PRACTICE_SESSION_STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as unknown;
    const legacySnapshot = parsePracticeSessionSnapshot(parsed);
    if (legacySnapshot) return { [legacySnapshot.modeFilter]: legacySnapshot };

    const persisted = parsed as Partial<PersistedPracticeSessionSnapshots>;
    if (
      !persisted ||
      typeof persisted !== 'object' ||
      persisted.version !== 1 ||
      !persisted.byMode ||
      typeof persisted.byMode !== 'object' ||
      Array.isArray(persisted.byMode)
    ) {
      return {};
    }

    const snapshots: PracticeSessionSnapshots = {};
    for (const [mode, candidate] of Object.entries(persisted.byMode)) {
      if (!isPracticeModeFilter(mode)) continue;
      const snapshot = parsePracticeSessionSnapshot(candidate);
      if (snapshot?.modeFilter === mode) snapshots[mode] = snapshot;
    }
    return snapshots;
  } catch {
    return {};
  }
}

export function readPracticeSessionSnapshot(
  mode: PracticeModeFilter,
  storage: StorageLike = resolveStorage(),
): PracticeSessionSnapshot | null {
  return readPracticeSessionSnapshots(storage)[mode] ?? null;
}

export function writePracticeSessionSnapshot(
  mode: PracticeModeFilter,
  snapshot: PracticeSessionSnapshot | null,
  storage: StorageLike = resolveStorage(),
): void {
  try {
    const snapshots = readPracticeSessionSnapshots(storage);
    if (snapshot && snapshot.modeFilter !== mode) return;
    if (snapshot) {
      snapshots[mode] = snapshot;
    } else {
      delete snapshots[mode];
    }
    if (Object.keys(snapshots).length === 0) {
      storage.removeItem(PRACTICE_SESSION_STORAGE_KEY);
      return;
    }
    const persisted: PersistedPracticeSessionSnapshots = { version: 1, byMode: snapshots };
    storage.setItem(PRACTICE_SESSION_STORAGE_KEY, JSON.stringify(persisted));
  } catch {
    // Best-effort persistence.
  }
}

export function clearPracticeSessionSnapshots(storage: StorageLike = resolveStorage()): void {
  try {
    storage.removeItem(PRACTICE_SESSION_STORAGE_KEY);
  } catch {
    // Best-effort persistence.
  }
}

export function isPracticeSessionResumable(
  snapshot: PracticeSessionSnapshot | null,
  now: Date | number = Date.now(),
): boolean {
  if (!snapshot) return false;
  const nowTime = toTime(now) ?? Date.now();
  if (nowTime - snapshot.startedAt >= SESSION_RESUME_MAX_MS) return false;
  const plannedTotal = snapshot.plannedTotal ?? snapshot.budget;
  if (typeof plannedTotal === 'number' && snapshot.completed >= plannedTotal) {
    const unresolved = snapshot.unresolvedCardKeys?.length ?? 0;
    if (unresolved === 0) return false;
  }
  return true;
}

export function nextDuePreviewTime(now: Date | number = Date.now()): Date | null {
  const state = currentState();
  const nowTime = toTime(now) ?? Date.now();
  let nextDue: number | null = null;
  for (const card of state.cards.values()) {
    if (card.due <= nowTime) continue;
    if (nextDue === null || card.due < nextDue) nextDue = card.due;
  }
  return nextDue === null ? null : new Date(nextDue);
}

export type SessionCompletionDecision = 'continue' | 'extend' | 'summary' | 'summary-with-deferred';

export function resolveSessionCompletion(options: {
  completed: number;
  plannedTotal: number;
  extensionUsed: number;
  unresolvedCount: number;
  maxExtension?: number;
}): SessionCompletionDecision {
  const maxExtension = options.maxExtension ?? SESSION_CLOSURE_EXTENSION_MAX;
  const target = options.plannedTotal + options.extensionUsed;
  if (options.completed < target) return 'continue';
  if (options.unresolvedCount > 0 && options.extensionUsed < maxExtension) return 'extend';
  if (options.unresolvedCount > 0) return 'summary-with-deferred';
  return 'summary';
}
