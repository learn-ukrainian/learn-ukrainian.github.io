# Ukrainian Linguistic Decolonization & Reasoning (ULDR) & Open Model Data

> **Parent Epics:** [#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321) (ULDR Open Model Data) & [#7423](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/7423) (Human-Source Dataset Delivery)
> **Stream Registry:** `open-model-data` (in `scripts/config/issue_streams.yaml`)
> **Public Hub Dataset:** [`krisztiankoos/uldr-v0.1-pilot`](https://huggingface.co/datasets/krisztiankoos/uldr-v0.1-pilot) *(Exploratory Pilot Canary v0.1; v1.0 Production Release in Phase 5.5)*
> **Target Alignment Weights:** Google Gemma 3 (4B-it, 12B-it, 27B-it) & Gemma 4 Architectures

---

## 1. Executive Mission & Strategic Positioning

Foundation language models pre-trained on generic web crawls know *how to speak Ukrainian*, but they frequently fail to produce **authentic, standard, and decolonized Ukrainian**. Because web dumps are heavily contaminated by machine translations, Soviet-era prescriptive dictionaries (e.g. СУМ-11), and conversational Russianisms, raw foundation models replicate lexical calques, unnatural syntactic structures, and Russian case government.

The **ULDR (Ukrainian Linguistic Decolonization & Reasoning)** project establishes a precision alignment dataset and evaluation infrastructure to engrave authentic linguistic discipline directly into model weights via multi-step Chain-of-Thought (SFT) and contrastive preference optimization (DPO).

### What This Project IS For
1. **Grammar, Syntactic Rigor & Morphological Precision:** Teaching models authentic Ukrainian grammatical rules, inflectional paradigms (grounded in `vesum.db`), verbal valencies (*дякувати комусь*, *опановувати щось*), and prepositional government (*у справах*, *щовівторка*, *за правилами*).
2. **Systematic Decolonization:** Eliminating Soviet lexical leveling and Russian calques (*пилосос* $\rightarrow$ *пилосмок*, *приймати участь* $\rightarrow$ *брати участь*, *переключити* $\rightarrow$ *перемкнути*).
3. **Structured Linguistic Reasoning:** Teaching the model to diagnose language using authentic linguistic criteria (morphemic root analysis, etymological history, academic dictionary attestation, and stylistic register spectrums).
4. **Anti-Hyper-Purist Preservation (~30% Negative Controls):** Ensuring models do NOT over-correct valid Ukrainian standard vocabulary, international scientific terminology, or established literary forms.
5. **Protection of Dialects & Historical Stages:** Ensuring models respect living regional dialects (Hutsul, Boyko, Lemko, Polissian) and historical stages (Old East Slavic, Middle Ukrainian) without flattening them into synthetic modern standard forms.

### What This Project IS NOT For
* **NOT for Bulk Conversational Fluency:** Pre-training foundation models for general conversational fluency and encyclopedic world knowledge requires trillions of tokens and is already solved by foundation model builders (Google, Meta, Mistral, and open-source pre-training consortia). We do not scrape the web or replicate general pre-training.
* **NOT an Exhaustive Dictionary of All Words:** Our corpus is a precision pedagogical instrument designed to instill grammatical discipline, case government, and decolonized reasoning—not to cover every rare noun or technical jargon term in existence.
* **NOT Unvetted AI Synthetic Generation:** Zero raw LLM generation is admitted without strict rule-based verification. All admitted replacement candidates and negative controls are validated against MESU-approved school textbooks (Gr 1–11), academic style guides (Antonenko-Davydovych, Ponomariv, Karavanskyi), and morphological engines (VESUM).

---

## 2. Architecture & Operational Pipeline

```mermaid
flowchart LR
    subgraph Sources ["1. Verified Human Holdings"]
        TB["MESU Textbooks (Gr 1-11)"]
        SG["Style Guides (Antonenko-Davydovych)"]
        ZNO["Official ZNO / NMT Exams"]
        GEC["UA-GEC Human Error Corpus"]
    end

    subgraph Mining ["2. Rule-Grounded Miners"]
        M1["v4_mine_corpus_calques.py"]
        M2["v4_mine_stem_controls.py"]
        M3["v4_differential_soviet_miner.py"]
    end

    subgraph Verification ["3. Verification Gates"]
        V1["VESUM Inflection & Paradigm Check"]
        V2["v4_verify_trajectory_claims.py"]
        V3["Partition Firewall & MinHash Dedup"]
    end

    subgraph Products ["4. Delivered Products"]
        SFT["6,000 SFT Reasoning Trajectories (30% PRESERVE)"]
        DPO["3,000 DPO Preference Pairs (Minimal-Pair Scaffold)"]
        EVAL["1,000-Case Held-Out Test Suite"]
        HF["Hugging Face Open Weights & Shards"]
    end

    Sources --> Mining --> Verification --> Products
```

---

## 3. Project Roadmap & Active Phases

### Completed Phases (1–4)
* **Phase 1 (PR #7918):** Frozen JSON schemas (`v1_decolonization_trajectory.schema.json`, `v1_decolonization_dpo_pair.schema.json`) and canonical contract seeds.
* **Phase 2 (PR #7923):** Automated miner engine and dynamic textbook attestation.
* **Phase 3 (PR #7925, #8004, #8025):**
  - Partition firewall & MinHash near-duplicate isolation.
  - STEM negative controls (1,800 SFT + 900 DPO `PRESERVE`).
  - Automated CoT claim verification against VESUM and dictionaries.
  - Pilot assembly: 6,000 SFT + 3,000 DPO packaged and released on Hugging Face as exploratory pilot canary v0.1 at [`krisztiankoos/uldr-v0.1-pilot`](https://huggingface.co/datasets/krisztiankoos/uldr-v0.1-pilot) (Production release v1.0 scheduled for Phase 5.5).
* **Phase 4 (PR #8038):** Production training recipe and Hugging Face Job runner (`train_gemma3_production.py`) executing QLoRA SFT + DPO on Nvidia A10G.

### Active Next Phases (Phase 5 Sub-Issues under Epic #6321)
* [**#8050 — Phase 5.1**](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8050): **Automated Evaluation Suite for Grammatical Correctness & Academic Non-Inferiority** (`Eval-UA-tion 1.0` via `lm-evaluation-harness`).
* [**#8051 — Phase 5.2**](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8051): **Dialect & Historical Protection Test Suite** (Preventing hyper-purist over-standardization of regional dialects and historical stages).
* [**#8052 — Phase 5.3**](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8052): **Curate 150 High-Assurance Corpus-Grounded Gold Seeds** (Deeply researched trajectories from Antonenko-Davydovych *«Як ми говоримо»* and *mova.ua*).
* [**#8053 — Phase 5.4**](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8053): **Targeted Grammatical & Syntactic Alignment Expansion** (Precision correctness over bulk fluency; ~30% `PRESERVE` controls).
* [**#8054 — Phase 5.5**](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8054): **Production Model Alignment Run & Open-Weight Release on Hugging Face** (Full training on larger base weights with formal Model Card).

---

## 4. Documentation Index & Taxonomy

### Authoritative Plans & Architecture (Active)
| Document | Purpose |
| :--- | :--- |
| [`ROADMAP_250K_SOVEREIGN_UKRAINIAN.md`](ROADMAP_250K_SOVEREIGN_UKRAINIAN.md) | Authoritative, source-honest roadmap for Epic #6321 (rewritten 2026-09-20). |
| [`GRAMMAR_DATASET_SPEC_8342.md`](GRAMMAR_DATASET_SPEC_8342.md) | Grammar dataset redo specification, mixture ratios, and #8339/#8338 acceptance gates (#8342). |
| [`CORPUS_GROUNDED_DECOLONIZATION_DATASET_PLAN.md`](CORPUS_GROUNDED_DECOLONIZATION_DATASET_PLAN.md) | Operational plan for the 6K SFT + 3K DPO production dataset and miner pipeline. |
| [`DECOLONIZATION_EPIC_ARCHITECTURE.md`](DECOLONIZATION_EPIC_ARCHITECTURE.md) | Tri-family architectural agreement (Gemini, Claude, Codex) on production design. |
| [`LINGUISTIC_DECOLONIZATION_REASONING_DATASET_PLAN.md`](LINGUISTIC_DECOLONIZATION_REASONING_DATASET_PLAN.md) | Complete specification of linguistic diagnostic methodology and Soviet lexicographical analysis. |
| [`SOURCE_RECORD_CONTRACT.md`](SOURCE_RECORD_CONTRACT.md) | Human-source record schema and provenance validation rules for raw inputs. |
| [`decolonization-training-guide.md`](decolonization-training-guide.md) | Downstream recipe for fine-tuning Gemma 3 and Gemma 4 architectures using ULDR shards. |

### Component Deep Dives & Phase Summaries
| Document | Scope |
| :--- | :--- |
| [`CORPUS_PROFILER.md`](CORPUS_PROFILER.md) | Corpus profiling tool assessing lexical diversity, genre balance, and vocabulary distribution across training sources. |
| [`PHASE_3_3_STEM_NEGATIVE_CONTROLS.md`](PHASE_3_3_STEM_NEGATIVE_CONTROLS.md) | Extraction methodology for 15,563 STEM chunks and polysemy boundaries (*об'єм* vs. *обсяг*). |
| [`PHASE_3_5_COT_CLAIM_VERIFIER.md`](PHASE_3_5_COT_CLAIM_VERIFIER.md) | Automated fact-checking engine validating dictionary and morphological claims in reasoning traces. |
| [`PHASE_3_6_PILOT_CANARY.md`](PHASE_3_6_PILOT_CANARY.md) | 200-item canary fine-tuning results on Gemma 3 4B. |
| [`PHASE_3_7_PRODUCTION_SHARDS.md`](PHASE_3_7_PRODUCTION_SHARDS.md) | Packaging, hashing, and MinHash isolation audit for the 6K SFT + 3K DPO production release. |
| [`SOVIET_DIFFERENTIAL_MINER.md`](SOVIET_DIFFERENTIAL_MINER.md) | Algorithmic miner identifying Soviet ideological elevation in СУМ-11 against pre-Soviet dictionaries. |
| [`UNLP_DECOLONIZATION_REASONING_PAPER.md`](UNLP_DECOLONIZATION_REASONING_PAPER.md) | Academic research paper draft for UNLP 2026 outlining the Triad of False Authority. |

### Historical & Superseded Predecessor Records
> **Note:** The following documents represent older exploratory mechanisms (Cycle007 or early V4 100-slot factory) that have been formally superseded by the active ULDR architecture under Epic #6321 / #7423. They are retained for provenance and historical audit only:
* [`cyrillic-slavic-dataset-delivery-plan.md`](cyrillic-slavic-dataset-delivery-plan.md) — Predecessor V4 100-slot mechanism (original-row generation stopped; superseded by ULDR).
* [`cycle007-evidence-compile-throughput.md`](cycle007-evidence-compile-throughput.md) — Predecessor Cycle007 evidence-compiler notes (superseded).
* [`cycle007-labeling-runtime.md`](cycle007-labeling-runtime.md) — Predecessor Cycle007 labeling runtime guarantees (superseded).
* [`cycle007-storage-custody.md`](cycle007-storage-custody.md) — Predecessor Cycle007 storage compaction and custody history (superseded).
* [`v4-real-slot-mechanism-runbook.md`](v4-real-slot-mechanism-runbook.md) — Predecessor V4 slot runner runbook (superseded).
