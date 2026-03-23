  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=26482 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
## Linguistic Scan
No linguistic errors found other than one phonetic explanation error: the word "фотографія" is explained as having stress on the "third а" but the syllable "ФІ" is highlighted. The correct standard Ukrainian stress is on the syllable "ГРА" (фотогра́фія).

## Exercise Check
- `:::quiz` "Де наголос? (Where is the stress?)": 8 items. Matches plan (8 items). Tests phonetic stress concepts taught in the section.
- `:::match-up` "Match the stress pairs": 4 items. Matches plan (4 items). Tests the meaning-changing nature of stress.
- `:::quiz` "Розповідне, питальне чи окличне?": 6 items. Matches plan (6 items). Tests sentence types based on punctuation and intonation rules.
- `:::fill-in` "Add the correct punctuation": 6 items. Matches plan (6 items). Tests practical application of intonation to punctuation.
All exercises are well-formed, logically sound, and perfectly aligned with the plan's `activity_hints`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All outline points are covered (Заболотний reference, 3 intonation patterns, goroh.pp.ua tip). However, the word count is noticeably under the 1200-word target (estimated ~850 words). |
| 2. Linguistic accuracy | 8/10 | Ukrainian examples are natural and accurate. No Russianisms or Surzhyk. However, the explanation for the stress in "фотографія" is contradictory and highlights the wrong syllable. |
| 3. Pedagogical quality | 10/10 | Excellent application of PPP. Concepts are explained simply without overwhelming metalanguage. The progression from syllable stress to sentence intonation is logical. |
| 4. Vocabulary coverage | 10/10 | All required (наголос, замок, кава, вода, столиця) and recommended (мука, ранок, метро, фотографія) words are integrated naturally into the prose and examples. |
| 5. Exercise quality | 10/10 | Exercises directly test the taught concepts. Distractors in the quizzes are plausible. The match-up effectively tests the semantic difference caused by stress. |
| 6. Engagement & tone | 9/10 | The tone is encouraging, authoritative, and direct. Good use of the "coffee cup" scenario to explain intonation. |
| 7. Structural integrity | 9/10 | Clean markdown, correct H2 headers following the plan. No LLM meta-commentary. Word count is the only structural minor deficiency. |
| 8. Cultural accuracy | 10/10 | Accurate representation of Ukrainian phonetic rules. Focus on Ukrainian as a distinct language with its own free stress system. |
| 9. Dialogue & conversation quality | 10/10 | The short greeting dialogue is perfectly calibrated for A1.1, reusing known vocabulary to teach a new phonetic concept. |

## Findings
[Linguistic accuracy] [major]
Location: "фо-то-гра-фі-я — stress on the third а: фо-то-гра-ФІ-я (photograph)"
Issue: The explanation is contradictory (says "stress on the third а" but highlights "ФІ" which contains 'і'). Furthermore, the standard Ukrainian stress for photograph is on the syllable "ГРА" (фотогра́фія).
Fix: Change the explanation to highlight "ГРА" and mention stress on "а".

[Plan adherence] [minor]
Location: Entire module
Issue: The total word count is approximately 850 words, missing the 1200 word target.
Fix: For A1, brevity is often preferred to avoid overwhelming the learner, so this is a minor issue. An `insert_after` block could be used to expand the text, but a find/replace fix for the major linguistic issue is sufficient for a REVISE verdict.

## Verdict: REVISE
The module is structurally excellent, pedagogically sound, and the exercises are perfect. However, the contradictory and factually incorrect explanation of the stress in "фотографія" is a major linguistic error that might confuse learners. It must be fixed before shipping.

<fixes>
- find: "фо-то-гра-фі-я — stress on the third а: фо-то-гра-ФІ-я (photograph)"
  replace: "фо-то-гра-фі-я — stress on **а**: фо-то-ГРА-фі-я (photograph)"
</fixes>
