import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { act, render, renderHook, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createRef } from 'react';
import ZnoPractice, { nextDueItem, type ZnoPracticeDeck, type ZnoPracticeItem, type ZnoSessionControls } from '@site/src/components/ZnoPractice';
import { SRS_STORAGE_KEY, cardKey, loadState } from '@site/src/lib/lexicon/srs';
import * as srs from '@site/src/lib/lexicon/srs';
import * as zno from '@site/src/components/ZnoPractice';
import { useZnoPracticeOverlay } from '@site/src/components/useZnoPracticeOverlay';

const decks: ZnoPracticeDeck[] = [{
  deckId: 'zno-paronym', title: 'Пароніми', thinDeck: true,
  items: [{
    znoTaskId: 'zno:7', znoMode: 'choice', taskFormat: 'single-choice', stem: 'Оберіть відповідь.',
    options: ['перша', 'друга', 'третя', 'четверта', 'п’ята'], correctLetter: 'Б', correctIndex: 1,
    year: 2021, exam: 'zno', session: 'osnovna', taskNo: 2, topicTag: 'Пароніми',
    attribution: 'Джерело: УЦОЯО · ЗНО 2021, основна сесія · завдання №2',
  }],
}];

describe('ZnoPractice', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    srs.clearLoadedSrsState();
    document.documentElement.dataset.chromeLocale = 'en';
  });

  afterEach(() => {
    delete document.documentElement.dataset.chromeLocale;
  });

  test('resume after reload restores answered and unanswered items of a frozen queue', async () => {
    const user = userEvent.setup();
    const deck = { ...decks[0], items: Array.from({ length: 3 }, (_, index) => ({
      ...decks[0].items[0], znoTaskId: `resume:${index}`, stem: `Resume task ${index}`,
    })) };
    const rate = vi.spyOn(srs, 'rateCard');
    let view = render(<ZnoPractice deck={deck} />);
    const firstStem = screen.getByText(/Resume task/).textContent;
    await user.click(screen.getByRole('button', { name: 'А перша' }));
    view.unmount();
    srs.clearLoadedSrsState();
    const loader = vi.spyOn(zno, 'loadZnoDeck').mockRejectedValueOnce(new Error('chunk unavailable')).mockResolvedValue(deck);
    vi.spyOn(console, 'error').mockImplementation(() => {});
    const overlay = renderHook(() => useZnoPracticeOverlay());
    act(() => overlay.result.current.setActiveZnoDeckId(deck.deckId));
    await waitFor(() => expect(overlay.result.current.activeZnoDeckError).toBe(true));
    act(() => overlay.result.current.retryActiveZnoDeck());
    await waitFor(() => expect(overlay.result.current.activeZnoDeck).toEqual(deck));
    expect(loader).toHaveBeenCalledTimes(2);
    overlay.unmount();
    view = render(<ZnoPractice deck={deck} />);
    expect(screen.getByText(firstStem!)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'А перша' })).toBeDisabled();
    expect(screen.getByTestId('zno-session-progress')).toHaveTextContent('1/3');
    await user.click(screen.getByRole('button', { name: 'Next task' }));
    const secondStem = screen.getByText(/Resume task/).textContent;
    expect(secondStem).not.toBe(firstStem);
    await user.click(screen.getByRole('button', { name: 'End session' }));
    view.unmount();
    view = render(<ZnoPractice deck={deck} />);
    expect(screen.getByTestId('zno-session-score')).toHaveTextContent('0/3');
    await user.click(screen.getByRole('button', { name: 'Resume unanswered items' }));
    expect(screen.getByText(secondStem!)).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Б друга' }));
    expect(rate).toHaveBeenCalledTimes(2);
    view.unmount();
    view = render(<ZnoPractice deck={{ ...deck, items: deck.items.map((item) => ({ ...item, options: ['changed', 'key', 'three'] })) }} />);
    expect(screen.getByRole('alert')).toHaveTextContent('The task content has changed');
    expect(screen.queryByTestId('zno-practice-item')).not.toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Start a new session' }));
    expect(screen.getAllByRole('button', { name: /^[АБВ] / })).toHaveLength(3);
    expect(rate).toHaveBeenCalledTimes(2);
  });

  test('a task shared by two topics is counted once in the queue and summary', async () => {
    const user = userEvent.setup();
    const shared = decks[0].items[0];
    const topics = [decks[0], { ...decks[0], deckId: 'other-topic', items: [{ ...shared, topicTag: 'Other topic' }] }];
    const deck = { ...decks[0], items: topics.flatMap((topic) => topic.items) };
    let view = render(<ZnoPractice deck={deck} />);
    expect(screen.getByTestId('zno-session-progress')).toHaveTextContent('0/1');
    await user.click(screen.getByRole('button', { name: 'Б друга' }));
    await user.click(screen.getByRole('button', { name: 'Next task' }));
    view.unmount();
    srs.clearLoadedSrsState();
    view = render(<ZnoPractice deck={deck} />);
    expect(screen.getByTestId('zno-session-score')).toHaveTextContent('1/1');
    expect(loadState().reviews.filter((review) => review.lemmaId === shared.znoTaskId)).toHaveLength(1);
    view.unmount();
  });

  test('due-only continuation serves no future card and stops at its fixed budget', async () => {
    const user = userEvent.setup();
    const items = Array.from({ length: 12 }, (_, index) => ({
      ...decks[0].items[0], znoTaskId: `bounded-due:${index}`, stem: `Due task ${index}`,
    }));
    for (const item of items) srs.rateCard(item.znoTaskId, 'choice', 'good', Date.now() - 30 * 86_400_000);
    srs.rateCard('bounded-future', 'choice', 'good');
    const deck = { ...decks[0], items: [...items, items[0],
      { ...items[0], znoTaskId: 'bounded-future', stem: 'Future task' },
      { ...items[0], znoTaskId: 'bounded-new', stem: 'New task' },
    ] };
    render(<ZnoPractice deck={deck} />);
    await user.click(screen.getByRole('button', { name: 'End session' }));
    await user.click(screen.getByRole('button', { name: 'Continue with due items' }));
    expect(screen.getByTestId('zno-session-progress')).toHaveTextContent('0/8');
    for (let index = 0; index < 8; index += 1) {
      expect(screen.queryByText('Future task')).not.toBeInTheDocument();
      expect(screen.queryByText('New task')).not.toBeInTheDocument();
      await user.click(screen.getByRole('button', { name: 'Б друга' }));
      await user.click(screen.getByRole('button', { name: 'Next task' }));
    }
    expect(screen.getByTestId('zno-session-score')).toHaveTextContent('8/8');
    expect(screen.queryByTestId('zno-practice-item')).not.toBeInTheDocument();
    expect(loadState().cards.get(cardKey('bounded-future', 'choice'))?.reps).toBe(1);
    expect(loadState().cards.has(cardKey('bounded-new', 'choice'))).toBe(false);
  });

  test('storage write failure keeps the in-memory session and shows recovery without duplicate ratings', async () => {
    const user = userEvent.setup();
    const rate = vi.spyOn(srs, 'rateCard');
    let view = render(<ZnoPractice deck={decks[0]} />);
    const write = vi.spyOn(localStorage, 'setItem').mockImplementation(() => { throw new Error('QuotaExceededError'); });
    await user.click(screen.getByRole('button', { name: 'А перша' }));
    expect(screen.getByRole('alert')).toHaveTextContent('Keep this page open');
    view.unmount();
    view = render(<ZnoPractice deck={decks[0]} />);
    expect(screen.getByRole('button', { name: 'А перша' })).toBeDisabled();
    await user.click(screen.getByRole('button', { name: 'Next task' }));
    await user.click(screen.getByRole('button', { name: 'Retry missed items once' }));
    await user.click(screen.getByRole('button', { name: 'Б друга' }));
    view.unmount();
    view = render(<ZnoPractice deck={decks[0]} />);
    expect(screen.getByRole('button', { name: 'Б друга' })).toBeDisabled();
    await user.click(screen.getByRole('button', { name: 'Next task' }));
    expect(screen.getByTestId('zno-session-score')).toHaveTextContent('0/1');
    write.mockRestore();
    await user.click(screen.getByRole('button', { name: 'Try saving again' }));
    view.unmount();
    srs.clearLoadedSrsState();
    view = render(<ZnoPractice deck={decks[0]} />);
    expect(screen.getByTestId('zno-session-score')).toHaveTextContent('0/1');
    expect(rate).toHaveBeenCalledTimes(1);
    expect(loadState().reviews.filter((review) => review.lemmaId === 'zno:7')).toHaveLength(1);
    view.unmount();

    // SRS may save while the session write fails. A true reload must not rerate.
    localStorage.clear();
    srs.clearLoadedSrsState();
    rate.mockClear();
    view = render(<ZnoPractice deck={decks[0]} />);
    const setItem = localStorage.setItem.bind(localStorage);
    const sessionWrite = vi.spyOn(localStorage, 'setItem').mockImplementation((key, value) => {
      if (key.startsWith(srs.ZNO_SESSION_STORAGE_KEY)) throw new Error('QuotaExceededError');
      setItem(key, value);
    });
    await user.click(screen.getByRole('button', { name: 'Б друга' }));
    expect(screen.getByRole('alert')).toHaveTextContent('Keep this page open');
    view.unmount();
    sessionWrite.mockRestore();
    srs.clearLoadedSrsState();
    view = render(<ZnoPractice deck={decks[0]} />);
    expect(screen.getByRole('alert')).toHaveTextContent('Some answers could not be saved');
    await user.click(screen.getByRole('button', { name: 'Б друга' }));
    await user.click(screen.getByRole('button', { name: 'Next task' }));
    expect(screen.getByTestId('zno-session-score')).toHaveTextContent('1/1');
    expect(rate).toHaveBeenCalledTimes(1);
    expect(loadState().reviews.filter((review) => review.lemmaId === 'zno:7')).toHaveLength(1);
    view.unmount();

    // Blocked reads use SRS's memory store and must flush ratings on recovery.
    localStorage.clear();
    srs.clearLoadedSrsState();
    rate.mockClear();
    const read = vi.spyOn(localStorage, 'getItem').mockImplementation(() => { throw new Error('SecurityError'); });
    view = render(<ZnoPractice deck={decks[0]} />);
    expect(screen.getByRole('alert')).toHaveTextContent('Keep this page open');
    await user.click(screen.getByRole('button', { name: 'Б друга' }));
    await user.click(screen.getByRole('button', { name: 'Next task' }));
    read.mockRestore();
    await user.click(screen.getByRole('button', { name: 'Try saving again' }));
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    view.unmount();
    srs.clearLoadedSrsState();
    render(<ZnoPractice deck={decks[0]} />);
    expect(screen.getByTestId('zno-session-score')).toHaveTextContent('1/1');
    expect(rate).toHaveBeenCalledTimes(1);
    expect(loadState().reviews.filter((review) => review.lemmaId === 'zno:7')).toHaveLength(1);
  });

  test('uses Ukrainian chrome for the picker and summary labels', async () => {
    document.documentElement.dataset.chromeLocale = 'uk';
    const user = userEvent.setup();
    render(<ZnoPractice decks={decks} />);
    expect(screen.getByRole('region', { name: 'Практика ЗНО та НМТ' })).toBeInTheDocument();
    expect(screen.getByText('Невелика добірка', { exact: false })).toBeInTheDocument();
    await user.click(screen.getByTestId('zno-deck-zno-paronym'));
    await user.click(screen.getByRole('button', { name: 'А перша' }));
    await user.click(screen.getByRole('button', { name: 'Наступне завдання' }));

    const summary = within(screen.getByTestId('zno-session-summary'));
    expect(summary.getByRole('heading', { name: 'Сесію завершено' })).toBeInTheDocument();
    expect(summary.getByText('Результат перших спроб')).toBeInTheDocument();
    expect(summary.getByText('Без відповіді')).toBeInTheDocument();
    expect(summary.getByRole('heading', { name: 'Помилки за темами' })).toBeInTheDocument();
    expect(summary.getByRole('button', { name: 'Переглянути помилки' })).toBeInTheDocument();
    expect(summary.getByRole('button', { name: 'Повторити помилки один раз' })).toBeInTheDocument();
    expect(summary.getByRole('button', { name: 'Вийти' })).toBeInTheDocument();
    const nextDue = screen.getByTestId('zno-session-summary').querySelector('time');
    expect(nextDue).not.toBeNull();
    expect(nextDue).toHaveTextContent(new Date(nextDue!.dateTime).toLocaleString('uk-UA'));
  });

  test('Home exits when the session summary is already showing', async () => {
    const user = userEvent.setup();
    const onBackToDecks = vi.fn();
    const controlsRef = createRef<ZnoSessionControls>();
    render(<>
      <button type="button" onClick={() => controlsRef.current?.endSession()}>Home</button>
      <ZnoPractice deck={decks[0]} onBackToDecks={onBackToDecks} sessionControlsRef={controlsRef} />
    </>);

    await user.click(screen.getByRole('button', { name: 'Home' }));
    expect(screen.getByTestId('zno-session-summary')).toBeInTheDocument();
    expect(onBackToDecks).not.toHaveBeenCalled();
    await user.click(screen.getByRole('button', { name: 'Home' }));
    expect(onBackToDecks).toHaveBeenCalledOnce();
  });

  test('shows the required thin-deck treatment and learner-facing attribution', async () => {
    const user = userEvent.setup();
    render(<ZnoPractice decks={decks} />);
    await user.click(screen.getByTestId('zno-deck-zno-paronym'));
    expect(screen.getByText('Small collection: 1')).toBeInTheDocument();
    expect(screen.getByText('Джерело: УЦОЯО · ЗНО 2021, основна сесія · завдання №2')).toBeInTheDocument();
    expect(screen.queryByText(/osvita\.ua/)).not.toBeInTheDocument();
  });

  test('grades by letter index and persists an item-keyed SRS card', async () => {
    const user = userEvent.setup();
    render(<ZnoPractice decks={decks} />);
    await user.click(screen.getByTestId('zno-deck-zno-paronym'));
    const correctOption = screen.getByRole('button', { name: 'Б друга' });
    await user.click(correctOption);
    expect(screen.getByTestId('zno-practice-verdict')).toHaveTextContent('✓ Correct');
    expect(screen.getByTestId('zno-practice-verdict')).toHaveClass('correct');
    expect(correctOption).toHaveAttribute('data-selected', 'true');
    expect(correctOption).toHaveAttribute('data-correct', 'true');
    expect(correctOption).toHaveClass('selected', 'correct');
    expect(localStorage.getItem(SRS_STORAGE_KEY)).not.toBeNull();
    expect(loadState().cards.has(cardKey('zno:7', 'choice'))).toBe(true);
  });

  test('marks the learner\'s wrong pick red and the correct option green', async () => {
    const user = userEvent.setup();
    render(<ZnoPractice decks={decks} />);
    await user.click(screen.getByTestId('zno-deck-zno-paronym'));
    const wrongOption = screen.getByRole('button', { name: 'А перша' });
    const correctOption = screen.getByRole('button', { name: 'Б друга' });
    await user.click(wrongOption);

    expect(screen.getByTestId('zno-practice-verdict')).toHaveTextContent('✗ Correct answer: Б');
    expect(screen.getByTestId('zno-practice-verdict')).toHaveClass('wrong');

    expect(wrongOption).toHaveAttribute('data-selected', 'true');
    expect(wrongOption).toHaveAttribute('data-wrong', 'true');
    expect(wrongOption).not.toHaveAttribute('data-correct');
    expect(wrongOption).toHaveClass('selected', 'wrong');

    expect(correctOption).toHaveAttribute('data-correct', 'true');
    expect(correctOption).not.toHaveAttribute('data-selected');
    expect(correctOption).toHaveClass('correct');
    expect(correctOption).not.toHaveClass('selected', 'wrong');
  });

  test('renders a distinct passage card for multi-line reading-comprehension stems', async () => {
    const passageDecks: ZnoPracticeDeck[] = [{
      deckId: 'zno-orthography', title: 'Орфографія', thinDeck: false,
      items: [{
        znoTaskId: 'zno:9', znoMode: 'choice', taskFormat: 'single-choice',
        stem: 'Прочитайте текст і виконайте завдання\n(1) Усе починається з дитинства.\nОкремо в цьому тексті пишуться слова',
        options: ['перша', 'друга', 'третя', 'четверта'], correctLetter: 'А', correctIndex: 0,
        year: 2022, exam: 'nmt', session: 'sesiya-1', taskNo: 5, topicTag: 'Орфографія',
        attribution: 'Джерело: УЦОЯО · НМТ 2022, сесія 1 · завдання №5',
      }],
    }];
    const user = userEvent.setup();
    render(<ZnoPractice decks={passageDecks} />);
    await user.click(screen.getByTestId('zno-deck-zno-orthography'));
    expect(screen.getByText('Прочитайте текст і виконайте завдання')).toBeInTheDocument();
    const passage = screen.getByText(/Усе починається з дитинства/);
    expect(passage).toHaveClass('zno-practice-passage');
  });

  test('renders underlined letter marks when optionMarks are present', async () => {
    const phoneticsDeck: ZnoPracticeDeck[] = [{
      deckId: 'zno-phonetics', title: 'Фонетика', thinDeck: false,
      items: [{
        znoTaskId: 'zno:457', znoMode: 'choice', taskFormat: 'single-choice',
        stem: 'Однаковий звук позначають букви, виділені в кожному слові рядка',
        options: ['бігти, поріг, злегка', 'повість, сяйво, свічка', 'лічба, почасти, чітко', 'кістці, тім\'я, житній'],
        optionMarks: [
          [{ start: 2, end: 3, style: 'underline' }],
          [{ start: 4, end: 5, style: 'underline' }],
          [{ start: 2, end: 3, style: 'underline' }],
          [{ start: 3, end: 4, style: 'underline' }],
        ],
        correctLetter: 'Б', correctIndex: 1,
        year: 2024, exam: 'nmt', session: 'sesiya-2', taskNo: 1, topicTag: 'Фонетика',
        attribution: 'Джерело: УЦОЯО · НМТ 2024, сесія 2 · завдання №1',
      }],
    }];
    const user = userEvent.setup();
    render(<ZnoPractice decks={phoneticsDeck} />);
    await user.click(screen.getByTestId('zno-deck-zno-phonetics'));
    expect(document.querySelector('.zno-practice-mark-underline')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /повість, сяйво, свічка/ })).toBeInTheDocument();
  });

  test('renders a hub-controlled deck without the standalone picker and returns through its callback', async () => {
    const user = userEvent.setup();
    const onBackToDecks = vi.fn();
    const controlsRef = createRef<ZnoSessionControls>();
    render(<>
      <button type="button" onClick={() => controlsRef.current?.endSession()}>Leave hub</button>
      <ZnoPractice deck={decks[0]} onBackToDecks={onBackToDecks} sessionControlsRef={controlsRef} />
    </>);

    expect(screen.queryByRole('heading', { name: 'ЗНО / НМТ' })).not.toBeInTheDocument();
    expect(screen.getByTestId('zno-practice-item')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Leave hub' }));
    expect(screen.getByTestId('zno-session-summary')).toHaveTextContent('Unanswered1');
    expect(screen.getByTestId('zno-session-unanswered')).toHaveTextContent('Оберіть відповідь.');
    expect(onBackToDecks).not.toHaveBeenCalled();
    await user.click(screen.getByRole('button', { name: 'Exit' }));
    expect(onBackToDecks).toHaveBeenCalledOnce();
  });

  test.each([0, 1, 3])('%i-item sessions stop explicitly instead of silently resetting', async (count) => {
    const user = userEvent.setup();
    const deck = {
      ...decks[0],
      items: Array.from({ length: count }, (_, index) => ({ ...decks[0].items[0], znoTaskId: `zno:${index}` })),
    };
    render(<ZnoPractice deck={deck} />);
    for (let index = 0; index < count; index += 1) {
      expect(screen.getByTestId('zno-session-progress')).toHaveTextContent(`${index}/${count}`);
      await user.click(screen.getByRole('button', { name: 'Б друга' }));
      await user.click(screen.getByRole('button', { name: 'Next task' }));
    }
    expect(screen.getByRole('heading', { name: 'Session complete' })).toBeInTheDocument();
    expect(screen.getByTestId('zno-session-score')).toHaveTextContent(`${count}/${count}`);
    expect(screen.queryByTestId('zno-practice-item')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Continue with due items' })).not.toBeInTheDocument();
  });

  test('retry preserves a literal 2/3 first-attempt score and never rates retry or review', async () => {
    const user = userEvent.setup();
    const rate = vi.spyOn(srs, 'rateCard');
    const deck = {
      ...decks[0],
      items: Array.from({ length: 3 }, (_, index) => ({ ...decks[0].items[0], znoTaskId: `zno:${index}` })),
    };
    render(<ZnoPractice deck={deck} />);
    for (const option of ['Б друга', 'Б друга', 'А перша']) {
      await user.click(screen.getByRole('button', { name: option }));
      await user.click(screen.getByRole('button', { name: 'Next task' }));
    }
    expect(screen.getByTestId('zno-session-score')).toHaveTextContent('2/3');
    expect(screen.getByTestId('zno-session-topic-errors')).toHaveTextContent('Пароніми: 1');
    expect(rate).toHaveBeenCalledTimes(3);
    const history = localStorage.getItem(SRS_STORAGE_KEY);
    await user.click(screen.getByRole('button', { name: 'Review errors' }));
    expect(screen.getByRole('button', { name: 'Б друга' })).toBeDisabled();
    await user.click(screen.getByRole('button', { name: 'Next task' }));
    await user.click(screen.getByRole('button', { name: 'Retry missed items once' }));
    await user.click(screen.getByRole('button', { name: 'Б друга' }));
    await user.click(screen.getByRole('button', { name: 'Next task' }));
    expect(screen.getByTestId('zno-session-score')).toHaveTextContent('2/3');
    expect(screen.queryByRole('button', { name: 'Retry missed items once' })).not.toBeInTheDocument();
    expect(rate).toHaveBeenCalledTimes(3);
    expect(localStorage.getItem(SRS_STORAGE_KEY)).toBe(history);
  });

  test('exhaustion never refills from duplicates or future cards and bounds new items', async () => {
    const user = userEvent.setup();
    srs.rateCard('future', 'choice', 'good');
    srs.rateCard('due', 'choice', 'good', Date.now() - 30 * 86_400_000);
    const due = { ...decks[0].items[0], znoTaskId: 'due', stem: 'Due task' };
    const deck = {
      ...decks[0],
      items: [due, due, { ...due, znoTaskId: 'future', stem: 'Future task' },
        ...Array.from({ length: 10 }, (_, index) => ({ ...due, znoTaskId: `new:${index}`, stem: `New task ${index}` }))],
    };
    render(<ZnoPractice deck={deck} />);
    expect(screen.getByText('Due task')).toBeInTheDocument();
    for (let index = 0; index < 9; index += 1) {
      expect(screen.getByTestId('zno-session-progress')).toHaveTextContent(`${index}/9`);
      expect(screen.queryByText('Future task')).not.toBeInTheDocument();
      await user.click(screen.getByRole('button', { name: 'Б друга' }));
      if (index === 0) {
        // A card becoming due mid-session cannot change the frozen denominator.
        const state = loadState();
        const futureCard = state.cards.get(cardKey('future', 'choice'));
        if (!futureCard) throw new Error('Expected the scheduled fixture card');
        state.cards.set(cardKey('future', 'choice'), { ...futureCard, due: Date.now() - 1 });
        srs.saveState(state);
      }
      await user.click(screen.getByRole('button', { name: 'Next task' }));
    }
    expect(screen.getByTestId('zno-session-score')).toHaveTextContent('9/9');
    expect(screen.queryByTestId('zno-practice-item')).not.toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Continue with due items' }));
    expect(screen.getByText('Future task')).toBeInTheDocument();
    expect(screen.getByTestId('zno-session-progress')).toHaveTextContent('0/1');
    await user.click(screen.getByRole('button', { name: 'End session' }));
    expect(within(screen.getByTestId('zno-session-unanswered')).getByText('Future task')).toBeInTheDocument();
  });

  test('nextDueItem randomizes task order across seeds and respects excludedIds', () => {
    const multiItems: ZnoPracticeItem[] = Array.from({ length: 10 }, (_, i) => ({
      znoTaskId: `zno:task_${i}`,
      znoMode: 'choice',
      taskFormat: 'single-choice',
      stem: `Завдання ${i}`,
      options: ['А', 'Б', 'В', 'Г'],
      correctLetter: 'А',
      correctIndex: 0,
      year: 2023,
      exam: 'zno',
      session: 'osnovna',
      taskNo: i + 1,
      topicTag: 'Лексика',
      attribution: 'Джерело: УЦОЯО',
    }));

    const firstPicks = new Set<string>();
    for (let s = 1; s <= 10; s += 1) {
      const item = nextDueItem(multiItems, null, s * 7919);
      if (item) firstPicks.add(item.znoTaskId);
    }
    // Across 10 different seeds, at least 3 distinct first items must be picked
    expect(firstPicks.size).toBeGreaterThanOrEqual(3);

    // excludedIds filtering prevents repeating recently seen items
    const excluded = new Set(['zno:task_0', 'zno:task_1', 'zno:task_2']);
    const pickWithExclusion = nextDueItem(multiItems, null, 12345, excluded);
    expect(excluded.has(pickWithExclusion!.znoTaskId)).toBe(false);
  });
});
