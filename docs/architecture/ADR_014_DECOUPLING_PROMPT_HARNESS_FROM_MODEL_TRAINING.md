# ADR 014: Decoupling Runtime Prompt Harness from Model Fine-Tuning

> **Status**: APPROVED / ARCHITECTURAL PRINCIPLE  
> **Date**: July 24, 2026  
> **Authors**: Lead Architecture Review, UNLP Strategy Team  
> **Target Epic**: #4542 (Hramatka Authoring Architecture & Harness Separation)

---

## Context & Key Insight

A critical architectural distinction exists between **Runtime Prompt Engineering** (Harness Constraints) and **Model Fine-Tuning** (Weight Adaptation):

- **Prompt Engineering (Harness Layer)**: Controls structural activity shapes, JSON schemas, activity variety (8/8 activity types), and item density ($\ge 5$ items per activity). It runs dynamically at $0.00 compute cost.
- **Model Fine-Tuning (Weight Layer)**: Embeds deep linguistic competence, Poltava literary euphony (*милозвучність*), zero-Russianism habits, and authentic grammar terminology directly into model parameters.

Attempting to force model weights to solve purely structural formatting issues via expensive fine-tuning is an anti-pattern. Conversely, expecting prompt engineering to fix corrupted pre-training language weights is equally flawed.

---

## Decoupled Architectural Responsibilities

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          HRAMATKA AUTHORING ENGINE                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│ LAYER 1: RUNTIME PROMPT HARNESS (In-Context Prompt Engineering)               │
│ • Controls: Activity counts (8/8), item density (>=5 items), JSON schemas      │
│ • Mechanics: System prompts, JSON schema enforcement, structural exemplars       │
│ • Cost: $0.00 | Instantaneous iteration without retraining                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│ LAYER 2: MODEL NEURAL WEIGHTS (Fine-Tuned Gemma 4 31B / Gemini 3.6 Flash)       │
│ • Controls: Native Ukrainian vocabulary, zero Russianisms, correct morphology   │
│ • Mechanics: SFT on Poltava literature + DPO preference alignment               │
│ • Cost: ~$25–$50 GPU compute for open models                                    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Architectural Rules

1. **Activity Density is Driven by Prompt Engineering**:
   - High activity density ($\ge 5$ items per activity across 8 activity types) MUST be enforced dynamically via Harness V3 system prompts and JSON schema templates.
   - Do not waste fine-tuning compute trying to teach a model *how many items to output*; use explicit system prompt constraints.

2. **Linguistic Purity is Driven by Neural Weights & Linters**:
   - Eliminating Russianisms, enforcing Poltava literary euphony (*милозвучність*), and correcting case government are handled by the model's weights (or fine-tuning) + deterministic linter gates (`scripts/audit/hramatka_qg_rules.py`).

3. **Immediate Action Item**:
   - Test Harness V3 prompt engineering **first** on raw Gemma 4 31B and Gemini 3.6 Flash to verify high activity density at $0.00 cost before launching GPU fine-tuning runs.

---

*Recorded for the Learn Ukrainian Architecture Registry.*
