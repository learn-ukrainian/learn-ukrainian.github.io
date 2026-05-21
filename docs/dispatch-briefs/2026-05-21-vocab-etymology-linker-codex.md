# Dispatch brief — vocab → etymology linker (Astro remark plugin)

**Agent**: codex (gpt-5.5, xhigh)
**Mode**: danger
**Worktree**: `.worktrees/dispatch/codex/vocab-etymology-linker-2026-05-21` (REQUIRED)
**Task ID**: `vocab-etymology-linker-2026-05-21`
**Created**: 2026-05-21 night

## Why

User goal (2026-05-21 PM): "I would like if our vocab should point to the etymology entries." Vocab tables in V7 lesson MDX (`| Word | IPA | English | POS | Gender | Note |`) currently render as plain markdown — no etymology links. The `/etymology/{slug}/` pages exist and the manifest covers ~36K entries with the new corpus.

Post-corpus-fix coverage probe (commit `00c09fc442`): 35/40 common Ukrainian words (`субота, кава, рік, дім, день, мати, ...`) extract as proper lemmas in the manifest. That's strong enough to ship vocab→etymology linking.

## What

Build an Astro remark plugin that walks every MDX file at build time, finds vocabulary tables, and wraps matched words in `<a href="/etymology/{slug}/">{word}</a>` links.

### Components

1. **Lemma index loader** (`starlight/src/data/etymology-lemma-index.ts` or similar):
   - At Astro build time, load `etymology-manifest.json`
   - Build a Map keyed by normalized lemma → primary route. Two route shapes:
     - Single entry → `/etymology/{page_slug}/` (direct)
     - Polysemy (slug has multiple page_slugs) → `/etymology/{slug}/` (landing/disambig)
   - Normalization: lowercase + strip combining diacritics (NFD then drop U+0300-U+036F)
   - Also build a reverse VESUM map: word_form → lemma (load `data/vesum.db` at build time; ~7M forms, may need a smaller cached subset)

2. **VESUM lemmatizer** (optional, ~30% coverage boost):
   - Given a vocab word, look up its canonical lemma in VESUM
   - Try direct match first, then fall back to base form (strip reflexive `-ся`/`-сь`)
   - For multi-word vocab like "Доброго ранку" → split, try each word
   - **Constraint**: VESUM lookup at Astro build time is expensive (7M-row table). Pre-build a subset: lemmatize only the words that appear in any committed `*.mdx` vocab table (run a one-shot script that scans MDX files, extracts vocab words, and emits `starlight/src/data/vesum-vocab-lemmas.json` with form→lemma map covering only those words).

3. **Remark plugin** (`starlight/plugins/vocab-etymology-link.ts`):
   - Use unified/remark AST: walk `mdxJsxFlowElement` for `<TabItem label="Vocabulary">`, then walk descendant tables
   - For each table row, identify the "Word" column by looking at the header row's first column label (case-insensitive match against `word` or `слово`)
   - For each non-header data row, take the first column's text content
   - If the word matches a manifest lemma (direct or via VESUM fallback), replace the text node with a Link AST node
   - Skip if already wrapped in a link (idempotent)

4. **Register in `astro.config.mjs`**:
   - Add to `integrations: [starlight({...}), { ... }]` or `markdown.remarkPlugins`
   - Order it after the table parser, before HTML stringification

5. **Style** (`starlight/src/components/Direct.module.css` or new CSS):
   - Subtle dotted underline for etymology links (no full underline; learner shouldn't think it's a critical UI element)
   - On hover: slight color change + tooltip with the slug

### Acceptance gates

1. **Coverage** on real V7 lesson MDX: ≥25% of vocab words in a sample of 5 random A1/A2/B1 modules become linked (target 30-40% with VESUM lemmatizer).
2. **Build success**: `npm --prefix starlight run build` completes with no errors. Check the build output for the `dist/` HTML — verify links resolve to existing etymology pages (no 404s).
3. **Idempotent**: running the plugin twice produces identical output.
4. **No false positives**: do not link words that aren't in the manifest (vs creating broken /etymology/X/ links).
5. **Test coverage**:
   - Unit tests for the lemma normalizer (stress mark strip, lowercase)
   - Unit tests for VESUM lemmatizer (reflexive verb, declined noun)
   - Integration test: feed a synthetic MDX with a vocab table → verify links emitted on matched words, plain text on unmatched
6. **Documentation**: short README in `starlight/plugins/` explaining what the plugin does, how to opt out for specific tables (data attribute or comment).

### Don't

- Don't link multi-word phrases or words containing spaces. ESUM is single-lemma-only.
- Don't link words in non-Vocabulary tabs. (Activity tabs may have words in different contexts.)
- Don't precompute the link list at corpus-rebuild time. The plugin reads the manifest at Astro build time so it stays in sync with `etymology-manifest.json` changes.
- Don't reach into VESUM at runtime in Astro (build-only).
- Don't ship if `npm run build` produces broken links — that's worse than no links.

## Verification before commit

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/ruff check scripts/ tests/
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python -m pytest tests/etymology/ -v --tb=short
cd /Users/krisztiankoos/projects/learn-ukrainian/starlight && npm run build 2>&1 | tail -30
# Spot-check a real lesson page for vocab links:
cd /Users/krisztiankoos/projects/learn-ukrainian && grep -c 'href="/etymology/' starlight/dist/a1/*/index.html 2>&1 | head -10
```

The grep should produce at least one match per page sampled. Report the actual numbers.

## Commit + PR shape

- **Branch**: `feat/vocab-etymology-linker-2026-05-21`
- **One or two commits** (plugin + tests + style can be one; one-shot lemmatization script can be a second).
- **PR title**: `feat(starlight): vocab → etymology linker (closes vocab-linking ask 2026-05-21)`
- **PR body**: coverage stats per CEFR level, sample before/after HTML rendering, list of opt-out hooks.
- **Do NOT auto-merge.**

## Steps (mandatory)

1. `git worktree add -B feat/vocab-etymology-linker-2026-05-21 .worktrees/dispatch/codex/vocab-etymology-linker-2026-05-21 origin/main`
2. Read `starlight/astro.config.mjs` to understand integration points.
3. Read `starlight/src/pages/etymology/[slug].astro` to understand the manifest schema.
4. Build the one-shot VESUM lemmatization script (output: `starlight/src/data/vesum-vocab-lemmas.json` covering only vocab words found in committed MDX).
5. Build the remark plugin.
6. Register in `astro.config.mjs`.
7. Add tests (unit + integration).
8. Style (CSS).
9. Run `npm run build`, check for 404 links + broken pages.
10. Single conventional commit (or 2).
11. `git push -u origin feat/vocab-etymology-linker-2026-05-21`
12. `gh pr create --title ... --body ...` (NO auto-merge).
13. Report task done with coverage stats verbatim from the smoke-run.

## Anti-fabrication (per #M-4)

Every "tests pass" / "build clean" / "coverage = N%" / "no 404 links" claim MUST be backed by literal command output (cmd + cwd + raw last lines). Quote `npm run build` summary, pytest summary, grep counts. Don't paraphrase.
