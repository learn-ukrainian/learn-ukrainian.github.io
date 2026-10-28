import { describe, test, expect, beforeEach, vi } from 'vitest';
import React from 'react';
import { act } from 'react';
import { renderToString } from 'react-dom/server';
import { hydrateRoot } from 'react-dom/client';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Quiz, { QuizQuestion } from '@site/src/components/Quiz';
import FillIn, { FillInQuestion } from '@site/src/components/FillIn';
import Select, { SelectQuestion } from '@site/src/components/Select';
import Translate, { TranslateItem } from '@site/src/components/Translate';
import { ErrorCorrectionItem } from '@site/src/components/ErrorCorrection';
import OddOneOut from '@site/src/components/OddOneOut';
import { shuffle } from '@site/src/components/utils';

// Option lists are authored answer-first. Server output (and the first
// hydrating render) must not list them in source order; after hydration every
// attempt gets a fresh random order, and per-option feedback still follows the
// authored option.

const OPTION_SETS: string[][] = [
  ['рік', 'роки', 'років'],
  ['років', 'рік', 'роки'],
  ['97', '907', '0907'],
  ['один', 'одна', 'одне', 'одні'],
  ['так', 'ні'],
  ['в парку', 'в парк', 'до парку', 'з парку', 'біля парку'],
];

function html(node: React.ReactElement): HTMLElement {
  const host = document.createElement('div');
  host.innerHTML = renderToString(node);
  return host;
}

function texts(root: ParentNode, selector: string): string[] {
  return [...root.querySelectorAll(selector)].map((el) => el.textContent?.trim() ?? '');
}

const sourceOrder = (options: string[]) => options.join('|');

beforeEach(() => {
  document.documentElement.dataset.chromeLocale = 'en';
});

describe('shuffle', () => {
  test('never returns source order for two or more items', () => {
    for (let n = 2; n <= 8; n++) {
      for (let variant = 0; variant < 40; variant++) {
        const list = Array.from({ length: n }, (_, i) => `v${variant}-${i}`);
        expect(shuffle(list)).not.toEqual(list);
      }
    }
  });

  test('is deterministic for the same content', () => {
    expect(shuffle(['a', 'b', 'c'])).toEqual(shuffle(['a', 'b', 'c']));
  });

  test('passes single and empty lists through', () => {
    expect(shuffle(['a'])).toEqual(['a']);
    expect(shuffle([])).toEqual([]);
  });
});

describe('server-rendered output is never in source order', () => {
  test.each(OPTION_SETS)('QuizQuestion %s', (...options) => {
    const root = html(<QuizQuestion question="q" options={options} correctIndex={0} />);
    expect(texts(root, '[data-activity="quiz-options"] button')).not.toEqual(options);
    expect(new Set(texts(root, 'button'))).toEqual(new Set(options));
  });

  test.each(OPTION_SETS)('TranslateItem %s', (...options) => {
    const root = html(<TranslateItem source="s" answer={options[0]} options={options} />);
    expect(texts(root, '[data-activity="translate-options"] button')).not.toEqual(options);
  });

  test.each(OPTION_SETS)('SelectQuestion %s', (...options) => {
    const root = html(<SelectQuestion question="q" options={options} correctAnswers={[options[0]]} />);
    const rendered = texts(root, '[class*="checkboxLabel"]');
    expect(rendered).toHaveLength(options.length);
    expect(sourceOrder(rendered)).not.toBe(sourceOrder(options));
  });

  test.each(OPTION_SETS)('FillIn batch <select> %s', (...options) => {
    const root = html(<FillIn items={[{ sentence: 'a ___ b', answer: options[0], options }]} />);
    const rendered = texts(root, 'select option').slice(1); // drop the placeholder
    expect(rendered).toEqual(expect.arrayContaining(options));
    expect(rendered).not.toEqual(options);
  });

  test.each(OPTION_SETS)('FillIn chips %s', (...options) => {
    const root = html(
      <FillInQuestion sentence="a ___ b" answer={options[0]} options={options} mode="form-choice" />,
    );
    expect(texts(root, '[data-activity="fillin-chips"] button')).not.toEqual(options);
  });

  test('OddOneOut words', () => {
    const words = ['стіл', 'стілець', 'шафа', 'бігти'];
    const root = html(<OddOneOut items={[{ words, correct: 3, explanation: 'e' }]} />);
    const rendered = texts(root, '[data-activity="odd-one-out-options"] button');
    expect(new Set(rendered)).toEqual(new Set(words));
    expect(rendered).not.toEqual(words);
  });
});

