# Master Engineering Roadmap: Learn Ukrainian Architecture & Alignment Engine

> **Document Status**: MASTER ARCHITECTURAL ROADMAP  
> **Author & Design**: Sol (`gpt-5.6-sol`), Lead Architect  
> **Date**: July 24, 2026  
> **Target Epics**: #4542 (Model Qualification), #4708 (Hramatka Engine & Datasets)  
> **Public Path**: `docs/plans/MASTER_ENGINEERING_ROADMAP.md`  
> **Private Path**: `/Users/krisztiankoos/projects/learn-ukrainian-infra-private/docs/plans/MASTER_ENGINEERING_ROADMAP.md`

---

## 1. Executive Strategy & Non-Negotiable Core

Our project's mission is to build the world's most rigorous, decolonized Ukrainian language learning engine. To avoid novice traps, waste of compute, or low-quality data releases, our work is organized across **four sequential engineering phases**, bounded by hard quantitative gates.

---

## Phase 1: Rights-Cleared Open Dataset Package (`hramatka_literary_poltava_v1`)

### **Deliverables**:
- **Three Distinct Dataset Configurations**:
  1. `corpus`: Faithful historical & literary passages (never silently normalized).
  2. `instruction`: Grounded instruction/response triples for SFT.
  3. `preference`: Independently adjudicated `chosen`/`rejected` pairs for DPO.
- **Deterministic Exporter & Manifest**:
  - Exporter with fixed seed, schema validation, immutable record IDs, SHA-256 build manifest, and reproducible build CLI command (`scripts/dataset/export_literary_poltava_dataset.py`).
- **Per-Record Provenance Metadata**:
  - `source_id`, `source_url`, `author`, `work`, `work_id`, `year`, `language_period` (`old_east_slavic`, `middle_ukrainian`, `modern`), `genre`, and `license_basis`.
- **Work/Author-Level Split Isolation**:
  - Split training vs holdout sets by **work and author family**, NEVER by arbitrary chunk, ensuring zero data leakage.

### **Phase 1 Exit Gates**:
- 100% of released records have an explicit rights/redistribution basis.
- Zero exact cross-split duplicates; zero unadjudicated near-duplicates.
- Double-review of 400+ stratified records with **Wilson lower 95% bound $\ge 0.98$** for text fidelity.
- Historical and regional language is correctly tagged by period, not blanket-stamped "Poltava".
- Public package rebuilds byte-identically from the frozen manifest.

---

## Phase 2: Open Evaluation Benchmark Suite (`zno-textbook-drill-v1`)

### **Deliverables**:
- **Formal Construct Map**:
  - Evaluating morphology, syntax, case government, vocabulary depth, reading comprehension, answer-key correctness, CEFR level appropriateness, source grounding, naturalness, and decolonization.
- **Anchor Test Suite**:
  - 120 public development anchors + 300 hidden qualification anchors, stratified by CEFR level (A1–C2), skill, topic, and language period.
- **Open Evaluation CLI Runner (`scripts/eval/run_benchmark.py`)**:
  - Deterministic evaluation runner, frozen schemas, baseline outputs, scoring rubric, and error taxonomy.
- **Native Teacher Gold Labels**:
  - Human native Ukrainian teacher/linguist gold labels as ultimate authority (LLM judges used only for first-pass triage).

### **Phase 2 Exit Gates**:
- 100% benchmark items rights-cleared and source-verifiable.
- 100% gold-answer deterministic checks pass.
- Double-annotated with **Krippendorff’s $\alpha \ge 0.80$** inter-rater reliability.
- Hidden test labels strictly isolated from model development loops.
- Baseline results reproduce within declared tolerance across 2 clean runs.

---

## Phase 3: Production Authoring Engine Architecture

### **Core Pipeline**:
```
[Versioned Request] ──> [Evidence Retrieval] ──> [Model Adapter]
                              │
                              ▼
[Semantic Release] <── [Full Re-Validation] <── [Bounded Repair (max 1)] <── [Validator Check]
```

### **Required Engine Components**:
- **Model Adapter & Route Registry**: Model-agnostic adapter interface (`ask-agy`, `ask-claude`, `ask-codex`, `ask-opencode`).
- **Fail-Closed Validation Suite**:
  - Validates JSON schema, activity density ($\ge 7$ types, $\ge 5$ items), answer key correctness, citations, immersion, Russianism candidates, and unsupported grammar claims.
  - Linters reject or escalate; they NEVER silently "clean" or rewrite language.
- **Model Routing Policy**:
  - **Gemini 3.6 Flash**: Primary production authoring seat (**10/10 PASS**, 12s latency).
  - **Gemini 3.1 Pro**: Secondary deep seat (**9.5/10 PASS**, 45s latency).
  - **Gemma 4 31B**: Shadow mode only until Phase 4 qualification passes.

### **Phase 3 Exit Gates (Canary 100-Request Production Suite)**:
- First-pass schema validity $\ge 99.0\%$; post-repair validity $\ge 99.5\%$.
- Answer-key correctness $\ge 99.5\%$.
- Zero verified critical linguistic or decolonization failures.
- Repair rate $\le 10\%$; no request receives more than 1 repair pass.
- Gemini Flash p95 latency $\le 30$ seconds.

---

## Phase 4: Model Qualification Gate & Release Protocol

### **Evaluation Protocol**:
- Freeze candidate model ID/checkpoint, provider route, prompt harness, schema, and retrieval snapshot before evaluation.
- Test across 300 unseen anchors with 3 generations per anchor.
- Conduct blinded native-speaker raters, randomized model identities, and explicit critical-error vetoes.
- Compute aggregate scores using a **10,000-resample hierarchical bootstrap** over anchors and raters.

### **Phase 4 Release Gates**:
- **Lower 95% Confidence Bound of Aggregate Score $\text{CI}_{\text{lower}} \ge 9.0$**.
- Every quality dimension mean $\ge 8.5$ (no averaging away a weak linguistic or pedagogical dimension).
- Zero verified Russianisms, fabricated grammar rules, invalid gold keys, or colonial-framing errors.
- Candidate–Champion Non-Inferiority: Lower 95% bound of paired difference $\ge -0.2$.
- Requalification mandatory after any material model, prompt, schema, retrieval, or validator change.

---

## Five Expensive Mistakes to Avoid

1. **Calling a Random Dump "Curated"**: `ORDER BY RANDOM()` plus a universal dialect label creates mislabeled training data.
2. **Publishing Before Rights Resolution**: Unabridged modern literature and textbooks must be verified for public domain or CC-BY redistribution basis.
3. **Splitting by Chunk Instead of Work**: Splitting by chunk leaks adjacent paragraphs and editions into evaluation. Split and deduplicate at work/author level.
4. **Treating One-Anchor Scores as Production Qualification**: One anchor cannot establish statistical confidence. Use 300 anchors with hierarchical bootstrapping.
5. **Using Fine-Tuning or Linters as a Magic Wand**: Harness/schema solve structure; retrieval supplies evidence; weights affect linguistic behavior; native experts adjudicate semantics.

---

*Master Engineering Roadmap designed by Sol (`gpt-5.6-sol`), Lead Architect (July 24, 2026).*
