import { describe, test, expect, beforeEach } from 'vitest';
import { render, screen, within, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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
  beforeEach(() => {
    document.documentElement.dataset.chromeLocale = 'en';
  });

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
  beforeEach(() => {
    document.documentElement.dataset.chromeLocale = 'en';
  });

  const groups = { A: ['one'], B: ['two'] };

  test('renders English header by default', () => {
    render(<GroupSort groups={groups} />);
    expect(screen.getAllByText('Group Sort').length).toBeGreaterThan(0);
  });

  test('renders Ukrainian header when isUkrainian=true', () => {
    document.documentElement.dataset.chromeLocale = 'uk';
    render(<GroupSort groups={groups} isUkrainian />);
    expect(screen.getAllByText('Розподіліть за категоріями').length).toBeGreaterThan(0);
  });

  test('placeholder uses English label by default', () => {
    const { container } = render(<GroupSort groups={groups} />);
    expect(bucketByName(container, 'A').textContent).toContain('Drop words here');
  });

  test('placeholder uses Ukrainian label when isUkrainian=true', () => {
    document.documentElement.dataset.chromeLocale = 'uk';
    const { container } = render(<GroupSort groups={groups} isUkrainian />);
    expect(bucketByName(container, 'A').textContent).toContain('Перетягніть слова сюди');
  });

  test('renders instruction when provided', () => {
    render(<GroupSort groups={groups} instruction="Sort these things" />);
    expect(screen.getByText('Sort these things')).toBeInTheDocument();
  });
});

