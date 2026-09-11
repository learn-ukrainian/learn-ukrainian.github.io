### `INDEPENDENT_REVIEW_REQUIRED`

Send the final diff to one reviewer outside every recorded machine author
family. Internal same-family subagents do not satisfy this gate. Record the
reviewer family, exact evidence artifact, and `PASS`. Resolve requested changes,
record `CHANGES_REQUESTED` with its deterministic `--owner-kind`, resolve the
repair, and rerun post-build review before trying again.

If only the versioned audit workflow changes while this gate is pending, record
that exact `audit_tooling` change. The helper requires unchanged learner hashes
and returns the module to `POST_BUILD_REVIEW_REQUIRED`; stale review evidence
must never remain authoritative merely because it had already reached this gate.

Record both the process receipt and the strict `independent-review`
certification artifact. Only the strict current artifact advances to
`PUBLISH_REQUIRED`.

A qualifying canonical post-build semantic review may satisfy this learner
content gate once when its reviewer group is outside every recorded learner
author group and its result, protocol identity, and learner hashes remain
current. The ledger records that reuse explicitly and fails closed on any
binding drift. This reuse is only learner-content evidence: a code change still
requires the repository's separate cross-family code-review gate before its PR
can merge.
