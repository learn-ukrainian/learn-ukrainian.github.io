/**
 * Current-run Astro build record for the Frontend CI job (#9718).
 *
 * `record` runs the build once, keeps its complete merged stdout/stderr log and
 * exit code, writes a fresh nonce into dist/, and binds all of it to the input
 * identity: HEAD, the tracked working-tree diff and the content of every file
 * under the hydrated inputs (site/src/data, site/public, data/atlas.db).
 * The identity is taken before the build. A file the build itself creates under
 * the inputs (astro.config.mjs writes the fallback
 * public/audio/pronunciation/manifest.json when it is absent, #8378) is added
 * with its post-build content and listed in `buildCreatedInputs`; a build that
 * changes or removes an existing input still fails verification.
 *
 * `verify` fails closed unless the record, its log and dist/ are exactly that
 * build, the build exited 0, and a fresh recomputation of the input identity
 * still matches. There is no fallback to rebuilding.
 *
 * CLI (run from site/ with `node --experimental-strip-types`):
 *   record --record <path> -- <build command...>
 *   verify --record <path>
 */

import { execFileSync, spawn } from 'node:child_process';
import { createHash, randomUUID } from 'node:crypto';
import {
  closeSync,
  createWriteStream,
  existsSync,
  lstatSync,
  mkdirSync,
  openSync,
  readFileSync,
  readSync,
  readdirSync,
  readlinkSync,
  writeFileSync,
} from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

export const RECORD_SCHEMA = 'lu.frontend-build-record.v1';
export const NONCE_FILE = '.frontend-build-nonce';
export const INPUT_PATHS = ['site/src/data', 'site/public', 'data/atlas.db'] as const;
export const BUILD_ENV_KEYS = [
  'ATLAS_MANIFEST_ALLOW_STALE_POINTER',
  'ATLAS_STATIC_ROUTES',
  'CI',
  'NODE_ENV',
  'NODE_OPTIONS',
] as const;

export interface BuildRoots {
  repoRoot: string;
  siteDir: string;
}

const SITE_DIR = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
export const DEFAULT_ROOTS: BuildRoots = { repoRoot: resolve(SITE_DIR, '..'), siteDir: SITE_DIR };

export interface InputIdentity {
  head: string;
  worktreeDiffSha256: string;
  files: Record<string, string>;
}

export interface BuildRecord {
  schema: typeof RECORD_SCHEMA;
  siteDir: string;
  command: string[];
  exitCode: number | null;
  signal: string | null;
  log: { path: string; sha256: string; bytes: number };
  nonce: string | null;
  /** Input files absent before the build and created by it, fingerprinted after it. */
  buildCreatedInputs: string[];
  buildEnv: { node: string; platform: string; arch: string; env: Record<string, string | null> };
  inputs: InputIdentity;
}

export class BuildRecordError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'BuildRecordError';
  }
}

function sha256File(path: string): string {
  const hash = createHash('sha256');
  const buffer = Buffer.allocUnsafe(1 << 20);
  const fd = openSync(path, 'r');
  try {
    let bytesRead: number;
    while ((bytesRead = readSync(fd, buffer, 0, buffer.length, null)) > 0) {
      hash.update(buffer.subarray(0, bytesRead));
    }
  } finally {
    closeSync(fd);
  }
  return hash.digest('hex');
}

function hashTree(repoRoot: string, relPath: string, out: Record<string, string>): void {
  const absolute = join(repoRoot, relPath);
  const stat = lstatSync(absolute);
  if (stat.isSymbolicLink()) {
    out[relPath] = `symlink:${readlinkSync(absolute)}`;
  } else if (stat.isDirectory()) {
    for (const entry of readdirSync(absolute).sort()) hashTree(repoRoot, `${relPath}/${entry}`, out);
  } else if (stat.isFile()) {
    out[relPath] = sha256File(absolute);
  } else {
    throw new BuildRecordError(`unsupported input file type: ${relPath}`);
  }
}

const REDIRECTING_GIT_ENV = new Set(['GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE']);

function git(repoRoot: string, args: string[]): Buffer {
  // A caller's GIT_DIR/GIT_WORK_TREE/GIT_INDEX_FILE would point git away from repoRoot.
  const env = Object.fromEntries(
    Object.entries(process.env).filter(([key]) => !REDIRECTING_GIT_ENV.has(key)),
  );
  return execFileSync('git', args, { cwd: repoRoot, env, maxBuffer: 1 << 30 });
}

