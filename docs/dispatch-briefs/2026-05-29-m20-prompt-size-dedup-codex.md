# Dispatch (follow-up on PR #2404) — fix writer-prompt size regression via de-dup

**Agent:** codex `gpt-5.5`, `--effort xhigh`, `--mode danger`. **SAME worktree/branch** as
PR #2404: `.worktrees/dispatch/codex/m20-wiki-coverage-err-seam-2026-05-29`
(branch `codex/m20-wiki-coverage-err-seam-2026-05-29`). Commit on top + push to
update the existing PR. Do NOT open a new PR.

## The one failing check (everything else green; gate logic is CORRECT — do NOT change it)
`tests/test_writer_prompt_render_size.py::test_a1_letter_module_writer_prompt_stays_under_ceiling`
FAILS: rendered writer prompt = **142,520 bytes** vs ceiling **138,240** (135KB).
Overage ≈ 4.2KB.

## Root cause (verified)
Your stub-seeding put the error-correction manifest into
`treatment_template["activity_stub"] = {..., "manifest": {incorrect, correct, why}, ...}`.
`render_for_writer_prompt` (scripts/build/phases/implementation_map.py) then renders
that whole sub-dict into the writer prompt — once PER err obligation (×6 on m20) ≈
+4.2KB. But the SAME `incorrect`/`correct`/`why` text is ALREADY in the Obligation
Checklist that renders into the prompt. It's a DOUBLE-RENDER.

## Fix — de-duplicate (preferred), don't raise the ceiling, don't weaken anything
1. In `render_for_writer_prompt`, render `activity_stub` COMPACTLY: keep the
   structural slot signal the writer needs (obligation_id, `type: error-correction`,
   `location_hint: activities.yaml`, the empty `sentence`/`items` placeholders) but
   DROP the `manifest` sub-dict from the PROMPT render — it is redundant with the
   Obligation Checklist. **Verify** (render the a1-letter prompt and grep) that the
   err `incorrect/correct/why` still appears ONCE (in the checklist) so the writer
   loses no information.
2. KEEP `activity_stub.manifest` in the SEEDED MAP (`implementation_map.json`) — the
   gate's seeded-claim fallback + Goodhart sentinel rely on it. Only the PROMPT
   render changes, not the sidecar.
3. If de-dup alone doesn't clear the ceiling with headroom, trim additional
   redundant rule PROSE (move rationale to docs; terse rule bodies) to reach
   **≤ 132KB** (give back the chronic-creep headroom) — but NEVER drop a rule's
   binding instruction and NEVER raise WRITER_PROMPT_CEILING_BYTES.

## #M-4 — verifiable claims (quote raw output)
- "prompt under ceiling" → `.venv/bin/python -m pytest tests/test_writer_prompt_render_size.py -q` final line raw + the new byte count.
- "err guidance not lost" → grep of the rendered a1-letter prompt showing the err manifest present once.
- "gate tests still pass" → `.venv/bin/python -m pytest tests/audit/test_wiki_coverage_gate.py tests/audit/test_wiki_coverage_gate_fix_proposals.py tests/test_correction_loop_surgical.py -q` final line raw.
- "lint" → `.venv/bin/ruff check scripts tests` final line raw.

## Numbered steps
1. cwd = the existing worktree above; you are on branch `codex/m20-wiki-coverage-err-seam-2026-05-29`. `git pull` is NOT needed (work on top of your commit `2148ff476b`).
2. Apply fix #1 (and #3 only if needed).
3. Run the three pytest groups above + `test_writer_prompt_render_size.py` → all green. ruff clean.
4. Commit: `fix(writer-prompt): de-dup err-stub manifest from prompt render (under 135KB ceiling)`. Trailer `X-Agent: codex/m20-wiki-coverage-err-seam-2026-05-29`.
5. `git push` (updates PR #2404). Do NOT open a new PR. Do NOT merge.
