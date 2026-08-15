import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import fixtures from '../../../packages/activity-kit/src/fixtures/lu.activity.v1.fixtures.json';
import {
  ActivityPlayer,
  Cloze,
  ClozePassage,
  MatchUp,
  TrueFalseQuestion,
} from '../../../packages/activity-kit/src';
import type { LuActivityV1 } from '../../../packages/activity-kit/src';

// Mirrors packages/activity-kit MatchUp MISSHAKE_TIMEOUT_MS (wrong-pair reset).
const MISSHAKE_TIMEOUT_MS = 240;

const trueFalseFixture = fixtures.find((fixture) => fixture.type === 'true-false');
const clozeFixture = fixtures.find((fixture) => fixture.type === 'cloze');
const matchUpFixture = fixtures.find((fixture) => fixture.type === 'match-up');

function rightColumn(container: HTMLElement): HTMLElement {
  const column = container.querySelector('[data-activity="match-right-column"]');
  if (!column) throw new Error('match-right-column not found');
  return column as HTMLElement;
}

function rightTileByText(container: HTMLElement, text: string): HTMLElement {
  return within(rightColumn(container)).getByRole('button', { name: text });
}

function leftTileByText(container: HTMLElement, text: string): HTMLElement {
  const column = container.querySelector('[data-activity="match-left-column"]');
  if (!column) throw new Error('match-left-column not found');
  return within(column as HTMLElement).getByRole('button', { name: text });
}

function allTiles(container: HTMLElement): HTMLElement[] {
  return [
    ...within(
      container.querySelector('[data-activity="match-left-column"]') as HTMLElement,
    ).getAllByRole('button'),
    ...within(rightColumn(container)).getAllByRole('button'),
  ];
}

function fillCloze(container: HTMLElement, blankIndex: number, value: string) {
  const select = container.querySelector(`select[data-blank-index="${blankIndex}"]`);
  if (!select) throw new Error(`cloze select for blank ${blankIndex} not found`);
  fireEvent.change(select, { target: { value } });
}

