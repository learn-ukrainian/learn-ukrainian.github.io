// @vitest-environment node

import { afterAll, beforeAll, describe, expect, test } from 'vitest';
import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import { Window, type Document, type Element } from 'happy-dom';
import Home from '../../src/pages/index.astro';
import CourseLayout from '../../src/layouts/CourseLayout.astro';
import { CHROME_STRINGS } from '../../src/lib/i18n/chrome';

const editions = ['/a1/', '/a1-v1/'];

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

  test('home actions open either edition and keep Start A1 canonical', () => {
    const actions = home.querySelector('.home-actions')!;
    requireBothEditions(actions);
    expect(actions.querySelector('.home-primary')?.getAttribute('href')).toBe('/a1/');
    expect(actions.querySelector('a[href="/a1-v1/"]')?.textContent).toContain('Open previous A1');
  });

  test('Available Now has adjacent, distinctly labelled edition cards in both locales', () => {
    const cards = home.querySelector('.lu-card-grid')!;
    requireBothEditions(cards);
    const current = cards.querySelector('a[href="/a1/"]')!;
    const previous = cards.querySelector('a[href="/a1-v1/"]')!;
    expect(current.nextElementSibling).toBe(previous);
    for (const locale of ['en', 'uk'] as const) {
      expect(current.querySelector(`h3 [data-loc="${locale}"]`)?.textContent)
        .toBe(CHROME_STRINGS[locale]['home.track.a1New']);
      expect(previous.querySelector(`h3 [data-loc="${locale}"]`)?.textContent)
        .toBe(CHROME_STRINGS[locale]['home.track.a1Previous']);
    }
    expect(previous.textContent).toContain('55');
    expect(current.textContent).toContain('landing only');
  });

  test('course ladder links both editions and shows the complete previous course', () => {
    const ladder = home.querySelector('.track-column')!;
    requireBothEditions(ladder);
    expect(ladder.querySelector('a[href="/a1-v1/"]')?.textContent).toContain('55');
  });

  test.each(editions)('desktop and mobile header retain both editions on %s', async (currentPath) => {
    const container = await AstroContainer.create();
    const page = parse(await container.renderToString(CourseLayout as any, {
      props: { title: 'Course', currentPath },
    }));
    for (const label of ['Primary', 'Mobile primary']) {
      const nav = page.querySelector(`header nav[aria-label="${label}"]`)!;
      requireBothEditions(nav);
      expect(nav.querySelectorAll('a[aria-current="page"]')).toHaveLength(1);
      expect(nav.querySelector('a[aria-current="page"]')?.getAttribute('href')).toBe(currentPath);
      for (const locale of ['en', 'uk'] as const) {
        expect(nav.querySelector(`a[href="/a1-v1/"] [data-loc="${locale}"]`)?.textContent)
          .toBe(CHROME_STRINGS[locale]['nav.a1Previous']);
      }
    }
  });

  test('English and Ukrainian cover the same chrome keys', () => {
    expect(Object.keys(CHROME_STRINGS.uk).sort()).toEqual(Object.keys(CHROME_STRINGS.en).sort());
  });
});
