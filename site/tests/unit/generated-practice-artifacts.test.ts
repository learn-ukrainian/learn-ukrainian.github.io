/**
 * Drift guard for the two build-time-derived artifacts introduced by #7671
 * (scripts/generate-teacher-lesson-keys.ts, scripts/generate-zno-deck-meta.ts).
 * Both replace a raw source file's full-content static import in the
 * client-only LexiconPractice island with a small derived file computed at
 * build time. If a source file changes without re-running the generator, the
 * committed derived file silently goes stale — these tests recompute each
 * derivation independently and diff against what is committed.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, test } from 'vitest';
import { filterTeacherClozeItems } from '../../src/lib/lexicon/teacher-cloze-filter';

const ROOT = process.cwd();

function readJson<T>(rel: string): T {
  return JSON.parse(readFileSync(resolve(ROOT, rel), 'utf8')) as T;
}

describe('lexicon-teacher-lesson-keys.json stays in sync with lexicon-teacher-cloze.json (#7671)', () => {
  test('committed key list matches filterTeacherClozeItems applied to the raw source', () => {
    const source = readJson<{ cloze?: Array<{ clozeId: string; lemmaId?: string; lemma?: string }> }>(
      'src/data/lexicon-teacher-cloze.json',
    );
    const expected = Array.from(
      new Set(
        filterTeacherClozeItems(source.cloze ?? [])
          .map((item) => item.lemmaId || item.lemma)
          .filter((key): key is string => Boolean(key)),
      ),
    );
    const committed = readJson<string[]>('src/data/lexicon-teacher-lesson-keys.json');

    expect(committed).toEqual(expected);
    // Sanity bound: guards against an accidentally-empty or truncated regeneration.
    expect(committed.length).toBeGreaterThan(1000);
  });
});

describe('practice-zno-meta.json stays in sync with the practice-zno.*.json decks (#7671)', () => {
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

  test('committed deck meta matches deckId/title/thinDeck/itemCount from each source deck', () => {
    const expected = DECK_SLUGS.map((slug) => {
      const deck = readJson<{ deckId: string; title: string; thinDeck: boolean; items: unknown[] }>(
        `src/data/practice-zno.${slug}.json`,
      );
      return { deckId: deck.deckId, title: deck.title, thinDeck: deck.thinDeck, itemCount: deck.items.length };
    });
    const committed = readJson<typeof expected>('src/data/practice-zno-meta.json');

    expect(committed).toEqual(expected);
  });
});
