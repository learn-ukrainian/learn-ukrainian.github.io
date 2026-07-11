# Automated CEFR-Level Assessment for Ukrainian Texts

Source: Kanishcheva & Kopotev, UNLP 2026 — https://aclanthology.org/2026.unlp-1.18/

Compact per-record digest for research-registry id `unlp-2026-cefr-assessment`.
Paraphrase and pointers only; no paper tables, figures, or verbatim passages are
reproduced here. Read the full source at the link above.

## Finding

The authors build an A1–B2 difficulty classifier for Ukrainian-as-a-foreign-language
texts derived from print textbooks, and compare deterministic linguistic features
against transformer and large-language-model baselines. Their headline result is that
an interpretable feature model (a random forest over explicit descriptive, lexical,
morphological, and syntactic features) matches or edges out a fine-tuned multilingual
transformer and a strong general LLM on macro-F1. The single strongest individual
marker they report is average dependency-tree depth, followed by lexical-diversity
signals (hapax counts, unique lemmas, type-token ratio) and sentence-length statistics.
Confusion concentrates on the adjacent A2/B1 boundary, and the released corpus has no
C1/C2 coverage. The paper also validates that classification is driven by structural
complexity rather than topic vocabulary.

The pedagogical takeaway we adopt is method-level: for level-sensitivity tooling,
deterministic, interpretable features are preferable to an opaque model, both for
auditability and because they were empirically competitive here.

## What we actually shipped (adoption boundary — do not overclaim)

Issue #4952 Phase 1 has merged (`scripts/audit/text_difficulty.py`). It is
**advisory and uncalibrated**: it extracts reader-visible Ukrainian surface and
lexical observations only — token and sentence length, unique and hapax Ukrainian
forms, mean type-token ratio (MATTR) over fixed windows, and language coverage.
Dependency-tree depth and clauses-per-sentence — including the paper's strongest
marker — remain explicitly **unavailable** (no parser is used). The tool produces
**no CEFR estimate, no threshold, and no pass/fail verdict**. Calibration and any
gating are out of scope for Phase 1 and deferred.

## Method hygiene we carry forward

- Prefer deterministic, interpretable features for pedagogy tooling over black-box scoring.
- If a difficulty classifier is ever trained on our corpus, replicate the paper's
  topic-bias validation so level signal is structural, not topical.
- Our graded corpus is far larger than their ~84K-token set and extends to C1/C2,
  so any future calibration must be done on our own data, not their published cut-offs.
