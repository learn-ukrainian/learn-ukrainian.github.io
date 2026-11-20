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
// tests/test_browser_hardening_guard.py checks for launches outside this module.
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
// args, ignoreDefaultArgs, proxy, env, ...) stays under our control.
const CALLER_OPTIONS = new Set(['headless', 'timeout', 'slowMo']);
const CHROME_ARGS = ['--enable-automation', `--host-resolver-rules=${HOST_RESOLVER_RULES}`];
const SANDBOX_URL = 'chrome://sandbox/';
const SANDBOX_ROWS = new Map([
  ['Layer 1 Sandbox', 'Namespace'],
  ['PID namespaces', 'Yes'],
  ['Network namespaces', 'Yes'],
  ['Seccomp-BPF sandbox', 'Yes'],
]);
const FORBIDDEN_SWITCHES = new Set([
  'no-sandbox',
  'disable-namespace-sandbox',
  'disable-setuid-sandbox',
  'disable-seccomp-filter-sandbox',
  'disable-gpu-sandbox',
  'disable-webnn-compiler-sandbox',
  'allow-sandbox-debugging',
  'no-zygote',
  // Chrome only adds this to its unsandboxed zygote child. CDP reports the main process.
  'no-zygote-sandbox',
  'single-process',
  'in-process-gpu',
]);

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
  const callerOptions = { ...overrides };
  for (const key of Object.keys(callerOptions)) {
    if (!CALLER_OPTIONS.has(key)) throw new Error(`hardened launcher: launch option "${key}" is not allowed`);
  }
  // headless stays unset unless given: Playwright defaults to headless and `--headed` keeps working.
  return { ...callerOptions, channel: 'chrome', chromiumSandbox: true, args: [...CHROME_ARGS] };
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

async function verifySandbox(browser) {
  const context = await browser.newContext(HARDENED_CONTEXT_OPTIONS);
  try {
    const page = await context.newPage();
    await page.goto(SANDBOX_URL, { timeout: 15_000 });
    if (page.url() !== SANDBOX_URL) throw new Error('Chrome did not load chrome://sandbox');

    const rows = await page.locator('#sandbox-status tr').evaluateAll(
      (elements) => elements.map((row) => Array.from(row.cells, (cell) => cell.textContent.trim())),
    );
    for (const [label, expected] of SANDBOX_ROWS) {
      const matches = rows.filter(([name]) => name === label);
      if (matches.length !== 1 || matches[0].length !== 2 || matches[0][1] !== expected) {
        throw new Error(`chrome://sandbox did not report "${label}" = "${expected}" exactly once`);
      }
    }
  } finally {
    await context.close();
  }
}

async function verifyBrowserCommandLine(browser) {
  const session = await browser.newBrowserCDPSession();
  try {
    const { arguments: argv } = await session.send('Browser.getBrowserCommandLine');
    if (!Array.isArray(argv) || !argv[0] || argv.some((arg) => typeof arg !== 'string')) {
      throw new Error('Chrome did not return a valid browser command line');
    }
    const switches = new Set(argv.slice(1).map((arg) => /^--?([^=]+)/.exec(arg)?.[1]));
    if (!switches.has('enable-automation')) throw new Error('Chrome command line lacks enable-automation');
    for (const name of FORBIDDEN_SWITCHES) {
      if (switches.has(name)) throw new Error(`Chrome command line contains forbidden switch --${name}`);
    }
  } finally {
    await session.detach();
  }
}

/** Launch installed Chrome and verify its sandbox before giving it to the caller. */
export async function launchHardenedChromium(overrides = {}, { log = console.warn } = {}) {
  const browser = await chromium.launch(hardenedLaunchOptions(overrides));
  try {
    await verifySandbox(browser);
    await verifyBrowserCommandLine(browser);
    console.info('[chrome-sandbox] Namespace, PID namespaces, network namespaces, Seccomp-BPF and command line verified');
    return hardenBrowser(browser, { log });
  } catch (error) {
    await browser.close();
    throw new Error(`hardened launcher: ${error.message}`, { cause: error });
  }
}

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
    || launchOptions?.chromiumSandbox !== true || args.length !== CHROME_ARGS.length
    || CHROME_ARGS.some((arg, index) => args[index] !== arg)) {
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
