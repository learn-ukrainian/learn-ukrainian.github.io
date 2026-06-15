# Word Atlas — data-coverage strategy (#2882)

> Measured 2026-06-15 against `site/src/data/lexicon-manifest.json` (post-#3213 regen,
> 2,667 entries / 150 modules). This is the plan for **completing** the Atlas — i.e.
> closing the population gaps, after the correctness work (#3197/#3210/#3218) landed.

## TL;DR — it's a DATA problem, not a code problem

- **Design:** ✅ have it (POC 4-tab + section model: meaning / pronunciation+stress /
  morphology / etymology / cefr / synonyms / antonyms / idioms / literary / wiki).
- **Code:** ✅ every section already has a working filler in `enrich_manifest.py`
  (`_meaning`, `_translation`, `_etymology`, `_cefr`, `_stress`, `_morphology`,
  `_synonyms`, `_idioms`, `_antonyms`, `_literary_attestation`, `_wiki_reference`).
  **No section-renderer code is missing.** What's missing is a few *fetcher/indexer*
  code paths that feed those fillers from sources they don't yet consult (below).
- **Data:** ⚠️ the actual gap. The fillers query local dictionaries; a word is
  "uncovered" when the source dictionary simply doesn't contain it.

## Segmented coverage (raw % is misleading)

The headline "70% have a meaning" conflates fillable words with structurally-unfillable
ones. Segmenting 2,667 entries:

| Segment | Count | Note |
|---|---|---|
| **Core single-word common vocab** | 2,159 | the real fill target |
| Phrases / chunks / multiword | 468 | constructed A1 items (`phrase`, `chunk`, `noun phrase`, `time chunk`…) — won't have a dictionary headword; `gloss` is already 100% |
| Proper nouns (names/toponyms) | 40 | СУМ-11 / Балла / ЕСУМ **exclude proper nouns by design** |

**Core-vocab coverage (the honest target):**

| Section | Core coverage | True gap | Root cause of the gap |
|---|---|---|---|
| stress | 87.9% | ~262 | multi-word / rare forms the stress dict can't resolve |
| morphology | 82.7% | ~373 | VESUM can't decline some forms/multiword |
| **meaning** | **80.6%** | **~420** | word absent from local СУМ-11 |
| **translation** | **75.2%** | **~535** | **Балла is EN→UK one-way — no UK→EN reverse index** |
| **etymology** | **65.8%** | **~740** | ЕСУМ is root-based (36K) — misses derived/borrowed forms |
| **cefr** | **57.1%** | **~925** | PULS CEFR list is only ~5.9K words — a hard ceiling |

## Fill plan — by leverage × cost (local first, online second, honest "uncovered" third)

| # | Gap | Source we'd use | Local / Online | Code needed |
|---|---|---|---|---|
| **1** | translation ~535 | **Invert Балла's 79K EN→UK pairs → a UK→EN reverse index** | **LOCAL** (deterministic, no network) | new: build `balla_uk_en` reverse index + `_translation` consults it. **Highest ROI, zero quality risk.** |
| **2** | etymology ~740 | **ЕСУМ root-lemma fallback** (map derived→root, e.g. хвастливий→хвастати) | **LOCAL** | new: derived→root resolver in `_etymology` (reuse `_etymology_lookup_variants` + a stemming/root map) |
| **3** | meaning ~420 | **СУМ-20 via slovnyk.me live** for words missing from local СУМ-11 | **ONLINE** (slovnyk.me live-fallback infra already exists for synonyms/idioms) | extend `_meaning` to fall back to the slovnyk.me СУМ-20 fetch; cache like the existing slovnyk cache |
| 4 | proper nouns ~16 missing | **Wikipedia summary** (`query_wikipedia`) + a "personal name/toponym" tag | ONLINE | new: proper-noun enrichment path (1-line wiki gloss) |
| 5 | cefr ~925 | **No authoritative source beyond PULS 5.9K.** Option: heuristic band from GRAC corpus frequency (approximate, must be labelled "estimated") | partly LOCAL (GRAC), largely **UNCOVERED** | optional; do NOT fabricate exact CEFR — label estimates |
| 6 | phrases/chunks (468) | `gloss` (already 100%) is the meaning for constructed phrases | LOCAL | none — design call: accept gloss, don't force a dictionary "meaning" |

## Design refinement to flag (shrinks the denominator)

The Atlas currently emits **separate entries for inflected forms** (e.g. `Андрію` =
vocative of `Андрій`; `Олену` = accusative of `Олена`). These forms can't get their own
definition/translation (the lemma carries it), so they inflate the "missing meaning"
count. **Decision needed:** dedupe inflected forms to their lemma (and link forms → the
lemma's page) vs keep them as form-pages that inherit the lemma's enrichment. Either way
reduces the apparent gap without fetching any data.

## What is genuinely UNCOVERED (no source, local or online)

- **CEFR level beyond the PULS 5.9K list** — there is no larger CEFR-tagged Ukrainian
  word list. Either estimate from frequency (label it) or accept the ceiling honestly.
- **Etymology for some recent borrowings** absent from both ЕСУМ and Вікісловник.
- **Definitions for purely-constructed A1 phrases** — by nature not dictionary headwords.

## Execution order (after #1908)

1. Build the **Балла UK→EN reverse index** (local) → re-run `_translation` → +~535. *(biggest, safest win)*
2. Add **ЕСУМ root-fallback** to `_etymology` (local) → +~hundreds.
3. Add **СУМ-20 slovnyk.me online fallback** to `_meaning` (cached) → +~420 over time.
4. Proper-noun Wikipedia gloss path → +~16.
5. Decide CEFR policy (estimate-and-label vs accept ceiling) and the inflected-form dedupe.
6. Each step: code → unit test → `make atlas` regen → `verify_manifest` (0 violations) →
   measure coverage delta → commit. Ship incrementally; the §8 gate + freshness gate guard each regen.

**Every step is a normal lexicon-code PR; none requires new infrastructure.** Steps 1–2
are pure-local and should land first. Step 5's CEFR honesty matters: an estimated level
must be labelled estimated, never presented as authoritative (#M-4 / #1 quality).
