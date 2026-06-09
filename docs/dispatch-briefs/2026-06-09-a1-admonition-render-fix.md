# Dispatch brief — A1 render fixes: ::: admonitions + dev-server hardening (LIVE)

The A1 course is live. Audit (orchestrator, 2026-06-09) found ONE systemic render bug plus a
dev-server stability issue. Fix at the pipeline layer, add tests, build-verify, **NO auto-merge**.

## #M-4 verifiable-claims preamble
Every claim in the final report = command + cwd + raw output. Quote raw, never "I checked":
- "admonitions render" → after `npm run build:full`, `grep -roE ':::(info|tip|caution|note)' dist/a1/ dist/folk/ | wc -l` returns **0** (raw directives gone), AND a built file contains `<aside class="admonition` — paste both raw.
- "dev server clean" → start dev, load `/a1/sounds-letters-and-hello/`, and show the browser/console has NO `jsxDEV is not a function` (or paste `vite` startup with deps optimized and no error).
- "tests pass" / "build green" → raw final lines.

## Bug 1 (PRIMARY) — Starlight `:::` admonitions render RAW in all 55 A1 lessons
Every A1 module (and folk/lexicon content) uses Starlight admonition directives that Astro's
pipeline does NOT process — they render as literal text. Confirmed counts in source:
`:::info` ×55, `:::tip` ×43, `:::caution` ×11, `:::note` ×1. Built HTML contains raw `:::info[...]`.
Syntax includes the **label form**: `:::info[🎧 🔗 External Resources]` … content … `:::` (the
Resources tab header), and plain `:::tip` / `:::caution` blocks with markdown bodies (bold, lists, links).

Fix at the **markdown pipeline** (parity-safe, NO per-MDX edits):
1. `cd starlight && npm install remark-directive` (add dep).
2. New `plugins/remark-admonitions.mjs`: a remark plugin that visits `containerDirective` nodes
   whose `name` ∈ {info, tip, caution, note, danger, warning}, reads the optional label
   (`directive[label]` → the directive's `data.directiveLabel` paragraph child) as the title, and
   rewrites the node to `<aside class="admonition admonition-{name}">` with a
   `<p class="admonition-title">{title or default-per-type}</p>` then the body. Keep the body's
   inner markdown intact (it renders normally).
3. Wire `remarkDirective` THEN the admonitions plugin into BOTH `markdown.remarkPlugins` and the
   `mdx()` integration's `remarkPlugins` in `astro.config.mjs` (order matters: directive parser first).
4. Add CSS for `.admonition` + per-type accent (info/tip/caution/note/danger/warning) in the global
   stylesheet the lessons already load. Match the POC look if one exists (`docs/poc/`).
5. Verify: `grep -roE ':::(info|tip|caution|note|danger|warning)' dist/a1 dist/folk` → 0; built
   HTML shows `<aside class="admonition`. Spot-check `/a1/weather/` (has :::info + :::tip) and the
   Resources tab of `/a1/sounds-letters-and-hello/`.

## Bug 2 — dev server `jsxDEV is not a function` (React-island stale Vite pre-bundle)
On `astro dev`, all React islands (VocabCard, Quiz, FillIn, MatchUp, TrueFalse, Order, …) threw
`TypeError: jsxDEV is not a function` → empty Словник/Зошит locally. Cleared cache as a stopgap;
make it durable:
1. Remove the **extraneous `preact`** (leftover from the old Starlight/docsearch setup) — `npm prune`
   or remove it so it can't shadow React's jsx runtime.
2. Add `'react/jsx-runtime'` and `'react/jsx-dev-runtime'` to `optimizeDeps.include` in
   `astro.config.mjs` (currently only `['react','react-dom']`) so Vite always pre-bundles them
   consistently.
3. Verify: fresh `astro dev`, load an A1 module, confirm islands render and console has no jsxDEV error.

## Numbered steps
1. Confirm `pwd` is the dispatch worktree (not main).
2. Bug 1: install remark-directive; add the admonitions plugin; wire into both pipelines; add CSS.
3. Bug 2: prune preact; extend optimizeDeps.
4. Tests: a unit test for the remark-admonitions plugin (`:::info[Title]\nbody\n:::` → aside with
   title + body; plain `:::tip` → aside with default title); keep/extend any vitest that asserts
   built output has no raw `:::`.
5. `npm run build:full --prefix starlight` (green) + the grep verifications above + `npm test --prefix starlight`.
6. Commit (conventional + `X-Agent` trailer): `fix(ui): render ::: admonitions (Astro pipeline) + harden React-island dev pre-bundle [A1 live bugs]`.
7. `git push -u origin <branch>`; `gh pr create` describing both root causes + the verification output. **NO merge.**

## Out of scope (orchestrator handles)
- Word Atlas gloss/entity cleanup and the ESUM v2 etymology source swap — separate phase. Do not touch lexicon-manifest or etymology data here.
