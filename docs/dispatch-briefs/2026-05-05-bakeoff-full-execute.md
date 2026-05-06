# Codex dispatch brief — Run full 3-way A1/20 bakeoff (DANGER mode)

> **Mode:** danger (full sandbox bypass — needed for `pgrep`/`pkill` watchdog and Claude/Gemini CLI invocations)
> **Worktree:** `.worktrees/dispatch/codex/bakeoff-execute/` (delegate.py requires worktree for danger mode)
> **Output dir:** `/Users/krisztiankoos/projects/learn-ukrainian/audit/bakeoff-2026-05-05/` (absolute path so REPORT.md lands in the MAIN checkout, not in the worktree)
> **Hard timeout:** 7200s (120 min)
> **Effort:** medium

## Goal

Run the FULL A1/20 bakeoff: 3 writes (Claude → Gemini → Codex) + 6 cross-reviews + aggregator report. Two prior dispatches failed in workspace-write sandbox (Codex couldn't run `pgrep`/`pkill`, Gemini hung again). Danger mode bypasses both.

## Steps

(You start inside the worktree. Run all commands from the MAIN checkout — `cd` first.)

1. From the MAIN checkout, clean any leftover bakeoff state:
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian
   rm -rf audit/bakeoff-2026-05-05/
   ```

2. Pre-flight smoke (catches plan/packet drift fast):
   ```bash
   .venv/bin/python scripts/build/v7_build.py a1 my-morning --writer claude-tools --dry-run
   ```
   Expect exit 0 in <5s. If it fails, STOP and report.

3. **Fire the full bakeoff** with absolute --bakeoff-dir:
   ```bash
   .venv/bin/python scripts/audit/bakeoff_run.py \
       --bakeoff-dir /Users/krisztiankoos/projects/learn-ukrainian/audit/bakeoff-2026-05-05 \
       --level a1 --slug my-morning \
       --writers claude-tools,gemini-tools,codex-tools
   ```
   This runs: 3 writes (Claude→Gemini→Codex order) + 6 cross-reviews + aggregate. Total wall ~60-90 min.

4. **Watchdog** — monitor stdout from step 3. If any writer/reviewer goes silent (no new JSONL events) for >20 min:
   - Identify silent CLI process: `pgrep -fl "gemini -y\|claude exec\|codex exec"`
   - SIGKILL the silent one; the harness logs fail and continues to the next step
   - Note in final summary which step required intervention

5. **Verify** layout when done:
   ```bash
   ls -la /Users/krisztiankoos/projects/learn-ukrainian/audit/bakeoff-2026-05-05/
   for f in /Users/krisztiankoos/projects/learn-ukrainian/audit/bakeoff-2026-05-05/*.jsonl; do
       echo "=== $f ==="
       tail -1 "$f" | head -c 250
       echo
   done
   ```
   Expected: `claude.md`, `gemini.md`, `gpt55.md`, three `*.write.jsonl`, six `*-*.review.jsonl`, `REPORT.md`.

## Reporting

Concise summary:
- Per-writer: wall time, word count of `.md`, terminal event (`phase_writer_summary` or last seen)
- Per-review: wall time, terminal event (`phase_review_summary` or last seen)
- Aggregator exit code
- Top-line summary tables from REPORT.md (paste, don't re-analyze)
- Any hangs or kills

## Constraints

- No commits, no PRs (execution-only)
- No code edits — if something fails after a watchdog kill, report don't try to fix
- `--writers claude-tools,gemini-tools,codex-tools` order is intentional (Claude first per user)
- Output dir is the absolute path under MAIN repo, NOT in your worktree
