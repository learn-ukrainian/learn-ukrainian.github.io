# Claude session handoff — 2026-06-13 (Atlas pair-slug fix · starlight→site rename · big git cleanup)

> Router: `current.md` → `current.claude.md` → this. Long, multi-thread session. Everything below is
> merged + on `origin/main` (`19c89e6aa4`) + deploy-verified unless marked otherwise.

## TL;DR
- **`starlight/` → `site/` rename SHIPPED + LIVE** (#3062/#3065). Compat symlink removed; all functional refs updated; deploy green; live site 200.
- **Word Atlas pair-slug enrichment bug ROOT-CAUSED + FIXED** (`19c89e6aa4`, #2985). 67 core aspectual verb pairs were silently thin; варити now shows СУМ-20 + idioms.
- **Vocab→Atlas "more →" link** shipped earlier (#3056).
- **Git fully cleaned** (user order): 1 local branch, 1 worktree, 0 stashes; remote = main + dependabot only. **Recovery SHAs embedded below.**
- Filed #3062 (rename) + #3063 (EPIC gemini→agy). #3060/#3061 still open.

## ✅ Shipped (merged + on main + deployed)
1. **#3056** Vocab→Atlas link — VocabCard "Докладніше →" → `/lexicon/{lemma}`, integrity-gated, render-time. Merged, deployed.
2. **#3062 / #3065** `starlight/` → `site/` rename. `git mv` (272 files) → compat symlink (transitional) → **symlink removed + ~80 functional refs updated** (CI, ~23 scripts, settings sparsePaths, pre-commit, shell hooks). `@astrojs/starlight/components` alias preserved (npm alias, not a path). Deploy run 27440086542→27464981713→**27474922061 all green**; live `/`, `/a1/`, `/lexicon/робота/` = 200.
3. **`19c89e6aa4`** Atlas pair-slug fix (#2985). See below.

## 🔬 Atlas pair-slug bug — the core finding (#2985)
**Symptom:** common words like `варити/зварити` showed only Sovietized СУМ-11, no idioms/etymology/synonyms — looked like "missing sources."
**Root cause (proven via the slovnyk cache):** `_slovnyk_lookup_word` queried slovnyk.me with the **combined pair string** `"варити / зварити"`, which has NO entry → all 7 dictionaries missed → **the miss was cached** → re-runs re-read the cached `None`. Hit **67 entries — the core aspectual verb pairs** (бачити/побачити, брати/взяти, вчити/вивчити…).
**Fix:** `_slovnyk_lookup_word` now splits on `/` → looks up the base (imperfective) form → re-keys the cache (bypasses stale miss). Verified: варити now renders **СУМ-20 (modern) first + Фразеологізми**. Coverage: СУМ-20 defs 814→857, idioms 507→551. 56 enrich tests green.

### ⏭️ Atlas — remaining coverage fixes (SAME pattern, NOT "blocked")
The data IS fetchable live (proven: `query_sum20`/`query_slovnyk_me`/`search_idioms`/`search_esum` all return варити). Two concrete pipeline fixes remain:
1. **§7 Синоніми (1%)** — choked by the hardcoded `_A1_SENSE_SYNONYMS` allowlist (`enrich_manifest.py:198`). Un-gate → use `synonyms_karavansky` (native, clean) + slovnyk with sense-filtering (the #3018 approach). NOT WordNet (auto-translated junk: варити→«фальсифікувати, бариги»).
2. **Non-pair cached misses never re-fetch** — the cache stores `None` misses; transient/out-of-scope failures stick. Fix: don't cache all-`None` misses, or add expiry/force-refresh.
- §6 Антоненко (0%) + §12 Вікі (0%) are un-wired *features* (data exists via `search_style_guide`/`query_wikipedia`; the section isn't in `[lemma].astro` + manifest builder).
- Live external toolkit reminder: `query_slovnyk_me` (СУМ-20, Karavansky synonyms, phraseology, Antonenko, Franko, foreign-words, bilinguals), goroh/ЕСУМ, Wikipedia/Wiktionary/Wikisource, GRAC corpus.

## 🧭 Open priorities (next)
1. **#3060 — wire `sources` MCP into agy** (Stream A P0, the gemini→agy unblock). MAPPED, ready, NOT done: agy has no MCP flag/subcommand; `plugin install` takes a dir; MCP goes in agy's local settings (`~/.agy/settings.json`, doesn't exist yet; gemini-cli `mcpServers` format, streamable-http likely `httpUrl`). Then un-no-op `tool_config.py:240` + `agy.py`. **⚠️ See recovery note — `codex/agy-mcp-fix` may already implement this.**
2. **Atlas synonym gate + cached-miss refetch** (above).
3. **#3061** (pipeline gemini→agy flip, blocked by #3060) · **#3063 EPIC** (retire gemini everywhere) · **grok-build validation** (already wired CLI v0.2.50; needs a bounded coding-task bakeoff, then promote MEMORY #0).

## ⚠️ RECOVERY NOTE — git cleanup deleted branches/stashes (user-ordered)
All recoverable via SHA (`git fetch origin <sha>` while GitHub keeps it ~90d, or local reflog): **`git branch <name> <sha>`**.
**🔴 MOST IMPORTANT: `codex/agy-mcp-fix` = `c880dab111`** — by name this is the **#3060 agy-MCP solution**. CHECK IT before re-doing #3060: `git fetch origin c880dab111 && git log c880dab111`.

Deleted remote branches:
```
agy/bio-r5-warkilled-2026-05-28 cb759acc1f · agy/deadcode-tool-1863-flash 03ebf77b5c
agy/issue-1794-brief-linter-fp-2026-05-25 ed05277298 · agy/word-atlas-wordnet-synonyms 2822898085
bio/blk1-review-fixes d776a68b8d · bio/handoff-blk3 4c85f6ed21
claude/b1-v72-build-2026-06-01 9f8978bc65 · claude/folk-agent-default c92c2e50ff
claude/plan-header-sync-a1-c2-2026-06-01 89101924d9 · codex/6877-b1-adjectives-comparative-e2e b9ebb7420b
codex/agy-mcp-fix c880dab111 · codex/context-handoff-memory 156c6299f9
codex/esum-bakeoff-2026-05-21 01cb3bd89f · codex/folk-dumy-correction 099c2c56ed
codex/heritage-classifier-fix 39553357e5 · cursor/bio-blk5-248-252 3d9b495a89
docs/handoff-2026-05-22-evening f8eaa1d3a4 · docs/handoff-2026-05-23-codex-parser-fix-anchor-partial a978245337
feat/writer-bench-v0 fcdbd13a87 · gemini/bio-batch4 b2e82ad5ba
gemini/bio-r1a-blockD-survived-2026-05-28 68cb28c10b · gemini/esum-textpdf-noise-filter-2026-05-21 0c4fae81dd
```
Cleared stashes (recover: `git stash apply <sha>`): folk-wip-presync `1f9d73fad3` · plus 13 older (autostash + codex/bio/session-state WIP). Full list was in this session's `/tmp/cleared-stashes-shas.txt`; the load-bearing one is the folk WIP `1f9d73fad3`.

## ⚠️ Lessons / watch-outs (mistakes made this session)
- **`core.bare` flipped to `true` mid-session (#2842)** broke local git (`git status` → "must be run in a work tree"). Heal: `git config core.bare false`. The session-setup canary auto-heals at start but it flips during heavy worktree/node ops.
- **NEVER `mv` `node_modules` across a dir rename** — relocating it left stale absolute `starlight/node_modules` paths in vite/astro caches → astro wouldn't start. Fix = `rm -rf <dir>/node_modules .astro dist && npm ci --prefix <dir>` + kill stale dev-server PID on the port (`services.sh stop` does NOT kill a foreign PID holding :4321).
- **`enrich_manifest.py` ignores argv** (always runs the full `enrich()`), is **silent** (only final summary), and a manual `nohup … &` gets **killed when the Bash tool's shell tears down** → use Bash `run_in_background:true`. **Never run >1 enricher** (they race on the manifest; I accidentally launched 4, caught before corruption).
- Direct-to-main commits (per user) bypass CI → a flaky `/api/orient` p95 test went red on main once; re-run cleared it.

## State at handoff
- `origin/main` = `19c89e6aa4`; local clean, == origin.
- Services running: sources :8766, api :8765, astro :4321. Atlas deploy 27474922061 green (live).
- Git: 1 local branch (main), 1 worktree, 0 stashes; remote = main + 11 dependabot (open PRs #3066–3076).

## Restart
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin -q && git log -1 --oneline origin/main   # expect 19c89e6aa4 or later
gh issue view 2985    # Atlas backlog (synonyms gate, cached-miss refetch next)
gh issue view 3060    # agy MCP — CHECK codex/agy-mcp-fix c880dab111 FIRST
```
