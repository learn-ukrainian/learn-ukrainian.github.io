import { describe, test, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ImageToLetter from '@site/src/components/ImageToLetter';

// The component takes {emoji, answer, distractors[]}; the Python activity
// parser maps the A1 schema fields {image, letter, options} onto it (#8716).

const items = [
  {
    emoji: '🍎',
    answer: 'Я',
    distractors: ['А', 'О'],
    explanation: 'Яблуко begins with Я.',
  },
];

describe('ImageToLetter', () => {
  test('renders the answer and every distractor as an option button', () => {
    render(<ImageToLetter items={items} />);
    const labels = screen.getAllByRole('button').map((b) => b.textContent);
    expect(labels.sort()).toEqual(['А', 'О', 'Я']);
  });

  test('shows the emoji and the instruction', () => {
    render(<ImageToLetter items={items} instruction="Pick the first letter." />);
    expect(screen.getByText('🍎')).toBeInTheDocument();
    expect(screen.getByText('Pick the first letter.')).toBeInTheDocument();
  });
});
