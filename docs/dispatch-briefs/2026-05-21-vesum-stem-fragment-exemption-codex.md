# Dispatch brief — exempt morphological stem fragments from `vesum_verified`

**Agent**: codex (gpt-5.5, xhigh)
**Mode**: danger
**Worktree**: `.worktrees/codex-vesum-stem-2026-05-21` (REQUIRED — per `delegate-must-use-worktree.md`)
**Task ID**: `vesum-stem-exemption-2026-05-21`
**Created**: 2026-05-21

## Why

claude-tools V7 build of `a1/my-morning` (branch `build/a1/my-morning-20260521-101042`) hit **21/22 gates** — closest to first all-green V7 module this week. The lone HARD-failure is `vesum_verified` on a single token: `**користу**` extracted from line 90 of `module.md`:

> Verbs like **користуватися** lose the suffix **-ва-** in the present tense. The stem begins **користу**-, not "користуву-".

`користу` is a **morphological stem fragment** (the verb stem of `користуватися` before the `-ся` postfix and present-tense ending). The writer uses it correctly as a pedagogical demonstration of the `-ва-` drop pattern. VESUM rightly doesn't list bare stems as lemmas, so the gate flags it as missing. ADR-008 has no correction path for this — `python_qg_correction_r1.json` and `_r2.json` both show `vesum_verified: {}` empty (the correction loop couldn't act).

The gate already exempts several pedagogical-fragment classes — postfix fragments (`ся`, `сь`, `тся`...), blank markers (`__X`), syllable-break notation (`за-пи-са-ний` → `записаний`), and phonetic transcriptions / inline code. **Prefix/stem fragments are the missing exemption class.** See the gate code at `scripts/build/linear_pipeline.py::_iter_vesum_word_surfaces` (around line 6318) and the existing exemption helpers `_STANDALONE_POSTFIX_FRAGMENTS` (line 623), `_touches_blank_marker` (line 6383), `_collapse_syllable_break` (line 6350).

## What

Add stem-fragment exemption to `_iter_vesum_word_surfaces`. Mirror the shape of the existing `_touches_blank_marker` / `_touches_latin_letter` helpers exactly — these are precedent for "skip the candidate when the surrounding context tells us it isn't a complete word."

### Detection rule (precise)

A Cyrillic word match is a **stem fragment** when ALL of the following hold:
1. The character immediately after the match end is a hyphen `-` (any of: ASCII `-`, en-dash `–`, em-dash `—` — but stick to ASCII for the first cut; document the others as a follow-up only if you find evidence in the corpus).
2. The character AFTER that hyphen is NOT a Cyrillic letter — i.e., it's whitespace, punctuation (period, comma, closing quote), end-of-string, or markdown-closing markers (`*`, `_`, backtick, `)`, `]`, `,`).
3. (Optional gate to avoid false positives) The character BEFORE the match start is a markdown-bold/italic opener (`*` or `_`) or whitespace — this restricts the rule to ATTRIBUTED stem demonstrations and avoids accidentally exempting compound-word leaders like `Івано-` in `Івано-Франківськ` where rule (2) already filters but the extra anchor adds safety.

The negative side of rule (2) is what protects real compound nouns like `темно-синій` and `Івано-Франківськ` — the next char IS a Cyrillic letter, so the rule says "this is a compound, not a stem."

### Touch points

1. **`scripts/build/linear_pipeline.py`**:
   - Add a new helper `_looks_like_stem_fragment(text: str, start: int, end: int) -> bool` near `_touches_blank_marker` (around line 6383). Keep it short and well-commented — include a one-line reference to the gate-failure case that motivated it (claude-tools build a1/my-morning 2026-05-21).
   - Call it inside `_iter_vesum_word_surfaces` after the existing `_touches_latin_letter` check and before the `word = raw.strip(...)` line. `continue` to skip the candidate when it fires.

2. **Tests** (`tests/`):
   - Add unit tests for `_looks_like_stem_fragment` directly: positive case (`**користу**-, not "користуву-"`), positive with single asterisk (`*користу*-`), positive with backtick (`` `користу-` ``), negative for real compound (`темно-синій`, `Івано-Франківськ`, `я-форма`), negative when there is no trailing hyphen.
   - Add a `_vesum_gate`-level integration test that feeds the exact failing prose ("Verbs like **користуватися** lose the suffix **-ва-** in the present tense. The stem begins **користу**-, not \"користуву-\".") and asserts `missing == []`. Pick a fixture pattern that already exists in `tests/test_vesum_*` or `tests/build/test_linear_pipeline.py` and follow it.
   - Do NOT loosen the gate on real test corpora — keep the existing exemption tests passing. Run `pytest -k vesum` and make sure the existing pass count stays ≥ current + new tests.

3. **Documentation** — none unless `docs/best-practices/audit-standards.md` or similar already documents the exemption list, in which case add stem-fragments there. Do not invent new docs.

## Don't

- Don't widen the rule to anything that doesn't end with a hyphen. The hyphen is the canonical stem-notation signal in Ukrainian grammar texts.
- Don't strip the hyphen earlier in the pipeline as an alternative path — keep `_iter_vesum_candidate_words` behavior unchanged.
- Don't touch the writer prompt as part of this PR. A separate prompt-side directive is a follow-up if false positives surface; for now the gate fix is the canonical one.
- Don't refactor `_iter_vesum_word_surfaces` beyond adding the one early-continue branch.

## Verification before commit

```
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/ruff check scripts/build/linear_pipeline.py tests/
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python -m pytest tests/ -k 'vesum or linear_pipeline' -v --tb=short
```

All green required before commit. Per `#M-7` in `memory/MEMORY.md`: pre-commit hook is not a test run.

## Commit + PR shape

- **Branch**: `fix/vesum-stem-fragment-exemption-2026-05-21`
- **Single commit** with conventional message: `fix(vesum_verified): exempt morphological stem fragments (X- not followed by Cyrillic letter)`
- **PR title**: `fix(vesum_verified): exempt morphological stem fragments`
- **PR body**: explain the build #5 single-token failure (claude-tools a1/my-morning, branch `build/a1/my-morning-20260521-101042`), link this brief, name the gate-code touch point.
- **Do NOT auto-merge.** Orchestrator (Claude) reviews and merges after `gh pr checks {N} --watch` passes.

## Steps (mandatory per dispatch-brief checklist)

1. `git worktree add -B fix/vesum-stem-fragment-exemption-2026-05-21 .worktrees/codex-vesum-stem-2026-05-21 origin/main`
2. Implement the helper + the `_iter_vesum_word_surfaces` patch.
3. Add unit tests + integration test with the exact failing prose as fixture.
4. Run verification commands.
5. Single conventional commit.
6. `git push -u origin fix/vesum-stem-fragment-exemption-2026-05-21`
7. `gh pr create --title ... --body ...` (NO auto-merge).
8. Report task done.

## Anti-fabrication (per #M-4)

Every claim of "tests pass" / "ruff clean" / "PR opened" in the final report MUST be backed by literal command output (cmd + cwd + raw last lines). A bare "all green" with no transcript is invalid.
