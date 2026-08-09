import { beforeEach, describe, expect, test } from 'vitest';
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
    await user.click(screen.getByRole('button', { name: 'Б. друга' }));
    expect(screen.getByTestId('zno-practice-verdict')).toHaveTextContent('✓ Правильно');
    expect(localStorage.getItem(SRS_STORAGE_KEY)).not.toBeNull();
    expect(loadState().cards.has(cardKey('zno:7', 'choice'))).toBe(true);
  });
});
