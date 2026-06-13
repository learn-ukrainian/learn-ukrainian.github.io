// @ts-check
import { realpathSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
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
const starlightRoot = fileURLToPath(new URL('.', import.meta.url));
const starlightNodeModules = realpathSync(fileURLToPath(new URL('./node_modules', import.meta.url)));
// Folk un-hidden 2026-06-14 for the preview/seminar-test launch (reverses
// orchestrator #3027). Empty = nothing suppressed from public routing.
const hiddenPublicPaths = [];

const isHiddenPublicPage = (page) => {
  const pathname = page.startsWith('http') ? new URL(page).pathname : page;
  return hiddenPublicPaths.some(
    (hiddenPath) => pathname === hiddenPath || pathname.startsWith(`${hiddenPath}/`),
  );
};

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
    server: {
      fs: {
        allow: [starlightRoot, starlightNodeModules],
      },
    },
    resolve: {
      alias: {
        '@site': starlightRoot,
        '@astrojs/starlight/components': fileURLToPath(new URL('./src/starlight-compat/index.ts', import.meta.url)),
      },
      dedupe: ['react', 'react-dom'],
    },
    optimizeDeps: {
      include: ['react', 'react-dom', 'react/jsx-runtime', 'react/jsx-dev-runtime'],
    },
  },

  integrations: [
    // GoatCounter — privacy-friendly analytics (no cookies, no PII). Injected on
    // every page from astro.config so coverage does not depend on any single layout.
    // Site code is hardcoded (always active in the production build — no env var that
    // can silently be unset in CI), and the loader is self-hosted at /count.js
    // (public/count.js) to avoid a third-party CDN dependency.
    {
      name: 'goatcounter-analytics',
      hooks: {
        'astro:config:setup': ({ injectScript }) => {
          injectScript(
            'page',
            "if (!document.querySelector('script[data-goatcounter]')) {" +
              "var s=document.createElement('script');" +
              "s.async=true;s.src='/count.js';" +
              "s.setAttribute('data-goatcounter','https://learn-ukrainian.goatcounter.com/count');" +
              'document.head.appendChild(s);}',
          );
        },
      },
    },
    mdx({
      remarkPlugins,
      rehypePlugins: [rehypeMermaid],
    }),
    react(),
    sitemap({
      filter: (page) => !isHiddenPublicPage(page),
    }),
  ],
});
