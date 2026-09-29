import { afterEach, describe, expect, test } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { State } from 'ts-fsrs';
import TeacherDeckPractice from '@site/src/components/practice/TeacherDeckPractice';
import { buildTeacherDeck, type TeacherDeck } from '@site/src/lib/lexicon/teacher-deck';
import {
  deckProgressStorageKey,
  emptyDeckProgress,
  nextLocalMidnight,
  writeDeckProgress,
  type DeckProgress,
} from '@site/src/lib/lexicon/teacher-deck-srs';
import type { StorageLike } from '@site/src/lib/lexicon/srs';
import { buildFixturePayloads, FIXTURE_DECK_ID, FIXTURE_ROWS, fixtureEntryId } from '../helpers/teacher-deck-fixture';

const CONFIG = {
  deckFile: 'practice-deck.teacher.json',
  clozeFile: 'practice-cloze.teacher.json',
  newPerDay: 10,
  reviewCap: 100,
};
const DAY1 = new Date(2026, 8, 27, 9, 0).getTime();
const DAY2 = new Date(2026, 8, 28, 9, 0).getTime();

function memoryStorage(): StorageLike & { data: Map<string, string> } {
  const data = new Map<string, string>();
  return {
    data,
    getItem: (key) => data.get(key) ?? null,
    setItem: (key, value) => void data.set(key, value),
    removeItem: (key) => void data.delete(key),
  };
}

function fixtureDeck(options: Parameters<typeof buildFixturePayloads>[0] = {}): TeacherDeck {
  const { deck, cloze } = buildFixturePayloads(options);
  return buildTeacherDeck(FIXTURE_DECK_ID, deck, cloze);
}

function renderPanel(deck: TeacherDeck, storage: StorageLike, clock: { now: number }) {
  return render(
    <TeacherDeckPractice
      deckId={FIXTURE_DECK_ID}
      titleUk="Приклад розробника"
      titleEn="Dev's example deck"
      config={CONFIG}
      chromeLocale="en"
      loadDeck={() => Promise.resolve(deck)}
      storage={storage}
      now={() => clock.now}
    />,
  );
}

function storedProgress(storage: StorageLike): DeckProgress {
  return JSON.parse(storage.getItem(deckProgressStorageKey(FIXTURE_DECK_ID))!) as DeckProgress;
}

afterEach(() => cleanup());

