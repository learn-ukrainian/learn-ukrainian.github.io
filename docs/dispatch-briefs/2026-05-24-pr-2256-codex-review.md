# PR #2256 — Codex adversarial review

**Date**: 2026-05-24
**Agent**: codex
**Mode**: read-only (no commits — read-and-report only)
**Effort**: high
**Wall budget**: 30 min

## What you're reviewing

PR #2256 `fix(monitor): polish artifacts UI and migrate comms off deprecated endpoints`
Author: cursor (composer-2.5 via dispatch `monitor-api-ui-polish-2026-05-24`)
Branch: `cursor/monitor-api-ui-polish-2026-05-24`
URL: https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/2256
Scope: 11 files, 287 add / 110 del, 743 diff lines.

The orchestrator (Claude) will MERGE based on your verdict. You are the gate.

## Read these files first (in this order)

1. `gh pr view 2256` for description.
2. `gh pr diff 2256 -- scripts/api/images_router.py` — the load-bearing API fix (claimed: "no longer opens every PDF on each list call; was causing 504s in stability tests").
3. `gh pr diff 2256 -- dashboards/artifacts.html` — the biggest UI diff (203/54). Loading skeleton + refresh + filters + type badges + collapsible ops directory.
4. `gh pr diff 2256 -- dashboards/comms.html` — endpoint migration (deprecated `live-activity` → `/api/build/events/*`).
5. `gh pr diff 2256 -- dashboards/audit-dashboard.html` — parchment theme via shared `monitor.css`. Verify CSS class names match what `monitor.css` actually exports.
6. `gh pr diff 2256 -- scripts/build/build_playgrounds.py` — `playgrounds/` → `dashboards/` directory rename. Verify all path references are updated consistently.
7. `gh pr diff 2256 -- tests/test_dashboards.py tests/test_playground_api_stability.py` — verify the test changes actually validate the new behavior (especially the PDF fix).
8. `gh pr diff 2256 -- docs/MONITOR-API.md docs/api-endpoint-consumer-map-2026-05-06.md docs/best-practices/agent-bridge.md docs/best-practices/local-api-server.md` — doc updates should match the implementation changes 1:1.

## Specific concerns to address (verdict-relevant)

### (A) `scripts/api/images_router.py` — the PDF-opening fix

The claim: list call no longer opens every PDF. Verify:

1. Read the OLD code (pre-PR) — `git show main:scripts/api/images_router.py` — what was opening each PDF? Was it PyMuPDF `fitz.open()` in a loop?
2. Read the NEW code — what mechanism replaces it? (Cached metadata index? On-demand load? Database lookup?)
3. **Is there a stale-cache risk?** If the new path reads a cached manifest, what invalidates it when new textbooks are added? Is there a fallback for missing cache?
4. **Does the test actually exercise the fix?** `tests/test_playground_api_stability.py` got +3/-1 lines. Does the new assertion measure "list endpoint completes within X ms" or just "endpoint returns 200"? The latter is insufficient.
5. Confirm `images_router` still returns the same response shape as before — any UI consumer relying on the JSON shape should not break.

### (B) `dashboards/artifacts.html` — XSS / DOM safety

203 additions of HTML/JS. Specifically check:

1. Every dynamic text insertion into the DOM — is it `textContent` (safe) or `innerHTML` (XSS risk)? Search the diff for `innerHTML =` and verify each instance receives only literal HTML or sanitized content, never raw API response strings.
2. Type badges + filter chips — when constructed from API response field values, are they escaped?
3. Collapsible ops directory — verify the toggle handler removes/adds CSS classes rather than re-injecting HTML on each toggle (performance).
4. Refresh button — does it debounce? Or can a user spam it and queue dozens of in-flight fetches?
5. Loading skeleton — does it clean up properly when fetch fails (error state) or only on success (which would leave skeleton forever on failure)?

### (C) `dashboards/comms.html` — endpoint migration correctness

1. The OLD endpoint was `/api/comms/live-activity` (per the handoff "deprecated"). Verify that the NEW endpoint `/api/build/events/*` actually exists and has the response shape this dashboard expects. Check by reading `scripts/api/*.py` for a `/api/build/events` route registration.
2. If the new endpoint is SSE/streaming (Server-Sent Events), verify the dashboard handles connection drops + reconnect.
3. If the OLD endpoint was used elsewhere (not just `comms.html`), this PR may have left orphaned callers. Grep `dashboards/ scripts/` for any remaining `live-activity` references.

### (D) `dashboards/audit-dashboard.html` — parchment theme

1. The diff is 14 add / 19 del — net negative. Verify the dashboard didn't lose functionality, just reused shared `monitor.css` classes. Read `dashboards/monitor.css` (or wherever shared styles live) and confirm the classes referenced in `audit-dashboard.html` actually exist there.
2. If parchment theme uses any CSS custom properties (`--var-name`), verify the `:root` declaration is present.

