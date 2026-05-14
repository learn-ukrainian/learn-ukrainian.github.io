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
  // defaults to 5000ms, which is far shorter than an Astro build.
  // Without an explicit override the test hits vitest's SIGTERM before
  // `execSync` even returns, so the timeout inside execSync never gets
  // a chance to fire. Match the external timeout to keep the outer
  // bound consistent.
  //
  // Build scope: ~22 base pages + 31,336 etymology dynamic-route pages
  // (PR #1998, /etymology/[slug].astro). Local 8GB heap on M-series:
  // ~56s. CI runner (Ubuntu x86, slower per-core): allow 4 min, with
  // 5 min vitest outer bound. Bump these if etymology corpus grows
  // significantly.
  it('astro build succeeds with zero errors', () => {
    try {
      buildOutput = execSync('npm run build 2>&1', {
        cwd: STARLIGHT_DIR,
        timeout: 240000,
        encoding: 'utf-8',
        maxBuffer: 50 * 1024 * 1024, // 50MB: full build output for 31k pages exceeds default 1MB
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
  }, 300000);

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
    if (!existsSync(weatherPage)) {
      // Module page deleted by #1577 Phase 1 Q3 curriculum reboot.
      // Test self-restores when the a1/weather module is rebuilt and
      // produces a Starlight build output. Same self-skip pattern that
      // f0635c70ad applied to test_a1_1_sounds_letters_golden.
      return;
    }

    const html = readFileSync(weatherPage, 'utf-8');

    expect(html).not.toContain('starlight-tab-item');
    expect((html.match(/role="tab"/g) || []).length).toBeGreaterThan(0);
    expect((html.match(/role="tabpanel"/g) || []).length).toBeGreaterThan(0);
  });
});
