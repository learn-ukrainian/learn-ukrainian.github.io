## Linguistic Scan
No linguistic errors found.

## Exercise Check
Four activity markers are present, match the four `activity_hints`, and are placed after the relevant teaching sections:
`quiz` after Scenario 1, `match-up` after Scenario 2, `fill-in` after Scenario 3, `error-correction` after the speaking task. They are spread through the module rather than clustered at the end. No exercise-placement issues found.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All four planned H2 sections are present, but Scenario 2 says `Ми орендуємо маленьку дерев'яну хатинку в лісі` instead of teaching the planned cabin-booking move, and the explicit motion contrast only names `їздити` / `поїхати`. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, bad case endings, or banned Russian letters found. Key forms used in the module are standard Ukrainian. |
| 3. Pedagogical quality | 7/10 | Scenario 1 has a strong scene→event→analysis flow, but Scenario 2 leaves `іти/ходити` and `летіти/літати` underexplained, and Scenario 3 analyzes `поїхали` although the model paragraph says `сіли у потяг`. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary is integrated naturally in prose: `подорож`, `квиток`, `потяг`, `вокзал`, `зупинитися`, `доїхати`, `сподобатися`, `враження`. Recommended connectors also appear. |
| 5. Exercise quality | 9/10 | Four markers are present and well placed: quiz after Scenario 1, match-up after Scenario 2, fill-in after Scenario 3, error-correction after the writing task. |
| 6. Engagement & tone | 9/10 | The tone is teacherly and concrete, with travel stories and usable examples rather than generic hype. |
| 7. Structural integrity | 10/10 | All planned sections are present and ordered correctly; pipeline word count is 2801, above the 2000 target. |
| 8. Cultural accuracy | 10/10 | The module uses Ukrainian places and travel contexts (`Карпати`, `Львів`, `Одеса`) on Ukrainian terms, with no Russia-centered framing. |
| 9. Dialogue & conversation quality | 7/10 | Speakers are named, but Scenario 3 is mostly one speaker asking and the other answering (`Де ти була?`, `Як ви доїхали?`, `Що ви там бачили?`), so it reads more like an oral exam than a shared conversation. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `> — **Олена:** Я вже знайшла гарне місце для нас. Ми орендуємо маленьку дерев'яну хатинку в лісі.`  
Issue: The plan’s Scenario 2 explicitly includes “booking хатинка”. The section includes a cabin, but no booking language appears.  
Fix: Make Olena say she has already booked the cabin.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `This contrasts with our regular habits. When we describe repeated trips, we use imperfective verbs of motion like **їздити**... The perfective verb **поїхати** focuses on one specific departure.`  
Issue: This is the only explicit contrast paragraph, and it teaches only `їздити/поїхати`. The planned `іти/ходити` and `летіти/літати` contrasts are not actually taught as contrasts.  
Fix: Expand this paragraph to include all three motion-verb pairs with short examples.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `Минулого тижня я їздив до Одеси на відпочинок. Спочатку ми сіли у потяг. Ми змогли **доїхати**...` and later `Then, the perfective verbs **поїхали** and **доїхали** describe...`  
Issue: The analysis claims the model story contains `поїхали`, but the story itself does not. That weakens the form-to-example mapping.  
Fix: Change the model story so it actually uses `поїхали` and `доїхали`.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: `> — **Максим:** Що тобі найбільше сподобалося?` / `> — **Олена:** Мені дуже сподобалася архітектура міста.`  
Issue: Scenario 3 stays as straight interview Q/A. The plan frames this situation as showing vacation photos from Odesa, but the dialogue never actually does that and gives Maxim no meaningful response turn.  
Fix: Expand Olena’s answer to point to the photos and add a short Maxim reaction.

## Verdict: REVISE
No linguistic blockers, but there are four major plan/pedagogy/dialogue issues, and dimensions 1, 3, and 9 fall below 9.

<fixes>
- find: "> — **Олена:** Я вже знайшла гарне місце для нас. Ми орендуємо маленьку дерев'яну хатинку в лісі. *(I have already found a nice place for us. We will rent a small wooden cabin in the forest.)*"
  replace: "> — **Олена:** Я вже знайшла гарне місце для нас і забронювала маленьку дерев'яну хатинку в лісі. *(I have already found a nice place for us and booked a small wooden cabin in the forest.)*"
- find: "This contrasts with our regular habits. When we describe repeated trips, we use imperfective verbs of motion like **їздити** (to go by vehicle). For example: «Зазвичай ми їздимо туди щоліта» (Usually we go there every summer). The perfective verb **поїхати** focuses on one specific departure."
  replace: "This contrasts with our regular habits. When we describe repeated movement, we use imperfective verbs of motion such as **їздити**, **ходити**, and **літати**. For example: «Зазвичай ми їздимо туди щоліта», «У горах ми щодня ходимо до лісу», «Щоліта ми літаємо на море». For one specific departure, we switch to perfective forms such as **поїхати**, **піти**, or **полетіти**."
- find: "Минулого тижня я їздив до Одеси на відпочинок. Спочатку ми сіли у потяг. Ми змогли **доїхати** (to reach) туди за десять годин."
  replace: "Минулого тижня я їздив до Одеси на відпочинок. Спочатку ми поїхали потягом і **доїхали** (to reach) туди за десять годин."
- find: |
    > — **Максим:** Що тобі найбільше сподобалося? *(What did you like the most?)*
    > — **Олена:** Мені дуже сподобалася архітектура міста. *(I really liked the architecture of the city.)*
  replace: |
    > — **Максим:** Що тобі найбільше сподобалося? *(What did you like the most?)*
    > — **Олена:** Мені дуже сподобалася архітектура міста. Ось фото з пляжу, моря і ресторану. *(I really liked the architecture of the city. Here are photos from the beach, the sea, and the restaurant.)*
    > — **Максим:** Клас! Тепер я теж хочу поїхати до Одеси. *(Cool! Now I want to go to Odesa too.)*
</fixes>