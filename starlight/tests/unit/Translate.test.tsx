import { describe, test, expect } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Translate, { TranslateItem } from '@site/src/components/Translate';

// Translate shuffles options on mount, so tests find option buttons
// by text content rather than by index. The correct answer may appear
// in any slot; findOption() locates it by literal text match.

// ── helpers ──────────────────────────────────────────────────────────────────

function optionButtons(container: HTMLElement) {
  const box = container.querySelector('[data-activity="translate-options"]');
  if (!box) throw new Error('translate-options container not found');
  return within(box as HTMLElement).getAllByRole('button');
}

function findOption(container: HTMLElement, text: string) {
  const btn = optionButtons(container).find(b => b.textContent?.trim() === text);
  if (!btn) throw new Error(`option "${text}" not found`);
  return btn;
}

function feedbackBox(container: HTMLElement) {
  return container.querySelector('[data-activity="translate-feedback"]');
}

function retryBtn(container: HTMLElement) {
  return [...container.querySelectorAll<HTMLButtonElement>('button')].find(
    b => b.textContent?.trim() === 'Try Again' || b.textContent?.trim() === 'Спробувати знову'
  );
}

// ── TranslateItem ─────────────────────────────────────────────────────────────

describe('TranslateItem (options-based)', () => {
  const baseProps = {
    source: 'Hello, how are you?',
    answer: 'Привіт, як справи?',
    options: ['Привіт, як справи?', 'До побачення', 'Дякую'],
  };

  test('renders the source text', () => {
    const { container } = render(<TranslateItem {...baseProps} />);
    expect(container.textContent).toContain('Hello, how are you?');
  });

  test('renders one button per option', () => {
    const { container } = render(<TranslateItem {...baseProps} />);
    expect(optionButtons(container)).toHaveLength(3);
  });

  test('renders all option texts regardless of shuffle order', () => {
    const { container } = render(<TranslateItem {...baseProps} />);
    const texts = optionButtons(container).map(b => b.textContent?.trim());
    expect(new Set(texts)).toEqual(
      new Set(['Привіт, як справи?', 'До побачення', 'Дякую'])
    );
  });

  test('no feedback shown before an option is selected', () => {
    const { container } = render(<TranslateItem {...baseProps} />);
    expect(feedbackBox(container)).toBeNull();
  });

  test('clicking the correct option reveals correct feedback', async () => {
    const user = userEvent.setup();
    const { container } = render(<TranslateItem {...baseProps} />);

    await user.click(findOption(container, 'Привіт, як справи?'));

    const fb = feedbackBox(container);
    expect(fb).toBeInTheDocument();
    expect(fb!.getAttribute('data-correct')).toBe('true');
    expect(fb!.textContent).toContain('Correct');
  });

  test('clicking a wrong option reveals incorrect feedback with the right answer', async () => {
    const user = userEvent.setup();
    const { container } = render(<TranslateItem {...baseProps} />);

    await user.click(findOption(container, 'Дякую'));

    const fb = feedbackBox(container);
    expect(fb).toBeInTheDocument();
    expect(fb!.getAttribute('data-correct')).toBe('false');
    expect(fb!.textContent).toContain('Привіт, як справи?');
  });

  test('all option buttons become disabled after submission', async () => {
    const user = userEvent.setup();
    const { container } = render(<TranslateItem {...baseProps} />);

    await user.click(findOption(container, 'Привіт, як справи?'));

    for (const btn of optionButtons(container)) {
      expect(btn).toBeDisabled();
    }
  });

  test('Try Again restores the options and clears feedback', async () => {
    const user = userEvent.setup();
    const { container } = render(<TranslateItem {...baseProps} />);

    await user.click(findOption(container, 'Дякую'));
    expect(feedbackBox(container)).toBeInTheDocument();

    await user.click(retryBtn(container)!);

    expect(feedbackBox(container)).toBeNull();
    for (const btn of optionButtons(container)) {
      expect(btn).toBeEnabled();
    }
  });

  test('renders explanation in the feedback when provided', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <TranslateItem {...baseProps} explanation="Standard greeting form" />
    );

    await user.click(findOption(container, 'Привіт, як справи?'));

    expect(container.textContent).toContain('Standard greeting form');
  });

  test('accepts alternative answers as correct', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <TranslateItem
        source="Hi"
        answer="Привіт"
        alternatives={['Добрий день']}
        options={['Привіт', 'Добрий день', 'Бувай']}
      />
    );

    await user.click(findOption(container, 'Добрий день'));

    expect(feedbackBox(container)?.getAttribute('data-correct')).toBe('true');
  });

  test('shows "also accepted" list on wrong answer when alternatives exist', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <TranslateItem
        source="Hi"
        answer="Привіт"
        alternatives={['Добрий день', 'Вітаю']}
        options={['Привіт', 'Добрий день', 'Вітаю', 'Бувай']}
      />
    );

    await user.click(findOption(container, 'Бувай'));

    const text = feedbackBox(container)?.textContent || '';
    expect(text).toContain('also accepted');
    expect(text).toContain('Добрий день');
    expect(text).toContain('Вітаю');
  });

  test('Ukrainian labels when isUkrainian=true', async () => {
    const user = userEvent.setup();
    const { container } = render(<TranslateItem {...baseProps} isUkrainian />);

    await user.click(findOption(container, 'Привіт, як справи?'));

    expect(feedbackBox(container)?.textContent).toContain('Правильно');
    expect(retryBtn(container)?.textContent).toContain('Спробувати знову');
  });
});

