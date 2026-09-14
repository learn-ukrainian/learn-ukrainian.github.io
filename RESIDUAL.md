# Curriculum upgrade Phase 1 residuals (#7994)

## Blocking: lesson allocation of the existing immersion exposure floor

Owner: driver Grok, with operator/designated-advisor approval for the pedagogical
decision. No threshold or gate disposition was changed in this PR.

The Phase 0 checker does not include an immersion gate. Current V7
`_l2_exposure_floor_gate` derives a module-level minimum of 13 Ukrainian dialogue
lines for the pinned original plan. The gold lessons contain 5, 0 and 0 lines under
that counter. Applying the current gate separately therefore rejects all lessons,
although original preservation, activity counts, vocabulary union and render
coverage pass. The unchanged current long-Ukrainian ceiling and component density
checks also run.

`tests/build/test_lesson_gates.py::test_gold_assembler_coverage_and_explicit_immersion_residual`
asserts the exact blocking exposure results. Decide how the existing module-level
exposure obligation applies to split lesson units; then implement and test the
approved allocation against the independent fixture. Until then the pipeline fails
closed and this PR stays draft. The machinery tests passing do not certify gold as
shippable and do not close #7994 Phase 1.

## Validation awaiting the site environment and driver

Full Astro/Playwright verification on actual lesson pages and exact-head cross-family
PR review remain required. The isolated real-component Astro build and generated-page browser checks pass;
these and Node island checks remain narrower than the complete deployed site.
No live writer, deployment, merge, or production lesson generation was run in this PR.

## Broader checkout validation limitations

Owner: driver/CI. The expanded existing regression run reported 290 passed,
3 failed and 1 skipped. All three failures require `wiki/pedagogy/a1/my-morning`,
which this dispatch explicitly excludes through sparse checkout. The existing
optional historical writer replay skips because its old build worktree is absent.
No tests were disabled or changed to conceal these results. Re-run in the full CI
checkout; a new dispatch with wiki included is required for that local validation.

Repository-wide Ruff reports 12 import-order findings in 11 untouched files;
all 12 were reproduced by checking their HEAD content. Ruff on every changed/new
Python file passes. No linter configuration was changed. CI must distinguish its
full-checkout result from this local baseline.
