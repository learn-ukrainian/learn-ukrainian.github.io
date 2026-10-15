// @vitest-environment node
import { execFileSync, spawnSync } from 'node:child_process';
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { afterEach, expect, it } from 'vitest';
import { recordBuild } from '../helpers/ci-build-artifact';

const wrapper = resolve(__dirname, '../helpers/practice-browser-ci.mjs');
const roots: string[] = [];
const files = ['practice-viewport', 'practice-touch-targets', 'atlas-practice', 'ui-policy-axe'];
const env = Object.fromEntries(Object.entries(process.env).filter(([k]) =>
  !/^(GIT_|PW_TEST_|PLAYWRIGHT_|FRONTEND_BUILD_RECORD)/.test(k)));

function report(run: boolean) {
  return {
    config: { rootDir: '', grep: {}, grepInvert: null, shard: null, projects: [
      { name: 'chromium', repeatEach: 1, retries: 0 },
    ] },
    errors: [], stats: { expected: run ? 4 : 0, unexpected: 0, flaky: 0, skipped: run ? 0 : 4 },
    suites: files.map(file => ({ title: `${file}.spec.ts`, specs: [{
      title: 'literal case', file: `${file}.spec.ts`, line: 1, column: 1,
      tests: [{ projectName: 'chromium', expectedStatus: 'passed', status: run ? 'expected' : 'skipped',
        results: run ? [{ status: 'passed', retry: 0, errors: [] }] : [] }],
    }] })),
  };
}

