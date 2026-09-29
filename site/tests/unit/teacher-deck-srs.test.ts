import { beforeEach, describe, expect, test } from 'vitest';
import { State } from 'ts-fsrs';
import { buildTeacherDeck, TeacherDeckLoadError, type TeacherDeck } from '@site/src/lib/lexicon/teacher-deck';
import {
  applyDeckReview,
  deckProgressStorageKey,
  emptyDeckProgress,
  migrateLegacyPracticeState,
  nextLocalMidnight,
  pickMatchingRound,
  planDeckDay,
  readDeckProgress,
  readLegacyPracticeCards,
  recordDeckReview,
  writeDeckProgress,
  type DeckProgress,
  type DeckQueueSlot,
  type DeckSettings,
} from '@site/src/lib/lexicon/teacher-deck-srs';
import type { StorageLike } from '@site/src/lib/lexicon/srs';
import {
  buildFixturePayloads,
  FIXTURE_DECK_ID,
  FIXTURE_ROWS,
  fixtureEntryId,
} from '../helpers/teacher-deck-fixture';

const DEFAULTS: DeckSettings = { newPerDay: 10, reviewCap: 100 };
const DAY1_9AM = new Date(2026, 8, 27, 9, 0).getTime();
const DAY1_3PM = new Date(2026, 8, 27, 15, 0).getTime();
const DAY2_9AM = new Date(2026, 8, 28, 9, 0).getTime();
const DAY3_9AM = new Date(2026, 8, 29, 9, 0).getTime();

function loadFixture(options: Parameters<typeof buildFixturePayloads>[0] = {}): TeacherDeck {
  const { deck, cloze } = buildFixturePayloads(options);
  return buildTeacherDeck(FIXTURE_DECK_ID, deck, cloze);
}

function memoryStorage(): StorageLike & { data: Map<string, string> } {
  const data = new Map<string, string>();
  return {
    data,
    getItem: (key) => data.get(key) ?? null,
    setItem: (key, value) => void data.set(key, value),
    removeItem: (key) => void data.delete(key),
  };
}

function progressWith(settings: Partial<DeckSettings> = {}): DeckProgress {
  return { ...emptyDeckProgress(FIXTURE_DECK_ID, DEFAULTS), settings: { ...DEFAULTS, ...settings } };
}

/** Plan today, then review every pending slot in order with `rating` (repeats included). */
function completeDay(deck: TeacherDeck, start: DeckProgress, now: number, rating: 'good' | 'again' = 'good') {
  let progress: DeckProgress = { ...start, queue: planDeckDay(deck, start, now).queue };
  let guard = 0;
  for (;;) {
    const plan = planDeckDay(deck, progress, now);
    progress = { ...progress, queue: plan.queue };
    const slot = plan.pending[0];
    if (!slot || guard++ > 200) break;
    progress = applyDeckReview(deck, progress, slot, rating, now).progress;
    // Learning steps are minutes long: stay on the same clock so repeats come due.
  }
  return progress;
}

describe('teacher deck artifacts', () => {
  test('validates schema, deck id and matching versions', () => {
    const { deck, cloze } = buildFixturePayloads();
    expect(() => buildTeacherDeck(FIXTURE_DECK_ID, { ...deck, schema: 'atlas-practice' }, cloze)).toThrow(
      TeacherDeckLoadError,
    );
    expect(() => buildTeacherDeck(FIXTURE_DECK_ID, deck, { ...cloze, deckVersion: 'other' })).toThrow(/version/);
    expect(() => buildTeacherDeck('virtual_teacher_lesson', deck, cloze)).toThrow(/deck id/);
    expect(buildTeacherDeck(FIXTURE_DECK_ID, deck, cloze).entries).toHaveLength(FIXTURE_ROWS.length);
  });

  test('matching excludes English glosses that collide after display normalization', () => {
    const matchingDeck = loadFixture();
    matchingDeck.entries[0]!.en = 'Fair, just';
    matchingDeck.entries[5]!.en = 'FAIR; equitable';
    const progress = progressWith({ newPerDay: 0 });
    for (const index of [0, 5, 6, 7]) {
      progress.introduced[fixtureEntryId(index)] = { day: '2026-09-26', at: DAY1_9AM - 86400000, source: 'practice' };
    }
    const round = pickMatchingRound(matchingDeck, progress, 0, 5, 3);
    expect(round).toHaveLength(3);
    expect(round.filter((entry) => [fixtureEntryId(0), fixtureEntryId(5)].includes(entry.entryId))).toHaveLength(1);
  });
});

