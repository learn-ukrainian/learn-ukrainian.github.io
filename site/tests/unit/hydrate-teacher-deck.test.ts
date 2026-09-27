import { createHash } from 'node:crypto';
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { gzipSync } from 'node:zlib';
import { afterEach, describe, expect, test, vi } from 'vitest';
import { randomBytes } from 'node:crypto';
import {
  hydrateTeacherDeck,
  parseTeacherPackage,
  validatePointer,
  verifyTeacherDeckPointer,
} from '../../scripts/hydrate-teacher-deck.mjs';

const ASSET_URL =
  'https://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/download/atlas-teacher-deck/lexicon-teacher-deck-teacher-v1-test.json.gz';
const dirs: string[] = [];

function sha256(data: Buffer | string): string {
  return createHash('sha256').update(data).digest('hex');
}

function tempDir(): string {
  const dir = mkdtempSync(join(tmpdir(), 'teacher-deck-'));
  dirs.push(dir);
  return dir;
}

function fixture(options: { dropCloze?: boolean; deckSchemaVersion?: number; clozePadding?: string } = {}) {
  const deck = `${JSON.stringify({
    schema: 'atlas-practice-teacher-deck',
    schemaVersion: options.deckSchemaVersion ?? 1,
    deckVersion: 'teacher-v1-test',
    clozeFile: 'practice-cloze.teacher.json',
    entries: [],
  })}\n`;
  const cloze = `${JSON.stringify({
    schema: 'atlas-practice-teacher-cloze',
    schemaVersion: 1,
    deckVersion: 'teacher-v1-test',
    cloze: [],
    ...(options.clozePadding ? { padding: options.clozePadding } : {}),
  })}\n`;
  const served = { 'practice-deck.teacher.json': deck, 'practice-cloze.teacher.json': cloze };
  const packaged = Object.entries(served)
    .filter(([path]) => !(options.dropCloze && path === 'practice-cloze.teacher.json'))
    .map(([path, content]) => ({ path, content }));
  const packageBytes = Buffer.from(
    JSON.stringify({
      schema: 'atlas-practice-teacher-package',
      schemaVersion: 1,
      deckVersion: 'teacher-v1-test',
      files: packaged,
    }),
    'utf8',
  );
  const gzBytes = gzipSync(packageBytes);
  const pointer = {
    asset_url: ASSET_URL,
    deck_version: 'teacher-v1-test',
    package_schema_version: 1,
    gz_sha256: sha256(gzBytes),
    package_sha256: sha256(packageBytes),
    gz_bytes: gzBytes.length,
    package_bytes: packageBytes.length,
    files: Object.entries(served).map(([path, content]) => ({
      path,
      schema: JSON.parse(content).schema,
      schemaVersion: 1,
      published: true,
      bytes: Buffer.byteLength(content),
      gzipBytes: gzipSync(Buffer.from(content), { level: 9 }).length,
      sha256: sha256(content),
    })),
  };
  return { pointer, packageBytes, gzBytes };
}

type Pointer = ReturnType<typeof fixture>['pointer'];

function record(pointer: Pointer, path: string) {
  const found = pointer.files.find((file) => file.path === path);
  if (!found) throw new Error(`fixture lacks ${path}`);
  return found;
}

function writePointer(pointer: unknown): string {
  const pointerPath = join(tempDir(), 'pointer.json');
  writeFileSync(pointerPath, JSON.stringify(pointer));
  return pointerPath;
}

function stubDownload(gzBytes: Buffer) {
  const fetchMock = vi.fn(async () => new Response(new Uint8Array(gzBytes), { status: 200 }));
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllGlobals();
  for (const dir of dirs.splice(0)) rmSync(dir, { recursive: true, force: true });
});

