# Authentic Ukrainian Linguistic Decolonization & Reasoning: Dataset Construction Specification and Implementation Plan

## 1. Executive Summary & Objective

Modern open-weight foundation models trained on web crawls exhibit severe contamination from Russian-imperial framing, Soviet-era prescriptive lexicography (e.g., СУМ-11), machine-translated syntax, and Russian lexical calques. Standard alignment methods (simple synonym replacement or superficial RLHF) fail because they treat language as a binary lookup table rather than a nuanced system of morphological, historical, and stylistic registers.

This specification establishes an end-to-end framework and data construction pipeline to create the **Ukrainian Linguistic Decolonization & Reasoning Dataset (ULDR)**. The objective is to **engrave the systematic decolonization diagnostic method directly into model weights** via:
1. **Instruction Supervised Fine-Tuning (SFT)** on multi-step linguistic diagnostic trajectories (morphemic root cause, lexicographical history, multi-source attestation, and register spectrum).
2. **Preference Optimization (DPO/RLVR)** with deterministic rule-based verification (VESUM inflectional gating and textbook grounding).
3. **Targeted Continual Pre-Training (CPT)** with dual-view loss masking over verified human holdings.

### 1.1 Strategic Positioning: Normative Alignment vs. Bulk Pre-Training

A critical strategic principle guides this effort:
- **Bulk Pre-training is Solved by Others**: Pre-training foundation models from scratch requires trillions of tokens (Common Crawl, Wikipedia, huge book dumps). Other open-source teams and labs are already building general Ukrainian-capable foundation models.
- **The Bulk Data Flaw**: General web dumps are inherently contaminated. They scrape forums, machine-translated e-commerce sites, and Soviet-era scanned literature. Consequently, existing models know *how to speak Ukrainian*, but they do *not* know how to speak **authentic, decolonized, standard Ukrainian**. They confidently replicate Russianisms, calques, and syntactic distortions.
- **The LIMA Principle (Less Is More for Alignment)**: As demonstrated by modern alignment research, a model does not need billions of tokens to acquire normative reasoning and stylistic discipline. A dense corpus of **1,000 to 10,000 rigorous, step-by-step linguistic reasoning trajectories** is sufficient to fundamentally realign an existing 30B–70B model's generative priors.
- **The Deliverable**: ULDR is not a 10-terabyte web dump; it is the **high-leverage "Normative & Methodological Brain"**—an alignment adapter (SFT + DPO LoRA / full-weight tune) that transforms any base Ukrainian-capable model into an authentic linguistic authority.

---

## 2. Root-Cause Analysis: The Soviet Lexicographical Trap

```
                     ┌─────────────────────────────────────────────────────────┐
                     │          Soviet Lexicographical Policy (1930s-1970s)    │
                     │  - 1933 Terminological Bulletins (suppressed UA roots)  │
                     │  - СУМ-11 (1970s) codified Russian loans as standard     │
                     └────────────────────────────┬────────────────────────────┘
                                                  │
                                                  ▼
                     ┌─────────────────────────────────────────────────────────┐
                     │           Modern Foundation LLMs (Web Crawl)            │
                     │  - High frequency of Soviet calques (e.g. пилосос)      │
                     │  - Inability to distinguish living standard from purism │
                     │  - Hallucinated translations & false WordNet synsets    │
                     └─────────────────────────────────────────────────────────┘
```

### The Problem in Practice: The Case of *Пилосос*
1. **Morphemic Origin**:
   - In Russian, *пылесос* is formed from *пыль* (dust) + *сосать* (to suck).
   - In Ukrainian, dust is not *смокчуть* (sucked like liquid or candy); it is *втягують* (drawn in) or *всмоктують*.
2. **Soviet Imposition**:
   - Soviet terminological commissions in the 1930s and later СУМ-11 (1970s) systematically favored *пилосос* to synchronize Ukrainian technical vocabulary with Russian, actively suppressing authentic Ukrainian alternatives.