describe('teacher deck daily plan', () => {
  let deck: TeacherDeck;
  beforeEach(() => {
    deck = loadFixture();
  });

  test('introduces unseen entries newest firstSeen first, as recognition flashcards', () => {
    const plan = planDeckDay(deck, progressWith({ newPerDay: 3 }), DAY1_9AM);
    expect(plan.pending.map((slot) => slot.entryId)).toEqual([
      fixtureEntryId(11),
      fixtureEntryId(10),
      fixtureEntryId(9),
    ]);
    expect(plan.pending.every((slot) => slot.origin === 'new' && slot.kind === 'recognition')).toBe(true);
    expect(plan.pending.every((slot) => slot.presentation.type === 'recognition-flashcard')).toBe(true);
    expect(plan.stats).toMatchObject({ plannedNew: 3, plannedReviews: 0, unseen: 12, dueBacklog: 0 });
  });

  test('new words per day counts distinct entries across sessions, zero allowed', () => {
    let progress: DeckProgress = progressWith({ newPerDay: 3 });
    let plan = planDeckDay(deck, progress, DAY1_9AM);
    progress = { ...progress, queue: plan.queue };
    // Session 1: two words, the first one failed (it repeats but is one word).
    progress = applyDeckReview(deck, progress, plan.pending[0]!, 'again', DAY1_9AM).progress;
    progress = applyDeckReview(deck, progress, plan.pending[1]!, 'good', DAY1_9AM).progress;

    // Session 2 later the same day: one new word left, plus the repeats.
    plan = planDeckDay(deck, progress, DAY1_3PM);
    expect(plan.stats.newDoneToday).toBe(2);
    expect(plan.pending.filter((slot) => slot.origin === 'new').map((slot) => slot.entryId)).toEqual([
      fixtureEntryId(9),
    ]);
    const repeated = plan.pending.filter((slot) => slot.origin === 'repeat').map((slot) => slot.entryId);
    expect(repeated).toContain(fixtureEntryId(11));

    // The next day the allowance resets; newest unseen continue.
    const tomorrow = planDeckDay(deck, progress, DAY2_9AM);
    expect(tomorrow.pending.filter((slot) => slot.origin === 'new').map((slot) => slot.entryId)).toEqual([
      fixtureEntryId(9),
      fixtureEntryId(8),
      fixtureEntryId(7),
    ]);

    expect(planDeckDay(deck, progressWith({ newPerDay: 0 }), DAY1_9AM).pending).toEqual([]);
  });

  test('due reviews come first and are capped by the review cap', () => {
    let progress = completeDay(deck, progressWith({ newPerDay: 5 }), DAY1_9AM);
    // Five words introduced; their recognition cards are due again later.
    const later = DAY1_9AM + 40 * 24 * 60 * 60 * 1000;
    progress = { ...progress, settings: { newPerDay: 2, reviewCap: 3 } };
    const plan = planDeckDay(deck, progress, later);
    expect(plan.stats.dueBacklog).toBeGreaterThan(3);
    expect(plan.stats.plannedReviews).toBe(3);
    expect(plan.pending.slice(0, 3).every((slot) => slot.origin === 'review')).toBe(true);
    expect(plan.pending.slice(3).map((slot) => slot.origin)).toEqual(['new', 'new']);

    // One review done: the cap counts it, so only two more reviews are planned today.
    const next = applyDeckReview(deck, { ...progress, queue: plan.queue }, plan.pending[0]!, 'good', later).progress;
    const after = planDeckDay(deck, next, later + 60_000);
    expect(after.stats.reviewsDoneToday).toBe(1);
    expect(after.stats.plannedReviews).toBe(2);
    // Unfinished reviews are never forgiven: the backlog stays due.
    expect(after.stats.dueBacklog).toBeGreaterThanOrEqual(plan.stats.dueBacklog - 1);
  });

  test('production, cloze and grammar unlock after the first successful recognition, due the next local day', () => {
    const newest = progressWith({ newPerDay: 12 });
    let plan = planDeckDay(deck, newest, DAY1_9AM);
    let progress: DeckProgress = { ...newest, queue: plan.queue };
    const fair = plan.pending.find((slot) => slot.entryId === fixtureEntryId(0))!;
    const id = fixtureEntryId(0);

    progress = applyDeckReview(deck, progress, fair, 'again', DAY1_9AM).progress;
    expect(progress.cards[`${id}:production`]).toBeUndefined();

    plan = planDeckDay(deck, progress, DAY1_9AM + 5 * 60_000);
    const repeat = plan.pending.find((slot) => slot.entryId === id && slot.origin === 'repeat')!;
    progress = applyDeckReview(deck, { ...progress, queue: plan.queue }, repeat, 'good', DAY1_9AM + 5 * 60_000).progress;
    for (const kind of ['production', 'cloze', 'grammar']) {
      const card = progress.cards[`${id}:${kind}`]!;
      expect(card.state).toBe(State.New);
      expect(card.due).toBe(nextLocalMidnight(DAY1_9AM));
    }
    // Not due today (a recognised word is not producible yet) …
    const today = planDeckDay(deck, progress, DAY1_3PM);
    expect(today.pending.some((slot) => slot.entryId === id && slot.kind !== 'recognition')).toBe(false);
    // … due tomorrow as reviews counted by the cap.
    const tomorrow = planDeckDay(deck, progress, DAY2_9AM);
    const kinds = tomorrow.pending.filter((slot) => slot.entryId === id).map((slot) => [slot.kind, slot.origin]);
    expect(kinds).toEqual(
      expect.arrayContaining([
        ['production', 'review'],
        ['cloze', 'review'],
        ['grammar', 'review'],
      ]),
    );
    // Entries without drill data get no empty cloze/grammar cards.
    const other = fixtureEntryId(11);
    expect(Object.keys(progress.cards).filter((cardId) => cardId.startsWith(other))).not.toContain(`${other}:cloze`);
  });

  test('recognition and production keep separate FSRS state', () => {
    let progress = completeDay(deck, progressWith({ newPerDay: 12 }), DAY1_9AM);
    const id = fixtureEntryId(1);
    const recognitionBefore = progress.cards[`${id}:recognition`]!;
    const plan = planDeckDay(deck, progress, DAY2_9AM);
    const production = plan.pending.find((slot) => slot.entryId === id && slot.kind === 'production')!;
    expect(production.presentation.type).toBe('production-flashcard');
    progress = applyDeckReview(deck, { ...progress, queue: plan.queue }, production, 'again', DAY2_9AM).progress;
    expect(progress.cards[`${id}:recognition`]).toEqual(recognitionBefore);
    expect(progress.cards[`${id}:production`]!.lapses + progress.cards[`${id}:production`]!.reps).toBeGreaterThan(0);
    expect(progress.cards[`${id}:production`]).not.toEqual(recognitionBefore);
  });

  test('entries with overlapping meanings never get a production card and are never matched together', () => {
    const progress = completeDay(deck, progressWith({ newPerDay: 12 }), DAY1_9AM);
    expect(progress.cards[`${fixtureEntryId(3)}:production`]).toBeUndefined();
    expect(progress.cards[`${fixtureEntryId(4)}:production`]).toBeUndefined();
    for (let seed = 0; seed < 40; seed += 1) {
      const round = pickMatchingRound(deck, progress, seed, 12);
      const ids = round.map((entry) => entry.entryId);
      expect(ids.includes(fixtureEntryId(3)) && ids.includes(fixtureEntryId(4))).toBe(false);
    }
    expect(pickMatchingRound(deck, progressWith(), 1)).toEqual([]);
  });

  test('cloze rotates sentences and grammar rotates modes with the review count', () => {
    let progress = completeDay(deck, progressWith({ newPerDay: 12 }), DAY1_9AM);
    const id = fixtureEntryId(0);
    const seen: string[] = [];
    let now = DAY2_9AM;
    for (let day = 0; day < 4; day += 1) {
      const plan = planDeckDay(deck, progress, now);
      progress = { ...progress, queue: plan.queue };
      for (const slot of plan.pending.filter((s) => s.entryId === id && (s.kind === 'cloze' || s.kind === 'grammar'))) {
        seen.push(JSON.stringify(slot.presentation));
        progress = applyDeckReview(deck, progress, slot, 'good', now).progress;
      }
      now += 40 * 24 * 60 * 60 * 1000;
    }
    expect(seen).toEqual(expect.arrayContaining([
      JSON.stringify({ type: 'cloze', clozeId: `${id}:cloze:0` }),
      JSON.stringify({ type: 'cloze', clozeId: `${id}:cloze:1` }),
      JSON.stringify({ type: 'grammar', mode: 'stress', itemId: `${id}:stress` }),
      JSON.stringify({ type: 'grammar', mode: 'classify', itemId: `${id}:classify`, setId: 'pos' }),
    ]));
  });
});

