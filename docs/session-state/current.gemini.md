# Current - Gemini Thread Handoff

> No Gemini-specific replacement-thread handoff has been prepared yet.
> Generate one with:

```bash
.venv/bin/python -m lu_machinery.orchestration.thread_handoff prepare --agent gemini
```

Gemini agents should read `docs/session-state/current.md` for the router, then
this file for Gemini-specific continuation state. Do not update
`docs/session-state/current.md` unless the task explicitly authorizes a router
update.
