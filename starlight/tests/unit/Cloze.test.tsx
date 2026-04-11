import { describe, test, expect } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Cloze, { ClozePassage } from '@site/src/components/Cloze';

// ── helpers ──────────────────────────────────────────────────────────────────

function blanks(container: HTMLElement) {
  return [...container.querySelectorAll<HTMLSelectElement>('[data-activity="cloze-blank"]')];
}

function blankByIndex(container: HTMLElement, idx: number) {
  const b = blanks(container).find(s => s.getAttribute('data-blank-index') === String(idx));
  if (!b) throw new Error(`cloze blank index=${idx} not found`);
  return b;
}

function feedback(container: HTMLElement) {
  return container.querySelector('[data-activity="cloze-feedback"]');
}

function checkBtn(container: HTMLElement) {
  return [...container.querySelectorAll<HTMLButtonElement>('button')].find(
    b => b.textContent?.trim() === 'Check Answers' || b.textContent?.trim() === 'Перевірити'
  );
}

function retryBtn(container: HTMLElement) {
  return [...container.querySelectorAll<HTMLButtonElement>('button')].find(
    b => b.textContent?.trim() === 'Try Again' || b.textContent?.trim() === 'Спробувати знову'
  );
}

// ── ClozePassage ──────────────────────────────────────────────────────────────

describe('ClozePassage', () => {
  const baseProps = {
    text: 'The sun [___:0] in the east. Water [___:1] wet.',
    blanks: [
      { index: 0, options: ['rises', 'sets'], answer: 'rises' },
      { index: 1, options: ['is', 'are'], answer: 'is' },
    ],
  };

  test('renders the passage wrapper', () => {
    const { container } = render(<ClozePassage {...baseProps} />);
    expect(container.querySelector('[data-activity="cloze-passage"]')).toBeInTheDocument();
  });

  test('replaces each [___:N] marker with a select element', () => {
    const { container } = render(<ClozePassage {...baseProps} />);
    expect(blanks(container)).toHaveLength(2);
  });

  test('each select carries its blank index via data-blank-index', () => {
    const { container } = render(<ClozePassage {...baseProps} />);
    const indices = blanks(container).map(s => s.getAttribute('data-blank-index'));
    expect(new Set(indices)).toEqual(new Set(['0', '1']));
  });

  test('Check Answers is disabled while any blank is unfilled', () => {
    const { container } = render(<ClozePassage {...baseProps} />);
    expect(checkBtn(container)).toBeDisabled();
  });

  test('Check Answers becomes enabled once every blank has a non-empty value', async () => {
    const user = userEvent.setup();
    const { container } = render(<ClozePassage {...baseProps} />);

    await user.selectOptions(blankByIndex(container, 0), 'rises');
    expect(checkBtn(container)).toBeDisabled(); // one blank still unfilled
    await user.selectOptions(blankByIndex(container, 1), 'is');

    expect(checkBtn(container)).toBeEnabled();
  });

  test('submitting all-correct answers reveals a success feedback', async () => {
    const user = userEvent.setup();
    const { container } = render(<ClozePassage {...baseProps} />);

    await user.selectOptions(blankByIndex(container, 0), 'rises');
    await user.selectOptions(blankByIndex(container, 1), 'is');
    await user.click(checkBtn(container)!);

    const fb = feedback(container);
    expect(fb).toBeInTheDocument();
    expect(fb!.getAttribute('data-correct')).toBe('true');
    expect(fb!.textContent).toContain('All answers are correct');
  });

  test('submitting with a wrong answer reveals an incorrect feedback with all correct answers listed', async () => {
    const user = userEvent.setup();
    const { container } = render(<ClozePassage {...baseProps} />);

    await user.selectOptions(blankByIndex(container, 0), 'sets'); // wrong
    await user.selectOptions(blankByIndex(container, 1), 'is'); // correct
    await user.click(checkBtn(container)!);

    const fb = feedback(container);
    expect(fb).toBeInTheDocument();
    expect(fb!.getAttribute('data-correct')).toBe('false');
    expect(fb!.textContent).toContain('rises');
    expect(fb!.textContent).toContain('is');
  });

  test('selects are disabled after submission', async () => {
    const user = userEvent.setup();
    const { container } = render(<ClozePassage {...baseProps} />);

    await user.selectOptions(blankByIndex(container, 0), 'rises');
    await user.selectOptions(blankByIndex(container, 1), 'is');
    await user.click(checkBtn(container)!);

    for (const sel of blanks(container)) {
      expect(sel).toBeDisabled();
    }
  });

  test('Try Again clears selections and re-enables selects', async () => {
    const user = userEvent.setup();
    const { container } = render(<ClozePassage {...baseProps} />);

    await user.selectOptions(blankByIndex(container, 0), 'rises');
    await user.selectOptions(blankByIndex(container, 1), 'is');
    await user.click(checkBtn(container)!);
    await user.click(retryBtn(container)!);

    for (const sel of blanks(container)) {
      expect(sel.value).toBe('');
      expect(sel).toBeEnabled();
    }
    expect(feedback(container)).toBeNull();
    expect(checkBtn(container)).toBeDisabled();
  });

  test('preserves surrounding text around each blank', () => {
    const { container } = render(<ClozePassage {...baseProps} />);
    // Passage text should still contain the static parts
    expect(container.textContent).toContain('The sun');
    expect(container.textContent).toContain('in the east');
    expect(container.textContent).toContain('Water');
    expect(container.textContent).toContain('wet');
  });

  test('Ukrainian labels when isUkrainian=true', async () => {
    const user = userEvent.setup();
    const { container } = render(<ClozePassage {...baseProps} isUkrainian />);

    expect(checkBtn(container)?.textContent).toContain('Перевірити');

    await user.selectOptions(blankByIndex(container, 0), 'rises');
    await user.selectOptions(blankByIndex(container, 1), 'is');
    await user.click(checkBtn(container)!);

    expect(feedback(container)?.textContent).toContain('Всі відповіді правильні');
  });

  test('answer comparison is case-insensitive and trim-tolerant', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <ClozePassage
        text="It [___:0] green."
        blanks={[{ index: 0, options: ['  IS  ', 'are'], answer: 'is' }]}
      />
    );

    // User picks the lowercase-equivalent option with whitespace padding
    await user.selectOptions(blankByIndex(container, 0), '  IS  ');
    await user.click(checkBtn(container)!);

    expect(feedback(container)?.getAttribute('data-correct')).toBe('true');
  });
});