describe('player contract: envelope rendering and completion events', () => {
  test('renders the activity title as the region label and heading', () => {
    render(<ActivityPlayer activity={clozeFixture as LuActivityV1} isUkrainian />);

    expect(screen.getByRole('region', { name: 'Читання в контексті' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Читання в контексті' })).toBeInTheDocument();
  });

  test('falls back to the activity type as title when the envelope omits one', () => {
    const untitled = structuredClone(clozeFixture) as unknown as LuActivityV1;
    delete (untitled as Partial<LuActivityV1>).title;

    render(<ActivityPlayer activity={untitled} isUkrainian />);

    expect(screen.getByRole('region', { name: 'cloze' })).toBeInTheDocument();
  });

  test('emits a typed completion event for cloze after a full submission', () => {
    const onComplete = vi.fn();
    const { container } = render(
      <ActivityPlayer activity={clozeFixture as LuActivityV1} onComplete={onComplete} isUkrainian />,
    );

    fillCloze(container, 1, 'допомагає');
    fireEvent.click(screen.getByRole('button', { name: 'Перевірити' }));

    expect(onComplete).toHaveBeenCalledTimes(1);
    expect(onComplete).toHaveBeenCalledWith({
      activityId: 'golden-cloze',
      activityType: 'cloze',
    });
  });

  test('emits a typed completion event for match-up once every pair is connected', () => {
    const onComplete = vi.fn();
    const { container } = render(
      <ActivityPlayer activity={matchUpFixture as LuActivityV1} onComplete={onComplete} isUkrainian />,
    );

    expect(onComplete).not.toHaveBeenCalled();

    fireEvent.click(leftTileByText(container, 'пояснення'));
    fireEvent.click(rightTileByText(container, 'додатковий коментар'));
    expect(onComplete).not.toHaveBeenCalled();

    fireEvent.click(leftTileByText(container, 'відповідь'));
    fireEvent.click(rightTileByText(container, 'реакція на запитання'));

    expect(onComplete).toHaveBeenCalledTimes(1);
    expect(onComplete).toHaveBeenCalledWith({
      activityId: 'golden-match-up',
      activityType: 'match-up',
    });
  });
});

describe('player contract: payload mapping and answer_key separation', () => {
  test('maps cloze payload blank ids onto select data-blank-index markers', () => {
    const activity = structuredClone(clozeFixture) as unknown as LuActivityV1;
    activity.id = 'deep-map-cloze';
    activity.payload = {
      type: 'cloze',
      instruction: 'Виберіть слова.',
      text: 'Перше [___:2] і друге [___:5].',
      blanks: [
        { id: 2, answer: 'альфа', options: ['альфа', 'бета'] },
        { id: 5, answer: 'гамма', options: ['гамма', 'дельта'] },
      ],
    };

    const { container } = render(<ActivityPlayer activity={activity} isUkrainian />);

    const selects = [...container.querySelectorAll('select[data-blank-index]')];
    expect(selects.map((select) => select.getAttribute('data-blank-index'))).toEqual(['2', '5']);

    // Grading keys each selection to its mapped blank index, not to option order.
    fillCloze(container, 2, 'бета');
    fillCloze(container, 5, 'гамма');
    fireEvent.click(screen.getByRole('button', { name: 'Перевірити' }));

    const feedback = container.querySelector('[data-activity="cloze-feedback"]');
    expect(feedback).toBeInTheDocument();
    expect(feedback?.getAttribute('data-correct')).toBe('false');
  });

  test('grades true-false from the payload, never from answer_key', () => {
    const corrupted = structuredClone(trueFalseFixture) as unknown as LuActivityV1;
    (corrupted.answer_key as { items: Array<{ correct: boolean }> }).items[0].correct = false;

    const { container } = render(<ActivityPlayer activity={corrupted} />);

    fireEvent.click(screen.getByRole('button', { name: 'True' }));
    fireEvent.click(screen.getByRole('button', { name: 'Check Answers' }));

    const feedback = container.querySelector('[data-activity="tf-row-feedback"]');
    expect(feedback).toBeInTheDocument();
    expect(feedback?.getAttribute('data-correct')).toBe('true');
  });

  test('grades cloze from the payload, never from answer_key', () => {
    const corrupted = structuredClone(clozeFixture) as unknown as LuActivityV1;
    (corrupted.answer_key as { blanks: Array<{ answer: string }> }).blanks[0].answer = 'заважає';

    const { container } = render(<ActivityPlayer activity={corrupted} />);

    fillCloze(container, 1, 'допомагає');
    fireEvent.click(screen.getByRole('button', { name: 'Check Answers' }));

    const feedback = container.querySelector('[data-activity="cloze-feedback"]');
    expect(feedback).toBeInTheDocument();
    expect(feedback?.getAttribute('data-correct')).toBe('true');
  });
});

describe('player contract: content rendering', () => {
  test('renders true-false instruction, statement, and feedback explanation', () => {
    const { container } = render(
      <ActivityPlayer activity={trueFalseFixture as LuActivityV1} isUkrainian />,
    );

    expect(screen.getByText('Прочитайте твердження й оберіть правильну відповідь.')).toBeInTheDocument();
    expect(screen.getByText('Це навчальне твердження позначено як правдиве.')).toBeInTheDocument();

    fireEvent.click(screen.getAllByRole('button', { name: 'Правда' })[0]);
    fireEvent.click(screen.getByRole('button', { name: 'Перевірити' }));

    const feedback = container.querySelector('[data-activity="tf-row-feedback"]');
    expect(feedback?.textContent).toContain('У ключі для цього твердження вказано «правда».');
  });

  test('renders cloze instruction and passage text around each blank select', () => {
    const { container } = render(
      <ActivityPlayer activity={clozeFixture as LuActivityV1} isUkrainian />,
    );

    expect(screen.getByText('Виберіть слова, що доповнюють речення.')).toBeInTheDocument();

    const passage = container.querySelector('[data-activity="cloze-passage"] p');
    expect(passage?.textContent).toContain('Уважне читання');
    expect(passage?.textContent).toContain('зрозуміти зміст речення.');
    expect(container.querySelectorAll('select[data-activity="cloze-blank"]')).toHaveLength(1);
  });

  test('renders match-up instruction and every pair text on the board', () => {
    render(<ActivityPlayer activity={matchUpFixture as LuActivityV1} isUkrainian />);

    expect(screen.getByText("З'єднайте поняття з відповідним описом.")).toBeInTheDocument();
    for (const text of ['пояснення', 'відповідь', 'додатковий коментар', 'реакція на запитання']) {
      expect(screen.getByRole('button', { name: text })).toBeInTheDocument();
    }
  });
});

describe('ClozePassage in isolation', () => {
  const blanks = [
    { index: 1, answer: 'сонце', options: ['сонце', 'місяць'] },
    { index: 2, answer: 'зірки', options: ['зірки', 'хмари'] },
  ];

  test('keeps the submit button disabled until every blank is filled', () => {
    const { container } = render(<ClozePassage text="На небі [___:1] і [___:2]." blanks={blanks} />);

    const submit = screen.getByRole('button', { name: 'Check Answers' });
    expect(submit).toBeDisabled();

    fillCloze(container, 1, 'сонце');
    expect(submit).toBeDisabled();

    fillCloze(container, 2, 'зірки');
    expect(submit).toBeEnabled();
  });

  test('flags wrong selections and lists the correct answers on submit', () => {
    const { container } = render(<ClozePassage text="На небі [___:1] і [___:2]." blanks={blanks} />);

    fillCloze(container, 1, 'місяць');
    fillCloze(container, 2, 'зірки');
    fireEvent.click(screen.getByRole('button', { name: 'Check Answers' }));

    const feedback = container.querySelector('[data-activity="cloze-feedback"]');
    expect(feedback).toBeInTheDocument();
    expect(feedback?.getAttribute('data-correct')).toBe('false');
    expect(feedback?.textContent).toContain('✗ Some answers are incorrect. Correct answers:');
    expect(feedback?.textContent).toContain('сонце');
    expect(feedback?.textContent).toContain('зірки');

    const [firstBlank, secondBlank] = [
      ...container.querySelectorAll('select[data-activity="cloze-blank"]'),
    ];
    expect(firstBlank.className).toContain('incorrect');
    expect(secondBlank.className).toContain('correct');
    expect(firstBlank).toBeDisabled();
  });

  test('reset clears selections and feedback so the passage can be retried', () => {
    const { container } = render(<ClozePassage text="На небі [___:1] і [___:2]." blanks={blanks} />);

    fillCloze(container, 1, 'місяць');
    fillCloze(container, 2, 'хмари');
    fireEvent.click(screen.getByRole('button', { name: 'Check Answers' }));
    expect(container.querySelector('[data-activity="cloze-feedback"]')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Try Again' }));

    expect(container.querySelector('[data-activity="cloze-feedback"]')).not.toBeInTheDocument();
    const selects = [...container.querySelectorAll('select[data-activity="cloze-blank"]')];
    for (const select of selects) {
      expect(select).toBeEnabled();
      expect((select as HTMLSelectElement).value).toBe('');
    }
    expect(screen.getByRole('button', { name: 'Check Answers' })).toBeDisabled();
  });

  test('fires onComplete exactly once per submission', () => {
    const onComplete = vi.fn();
    const { container } = render(
      <ClozePassage text="На небі [___:1] і [___:2]." blanks={blanks} onComplete={onComplete} />,
    );

    fillCloze(container, 1, 'сонце');
    fillCloze(container, 2, 'зірки');
    fireEvent.click(screen.getByRole('button', { name: 'Check Answers' }));

    expect(onComplete).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole('button', { name: 'Try Again' }));
    fillCloze(container, 1, 'сонце');
    fillCloze(container, 2, 'зірки');
    fireEvent.click(screen.getByRole('button', { name: 'Check Answers' }));

    expect(onComplete).toHaveBeenCalledTimes(2);
  });
});

describe('TrueFalseQuestion in isolation', () => {
  test('shows correct feedback with the explanation after the right answer', () => {
    const { container } = render(
      <TrueFalseQuestion
        statement="Київ — столиця України."
        isTrue
        explanation="Київ є столицею з 1918 року."
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'True' }));

    const feedback = container.querySelector('[data-activity="tf-feedback"]');
    expect(feedback).toBeInTheDocument();
    expect(feedback?.getAttribute('data-correct')).toBe('true');
    expect(feedback?.textContent).toContain('✓ Correct!');
    expect(feedback?.textContent).toContain('Київ є столицею з 1918 року.');
  });

  test('reports the true/false verdict on a wrong answer and locks the buttons', () => {
    const { container } = render(
      <TrueFalseQuestion statement="Львів — столиця України." isTrue={false} />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'True' }));

    const feedback = container.querySelector('[data-activity="tf-feedback"]');
    expect(feedback?.getAttribute('data-correct')).toBe('false');
    expect(feedback?.textContent).toContain('✗ The statement is false.');
    expect(screen.getByRole('button', { name: 'True' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'False' })).toBeDisabled();
  });
});

