# TOMBSTONE: Quarantined `uldr_v05_grammar_valency` Dataset

**Status:** RETIRED / QUARANTINED / DO NOT USE FOR TRAINING OR SFT/DPO ALIGNMENT
**Retired Date:** 2026-09-23
**Governing Issue:** [#8342](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8342) (replaces [#8143](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8143))
**Parent Epic:** [#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321)
**Related Issues:** [#8339](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8339), [#8338](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8338)

---

## 1. Background & Reason for Quarantine

The `uldr_v05_grammar_valency` release assembled under Issue #8143 was evaluated against the mechanical dataset acceptance gates under Epic #6321 and [#8339](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8339).

The dataset exhibited systemic flaws that risk poisoning model training:
1. **93% Passivity / Control Imbalance:** 32,629 of 35,000 rows were labeled as controls ("nothing wrong here"), with only 2,371 rows of actual corrections. This severe passivity bias induces catastrophic under-correction and failure to catch grammatical defects.
2. **Template Collapse:** Exactly 13 question templates covered 100% of the 35,000 lines ($K=13$), failing the required skeleton entropy floor ($K \ge 50$, $H_{\text{norm}} \ge 0.80$).
3. **Severe Category Deficit:** 8 of 20 grammatical error categories had fewer than 50 examples, while others suffered from synthetic distortion.
4. **Synthetic Corruption Artifacts:** Portions of the dataset relied on rule-based or synthetic negative generation rather than authentic human linguistic performance.

---

## 2. Strict Prohibition

> [!CAUTION]
> **DO NOT USE THIS DATASET FOR MODEL TRAINING, SFT FINE-TUNING, DPO PREFERENCE TUNING, OR HARNESS EVALUATION.**
>
> Ingesting these shards into training pipelines risks inducing passive collapse where the model ignores grammatical defects in learner text.

---

## 3. Active Canonical Replacement

The grammar valency, prepositional government, and morphosyntactic dataset has been completely rebuilt from authentic human-annotated sentences from the pinned UA-GEC corpus under [#8342](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8342):

- **Canonical Dataset Location:** `data/projects/open_model_data/components/grammar/`
- **Governing Specification:** [`docs/projects/open-model-data/GRAMMAR_DATASET_SPEC_8342.md`](../../../docs/projects/open-model-data/GRAMMAR_DATASET_SPEC_8342.md)
- **Acceptance Profile:** [`scripts/projects/open_model_data/profiles/grammar_8342.yaml`](../../../scripts/projects/open_model_data/profiles/grammar_8342.yaml)
- **Verified Mixture:** Exactly 75.0% substantive corrections / 25.0% pristine controls, 0 synthetic corruptions, 0 shared `doc_id` leakage to held-out test splits, and 100% verified Ukrainian linguistic authorities.
