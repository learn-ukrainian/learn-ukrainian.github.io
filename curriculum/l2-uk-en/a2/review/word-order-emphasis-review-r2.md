## Linguistic Scan
No linguistic errors found.

## Exercise Check
Five activity markers are present and placed after the relevant teaching blocks.

- `quiz-identify-rheme` follows the theme/rheme section.
- `group-sort-neutral-emphatic` follows the neutral word order section.
- `fill-in-reorder-emphasis` follows the inversion section.
- `match-up-questions-answers` and `error-correction-unintended-emphasis` follow the real-speech section.

Marker coverage matches all five `activity_hints`. No inline DSL exercises are present in the supplied content, so there is no exercise logic to audit beyond placement.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All four planned H2 sections appear in order, and the references are cited in the closing paragraph, but the plan point “Reading practice: identifying word order shifts in a short Ukrainian text...” is not realized before the final activity markers. |
| 2. Linguistic accuracy | 8/10 | No Russianisms/Surzhyk/Russian letters found, and spot-checked Ukrainian forms verify cleanly; however, the cleft explanation contradicts itself by saying `головну **рему**` in Ukrainian and `main theme` in the English gloss. |
| 3. Pedagogical quality | 7/10 | The question→answer modeling is strong, but the `це` explanation reduces focus marking to “author of the action,” and `Якщо ви відповісте «Каву купив я», це звучатиме вкрай дивно` overstates a marked-but-valid contrastive order instead of teaching when it is appropriate. |
| 4. Vocabulary coverage | 8/10 | Required vocabulary is well integrated, but recommended `виділяти` and `емфатичний` do not appear in the supplied prose (search hits: 0). |
| 5. Exercise quality | 9/10 | All five planned activity types are represented by correctly placed markers, and each comes after the concept it should test. |
| 6. Engagement & tone | 9/10 | The tone is teacherly and concrete; the chores dialogue and question-based framing keep the lesson lively without fluff. |
| 7. Structural integrity | 10/10 | All four H2 headings are present and ordered correctly; markdown is clean; total pipeline word count is 2914, above target. |
| 8. Cultural accuracy | 10/10 | The module is Ukrainian-centered throughout and avoids Russia-centered comparison framing. |
| 9. Dialogue & conversation quality | 8/10 | The chores dialogue is natural and useful, but `А от «Номери» — це точно Сенцов зняв` sounds stilted and blurs the contrast pattern being taught. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Порядок слів у реальному мовленні`, closing paragraph: `Завжди уважно слухайте питання співрозмовника...` followed immediately by activity markers.  
Issue: The plan explicitly requires reading practice with a short Ukrainian text and explanation of word-order choices, but the module ends without that component.  
Fix: Insert a short connected text plus a prompt explaining why specific words are fronted or sentence-final.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `## Інверсія для контрасту`, cleft paragraph: `Ця маленька граматична частка допомагає явно виділити головну **рему**...` / English gloss: `This small grammatical particle shows where the main theme of your story is.`  
Issue: The English gloss reverses the key concept. `Theme` is not the same as `rheme`, so the bilingual explanation teaches inconsistent information structure terminology.  
Fix: Replace the paragraph so both languages consistently describe `це` as marking focus/rheme.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `## Інверсія для контрасту`, paragraph beginning `Слово «це» допомагає нам чітко виділити...`  
Issue: The explanation narrows the construction to “the author of the action,” but the module’s own plan defines it more broadly as a cleft-like focus pattern.  
Fix: Rephrase it to say `це` highlights whichever element is in focus, not only an agent.

[VOCABULARY COVERAGE] [SEVERITY: major]  
Location: same cleft paragraph.  
Issue: Recommended vocabulary from the plan, specifically `виділяти` and `емфатичний`, is missing from the prose.  
Fix: Revise this paragraph to introduce those terms naturally while explaining focus marking.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `## Порядок слів у реальному мовленні`, paragraph: `Якщо ви відповісте «Каву купив я», це звучатиме вкрай дивно.`  
Issue: This is too absolute. `Каву купив я` is strongly contrastive, not inherently “extremely strange”; the learner needs a context rule, not a blanket prohibition.  
Fix: Change the wording to explain that the order is appropriate in explicit contrast and give a brief example.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: movie dialogue: `А от «Номери» — це точно Сенцов зняв.`  
Issue: The line sounds stilted and weakens the very word-order pattern the section is trying to model.  
Fix: Rewrite it as a more natural contrastive sentence with the focused name in final position.

