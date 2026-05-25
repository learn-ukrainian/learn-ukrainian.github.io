# Option C — Plan-reference-match gate (close the `packet_chunk_id` bypass)

**Date**: 2026-05-24
**Agent**: cursor (composer-2.5)
**Mode**: danger
**Effort**: medium
**Wall budget**: 45 min

## Why

The V7 module writer (across `claude-tools` and other writers) fabricates textbook references that are not in `plan.references` but that DO appear in the upstream Knowledge Packet. m20 a1/my-morning build #6 (worktree `.worktrees/builds/a1-my-morning-20260523-220712/`) cited "Захарійчук, Українська мова та читання, Grade 4, p.150" with `notes: "Knowledge Packet anchor S1 (chunk 4-klas-ukrmova-zaharijchuk_s1922): ..."` when the plan only references Grade 1 pp.24/52.

`scripts/build/linear_pipeline.py::_citation_gate` (line 7801) currently catches THIS particular case because the fabricated entry didn't set a `packet_chunk_id` field — it only mentioned the chunk in prose notes. But the gate has a **structural hole at line 7823**:

```python
if (
    normalized_ref not in plan_titles
    and (
        source_key is None
        or not any(citation_keys_match(source_key, plan_key) for plan_key in plan_keys)
    )
    and resource.get("packet_chunk_id") is None   # <-- SHORT-CIRCUIT BYPASS
):
    unknown.append(source_ref)
```

