import { afterEach, describe, expect, test, vi } from 'vitest';

import {
  CUSTOM_SETS_STORAGE_KEY,
  DEVICE_ID_KEY,
  getDeviceId,
  saveLocalCustomSet,
} from '../../src/lib/lexicon/custom-decks';

const realLocalStorage = globalThis.localStorage;

/** Storage stub that mimics private-browsing / blocked localStorage. */
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
  realLocalStorage.removeItem(DEVICE_ID_KEY);
  realLocalStorage.removeItem(CUSTOM_SETS_STORAGE_KEY);
});

describe('getDeviceId with blocked localStorage (#6767)', () => {
  test('returns the stored id on the happy path', () => {
    realLocalStorage.setItem(DEVICE_ID_KEY, 'dev_existing');
    expect(getDeviceId()).toBe('dev_existing');
  });

  test('does not throw when setItem throws (private browsing / blocked storage)', () => {
    vi.stubGlobal('localStorage', throwingLocalStorage());
    vi.spyOn(console, 'warn').mockImplementation(() => {});

    const id = getDeviceId();
    expect(id).toMatch(/^dev_/);
    // Session-stable fallback: a second blocked call returns the same id.
    expect(getDeviceId()).toBe(id);
    expect(console.warn).toHaveBeenCalled();
  });

  test('does not throw when even getItem throws', () => {
    vi.stubGlobal('localStorage', throwingLocalStorage({ onGet: true }));
    vi.spyOn(console, 'warn').mockImplementation(() => {});

    const id = getDeviceId();
    expect(id).toMatch(/^dev_/);
    expect(getDeviceId()).toBe(id);
  });
});

describe('saveLocalCustomSet with blocked localStorage (#6767)', () => {
  test('creating a custom set does not throw when storage writes fail', () => {
    vi.stubGlobal('localStorage', throwingLocalStorage());
    vi.spyOn(console, 'warn').mockImplementation(() => {});

    let created: ReturnType<typeof saveLocalCustomSet> | undefined;
    expect(() => {
      created = saveLocalCustomSet({ title: 'Blocked deck', lemma_keys: ['мир'] });
    }).not.toThrow();

    expect(created?.device_id).toMatch(/^dev_/);
    expect(created?.title).toBe('Blocked deck');
    expect(created?.revision).toBe(1);
  });
});