// ── Translate wrapper ─────────────────────────────────────────────────────────

describe('Translate wrapper', () => {
  const questions = [
    {
      source: 'Hello',
      options: [
        { text: 'Привіт', correct: true },
        { text: 'Бувай', correct: false },
      ],
    },
    {
      source: 'Goodbye',
      options: [
        { text: 'Привіт', correct: false },
        { text: 'Бувай', correct: true },
      ],
    },
  ];

  test('wraps everything in a translate activity container', () => {
    const { container } = render(<Translate questions={questions} />);
    expect(container.querySelector('[data-activity="translate"]')).toBeInTheDocument();
  });

  test('defaults to direction "to-uk"', () => {
    const { container } = render(<Translate questions={questions} />);
    expect(container.querySelector('[data-activity="translate"]')!.getAttribute('data-direction')).toBe('to-uk');
  });

  test('renders one TranslateItem per question', () => {
    const { container } = render(<Translate questions={questions} />);
    expect(container.querySelectorAll('[data-activity="translate-item"]')).toHaveLength(2);
  });

  test('renders default English title for direction="to-uk"', () => {
    render(<Translate questions={questions} />);
    expect(screen.getAllByText('Translate to Ukrainian').length).toBeGreaterThan(0);
  });

  test('renders English title for direction="to-en"', () => {
    render(<Translate questions={questions} direction="to-en" />);
    expect(screen.getAllByText('Translate to English').length).toBeGreaterThan(0);
  });

  test('renders Ukrainian title when isUkrainian=true', () => {
    render(<Translate questions={questions} isUkrainian />);
    expect(screen.getAllByText('Перекладіть на українську').length).toBeGreaterThan(0);
  });

  test('renders Ukrainian title for direction="to-en" + isUkrainian', () => {
    render(<Translate questions={questions} direction="to-en" isUkrainian />);
    expect(screen.getAllByText('Перекладіть на англійську').length).toBeGreaterThan(0);
  });

  test('renders instruction when provided', () => {
    render(<Translate questions={questions} instruction="Choose the best translation" />);
    expect(screen.getByText('Choose the best translation')).toBeInTheDocument();
  });

  test('wrapper correctly passes correct:true through to TranslateItem (end-to-end)', async () => {
    const user = userEvent.setup();
    const { container } = render(<Translate questions={questions} />);

    const items = [...container.querySelectorAll<HTMLElement>('[data-activity="translate-item"]')];
    const firstItem = items[0];
    const correctBtn = within(firstItem).getByRole('button', { name: 'Привіт' });
    await user.click(correctBtn);

    const fb = firstItem.querySelector('[data-activity="translate-feedback"]');
    expect(fb).toBeInTheDocument();
    expect(fb!.getAttribute('data-correct')).toBe('true');
  });

  test('renders children when no questions prop is passed', () => {
    const { container } = render(
      <Translate>
        <div data-testid="custom-child">custom content</div>
      </Translate>
    );
    expect(container.querySelector('[data-testid="custom-child"]')).toBeInTheDocument();
  });
});
