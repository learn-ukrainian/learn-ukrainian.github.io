import { describe, test, expect, vi } from 'vitest';
import React from 'react';
import { act } from 'react';
import { renderToString } from 'react-dom/server';
import { hydrateRoot } from 'react-dom/client';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import KitMatchUp from '../../../packages/activity-kit/src/components/MatchUp';
import KitCloze, { ClozePassage } from '../../../packages/activity-kit/src/components/Cloze';
import KitQuiz, { QuizQuestion } from '../../../packages/activity-kit/src/components/Quiz';
import KitFillIn, { FillInQuestion } from '../../../packages/activity-kit/src/components/FillIn';
import { ErrorCorrectionItem } from '../../../packages/activity-kit/src/components/ErrorCorrection';
import { seededShuffle, shuffle } from '../../../packages/activity-kit/src/components/utils';

// The shared activity-kit components must behave like the site components: option
// lists are authored answer-first, so server output is never in source order, and
// after hydration every load and retry draws a fresh random order. Scoring and
// per-option feedback still follow the authored option.

const PAIRS = [
  { left: 'a1', right: 'відповідь' },
  { left: 'b2', right: 'друге' },
  { left: 'c3', right: 'третє' },
  { left: 'd4', right: 'четверте' },
];
const PAIR_RIGHTS = PAIRS.map((p) => p.right);

function html(node: React.ReactElement): HTMLElement {
  const host = document.createElement('div');
  host.innerHTML = renderToString(node);
  return host;
}

function texts(root: ParentNode, selector: string): string[] {
  return [...root.querySelectorAll(selector)].map((el) => el.textContent?.trim() ?? '');
}

const rightOrder = (root: ParentNode) => texts(root, '[data-activity="match-right-tile"]');

describe('shuffle helpers in the package', () => {
  test('shuffle never returns source order for two or more distinct items', () => {
    for (let n = 2; n <= 8; n++) {
      for (let variant = 0; variant < 30; variant++) {
        const list = Array.from({ length: n }, (_, i) => `v${variant}-${i}`);
        expect(shuffle(list)).not.toEqual(list);
      }
    }
  });

  test('seededShuffle is the plain content-seeded permutation', () => {
    const list = ['a', 'b', 'c', 'd'];
    expect(seededShuffle(list)).toEqual(seededShuffle([...list]));
    expect([...seededShuffle(list)].sort()).toEqual(list);
  });
});

describe('server output is never in source order', () => {
  test('MatchUp right column', () => {
    expect(rightOrder(html(<KitMatchUp pairs={PAIRS} />))).not.toEqual(PAIR_RIGHTS);
    expect(rightOrder(html(<KitMatchUp pairs={PAIRS.slice(0, 2)} />))).not.toEqual(PAIR_RIGHTS.slice(0, 2));
  });

  test('Cloze selects', () => {
    const options = ['рік', 'роки', 'років'];
    const root = html(
      <ClozePassage text="Один [___:1]." blanks={[{ index: 1, options, answer: options[0] }]} />,
    );
    const rendered = texts(root, 'select option').slice(1);
    expect(new Set(rendered)).toEqual(new Set(options));
    expect(rendered).not.toEqual(options);
  });

  test('Quiz, FillIn chips, FillIn selects and ErrorCorrection chips', () => {
    const options = ['один', 'одна', 'одне', 'одні'];
    const quiz = html(<QuizQuestion question="q" options={options} correctIndex={0} />);
    expect(texts(quiz, '[data-activity="quiz-options"] button')).not.toEqual(options);

    const chips = html(<FillInQuestion sentence="a ___ b" answer={options[0]} options={options} />);
    expect(texts(chips, '[data-activity="fillin-chips"] button')).not.toEqual(options);

    const selects = html(<KitFillIn items={[{ sentence: 'a ___ b', answer: options[0], options }]} />);
    expect(texts(selects, 'select option').slice(1)).not.toEqual(options);
  });
});

describe('hydration', () => {
  test.each([
    ['MatchUp', <KitMatchUp pairs={PAIRS} />, '[data-activity="match-right-tile"]'],
    [
      'Cloze',
      <ClozePassage text="x [___:1]" blanks={[{ index: 1, options: ['aa', 'bb', 'cc'], answer: 'aa' }]} />,
      'select option',
    ],
  ])('%s hydrates server markup without a mismatch and keeps every option', async (_name, element, selector) => {
    const container = document.createElement('div');
    container.innerHTML = renderToString(element);
    document.body.appendChild(container);
    const before = texts(container, selector).sort();
    const errors = vi.spyOn(console, 'error').mockImplementation(() => {});

    await act(async () => {
      hydrateRoot(container, element);
    });

    expect(errors).not.toHaveBeenCalled();
    errors.mockRestore();
    expect(texts(container, selector).sort()).toEqual(before);
    container.remove();
  });
});

