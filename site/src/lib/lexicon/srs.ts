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

const CURRENT_VERSION = 3;
const SETTINGS_VERSION = 1;
const HOUR_MS = 60 * 60 * 1000;
const DAY_MS = 24 * 60 * 60 * 1000;
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

export interface PracticeDeckData {
  deckVersion: string;
  level: string;
  index: PracticeIndexItem[];
  lexemes: PracticeLexeme[];
  cloze: PracticeClozeItem[];
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
  recallDirection: RecallDirection;
  choicePolarity: ChoicePolarity;
}

export interface SelectPracticeOptions {
  now?: Date | number;
  history?: SelectionHistoryItem[];
  modeFilter?: PracticeModeFilter;
  minRecognitionStability?: number;
  clozeSoftCap?: number;
  dueWindowMs?: number;
  wordRepeatWindow?: number;
}

interface PersistedSrsSchemaV3 {
  version: typeof CURRENT_VERSION;
  cards: Record<string, CardState>;
  reviews?: ReviewLogEntry[];
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

function resolveStorage(): StorageLike {
  if (typeof window === 'undefined') return memoryStorage;
  try {
    return window.localStorage;
  } catch {
    return memoryStorage;
  }
}

function emptyFlags(clockJump: ClockJump | null = null): SrsFlags {
  return {
    corrupt: false,
    migrationFailed: false,
    migrated: false,
    backupWritten: false,
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

function hydrateStore(
  store: PersistedSrsSchemaV3,
  settings: SrsSettings,
  raw: string | null,
  flags: SrsFlags,
): LoadedSrsState | null {
  const cards = normalizeCards(store.cards);
  const reviews = normalizeReviews(store.reviews);
  if (!cards || !reviews) return null;
  return {
    version: CURRENT_VERSION,
    cards,
    reviews,
    settings,
    flags,
    raw,
  };
}

function migrateToCurrent(parsed: Record<string, unknown>): PersistedSrsSchemaV3 | null {
  if (parsed.version === CURRENT_VERSION) return parsed as unknown as PersistedSrsSchemaV3;
  if (parsed.version !== 1 && parsed.version !== 2) return null;
  const cards = normalizeCards(parsed.cards, true);
  const reviews = normalizeReviews(parsed.reviews);
  if (!cards || !reviews) return null;
  return {
    version: CURRENT_VERSION,
    cards: Object.fromEntries(cards),
    reviews,
    lastSavedAt: Date.now(),
  };
}

function serializeState(state: LoadedSrsState, savedAt: number): string {
  const store: PersistedSrsSchemaV3 = {
    version: CURRENT_VERSION,
    cards: Object.fromEntries(state.cards),
    reviews: state.reviews,
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
  const { settings, corrupt: settingsCorrupt } = loadSettings(storage);
  const raw = storage.getItem(SRS_STORAGE_KEY);
  if (!raw) {
    activeState = {
      version: CURRENT_VERSION,
      cards: new Map(),
      reviews: [],
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
      settings,
      flags: { ...emptyFlags(), corrupt: true, settingsCorrupt },
      raw,
    };
    return activeState;
  }

  if (parsed.version === CURRENT_VERSION) {
    const state = hydrateStore(parsed as unknown as PersistedSrsSchemaV3, settings, raw, {
      ...emptyFlags(),
      settingsCorrupt,
      clockJump: detectClockJump((parsed as unknown as PersistedSrsSchemaV3).lastSavedAt, now),
    });
    if (state) {
      activeState = state;
      return state;
    }
    activeState = {
      version: CURRENT_VERSION,
      cards: new Map(),
      reviews: [],
      settings,
      flags: { ...emptyFlags(), corrupt: true, settingsCorrupt },
      raw,
    };
    return activeState;
  }

  try {
    storage.setItem(SRS_BACKUP_KEY, raw);
    const migrated = migrateToCurrent(parsed);
    if (!migrated) throw new Error('unsupported SRS schema');
    const nextRaw = JSON.stringify(migrated);
    storage.setItem(SRS_STORAGE_KEY, nextRaw);
    const state = hydrateStore(migrated, settings, nextRaw, {
      ...emptyFlags(),
      migrated: true,
      backupWritten: true,
      settingsCorrupt,
      clockJump: detectClockJump(migrated.lastSavedAt, now),
    });
    if (!state) throw new Error('migrated SRS schema is invalid');
    activeState = state;
    return state;
  } catch {
    activeState = {
      version: CURRENT_VERSION,
      cards: new Map(),
      reviews: [],
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
    if (previousRaw && previousRaw !== nextRaw) {
      storage.setItem(SRS_BACKUP_KEY, previousRaw);
      state.flags.backupWritten = true;
    }
    storage.setItem(SRS_STORAGE_KEY, nextRaw);
    storage.setItem(SRS_SETTINGS_KEY, serializeSettings(state.settings));
    state.raw = nextRaw;
    activeState = state;
    return { ok: true };
  } catch (error) {
    return { ok: false, error };
  }
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
): CardState;
export function rateCard(
  lemmaId: string,
  modeOrRating: PracticeMode | PracticeRating,
  ratingOrDate?: PracticeRating | Date | number,
  maybeDate?: Date | number,
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
  state.reviews.push(serializeReview(key, lemmaId, mode, rating, record));
  saveState(state, resolveStorage(), reviewDate.getTime());
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

function deckMaps(deck: PracticeDeckData) {
  return {
    lexemes: new Map(deck.lexemes.map((lexeme) => [lexeme.lemmaId, lexeme])),
    cloze: new Map(deck.cloze.map((item) => [item.clozeId, item])),
  };
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

function directionFor(candidateKey: string, history: SelectionHistoryItem[]): RecallDirection {
  const last = [...history].reverse().find((item) => item.recallDirection)?.recallDirection;
  if (last === 'uk-to-meaning') return 'meaning-to-uk';
  if (last === 'meaning-to-uk') return 'uk-to-meaning';
  return candidateKey.length % 2 === 0 ? 'uk-to-meaning' : 'meaning-to-uk';
}

function polarityFor(candidateKey: string, history: SelectionHistoryItem[]): ChoicePolarity {
  const last = [...history].reverse().find((item) => item.choicePolarity)?.choicePolarity;
  if (last === 'word-to-meaning') return 'meaning-to-word';
  if (last === 'meaning-to-word') return 'word-to-meaning';
  return candidateKey.length % 2 === 0 ? 'word-to-meaning' : 'meaning-to-word';
}

function sessionCounts(history: SelectionHistoryItem[]): Record<PracticeMode, number> {
  return PRACTICE_MODES.reduce(
    (counts, mode) => {
      counts[mode] = history.filter((item) => item.mode === mode).length;
      return counts;
    },
    {} as Record<PracticeMode, number>,
  );
}

function candidatePenalty(
  candidate: PracticeSelection,
  candidates: PracticeSelection[],
  history: SelectionHistoryItem[],
  clozeSoftCap: number,
  nowTime: number,
): number {
  if (candidate.lapsed) return -100_000;
  let penalty = 0;
  const recent = history.slice(-12);
  const lastThreeModes = history.slice(-3).map((item) => item.mode);
  if (lastThreeModes.includes(candidate.mode)) penalty += 18;
  const counts = sessionCounts(history);
  const availableModes = new Set(candidates.map((item) => item.mode));
  if (history.length < 8 && !counts[candidate.mode] && availableModes.size > 1) {
    penalty -= 45;
  }
  const total = Math.max(1, history.length);
  const expected = total / Math.max(1, availableModes.size);
  penalty -= Math.max(0, expected - counts[candidate.mode]) * 3;

  if (candidate.mode === 'cloze' && recent.length >= 4) {
    const clozeRatio = recent.filter((item) => item.mode === 'cloze').length / recent.length;
    if (clozeRatio >= clozeSoftCap && candidate.due > nowTime) penalty += 35;
  }

  if (candidate.cloze) {
    const candidateCases = new Set(
      candidates.filter((item) => item.cloze).map((item) => item.cloze?.blankCase),
    );
    const recentCases = new Set(
      history
        .slice(-8)
        .filter((item) => item.mode === 'cloze' && item.blankCase)
        .map((item) => item.blankCase),
    );
    if (candidateCases.size >= 3 && recentCases.size < 3) {
      penalty += recentCases.has(candidate.cloze.blankCase) ? 16 : -12;
    }
    const last = history.at(-1);
    if (last?.sentenceFrameId === candidate.cloze.sentenceFrameId) penalty += 60;
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
  if (!candidate.cardState) return 0;
  return Math.floor((candidate.due - nowTime) / HOUR_MS);
}

function rankCandidates(
  pool: PracticeSelection[],
  history: SelectionHistoryItem[],
  clozeSoftCap: number,
  nowTime: number,
): PracticeSelection | null {
  // Urgency is the PRIMARY sort key (lapsed first, then most-overdue); the soft
  // anti-monotony penalty is only a TIEBREAK within the same urgency bucket. Adding the
  // penalty to the urgency score (as before) let a +18–60 penalty leak across hour-buckets
  // and overtake a genuinely-more-due card — variety must never delay a due/lapsed card.
  return (
    [...pool].sort((left, right) => {
      return (
        urgencyBucket(left, nowTime) - urgencyBucket(right, nowTime) ||
        candidatePenalty(left, pool, history, clozeSoftCap, nowTime) -
          candidatePenalty(right, pool, history, clozeSoftCap, nowTime) ||
        left.indexItem.newOrder - right.indexItem.newOrder ||
        left.itemId.localeCompare(right.itemId)
      );
    })[0] ?? null
  );
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
  const wordRepeatWindow = Math.max(MIN_WORD_REPEAT_WINDOW, options.wordRepeatWindow ?? MIN_WORD_REPEAT_WINDOW);
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
        if (
          modeFilter !== 'cloze' &&
          !recognitionMastered(indexItem.lemmaId, state, minRecognitionStability)
        )
          continue;
        for (const clozeId of indexItem.clozeIds) {
          const cloze = maps.cloze.get(clozeId);
          if (!cloze) continue;
          const key = cardKey(indexItem.lemmaId, 'cloze');
          const card = state.cards.get(key) ?? null;
          candidates.push({
            itemId: makeItemId(indexItem.lemmaId, mode, clozeId),
            lemma,
            indexItem,
            mode,
            cardKey: key,
            cardState: card,
            due: card?.due ?? 0,
            lapsed: Boolean(card && card.lapses > 0 && card.due <= nowTime),
            cloze,
            recallDirection: directionFor(key, history),
            choicePolarity: polarityFor(key, history),
          });
        }
        continue;
      }
      const key = cardKey(indexItem.lemmaId, mode);
      const card = state.cards.get(key) ?? null;
      candidates.push({
        itemId: makeItemId(indexItem.lemmaId, mode),
        lemma,
        indexItem,
        mode,
        cardKey: key,
        cardState: card,
        due: card?.due ?? 0,
        lapsed: Boolean(card && card.lapses > 0 && card.due <= nowTime),
        recallDirection: directionFor(key, history),
        choicePolarity: polarityFor(key, history),
      });
    }
  }

  const overduePool = candidates.filter((candidate) => candidate.due <= nowTime);
  const windowPool = candidates.filter(
    (candidate) => candidate.due <= nowTime + Math.max(dueWindowMs, WIDENED_DUE_WINDOW_MS),
  );
  let scheduledPool = overduePool.length ? overduePool : windowPool;
  scheduledPool = applySpacingFilters(scheduledPool, history, wordRepeatWindow);
  if (!scheduledPool.length && windowPool.length) scheduledPool = windowPool;
  if (!scheduledPool.length) {
    const borrowedPool = candidates
      .filter((candidate) => candidate.due > nowTime)
      .sort((left, right) => left.due - right.due)
      .slice(0, Math.max(1, Math.min(4, candidates.length)));
    scheduledPool = applySpacingFilters(borrowedPool, history, wordRepeatWindow);
    if (!scheduledPool.length) scheduledPool = borrowedPool;
  }
  if (!scheduledPool.length) return null;

  return rankCandidates(scheduledPool, history, clozeSoftCap, nowTime);
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
): PracticeDeckData {
  return {
    deckVersion: indexShard.deckVersion,
    level: indexShard.level,
    index: indexShard.items,
    lexemes: lexemeShard.lexemes,
    cloze: clozeShard?.cloze ?? [],
    fixtureNote: indexShard.fixtureNote,
  };
}
