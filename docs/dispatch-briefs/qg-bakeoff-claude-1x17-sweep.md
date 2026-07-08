# QG bakeoff — Claude 1×17 sweep (GLM-5.2, #4763)

**Prerequisite:** PR #4762/#4763 harness merged on `main` (tooled_runtime_claude + lenient JSON + session JSONL tool recovery).

You are the measurement driver. **Run ONE Python command.** Do not write bash scripts, do not use a shell tool, do not run `nohup`.

## The only command

From repo root `/Users/krisztiankoos/projects/learn-ukrainian`:

```
cd /Users/krisztiankoos/projects/learn-ukrainian
QG_BAKEOFF=1 .venv/bin/python scripts/audit/run_subscription_1x17_sweep.py --model claude-opus-4-8
```

## What it does

- **34 cells:** 17 fixtures × tooled + bare (greenfield — do not reuse old multirun bare cells).
- **Output:** `audit/2026-07-08-claude-multirun-1x/` (`_sweep.log`, `RESULTS.tsv`, `SCORECARD.md`).
- **Serial** with 90s/60s pauses between cells.

## Parallel with GPT

Claude and GPT use different subscription buckets. GPT sweep can run at the same time in a **separate** session:

```
cd /Users/krisztiankoos/projects/learn-ukrainian
QG_BAKEOFF=1 .venv/bin/python scripts/audit/run_subscription_1x17_sweep.py --model gpt-5.5
```

Do not share the same `--out-dir`.

## When finished

Write `audit/2026-07-08-claude-multirun-1x/REPORT.md` with SCORECARD link, 17×lift table, and viability verdict under STRICT.

## Hard stops

- `QG_BAKEOFF=1` not set
- More than 2 consecutive cell failures
- Harness cells with `status=error` and `tool_call_count=0` on tooled arm (report — do not patch harness)

## Never

- Edit harness code or open PRs during measurement
- Rerun gemini/gemma/deepseek arms