describe('after hydration the displayed position varies', () => {
  test('MatchUp spreads the first pair’s right tile across every position', () => {
    const seen = new Set<number>();
    for (let i = 0; i < 120; i++) {
      const { container, unmount } = render(<KitMatchUp pairs={PAIRS} />);
      seen.add(rightOrder(container).indexOf(PAIRS[0].right));
      unmount();
    }
    expect([...seen].sort()).toEqual([0, 1, 2, 3]);
  });

  test('two-pair MatchUp is not stuck in one order', () => {
    const seen = new Set<string>();
    for (let i = 0; i < 60; i++) {
      const { container, unmount } = render(<KitMatchUp pairs={PAIRS.slice(0, 2)} />);
      seen.add(rightOrder(container).join('|'));
      unmount();
    }
    expect(seen.size).toBe(2);
  });

  test('Cloze spreads the answer across every position', () => {
    const options = ['рік', 'роки', 'років'];
    const seen = new Set<number>();
    for (let i = 0; i < 90; i++) {
      const { container, unmount } = render(
        <ClozePassage text="Один [___:1]." blanks={[{ index: 1, options, answer: options[0] }]} />,
      );
      seen.add(texts(container, 'select option').slice(1).indexOf(options[0]));
      unmount();
    }
    expect([...seen].sort()).toEqual([0, 1, 2]);
  });

  test('Cloze draws each blank’s order independently', () => {
    const options = ['aa', 'bb', 'cc', 'dd'];
    const blanks = [
      { index: 1, options, answer: 'aa' },
      { index: 2, options, answer: 'aa' },
    ];
    let differed = false;
    for (let i = 0; i < 30 && !differed; i++) {
      const { container, unmount } = render(<ClozePassage text="[___:1] [___:2]" blanks={blanks} />);
      const [first, second] = [...container.querySelectorAll('select')].map((s) =>
        texts(s, 'option').slice(1).join('|'),
      );
      differed = first !== second;
      unmount();
    }
    expect(differed).toBe(true);
  });

  test('Quiz spreads the answer across every position', () => {
    const options = ['один', 'одна', 'одне', 'одні'];
    const seen = new Set<number>();
    for (let i = 0; i < 120; i++) {
      const { container, unmount } = render(<QuizQuestion question="q" options={options} correctIndex={0} />);
      seen.add(texts(container, '[data-activity="quiz-options"] button').indexOf(options[0]));
      unmount();
    }
    expect([...seen].sort()).toEqual([0, 1, 2, 3]);
  });
});

describe('every retry shows a different order', () => {
  test('Cloze', async () => {
    const user = userEvent.setup();
    const options = ['aa', 'bb', 'cc', 'dd'];
    const { container } = render(
      <ClozePassage text="x [___:1]" blanks={[{ index: 1, options, answer: 'aa' }]} />,
    );
    const order = () => texts(container, 'select option').slice(1);
    let previous = order();
    for (let attempt = 0; attempt < 12; attempt++) {
      await user.selectOptions(container.querySelector('select')!, 'bb');
      await user.click(screen.getByRole('button', { name: 'Check Answers' }));
      await user.click(screen.getByRole('button', { name: 'Try Again' }));
      const next = order();
      expect(new Set(next)).toEqual(new Set(options));
      expect(next).not.toEqual(previous);
      previous = next;
    }
  });

  test('FillIn chips and FillIn selects', async () => {
    const user = userEvent.setup();
    const options = ['рік', 'роки', 'років'];

    const chips = render(<FillInQuestion sentence="a ___" answer="рік" options={options} />);
    const chipOrder = () => texts(chips.container, '[data-activity="fillin-chips"] button');
    let previous = chipOrder();
    for (let attempt = 0; attempt < 10; attempt++) {
      await user.click(screen.getByRole('button', { name: 'роки' }));
      await user.click(screen.getByRole('button', { name: 'Try Again' }));
      const next = chipOrder();
      expect(next).not.toEqual(previous);
      previous = next;
    }
    chips.unmount();

    const batch = render(
      <KitFillIn items={[{ sentence: 'a ___', answer: 'рік', options }, { sentence: 'b ___', answer: 'рік', options }]} />,
    );
    const orders = () =>
      [...batch.container.querySelectorAll('select')].map((s) => texts(s, 'option').slice(1).join('|'));
    const before = orders();
    for (const select of batch.container.querySelectorAll('select')) {
      await user.selectOptions(select, 'рік');
    }
    await user.click(screen.getByRole('button', { name: 'Check Answers' }));
    await user.click(screen.getByRole('button', { name: 'Try Again' }));
    const after = orders();
    expect(after[0]).not.toBe(before[0]);
    expect(after[1]).not.toBe(before[1]);
  });

  test('ErrorCorrection fix chips', async () => {
    const user = userEvent.setup();
    const options = ['рік', 'роки', 'років'];
    const { container } = render(
      <ErrorCorrectionItem sentence="тут помилка" errorWord="помилка" correctForm="рік" options={options} explanation="e" />,
    );
    const chips = () => texts(container, '[data-activity="error-correction-fix-chip"]');
    const spot = async () => {
      const word = [...container.querySelectorAll('[data-activity="error-correction-word"]')].find(
        (el) => el.textContent?.trim() === 'помилка',
      );
      await user.click(word as Element);
    };
    await spot();
    let previous = chips();
    for (let attempt = 0; attempt < 10; attempt++) {
      await user.click(screen.getByRole('button', { name: 'роки' }));
      await user.click(screen.getByRole('button', { name: 'Try Again' }));
      await spot();
      const next = chips();
      expect(new Set(next)).toEqual(new Set(options));
      expect(next).not.toEqual(previous);
      previous = next;
    }
  });
});

