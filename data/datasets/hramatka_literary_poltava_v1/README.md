# Literary Ukrainian Candidate Collection (`hramatka_literary_poltava_v1`)

> **Status:** Internal candidate collection; not training-ready or approved for
> publication.
> **Target audience:** Dataset auditors and Ukrainian NLP researchers.
> **Purpose:** Evaluate whether the selected literary records can become a
> provenance-rich contribution to open-weight Ukrainian model development.

The current JSONL contains 5,000 records, but it does not yet carry the
release-level provenance, source license, redistribution status, deduplication
receipt, or frozen train/validation/test split required for a defensible
training release. The labels "pure," "decolonized," and "Poltava standard" have
not been established by an expert audit and must not be used as dataset quality
claims.

The governing strategy is
[Ukrainian Open-Model Data Infrastructure: North Star](../../../docs/strategy/UKRAINIAN_OPEN_MODEL_DATA_INFRASTRUCTURE_NORTH_STAR.md).

---

## Research hypothesis

Generic web corpora can contain:
1. **Soviet Bureaucratic Calques (*канцеляризми*)**: Rigid, non-native phrasing translated literally from Russian.
2. **Semantic Surzhyk**: Valid Ukrainian words assigned Russian meanings.
3. **Phonoaesthetic Violations**: Disregarding Ukrainian euphony rules (*милозвучність*, alternation of *у/в*, *і/й*).

---

These are hypotheses to measure against existing Ukrainian corpora and
quality-filtering work, not established properties of every web crawl.

## Candidate collection overview

Modern Literary Ukrainian (*сучасна українська літературна мова*) was historically synthesized from the **Poltava-Middle Dnieper dialect region** (Kotlyarevsky, Shevchenko, Nechuy-Levytsky, Franko, Lesya Ukrainka).

The collection contains selected, chronologically tagged passages exported
from the project's literary database. Its current source mix includes:
- **Classic 19th Century Literature** (Kotlyarevsky, Shevchenko, Nechuy-Levytsky, Marko Vovchok)
- **Modern 20th Century & Contemporary Ukrainian** (Rylsky, Tychyna, Kostenko, Stus)
- **Ukrainian School Textbooks** (Grades 1–11, 2019 Pravopys)

---

## Required audit before training or release

1. Link every record to a stable source identifier and acquisition record.
2. Record source license, copyright, redistribution, and model-training status.
3. Verify author, work, year, language period, genre, and translation origin.
4. Detect exact and near duplicates against training and evaluation inventories.
5. Measure period, author, genre, region, register, and domain balance.
6. Review samples for OCR artifacts, machine translation, editorial
   modernization, Russian-language leakage, and encoding problems.
7. Define consumer-specific, author-disjoint splits and contamination receipts.
8. Obtain Ukrainian linguistic review for any quality, purity, or
   decolonization claim.

No fine-tuning result is claimed. Training remains parked until a scoped
consumer need, a reviewed data card, and explicit approval exist.
