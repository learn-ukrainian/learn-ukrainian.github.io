# ADR 013: Literary Ukrainian Alignment (Poltava Standard) & Open Model Training Strategy

> **Status**: APPROVED / IMPLEMENTATION  
> **Date**: July 23, 2026  
> **Authors**: Lead Architecture Review, Sol (`gpt-5.6-sol`), UNLP Dataset Task Force  
> **Target Epic**: #4542 (Hramatka Model Alignment & UNLP Dataset Release)

---

## Context & Problem Statement

Modern Literary Ukrainian (*сучасна українська літературна мова*) is historically grounded in the **Poltava-Middle Dnieper dialect region** (Kotlyarevsky, Shevchenko, Nechuy-Levytsky, Marko Vovchok, Rylsky, Franko/Lesya Ukrainka synthesis).

General-purpose open models (Gemma 4 31B, Llama 4, Mistral) are pre-trained on uncurated global web crawls (Common Crawl, Wikipedia, news scrapes). In Ukrainian, these web crawls suffer from three major systemic flaws:
1. **Soviet Bureaucratic Calques (*канцеляризми*)**: Awkward, non-native phrasing translated literally from Russian administrative texts.
2. **Semantic Surzhyk**: Valid Ukrainian words assigned Russian meanings (e.g. *лук* as onion instead of bow).
3. **Phonoaesthetic Violations**: Disregarding Ukrainian euphony rules (*милозвучність*, proper alternation of *у/в* and *і/й*).

Prompt engineering alone cannot fix missing pre-training distributions. To make open models like Gemma 4 31B truly fluent in high-register literary Ukrainian, we must fine-tune them on clean, chronologically tagged Ukrainian literature and textbooks.

---

## Decision 1: Utilizing Our Pristine Corpus (`data/sources.db`)

Our repository contains the largest curated, decolonized, and chronologically tagged Ukrainian corpus available:
- **137,723 Literary Text Chunks**: Tagged by author, work, year, genre, and language period (Early Ruthenian $\rightarrow$ 19th c. Poltava Classic $\rightarrow$ Modern Literary 2019 Pravopys).
- **54,979 Grade 1–11 Textbook Chunks**: Pure normative school Ukrainian across subjects.
- **1,029 Curated Wikipedia Articles**.

We do **not** rely on unverified external web dumps. Our corpus is hand-verified, cleaned, and free of Soviet administrative calques.

---

## Decision 2: Release of `hramatka_literary_poltava_v1` Dataset for UNLP

We have built and exported **`hramatka_literary_poltava_v1`**:
- **Dataset Path**: `data/datasets/hramatka_literary_poltava_v1/hramatka_literary_poltava_v1.jsonl`
- **Exporter Script**: `scripts/dataset/export_literary_poltava_dataset.py`
- **Passage Count**: 5,000 curated, high-register literary passages tagged by author and period.

---

## Fine-Tuning Strategy for Gemma 4 31B

1. **Continued Pre-Training / SFT**: Fine-tune Gemma 4 31B on `hramatka_literary_poltava_v1.jsonl` using QLoRA / LoRA causal language modeling.
2. **Pedagogical Alignment (DPO)**: Pair the fine-tuned Gemma base model with our `hramatka_uk_pedagogy_v1.jsonl` preference pairs to enforce 8/8 activity density and zero-Russianism pedagogical rules.
3. **Target Outcome**: An open-weights Gemma model that rivals Gemini 3.6 Flash in both literary euphony (*милозвучність*) and B1 lesson authoring density.

---

*Recorded and approved for the Learn Ukrainian Architecture Registry (July 2026).*
