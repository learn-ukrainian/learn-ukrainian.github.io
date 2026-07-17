# Path-filter gate coverage — a gate whose trigger does not cover its inputs

## Symptom

PR #5350 (CI-only changes: paths-filter retry wrapper) failed the `Lesson Schema Drift`
gate — regenerating `docs/lesson-schema.yaml` changed `components_sha256`
(b511c102… → b88d64e2…) although the PR touched nothing the schema is generated from.
The drift was pre-existing on main: the latest main CI run (29564685615) showed
`Lesson Schema Drift: skipped`, so main's green never proved the schema was fresh.

## Root cause

The drift gate runs only when the `lesson_schema` path filter matches, but the filter
did not include the generator's actual inputs: `site/src/components/**` (rglob'd and
hashed as `components_sha256`), `scripts/pipeline/config_tables.py`
(`config_tables_sha256`), and `scripts/build/lesson_schema_extractor.mjs` (shapes the
extraction). Component-changing PRs (#5115, #5164, #5194, #5336 — everything since the
last regeneration in #5139) merged without ever running the gate; drift accumulated
silently; the gate finally fired — and turned red — on the first unrelated PR that
touched `ci.yml`.

Fourth manifestation of the filter-gap class: #3873 (curriculum deletion skipped
pytest), #4888 (data-only lexicon PR skipped pytest), #4936 (atlas manifest publish
skipped pytest). The prior three gated *pytest*; this one gated a *drift check*. The
shared shape: a conditional gate whose trigger-path set is written by hand and never
derived from — or checked against — the gate's real input set.

## Prevention

1. `lesson_schema` filter now covers all generator inputs (ci.yml, #5351).
2. Load-bearing test `tests/test_lesson_schema_filter_coverage.py` derives the input
   set from `generate_lesson_schema.py` itself and fails when any input path is not
   matched by the filter globs — adding a generator input without widening the filter
   breaks pytest.
3. Same test also recomputes the input fingerprints and compares them with the
   committed `generated_from` block, so scripts-touching PRs surface staleness even
   before the drift gate runs.
4. Review rule for ANY conditional CI gate: enumerate the gated check's inputs and
   diff them against the trigger filter — by test where possible, by review otherwise.
