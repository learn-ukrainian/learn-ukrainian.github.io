import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, test, vi } from 'vitest';
import {
  fnv1a32,
  vesumFormKey,
  vesumShardId,
  VESUM_FORM_SHARD_COUNT,
} from '@site/src/lib/lexicon/vesum-form-key';
import { VesumFormShardClient, VESUM_FORM_SHARD_BASE_URL } from '@site/src/lib/lexicon/vesum-form-shard';

const vectorsPath = resolve(process.cwd(), '../scripts/lexicon/vesum_form_key_vectors.json');

describe('vesumFormKey — parity with scripts/lexicon/vesum_form_key.py', () => {
  test('TypeScript vesumFormKey matches the shared golden vectors', () => {
    const payload = JSON.parse(readFileSync(vectorsPath, 'utf-8')) as {
      cases: Array<{ input: string; expected: string }>;
    };
    for (const testCase of payload.cases) {
      expect(vesumFormKey(testCase.input), testCase.input).toBe(testCase.expected);
    }
  });

  test('canonicalizes apostrophe variants to the VESUM modifier-letter apostrophe', () => {
    expect(vesumFormKey("п'ять")).toBe(vesumFormKey('п’ять'));
    expect(vesumFormKey('пʻять')).toBe(vesumFormKey('пʼять'));
  });

  test('preserves ґ and strips combining acute stress, matching normalizeAtlasText', () => {
    expect(vesumFormKey('Ґанок')).toBe('ґанок');
    expect(vesumFormKey('абре́віатура')).toBe('абревіатура');
  });
});

describe('fnv1a32 / vesumShardId — cross-checked against the Python generator', () => {
  // Cross-checked against scripts/lexicon/vesum_form_key.py::fnv1a32 /
  // vesum_shard_id for the SAME normalized keys. If either implementation
  // drifts, the client fetches the wrong shard and every lookup silently
  // misses — this is the load-bearing parity guard for shard selection.
  const cases: Array<{ word: string; key: string; hash: number; shard4096: string; shard16: string }> = [
    { word: 'привіт', key: 'привіт', hash: 839842187, shard4096: '98b', shard16: '00b' },
    { word: 'книжка', key: 'книжка', hash: 315621804, shard4096: '1ac', shard16: '00c' },
    { word: "п'ять", key: 'пʼять', hash: 3130142632, shard4096: 'fa8', shard16: '008' },
    { word: 'Ґанок', key: 'ґанок', hash: 4154897671, shard4096: '507', shard16: '007' },
  ];

  test('fnv1a32 matches the Python-computed hash for each normalized key', () => {
    for (const c of cases) {
      expect(fnv1a32(vesumFormKey(c.word)), c.word).toBe(c.hash);
    }
  });

  test('vesumShardId matches the Python-computed shard id at shardCount=4096 (default)', () => {
    for (const c of cases) {
      expect(vesumShardId(vesumFormKey(c.word)), c.word).toBe(c.shard4096);
    }
  });

  test('vesumShardId matches the Python-computed shard id at a smaller shardCount', () => {
    for (const c of cases) {
      expect(vesumShardId(vesumFormKey(c.word), 16), c.word).toBe(c.shard16);
    }
  });

  test('shard ids are always zero-padded to at least 3 hex digits and within range', () => {
    for (const word of ['слово', 'тест', 'вигаданеслово']) {
      const shardId = vesumShardId(vesumFormKey(word));
      expect(shardId.length).toBeGreaterThanOrEqual(3);
      expect(Number.parseInt(shardId, 16)).toBeGreaterThanOrEqual(0);
      expect(Number.parseInt(shardId, 16)).toBeLessThan(VESUM_FORM_SHARD_COUNT);
    }
  });
});

function jsonResponse(body: unknown, ok = true, status = 200): Response {
  return {
    ok,
    status,
    json: async () => body,
  } as Response;
}

describe('VesumFormShardClient', () => {
  test('resolves a known form to its VESUM lemmas from the correct shard', async () => {
    const key = vesumFormKey('книжки');
    const shardId = vesumShardId(key);
    const fetchImpl = vi.fn(async (url: string) => {
      expect(url).toBe(`${VESUM_FORM_SHARD_BASE_URL}${shardId}.json`);
      return jsonResponse({ [key]: ['книжка'] });
    });
    const client = new VesumFormShardClient(fetchImpl);

    const results = await client.resolve(['книжки']);
    expect(results.get(key)).toEqual({ lemmas: ['книжка'], degraded: false });
    expect(fetchImpl).toHaveBeenCalledTimes(1);
  });

  test('a form absent from its (successfully fetched) shard is a real VESUM miss, not degraded', async () => {
    const key = vesumFormKey('вигаданеслово');
    const fetchImpl = vi.fn(async () => jsonResponse({}));
    const client = new VesumFormShardClient(fetchImpl);

    const results = await client.resolve(['вигаданеслово']);
    expect(results.get(key)).toEqual({ lemmas: [], degraded: false });
  });

  test('a non-ok shard response degrades every form that hashed to it, never throws', async () => {
    const fetchImpl = vi.fn(async () => jsonResponse({}, false, 404));
    const client = new VesumFormShardClient(fetchImpl);

    const results = await client.resolve(['слово', 'тест']);
    for (const result of results.values()) {
      expect(result).toEqual({ lemmas: [], degraded: true });
    }
  });

  test('a network error degrades the lookup instead of rejecting resolve()', async () => {
    const fetchImpl = vi.fn(async () => {
      throw new Error('network down');
    });
    const client = new VesumFormShardClient(fetchImpl);

    await expect(client.resolve(['слово'])).resolves.not.toThrow();
    const result = (await client.resolve(['слово'])).get(vesumFormKey('слово'));
    expect(result?.degraded).toBe(true);
  });

  test('caches a shard across resolve() calls — fetches it only once', async () => {
    const key = vesumFormKey('книжки');
    const shardId = vesumShardId(key);
    let fetchCount = 0;
    const fetchImpl = vi.fn(async () => {
      fetchCount += 1;
      return jsonResponse({ [key]: ['книжка'] });
    });
    const client = new VesumFormShardClient(fetchImpl);

    await client.resolve(['книжки']);
    await client.resolve(['книжки']);
    expect(fetchCount).toBe(1);
    void shardId;
  });

  test('a single batch dedupes words that normalize to the same key', async () => {
    const fetchImpl = vi.fn(async () => jsonResponse({}));
    const client = new VesumFormShardClient(fetchImpl);

    await client.resolve(['Слово', 'слово', '  слово  ']);
    // All three normalize to the same key and the same shard — one fetch.
    expect(fetchImpl).toHaveBeenCalledTimes(1);
  });

  test('a batch spanning multiple shards fetches each shard exactly once, in parallel', async () => {
    const words = ['привіт', 'книжка', "п'ять", 'Ґанок'];
    const requestedUrls: string[] = [];
    const fetchImpl = vi.fn(async (url: string) => {
      requestedUrls.push(url);
      return jsonResponse({});
    });
    const client = new VesumFormShardClient(fetchImpl);

    await client.resolve(words);
    expect(new Set(requestedUrls).size).toBe(requestedUrls.length); // no duplicate shard fetches
  });
});
