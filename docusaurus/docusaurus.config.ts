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

  clientModules: [],

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

  themes: [
    [
      require.resolve("@easyops-cn/docusaurus-search-local"),
      /** @type {import("@easyops-cn/docusaurus-search-local").PluginOptions} */
      ({
        hashed: true,
        language: ["en"],
        highlightSearchTermsOnTargetPage: true,
        explicitSearchResultPath: true,
      }),
    ],
  ],

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
    // Algolia Search Configuration (Uncomment to use Algolia instead of Local Search)
    // algolia: {
    //   // The application ID provided by Algolia
    //   appId: 'YOUR_APP_ID',
    //   // Public API key: it is safe to commit it
    //   apiKey: 'YOUR_SEARCH_API_KEY',
    //   // The index name to query
    //   indexName: 'learn-ukrainian',
    //   // Optional: see doc section below
    //   contextualSearch: true,
    //   // Optional: Specify domains where the navigation should occur through window.location instead on history.push. Useful when our Algolia config crawls multiple documentation sites and we want to navigate with window.location.href to them.
    //   // externalUrlRegex: 'external\\.com|domain\\.com',
    //   // Optional: Replace parts of the item URLs from Algolia. Useful when using the same search index for multiple deployments using a different baseUrl. You can use regexp or string in the `from` param. For example: localhost:3000 vs myCompany.com/docs
    //   // replaceSearchResultPathname: {
    //   //   from: '/docs/', // or as RegExp: /\/docs\//
    //   //   to: '/',
    //   // },
    //   // Optional: Algolia search parameters
    //   // searchParameters: {},
    //   // Optional: path for search page that enabled by default (`false` to disable it)
    //   // searchPagePath: 'search',
    // },
  } satisfies Preset.ThemeConfig,
};

export default config;
