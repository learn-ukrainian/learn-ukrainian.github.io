import { describe, test, expect } from 'vitest';
import { render, screen, within } from '@testing-library/react';
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
  const btn = rightTiles(container).find(b => b.textContent?.trim() === text);
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

    await user.click(leftTiles(container)[1]);
    expect(leftTiles(container)[0].getAttribute('data-selected')).toBe('false');
    expect(leftTiles(container)[1].getAttribute('data-selected')).toBe('true');
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
});
