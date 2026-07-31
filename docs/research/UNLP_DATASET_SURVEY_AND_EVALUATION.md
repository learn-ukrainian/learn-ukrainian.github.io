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

## How to interpret this comparison now

The table records the categories and impressions used by the former proposal;
it is not a current rating of the named projects. Labels such as *gold*,
*excellent*, *clean*, *mixed*, or *fully integrated* need a stated criterion,
an attributable source, and a current verification date before they can
support a decision. The existence of a local table, index, or RAG adapter would
show an integration state only. It would not prove the completeness,
authenticity, licensing, representativeness, or linguistic authority of the
underlying collection.

The named resources also serve different purposes, so a single quality order
would be misleading. A morphological lexicon, a grammar-error corpus, a large
web corpus, a regional corpus, and an encyclopedia are not interchangeable
training ingredients or evaluation baselines. Their useful comparison begins
with a documented consumer question: for example, whether a tool needs
inflection evidence, attested regional usage, editing examples, source text, or
encyclopedic context. Only after that question is fixed can coverage,
provenance, rights, format, and limitations be assessed independently.

### Capability evidence and permission evidence

Capability evidence answers what a resource contains or supports. Permission
evidence answers which uses are allowed for the exact obtained version. The
former proposal treated availability and local ingestion as if they implied
permission to combine and train. They do not. A future assessment must retain
the source or catalog URL, version and retrieval date, content receipt, license
or terms evidence, redistribution status, model-training permission, and any
jurisdictional uncertainty. Unknown or conflicting fields must fail closed
rather than inherit a permissive assumption from another version or a project
homepage.

The same separation applies to derived records. Tokenization, normalization,
error annotation, instruction formatting, or passage extraction can create a
new technical representation, but the derived record still needs its parent
content hash and a transformation receipt. A transformation cannot erase the
source work, edition, author, or rights lineage. Nor can a downstream
repository claim make an upstream license more permissive.

### Linguistic coverage and protected variation

The historical concern about calques and translated syntax remains a research
question, not a blanket characterization of public Ukrainian data. A credible
study would define the phenomenon, sample under a frozen method, cite source
contexts, and retain reviewer uncertainty. It would also include clean
no-change controls so that editing pressure itself is measured.

Most importantly, quality review must protect legitimate historical,
regional, dialectal, conversational, archaic, cognate, and register-marked
Ukrainian. Frequency, modern spelling, an exact reference string, or a
morphological lookup is not sufficient authority to normalize such material.
Qualified Ukrainian reviewers need access to source evidence and multiple
acceptable references, plus an unresolved outcome when the evidence does not
support a confident decision. Coverage should be reported by declared strata,
not converted into a purity score.

### Why the former pipeline diagram is non-operational

The diagram orders resources as though combination were already approved and
the candidate were an admitted intermediate asset. The merged audit disproves
that premise for the candidate: all 5,000 records lack the required provenance
and rights evidence, and cleaning cannot repair that missing lineage. The
diagram also mixes public evaluation, possible training material, linguistic
tools, and preference data without contamination boundaries. Following it
would therefore bypass both admission and evaluation integrity.

A future architecture would start with independently validated source records
and one declared consumer need. It would assign each record an explicit role,
such as excluded, evaluation-only, or a separately reviewed training
candidate. Evaluation records would remain outside training and preference
views. Any later model experiment would need its own operator-approved issue,
frozen inputs and prompts, contamination checks, and a qualified-human
interpretation contract. None of those later steps is authorized by this
historical survey.

### Durable value of the record

Retaining this document is useful because it shows which assumptions once
drove the proposed strategy: that local availability implied usability, that
format implied novelty, and that broad quality labels could stand in for
record-level evidence. The corrective lesson is durable across tools and base
models. Source identity, rights evidence, derivation lineage, protected
variation, role separation, and consumer-specific coverage must be explicit
before scale or model fashion becomes relevant.

Until a new evidence-backed survey is commissioned, the material above may be
used to identify questions and candidate comparison dimensions only. It must
not be cited as a current endorsement, integration receipt, permission grant,
release plan, or ranking of Ukrainian resources.

---

*Survey compiled for the Learn Ukrainian Architecture Registry (July 2026).*
