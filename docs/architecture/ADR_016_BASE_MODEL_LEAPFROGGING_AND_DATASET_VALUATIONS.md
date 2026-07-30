# ADR 016: Base Model Leapfrogging & Data/Harness Value Preservation

> **Superseded for current strategy:** Only the general asset-category insight
> is retained: data, evidence, and evaluation tooling can outlast one model
> generation. Specific model rankings, inventory counts, data-quality,
> purity/decolonization, and production-policy claims below are not
> authoritative. Use
> [Ukrainian Open-Model Data Infrastructure: North Star](../strategy/UKRAINIAN_OPEN_MODEL_DATA_INFRASTRUCTURE_NORTH_STAR.md)
> for the evidence-backed direction and current data boundaries. This file is
> retained as historical context.
>
> **Status**: SUPERSEDED — historical context only
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

The historical proposal identified four potentially durable asset categories.
This is not a current inventory or a quality assessment:

1. Literary and reference source inventories, pending provenance, rights,
   quality, and balance audits.
2. VESUM-backed morphology integration, with the exact version, counts,
   semantics, and license pinned for each use.
3. Validation and evidence tooling, limited to the rules and behavior that
   tests actually verify.
4. Prompt and evaluation harnesses, durable only where their interfaces,
   inputs, and results remain reproducible across models.

---

## 3. Historical proposals and current disposition

1. The model-specific production recommendation was never supported by a
   reproducible qualification and is withdrawn.
2. The recommendation not to train local model weights now is retained by the
   current north star, with future training requiring a scoped need and
   approval.
3. The instruction to publish `hramatka_literary_poltava_v1` as a clean dataset
   is withdrawn. It is an internal candidate collection pending provenance,
   rights, deduplication, split, contamination, and linguistic audits.

---

*Recorded for the Learn Ukrainian Architecture Registry.*
