## Linguistic Scan
No linguistic errors found.

## Exercise Check
All four expected activity markers are present and placed after the relevant teaching blocks: `quiz-preposition-identification` after Part 1, `fill-in-genitive-agreement` and `error-correction-genitive` after Part 2, and `match-up-situations` after Part 3. The marker types match the plan’s `activity_hints`, and they are spread through the module rather than clustered at the end. No visible inline-exercise logic errors in the prose itself.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | The plan is preposition-centered, but Part 2 shifts to non-prepositional genitive in `Я потребую допомоги` and `У мене немає сестри`. Part 3 also omits the planned `Dialogue completion` and `Translation challenge`, and its local heading-based length is only about 411 words vs. the planned 550. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, paronym errors, or wrong case forms found. Tricky claims were supportable: `від` with time is attested in СУМ-11, and forms like `морів`, `дітей`, `людей` are confirmed in VESUM. |
| 3. Pedagogical quality | 8/10 | Parts 1-2 give many examples and move from recognition to patterning, but the paragraph beginning `To виправити...` teaches extra governance patterns outside the checkpoint brief, which weakens review focus. |
| 4. Vocabulary coverage | 10/10 | All required vocabulary appears naturally in prose: `родовий відмінок`, `прийменник`, `узгодження`, `множина`, `однина`, `закінчення`, `перевірка`, `помилка`. Recommended `виправити`, `впізнати`, and `вибрати` also appear. |
| 5. Exercise quality | 10/10 | Marker inventory matches the four planned activity types exactly, and each marker comes after the relevant teaching section. No visible exercise-logic problems in the prose. |
| 6. Engagement & tone | 9/10 | The voice is teacherly and generally substantive, with concrete contexts like Kyiv landmarks, the market, and directions. |
| 7. Structural integrity | 8/10 | All required H2 sections are present and the pipeline word count is 1674, but section pacing is uneven: local heading-based counts are about 535 / 541 / 411 against the planned 450 / 500 / 550. |
| 8. Cultural accuracy | 10/10 | The module stays Ukrainian-centered, with examples such as `Софійського собору` and `Хрещатика`, and avoids Russian-comparison framing. |
| 9. Dialogue & conversation quality | 8/10 | The tour-guide and market dialogues are functional and multi-turn, but the pharmacy closing `бо я бачу, що у вас немає настрою` sounds stilted for an `Аптекар`. |

## Findings
[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: Part 2, paragraph beginning `To **виправити** (to correct) your own speech...`  
Issue: The checkpoint plan is about genitive after studied prepositions, agreement, and plural, but this paragraph switches to non-prepositional genitive with `Я потребую допомоги` and `У мене немає сестри`. That broadens scope beyond the stated review target.  
Fix: Replace the paragraph with error patterns tied to this checkpoint only: preposition + noun form, adjective/pronoun agreement, and genitive plural after numbers.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: Part 3, after `Practice these patterns out loud. The genitive case should feel like a rhythm, naturally following the prepositions that trigger it.`  
Issue: The plan explicitly requires `Dialogue completion` and `Translation challenge` in Part 3, but the section contains examples plus `<!-- INJECT_ACTIVITY: match-up-situations -->` only. This also leaves Part 3 underbuilt relative to its 550-word budget.  
Fix: Insert a short production block with sentence building, dialogue completion, and translation prompts before the match-up marker.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: minor]  
Location: Part 3 pharmacy dialogue: `І відпочивайте, бо я бачу, що у вас **немає настрою** (you have no mood).`  
Issue: This line sounds unnatural for an `Аптекар` and weakens the dialogue’s realism.  
Fix: Replace it with a simpler natural closing, e.g. `І відпочивайте.`

## Verdict: REVISE
The module is linguistically clean, but it does not fully adhere to the plan: Part 2 drifts beyond the checkpoint scope, and Part 3 is missing two planned free-production elements. Those are fixable with targeted edits, so this is a revision, not a rebuild.

<fixes>
- find: |-
    To **виправити** (to correct) your own speech, watch out for the most common L2 errors. First, never translate English sentence structure directly. "I need help" translates to `Я потребую допомоги` (genitive), not `Я потребую допомогу`. Second, remember that the genitive is very common in negative constructions with words like `немає`: "I don't have a sister" is `У мене немає сестри`, never `У мене немає сестра`. Finally, remember the number rule: numbers 5 and above require the genitive plural. "Five books" is `п'ять книжок`, never `п'ять книга`.
  replace: |-
    To **виправити** (to correct) your own speech, watch out for the most common review errors from this checkpoint. First, keep the preposition and the noun form together: `до магазину`, not `до магазин`. Second, make the whole phrase agree in the genitive: `для моєї сестри`, not `для моя сестра`. Finally, remember the number rule: numbers 5 and above require the genitive plural. "Five books" is `п'ять книжок`, never `п'ять книга`.
- insert_after: |-
    Practice these patterns out loud. The genitive case should feel like a rhythm, naturally following the prepositions that trigger it.
  content: |-
    Try three final production tasks before you move on.
    *   **Sentence building:** Write one sentence about the market, one about directions, and one about your daily routine using `без`, `до`, and `після`.
    *   **Dialogue completion:** Complete this mini-dialogue: `— Перепрошую, як дійти ... ?` `— Ідіть прямо, аптека знаходиться ... банку.`
    *   **Translation challenge:** Translate these into Ukrainian: `We are going to the doctor after work.` `This tea is for my old friend.` `There is no sugar near the coffee machine.`
- find: |-
    > **Аптекар**: Ні, просто пийте їх **після обіду** (after lunch). І відпочивайте, бо я бачу, що у вас **немає настрою** (you have no mood).
  replace: |-
    > **Аптекар**: Ні, просто пийте їх **після обіду** (after lunch). І відпочивайте.
</fixes>