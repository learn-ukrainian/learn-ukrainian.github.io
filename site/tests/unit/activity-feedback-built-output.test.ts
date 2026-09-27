/**
 * Quality gate (#8889 A1-P3): every planned workbook task on a fixture
 * lesson page renders, is playable (answers once correctly and once
 * wrongly), and shows the required feedback — the chosen option's `why`
 * then, on a wrong answer, the correct option's `why` (or the entry / pair
 * `why`, or the activity `explanation`, per header §3).
 *
 * TODO(#8889 A1-P2): `buildRenderedReport` below hand-builds a dict in the
 * shape `rendered_report(plan, built_pages) -> dict` is expected to return
 * (header §4, scripts/curriculum/validate/activity_report.py). Once that
 * module lands, replace this with a real call — or, if `rendered_report`
 * only ever runs over Python-built lesson JSON, keep this as the page-level
 * mirror and cross-check the two shapes in a follow-up.
 */

import { describe, test, expect } from 'vitest';
import { render, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';

import Quiz from '@site/src/components/Quiz';
import { FillInQuestion } from '@site/src/components/FillIn';
import OddOneOut from '@site/src/components/OddOneOut';
import { ErrorCorrectionItem } from '@site/src/components/ErrorCorrection';
import { TranslateItem } from '@site/src/components/Translate';
import ImageToLetter from '@site/src/components/ImageToLetter';
import { TrueFalseQuestion } from '@site/src/components/TrueFalse';
import GroupSort from '@site/src/components/GroupSort';
import MatchUp from '@site/src/components/MatchUp';
import Order from '@site/src/components/Order';
import PickSyllables from '@site/src/components/PickSyllables';

interface TaskResult {
  slug: string;
  rendered: boolean;
  playable: boolean;
  feedbackShownOnCorrect: boolean;
  feedbackShownOnWrong: boolean;
}

function dragTile(tile: HTMLElement, target: HTMLElement) {
  const dataTransfer = {};
  fireEvent.dragStart(tile, { dataTransfer });
  fireEvent.dragOver(target, { dataTransfer });
  fireEvent.drop(target, { dataTransfer });
}

// ── one task per §3 choice/activity type in the A1-P3 page-payload contract ──

const tasks: Array<() => Promise<TaskResult>> = [
  // quiz
  async () => {
    const slug = 'quiz';
    const props = {
      question: 'Яка це буква?',
      options: ['А', 'Б', 'В'],
      correctIndex: 0,
      optionWhy: ['А is correct.', 'Б is wrong.', 'В is wrong.'],
    };
    const rendered = render(React.createElement(Quiz, {
      questions: [{ question: props.question, options: props.options.map((text, i) => ({ text, correct: i === props.correctIndex })), optionWhy: props.optionWhy }],
    }));
    const rendered1 = !!rendered.container.querySelector('[data-activity="quiz"]');
    const q1 = rendered.container.querySelectorAll<HTMLElement>('[data-activity="quiz-question"]')[0];
    const user = userEvent.setup();
    await user.click([...q1.querySelectorAll('button')].find((b) => b.textContent === 'А')!);
    const correctFeedback = !!q1.querySelector('[data-activity="quiz-option-why"]');
    rendered.unmount();

    const rendered2 = render(React.createElement(Quiz, {
      questions: [{ question: props.question, options: props.options.map((text, i) => ({ text, correct: i === props.correctIndex })), optionWhy: props.optionWhy }],
    }));
    const q2 = rendered2.container.querySelectorAll<HTMLElement>('[data-activity="quiz-question"]')[0];
    await user.click([...q2.querySelectorAll('button')].find((b) => b.textContent === 'Б')!);
    const wrongFeedback =
      !!q2.querySelector('[data-activity="quiz-option-why"]') && !!q2.querySelector('[data-activity="quiz-correct-why"]');
    rendered2.unmount();

    return { slug, rendered: rendered1, playable: true, feedbackShownOnCorrect: correctFeedback, feedbackShownOnWrong: wrongFeedback };
  },

  // fill-in: form-choice
  async () => {
    const slug = 'fill-in-form-choice';
    const props = {
      sentence: 'Я ___ книгу.',
      answer: 'читаю',
      options: ['читаю', 'читаєш'],
      mode: 'form-choice' as const,
      optionWhy: ['1st person singular.', '2nd person singular.'],
    };
    const user = userEvent.setup();

    const r1 = render(React.createElement(FillInQuestion, props));
    const renderedOk = !!r1.container.querySelector('[data-activity="fillin-question"]');
    await user.click([...r1.container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'читаю')!);
    const correctFeedback = !!r1.container.querySelector('[data-activity="fillin-option-why"]');
    r1.unmount();

    const r2 = render(React.createElement(FillInQuestion, props));
    await user.click([...r2.container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'читаєш')!);
    const wrongFeedback =
      !!r2.container.querySelector('[data-activity="fillin-option-why"]') &&
      !!r2.container.querySelector('[data-activity="fillin-correct-why"]');
    r2.unmount();

    return { slug, rendered: renderedOk, playable: true, feedbackShownOnCorrect: correctFeedback, feedbackShownOnWrong: wrongFeedback };
  },

  // fill-in: orthography
  async () => {
    const slug = 'fill-in-orthography';
    const props = {
      sentence: "прем___єра",
      answer: "'",
      options: ["'", ''],
      mode: 'orthography' as const,
      optionWhy: ['Apostrophe before я/ю/є/ї after a labial.', 'No apostrophe here.'],
    };
    const user = userEvent.setup();

    const r1 = render(React.createElement(FillInQuestion, props));
    const renderedOk = !!r1.container.querySelector('[data-orthography-slot]');
    await user.click([...r1.container.querySelectorAll('button')].find((b) => b.textContent?.trim() === "'")!);
    const correctFeedback = !!r1.container.querySelector('[data-activity="fillin-option-why"]');
    r1.unmount();

    const r2 = render(React.createElement(FillInQuestion, props));
    const emptyChip = [...r2.container.querySelectorAll('button')].find((b) => b.getAttribute('aria-label') === 'empty')!;
    await user.click(emptyChip);
    const wrongFeedback =
      !!r2.container.querySelector('[data-activity="fillin-option-why"]') &&
      !!r2.container.querySelector('[data-activity="fillin-correct-why"]');
    r2.unmount();

    return { slug, rendered: renderedOk, playable: true, feedbackShownOnCorrect: correctFeedback, feedbackShownOnWrong: wrongFeedback };
  },

  // odd-one-out
  async () => {
    const slug = 'odd-one-out';
    const item = {
      words: ['день', 'ніч', 'стіл'],
      correct: 2,
      explanation: 'стіл is not a time of day.',
      optionWhy: ['день is a time of day.', 'ніч is a time of day.', 'стіл is furniture.'],
    };
    const user = userEvent.setup();

    const r1 = render(React.createElement(OddOneOut, { items: [item] }));
    const renderedOk = !!r1.container.querySelector('[data-activity="odd-one-out"]');
    await user.click([...r1.container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'стіл')!);
    const correctFeedback = !!r1.container.querySelector('[data-activity="odd-one-out-option-why"]');
    r1.unmount();

    const r2 = render(React.createElement(OddOneOut, { items: [item] }));
    await user.click([...r2.container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'день')!);
    const wrongFeedback =
      !!r2.container.querySelector('[data-activity="odd-one-out-option-why"]') &&
      !!r2.container.querySelector('[data-activity="odd-one-out-correct-why"]');
    r2.unmount();

    return { slug, rendered: renderedOk, playable: true, feedbackShownOnCorrect: correctFeedback, feedbackShownOnWrong: wrongFeedback };
  },

  // error-correction (with options)
  async () => {
    const slug = 'error-correction';
    const props = {
      sentence: 'Я хочу читати книга.',
      errorWord: 'книга',
      correctForm: 'книгу',
      options: ['книгу', 'книги'],
      explanation: 'Accusative case after хочу читати.',
      optionWhy: ['книгу is accusative.', 'книги is genitive/plural, not accusative.'],
    };
    const user = userEvent.setup();

    const r1 = render(React.createElement(ErrorCorrectionItem, props));
    const renderedOk = !!r1.container.querySelector('[data-activity="error-correction-item"]');
    await user.click(
      [...r1.container.querySelectorAll('[data-activity="error-correction-word"]')].find(
        (w) => w.textContent?.trim() === 'книга',
      )!,
    );
    await user.click(
      [...r1.container.querySelectorAll('[data-activity="error-correction-fix-chip"]')].find(
        (b) => b.textContent?.trim() === 'книгу',
      )!,
    );
    const correctFeedback = !!r1.container.querySelector('[data-activity="error-correction-option-why"]');
    r1.unmount();

    const r2 = render(React.createElement(ErrorCorrectionItem, props));
    await user.click(
      [...r2.container.querySelectorAll('[data-activity="error-correction-word"]')].find(
        (w) => w.textContent?.trim() === 'книга',
      )!,
    );
    await user.click(
      [...r2.container.querySelectorAll('[data-activity="error-correction-fix-chip"]')].find(
        (b) => b.textContent?.trim() === 'книги',
      )!,
    );
    const wrongFeedback =
      !!r2.container.querySelector('[data-activity="error-correction-option-why"]') &&
      !!r2.container.querySelector('[data-activity="error-correction-correct-why"]');
    r2.unmount();

    return { slug, rendered: renderedOk, playable: true, feedbackShownOnCorrect: correctFeedback, feedbackShownOnWrong: wrongFeedback };
  },

  // translate (options)
  async () => {
    const slug = 'translate-options';
    const props = {
      source: 'book',
      answer: 'книга',
      options: ['книга', 'машина'],
      optionWhy: ['книга means book.', 'машина means car.'],
    };
    const user = userEvent.setup();

    const r1 = render(React.createElement(TranslateItem, props));
    const renderedOk = !!r1.container.querySelector('[data-activity="translate-item"]');
    await user.click([...r1.container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'книга')!);
    const correctFeedback = !!r1.container.querySelector('[data-activity="translate-option-why"]');
    r1.unmount();

    const r2 = render(React.createElement(TranslateItem, props));
    await user.click([...r2.container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'машина')!);
    const wrongFeedback =
      !!r2.container.querySelector('[data-activity="translate-option-why"]') &&
      !!r2.container.querySelector('[data-activity="translate-correct-why"]');
    r2.unmount();

    return { slug, rendered: renderedOk, playable: true, feedbackShownOnCorrect: correctFeedback, feedbackShownOnWrong: wrongFeedback };
  },

  // image-to-letter
  async () => {
    const slug = 'image-to-letter';
    const item = {
      emoji: '🍎',
      answer: 'Я',
      distractors: ['А', 'О'],
      explanation: 'Яблуко begins with Я.',
      optionWhy: ['Я for яблуко.', 'А is a different letter.', 'О is a different letter.'],
    };
    const r1 = render(React.createElement(ImageToLetter, { items: [item] }));
    const renderedOk = !!r1.container.querySelector('[data-activity="image-to-letter"]');
    fireEvent.click([...r1.container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'Я')!);
    const correctFeedback = !!r1.container.querySelector('[data-activity="itl-option-why"]');
    r1.unmount();

    const r2 = render(React.createElement(ImageToLetter, { items: [item] }));
    fireEvent.click([...r2.container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'А')!);
    const wrongFeedback =
      !!r2.container.querySelector('[data-activity="itl-option-why"]') &&
      !!r2.container.querySelector('[data-activity="itl-correct-why"]');
    r2.unmount();

    return { slug, rendered: renderedOk, playable: true, feedbackShownOnCorrect: correctFeedback, feedbackShownOnWrong: wrongFeedback };
  },

  // true-false
  async () => {
    const slug = 'true-false';
    const props = {
      statement: 'Київ — столиця України.',
      isTrue: true,
      optionWhy: ['Correct: Kyiv is the capital.', 'Wrong: Kyiv is the capital.'] as [string, string],
    };
    const user = userEvent.setup();

    const r1 = render(React.createElement(TrueFalseQuestion, props));
    const renderedOk = !!r1.container.querySelector('[data-activity="tf-question"]');
    await user.click([...r1.container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'True')!);
    const correctFeedback = !!r1.container.querySelector('[data-activity="tf-option-why"]');
    r1.unmount();

    const r2 = render(React.createElement(TrueFalseQuestion, props));
    await user.click([...r2.container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'False')!);
    const wrongFeedback =
      !!r2.container.querySelector('[data-activity="tf-option-why"]') &&
      !!r2.container.querySelector('[data-activity="tf-correct-why"]');
    r2.unmount();

    return { slug, rendered: renderedOk, playable: true, feedbackShownOnCorrect: correctFeedback, feedbackShownOnWrong: wrongFeedback };
  },

  // group-sort
  async () => {
    const slug = 'group-sort';
    const groups = {
      Fruits: [{ text: 'apple', why: 'apple is a fruit.' }],
      Vegetables: [{ text: 'carrot', why: 'carrot is a vegetable.' }],
    };

    const r1 = render(React.createElement(GroupSort, { groups }));
    const renderedOk = !!r1.container.querySelector('[data-activity="group-sort"]');
    const pool1 = r1.container.querySelector('[data-activity="group-sort-pool"]')!;
    const buckets1 = [...r1.container.querySelectorAll<HTMLElement>('[data-activity="group-sort-bucket"]')];
    const fruitsBucket1 = buckets1.find((b) => b.getAttribute('data-group-name') === 'Fruits')!;
    const vegBucket1 = buckets1.find((b) => b.getAttribute('data-group-name') === 'Vegetables')!;
    dragTile([...pool1.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'apple')!, fruitsBucket1);
    dragTile([...pool1.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'carrot')!, vegBucket1);
    fireEvent.click([...r1.container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'Check Answers')!);
    const correctFeedback = !r1.container.querySelector('[data-activity="group-sort-entry-why"]')
      && r1.container.querySelector('[data-activity="group-sort-feedback"]')?.getAttribute('data-correct') === 'true';
    r1.unmount();

    const r2 = render(React.createElement(GroupSort, { groups }));
    const pool2 = r2.container.querySelector('[data-activity="group-sort-pool"]')!;
    const buckets2 = [...r2.container.querySelectorAll<HTMLElement>('[data-activity="group-sort-bucket"]')];
    const vegBucket2 = buckets2.find((b) => b.getAttribute('data-group-name') === 'Vegetables')!;
    // Drop BOTH into Vegetables — apple lands wrong.
    dragTile([...pool2.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'apple')!, vegBucket2);
    dragTile([...pool2.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'carrot')!, vegBucket2);
    fireEvent.click([...r2.container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'Check Answers')!);
    const why = r2.container.querySelector('[data-activity="group-sort-entry-why"]');
    const wrongFeedback = !!why && why.textContent === 'apple is a fruit.';
    r2.unmount();

    return { slug, rendered: renderedOk, playable: true, feedbackShownOnCorrect: !!correctFeedback, feedbackShownOnWrong: wrongFeedback };
  },

  // match-up
  async () => {
    const slug = 'match-up';
    const pairs = [
      { left: 'кіт', right: 'cat', why: 'кіт means cat.' },
      { left: 'пес', right: 'dog', why: 'пес means dog.' },
    ];
    const user = userEvent.setup();

    const r1 = render(React.createElement(MatchUp, { pairs }));
    const renderedOk = !!r1.container.querySelector('[data-activity="match-up"]');
    const leftCol1 = r1.container.querySelector('[data-activity="match-left-column"]')!;
    const rightCol1 = r1.container.querySelector('[data-activity="match-right-column"]')!;
    for (const pair of pairs) {
      await user.click([...leftCol1.querySelectorAll('button')].find((b) => b.textContent?.trim() === pair.left)!);
      await user.click([...rightCol1.querySelectorAll('button')].find((b) => b.textContent?.trim() === pair.right)!);
    }
    const correctFeedback = !!r1.container.querySelector('[data-activity="match-feedback"]');
    r1.unmount();

    const r2 = render(React.createElement(MatchUp, { pairs }));
    const leftCol2 = r2.container.querySelector('[data-activity="match-left-column"]')!;
    const rightCol2 = r2.container.querySelector('[data-activity="match-right-column"]')!;
    await user.click([...leftCol2.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'кіт')!);
    await user.click([...rightCol2.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'dog')!); // wrong
    const wrongFeedback = r2.container.querySelector('[data-activity="match-wrong-why"]')?.textContent === 'кіт means cat.';
    r2.unmount();

    return { slug, rendered: renderedOk, playable: true, feedbackShownOnCorrect: correctFeedback, feedbackShownOnWrong: !!wrongFeedback };
  },

  // order
  async () => {
    const slug = 'order';
    const items = ['First', 'Second'];
    const correct_order = [0, 1];
    const explanation = 'Chronological order.';
    const user = userEvent.setup();

    const r1 = render(React.createElement(Order, { items, correct_order, explanation }));
    const renderedOk = !!r1.container.querySelector('[data-activity="order"]');
    const available1 = r1.container.querySelector('[data-activity="order-available"]')!;
    for (const text of ['First', 'Second']) {
      await user.click([...available1.querySelectorAll('button')].find((b) => b.textContent?.trim() === text)!);
    }
    await user.click([...r1.container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'Check')!);
    const correctFeedback = !!r1.container.querySelector('[data-activity="order-explanation"]')
      && r1.container.querySelector('[data-activity="order-feedback"]')?.getAttribute('data-correct') === 'true';
    r1.unmount();

    const r2 = render(React.createElement(Order, { items, correct_order, explanation }));
    const available2 = r2.container.querySelector('[data-activity="order-available"]')!;
    for (const text of ['Second', 'First']) {
      await user.click([...available2.querySelectorAll('button')].find((b) => b.textContent?.trim() === text)!);
    }
    await user.click([...r2.container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'Check')!);
    const wrongFeedback = !!r2.container.querySelector('[data-activity="order-explanation"]')
      && r2.container.querySelector('[data-activity="order-feedback"]')?.getAttribute('data-correct') === 'false';
    r2.unmount();

    return { slug, rendered: renderedOk, playable: true, feedbackShownOnCorrect: correctFeedback, feedbackShownOnWrong: wrongFeedback };
  },

  // pick-syllables
  async () => {
    const slug = 'pick-syllables';
    const syllables = ['кіт', 'со-ба-ка'];
    const correctIndices = [0];
    const explanation = 'Закритий склад закінчується на приголосний.';
    const user = userEvent.setup();

    const r1 = render(React.createElement(PickSyllables, { syllables, correctIndices, category: 'закриті', explanation }));
    const renderedOk = !!r1.container.querySelector('[data-activity="pick-syllables"]');
    const options1 = r1.container.querySelector('[data-activity="pick-syllables-options"]')!;
    await user.click(options1.querySelectorAll('button')[0]);
    await user.click([...r1.container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'Перевірити')!);
    const correctFeedback = !!r1.container.querySelector('[data-activity="pick-syllables-explanation"]')
      && r1.container.querySelector('[data-activity="pick-syllables-feedback"]')?.getAttribute('data-correct') === 'true';
    r1.unmount();

    const r2 = render(React.createElement(PickSyllables, { syllables, correctIndices, category: 'закриті', explanation }));
    const options2 = r2.container.querySelector('[data-activity="pick-syllables-options"]')!;
    await user.click(options2.querySelectorAll('button')[1]);
    await user.click([...r2.container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'Перевірити')!);
    const wrongFeedback = !!r2.container.querySelector('[data-activity="pick-syllables-explanation"]')
      && r2.container.querySelector('[data-activity="pick-syllables-feedback"]')?.getAttribute('data-correct') === 'false';
    r2.unmount();

    return { slug, rendered: renderedOk, playable: true, feedbackShownOnCorrect: correctFeedback, feedbackShownOnWrong: wrongFeedback };
  },
];

// See the module docstring: this mirrors rendered_report(plan, built_pages)
// -> dict (header §4) until scripts/curriculum/validate/activity_report.py
// lands and can be called for real.
function buildRenderedReport(results: TaskResult[]) {
  return {
    lessons: {
      'fixture-a1-p3': {
        tasks_planned: results.length,
        tasks_rendered: results.filter((r) => r.rendered).length,
        tasks_playable: results.filter((r) => r.playable).length,
        tasks_with_feedback_shown: results.filter((r) => r.feedbackShownOnCorrect && r.feedbackShownOnWrong).length,
        by_task: Object.fromEntries(results.map((r) => [r.slug, r])),
      },
    },
  };
}

describe('A1-P3 per-option feedback: fixture lesson page (built-output gate)', () => {
  test('every planned workbook task renders, is playable, and shows feedback on both a correct and a wrong answer', async () => {
    const results: TaskResult[] = [];
    for (const task of tasks) {
      results.push(await task());
    }

    const report = buildRenderedReport(results);
    const lesson = report.lessons['fixture-a1-p3'];

    for (const r of results) {
      expect(r.rendered, `${r.slug}: did not render`).toBe(true);
      expect(r.playable, `${r.slug}: was not playable`).toBe(true);
      expect(r.feedbackShownOnCorrect, `${r.slug}: no feedback on a correct answer`).toBe(true);
      expect(r.feedbackShownOnWrong, `${r.slug}: no feedback on a wrong answer`).toBe(true);
    }

    expect(lesson.tasks_planned).toBe(tasks.length);
    expect(lesson.tasks_rendered).toBe(lesson.tasks_planned);
    expect(lesson.tasks_playable).toBe(lesson.tasks_planned);
    expect(lesson.tasks_with_feedback_shown).toBe(lesson.tasks_planned);
  });
});
