# Red-CI known-failures registry + lookup tool + raceless rerun primitive — design

- **Status**: STAGES 1–2 SHIPPED; Stage 3 (rerun primitive / atomic claimant ledger) is
  operator-gated and OUT OF STANDING SCOPE — tracked as P13.
- **Shipped surface** (verified from git history):
  - Schemas: `agents_extensions/shared/schemas/red-ci-known-failures.v1.schema.json`,
    `agents_extensions/shared/schemas/red-ci-signature-receipt.v1.schema.json`,
    `agents_extensions/shared/schemas/red-ci-lookup-receipt.v1.schema.json`
  - Validator / lookup module: `scripts/orchestration/red_ci_known_failures.py`
  - Trail integration: `scripts/config/trails/rb4-red-ci-triage.trail.yaml`
  - Tests: `tests/test_red_ci_known_failures.py`
  - Checked-in registry seed (this package): `scripts/config/trails/red-ci-known-failures.yaml`
- **PR refs**: stage 1 (#5926), stage 2 (#5946), TrailSpec v1.1 contract schema base (#5963).
- **Provenance**: designed by the advisor seat (gpt-5.6-sol @ xhigh, bridge task
  `registry-design-sol`, reply msg 5551, 2026-07-28), commissioned by the infra lane per the
  RB-4 (#5919) review resolution: the registry, its lookup tool, and the rerun primitive are
  designed TOGETHER. Part of #5885.
- **Consumers**: `scripts/config/trails/rb4-red-ci-triage.trail.yaml` (`allowlist_match` is an
  enforced fail-closed gate on the registry file + lookup tool), the `red-ci-triage` decision
  table, and `scripts/orchestration/validate_trailspec.py`.
- **Integration hazards the memo found in merged RB-4** (fix before activation, tracked by the
  infra lane): `extract_signature` bypasses `head_currency_check` (unreachable step — the
  validator checks dangling targets, not reachability); `locate_failing_run`'s
  `gh run list --limit 1` can select a newer pending run instead of the failing one.
- **Operator decisions closed on #5885** (encoded in the registry header and tests):
  30-day review horizon, run + receipt evidence minimums, additions via infra-lane PR +
  advisor sign-off, and single-host claimant scope. **Still open** (§D): TrailSpec v1.1
  approval and disposition of the GitHub head-change TOCTOU.

---

## Architecture memo: red-CI known failures (gpt-5.6-sol, 2026-07-28, verbatim)

### Executive decision

Ship registry and lookup first, fail-closed. Do not make automatic rerun reachable under TrailSpec v1.

The safe rerun design needs TrailSpec v1.1 invocation binding plus an atomic claimant ledger. Even then, a client-side head check cannot eliminate the final GitHub head-change race; that residual needs an explicit operator decision or workflow-concurrency hardening.

Two existing integration hazards should be fixed before activation:

- `extract_signature` currently transitions to `staleness_probe`, making `head_currency_check` unreachable. The validator checks dangling targets but not graph reachability.
- `gh run list --branch ... --limit 1` can select a newer pending run instead of the run referenced by the failing check. Resolve the run and job from the failing check URL/ID.

### A. Registry schema

Use a versioned schema such as:

```yaml
schema_version: red-ci-known-failures.v1
registry_version: "1.0.0"

entries:
  - id: pytest-cache-race
    matcher:
      check_name:
        exact: "CI / Test (pytest)"
      lines:
        required:
          - type: regex
            value: 'FAILED tests/test_cache\.py::test_parallel_cache .*'
        accepted:
          - type: regex
            value: 'FAILED tests/test_cache\.py::test_parallel_cache .*'
        require_full_coverage: true

    action:
      kind: retry-once  # retry-once | note-and-proceed | stop
      # stop_code required only for kind: stop

    owning_issue: 5885

    evidence:
      - run_id: 123456789
        run_attempt: 1
        pr_number: 1234
        head_sha: "40-lowercase-hex"
        observed_at: "2026-07-28T10:00:00Z"
        signature_sha256: "64-lowercase-hex"

    governance:
      added_by: "github-login"
      added_at: "2026-07-28T10:00:00Z"
      added_in_pr: 6000
      reviewed_by: ["independent-reviewer"]
      reviewed_at: "2026-07-28T11:00:00Z"
      review_by: "2026-08-27T11:00:00Z"
```

Rules:

- Require exact check-name matching plus full-line exact or anchored/full-match regex rules. Reject substring-only matching.
- `required` is all-of. `accepted` must cover every normalized signature line; otherwise an additional unknown failure could be hidden by one familiar line.
- Strip ANSI and normalize CRLF only. Do not lowercase or collapse whitespace implicitly.
- Require unique IDs, nonempty evidence, an owning issue, governance metadata, and action-specific schema constraints.
- Parse all timestamps into timezone-aware instants and epoch-compare them. Never lexicographically compare ISO strings.
- `review_by` is a hard eligibility deadline, not an advisory reminder. An expired matching entry yields `table-unknown`; it never authorizes an action. Scheduled/current-time validation should also fail while expired entries remain.
- Renewal requires a reviewed registry PR updating evidence and governance. Runtime tools never edit the registry.
- Define `note-and-proceed` narrowly: annotate and leave RB-4 triage, while the PR remains blocked by any blocking red check. It must never mean bypassing branch protection, claiming green, or arming merge.

The present bare text receipt is insufficient because it carries neither check identity nor trustworthy run binding. Introduce `red-ci-signature-receipt.v1` containing repository ID/name, PR, run ID/attempt/head SHA, job/check ID and name, normalized signature lines, extraction version, timestamp, and digest.

For runs with multiple failures, lookup is per atomic failed job/signature. Aggregate fail-closed:

1. Any malformed, unknown, ambiguous, expired-match, or `stop` result stops.
2. Otherwise any `retry-once` permits one run-level retry.
3. Only an all-`note-and-proceed` set takes that disposition.

### B. Lookup contract

Recommended interface:

```text
red_ci_known_failures.py lookup \
  --registry PATH \
  --receipt PATH \
  --repository-id ID \
  --pr NUMBER \
  --run-id ID \
  --as-of ISO_TIMESTAMP \
  --output LOOKUP_RECEIPT
```

`--as-of` is required so results are deterministic and expiry tests are reproducible.

Successful JSON:

```json
{
  "schema_version": "red-ci-lookup-receipt.v1",
  "status": "matched",
  "entry_id": "pytest-cache-race",
  "action": {"kind": "retry-once"},
  "registry_sha256": "...",
  "signature_receipt_sha256": "...",
  "as_of_epoch": 1785240000
}
```

No match:

```json
{
  "schema_version": "red-ci-lookup-receipt.v1",
  "status": "table-unknown",
  "reason": "no-match"
}
```

Contract:

- Exit `0`: valid `matched` or `table-unknown`.
- Nonzero with no actionable stdout: malformed registry, malformed receipt, identity mismatch, unsafe regex, unsupported schema, or I/O failure.
- Receipt identity must equal CLI identity. The lookup itself remains pure and network-free.
- Evaluate every entry. Zero eligible matches means `table-unknown`; exactly one means matched; more than one means `table-unknown` with reason `ambiguous`. Never use file order, "first match," or invented regex specificity.
- If an expired entry would match, return `table-unknown` even if an active overlapping entry also matches.

Put JSON Schema in `agents_extensions/shared/schemas/`. Put parsing, domain validation, timestamp normalization, and matching in one reusable module consumed by both the lookup CLI and `validate_trailspec.py`; do not duplicate validation. Extend `validate_trailspec.py` as the CI-facing entry point, including expiry and trail reachability checks.

### C. Rerun primitive and v1/v1.1 verdict

Verdict: TrailSpec v1.1 is required. Registry and lookup may ship under v1, but the retry transition remains mechanically unreachable until v1.1 is operator-approved and implemented.

Minimum v1.1 addition:

- Generate a stable `invocation_id` before executing the command.
- Pass it to the command.
- Bind the evidence predicate to that invocation's immutable command receipt/digest.
- Never re-execute a side-effecting command as its predicate.
- Add `invocation_id`, command-receipt digest, and actor outcome to StepReceipt.
- Map exact primitive signals to transitions.

The primitive should:

1. Recompute lookup from the registry and signature receipt; require `retry-once`.
2. Fetch live run and PR identity. Validate both SHAs independently as lowercase 40-hex, then require equality.
3. Require the original run to be completed, failed, and `run_attempt == 1`.
4. Atomically claim unique `(repository_id, workflow_run_id)` in a shared ignored SQLite ledger using `BEGIN IMMEDIATE` and a unique constraint. Commit the claim before the network side effect.
5. Re-fetch and revalidate both SHAs and run state immediately before POST.
6. Call the workflow-rerun REST endpoint and accept only its direct HTTP `201` response as evidence. Never infer success from later queued-run status. GitHub documents `201 Created` for this endpoint and confirms reruns retain the original SHA/ref.
7. Write an immutable per-invocation receipt using exclusive creation.

Ledger states should be `claimed`, `accepted`, `refused`, and `indeterminate`. A losing claimant reports `already-accepted` or `claim-in-progress`; it never reports that its own rerun fired. A crash after claim is never automatically taken over because the POST may already have succeeded.

One unresolved hard limit: GitHub's documented rerun endpoint accepts a run ID but no expected-current-head conditional. Therefore a PR head can change between the last equality check and POST. A client-only primitive cannot prove absolute atomic head currency. Operator input is required to choose between:

- keeping automatic rerun disabled;
- accepting the documented final-preflight residual risk; or
- approving workflow-concurrency hardening keyed by immutable head SHA so a stale rerun cannot cancel current-head CI.

The SQLite mechanism also assumes all claimants share the canonical local runtime state. Multi-host execution requires a server-side/shared CAS coordinator; local SQLite is insufficient.

### D. Packaging

Use one approved design and final integration review, with staged implementation PRs:

1. Registry and signature-receipt schemas, reusable validator, expiry policy, reachability validation.
2. Structured extraction, deterministic lookup, ambiguity/multi-failure aggregation, non-rerun trail routes.
3. Operator-approved TrailSpec v1.1, atomic ledger/primitive, adversarial concurrency and crash tests, then the retry transition.

Each PR gets independent cross-family review. PR 3 also receives a combined interface/conformance review against this memo. "Reviewed together" should mean shared architecture and final integration acceptance—not one oversized PR.

Rejected choices: substring matching, first-match or "most-specific" resolution, soft expiry dates, shared result files, queued-status inference, automatic takeover of uncertain claims, and any meaning of `note-and-proceed` that bypasses red CI.

Operator decisions closed on #5885: 30-day maximum review horizon; run + receipt evidence minimums; additions via infra-lane PR with advisor sign-off; and single-host claimant scope. Decisions still required: TrailSpec v1.1 approval and disposition of the unavoidable GitHub head-change TOCTOU.
