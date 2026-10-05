# Gemini Launcher Runbook

> **Gemini 3.8 Flash (AGY) is not a planning, design or driver seat** (operator decision
> 2026-10-03, #9584). Epic driving belongs to `gpt-6.1-sol` and `claude-opus-5-5`
> (see `docs/runbooks/epic-orchestrator-roster.md`). Use Gemini for bounded, fully specified
> work and Ukrainian content review. The former driver entrypoint is a refusing
> compatibility stub (#9633).

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

`start-gemini-driver.sh` is retained as a refusing compatibility stub. Every
AGY/Gemini driver attempt exits with code 4 and names `claude-opus-5-5`
(Opus 5.5), `gpt-6.1-sol` (Sol 6.1), and the `grok-4.7` driver fallback.
The shared launcher refuses before root resolution, adapter preflight,
deployment, stream lease, canary or provider execution, including dry-run
and forced attempts. Help remains read-only. `--epic` and `--force` are
rejected by the standalone launcher; it never claims a driver lease.

## Launcher Flags

| Flag | Meaning |
| --- | --- |
| `--model <id>` | Gemini model (`gemini-3.8-flash-high` by default; Pro on explicit request) |
| `--harness agy` | Native Antigravity harness; other harnesses are refused |
| `--help` | Show launcher help without starting a session |
| `--` | Forward remaining arguments to AGY |

Standalone `start-gemini.sh` and `delegate.py --agent agy` remain available
for their permitted non-driver roles. The rules core is included in the
standalone session. Gemini driver slots are absent from
`scripts/config/area_assignments.yaml`; the legacy handoff identity resolver
is retained solely for historical packet lookup.

## Fleet Management & Rate Limits

The driver of record (Opus 5.5 or Sol 6.1) monitors usage across the fleet using the native fleet probes:

```bash
.venv/bin/python -m scripts.fleet.usage show --fresh
```

Use `scripts.fleet.usage show` to verify credits, quota windows, and availability before dispatching. `--fresh` bypasses the cached Monitor snapshot. CodexBar v0.69.0 remains a manual cross-check (`codexbar usage --provider <provider> --format json --no-color`); JSON enables its optional Codex reset inventory. Reset credits are informational and spending one requires an operator decision.

## Advisor Approval Gate

All architecture, file layout, and process decisions require designated approval: the operator, or the designated advisors (**Opus 5.5** `claude-opus-5-5` and **Sol 6.1** `gpt-6.1-sol`) agreeing; when one of them authored the proposal, the other's approval completes it; a proposal by any other agent, Gemini included, needs both; if they disagree, the operator decides. Gemini does not own task breakdown, fleet routing or structural decisions; those stay with the driver of record and the advisors.
