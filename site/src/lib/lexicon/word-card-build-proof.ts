import { deepStrictEqual } from 'node:assert/strict';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { AstroIntegration } from 'astro';
import { Window, type Document, type Element } from 'happy-dom';
import { canonicalWordCardBuildInput, canonicalWordCards, wordCardRoute, type CanonicalWordCard } from './word-card-publication.ts';
import { attributionGap } from './word-card-release.ts';

function children(element: Element, tags: string[]) {
  const elements = Array.from(element.children);
  deepStrictEqual(elements.map(child => child.localName), tags, `Unexpected elements in ${element.localName}`);
  deepStrictEqual(Array.from(element.childNodes).filter(node => node.nodeType === 3 && node.textContent?.trim()), [],
    `Unexpected text in ${element.localName}`);
  return elements;
}

function text(element: Element) {
  deepStrictEqual(element.childElementCount, 0, `Expected plain text in ${element.localName}`);
  return element.textContent;
}

/** Compare the learner DOM with the authenticated release row, independently of the renderer. */
function verifyCard(document: Document, card: CanonicalWordCard, url: string) {
  const { row } = card;
  deepStrictEqual(Array.from(document.querySelectorAll('link[rel~="canonical"]'), link => link.getAttribute('href')), [url]);
  deepStrictEqual(document.querySelectorAll('meta[name="robots" i], meta[name="googlebot" i]').length, 0);
  const articles = document.querySelectorAll('article[data-word-card]');
  deepStrictEqual(articles.length, 1);
  const article = articles.item(0);
  if (!article) throw Error('Missing word-card article');
  deepStrictEqual(article.getAttribute('data-word-card'), row.card_id);
  deepStrictEqual(article.getAttribute('data-card-version'), row.card_version);

  const siteAssertions = row.fields.filter(({ citation }) => citation.licence_ref.appears_in?.includes('site'));
  const publicAssertions = siteAssertions.filter(({ citation }) => attributionGap(citation) === null);
  const noSiteScope = row.fields.length - siteAssertions.length;
  const incompleteAttribution = siteAssertions.length - publicAssertions.length;
  const gaps = row.known_gaps.length;
  const expectedNotices = [
    ...(noSiteScope ? [['site', `Release assertions without site scope (${noSiteScope})`]] : []),
    ...(incompleteAttribution ? [['attribution', `Release assertions with incomplete attribution (${incompleteAttribution})`]] : []),
    ...(gaps ? [['gap', `Declared release gaps (${gaps})`]] : []),
  ];
  const parts = children(article, ['h1', 'dl', ...expectedNotices.map(() => 'p')]);
  const [heading, list, ...notices] = parts;
  if (!heading || !list) throw Error('Missing card heading or assertions');
  const headwords = new Set(publicAssertions.flatMap(assertion => {
    const expectedField = row.card_kind === 'mwe' ? 'mwe_form' : 'spelling';
    if (assertion.field !== expectedField || assertion.subject.kind !== 'card' || typeof assertion.value !== 'string') return [];
    return [assertion.value];
  }));
  const firstWord = headwords.values().next().value;
  const expectedHeading = headwords.size === 1 && firstWord?.trim() ? firstWord : row.card_id;
  deepStrictEqual(text(heading), expectedHeading, 'Word-card heading');
  deepStrictEqual(document.querySelector('title')?.textContent, `${expectedHeading} · Learn Ukrainian`, 'Word-card title');

  const actual = children(list, publicAssertions.map(() => 'div')).map(element => {
    const [label, detail] = children(element, ['dt', 'dd']);
    if (!label || !detail) throw Error('Missing assertion label or detail');
    const [value, credit] = children(detail, ['div', 'div']);
    if (!value || !credit) throw Error('Missing assertion value or credit');
    return [
      element.getAttribute('data-assertion'), element.getAttribute('data-subject-kind'), element.getAttribute('data-subject-id'),
      text(label), text(value), children(credit, ['span', 'span', 'span']).map(text),
    ];
  });
  deepStrictEqual(actual, publicAssertions.map(assertion => [
    assertion.assertion_id, assertion.subject.kind, assertion.subject.id, assertion.field.split('_').join(' '),
    typeof assertion.value === 'string' ? assertion.value : JSON.stringify(assertion.value, null, 2),
    [assertion.citation.source_id, assertion.citation.attribution, assertion.citation.licence.name],
  ]), 'Word-card assertions or provenance differ from the release');
  deepStrictEqual(notices.map(notice => [notice.getAttribute('data-excluded'), text(notice)]), expectedNotices,
    'Word-card exclusion counts differ from the release');
}

