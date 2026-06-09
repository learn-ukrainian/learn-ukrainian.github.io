// @ts-check
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import react from '@astrojs/react';
import sitemap from '@astrojs/sitemap';
import rehypeMermaid from 'rehype-mermaid';
import remarkDirective from 'remark-directive';
import remarkGfm from 'remark-gfm';
import remarkAdmonitions from './plugins/remark-admonitions.mjs';
import vocabEtymologyLinker from './plugins/vocab-etymology-link.mjs';

const remarkPlugins = [remarkDirective, remarkAdmonitions, remarkGfm, vocabEtymologyLinker];

// https://astro.build/config
export default defineConfig({
  site: 'https://learn-ukrainian.github.io',
  trailingSlash: 'always',

  compressHTML: true,

  markdown: {
    remarkPlugins,
    rehypePlugins: [rehypeMermaid],
  },

  // Prevent duplicate React instances (SSR + client hydration)
  vite: {
    resolve: {
      alias: {
        '@site': new URL('.', import.meta.url).pathname,
        '@astrojs/starlight/components': new URL('./src/starlight-compat/index.ts', import.meta.url).pathname,
      },
      dedupe: ['react', 'react-dom'],
    },
    optimizeDeps: {
      include: ['react', 'react-dom', 'react/jsx-runtime', 'react/jsx-dev-runtime'],
    },
  },

  integrations: [
    mdx({
      remarkPlugins,
      rehypePlugins: [rehypeMermaid],
    }),
    react(),
    sitemap(),
  ],
});
