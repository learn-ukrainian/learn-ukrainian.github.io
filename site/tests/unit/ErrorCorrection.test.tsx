import { describe, test, expect } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ErrorCorrection, { ErrorCorrectionItem } from '@site/src/components/ErrorCorrection';

// ErrorCorrection is a step machine: identify → fix → complete.
// The sentence is split into clickable <span> tokens (role="button"
// for a11y). Options are shuffled on mount — look up by text.

// ── helpers ──────────────────────────────────────────────────────────────────

function wordByText(container: HTMLElement, text: string) {
  const all = [...container.querySelectorAll('[data-activity="error-correction-word"]')];
  const el = all.find(w => w.textContent?.trim() === text);
  if (!el) throw new Error(`word "${text}" not found (present: ${all.map(w => w.textContent?.trim()).join(', ')})`);
  return el as HTMLElement;
}

function noErrorBtn(container: HTMLElement) {
  return container.querySelector('[data-activity="error-correction-no-error"]') as HTMLButtonElement | null;
}

function fixChipByText(container: HTMLElement, text: string) {
  const panel = container.querySelector('[data-activity="error-correction-fix-options"]');
  if (!panel) throw new Error('fix-options panel not visible — still in identify step?');
  const btns = [...panel.querySelectorAll('[data-activity="error-correction-fix-chip"]')];
  const btn = btns.find(b => b.textContent?.trim() === text);
  if (!btn) throw new Error(`fix chip "${text}" not found`);
  return btn as HTMLElement;
}

function feedback(container: HTMLElement) {
  return container.querySelector('[data-activity="error-correction-feedback"]');
}

function itemContainer(container: HTMLElement) {
  return container.querySelector('[data-activity="error-correction-item"]') as HTMLElement;
}

function retryBtn(container: HTMLElement) {
  return [...container.querySelectorAll<HTMLButtonElement>('button')].find(
    b => b.textContent?.trim() === 'Try Again' || b.textContent?.trim() === 'Спробувати знову'
  );
}

// ── ErrorCorrectionItem ───────────────────────────────────────────────────────

describe('ErrorCorrectionItem (identify step)', () => {
  const baseProps = {
    sentence: 'I goed to school yesterday.',
    errorWord: 'goed',
    correctForm: 'went',
    options: ['went', 'go', 'going'],
    explanation: 'Past tense of "go" is irregular: went.',
  };

  test('starts in the identify step', () => {
    const { container } = render(<ErrorCorrectionItem {...baseProps} />);
    expect(itemContainer(container).getAttribute('data-step')).toBe('identify');
  });

  test('renders each word in the sentence as a clickable span', () => {
    const { container } = render(<ErrorCorrectionItem {...baseProps} />);
    const words = [...container.querySelectorAll('[data-activity="error-correction-word"]')].map(w => w.textContent?.trim());
    // "I goed to school yesterday" — 5 content words (punctuation excluded)
    expect(words).toContain('I');
    expect(words).toContain('goed');
    expect(words).toContain('to');
    expect(words).toContain('school');
    expect(words).toContain('yesterday');
  });

  test('renders the "No Error" button during identify step', () => {
    const { container } = render(<ErrorCorrectionItem {...baseProps} />);
    expect(noErrorBtn(container)).toBeInTheDocument();
  });

  test('does NOT render fix options during identify step', () => {
    const { container } = render(<ErrorCorrectionItem {...baseProps} />);
    expect(container.querySelector('[data-activity="error-correction-fix-options"]')).toBeNull();
  });

  test('does NOT render feedback during identify step', () => {
    const { container } = render(<ErrorCorrectionItem {...baseProps} />);
    expect(feedback(container)).toBeNull();
  });
});

