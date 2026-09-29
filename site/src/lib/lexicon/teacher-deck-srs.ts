/**
 * Per-deck progress, daily queue and FSRS scheduling for the teacher-table deck
 * (#8843 scope 4; contract: docs/practice/teacher-deck-artifacts.md § Card identity).
 *
 * - One FSRS state per card id `<entryId>:recognition|production|cloze|grammar`.
 * - "New words per day" counts distinct entries whose recognition card is first
 *   introduced that local day. Production/cloze/grammar unlock after the first
 *   successful recognition review and become due the next local day.
 * - Each local day's queue: due reviews first (up to the review cap), then unseen
 *   entries, newest `firstSeen` first.
 * - Every review is persisted as it happens and applied at most once (review id).
 *   A saved queue is restored only on the same local day and reconciled against
 *   the current deck version; a new local day rebuilds it.
 *
 * The store is this deck's own (`lu-deck-progress:<deckId>`), never shared with
 * CEFR practice. Everything here is a pure function of (deck, progress, now)
 * except the explicit storage read/write helpers.
 */

import { createEmptyCard, fsrs, Rating, State, type FSRSParameters, type Grade } from 'ts-fsrs';
import {
  formatFsrsIntervalUk,
  fsrsCardFromState,
  parseCardKey,
  practiceFsrsParams,
  SRS_STORAGE_KEY,
  stateFromFsrsCard,
  stripStressMarks,
  todayDateKey,
  type CardState,
  type PracticeRating,
  type StorageLike,
} from './srs';
import {
  entryClozeItems,
  entryGrammarItems,
  TEACHER_CARD_KINDS,
  type TeacherCardKind,
  type TeacherDeck,
  type TeacherDeckEntry,
  type TeacherGrammarMode,
} from './teacher-deck';

export const DECK_PROGRESS_VERSION = 1;
export const DECK_PROGRESS_KEY_PREFIX = 'lu-deck-progress:';
/** Raw review records kept; today's records are never dropped (idempotency window). */
export const MAX_DECK_REVIEW_LOG = 3000;
export const MAX_NEW_PER_DAY = 500;
export const MAX_REVIEW_CAP = 5000;

export interface DeckSettings {
  newPerDay: number;
  reviewCap: number;
}

export type SlotOrigin = 'review' | 'new' | 'repeat';

export type TeacherPresentation =
  | { type: 'recognition-flashcard' }
  | { type: 'recognition-choice' }
  | { type: 'production-flashcard' }
  | { type: 'production-choice' }
  | { type: 'cloze'; clozeId: string }
  | { type: 'grammar'; mode: TeacherGrammarMode; itemId: string; setId?: string };

export interface DeckQueueSlot {
  /** Unique across days and rebuilds; doubles as the review id (idempotency key). */
  slotId: string;
  cardId: string;
  entryId: string;
  kind: TeacherCardKind;
  origin: SlotOrigin;
  presentation: TeacherPresentation;
  /** Fingerprint of what the slot shows; a changed entry no longer matches. */
  sig: string;
}

export interface DeckDailyQueue {
  day: string;
  builtAt: number;
  deckVersion: string;
  nextSeq: number;
  slots: DeckQueueSlot[];
}

export interface DeckReviewRecord {
  reviewId: string;
  cardId: string;
  entryId: string;
  kind: TeacherCardKind;
  origin: SlotOrigin;
  rating: PracticeRating;
  at: number;
  day: string;
  presentation: string;
}

export interface DeckIntroduction {
  day: string;
  at: number;
  source: 'practice' | 'migration';
}

export interface DeckProgress {
  version: typeof DECK_PROGRESS_VERSION;
  deckId: string;
  settings: DeckSettings;
  /** Introduced entries by stable entry id. */
  introduced: Record<string, DeckIntroduction>;
  /** FSRS state by card id. A non-recognition card exists only once unlocked. */
  cards: Record<string, CardState>;
  reviews: DeckReviewRecord[];
  queue: DeckDailyQueue | null;
  migration: { at: number; entries: number; recognitionStates: number } | null;
}

export interface DeckDayStats {
  day: string;
  total: number;
  introduced: number;
  unseen: number;
  /** Every card due today (not capped). */
  dueBacklog: number;
  reviewsDoneToday: number;
  newDoneToday: number;
  /** Pending slots in today's queue, by origin. */
  plannedReviews: number;
  plannedNew: number;
  plannedRepeats: number;
  completedToday: number;
}

