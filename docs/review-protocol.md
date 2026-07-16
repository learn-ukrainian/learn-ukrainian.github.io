# Universal Review Protocol

> **Canonical contract (v1):** versioned JSON schema
> `schemas/code-review-findings.v1.schema.json`, validated by
> `scripts/verify_review.py`. Legacy loose `FINDING:` text is **removed** as a
> dual source of truth (issue #5284). Reviewers must emit **only** schema-valid
> JSON — no prose wrapper, no markdown fences around the payload.

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
and non-JSON chatter **fail closed**.

## Hallucination guards

1. **DIFF vs FILE**: lines outside the diff still exist on the branch. A
   “missing” claim must prove absence with **file** evidence (`claim_type:
   "missing"` plus verbatim context), not “I don’t see it in the diff.”
2. **Primary location on the change**: for `claim_type: "present"`, the
   primary line range must land on a **changed line** of the frozen target.
   Missing-code claims use contextual evidence and must not invent a diff line
   for code that is not there.
3. **No invented line numbers**: every location must resolve on the exact
   frozen head/local snapshot. Prefer an exact match at the claimed
   `start_line`; identical text earlier in the file must not steal a later
   true match. `end_line` must equal the exact verbatim span (no inflated
   ranges that intersect unrelated changed lines). On mismatch, report the
   deterministic first actual match and `line_mismatch`.
4. **Path safety**: no absolute paths, no `..`, no drive paths, no symlink
   escapes, no paths outside the reviewed changed surface.
5. **Decode/read failures** become a stable fail-closed evidence outcome
   (`quote_missing` with detail), never an uncaught exception.

## Canonical reviewer JSON

```json
{
  "schema_version": "code-review-findings.v1",
  "overall": {
    "correctness": "correct",
    "explanation": "No defects found on the frozen target.",
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
base/head, or committed content changes.

Reviewer JSON is hashed separately as `reviewer_output_sha256`.

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
  --behavior-proof-json '{"source_aware":{"status":"pass"},"source_blind":{"status":"pass"}}' \
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
- non-empty `tests`;
- both `source_aware` and `source_blind` keys in `behavior_proof`;
- explicit non-empty `routing_lineage` (supplied by the runner; not invented);
- for every finding: disposition key present, disposition ∈
  `in_scope_blocker` | `follow_up` | `stop_and_escalate`, non-empty rationale;
  unknown or missing finding IDs rejected.

Malformed or incomplete envelope data may still emit a receipt, but exits
`incomplete` or `invalid` — **never** `0`/`1`.

## Runner command

Local / CI (no GitHub mutation) — full envelope example:

```bash
TARGET_SHA=$(.venv/bin/python scripts/verify_review.py --emit-target-manifest \
  --mode local --repo-root . | .venv/bin/python -c 'import json,sys; print(json.load(sys.stdin)["input_sha256"])')

.venv/bin/python scripts/verify_review.py --from-stdin --mode local \
  --expected-input-sha256 "$TARGET_SHA" \
  --issue-ref '#5284' \
  --scope-json '{"owner_boundary":"scripts/verify_review.py"}' \
  --author-model 'gpt-5.6-sol' --author-family openai --author-harness codex \
  --author-selection-reason 'accountable-author' \
  --reviewer-model 'grok-4.5' --reviewer-family xai --reviewer-harness grok-build \
  --reviewer-selection-reason 'cross-family-gate' \
  --tests-json '{"commands":["pytest tests/test_verify_review.py"],"passed":true}' \
  --behavior-proof-json '{"source_aware":{"status":"pass"},"source_blind":{"status":"n/a","reason":"no user-visible surface"}}' \
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
| 1 | `actionable` | Valid review with findings or overall `incorrect` (evidence OK + complete envelope) |
| 2 | `invalid` | Non-JSON, legacy text, schema violation, unsafe/malformed structure |
| 3 | `incomplete` | Empty input, overall `uncertain` with no findings, or incomplete envelope / missing expected fingerprint |
| 4 | `stale` | Head SHA or target-input fingerprint mismatch |
| 5 | `unverifiable` | `quote_missing`, `line_mismatch`, or `out_of_scope` on any finding |

## Deterministic receipt (runner-built)

The **runner** — not the reviewer — emits a receipt
(`schema_version: code-review-receipt.v1`) containing:

- originating issue and frozen scope;
- author and reviewer model / family / harness / selection reason;
- target mode, base SHA, head SHA, changed paths, non-test LOC,
  **target-input** `input_sha256`;
- separate `reviewer_output_sha256`;
- per-finding validation outcome (and disposition/rationale when supplied);
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