describe('TeacherDeckPractice', () => {
  test("shows the teacher's English (with the source aspect label) as the meaning", async () => {
    // Put a verb last so it is the newest entry and introduced first.
    const verb = FIXTURE_ROWS[1]!;
    const rows = [...FIXTURE_ROWS.filter((row) => row !== verb), verb];
    const deck = fixtureDeck({ rows });
    const storage = memoryStorage();
    renderPanel(deck, storage, { now: DAY1 });

    fireEvent.click(await screen.findByTestId('teacher-deck-start'));
    const card = within(screen.getByTestId('teacher-deck-recognition-flashcard'));
    expect(screen.getByTestId('teacher-deck-new-word')).toBeInTheDocument();
    const front = card.getByRole('button', { name: /Витирати/ });
    expect(front.querySelector('.flashcard-front .flashcard-word')).toHaveTextContent('Витирати');
    // The back is the teacher's English, never the Ukrainian key itself.
    expect(front.querySelector('.flashcard-back .flashcard-word')).toHaveTextContent('To wipe (impf.)');
    expect(front.querySelector('.flashcard-back .flashcard-word')).not.toHaveTextContent('Витирати');
  });

  test('persists each review as it happens and resumes the same queue after a reload', async () => {
    const deck = fixtureDeck();
    const storage = memoryStorage();
    const clock = { now: DAY1 };
    const first = renderPanel(deck, storage, clock);

    fireEvent.click(await screen.findByTestId('teacher-deck-start'));
    const card = screen.getByTestId('teacher-deck-recognition-flashcard');
    expect(card).toHaveTextContent('Цілодобово');
    fireEvent.click(within(card).getByRole('button', { name: /Цілодобово/ }));
    fireEvent.click(within(card).getByRole('button', { name: /Easy/ }));

    const saved = storedProgress(storage);
    expect(saved.reviews).toHaveLength(1);
    expect(saved.introduced[fixtureEntryId(11)]).toMatchObject({ source: 'practice' });
    expect(saved.cards[`${fixtureEntryId(11)}:recognition`]!.reps).toBe(1);
    first.unmount();

    // Reload later the same day: the panel offers to continue, and the next card is
    // the next queued word — the answered one is not asked again.
    clock.now = DAY1 + 60 * 60 * 1000;
    renderPanel(deck, storage, clock);
    const start = await screen.findByTestId('teacher-deck-start');
    expect(start).toHaveTextContent("Continue today's practice");
    fireEvent.click(start);
    expect(screen.getByTestId('teacher-deck-recognition-flashcard')).toHaveTextContent('Камера спостереження');
    expect(storedProgress(storage).reviews).toHaveLength(1);
  });

  test('EN→UK recall needs an attempt before the answer shows, and rates only the production card', async () => {
    const deck = fixtureDeck();
    const storage = memoryStorage();
    const id = fixtureEntryId(0);
    const recognition = {
      due: DAY2 + 10 * 24 * 60 * 60 * 1000,
      stability: 10,
      difficulty: 5,
      elapsed_days: 0,
      scheduled_days: 10,
      learning_steps: 0,
      reps: 2,
      lapses: 0,
      state: State.Review,
      last_review: DAY1,
    };
    const progress: DeckProgress = {
      ...emptyDeckProgress(FIXTURE_DECK_ID, { newPerDay: 0, reviewCap: 100 }),
      introduced: { [id]: { day: '2026-09-27', at: DAY1, source: 'practice' } },
      cards: {
        [`${id}:recognition`]: recognition,
        [`${id}:production`]: {
          ...recognition,
          due: nextLocalMidnight(DAY1),
          stability: 0,
          difficulty: 0,
          scheduled_days: 0,
          reps: 0,
          state: State.New,
        },
      },
      migration: { at: DAY1, entries: 0, recognitionStates: 0 },
    };
    writeDeckProgress(storage, progress);
    renderPanel(deck, storage, { now: DAY2 });

    expect(await screen.findByTestId('teacher-deck-session-size')).toHaveTextContent('1 due + 0 new');
    fireEvent.click(screen.getByTestId('teacher-deck-start'));
    const stage = screen.getByTestId('teacher-deck-production-flashcard');
    expect(within(stage).getByTestId('teacher-deck-prompt')).toHaveTextContent('Fair');
    expect(within(stage).queryByTestId('teacher-deck-answer')).toBeNull();
    const check = within(stage).getByTestId('teacher-deck-reveal');
    expect(check).toBeDisabled();

    fireEvent.change(within(stage).getByTestId('teacher-deck-attempt'), { target: { value: 'справедливий' } });
    fireEvent.click(check);
    expect(within(stage).getByTestId('teacher-deck-answer')).toHaveTextContent('Справедливий');
    expect(within(stage).getByTestId('teacher-deck-attempt-result')).toHaveTextContent('✓');
    fireEvent.click(within(stage).getByTestId('teacher-deck-rate-good'));

    const saved = storedProgress(storage);
    expect(saved.cards[`${id}:production`]!.reps).toBe(1);
    expect(saved.cards[`${id}:recognition`]).toEqual(recognition);
    expect(saved.reviews.map((review) => review.cardId)).toEqual([`${id}:production`]);
  });

  test('daily settings are editable, persisted per deck, and zero new words is allowed', async () => {
    const deck = fixtureDeck();
    const storage = memoryStorage();
    renderPanel(deck, storage, { now: DAY1 });

    expect(await screen.findByTestId('teacher-deck-session-size')).toHaveTextContent('0 due + 10 new');
    fireEvent.change(screen.getByTestId('teacher-deck-new-per-day'), { target: { value: '3' } });
    expect(screen.getByTestId('teacher-deck-session-size')).toHaveTextContent('0 due + 3 new');
    fireEvent.change(screen.getByTestId('teacher-deck-review-cap'), { target: { value: '40' } });
    expect(storedProgress(storage).settings).toEqual({ newPerDay: 3, reviewCap: 40 });

    fireEvent.change(screen.getByTestId('teacher-deck-new-per-day'), { target: { value: '0' } });
    expect(screen.getByTestId('teacher-deck-session-size')).toHaveTextContent('0 due + 0 new');
    expect(screen.queryByTestId('teacher-deck-start')).toBeNull();
    expect(screen.getByTestId('teacher-deck-nothing-today')).toBeInTheDocument();
  });

  test('offers only card kinds that have items in this deck', async () => {
    const deck = fixtureDeck({ drillIndexes: [] });
    renderPanel(deck, memoryStorage(), { now: DAY1 });
    await screen.findByTestId('teacher-deck-modes');
    expect(screen.getByTestId('teacher-deck-kind-recognition')).toHaveTextContent('12');
    expect(screen.getByTestId('teacher-deck-kind-production')).toHaveTextContent('10');
    expect(screen.queryByTestId('teacher-deck-kind-cloze')).toBeNull();
    expect(screen.queryByTestId('teacher-deck-kind-grammar')).toBeNull();
    // Matching needs introduced words; none yet.
    expect(screen.queryByTestId('teacher-deck-matching-start')).toBeNull();
  });

  test('a missing deck file shows a load error with retry, not CEFR fallback cards', async () => {
    let attempts = 0;
    render(
      <TeacherDeckPractice
        deckId={FIXTURE_DECK_ID}
        titleUk="Приклад розробника"
        titleEn="Dev's example deck"
        config={CONFIG}
        chromeLocale="en"
        loadDeck={() => {
          attempts += 1;
          return attempts === 1 ? Promise.reject(new Error('404')) : Promise.resolve(fixtureDeck());
        }}
        storage={memoryStorage()}
        now={() => DAY1}
      />,
    );
    expect(await screen.findByTestId('teacher-deck-load-error')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Try again/ }));
    await waitFor(() => expect(screen.getByTestId('teacher-deck-start')).toBeInTheDocument());
  });
});