export interface DeckPlan {
  queue: DeckDailyQueue;
  pending: DeckQueueSlot[];
  stats: DeckDayStats;
}

// --------------------------------------------------------------------------- time

export function localDayKey(now: number): string {
  return todayDateKey(new Date(now));
}

export function nextLocalMidnight(now: number): number {
  const date = new Date(now);
  return new Date(date.getFullYear(), date.getMonth(), date.getDate() + 1).getTime();
}

// --------------------------------------------------------------------------- store

export function deckProgressStorageKey(deckId: string): string {
  return `${DECK_PROGRESS_KEY_PREFIX}${deckId}`;
}

function clampInt(value: unknown, fallback: number, max: number): number {
  const number = typeof value === 'number' ? value : Number(value);
  if (!Number.isFinite(number)) return fallback;
  return Math.min(max, Math.max(0, Math.round(number)));
}

export function normalizeDeckSettings(raw: unknown, defaults: DeckSettings): DeckSettings {
  const source = (raw && typeof raw === 'object' ? raw : {}) as Partial<DeckSettings>;
  return {
    newPerDay: clampInt(source.newPerDay, defaults.newPerDay, MAX_NEW_PER_DAY),
    reviewCap: clampInt(source.reviewCap, defaults.reviewCap, MAX_REVIEW_CAP),
  };
}

