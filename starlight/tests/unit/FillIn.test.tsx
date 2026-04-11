import { describe, test, expect } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FillIn, { FillInQuestion } from '@site/src/components/FillIn';

// Components are instrumented with data-activity attributes; tests
// use them for stable element selection rather than CSS class
// substring matching. Drag-drop paths are NOT tested here because
// happy-dom doesn't implement drag events — E2E Playwright coverage
// is a follow-up (#1082 non-blocker).

// ── helpers ──────────────────────────────────────────────────────────────────

function chipsIn(container: HTMLElement) {
  const box = container.querySelector('[data-activity="fillin-chips"]');
  if (!box) return []; // chips unmount after submission
  return within(box as HTMLElement).getAllByRole('button');
}

function chipByText(container: HTMLElement, text: string) {
  const btn = chipsIn(container).find(b => b.textContent?.trim() === text);
  if (!btn) throw new Error(`chip "${text}" not found`);
  return btn;
}

function blankZone(container: HTMLElement) {
  return container.querySelector('[data-activity="fillin-blank"]') as HTMLElement | null;
}

function feedback(container: HTMLElement) {
  return container.querySelector('[data-activity="fillin-feedback"]') as HTMLElement | null;
}

function tryAgainBtn(container: HTMLElement) {
  return [...container.querySelectorAll<HTMLButtonElement>('button')].find(
    b => b.textContent?.trim() === 'Try Again' || b.textContent?.trim() === 'Спробувати знову'
  );
}

function checkButton(container: HTMLElement) {
  return [...container.querySelectorAll<HTMLButtonElement>('button')].find(
    b => b.textContent?.trim() === 'Check Answers' || b.textContent?.trim() === 'Перевірити'
  );
}

// ── FillInQuestion (single-blank, chip-style) ────────────────────────────────

describe('FillInQuestion', () => {
  const baseProps = {
    sentence: 'The capital of Ukraine is ___.',
    answer: 'Kyiv',
    options: ['Kyiv', 'Moscow', 'Warsaw'],
  };

  test('renders the sentence text', () => {
    const { container } = render(<FillInQuestion {...baseProps} />);
    expect(container.textContent).toContain('The capital of Ukraine is');
  });

  test('renders one chip per option', () => {
    const { container } = render(<FillInQuestion {...baseProps} />);
    expect(chipsIn(container)).toHaveLength(3);
  });

  test('renders all option texts regardless of shuffle order', () => {
    const { container } = render(<FillInQuestion {...baseProps} />);
    const texts = chipsIn(container).map(b => b.textContent?.trim());
    expect(new Set(texts)).toEqual(new Set(['Kyiv', 'Moscow', 'Warsaw']));
  });

  test('blank zone shows placeholder text before an answer is chosen', () => {
    const { container } = render(<FillInQuestion {...baseProps} />);
    expect(blankZone(container)?.textContent).toBe('drag here');
  });

  test('no feedback is shown before an answer is chosen', () => {
    const { container } = render(<FillInQuestion {...baseProps} />);
    expect(feedback(container)).toBeNull();
  });

  test('clicking a chip fills the blank with its text', async () => {
    const user = userEvent.setup();
    const { container } = render(<FillInQuestion {...baseProps} />);

    await user.click(chipByText(container, 'Kyiv'));

    expect(blankZone(container)?.textContent).toBe('Kyiv');
  });

  test('clicking the correct chip reveals correct feedback', async () => {
    const user = userEvent.setup();
    const { container } = render(<FillInQuestion {...baseProps} />);

    await user.click(chipByText(container, 'Kyiv'));

    const fb = feedback(container);
    expect(fb).toBeInTheDocument();
    expect(fb!.getAttribute('data-correct')).toBe('true');
    expect(fb!.textContent).toContain('Correct');
  });

  test('clicking a wrong chip reveals incorrect feedback with the right answer', async () => {
    const user = userEvent.setup();
    const { container } = render(<FillInQuestion {...baseProps} />);

    await user.click(chipByText(container, 'Moscow'));

    const fb = feedback(container);
    expect(fb).toBeInTheDocument();
    expect(fb!.getAttribute('data-correct')).toBe('false');
    expect(fb!.textContent).toContain('Kyiv'); // reveals the correct answer
  });

  test('chips disappear once an answer has been submitted', async () => {
    const user = userEvent.setup();
    const { container } = render(<FillInQuestion {...baseProps} />);

    expect(chipsIn(container).length).toBeGreaterThan(0);
    await user.click(chipByText(container, 'Kyiv'));

    // After submission the chip bank unmounts — `!showResult` guard
    expect(chipsIn(container)).toHaveLength(0);
  });

  test('Try Again restores initial state', async () => {
    const user = userEvent.setup();
    const { container } = render(<FillInQuestion {...baseProps} />);

    await user.click(chipByText(container, 'Moscow'));
    expect(feedback(container)).toBeInTheDocument();

    await user.click(tryAgainBtn(container)!);

    expect(feedback(container)).toBeNull();
    expect(blankZone(container)?.textContent).toBe('drag here');
    expect(chipsIn(container).length).toBe(3);
  });

  test('handles sentences with an underscore-style blank marker', () => {
    const { container } = render(
      <FillInQuestion sentence="I ___ pizza." answer="love" options={['love']} />
    );
    expect(container.textContent).toContain('I');
    expect(container.textContent).toContain('pizza');
  });

  test('renders without options (no chip bank)', () => {
    const { container } = render(
      <FillInQuestion sentence="The answer is ___." answer="42" />
    );
    expect(chipsIn(container)).toHaveLength(0);
    // Sentence + blank zone still present
    expect(blankZone(container)).toBeInTheDocument();
  });
});

