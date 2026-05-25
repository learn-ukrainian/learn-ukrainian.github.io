---
date: 2026-05-24
session: "Daytime continuation of overnight handoff. Five PRs merged (#2256 monitor UI polish, #2257 Option C plan_reference_match gate, #2258 cursor adapter `-p -` argv bug fix, #2259 F2+F3 cleanup, #2260 writer-prompt Option B fixes). PR #2235 also merged via codex stale-PR triage. Orchestrator skill rewritten as hard-rules cheatsheet with detail in docs/orchestrator-frictions.md (lessons: routing, verify-before-accept-adapter-label, active-watch-same-turn, status-report-shape, repeated-attempt-trigger, persistence-write-twice, adapter-bug-flip-the-test). 38 open issues triaged + labeled by agent (25 codex / 5 cursor / 5 gemini / 3 orchestrator); #1960 closed as dup of #2251. Disk cleanup: 23 worktrees → 3, recovered ~24 GB. m20 still NOT shipping — composer-2.5 writer attempt revealed 3 separate problems (disk-emission contract / Grade 4 fabrication / under-production at 4 activities vs 10-15 floor) → composer-2.5 abandoned for m20; pivot to claude-tools after #2208 workbook-auto-inject fix lands."
status: infra-shipped-m20-pivots-to-claude-tools
main_sha: 3c1813a296
main_green: clean (review/review F7 advisory persists)
working_tree_dirty: pre-existing untracked from prior sessions (5 archived dispatch briefs + a few dashboards/scripts files); not from this session's work
prs_merged_this_session: ["#2256 monitor UI polish + endpoint migration (cursor → gemini fixups via codex review)", "#2257 Option C plan_reference_match gate (closes packet_chunk_id bypass)", "#2258 cursor adapter `-p -` literal positional bug + flipped test enshrining the bug", "#2259 F2+F3 cleanup (5 brief lint + 1 test label)", "#2260 writer-prompt Option B fixes (3 competing rules removed)", "#2235 parser fix (codex tool_result + envelope unwrap) — rebased + merged in codex stale-PR triage"]
prs_closed_this_session: ["#2236 superseded session-state handoff", "#2229 writer-bench v0 DRAFT (scaffold already on main)", "#2226 dependabot torchvision 0.27 (real CI break, tracked in #2261)", "#1960 ext-article-N stubs (dup of #2251)"]
prs_wip_unmerged: ["#2208 workbook auto-inject fix — codex dispatch issue-2208-workbook-auto-inject-2026-05-24 IN FLIGHT at handoff time; branch fix/issue-2208-workbook-auto-inject; session ~/.codex/sessions/2026/05/24/rollout-2026-05-24T21-48-55-*.jsonl; monitor task bl0sclr9x"]
issues_filed_this_session: ["#2261 torchvision 0.27.0 CI break (filed by codex during stale-PR triage)"]
active_dispatches: ["issue-2208-workbook-auto-inject-2026-05-24 (codex, danger, effort=medium)"]
active_builds: []
builds_attempted_this_session: ["a1/my-morning #162518 (cursor-tools, composer-2.5) — FAILED at writer phase: disk-emission contract mismatch (writer uses file-edit tools, pipeline expects stdout fenced blocks) + on-disk artifacts show under-production (4 activities total, 0 workbook vs floor 10-15 split 4-6/6-9) + Grade 4 fabrication in resources.yaml (same as claude-tools)"]
headline_finding: "**Three infrastructure problems fully solved (5 PRs merged) but m20 still NOT shipping — for a NEW reason than overnight.** Composer-2.5 writer attempt produced under-population of activities and disk-emission contract mismatch on top of the known Grade 4 fabrication. Composer-2.5 abandoned for m20 anchor; m20 pivots to claude-tools after #2208 workbook-auto-inject fix lands. Orchestrator skill rewritten with concrete hard rules covering today's friction patterns (routing, monitoring, adapter labels, status reports, redesign trigger, persistence, adapter-bug discipline). Issue queue triaged (38 issues labeled by agent)."
next_session_first_item: "1) Wait for codex #2208 dispatch to land its PR (monitor bl0sclr9x at session start) → merge it → push to main. 2) Get explicit user OK on Claude quota spend for m20 anchor build (one-time). 3) Fire `.venv/bin/python -u scripts/build/v7_build.py a1 my-morning --writer claude-tools --effort xhigh --worktree` and Monitor JSONL events. 4) If python_qg runs and the new plan_reference_match gate (PR #2257) fires on Grade 4 fabrication: implement Option B (hoist gate to pre-python_qg + extend ADR-008 correction message to handle 'remove resources.yaml entry by source_ref/chunk_id'). 5) If claude-tools ships m20: 10-check verify-before-promote per #M-11, then promote as first V7 anchor under post-reset shape."
---

