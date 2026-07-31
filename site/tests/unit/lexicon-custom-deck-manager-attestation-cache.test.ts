import { afterEach, describe, expect, test, vi } from 'vitest';
import { loadAttestationIndex } from '@site/src/components/LexiconCustomDeckManager';
import type { AtlasAttestationRow } from '@site/src/lib/lexicon/paste-text-vocab';

const ROWS: AtlasAttestationRow[] = [{ l: 'привіт', s: 'pryvit', g: 'hello', c: 'A1' }];

function mockFetchOk() {
  return vi.fn(async () => ({
    ok: true,
    json: async () => ROWS,
  })) as unknown as typeof fetch;
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe('loadAttestationIndex cache keying (F001)', () => {
  test('fetches independently per distinct shardBaseUrl instead of sharing one global promise', async () => {
    const fetchMock = mockFetchOk();
    vi.stubGlobal('fetch', fetchMock);

    await loadAttestationIndex('/lexicon-cache-test-a');
    await loadAttestationIndex('/lexicon-cache-test-b');

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock).toHaveBeenNthCalledWith(1, '/lexicon-cache-test-a/search-index.json');
    expect(fetchMock).toHaveBeenNthCalledWith(2, '/lexicon-cache-test-b/search-index.json');
  });

  test('reuses the cached promise for the same shardBaseUrl', async () => {
    const fetchMock = mockFetchOk();
    vi.stubGlobal('fetch', fetchMock);

    const [first, second] = await Promise.all([
      loadAttestationIndex('/lexicon-cache-test-c'),
      loadAttestationIndex('/lexicon-cache-test-c'),
    ]);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(first).toBe(second);
  });

  test('normalizes a trailing slash so it hits the same cache entry', async () => {
    const fetchMock = mockFetchOk();
    vi.stubGlobal('fetch', fetchMock);

    await loadAttestationIndex('/lexicon-cache-test-d');
    await loadAttestationIndex('/lexicon-cache-test-d/');

    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  test('a failed fetch for one shardBaseUrl does not evict or block a different shardBaseUrl', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      if (String(input).startsWith('/lexicon-cache-test-fail')) {
        return { ok: false, status: 500, json: async () => [] } as Response;
      }
      return { ok: true, json: async () => ROWS } as unknown as Response;
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(loadAttestationIndex('/lexicon-cache-test-fail')).rejects.toThrow();
    const ok = await loadAttestationIndex('/lexicon-cache-test-ok');

    expect(ok.get('pryvit')).toEqual(ROWS[0]);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  test('a failed fetch clears its own cache entry so a retry re-fetches', async () => {
    const fetchMock = vi.fn(async () => ({ ok: false, status: 500, json: async () => [] }) as Response);
    vi.stubGlobal('fetch', fetchMock);

    await expect(loadAttestationIndex('/lexicon-cache-test-retry')).rejects.toThrow();
    await expect(loadAttestationIndex('/lexicon-cache-test-retry')).rejects.toThrow();

    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