describe('teacher deck build gate (#8843)', () => {
  test('downloads, verifies and serves the pinned teacher deck', async () => {
    const { pointer, gzBytes } = fixture();
    const pointerPath = join(tempDir(), 'pointer.json');
    writeFileSync(pointerPath, JSON.stringify(pointer));
    const targetDir = tempDir();
    const fetchMock = stubDownload(gzBytes);

    await expect(hydrateTeacherDeck({ pointerPath, targetDir })).resolves.toEqual({
      version: 'teacher-v1-test',
      downloaded: true,
      skipped: false,
    });
    expect(JSON.parse(readFileSync(join(targetDir, 'practice-cloze.teacher.json'), 'utf8')).cloze).toEqual([]);
    await expect(hydrateTeacherDeck({ pointerPath, targetDir })).resolves.toMatchObject({ downloaded: false });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  test('fails the build when the teacher cloze artifact is missing', async () => {
    const { pointer, gzBytes } = fixture({ dropCloze: true });
    const pointerPath = join(tempDir(), 'pointer.json');
    writeFileSync(pointerPath, JSON.stringify(pointer));
    const targetDir = tempDir();
    stubDownload(gzBytes);

    await expect(hydrateTeacherDeck({ pointerPath, targetDir })).rejects.toThrow(
      /artifact missing from the package: practice-cloze.teacher.json/,
    );
    expect(existsSync(join(targetDir, 'practice-deck.teacher.json'))).toBe(false);
  });

  test('skips with a log line before the first publish and drops stale served copies', async () => {
    const targetDir = tempDir();
    writeFileSync(join(targetDir, 'practice-deck.teacher.json'), '{"stale":true}');
    const fetchMock = stubDownload(Buffer.alloc(0));
    const log = vi.fn();

    await expect(
      hydrateTeacherDeck({ pointerPath: join(tempDir(), 'none.json'), targetDir, log }),
    ).resolves.toEqual({ version: null, downloaded: false, skipped: true });
    expect(log).toHaveBeenCalledWith(expect.stringMatching(/^teacher deck: skipped — no pointer at .*none\.json/));
    expect(existsSync(join(targetDir, 'practice-deck.teacher.json'))).toBe(false);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  test('fails the build when the pointed asset is not the pinned release asset', async () => {
    const { pointer, gzBytes } = fixture();
    const pointerPath = writePointer({ ...pointer, asset_url: ASSET_URL.replace('teacher-v1-test', 'teacher-v1-other') });
    stubDownload(gzBytes);
    await expect(hydrateTeacherDeck({ pointerPath, targetDir: tempDir() })).rejects.toThrow(/asset_url is not/);
  });

  test('fails the build when a served file exceeds its gzip budget', () => {
    // Incompressible padding: the pointer under-reports the size, the package check measures it.
    const { pointer, packageBytes } = fixture({ clozePadding: randomBytes(700_000).toString('base64') });
    record(pointer, 'practice-cloze.teacher.json').gzipBytes = 1;
    expect(() => parseTeacherPackage(packageBytes, pointer)).toThrow(/over its 560000 B budget/);
  });

  test('rejects a schema version the page does not understand', () => {
    const { pointer, packageBytes } = fixture({ deckSchemaVersion: 2 });
    expect(() => parseTeacherPackage(packageBytes, pointer)).toThrow(/schema/);
  });

  test('rejects a served file whose hash differs from the pointer', () => {
    const { pointer, packageBytes } = fixture();
    record(pointer, 'practice-deck.teacher.json').sha256 = '0'.repeat(64);
    expect(() => parseTeacherPackage(packageBytes, pointer)).toThrow(/does not match its pointer hash/);
  });

  test('rejects a package that does not match its pointer', () => {
    const { pointer, packageBytes } = fixture();
    expect(() => parseTeacherPackage(Buffer.concat([packageBytes, Buffer.from(' ')]), pointer)).toThrow(
      /does not match its pointer/,
    );
  });
});

describe('teacher deck committed-artifact check (#8843)', () => {
  test('skips with a log line while no pointer is committed', () => {
    const log = vi.fn();
    expect(verifyTeacherDeckPointer({ pointerPath: join(tempDir(), 'none.json'), log })).toEqual({ skipped: true });
    expect(log).toHaveBeenCalledWith(expect.stringMatching(/^teacher deck: skipped — no pointer at /));
  });

  test('accepts a well-formed pointer', () => {
    const { pointer } = fixture();
    expect(verifyTeacherDeckPointer({ pointerPath: writePointer(pointer), log: vi.fn() })).toEqual({
      skipped: false,
      version: 'teacher-v1-test',
    });
  });

  test.each([
    ['asset', (p: Pointer) => ({ ...p, asset_url: 'https://example.com/deck.json.gz' }), /asset_url is not/],
    ['package hash', (p: Pointer) => ({ ...p, gz_sha256: 'not-a-hash' }), /SHA-256 hex digests/],
    [
      'file hash',
      (p: Pointer) => {
        record(p, 'practice-deck.teacher.json').sha256 = 'x';
        return p;
      },
      /lacks a SHA-256/,
    ],
    [
      'schema',
      (p: Pointer) => {
        record(p, 'practice-deck.teacher.json').schemaVersion = 2;
        return p;
      },
      /unexpected schema or schema version/,
    ],
    [
      'cloze file',
      (p: Pointer) => ({ ...p, files: p.files.filter((file) => file.path !== 'practice-cloze.teacher.json') }),
      /does not publish practice-cloze.teacher.json/,
    ],
    [
      'gzip budget',
      (p: Pointer) => {
        record(p, 'practice-cloze.teacher.json').gzipBytes = 560_001;
        return p;
      },
      /over its 560000 B budget/,
    ],
  ])('fails closed on a wrong %s', (_label, mutate, message) => {
    const pointerPath = writePointer(mutate(fixture().pointer));
    expect(() => verifyTeacherDeckPointer({ pointerPath, log: vi.fn() })).toThrow(message);
    expect(() => validatePointer(mutate(fixture().pointer))).toThrow(message);
  });
});
