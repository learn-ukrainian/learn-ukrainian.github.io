# Writer-prompt Option B fixes — apply the 3 audit-identified changes

**Date**: 2026-05-24
**Agent**: codex
**Mode**: danger
**Effort**: high
**Wall budget**: 40 min

## Why

m20 a1/my-morning has failed 6+ build attempts with the same root cause: the writer fabricates textbook citations outside `plan.references` (cites Grade 4 anchors when plan only lists Grade 1). The 2026-05-24 audit at `audit/2026-05-24-writer-prompt-competing-rules.md` identified the smoking gun: 3 competing rules in `scripts/build/phases/linear-write.md` that fight `#R-TEXTBOOK-30W`. Option C (post-emit gate) merged in PR #2257 as a backstop. This dispatch fixes the writer prompt itself so the writer doesn't fabricate in the first place.

## Read these first

1. `audit/2026-05-24-writer-prompt-competing-rules.md` — full audit (1511 chars, ~20 lines).
2. `scripts/build/phases/linear-write.md` — the writer prompt template (~530 lines).
3. `.worktrees/builds/a1-my-morning-20260523-220712/curriculum/l2-uk-en/a1/my-morning/knowledge_packet.md` — the actual Knowledge Packet that the writer saw in build #6 (has Grade 4 S1 anchor outside plan).
4. `curriculum/l2-uk-en/plans/a1/my-morning.yaml` — the plan (`references` field lists Grade 1 only).

## The 3 fixes

### Fix 1 — Citation-authority hierarchy (add after linear-write.md:99)

The writer prompt currently has NO explicit ordering of citation authorities (plan > knowledge packet > corpus). The audit recommends adding an early statement that makes plan.references the SOLE source of textbook citations.

Concrete addition after line 99 (find the right insertion point — right after the lesson-contract opening, before any rule blocks):

```
## Citation authority (read this FIRST, applies to every artifact)

The plan's `references` field is the SOLE source of textbook citations for `resources.yaml`. Knowledge Packet anchors (S1, S2, S3, ...) are research material — they help you UNDERSTAND topic context, but they are NOT citation candidates. If a Knowledge Packet anchor points to a chunk OUTSIDE `plan.references`, you MUST NOT cite that chunk in `resources.yaml`.

Concrete example: if `plan.references` lists [Захарійчук Grade 1, p.24] and the Knowledge Packet S1 anchor points to Захарійчук Grade 4 p.150, you cite ONLY Grade 1 p.24. The Grade 4 anchor is research context, not citation material.

This rule overrides any later instruction that suggests "enriching" or "extending" plan_references — those instructions apply within the plan-provided sources, never outside them.
```

Place this BEFORE the existing rules so it sets the frame.

### Fix 2 — Knowledge Packet ≠ resources.yaml (rewrite linear-write.md:193)

The audit names line 193 as: "allows Knowledge Packet anchors to become textbook entries in `resources.yaml`."

Read the current line 193 (it's likely a rule about resources.yaml or wiki obligations). Make it explicit that resources.yaml entries with `role: textbook` MUST have a `chunk_id` (in `packet_chunk_id`, `chunk_id`, or `notes` field) that appears in `plan.references[*].notes`.

If the current text says something like "every wiki obligation must be emitted as a resources.yaml entry" — qualify it: "EXCEPT textbook-role entries, which come ONLY from plan.references."

### Fix 3 — Replace linear-write.md:455 with chunk-id-first protocol

The audit names line 455 as the **direct contradiction** to `#R-TEXTBOOK-30W` Step A. Current line 455 reads (per the audit):

```
1. Textbook grounding: `mcp__sources__search_text` for each `plan_references` entry, then `mcp__sources__get_chunk_context` for quotes.
```

This tells the writer to call `search_text` FIRST for each plan ref, which:
- Wastes a tool call (chunk_id is already in plan.notes).
- Often returns the wrong chunk (FTS5 matches "p.24" across all textbooks → wrong author).
- Encourages the writer to "extend" references beyond plan.

**Replace with**:

```
1. Textbook grounding (mandatory chunk_id-first protocol):
   For each entry in `plan_references`, parse the `notes` field for the literal substring `chunk_id: <ID>` (always present — example: `chunk_id: 1-klas-bukvar-zaharijchuk-2025-1_s0024`).
   Call `mcp__sources__get_chunk_context(chunk_id=<ID>)` to fetch the chunk text.
   DO NOT call `mcp__sources__search_text` for plan references — the chunk_id in notes is authoritative.
   Concrete example: plan says `chunk_id: 1-klas-bukvar-zaharijchuk-2025-1_s0024` → call `get_chunk_context(chunk_id="1-klas-bukvar-zaharijchuk-2025-1_s0024")`, paste from THAT returned text. Do NOT search by "p.24" — FTS5 will return the wrong author (e.g. Pohribnyi instead of Захарійчук).
```

## REQUIRED steps (numbered)

1. From project root: `git fetch origin && git worktree add -b fix/writer-prompt-option-b-fixes-2026-05-24 .worktrees/dispatch/codex/writer-prompt-option-b-fixes-2026-05-24 origin/main`
2. `cd .worktrees/dispatch/codex/writer-prompt-option-b-fixes-2026-05-24 && ln -s ../../../../.venv .venv` (# venv symlinked)
3. Read the 4 files in the "Read these first" list.
4. Apply Fix 1, Fix 2, Fix 3 in that order. After each, run `git diff scripts/build/phases/linear-write.md | head -40` to visually verify.
5. Run lint: `.venv/bin/ruff check scripts/build/phases/ 2>&1 | tail -5` (should pass — these are .md files, ruff won't touch them, but check for any related tests).
6. Run prompt-related tests:
   ```
   .venv/bin/pytest tests/build/test_writer_pre_emit_checklist.py tests/build/test_linear_pipeline.py -v 2>&1 | tail -20
   ```
   All must pass.
7. Run writer-prompt-size check: `.venv/bin/python scripts/audit/check_writer_prompt_size.py 2>&1 | tail -5` — must stay under the 130KB ceiling (current is ~120KB; these changes are ADDITIVE so verify).
8. Three separate commits (one per fix). Conventional: `feat(writer-prompt): add citation-authority hierarchy`, `fix(writer-prompt): exclude knowledge packet anchors from resources.yaml`, `fix(writer-prompt): chunk_id-first protocol replaces search_text-first`.
9. `git push -u origin fix/writer-prompt-option-b-fixes-2026-05-24`
10. `gh pr create --base main --title "fix(writer-prompt): close 3 competing rules vs #R-TEXTBOOK-30W (Option B)" --body "Implements the 3 fixes from audit/2026-05-24-writer-prompt-competing-rules.md. Companion to PR #2257 (Option C deterministic gate)."`
11. **NO auto-merge.** Leave for orchestrator review.

## Verifiable claims

| Claim | Evidence |
|---|---|
| "Fix 1 added" | `git diff scripts/build/phases/linear-write.md` showing new "Citation authority" section |
| "Fix 2 applied at line 193" | `git diff` showing line 193 edit |
| "Fix 3 applied at line 455" | `git diff` showing the search_text → chunk_id-first rewrite |
| "Prompt size still under ceiling" | `check_writer_prompt_size.py` output |
| "Tests pass" | `pytest` summary raw |
| "PR opened" | `gh pr view --json url` raw URL |

## Anti-fabrication (#M-4)

Every claim tool-backed. Quote raw outputs in PR body. The audit file is your guide — do not invent alternative fixes beyond what it specifies.
