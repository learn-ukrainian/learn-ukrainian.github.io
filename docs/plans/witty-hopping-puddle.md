# Plan: Single-Session Self-Audit Architecture

## Context

The current pipeline generates content in one Gemini session, then runs audit externally, builds a fix prompt, and dispatches to a NEW Gemini session that has zero context about what it wrote or why. This causes 2-7 fix loop iterations per module, wasting tokens and degrading quality.

The user's request: "when LLM finds errors he should fix it right away and don't loop for fix loops and give it more time."

**Goal**: Gemini generates content → runs audit → fixes issues → re-runs audit, all in ONE session with full context. Estimated savings: 3-40 minutes per module build.

## Architecture

Gemini already has FULL-EXECUTION mode (`allow_write=True` in `dispatch_gemini()`), which grants bash + read/write file access via `-y` flag. The validate fix loop already uses this mode. The change: use it for the **content phase** too, so Gemini can write content, run `audit_module.sh`, read audit output, fix in-place, and loop — all in one session.

```
BEFORE: Content (stdout) → Python audit → Fix prompt → NEW Gemini session → loop N times
AFTER:  Content+SelfAudit (allow_write) → Write file → Run audit → Fix → Re-audit → Done
        Validate phase becomes lightweight (just verify + activity/vocab fixes)
```

## Changes

### 1. New file: `claude_extensions/phases/gemini/_shared-self-audit.md`

Self-audit instruction snippet injected via `{SELF_AUDIT_SNIPPET}` placeholder:

- Tells Gemini to write content to `{CONTENT_PATH}` using write_file
- Run `scripts/audit_module.sh {CONTENT_PATH} --skip-activities --no-rag-verify`
- Parse audit output for PASS/FAIL
- If FAIL: read violations, fix content in-place, re-run audit (max 2 iterations)
- Output final content between `===CONTENT_START===`/`===CONTENT_END===` and audit result between `===SELF_AUDIT_START===`/`===SELF_AUDIT_END===`

### 2. Modify `claude_extensions/phases/gemini/beginner-content.md`

Add `{SELF_AUDIT_SNIPPET}` between "Pre-Submission Checks" and "Output Format" sections. The Output Format section stays — Gemini writes to file AND outputs between delimiters for pipeline verification.

### 3. Modify `scripts/pipeline_lib.py` — `phase_2_content()`

In the dispatch call (~line 3259):
- Change from `stdout_only=True` (no write access) to `allow_write=True` (full execution)
- Increase timeout from 600s to 1200s
- Add `SELF_AUDIT_SNIPPET` to overrides dict (reads `_shared-self-audit.md`)
- After dispatch, extract `===SELF_AUDIT_START===` content and log it
- Set `self_audited` flag on state if audit passed

### 4. Modify `scripts/pipeline_v5.py`

- Add `TIMEOUT_CONTENT_SELFAUDIT = 1200` constant (20 min for generate+audit+fix)
- In `phase_content()`: extract self-audit result, save to orchestration, mark state
- In `phase_validate()`: if content was self-audited, reduce max fix iterations from 6 to 2

## Key Design Decisions

1. **Why still output between delimiters?** Pipeline needs stdout capture for word count verification and fallback if file write fails.
2. **Why `--skip-activities --no-rag-verify`?** Activities don't exist yet during content phase. RAG is slow network I/O.
3. **Why max 2 self-fix iterations?** Each audit+fix ~60-90s. 2 iterations keeps content phase under 15 min. Validate phase catches remaining issues.
4. **Why keep validate phase?** It validates activities+vocab (generated after content), runs deterministic checks (more reliable than LLM self-checking), and serves as a safety net.

## Files to Modify

| File | Change |
|------|--------|
| `claude_extensions/phases/gemini/_shared-self-audit.md` | **NEW** — self-audit instructions |
| `claude_extensions/phases/gemini/beginner-content.md` | Add `{SELF_AUDIT_SNIPPET}` placeholder |
| `scripts/pipeline_lib.py` | `phase_2_content()`: `allow_write=True`, timeout, self-audit extraction |
| `scripts/pipeline_v5.py` | `TIMEOUT_CONTENT_SELFAUDIT`, lighter validate when self-audited |

## Verification

1. Rebuild M11 with `--rebuild`: `.venv/bin/python scripts/build_module.py a1 11 --rebuild`
2. Check orchestration folder for `self-audit-output.md`
3. Verify validate phase skips/reduces fix loops
4. Compare total build time vs previous builds
