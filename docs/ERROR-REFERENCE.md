# Audit & Review Reference

This document provides a reference for the various quality gates and pedagogical checks performed during the curriculum development process.

---

## 1. Structural Gates

These checks ensure the module follows the required file structure and basic formatting.

| Check | Description | Fix |
|-------|-------------|-----|
| **Structure** | Verifies mandatory sections like `# Підсумок` (Summary) and `# Вправи` (Activities) or their sidecar equivalents. | Ensure all required headers or sidecar files exist. |
| **Lint** | Checks for basic Markdown formatting errors, AI artifacts, or invalid checkbox syntax. | Follow the specific line-by-line instructions in the audit log. |
| **Section Order** | Ensures sections follow the standard sequence: Summary → Activities → Vocabulary. | Reorder sections in the `.md` file to match the specification. |

---

## 2. Quality Gates

These checks measure the pedagogical depth and richness of the content.

| Check | Description | Fix |
|-------|-------------|-----|
| **Words** | Core content word count against the `word_target` defined in the plan. | Expand explanations, add more authentic examples, or develop narrative sections. |
| **Richness** | A weighted score (target 95%+) based on engagement, vocabulary density, and activity variety. | Add callouts, dialogues, cultural references, or proverbs. |
| **Engagement** | Counts callouts like `[!myth-buster]`, `[!history-bite]`, or `[!quote]`. | Add at least 5-6 relevant callouts throughout the lesson. |
| **Immersion** | The ratio of Ukrainian to English text based on the level's phase. | Adjust the balance of L1/L2 by converting explanations to Ukrainian or adding more narrative. |
| **Naturalness** | A 0-10 score evaluating the quality of Ukrainian (target 8+). | Rewrite unnatural passages; ensure native-level phrasing and correct grammar. |

---

## 3. Activity Gates

These checks validate the exercises provided in the module.

| Check | Description | Fix |
|-------|-------------|-----|
| **Activities** | Total number of unique activities against the level's requirement. | Add more activities to meet the minimum count (usually 8+). |
| **Density** | Ensures each activity has enough items (e.g., 12+ items per quiz). | Add more items to the failing activities. |
| **Unique Types** | Number of distinct activity types used (e.g., quiz, fill-in, unjumble). | Diversify the activity types used in the module. |
| **Priority** | Checks for level-specific priority activity types (e.g., error-correction at A2+). | Ensure at least one priority type is included. |

---

## 4. Specific Pedagogical Violations

Common violations found in the **PEDAGOGICAL VIOLATIONS** section of the audit log.

| Violation Type | Meaning |
|----------------|---------|
| **NO_UKRAINIAN_CONTENT** | Activity has too little Cyrillic text (pedagogically weak). |
| **UNJUMBLE_WORD_MISMATCH** | Scrambled words in an unjumble activity don't match the answer. |
| **ERROR_WORD_HIGHLIGHTED** | Error-correction activity gives away the answer by bolding the error. |
| **LEVEL_RESTRICTION** | Activity type used is not allowed at this CEFR level (e.g., anagram at B1). |
| **MALFORMED_CLOZE** | Cloze activity uses complete dialogue lines instead of words/phrases. |
| **OUTLINE_SECTION_MISSING** | A section defined in the `meta.yaml` outline is missing from the Markdown. |
| **VOCABULARY_NOT_DEFINED** | A word used in activities is not found in the vocabulary sidecars (A1-A2). |
| **DUPLICATE_SYNONYMOUS_HEADERS** | Multiple headers contain the same keyword, causing confusion. |

---

## 5. Review Criteria (v4 Protocol)

During the Deep Quality Review (`/review-content-v4`), the following dimensions are scored:

1. **Experience Quality**: Overall engagement and intellectual depth.
2. **Language**: Native-level Ukrainian phrasing, register correctness, no Russianisms.
3. **Linguistic Accuracy**: Historical facts verified, dates correct, grammar rules accurate.
4. **Propaganda Filter**: Decolonized narrative, avoid imperial euphemisms.
5. **Humanity**: Warm teacher voice vs. robotic AI tone.
6. **LLM Fingerprint**: Absence of AI cliches and generic openings.
