/**
 * Practice first paint (#6715).
 *
 * `/words-of-the-day/practice/` mounts LexiconPractice with client:only, so
 * without an SSR shell the <main> is empty until the bundle downloads and
 * hydrates. The mount must ship a visible static shell, and the inline script
 * must hide it on both the success (hydrated content) and fallback paths.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, test } from 'vitest';

const ROOT = process.cwd();

function readSrc(rel: string): string {
  return readFileSync(resolve(ROOT, rel), 'utf8');
}

describe('practice first-paint shell (#6715)', () => {
  const src = readSrc('src/lexicon/LexiconPracticeMount.astro');

  test('mount contains a visible (non-hidden) status shell before the island', () => {
    const mountStart = src.indexOf('id="lexicon-practice-mount"');
    const islandStart = src.indexOf('client:only="react"');
    expect(mountStart).toBeGreaterThan(-1);
    expect(islandStart).toBeGreaterThan(-1);

    const preIsland = src.slice(mountStart, islandStart);
    expect(preIsland).toContain('id="lexicon-practice-shell"');
    expect(preIsland).toContain('role="status"');
    expect(preIsland).toContain('aria-busy="true"');
    // Visible at first paint: the shell itself must not start hidden.
    const shellTag = preIsland.slice(
      preIsland.indexOf('id="lexicon-practice-shell"'),
      preIsland.indexOf('>', preIsland.indexOf('id="lexicon-practice-shell"')),
    );
    expect(shellTag).not.toContain('hidden');
    expect(preIsland).toContain('lexicon-practice-skel-line');
    expect(preIsland).toContain('Завантаження практики…');
  });

  test('inline script hides the shell on success and on fallback', () => {
    expect(src).toContain("const SHELL_ID = 'lexicon-practice-shell';");
    expect(src).toMatch(/function hideShell\(\)[\s\S]{0,200}setAttribute\('hidden', ''\)/);
    expect(src).toMatch(/function markSuccess\(\)[\s\S]{0,150}hideShell\(\)/);
    expect(src).toMatch(/function showFallback\(\)[\s\S]{0,300}hideShell\(\)/);
  });

  test('fallback remains hidden at first paint; shell hides via [hidden] rule', () => {
    expect(src).toMatch(/id="lexicon-practice-fallback"[^>]*hidden/);
    expect(src).toContain('.lexicon-practice-shell[hidden]');
  });
});
