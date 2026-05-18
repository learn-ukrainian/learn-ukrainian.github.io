# Dispatch brief — Issue #1969: resources_search_attempted=0 regression (multimedia search obligation)

**Agent:** Codex gpt-5.5 xhigh
**Mode:** danger (commits + PR open; NO auto-merge)
**Worktree:** required (per #1952)
**Issue:** #1969
**Severity:** HIGH cascade (every module with multimedia obligations — most A1/A2 modules — hits this)
**Sibling open issues:** related to #1964 (a1-m15-24 shape contract) which crowded out the multimedia obligation by tightening citation directives in the early-mandate region of the writer prompt

---

## Why

m20 build #4 (post #1964 shape contract) writer made ZERO multimedia search calls. From `writer_tool_calls.json`:

| Call | Count |
|---|---|
| mcp__sources__verify_words | 6 |
| mcp__sources__search_text | 4 |
| mcp__sources__search_style_guide | 2 |
| mcp__sources__query_pravopys | 1 |
| **mcp__sources__query_wikipedia** | **0** |
| **mcp__sources__search_external** | **0** |
| **mcp__sources__search_images** | **0** |

The `resources_search_attempted` gate caught it and failed the build. Build #3 (pre-#1964) made the multimedia calls naturally; build #4 didn't. Diagnosis: attention-budget issue caused by #1964 tightening textbook-grounding mandates in the early prompt region while multimedia mandate sits at lines 205-241 (later, gets crowded out).

This cascade-blocks every module with multimedia obligations (most A1/A2) — they will all fail `resources_search_attempted` unless the writer's attention budget is rebalanced.

---

## What you build

### Pre-emit checklist (Option A from #1969 — recommended)

In `scripts/build/phases/linear-write.md`, near the END of the prompt (around line 380, before final output instructions), ADD a "Pre-emit verification" checklist that forces the writer to confirm each obligation class has been satisfied before emitting artifacts:

```markdown
## Pre-emit verification (run BEFORE you write any artifact)

Confirm you have made AT LEAST one of each of the following MCP tool calls. If any line below is FALSE for your current session, make the call now BEFORE emitting any artifact:

1. **Textbook grounding** — `mcp__sources__search_text` for each plan_references textbook entry (one call per entry; verify the citation page exists in the search hit).
2. **Multimedia obligation** — AT LEAST ONE of `mcp__sources__query_wikipedia`, `mcp__sources__search_external`, OR `mcp__sources__search_images`. This is non-negotiable: the `resources_search_attempted` gate will REJECT modules with `multimedia_calls_total == 0`.
3. **VESUM verification** — `mcp__sources__verify_words` on EVERY Ukrainian form you intend to write that isn't trivially known (i.e. anything beyond top-100 frequency). One batched call per dozen lemmas/forms is fine.
4. **Russianism check** — `mcp__sources__search_style_guide` on at least one Russianism-candidate form (when teaching contrast pairs).

If any line above is FALSE, make the call now. Do not emit artifacts until the checklist is fully green.
```

**Then immediately after the checklist**, before the "Now emit your artifacts" sentence (or equivalent), ADD a sentence that frames non-compliance:

> Failure to satisfy ANY checklist line will cause the build to fail at the `resources_search_attempted` / `vesum_verified` / `textbook_grounding` / `style_guide_evidence` gate AFTER you've spent compute generating prose. The 4 tool calls above cost you 30 seconds of latency and unblock the entire build. Make them.

### Apply same change to `linear-write-grok.md`

For symmetric coverage across writer agents (Grok is a known runner-up; same regression would hit it). Add the same checklist near line 380 of `scripts/build/phases/linear-write-grok.md`.

### Test — `tests/build/test_writer_pre_emit_checklist.py`

Two cases:

1. `test_linear_write_contains_pre_emit_checklist` — assert the literal string "Pre-emit verification" appears in `scripts/build/phases/linear-write.md`, AND assert each of the 4 obligation labels (textbook grounding / multimedia / VESUM / Russianism) appears in the checklist body.
2. `test_linear_write_grok_contains_pre_emit_checklist` — same assertions for `linear-write-grok.md`.

This is a prompt-content lint test, not a behavioral test. It exists to prevent silent regression where the checklist is reverted in a future prompt edit.

---

## Out of scope

- **No changes to `linear_pipeline.py`.** The gate code itself is correct; the writer prompt is the problem.
- **No new gates.** `resources_search_attempted` already exists and is doing the right thing — it's catching the regression. The fix is making the writer call the tools.
- **Don't restructure the existing mandate sections** (lines 81-95 for textbook grounding, 205-241 for multimedia). The checklist at the END acts as a closing reminder; restructuring the early-mandate region carries higher regression risk.
- **Don't touch `vocabulary-activity-standards.md` or other docs.** This is a prompt + test PR.
- **Don't address the `pedagogical_deviations_from_standard` plan field** (#1940) — separate issue.

---

## Verifiable claims (per #M-4)

| Claim | Tool + raw output |
|---|---|
| Pre-emit checklist added to writer prompt | `git diff origin/main -- scripts/build/phases/linear-write.md` showing the new section |
| Same checklist in grok writer prompt | `git diff origin/main -- scripts/build/phases/linear-write-grok.md` showing the new section |
| Test file added | `git diff origin/main -- tests/build/test_writer_pre_emit_checklist.py` showing new file |
| New test passes | `.venv/bin/pytest tests/build/test_writer_pre_emit_checklist.py -v` final summary line raw |
| Existing prompt-content tests still pass | `.venv/bin/pytest tests/build/ tests/audit/ -q` final summary line raw |
| Full pytest green | `.venv/bin/pytest tests/ -q` final summary line raw (NO `-x` per #1942) |
| Ruff clean | `.venv/bin/ruff check tests/build/test_writer_pre_emit_checklist.py scripts/build/phases/` raw |
| Pre-commit clean | `.venv/bin/python -m pre_commit run --files <changed>` raw |
| Commit + PR | `git log -1 --oneline` + `gh pr view --json url` raw |

**No claim allowed without its raw output line.** Per #M-4.

---

## Worktree setup

Branch: `fix/1969-multimedia-pre-emit-checklist`. Path: `.worktrees/dispatch/codex/1969-multimedia-pre-emit-checklist-<timestamp>/`.

## Verification (must run all BEFORE pushing)

```bash
# venv symlinked from main; run from worktree root
.venv/bin/pytest tests/build/test_writer_pre_emit_checklist.py -v
.venv/bin/pytest tests/build/ tests/audit/ -q
.venv/bin/pytest tests/ -q
.venv/bin/ruff check tests/build/test_writer_pre_emit_checklist.py scripts/build/phases/
.venv/bin/python -m pre_commit run --files \
    scripts/build/phases/linear-write.md \
    scripts/build/phases/linear-write-grok.md \
    tests/build/test_writer_pre_emit_checklist.py
git diff --stat origin/main
```

Per #M-7: pre-commit ≠ pytest. Both required.
Per #1942: NO `-x` flag.

## Commit + PR

Conventional commit. Title: `fix(writer-prompt): add pre-emit checklist for multimedia/vesum/textbook obligations (#1969)`. Body covers:
1. Root cause (attention-budget regression from #1964 shape contract tightening)
2. Fix (pre-emit checklist near prompt end)
3. Coverage of both linear-write.md and linear-write-grok.md
4. All verifiable-claims raw outputs

NO `--auto-merge`.

## Anti-fabrication preamble

If anything in this brief surprises you when you read the code:

- The "line 380" reference is approximate; locate the closest natural fence in the prompt structure (probably right before the final "Now emit your artifacts" line or equivalent).
- If `linear-write.md` already has a "Pre-emit verification" section, do NOT add another — investigate why this brief was filed and report back.
- If the grok writer prompt is structured differently (different line counts, different mandate locations), adapt the checklist insertion point to fit its structure — don't blindly add at line 380.

STOP and quote the surprise verbatim before patching.

## Notes for orchestrator (Claude, not Codex)

* This is HIGH-cascade per the cascade-risk handoff: every m20-style module with multimedia obligations hits this. Firing in parallel to #2127 because the file scope is disjoint (#2127 touches linear-correction*, #1969 touches linear-write*).
* Estimated duration: 25-40 min (smaller scope than #2127/#2128 — single prompt section + 1 test).
* On finalize: confirm m20 re-build (after both #2127 + #1969 land) actually calls `query_wikipedia` / `search_images` / `search_external` at least once. That's THE proof the checklist worked.
* Per the Codex silent-exit pattern observed on #2128 (issue #2134): monitor worktree progress mid-flight; finalize manually if Codex dies silently after edits but before commit.
