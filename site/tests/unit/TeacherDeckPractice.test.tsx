import { afterEach, describe, expect, test } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { State } from 'ts-fsrs';
import TeacherDeckPractice from '@site/src/components/practice/TeacherDeckPractice';
import { buildTeacherDeck, type TeacherDeck, type TeacherGrammarItem } from '@site/src/lib/lexicon/teacher-deck';
import { teacherOptionDisplay } from '@site/src/lib/lexicon/teacher-deck-options';
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

function dueReview(storage: StorageLike, kind: 'recognition' | 'production' | 'cloze' | 'grammar', reps = 1) {
  const id = fixtureEntryId(0);
  const progress = emptyDeckProgress(FIXTURE_DECK_ID, { newPerDay: 0, reviewCap: 100 });
  const card = {
    due: DAY1, stability: 1, difficulty: 5, elapsed_days: 1, scheduled_days: 1,
    learning_steps: 0, reps, lapses: 0, state: State.Review, last_review: DAY1 - 86400000,
  };
  progress.introduced[id] = { day: '2026-09-26', at: DAY1 - 86400000, source: 'practice' };
  progress.cards[`${id}:recognition`] = { ...card, due: kind === 'recognition' ? DAY1 : DAY2 + 86400000 };
  if (kind !== 'recognition') progress.cards[`${id}:${kind}`] = card;
  progress.migration = { at: DAY1, entries: 0, recognitionStates: 0 };
  writeDeckProgress(storage, progress);
}

function shownOptions(testId: string): string[] {
  return Array.from(screen.getByTestId(testId).querySelectorAll('.mc-opt span[lang]'), (node) => node.textContent ?? '');
}

function expectPlainOptions(labels: string[]) {
  expect(labels).toHaveLength(4);
  expect(new Set(labels).size).toBe(4);
  expect(labels.every((label) => label === label.toLocaleLowerCase() && !/[.!?;:,\u0301]$/u.test(label))).toBe(true);
}

afterEach(() => cleanup());

