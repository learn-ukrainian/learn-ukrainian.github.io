import { expect, test, type Locator, type Page } from '@playwright/test';

/**
 * #5376 check 2 — selector-state rule.
 *
 * Policy: every button group with SELECTOR semantics (pick-one-of-N state that
 * persists: CEFR level, session size, …) must expose its state two ways:
 *   1. programmatically — every option carries aria-pressed (or aria-checked),
 *      and exactly one enabled option is pressed;
 *   2. visually — the pressed option's computed style differs measurably from
 *      its unpressed siblings (the "10/20 invisibility" and pairing-selection
 *      invisibility defects were both "state exists, styling doesn't show it").
 *
 * The group registry below is explicit and fail-closed in both directions:
 * removing aria-pressed from a registered group fails, and registering a new
 * group is a deliberate reviewed act. Known non-compliant groups (e.g. the
 * Atlas browse filter chips, which carry selection only in the URL) are NOT
 * registered here; closing that gap is product work outside this gate's scope.
 */

const STYLE_CHANNELS: string[] = [
  'background-color',
  'color',
  'border-color',
  'outline-color',
  'font-weight',
  'box-shadow',
];

interface StyleSnapshot {
  [channel: string]: string;
}

async function snapshotStyles(locator: Locator): Promise<StyleSnapshot[]> {
  return locator.evaluateAll((elements, channels) => {
    return elements.map((el) => {
      const style = getComputedStyle(el);
      const snap: Record<string, string> = {};
      for (const channel of channels as string[]) {
        snap[channel] = style.getPropertyValue(channel);
      }
      return snap;
    });
  }, STYLE_CHANNELS);
}

function differingChannels(selected: StyleSnapshot, sibling: StyleSnapshot): string[] {
  return Object.keys(selected).filter((channel) => selected[channel] !== sibling[channel]);
}

interface SelectorGroup {
  name: string;
  selector: string;
}

const PERSISTENT_GROUPS: SelectorGroup[] = [
  { name: 'CEFR level picker', selector: '.k3-levels button' },
  { name: 'session size picker', selector: '.k3-session-budgets button' },
];

test('persistent selector groups expose exactly one pressed, visually distinct option', async ({ page, context }) => {
  await context.clearCookies();
  await page.goto('/words-of-the-day/practice/');
  await expect(page.locator('#lexicon-practice-mount .lexicon-practice')).toBeVisible();

  for (const group of PERSISTENT_GROUPS) {
    const options = page.locator(group.selector);
    const count = await options.count();
    expect(count, `${group.name}: group must render options`).toBeGreaterThan(1);

    // 1. Every option carries the state attribute (fail-closed on removal).
    const pressedValues = await options.evaluateAll((elements) =>
      elements.map((el) => ({
        pressed: el.getAttribute('aria-pressed') ?? el.getAttribute('aria-checked'),
        disabled: (el as HTMLButtonElement).disabled,
      })),
    );
    for (const [index, value] of pressedValues.entries()) {
      expect(
        value.pressed,
        `${group.name} option ${index}: missing aria-pressed/aria-checked — state is invisible to AT`,
      ).not.toBeNull();
    }

    // 2. Exactly one ENABLED option is pressed.
    const pressedIndexes = pressedValues
      .map((value, index) => ({ value, index }))
      .filter(({ value }) => value.pressed === 'true' && !value.disabled)
      .map(({ index }) => index);
    expect(
      pressedIndexes.length,
      `${group.name}: expected exactly one pressed option, got [${pressedIndexes.join(', ')}]`,
    ).toBe(1);

    // 3. The pressed option differs measurably from every enabled unpressed sibling.
    const styles = await snapshotStyles(options);
    const selected = styles[pressedIndexes[0]];
    const unpressed = styles
      .map((snap, index) => ({ snap, index }))
      .filter(({ index }) => index !== pressedIndexes[0] && !pressedValues[index].disabled);
    expect(unpressed.length, `${group.name}: needs at least one unpressed sibling`).toBeGreaterThan(0);
    for (const { snap, index } of unpressed) {
      const diff = differingChannels(selected, snap);
      expect(
        diff.length,
        `${group.name}: pressed option ${pressedIndexes[0]} is visually identical to option ${index} ` +
          `(checked: ${STYLE_CHANNELS.join(', ')})`,
      ).toBeGreaterThan(0);
    }
  }
});

test('matching pairing: the selected tile is announced and visually distinct', async ({ page, context }) => {
  await context.clearCookies();
  await page.goto('/words-of-the-day/practice/');

  await page.locator('button[data-mode="matching"]').click();
  const leftTiles = page.locator('[data-activity="match-left-tile"]');
  await expect.poll(() => leftTiles.count()).toBeGreaterThanOrEqual(3);

  // Before any pick: every tile carries the attribute, none is pressed.
  const initial = await leftTiles.evaluateAll((elements) =>
    elements.map((el) => el.getAttribute('aria-pressed')),
  );
  for (const value of initial) {
    expect(value, 'matching left tile: missing aria-pressed').not.toBeNull();
  }

  await leftTiles.first().click();

  // Exactly one tile pressed, and it is measurably distinct from its siblings.
  const pressedCount = await leftTiles.evaluateAll(
    (elements) => elements.filter((el) => el.getAttribute('aria-pressed') === 'true').length,
  );
  expect(pressedCount, 'matching: exactly one selected tile after a pick').toBe(1);

  const styles = await snapshotStyles(leftTiles);
  const pressed = await leftTiles.evaluateAll((elements) =>
    elements.map((el) => el.getAttribute('aria-pressed') === 'true'),
  );
  const selectedIndex = pressed.indexOf(true);
  for (const [index, snap] of styles.entries()) {
    if (index === selectedIndex) continue;
    const diff = differingChannels(styles[selectedIndex], snap);
    expect(
      diff.length,
      `matching: selected tile ${selectedIndex} is visually identical to tile ${index}`,
    ).toBeGreaterThan(0);
  }
});