async function fixture(control = '') {
  const repoRoot = mkdtempSync(join(tmpdir(), 'practice-browser-ci-'));
  roots.push(repoRoot);
  const siteDir = join(repoRoot, 'site');
  for (const path of ['tests/helpers', 'e2e', 'src/data', 'public', 'node_modules/@playwright/test',
    'node_modules/playwright', 'node_modules/playwright-core']) mkdirSync(join(siteDir, path), { recursive: true });
  mkdirSync(join(repoRoot, 'data'));
  copyFileSync(wrapper, join(siteDir, 'tests/helpers/practice-browser-ci.mjs'));
  copyFileSync(resolve(__dirname, '../helpers/ci-build-artifact.ts'), join(siteDir, 'tests/helpers/ci-build-artifact.ts'));
  for (const file of files) writeFileSync(join(siteDir, `e2e/${file}.spec.ts`), '// fixture\n');
  writeFileSync(join(siteDir, 'playwright.config.ts'), '// fixture config\n');
  writeFileSync(join(siteDir, 'astro.config.mjs'), '// fixture config\n');
  writeFileSync(join(siteDir, 'package.json'), '{"type":"module"}');
  writeFileSync(join(siteDir, 'package-lock.json'), JSON.stringify({ packages: {
    'node_modules/@playwright/test': { version: '1.63.0' },
    'node_modules/playwright': { version: '1.63.0' },
    'node_modules/playwright-core': { version: '1.63.0' },
  } }));
  for (const pkg of ['@playwright/test', 'playwright', 'playwright-core']) {
    writeFileSync(join(siteDir, `node_modules/${pkg}/package.json`), '{"version":"1.63.0","main":"index.cjs"}');
  }
  writeFileSync(join(siteDir, 'node_modules/playwright/index.cjs'), control === 'browserMissing'
    ? "exports.chromium={launch:async()=>{throw Error('Executable does not exist')}}"
    : `exports.chromium = {
    launch: async () => ({version: () => '149.0.0.0', close: async () => {}})
  };`);
  writeFileSync(join(siteDir, 'node_modules/playwright-core/browsers.json'), JSON.stringify({ browsers: [
    { name: 'chromium', revision: '1234', browserVersion: '149.0.0.0' },
    { name: 'chromium-headless-shell', revision: '1234', browserVersion: '149.0.0.0' },
  ] }));
  writeFileSync(join(siteDir, 'node_modules/@playwright/test/cli.js'), `
    const fs = require('node:fs'); const http = require('node:http');
    const discovery = process.argv.includes('--list');
    const data = fs.readFileSync(discovery ? 'discovery-fixture.json' : 'run-fixture.json');
    if (discovery) {
      fs.writeFileSync(process.env.PLAYWRIGHT_JSON_OUTPUT_FILE, data);
    } else {
      const server = http.createServer((req, res) => {
        res.end(req.url === '/' && ${control === 'wrongBytes'} ? 'wrong served bytes' :
          fs.readFileSync(req.url === '/.frontend-build-nonce' && ${control !== 'wrongServer'} ? 'dist/.frontend-build-nonce' : 'dist/index.html'));
      });
      server.listen(Number(process.env.PLAYWRIGHT_PORT), '127.0.0.1', () => setTimeout(() => {
        fs.writeFileSync(process.env.PLAYWRIGHT_JSON_OUTPUT_FILE, data);
        if (${control === 'lateDistDrift'}) fs.writeFileSync('dist/index.html', 'changed during execution');
        server.close(); process.exit(Number(fs.readFileSync('exit-fixture', 'utf8')));
      }, 350));
    }
  `);
  const discovery = report(false), execution = report(true);
  discovery.config.rootDir = execution.config.rootDir = join(siteDir, 'e2e');
  writeFileSync(join(siteDir, 'discovery-fixture.json'), JSON.stringify(discovery));
  writeFileSync(join(siteDir, 'run-fixture.json'), JSON.stringify(execution));
  writeFileSync(join(siteDir, 'exit-fixture'), '0');
  writeFileSync(join(repoRoot, 'data/atlas.db'), 'fixture');
  writeFileSync(join(siteDir, 'src/data/input.json'), '{}');
  writeFileSync(join(repoRoot, '.gitignore'), 'site/dist/\nrecord*\nsite/*fixture*\n');
  for (const args of [['init', '-q'], ['add', '.'], ['-c', 'user.name=fixture', '-c',
    'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture']]) {
    execFileSync('git', args, { cwd: repoRoot, env, stdio: 'ignore' });
  }
  const recordPath = join(repoRoot, 'record.json');
  await recordBuild({ roots: { repoRoot, siteDir }, recordPath, env: { ...env, CI: '1' }, echo: false,
    command: [process.execPath, '-e', "require('fs').mkdirSync('dist');require('fs').writeFileSync('dist/index.html','<h1>literal build</h1>')"] });
  const cli = (command: string, args: string[] = [], extraEnv = {}) => spawnSync(process.execPath,
    ['--experimental-strip-types', join(siteDir, 'tests/helpers/practice-browser-ci.mjs'), command, '--record', recordPath, ...args],
    { cwd: siteDir, env: { ...env, CI: '1', ...extraEnv }, encoding: 'utf8', timeout: 15000 });
  return { repoRoot, siteDir, recordPath, discovery, execution, cli,
    save: () => {
      writeFileSync(join(siteDir, 'discovery-fixture.json'), JSON.stringify(discovery));
      writeFileSync(join(siteDir, 'run-fixture.json'), JSON.stringify(execution));
    } };
}

afterEach(() => { for (const root of roots.splice(0)) rmSync(root, { recursive: true, force: true }); });

it('runs the complete CLI and emits literal reconciled counts and a bound receipt', async () => {
  const f = await fixture();
  expect(f.cli('baseline').status).toBe(0);
  const result = f.cli('run');
  expect(result.stderr).toBe('');
  expect(result.status).toBe(0);
  const receipt = JSON.parse(readFileSync(`${f.recordPath}.browser/receipt.json`, 'utf8'));
  expect(receipt.counts).toEqual({ discovered: 4, executed: 4, passed: 4, failed: 0, timedOut: 0,
    skipped: 0, unavailable: 0, attempts: 4, globalErrors: 0 });
  expect(receipt.distBefore).toBe(receipt.baseline.dist);
  expect(receipt.distAfter).toBe(receipt.baseline.dist);
  expect(receipt.served.nonce).toBe(JSON.parse(readFileSync(f.recordPath, 'utf8')).nonce);
});

