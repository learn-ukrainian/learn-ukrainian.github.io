import {
  createEmptyCard,
  fsrs,
  Rating,
  State,
  type Card as FsrsCard,
  type FSRSParameters,
  type RecordLogItem,
} from 'ts-fsrs';

export const SRS_STORAGE_KEY = 'lu-lexicon-srs';
export const SRS_SETTINGS_KEY = 'lu-lexicon-srs-settings';
export const SRS_BACKUP_KEY = 'lu-lexicon-srs.backup';

const CURRENT_VERSION = 2;
const SETTINGS_VERSION = 1;
const DAY_MS = 24 * 60 * 60 * 1000;

export type PracticeRating = 'again' | 'hard' | 'good' | 'easy';

export interface PracticeDeckEntry {
  lemma: string;
  slug: string;
  gloss: string;
  ipa: string | null;
  pos: string | null;
  cefr: string | null;
  heritage: string | null;
  example: string | null;
  audioKey: null;
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
  slug: string;
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

interface PersistedSrsSchemaV2 {
  version: typeof CURRENT_VERSION;
  cards: Record<string, CardState>;
  reviews: ReviewLogEntry[];
  lastSavedAt: number;
}

type StorageLike = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>;

export const FSRS6_DEFAULT_PARAMS: FSRSParameters = {
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

const RATING_TO_FSRS: Record<PracticeRating, Rating> = {
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

function normalizeCards(rawCards: unknown): Map<string, CardState> | null {
  if (!rawCards || typeof rawCards !== 'object' || Array.isArray(rawCards)) return null;
  const cards = new Map<string, CardState>();
  for (const [slug, rawCard] of Object.entries(rawCards as Record<string, unknown>)) {
    const normalized = normalizeCard(rawCard);
    if (!normalized) return null;
    cards.set(slug, normalized);
  }
  return cards;
}

function normalizeReview(raw: unknown): ReviewLogEntry | null {
  if (!raw || typeof raw !== 'object') return null;
  const source = raw as Record<string, unknown>;
  if (typeof source.slug !== 'string') return null;
  const due = toTime(source.due as Date | number | string | undefined);
  const review = toTime(source.review as Date | number | string | undefined);
  if (due === null || review === null) return null;
  const rating = source.rating;
  if (rating !== 'again' && rating !== 'hard' && rating !== 'good' && rating !== 'easy') {
    return null;
  }
  return {
    slug: source.slug,
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
  store: PersistedSrsSchemaV2,
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

function migrateToCurrent(parsed: Record<string, unknown>): PersistedSrsSchemaV2 | null {
  if (parsed.version === CURRENT_VERSION) return parsed as PersistedSrsSchemaV2;
  if (parsed.version !== 1) return null;
  const cards = normalizeCards(parsed.cards);
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
  const store: PersistedSrsSchemaV2 = {
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
  previous: Date | number | string | undefined | null,
  now: Date | number | string,
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
    const state = hydrateStore(parsed as PersistedSrsSchemaV2, settings, raw, {
      ...emptyFlags(),
      settingsCorrupt,
      clockJump: detectClockJump((parsed as PersistedSrsSchemaV2).lastSavedAt, now),
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

export function saveState(
  state: LoadedSrsState = activeState ?? loadState(),
  storage: StorageLike = resolveStorage(),
  savedAt: number = Date.now(),
): { ok: boolean; reason?: string } {
  if (state.flags.corrupt || state.flags.migrationFailed) {
    return { ok: false, reason: 'existing SRS data is not writable' };
  }
  const previousRaw = storage.getItem(SRS_STORAGE_KEY);
  const nextRaw = serializeState(state, savedAt);
  if (previousRaw && previousRaw !== nextRaw) {
    storage.setItem(SRS_BACKUP_KEY, previousRaw);
    state.flags.backupWritten = true;
  }
  storage.setItem(SRS_STORAGE_KEY, nextRaw);
  storage.setItem(SRS_SETTINGS_KEY, serializeSettings(state.settings));
  state.raw = nextRaw;
  activeState = state;
  return { ok: true };
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

function serializeReview(slug: string, rating: PracticeRating, record: RecordLogItem): ReviewLogEntry {
  return {
    slug,
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

function currentState(): LoadedSrsState {
  return activeState ?? loadState();
}

export function getDueQueue(
  deck: PracticeDeckEntry[],
  now: Date | number = Date.now(),
): PracticeDeckEntry[] {
  const state = currentState();
  const nowTime = toTime(now) ?? Date.now();
  return deck
    .map((entry, index) => {
      const card = state.cards.get(entry.slug);
      return {
        entry,
        index,
        due: card?.due ?? Number.NEGATIVE_INFINITY,
      };
    })
    .filter((item) => item.due <= nowTime)
    .sort((a, b) => a.due - b.due || a.index - b.index)
    .map((item) => item.entry);
}

export function rateCard(
  slug: string,
  rating: PracticeRating,
  now: Date | number = Date.now(),
): CardState {
  const state = currentState();
  if (state.flags.corrupt || state.flags.migrationFailed) {
    throw new Error('Cannot write SRS review while stored data is corrupt');
  }
  const reviewDate = now instanceof Date ? now : new Date(now);
  const scheduler = fsrs(state.settings.params);
  const currentCard = state.cards.get(slug);
  const fsrsCard = currentCard ? fsrsCardFromState(currentCard) : createEmptyCard(reviewDate);
  const record = scheduler.next(fsrsCard, reviewDate, RATING_TO_FSRS[rating]);
  const next = stateFromFsrsCard(record.card);
  state.cards.set(slug, next);
  state.reviews.push(serializeReview(slug, rating, record));
  saveState(state, resolveStorage(), reviewDate.getTime());
  return next;
}

export function masteredCount(threshold = 21): number {
  const state = currentState();
  let count = 0;
  for (const card of state.cards.values()) {
    if (card.stability >= threshold) count += 1;
  }
  return count;
}
