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
| `{META_PATH}` | `curriculum/l2-uk-en/{track}/meta/{slug}.yaml` |
| `{RESEARCH_PATH}` | `curriculum/l2-uk-en/{track}/research/{slug}-research.md` |
| `{CONTENT_PATH}` | `curriculum/l2-uk-en/{track}/{slug}.md` |
| `{ACTIVITIES_PATH}` | `curriculum/l2-uk-en/{track}/activities/{slug}.yaml` |
| `{VOCAB_PATH}` | `curriculum/l2-uk-en/{track}/vocabulary/{slug}.yaml` |
| `{QUICK_REF_PATH}` | `claude_extensions/quick-ref/{LEVEL}.md` |
| `{SCHEMA_PATH}` | `schemas/activities-{track}.schema.json` |
| `{WORD_TARGET}` | From plan/meta YAML |
| `{SLUG}` | Module slug |
| `{TRACK}` | Track identifier |

## Files

| Template | Phase | Purpose |
|----------|-------|---------|
| `phase-0-research-seminar.md` | 0 | Deep research for seminar tracks |
| `phase-0-research-core.md` | 0 | Lightweight research for core tracks |
| `phase-1-meta.md` | 1 | Refine content_outline with word allocations |
| `phase-2-content.md` | 2 | Write lesson prose (1.5x overshoot) |
| `phase-3-activities.md` | 3 | Generate activities + vocabulary YAML |
| `phase-5-review.md` | 5 | Critical 14-dimension deep review |
| `phase-fix.md` | Fix | Apply review fix plan to reach 9.0+ |
| `help-response.md` | — | Template for Claude's NEEDS_HELP responses |

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