it.each(['zero', 'missing', 'duplicate', 'skipped', 'unrun', 'failed', 'timedOut', 'globalError', 'wrongIdentity', 'retry', 'malformed', 'nonzero'])(
  'refuses %s evidence through the CLI', async (kind) => {
    const f = await fixture(kind);
    expect(f.cli('baseline').status).toBe(0);
    const first = f.execution.suites[0].specs[0].tests[0];
    if (kind === 'zero') f.discovery.suites = [];
    if (kind === 'missing') f.execution.suites.pop();
    if (kind === 'duplicate') f.execution.suites.push(f.execution.suites[0]);
    if (['skipped', 'failed', 'timedOut'].includes(kind)) first.results[0].status = kind;
    if (kind === 'unrun') first.results = [];
    if (kind === 'globalError') Object.assign(f.execution, { errors: [{ message: 'literal global error' }] });
    if (kind === 'wrongIdentity') f.execution.suites[0].specs[0].title = 'different case';
    if (kind === 'retry') first.results.push({ status: 'passed', retry: 1, errors: [] });
    f.save();
    if (kind === 'malformed') writeFileSync(join(f.siteDir, 'run-fixture.json'), '{');
    if (kind === 'nonzero') writeFileSync(join(f.siteDir, 'exit-fixture'), '7');
    const result = f.cli('run');
    expect(result.status).toBe(kind === 'nonzero' ? 7 : 1);
    expect(result.stderr).toContain('practice browser CI:');
  });

it.each(['--grep', '--project', '--pass-with-no-tests'])('refuses selection argument %s', async arg => {
  const f = await fixture();
  expect(f.cli('run', [arg, 'literal case']).status).toBe(1);
});

it.each(['PW_TEST_GREP', 'PLAYWRIGHT_TEST_FILTER', 'PW_TEST_REPORTER'])('refuses inherited %s', async key => {
  const f = await fixture();
  expect(f.cli('baseline', [], { [key]: 'literal case' }).status).toBe(1);
});

it('rejects a shared nonempty filtered subset in discovery and execution', async () => {
  const f = await fixture();
  expect(f.cli('baseline').status).toBe(0);
  Object.assign(f.discovery.config, { grep: { source: 'literal', flags: '' } });
  Object.assign(f.execution.config, { grep: { source: 'literal', flags: '' } });
  f.save();
  expect(f.cli('run').status).toBe(1);
});

it.each(['absent', 'failed', 'inputDrift', 'distDrift', 'lateDistDrift', 'noDist', 'envDrift', 'noBaseline', 'wrongServer', 'wrongBytes', 'browserMissing'])(
  'rejects %s without blessing another baseline', async kind => {
    const f = await fixture(kind);
    if (kind !== 'noBaseline') expect(f.cli('baseline').status).toBe(0);
    if (kind === 'absent') rmSync(f.recordPath);
    if (kind === 'failed') {
      const record = JSON.parse(readFileSync(f.recordPath, 'utf8')); record.exitCode = 3;
      writeFileSync(f.recordPath, JSON.stringify(record));
    }
    if (kind === 'inputDrift') writeFileSync(join(f.siteDir, 'src/data/input.json'), '{"changed":true}');
    if (kind === 'distDrift') writeFileSync(join(f.siteDir, 'dist/index.html'), '<h1>changed, nonce preserved</h1>');
    if (kind === 'noDist') rmSync(join(f.siteDir, 'dist'), { recursive: true });
    const result = f.cli('run', [], kind === 'envDrift' ? { NODE_ENV: 'changed' } : {});
    expect(result.status).toBe(1);
    expect(result.stderr).toContain('practice browser CI:');
    if (kind === 'distDrift') expect(result.stderr).toContain('dist changed');
    if (kind === 'wrongServer') expect(result.stderr).toContain('wrong served build nonce');
    if (kind === 'wrongBytes') expect(result.stderr).toContain('wrong served build bytes');
    if (kind === 'browserMissing') expect(result.stderr).toContain('Executable does not exist');
  });

it('never recaptures an existing baseline after dist mutates', async () => {
  const f = await fixture();
  expect(f.cli('baseline').status).toBe(0);
  writeFileSync(join(f.siteDir, 'dist/index.html'), 'mutated with original nonce');
  expect(f.cli('baseline').status).toBe(1);
  expect(f.cli('run').status).toBe(1);
});
