// @vitest-environment node

/**
 * Contract for the Frontend CI build record (#9718): the reused build must be
 * the exact fresh, successful build of the current inputs, or verification
 * fails. Every fixture lives in its own temp repository.
 */

import { execFileSync, spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, unlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { afterEach, describe, expect, it } from 'vitest';
import {
  BuildRecordError,
  NONCE_FILE,
  RECORD_SCHEMA,
  computeInputIdentity,
  defaultLogPath,
  main,
  recordBuild,
  verifyBuildRecord,
  type BuildRoots,
} from '../helpers/ci-build-artifact';

const HELPER = resolve(__dirname, '../helpers/ci-build-artifact.ts');
const fixtures: string[] = [];

const GIT_ENV = Object.fromEntries(
  Object.entries(process.env).filter(([key]) => !key.startsWith('GIT_')),
);

function git(repoRoot: string, ...args: string[]): void {
  execFileSync(
    'git',
    ['-c', 'user.name=fixture', '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false', ...args],
    { cwd: repoRoot, env: GIT_ENV, stdio: 'ignore' },
  );
}

function makeFixture(): BuildRoots & { recordPath: string } {
  const repoRoot = mkdtempSync(join(tmpdir(), 'frontend-build-record-'));
  fixtures.push(repoRoot);
  const siteDir = join(repoRoot, 'site');
  mkdirSync(join(siteDir, 'src/data'), { recursive: true });
  mkdirSync(join(siteDir, 'public/lexicon'), { recursive: true });
  mkdirSync(join(repoRoot, 'data'));
  writeFileSync(join(siteDir, 'src/data/lexicon-teacher-lesson-keys.json'), '{"keys":[]}\n');
  writeFileSync(join(siteDir, 'src/index.astro'), '<h1>fixture</h1>\n');
  writeFileSync(join(siteDir, 'public/lexicon/practice-index.A1.json'), '{"counts":{}}\n');
  writeFileSync(join(repoRoot, 'data/atlas.db'), 'sqlite fixture\n');
  writeFileSync(join(repoRoot, '.gitignore'), 'data/atlas.db\nsite/dist/\nrecords/\n');
  git(repoRoot, 'init', '-q');
  git(repoRoot, 'add', '.');
  git(repoRoot, 'commit', '-q', '-m', 'fixture');
  return { repoRoot, siteDir, recordPath: join(repoRoot, 'records', 'build.json') };
}

/** A stand-in build: writes dist/ (cwd is site/), prints to both streams, then runs `tail`. */
function fakeBuild(tail = ''): string[] {
  return [
    process.execPath,
    '-e',
    "const fs = require('fs'); fs.mkdirSync('dist', { recursive: true });" +
      "fs.writeFileSync('dist/index.html', '<h1>ok</h1>');" +
      "process.stdout.write('built 1 page\\n'); process.stderr.write('[WARN] fixture\\n');" +
      tail,
  ];
}

async function recordFixture(fixture: ReturnType<typeof makeFixture>, command = fakeBuild()) {
  return recordBuild({ recordPath: fixture.recordPath, command, roots: fixture, echo: false });
}

function expectRejected(fixture: ReturnType<typeof makeFixture>, message: RegExp): void {
  expect(() => verifyBuildRecord(fixture.recordPath, fixture)).toThrow(BuildRecordError);
  expect(() => verifyBuildRecord(fixture.recordPath, fixture)).toThrow(message);
}

afterEach(() => {
  for (const dir of fixtures.splice(0)) rmSync(dir, { recursive: true, force: true });
});

describe('frontend CI build record', () => {
  it('records one successful build and verifies its exact log, exit code and dist nonce', async () => {
    const fixture = makeFixture();
    const record = await recordFixture(fixture);

    expect(record.schema).toBe(RECORD_SCHEMA);
    expect(record.exitCode).toBe(0);
    expect(record.nonce).toMatch(/^[0-9a-f-]{36}$/);
    expect(readFileSync(join(fixture.siteDir, 'dist', NONCE_FILE), 'utf-8')).toBe(record.nonce);
    expect(record.inputs).toEqual(computeInputIdentity(fixture));
    expect(Object.keys(record.inputs.files)).toEqual([
      'site/src/data/lexicon-teacher-lesson-keys.json',
      'site/public/lexicon/practice-index.A1.json',
      'data/atlas.db',
    ]);
    expect(record.buildEnv.env).toHaveProperty('ATLAS_MANIFEST_ALLOW_STALE_POINTER');

    const verified = verifyBuildRecord(fixture.recordPath, fixture);
    expect(verified.log).toBe('built 1 page\n[WARN] fixture\n');
    expect(verified.log).toBe(readFileSync(defaultLogPath(fixture.recordPath), 'utf-8'));
    expect(verified.record.exitCode).toBe(0);
  });

  it('passes a rendering-error log from an exit-0 build through byte for byte', async () => {
    // build-renders.test.ts asserts on this text unchanged, so the error stays red there.
    const fixture = makeFixture();
    await recordFixture(fixture, fakeBuild("process.stdout.write('Caught error rendering /a1/x/\\n');"));
    const { log } = verifyBuildRecord(fixture.recordPath, fixture);
    expect(log).toContain('Caught error rendering /a1/x/');
  });

  it('rejects a missing or empty record path', () => {
    const fixture = makeFixture();
    expectRejected(fixture, /missing build record/);
    expect(() => verifyBuildRecord('', fixture)).toThrow(/missing build record: \(empty path\)/);
  });

  it('rejects a malformed record', async () => {
    const fixture = makeFixture();
    await recordFixture(fixture);
    writeFileSync(fixture.recordPath, '{"schema":');
    expectRejected(fixture, /unreadable build record/);
    writeFileSync(fixture.recordPath, '{"schema":"other"}');
    expectRejected(fixture, /unknown build record schema/);
  });

  it('rejects a record from another checkout', async () => {
    const fixture = makeFixture();
    await recordFixture(fixture);
    const other = makeFixture();
    expect(() => verifyBuildRecord(fixture.recordPath, other)).toThrow(/belongs to/);
  });

  it('rejects a missing build log', async () => {
    const fixture = makeFixture();
    await recordFixture(fixture);
    unlinkSync(defaultLogPath(fixture.recordPath));
    expectRejected(fixture, /missing build log/);
  });

  it('rejects a build log that differs from the recorded one', async () => {
    const fixture = makeFixture();
    await recordFixture(fixture);
    writeFileSync(defaultLogPath(fixture.recordPath), 'built 1 page\n');
    expectRejected(fixture, /build log does not match/);
  });

  it('rejects missing dist output', async () => {
    const fixture = makeFixture();
    await recordFixture(fixture);
    rmSync(join(fixture.siteDir, 'dist'), { recursive: true });
    expectRejected(fixture, /missing build output/);
  });

  it('rejects dist output that is not the recorded build', async () => {
    const fixture = makeFixture();
    await recordFixture(fixture);
    writeFileSync(join(fixture.siteDir, 'dist', NONCE_FILE), 'another build');
    expectRejected(fixture, /nonce mismatch/);
    unlinkSync(join(fixture.siteDir, 'dist', NONCE_FILE));
    expectRejected(fixture, /nonce mismatch/);
  });

  it('records a nonzero build exit and refuses to verify it', async () => {
    const fixture = makeFixture();
    const record = await recordFixture(fixture, fakeBuild('process.exit(3);'));
    expect(record.exitCode).toBe(3);
    expect(record.nonce).toBeNull();
    expectRejected(fixture, /recorded build failed: exit 3/);
  });

  it('records a signal-killed build as failed', async () => {
    const fixture = makeFixture();
    const record = await recordFixture(fixture, fakeBuild("process.kill(process.pid, 'SIGTERM');"));
    expect(record.exitCode).toBeNull();
    expect(record.signal).toBe('SIGTERM');
    expectRejected(fixture, /recorded build failed: exit null, signal SIGTERM/);
  });

  it('rejects a changed hydrated source input', async () => {
    const fixture = makeFixture();
    await recordFixture(fixture);
    writeFileSync(join(fixture.siteDir, 'src/data/lexicon-teacher-lesson-keys.json'), '{"keys":[1]}\n');
    expectRejected(fixture, /changed site\/src\/data\/lexicon-teacher-lesson-keys\.json/);
  });

  it('rejects added and removed generated public outputs', async () => {
    const fixture = makeFixture();
    await recordFixture(fixture);
    writeFileSync(join(fixture.siteDir, 'public/lexicon/practice-index.A2.json'), '{}\n');
    expectRejected(fixture, /added site\/public\/lexicon\/practice-index\.A2\.json/);
    unlinkSync(join(fixture.siteDir, 'public/lexicon/practice-index.A2.json'));
    unlinkSync(join(fixture.siteDir, 'public/lexicon/practice-index.A1.json'));
    expectRejected(fixture, /removed site\/public\/lexicon\/practice-index\.A1\.json/);
  });

  it('rejects a changed atlas database', async () => {
    const fixture = makeFixture();
    await recordFixture(fixture);
    writeFileSync(join(fixture.repoRoot, 'data/atlas.db'), 'sqlite fixture v2\n');
    expectRejected(fixture, /changed data\/atlas\.db/);
  });

  it('rejects a new HEAD commit', async () => {
    const fixture = makeFixture();
    await recordFixture(fixture);
    git(fixture.repoRoot, 'commit', '-q', '--allow-empty', '-m', 'next');
    expectRejected(fixture, /HEAD [0-9a-f]{40} -> [0-9a-f]{40}/);
  });

  it('rejects a changed tracked source file outside the data inputs', async () => {
    const fixture = makeFixture();
    await recordFixture(fixture);
    writeFileSync(join(fixture.siteDir, 'src/index.astro'), '<h1>changed</h1>\n');
    expectRejected(fixture, /tracked working-tree diff changed/);
  });

  it('rejects a build that mutates its own inputs', async () => {
    const fixture = makeFixture();
    await recordFixture(fixture, fakeBuild("fs.writeFileSync('public/lexicon/practice-index.A1.json', '{}');"));
    expectRejected(fixture, /changed site\/public\/lexicon\/practice-index\.A1\.json/);
  });

  it('refuses to record when a build input is missing', async () => {
    const fixture = makeFixture();
    unlinkSync(join(fixture.repoRoot, 'data/atlas.db'));
    await expect(recordFixture(fixture)).rejects.toThrow(/missing build input: data\/atlas\.db/);
  });

  it('CLI entry point fails closed on bad usage and a missing record', () => {
    const fixture = makeFixture();
    const run = (...args: string[]) =>
      spawnSync(process.execPath, ['--experimental-strip-types', HELPER, ...args], {
        cwd: fixture.siteDir,
        encoding: 'utf-8',
      });

    for (const args of [['verify'], ['verify', '--record', fixture.recordPath, '--', 'x'], ['other', '--record', 'x']]) {
      const usage = run(...args);
      expect(usage.status, args.join(' ')).toBe(1);
      expect(usage.stderr).toContain('usage:');
    }

    const missing = run('verify', '--record', fixture.recordPath);
    expect(missing.status).toBe(1);
    expect(missing.stderr).toContain('missing build record');

    for (const args of [['verify', '--record', ''], ['record', '--record', '', '--', process.execPath, '-e', '0']]) {
      const empty = run(...args);
      expect(empty.status, args.join(' ')).toBe(1);
      expect(empty.stderr).toContain('missing build record: (empty path)');
    }
    expect(readdirSync(fixture.siteDir)).not.toContain('dist');
  });

  it('main returns the build status, and 0 only for a verifiable build', async () => {
    const fixture = makeFixture();
    const record = ['record', '--record', fixture.recordPath, '--'];
    const verify = ['verify', '--record', fixture.recordPath];

    expect(await main([...record, process.execPath, '-e', 'process.exit(4)'], fixture)).toBe(4);
    expect(JSON.parse(readFileSync(fixture.recordPath, 'utf-8')).exitCode).toBe(4);
    expect(await main(verify, fixture)).toBe(1);

    expect(await main([...record, process.execPath, '-e', '0'], fixture)).toBe(1);
    expect(await main(verify, fixture)).toBe(1);

    expect(await main([...record, ...fakeBuild()], fixture)).toBe(0);
    expect(await main(verify, fixture)).toBe(0);
  });
});
