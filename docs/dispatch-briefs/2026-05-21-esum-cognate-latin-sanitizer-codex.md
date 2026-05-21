# Dispatch brief — recover Latin transliterations in ESUM cognate forms (closes #2186)

**Agent**: codex (gpt-5.5, xhigh)
**Mode**: danger
**Worktree**: `.worktrees/dispatch/codex/esum-cognate-latin-sanitizer-2026-05-21` (REQUIRED)
**Task ID**: `esum-cognate-latin-sanitizer-2026-05-21`
**Issue**: #2186
**Created**: 2026-05-21 evening

## Why

After the ESUM corpus pivot (commit `be4c86e00b`) and manifest regen (`7d3ab9d898`), the cognate-form extraction faithfully preserves the upstream PDF text-layer OCR damage on Latin transliterations of Polish/Czech/Slovak/etc. cognates. Examples:

| Cognate marker | Stored as | Should be | Entry |
|---|---|---|---|
| `п.:` | `зіегдгізку` | `sierdzisty` | сердитий vol5 p216 |
| `ч.:` | `5гбей` | `srdce` | (серце-family) vol5 p222 |
| `п.:` | `5егрепіуп` | `serpentyn` | серпентин vol5 p220 |
| `ч. слц.:` | `8егрепіїп` | `serpentin` | серпентин vol5 p220 |
| `п.:` | `зегдійК` | `serdjuk` (probably) | сердюк vol5 p217 |
| `тур.:` | `5йГіЙК` | (Turkish form, damaged) | сердюк vol5 p217 |

The damage is **systematic, character-class-level confusion** at OCR time:

- `s` → `5` / `з` / `8`
- `r` → `г`
- `i` → `і` / `ї`
- `e` → `е`
- `d` → `б` / `г` / `й`
- `c` → `е`
- `n` → `п` / `н`
- `t` → `к` / `ї`
- `y` → `у` / `ї`
- `z` → `г`
- `j` → `з`
- Uppercase variants follow similar patterns.

This is character-encoding damage in the PDF's text layer — both `pdftotext` and ABBYY OCR would surface it (the PDFs are derived from the same scan). Re-OCR with a vision-LLM was the killed approach (issue #2001 / autopsy `esum-ocr-pivot.md`).

## What

Build a **Cyrillic→Latin recovery sanitizer** that, when applied to cognate-form strings tagged with a non-Cyrillic-script language marker, produces a candidate Latin transliteration and stores it alongside the original.

### Investigation phase (do this first; ~30 min)

1. **Re-download one ABBYY XML file** (e.g. vol1: `https://archive.org/download/etslukrmov1/etslukrmov1_abbyy.gz`). Decompress. Search the `<charParams>` data for a Polish cognate form (e.g., near лемма `адміністрація` or any vol1 lemma whose Polish cognate appears in the new corpus). Check: are Latin chars encoded as Latin Unicode codepoints (U+0061-U+007A) or as Cyrillic Unicode codepoints (U+0430-U+044F) in the XML? Document the finding in the PR body.
2. **Compare to text.pdf**: same lemma, same cognate, what does `pdftotext` give? Document.
3. **Compare to deployed djvutxt**: we just deleted it, but it's re-downloadable from IA (`/download/etslukrmov{N}/*_djvu.txt`). Worth one volume's worth of comparison. Document.

The finding determines path:
- **If ABBYY preserves Latin chars correctly**: switch the corpus path for vols 1, 2, 3, 6 back to ABBYY (the parser is in repo: `scripts/ingest/esum_abbyy_parser.py`). Document the tradeoff. The sanitizer is then only needed for vols 4, 5 which lack ABBYY.
- **If ABBYY also has Cyrillic-as-Latin damage**: confirmed upstream issue, proceed with sanitizer for all 6 vols.

### Sanitizer implementation phase

Create `scripts/etymology/recover_latin_cognates.py`:

