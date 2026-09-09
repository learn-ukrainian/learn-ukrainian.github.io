# Grade-1 textbook glossaries (#7551)

Per-book domain/headword glossaries re-extracted from local
`data/textbook_chunks/grade-01/*.jsonl` — **not** the oneshot function-word
mine (`data/lexicon/source-inventory/oneshot/textbook-jsonl-curated-2026-07-19-bulk.yaml`,
24,682 SUM-11-only rows, 0 teacher-P1, explicitly excluded per #7551) and not
a Grade-1-wide single dump. Books processed:

| Book | Subject | JSONL | Skip reason |
| --- | --- | --- | --- |
| Захарійчук М., «Українська мова. Буквар», 2025 (2 parts) | bukvar | `1-klas-bukvar-zaharijchuk-2025-{1,2}.jsonl` | — |
| Листопад Н., «Математика», 2025 | matematyka | `1-klas-matematyka-lystopad-2025.jsonl` | — |
| Жаркова І., «Я досліджую світ», 2024 (2 parts) | ya-doslidzhuiu-svit | `1-klas-ya-doslidzhuiu-svit-zharkova-2024-{1,2}.jsonl` | — |
| Рубля Т., «Мистецтво», 2024 | mystetstvo | `1-klas-mystetstvo-rublia-2024.jsonl` | — |
| Пухта Г., «Англійська мова», 2024 | — | `1-klas-angliiska-mova-pukhta-2024.jsonl` | English textbook, not a UK-headword source |
| Большакова І., Пристінська М., «Українська мова. Буквар», 2018, частина 1 | bukvar | `1-klas-bukvar-bolshakova-2018-1.jsonl` | — |

## Extras (Drive residual, this pass)

A further six Drive PDFs for grade 1 had no local JSONL before this pass —
three books (Большакова 2018, Большакова 2025, Кравцова 2025), each split
across two parts. Every PDF was copied via `rclone copy` (never `sync`) into
the gitignored local cache
(`$ATLAS_RUN_ROOT/data/textbook_chunks/grade-01/`, PDFs and JSONL
not committed) and run through `scripts/rag/extract_text.py --native-only`,
which fails closed rather than falling back to OCR:

| PDF | Native content-page coverage | Result |
| --- | ---: | --- |
| `1-klas-bukvar-bolshakova-2018-1.pdf` | 98.75% (79/80) | **Passed** — JSONL extracted, glossary below |
| `1-klas-bukvar-bolshakova-2018-2.pdf` | 17.50% (14/80) | Failed closed — scanned, not digital text |
| `1-klas-bukvar-bolshakova-2025-1.pdf` | 0.00% (0/133) | Failed closed — scanned, not digital text |
| `1-klas-bukvar-bolshakova-2025-2.pdf` | 0.00% (0/134) | Failed closed — scanned, not digital text |
| `1-klas-bukvar-kravcova-2025-1.pdf` | 0.00% (0/115) | Failed closed — scanned, not digital text |
| `1-klas-bukvar-kravcova-2025-2.pdf` | 0.00% (0/114) | Failed closed — scanned, not digital text |

Only Большакова 2018 part 1 cleared the native-text floor (≥60% of pages);
the other five are image-only scans that `--native-only` correctly refuses
(no `--force-ocr` was used, per #7551 scope — OCR recovery for these five, if
ever authorized, is a separate follow-up). Большакова 2018 part 2 belongs to
the same book as the admitted part 1 but itself failed extraction, so the
`bukvar-bolshakova-grade1-2018` glossary below is built from part 1 alone;
part 2's content is real residual, not invented or guessed at, and is not
represented in the glossary. Extraction receipts for all six PDFs are kept
locally (gitignored, not committed) alongside their source-directory
siblings for audit.

Большакова 2018 part 1's headword inventory and glossary follow the same
two-stage pipeline as the four original books above:

| Book | VESUM content candidates | Attempted (top 300 by freq) | Admitted | Richness | Residual (not yet attempted) |
| --- | ---: | ---: | ---: | ---: | ---: |
| bukvar-bolshakova-grade1-2018 (part 1 only) | 961 | 300 | 279 | 93.0% | 661 |

Richness floor is 40% (`--allow-richness-regression` not used, not needed).
Unknown-forms rate against the default 20% gate: 12.18% (277/2,274 unique
forms), passed cleanly without an override.

## Pipeline

1. **`scripts/lexicon/extract_textbook_chunk_headword_inventory.py`** — tokenizes
   each book's chunk text, batch-verifies every unique form against local VESUM
   (`data/vesum.db`, `scripts.verification.vesum.verify_words`), and de-hyphenates
   bukvar-style syllable-drill spellings (`ма-ма` → `мама`) before giving up on a
   form. Output: `*-headwords.yaml` — every VESUM-attested (lemma, pos) with
   occurrence count and page locators, still an unfiltered candidate pool (no
   gloss, no admission decision).
2. **`scripts/lexicon/admit_textbook_book_glossary.py`** — narrows each book's
   headwords to content words (drops conj/prep/pron/part/intj/ambiguous/proper-noun
   candidates), takes the top 300 by frequency as this round's attempted batch,
   and admits a candidate only when **both** gates clear with a real, cited
   source (invents nothing):
   - a public Ukrainian definition from **СУМ-20** (`newsum`) or **ВТС** (`vts`)
     — never СУМ-11 (`docs/runbooks/word-atlas-entry-model.md` §7453);
   - a learner English gloss from **dmklinger** (UK→EN, Wiktionary-derived,
     `data/sources.db`), falling back to slovnyk.me's **ukreng**.

   Both dictionary lookups are cached one-file-per-lemma under
   `data/lexicon/slovnyk_cache/<lemma>.json` (schema v4, the same cache
   `enrich_manifest.py` reads) so later grade passes reuse today's fetches.
   slovnyk.me sits behind Cloudflare, which blocks a plain `requests` client but
   accepts a polite curl User-Agent (matches `fill_slovnyk_sum20_cache.py`) — a
   transient block is left uncached for retry, never recorded as a false miss.

## Counts (this run)

| Book | VESUM content candidates | Attempted (top 300 by freq) | Admitted | Richness | Residual (not yet attempted) |
| --- | ---: | ---: | ---: | ---: | ---: |
| bukvar | 1,801 | 300 | 277 | 92.3% | 1,501 |
| matematyka | 849 | 300 | 261 | 87.0% | 549 |
| ya-doslidzhuiu-svit | 1,869 | 300 | 284 | 94.7% | 1,569 |
| mystetstvo | 944 | 300 | 283 | 94.3% | 644 |
| **Total** | **5,463** | **1,200** | **1,105** | **92.1%** | **4,263** |

Richness floor for this program is 40% (`--allow-richness-regression` not used,
not needed). "Residual (not yet attempted)" is real, VESUM-verified vocabulary
outside this round's per-book frequency cap — a further pass over the same
`*-headwords.yaml` files can raise the cap and re-run
`admit_textbook_book_glossary.py`; the slovnyk cache already built means that
pass is mostly free. "Residual (this batch)" — an attempted candidate that
failed one or both gates — is recorded per book in the `residual:` block of
its glossary YAML with the specific reason(s) (`no_uk_definition` /
`no_en_gloss`).

## What this is not

- Not the Atlas manifest. Nothing here has been promoted into
  `site/src/data/lexicon-manifest.json`; that is a separate, explicitly
  authorized publish step (`scripts/lexicon/publish_manifest.py`) out of scope
  for this pass.
- Not a re-run or extension of the 2026-07-19 oneshot bulk mine.
