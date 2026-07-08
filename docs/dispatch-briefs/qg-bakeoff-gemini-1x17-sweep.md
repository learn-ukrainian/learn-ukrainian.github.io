# QG bakeoff — Gemini 1×17 sweep (GLM-5.2, #4761)

You are the measurement driver. **Run ONE Python command.** Do not write bash scripts, do not use a shell tool, do not run `nohup`, do not improvise.

## The only command

From repo root `/Users/krisztiankoos/projects/learn-ukrainian`:

```
cd /Users/krisztiankoos/projects/learn-ukrainian
QG_BAKEOFF=1 .venv/bin/python scripts/audit/run_gemini_1x17_sweep.py
```

That is the entire sweep. The script handles seeding, throttle waits, 26 remaining cells, logging, and recording.

## What it does

- **Checkout:** `main` at repo root (worktree is gone; code merged).
- **Seeds** 8 done artifacts from `audit/2026-07-08-gemini-strict-probe/` into `audit/2026-07-08-gemini-multirun-1x/`.
- **Skips** 4 fixtures already complete: `vesnianky`, `koliadky`, `khreshchennia-rusi`, `skovoroda-hryhorii`.
- **Runs** 13 remaining fixtures × tooled + bare = **26 cells**, serial, CodexBar-throttled.
- **Writes** `audit/2026-07-08-gemini-multirun-1x/_sweep.log`, `THROTTLE.md`, `RESULTS.tsv`.

## When finished

Write `audit/2026-07-08-gemini-multirun-1x/REPORT.md` with:

1. Link to `SCORECARD.md`
2. Table: 17 fixtures × MJ tooled / live tooled / MJ bare / live bare / live lift
3. CodexBar wait summary
4. Decision: is gemini-3.1-pro-high viable under STRICT? Yes/No + one sentence

## Hard stops (stop and report)

- `QG_BAKEOFF=1` not set before running
- More than 2 consecutive cell failures inside the script
- Antigravity quota blocked more than 2 hours straight

## Never

- Edit harness code, open PRs, or merge branches
- Run gemini cells in parallel
- Use `--regate` on fresh artifacts
- Rerun gemma/deepseek
