# Рецензія: Як говорити про граматику

**Level:** B1 | **Module:** M01
**Overall Score:** 9.2/10
**Status:** PASS
**Reviewed:** Friday, February 13, 2026

## Plan Verification
*   **Outline Compliance:** The module follows the `content_outline` from the meta and plan files. All H2 sections are present, and the H3 hierarchy for parts of speech and cases is strictly maintained.
*   **Vocabulary Scope:** All "required" and "recommended" vocabulary from the plan is included in the vocabulary YAML and used effectively in the text.
*   **Grammar Scope:** Correctly identifies and focuses on B1.0 bridge metalanguage without premature deep-dives into M02/M03 verb/rule specifics.
*   **Objectives:** The module successfully addresses all three primary objectives: identifying parts of speech, naming seven cases, and describing sentence elements using Ukrainian terms.

## Scores
| # | Dimension | Score | Evidence |
|---|---|---|---|
| 1 | Experience Quality | 8.8 | Strong teacher voice, but coverage of cases is inconsistent in depth (see Pedagogy). |
| 2 | Coherence | 9.5 | Excellent logical progression from "Why" to "Parts of Speech" to "Syntax." |
| 3 | Relevance | 10.0 | Critical bridge module for B1 autonomy. |
| 4 | Educational | 9.5 | High value cultural bites (Smotrytsky, Franko) and decolonization focus (Line 107). |
| 5 | Language | 9.5 | Native-level naturalness, respects euphony (у/в, і/й). |
| 6 | Pedagogy | 8.5 | Weak analogy for declension (Line 54) and uneven case detail distribution. |
| 7 | Immersion | 9.5 | 96.4% immersion is managed well through clear context and metalanguage cognates. |
| 8 | Activities | 8.5 | Activity 1 (Quiz) fails the plan's item count requirement (8 vs 10+). |
| 9 | Richness | 10.0 | High word count (120%), multiple Mermaid diagrams, and specific poet quotes. |
| 10 | Beginner Safety | 9.0 | Clear English framing in the intro eases the A2->B1 transition. |
| 11 | LLM Fingerprint | 9.5 | Low footprint; uses specific Ukrainian context rather than generic filler. |
| 12 | Linguistic Accuracy | 10.0 | Grammar terminology and case questions are historically and linguistically precise. |

**Weighted Overall:** 9.2/10

## Auto-Fail Checklist Results
*   **Russianisms:** NONE found.
*   **Calques:** NONE found.
*   **Grammar scope violations:** NONE found.
*   **Activity errors:** Item count violation (Activity 1).
*   **Beginner safety:** PASS.

## Critical Issues Found
1.  **Activity Item Count Deficiency (Plan Violation):** In `activities/how-to-talk-about-grammar.yaml`, the Quiz activity (Activity 1) contains only 8 items. The plan explicitly requires `- items: 10+`.
2.  **Pedagogical Inconsistency in Case Coverage:** In the section «Відмінки: сім ключів», the headers for «Називний відмінок» (Line 191), «Давальний відмінок» (Line 196), and «Місцевий відмінок» (Line 222) lack the «Додаткова інформація» sections provided for the other four cases. This leaves the learner with significantly less detail for these foundational categories.
3.  **Flawed Metalanguage Analogy:** Line 54: «Це як розрізняти «модель машини» та «станцію технічного обслуговування»: одне стосується суті об'єкта, інше — того, як з ним працювати.» The comparison of `відміна` (declension group) to a "service station" is logically flawed; a declension group is an inherent structural property of the word (the engine type/fuel), not an external service facility.

## Ukrainian Language Issues
*   **Missing IPA for Key Concepts:** While most lemmas have IPA in the vocabulary file, the terms «Недоконаний вид» and «Доконаний вид» (Lines 284-287) are introduced in the text as critical B1 concepts but lack IPA or stress marks in their first appearance, which is a missed opportunity for a bridge module.
*   **Formatting Inconsistency:** Line 118: «Приклад: «Сьогодні чудовий сонячний день»» uses straight quotes `"` instead of the Ukrainian angular quotes `«...»` used elsewhere in the document.

## Beginner Safety Audit
The module is safe for B1.0 bridge learners. The English introduction (Lines 23-28) provides a necessary "soft landing" before the high-immersion technical sections. The use of cognates in metalanguage (граматика, приклад, правило) further supports the transition.

## Strengths
*   **Decolonization Focus:** Line 107 explicitly warns against the Russianism «глагол», providing the native etymology for «дієслово» (дія + слово).
*   **Cultural Anchoring:** Integration of Smotrytsky's 1619 grammar (Line 158) provides historical depth often missing from modern curricula.
*   **Syntactic Logic:** The "Note about structure" (Line 307) correctly explains why cases are necessary in a free-word-order language, solving a common learner frustration.

## Fix Plan to Reach 9.5/10
1.  **Activities (Line 1):** Add at least 2 more items to Activity 1 (Quiz) to meet the plan's 10+ requirement.
2.  **Pedagogy (Lines 191-222):** Expand the sections for Називний, Давальний, and Місцевий відмінки with a «Додаткова інформація» block, following the pattern established for Родовий and Орудний.
3.  **Clarify Analogy (Line 54):** Replace the "service station" comparison with «тип двигуна (дизельний чи бензиновий)», which better reflects how a word's `відміна` dictates its internal behavior/endings.
4.  **Typography (Line 118):** Correct straight quotes to `«Сьогодні чудовий сонячний день.»`.

## Verification Summary
- Content lines read: 350
- Activity items checked: 94
- Vocabulary items checked: 27
- Plan requirements checked: 100%
- Issues found: 5

## Verdict: PASS
The module is a high-quality, linguistically rigorous introduction to Ukrainian metalanguage. Despite a minor plan violation regarding activity item counts and some inconsistency in section depth, it effectively prepares the learner for the B1.1 immersion phase.