1. **Confusion table** — a Cyrillic→Latin reverse mapping, hand-curated based on the damage examples above. Include uppercase variants. Include digit-as-letter (`5`→`s`, `8`→`s`, `0`→`o`).
2. **Apply only to non-Cyrillic-script lang markers**. Cyrillic-script markers (don't touch): `р.`, `бр.`, `др.`, `болг.`, `схв.`, `слн.`, `мак.`, `срб.`, `церк.-сл.`, `прасл.`, `псл.`, `укр.`. Non-Cyrillic-script markers (apply): `п.`, `ч.`, `слц.`, `вл.`, `нл.`, `полаб.`, `лит.`, `латиш.`, `прус.`, `лат.`, `гр.`, `рум.`, `угор.`, `нвн.`, `н.`, `дангл.`, `англ.`, `двн.`, `гот.`, `фр.`, `іт.`, `ісп.`, `тур.`, `тат.`, `тюрк.`, `чу́в.`, `узб.`, `туркм.`, `башк.`, `ягноб.`, `ар.`, `євр.`, `ід.`, `іє.`, etc.
3. **Validation pass**: after applying the mapping, check that the result is plausible Latin (mostly U+0041-U+007A, possibly with digraphs / diacritics that match Slavic phonotactics). Reject and fall back to original if result is implausible.
4. **Store both** in `esum_cognate_forms`: add a new column `cognate_forms_recovered` (JSON dict mirroring `cognate_forms` shape) holding the recovered Latin transliterations. Don't overwrite the original.

### Manifest integration

Update `scripts/etymology/build_data_manifest.py` to include `cognate_forms_recovered` in each entry where available. The Astro side renders BOTH the raw + recovered if `cognate_forms_recovered` is present and different.

### Acceptance gates

1. **Investigation report**: PR body documents what the ABBYY XML showed for at least 5 cognate forms in vol1, with character codepoints (use `python3 -c "import unicodedata; ..."` to print codepoints). This decides the path.
2. **Sanitizer correctness on known cases**:
   - `зіегдгізку` → `sierdzisty` or close (Levenshtein ≤ 2)
   - `5гбей` → `srdce` (exact)
   - `5егрепіуп` → `serpentyn` (exact)
   - `8егрепіїп` → `serpentin` (close)
3. **Sanitizer doesn't damage clean cases**: e.g., `5cgemenetz` (already mostly Latin) → unchanged or improved, never worse.
4. **No false positives on Cyrillic-script markers**: a Russian cognate `р.: сердце` stays `сердце`, not converted to Latin.
5. **Coverage**: recovered Latin should appear in ≥50% of entries with non-Cyrillic-script markers (best-effort target).
6. **Pytest green**: `.venv/bin/python -m pytest tests/etymology/ -v`.
7. **Ruff green**.

DO NOT regenerate `data/sources.db` or the manifest as part of this dispatch unless the investigation finds we should switch to ABBYY for some vols (in which case follow the full reload path documented in commit `7d3ab9d898`'s message). Otherwise, leave the corpus reload to a Claude follow-up commit.

## Don't

- Don't modify the original `cognate_forms` field — add `cognate_forms_recovered` alongside.
- Don't apply the sanitizer to Cyrillic-script language markers — that would corrupt legitimate Cyrillic cognates.
- Don't ship a sanitizer that has < 80% accuracy on the test cases listed above. If you can't reach that, surface what you found and ask for direction.
- Don't pretend the residual damage is "fine" — it's the original #2001 grievance. Either we fix it or we hide cognate-form display in the UI. The brief asks for the fix; if it's not tractable, document why.

## Verification before commit

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/ruff check scripts/etymology/ tests/
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python -m pytest tests/etymology/ -v --tb=short
# Smoke-run the sanitizer:
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python -c "
from scripts.etymology.recover_latin_cognates import recover_latin
cases = [
    ('зіегдгізку', 'sierdzisty'),
    ('5гбей', 'srdce'),
    ('5егрепіуп', 'serpentyn'),
    ('8егрепіїп', 'serpentin'),
]
for damaged, expected in cases:
    recovered = recover_latin(damaged)
    print(f'  {damaged!r:30} -> {recovered!r:30} (expected {expected!r})')
"
```

All claims about accuracy must be backed by raw output of the smoke-run.

## Commit + PR shape

- **Branch**: `feat/esum-cognate-latin-sanitizer-2026-05-21`
- **One commit**.
- **PR title**: `feat(etymology): Cyrillic→Latin sanitizer for damaged ESUM cognate forms (closes #2186)`
- **PR body**: investigation findings (ABBYY vs text-pdf vs djvutxt character encoding), sanitizer architecture, accuracy on known cases, coverage on full corpus, what the UI side needs to change.
- **Do NOT auto-merge.**

## Steps (mandatory)

1. `git worktree add -B feat/esum-cognate-latin-sanitizer-2026-05-21 .worktrees/dispatch/codex/esum-cognate-latin-sanitizer-2026-05-21 origin/main`
2. **Investigation phase** (~30 min): download ABBYY vol1, compare encoding to text-pdf, document findings.
3. **Decide path**: sanitizer-only OR ABBYY-for-vols-1236 + sanitizer-for-vols-45. Document decision in commit body.
4. **Implement** `scripts/etymology/recover_latin_cognates.py` with the confusion table + validation pass + lang-marker scoping.
5. **Add migration** for `esum_cognate_forms.cognate_forms_recovered` column.
6. **Tests** at `tests/etymology/test_recover_latin_cognates.py` covering: known-damaged cases, clean Latin cases (no-op), Cyrillic-script markers (no-op), edge cases (empty string, single char, no Cyrillic).
7. **Update** `scripts/etymology/build_data_manifest.py` to include `cognate_forms_recovered`.
8. **Verification** commands. Iterate until green.
9. Single conventional commit.
10. `git push -u origin feat/esum-cognate-latin-sanitizer-2026-05-21`
11. `gh pr create --title ... --body ...` (NO auto-merge).
12. Report task done with the smoke-run output verbatim + investigation findings.

## Anti-fabrication (per #M-4)

Every "tests pass" / "accuracy = N%" / "investigation found X" claim MUST be backed by literal command output. Quote pytest summary, ruff result, smoke-run recovery cases, and the actual Unicode codepoint analysis from the investigation. Don't paraphrase accuracy numbers.
