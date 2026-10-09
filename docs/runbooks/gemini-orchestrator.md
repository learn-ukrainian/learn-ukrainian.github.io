# Gemini Launcher Runbook

> **Gemini may drive epics (2026-10-08 approval)** through `start-gemini-driver.sh`
> (see `docs/runbooks/epic-orchestrator-roster.md`). Design input and designated approval
> stay with `gpt-6.1-sol` and `claude-opus-5-5`. Standalone sessions take bounded, fully
> specified work and Ukrainian content review.

## Launcher

`start-gemini.sh` is the native Antigravity (`agy`) CLI launcher for Gemini. It mirrors `start-claude.sh` and `start-grok.sh` but targets the Gemini seat.

## Usage

```bash
# Standalone AGY session for bounded work or Ukrainian content review
./start-gemini.sh --model gemini-3.8-flash-high

# Gemini Pro only on explicit request
./start-gemini.sh --model gemini-3.1-pro-high

# Forward AGY arguments after the launcher separator
./start-gemini.sh -- --sandbox read-only
```

`start-gemini-driver.sh --epic <lane>` launches a Gemini epic driver through
the shared driver path (2026-10-08 approval): scope entry, rules core, deploy,
stream lease, provider canary and drive-epic binding, the same shape as the
other driver entrypoints. The driver defaults to `gemini-3.1-pro-high`;
`--model gemini-3.8-flash-high` is also certified. Any other Gemini model id
exits with code 4 before startup, and so does a Gemini model id given to
another provider's driver. `--epic` and `--force` are rejected by the
standalone launcher; it never claims a driver lease.

```bash
./start-gemini-driver.sh --epic infra
./start-gemini-driver.sh --epic infra --model gemini-3.8-flash-high
```

## Launcher Flags

| Flag | Meaning |
| --- | --- |
| `--model <id>` | Gemini model (standalone default `gemini-3.8-flash-high`, Pro on explicit request; driver default `gemini-3.1-pro-high`, `gemini-3.8-flash-high` also certified; a forwarded `--model` after `--` is refused for the driver) |
| `--harness agy` | Native Antigravity harness; other harnesses are refused |
| `--help` | Show launcher help without starting a session |
| `--` | Forward remaining arguments to AGY |

Standalone `start-gemini.sh` and `delegate.py --agent agy` remain available
for their permitted non-driver roles. The rules core is included in the
standalone session. Gemini driver slots are listed in
`scripts/config/area_assignments.yaml` wherever Codex has one, and
`handoff_identity_for_gemini_epic` names the `gemini-<lane>` slot.

## Fleet Management & Rate Limits

The driver of record (Opus 5.5 or Sol 6.1) monitors usage across the fleet using the native fleet probes:

```bash
.venv/bin/python -m scripts.fleet.usage show --fresh
```

Use `scripts.fleet.usage show` to verify credits, quota windows, and availability before dispatching. `--fresh` bypasses the cached Monitor snapshot. CodexBar v0.69.0 remains a manual cross-check (`codexbar usage --provider <provider> --format json --no-color`); JSON enables its optional Codex reset inventory. Reset credits are informational and spending one requires an operator decision.

## Advisor Approval Gate

All architecture, file layout, and process decisions require designated approval: the operator, or the designated advisors (**Opus 5.5** `claude-opus-5-5` and **Sol 6.1** `gpt-6.1-sol`) agreeing; when one of them authored the proposal, the other's approval completes it; a proposal by any other agent, Gemini included, needs both; if they disagree, the operator decides. When Gemini is the driver of record, it owns task breakdown and fleet routing for its stream; architecture, layout and process changes still need designated approval.
