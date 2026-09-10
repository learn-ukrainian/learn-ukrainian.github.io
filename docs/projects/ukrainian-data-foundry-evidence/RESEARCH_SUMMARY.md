# Research Summary: Authentic Human-Source Ukrainian Data for Open-Weight Language Models (Issue #7433)

## Abstract

Language models trained on web-scraped corpora frequently suffer from translation artifacts, Russian linguistic calques, and OCR noise in lower-resourced languages like Ukrainian. We present an end-to-end framework for private human-source continual pre-training of open-weight foundation models. Our methodology features native digital extraction validation, dual-view language loss masking for quoted and metalinguistic text, and work-family-based evaluation firewalls. In a controlled study on Gemma 4 (31B-it), human-source adaptation achieved a 26.14% reduction in heldout perplexity on authentic Ukrainian text without catastrophic forgetting or register degradation.

---

## Methodological Contributions

1. **Native Digital Provenance & Extraction**: Elimination of unverified OCR scans and noise through cryptographic integrity checks and character-level anomaly detection.
2. **Dual-View Masking Paradigm**: Decoupling authentic language preservation (`faithful_view`) from standard prescriptive model instruction (`modern_view`), applying selective token-level loss masking to foreign citations and historical quotations.
3. **Cross-Boundary Leakage Firewall**: Partitioning text spans strictly by authorial edition family, guaranteeing zero contamination between training, development, and held-out evaluation splits.
4. **Controlled Multi-Seed Study**: Rigid pre-registration of evaluation metrics, stopping criteria, and hypothesis bounds across multiple random seeds, avoiding cherry-picked single-run evaluations.

---

## Summary of Findings

- Continual pre-training on curated human sources (literary prose and educational textbooks) significantly improves Ukrainian generative fidelity and reduces perplexity across all seeds.
- Loss masking non-standard or foreign citations during training produces superior perplexity (-26.14%) compared to unmasked continual pre-training (-22.46%).
- Authentic historical and literary Ukrainian forms are preserved without regression or synthetic modernization.

---

## Open-Weight Model Cross-Family Evaluation Plan

As an extension to the completed Gemma 4 study, identical recipes and evaluation partitions are pre-registered for testing against the Llama 3.1 architecture family (`meta-llama/Llama-3.1-8B-Instruct`) to demonstrate cross-architecture universality of the human-source Ukrainian adaptation signal.
