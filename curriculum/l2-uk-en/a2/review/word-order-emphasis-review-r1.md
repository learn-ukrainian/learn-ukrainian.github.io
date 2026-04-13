## Linguistic Scan
No Russianisms, Surzhyk, calques, paronym errors, or banned Russian characters found.

- Factual grammar error: “У прямому порядку прикметник завжди стоїть перед іменником.” This is too absolute for Ukrainian.
- Factual grammar error: “Це означає, що прикметник виконує роль дієслова.” In `Світанок тихий`, `тихий` is a predicative adjective / part of the predicate, not a verb.
- Factual grammar error: “Ця маленька граматична частка показує, де знаходиться головна **тема**...” In `Це Тарас допоміг мені`, the highlighted element is rheme/focus, not theme.

## Exercise Check
5 markers found, matching all 5 `activity_hints`: `quiz-identify-rheme`, `group-sort-neutral-emphatic`, `fill-in-reorder-emphasis`, `match-up-questions-answers`, `error-correction-unintended-emphasis`.

All markers appear after the relevant teaching section. The last two are both at the end, but both test the final question-answer/emphasis material, so placement is still acceptable. No exercise-logic issues are visible at marker level.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All four planned H2 sections and all five activity markers are present, but the prose never cites the plan references (`Заболотний`, `Авраменко`, `ULP` all 0 hits in search), and the `Це Тарас допоміг мені` explanation contradicts the plan point that `Це + noun identifies the rheme explicitly`. |
| 2. Linguistic accuracy | 6/10 | Critical grammar-teaching problems: `У прямому порядку прикметник завжди стоїть перед іменником`, `Це означає, що прикметник виконує роль дієслова`, and `головна тема` in the `Це Тарас допоміг мені` explanation. |
| 3. Pedagogical quality | 7/10 | The module has strong sequencing and many examples, but several rules are taught too absolutely, and the gloss `literally: "The book bought Taras"` is misleading in a lesson that is supposed to clarify case roles. |
| 4. Vocabulary coverage | 9/10 | All required plan vocabulary is used naturally in prose: `порядок, речення, тема, рема, наголос, інверсія, контраст, підкреслювати, початок, кінець`. |
| 5. Exercise quality | 9/10 | Marker inventory matches the plan exactly, and each marker follows the concept it is meant to test. |
| 6. Engagement & tone | 9/10 | Teacherly and substantive, with concrete situations like chores and film discussion rather than filler or gamified language. |
| 7. Structural integrity | 10/10 | Clean markdown, all planned sections present and ordered correctly, and deterministic total word count is 2887, above target. |
| 8. Cultural accuracy | 10/10 | The module explains Ukrainian on its own terms through case and information structure, with no Russian-centered framing. |
| 9. Dialogue & conversation quality | 9/10 | Named speakers, multi-turn exchanges, and context-driven answers support the lesson goal well. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: Neutral Word Order section — “У прямому порядку прикметник завжди стоїть перед іменником.” / “Це означає, що прикметник виконує роль дієслова.”  
Issue: The explanation turns a default pattern into an absolute rule and then misdescribes the postposed adjective as if it becomes a verb.  
Fix: Change `завжди` to `зазвичай`, and explain that `світанок тихий` is read as a sentence where the adjective is part of the predicate, not “a verb”.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: Fronting for Contrast section — “Ця маленька граматична частка показує, де знаходиться головна **тема** (theme) вашої розповіді.”  
Issue: In `Це Тарас допоміг мені`, `Тарас` is the highlighted new information/focus, i.e. rheme, not theme.  
Fix: Replace `тема` with `рема` / `фокус висловлювання`.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: Theme and Rheme section — `Therefore, we say: "The book was bought by Taras" (literally: "The book bought Taras").`  
Issue: The literal gloss is wrong and undermines the immediately following explanation about case endings showing grammatical roles.  
Fix: Remove the faulty literal gloss or replace it with a word-order gloss such as `The book, Taras bought`.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: Whole module; search check found no occurrences of `Заболотний`, `Авраменко`, or `ULP` in the prose.  
Issue: The plan includes three references, but none are integrated or cited anywhere in the lesson text.  
Fix: Add one short source note tying the explanation to Заболотний §10-12, Авраменко §6-7, and Ukrainian Lessons Project.

