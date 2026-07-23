# UNLP & lang-uk GitHub Dataset Survey & Assessment

> **Purpose**: Comparative evaluation of public UNLP (Ukrainian Natural Language Processing / lang-uk) datasets vs. our curated repository corpus for fine-tuning open LLMs (Gemma 4 31B, Llama 4, Mistral) to Poltava literary standard.  
> **Date**: July 23, 2026

---

## 1. Survey of Public UNLP / lang-uk Datasets

| Dataset | Provider | Size | Content / Focus | Quality Assessment for Poltava Literary Alignment | Integration Status in Our Repo |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **`UA-GEC`** | UNLP / lang-uk | ~20K sents | Human-annotated Ukrainian grammar & Surzhyk error corrections | **GOLD / EXCELLENT**. High precision, curated by native Ukrainian linguists. | **Fully Ingested** (`data/sources.db` $\rightarrow$ `ua_gec_errors` table) |
| **`VESUM`** | Andriy Rysin et al. | 409K lemmas, 6.7M forms | Comprehensive morphological dictionary of Ukrainian | **GOLD / ESSENTIAL**. Authoritative morphological truth engine. | **Fully Integrated** (`data/vesum.db`) |
| **`UberText` / `UberText2`** | lang-uk / UNLP | 2.7B+ tokens | Massive web crawl (news, web, Wikipedia, books) | **MIXED / HIGH VOLUME**. Essential for scale, but contains newsroom calques (*канцеляризми*) and web translations. | Used for general reference |
| **`GRAC`** | Maria Shvedova et al. | 1B+ tokens | Regionally and chronologically annotated Ukrainian corpus | **HIGH / EXCELLENT**. Outstanding for regional dialect and historical Poltava research. | Queried via RAG |
| **`Ukrainian Wiki`** | Wikimedia / UNLP | 1.0M+ articles | Ukrainian Wikipedia articles | **HIGH / INFORMATIVE**. Clean encyclopedic Ukrainian, but lacks literary dialogue and pedagogical drills. | **Ingested** (`data/sources.db` $\rightarrow$ `wikipedia` table) |

---

## 2. Strengths & Limitations of Public Datasets

### A. Strengths of UNLP Datasets (`UA-GEC`, `VESUM`, `UberText`)
- **Scale**: `UberText` provides massive token volume required for foundational language modeling.
- **Precision Error Data**: `UA-GEC` is the single best dataset for training grammar-error detection models (correcting Surzhyk, calques, and spelling mistakes).
- **Morphological Ground Truth**: `VESUM` guarantees 100% accurate inflected forms and part-of-speech tags.

### B. Why Public Datasets Need Our Curated Corpus (`data/sources.db`)
Public web corpora (`UberText`) are collected from modern internet sources. In Ukrainian, generic web crawls contain three major systemic contaminants:
1. **Soviet Administrative Calques (*канцеляризми*)**: Awkward phrasing translated literally from Russian legal and news texts.
2. **Semantic Surzhyk**: Valid Ukrainian words used with Russian semantic meanings.
3. **Phonoaesthetic Violations**: Disregarding native Ukrainian euphony (*милозвучність*, alternation of *у/в* and *і/й*).

---

## 3. The Combined Hybrid Fine-Tuning Strategy

To fine-tune open models (Gemma 4 31B) to match Gemini 3.6 Flash level quality, we combine public UNLP datasets with our curated repository corpus:

```
                  ┌─────────────────────────────────────────┐
                  │ 1. Foundational Ukrainian Scale         │
                  │    UberText2 (UNLP)                     │
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │ 2. Poltava Literary Alignment           │
                  │    hramatka_literary_poltava_v1 (Ours)  │
                  │    (137,700 classic literary chunks)    │
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │ 3. Grammar Error & Surzhyk Correction   │
                  │    UA-GEC (UNLP)                        │
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │ 4. Pedagogical DPO Alignment            │
                  │    hramatka_uk_pedagogy_v1 (Ours)       │
                  │    (8/8 activity density preference)    │
                  └─────────────────────────────────────────┘
```

---

## 4. Conclusion & Action Item

- Public UNLP datasets (**`UA-GEC`** and **`VESUM`**) are world-class gold standards that we already rely on for dictionary verification and error detection.
- For fine-tuning LLMs specifically into **fluent, decolonized, literary Ukrainian (Poltava standard)**, `UberText` must be paired with our **`hramatka_literary_poltava_v1`** dataset to filter out modern web calques and restore native phonoaesthetic euphony.

---

*Survey compiled for the Learn Ukrainian Architecture Registry (July 2026).*
