# Codex dispatch brief — Run full 3-way A1/20 bakeoff (DANGER mode, post-fixes) — V2

> **Mode:** danger (full sandbox bypass — needed for `pgrep`/`pkill` watchdog and Claude/Gemini CLI invocations)
> **Worktree:** `.worktrees/dispatch/codex/bakeoff-2026-05-07-retry/`
> **Output dir:** `/Users/krisztiankoos/projects/learn-ukrainian/audit/bakeoff-2026-05-07-retry/` (absolute path so REPORT.md lands in MAIN checkout; suffix `-retry` preserves prior committed evidence at `audit/bakeoff-2026-05-07/`)
> **Hard timeout:** 7200s (120 min)
> **Effort:** medium
> **Silence timeout:** 3600s (1h — bakeoff serial-3-writer execution has long silent stretches between writers; 1800s default killed `bakeoff-2026-05-07` previously)

---

## ⚠️ CRITICAL — fresh-shell behavior

**Each bash block runs in a FRESH SHELL. CWD does NOT persist across blocks.** Every command that uses files in the MAIN checkout (`.venv/`, `scripts/`, `docs/`) MUST be prefixed with `cd /Users/krisztiankoos/projects/learn-ukrainian && ...` or use absolute paths.

The previous retry attempt (`bakeoff-2026-05-07-retry` task-id, completed 2026-05-07T18:41) failed at step 2 because `.venv/bin/python` resolved against worktree CWD where `.venv/` does not exist (worktrees never have `.venv/` — it's gitignored). Brief V2 wraps every command with explicit `cd`.

---

## Goal

Run the FULL A1/20 bakeoff with all bakeoff-blocker fixes applied. This is the **first fair bakeoff retry** — prior attempts had broken signal:

- `audit/bakeoff-2026-05-05/` — pre-fix attempt; missing trace capture, adapter contamination, weighted-avg aggregator
- `audit/bakeoff-2026-05-07/` — committed evidence of failed first-fair attempt; Claude wrote 474-byte meta-summary instead of 4 artifact fences (HARD STOP RULE in PR #1781 fixes that)
- `audit/bakeoff-2026-05-07-retry/` — **THIS run** (the actual fair bakeoff)

Fixes since `bakeoff-2026-05-05`:

- Missing trace-capture (#1761/#1767, fixed)
- Adapter contamination bugs (#1768, fixed via #1775 — Gemini cross-contamination, Codex prompt-echo, Claude format-fragility)
- Aggregator using weighted-avg instead of min(dim) and ignoring theatre fields (#1773, fixed via #1776)
- Verbatim textbook quoting gate not enforced (#1725, fixed via #1757 + WARN→REJECT revert)
- Structured CoT + verification_trace + grammar-claim grounding missing (#1661 + #1673, fixed via #1772)
- Plan-review-time corpus check missing (#1765, fixed via #1769)
- HARD STOP RULE preventing meta-summary after artifact fences (#1781, merged 2026-05-07)

Current main commit: should be `6014cbab74` or later (after #1781 merge).

---

## Steps

1. Verify base SHA (sanity check):
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian && git rev-parse HEAD && git log --oneline -3
   ```

2. **Do NOT** clean `audit/bakeoff-2026-05-07/` — that is committed evidence from the prior failed attempt. The retry uses a different output dir (`audit/bakeoff-2026-05-07-retry/`).

   Clean only the retry output dir for a fresh run:
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian && rm -rf audit/bakeoff-2026-05-07-retry/
   ```

3. Pre-flight smoke (catches plan/packet drift fast):
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python scripts/build/v7_build.py a1 my-morning --writer claude-tools --dry-run
   ```
   Expect exit 0 in <5s. If it fails, STOP and report.

4. **Fire the full bakeoff** with absolute `--bakeoff-dir`:
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python scripts/audit/bakeoff_run.py \
       --bakeoff-dir /Users/krisztiankoos/projects/learn-ukrainian/audit/bakeoff-2026-05-07-retry \
       --level a1 --slug my-morning \
       --writers claude-tools,gemini-tools,codex-tools
   ```
   Runs: 3 writes (Claude→Gemini→Codex order) + 6 cross-reviews + aggregate. Total wall ~60-90 min.

5. **Watchdog** — monitor stdout from step 4. If any writer/reviewer goes silent (no new JSONL events) for >20 min:
   - Identify silent CLI process: `pgrep -fl "gemini -y\|claude exec\|codex exec"`
   - SIGKILL the silent one; the harness logs fail and continues
   - Note in final summary which step required intervention

6. **Verify** layout when done:
   ```bash
   ls -la /Users/krisztiankoos/projects/learn-ukrainian/audit/bakeoff-2026-05-07-retry/
   for f in /Users/krisztiankoos/projects/learn-ukrainian/audit/bakeoff-2026-05-07-retry/*.jsonl; do
       echo "=== $f ==="
       tail -1 "$f" | head -c 250
       echo
   done
   ```
   Expected: `claude.md`, `gemini.md`, `gpt55.md`, three `*.write.jsonl`, six `*-*.review.jsonl`, `REPORT.md`.

7. **NEW (post-#1773 aggregator):** confirm REPORT.md has the new sections:
   - `## Winner ranking by tool-call density` (top of report, before "Prompt adherence")
   - `## REVIEWER PROTOCOL BROKEN` banner ONLY if `reviewer_fixes_unparseable` events fired
   - Per-writer `tool_theatre_violation_count` row in writer-prompt table
   - Winner gate uses min(dim) — confirm by inspecting findings section

8. **Confirm HARD STOP RULE held** (post-#1781 verification):
   - For each writer, the `*.write.jsonl` should NOT contain a meta-summary phase after `<end_gate>`
   - Each writer's raw output should end at the `<end_gate>` block
   - If any writer wrote a summary after `<end_gate>`, flag prominently in report — that means HARD STOP RULE failed

---

## Reporting (concise)

- Per-writer: wall time, word count of `.md`, terminal event (`phase_writer_summary` or last seen), **tool_calls_total**, **tool_theatre_violation_count**, **HARD_STOP_RULE_held: yes/no**
- Per-review: wall time, terminal event (`phase_review_summary` or last seen)
- Aggregator exit code
- Top-line summary tables from REPORT.md (paste, don't re-analyze)
- **Winner per the new ranking section** (NOT re-derived)
- Any hangs or kills

---

## Constraints

- No commits, no PRs (execution-only)
- No code edits — if something fails after a watchdog kill, report don't fix
- `--writers claude-tools,gemini-tools,codex-tools` order is intentional
- Output dir is absolute path under MAIN repo, NOT worktree
- Do NOT touch `audit/bakeoff-2026-05-05/` or `audit/bakeoff-2026-05-07/` — both are historical record
- This is the first fair bakeoff — outcome determines writer-selection per `docs/decisions/2026-04-26-reboot-agent-responsibilities.md` §3
