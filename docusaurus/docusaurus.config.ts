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

  themes: [],

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          // Editing disabled
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
              label: 'LIT - Literature & Classics',
              to: '/docs/lit/',
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
      contextualSearch: true,
      searchParameters: {
        // Temporarily disabled facetFilters to debug - crawler may not be setting language facet yet
        // facetFilters: [
        //   ['language:en', 'language:uk'],
        // ],
        hitsPerPage: 10,
      },
      searchPagePath: 'search',
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
