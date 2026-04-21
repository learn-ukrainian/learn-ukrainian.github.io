# Pilot Readiness Audit — 2026-04-21

> **Context:** EPIC #1365 A.11 / A.12 Ukrainian-canonical pilot hit real
> problems during M01 end-to-end smoke. This doc inventories EVERY
> problem surfaced (and some that were latent), groups them, proposes
> priority and ownership. It exists so we don't build on sand, and so
> Codex/Gemini can chip in adversarially before we file the full
> issue cluster.

> **Dependency chain for scale-up (user-defined sequencing):**
>
>  1. **Plans reviewed & fixed** — plans are the source of truth for
>     modules. Contaminated plans → contaminated modules forever.
>  2. **Wikis reviewed & fixed** — wikis are the retrieved context for
>     module writing. Flash-grade wikis + glossary leaks = wrong source.
>  3. **Then build modules** — only when the upstream is clean.
>
> Anything that builds modules before (1) and (2) complete is
> throwaway work.

---

## Part 1 — Problem inventory (48 items, grouped)

### A. Track architecture (the hole Krisztian flagged)

**A1.** No destination path for Ukrainian-canonical content. Running
`v6_build.py --step publish` writes to `starlight/src/content/docs/a1/`
— the English track's URL path. M01 Ukrainian lesson overwrote the
English M01 before the deeper issue surfaced. **Alona can't review what
she can't access, and we can't publish UK-canonical content without
clobbering English.**

Options to pick from:
- Separate Starlight collection (`docs-uk/` or `docs-native/`)
- Separate sidecar site
- Markdown-only export for review (no Starlight render)
- Subpath: `/uk-native/a1/...`

**A2.** No ADR pinning the two-track publishing model. Existing doc:
`docs/architecture/ROADMAP-two-track-build-plan.md`. Need an ADR that
codifies: UK pipeline outputs → HERE, English pipeline outputs → HERE,
they never overwrite each other, pipeline refuses to cross paths.

---

### B. Review pipeline (content-level, biggest blocker)

