# Bug Autopsy: ESUM re-OCR pivot — vision-LLM failure → Internet Archive text layers

**Date:** 2026-05-21
**Issue:** #2001 (closed 2026-05-17) — autopsy added 2026-05-21
**Companion autopsy:** [`gemini-ocr-hallucinations.md`](./gemini-ocr-hallucinations.md) — detector-side write-up of the specific hallucination patterns we quarantined

## What broke

Issue #2001 called for re-OCRing all six volumes of ЕСУМ (Етимологічний словник української мови) because the deployed djvutxt-derived corpus contained too much OCR damage on the cognate lines (Latin transliterations of Polish/Czech/Slovak forms read as Cyrillic garbage; digit-confusions; sweep-in of adjacent Ukrainian function words). Two pipelines were attempted before the project was killed:

1. **Tesseract** — competent on Ukrainian prose, weak on dense polyglot lines.
2. **Gemini-2.5-flash vision OCR** — the headline plan. Daily-quota slow-burn run produced 3,179 page outputs over multiple days. The output looked clean. It wasn't.

The Gemini-2.5-flash bake-off (`audit/etymology-ocr-bakeoff/REPORT.md`, branch `codex/esum-bakeoff-2026-05-21`) measured a **97% wrong-page hallucination rate**: the model was emitting etymologically-plausible, linguistically-coherent Ukrainian text that corresponded to a *different page* than the scan it was given. Independent orchestrator spot-checks confirmed:

- vol5/p0017 scan = `РАЙ-` headwords; Gemini emitted М-section text (`м'ясо, мука, муха, місяць, морок`).
- vol3/p0200 scan = Л-section; Gemini emitted Ж-section (`ЖОЛО́Б`).
- vol4/p0500 scan = П-section полоскати; Gemini emitted К-section (`КРА́ПКА`).
- vol1/p0100 — content overlap with the right region but mislabeled entry boundaries.

All 3,173 corrupt files were deleted; 17 forensic samples were preserved at `data/raw/esum/gemini-ocr/_quarantine/2026-05-19-repetition-hallucination/` and committed as test fixtures by PR #2179.

## Why

Vision-LLMs on dense print at scale conflate "what this kind of page typically looks like" with "what THIS specific page says." When faced with dense lexicographic typography (abbreviation-heavy cognate lines, italicized proto-forms, mixed Cyrillic + Latin + Greek), the model's *language prior* overrides its visual grounding. It hallucinates plausible-looking etymology entries instead of transcribing the image.

Cross-validation evidence:
- Tesseract: 0.74 char_acc / **0.92 semantic_acc** (right page, garbled glyphs).
- Gemini-2.5-flash: 0.14 char_acc / **0.03 semantic_acc** (clean glyphs, wrong page).
- Gemini-3.5/agy: 0.98/0.98 on the 4-of-30 pages it returned text; blank stdout on 26/30 (headless CLI broken).

The catastrophic-but-invisible failure mode — output that "reads" correct in Ukrainian but corresponds to a different scan — is fundamentally worse than classical OCR noise. Reviewers cannot detect it from the output alone; only side-by-side comparison against the source image surfaces it.

## The pivot

Mid-session discovery: the Internet Archive (`archive.org/details/etslukrmov{1..6}`) already serves clean text layers for the whole 6-volume set as `_text.pdf` (searchable PDF), `_djvu.txt` (what we already had), `_abbyy.gz` (ABBYY FineReader 11 XML, gold-standard structured OCR — vols 1, 2, 3, 6 only), `_djvu.xml`, and `_hocr_searchtext.txt.gz` (vols 4, 5).

Cross-validation of `_text.pdf` against `_abbyy.gz` on 20 random pages × 4 volumes: **mean Jaccard 0.953**, min 0.911, max 0.995. Both pipelines agree on content; differences are hyphenation handling and a handful of single-char OCR variants.

