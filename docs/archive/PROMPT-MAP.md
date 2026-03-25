# Prompt Map — Phase → Template → Model

All prompt templates live in `claude_extensions/phases/gemini/`.
Retired v3/v4 templates are in `claude_extensions/phases/gemini/_retired/`.

## Pipeline v5 Phase → Template Mapping

### Research

| Tier | Template | Model |
|------|----------|-------|
| Beginner (A1-A2) | `beginner-research.md` | Gemini |
| Core (B1+) | `research-core.md` | Gemini |
| Seminar (HIST, BIO, etc.) | `research-seminar.md` | Gemini |
| Pro | `research-pro.md` | Gemini |
| Meta-only rebuild | `research-meta-only.md` | Gemini |

### Content

| Tier | Template | Model |
|------|----------|-------|
| Beginner (single-call) | `beginner-full.md` / `beginner-full-rag.md` | Gemini |
| Beginner (separate) | `beginner-content.md` | Gemini |
| Core (B1+) | `core-content.md` | Gemini |
| Seminar | `content.md` | Gemini |

### Activities

| Tier | Template | Model |
|------|----------|-------|
| Beginner | `beginner-activities.md` | Gemini |
| Core (B1+) | `core-activities.md` | Gemini |
| Seminar | `activities.md` | Gemini |

### Review (Claude)

| Step | Template | Model |
|------|----------|-------|
| Structured review | `review-structured.md` | Claude |
| Evidence review (fallback) | `review-evidence.md` | Claude |
| Output format | `review-output-format.md` | (injected) |
| Repair | `review-repair.md` | Claude |

### Gemini Review Loop

| Step | Template | Model |
|------|----------|-------|
| Pass 1 | `gemini-review-pass1.md` | Gemini |
| Pass 2 | `gemini-review-pass2.md` | Gemini |
| Fix iteration | `gemini-review-fix.md` | Gemini |

### Shared (injected into other templates)

| File | Purpose |
|------|---------|
| `_shared-activity-rules.md` | Activity YAML schema rules |
| `_shared-content-rules.md` | Content writing standards |
| `_shared-self-audit.md` | Self-audit checklist |

### Utility (not part of main pipeline)

| File | Purpose |
|------|---------|
| `plan-enrichment.md` | Plan vocabulary enrichment |
| `resource-request.md` | Resource discovery requests |
| `help-response.md` | Help/FAQ response template |
| `direct-enrich.md` | L2-UK-Direct track enrichment |

## Three-Tier System

```
Beginner (A1-A2, B1 M1-5)
  └── Single-call mode: research + content + activities in one Gemini call
  └── Simpler templates, decodability constraints, limited vocabulary

Core (B1+ except seminars)
  └── Full pipeline: separate research, content, activities, review
  └── Complex grammar, aspect system, immersion targets

Seminar (HIST, BIO, ISTORIO, LIT, OES, RUTH)
  └── Content-heavy: 5000 word targets, primary sources
  └── Cultural/historical depth, no grammar progression
```

## Batch System Templates

Used by `batch_gemini_config.py` and Gemini `otaman`/`hetman` skills:

| File | Purpose |
|------|---------|
| `research-seminar-v0.md` | Batch research for seminar tracks |
| `review-legacy.md` | Batch review phase |
| `fix.md` | Batch fix iteration |
| `fix-content.md` | Batch fix (content only) |
| `fix-activities.md` | Batch fix (activities only) |

## Orchestration Artifacts

Files written to `curriculum/.../orchestration/{slug}/` during build:

| Phase | Artifacts |
|-------|-----------|
| Research | `research-prompt.md`, `research-output.md`, `research-gemini-session.json` |
| Content | `content-prompt.md`, `content-output-{N}.md`, `content-attempt-{N}-gemini-session.json` |
| Activities | `activities-prompt.md`, `activities-output.yaml`, `activities-gemini-session.json` |
| Validate | `validate-fix{N}-prompt.md`, `validate-fix{N}-raw.md`, `validate-fix{N}-gemini-session.json` |
| Review | `final-review.md` |

## Retired Templates (v3/v4)

All in `_retired/`. Do not reference in new code.

| File | Era | Replaced By |
|------|-----|-------------|
| `phase-0-research-core.md` | v3 | `research-core.md` |
| `phase-0-5-enrich-plan.md` | v3 | `plan-enrichment.md` |
| `phase-1-meta.md` | v4 | (meta generation removed) |
| `phase-2-content-section.md` | v4 | `core-content.md` |
| `phase-2-summary.md` | v4 | (removed) |
| `phase-6-review.md` | v4 | `gemini-review-pass2.md` |
| `phase-7-final-review.md` | v4 | (removed) |
| `phase-D-review-fix.md` | v4 | `review-repair.md` |

## Cross-Agent Contract

| Direction | What | Format |
|-----------|------|--------|
| Claude → Gemini | Review findings | Markdown in `review-structured.md` output |
| Gemini → Claude | Content + activities | `===TAG===` delimited blocks extracted by `gemini_output.py` |
| Claude → Gemini | Fix instructions | Injected via `{EXTRACTED_FIX_PLAN}` and `{INJECTED_AUDIT_FAILURES}` |
| Gemini → Claude | Fixed content | Same `===TAG===` format |

## Linting

```bash
# Lint all prompt templates (blocks deploy on errors)
.venv/bin/python scripts/lint/lint_prompts.py

# Also check curriculum research files
.venv/bin/python scripts/lint/lint_prompts.py --curriculum

# Auto-fix persona contamination
.venv/bin/python scripts/lint/lint_prompts.py --fix
```

CI runs `lint_prompts.py` on every push to `claude_extensions/phases/` or `gemini_extensions/skills/`.
