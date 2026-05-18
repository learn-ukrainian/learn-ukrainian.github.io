# Dispatch: harden `bulk_ocr_gemini.py` quality filter against refusal + completion-meta leaks (#2001)

## Why this matters

QA pass over the 1,862 already-OCR'd `.md` files at
`data/raw/esum/gemini-ocr/` found **18 corrupt outputs** that survived the
existing `is_low_quality_output()` filter. Three new failure shapes:

1. **Bare refusal** (1 file, e.g. `vol4/p0078.md` 532 B): Gemini refuses to
   process the image and emits chat-shaped refusal text only.
2. **Mixed: legit + refusal** (9 files, sizes 8 KB – 182 KB): real
   transcription followed by hallucinated continuation then a refusal block.
3. **Mixed: legit + completion-meta / tool-schema leak** (8 files): real
   transcription followed by either self-praise (`"I have successfully
   transcribed..."`) or Gemini's internal tool-call schema dump
   (`update_topic{strategic_intent:...,summary:...}`).

The 18 files have been moved to
`data/raw/esum/gemini-ocr/_quarantine/2026-05-17-corrupt-refusal-meta/`
(gitignored) and will be re-OCR'd by the next refire of the bulk runner
(idempotent on missing `.md`). **The filter must learn these signatures so
new leaks during the remaining 1,829-page run do not re-pollute the data.**

Full findings + sample matches:
https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/2001#issuecomment-4472282658

## Files

- `scripts/etymology/bulk_ocr_gemini.py` — patch `is_low_quality_output()`
  and `strip_planning_preamble()` around lines 414-474. Read the surrounding
  context first; the existing patterns `MIN_OUTPUT_BYTES`, `CONTROL_GARBAGE_RE`,
  `PREAMBLE_CTRL_RE`, `PREAMBLE_UPDATE_TOPIC_RE`, `CYRILLIC_RUN_RE` are the
  reference style.
- **New test file**: `tests/etymology/test_bulk_ocr_quality.py`
- **Sample fixtures**: `data/raw/esum/gemini-ocr/_quarantine/2026-05-17-corrupt-refusal-meta/`
  — read 2-3 of these to ground your regex design in the actual leak shapes.

## What to do (verifiable steps)

1. **Worktree setup.** You were spawned with `--worktree`. Verify:

   ```bash
   git rev-parse --show-toplevel
   git branch --show-current
   ```

   Quote raw output. Confirm you are NOT on main.

2. **Read the failure corpus first.** Before designing regexes, read at least
   3 of the quarantined files:

   ```bash
   cat data/raw/esum/gemini-ocr/_quarantine/2026-05-17-corrupt-refusal-meta/vol4/p0078.md
   tail -20 data/raw/esum/gemini-ocr/_quarantine/2026-05-17-corrupt-refusal-meta/vol2/p0301.md
   sed -n '5155,5165p' data/raw/esum/gemini-ocr/_quarantine/2026-05-17-corrupt-refusal-meta/vol3/p0001.md
   ```

   Quote one match per category (refusal, completion-meta, update_topic-trailing)
   in your PR body so reviewers can verify your regexes target real shapes.

3. **Patch `is_low_quality_output`** in `scripts/etymology/bulk_ocr_gemini.py`.
   Add a new module-level constant `REFUSAL_AND_META_PATTERNS` containing
   compiled regexes for these signatures (case-insensitive where appropriate):

   **Refusal patterns:**
   - `\bas an AI\b`
   - `\bI cannot (?:directly )?(?:see|read|OCR|process|view|access|perform)\b`
   - `\bI can only (?:process|see|read|handle)\b`
   - `\bplease (?:paste|provide|share|attach)\b`
   - `\bI(?:'ll| will) (?:do my best|try|attempt)\b`
   - `\bI(?:'m| am) (?:unable|not able) to\b`
   - `\bcannot directly\b`
   - `\bif you can provide\b`
   - `\bI apologize, but\b`

   **Completion-meta patterns:**
   - `\bI(?:'ve| have) successfully (?:transcribed|completed|finished|processed)\b`
   - `\bAn?\s+excellent\s+(?:start|job|work|page)\b`
   - `\banother page to (?:transcribe|process|do)\b`
   - `\baccording to your instructions\b`
   - `\bmaintaining the two-column\b`
   - `\b(?:transcription|task|page) (?:complete|completed|finished|done)\b`
   - `\bI(?:'ve| have) (?:rendered|preserved|maintained|ensured)\b`

   **Tool-schema leaks:**
   - `update_topic\{strategic_intent:` (anywhere in file — current
     `PREAMBLE_UPDATE_TOPIC_RE` only catches the leading variant
     anchored to `"page number at the (end|bottom)"`)
   - `<\|[\w_]+\|>` (chat-template tokens)
   - `\[(?:INST|SYSTEM|/INST|/SYSTEM)\]` (instruction-template leaks)

   Have `is_low_quality_output()` return `True` if any pattern matches.

