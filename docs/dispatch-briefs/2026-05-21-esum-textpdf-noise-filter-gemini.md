# Dispatch brief — text-pdf parser noise filter (closes #2183)

**Agent**: gemini (default model)
**Mode**: danger
**Worktree**: `.worktrees/dispatch/gemini/esum-textpdf-noise-filter-2026-05-21` (REQUIRED)
**Task ID**: `esum-textpdf-noise-filter-2026-05-21`
**Issue**: #2183
**Created**: 2026-05-21 evening

## Why

After the corpus pivot to text-pdf for all 6 ESUM vols (commit `be4c86e00b`), spot-checks revealed ~20% noise in lemma extraction: backmatter colophon entries (`видавництво`, `виготовлено`, `НВП`, `ТОВ`, `укладачі`, `последний`), bibliography blocks (`СУМ 9, 763; Бупр. Ш 222`), and single-character / OCR-garbage entries (`і, п, т, і£і, ргазкас`). See #2183 for the full noise table per vol.

The relaxed entry-start heuristic in `--source-format text-pdf` (min-length 5 chars, no punctuation requirement on cross-references) was tuned to catch legit short entries but also catches these structural artifacts.

## What

Tighten `scripts/ingest/esum_ingest.py` text-pdf branch with three layers of defense, in order of preference:

### Layer 1 (must-have) — `_strip_front_and_back_matter` colophon detection for text-pdf

The existing function strips front and back matter on the djvutxt anchor (`BODY_END_RE`). text-pdf has different anchors. Add a text-pdf-specific tail trim that detects colophon markers:

```python
COLOPHON_MARKERS_RE = re.compile(
    r"\b(видавництв[оа]|виготовлен[ао]|укладач[іа]?|редактор[иа]|редколегі[яї]|"
    r"наукове видання|підписано до друку|формат|папір офсет|друк офсет|"
    r"гарнітура|умов[нi]?\.? друк\.? арк\.|тираж|зам\.|"
    r"АН України|НВП|ТОВ|ВАТ|ПП)\b",
    re.IGNORECASE,
)
```

Apply: scan from the END of the cleaned line list; once a line matches `COLOPHON_MARKERS_RE` AND the next 5 lines also have colophon-shaped content (short lines, no body-of-entry punctuation), truncate the corpus at that point.

This is the canonical fix — addresses the root cause (backmatter slipping through entry detection).

### Layer 2 (must-have) — lemma sanity gate in `parse_esum`

After `_extract_headword` returns a candidate lemma, reject the entry if:

1. Lemma is a single character (`і`, `п`, `т`, `и`).
2. Lemma is mixed-script: any Latin letter (`a-z`, `A-Z`) appearing inside a Cyrillic word (excluding the homonym suffix markers `1`, `2`, `3`, `!`, `?` which are legitimate). Examples to reject: `і£і`, `ргазкас`, `з8оіуь`, `егаепке!`, `угаьіе`, `іїейїма`, `кайап`, `к88`, `пп:`, `кзсря`.
3. Lemma contains digit characters other than as a trailing homonym number (1/2/3 after a Cyrillic stem). Examples to reject: `к88`, `з8оіуь`.
4. Lemma is a known Russian-only headword that shouldn't be a Ukrainian dictionary entry: `последний`, `который`, `этот`, `тот` (just these 4; not a wider RU-detection — RU words appear legitimately in cognate sections).

Use a helper `_is_sane_lemma(lemma: str) -> bool` near `_extract_headword`. Document each rule with a one-line comment + example from the corpus.

### Layer 3 (optional, if Layer 1 + 2 don't get noise below ~5%) — bibliography-body detector

After entry extraction, if the etymology body matches a pure-bibliography pattern (starts with uppercase abbreviation + space + Roman or Arabic numeral + comma, repeated), reject the entry. Example to catch: `СУМ 9, 763; Бупр. Ш 222; Фасмер Ш 776; Преобр. П 397;` as the *entire* body. Real entries always have prose etymology before any citation cluster.

A simple check: if 80%+ of body characters are within citation-shaped substrings (`[А-Я]+\.? [IVXLCDM\d]+ \d+(--\d+)?`), reject.

Mark Layer 3 as `pytest.mark.optional` if it would be a stretch to fit in the time budget.

## Acceptance gates

