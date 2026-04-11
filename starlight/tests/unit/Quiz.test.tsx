import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Quiz, { QuizQuestion } from '@site/src/components/Quiz';

// Quiz shuffles its options on mount via useMemo, so tests find
// option buttons by text content rather than by index. Everything
// else (containers, feedback) is selected via the `data-activity`
// attributes baked into the component for test affordance — the
// same pattern used by Anagram/Unjumble.

// ── helpers ──────────────────────────────────────────────────────────────────

function optionButtons(container: HTMLElement) {
  const box = container.querySelector('[data-activity="quiz-options"]');
  if (!box) throw new Error('quiz-options container not found');
  return within(box as HTMLElement).getAllByRole('button');
}

function findOptionByText(container: HTMLElement, text: string) {
  const btn = optionButtons(container).find(b => b.textContent?.trim() === text);
  if (!btn) throw new Error(`option "${text}" not found`);
  return btn;
}

function feedbackBox(container: HTMLElement) {
  return container.querySelector('[data-activity="quiz-feedback"]');
}

// ── QuizQuestion ──────────────────────────────────────────────────────────────

describe('QuizQuestion', () => {
  const baseProps = {
    question: 'What is 2+2?',
    options: ['3', '4', '5', '6'],
    correctIndex: 1, // '4'
  };

  test('renders the question text', () => {
    const { container } = render(<QuizQuestion {...baseProps} />);
    expect(container.textContent).toContain('What is 2+2?');
  });

  test('renders one button per option', () => {
    const { container } = render(<QuizQuestion {...baseProps} />);
    expect(optionButtons(container)).toHaveLength(4);
  });

  test('renders all options regardless of shuffle order', () => {
    const { container } = render(<QuizQuestion {...baseProps} />);
    const texts = optionButtons(container).map(b => b.textContent?.trim());
    expect(new Set(texts)).toEqual(new Set(['3', '4', '5', '6']));
  });

  test('no feedback element is present before answering', () => {
    const { container } = render(<QuizQuestion {...baseProps} />);
    expect(feedbackBox(container)).not.toBeInTheDocument();
  });

  test('clicking the correct option shows correct feedback', async () => {
    const user = userEvent.setup();
    const { container } = render(<QuizQuestion {...baseProps} />);

    await user.click(findOptionByText(container, '4'));

    const fb = feedbackBox(container);
    expect(fb).toBeInTheDocument();
    expect(fb!.getAttribute('data-correct')).toBe('true');
    expect(fb!.textContent).toContain('Correct');
  });

  test('clicking a wrong option shows incorrect feedback with the right answer', async () => {
    const user = userEvent.setup();
    const { container } = render(<QuizQuestion {...baseProps} />);

    await user.click(findOptionByText(container, '3'));

    const fb = feedbackBox(container);
    expect(fb).toBeInTheDocument();
    expect(fb!.getAttribute('data-correct')).toBe('false');
    expect(fb!.textContent).toContain('Incorrect');
    // The incorrect message should reveal the correct answer text
    expect(fb!.textContent).toContain('4');
  });

  test('all option buttons become disabled after an answer is submitted', async () => {
    const user = userEvent.setup();
    const { container } = render(<QuizQuestion {...baseProps} />);

    await user.click(findOptionByText(container, '4'));

    for (const btn of optionButtons(container)) {
      expect(btn).toBeDisabled();
    }
  });

  test('second click on a locked option has no effect', async () => {
    const user = userEvent.setup();
    const { container } = render(<QuizQuestion {...baseProps} />);

    await user.click(findOptionByText(container, '3'));
    const firstFeedbackText = feedbackBox(container)!.textContent;

    // Try clicking a different option — disabled, so no feedback change
    const anotherOption = optionButtons(container).find(
      b => b.textContent?.trim() !== '3'
    )!;
    await user.click(anotherOption); // no-op — button is disabled

    expect(feedbackBox(container)!.textContent).toBe(firstFeedbackText);
  });

  test('renders explanation when provided and answer is revealed', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <QuizQuestion {...baseProps} explanation="Because 2 plus 2 equals 4." />
    );

    await user.click(findOptionByText(container, '4'));

    expect(container.textContent).toContain('Because 2 plus 2 equals 4.');
  });

  test('does not render explanation element when explanation is omitted', async () => {
    const user = userEvent.setup();
    const { container } = render(<QuizQuestion {...baseProps} />);

    await user.click(findOptionByText(container, '4'));

    // The `explanation` CSS module class should never appear in the DOM.
    expect(container.querySelector('[class*="explanation"]')).not.toBeInTheDocument();
  });

  test('renders Ukrainian correct label when isUkrainian=true', async () => {
    const user = userEvent.setup();
    const { container } = render(<QuizQuestion {...baseProps} isUkrainian />);

    await user.click(findOptionByText(container, '4'));

    expect(feedbackBox(container)!.textContent).toContain('Правильно');
  });

  test('renders Ukrainian incorrect label when isUkrainian=true', async () => {
    const user = userEvent.setup();
    const { container } = render(<QuizQuestion {...baseProps} isUkrainian />);

    await user.click(findOptionByText(container, '3'));

    expect(feedbackBox(container)!.textContent).toContain('Неправильно');
  });
});

