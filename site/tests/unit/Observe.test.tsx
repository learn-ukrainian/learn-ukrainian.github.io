import React from 'react';
import { describe, test, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { evaluate } from '@mdx-js/mdx';
import * as runtime from 'react/jsx-runtime';
import { readFileSync } from 'node:fs';
import Observe, { ObserveActivity } from '@site/src/components/Observe';
import Classify from '@site/src/components/Classify';
import LetterGrid from '@site/src/components/LetterGrid';
import PhraseTable from '@site/src/components/PhraseTable';

const instruction = 'Compare the examples.';
const examples = ['first', 'second'];

function expectInstruction(container: HTMLElement) {
  const text = screen.getByText(instruction, { selector: 'strong' });
  expect(text.tagName).toBe('STRONG');
  expect(text.parentElement?.tagName).toBe('P');
  expect(text.parentElement?.className).toContain('instruction');
  expect(container.querySelectorAll('p[class*="instruction"]')).toHaveLength(1);
}

describe('Observe instructions', () => {
  test('named activity displays its instruction above the examples', () => {
    const { container } = render(<ObserveActivity examples={examples} instruction={instruction} />);
    expectInstruction(container);
    expect(container.textContent?.indexOf(instruction)).toBeLessThan(container.textContent!.indexOf('first'));
  });

  test('default wrapper forwards the instruction with examples and prompt', () => {
    const { container } = render(<Observe examples={examples} instruction={instruction} prompt="Notice the pattern." />);
    expectInstruction(container);
    expect(screen.getByText('Notice the pattern.')).toBeInTheDocument();
    expect(screen.getByText('first')).toBeInTheDocument();
  });

  test('children wrapper displays the instruction once', () => {
    const { container } = render(<Observe instruction={instruction}><div>Child content</div></Observe>);
    expectInstruction(container);
    expect(screen.getByText('Child content')).toBeInTheDocument();
  });

  test.each([undefined, ''])('omits the instruction paragraph for %s', (value) => {
    const { container } = render(<Observe examples={examples} instruction={value} />);
    expect(container.querySelector('p[class*="instruction"]')).toBeNull();
    expect(screen.getByText('first')).toBeInTheDocument();
  });

  test('renders instruction text without interpreting HTML', () => {
    const text = '<img src=x onerror=alert("instruction")>';
    const { container } = render(<Observe examples={examples} instruction={text} />);
    expect(screen.getByText(text)).toBeInTheDocument();
    expect(container.querySelector('img')).toBeNull();
  });

  test('compiles and renders the Observe MDX fixture page with a visible instruction', async () => {
    const source = readFileSync('tests/fixtures/observe-instruction.mdx', 'utf8');
    const { default: Page } = await evaluate(source, { ...runtime });
    const { container } = render(<Page components={{ Observe }} />);
    expectInstruction(container);
    expect(screen.getByText('Observe instruction fixture')).toBeInTheDocument();
    expect(screen.getByText('first')).toBeInTheDocument();
    expect(screen.getByText('Notice the pattern.')).toBeInTheDocument();
  });
});

describe('sibling instruction contracts', () => {
  test('classify displays its instruction', () => {
    const { container } = render(<Classify categories={[{ label: 'First', items: ['A'] }]} instruction={instruction} />);
    expectInstruction(container);
  });

  test('letter-grid displays its instruction', () => {
    const { container } = render(<LetterGrid letters={[{ upper: 'A', lower: 'a' }]} instruction={instruction} />);
    expectInstruction(container);
  });

  test('phrase-table displays its instruction', () => {
    const { container } = render(<PhraseTable groups={[{ label: 'First', phrases: [{ phrase: 'Hello' }] }]} instruction={instruction} />);
    expectInstruction(container);
  });
});
