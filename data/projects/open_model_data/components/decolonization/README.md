# Component: Ukrainian Decolonization, Anti-Calque Reasoning & Authentic Defense

**Governing Issue:** [#8340](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8340)
**Parent Epic:** [#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321)
**Status:** Accepted (`audit_dataset_acceptance.py` exit code 0)

## Overview
This component provides a curated, verified catalog and training/evaluation corpus of 250 distinct linguistic phenomena (500 total records: 400 train, 100 eval) addressing Russianisms, calqued officialese, and Soviet linguistic distortion in Ukrainian, while strictly defending authentic Ukrainian expressions against hyperpurism.

## Core Properties
1. **Real Content Share (70/30 Invariant)**:
   - 350 substantive correction records (70%)
   - 150 protective authentic control records (30%) defending legitimate Ukrainian words and idioms (e.g. *приймати рішення*, *відігравати роль*, *кобіта*, *наразі*, *протягом дня*, *будь ласка*, *завдяки зусиллям*, *йдеться про*, *мати на увазі*).
2. **Category Balance**:
   - `calque_lexical`: 120 records (24%) across 60 phenomena
   - `calque_syntactic`: 130 records (26%) across 65 phenomena
   - `calque_prepositional`: 100 records (20%) across 50 phenomena
   - `protective_authentic`: 150 records (30%) across 75 phenomena
3. **Disjoint Held-Out Evaluation Split**:
   - 100% disjoint target phenomena between train (200 phenomena) and eval (50 phenomena) verified under aspect normalization.
   - 0 exact query leakage and 0% high 4-gram lemma containment.
4. **Authority Grounding**:
   - Борис Антоненко-Давидович (*«Як ми говоримо»*)
   - Олександр Пономарів (*«Культура слова»*)
   - СУМ-20 (Словник української мови у 20 томах)
   - Український правопис (2019)
   - UA-GEC v2 (Syvokon et al., 2023)
   - 0 Soviet СУМ-11 normative citations, 0 bilingual translation dictionaries.
5. **Quality & Diversity**:
   - Distinct QA pairs: 500 / 500 (near-duplicate template rate: 0.0%)
   - High entropy query and reasoning traces across administrative, journalistic, educational, and conversational registers.
   - Passes all 7 automated checks of `scripts/projects/open_model_data/audit_dataset_acceptance.py`.