/** Check the complete built route and sitemap populations, then replay each page against its source. */
export async function verifyWordCardBuild(directory: string, site: URL, cards: readonly CanonicalWordCard[]) {
  const pagesDirectory = join(directory, wordCardRoute);
  const actualPages = existsSync(pagesDirectory)
    ? readdirSync(pagesDirectory, { recursive: true }).filter(file => file.endsWith('.html'))
    : [];
  const expectedPages = cards.map(card => `${card.row.card_id}/index.html`);
  deepStrictEqual(actualPages.sort(), expectedPages.sort(), 'Canonical word-card output differs from the certified release');

  const window = new Window({ settings: {
    disableJavaScriptEvaluation: true, disableJavaScriptFileLoading: true, disableCSSFileLoading: true,
    disableIframePageLoading: true,
  } });
  const parser = new window.DOMParser();
  try {
    const locations = (file: string, selector: string) => Array.from(parser.parseFromString(
      readFileSync(join(directory, file), 'utf8'), 'application/xml',
    ).querySelectorAll(selector), node => new URL(node.textContent ?? ''));
    const sitemapUrls: string[] = [];
    const index = join(directory, 'sitemap-index.xml');
    const listedFiles = existsSync(index) ? locations('sitemap-index.xml', 'sitemap > loc').map(url => url.href) : [];
    for (const file of readdirSync(directory).filter(name => /^sitemap-\d+\.xml$/.test(name))) {
      for (const url of locations(file, 'url > loc')) {
        const path = decodeURIComponent(url.pathname);
        if (path === '/lexicon-v2' || path.startsWith('/lexicon-v2/')) {
          throw Error('Word-card preview URL in sitemap');
        }
        if (!path.startsWith(wordCardRoute) && path !== wordCardRoute.slice(0, -1)) continue;
        deepStrictEqual(listedFiles.filter(href => href === new URL(file, site).href).length, 1,
          'Word-card sitemap chunk must appear once in the sitemap index');
        sitemapUrls.push(url.href);
      }
    }
    deepStrictEqual(sitemapUrls.sort(), cards.map(card => new URL(card.path, site).href).sort(),
      'Word-card sitemap differs from the certified release');

    for (const card of cards) {
      try {
        const document = parser.parseFromString(readFileSync(join(directory, card.path, 'index.html'), 'utf8'), 'text/html');
        verifyCard(document, card, new URL(card.path, site).href);
      } catch (cause) {
        throw Error(`Word-card HTML differs from release for ${card.row.card_id} at ${card.row.card_version}: ${cause instanceof Error ? cause.message.split('\n')[0] : 'DOM proof failed'}`);
      }
    }
    return { canonical: actualPages.length, sitemap: sitemapUrls.length };
  } finally {
    await window.happyDOM.close();
  }
}

/** Register after @astrojs/sitemap so the proof checks the files the build will ship. */
export function wordCardPublication(): AstroIntegration {
  let site: string | undefined;
  return {
    name: 'atlas-word-card-publication',
    hooks: {
      'astro:config:setup': ({ injectRoute }) => {
        injectRoute({ pattern: `${wordCardRoute}[id]`, entrypoint: new URL('./WordCardCanonical.astro', import.meta.url) });
      },
      'astro:config:done': ({ config }) => { site = config.site; },
      'astro:build:done': async ({ dir, logger }) => {
        if (!site) throw Error('Word-card proof requires the Astro site URL');
        const cards = canonicalWordCards(canonicalWordCardBuildInput());
        const counts = await verifyWordCardBuild(fileURLToPath(dir), new URL(site), cards);
        logger.info(`${counts.canonical} canonical word-card pages, ${counts.sitemap} word-card sitemap entries`);
      },
    },
  };
}
