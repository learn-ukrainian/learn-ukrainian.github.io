---
version: 1
status: approved-design
title: Agent-friendly architecture and delivery plan
epic: 9737
issue: 9738
source_sha256: d7e14787b55e13cd9c93056f06925cee1e7a618aad2eb4ddd2f34f36c8d2a2e4
published_body_sha256: c641331446da78909d161e725d8304c350e1c4d0bfc4822291cdef0f1192a36e
published_body_scope: every byte after the closing frontmatter delimiter line
review:
  reviewer_model: claude-opus-5-5
  reviewer_family: anthropic
  reviewer_harness: native Claude Code, read-only dispatch
  verdict: APPROVE
  verdict_scope: design only; not implementation review, CI, merge or deployment approval
  reviewed_sha256: d7e14787b55e13cd9c93056f06925cee1e7a618aad2eb4ddd2f34f36c8d2a2e4
  reviewed_at_utc: "2026-10-05T08:09Z"
  receipt_locator: task devops-pstack-opus-plan-final
  prior_rounds: CHANGES_REQUESTED in tasks devops-pstack-opus-plan and devops-pstack-opus-plan-r2
  synthesis: gpt-6.1-sol, as recorded by epic 9737
implementation_status: not-started
---
# Agent-friendly architecture and delivery plan

Status: draft for operator review, not implemented. Accountable lead: existing DevOps driver. Existing stream owners retain their tasks and leases. Basis: a bounded Git-history audit, existing Fleet/Work API snapshots and safe pure-function replays. New architecture execution awaits the requested operator checkpoint.

## Outcome and diagnosis

Make verified changes flow across every epic with fewer repeated instructions, recoverable failures and an explicit owner for waiting work. Cover intake, onboarding, routing, authoring, verification/review, CI/landing and recovery/closeout. A delivered outcome includes task-specific acceptance proof and required review/CI/merge/cleanup; an agent response or a green dashboard is not the denominator.

Working diagnosis: several boundaries require callers to reconstruct facts that another module already owns. A locally reasonable choice can therefore be globally wrong. Repeating agent instructions cannot enforce agreement between those consumers. There is evidence for this failure surface, but no measured attribution of all queue growth or latency to it. Provider limits are one input to recovery; changing the model does not repair broken ownership or evidence flow.

## Evidence and uncertainty

The history scout sampled 200 recent non-merge commits at c21043daa586e69df3637c81782d8800e0a59b1c, spanning 2026-09-30 through 2026-10-05. Eight diffs were inspected; some were large and no CI-specific implementation diff was inspected. This is a bounded discovery sample, not a fleet-wide defect rate.

Two repeated broad classes have independent diff evidence:

| Class | Historical evidence | Adequate prevention and current status |
| --- | --- | --- |
| Consumers interpret shared routing/credit facts differently | 84c9f897da9bc272c6ac9e1a2ab6bc2f553d097b updates capacity consumers to derived pace-deficit state; 8e4496f135ead2a1d23f608177917dea1e3d6ff2 re-checks published credit relief and allowlists across review/wave consumers | Keep existing credit_lane as knowledge owner; use its shared decision and test agreement among consumers. These corrections are merged; their history does not prove an ongoing defect. |
| Curriculum requirements remain expectations until production validates them | d975ded6c80d38f50fa7e617876c0f4ef2ab0507 adds learner-text and arc checks in assembly; df12cabbbc043952e1fb55b30607005ab3cd201c checks planned lesson-page completeness before shipping | Keep assembler/shipping validators authoritative. Replay real invalid outputs and valid domain cases; do not replace semantic/source proof with generic completion. These checks already exist. |

Single sampled events, not established recurrence: canonical launcher stream forwarding (6302130bc1ed0e4665ca4881b9165aea158a6adf), dispatch bus/environment validation (610f1d50bdcc85d60b237867e6291c4c290a3bdc), structured review receipt acceptance (882e654f64d27ae641043f25fa1db4b4de4c5d63). Existing open reports #9673/#9668/#9645 identify additional routing-diagnostic, cancellation and ignored-output seams; code inspection supports specific seams but has not reproduced their full runtime scenarios.