## Verdict: REVISE
Multiple critical findings teach incorrect grammar analysis, so this cannot ship as-is even though the structure, tone, and exercise placement are solid.

<fixes>
- find: |
    У прямому порядку прикметник завжди стоїть перед іменником. Ми кажемо «нова книга» або «тихий світанок». Прислівники можуть стояти перед дієсловом або після нього. Фрази «він добре працює» та «він працює добре» є правильними. Обидва варіанти звучать природно і майже не змінюють зміст.
  replace: |
    У прямому порядку прикметник зазвичай стоїть перед іменником. Ми кажемо «нова книга» або «тихий світанок». Прислівники можуть стояти перед дієсловом або після нього. Фрази «він добре працює» та «він працює добре» є правильними. Обидва варіанти звучать природно, але порядок слів може трохи зміщувати акцент.
- find: |
    Позиція прикметника є дуже важливою. Фраза «тихий світанок» — це просто іменник з означенням. Але якщо ви скажете «світанок тихий», ви створите повне речення. Тут слово «світанок» є підметом, а слово «тихий» стає присудком. Це означає, що прикметник виконує роль дієслова.
  replace: |
    Позиція прикметника є дуже важливою. Фраза «тихий світанок» — це іменник з означенням. А «світанок тихий» у звичайному контексті вже сприймається як речення: слово «світанок» є підметом, а слово «тихий» входить до складу присудка. Це не означає, що прикметник стає дієсловом, але він уже не просто означення.
- find: |
    Remember that Ukrainian often omits the present tense verb "to be" (є). Because of this, an adjective placed *after* a noun («Книга цікава») acts as the verb ("The book *is* interesting"). An adjective placed *before* a noun («Цікава книга») is just a modifier ("An interesting book").
  replace: |
    Remember that Ukrainian often omits the present tense verb "to be" (є). Because of this, an adjective placed *after* a noun («Книга цікава») functions as part of the predicate ("The book *is* interesting). An adjective placed *before* a noun («Цікава книга») is just a modifier ("An interesting book").
- find: |
    Therefore, we say: "The book was bought by Taras" (literally: "The book bought Taras").
  replace: |
    Therefore, we say: "The book was bought by Taras".
- find: |
    Слово «це» допомагає нам чітко виділити головну дійову особу. Ви ставите слово «це» на перше місце, щоб показати автора дії. Наприклад: «Це Тарас допоміг мені». Це означає, що саме він вчасно запропонував допомогу. Ця маленька граматична частка показує, де знаходиться головна **тема** (theme) вашої розповіді.
  replace: |
    Слово «це» допомагає нам чітко виділити головну дійову особу. Ви ставите слово «це» на перше місце, щоб показати автора дії. Наприклад: «Це Тарас допоміг мені». Це означає, що саме він вчасно запропонував допомогу. Ця маленька граматична частка допомагає явно виділити головну **рему** (rheme) або фокус висловлювання.
- find: |
    Завжди уважно слухайте питання співрозмовника. Питання допомагає побудувати правильну та природну відповідь. З часом ви почнете відчувати мелодику мови.
  replace: |
    Завжди уважно слухайте питання співрозмовника. Питання допомагає побудувати правильну та природну відповідь. З часом ви почнете відчувати мелодику мови. Якщо хочете побачити шкільне формулювання теми, порівняйте пояснення в Заболотного (§10-12), Авраменка (§6-7) і короткий огляд Ukrainian Lessons Project про Ukrainian word order.
</fixes>