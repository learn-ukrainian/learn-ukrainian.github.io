## Linguistic Scan
- Errors found:
  1. **Russianism/Calque**: The phrase "Давайте" + verb is repeatedly used for imperatives (Давайте згадаємо, Давайте розглянемо, Давайте послухаємо). This is a calque of Russian. The normative Ukrainian synthetic imperative should be used instead (Згадаймо, Розгляньмо, Послухаймо).
  2. **Spelling**: "інфінитива" is misspelled. The correct form is "інфінітива".

## Exercise Check
- Marker `<!-- INJECT_ACTIVITY: fill-in-mixed-cases -->` (matches plan hint: fill-in). Placement is correct.
- Marker `<!-- INJECT_ACTIVITY: quiz-aspect-choice -->` (matches plan hint: quiz). Placement is correct.
- Marker `<!-- INJECT_ACTIVITY: group-sort-grammar-categories -->` (matches plan hint: group-sort). Placement is correct.
- Marker `<!-- INJECT_ACTIVITY: error-correction -->` (matches plan hint: error-correction). Placement is correct.
- Marker `<!-- INJECT_ACTIVITY: error-correction-final-review -->` is **HALLUCINATED**. The plan only provides 4 activity hints; the writer injected 5 markers.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | Missed plan dialogue requirements: Dialogue 1 didn't quiz cases/conjunctions. Dialogue 2 used Teacher/Student instead of Student/Classmate. Hallucinated a 5th exercise marker. Missed specific module recommendations in "Self-Assessment": `Якщо ні, варто зробити **повторення** (review). If not, it is worth doing a review.` |
| 2. Linguistic accuracy | 7/10 | Used Russianism/calque "Давайте" + verb 6 times. Misspelled `до інфінитива` (correct: `інфінітива`). |
| 3. Pedagogical quality | 8/10 | Solid grammar overview, but Dialogue 1 characters explaining English metalanguage ("The word 'дієслово' means 'verb'") is poor pedagogy that breaks immersion. |
| 4. Vocabulary coverage | 10/10 | Covered required and recommended vocabulary naturally, embedding terms perfectly in context. |
| 5. Exercise quality | 8/10 | Injected markers for planned exercises, but hallucinated an extra marker not in the plan. |
| 6. Engagement & tone | 7/10 | Good teacher tone overall, but Dialogue 1 was extremely robotic and stilted. |
| 7. Structural integrity | 9/10 | Left an artifact in the first heading: `## Відмінки: від називного до кличного (~550 words total)`. Word count met. |
| 8. Cultural accuracy | 10/10 | Accurate and decolonized presentation of Ukrainian grammar. |
| 9. Dialogue & conversation quality | 4/10 | Dialogue 1 was pure robotic translation delivery. Dialogue 2 completely ignored the prompt's character requirements and scenario. |

## Findings
[1. Plan adherence] [MAJOR]
Location: `## Дієслово: вид, час, спосіб` (Dialogue 1)
Issue: Dialogue 1 characters only discuss aspect, ignoring cases and conjunctions required by the plan ("quizzing each other on cases, aspect, and conjunctions").
Fix: Rewrite dialogue to include cases and conjunctions.

[1. Plan adherence] [MAJOR]
Location: `## Складне речення: з'єднуємо думки` (Dialogue 2)
Issue: Dialogue 2 features a Teacher and Student ("Вчителька: Марку..."), violating the plan's instruction for "A student explaining to a new classmate".
Fix: Change "Вчителька" to "Анна" (a new classmate) and adjust lines to match the scenario.

[1. Plan adherence] [MAJOR]
Location: `Якщо ваша оцінка висока — це чудовий результат. If your score is high — this is an excellent result. Якщо ні, варто зробити **повторення** (review). If not, it is worth doing a review.`
Issue: Failed to specify "which A2 modules to revisit before starting B1" as explicitly requested by the plan.
Fix: Add concrete module recommendations: "Поверніться до модулів M48-M54 для повторення відмінків, або до M30-M35 для повторення дієслів руху. Return to modules M48-M54 to review cases, or to M30-M35 to review verbs of motion."