Executed helper proof: 12 positive/negative controls on AST-isolated existing pure helpers. Disposable-cache classification rejects the transcription output path as disposable; routing helpers preserve hot/near-cap/unknown states and false/true/unknown reset sufficiency. The cache helper is NOT on the dispatcher path implicated in #9645; its output is not evidence that this loss path is safe. The exact command/output is in pstack-replay-evidence.json.

Independent Opus review verified all eight historical descriptions and ran an actual disposable Git-repository counterexample: with an ignored output present, ordinary porcelain was empty and non-forced worktree removal succeeded, deleting the output. This confirms Git behavior underlying callers that assume non-force removal protects ignored data; those production callers were not run end to end. Opus also found caller-attached preservation rather than boundary-enforced preservation, and three disagreeing disposable-directory interpretations. Its report is the result of task `devops-pstack-opus-plan`, SHA25613f69e0259ecacc9027acd757127d90b697de248d9814128a28cfccb5e7ea4a5. The first and second Opus reviews remain retained as CHANGES_REQUESTED records. The second corrected a mistaken valid-case assertion in the first. Current scoped re-review state is recorded in companion receipts; no implementation approval is implied.

Work API refreshed at 2026-10-05T07:41:53Z reports 211 open issues and 6 open PRs, public task history truncated to 500 and private source unavailable. Earlier snapshots had a PR fetch timeout. Source-specific omissions and freshness must remain visible; no delivery-health or latency conclusion follows from aggregate status.

## Architecture choice

| Design | Benefit | Cost and decision |
| --- | --- | --- |
| Central advance-task facade controlling all seven stages | Fewer commands at the driver surface | Risks a new orchestration engine, universal context object and duplicate lifecycle authority. Reject on current evidence. |
| Strong owner-specific interfaces with a thin composed read view | Each knowledge owner enforces its invariants; agents need less hidden implementation knowledge | Requires agreement tests at existing boundaries. Recommended; retain Fleet jobs, current task identity/lifecycle and stream ownership. |

This recommendation groups code by knowledge ownership, not just execution order. A read view may explain the next supported action; it cannot independently grant admission, approve a review, mutate a lease or claim completion. Keep task-specific proof contracts. No new database, message bus, Project driver, universal DTO or competing state machine is justified.

Caller-first interface sketches below are proposed contracts, not shipped APIs:

