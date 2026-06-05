# Session Handoff — 2026-04-23 overnight: scale batch 1 in flight

> **Status:** ACTIVE — main session continues as orchestrator while user sleeps. 4 review-and-lock dispatches running in parallel on next batch of A1 slugs.

## Where we ended the day (2026-04-22 → 2026-04-23 night)

Main at **`4f0fae3c0b`** — 7 PRs landed in the late-night session, all roadmap-blocking infra cleared:

| PR | What | Closed |
|---|---|---|
| #1407 | Gemini API leak fix (batch_gemini_runner → adapter) | #1406 |
| #1408 | delegate.py rate-limit misclassification | #1404 |
| #1411 | MCP `search_sources` tool — wikis wired into v6 writer | #1410 |
| #1413 | Scenario-aware excerpt selection (H2 split + bonus) | #1282 |
| #1414 | CI red repaired (jsonschema + trufflehog + yamllint + radon) | #1405 |
| #1415 | at-the-cafe wiki+plan LOCKED + rubric template | #1412 (partial — AC-4 deferred) |
| `4f0fae3c0b` | Gemini always-subscription policy (Keychain blunt fix) | #1416 |

**Roadmap state per EPIC #1365:**
- ✅ Wikis ingested (1424 chunks)
- ✅ Wikis wired to writer (search_sources MCP)
- ✅ Excerpt selection improved
- ✅ at-the-cafe canary inputs LOCKED
- ✅ CI clean
- ✅ Gemini bridge unblocked (subscription always)
- ⏳ A.8 canary measurement — **ready to run** (not yet executed; user runs builds per memory rule)
- ⏳ Native reviewer engagement (A.7) — user-owned

## Active dispatches — overnight scale batch 1

Applying the at-the-cafe review-and-lock template (`docs/best-practices/wiki-plan-review-and-lock.md`) to the next 4 A1 slugs in parallel.

| Task ID | Agent | Slug | Why this slug |
|---|---|---|---|
| `scale-my-family-review-and-lock` | Claude opus 4.7 xhigh | `my-family` | High-frequency basic content; 5 prior review files (warm start) |
| `scale-sounds-letters-and-hello-review-and-lock` | Claude opus 4.7 xhigh | `sounds-letters-and-hello` | Literacy canary; 6 prior review files (warm start, recent rebuild) |
| `scale-food-and-drink-review-and-lock` | Codex | `food-and-drink` | Dialogue-rich scenario; complement to at-the-cafe |
| `scale-colors-review-and-lock` | Codex | `colors` | Simple A1 vocab; tests rubric on minimal-content case |

All started ~01:30 CEST. Hard timeout 5400s (90 min) each. Briefs at `.worktree-briefs/scale-{slug}-review-and-lock.md`. Monitor task `<task_id>` watching for completions.

**Cross-agent adversarial review enforced** — each brief explicitly bans `ask-gemini` (Keychain block) and routes to `ask-codex` (Claude work) or `ask-claude` (Codex work) instead.

## What main session is doing

- Orchestrator role per MEMORY #2 overnight discipline.
- Monitor watching dispatch completions (1-event-per-completion + `ALL_SCALE_BATCH1_COMPLETE` when done).
- Reviews each PR as it lands (Claude inline review; cleared to merge cleanly-passing PRs given user's explicit "follow the roadmap").
- Will fire scale batch 2 (next 4 A1 slugs) after batch 1 lands cleanly.

## When you (user, returning in the morning) resume

1. **Check what scale batch 1 produced:**
   ```bash
   gh pr list --state merged --search "scale-" --limit 10 --json number,title,mergedAt | jq
   gh pr list --state open --search "scale-" --limit 10 --json number,title
   ```
2. **Inspect the 4 LOCKED plans** — check that lifecycle markers landed correctly:
   ```bash
   for slug in my-family sounds-letters-and-hello food-and-drink colors at-the-cafe; do
     yq '.lifecycle, .reviewed_at, .reviewed_by' curriculum/l2-uk-en/plans/a1/$slug.yaml
   done
   ```
3. **Click "Always Allow" once on the macOS Keychain popup** for `gemini-cli` if it appears — one-time, then no more popups (per #1416 fix).
4. **Run A.8 canary** when ready: full protocol at `docs/architecture/a8-canary-protocol.md`. The canary slug (at-the-cafe) is locked, the wire-up is shipped, the excerpt selection is improved — all the prerequisites are in place.
5. **Continue scaling review-and-lock** to remaining A1 slugs (51 left after batch 1) → then A2 (67 slugs).

## Risks / things to watch

- **Keychain popup:** if user hasn't clicked "Always Allow" yet, gemini-cli (called by anything?) could still prompt. Briefs explicitly ban ask-gemini for adversarial reviews; risk is only if some other code path invokes gemini-cli.
- **Plan schema drift:** at-the-cafe added `lifecycle`, `reviewed_at`, `reviewed_by`, `review_notes` as new top-level fields. If batch 1 dispatches use slightly different naming, future tooling breaks. Cross-agent adversarial review should catch this — verify on merge.
- **Cross-agent review with ask-codex:** Codex reviewing Claude-side work is the right pattern, but if Codex is hot/slow, the dispatch could time out at adversarial-review step. Each dispatch's PR will note if AC-3 was completed or deferred.

## Operational state

- Local: 1 branch (main), 5 worktrees (main + 4 dispatch)
- Remote: 1 branch (origin/main)
- Open PRs: 0 (will grow as batch 1 lands)
- Open issues: 68 (down from 76 today)
- Net today: -8 open issues, -1 open PR, +zero stale branches
- Monitor task watching dispatch state files

## What I will NOT do overnight

- Run any v6_build.py invocation (per MEMORY rule "user runs builds")
- Merge PRs whose adversarial review didn't pass
- File new issues unless a real bug surfaces (no exploratory tickets)
- Touch native-reviewer-related work (A.7 — user-owned)