describe('GroupSort with many groups', () => {
  beforeEach(() => {
    document.documentElement.dataset.chromeLocale = 'en';
  });

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
  beforeEach(() => {
    document.documentElement.dataset.chromeLocale = 'en';
  });

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

// ── per-entry feedback on a wrong placement (optionWhy, #8889 A1-P3) ────────
//
// The component doesn't read HTML5 DataTransfer payloads (it tracks the
// dragged item in local React state), so a plain object stands in for
// DataTransfer across dragStart/dragOver/drop — enough to drive the same
// handlers a real drag would.

function drag(tile: HTMLElement, target: HTMLElement) {
  const dataTransfer = {};
  fireEvent.dragStart(tile, { dataTransfer });
  fireEvent.dragOver(target, { dataTransfer });
  fireEvent.drop(target, { dataTransfer });
}

describe('GroupSort entry why (object entries {text, record, why})', () => {
  beforeEach(() => {
    document.documentElement.dataset.chromeLocale = 'en';
  });

  const groups = {
    Fruits: [{ text: 'apple', why: 'apple is a fruit.' }],
    Vegetables: [{ text: 'carrot', why: 'carrot is a vegetable.' }],
  };

  test('dropping a word in the wrong bucket then checking shows that entry\'s why', () => {
    const { container } = render(<GroupSort groups={groups} />);

    // Drag "apple" into the Vegetables bucket (wrong).
    const appleTile = wordTiles(pool(container)).find((t) => t.textContent?.trim() === 'apple')!;
    drag(appleTile, bucketByName(container, 'Vegetables'));
    // Drag "carrot" into the Vegetables bucket (correct), emptying the pool.
    const carrotTile = wordTiles(pool(container)).find((t) => t.textContent?.trim() === 'carrot')!;
    drag(carrotTile, bucketByName(container, 'Vegetables'));

    const checkBtn = [...container.querySelectorAll<HTMLButtonElement>('button')].find(
      (b) => b.textContent?.trim() === 'Check Answers',
    )!;
    fireEvent.click(checkBtn);

    const why = container.querySelector('[data-activity="group-sort-entry-why"]');
    expect(why).toBeInTheDocument();
    expect(why).toHaveTextContent('apple is a fruit.');
    expect(why).toHaveAttribute('role', 'status');
    expect(why).toHaveAttribute('aria-live', 'polite');
    // The correctly-placed entry gets no why (it isn't wrong).
    expect(bucketByName(container, 'Vegetables').textContent).not.toContain('carrot is a vegetable.');
  });

  test('a correctly-placed entry never shows a why, even when one is authored', () => {
    const { container } = render(<GroupSort groups={groups} />);
    const appleTile = wordTiles(pool(container)).find((t) => t.textContent?.trim() === 'apple')!;
    drag(appleTile, bucketByName(container, 'Fruits'));
    const carrotTile = wordTiles(pool(container)).find((t) => t.textContent?.trim() === 'carrot')!;
    drag(carrotTile, bucketByName(container, 'Vegetables'));

    const checkBtn = [...container.querySelectorAll<HTMLButtonElement>('button')].find(
      (b) => b.textContent?.trim() === 'Check Answers',
    )!;
    fireEvent.click(checkBtn);

    expect(container.querySelector('[data-activity="group-sort-entry-why"]')).not.toBeInTheDocument();
  });

  test('plain string entries (V7 content) keep working exactly as before', () => {
    const legacyGroups = { Fruits: ['apple'], Vegetables: ['carrot'] };
    const { container } = render(<GroupSort groups={legacyGroups} />);
    const texts = wordTiles(pool(container)).map((b) => b.textContent?.trim());
    expect(new Set(texts)).toEqual(new Set(['apple', 'carrot']));
  });

  // #8889 A1-P3 finding 5: plain string entries never gain a live region or
  // an extra wrapper element around the tile — matches main exactly.
  test('plain string entries: checking shows feedback with no live region and no entry-why wrapper', () => {
    const legacyGroups = { Fruits: ['apple'], Vegetables: ['carrot'] };
    const { container } = render(<GroupSort groups={legacyGroups} />);

    const appleTile = wordTiles(pool(container)).find((t) => t.textContent?.trim() === 'apple')!;
    drag(appleTile, bucketByName(container, 'Fruits'));
    const carrotTile = wordTiles(pool(container)).find((t) => t.textContent?.trim() === 'carrot')!;
    drag(carrotTile, bucketByName(container, 'Vegetables'));

    const checkBtn = [...container.querySelectorAll<HTMLButtonElement>('button')].find(
      (b) => b.textContent?.trim() === 'Check Answers',
    )!;
    fireEvent.click(checkBtn);

    const fb = container.querySelector('[data-activity="group-sort-feedback"]');
    expect(fb).toBeInTheDocument();
    expect(fb).not.toHaveAttribute('role');
    expect(fb).not.toHaveAttribute('aria-live');
    expect(container.querySelector('[data-activity="group-sort-entry-why"]')).not.toBeInTheDocument();
    // The tile is not wrapped in an extra flex-column element when the
    // entry has no `why` (that wrapper only appears for {text, why} entries).
    const fruitsTile = wordTiles(bucketByName(container, 'Fruits'))[0];
    expect(fruitsTile.parentElement?.style.display).not.toBe('flex');
  });
});

// ── keyboard-only placement path (#8889 A1-P3 finding 3) ────────────────────
//
// HTML5 drag-and-drop has no native keyboard equivalent, so GroupSort also
// offers: focus + activate an entry (select it), then focus + activate one
// of the group-choice buttons that appear. Both are plain <button>s, so Tab
// reaches them and Enter/Space activates them like any other button —
// verified here with real keyboard events (focus + `user.keyboard`), no
// mouse/click/drag events at all.

describe('GroupSort keyboard-only placement', () => {
  beforeEach(() => {
    document.documentElement.dataset.chromeLocale = 'en';
  });

  const groups = {
    Fruits: [{ text: 'apple', why: 'apple is a fruit.' }],
    Vegetables: [{ text: 'carrot', why: 'carrot is a vegetable.' }],
  };

  test('a keyboard-only learner can place entries into groups and reach a wrong-placement why', async () => {
    const user = userEvent.setup();
    const { container } = render(<GroupSort groups={groups} />);

    // Select "apple" (focus + Enter — a real keyboard activation, not a click).
    const appleTile = wordTiles(pool(container)).find((t) => t.textContent?.trim() === 'apple')!;
    appleTile.focus();
    await user.keyboard('{Enter}');
    expect(appleTile).toHaveAttribute('aria-pressed', 'true');

    // The group chooser appears; place apple into Vegetables (wrong).
    let chooser = container.querySelector('[data-activity="group-sort-chooser"]')!;
    expect(chooser).toBeInTheDocument();
    let vegChoice = [...chooser.querySelectorAll<HTMLButtonElement>('button')].find(
      (b) => b.getAttribute('data-target') === 'Vegetables',
    )!;
    vegChoice.focus();
    await user.keyboard('{Enter}');

    expect(wordTiles(bucketByName(container, 'Vegetables')).map((t) => t.textContent?.trim())).toContain('apple');

    // Select "carrot" and place it into Vegetables (correct) via keyboard too.
    const carrotTile = wordTiles(pool(container)).find((t) => t.textContent?.trim() === 'carrot')!;
    carrotTile.focus();
    await user.keyboard('{Enter}');
    chooser = container.querySelector('[data-activity="group-sort-chooser"]')!;
    vegChoice = [...chooser.querySelectorAll<HTMLButtonElement>('button')].find(
      (b) => b.getAttribute('data-target') === 'Vegetables',
    )!;
    vegChoice.focus();
    await user.keyboard('{Enter}');

    // Check answers — also reached by keyboard (focus + Enter).
    const checkBtn = [...container.querySelectorAll<HTMLButtonElement>('button')].find(
      (b) => b.textContent?.trim() === 'Check Answers',
    )!;
    checkBtn.focus();
    await user.keyboard('{Enter}');

    const why = container.querySelector('[data-activity="group-sort-entry-why"]');
    expect(why).toBeInTheDocument();
    expect(why).toHaveTextContent('apple is a fruit.');
  });

  test('selecting a placed entry and choosing "return to pool" moves it back, by keyboard', async () => {
    const user = userEvent.setup();
    const { container } = render(<GroupSort groups={groups} />);

    const appleTile = wordTiles(pool(container)).find((t) => t.textContent?.trim() === 'apple')!;
    appleTile.focus();
    await user.keyboard('{Enter}');
    let chooser = container.querySelector('[data-activity="group-sort-chooser"]')!;
    let fruitsChoice = [...chooser.querySelectorAll<HTMLButtonElement>('button')].find(
      (b) => b.getAttribute('data-target') === 'Fruits',
    )!;
    fruitsChoice.focus();
    await user.keyboard('{Enter}');
    expect(wordTiles(bucketByName(container, 'Fruits')).map((t) => t.textContent?.trim())).toContain('apple');

    // Re-select the now-placed tile and send it back to the pool.
    const placedApple = wordTiles(bucketByName(container, 'Fruits'))[0];
    placedApple.focus();
    await user.keyboard('{Enter}');
    chooser = container.querySelector('[data-activity="group-sort-chooser"]')!;
    const poolChoice = [...chooser.querySelectorAll<HTMLButtonElement>('button')].find(
      (b) => b.getAttribute('data-target') === '__pool__',
    )!;
    poolChoice.focus();
    await user.keyboard('{Enter}');

    expect(wordTiles(bucketByName(container, 'Fruits'))).toHaveLength(0);
    expect(wordTiles(pool(container)).map((t) => t.textContent?.trim())).toContain('apple');
  });
});