describe('ErrorCorrectionItem (correct → identify → fix → complete path)', () => {
  const baseProps = {
    sentence: 'I goed to school yesterday.',
    errorWord: 'goed',
    correctForm: 'went',
    options: ['went', 'go', 'going'],
    explanation: 'Past tense of "go" is irregular: went.',
  };

  test('clicking the error word advances to the fix step', async () => {
    const user = userEvent.setup();
    const { container } = render(<ErrorCorrectionItem {...baseProps} />);

    await user.click(wordByText(container, 'goed'));

    expect(itemContainer(container).getAttribute('data-step')).toBe('fix');
    expect(container.querySelector('[data-activity="error-correction-fix-options"]')).toBeInTheDocument();
  });

  test('fix step shows all option chips', async () => {
    const user = userEvent.setup();
    const { container } = render(<ErrorCorrectionItem {...baseProps} />);

    await user.click(wordByText(container, 'goed'));

    const chips = [...container.querySelectorAll('[data-activity="error-correction-fix-chip"]')];
    expect(chips).toHaveLength(3);
    const texts = chips.map(c => c.textContent?.trim());
    expect(new Set(texts)).toEqual(new Set(['went', 'go', 'going']));
  });

  test('selecting the correct fix advances to complete with correct feedback', async () => {
    const user = userEvent.setup();
    const { container } = render(<ErrorCorrectionItem {...baseProps} />);

    await user.click(wordByText(container, 'goed'));
    await user.click(fixChipByText(container, 'went'));

    expect(itemContainer(container).getAttribute('data-step')).toBe('complete');
    const fb = feedback(container);
    expect(fb).toBeInTheDocument();
    expect(fb!.getAttribute('data-correct')).toBe('true');
    expect(fb!.textContent).toContain('went');
  });

  test('selecting a wrong fix advances to complete with incorrect feedback', async () => {
    const user = userEvent.setup();
    const { container } = render(<ErrorCorrectionItem {...baseProps} />);

    await user.click(wordByText(container, 'goed'));
    await user.click(fixChipByText(container, 'go'));

    expect(itemContainer(container).getAttribute('data-step')).toBe('complete');
    const fb = feedback(container);
    expect(fb).toBeInTheDocument();
    expect(fb!.getAttribute('data-correct')).toBe('false');
    // Reveals correct answer in the feedback
    expect(fb!.textContent).toContain('went');
  });

  test('explanation is shown in the feedback when complete', async () => {
    const user = userEvent.setup();
    const { container } = render(<ErrorCorrectionItem {...baseProps} />);

    await user.click(wordByText(container, 'goed'));
    await user.click(fixChipByText(container, 'went'));

    expect(container.textContent).toContain('Past tense of');
  });

  test('Try Again resets back to identify step', async () => {
    const user = userEvent.setup();
    const { container } = render(<ErrorCorrectionItem {...baseProps} />);

    await user.click(wordByText(container, 'goed'));
    await user.click(fixChipByText(container, 'went'));

    await user.click(retryBtn(container)!);

    expect(itemContainer(container).getAttribute('data-step')).toBe('identify');
    expect(feedback(container)).toBeNull();
    expect(noErrorBtn(container)).toBeInTheDocument();
  });
});

describe('ErrorCorrectionItem (wrong-word attempt during identify)', () => {
  const baseProps = {
    sentence: 'I goed to school yesterday.',
    errorWord: 'goed',
    correctForm: 'went',
    options: ['went', 'go'],
    explanation: '',
  };

  test('clicking a non-error word keeps the step at identify', async () => {
    const user = userEvent.setup();
    const { container } = render(<ErrorCorrectionItem {...baseProps} />);

    await user.click(wordByText(container, 'school'));

    expect(itemContainer(container).getAttribute('data-step')).toBe('identify');
    expect(container.querySelector('[data-activity="error-correction-fix-options"]')).toBeNull();
  });

  test('clicking a non-error word does NOT open the fix step', async () => {
    const user = userEvent.setup();
    const { container } = render(<ErrorCorrectionItem {...baseProps} />);

    await user.click(wordByText(container, 'I'));
    await user.click(wordByText(container, 'to'));

    expect(itemContainer(container).getAttribute('data-step')).toBe('identify');
  });
});

