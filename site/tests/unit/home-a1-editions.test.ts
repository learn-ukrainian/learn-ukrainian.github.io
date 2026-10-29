// @vitest-environment node

import { afterAll, beforeAll, describe, expect, test, vi } from 'vitest';
import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import { Window, type Document, type Element } from 'happy-dom';
import Home from '../../src/pages/index.astro';
import CourseLayout from '../../src/layouts/CourseLayout.astro';
import { CHROME_STRINGS } from '../../src/lib/i18n/chrome';
import { readFileSync } from 'node:fs';
import yaml from 'js-yaml';
import unpublished from '../fixtures/arc-a1/unpublished.json';
import openingPublished from '../fixtures/arc-a1/opening-published.json';
import { deriveA1PrimaryHref, levelEntryHref } from '../../src/lib/a1-entry';

const editions = ['/a1/', '/a1-v1/'];

// The suite never reads the live arc data: publication state comes from these fixtures.
vi.mock('../../src/data/arc-a1.json', async () => ({
  default: (await import('../fixtures/arc-a1/unpublished.json')).default,
}));

const windows: Window[] = [];

function parse(html: string) {
  const window = new Window();
  windows.push(window);
  window.document.write(html);
  return window.document;
}

afterAll(async () => {
  await Promise.all(windows.map((window) => window.happyDOM.abort()));
});

function requireBothEditions(root: Document | Element): void {
  for (const href of editions) {
    expect(root.querySelector(`a[href="${href}"]`), href).not.toBeNull();
  }
}