- Launcher resolves a selector once using the existing stream resolver. The same canonical stream reaches lease checks, canary and driver entry. Adapters receive the resolved identity; they do not reconstruct it.
- Routing consumers call the existing shared credit/pace decision owner with the same snapshot and concrete route. Typed ready/refused/unknown observations retain reasons and freshness. Explicit route selection suppresses substitution, not diagnostics; observation and admission remain separate. Model/harness eligibility and independent authorship remain catalogued facts.
- A dispatch reservation is operated on through its existing owner under its existing lock. Cancellation distinguishes an empty owned reservation from a task with commits, output or uncertain activity. Retry uses supported archival/continuation paths and records an explicit new attempt; it does not clobber the task or silently invoke a second provider.
- Removal ownership: scripts/orchestration/worktree_claims.py owns remove_unclaimed_worktree under the existing worktree lock. Inventory and copy-or-refuse become mandatory inside that boundary, including non-force removal; attaching preservation independently in callers is insufficient. The scheduled reaper has a permitted guarded path to the sole raw git_worktree_remove function, so that path must satisfy the same preservation decision/receipt contract. The existing test_worktree_removal_invariant.py must reject any permitted raw-removal caller lacking that contract; do not create another removal path.
- Inventory ownership: worktree_artifacts.py owns one disposable taxonomy, used by reap_worktrees.py and removal guards. Capture an ignored-path/content inventory when a worktree is created under the same lock, referenced by its existing task identity. An old or reused tree without a trustworthy inventory retains unknown data; file timestamps compared to started_at are not an ownership algorithm. Inventory, preserve or explicitly retain precedes removal. Forced dirty checks include ignored non-disposable data; non-force callers cannot rely on Git to protect it. Missing task attribution, oversized output or failed retrieval proof retains the tree with an owner. Both remove_unclaimed_worktree and the scheduled guarded raw-removal path MUST read and honor the task keep_worktree intent before removal. It is a proposed enforcement repair, not current guaranteed behavior. A scheduler cannot override that intent; release requires the existing owner to explicitly resolve it after output is safely retrievable. No bulk corpus deletion is authorized.
- Review feasibility ownership: existing dispatch admission in scripts/delegate.py calls the existing reviewer_resolver before another model family can add commits to an existing branch. It passes all existing branch author families, plus the proposed incoming writer family, using the same authorship calculation as record_cf_verdict. Selection and eventual verdict recording consume the same full target and protected scope. If no qualified independent family remains, refuse that additional authoring route before work is created, preserve the branch and expose the reason. This repairs producer/consumer agreement; it does not change eligibility, erase authorship or authorize self-review. A current eligible exact-head verdict remains reusable on an unchanged head.
- Assembly/shipping validators own executable completeness and language-channel constraints. Independent domain reviewers own semantic and Ukrainian source judgments. The task ledger references these receipts instead of inventing another definition of success.
- Projection ownership: scripts/work/attention.py derives existing safe_next_action; scripts/api/work_router.py exposes it through the existing /v1/next work-next.v1 response. Extend those fields and existing projection composition only where evidence is available; do not build a second view or action authority. CI owns tested-tree evidence; the accountable driver owns landing. Missing stage timing, ownership or proof remains unknown.

## All seven delivery stages

1. Intake: each actionable item has a registered stream owner, outcome, terminal goal and unblock condition. Cap new work by real downstream capacity and stop leaving finished deliverables waiting for integration. Reconcile projection against canonical task/Git/GitHub state.
2. Onboarding: launchers inject one short common skill binding after their existing lease/canary. Task-specific references provide details. Reuse fresh cold-start observations rather than repeat the same probe immediately. Interactive launchers retain their different ownership contract.
3. Capacity: one interpretation of health/quota/credit and explicit substitution decisions with provenance. Preserve work across unavailable routes. Protect an achievable independent review path before dispatch.
4. Authoring: bounded whole outcomes and disjoint owned paths. Stable task identity, artifact references and terminal disposition persist through crashes, cancellation and handoff. Avoid source refactors justified only by file size.
5. Verification/review: deterministic checks first; qualified independent critique examines failure modes and missing evidence. Use differentiated proof for a repair, architecture/security change and Ukrainian lesson. The already-authorized quick-fix outcome is not globally rolled out while its authority-changing implementation remains unmerged.
6. CI/landing: establish usable timing evidence before attributing waiting to a check or queue. Reuse existing exact-tree green evidence where supported. Affected feedback requires demonstrated dependency coverage; keep integration/security checks. Driver lands eligible current-head work without waiting for operator action.
7. Recovery/closeout: use existing finalizer/archive/reaper interfaces consistently. A terminal record keeps recoverable work and explicit residual owner; cleanup cannot erase a deliverable. Unknown cleanup disposition retains state rather than forcing deletion.

## Correcting the environment

For each confirmed repeat, choose architecture first, then types, then an actionable lint/check, then a behavior test. Documentation is for remaining judgment. Prefer removing duplicate interpretations to adding wrappers. Existing good checks are reused and qualified, not recreated.

Each prevention entry pairs: two independent historical examples; knowledge owner; supported caller; highest adequate enforcement; a real past-fault rejection; a held-out valid case; and a fail-closed uncertain case. A retrospective-only rule is insufficient. If architecture alone cannot prevent a mistake, state why the next enforcement level is necessary. Exceptions require narrowly approved justification; do not introduce a general escape switch.