describe('ErrorCorrectionItem (no-error path)', () => {
  const noErrorProps = {
    sentence: 'I went to school yesterday.',
    errorWord: null,
    correctForm: '',
    options: [],
    explanation: 'Correct as written.',
  };

  test('clicking "No Error" when errorWord is null advances to complete', async () => {
    const user = userEvent.setup();
    const { container } = render(<ErrorCorrectionItem {...noErrorProps} />);

    await user.click(noErrorBtn(container)!);

    expect(itemContainer(container).getAttribute('data-step')).toBe('complete');
    const fb = feedback(container);
    expect(fb).toBeInTheDocument();
    expect(fb!.getAttribute('data-correct')).toBe('true');
    expect(fb!.textContent).toContain('no error');
  });

  test('clicking "No Error" when there IS an error keeps the step at identify', async () => {
    const user = userEvent.setup();
    const errorProps = { ...noErrorProps, errorWord: 'went', correctForm: 'goed', options: ['went', 'goed'] };
    const { container } = render(<ErrorCorrectionItem {...errorProps} />);

    await user.click(noErrorBtn(container)!);

    expect(itemContainer(container).getAttribute('data-step')).toBe('identify');
    // Button now carries the "wrong" visual state class
    expect(noErrorBtn(container)?.className).toMatch(/noErrorWrong|wrong/i);
  });
});

describe('ErrorCorrectionItem multi-word error', () => {
  // The component supports multi-word error phrases via
  // `errorWord.split(/\s+/)` — clicking ANY word that belongs to the
  // phrase should advance to the fix step, and the stored selection
  // is the full phrase (not just the clicked word).
  const props = {
    sentence: 'The new car have been parked here.',
    errorWord: 'have been',
    correctForm: 'has been',
    options: ['has been', 'was being', 'is being'],
    explanation: '"car" is singular, so the auxiliary must be "has".',
  };

  test('clicking the first word of a multi-word error phrase advances to fix', async () => {
    const user = userEvent.setup();
    const { container } = render(<ErrorCorrectionItem {...props} />);

    await user.click(wordByText(container, 'have'));

    expect(itemContainer(container).getAttribute('data-step')).toBe('fix');
  });

  test('clicking the second word of a multi-word error phrase ALSO advances to fix', async () => {
    const user = userEvent.setup();
    const { container } = render(<ErrorCorrectionItem {...props} />);

    await user.click(wordByText(container, 'been'));

    expect(itemContainer(container).getAttribute('data-step')).toBe('fix');
  });

  test('fix panel shows the full phrase (not the clicked word) as the prompt target', async () => {
    const user = userEvent.setup();
    const { container } = render(<ErrorCorrectionItem {...props} />);

    await user.click(wordByText(container, 'have'));

    const panel = container.querySelector('[data-activity="error-correction-fix-options"]');
    // The prompt text contains the full phrase in a <strong> tag
    expect(panel?.textContent).toContain('have been');
  });

  test('selecting the correct fix for a multi-word phrase completes with correct feedback', async () => {
    const user = userEvent.setup();
    const { container } = render(<ErrorCorrectionItem {...props} />);

    await user.click(wordByText(container, 'have'));
    await user.click(fixChipByText(container, 'has been'));

    const fb = feedback(container);
    expect(fb).toBeInTheDocument();
    expect(fb!.getAttribute('data-correct')).toBe('true');
  });
});

describe('ErrorCorrectionItem keyboard a11y', () => {
  // Clickable word spans are role="button" + tabIndex=0 during the
  // identify step, and MUST respond to Enter and Space per WCAG
  // SC 2.1.1. This is why the onKeyDown handler exists — adding
  // role="button" without the keyboard path would be a WCAG
  // violation (#1082 batch-2 review r1 blocker).
  const props = {
    sentence: 'I goed to school.',
    errorWord: 'goed',
    correctForm: 'went',
    options: ['went', 'go'],
    explanation: '',
  };

  test('pressing Enter on the error word advances to the fix step', async () => {
    const user = userEvent.setup();
    const { container } = render(<ErrorCorrectionItem {...props} />);

    const target = wordByText(container, 'goed');
    target.focus();
    await user.keyboard('{Enter}');

    expect(itemContainer(container).getAttribute('data-step')).toBe('fix');
  });

  test('pressing Space on the error word advances to the fix step', async () => {
    const user = userEvent.setup();
    const { container } = render(<ErrorCorrectionItem {...props} />);

    const target = wordByText(container, 'goed');
    target.focus();
    await user.keyboard('[Space]');

    expect(itemContainer(container).getAttribute('data-step')).toBe('fix');
  });

  test('pressing other keys (e.g. Tab-like letters) does NOT activate the word', async () => {
    const user = userEvent.setup();
    const { container } = render(<ErrorCorrectionItem {...props} />);

    const target = wordByText(container, 'goed');
    target.focus();
    await user.keyboard('a');

    expect(itemContainer(container).getAttribute('data-step')).toBe('identify');
  });

  test('words are focusable during identify step (tabIndex=0)', () => {
    const { container } = render(<ErrorCorrectionItem {...props} />);
    expect(wordByText(container, 'goed').getAttribute('tabindex')).toBe('0');
  });

  test('words become non-focusable after advancing past identify (tabIndex=-1)', async () => {
    const user = userEvent.setup();
    const { container } = render(<ErrorCorrectionItem {...props} />);

    await user.click(wordByText(container, 'goed'));
    // Now in fix step — words should no longer be focusable
    expect(wordByText(container, 'I').getAttribute('tabindex')).toBe('-1');
  });

  test('words carry an aria-label during identify step for screen readers', () => {
    const { container } = render(<ErrorCorrectionItem {...props} />);
    const label = wordByText(container, 'goed').getAttribute('aria-label');
    expect(label).toContain('goed');
    expect(label).toContain('error');
  });
});

