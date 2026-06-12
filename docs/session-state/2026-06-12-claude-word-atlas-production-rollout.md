# Claude session handoff — 2026-06-12 (Word Atlas → production rollout)

> Router: `current.md` → `current.claude.md` → this. Long session. Main orchestrator (standalone).
> **Context that changes everything: real learners are on A1 now (user's teacher started using it). This is PRODUCTION. Verify the LIVE site, rollback-ready, no ship-and-see.**

## 🚨 RESUME HERE — finish the one production deploy
1. **`atlas-finalize-all` dispatch is RUNNING** (started 10:01 UTC, silence-timeout disabled, hard-timeout 9000s). Worktree `.worktrees/dispatch/codex/atlas-finalize-all`. Check `batch_state/tasks/atlas-finalize-all.json` `status`. The session monitor (bd2mu32g2) may not survive the handoff — **poll the task json yourself**.
2. **When it lands → VERIFY (production discipline, #M-4 + #M-11):**
   - full vocab ~2,045 lemmas (A1 `lemma` key + A2 `word` key both parsed; A2 must appear)
   - **ZERO Russian / no Грінченко displayed** (grep built dist for Грінченко glosses)
   - **прапор reads CLEAN** — soviet caveat ONLY on the СУМ-11 definition card, NO word-level banner (user was explicit: flag the entry, not the word)
   - synonyms sense-correct (вода/голосний/місто omitted, not wrong; батько→тато/отець)
   - heritage detection: вельми→Архаїзм, гетьман→Історизм, кобіта→Діалектизм (the brief asked to wire VESUM `is_archaic` + `search_heritage`; VERIFY it actually fires — may be partial)
3. **Merge it** (no conflict with #3027 — finalize touches `lexicon/[lemma].astro` + lexicon scripts; #3027 touched `CourseLayout.astro`/`index.astro`).
4. **Wire GoatCounter for the deploy:** add `PUBLIC_GOATCOUNTER_CODE=learn-ukrainian` to the build step in `.github/workflows/deploy-pages.yml` (build = `npm run build:full`; CourseLayout.astro reads `import.meta.env.PUBLIC_GOATCOUNTER_CODE`). Code is PUBLIC (not a secret). Full snippet + plan in `/tmp/claude-atlas-briefs/GOATCOUNTER-CODE.txt`.
5. **Deploy:** `gh workflow run deploy-pages.yml --ref main` (auto-deploy is DISABLED — manual only). Watch it.
6. **Verify the LIVE site** (learn-ukrainian.github.io): no `/folk/` links anywhere; no Russian on Atlas pages; full vocab; GoatCounter pinging (check learn-ukrainian.goatcounter.com); a few A1 words render right. Rollback = `git revert` + redeploy.

## State (verified end of session)
- **Live now** = deploy `4d03d1aac` (2026-06-12 01:44): warnings + synonyms + idioms + stress + CEFR + banners + multi-source defs, **on 138 words**. ⚠️ Live STILL has: Грінченко Russian glosses, folk links, word-level soviet flag, no GoatCounter. The finalize+#3027 fix all of these but are **NOT deployed yet**.
- **origin/main HEAD** = `8e68803c82` (#3027). On main, NOT deployed: folk-hide + GoatCounter wiring (#3027), services self-heal (#3026).
- **Not on main yet**: the finalize (full vocab + Грінченко removal + entry-scoped soviet) — still building.

## ✅ Done this session
- Merged + DEPLOYED earlier: #3011 (warnings), #3018 (sense-filtered synonyms + idioms), #3020 (visual pass: stress, CEFR, editorial banners, 3-source defs, literary). Live at 138 words.
- Merged (staged, not deployed): #3022 (design doc: drop textbook/external sections → Wikimedia-family only), #3026 (services.sh self-heal astro deps), #3027 (folk-hide + GoatCounter wiring).
- Closed superseded: #3004, #3014, #3017. Git hygiene: main fast-forwarded +23, working tree clean, cache gitignored.

## 🧠 Lessons / gotchas (hard-won)
- **NEVER run `npm`/`build` in the main checkout** — it triggered an MDX regen that corrupted folk's `kalendarna...mdx` (I wrongly blamed folk; the mtime proved it was my build). Builds + briefs go in worktrees / `/tmp` only.
- **Cache pollution**: the finalize brief wrote the slovnyk cache to `data/lexicon/slovnyk_cache/` in main (gitignored on origin, so won't commit, but it's IN the checkout). The maintenance plan should put the cache OUTSIDE the repo.
- **Scale ≠ moat**: curated course vocab is clean — at 2,144 words only ~4 русизм warnings fire. The decolonization moat needs a surzhyk/learner-error source (UA-GEC), NOT more curriculum vocab. (Spike + rebuild both confirmed.)
- **Грінченко 1907 is a Ukrainian→RUSSIAN dictionary** — its glosses are Russian. Removed from display; KEPT as backend heritage evidence (never surfaces Russian).
- **Heritage detection under-fires**: classify_lemma returns "standard" for most archaisms/historisms/dialectisms — the render has the labels (Архаїзм/Історизм/Діалектизм/Запозичення) but detection needs VESUM `is_archaic` + `search_heritage` wired (the finalize brief asked for this — verify it landed).
- **Deploy is manual** (`workflow_dispatch` only). **`services.sh build/start/rebuild astro` now self-heals** (npm ci when node_modules wiped, #3026) — node_modules in main got emptied twice this session, cause unidentified (worktrees are isolated, so not them).

## Maintenance plan (user asked; not yet built)
Atlas = derivative of curriculum vocab. Auto-maintain: CI/hook on `vocabulary.yaml` change → rebuild manifest → incremental enrich (cache only new lemmas) → **no-Russian quality gate** → PR → manual deploy. Cache must move out-of-repo.

## Open follow-ups (not blocking the deploy)
- Heritage detection wiring (archaism/historism/dialect) — verify/strengthen.
- Table-width polish (minor — case table fills left third).
- Wikimedia sections (Wikipedia/Wiktionary-link/Wikisource) — design says keep Wikipedia, build later; near-empty for basic vocab.
- GitHub repo → Insights → Traffic = interim analytics until GoatCounter is deployed.

## Restart
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
.venv/bin/python -c "import json;print(json.load(open('batch_state/tasks/atlas-finalize-all.json')).get('status'))"  # finalize done?
gh run list --workflow=deploy-pages.yml --limit 2   # what's live
cat /tmp/claude-atlas-briefs/GOATCOUNTER-CODE.txt    # goatcounter wiring
```
