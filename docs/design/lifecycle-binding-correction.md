# Append-only correction of a lifecycle PR binding

## Decision and boundary

For [#11071](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/11071), select option A: a typed append-only binding-correction receipt. Ordinary `bind-pr` stays one-shot. The original binding and evidence remain historical records, and fresh evidence must establish the corrected context.

This note implements the [frozen decision](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/11071#issuecomment-6288122435), which records designated agreement on 2026-10-20. It defines a new mechanism, not a small bug fix. It changes no executable code, schema, ledger, proof requirement, or remote PR. Separately reviewed implementation is required before any live correction. The receipt described below does not exist in the current interface.

The denominator is one wrong binding, the three FD-01 through FD-03 behavior-proof records, one refused bind attempt, and existing evidence supersession. Atlas issue [#11035](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/11035) owns the behavior evidence. Infra owns the recovery implementation and its review. PR #11054 and its lifecycle remain untouched.

## Observed behavior on current main

The inspected base is `9738e18a8c11d32ceac13c6586f8ecdc87cc518c`. On 2026-10-20, `git fetch origin main` followed by `git rev-parse HEAD origin/main` returned that SHA twice. Commands ran in the assigned dispatch worktree, using the prescribed shared interpreter. In the commands below, `PROJECT_PYTHON` is that interpreter, and `TMPDIR` is the dispatch-managed scratch lease. No live ledger was written.

The authentic source is `.agent/task-lifecycle/ab3a61ed042f6f43/issue-11035.json` beneath the shared canonical state root. Its raw byte SHA-256 is `0c79fa078fa921269c75b1e3c4c6f02ed24308ef81542db9326631b0c8515825`; its `task_lifecycle.digest` is `sha256:5501fc15c2738768c8d3db4de69dc18045a6be0c0cdac0b91fdbc4dab49fca87`. These identify the inspected snapshot, not a future correction authorization.

`validate_lifecycle` accepts this snapshot. It binds repository `learn-ukrainian/learn-ukrainian.github.io`, issue 11035, and stream 4387 to PR 11054. Its three evidence records are all `behavior_proof`, with subject PR 11054 and commit `3d1a8991aaa787dff65f76f524156e40e821ec1a`. There are zero observation receipts and zero mutation receipts. Structural acceptance does not establish valid behavior proof.

The complete record IDs are:

| Criterion | Historical evidence ID |
| --- | --- |
| FD-01 | `sha256:29140a3ff34a9877e8f1c7dc0f2cbf897f8192648b197e5421d4b4788c600921` |
| FD-02 | `sha256:783df29e8635dec81b69e6c7be2d93bd96deb8fd24ebb507e3951a1fc048d326` |
| FD-03 | `sha256:3bc6c4b2d1e2bc063286c1b793da3440be10b664edc9ab26956f493acd63b23e` |

The following reproduction copies the actual bytes before invoking the real CLI. The final assertions also detect an unexpected write on refusal.

```bash
"$PROJECT_PYTHON" - <<'PY'
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import tempfile
from scripts.orchestration import task_lifecycle as tl

root = tl.canonical_state_root(Path.cwd())
source = root / '.agent/task-lifecycle/ab3a61ed042f6f43/issue-11035.json'
before = source.read_bytes()
ledger = tl.validate_lifecycle(json.loads(before))
print('source_bytes_sha256=' + sha256(before).hexdigest())
print('source_canonical_digest=' + tl.digest(ledger))
print('binding=' + str(ledger['pr']['number']))
print('evidence_count=' + str(len(ledger['evidence'])))
with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as temp:
    copied = Path(temp) / 'copied-ledger.json'
    copied.write_bytes(before)
    result = subprocess.run(
        [str(root / '.venv/bin/python'), '-m', 'scripts.orchestration.task_closeout',
         'bind-pr', '--state-file', str(copied), '--pr', '11055'],
        capture_output=True, text=True, check=False,
    )
    print('copied_bind_exit=' + str(result.returncode))
    print(result.stderr.strip())
    assert result.returncode == 2
    assert 'lifecycle is already bound to a different PR' in result.stderr
    assert copied.read_bytes() == before
    print('copied_ledger_unchanged=True')
assert source.read_bytes() == before
print('source_unchanged=True')
PY
```

Observed refusal and preservation output:

```text
binding=11054
evidence_count=3
copied_bind_exit=2
{
  "error": "lifecycle is already bound to a different PR"
}
copied_ledger_unchanged=True
source_unchanged=True
```

`gh pr view 11055 --json number,url,state,headRefOid,headRefName,mergeCommit,createdAt,mergedAt,closingIssuesReferences` reports `MERGED`, head `3d1a8991aaa787dff65f76f524156e40e821ec1a`, and merge commit `4cf7018ea91c7d2565c720ed109e9bb21d297ceb`. Creation and merge times are `2026-10-19T15:58:46Z` and `2026-10-19T16:43:23Z`. `closingIssuesReferences` is empty. This independently corroborates the actual PR/head; it does not prove which PR creation output the original driver received.

The inspected preserved-file inventories of tasks `atlas-11035-raw-import-opus` and `atlas-11035-raw-fix-opus` contain no PR creation output. Its existence elsewhere is unknown. Atlas must supply verifiable creation evidence before live correction; prose in an issue is insufficient.

## Existing mechanisms and limits

The current implementation establishes these boundaries:

- [`lifecycle_id`](../../scripts/orchestration/task_lifecycle.py#L151) hashes repository, issue, and stream. Another file with that identity does not create an independent lifecycle or resolve the canonical wrong binding.
- [`bind_pr`](../../scripts/orchestration/task_lifecycle.py#L859) accepts an unbound ledger or an identical replay and rejects another PR. [`cmd_bind_pr`](../../scripts/orchestration/task_closeout.py#L1009) locks, loads, calls that function, and writes only on success.
- [`validate_lifecycle`](../../scripts/orchestration/task_lifecycle.py#L746) requires every evidence subject's PR to equal the single stored binding. Its supersession check at line 806 requires the same criterion, type, repository, issue, and PR, an earlier target, one successor, and later chronology.
- [`add_evidence`](../../scripts/orchestration/task_lifecycle.py#L876) derives the subject from the stored binding. On copies, same-PR supersession of each FD record passes structural validation. Changing each replacement's PR to 11055 and recomputing its ID fails with `evidence PR does not match lifecycle binding`.
- [`_evidence_status`](../../scripts/orchestration/task_lifecycle.py#L1328) accepts independently valid chain tips. Supersession never supplies missing proof. [`_behavior_proof_reference_error`](../../scripts/orchestration/task_lifecycle.py#L1251) reads and verifies the canonical receipt, digest, input fingerprint, exact head, review families, and behavior surfaces.
- [`evaluate`](../../scripts/orchestration/task_lifecycle.py#L1473) and the closeout adapter currently read the single stored binding. The [schema](../../agents_extensions/shared/schemas/task-lifecycle.v1.schema.json) forbids additional top-level properties. A new correction cannot be smuggled into `details` or ignored by older readers.

The [existing evidence-correction contract](../../agents_extensions/shared/contracts/task-lifecycle-closeout.md#append-only-evidence-correction) permits pointer or head corrections within a PR. It supplies no cross-PR binding correction. The current same-PR supersession gates remain intact.

## Options and risks

| Option | What it changes or weakens | Forgery risk and approval boundary |
| --- | --- | --- |
| A. Typed append-only binding correction, selected | Adds an explicit effective binding while preserving the original binding and every old record. No evidence transfers between PRs. Adds narrowly checked authority to correct a mistake. | An unverified receipt could select an unrelated PR or make wrong-context proof count. Require predecessor, creation, identity, and head verification below. Designated decision exists; implementation still requires its own issue and exact-head review. |
| B. Abandon and create a fresh ledger | An unsupported duplicate evades canonical deterministic identity, hides history from readers, and risks choosing whichever ledger appears complete. | A caller could omit errors or criteria. No supported abandonment or successor mechanism exists. It would need a separate designated design and reviewed implementation; it is not an authorized workaround. |
| C. Document disposition only | Preserves every current refusal and leaves typed closeout blocked. Cannot deliver a corrected effective binding. | A prose exception could falsely claim closure. Keeping the issue open with preserved evidence is safe interim reporting. Treating prose as an evidence waiver requires separate approval and is not selected. |

## Correction receipt contract

The proposed `lifecycle-binding-correction.v1` receipt is an additional immutable event in the canonical lifecycle. Its schema must be explicit and rejected by readers that do not support it. This note does not prescribe a current CLI command or permit hand-authored live receipts.

For this recovery, the supported target is PR #11055 in the unchanged repository, at candidate head `3d1a8991aaa787dff65f76f524156e40e821ec1a`. Its authoritative merged result must match `4cf7018ea91c7d2565c720ed109e9bb21d297ceb`. Another PR, another candidate head, a missing PR, or a closed-unmerged target is unsupported. A merged result does not replace the candidate head in behavior-proof references.

The receipt must bind all of these facts:

| Required facts | Validation purpose |
| --- | --- |
| Receipt schema, content-derived ID, recording time, actor, reason, approval and implementation-review references | Preserve provenance. Actor text and approval URLs alone grant no authority; verify them through the authorized workflow. |
| Exact lifecycle ID, repository, issue, stream, and unchanged AC snapshot hash | Prevent moving a correction to another lifecycle or altering acceptance criteria. |
| Immutable predecessor snapshot locator, raw-byte SHA-256, canonical ledger digest, and original binding | Authenticate the complete pre-correction ledger under the lifecycle lock. Preserve its bytes and validate its original schema. |
| Actual repository and PR number/URL, exact candidate head, creation-evidence locator/digest, authoritative PR verification | Corroborate the intended task, creation result, branch/head, and target PR. A URL, matching commit, or issue keyword alone is insufficient. |
| Historical evidence IDs, including all three FD records above, and predecessor event boundaries | Make the invalid context explicit. Every listed ID must exist in that predecessor; preserve records and their digests unchanged. |

Validate the snapshot against the locked live predecessor before appending. Persist the verified snapshot through the existing durable artifact mechanism before atomically publishing the correction. A crash must leave either the unchanged ledger or one complete, verifiable correction. A snapshot alone changes nothing. Load-time verification checks its digest and the unchanged historical prefixes against the live ledger. A missing or changed snapshot fails closed.

Identical receipt replay returns the existing event without mutation. A different request against an already corrected binding is a conflicting correction and is refused. This bounded design authorizes no correction chain, reverse correction, rollback, or general rebinding. A later PR head change follows ordinary current-head proof rules; it never updates the historical receipt or transfers its proof.

### Historical validation and effective evaluation

Keep the persisted original `pr` binding as historical context. Derive the effective binding only from a validated correction event; do not overwrite the original `pr`. Existing ledgers without correction retain their current semantics.

The validator checks the predecessor and its evidence under the original binding. Thus the old FD records remain structurally attributable to PR 11054, with their exact original IDs, subjects, and times. It reports them as historical invalid-context records relative to the effective PR 11055. It must not rewrite their PRs, resign them, create cross-PR supersession edges, or label them valid proof for the new PR.

New evidence derives its subject from the corrected effective binding. The evidence validator, evaluator, observation producer, reconciliation and mutation adapters, receipt projections, and recovery readers must use the same effective-binding resolution. Any consumer still using the original binding for current actions blocks implementation release. Historical observations and mutation receipts remain immutable and cannot establish corrected-context readiness, prior review timing, merge, closure, or cleanup.

The evaluator exposes original binding, effective binding, correction ID, and historical invalid-context IDs separately. It excludes original-context evidence from current proof sets and review timing. Historical context mismatch alone is reported without perpetually blocking the corrected context, but malformed history or an invalid correction still blocks. It evaluates all corrected-context proof independently, including invalid supersession tips. It must not suppress unrelated evidence, identity, or readiness errors.

Fresh FD-01, FD-02, and FD-03 evidence references must pass the canonical behavior-proof checks for the corrected PR/head. Reusing old evidence IDs or merely changing a digest or subject is forbidden. An underlying receipt can be referenced only if independently verified for the corrected context; the correction itself supplies no behavior proof. FD-04 and all remaining acceptance, review, CI, local observation, issue-closeout, and cleanup gates retain their requirements.

### Mandatory refusals

| Input or state | Required result before any write |
| --- | --- |
| Wrong predecessor digest, changed historical prefix, unavailable snapshot, or stale locked state | Refuse; preserve ledger bytes. Re-observe rather than accept a caller's digest. |
| Unrelated issue, repository, stream, lifecycle ID, or altered AC snapshot | Refuse; matching PR numbers or commit hashes do not repair identity. |
| Missing or unverifiable creation evidence, unrelated PR, inconsistent branch/head, unsupported target state, or unavailable authoritative lookup | Refuse; unknown is not corroboration. Support the actual merged PR through authoritative retained head and merge facts, without requiring squash-head ancestry into main. |
| Unsupported target head, abbreviated SHA, or discrepancy between creation evidence and authoritative candidate | Refuse; never select an arbitrary historical commit to make proof pass. |
| Different second correction, competing append, reversed binding, or unknown receipt/schema version | Refuse; identical validated replay is the only no-op. |
| Rewritten historical record, cross-PR supersession, or old-context evidence offered as current proof | Refuse the invalid record or current proof claim; do not weaken ordinary validation. |

## Verification required of implementation

This design-only change adds no executable rule to mutation-test. Existing lifecycle and CLI tests exercise the preserved refusals. The implementation issue must add behavior tests at the public append/load/evaluate boundaries, with literal expected outcomes. Each guard above needs a negative case that fails if the guard is removed. In particular:

1. A copied authentic ledger accepts one corroborated correction, preserves the original binding and all three records, and reports zero valid corrected-context behavior proofs before new references are added.
2. Each digest, identity, target, and conflict refusal leaves ledger bytes unchanged. Missing creation evidence must refuse even when PR/head match.
3. Fresh valid corrected-context references satisfy only their own criteria. Missing, wrong-head, forged, or invalid replacement references remain blocking. Historical observations and review timing cannot satisfy current gates.
4. Replay, crash-before-publication, and concurrent append controls preserve one effective binding. Legacy ledgers keep their refusals, and unsupported readers reject the new format.
5. An independently selected held-out wrong-context proof must not count. Independent exact-head cross-family implementation review precedes PR creation, followed by same-head CI and merged-artifact proof.

The [#11058 census](lifecycle-closeout-unrecorded-push.md#thirty-day-census) remains the existing fixed-window inventory for the related reaping problem. It is not a count of wrong bindings or proof failures. This note does not rerun it or infer another affected population. The same document's distinction between publication and worktree custody applies here: a merged PR cannot manufacture missing historical observations or behavior proof.

## Atlas disposition and residual owners

Atlas keeps #11035 open with typed closeout blocked, preserves the erroneous snapshot and command evidence, and links this design. It must not rebind by editing JSON, reset or duplicate the ledger, supersede across PRs, mutate PR #11054, or claim behavior proof from the correction. The current supported action is preservation and explicit blocked disposition, not live recovery.

`claude-infra` owns the separate implementation issue, exact-head review, CI, landing, and verification of the supported correction before Atlas uses it. The driver must create and link that issue and publish the supported disposition on #11035 before closing #11071. Atlas owns locating verifiable creation evidence and submitting fresh corrected-context behavior references. If creation evidence cannot be verified, correction remains refused; any alternative disposition requires a new approved decision.

This author delivery does not claim independent review, implementation, issue updates, push, PR creation, merge, cleanup, or Atlas certification. Those remain driver-owned delivery gates. After two unchanged review rounds, unresolved material findings block; new material failures are not waived by the stopping rule.