After implementing Layer 1 + 2 (Layer 3 only if Layer 1+2 don't hit the target):

1. **Re-parse vol{1..6} text-pdf** into `/tmp/esum_vol${vol}_filtered.jsonl`.
2. **Spot-check noise reduction**:
   - vol1: tail no longer contains `і`, `підганяють`, `угаьіе` as lemma.
   - vol4: tail no longer contains `видавництво`, `виготовлено`, `к88`, `пп:`, `кзсря`.
   - vol5: mid no longer contains `з8оіуь`, `егаепке!`, `никсблод`; tail no longer contains `укладачі`, `нвп`, `тов`, `іїейїма`, `кайап`.
   - vol6: front no longer contains `последний` (×2 currently); tail no longer contains single chars `і, п, т`.
3. **Entry count delta** (acceptable range): each vol should lose between 50 and 500 entries from current; total cleanup ~1,500-3,000 entries removed (target ~5,000-10,000 if Layer 3 is enabled).
4. **No legitimate-entry regressions**: existing tests in `tests/ingest/test_esum_ingest.py` + `tests/test_esum_ingest_pdf.py` must still pass.
5. **New tests**: add unit tests for `_is_sane_lemma` covering each of the 4 rejection rules (positive + negative cases).

DO NOT regenerate `data/processed/esum_vol*.jsonl` or reload `data/sources.db` as part of this dispatch. Leave that to a follow-up commit (Claude will handle, since it requires re-running the manifest + cognate-extraction downstream).

## Don't

- Don't modify the djvutxt branch. The deployed djvutxt source files were removed in commit `7d3ab9d898`, so the djvutxt branch is unused in production, but the tests still exercise it. Keep it unchanged.
- Don't loosen the existing valid-entry checks (`_looks_like_head_candidate`, `_looks_like_entry_start`). The new rejection layers are ADDITIVE.
- Don't add a sanitizer table for Cyrillic→Latin character substitution — that's the scope of issue #2186, a separate dispatch.
- Don't touch `data/processed/` or `data/sources.db`. Leave the corpus reload to a follow-up commit.

## Verification before commit

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/ruff check scripts/ingest/ tests/
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python -m pytest tests/ -k esum -v --tb=short
# Smoke runs on all 6 vols:
for vol in 1 2 3 4 5 6; do
  cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python scripts/ingest/esum_ingest.py --input data/raw/esum/ia-text-pdf/vol${vol}-text.txt --output /tmp/esum_vol${vol}_filtered.jsonl --vol ${vol} --source-format text-pdf 2>&1 | tail -1
done
wc -l /tmp/esum_vol{1..6}_filtered.jsonl
# Sanity-check the rejection on known-noise lemmas:
for noise in видавництво виготовлено укладачі нвп тов і£і ргазкас з8оіуь "к88" последний; do
  echo "=== checking '$noise' ==="
  for vol in 1 2 3 4 5 6; do
    grep -l "\"lemma\": \"${noise}\"" /tmp/esum_vol${vol}_filtered.jsonl 2>/dev/null && echo "STILL PRESENT in vol${vol}"
  done
done
```

All ruff + pytest green required. The noise grep should produce no matches for the rejected lemmas.

## Commit + PR shape

- **Branch**: `feat/esum-textpdf-noise-filter-2026-05-21`
- **Single commit**: `feat(esum): filter colophon + mixed-script noise in text-pdf parser (closes #2183)`
- **PR body**: paste smoke-run wc -l of filtered output, paste grep verification of rejected lemmas, list per-vol entry-count delta.
- **Do NOT auto-merge.**

## Steps (mandatory)

1. `git worktree add -B feat/esum-textpdf-noise-filter-2026-05-21 .worktrees/dispatch/gemini/esum-textpdf-noise-filter-2026-05-21 origin/main`
2. Read `scripts/ingest/esum_ingest.py` end-to-end. Pay attention to: `_strip_front_and_back_matter`, `_extract_headword`, `_looks_like_*` helpers.
3. Implement Layer 1 (colophon strip) — add `COLOPHON_MARKERS_RE` and call site.
4. Implement Layer 2 (lemma sanity gate) — add `_is_sane_lemma` and call site.
5. Optionally Layer 3 (bibliography detector) if needed.
6. Add pytest covering all rejection rules.
7. Run verification commands. Iterate until green AND noise grep is empty for the listed examples.
8. Single conventional commit.
9. `git push -u origin feat/esum-textpdf-noise-filter-2026-05-21`
10. `gh pr create --title "feat(esum): filter colophon + mixed-script noise in text-pdf parser" --body ...` (NO auto-merge)
11. Report task done with the smoke-run wc -l and noise grep output verbatim.

## Anti-fabrication (per #M-4)

Every "tests pass" / "ruff clean" / "noise grep empty" claim MUST be backed by literal command output (cmd + cwd + raw last lines). Quote `wc -l` numbers, pytest summary line, ruff "All checks passed!", and the grep results raw. Don't paraphrase entry counts.
