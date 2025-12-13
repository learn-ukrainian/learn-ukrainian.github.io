import { themes as prismThemes } from 'prism-react-renderer';
import type { Config } from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Curricula Opus',
  tagline: 'A Theory-First Ukrainian Language Learning Platform',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://krisztiankoos.github.io',
  baseUrl: '/curricula-opus/',

  organizationName: 'krisztiankoos',
  projectName: 'curricula-opus',

  onBrokenLinks: 'warn',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

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
      title: 'Curricula Opus',
      logo: {
        alt: 'Curricula Opus Logo',
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
          href: 'https://github.com/krisztiankoos/curricula-opus',
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
              href: 'https://github.com/krisztiankoos/curricula-opus',
            },
          ],
        },
      ],
      copyright: `Curricula Opus © ${new Date().getFullYear()} — Слава Україні! 🇺🇦`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
