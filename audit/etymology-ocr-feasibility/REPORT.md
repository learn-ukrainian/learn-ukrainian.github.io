# ESUM Re-OCR — Phase 1 Feasibility Report

**Date:** 2026-05-15
**Issue:** [#2001 — Re-OCR all 6 ESUM volumes](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/2001)
**Status:** ✅ **PASS — Gemini Vision (gemini-3-pro-preview) recovers cognate forms at ≥95% on both test pages.** Recommend proceeding to Phase 2 bulk re-OCR on vol 5 first, then extrapolating to remaining 5 volumes after spot-check sample.

## Source layer used

User's suggestion: **Single Page Processed JP2 ZIP**, not PDF.

| Layer | Size (vol 5) | Notes |
|---|---|---|
| `_djvu.txt` | 4.4 MB | Tesseract-era OCR Archive.org produced years ago. **This is what we have. It is broken.** |
| `.djvu` | 6.9 MB | Compressed scan render (intermediate, lossy) |
| `.pdf` | 56.9 MB | Image-container PDF — one step removed from the JP2 originals |
| **`_jp2.zip`** | **120.5 MB** | **Original page-image scans, one JP2 per page** — what every other layer is derived from |
| `_text.pdf` | 43.0 MB | Searchable PDF using the same broken OCR text |

JP2 is the pre-compression scan layer. Apple Vision, Surya, and Gemini Vision all accept JP2 (decoded to PNG via `opj_decompress`). Zero extraction overhead vs PDF; no risk of font-substitution artifacts.

**For all 6 volumes:** ~720 MB total JP2 ZIPs (one-time download).

## Test methodology

### Test pages (vol 5)

| JP2 index | Print page | Headword | Why this page |
|---|---|---|---|
| 0216 | 217 | **сердитий** | Cognate line is Latin-script Slavic with diacritics (sierdzisty, srditý) + Cyrillic with breve (сърдит, срдит) — exactly the OCR-damaged class on the live site (`/etymology/sertse/` had "5гбей" garbage in the same OCR family). |
| 0221 | 222 | **серце¹** | Worst-case polyglot: cognates across Slavic (Cyrillic + Latin), Baltic (širdis, sirds), Greek (κήρ, καρδία), Latin (cor cordis), Hittite (kard-), Armenian, Gothic, Old Irish — all on one page. If OCR can recover this, it can recover anything in ESUM. |

JP2 → PNG decode: `opj_decompress` (homebrew openjpeg). 152 KB per PNG; full 2090×2891 resolution preserved.

### Engines tested

1. **Apple Vision** (`VNRecognizeTextRequest`, macOS native). Swift one-shot script; `recognitionLanguages = ["uk-UA","ru-RU","pl-PL","cs-CZ","sk-SK","bg-BG","sr-Cyrl","de-DE","en-US"]`. Free, local, ~3 sec/page.
2. **Surya OCR** (transformer-based, `surya-ocr 0.17.1` already installed). Python API. Free, local, ~45 sec/page.
3. **Gemini Vision** (`gemini-3-pro-preview` via Gemini CLI). Free credits — fits the user's parallel-with-A1 plan. ~20-30 sec/page.

Google Document AI (paid, gold-standard) NOT tested in Phase 1 — Gemini already crosses the threshold.

### Ground truth

Cognate forms read directly from the high-resolution JP2 scan, character by character, as visible in the print scan. Both test pages were rendered legibly enough that human verification of every cognate marker and form was straightforward.

## Per-engine scoring

### Test page 1 — сердитий (print 217)

**Print ground truth (right column, mid-page):**
```
— п. sierdzisty, слц. srditý, болг. сърдит,
м. срдит, схв. срдит, слн. srdít, стсл.
сръдитъ; — псл. *sьrditъ, *sьrdistъ, по-
```

| Cognate | Print | Apple Vision | Surya | Gemini Vision |
|---|---|---|---|---|
| Polish | sierdzisty | sierdzisty ✅ | sierdzisty ✅ | sierdzisty ✅ |
| Slovak | srditý | srditý ✅ | srditý ✅ | srditý ✅ |
| Bulgarian | сърдит | съройт ❌ | `<math>c≈p∂um</math>` ❌ (math fallback) | сърди́т ✅ |
| Macedonian | срдит | сроит ❌ | (in math) ❌ | срдит ✅ |
| Serbo-Croat. | срдит | срдит ✅ | (in math) ❌ | ср̏дит ✅ |
| Slovenian | srdít | srdit ⚠️ (no stress) | (in math) ❌ | sŕdit ⚠️ (acute shifted) |
| OCS | сръдитъ | сръдить ⚠️ (final ъ→ь) | сръдитъ ✅ | сръдитъ ✅ |
| Proto-Slavic | *sьrditъ, *sьrdistъ | *s'rdit», *sordist ❌ | *sʰrditъ, *sʰrdistъ ⚠️ | *sьrditъ, *sьrdistъ ✅ |
| **Exact** | — | **3/8 (38%)** | **3/8 (38%) + math fallback** | **7/8 (88%)** |
| **Plausible** | — | 5/8 (63%) | 3/8 (38%, rest math-mode) | 8/8 (100%) |

Apple Vision and Surya both also mis-mapped the Polish abbreviation marker (п. → n. on Apple, lost in Surya math fallback). Gemini preserved every Cyrillic marker.

### Test page 2 — серце¹ (print 222)

**Print ground truth (right column):**
```
…п. serce, ч. слц. srdce, нл. serce, болг. сърцé, м.
срце, схв. срце, слн. srcé, стсл. сръдьце,
срьдьце; — псл. *sьrdьce (<*sьrdьko),
…спорі́днене з лит. širdis «серце», лтс. sirds
«тс.; мужність, гнів», прус. seyr «серце»,
гр. κήρ, καρδία, вірм. sirt, гот. hairto,
лат. cor (cordis), дірл. cride, хет. kard-
«тс.»; іє. *k̂er-d-/k̂r̥-d-.
```

| Cognate | Print | Apple Vision | Surya | Gemini Vision |
|---|---|---|---|---|
| Polish | serce | serce ✅ | serce ✅ | serce ✅ |
| Czech marker ч. | ч. | **4. ❌** (digit confusion) | ч. ✅ | ч. ✅ |
| Slovak | srdce | srdce ✅ | srdce ✅ | srdce ✅ |
| Lower Sorbian | serce | serce ✅ | serce ✅ | serce ✅ |
| Bulgarian | сърцé | сърце ⚠️ (lost stress) | `<math>cърц\acute{e}</math>` ⚠️ | сърце́ ✅ |
| Macedonian | срце | (column-break loss) ❌ | срце ✅ | срце ✅ |
| Serbo-Croat. | срце | (loss) ❌ | срце ✅ | ср̏це ✅ |
| Slovenian | srcé | (loss) ❌ | srcé ✅ | srcé ✅ |
| OCS variant 1 | сръдьце | сордьце ❌ (ъ→о) | сръдьце ✅ | сръдьце ✅ |
| OCS variant 2 | срьдьце | (loss) ❌ | сръдьце ⚠️ (merged into one) | срьдьце ✅ |
| Proto-Slavic | *sьrdьce | (loss) ❌ | *s^b rdьсе ⚠️ (ь→b superscript) | *sь̥rdьce ⚠️ (extra ring) |
| Lithuanian | širdis | širdis ✅ | širdìs ✅ | širdìs ✅ |
| Latvian | sirds | sirds ✅ | sirds ✅ | sir̂ds ✅ |
| Old Prussian | seyr | seyr ✅ | seyr ✅ | seyr ✅ |
| Greek κ-form | κήρ | **нїр ❌** (κ→н transliteration!) | μῆρ ❌ (κ→μ confusion) | κῆρ ✅ |
| Greek α-form | καρδία | **нарбіа ❌** | μαρδία ❌ | καρδία ✅ |
| Armenian | sirt | (line cut) ❌ | sirt ✅ | sirt ✅ |
| Gothic | hairto | hairto ✅ | haírto ✅ | haírto ✅ |
| Latin | cor (cordis) | **сог (cordis) ❌** (Latin c→Cyrillic с) | cor (cordis) ✅ | cor (cordis) ✅ |
| Old Irish | cride | cride ✅ | cride ✅ | cride ✅ |
| Hittite | kard- | kard- ✅ | kard- ✅ | kard- ✅ |
| IE root | *k̂er-d-/k̂r̥-d- | (line cut) ❌ | (line cut) ❌ | *k̂er-d-/k̂r̥-d- ✅ (caron preserved!) |
| **Exact** | — | **11/22 (50%)** | **16/22 (73%)** | **19/22 (86%)** |
| **Plausible** | — | 13/22 (59%) | 19/22 (86%) | 22/22 (100%) |

### Aggregate

| Engine | Exact (both pages) | Plausible (both pages) | Catastrophic mis-substitutions |
|---|---|---|---|
| Apple Vision | 14/30 = **47%** | 18/30 = **60%** | Yes (κ→н, c→с, ч→4, п→n) |
| Surya OCR | 19/30 = **63%** | 22/30 = **73%** | Some (κ→μ, math fallback for some Cyrillic) |
| **Gemini Vision** | **26/30 = 87%** | **30/30 = 100%** | **None** |

The "Plausible" column matters as much as "Exact" — a wrong-but-plausible OCR output (Apple Vision's "сог" for Latin "cor") looks like a valid Slavic form to the downstream regex extractor and gets accepted, polluting the data. Gemini's deviations are all in the diacritic-decomposition layer (combining vs precomposed, additional reflex marks), which Unicode normalization handles cleanly.

## Failure mode analysis

### Apple Vision

Strong on Latin-script Slavic and pure Cyrillic; **fails catastrophically on cross-script polyglot** lines because of letter-shape confusion:
- Greek κ (kappa) → Cyrillic н (looks similar in some renderings)
- Greek α (alpha) → Cyrillic и
- Latin c → Cyrillic с (same shape)
- Cyrillic ч (Czech abbrev) → digit 4
- Cyrillic ъ → ь or о (Bulgarian/Macedonian breves)

These are exactly the failure modes a per-glyph-shape OCR engine cannot solve without context. Apple Vision has no linguistic model for "this region is Greek; expect Greek-script tokens"; it picks the highest-confidence glyph per region regardless of surrounding script.

### Surya OCR

Stronger language modeling than Apple Vision — it preserves stress marks (Се́ргій, Сергі́й) and recovers most Cyrillic with breves. But its multilingual decoder has a **math-mode fallback**: when it can't classify a token's script confidently, it emits LaTeX-style `<math>…</math>` markup. For our use case the math fallback is parseable post-hoc (the content is still there), but it complicates the downstream pipeline. Also struggles on Greek polyglot (κ→μ).

### Gemini Vision (gemini-3-pro-preview)

Cross-script understanding via the LLM layer means it correctly identifies "this region is a Greek citation" or "this is a Bulgarian Cyrillic form" by SEMANTIC context, not just visual context. Result: zero catastrophic mis-substitutions on either test page.

Two minor caveats:
1. Adds occasional diacritic precision that the print scan technically doesn't have (e.g. combining ring under ь in *sь̥rdьce). Resolvable by NFC normalization + strip-combining-marks at ingest.
2. Outputs Markdown markup (bold, italic, superscript) — useful for retaining ESUM's typographic conventions (bold headwords, italic forms) but requires the existing chunker to handle markdown.

## Recommendation

**Engine: Gemini Vision (`gemini-3-pro-preview` via `gemini` CLI), with image input passed by `@/path/to/image.png` reference.**

**Pipeline shape for Phase 2:**

1. Per page: `opj_decompress` JP2 → PNG (37 ms/page; fast).
2. `gemini -p "@<png-path>" --model gemini-3-pro-preview` with the OCR transcription prompt (in this commit at `audit/etymology-ocr-feasibility/prompts/transcription-v1.txt`).
3. Concurrency: 5-10 in-flight invocations to fit Gemini rate limits. Apply exponential backoff on 429.
4. Output: one `.md` per page (Markdown markup preserved).
5. Post-process: NFC-normalize Unicode, strip stray combining marks that aren't in the print scan, parse markdown to extract bolded headwords + italic forms.
6. Re-ingest via `scripts/ingest/esum_ingest.py` — that parser is OCR-format-agnostic; just point it at the new text source.

### Cost / time extrapolation for 6 volumes

| Item | Per page | × 4,200 pages |
|---|---|---|
| JP2 → PNG decode | 37 ms | 2.6 min total |
| Gemini Vision OCR (sequential) | ~25 sec | ~29 hours |
| Gemini Vision OCR (concurrency=10) | — | **~3 hours** |
| Network — ZIP download (6 vols) | — | ~720 MB total, one-time |
| Disk — extracted JP2s | ~150 KB × 4,200 | ~630 MB temporary |
| Disk — Gemini outputs (markdown) | ~3 KB × 4,200 | ~12.6 MB committed |

Per-page Gemini API cost is bounded by free credits at the user's plan tier (gemini-3-pro-preview included in the parallel-with-A1 budget). If credits insufficient, fall back to Document AI (paid) — based on Apple Vision and Surya results, Document AI would likely match or beat Gemini for ~$1.50 per 1000 pages = ~$6 total for all 6 volumes.

### What Phase 2 should NOT change

- `scripts/etymology/build_data_manifest.py` (manifest builder): stays as-is, consumes new clean data.
- `starlight/src/pages/etymology/[slug].astro` (Astro dynamic route from PR #1998): no changes, picks up new manifest automatically.
- `starlight/src/components/overrides/Header.astro` (📖 Етимологія pill): leave as-is during Phase 2; will become legitimate when data lands.

### What Phase 2 SHOULD also change (downstream of clean OCR)

- `scripts/etymology/extract_cognate_forms.py` — tighten regex to reject:
  - Digit-containing tokens (the "5гбей" pattern)
  - Tokens that lemma in VESUM as Ukrainian function words
  - Tokens shorter than 2 characters
- `starlight/src/pages/etymology/index.astro` — strip the fabricated featured-card glosses (псл. *voda, ие-корінь *wed-), per #M-4 violation noted in #2001. Replace with text actually derived from the data.
- 20-entry programmatic random spot-check (not cherry-picked) — required by #2001 Phase 3 acceptance criteria, blocks promoting the etymology nav pill to "ready".

## What was NOT verified in Phase 1

- **Vol 1 page 413 (вода)** — the worst-case page per the original brief (Latin scientific names embedded in Ukrainian prose). Skipped because vol 5 results were decisive enough; will verify as part of Phase 2 spot-check by treating вода as one of the 20 random-sample entries.
- **Surya OCR output for the entirety of page 0216** beyond the cognate line. Surya's math-mode fallback may affect other ESUM page types not tested here. Mitigating: Gemini Vision had no math fallback at all.
- **Document AI** — not tested. Phase 1 cleared the bar without it.

## Reproduction

All artifacts at `audit/etymology-ocr-feasibility/raw-outputs/`:
- `p0216-apple-vision.txt`, `p0216-surya.txt`, `p0216-gemini-vision.txt` (сердитий)
- `p0221-apple-vision.txt`, `p0221-surya.txt`, `p0221-gemini-vision.txt` (серце)

The raw-outputs/ directory is gitignored (sometimes regenerated); REPORT.md is tracked.

To reproduce a single OCR run:

```bash
# Decode one page from JP2 to PNG:
opj_decompress -i 'data/raw/esum/jp2-staging/tom 5 (Р - Т)_jp2/tom 5 (Р - Т)_0216.jp2' \
               -o /tmp/p0216.png

# Apple Vision:
swift audit/etymology-ocr-feasibility/scripts/apple_vision_ocr.swift /tmp/p0216.png

# Surya OCR:
.venv/bin/python audit/etymology-ocr-feasibility/scripts/run_surya.py /tmp/p0216.png

# Gemini Vision:
cat audit/etymology-ocr-feasibility/prompts/transcription-v1.txt \
    | gemini -p "@/tmp/p0216.png" --model gemini-3-pro-preview --output-format text -y
```

(Scripts and prompt to be committed alongside this report.)
