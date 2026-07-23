# Brief: Issue #5187 - Lesson-artifact target adapter for shadow llm_qg capture contract

## Goal
Implement the lesson-artifact target adapter for `hramatka` teacher-lesson artifacts so they can enter the `qg_shadow_run` / `qg_workflow` capture contract cleanly.

## Background
Currently `qg_workflow.ReviewTarget` assumes standard module directories (containing `module.md`, `activities.yaml`, `vocabulary.yaml`, `resources.yaml`). `hramatka` teacher-lesson artifacts have a different shape (teacher lesson JSON/YAML schemas).
Issue #5187 calls for a target adapter for `hramatka` teacher-lesson artifacts before they enter `qg_shadow_run`.

## Requirements
1. Create `scripts/audit/hramatka_target_adapter.py`:
   - Learner-facing field selection (selects user-facing text from hramatka lesson structure for evaluation, filtering out non-learner metadata).
   - Canonical serialization + SHA256 content hash generator.
   - Level/policy mapping (map hramatka level metadata to standard CEFR level/policy).
   - Source / teacher-note EXCLUSION (filters out teacher internal prompts, source references, private annotations).
   - Privacy/retention rules enforcement (strips user identifiers, private tokens, raw infrastructure secrets).
   - Provide an adapter method `convert_hramatka_lesson_to_review_target(...)` or `HramatkaLessonAdapter` class that produces or wraps a `qg_workflow.ReviewTarget` or schema compatible with `qg_shadow_run.py`.

2. Create comprehensive pytest test suite in `tests/test_hramatka_target_adapter.py`:
   - Test field selection & exclusions (teacher notes excluded, learner fields included).
   - Test canonical serialization & content hashing.
   - Test level/policy mapping.
   - Test privacy/retention sanitization.
   - Test integration/conversion to `ReviewTarget` shape.

3. Rules & Constraints:
   - Python 3.12 compatible.
   - Follow all repo rules: use `.venv/bin/python`, no modification to linter configs or `.python-version`.
   - Run `pytest tests/test_hramatka_target_adapter.py` and `ruff check scripts/audit/hramatka_target_adapter.py tests/test_hramatka_target_adapter.py`.
   - Commit with conventional commit message: `feat(harness): implement hramatka target adapter for llm_qg shadow capture (#5187)`
   - Trailer: `X-Agent: codex/5187-hramatka-target-adapter`
   - Create PR referencing #5187 and #4542.
   - DO NOT auto-merge or self-approve.

## Provenance
Recovered from a misplaced runtime copy at `.claude/dispatch-briefs/dispatch-5187.md` (gitignored
deploy target — never a durable location; broke `npm run agents:deploy` orphan-path parity) and
archived here at its canonical, git-tracked location per `scripts/audit/lint_dispatch_brief.py`'s
`BRIEFS_GLOB`. Executed as PR #5690 (merged).
