import { describe, test, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CountSyllables from '@site/src/components/CountSyllables';

describe('CountSyllables', () => {
  const items = [
    { word: 'мама', correct: 2, translation: 'mother', explanation: 'Два склади: ма-ма.' },
    { word: 'стіл', correct: 1 },
  ];

  test('renders word, translation, and syllable number buttons', () => {
    const { container } = render(<CountSyllables items={items} instruction="Визнач кількість складів" />);
    expect(screen.getByText('мама')).toBeInTheDocument();
    expect(screen.getByText('mother')).toBeInTheDocument();
    expect(screen.getByText('Визнач кількість складів')).toBeInTheDocument();
    // Default maxCount is 6, so buttons 1 to 6
    const buttons = container.querySelectorAll('button');
    expect(buttons.length).toBe(6);
  });

  test('shows correct result and explanation upon selecting correct answer', async () => {
    const user = userEvent.setup();
    const { container } = render(<CountSyllables items={items} />);
    const button2 = screen.getByRole('button', { name: '2' });
    await user.click(button2);

    expect(container.textContent).toContain('✅ 2 склади');
    expect(container.textContent).toContain('Два склади: ма-ма.');
    expect(screen.getByRole('button', { name: 'Далі →' })).toBeInTheDocument();
  });

  test('shows incorrect result and explanation upon selecting wrong answer', async () => {
    const user = userEvent.setup();
    const { container } = render(<CountSyllables items={items} />);
    const button3 = screen.getByRole('button', { name: '3' });
    await user.click(button3);

    expect(container.textContent).toContain('❌ 2 склади');
    expect(container.textContent).toContain('Два склади: ма-ма.');
  });

  test('returns null when items is empty', () => {
    const { container } = render(<CountSyllables items={[]} />);
    expect(container.firstChild).toBeNull();
  });
});
