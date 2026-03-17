# Plan: Preflight Split + Review Issue Hygiene + #937

## Context

Three related blockers preventing A1 module progress:

1. **Preflight architectural flaw**: Single preflight call mixes writer self-check and reviewer adversarial check, routed to the wrong agent. Gemini Pro also hangs on short prompts — Flash works fine.
2. **8 stale review-result issues**: #924, #926, #927, #928, #930, #931, #938, #939 are open but the modules may have been fixed already. No automated way to check/close them.
3. **#937**: Fix loops don't read review findings — they retry blindly instead of targeting the specific issues identified.

---

## Part 1: Split Preflight Into Feasibility + Coherence (new issue)

### Problem
The current preflight prompt says "You are about to build a module" (writer-facing) but routes to the reviewer. Two distinct concerns are conflated:
- **Can the writer execute these instructions?** (internal consistency)
- **Does this prompt implement the plan?** (plan-prompt alignment)

### Design

**Two parallel LLM calls:**

| Check | Agent | Model | Input | Checks |
|-------|-------|-------|-------|--------|
| **Feasibility** | Writer | Gemini Flash | rendered prompt + audit gates | Contradictions, impossible targets, missing instructions |
| **Coherence** | Reviewer | Claude Sonnet | rendered prompt + plan YAML + audit gates | Plan-prompt alignment, missing plan elements, gate achievability |

Both run in parallel via `ThreadPoolExecutor(max_workers=2)`. Results merge into `CombinedPreflightResult` with same `.high_issues`/`.status`/`.issues` interface.