Illustrative acceptance matrix:

| Boundary | Rejected historical/negative case | Held-out valid/uncertain control |
| --- | --- | --- |
| Routing agreement | Covered credit treated as uncovered, stale relief trusted, disallowed model admitted | Fresh covered/allowed route agrees across consumers; unknown snapshot stays explicit |
| Curriculum output | Unclassified learner text, invalid arc, missing planned lesson, landing-only module | Valid A1/A2 and scoped through-lesson outputs; semantic/source review still distinct |
| Launcher identity | Alias passed into a consumer requiring canonical stream | A second valid selector and an unknown selector; no second lease claim |
| Output retention | Generated ignored transcription omitted from inventory; historical e3c re-run removed despite keep_worktree intent | Both paths retain keep_worktree; copy/retrieval succeeds on controlled valid fixture; unknown/off-repo state stays unknown |
| Review feasibility | Selection admits a reviewer verdict recording will reject | Eligible independent exact-head route; mixed authors/no qualified family refuses before wasted review |

The last three are candidate seam repairs with single-event/report evidence, not statistically established repeat classes. Opus independently traced missing preservation in task_family/git_safety.py, fleet/sibling_git.py and ai_agent_bridge/_acp_execution.py, and disagreement between reaper cleanliness, regenerable-cache and artifact-disposable lists. Those multiple callers corroborate the split-knowledge diagnosis; their production end-to-end removal behavior remains to be tested on controlled fixtures.

Held-out failure, correcting the first review: Opus second-pass evidence found e3c-transcribe-opus-01-14b had keep_worktree true and finished done, but the scheduled reaper journal records removal at 2026-10-03T20:36:39Z. The named ignored transcript directory and task preservation entry were absent from checked repository locations. This is a second repository-local output disappearance and a violated retention intent, not a passed recovery case. An off-repository copy remains unknown; the open-model-data owner must resolve that question. Do not claim permanent global loss without that check. Rejection test: both removal paths retain a keep_worktree task even when ordinary porcelain is clean and Git would allow non-force removal. Held-out valid control is a new isolated fixture with successful copy/retrieval and authorized retention release; it has not run.

## Bounded prototypes and benchmark

No performance winner is selected from the pure-helper replay. Next author-lane prototypes, in isolated dispatch worktrees, are deliberately small:

- Routing: inject healthy/deficit/unavailable snapshots into an isolated actual admission wrapper. Capture diagnostics and substitution calls with force-agent both true and false. True must not substitute; both retain diagnostic evidence. No real provider spawn.
- Output recovery: create a disposable miniature repository with task-start baseline, a task-created ignored transcript, a pre-existing ignored corpus-like file and a disposable cache. Invoke the actual preservation/reaper path on the miniature fixture only. Retrieve the transcript byte-for-byte; retain ambiguous/pre-existing data and reject unsafe cleanup. No live corpus/tree cleanup.
- Review feasibility: independently replay selector and recorder on identical full author-family/target facts. Selection and acceptance agree on admissibility without changing policy. No actual verdict is published.

Prototype verdicts are correctness-only: reject, accept, preserve/retain, recover. Repeating a deterministic fixture does not measure fleet delivery speed. No fixture speed claim is planned.

