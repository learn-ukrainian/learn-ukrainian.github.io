import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, test } from 'vitest';

describe('CourseLayout CSP & Clickjacking Hardening', () => {
  const layoutPath = resolve(__dirname, '../../src/layouts/CourseLayout.astro');
  const layoutSource = readFileSync(layoutPath, 'utf8');

  test('enforces Content-Security-Policy meta tag with required directives', () => {
    expect(layoutSource).toContain('http-equiv="Content-Security-Policy"');

    // Extract CSP content
    const cspMatch = layoutSource.match(/http-equiv="Content-Security-Policy"\s+content="([^"]+)"/);
    expect(cspMatch).not.toBeNull();
    const cspContent = cspMatch![1];

    // Verify key boundaries
    expect(cspContent).toContain("default-src 'self'");
    expect(cspContent).toContain("object-src 'none'");
    expect(cspContent).toContain("base-uri 'self'");

    // Script sources (must permit GoatCounter, Google Identity, and Astro inline hydration)
    expect(cspContent).toContain("script-src 'self' 'unsafe-inline' https://accounts.google.com/gsi/client");

    // Style sources
    expect(cspContent).toContain("style-src 'self' 'unsafe-inline'");

    // Image sources (must include self, data, GoatCounter, and YouTube thumbnails)
    expect(cspContent).toContain("img-src 'self' data: https://learn-ukrainian.goatcounter.com https://img.youtube.com");

    // Font sources
    expect(cspContent).toContain("font-src 'self' data:");

    // Frame sources for Google Identity popup/iframe and YouTube video embeds
    expect(cspContent).toContain("frame-src https://accounts.google.com https://www.youtube.com https://www.youtube-nocookie.com");

    // Connect sources (GoatCounter, Google APIs for Drive AppData sync)
    expect(cspContent).toContain("connect-src 'self' https://learn-ukrainian.goatcounter.com https://accounts.google.com https://www.googleapis.com");

    // Media sources
    expect(cspContent).toContain("media-src 'self'");
  });

  test('enforces strict-origin-when-cross-origin referrer policy', () => {
    expect(layoutSource).toContain('<meta name="referrer" content="strict-origin-when-cross-origin" />');
  });

  test('includes anti-clickjacking frame-buster style and script pair for GitHub Pages', () => {
    // Assert fail-closed style hides body initially and keeps is:inline attribute
    expect(layoutSource).toContain('<style id="lu-anti-clickjack" is:inline>');
    expect(layoutSource).toContain('display: none !important');

    // Assert script un-hides body only if top === self, and attempts top navigation if framed
    expect(layoutSource).toContain('if (window.top === window.self)');
    expect(layoutSource).toContain("document.getElementById('lu-anti-clickjack')");
    expect(layoutSource).toContain('antiClickjack.parentNode.removeChild(antiClickjack)');
    expect(layoutSource).toContain('window.top.location = window.location.href');
  });
});
