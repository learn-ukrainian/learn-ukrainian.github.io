# Current — Claude INFRA / CODE lane role handoff

> **Lane:** infrastructure + our code — pipeline, gates, tooling, build, CI, schemas,
> harness, Atlas/lexicon. SEPARATE from the folk/seminar Claude (agent `claude`) and from
> the curriculum track-orchestrators.
>
> **Handoff identity:** `claude-infra`. Launch with **`./start-claude-infra.sh`** so the
> SessionStart hook routes cold-start to this lane's own slot
> (`.agent/claude-infra-thread-handoff.md`) instead of the shared `claude` slot. Plain
> `claude` / `start-claude.sh` (no `SESSION_HANDOFF_AGENT`) defaults to agent `claude`,
> which the folk driver and track-orchestrators also use — that shared slot is the
> cold-start collision this file's lane was created to avoid.

## Cold-start
1. `git fetch origin`
2. `gh pr list --search 'author:@me' --state open`
3. `curl -sS http://127.0.0.1:8765/api/orient`
4. Read the live queue: `.agent/claude-infra-thread-handoff.md` (gitignored, machine-local — START HERE).

## Lane boundaries
- Infra/code only. Do NOT touch the folk/seminar content lane
  (`.agent/claude-thread-handoff.md`, `docs/folk-epic/`) or any track's content.
- Keep the main checkout read-only for committed work; use dispatch worktrees.
- Shared git identity across agents is expected — judge work by content + lane, never flag
  identity collisions (it is noise the user does not want).
- Self-merge grant: green + off-seat-reviewed infra PRs may be self-merged; honor blocking CI.

> The live, session-by-session infra queue is hand-maintained in the gitignored
> `.agent/claude-infra-thread-handoff.md` (machine-local runtime state, never committed).
> This committed file is the durable pointer so a fresh clone knows the lane exists and how
> to enter it.
