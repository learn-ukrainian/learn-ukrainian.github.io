---
description: 200k-context cold start — Monitor API live state plus /api/rules
alwaysApply: true
---

# Cold start (Cursor · 200k)

**At session start, before other work:**

```bash
scripts/pre_commit/project_python.sh -I -m lu_machinery.cursor_cold_start
```

The script fetches `/api/rules`. Cursor already has `AGENTS.md` + `CLAUDE.md` as workspace rules (~50k tokens); those are digests, not a substitute for `/api/rules`.

## Do not fetch at boot

- `/api/session/current?agent=orchestrator` — wrong agent lane
- `context_canary.py mint` — 1M orchestrator only
- `Read` on `CLAUDE.md`, `AGENTS.md`

## Fetch at boot

| Need | Call |
| --- | --- |
| Canonical rules | `/api/rules?format=markdown` (script hits `/api/rules?format=json`) |

## Fetch on demand

| Need | Call |
| --- | --- |
| Fleet inbox | `/api/comms/inbox?agent=cursor` |
| Dispatches | `/api/delegate/active` |
| Track state | `/api/state/summary` |
| Track health | `/api/state/track-health/{track}` |
| One module | `/api/state/module/{track}/slug/{slug}` |
| Open PRs | `gh pr list` |
| Usage limits | `/api/runtime/agents` |
| After commit | `/api/orient?fresh=true` |

If Monitor is unavailable, run `git status --short --branch` and follow the
offline rules loader in the installed release (`agents_extensions/shared/rules/_load-via-api.md`).
After the rules change, fetch `/api/rules` again to refresh the session's rules.

For read-only `ab discuss` routing and receipts, see
`docs/runbooks/agent-seat-onboarding.md`. ACP discussion carries no formal review verdict.
