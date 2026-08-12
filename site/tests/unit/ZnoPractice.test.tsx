import { beforeEach, describe, expect, test, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ZnoPractice, { type ZnoPracticeDeck } from '@site/src/components/ZnoPractice';
import { SRS_STORAGE_KEY, cardKey, loadState } from '@site/src/lib/lexicon/srs';

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
  beforeEach(() => localStorage.clear());

  test('shows the required thin-deck treatment and learner-facing attribution', async () => {
    const user = userEvent.setup();
    render(<ZnoPractice decks={decks} />);
    await user.click(screen.getByTestId('zno-deck-zno-paronym'));
    expect(screen.getByText('Невелика добірка: 1 завдання.')).toBeInTheDocument();
    expect(screen.getByText('Джерело: УЦОЯО · ЗНО 2021, основна сесія · завдання №2')).toBeInTheDocument();
    expect(screen.queryByText(/osvita\.ua/)).not.toBeInTheDocument();
  });

  test('grades by letter index and persists an item-keyed SRS card', async () => {
    const user = userEvent.setup();
    render(<ZnoPractice decks={decks} />);
    await user.click(screen.getByTestId('zno-deck-zno-paronym'));
    const correctOption = screen.getByRole('button', { name: 'Б друга' });
    await user.click(correctOption);
    expect(screen.getByTestId('zno-practice-verdict')).toHaveTextContent('✓ Правильно');
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

    expect(screen.getByTestId('zno-practice-verdict')).toHaveTextContent('✗ Правильна відповідь: Б');
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
    render(<ZnoPractice deck={decks[0]} onBackToDecks={onBackToDecks} />);

    expect(screen.queryByRole('heading', { name: 'ЗНО / НМТ' })).not.toBeInTheDocument();
    expect(screen.getByTestId('zno-practice-item')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'До колод' }));
    expect(onBackToDecks).toHaveBeenCalledOnce();
  });
});
