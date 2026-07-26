# Required CI gate

The `CI Gate` status is the repository's required integration check. It is
unconditional on pull requests, merge groups, and pushes to `main`.

## What a green gate guarantees

- Pytest collects the complete repository suite with the default marker filter
  disabled. It never asks which files changed.
- Five deterministic node-level shards run the resulting suite. The
  thread-sensitive, source-inventory, and bounded-network nodes remain within
  their own external shard, while all other nodes are balanced by node count.
- Each matrix runner writes its full collected-node set plus planned and
  executed node IDs. `CI Gate` rejects a missing artifact, collection
  divergence, duplicate node, empty plan, incomplete execution report, failed
  job, cancelled job, or skipped job. It also proves that the union of shard
  plans and the exact quarantine ledger accounts for the whole collection.
- Pytest has full Git history and CPU Torch. The evidence plugin applies
  `SOURCES_MCP_NO_MLX=1` to wiki nodes only, preserving the separate MLX
  override contract test. Tests requiring ignored databases or ignored external
  JSONL retain their explicit pytest skip reason instead of failing
  mysteriously.
- Each substantive test, build, and integrity job restores a cache keyed by
  the committed Atlas manifest pointer, then verifies or hydrates that
  release-pinned manifest before it can be consumed. Only pytest shard 1 writes
  the shared manifest cache, so parallel shards cannot race to create it.
- One combined web-and-quality job provisions the Python runtime used by site
  hydration, then runs Ruff, Actionlint, frontend unit tests, a production
  build, Chromium browser tests, and the hydrated Atlas enrichment gate.
- One integrity-and-security job runs TruffleHog on every workflow invocation,
  verifies lesson-schema drift, MDX generation drift and parity, static practice
  assets, learner-surface IDs, locked-module publication, Atlas freshness,
  dossier word-count, and BIO capsule/active-hold validation, including a hard
  rejection of deleted BIO preparation files. These commands may calculate
  their own relevant source scope, but the job itself is never routed or
  skipped.
- Pushes to `main` also collect coverage from every complete pytest shard and
  fail if the combined `scripts` coverage falls below 35%. Coverage does not
  change which tests run.
- Alongside the five pytest shards, the combined web-and-quality job and the
  integrity job cap normal concurrent runner demand at seven slots.

The workflow reports a measured duration in every job summary. The pytest
evidence verifier also reports the measured duration of each shard.

## Time bounds

Pytest uses a 15-minute per-test timeout and a 30-minute wrapper that writes a
named timeout record with the last dispatched node ID before the 35-minute
GitHub job limit. Its sole xdist worker is not restarted after a crash, so a
worker failure cannot silently consume the remaining wrapper time. The combined
web and quality job has a 22-minute wrapper inside a 25-minute job. Integrity
contracts have a 15-minute wrapper inside a 20-minute job. These are failure
ceilings, not expected durations.

## Quarantine

[`scripts/config/pytest-quarantine.json`](../../scripts/config/pytest-quarantine.json)
is an explicit to-do list. Every entry contains one exact pytest node ID, a
reason, an owning stream, and a tracking reference. It currently contains 20
entries: two operator-reported main failures, one release-only Atlas database
node, and seventeen nodes that require a Stanza model unavailable without a
live download. The JSON ledger is the authoritative per-node explanation and
owner list.

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
