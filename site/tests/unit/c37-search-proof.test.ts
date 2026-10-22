import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { chromium, type Browser, type Page } from '@playwright/test';
import {
  expectCurrentAtlasArticle,
  foldUkrainian,
  inspectCurrentAtlasArticle,
  inspectHeteronymTab,
} from '../helpers/c37-search-proof';

const origin = 'http://c37.test';
let browser: Browser;
let page: Page;
let html = '';

beforeAll(async () => {
  browser = await chromium.launch({ headless: true });
  page = await browser.newPage();
  await page.route(`${origin}/**`, route => route.fulfill({
    status: 200,
    contentType: 'text/html; charset=utf-8',
    body: html,
  }));
}, 30_000);

afterAll(async () => {
  await browser?.close();
});

async function render(body: string, path: string): Promise<void> {
  html = `<!doctype html><html lang="uk"><head><meta charset="utf-8"></head><body>${body}</body></html>`;
  await page.goto(origin + path);
}

const articlePath = (slug: string): string => `/lexicon/${encodeURIComponent(slug)}/`;

type ArticleOptions = {
  title?: string | null;
  shells?: number;
  errorStates?: number;
  hero?: boolean;
  titleHidden?: boolean;
};

function articleHtml(options: ArticleOptions = {}): string {
  const { title = 'Замо́к', shells = 1, errorStates = 0, hero = true, titleHidden = false } = options;
  const heading = title === null ? '' : `<h1 class="word-title"${titleHidden ? ' hidden' : ''}>${title}</h1>`;
  const heroHtml = hero ? '<div class="word-hero">hero</div>' : '';
  const shell = `<main data-word-atlas>${heading}${heroHtml}</main>`;
  const errors = Array.from({ length: errorStates }, () => '<div data-word-atlas-state="not_found"></div>').join('');
  return `${shell.repeat(shells)}${errors}`;
}

type TabOptions = {
  selected?: [boolean, boolean];
  panelVisible?: [boolean, boolean];
  tabIds?: [string | null, string | null];
  tabControls?: [string | null, string | null];
  panelIds?: [string | null, string | null];
  panelLabelledBy?: [string | null, string | null];
  panelTitles?: [string | null, string | null];
};

function tabHtml(options: TabOptions = {}): string {
  const {
    selected = [true, false],
    panelVisible = [true, false],
    tabIds = ['tab-0', 'tab-1'],
    tabControls = ['panel-0', 'panel-1'],
    panelIds = ['panel-0', 'panel-1'],
    panelLabelledBy = ['tab-0', 'tab-1'],
    panelTitles = ['замо́к', 'за́мок'],
  } = options;
  const attribute = (name: string, value: string | null): string => value === null ? '' : ` ${name}="${value}"`;
  const tabs = [0, 1].map(index => `<button type="button" role="tab"${attribute('id', tabIds[index])}`
    + `${attribute('aria-selected', String(selected[index]))}${attribute('aria-controls', tabControls[index])}>`
    + `${index === 0 ? 'замо́к' : 'за́мок'}</button>`).join('');
  const panels = [0, 1].map(index => {
    if (panelIds[index] === null) return '';
    const title = panelTitles[index] === null ? '' : `<h1 class="word-title">${panelTitles[index]}</h1>`;
    return `<div role="tabpanel" id="${panelIds[index]}"${attribute('aria-labelledby', panelLabelledBy[index])}`
      + `${panelVisible[index] ? '' : ' hidden'}>panel ${index}${title}</div>`;
  }).join('');
  return `<div role="tablist">${tabs}</div>${panels}`;
}

