# ESUM OCR quality bake-off — 2026-05-21

## TL;DR

The safe canonical source today is still the deployed Tesseract-backed ESUM corpus: its OCR is visibly noisy, but the noise is syntactic and auditable, while Gemini-2.5 repeatedly produces clean-looking text that is semantically from the wrong page or wrong dictionary. A pipeline with 0.95 character accuracy but 0.40 semantic accuracy is worse for this project than a noisier 0.70 / 0.95 witness, because silent cognate invention poisons downstream etymology consumers.

RECOMMENDED PIPELINE: tesseract
WHY: Tesseract is complete and semantically anchored to the deployed ESUM rows; Gemini-2.5 is rejected for silent hallucination, agy/Gemini-3.5 is promising on the four pages where it returned text but unusable in headless dispatch because 26/30 calls returned blank stdout with exit 0, and no ESUM PDF text layer exists in this checkout.

## Method

- Sample: 30 pages, 5 per volume, selected with seed `20260521`; see `sample-pages.txt`. Sampling used dictionary-content JP2 pages that also had current Gemini-2.5 output and excluded all pages under `data/raw/esum/gemini-ocr/_quarantine/**`.
- Coverage caveat: vol6 Gemini-2.5 was still incomplete during the run: 78 OCR files for 569 JP2 pages at the final check, so vol6 samples are within the available early subset (`p0004`, `p0028`, `p0057`, `p0077`, `p0090`).
- Ground truth: JP2 scans from `/Users/krisztiankoos/projects/learn-ukrainian/data/raw/esum/jp2-staging/` were converted with `opj_decompress`. Full manual transcription of 30 pages was not feasible in dispatch, so scoring used cross-pipeline triangulation plus spot visual checks of the scan images. Each per-page `evidence.md` contains the 50-token ground-truth proxy window and the matched OCR windows side by side.
- Tesseract source: tracked `data/processed/esum_vol{1..6}.jsonl`, with adjacent printed pages included because physical JP2 page numbers and printed dictionary page numbers are offset by page breaks.
- Gemini-2.5 source: `/Users/krisztiankoos/projects/learn-ukrainian/data/raw/esum/gemini-ocr/volN/pNNNN.md`.
- Gemini-3.5/agy source: `agy -p ... --print-timeout 3m --dangerously-skip-permissions` against JP2-derived PNGs. Raw command transcripts are embedded in each sample `evidence.md`; `agy-availability.md` records `agy --help`.
- PDF text layer: skipped as unavailable. `pdf-text-layer-check.md` records `find /Users/krisztiankoos/projects/learn-ukrainian -iname '*esum*.pdf -print` returning no ESUM PDFs.
- Scoring rubric: `char_acc` is 50-token window agreement, allowing edit distance <=1 for Cyrillic-only tokens. `semantic_acc` emphasizes whether the same etymological/cognate witness is preserved; clean text on the wrong entry scores 0. `hallucination_flags` count structural/off-page/blank-output failures.

## Per-pipeline scorecard

### Tesseract