3. **The Living Reality**:
   - In independent Ukraine, authentic terminology was restored in living language:
     - **пилосмок** (*пил + смоктати*): The dominant contemporary standard taught in MESU-approved school textbooks (e.g. Gr 9 World History, Пометун 2026, p. 166: «Перша модель пилосмока»; recommended by Prof. Oleksandr Ponomariv).
     - **порохотяг** (*порох + тягти*): Classical historical and Western Ukrainian standard (documented in modern academic dictionaries СУМ-20 and ВТС).
     - **пилотяг** (*пил + тягти*): Technical compound standard.
     - **порохосмок** (*порох + смоктати*): Purist neologism coined by diaspora lexicographer Pavlo Shtepa (1968), absent from modern morphological standards (VESUM has 0 forms).
4. **The LLM Dilemma**:
   - Naive LLMs either defend *пилосос* as the only standard, or jump to *порохосмок* (the least standard, unvetted neologism), or map *вакуум* (English "vacuum") as a false synonym.
   - **The Model Must Learn the Thinking Process**: Recognize the calque, explain the historical context, cite primary educational sources, verify morphological validity in VESUM, and rank alternatives across stylistic registers.

---

## 3. The 5-Stage Data Construction Pipeline

```mermaid
flowchart TD
    A["Headword (Calque / Russianism / Problematic Term)"] --> B["Stage 1: Multi-Source Evidence Mining"]
    B --> B1["MESU School Textbooks (Gr 1-11) in sources.db"]
    B --> B2["Decolonization Style Guides (Антоненко-Давидович, Пономарів, Караванський)"]
    B --> B3["Academic Dictionaries (СУМ-20, ВТС, Горох)"]
    B --> B4["UA-GEC & LanguageTool Human Correction Corpus"]
    B1 & B2 & B3 & B4 --> C["Stage 2: Deduplicated Candidate Union"]
    C --> D["Stage 3: VESUM Morphological & Attestation Gate (vesum.db)"]
    D -->|Passed VESUM (Paradigms >= 1)| E["Register Spectrum Ranking"]
    D -->|Absent from VESUM (0 forms)| F["Purist / Historical Neologism Annotation"]
    E & F --> G["Stage 4: Reasoning Trajectory Generation (SFT)"]
    G --> H["Stage 5: Contrastive Preference Construction (DPO/RLVR)"]
```

### Stage 1: Multi-Source Evidence Mining
Querying internal corpora in `data/sources.db`:
- **Educational Textbooks (`textbooks`)**: Mining living vocabulary taught in Grades 1–11 approved by the Ministry of Education and Science of Ukraine (2023–2026).
- **Decolonization Style Guides (`style_guide`)**:
  - Borys Antonenko-Davydovych, *«Як ми говоримо»*
  - Oleksandr Ponomariv, *«Культура слова»*
  - Sviatoslav Karavanskyi, *«Практичний словник синонімів української мови»* & *«Пошук українського слова»*
  - Taras Bereza, *«Слова, що нас збагачують»*
- **Academic Dictionaries**: 21st-century academic restoration corpora (СУМ-20, ВТС).
- **UA-GEC Corpus (`ua_gec_errors`)**: Professional human linguist annotations of Russianisms and calques.

### Stage 2: Deduplicated Candidate Union
Aggregating all candidate alternatives into a canonical replacement pool, resolving multi-source overlap without dropping valid alternatives.

### Stage 3: VESUM Morphological & Attestation Gate (`vesum.db`)
Every candidate alternative is validated against `data/vesum.db` (409K lemmas, 6.7M forms):
- **Admitted Standard Candidates**: Candidates with full inflectional paradigms in VESUM (e.g. *пилосмок* [16 forms], *порохотяг* [16 forms], *пилотяг* [16 forms]).
- **Purist / Dialectal Outliers**: Candidates with 0 forms in VESUM (e.g. *порохосмок*) are classified as historical/diaspora neologisms. They are never presented as the primary classroom recommendation.

### Stage 4: Register Spectrum Ranking
Ranking valid alternatives into explicit pedagogical registers:
1. **Primary Living Standard**: Dominant modern classroom/media term (*пилосмок*).
2. **Classical / Regional Standard**: Historical, literary, and Western Ukrainian term (*порохотяг*).
3. **Specialized / Technical Compound**: Technical domain term (*пилотяг*).
4. **Purist / Neologistic Reference**: Historical neologisms (*порохосмок*).

