# CI Gate

New workflow (Fable 5.1, 2026-09-03). `.github/workflows/ci.yml` is a short
replacement, not the old two-tier merge-queue file.

`CI Gate` is the only required GitHub check. Same jobs on `pull_request` and
`merge_group`.

| Job | When |
| --- | --- |
| Changes | always (GitHub compare API; `docs_only` / `frontend` / `shards`) |
| Ruff | not docs-only |
| Secret scan | always |
| pytest | always (4 shards for code, 1 `docs_skills` shard for docs/skills) |
| Contracts | not docs-only |
| Frontend | when frontend paths changed |
| CI Gate | always |

Docs/skills PRs (every changed path is docs/, shared skills, agent deploy
trees, or `*.md`) skip ruff/contracts/frontend and run one pytest leg with
`-m docs_skills`. Compare API failure fail-closes to a full code run.

No CF attest. No auto-arm. No landing-class classifier. No coverage floor.
Red team review is out of band.
