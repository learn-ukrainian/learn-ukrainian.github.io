/**
 * Quality gate: verify all content pages render without errors.
 *
 * Catches:
 * - UnknownContentCollectionError (bad frontmatter)
 * - Component import failures
 * - MDX rendering errors (malformed JSX, missing props)
 * - React SSR crashes (undefined props, missing data)
 *
 * Runs `astro build` and checks:
 * 1. Exit code 0 (no fatal errors)
 * 2. No "[ERROR]" lines in output
 * 3. All expected pages generated
 */

import { describe, it, expect } from 'vitest';
import { execSync } from 'child_process';
import { readdirSync, existsSync, readFileSync } from 'fs';
import { join } from 'path';

const STARLIGHT_DIR = join(__dirname, '..', '..');

describe('Astro build renders all pages', () => {
  let buildOutput: string;
  let buildExitCode: number;

  // Run build once for all tests.
  //
  // IMPORTANT: the third arg to `it()` is the test timeout. vitest
  // defaults to 5000ms, which is far shorter than an Astro build (~15s
  // on this repo). Without an explicit override the test hits vitest's
  // SIGTERM before `execSync` even returns, so the `timeout: 60000`
  // option inside execSync never gets a chance to fire. Match the
  // external timeout to keep the outer bound consistent.
  it('astro build succeeds with zero errors', () => {
    try {
      buildOutput = execSync('npm run build 2>&1', {
        cwd: STARLIGHT_DIR,
        timeout: 60000,
        encoding: 'utf-8',
      });
      buildExitCode = 0;
    } catch (e: any) {
      buildOutput = e.stdout || e.message;
      buildExitCode = e.status || 1;
    }

    // Must exit 0
    expect(buildExitCode).toBe(0);

    // No [ERROR] lines
    const errorLines = buildOutput
      .split('\n')
      .filter(line => line.includes('[ERROR]'));
    expect(errorLines).toEqual([]);
  }, 120000);

  it('generates expected page count', () => {
    const distDir = join(STARLIGHT_DIR, 'dist');
    if (!existsSync(distDir)) return; // skip if build didn't run

    // Count HTML files recursively
    function countHtml(dir: string): number {
      let count = 0;
      for (const entry of readdirSync(dir, { withFileTypes: true })) {
        if (entry.isDirectory()) {
          count += countHtml(join(dir, entry.name));
        } else if (entry.name.endsWith('.html')) {
          count++;
        }
      }
      return count;
    }

    const pageCount = countHtml(distDir);
    // Should have at least homepage + 404 + a1 module + level indexes
    expect(pageCount).toBeGreaterThanOrEqual(10);
  });

  it('no pages have rendering errors in output', () => {
    if (!buildOutput) return;

    // Check for common error patterns
    const errorPatterns = [
      /Caught error rendering/,
      /Cannot read properties of undefined/,
      /UnknownContentCollectionError/,
      /is not a function/,
      /Module not found/,
    ];

    for (const pattern of errorPatterns) {
      const matches = buildOutput.match(pattern);
      expect(matches, `Build output contains: ${pattern}`).toBeNull();
    }
  });

  it('renders Starlight tabs for module pages instead of raw tab markers', () => {
    const weatherPage = join(STARLIGHT_DIR, 'dist', 'a1', 'weather', 'index.html');
    expect(existsSync(weatherPage)).toBe(true);

    const html = readFileSync(weatherPage, 'utf-8');

    expect(html).not.toContain('starlight-tab-item');
    expect((html.match(/role="tab"/g) || []).length).toBeGreaterThan(0);
    expect((html.match(/role="tabpanel"/g) || []).length).toBeGreaterThan(0);
  });
});
