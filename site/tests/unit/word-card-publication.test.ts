// @vitest-environment node
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import { afterEach, beforeEach, expect, it } from 'vitest';
import WordCardCanonical from '../../src/lib/lexicon/WordCardCanonical.astro';
import { verifyWordCardBuild } from '../../src/lib/lexicon/word-card-build-proof';
import { canonicalWordCards } from '../../src/lib/lexicon/word-card-publication';
import { candidateId, certifiedId, digest, fixtureRoot, pins } from '../fixtures/word-card-preview/release-controls';

const site = new URL('https://example.test');
const path = `/lexicon/card/${certifiedId}/`;
const candidatePath = `/lexicon/card/${candidateId}/`;
let scratch: string;

beforeEach(() => { scratch = mkdtempSync(join(tmpdir(), 'word-card-publication-')); });
afterEach(() => { rmSync(scratch, { recursive: true }); });

function release() {
  const artifactPath = join(scratch, 'release');
  mkdirSync(artifactPath);
  const dataset = JSON.parse(readFileSync(join(fixtureRoot, 'release-json/word-cards.json'), 'utf8'));
  dataset[0].fields[0].citation.licence_ref.appears_in = ['site'];
  dataset[0].fields[1].citation.licence_ref.appears_in = ['site'];
  dataset[0].fields[2].citation.licence_ref.appears_in = ['dataset'];
  const [sample] = dataset[0].fields;
  for (const [source, attribution, suffix] of [
    ['puls', 'PULS citation above.', 'a'],
    ['vesum', 'VESUM fixture <used version>', 'b'],
  ] as const) {
    dataset[0].fields.push({
      ...sample, assertion_id: `wa_${suffix.padStart(24, '9')}`, field: 'definition_uk', value: `uncited-${source}`,
      citation: { ...sample.citation, source_id: source, attribution,
        licence_ref: { ...sample.citation.licence_ref, register_source_id: source } },
    });
  }
  dataset[0].known_gaps = [{ internal_receipt: 'private-gap-sentinel' }];
  const bytes = JSON.stringify(dataset);
  const manifest = readFileSync(join(fixtureRoot, 'release-json/manifest.json'), 'utf8');
  const manifestBytes = JSON.stringify({ ...JSON.parse(manifest), dataset_bytes: Buffer.byteLength(bytes), dataset_sha256: digest(bytes),
    field_citation_count: dataset[0].fields.length + dataset[1].fields.length });
  writeFileSync(join(artifactPath, 'word-cards.json'), bytes);
  writeFileSync(join(artifactPath, 'manifest.json'), manifestBytes);
  const pin = { ...pins.json, dataset_sha256: digest(bytes), manifest_sha256: digest(manifestBytes),
    provenance: 'producer-declared' as const };
  return { input: { enabled: true, controlled: false, artifactPath }, pin };
}

function sitemap(directory: string, ...paths: string[]) {
  writeFileSync(join(directory, 'sitemap-index.xml'),
    `<sitemapindex><sitemap><loc>${site.href}sitemap-0.xml</loc></sitemap></sitemapindex>`);
  writeFileSync(join(directory, 'sitemap-0.xml'),
    `<urlset>${paths.map(path => `<url><loc>${new URL(path, site).href}</loc></url>`).join('')}</urlset>`);
}

async function builtCard() {
  const { input, pin } = release();
  const cards = canonicalWordCards(input, pin);
  const [card] = cards;
  if (!card) throw Error('Certified fixture was refused');
  const container = await AstroContainer.create({ astroConfig: { site: site.href } });
  const html = await container.renderToString(WordCardCanonical, { props: { card }, request: new Request(new URL(path, site)) });
  const file = join(scratch, path, 'index.html');
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(file, html);
  sitemap(scratch, path);
  return { cards, file, html };
}

it('refuses an uncertified card as a canonical page or sitemap entry', async () => {
  const { cards, file, html } = await builtCard();
  expect(cards.map(({ path, row }) => [path, row.card_id, row.card_version])).toEqual([
    [path, certifiedId, 'cv_fa34b32f0e93bece65b966e8'],
  ]);
  await expect(verifyWordCardBuild(scratch, site, cards)).resolves.toEqual({ canonical: 1, sitemap: 1 });
  sitemap(scratch, path, candidatePath);
  await expect(verifyWordCardBuild(scratch, site, cards)).rejects.toThrow('Word-card sitemap differs from the certified release');
  sitemap(scratch, path);
  const candidateFile = file.replace(certifiedId, candidateId);
  mkdirSync(dirname(candidateFile));
  writeFileSync(candidateFile, html);
  await expect(verifyWordCardBuild(scratch, site, cards)).rejects.toThrow('Canonical word-card output differs from the certified release');
});

it('refuses a certified card when the release bytes mismatch the pin', () => {
  const { input, pin } = release();
  expect(canonicalWordCards(input, pin)).toHaveLength(1);
  const file = join(input.artifactPath, 'word-cards.json');
  const data = readFileSync(file, 'utf8');
  const changed = data.replace('cv_fa34b32f0e93bece65b966e8', 'cv_000000000000000000000000');
  writeFileSync(file, changed);
  expect(canonicalWordCards(input, pin)).toEqual([]);

  const manifestPath = join(input.artifactPath, 'manifest.json');
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  const dataset_sha256 = digest(changed);
  const manifestBytes = JSON.stringify({ ...manifest, dataset_sha256 });
  writeFileSync(manifestPath, manifestBytes);
  const differentPin = JSON.stringify({ ...pin, dataset_sha256, manifest_sha256: digest(manifestBytes) });
  expect(canonicalWordCards({ ...input, pin: differentPin }, pin)).toEqual([]);
});

it('fails the build proof when a rendered value differs from its release source', async () => {
  const { cards, file, html } = await builtCard();
  expect(html).toContain('permitted-definition');
  expect(html).toContain('Synthetic ulif edition');
  expect(html).toContain('Release assertions without site scope (1)');
  expect(html).toContain('Release assertions with incomplete attribution (2)');
  expect(html).not.toMatch(/parallel-definition|private-gap-sentinel|ulif:row:|PULS citation above|used version|uncited-/);
  await expect(verifyWordCardBuild(scratch, site, cards)).resolves.toEqual({ canonical: 1, sitemap: 1 });
  writeFileSync(file, html.replace('permitted-definition', 'altered definition'));
  await expect(verifyWordCardBuild(scratch, site, cards)).rejects.toThrow('Word-card assertions or provenance differ from the release');
});
