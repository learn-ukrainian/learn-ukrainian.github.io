import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { cpSync, mkdirSync, readFileSync, writeFileSync, symlinkSync, readdirSync, existsSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import type { ReleasePin } from '../../../src/lib/lexicon/word-card-release';

export const pins = {
  jsonl: { release_version: 'v0.1.0-synthetic',
    dataset_sha256: 'edb0a667ed727597e0ae5187bff82b2ffeea0a03bfbcc48b91934a8b6cb22cbd',
    manifest_sha256: '24c3b98a65f57294bec78795c179252950eb071ede008320ce03b06f6c5faf6d', provenance: 'synthetic-fixture' },
  json: { release_version: 'v0.1.1-synthetic',
    dataset_sha256: 'e76f299a4302ccbb922732cbaf77f0211183f24fd5be5584b0e59e55ae20a8ae',
    manifest_sha256: '94dfc11425a3cf23dd23accb984366505edaa492d46bc9bc67f152fdbd89fa68', provenance: 'synthetic-fixture' },
} satisfies Record<string, ReleasePin>;
export const fixtureRoot = resolve('tests/fixtures/word-card-preview');
export const digest = (bytes: string | Buffer) => createHash('sha256').update(bytes).digest('hex');
export const candidateId = 'wc_0123456789ac';
export const certifiedId = 'wc_0123456789ab';
export type Control = { enabled: boolean; artifactPath?: string; pin?: string };

/** Negative rows are re-manifested by the pinned producer's canonical/hash functions. */
export function remanifest(directory: string, fault: string): string {
  const common = execFileSync('git', ['rev-parse', '--path-format=absolute', '--git-common-dir'], { encoding: 'utf8' }).trim();
  const interpreter = process.env.PYTHON || resolve(common, '../.venv/bin/python');
  return execFileSync(interpreter, ['-c', `
import json, sys
from pathlib import Path
from scripts.projects.open_model_data.word_cards.dataset_projection import canonical, sha256
p, fault = Path(sys.argv[1]), sys.argv[2]
m = json.loads((p/'manifest.json').read_bytes())
rows = [json.loads(line) for line in (p/m['dataset_file']).read_bytes().splitlines()]
if fault == 'status': rows[1]['status'] = 'APPROVED'
elif fault == 'missing-status': del rows[1]['status']
elif fault == 'citation': del rows[1]['fields'][1]['citation']
elif fault == 'required': del rows[1]['card_version']
elif fault == 'tamper': rows[1]['fields'][0]['value'] = 'TAMPERED'
elif fault == 'duplicate': rows[1]['card_id'] = rows[0]['card_id']
elif fault == 'assertion': rows[1]['fields'][0]['assertion_id'] = rows[0]['fields'][0]['assertion_id']
elif fault == 'subject': rows[1]['fields'][0]['subject']['id'] = rows[0]['card_id']
elif fault == 'binding': rows[1]['fields'][0]['citation']['licence_ref']['register_source_id'] = 'wrong'
elif fault == 'licence': rows[1]['fields'][0]['citation']['licence']['name'] = ''
elif fault == 'empty': rows = []
elif fault == 'shape': rows = {'unsupported': 'object'}
data = canonical(rows) if fault == 'shape' else b''.join(canonical(row) for row in rows)
if fault == 'shape': m['dataset_file'] = 'word-cards.json'
if fault == 'count': m['card_count'] = 7
if fault == 'schema': m['schema_version'] = 'unsupported.v1'
if fault == 'path': m['dataset_file'] = '../private.json'
if fault == 'withdrawal': m['withdrawal_notice_sha256'] = sha256(b'notice\\n'); (p/'withdrawal-notice.json').write_bytes(b'wrong\\n')
if fault == 'withdrawal-valid': m['withdrawal_notice_sha256'] = sha256(b'notice\\n'); (p/'withdrawal-notice.json').write_bytes(b'notice\\n')
if fault == 'malformed-dataset': data = b'{invalid JSON\\n'
if fault == 'empty': m.update(card_count=0, certified_count=0, candidate_count=0, field_citation_count=0)
m.update(dataset_bytes=len(data), dataset_sha256=sha256(data))
(p/m['dataset_file']).write_bytes(data)
manifest = canonical(m)
(p/'manifest.json').write_bytes(manifest)
print(json.dumps(dict(release_version=m['release_version'], dataset_sha256=m['dataset_sha256'], manifest_sha256=sha256(manifest), provenance='synthetic-fixture')))
`, directory, fault], { cwd: resolve('..'), encoding: 'utf8' }).trim();
}

export function releaseControls(root: string): Record<string, Control> {
  mkdirSync(root, { recursive: true });
  const base = join(root, 'base');
  cpSync(join(fixtureRoot, 'release-jsonl'), base, { recursive: true });
  const controls: Record<string, Control> = {
    base: { enabled: true, artifactPath: base, pin: JSON.stringify(pins.jsonl) },
    json: { enabled: true, artifactPath: join(fixtureRoot, 'release-json'), pin: JSON.stringify(pins.json) },
    absent: { enabled: true }, missing: { enabled: true, artifactPath: join(root, 'missing'), pin: JSON.stringify(pins.jsonl) },
    off: { enabled: false, artifactPath: join(root, 'must-not-read'), pin: 'invalid' },
  };
  for (const fault of ['status', 'missing-status', 'citation', 'required', 'tamper', 'duplicate', 'assertion', 'subject', 'binding', 'licence', 'count', 'schema', 'path', 'withdrawal', 'withdrawal-valid', 'shape', 'empty', 'malformed-dataset']) {
    const path = join(root, fault);
    cpSync(base, path, { recursive: true });
    controls[fault] = { enabled: true, artifactPath: path, pin: remanifest(path, fault) };
  }
  controls.tamper = { ...controls.tamper, pin: JSON.stringify(pins.jsonl) };
  for (const fault of ['malformed', 'bytes', 'replacement']) {
    const path = join(root, fault);
    cpSync(base, path, { recursive: true });
    let pin: ReleasePin = pins.jsonl;
    if (fault === 'malformed') {
      writeFileSync(join(path, 'manifest.json'), '{');
      pin = { ...pin, manifest_sha256: digest('{') };
    } else if (fault === 'bytes') writeFileSync(join(path, 'word-cards.jsonl'), readFileSync(join(path, 'word-cards.jsonl')).toString() + ' ');
    else cpSync(join(fixtureRoot, 'release-json'), path, { recursive: true });
    controls[fault] = { enabled: true, artifactPath: path, pin: JSON.stringify(pin) };
  }
  return controls;
}

/** Isolated diagnostic build: actual route/components, no corpus hydration or other pages. */
export function buildPreview(root: string, config: Control): string {
  const site = process.cwd();
  const src = join(root, 'src');
  mkdirSync(join(src, 'pages/lexicon-v2'), { recursive: true });
  for (const name of readdirSync(join(site, 'src'))) if (name !== 'pages' && name !== 'content' && name !== 'content.config.ts') {
    cpSync(join(site, 'src', name), join(src, name), { recursive: true });
  }
  for (const name of ['schemas', 'docs', 'packages']) if (!existsSync(join(root, '..', name))) symlinkSync(resolve(site, '..', name), join(root, '..', name));
  symlinkSync(join(site, 'tests'), join(root, 'tests'));
  symlinkSync(join(site, 'node_modules'), join(root, 'node_modules'));
  symlinkSync(join(site, 'package.json'), join(root, 'package.json'));
  cpSync(join(site, 'src/pages/lexicon-v2/[...path].astro'), join(src, 'pages/lexicon-v2/[...path].astro'));
  const out = join(root, 'dist');
  const configPath = join(root, 'astro.config.mjs');
  writeFileSync(configPath, `import base from ${JSON.stringify(pathToFileURL(join(site, 'astro.config.mjs')).href)};
export default {...base, root:${JSON.stringify(root)}, srcDir:${JSON.stringify(src)}, outDir:${JSON.stringify(out)},
publicDir:${JSON.stringify(join(root, 'public'))}, cacheDir:${JSON.stringify(join(root, 'cache'))}};\n`);
  try {
    const log = execFileSync(join(site, 'node_modules/.bin/astro'), ['build', '--root', root, '--config', 'astro.config.mjs'], {
      encoding: 'utf8', timeout: 120_000, env: { ...process.env, ATLAS_WORD_CARD_PREVIEW: config.enabled ? '1' : '0',
        ATLAS_WORD_CARD_RELEASE_PATH: config.artifactPath || '', ATLAS_WORD_CARD_RELEASE_PIN: config.pin || '' },
    });
    writeFileSync(join(root, 'build.log'), log);
  } catch (error) {
    if (error && typeof error === 'object' && 'stdout' in error) writeFileSync(join(root, 'build.log'), String(error.stdout));
    throw error;
  }
  return out;
}
