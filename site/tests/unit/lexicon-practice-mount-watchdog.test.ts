import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

const mountSource = readFileSync(resolve(process.cwd(), "src/lexicon/LexiconPracticeMount.astro"), "utf8");
const inlineScript = mountSource.match(/<script is:inline>\s*([\s\S]*?)\s*<\/script>/)![1]!;
const RETRY_DELAY_MS = 30_000;

function runInlineWatchdog(): void {
  // Exercise the actual import-free script shipped in the static HTML.
  (0, eval)(inlineScript);
}

function element(id: string): HTMLElement {
  return document.getElementById(`lexicon-practice-${id}`)!;
}

function hydrate(): void {
  element("mount").querySelector("astro-island")!.dispatchEvent(new Event("astro:hydrate"));
}

function fail(): void {
  element("mount").querySelector("astro-island")!.dispatchEvent(new Event("astro:hydration-error"));
}

function expectReady(): void {
  expect(element("mount").hidden).toBe(false);
  expect(element("shell").hidden).toBe(true);
  expect(element("fallback").hidden).toBe(true);
  expect(vi.getTimerCount()).toBe(0);
}

describe("practice hydration recovery", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    document.body.innerHTML = `
      <div id="lexicon-practice-mount">
        <div id="lexicon-practice-shell" role="status" aria-busy="true">Завантаження практики…</div>
        <astro-island component-url="/_astro/LexiconPractice.test.js"></astro-island>
      </div>
      <div id="lexicon-practice-fallback" hidden>
        <p id="lexicon-practice-error">Не вдалося завантажити практику.</p>
        <button type="button">Спробувати ще раз</button>
      </div>`;
  });

  afterEach(() => {
    document.dispatchEvent(new Event("astro:before-swap"));
    vi.useRealTimers();
    vi.restoreAllMocks();
    document.body.innerHTML = "";
  });

  test("offers retry once for slow hydration without claiming failure or hiding the island", async () => {
    const resourceTiming = vi.spyOn(performance, "getEntriesByType");
    runInlineWatchdog();
    expect(vi.getTimerCount()).toBe(1);
    await vi.advanceTimersByTimeAsync(RETRY_DELAY_MS - 1);
    expect(element("fallback").hidden).toBe(true);
    await vi.advanceTimersByTimeAsync(1);
    expect(element("fallback").hidden).toBe(false);
    expect(element("error").hidden).toBe(true);
    expect(element("shell").hidden).toBe(false);
    expect(element("mount").hidden).toBe(false);
    expect(resourceTiming).not.toHaveBeenCalled();
    expect(vi.getTimerCount()).toBe(0);
    await vi.advanceTimersByTimeAsync(60_000);
    hydrate();
    expectReady();
  });

  test("explicit errors show retry immediately and late hydration recovers", async () => {
    runInlineWatchdog();
    fail();
    expect(element("fallback").hidden).toBe(false);
    expect(element("error").hidden).toBe(false);
    expect(element("shell").hidden).toBe(true);
    expect(element("mount").hidden).toBe(true);
    expect(vi.getTimerCount()).toBe(0);
    await vi.advanceTimersByTimeAsync(RETRY_DELAY_MS);
    expect(element("error").hidden).toBe(false);
    hydrate();
    expectReady();
  });

  test("an explicit error after slow retry replaces loading with error", async () => {
    runInlineWatchdog();
    await vi.advanceTimersByTimeAsync(RETRY_DELAY_MS);
    fail();
    expect(element("error").hidden).toBe(false);
    expect(element("shell").hidden).toBe(true);
    hydrate();
    expectReady();
  });

  test("non-bubbling hydration cancels recovery resources and ignores late errors", async () => {
    runInlineWatchdog();
    hydrate();
    expectReady();
    fail();
    await vi.advanceTimersByTimeAsync(RETRY_DELAY_MS);
    expectReady();
  });

  test.each([false, true])("rendered content recovers via the observer, after error=%s", async (afterError) => {
    runInlineWatchdog();
    if (afterError) fail();
    element("mount").querySelector("astro-island")!.innerHTML = '<div class="lexicon-practice"></div>';
    await vi.advanceTimersByTimeAsync(0);
    expectReady();
  });

  test("already rendered content settles immediately", () => {
    element("mount").querySelector("astro-island")!.innerHTML = '<div class="lexicon-practice"></div>';
    runInlineWatchdog();
    expectReady();
  });

  test("unrelated island events cannot settle or fail practice", () => {
    runInlineWatchdog();
    const other = document.createElement("astro-island");
    document.body.appendChild(other);
    other.dispatchEvent(new Event("astro:hydrate"));
    other.dispatchEvent(new Event("astro:hydration-error"));
    document.dispatchEvent(new CustomEvent("astro:hydration-error", {
      detail: { componentUrl: "/_astro/LexiconPractice.other.js" },
    }));
    expect(element("shell").hidden).toBe(false);
    expect(element("fallback").hidden).toBe(true);
    expect(vi.getTimerCount()).toBe(1);
  });

  test("document errors require the exact island component URL", () => {
    runInlineWatchdog();
    document.dispatchEvent(new CustomEvent("astro:hydration-error", {
      detail: { componentUrl: "/_astro/LexiconPractice.test.js" },
    }));
    expect(element("fallback").hidden).toBe(false);
    expect(element("error").hidden).toBe(false);
    expect(vi.getTimerCount()).toBe(0);
  });

  test("navigation disconnects listeners, observer and timer before a new mount initializes", async () => {
    runInlineWatchdog();
    document.dispatchEvent(new Event("astro:before-swap"));
    expect(vi.getTimerCount()).toBe(0);
    fail();
    hydrate();
    await vi.advanceTimersByTimeAsync(RETRY_DELAY_MS);
    expect(element("shell").hidden).toBe(false);
    expect(element("fallback").hidden).toBe(true);
    runInlineWatchdog();
    hydrate();
    expectReady();
  });
});
