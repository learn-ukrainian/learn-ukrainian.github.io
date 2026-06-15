# Current — Claude Session Handoff (2026-06-15, late)

> Router: read `docs/session-state/current.md` first (if present).
> **Latest detailed handoff: `docs/session-state/2026-06-15-claude-atlas-antonym-live-conformance-gate-fix.md`** — read it in full.

> **ROLE:** main orchestrator = **infra / tooling / tech-debt / general features / integration / merge** — NOT tracks. Track issues (folk/bio/lit/seminar/B2-wiki) are track-orchestrator-owned.

> **✅ Shipped this session (merged):** **Dependabot 9/9** (#3180–#3188). **Atlas correctness chain:** #3195 (#3150 freshness rescoped to lexicon-CODE-only), #3206 (#3197 antonym noise filter), #3210 (§8 `lemma_in_vesum` root-fix), #3213 (full regen — **antonym cleanup LIVE + ~120K vocab refresh**, astro-render-validated), #3218 (#3211 §8 heritage fallback — Грінченко/ЕСУМ `sources.db` supersedes the manual allowlist, gate **self-heals**). **Freshness gate GREEN on main.** **#1908 (layered-harness) STARTED:** #3224 + #3226 = **#M-0.5 admin-merge guard hook** (PreToolUse(Bash) blocks `gh pr merge --admin` over failing required CI, denylist-safe, **fail-CLOSED**; #3226 fixed a fail-open on gh-error/bogus-PR caught by smoke-testing the *deployed* artifact). **Deployed live** to `.claude/` (verified exit 2 on bogus-PR --admin). 20 unit tests. Autopsy: `atlas-conformance-vesum-false-positives.md`.

> **⚠️ OPEN ITEMS (next session):**
> - **#1908 remaining hooks (continue):** #M-7 pytest-before-push (needs a pytest-freshness marker + PreToolUse(Bash) on `git push`), #M-5 secret-scan (PreToolUse(Bash) on env/printenv/set/grep-of-dotenv-files/cat-of-credential-files — rewrite-or-block; HIGH false-positive risk, design carefully), V7-build-guard (`LEARN_UK_HUMAN_AUTHORIZED=1` env gate). Pattern proven by the admin-guard: source in `agents_extensions/shared/hooks/` + register in `agents_extensions/shared/settings.json` PreToolUse[Bash] + `bash scripts/deploy_prompts.sh` to activate. Full inventory in issue #1908. **Note:** Claude hooks only fire for Claude Code; dispatched codex/gemini run their own CLIs (codex has `.codex/hooks.json`).
> - **ATLAS COMPLETION (user priority — after #1908):** strategy in **`docs/atlas-data-coverage-strategy.md`** (+ #2882 comment). Design ✓ / code ✓ (every section has a filler) / **data is the gap**. Core-vocab true gaps: translation ~535 (🟢 invert Балла→LOCAL UK→EN index, do FIRST), etymology ~740 (🟢 ЕСУМ root-fallback, LOCAL), meaning ~420 (🟡 СУМ-20 slovnyk.me online), cefr ~925 (🔴 largely UNCOVERED beyond PULS 5.9K — estimate-and-label or accept ceiling; **user's call**). Design refinement: inflected-form entries (Андрію=voc.) inflate the gap → dedupe-to-lemma decision. Each step = normal lexicon PR + `make atlas` regen, guarded by §8 + freshness gates.
> - **#3098 (§6 epic):** §6 calque note near-dormant; enhancement = surface it on the *replacement* word's Atlas page.
> - **#3150 fingerprint scope:** REJECTED narrowing it (under-gate risk > harmless friction). Verifier edits need a manual fingerprint bump — that's correct-and-safe; don't "fix."

> **🎯 Next (carried):** #2732 (isolate marker-pdf + resolver-lock — needs a DECISION, don't auto-fire), #3079 (seminar self-converge EPIC), #3162 (primary-text routing, folk-adjacent).

> ⚠️ Watch: **SHIP LIVE not just code-merged (#M-11)** — antonym fix needed the manifest regen, which surfaced the gate bug; chased to #3213. **Heritage-defense before "fixing" vocab** — `search_heritage` proved `хвастливий` authentic before I nearly replaced it. **VERIFY dispatch self-reports (#M-8)** — read codex #3195's diff inline. Atlas/lexicon dispatches = code-only / never commit `lexicon-manifest.json` (orchestrator regenerates after merge).

Prior handoff (superseded): `2026-06-15-claude-parallel-fanout-atlas-infra.md`.
