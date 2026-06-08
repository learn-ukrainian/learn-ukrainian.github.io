// @ts-check
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import react from '@astrojs/react';
import sitemap from '@astrojs/sitemap';
import rehypeMermaid from 'rehype-mermaid';
import remarkGfm from 'remark-gfm';
import vocabEtymologyLinker from './plugins/vocab-etymology-link.mjs';


// https://astro.build/config
export default defineConfig({
  site: 'https://learn-ukrainian.github.io',
  trailingSlash: 'always',

  compressHTML: true,

  markdown: {
    remarkPlugins: [remarkGfm, vocabEtymologyLinker],
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
      include: ['react', 'react-dom'],
    },
  },

  integrations: [
    mdx({
      remarkPlugins: [remarkGfm, vocabEtymologyLinker],
      rehypePlugins: [rehypeMermaid],
    }),
    react(),
    sitemap(),
  ],
});
