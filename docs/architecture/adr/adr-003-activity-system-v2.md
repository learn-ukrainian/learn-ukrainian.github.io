# ADR-003: Activity system v2 — YAML → JSX renderers

**Status**: Accepted
**Date**: 2026-02 (implemented) / 2026-04-11 (recorded)
**Related**: `docs/architecture/activity-system-v2.md`, `scripts/build/activity_schema.py`, `scripts/build/activity_validator.py`, `scripts/build/activity_repair.py`, `starlight/src/components/activities/`, #1185

## Context

Activity v1 was a DSL embedded in markdown: inline shortcodes like `{{fill: Я ____ в школу | answer: йду}}` that the MDX pipeline parsed into React components at render time. Three problems surfaced as we scaled beyond A1:

1. **The DSL parser couldn't handle schema variance.** Each activity type (fill-in, quiz, match-up, group-sort, error-correction, true-false, reading, critical-analysis, etc.) wanted different fields. The DSL forced a lowest-common-denominator grammar that made richer activity types impossible.
2. **Writer LLMs couldn't produce valid DSL reliably.** The DSL had escape rules for `|`, `:`, and `}` that Gemini got wrong ~15% of the time. YAML is a strict grammar that both LLMs produce reliably.
3. **The DSL was invisible to tooling.** We couldn't lint, audit, or repair DSL without a custom parser. Each new check meant another regex.

We needed first-class activity objects, not markdown macros.

## Decision

Activities live in a separate `curriculum/l2-uk-en/{level}/activities/{slug}.yaml` file with a schema-enforced structure:

```yaml
# curriculum/l2-uk-en/a2/activities/genitive-intro.yaml
inline:
  - id: q1
    type: quiz
    title: Перевірка розуміння
    items:
      - question: "Я йду з ___ (школа)."
        options: ["школи", "школу", "школою", "школі"]
        correct: 0
workbook:
  - id: f1
    type: fill-in
    title: Генітив однини
    items:
      - sentence: "Немає ___ (час)."
        answer: "часу"
```

Build pipeline:

1. **`step_activities`** calls the writer to generate the YAML from the skeleton's `INJECT_ACTIVITY` markers + the plan's `activity_hints`.
2. **`step_repair`** runs `scripts/build/activity_repair.py` to deterministically fix common issues (parenthetical hints, duplicate options, misplaced types, etc.). No LLM.
3. **`step_verify_exercises`** runs `scripts/build/activity_validator.py` against the JSON schema in `scripts/build/activity_schema.py` and the level-specific allowlists in `scripts/pipeline/config_tables.py`.
4. **`step_publish`** invokes renderer functions in `scripts/build/generate_mdx/activity_renderer.py` that emit JSX `<Quiz>`, `<FillIn>`, `<MatchUp>`, etc. components into the Starlight MDX output.

Each activity type gets its own React component under `starlight/src/components/activities/`. Adding a new activity type means: (1) extend the schema, (2) add a renderer function, (3) add a React component. No DSL grammar changes.

## Alternatives considered

- **Keep the DSL, add escape rules for hard cases** → rejected: each new activity type required 2-3 escape-rule patches. The complexity grew super-linearly with activity types.
- **JSON instead of YAML** → rejected: YAML is more human-writable (the writer LLM produces it more reliably) and our tooling already depends on YAML for plans and meta files.
- **Inline the activity JSX directly in module markdown** (skip the intermediate file) → rejected: (a) the writer LLM cannot produce valid JSX reliably, (b) we'd lose the audit/repair pipeline, (c) schema validation would become per-file AST walking instead of one YAML parse.
- **External activity authoring tool** → rejected: the point is that the writer LLM generates the activities. Adding a human authoring step defeats the autonomy goal.

## Consequences

**Positive**:
- The repair phase catches most writer errors deterministically. `activity_repair.py` handles 7 classes of fixable issues (parenthetical hints, duplicate options, placement violations, disallowed types, answer-not-in-options, malformed true-false, level-forbidden types).
- Validation catches the rest at build time, before publish. The audit gate blocks shipping of invalid activities.
- New activity types ship without touching any pipeline code except a renderer function. The seminar-activity-types expansion in #1148 added 12 new types with zero pipeline changes.
- Writer LLMs produce valid YAML ~99% of the time. The remaining 1% is caught by repair or verify; no manual intervention.

**Negative / risks**:
- Three places to keep in sync (schema, renderer, React component) when adding a type. Tolerable — adding a type is rare and the checklist is short.
- YAML parsing is strict about indentation, so a single space error by the writer can corrupt an activity. Mitigated by `activity_repair.py` and the writer prompt explicitly showing indentation examples.
- The schema gate is the quality ceiling: if the schema doesn't catch a bug, the renderer will silently produce broken UI. We've had two incidents like this; both were fixed by tightening the schema (not the renderer).

**Neutral / follow-ups**:
- The full list of supported types and their schemas lives in `scripts/build/activity_schema.py`. Treat that file as the source of truth when adding a new type — the prompt templates and the React components should reference it.

## Verification

- `tests/test_activity_schema.py` — schema validation tests
- `tests/test_activity_repair.py` — repair fixtures for each fix class (17 tests passing as of 2026-04-11)
- `scripts/build/activity_validator.py` — runs as part of `step_verify_exercises` in every build
- Audit gate: the `activities` gate must pass for a module to publish
