import { describe, test, expect } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TrueFalse, { TrueFalseQuestion } from '@site/src/components/TrueFalse';

// Components are instrumented with data-activity attributes for test
// affordance, matching the Anagram/Unjumble pattern.

// ── helpers ──────────────────────────────────────────────────────────────────

function tfButtonsIn(container: HTMLElement) {
  const box = container.querySelector('[data-activity="tf-buttons"]');
  if (!box) throw new Error('tf-buttons container not found');
  return within(box as HTMLElement).getAllByRole('button');
}

function findTfButton(container: HTMLElement, text: string) {
  const btn = tfButtonsIn(container).find(b => b.textContent?.trim() === text);
  if (!btn) throw new Error(`tf button "${text}" not found`);
  return btn;
}

function singleFeedback(container: HTMLElement) {
  return container.querySelector('[data-activity="tf-feedback"]');
}

function rowFeedbacks(container: HTMLElement) {
  return [...container.querySelectorAll('[data-activity="tf-row-feedback"]')];
}

function checkButton(container: HTMLElement) {
  return [...container.querySelectorAll<HTMLButtonElement>('button')].find(
    b => b.textContent?.trim() === 'Check Answers' || b.textContent?.trim() === 'Перевірити'
  );
}

function retryButton(container: HTMLElement) {
  return [...container.querySelectorAll<HTMLButtonElement>('button')].find(
    b => b.textContent?.trim() === 'Try Again' || b.textContent?.trim() === 'Спробувати знову'
  );
}

// ── TrueFalseQuestion (single-statement variant) ─────────────────────────────

describe('TrueFalseQuestion', () => {
  const baseProps = {
    statement: 'The sky is blue.',
    isTrue: true,
  };

  test('renders the statement', () => {
    const { container } = render(<TrueFalseQuestion {...baseProps} />);
    expect(container.textContent).toContain('The sky is blue.');
  });

  test('renders exactly two buttons (True and False) in English by default', () => {
    const { container } = render(<TrueFalseQuestion {...baseProps} />);
    const btns = tfButtonsIn(container);
    expect(btns).toHaveLength(2);
    expect(findTfButton(container, 'True')).toBeInTheDocument();
    expect(findTfButton(container, 'False')).toBeInTheDocument();
  });

  test('renders Ukrainian buttons when isUkrainian=true (regression for #1082 r1)', () => {
    const { container } = render(<TrueFalseQuestion {...baseProps} isUkrainian />);
    expect(findTfButton(container, 'Правда')).toBeInTheDocument();
    expect(findTfButton(container, 'Неправда')).toBeInTheDocument();
  });

  test('feedback is hidden before answering', () => {
    const { container } = render(<TrueFalseQuestion {...baseProps} />);
    expect(singleFeedback(container)).toBeNull();
  });

  test('clicking the correct button reveals the correct feedback', async () => {
    const user = userEvent.setup();
    const { container } = render(<TrueFalseQuestion {...baseProps} />);

    await user.click(findTfButton(container, 'True'));

    const fb = singleFeedback(container);
    expect(fb).toBeInTheDocument();
    expect(fb!.getAttribute('data-correct')).toBe('true');
    expect(fb!.textContent).toContain('Correct');
  });

  test('clicking the wrong button reveals the incorrect feedback', async () => {
    const user = userEvent.setup();
    const { container } = render(<TrueFalseQuestion {...baseProps} />);

    await user.click(findTfButton(container, 'False'));

    const fb = singleFeedback(container);
    expect(fb).toBeInTheDocument();
    expect(fb!.getAttribute('data-correct')).toBe('false');
    // For a "true" statement answered false, the message reveals the truth
    expect(fb!.textContent).toMatch(/true/i);
  });

  test('wrong-answer feedback uses Ukrainian phrasing in UK mode', async () => {
    const user = userEvent.setup();
    const { container } = render(<TrueFalseQuestion {...baseProps} isUkrainian />);

    await user.click(findTfButton(container, 'Неправда'));

    const fb = singleFeedback(container);
    expect(fb).toBeInTheDocument();
    expect(fb!.textContent).toContain('правдиве');
  });

  test('both buttons become disabled after an answer is submitted', async () => {
    const user = userEvent.setup();
    const { container } = render(<TrueFalseQuestion {...baseProps} />);

    await user.click(findTfButton(container, 'True'));

    for (const btn of tfButtonsIn(container)) {
      expect(btn).toBeDisabled();
    }
  });

  test('re-clicking a locked button does not change feedback', async () => {
    const user = userEvent.setup();
    const { container } = render(<TrueFalseQuestion {...baseProps} />);

    await user.click(findTfButton(container, 'False'));
    const firstText = singleFeedback(container)!.textContent;

    await user.click(findTfButton(container, 'True')); // disabled, no-op

    expect(singleFeedback(container)!.textContent).toBe(firstText);
  });

  test('renders explanation when provided and answer is revealed', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <TrueFalseQuestion {...baseProps} explanation="It's due to Rayleigh scattering." />
    );

    await user.click(findTfButton(container, 'True'));

    expect(container.textContent).toContain("It's due to Rayleigh scattering.");
  });
});

