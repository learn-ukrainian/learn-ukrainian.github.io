/**
 * #8889 A1-P3: per-option feedback across every §3 choice/activity type.
 *
 * For each type: a correct pick and a wrong pick, driven through real
 * events (click / keyboard), asserting the exact feedback text shown and
 * its order — the chosen option's `why` first, then (only when wrong) the
 * correct option's `why` — or the entry/pair `why` (group-sort, match-up),
 * or the activity `explanation` (order, pick-syllables).
 *
 * This is a component-fixture test (real DOM events against direct props),
 * not a built-output test: it does not build a lesson through the engine or
 * call `rendered_report`. That is A1-P3 part 2, after A1-P1 merges (header
 * §5 row, r3.2) — see docs/epics for the tracking item.
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

// Order in which the chosen-option `why` and the correct-option `why`
// appear relative to each other in the DOM (chosen first, correct second).
function assertOrder(chosenEl: Element | null, correctEl: Element | null) {
  expect(chosenEl).not.toBeNull();
  expect(correctEl).not.toBeNull();
  const position = chosenEl!.compareDocumentPosition(correctEl!);
  expect(position & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
}

function dragTile(tile: HTMLElement, target: HTMLElement) {
  const dataTransfer = {};
  fireEvent.dragStart(tile, { dataTransfer });
  fireEvent.dragOver(target, { dataTransfer });
  fireEvent.drop(target, { dataTransfer });
}

describe('quiz: per-option feedback', () => {
  const props = {
    question: 'Яка це буква?',
    options: ['А', 'Б', 'В'],
    correctIndex: 0,
    optionWhy: ['А is correct.', 'Б is wrong.', 'В is wrong.'],
  };
  const item = { question: props.question, options: props.options.map((text, i) => ({ text, correct: i === props.correctIndex })), optionWhy: props.optionWhy };

  test('a correct pick shows only the chosen (correct) why', async () => {
    const user = userEvent.setup();
    const { container } = render(<Quiz questions={[item]} />);
    await user.click([...container.querySelectorAll('button')].find((b) => b.textContent === 'А')!);
    expect(container.querySelector('[data-activity="quiz-option-why"]')?.textContent).toBe('А is correct.');
    expect(container.querySelector('[data-activity="quiz-correct-why"]')).not.toBeInTheDocument();
  });

  test('a wrong pick shows the chosen why, then the correct why', async () => {
    const user = userEvent.setup();
    const { container } = render(<Quiz questions={[item]} />);
    await user.click([...container.querySelectorAll('button')].find((b) => b.textContent === 'Б')!);
    const chosen = container.querySelector('[data-activity="quiz-option-why"]');
    const correct = container.querySelector('[data-activity="quiz-correct-why"]');
    expect(chosen?.textContent).toBe('Б is wrong.');
    expect(correct?.textContent).toBe('А is correct.');
    assertOrder(chosen, correct);
  });
});

describe('fill-in (form-choice): per-option feedback', () => {
  const props = {
    sentence: 'Я ___ книгу.',
    answer: 'читаю',
    options: ['читаю', 'читаєш'],
    mode: 'form-choice' as const,
    optionWhy: ['1st person singular.', '2nd person singular.'],
  };

  test('a correct pick shows only the chosen (correct) why', async () => {
    const user = userEvent.setup();
    const { container } = render(<FillInQuestion {...props} />);
    await user.click([...container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'читаю')!);
    expect(container.querySelector('[data-activity="fillin-option-why"]')?.textContent).toBe('1st person singular.');
    expect(container.querySelector('[data-activity="fillin-correct-why"]')).not.toBeInTheDocument();
  });

  test('a wrong pick shows the chosen why, then the correct why', async () => {
    const user = userEvent.setup();
    const { container } = render(<FillInQuestion {...props} />);
    await user.click([...container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'читаєш')!);
    const chosen = container.querySelector('[data-activity="fillin-option-why"]');
    const correct = container.querySelector('[data-activity="fillin-correct-why"]');
    expect(chosen?.textContent).toBe('2nd person singular.');
    expect(correct?.textContent).toBe('1st person singular.');
    assertOrder(chosen, correct);
  });
});

describe('fill-in (orthography): per-option feedback', () => {
  const props = {
    sentence: 'прем___єра',
    answer: "'",
    options: ["'", ''],
    mode: 'orthography' as const,
    optionWhy: ['Apostrophe before я/ю/є/ї after a labial.', 'No apostrophe here.'],
  };

  test('a correct pick shows only the chosen (correct) why', async () => {
    const user = userEvent.setup();
    const { container } = render(<FillInQuestion {...props} />);
    await user.click([...container.querySelectorAll('button')].find((b) => b.textContent?.trim() === "'")!);
    expect(container.querySelector('[data-activity="fillin-option-why"]')?.textContent).toBe(
      'Apostrophe before я/ю/є/ї after a labial.',
    );
    expect(container.querySelector('[data-activity="fillin-correct-why"]')).not.toBeInTheDocument();
  });

  test('a wrong pick shows the chosen why, then the correct why', async () => {
    const user = userEvent.setup();
    const { container } = render(<FillInQuestion {...props} />);
    const emptyChip = [...container.querySelectorAll('button')].find((b) => b.getAttribute('aria-label') === 'empty')!;
    await user.click(emptyChip);
    const chosen = container.querySelector('[data-activity="fillin-option-why"]');
    const correct = container.querySelector('[data-activity="fillin-correct-why"]');
    expect(chosen?.textContent).toBe('No apostrophe here.');
    expect(correct?.textContent).toBe('Apostrophe before я/ю/є/ї after a labial.');
    assertOrder(chosen, correct);
  });
});

describe('odd-one-out: per-word feedback', () => {
  const item = {
    words: ['день', 'ніч', 'стіл'],
    correct: 2,
    explanation: 'стіл is not a time of day.',
    optionWhy: ['день is a time of day.', 'ніч is a time of day.', 'стіл is furniture.'],
  };

  test('a correct pick shows only the chosen (correct) why', () => {
    const { container } = render(<OddOneOut items={[item]} />);
    fireEvent.click([...container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'стіл')!);
    expect(container.querySelector('[data-activity="odd-one-out-option-why"]')?.textContent).toBe('стіл is furniture.');
    expect(container.querySelector('[data-activity="odd-one-out-correct-why"]')).not.toBeInTheDocument();
  });

  test('a wrong pick shows the chosen why, then the correct why', () => {
    const { container } = render(<OddOneOut items={[item]} />);
    fireEvent.click([...container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'день')!);
    const chosen = container.querySelector('[data-activity="odd-one-out-option-why"]');
    const correct = container.querySelector('[data-activity="odd-one-out-correct-why"]');
    expect(chosen?.textContent).toBe('день is a time of day.');
    expect(correct?.textContent).toBe('стіл is furniture.');
    assertOrder(chosen, correct);
  });
});

describe('error-correction: per-option feedback', () => {
  const props = {
    sentence: 'Я хочу читати книга.',
    errorWord: 'книга',
    correctForm: 'книгу',
    options: ['книгу', 'книги'],
    explanation: 'Accusative case after хочу читати.',
    optionWhy: ['книгу is accusative.', 'книги is genitive/plural, not accusative.'],
  };

  async function pickFix(container: HTMLElement, user: ReturnType<typeof userEvent.setup>, fix: string) {
    await user.click(
      [...container.querySelectorAll('[data-activity="error-correction-word"]')].find(
        (w) => w.textContent?.trim() === 'книга',
      )!,
    );
    await user.click(
      [...container.querySelectorAll('[data-activity="error-correction-fix-chip"]')].find(
        (b) => b.textContent?.trim() === fix,
      )!,
    );
  }

  test('a correct pick shows only the chosen (correct) why', async () => {
    const user = userEvent.setup();
    const { container } = render(<ErrorCorrectionItem {...props} />);
    await pickFix(container, user, 'книгу');
    expect(container.querySelector('[data-activity="error-correction-option-why"]')?.textContent).toBe(
      'книгу is accusative.',
    );
    expect(container.querySelector('[data-activity="error-correction-correct-why"]')).not.toBeInTheDocument();
  });

  test('a wrong pick shows the chosen why, then the correct why', async () => {
    const user = userEvent.setup();
    const { container } = render(<ErrorCorrectionItem {...props} />);
    await pickFix(container, user, 'книги');
    const chosen = container.querySelector('[data-activity="error-correction-option-why"]');
    const correct = container.querySelector('[data-activity="error-correction-correct-why"]');
    expect(chosen?.textContent).toBe('книги is genitive/plural, not accusative.');
    expect(correct?.textContent).toBe('книгу is accusative.');
    assertOrder(chosen, correct);
  });
});

describe('translate (options): per-option feedback', () => {
  const props = {
    source: 'book',
    answer: 'книга',
    options: ['книга', 'машина'],
    optionWhy: ['книга means book.', 'машина means car.'],
  };

  test('a correct pick shows only the chosen (correct) why', async () => {
    const user = userEvent.setup();
    const { container } = render(<TranslateItem {...props} />);
    await user.click([...container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'книга')!);
    expect(container.querySelector('[data-activity="translate-option-why"]')?.textContent).toBe('книга means book.');
    expect(container.querySelector('[data-activity="translate-correct-why"]')).not.toBeInTheDocument();
  });

  test('a wrong pick shows the chosen why, then the correct why', async () => {
    const user = userEvent.setup();
    const { container } = render(<TranslateItem {...props} />);
    await user.click([...container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'машина')!);
    const chosen = container.querySelector('[data-activity="translate-option-why"]');
    const correct = container.querySelector('[data-activity="translate-correct-why"]');
    expect(chosen?.textContent).toBe('машина means car.');
    expect(correct?.textContent).toBe('книга means book.');
    assertOrder(chosen, correct);
  });
});

describe('image-to-letter: per-option feedback (payload order, header §3 r3.2)', () => {
  // Payload already reordered to {answer, distractors} with optionWhy
  // aligned to [answer, ...distractors] — the authored key was NOT option 0
  // (see tests/unit/ImageToLetter.test.tsx for the authored-order comment).
  const item = {
    emoji: '🍎',
    answer: 'Я',
    distractors: ['А', 'О'],
    explanation: 'Яблуко begins with Я.',
    optionWhy: ['Я for яблуко.', 'А is a different letter.', 'О is a different letter.'],
  };

  test('a correct pick shows only the chosen (correct) why', () => {
    const { container } = render(<ImageToLetter items={[item]} />);
    fireEvent.click([...container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'Я')!);
    expect(container.querySelector('[data-activity="itl-option-why"]')?.textContent).toBe('Я for яблуко.');
    expect(container.querySelector('[data-activity="itl-correct-why"]')).not.toBeInTheDocument();
  });

  test('a wrong pick shows that distractor\'s why, then the answer\'s why', () => {
    const { container } = render(<ImageToLetter items={[item]} />);
    fireEvent.click([...container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'А')!);
    const chosen = container.querySelector('[data-activity="itl-option-why"]');
    const correct = container.querySelector('[data-activity="itl-correct-why"]');
    expect(chosen?.textContent).toBe('А is a different letter.');
    expect(correct?.textContent).toBe('Я for яблуко.');
    assertOrder(chosen, correct);
  });
});

describe('true-false: per-pick feedback', () => {
  const props = {
    statement: 'Київ — столиця України.',
    isTrue: true,
    optionWhy: ['Correct: Kyiv is the capital.', 'Wrong: Kyiv is the capital.'] as [string, string],
  };

  test('a correct pick shows only the chosen (correct) why', async () => {
    const user = userEvent.setup();
    const { container } = render(<TrueFalseQuestion {...props} />);
    await user.click([...container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'True')!);
    expect(container.querySelector('[data-activity="tf-option-why"]')?.textContent).toBe('Correct: Kyiv is the capital.');
    expect(container.querySelector('[data-activity="tf-correct-why"]')).not.toBeInTheDocument();
  });

  test('a wrong pick shows the chosen why, then the correct why', async () => {
    const user = userEvent.setup();
    const { container } = render(<TrueFalseQuestion {...props} />);
    await user.click([...container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'False')!);
    const chosen = container.querySelector('[data-activity="tf-option-why"]');
    const correct = container.querySelector('[data-activity="tf-correct-why"]');
    expect(chosen?.textContent).toBe('Wrong: Kyiv is the capital.');
    expect(correct?.textContent).toBe('Correct: Kyiv is the capital.');
    assertOrder(chosen, correct);
  });
});

describe('group-sort: per-entry wrong-placement why', () => {
  const groups = {
    Fruits: [{ text: 'apple', why: 'apple is a fruit.' }],
    Vegetables: [{ text: 'carrot', why: 'carrot is a vegetable.' }],
  };

  function wordTiles(scope: Element) {
    return [...scope.querySelectorAll<HTMLButtonElement>('button')].filter(
      (b) => b.textContent?.trim() && !b.textContent?.trim().startsWith('Check') && !b.textContent?.trim().startsWith('Try'),
    );
  }

  test('correct placement of both entries shows no entry why', () => {
    const { container } = render(<GroupSort groups={groups} />);
    const pool = container.querySelector('[data-activity="group-sort-pool"]')!;
    const buckets = [...container.querySelectorAll<HTMLElement>('[data-activity="group-sort-bucket"]')];
    const fruitsBucket = buckets.find((b) => b.getAttribute('data-group-name') === 'Fruits')!;
    const vegBucket = buckets.find((b) => b.getAttribute('data-group-name') === 'Vegetables')!;
    dragTile(wordTiles(pool).find((t) => t.textContent?.trim() === 'apple')!, fruitsBucket);
    dragTile(wordTiles(pool).find((t) => t.textContent?.trim() === 'carrot')!, vegBucket);
    fireEvent.click([...container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'Check Answers')!);

    expect(container.querySelector('[data-activity="group-sort-entry-why"]')).not.toBeInTheDocument();
    expect(container.querySelector('[data-activity="group-sort-feedback"]')?.getAttribute('data-correct')).toBe('true');
  });

  test('a wrong placement shows that entry\'s why', () => {
    const { container } = render(<GroupSort groups={groups} />);
    const pool = container.querySelector('[data-activity="group-sort-pool"]')!;
    const buckets = [...container.querySelectorAll<HTMLElement>('[data-activity="group-sort-bucket"]')];
    const vegBucket = buckets.find((b) => b.getAttribute('data-group-name') === 'Vegetables')!;
    // Both dropped into Vegetables — apple lands wrong.
    dragTile(wordTiles(pool).find((t) => t.textContent?.trim() === 'apple')!, vegBucket);
    dragTile(wordTiles(pool).find((t) => t.textContent?.trim() === 'carrot')!, vegBucket);
    fireEvent.click([...container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'Check Answers')!);

    expect(container.querySelector('[data-activity="group-sort-entry-why"]')?.textContent).toBe('apple is a fruit.');
  });
});

describe('match-up: wrong-pair why', () => {
  const pairs = [
    { left: 'кіт', right: 'cat', why: 'кіт means cat.' },
    { left: 'пес', right: 'dog', why: 'пес means dog.' },
  ];

  test('matching every pair correctly shows the success feedback', async () => {
    const user = userEvent.setup();
    const { container } = render(<MatchUp pairs={pairs} />);
    const leftCol = container.querySelector('[data-activity="match-left-column"]')!;
    const rightCol = container.querySelector('[data-activity="match-right-column"]')!;
    for (const pair of pairs) {
      await user.click([...leftCol.querySelectorAll('button')].find((b) => b.textContent?.trim() === pair.left)!);
      await user.click([...rightCol.querySelectorAll('button')].find((b) => b.textContent?.trim() === pair.right)!);
    }
    expect(container.querySelector('[data-activity="match-feedback"]')).toBeInTheDocument();
  });

  test('a wrong pairing attempt shows that pair\'s why', async () => {
    const user = userEvent.setup();
    const { container } = render(<MatchUp pairs={pairs} />);
    const leftCol = container.querySelector('[data-activity="match-left-column"]')!;
    const rightCol = container.querySelector('[data-activity="match-right-column"]')!;
    await user.click([...leftCol.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'кіт')!);
    await user.click([...rightCol.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'dog')!); // wrong
    expect(container.querySelector('[data-activity="match-wrong-why"]')?.textContent).toBe('кіт means cat.');
  });
});

describe('order: activity explanation after checking', () => {
  const items = ['First', 'Second'];
  const correct_order = [0, 1];
  const explanation = 'Chronological order.';

  test('correct order shows the explanation with correct feedback', async () => {
    const user = userEvent.setup();
    const { container } = render(<Order items={items} correct_order={correct_order} explanation={explanation} />);
    const available = container.querySelector('[data-activity="order-available"]')!;
    for (const text of ['First', 'Second']) {
      await user.click([...available.querySelectorAll('button')].find((b) => b.textContent?.trim() === text)!);
    }
    await user.click([...container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'Check')!);
    expect(container.querySelector('[data-activity="order-feedback"]')?.getAttribute('data-correct')).toBe('true');
    expect(container.querySelector('[data-activity="order-explanation"]')?.textContent).toBe(explanation);
  });

  test('wrong order shows the explanation with incorrect feedback', async () => {
    const user = userEvent.setup();
    const { container } = render(<Order items={items} correct_order={correct_order} explanation={explanation} />);
    const available = container.querySelector('[data-activity="order-available"]')!;
    for (const text of ['Second', 'First']) {
      await user.click([...available.querySelectorAll('button')].find((b) => b.textContent?.trim() === text)!);
    }
    await user.click([...container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'Check')!);
    expect(container.querySelector('[data-activity="order-feedback"]')?.getAttribute('data-correct')).toBe('false');
    expect(container.querySelector('[data-activity="order-explanation"]')?.textContent).toBe(explanation);
  });
});

describe('pick-syllables: activity explanation after checking', () => {
  const syllables = ['кіт', 'со-ба-ка'];
  const correctIndices = [0];
  const explanation = 'Закритий склад закінчується на приголосний.';

  test('correct picks show the explanation with correct feedback', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <PickSyllables syllables={syllables} correctIndices={correctIndices} category="закриті" explanation={explanation} />,
    );
    const options = container.querySelector('[data-activity="pick-syllables-options"]')!;
    await user.click(options.querySelectorAll('button')[0]);
    await user.click([...container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'Перевірити')!);
    expect(container.querySelector('[data-activity="pick-syllables-feedback"]')?.getAttribute('data-correct')).toBe('true');
    expect(container.querySelector('[data-activity="pick-syllables-explanation"]')?.textContent).toBe(explanation);
  });

  test('wrong picks show the explanation with incorrect feedback', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <PickSyllables syllables={syllables} correctIndices={correctIndices} category="закриті" explanation={explanation} />,
    );
    const options = container.querySelector('[data-activity="pick-syllables-options"]')!;
    await user.click(options.querySelectorAll('button')[1]);
    await user.click([...container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'Перевірити')!);
    expect(container.querySelector('[data-activity="pick-syllables-feedback"]')?.getAttribute('data-correct')).toBe('false');
    expect(container.querySelector('[data-activity="pick-syllables-explanation"]')?.textContent).toBe(explanation);
  });
});
