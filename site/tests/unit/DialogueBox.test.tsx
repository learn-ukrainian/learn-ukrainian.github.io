import React from 'react';
import { describe, expect, test } from 'vitest';
import { render, screen } from '@testing-library/react';
import { evaluate } from '@mdx-js/mdx';
import * as runtime from 'react/jsx-runtime';
import DialogueBox from '@site/src/components/DialogueBox';

const exchanges = [
  { speaker: 'First', text: 'Dialogue first' },
  { speaker: 'Second', text: 'Dialogue second' },
];

function expectTranslationAfterDialogue(container: HTMLElement) {
  const text = container.textContent!;
  expect(text.indexOf('English first')).toBeGreaterThan(text.indexOf('Dialogue second'));
  expect(text.indexOf('English second')).toBeGreaterThan(text.indexOf('English first'));
  expect(container.querySelectorAll('[class*="dialogueBubble"]')).toHaveLength(2);
}

describe('DialogueBox translations', () => {
  test('shows the complete English translation after all dialogue exchanges', () => {
    const { container } = render(<DialogueBox exchanges={exchanges} en={'English first\nEnglish second'} />);
    expectTranslationAfterDialogue(container);
    expect(screen.getByText(/English first/).style.whiteSpace).toBe('pre-line');
  });

  test('compiles the generated JSON-string payload and renders both translations', async () => {
    const source = `<DialogueBox\n  exchanges={JSON.parse('${JSON.stringify(exchanges)}')}\n  en={JSON.parse('"English first\\\\nEnglish second"')}\n/>`;
    const { default: Page } = await evaluate(source, { ...runtime });
    const { container } = render(<Page components={{ DialogueBox }} />);
    expectTranslationAfterDialogue(container);
  });

  test('omits the translation block when English support is absent', () => {
    const { container } = render(<DialogueBox exchanges={exchanges} />);
    expect(container.querySelector('[class*="dialogueTranslation"]')).toBeNull();
  });

  test('keeps existing one-line uk/en lessons working', () => {
    render(<DialogueBox uk="First: Dialogue first" en="English first" />);
    expect(screen.getByText('Dialogue first')).toBeInTheDocument();
    expect(screen.getByText('English first')).toBeInTheDocument();
  });

  test('renders English as text, including punctuation and HTML-looking content', () => {
    const en = '<img src=x onerror=alert(1)> "quoted" & safe';
    const { container } = render(<DialogueBox exchanges={exchanges} en={en} />);
    expect(screen.getByText(en)).toBeInTheDocument();
    expect(container.querySelector('img')).toBeNull();
  });
});
