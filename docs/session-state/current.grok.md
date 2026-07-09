# Current Grok Handoff Pointer

The durable handoff for Grok (xAI) infra / harness work lives at:

`docs/session-state/2026-07-09-grok-infra-handoff.md`

When starting any new Grok session (especially a clean one after context loss or compaction):

1. Run the cold-start checklist in that handoff file.
2. Read the dated handoff completely.
3. Load `agents_extensions/shared/memory/MEMORY.md` (especially the Fleet Comms + Monitor API section added 2026-07-09).
4. Use `git worktree list` + `gh` + Monitor API (`/api/state/*`) to re-orient.
5. Confirm the active grok worktrees and finish any open items (e.g. 4818/4609) before picking new work.

This pointer exists for symmetry with `current.claude*.md`, `current.gemini.md`, `current.orchestrator.md`, and `codex-orchestrator-handoff.md`.

Do not put long session details here — keep the real state in the dated handoff + MEMORY files.

X-Agent reference: see the handoff file.
