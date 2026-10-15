/** Blocking evidence for #10702. Run from site/; never builds or changes test selection. */
import { execFileSync, spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, lstatSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { createServer } from 'node:net';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { setTimeout as delay } from 'node:timers/promises';
import { BUILD_ENV_KEYS, verifyBuildRecord } from './ci-build-artifact.ts';

const site = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const repo = resolve(site, '..');
const require = createRequire(join(site, 'package.json'));
const specs = ['practice-viewport', 'practice-touch-targets', 'atlas-practice', 'ui-policy-axe']
  .map(name => `e2e/${name}.spec.ts`);
const cli = join(site, 'node_modules/@playwright/test/cli.js');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const json = path => JSON.parse(readFileSync(path, 'utf8'));
const write = (path, value) => writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`);
const insist = (condition, message) => { if (!condition) throw new Error(message); };

function distDigest() {
  const files = [];
  function walk(path) {
    const absolute = join(site, 'dist', path);
    const stat = lstatSync(absolute);
    if (stat.isDirectory()) for (const name of readdirSync(absolute).sort()) walk(path ? `${path}/${name}` : name);
    else {
      insist(stat.isFile(), `unsupported dist entry: ${path}`);
      files.push([path, sha(readFileSync(absolute))]);
    }
  }
  walk('');
  insist(files.length > 1, 'empty dist');
  files.sort((a, b) => a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0);
  return sha(JSON.stringify(files));
}

function fingerprint(recordPath) {
  const { record } = verifyBuildRecord(recordPath);
  insist(record.buildEnv.node === process.version && record.buildEnv.platform === process.platform
    && record.buildEnv.arch === process.arch && BUILD_ENV_KEYS.every(key =>
      record.buildEnv.env[key] === (process.env[key] ?? null)), 'build runtime/environment changed');
  const paths = [...specs, 'playwright.config.ts', 'astro.config.mjs', 'package-lock.json',
    'tests/helpers/practice-browser-ci.mjs', 'tests/helpers/ci-build-artifact.ts',
    'node_modules/@playwright/test/cli.js', 'node_modules/playwright-core/browsers.json'];
  const packages = ['@playwright/test', 'playwright', 'playwright-core'];
  const lock = json(join(site, 'package-lock.json'));
  for (const pkg of packages) {
    const path = `node_modules/${pkg}/package.json`;
    const installed = json(join(site, path));
    insist(installed.version === lock.packages[`node_modules/${pkg}`]?.version,
      `installed ${pkg} differs from lock`);
    paths.push(path);
  }
  return {
    recordSha256: sha(readFileSync(recordPath)),
    inputs: record.inputs,
    log: { sha256: record.log.sha256, bytes: record.log.bytes },
    sourceSha: process.env.GITHUB_HEAD_SHA || record.inputs.head,
    testedSha: record.inputs.head,
    testedTree: execFileSync('git', ['rev-parse', 'HEAD^{tree}'], { cwd: repo, encoding: 'utf8',
      env: Object.fromEntries(Object.entries(process.env).filter(([key]) => !key.startsWith('GIT_'))),
    }).trim(),
    files: Object.fromEntries(paths.sort().map(path => [path, sha(readFileSync(join(site, path)))])),
    browserPin: json(join(site, 'node_modules/playwright-core/browsers.json')).browsers
      .filter(browser => ['chromium', 'chromium-headless-shell'].includes(browser.name)),
  };
}

function checkBaseline(recordPath) {
  const baseline = json(`${recordPath}.browser/baseline.json`);
  insist(baseline.schema === 'lu.practice-browser-baseline.v1', 'unknown baseline');
  insist(JSON.stringify(baseline.identity) === JSON.stringify(fingerprint(recordPath)), 'build/browser/spec identity changed');
  insist(baseline.dist === distDigest(), 'dist changed since adjacent post-build baseline');
  return baseline;
}

function inventory(report, requireEveryFile = true) {
  insist(report && Array.isArray(report.suites) && Array.isArray(report.errors), 'incomplete Playwright JSON');
  const config = report.config;
  insist(config && config.rootDir === join(site, 'e2e') && JSON.stringify(config.grep) === '{}'
    && config.grepInvert === null && config.shard === null, 'filtered or unexpected discovery config');
  insist(config.projects?.length === 1 && config.projects[0].name === 'chromium'
    && config.projects[0].repeatEach === 1 && config.projects[0].retries === 0, 'unexpected project/repeat/retry config');
  const cases = new Map();
  function visit(suite, parents) {
    insist(typeof suite.title === 'string' && Array.isArray(suite.specs), 'malformed suite');
    const titles = [...parents, suite.title];
    for (const spec of suite.specs) {
      insist(typeof spec.file === 'string' && typeof spec.title === 'string' && Array.isArray(spec.tests)
        && Number.isInteger(spec.line) && Number.isInteger(spec.column), 'malformed spec');
      insist(specs.includes(`e2e/${spec.file}`), `unexpected file: ${spec.file}`);
      for (const test of spec.tests) {
        insist(test.projectName === 'chromium' && Array.isArray(test.results), 'malformed case/project');
        const identity = JSON.stringify([spec.file, titles, spec.title, spec.line, spec.column, test.projectName]);
        insist(!cases.has(identity), `duplicate case: ${identity}`);
        cases.set(identity, test);
      }
    }
    for (const child of suite.suites ?? []) visit(child, titles);
  }
  for (const suite of report.suites) visit(suite, []);
  for (const spec of requireEveryFile ? specs : []) insist([...cases.keys()].some(key => JSON.parse(key)[0] === spec.slice(4)),
    `zero discovery for ${spec}/chromium`);
  return cases;
}

function reconcile(discovered, executed, report, counts) {
  counts.unavailable = 0;
  for (const identity of discovered.keys()) {
    const test = executed.get(identity);
    if (!test) { counts.unavailable++; continue; }
    counts.attempts += test.results.length;
    if (test.results.length === 0) { counts.unavailable++; continue; }
    if (test.results.some(result => result.status !== 'skipped')) counts.executed++;
    if (test.results.some(result => result.status === 'failed')) counts.failed++;
    else if (test.results.some(result => result.status === 'timedOut')) counts.timedOut++;
    else if (test.results.some(result => result.status === 'skipped')) counts.skipped++;
    else if (test.results.length === 1 && test.results[0].status === 'passed'
      && test.results[0].retry === 0 && Array.isArray(test.results[0].errors)
      && test.results[0].errors.length === 0 && !test.results[0].error
      && test.expectedStatus === 'passed' && test.status === 'expected') counts.passed++;
    else counts.unavailable++;
  }
  insist(discovered.size === executed.size && [...discovered.keys()].every(key => executed.has(key)),
    'missing or unexpected executed case identities');
  insist(report.errors.length === 0, `Playwright global errors: ${report.errors.length}`);
  insist(counts.passed === discovered.size, 'incomplete successful browser evidence');
  insist(report.stats?.expected === discovered.size && report.stats.unexpected === 0
    && report.stats.skipped === 0 && report.stats.flaky === 0, 'inconsistent Playwright stats');
}

function saveReceipt(directory, receipt) {
  receipt.evidence = {};
  for (const name of ['baseline.json', 'discovery.json', 'run.json', 'discovery.log', 'run.log']) {
    if (existsSync(join(directory, name))) receipt.evidence[name] = sha(readFileSync(join(directory, name)));
  }
  write(join(directory, 'receipt.json'), receipt);
}

async function unusedPort(port = 0) {
  const server = createServer();
  await new Promise((yes, no) => server.once('error', no).listen(port, '127.0.0.1', yes));
  const address = server.address();
  await new Promise((yes, no) => server.close(error => error ? no(error) : yes()));
  return address.port;
}

function launch(args, reportPath, logPath, port) {
  insist(!existsSync(reportPath), `refusing stale report: ${reportPath}`);
  const child = spawn(process.execPath, [cli, 'test', ...specs, '--config=playwright.config.ts',
    '--project=chromium', '--workers=1', '--retries=0', '--forbid-only', '--reporter=json',
    `--output=${join(dirname(reportPath), 'test-results')}`, ...args], {
    cwd: site, env: { ...process.env, PLAYWRIGHT_PORT: String(port), PLAYWRIGHT_JSON_OUTPUT_FILE: reportPath },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  const chunks = [];
  for (const [stream, output] of [[child.stdout, process.stdout], [child.stderr, process.stderr]]) {
    stream.on('data', chunk => { chunks.push(chunk); output.write(chunk); });
  }
  let finished = false;
  const done = new Promise((yes, no) => {
    child.once('error', no);
    child.once('close', (code, signal) => {
      finished = true;
      writeFileSync(logPath, Buffer.concat(chunks));
      yes({ code, signal });
    });
  });
  return { child, done, finished: () => finished };
}

async function servedBuild(processRun, port, recordPath, baseline) {
  const deadline = Date.now() + 180_000;
  const base = `http://127.0.0.1:${port}`;
  while (!processRun.finished() && Date.now() < deadline) {
    let response;
    try { response = await fetch(`${base}/.frontend-build-nonce`, { signal: AbortSignal.timeout(1000) }); }
    catch { await delay(50); continue; }
    insist(response.ok, `served nonce HTTP ${response.status}`);
    const nonce = await response.text();
    insist(nonce === json(recordPath).nonce, 'wrong served build nonce');
    const index = await fetch(`${base}/`, { signal: AbortSignal.timeout(5000) });
    insist(index.ok, `served index HTTP ${index.status}`);
    const indexSha256 = sha(Buffer.from(await index.arrayBuffer()));
    insist(indexSha256 === sha(readFileSync(join(site, 'dist/index.html'))), 'wrong served build bytes');
    insist(distDigest() === baseline.dist, 'dist changed during preview startup');
    return { nonce, indexSha256, dist: baseline.dist, base };
  }
  throw new Error('no task-owned preview evidence before browser exit/deadline');
}

