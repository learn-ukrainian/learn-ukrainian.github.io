# TOMBSTONE: Archived `uldr_v1_production`

**Status:** ARCHIVED / SUPERSEDED / DO NOT USE FOR TRAINING OR SFT/DPO ALIGNMENT
**Archived Date:** 2026-09-22
**Governing Issue:** [#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321)
**Related Issues:** [#8338](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8338), [#8340](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8340), [#8341](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8341), [#8342](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8342), [#8141](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8141), [#8330](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8330)

---

## 1. Background & Reason for Archival

This directory (`uldr_v1_production`) contains the initial 6,000 SFT and 3,000 DPO synthetic trajectories assembled in Phase 3.7.

Comprehensive dataset audit and empirical evaluation revealed critical flaws:
1. **Contaminated Reasoning Chains:** Early synthetic generations included hallucinated justifications, grammatical inconsistencies, and occasional Soviet calques embedded within the `<thought>` traces.
2. **Pre-training Reality & Foundation Model Shifts:** As demonstrated in UNLP 2026 literature (*Paniv et al.*) and the release of Gemma 4, modern open-weights models achieve top-tier general Ukrainian language fluency out of the box without requiring expensive domain pre-training.
3. **Shift to High-Precision Moat:** Our project value resides exclusively in **surgical alignment and decolonization**—calque defense, valency correction, authentic phraseology, and dialect protection—not bulk synthetic text.

---

## 2. Strict Prohibition

> [!CAUTION]
> **DO NOT USE THIS DATASET FOR MODEL TRAINING, FINE-TUNING, PREFERENCE TUNING (DPO/ORPO), OR REPLAY BUFFERS.**
>
> Ingesting these shards into training pipelines risks poisoning model outputs with outdated synthetic artifacts and unverified reasoning chains.

---

## 3. Active Replacements

All ongoing dataset curation and alignment work is organized into modular components under:
- `data/projects/open_model_data/components/decolonization/` (#8340)
- `data/projects/open_model_data/components/idioms/` (ULIF phraseology)
- `data/projects/open_model_data/components/grammar/` (#8342)
- `data/projects/open_model_data/components/textbooks/` (#8341)
- `data/projects/open_model_data/components/dialects/` (#8141)

Gold calibration rules remain maintained and active in:
- `data/projects/open_model_data/release/correction_protection_v1/`

---

## 4. Evidence & Literature References

- **Empirical Literature:**
  - Paniv, M., Kyrylov, V., & Babych, B. (2026). *"Data-Efficient Adaptation of Multilingual LLMs to Ukrainian"*, Proceedings of the 5th Workshop on Ukrainian Natural Language Processing (UNLP 2026), pages 144–154. [https://aclanthology.org/2026.unlp-1.14/](https://aclanthology.org/2026.unlp-1.14/). Demonstrates that targeted, data-efficient adaptation of multilingual models (e.g. Gemma-3-12B) with curated instruction and alignment datasets outperforms massive indiscriminate pre-training, showing that uncurated corpora degrade target language nuances and authentic Ukrainian syntax.
- **Foundation Model Benchmarks:**
  - Google Gemma 4 (Hugging Face Open Ukrainian LLM Leaderboard, 2026): Modern foundation models demonstrate strong native Ukrainian comprehension and generation out-of-the-box, confirming that expensive custom domain pre-training from unverified web scrapes is obsolete and dataset engineering must focus on human-grounded alignment, morphological precision, and decolonization defense.
- **Internal Strategic & Quality Audits:**
  - [#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321): Realignment of Open Model Data into modular components.
  - [#8338](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8338): Advisory council deliberation and quarantine of legacy synthetic shards.
  - [#8340](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8340): Anti-calque and decolonization component specification.
  - [#8141](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8141): Dialectal and historical preservation component specification.
  - [#8341](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8341): Authentic Ukrainian textbook extraction component specification.
  - [#8342](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8342): Ukrainian grammar valency component specification.