### Stage 5: Reasoning Trajectory & Preference Generation
Synthesizing structured multi-step reasoning traces for SFT and paired contrastive examples for DPO/RLVR.

---

## 4. Dataset Contracts & Schema Specifications

### A. SFT Reasoning Trajectory Schema (`v1`)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "UkrainianLinguisticReasoningTrajectoryV1",
  "type": "object",
  "required": ["trajectory_id", "query", "target_term", "morphemic_breakdown", "lexicographical_context", "vesum_attestation", "register_spectrum", "reasoning_steps", "final_response"],
  "properties": {
    "trajectory_id": { "type": "string", "pattern": "^traj\\.decolonize\\.[a-f0-9]{16}$" },
    "query": { "type": "string" },
    "target_term": { "type": "string" },
    "is_calque_or_russianism": { "type": "boolean" },
    "morphemic_breakdown": {
      "type": "object",
      "required": ["source_formation", "ukrainian_equivalent_mechanism"],
      "properties": {
        "source_formation": { "type": "string" },
        "ukrainian_equivalent_mechanism": { "type": "string" }
      }
    },
    "lexicographical_context": {
      "type": "object",
      "required": ["historical_suppression_note", "restoration_era"],
      "properties": {
        "historical_suppression_note": { "type": "string" },
        "restoration_era": { "type": "string" }
      }
    },
    "vesum_attestation": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["lemma", "vesum_forms_count", "is_standard_attested"],
        "properties": {
          "lemma": { "type": "string" },
          "vesum_forms_count": { "type": "integer" },
          "is_standard_attested": { "type": "boolean" }
        }
      }
    },
    "register_spectrum": {
      "type": "object",
      "required": ["primary_living_standard", "alternatives"],
      "properties": {
        "primary_living_standard": { "type": "string" },
        "alternatives": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["lemma", "register_tier", "evidence_source"],
            "properties": {
              "lemma": { "type": "string" },
              "register_tier": { "type": "string", "enum": ["living_standard", "classical_regional", "technical_compound", "purist_neologism"] },
              "evidence_source": { "type": "string" }
            }
          }
        }
      }
    },
    "reasoning_steps": {
      "type": "array",
      "items": { "type": "string" }
    },
    "final_response": { "type": "string" }
  }
}
```

### B. DPO Preference Pair Schema (`v1`)
```json
{
  "prompt": "Як правильно вживати: пилосос чи пилосмок?",
  "chosen": "Слово «пилосос» є радянською калькою з російської мови («пылесос»: пыль + сосать)... [Повний морфемний аналіз, цитати з підручників 2023–2026 рр., розрізнення «пилосмок» (основний стандарт), «порохотяг» (класичний стандарт), «пилотяг» (технічний) та роз'яснення щодо пуризму «порохосмок»]",
  "rejected": "Слово «пилосос» є нормативним літературним словом, зафіксованим у СУМ-11. Також деякі автори пропонують слово «порохосмок».",
  "metadata": {
    "rejected_flaw": "soviet_lexicography_acceptance_and_unvetted_purism",
    "target_term": "пилосос",
    "verified_in_vesum": true
  }
}
```

---

## 5. Fleet Allocation & Implementation Matrix

Following the **Operator Contract** (Item 5: Route by model × harness fit; Item 4: Independent cross-family review gate):

| Fleet Role | Agent / Model | Primary Responsibilities | Deliverables |
| :--- | :--- | :--- | :--- |
| **Linguistic Research & Content Builder** | **Gemini (Yellow Team / AGY)** | - Multi-source mining across `sources.db` (textbooks, style guides).<br>- Linguistic diagnosis: morphemic breakdown & historical lexicography notes.<br>- Authoring gold reasoning trajectories & seed diagnostic templates. | `data/projects/open_model_data/decolonization/seeds/`<br>`docs/projects/ukrainian-data-foundry-evidence/` |
| **Deterministic Pipeline & Architecture** | **Codex (Green Team / OpenAI)** | - JSON schema contracts (`v1.schema.json`).<br>- Automated trajectory generator script (`generate_decolonization_trajectories.py`).<br>- Strict VESUM verification gates (`vesum.db` integration).<br>- Pre-commit hooks, hash accounting, and PR management. | `scripts/projects/open_model_data/`<br>`data/projects/open_model_data/contracts/`<br>`tests/projects/open_model_data/` |
| **Adversarial Review & Evaluation Gate** | **Claude (Blue Team / Anthropic)** | - Independent cross-family review of all PRs.<br>- Adversarial hallucination auditing (detecting ghost sources or invented neologisms).<br>- Firewall verification (zero contamination between train and held-out splits). | Audit reviews on PRs<br>`tests/projects/open_model_data/test_decolonization_eval.py` |
| **Open-Weight Study & Training** | **Grok-build / Open-Weight Harness** | - Tokenization and loss-masking validation.<br>- SFT / DPO training runs on Gemma 4 (31B-it).<br>- Perplexity and benchmark evaluation on held-out authentic splits. | Training receipts & model checkpoints |

---

## 6. Phased Implementation Roadmap

```
  Phase 1: Seed Curation & Contracts ──► Phase 2: Automated Generator Pipeline ──► Phase 3: Export & Audit ──► Phase 4: SFT / DPO Training
  (Gemini + Codex)                       (Codex + Gemini)                           (Claude Review)              (Open-Weight Compute)
