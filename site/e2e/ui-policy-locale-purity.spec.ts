import { expect, test, type Page } from '@playwright/test';

/**
 * #5376 check 1 — locale purity (EN/UK chrome).
 *
 * Policy: the chrome locale toggle (`lu-chrome-locale`) must produce a PURE
 * interface locale. EN mode → zero Cyrillic in interface text; UK mode → zero
 * English chrome. A single label must never mix both scripts ('УКР / ENG'
 * dual-label class, the 2026-07-17 defects).
 *
 * FAIL-CLOSED DESIGN (binding per #5376): every visible text node is chrome
 * unless its element sits under an explicit content-allowlist selector below.
 * An unknown new text region is checked, not skipped — extending the allowlist
 * is a deliberate, reviewed act.
 *
 * ChromeText dual-renders both locales into the DOM and CSS-hides one
 * (`html[data-chrome-locale]`); visibility is resolved via checkVisibility(),
 * so the hidden variant is never inspected.
 */

const CYRILLIC_RE = /[Ѐ-ӿԀ-ԯ]/;

/**
 * Latin tokens tolerated in UK chrome. Fail-closed: a token not listed here
 * fails the check. Level codes, brand names, and technical acronyms only.
 */
const UK_LATIN_TOKEN_ALLOWLIST = new Set([
  'A1', 'A2', 'B1', 'B2', 'C1', 'C2', // CEFR level codes
  'LU', // logo monogram
  'GitHub', // brand
  'API', // technical acronym
  'ULP', // Ukrainian Lessons Podcast brand
  'VESUM', // Ukrainian morphological dictionary acronym (cited in mode descriptions)
]);

/** Selectors excluded on EVERY surface, each with its justification. */
const GLOBAL_CONTENT_ALLOWLIST = [
  '.lu-locale-label', // the toggle displays the TARGET locale name (УКР in EN mode)
  '.lu-logo', // brand wordmark ("Learn Ukrainian", "LU")
  '.lu-footer h2', // footer brand heading ("Learn Ukrainian")
  '.lu-footer a[href^="http"]', // external resources are proper-brand names (Ukrainian Lessons, ULP Podcast)
  '.lu-footer-bottom', // deliberately bilingual motto in both locales
  '.lu-footer p', // authored mission prose; may name Latin-script brands mid-sentence
];

interface Surface {
  path: string;
  /** Authored-content regions (Ukrainian-first by design), per surface. */
  contentAllowlist: string[];
}

const SURFACES: Surface[] = [
  {
    path: '/words-of-the-day/practice/',
    contentAllowlist: [
      '.k3-hero-epigraph', // authored Ukrainian epigraph (lang="uk")
      '[data-testid="practice-daily-deck"]', // words-of-the-day content: lemmas, EN glosses, etymology
      'button[data-zno-deck]', // official ЗНО/НМТ exam section names are Ukrainian content
      '.lexicon-weak-chip', // weak-spot chips render learner vocabulary
    ],
  },
  {
    path: '/lexicon/',
    contentAllowlist: [
      '.atlas-typeahead-landing', // Ukrainian-first dictionary search label/placeholder (hardcoded by design)
      '.atlas-runtime-grid', // technical build metadata: counts, version hashes, API paths
    ],
  },
  {
    path: '/lexicon/browse/',
    contentAllowlist: [
      '.atlas-index', // the A–Z browser is an authored Ukrainian-first immersion surface
    ],
  },
];

interface TextNodeReport {
  text: string;
  path: string;
}

async function collectVisibleText(page: Page, allowlist: string[]): Promise<TextNodeReport[]> {
  return page.evaluate((excludedSelectors) => {
    const skipTags = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
    const out: { text: string; path: string }[] = [];
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let node = walker.nextNode();
    while (node) {
      const el = node.parentElement;
      const text = (node.textContent ?? '').replace(/\s+/g, ' ').trim();
      if (el && text && !skipTags.has(el.tagName)) {
        const visible = el.checkVisibility({ checkOpacity: false, checkVisibilityCSS: true });
        const excluded = el.closest(excludedSelectors.join(',')) !== null;
        if (visible && !excluded) {
          const testid = el.getAttribute('data-testid');
          const cls =
            typeof el.className === 'string' && el.className
              ? `.${el.className.trim().split(/\s+/).join('.')}`
              : '';
          out.push({
            text: text.slice(0, 120),
            path: `${el.tagName.toLowerCase()}${cls}${testid ? `[data-testid="${testid}"]` : ''}`,
          });
        }
      }
      node = walker.nextNode();
    }
    return out;
  }, allowlist);
}

function formatViolations(title: string, violations: TextNodeReport[]): string {
  const lines = violations.map((v) => `  ${v.path}  ::  ${v.text}`);
  return `${title} (${violations.length}):\n${lines.join('\n')}`;
}

for (const surface of SURFACES) {
  for (const locale of ['en', 'uk'] as const) {
    test(`locale purity: ${surface.path} in ${locale.toUpperCase()} chrome`, async ({ page, context }) => {
      await context.clearCookies();
      await page.addInitScript((loc) => window.localStorage.setItem('lu-chrome-locale', loc), locale);
      await page.goto(surface.path);
      await page.waitForLoadState('networkidle');
      // Practice is a React island — wait for it to hydrate before sampling.
      if (surface.path.includes('/practice/')) {
        await expect(page.locator('#lexicon-practice-mount .lexicon-practice')).toBeVisible();
      }

      const nodes = await collectVisibleText(page, [
        ...GLOBAL_CONTENT_ALLOWLIST,
        ...surface.contentAllowlist,
      ]);
      expect(nodes.length, 'sanity: the check must actually inspect visible text').toBeGreaterThan(10);

      const failures: string[] = [];

      const cyrillicHits = nodes.filter((n) => CYRILLIC_RE.test(n.text));
      if (locale === 'en' && cyrillicHits.length > 0) {
        failures.push(formatViolations('EN chrome contains Cyrillic interface text', cyrillicHits));
      }

      if (locale === 'uk') {
        const latinHits = nodes.filter((n) => {
          const tokens = n.text.match(/[A-Za-z][A-Za-z0-9]*/g) ?? [];
          return tokens.some((token) => !UK_LATIN_TOKEN_ALLOWLIST.has(token));
        });
        if (latinHits.length > 0) {
          failures.push(
            formatViolations('UK chrome contains non-allowlisted English interface text', latinHits),
          );
        }
      }

      // Mixed-label trap ('УКР / ENG' class): one visible label must never mix
      // scripts, regardless of locale. Allowlisted Latin tokens (A1, GitHub…)
      // do not count as the Latin side of a mix.
      const mixedHits = nodes.filter((n) => {
        if (!CYRILLIC_RE.test(n.text)) return false;
        const latinWords = (n.text.match(/[A-Za-z][A-Za-z0-9]*/g) ?? []).filter(
          (token) => token.length >= 2 && !UK_LATIN_TOKEN_ALLOWLIST.has(token),
        );
        return latinWords.length > 0;
      });
      if (mixedHits.length > 0) {
        failures.push(formatViolations('single label mixes Cyrillic and Latin scripts', mixedHits));
      }

      expect(failures, failures.join('\n\n')).toEqual([]);
    });
  }
}
