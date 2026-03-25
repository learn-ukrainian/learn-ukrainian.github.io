import { describe, test, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import RuleBox from '@site/src/components/RuleBox';
import MythBuster from '@site/src/components/MythBuster';
import SourceBox from '@site/src/components/SourceBox';
import FlashcardDeck from '@site/src/components/FlashcardDeck';

// ── RuleBox ──────────────────────────────────────────────────────────────────

describe('RuleBox', () => {
  test('renders title and children', () => {
    render(
      <RuleBox title="Gender by ending">
        <p>Some grammar content</p>
      </RuleBox>
    );
    expect(screen.getByText('Gender by ending')).toBeTruthy();
    expect(screen.getByText('Some grammar content')).toBeTruthy();
  });

  test('renders default icon when none provided', () => {
    const { container } = render(
      <RuleBox title="Test">
        <p>Content</p>
      </RuleBox>
    );
    const iconEl = container.querySelector('.rule-box-icon');
    expect(iconEl).toBeTruthy();
    // Default icon is U+1F4D0 (triangular ruler)
    expect(iconEl!.textContent).toBe('\u{1F4D0}');
  });

  test('renders custom icon', () => {
    const { container } = render(
      <RuleBox title="Test" icon="⚡">
        <p>Content</p>
      </RuleBox>
    );
    const iconEl = container.querySelector('.rule-box-icon');
    expect(iconEl!.textContent).toBe('⚡');
  });

  test('renders table children correctly', () => {
    const { container } = render(
      <RuleBox title="Genders">
        <table>
          <tbody>
            <tr><td>masculine</td></tr>
            <tr><td>feminine</td></tr>
          </tbody>
        </table>
      </RuleBox>
    );
    expect(container.querySelector('table')).toBeTruthy();
    expect(container.querySelectorAll('td').length).toBe(2);
  });
});

// ── MythBuster ───────────────────────────────────────────────────────────────

describe('MythBuster', () => {
  const props = {
    claim: 'Ukrainian is a dialect of Russian',
    truth: 'Ukrainian is an independent language with distinct features',
  };

  test('renders claim and truth', () => {
    render(<MythBuster {...props} />);
    expect(screen.getByText(props.claim)).toBeTruthy();
    expect(screen.getByText(props.truth)).toBeTruthy();
  });

  test('renders source attributions when provided', () => {
    render(
      <MythBuster
        {...props}
        claimSource="Russian propaganda"
        truthSource="Shevelov, 1979"
      />
    );
    expect(screen.getByText('Russian propaganda')).toBeTruthy();
    expect(screen.getByText('Shevelov, 1979')).toBeTruthy();
  });

  test('omits source elements when not provided', () => {
    const { container } = render(<MythBuster {...props} />);
    expect(container.querySelectorAll('.myth-source').length).toBe(0);
  });

  test('has correct CSS classes for claim and truth', () => {
    const { container } = render(<MythBuster {...props} />);
    expect(container.querySelector('.myth-claim')).toBeTruthy();
    expect(container.querySelector('.myth-truth')).toBeTruthy();
    expect(container.querySelector('.myth-box')).toBeTruthy();
  });
});

// ── SourceBox ────────────────────────────────────────────────────────────────

describe('SourceBox', () => {
  const props = {
    title: 'Galician Chronicle',
    quote: 'Danylo was a great prince...',
    citation: 'Chronicle, 1253',
  };

  test('renders title, quote, and citation', () => {
    render(<SourceBox {...props} />);
    expect(screen.getByText(/Galician Chronicle/)).toBeTruthy();
    expect(screen.getByText(props.quote)).toBeTruthy();
    expect(screen.getByText(/Chronicle, 1253/)).toBeTruthy();
  });

  test('renders analysis children when provided', () => {
    render(
      <SourceBox {...props}>
        <p>Analysis of the source</p>
      </SourceBox>
    );
    expect(screen.getByText('Analysis of the source')).toBeTruthy();
  });

  test('omits analysis div when no children', () => {
    const { container } = render(<SourceBox {...props} />);
    expect(container.querySelector('.source-analysis')).toBeNull();
  });

  test('uses blockquote element for the quote', () => {
    const { container } = render(<SourceBox {...props} />);
    const bq = container.querySelector('blockquote');
    expect(bq).toBeTruthy();
    expect(bq!.textContent).toBe(props.quote);
  });
});

// ── FlashcardDeck ────────────────────────────────────────────────────────────

describe('FlashcardDeck', () => {
  const cards = [
    { front: 'стіл', back: 'table', subtitle: 'мій стіл', tag: 'м', tagColor: '#0057B8' },
    { front: 'книга', back: 'book', tag: 'ж', tagColor: '#C2185B' },
    { front: 'ліжко', back: 'bed' },
  ];

  test('renders correct number of cards', () => {
    const { container } = render(<FlashcardDeck cards={cards} />);
    expect(container.querySelectorAll('.flashcard').length).toBe(3);
  });

  test('returns null for empty cards', () => {
    const { container } = render(<FlashcardDeck cards={[]} />);
    expect(container.innerHTML).toBe('');
  });

  test('shows front content initially', () => {
    render(<FlashcardDeck cards={cards} />);
    expect(screen.getByText('стіл')).toBeTruthy();
    expect(screen.getByText('книга')).toBeTruthy();
    expect(screen.getByText('ліжко')).toBeTruthy();
  });

  test('shows subtitle when provided', () => {
    render(<FlashcardDeck cards={cards} />);
    // Subtitle appears on both front and back of the card
    expect(screen.getAllByText('мій стіл').length).toBe(2);
  });

  test('shows tag when provided', () => {
    render(<FlashcardDeck cards={cards} />);
    expect(screen.getByText('м')).toBeTruthy();
    expect(screen.getByText('ж')).toBeTruthy();
  });

  test('flips card on click', () => {
    const { container } = render(<FlashcardDeck cards={[cards[0]]} />);
    const card = container.querySelector('.flashcard')!;
    expect(card.classList.contains('flipped')).toBe(false);

    fireEvent.click(card);
    expect(card.classList.contains('flipped')).toBe(true);

    fireEvent.click(card);
    expect(card.classList.contains('flipped')).toBe(false);
  });

  test('flips card on Enter key', () => {
    const { container } = render(<FlashcardDeck cards={[cards[0]]} />);
    const card = container.querySelector('.flashcard')!;

    fireEvent.keyDown(card, { key: 'Enter' });
    expect(card.classList.contains('flipped')).toBe(true);
  });

  test('flips card on Space key', () => {
    const { container } = render(<FlashcardDeck cards={[cards[0]]} />);
    const card = container.querySelector('.flashcard')!;

    fireEvent.keyDown(card, { key: ' ' });
    expect(card.classList.contains('flipped')).toBe(true);
  });

  test('applies tag color as inline style', () => {
    const { container } = render(<FlashcardDeck cards={[cards[0]]} />);
    const tag = container.querySelector('.flashcard-tag') as HTMLElement;
    expect(tag).toBeTruthy();
    // jsdom keeps the hex value as-is (no conversion to rgb)
    expect(tag.style.background).toBe('#0057B8');
  });

  test('card without tag has no tag element', () => {
    const { container } = render(<FlashcardDeck cards={[cards[2]]} />);
    expect(container.querySelector('.flashcard-tag')).toBeNull();
  });
});
