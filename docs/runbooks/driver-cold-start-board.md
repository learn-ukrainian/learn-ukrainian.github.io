# Driver Cold Start Board & Handoff Runbook

**Status:** Sol PR-2 / WP-A + WP-D operational  
**Authority:** `scripts/fleet_comms/cold_start_board.py` · `scripts/fleet_comms/cli.py`  
**Binding doctrine:** `agents_extensions/shared/rules/fleet-comms-coordination.md`

## Purpose

The **Driver Cold Start Board** provides a fail-open, read-only diagnostic briefing for drivers and launchers entering a session. It aggregates environment, message plane status, delivery backlog, bottleneck metrics, session stream handoff diagnosis, agent inbox state, GitHub PR status, and single-token needle searches into a unified board capped at 16KiB.

The board operates strictly read-only: it **never** claims session leases, writes to databases, or posts to external APIs.

Drivers should treat the markdown board as the **first** cold-start surface: live plane mode and `board_status` appear in the Summary before any probe dump. Injected drive-epic clauses must resolve live plane mode (never hardcode `mode=off` when live default is `authority`).

---

## CLI Usage

Run the cold start board using the `fleet_comms` CLI module:

```bash
# First command for drivers: Markdown Summary + probes
.venv/bin/python -m scripts.fleet_comms cold-start-board --format markdown

# Default JSON briefing to stdout
.venv/bin/python -m scripts.fleet_comms cold-start-board

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

## Markdown Summary (first screen)

Markdown output leads with a six-line **Summary** before the probe dump:

1. `plane_mode` — live resolved mode (`resolve_plane_mode(None)` / plane-status)
2. `schema_version` — applied (or known) message-plane schema version
3. `inbox_pending` — pending/dispatched delivery count for the target agent
4. `board_status` — headline `ok` or `degraded`
5. `stream_id`
6. `agent`

---

## Diagnostic Probes & Fail-Open Contract

The board executes 10 diagnostic probes. Each probe measures execution timing (`elapsed_ms`) and returns a fail-open status (`ok`, `degraded`, `error`, or `skipped`):

1. **`capsule_session_env`**: Session env vars plus **live** `plane_mode` from `resolve_plane_mode(None)` (env override still honored inside that helper; never hardcode `off`).
2. **`plane_status`**: Fleet-comms message plane mode, schema version, and parity telemetry. **Load-bearing.**
3. **`backlog_and_dead_letters`**: Message delivery backlog and dead-letter inventory metadata. **Load-bearing.**
4. **`bottleneck_slice`**: Per-stream dispatch and lifecycle bottleneck metrics (uses fast local lookup without external network latency).
5. **`orient_lean`**: Fast local query to Monitor API `/api/orient?lean=true` (0.5s timeout). On timeout/unreachable: status **`skipped`** with `reason=monitor_unreachable` and local `git` branch/head fallback — does **not** poison `board_status`.
6. **`issues_streams_membership`**: Top open issues and stream memberships (from orient when reachable).
7. **`session_streams_and_handoff`**: Stream digest entries (pinned/recent) and read-only handoff diagnosis (`diagnose_handoff`). DB path resolves via git common-dir / primary checkout `.agent/session-streams/v1/session-streams.sqlite3` (dispatch worktrees must not false-miss). Missing DB / no `stream_id` → `skipped`. **Load-bearing only when the DB exists and the probe degrades/errors.**
8. **`inbox_check`**: Pending message deliveries addressed to the target agent. **Load-bearing.**
9. **`gh_pr_list`**: Best-effort query via `gh pr list` (if `gh` CLI tool is present on `PATH`). Never flips the headline.
10. **`needle_search`**: Single-token substring search across all collected probe data. Never flips the headline.

### `board_status` rules

- Headline is **`degraded`** only when a **load-bearing** probe is `degraded` or `error`: `plane_status`, `inbox_check`, `backlog_and_dead_letters`, and `session_streams_and_handoff` when `db_exists` and the probe raised.
- `skipped` / `orient_lean` / `needle_search` / `gh_pr_list` (and other optional probes) must **not** flip the headline to DEGRADED.

### Size Capping & Safety Guarantees

- **String Length Cap:** Individual strings in probe outputs are capped at **200 characters** (truncated with `...[truncated N chars]`).
- **List Length Cap:** Data lists are capped at **5 items** (truncated with `{"_truncated": "N items omitted"}`).
- **Overall Board Cap:** Total board output is strictly capped at **16KiB (16,384 bytes)**. Oversized payloads apply stricter truncation and append `"_board_truncated": true`.
- **Zero Side-Effects:** Exit code is `0` whenever a board is emitted (even if degraded). No leases are claimed, no SQLite databases are mutated, and no HTTP `POST` requests are made.

---

## Injected drive-epic clause (launchers)

`scripts/lib/fleet_comms_cold_start.sh` / `launcher_bind_drive_epic`:

- Export `FLEET_COMMS_PLANE_MODE="${FLEET_COMMS_PLANE_MODE:-$(fleet_comms_resolve_plane_mode)}"` before building the clause.
- `fleet_comms_cold_clause` resolves live mode when the env var is unset/empty (same as the banner). Never default the injected sentence to `off` when live mode is `authority`.
- Plane-mode resolve uses the checkout `.venv` or the primary interpreter via `git rev-parse --git-common-dir` so sparse dispatch worktrees still tell the truth.

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
.venv/bin/pytest tests/fleet_comms/test_cold_start_board.py tests/test_fleet_comms_launcher_awareness.py
```
