# ADR 012: Open Model Harness Elevation & Language Pre-training Assessment

> **Status**: APPROVED / IMPLEMENTATION  
> **Date**: July 23, 2026  
> **Authors**: Lead Architecture Review, Sol (`gpt-5.6-sol`), Claude Opus (`claude-opus-4-8`)  
> **Target Epic**: #4542 (Hramatka Model Qualification & Authoring Engine)

---

## Context & Problem Statement

In our level-playing-field benchmark on the Lviv rent anchor text (*«Як ми шукали квартиру у Львові»*), Gemini 3.6 Flash and Gemini 3.1 Pro passed qualification with 10/10 and 9.5/10 scores, while open models (Gemma 4 31B) reached 8.2/10 (NEAR) and Poolside Laguna S 2.1 scored 3.5/10 (FAIL).

Post-hoc prompt repairs (Tours 3 & 4) patched surface JSON keys and labels, but did **not** solve the fundamental architectural issue: **open models require specialized harness constraints to achieve Gemini-level activity density, pedagogical rigor, and flawless Ukrainian metalanguage.**

Furthermore, Poolside Laguna S 2.1 failed catastrophically due to deep pre-training data contamination (teaching Russianisms like *затем* and *перечисленого* as correct Ukrainian truth).

We must answer two core architectural questions:
1. How do we upgrade the **authoring harness and prompts** so Gemma 4 31B generates 10/10 PASS lessons natively?
2. Why did Laguna fail, and is it worth attempting to improve Laguna for Ukrainian pedagogy?

---

## Decision 1: Upgrading the Authoring Harness for Open Models (Gemma Elevation)

Open-weights models (Gemma 4 31B, Llama 4, Mistral) require a **Structured Harness Constraint System** rather than a single generic prompt.

### 1. Harness Enhancements to Implement:

- **A. Strict Activity Density Constraints**:
  - Enforce exactly **8 activity types** per lesson.
  - Require a minimum of **5–7 items per activity** (stopping activity collapse at 3 items).

- **B. Metalanguage Guardrails (Zero-Hallucination Grammar Notes)**:
  - Provide a closed list of Ukrainian linguistic terms (`іменник`, `прикметник`, `дієслово`, `прислівник`, `займенник`, `числівник`, `прийменник`, `сполучник`, `частка`). Prohibit inventing terms (e.g. *«речник»* for noun or *«прибутковий сполучник»*).
  - Prohibit Latin script in learner-facing phonetics/euphony rules (e.g., prohibiting Latin letters like "L/V/M").

- **C. Real Morphosyntax Error-Correction Schema**:
  - Instruct the `error-correction` module to test real B1 Ukrainian morphosyntax errors (`більш дешевша` $\rightarrow$ `дешевша`, case government after `ніж` / `за` / `від`, locative `на поверсі`) instead of factual recall or text substitution.

- **D. Mandatory B1 Communicative Task**:
  - Mandate that Activity 8 be a **Communicative Production Task** (e.g. roleplay calling a landlord, comparing two apartment listings, or writing an advertisement) to ensure 45-minute lesson completeness.

---

## Decision 2: Assessment of Poolside Laguna S 2.1 (Why It Failed & Future Disposition)

### Why Laguna S 2.1 Cannot Be Elevated via Prompting:
1. **Pre-training Data Contamination**: Laguna's underlying training corpus contains severe Russian/Surzhyk contamination. It confidently generates Russianisms (*затем*, *перечисленого*, *незважно*, *мають позитивний ставлення*) and treats them as *correct answer-key truth*.
2. **Anti-Pedagogy & False Rules**: Laguna invents false grammatical claims (e.g. asserting that locative *підлозі* is wrong, or claiming *в Києві* is ungrammatical).
3. **Broken Reasoning Keys**: In `error-correction`, Laguna emits `error == correction` (claiming non-existent errors), and produces nonsensical option repeats (*одразу одразу*).

### Disposition:
- **Laguna S 2.1 is REJECTED for Ukrainian Content Generation**. Prompt engineering cannot purge corrupted linguistic pre-training weights.
- **Do not waste compute on fine-tuning Laguna for language instruction**.
- Laguna may only be evaluated as a pure code/JSON syntax validator or execution engine, never as a language or pedagogy authority.

---

## Action Plan & Roadmap

1. **Harness Prompt V3 Development**: Update `hramatka/ops/author_bakeoff.py` and `scripts/wiki/` with Harness V3 incorporating Decisions 1A–1D.
2. **Dataset Release**: Publish `hramatka-uk-pedagogy-v1` to HuggingFace and share with UNLP researchers to fine-tune open models directly.
3. **Pre-Release Gate**: Do **NOT** release open-model seats into production until Harness V3 achieves a native 10/10 PASS on Gemma 4 31B without post-hoc intervention.

---

*Recorded and approved for the Learn Ukrainian Architecture Registry (July 2026).*
