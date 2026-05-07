# Session Handoff — 2026-05-09 (overnight orchestration shift)

> **Predecessor:** `docs/session-state/2026-05-08-replacement-evaluation-and-autonomous-mode.md`
> **Mode:** Autonomous orchestration. User asleep, orchestrator ran the night shift dispatching Codex / Gemini / Claude-headless.
> **Started:** 2026-05-08 ~00:30 CEST
> **User direction at 00:50 CEST:** "use all agents not just codex" — adjusted to spread work across Codex (mechanical code), Gemini (content + ADR + triage), Claude-headless (adversarial reviews of Codex PRs).

---

## TL;DR (read this — actionable for morning)

1. **A1-blocker escalation: #1790** — codex-tools writer STILL produces 0 tool calls post-#1784. MCP not actually wired in `codex exec` headless mode. **5-minute manual `codex exec` test in morning** is the unblock. See "A1-blocker escalation" section below.
2. **1 PR merged** (#1788 brief linter). 7 PRs open awaiting decisions or in-flight revisions.
3. **Multi-agent reviews shipped**: each non-trivial PR got an adversarial Claude-headless review posted as a PR comment. Verdicts informed merge decisions.
4. **Decision Graph ADR is PROPOSED at PR #1791** — Gemini drafted, Claude reviewed, Gemini revising per Claude findings. **User signoff required to flip PROPOSED → ACCEPTED.**
5. **#1789 anti-menu linter is REVISE in flight** — Claude review found 2 IMPORTANT bugs (false-positive on project's own brief format), Codex dispatched to revise.
6. **#1792 has merge conflicts with main** (from #1788's pre-commit hook addition). Holding rest of PRs to avoid cascade rebase pain. Morning user can decide merge order.

---

## A1-blocker escalation (READ FIRST)

**#1790 — codex-tools writer still 0 tool calls post-#1784.**

Re-fired the codex-tools-only bakeoff at `audit/bakeoff-2026-05-08-codex-only/` to verify Priority 1 from the predecessor handoff. Result: gpt55 produced 0 tool calls again, identical to the pre-#1784 result. The writer narrates intended tool use as prose (`<verification_trace>scripts/verification/vesum.py words(...)`) but never actually calls MCP tools.

#1784 was a **necessary but insufficient** fix — flag mapping is now correct (test `tests/test_agent_runtime.py:276` passes), but `codex exec` in headless mode does NOT actually wire MCP servers, regardless of flags.

**5-minute manual verification (your task in morning):**
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
codex exec --dangerously-bypass-approvals-and-sandbox --enable multi_agent -C "$PWD" - <<<"call mcp__sources__verify_words for word 'кіт' and report the JSON result"
```

- If it works → bug is in our subprocess env (env-var leak, working dir, similar) — Codex investigates
- If it returns "tool unavailable" → bug is in codex CLI / MCP-server config (likely `codex exec` doesn't load MCP at all) — config or upstream issue

A1 vertical-slice unblock cannot proceed past writer-selection signoff until this is resolved.

Issue: #1790 with full evidence + suggested next steps.

---

## What landed tonight

### Merged PR

| PR | What | Notes |
|---|---|---|
| **#1788** | feat(guardrail): brief linter rejects bare .venv/bin/python in worktrees | Claude review PASS with 4 NIT/IMPORTANT followups → filed as #1794 |

### Open PRs (awaiting morning decisions OR in-flight revisions)

| PR | Author | What | Status | Reviews |
|---|---|---|---|---|
| **#1789** | Codex | feat(guardrail): anti-menu linter | **REVISE recommended (revise dispatch FAILED)** | Claude review found 2 IMPORTANT bugs: (1) false-positive on `## Acceptance criteria (numbered, all required)` heading [`scripts/audit/lint_anti_menu.py:62, 130`], (2) META_EXAMPLE_RE only checks same line, false-positives on briefs that enumerate antipatterns including its own brief [`scripts/audit/lint_anti_menu.py:39-43`]. **Revise dispatch (`codex-1787-1.4-anti-menu-revise`) FAILED at worktree-prep** because delegate runner expected a new branch (`codex/1787-1.4-anti-menu-revise`) but the existing worktree is on `codex-1787-1.4-anti-menu-linter`. **Morning fix path**: either (a) re-dispatch with `--base origin/codex-1787-1.4-anti-menu-linter` or task-id matching the branch, or (b) merge as-is with followup issue documenting the false positives, or (c) revise inline. Full review at PR #1789 comment. |
| **#1791** | Gemini | docs(adr): Decision Graph view ADR (PROPOSED, kubedojo Action C) | **REVISE recommended (revise dispatch FAILED)** | Claude review found 5 IMPORTANT issues: (1) fabricated `ADR-008` cross-reference (Multi-UI ADR is `2026-05-06-multi-ui-channel-participation.md`, not ADR-008 which is `2026-05-05-adr-008-supersession-resolved-keep.md`), (2) missing `Scope:` frontmatter field, (3) vague Q3 marker regex (no concrete pattern), (4) Q2 body-size rationale over-generalizes architecture-only data, (5) Q4 convergence wording internally muddled. **Revise dispatch (`gemini-1791-adr-revise`) FAILED at worktree-prep** with same branch-name mismatch as #1789. **PROPOSED status preserved.** Morning fix path: re-dispatch with corrected `--base`, or revise inline. Full review at PR #1791 comment. |
| **#1792** | Codex | feat(guardrail): handoff verifier | **MERGE CONFLICTS with main** | Claude review verdict: REVISE [OPTION] — closed-world detection misses typos. But ACs met, tests pass. Holding due to conflicts; user merges first or can dispatch rebase. |
| **#1793** | Codex | feat(guardrail): status-or-fail subcommand + memory rule #0G | OPEN, unmerged | Adds `/api/delegate/active` endpoint (slight scope creep but defensible). 392 LOC, 7 files. Pending Claude review (queue full at time of decision). |
| **#1795** | Gemini | docs(audit): #1770 plan-references triage (32 plans) | OPEN, unmerged — INFORMATIONAL | 19 INGEST + 9 AMEND + 4 DEFER verdicts. 4 HIGH-priority textbooks identified (Кравцова, Варзацька, Пономарьова, Кравцова Grade 3). User decides ingestion. |
| **#1796** | Codex | fix(ab-bridge): preserve discuss root and infer ask sender (#1786) | **OPEN — REVISE [BLOCKING] per Claude review** | Fixes B.1, B.2, B.3 from #1786. 240 additions, 8 files. **Claude headless review found 1 BLOCKING bug**: `tests/test_coverage_misc.py::TestSendGeminiMessage` (×3) fails because the PR widened `_send_gemini_message`'s signature (inserted `from_llm` as 5th positional arg) without updating the 3 existing test calls. **CI confirms** (`actions/runs/25527415468`). Mechanical fix: insert one positional arg in 3 test calls. Plus 2 IMPORTANT issues: huge-root-brief regression (>22KB body would now `ValueError`), fragile `CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS` env proxy. Architecture is sound; merge after CI green. Full review on PR comment. |
| **#1797** | Codex | feat(audit): D4 decision-lineage backlink scanner with multi-alias support (#1785) | OPEN — **NO REVIEW** (Claude headless review #3 ran out of time after #1796) | D4 lineage scanner per #1785. 546 additions. Tests/CI status unverified by adversarial review. **Morning fix path**: spot-check via `gh pr diff 1797` + run scanner on live repo (`.venv/bin/python scripts/audit/decision_lineage.py --decision-id ADR-008`) before merge. |

### Issues filed tonight

| # | Title | Reason |
|---|---|---|
| #1785 | Add decision-lineage backlink scanner (multi-alias) with JSON/API output | kubedojo Action A — paradigm-independent D4 tool |
| #1786 | ab discuss + ask-* infrastructure bugs (root truncation, plan-mode tool subset, --from default) | kubedojo Action B — 3 sub-bugs in one umbrella |
| #1787 | EPIC: Build orchestration guardrails (4 sub-tasks 1.1, 1.3, 1.4, 1.5) | replacement-evaluation guardrails 1, 3, 4, 5 |
| #1790 | codex-tools writer still 0 tool calls post-#1784 — MCP not actually wired | A1-blocker, requires manual verification |
| #1794 | follow-ups for #1788 brief linter (prose-mention false positive + hardcoded learn-ukrainian) | followup from Claude review |

### Direct main commits

- `b94150a86f` — chore: 2026-05-08 evening hygiene — bakeoff retry-2 evidence + kubedojo follow-ups (committed evidence files: `audit/bakeoff-2026-05-07-retry/`, dispatch briefs, kubedojo follow-up doc)
- (#1788 squash merge) — feat(guardrail): brief linter

---

## Multi-agent review map (who reviewed what)

| PR | Codex review | Gemini review | Claude headless review |
|---|---|---|---|
| #1788 | n/a (Codex authored) | n/a | ✓ PASS with NITs (Issue #1794 filed) |
| #1789 | n/a (Codex authored) | n/a | ✓ REVISE — 2 IMPORTANT bugs, in-flight Codex revise |
| #1791 | requested via `ask-codex` (single-shot, output not visible on PR) | n/a (Gemini authored) | ✓ REVISE — 5 IMPORTANT issues, in-flight Gemini revise |
| #1792 | n/a | n/a | ✓ REVISE [OPTION] — recommended merge with followup |
| #1793 | n/a | n/a | NOT YET (queue was full when reviews fired) |
| #1795 | n/a | n/a (Gemini authored) | NOT YET — informational triage, low review priority |
| #1796 | n/a (Codex authored) | n/a | ✓ REVISE [BLOCKING] — CI red, signature-change broke 3 existing tests. Plus 2 IMPORTANT, 2 NIT. Posted on PR #1796 |
| #1797 | n/a (Codex authored) | n/a | NOT COMPLETED — Claude review #3 worker exited rc=0 after only writing #1796 review (`/tmp/claude-review-1796-body.md`). #1797 review never started. Worker had 0 stdout the whole run; cause unclear. |

---

## Bakeoff evidence preserved

- `audit/bakeoff-2026-05-07-retry/` — 2026-05-07 second-attempt bakeoff (committed as `b94150a86f`)
- `audit/bakeoff-2026-05-08-codex-only/` — Priority 1 verification run, **gpt55 still 0 tool calls** (NOT committed — surfaces #1790's evidence)

---

## Remaining work for next session (sequenced)

### Priority 1 — resolve A1 unblocker (#1790)

5-minute manual `codex exec` verification. Direct Codex/orchestrator to fix the right layer based on result.

### Priority 2 — review + merge / decide on open PRs

Recommended order (gates the rest):

1. **#1788 (already merged ✓)**
2. **#1796** — **BLOCKED on test fix**. Claude review found `tests/test_coverage_misc.py::TestSendGeminiMessage` (×3) failing because Codex widened `_send_gemini_message`'s signature without updating callers. Fix: insert `from_llm` as 5th positional arg in 3 test calls (`tests/test_coverage_misc.py:436, 444, 452`). Could be a 5-LOC inline fix OR re-dispatch Codex with the targeted brief. After CI green, merge.
3. **#1797** — **NEEDS REVIEW** before merge (Claude review #3 didn't get to it). Spot-check via `gh pr diff 1797` + run scanner on live repo: `.venv/bin/python scripts/audit/decision_lineage.py --decision-id ADR-008` should show ADR-008's lineage. If scanner works + tests pass, merge.
4. **#1793** — read body, run Claude review or merge if confident (delegate.py status-or-fail + memory rule #0G is straightforward)
5. **#1792** — REBASE first (conflicts with #1788). Verdict was OPTION. Merge after rebase. File followup issue from Claude review.
6. **#1789** — wait for Codex revision PR to update; Claude re-review; merge.
7. **#1791** — wait for Gemini revision; review again; **flip PROPOSED → ACCEPTED if happy** (user-only action).
8. **#1795** — informational; act on the textbook ingestion priorities OR file follow-up issues for the HIGH-priority ingestion candidates.

Cap is 2 Codex + 2 Claude in-flight; check `/api/delegate/active` before queueing rebases.

### Priority 3 — pending ADRs awaiting user signoff

- `docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md` (Multi-UI ADR)
- `docs/decisions/pending/2026-05-09-decision-graph-view.md` (Decision Graph ADR — this shift's output)

### Priority 4 — kubedojo follow-ups continuation

- Action A (#1785, D4 lineage scanner): **shipped at #1797** (pending review + merge)
- Action B (#1786, infra bugs): **shipped at #1796** (pending review + merge)
- Action C (#1791, Decision Graph ADR): **shipped at #1791** (PROPOSED, in-flight revision)
- Action D: reply to kubedojo team (after C signoff)
- Action F: tier-3 listener POC — still deferred until Multi-UI ADR ACCEPTED

### Priority 5 — writer-selection signoff (still blocked on Priority 1)

After codex-tools tool-use is verified working AND the bakeoff produces a fair signal, post the writer-selection proposal on EPIC #1577. User signoff → A1 unblocked.

### Priority 6 — Boy-Scout cleanup

- `.worktrees/dispatch/codex/1476-auto-path` — orphan directory with stale data symlinks. Can be `rm -rf`'d. Not critical.
- `.worktrees/dispatch/codex/1787-1.1-brief-linter` — merged-PR worktree, branch deleted, can `git worktree prune`.

---

## Behavioral discipline held this shift

- **Cap discipline**: tracked active dispatches via orient API. Briefly went 3 Codex during the 1.4-revise fire (anticipated ab-bugs landing), corrected by holding off further Codex.
- **No menus to user**: autonomous decisions at every fork (which PR to merge, which issue to file, which agent to dispatch).
- **Surfaced ESCALATIONS only**: just #1790 (A1-blocker) explicitly flagged for user manual verification.
- **State-from-source-of-truth**: used Monitor API + git worktree direct inspection over `gh` API (which had ~30s eventual-consistency lag throughout the night).
- **Adversarial reviews**: every non-trivial PR got an independent Claude headless review before merge decision. Reviews caught real bugs (#1789's heading false-positive, #1791's fabricated ADR-008 ref).

---

## Files written this shift

- `docs/session-state/2026-05-09-night-shift-orchestration.md` — THIS file
- `docs/dispatch-briefs/2026-05-08-night/` — 9 dispatch briefs:
  - `1787-1.1-brief-linter.md`
  - `1787-1.4-anti-menu-linter.md`
  - `1787-1.5-handoff-verifier.md`
  - `1787-1.3-status-verifier.md`
  - `1785-d4-decision-lineage.md`
  - `1786-ab-discuss-bugs.md`
  - `decision-graph-adr-gemini.md`
  - `1770-plan-references-triage-gemini.md`
  - `1789-anti-menu-revise.md`
  - `1791-adr-revise-gemini.md`
- `audit/bakeoff-2026-05-08-codex-only/` — Priority 1 verification (failed — led to #1790)
- `/tmp/claude-review-1788-1789-report.md` — first Claude review (full report)
- `/tmp/claude-review-1791-1792.md` and `/tmp/claude-review-1796-1797.md` — Claude review briefs

---

## Cross-thread notes (still active from predecessor)

(Inherited from `docs/session-state/current.md` — not modified this shift.)

- ADR-008 PROPOSED on main, awaits user signoff (`docs/decisions/2026-05-05-adr-008-supersession-resolved-keep.md`)
- Multi-UI ADR PROPOSED, awaits user signoff (`docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md`)
- Wiki rebuild fully landed; lit-doc / lit-crimea scrub fan-out tracked separately
- `GH_TOKEN` lives in `.envrc` (corrected 2026-05-07)
