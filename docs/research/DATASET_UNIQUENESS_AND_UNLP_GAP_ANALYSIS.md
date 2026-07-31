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

## How the historical hypothesis would need to be re-tested

The earlier document collapsed several different questions into a single
novelty claim. Those questions must be kept separate. Whether a public
collection exists is an inventory question. Whether two collections overlap is
a record-lineage and content-comparison question. Whether a collection
represents literary, regional, historical, or pedagogical Ukrainian well is a
linguistic and coverage question. Whether a record may be redistributed or
used for model training is a rights-and-permission question. A positive answer
to any one question supplies no evidence for the others.

A future inventory would therefore need stable dataset identifiers, canonical
catalog or source URLs, version or retrieval dates, declared maintainers, and
the terms attached to the exact version examined. Descriptions copied from a
catalog page would be evidence about the publisher's claim, not independent
confirmation of corpus composition or quality. Likewise, a repository import
or database join would show that bytes were locally available, not where each
record originated or which downstream uses were permitted.

The candidate-specific side of a comparison would require record-level source
identity, work and edition identity, acquisition receipts, content hashes, and
derivation lineage. It would also require separately evidenced copyright,
license, redistribution, and model-training fields. Unknown or conflicting
status would remain unresolved and fail closed. Cleaning language, removing
duplicates, or attaching internal metadata could improve a technical artifact,
but none of those operations can reconstruct a missing external lineage or
grant a missing permission.

### Comparison dimensions that remain potentially useful

The historical notes point toward real research dimensions, but not toward a
verified winner. A future comparison could describe:

- source genre and time-period coverage;
- regional, dialectal, conversational, archaic, cognate, and marked-language
  coverage;
- whether content is raw text, correction pairs, question-answer material, or
  another documented structure;
- the presence and provenance of linguistic annotations;
- exact duplicate and near-duplicate overlap under a frozen method;
- the availability of stable record-level citations and hashes;
- declared usage restrictions and contamination exclusions;
- one documented consumer need that the proposed records actually satisfy.

These dimensions must not be compressed into labels such as *clean*,
*decolonized*, *gold*, *native*, or *unique* without criteria and attributed
evidence. In particular, a text's literary register does not establish its
rights status, and a permissive license does not establish linguistic
representativeness. Instruction formatting is also a transformation, not
proof of novelty: the underlying work, source edition, and transformation
lineage still determine whether the record is independent and usable.

### Ukrainian quality without erasing variation

The durable quality question is broader than removing obvious calques. A
useful Ukrainian collection must make it possible to distinguish documented
errors from legitimate historical, regional, dialectal, conversational,
archaic, cognate, or register-marked forms. That requires qualified Ukrainian
review, source citations, uncertainty, and an explicit unresolved state.
Automated morphology or exact-string comparison can route evidence, but it
cannot by itself decide that a less frequent or non-modern form is wrong.

Coverage claims would need denominators and frozen category definitions.
Examples selected because they demonstrate a desired contrast cannot also
serve as uncontaminated evidence that a system handles that contrast. Public
evaluation material must remain separated from training and preference data.
The useful outcome is therefore a reproducible coverage and provenance
contract, not a temporary claim that one collection or model is best.

### Successor boundary

The immediate successor to these notes is not a release. It is a
provenance-rich source-record contract followed, only under a separately
approved issue, by a deliberately small rights-cleared pilot around one real
consumer need. Such a pilot would test whether official source and rights
evidence can be collected, reviewed, hashed, and validated without carrying
forward the failed candidate's assumptions. It would not inherit the
candidate's proposed name, counts, purity language, or release trajectory.

Until that evidence exists, the tables and diagrams above remain historical
inputs for forming questions. They are not a current market survey, dataset
card, admission decision, training plan, or publication record.

---

*Analysis recorded for the Learn Ukrainian Architecture Registry.*
