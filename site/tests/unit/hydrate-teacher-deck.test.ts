import { createHash } from 'node:crypto';
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { gzipSync } from 'node:zlib';
import { afterEach, describe, expect, test, vi } from 'vitest';
import { hydrateTeacherDeck, parseTeacherPackage } from '../../scripts/hydrate-teacher-deck.mjs';

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

function fixture(options: { dropCloze?: boolean; deckSchemaVersion?: number } = {}) {
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
      sha256: sha256(content),
    })),
  };
  return { pointer, packageBytes, gzBytes };
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

  test('fails the build when the pointer is missing', async () => {
    await expect(hydrateTeacherDeck({ pointerPath: join(tempDir(), 'none.json'), targetDir: tempDir() })).rejects.toThrow(
      /pointer missing/,
    );
  });

  test('rejects a schema version the page does not understand', () => {
    const { pointer, packageBytes } = fixture({ deckSchemaVersion: 2 });
    expect(() => parseTeacherPackage(packageBytes, pointer)).toThrow(/schema/);
  });

  test('rejects a package that does not match its pointer', () => {
    const { pointer, packageBytes } = fixture();
    expect(() => parseTeacherPackage(Buffer.concat([packageBytes, Buffer.from(' ')]), pointer)).toThrow(
      /does not match its pointer/,
    );
  });
});