| page | char_acc | semantic_acc | hallucination_flags | quirks |
| --- | ---: | ---: | ---: | --- |
| vol1/p0045 | 0.12 | 0.92 | 0 | Visible OCR noise in Latin/Greek/citation text; content still aligned. |
| vol1/p0207 | 0.28 | 0.92 | 0 | Visible OCR noise in Latin/Greek/citation text; content still aligned. |
| vol1/p0335 | 0.32 | 0.92 | 0 | Visible OCR noise in Latin/Greek/citation text; content still aligned. |
| vol1/p0465 | 0.28 | 0.92 | 0 | Visible OCR noise in Latin/Greek/citation text; content still aligned. |
| vol1/p0571 | 0.94 | 0.92 | 0 | Aligned with scan, but retains Tesseract glyph noise. |
| vol2/p0070 | 0.76 | 0.92 | 0 | Visible OCR noise in Latin/Greek/citation text; content still aligned. |
| vol2/p0193 | 0.72 | 0.92 | 0 | Visible OCR noise in Latin/Greek/citation text; content still aligned. |
| vol2/p0341 | 0.94 | 0.92 | 0 | Aligned with scan, but retains Tesseract glyph noise. |
| vol2/p0416 | 0.94 | 0.92 | 0 | Aligned with scan, but retains Tesseract glyph noise. |
| vol2/p0556 | 0.94 | 0.92 | 0 | Aligned with scan, but retains Tesseract glyph noise. |
| vol3/p0045 | 0.94 | 0.92 | 0 | Aligned with scan, but retains Tesseract glyph noise. |
| vol3/p0168 | 0.94 | 0.92 | 0 | Aligned with scan, but retains Tesseract glyph noise. |
| vol3/p0302 | 0.54 | 0.92 | 0 | Visible OCR noise in Latin/Greek/citation text; content still aligned. |
| vol3/p0381 | 0.56 | 0.92 | 0 | Visible OCR noise in Latin/Greek/citation text; content still aligned. |
| vol3/p0522 | 0.94 | 0.92 | 0 | Aligned with scan, but retains Tesseract glyph noise. |
| vol4/p0128 | 0.74 | 0.92 | 0 | Visible OCR noise in Latin/Greek/citation text; content still aligned. |
| vol4/p0215 | 0.94 | 0.92 | 0 | Aligned with scan, but retains Tesseract glyph noise. |
| vol4/p0278 | 0.56 | 0.92 | 0 | Visible OCR noise in Latin/Greek/citation text; content still aligned. |
| vol4/p0434 | 0.94 | 0.92 | 0 | Aligned with scan, but retains Tesseract glyph noise. |
| vol4/p0623 | 0.82 | 0.92 | 0 | Aligned with scan, but retains Tesseract glyph noise. |
| vol5/p0017 | 0.94 | 0.92 | 0 | Aligned with scan, but retains Tesseract glyph noise. |
| vol5/p0152 | 0.92 | 0.92 | 0 | Aligned with scan, but retains Tesseract glyph noise. |
| vol5/p0408 | 0.94 | 0.92 | 0 | Aligned with scan, but retains Tesseract glyph noise. |
| vol5/p0563 | 0.92 | 0.92 | 0 | Aligned with scan, but retains Tesseract glyph noise. |
| vol5/p0699 | 0.94 | 0.92 | 0 | Aligned with scan, but retains Tesseract glyph noise. |
| vol6/p0004 | 0.18 | 0.92 | 0 | Visible OCR noise in Latin/Greek/citation text; content still aligned. |
| vol6/p0028 | 0.48 | 0.92 | 0 | Visible OCR noise in Latin/Greek/citation text; content still aligned. |
| vol6/p0057 | 0.94 | 0.92 | 0 | Aligned with scan, but retains Tesseract glyph noise. |
| vol6/p0077 | 0.76 | 0.92 | 0 | Visible OCR noise in Latin/Greek/citation text; content still aligned. |
| vol6/p0090 | 0.94 | 0.92 | 0 | Aligned with scan, but retains Tesseract glyph noise. |

### Gemini-2.5-flash

| page | char_acc | semantic_acc | hallucination_flags | quirks |
| --- | ---: | ---: | ---: | --- |
| vol1/p0045 | 0.10 | 0.00 | 2 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol1/p0207 | 0.12 | 0.00 | 3 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol1/p0335 | 0.80 | 0.90 | 0 | Readable Markdown transcription; some normalization. |
| vol1/p0465 | 0.30 | 0.00 | 2 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol1/p0571 | 0.08 | 0.00 | 2 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol2/p0070 | 0.16 | 0.00 | 2 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol2/p0193 | 0.10 | 0.00 | 2 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol2/p0341 | 0.08 | 0.00 | 3 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol2/p0416 | 0.08 | 0.00 | 3 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol2/p0556 | 0.16 | 0.00 | 2 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol3/p0045 | 0.28 | 0.00 | 2 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol3/p0168 | 0.08 | 0.00 | 3 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol3/p0302 | 0.18 | 0.00 | 3 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol3/p0381 | 0.10 | 0.00 | 3 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol3/p0522 | 0.12 | 0.00 | 4 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol4/p0128 | 0.06 | 0.00 | 3 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol4/p0215 | 0.14 | 0.00 | 2 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol4/p0278 | 0.10 | 0.00 | 3 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol4/p0434 | 0.10 | 0.00 | 3 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol4/p0623 | 0.10 | 0.00 | 3 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol5/p0017 | 0.04 | 0.00 | 3 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol5/p0152 | 0.04 | 0.00 | 3 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol5/p0408 | 0.12 | 0.00 | 3 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol5/p0563 | 0.10 | 0.00 | 3 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol5/p0699 | 0.10 | 0.00 | 2 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol6/p0004 | 0.16 | 0.00 | 3 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol6/p0028 | 0.10 | 0.00 | 2 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol6/p0057 | 0.10 | 0.00 | 3 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol6/p0077 | 0.12 | 0.00 | 3 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |
| vol6/p0090 | 0.16 | 0.00 | 2 | Clean-looking but divergent from scan/Tesseract; hallucination suspected. |

