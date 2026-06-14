# Dispatch: pipeline replay-mode regression suite (#1905)

Build a deterministic, **LLM-free** regression suite that replays recorded pipeline inputs through the gates,
telemetry summarizers, and adapter parsers — so the bug class that "only surfaces after a 12-30 min build +
LLM quota" becomes a <1s unit test. Read it: `gh issue view 1905` (lists 4 motivating bugs).

## Goal
A `tests/replay/` suite + small fixture corpus where each fixture is a recorded input (a tool-call result,
an activity-schema blob, a writer-telemetry record, a codex rollout snippet) and the test asserts the
deterministic component handles it correctly — NO network, NO LLM, NO real build.

## Cover the 4 documented bug classes as regression fixtures (each must FAIL pre-fix, PASS post-fix logic)
1. **`_prepare_query` OSError on long Cyrillic query** (`scripts/build/pilot_uk_lesson.py`) — fixture: an
   over-long Cyrillic query; assert no OSError / graceful handling. (PR #1902 added one test — extend/relocate.)
2. **`_vesum_gate` flags MC distractors as invented** — fixture: activity schema `options: [{text, correct:false}]`;
   assert `correct:false` distractors are NOT sent to VESUM verify.
3. **Writer telemetry `search_text` summary empty** — fixture: a `search_text` tool result; assert
   `_summarize_generic_tool_result` produces matchable items for the `textbook_grounding` gate.
4. **Codex rollout-matcher fail-fast** (#1903) — fixture: a rollout snippet; assert the matcher pairs it correctly.

## Design constraints
- Fixtures are small, committed, redacted JSON/text under `tests/replay/fixtures/`. No `data/*.db`, no
  `batch_state/`, no secrets.
- Pure-function / parser-level assertions. If a component needs a DB, stub/monkeypatch it — the suite must run
  on CI (which has NO `vesum.db`/`sources.db`).
- Make it EXTENSIBLE: a clear pattern so the next gate/adapter bug gets a fixture, not a full build.

## Numbered steps
1. `cd /Users/krisztiankoos/projects/learn-ukrainian && git fetch origin` (`--worktree` from origin/main).
2. Build `tests/replay/` + fixtures + the 4 regression tests. Reuse existing test patterns
   (`tests/test_linear_pipeline_telemetry.py`, `tests/test_vesum_*`).
3. `cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python -m pytest tests/replay -q` → paste summary (all green, runs with no DB/network).
4. `cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/ruff check tests/ scripts/ -q` → paste final line.
5. Commit `test(replay): LLM-free pipeline regression suite — 4 gate/telemetry/adapter bug fixtures (#1905)`.
6. `git push -u origin <branch>`; `gh pr create` referencing #1905 + #1865. NO auto-merge.

## Evidence (#M-4 — command + cwd + raw output per claim)
- pytest summary for `tests/replay` (raw); proof each fixture exercises a real component (cite the function
  under test per fixture); ruff final line; `git log -1 --oneline`; `gh pr view --json url`.