describe('hydration', () => {
  test('hydrating server markup raises no mismatch error and keeps every option', async () => {
    const options = ['один', 'одна', 'одне', 'одні'];
    const element = <QuizQuestion question="q" options={options} correctIndex={0} />;
    const container = document.createElement('div');
    container.innerHTML = renderToString(element);
    document.body.appendChild(container);
    const errors = vi.spyOn(console, 'error').mockImplementation(() => {});

    await act(async () => {
      hydrateRoot(container, element);
    });

    expect(errors).not.toHaveBeenCalled();
    errors.mockRestore();
    const after = texts(container, '[data-activity="quiz-options"] button');
    expect(new Set(after)).toEqual(new Set(options));
    container.remove();
  });
});

describe('after hydration the correct answer moves between positions', () => {
  const options = ['один', 'одна', 'одне', 'одні'];

  test('two-option lists are not stuck in source order', () => {
    const seen = new Set<number>();
    for (let i = 0; i < 60; i++) {
      const { container, unmount } = render(<QuizQuestion question="q" options={['так', 'ні']} correctIndex={0} />);
      seen.add(texts(container, '[data-activity="quiz-options"] button').indexOf('так'));
      unmount();
    }
    expect([...seen].sort()).toEqual([0, 1]);
  });

  test('QuizQuestion spreads the answer across every position', () => {
    const seen = new Set<number>();
    for (let i = 0; i < 120; i++) {
      const { container, unmount } = render(<QuizQuestion question="q" options={options} correctIndex={0} />);
      seen.add(texts(container, '[data-activity="quiz-options"] button').indexOf(options[0]));
      unmount();
    }
    expect([...seen].sort()).toEqual([0, 1, 2, 3]);
  });

  test('TranslateItem shows a different order after every retry', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <TranslateItem source="s" answer={options[0]} options={options} />,
    );
    const order = () => texts(container, '[data-activity="translate-options"] button');
    let previous = order();
    for (let attempt = 0; attempt < 12; attempt++) {
      await user.click(screen.getByRole('button', { name: options[1] }));
      await user.click(screen.getByRole('button', { name: 'Try Again' }));
      const next = order();
      expect(new Set(next)).toEqual(new Set(options));
      expect(next).not.toEqual(previous);
      previous = next;
    }
  });

  test('SelectQuestion reshuffles on retry', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <SelectQuestion question="q" options={options} correctAnswers={[options[0]]} />,
    );
    const order = () => texts(container, '[class*="checkboxLabel"]');
    const before = order();
    await user.click(screen.getByText(options[0]));
    await user.click(screen.getByRole('button', { name: /check/i }));
    await user.click(screen.getByRole('button', { name: 'Try Again' }));
    expect(order()).not.toEqual(before);
  });

  test('FillIn batch selects reshuffle on retry, each blank independently', async () => {
    const user = userEvent.setup();
    const items = [
      { sentence: 'a ___', answer: options[0], options },
      { sentence: 'b ___', answer: options[0], options },
    ];
    const { container } = render(<FillIn items={items} />);
    const orders = () =>
      [...container.querySelectorAll('select')].map((s) => texts(s, 'option').slice(1).join('|'));
    const before = orders();
    for (const select of container.querySelectorAll('select')) {
      await user.selectOptions(select, options[0]);
    }
    await user.click(screen.getByRole('button', { name: 'Check Answers' }));
    await user.click(screen.getByRole('button', { name: 'Try Again' }));
    const after = orders();
    expect(after[0]).not.toBe(before[0]);
    expect(after[1]).not.toBe(before[1]);
  });

  test('ErrorCorrectionItem shows a different fix order after every retry', async () => {
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
    expect(new Set(previous)).toEqual(new Set(options.filter((o) => o !== 'помилка')));
    for (let attempt = 0; attempt < 10; attempt++) {
      await user.click(screen.getByRole('button', { name: 'роки' }));
      await user.click(screen.getByRole('button', { name: 'Try Again' }));
      await spot();
      const next = chips();
      expect(next).not.toEqual(previous);
      previous = next;
    }
  });

  test('OddOneOut shows a fresh order on replay', async () => {
    const user = userEvent.setup();
    const words = ['стіл', 'стілець', 'шафа', 'бігти'];
    const { container } = render(<OddOneOut items={[{ words, correct: 3, explanation: 'e' }]} />);
    const order = () => texts(container, '[data-activity="odd-one-out-options"] button');
    const before = order();
    await user.click(screen.getByRole('button', { name: 'бігти' }));
    await user.click(screen.getByRole('button', { name: 'Результат' }));
    await user.click(screen.getByRole('button', { name: 'Ще раз' }));
    expect(order()).not.toEqual(before);
  });
});

