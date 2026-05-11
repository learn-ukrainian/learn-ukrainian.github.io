---
date: 2026-05-11
session: "Evening — Phase 2 MCP shipped + orchestrator hygiene caught"
status: ok
detail: 2026-05-11-evening-phase2-mcp-and-orchestrator-hygiene.html
main_sha: f1c7a1701c
main_green: true
open_prs: 7                                   # 0 of mine, 7 dependabot
active_dispatches: 0
merged_today: [1879, 1880, 1881, 1867, 1869]  # this session
rejected_today: []
filed_today: [1877, 1878, 1882]
closed_today: [1657-Phase2, 1787, 1877, 1878] # #1657 Phase 2 complete (not the EPIC); #1787 closed as already-done; #1877+#1878 filed+closed
in_flight: []
blocked: []
next_p0: "User runs prompt-validation bakeoff on a1/my-morning with updated prompts after Codex weekly quota resets at 01:07 May 12 (~3h after session close, ~7% remaining if attempted before reset). If writer_tool_call > 0 AND writer_tool_theatre = 0 → #1577 vertical-slice A1 batch unblocked. If fail → iterate prompts further on #1807."
agents: [claude, codex, gemini]
worktrees_open: 0
ci_notes: "GH Actions pull_request event refused to retrigger on Codex's force-push to #1879 — close+reopen also failed; resolved via rebase on current main (resolved 6 merge conflicts in server.py + tests, all additive) which triggered fresh CI green. Followup if this recurs: empty commit + push, OR web-UI 'Re-run all jobs'."
incidents: ["Re-dispatched 4 #1787 sub-tasks that had ALREADY SHIPPED 2026-05-08 (PRs #1788/#1789/#1792/#1793). EPIC body was never updated. Caught by 1st Claude-headless dispatch which self-refused; killed 3 others; encoded as orchestrator-discipline lesson (see Decisions below)."]
---

# Brief — 2026-05-11 evening (Phase 2 MCP shipped + orchestrator hygiene caught)

> Machine-readable companion to `2026-05-11-evening-phase2-mcp-and-orchestrator-hygiene.html`.

## TL;DR

- **#1657 Phase 2 complete on main** (4/4 verifiers: `verify_quote`, `verify_source_attribution`, `check_modern_form`, `check_russian_shadow`). Plus **ADR-010 PROPOSED** merged covering Phase 3.
- **Writer + reviewer prompts rewritten** to call the new primitives as single tool calls — directly attacks #1807 tool-theatre. Awaiting bakeoff validation.
- **Major drift caught:** #1787 was already 100% shipped on 2026-05-08 (no one updated EPIC body) — re-dispatched 4 redundant tasks before catching it. Killed 3, encoded the lesson as new **X-Agent commit trailer guardrail** (`scripts/audit/lint_agent_trailer.py`).
- Codex weekly at **7%** remaining, resets 01:07 May 12. Bakeoff path ready when user attempts.

## What shipped

| PR / Commit | Title | Source |
|---|---|---|
| **#1879** | `feat(mcp): add verify_source_attribution(source, claim)` | Codex dispatch → Gemini REVISE (Wikipedia fragility) → Codex fix push → 6-conflict rebase + force-with-lease → CI green → merged |
| **#1880** | `feat(mcp): add verify_quote(author, text)` | Codex dispatch — Gemini PASS, merged clean |
| **#1881** | `docs(adr): ADR-010 PROPOSED — MCP verification Phase 3` | Claude-headless xhigh dispatch — Gemini PASS, merged. Concrete designs for `verify_external`, `VerificationVerdict` envelope, asymmetric `review_dim_*` (only 2 of 5 dimensions get server-side bundles). |
| **#1867, #1869** | dependabot patch bumps (markdown2, joserfc) | Gemini batch-triage → GREEN → merged |
| `1515fc5a8a` | docs(worktree): subtree layout across all agent rule docs | inline (user request) |
| `28417cc3cb` | feat(prompts): writer + reviewer use new primitives as single calls — addresses #1807 | inline (Claude prompt-eng) |
| `f1c7a1701c` | feat(audit): X-Agent commit trailer + lint guardrail | inline (orchestrator-visibility fix) |

## What rejected / killed

- 3 redundant #1787 dispatches killed mid-flight after discovering the work was already on main since 2026-05-08 (PRs #1788/#1789/#1792/#1793). 1 Claude-headless dispatch self-refused before any work. **Encoded lesson**: when PR body says `(#NNN)`, EPIC NNN body MUST be updated checkbox-by-checkbox in the same orchestrator turn — re-dispatch happens when the EPIC body is the stale source of truth.

## Carry-over queue (priority order)

### User-action gate

1. **PROMPT-VALIDATION BAKEOFF** on `a1/my-morning` with `--writer codex-tools`. Use `/goal` (interactive Codex; enable via `codex features enable goals`). The goal statement is prepared in the HTML companion + the prior orchestrator turn. SUCCESS = `writer_tool_call > 0 AND writer_tool_theatre = 0`. Cost ~3-5% of weekly Codex budget. **Either attempt before 01:07 reset using ~7% remaining, OR wait for reset.**

### After bakeoff

2. **If PASS** → start #1577 vertical-slice A1 batch (user-runs `v7_build` in `/loop` after reset).
3. **If FAIL** → iterate prompt on #1807 further (likely intervention: remove `<verification_trace>` block entirely + force tool calls outside the artifact).