### (E) `scripts/build/build_playgrounds.py` — directory rename

1. `playgrounds/` → `dashboards/`. Grep the whole repo for any remaining `playgrounds/` references in PYTHON code (`grep -rn "playgrounds" scripts/ tests/`). If there are stragglers, list them — those will break post-merge.
2. The script itself: does it still write output under `dashboards/` or did the rename only partially apply?
3. Are there any GitHub Actions workflows that reference `playgrounds/` paths? `grep -rn playgrounds .github/`.

### (F) Test changes — adequate coverage?

1. `tests/test_dashboards.py` — +2 / -1. What test? Verify it covers the new UI affordances at least minimally (filter, type badge, loading state).
2. `tests/test_playground_api_stability.py` — +3 / -1. As noted in (A)(4), confirm it tests for the actual stability claim (no PDF opens in list path), not just endpoint liveness.

### (G) Doc consistency

The 4 doc files updated should reflect the actual code changes 1:1. Cherry-check that:
- `docs/MONITOR-API.md` lists `/api/build/events/*` if that's now the canonical comms endpoint.
- `docs/api-endpoint-consumer-map-2026-05-06.md` doesn't still claim `live-activity` is a consumer.
- `docs/best-practices/agent-bridge.md` and `docs/best-practices/local-api-server.md` paragraph changes are factual.

## CI state at review-start

`BLOCKED` per `gh pr view 2256 --json mergeStateStatus`. As of last check:
- 18 checks green (CodeQL × 3, CI lint/quality/secret/lesson-schema/prompts/dispatch-changes/no-new-root-scripts/Quality-radon, zizmor x 2, codeql x 1, gemini-dispatch x 4)
- `Frontend (build + vitest)` IN_PROGRESS — likely passes given UI-only edits but a vitest failure would be blocking.
- `Test (pytest)` IN_PROGRESS — likely passes given test files were updated.
- `review/review` FAILURE — this is the persistent F7 GEMINI_API_KEY noise per project handoff; treat as ADVISORY unless your review finds an actual issue with the diff content.

Re-check CI before declaring your verdict: `gh pr view 2256 --json statusCheckRollup,mergeStateStatus`.

## Output format (mandatory, structured)

Write your review to `audit/pr-2256-codex-review-2026-05-24.md` with EXACTLY this shape:

```markdown
# PR #2256 codex review — 2026-05-24

## Verdict

ONE OF: `APPROVE` | `APPROVE_WITH_NITS` | `REQUEST_CHANGES` | `BLOCK`

(If APPROVE / APPROVE_WITH_NITS, orchestrator merges. If REQUEST_CHANGES, orchestrator pushes back to cursor. If BLOCK, orchestrator holds + reports to user.)

## Summary (3 sentences)

(What the PR does, the core risk, your overall confidence.)

## Findings

### Critical (block merge)
- ... or "None" ...

### Significant (delay merge for fix)
- ... or "None" ...

### Nit (track as follow-up, don't block)
- ... or "None" ...

## CI cross-check

`gh pr view 2256 --json statusCheckRollup,mergeStateStatus` — paste raw output here.

## Evidence per finding

For every Critical / Significant finding, include:
- File:line
- The relevant diff hunk
- The specific concern in 1-2 sentences
- The fix you'd request (if Critical/Significant)
```

## Workflow

1. Read all files in the "Read these files first" list (read the diff via `gh pr diff`).
2. Address each lettered concern (A-G) explicitly — if the concern is moot for a given diff, say so and skip.
3. Write your review to `audit/pr-2256-codex-review-2026-05-24.md` in this main project tree (NOT in the cursor worktree).
4. Optional: post your top 1-3 Critical/Significant findings as inline PR comments via `gh pr comment 2256 --body "..."` or `gh api repos/learn-ukrainian/learn-ukrainian.github.io/pulls/2256/comments` — use `--mode read-only` does NOT allow writes; if you're in read-only mode skip inline comments and rely on the audit file.
5. **Do not approve via `gh pr review`** — the orchestrator handles the approve+merge step based on your audit verdict.

## Verifiable claims (per #M-4)

Every claim of "the code does X" or "this test covers Y" must be backed by a quoted line from the file. Use this shape in findings:

> `scripts/api/images_router.py:42` reads `for pdf in pdf_paths: with fitz.open(pdf) as doc: ...`

vs the unacceptable:

> "The router opens PDFs in a loop."

If the second form sneaks in, you're paraphrasing — go back and quote the literal line.

## Time budget

30 min wall. If you're not done in 30 min, write what you have to the audit file with a `## Incomplete review note` at the top and exit. Partial verdict beats no verdict.
