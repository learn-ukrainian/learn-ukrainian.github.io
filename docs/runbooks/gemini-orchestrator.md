# Gemini Orchestrator Runbook

## Launcher

`start-gemini.sh` is the native Antigravity (`agy`) CLI launcher for Gemini. It mirrors `start-claude.sh` and `start-grok.sh` but targets the Gemini seat.

## Usage

```bash
# Pin a lane and auto-claim the stream lease in interactive mode
./start-gemini.sh --epic atlas

# Use Gemini 3.1 Pro High for complex epic planning & orchestration
./start-gemini.sh --epic harness --model pro

# Pass an explicit interactive prompt
./start-gemini.sh --epic atlas "check issue streams and open PRs"

# Non-epic mode — standard agy session
./start-gemini.sh --model gemini-3.6-flash-high
```

## Launcher Flags

| Flag | Meaning |
| --- | --- |
| `--epic <name>` | Pin lane (atlas, harness, hramatka, …) |
| `--stream <id>` | Override stream id (default derived from epic) |
| `--handoff-agent <id>` | Override `SESSION_HANDOFF_AGENT` |
| `--model <id>` | Gemini model (`gemini-3.6-flash-high` [default], `pro` / `gemini-3.1-pro-high`, `gemini-3.5-flash-high`) |
| `--no-always-approve` | Require manual tool approval (do not pass `--dangerously-skip-permissions`) |
| `--help-launcher` | Show launcher help |

All positional prompt arguments are passed to `agy -i <prompt>` for interactive session startup.

## Cold-Start Flow with `--epic`

1. Launcher resolves the epic to a stream id via `scripts/lib/session_supervisor.sh`.
2. Launcher calls the common session supervisor (`scripts.session_supervisor open --role driver`) with agent `gemini` / harness `agy`.
3. Launcher sources `SESSION_STREAM_*` from supervisor output.
4. Launcher writes a capsule to `.agent/session-capsules/<stream>/`.
5. Launcher injects an auto-continue prompt for Gemini Orchestrator if no prompt was supplied.
6. Launcher execs `agy -i <prompt> --model <model> --dangerously-skip-permissions`.

The cold-start prompt explicitly tells Gemini **not** to open or resume the lease — the launcher has already claimed it.

## Gemini Model Selection for Orchestration

- **`gemini-3.6-flash-high`** (Default): Extremely fast, high throughput, great for active task management, issue triage, and worktree dispatching.
- **`gemini-3.1-pro-high`** (`--model pro`): Deep reasoning (1M-2M context window), ideal for complex epic planning, multi-file architecture decisions, and cross-agent review routing.

## Handoff Identity

| Epic | `SESSION_HANDOFF_AGENT` |
| --- | --- |
| atlas, hramatka, folk, bio, … | `gemini-<epic>` |
| harness / infra / devops | `gemini-infra` |

## Fleet Management & Rate Limits (`codexbar`)

Gemini orchestrators monitor usage across the fleet using `codexbar`:

```bash
codexbar usage --format json
```

Use `codexbar` to verify model credits, rate limits, and availability before dispatching tasks to specific agent families (Codex, Claude, Grok, Kimi, Gemini).

## Advisor Approval Gate

All architecture, file layout, and process decisions require approval from designated advisors (**Fable**, **Sol**). Gemini orchestrators manage task breakdown, fleet routing, and verification, but must consult advisors for structural decisions.