[2. Linguistic accuracy] [CRITICAL]
Location: Multiple occurrences across text (e.g., `Давайте згадаємо їхні головні ролі.`)
Issue: "Давайте" + verb is a known Russianism/calque for imperatives.
Fix: Use the normative synthetic imperative ("Згадаймо", "Розгляньмо", "Проведімо", "Послухаймо", "Коротко згадаймо").

[2. Linguistic accuracy] [CRITICAL]
Location: `Ми додаємо закінчення прямо до інфінитива.`
Issue: Spelling error. The genitive of "інфінітив" is "інфінітива", not "інфінитива".
Fix: Change "до інфінитива" to "до інфінітива".

[5. Exercise quality] [MAJOR]
Location: `<!-- INJECT_ACTIVITY: error-correction-final-review -->`
Issue: Hallucinated a 5th activity marker that doesn't exist in the plan's `activity_hints` array (which only has 4 items).
Fix: Remove the marker.

[7. Structural integrity] [MINOR]
Location: `## Відмінки: від називного до кличного (~550 words total)`
Issue: The writer left a prompt word count artifact (`~550 words total`) in the H2 heading.
Fix: Remove the word count artifact from the heading.

[9. Dialogue & conversation quality] [MAJOR]
Location: `> — **Олена:** Максиме, ти готовий до тесту на рівень B1? Are you ready for the B1 level test?`
Issue: Characters explicitly speak English metalanguage translations to each other ("The word 'дієслово' means 'verb'"), which is robotic and breaks immersion. Inconsistent translation formatting (inline vs parens).
Fix: Rewrite dialogue to be natural, placing English translations in italics inside parentheses.

## Verdict: REVISE
The module contains critical linguistic errors (Russianism "давайте", misspelled "інфінітива"), hallucinated activity markers, prompt artifacts in headings, and robotic dialogues that violate the plan's character constraints. These issues require targeted fixes before publication.

<fixes>
- find: "## Відмінки: від називного до кличного (~550 words total)"
  replace: "## Відмінки: від називного до кличного"
- find: "Давайте згадаємо їхні головні ролі."
  replace: "Згадаймо їхні головні ролі."
- find: "Давайте розглянемо типові помилки на рівні А2."
  replace: "Розгляньмо типові помилки на рівні А2."
- find: "до інфінитива."
  replace: "до інфінітива."
- find: "> — **Олена:** Максиме, ти готовий до тесту на рівень B1? Are you ready for the B1 level test?\n> — **Максим:** Майже готовий. I am almost ready. Але я хочу повторити **дієслово**. The word \"дієслово\" means \"verb\".\n> — **Олена:** Добре. Good. Давай згадаємо **вид**. The word \"вид\" means \"aspect\". Що таке **доконаний** і **недоконаний** вид? These mean \"perfective\" and \"imperfective\".\n> — **Максим:** Недоконаний вид — це тривалий процес. Imperfective aspect is a continuous process. Доконаний вид — це результат. Perfective aspect is a result.\n> — **Олена:** Правильно. Correct. Кожне дієслово зазвичай має пару. Every verb usually has a pair. Це видова **пара**. The word \"пара\" means \"pair\".\n> — **Максим:** А як щодо дієслів руху? What about verbs of motion? Префікси змінюють їхнє значення. Prefixes change their meaning.\n> — **Олена:** Так, префікси дуже важливі. Yes, prefixes are very important. П'ємо каву і продовжуємо нашу розмову. Let's drink coffee and continue."
  replace: "> — **Олена:** Максиме, ти готовий до тесту на рівень B1? *(Maksym, are you ready for the B1 level test?)*\n> — **Максим:** Майже готовий, але я хочу повторити відмінки, дієслова та сполучники. *(Almost ready, but I want to review cases, verbs, and conjunctions.)*\n> — **Олена:** Добре. Згадаймо вид. Що ти робив учора, а що зробив сьогодні? *(Good. Let's recall aspect. What were you doing yesterday, and what did you complete today?)*\n> — **Максим:** Учора я читав книгу, а сьогодні я прочитав її до кінця! *(Yesterday I was reading a book, and today I read it to the end!)*\n> — **Олена:** Правильно. А який відмінок після прийменника «без»? *(Correct. And which case follows the preposition "bez"?)*\n> — **Максим:** Родовий! Наприклад, кава без цукру. *(Genitive! For example, coffee without sugar.)*\n> — **Олена:** Чудово. П'ємо каву і продовжуємо нашу розмову, тому що тест уже завтра! *(Great. Let's drink coffee and continue our conversation, because the test is already tomorrow!)*"