describe('scoring and feedback follow the authored option', () => {
  test('MatchUp matches by authored pair wherever the tile lands, and a wrong pick shows that pair’s why', async () => {
    const user = userEvent.setup();
    const pairs = PAIRS.map((p, i) => ({ ...p, why: `why-${i}` }));
    const onComplete = vi.fn();
    for (let round = 0; round < 6; round++) {
      onComplete.mockClear();
      const { container, unmount } = render(<KitMatchUp pairs={pairs} onComplete={onComplete} />);
      const left = (i: number) => within(container).getAllByRole('button').find((b) => b.getAttribute('data-original-index') === String(i) && b.getAttribute('data-activity') === 'match-left-tile')!;
      const right = (text: string) =>
        [...container.querySelectorAll('[data-activity="match-right-tile"]')].find((el) => el.textContent?.trim() === text) as HTMLElement;

      await user.click(left(0));
      await user.click(right('друге'));
      expect(container.querySelector('[data-activity="match-wrong-why"]')?.textContent).toBe('why-0');
      await new Promise((resolve) => setTimeout(resolve, 300));

      for (let i = 0; i < pairs.length; i++) {
        await user.click(left(i));
        await user.click(right(pairs[i].right));
      }
      expect(container.querySelector('[data-activity="match-feedback"]')?.getAttribute('data-correct')).toBe('true');
      expect(onComplete).toHaveBeenCalledWith(false); // a wrong attempt was made
      unmount();
    }
  });

  test('Cloze scores the authored answer in any order', async () => {
    const user = userEvent.setup();
    for (let round = 0; round < 6; round++) {
      const { container, unmount } = render(
        <ClozePassage text="Один [___:1]." blanks={[{ index: 1, options: ['рік', 'роки', 'років'], answer: 'рік' }]} />,
      );
      await user.selectOptions(container.querySelector('select')!, 'рік');
      await user.click(screen.getByRole('button', { name: 'Check Answers' }));
      expect(container.querySelector('[data-activity="cloze-feedback"]')?.getAttribute('data-correct')).toBe('true');
      unmount();
    }
  });

  test('Quiz scores the authored correct option in any order', async () => {
    const user = userEvent.setup();
    for (let round = 0; round < 6; round++) {
      const right = render(<QuizQuestion question="q" options={['рік', 'роки', 'років']} correctIndex={0} />);
      await user.click(within(right.container).getByRole('button', { name: 'рік' }));
      expect(right.container.querySelector('[data-activity="quiz-feedback"]')?.getAttribute('data-correct')).toBe('true');
      right.unmount();
      const wrong = render(<QuizQuestion question="q" options={['рік', 'роки', 'років']} correctIndex={0} />);
      await user.click(within(wrong.container).getByRole('button', { name: 'роки' }));
      expect(wrong.container.querySelector('[data-activity="quiz-feedback"]')?.getAttribute('data-correct')).toBe('false');
      wrong.unmount();
    }
  });

  test('wrapper components render', () => {
    expect(render(<KitCloze passage="x [___:1]" blanks={[{ index: 1, options: ['aa', 'bb'], answer: 'aa' }]} />).container.querySelectorAll('select option')).toHaveLength(3);
    expect(render(<KitQuiz questions={[{ question: 'q', options: [{ text: 'a', correct: true }, { text: 'b', correct: false }] }]} />).container.querySelectorAll('[data-activity="quiz-options"] button')).toHaveLength(2);
  });
});
