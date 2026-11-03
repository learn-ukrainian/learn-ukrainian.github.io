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

// Flags that turn a sandbox layer off or move traffic around the resolver rules.
const FORBIDDEN_ARG = /^--(no-sandbox|disable-setuid-sandbox|disable-namespace-sandbox|disable-seccomp-filter-sandbox|disable-gpu-sandbox|no-zygote-sandbox|no-zygote|single-process|host-resolver-rules|host-rules|proxy-server|proxy-pac-url|proxy-bypass-list)(=|$)/;
// Launch options a caller may set. Everything else (channel, executablePath,
// chromiumSandbox, ignoreDefaultArgs, proxy, env, ...) stays under our control.
const CALLER_OPTIONS = new Set(['headless', 'timeout', 'slowMo', 'args']);

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

/** Launch options for installed Chrome with the sandbox on; refuses anything that weakens them. */
export function hardenedLaunchOptions(overrides = {}) {
  for (const key of Object.keys(overrides)) {
    if (!CALLER_OPTIONS.has(key)) throw new Error(`hardened launcher: launch option "${key}" is not allowed`);
  }
  // headless stays unset unless given: Playwright defaults to headless and `--headed` keeps working.
  const { args: extra = [], ...scalars } = overrides;
  for (const arg of extra) {
    if (FORBIDDEN_ARG.test(String(arg))) throw new Error(`hardened launcher: Chrome flag "${arg}" is not allowed`);
  }
  return {
    ...scalars,
    channel: 'chrome',
    chromiumSandbox: true,
    args: [`--host-resolver-rules=${HOST_RESOLVER_RULES}`, ...extra],
  };
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

/**
 * Launch installed Chrome, sandbox on. Every context and page it creates
 * blocks service workers and enforces the origin allowlist.
 */
export async function launchHardenedChromium(overrides = {}, { log = console.warn } = {}) {
  const browser = await chromium.launch(hardenedLaunchOptions(overrides));
  const newContext = browser.newContext.bind(browser);
  browser.newContext = async (options = {}) => {
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

/** A `browserType` for libraries that launch their own browser (rehype-mermaid). */
export const hardenedChromium = Object.freeze({
  launch: (options = {}) => launchHardenedChromium(options),
});

/** Playwright Test `test` whose every context enforces the allowlist. Specs import this. */
export const test = base.extend({
  context: async ({ context }, use) => {
    await enforceOriginAllowlist(context);
    await use(context);
  },
});

export { expect };