## Verdict: REVISE
REVISE. The module is structurally complete and linguistically clean in Ukrainian, but it contains one critical concept mismatch in the bilingual explanation plus several major plan/pedagogy/dialogue issues. These should be fixed before shipping.

<fixes>
- find: |
    > — **Антон:** Можливо. А от «Номери» — це точно Сенцов зняв. *(Maybe. But "Numbers" — Sentsov definitely directed that.)*
  replace: |
    > — **Антон:** Можливо. А от «Номери» точно зняв Сенцов. *(Maybe. But "Numbers" was definitely directed by Sentsov.)*

- find: |
    Слово «це» допомагає нам чітко виділити головну дійову особу. Ви ставите слово «це» на перше місце, щоб показати автора дії. Наприклад: «Це Тарас допоміг мені». Це означає, що саме він вчасно запропонував допомогу. Ця маленька граматична частка допомагає явно виділити головну **рему** (rheme) або фокус висловлювання.

    > *The word "це" helps us clearly highlight the main character. You put the word "це" in the first place to show the author of the action. For example: "It was Taras who helped me." This means that exactly he offered help in time. This small grammatical particle shows where the main theme of your story is.*
  replace: |
    Слово «це» допомагає нам чітко **виділяти** той елемент речення, на якому ми хочемо зосередити увагу. Ви ставите «це» на перше місце, щоб показати, що саме цей елемент є фокусом висловлювання. Наприклад: «Це Тарас допоміг мені». Це **емфатичний** спосіб виділити головну **рему** (rheme) у реченні.

    > *The word "це" helps us clearly highlight the element we want to focus on. You put "це" in the first position to show that this element is the focus of the utterance. For example: "It was Taras who helped me." This is an emphatic way to mark the main rheme of the sentence.*

- find: |
    Українська мова дуже гнучка, але не перекладайте англійські фрази механічно. Неправильний порядок слів може створити сильний і небажаний **контраст** (contrast). Якщо ви відповісте «Каву купив я», це звучатиме вкрай дивно. Такий **наголос** (stress, emphasis) означає: «Саме я купив цю каву». Співрозмовник може подумати, що ви сперечаєтеся з ним. Ви не повинні **підкреслювати** (to emphasize, to underline) слово «я» без причини.
  replace: |
    Українська мова дуже гнучка, але не перекладайте англійські фрази механічно. Неправильний порядок слів може створити сильний і небажаний **контраст** (contrast). Якщо ви відповісте «Каву купив я», це звучатиме дуже контрастно. Такий **наголос** (stress, emphasis) доречний, коли ви справді протиставляєте себе комусь іншому: «Каву купив я, а чай — Олег». Без такого контексту співрозмовник може подумати, що ви сперечаєтеся з ним. Не варто **підкреслювати** (to emphasize, to underline) слово «я» без причини.

- insert_after: |
    Завжди уважно слухайте питання співрозмовника. Питання допомагає побудувати правильну та природну відповідь. З часом ви почнете відчувати мелодику мови. Якщо хочете побачити шкільне формулювання теми, порівняйте пояснення в Заболотного (§10-12), Авраменка (§6-7) і короткий огляд Ukrainian Lessons Project про Ukrainian word order.
  content: |
    One final reading task helps turn this idea into a real-text skill. Read the short passage and explain why the highlighted words stand where they do.

    Ось короткий текст для читання: «На столі лежала книжка. Книжку взяла Марійка. Увечері цю книжку прочитав брат». Поясніть, чому в другому реченні слово «книжку» стоїть на початку, а в третьому реченні слово «брат» стоїть в кінці. Так ви побачите, як порядок слів працює в маленькому зв'язному тексті, а не лише в окремих відповідях.

    > *Here is a short reading text: "A book was lying on the table. Maryka took the book. In the evening, her brother read this book." Explain why the word "book" stands at the beginning in the second sentence and why the word "brother" stands at the end in the third sentence. This helps you see how word order works in a small connected text, not only in isolated answers.*
</fixes>