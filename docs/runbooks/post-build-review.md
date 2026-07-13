# Post-build review runbook

The canonical protocol lives only at
`agents_extensions/shared/skills/post-build-review/`. Deployed agent directories
are mirrors. Do not maintain an independent Codex, Claude, Gemini, `.agent`, or
dispatch-prompt copy.

## Operator invocation

Use the short prompt:

```text
Use $post-build-review for bio/oleksandr-bilash.
```

The skill runs deterministic preparation, selects the core or seminar semantic
family from versioned track policy, requires a source-backed semantic result,
and combines both layers into `/tmp/post-build-review-result.json`. It must not
write curriculum audit/status/review files or telemetry.

## Responsibility boundaries

| Responsibility | Canonical location |
| --- | --- |
| Deterministic facts and aggregation | `scripts/audit/post_build_review.py` plus existing audit code |
| Mechanically verifiable track rules | `post-build-review/config/track-policy.v1.yaml` |
| Semantic judgment | `post-build-review/prompts/*.md` |
| Orchestration order | `post-build-review/SKILL.md` |
| Output shape | `post-build-review/schema/review-result.v2.schema.json` |
| Operator maintenance | This runbook |

The evidence-derived size contract consumes the existing size-policy audit. It
does not duplicate thresholds. Bilash is the first BIO exemplar; its range,
headings, and disposition are local evidence, never global BIO policy.

## Versioning

Every result records:

- `review_protocol_version`
- `deterministic_contract_version`
- `semantic_prompt_version`
- `track_policy_version`
- effective `prompt_sha256`
- reviewer agent, family, exact model, and effort
- reviewer evidence capabilities and learner-evidence access ledger
- exact raw semantic-response SHA-256, byte count, parser status, and contract status
- atomic claim ledger with count-consistency enforcement
- deterministic argv/cwd/exit/output hashes/config provenance
- source-file hashes and a normalized reproducibility key

Bump the version responsible for a behavior change:

| Change | Version to bump |
| --- | --- |
| Aggregation, command composition, disposition order | `review_protocol_version` |
| Deterministic evidence/provenance semantics | `deterministic_contract_version` |
| Common/core/seminar judgment instruction | `semantic_prompt_version` |
| Track mapping, mechanical rule, skip classification | `track_policy_version` |

Use semantic versioning. A breaking schema change requires a new schema id/file
and review protocol major version. Schema v1 remains available for historical
validation; new reviews emit v2. Prompt hashes change automatically from the
exact assembled common + family + resolved context.

## Bug-fix workflow

For every review defect:

1. Reproduce it with a failing fixture in
   `tests/fixtures/post_build_review/regressions.v1.yaml`.
2. Classify the responsible layer: deterministic code, track policy, semantic
   prompt, disposition, schema, or orchestration.
3. Patch the single canonical source for that layer.
4. Add or extend a regression test that fails before the patch.
5. Increment the applicable protocol version above.
6. Regenerate mirrors with `npm run agents:deploy` (or
   `scripts/deploy_prompts.sh`) and never edit a mirror directly.
7. Run all affected fixtures, schema/prompt/track/read-only tests, deployment
   drift checks, and the Bilash exemplar.
8. Obtain an independent review from outside the author's model family. Resolve
   all material findings; internal same-family helpers do not satisfy the gate.
9. Commit with an `X-Agent` trailer and merge through one scoped PR. Close the
   linked stream issue with command/output evidence and clean the worktree.

For semantic-response defects, preserve the exact reviewer output. Never copy
selected fields into a new JSON object, strip a Markdown wrapper, choose one of
multiple objects, adjust counts, or reconcile retries. Finalize the raw response
to a structured `INCOMPLETE` result. A retry starts a distinct review and cannot
erase the failed result.

For learner-evidence defects, separate catalog metadata from content evidence.
Metadata may verify identity/date labels; it cannot verify what a recording,
video, image, or source passage contains. Record the reviewer's direct modality
capabilities during `prepare`. If a required modality cannot be inspected,
return `INCOMPLETE`; if evidence is definitively metadata-only, inaccessible,
or absent for the learner task, record a material grounding/pedagogy finding.

`.agent/` is preserve-by-default because it contains runtime state. A skill
rename/removal therefore requires an explicit post-deploy check for the old
`.agent/skills/<name>` mirror and removal of that stale mirror only; never clean
unrelated `.agent/` state.

## Validation

From the issue worktree:

```bash
.venv/bin/python -m pytest tests/audit/test_post_build_review.py -q
.venv/bin/python -m pytest tests/test_deploy_script_idempotency.py -q
.venv/bin/python scripts/lint/lint_agent_skills.py
.venv/bin/python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" \
  agents_extensions/shared/skills/post-build-review
scripts/deploy_prompts.sh
bash scripts/check_rules_deployment.sh
git diff --check
```

Then forward-test the exact short prompt in a fresh agent. Validate the emitted
result with:

```bash
.venv/bin/python scripts/audit/post_build_review.py validate \
  /tmp/post-build-review-result.json
```

Compare `reproducibility_key`, version fields, prompt hash, source hashes,
deterministic findings, size-policy evidence, and combined disposition with the
versioned Bilash exemplar. Reviewer identity is expected to differ across
independent agents.

## Read-only and failure behavior

- Outputs inside the repository are rejected.
- Unknown tracks, ambiguous/missing targets, malformed audit JSON, incomplete
  seminar claim coverage, claim-ledger/count mismatch, malformed or duplicated
  semantic JSON, uncovered learner-evidence modalities, source drift, required
  skips, and missing provenance fail closed.
- `finalize` exits zero only for `PASS`; `BLOCK`, `REVISE`, and `INCOMPLETE`
  return non-zero after writing a valid structured result.
- Never use the legacy module audit/shell wrapper or opt into MDX regeneration
  from this protocol; those paths can write generated artifacts.
