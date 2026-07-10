import { createHash } from 'node:crypto';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { gzipSync } from 'node:zlib';
import { afterEach, describe, expect, test, vi } from 'vitest';
import {
  assertAllowedDownloadUrl,
  assertNotClobberingRicherLocal,
  downloadGzip,
  downloadUrl,
  parsePackage,
} from '../../scripts/hydrate-practice-deck.mjs';

const ASSET_URL =
  'https://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/download/atlas-practice-deck/lexicon-practice-deck.json.gz';
const VERSIONED_ASSET_URL =
  'https://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/download/atlas-practice-deck/lexicon-practice-deck-atlas-practice-v1-0123456789ab.json.gz';

function sha256(data: Buffer): string {
  return createHash('sha256').update(data).digest('hex');
}

function packageFixture() {
  const content = '{"schema":"atlas-practice-index","schemaVersion":1,"deckVersion":"deck","level":"A1"}\n';
  const fileBytes = Buffer.from(content, 'utf8');
  const packageBytes = Buffer.from(
    JSON.stringify({
      schema: 'atlas-practice-deck-package',
      schemaVersion: 1,
      deckVersion: 'deck',
      files: [{ path: 'practice-index.A1.json', content }],
    }),
    'utf8',
  );
  const gzBytes = gzipSync(packageBytes);
  const pointer = {
    asset_url: ASSET_URL,
    deck_version: 'deck',
    package_schema_version: 1,
    gz_sha256: sha256(gzBytes),
    package_sha256: sha256(packageBytes),
    gz_bytes: gzBytes.length,
    package_bytes: packageBytes.length,
    file_count: 1,
    files: [
      {
        path: 'practice-index.A1.json',
        level: 'A1',
        kind: 'index',
        bytes: fileBytes.length,
        sha256: sha256(fileBytes),
      },
    ],
  };
  return { gzBytes, packageBytes, pointer };
}

function okResponse(gzBytes: Buffer) {
  return {
    ok: true,
    arrayBuffer: async () =>
      gzBytes.buffer.slice(gzBytes.byteOffset, gzBytes.byteOffset + gzBytes.byteLength),
  };
}

describe('hydrate practice deck release download', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  test('adds deterministic cache-busting query parameters after first attempt', () => {
    const { pointer } = packageFixture();

    expect(downloadUrl(pointer, 0)).toBe(ASSET_URL);
    expect(downloadUrl(pointer, 1)).toBe(
      `${ASSET_URL}?atlas_practice_deck_sha256=${pointer.gz_sha256}&atlas_practice_deck_attempt=1`,
    );
  });

  test('preserves the versioned filename when adding cache-busting query parameters', () => {
    const { pointer } = packageFixture();
    const pointerWithVersioned = { ...pointer, asset_url: VERSIONED_ASSET_URL };

    expect(downloadUrl(pointerWithVersioned, 0)).toBe(VERSIONED_ASSET_URL);
    expect(downloadUrl(pointerWithVersioned, 1)).toBe(
      `${VERSIONED_ASSET_URL}?atlas_practice_deck_sha256=${pointer.gz_sha256}&atlas_practice_deck_attempt=1`,
    );
  });

  test('retries stale gzip responses with cache-busting URL', async () => {
    const { gzBytes, pointer } = packageFixture();
    const staleGzBytes = gzipSync(Buffer.from('{"old":true}'));
    const fetchMock = vi.fn().mockResolvedValueOnce(okResponse(staleGzBytes)).mockResolvedValueOnce(okResponse(gzBytes));
    vi.stubGlobal('fetch', fetchMock);

    await expect(downloadGzip(pointer)).resolves.toEqual(gzBytes);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      expect.stringContaining('atlas_practice_deck_attempt=1'),
      expect.objectContaining({ cache: 'no-store' }),
    );
  });

  test('explains that re-downloading cannot fix a stale pointer after repeated sha mismatch', async () => {
    const { pointer } = packageFixture();
    const staleGzBytes = gzipSync(Buffer.from('{"old":true}'));
    const fetchMock = vi.fn().mockResolvedValue(okResponse(staleGzBytes));
    vi.stubGlobal('fetch', fetchMock);

    await expect(downloadGzip(pointer)).rejects.toThrow('Re-downloading cannot fix a stale pointer.');
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  test('verifies package and shard hashes before writing', () => {
    const { packageBytes, pointer } = packageFixture();

    const files = parsePackage(packageBytes, pointer);

    expect(files).toHaveLength(1);
    expect(files[0][0]).toBe('practice-index.A1.json');
    expect(files[0][1].toString('utf8')).toContain('"atlas-practice-index"');
  });

  test('accepts versioned github.com release-asset URLs unchanged', () => {
    expect(assertAllowedDownloadUrl(VERSIONED_ASSET_URL)).toBe(VERSIONED_ASSET_URL);
  });

  test.each([
    ['http://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/download/t/f.gz', 'non-https scheme'],
    ['https://evil.test/lexicon-practice-deck.json.gz', 'off-allowlist host'],
    ['https://github.com.evil.test/file.gz', 'look-alike host'],
    ['https://fake-githubusercontent.com/x.gz', 'hyphen-spoof CDN host'],
    ['https://github.com/attacker/repo/releases/download/t/evil.gz', 'github.com different repo'],
  ])('rejects non-allowlisted asset URL: %s (%s)', (url) => {
    expect(() => assertAllowedDownloadUrl(url)).toThrow(/allowlisted|https/);
  });
});

describe('practice deck local-work guard', () => {
  let dir: string | undefined;

  afterEach(() => {
    vi.unstubAllEnvs();
    if (dir) rmSync(dir, { recursive: true, force: true });
  });

  function richerLocalIndex(lexemes: number): string {
    dir = mkdtempSync(join(tmpdir(), 'practice-deck-guard-'));
    writeFileSync(join(dir, 'practice-index.A1.json'), JSON.stringify({ counts: { lexemes } }));
    return dir;
  }

  function pointerWithIndexCount(lexemes: number) {
    const { pointer } = packageFixture();
    pointer.files[0].counts = { lexemes };
    return pointer;
  }

  test('refuses to overwrite a richer local practice deck', async () => {
    await expect(assertNotClobberingRicherLocal(pointerWithIndexCount(3), richerLocalIndex(5))).rejects.toThrow(
      /local practice deck with 5 lexemes.*published release with only 3/,
    );
  });

  test('force escape hatch permits an intentional practice deck restore', async () => {
    vi.stubEnv('ATLAS_MANIFEST_FORCE_HYDRATE', '1');
    await expect(assertNotClobberingRicherLocal(pointerWithIndexCount(3), richerLocalIndex(5))).resolves.toBeUndefined();
  });
});
