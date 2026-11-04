// The one hardened Playwright launcher for Node (#12689).
//
// Operator decision 2026-11-03: Playwright runs only against our own trusted
// content. Every browser is the system's auto-updated Google Chrome
// (`channel: 'chrome'`, never Playwright's bundled build), with its sandbox on,
// and it can reach only the loopback host and learn-ukrainian.github.io.
//
// Two layers keep a page inside that allowlist:
// 1. A context route aborts every other request and logs why (AC-02).
// 2. Chrome's resolver refuses every other host name or IP address, so
//    requests a route never sees (redirect hops, service workers, a test's own
//    `route.continue()`) still cannot leave the host. Its failures are logged too.
//
// Python has the same contract in scripts/validate/browser_launcher.py; the
// guard in tests/test_browser_hardening_guard.py keeps every launch on these two.
import { chromium } from 'playwright';
import { test as base, expect } from '@playwright/test';

/** Host names a page may reach. URL host names keep IPv6 brackets; these do not. */
export const ALLOWED_HOSTS = Object.freeze(['localhost', '127.0.0.1', '::1', 'learn-ukrainian.github.io']);

const NETWORK_SCHEMES = new Set(['http:', 'https:', 'ws:', 'wss:']);
// Local schemes never reach the network: page-built data, in-memory blobs,
// about:blank, and files the caller opened on purpose.
const LOCAL_SCHEMES = new Set(['data:', 'blob:', 'about:', 'file:']);

// Chrome's resolver maps every host to "not found" except the allowlist; this
// also covers IP literals, so http://1.1.1.1/ fails as well as example.com.
export const HOST_RESOLVER_RULES = ['MAP * ~NOTFOUND', ...ALLOWED_HOSTS.map((host) => `EXCLUDE ${host}`)].join(', ');

// Launch options a caller may set. Everything else (channel, executablePath, chromiumSandbox,
// args, ignoreDefaultArgs, proxy, env, ...) stays under our control. Callers pass no Chrome
// flags at all: Chrome accepts several spellings of each switch, so a denylist cannot hold.
const CALLER_OPTIONS = new Set(['headless', 'timeout', 'slowMo']);
const RESOLVER_ARG = `--host-resolver-rules=${HOST_RESOLVER_RULES}`;

/** True when a request to `url` may proceed. */
export function isAllowedUrl(url) {
  let parsed;
  try {
    parsed = new URL(url);
  } catch {
    return false;
  }
  if (LOCAL_SCHEMES.has(parsed.protocol)) return true;
  if (!NETWORK_SCHEMES.has(parsed.protocol)) return false;
  const host = parsed.hostname.replace(/^\[(.*)\]$/, '$1').toLowerCase();
  return ALLOWED_HOSTS.includes(host);
}

/** Launch options for installed Chrome with the sandbox on; refuses any other option. */
export function hardenedLaunchOptions(overrides = {}) {
  for (const key of Object.keys(overrides)) {
    if (!CALLER_OPTIONS.has(key)) throw new Error(`hardened launcher: launch option "${key}" is not allowed`);
  }
  // headless stays unset unless given: Playwright defaults to headless and `--headed` keeps working.
  return { ...overrides, channel: 'chrome', chromiumSandbox: true, args: [RESOLVER_ARG] };
}

/** Context options every hardened context uses; service workers would bypass routes. */
export const HARDENED_CONTEXT_OPTIONS = Object.freeze({ serviceWorkers: 'block' });

const blocked = new WeakMap();
const enforced = new WeakSet();

/** The blocked requests recorded for `context`, oldest first. */
export function blockedRequests(context) {
  return blocked.get(context) ?? [];
}

function record(context, log, entry) {
  blocked.get(context).push(entry);
  log(`[origin-allowlist] blocked ${entry.kind} ${entry.url}: ${entry.reason}`);
}

/** Abort and log every request from `context` whose origin is outside the allowlist. */
export async function enforceOriginAllowlist(context, { log = console.warn } = {}) {
  if (enforced.has(context)) return context;
  enforced.add(context);
  blocked.set(context, []);
  const reason = (url) => `origin ${originOf(url)} is not in the allowlist (${ALLOWED_HOSTS.join(', ')})`;
  await context.route(
    (url) => !isAllowedUrl(url.href),
    async (route) => {
      const url = route.request().url();
      record(context, log, { kind: route.request().resourceType(), url, reason: reason(url) });
      await route.abort('blockedbyclient');
    },
  );
  await context.routeWebSocket(
    (url) => !isAllowedUrl(url.href),
    (ws) => {
      record(context, log, { kind: 'websocket', url: ws.url(), reason: reason(ws.url()) });
      ws.close({ code: 1008, reason: 'origin not in allowlist' });
    },
  );
  // Requests the route never sees (redirect hops, a test's own continue()) die
  // in the resolver; log those too so no block is silent.
  context.on('requestfailed', (request) => {
    const url = request.url();
    if (!isAllowedUrl(url) && request.failure()?.errorText === 'net::ERR_NAME_NOT_RESOLVED') {
      record(context, log, { kind: request.resourceType(), url, reason: `${reason(url)}; refused by the resolver` });
    }
  });
  return context;
}

