# Dispatch Brief — #1969 multimedia search pre-emit checklist

**Agent:** gemini (default for routine docs-near-code / prompt edits, unmetered)
**Effort:** medium
**Mode:** danger (commit + push + open PR)
**Worktree:** mandatory (PR #1952 invariant)
**Closes:** #1969
**Branch name:** `gemini/1969-multimedia-preemit-checklist`

## Context

m20 build #4 had `resources_search_attempted=0` — the writer made zero calls
to `mcp__sources__query_wikipedia` / `search_external` / `search_images`,
even though the multimedia obligation is in the prompt at lines 200–241. The
multimedia mandate got crowded out by the strong `MUST` / `mandatory` / `hard
fail` language in the #1964 textbook-grounding contract directives at lines
75–100.

Full diagnosis in issue #1969 (read it first). Recommended fix is **Option
A**: add a pre-emit verification checklist near the end of the writer prompt
that explicitly enumerates the four mandatory tool-call obligations. Low
risk, ~25 LOC, addresses the attention-budget issue without restructuring
the existing mandate sections.

## The edit

File: `scripts/build/phases/linear-write.md` (currently 387 lines).

Insert the checklist **immediately before** the `## HARD STOP RULE` section
at the bottom of the file (currently begins at line 375 — find it by
searching for `## HARD STOP RULE`). The `HARD STOP RULE` block MUST remain
the very last instruction in the prompt; the checklist goes ABOVE it.

Content to insert (copy-paste exactly, including the surrounding blank
lines):

```
## Pre-emit verification (run BEFORE you write any artifact)

Before emitting the four fenced blocks and the `<end_gate>` block, confirm
you have made AT LEAST one of each of the following tool calls during this
turn. If any line below is FALSE, make the call now before emitting.

1. `mcp__sources__search_text` — at least one call per `plan_references`
   textbook entry (textbook grounding obligation; gate
   `textbook_grounding`).
2. `mcp__sources__query_wikipedia` OR `mcp__sources__search_external` OR
   `mcp__sources__search_images` — at least one call (multimedia search
   obligation; gate `resources_search_attempted`). Honest "no result"
   counts — the attempt is what the gate counts.
3. `mcp__sources__verify_words` (or `verify_word` / `verify_lemma`) — at
   least one call on novel Ukrainian forms before writing them
   (verification obligation; reviewer evidence requirement).
4. `mcp__sources__search_style_guide` — at least one call on a Russianism
   or paronym candidate from the topic vocabulary (heritage-defense
   obligation; reviewer evidence requirement).

This checklist is not a substitute for the per-mandate instructions above;
it is a final cross-check that no mandate was forgotten under the attention
budget of the early-prompt contract directives.

```

(Trailing blank line is intentional; ensure exactly one blank line before
the `## HARD STOP RULE` header that follows.)

## The test

Create `tests/test_writer_prompt_preemit_checklist.py` mirroring the
existing pattern from `tests/test_writer_prompt_structured_cot.py`:

```python
from __future__ import annotations

from scripts.build import linear_pipeline

WRITER_TEMPLATE = (
    linear_pipeline.PROJECT_ROOT / "scripts/build/phases/linear-write.md"
)

CHECKLIST_HEADER = "## Pre-emit verification (run BEFORE you write any artifact)"

REQUIRED_TOOL_MENTIONS = (
    "mcp__sources__search_text",
    "mcp__sources__query_wikipedia",
    "mcp__sources__search_external",
    "mcp__sources__search_images",
    "mcp__sources__verify_words",
    "mcp__sources__search_style_guide",
)


def _writer_template() -> str:
    return WRITER_TEMPLATE.read_text(encoding="utf-8")


def test_writer_prompt_has_preemit_checklist() -> None:
    prompt = _writer_template()
    assert CHECKLIST_HEADER in prompt, (
        "Pre-emit checklist header missing from writer prompt — see #1969."
    )


def test_writer_prompt_preemit_lists_required_tool_calls() -> None:
    prompt = _writer_template()
    # Find the checklist section, assert each required tool is mentioned
    # inside it (not just somewhere in the file).
    idx = prompt.find(CHECKLIST_HEADER)
    assert idx >= 0
    hard_stop_idx = prompt.find("## HARD STOP RULE", idx)
    assert hard_stop_idx > idx, "HARD STOP RULE must follow the checklist"
    checklist_body = prompt[idx:hard_stop_idx]
    for tool in REQUIRED_TOOL_MENTIONS:
        assert tool in checklist_body, f"{tool} missing from pre-emit checklist"


def test_writer_prompt_preemit_precedes_hard_stop() -> None:
    prompt = _writer_template()
    checklist_idx = prompt.find(CHECKLIST_HEADER)
    hard_stop_idx = prompt.find("## HARD STOP RULE")
    assert 0 <= checklist_idx < hard_stop_idx, (
        "Pre-emit checklist must appear before HARD STOP RULE, "
        "and HARD STOP RULE must remain the final section."
    )
```

## Deterministic evidence required in PR body

Per `docs/best-practices/deterministic-over-hallucination.md` and MEMORY
#M-4, quote raw tool output for each claim. The PR body MUST include:

| Claim | Required raw output |
|---|---|
| Test file added | `git diff --stat origin/main..HEAD` showing `tests/test_writer_prompt_preemit_checklist.py | +N` |
| Prompt edited | `git diff --stat` showing `scripts/build/phases/linear-write.md | +N` |
| Tests pass | `.venv/bin/python -m pytest tests/test_writer_prompt_preemit_checklist.py tests/test_writer_prompt_structured_cot.py` final line raw (e.g. `4 passed in N.NNs`) |
| Lint clean | `.venv/bin/ruff check tests/test_writer_prompt_preemit_checklist.py scripts/build/phases/linear-write.md` final line raw |
| HARD STOP still last | `grep -n '^## ' scripts/build/phases/linear-write.md \| tail -3` raw output showing the final headers in order (Pre-emit verification → HARD STOP RULE) |

## Numbered execution steps (per MEMORY DISPATCH-BRIEF CHECKLIST)

1. **Worktree setup.** `git worktree add .worktrees/dispatch/1969-multimedia-preemit-checklist -b gemini/1969-multimedia-preemit-checklist origin/main` and `cd` into it.
2. **Read context.** Read `scripts/build/phases/linear-write.md` (full file), `tests/test_writer_prompt_structured_cot.py` (pattern), and the body of issue #1969 (`gh issue view 1969`).
3. **Insert the checklist** into `scripts/build/phases/linear-write.md` immediately before `## HARD STOP RULE`. Preserve exactly one blank line between the new section and the `## HARD STOP RULE` header.
4. **Add the new test file** `tests/test_writer_prompt_preemit_checklist.py` with the three tests above.
5. **Run the targeted tests** locally: `.venv/bin/python -m pytest tests/test_writer_prompt_preemit_checklist.py tests/test_writer_prompt_structured_cot.py tests/test_lint_prompts.py -v`. Quote the final summary line.
6. **Run ruff** on the changed files: `.venv/bin/ruff check tests/test_writer_prompt_preemit_checklist.py`.
7. **Commit** with conventional message:
   ```
   fix(writer-prompt): add pre-emit checklist for multimedia obligation (#1969)

   m20 build #4 had resources_search_attempted=0 — the multimedia
   obligation in the writer prompt got crowded out by the strong
   `MUST` / `mandatory` / `hard fail` language in the #1964 textbook-
   grounding contract directives that appear earlier in the prompt.

   Add a pre-emit verification checklist near the end of the prompt
   (immediately above HARD STOP RULE) enumerating the four mandatory
   tool-call obligations: textbook search, multimedia search, word
   verification, style-guide search.

   Three new tests in tests/test_writer_prompt_preemit_checklist.py
   verify the checklist is present, lists every required tool, and
   precedes the HARD STOP RULE.

   Closes #1969.
   ```
8. **Push** `-u origin gemini/1969-multimedia-preemit-checklist`.
9. **Open PR** with `gh pr create --title "fix(writer-prompt): add pre-emit checklist for multimedia obligation (#1969)" --body @-` (paste the deterministic-evidence table from above into the body).
10. **NO auto-merge.** Stop after PR is open; orchestrator will review.

## Out of scope (do NOT touch in this PR)

- Pohribnyi auto-caption verbatim policy (separate work; batched with
  broader ULP/Ohoiko verbatim-policy refresh later).
- Promoting the multimedia mandate into the early-mandate block (Option B
  in #1969 — explicitly rejected as higher risk).
- SDK hook for in-stream tool-call telemetry (Option C — deferred to SDK
  adoption Decision Card, currently RECONSIDER).
- Any restructuring of the existing mandate sections at lines 75–250.
- Any other writer-prompt edits.

## Acceptance criteria

- PR opens, closes #1969 automatically on merge.
- All 5 deterministic-evidence rows present in PR body with raw output.
- Three new tests pass.
- `tests/test_lint_prompts.py` and `tests/test_writer_prompt_structured_cot.py` still pass (no regression).
- `grep -n '^## ' scripts/build/phases/linear-write.md | tail -3` shows the final two headers as `## Pre-emit verification (run BEFORE you write any artifact)` then `## HARD STOP RULE`.

---

*Brief written 2026-05-13 late by orchestrator. Predicate-bounded mechanical
prompt-edit work. Expected wall-clock ~10–15 min. After PR opens: orchestrator
reviews + merges (clean CI) → m20 build #5 with `--worktree`.*
