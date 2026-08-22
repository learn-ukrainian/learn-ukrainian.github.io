/**
 * Quality gate: /etymology/ must no longer advertise a fake ESUM catalog
 * or prerender standalone lemma demo pages (#7059).
 *
 * Learners looking for etymology are redirected to Word Atlas (/lexicon/).
 * Standalone /etymology/[slug].astro dynamic routes are removed so thousands
 * of HTML pages (or 4 fake demo pages) are never prerendered.
 */

import { describe, it, expect } from 'vitest';
import { existsSync, readFileSync } from 'fs';
import { join } from 'path';

const SITE_DIR = join(__dirname, '..', '..');
const INDEX_ASTRO = join(SITE_DIR, 'src', 'pages', 'etymology', 'index.astro');
const SLUG_ASTRO = join(SITE_DIR, 'src', 'pages', 'etymology', '[slug].astro');

describe('Etymology catalog retirement (#7059)', () => {
  it('/etymology/index.astro is a redirect/moved page to Word Atlas (/lexicon/)', () => {
    expect(existsSync(INDEX_ASTRO)).toBe(true);
    const src = readFileSync(INDEX_ASTRO, 'utf-8');

    // Points to /lexicon/
    expect(src).toContain('/lexicon/');

    // Does not import manifest for route generation or stats
    expect(src).not.toContain('etymology-manifest.json');

    // Does not contain the old featured demo slug array
    expect(src).not.toContain("slug: 'dim'");
    expect(src).not.toContain("slug: 'voda'");

    // Does not claim tens of thousands of articles
    expect(src).not.toContain('36');
    expect(src).not.toContain('total_entries');
  });

  it('standalone dynamic routes /etymology/[slug].astro are deleted', () => {
    expect(existsSync(SLUG_ASTRO)).toBe(false);
  });
});
