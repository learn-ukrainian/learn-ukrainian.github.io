# Kimi orchestrator runbook

## Launcher

`start-kimi.sh` is the native Kimi Code CLI launcher. It mirrors `start-grok.sh` but targets the Kimi seat.

## Usage

```bash
# Pin a lane and auto-claim the stream lease
./start-kimi.sh --epic atlas

# Explicit stream override
./start-kimi.sh --epic atlas --stream epic:4387

# Use K3 for a consequential review
./start-kimi.sh --epic harness --model k3 "review the open PR"

# No epic — plain kimi prompt mode (no supervisor claim)
./start-kimi.sh --model k2.7-coding "summarize the diff"
```

## Launcher-only flags

| Flag | Meaning |
| --- | --- |
| `--epic <name>` | Pin lane (atlas, harness, hramatka, …) |
| `--stream <id>` | Override the stream id (default derived from epic) |
| `--handoff-agent <id>` | Override `SESSION_HANDOFF_AGENT` |
| `--model <id>` | Kimi model (default: `k2.7-coding`) |
| `--help-launcher` | Show launcher help |

All other arguments are treated as the prompt passed to `kimi -p …`.

## Cold-start flow with `--epic`

1. Launcher resolves the epic to a stream id.
2. Launcher calls the common session supervisor (`scripts.session_supervisor open --role driver`) with agent `kimi` / harness `kimi-code`.
3. Launcher sources `SESSION_STREAM_*` from supervisor output.
4. Launcher writes a capsule to `.agent/session-capsules/<stream>/`.
5. Launcher injects an auto-continue prompt if none was supplied.
6. Launcher execs `kimi -p <prompt> -m <model> --output-format stream-json`.

The cold-start prompt explicitly tells the model **not** to open or resume the lease — the launcher has already claimed it.

## Models

| Short name | Maps to | Use case |
| --- | --- | --- |
| `k2.7-coding` | `kimi-code/kimi-for-coding` | Routine / bounded coding (default) |
| `k2.7-coding-highspeed` | `kimi-code/kimi-for-coding-highspeed` | Fast routine work |
| `k3` | `kimi-code/k3` | Consequential coding, deep review, cross-family review |

K3 is always max effort; an explicit `--effort` is ignored for K3.

## Handoff identity

| Epic | `SESSION_HANDOFF_AGENT` |
| --- | --- |
| atlas, hramatka, folk, bio, … | `kimi-<epic>` |
| harness / infra | `kimi-infra` |

## Session lifecycle

- Lease is claimed by the launcher PID (which becomes the `kimi` PID after `exec`).
- Heartbeat / clean-close hooks are available via `agents_extensions.shared.session_streams hook` but are not automatically wired for Kimi in PR-J1; call them explicitly if a long-running prompt session needs to keep the lease alive.
- End-of-session canary policy follows the same `FAIL-HANDOFF (<8/10)` rule as Grok.

## No lease folklore

The model must not:
- Call `scripts.session_supervisor` open/close, `handoff-claim`, or any other lease lifecycle command.
- Invent a second stream lease.
- Ignore the `SESSION_STREAM_ID` already exported by the launcher.

If the launcher fails to claim the lease, it exits before starting Kimi.

## Related

- `start-kimi.sh`
- `scripts/lib/session_supervisor.sh`
- `docs/runbooks/session-supervisor.md`
- `scripts/agent_runtime/adapters/kimi.py`