If the writer puts `packet_chunk_id: 4-klas-ukrmova-zaharijchuk_s1922` (a real chunk from the Knowledge Packet but NOT in the plan's references), `citations_resolve` SKIPS the entry entirely and lets the fabrication through.

Plan-grounding must be the source of truth. Knowledge Packet anchors are NOT plan references.

## What to build

A new deterministic gate `plan_reference_match` that:

1. **Extracts the authoritative chunk_id set from `plan.references`** by parsing each `references[*].notes` field for the literal substring `chunk_id: <id>` (the project convention — see `curriculum/l2-uk-en/plans/a1/my-morning.yaml` for an example). The chunk_id regex pattern should be `r"chunk_id:\s*([A-Za-z0-9_\-]+)"`.
2. **For every `resources.yaml` entry with `role: textbook`**, verify that the resource's `packet_chunk_id` (or its alias `chunk_id` per `e63c91d274`) is in the plan's chunk_id set. If the resource has no `packet_chunk_id`/`chunk_id` field at all, also parse its `notes` field for a `chunk_id: <id>` reference (writers sometimes embed it in notes only).
3. **HARD-reject** with `severity: HARD`, `rule_ids: ["#R-CITE-HONEST", "#R-TEXTBOOK-30W"]`, and an explicit failure shape:

```python
{
    "passed": False,
    "severity": "HARD",
    "plan_chunk_ids": ["<chunk_id_1>", "<chunk_id_2>"],
    "out_of_plan": [
        {"source_ref": "<title>", "cited_chunk_id": "<id>"},
        ...
    ],
    "rule_ids": ["#R-CITE-HONEST", "#R-TEXTBOOK-30W"],
    "reason": "resources_cite_chunk_ids_not_in_plan_references"
}
```

4. **`passed: True`** if every textbook resource's chunk_id is in the plan's chunk_id set, OR if the plan has no chunk_ids (some legacy plans without notes — degrade to warning rather than hard-pass, see (8) below).
5. Wire it into the gate registry alongside `citations_resolve` and `textbook_grounding`. Search for `record("citations_resolve", ...)` and `record("textbook_grounding", ...)` at `scripts/build/linear_pipeline.py:5999-6000` — add `record("plan_reference_match", _plan_reference_match_gate(resources, plan))` right after `citations_resolve` (logical ordering: citation resolution first, then plan-membership check on those resolved citations).
6. Update the `TERMINAL_GATES` / `HARD_GATES` list at `scripts/build/linear_pipeline.py:156-190` (search for `"citations_resolve"`) to include `"plan_reference_match"`.
7. Make sure the gate plays correctly with ADR-008 correction: when the gate fails, the correction loop should see a clear `reason` string so it can either (a) remove the out-of-plan citation or (b) signal `correction_impossible` if the writer's blockquotes are sourced from out-of-plan chunks.
8. **Degrade behavior for plans without chunk_ids**: if `plan.references` exists but no entry has a parseable `chunk_id:` in its notes, set `passed: True` with `warnings: ["plan_has_no_chunk_ids_skipping_membership_check"]`. This avoids breaking legacy plans that pre-date the chunk_id convention.

## Tests

Write 3 tests in `tests/test_plan_reference_match_gate.py`:

1. **`test_passes_when_all_textbook_resources_match_plan_chunk_ids`** — fixture with plan.references containing 2 chunk_ids and resources.yaml citing exactly those 2 chunk_ids via `packet_chunk_id`. Gate `passed: True`, `out_of_plan: []`.
2. **`test_rejects_resource_with_out_of_plan_chunk_id`** — fixture mirroring the build #6 failure: plan has Grade 1 chunk_ids (`1-klas-bukvar-zaharijchuk-2025-1_s0024`, `1-klas-bukvar-zaharijchuk-2025-2_s0052`); resources.yaml has those 2 PLUS a Grade 4 entry with `packet_chunk_id: 4-klas-ukrmova-zaharijchuk_s1922`. Gate `passed: False`, `out_of_plan` lists the Grade 4 entry with both `source_ref` and `cited_chunk_id` fields, `severity: HARD`, `reason: "resources_cite_chunk_ids_not_in_plan_references"`.
3. **`test_extracts_chunk_id_from_notes_when_packet_chunk_id_missing`** — the build #6 actual shape: writer puts `chunk_id` only in the notes string ("Knowledge Packet anchor S1 (chunk 4-klas-...)"), not as a structured field. Gate should still detect via notes-parsing fallback and reject. Use the exact line from build #6 resources.yaml entry 3 as the notes fixture.

Additional edge-case test (combined into `test_plan_reference_match_gate.py` for clarity):

4. **`test_passes_when_plan_has_no_chunk_ids`** — plan.references entries have notes WITHOUT any `chunk_id:` token. Gate `passed: True`, `warnings: ["plan_has_no_chunk_ids_skipping_membership_check"]`.
5. **`test_ignores_non_textbook_roles`** — resources.yaml has a `role: youtube` and a `role: wiki` entry with no chunk_id — gate ignores them (only textbook role is checked). `passed: True`.

## Out of scope

- Do NOT modify `_citation_gate` itself. Add a separate gate; existing tests for `citations_resolve` MUST keep passing unchanged. Run `.venv/bin/python -m pytest tests/test_citation_matcher.py tests/test_textbook_grounding_gate.py -x` to confirm.
- Do NOT modify writer prompts (`scripts/build/phases/linear-write.md`). The gate is a defensive backstop; prompt iteration is a separate concern handled elsewhere.
- Do NOT modify ADR-008 correction logic itself. The new gate emits its `reason` string and the existing correction infrastructure consumes it.
- Do NOT touch `scripts/build/citation_matcher.py` unless adding a new utility function specifically for chunk_id extraction (and if you do, name it `extract_chunk_id_from_notes(notes: str) -> str | None` and add it AFTER `extract_plan_reference_titles`).

## REQUIRED steps (numbered — follow in order)

1. `git worktree add -b feat/plan-reference-match-gate ../.worktrees/cursor-option-c-2026-05-24 origin/main` from the project root. Use this worktree for all work; do NOT modify the main project tree.
2. **CD into the worktree** for every subsequent command: `cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/cursor-option-c-2026-05-24`.
3. Symlink venv: `ln -s ../../.venv .venv` (venv symlinked — required for tests). Verify: `ls -la .venv` shows the symlink. # venv symlinked
4. Read the files you'll modify in this order:
   - `scripts/build/linear_pipeline.py` lines 1-200 (imports + gate registry), 5990-6020 (gate recording), 7801-7826 (existing `_citation_gate`)
   - `scripts/build/citation_matcher.py` (utility functions)
   - `curriculum/l2-uk-en/plans/a1/my-morning.yaml` (plan.references shape)
   - `.worktrees/builds/a1-my-morning-20260523-220712/curriculum/l2-uk-en/a1/my-morning/resources.yaml` (failing fixture from build #6 — use this verbatim in test 2/3)
   - `.worktrees/builds/a1-my-morning-20260523-220712/curriculum/l2-uk-en/a1/my-morning/python_qg.json` (current gate output shape — your new gate's output should match the shape of `citations_resolve`)
5. Implement `_plan_reference_match_gate(resources, plan) -> dict` in `scripts/build/linear_pipeline.py`. Place it directly after `_citation_gate`. Use `extract_plan_reference_titles` and `extract_citation_key` from `citation_matcher.py` only if useful (likely you just need a new helper).
6. Wire the gate: add `record("plan_reference_match", _plan_reference_match_gate(resources, plan))` at line ~6000. Add `"plan_reference_match"` to the HARD gate list at line ~156-190 (the same place `citations_resolve` appears).
7. Write `tests/test_plan_reference_match_gate.py` with the 5 tests above. Use `pytest` parametrize for cleanness if helpful. Each test must construct minimal `resources` (list of dicts) and `plan` (dict with `references` list) fixtures — do NOT depend on the build worktree disk paths.
8. Run focused tests: `.venv/bin/pytest tests/test_plan_reference_match_gate.py -v` — all 5 must pass.
9. Run regression: `.venv/bin/pytest tests/test_citation_matcher.py tests/test_textbook_grounding_gate.py -v` — all must pass unchanged.
10. Run full pipeline tests: `.venv/bin/pytest tests/test_linear_pipeline.py -x` — must pass. If any pre-existing failures from main appear (the handoff names 3 in `test_writer_pre_emit_checklist` + `test_linear_pipeline::test_linear_write_*`), document them in the PR body as pre-existing, do NOT fix in this PR.
11. Lint: `.venv/bin/ruff check scripts/build/linear_pipeline.py tests/test_plan_reference_match_gate.py` — must be clean. Then `.venv/bin/ruff format scripts/build/linear_pipeline.py tests/test_plan_reference_match_gate.py`.
12. Commit:
    ```
    git add scripts/build/linear_pipeline.py tests/test_plan_reference_match_gate.py
    git commit -m "feat(pipeline): plan_reference_match gate closes packet_chunk_id bypass

    The citation_gate at scripts/build/linear_pipeline.py:7823 short-circuits
    when resource.packet_chunk_id is set, letting the writer cite chunks that
    are NOT in plan.references (e.g. m20 build #6 cited Knowledge Packet S1
    anchor 4-klas-ukrmova-zaharijchuk_s1922 even though plan.references only
    lists Grade 1 chunks 1-klas-..._s0024 and 1-klas-..._s0052).

    Adds a structural plan_reference_match gate that hard-rejects when any
    textbook resource cites a chunk_id not in plan.references. Parses
    chunk_id from plan.references[*].notes (project convention) and matches
    against resources.yaml packet_chunk_id / chunk_id field, with notes-string
    fallback for writers that only embed chunk_id in prose.

    Closes the Option C hole identified in handoff 2026-05-24-overnight-cursor-end-to-end-m20-stuck-on-writer-protocol.md."
    ```
13. `git push -u origin feat/plan-reference-match-gate`
14. `gh pr create --base main --head feat/plan-reference-match-gate --title "feat(pipeline): plan_reference_match gate closes packet_chunk_id bypass" --body "<HEREDOC with PR template — Summary / Test plan checklist>"`.
15. **NO auto-merge.** Leave PR open for orchestrator review.

## Self-verification before commit (mandatory)

After step 11 lint+format, BEFORE committing in step 12, dump and read your own diff:

```
git diff --stat
git diff scripts/build/linear_pipeline.py | head -200
git diff tests/test_plan_reference_match_gate.py | head -200
```

Verify by reading each diff hunk:
- The new gate function appears EXACTLY ONCE in `linear_pipeline.py`.
- The `record("plan_reference_match", ...)` call appears EXACTLY ONCE.
- `"plan_reference_match"` is added to the HARD gates frozenset/list, NOT duplicated and NOT misspelled.
- No call site of the existing `_citation_gate` was modified.
- No test file other than the new `tests/test_plan_reference_match_gate.py` was modified.

If any verification fails, fix and re-diff before committing.

## Verifiable claims you must back with raw tool output in your PR body

| Claim | Required evidence |
|---|---|
| "5 new tests pass" | `.venv/bin/pytest tests/test_plan_reference_match_gate.py -v` final line raw |
| "Existing citation/textbook tests still pass" | `.venv/bin/pytest tests/test_citation_matcher.py tests/test_textbook_grounding_gate.py -v` final line raw |
| "Full pipeline test pass / regressions documented" | `.venv/bin/pytest tests/test_linear_pipeline.py` final summary line raw + named list of any pre-existing failures |
| "Lint clean" | `.venv/bin/ruff check` raw output (`All checks passed!` or zero-error line) |
| "Commit landed + PR opened" | `git log -1 --oneline` raw + `gh pr view --json url` raw URL line |

Do not paraphrase tool output. If a claim is not in this evidence list, do not make it.

## Anti-fabrication preamble

Per project rule #M-4 (Deterministic Over Hallucination): every verifiable claim in your PR body and commit message must be tool-backed. If you find yourself writing "I believe", "I think", "this should work" — stop, run the tool, paste the output. The PR body should be: 1 paragraph what + why, then a quoted block of raw tool outputs proving each claim.

## Failure modes — known traps

- **Don't add a global mutex/lock that breaks other tests** — the gate is pure-function over `(resources, plan)`. No I/O, no globals.
- **Don't fall back to `search_text`** to retrieve chunks. The gate is deterministic; it operates on the data structures in memory. Plan chunk_ids come from `plan.references[*].notes` parse. Resource chunk_ids come from `resources[*].packet_chunk_id` / `chunk_id` / notes parse.
- **Don't import yaml** in the gate function — `plan` and `resources` are already-parsed dicts/lists by the caller (see `_citation_gate` for the pattern).
- **Don't normalize chunk_ids** (no lowercasing, no stripping prefixes) — chunk_ids are opaque identifiers and must match exactly. Verify by inspection: plan says `1-klas-bukvar-zaharijchuk-2025-1_s0024`, resources should say exactly that string.
