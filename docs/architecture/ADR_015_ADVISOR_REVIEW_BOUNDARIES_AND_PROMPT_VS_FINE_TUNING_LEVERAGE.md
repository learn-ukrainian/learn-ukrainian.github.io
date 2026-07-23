# ADR 015: Advisor Review Boundaries & Harness vs. Weight Leverage Analysis

> **Status**: APPROVED / LESSON LEARNED  
> **Date**: July 24, 2026  
> **Authors**: Lead Architecture Review, Sol (`gpt-5.6-sol`), Fable  
> **Target Epic**: #4542 (Hramatka Systems Architecture & Meta-Review Protocol)

---

## 1. Context & Meta-Analysis

When reviewing fine-tuning specifications, AI reviewers and advisors (Sol, Claude Opus) evaluated the proposal strictly as **Machine Learning System Engineers**. They audited VRAM math, QLoRA parameters, n-gram contamination hashing, and statistical confidence intervals, but did **not** challenge the fundamental assumption of whether neural fine-tuning was the correct tool for activity density.

The user correctly identified that **Activity Density ($\ge 5$ items per activity across 8 activity types) is a structural formatting task best solved by In-Context Prompt Engineering (Harness Layer)**, whereas **Fine-Tuning (Weight Adaptation) is reserved for linguistic purity, vocabulary, and decolonization.**

---

## 2. Why AI Advisors Evaluated the Plan This Way

1. **Scope-Bound Evaluation**: When asked to review an ML Fine-Tuning Plan, LLM advisors focus strictly on ML execution validity (loss curves, DPO pairs, bitsandbytes quantization, FlashAttention-2). They assume product-level harness choices are pre-decided.
2. **Training Data Prior**: Standard ML literature treats SFT/DPO as the unified solution for both format compliance and domain adaptation. In production software, however, decoupled prompt constraints are faster, cheaper ($0.00), and more reliable for structural shapes.

---

## 3. Mandatory Protocol Change for Future Advisor Reviews

Going forward, all architectural reviews and advisor prompts MUST explicitly separate:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DECOUPLED DESIGN CHECK                          │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Harness Layer (Prompt Engineering):                                  │
│    • Can this structural or formatting issue be solved via system      │
│      prompts, exemplars, or JSON schema constraints? (Cost: $0.00)     │
├────────────────────────────────────────────────────────────────────────┤
│ 2. Weight Layer (Neural Fine-Tuning):                                  │
│    • Does this issue stem from missing base-model knowledge,           │
│      Russianisms in training weights, or un-euphonic grammar rules?    │
│      (Requires SFT / DPO training)                                     │
└────────────────────────────────────────────────────────────────────────┘
```

---

*Recorded for the Learn Ukrainian Architecture Registry.*
