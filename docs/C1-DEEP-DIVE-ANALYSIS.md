# Deep Dive Gap Analysis: C1 Curriculum

**Date:** February 17, 2026
**Scope:** Detailed review of C1 (Advanced) plans against State Standard 2024.
**References:** `docs/l2-uk-en/state-standard-2024-mapping.yaml`, `curriculum/l2-uk-en/plans/c1/*`

---

## Level C1: Advanced

### 1. High Formal Register (Major Gap)
*   **Requirement:** State Standard §4.4.1.1 (C1): "Official style... substyles".
*   **Status:** `high-formal-register.yaml` exists but is a **Version 1.0 Stub** with "TBD" content.
*   **Action:** Immediate priority to flesh out this plan. It must cover:
    *   **Bureaucratic Syntax:** Passive chains (*було прийнято рішення*), nominalization (*з метою покращення*).
    *   **Document Types:** Laws (*Закон*), Decrees (*Постанова*), Protocols (*Протокол*).
    *   **Clichés:** *Відповідно до...*, *На підставі...*, *З огляду на...*.

### 2. Asyndetic Syntax (Nuance Gap)
*   **Requirement:** State Standard §4.3.4.2 (C1): "Asyndetic complex sentences — semantic relations".
*   **Status:** Covered in `advanced-punctuation.yaml`, but the focus there is *punctuation rules* (Where to put the colon?).
*   **Gap:** The *semantic logic* is missing. Learners need to know *why* to use a colon (explanation/cause) vs a dash (consequence/contrast) vs a comma (sequence).
*   **Action:** Create `curriculum/l2-uk-en/plans/c1/asyndetic-semantics.yaml` (The Logic of the Dash and Colon). Focus on replacing conjunctions (*тому що* -> colon, *але* -> dash).

### 3. Rhetoric & Persuasion (Expansion Needed)
*   **Requirement:** State Standard §4.3.5 (C1): "Rhetoric — argumentation, persuasion".
*   **Status:** `rhetorical-questions.yaml` covers the interrogative aspect. `hyperbole-litotes.yaml` covers magnification.
*   **Gap:** Argumentative structures (Thesis -> Antithesis -> Synthesis) and figures of speech like *anaphora* (repetition), *epiphora*, and *gradation* are missing or scattered.
*   **Action:** Create `curriculum/l2-uk-en/plans/c1/persuasive-speech.yaml`. Focus on structuring a political or debating speech.

### 4. Professional Terminology (Verification)
*   **Requirement:** State Standard Morphology (C1): "Professional terminology".
*   **Status:** `professional-scenarios.yaml` exists.
*   **Action:** Verify it includes *word formation* for professional terms (suffix *-ість*, *-ння*, *-лог*).

---

## Action Plan Summary

### Immediate Fixes (Update/Create Plans)

1.  **Update:** `curriculum/l2-uk-en/plans/c1/high-formal-register.yaml`
    *   Status: **Critical**. Convert from Stub to Full Plan.
    *   Content: Officialese, passive constructions, document templates.

2.  **Create:** `curriculum/l2-uk-en/plans/c1/asyndetic-semantics.yaml`
    *   Focus: The semantic difference between `:` and `—` in complex sentences.

3.  **Create:** `curriculum/l2-uk-en/plans/c1/persuasive-speech.yaml`
    *   Focus: Structuring arguments, using anaphora/gradation for effect.

### Content Enhancements (Review)

4.  **Review:** `advanced-punctuation.yaml` to ensure it cross-references the semantic module.
5.  **Review:** `professional-scenarios.yaml` to ensure it covers *morphological* derivation of terms, not just vocabulary lists.

