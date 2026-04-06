# Token Usage Insights (2026-04-06)

## Baseline (since Apr 3 reset)
- 1.86B tokens / 3.5 days / 880 sessions
- learn-ukrainian: 1.19B (211 sessions, 72 subagents)
- kubedojo: 667M (669 sessions, 64 subagents)

## Where tokens go
- 95% cache reads (context re-loaded every turn — cheap per token, but adds up)
- 74% of token volume is subagent sessions (mostly cache reads, not expensive per-token, but each reload still costs)
- Actual "new" work: ~5% (cache creation + output — this is where real cost is)

## Top cost drivers
1. **Subagent count** — each spawns full context (~2-3M tokens). 33 subagents in one session = ~100M just loading context.
2. **Session restarts** — new session = cold cache. Continuing a session reuses warm cache.
3. **System prompt size** — MEMORY.md + rules + agent definition loaded on every turn and every subagent.

## Improvements to make
- Fewer subagents: batch work into fewer, longer subagents
- Use `model: "haiku"` or `model: "sonnet"` for simple subagent tasks (grep, file reads, linting)
- Keep sessions alive longer (`--continue`) instead of starting fresh
- Trim MEMORY.md ruthlessly (it's over 200-line budget — every extra line multiplied by every turn)
- Consider if all rules files need to load for every session (some are large)

## Script
`scripts/token_usage.py` — run with `SINCE_DATE=2026-04-03 .venv/bin/python scripts/token_usage.py`
