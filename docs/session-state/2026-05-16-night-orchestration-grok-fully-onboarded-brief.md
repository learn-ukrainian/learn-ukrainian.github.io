---
date: 2026-05-16
session: "Overnight orchestration session 2026-05-16 ~22:00 → ~02:30 UTC. Goal: 'green m20 after grok is fully onboarded.' Achieved: Grok 4.3 FULLY onboarded (all 5 stages, --writer grok-tools live in V7); m20 dramatically improved (19/22 substantive gates GREEN, best build to date) but not 100% GREEN — 3 content-level gates remain RED with concrete fix paths captured in #2032. 6 PRs merged, 5 follow-up issues filed, 1 dispatch lesson encoded."
status: green
main_sha: 02c448d859
main_green: true
open_prs: [2006, 2000, 2018]
active_dispatches: 0
worktrees_open: 5  # main + 1 m20-failed-build (preserve for #2032) + 3 user/other
agents: [claude, codex, gemini, grok-4.3, hermes]
filed_today: [2027, 2028, 2029, 2030, 2032]
merged_today: [2020, 2021, 2025, 2019, 2031, 2033]
closed_today: [2024]
opened_today: [2025, 2026, 2031, 2033, 2020, 2021]
hermes_config: medium
next_p0: |
  THREE SMALL FIXES TO GET m20 GREEN — concrete fix paths in #2032.

  All 3 fixes total ~25 LOC + 2 tests. One Codex dispatch can ship them.

  ### Fix 1 (smallest, structural) — reviewer-anchor-leak in `_vesum_gate`
  When the codex-tools dim-reviewer's `<fixes>` block has an anchor that
  doesn't match (per `reviewer_fixes_anchor_unmatched` event), the bogus
  anchor leaks into the gate's `missing` list as if the writer emitted it.
  Fix: don't include reviewer-fix-anchor strings in `missing` when the
  anchor failed to match. ~10 LOC in `scripts/build/linear_pipeline.py` +
  1 test. Removes the `двоколонкова` false-positive.

  ### Fix 2 (smaller, plan-only) — m20 plan citations
  `curriculum/l2-uk-en/plans/a1/my-morning.yaml` cites Захарійчук Grade 4
  pages 162/163 (NOT in corpus per #1901). Should be Grade 1 sources from
  `1-klas-bukvar-zaharijchuk-2025-1`. PR #2014 supposedly fixed this but
  apparently swapped to other still-wrong pages — re-verify against actual
  corpus before swapping. Pure YAML edit. Removes `textbook_grounding HARD`.

  ### Fix 3 (small, structural) — warning-quote strip in `_strip_metalinguistic`
  Writer's pedagogical pattern `not "дивюся"` (showing the wrong form in
  quotes after `not`) is not recognized by the gate. Same class as the
  `<!-- bad -->` HTML-marker fix that PR #2019 shipped, but for the prose
  quoted form. Add regex: `r'\\bnot\\s+["«][^"»]+["»]'` (or equivalent)
  to `_strip_metalinguistic`. ~5 LOC + 1 test. Removes `дивюся` false-positive.

  ### After fixes ship
  Re-run m20: `.venv/bin/python scripts/build/v7_build.py a1 my-morning --worktree --writer claude-tools` (Monitor tool on JSONL stream).

  If green: copy module to `curriculum/l2-uk-en/a1/my-morning/` per the V7
  publication pattern. Phase 2b A1 m01-m07 batch can resume.

  If only `long_uk_ceiling` remains: that's content-quality (writer needs
  to add gloss to long UK runs). Decide gate-threshold vs writer-prompt.

  ### CARRY-OVER (not blocking)

  - **PR #2018-equivalent for grok-tools as writer** — Stage 3 plumbing
    is in main but no V7 build has actually been run with `--writer
    grok-tools` yet. After m20 GREEN with claude-tools, run an A/B build
    with grok-tools to compare output quality + cost. The proxy is also
    available at `:8767` for any tool wanting Grok inline.
  - **4 OpenAI-proxy follow-ups** filed tonight from Gemini-3.1-pro
    adversarial review:
    - **#2027 HIGH**: ARG_MAX/E2BIG vulnerability when prompt > ~256KB
      (3 of 4 backends pass via argv; should use stdin)
    - **#2028 HIGH**: 422 envelope spec violation (FastAPI default
      `detail` array doesn't match OpenAI `error` shape)
    - **#2029 MED**: /healthz forks 4 subprocesses per request (DoS surface)
    - **#2030 LOW**: --host accepts non-localhost without explicit flag
  - **PR #2006** (Russianism judge production harness) DIRTY rebase still
    pending; Grok harness reads from `origin/pr-2006` directly so doesn't
    block but should land eventually
  - **#2018 itself** can be CLOSED (closed by PR #2031 — verify the issue
    body's acceptance criteria are met, then close)
  - **Issue #2022/#2023** (proxy Gemini 3.0 route + Claude --bare auth)
    were filed by Codex during the proxy dispatch — separate Phase 2 work
