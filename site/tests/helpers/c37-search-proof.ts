import { expect, type Page } from '@playwright/test';

// A URL change alone is not article arrival. This predicate reads the rendered
// current Atlas article: exactly one trusted shell, no error state, and a
// word-title heading whose canonical headword equals the navigated slug.
export const foldUkrainian = (value: string): string => value.normalize('NFC')
  .replace(/[\u0300-\u036f]/g, '').toLowerCase()
  .replace(/[^\p{L}\p{N}]+/gu, '-').replace(/^-+|-+$/g, '');

export type ArticleArrival =
  | { ok: true; url: string; heading: string }
  | { ok: false; reason: string; url: string; heading?: string };

export async function inspectCurrentAtlasArticle(page: Page, slug: string): Promise<ArticleArrival> {
  const expected = `/lexicon/${encodeURIComponent(slug)}/`;
  const url = new URL(page.url()).pathname;
  if (url !== expected) return { ok: false, reason: `url ${url} is not ${expected}`, url };
  const article = page.locator('[data-word-atlas]');
  const articles = await article.count();
  if (articles !== 1) return { ok: false, reason: `expected one [data-word-atlas], found ${articles}`, url };
  const errorStates = await page.locator('[data-word-atlas-state]').count();
  if (errorStates !== 0) return { ok: false, reason: `current Atlas shell reported ${errorStates} error state(s)`, url };
  const titles = article.locator('h1.word-title:visible');
  const titlesCount = await titles.count();
  if (titlesCount < 1) return { ok: false, reason: 'no visible current-article word title', url };
  const heading = await titles.first().evaluate(title => {
    const headword = title.cloneNode(true);
    if (!(headword instanceof Element)) throw Error('word title is not an element');
    headword.querySelectorAll('.word-stress').forEach(stress => stress.remove());
    return (headword.textContent ?? '').replace(/\s+/g, ' ').trim();
  });
  const target = foldUkrainian(decodeURIComponent(slug));
  if (!heading || foldUkrainian(heading) !== target) {
    return { ok: false, reason: `visible word title ${JSON.stringify(heading)} does not match ${JSON.stringify(target)}`, url, heading };
  }
  if (!(await article.locator('.word-hero').first().isVisible())) {
    return { ok: false, reason: 'word title rendered without an article hero', url, heading };
  }
  return { ok: true, url, heading };
}

/** Waits for rendering, then asserts real article arrival rather than a bare URL change. */
export async function expectCurrentAtlasArticle(page: Page, slug: string, label: string, timeout = 15_000): Promise<string> {
  await expect.poll(async () => (await inspectCurrentAtlasArticle(page, slug)).ok, {
    message: `${label}: current Atlas article for ${JSON.stringify(slug)} did not arrive`, timeout,
  }).toBe(true);
  const arrival = await inspectCurrentAtlasArticle(page, slug);
  if (!arrival.ok) throw Error(`${label}: ${arrival.reason}`);
  return arrival.heading;
}

/** A tab is active only when its matching tabpanel is exposed and owned by that tab. */
export async function inspectHeteronymTab(page: Page, index: number): Promise<{ ok: boolean; reason?: string; title?: string }> {
  const tabs = page.getByRole('tab');
  const count = await tabs.count();
  if (index < 0 || index >= count) return { ok: false, reason: `tab index ${index} outside ${count} tabs` };
  const tab = tabs.nth(index);
  const selected = await tab.getAttribute('aria-selected');
  if (selected !== 'true') return { ok: false, reason: `tab ${index} aria-selected=${JSON.stringify(selected)}` };
  const controls = await tab.getAttribute('aria-controls');
  if (!controls) return { ok: false, reason: `tab ${index} has no aria-controls` };
  const panel = page.locator(`#${controls}`);
  if (!(await panel.isVisible())) return { ok: false, reason: `panel ${controls} is not visible` };
  const labelledBy = await panel.getAttribute('aria-labelledby');
  const tabId = await tab.getAttribute('id');
  if (!tabId || labelledBy !== tabId) return { ok: false, reason: `panel ${controls} labelled by ${JSON.stringify(labelledBy)}, not ${JSON.stringify(tabId)}` };
  const visiblePanels = await page.locator('[role="tabpanel"]:visible').count();
  if (visiblePanels !== 1) return { ok: false, reason: `expected one visible tabpanel, found ${visiblePanels}` };
  const title = ((await panel.locator('h1.word-title:visible').first().textContent()) ?? '').trim();
  if (!title) return { ok: false, reason: `panel ${controls} has no visible word title` };
  return { ok: true, title };
}
