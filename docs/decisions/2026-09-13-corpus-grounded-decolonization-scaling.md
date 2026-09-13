# Architecture Decision Record: Corpus-Grounded Decolonization Dataset Scaling (6K SFT + 3K DPO)

**Date:** 2026-09-13
**Status:** Approved (Tri-Family Multi-Agent Consensus + Operator Direction)
**Deciders:** Yellow Team (Gemini/AGY — Mining Driver), Blue Team (Claude Fable 5.1 — Authority Reviewer), Red/Alternate (Codex Sol / GPT-6.0 Astra — Adversarial Critic), Human Operator
**Parent Epic:** #6321 (Open Model Data)
**Tracking PR:** #8004
**Sub-Issues:** #8005 (Phase 3.0), #8006 (Phase 3.1–3.2), #8007 (Phase 3.3), #8008 (Phase 3.4), #8009 (Phase 3.5), #8010 (Phase 3.6), #8011 (Phase 3.7)

---

## 1. Context & Problem Statement

Pre-trained foundation models (including Google Gemma 3 and Gemma 4) systematically confuse Soviet-era lexical leveling with authentic Ukrainian standards. Following the successful completion and approval of **Phase 2 (150 Human Gold Seeds, PR #8002)**, the program expands to production scale:
- **6,000 SFT Reasoning Trajectories** (with multi-format Chain-of-Thought explaining linguistic laws and stylistic register).
- **3,000 DPO Preference Pairs** (contrasting authentic decolonized Ukrainian against Sovietized calques and hyper-purist overcorrections).
- **Held-Out Evaluation Suite** (1,000 blind test cases).

Naive automated scaling risks three fatal failure modes:
1. **Hyper-Purist Over-Correction:** Blindly replacing words without regard for domain semantics (e.g. altering mathematical/physical *об'єм піраміди* or *відношення $a:b$*), destroying valid scientific Ukrainian.
2. **Archaic Distortion:** Treating 1920s dictionaries or 1933–35 Soviet purge bulletins as an uncritical positive blueprint, reviving terms that never re-entered the modern standard (e.g. *рівнобіжник* instead of standard *паралелограм*).
3. **Synthetic Hallucination & Pretraining Contamination:** Generating synthetic error contexts or evaluating models on public web-mirrored exam questions (ZNO) that foundation models have already memorized.

---

## 2. Decision: The Six Core Pillars & 21 Invariants

The tri-family multi-agent deliberation formally established six non-negotiable architectural pillars and 21 binding invariants:

### Pillar 1: Pinned Modern Target Norm
- **Norm Anchor:** All corrections and recommendations are strictly anchored to **Modern Standard Ukrainian per Pravopys 2019 and current MESU school curricula**, cleansed of Soviet lexical leveling and Russian calques.
- **Discovery Heuristic Only:** 1920s Academy dictionaries (R2U) and 1930s Terminological Purge Bulletins serve strictly as *candidate discovery heuristics*. Every candidate must be individually checked against modern standard Ukrainian before inclusion.
- **Nomenclature Distinction:** Traditional Ukrainian trivial names (*сірчана кислота*, formed natively from *сірка*) alongside modern IUPAC names (*сульфатна кислота*) are categorized as *nomenclature modernization*, not Soviet calques.

### Pillar 2: 100% Human Source Grounding & Automated Claim-Verification
- **Zero Synthetic Sentences:** 100% of underlying sentence contexts, attested error spans, distractors, and candidate replacements originate in verified local human-authored corpus files (`sources.db`, `textbooks`, `zno_tasks`, `ua_gec_errors`, `style_guide`). No sentences or errors may be invented by an LLM.
- **Automated CoT Claim-Verifier (`v4_verify_trajectory_claims.py`):** Every explanatory statement, dictionary citation (СУМ-11, R2U), inflectional claim (VESUM), and register qualifier (ULIF) is verified against local databases. Any ungrounded or hallucinated claim triggers immediate record rejection.

### Pillar 3: Semantic Entity Boundaries & 30% `PRESERVE` Controls
- **Entity-Level Semantic Typing:** Boundary decisions key on *semantic context type*, not coarse textbook subject tags:
  - *об'єм*: 3D physical spatial volume of a geometric body or fluid capacity (*об'єм піраміди*, *об'єм розчину*) $\rightarrow$ `PRESERVE`; data volume, scope of work, or economics (*об'єм даних*, *об'єм робіт*) $\rightarrow$ `CORRECT` (*обсяг*).
  - *рахувати*: discrete counting (*рахувати дні*, *порахувати предмети*) $\rightarrow$ `PRESERVE`; mathematical calculation $\rightarrow$ normalize to *обчислити*; cognitive opinion $\rightarrow$ `CORRECT` (*вважати*).
  - *відношення*: mathematical/physical ratio $\rightarrow$ `PRESERVE`; interpersonal behavior $\rightarrow$ `CORRECT` (*ставлення / взаємини*).
- **Cleanliness Vetting:** Raw textbook chunks pass an automated filter (VESUM attestation + style-guide collision check + OCR sanity check) before admission as `PRESERVE` negative controls.
- **Colloquial Register Preservation:** Vetted conversational Ukrainian (`розм.`) is included in `PRESERVE` controls to teach the model that informal register does not equal Russian interference.

### Pillar 4: Minimal-Pair DPO Preference Architecture
- **Shortcut Elimination:** Chosen and rejected responses are constructed as length-matched minimal pairs ($\pm 10\%$) with identical CoT scaffolds, eliminating superficial style shortcuts.
- **Hyper-Purist Overcorrection Negatives:** For 900 `PRESERVE` DPO pairs, rejected responses represent unjustified substitutions (e.g. wrongly modifying *об'єм куба* $\rightarrow$ *обсяг куба*).
- **Reframed Human Correction Pairs:** Human-corrected clean sentences serve as input + chosen (`PRESERVE`), with the original human pre-correction erroneous sentence serving as the rejected completion.
- **Caricature Control:** Rejected completions are bounded to realistic error densities (1–2 errors per sentence, matching empirical UA-GEC writing).
- **On-Policy Error Harvesting:** Target Gemma checkpoints are sampled on development prompts; model-emitted verified calques are harvested as authentic hard negatives.

### Pillar 5: Pre-Extraction Partition Firewall & Leakage Defense
- **Source Custody (Phase 3.0):** Partitioning happens at source intake *before* extraction, feature derivation, or prompt authoring.
- **Contamination Defense:** Verbatim public ZNO/NMT exam tasks and classic Antonenko-Davydovych chapters are restricted to **Train-only** because they exist in Gemma's pretraining web scrape.
- **Held-Out Evaluation Allocation:** The 1,000 held-out cases are allocated as **600 PRESERVE cases + 400 CORRECT cases**. On 600 clean cases, observing $\le 1$ harmful edit yields an exact one-sided 95% binomial upper bound of $0.788\%$, statistically proving compliance with the $\le 1.0\%$ Harmful-Edit Rate gate.
- **MinHash Deduplication:** Overlapping chunks, revisions, and reprinted textbook editions are deduplicated across splits using MinHash / Jaccard similarity ($\ge 0.80$).
- **UA-GEC Test Split Protection:** The official published UA-GEC test split is strictly excluded from all training partitions to preserve independent external evaluation.

### Pillar 6: Differential Mining Guardrails & Licensing
- **20th-Century Neologism Whitelist:** Maintain an explicit whitelist of modern technical, scientific, and computing vocabulary coined after 1930 (e.g. *програмування*, *авіація*, *транзистор*). Absence from 1920s R2U is expected and must not trigger false calque flags.
- **`r2u_translate` Error Disambiguation:** Differentiate `SOURCE_UNAVAILABLE` (network timeout / HTTP failure) from `NOT_FOUND_WITHIN_VERIFIED_COVERAGE`. Never treat an empty network return as proof of absence.
- **Curriculum Stratification Caps:** Prepositional government (`G/Case`) is capped at $\le 25\%$ of training records, preventing UA-GEC's 5,024 prepositional errors from overwhelming the dataset.
- **Dual-Tier Open Release:** Public domain / CC-BY-4.0 shards released openly on Hugging Face; copyrighted textbook shards placed in a local train-only research partition with model weights publicly released.
- **200-Item Pilot Canary Gate:** Mandatory empirical verification on Gemma 3 4B before launching 6K-scale generation.

---

## 3. Seven-Issue Execution Sequence

| Issue | Phase | Description | Deliverable |
| :--- | :--- | :--- | :--- |
| **#8005** | **Phase 3.0** | Source Custody & Pre-Extraction Partition Firewall | `phase3_heldout_partition.py` (MinHash dedup, 600/400 split) |
| **#8006** | **Phase 3.1–3.2** | Human Error & Contrast Miners (Textbooks, ZNO, UA-GEC) | `v4_mine_corpus_calques.py`, `v4_mine_uagec_calques.py` |
| **#8007** | **Phase 3.3** | STEM Negative Controls & Semantic Entity Boundaries | `v4_mine_stem_controls.py` (15.5K chunks, 30% `PRESERVE`) |
| **#8008** | **Phase 3.4** | Differential Soviet Candidate Miner & Modern Whitelist Filter | `v4_differential_soviet_miner.py` (СУМ-11 vs R2U) |
| **#8009** | **Phase 3.5** | Automated CoT Claim-Verifier & Schema Reconciliation | `v4_verify_trajectory_claims.py` |
| **#8010** | **Phase 3.6** | 200-Item Pilot Canary Fine-Tune on Gemma 3 4B | `v4_pilot_canary_evaluation.py` (LoRA canary run) |
| **#8011** | **Phase 3.7** | Production Shards Assembly (6K SFT + 3K DPO) & Packaging | Production JSONL shards & held-out suite |

---

## 4. Architectural Authority & Cross-References

- **Authoritative Operational Plan:** `docs/projects/open-model-data/CORPUS_GROUNDED_DECOLONIZATION_DATASET_PLAN.md`
- **Epic Architecture Specification:** `docs/projects/open-model-data/DECOLONIZATION_EPIC_ARCHITECTURE.md`
- **Academic Methodology Paper:** `docs/projects/open-model-data/UNLP_DECOLONIZATION_REASONING_PAPER.md`
- **Preceding Approved Milestone:** Phase 2 (150 Human Gold Seeds, PR #8002, commit `c171c89c5f`)
