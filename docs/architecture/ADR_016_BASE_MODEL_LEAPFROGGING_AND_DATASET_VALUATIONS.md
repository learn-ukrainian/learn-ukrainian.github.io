# ADR 016: Base Model Leapfrogging & Data/Harness Value Preservation

> **Status**: APPROVED / ARCHITECTURAL STRATEGY  
> **Date**: July 24, 2026  
> **Authors**: Lead Architecture Review, UNLP Case Study Task Force  
> **Target Epic**: #4542 (Hramatka Long-Term Strategy & Model Agnosticism)

---

## 1. Case Study: UNLP Lapa (Gemma 3) vs. Gemma 4

The UNLP community invested heavy compute and human annotation resources into fine-tuning **Gemma 3** into **Lapa / Lapa-Ukrainian** to improve Ukrainian tokenization and grammar. Shortly after release, Google launched **Gemma 4 31B**, whose base capabilities and native multilingual tokenization immediately outperformed the custom fine-tuned Lapa model.

### **The "Base Model Leapfrogging" Reality**:
1. **Model Weights Deprecate Rapidly**: Fine-tuning an $N$-th generation base model (e.g. Gemma 3 or Gemma 4) carries high risk because the next frontier base model ($N+1$) will inevitably crush the custom fine-tune.
2. **Compute Sunk Cost Risk**: Investing heavy financial resources in custom weight training on mid-tier open models provides short-lived returns compared to leveraging frontier API models (Gemini 3.6 Flash).

---

## 2. Strategic Asset Allocation: Where Our Value Lies

Our project's durable competitive advantage is **NOT** in custom fine-tuned model weights. Our durable assets are **Model-Agnostic Engine Components**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     DURABLE PROJECT ASSETS (Immune to Model Leaps)      │
├─────────────────────────────────────────────────────────────────────────┤
│ 1. Curated Decolonized Corpus (`data/sources.db`)                        │
│    • 137,700 literary chunks, 54,900 textbook chunks, tagged by period │
├─────────────────────────────────────────────────────────────────────────┤
│ 2. Morphological Ground Truth Engine (`data/vesum.db`)                   │
│    • 409,000 lemmas & 6.7M inflected forms for deterministic audit      │
├─────────────────────────────────────────────────────────────────────────┤
│ 3. Deterministic QG Linter & Euphony Rules (`scripts/audit/`)            │
│    • Rules enforcing State Standard 2024 & zero-Russianism gates        │
├─────────────────────────────────────────────────────────────────────────┤
│ 4. Hramatka Prompt Harness V3 (Dynamic System Constraints)               │
│    • Runtime structural control enforcing 8/8 activity types & density  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Operational Policy

1. **Use Frontier API Models for Production**: Rely on **Gemini 3.6 Flash** (12s, 10/10 PASS) and **Gemini 3.1 Pro** for production lesson generation today.
2. **Keep Open Models Light & Zero-Shot / Harness-Driven**: Do not spend heavy compute or hundreds of dollars fine-tuning Gemma 4 31B. Use lightweight prompt harness constraints and rely on our deterministic QG linters to clean output.
3. **Dataset Contribution**: Publish our clean datasets (`hramatka_literary_poltava_v1`) for the open-source UNLP community, but keep our project's primary focus on curriculum engine architecture.

---

*Recorded for the Learn Ukrainian Architecture Registry.*
