import { createHash } from 'node:crypto';
import { gzipSync } from 'node:zlib';
import { afterEach, describe, expect, test, vi } from 'vitest';
import {
  assertAllowedDownloadUrl,
  downloadGzip,
  downloadUrl,
} from '../../scripts/hydrate-manifest.mjs';

const ASSET_URL =
  'https://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/download/atlas-manifest/lexicon-manifest.json.gz';

function sha256(data: Buffer): string {
  return createHash('sha256').update(data).digest('hex');
}

function pointerFor(gzBytes: Buffer) {
  return {
    asset_url: ASSET_URL,
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
});

describe('asset_url host allowlist', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  test('accepts github.com release-asset URLs unchanged', () => {
    expect(assertAllowedDownloadUrl(ASSET_URL)).toBe(ASSET_URL);
  });

  test('accepts *.githubusercontent.com redirect targets', () => {
    const url = 'https://objects.githubusercontent.com/github-production-release-asset/x.gz';
    expect(assertAllowedDownloadUrl(url)).toBe(url);
  });

  test.each([
    ['http://github.com/owner/repo/releases/download/tag/file.gz', 'non-https scheme'],
    ['https://evil.test/lexicon-manifest.json.gz', 'off-allowlist host'],
    ['https://github.com.evil.test/file.gz', 'look-alike host'],
    ['not a url', 'malformed url'],
  ])('rejects %s (%s)', (badUrl) => {
    expect(() => assertAllowedDownloadUrl(badUrl)).toThrow();
  });

  test('downloadGzip refuses to fetch an off-allowlist asset_url', async () => {
    const gzBytes = gzipSync(Buffer.from('{"entries":[]}'));
    const pointer = { asset_url: 'https://evil.test/manifest.gz', gz_sha256: sha256(gzBytes) };
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    await expect(downloadGzip(pointer)).rejects.toThrow('not allowlisted');
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
