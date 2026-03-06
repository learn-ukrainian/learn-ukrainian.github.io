# Content Review: plurals-and-alternation
**Track:** a1 | **Sequence:** 13
**Mode:** core
**Tier:** 1-beginner
**Pipeline:** PASS (words: 1537, target: 1200)
**Verdict:** C

## Plan Adherence

| Plan Point | Status | Notes |
|-----------|--------|-------|
| Masculine plural endings -и/-і | PASS | Covered with студент/студенти, хлопець/хлопці |
| Feminine plural endings -и/-і replacing -а/-я | PASS | Covered with книга/книги, земля/землі |
| Neuter plural endings -а/-я replacing -о/-е | PASS | Covered with місто/міста, море/моря |
| Irregular plurals (діти, люди, очі) | PASS | All three shown in table |
| Vowel alternation і to о (кіт/коти, рік/роки) | PASS | Covered with table |
| Vowel alternation і to е (піч/печі, палець/пальці) | PARTIAL | піч/печі shown, but ніж/ножі used instead of палець/пальці. ніж/ножі is і to о, NOT і to е -- mislabeled in the content |
| **Consonant alternation preview (к to ц, г to з, х to с)** | **FAIL** | Completely absent from content. Plan explicitly includes this point. |
| Adjective plural -і/-ї | PASS | Covered with новий/нові, синій/сині |
| Hard vs soft adjective stems | PASS | Both demonstrated |
| Adjective-noun agreement in plural | PASS | Multiple examples |
| Uncountable nouns (молоко, цукор, вода) | PASS | Table present with повітря added |
| Plural-only nouns (гроші, двері, ножиці) | PASS | Table present |
| Stress shifts (рука to руки) | PASS | Example provided |
| **Summary table of endings by gender** | **FAIL** | Plan says "Provide a quick summary table" but summary section has only prose, no table |
| **Separate Практика section (250 words)** | **FAIL** | Plan has "Практика (Practice)" as a separate section with 250 words including drills, matching, reading exercises. Meta merged it into summary (150 words). Content has 4 self-check questions but no actual practice drills. |

**Objectives coverage:** 3/4 fully met, 1 partially met (vowel alternation demonstrated but consonant alternation missing).

## Linguistic Accuracy

All Ukrainian words verified via VESUM -- no ghost words found. Plural forms are correct:
- студенти, книги, міста, коти, діти, люди, очі, гроші, двері, ножиці -- all valid
- печі, ножі, роки, хлопці, землі, моря -- all valid

**Issues found:**

1. **CRITICAL: ніж/ножі mislabeled as і to е alternation.** Content line 75-80: ніж to ножі is presented under "the shift from і to е" but this is actually і to о alternation (ніж has і, ножі has о). The і to е examples should use піч/печі (correct, already there) and палець/пальці (from plan, missing).

2. **HIGH: Conjugated verbs used in Ukrainian examples despite M15 constraint.** Line 52: "Там грають діти" uses грають (грати, conjugated). Line 66: "Там сидять коти" uses сидять (сидіти, conjugated). Verb conjugation is explicitly FORBIDDEN before M15 per sequence constraints. These should be replaced with Це-type sentences (e.g., "Це діти" or "Це маленькі діти").

3. **MEDIUM: "pluralia tantum" terminology used without explanation.** Line 125: "These unique words are called pluralia tantum." This is Latin grammar terminology that an A1 beginner would not understand. The concept should be explained in plain English ("words that only exist in the plural form") without the Latin label.

## Pedagogical Quality

**Strengths:**
- Clear progressive structure: noun plurals by gender, then alternation, then adjectives, then special cases
- Good use of tables for each gender's pattern
- Examples before rules pattern followed
- English scaffolding is consistent and appropriate for A1

**Weaknesses:**
- No warm greeting or "today you'll learn" preview (jumps to "Welcome to the next big step")
- No celebration/encouragement at the end ("Look how far you've come!")
- The summary section is thin -- no summary table, no real practice drills, just 4 questions
- The "fleeting і" concept explanation (lines 59-61) is dense for A1: "When a syllable is closed, meaning it ends in a consonant, it very often contains the vowel і. When we add a plural ending, we add a brand new vowel to the word. This opens the syllable." This is abstract phonological reasoning that may overwhelm beginners.

