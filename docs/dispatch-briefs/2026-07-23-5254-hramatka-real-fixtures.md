# Brief: Issue #5254 - Calibrate hramatka QG gate against REAL known-bad lessons (fixtures)

## Goal
Calibrate `scripts/audit/hramatka_qg_rules.py` against REAL known-bad lesson fixtures (real generated defects, not just synthetic planted-fault fixtures).

## Background
Currently `scripts/audit/hramatka_qg_rules.py` is calibrated against synthetic planted-fault fixtures. Issue #5254 calls for adding real generated defect fixtures (Russianism/calque, invalid distractor, placeholder answer key, broken activity, over-level task word) to ensure full load-bearing coverage.

## Requirements
1. In `tests/test_hramatka_qg_rules.py` (or dedicated fixture file under `tests/fixtures/hramatka/`):
   - Add real known-bad lesson exemplars representing:
     - Real generated Russianism / calque defect
     - Invalid distractor defect
     - Placeholder answer key defect
     - Structural activity defect
     - Over-level task vocabulary defect
   - Assert that `run_hramatka_qg()` catches every real exemplar.
   - If any real exemplar slips through existing rules in `scripts/audit/hramatka_qg_rules.py` -> fix/extend the corresponding rule in `scripts/audit/hramatka_qg_rules.py` so that it is caught.

2. Verify:
   - Run `pytest tests/test_hramatka_qg_rules.py` and ensure all tests pass.
   - Run `ruff check scripts/audit/hramatka_qg_rules.py tests/test_hramatka_qg_rules.py`.

3. Commit & PR:
   - Commit message: `test(hramatka): calibrate QG gate against real known-bad lesson fixtures (#5254)`
   - Trailer: `X-Agent: sonnet/5254-hramatka-real-fixtures` (or whichever agent/lane is assigned)
   - Create PR referencing #5254 and #4542.
   - DO NOT auto-merge or self-approve.

## Provenance
Recovered from a misplaced runtime copy at `.claude/dispatch-briefs/dispatch-5254.md` (gitignored
deploy target — never a durable location; broke `npm run agents:deploy` orphan-path parity) and
archived here at its canonical, git-tracked location per `scripts/audit/lint_dispatch_brief.py`'s
`BRIEFS_GLOB`. Executed as PR #5691.
