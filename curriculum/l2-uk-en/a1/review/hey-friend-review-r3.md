## Linguistic Scan
Linguistic scan revealed a phonetic terminology error: the text refers to the [ж] and [ч] consonants as "softened" when they are actually hard (тверді) in modern Ukrainian. No Russianisms, Surzhyk, or calques were found.

## Exercise Check
- `<!-- INJECT_ACTIVITY: quiz-vocative -->` placed correctly after general vocative intro.
- `<!-- INJECT_ACTIVITY: fill-in-vocative -->` placed correctly after explaining the rules.
- `<!-- INJECT_ACTIVITY: group-sort-vocative -->` placed correctly.
- `<!-- INJECT_ACTIVITY: quiz-choose-vocative -->` placed correctly at the end.
All markers match the plan's `activity_hints` count and pedagogical flow perfectly.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Failed to cite "State Standard 2024" and "Zabolotnyi Grade 4" as required by the plan references, and instead hallucinated "Avramenko's Grade 6" and "Litvinova Grade 6". |
| 2. Linguistic accuracy | 9/10 | Incorrectly stated "the back consonant softens before -е" for г→ж and к→ч. Phonetically, [ж] and [ч] are hard (тверді) consonants in Ukrainian. |
| 3. Pedagogical quality | 10/10 | Excellent pedagogical distinction: "Олена прийшла (talking ABOUT her) vs Олено, ходи сюди! (talking TO her)". |
| 4. Vocabulary coverage | 10/10 | Successfully integrated all required (друг, подруга, брат, сестра, пан, пані) and recommended words into the prose naturally. |
| 5. Exercise quality | 10/10 | 4 injected activity markers matching the plan precisely in sequence. |
| 6. Engagement & tone | 10/10 | Grounded tone: "It is roughly like saying 'Hey, him!' instead of 'Hey, you!' in English. Ukrainians immediately notice if you skip the vocative". |
| 7. Structural integrity | 10/10 | Section headers match plan, word count is 1265 (within the 10% tolerance for the 1200 target). |
| 8. Cultural accuracy | 10/10 | Authentic cultural context, correct use of patronymics and terms of address (пан/пані). |
| 9. Dialogue & conversation quality | 10/10 | Excellent, highly contextual multi-turn dialogue showing busy environments (birthday party, leaving house). |

## Findings

[1. Plan adherence] [MAJOR]
Location: Section "Кличний відмінок" and Section "Закінчення кличного"
Issue: The plan explicitly required citing "State Standard 2024, §4.2.3.4" and "Grade 4 textbook: Кличний відмінок (Заболотний)". The generated text omitted these references and instead hallucinated textbook citations not in the plan ("Avramenko's Grade 6", "Litvinova Grade 6").
Fix: Replace the hallucinated references with the ones specified in the plan.

[2. Linguistic accuracy] [CRITICAL]
Location: Section "Закінчення кличного", under "Masculine: soft consonant / -й → -ю" ("These follow standard Ukrainian phonetic patterns — the back consonant softens before -е.")
Issue: Phonetically, [ж] and [ч] are hard (тверді) consonants in modern Ukrainian. Calling this alternation "softening" is factually incorrect and teaches a wrong phonetic rule. This is a consonant mutation/alternation (the first palatalization).
Fix: Change "softens" to "mutates".

## Verdict: REVISE
The module is incredibly well-written, engaging, and pedagogically sound. However, the critical phonetic terminology error ("softening" into hard consonants) and the hallucinated textbook citations (failing to use the plan's required references) trigger the REVISE gate. Applying the provided fixes will correct these issues.

<fixes>
- find: "Ukrainian Grade 4 grammar uses a helpful shorthand:"
  replace: "The Grade 4 textbook by Zabolotnyi uses a helpful shorthand:"
- find: "As Avramenko's Grade 6 textbook notes, forms like"
  replace: "As the State Standard 2024 notes, forms like"
- find: "From Litvinova Grade 6: **пан Євге́н**"
  replace: "Following the standard pattern: **пан Євге́н**"
- find: "the back consonant softens before **-е**."
  replace: "the back consonant mutates before **-е**."
</fixes>