describe('MatchUp onMatch in isolation', () => {
  const pairs = [
    { left: 'кіт', right: 'няв' },
    { left: 'пес', right: 'гав' },
    { left: 'корова', right: 'му' },
  ];

  test('rates a clean match good and reports a correct completion', () => {
    const onMatch = vi.fn();
    const onComplete = vi.fn();
    const { container } = render(
      <MatchUp pairs={pairs} onMatch={onMatch} onComplete={onComplete} />,
    );

    fireEvent.click(leftTileByText(container, 'кіт'));
    fireEvent.click(rightTileByText(container, 'няв'));

    expect(onMatch).toHaveBeenCalledTimes(1);
    expect(onMatch).toHaveBeenCalledWith(0, 'good');

    fireEvent.click(leftTileByText(container, 'пес'));
    fireEvent.click(rightTileByText(container, 'гав'));
    fireEvent.click(leftTileByText(container, 'корова'));
    fireEvent.click(rightTileByText(container, 'му'));

    expect(onMatch).toHaveBeenCalledTimes(3);
    expect(onComplete).toHaveBeenCalledTimes(1);
    expect(onComplete).toHaveBeenCalledWith(true);

    const feedback = container.querySelector('[data-activity="match-feedback"]');
    expect(feedback).toBeInTheDocument();
    expect(feedback?.getAttribute('data-correct')).toBe('true');
    for (const tile of allTiles(container)) {
      expect(tile.getAttribute('data-matched')).toBe('true');
    }
  });

  test('rates a match hard after one miss and again after two misses', () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    try {
      const onMatch = vi.fn();
      const onComplete = vi.fn();
      const { container } = render(
        <MatchUp pairs={pairs} onMatch={onMatch} onComplete={onComplete} />,
      );

      // Pair 1: two misses against still-unmatched right tiles → 'again'.
      fireEvent.click(leftTileByText(container, 'пес'));
      fireEvent.click(rightTileByText(container, 'му'));
      act(() => {
        vi.advanceTimersByTime(MISSHAKE_TIMEOUT_MS);
      });
      fireEvent.click(leftTileByText(container, 'пес'));
      fireEvent.click(rightTileByText(container, 'няв'));
      act(() => {
        vi.advanceTimersByTime(MISSHAKE_TIMEOUT_MS);
      });
      fireEvent.click(leftTileByText(container, 'пес'));
      fireEvent.click(rightTileByText(container, 'гав'));
      expect(onMatch).toHaveBeenCalledWith(1, 'again');

      // Pair 0: one miss before matching → 'hard'.
      fireEvent.click(leftTileByText(container, 'кіт'));
      fireEvent.click(rightTileByText(container, 'му'));
      act(() => {
        vi.advanceTimersByTime(MISSHAKE_TIMEOUT_MS);
      });
      fireEvent.click(leftTileByText(container, 'кіт'));
      fireEvent.click(rightTileByText(container, 'няв'));
      expect(onMatch).toHaveBeenCalledWith(0, 'hard');

      fireEvent.click(leftTileByText(container, 'корова'));
      fireEvent.click(rightTileByText(container, 'му'));

      expect(onComplete).toHaveBeenCalledTimes(1);
      expect(onComplete).toHaveBeenCalledWith(false);
    } finally {
      vi.useRealTimers();
    }
  });

  test('attributes ratings to the original pair index despite the shuffled right column', () => {
    const onMatch = vi.fn();
    const { container } = render(<MatchUp pairs={pairs} onMatch={onMatch} />);

    fireEvent.click(leftTileByText(container, 'корова'));
    fireEvent.click(rightTileByText(container, 'му'));

    expect(onMatch).toHaveBeenCalledWith(2, 'good');
  });
});

