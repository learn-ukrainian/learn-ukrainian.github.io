# Dispatch: detect Gemini repetition-hallucination in `bulk_ocr_gemini.py` (#2001)

## Why this matters

Second quality sweep over OCR'd files (after PR #2115 filter-hardening) found
a **NEW failure mode the existing filter cannot catch**:
**repetition hallucination**. Gemini Vision falls into a generation loop and
outputs the same line/phrase tens or hundreds of times before stopping.

The output looks structurally Ukrainian (Cyrillic, italics markup, `див.`
cross-references) so the refusal/completion-meta regexes don't trip. But it's
not a real ESUM page — the model invented fake morphological variants or got
stuck repeating a single cross-reference line.

**41 files** identified in production output. Worst cases:

| File | Most-line repeat count | Tail unique / 30 | Size |
|---|---|---|---|
| vol3/p0293 | **2,431** | 2 | 147 KB |
| vol3/p0046 | **1,365** | 3 | 145 KB |
| vol4/p0281 | **1,073** | 4 | 135 KB |
| vol3/p0303 | 566 | 4 | 134 KB |
| vol3/p0091 | 482 | 5 | 130 KB |
| vol3/p0011 | 508 | 7 | 111 KB |
| vol3/p0421 | 211 | 9 | 127 KB |

All 41 quarantined to `data/raw/esum/gemini-ocr/_quarantine/2026-05-18-repetition-hallucination/`
(gitignored). They will be re-OCR'd by the next refire of the bulk runner.

## Detection heuristic that found these 41

Run this against any OCR'd `.md`:

```python
from collections import Counter
lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 5]
counter = Counter(lines)
_, most_count = counter.most_common(1)[0]
tail_unique = len(set(lines[-30:]))
is_repetition = most_count >= 5 and tail_unique < 10
```

Both conditions are needed to avoid false positives on ESUM cross-reference
pages (which DO have legitimate `див. *X*.` repeats but the tail stays diverse).
The 326 "borderline" cases (only one condition met) are explicitly NOT
quarantined — they're heavy-cross-reference pages, not hallucinations.

## Files

- `scripts/etymology/bulk_ocr_gemini.py` — add `is_repetition_hallucination()`
  function and call it inside `is_low_quality_output()`. Read the surrounding
  context first (around line 414-474). Follow the existing pattern style:
  module-level compiled regexes + a function that returns `bool`.
- **New test cases**: extend `tests/etymology/test_bulk_ocr_quality.py` with
  4 new tests. Do NOT create a new file.
- **Sample fixtures**: `data/raw/esum/gemini-ocr/_quarantine/2026-05-18-repetition-hallucination/`
  — read 2-3 of these to ground your implementation in real shapes.

## What to do (verifiable steps)

1. **Worktree setup.** You were spawned with `--worktree`. Verify:

   ```bash
   git rev-parse --show-toplevel
   git branch --show-current
   ```

   Quote raw output. Confirm you are NOT on main.

2. **Read the failure corpus first.** Tail 30 lines of 2-3 quarantined files:

   ```bash
   tail -30 data/raw/esum/gemini-ocr/_quarantine/2026-05-18-repetition-hallucination/vol3/p0421.md
   tail -30 data/raw/esum/gemini-ocr/_quarantine/2026-05-18-repetition-hallucination/vol3/p0293.md
   tail -30 data/raw/esum/gemini-ocr/_quarantine/2026-05-18-repetition-hallucination/vol4/p0281.md
   ```

   Quote the literal repetition pattern from one of them in the PR body.

3. **Add `is_repetition_hallucination()`** to
   `scripts/etymology/bulk_ocr_gemini.py`. Implement the heuristic above.
   Required signature:

   ```python
   from collections import Counter

   MIN_LINES_FOR_REPETITION_CHECK = 10
   REPETITION_LINE_THRESHOLD = 5       # most-common line appears N times
   REPETITION_TAIL_UNIQUE_MAX = 10     # tail of 30 lines has <N distinct
   REPETITION_TAIL_WINDOW = 30

   def is_repetition_hallucination(text: str) -> bool:
       """True if output shows Gemini-style generation loop (same line repeated)."""
       lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 5]
       if len(lines) < MIN_LINES_FOR_REPETITION_CHECK:
           return False
       most_count = Counter(lines).most_common(1)[0][1]
       tail_unique = len(set(lines[-REPETITION_TAIL_WINDOW:]))
       return most_count >= REPETITION_LINE_THRESHOLD and tail_unique < REPETITION_TAIL_UNIQUE_MAX
   ```

   Then call it from `is_low_quality_output()` — add this line near the top
   (BEFORE the regex pattern loop):

   ```python
       if is_repetition_hallucination(stdout_text):
           return True
   ```

