new Crawler({
  appId: 'MFWOKG2YFD',
  apiKey: 'YOUR_ADMIN_API_KEY', // CRITICAL: Use your Algolia Admin API Key here (NOT the Search Key)
  rateLimit: 8,
  startUrls: ['https://learn-ukrainian.github.io/'],
  renderJavaScript: false,
  sitemaps: ['https://learn-ukrainian.github.io/sitemap.xml'],
  ignoreCanonicalTo: true,
  discoveryPatterns: ['https://learn-ukrainian.github.io/**'],
  schedule: 'at 02:00 every 1 day',
  actions: [
    {
      indexName: 'https_learn_ukrainian_github_io_pages',
      pathsToMatch: ['https://learn-ukrainian.github.io/**'],
      recordExtractor: ({ $, helpers }) => {
        // Priority order for hierarchy extraction
        const lvl0 =
          $('.menu__link.menu__link--sublist.menu__link--active').text() ||
          $('.navbar__item.navbar__link--active').text() ||
          'Documentation';

        const records = helpers.docsearch({
          recordProps: {
            lvl0: {
              selectors: '',
              defaultValue: lvl0,
            },
            lvl1: ['header h1', 'article h1'],
            lvl2: 'article h2',
            lvl3: 'article h3',
            lvl4: 'article h4',
            lvl5: 'article h5, article td:first-child',
            // - .theme-admonition > div:first-child: Splits Callout/Admonition titles
            // - dt: Splits Definition Lists
            // - blockquote: Splits large quotes
            // - tr: Splits Table Rows (CRITICAL for vocab lists)
            // - li: Splits List Items
            // - pre: Splits Code Blocks
            // - p: Splits Paragraphs (CRITICAL for long texts)
            lvl6: [
              'article h6', 
              'article .theme-admonition > div:first-child', 
              'article dt', 
              'article blockquote',
              'article tr',
              'article li',
              'article pre',
              'article p'
            ],
            content: 'article p, article li, article td:last-child',
          },
          indexHeadings: true,
          // Re-enable aggregation to prevent "Too many records" error
          // The enhanced lvl6 selectors above will prevent "Record too big" error
          aggregateContent: true,
          recordVersion: 'v3',
        });

        // Post-processing: Detect Ukrainian content and override language
        // This is critical because Docusaurus sets lang="en" globally
        records.forEach(record => {
          // Check if Title (lvl1) or Header (lvl2) contains Cyrillic characters
          if (/[а-яА-ЯґҐєЄіІїЇ]/.test(record.hierarchy.lvl1) || /[а-яА-ЯґҐєЄіІїЇ]/.test(record.hierarchy.lvl2)) {
            record.lang = 'uk';
            record.language = 'uk';
          }
        });

        return records;
      },
    },
  ],
  initialIndexSettings: {
    https_learn_ukrainian_github_io_pages: {
      attributesForFaceting: [
        'type',
        'lang',
        'language',
        'version',
        'docusaurus_tag',
      ],
      attributesToRetrieve: [
        'hierarchy',
        'content',
        'anchor',
        'url',
        'url_without_anchor',
        'type',
      ],
      attributesToHighlight: ['hierarchy', 'hierarchy_camel', 'content'],
      attributesToSnippet: ['content:10'],
      camelCaseAttributes: ['hierarchy', 'hierarchy_radio', 'content'],
      searchableAttributes: [
        'unordered(hierarchy.lvl0)',
        'unordered(hierarchy.lvl1)',
        'unordered(hierarchy.lvl2)',
        'unordered(hierarchy.lvl3)',
        'unordered(hierarchy.lvl4)',
        'unordered(hierarchy.lvl5)',
        'unordered(hierarchy.lvl6)',
        'content',
      ],
      distinct: true,
      attributeForDistinct: 'url',
      customRanking: [
        'desc(weight.pageRank)',
        'desc(weight.level)',
        'asc(weight.position)',
      ],
      ranking: [
        'words',
        'filters',
        'typo',
        'attribute',
        'proximity',
        'exact',
        'custom',
      ],
      highlightPreTag: '<span class="algolia-docsearch-suggestion--highlight">',
      highlightPostTag: '</span>',
      minWordSizefor1Typo: 3,
      minWordSizefor2Typos: 7,
      allowTyposOnNumericTokens: false,
      minProximity: 1,
      ignorePlurals: true,
      advancedSyntax: true,
      attributeCriteriaComputedByMinProximity: true,
      removeWordsIfNoResults: 'allOptional',
      indexLanguages: ['en', 'uk'],
      queryLanguages: ['en', 'uk'],
      separatorsToIndex: '_',
    },
  },
});