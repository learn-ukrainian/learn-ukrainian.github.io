# Session state

Fleet-comms owns coordination. Do not add handoffs in this directory.

`thread_handoff.py` does not write `current.md`. The `current.*.md` files and
`codex-orchestrator-handoff.md` stay only as the compatibility routes named by
`lu_machinery/api/session_router.py`. Dated handoffs and `pending-dispatches/` were
removed (#8457).