describe('teacher deck continuity', () => {
  let deck: TeacherDeck;
  beforeEach(() => {
    deck = loadFixture();
  });

  test('a review is applied once, even when replayed after a reload', () => {
    const storage = memoryStorage();
    const start = progressWith({ newPerDay: 2 });
    const plan = planDeckDay(deck, start, DAY1_9AM);
    writeDeckProgress(storage, { ...start, queue: plan.queue });
    const slot = plan.pending[0]!;

    const first = recordDeckReview(storage, deck, DEFAULTS, slot, 'good', DAY1_9AM);
    expect(first).toMatchObject({ applied: true, ok: true });
    // The page reloads and replays the same answer (e.g. an unflushed click).
    const replay = recordDeckReview(storage, deck, DEFAULTS, slot, 'good', DAY1_9AM + 1000);
    expect(replay.applied).toBe(false);

    const reloaded = readDeckProgress(storage, FIXTURE_DECK_ID, DEFAULTS);
    expect(reloaded.reviews.filter((review) => review.reviewId === slot.slotId)).toHaveLength(1);
    expect(reloaded.cards[slot.cardId]!.reps).toBe(1);
    const resumed = planDeckDay(deck, reloaded, DAY1_9AM + 2000);
    expect(resumed.pending.map((s) => s.slotId)).not.toContain(slot.slotId);
    expect(resumed.stats.completedToday).toBe(1);
  });

  test('restores the saved queue on the same local day and rebuilds it on the next', () => {
    const storage = memoryStorage();
    const start = progressWith({ newPerDay: 4 });
    const morning = planDeckDay(deck, start, DAY1_9AM);
    writeDeckProgress(storage, { ...start, queue: morning.queue });
    recordDeckReview(storage, deck, DEFAULTS, morning.pending[0]!, 'easy', DAY1_9AM);

    const afternoon = planDeckDay(deck, readDeckProgress(storage, FIXTURE_DECK_ID, DEFAULTS), DAY1_3PM);
    expect(afternoon.queue.builtAt).toBe(morning.queue.builtAt);
    expect(afternoon.pending.map((slot) => slot.slotId)).toEqual(morning.pending.slice(1).map((slot) => slot.slotId));

    const nextDay = planDeckDay(deck, readDeckProgress(storage, FIXTURE_DECK_ID, DEFAULTS), DAY2_9AM);
    expect(nextDay.queue.day).not.toBe(morning.queue.day);
    expect(nextDay.queue.builtAt).toBe(DAY2_9AM);
    expect(nextDay.pending.some((slot) => morning.queue.slots.some((old) => old.slotId === slot.slotId))).toBe(false);
    // Yesterday's unfinished new words are still the newest unseen ones.
    expect(nextDay.pending.filter((slot) => slot.origin === 'new').map((slot) => slot.entryId).slice(0, 3)).toEqual(
      morning.pending.slice(1).map((slot) => slot.entryId),
    );
  });

  test('reconciles a saved queue against a new deck version, keeping history', () => {
    const start = progressWith({ newPerDay: 4 });
    const plan = planDeckDay(deck, start, DAY1_9AM);
    let progress: DeckProgress = { ...start, queue: plan.queue };
    progress = applyDeckReview(deck, progress, plan.pending[0]!, 'good', DAY1_9AM).progress;
    const doneEntry = plan.pending[0]!.entryId;
    const removed = plan.pending[1]!.entryId; // index 10
    const changed = plan.pending[2]!.entryId; // index 9

    const rows = FIXTURE_ROWS.map((row, index) =>
      index === 9 ? { ...row, teacherEn: 'Cockroach (insect)' } : row,
    );
    const refreshed = buildFixturePayloads({ deckVersion: 'teacher-v1-fixture0002', rows });
    refreshed.deck.entries = refreshed.deck.entries.filter((entry) => entry.entryId !== removed);
    const next = buildTeacherDeck(FIXTURE_DECK_ID, refreshed.deck, refreshed.cloze);

    const reconciled = planDeckDay(next, progress, DAY1_3PM);
    expect(reconciled.queue.deckVersion).toBe('teacher-v1-fixture0002');
    expect(reconciled.pending.some((slot) => slot.entryId === removed)).toBe(false);
    const changedSlot = reconciled.pending.find((slot) => slot.entryId === changed)!;
    expect(changedSlot.slotId).not.toBe(plan.pending[2]!.slotId);
    // The untouched pending slot survives with its id.
    expect(reconciled.pending.map((slot) => slot.slotId)).toContain(plan.pending[3]!.slotId);
    // History of the completed word is kept.
    expect(progress.introduced[doneEntry]).toBeDefined();
    expect(reconciled.stats.completedToday).toBe(1);
    expect(reconciled.stats.newDoneToday).toBe(1);
  });

  test('settings are per deck and persisted; lowering them trims today\'s pending queue', () => {
    const storage = memoryStorage();
    const start = progressWith({ newPerDay: 6 });
    const plan = planDeckDay(deck, start, DAY1_9AM);
    writeDeckProgress(storage, { ...start, queue: plan.queue, settings: { newPerDay: 2, reviewCap: 100 } });
    const reloaded = readDeckProgress(storage, FIXTURE_DECK_ID, DEFAULTS);
    expect(reloaded.settings).toEqual({ newPerDay: 2, reviewCap: 100 });
    expect(planDeckDay(deck, reloaded, DAY1_9AM).pending).toHaveLength(2);
    expect(storage.data.has(deckProgressStorageKey(FIXTURE_DECK_ID))).toBe(true);
    expect(readDeckProgress(memoryStorage(), FIXTURE_DECK_ID, DEFAULTS).settings).toEqual(DEFAULTS);
  });

  test('a session that crosses midnight rebuilds for the new day', () => {
    const lateNight = new Date(2026, 8, 27, 23, 58).getTime();
    const start = progressWith({ newPerDay: 2 });
    const plan = planDeckDay(deck, start, lateNight);
    const progress: DeckProgress = { ...start, queue: plan.queue };
    const afterMidnight = planDeckDay(deck, progress, new Date(2026, 8, 28, 0, 2).getTime());
    expect(afterMidnight.queue.day).toBe('2026-09-28');
    expect(afterMidnight.queue.slots.every((slot) => slot.slotId.startsWith('2026-09-28:'))).toBe(true);
  });
});