// ── TrueFalse wrapper (multi-item with Check Answers button) ─────────────────

describe('TrueFalse wrapper', () => {
  const items = [
    { statement: 'Kyiv is the capital of Ukraine.', isTrue: true, explanation: 'Correct.' },
    { statement: 'The Dnipro flows into the Baltic Sea.', isTrue: false, explanation: 'It flows into the Black Sea.' },
  ];

  test('renders one tf-row per item', () => {
    const { container } = render(<TrueFalse items={items} />);
    expect(container.querySelectorAll('[data-activity="tf-row"]')).toHaveLength(2);
  });

  test('wraps everything in a true-false activity container', () => {
    const { container } = render(<TrueFalse items={items} />);
    expect(container.querySelector('[data-activity="true-false"]')).toBeInTheDocument();
  });

  test('renders the instruction when provided', () => {
    render(<TrueFalse items={items} instruction="Decide if each statement is true" />);
    expect(screen.getByText('Decide if each statement is true')).toBeInTheDocument();
  });

  test('renders English header label by default', () => {
    render(<TrueFalse items={items} />);
    expect(screen.getAllByText('True or False').length).toBeGreaterThan(0);
  });

  test('renders Ukrainian header label when isUkrainian=true', () => {
    render(<TrueFalse items={items} isUkrainian />);
    expect(screen.getAllByText('Правда чи хибність').length).toBeGreaterThan(0);
  });

  test('Check Answers button is disabled until at least one answer is selected', () => {
    const { container } = render(<TrueFalse items={items} />);
    expect(checkButton(container)).toBeDisabled();
  });

  test('Check Answers button becomes enabled after a selection', async () => {
    const user = userEvent.setup();
    const { container } = render(<TrueFalse items={items} />);

    const firstRow = container.querySelectorAll<HTMLElement>('[data-activity="tf-row"]')[0];
    await user.click(within(firstRow).getByRole('button', { name: 'True' }));

    expect(checkButton(container)).toBeEnabled();
  });

  test('clicking Check Answers reveals one feedback box per answered item', async () => {
    const user = userEvent.setup();
    const { container } = render(<TrueFalse items={items} />);

    const rows = [...container.querySelectorAll<HTMLElement>('[data-activity="tf-row"]')];
    await user.click(within(rows[0]).getByRole('button', { name: 'True' }));
    await user.click(within(rows[1]).getByRole('button', { name: 'False' }));
    await user.click(checkButton(container)!);

    expect(rowFeedbacks(container).length).toBe(2);
    // Both answers were correct — verify the data-correct marker
    for (const fb of rowFeedbacks(container)) {
      expect(fb.getAttribute('data-correct')).toBe('true');
    }
  });

  test('Try Again resets selections and hides feedback', async () => {
    const user = userEvent.setup();
    const { container } = render(<TrueFalse items={items} />);

    const rows = [...container.querySelectorAll<HTMLElement>('[data-activity="tf-row"]')];
    await user.click(within(rows[0]).getByRole('button', { name: 'True' }));
    await user.click(within(rows[1]).getByRole('button', { name: 'False' }));
    await user.click(checkButton(container)!);

    expect(rowFeedbacks(container).length).toBe(2);

    await user.click(retryButton(container)!);

    expect(rowFeedbacks(container).length).toBe(0);
    // Check button reappears and is disabled again (no answers yet)
    expect(checkButton(container)).toBeDisabled();
  });

  test('uses Ukrainian button labels in wrapper when isUkrainian=true', () => {
    const { container } = render(<TrueFalse items={items} isUkrainian />);
    const rows = [...container.querySelectorAll<HTMLElement>('[data-activity="tf-row"]')];
    const firstRowBtns = within(rows[0]).getAllByRole('button');
    const labels = firstRowBtns.map(b => b.textContent?.trim());
    expect(labels).toContain('Правда');
    expect(labels).toContain('Неправда');
  });

  test('Check Answers uses the Ukrainian label when isUkrainian=true', async () => {
    const user = userEvent.setup();
    const { container } = render(<TrueFalse items={items} isUkrainian />);
    const firstRow = container.querySelectorAll<HTMLElement>('[data-activity="tf-row"]')[0];
    await user.click(within(firstRow).getByRole('button', { name: 'Правда' }));

    const check = [...container.querySelectorAll<HTMLButtonElement>('button')].find(
      b => b.textContent?.trim() === 'Перевірити'
    );
    expect(check).toBeInTheDocument();
  });
});
