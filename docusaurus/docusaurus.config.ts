import { themes as prismThemes } from 'prism-react-renderer';
import type { Config } from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Learn Ukrainian',
  tagline: 'Мова – душа народу • Language is the soul of a nation',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  trailingSlash: true,  // Ensure URLs match sitemap format

  clientModules: [],

  // Algolia site verification
  headTags: [
    {
      tagName: 'meta',
      attributes: {
        name: 'algolia-site-verification',
        content: '1DB51F4A18C9DC67',
      },
    },
  ],

  url: 'https://learn-ukrainian.github.io',
  baseUrl: '/',

  organizationName: 'learn-ukrainian',
  projectName: 'learn-ukrainian.github.io',

  onBrokenLinks: 'warn',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  markdown: {
    mermaid: true,
  },

  themes: ['@docusaurus/theme-mermaid'],

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          // Editing disabled
          // Custom admonition keywords for historical tracks (OES, RUTH, LIT, B2-HIST)
          admonitions: {
            keywords: [
              // Standard Docusaurus admonitions
              'note', 'tip', 'info', 'warning', 'danger', 'caution',
              // Historical / primary source admonitions
              'primary-source',  // For authentic historical documents
              'historical',      // For historical context blocks
              'chronicle',       // For chronicle/litopys quotes
              'quote',           // For general citations
              // Curriculum-specific admonitions
              'myth-buster',     // For debunking myths
              'history-bite',    // For historical trivia
              'reflection',      // For reflection prompts
              'resources',       // For further reading
              'solution',        // For exercise solutions (collapsible)
              'context',         // For contextual information
            ],
          },
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/social-card.jpg',
    colorMode: {
      defaultMode: 'light',
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Learn Ukrainian',
      logo: {
        alt: 'Learn Ukrainian Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          label: 'Curriculum',
          position: 'left',
          items: [
            {
              label: 'Overview',
              to: '/docs/',
            },
            {
              label: 'A1 - Beginner',
              to: '/docs/a1/',
            },
            {
              label: 'A2 - Elementary',
              to: '/docs/a2/',
            },
            {
              label: 'B1 - Intermediate',
              to: '/docs/b1/',
            },
            {
              label: 'B2 - Upper-Intermediate',
              to: '/docs/b2/',
            },
            {
              label: 'C1 - Advanced',
              to: '/docs/c1/',
            },
            {
              label: 'C2 - Mastery',
              to: '/docs/c2/',
            },
            {
              type: 'html',
              value: '<hr style="margin: 4px 12px; border-color: var(--ifm-color-emphasis-300);">',
            },
            {
              label: 'B2-HIST - Ukrainian History',
              to: '/docs/b2-hist/',
            },
            {
              label: 'C1-BIO - Biographies',
              to: '/docs/c1-bio/',
            },
            {
              label: 'LIT - Literature & Classics',
              to: '/docs/lit/',
            },
            {
              type: 'html',
              value: '<hr style="margin: 4px 12px; border-color: var(--ifm-color-emphasis-300);">',
            },
            {
              label: 'OES - Old East Slavic',
              to: '/docs/oes/',
            },
            {
              label: 'RUTH - Ruthenian',
              to: '/docs/ruth/',
            },
          ],
        },
        {
          href: 'https://github.com/learn-ukrainian/learn-ukrainian.github.io',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Learn',
          items: [
            {
              label: 'A1 - Beginner',
              to: '/docs/a1/',
            },
            {
              label: 'A2 - Elementary',
              to: '/docs/a2/',
            },
            {
              label: 'B1 - Intermediate',
              to: '/docs/b1/',
            },
          ],
        },
        {
          title: 'Advanced',
          items: [
            {
              label: 'B2 - Upper-Intermediate',
              to: '/docs/b2/',
            },
            {
              label: 'C1 - Advanced',
              to: '/docs/c1/',
            },
            {
              label: 'C2 - Mastery',
              to: '/docs/c2/',
            },
          ],
        },
        {
          title: 'More',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/learn-ukrainian/learn-ukrainian.github.io',
            },
          ],
        },
      ],
      copyright: `Learn Ukrainian © ${new Date().getFullYear()} — Слава Україні! 🇺🇦`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
    // Algolia Search Configuration (Build Plan)
    algolia: {
      appId: 'MFWOKG2YFD',
      apiKey: '4413bc11f7878cb2605766f6a050bdcc',
      indexName: 'https_learn_ukrainian_github_io_pages',
      // CRITICAL: Disable contextualSearch because it forces 'language:en'
      // We need to search BOTH 'en' and 'uk' manually
      contextualSearch: false,
      searchParameters: {
        facetFilters: [
          ['language:en', 'language:uk'],       // Search both languages (OR condition)
          ['docusaurus_tag:docs-default-current'], // Filter by version
        ],
        hitsPerPage: 10,
      },
      searchPagePath: 'search',
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
