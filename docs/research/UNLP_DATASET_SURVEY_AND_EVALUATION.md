# UNLP & lang-uk GitHub Dataset Survey & Assessment

> **Current authority — superseded and non-operational:**
> [Issue #6058](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6058)
> and its merged [Literary Poltava candidate audit](hramatka_literary_poltava_candidate_audit.md)
> are the current authority for the Literary Poltava candidate. The audit's
> `rebuild_required` verdict excludes every candidate record pending rights and
> provenance evidence. This survey does **not** authorize training, upload,
> release, redistribution, publication, or claims of purity, provenance,
> rights, or readiness. It is historical context only.
>
> **Historical purpose**: former comparative survey and proposed fine-tuning
> rationale; do not treat it as a current assessment or action plan.
>
> **Date**: July 23, 2026

---

## Historical survey of public UNLP / lang-uk datasets

The comparisons and repository integration statements below are historical
notes. They were not revalidated by the merged audit and must not be used as
current quality, licensing, provenance, or use-authority conclusions.

| Dataset | Provider | Size | Content / Focus | Quality Assessment for Poltava Literary Alignment | Integration Status in Our Repo |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **`UA-GEC`** | UNLP / lang-uk | ~20K sents | Human-annotated Ukrainian grammar & Surzhyk error corrections | **GOLD / EXCELLENT**. High precision, curated by native Ukrainian linguists. | **Fully Ingested** (`data/sources.db` $\rightarrow$ `ua_gec_errors` table) |
| **`VESUM`** | Andriy Rysin et al. | 409K lemmas, 6.7M forms | Comprehensive morphological dictionary of Ukrainian | **GOLD / ESSENTIAL**. Authoritative morphological truth engine. | **Fully Integrated** (`data/vesum.db`) |
| **`UberText` / `UberText2`** | lang-uk / UNLP | 2.7B+ tokens | Massive web crawl (news, web, Wikipedia, books) | **MIXED / HIGH VOLUME**. Essential for scale, but contains newsroom calques (*канцеляризми*) and web translations. | Used for general reference |
| **`GRAC`** | Maria Shvedova et al. | 1B+ tokens | Regionally and chronologically annotated Ukrainian corpus | **HIGH / EXCELLENT**. Outstanding for regional dialect and historical Poltava research. | Queried via RAG |
| **`Ukrainian Wiki`** | Wikimedia / UNLP | 1.0M+ articles | Ukrainian Wikipedia articles | **HIGH / INFORMATIVE**. Clean encyclopedic Ukrainian, but lacks literary dialogue and pedagogical drills. | **Ingested** (`data/sources.db` $\rightarrow$ `wikipedia` table) |

---

## Historical strengths and limitations discussion

### A. Strengths of UNLP Datasets (`UA-GEC`, `VESUM`, `UberText`)

- **Scale**: `UberText` provides massive token volume required for foundational language modeling.
- **Precision Error Data**: `UA-GEC` is the single best dataset for training grammar-error detection models (correcting Surzhyk, calques, and spelling mistakes).
- **Morphological Ground Truth**: `VESUM` guarantees 100% accurate inflected forms and part-of-speech tags.

### B. Historical rationale for a proposed corpus

This section records a former rationale. It does not establish that the
repository corpus is curated, rights-cleared, linguistically superior, or fit
for use. It also does not determine the quality of public web corpora.

The proposal characterized generic web crawls as having three systemic issues:
1. **Soviet Administrative Calques (*канцеляризми*)**: Awkward phrasing translated literally from Russian legal and news texts.
2. **Semantic Surzhyk**: Valid Ukrainian words used with Russian semantic meanings.
3. **Phonoaesthetic Violations**: Disregarding native Ukrainian euphony (*милозвучність*, alternation of *у/в* and *і/й*).

---

## Withdrawn historical hybrid fine-tuning proposal

This diagram records a proposed combination of public datasets with the
candidate corpus. It is not a workflow to execute and does not establish
permission to combine, upload, train on, release, redistribute, or publish any
data.

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

## Historical conclusion

The former conclusion that a candidate dataset should be paired with public
datasets for fine-tuning is withdrawn. The quality labels and use assertions
above are historical, not current authority. No use of the candidate is
authorized unless a future separately approved effort first completes a
rights-cleared rebuild and fresh audit.

---

*Survey compiled for the Learn Ukrainian Architecture Registry (July 2026).*
