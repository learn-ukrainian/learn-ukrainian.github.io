// AC-02 (#12689): a browser started by the hardened launcher reaches only the
// loopback host and learn-ukrainian.github.io; anything else is aborted and logged.
import { blockedRequests, expect, isAllowedUrl, test } from './support/hardened-browser.mjs';

// Reserved names and documentation addresses: nothing real answers here even if a block failed.
const OUTSIDE_PAGE = 'https://outside.example/';
const OUTSIDE_IMAGE = 'https://cdn.outside.example/pixel.png';
const OUTSIDE_FETCH = 'http://203.0.113.7/data.json';

test('a navigation to an outside origin is aborted and logged', async ({ page, context }) => {
  const error = await page.goto(OUTSIDE_PAGE).then(() => null, (reason: Error) => reason);
  expect(error?.message).toContain('net::ERR_BLOCKED_BY_CLIENT');
  expect(blockedRequests(context)).toEqual([
    expect.objectContaining({ kind: 'document', url: OUTSIDE_PAGE, reason: expect.stringContaining('https://outside.example') }),
  ]);
});

test('subresources to outside origins are aborted and logged', async ({ page, context, baseURL }) => {
  // Serve the probe page from our own origin so only its subresources leave it.
  const probe = new URL('/__origin-allowlist-probe/', baseURL).href;
  await page.route(probe, (route) => route.fulfill({
    contentType: 'text/html; charset=utf-8',
    body: `<!doctype html><img id="pixel" src="${OUTSIDE_IMAGE}">
      <script>window.fetchResult = fetch(${JSON.stringify(OUTSIDE_FETCH)}).then(() => 'loaded', (e) => 'failed: ' + e.name);</script>`,
  }));
  await page.goto(probe);
  expect(await page.evaluate(() => (window as unknown as { fetchResult: Promise<string> }).fetchResult)).toBe('failed: TypeError');
  await expect.poll(() => page.locator('#pixel').evaluate((img: HTMLImageElement) => img.complete && img.naturalWidth)).toBe(0);
  const blocked = blockedRequests(context).map(({ kind, url }) => ({ kind, url }));
  expect(blocked).toEqual(expect.arrayContaining([
    { kind: 'image', url: OUTSIDE_IMAGE },
    { kind: 'fetch', url: OUTSIDE_FETCH },
  ]));
});

test('a request a test lets through still cannot leave the host', async ({ page, context }) => {
  // Page routes run before the allowlist route; the resolver rules are the backstop.
  await page.route(OUTSIDE_PAGE, (route) => route.continue());
  const error = await page.goto(OUTSIDE_PAGE).then(() => null, (reason: Error) => reason);
  expect(error?.message).toContain('net::ERR_NAME_NOT_RESOLVED');
  expect(blockedRequests(context)).toEqual([
    expect.objectContaining({ url: OUTSIDE_PAGE, reason: expect.stringContaining('refused by the resolver') }),
  ]);
});

test('the allowlist is exactly loopback and the published site', () => {
  for (const url of ['http://localhost:4321/', 'http://127.0.0.1/', 'http://[::1]:8080/', 'https://learn-ukrainian.github.io/a1/', 'data:text/plain,x', 'about:blank']) {
    expect(isAllowedUrl(url), url).toBe(true);
  }
  for (const url of [
    'https://example.com/',
    'http://192.0.2.10/',
    'http://0.0.0.0/',
    'https://learn-ukrainian.github.io.outside.example/',
    'https://learn-ukrainian.github.io@outside.example/',
    'https://github.io/',
    'ftp://localhost/',
    'not a url',
  ]) {
    expect(isAllowedUrl(url), url).toBe(false);
  }
});
