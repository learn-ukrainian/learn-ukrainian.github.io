# Independent Human-Source Dataset Quality and Evaluation Separation Assessment (#7431)

## 1. Executive Summary & Verification Verdict

Under the operator's human-source dataset mandate (#7423, stream `epic:6321`), this document establishes the independent dataset quality and evaluation separation assessment for the first human-source dataset pilot (#7430).

- **Evaluation Verdict**: **`DATASET_QUALITY_CONFIRMED`**
- **Assessment Receipt ID**: `eval.assessment.c5e1eb862b4aada83dc7e417`
- **Assessed Pilot Receipt**: `receipt.pilot.702e1b404da41ffda2824da5` (`02030df11079f186328b584e480aa462834520bea25f9c16ace87a65c874cdf0`)
- **Assessed Pilot Records SHA-256**: `98e722ff3f9cf9db2283b2b660bb805a5971f761bf488d09304402f201d9e265`
- **Legacy 100-Slot Manifest/Hash**: **REJECTED** (Legacy hash `78a1edad...` and slot templates are non-applicable historical artifacts).
- **Target Issue**: [#7431](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/7431)
- **Downstream Unblocked**: [#7432](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/7432) (Full Denominator), [#7889](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/7889) (Open-Weight Learning Experiments).

---

## 2. EVAL-1: Denominator & Residual Accounting

The successor pilot denominator covers 1,419 evaluated spans from the verified human-authored collection across literary prose and educational humanities.

### Accounting Breakdown

| Category | Span Count | Disposition |
| --- | --- | --- |
| **Total Evaluated Spans** | **1,419** | Evaluated via extraction and language separation |
| **Total Admitted Records** | **1,418** | Admitted under `LOCAL_LEARNING_APPROVED_NON_OCR_HUMAN` |
| **Exported Training Records** | **614** | `builder_training_cleared: true`, partition `training` |
| **Firewalled Held-Out Evaluation** | **559** | `builder_training_cleared: false`, partition `heldout_evaluation` |
| **Development Partition** | **245** | `builder_training_cleared: false`, partition `development` |
| **Quarantined Records** | **1** | `control_character_detected`, partition `quarantine_excluded` |
| **Silent Drops / Unaccounted** | **0** | Strict accounting invariant enforced |

### Covered Strata

1. `literary_fiction_prose` (Cohort `literary-non-ocr`, 1,174 spans)
2. `educational_textbooks_general_humanities` (Cohort `public-textbooks-non-stem-non-ocr`, 245 spans)

### Operator-Excluded Residual Strata (Deferred to #7432)

1. `stem_technical_and_exact_sciences`: Excluded by operator decision from initial humanities/linguistic cohort.
2. `video_captions_transcripts`: Excluded by operator decision due to automated speech-to-text noise.
3. `ocr_scanned_unverified_sources`: Excluded by operator decision; native digital extraction required.
4. `private_teaching_material`: Excluded by operator decision without explicit local-use clearance.

---

## 3. EVAL-2: Independent Quality & Separation Verification

### Verbatim Original-Text Fidelity

- **Fidelity Rate**: **100.0%** (`verbatim_fidelity_rate = 1.0`).
- Every evaluated record matches the exact cryptographic hash of the human-authored source span.
- Zero artificial modernized spellings, zero synthetic transformations, zero manufactured correction pairs.

### Dual-View Loss Mask Verification

- Records supply dual consumer payloads:
  - `faithful_view`: Verbatim representation preserving all original orthography, quotes, and punctuation.
  - `modern_view`: Validated loss mask intervals masking non-target citations, foreign-language quotations, and historical forms from modern production gradient updates.
- All loss mask intervals satisfy `0 <= start <= end <= len(text)` with zero out-of-bound errors.

### Linguistic Validity (VESUM & Sources)

- Modern Ukrainian vocabulary verified against VESUM.
- **Non-Punitive Adjudication**: Dialectal, regional, and historical vocabulary attested in Sources authorities (Грінченко, СУМ-11, Франко, etc.) is preserved without penalty.
- **Strict Invariant**: **No gold claim from model agreement.** Ground-truth status originates solely from verified human authorship.

### Cross-Partition Firewall Integrity

- Chunks and editions are grouped monolithically by work family:
  - `work_family.literary.yuriy_andrukhovych_moskoviada` -> `training` (614 spans)
  - `work_family.public_textbooks.masol_mystetstvo_grade_9` -> `development` (245 spans)
  - `work_family.literary.hrushevskyy_istoriya_ukrayiny_odnotomnyk` -> `heldout_evaluation` (559 spans)
- **Work Family Leaks**: **0** (`training_families ∩ evaluation_families = ∅`).

### Deduplication & Contamination Screening

- **Duplicate Spans Detected**: **0** (1,419 / 1,419 spans have unique SHA-256 digests).
- **Benchmark Contamination Detected**: **False** (Zero hits against ZNO, NMT, or standard evaluation test sets).

---

## 4. EVAL-3: Legitimate Use Preservation & Evidence-Backed Adjudication

- Preserves natural Ukrainian literary and scholarly registers:
  - Yuriy Andrukhovych (*Московіада*): modern postmodern literary prose register.
  - Mykhailo Hrushevsky (*Історія України-Руси / Однотомник*): early 20th-century scholarly historiographical register.
  - L. Masol (*Мистецтво 9 клас*): contemporary standard educational register.
- Extraction anomaly handling: Span `record.human.f336bce65c0295bbcb8c3772` contained anomalous control characters; it was honestly quarantined (`quarantine_excluded`, `training_eligible: false`) rather than artificially rewritten.

---

## 5. EVAL-4: Held-Out Evaluation Protocol & Sealed Custody

- **Custody Firewall**: Held-out evaluation records are sealed on the protected custody layer. Builders receive only public partition receipts with cryptographic hash commitments, preventing training leakage.
- **Scoring Protocol for Downstream Evaluators**:
  - `loss_faithful_view` & `perplexity_faithful_view`: Evaluates model perplexity across all original tokens.
  - `loss_modern_view` & `perplexity_modern_view`: Evaluates perplexity strictly on unmasked modern tokens.
  - `grammatical_accuracy_heldout`: Measures morphological agreement on held-out linguistic probes.

---

## 6. EVAL-5: Independent Reproduction & Cohort Findings

### Cohort Results

| Cohort ID | Stratum | Evaluated Spans | Fidelity Rate | Firewall Separation | Verdict |
| --- | --- | --- | --- | --- | --- |
| `literary-non-ocr` | `literary` | 1,174 | 100.0% | Confirmed | **PASS** |
| `public-textbooks-non-stem-non-ocr` | `public_textbooks` | 245 | 100.0% | Confirmed | **PASS** |

### Independent CLI Verification

```bash
.venv/bin/python scripts/projects/open_model_data/v4_dataset_quality_evaluation.py verify
```
Result:
```
SUCCESS: Assessment verified and confirmed.
```

---

## 7. EVAL-6: Open-Weight Learning Study Methodology (#7889)

### Decoupled Verdict Architecture

Issue [#7889](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/7889) conducts controlled open-weight training experiments. Under operator principles, dataset quality and trained-model utility must receive separate, decoupled verdicts:
1. **Dataset Quality Verdict**: **`PASS`** (confirmed here in #7431 via data integrity, verbatim preservation, linguistic validity, and firewall separation).
2. **Trained-Model Utility Verdict**: **`PENDING_EXPERIMENTAL_STUDY`** (to be determined in #7889 via parameter fine-tuning, loss curves, and perplexity deltas).

### Uncertainty and Limitations

1. **Pilot Scale**: The pilot cohort consists of 1,419 spans across 3 work families; broad lexical variance will expand in #7432.
2. **Excluded Strata**: STEM, video captions, and OCR scans remain excluded residuals.
3. **Tokenizer Fertility**: Base open-weight models (Llama-3, Gemma-2, Mistral) exhibit varying byte-per-token fertility on Cyrillic Ukrainian; fertility adjustments must be controlled during evaluation.