End-to-end measurement requires a qualified baseline before Phase 3. A bounded local scan found 55 lifecycle-named candidate JSON files; 11 parsed as task-lifecycle.v1, of which two are CLEANED_UP and nine ISSUE_LINKED. In this audited accepted-outcome cohort, launcher repair has one linked completed outcome (#9712); provider/runtime recovery, routine product change, architecture change, Ukrainian content and long epic resume each have zero confirmed members. One additional completed CI/test repair (#9723) is outside these frozen six strata. These are coverage counts, not assertions that the repository has no other completed outcomes. Broader cohort classification and acceptance evidence are unverified. Do not use every done task or receipt file as a delivered outcome.

Timing map to qualify before Phase 3:

| Stage | Existing candidate timestamps | What can and cannot be measured |
| --- | --- | --- |
| Intake | GitHub issue createdAt to dispatch task started_at | Coarse pre-dispatch elapsed time; readiness and active preparation versus waiting are not separated |
| Onboarding | Session capsule generated_at and health/canary checked_at where linked | Point observations only; no verified paired span in audited cohort, report unknown |
| Routing | Existing routing selection/admission event trace, if paired timestamps are present | Audit exact fields first; no verified paired span in audited cohort, report unknown |
| Authoring | Dispatch task started_at and finished_at | Worker wall time including embedded checks; not active coding time |
| Verification/review | Reviewer task started_at/finished_at; evidence recorded_at | Reviewer execution wall time when linked; evidence recorded_at alone is not test duration or review-queue wait |
| CI/landing | Check run started_at/completed_at; PR createdAt/mergedAt | Check runtime and PR elapsed lifetime; queue time needs an actual enqueue event, not inference from approval |
| Recovery/closeout | Failed-attempt finished_at, next-attempt started_at/finished_at; cleanup observation recorded_at | Coarse retry and observed closeout intervals; receipt arrival is not actual operation duration |

Do not sum overlapping intervals or call worker elapsed time active work. Where no paired fields exist, keep that metric unavailable or add narrow timestamped events through the existing lifecycle/Fleet receipt owner before claiming it. Timestamp qualification is measurement preparation, not another delivery gate.

Build the before/after comparison from canonical task records and GitHub PR/check history, not only the new pilot lifecycle ledgers. Use lifecycle ledgers as acceptance evidence when present; their two completed pilots are coverage examples, not an unbiased before group. Freeze group membership and success definition before comparison. Minimum: five independently delivered outcomes per side in every stratum for which a performance comparison is reported. This is a minimum coverage floor, not statistical power or a guarantee of significance. Below that, or with incomparable setups/large variation/missing endpoints, report inconclusive for that stratum; do not pool unrelated tasks to hide it. Record denominators, matched scope/configuration, correct accepted outputs, failures, refusals, retries, retrieval success, rework and missing telemetry. Compare natural completed work; do not multiply paid runs for a benchmark. Use a separate profiling/trace assessment to identify the limiter and report end-to-end distributions/uncertainty. Only Phase 3 supports a fleet delivery-speed claim.

Correctness-qualified narrow fixes may ship under their normal issue gates while the baseline accumulates. Cohort size is not a prerequisite for repairing or merging them. No invented improvement target is used.

## Execution and rollout after review

Phase 0 (this assessment): grounded history, owner traces, explicit uncertainty, pure controls and an independently critiqued concrete plan. Remaining end-to-end prototypes are unexecuted.

Creation inventory adoption is bounded to inventoried worktree creators; missing baselines retain data and expose a named residual, with migration and disk impact measured rather than hiding indefinite retention.

Phase 1 maps onto existing owned work rather than creating a new program around it:

- #9645, infra-harness owner: close the demonstrated ignored-output preservation/removal gap at the existing ownership boundary; strengthen the removal invariant and shared disposable taxonomy. Include the second re-run disappearance and both-path keep_worktree checks in that issue scope; the open-model-data owner verifies any off-repository copy. Coordinate with the infra-harness driver; DevOps does not take its lease or silently own its implementation.
- #9673, DevOps owner: preserve diagnostics when an explicit agent suppresses substitution, using its existing acceptance criteria and isolated admission test. No new prototype ceremony beyond the smallest proof those criteria require.
- #9668, DevOps owner: recover cancelled empty owned reservations under existing locks, preserving nonempty/uncertain work, using its existing acceptance criteria.
- Review-feasibility producer/consumer repair belongs to the existing review/admission owners and #9719 residual context. Before coding, record exact owned paths and criterion linkage on existing work, or create a single correctly registered issue only if none owns that outcome. No eligibility expansion is smuggled into it.

The shared routing/credit repairs in recent history already exist; agreement tests protect them only where actual caller gaps are demonstrated. Their existence alone is not a reason to lead with a routing rewrite. Each packet delivers one whole verifiable outcome through normal gates; no extra review panel, benchmark prerequisite or second repo driver.

Phase 2: simplify onboarding and Work API composition using the established interfaces and proof; integrate the existing pending quick-fix work after its required review/merge. Remove redundant caller interpretations and copied procedure text only when the supported path covers them.

Phase 3: pilot with one existing DevOps driver and one existing curriculum driver, retaining their leases and domain contracts. Compare verified delivery/recovery and coordination against observed baseline. Expand only when artifacts, gates and semantics are preserved and coordination/wait improves without more defects. No invented target before baseline.

Choose stack versus full-autopilot execution after operator plan approval, as requested. Either mode uses existing worktrees, task ownership, qualified review, CI, accountable landing and common cleanup. Current policy/cutover/eligibility changes still need their own scoped authority. CLIProxy is a possible compatible inference/telemetry adapter, not durable Fleet authority; do not migrate all seats without native tool/runtime compatibility proof and explicit scope.

Stop/rollback: duplicate execution, ownership loss, stale/protected-scope acceptance, lost output, unknown shown green or worsened semantic proof blocks expansion. Revert the affected integration while preserving existing task records, artifacts and in-flight identities. Do not disable gates to produce a favorable benchmark.

## Residuals and approval boundary

Owner: existing DevOps driver for this plan and cross-stream coordination; each implementation packet remains with its registered stream owner. Global rollout is not implemented; prototype runtime proof and measured baseline remain outstanding. #9719 still needs admissible implementation review outside all author families; fresh Claude capacity does not by itself remove that policy conflict. It is a separate delivery residual, not a reason to suspend this assessment or other ready work.

[Redacted for public-repository OPSEC.] This draft is the concrete checkpoint. Opus reviews requested changes and are retained with their exact target hashes. This revision addresses all three classes, including the second-pass keep_worktree counterexample. After two rounds the stopping rule is resolution of those classes only; cosmetic or unrelated findings become owned residuals. Exact-current-hash review state is recorded in companion receipts. Sol concurrence and a design verdict never assert that implementation is reviewed, CI-green, merged or deployed.

Sources: current upstream pstack correct, architect, design-red-flags and benchmark-checklist; Brendan Gregg benchmarking checklist. These are method evidence, not project authority. Existing source rules and ownership remain binding.

## Proposed for the next version

Everything above this heading is the reviewed text, except for the two publication deviations listed below. Version 1 makes no other change. The notes here are inputs for designated approval of a version 2; until then they change nothing.

1. Line 3 still describes the text as a draft awaiting an operator checkpoint, and line 137 describes this text as that checkpoint. The frontmatter records the approved design state. Version 2 should restate both sentences as the approved state.
2. Lines 3 and 135 name the existing DevOps driver as the accountable lead. Epic #9737 names the existing infra-harness driver as the single accountable lead, with DevOps contributing launcher, CI and landing work. Version 2 should reconcile the owner wording with the epic.
3. Lines 24, 26 and 137 point to companion evidence that lives only in ignored local state (`pstack-replay-evidence.json` and the review receipts). Version 2 should replace those references with sanitized repository locators or summaries.
4. Line 99 describes the authoring span as dispatch `started_at` to `finished_at`. The task record writes `started_at` when the dispatch is admitted or its worktree is reserved, before the worker starts. The span therefore includes the admission hold. [`docs/design/agent-friendly-delivery-baseline.md`](../design/agent-friendly-delivery-baseline.md) qualifies this; version 2 should adopt that wording.
5. Line 26 lacks a space between `SHA256` and the hash. This is cosmetic and was kept verbatim.

## Publication deviations

| Source line | Original class | Replacement | Reason |
| --- | --- | --- | --- |
| 26 | Ignored local-state path to a review receipt | Task-id locator: the result of task `devops-pstack-opus-plan` | Ignored state cannot be retrieved from the repository; the task id is the stable locator |
| 137 | Reported speech of the operator (one sentence) | `[Redacted for public-repository OPSEC.]` | The repository is public. Operator words stay out of public text |

The OPSEC pre-publication matcher (`scripts.opsec.prepublish.check_texts`) also flagged source line 42 (rule `4-backup-context`) and source line 133 (rule `6-speaker-label`, non-blocking). Both are false positives. Line 42 uses an ordinary routing-credit term, and line 133 is a section label followed by an owner field. Neither line contains host, backup, credential or personal detail, so both were kept verbatim. Changing them would have been a material edit.

## Publication verification

The script below compares the reviewed source with this file line by line. It prints counts, line numbers and deviation classes only, never line text. Run it where the ignored source is present:

```bash
.venv/bin/python compare_publication.py \
  batch_state/devops-review-workflow/agent-friendly-architecture-plan.md \
  docs/plans/agent-friendly-delivery.md \
  26=ignored-state-locator 137=opsec-operator-speech
```

```python
"""Compare a published plan body with its reviewed source, line by line."""

import hashlib
import json
import sys
from pathlib import Path

MARKER = "## Proposed for the next version"
source_path, published_path, *declared = sys.argv[1:]
source = Path(source_path).read_text(encoding="utf-8").splitlines()
text = Path(published_path).read_text(encoding="utf-8")
_, frontmatter, body = text.split("---\n", 2)
published = body.splitlines()
reviewed = published[: published.index(MARKER)]
while reviewed and reviewed[-1] == "":
    reviewed.pop()
classes = {int(item.split("=", 1)[0]): item.split("=", 1)[1] for item in declared}
changed = [n for n, (a, b) in enumerate(zip(source, reviewed), 1) if a != b]
regions = {}
for n in changed:
    a, b = source[n - 1], reviewed[n - 1]
    prefix = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    suffix = next((i for i, (x, y) in enumerate(zip(reversed(a), reversed(b))) if x != y), min(len(a), len(b)))
    suffix = min(suffix, min(len(a), len(b)) - prefix)
    regions[n] = {
        "class": classes.get(n, "UNDECLARED"),
        "verbatim_prefix_chars": prefix,
        "verbatim_suffix_chars": suffix,
        "source_chars": len(a),
    }
by_class = {}
for item in regions.values():
    by_class[item["class"]] = by_class.get(item["class"], 0) + 1
print(json.dumps({
    "source_sha256": hashlib.sha256(Path(source_path).read_bytes()).hexdigest(),
    "source_lines": len(source),
    "reviewed_lines_published": len(reviewed),
    "same_line_count_and_order": len(source) == len(reviewed),
    "verbatim_lines": len(source) - len(changed),
    "changed_lines": regions,
    "changed_by_class": by_class,
    "undeclared_changes": sorted(n for n in changed if n not in classes),
    "declared_but_unchanged": sorted(n for n in classes if n not in changed),
}, indent=2, sort_keys=True))
```

Output at version 1:

```json
{
  "changed_by_class": {
    "ignored-state-locator": 1,
    "opsec-operator-speech": 1
  },
  "changed_lines": {
    "26": {
      "class": "ignored-state-locator",
      "source_chars": 937,
      "verbatim_prefix_chars": 564,
      "verbatim_suffix_chars": 325
    },
    "137": {
      "class": "opsec-operator-speech",
      "source_chars": 615,
      "verbatim_prefix_chars": 0,
      "verbatim_suffix_chars": 525
    }
  },
  "declared_but_unchanged": [],
  "reviewed_lines_published": 139,
  "same_line_count_and_order": true,
  "source_lines": 139,
  "source_sha256": "d7e14787b55e13cd9c93056f06925cee1e7a618aad2eb4ddd2f34f36c8d2a2e4",
  "undeclared_changes": [],
  "verbatim_lines": 137
}
```
