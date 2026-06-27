import { createHash } from 'node:crypto';
import { gzipSync } from 'node:zlib';
import { afterEach, describe, expect, test, vi } from 'vitest';
import { downloadGzip, downloadUrl } from '../../scripts/hydrate-manifest.mjs';

function sha256(data: Buffer): string {
  return createHash('sha256').update(data).digest('hex');
}

function pointerFor(gzBytes: Buffer) {
  return {
    asset_url: 'https://example.test/lexicon-manifest.json.gz',
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

    expect(downloadUrl(pointer, 0)).toBe('https://example.test/lexicon-manifest.json.gz');
    expect(downloadUrl(pointer, 1)).toBe(
      `https://example.test/lexicon-manifest.json.gz?atlas_manifest_sha256=${sha256(
        gzBytes,
      )}&atlas_manifest_attempt=1`,
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
