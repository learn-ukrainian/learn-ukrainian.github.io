# Gap Analysis Report: A1 & A2 Curriculum vs State Standard 2024

**Date:** February 17, 2026
**Scope:** `curriculum/l2-uk-en/plans/a1/` and `curriculum/l2-uk-en/plans/a2/`
**Reference:** `docs/l2-uk-en/state-standard-2024-mapping.yaml`

## Executive Summary

The A1 and A2 curricula are highly robust and well-aligned with the 2024 State Standard thematic and functional requirements. A1 effectively scaffolds the "Survival" competence, while A2 builds the "Social" competence.

However, a few structural anomalies, potential redundancies in A2 Health topics, and a specific grammatical gap regarding Passive Voice (A2) were identified.

---

## Level A1: Beginner

### 1. State Standard Coverage
*   **Compliance:** High. The curriculum actually exceeds the strict "Nom/Acc/Loc/Voc" case limitation of the mapping file by introducing **Genitive** for absence (`a1-16`) and origin (`a1-30`). This is a pedagogical necessity for high-frequency structures like "немає часу" and "з України" and should remain.
*   **Vocative Case:** Explicitly covered in `a1-32` and `a1-42` as required.
*   **Future Tense:** Covered in `a1-22`, meeting the standard for "Indicative Mood".

### 2. Redundancies & Misnaming
*   **`prepositions-iii.yaml` (`a1-30`):**
    *   **Issue:** The title suggests a sequence (III), but there are no files named `prepositions-i` or `prepositions-ii`.
    *   **Context:** `a1-13` (Locative) and `a1-16` (Genitive) serve as the first two "preposition" modules effectively.
    *   **Recommendation:** Rename `a1-30` to `prepositions-direction-origin.yaml` or similar to describe its function rather than its sequence number.

### 3. Ordering Issues
*   No significant ordering blocking issues found. The progression from Phonetics -> Gender -> Cases -> Tenses is logical.

---

## Level A2: Elementary

### 1. State Standard Coverage
*   **Gap: Passive Voice / Participles:**
    *   **Requirement:** State Standard §4.1.3.1 mentions "passive voice (participles)" for A2.
    *   **Status:** No dedicated module found. `a2-40` and `a2-39` cover adjective suffixes, but do not explicitly teach the formation of passive participles (e.g., *зроблений*, *написаний*) or passive constructions.
    *   **Recommendation:** Add a module `a2-71-passive-voice.yaml` or integrate into `wf-mastery`.

### 2. Redundancies & Misnaming
*   **Health Cluster Overlap (`a2-34`, `a2-55`, `a2-59`):**
    *   `a2-34` (Seq 34): "At the Doctor" (Health and Medical Vocabulary)
    *   `a2-55` (Seq 55): "Health and Body" (Feeling Good)
    *   `a2-59` (Seq 59): "Doctor Visit" (Medical Consultation)
    *   **Analysis:** `a2-34` and `a2-59` have nearly identical titles and very similar scopes (symptoms, appointments). `a2-55` focuses on body parts and simple states, which seems foundational and perhaps placed too late (Seq 55) if `a2-34` (Seq 34) already assumes medical vocab.
    *   **Recommendation:**
        1.  Merge `a2-34` and `a2-55` into an earlier "Health Basics" module.
        2.  Keep `a2-59` as the advanced "Medical Scenarios" module.
        3.  Rename to avoid "At the Doctor" duplicate title.

*   **Adjective Suffixes Naming:**
    *   `adj-suffixes.yaml` (`a2-40`) vs `adjective-suffixes-qualities.yaml` (`a2-39`).
    *   **Issue:** Inconsistent naming convention (`adj` vs `adjective`).
    *   **Recommendation:** Rename `a2-40` to `adjective-suffixes-types.yaml` for consistency.

### 3. Ordering Issues
*   **Health Sequence:** `a2-55` (Health/Body) appears *after* `a2-34` (At the Doctor). It would be more logical to teach body parts (`a2-55`) *before* or alongside the doctor visit (`a2-34`).

### 4. Thematic Gaps (Catalogue B)
*   **Science & Tech:** Covered well in `a2-50`.
*   **Economy:** Covered in `a2-10` and `a2-24`.
*   **Politics:** Not explicitly covered, which is appropriate for A2 (reserved for B1/B2).

---

## Action Plan

1.  **Rename** `curriculum/l2-uk-en/plans/a1/prepositions-iii.yaml` -> `prepositions-direction-origin.yaml`.
2.  **Rename** `curriculum/l2-uk-en/plans/a2/adj-suffixes.yaml` -> `adjective-suffixes-types.yaml`.
3.  **Consolidate** A2 Health modules:
    *   Move `a2-55` (Body) to an earlier slot (e.g., swap with `a2-34`).
    *   Differentiate titles for `a2-34` (e.g., "Health Basics") vs `a2-59` (e.g., "Medical Care").
4.  **Create** `curriculum/l2-uk-en/plans/a2/passive-structures.yaml` to cover the State Standard gap for passive voice basics.