**Lesson Arc:** WELCOME (weak) -> PRESENT (good) -> PRACTICE (weak) -> CELEBRATE (absent)

## Activities Quality

8 activities total: group-sort, match-up, fill-in, true-false, quiz, group-sort, unjumble, anagram.

**Issues:**

1. **CRITICAL: Unjumble activity has wrong schema.** Uses `sentence` field (string) instead of required `words` (array) + `answer` (string). This will fail schema validation. All 6 unjumble items are broken.

2. **HIGH: Activities use verbs forbidden at M13.** fill-in sentences use "Там є" (borderline OK as fixed expression) but unjumble sentence "Де твої великі міста?" uses interrogative structure not yet taught. Several fill-in items use "Де мої ___?" which implies question formation.

3. **MEDIUM: group-sort "Sort by Plural Ending" includes words not in vocabulary.** "машина", "зошит", "пісня", "лікар" appear in activities but some are not in the lesson content, potentially confusing beginners who haven't seen them.

4. **LOW: Anagram letter spacing inconsistency.** Some use single spaces ("о с т л и"), which is correct per schema.

**Activity type variety:** 6 different types (group-sort x2, match-up, fill-in, true-false, quiz, unjumble, anagram) -- good variety.

## Engagement

- 3 callout boxes: [!tip] (line 34), [!warning] (line 82), [!culture] (line 111) -- meets minimum
- Good use of tables throughout (6 tables in content)
- Ukrainian example sentences with translations provided

**Missing:**
- No [!did-you-know] box (only 3 types used, could be more varied)
- No encouragement phrases ("Great job!", "You've got this!")
- No progress markers ("You can now...")

## Vocabulary Quality

19 items in vocabulary YAML (target: 20). All are singular noun lemmas.

**CRITICAL gap:** The plan's 8 required vocabulary items include дитина (for діти), людина (for люди), гроші, двері. None of these appear in the vocabulary YAML. The vocabulary is entirely singular-form nouns useful for plural practice but misses the irregular/special items that are the module's distinguishing content.

**Missing required items:** дитина, людина, гроші, двері
**Missing recommended items:** око (for очі), ножиці, цукор, молоко

## Issues Found

| # | Severity | Category | Description |
|---|----------|----------|-------------|
| 1 | CRITICAL | Linguistic Accuracy | ніж/ножі mislabeled as і-to-е alternation (it is і-to-о). Misrepresents the grammatical rule. |
| 2 | CRITICAL | Schema | Unjumble activity uses `sentence` field instead of required `words` + `answer` fields. Will fail validation. |
| 3 | HIGH | Grammar Scope | Conjugated verbs грають (line 52) and сидять (line 66) used in examples despite verb conjugation being FORBIDDEN before M15. |
| 4 | HIGH | Plan Adherence | Consonant alternation preview (к to ц, г to з, х to с) completely missing from content. |
| 5 | HIGH | Vocabulary | 4 required plan vocabulary items (дитина, людина, гроші, двері) absent from vocabulary YAML. |
| 6 | MEDIUM | Plan Adherence | Summary table of plural endings by gender missing from summary section. |
| 7 | MEDIUM | Plan Adherence | Separate Практика section (250 words of drills) merged into thin summary, losing most practice content. |
| 8 | MEDIUM | Pedagogy | "pluralia tantum" Latin terminology used at A1 level without simplification. |
| 9 | LOW | Engagement | No encouragement phrases, no progress celebration, no warm closing. |

## Grade Justification

**Grade: C** -- The module is structurally adequate and covers most core content correctly, but has two CRITICAL issues (mislabeled alternation rule, broken unjumble schema), two HIGH grammar/plan issues (verbs in examples, missing consonant alternation), and significant vocabulary gaps. The content teaches plurals competently but the linguistic accuracy error (mislabeling і-to-о as і-to-е) directly undermines the module's core educational purpose. The broken unjumble activity means 1 of 8 activities will fail schema validation. These issues prevent a B grade.

**Not an F because:** Only 1 objective is partially missed (not >2), no Russianisms or ghost words found, lesson structure is logical, and 7 of 8 activities are schema-compliant.