describe('C37 article-arrival oracle', () => {
  it('accepts a ready real article with a folded word title and hero', async () => {
    await render(articleHtml(), articlePath('замок'));

    const arrival = await inspectCurrentAtlasArticle(page, 'замок');

    expect(arrival.ok).toBe(true);
    expect(arrival).toEqual({ ok: true, url: articlePath('замок'), heading: 'Замо́к' });
    await expect(expectCurrentAtlasArticle(page, 'замок', 'ready article')).resolves.toBe('Замо́к');
  });

  it('folds case, stress marks and whitespace without losing Ukrainian letters', () => {
    expect(foldUkrainian('  Замо́к  ')).toBe('замок');
    expect(foldUkrainian('ЗАМОК')).toBe('замок');
    expect(foldUkrainian('за́мок')).toBe('замок');
  });

  it('rejects URL-only navigation even though the legacy URL check accepts it', async () => {
    await render(articleHtml(), articlePath('замок'));
    await page.evaluate(path => window.history.pushState({}, '', path), articlePath('інший'));

    const legacyUrlOnly = new URL(page.url()).pathname === articlePath('інший');
    const arrival = await inspectCurrentAtlasArticle(page, 'інший');

    expect(legacyUrlOnly).toBe(true);
    expect(arrival.ok).toBe(false);
    if (arrival.ok) throw Error('URL-only navigation was accepted as article arrival');
    expect(arrival.reason).toContain('does not contain');
    expect(arrival.heading).toBe('Замо́к');
    await expect(expectCurrentAtlasArticle(page, 'інший', 'url only', 200)).rejects.toThrow(/did not arrive/);
  });

  it('rejects a mismatched pathname before reading the article', async () => {
    await render(articleHtml(), articlePath('замок'));

    const arrival = await inspectCurrentAtlasArticle(page, 'інший');

    expect(arrival.ok).toBe(false);
    if (arrival.ok) throw Error('mismatched pathname was accepted');
    expect(arrival.reason).toContain('is not');
  });

  it('rejects an absent trusted article shell', async () => {
    await render(articleHtml({ shells: 0 }), articlePath('замок'));

    const arrival = await inspectCurrentAtlasArticle(page, 'замок');

    expect(arrival.ok).toBe(false);
    if (arrival.ok) throw Error('absent article shell was accepted');
    expect(arrival.reason).toContain('expected one [data-word-atlas], found 0');
  });

  it('rejects duplicate trusted article shells', async () => {
    await render(articleHtml({ shells: 2 }), articlePath('замок'));

    const arrival = await inspectCurrentAtlasArticle(page, 'замок');

    expect(arrival.ok).toBe(false);
    if (arrival.ok) throw Error('duplicate article shells were accepted');
    expect(arrival.reason).toContain('expected one [data-word-atlas], found 2');
  });

  it('rejects an article shell that reports an error state', async () => {
    await render(articleHtml({ errorStates: 1 }), articlePath('замок'));

    const arrival = await inspectCurrentAtlasArticle(page, 'замок');

    expect(arrival.ok).toBe(false);
    if (arrival.ok) throw Error('error state was accepted');
    expect(arrival.reason).toContain('reported 1 error state');
  });

  it('rejects a hidden or absent word title', async () => {
    await render(articleHtml({ titleHidden: true }), articlePath('замок'));
    const hidden = await inspectCurrentAtlasArticle(page, 'замок');
    expect(hidden.ok).toBe(false);
    if (hidden.ok) throw Error('hidden title was accepted');
    expect(hidden.reason).toContain('no visible current-article word title');

    await render(articleHtml({ title: null }), articlePath('замок'));
    const absent = await inspectCurrentAtlasArticle(page, 'замок');
    expect(absent.ok).toBe(false);
    if (absent.ok) throw Error('absent title was accepted');
    expect(absent.reason).toContain('no visible current-article word title');
  });

  it('rejects an empty or wrong word title', async () => {
    await render(articleHtml({ title: '\u00a0' }), articlePath('замок'));
    const empty = await inspectCurrentAtlasArticle(page, 'замок');
    expect(empty.ok).toBe(false);
    if (empty.ok) throw Error('empty title was accepted');
    expect(empty.reason).toContain('does not contain');

    await render(articleHtml({ title: 'Інше слово' }), articlePath('замок'));
    const wrong = await inspectCurrentAtlasArticle(page, 'замок');
    expect(wrong.ok).toBe(false);
    if (wrong.ok) throw Error('wrong title was accepted');
    expect(wrong.reason).toContain('"Інше слово" does not contain "замок"');
  });

  it('rejects a matching word title without a visible hero', async () => {
    await render(articleHtml({ hero: false }), articlePath('замок'));

    const arrival = await inspectCurrentAtlasArticle(page, 'замок');

    expect(arrival.ok).toBe(false);
    if (arrival.ok) throw Error('title without a hero was accepted');
    expect(arrival.reason).toContain('without an article hero');
  });
});

