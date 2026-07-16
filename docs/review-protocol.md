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
   frozen head/local snapshot.
4. **Path safety**: no absolute paths, no `..`, no drive paths, no symlink
   escapes, no paths outside the reviewed changed surface.

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

Evidence matching:

- Compare with **line-ending normalization only** (CRLF/CR → LF).
- Do **not** strip backticks, punctuation, or collapse whitespace.
- Report the **actual matched line** when the quote is found elsewhere
  (`line_mismatch`).
- Distinct outcomes: `verified`, `line_mismatch`, `quote_missing`,
  `malformed`, `out_of_scope`.
- A structurally valid report with invalid evidence is **not** a clean review.

Stale checks (fail closed):

- `--expected-head` must match the resolved target head (non-local modes).
- `--expected-input-sha256` must match the SHA-256 of the review input bytes.
- Paths outside the frozen changed set, unsafe paths, and symlink escapes fail.

## Runner command

Local / CI (no GitHub mutation):

```bash
.venv/bin/python scripts/verify_review.py --from-stdin --mode local \
  --issue-ref '#5284' \
  --author-model 'gpt-5.6-sol' --author-family openai --author-harness codex \
  --author-selection-reason 'accountable-author' \
  --reviewer-model 'grok-4.5' --reviewer-family xai --reviewer-harness grok-build \
  --reviewer-selection-reason 'cross-family-gate' \
  --tests-json '{"commands":["pytest tests/test_verify_review.py"],"passed":true}' \
  --behavior-proof-json '{"source_aware":{"status":"pass"},"source_blind":{"status":"n/a","reason":"no user-visible surface"}}' \
  --receipt-path /tmp/review-receipt.json
```

Commit / branch / PR targets:

```bash
.venv/bin/python scripts/verify_review.py --review-file review.json --mode commit --commit HEAD
.venv/bin/python scripts/verify_review.py --from-stdin --mode branch --branch feature/x --base origin/main
.venv/bin/python scripts/verify_review.py --from-stdin --mode pr --pr 5286
```

GitHub comment posting remains **opt-in** (`--post-comment` with `--issue`)
and is never the only durable proof path. Prefer stdout or `--receipt-path`.

### Stable exit codes

| Code | Name | Meaning |
| --- | --- | --- |
| 0 | `clean` | Valid JSON, overall correct, no findings, all evidence verified |
| 1 | `actionable` | Valid review with findings or overall `incorrect` (evidence OK) |
| 2 | `invalid` | Non-JSON, legacy text, schema violation, unsafe/malformed structure |
| 3 | `incomplete` | Empty input or overall `uncertain` with no findings |
| 4 | `stale` | Head SHA or input hash mismatch |
| 5 | `unverifiable` | `quote_missing`, `line_mismatch`, or `out_of_scope` on any finding |

## Deterministic receipt (runner-built)

The **runner** — not the reviewer — emits a receipt
(`schema_version: code-review-receipt.v1`) containing:

- originating issue and frozen scope;
- author and reviewer model / family / harness / selection reason;
- target mode, base SHA, head SHA, changed paths, non-test LOC, input SHA-256;
- per-finding validation outcome (and optional accountable disposition/rationale);
- tests and source-aware / source-blind behavior proof;
- final disposition and exit code;
- routing lineage (implementation agent, accountable advisor; **do not** embed
  transient quota percentages as defaults).

Example routing lineage for this infrastructure slice:

```json
{
  "implementation_agent": "grok/5284-strict-review-receipts",
  "accountable_advisor": "GPT-5.6 Sol",
  "selection_note": "Grok 4.5 high substituted for the issue's provisional Claude developer due to live routing-budget recommendation; GPT-5.6 Sol remains accountable advisor/integrator and cross-family reviewer."
}
```

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
2. Dispatch the reviewer with `--review` so this protocol is prepended.
3. Reviewer reads the **exact target** (worktree / `git show <head>:<path>` /
   PR head), not a different checkout.
4. Reviewer returns **only** `code-review-findings.v1` JSON.
5. Run `scripts/verify_review.py` with the same mode/base/head constraints.
6. Read the receipt:
   - `clean` → proceed to merge/closeout.
   - `actionable` → adjudicate and fix only in-scope blockers.
   - `invalid` / `incomplete` / `stale` / `unverifiable` → reject the review
     output; re-run after correcting structure, freshness, or evidence — do not
     treat bad evidence as a green closeout.
