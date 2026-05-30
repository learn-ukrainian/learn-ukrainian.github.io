# Current - Claude Thread Handoff

> No Claude-specific replacement-thread handoff has been prepared yet.
> Generate one with:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py prepare --agent claude
```

Claude agents should read `docs/session-state/current.md` for the router, then
this file for Claude-specific continuation state. Do not update
`docs/session-state/current.md` unless the task explicitly authorizes a router
update.