# 2026-05-24 — Five PRs, orchestrator skill rewritten, issue triage done, m20 pivots to claude-tools

## Session arc

User picked up from overnight handoff at ~07:00 UTC. Asked "drive the project pls and would be nice to ship finally a working m20." Day split into:

1. **Codex review pattern** — PR #2256 (cursor's UI polish) reviewed by codex (REQUEST_CHANGES with 3 substantive findings) → gemini dispatched to fix → all 3 codex findings addressed → MERGED.
2. **Critical cursor adapter bug discovery** — Option C dispatch to cursor/composer-2.5 returned `rate_limited` after 168s with `returncode=0` and `response_chars=0`. User pushed back: "i see no limit problems at composer." Investigation found adapter passed `-p -` to cursor-agent, which parses `-` as the literal positional prompt = the string "-", ignoring stdin. The existing test ASSERTED `"-" in plan.cmd` — the bug was enshrined as a feature. Fixed in PR #2258 (1-line argv fix + FLIPPED the assertion + new 3-mode regression test). Investigation also identified the right monitoring sources for codex/cursor/gemini dispatches (session JSONL under ~/.codex/, ~/.cursor/, ~/.gemini/), encoded as a hard rule.
3. **5 PRs landed end-to-end** via codex/gemini dispatches (zero Claude code-writing burn after the cursor-adapter inline fix): #2256, #2257, #2258, #2259, #2260. Plus #2235 merged via codex stale-PR triage.
4. **Orchestrator skill rewritten** — `claude_extensions/agents/curriculum-orchestrator.md` got a tight "Hard rules" cheatsheet section (routing, monitoring, verify-before-accept, status reports, redesign trigger, persistence, adapter-bug discipline). Detail moved to `docs/orchestrator-frictions.md` (autopsies + examples). Deployed via `scripts/deploy_prompts.sh`. MEMORY.md #M-8 also updated.
5. **Issue triage** — 38 open issues labeled with `agent:codex` (25) / `agent:cursor` (5) / `agent:gemini` (5) / `agent:orchestrator` (3). Cross-reference comments added to the 3 codex-CLI runtime bugs (#2159, #2134, #2071) clustering them as one investigation. #1960 closed as duplicate of #2251.
6. **m20 build attempt #7** (cursor-tools / composer-2.5) — FAILED. Revealed 3 distinct problems beyond the known Grade 4 fabrication. Composer-2.5 abandoned for m20. Pivot to claude-tools after #2208 fix lands.
7. **Disk cleanup** — disk hit 100% (2.1 GB free). 23 worktrees → 3 via `git worktree remove --force` per #M-10 (artifacts auto-committed to local `build/<level>/<slug>-<stamp>` branches). Recovered ~24 GB.

User explicitly:
- Pushed back on "rate_limited" classification (correct — adapter bug).
- Pushed back on passive Monitor + me asking "any update?" (correct — should poll).
- Pushed back on Claude doing inline code edits when codex has reset compute (correct — routing failure).
- Pushed back on skill being too long vs too short (encoded as cheatsheet + detail-file pattern).
- Flagged considering canceling Claude subscription (frustration peak). Orchestrator's honest answer: I'm useful for orchestration / cross-session memory / linguistic-MCP work; not for code writing. Sonnet downgrade as middle option proposed.

## What's shipped (5+1 PRs merged)

| PR | Commit / SHA at merge | Scope |
|---|---|---|
| #2256 | (cursor branch + gemini fixups merged) | `scripts/api/images_router.py` page_count cached in pdf_catalog at index build (fixes codex finding A — page_count regression broke image-explorer navigation); `scripts/generate_mdx/generate_playground_data.py` writes to `dashboards/` not `playgrounds/` (fix E); `docs/api-endpoint-consumer-map-2026-05-06.md` matrix rows migrated `playgrounds/` → `dashboards/` (fix G). Plus the cursor-authored UI polish: artifacts.html loading skeleton/refresh/filters/type badges/collapsible ops directory; comms.html migrated from deprecated `/api/comms/live-activity` to `/api/build/events/*`; audit-dashboard.html parchment theme via shared monitor.css. Tests: `tests/test_dashboards.py`, `tests/test_playground_api_stability.py`. |
| #2257 | `feat/plan-reference-match-gate` 921333bd82 | `scripts/build/citation_matcher.py` adds `extract_chunk_id_from_notes(notes: str) -> str | None`. `scripts/build/linear_pipeline.py` adds `_plan_reference_match_gate(resources, plan) -> dict` registered alongside `_citation_gate`. Closes the `packet_chunk_id` short-circuit bypass: even if a resource has packet_chunk_id, the new gate HARD-rejects if the chunk_id is not in plan.references[*].notes. CodeQL suppression at line 5888 wrapped in `# fmt: off`/`# fmt: on` to survive future `ruff format` runs (pyproject.toml ignores E501 globally so `ruff check` passes, but `ruff format` is a separate concern). 5 new tests in `tests/test_plan_reference_match_gate.py`. |
| #2258 | `fix/cursor-adapter-prompt-stdin-2026-05-24` 36625d833f | `scripts/agent_runtime/adapters/cursor.py:97` drops `"-"` from argv — cursor-agent's `-p` is a boolean toggle and a bare `-` is parsed as the positional prompt = string "-". The 14KB delegated brief sat unread on stdin. `tests/agent_runtime/adapters/test_cursor_adapter.py:34` flipped from `assert "-" in plan.cmd` (the test enshrined the bug) to `assert "-" not in plan.cmd`. New regression test `test_cursor_adapter_no_literal_dash_argument_anywhere` covers all 3 modes (read-only/workspace-write/danger). Unblocks every `delegate.py --agent cursor` invocation AND the V7 `--writer cursor-tools` build path. |
| #2259 | `fix/f2-f3-cleanup-2026-05-24` (codex 2 atomic commits) | F2: 5 archived dispatch briefs (issue-2239, PR-A, PR-B, PR-C, PR-D1) lint cleanup (.venv cd-guard markers). F3: `tests/build/test_writer_pre_emit_checklist.py` `OBLIGATION_LABELS` relaxed from full-phrase ("VESUM verification", "Russianism check") to topic-keyword ("VESUM", "Russianism") matching both stripped and grok variants. |
| #2260 | `fix/writer-prompt-option-b-fixes-2026-05-24` (codex 3 atomic + 1 fixup commits) | `scripts/build/phases/linear-write.md` +25 / -118 (NET shorter). Three fixes from audit/2026-05-24-writer-prompt-competing-rules.md: (1) added "Citation authority" section near top making plan.references the SOLE source for textbook citations + naming Knowledge Packet anchors as research-only-NOT-citation; (2) tightened resources.yaml textbook-role entries to require a plan chunk_id; (3) replaced line 455 `search_text`-first protocol with `chunk_id`-first `get_chunk_context` mandatory protocol matching `#R-TEXTBOOK-30W` Step A. Fixup commit restored 7 structural-marker literal strings (`"Full Wiki Context (source of truth for citations)"` etc.) that compression had removed and tests asserted on. |
| #2235 | (codex rebased + merged in stale-PR triage) | `fix/codex-tool-result-correlation-and-envelope-unwrap` — small parser fix that had been sitting OPEN, rebased onto main, tested green, squash-merged via codex stale-PR triage dispatch. |

## What's closed (4 PRs closed, 1 issue closed)

| PR/Issue | Reason |
|---|---|
| #2236 | Superseded session-state handoff (2026-05-23 content; today's handoffs supersede). Closed by codex stale-PR triage. |
| #2229 | writer-bench v0 DRAFT — scaffold already on main in cd652772f2 (committed during 2026-05-23 evening hygiene), branch was duplicate. Closed by codex stale-PR triage. |
| #2226 | dependabot torchvision 0.27.0 — real CI break (pytest + CodeQL failures unrelated to our code; torch CPU wheel mismatch). Closed; tracking issue #2261 filed by codex. |
| #1960 | Closed as duplicate of #2251 (Option B follow-up tracking issue inherits the 158 ext-article-N stubs backfill scope). |

## Issue triage (38 issues labeled)

| Label | Count | Examples |
|---|---|---|
| `agent:codex` | 25 | #2210, #2209, #2208 (live dispatch), #2126, #2116, #2072, #2036, #2023, #2039, #1969, #1940, #1933, #1918, #1916, #1914, #1908, #1905, #1896, #1863, #1807, #1799, #1794, #1657, #2156, #2261 |
| `agent:cursor` | 5 | #2159, #2134, #2071 (clustered as ONE investigation — cross-ref comments added), #1814 (HTML/UI on Monitor API), #1782 (persistent agent listeners) |
| `agent:gemini` | 5 | #2251 (ext-article backfill), #2054, #2053, #2052 (MCP data acquisition x3), #2048 (R2U ingest) |
| `agent:orchestrator` | 3 | #2132 (promote-protocol Round 1 ACCEPT decision), #1865 EPIC (context budget), #1577 EPIC (curriculum reboot vertical slice) |

Query examples: `gh issue list --label "agent:codex"`, etc.

## m20 attempt #7 (cursor-tools, composer-2.5) — failure analysis

**Build**: `.worktrees/builds/a1-my-morning-20260524-162518/` (worktree removed in cleanup, branch `build/a1/my-morning-20260524-162518` retained locally — `git checkout` to retrieve).

**Where it died**: writer phase, 166s in. `Writer call returned no response (writer=cursor-tools, effort=medium, returncode=0, duration_s=166.7, stalled=False, rate_limited=False)`.

**Root cause = THREE separate issues**:

1. **Disk-emission contract mismatch.** cursor-tools writer uses file-edit tools to write artifacts directly to disk (activities.yaml, module.md, resources.yaml, vocabulary.yaml all present on disk). The pipeline's `_call_writer` expects the artifacts emitted inline in stdout via fenced code blocks (```` ```json file=<name> ```` shape). Empty stdout → classified as failure → pipeline aborted before python_qg ran.

2. **Composer-2.5 also fabricates Grade 4 references.** `resources.yaml` cites `Захарійчук Grade 4, p.162` and `Захарійчук Grade 4, p.163` — IDENTICAL pattern to claude-tools. The new writer-prompt Option B fixes (PR #2260) did NOT change this. Smoking gun: the Knowledge Packet S1 anchor still points to Grade 4 (it's UPSTREAM of the writer prompt). The writer treats Knowledge Packet anchors as authoritative regardless of what the prompt says about plan.references being the sole source.

3. **Composer-2.5 under-produces activities.** Only 4 activities total (all inline, 0 workbook). A1 floor per `ACTIVITY_CONFIGS`: 10-15 total, split 4-6 inline + 6-9 workbook. Composer-2.5 produces lean focused outputs (good for code, bad for 1200-word multi-section A1 lesson modules). Would HARD-fail activity_schema or related gate even if disk-emission were fixed.

**Decision: composer-2.5 abandoned for m20.** No new issues filed for the disk-emission contract bug or under-production fix — both are composer-2.5-specific and the m20 anchor doesn't need composer-2.5. Cursor-tools wiring (PR #2255 + PR #2258) stays merged for future cursor use cases; just not the A1 module-writer use case.

**Pivot to claude-tools after #2208 lands.** Claude-tools previously produced healthy 5+5 activity splits BEFORE the workbook auto-promote anti-pattern hit (which is what #2208 fixes). Once #2208 lands, claude-tools should produce 10/4-6/6-9 splits cleanly. Quota cost: ~30K Claude tokens for one anchor build — user-OK required.

## Orchestrator skill rewritten

Source: `claude_extensions/agents/curriculum-orchestrator.md`. Deploy target: `.claude/agents/curriculum-orchestrator.md`. Detail file: `docs/orchestrator-frictions.md`.

New sections (HARD rules):
- **Routing** — table of work→agent assignments. Default = dispatch. Inline ONLY for ≤5 LOC CI fixes you just caused, orchestration (PR merging, brief writing, log reading), or Ukrainian linguistic MCP work.
- **After firing any dispatch — MANDATORY active watch** — signal-source-by-agent table. `batch_state/tasks/logs/*.{stdout,stderr}.log` is NOT a valid signal source for codex/cursor/gemini (they go silent). Use per-agent session dirs: `~/.codex/sessions/.../rollout-*.jsonl`, `~/.cursor/chats/<hash>/`, `~/.gemini/history/<task-name>/`.
- **After opening any PR — MANDATORY watch** — `gh pr checks N --watch --interval 15` in `run_in_background=true` in the same turn as the open.
- **Verify before accepting an adapter label** — `rate_limited`/`failed` can be wrong. Read full stderr + usage JSONL row; grep ground truth; run CLI manually if suspect. (Pattern proved on 2026-05-24 cursor adapter bug.)
- **Status reports** — ≤5 lines, past tense + present + next verb. No "I'll do X." No "Want me to Y?" when obvious.
- **Repeated-attempt loop** — N≥3 same-failure-mode attempts → STOP, audit (Option B style), redesign. (Pattern proved on m20: 6+ attempts with same Grade 4 fabrication before the audit identified `linear-write.md:455`.)
- **Persistence — write twice** — new lesson → BOTH curriculum-orchestrator.md AND memory/MEMORY.md. Run `./scripts/deploy_prompts.sh`.
- **Adapter-bug discipline** — fix adapter + FLIP the test that enshrined the bug (don't just add a new test alongside) + autopsy in commit message.

Lessons captured in `docs/orchestrator-frictions.md`:
- Why "code edit, any size → codex" matters (today's burn arithmetic).
- 2026-05-24 cursor adapter `-p -` argv bug autopsy.
- 2026-05-24 passive Monitor missed 3 silent-exit dispatches autopsy.
- 2026-05-24 repeated "I'll do X" without doing X (status-report pattern failure).
- 2026-05-23 m20 prompt-rewrite loop (smoking gun found 2026-05-24 in `linear-write.md:455` via audit dispatch).
- 2026-05-24 wrote lesson only to MEMORY.md, user pushed back that skill is canonical.

MEMORY.md #M-8 (orchestrator-active through dispatch lifecycle) updated with the per-agent session signal sources + the explicit anti-rule against passive Monitor on batch_state CLI logs.

## Disk cleanup

Disk hit 100% used / 2.1 GB free during session. After cleanup: 89% / **26 GB free**.

| | Before | After |
|---|---|---|
| Total worktrees | 23 | 3 |
| .worktrees/builds/ | 9.0 GB (21 build worktrees) | 0 |
| .worktrees/dispatch/ | 8.4 GB (17 dispatch worktrees) | 459 MB (1 live #2208 dispatch) |
| .worktrees/{docs, feat, fix}/ | 1.4 GB | 0 |
| Free space | 2.1 GB | 26 GB |

**Method**: `git worktree list --porcelain | grep "^worktree " | awk '{print $2}' | grep -v <protected paths> | sort by depth descending | xargs -P 4 git worktree remove --force`. Per #M-10: build worktrees have artifacts auto-committed to local `build/<level>/<slug>-<stamp>` branches before worktree removal, so `--force` is safe. To inspect a removed build's artifacts: `git checkout build/a1/my-morning-<stamp>`.

**Protected during cleanup**: main project (`/Users/krisztiankoos/projects/learn-ukrainian`), codex's own scratch (`~/.codex/worktrees/6877/learn-ukrainian`), live #2208 dispatch (`.worktrees/dispatch/codex/issue-2208-workbook-auto-inject-2026-05-24`).

## Active state at handoff

- **Main**: `3c1813a296` (5 PRs of this session + #2235 + #2208 fix when it lands).
- **Open PRs**: 0 (all 5+1 merged + 4 closed). #2208 fix will open shortly when codex dispatch finishes.
- **Active dispatches**: 1 (`issue-2208-workbook-auto-inject-2026-05-24`, codex, session `~/.codex/sessions/2026/05/24/rollout-2026-05-24T21-48-55-019e5b88-8ac9-76c3-98d4-69eb0673b732.jsonl`, monitor task `bl0sclr9x`).
- **Active builds**: 0.
- **Disk**: 26 GB free.
- **Working tree**: still has pre-existing untracked files (5 archived dispatch briefs + a few dashboards/scripts files from prior sessions). Not blocking. Not introduced today.
- **Codex compute**: reset last night per user — abundant.
- **Claude weekly**: 7% at session start, refreshes tomorrow morning. agy = claude-sonnet (same lane). Avoid both for code work.
- **Cursor composer-2.5**: working post-PR-#2258 adapter fix. Not the A1 anchor writer.

## Carry-over priority queue

| # | Item | Priority | Notes |
|---|---|---|---|
| F0-today | Wait for codex #2208 dispatch PR → merge | **P0** | Prerequisite for m20 attempt #8 via claude-tools |
| F1-today | Fire m20 with `--writer claude-tools --effort xhigh --worktree` after #2208 merged + user OK on quota | **P0** | First V7 anchor module ship attempt #8 |
| F2-today | If m20 attempt #8 hits Grade 4 fabrication via plan_reference_match gate: implement Option B (hoist gate to pre-python_qg + extend ADR-008 correction message for "remove resources.yaml entry by source_ref/chunk_id") | P1 | Conditional on attempt #8 outcome |
| F3-today | If m20 ships: 10-check verify-before-promote per #M-11 → promote as first V7 anchor under post-reset shape | P0 conditional | The user-facing goal of all today's work |
| F4-today | 25 codex-labeled issues to dispatch as backlog | P1-P3 | All labeled; orchestrator dispatches at cadence |
| F5-today | 5 cursor-labeled issues: codex CLI bug cluster (#2159+#2134+#2071 as ONE), HTML/UI #1814, persistent listeners #1782 | P1 | Cursor handles bugs well per user direction |
| F6-today | 5 gemini-labeled issues: wiki/ingestion bulk work (#2251 ext-article, #2054+#2053+#2052 MCP data, #2048 R2U) | P2 | Unmetered, mechanical |
| F7-today | 3 orchestrator decisions: #2132 promote-protocol Round 1, #1865 context-budget EPIC, #1577 curriculum-reboot EPIC | P2-P3 | Strategic, no code |
| F-prior | Carry-overs from 2026-05-24 overnight handoff: amelina real-references backfill, F3 renderer-logic audit, F2 DOWNSTREAM_TOKENS guard, PR-D2 full delegate adapter for opencode+hermes, PR-E verify_before_promote automation | P1-P3 | Unchanged |

## Behavioral lessons (today, captured in skill)

1. **Inline edits add up — dispatch ALL code work, even 1 line.** Today the orchestrator burned multiple Claude turns on small edits (cursor adapter, codeql comment, ruff fmt:off) that should have gone to codex. Each individually was "too small to dispatch"; together more than a single codex dispatch.
2. **Passive Monitor on batch_state logs is silent for codex/cursor/gemini.** Right signal: `~/.codex/sessions/`, `~/.cursor/chats/`, `~/.gemini/history/`. Or `gh pr checks --watch` for PR CI. Or `/api/delegate/active` polling.
3. **Adapter classifications can be wrong.** Verify against ground truth (grep buffer for the actual rate-limit text, run CLI manually if suspect) before treating a `rate_limited`/`failed` label as canonical.
4. **N≥3 attempts on same failure mode = redesign trigger.** m20 needed 6+ attempts before the audit found `linear-write.md:455`. Should have switched tactics after attempt #2-3.
5. **Tests can enshrine bugs.** PR #2254 cursor adapter test asserted `"-" in plan.cmd` — the bug WAS the test. When fixing an adapter bug, FLIP the assertion, don't just add a new test next to the wrong one.
6. **Skill too long → I skim. Skill too short → lossy.** Pattern: tight cheatsheet in the skill + detail in a separate referenced file.
7. **Persistence = write twice** — `claude_extensions/agents/curriculum-orchestrator.md` AND `memory/MEMORY.md`. Run `./scripts/deploy_prompts.sh` after skill edits.

## Tomorrow's first action — DO THIS

```bash
# Step 1: check #2208 dispatch state
.venv/bin/python scripts/delegate.py status issue-2208-workbook-auto-inject-2026-05-24
# If status=done: read result file
cat batch_state/tasks/issue-2208-workbook-auto-inject-2026-05-24.result
# Check for new PR
gh pr list --state open --search "head:fix/issue-2208"

# Step 2: review PR diff (small fix to linear-write.md). Watch CI.
gh pr view <N> --json statusCheckRollup,mergeStateStatus
# Step 3: merge if CI green
gh pr merge <N> --squash --delete-branch

# Step 4: confirm Claude quota with user, then fire m20 attempt #8
.venv/bin/python -u scripts/build/v7_build.py a1 my-morning \
  --writer claude-tools --effort xhigh --worktree 2>&1 \
  | grep --line-buffered -E '^\{"event"|^Traceback|Error|FAILED|REJECT|module_done|module_failed|phase_done|writer_end_gate|review_score'

# Step 5: if python_qg fires plan_reference_match (Grade 4 fabrication caught):
#   implement Option B per F2-today (pre-emit gate + correction loop) before re-firing.
# Step 6: if python_qg green + LLM dim review acceptable:
#   10-check verify-before-promote per #M-11, then promote.
```

Full session arc + commit chain + autopsies above. Handoff is the boundary — next session opens with #2208 dispatch outcome + m20 attempt #8 via claude-tools.
