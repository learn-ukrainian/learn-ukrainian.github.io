# ADR-006: Structured logging - defer JSON logging until a log-consuming UI exists

**Status**: Accepted
**Date**: 2026-04-10
**Deciders**: Engineering
**Related**: #1081, `scripts/build/v6_build.py`, `scripts/api/state_helpers.py`, `docs/architecture/adr/adr-004-agent-runtime.md`

## Context

Issue #1081 asked whether the project should adopt structured application logging with `python-json-logger`, `structlog`, or a stdlib logging JSON config. The current codebase does not rely on centralized log ingestion for core workflow visibility.

Instead, the build and orchestration paths already persist structured phase events into module `state.json` files via the internal `_log()` helper and the API helpers that read orchestration state. That state is what the project actually inspects during debugging, review, and pipeline recovery.

Switching stdout or file logging to JSON right now would add a second structured event stream beside `state.json`. That creates duplication unless a consumer exists that prefers process logs over orchestration state.

## Decision

Defer adoption of a new structured-logging library for now and keep the current status quo: stdlib logging where needed, `_log()` phase events for orchestration truth, and no new JSON logging dependency.

Evaluation summary:

| Option | Integration cost | Observability benefit now | Alignment with existing `state.json` events | Result |
|---|---:|---:|---:|---|
| Status quo (`_log()` + selective stdlib logging) | 1/5 | 3/5 | 5/5 | Keep now |
| stdlib logging with JSON formatter config | 2/5 | 2/5 | 2/5 | Reject for now |
| `python-json-logger` | 3/5 | 3/5 | 2/5 | Reject for now |
| `structlog` | 4/5 | 4/5 | 3/5 | Reject for now |

The trigger to revisit this decision is clear: once a multi-agent web UI or another external consumer needs live machine-readable process logs, reevaluate whether `structlog` or JSON-formatted stdlib logging gives the best path.

## Alternatives considered

- **`python-json-logger`**: lowest-friction path to JSON output for existing `logging` calls, but it mainly reformats process logs. It does not replace or simplify the state-machine data already written to `state.json`.
- **`structlog`**: strongest developer ergonomics for contextual structured events, but it would require broader call-site changes and conventions. That cost is hard to justify before there is a live consumer for those events.
- **Stdlib logging config only**: avoids a new dependency, but still creates a parallel JSON log channel with little benefit unless the team starts ingesting logs centrally.
- **Status quo**: keeps one authoritative structured stream today. The main downside is weaker ad hoc process-log searchability compared with a true JSON logging pipeline.

## Consequences

**Positive**:
- Avoids adding logging dependencies and migration churn during active v6 pipeline work.
- Preserves `state.json` as the single source of truth for phase progression and recovery.
- Keeps future options open when the actual consumer requirements are clearer.

**Negative / risks**:
- Process logs remain less queryable than JSON logs in external tooling.
- If a UI starts tailing subprocess logs before this is revisited, the project may need a rushed follow-up change.

**Neutral / follow-ups**:
- Re-evaluate when the multi-agent web UI lands or when logs need to feed an external collector.
- If revisited, compare `structlog` against JSON-formatted stdlib logging using one real UI log-consumption path, not a hypothetical benefit.

## Expiry

Revisit by **2026-10-01**. If no UI or centralized log consumer exists by then, renew or supersede this ADR with current evidence.
