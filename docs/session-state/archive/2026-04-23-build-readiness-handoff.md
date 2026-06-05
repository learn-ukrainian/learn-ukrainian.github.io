# Session Handoff — 2026-04-23 build readiness (pre-build gate)

> **Status:** PRE-BUILD HOLD. 7+ hours of infra + lock work landed. **Zero modules built.** User explicitly pulled brakes on rushing into builds before the per-dim reviewer + smoke-test gates clear. Honest accounting of what's done vs what's left below.

## Where we ARE (main at the time of handoff)

`main = 8338218e24` (post `colors` review-and-lock merge)

### Landed tonight (7 PRs + 4 doc/rules commits)

| Item | Closes |
|---|---|
| #1407 — Gemini API leak fix (batch_gemini_runner → adapter) | #1406 |
| #1408 — `delegate.py` rate-limit misclassification | #1404 |
| #1411 — MCP `search_sources` — wikis wired into v6 writer | #1410 |
| #1413 — Scenario-aware excerpt selection (H2 split + bonus + trace) | #1282 |
| #1414 — CI red repaired (jsonschema + trufflehog + yamllint + radon) | #1405 |
| #1415 — at-the-cafe wiki + plan LOCKED + rubric template | #1412 |
| #1417 — food-and-drink LOCKED | (scale batch 1) |
| #1418 — my-family LOCKED | (scale batch 1) |
| #1419 — sounds-letters-and-hello LOCKED | (scale batch 1) |
| #1420 — colors LOCKED | (scale batch 1) |
| `da26c85f00` — `docs/best-practices/strict-reviewer-persona.md` (canonical, NEVER ask user to re-explain) | n/a |
| `76f031a20a` — `non-negotiable-rules.md` §5 codifies per-dim independent + MIN-score gate | n/a |
| `431194514b` — MIN-score gate threshold dropped 9 → 8 (user 2026-04-23) | n/a |
| Earlier today — Gemini always-subscription policy | #1416 |

### Roadmap state per EPIC #1365 Phase 2 Track A