### Mechanical

4. **#1870 + #1874 react pair** — atomic merge required (`react` + `react-dom` must move together; CI on each alone breaks). Cleanest: `@dependabot rebase` one onto the other after the first merges, OR manual combined branch. User-coordinated.
5. **3 RED dependabots** — #1866 lxml 5.4→6.1 (major), #1868 attrs 25.4→26.1 (major), #1871 mcp-memory-service 10.29.1→10.54.0 (+25 minors). Careful review each.
6. **2 YELLOW dependabots** — #1872 astro 6.2→6.3, #1873 starlight 0.38→0.39 (both in `/starlight`, load-bearing). Review patch notes + test build.
7. **CI retrigger fix** — investigate why GH Actions `pull_request` event stopped firing today (close+reopen + empty-commit-push both failed; only rebase worked). Possibly path-filter regression or billing/quota.

### Decisions to revisit (still PROPOSED — not blocking)

- `docs/decisions/pending/2026-05-09-decision-graph-view.md` — channels.html UI toggle
- `docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md` — agent bridge multi-surface identity
- `docs/architecture/adr/adr-010-mcp-verification-phase3.md` — **JUST MERGED PROPOSED**, user needs to review and either ACCEPT (then Phase 3 implementation sub-issues get filed) or REVISE

### Tracked but not actioned

- **#1782** persistent-listener architecture — `decision-pending` label. Premise partially superseded by Codex Desktop Automations per Multi-UI ADR. User explicitly chose to keep active.
- **#1807** codex-tools writer tool-theatre — open. Will close after next bakeoff confirms #1882 prompt fix actually worked.

## Decisions encoded

1. **Orchestrator definition refined.** Orchestrator owns workflow goal-to-done — including updating EPIC bodies when PRs with `(#NNN)` land. Re-dispatch on stale EPIC body = orchestrator failure. Encoded informally; should become a `scripts/audit/lint_epic_drift.py` (follow-up).
2. **X-Agent commit trailer convention.** Every commit on a non-main feature branch must carry `X-Agent: <agent>/<task-id>` trailer. Lint script + docs + warn-only pre-push hook shipped this session (commit `f1c7a1701c`). Flip to blocking after adoption. Forward-only enforcement — don't rewrite history.
3. **Worktree subtree layout standardized.** `.worktrees/dispatch/<agent>/<task>/` is the canonical layout. Flat layout deprecated. Runtime nags loudly on flat. Rule deployed to `.claude/`, `.agent/`, `.codex/` + AGENTS.md + GEMINI.md.
4. **Writer-prompt mandate**: single-primitive calls (`verify_quote`, `verify_source_attribution`, `check_modern_form`, `check_russian_shadow`) instead of compose-patterns. Compose-pattern reserved for retrieving evidence chunks, not for boolean verdicts. Filed as **#1882**.
5. **Codex `/goal` use case identified**: thread-level goal tracking for the prompt-validation bakeoff. Not a workflow engine; useful for keeping Codex on-task within one interactive session with token-budget awareness. Enable via `codex features enable goals`.
6. **Stash dropped**: `stash@{0}` phantom-edits-PR-1824 (UI nav links + Promise.allSettled robustness on `playgrounds/orient.html`) was stale — paths now under `dashboards/*` post-#1864 rename. Content summary captured in HTML companion if salvageable.

## Pending decisions (still PROPOSED — not blocking next P0)

- `docs/decisions/pending/2026-05-09-decision-graph-view.md` — out of scope for bakeoff
- `docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md` — out of scope for bakeoff
- `docs/architecture/adr/adr-010-mcp-verification-phase3.md` — **NEWLY PROPOSED**, awaiting user accept/revise

## Cold-start orientation for next agent

1. **Read this brief first.** Skip the `.html` unless flagged otherwise here.
2. **First action: check Codex weekly quota.** If reset (after 01:07 May 12), the prompt-validation bakeoff is ready to run — see "Carry-over queue → User-action gate" above.
3. **The actual A1/A2 goal:** #1577 vertical-slice batch build — UNBLOCKED structurally as of this session. Gating on bakeoff signal validating the #1882 prompt fix. Read `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md` if you don't recall the writer-lock conditions.
4. **Repo state**: clean. main at `f1c7a1701c`. 0 PRs of mine open. 7 dependabot PRs (1 pair + 5 individual) queued. 0 stale worktrees. 0 active dispatches.
5. **New orchestrator guardrails active**:
   - `scripts/audit/lint_agent_trailer.py` — every commit needs `X-Agent: <agent>/<task>` trailer (warn-only pre-push hook). Use `X-Agent: claude-inline/<topic>` for orchestrator inline commits.
   - Subtree worktree layout `.worktrees/dispatch/<agent>/<task>/` — use bare `--worktree` flag (no path) and the dispatch runtime auto-derives.
6. **Before any new dispatch**: verify the work isn't already on main. Run `find . -name '<target-file>'` + `gh search prs '#<EPIC> in:body'` BEFORE writing the brief. The 2026-05-04/05 EPIC #1787 sub-issues are the cautionary tale.

---

*Format spec: `claude_extensions/rules/workflow.md` § "Two-tier handoffs". Companion HTML: `2026-05-11-evening-phase2-mcp-and-orchestrator-hygiene.html`.*
