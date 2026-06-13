import { describe, test, expect } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import GroupSort from '@site/src/components/GroupSort';

// GroupSort is DRAG-ONLY — there is no click interaction path for
// moving tiles between the pool and the buckets. happy-dom does not
// implement the full HTML5 drag-and-drop event pipeline (DataTransfer,
// dragstart → dragover → drop with effectAllowed negotiation), so
// asserting the sort flow in a jsdom-style environment would require
// mocking the component's internal state handlers directly — which
// defeats the purpose of an integration-ish unit test.
//
// These tests cover everything that DOESN'T require drag events:
// initial render, word count in pool, bucket rendering, header /
// instruction / placeholder labels, EN/UK variants, Check Answers
// visibility gating, and reset behaviour wrt static state.
//
// The full sort → check → retry flow is tracked as follow-up
// Playwright E2E coverage (#1082).

// ── helpers ──────────────────────────────────────────────────────────────────

function pool(container: HTMLElement) {
  return container.querySelector('[data-activity="group-sort-pool"]') as HTMLElement;
}

function buckets(container: HTMLElement) {
  return [...container.querySelectorAll('[data-activity="group-sort-bucket"]')] as HTMLElement[];
}

function bucketByName(container: HTMLElement, name: string) {
  const b = buckets(container).find(el => el.getAttribute('data-group-name') === name);
  if (!b) throw new Error(`bucket "${name}" not found`);
  return b;
}

function wordTiles(scope: HTMLElement) {
  return [...scope.querySelectorAll<HTMLButtonElement>('button')].filter(
    b => b.textContent?.trim() && !b.textContent?.trim().startsWith('Check') && !b.textContent?.trim().startsWith('Try')
  );
}

// ── GroupSort ─────────────────────────────────────────────────────────────────

describe('GroupSort initial render', () => {
  const groups = {
    Fruits: ['apple', 'banana'],
    Vegetables: ['carrot', 'potato'],
  };

  test('wraps everything in a group-sort activity container', () => {
    const { container } = render(<GroupSort groups={groups} />);
    expect(container.querySelector('[data-activity="group-sort"]')).toBeInTheDocument();
  });

  test('renders the word pool', () => {
    const { container } = render(<GroupSort groups={groups} />);
    expect(pool(container)).toBeInTheDocument();
  });

  test('pool contains all words (4 across both groups)', () => {
    const { container } = render(<GroupSort groups={groups} />);
    const texts = wordTiles(pool(container)).map(b => b.textContent?.trim());
    expect(texts.length).toBe(4);
    expect(new Set(texts)).toEqual(new Set(['apple', 'banana', 'carrot', 'potato']));
  });

  test('renders one bucket per group', () => {
    const { container } = render(<GroupSort groups={groups} />);
    expect(buckets(container)).toHaveLength(2);
  });

  test('each bucket shows its group name as a heading', () => {
    const { container } = render(<GroupSort groups={groups} />);
    expect(within(bucketByName(container, 'Fruits')).getByText('Fruits')).toBeInTheDocument();
    expect(within(bucketByName(container, 'Vegetables')).getByText('Vegetables')).toBeInTheDocument();
  });

  test('buckets start empty (no word tiles inside)', () => {
    const { container } = render(<GroupSort groups={groups} />);
    for (const b of buckets(container)) {
      expect(wordTiles(b)).toHaveLength(0);
    }
  });

  test('buckets show the "drop words here" placeholder initially', () => {
    const { container } = render(<GroupSort groups={groups} />);
    const fruits = bucketByName(container, 'Fruits');
    expect(fruits.textContent).toContain('Drop words here');
  });

  test('Check Answers button is NOT shown when the pool is non-empty', () => {
    const { container } = render(<GroupSort groups={groups} />);
    const check = [...container.querySelectorAll<HTMLButtonElement>('button')].find(
      b => b.textContent?.trim() === 'Check Answers'
    );
    expect(check).toBeUndefined();
  });

  test('no feedback is present before checking', () => {
    const { container } = render(<GroupSort groups={groups} />);
    expect(container.querySelector('[data-activity="group-sort-feedback"]')).toBeNull();
  });
});

describe('GroupSort labels', () => {
  const groups = { A: ['one'], B: ['two'] };

  test('renders English header by default', () => {
    render(<GroupSort groups={groups} />);
    expect(screen.getAllByText('Group Sort').length).toBeGreaterThan(0);
  });

  test('renders Ukrainian header when isUkrainian=true', () => {
    render(<GroupSort groups={groups} isUkrainian />);
    expect(screen.getAllByText('Розподіліть за категоріями').length).toBeGreaterThan(0);
  });

  test('placeholder uses English label by default', () => {
    const { container } = render(<GroupSort groups={groups} />);
    expect(bucketByName(container, 'A').textContent).toContain('Drop words here');
  });

  test('placeholder uses Ukrainian label when isUkrainian=true', () => {
    const { container } = render(<GroupSort groups={groups} isUkrainian />);
    expect(bucketByName(container, 'A').textContent).toContain('Перетягніть слова сюди');
  });

  test('renders instruction when provided', () => {
    render(<GroupSort groups={groups} instruction="Sort these things" />);
    expect(screen.getByText('Sort these things')).toBeInTheDocument();
  });
});

describe('GroupSort with many groups', () => {
  test('renders a bucket for each group even with 5 groups', () => {
    const groups = {
      Red: ['a', 'b'],
      Blue: ['c'],
      Green: ['d', 'e', 'f'],
      Yellow: ['g'],
      Purple: ['h', 'i'],
    };
    const { container } = render(<GroupSort groups={groups} />);

    expect(buckets(container)).toHaveLength(5);
    // Pool should have 9 total words
    expect(wordTiles(pool(container))).toHaveLength(9);
  });

  test('renders a single-group instance without crashing', () => {
    const groups = { Only: ['solo'] };
    const { container } = render(<GroupSort groups={groups} />);

    expect(buckets(container)).toHaveLength(1);
    expect(wordTiles(pool(container))).toHaveLength(1);
  });

  test('renders a group with zero words without crashing', () => {
    const groups = { Full: ['a', 'b'], Empty: [] };
    const { container } = render(<GroupSort groups={groups} />);

    expect(buckets(container)).toHaveLength(2);
    expect(wordTiles(pool(container))).toHaveLength(2);
    // The empty group still renders as a bucket with its header
    expect(bucketByName(container, 'Empty')).toBeInTheDocument();
  });
});

describe('GroupSort draggability', () => {
  // We can't test drag events themselves but we can confirm the DOM
  // contract: every word tile should be draggable=true so the real
  // drag handlers in a browser have something to fire on.
  const groups = { X: ['alpha', 'beta'] };

  test('all word tiles expose draggable=true', () => {
    const { container } = render(<GroupSort groups={groups} />);
    const tiles = wordTiles(pool(container));
    expect(tiles.length).toBeGreaterThan(0);
    for (const t of tiles) {
      expect(t.getAttribute('draggable')).toBe('true');
    }
  });
});
