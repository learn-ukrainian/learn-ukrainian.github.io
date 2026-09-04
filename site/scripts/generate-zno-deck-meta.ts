/**
 * Build-time metadata extraction for the ZNO/NMT practice deck picker (#7671).
 *
 * The nine `src/data/practice-zno.*.json` files (~688KB combined) hold the full
 * task content for every deck. `ZnoPractice.tsx` used to statically import all
 * nine just to render the picker grid (deck title, thin-deck note, item count)
 * on the practice hub home screen — that bundled every deck's full content into
 * the client-only LexiconPractice island even for a learner who never opens
 * ZNO practice. The picker only ever reads `deckId`/`title`/`thinDeck`/item
 * count, so this script derives that small metadata array at build time; the
 * full per-deck content loads on demand via ZnoPractice.tsx's dynamic imports,
 * one chunk per deck, only when a learner actually opens it.
 *
 * Re-run whenever a practice-zno.*.json source file changes (wired into
 * `npm run hydrate`).
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = dirname(fileURLToPath(import.meta.url));
const dataDir = resolve(scriptDir, '../src/data');
const outPath = resolve(dataDir, 'practice-zno-meta.json');

// Order matches the picker's historical render order (ZnoPractice.tsx's old
// ZNO_PRACTICE_DECKS array), which is also useZnoPracticeOverlay.ts's
// ZNO_MODE_META key order.
const DECK_SLUGS = [
  'stress',
  'paronym',
  'lexical-norm',
  'morphological-norm',
  'syntactic-norm',
  'orthography',
  'morphology',
  'syntax',
  'phonetics',
];

interface ZnoDeckSource {
  deckId: string;
  title: string;
  thinDeck: boolean;
  items: unknown[];
}

interface ZnoDeckMeta {
  deckId: string;
  title: string;
  thinDeck: boolean;
  itemCount: number;
}

function generate(): void {
  const meta: ZnoDeckMeta[] = DECK_SLUGS.map((slug) => {
    const source = JSON.parse(
      readFileSync(resolve(dataDir, `practice-zno.${slug}.json`), 'utf8'),
    ) as ZnoDeckSource;
    return {
      deckId: source.deckId,
      title: source.title,
      thinDeck: source.thinDeck,
      itemCount: source.items.length,
    };
  });
  writeFileSync(outPath, `${JSON.stringify(meta)}\n`);
  console.log(`✓ ${meta.length} ZNO deck meta entries -> ${outPath}`);
}

generate();
