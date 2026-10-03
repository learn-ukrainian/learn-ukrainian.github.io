# Gemini Launcher Runbook

> **Gemini 3.8 Flash (AGY) is not a planning, design or driver seat** (operator decision
> 2026-10-03, #9584). Epic driving belongs to `gpt-6.1-sol` and `claude-opus-5-5`
> (see `docs/runbooks/epic-orchestrator-roster.md`). Use Gemini for bounded, fully specified
> work and Ukrainian content review. The driver entrypoint below remains in the launcher
> estate only for existing operator tooling; it is not a routing recommendation. Gemini 4 is
> re-evaluated at general availability.

## Launcher

`start-gemini.sh` is the native Antigravity (`agy`) CLI launcher for Gemini. It mirrors `start-claude.sh` and `start-grok.sh` but targets the Gemini seat.

## Usage

```bash
# Pin a lane and auto-claim the stream lease through the driver entrypoint
./start-gemini-driver.sh --epic atlas

# Optional: Use Gemini 3.1 Pro High on explicit request (Flash is default for routine and deep)
./start-gemini-driver.sh --epic harness --model gemini-3.1-pro-high

# Pass an explicit driver prompt after the core's binding
./start-gemini-driver.sh --epic atlas "check issue streams and open PRs"

# Non-epic mode — standard agy session
./start-gemini.sh --model gemini-3.8-flash-high
```

## Launcher Flags

| Flag | Meaning |
| --- | --- |
| `--epic <name>` | Pin lane (atlas, harness, hramatka, …) |
| `--stream <id>` | Override stream id (default derived from epic) |
| `--handoff-agent <id>` | Override `SESSION_HANDOFF_AGENT` |
| `--model <id>` | Gemini model (`gemini-3.8-flash-high` [default], `pro` / `gemini-3.1-pro-high` [explicit request only]) |
| `--no-always-approve` | Require manual tool approval (do not pass `--dangerously-skip-permissions`) |
| `--help-launcher` | Show launcher help |

All positional prompt arguments are passed to `agy -i <prompt>` for interactive session startup.

## Cold-Start Flow with `--epic`

1. Launcher resolves the epic to a stream id via `scripts/lib/session_supervisor.sh`.
2. Launcher calls the common session supervisor (`scripts.session_supervisor open --role driver`) with agent `gemini` / harness `agy`.
3. Launcher sources `SESSION_STREAM_*` from supervisor output.
4. Launcher writes a capsule to `.agent/session-capsules/<stream>/`.
5. Launcher injects an auto-continue prompt if no prompt was supplied.
6. Launcher execs `agy -i <prompt> --model <model> --dangerously-skip-permissions`.

The cold-start prompt explicitly tells Gemini **not** to open or resume the lease — the launcher has already claimed it.

## Gemini Model Selection

- **`gemini-3.8-flash-high`** (Default): Extremely fast, high throughput; default for routine AND deep bounded work (operator 2026-09-22: 3.8 Flash High outperforms 3.1 Pro).
- **`gemini-3.1-pro-high`** (`--model pro`): Deep reasoning (1M-2M context window); superseded as deep default by 3.8 Flash High; only on explicit request.

## Handoff Identity

| Epic | `SESSION_HANDOFF_AGENT` |
| --- | --- |
| atlas, hramatka, folk, bio, … | `gemini-<epic>` |
| harness / infra | `gemini-infra` |
| devops | `gemini-devops` |

## Fleet Management & Rate Limits

The driver of record (Opus 5.5 or Sol 6.1) monitors usage across the fleet using the native fleet probes:

```bash
.venv/bin/python -m scripts.fleet.usage show --fresh
```

Use `scripts.fleet.usage show` to verify credits, quota windows, and availability before dispatching. `--fresh` bypasses the cached Monitor snapshot. CodexBar v0.69.0 remains a manual cross-check (`codexbar usage --provider <provider> --format json --no-color`); JSON enables its optional Codex reset inventory. Reset credits are informational and spending one requires an operator decision.

## Advisor Approval Gate

All architecture, file layout, and process decisions require designated approval: the operator, or the designated advisors (**Opus 5.5** `claude-opus-5-5` and **Sol 6.1** `gpt-6.1-sol`) agreeing; when one of them authored the proposal, the other's approval completes it; a proposal by any other agent, Gemini included, needs both; if they disagree, the operator decides. Gemini does not own task breakdown, fleet routing or structural decisions; those stay with the driver of record and the advisors.
