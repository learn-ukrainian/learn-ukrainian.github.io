// @ts-check
/**
 * One selection policy for the generated Word Atlas search/browse artifacts (#12527).
 *
 * Two projections of the same five JSON files exist:
 *
 * - committed: the DB-derived snapshot tracked under `src/data` and
 *   `public/lexicon/browse`. Python tests, `verify:artifacts` and unpinned
 *   builds read it.
 * - pinned: the projection of the immutable Atlas runtime tree that Pages
 *   deploys. `generate_search_index.py` writes it to the ignored
 *   `.atlas-pinned/` directory when `ATLAS_SEARCH_RUNTIME_TREE` is set, so a
 *   release build never rewrites tracked files.
 *
 * Every reader (Vite imports, filesystem readers, the Node hydration script,
 * `verify:artifacts`, the build record and the dist installer) asks this module
 * which one is selected. The pinned selection fails closed: a missing or
 * incomplete pinned set is an error and never falls back to committed files.
 *
 * Callers pass `siteRoot` explicitly: bundled server chunks cannot derive it
 * from `import.meta.url`, so runtime readers pass `process.cwd()` (the `site/`
 * directory, as the other runtime readers already assume).
 */
import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, rmSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';

export const PINNED_SELECTION_ENV = 'ATLAS_SEARCH_RUNTIME_TREE';
/** Ignored build directory under `site/`; `generate_search_index.py` writes the same name. */
export const PINNED_ARTIFACT_DIRNAME = '.atlas-pinned';
/** The generated JSON files whose location depends on the selection. */
export const SELECTED_ARTIFACT_NAMES = Object.freeze([
  'lexicon-search-index.json',
  'lexicon-search-aliases.json',
  'lexicon-search-shards.json',
  'lexicon-browse-meta.json',
  'lexicon-browse-flagged.json',
]);

const SELECTED_NAME_PATTERN = SELECTED_ARTIFACT_NAMES.map((name) =>
  name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'),
).join('|');
const SELECTED_IMPORT_RE = new RegExp(`(?:^|/)(${SELECTED_NAME_PATTERN})$`);

export class AtlasArtifactSelectionError extends Error {
  /** @param {string} message */
  constructor(message) {
    super(message);
    this.name = 'AtlasArtifactSelectionError';
  }
}

/** @param {NodeJS.ProcessEnv} [env] */
export function isPinnedSelection(env = process.env) {
  return typeof env[PINNED_SELECTION_ENV] === 'string' && env[PINNED_SELECTION_ENV].trim() !== '';
}

/**
 * @param {string} siteRoot
 * @param {NodeJS.ProcessEnv} [env]
 */
export function resolveSelectedArtifactLocations(siteRoot, env = process.env) {
  const root = resolve(siteRoot);
  const pinned = isPinnedSelection(env);
  return {
    mode: /** @type {'pinned' | 'committed'} */ (pinned ? 'pinned' : 'committed'),
    committedDataDir: join(root, 'src', 'data'),
    dataDir: pinned ? join(root, PINNED_ARTIFACT_DIRNAME, 'data') : join(root, 'src', 'data'),
    browseDir: pinned
      ? join(root, PINNED_ARTIFACT_DIRNAME, 'public', 'lexicon', 'browse')
      : join(root, 'public', 'lexicon', 'browse'),
  };
}

/**
 * @param {string} name
 * @param {string} siteRoot
 * @param {NodeJS.ProcessEnv} [env]
 */
export function selectedArtifactPath(name, siteRoot, env = process.env) {
  if (!SELECTED_ARTIFACT_NAMES.includes(name)) {
    throw new AtlasArtifactSelectionError(`${name} is not a selectable Atlas artifact`);
  }
  return join(resolveSelectedArtifactLocations(siteRoot, env).dataDir, name);
}

/**
 * Read one selected artifact. Pinned selection never falls back to committed files.
 * @param {string} name
 * @param {string} siteRoot
 * @param {NodeJS.ProcessEnv} [env]
 */
export function readSelectedArtifactText(name, siteRoot, env = process.env) {
  const path = selectedArtifactPath(name, siteRoot, env);
  if (isPinnedSelection(env) && !existsSync(path)) {
    throw new AtlasArtifactSelectionError(
      `${PINNED_SELECTION_ENV} is set but ${path} is missing; run the pinned hydrate (atlas:build-search) first`,
    );
  }
  return readFileSync(path, 'utf8');
}

/**
 * @param {string} name
 * @param {string} siteRoot
 * @param {NodeJS.ProcessEnv} [env]
 */
export function readSelectedArtifactJson(name, siteRoot, env = process.env) {
  return JSON.parse(readSelectedArtifactText(name, siteRoot, env));
}

/**
 * Letters the browse metadata advertises, mapped to their shard file names.
 * @param {unknown} meta
 * @param {string} metaPath
 * @returns {string[]}
 */