function originOf(url) {
  try {
    const { origin, protocol } = new URL(url);
    return origin === 'null' ? protocol : origin;
  } catch {
    return '(unparseable)';
  }
}

/** Make every context and page `browser` creates block service workers and enforce the allowlist. */
function hardenBrowser(browser, { log = console.warn } = {}) {
  const newContext = browser.newContext.bind(browser);
  browser.newContext = async (options = {}) => {
    // A context proxy on the loopback host could carry requests the resolver would refuse.
    if (options.proxy) throw new Error('hardened launcher: a context proxy is not allowed');
    const context = await newContext({ ...options, ...HARDENED_CONTEXT_OPTIONS });
    return enforceOriginAllowlist(context, { log });
  };
  // Same contract as Browser.newPage: a fresh context that closes with its page.
  browser.newPage = async (options = {}) => {
    const context = await browser.newContext(options);
    const page = await context.newPage();
    page.once('close', () => context.close().catch(() => {}));
    return page;
  };
  return browser;
}

/** Launch installed Chrome, sandbox on, with every context and page hardened. */
export async function launchHardenedChromium(overrides = {}, { log = console.warn } = {}) {
  return hardenBrowser(await chromium.launch(hardenedLaunchOptions(overrides)), { log });
}

/** A `browserType` for libraries that launch their own browser (rehype-mermaid). */
export const hardenedChromium = Object.freeze({
  launch: (options = {}) => launchHardenedChromium(options),
});

// What the Playwright configs set; a spec's test.use() must not change it.
function assertHardenedRun({ browserName, channel, launchOptions, connectOptions }) {
  // A connected browser was started elsewhere, so nothing here can show it is sandboxed.
  // Playwright also reads this from PW_TEST_CONNECT_WS_ENDPOINT.
  if (connectOptions) {
    throw new Error('hardened launcher: connecting to a browser started elsewhere is not allowed (connectOptions, PW_TEST_CONNECT_WS_ENDPOINT)');
  }
  // Fail closed on any other launch option (a launch-level proxy, extra Chrome flags, ...).
  const args = launchOptions?.args ?? [];
  const unknown = Object.keys(launchOptions ?? {}).filter((key) => !CALLER_OPTIONS.has(key) && !['channel', 'chromiumSandbox', 'args'].includes(key));
  if (unknown.length || browserName !== 'chromium' || channel !== 'chrome' || launchOptions?.channel !== 'chrome'
    || launchOptions?.chromiumSandbox !== true || args.length !== 1 || args[0] !== RESOLVER_ARG) {
    throw new Error('hardened launcher: this run must use installed Chrome with hardenedLaunchOptions() (see playwright.config.ts)');
  }
}

/**
 * Playwright Test `test` for every spec. It refuses a run whose browser options differ
 * from the hardened config, and every context enforces the allowlist.
 *
 * The browser fixture does not take Playwright's own browser: that one is launched or
 * connected before this fixture could check anything. It checks first, then launches
 * through launchHardenedChromium. Playwright Test's defaults (headless, traces and
 * artifacts directories) still apply, because both use the same Playwright instance.
 */
export const test = base.extend({
  browser: [async ({ browserName, channel, launchOptions, connectOptions }, use) => {
    assertHardenedRun({ browserName, channel, launchOptions, connectOptions });
    const callerOptions = Object.fromEntries(Object.entries(launchOptions).filter(([key]) => CALLER_OPTIONS.has(key)));
    const browser = await launchHardenedChromium(callerOptions);
    try {
      await use(browser);
    } finally {
      await browser.close({ reason: 'Test ended.' });
    }
  }, { scope: 'worker', timeout: 0 }],
  context: async ({ context, serviceWorkers, proxy }, use) => {
    if (serviceWorkers !== 'block' || proxy) {
      throw new Error("hardened launcher: contexts keep serviceWorkers 'block' and no proxy");
    }
    await enforceOriginAllowlist(context);
    await use(context);
  },
});

export { expect };
