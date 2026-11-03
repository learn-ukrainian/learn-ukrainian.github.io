// @vitest-environment node

/**
 * #12527 defect class: pinned-mode build output written into (or read from) the
 * committed artifact paths. The pinned set lives in the ignored site/.atlas-pinned/
 * and every reader must follow the one shared selection, with deliberately
 * different committed and pinned contents so a reader on the wrong set is visible.
 */

import { existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { build } from 'vite';
import { afterEach, describe, expect, it } from 'vitest';
import {
  AtlasArtifactSelectionError,
  PINNED_SELECTION_ENV,
  SELECTED_ARTIFACT_NAMES,
  assertSelectedArtifactsComplete,
  atlasArtifactSelectionPlugin,
  installSelectedBrowseShards,
  readSelectedArtifactText,
  resolveSelectedArtifactLocations,
} from '../../src/lib/lexicon/atlas-artifact-selection.mjs';
import { writeSearchShardFiles } from '../../src/lib/lexicon/search-api-shard';

const PINNED_ENV = { [PINNED_SELECTION_ENV]: '/runtime/tree' } as NodeJS.ProcessEnv;
const COMMITTED_ENV = {} as NodeJS.ProcessEnv;
const fixtures: string[] = [];

function write(path: string, text: string): void {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, text);
}

/** A site root holding a committed snapshot and, optionally, a pinned set with different bytes. */
function makeSite(options: { pinned: boolean }): string {
  const root = mkdtempSync(join(tmpdir(), 'atlas-selection-'));
  fixtures.push(root);
  const meta = (tag: string, letters: string[]) =>
    JSON.stringify({
      total: letters.length,
      usageSources: { records: { [`${tag}-sentinel`]: { digest: tag } } },
      browseShards: Object.fromEntries(letters.map((letter) => [letter, { path: `/lexicon/browse/${letter}.json` }])),
    });
  for (const name of SELECTED_ARTIFACT_NAMES) {
    write(join(root, 'src/data', name), name === 'lexicon-browse-meta.json' ? meta('COMMITTED', ['А', 'Б']) : `"COMMITTED ${name}"`);
  }
  write(join(root, 'public/lexicon/browse/А.json'), '"COMMITTED А"');
  write(join(root, 'public/lexicon/browse/Б.json'), '"COMMITTED Б"');
  if (options.pinned) {
    for (const name of SELECTED_ARTIFACT_NAMES) {
      write(join(root, '.atlas-pinned/data', name), name === 'lexicon-browse-meta.json' ? meta('PINNED', ['А']) : `"PINNED ${name}"`);
    }
    write(join(root, '.atlas-pinned/public/lexicon/browse/А.json'), '"PINNED А"');
  }
  return root;
}

afterEach(() => {
  for (const root of fixtures.splice(0)) rmSync(root, { recursive: true, force: true });
});

