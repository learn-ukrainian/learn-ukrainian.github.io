# Architecture Decision Record: Atlas Enrich-First Strategy & Deterministic Decolonization Engine

**Date:** 2026-09-11
**Status:** Approved
**Deciders:** Yellow Team (Gemini), Human Operator
**Parent Epic:** #4387 (Word Atlas / Lexicon)
**Tracking Issues:** #7913, #7914, #7915

---

## 1. Context & Problem Statement

The Ukrainian Word Atlas has reached **27,298 entries** (covering all A1–C2 Core curriculum vocabulary, all 11 grades of Ukrainian school textbooks, and curated teacher inventories up to Batch 20).

However, an audit of the current dataset revealed critical depth and quality issues:
1. **Old-Gate / Thin Pages Debt**:
   - 3,010 entries lack an English translation anchor or comprehensive definition cards.
2. **Incomplete Decolonization & Calque Mappings**:
   - Analysis of `data/lt_replacements.json` (9,380 pairs) showed that **82 Russianisms** already exist as headwords in `data/atlas.db` (e.g. `безкоштовний`, `відволікати`, `жених`, `датський`), but only **4** entries currently carry `is_russianism: true`.
   - Meanwhile, **2,841 authentic replacement words** (e.g. `безплатний`, `відвертати`, `наречений`, `данський`) already exist as articles in the Atlas, but are completely unlinked from their calque counterparts!
3. **The Single-Alternative Ingestion Bug**:
   - As discovered in `пилосос`, previous ingestion logic in `enrich_manifest.py` overwrote standard alternatives with a single suggestion from the last dictionary queried (Pavlo Shtepa's `порохосмок`, a purist neologism with **0 forms in VESUM**), dropping living authentic words taught in school textbooks (**`пилосмок`**, **`порохотяг`**, **`пилотяг`**, each having **16 VESUM forms**).
4. **Mechanical Synonym Hallucinations**:
   - Naive WordNet synset mappings injected false cross-language cognates (e.g. `пилосос` listing `вакуум` as a synonym because of the English word "vacuum").

---

## 2. Decision: Enrich-First + Clustered Inflow (Depth Over Raw Breadth)

We explicitly adopt an **Enrich-First** strategy over raw bulk expansion:

1. **Depth Over Raw Quantity**:
   - Expanding from 27,000 to 35,000 words without a robust enrichment engine would explode the thin-page backlog from 3,010 to 8,000+, scaling up noisy synonyms and unflagged Russianisms.
   - Grounded in the core project tenet: *"Quality over quantity. 5 excellent modules beat 55 mediocre ones."*
2. **Zero-LLM Deterministic Pipelines**:
   - **No LLMs are to be used for lexicographical definitions, synonym extraction, or decolonization alternatives.**
   - LLMs carry severe Russian-imperial training priors, hallucinate false synsets, and are non-deterministic.
   - All reconciliation, validation, and wiring must be executed by deterministic Python scripts against local ground-truth SQLite databases (`data/sources.db`, `data/vesum.db`, `data/lt_replacements.json`, `data/lexicon/heritage_pairs.yaml`).
3. **Clustered Gap Inflow (The Vacuum Effect)**:
   - When an existing entry is enriched or decolonized (e.g. `пилосос`), the engine detects any missing authentic alternatives that are verified in VESUM and attested in school textbooks (`пилосмок`, `порохотяг`, `пилотяг`, `кримець`).
   - These missing words are admitted immediately as **100% fully enriched, zero-debt articles** (VESUM paradigm, stress, CEFR, authentic СУМ-20/ВТС definitions, learner EN gloss, textbook citations).
   - Bulk curriculum expansion (NUS Grades 1–11) will only run *after* the enrichment pipeline is fully stabilized, ensuring new entries arrive enriched at intake.

---

## 3. Engine Architecture: `reconcile_calque_clusters.py`

The deterministic pipeline follows five strict stages:

```
[Atlas Headword Scanner]
         │
         ▼
[Multi-Source Candidate Extraction]
  ├── lt_replacements.json (9,380 pairs)
  ├── heritage_pairs.yaml (252 curated pairs)
  ├── Textbook FTS Regex (e.g. "Пилосос (пилосмок, порохотяг, пилотяг)")
  └── Modern Dictionaries (СУМ-20 / ВТС)
         │
         ▼
[VESUM Morphological Validation Gate]
  ├── Validated (VESUM forms > 0, matching POS) ──> Standard Alternative
  └── Unattested (VESUM forms == 0) ──────────────> Quarantined / Purist Note
         │
         ▼
[Deduplicated Union & Graph Cross-Wiring]
  ├── calque_warning.standard_alternatives updated
  ├── Prune spurious WordNet synsets
  └── Mutual bidirectional synonyms wired across cluster
         │
         ▼
[Clustered Admission Dispatch]
  └── If authentic alternative is missing from Atlas:
      auto-construct and admit as Tier-1 fully enriched article
```

---

## 4. Consequences & Guarantees

- **Richness Invariant**: Zero richness regressions on every merge (`poc_thin_pages <= 10550`, `search_no_visible_gloss <= 5`, `old_gate_no_english_anchor <= 3010`).
- **Linguistic Authenticity**: Russianisms are visibly flagged, while authentic Ukrainian words taught in schools are highlighted and mutually cross-linked.
---

## 5. Enrichment Versioning Contract

To ensure idempotency and prevent redundant re-enrichment of already up-to-date entries, the pipeline implements an explicit versioning gate:

1. **`enrichment_version` Field**:
   - Every admitted or reconciled entry carries an integer `enrichment_version` in its payload (and `updated_at` ISO-8601 timestamp):
     * `0`: Legacy / unvetted baseline.
     * `1`: Initial enrichment (single-source slovnyk / Wiktionary).
     * `2`: Current standard: Multi-source textbook integration, VESUM morphological paradigm gating, deterministic decolonization union, and verified mutual synonym wiring.
2. **Incremental Execution Logic**:
   ```python
   CURRENT_ENRICHMENT_VERSION = 2

   def should_enrich(entry: dict, force: bool = False) -> bool:
       if force:
           return True
       return entry.get("enrichment_version", 0) < CURRENT_ENRICHMENT_VERSION
   ```
3. **Selective Re-enrichment**:
   - Upgrading the enricher (e.g. adding a new authoritative source like modern СУМ-20 or a new textbook grade) bumps `CURRENT_ENRICHMENT_VERSION` to `3`.
   - The runner automatically detects and processes only the stale delta (`version < 3`), preserving all up-to-date entries and minimizing runtime.
