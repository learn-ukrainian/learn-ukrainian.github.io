# Codex brief — Fix `_extract_required_items` over-extraction (m20 residual 6.8 root cause)

## Why (root-caused from the m20 rebuild verify-before-promote)
The de-scaffold fix (#2412) killed the `Крок N:`/`[SN]` leak (m20 went 3.5 REJECT → 6.8 REVISE,
zero rejected dims). But naturalness/tone are stuck at 6.8/7.0 because of a SECOND deterministic
defect: `_extract_required_items` in `scripts/audit/wiki_coverage_gate.py:1170` over-extracts
"vocabulary to introduce". It takes EVERY comma-separated Cyrillic token inside any `(...)` as a
vocab lemma. From the m20 writer_prompt (real output):

```
- Vocabulary to introduce: наприклад, читати                      # "наприклад" (=for example) is NOT vocab
- Vocabulary to introduce: прокидатися, одягатися, умиватися, або -сь після голосних, я, ти   # connectors + pronouns
- Vocabulary to introduce: наприклад, дивитися в дзеркало під час ранкових зборів, поява вставного «л» — дивлюся, л   # whole phrases + single letter "л"
```

The writer then dutifully forced this noise into English prose (module.md):
`"With читати — to read, наприклад, the I-conjugation endings are familiar..."` and
`"For example, дивитися в дзеркало під час ранкових зборів: поява вставного «л» — дивлюся..."`.
Result: mid-paragraph English→Ukrainian register shifts (#R-SINGLE-VOICE-A1) that no A1 learner can read.

## The fix — extract only plausible LEMMAS, drop the noise
In `_extract_required_items`, after pulling parenthetical comma-tokens, FILTER out:
1. **Discourse markers / connectors** (curated stoplist, case-insensitive): `наприклад`, `напр`,
   `тобто`, `тощо`, `або`, `чи`, `та`, `і`, `й`, `а`, `але`, `зокрема`, `наприклад,`. (The recurring
   offender is `наприклад`.)
2. **Multi-word descriptive phrases**: a vocab lemma is 1–2 tokens. Drop any candidate with >2
   whitespace-separated words (e.g. `дивитися в дзеркало під час ранкових зборів`,
   `поява вставного «л» — дивлюся`, `або -сь після голосних`). (Keep 2-word forms like reflexive
   `одягатися` — those are single tokens anyway; the guard is on word-count.)
3. **Pronouns / bare particles / single chars**: `я`, `ти`, `він`, `вона`, `воно`, `ми`, `ви`,
   `вони`, `-ся`, `-сь`, `ся`, `сь`, and any token of length 1 (e.g. `л`).
4. Strip surrounding markdown emphasis/quotes (`*`, `«»`, backticks) before the checks.

The result for the m20 step claims should be the REAL lemmas only:
`читати` / `прокидатися, одягатися, умиватися` / `користуватися, одружуватися` / `дивитися`.

## CRITICAL — keep gate semantics correct
`_extract_required_items` feeds BOTH the writer-prompt obligation render AND the `wiki_coverage`
gate's coverage check. After the fix:
- The gate must STILL require the real lemmas (читати, прокидатися, …) to appear — do not weaken that.
- The gate must NO LONGER require the noise tokens (наприклад, л, phrases). That's the point — they
  were never real obligations.
Run the existing wiki_coverage tests to confirm no regression in legitimate coverage detection.

## Tests (required)
Add `tests/test_extract_required_items_noise.py` (or extend the existing wiki_coverage test module):
- Input the m20 step-1 claim `"...першої дієвідміни (наприклад, читати) [S8]..."` → extracted
  vocabulary == `["читати"]` (NOT `наприклад`).
- Input the step-4 claim with `(наприклад, дивитися в дзеркало під час ранкових зборів)` and
  `поява вставного «л» — дивлюся` → vocabulary contains `дивитися`, and does NOT contain `наприклад`,
  the long phrase, or `л`.
- A claim with a legit 1-word lemma in parens still extracts it (no over-filtering).

## Verification (#M-4 — quote raw)
- `.venv/bin/python -m pytest tests/test_extract_required_items_noise.py tests/test_wiki_coverage_gate.py -q` → final `N passed`.
- `.venv/bin/ruff check scripts/audit/wiki_coverage_gate.py <new test>` → `All checks passed!`.

## Steps (dispatch enforces worktree)
1. Confirm worktree root.
2. Fix `_extract_required_items` + add tests.
3. pytest (new + wiki_coverage suite) + ruff — paste raw final lines.
4. `git commit` conventional (`fix(wiki-coverage): extract only real lemmas, drop discourse-marker/phrase/particle noise (#2389)`); Co-Authored-By line.
5. `git push -u origin <branch>` ; `gh pr create --base main`. **No auto-merge.**
Report PR URL (raw) + the two pytest/ruff lines.
