# Required CI gate

The `CI Gate` status is the repository's required integration check. It is
unconditional on pull requests, merge groups, and pushes to `main`.

## What a green gate guarantees

- Pytest collects the complete repository suite with the default marker filter
  disabled. It never asks which files changed.
- Five deterministic node-level shards run the resulting suite. The
  thread-sensitive and source-inventory nodes remain within their own external
  shard, while all other nodes are balanced by node count.
- Each shard writes its planned and executed node IDs. `CI Gate` rejects a
  missing artifact, duplicate node, empty plan, incomplete execution report,
  failed job, cancelled job, or skipped job.
- Pytest has full Git history and CPU Torch. The evidence plugin applies
  `SOURCES_MCP_NO_MLX=1` to wiki nodes only, preserving the separate MLX
  override contract test. Tests requiring ignored databases or ignored external
  JSONL retain their explicit pytest skip reason instead of failing
  mysteriously.
- One combined web-and-quality job runs Ruff, Actionlint, frontend unit tests,
  a production build, and Chromium browser tests. Alongside the five pytest
  shards, it caps the normal concurrent runner demand at six slots.

The workflow reports a measured duration in every job summary. The pytest
evidence verifier also reports the measured duration of each shard.

## Time bounds

Pytest uses a 15-minute per-test timeout and a 30-minute wrapper that writes a
named timeout record before the 35-minute GitHub job limit. The combined web
and quality job has a 22-minute wrapper inside a 25-minute job. These are
failure ceilings, not expected durations.

## Quarantine

[`scripts/config/pytest-quarantine.json`](../../scripts/config/pytest-quarantine.json)
is an explicit to-do list. Every entry contains one exact pytest node ID, a
reason, an owning stream, and a tracking reference. It currently contains 33
entries: two operator-reported main failures, thirteen retired BIO
routing-contract nodes, one release-only Atlas database node, and seventeen
nodes that require a Stanza model unavailable without a live download. The
JSON ledger is the authoritative per-node explanation and owner list.

To remove an entry:

1. Fix the test or its dependency in its owning stream; do not change CI to
   make it pass.
2. Run the exact node and then the complete shard plan locally or in a PR.
3. Delete only that JSON entry. The planner fails if a ledger entry names a
   node that no longer exists, and the gate verifies every listed entry was
   accounted for.

The gate does not claim coverage for quarantined nodes, ignored corpus data, or
live ML model downloads. Those limits are visible in the ledger or in pytest's
own `-rs` skip output; they are never turned into a changed-file selection,
broad `-k` exclusion, or `xfail`.