```

### Phase 1: Contract Freezing & Seed Anchors (Milestone 1 — PR #7918)
- **Contracts**: Frozen `v1` JSON schemas for trajectories (`v1_decolonization_trajectory.schema.json`) and DPO pairs (`v1_decolonization_dpo_pair.schema.json`) under `data/projects/open_model_data/contracts/`.
- **Seed Anchors**: Frozen 3 canonical gold reference seeds (*пилосос*, *переключити*, *кримчанин*) under `data/projects/open_model_data/decolonization/seeds/` with 100% VESUM verification, textbook citations, and register spectrum.
- **Review**: Independent cross-family review approved by Claude Sonnet 5.

### Phase 2: Automated Generator Pipeline & Attestation Engine (Milestone 2 — PR #7923)
- Build `scripts/projects/open_model_data/v4_decolonization_reasoning.py`:
  1. Multi-source mining across `sources.db` (MESU textbooks Gr 1–11, style guides, and dictionaries).
  2. Query `vesum.db` to verify morphological paradigms for all tokens in multi-word phrases.
  3. Synthesize structured reasoning steps and contrastive DPO pairs into JSONL streams with dynamic attestation metrics.
- Add linguistic evaluation test fixtures ensuring multi-word phrases and register nuances are verified.

### Phase 3: Dataset Packaging, Firewall & Manifests (Milestone 3 — PR #7925)
- Generate 1,200 normative SFT reasoning trajectories and 1,200 contrastive DPO preference pairs across 4 shards (3 train + 1 held-out).
- Enforce strict deterministic partition firewall (`get_partition_for_term`) with 0 overlap between train (967 records) and held-out (233 records).
- Enforce repository hard gates:
  - File size ceiling: `< 2000 KB` per shard.
  - Zero private host paths (`/home/`, `/tmp/`, `/workspace/`, `/root/`).
  - Strict cryptographic SHA-256 manifests (`trajectories_manifest.json`, `dpo_pairs_manifest.json`).

### Phase 4: Consumer Recipes, Formatters & Evaluation Harness (Milestone 4 — PR #7927)
- Transform canonical shards into ShareGPT (with `<thought>` tags and Gemma `messages` turn structure) and Hugging Face TRL DPO formats with embedded system prompts.
- Implement automated evaluation harness (`v4_evaluate_decolonization.py`) benchmarking against held-out partition across 5 core metrics with strict denominator reconciliation and contradiction detection.
- Provide downstream training recipes for Gemma 3 (`google/gemma-3-27b-it`) and Gemma 4 (`google/gemma-4-31b-it`) in `docs/projects/open-model-data/decolonization-training-guide.md`.
- Boundary Invariant: Model training compute remains a downstream community activity; this repository delivers verified datasets, cryptographic manifests, evaluation canaries, and consumer recipes.
