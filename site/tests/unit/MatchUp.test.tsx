import { describe, test, expect, vi } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MatchUp from '@site/src/components/MatchUp';

// MatchUp shuffles the RIGHT column on mount, so tests find right-
// tiles by text content, never by index. Left column is stable.

// ── helpers ──────────────────────────────────────────────────────────────────

function leftTiles(container: HTMLElement) {
  const col = container.querySelector('[data-activity="match-left-column"]');
  if (!col) throw new Error('match-left-column not found');
  return within(col as HTMLElement).getAllByRole('button');
}

function rightTiles(container: HTMLElement) {
  const col = container.querySelector('[data-activity="match-right-column"]');
  if (!col) throw new Error('match-right-column not found');
  return within(col as HTMLElement).getAllByRole('button');
}

function findRightByText(container: HTMLElement, text: string) {
  const btn = rightTiles(container).find((b) => {
    const tag = b.querySelector('.matchPairTag');
    const content = tag ? b.textContent?.replace(tag.textContent ?? '', '') : b.textContent;
    return content?.trim() === text;
  });
  if (!btn) throw new Error(`right tile "${text}" not found`);
  return btn;
}

function feedback(container: HTMLElement) {
  return container.querySelector('[data-activity="match-feedback"]');
}

// ── MatchUp ───────────────────────────────────────────────────────────────────

