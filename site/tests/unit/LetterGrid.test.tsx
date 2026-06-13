import { describe, test, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import LetterGrid from '@site/src/components/LetterGrid';

// LetterGrid is a pure presentational component — no state, no
// interaction, no handlers. Tests cover rendering, conditional
// classes driven by sound_type, and the null-safe edge cases.

// ── helpers ──────────────────────────────────────────────────────────────────

function grid(container: HTMLElement) {
  return container.querySelector('[data-activity="letter-grid"]');
}

function cards(container: HTMLElement) {
  return [...container.querySelectorAll('[data-activity="letter-card"]')] as HTMLElement[];
}

function cardByUpper(container: HTMLElement, upper: string) {
  const card = cards(container).find(c => c.getAttribute('data-upper') === upper);
  if (!card) throw new Error(`letter card for "${upper}" not found`);
  return card;
}

// ── LetterGrid ────────────────────────────────────────────────────────────────

describe('LetterGrid', () => {
  const letters = [
    { upper: 'А', lower: 'а', emoji: '🍎', key_word: 'абрикос', sound_type: 'vowel' },
    { upper: 'Б', lower: 'б', emoji: '🐝', key_word: 'бджола' }, // no sound_type → consonant default
    { upper: 'Ь', lower: 'ь', emoji: '🔇', key_word: 'знак', sound_type: 'special' },
  ];

  test('wraps everything in a letter-grid container', () => {
    const { container } = render(<LetterGrid letters={letters} />);
    expect(grid(container)).toBeInTheDocument();
  });

  test('renders one card per letter', () => {
    const { container } = render(<LetterGrid letters={letters} />);
    expect(cards(container)).toHaveLength(3);
  });

  test('each card exposes the upper letter via data-upper', () => {
    const { container } = render(<LetterGrid letters={letters} />);
    const uppers = cards(container).map(c => c.getAttribute('data-upper'));
    expect(uppers).toEqual(['А', 'Б', 'Ь']);
  });

  test('renders upper, lower, emoji, and key_word for each letter', () => {
    const { container } = render(<LetterGrid letters={letters} />);
    const aCard = cardByUpper(container, 'А');
    expect(aCard.textContent).toContain('А');
    expect(aCard.textContent).toContain('а');
    expect(aCard.textContent).toContain('🍎');
    expect(aCard.textContent).toContain('абрикос');
  });

  test('renders note when provided', () => {
    const { container } = render(
      <LetterGrid letters={[{ upper: 'Г', lower: 'г', emoji: '🌾', key_word: 'голос', note: 'fricative' }]} />
    );
    expect(container.textContent).toContain('fricative');
  });

  test('does NOT render a note element when not provided', () => {
    const { container } = render(<LetterGrid letters={letters} />);
    // None of the baseline letters have notes
    expect(container.querySelector('[class*="letterCardNote"]')).toBeNull();
  });

  test('vowel letters get data-sound-type="vowel"', () => {
    const { container } = render(<LetterGrid letters={letters} />);
    expect(cardByUpper(container, 'А').getAttribute('data-sound-type')).toBe('vowel');
  });

  test('special letters get data-sound-type="special"', () => {
    const { container } = render(<LetterGrid letters={letters} />);
    expect(cardByUpper(container, 'Ь').getAttribute('data-sound-type')).toBe('special');
  });

  test('letters without a sound_type default to consonant', () => {
    const { container } = render(<LetterGrid letters={letters} />);
    expect(cardByUpper(container, 'Б').getAttribute('data-sound-type')).toBe('consonant');
  });

  test('applies different CSS classes per sound type', () => {
    const { container } = render(<LetterGrid letters={letters} />);
    // The exact hashed class name depends on CSS modules, but the
    // substring match below is stable under happy-dom's non-hashed
    // class name passthrough.
    const aClass = cardByUpper(container, 'А').className;
    const bClass = cardByUpper(container, 'Б').className;
    const ьClass = cardByUpper(container, 'Ь').className;
    expect(aClass).toMatch(/letterCardVowel/);
    expect(bClass).toMatch(/letterCardConsonant/);
    expect(ьClass).toMatch(/letterCardSpecial/);
  });

  test('renders a title when provided', () => {
    render(<LetterGrid letters={letters} title="Ukrainian Alphabet" />);
    expect(screen.getByText('Ukrainian Alphabet')).toBeInTheDocument();
  });

  test('does NOT render a title heading when title is omitted', () => {
    const { container } = render(<LetterGrid letters={letters} />);
    expect(container.querySelector('h3')).toBeNull();
  });

  test('renders null when letters array is empty', () => {
    const { container } = render(<LetterGrid letters={[]} />);
    expect(container.firstChild).toBeNull();
  });

  test('renders null when letters prop is not provided (undefined)', () => {
    // @ts-expect-error — intentionally passing undefined to exercise the null-safe branch
    const { container } = render(<LetterGrid letters={undefined} />);
    expect(container.firstChild).toBeNull();
  });

  test('large alphabet: renders all 33 Ukrainian letters without issue', () => {
    const ukAlphabet = [
      'А', 'Б', 'В', 'Г', 'Ґ', 'Д', 'Е', 'Є', 'Ж', 'З', 'И', 'І', 'Ї', 'Й', 'К',
      'Л', 'М', 'Н', 'О', 'П', 'Р', 'С', 'Т', 'У', 'Ф', 'Х', 'Ц', 'Ч', 'Ш', 'Щ',
      'Ь', 'Ю', 'Я',
    ].map(u => ({ upper: u, lower: u.toLowerCase(), emoji: '🔠', key_word: 'слово' }));

    const { container } = render(<LetterGrid letters={ukAlphabet} />);
    expect(cards(container)).toHaveLength(33);
  });
});