// ── Quiz wrapper ──────────────────────────────────────────────────────────────

describe('Quiz wrapper', () => {
  const questionsProp = [
    {
      question: 'Q1?',
      options: [
        { text: 'a', correct: false },
        { text: 'b', correct: true },
      ],
    },
    {
      question: 'Q2?',
      options: [
        { text: 'x', correct: true },
        { text: 'y', correct: false },
      ],
    },
  ];

  test('renders one QuizQuestion per item in questions prop', () => {
    const { container } = render(<Quiz questions={questionsProp} />);
    expect(container.querySelectorAll('[data-activity="quiz-question"]')).toHaveLength(2);
  });

  test('wraps everything in a quiz activity container', () => {
    const { container } = render(<Quiz questions={questionsProp} />);
    expect(container.querySelector('[data-activity="quiz"]')).toBeInTheDocument();
  });

  test('renders instruction text when provided', () => {
    render(<Quiz questions={questionsProp} instruction="Pick the letter" />);
    expect(screen.getByText('Pick the letter')).toBeInTheDocument();
  });

  test('renders default English header label', () => {
    render(<Quiz questions={questionsProp} />);
    expect(screen.getAllByText('Quiz').length).toBeGreaterThan(0);
  });

  test('renders Ukrainian header label when isUkrainian=true', () => {
    render(<Quiz questions={questionsProp} isUkrainian />);
    expect(screen.getAllByText('Тест').length).toBeGreaterThan(0);
  });

  test('transforms options array to correctIndex and feeds through to question', async () => {
    // The wrapper converts [{text, correct}] -> string[] + correctIndex.
    // Verify end-to-end: clicking the "correct:true" option should give
    // the correct-feedback path.
    const user = userEvent.setup();
    const { container } = render(<Quiz questions={questionsProp} />);

    const firstQuestion = container.querySelectorAll<HTMLElement>('[data-activity="quiz-question"]')[0];
    const bBtn = within(firstQuestion).getByRole('button', { name: 'b' });
    await user.click(bBtn);

    const fb = firstQuestion.querySelector('[data-activity="quiz-feedback"]');
    expect(fb).toBeInTheDocument();
    expect(fb!.getAttribute('data-correct')).toBe('true');
  });

  test('renders children when no questions prop is passed', () => {
    const { container } = render(
      <Quiz>
        <div data-testid="child">custom child content</div>
      </Quiz>
    );
    expect(container.querySelector('[data-testid="child"]')).toBeInTheDocument();
  });
});

// ── Malformed-data guard rail ────────────────────────────────────────────────

describe('Quiz graceful degradation (malformed data)', () => {
  let warnSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => { /* swallow */ });
  });

  afterEach(() => {
    warnSpy.mockRestore();
  });

  test('logs a warning when no option has correct:true', () => {
    render(
      <Quiz
        questions={[
          {
            question: 'Broken data?',
            options: [
              { text: 'p', correct: false },
              { text: 'q', correct: false },
            ],
          },
        ]}
      />
    );
    expect(warnSpy).toHaveBeenCalledTimes(1);
    const msg = warnSpy.mock.calls[0][0] as string;
    expect(msg).toMatch(/\[Quiz\]/);
    expect(msg).toMatch(/Broken data\?/);
    expect(msg).toMatch(/correct:true/);
  });

  test('still renders the question rather than crashing the lesson page', () => {
    // Graceful degradation: the entire module MUST keep rendering even
    // with bad data. The fallback is index 0. Defensive rendering is
    // intentional — server-side validation is the primary defense and
    // the warning surfaces bad data in the browser console for devs.
    const { container } = render(
      <Quiz
        questions={[
          {
            question: 'Broken data?',
            options: [
              { text: 'p', correct: false },
              { text: 'q', correct: false },
            ],
          },
        ]}
      />
    );
    expect(container.querySelector('[data-activity="quiz-question"]')).toBeInTheDocument();
    expect(optionButtons(container)).toHaveLength(2);
  });

  test('does NOT warn when the question is well-formed', () => {
    render(
      <Quiz
        questions={[
          {
            question: 'Good data',
            options: [
              { text: 'a', correct: true },
              { text: 'b', correct: false },
            ],
          },
        ]}
      />
    );
    expect(warnSpy).not.toHaveBeenCalled();
  });
});
