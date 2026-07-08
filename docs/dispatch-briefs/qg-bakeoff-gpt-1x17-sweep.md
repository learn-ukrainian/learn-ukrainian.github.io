# QG bakeoff — GPT (Codex) 1×17 sweep (Codex / GLM, #4762)

**Prerequisite:** PR #4762/#4763 harness merged on `main` (tooled_runtime_gpt via Codex exec).

You are the measurement driver. **Run ONE Python command.** Do not write bash scripts, do not use a shell tool, do not run `nohup`.

## The only command

From repo root `/Users/krisztiankoos/projects/learn-ukrainian`:

```
cd /Users/krisztiankoos/projects/learn-ukrainian
QG_BAKEOFF=1 .venv/bin/python scripts/audit/run_subscription_1x17_sweep.py --model gpt-5.5
```

## What it does

- **34 cells:** 17 fixtures × tooled + bare (greenfield).
- **Output:** `audit/2026-07-08-gpt-multirun-1x/`.
- **Serial** with pauses between cells.

## Parallel with Claude

Safe to run alongside the Claude sweep (different model pin, different out dir). Gemini 1×17 may still be running — that is fine (Antigravity quota is separate).

## When finished

Write `audit/2026-07-08-gpt-multirun-1x/REPORT.md` with SCORECARD link, lift table, viability verdict.

## Hard stops

- `QG_BAKEOFF=1` not set
- More than 2 consecutive cell failures

## Never

- Edit harness during measurement
- Reuse old multirun bare artifacts for engine selection