describe('teacher deck migration of existing practice state', () => {
  test('entries practised before count as introduced; recognition state carries over', () => {
    const deck = loadFixture();
    const storage = memoryStorage();
    const legacyCard = {
      due: DAY3_9AM,
      stability: 12,
      difficulty: 4,
      elapsed_days: 3,
      scheduled_days: 12,
      learning_steps: 0,
      reps: 4,
      lapses: 0,
      state: State.Review,
      last_review: DAY1_9AM,
    };
    storage.setItem(
      'lu-lexicon-srs',
      JSON.stringify({
        version: 4,
        cards: {
          // By Atlas slug (the practice shards' lemma id) …
          'справедливий::flashcards': legacyCard,
          // … and by the raw table key (the old custom-deck fallback), cloze only.
          'Таємно::cloze': { ...legacyCard, last_review: DAY1_9AM - 1000 },
          // Not in this deck.
          'кіт::flashcards': legacyCard,
        },
      }),
    );
    const legacy = readLegacyPracticeCards(storage);
    const migrated = migrateLegacyPracticeState(deck, progressWith(), legacy, DAY2_9AM);

    expect(Object.keys(migrated.introduced).sort()).toEqual([fixtureEntryId(0), fixtureEntryId(5)].sort());
    expect(migrated.introduced[fixtureEntryId(0)]!.source).toBe('migration');
    expect(migrated.cards[`${fixtureEntryId(0)}:recognition`]).toMatchObject({ reps: 4, stability: 12, due: DAY3_9AM });
    for (const kind of ['production', 'cloze', 'grammar']) {
      expect(migrated.cards[`${fixtureEntryId(0)}:${kind}`]).toMatchObject({
        reps: 0, state: State.New, due: nextLocalMidnight(DAY2_9AM),
      });
    }
    expect(migrated.cards[`${fixtureEntryId(5)}:recognition`]).toBeUndefined();
    expect(migrated.migration).toEqual({ at: DAY2_9AM, entries: 2, recognitionStates: 1 });

    const plan = planDeckDay(deck, migrated, DAY2_9AM);
    // Not re-drilled as new, not counted against today's new words.
    expect(plan.pending.some((slot) => slot.origin === 'new' && slot.entryId === fixtureEntryId(0))).toBe(false);
    expect(plan.stats.newDoneToday).toBe(0);
    expect(plan.stats.plannedNew).toBe(10);
    expect(plan.pending.some((slot) => slot.entryId === fixtureEntryId(0) && slot.kind === 'production')).toBe(false);
    const nextDay = planDeckDay(deck, migrated, DAY3_9AM);
    expect(nextDay.pending.some((slot) => slot.entryId === fixtureEntryId(0) && slot.kind === 'production')).toBe(true);
    // The cloze-only word has no recognition state yet, so it is due as a review now.
    expect(plan.pending.find((slot) => slot.entryId === fixtureEntryId(5))).toMatchObject({
      kind: 'recognition',
      origin: 'review',
    });
    // Runs once; the CEFR store is untouched.
    expect(migrateLegacyPracticeState(deck, migrated, legacy, DAY3_9AM)).toBe(migrated);
    expect(JSON.parse(storage.getItem('lu-lexicon-srs')!).cards['справедливий::flashcards']).toEqual(legacyCard);
  });
});

