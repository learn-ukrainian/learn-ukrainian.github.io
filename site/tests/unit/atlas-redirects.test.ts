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
});
