---
date: 2026-05-18
session: "Late-night drive after late-night-deepseek session. User direction: 'drive so we solve as much tech debt as possible and also drive that we can finally build m20 successfully and output it.' Going to sleep + /clear (not restart). Handoff = primary cold-start input for the cleared session."
status: green
main_sha: 4bb0ec0ca1
main_green: true
open_prs: [1873]  # dependabot starlight only
active_dispatches:
  - task_id: adopt-kubedojo-artifacts-20260517-215941
    agent: codex
    model: gpt-5.5
    effort: xhigh
    started_at: 2026-05-17T21:59:46Z
    duration_at_handoff_s: 642
    purpose: server-rendered /artifacts page with classified sections (kubedojo-inspired); see docs/dispatch-briefs/2026-05-17-adopt-kubedojo-artifacts-layout.md
worktrees_open:
  - .worktrees/dispatch/codex/adopt-kubedojo-artifacts-20260517-215941   # active dispatch above
  - .worktrees/dispatch/gemini/artifacts-workflow-analysis-20260517-215135  # report at SHA 0ce17b725a — UNPUSHED, see below
prs_merged_this_session: [2113, 2114, 2115, 2117, 2118, 2119]
issues_closed_by_merges: [2089, 2099, 2100, 2101, 2102, 2106]
direct_to_main_commits: [634bd08780]  # .gitignore hygiene (orphan-ocr/) — bypassed pytest gate, low-risk
---

# Midnight handoff — tech debt + m20 ship drive

## TL;DR (4 lines)

