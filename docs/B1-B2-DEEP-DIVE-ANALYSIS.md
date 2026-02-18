# Deep Dive Gap Analysis: B1 & B2 Curriculum

**Date:** February 17, 2026
**Scope:** Detailed review of B1 (Intermediate) and B2 (Upper Intermediate) plans against State Standard 2024.
**References:** `docs/l2-uk-en/state-standard-2024-mapping.yaml`, `curriculum/l2-uk-en/plans/{b1,b2}/*`

---

## Level B1: Intermediate

### 1. Pronoun System Gap (Major)
*   **Requirement:** State Standard §4.2.1.4 (B1): "Expanded pronouns — indefinite (*хтось, щось, дехто*), negative (*ніхто, ніщо*), relative (*який, що, хто*)".
*   **Status:**
    *   Relative pronouns are well-covered in `relative-clauses-*.yaml`.
    *   **GAP:** Indefinite (*-сь, -небудь, де-*) and Negative (*ні-*) pronouns lack a dedicated grammar module. `aspect-negation.yaml` touches on negative adverbs (*ніколи*) but not the full pronoun paradigm.
*   **Action:** Create `curriculum/l2-uk-en/plans/b1/indefinite-negative-pronouns.yaml`.

### 2. Phonetics & Assimilation (Minor)
*   **Requirement:** State Standard §4.1.1 (B1): "Consonant clusters, assimilation, simplification; alternations".
*   **Status:** No dedicated module. This is often "hidden" in other topics, but explicit instruction on *assimilation* (e.g., *г* -> *х* in *легко*) is crucial for B1 listening comprehension.
*   **Action:** Create `curriculum/l2-uk-en/plans/b1/phonetics-assimilation.yaml` or integrate heavily into `ready-for-immersion.yaml`.

### 3. "Deverbal Nouns" (Word Formation)
*   **Requirement:** State Standard §4.3.4 (B1): "Verbal nouns — -ння/-ення (*читання, навчання*)".
*   **Status:** Covered in A2 (`word-formation-*`)? B1 list has `diminutives-master-class`. Need to ensure `-ння` is revisited as a productive B1 tool for abstract concepts.
*   **Action:** Add a focused section to `abstract-concepts-processes.yaml` specifically on forming nouns from verbs (Process -> Object).

---

## Level B2: Upper Intermediate

### 1. Pluperfect Tense (Major Gap)
*   **Requirement:** State Standard §4.1.3.1 (B2): "Indicative — ... pluperfect (*давноминулий*)".
*   **Status:** Completely missing. While rare in spoken Ukrainian, it is a marker of literary/high style (B2/C1) and required by the standard.
*   **Action:** Create `curriculum/l2-uk-en/plans/b2/pluperfect-tense.yaml`.

### 2. One-Member Sentences (Verification)
*   **Requirement:** State Standard §4.3.3 (B2): "One-member sentences — impersonal, infinitive, nominative".
*   **Status:** `one-member-sentences.yaml` exists in the B2 list.
*   **Action:** Verify this module covers the full typology:
    *   Definite personal (*Люблю грозу...*)
    *   Indefinite personal (*Кажуть, що...*)
    *   Impersonal (*Світає.*)
    *   Nominative (*Ніч.*)

### 3. Syntax: Direct/Indirect Speech Mastery
*   **Requirement:** State Standard §4.3.5 (B2): "Direct and indirect speech — transformation rules".
*   **Status:** B1 covers basic reporting. B2 needs complex reporting (mixed sentence types, reporting thoughts vs words, free indirect discourse).
*   **Action:** Ensure `news-analysis-basics.yaml` or a new module `advanced-reported-speech.yaml` covers these nuances.

---

## Action Plan Summary

### Immediate Fixes (Create New Plans)

1.  **B1:** `curriculum/l2-uk-en/plans/b1/indefinite-negative-pronouns.yaml`
    *   Focus: *хтось vs хто-небудь vs дехто*; *ніхто* + double negation.
2.  **B1:** `curriculum/l2-uk-en/plans/b1/phonetics-assimilation.yaml`
    *   Focus: Pronunciation rules for fluency (*-ться*, *шс* -> *с*, etc.).
3.  **B2:** `curriculum/l2-uk-en/plans/b2/pluperfect-tense.yaml`
    *   Focus: *ходив був*, *робив був*. Literary context.

### Content Enhancements (Edit Existing)

4.  **B1:** Update `abstract-concepts-processes.yaml` to explicitly drill `-ння` formation.
5.  **B2:** Review `one-member-sentences.yaml` for completeness (4 types).
6.  **B2:** Review `news-analysis-basics.yaml` to ensure it serves as the "Advanced Reported Speech" module.

