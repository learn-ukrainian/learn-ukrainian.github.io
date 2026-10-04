# Cursor cold start

Cursor already loads `AGENTS.md` + `CLAUDE.md` as workspace rules; those files
are digests. Load the sources for the task and current phase through
`agents_extensions/shared/rules/task-scoped-reading.md` (served as
`/api/rules?scope=task:<name>`). The complete `/api/rules?format=markdown` is
for full policy audits, ambiguous cross-cutting tasks and clients that need the
whole ruleset. `scripts/cursor_cold_start.py` hits `/api/rules?format=json` and
prints the hash and source list; it does not reprint the rules blob.

## Sequence (every session)

```bash
.venv/bin/python scripts/cursor_cold_start.py
```

Manual equivalents:

```bash
curl -s http://localhost:8765/api/state/manifest
curl -s 'http://localhost:8765/api/rules?scope=task:<name>'   # task/phase sources
curl -s http://localhost:8765/api/orient   # parse git, health, delegate, governance only
```

## Skip (orchestrator / 1M lanes)

- `/api/session/current?agent=orchestrator` — wrong agent
- `context_canary.py mint` — 1M orchestrator sessions only
- `Read` on `CLAUDE.md` or `AGENTS.md` at boot

## Fetch on demand (task-scoped)

| Task | Endpoint |
| --- | --- |
| Rules for a task or phase | `/api/rules?scope=task:<name>` |
| Fleet inbox | `/api/comms/inbox?agent=cursor` |
| Active dispatches | `/api/delegate/active` |
| Track / curriculum | `/api/state/summary`, `/api/state/track-health/{track}` |
| One module | `/api/state/module/{track}/slug/{slug}` |
| Open PRs | `gh pr list` (not full orient replay) |
| Usage limits | `.venv/bin/python -m scripts.fleet.usage show` + `/api/runtime/agents` |

Fleet launchers route eligible 2-to-4-seat read-only `ask-*` and `discuss` calls
through the durable ACP controller automatically. Enabled participants resolve
from the live ACP participant registry (`ACPX_SUPPORTED_PARTICIPANTS` in
`scripts/agent_runtime/adapters/acpx.py`), not from this file; seats such as Codex
or Pool are examples, never an eligibility list. Kimi seats are refused even when
named in the registry: web, UI and backend coding only. A participant count outside
2–4 is rejected before a conversation starts. There is no bridge/provider-execution fallback: an ACP
failure, timeout or partial result is a typed durable outcome and never
silently replays provider calls over bridge. ACP does not replace fleet
coordination or formal review; review, design and plan run on toolful native
seats. Follow `docs/runbooks/agent-seat-onboarding.md` for the direct operator
command, busy/partial behavior, and receipt-verification contract.

## After local writes

`curl -s 'http://localhost:8765/api/orient?fresh=true'`

## Offline fallback

If Monitor API is down: `git status --short --branch` + read
`agents_extensions/shared/rules/_load-via-api.md` and its ordered local
fallback list.

## Rules hash refresh (no Monitor restart)

`GET /api/rules` reads rule files **live from the Monitor project checkout** on
every request (ETag = content SHA-256). After a rules PR merges and the primary
checkout is pulled, the next cold-start /rules fetch sees the new hash — **do not
restart Monitor** for rule text. Long-running driver *sessions* that already
injected an old rules blob into context must **re-fetch** `/api/rules` or start a
new session; a TUI driver relaunch re-runs cold start and picks up the new hash.