1. **User direction is autonomous-overnight drive on tech debt + m20 ship.** They said "drive so we solve as much tech debt as possible and also drive that we can finally build m20 successfully and output it" then "i ma going to sleep." Clearing context (`/clear`) but not restarting — so SAME session id, FRESH context. This handoff is the cold-start input.
2. **m20 ship critical path = Path 3 PR3 + PR4 + V7 build.** PR1 (#2108) + PR2 (#2117) MERGED. **PR3 (Phase 3 batched correction pass) NOT YET DRAFTED — write brief inline NEXT, fire to Codex.** PR4 (Goodhart sentinel) after PR3. Then `v7_build.py a1 my-morning --worktree`.
3. **6 PRs merged this session** (#2113/#2114/#2115/#2117/#2118/#2119) clearing carry-over tech debt: routing rules update, OCR filter hardening, gemma-local removal, PR2 fix_proposals gate, OpenAI proxy 422 envelope fix.
4. **1 active dispatch** (Codex adopt-kubedojo-artifacts, 642s in at handoff — UI redesign per user request). Check status first; merge if green.

## What landed this session

| SHA | PR | What |
|---|---|---|
| `634bd08780` | (direct) | chore(hygiene): gitignore `data/raw/orphan-ocr/` + root `transcription.md` (process debt — flagged in commit msg) |
| `15834d642c` | #2113 | (predecessor session) audit_external_resources path fix |
| `4bb0ec0ca1` | #2114 | DeepSeek routing rules added to model-assignment.md + MEMORY #M0 |
| `8f995fd2c3` | #2115 | bulk_ocr_gemini.py refusal + completion-meta leak filter (#2001 closed) |
| `dce4064ec2` | #2117 | **Path 3 PR2 — wiki_coverage_gate emits structured fix_proposals on failure** |
| (TBD) | #2118 | gemma-local lane removed (user direct order: "we wont use local gemma") |
| (TBD) | #2119 | OpenAI proxy 422 validation errors use OpenAI error envelope (#2028 closed) |

**Closed issues**: #2089 (Dagger pre-push pytest, fixed by #2088 earlier), #2028 (envelope, #2119), plus all four clawpatch issues from the predecessor session.

**Filed issues**: #2116 (claude-i tmux wrapper adopted as post-June-15 Claude dispatch lane — research/follow-up).

## Critical carry-over: m20 ship plan

**Why m20 still fails today**: m20-my-morning has 18 obligations in the Wiki Manifest. Single-pass writer asymptotes at 44% coverage (proven on m20 builds #16–#21). Path 3 architecture (`docs/decisions/2026-05-17-path3-per-obligation-review-loop.md`) is the architectural fix. PR1 + PR2 are merged. PR3 + PR4 + m20 rebuild remain.

### PR3 — Phase 3 batched correction pass (NEXT WORK ITEM)

Per Decision Card lines 66-92. **No brief exists yet — write inline first thing after cold-start.**

Scope:
- Read fix_proposals emitted by wiki_coverage_gate (PR2's new field).
- Group failures by `(artifact, obligation_type)`.
- For each group, fire ONE Codex (xhigh) reviewer call with all failures + manifest specs + current artifact text. Reviewer emits `<fixes>` block only (strict ADR-007: find/replace pairs, NO regeneration).
- Pipeline applies fixes deterministically via existing `_apply_writer_correction`.
- Re-run wiki_coverage_gate.
- Phase 4: if some obligations still fail, per-obligation narrow reviewer call (Codex high), cap at 2 iterations per obligation. After cap, emit `plan_revision_request` (mechanism: TBD per design — JSONL event or module_dir file).
- Per-iteration `coverage_pct` must monotonically improve or abort (per Decision Card risk #1).

Files involved:
- `scripts/build/linear_pipeline.py` — pipeline orchestration (add Phase 3 + Phase 4 stages, max-iter caps, telemetry events)
- `scripts/build/correction.py` (or wherever `_apply_writer_correction` lives) — reuse existing `<fixes>`-only apply path
- `scripts/build/phases/correction_loop.py` — NEW module if needed for the loop logic
- `tests/build/test_phase3_correction_loop.py` — NEW test suite

Brief template: use `docs/dispatch-briefs/2026-05-17-path3-pr2-fix-proposals.md` as the structural reference. Same shape: Why / What you build / Verifiable claims (per #M-4) / Worktree / Verification / Commit + PR / Out of scope / Anti-fabrication. Reuse the "for Codex xhigh, mode=danger, --worktree" pattern.

**Open design question (no consensus yet — pick during brief writing)**: should `plan_revision_request` surface as a JSONL event the orchestrator catches, or as a file in module_dir? The 3-agent `ab discuss` fired during the prior session to settle this DIED with `READ_ONLY_VIOLATION` (codex/grok/deepseek all tried to write files during read-only mode). DO NOT re-fire the discuss — write the brief inline using the Decision Card as the source of truth. Pick "JSONL event" as the default — matches the existing `linear_pipeline.py` event-emission pattern.

### PR4 — Phase 5 Goodhart sentinel (after PR3 lands)

Per Decision Card lines 82-92. After the deterministic gate passes, fire a secondary semantic reviewer (Gemini cross-family — model: `gemini-3.1-pro-preview`) that judges "is this obligation woven into the prose, or just keyword-stuffed?" Fail the build if the gate passes but the semantic reviewer flags substance-missing.

Smaller scope than PR3. Estimated effort 1 day. Brief template: same shape as PR3.

### m20 rebuild — after PR4 lands

```bash
.venv/bin/python -u scripts/build/v7_build.py a1 my-morning --worktree 2>&1 | grep --line-buffered '^{"event"' | tee /tmp/m20-build-events.jsonl
```

Use `Monitor` tool on the JSONL stream per #0B. Watch for `phase_done`, `review_score`, `wiki_coverage_fix_proposals` (PR2's new event), and the new `phase3_correction_pass_done` event PR3 will add. Expected outcome: coverage_pct ≥ 80% (the level-A1 threshold per `WIKI_COVERAGE_MIN_PCT_BY_LEVEL`).

## Tech debt queue (drive autonomously)

Ordered by ROI / unblock-likelihood:

1. **#2071 Codex dispatch hangs (`response_chars=0`)** — pattern surfaced repeatedly in handoffs. Fix: add `initial-response-timeout` distinct from `silence-timeout` (3 min vs 30 min). Codex-shaped. Brief at NONE yet.
2. **#2029 Bridge /healthz forks 4 subprocesses per request** (DoS surface, MEDIUM). Fix: TTL cache (60s) or background probe + cached state. DeepSeek-pro hermes is well-suited (small focused refactor, MCP-backed). Brief at NONE yet.
3. **#2039 grok-tools writer under-target word count + token-truncation artifact** — Grok-shaped self-fix BUT Grok lacks file-edit dispatch per #2072. Until #2072 lands, Codex or Gemini takes the fix.
4. **#2072 Grok integration — extend dispatch to support file edits / git operations** — architectural. Decision needed first: should Grok ever do file edits? If yes, write the wrapper. If no, document and close.
5. **#2023 Bridge: document or fix Claude --bare auth for OpenAI proxy** — investigation + likely docs-only fix. Gemini-shaped.
6. **#2022 Bridge: reconcile Gemini 3.0 OpenAI proxy route with available CLI models** — small mapping fix.
7. **#2052 Karavansky data acquisition** — BLOCKED on text file. Defer until user provides materials.
8. **#2053 Holovashchuk data acquisition** — BLOCKED on PDF (404). Defer.
9. **#2054 Paronyms data acquisition** — BLOCKED on PDF OCR. Defer.
10. **#2048 R2U difficult-lexis script ready, data file not loaded** — BLOCKED on text file. Defer.

**Filed tonight (already trackable, follow up when slot opens):**
- **#2116 claude-i tmux wrapper adoption** — Pre-June-15 Claude dispatch lane via subscription (not API pool). Build adapter `scripts/agent_runtime/adapters/claude_interactive.py` modeled on `hermes_grok.py`.

## Artifacts-workflow-analysis report (Gemini, 2026-05-17 night)

The Gemini-3.1-pro analysis dispatch (`artifacts-workflow-analysis-20260517-215135`) produced a 186-line REPORT.md committed at SHA `0ce17b725a` on local branch `gemini/artifacts-workflow-analysis-20260517-215135` in worktree `.worktrees/dispatch/gemini/artifacts-workflow-analysis-20260517-215135`. **NOT PUSHED to origin** at handoff — orchestrator must push or read locally.

8 recommendations with file:line evidence (full text in REPORT.md):

1. Formalize DeepSeek through Hermes (DONE this session — PR #2114 added DeepSeek routing rules).
2. **Implement fail-fast heartbeats for Codex** — `initial-response-timeout` vs `silence-timeout`. Maps to #2071. **HIGH priority for autonomous drive.**
3. Consolidate Agent Routing Rules (deprecate AGENT-CAPABILITY-MATRIX.md as manual; auto-generate from a YAML).
4. Enforce Path 3 strictness against manual writer-output edits (in progress via PR1/PR2/PR3/PR4).
5. Automated VESUM/corpus cross-checks (largely have via `mcp__sources__*`; refine).
6. **Automate git worktree lifecycle cleanup in `delegate.py`** — recurring hygiene cost. Worth a Codex dispatch.
7. Mandate "Out of scope" sections in dispatch briefs — process improvement; codify in MEMORY DISPATCH-BRIEF CHECKLIST.
8. Automate Clawpatch validation (currently manual pytest re-run + provider rotation).

**Action**: after merging the in-flight kubedojo-artifacts dispatch + PR3/PR4, file individual GH issues for #2/3/6/7/8 (already #2071 covers #2). #2/6 are best candidates for the autonomous-drive window.

## Active dispatch + queue

| Task | Agent | Status | ETA |
|---|---|---|---|
| `adopt-kubedojo-artifacts-20260517-215941` | Codex gpt-5.5 xhigh | running, 642s in at handoff | ~10-15 min more |
| **NEXT**: Path 3 PR3 brief + dispatch | Codex (queue) | not yet started | brief writing inline, ~20-30 min total |
| **NEXT+1**: Path 3 PR4 brief + dispatch | Codex (queue) | not yet started | shorter than PR3 |
| **NEXT+2**: m20 v7_build | local, agent-run | not yet started | 20-40 min after PR4 lands |

DeepSeek + Grok + Claude lanes idle — fire parallel tech debt while Codex chews through Path 3.

## Worktrees at handoff

```
/Users/krisztiankoos/projects/learn-ukrainian                                                                        4bb0ec0ca1 [main]
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/adopt-kubedojo-artifacts-20260517-215941     4bb0ec0ca1 [codex/adopt-kubedojo-artifacts-20260517-215941]  # ACTIVE
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/gemini/artifacts-workflow-analysis-20260517-215135 0ce17b725a [gemini/artifacts-workflow-analysis-20260517-215135]  # DONE, NOT PUSHED
```

**Cleanup needed after handoff**: push the analysis branch (or leave for the next session). Remove the worktree only after pushing.

## Cold-start instructions (post-/clear)

1. **Read this handoff first** — `docs/session-state/2026-05-18-midnight-handoff-tech-debt-and-m20-drive.md`.
2. Standard orient: `curl -s --max-time 2 http://localhost:8765/api/state/manifest` + `/api/orient` + `/api/comms/inbox?agent=claude`.
3. **Check `adopt-kubedojo-artifacts-20260517-215941` status first** — `curl /api/delegate/active`; if `total=0`, find the PR via `gh pr list --state open`; if all blocking checks green, merge + reap worktree.
4. **Then start PR3** — write brief inline at `docs/dispatch-briefs/2026-05-18-path3-pr3-batched-correction.md` using the Decision Card and PR2 brief as templates. Default `plan_revision_request` shape: JSONL event (no consensus from prior ab discuss — it died with READ_ONLY_VIOLATION; use the Decision Card and your own design judgment). Fire to Codex with `--worktree`.
5. **While PR3 runs in flight**, fire parallel tech debt:
   - DeepSeek-pro hermes on **#2029** (bridge /healthz TTL cache — small, focused, MCP-backed).
   - Gemini on **#2023** or **#2022** (bridge auth/route docs/fixes — routine).
   - Codex (when slot frees after PR3) on **#2071** + **artifacts-analysis §6 worktree cleanup automation** in `delegate.py`.
6. **When PR3 lands**: fire PR4 (Goodhart sentinel) brief + dispatch immediately. Smaller scope.
7. **When PR4 lands**: fire `.venv/bin/python -u scripts/build/v7_build.py a1 my-morning --worktree 2>&1 | grep --line-buffered '^{"event"'` via `Monitor` tool. Watch for coverage_pct ≥ 80%.
8. **Throughout**: keep MEMORY.md at ≤150 lines (currently 150 after this session's DeepSeek routing add). Trim BEFORE adding.
9. **Throughout**: per #M-6 — do not ask permission for obvious next actions. Drive.
10. **Open issues to drive in parallel** as Codex/Gemini slots free: #2071, #2029, #2039 (after #2072), #2072 design, #2023, #2022. Skip data-acquisition issues (blocked on materials).

## What I will NOT do without user signal

- Merge dependabot PR #1873 (starlight 0.38.4 → 0.39.2) — frontend deps are user-owned for review.
- Restart any service unless a dispatch explicitly requires it AND no dispatches are in flight.
- Push to main directly (use PRs for everything — process debt flagged this session).
- Force-remove worktrees without confirming they're not the live dispatch path.
- Lower any quality gate threshold to "make m20 ship" — that's a #1 rule violation. m20 ships at ≥80% coverage or it doesn't ship.

## Format note

MD per #M-2 (ai → ai handoff). Update `docs/session-state/current.md` to point at this file in the same commit if the handoff is being landed via PR (orchestrator's call — for /clear handoff, in-place file suffices).
