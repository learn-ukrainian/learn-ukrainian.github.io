import { describe, expect, test } from 'vitest';
import { readFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';

describe('Atlas redirects', () => {
  test('redirects truncated ghost entry проєк to canonical проєкт in astro.config.mjs', () => {
    const configPath = resolve(__dirname, '../../astro.config.mjs');
    expect(existsSync(configPath)).toBe(true);
    const configContent = readFileSync(configPath, 'utf-8');

    // Verify static redirect mappings
    expect(configContent).toContain("'/lexicon/проєк': '/lexicon/проєкт/'");
    expect(configContent).toContain("'/lexicon/%D0%BF%D1%80%D0%BE%D1%94%D0%BA': '/lexicon/проєкт/'");
  });

  test('search index does not contain purged ghost entry проєк', () => {
    const searchIndexPath = resolve(__dirname, '../../src/data/lexicon-search-index.json');
    expect(existsSync(searchIndexPath)).toBe(true);
    const searchIndex = JSON.parse(readFileSync(searchIndexPath, 'utf-8'));
    const ghostEntry = searchIndex.find(
      (entry: { l: string; s: string }) => entry.s === 'проєк' || entry.l === 'проєк',
    );
    expect(ghostEntry).toBeUndefined();

    // Verify canonical entry exists
    const canonicalEntry = searchIndex.find(
      (entry: { l: string; s: string }) => entry.s === 'проєкт' && entry.l === 'проєкт',
    );
    expect(canonicalEntry).toBeDefined();
  });

  test('search aliases resolve proiek and проєк to canonical проєкт', () => {
    const searchAliasesPath = resolve(__dirname, '../../src/data/lexicon-search-aliases.json');
    expect(existsSync(searchAliasesPath)).toBe(true);
    const aliases = JSON.parse(readFileSync(searchAliasesPath, 'utf-8'));

    const proiekAlias = aliases.find((alias: { a: string }) => alias.a === 'proiek');
    expect(proiekAlias).toBeDefined();
    expect(proiekAlias.s).toBe('проєкт');

    const proiekCyrillicAlias = aliases.find((alias: { a: string }) => alias.a === 'проєк');
    expect(proiekCyrillicAlias).toBeDefined();
    expect(proiekCyrillicAlias.s).toBe('проєкт');
  });
});
