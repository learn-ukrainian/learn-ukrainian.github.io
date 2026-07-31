# Gap Analysis: Public Ukrainian Datasets vs. Our Unique Literary Alignment Asset

> **Current authority — superseded research claims:**
> [Issue #6058](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6058)
> and its merged [Literary Poltava candidate audit](hramatka_literary_poltava_candidate_audit.md)
> are the current authority for the candidate called
> `hramatka_literary_poltava_v1`. The audit's `rebuild_required` verdict finds
> no evidence for rights, provenance, redistribution, or model-training
> permission. This document does **not** authorize training, upload, release,
> redistribution, publication, or claims of purity, uniqueness, provenance,
> or rights. It remains only as historical research notes.
>
> **Historical purpose**: former survey intended to support a novelty and gap
> claim; its candidate-specific conclusions are unestablished.
>
> **Date**: July 24, 2026

---

## Historical survey of publicly available Ukrainian datasets

This survey's scope, completeness, comparative characterizations, and overlap
conclusions were not revalidated by the merged audit. They must not be used to
make a current claim about third-party datasets or the candidate collection.

We evaluated all major public Ukrainian datasets on HuggingFace Hub and GitHub (`lang-uk`, `UNLP`, HuggingFace Datasets registry):

| Dataset Name | Source / Maintainer | Type | Major Limitations | Does it overlap with our dataset? |
| :--- | :--- | :--- | :--- | :---: |
| **`lang-uk/ubertext2`** | UNLP / `lang-uk` | Uncurated Web Scrape | Raw web text (news, blogs). Unformatted, contains Soviet administrative calques (*канцеляризми*) and web noise. | **NO** (UberText is raw web crawl, not instruction-formatted or literary). |
| **`ua-gec`** | UNLP / Oleksiy Syvokon | Grammar Error Correction | 20,000 GEC pairs. Excellent for spellchecking, but **not designed for instruction tuning or literary alignment**. | **NO** (GEC only, no literary prose or pedagogical drill synthesis). |
| **`yarysh/ukrainian-alpaca`** | Open Source | Machine-Translated | Translated from English Alpaca/ShareGPT. **Suffers from heavy machine-translation calques and English syntax**. | **NO** (Synthetic translation, not authentic Ukrainian literature). |
| **`dmytro/ukrainian-qa`** | Open Source | Wikipedia QA | Short QA pairs from Wikipedia. Factual recall only, no literary style or pedagogy. | **NO** (Encyclopedic facts only). |

---

## Historical gap hypothesis

This document formerly asserted that no public dataset supplied the following
features. That conclusion is unestablished and is retained as a record of the
earlier hypothesis only:

1. **Instruction-Formatted Literary Prose (Poltava Standard)**:
   - Zero datasets exist that format authentic 19th–21st century Ukrainian literature (Shevchenko, Kulish, Franko, Lesya Ukrainka, Kostenko) into prompt-response instruction triples (`<|im_start|>user ... <|im_end|>`).
2. **Decolonized & Chronologically Tagged Text**:
   - Zero datasets classify passages by historical language period (`old_east_slavic`, `middle_ukrainian`, `modern`) with verified author metadata.
3. **Structured Pedagogical Drill Synthesis**:
   - Zero datasets provide DPO preference pairs for 8/8 activity types, B1 case government rules, and State Standard 2024 pedagogical alignment.

---

## Historical description of a proposed asset

This was a proposed description of **`hramatka_literary_poltava_v1`**, not an
accurate current inventory, release notice, or authorization to use the
candidate:

```
┌───────────────────────────────────────────────────────────────────────────┐
│               HRAMATKA LITERARY POLTAVA DATASET (v1)                       │
├───────────────────────────────────────────────────────────────────────────┤
│ • 10,000 Instruction-Formatted Triples (SFT)                             │
│   - Source: Our 137,723-chunk unabridged literary database                │
│   - Authors: 134 native Ukrainian classic & modern writers                 │
│   - Metadata: Author, work, composition year, language period tag         │
│   - Quality: Zero machine translation, zero Soviet administrative calques │
├───────────────────────────────────────────────────────────────────────────┤
│ • 2,500 Pedagogical Preference Pairs (DPO)                                │
│   - Source: Hramatka B1 curriculum benchmark                              │
│   - Alignment: State Standard 2024, 8/8 activity density, 0 Russianisms   │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Historical value proposition

The following value claims were proposal-era aspirations, not verified facts:

- The candidate could replace machine-translated instruction data with
  authentic native Ukrainian literary prose.
- The candidate could supply high-precision instruction-tuning material for
  high-register Ukrainian.

They cannot support release, redistribution, upload, training, or publication.
The audit requires a rights-cleared rebuild before any separately authorized
future evaluation of such claims.

---

*Analysis recorded for the Learn Ukrainian Architecture Registry.*
