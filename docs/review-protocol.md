# Universal Review Protocol

> **Canonical contract (v1):** versioned JSON schema
> `schemas/code-review-findings.v1.schema.json`, validated by
> `scripts/verify_review.py`. Legacy loose `FINDING:` text is **removed** as a
> dual source of truth (issue #5284). The verifier accepts bare schema-valid
> JSON or the review-loop reply envelope described below.

The review-loop envelope starts with one `VERDICT:` line, then one `SCORE:`
line. Leading whitespace is allowed. Verdicts are `APPROVE`, `REQUEST_CHANGES`
and `BLOCKED`; scores are integers from 1 through 10 followed by `/10`, with
an optional rationale. Exactly one closed, top-level fenced block contains
the JSON object, with info string `json` or empty. Other prose supplies no
verdict or findings. Duplicate header declarations, absent or multiple fenced
blocks, invalid schema and header/correctness disagreement fail closed.
`APPROVE` requires `correct`, `REQUEST_CHANGES` requires `incorrect`, and
`BLOCKED` requires `uncertain`. The recorder's shared findings validation
also applies. No reviewer payload is synthesized from prose.

## Evidence requirement — NON-NEGOTIABLE

Every finding MUST include:

1. **Stable ID**, title, body, priority `P0`–`P3`, confidence `0..1`, and category.
2. **Code location** — repository-relative path plus `start_line` / `end_line`
   and `claim_type` (`present` | `missing`).
3. **Verbatim evidence** copied exactly from the reviewed target (only
   line-ending normalization is applied during verification).
4. **Why it is wrong** and the **smallest correct fix**.
5. **Source citation(s)** or explicit `["none"]`.

Unknown fields, missing required fields, unsafe paths, invalid enums/ranges,
and text outside either accepted input form **fail closed**.

## Hallucination guards

1. **DIFF vs FILE**: lines outside the diff still exist on the branch. A
   “missing” claim must prove absence with **file** evidence (`claim_type:
   "missing"` plus verbatim context), not “I don’t see it in the diff.”
2. **Three-dot surface only (#5802)**: every finding `location.path` MUST appear
   on the PR’s three-dot / merge-base file list (`gh pr view <N> --json files`,
   sealed snapshot `changed_paths`, or
   `git diff $(git merge-base <base> <head>)...<head>`). **Never** use two-dot
   `git diff <base-tip>..<head>` against a moved base tip — that invents
   deletions of files main gained after the fork and produces confident-but-false
   BLOCK verdicts. A runner-dispositioned `follow_up` with a nonempty rationale
   may cite a regular file outside the changed paths when it exists in Git at
   `target.head_sha`. Its quote and range are checked against that head blob,
   never the working copy. Blocking dispositions, absent head files, directories
   and symlinks remain refused.
3. **Primary location on the change**: for `claim_type: "present"`, the
   primary line range must land on a **changed line** of the frozen target,
   except for the unchanged-file follow-up above.
   Missing-code claims use contextual evidence and must not invent a diff line
   for code that is not there.
4. **No invented line numbers**: every location must resolve on the exact
   frozen head/local snapshot. Prefer an exact match at the claimed
   `start_line`; identical text earlier in the file must not steal a later
   true match. `end_line` must equal the exact verbatim span (no inflated
   ranges that intersect unrelated changed lines). On mismatch, report the
   deterministic first actual match and `line_mismatch`.
5. **Path safety**: no absolute paths, no `..`, no drive paths, no symlink
   escapes. Paths outside the changed surface require the follow-up exception above.
6. **Decode/read failures** become a stable fail-closed evidence outcome
   (`quote_missing` with detail), never an uncaught exception.

## Canonical reviewer JSON

```json
{
  "schema_version": "code-review-findings.v1",
  "overall": {
    "correctness": "incorrect",
    "explanation": "A blocking defect was found on the frozen target.",
    "confidence": 0.9
  },
  "findings": [
    {
      "id": "F001",
      "title": "Short title",
      "body": "Full finding narrative.",
      "priority": "P1",
      "confidence": 0.85,
      "category": "bug",
      "location": {
        "path": "scripts/example.py",
        "start_line": 12,
        "end_line": 12,
        "claim_type": "present"
      },
      "verbatim": "exact = line_from_file",
      "why_wrong": "One paragraph on the defect.",
      "smallest_fix": "Minimal correct change.",
      "sources": ["none"]
    }
  ]
}
```

Categories: `bug`, `security`, `correctness`, `regression`, `api`, `tests`,
`docs`, `performance`, `style`, `other`.

`overall.correctness: "correct"` with findings means the reviewer judges no
finding blocking under `critical-rules.md` section 8.4. Findings remain in the
receipt, and the runner still returns `actionable` / exit 1.

### Compatibility / removal decision

| Format | Status |
| --- | --- |
| `schema_version: code-review-findings.v1` JSON | **Canonical** |
| Legacy `FINDING:` / `FILE:LINE:` text blocks | **Removed** — verifier exits `invalid` |

Do not maintain two canonical formats indefinitely. Update any prompt that
still shows the old text block to this JSON contract.

## Exact-target verification

Bind verification to one explicit mode from `scripts.review.target_resolution`
(PR #5286 foundation — do not invent a parallel target API):

| Mode | Meaning |
| --- | --- |
| `local` | staged + unstaged + untracked vs HEAD |
| `commit` | single commit vs its parent |
| `branch` | branch vs explicit base (merge-base) |
| `pr` | PR head vs merge-base with its base branch |

### Target-input fingerprint (not reviewer JSON)

`input_sha256` on the receipt is the **target-input fingerprint**: a
deterministic SHA-256 over target metadata plus the exact patch bytes (and
untracked file bytes in local mode) needed to reconstruct the reviewed
surface. It **must** change when a local source, the changed-path set,
base/head, or committed content changes. Display-only target descriptions and
equivalent ref spellings do not affect the fingerprint.

The whole raw reviewer reply is hashed separately as `reviewer_output_sha256`,
including headers, fences and surrounding prose. UTF-8 file input preserves
line endings so a historical result can be replayed without changing its digest.

### Two-stage runner usage

**Stage 1 — source-blind capture (before the reviewer runs):**

```bash
.venv/bin/python scripts/verify_review.py --emit-target-manifest \
  --mode local --repo-root .
# → JSON with mode, head_sha (when applicable), changed_paths, input_sha256
```

**Stage 2 — verify after review (same mode/target):**

```bash
.venv/bin/python scripts/verify_review.py --from-stdin --mode local \
  --expected-input-sha256 "$TARGET_INPUT_SHA" \
  --expected-head "$HEAD_SHA" \   # non-local modes
  --issue-ref '#NNNN' \
  --scope-json '{"owner_boundary":"path/or/paths"}' \
  --author-model '...' --author-family '...' --author-harness '...' \
  --author-selection-reason '...' \
  --reviewer-model '...' --reviewer-family '...' --reviewer-harness '...' \
  --reviewer-selection-reason '...' \
  --tests-json '{"commands":["pytest ..."],"passed":true}' \
  --behavior-proof-state-file "$STATE_FILE" \
  --routing-lineage-json '{"implementation_agent":"...","accountable_advisor":"..."}' \
  --dispositions-json '{"F001":{"disposition":"in_scope_blocker","rationale":"..."}}' \
  --receipt-path /tmp/review-receipt.json
```

Stale / incomplete gates (fail closed):

- `--expected-input-sha256` is **required** for `clean` / `actionable`.
  Absence → `incomplete` (never green). Mismatch → `stale`.
- `--expected-head` must match the resolved target head (non-local modes).
- Paths outside the frozen changed set, unsafe paths, and symlink escapes fail.

## Envelope provenance (fail closed, generic)

The runner **never** fabricates routing lineage or task-specific agent
defaults. Placeholders `unknown`, `unspecified`, and `not_provided` fail.

A valid **clean** or **actionable** receipt requires:

- concrete `issue_ref` (not empty / placeholder);
- non-empty frozen `scope` with at least one concrete value;
- complete author and reviewer `model` / `family` / `harness` /
  `selection_reason` (no placeholders);
- **cross-family gate**: `author.family` and `reviewer.family` must be
  concrete and different (case-insensitive). Same-family lineage cannot
  exit `clean` (final disposition is non-clean / `actionable`);
- `tests` with concrete `commands` and `passed: true`, **or** explicitly
  supported `status: "n/a"` with a non-empty `reason`. `passed: false` /
  `status: "fail"` makes the receipt non-clean / `actionable` (never exit 0);
- `behavior_proof.schema_version: "behavior-proof.v1"`, emitted by
  `closeout_cli behavior-proof record`; unversioned proof is not accepted as
  legacy green evidence. Both `source_aware` and `source_blind` are required.
  A `pass` needs
  at least one complete clause: the frozen `intended_behavior` claim, a
  command or manual step (and `cwd` for a command), exit/result, observation,
  evidence reference, and the exact target-input fingerprint. Record it with
  `closeout_cli behavior-proof record`; do not hand-author a competing surface
  claim. `n/a` requires a non-empty `reason`; `fail` is non-clean / actionable;
  missing or incomplete proof is `incomplete`;
- `source_blind` `pass` records an explicit boolean `blind_enforced`. A true
  value on any status requires a target-bound isolation attestation validated
  through the isolation interface. Ordinary justified `n/a` does not carry the
  field. A false value is rendered as `declared-blind/unenforced`, never as
  mechanically enforced;
- explicit non-empty `routing_lineage` (supplied by the runner; not invented);
- for every finding: disposition key present, disposition ∈
  `in_scope_blocker` | `follow_up` | `stop_and_escalate`, non-empty rationale;
  unknown or missing finding IDs rejected.

Malformed runner envelope JSON (`--scope-json`, `--tests-json`,
`--behavior-proof-json`, `--dispositions-json`, `--routing-lineage-json`)
exits `invalid` (2) with structured error output. Incomplete envelope data
exits `incomplete` (3). Explicit failed proof / same-family exits
`actionable` (1) — **never** `0` when the formal closeout gate fails.

## Runner command

Local / CI (no GitHub mutation) — full envelope example:

```bash
TARGET_SHA=$(.venv/bin/python scripts/verify_review.py --emit-target-manifest \
  --mode local --repo-root . | .venv/bin/python -c 'import json,sys; print(json.load(sys.stdin)["input_sha256"])')

# After `target` and `freeze`, record the proof against that frozen state.
# The recorder emits behavior_proof.schema_version = behavior-proof.v1 and
# derives `claim` from `--intended-behavior`; it does not accept a separate
# behavior-surface field.
.venv/bin/python -m scripts.review.closeout_cli --state-file "$STATE_FILE" \
  behavior-proof record --surface source_aware --status pass \
  --command '.venv/bin/python scripts/verify_review.py --help' --cwd . \
  --exit-code 0 --observation 'help rendered' --evidence-ref 'terminal:proof-aware'
.venv/bin/python -m scripts.review.closeout_cli --state-file "$STATE_FILE" \
  behavior-proof record --surface source_blind --status pass \
  --command '.venv/bin/python scripts/verify_review.py --help' --cwd . \
  --exit-code 0 --observation 'help rendered as a user' --evidence-ref 'terminal:proof-blind'

.venv/bin/python scripts/verify_review.py --from-stdin --mode local \
  --expected-input-sha256 "$TARGET_SHA" \
  --issue-ref '#5284' \
  --scope-json '{"owner_boundary":"scripts/verify_review.py"}' \
  --author-model 'gpt-6.1-sol' --author-family openai --author-harness codex \
  --author-selection-reason 'accountable-author' \
  --reviewer-model 'grok-4.7' --reviewer-family xai --reviewer-harness grok-build \
  --reviewer-selection-reason 'cross-family-gate' \
  --tests-json '{"commands":["pytest tests/test_verify_review.py"],"passed":true}' \
  --behavior-proof-state-file "$STATE_FILE" \
  --routing-lineage-json '{"implementation_agent":"runner-supplied","accountable_advisor":"runner-supplied"}' \
  --receipt-path /tmp/review-receipt.json
```

Commit / branch / PR targets:

```bash
.venv/bin/python scripts/verify_review.py --review-file review.json --mode commit --commit HEAD \
  --expected-input-sha256 "$TARGET_SHA" --expected-head "$HEAD" ...
.venv/bin/python scripts/verify_review.py --from-stdin --mode branch --branch feature/x --base origin/main ...
.venv/bin/python scripts/verify_review.py --from-stdin --mode pr --pr 5286 ...
```

GitHub comment posting remains **opt-in** (`--post-comment` with `--issue`)
and is never the only durable proof path. Prefer stdout or `--receipt-path`.

### Stable exit codes

| Code | Name | Meaning |
| --- | --- | --- |
| 0 | `clean` | Valid JSON, overall correct, no findings, evidence OK, complete envelope + target fingerprint |
| 1 | `actionable` | Valid review with findings or overall `incorrect`; complete envelope, with the approved unverified follow-up exception below |
| 2 | `invalid` | Non-JSON, legacy text, schema violation, unsafe/malformed structure |
| 3 | `incomplete` | Empty input, overall `uncertain` with no findings, or incomplete envelope / missing expected fingerprint |
| 4 | `stale` | Head SHA or target-input fingerprint mismatch |
| 5 | `unverifiable` | `quote_missing`, `line_mismatch`, or `out_of_scope`, except approved unverified follow-up notes below |

A frozen `ukrainian` closeout is a behavior-proof carrier, not a reviewer
selection. `closeout_cli freeze --review-profile ukrainian` stores that
profile. `resolve-reviewer` still refuses it. After both surfaces are recorded
on a pull-request target, `closeout_cli behavior-proof receipt` reads the live
pull-request comments and the authenticated login and writes the receipt beside
the state file. The receipt keeps `code-review-receipt.v1` and both proof
surfaces, omits `reviewer` and `reviewer_payload`, and records
`ukrainian_seat_verdicts`: one entry per required family from the recorded
comments, each entry the union of that family's non-void cross-family chunks.
One partial chunk does not complete a seat, and conflicting denominators are
refused. Author models come from those comments; author harness comes from the
implementation commits. Caller reviewer flags, findings JSON, and caller
lineage are refused. A learner-content diff does not reconcile a receipt that
lacks this profile.
The receipt target SHA stays the PR head after merge. Running the learner
page on a local merge of that head is a separate observation.

For typed lifecycle behavior evidence, `error` must be null. The receipt must
be either `clean` / exit 0, or `actionable` / exit 1 with all of:

- `reviewer_payload.overall.correctness` is `correct`;
- receipt finding IDs equal `reviewer_payload.finding_ids`;
- every finding outcome is `verified`, or is `quote_missing`, `line_mismatch`
  or `out_of_scope` with runner disposition `follow_up`;
- every finding has a disposition and a non-empty rationale;
- no finding has disposition `stop_and_escalate`.
- `unverified_follow_up_notes` lists every unverified note, preserving its
  original outcome, detail, disposition and rationale. Lifecycle closeout
  reports name those notes with their AC and evidence IDs.

This accepts the reviewer's non-blocking judgment without removing findings or
changing the receipt. An `in_scope_blocker` disposition is not itself a refusal:
the reviewer's `correct` verdict carries the blocking judgment. All other
lifecycle checks, including receipt digest, exact head, target-input fingerprint,
reviewer independence, and passing behavior surfaces, still apply.

An APPROVE with these unverified follow-up notes remains `actionable` / exit 1.
It is approved, never evidentially clean. Exact quotes and line ranges still
produce their original failures, with no whitespace normalization, severity
change or automatic disposition change. Non-APPROVE verdicts, schema and
malformed-path failures, header/JSON disagreement, missing or invalid
dispositions or rationale, stale target or provenance, failed behavior proof
and missing outside-family approval remain refused. This exception permits
unverified notes; it does not verify absent files or other out-of-scope evidence.

## Deterministic receipt (runner-built)

The **runner** — not the reviewer — emits a receipt
(`schema_version: code-review-receipt.v1`) containing:

- originating issue and frozen scope;
- author and reviewer model / family / harness / selection reason;
- target mode, base SHA, head SHA, changed paths, non-test LOC,
  **target-input** `input_sha256`;
- separate `reviewer_output_sha256`;
- per-finding validation outcome (and disposition/rationale when supplied);
- visible `unverified_follow_up_notes`, with each original outcome and detail;
- tests and source-aware / source-blind behavior proof;
- final disposition and exit code;
- routing lineage **only when the runner supplies it** (never hardcoded
  task-specific defaults; **do not** embed transient quota percentages).

Runtime receipts are **generated evidence**. Write them to stdout or an
explicit local path. They must **not** enter forbidden PR artifacts:

- `status/*.json`
- `audit/*-review.md`
- `review/*-review.md`
- `data/telemetry/**`

Multi-finding validation order is deterministic: sort by
`(path, start_line, end_line, id)`.

## Universal review loop

1. Freeze scope and resolve the exact target (`scripts.review.closeout_cli` /
   `target_resolution`).
2. **Emit target manifest** (`--emit-target-manifest`) and record
   `input_sha256` (+ head when applicable).
3. Dispatch the reviewer with `--review` so this protocol is prepended.
4. Reviewer reads the **exact target** (worktree / `git show <head>:<path>` /
   PR head), not a different checkout.
5. Reviewer returns **only** `code-review-findings.v1` JSON.
6. Run `scripts/verify_review.py` with the same mode/base/head constraints,
   `--expected-input-sha256`, and a complete envelope.
7. Read the receipt:
   - `clean` → proceed to merge/closeout.
   - `actionable` → adjudicate and fix only in-scope blockers.
   - `invalid` / `incomplete` / `stale` / `unverifiable` → reject the review
     output; re-run after correcting structure, freshness, or evidence — do not
     treat bad evidence or incomplete provenance as a green closeout.

## Reviewer selection trace

`closeout_cli resolve-reviewer` applies hard exclusions before ranking. Its
`review_scheduler.profile_risk_role_order` then ranks semantic suitability,
followed by quality tier and deterministic resource-pressure scoring within
that fit and tier. An earlier YAML rung does not override a better role match.

For a `gpt-6.1-sol` author with profile `code` and risk `medium` or `low`,
native `claude-opus-5-5` is eligible, but `claude-sonnet-5-5` matches a role
earlier in that profile's role order, so Sonnet wins before `selection_score`
breaks ties. This is the configured suitability rule, rather than an Opus health
or quota exclusion. Both may report unknown health when no routing snapshot is
supplied. When an explicit requested role fits both equally, Opus's authority
tier wins. At risk `high`, only the models `review_scheduler.risk_reviewer_models`
lists (`gpt-6.1-sol`, `claude-opus-5-5`) are eligible (#9538), so Sonnet is
excluded with that stated reason. Critical security review excludes every Sonnet
model.

Activity admission reads the catalog roles (#9583). A review, critique or
approval of record — a review-typed `dispatch.py dispatch` of any profile, an
`ask-* --review`, the review worker, and `record_cf_verdict` — refuses a model
pin with no `review_scheduler.activity_roles.review` role; an ACP ask, consult
or discussion refuses one with neither a `review` nor a `consult` role. The
refusal applies on every seat and transport, including the Cursor slug, so
`claude-fable-5-1` has no review or consult role and is refused for those activities.
Fable 5.1 is parked: not routed by default, explicit pin only for its catalogued
coding/orchestration roles; reintroduction or a successor model is an operator
decision (OO-58, #11327). Retired models such as `gpt-6-astra` are refused.

Read `status`, `reason`, `suitability_rank`, and `selection_score` for every
candidate; do not infer provider health or review eligibility from selection.
