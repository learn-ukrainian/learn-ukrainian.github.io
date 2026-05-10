# Codex brief — V6 → V7 documentation sweep

**Issue:** N/A (orchestrator-driven follow-up to user-stated rule "V7 only — v5/v6 obsolete, never going back" from 2026-05-10).
**Task ID:** `codex-v6-v7-doc-sweep`
**Mode:** `--mode danger --worktree`
**Effort:** Codex CLI default (high).
**Base branch:** `origin/main`.
**Hard timeout:** 7200s default; silence-timeout 1800s.

---

## Worktree instructions (mandatory)

Work in a git worktree at `.worktrees/codex-v6-v7-doc-sweep`. Do NOT create a feature branch in the main checkout. Concrete setup:

```
git worktree add -b codex-v6-v7-doc-sweep .worktrees/codex-v6-v7-doc-sweep origin/main
cd .worktrees/codex-v6-v7-doc-sweep
```

Main checkout stays untouched on `main`. Post-merge cleanup is the orchestrator's job.

---

## Context

User stated 2026-05-10: **V7 is the only build pipeline. v5/v6 are obsolete and we are never going back.** This was already encoded into `memory/MEMORY.md` (#0 + #M0 row 2 + `BUILDS — NEVER RUN, ONLY SUGGEST` section) and `claude_extensions/agents/curriculum-maintainer.md` (Critical-operational-rules + Reference-docs).

Five other source files still describe v6 as if it were live or co-equal. Sweep them. **Do not delete `scripts/build/v6_build.py` from disk** — file existence is fine, only the documentation framing needs to change.

The V7 entry point is `scripts/build/v7_build.py`. Verify its exact CLI shape with `.venv/bin/python scripts/build/v7_build.py --help` before writing the new prose. Confirmed via orchestrator probe at handoff time:

- Positional args: `level slug` (single-module per invocation)
- **No `--range`, no `--step`, no batch / resume / rewrite / regeneration flags.** Per `--help` epilog: *"Use for single-module V7 reboot builds; do not use for V6 legacy batch, resume, rewrite, or regeneration workflows."*
- Optional flags: `--writer {claude-tools,gemini-tools,codex-tools,claude,gemini,codex}` (default `claude-tools`; alias-normalized), `--writer-timeout`, `--dry-run`, `--out`, `--telemetry-out`.
- V7 phase prompts live at `scripts/build/phases/linear-write.md`, `linear-review-dim.md`, `linear-writer-correction.md`. The `v6-*.md` phase prompts in that directory are obsolete (do not delete; just stop referencing).
- V7 emits FAR fewer JSONL events than V6 — primarily error events around reviewer fixes (`reviewer_fixes_anchor_unmatched`, `reviewer_fixes_unparseable`, `writer_correction_unparseable`). The V6 events `module_start`/`phase_done`/`review_score`/`module_done`/`module_failed`/`batch_done` do NOT exist in V7.

**V7 builds are USER-RUN ONLY** (encoded in curriculum-maintainer.md). Agents never invoke v7_build.py. This affects the CLAUDE.md `Build Monitoring (MANDATORY)` section reframing below.

---

## Files to update (verbatim line refs from grep at handoff time)

```
CLAUDE.md:51
CLAUDE.md:78
CLAUDE.md:94
CLAUDE.md:101
claude_extensions/rules/pipeline.md:17
claude_extensions/rules/pipeline.md:31
claude_extensions/rules/pipeline.md:32
claude_extensions/skills/code-review/SKILL.md:15
claude_extensions/skills/code-review/code-review-checklist.md:96
claude_extensions/skills/prompt-template-review/template-review-checklist.md:19
claude_extensions/skills/prompt-template-review/template-review-checklist.md:28
claude_extensions/skills/prompt-template-review/template-review-checklist.md:37
claude_extensions/skills/prompt-template-review/template-review-checklist.md:38
claude_extensions/skills/prompt-template-review/template-review-checklist.md:72
```

**Run `ugrep -rn 'v6_build\|v6-write\|v6-review\|v6-skeleton\|v6-vocab\|v6-enrich\|v6-activities' claude_extensions/ CLAUDE.md AGENTS.md` first** to make sure you don't miss any. The list above came from one grep pass; if grep found more, sweep those too. Do not silently ignore stragglers.

---

## What each file needs

### `CLAUDE.md`

- **L51 — Build pipeline**: change to `.venv/bin/python scripts/build/v7_build.py {level} {slug}` (positional args reflect V7 reality). Remove `[--step {step}]` (doesn't exist in V7). Optionally show `[--writer {claude-tools|gemini-tools|codex-tools}]` (default `claude-tools`).
- **L78 (Monitor tool row in Power Features table)**: rewrite to reflect V7 monitoring reality. Suggested prose:

  > `Monitor` tool — Stream stdout events as notifications. **Use when the USER runs a build** (V7 builds are user-run only; agents never invoke `v7_build.py`). Filter `v7_build.py` JSONL events with `grep --line-buffered '^{\"event\"'`. See "Build Monitoring" below.

- **L94 — Monitor tool example block**: replace v6_build.py invocation. Since V7 is single-module + user-run, the example should reflect that, e.g.:

  ```
  Monitor(
      command=".venv/bin/python -u scripts/build/v7_build.py {level} {slug} 2>&1 | grep --line-buffered '^{\"event\"'",
      description="V7 build events for {level}/{slug}",
      persistent=True,
      timeout_ms=3600000
  )
  ```

  Add a one-line note above the block: *"Only used when monitoring a user-run V7 build; agents do not invoke v7_build.py themselves."*

- **L101 — V6 event names enumeration**: replace with V7 truth. Suggested prose:

  > `v7_build.py` emits sparse JSONL events — primarily error events around reviewer fixes (`reviewer_fixes_anchor_unmatched`, `reviewer_fixes_unparseable`, `writer_correction_unparseable`). Successful builds emit few events; failure surfaces are the main monitoring signal. Each line becomes a notification — zero polling overhead.

  Verify the event-name list against `scripts/build/linear_pipeline.py` (use `grep -nE 'emit_event\(\s*"[a-z_]+"' scripts/build/linear_pipeline.py | sort -u`). Quote raw grep output in your commit message as evidence.

### `claude_extensions/rules/pipeline.md`

The current "Two pipelines coexist during the reboot transition" framing is obsolete. Rewrite the top section accordingly:

- **L14-19 (block "Two pipelines coexist…")**: replace with a one-sentence statement that V7 (`scripts/build/linear_pipeline.py` driven by `scripts/build/v7_build.py`) is the only pipeline. v5/v6/v4/v3 are RETIRED — files may still be on disk for forensic reference but must not be invoked, extended, or referenced as live policy.
- **L17 specifically**: drop. The "LEGACY. The reboot replaces it" framing implied co-existence; the user has now killed v6 entirely.
- **L28-34 (the entire "V6 (legacy) reference" subsection)**: remove. Don't replace with "V7 reference" — the entry point + flags are already documented in CLAUDE.md / curriculum-maintainer.md / `--help`. One source of truth, not three.
- **L31 + L32 specifically**: removed as part of the section delete.
- **L22 ("Reboot policy authority")**: rename heading from "Reboot policy" to "Pipeline policy" (reboot is over). Keep the bullet about Codex/GPT-5.5 writer being conditional on #1731 Part B since the Decision Card is still live; do NOT alter that bullet's content. Just normalize "the reboot" / "reboot code paths" → "V7" / "the pipeline" throughout.

### `claude_extensions/skills/code-review/SKILL.md` and `code-review-checklist.md`

- **`SKILL.md:15`**: replace `scripts/build/v6_build.py scripts/build/dispatch.py` with `scripts/build/v7_build.py scripts/build/linear_pipeline.py` (linear_pipeline is where the actual phase logic now lives — reviewing `v7_build.py` alone misses the meat).
- **`code-review-checklist.md:96`**: replace `scripts/build/v6_build.py` → `tests/test_v6_build.py` mapping with `scripts/build/v7_build.py` → `tests/test_v7_build.py` (verify the test file actually exists with `ls tests/test_v7_build.py`; if it doesn't, use whatever V7 test file does exist — `ugrep -l 'v7_build\|linear_pipeline' tests/`).

### `claude_extensions/skills/prompt-template-review/template-review-checklist.md`

This skill's whole purpose is to validate prompt templates against the build script that consumes them. V7 changed both:

- **L19 + L72**: replace `scripts/build/v6_build.py` with the actual V7 placeholder-replacement site. Trace it: `linear_pipeline.py` is where the writer/reviewer prompts get rendered. Use `grep -n '\.format(\|f"' scripts/build/linear_pipeline.py | head -40` to find replacement sites.
- **L28**: change the flag wording from `UNREPLACED: {PLACEHOLDER} in {template} — no replacement found in v6_build.py` to `... no replacement found in linear_pipeline.py`.
- **L37 + L38**: the template names `v6-write.md` and `v6-write-seminar.md` are obsolete. Replace with V7's actual phase prompt files: `linear-write.md` (replaces `v6-write.md` for core tracks). Verify whether a seminar variant exists in `scripts/build/phases/` — if no V7 seminar template exists yet, drop that L38 example or replace with `linear-write.md` only with a note that seminars are not yet split out in V7.

---

## Acceptance criteria

1. **Zero `v6_build`, `v6-write`, `v6-review`, `v6-skeleton`, `v6-vocab`, `v6-enrich`, `v6-activities` references** remaining in the 5 files above. Verify with `ugrep -n 'v6_build\|v6-write\|v6-review\|v6-skeleton\|v6-vocab\|v6-enrich\|v6-activities' CLAUDE.md claude_extensions/rules/pipeline.md claude_extensions/skills/code-review/SKILL.md claude_extensions/skills/code-review/code-review-checklist.md claude_extensions/skills/prompt-template-review/template-review-checklist.md` → must return zero lines. Quote the empty grep output in your commit message.
2. **Zero `--range` / `--step` / `--resume` mentions** in the new prose for those 5 files (V7 has none of those flags). Verify: `ugrep -n -- '--range\|--step\|--resume' CLAUDE.md claude_extensions/rules/pipeline.md claude_extensions/skills/code-review/SKILL.md claude_extensions/skills/code-review/code-review-checklist.md claude_extensions/skills/prompt-template-review/template-review-checklist.md`.
3. **CLAUDE.md L101 event names match `linear_pipeline.py` emit_event call sites.** Quote the grep output (`grep -nE 'emit_event\(\s*"' scripts/build/linear_pipeline.py | sort -u`) in your commit message as evidence (per `#M-4` deterministic-over-hallucination rule).
4. **`scripts/build/v6_build.py` is NOT deleted** from disk. (`ls scripts/build/v6_build.py` still resolves.)
5. `npm run claude:deploy` runs clean and the deployed `.claude/rules/pipeline.md` reflects the V7-only framing. Run it; verify no diff explosion.
6. Pre-commit chain: `.venv/bin/ruff check .` clean (no Python touched, but run anyway); markdown lint with `.markdownlint.json` should not regress (don't modify `.markdownlint.json` per `AGENTS.md:11-26`).
7. Conventional commit message: `docs: V7-only sweep across CLAUDE.md + pipeline rule + 3 skill files`. Body must include the four grep outputs cited in ACs 1-3 as raw output blocks (per `#M-4` evidence requirement).

---

## #M-4 (deterministic-over-hallucination) preamble

Verifiable claims this brief makes — and the deterministic source for each:

| Claim | Source |
|---|---|
| V7 entry point is `scripts/build/v7_build.py` with positional `level slug` only | `.venv/bin/python scripts/build/v7_build.py --help` |
| V7 phase prompts live at `scripts/build/phases/linear-{write,review-dim,writer-correction}.md` | `ls scripts/build/phases/linear-*.md` |
| V7 emits 3 named JSONL error events (no module/batch lifecycle events) | `grep -nE 'emit_event\(\s*"' scripts/build/linear_pipeline.py \| sort -u` |
| Specific line refs in 5 files have v6 references | The grep output captured at handoff time (re-run before editing to confirm offsets haven't drifted) |

When making the edits, re-run each command above and use its raw output, not the orchestrator's quoted summary. If any source disagrees with what's stated in this brief — STOP, report the discrepancy, do not write to disk.

---

## Pre-submit checklist (mandatory — from AGENTS.md:11-26)

- [ ] `.python-version` unchanged (`3.12.8`)
- [ ] `.yamllint` and `.markdownlint.json` unchanged
- [ ] No `status/*.json`, `audit/*-review.md`, `review/*-review.md` artifacts in diff
- [ ] No `sys.executable` (use `.venv/bin/python`)
- [ ] No `@pytest.mark.skip` with empty `pass` bodies
- [ ] No assertions weakened
- [ ] Every changed file directly related to the task
- [ ] Total files changed < 20
- [ ] Code runs without `NameError` / `KeyError` / `ImportError`

---

## Workflow steps (numbered, mandatory)

1. `git worktree add -b codex-v6-v7-doc-sweep .worktrees/codex-v6-v7-doc-sweep origin/main`
2. `cd .worktrees/codex-v6-v7-doc-sweep`
3. Re-run the source-of-truth probes from the #M-4 table above; capture outputs.
4. Edit the 5 files per the per-file guidance above.
5. Run `ugrep` ACs from §Acceptance criteria; ALL must return zero lines.
6. `.venv/bin/ruff check .` (no Python touched but verify zero regression).
7. `npm run claude:deploy` and check the deployed mirrors are consistent.
8. `git add -p` (specific files only — no `git add .`); `git commit -m "docs: V7-only sweep across CLAUDE.md + pipeline rule + 3 skill files"` with body containing the grep evidence blocks.
9. `git push -u origin codex-v6-v7-doc-sweep`.
10. `gh pr create` with title `docs: V7-only sweep across CLAUDE.md + pipeline rule + 3 skill files` and body matching the commit body.
11. Do NOT auto-merge. Report PR URL back to orchestrator.
