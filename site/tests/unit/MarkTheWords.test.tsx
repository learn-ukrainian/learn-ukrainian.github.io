import { describe, expect, test, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MarkTheWordsActivity } from '@site/src/components/MarkTheWords';

describe('MarkTheWordsActivity Practice host contract', () => {
  test('reports a correct checked selection once', async () => {
    const user = userEvent.setup();
    const onComplete = vi.fn();
    render(
      <MarkTheWordsActivity
        text="Я бачу дім щодня."
        correctWords={['дім']}
        isUkrainian
        onComplete={onComplete}
      />,
    );

    await user.click(screen.getByRole('button', { name: 'дім' }));
    await user.click(screen.getByRole('button', { name: 'Перевірити' }));

    expect(onComplete).toHaveBeenCalledTimes(1);
    expect(onComplete).toHaveBeenCalledWith(true);
    expect(screen.getByText(/Чудово! Ви знайшли всі правильні слова/)).toBeInTheDocument();
  });

  test('reports an incorrect checked selection and respects a host lock', async () => {
    const user = userEvent.setup();
    const onComplete = vi.fn();
    const { rerender } = render(
      <MarkTheWordsActivity
        text="Я бачу дім щодня."
        correctWords={['дім']}
        onComplete={onComplete}
      />,
    );

    await user.click(screen.getByRole('button', { name: 'Я' }));
    await user.click(screen.getByRole('button', { name: 'Check Answer' }));
    expect(onComplete).toHaveBeenCalledWith(false);

    rerender(
      <MarkTheWordsActivity
        text="Я бачу дім щодня."
        correctWords={['дім']}
        onComplete={onComplete}
        disabled
      />,
    );
    expect(screen.getByRole('button', { name: 'Try Again' })).toBeDisabled();
    await user.click(screen.getByRole('button', { name: 'Try Again' }));
    expect(onComplete).toHaveBeenCalledTimes(1);
  });

  test('treats a hyphenated Ukrainian form as one tappable word', async () => {
    const user = userEvent.setup();
    const onComplete = vi.fn();
    render(<MarkTheWordsActivity text="Це будь-що." correctWords={['будь-що']} onComplete={onComplete} />);

    await user.click(screen.getByRole('button', { name: 'будь-що' }));
    await user.click(screen.getByRole('button', { name: 'Check Answer' }));

    expect(onComplete).toHaveBeenCalledWith(true);
  });
});
