import { describe, test, expect } from 'vitest';
import { render } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DivideWords from '@site/src/components/DivideWords';

// DivideWords renders one clickable "split" button between each grapheme of
// current.word, and compares the tapped split positions against the correct
// positions parsed from current.answer (hyphen, space, or middle dot as the
// syllable-break marker). A combining acute (U+0301, Ukrainian стрес) must
// stay attached to its base vowel as a single grapheme — it is never its own
// tap target.

function letterSpans(container: HTMLElement) {
  return [...container.querySelectorAll('[data-activity="divide-words-letter"]')];
}

function splitButtons(container: HTMLElement) {
  return [...container.querySelectorAll<HTMLButtonElement>('[data-activity="divide-words-split"]')];
}

function splitButtonAfter(container: HTMLElement, index: number) {
  const btn = splitButtons(container).find(
    (b) => b.getAttribute('data-split-index') === String(index),
  );
  if (!btn) throw new Error(`no split button after grapheme index ${index}`);
  return btn;
}

function submitBtn(container: HTMLElement) {
  return [...container.querySelectorAll('button')].find((b) => b.textContent === 'Перевірити')!;
}

function feedbackText(container: HTMLElement) {
  return container.textContent ?? '';
}

describe('DivideWords — grapheme-aware splitting', () => {
  test('word is rendered as one tap slot per grapheme, not per UTF-16 code unit', () => {
    const { container } = render(
      <DivideWords items={[{ word: 'рука́', answer: 'ру ка́' }]} />,
    );
    // "рука́" is 4 graphemes: р, у, к, а́ (а + combining acute) — the acute is
    // not a separate cell, so there are only 3 split buttons (between them).
    expect(letterSpans(container)).toHaveLength(4);
    expect(splitButtons(container)).toHaveLength(3);
  });

  test('combining acute on со́рок is not its own click slot', () => {
    const { container } = render(
      <DivideWords items={[{ word: 'со́рок', answer: 'со́ рок' }]} />,
    );
    // "со́рок" is 5 graphemes: с, о́, р, о, к → 4 split buttons.
    expect(letterSpans(container)).toHaveLength(5);
    expect(splitButtons(container)).toHaveLength(4);
  });

  test('space-separated answer "ру ка́" is accepted for рука́ split after "у"', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <DivideWords items={[{ word: 'рука́', answer: 'ру ка́' }]} />,
    );
    await user.click(splitButtonAfter(container, 2)); // after р,у
    await user.click(submitBtn(container));
    expect(feedbackText(container)).toContain('Правильно!');
  });

  test('hyphenated answer "ру-ка́" is also accepted for рука́ split after "у"', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <DivideWords items={[{ word: 'рука́', answer: 'ру-ка́' }]} />,
    );
    await user.click(splitButtonAfter(container, 2));
    await user.click(submitBtn(container));
    expect(feedbackText(container)).toContain('Правильно!');
  });

  test('молоко́ / "мо ло ко́" requires two splits, after мо and after ло', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <DivideWords items={[{ word: 'молоко́', answer: 'мо ло ко́' }]} />,
    );
    await user.click(splitButtonAfter(container, 2)); // after мо
    await user.click(splitButtonAfter(container, 4)); // after ло
    await user.click(submitBtn(container));
    expect(feedbackText(container)).toContain('Правильно!');
  });

  test('wrong split positions are marked incorrect', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <DivideWords items={[{ word: 'рука́', answer: 'ру ка́' }]} />,
    );
    await user.click(splitButtonAfter(container, 1)); // wrong: after р only
    await user.click(submitBtn(container));
    expect(feedbackText(container)).toContain('Правильно: ру ка́');
  });

  test('submit is allowed with zero splits for a one-syllable answer', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <DivideWords items={[{ word: 'рак', answer: 'рак' }]} />,
    );
    expect(submitBtn(container)).toBeEnabled();
    await user.click(submitBtn(container));
    expect(feedbackText(container)).toContain('Правильно!');
  });
});
