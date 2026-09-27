import { describe, test, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ImageToLetter from '@site/src/components/ImageToLetter';

// The component takes {emoji, answer, distractors[]}; the Python activity
// parser maps the A1 schema fields {image, letter, options} onto it (#8716).

const apple = {
  emoji: '🍎',
  answer: 'Я',
  distractors: ['А', 'О'],
  explanation: 'Яблуко begins with Я.',
};
const owl = {
  emoji: '🦉',
  answer: 'С',
  distractors: ['Т', 'К'],
  explanation: 'Сова begins with С.',
};
const legacy = {
  emoji: '🐱',
  answer: 'К',
  distractors: ['М', 'Л'],
  note: 'Кіт begins with К.',
};

const DONE = /Вправу завершено!/;

describe('ImageToLetter', () => {
  test('renders an asset path as an <img> with answer-neutral alt text, not as text', () => {
    const { container } = render(<ImageToLetter items={[{ ...apple, emoji: 'assets/apple.png' }]} />);
    const img = container.querySelector('img');
    expect(img).not.toBeNull();
    expect(img).toHaveAttribute('src', 'assets/apple.png');
    const alt = img?.getAttribute('alt') ?? '';
    expect(alt).not.toBe('');
    for (const leak of [apple.answer, ...apple.distractors, 'apple']) {
      expect(alt).not.toContain(leak);
    }
    expect(screen.queryByText('assets/apple.png')).not.toBeInTheDocument();
  });

  test.each(['🍎', '👨‍👩‍👧‍👦', '🇺🇦'])('renders the emoji %s as text, not as an image', (emoji) => {
    const { container } = render(<ImageToLetter items={[{ ...apple, emoji }]} />);
    expect(container.querySelector('img')).toBeNull();
    expect(screen.getByText(emoji)).toBeInTheDocument();
  });

  test('renders the answer and every distractor as an option button', () => {
    render(<ImageToLetter items={[apple]} />);
    const labels = screen.getAllByRole('button').map((b) => b.textContent);
    expect(labels.sort()).toEqual(['А', 'О', 'Я']);
  });

  test('shows the emoji and the instruction', () => {
    render(<ImageToLetter items={[apple]} instruction="Pick the first letter." />);
    expect(screen.getByText('🍎')).toBeInTheDocument();
    expect(screen.getByText('Pick the first letter.')).toBeInTheDocument();
  });

  test('hides the explanation until the correct answer is chosen', () => {
    render(<ImageToLetter items={[apple, owl]} />);
    expect(screen.queryByText(apple.explanation)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'А' }));
    expect(screen.queryByText(apple.explanation)).not.toBeInTheDocument();
  });

  test('middle item: explanation shown after a correct answer, Next advances', () => {
    render(<ImageToLetter items={[apple, owl]} />);
    fireEvent.click(screen.getByRole('button', { name: 'Я' }));
    expect(screen.getByText(apple.explanation)).toBeInTheDocument();
    expect(screen.queryByText(DONE)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Далі →' }));
    expect(screen.queryByText(apple.explanation)).not.toBeInTheDocument();
    expect(screen.getByText('🦉')).toBeInTheDocument();
    expect(screen.queryByText(DONE)).not.toBeInTheDocument();
  });

  test('final item: explanation shown, completion only after Finish', () => {
    render(<ImageToLetter items={[apple, owl]} />);
    fireEvent.click(screen.getByRole('button', { name: 'Я' }));
    fireEvent.click(screen.getByRole('button', { name: 'Далі →' }));
    fireEvent.click(screen.getByRole('button', { name: 'С' }));

    expect(screen.getByText(owl.explanation)).toBeInTheDocument();
    expect(screen.queryByText(DONE, { exact: false })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Завершити' }));
    expect(screen.getByText(DONE, { exact: false })).toBeInTheDocument();
    expect(screen.queryByText(owl.explanation)).not.toBeInTheDocument();
  });

  test('single-item activity: explanation shown, completion only after Finish', () => {
    render(<ImageToLetter items={[apple]} />);
    fireEvent.click(screen.getByRole('button', { name: 'Я' }));

    expect(screen.getByText(apple.explanation)).toBeInTheDocument();
    expect(screen.queryByText(DONE, { exact: false })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Завершити' }));
    expect(screen.getByText(DONE, { exact: false })).toBeInTheDocument();
  });

  test('legacy note is shown after the correct answer on a single item', () => {
    render(<ImageToLetter items={[legacy]} />);
    fireEvent.click(screen.getByRole('button', { name: 'К' }));

    expect(screen.getByText(legacy.note)).toBeInTheDocument();
    expect(screen.queryByText(DONE, { exact: false })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Завершити' }));
    expect(screen.getByText(DONE, { exact: false })).toBeInTheDocument();
  });

  test('English labels when isUkrainian is false', () => {
    render(<ImageToLetter items={[apple, owl]} isUkrainian={false} />);
    fireEvent.click(screen.getByRole('button', { name: 'Я' }));
    fireEvent.click(screen.getByRole('button', { name: 'Next →' }));
    fireEvent.click(screen.getByRole('button', { name: 'С' }));
    fireEvent.click(screen.getByRole('button', { name: 'Finish' }));
    expect(screen.getByText(/Exercise complete!/)).toBeInTheDocument();
  });
});

// ── per-option feedback (optionWhy, aligned to [answer, ...distractors]) ───

describe('ImageToLetter optionWhy (fresh-build per-option feedback)', () => {
  const withWhy = {
    ...apple,
    // Aligned to [answer, ...distractors] = ['Я', 'А', 'О']
    optionWhy: ['Я for яблуко.', 'А is a different letter.', 'О is a different letter.'],
  };

  test('a correct pick shows only the chosen (= correct) option why, in a status region', () => {
    const { container } = render(<ImageToLetter items={[withWhy]} />);
    fireEvent.click(screen.getByRole('button', { name: 'Я' }));

    const panel = container.querySelector('[data-activity="itl-option-why-panel"]');
    expect(panel).toBeInTheDocument();
    expect(panel).toHaveAttribute('role', 'status');
    expect(panel).toHaveAttribute('aria-live', 'polite');
    expect(container.querySelector('[data-activity="itl-option-why"]')?.textContent).toBe('Я for яблуко.');
    expect(container.querySelector('[data-activity="itl-correct-why"]')).not.toBeInTheDocument();
  });

  test('a wrong pick shows the chosen option why, then the correct option why', () => {
    const { container } = render(<ImageToLetter items={[withWhy]} />);
    fireEvent.click(screen.getByRole('button', { name: 'А' }));

    expect(container.querySelector('[data-activity="itl-option-why"]')?.textContent).toBe(
      'А is a different letter.',
    );
    expect(container.querySelector('[data-activity="itl-correct-why"]')?.textContent).toBe('Я for яблуко.');
  });

  test('without optionWhy, no why-panel renders and legacy explanation/note keep working (V7 fallback)', () => {
    const { container } = render(<ImageToLetter items={[apple]} />);
    fireEvent.click(screen.getByRole('button', { name: 'Я' }));

    expect(container.querySelector('[data-activity="itl-option-why-panel"]')).not.toBeInTheDocument();
    expect(screen.getByText(apple.explanation)).toBeInTheDocument();
  });
});