4. **Add 4 tests to `tests/etymology/test_bulk_ocr_quality.py`** (extend the
   existing file; don't create a new one). Required test names:

   - `test_is_low_quality_rejects_repetition_hallucination_extreme` — fixture
     is a synthetic string with one line repeated 100 times (mirrors the
     vol3/p0293 shape). Must return `True`.
   - `test_is_low_quality_rejects_repetition_hallucination_moderate` —
     fixture with one line repeated 10 times in the tail of an otherwise-
     reasonable page. Must return `True`.
   - `test_is_low_quality_accepts_legit_cross_reference_heavy_page` —
     fixture with 4-5 distinct `див. *X*.` lines + body text. Each cross-ref
     repeats no more than 2-3 times. Must return `False` (no false positive).
   - `test_is_repetition_hallucination_short_page_skip` — fixture with only
     5 lines total. Must return `False` (short pages can't trigger).

   Run:

   ```bash
   # venv symlinked from main; run from worktree root
   .venv/bin/python -m pytest tests/etymology/test_bulk_ocr_quality.py -v
   ```

   Quote raw `N passed in M.MMs`.

5. **Run ruff:**

   ```bash
   # venv symlinked from main; run from worktree root
   .venv/bin/ruff check scripts/etymology/bulk_ocr_gemini.py tests/etymology/test_bulk_ocr_quality.py
   ```

   Quote raw output.

6. **Sanity check against the 41-file quarantine corpus.** Run:

   ```bash
   # venv symlinked from main; run from worktree root
   .venv/bin/python -c "
   import sys
   sys.path.insert(0, 'scripts/etymology')
   from bulk_ocr_gemini import is_low_quality_output
   from pathlib import Path
   QUAR = Path('data/raw/esum/gemini-ocr/_quarantine/2026-05-18-repetition-hallucination')
   files = sorted(QUAR.rglob('p*.md'))
   missed = [str(f) for f in files if not is_low_quality_output(f.read_text())]
   print(f'caught={len(files)-len(missed)}/{len(files)}')
   if missed: print('MISSED:', missed)
   "
   ```

   Quote raw `caught=41/41` line. If any miss, tune the thresholds.

7. **Sanity check against the existing live tree** — confirm no false positives
   on clean pages:

   ```bash
   # venv symlinked from main; run from worktree root
   .venv/bin/python -c "
   import sys
   sys.path.insert(0, 'scripts/etymology')
   from bulk_ocr_gemini import is_low_quality_output
   from pathlib import Path
   ROOT = Path('data/raw/esum/gemini-ocr')
   live = sorted([p for p in ROOT.rglob('p*.md') if '_quarantine' not in str(p)])
   bad = [str(f) for f in live if is_low_quality_output(f.read_text())]
   print(f'false_positives={len(bad)}/{len(live)}')
   if bad: print('FALSE POSITIVES (first 10):', bad[:10])
   "
   ```

   Quote raw `false_positives=N/M` line. Should be **0 false positives** —
   if non-zero, eyeball each and either confirm the page IS bad (rare new
   discovery) or tune the thresholds. Document the call either way.

8. **Commit + push + PR.** Conventional commit message:

   ```
   fix(etymology/ocr): reject Gemini repetition-hallucination output (#2001)
   ```

   PR body includes the verifiable claims below.

9. **DO NOT MERGE.** PR opens, CI runs, human reviews.

## Verifiable claims required in the PR body

Per `docs/best-practices/deterministic-over-hallucination.md`:

| Claim | Evidence |
|---|---|
| "Pattern sourced from real failures" | one literal tail snippet quote from quarantine sample |
| "All 41 quarantined files rejected" | raw `caught=41/41` |
| "Zero false positives on existing live tree" | raw `false_positives=0/N` |
| "Tests pass" | raw `pytest -v` summary line: `N passed in M.MMs` |
| "Lint clean" | raw `ruff check` final line |
| "Commit landed" | raw `git log -1 --oneline` |
| "PR opened" | raw `gh pr view --json url` |

## Out of scope (do NOT do)

- Do NOT touch the running OCR process or re-fire it. The orchestrator
  (Claude) owns the run lifecycle.
- Do NOT delete or modify the quarantined files.
- Do NOT extend the script's CLI, change defaults, or refactor unrelated
  functions.
- Do NOT auto-merge the PR.
- Do NOT investigate the 326 "borderline" cases — they're a follow-up.

## Acceptance

- PR opens at `https://github.com/.../pull/N`
- `Test (pytest)` blocking CI green
- `Ruff` CI green
- PR body includes all 7 verifiable-claim evidence lines
- Closes a follow-up note on #2001 referring back to the QA discovery

## Pointers

- Issue: `gh issue view 2001`
- Prior filter PR (refusal+meta): #2115
- Quarantine corpus: `data/raw/esum/gemini-ocr/_quarantine/2026-05-18-repetition-hallucination/`
- Existing filter code: `scripts/etymology/bulk_ocr_gemini.py:414-474`
- Test file to extend: `tests/etymology/test_bulk_ocr_quality.py` (added by PR #2115)
- Trailer: every commit gets `X-Agent: codex/2001-ocr-repetition-filter`