4. **Patch `strip_planning_preamble`** to also strip the **trailing**
   `update_topic{...}` schema fragments. The existing leading-anchor regex
   stays; add a new trailing-anchor regex like:

   ```python
   TRAILING_UPDATE_TOPIC_RE = re.compile(
       r"\n?update_topic\{.*\}\s*\Z",
       re.DOTALL,
   )
   ```

   Apply this AFTER the existing strips. **CAUTION:** for mixed-output files,
   stripping the trailing meta might leave behind a partial-page transcript
   that looks valid. The combination of (1) trailing-strip + (2)
   `is_low_quality_output` post-strip refusal-check is intentional: if the
   refusal phrases are still in the middle of the text post-strip, the page
   gets rejected and retried.

5. **Add `tests/etymology/test_bulk_ocr_quality.py`** with one test per
   failure shape. Use the literal text from the quarantined files as
   fixtures, but inline them in the test (don't import them — fixtures
   should be self-contained). Cover:

   - `test_is_low_quality_rejects_bare_refusal` — uses literal vol4/p0078 text
   - `test_is_low_quality_rejects_mixed_refusal_block` — real text + refusal
   - `test_is_low_quality_rejects_completion_meta_self_praise` — vol2/p0511 shape
   - `test_is_low_quality_rejects_trailing_update_topic` — vol2/p0301 shape
   - `test_strip_planning_preamble_removes_trailing_update_topic`
   - `test_is_low_quality_accepts_clean_page` — uses a real clean page text
     (e.g. literal first 30 lines of `vol1/p0100.md` or similar). MUST PASS.
   - **Negative test**: `test_is_low_quality_accepts_legit_apology` — invent
     a hypothetical Ukrainian sentence that LEGITIMATELY contains a word that
     could partially match (the patterns are word-boundaried English; if your
     regexes don't trip on Ukrainian content, this trivially passes).

   Run them with:

   ```bash
   # venv symlinked from main; run from worktree root
   .venv/bin/python -m pytest tests/etymology/test_bulk_ocr_quality.py -v
   ```

   Quote the raw pytest summary line (`N passed in M.MMs`) in the PR body.

6. **Run ruff** on the file you edited:

   ```bash
   .venv/bin/ruff check scripts/etymology/bulk_ocr_gemini.py tests/etymology/test_bulk_ocr_quality.py
   ```

   Quote raw output.

7. **Sanity check against the full quarantine corpus.** Write a small inline
   script that runs each quarantined `.md` through the new
   `is_low_quality_output` and confirms ALL 18 return `True`:

   ```bash
   # venv symlinked from main; run from worktree root
   .venv/bin/python -c "
   import sys
   sys.path.insert(0, 'scripts/etymology')
   from bulk_ocr_gemini import is_low_quality_output
   from pathlib import Path
   QUAR = Path('data/raw/esum/gemini-ocr/_quarantine/2026-05-17-corrupt-refusal-meta')
   files = sorted(QUAR.rglob('p*.md'))
   missed = []
   for f in files:
       if not is_low_quality_output(f.read_text()):
           missed.append(str(f))
   print(f'caught={len(files)-len(missed)}/{len(files)}')
   if missed: print('MISSED:', missed)
   "
   ```

   Quote the raw `caught=18/18` line in the PR body. If any are missed,
   strengthen the regex until they all catch.

8. **Commit + push + PR.** Conventional commit message:

   ```
   fix(etymology/ocr): reject Gemini refusal + completion-meta leaks (#2001)
   ```

   Branch: `codex/etymology-ocr-quality-filter-2026-05-17` (or whatever
   the worktree default gives you).

   PR body includes the verifiable claims below.

9. **DO NOT MERGE.** PR opens, CI runs, human reviews. `AGENT_NO_MERGE=1`
   is enforced.

## Verifiable claims required in the PR body

Per `docs/best-practices/deterministic-over-hallucination.md`:

| Claim | Evidence |
|---|---|
| "Patterns sourced from real failures" | one literal quote per failure category (3 quotes) |
| "All 18 quarantined files now rejected" | raw `caught=18/18` from step 7 |
| "Clean pages still accepted" | the `test_is_low_quality_accepts_clean_page` test passes (cite the test name + raw summary) |
| "Tests pass" | raw `pytest -v` summary line: `N passed in M.MMs` |
| "Lint clean" | raw `ruff check` final line |
| "Commit landed" | raw `git log -1 --oneline` |
| "PR opened" | raw `gh pr view --json url` |

## Out of scope (do NOT do)

- Do NOT touch the running OCR process or re-fire it. The orchestrator
  (Claude) owns the run lifecycle.
- Do NOT delete or modify the quarantined files. They are evidence;
  the next refire of the bulk runner will regenerate them with the
  hardened filter active.
- Do NOT extend the script's CLI, change defaults, or refactor
  unrelated functions. This is a focused leak-detection patch.
- Do NOT auto-merge the PR.

## Acceptance

- PR opens at `https://github.com/.../pull/N`
- `Test (pytest)` blocking CI check green
- `Ruff` CI check green
- PR body includes all 7 verifiable-claim evidence lines above
- Closes a comment on #2001 referring back to the QA comment
  https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/2001#issuecomment-4472282658

## Pointers

- Issue: `gh issue view 2001`
- QA comment with full pattern catalogue: link above
- Quarantine corpus: `data/raw/esum/gemini-ocr/_quarantine/2026-05-17-corrupt-refusal-meta/`
- Existing filter code: `scripts/etymology/bulk_ocr_gemini.py:414-474`
- Trailer: every commit gets `X-Agent: codex/2001-ocr-quality-filter`