describe('ErrorCorrectionItem Ukrainian labels', () => {
  const props = {
    sentence: 'Я пішов до школу вчора.',
    errorWord: 'школу',
    correctForm: 'школи',
    options: ['школи', 'школа'],
    explanation: 'Після "до" потрібен родовий відмінок.',
    isUkrainian: true,
  };

  test('step 1 uses Ukrainian label', () => {
    render(<ErrorCorrectionItem {...props} />);
    expect(screen.getByText('Крок 1: Знайдіть помилку')).toBeInTheDocument();
  });

  test('No Error button uses Ukrainian label', () => {
    const { container } = render(<ErrorCorrectionItem {...props} />);
    expect(noErrorBtn(container)?.textContent).toContain('У цьому реченні немає помилок');
  });

  test('Ukrainian correct feedback after fixing', async () => {
    const user = userEvent.setup();
    const { container } = render(<ErrorCorrectionItem {...props} />);

    await user.click(wordByText(container, 'школу'));
    await user.click(fixChipByText(container, 'школи'));

    expect(feedback(container)?.textContent).toContain('Правильно');
  });
});

// ── ErrorCorrection wrapper ──────────────────────────────────────────────────

describe('ErrorCorrection wrapper', () => {
  const items = [
    {
      sentence: 'I goed to school.',
      errorWord: 'goed',
      correctForm: 'went',
      options: ['went', 'go'],
      explanation: '',
    },
    {
      sentence: 'She have three cats.',
      errorWord: 'have',
      correctForm: 'has',
      options: ['has', 'had'],
      explanation: '',
    },
  ];

  test('wraps everything in an error-correction activity container', () => {
    const { container } = render(<ErrorCorrection items={items} />);
    expect(container.querySelector('[data-activity="error-correction"]')).toBeInTheDocument();
  });

  test('renders one ErrorCorrectionItem per item', () => {
    const { container } = render(<ErrorCorrection items={items} />);
    expect(container.querySelectorAll('[data-activity="error-correction-item"]')).toHaveLength(2);
  });

  test('renders instruction when provided', () => {
    render(<ErrorCorrection items={items} instruction="Find the mistake" />);
    expect(screen.getByText('Find the mistake')).toBeInTheDocument();
  });

  test('renders English header by default', () => {
    render(<ErrorCorrection items={items} />);
    expect(screen.getAllByText('Find and Fix').length).toBeGreaterThan(0);
  });

  test('renders Ukrainian header when isUkrainian=true', () => {
    render(<ErrorCorrection items={items} isUkrainian />);
    expect(screen.getAllByText('Знайдіть і виправте помилку').length).toBeGreaterThan(0);
  });

  test('items operate independently — one item advancing does not affect another', async () => {
    const user = userEvent.setup();
    const { container } = render(<ErrorCorrection items={items} />);

    const allItems = [...container.querySelectorAll<HTMLElement>('[data-activity="error-correction-item"]')];
    // Advance the first item to fix step
    const goedBtn = within(allItems[0])
      .getAllByText((_, el) => el?.textContent?.trim() === 'goed' && el.getAttribute('data-activity') === 'error-correction-word')[0];
    await user.click(goedBtn);

    expect(allItems[0].getAttribute('data-step')).toBe('fix');
    expect(allItems[1].getAttribute('data-step')).toBe('identify');
  });
});
