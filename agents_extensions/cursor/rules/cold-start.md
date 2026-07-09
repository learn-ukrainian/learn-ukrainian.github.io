# Cursor cold start (200k context)

Cursor already loads `AGENTS.md` + `CLAUDE.md` as workspace rules (~40–60k tokens).
Do **not** refetch `/api/rules` unless those files are missing from context.

## Budget

| Reserve | Tokens | Purpose |
| --- | --- | --- |
| Workspace rules | ~50k | AGENTS + CLAUDE (Cursor-injected) |
| Cold-start API | ~3–5k | manifest + condensed orient |
| Task work | ~120–140k | reads, edits, reasoning |
| Headroom | ~10k | tool output spikes |

## Sequence (every session)

```bash
.venv/bin/python scripts/cursor_cold_start.py
```

Equivalent manual calls:

```bash
curl -s http://localhost:8765/api/state/manifest
curl -s http://localhost:8765/api/orient   # parse git, health, delegate, governance only
```

## Skip (orchestrator / 1M lanes)

- `/api/rules` — duplicates workspace rules
- `/api/session/current?agent=orchestrator` — wrong agent
- `context_canary.py mint` — 1M orchestrator sessions only
- `Read` on `CLAUDE.md`, `AGENTS.md`, or `memory/MEMORY.md` at boot

## Fetch on demand (task-scoped)

| Task | Endpoint |
| --- | --- |
| Fleet inbox | `/api/comms/inbox?agent=cursor` |
| Active dispatches | `/api/delegate/active` |
| Track / curriculum | `/api/state/summary`, `/api/state/track-health/{track}` |
| One module | `/api/state/module/{track}/slug/{slug}` |
| Open PRs | `gh pr list` (not full orient replay) |
| Usage limits | CodaxBar.app + `/api/runtime/agents` |

## After local writes

`curl -s 'http://localhost:8765/api/orient?fresh=true'`

## Offline fallback

If Monitor API is down: `git status --short --branch` + read
`agents_extensions/shared/rules/operator-expectations.md` (digest only).
