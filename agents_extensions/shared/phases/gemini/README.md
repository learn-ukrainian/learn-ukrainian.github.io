# Gemini Phase Templates

Phase prompt templates for the `/orchestrate-rebuild` workflow where Claude orchestrates and Gemini executes.

## How It Works

1. Claude reads a template from this directory
2. Claude fills placeholders with module-specific data (file paths, targets, etc.)
3. Claude writes the assembled prompt to `curriculum/l2-uk-en/{track}/orchestration/{slug}/phase-{N}-prompt.md`
4. Claude sends Gemini a SHORT broker message: "Read and execute prompt at {path}"
5. Gemini reads the prompt file from shared filesystem, executes, returns text output
6. Claude captures output, validates, writes to disk

## Placeholder Convention

Templates use `{PLACEHOLDER}` syntax. Claude replaces these before writing the prompt file.

| Placeholder | Source |
|-------------|--------|
| `{PLAN_PATH}` | `curriculum/l2-uk-en/plans/{track}/{slug}.yaml` |
| `{RESEARCH_PATH}` | `curriculum/l2-uk-en/{track}/research/{slug}-research.md` |
| `{CONTENT_PATH}` | `curriculum/l2-uk-en/{track}/{slug}.md` |
| `{ACTIVITIES_PATH}` | `curriculum/l2-uk-en/{track}/activities/{slug}.yaml` |
| `{VOCAB_PATH}` | `curriculum/l2-uk-en/{track}/vocabulary/{slug}.yaml` |
| `{QUICK_REF_PATH}` | `agents_extensions/shared/quick-ref/{LEVEL}.md` |
| `{SCHEMA_PATH}` | `schemas/activities-{track}.schema.json` |
| `{WORD_TARGET}` | Historical, non-authoritative length metadata from level config (`scripts/audit/config.py`) |
| `{SLUG}` | Module slug |
| `{TRACK}` | Track identifier |

## Registry and retained templates

The lifecycle prompt registry is
`agents_extensions/shared/prompt-contracts/registry.v1.yaml`; its manifests
select fragments under `prompt-contracts/`, not this directory. Legacy phase
callers still use templates here, so registry absence alone is not deletion
proof. The unused `v6-skeleton.md` and `v6-activities.md` copies were removed in
#7686. `v6-write.md` and `v6-review.md` are retirement pointers for existing
documentation links; build-owned templates remain under `scripts/build/phases/`.
The V6 per-dimension review prompts (`scripts/build/phases/v6-review/`) were removed in REMOVE-UNNEEDED-1107; see git history.
The retired v3/v4 template archive was removed in REMOVE-UNNEEDED-1107; see git history.
Unreferenced legacy prompts (the `gemini-review-*` and `phase-gemini-review-*` sets, `phase-fix-content.md`, `phase-fix-activities.md`, `plan-enrichment.md` and others) were removed in the cleanup that produced the table below; see git history.

## Files

Every file here must be loaded or linked by something live; a file nothing
references is deleted (census at `6a75676ebe7`, PR body of the cleanup). The
"Used by" column names that reference.

| Template | Used by |
|----------|---------|
| `_shared-quality-dimensions.md`, `_shared-quality-dimensions-seminar.md`, `_shared-preflight.md`, `_shared-activity-rules.md`, `_shared-self-audit.md` | `scripts/pipeline/core.py` placeholder injection (`_read_phase_file`) |
| `_shared-content-rules-beginner.md`, `_shared-content-rules-core.md` | `scripts/pipeline/core.py`, name built as `_shared-content-rules-{tier}.md` |
| `review-output-format.md` | `scripts/pipeline/core.py` (`D1_OUTPUT_FORMAT`) |
| `beginner-full-rag.md`, `beginner-checkpoint.md`, `core-content.md`, `core-checkpoint.md` | `scripts/pipeline/core.py` `_get_content_template` |
| `beginner-activities.md`, `beginner-checkpoint-activities.md`, `core-activities.md`, `core-checkpoint-activities.md` | `scripts/pipeline/core.py` `_get_activities_template`, which currently has no caller beyond its re-export in `scripts/pipeline_lib.py` |
| `content.md`, `activities.md`, `fix.md`, `fix-content.md`, `fix-activities.md`, `phase-5-review.md`, `research-seminar-v0.md`, `research-core.md` | `scripts/batch/batch_gemini_config.py` template tables |
| `phase-fix.md`, `phase-5-review.md` | `scripts/batch/batch_fix_review.py` |
| `direct-enrich.md` | `scripts/build/build_module_direct.py` |
| `phase-2-content.md` | usage example in `scripts/generate_mdx/fill_template.py` |
| `phase-A-seminar.md`, `phase-A-meta-only.md` | linked from `docs/best-practices/context-engineering.md` |
| `phase-D1-structured-review.md`, `review-structured.md` | named as reviewer-rubric files to edit in `docs/folk-epic/seminar-quality-gate-design.md` |
| `v6-write.md`, `v6-review.md` | retirement pointers for documentation links (`docs/SCRIPTS.md`) |

## Delimiter Convention

All phase templates use `===TAG_START===` / `===TAG_END===` delimiters to wrap structured output. Content outside delimiters (thinking tokens, commentary) is **automatically discarded** by `scripts/gemini_output.py`.

| Phase | Tags | Content Type |
|-------|------|-------------|
| 0 (Research) | `RESEARCH` | Markdown |
| 1 (Meta) | `META_OUTLINE` | YAML |
| 2 (Content) | `CONTENT` | Markdown |
| 3 (Activities) | `ACTIVITIES`, `VOCABULARY` | YAML |
| 5 (Review) | `REVIEW` | Markdown |
| Fix | `CONTENT`, `ACTIVITIES`, `VOCABULARY`, `CHANGES` | Mixed |

**Extraction utility:** `scripts/gemini_output.py` — pure functions, no I/O:
- `extract_delimited(text, tag)` — extract content between delimiters
- `extract_yaml(text, tag)` — extract + parse YAML
- `validate_output(text, expected_tags)` — check for complete/missing/truncated tags
- `PHASE_TAGS` — phase-to-tag mapping constant

## Adding New Templates

1. Create `phase-{N}-{name}.md` in this directory
2. Use `{PLACEHOLDER}` syntax for module-specific data
3. Include explicit output format with delimiters
4. Add the delimiter enforcement callout: `> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.`
5. Add anti-pattern warnings relevant to the phase
6. Update the orchestrate-rebuild.md skill to reference the new template
