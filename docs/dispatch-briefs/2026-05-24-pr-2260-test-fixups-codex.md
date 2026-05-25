# PR #2260 fix-up — restore literal strings the structural tests check

**Date**: 2026-05-24
**Agent**: codex
**Mode**: danger
**Effort**: medium
**Wall budget**: 30 min

## Why

PR #2260 (Option B writer-prompt fixes) has 7 failing tests on CI because compression removed literal strings that structural tests assert. Known failure example:

```
tests/test_linear_pipeline_wiki_coverage.py::test_writer_prompt_places_manifest_before_module_context
    assert "Full Wiki Context (source of truth for citations)" in rendered
```

Plus 6 others in `tests/test_prompt_cot_tier1_scaffolding.py` (variants of `test_writer_prompt_has_tier1_discipline` and `test_writer_prompt_mandates_tool_call_match` across a1/a2/b1).

The semantic intent of Option B (chunk_id-first protocol, plan-references-only citation, knowledge-packet anchors not citation candidates) MUST be preserved. The fix-up is purely about restoring removed structural-marker strings.

## Read these first

1. `tests/test_linear_pipeline_wiki_coverage.py::test_writer_prompt_places_manifest_before_module_context` (around line 25)
2. `tests/test_prompt_cot_tier1_scaffolding.py::test_writer_prompt_has_tier1_discipline` (around line 124)
3. `tests/test_prompt_cot_tier1_scaffolding.py::test_writer_prompt_mandates_tool_call_match` (around line 185)
4. Current state of `scripts/build/phases/linear-write.md` on branch `fix/writer-prompt-option-b-fixes-2026-05-24`

## What to do

1. Run the 3 failing test families locally on the branch to get the FULL list of asserted strings:
   ```
   .venv/bin/pytest tests/test_linear_pipeline_wiki_coverage.py::test_writer_prompt_places_manifest_before_module_context tests/test_prompt_cot_tier1_scaffolding.py -v 2>&1 | tail -60
   ```
2. For each failing assertion, identify the literal string the test expects.
3. Restore each missing string into `linear-write.md` in a location consistent with the test's intent (e.g., the "manifest before module context" test checks ORDER — restore the marker text in the same position it was originally).
4. **DO NOT undo the 3 Option B fixes** — citation-authority section, resources.yaml schema tightening, chunk_id-first protocol. Those are the load-bearing content of this PR. The fix-up only restores STRUCTURAL MARKERS that compression touched.
5. Re-run prompt size check: `.venv/bin/python scripts/audit/check_writer_prompt_size.py 2>&1 | tail -3`. Must stay under 130KB ceiling. If restoring the strings pushes over, compress something ELSE (a paragraph of background/context, NOT the Option B fixes or structural markers).
6. Run the full prompt test suite:
   ```
   .venv/bin/pytest tests/test_linear_pipeline_wiki_coverage.py tests/test_prompt_cot_tier1_scaffolding.py tests/build/test_writer_pre_emit_checklist.py tests/build/test_linear_pipeline.py -v 2>&1 | tail -20
   ```
   All must pass.

## REQUIRED steps

1. Use the EXISTING worktree at `.worktrees/dispatch/codex/writer-prompt-option-b-fixes-2026-05-24` (already on branch `fix/writer-prompt-option-b-fixes-2026-05-24`). DO NOT create a new branch — push fixup commit onto the same PR.
2. `cd .worktrees/dispatch/codex/writer-prompt-option-b-fixes-2026-05-24`
3. Read tests, identify missing strings, restore them.
4. One commit: `fix(writer-prompt): restore structural markers compressed by Option B (PR #2260 CI fix)`.
5. `git push` (NOT `--set-upstream` — branch already pushed).
6. Verify CI: `gh pr checks 2260 --watch --interval 15`. Report final state.

## Verifiable claims

| Claim | Evidence |
|---|---|
| "All 7 failing tests now pass" | `.venv/bin/pytest <test list> -v` summary raw |
| "Prompt size still under 130KB" | `check_writer_prompt_size.py` raw |
| "Option B fixes preserved" | `git diff origin/main..HEAD -- scripts/build/phases/linear-write.md` showing the 3 fixes still present (citation-authority section, schema tightening, chunk_id-first protocol) |
| "CI green on PR #2260" | `gh pr checks 2260 --json bucket` showing pass on Test (pytest) |

## Anti-fabrication (#M-4)

Tool-back every claim. The literal strings that tests check for come from the test code, not from memory.
