# Component: Decolonization & Calque Defense

**Governing Issue:** [#8340](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8340)
**Parent Epic:** [#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321)
**Status:** Active Development

## Purpose
Curates high-precision, dictionary-grounded pairs and chain-of-thought trajectories that:
1. Detect and eliminate Russianisms, syntactic calques, and Soviet administrative distortion.
2. Defend authentic Ukrainian constructions against hyperpurist false corrections.
3. Validate every positive and negative candidate against VESUM, СУМ-20, and authoritative style guides (Антоненко-Давидович, Городенська, Пономарів).

## Dataset Outputs
- `decolonization_sft.jsonl`: Multi-turn decolonization reasoning trajectories.
- `decolonization_dpo.jsonl`: Length-matched contrastive preference pairs (accepted authentic vs rejected calqued/hyperpurist).