describe('teacher deck storage recovery', () => {
  test('saves a corrupt payload separately and returns an empty usable store', () => {
    const storage = memoryStorage();
    const key = deckProgressStorageKey(FIXTURE_DECK_ID);
    storage.setItem(key, '{broken json');
    const recovered = readDeckProgress(storage, FIXTURE_DECK_ID, DEFAULTS);
    expect(recovered).toEqual(emptyDeckProgress(FIXTURE_DECK_ID, DEFAULTS));
    expect(storage.getItem(`${key}.corrupt`)).toBe('{broken json');
    expect(writeDeckProgress(storage, recovered)).toBe(true);
    expect(readDeckProgress(storage, FIXTURE_DECK_ID, DEFAULTS)).toEqual(recovered);
  });
});

describe('queue slot shape', () => {
  test('slot ids are unique within and across days', () => {
    const deck = loadFixture();
    const ids = new Set<string>();
    const collect = (slots: DeckQueueSlot[]) => slots.forEach((slot) => ids.add(slot.slotId));
    const day1 = planDeckDay(deck, progressWith({ newPerDay: 5 }), DAY1_9AM);
    collect(day1.queue.slots);
    const day2 = planDeckDay(deck, progressWith({ newPerDay: 5 }), DAY2_9AM);
    collect(day2.queue.slots);
    expect(ids.size).toBe(day1.queue.slots.length + day2.queue.slots.length);
  });
});
