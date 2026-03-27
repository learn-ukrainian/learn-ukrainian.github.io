// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import react from '@astrojs/react';
import sitemap from '@astrojs/sitemap';
import starlightDocSearch from '@astrojs/starlight-docsearch';
import rehypeMermaid from 'rehype-mermaid';


// https://astro.build/config
export default defineConfig({
  site: 'https://learn-ukrainian.github.io',
  trailingSlash: 'always',

  compressHTML: true,

  markdown: {
    rehypePlugins: [rehypeMermaid],
  },

  // Prevent duplicate React instances (SSR + client hydration)
  vite: {
    resolve: {
      dedupe: ['react', 'react-dom'],
    },
    optimizeDeps: {
      include: ['react', 'react-dom'],
    },
  },

  integrations: [
    starlight({
      title: 'Learn Ukrainian',
      tagline: 'Мова – душа народу • Language is the soul of a nation',
      logo: {
        src: './src/assets/logo.svg',
        alt: 'Learn Ukrainian logo',
      },
      social: [
        {
          label: 'GitHub',
          icon: 'github',
          href: 'https://github.com/learn-ukrainian/learn-ukrainian.github.io',
        },
      ],
      head: [
        {
          tag: 'meta',
          attrs: {
            name: 'algolia-site-verification',
            content: '1DB51F4A18C9DC67',
          },
        },
        // Privacy-respecting analytics — no cookies, GDPR-compliant
        // To activate: sign up at plausible.io and set data-domain
        {
          tag: 'script',
          attrs: {
            defer: true,
            'data-domain': 'learn-ukrainian.github.io',
            src: 'https://plausible.io/js/script.js',
          },
        },
      ],
      credits: false,
      components: {
        // Suppress Starlight's auto-rendered PageTitle on splash pages — the
        // custom Home component renders its own hero with a title.
        PageTitle: './src/components/overrides/PageTitle.astro',
      },
      customCss: [
        './src/css/custom.css',
        './src/styles/lesson.css',
      ],
      plugins: [
        starlightDocSearch({
          appId: 'MFWOKG2YFD',
          apiKey: '4413bc11f7878cb2605766f6a050bdcc',
          indexName: 'https_learn_ukrainian_github_io_pages',
          searchParameters: {
            // Note: removed 'docusaurus_tag' — that was a Docusaurus-specific facet
            // that does not exist in Starlight and caused zero search results.
            facetFilters: [
              ['language:en', 'language:uk'],
            ],
          },
        }),
      ],
      sidebar: [
        { label: 'Getting Started', slug: 'index' },
        { label: 'A1 - Beginner', autogenerate: { directory: 'a1' }, collapsed: true },
        { label: 'A2 - Elementary', autogenerate: { directory: 'a2' }, collapsed: true },
        { label: 'B1 - Intermediate', autogenerate: { directory: 'b1' }, collapsed: true },
        { label: 'B2 - Upper-Intermediate', autogenerate: { directory: 'b2' }, collapsed: true },
        { label: 'C1 - Advanced', autogenerate: { directory: 'c1' }, collapsed: true },
        { label: 'C2 - Mastery', autogenerate: { directory: 'c2' }, collapsed: true },
        { label: 'LIT - Literature', autogenerate: { directory: 'lit' }, collapsed: true },
        { label: 'HIST - Історія України', autogenerate: { directory: 'hist' }, collapsed: true },
        { label: 'ISTORIO - Історіографія', autogenerate: { directory: 'istorio' }, collapsed: true },
        { label: 'BIO - Біографії українців', autogenerate: { directory: 'bio' }, collapsed: true },
        { label: 'B2-PRO - Професійна українська', autogenerate: { directory: 'b2-pro' }, collapsed: true },
        { label: 'C1-PRO - Фахова українська', autogenerate: { directory: 'c1-pro' }, collapsed: true },
        { label: 'OES - Old East Slavic', autogenerate: { directory: 'oes' }, collapsed: true },
        { label: 'RUTH - Ruthenian', autogenerate: { directory: 'ruth' }, collapsed: true },
      ],
    }),
    react(),
    sitemap(),
  ],
});