The whole re-OCR project (issue #2001) was solving a problem **already solved on the source's side**. The publisher's PDFs have text layers, and IA ran ABBYY OCR on the JP2 scans — both freely downloadable.

Plan locked the same session: **ABBYY XML for vols 1/2/3/6 (gold standard), text.pdf for vols 4/5 (no ABBYY available).**

## What shipped (2026-05-21)

| PR | Issue | Description |
|---|---|---|
| #2179 | #2177 | Hallucination detector + 17 fixtures + autopsy `gemini-ocr-hallucinations.md` |
| #2180 | #2175 | ABBYY XML streaming parser (`scripts/ingest/esum_abbyy_parser.py`) for vols 1, 2, 3, 6 |
| #2181 | #2174 | `text.pdf` parser branch (`--source-format text-pdf`) in `scripts/ingest/esum_ingest.py` for vols 4, 5 |
| `c56835257b` | #2176 | Regenerated all 6 `data/processed/esum_vol{1..6}.jsonl` and reloaded `data/sources.db` |

Corpus delta:

| Vol | Parser | Old (djvutxt) | New | Δ |
|---|---|---|---|---|
| 1 | ABBYY | 5,146 | 4,809 | −337 |
| 2 | ABBYY | 4,899 | 4,686 | −213 |
| 3 | ABBYY | 4,007 | 3,899 | −108 |
| 4 | text-pdf | 6,088 | 5,787 | −301 |
| 5 | text-pdf | 4,029 | 5,912 | **+1,883** |
| 6 | ABBYY | 5,002 | 4,483 | −519 |
| **sum** | | **29,171** | **29,576** | **+405** |

ABBYY-parsed volumes (1, 2, 3, 6) drops are **real quality wins**: deployed djvutxt parser was over-extracting by treating continuation paragraphs as separate entries. The new parser correctly emits `а-` as the third vol1 lemma where djvutxt was emitting `літичний` (extracted from a continuation paragraph mid-entry).

Vol5 +47% is **real new coverage** of entries the deployed djvutxt parser missed (`разівка`, `рантувати`, and many others spot-checked).

## Open follow-up

#2183 — vol4 + vol5 text-pdf parser noise: ~20% of sampled results contain backmatter (colophon: `видавництво`, `виготовлено`, `НВП`, `ТОВ`) or bibliography blocks (citation lists like `СУМ 9, 763; Бупр. Ш 222; Фасмер Ш 776`) extracted as if they were lemma entries. The relaxed entry-start heuristic in `--source-format text-pdf` (min-length 5 chars, no punctuation requirement on cross-references) catches legit short entries vols 1/2/3/6's ABBYY structure recovered explicitly, but it also catches structural artifacts. Vols 1/2/3/6 are clean on spot-check.

## Prevention

1. **Check the source's existing metadata first.** Before launching any OCR pipeline, audit what the source host already serves. Internet Archive provides `_text.pdf`, `_djvu.txt`, `_abbyy.gz`, `_djvu.xml`, `_hocr_searchtext.txt.gz` for every printed item it hosts. The publisher's PDFs frequently have text layers. **Spending compute + quota to re-OCR a document that already has a clean text layer is a planning failure**, regardless of how the OCR run goes.

2. **For any future visual-OCR experiment: ship a semantic-diff gate against a baseline classical OCR.** Tesseract scored 0.92 semantic_acc; Gemini-2.5-flash 0.03. If a vision-LLM output diverges massively from the classical baseline on the same page, the vision-LLM is hallucinating. The diff is the gate. Without it, the hallucination is invisible.

3. **The shadow-uniqueness check has a known gap; PR #2179 closes it.** The legacy `is_low_quality_output` check guard `if len(lines) < 10: continue` skipped short files where Gemini looped on a single line. New `has_substring_repetition` catches those (window=15, threshold=4; 0 false positives against 100 clean baseline entries; 16/17 quarantined samples flagged automatically, 1 reserved for the semantic-hallucination case which needs RAG verification).

4. **Bake-offs catch hallucination; self-evaluation does not.** Gemini-2.5-flash's outputs read as clean Ukrainian etymology — to humans and to automated checks that don't have ground truth. The wrong-page failure was only visible via side-by-side comparison against a baseline (Tesseract here). Any pipeline that consumes vision-LLM output without a cross-validation gate is shipping hallucination.

## Cross-references

- Session handoff: `docs/session-state/2026-05-21-issue-2001-ocr-handoff.md` (the morning-after closeout of the killed Gemini project)
- Bake-off REPORT: `audit/etymology-ocr-bakeoff/REPORT.md` on branch `codex/esum-bakeoff-2026-05-21`
- Companion detector autopsy: `docs/bug-autopsies/gemini-ocr-hallucinations.md`
- Dispatch briefs: `docs/dispatch-briefs/2026-05-21-esum-{textpdf,abbyy}-parser-*.md`, `docs/dispatch-briefs/2026-05-21-gemini-hallucination-fixtures-gemini.md`
