import { createHash } from 'node:crypto';
import { gzipSync } from 'node:zlib';
import { afterEach, describe, expect, test, vi } from 'vitest';
import {
  assertAllowedDownloadUrl,
  assertNotClobberingRicherLocal,
  assertPointerFresh,
  downloadGzip,
  downloadUrl,
} from '../../scripts/hydrate-manifest.mjs';

const ASSET_URL =
  'https://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/download/atlas-manifest/lexicon-manifest.json.gz';
const VERSIONED_ASSET_URL =
  'https://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/download/atlas-manifest/lexicon-manifest-0123456789ab.json.gz';

function sha256(data: Buffer): string {
  return createHash('sha256').update(data).digest('hex');
}

function pointerFor(gzBytes: Buffer, assetUrl = ASSET_URL) {
  return {
    asset_url: assetUrl,
    gz_sha256: sha256(gzBytes),
  };
}

function okResponse(gzBytes: Buffer) {
  return {
    ok: true,
    arrayBuffer: async () =>
      gzBytes.buffer.slice(gzBytes.byteOffset, gzBytes.byteOffset + gzBytes.byteLength),
  };
}

describe('hydrate manifest release download', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  test('adds deterministic cache-busting query parameters after first attempt', () => {
    const gzBytes = gzipSync(Buffer.from('{"entries":[]}'));
    const pointer = pointerFor(gzBytes);

    expect(downloadUrl(pointer, 0)).toBe(ASSET_URL);
    expect(downloadUrl(pointer, 1)).toBe(
      `${ASSET_URL}?atlas_manifest_sha256=${sha256(gzBytes)}&atlas_manifest_attempt=1`,
    );
  });

  test('preserves the versioned filename when adding cache-busting query parameters', () => {
    const gzBytes = gzipSync(Buffer.from('{"entries":[]}'));
    const pointer = pointerFor(gzBytes, VERSIONED_ASSET_URL);

    expect(downloadUrl(pointer, 0)).toBe(VERSIONED_ASSET_URL);
    expect(downloadUrl(pointer, 1)).toBe(
      `${VERSIONED_ASSET_URL}?atlas_manifest_sha256=${sha256(gzBytes)}&atlas_manifest_attempt=1`,
    );
  });

  test('retries stale gzip responses with cache-busting URL', async () => {
    const gzBytes = gzipSync(Buffer.from('{"entries":[{"lemma":"новий"}]}'));
    const staleGzBytes = gzipSync(Buffer.from('{"entries":[{"lemma":"старий"}]}'));
    const pointer = pointerFor(gzBytes);
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okResponse(staleGzBytes))
      .mockResolvedValueOnce(okResponse(gzBytes));
    vi.stubGlobal('fetch', fetchMock);

    await expect(downloadGzip(pointer)).resolves.toEqual(gzBytes);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      expect.stringContaining('atlas_manifest_sha256='),
      expect.objectContaining({ cache: 'no-store' }),
    );
  });

  test('retries transient fetch failures with cache-busting URL', async () => {
    const gzBytes = gzipSync(Buffer.from('{"entries":[{"lemma":"мережа"}]}'));
    const pointer = pointerFor(gzBytes);
    const fetchMock = vi
      .fn()
      .mockRejectedValueOnce(new Error('temporary edge failure'))
      .mockResolvedValueOnce(okResponse(gzBytes));
    vi.stubGlobal('fetch', fetchMock);

    await expect(downloadGzip(pointer)).resolves.toEqual(gzBytes);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      expect.stringContaining('atlas_manifest_attempt=1'),
      expect.objectContaining({ cache: 'no-store' }),
    );
  });

  test('reports final fetch failure after prior stale gzip response', async () => {
    const gzBytes = gzipSync(Buffer.from('{"entries":[{"lemma":"збій"}]}'));
    const staleGzBytes = gzipSync(Buffer.from('{"entries":[{"lemma":"старий"}]}'));
    const pointer = pointerFor(gzBytes);
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okResponse(staleGzBytes))
      .mockRejectedValueOnce(new Error('temporary edge failure'))
      .mockRejectedValueOnce(new Error('late edge failure'));
    vi.stubGlobal('fetch', fetchMock);

    await expect(downloadGzip(pointer)).rejects.toThrow(
      'failed to download Atlas manifest release asset after 3 attempts: late edge failure',
    );
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  test('explains that re-downloading cannot fix a stale pointer after repeated sha mismatch', async () => {
    const gzBytes = gzipSync(Buffer.from('{"entries":[{"lemma":"новий"}]}'));
    const staleGzBytes = gzipSync(Buffer.from('{"entries":[{"lemma":"старий"}]}'));
    const pointer = pointerFor(gzBytes);
    const fetchMock = vi.fn().mockResolvedValue(okResponse(staleGzBytes));
    vi.stubGlobal('fetch', fetchMock);

    await expect(downloadGzip(pointer)).rejects.toThrow('Re-downloading cannot fix a stale pointer.');
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });
});

