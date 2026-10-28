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

  test('renders visibly by default and hides the page only when framed', () => {
    // No static rule hides the body: script-disabled top-level readers must see the page.
    expect(layoutSource).not.toContain('<style id="lu-anti-clickjack"');
    expect(layoutSource).not.toContain('<noscript');

    const script = layoutSource.match(/<script is:inline>\s*(if \(window\.top !== window\.self\)[\s\S]*?)<\/script>/);
    expect(script).not.toBeNull();

    const run = (framed: boolean, navigationDenied = false) => {
      const appended: Array<{ id: string; textContent: string }> = [];
      const self = {} as { self: unknown; top: unknown; location: unknown };
      self.self = self;
      const top = {} as { location: unknown };
      Object.defineProperty(top, 'location', {
        set(value) {
          if (navigationDenied) throw new Error('SecurityError');
          navigated.push(value);
        },
      });
      const navigated: unknown[] = [];
      self.top = framed ? top : self;
      self.location = { href: 'https://learn-ukrainian.github.io/a1/' };
      const document = {
        createElement: () => ({ id: '', textContent: '' }),
        head: { appendChild: (node: { id: string; textContent: string }) => appended.push(node) },
      };
      new Function('window', 'document', script![1])(self, document);
      return { appended, navigated };
    };

    const topLevel = run(false);
    expect(topLevel.appended).toHaveLength(0);
    expect(topLevel.navigated).toHaveLength(0);

    const framed = run(true);
    expect(framed.appended).toHaveLength(1);
    expect(framed.appended[0].id).toBe('lu-anti-clickjack');
    expect(framed.appended[0].textContent).toContain('display: none !important');
    expect(framed.navigated).toEqual(['https://learn-ukrainian.github.io/a1/']);

    // Navigation denied (sandboxed frame): the page stays hidden and nothing throws.
    const denied = run(true, true);
    expect(denied.appended).toHaveLength(1);
  });
});