export function browseShardFileNames(meta, metaPath) {
  const shards =
    meta && typeof meta === 'object' ? /** @type {{ browseShards?: unknown }} */ (meta).browseShards : undefined;
  if (!shards || typeof shards !== 'object' || Array.isArray(shards)) {
    throw new AtlasArtifactSelectionError(`${metaPath} lacks a browseShards object`);
  }
  return Object.entries(shards).map(([letter, shard]) => {
    const path = shard && typeof shard === 'object' ? /** @type {{ path?: unknown }} */ (shard).path : undefined;
    if (typeof path !== 'string' || !path.startsWith('/lexicon/browse/') || !path.endsWith('.json')) {
      throw new AtlasArtifactSelectionError(`${metaPath} has an invalid browse shard for ${letter}`);
    }
    return path.slice('/lexicon/browse/'.length);
  });
}

/**
 * Throw unless the pinned set is complete and has no stale shard. A no-op for the
 * committed selection, whose completeness `verify:artifacts` owns.
 * @param {string} siteRoot
 * @param {NodeJS.ProcessEnv} [env]
 */
export function assertSelectedArtifactsComplete(siteRoot, env = process.env) {
  if (!isPinnedSelection(env)) return;
  const { dataDir, browseDir } = resolveSelectedArtifactLocations(siteRoot, env);
  const missing = SELECTED_ARTIFACT_NAMES.filter((name) => !existsSync(join(dataDir, name)));
  if (missing.length > 0) {
    throw new AtlasArtifactSelectionError(
      `${PINNED_SELECTION_ENV} is set but the pinned set in ${dataDir} lacks: ${missing.join(', ')}`,
    );
  }
  const metaPath = join(dataDir, 'lexicon-browse-meta.json');
  const expected = new Set(browseShardFileNames(JSON.parse(readFileSync(metaPath, 'utf8')), metaPath));
  const present = existsSync(browseDir) ? readdirSync(browseDir).filter((name) => name.endsWith('.json')) : [];
  const absent = [...expected].filter((name) => !present.includes(name));
  const stale = present.filter((name) => !expected.has(name));
  if (absent.length > 0 || stale.length > 0) {
    throw new AtlasArtifactSelectionError(
      `pinned browse shards in ${browseDir} do not match lexicon-browse-meta.json` +
        ` (missing: ${absent.join(', ') || 'none'}; stale: ${stale.join(', ') || 'none'})`,
    );
  }
}

/**
 * Replace the letter shards in `<distDir>/lexicon/browse` with the pinned ones.
 * `public/` carries the committed shards into every build; the pinned build must
 * ship only its own. The directory also holds the prerendered browse page
 * (`index.html`), so only the `*.json` shards are replaced. A no-op for the
 * committed selection.
 * @param {string} distDir
 * @param {string} siteRoot
 * @param {NodeJS.ProcessEnv} [env]
 */
export function installSelectedBrowseShards(distDir, siteRoot, env = process.env) {
  if (!isPinnedSelection(env)) return;
  assertSelectedArtifactsComplete(siteRoot, env);
  const { browseDir } = resolveSelectedArtifactLocations(siteRoot, env);
  const target = join(distDir, 'lexicon', 'browse');
  mkdirSync(target, { recursive: true });
  for (const name of readdirSync(target)) {
    if (name.endsWith('.json')) rmSync(join(target, name));
  }
  for (const name of readdirSync(browseDir)) {
    if (name.endsWith('.json')) cpSync(join(browseDir, name), join(target, name));
  }
}

/**
 * Vite plugin that redirects the static JSON imports of the five selected
 * artifacts (`../data/lexicon-*.json` from anywhere under `src/`, including
 * client-bundled modules) to the pinned set. It adds nothing for the committed
 * selection and fails closed when a pinned file is missing.
 * @param {{ siteRoot: string, env?: NodeJS.ProcessEnv }} options
 * @returns {import('vite').Plugin}
 */
export function atlasArtifactSelectionPlugin({ siteRoot, env = process.env }) {
  const { committedDataDir, dataDir } = resolveSelectedArtifactLocations(siteRoot, env);
  const pinned = isPinnedSelection(env);
  return {
    name: 'atlas-artifact-selection',
    enforce: 'pre',
    buildStart() {
      assertSelectedArtifactsComplete(siteRoot, env);
    },
    resolveId(source, importer) {
      if (!pinned || !importer) return null;
      const [pathPart, ...query] = source.split('?');
      if (!SELECTED_IMPORT_RE.test(pathPart)) return null;
      const importerPath = importer.split('?')[0];
      if (importerPath.startsWith('\0')) return null;
      const absolute = resolve(dirname(importerPath), pathPart);
      if (dirname(absolute) !== committedDataDir) return null;
      const name = absolute.slice(committedDataDir.length + 1);
      const redirected = join(dataDir, name);
      if (!existsSync(redirected)) {
        throw new AtlasArtifactSelectionError(
          `${PINNED_SELECTION_ENV} is set but ${redirected} is missing (import of ${name} from ${importerPath})`,
        );
      }
      return query.length > 0 ? `${redirected}?${query.join('?')}` : redirected;
    },
  };
}
