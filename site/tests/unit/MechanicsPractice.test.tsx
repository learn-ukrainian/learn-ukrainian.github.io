import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MechanicsPractice from '../../src/components/practice/MechanicsPractice';
import type { NormalizedMechanicsCard, MechanicsDeckMeta } from '../../src/lib/lexicon/mechanics-deck-loader';

const mockMeta: MechanicsDeckMeta = {
  pos: 'noun',
  titleUk: 'Іменник',
  titleEn: 'Noun',
  descriptionUk: 'Закінчення -а/-у в родовому, кличний відмінок',
  descriptionEn: 'Genitive -а/-у endings, vocative case',
  itemCount: 2,
  accent: 'purple',
};

const mockCards: NormalizedMechanicsCard[] = [
  {
    id: 'test_noun_1',
    pos: 'noun',
    category: 'noun_genitive_ending',
    cefrLevel: 'A2',
    prompt: 'Я вийшов з ___ вранці.',
    options: ['будинку', 'будинка', 'будинком', 'будинкові'],
    correctAnswer: 'будинку',
    ruleCitation: '§ 82, п. 2',
    ruleSummary: {
      uk: 'Назви будівель, споруд та приміщень мають закінчення -у/-ю',
      en: 'Buildings, structures, and premises take -у/-ю ending',
    },
    evaluate: (opt) => ({
      isCorrect: opt === 'будинку',
      feedback:
        opt === 'будинку'
          ? 'Правильно! Назви споруд та будівель у Р. в. мають закінчення -у.'
          : 'Помилка. Для назв будівель і споруд у Р. в. закінчення -у, а не -а.',
      ruleCitation: '§ 82, п. 2',
      ruleSummary: 'Назви будівель, споруд та приміщень мають закінчення -у/-ю',
    }),
  },
  {
    id: 'test_noun_2',
    pos: 'noun',
    category: 'noun_vocative_case',
    cefrLevel: 'B1',
    prompt: 'Шановний ___, раді вітати вас!',
    options: ['колего', 'колегу', 'колега', 'колегом'],
    correctAnswer: 'колего',
    ruleCitation: '§ 87, п. 1',
    ruleSummary: {
      uk: 'Іменники I відміни твердої групи у кличному відмінку мають закінчення -о',
      en: 'First-declension hard stem nouns in vocative take -о ending',
    },
    evaluate: (opt) => ({
      isCorrect: opt === 'колего',
      feedback:
        opt === 'колего'
          ? 'Правильно! Іменники I відміни твердої групи закінчуються на -о.'
          : 'Помилка. Звертання вимагає кличного відмінка із закінченням -о.',
      ruleCitation: '§ 87, п. 1',
      ruleSummary: 'Іменники I відміни твердої групи у кличному відмінку мають закінчення -о',
    }),
  },
];

describe('MechanicsPractice component', () => {
  it('renders drill session shell, prompt, blank, and all options', () => {
    const onBack = vi.fn();
    render(<MechanicsPractice meta={mockMeta} cards={mockCards} onBackToTracks={onBack} />);

    expect(screen.getByTestId('practice-mechanics-session')).toBeInTheDocument();
    expect(screen.getByTestId('practice-mechanics-counter')).toHaveTextContent('1 / 2');
    expect(screen.getByTestId('practice-mechanics-prompt')).toHaveTextContent('Я вийшов з');
    expect(screen.getByTestId('practice-mechanics-blank')).toHaveTextContent('____');

    for (const opt of mockCards[0].options) {
      expect(screen.getByTestId(`practice-mechanics-opt-${opt}`)).toBeInTheDocument();
    }
  });

  it('evaluates correct answer, displays positive feedback, rule citation, and enables advancement', async () => {
    const user = userEvent.setup();
    const onBack = vi.fn();
    render(<MechanicsPractice meta={mockMeta} cards={mockCards} onBackToTracks={onBack} />);

    const correctBtn = screen.getByTestId('practice-mechanics-opt-будинку');
    await user.click(correctBtn);

    expect(correctBtn).toHaveAttribute('data-correct', 'true');
    expect(screen.getByTestId('practice-mechanics-blank')).toHaveTextContent('будинку');
    expect(screen.getByTestId('practice-mechanics-feedback')).toBeInTheDocument();
    expect(screen.getByText('✓ Правильно!')).toBeInTheDocument();
    expect(screen.getAllByText(/§ 82, п. 2/i).length).toBeGreaterThanOrEqual(1);

    // Advance to next card
    const nextBtn = screen.getByTestId('practice-mechanics-next');
    await user.click(nextBtn);

    expect(screen.getByTestId('practice-mechanics-counter')).toHaveTextContent('2 / 2');
    expect(screen.getByTestId('practice-mechanics-prompt')).toHaveTextContent('Шановний');
  });

  it('evaluates wrong answer, highlights error and correct answer, and displays corrective rule', async () => {
    const user = userEvent.setup();
    const onBack = vi.fn();
    render(<MechanicsPractice meta={mockMeta} cards={mockCards} onBackToTracks={onBack} />);

    const wrongBtn = screen.getByTestId('practice-mechanics-opt-будинка');
    await user.click(wrongBtn);

    expect(wrongBtn).toHaveAttribute('data-wrong', 'true');
    const correctBtn = screen.getByTestId('practice-mechanics-opt-будинку');
    expect(correctBtn).toHaveAttribute('data-correct', 'true');
    expect(screen.getByTestId('practice-mechanics-feedback')).toBeInTheDocument();
    expect(screen.getByText(/Помилка/i)).toBeInTheDocument();
  });

  it('completes session, renders summary with score and misses list, and allows restart', async () => {
    const user = userEvent.setup();
    const onBack = vi.fn();
    render(<MechanicsPractice meta={mockMeta} cards={mockCards} onBackToTracks={onBack} />);

    // Answer card 1 correctly
    await user.click(screen.getByTestId('practice-mechanics-opt-будинку'));
    await user.click(screen.getByTestId('practice-mechanics-next'));

    // Answer card 2 wrongly
    await user.click(screen.getByTestId('practice-mechanics-opt-колегу'));
    await user.click(screen.getByTestId('practice-mechanics-next'));

    // Summary screen
    expect(screen.getByTestId('practice-mechanics-summary')).toBeInTheDocument();
    expect(screen.getByText('50%')).toBeInTheDocument();
    expect(screen.getByText(/Правильних відповідей: 1 із 2/i)).toBeInTheDocument();
    expect(screen.getByText(/Варто повторити:/i)).toBeInTheDocument();

    // Restart
    const restartBtn = screen.getByTestId('practice-mechanics-restart');
    await user.click(restartBtn);

    expect(screen.getByTestId('practice-mechanics-session')).toBeInTheDocument();
    expect(screen.getByTestId('practice-mechanics-counter')).toHaveTextContent('1 / 2');
  });

  it('calls onBackToTracks when back button is clicked', async () => {
    const user = userEvent.setup();
    const onBack = vi.fn();
    render(<MechanicsPractice meta={mockMeta} cards={mockCards} onBackToTracks={onBack} />);

    await user.click(screen.getByTestId('practice-mechanics-back-button'));
    expect(onBack).toHaveBeenCalledTimes(1);
  });
});