export function computeInputIdentity(roots: BuildRoots = DEFAULT_ROOTS): InputIdentity {
  const files: Record<string, string> = {};
  for (const relPath of INPUT_PATHS) {
    if (!existsSync(join(roots.repoRoot, relPath))) {
      throw new BuildRecordError(`missing build input: ${relPath}`);
    }
    hashTree(roots.repoRoot, relPath, files);
  }
  return {
    head: git(roots.repoRoot, ['rev-parse', 'HEAD']).toString('utf-8').trim(),
    worktreeDiffSha256: createHash('sha256')
      .update(git(roots.repoRoot, ['diff', '--binary', '--no-ext-diff', 'HEAD']))
      .digest('hex'),
    files,
  };
}

export function inputIdentityDifferences(recorded: InputIdentity, current: InputIdentity): string[] {
  const differences: string[] = [];
  if (recorded.head !== current.head) differences.push(`HEAD ${recorded.head} -> ${current.head}`);
  if (recorded.worktreeDiffSha256 !== current.worktreeDiffSha256) {
    differences.push('tracked working-tree diff changed');
  }
  const paths = new Set([...Object.keys(recorded.files), ...Object.keys(current.files)]);
  for (const path of [...paths].sort()) {
    if (!(path in current.files)) differences.push(`removed ${path}`);
    else if (!(path in recorded.files)) differences.push(`added ${path}`);
    else if (recorded.files[path] !== current.files[path]) differences.push(`changed ${path}`);
  }
  return differences;
}

export function defaultLogPath(recordPath: string): string {
  return `${recordPath}.log`;
}

export interface RecordOptions {
  recordPath: string;
  command: string[];
  roots?: BuildRoots;
  env?: NodeJS.ProcessEnv;
  /** Also stream build output to this process's stdout/stderr (default true). */
  echo?: boolean;
}

/** Run the build once and write its record. Resolves to the record. */
export async function recordBuild(options: RecordOptions): Promise<BuildRecord> {
  const { recordPath, command } = options;
  const roots = options.roots ?? DEFAULT_ROOTS;
  const env = options.env ?? process.env;
  if (command.length === 0) throw new BuildRecordError('record needs a build command after --');

  const inputs = computeInputIdentity(roots);
  const logPath = defaultLogPath(recordPath);
  mkdirSync(dirname(recordPath), { recursive: true });

  const log = createWriteStream(logPath);
  const hash = createHash('sha256');
  let bytes = 0;
  const { exitCode, signal } = await new Promise<{ exitCode: number | null; signal: string | null }>(
    (resolvePromise, reject) => {
      const child = spawn(command[0], command.slice(1), {
        cwd: roots.siteDir,
        env,
        stdio: ['ignore', 'pipe', 'pipe'],
      });
      const capture = (chunk: Buffer, stream: NodeJS.WriteStream) => {
        hash.update(chunk);
        bytes += chunk.length;
        log.write(chunk);
        if (options.echo !== false) stream.write(chunk);
      };
      child.stdout.on('data', (chunk: Buffer) => capture(chunk, process.stdout));
      child.stderr.on('data', (chunk: Buffer) => capture(chunk, process.stderr));
      child.on('error', reject);
      child.on('close', (code, sig) => resolvePromise({ exitCode: code, signal: sig }));
    },
  );
  await new Promise<void>((resolvePromise, reject) => {
    log.on('error', reject);
    log.end(resolvePromise);
  });

  // Admit only inputs the build created: changed or removed inputs keep their
  // pre-build hashes, so verification reports them.
  const after = computeInputIdentity(roots);
  const buildCreatedInputs = Object.keys(after.files)
    .filter((path) => !(path in inputs.files))
    .sort();
  for (const path of buildCreatedInputs) inputs.files[path] = after.files[path];

  const distDir = join(roots.siteDir, 'dist');
  let nonce: string | null = null;
  if (exitCode === 0 && existsSync(distDir)) {
    nonce = randomUUID();
    writeFileSync(join(distDir, NONCE_FILE), nonce);
  }

  const record: BuildRecord = {
    schema: RECORD_SCHEMA,
    siteDir: roots.siteDir,
    command,
    exitCode,
    signal,
    log: { path: logPath, sha256: hash.digest('hex'), bytes },
    nonce,
    buildCreatedInputs,
    buildEnv: {
      node: process.version,
      platform: process.platform,
      arch: process.arch,
      env: Object.fromEntries(BUILD_ENV_KEYS.map((key) => [key, env[key] ?? null])),
    },
    inputs,
  };
  writeFileSync(recordPath, `${JSON.stringify(record, null, 2)}\n`);
  return record;
}