**B1.** Heal loop does FROM-SCRATCH rewrite when review verdict is
REVISE. Non-negotiable rule §4 explicitly says *"Never rewrite from
scratch. PATCH fixes only what's broken."* Current `step_write::FIX
OUTPUT — Holistic correction` path regenerates content, which degrades
it round-over-round. M01 demonstrated: 6.2 → 5.8 on consecutive rounds,
exactly matching the rule's prediction (9.6 → 9.2 → 8.4). Reviewer
emits `<fixes>` blocks; heal loop must apply them as find/replace, not
regenerate.

**B2.** Reviewer rubric penalizes word-count overruns. Rule §1: word
targets are MINIMUMS; 1.5× overshoot is expected. `v6-review-uk.md`
(freshly written by Codex in #1385) doesn't know this. M01 got "Plan
adherence: 4/10" partly because it was 1977 vs 1200 target. Needs
rubric edit: "Word count over target is NOT a defect. Only underrun
below 0.9× target is."

**B3.** UK reviewer enforces plan prose mechanically, even when plan
is wrong. The `А тебе?` / `А у тебе?` case: writer produced natural
Ukrainian, reviewer overruled it citing plan text, plan text was
imprecise. Rubric needs: "If the plan requires a phrase that breaks
native Ukrainian pragmatics in the given context, flag it as a PLAN
issue (verdict: plan_revision_request), not a content defect."

**B4.** Cross-agent review isn't enforced for UK track. Gemini
self-reviewed its own M01 writing and scored it +2.4 pts higher than
Codex reviewing the same content. The `SELF_REVIEW_DETECTED` audit
gate exists but either didn't fire or was bypassed by `--force-publish`.
Needs: UK track must block self-review at build time, not only at
audit time.

**B5.** Review rubric has no way to say "plan is wrong, content is
right." Today the reviewer only emits fix blocks for content. When the
problem is upstream (imprecise plan), the fix block is useless. Needs
output format: `<plan_issue>...</plan_issue>` or `verdict:
plan_revision_request` (which already exists in the state machine per
scripts/build/v6_build.py:1336).

---

### C. Wiki pipeline

**C1.** Flash fallback writes some wiki articles when Pro is
unavailable. B1 batch running right now has some Flash-written
articles. They're indistinguishable from Pro-written ones afterwards.
When a later module retrieves from them as "source of truth," we
silently build on degraded content. Need: metadata field
`generated_by_model`, pipeline records which rung succeeded, UI/report
flags Flash articles for Pro rebuild queue.

**C2.** Dim-review is shadow mode only (logs, never blocks). Is that
correct? If yes, rename so nobody thinks it's a gate. If no, promote
to gating with calibrated thresholds (Phase 3 per
`docs/design/dimensional-review.md`).

**C3.** Three bespoke Gemini paths in `wiki/compile.py` that bypass
the fallback ladder (`_send_review` at line 733 when `--review` is
used, rewrite step at line 928 when REVISE verdict fires). Not biting
the current batch (`--review` not set), but scales into problems.

**C4.** Hungarian-minority textbooks contaminated the corpus. Already
fixed today (deleted 2 books, 491 chunks). But: no ingestion filter
exists, so if someone re-ingests textbooks the contamination comes
back. Need: `scripts/corpus/ingest.py` must reject `*uhor*`, `*-rum-*`,
`*-pol-*` patterns + author surnames writing for minority schools.

**C5.** Compile.py skip-check runs AFTER retrieval (#1378, already
tracked). Not blocking but wasteful.

---

### D. Plans

**D1.** Latin M## cross-refs in Ukrainian prose across 183 plans
(a1/a2/b1). `M48`, `M06`, `M37` inside teaching prose. Codex is
fixing via #1392 Phase 1 now.

**D2.** Context-blind `ОБОВ'ЯЗКОВО` patterns. One confirmed (the `А у
тебе?` case). Gemini audited 30 samples and didn't find more, but
sample size is ~16% of the corpus. Full audit needed — probably same
Gemini pass extended to all 183.

**D3.** Homoglyph leaks. `ЗМI` with Latin I confirmed in 1 B1 plan.
Different regex class from M##. Needs full-corpus scan.

**D4.** Plain calques in plan prose. Gemini flagged 5 in 30 samples:
`Давайте обговоримо`, `кожен день`, `приймати ліки`, `близько від`,
`зимний`. Extrapolation: ~30 across 183. Needs sweep, but stylistic
findings need native-reviewer (Alona/Tetiana) confirmation before
mass-apply.

**D5.** Structural defects (duplicate summaries — `a2-067` pulls from
`a2-09`). Pedagogy bug, not just prose. Needs structural audit pass.

**D6.** Russian contamination risk I won't spot by eye. Memory #1
warns my pre-training is Russian-contaminated. Plans written by older
Opus may have subtle issues I'd miss. Needs: MCP-tool-grounded audit
(VESUM + Антоненко-Давидович + Правопис), not eyeballing.

**D7.** "ULP" appearing in plan prose. External-resource titles are
legitimate (brand name) but prose body references like "На основі
епізоду 1 ULP" leak Latin into Ukrainian. Already partly fixed in M01
manually; corpus-wide sweep needed as part of D1.

---

### E. Safety / infrastructure (from Codex adversarial review today)

**E1.** Cooldown concurrency race. `scripts/ai_llm/cooldown.py` uses
tmp+rename atomic write, but two writers hitting same temp path race.
`later-expiry-wins` logic reads pre-race stale state. Minor for
current serial use, real for concurrent builds.

**E2.** Session-file recovery race in parallel Gemini calls. Dim-review
fans out 4 parallel subprocesses; the adapter's `_read_latest_session_response`
takes "newest file" which can be ANOTHER request's answer. On
timeout, dim A can return dim B's JSON as its own result. Latent.

**E3.** Rate-limit classifier completeness. Expanded today (`No capacity
available`, `model is overloaded`, `unavailable`). More patterns may
exist. Needs empirical corpus of real 429-shaped stderrs.

**E4.** Stale contract test in `tests/test_agent_runtime.py` expects
old `auto` semantics (from when I reverted AC1). Minor.

**E5.** Remaining bespoke Gemini paths in `audit/review_plan.py:182`
and `audit/checks/naturalness.py:108`. Don't bite current batch but
same pattern as C3. Phase 2 of #1384.

**E6.** Heal loop budget exhaustion is a distinct failure mode from
B1 above. Even if heal PATCHED, a plan that legitimately needs 5+
fixes would hit the 3-round budget. Need: configurable max-rounds
per-track, or a "plan revision request" exit when rounds plateau.

---

### F. Architecture decisions needing explicit resolution

**F1.** Review authority model. Who is allowed to ship a module? Pick one:
- Alona alone (native-speaker canon, pipeline is advisory)
- Pipeline ≥9 AND Alona sign-off
- Pipeline ≥8 AND Alona veto window
- Alona does UK-canonical, pipeline does English-track

**F2.** Fallback model policy. Pick one:
- Pro-only for wikis/research (block Flash)
- Flash acceptable for drafts, flagged for Pro rebuild
- Flash acceptable with disclaimer in metadata
- Any rung acceptable, metadata tracks provenance

**F3.** UK-track destination path. (Same as A1 — needs decision.)

**F4.** Writer→Reviewer matrix per track. UK-canonical showed Codex
is a better reviewer than Gemini for Ukrainian pragmatics. Should UK
track have fixed `writer=gemini, reviewer=codex`, or stay cross-agent
by rotation?

---

### G. Agent / tooling (minor but real)

**G1.** `ask-codex` bridge command runs in read-only sandbox, can't
execute code. Using it for implementation work returns useless
responses. Only `delegate.py dispatch` does actual work. Document this
in the tool-selection memory more explicitly.

**G2.** Daily Gemini API quota burns fast if cooldown is absent.
Mitigations landed today; needs monitoring / budget dashboard.

---

## Part 2 — Priority matrix

|  | **P0: Blocks Alona pilot** | **P1: Blocks scale-up** | **P2: Defer** |
|---|---|---|---|
| **Track arch** | A1 (UK path), A2 (ADR), F3 | | |
| **Review pipeline** | B1 (heal-patch), B2 (word count), B3 (plan-prose enforcement), B5 (plan-issue verdict) | B4 (cross-agent enforce) | |
| **Wiki** | | C1 (Flash tracking), C4 (ingest filter) | C2 (dim gate decision), C3 (wiki bespoke paths), C5 |
| **Plans** | D1 (Codex #1392 running), D3 (homoglyph, add to #1392) | D2 (full ОБОВ'ЯЗКОВО audit), D4 (calques), D5 (structural), D6 (Russian audit), D7 | |
| **Safety** | | E5 (unify Gemini paths) | E1, E2, E3, E4, E6 |
| **Architecture** | F3 (= A1) | F1 (review authority), F2 (fallback policy), F4 (writer-reviewer matrix) | |
| **Tooling** | | | G1, G2 |

**P0 count:** 10 items. These gate the 4-lesson pilot.
**P1 count:** 11 items. These gate batching A1/A2 at scale.
**P2 count:** 10 items. Real but can run in background.

---

## Part 3 — Proposed sequencing (user's dependency chain applied)

### Phase A: Architecture decisions (YOU, not agents)
Cannot be delegated.
- **F3/A1**: UK-track destination path — you pick
- **F1**: review authority — you pick (likely "Alona canonical, pipeline advisory")
- **F2**: fallback model policy — you pick
- **F4**: writer-reviewer matrix for UK — you pick

These are 1-4 hour decisions. Block everything downstream. I draft a
decision memo per item; you approve.

### Phase B: Plan review & fix (Codex + Gemini, in parallel)
Depends on Phase A only for F3 path decisions.
- **D1** (Codex, #1392 running) — Latin M## sweep
- **D3** (extend Codex brief) — homoglyph scanner
- **D2** (Gemini) — full context-blind ОБОВ'ЯЗКОВО audit across 183 plans
- **D4/D7** (Gemini) — calque sweep, needs Alona confirmation before apply
- **D5** (Gemini + Codex) — structural audit for duplicate sections
- **D6** (Gemini with MCP tools) — Russian contamination audit

### Phase C: Wiki review & fix (Codex + Gemini)
Depends on Phase B? No — can run in parallel since wikis are already
compiled and plans retrieve from them, not the other way around.
- **C1** (Codex) — add `generated_by_model` metadata, flag Flash articles
- **C4** (Codex) — ingest filter for minority textbooks
- **C2** (decision, then implement) — dim-review: enforce or delete
- **C3** (Codex, Phase 2 of #1384) — unify wiki Gemini paths through ladder

### Phase D: Review pipeline fixes (Codex)
Must complete before module builds scale.
- **B1** (Codex) — heal loop PATCH not REGENERATE
- **B2** (Codex) — word-count rubric correction
- **B3/B5** (Codex) — plan-issue verdict separate from content-issue
- **B4** (Codex) — self-review enforcement at build time

### Phase E: Pilot 4-lesson rebuild (after A, B, D; C optional)
Run M01/M08/M38/A2-M02 with:
- Clean plans (B complete)
- UK-canonical destination (A complete)
- Patched heal loop + fixed rubric (D complete)

Send to Alona. Her review is canon.

### Phase F: Scale-up batch (after E + Alona sign-off)
Full A1 + A2 Ukrainian-canonical build.

### Phase G: English A1/A2 rebuild (after F, using enriched corpus)
Per the original corpus-bootstrap plan. This is the destination of
the whole pipeline.

---

## Part 4 — Ownership proposal

| Agent | Scope | Why |
|---|---|---|
| **Krisztian** | Phase A decisions (F1-F4) | Not delegable — project thesis and authority model are yours |
| **Claude (me)** | Oversight: filing issues, writing briefs, integrating adversarial review, posting status to GH | Strategic/glue work — no bulk writing |
| **Codex** | Phase B mechanical (D1, D3, D5), Phase C infrastructure (C1, C4), Phase D (B1-B5) | Deterministic code/regex work where it excels; cross-agent vs Gemini content |
| **Gemini** | Phase B audit (D2, D4, D6) | Native-language pragmatic judgment (better than Codex for linguistic nuance) |
| **Alona (Tetiana-backup)** | Confirm D4 calques before mass-apply; final Phase E pilot review | Native speaker, canon for register decisions |

**Claude constraints I commit to:**
- No bulk content writing. Content = Gemini/Codex.
- No adapter-level or pipeline-internal LLM calls outside the ladder.
- Any non-trivial action states: issue # + AC + expected artifact path BEFORE the first command.
- When I discover a defect: file the issue FIRST, then decide if fixing is in scope.

---

## Part 5 — Open questions for Codex/Gemini adversarial review

1. **Am I missing a whole category?** Content distribution, curriculum scope, localization, accessibility, licensing, monitoring/analytics — anything here that should be in the inventory but isn't?

2. **Is the sequencing right?** Does B (plans) really need to finish before D (review pipeline fixes)? Could they run in parallel safely? What's the real dependency?

3. **P0/P1/P2 priority calls** — which ones would you push higher or lower?

4. **UK-track destination decision (F3)** — what are the trade-offs of the 4 options? Which is lowest-risk for a pilot?

5. **Review authority (F1)** — Alona alone vs gated-with-Alona-veto. What have other L2 corpora projects done?

6. **Phase B bottleneck** — Gemini auditing all 183 plans for Russian contamination (D6) at ~5s/plan + tool calls = ~30-60 min but will probably need multiple passes. Is there a faster approach?

7. **Any findings from today we didn't capture here** that you'd add?

---

## Appendix: commits landed 2026-04-21

- 67ddd96cd, 863ed7524, b0b8c1e26, bd5adf85a — M01 pipeline work + snapshots
- 811a089a4 — UK activities schema contract
- 805f67413, a43bc6e70, 8fdec493f, d30e883ed, fac3002de — #1384 Gemini ladder/cooldown series
- 8e9c0be85 — worktree enforcement rule
- d4a18623d — pilot_uk_lesson.py initial
- fdfca8565 — wiki compile observability
- 744427521 — Gemini fallback ladder (Codex)

Current worktrees:
- `codex-1392-plan-latin-fix` (Codex running Phase 1, PID 80120)

Open issues:
- #1381 chunk cache (closed — landed)
- #1384 Gemini ladder/cooldown (Phase 1 landed, Phase 2 open)
- #1385 UK pipeline (merged, pilot smoke partial)
- #1392 plan audit (Codex running Phase 1)
- #1377 wiki expansion (assigned user)
- #1378 compile skip-check order
- #1379 CLI --help standard
- #1380 compile.py dead code
- #1383 delegate --worktree enforcement (landed)
