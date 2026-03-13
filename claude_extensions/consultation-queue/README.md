# Consultation Queue

Template change proposals awaiting human review.

## How it works

When the pipeline's `--consult` flag diagnoses a **template-caused issue** and the consultation result has `scope: all_modules`, the proposed change is queued here instead of being auto-applied. This prevents a single module's diagnosis from silently altering templates used by 700+ modules.

## File format

Each `.yaml` file contains:

```yaml
source_module: "a1/the-ukrainian-alphabet"
consultation_num: 1
confidence: high
root_cause: "The template instructs..."
proposed_changes:
  - find: "original text in base template"
    replace: "proposed replacement"
    file: "content.md"
    rationale: "Why this change helps"
additional_notes: "..."
queued_at: "2026-03-13T..."
source_file: "/path/to/consultation-1.md"
```

## Review workflow

1. Read the proposal — check `root_cause` and `confidence`
2. Verify `proposed_changes` against the actual base template in `claude_extensions/phases/gemini/`
3. If approved: apply the FIND/REPLACE manually to the base template, then delete the queue file
4. If rejected: delete the queue file (optionally note why in the GH issue)

## Important

- Changes here affect ALL future module builds — review carefully
- The `source_file` field points to the full consultation result for context
- Multiple proposals may target the same template — check for conflicts
