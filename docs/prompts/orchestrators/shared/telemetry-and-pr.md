# Shared Telemetry And PR Requirements

Prompt suite component version: 0.2
Last reviewed: 2026-06-21

Module-build and remediation prompts must encode this policy.

## Commit Trailer

Every commit must include an `X-Agent` trailer:

```bash
git commit -m "scope: summary" --trailer "X-Agent: codex/<task-id>"
```

Run the trailer linter before push:

```bash
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

## Module-Build Telemetry

Persist telemetry through the local Monitor API and include the same summary in the PR body or final orchestration note. The SQLite database under `data/telemetry/` is local runtime state and must not be committed.

Required fields include:

- `level`
- `slug`
- `run_id`
- `branch`
- `commit_sha` when known
- `pr_number` and `pr_url` when known
- `status`
- `swarm_used`
- `swarm_label`
- `swarm_note`
- `participants`
- `token_source`

Solo runs still require `swarm_used: false` and a `swarm_note`.

Example API shape. `curl` requires a scheme and host, so set `MONITOR_API_BASE` from the current local runbook or shell context before posting. Do not commit telemetry database files.

```bash
MONITOR_API_BASE="${MONITOR_API_BASE:?set Monitor API base URL from docs/runbooks/module-build-token-telemetry.md}"
curl -s -X POST "${MONITOR_API_BASE%/}/api/telemetry/module-builds" \
  -H 'Content-Type: application/json' \
  -d '{
    "run_id": "<level>-<slug>-<task>",
    "level": "<level>",
    "slug": "<slug>",
    "branch": "codex/<task>",
    "status": "ready",
    "swarm_used": false,
    "swarm_label": "none",
    "swarm_note": "solo run; no swarm used",
    "source": "codex-final",
    "token_source": "unavailable",
    "participants": [
      {
        "role": "main",
        "agent": "codex",
        "model": "<model>",
        "label": "integration",
        "token_source": "unavailable"
      }
    ]
  }'
```

## PR Body Requirements

Module-build and remediation PR bodies should include:

- scope and target modules
- source files changed
- generated MDX files changed
- validation commands and outcomes
- audit findings addressed, if this is remediation
- independent review outcome before merge
- token telemetry summary, including `swarm_used` and `swarm_note`
- statement that no generated `status/`, curriculum `audit/`, curriculum `review/`, or telemetry DB artifacts are included

## Independent Review

Before merge, require an independent-family review. The builder should not be the sole reviewer of its own module work. Record reviewer identity, review scope, and final disposition in the PR body or orchestration note.
