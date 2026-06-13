import { describe, test, expect } from 'vitest';
import { render, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FlashcardDeck from '@site/src/components/FlashcardDeck';

type FlashcardData = {
  front: string;
  back: string;
  subtitle?: string;
  tag?: string;
  tagColor?: string;
};

function deck(container: HTMLElement) {
  const el = container.querySelector<HTMLElement>('[data-activity="flashcard-deck"]');
  if (!el) throw new Error('flashcard-deck container not found');
  return el;
}

function flashcards(container: HTMLElement) {
  return [...container.querySelectorAll<HTMLElement>('[data-activity="flashcard"]')];
}

function sampleCards(): FlashcardData[] {
  return [
    {
      front: 'dobryi den',
      back: 'good afternoon',
      subtitle: 'formal greeting',
      tag: 'phrase',
      tagColor: '#0057B8',
    },
    {
      front: 'pryvit',
      back: 'hi',
    },
  ];
}

describe('FlashcardDeck rendering', () => {
  test('wraps in [data-activity="flashcard-deck"]', () => {
    const { container } = render(<FlashcardDeck cards={sampleCards()} />);
    expect(deck(container)).toBeInTheDocument();
  });

  test('renders one [data-activity="flashcard"] per card', () => {
    const cards = sampleCards();
    const { container } = render(<FlashcardDeck cards={cards} />);
    expect(flashcards(container)).toHaveLength(cards.length);
  });

  test('each card starts with data-flipped="false"', () => {
    const { container } = render(<FlashcardDeck cards={sampleCards()} />);

    for (const card of flashcards(container)) {
      expect(card).toHaveAttribute('data-flipped', 'false');
    }
  });

  test('renders the front text', () => {
    const cards = sampleCards();
    const { container } = render(<FlashcardDeck cards={cards} />);

    expect(container.textContent).toContain(cards[0].front);
    expect(container.textContent).toContain(cards[1].front);
  });

  test('renders the subtitle when provided', () => {
    const cards = sampleCards();
    const { container } = render(<FlashcardDeck cards={cards} />);

    expect(within(flashcards(container)[0]).getAllByText(cards[0].subtitle!)).toHaveLength(2);
  });

  test('does not render the subtitle when absent', () => {
    const cards = sampleCards();
    const { container } = render(<FlashcardDeck cards={cards} />);

    expect(within(flashcards(container)[1]).queryByText('formal greeting')).not.toBeInTheDocument();
    expect(
      flashcards(container)[1].querySelector('.flashcard-subtitle')
    ).not.toBeInTheDocument();
  });

  test('renders the tag when provided', () => {
    const cards = sampleCards();
    const { container } = render(<FlashcardDeck cards={cards} />);

    expect(within(flashcards(container)[0]).getByText(cards[0].tag!)).toBeInTheDocument();
  });

  test('does not render the tag when absent', () => {
    const { container } = render(<FlashcardDeck cards={sampleCards()} />);

    expect(flashcards(container)[1].querySelector('.flashcard-tag')).not.toBeInTheDocument();
  });

  test('applies tagColor as background style when provided', () => {
    const cards = sampleCards();
    const { container } = render(<FlashcardDeck cards={cards} />);

    const tag = within(flashcards(container)[0]).getByText(cards[0].tag!);
    expect(tag).toHaveStyle({ background: '#0057B8' });
  });
});

describe('FlashcardDeck flip interaction', () => {
  test('clicking a card sets data-flipped="true"', async () => {
    const user = userEvent.setup();
    const { container } = render(<FlashcardDeck cards={sampleCards()} />);
    const cards = flashcards(container);

    await user.click(cards[0]);

    expect(cards[0]).toHaveAttribute('data-flipped', 'true');
  });

  test('clicking again toggles back to data-flipped="false"', async () => {
    const user = userEvent.setup();
    const { container } = render(<FlashcardDeck cards={sampleCards()} />);
    const cards = flashcards(container);

    await user.click(cards[0]);
    await user.click(cards[0]);

    expect(cards[0]).toHaveAttribute('data-flipped', 'false');
  });

  test('the back text is findable in the DOM after flipping', async () => {
    const user = userEvent.setup();
    const cards = sampleCards();
    const { container } = render(<FlashcardDeck cards={cards} />);
    const renderedCards = flashcards(container);

    await user.click(renderedCards[0]);

    expect(within(renderedCards[0]).getByText(cards[0].back)).toBeInTheDocument();
  });
});

describe('FlashcardDeck keyboard a11y', () => {
  test('Enter flips a focused card', async () => {
    const user = userEvent.setup();
    const { container } = render(<FlashcardDeck cards={sampleCards()} />);
    const cards = flashcards(container);

    cards[0].focus();
    await user.keyboard('{Enter}');

    expect(cards[0]).toHaveAttribute('data-flipped', 'true');
  });

  test('Space flips a focused card and prevents default scroll', async () => {
    const user = userEvent.setup();
    const { container } = render(<FlashcardDeck cards={sampleCards()} />);
    const cards = flashcards(container);
    let defaultPrevented = false;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === ' ') {
        defaultPrevented = event.defaultPrevented;
      }
    };

    document.addEventListener('keydown', onKeyDown);

    try {
      cards[0].focus();
      await user.keyboard(' ');
    } finally {
      document.removeEventListener('keydown', onKeyDown);
    }

    expect(cards[0]).toHaveAttribute('data-flipped', 'true');
    expect(defaultPrevented).toBe(true);
  });

  test('other keys do not flip', async () => {
    const user = userEvent.setup();
    const { container } = render(<FlashcardDeck cards={sampleCards()} />);
    const cards = flashcards(container);

    cards[0].focus();
    await user.keyboard('a');

    expect(cards[0]).toHaveAttribute('data-flipped', 'false');
  });

  test('cards have tabIndex=0', () => {
    const { container } = render(<FlashcardDeck cards={sampleCards()} />);

    for (const card of flashcards(container)) {
      expect(card.tabIndex).toBe(0);
    }
  });

  test('aria-label contains card.front when not flipped', () => {
    const cards = sampleCards();
    const { container } = render(<FlashcardDeck cards={cards} />);

    expect(flashcards(container)[0]).toHaveAttribute(
      'aria-label',
      expect.stringContaining(cards[0].front)
    );
  });

  test('aria-label contains card.back when flipped', async () => {
    const user = userEvent.setup();
    const cards = sampleCards();
    const { container } = render(<FlashcardDeck cards={cards} />);
    const renderedCards = flashcards(container);

    await user.click(renderedCards[0]);

    expect(renderedCards[0]).toHaveAttribute(
      'aria-label',
      expect.stringContaining(cards[0].back)
    );
  });
});