// ── FillIn wrapper (select-dropdown, multi-item) ─────────────────────────────

describe('FillIn wrapper', () => {
  const items = [
    { sentence: 'The sun is ___.', answer: 'yellow', options: ['yellow', 'blue'] },
    { sentence: 'Water is ___.', answer: 'wet', options: ['wet', 'dry'] },
  ];

  test('renders one row per item', () => {
    const { container } = render(<FillIn items={items} />);
    expect(container.querySelectorAll('[data-activity="fillin-row"]')).toHaveLength(2);
  });

  test('wraps everything in a fill-in activity container', () => {
    const { container } = render(<FillIn items={items} />);
    expect(container.querySelector('[data-activity="fill-in"]')).toBeInTheDocument();
  });

  test('renders one select dropdown per item', () => {
    const { container } = render(<FillIn items={items} />);
    expect(container.querySelectorAll('select')).toHaveLength(2);
  });

  test('renders instruction text when provided', () => {
    render(<FillIn items={items} instruction="Pick the best word" />);
    expect(screen.getByText('Pick the best word')).toBeInTheDocument();
  });

  test('renders English header label by default', () => {
    render(<FillIn items={items} />);
    expect(screen.getAllByText('Fill in the Blank').length).toBeGreaterThan(0);
  });

  test('renders Ukrainian header label when isUkrainian=true', () => {
    render(<FillIn items={items} isUkrainian />);
    expect(screen.getAllByText('Заповніть пропуски').length).toBeGreaterThan(0);
  });

  test('Check Answers button is disabled until every item has a selection', () => {
    const { container } = render(<FillIn items={items} />);
    expect(checkButton(container)).toBeDisabled();
  });

  test('Check Answers button becomes enabled after every item is answered', async () => {
    const user = userEvent.setup();
    const { container } = render(<FillIn items={items} />);

    const selects = [...container.querySelectorAll<HTMLSelectElement>('select')];
    await user.selectOptions(selects[0], 'yellow');
    // still disabled — only one answered
    expect(checkButton(container)).toBeDisabled();
    await user.selectOptions(selects[1], 'wet');

    expect(checkButton(container)).toBeEnabled();
  });

  test('Check Answers reveals correct-hint on wrong answers only', async () => {
    const user = userEvent.setup();
    const { container } = render(<FillIn items={items} />);

    const selects = [...container.querySelectorAll<HTMLSelectElement>('select')];
    await user.selectOptions(selects[0], 'yellow'); // correct
    await user.selectOptions(selects[1], 'dry'); // wrong
    await user.click(checkButton(container)!);

    const hints = container.querySelectorAll('[class*="correctHint"]');
    // Only the incorrect row should render a hint
    expect(hints.length).toBe(1);
    expect(hints[0].textContent).toContain('wet');
  });

  test('Try Again resets selections and hides feedback', async () => {
    const user = userEvent.setup();
    const { container } = render(<FillIn items={items} />);

    const selects = () => [...container.querySelectorAll<HTMLSelectElement>('select')];
    await user.selectOptions(selects()[0], 'yellow');
    await user.selectOptions(selects()[1], 'wet');
    await user.click(checkButton(container)!);

    await user.click(tryAgainBtn(container)!);

    // Back to Check Answers, disabled, selections cleared
    expect(checkButton(container)).toBeDisabled();
    for (const sel of selects()) {
      expect(sel.value).toBe('');
    }
  });

  test('selects are disabled after Check Answers is pressed', async () => {
    const user = userEvent.setup();
    const { container } = render(<FillIn items={items} />);

    const selects = [...container.querySelectorAll<HTMLSelectElement>('select')];
    await user.selectOptions(selects[0], 'yellow');
    await user.selectOptions(selects[1], 'wet');
    await user.click(checkButton(container)!);

    for (const sel of container.querySelectorAll<HTMLSelectElement>('select')) {
      expect(sel).toBeDisabled();
    }
  });
});