// ── Cloze wrapper ─────────────────────────────────────────────────────────────

describe('Cloze wrapper', () => {
  const passage = 'Water [___:0] wet.';
  const blanks = [{ index: 0, options: ['is', 'are'], answer: 'is' }];

  test('wraps everything in a cloze activity container', () => {
    const { container } = render(<Cloze passage={passage} blanks={blanks} />);
    expect(container.querySelector('[data-activity="cloze"]')).toBeInTheDocument();
  });

  test('renders a ClozePassage inside the wrapper', () => {
    const { container } = render(<Cloze passage={passage} blanks={blanks} />);
    expect(container.querySelector('[data-activity="cloze-passage"]')).toBeInTheDocument();
  });

  test('renders the English header by default', () => {
    render(<Cloze passage={passage} blanks={blanks} />);
    expect(screen.getAllByText('Complete the Passage').length).toBeGreaterThan(0);
  });

  test('renders the Ukrainian header when isUkrainian=true', () => {
    render(<Cloze passage={passage} blanks={blanks} isUkrainian />);
    expect(screen.getAllByText('Заповніть текст').length).toBeGreaterThan(0);
  });

  test('renders instruction text when provided', () => {
    render(<Cloze passage={passage} blanks={blanks} instruction="Fill in each blank" />);
    expect(screen.getByText('Fill in each blank')).toBeInTheDocument();
  });

  test('parses embedded-options passage format when no blanks are provided', () => {
    // Inline format: passage text uses 0-based [___:N] markers; option
    // blocks are numbered from 1 because the parser does `parseInt - 1`
    // to convert them into the 0-based namespace the text markers use.
    // Confirmed by reading parsePassageWithEmbeddedOptions() in the
    // component source.
    const embedded = `The sky is [___:0] today.

1. blue | green | red
   > [!answer] blue`;
    const { container } = render(<Cloze passage={embedded} />);
    const sels = container.querySelectorAll<HTMLSelectElement>('[data-activity="cloze-blank"]');
    expect(sels).toHaveLength(1);
    // Three options plus the empty "---" placeholder
    expect(sels[0].querySelectorAll('option').length).toBe(4);
  });

  test('renders children when no passage is provided', () => {
    const { container } = render(
      <Cloze>
        <div data-testid="custom-child">custom</div>
      </Cloze>
    );
    expect(container.querySelector('[data-testid="custom-child"]')).toBeInTheDocument();
  });
});