describe('Cloze legacy passage contract', () => {
  const legacyPassage = [
    'Учні [___:1] уважно.',
    '',
    '1. читають | пишуть',
    '   > [!answer] читають',
  ].join('\n');

  test('parses legacy embedded options from the passage and grades the marked answer', () => {
    const onComplete = vi.fn();
    const { container } = render(
      <Cloze passage={legacyPassage} onComplete={onComplete} isUkrainian />,
    );

    // The option block is stripped from the rendered passage text; the blank
    // marker is replaced by the select, so only the surrounding text nodes remain.
    const passage = container.querySelector('[data-activity="cloze-passage"] p');
    expect(passage?.firstChild?.textContent).toBe('Учні ');
    expect(passage?.lastChild?.textContent).toBe(' уважно.');
    expect(passage?.textContent).not.toContain('[!answer]');
    expect(passage?.textContent).not.toContain('1. читають');

    const select = container.querySelector('select[data-blank-index="1"]');
    expect(select).toBeInTheDocument();
    const optionValues = [...(select as HTMLSelectElement).options].map((option) => option.value);
    expect(new Set(optionValues)).toEqual(new Set(['', 'читають', 'пишуть']));

    fireEvent.change(select!, { target: { value: 'читають' } });
    fireEvent.click(screen.getByRole('button', { name: 'Перевірити' }));

    const feedback = container.querySelector('[data-activity="cloze-feedback"]');
    expect(feedback?.getAttribute('data-correct')).toBe('true');
    expect(onComplete).toHaveBeenCalledTimes(1);
  });

  test('provided blanks take precedence over embedded-option parsing', () => {
    const { container } = render(
      <Cloze
        passage={legacyPassage}
        blanks={[{ index: 1, answer: 'пишуть', options: ['пишуть', 'читають'] }]}
      />,
    );

    // With explicit blanks the passage is used verbatim, including the option block.
    const select = container.querySelector('select[data-blank-index="1"]');
    fireEvent.change(select!, { target: { value: 'пишуть' } });
    fireEvent.click(screen.getByRole('button', { name: 'Check Answers' }));

    const feedback = container.querySelector('[data-activity="cloze-feedback"]');
    expect(feedback?.getAttribute('data-correct')).toBe('true');
  });

  test('falls back to children when no passage is provided', () => {
    const { container } = render(
      <Cloze isUkrainian>
        <p data-testid="legacy-child">вкладений вміст</p>
      </Cloze>,
    );

    expect(screen.getByTestId('legacy-child')).toBeInTheDocument();
    expect(container.querySelector('[data-activity="cloze-passage"]')).not.toBeInTheDocument();
  });
});

