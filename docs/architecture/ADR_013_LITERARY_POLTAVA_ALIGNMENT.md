# ADR 013: Literary Ukrainian Alignment (Poltava Standard) & Open Model Training Strategy

> **Current authority — superseded and non-operational:**
> [Issue #6058](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6058)
> and its merged [Literary Poltava candidate audit](../research/hramatka_literary_poltava_candidate_audit.md)
> are the current authority for `hramatka_literary_poltava_v1`. The audit's
> `rebuild_required` verdict finds rights and provenance unknown and excludes
> every candidate record pending evidence. This ADR does **not** authorize
> training, upload, release, redistribution, or any purity, provenance, or
> rights claim. It is retained only as a historical record of a withdrawn
> proposal; do not follow its decision or strategy language.
>
> **Historical status**: formerly APPROVED / IMPLEMENTATION; withdrawn for
> current use
>
> **Date**: July 23, 2026  
> **Authors**: Lead Architecture Review, Sol (`gpt-5.6-sol`), UNLP Dataset Task Force  
> **Target Epic**: #4542 (Hramatka Model Alignment & UNLP Dataset Release)

---

## Historical context and problem statement

The text in this section records the rationale that informed the July 2026
proposal. It is not a verified characterization of the candidate corpus or a
current implementation direction.

Modern Literary Ukrainian (*сучасна українська літературна мова*) is historically grounded in the **Poltava-Middle Dnieper dialect region** (Kotlyarevsky, Shevchenko, Nechuy-Levytsky, Marko Vovchok, Rylsky, Franko/Lesya Ukrainka synthesis).

General-purpose open models (Gemma 4 31B, Llama 4, Mistral) are pre-trained on uncurated global web crawls (Common Crawl, Wikipedia, news scrapes). In Ukrainian, these web crawls suffer from three major systemic flaws:
1. **Soviet Bureaucratic Calques (*канцеляризми*)**: Awkward, non-native phrasing translated literally from Russian administrative texts.
2. **Semantic Surzhyk**: Valid Ukrainian words assigned Russian meanings (e.g. *лук* as onion instead of bow).
3. **Phonoaesthetic Violations**: Disregarding Ukrainian euphony rules (*милозвучність*, proper alternation of *у/в* and *і/й*).

The historical proposal asserted that prompt engineering alone could not fix
missing pre-training distributions and proposed fine-tuning on purportedly
clean, chronologically tagged Ukrainian literature and textbooks. The merged
audit now prevents treating those descriptions as established or actionable.

---

## Historical Decision 1: Proposed corpus use (`data/sources.db`)

This ADR previously described the repository as containing the largest curated,
decolonized, and chronologically tagged Ukrainian corpus available:
- **137,723 Literary Text Chunks**: Tagged by author, work, year, genre, and language period (Early Ruthenian $\rightarrow$ 19th c. Poltava Classic $\rightarrow$ Modern Literary 2019 Pravopys).
- **54,979 Grade 1–11 Textbook Chunks**: Pure normative school Ukrainian across subjects.
- **1,029 Curated Wikipedia Articles**.

These were proposal-era assertions, not audit-backed findings. They must not be
read as evidence of provenance, rights, linguistic quality, decolonization, or
fitness for any downstream use.

---

## Historical Decision 2: Proposed release of `hramatka_literary_poltava_v1`

The proposal stated that **`hramatka_literary_poltava_v1`** had been built and
exported:
- **Dataset Path**: `data/datasets/hramatka_literary_poltava_v1/hramatka_literary_poltava_v1.jsonl`
- **Exporter Script**: `scripts/dataset/export_literary_poltava_dataset.py`
- **Passage Count**: 5,000 curated, high-register literary passages tagged by author and period.

---

## Withdrawn historical fine-tuning strategy

The following was a historical proposal, not a plan to execute:

1. Continued pre-training or SFT on the candidate collection.
2. Pedagogical preference alignment using a separate claimed dataset.
3. An open-weights model outcome framed around literary euphony and lesson
   authoring.

No part of this proposal authorizes training, model adaptation, dataset upload,
redistribution, release, or publication. A future, separately approved effort
would first need a rights-cleared rebuild and a new audit; this document grants
no permission.

---

*Recorded as a historical, non-operational record for the Learn Ukrainian
Architecture Registry (July 2026).*
