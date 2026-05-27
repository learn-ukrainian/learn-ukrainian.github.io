# 2026-05-27 — `textbook_grounding` gate split (Gemini)

> Dispatch target: `gemini --mode danger --worktree`, model `gemini-3.1-pro-preview`.
> Base: `origin/main` (post PR #2366 + PR #2367 merges; verify with `git log -1`).
> Tracking: brain-pick turn 2 Q4 (`audit/2026-05-27-codex-brain-pick-m20/turn-2-followups.md`) + HARD prerequisite for Phase 2a m20 refire.

## Why this exists

PR #2366 modified the writer prompt `#R-TEXTBOOK-30W` in `linear-write.md` to allow Grade 1-3 chunks to ground the writer's lexical choices WITHOUT publishing a learner-facing blockquote. The codex brain-pick proposed this exact resolution to the m20 Grade 1 conflict.

**The existing gate `_textbook_grounding_gate` in `scripts/build/linear_pipeline.py:8571` still enforces the OLD contract**: every `plan_reference` requires a long blockquote in `module.md`. The gate counts `long_blockquotes_checked` per plan ref; if a writer follows the new prompt and omits the Grade 1 blockquote, the gate HARD-rejects.

This makes Phase 2a m20 refire impossible until the gate matches the prompt. The brain-pick proposal:
- Split `textbook_grounding` into two gates with different responsibilities.
- `chunk_context_for_all_refs`: every `plan_reference` MUST be retrieved via `mcp__sources__get_chunk_context` — applies regardless of source grade.
- `published_quote_for_publishable_refs`: only publishable refs (Grade 7+, adult literature, style guides, dictionaries — see below for the exact predicate) require a ≥30-word blockquote in `module.md`.

After the split, Grade 1-3 plan refs need `get_chunk_context` calls (still gated) but DON'T need a published blockquote (no longer gated).

## What to build

### Part A — split the gate

In `scripts/build/linear_pipeline.py`:

1. **Read the current `_textbook_grounding_gate` function** (~line 8571 down to ~8730). Understand what it currently checks: at minimum, (a) every `plan_reference` had a chunk_context call (via `chunk_context_calls` in writer telemetry), (b) every plan ref has a long blockquote in module text, (c) blockquotes literally appear in their referenced chunk's text.

2. **Define a `is_publishable_ref(ref: Mapping) -> bool` helper** that returns True if the plan reference's source is adult-appropriate. Predicate logic (use plan-reference metadata; common shapes are `notes` containing `chunk_id` patterns, `source`, `grade`, `author`):
   - **publishable** (returns True) when ANY of:
     - `grade` ≥ 7 (parse from `grade`, `notes` `grade=N` substring, or `chunk_id` prefix like `7-klas-...`)
     - `source_type` ∈ `{"literature", "style_guide", "dictionary"}` (case-insensitive)
     - `author` matches a curated list of adult-style authors (e.g., `Антоненко-Давидович`, `Грінченко`) — keep this list small and explicit; document additions
   - **internal-only** (returns False) when:
     - `grade` ∈ `{1, 2, 3}` AND no other publishable signal — these are children's primers
     - Anything else lacking publishable signals
   - When ambiguous (no grade, no source_type, no author): default to **internal-only** (safer; prevents accidentally publishing children's quotes).
   - Write this helper as a pure function with unit tests covering each branch.

3. **Split into two gates:**
   - **`_chunk_context_for_all_refs_gate(plan, writer_tool_calls, module_dir)`** — for each `plan_reference`, check that the writer issued a `mcp__sources__get_chunk_context` call returning that ref's `chunk_id`. HARD-rejects if any plan ref is missing a chunk_context call. (Equivalent to the current gate's chunk_context check, but unconditional on publishability.)
   - **`_published_quote_for_publishable_refs_gate(module_text, plan, module_dir)`** — for each `plan_reference` where `is_publishable_ref(ref) is True`, verify a ≥30-word blockquote literally appears in `module.md` and that the blockquote's text is string-contained in the chunk's `text`. Skip internal-only refs entirely (passing them through without checking for a blockquote).

4. **Wire both new gates** into the gate registry at the SAME phase ordering as the old gate (look near line 6093-6095 for the `record(...)` calls). Replace the existing `record("textbook_grounding", _textbook_grounding_gate(...))` with TWO records:
   ```python
   record("chunk_context_for_all_refs", _chunk_context_for_all_refs_gate(plan, writer_tool_calls, module_dir))
   record("published_quote_for_publishable_refs", _published_quote_for_publishable_refs_gate(module_text, plan, module_dir))
   ```
   Keep the old gate function code in the file (don't delete it yet) but un-register it. Mark its definition with a comment `# DEPRECATED: split into chunk_context_for_all_refs + published_quote_for_publishable_refs as of 2026-05-27. Remove after one successful Phase 2a refire.`

5. **Update the writer prompt** in `scripts/build/phases/linear-write.md` to reference the new gate names. Current `#R-TEXTBOOK-30W` says "The gate counts `chunk_context_calls`; if zero while `plan_references` is non-empty, the gate HARD-rejects" — update to name the specific gate (`chunk_context_for_all_refs`). Update the long-blockquote phrasing to name `published_quote_for_publishable_refs`.

### Part B — tests

In `tests/build/test_textbook_grounding_split.py` (new file):

1. **`is_publishable_ref` unit tests** — one per branch:
   - Grade 1 → False
   - Grade 7 → True
   - Grade with `source_type: literature` → True regardless of grade
   - `author: Антоненко-Давидович` → True
   - No grade, no source_type, no author → False (default)

2. **`_chunk_context_for_all_refs_gate` tests:**
   - All plan refs have matching chunk_context calls (Grade 1 + Grade 7 mixed) → passed=True
   - One Grade 1 ref missing chunk_context call → passed=False with that ref's chunk_id in violation
   - One Grade 7 ref missing chunk_context call → passed=False with that ref's chunk_id in violation

3. **`_published_quote_for_publishable_refs_gate` tests:**
   - Plan has only Grade 1 refs → no blockquote required → passed=True even with EMPTY `module_text`
   - Plan has Grade 7 ref + matching ≥30-word blockquote → passed=True
   - Plan has Grade 7 ref but blockquote is missing → passed=False
   - Plan has Grade 7 ref but blockquote text not contained in chunk → passed=False
   - Plan has Grade 1 + Grade 7 mixed; Grade 7 blockquote present, Grade 1 not present → passed=True

4. **Regression test against m20 plan:**
   - Load `curriculum/l2-uk-en/plans/a1/my-morning.yaml`.
   - Construct mock `writer_tool_calls` with chunk_context calls for ALL plan refs.
   - Assert `_chunk_context_for_all_refs_gate` passes.
   - Construct mock `module_text` with publishable blockquotes only (no Grade 1).
   - Assert `_published_quote_for_publishable_refs_gate` passes.
   - This proves the m20 plan can build under the split gate WITHOUT Grade 1 blockquotes.

### Part C — DON'T forget

- Update the existing `tests/build/test_linear_pipeline.py` test cases that reference `textbook_grounding` if any (look near line 3419 where PR #2367 already touched the `search_text` → `get_chunk_context` mock).
- DO NOT delete the old `_textbook_grounding_gate` function body — leave deprecated. Other tests may still call it.
- DO NOT modify any other gates.

## Anti-fabrication contract (#M-4)

| Claim | Required evidence in PR body |
|---|---|
| "Two new gates registered" | `grep -n 'chunk_context_for_all_refs\|published_quote_for_publishable_refs' scripts/build/linear_pipeline.py` raw output |
| "Old gate is no-op-registered" | `grep -n 'textbook_grounding' scripts/build/linear_pipeline.py` showing the un-registered line |
| "is_publishable_ref covers each branch" | Test names from `pytest tests/build/test_textbook_grounding_split.py --collect-only` |
| "m20 plan parses under the split" | Test output of the regression case |
| "Tests pass" | `.venv/bin/pytest tests/build/test_textbook_grounding_split.py tests/build/test_linear_pipeline.py -q --no-header` final summary line raw |
| "Lint clean" | `.venv/bin/ruff check scripts/build/linear_pipeline.py tests/build/test_textbook_grounding_split.py` final line raw |
| "PR opened" | `gh pr view --json url` raw URL line |

## Numbered execution steps

1. **Worktree.** You start in a fresh worktree at `.worktrees/dispatch/gemini/textbook-grounding-gate-split-2026-05-27/`. Verify `pwd`, `git branch --show-current` (should be `gemini/textbook-grounding-gate-split-2026-05-27`).
2. **Pull latest origin/main** to ensure PR #2366 and #2367 are in your base: `git fetch origin main && git log --oneline -5`. Confirm the last 5 commits include the codex prompt-hardening PR (#2366) and verify_quote gate PR (#2367).
3. **Read `scripts/build/linear_pipeline.py`** around the existing `_textbook_grounding_gate` (~line 8571 to 8730). Note its current shape.
4. **Read `scripts/build/phases/linear-write.md`** around `#R-TEXTBOOK-30W` (line 119 to 140). Note the current contract language.
5. **Read `curriculum/l2-uk-en/plans/a1/my-morning.yaml`** to see real plan reference shapes (`notes`, `chunk_id`, `grade`, `author`, `source_type` fields).
6. **Implement Part A** — `is_publishable_ref` helper, two new gate functions, wire registration, deprecate old gate.
7. **Update Part A.5** — writer prompt language to reference new gate names.
8. **Implement Part B** — new test file with the unit tests + regression case.
9. **Run tests.** `.venv/bin/pytest tests/build/test_textbook_grounding_split.py tests/build/test_linear_pipeline.py -q --no-header`. Capture final line.
10. **Run lint.** `.venv/bin/ruff check scripts/build/linear_pipeline.py tests/build/test_textbook_grounding_split.py scripts/build/phases/linear-write.md`. Capture final line. (Note: ruff doesn't lint markdown; that's prompt-lint workflow.)
11. **Commit conventional:**
    ```
    feat(v7-gates): split textbook_grounding into chunk_context_for_all_refs + published_quote_for_publishable_refs

    Resolves the writer-prompt vs gate drift introduced by PR #2366
    (#R-TEXTBOOK-30W relaxed for Grade 1-3) while the old monolithic
    gate still enforced per-ref blockquote requirements.

    Split contract:
    - chunk_context_for_all_refs: every plan_reference requires a
      get_chunk_context call regardless of source grade.
    - published_quote_for_publishable_refs: only publishable refs
      (Grade 7+, adult lit, style guide, dictionary, named adult
      authors) require a >=30-word blockquote in module.md.

    is_publishable_ref helper defaults to internal-only when grade
    metadata is absent (safer; prevents accidental child-primer
    quotes from leaking).

    Old _textbook_grounding_gate retained as deprecated for one
    Phase 2a refire cycle, then removed.

    Resolves brain-pick turn 2 Q4. Hard prerequisite for m20 refire
    under the hardened pipeline.

    X-Agent: gemini/textbook-grounding-gate-split-2026-05-27
    ```
12. **Push + PR.** `git push -u origin gemini/textbook-grounding-gate-split-2026-05-27` then `gh pr create` with title `feat(v7-gates): split textbook_grounding into chunk_context_for_all_refs + published_quote_for_publishable_refs`. Body must include: (a) raw test/lint outputs, (b) reference to brain-pick turn 2 Q4, (c) Phase 2a unblocker note.
13. **DO NOT auto-merge.** Orchestrator review required.

## Scope guardrails

- DO NOT change writer prompt rules other than naming the new gate. The 6 `#R-` rules from PR #2366 stay as-is.
- DO NOT modify any other gates.
- DO NOT modify reviewer rubric (`linear-review-dim.md`).
- DO NOT touch `curriculum/l2-uk-en/a1/my-morning/` — m20 stays as-is until refire.
- DO NOT delete the old `_textbook_grounding_gate` function body in this PR. Just un-register it.

## On unexpected blockers

- If the plan-reference shape varies across modules (some have `grade` as int, some as string, some have only `chunk_id` prefix like `1-klas-...`), `is_publishable_ref` must handle all shapes. Use defensive parsing; default to internal-only on parse failure.
- If existing tests beyond `test_linear_pipeline.py` reference `textbook_grounding`, update them to use one or both new gates as appropriate. Don't silently delete assertions.
- If you discover that the chunk_context_calls check is implemented OUTSIDE `_textbook_grounding_gate` (e.g., in a separate gate or in writer telemetry processing), the split may need different wiring. Surface this discovery in PR body; the brief assumes the old gate handles both.
