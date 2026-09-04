/**
 * Practice island watchdog (#7671).
 *
 * `/words-of-the-day/practice/` mounts LexiconPractice with client:only, so an
 * inline is:inline watchdog paints a "couldn't load" fallback if hydration
 * never happens. The island chunk used to be ~5MB, big enough that a slow
 * connection could still be downloading it past the watchdog's original fixed
 * 10s timer — the watchdog must not paint failure while that download is
 * still in flight, only once it has actually stalled or errored.
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

const ROOT = process.cwd();
const TIMEOUT_MS = 10_000;
const HARD_TIMEOUT_MS = 30_000;

const mountSource = readFileSync(
  resolve(ROOT, "src/lexicon/LexiconPracticeMount.astro"),
  "utf8",
);

/** Extract the is:inline watchdog (must stay import-free, same rule as DailyWords). */
function extractInlineWatchdogSource(astroSource: string): string {
  const match = astroSource.match(/<script is:inline>\s*([\s\S]*?)\s*<\/script>/);
  if (!match) {
    throw new Error("LexiconPracticeMount.astro is missing the is:inline watchdog script");
  }
  return match[1]!;
}

const inlineScript = extractInlineWatchdogSource(mountSource);

function mountPracticeIsland(): void {
  document.body.innerHTML = `
    <div id="lexicon-practice-mount" data-lexicon-practice-island>
      <div id="lexicon-practice-shell" role="status" aria-busy="true"></div>
    </div>
    <div id="lexicon-practice-fallback" hidden>
      <p>Не вдалося завантажити практику.</p>
    </div>
  `;
}

function runInlineWatchdog(): void {
  // eslint-disable-next-line no-eval -- intentional: exercise production is:inline source
  (0, eval)(inlineScript);
}

function shellHidden(): boolean {
  return document.getElementById("lexicon-practice-shell")!.hasAttribute("hidden");
}

function fallbackHidden(): boolean {
  return document.getElementById("lexicon-practice-fallback")!.hasAttribute("hidden");
}

/** Simulates the astro-hashed island chunk's Resource Timing entry. */
function mockIslandResourceEntry(entry: { responseEnd: number } | null): void {
  vi.spyOn(performance, "getEntriesByType").mockReturnValue(
    entry
      ? ([{ name: "/_astro/LexiconPractice.CTdQX-4o.js", responseEnd: entry.responseEnd }] as unknown as PerformanceEntryList)
      : [],
  );
}

describe("practice island watchdog (#7671)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mountPracticeIsland();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    document.body.innerHTML = "";
  });

  test("self-contained is:inline watchdog (no module imports)", () => {
    // Matches a real ES import statement, not the word "import" inside a comment
    // (e.g. "... on import/hydrate fail").
    expect(inlineScript).not.toMatch(/^\s*import\s/m);
    expect(inlineScript).toContain("TIMEOUT_MS");
    expect(inlineScript).toContain("HARD_TIMEOUT_MS");
  });

  test("does not paint fallback while the island chunk is still downloading past TIMEOUT_MS", async () => {
    mockIslandResourceEntry({ responseEnd: 0 }); // still transferring
    runInlineWatchdog();

    await vi.advanceTimersByTimeAsync(TIMEOUT_MS + 5_000);
    expect(fallbackHidden()).toBe(true);
    expect(shellHidden()).toBe(false);

    // Still in flight right up to (but not past) the hard cap.
    await vi.advanceTimersByTimeAsync(HARD_TIMEOUT_MS - TIMEOUT_MS - 5_000 - 1);
    expect(fallbackHidden()).toBe(true);
  });

  test("paints fallback at the hard cap even if the chunk never finishes downloading", async () => {
    mockIslandResourceEntry({ responseEnd: 0 }); // still transferring, forever
    runInlineWatchdog();

    await vi.advanceTimersByTimeAsync(HARD_TIMEOUT_MS);
    expect(fallbackHidden()).toBe(false);
    expect(shellHidden()).toBe(true);
  });

  test("paints fallback at TIMEOUT_MS once the download has actually finished without hydrating", async () => {
    mockIslandResourceEntry({ responseEnd: 1234 }); // finished transferring
    runInlineWatchdog();

    await vi.advanceTimersByTimeAsync(TIMEOUT_MS - 1);
    expect(fallbackHidden()).toBe(true);

    await vi.advanceTimersByTimeAsync(1);
    expect(fallbackHidden()).toBe(false);
    expect(shellHidden()).toBe(true);
  });

  test("treats an unobserved resource (no matching entry yet) as in-flight, not failure", async () => {
    mockIslandResourceEntry(null); // no Resource Timing entry at all
    runInlineWatchdog();

    await vi.advanceTimersByTimeAsync(TIMEOUT_MS + 5_000);
    expect(fallbackHidden()).toBe(true);

    await vi.advanceTimersByTimeAsync(HARD_TIMEOUT_MS);
    expect(fallbackHidden()).toBe(false);
  });

  test("hydration success (mutation observer) short-circuits the watchdog regardless of download state", async () => {
    mockIslandResourceEntry({ responseEnd: 0 });
    runInlineWatchdog();

    const mount = document.querySelector("#lexicon-practice-mount")!;
    const success = document.createElement("div");
    success.className = "lexicon-practice";
    mount.appendChild(success);

    await vi.advanceTimersByTimeAsync(TIMEOUT_MS + 5_000);
    expect(shellHidden()).toBe(true);
    expect(fallbackHidden()).toBe(true);
    expect(mount.hasAttribute("hidden")).toBe(false);
  });
});
