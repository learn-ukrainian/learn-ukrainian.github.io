# Folk Nav Hide + GoatCounter Analytics Report

Date: 2026-06-12

## Folk Entry Points Removed

- `starlight/src/pages/index.astro:23` removed the Folk row from the home page seminar track inventory.
- `starlight/src/pages/[...slug].astro:166` removed the `/folk/koliadky-shchedrivky/` primary CTA from the Folk track metadata.
- `starlight/src/pages/[...slug].astro:167` removed the `/folk/dumy-lytsarski/` secondary CTA from the Folk track metadata.
- `starlight/src/pages/[...slug].astro` now excludes Folk from generated search result links.
- `starlight/src/pages/[...slug].astro` now suppresses Folk breadcrumbs, lesson sidebar links, and previous/next links.
- `starlight/src/components/LevelLanding.tsx` now renders Folk active module cards as disabled, unlinked cards, so `starlight/src/content/docs/folk/index.mdx` stays on disk without linking to `/folk/...`.
- `starlight/astro.config.mjs` now filters `/folk` and `/folk/...` URLs out of the generated sitemap.

Lexicon top nav was checked in `starlight/src/pages/lexicon/[lemma].astro`, `starlight/src/pages/lexicon/index.astro`, and `starlight/src/pages/lexicon/index/index.astro`; those pages inherit `CourseLayout` top nav, which has no Folk item.

## GoatCounter Wiring

- `starlight/src/layouts/CourseLayout.astro` reads `import.meta.env.PUBLIC_GOATCOUNTER_CODE`.
- If the value is empty, no GoatCounter script is rendered.
- If set, the shared head renders `data-goatcounter="https://CODE.goatcounter.com/count"` with `src="//gc.zgo.at/count.js"`.

To activate: register a free site at goatcounter.com, set `PUBLIC_GOATCOUNTER_CODE=<your-code>` in the Starlight build environment or `starlight/.env`, then rebuild with `cd starlight && npm run build`.

## Verification

- `cd starlight && npm ci`
- `cd starlight && npm run build`
- `cd starlight && PUBLIC_GOATCOUNTER_CODE=learnukrainian-test npm run build`
- `cd starlight && npm test`
- Local code review: Gemini found four issues; fixes were applied for the robust sitemap filter and disabled-card affordance. The badge CSS and shared-constant suggestions were rejected as non-blocking for this scoped diff.

Final no-env build checks:

- `rg -n "/folk/" dist --glob '*.html' --glob '*.xml' --glob '*.js' --glob '*.json'` returned 0 matches.
- `rg -n "goatcounter|gc\\.zgo\\.at" dist --glob '*.html'` returned 0 matches.
- `rg -n "href=[\\\"']/(a1|a2|b1|lexicon)/[\\\"']" dist/index.html --glob '*.html'` confirmed A1, A2, B1 Preview, and Word Atlas links remain present.

Dummy env build check:

- `PUBLIC_GOATCOUNTER_CODE=learnukrainian-test npm run build` rendered `data-goatcounter="https://learnukrainian-test.goatcounter.com/count"` and `src="//gc.zgo.at/count.js"`.
- The same dummy build had 0 `/folk/` matches across built HTML/XML/JS/JSON.