describe('C37 heteronym tab-activation oracle', () => {
  it('accepts only the selected tab whose matching panel is visible and owned', async () => {
    await render(tabHtml({ selected: [false, true], panelVisible: [false, true] }), articlePath('замок'));

    const active = await inspectHeteronymTab(page, 1);

    expect(active).toEqual({ ok: true, title: 'за́мок' });
  });

  it('rejects an inactive tab even though its panel exists', async () => {
    await render(tabHtml(), articlePath('замок'));

    const legacyPanelPresent = await page.locator('#panel-1').count();
    const inactive = await inspectHeteronymTab(page, 1);

    expect(legacyPanelPresent).toBe(1);
    expect(inactive.ok).toBe(false);
    expect(inactive.reason).toContain('aria-selected="false"');
  });

  it('rejects invalid tab indexes', async () => {
    await render(tabHtml(), articlePath('замок'));

    const past = await inspectHeteronymTab(page, 2);
    const negative = await inspectHeteronymTab(page, -1);

    expect(past.reason).toBe('tab index 2 outside 2 tabs');
    expect(negative.reason).toBe('tab index -1 outside 2 tabs');
  });

  it('rejects a selected tab without aria-controls', async () => {
    await render(tabHtml({ selected: [false, true], panelVisible: [true, true], tabControls: ['panel-0', null] }), articlePath('замок'));

    const arrival = await inspectHeteronymTab(page, 1);

    expect(arrival.ok).toBe(false);
    expect(arrival.reason).toBe('tab 1 has no aria-controls');
  });

  it('rejects a selected tab whose target panel is missing', async () => {
    await render(tabHtml({ selected: [false, true], panelVisible: [true, true], tabControls: ['panel-0', 'panel-9'] }), articlePath('замок'));

    const arrival = await inspectHeteronymTab(page, 1);

    expect(arrival.ok).toBe(false);
    expect(arrival.reason).toBe('panel panel-9 is not visible');
  });

  it('rejects a selected tab whose matching panel is hidden', async () => {
    await render(tabHtml({ selected: [false, true], panelVisible: [true, false] }), articlePath('замок'));

    const arrival = await inspectHeteronymTab(page, 1);

    expect(arrival.ok).toBe(false);
    expect(arrival.reason).toBe('panel panel-1 is not visible');
  });

  it('rejects a visible panel labelled by another tab', async () => {
    await render(tabHtml({ selected: [false, true], panelVisible: [true, true], panelLabelledBy: ['tab-0', 'tab-0'] }), articlePath('замок'));

    const arrival = await inspectHeteronymTab(page, 1);

    expect(arrival.ok).toBe(false);
    expect(arrival.reason).toBe('panel panel-1 labelled by "tab-0", not "tab-1"');
  });

  it('rejects a selected tab without an id', async () => {
    await render(tabHtml({ selected: [false, true], panelVisible: [true, true], tabIds: ['tab-0', null] }), articlePath('замок'));

    const arrival = await inspectHeteronymTab(page, 1);

    expect(arrival.ok).toBe(false);
    expect(arrival.reason).toBe('panel panel-1 labelled by "tab-1", not null');
  });

  it('rejects multiple visible tabpanels', async () => {
    await render(tabHtml({ selected: [false, true], panelVisible: [true, true] }), articlePath('замок'));

    const arrival = await inspectHeteronymTab(page, 1);

    expect(arrival.ok).toBe(false);
    expect(arrival.reason).toBe('expected one visible tabpanel, found 2');
  });

  it('rejects an active panel without a visible word title', async () => {
    await render(tabHtml({ selected: [false, true], panelVisible: [false, true], panelTitles: [null, '\u00a0'] }), articlePath('замок'));

    const arrival = await inspectHeteronymTab(page, 1);

    expect(arrival.ok).toBe(false);
    expect(arrival.reason).toBe('panel panel-1 has no visible word title');
  });
});