- ✅ A.4 corpus engineered (`ukrainian_wiki` table + FTS5 + admission gate)
- ✅ A.5 wikis compiled for A1 (55 articles)
- ✅ A.6 wikis ingested (1424 chunks, 55 A1 + 69 A2)
- ✅ wire-up: `search_sources` MCP tool exposes ukrainian_wiki to writer (#1411)
- ✅ excerpt selection improved (#1413)
- ✅ writer prompt hardened (#1401, earlier today)
- ✅ Gemini bridge unblocked (always-subscription, #1416)
- ✅ CI clean (#1414)
- ⚠️ Inputs LOCKED: **5 of 55** A1 plans + wikis (at-the-cafe, food-and-drink, my-family, sounds-letters-and-hello, colors) — 9% of A1
- ⏳ A.7 native-reviewer engagement — user-owned, not yet started
- ⏳ A.8 canary measurement — **cancelled twice** awaiting per-dim reviewer
- ⏳ A.9 batch rebuild — gated on A.8 PASS

## What is IN FLIGHT right now

| Task ID | Agent | What | Hard timeout |
|---|---|---|---|
| `scale-hey-friend-review-and-lock` | Claude opus 4.7 xhigh | Lock A1 hey-friend wiki + plan | 5400s |
| `scale-my-day-review-and-lock` | Claude opus 4.7 xhigh | Lock A1 my-day wiki + plan | 5400s |
| `scale-shopping-review-and-lock` | Codex | Lock A1 shopping wiki + plan | 5400s |
| `scale-holidays-review-and-lock` | Codex | Lock A1 holidays wiki + plan | 5400s |
| `codex-per-dim-reviewer-refactor-v2` | Codex | Refactor v6 reviewer to per-dim independent + MIN ≥ 8 aggregator | 10800s |

Monitors:
- `b71h08ifk` — scale batch 2 completions
- `bwd7abztr` — per-dim reviewer refactor completion

## ZERO modules built tonight

Honest accounting: tonight is **input-side work only**. Plans + wikis locked, infrastructure unblocked, persona/rules codified. **Not a single new A1 or A2 module rendered to .mdx.** The starlight site at `localhost:4321` (user has it running) shows pre-tonight stale content for the 5 locked slugs — none of tonight's quality lift is visible there yet.

## Why builds haven't started — the readiness gate user named

User pulled brakes 2026-04-23 ~01:50 CEST. Their question "are we ready for building?" surfaced these UNTESTED end-to-end-together pieces:

| Piece shipped tonight | Tested by full build? |
|---|---|
| `search_sources` MCP tool | **No** — no build has called it yet |
| Excerpt selection refactor (H2 split + scenario bonus) | **No** — no build has used it yet |
| Plan lifecycle fields (`lifecycle/reviewed_at/reviewed_by/review_notes`) | **No** — does v6_build / audit / writer-prompt tolerate these? Schema is `additionalProperties: true` per Codex but never exercised |
| Always-subscription Gemini policy | **No** — no build run after the flip |
| Per-dim reviewer + MIN ≥ 8 gate | **NOT YET SHIPPED** (refactor in flight) |

Plus the deeper concern: building NOW means reviewing with the single-pass weighted-average reviewer the user explicitly rejected. Modules could PASS at avg 8.5 with a single dim at 6 → published modules would lie about quality.

## The build-readiness checklist (do these BEFORE firing builds)

1. **Wait for + merge per-dim reviewer refactor PR** (in flight, hard timeout 3h). After this lands, MIN-score gate is enforced in the live pipeline, not just in docs.
2. **Smoke-test `mcp__sources__search_sources`** — call it directly (Python or MCP client) with a realistic A1 query like "сім'я" or "кольори"; verify response includes ukrainian_wiki rows.
3. **Verify audit pipeline tolerates new plan lifecycle fields** — load any locked plan (e.g., `curriculum/l2-uk-en/plans/a1/at-the-cafe.yaml`) through `scripts/audit_module.py` or whatever the audit entrypoint is. Confirm no schema rejection.
4. **Smoke build on ONE slug** — pick the lowest-risk locked slug (likely `colors` — simple vocab, small surface area). Run `v6_build.py a1 <module-num> --force` end-to-end. Verify:
   - Phase progression (check → research → skeleton → write → exercises → annotate → enrich → verify → review → publish) all complete
   - Per-dim reviewer fans out + MIN-aggregates correctly
   - Audit gate accepts the per-dim aggregate
   - Published .mdx renders correctly in `starlight/src/content/docs/a1/colors.mdx`
   - User can see new content at `http://localhost:4321/a1/colors`
5. **Only AFTER smoke passes** — fire 4 parallel builds (the other 4 locked slugs). Hard timeout 5400s each. Codex (request-billed, parallel-friendly).
6. **A.8 canary** as a separate explicit measurement against the new reviewer — re-fire the dispatch we cancelled (codex-a8-canary-execute) but updated to reference the new reviewer architecture. PR opens with verdict.

## Other open work

- Open issues: ~63 (down from 76 today; 14 closed today; need to triage older `#12xx` items eventually)
- 5 worktrees: `scale-{hey-friend,my-day,shopping,holidays}` + `codex-per-dim-reviewer` + main
- Local has uncommitted noise: `.claude/phases/gemini/*` modified-vs-origin from earlier `claude:deploy` — non-blocking, reconcile in next clean pass
- 4 untracked scale-batch-2 brief files in `.worktree-briefs/` — keep for dispatch records, can stage on next commit

## Behavioral lesson captured

7+ hours of careful infra/lock work with zero delivered output is **disproportionate**. The user pulled brakes because the right pattern is:
- Build the smallest meaningful end-to-end vertical (1 locked slug → 1 built + reviewed + published module)
- Verify it works
- THEN scale horizontally (lock + build remaining slugs in parallel)

I went horizontal-first on locks (5 slugs locked) without proving the vertical works (0 slugs built). User correctly identified this as fucking around.

Recorded in this handoff so the next session doesn't repeat it. Adding a memory rule: **before firing parallel infrastructure work, prove the end-to-end vertical first on ONE example.**

## When you (returning user or next session) resume

1. Cold-start via Monitor API per `workflow.md`
2. Check this handoff (`docs/session-state/2026-04-23-build-readiness-handoff.md`)
3. Check the in-flight dispatch status (5 tasks, see above)
4. Walk the build-readiness checklist (steps 1-6)
5. ONLY when smoke build passes → continue scaling

## Operational state at handoff

- main: `8338218e24` (will be ahead by some commits if scale batch 2 + reviewer refactor have landed by then)
- worktrees: 5 (main + 4 scale + 1 reviewer-refactor)
- open PRs: 0 at this moment (will grow as in-flight dispatches land)
- open issues: ~63
- starlight dev server: running per user
- gemini Keychain: user needs to click "Always Allow" once on the popup if it appears
