# Codex dispatch brief — Run full 3-way A1/20 bakeoff (DANGER mode, post-fixes)

> **Mode:** danger (full sandbox bypass — needed for `pgrep`/`pkill` watchdog and Claude/Gemini CLI invocations)
> **Worktree:** `.worktrees/dispatch/codex/bakeoff-2026-05-07/`
> **Output dir:** `/Users/krisztiankoos/projects/learn-ukrainian/audit/bakeoff-2026-05-07/` (absolute path so REPORT.md lands in MAIN checkout)
> **Hard timeout:** 7200s (120 min)
> **Effort:** medium
> **Silence timeout:** 1800s (30 min — uses new default from #1763)

## Goal

Run the FULL A1/20 bakeoff with all bakeoff-blocker fixes applied. This is the **first fair bakeoff** — prior runs (`audit/bakeoff-2026-05-05/`) had broken signal due to:

- Missing trace-capture (#1761/#1767, fixed)
- Adapter contamination bugs (#1768, fixed via #1775 — Gemini cross-contamination, Codex prompt-echo, Claude format-fragility)
- Aggregator using weighted-avg instead of min(dim) and ignoring theatre fields (#1773, fixed via #1776)
- Verbatim textbook quoting gate not enforced (#1725, fixed via #1757 + WARN→REJECT revert)
- Structured CoT + verification_trace + grammar-claim grounding missing (#1661 + #1673, fixed via #1772)
- Plan-review-time corpus check missing (#1765, fixed via #1769)

Current main commit: should be ≥ `b2a886bfd8` (after #1775 merge). Verify before firing.

## Steps

(Start inside the worktree. Run all commands from MAIN checkout — `cd` first.)

1. From MAIN checkout, clean any leftover bakeoff state for this fresh run:
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian
   rm -rf audit/bakeoff-2026-05-07/
   ```
   (Do NOT touch `audit/bakeoff-2026-05-05/` — leave the prior broken-signal data as historical record.)

2. Pre-flight smoke (catches plan/packet drift fast):
   ```bash
   .venv/bin/python scripts/build/v7_build.py a1 my-morning --writer claude-tools --dry-run
   ```
   Expect exit 0 in <5s. If it fails, STOP and report.

3. **Fire the full bakeoff** with absolute --bakeoff-dir:
   ```bash
   .venv/bin/python scripts/audit/bakeoff_run.py \
       --bakeoff-dir /Users/krisztiankoos/projects/learn-ukrainian/audit/bakeoff-2026-05-07 \
       --level a1 --slug my-morning \
       --writers claude-tools,gemini-tools,codex-tools
   ```
   Runs: 3 writes (Claude→Gemini→Codex order) + 6 cross-reviews + aggregate. Total wall ~60-90 min.

4. **Watchdog** — monitor stdout from step 3. If any writer/reviewer goes silent (no new JSONL events) for >20 min:
   - Identify silent CLI process: `pgrep -fl "gemini -y\|claude exec\|codex exec"`
   - SIGKILL the silent one; the harness logs fail and continues
   - Note in final summary which step required intervention

5. **Verify** layout when done:
   ```bash
   ls -la /Users/krisztiankoos/projects/learn-ukrainian/audit/bakeoff-2026-05-07/
   for f in /Users/krisztiankoos/projects/learn-ukrainian/audit/bakeoff-2026-05-07/*.jsonl; do
       echo "=== $f ==="
       tail -1 "$f" | head -c 250
       echo
   done
   ```
   Expected: `claude.md`, `gemini.md`, `gpt55.md`, three `*.write.jsonl`, six `*-*.review.jsonl`, `REPORT.md`.

6. **NEW (post-#1773 aggregator):** confirm REPORT.md has the new sections:
   - `## Winner ranking by tool-call density` (top of report, before "Prompt adherence")
   - `## REVIEWER PROTOCOL BROKEN` banner ONLY if `reviewer_fixes_unparseable` events fired
   - Per-writer `tool_theatre_violation_count` row in writer-prompt table
   - Winner gate uses min(dim) — confirm by inspecting findings section

## Reporting (concise)

- Per-writer: wall time, word count of `.md`, terminal event (`phase_writer_summary` or last seen), **tool_calls_total**, **tool_theatre_violation_count**
- Per-review: wall time, terminal event (`phase_review_summary` or last seen)
- Aggregator exit code
- Top-line summary tables from REPORT.md (paste, don't re-analyze)
- **Winner per the new ranking section** (NOT re-derived)
- Any hangs or kills

## Constraints

- No commits, no PRs (execution-only)
- No code edits — if something fails after a watchdog kill, report don't fix
- `--writers claude-tools,gemini-tools,codex-tools` order is intentional
- Output dir is absolute path under MAIN repo, NOT worktree
- This is the first fair bakeoff — outcome determines writer-selection per `docs/decisions/2026-04-26-reboot-agent-responsibilities.md` §3
