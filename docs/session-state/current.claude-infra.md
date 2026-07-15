# Current — Claude INFRA / CODE lane role handoff

> **Lane:** infrastructure + our code — pipeline, gates, tooling, build, CI, schemas,
> harness, Atlas/lexicon. SEPARATE from the folk/seminar Claude (agent `claude`) and from
> the curriculum track-orchestrators.
>
> **Handoff identity:** `claude-infra`. Launch with **`./start-claude.sh --agent infra-orchestrator`**
> and/or **`--epic harness`**: the launcher derives `SESSION_HANDOFF_AGENT=claude-infra` from either
> flag (via `scripts/lib/handoff_identity.sh` — harness is a canonical alias for this lane, not a
> phantom `claude-harness` slot; #5201), so the SessionStart hook routes cold-start to this lane's own
> slot (`.agent/claude-infra-thread-handoff.md` + `.agent/thread-rollovers/claude-infra/`) instead of
> the shared `claude` slot. A bare `claude` / `./start-claude.sh` with no `--agent` (or
> `--agent curriculum-orchestrator`) defaults to agent `claude`, which the folk driver and
> track-orchestrators also use — that shared slot is the cold-start collision this lane was created
> to avoid. (One launcher, one agent/epic flag — there is no separate `start-claude-infra.sh`.)

## Cold-start
1. `git fetch origin`
2. `gh pr list --search 'author:@me' --state open`
3. Use the validated automatic SessionStart rollover output as authoritative. Do not manually parse flat handoff files or leases if a rollover packet was surfaced at startup.
4. If the SessionStart hook output is unavailable, or the API is down, or the hook explicitly surfaces the legacy file, use the legacy flat file fallback: `.agent/claude-infra-thread-handoff.md` (gitignored, machine-local).
5. Orient via Monitor API (lean cold-start mode): `curl -s --max-time 2 "http://127.0.0.1:8765/api/orient?lean=true&session=$CLAUDE_CODE_SESSION_ID"`


## Lane boundaries
- Infra/code only. Do NOT touch the folk/seminar content lane
  (`.agent/claude-thread-handoff.md`, `docs/folk-epic/`) or any track's content.
- Keep the main checkout read-only for committed work; use dispatch worktrees.
- Shared git identity across agents is expected — judge work by content + lane, never flag
  identity collisions (it is noise the user does not want).
- Merge ownership: I merge PRs I drive in my lane (infra/code/Atlas) once fleet/off-seat review clears
  them AND blocking CI is green — INCLUDING my agent-def/governance/settings/hooks/launcher changes. The
  user does NOT merge; do not park PRs (#M-12). Honor blocking CI (#M-0.5; never `--admin`). Content/
  track-lane PRs keep their own protocol (Codex/main reconciles).

> The live, session-by-session infra queue is hand-maintained in the gitignored
> `.agent/claude-infra-thread-handoff.md` (machine-local runtime state, never committed).
> This committed file is the durable pointer so a fresh clone knows the lane exists and how
> to enter it.
