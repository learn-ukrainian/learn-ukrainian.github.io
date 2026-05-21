# Dispatch brief — preserve 17 Gemini OCR hallucination samples as detection fixtures

**Agent**: gemini (default model)
**Mode**: danger
**Worktree**: `.worktrees/dispatch/gemini/gemini-hallucination-fixtures-2026-05-21` (REQUIRED)
**Task ID**: `gemini-hallucination-fixtures-2026-05-21`
**Issue**: #2177
**Created**: 2026-05-21

## Why

During the dead Gemini-2.5 re-OCR project (now killed — see `docs/session-state/2026-05-21-issue-2001-ocr-handoff.md`), we quarantined 17 files with various hallucination patterns:

- 10 large repetition-loops (caught by existing shadow uniqueness check)
- 6 single-line repetition-loops (caught by a NEW substring-repetition check — gap in the existing shadow check)
- 1 semantic hallucination (fake cognates, caught by ESUM MCP fact-check)

Quarantined at `data/raw/esum/gemini-ocr/_quarantine/2026-05-19-repetition-hallucination/` (gitignored, local only). These are valuable as test fixtures for any future visual-OCR pipeline — they document the exact failure shapes vision-LLM OCR produces on dense print. **Do not let them rot in a gitignored folder.**

## What

Promote the 17 samples to committed test fixtures and ship a detection function with pytest coverage that flags all 17 and does NOT flag clean ESUM entries.

### Steps in detail

1. **Copy samples** → `tests/fixtures/etymology/gemini-hallucinations/` (committed). 17 files. Keep the existing `vol{N}_p{NNNN}.md` naming. Include a tiny `README.md` in that directory describing what these are and which check should fire on each (10 + 6 + 1 split).

2. **Detection function**: add `is_gemini_hallucination(text: str) -> tuple[bool, str]` (returns `(flagged, reason)`) in a new module `scripts/etymology/hallucination_detector.py`. The function combines:
   - **Shadow uniqueness check** — extract the current logic from `scripts/etymology/bulk_ocr_gemini.py::is_low_quality_output` (or whatever the current name is — `grep` for shadow-uniqueness logic). Reuse, do not re-derive.
   - **NEW substring-repetition check** for short files (gap-closer) — see spec below.
   - **Optional**: stub for "semantic hallucination" with a comment that it needs RAG verification and is not currently automated. Do NOT implement the RAG path in this dispatch.

3. **Substring-repetition spec**:

   ```python
   def has_substring_repetition(text: str, window: int = 30, threshold: int = 5) -> bool:
       """Detect repetition-loop in short files (<100 lines).

       Returns True if any window-char substring appears threshold+ times.
       Catches single-line cases like
         "**пра́во** ... полаб. *provü*, схв. *пра̏во* ..." × 9
       that the shadow uniqueness check skips due to its <100-line guard.

       The existing shadow check has `if len(lines) < 100: continue` — this is the gap
       this function closes. Used in conjunction with, not as a replacement for, shadow uniqueness.
       """
   ```

   Tune `window` and `threshold` against the 6 quarantined single-line samples until they all flag, AND a random sample of clean ESUM entries (from `data/processed/esum_vol{1..6}.jsonl`) does NOT flag.

4. **Pytest** (`tests/etymology/test_hallucination_detector.py`):
   - **Positive cases**: loop over all 17 fixtures; each must trip `is_gemini_hallucination(text)[0] == True`. Identify which detector (`shadow` vs `substring` vs `semantic-stub`) flagged it. Assert at least 10 shadow flags + 6 substring flags (the 1 semantic-hallucination sample currently has no automated detector — note it in the test as a `@pytest.mark.skip(reason="needs RAG verification, see autopsy")`).
   - **Negative cases**: pull 10 random clean entries from `data/processed/esum_vol1.jsonl`; each must NOT flag.
   - Use `pytest.parametrize` over the fixture list.