describe('shared Atlas artifact selection (#12527)', () => {
  it('reads the committed snapshot unpinned and the ignored pinned set when pinned, never the other', () => {
    const root = makeSite({ pinned: true });
    expect(resolveSelectedArtifactLocations(root, COMMITTED_ENV).mode).toBe('committed');
    expect(readSelectedArtifactText('lexicon-search-index.json', root, COMMITTED_ENV)).toBe(
      '"COMMITTED lexicon-search-index.json"',
    );
    expect(resolveSelectedArtifactLocations(root, PINNED_ENV).mode).toBe('pinned');
    expect(readSelectedArtifactText('lexicon-search-index.json', root, PINNED_ENV)).toBe(
      '"PINNED lexicon-search-index.json"',
    );
    // A blank variable is not a pin.
    expect(resolveSelectedArtifactLocations(root, { [PINNED_SELECTION_ENV]: '  ' }).mode).toBe('committed');
  });

  it('fails closed when the pinned set is missing, incomplete or stale; never falls back to committed files', () => {
    const missing = makeSite({ pinned: false });
    expect(() => readSelectedArtifactText('lexicon-search-index.json', missing, PINNED_ENV)).toThrow(
      AtlasArtifactSelectionError,
    );
    expect(() => assertSelectedArtifactsComplete(missing, PINNED_ENV)).toThrow(/lacks/);
    expect(() => assertSelectedArtifactsComplete(missing, COMMITTED_ENV)).not.toThrow();

    const site = makeSite({ pinned: true });
    expect(() => assertSelectedArtifactsComplete(site, PINNED_ENV)).not.toThrow();
    write(join(site, '.atlas-pinned/public/lexicon/browse/Я.json'), '"STALE"');
    expect(() => assertSelectedArtifactsComplete(site, PINNED_ENV)).toThrow(/stale: Я\.json/);
    rmSync(join(site, '.atlas-pinned/public/lexicon/browse/Я.json'));
    rmSync(join(site, '.atlas-pinned/public/lexicon/browse/А.json'));
    expect(() => assertSelectedArtifactsComplete(site, PINNED_ENV)).toThrow(/missing: А\.json/);
  });

  it('installs only the pinned browse shards into dist and leaves committed files untouched', () => {
    const site = makeSite({ pinned: true });
    const dist = join(site, 'dist');
    // public/ copied the committed shards, including one the pinned set no longer has.
    write(join(dist, 'lexicon/browse/А.json'), '"COMMITTED А"');
    write(join(dist, 'lexicon/browse/Б.json'), '"COMMITTED Б"');
    // The same directory holds the prerendered browse page, which the Atlas vendor step requires.
    write(join(dist, 'lexicon/browse/index.html'), '<h1>browse</h1>');

    installSelectedBrowseShards(dist, site, COMMITTED_ENV);
    expect(readdirSync(join(dist, 'lexicon/browse')).sort()).toEqual(['index.html', 'А.json', 'Б.json']);

    installSelectedBrowseShards(dist, site, PINNED_ENV);
    expect(readdirSync(join(dist, 'lexicon/browse')).sort()).toEqual(['index.html', 'А.json']);
    expect(readFileSync(join(dist, 'lexicon/browse/index.html'), 'utf8')).toBe('<h1>browse</h1>');
    expect(readFileSync(join(dist, 'lexicon/browse/А.json'), 'utf8')).toBe('"PINNED А"');
    expect(readFileSync(join(site, 'public/lexicon/browse/А.json'), 'utf8')).toBe('"COMMITTED А"');
    expect(existsSync(join(site, 'public/lexicon/browse/Б.json'))).toBe(true);
  });

  it('redirects the Vite JSON import of a client-bundled module (heritage-severity) to the selected set', async () => {
    const site = makeSite({ pinned: true });
    // heritage-severity.ts is bundled into the client; it statically imports ../../data/lexicon-browse-meta.json.
    write(
      join(site, 'src/lib/lexicon/heritage-severity.ts'),
      readFileSync(resolve(__dirname, '../../src/lib/lexicon/heritage-severity.ts'), 'utf8'),
    );
    async function bundle(root: string, env: NodeJS.ProcessEnv): Promise<string> {
      const result = await build({
        root,
        configFile: false,
        logLevel: 'silent',
        plugins: [atlasArtifactSelectionPlugin({ siteRoot: root, env })],
        build: {
          write: false,
          minify: false,
          lib: { entry: 'src/lib/lexicon/heritage-severity.ts', formats: ['es'], fileName: 'out' },
        },
      });
      const outputs = (Array.isArray(result) ? result : [result]) as Array<{
        output: Array<{ type: string; code?: string }>;
      }>;
      return outputs.flatMap((o) => o.output.map((chunk) => chunk.code ?? '')).join('\n');
    }

    const committed = await bundle(site, COMMITTED_ENV);
    expect(committed).toContain('COMMITTED-sentinel');
    expect(committed).not.toContain('PINNED-sentinel');

    const pinned = await bundle(site, PINNED_ENV);
    expect(pinned).toContain('PINNED-sentinel');
    expect(pinned).not.toContain('COMMITTED-sentinel');

    // Pinned and incomplete: the build fails instead of bundling the committed file.
    rmSync(join(site, '.atlas-pinned/data/lexicon-browse-meta.json'));
    await expect(bundle(site, PINNED_ENV)).rejects.toThrow(/lacks: lexicon-browse-meta\.json/);
  });

  it('hydrates search shards from the selected set (plain Node import) and drops stale shards', () => {
    const site = makeSite({ pinned: true });
    const row = (slug: string) => ({ l: slug, s: slug, g: '', r: slug, t: 'lemma' });
    const shards = (tag: string) =>
      JSON.stringify({ prefixMap: { [tag.slice(0, 1)]: tag }, shards: { [tag]: { count: 1 } } });
    write(join(site, 'src/data/lexicon-search-index.json'), JSON.stringify([row('committed')]));
    write(join(site, 'src/data/lexicon-search-shards.json'), shards('committed'));
    write(join(site, '.atlas-pinned/data/lexicon-search-index.json'), JSON.stringify([row('pinned')]));
    write(join(site, '.atlas-pinned/data/lexicon-search-shards.json'), shards('pinned'));
    write(join(site, 'public/lexicon/search/earlier-run.json'), '[]');

    const previous = process.env[PINNED_SELECTION_ENV];
    process.env[PINNED_SELECTION_ENV] = '/runtime/tree';
    try {
      expect(() => writeSearchShardFiles(site)).not.toThrow();
    } finally {
      if (previous === undefined) delete process.env[PINNED_SELECTION_ENV];
      else process.env[PINNED_SELECTION_ENV] = previous;
    }
    expect(readdirSync(join(site, 'public/lexicon/search'))).toEqual(['pinned.json']);
    expect(readFileSync(join(site, 'public/lexicon/search/pinned.json'), 'utf8')).toContain('"pinned"');
  });
});
