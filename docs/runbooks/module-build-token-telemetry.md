# Module Build Token Telemetry Runbook

This runbook is the source of truth for token telemetry on module-build work.
Every module-build PR should persist one telemetry record through the local
Monitor API and include the same summary in the PR body or merge note.

## Required Fields

Every record must state whether a swarm was used:

- `swarm_used: true` means at least one helper/subagent/reviewer thread did
  bounded work for the module build.
- `swarm_used: false` means the module was built solo. The record still needs
  a `swarm_note`, for example `solo run; no swarm used`.

Every record should also include:

- `level` and `slug`
- `run_id`, stable for the PR or build attempt
- `branch`, `commit_sha`, `pr_number`, and `pr_url` when known
- `status`, usually `draft`, `ready`, `merged`, or `abandoned`
- `wall_clock_minutes` when known
- `source`, such as `codex-final`, `dispatch-meta`, `api-usage`, or `manual`
- one participant per main agent, helper, reviewer, validator, or subagent

Token fields may be actual or estimated, but the `token_source` field must say
which. Use `unavailable` rather than inventing numbers when no telemetry exists.

## API

Persist telemetry with:

```bash
curl -s -X POST http://localhost:8765/api/telemetry/module-builds \
  -H 'Content-Type: application/json' \
  -d '{
    "run_id": "b1-m13-pr3148",
    "level": "b1",
    "slug": "alternation-consonants-verbs",
    "branch": "codex/b1-m13-alternation-verbs",
    "commit_sha": "7066d5f506",
    "pr_number": 3148,
    "pr_url": "https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/3148",
    "status": "merged",
    "swarm_used": true,
    "swarm_label": "thin",
    "swarm_note": "Used bounded reviewers and validation runner.",
    "wall_clock_minutes": 30.5,
    "source": "codex-final",
    "participants": [
      {
        "role": "main",
        "agent": "codex",
        "model": "gpt-5.5",
        "effort": "xhigh",
        "label": "integration",
        "prompt_tokens": 120000,
        "response_tokens": 18000,
        "token_source": "estimated"
      },
      {
        "role": "helper",
        "agent": "gemini",
        "model": "gemini-3.1-pro-preview",
        "label": "independent review",
        "total_tokens": 42000,
        "token_source": "estimated"
      }
    ]
  }'
```

Read recent records:

```bash
curl -s 'http://localhost:8765/api/telemetry/module-builds?level=b1'
curl -s 'http://localhost:8765/api/telemetry/module-builds/b1/alternation-consonants-verbs'
curl -s 'http://localhost:8765/api/telemetry/module-builds?swarm_used=false'
```

The SQLite store lives under `data/telemetry/` and is local runtime state. Do
not add the database file to PRs.

## PR Summary Format

Use this shape in module-build PR bodies and final orchestration notes:

```text
Token telemetry:
- swarm_used: true
- swarm_label: thin
- swarm_note: Used bounded reviewers and validation runner.
- wall_clock_minutes: 30.5
- token_source: estimated
- main: codex gpt-5.5 xhigh, 138000 tokens
- helpers: gemini independent review, 42000 tokens
- total_tokens: 180000
```

For solo work:

```text
Token telemetry:
- swarm_used: false
- swarm_label: none
- swarm_note: Solo run; no swarm used because scope was narrow.
- token_source: unavailable
```

## Estimation Rules

Prefer actual provider or transcript usage. If unavailable:

- Use persisted dispatch metadata when present.
- Use character-count estimates only when clearly marked `estimated`.
- Keep helper/reviewer rows separate from the main integrator row.
- Record wall-clock separately from token volume; swarms may be faster while
  still using more aggregate tokens.