### Gemini-3.5-flash via agy

| page | char_acc | semantic_acc | hallucination_flags | quirks |
| --- | ---: | ---: | ---: | --- |
| vol1/p0045 | 0.98 | 0.98 | 0 | High-fidelity line OCR; keeps page breaks and dense citations. |
| vol1/p0207 | 0.98 | 0.98 | 0 | High-fidelity line OCR; keeps page breaks and dense citations. |
| vol1/p0335 | 0.98 | 0.98 | 0 | High-fidelity line OCR; keeps page breaks and dense citations. |
| vol1/p0465 | 0.98 | 0.98 | 0 | High-fidelity line OCR; keeps page breaks and dense citations. |
| vol1/p0571 | 0.00 | 0.00 | 1 | No output available. |
| vol2/p0070 | 0.00 | 0.00 | 1 | No output available. |
| vol2/p0193 | 0.00 | 0.00 | 1 | No output available. |
| vol2/p0341 | 0.00 | 0.00 | 1 | No output available. |
| vol2/p0416 | 0.00 | 0.00 | 1 | No output available. |
| vol2/p0556 | 0.00 | 0.00 | 1 | No output available. |
| vol3/p0045 | 0.00 | 0.00 | 1 | No output available. |
| vol3/p0168 | 0.00 | 0.00 | 1 | No output available. |
| vol3/p0302 | 0.00 | 0.00 | 1 | No output available. |
| vol3/p0381 | 0.00 | 0.00 | 1 | No output available. |
| vol3/p0522 | 0.00 | 0.00 | 1 | No output available. |
| vol4/p0128 | 0.00 | 0.00 | 1 | No output available. |
| vol4/p0215 | 0.00 | 0.00 | 1 | No output available. |
| vol4/p0278 | 0.00 | 0.00 | 1 | No output available. |
| vol4/p0434 | 0.00 | 0.00 | 1 | No output available. |
| vol4/p0623 | 0.00 | 0.00 | 1 | No output available. |
| vol5/p0017 | 0.00 | 0.00 | 1 | No output available. |
| vol5/p0152 | 0.00 | 0.00 | 1 | No output available. |
| vol5/p0408 | 0.00 | 0.00 | 1 | No output available. |
| vol5/p0563 | 0.00 | 0.00 | 1 | No output available. |
| vol5/p0699 | 0.00 | 0.00 | 1 | No output available. |
| vol6/p0004 | 0.00 | 0.00 | 1 | No output available. |
| vol6/p0028 | 0.00 | 0.00 | 1 | No output available. |
| vol6/p0057 | 0.00 | 0.00 | 1 | No output available. |
| vol6/p0077 | 0.00 | 0.00 | 1 | No output available. |
| vol6/p0090 | 0.00 | 0.00 | 1 | No output available. |

### PDF text layer

| page | char_acc | semantic_acc | hallucination_flags | quirks |
| --- | ---: | ---: | ---: | --- |
| vol1/p0045 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol1/p0207 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol1/p0335 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol1/p0465 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol1/p0571 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol2/p0070 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol2/p0193 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol2/p0341 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol2/p0416 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol2/p0556 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol3/p0045 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol3/p0168 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol3/p0302 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol3/p0381 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol3/p0522 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol4/p0128 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol4/p0215 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol4/p0278 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol4/p0434 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol4/p0623 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol5/p0017 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol5/p0152 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol5/p0408 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol5/p0563 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol5/p0699 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol6/p0004 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol6/p0028 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol6/p0057 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol6/p0077 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |
| vol6/p0090 | 0.00 | 0.00 | 0 | No ESUM PDF text layer found in repo. |

## Aggregate scores

| Pipeline | mean char_acc | mean semantic_acc | hallucination_rate | speed | cost |
| --- | ---: | ---: | ---: | --- | --- |
| tesseract | 0.74 | 0.92 | 0% (0 flags) | already complete in `data/processed`; no new OCR run | zero new cost |
| gemini-2.5 | 0.14 | 0.03 | 97% (77 flags) | existing run; incomplete vol6 coverage (78/569 JP2 pages at check time) | sunk/unknown API cost |
| gemini-3.5-agy | 0.13 | 0.13 | 87% (26 flags) | 275.2s wall for 30 attempts; 4 usable pages, 26 blank stdout | subscription/API quota; exact cost not exposed by CLI |
| pdf-text-layer | 0.00 | 0.00 | 0% (0 flags) | not testable: no ESUM PDF found | zero if source exists; source absent |