describe('MatchUp', () => {
  const pairs = [
    { left: 'Cat', right: 'Meow' },
    { left: 'Dog', right: 'Bark' },
    { left: 'Cow', right: 'Moo' },
  ];

  test('renders the activity container with data-activity="match-up"', () => {
    const { container } = render(<MatchUp pairs={pairs} />);
    expect(container.querySelector('[data-activity="match-up"]')).toBeInTheDocument();
  });

  test('renders one left tile per pair', () => {
    const { container } = render(<MatchUp pairs={pairs} />);
    expect(leftTiles(container)).toHaveLength(3);
  });

  test('renders one right tile per pair', () => {
    const { container } = render(<MatchUp pairs={pairs} />);
    expect(rightTiles(container)).toHaveLength(3);
  });

  test('left column preserves the original order', () => {
    const { container } = render(<MatchUp pairs={pairs} />);
    const texts = leftTiles(container).map(b => b.textContent?.trim());
    expect(texts).toEqual(['Cat', 'Dog', 'Cow']);
  });

  test('right column contains all right texts regardless of shuffle order', () => {
    const { container } = render(<MatchUp pairs={pairs} />);
    const texts = rightTiles(container).map(b => b.textContent?.trim());
    expect(new Set(texts)).toEqual(new Set(['Meow', 'Bark', 'Moo']));
  });

  test('no feedback shown before all matches are made', () => {
    const { container } = render(<MatchUp pairs={pairs} />);
    expect(feedback(container)).not.toBeInTheDocument();
  });

  test('renders English header by default', () => {
    render(<MatchUp pairs={pairs} />);
    expect(screen.getAllByText('Match Up').length).toBeGreaterThan(0);
  });

  test('renders Ukrainian header when isUkrainian=true', () => {
    render(<MatchUp pairs={pairs} isUkrainian />);
    expect(screen.getAllByText('Знайдіть пару').length).toBeGreaterThan(0);
  });

  test('renders instruction text when provided', () => {
    render(<MatchUp pairs={pairs} instruction="Match sounds to animals" />);
    expect(screen.getByText('Match sounds to animals')).toBeInTheDocument();
  });

  test('clicking a correct pair marks both tiles as matched', async () => {
    const user = userEvent.setup();
    const { container } = render(<MatchUp pairs={pairs} />);

    await user.click(leftTiles(container)[0]); // 'Cat' (originalIndex=0)
    await user.click(findRightByText(container, 'Meow'));

    const catTile = leftTiles(container)[0];
    const meowTile = findRightByText(container, 'Meow');
    expect(catTile.getAttribute('data-matched')).toBe('true');
    expect(meowTile.getAttribute('data-matched')).toBe('true');
  });

  test('matched tiles become disabled', async () => {
    const user = userEvent.setup();
    const { container } = render(<MatchUp pairs={pairs} />);

    await user.click(leftTiles(container)[0]);
    await user.click(findRightByText(container, 'Meow'));

    expect(leftTiles(container)[0]).toBeDisabled();
    expect(findRightByText(container, 'Meow')).toBeDisabled();
  });

  test('unmatched tiles remain enabled after a correct match', async () => {
    const user = userEvent.setup();
    const { container } = render(<MatchUp pairs={pairs} />);

    await user.click(leftTiles(container)[0]);
    await user.click(findRightByText(container, 'Meow'));

    expect(leftTiles(container)[1]).toBeEnabled();
    expect(findRightByText(container, 'Bark')).toBeEnabled();
  });

  test('wrong pair does NOT mark tiles as matched', async () => {
    const user = userEvent.setup();
    const { container } = render(<MatchUp pairs={pairs} />);

    await user.click(leftTiles(container)[0]); // Cat
    await user.click(findRightByText(container, 'Bark')); // wrong — should be Meow

    expect(leftTiles(container)[0].getAttribute('data-matched')).toBe('false');
    expect(findRightByText(container, 'Bark').getAttribute('data-matched')).toBe('false');
  });

  test('selecting a new left tile deselects the previous one', async () => {
    const user = userEvent.setup();
    const { container } = render(<MatchUp pairs={pairs} />);

    await user.click(leftTiles(container)[0]);
    expect(leftTiles(container)[0].getAttribute('data-selected')).toBe('true');
    expect(leftTiles(container)[0]).toHaveAttribute('aria-pressed', 'true');
    expect(leftTiles(container)[0]).toHaveClass('selected');

    await user.click(leftTiles(container)[1]);
    expect(leftTiles(container)[0].getAttribute('data-selected')).toBe('false');
    expect(leftTiles(container)[0]).toHaveAttribute('aria-pressed', 'false');
    expect(leftTiles(container)[0]).not.toHaveClass('selected');
    expect(leftTiles(container)[1].getAttribute('data-selected')).toBe('true');
    expect(leftTiles(container)[1]).toHaveAttribute('aria-pressed', 'true');
    expect(leftTiles(container)[1]).toHaveClass('selected');
  });

  test('selected left tile stays visibly marked until its pair is chosen', async () => {
    const user = userEvent.setup();
    const { container } = render(<MatchUp pairs={pairs} />);

    await user.click(leftTiles(container)[0]);
    const selected = leftTiles(container)[0];
    expect(selected).toHaveClass('selected');
    expect(selected).toHaveAttribute('aria-pressed', 'true');
    expect(selected).toHaveAttribute('data-selected', 'true');

    // Still selected before the right tile is chosen.
    expect(leftTiles(container)[0]).toHaveClass('selected');

    await user.click(findRightByText(container, 'Meow'));
    expect(leftTiles(container)[0]).not.toHaveClass('selected');
    expect(leftTiles(container)[0]).toHaveAttribute('aria-pressed', 'false');
  });

  test('clicking a right tile without a left selection is a no-op', async () => {
    const user = userEvent.setup();
    const { container } = render(<MatchUp pairs={pairs} />);

    await user.click(findRightByText(container, 'Meow'));

    // Nothing matched
    for (const b of [...leftTiles(container), ...rightTiles(container)]) {
      expect(b.getAttribute('data-matched')).toBe('false');
    }
  });

  test('shows success feedback when all pairs are matched', async () => {
    const user = userEvent.setup();
    const { container } = render(<MatchUp pairs={pairs} />);

    // Match Cat → Meow, Dog → Bark, Cow → Moo
    await user.click(leftTiles(container)[0]);
    await user.click(findRightByText(container, 'Meow'));
    await user.click(leftTiles(container)[1]);
    await user.click(findRightByText(container, 'Bark'));
    await user.click(leftTiles(container)[2]);
    await user.click(findRightByText(container, 'Moo'));

    const fb = feedback(container);
    expect(fb).toBeInTheDocument();
    expect(fb!.textContent).toContain('All matched correctly');
  });

  test('shows Ukrainian success message when isUkrainian=true', async () => {
    const user = userEvent.setup();
    const { container } = render(<MatchUp pairs={pairs} isUkrainian />);

    await user.click(leftTiles(container)[0]);
    await user.click(findRightByText(container, 'Meow'));
    await user.click(leftTiles(container)[1]);
    await user.click(findRightByText(container, 'Bark'));
    await user.click(leftTiles(container)[2]);
    await user.click(findRightByText(container, 'Moo'));

    expect(feedback(container)!.textContent).toContain('Все з’єднано правильно');
  });

  test('clicking an already-matched left tile is a no-op', async () => {
    const user = userEvent.setup();
    const { container } = render(<MatchUp pairs={pairs} />);

    await user.click(leftTiles(container)[0]);
    await user.click(findRightByText(container, 'Meow'));

    // Try to click the matched Cat again
    await user.click(leftTiles(container)[0]);

    // Still matched, still disabled
    expect(leftTiles(container)[0]).toBeDisabled();
  });

  test('renders correctly in a lesson context (Cyrillic/English pairs and custom instructions)', () => {
    const lessonPairs = [
      { left: 'стіл', right: 'table' },
      { left: 'книга', right: 'book' },
      { left: 'вікно', right: 'window' },
    ];
    const { container } = render(
      <MatchUp
        pairs={lessonPairs}
        instruction="Match each Ukrainian noun with its English cue."
        isUkrainian={false}
      />
    );

    expect(screen.getByText('Match each Ukrainian noun with its English cue.')).toBeInTheDocument();

    const leftTextContents = leftTiles(container).map((b) => b.textContent?.trim());
    expect(leftTextContents).toEqual(['стіл', 'книга', 'вікно']);

    const rightTextContents = rightTiles(container).map((b) => b.textContent?.trim());
    expect(new Set(rightTextContents)).toEqual(new Set(['table', 'book', 'window']));
  });

  describe('practice-only matchedPairCoding="semantic-four"', () => {
    test('omitted prop leaves default DOM and pair-color attributes', async () => {
      const user = userEvent.setup();
      const { container } = render(<MatchUp pairs={pairs} />);

      await user.click(leftTiles(container)[0]);
      await user.click(findRightByText(container, 'Meow'));

      const catTile = leftTiles(container)[0];
      const meowTile = findRightByText(container, 'Meow');
      expect(catTile).not.toHaveAttribute('data-pair-coding');
      expect(meowTile).not.toHaveAttribute('data-pair-coding');
      expect(catTile.querySelector('.matchPairTag')).not.toBeInTheDocument();
      expect(meowTile.querySelector('.matchPairTag')).not.toBeInTheDocument();
    });

    test('opted-in board exposes data-pair-coding and visible tags after match', async () => {
      const user = userEvent.setup();
      const { container } = render(<MatchUp pairs={pairs} matchedPairCoding="semantic-four" />);

      await user.click(leftTiles(container)[0]);
      await user.click(findRightByText(container, 'Meow'));

      const catTile = leftTiles(container)[0];
      const meowTile = findRightByText(container, 'Meow');
      expect(catTile).toHaveAttribute('data-pair-coding', 'semantic-four');
      expect(meowTile).toHaveAttribute('data-pair-coding', 'semantic-four');
      expect(catTile).toHaveAttribute('data-pair-token', '0');
      expect(meowTile).toHaveAttribute('data-pair-token', '0');
      expect(catTile.querySelector('.matchPairTag')).toHaveTextContent('①');
      expect(meowTile.querySelector('.matchPairTag')).toHaveTextContent('①');
    });

    test('four-pair board produces four token families and four unique tags', async () => {
      const user = userEvent.setup();
      const fourPairs = [
        { left: 'A', right: 'a' },
        { left: 'B', right: 'b' },
        { left: 'C', right: 'c' },
        { left: 'D', right: 'd' },
      ];
      const { container } = render(<MatchUp pairs={fourPairs} matchedPairCoding="semantic-four" />);

      // Match in the order 2, 0, 3, 1 so tag order differs from original index order.
      await user.click(leftTiles(container)[2]);
      await user.click(findRightByText(container, 'c'));
      await user.click(leftTiles(container)[0]);
      await user.click(findRightByText(container, 'a'));
      await user.click(leftTiles(container)[3]);
      await user.click(findRightByText(container, 'd'));
      await user.click(leftTiles(container)[1]);
      await user.click(findRightByText(container, 'b'));

      const tags = new Set<string>();
      const tokens = new Set<string>();
      for (const tile of [...leftTiles(container), ...rightTiles(container)]) {
        const tag = tile.querySelector('.matchPairTag');
        expect(tag).toBeInTheDocument();
        tags.add(tag!.textContent ?? '');
        tokens.add(tile.getAttribute('data-pair-token') ?? '');
      }
      expect(Array.from(tags).sort()).toEqual(['①', '②', '③', '④']);
      expect(tokens).toEqual(new Set(['0', '1', '2', '3']));
    });

    test('board above four pairs cycles colors but keeps unique tags', async () => {
      const user = userEvent.setup();
      const sixPairs = [
        { left: 'A', right: 'a' },
        { left: 'B', right: 'b' },
        { left: 'C', right: 'c' },
        { left: 'D', right: 'd' },
        { left: 'E', right: 'e' },
        { left: 'F', right: 'f' },
      ];
      const { container } = render(<MatchUp pairs={sixPairs} matchedPairCoding="semantic-four" />);

      for (let i = 0; i < sixPairs.length; i += 1) {
        await user.click(leftTiles(container)[i]);
        await user.click(findRightByText(container, sixPairs[i].right));
      }

      const tags = new Set<string>();
      for (const tile of [...leftTiles(container), ...rightTiles(container)]) {
        const tag = tile.querySelector('.matchPairTag');
        expect(tag).toBeInTheDocument();
        tags.add(tag!.textContent ?? '');
      }
      expect(tags.size).toBe(6);
      expect(Array.from(tags).sort()).toEqual(['①', '②', '③', '④', '⑤', '⑥']);
    });

    test('shuffle does not change original pair identity or rating attribution', async () => {
      const user = userEvent.setup();
      const onMatch = vi.fn();
      const { container } = render(
        <MatchUp pairs={pairs} matchedPairCoding="semantic-four" onMatch={onMatch} />,
      );

      await user.click(leftTiles(container)[0]);
      const meowTile = findRightByText(container, 'Meow');
      expect(meowTile).toHaveAttribute('data-original-index', '0');
      await user.click(meowTile);

      expect(onMatch).toHaveBeenCalledTimes(1);
      expect(onMatch).toHaveBeenCalledWith(0, 'good');
    });

    test('matched tiles announce pair identity and tag in accessible name', async () => {
      const user = userEvent.setup();
      const { container } = render(
        <MatchUp pairs={pairs} matchedPairCoding="semantic-four" isUkrainian />,
      );

      await user.click(leftTiles(container)[0]);
      await user.click(findRightByText(container, 'Meow'));

      const catTile = leftTiles(container)[0];
      const meowTile = findRightByText(container, 'Meow');
      expect(catTile).toHaveAttribute('aria-label', expect.stringContaining('пара ①'));
      expect(catTile).toHaveAttribute('aria-label', expect.stringContaining('Meow'));
      expect(meowTile).toHaveAttribute('aria-label', expect.stringContaining('пара ①'));
      expect(meowTile).toHaveAttribute('aria-label', expect.stringContaining('Cat'));
    });

    test('wrong match clears after 240ms and never advances the board', async () => {
      const user = userEvent.setup();
      const onMatch = vi.fn();
      const { container } = render(
        <MatchUp pairs={pairs} matchedPairCoding="semantic-four" onMatch={onMatch} />,
      );

      await user.click(leftTiles(container)[0]); // Cat
      await user.click(findRightByText(container, 'Bark')); // wrong

      const catTile = leftTiles(container)[0];
      const barkTile = findRightByText(container, 'Bark');
      expect(catTile).toHaveClass('wrong');
      expect(barkTile).toHaveClass('wrong');
      expect(onMatch).not.toHaveBeenCalled();

      await waitFor(() => {
        expect(catTile).not.toHaveClass('wrong');
        expect(barkTile).not.toHaveClass('wrong');
      }, { timeout: 500 });

      expect(onMatch).not.toHaveBeenCalled();
    });
  });
});