export function emptyDeckProgress(deckId: string, defaults: DeckSettings): DeckProgress {
  return {
    version: DECK_PROGRESS_VERSION,
    deckId,
    settings: normalizeDeckSettings(defaults, defaults),
    introduced: {},
    cards: {},
    reviews: [],
    queue: null,
    migration: null,
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function normalizeCardState(raw: unknown): CardState | null {
  if (!isRecord(raw)) return null;
  const num = (value: unknown, fallback = 0) =>
    typeof value === 'number' && Number.isFinite(value) ? value : fallback;
  const due = typeof raw.due === 'number' ? raw.due : new Date(String(raw.due)).getTime();
  if (!Number.isFinite(due)) return null;
  const state = raw.state === State.Learning || raw.state === State.Review || raw.state === State.Relearning
    ? raw.state
    : State.New;
  const lastReview = typeof raw.last_review === 'number'
    ? raw.last_review
    : raw.last_review
      ? new Date(String(raw.last_review)).getTime()
      : NaN;
  return {
    due,
    stability: num(raw.stability),
    difficulty: num(raw.difficulty),
    elapsed_days: num(raw.elapsed_days),
    scheduled_days: num(raw.scheduled_days),
    learning_steps: num(raw.learning_steps),
    reps: num(raw.reps),
    lapses: num(raw.lapses),
    state,
    ...(Number.isFinite(lastReview) ? { last_review: lastReview } : {}),
  };
}

/** Tolerant parse; unreadable data is kept under `<key>.corrupt` and an empty store returned. */
export function readDeckProgress(storage: StorageLike, deckId: string, defaults: DeckSettings): DeckProgress {
  const key = deckProgressStorageKey(deckId);
  let raw: string | null = null;
  try {
    raw = storage.getItem(key);
  } catch {
    return emptyDeckProgress(deckId, defaults);
  }
  if (!raw) return emptyDeckProgress(deckId, defaults);
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    if (parsed.version !== DECK_PROGRESS_VERSION || parsed.deckId !== deckId) throw new Error('version');
    const cards: Record<string, CardState> = {};
    for (const [cardId, value] of Object.entries(isRecord(parsed.cards) ? parsed.cards : {})) {
      const card = normalizeCardState(value);
      if (card) cards[cardId] = card;
    }
    const introduced: Record<string, DeckIntroduction> = {};
    for (const [entryId, value] of Object.entries(isRecord(parsed.introduced) ? parsed.introduced : {})) {
      if (isRecord(value) && typeof value.day === 'string' && typeof value.at === 'number') {
        introduced[entryId] = {
          day: value.day,
          at: value.at,
          source: value.source === 'migration' ? 'migration' : 'practice',
        };
      }
    }
    const reviews = Array.isArray(parsed.reviews)
      ? (parsed.reviews as DeckReviewRecord[]).filter(
          (review) => isRecord(review) && typeof review.reviewId === 'string' && typeof review.day === 'string',
        )
      : [];
    const queue = isRecord(parsed.queue) && Array.isArray(parsed.queue.slots) && typeof parsed.queue.day === 'string'
      ? (parsed.queue as unknown as DeckDailyQueue)
      : null;
    const migration = isRecord(parsed.migration)
      ? (parsed.migration as unknown as DeckProgress['migration'])
      : null;
    return {
      version: DECK_PROGRESS_VERSION,
      deckId,
      settings: normalizeDeckSettings(parsed.settings, defaults),
      introduced,
      cards,
      reviews,
      queue,
      migration,
    };
  } catch {
    try {
      storage.setItem(`${key}.corrupt`, raw);
    } catch {
      // Best effort; the empty store below still lets the learner practise.
    }
    return emptyDeckProgress(deckId, defaults);
  }
}

/** Returns false when the browser refused the write (quota, blocked storage). */
export function writeDeckProgress(storage: StorageLike, progress: DeckProgress): boolean {
  try {
    storage.setItem(deckProgressStorageKey(progress.deckId), JSON.stringify(progress));
    return true;
  } catch {
    return false;
  }
}

// --------------------------------------------------------------------------- cards

/** Card kinds the entry can actually schedule with the loaded deck (no empty modes). */
export function schedulableKinds(deck: TeacherDeck, entry: TeacherDeckEntry): TeacherCardKind[] {
  return TEACHER_CARD_KINDS.filter((kind) => {
    if (kind === 'recognition') return true;
    if (kind === 'production') return Boolean(entry.cards.production);
    if (kind === 'cloze') return entryClozeItems(deck, entry).length > 0;
    return entryGrammarItems(deck, entry).length > 0;
  });
}

function cardIdFor(entry: TeacherDeckEntry, kind: TeacherCardKind): string {
  return entry.cards[kind]?.cardId ?? `${entry.entryId}:${kind}`;
}

/**
 * Deterministic presentation for a card, rotating with its review count:
 * recognition/production alternate flashcard and choice (a first exposure is always
 * the flashcard), cloze rotates its ≤3 sentences, grammar rotates its modes and then
 * the items (and classify sets) within a mode.
 */
export function choosePresentation(
  deck: TeacherDeck,
  entry: TeacherDeckEntry,
  kind: TeacherCardKind,
  card: CardState | undefined,
): TeacherPresentation | null {
  const reps = card?.reps ?? 0;
  if (kind === 'recognition') {
    return reps % 2 === 1 && entry.cards.recognition.choice
      ? { type: 'recognition-choice' }
      : { type: 'recognition-flashcard' };
  }
  if (kind === 'production') {
    if (!entry.cards.production) return null;
    return reps % 2 === 1 && entry.cards.production.choice
      ? { type: 'production-choice' }
      : { type: 'production-flashcard' };
  }
  if (kind === 'cloze') {
    const items = entryClozeItems(deck, entry);
    if (items.length === 0) return null;
    return { type: 'cloze', clozeId: items[reps % items.length]!.clozeId };
  }
  const items = entryGrammarItems(deck, entry);
  if (items.length === 0) return null;
  const modes = Array.from(new Set(items.map((item) => item.mode)));
  const mode = modes[reps % modes.length]!;
  const round = Math.floor(reps / modes.length);
  const ofMode = items.filter((item) => item.mode === mode);
  const picked = ofMode[round % ofMode.length]!;
  const itemId = grammarItemId(picked.mode, picked.item);
  if (picked.mode === 'classify') {
    const sets = picked.item.sets ?? [];
    if (sets.length === 0) return null;
    return { type: 'grammar', mode, itemId, setId: sets[round % sets.length]!.setId };
  }
  return { type: 'grammar', mode, itemId };
}

function grammarItemId(mode: TeacherGrammarMode, item: unknown): string {
  const record = item as Record<string, string>;
  if (mode === 'stress') return record.stressId!;
  if (mode === 'paradigm') return record.paradigmId!;
  if (mode === 'classify') return record.classifyId!;
  return record.synonymId!;
}

function hashString(value: string): string {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(36);
}

/** Fingerprint of the content a presentation shows, or null when it no longer resolves. */
export function presentationSignature(
  deck: TeacherDeck,
  entry: TeacherDeckEntry,
  presentation: TeacherPresentation,
): string | null {
  const base = [entry.uk, entry.en];
  switch (presentation.type) {
    case 'recognition-flashcard':
    case 'production-flashcard':
      if (presentation.type === 'production-flashcard' && !entry.cards.production) return null;
      return hashString(JSON.stringify([presentation.type, ...base]));
    case 'recognition-choice':
    case 'production-choice': {
      const card = presentation.type === 'recognition-choice' ? entry.cards.recognition : entry.cards.production;
      if (!card?.choice) return null;
      return hashString(JSON.stringify([presentation.type, ...base, card.choice]));
    }
    case 'cloze': {
      const item = deck.clozeById.get(presentation.clozeId);
      if (!item || item.entryId !== entry.entryId) return null;
      return hashString(JSON.stringify(['cloze', ...base, item.sentence, item.form, item.options]));
    }
    case 'grammar': {
      const found = deck.grammarById.get(presentation.itemId);
      if (!found || found.item.entryId !== entry.entryId) return null;
      if (presentation.setId && found.mode === 'classify'
        && !found.item.sets.some((set) => set.setId === presentation.setId)) return null;
      return hashString(JSON.stringify(['grammar', ...base, presentation.setId ?? '', found.item]));
    }
    default:
      return null;
  }
}

export function presentationKey(presentation: TeacherPresentation): string {
  switch (presentation.type) {
    case 'cloze':
      return `cloze:${presentation.clozeId}`;
    case 'grammar':
      return `grammar:${presentation.mode}:${presentation.itemId}${presentation.setId ? `:${presentation.setId}` : ''}`;
    default:
      return presentation.type;
  }
}

// --------------------------------------------------------------------------- counts

export function introducedTodayCount(progress: DeckProgress, day: string): number {
  let count = 0;
  for (const intro of Object.values(progress.introduced)) {
    if (intro.day === day && intro.source === 'practice') count += 1;
  }
  return count;
}

/** Distinct cards reviewed today as scheduled reviews (what the review cap counts). */
export function reviewedTodayCardIds(progress: DeckProgress, day: string): Set<string> {
  const ids = new Set<string>();
  for (const review of progress.reviews) {
    if (review.day === day && review.origin === 'review') ids.add(review.cardId);
  }
  return ids;
}

interface DueCard {
  entry: TeacherDeckEntry;
  kind: TeacherCardKind;
  cardId: string;
  due: number;
}

/** Every card of an introduced entry that is due before the next local midnight. */
export function dueCards(deck: TeacherDeck, progress: DeckProgress, now: number): DueCard[] {
  const endOfDay = nextLocalMidnight(now);
  const due: DueCard[] = [];
  for (const entry of deck.entries) {
    const intro = progress.introduced[entry.entryId];
    if (!intro) continue;
    for (const kind of schedulableKinds(deck, entry)) {
      const cardId = cardIdFor(entry, kind);
      const card = progress.cards[cardId];
      if (!card) {
        // An introduced entry without recognition state (e.g. migrated from a
        // mode other than recognition) is due now; other kinds are still locked.
        if (kind === 'recognition') due.push({ entry, kind, cardId, due: intro.at });
        continue;
      }
      if (card.due < endOfDay) due.push({ entry, kind, cardId, due: card.due });
    }
  }
  const kindRank = (kind: TeacherCardKind) => TEACHER_CARD_KINDS.indexOf(kind);
  due.sort(
    (left, right) =>
      left.due - right.due ||
      right.entry.firstSeen - left.entry.firstSeen ||
      kindRank(left.kind) - kindRank(right.kind) ||
      left.cardId.localeCompare(right.cardId),
  );
  return due;
}

/** Unseen entries, newest `firstSeen` first (entry id breaks ties). */
export function unseenEntries(deck: TeacherDeck, progress: DeckProgress): TeacherDeckEntry[] {
  return deck.entries
    .filter((entry) => !progress.introduced[entry.entryId])
    .sort((left, right) => right.firstSeen - left.firstSeen || left.entryId.localeCompare(right.entryId));
}

// --------------------------------------------------------------------------- plan

function slotStillValid(
  deck: TeacherDeck,
  progress: DeckProgress,
  slot: DeckQueueSlot,
  endOfDay: number,
): boolean {
  const entry = deck.entriesById.get(slot.entryId);
  if (!entry) return false;
  if (!schedulableKinds(deck, entry).includes(slot.kind)) return false;
  if (cardIdFor(entry, slot.kind) !== slot.cardId) return false;
  if (presentationSignature(deck, entry, slot.presentation) !== slot.sig) return false;
  if (slot.origin === 'new') return !progress.introduced[slot.entryId];
  const card = progress.cards[slot.cardId];
  if (!card) return slot.kind === 'recognition' && Boolean(progress.introduced[slot.entryId]);
  return card.due < endOfDay;
}

/** Keep two slots of the same entry apart where possible (one would give the other away). */
function spreadByEntry(slots: DeckQueueSlot[], previous?: DeckQueueSlot): DeckQueueSlot[] {
  const rest = [...slots];
  const ordered: DeckQueueSlot[] = [];
  let last = previous;
  while (rest.length > 0) {
    let index = rest.findIndex((slot) => slot.entryId !== last?.entryId);
    if (index < 0) index = 0;
    const [slot] = rest.splice(index, 1);
    ordered.push(slot!);
    last = slot;
  }
  return ordered;
}

/**
 * Today's queue. Restores the saved queue on the same local day (completed slots
 * kept, pending slots reconciled against the current deck), re-applies today's
 * allowances (settings may have changed) and tops up: due reviews first up to the
 * review cap, then unseen entries newest-first up to the new-words allowance.
 * A saved queue from another day is discarded and the day rebuilt.
 */
export function planDeckDay(deck: TeacherDeck, progress: DeckProgress, now: number): DeckPlan {
  const day = localDayKey(now);
  const endOfDay = nextLocalMidnight(now);
  const applied = new Set(progress.reviews.map((review) => review.reviewId));
  const saved = progress.queue && progress.queue.day === day ? progress.queue : null;
  const builtAt = saved?.builtAt ?? now;
  let seq = saved?.nextSeq ?? 0;

  const completed: DeckQueueSlot[] = [];
  const kept: DeckQueueSlot[] = [];
  const keptKeys = new Set<string>();
  for (const slot of saved?.slots ?? []) {
    if (applied.has(slot.slotId)) {
      completed.push(slot);
      continue;
    }
    // One pending slot per card (a repeat and a review of one card never both wait).
    const dedupeKey = slot.origin === 'new' ? `new:${slot.entryId}` : slot.cardId;
    if (keptKeys.has(dedupeKey) || !slotStillValid(deck, progress, slot, endOfDay)) continue;
    keptKeys.add(dedupeKey);
    kept.push(slot);
  }

  const reviewedToday = reviewedTodayCardIds(progress, day);
  const touchedToday = new Set(progress.reviews.filter((review) => review.day === day).map((review) => review.cardId));
  const reviewAllowance = Math.max(0, progress.settings.reviewCap - reviewedToday.size);
  const newAllowance = Math.max(0, progress.settings.newPerDay - introducedTodayCount(progress, day));

  // Settings may have been lowered since the queue was saved: trim pending slots.
  let keptReviews = 0;
  let keptNew = 0;
  const pending = kept.filter((slot) => {
    if (slot.origin === 'review') return keptReviews++ < reviewAllowance;
    if (slot.origin === 'new') return keptNew++ < newAllowance;
    return true;
  });
  const pendingCards = new Set(pending.map((slot) => slot.cardId));
  const pendingNewEntries = new Set(pending.filter((slot) => slot.origin === 'new').map((slot) => slot.entryId));

  const makeSlot = (entry: TeacherDeckEntry, kind: TeacherCardKind, origin: SlotOrigin): DeckQueueSlot | null => {
    const cardId = cardIdFor(entry, kind);
    const presentation = choosePresentation(deck, entry, kind, progress.cards[cardId]);
    if (!presentation) return null;
    const sig = presentationSignature(deck, entry, presentation);
    if (sig === null) return null;
    let slotId = `${day}:${builtAt}:${seq++}`;
    // Never reuse an applied review id (a slot answered but not yet in the saved queue).
    while (applied.has(slotId)) slotId = `${day}:${builtAt}:${seq++}`;
    return { slotId, cardId, entryId: entry.entryId, kind, origin, presentation, sig };
  };

  let reviewRoom = Math.max(0, reviewAllowance - Math.min(keptReviews, reviewAllowance));
  const addedReviews: DeckQueueSlot[] = [];
  for (const due of dueCards(deck, progress, now)) {
    if (pendingCards.has(due.cardId)) continue;
    let origin: SlotOrigin;
    if (touchedToday.has(due.cardId)) origin = 'repeat';
    else if (reviewRoom > 0) {
      origin = 'review';
      reviewRoom -= 1;
    } else continue;
    const slot = makeSlot(due.entry, due.kind, origin);
    if (slot) addedReviews.push(slot);
  }

  let newRoom = Math.max(0, newAllowance - Math.min(keptNew, newAllowance));
  const addedNew: DeckQueueSlot[] = [];
  for (const entry of unseenEntries(deck, progress)) {
    if (newRoom <= 0) break;
    if (pendingNewEntries.has(entry.entryId)) continue;
    const slot = makeSlot(entry, 'recognition', 'new');
    if (slot) {
      addedNew.push(slot);
      newRoom -= 1;
    }
  }

  // Due reviews first, then new words — kept slots keep their saved order.
  const firstNew = pending.findIndex((slot) => slot.origin === 'new');
  const pendingHead = firstNew < 0 ? pending : pending.slice(0, firstNew);
  const pendingTail = firstNew < 0 ? [] : pending.slice(firstNew);
  const orderedPending = [
    ...pendingHead,
    ...spreadByEntry(addedReviews, pendingHead[pendingHead.length - 1] ?? completed[completed.length - 1]),
    ...pendingTail,
    ...addedNew,
  ];

  const queue: DeckDailyQueue = {
    day,
    builtAt,
    deckVersion: deck.deckVersion,
    nextSeq: seq,
    slots: [...completed, ...orderedPending],
  };
  return { queue, pending: orderedPending, stats: dayStats(deck, progress, now, orderedPending, completed.length) };
}

function dayStats(
  deck: TeacherDeck,
  progress: DeckProgress,
  now: number,
  pending: DeckQueueSlot[],
  completedToday: number,
): DeckDayStats {
  const day = localDayKey(now);
  let introduced = 0;
  for (const entry of deck.entries) if (progress.introduced[entry.entryId]) introduced += 1;
  return {
    day,
    total: deck.entries.length,
    introduced,
    unseen: deck.entries.length - introduced,
    dueBacklog: dueCards(deck, progress, now).length,
    reviewsDoneToday: reviewedTodayCardIds(progress, day).size,
    newDoneToday: introducedTodayCount(progress, day),
    plannedReviews: pending.filter((slot) => slot.origin === 'review').length,
    plannedNew: pending.filter((slot) => slot.origin === 'new').length,
    plannedRepeats: pending.filter((slot) => slot.origin === 'repeat').length,
    completedToday,
  };
}

// --------------------------------------------------------------------------- review

const GRADE: Record<PracticeRating, Grade> = {
  again: Rating.Again,
  hard: Rating.Hard,
  good: Rating.Good,
  easy: Rating.Easy,
};

export interface DeckReviewResult {
  progress: DeckProgress;
  /** False when the review id was already applied (a reload or a second tab). */
  applied: boolean;
  card?: CardState;
  repeatSlot?: DeckQueueSlot;
}

function trimReviews(reviews: DeckReviewRecord[], day: string): DeckReviewRecord[] {
  if (reviews.length <= MAX_DECK_REVIEW_LOG) return reviews;
  let excess = reviews.length - MAX_DECK_REVIEW_LOG;
  return reviews.filter((review) => {
    if (excess > 0 && review.day !== day) {
      excess -= 1;
      return false;
    }
    return true;
  });
}

/**
 * Apply one completed review. Idempotent by `slot.slotId`: a second call with the
 * same slot returns the progress unchanged. A first successful recognition review
 * unlocks the entry's other cards, due the next local midnight. A card that is
 * still in a learning step due today gets a repeat slot at the end of today's queue.
 */
export function applyDeckReview(
  deck: TeacherDeck,
  progress: DeckProgress,
  slot: DeckQueueSlot,
  rating: PracticeRating,
  now: number,
  params: FSRSParameters = practiceFsrsParams(),
): DeckReviewResult {
  if (progress.reviews.some((review) => review.reviewId === slot.slotId)) {
    return { progress, applied: false };
  }
  const day = localDayKey(now);
  const reviewDate = new Date(now);
  const previous = progress.cards[slot.cardId];
  const record = fsrs(params).next(
    previous ? fsrsCardFromState(previous) : createEmptyCard(reviewDate),
    reviewDate,
    GRADE[rating],
  );
  const next = stateFromFsrsCard(record.card);
  const cards = { ...progress.cards, [slot.cardId]: next };
  let introduced = progress.introduced;
  const entry = deck.entriesById.get(slot.entryId);

  if (slot.kind === 'recognition') {
    if (!introduced[slot.entryId]) {
      introduced = { ...introduced, [slot.entryId]: { day, at: now, source: 'practice' } };
    }
    if (rating !== 'again' && entry) {
      const unlockDue = new Date(nextLocalMidnight(now));
      for (const kind of schedulableKinds(deck, entry)) {
        if (kind === 'recognition') continue;
        const cardId = cardIdFor(entry, kind);
        if (!cards[cardId]) cards[cardId] = stateFromFsrsCard(createEmptyCard(unlockDue));
      }
    }
  }

  const reviews = trimReviews(
    [
      ...progress.reviews,
      {
        reviewId: slot.slotId,
        cardId: slot.cardId,
        entryId: slot.entryId,
        kind: slot.kind,
        origin: slot.origin,
        rating,
        at: now,
        day,
        presentation: presentationKey(slot.presentation),
      },
    ],
    day,
  );

  let queue = progress.queue;
  let repeatSlot: DeckQueueSlot | undefined;
  const learning = next.state === State.Learning || next.state === State.Relearning;
  if (queue && queue.day === day && entry && learning && next.due < nextLocalMidnight(now)) {
    const presentation = choosePresentation(deck, entry, slot.kind, next);
    const sig = presentation ? presentationSignature(deck, entry, presentation) : null;
    const applied = new Set(reviews.map((review) => review.reviewId));
    let seq = queue.nextSeq;
    while (applied.has(`${queue.day}:${queue.builtAt}:${seq}`)) seq += 1;
    if (presentation && sig !== null) {
      repeatSlot = {
        slotId: `${queue.day}:${queue.builtAt}:${seq}`,
        cardId: slot.cardId,
        entryId: slot.entryId,
        kind: slot.kind,
        origin: 'repeat',
        presentation,
        sig,
      };
      queue = { ...queue, nextSeq: seq + 1, slots: [...queue.slots, repeatSlot] };
    }
  }

  return {
    progress: { ...progress, cards, introduced, reviews, queue },
    applied: true,
    card: next,
    repeatSlot,
  };
}

/** Next-interval label per rating for a card (flashcard rating buttons). */
export function previewDeckIntervals(
  card: CardState | undefined,
  now: number,
  params: FSRSParameters = practiceFsrsParams(),
): Record<PracticeRating, string> {
  const reviewDate = new Date(now);
  const records = fsrs(params).repeat(card ? fsrsCardFromState(card) : createEmptyCard(reviewDate), reviewDate);
  const previews = {} as Record<PracticeRating, string>;
  for (const rating of Object.keys(GRADE) as PracticeRating[]) {
    previews[rating] = formatFsrsIntervalUk(reviewDate, records[GRADE[rating]].card.due);
  }
  return previews;
}

/**
 * Read-apply-write against storage, so a reload or a second tab never applies a
 * review twice and never loses one. `ok` is false when the write failed.
 */
export function recordDeckReview(
  storage: StorageLike,
  deck: TeacherDeck,
  defaults: DeckSettings,
  slot: DeckQueueSlot,
  rating: PracticeRating,
  now: number,
  params?: FSRSParameters,
): DeckReviewResult & { ok: boolean } {
  const current = readDeckProgress(storage, deck.deckId, defaults);
  const result = applyDeckReview(deck, current, slot, rating, now, params);
  const ok = result.applied ? writeDeckProgress(storage, result.progress) : true;
  return { ...result, ok };
}

// --------------------------------------------------------------------------- migration

function normalizeLemma(value: string): string {
  return stripStressMarks(value)
    .replace(/[’ʼ`‘]/g, "'")
    .replace(/\s+/g, ' ')
    .trim()
    .toLocaleLowerCase('uk');
}

const RECOGNITION_LEGACY_MODES = new Set(['flashcards', 'choice', 'matching']);

/** The CEFR practice store's card map (read-only; never modified). */
export function readLegacyPracticeCards(storage: StorageLike): Record<string, unknown> | null {
  try {
    const raw = storage.getItem(SRS_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    return isRecord(parsed.cards) ? parsed.cards : null;
  } catch {
    return null;
  }
}

/**
 * One-time migration: an entry that already has practice state in the browser
 * (the CEFR practice store, where this deck's words used to be practised by Atlas
 * slug or table key) counts as introduced, and its most recent recognition-style
 * state (flashcards, choice, matching) becomes its recognition card. The CEFR store
 * is only read. Migrated entries do not count against today's new-word allowance.
 */
export function migrateLegacyPracticeState(
  deck: TeacherDeck,
  progress: DeckProgress,
  legacyCards: Record<string, unknown> | null,
  now: number,
): DeckProgress {
  if (progress.migration) return progress;
  const byLemma = new Map<string, { mode: string; card: CardState }[]>();
  for (const [key, raw] of Object.entries(legacyCards ?? {})) {
    const parsed = parseCardKey(key);
    if (parsed.quarantined) continue;
    const card = normalizeCardState(raw);
    if (!card || (card.reps <= 0 && card.state === State.New)) continue;
    const lemma = normalizeLemma(parsed.lemmaId);
    const list = byLemma.get(lemma) ?? [];
    list.push({ mode: parsed.mode, card });
    byLemma.set(lemma, list);
  }

  const introduced = { ...progress.introduced };
  const cards = { ...progress.cards };
  let entries = 0;
  let recognitionStates = 0;
  for (const entry of deck.entries) {
    if (introduced[entry.entryId]) continue;
    const names = new Set(
      [entry.key, entry.uk, ...(entry.sourceKeys ?? []), entry.atlas?.slug ?? '']
        .filter(Boolean)
        .map(normalizeLemma),
    );
    const found = Array.from(names).flatMap((name) => byLemma.get(name) ?? []);
    if (found.length === 0) continue;
    const lastSeen = Math.max(...found.map(({ card }) => card.last_review ?? 0));
    const at = lastSeen > 0 ? lastSeen : now;
    introduced[entry.entryId] = { day: localDayKey(at), at, source: 'migration' };
    entries += 1;
    const recognition = found
      .filter(({ mode }) => RECOGNITION_LEGACY_MODES.has(mode))
      .sort((left, right) => (right.card.last_review ?? 0) - (left.card.last_review ?? 0))[0];
    const recognitionId = cardIdFor(entry, 'recognition');
    if (recognition && !cards[recognitionId]) {
      cards[recognitionId] = { ...recognition.card };
      recognitionStates += 1;
    }
  }
  return { ...progress, introduced, cards, migration: { at: now, entries, recognitionStates } };
}

// --------------------------------------------------------------------------- matching

/**
 * A matching round over introduced words (a session activity; never updates FSRS).
 * Entries whose meanings overlap (`conflicts`) or share a label are never grouped.
 * Returns an empty list when fewer than `minimum` compatible entries exist.
 */
export function pickMatchingRound(
  deck: TeacherDeck,
  progress: DeckProgress,
  seed: number,
  size = 5,
  minimum = 3,
): TeacherDeckEntry[] {
  const pool = deck.entries
    .filter((entry) => entry.matching && progress.introduced[entry.entryId])
    .map((entry) => ({ entry, order: Number.parseInt(hashString(`${seed}:${entry.entryId}`), 36) }))
    .sort((left, right) => left.order - right.order)
    .map(({ entry }) => entry);
  const picked: TeacherDeckEntry[] = [];
  const labels = new Set<string>();
  for (const entry of pool) {
    if (picked.length >= size) break;
    const uk = entry.uk.toLocaleLowerCase('uk');
    const en = entry.en.toLocaleLowerCase('en');
    if (labels.has(`uk:${uk}`) || labels.has(`en:${en}`)) continue;
    if (picked.some((other) => other.conflicts.includes(entry.entryId) || entry.conflicts.includes(other.entryId))) {
      continue;
    }
    picked.push(entry);
    labels.add(`uk:${uk}`);
    labels.add(`en:${en}`);
  }
  return picked.length >= minimum ? picked : [];
}
