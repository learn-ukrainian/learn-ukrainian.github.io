# Codex dispatch brief — Bakeoff Phase 2 execution (no Claude calls)

> **Goal:** run Phase 2 of the A1/20 bakeoff (2 writes + 2 cross-reviews; zero Claude calls). Report results so the orchestrator (Claude) can decide on Phase 3 timing.
> **Mode:** `workspace-write` (no worktree needed — this is script execution, not code changes)
> **Hard timeout:** 5400s (90 min — generous; expected wall time 30-60 min)
> **Effort:** medium

## Context

Today the bakeoff harness merged via PR #1704 and a writer-prompt fix merged via PR #1706. Phase 1 (`--dry-run`) is confirmed clean. Phase 2 runs the two non-Claude writers + the two cross-reviews where neither side is Claude. Claude write + 4 Claude-involving reviews defer to Phase 3 after 20:00 CET (Anthropic peak-hours pricing).

A leftover from a previous failed Phase 2 run (the `{X}` bug fixed in #1706) is still in `audit/bakeoff-2026-05-05/`. The harness's `--resume` would falsely skip the writes (size-based check, not terminal-event check — tracked in #1707). So step 1 is to nuke the dir.

## Numbered execution steps

1. From the repository root (`/Users/krisztiankoos/projects/learn-ukrainian`), verify you're on `origin/main`:

   ```bash
   git fetch origin main
   git log --oneline HEAD..origin/main  # must be empty
   ```

   If non-empty: `git pull --ff-only origin main` (don't try to commit; this dispatch is execution-only).

2. Clean the previous-run leftovers:

   ```bash
   rm -rf audit/bakeoff-2026-05-05/
   ```

3. Run Phase 2 step 1 (writes only — Gemini and Codex):

   ```bash
   .venv/bin/python scripts/audit/bakeoff_run.py \
       --bakeoff-dir audit/bakeoff-2026-05-05 \
       --level a1 --slug my-morning \
       --writers gemini-tools,codex-tools \
       --writers-only
   ```

   Stream stdout to your runtime log. Expected: two `phase_writer_summary` events (one per writer), each with `module_done`. Wall time per writer: 5-15 min.

4. Run Phase 2 step 2 (cross-reviews only — Codex reviews Gemini's lesson; Gemini reviews Codex's lesson):

   ```bash
   .venv/bin/python scripts/audit/bakeoff_run.py \
       --bakeoff-dir audit/bakeoff-2026-05-05 \
       --level a1 --slug my-morning \
       --writers gemini-tools,codex-tools \
       --reviewers-only \
       --skip-aggregate \
       --resume
   ```

   `--resume` skips the writes (already done in step 3). `--skip-aggregate` because the aggregator report is incomplete without Claude's data. Expected: 2 reviews complete with `phase_review_summary` events.

5. Verify file layout:

   ```bash
   ls -la audit/bakeoff-2026-05-05/
   ```

   Expected files (sizes will vary; non-empty is the test):
   - `gemini.md` — Gemini's lesson
   - `gpt55.md` — Codex's lesson
   - `gemini.write.jsonl` — Gemini writer telemetry
   - `gpt55.write.jsonl` — Codex writer telemetry
   - `gemini-gpt55.review.jsonl` — Codex reviewing Gemini's lesson
   - `gpt55-gemini.review.jsonl` — Gemini reviewing Codex's lesson
   - `gemini/` and `gpt55/` directories — module artifacts (knowledge_packet, writer_prompt, etc.)

6. For each `*.write.jsonl` and `*.review.jsonl`, grep the last line and confirm it's the expected terminal event:

   ```bash
   for f in audit/bakeoff-2026-05-05/*.write.jsonl; do
       echo "=== $f ==="
       tail -1 "$f"
   done
   for f in audit/bakeoff-2026-05-05/*.review.jsonl; do
       echo "=== $f ==="
       tail -1 "$f"
   done
   ```

   Pass criteria:
   - Each `.write.jsonl` ends with a line containing `"event": "phase_writer_summary"` AND `"event": "module_done"`.
   - Each `.review.jsonl` ends with a line containing `"event": "phase_review_summary"`.

## Reporting

When done, output a concise summary:

- Wall time per step
- Per-writer: `phase_writer_summary` event content (or "FAILED — last event: <type>")
- Per-review: `phase_review_summary` event content (or "FAILED — last event: <type>")
- Word count of each writer's `.md` (use `wc -w`)
- Any non-zero exit codes

Do NOT:

- Commit, push, or open a PR (this is execution-only)
- Modify any code (no edits to `scripts/`, `tests/`, `docs/`, etc.)
- Re-run a failed step automatically — report the failure and exit
- Attempt Claude (`claude-tools`) writes or any Claude-as-reviewer step — those are explicitly Phase 3 (after 20:00)

## Failure modes to surface clearly

- `Unknown placeholder-shaped token` — the prompt-template regression returned somehow. Stop, report which template + line.
- Non-zero exit from `bakeoff_run.py` — paste the last 30 lines of stdout/stderr.
- Writer subprocess timeout — surface the writer name and the timeout message.
- File missing after the run (e.g., no `gemini.md`) — report which file is missing.

## Out of scope

- The aggregator report (`REPORT.md`). It needs Claude's data to be useful; it gets generated in Phase 3.
- Any change to the harness, V7 builder, or review logic — defer to a separate dispatch if found.
- Cleanup of #1707 (resume-logic refinement) — that's a separate issue.

## Constraints

- Mode is `workspace-write`. You can write files under `audit/`. You should NOT commit or push.
- No agent CLIs invoked manually — `bakeoff_run.py` invokes them itself.
- Hard timeout 5400s. If it expires mid-step, the dispatch supervisor terminates; report what completed.