export async function main(argv) {
  if (argv.length === 1 && argv[0] === '--help') {
    process.stdout.write(`Require complete practice Chromium evidence for the existing Frontend build (#10702).
Use baseline immediately after the recorded build and adjacent generated-key drift check, then run after unit/built-output checks.
  node --experimental-strip-types tests/helpers/practice-browser-ci.mjs baseline --record "$FRONTEND_BUILD_RECORD"
  node --experimental-strip-types tests/helpers/practice-browser-ci.mjs run --record "$FRONTEND_BUILD_RECORD"
Only these commands/arguments are accepted. No selection overrides. CI must be enabled consistently with the build.
Outputs: <record>.browser/baseline.json, discovery/run JSON and logs, receipt.json and failure traces. Never rebuilds.
Exit codes: 0 complete positive evidence; subprocess failure retains its exit code; other missing/invalid evidence exits 1.
Related: ci-build-artifact.ts, playwright.config.ts, .github/workflows/ci.yml.
`);
    return 0;
  }
  let receipt, directory;
  let exitCode = 1;
  try {
    const [command, option, recordArg] = argv;
    insist(argv.length === 3 && ['baseline', 'run'].includes(command) && option === '--record' && recordArg,
      'usage: baseline|run --record <path>; selection arguments are forbidden');
    insist(['1', 'true'].includes(process.env.CI), 'CI must be enabled; foreign-server reuse is forbidden');
    for (const key of Object.keys(process.env)) {
      insist(!/^(PW_TEST_|PWTEST_|PWDEBUG|PLAYWRIGHT_)/.test(key) || key === 'PLAYWRIGHT_BROWSERS_PATH',
        `inherited selection/runtime override forbidden: ${key}`);
    }
    insist(!process.env.ASTRO_PREVIEW_BACKGROUND, 'background preview override forbidden');
    const recordPath = resolve(recordArg);
    directory = `${recordPath}.browser`;
    if (command === 'baseline') {
      mkdirSync(directory, { recursive: true });
      insist(!existsSync(join(directory, 'baseline.json')), 'baseline already exists; never recapture');
      const identity = fingerprint(recordPath);
      write(join(directory, 'baseline.json'), { schema: 'lu.practice-browser-baseline.v1', identity, dist: distDigest() });
      return 0;
    }
    const baseline = checkBaseline(recordPath);
    receipt = {
      schema: 'lu.practice-browser-receipt.v1', status: 'failed', baseline,
      run: { id: process.env.GITHUB_RUN_ID ?? null, attempt: process.env.GITHUB_RUN_ATTEMPT ?? null,
        job: process.env.GITHUB_JOB ?? null },
      counts: { discovered: 0, executed: 0, passed: 0, failed: 0, timedOut: 0, skipped: 0,
        unavailable: 0, attempts: 0, globalErrors: 0 },
    };
    const discovery = launch(['--list'], join(directory, 'discovery.json'), join(directory, 'discovery.log'), 0);
    receipt.discoveryExit = await discovery.done;
    if (receipt.discoveryExit.code !== 0) { exitCode = receipt.discoveryExit.code || 1; throw new Error('discovery subprocess failed'); }
    const discoveredReport = json(join(directory, 'discovery.json'));
    const discovered = inventory(discoveredReport);
    receipt.counts.discovered = discovered.size;
    receipt.counts.unavailable = discovered.size;
    insist(discoveredReport.errors.length === 0, 'discovery global errors');
    receipt.cases = [...discovered.keys()].sort();
    const { chromium } = require('playwright');
    const browser = await chromium.launch({ headless: true });
    try { receipt.browserVersion = browser.version(); } finally { await browser.close(); }
    insist(baseline.identity.browserPin.length === 2
      && baseline.identity.browserPin.every(pin => pin.browserVersion === receipt.browserVersion), 'browser differs from locked revision');
    checkBaseline(recordPath);
    receipt.distBefore = distDigest();
    const port = await unusedPort();
    const execution = launch([], join(directory, 'run.json'), join(directory, 'run.log'), port);
    // Observe the server launched and reaped by the unchanged CI Playwright config.
    // Always settle Playwright so its process-group cleanup runs, even if identity fails.
    const [result, served] = await Promise.allSettled([
      execution.done, servedBuild(execution, port, recordPath, baseline),
    ]);
    insist(result.status === 'fulfilled', 'execution process failed to settle');
    receipt.executionExit = result.value;
    if (result.value.code !== 0) exitCode = result.value.code || 1;
    if (served.status === 'fulfilled') receipt.served = served.value;
    // A remaining listener is not reusable and cannot qualify a successful receipt.
    await unusedPort(port);
    receipt.distAfter = distDigest();
    checkBaseline(recordPath);
    const executionReport = json(join(directory, 'run.json'));
    receipt.counts.globalErrors = executionReport.errors?.length ?? 1;
    reconcile(discovered, inventory(executionReport, false), executionReport, receipt.counts);
    insist(served.status === 'fulfilled', served.status === 'rejected' ? served.reason.message : 'missing served identity');
    insist(result.value.code === 0 && !result.value.signal, 'browser subprocess failed');
    receipt.status = 'passed';
    saveReceipt(directory, receipt);
    process.stdout.write(`${JSON.stringify(receipt.counts)}\n`);
    return 0;
  } catch (error) {
    if (receipt) {
      receipt.error = error.message;
      saveReceipt(directory, receipt);
    }
    process.stderr.write(`practice browser CI: ${error.message}\n`);
    return exitCode;
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  process.exitCode = await main(process.argv.slice(2));
}
