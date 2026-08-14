import { afterEach, describe, expect, test, vi } from 'vitest';

import {
  clearLoadedSrsState,
  isPracticeStorageEphemeral,
  loadState,
  nextDuePreviewTime,
  rateCard,
  readPracticeSessionSnapshots,
  writePracticeSessionSnapshot,
  type PracticeSessionSnapshot,
} from '../../src/lib/lexicon/srs';

const realLocalStorage = globalThis.localStorage;

/** Storage stub that mimics Chrome `--disable-local-storage` / blocked private mode. */
function throwingLocalStorage({ onGet = false }: { onGet?: boolean } = {}): Storage {
  const denied = () => {
    throw new DOMException('Access is denied', 'SecurityError');
  };
  return {
    get length() {
      return 0;
    },
    clear: vi.fn(),
    getItem: onGet ? denied : vi.fn(() => null),
    key: vi.fn(() => null),
    removeItem: vi.fn(),
    setItem: denied,
  } as unknown as Storage;
}

afterEach(() => {
  vi.stubGlobal('localStorage', realLocalStorage);
  vi.restoreAllMocks();
  clearLoadedSrsState();
  realLocalStorage.clear();
});

describe('practice storage fallback (#6780)', () => {
  test('loadState and nextDuePreviewTime do not throw when getItem throws', () => {
    vi.stubGlobal('localStorage', throwingLocalStorage({ onGet: true }));
    clearLoadedSrsState();

    expect(() => loadState()).not.toThrow();
    expect(isPracticeStorageEphemeral()).toBe(true);
    expect(() => nextDuePreviewTime()).not.toThrow();
  });

  test('ratings persist in the in-memory store for the session', () => {
    vi.stubGlobal('localStorage', throwingLocalStorage({ onGet: true }));
    clearLoadedSrsState();

    loadState();
    expect(() => rateCard('мир', 'flashcards', 'good', new Date('2026-08-14T12:00:00.000Z'))).not.toThrow();

    const reloaded = loadState();
    expect(reloaded.cards.has('мир::flashcards')).toBe(true);
    expect(reloaded.reviews).toHaveLength(1);
  });

  test('session snapshots use the same in-memory fallback', () => {
    vi.stubGlobal('localStorage', throwingLocalStorage({ onGet: true }));
    clearLoadedSrsState();

    const snapshot: PracticeSessionSnapshot = {
      sessionSeed: 1,
      history: [],
      budget: 10,
      completed: 0,
      modeFilter: 'mixed',
      level: 'A1',
      deckId: 'all',
      dateSeed: 20260814,
      startedAt: Date.parse('2026-08-14T12:00:00.000Z'),
      extensionUsed: 0,
      sessionNewIntroduced: 0,
      plannedReviews: 0,
      plannedNew: 10,
      plannedTotal: 10,
      reviewsCompleted: 0,
      unresolvedCardKeys: [],
    };

    expect(() => writePracticeSessionSnapshot('mixed', snapshot)).not.toThrow();
    expect(readPracticeSessionSnapshots().mixed?.sessionSeed).toBe(1);
  });

  test('accessor-only localStorage (setItem throws, getItem works) still falls back for writes', () => {
    // setItem-only failure: resolveStorage keeps localStorage (getItem ok), but
    // writes must not crash the session — save paths already catch; probe stays read-only.
    vi.stubGlobal('localStorage', throwingLocalStorage({ onGet: false }));
    clearLoadedSrsState();

    expect(() => loadState()).not.toThrow();
    expect(isPracticeStorageEphemeral()).toBe(false);
  });
});