**Critical (from Gemini review #941):**
- **Auto-fix only for feasibility issues.** Coherence issues (missing plan sections, structural misalignment) can't be fixed by regex — they require template/plan rework. If coherence finds HIGH issues → pipeline fails immediately, human must fix.
- **Thread safety:** `log()` in `core.py` is documented as thread-safe, but verify. Both dispatches write to separate files — no shared state. `apply_preflight_fixes` runs AFTER both futures complete (sequential), not inside threads.
- **Sonnet for coherence is a starting point.** For A1 (short plans, simple prompts) Sonnet is fine. If false positive/negative rate is high on complex tracks (B2+/seminar), escalate to Opus. Add a `--coherence-model` override flag for testing.
- **Flash checking Pro's instructions:** Minor capability mismatch risk. Acceptable because feasibility checks are about logical consistency (contradictions, math), not creative capability.

### Files to Change

**`scripts/pipeline/prompt_preflight.py`**:
- Add `source: str = "unknown"` field to `PreflightIssue`
- Add `CombinedPreflightResult` dataclass (aggregates feasibility + coherence)
- New `_FEASIBILITY_PROMPT` — writer self-check (keep current prompt's spirit, tighten focus)
- New `_COHERENCE_PROMPT` — reviewer checks plan-prompt alignment (needs plan YAML context)
- New `build_feasibility_prompt()` and `build_coherence_prompt()` builders
- New `run_feasibility_check()` and `run_coherence_check()` runners
- New `_log_and_save_result()` helper (DRY for logging + YAML save)
- Refactor `run_prompt_preflight()` → thin orchestrator calling both in parallel
- Old `_PREFLIGHT_PROMPT` and `build_preflight_prompt()` → delete

**`scripts/pipeline/core.py`** (single call site ~line 1739):
- Wire two dispatch functions: Flash for feasibility, Claude Sonnet for coherence
- Pass `plan_path=ctx.paths.get("plan")` to `run_prompt_preflight`
- Expand state dict to include `feasibility_status` and `coherence_status`
- `FLASH_MODEL` import already added; add `CLAUDE_SONNET` import

**`tests/test_prompt_preflight.py`**:
- `TestBuildFeasibilityPrompt` — prompt contains rendered content, audit gates, no plan
- `TestBuildCoherencePrompt` — prompt contains plan YAML + rendered content + audit gates
- `TestPreflightIssueSource` — source field propagates through parsing
- `TestCombinedPreflightResult` — status aggregation (PASS+PASS=PASS, etc.)
- `TestRunPromptPreflightCombined` — mock both dispatches, verify parallel execution

### Orchestration Artifacts (per module)

```
preflight-feasibility-prompt.md     # sent to Gemini Flash
preflight-feasibility-output.md     # Flash response
preflight-feasibility-result.yaml   # parsed
preflight-coherence-prompt.md       # sent to Claude Sonnet
preflight-coherence-output.md       # Claude response
preflight-coherence-result.yaml     # parsed
preflight-result.yaml               # combined (backward compat)
```

### Key Decisions
- **Coherence uses Sonnet (default), escalatable to Opus** — Sonnet for A1/A2, may need Opus for complex tracks
- **Coherence gets plan YAML** — essential for checking plan-prompt alignment
- **Auto-fix ONLY for feasibility issues** — coherence HIGH issues → immediate pipeline failure (human must fix template/plan)
- **`dispatch_claude_phase`** for coherence — reuse existing Claude CLI dispatch, phase_label="preflight-coherence" falls to generic delimiter branch (fine for YAML output)
- **Parallel execution** — no data dependency, separate output files, `apply_preflight_fixes` runs after both complete
- **Graceful skip** — if no plan_path, skip coherence (log and continue)

---

## Part 2: Review Issue Hygiene Script (new)

### Problem
8 open `review-result` issues (#924-#939) with detailed findings. No way to check if the module was rebuilt/fixed since the review.

### Design
New script: `scripts/check_review_issues.py`

**Logic per issue (Gemini review hardened):**
1. Parse issue title → extract module slug via regex `Review: (.+)-review-` (e.g., "consonant-sounds")
2. Check module's `state.json` for latest build timestamp AND audit status
3. **Timestamp alone is NOT enough** (Gemini's point) — module could rebuild and still fail
4. Run `audit_module.py` to verify ALL gates pass (word count, activities, etc.)
5. If all gates GREEN → close issue with comment citing gate results
6. If any gate FAILS → leave open, add comment with current gate status

**Long-term:** Integrate into pipeline — after successful review phase pass, auto-close matching GH issues. But the script solves the immediate backlog.

**Usage:**
```bash
.venv/bin/python scripts/check_review_issues.py [--close] [--dry-run]
```

### Files
- `scripts/check_review_issues.py` — new script
- No pipeline changes needed (long-term: add auto-close to review phase)

---

## Part 3: #937 — Feed Review Findings Into Fix Loops

### Problem
Fix loops retry blindly. Review issues contain structured findings (Issue 1, Issue 2, etc.) that should be injected into fix prompts.

### Design
This is a larger feature that depends on Parts 1-2 working. Scope for this session:

1. **Parse review findings from `review-result.md`** — already structured with `### Issue N:` headers
2. **Extract structured fix targets** — per-issue: location, problem, suggested fix (strip conversational filler)
3. **Inject findings into fix prompt with constraints** (Gemini's point): "Fix ONLY these sections. Do NOT rewrite surrounding text. Preserve word count and structure."
4. **After successful fix + audit pass** — update/close the corresponding GH issue

**Gemini's concern addressed:** Blind injection risks full module rewrites. The fix prompt must:
- List specific sections to modify (from review `**Location**` fields)
- Explicitly forbid touching other sections
- Include a "preserve these gates" reminder (word count, immersion, activity count)

### Files
- `scripts/pipeline/core.py` — review fix loop, inject findings
- `scripts/pipeline/parsing_review.py` — extract structured findings, strip filler
- New: `scripts/pipeline/review_findings.py` — structured finding extraction + fix prompt builder

---

## Implementation Order

1. **Create GH issue** for preflight split
2. **Implement Part 1** (preflight split) — `prompt_preflight.py` → `core.py` → tests
3. **Run /simplify** on changed code
4. **Send to Gemini** for adversarial review
5. **Implement Part 2** (review issue hygiene script)
6. **Implement Part 3** (#937 — feed findings into fix loops)
7. **Close issues** when ACs verified

---

## Verification

### Part 1
```bash
# Tests
.venv/bin/python -m pytest tests/test_prompt_preflight.py -x -v

# Integration test (dry run)
.venv/bin/python scripts/build_module_v5.py a1 3 --restart-from content --preflight-only

# Verify both output files exist
ls curriculum/l2-uk-en/a1/orchestration/consonant-sounds/preflight-*-output.md
```

### Part 2
```bash
.venv/bin/python scripts/check_review_issues.py --dry-run
```

### Part 3
```bash
# After rebuild with fix loop, check if findings were injected
cat curriculum/l2-uk-en/a1/orchestration/consonant-sounds/review-fix-*-prompt.md | grep "Review Findings"
```
