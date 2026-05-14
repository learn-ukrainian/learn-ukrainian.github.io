/**
 * Quality gate: every featured slug on the /etymology/ landing page
 * must exist in the build manifest.
 *
 * Background: 2026-05-15 — the landing originally featured 'хата'
 * (transliterated 'khata'), but ESUM has no headword 'хата' (closest
 * real entries are 'хати' / 'хатьма'), so clicking that LinkCard
 * returned 404 in dev mode. This test prevents recurrence by
 * validating every featured slug against the canonical manifest
 * before CI lets the change land.
 */

import { describe, it, expect } from 'vitest';
import { readFileSync } from 'fs';
import { join } from 'path';

const STARLIGHT_DIR = join(__dirname, '..', '..');
const INDEX_ASTRO = join(STARLIGHT_DIR, 'src', 'pages', 'etymology', 'index.astro');
const MANIFEST = join(STARLIGHT_DIR, 'src', 'data', 'etymology-manifest.json');

describe('Etymology featured slugs', () => {
  it('every featured slug in /etymology/ landing exists in the build manifest', () => {
    const src = readFileSync(INDEX_ASTRO, 'utf-8');
    const manifest = JSON.parse(readFileSync(MANIFEST, 'utf-8')) as {
      slug_groups: Record<string, string[]>;
    };

    // Match `slug: 'xxx'` inside the `featured` array. Captures the slug
    // value regardless of single/double quotes.
    const slugMatches = Array.from(src.matchAll(/slug:\s*['"]([^'"]+)['"]/g));
    const slugs = slugMatches.map((m) => m[1]);

    expect(slugs.length).toBeGreaterThanOrEqual(3);

    const missing = slugs.filter((s) => !(s in manifest.slug_groups));
    expect(
      missing,
      `Featured slugs missing from manifest: ${missing.join(', ')}. ` +
        `Verify each slug exists in starlight/src/data/etymology-manifest.json:slug_groups. ` +
        `Regenerate manifest if ESUM data changed: .venv/bin/python scripts/etymology/build_data_manifest.py`,
    ).toEqual([]);
  });
});