describe('isUkrainian label and feedback switching', () => {
  test('switches cloze header, buttons, and feedback between Ukrainian and English', () => {
    const blanks = [{ index: 1, answer: 'сонце', options: ['сонце', 'місяць'] }];

    const ukrainian = render(
      <ClozePassage text="На небі [___:1]." blanks={blanks} isUkrainian />,
    );
    expect(screen.getByRole('button', { name: 'Перевірити' })).toBeInTheDocument();
    fillCloze(ukrainian.container, 1, 'місяць');
    fireEvent.click(screen.getByRole('button', { name: 'Перевірити' }));
    expect(
      ukrainian.container.querySelector('[data-activity="cloze-feedback"]')?.textContent,
    ).toContain('✗ Деякі відповіді неправильні. Правильні відповіді:');
    expect(screen.getByRole('button', { name: 'Спробувати знову' })).toBeInTheDocument();
    ukrainian.unmount();

    const english = render(<ClozePassage text="На небі [___:1]." blanks={blanks} />);
    expect(screen.getByRole('button', { name: 'Check Answers' })).toBeInTheDocument();
    fillCloze(english.container, 1, 'сонце');
    fireEvent.click(screen.getByRole('button', { name: 'Check Answers' }));
    expect(
      english.container.querySelector('[data-activity="cloze-feedback"]')?.textContent,
    ).toContain('✓ All answers are correct!');
    expect(screen.getByRole('button', { name: 'Try Again' })).toBeInTheDocument();
  });

  test('switches TrueFalseQuestion labels and verdict language', () => {
    const ukrainian = render(
      <TrueFalseQuestion statement="Два плюс два — чотири." isTrue isUkrainian />,
    );
    fireEvent.click(screen.getByRole('button', { name: 'Неправда' }));
    expect(
      ukrainian.container.querySelector('[data-activity="tf-feedback"]')?.textContent,
    ).toContain('✗ Це твердження правдиве.');
    ukrainian.unmount();

    const english = render(<TrueFalseQuestion statement="Два плюс два — чотири." isTrue />);
    fireEvent.click(screen.getByRole('button', { name: 'False' }));
    expect(
      english.container.querySelector('[data-activity="tf-feedback"]')?.textContent,
    ).toContain('✗ The statement is true.');
  });

  test('switches the match-up header between Ukrainian-only and bilingual', () => {
    const ukrainian = render(<MatchUp pairs={[{ left: 'а', right: '1' }]} isUkrainian />);
    expect(ukrainian.container.textContent).toContain('Знайдіть пару');
    expect(ukrainian.container.textContent).not.toContain('Match Up');
    ukrainian.unmount();

    const english = render(<MatchUp pairs={[{ left: 'а', right: '1' }]} />);
    expect(english.container.textContent).toContain('Знайдіть пару');
    expect(english.container.textContent).toContain('Match Up');
  });
});