---

# Brief — 2026-05-16 — Grok 4.3 fully onboarded; m20 19/22 GREEN

> Predecessor: `2026-05-16-grok-4.3-onboarding-complete-handoff.md` (this
> night session opened from there with 4 of 5 Grok stages done; tonight
> closed Stage 3 + made major m20 progress).

## TL;DR

User asked for "green m20 after grok is fully onboarded." Outcome:
- **Grok 4.3 FULLY onboarded** — all 5 stages done; `--writer grok-tools`
  is live in V7 (PR #2033), `--reviewer grok-tools` too, OpenAI-compat
  HTTP proxy at `:8767` (PR #2025) routes `model: grok-4.3` via Hermes.
- **m20 dramatically improved** — 19/22 substantive gates GREEN (best
  build to date), but not 100%. Three concrete fixes captured in #2032
  totaling ~25 LOC + 2 tests; one Codex dispatch can ship them.

6 PRs merged tonight. 5 follow-up issues filed. 1 dispatch lesson
encoded (#M-8 rescue protocol fired too eagerly → duplicate PR #2024).

## What shipped tonight (6 PRs merged)

| PR | What | LOC |
|---|---|---|
| #2020 | Deploy preflight `tmp/` orphan declaration | +3 |
| #2021 | Grok 4.3 onboarding harness + 4-round calibration + 5-stage probe | +1,901 |
| #2025 | OpenAI-compat HTTP proxy at `:8767` (Codex / Gemini / Claude / Grok-via-Hermes) | +634 |
| #2026 | Vesum-gate test fixes (3 failing tests → green) — stacked into #2019 | +81 |
| #2019 | m20 gate + writer-prompt: Russianism HTML markers + bold-strip + 2-step textbook retrieval | +160 |
| #2031 | activity_schema gate runs first, rejects forbidden field aliases (closes #2018) | +387 |
| #2033 | grok-tools writer family via Hermes adapter (Stage 3 closer) | +463 |

Closed: #2024 (orchestrator-rescue duplicate of #2025 — see lesson below).

## Live infrastructure now

- **`:8765`** Monitor API — state queries (existing)
- **`:8767`** OpenAI-compat proxy — chat completions for codex / gemini-3.0-flash-preview / gemini-3.1-pro-preview / claude-opus-4-7 / claude-sonnet-4-7 / grok-4.3 (NEW tonight)
- **`ab` CLI** — channels / discuss / ask-X (existing)
- **V7 writer surface**: `--writer {claude-tools,gemini-tools,codex-tools,grok-tools}` (grok-tools added tonight)
- **V7 reviewer surface**: same 4 families

## Grok 4.3 onboarding — full status

| Stage | What | Status |
|---|---|---|
| 1 | Judge calibration (4 rounds × medium/high/xhigh × ±MCP) | ✅ done (#2021) |
| 2 | Code-gen probe | ✅ done (#2021) |
| 3 | V7 module writer plumbing (`--writer grok-tools`) | ✅ done (#2033) |
| 4 | `<fixes>` reviewer probe | ✅ done (#2021) |
| 5 | Hallucination probe (3/3 refusals) | ✅ done (#2021) |

**Production recommendations** (from #2021's CONSOLIDATED-REPORT.md):
- Cleanliness classifier: STRONG (case_acc 91.7% at medium+MCP)
- Second-opinion validator: STRONG (precision 85%)
- Code reviewer: STRONG candidate (caught #2018 in PR review test, plus 3 regex edge cases I missed)
- Honesty: STRONG (effort-independent 3/3 refusals)
- V7 module writer: PLUMBED but not yet validated end-to-end (Phase F follow-up — A/B against claude-tools after m20 GREEN with claude-tools)

**Cost**: $0.20/M input, $0.50/M output — ~75× cheaper than claude-opus on input, 150× cheaper on output. ~19s/call typical.

**Hermes integration path locked in:**
- Auth via `hermes auth add xai-oauth`
- Direct `api.x.ai/v1/...` calls return 403 (OAuth scope is session, not bearer)
- Use `hermes -z PROMPT -m grok-4.3` subprocess
- MCP registration: `hermes mcp add sources --url http://127.0.0.1:8766/mcp`
- For headless reasoning level: edit `~/.hermes/config.yaml` line ~52 (`agent.reasoning_effort: medium`) — **medium is BEST for code-gen on Grok**, NOT high or xhigh per onboarding finding

## m20 status — 19/22 substantive gates GREEN

Build #9 (worktree `.worktrees/builds/a1-my-morning-20260515-235548/`,
preserve for #2032 reproduction):

### Gates passing (19) — including the new activity_schema

✅ **activity_schema** (PR #2031 working — writer used canonical `error:` fields this build, no aliases)
✅ word_count, plan_sections, formatting_standards
✅ citations_resolve, resources_search_attempted, immersion_advisory
✅ l2_exposure_floor, component_density, inject_activity_ids
✅ activity_types, ai_slop_clean, component_props
✅ russianisms_clean, surzhyk_clean, calques_clean, paronym_clean
✅ previously_passed_regression

### Gates failing (3) — content-level, NOT structural

❌ **vesum_verified** — 2 false positives:
   - `дивюся` (writer's pedagogical `not "дивюся"` warning quote — gate doesn't recognize quoted negative-example)
   - `двоколонкова` (REVIEWER hallucination — codex-tools dim-reviewer's `<fixes>` anchor doesn't match text `двоколонна`; bogus anchor leaks into missing list)

❌ **textbook_grounding HARD** — plan cites Захарійчук Grade 4 p.162/163 (NOT in corpus per #1901). Need Grade 1 swap.

❌ **long_uk_ceiling** — UK runs > 28 words without close gloss.

⚠️ mdx_render: not-run cascade.

Full diagnosis + fix paths: **issue #2032**.

## What's NOT done

| Item | Why | Effort |
|---|---|---|
| m20 GREEN | 3 content-level fixes remain (#2032) | ~25 LOC + 2 tests, 1 Codex dispatch |
| V7 build with `--writer grok-tools` | plumbing landed but no actual build run | 1 m20 build × ~20 min |
| 4 proxy Phase-2 follow-ups | filed tonight, deferred (#2027 HIGH, #2028 HIGH, #2029 MED, #2030 LOW) | varies |
| Phase 2b A1 m01-m07 batch | gated on m20 GREEN | per module ~20 min |
| Issue #2018 close-out | PR #2031 closes it, but issue still open | ~30s `gh issue close 2018 --reason completed` |
| Grok OCR PoC for ESUM (issue #2001) | user-mentioned; deferred (Hermes vision toolset enabled, but no probe run yet) | ~30 min for 10-page test |

## Dispatch lesson encoded — #M-8 rescue too eager

**Failure:** I rescued the OpenAI-compat proxy dispatch (PR #2025) at
T+1-2min after `status=done`, before Codex finished its push/PR-create
step. Codex then opened PR #2024 with the same commit `db04f07bed`,
creating a duplicate PR I had to close.

**Pattern:** `delegate.py status` reports `done` when the wrapper's
silence_timeout fires or the worker exits — but Codex's push + PR-create
sometimes happens AFTER that signal. The 1-2 min rescue window is too
short.

**Encoded fix (applied to subsequent dispatches tonight):** wait at
least 5 min after `status=done` before applying #M-8 rescue protocol.
Re-check `gh pr list --search "head:codex/<task-id>"` and
`git ls-remote origin <branch>` 2-3 times across the 5-min window. Only
rescue if both remain empty after the window.

This pattern was successfully applied to Phase C (#2031) and Phase E
(#2033) tonight — both Codex dispatches DID push and open PRs cleanly
without rescue, validated by waiting longer.

To formalize: add a `--rescue-after Ns` knob to `delegate.py status`
that waits N seconds after `done` before reporting "no PR opened" —
removes the orchestrator's manual countdown burden. Filed as carry-over
not blocking.

## What looks great

- **kubedojo's parallel research** (shared mid-session) showed
  Gemini-3.1-pro is the strongest reviewer (2/2 #1229 bugs caught).
  Used it for proxy review — it caught 4 real findings (#2027-#2030)
  including 2 HIGH-severity bugs that 11 mocked tests missed
  (ARG_MAX argv, 422 spec violation).
- **Phase C dispatch pattern**: the activity_schema gate empirically
  validated — writer used canonical `error:` fields on first attempt
  in m20 build #9, zero forbidden aliases. Either the schema-gate
  diagnostic in correction round taught the writer, or the writer
  happened to produce canonical fields without prompting. Either
  way, structural gate is doing its job.
- **OpenAI-compat proxy live with all 4 backends working** — `/healthz`
  returns `{ok:true, backends:{codex:true, gemini:true, claude:true,
  hermes:true}}`. Live curl round-trips against codex/grok-4.3/
  gemini-3.1-pro all return correct PONG/4 responses.

## Worktrees alive at handoff

```
main                                                                    02c448d859 [main]
.worktrees/2006-trigger                                                 1dd8d29524 [feat/russianism-judge-production]   ← user/other (PR #2006)
.worktrees/codex-interactive                                            2eb62691d4 (detached HEAD)                      ← user/other
.worktrees/dispatch/codex/pr2-ua-gec-bulk-lookup-2026-05-15             46ffc47291 [codex/pr2-ua-gec-bulk-lookup]       ← user/other (PR #2000)
.worktrees/builds/a1-my-morning-20260515-235548/                        FAILED-BUILD-PRESERVED-FOR-#2032                ← DO NOT DELETE — diagnostic for night handoff
```

Plus the 3 dispatch worktrees from tonight (`.worktrees/dispatch/codex/`)
were `git worktree remove --force`'d after PR merges. Branches deleted
locally.

## Untracked files at handoff

```
audit/2026-05-16-openai-proxy-gemini-review/REPORT.md   # Gemini-3.1-pro review of PR #2025; orphan but useful — keep
docs/dispatch-briefs/2026-05-16-2018-activity-schema-gate-codex.md       # used in #2031, can archive
docs/dispatch-briefs/2026-05-16-grok-stage-3-writer-plumbing-codex.md    # used in #2033, can archive
docs/dispatch-briefs/2026-05-16-openai-compat-bridge-proxy-codex.md      # used in #2025, can archive
docs/dispatch-briefs/2026-05-16-pr2019-vesum-gate-test-failures-codex.md # used in #2026, can archive
docs/dispatch-briefs/2026-05-16-pr2025-proxy-adversarial-review-gemini.md # used in Gemini review, can archive
docs/session-state/2026-05-16-night-orchestration-grok-fully-onboarded-brief.md # THIS FILE
```

Recommended cleanup: commit the dispatch briefs as `chore(docs): archive 2026-05-16 night dispatch briefs` — they're useful as reference for the night's pattern but don't need to live untracked.

The Gemini review report at `audit/2026-05-16-openai-proxy-gemini-review/REPORT.md` is the single canonical source for the 4 follow-up issues — keep it tracked.

## How to start the next session

1. Read this brief.
2. Cold-start orient via Monitor API.
3. Quick win: `gh issue close 2018 --reason completed --comment "Closed by PR #2031 (activity_schema gate). Verified empirically in m20 build #9 — writer used canonical error: fields, zero forbidden aliases. See #2032 for remaining m20 content-level gates."`
4. Decide on the m20-GREEN dispatch: write a brief covering the 3 fixes from #2032 in one Codex run, fire it.
5. While Codex works on the 3 fixes: commit the night's dispatch briefs (`chore(docs)`) and clean up untracked.
6. After fixes merge: re-run m20 build with claude-tools (`v7_build.py a1 my-morning --worktree`). Monitor JSONL events.
7. If GREEN: ship to `curriculum/l2-uk-en/a1/my-morning/`. Then queue Phase 2b m01-m07 batch.
8. If still RED on `long_uk_ceiling`: that's content-only — file follow-up + decide gate-threshold-vs-writer-prompt.
9. Once m20 ships: A/B build with `--writer grok-tools` to validate Stage 3 end-to-end. Compare cost + content quality.
10. The 4 proxy Phase-2 follow-ups (#2027 #2028 #2029 #2030) can be batched as one Codex dispatch (~30-60 min).

## #M-* lessons from tonight

- **#M-4 (deterministic over hallucination):** held. Every PR merge backed by raw pytest output + raw curl output for live infrastructure. Issue #2032 quotes raw event traces and gate output for each failure class.
- **#M-5 (never print secrets):** held. The user noted mid-session they'd reconfigured `gh` setup so agents no longer need the GH_TOKEN env var — closed a recurring leak surface.
- **#M-6 (drive priorities):** mostly held. One menu-shaped question early on ("which test gap do you mean?") was appropriate (genuine ambiguity between Stage 3 vs full-pytest vs both interpretations of "finish the tests"). All other decisions driven inline.
- **#M-7 (pytest before push):** held. Every code change ran targeted pytest before commit; the wider sweep ran post-merge.
- **#M-8 (orchestrator-active through dispatch lifecycle):** REFINED tonight. The original protocol's 1-2 min rescue window after `status=done` is too short — caused the duplicate PR #2024. New refined pattern: 5-min wait + 2-3 re-checks of `gh pr list` + `git ls-remote` before rescue. Held cleanly for Phase C and Phase E afterwards.

## New patterns / observations to consider for MEMORY

| Pattern | Worth promoting to MEMORY? |
|---|---|
| 5-min rescue window (vs 1-2 min) for #M-8 | **YES** — refines #M-8's existing rule with empirical evidence from PR #2024 incident |
| Gemini-3.1-pro is the strongest reviewer per kubedojo data (2/2 vs Codex 1/2 vs Grok 0/2 on bug-catch) | YES — refines #M0 routing for adversarial-review lane |
| `reasoning_effort=high` is WORSE than medium for both Grok (onboarding study) AND code-gen (kubedojo bonus) | YES — generalize beyond Grok-specific note |
| OpenAI-compat HTTP proxy at `:8767` is the new shared-fleet entrypoint | YES — add to TOOL SELECTION row |

---

*Format: MD per #M-2 (ai → ai). Companion: 6 dispatch briefs in
`docs/dispatch-briefs/2026-05-16-*.md` (5 successful dispatches + 1
brief that was used directly inline by orchestrator for issue #2032
diagnostics).*