describe('public A1 edition entry points', () => {
  let home: ReturnType<typeof parse>;

  beforeAll(async () => {
    const container = await AstroContainer.create();
    home = parse(await container.renderToString(Home as any));
  });

  test('home actions start the usable course and label the preparation edition', () => {
    const actions = home.querySelector('.home-actions')!;
    requireBothEditions(actions);
    expect(actions.querySelector('.home-primary')?.getAttribute('href')).toBe('/a1-v1/');
    expect(actions.querySelector('a[href="/a1/"]')?.textContent).toContain('in preparation');
    expect(home.querySelector('.home-intro')?.textContent).not.toMatch(/archive|архів/);
  });

  test('Available Now has adjacent, distinctly labelled edition cards in both locales', () => {
    const cards = home.querySelector('.lu-card-grid')!;
    requireBothEditions(cards);
    const current = cards.querySelector('a[href="/a1/"]')!;
    const previous = cards.querySelector('a[href="/a1-v1/"]')!;
    expect(cards.firstElementChild).toBe(previous);
    expect(previous.nextElementSibling).toBe(current);
    for (const locale of ['en', 'uk'] as const) {
      expect(current.querySelector(`h3 [data-loc="${locale}"]`)?.textContent)
        .toBe(CHROME_STRINGS[locale]['home.track.a1Preparing']);
      expect(previous.querySelector(`h3 [data-loc="${locale}"]`)?.textContent)
        .toBe(CHROME_STRINGS[locale]['home.track.a1Available']);
    }
    expect(previous.textContent).toContain('55');
    expect(current.textContent).toContain('in preparation');
  });

  test('course ladder links both editions and shows the complete previous course', () => {
    const ladder = home.querySelector('.track-column')!;
    requireBothEditions(ladder);
    expect(ladder.querySelector('a[href="/a1-v1/"]')?.textContent).toContain('55');
    expect(ladder.querySelector('a')?.getAttribute('href')).toBe('/a1-v1/');
    expect(ladder.querySelector('a[href="/a1/"]')?.textContent).toContain('in preparation');
  });

  test('course map shows the manifest-derived module count on every linked track row (from curriculum.yaml)', () => {
    // The manifest, not the generated JSON, is the oracle: a stale stats file must fail here.
    const manifest = yaml.load(
      readFileSync(new URL('../../../curriculum/l2-uk-en/curriculum.yaml', import.meta.url), 'utf8'),
    ) as { levels: Record<string, { modules?: string[] }> };
    const rows = [...home.querySelectorAll('.track-inventory-grid a.track-link')];
    const shown = new Map(rows.map((row) => [
      row.getAttribute('href')!.replaceAll('/', ''),
      row.querySelector('.track-meta')!.textContent!.trim(),
    ]));
    // #9754: the tracks whose counts were stale must be on the map, with their current counts.
    for (const id of ['c1', 'bio', 'folk']) {
      expect(shown.has(id), id).toBe(true);
    }
    for (const [id, meta] of shown) {
      expect(meta, id).toMatch(new RegExp(`^${manifest.levels[id].modules!.length}\\s`));
    }
  });

  test.each(editions)('desktop and mobile header retain both editions on %s', async (currentPath) => {
    const container = await AstroContainer.create();
    const page = parse(await container.renderToString(CourseLayout as any, {
      props: { title: 'Course', currentPath },
    }));
    // #8730: responsive navigation must not hide the only preference controls.
    const controls = page.querySelector('.lu-header-controls')!;
    expect(controls.closest('.lu-header-inner')).not.toBeNull();
    expect(controls.closest('nav, details')).toBeNull();
    expect([...controls.querySelectorAll('button')].map((button) => [
      button.id, button.getAttribute('type'), button.getAttribute('aria-label'),
    ])).toEqual([
      ['lu-theme-toggle', 'button', 'Toggle dark and light theme'],
      ['lu-locale-toggle', 'button', 'Switch interface language (English / Ukrainian)'],
    ]);
    expect(page.querySelectorAll('#lu-theme-toggle')).toHaveLength(1);
    expect(page.querySelectorAll('#lu-locale-toggle')).toHaveLength(1);
    expect(controls.previousElementSibling?.getAttribute('aria-label')).toBe('Primary');
    expect(controls.nextElementSibling?.className).toBe('lu-mobile-menu');
    for (const label of ['Primary', 'Mobile primary']) {
      const nav = page.querySelector(`header nav[aria-label="${label}"]`)!;
      requireBothEditions(nav);
      expect(nav.querySelectorAll('a[aria-current="page"]')).toHaveLength(1);
      expect(nav.querySelector('a[aria-current="page"]')?.getAttribute('href')).toBe(currentPath);
      for (const locale of ['en', 'uk'] as const) {
        expect(nav.querySelector(`a[href="/a1-v1/"] [data-loc="${locale}"]`)?.textContent)
          .toBe(CHROME_STRINGS[locale]['nav.a1']);
        expect(nav.querySelector(`a[href="/a1/"] [data-loc="${locale}"]`)?.textContent)
          .toBe(CHROME_STRINGS[locale]['home.track.a1Preparing']);
      }
    }
    expect(page.querySelector('footer a[href="/a1-v1/"]')).not.toBeNull();
  });

  test('English and Ukrainian cover the same chrome keys', () => {
    expect(Object.keys(CHROME_STRINGS.uk).sort()).toEqual(Object.keys(CHROME_STRINGS.en).sort());
  });

  test('publication derivation cannot promote an empty or incomplete opening module or a later lesson', () => {
    const opening = { position: 1, lesson_numbers: [1, 2], built_lessons: [] };
    const later = { position: 2, lesson_numbers: [1], built_lessons: [1] };
    expect(deriveA1PrimaryHref([])).toBe('/a1-v1/');
    expect(deriveA1PrimaryHref(unpublished.positions)).toBe('/a1-v1/');
    expect(deriveA1PrimaryHref(openingPublished.positions)).toBe('/a1/');
    expect(deriveA1PrimaryHref([opening, later])).toBe('/a1-v1/');
    expect(deriveA1PrimaryHref([{ ...opening, built_lessons: [1] }])).toBe('/a1-v1/');
    expect(deriveA1PrimaryHref([{ ...opening, lesson_numbers: [], built_lessons: [1, 2] }])).toBe('/a1-v1/');
    expect(deriveA1PrimaryHref([later])).toBe('/a1-v1/');
    expect(deriveA1PrimaryHref([later, { ...opening, built_lessons: [2, 1] }])).toBe('/a1/');
    expect(levelEntryHref('A1')).toBe('/a1-v1/');
    expect(levelEntryHref('B2')).toBe('/b2/');
  });

  test('publishing the opening module automatically promotes home, map, header, footer and picker together', async () => {
    vi.resetModules();
    vi.doMock('../../src/data/arc-a1.json', () => ({ default: openingPublished }));
    try {
      const { default: PromotedHome } = await import('../../src/pages/index.astro');
      const { levelEntryHref: promotedLevelHref } = await import('../../src/lib/a1-entry');
      const container = await AstroContainer.create();
      const promoted = parse(await container.renderToString(PromotedHome));
      expect(promoted.querySelector('.home-primary')?.getAttribute('href')).toBe('/a1/');
      expect(promoted.querySelector('.home-actions a[href="/a1-v1/"]')?.textContent).toContain('Open previous A1');
      expect(promoted.querySelector('.lu-card-grid a')?.getAttribute('href')).toBe('/a1/');
      expect(promoted.querySelector('.lu-card-grid a')?.textContent).toContain('opening module is available');
      expect(promoted.querySelector('.track-column a')?.getAttribute('href')).toBe('/a1/');
      expect(promoted.querySelector('.track-column a')?.textContent).not.toContain('planned');
      expect(promoted.querySelector('header nav a[href="/a1/"] [data-loc="en"]')?.textContent).toBe('A1');
      expect(promoted.querySelector('footer a[href="/a1/"]')).not.toBeNull();
      expect(promoted.querySelector('header nav a[href="/a1-v1/"] [data-loc="en"]')?.textContent).toBe('A1 previous');
      expect(promotedLevelHref('A1')).toBe('/a1/');
      expect(promoted.textContent).not.toContain('in preparation');
    } finally {
      vi.doUnmock('../../src/data/arc-a1.json');
      vi.resetModules();
    }
  });
});
