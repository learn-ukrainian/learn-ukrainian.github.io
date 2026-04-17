# State/Artifact Reconciliation — Operator Guide

The v6 build pipeline maintains two sources of truth for each module:

1. **`state.json`** — phase-level status in `curriculum/{level}/orchestration/{slug}/state.json`
2. **Artifacts on disk** — the actual `.md` content files, review files, `needs-human-review.yaml`, etc.

These can drift apart when builds fail mid-flight, plan patches modify the plan after phases have run, or file operations fail silently. The reconciliation system detects these contradictions at resume time and forces re-execution of affected phases.

## How it works

`reconcile_state_artifacts(level, slug)` runs at the start of `_build_resume_invalidation_plan` — i.e., every time `--resume` evaluates whether to skip or re-run a module. It returns a list of `StateArtifactContradiction` objects, each with a `kind` and `detail`.

When contradictions are found:
- Each is logged as a warning: `state drift [level/slug]: kind — detail`
- Affected phases are invalidated (forced to re-run)
- The resume plan reports `reason: "state/artifact drift detected: ..."`

## Contradiction types

| `kind` | What it means | Auto-fix |
|--------|---------------|----------|
| `needs_human_review_state_only` | `state.json` says the module needs human review, but the `needs-human-review.yaml` artifact is missing. The escalation context is lost. | No auto-fix. Investigate `state.json` to decide whether to clear the flag or recreate the artifact. |
| `needs_human_review_artifact_only` | `needs-human-review.yaml` exists on disk but `state.json` doesn't have the `needs_human_review` flag. This can happen when state was cleared but file deletion failed. | No auto-fix. Either delete the stale artifact or re-set the state flag. |
| `verify_stale_after_content_update` | State says `verify: failed` but the content `.md` file was modified after the verify timestamp. The failure may no longer apply. | `verify` phase is invalidated and will re-run. |
| `review_complete_no_artifact` | State says `review: complete` but no review artifact (`.md` file) exists. The "pass" has no supporting evidence. | Review and downstream phases (`review-style`, `stress`, `publish`, `audit`) are invalidated. |
| `failed_phase_plan_hash_drift` | A plan-hash-tracked phase (`skeleton`, `write`, `exercises`, `annotate`, `verify`) is `failed`, but the plan has since changed. The failure was against an old plan. | Phases from the earliest drifted one onward are invalidated. |

## Manual investigation

To check a specific module's state health:

```bash
# Read state.json
cat curriculum/{level}/orchestration/{slug}/state.json | python -m json.tool

# Check for needs-human-review artifact
ls curriculum/{level}/orchestration/{slug}/needs-human-review.yaml

# Check content mtime vs state timestamps
stat curriculum/{level}/{slug}.md
```

To see contradictions without running a build:

```python
from build.v6_build import reconcile_state_artifacts
contradictions = reconcile_state_artifacts("a1", "module-slug")
for c in contradictions:
    print(f"{c.kind}: {c.detail}")
```

## Plan-patch failure diagnostics

When a plan-patch attempt fails to parse Gemini's response, a diagnostic artifact is saved to `curriculum/{level}/orchestration/{slug}/v6-plan-patch-diagnostic.yaml`. It contains:

- `failure_reason` — one of: `empty_output`, `missing_delimiters`, `empty_payload_between_delimiters`, `yaml_parse_error: ...`, `unexpected_payload_type: ...`
- `raw_output_length` — how many characters Gemini returned
- `raw_output_preview` — first 500 characters of the response

The full raw output is always saved to `v6-plan-patch-output.md` for investigation.

### Failure reasons

| Reason | Typical cause | Suggested action |
|--------|---------------|------------------|
| `empty_output` | Gemini returned nothing (timeout, quota) | Retry the build; check Gemini API status |
| `missing_delimiters` | Gemini produced prose instead of structured output | Review the prompt in `v6-plan-patch-prompt.md`; the model may need stronger delimiter instructions |
| `yaml_parse_error` | Delimiters present but content is not valid YAML | Usually a one-off — retry should work |
| `unexpected_payload_type` | YAML parsed but was a list/string, not a mapping | Prompt issue — review template |
| `empty_payload_between_delimiters` | Delimiters present but nothing between them | Usually a one-off — retry should work |