export interface VerifiedBuild {
  record: BuildRecord;
  log: string;
}

/** Throw BuildRecordError unless the record proves this exact, successful, current build. */
export function verifyBuildRecord(recordPath: string, roots: BuildRoots = DEFAULT_ROOTS): VerifiedBuild {
  if (!recordPath || !existsSync(recordPath)) {
    throw new BuildRecordError(`missing build record: ${recordPath || '(empty path)'}`);
  }
  let record: BuildRecord;
  try {
    record = JSON.parse(readFileSync(recordPath, 'utf-8')) as BuildRecord;
  } catch (error) {
    throw new BuildRecordError(`unreadable build record ${recordPath}: ${(error as Error).message}`);
  }
  if (record?.schema !== RECORD_SCHEMA) {
    throw new BuildRecordError(`unknown build record schema: ${String(record?.schema)}`);
  }
  if (resolve(record.siteDir) !== resolve(roots.siteDir)) {
    throw new BuildRecordError(`build record belongs to ${record.siteDir}, not ${roots.siteDir}`);
  }
  if (record.exitCode !== 0) {
    throw new BuildRecordError(
      `recorded build failed: exit ${String(record.exitCode)}, signal ${String(record.signal)}`,
    );
  }
  if (!existsSync(record.log.path)) throw new BuildRecordError(`missing build log: ${record.log.path}`);
  const logBytes = readFileSync(record.log.path);
  const logSha = createHash('sha256').update(logBytes).digest('hex');
  if (logSha !== record.log.sha256 || logBytes.length !== record.log.bytes) {
    throw new BuildRecordError(`build log does not match the record: ${record.log.path}`);
  }
  const distDir = join(roots.siteDir, 'dist');
  if (!existsSync(distDir)) throw new BuildRecordError(`missing build output: ${distDir}`);
  const noncePath = join(distDir, NONCE_FILE);
  const distNonce = existsSync(noncePath) ? readFileSync(noncePath, 'utf-8') : null;
  if (!record.nonce || distNonce !== record.nonce) {
    throw new BuildRecordError(`${distDir} is not the recorded build (nonce mismatch)`);
  }
  const differences = inputIdentityDifferences(record.inputs, computeInputIdentity(roots));
  if (differences.length > 0) {
    const shown = differences.slice(0, 20).join('\n  ');
    const more = differences.length > 20 ? `\n  ... ${differences.length - 20} more` : '';
    throw new BuildRecordError(`build inputs changed since the recorded build:\n  ${shown}${more}`);
  }
  return { record, log: logBytes.toString('utf-8') };
}

function parseArgs(argv: string[]): { command: string; recordPath: string; buildCommand: string[] } {
  const [command, ...rest] = argv;
  const separator = rest.indexOf('--');
  const options = separator === -1 ? rest : rest.slice(0, separator);
  const buildCommand = separator === -1 ? [] : rest.slice(separator + 1);
  if (options.length !== 2 || options[0] !== '--record') {
    throw new BuildRecordError('usage: record --record <path> -- <command...> | verify --record <path>');
  }
  // An unset FRONTEND_BUILD_RECORD expands to '', which resolve() would turn into the cwd.
  if (options[1] === '') throw new BuildRecordError('missing build record: (empty path)');
  return { command, recordPath: resolve(options[1]), buildCommand };
}

export async function main(argv: string[], roots: BuildRoots = DEFAULT_ROOTS): Promise<number> {
  try {
    const { command, recordPath, buildCommand } = parseArgs(argv);
    if (command === 'record') {
      const record = await recordBuild({ recordPath, command: buildCommand, roots });
      if (record.exitCode !== 0) {
        console.error(`build failed: exit ${String(record.exitCode)}, signal ${String(record.signal)}`);
        return record.exitCode || 1;
      }
      if (record.nonce === null) {
        console.error('build exited 0 but produced no dist/');
        return 1;
      }
      for (const path of record.buildCreatedInputs) console.log(`build created input: ${path}`);
      console.log(`frontend build record: ${recordPath}`);
      return 0;
    }
    if (command === 'verify' && buildCommand.length === 0) {
      const { record } = verifyBuildRecord(recordPath, roots);
      console.log(`verified frontend build record ${recordPath} (HEAD ${record.inputs.head})`);
      return 0;
    }
    throw new BuildRecordError('usage: record --record <path> -- <command...> | verify --record <path>');
  } catch (error) {
    if (!(error instanceof BuildRecordError)) throw error;
    console.error(`frontend build record: ${error.message}`);
    return 1;
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  process.exitCode = await main(process.argv.slice(2));
}