describe('scoring and per-option feedback follow the authored option', () => {
  test('Quiz maps feedback to the chosen option in any display order', async () => {
    const user = userEvent.setup();
    const options = ['рік', 'роки', 'років'];
    const optionWhy = ['why-0', 'why-1', 'why-2'];
    for (let i = 0; i < 10; i++) {
      const { container, unmount } = render(
        <QuizQuestion question="q" options={options} correctIndex={0} optionWhy={optionWhy} />,
      );
      await user.click(within(container).getByRole('button', { name: 'роки' }));
      expect(container.querySelector('[data-activity="quiz-option-why"]')?.textContent).toBe('why-1');
      expect(container.querySelector('[data-activity="quiz-correct-why"]')?.textContent).toBe('why-0');
      expect(container.querySelector('[data-activity="quiz-feedback"]')?.getAttribute('data-correct')).toBe('false');
      unmount();
    }
  });

  test('Quiz scores the authored correct option as correct', async () => {
    const user = userEvent.setup();
    const { container } = render(<QuizQuestion question="q" options={['рік', 'роки', 'років']} correctIndex={0} />);
    await user.click(within(container).getByRole('button', { name: 'рік' }));
    expect(container.querySelector('[data-activity="quiz-feedback"]')?.getAttribute('data-correct')).toBe('true');
  });

  test('FillIn chips and Translate keep their per-option feedback after a reshuffle', async () => {
    const user = userEvent.setup();
    const options = ['рік', 'роки', 'років'];
    const optionWhy = ['why-0', 'why-1', 'why-2'];
    const chips = render(
      <FillInQuestion sentence="a ___" answer="рік" options={options} optionWhy={optionWhy} mode="form-choice" />,
    );
    await user.click(screen.getByRole('button', { name: 'роки' }));
    expect(chips.container.querySelector('[data-activity="fillin-option-why"]')?.textContent).toBe('why-1');
    await user.click(screen.getByRole('button', { name: 'Try Again' }));
    await user.click(screen.getByRole('button', { name: 'років' }));
    expect(chips.container.querySelector('[data-activity="fillin-option-why"]')?.textContent).toBe('why-2');
    chips.unmount();

    const translate = render(
      <TranslateItem source="s" answer="рік" options={options} optionWhy={optionWhy} />,
    );
    await user.click(screen.getByRole('button', { name: 'роки' }));
    await user.click(screen.getByRole('button', { name: 'Try Again' }));
    await user.click(screen.getByRole('button', { name: 'років' }));
    expect(translate.container.textContent).toContain('why-2');
  });
});

describe('Quiz and Translate wrappers', () => {
  test('server markup of a wrapper question set never starts with the answer', () => {
    const questions = [
      { question: 'q1', options: [{ text: 'a1', correct: true }, { text: 'b1', correct: false }, { text: 'c1', correct: false }] },
      { question: 'q2', options: [{ text: 'a1', correct: true }, { text: 'b1', correct: false }, { text: 'c1', correct: false }] },
    ];
    const root = html(<Quiz questions={questions} />);
    for (const box of root.querySelectorAll('[data-activity="quiz-options"]')) {
      expect(texts(box, 'button')).not.toEqual(['a1', 'b1', 'c1']);
    }
    const translate = html(
      <Translate
        questions={[{ source: 's', options: questions[0].options }]}
      />,
    );
    expect(texts(translate, '[data-activity="translate-options"] button')).not.toEqual(['a1', 'b1', 'c1']);
  });
});