5. **Autopsy** at `docs/bug-autopsies/gemini-ocr-hallucinations.md`. Update `docs/bug-autopsies/INDEX.md` with a one-liner. Cover:
   - **What broke**: Gemini-2.5-flash emitted etymologically-plausible content for a DIFFERENT page than the one in the input image. ~97% wrong-page rate.
   - **Why**: vision-LLM OCR on dense print at scale conflates "what this kind of page looks like" with "what THIS page says." See bake-off REPORT for cross-validation evidence.
   - **Detection gaps**: shadow uniqueness skipped short files (the <100-line guard); semantic hallucination undetectable without RAG fact-check.
   - **Prevention**: before launching an OCR pipeline, check the source's existing metadata/text formats on its host (IA had clean text layers the whole time — issue #2001 was solving an already-solved problem). For any future visual-OCR experiment, ship a semantic-diff gate against a baseline OCR (Tesseract scored 0.92 semantic_acc; Gemini 0.03).

### Acceptance gates

- **17/17 positive flags**: every quarantined fixture trips the detector (16 by automated checks; 1 marked `xfail` / `skip` for the semantic case).
- **0/10 negative flags**: 10 random clean ESUM entries pass.
- **Pytest green**: `.venv/bin/python -m pytest tests/etymology/ -v`.
- **Ruff green**: `.venv/bin/ruff check scripts/etymology/ tests/etymology/`.
- **Autopsy + INDEX entry committed.**

## Don't

- Don't ship a RAG-based semantic detector — that's a multi-day scope and outside this issue.
- Don't move or delete the existing quarantine dir — leave it where it is; this dispatch COPIES 17 files into `tests/fixtures/`.
- Don't modify `scripts/etymology/bulk_ocr_gemini.py` (the OCR script itself is preserved for future visual-OCR experiments; this dispatch only extracts a reusable detector).
- Don't change the existing shadow-uniqueness check's behavior on long files. Encapsulate it; don't rewrite it.

## Verification before commit

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian && ls tests/fixtures/etymology/gemini-hallucinations/ | wc -l   # expect 17 + 1 README = 18
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/ruff check scripts/etymology/ tests/etymology/
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python -m pytest tests/etymology/ -v --tb=short
```

All green required before commit.

## Commit + PR shape

- **Branch**: `feat/gemini-ocr-hallucination-detector-2026-05-21`
- **One commit** (fixtures + detector + tests + autopsy together — coherent feature).
- **PR title**: `feat(etymology): Gemini OCR hallucination detector + 17 fixture samples`
- **PR body**: link issue #2177, link this brief, paste pytest summary, note the substring-repetition spec parameters chosen.
- **Do NOT auto-merge.** Orchestrator reviews and merges.

## Steps (mandatory)

1. `git worktree add -B feat/gemini-ocr-hallucination-detector-2026-05-21 .worktrees/dispatch/gemini/gemini-hallucination-fixtures-2026-05-21 origin/main`
2. `cp -R data/raw/esum/gemini-ocr/_quarantine/2026-05-19-repetition-hallucination/*.md tests/fixtures/etymology/gemini-hallucinations/`
3. Locate existing shadow-uniqueness check (`grep -n` in `scripts/etymology/`). Extract; encapsulate.
4. Implement substring-repetition check, tune against the 6 single-line samples.
5. Write `scripts/etymology/hallucination_detector.py` combining both.
6. Write `tests/etymology/test_hallucination_detector.py` with parametrized positives + negatives.
7. Write autopsy + INDEX entry.
8. Run verification; iterate until green.
9. Single conventional commit.
10. `git push -u origin feat/gemini-ocr-hallucination-detector-2026-05-21`
11. `gh pr create --title ... --body ...` (NO auto-merge).
12. Report task done with pytest summary + the substring spec params chosen.

## Anti-fabrication (per #M-4)

Every "tests pass" / "ruff clean" / "PR opened" / "17/17 positives flagged" claim MUST be backed by literal command output (cmd + cwd + raw last lines). Quote the actual pytest line, the actual fixture count from `ls | wc -l`. Don't paraphrase.
