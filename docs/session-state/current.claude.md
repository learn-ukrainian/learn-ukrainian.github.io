# Current — Claude Session Handoff (2026-06-15, late)

> Router: read `docs/session-state/current.md` first (if present).
> **Latest detailed handoff: `docs/session-state/2026-06-15-claude-atlas-antonym-live-conformance-gate-fix.md`** — read it in full.

> **ROLE:** main orchestrator = **infra / tooling / tech-debt / general features / integration / merge** — NOT tracks. Track issues (folk/bio/lit/seminar/B2-wiki) are track-orchestrator-owned.

> **✅ Shipped this session (merged):** Dependabot ×5 (#3180–#3183, #3185). **#3195** (#3150 Atlas freshness **rescoped to lexicon-CODE-only** — codex re-dispatch, reviewed+verified). **#3206** (#3197 Вікісловник **antonym noise filter**, did inline). **#3210** (**§8 `lemma_in_vesum` conformance gate root-fix** — casefold-vs-capitalized + suffix-blind exemption + VESUM-gap heritage allowlist). **#3213** (full `make atlas` regen — **antonym cleanup LIVE + ~120K-line vocab refresh**; Frontend astro render-validated). **Freshness gate GREEN on main.** Autopsy: `docs/bug-autopsies/atlas-conformance-vesum-false-positives.md`.

> **⚠️ OPEN ITEMS (next session):**
> - **Dependabot stragglers #3186 (react patch), #3187 (happy-dom patch), #3188 (@astrojs/mdx 5→6 MAJOR)** + **#3184 greenlet** (in-flight, watcher `b43c7wm53` — confirm it merged). Repo has **auto-merge OFF + dependabot ignores `@dependabot merge`** → each needs `gh pr update-branch <N>` → wait CI → `gh pr merge --squash --delete-branch` (NO `--admin`, #M-0.5). npm trio serializes on `package-lock.json` (one at a time, re-update next after each merge).
> - **#3211 (filed):** replace manual `_VESUM_GAP_HERITAGE_LEMMAS` allowlist with a `sources.db` heritage-fallback (Грінченко/ЕСУМ) so the §8 gate self-heals on VESUM gaps. Proper class fix.
> - **#3098 (§6 epic):** commented — §6 calque note near-dormant; enhancement = surface it on the *replacement* word's Atlas page.

> **🎯 Next (carried):** #2732 (isolate marker-pdf + resolver-lock — needs a DECISION, don't auto-fire), #1908 (layered-harness audit), #3079 (seminar self-converge EPIC), #3162 (primary-text routing, folk-adjacent).

> ⚠️ Watch: **SHIP LIVE not just code-merged (#M-11)** — antonym fix needed the manifest regen, which surfaced the gate bug; chased to #3213. **Heritage-defense before "fixing" vocab** — `search_heritage` proved `хвастливий` authentic before I nearly replaced it. **VERIFY dispatch self-reports (#M-8)** — read codex #3195's diff inline. Atlas/lexicon dispatches = code-only / never commit `lexicon-manifest.json` (orchestrator regenerates after merge).

Prior handoff (superseded): `2026-06-15-claude-parallel-fanout-atlas-infra.md`.
