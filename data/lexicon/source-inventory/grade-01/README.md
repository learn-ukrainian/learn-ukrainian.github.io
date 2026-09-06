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