describe('asset_url host allowlist', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  test('accepts github.com release-asset URLs unchanged', () => {
    expect(assertAllowedDownloadUrl(ASSET_URL)).toBe(ASSET_URL);
  });

  test('accepts versioned github.com release-asset URLs unchanged', () => {
    expect(assertAllowedDownloadUrl(VERSIONED_ASSET_URL)).toBe(VERSIONED_ASSET_URL);
  });

  test('accepts *.githubusercontent.com redirect targets', () => {
    const url = 'https://objects.githubusercontent.com/github-production-release-asset/x.gz';
    expect(assertAllowedDownloadUrl(url)).toBe(url);
  });

  test.each([
    [`http://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/download/t/f.gz`, 'non-https scheme'],
    ['https://evil.test/lexicon-manifest.json.gz', 'off-allowlist host'],
    ['https://github.com.evil.test/file.gz', 'look-alike host'],
    ['https://github.com@evil.test/learn-ukrainian/learn-ukrainian.github.io/releases/download/t/f.gz', 'userinfo spoof'],
    ['https://fake-githubusercontent.com/x.gz', 'hyphen-spoof CDN host'],
    ['https://github.com/attacker/repo/releases/download/t/evil.gz', 'github.com but wrong repo'],
    ['https://github.com./learn-ukrainian/learn-ukrainian.github.io/releases/download/t/f.gz', 'trailing-dot host'],
    ['not a url', 'malformed url'],
  ])('rejects %s (%s)', (badUrl) => {
    expect(() => assertAllowedDownloadUrl(badUrl)).toThrow();
  });

  test('downloadGzip refuses to fetch a non-allowlisted asset_url', async () => {
    const gzBytes = gzipSync(Buffer.from('{"entries":[]}'));
    const pointer = {
      asset_url: 'https://github.com/attacker/repo/releases/download/t/manifest.gz',
      gz_sha256: sha256(gzBytes),
    };
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    await expect(downloadGzip(pointer)).rejects.toThrow('allowlisted');
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

describe('pointer freshness checks', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  test('warns instead of aborting when the code fingerprint is newer than the pointer', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const pointer = {
      asset_url: ASSET_URL,
      release_tag: 'atlas-manifest',
      manifest_version: '0.1',
      manifest_fingerprint: 'old-fingerprint',
      fingerprint_schema_version: 1,
      gz_sha256: '0'.repeat(64),
      json_sha256: '1'.repeat(64),
      gz_bytes: 1,
      json_bytes: 2,
    };
    const fingerprint = {
      schema_version: 1,
      fingerprint: 'new-fingerprint',
    };

    expect(() => assertPointerFresh(pointer, fingerprint)).not.toThrow();
    expect(warn).toHaveBeenCalledWith(
      'Atlas manifest pointer fingerprint old-fingerprint is stale; expected new-fingerprint. Run make atlas-publish.',
    );
  });
});

describe('local-work guard (#4917: hydrate must not clobber richer local manifest)', () => {
  const { mkdtempSync, writeFileSync, rmSync } = require('node:fs');
  const { tmpdir } = require('node:os');
  const { join } = require('node:path');

  let dir: string;
  afterEach(() => {
    delete process.env.ATLAS_MANIFEST_FORCE_HYDRATE;
    if (dir) rmSync(dir, { recursive: true, force: true });
  });

  function writeLocal(entries: number): string {
    dir = mkdtempSync(join(tmpdir(), 'hydrate-guard-'));
    const p = join(dir, 'lexicon-manifest.json');
    writeFileSync(p, JSON.stringify({ entries: Array.from({ length: entries }, (_, i) => ({ lemma: `w${i}` })) }));
    return p;
  }

  test('refuses when local has MORE entries than the download', async () => {
    const p = writeLocal(5);
    await expect(assertNotClobberingRicherLocal(3, p)).rejects.toThrow(/refusing to overwrite local manifest with 5 entries/);
  });

  test('proceeds when download is richer or equal', async () => {
    const p = writeLocal(3);
    await expect(assertNotClobberingRicherLocal(3, p)).resolves.toBeUndefined();
    await expect(assertNotClobberingRicherLocal(10, p)).resolves.toBeUndefined();
  });

  test('ATLAS_MANIFEST_FORCE_HYDRATE=1 overrides the refusal (explicit restore)', async () => {
    const p = writeLocal(5);
    process.env.ATLAS_MANIFEST_FORCE_HYDRATE = '1';
    await expect(assertNotClobberingRicherLocal(3, p)).resolves.toBeUndefined();
  });

  test('missing or corrupt local file never blocks', async () => {
    await expect(assertNotClobberingRicherLocal(3, '/nonexistent/path.json')).resolves.toBeUndefined();
    dir = mkdtempSync(join(tmpdir(), 'hydrate-guard-'));
    const bad = join(dir, 'corrupt.json');
    writeFileSync(bad, '{not json');
    await expect(assertNotClobberingRicherLocal(3, bad)).resolves.toBeUndefined();
  });
});
