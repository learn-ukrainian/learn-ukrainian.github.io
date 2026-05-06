# Codex dispatch brief — Bakeoff gate fixes (silent no-ops + Codex fence prompt)

> **Branch base:** `origin/main`
> **Worktree:** `.worktrees/dispatch/codex/bakeoff-gate-fixes/`
> **Branch:** `codex/bakeoff-gate-fixes`
> **Mode:** danger
> **Hard timeout:** 3600s
> **Effort:** medium
> **Reviewer:** Claude (cross-family; you are author)

## Goal

Fix five bugs surfaced by tonight's A1/20 bakeoff (run `bakeoff-execute-danger`, msg 525 diagnosis from yourself). All five are pre-existing pipeline bugs that the bakeoff exposed.

## Five edits

### 1. Writer-correction silent no-op — `scripts/build/linear_pipeline.py:2326` area

Today: `_apply_writer_correction` silently returns when the LLM response doesn't contain ALL four artifact names. Failure mode: correction round runs, gate stays red, ADR-008 declares "writer still bad" — no diagnostic that the correction LLM produced unparseable output.

Fix: log a `writer_correction_unparseable` event (or equivalent in the existing emit_event vocabulary) when the response doesn't match expected shape. Include the first 200 chars of response in the event for diagnosis. Still return — don't fail-stop — but make the no-op visible in JSONL.

### 2. Reviewer-correction silent no-ops — `linear_pipeline.py:2394` and `:2422`

Today: reviewer `<fixes>` parsing silently no-ops when format is off, and unmatched anchors silently skip. Failure mode: reviewer reports REVISE, fixes don't apply, gate stays red.

Fix: emit `reviewer_fixes_unparseable` (no `<fixes>` block found OR malformed) and `reviewer_fixes_anchor_unmatched` (anchor string not found in source) events with truncated previews. Return same value, just make failures visible.

### 3. Citation whitespace fragility — `linear_pipeline.py:3350`

Today: citation matching is exact-string. `"p. 176"` (writer output) doesn't match `"p.176"` (plan). Real example from tonight's `gemini/resources.yaml:1` vs `curriculum/l2-uk-en/plans/a1/my-morning.yaml`.

Fix: normalize whitespace in BOTH sides before comparing. Strip multiple spaces, normalize `p.\s*N` → `p.N`, and trim leading/trailing whitespace. Add a unit test with the exact case from tonight: `"p. 176"` should match `"p.176"`.

### 4. Codex fence prompt strengthening — `scripts/build/phases/linear-write.md:105`

Today: prompt says "do not fence prose inside `module.md`" — too vague. Codex (gpt-5.5) tonight emitted a fenced ```text block at line 53 inside `module.md`, parser at `linear_pipeline.py:1535` saw it as closing the artifact, real closer at line 57 became unnamed → fail.

Fix: replace whatever's at `linear-write.md:105` with: `Inside the \`module.md\` artifact, do NOT use triple backticks (\`\`\`) for ANY purpose — no fenced code, no fenced quote, no fenced text. Use plain paragraphs, lists, or tables instead. Triple backticks inside the artifact will be parsed as a closing fence and break the artifact boundary.`

### 5. Tests

Add tests under `tests/`:
- `test_writer_correction_no_op_diagnostic.py` — feed a fake LLM response missing artifact names; assert `writer_correction_unparseable` event emitted.
- `test_reviewer_correction_diagnostics.py` — two cases: (a) no `<fixes>` block, (b) anchor not found. Assert respective events.
- `test_citation_whitespace.py` — `"p. 176"` ↔ `"p.176"` ↔ `"p.  176"` all match.
- (Existing `test_prompt_template_render.py` will catch any markdown structural break in `linear-write.md`.)

## Numbered execution

1. Verify worktree base clean.
2. Read these files first to understand current state: `scripts/build/linear_pipeline.py` (lines 2326, 2394, 2422, 3350), `scripts/build/phases/linear-write.md:105`. Cite specifics in your PR body.
3. Apply edits 1-4. Add tests per #5.
4. Run `.venv/bin/ruff check scripts/build/ tests/`
5. Run `.venv/bin/pytest tests/test_writer_correction_no_op_diagnostic.py tests/test_reviewer_correction_diagnostics.py tests/test_citation_whitespace.py tests/test_prompt_template_render.py -v`
6. Get Claude review:
   ```
   git add -A
   git diff --cached > /tmp/gate-fixes-diff.txt
   .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-claude \
       "Adversarial review for bakeoff gate fixes. Read /tmp/gate-fixes-diff.txt. Focus: (1) do the silent-no-op diagnostic events use the right schema (compare with existing emit_event call shapes in linear_pipeline.py)? (2) is the citation whitespace normalization too aggressive (could it accidentally match unrelated citations)? (3) is the linear-write.md edit clear enough for Codex / Claude / Gemini all to follow consistently?" \
       --task-id bakeoff-gate-fixes-review
   ```
7. Apply feedback or argue back in writing.
8. Commit with `Reviewed-By: claude-opus-4-7 (bakeoff-gate-fixes-review)` trailer.
9. Push, open PR titled `fix(bakeoff): silent no-op diagnostics + citation whitespace + Codex fence prompt`.
10. PR body lists the 4 edits + their evidence (file:line + tonight's bakeoff log lines).

## Constraints

- No auto-merge.
- No edits outside the 5 listed (don't reformat unrelated code).
- Don't change the structural python_qg gates (those are intentionally strict per ADR-008) — only make the silent failures visible.