describe('FlashcardDeck independence', () => {
  test('clicking card A does not flip card B', async () => {
    const user = userEvent.setup();
    const cards = [
      { front: 'odin', back: 'one' },
      { front: 'dva', back: 'two' },
      { front: 'try', back: 'three' },
    ];
    const { container } = render(<FlashcardDeck cards={cards} />);
    const renderedCards = flashcards(container);

    await user.click(renderedCards[0]);

    expect(renderedCards[0]).toHaveAttribute('data-flipped', 'true');
    expect(renderedCards[1]).toHaveAttribute('data-flipped', 'false');
    expect(renderedCards[2]).toHaveAttribute('data-flipped', 'false');
  });
});

describe('FlashcardDeck edge cases', () => {
  test('empty cards array returns null', () => {
    const { container } = render(<FlashcardDeck cards={[]} />);
    expect(container.firstChild).toBeNull();
  });

  test('undefined cards prop returns null', () => {
    const { container } = render(
      // @ts-expect-error testing runtime guard for missing cards
      <FlashcardDeck cards={undefined} />
    );

    expect(container.firstChild).toBeNull();
  });

  test('5 cards with duplicate front values all render', () => {
    const cards: FlashcardData[] = [
      { front: 'same', back: 'one' },
      { front: 'same', back: 'two' },
      { front: 'same', back: 'three' },
      { front: 'same', back: 'four' },
      { front: 'same', back: 'five' },
    ];
    const { container } = render(<FlashcardDeck cards={cards} />);

    expect(flashcards(container)).toHaveLength(5);
    expect(within(deck(container)).getAllByText('same')).toHaveLength(5);
  });
});