- find: "Давайте коротко згадаємо дієслова руху."
  replace: "Коротко згадаймо дієслова руху."
- find: "> — **Вчителька:** Марку, як твої успіхи? *(Mark, how is your progress?)*\n> — **Марко:** Я вже говорю краще, **хоча** роблю **помилки**. *(I speak better already, **although** I make **mistakes**.)*\n> — **Вчителька:** Це нормально! *(That's normal!)*\n> — **Марко:** **Коли** я починав, я знав тільки прості слова. *(**When** I started, I knew only simple words.)*\n> — **Вчителька:** А зараз ти знаєш багато правил **граматики**. *(And now you know many rules of **grammar**.)*\n> — **Марко:** Так, я вчуся, **щоб** перейти на рівень В1. *(Yes, I study **in order to** move to the B1 level.)*\n> — **Вчителька:** **Якщо** ти будеш так вчитися, у тебе все вийде! *(**If** you study like this, you will succeed!)*\n> — **Марко:** Дякую! Я впевнений, **що** це можливо. *(Thank you! I am confident **that** it is possible.)*"
  replace: "> — **Анна:** Марку, що ми вивчали на рівні А2? Я нова учениця. *(Mark, what did we study at the A2 level? I am a new student.)*\n> — **Марко:** Я вже говорю краще, **хоча** ще роблю **помилки**. *(I speak better already, **although** I still make **mistakes**.)*\n> — **Анна:** Це нормально! *(That's normal!)*\n> — **Марко:** **Коли** я починав, я знав тільки прості слова. *(**When** I started, I knew only simple words.)*\n> — **Анна:** А зараз ти знаєш багато правил **граматики**. *(And now you know many rules of **grammar**.)*\n> — **Марко:** Так, я багато вчився, **щоб** перейти на рівень В1. *(Yes, I studied a lot **in order to** move to the B1 level.)*\n> — **Анна:** **Якщо** я буду так вчитися, у мене теж все вийде? *(**If** I study like this, will I also succeed?)*\n> — **Марко:** Звичайно! Я впевнений, **що** це можливо. *(Of course! I am confident **that** it is possible.)*"
- find: "Давайте послухаємо, як студент розповідає про свій прогрес."
  replace: "Послухаймо, як студент розповідає про свій прогрес."
- find: "Давайте проведемо невелику самооцінку."
  replace: "Проведімо невелику самооцінку."
- find: "Якщо ваша оцінка висока — це чудовий результат. If your score is high — this is an excellent result. Якщо ні, варто зробити **повторення** (review). If not, it is worth doing a review."
  replace: "Якщо ваша оцінка висока — це чудовий результат. If your score is high — this is an excellent result. Якщо ні, варто зробити **повторення** (review). If not, it is worth doing a review. Поверніться до модулів M48-M54 для повторення відмінків, або до M30-M35 для повторення дієслів руху. Return to modules M48-M54 to review cases, or to M30-M35 to review verbs of motion."
- find: "<!-- INJECT_ACTIVITY: error-correction-final-review -->\n\n"
  replace: ""
</fixes>
