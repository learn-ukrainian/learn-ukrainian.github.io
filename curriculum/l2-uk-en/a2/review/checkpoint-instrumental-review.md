## Linguistic Scan
The verification tool flagged a few items not found in VESUM:
- Оксана, Тарас — Proper nouns (correct).
- ами, ими, іми — Adjective/noun endings extracted from text due to hyphenation (correct).
- конференц — Part of the compound word "конференц-залі" (correct).

However, I found one linguistic error in the text:
- "раковина" is a Russianism/calque when referring to a kitchen sink (in Ukrainian, it primarily means "shell"). The correct word for a kitchen sink is "мийка".

## Exercise Check
All 4 activity markers are present, matching the `activity_hints` in the plan exactly in type and focus. They are logically distributed throughout the module:
1. `<!-- INJECT_ACTIVITY: quiz-instrumental-mixed -->` (Placed after Part 1: forms and declensions)
2. `<!-- INJECT_ACTIVITY: fill-in-instrumental-transform -->` (Placed after Part 2: functions and verbs)
3. `<!-- INJECT_ACTIVITY: group-sort-functions -->` (Placed after Part 2)
4. `<!-- INJECT_ACTIVITY: error-correction-instrumental -->` (Placed after Part 3: free production and linguistic hygiene)

The outline's requirement for a writing prompt (Exercise 10) was excellently modeled with the reading text "Мій вівторок".

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The module failed to explicitly cite the textbook references specified in the plan (Захарійчук Grade 4, Заболотний Grade 5, Голуб Grade 6). Also missed one recommended vocabulary word. All other plan requirements (e.g., content outline sections) were strongly met. |
| 2. Linguistic accuracy | 9/10 | The grammar and phonetic explanations are flawless. However, the text used the Russianism "раковиною" for a kitchen sink instead of the correct Ukrainian term "мийкою" (`Білий рушник висить під раковиною.`). |
| 3. Pedagogical quality | 10/10 | Superb execution. The text expertly isolates learner pain points: `The most common mistake learners make is mixing up the tool function and the accompaniment function`. The anti-calque section (`Ми сміялися над ним` vs `Ми сміялися з нього`) is exactly what is needed for this level. |
| 4. Vocabulary coverage | 9/10 | All required vocabulary was embedded naturally. Only one recommended word (`визначити`) was missing from the text. |
| 5. Exercise quality | 10/10 | All markers are present, match the plan, and logically follow the teaching blocks they are meant to test. |
| 6. Engagement & tone | 10/10 | The tone is an encouraging teacher. Introductions to tasks like `Let us analyze a visual scene to prepare for your next завдання (task).` are natural and maintain the Ukrainian context. |
| 7. Structural integrity | 10/10 | Clean markdown, sections perfectly align with the plan. Word count is 2073, which safely exceeds the 1500-word target. |
| 8. Cultural accuracy | 10/10 | Excellent integration of linguistic hygiene, directly addressing and correcting common Russian interference patterns (`Я сумую по тобі` -> `Я сумую за тобою`). |
| 9. Dialogue & conversation quality | 10/10 | The dialogue (`Пам'ятаєш наш чудовий день у парку?`) feels natural and successfully showcases four different applications of the instrumental case in a short, realistic exchange. |

## Findings
[Linguistic accuracy] [critical]
Location: `> **Білий рушник висить під раковиною.**` and `spatial relations (**між вікнами**, **під раковиною**, **під обіднім столом**).`
Issue: The word "раковина" is a Russian calque when referring to a kitchen sink. The proper Ukrainian term in a kitchen context is "мийка".
Fix: Replace "раковиною" with "мийкою".

[Plan adherence] [major]
Location: Throughout the text.
Issue: The plan explicitly provided textbook references (Захарійчук, Заболотний, Голуб) which were not cited in the prose.
Fix: Integrate the textbook references naturally into the grammar explanation introductions.

[Vocabulary coverage] [minor]
Location: `You must **описати** (to describe) the scene using the instrumental case.`
Issue: The recommended vocabulary word "визначити" is missing from the module.
Fix: Weave the word into the task instruction.

## Verdict: REVISE
While the pedagogical quality and linguistic hygiene of this module are phenomenal, any factual/linguistic error forces a REVISE verdict. The use of "раковина" for a sink is a calque that must be fixed. The missing textbook references must also be integrated to adhere fully to the plan.

<fixes>
- find: "**Білий рушник висить під раковиною.** *(A white towel hangs under the sink.)*"
  replace: "**Білий рушник висить під мийкою.** *(A white towel hangs under the sink.)*"
- find: "із м'ясом**), and the spatial relations (**між вікнами**, **під раковиною**, **під обіднім столом**)."
  replace: "із м'ясом**), and the spatial relations (**між вікнами**, **під мийкою**, **під обіднім столом**)."
- find: "Let's review the basic noun endings. Words in the first and second declensions"
  replace: "Let's review the basic noun endings, as taught in Ukrainian school textbooks (Захарійчук Grade 4, Заболотний Grade 5). Words in the first and second declensions"
- find: "Personal pronouns also have specific forms. You must memorize these forms:"
  replace: "As noted in Голуб (Grade 6, p. 179), personal pronouns also have specific forms. You must memorize these forms:"
- find: "prepare for your next **завдання** (task). Imagine a busy kitchen. You must **описати** (to describe) the scene using the instrumental case."
  replace: "prepare for your next **завдання** (task). Imagine a busy kitchen. You must **визначити** (to identify) the objects and **описати** (to describe) the scene using the instrumental case."
</fixes>