describe('TeacherDeckPractice', () => {
  test('English source prefixes and aspect tags do not mark a choice', () => {
    expect(teacherOptionDisplay('To wipe (impf.)', 'en')).toBe('wipe');
    expect(teacherOptionDisplay('TO clean (perf.)!', 'en')).toBe('clean');
    expect(teacherOptionDisplay('Location / Whereabouts', 'en')).toBe('location');
    expect(teacherOptionDisplay('Father-in-law (wife’s father)', 'en')).toBe('father-in-law');
  });

  test('stress answer stays out of the accessible label until the learner selects', async () => {
    const deck = fixtureDeck();
    const storage = memoryStorage();
    dueReview(storage, 'grammar', 0);
    renderPanel(deck, storage, { now: DAY1 });
    fireEvent.click(await screen.findByTestId('teacher-deck-start'));
    const word = screen.getByTestId('practice-stress').querySelector('.practice-stress-word')!;
    expect(word.getAttribute('aria-label')).toBe('справедливий');
    expect(word.querySelectorAll('.stress-vowel')).toHaveLength(4);
    fireEvent.click(word.querySelector('[data-position="8"]')!);
    expect(word.getAttribute('aria-label')).toBe('справедли́вий');
  });

  test('recognition renders the тісний mixed-source glosses without an answer-shape cue', async () => {
    const deck = fixtureDeck();
    const entry = deck.entries[0]!;
    entry.uk = 'Тісний';
    entry.en = 'tight-fitting, cramped';
    entry.cards.recognition.choice!.prompt = entry.uk;
    entry.cards.recognition.choice!.options = [
      { entryId: fixtureEntryId(1), label: 'Mysterious', kind: 'distractor' },
      { entryId: fixtureEntryId(2), label: 'Countless.', kind: 'distractor' },
      { entryId: entry.entryId, label: entry.en, kind: 'answer' },
      { entryId: fixtureEntryId(3), label: 'Exhausted!', kind: 'distractor' },
    ];
    const storage = memoryStorage();
    dueReview(storage, 'recognition');
    renderPanel(deck, storage, { now: DAY1 });
    fireEvent.click(await screen.findByTestId('teacher-deck-start'));
    expect(shownOptions('teacher-deck-recognition-choice')).toEqual(['mysterious', 'countless', 'tight-fitting', 'exhausted']);
    fireEvent.click(within(screen.getByTestId('teacher-deck-recognition-choice')).getByRole('button', { name: /tight-fitting/ }));
    expect(screen.getByTestId('teacher-deck-feedback')).toHaveTextContent('tight-fitting, cramped');
    expect(entry.cards.recognition.choice!.options[2]!.label).toBe('tight-fitting, cramped');
  });

  test('a choice that would have identical display labels uses a flashcard', async () => {
    const deck = fixtureDeck();
    deck.entries[0]!.cards.recognition.choice!.options[0]!.label = 'Fair, just';
    deck.entries[0]!.cards.recognition.choice!.options[1]!.label = 'FAIR; equitable';
    const storage = memoryStorage();
    dueReview(storage, 'recognition');
    renderPanel(deck, storage, { now: DAY1 });
    fireEvent.click(await screen.findByTestId('teacher-deck-start'));
    expect(screen.queryByTestId('teacher-deck-recognition-choice')).toBeNull();
    expect(screen.getByRole('button', { name: /Справедливий/ })).toBeInTheDocument();
  });

  test('production choice shows uniform Ukrainian case, punctuation, and stress shape', async () => {
    const deck = fixtureDeck();
    deck.entries[0]!.cards.production!.choice!.options = [
      { entryId: fixtureEntryId(0), label: 'Справедли́вий.', kind: 'answer' },
      { entryId: fixtureEntryId(1), label: 'Витирати', kind: 'distractor' },
      { entryId: fixtureEntryId(2), label: 'витерти!', kind: 'distractor' },
      { entryId: fixtureEntryId(5), label: 'Таємно,', kind: 'distractor' },
    ];
    const storage = memoryStorage();
    dueReview(storage, 'production');
    renderPanel(deck, storage, { now: DAY1 });
    fireEvent.click(await screen.findByTestId('teacher-deck-start'));
    const labels = shownOptions('teacher-deck-production-choice');
    expectPlainOptions(labels);
    expect(labels).toEqual(['справедливий', 'витирати', 'витерти', 'таємно']);
    expect(deck.entries[0]!.cards.production!.choice!.options[0]!.label).toBe('Справедли́вий.');
  });

  test('cloze renders mixed-source forms with the same visible shape', async () => {
    const deck = fixtureDeck();
    const item = deck.clozeById.get(`${fixtureEntryId(0)}:cloze:0`)!;
    item.options[0]!.label = 'Справедли́вими.';
    item.options[1]!.label = 'Низькими!';
    item.options[2]!.label = 'прихованими,';
    const storage = memoryStorage();
    dueReview(storage, 'cloze', 0);
    renderPanel(deck, storage, { now: DAY1 });
    fireEvent.click(await screen.findByTestId('teacher-deck-start'));
    expectPlainOptions(shownOptions('teacher-deck-cloze'));
    expect(shownOptions('teacher-deck-cloze')).toEqual(['справедливими', 'низькими', 'прихованими', 'розкішними']);
  });

  test('grammar classify renders mixed-source labels uniformly', async () => {
    const deck = fixtureDeck();
    const item = deck.grammarById.get(`${fixtureEntryId(0)}:classify`)!.item;
    if (!('sets' in item)) throw new Error('expected classify fixture');
    item.sets[0]!.options[0]!.labelUk = 'Іменник.';
    item.sets[0]!.options[1]!.labelUk = 'При́кметник!';
    const storage = memoryStorage();
    dueReview(storage, 'grammar', 1);
    renderPanel(deck, storage, { now: DAY1 });
    fireEvent.click(await screen.findByTestId('teacher-deck-start'));
    const labels = shownOptions('teacher-deck-grammar-classify');
    expect(labels).toEqual(['іменник', 'прикметник', 'дієслово']);
  });

  test('grammar paradigm renders mixed-source forms uniformly', async () => {
    const deck = fixtureDeck();
    const id = `${fixtureEntryId(0)}:paradigm`;
    (deck.grammarById as Map<string, TeacherGrammarItem>).set(id, { mode: 'paradigm', item: {
      paradigmId: id, entryId: fixtureEntryId(0), cardId: `${fixtureEntryId(0)}:grammar`,
      lemmaId: 'справедливий', lemma: 'справедливий',
      slot: { case: 'nominative', number: 'singular', labelUk: 'форма' }, form: 'справедливий',
      options: [
        { label: 'Справедли́вий.', kind: 'answer' }, { label: 'Низький!', kind: 'same-paradigm' },
        { label: 'прихований,', kind: 'same-paradigm' }, { label: 'розкішний', kind: 'same-paradigm' },
      ],
    } });
    deck.entries[0]!.cards.grammar!.items.push({ mode: 'paradigm', id });
    const storage = memoryStorage();
    dueReview(storage, 'grammar', 2);
    renderPanel(deck, storage, { now: DAY1 });
    fireEvent.click(await screen.findByTestId('teacher-deck-start'));
    expect(shownOptions('teacher-deck-grammar-paradigm')).toEqual(['справедливий', 'низький', 'прихований', 'розкішний']);
  });

  test.each(['synonym', 'antonym'] as const)('grammar %s renders mixed-source options uniformly', async (mode) => {
    const deck = fixtureDeck();
    const id = `${fixtureEntryId(0)}:${mode}`;
    (deck.grammarById as Map<string, TeacherGrammarItem>).set(id, { mode, item: {
      synonymId: id, entryId: fixtureEntryId(0), cardId: `${fixtureEntryId(0)}:grammar`,
      lemmaId: 'справедливий', targetLemmaId: 'x', polarity: mode,
      prompt: 'справедливий', answer: 'чесний', source: 'fixture',
      options: [
        { label: 'Че́сний.', lemmaId: 'a', kind: 'answer' },
        { label: 'низький!', lemmaId: 'b', kind: 'distractor' },
        { label: 'Розкішний,', lemmaId: 'c', kind: 'distractor' },
        { label: 'прихований', lemmaId: 'd', kind: 'distractor' },
      ],
    } });
    deck.entries[0]!.cards.grammar!.items.push({ mode, id });
    const storage = memoryStorage();
    dueReview(storage, 'grammar', 2);
    renderPanel(deck, storage, { now: DAY1 });
    fireEvent.click(await screen.findByTestId('teacher-deck-start'));
    expect(shownOptions(`teacher-deck-grammar-${mode}`)).toEqual(['чесний', 'низький', 'розкішний', 'прихований']);
  });
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
    expect(document.activeElement).toBe(within(stage).getByTestId('teacher-deck-rate-again'));
    fireEvent.keyDown(window, { key: '3' });

    const saved = storedProgress(storage);
    expect(saved.cards[`${id}:production`]!.reps).toBe(1);
    expect(saved.cards[`${id}:recognition`]).toEqual(recognition);
    expect(saved.reviews.map((review) => review.cardId)).toEqual([`${id}:production`]);
  });

  test('focus follows keyboard practice from a choice answer to Next and the next item', async () => {
    const deck = fixtureDeck({ drillIndexes: [] });
    const storage = memoryStorage();
    const id = fixtureEntryId(0);
    const progress = emptyDeckProgress(FIXTURE_DECK_ID, { newPerDay: 1, reviewCap: 100 });
    progress.introduced[id] = { day: '2026-09-26', at: DAY1 - 86400000, source: 'practice' };
    progress.cards[`${id}:recognition`] = {
      due: DAY1,
      stability: 1,
      difficulty: 5,
      elapsed_days: 1,
      scheduled_days: 1,
      learning_steps: 0,
      reps: 1,
      lapses: 0,
      state: State.Review,
      last_review: DAY1 - 86400000,
    };
    progress.migration = { at: DAY1, entries: 0, recognitionStates: 0 };
    writeDeckProgress(storage, progress);
    renderPanel(deck, storage, { now: DAY1 });
    const user = userEvent.setup();

    const start = await screen.findByTestId('teacher-deck-start');
    start.focus();
    await user.keyboard('{Enter}');
    expect(document.activeElement).toBe(within(screen.getByTestId('teacher-deck-session')).getByRole('heading'));
    const choice = screen.getByTestId('teacher-deck-recognition-choice');
    const option = within(choice).getAllByRole('button')[0]!;
    option.focus();
    await user.keyboard('{Enter}');
    const next = screen.getByTestId('teacher-deck-next');
    expect(document.activeElement).toBe(next);
    await user.tab({ shift: true });
    await user.tab();
    expect(document.activeElement).toBe(next);
    await user.keyboard('{Enter}');
    expect(screen.queryByTestId('teacher-deck-next')).toBeNull();
    expect(document.activeElement).toBe(within(screen.getByTestId('teacher-deck-session')).getByRole('heading'));
  });

  test('production rating digits ignore the attempt input and work after reveal', async () => {
    const deck = fixtureDeck();
    const storage = memoryStorage();
    const id = fixtureEntryId(0);
    const progress = emptyDeckProgress(FIXTURE_DECK_ID, { newPerDay: 0, reviewCap: 100 });
    progress.introduced[id] = { day: '2026-09-27', at: DAY1, source: 'practice' };
    progress.cards[`${id}:recognition`] = {
      due: DAY2 + 10 * 86400000,
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
    progress.cards[`${id}:production`] = {
      due: DAY1,
      stability: 0,
      difficulty: 0,
      elapsed_days: 0,
      scheduled_days: 0,
      learning_steps: 0,
      reps: 0,
      lapses: 0,
      state: State.New,
    };
    progress.migration = { at: DAY1, entries: 0, recognitionStates: 0 };
    writeDeckProgress(storage, progress);
    renderPanel(deck, storage, { now: DAY1 });
    fireEvent.click(await screen.findByTestId('teacher-deck-start'));
    const input = screen.getByTestId('teacher-deck-attempt');
    input.focus();
    fireEvent.keyDown(input, { key: '3' });
    expect(storedProgress(storage).reviews).toHaveLength(0);
    fireEvent.change(input, { target: { value: 'справедливий' } });
    fireEvent.click(screen.getByTestId('teacher-deck-reveal'));
    fireEvent.keyDown(window, { key: '3' });
    expect(storedProgress(storage).reviews[0]).toMatchObject({ cardId: `${id}:production`, rating: 'good' });
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

  test('settings changes preserve reviews saved by another tab', async () => {
    const deck = fixtureDeck();
    const storage = memoryStorage();
    renderPanel(deck, storage, { now: DAY1 });
    await screen.findByTestId('teacher-deck-new-per-day');
    const fromOtherTab = storedProgress(storage);
    fromOtherTab.reviews.push({
      reviewId: 'other-tab', cardId: `${fixtureEntryId(0)}:recognition`, entryId: fixtureEntryId(0),
      kind: 'recognition', origin: 'review', rating: 'good', at: DAY1, day: '2026-09-27',
      presentation: 'recognition-flashcard',
    });
    writeDeckProgress(storage, fromOtherTab);
    fireEvent.change(screen.getByTestId('teacher-deck-new-per-day'), { target: { value: '3' } });
    expect(storedProgress(storage).reviews).toEqual(fromOtherTab.reviews);
    expect(storedProgress(storage).settings.newPerDay).toBe(3);
  });

  test('a refused storage write warns while keeping settings usable in memory', async () => {
    const deck = fixtureDeck();
    const storage = memoryStorage();
    const failingStorage: StorageLike = {
      getItem: storage.getItem,
      removeItem: storage.removeItem,
      setItem: () => { throw new Error('quota'); },
    };
    renderPanel(deck, failingStorage, { now: DAY1 });
    expect(await screen.findByTestId('teacher-deck-storage-warning')).toHaveTextContent('Progress is not being saved');
    fireEvent.change(screen.getByTestId('teacher-deck-new-per-day'), { target: { value: '3' } });
    expect(screen.getByTestId('teacher-deck-new-per-day')).toHaveValue(3);
    expect(screen.getByTestId('teacher-deck-session-size')).toHaveTextContent('0 due + 3 new');
  });

  test('matching uses introduced words without writing reviews and keeps focus on the new stage', async () => {
    const deck = fixtureDeck();
    deck.entries[0]!.en = 'Fair, just.';
    deck.entries[5]!.en = 'SECRETLY!';
    deck.entries[6]!.en = 'Quarter; fourth';
    const storage = memoryStorage();
    const progress = emptyDeckProgress(FIXTURE_DECK_ID, { newPerDay: 0, reviewCap: 100 });
    for (const index of [0, 5, 6]) {
      progress.introduced[fixtureEntryId(index)] = { day: '2026-09-26', at: DAY1 - 86400000, source: 'practice' };
    }
    progress.migration = { at: DAY1, entries: 0, recognitionStates: 0 };
    writeDeckProgress(storage, progress);
    renderPanel(deck, storage, { now: DAY1 });
    fireEvent.click(await screen.findByTestId('teacher-deck-matching-start'));
    const stage = screen.getByTestId('teacher-deck-matching');
    const rightLabels = Array.from(stage.querySelectorAll('[data-activity="match-right-tile"]'), (node) => node.textContent ?? '');
    expect(rightLabels.sort()).toEqual(['fair', 'quarter', 'secretly']);
    expect(document.activeElement).toBe(within(stage).getByRole('heading', { name: /Matching/ }));
    for (const left of within(stage).getAllByRole('button').filter((button) => button.matches('[data-activity="match-left-tile"]'))) {
      const index = left.getAttribute('data-original-index');
      fireEvent.click(left);
      fireEvent.click(stage.querySelector(`[data-activity="match-right-tile"][data-original-index="${index}"]`)!);
    }
    expect(screen.getByTestId('teacher-deck-matching-again')).toBeInTheDocument();
    expect(document.activeElement).toBe(screen.getByTestId('teacher-deck-matching-again'));
    expect(storedProgress(storage).reviews).toHaveLength(0);
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
