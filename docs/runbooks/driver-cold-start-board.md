# Driver Cold Start Board & Handoff Runbook

**Status:** Sol PR-2 / WP-A + WP-D operational  
**Authority:** `scripts/fleet_comms/cold_start_board.py` · `scripts/fleet_comms/cli.py`  
**Binding doctrine:** `agents_extensions/shared/rules/fleet-comms-coordination.md`

## Purpose

The **Driver Cold Start Board** provides a fail-open, read-only diagnostic briefing for drivers and launchers entering a session. It aggregates environment, message plane status, delivery backlog, bottleneck metrics, session stream handoff diagnosis, agent inbox state, GitHub PR status, and single-token needle searches into a unified board capped at 16KiB.

The board operates strictly read-only: it **never** claims session leases, writes to databases, or posts to external APIs.

---

## CLI Usage

Run the cold start board using the `fleet_comms` CLI module:

```bash
# Default JSON briefing to stdout
.venv/bin/python -m scripts.fleet_comms cold-start-board

# Formatted Markdown briefing for agent context injection
.venv/bin/python -m scripts.fleet_comms cold-start-board --format markdown

# Scoped to specific stream, agent, and single-token search needle
.venv/bin/python -m scripts.fleet_comms cold-start-board \
    --format json \
    --stream-id epic:4707 \
    --agent agy/cold-start-pr2-board \
    --needle cold_start
```

### CLI Arguments

| Argument | Description | Default |
| --- | --- | --- |
| `--format` | Output format: `json` or `markdown` | `json` |
| `--stream-id` | Target session stream ID (e.g. `epic:4707`) | `$SESSION_STREAM_ID` |
| `--agent` | Target agent identifier | `$SESSION_HANDOFF_AGENT` or `$AGENT` |
| `--needle` | Single-token search string across diagnostic status | None |
| `--root` | Fleet-comms plane root override | Auto-resolved |
| `--repo-root` | Repository root override | Current working directory |

---

## Diagnostic Probes & Fail-Open Contract

The board executes 10 diagnostic probes. Each probe measures execution timing (`elapsed_ms`) and returns a fail-open status (`ok`, `degraded`, `error`, or `skipped`):

1. **`capsule_session_env`**: Session env vars (`SESSION_STREAM_ID`, `SESSION_HANDOFF_AGENT`, `LU_AGENT_COMM_TRANSPORT`, `FLEET_COMMS_PLANE_MODE`, `CAPSULE_ID`, `SESSION_ID`, `TASK_ID`, `CORRELATION_ID`).
2. **`plane_status`**: Fleet-comms message plane mode, schema version, and parity telemetry.
3. **`backlog_and_dead_letters`**: Message delivery backlog and dead-letter inventory metadata.
4. **`bottleneck_slice`**: Per-stream dispatch and lifecycle bottleneck metrics (uses fast local lookup without external network latency).
5. **`orient_lean`**: Fast local query to Monitor API `/api/orient` (0.5s timeout) with fail-open fallback to local `git` branch and head commit SHA.
6. **`issues_streams_membership`**: Top open issues and stream memberships.
7. **`session_streams_and_handoff`**: Stream digest entries (pinned/recent) and read-only handoff diagnosis (`diagnose_handoff`).
8. **`inbox_check`**: Pending message deliveries addressed to the target agent.
9. **`gh_pr_list`**: Best-effort query via `gh pr list` (if `gh` CLI tool is present on `PATH`).
10. **`needle_search`**: Single-token substring search across all collected probe data.

### Size Capping & Safety Guarantees

- **String Length Cap:** Individual strings in probe outputs are capped at **200 characters** (truncated with `...[truncated N chars]`).
- **List Length Cap:** Data lists are capped at **5 items** (truncated with `{"_truncated": "N items omitted"}`).
- **Overall Board Cap:** Total board output is strictly capped at **16KiB (16,384 bytes)**. Oversized payloads apply stricter truncation and append `"_board_truncated": true`.
- **Zero Side-Effects:** Exit code is `0` whenever a board is emitted (even if degraded). No leases are claimed, no SQLite databases are mutated, and no HTTP `POST` requests are made.

---

## WP-D: Entire-Context Handoff & Closed-Issue Recipe

When drivers record or consume entire-context handoffs during session transitions:

### 1. `bootstrap-git` for Closed Issues

- **Closed Issue Limitation:** Closed GitHub issues **cannot** be indexed using `bootstrap-github-issue` (the GitHub issue API rejects closed issues for bootstrap).
- **Recipe:** Drivers must use `bootstrap-git` with a full 40-character hex commit SHA:

```bash
# Bootstrap entire-context using real commit SHA after merge
.venv/bin/python -m scripts.entire_context bootstrap-git <40-hex-sha>
```

- **SHA Rule:** Always pass real, verified commit SHAs from `git log` or GitHub PR merges. **Do not invent placeholder SHAs** in scripts or code.

### 2. Single-Token Search Needles

- **Substring Matching:** Entire-context search and cold-start board needle searches perform exact single substring matching rather than multi-word natural language parsing.
- **Rule:** Use single-token needles (e.g. `practice`, `cold_start`, `4707`, or a commit SHA fragment).
- **Warning:** Multi-word queries (such as `"practice membership"`) score zero or trigger `seed_invalid` errors when no single entry contains the entire phrase verbatim.

---

## Verification & Testing

To run the suite of unit tests for the cold start board:

```bash
.venv/bin/pytest tests/fleet_comms/test_cold_start_board.py
```