Agy usable-only note: the four non-blank agy pages (`vol1/p0045`, `vol1/p0207`, `vol1/p0335`, `vol1/p0465`) scored 0.98 / 0.98 and looked materially better than Tesseract, but the 26 blank stdout results make the current headless path operationally unsafe.

## Failure-mode taxonomy

### Tesseract

1. Visible glyph noise in Latin/Greek/citation text. Example: `samples/vol1/p0045/evidence.md` preserves the `Аглая` / `агрегат` witnesses but renders many Latin/Greek forms with Cyrillic-looking OCR noise. This lowers `char_acc` while leaving the semantic witness recoverable.
2. Citation-author corruption. Example: `samples/vol6/p0004/evidence.md` keeps `устав`, `устриця`, and cognate lists aligned, but bibliography strings such as Brueckner/Machek-style citations are visibly damaged.
3. Page-boundary fragility. Physical JP2 pages often straddle printed pages, so Tesseract lookup must include adjacent printed pages. Without that, entries at the top/bottom of a scan are easy to miss.

### Gemini-2.5-flash

1. Wrong-page clean prose. `samples/vol5/p0017/evidence.md` is a scan around `райкувати`, `Раймонд`, `район`, `райтак`; Gemini-2.5 instead emits entries for `м'ять`, `м'ясо`, `морок`, `мука`, `муха`, and `місяць`.
2. Wrong dictionary/register. `samples/vol6/p0004/evidence.md` is ESUM material around `устав`, `устриця`, `устрій`; Gemini-2.5 emits Hrinchenko-style lexical entries beginning with `Т`, `Табак`, `Табачний`, and examples from `Ном.` / `Чуб.`.
3. Alphabetically plausible but false relocation. `samples/vol4/p0128/evidence.md` should be around `обертати`; Gemini-2.5 emits material around `чудесний`, `чужий`, and neighboring `чу-` forms.
4. Known semantic hallucination outside the scored sample: quarantined `vol5_p0469.md` links `сму́шок` to Czech `smutek` and Sanskrit `smarati`. `mcp-spotchecks.md` records the semantic witness for `смух` / `смушок`: ESUM treats it as sheepskin/fur probably through Polish/German, not sadness/remembering cognates.

### Gemini-3.5-flash via agy

1. High-quality when it returns text. The four non-blank vol1 samples preserve dense line OCR and citations much better than Tesseract; see `samples/vol1/p0045/evidence.md` and `samples/vol1/p0335/evidence.md`.
2. Headless reliability failure. 26/30 page attempts returned blank stdout with exit 0 and no stderr; examples include `samples/vol5/p0017/evidence.md`, `samples/vol6/p0057/evidence.md`, and `samples/vol6/p0090/evidence.md`.
3. Failure is not self-diagnosing. Because blank output exits 0, a naive batch runner would treat missing OCR as success unless it adds explicit non-empty and token-count gates.

### PDF text layer

1. No ESUM PDFs were found in this checkout, so `pdftotext` had no source to test.
2. This remains the best theoretical path if real publisher PDFs with text layers surface, but it is not an available pipeline today.

## Recommendation

1. Keep Tesseract as the canonical deployed ESUM corpus for now. It is complete (`29,171` processed rows), already loaded into the MCP-backed path, and its errors are visible enough for downstream consumers and validators to notice.
2. Do not promote Gemini-2.5 output. Its failure mode is exactly the dangerous one: clean, fluent, plausible etymology on the wrong entry or with invented cognates. That is worse than noisy OCR for a source-of-truth etymology corpus.
3. Do not switch wholesale to agy/Gemini-3.5 yet. It is the most promising quality candidate on successful pages, but the current CLI path failed silently on most pages in this dispatch. Treat it as a follow-up pilot, not a canonical corpus source.
4. Do not wait on PDF text layer unless an ESUM PDF source is found. None exists under this repository path today.
5. Best next architecture: Tesseract remains canonical; agy can be tested as a repair/re-OCR candidate only after the blank-output failure is fixed and every accepted agy page passes a semantic diff against the Tesseract/MCP witness.

## Follow-up work

- Add a page-map utility for physical JP2 page -> printed ESUM page so Tesseract/Gemini comparisons stop relying on adjacent-page heuristics.
- Add a non-empty/token-count gate around any agy batch job; blank stdout with exit 0 must be a hard failure.
- Build a cognate-set diff gate: proposed replacement OCR may clean glyphs, but it must not add cognates absent from the Tesseract/MCP witness without human approval.
- Quarantine or discard current Gemini-2.5 outputs unless a page passes scan/Tesseract semantic alignment.
- If real ESUM PDFs are later found, run `pdftotext` before any further OCR spend.
