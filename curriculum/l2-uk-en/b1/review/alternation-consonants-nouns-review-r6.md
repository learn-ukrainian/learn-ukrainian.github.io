## Linguistic Scan
Errors found:
1. `у Мекці` — incorrect locative form. The correct form of `Мекка` is `Мецці`.
2. `у Нью-Йорці` — factual error. Modern borrowings like `Нью-Йорк` only take the `-у` ending (`у Нью-Йорку`), and the form `у Нью-Йорці` does not exist.
3. `знаходиться` — calque when used for physical location. Should be `розташована`.
4. `фронтальний голосний` — calque/anglicism. The correct phonetic term is `голосний переднього ряду`.

## Exercise Check
All markers are present and correctly placed:
- `INJECT_ACTIVITY: fill-in` (Кличний) — correctly placed after the first palatalization section.
- `INJECT_ACTIVITY: fill-in` (Давальний/Місцевий) — correctly placed after the second palatalization section.
- `INJECT_ACTIVITY: quiz` (Identify palatalization type) — correctly placed.
- `INJECT_ACTIVITY: match-up` — correctly placed.
- `INJECT_ACTIVITY: error-correction` — correctly placed.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | The writer completely ignored the plan's dialogue setup (Книгар and Покупець in Lviv), modified H2 headers making them incompatible with the audit script, added an unauthorized H2 header (`## Родинні слова...`), and failed to cite the required textbooks from the `content_outline` (Авраменко, Заболотний, Глазова, Литвінова). |
| 2. Linguistic accuracy | 7/10 | Critical errors found: claimed `у Мекці` instead of `у Мецці`; claimed `у Нью-Йорці` is a valid form. Used calques `знаходиться` and `фронтальний голосний`. |
| 3. Pedagogical quality | 9/10 | Strong, logical breakdown of the two palatalizations. Historical context is helpful without being overwhelming. |
| 4. Vocabulary coverage | 10/10 | All required vocabulary (`чергування`, `палаталізація`, `кличний відмінок`, etc.) was naturally integrated into the text. |
| 5. Exercise quality | 10/10 | The 5 required markers match the plan's `activity_hints` in type and focus, and are placed logically after the concept is taught. |
| 6. Engagement & tone | 9/10 | The tone is encouraging. The breakdown of related words (cognates) effectively shows rather than tells the beauty of the language. |
| 7. Structural integrity | 6/10 | H2 headings do not exactly match the plan's `content_outline`, which breaks the audit script. An extra H2 was added. |
| 8. Cultural accuracy | 10/10 | Excellent explanation of the cultural importance of the vocative case for emotional closeness and authentic naming. |
| 9. Dialogue & conversation quality | 7/10 | The opening dialogue ignored the prompt and was somewhat stilted. The characters "Олег" and "Марко" were used instead of the requested bookseller and buyer. |

## Findings
[Plan adherence] [Major]
Location: `## Перша палаталізація: [г], [к], [х] → [ж], [ч], [ш]` (and other headers)
Issue: The H2 headings do not match the `content_outline` in the plan. The script `audit_module.py` requires exact matching. The writer also added an H2 heading `## Родинні слова: як чергування створює лексичну мережу` which is not in the outline.
Fix: Update headers to exactly match the plan. Change the extra H2 to an H3.

[Dialogue & conversation quality] [Major]
Location: `— Привіт, Олеже!...` (First dialogue)
Issue: The generated dialogue ignores the plan's setting ("At a Львівська книгарня... discussing authors and book titles") and characters ("Книгар, Покупець").
Fix: Replace the dialogue and the following explanation paragraph to match the plan's setting and target words.

[Linguistic accuracy] [Critical]
Location: `Саме тому ми кажемо в Америці, у Празі, у Мекці.`
Issue: The locative form of "Мекка" is "у Мецці", not "у Мекці". This is a critical grammatical error.
Fix: Replace `у Мекці` with `у Мецці`.

[Linguistic accuracy] [Critical]
Location: `я працюю у Нью-Йорку (також можлива форма «у Нью-Йорці», але вона вживається рідше).`
Issue: The form "у Нью-Йорці" does not exist and is a factual error. As a modern foreign borrowing, it only takes the "-у" ending.
Fix: Remove the claim that "у Нью-Йорці" is a possible form.

[Linguistic accuracy] [Minor]
Location: `Моя квартира знаходиться на п'ятому поверсі.`
Issue: The word "знаходиться" is a common calque when describing physical location.
Fix: Replace "знаходиться" with "розташована".

[Linguistic accuracy] [Minor]
Location: `додається фронтальний голосний [е]`
Issue: "Фронтальний голосний" is an unnatural calque. The correct phonetic term is "голосний переднього ряду".
Fix: Replace "фронтальний голосний" with "голосний переднього ряду".

[Plan adherence] [Major]
Location: `Що таке чергування приголосних?` and other sections
Issue: The plan explicitly requires citing textbook references (Авраменко, Заболотний, Глазова, Литвінова) in the `content_outline`, but they are missing from the prose.
Fix: Integrate the textbook references into the text naturally.

## Verdict: REVISE
The module requires revision due to critical linguistic errors (`у Мекці`, `у Нью-Йорці`) and major structural and plan adherence deviations (incorrect H2 headers, missing textbook references, and ignored dialogue setup).

<fixes>
- find: "## Перша палаталізація: [г], [к], [х] → [ж], [ч], [ш]"
  replace: "## Перша палаталізація: [г/к/х] -> [ж/ч/ш]"
- find: "## Друга палаталізація у жіночому роді: [г/к/х] → [з'/ц'/с']"
  replace: "## Друга палаталізація: [г/к/х] -> [з'/ц'/с']"
- find: "## Родинні слова: як чергування створює лексичну мережу"
  replace: "### Родинні слова: як чергування створює лексичну мережу"
- find: "## Зміни м'якого [ц'] на твердий [ч] та інші явища"
  replace: "## Чергування [ц'] -> [ч] та інші"
- find: "## Підсумок: глобальна таблиця чергувань"
  replace: "## Підсумок: таблиця чергувань"
- find: |
    — Привіт, Олеже!
    — Привіт, Марку! Яка гарна книжка!
    — Дякую, я купив її вчора у новій книгарні.
    — А я шукаю підручник з історії. Завтра ми з друзями йдемо до бібліотеки.
    — У бібліотеці на другому поверсі є чудовий відділ. Я можу допомогти тобі знайти його, коли ми будемо на місці.

    У цьому короткому діалозі ви можете помітити кілька незвичних граматичних форм. Чому ім'я «Олег» перетворилося на «Олеже»? Чому слово «книга» змінилося на «книжка» та «книжечка»? Чому замість очікуваного «у бібліотекі» ми чуємо «у бібліотеці», а замість «на поверхі» — «на поверсі»?
  replace: |
    **Книгар:** Доброго дня! Чим можу допомогти у нашій львівській книгарні?
    **Покупець:** Доброго дня. Я тримаю у руці список авторів. Шукаю нову книжку про козаків.
    **Книгар:** Так, звісно, друже. У цій книжці є чудові ілюстрації — можна роздивитися кожну деталь, навіть сережку у козачому вусі.
    **Покупець:** Дякую!

    У цьому короткому діалозі ви можете помітити кілька незвичних граматичних форм. Чому слово «друг» перетворилося на «друже»? Чому «книга» змінилася на «книжці», замість очікуваного «у рукі» ми чуємо «у руці», а замість «у вухі» — «у вусі»?
- find: "Саме тому ми кажемо в Америці, у Празі, у Мекці."
  replace: "Саме тому ми кажемо в Америці, у Празі, у Мецці."
- find: "я працюю у Нью-Йорку (також можлива форма «у Нью-Йорці», але вона вживається рідше)."
  replace: "я працюю у Нью-Йорку (тут корінь залишається твердим)."
- find: "Моя квартира знаходиться на п'ятому поверсі."
  replace: "Моя квартира розташована на п'ятому поверсі."
- find: "додається фронтальний голосний [е]"
  replace: "додається голосний переднього ряду [е]"
- find: "Всі ці зміни не є випадковими винятками. Це прояв одного з найважливіших і найдавніших фонетичних законів української мови. В українській мові приголосні звуки часто і регулярно змінюються під час творення нових слів або під час зміни їхньої граматичної форми (відмінювання). Цей фундаментальний процес називається **чергування** *(alternation)*."
  replace: "Всі ці зміни не є випадковими винятками. Це прояв одного з найважливіших фонетичних законів української мови. В українській мові приголосні звуки часто і регулярно змінюються під час творення нових слів або під час зміни їхньої граматичної форми (відмінювання). Цей фундаментальний процес називається **чергування** *(alternation)*. Як зазначає Олександр Авраменко у своєму підручнику (Grade 5, p. 114): «Найпоширенішими є такі чергування приголосних: [г] — [з] — [ж], [к] — [ц] — [ч], [х] — [с] — [ш]»."
- find: "Механізм першої палаталізації виглядає так:\n*   Звук **[г]** перетворюється на шиплячий **[ж]**. Приклад: корінь *друг-* змінюється на *друж-*."
  replace: "Як пояснює підручник Заболотного (Grade 5, p. 116), механізм першої палаталізації виглядає так:\n*   Звук **[г]** перетворюється на шиплячий **[ж]**. Приклад: корінь *друг-* змінюється на *друж-*."
- find: "Ця фонетична зміна найчастіше трапляється у кличному відмінку іменників чоловічого роду другої відміни, які мають розповсюджений суфікс **-ець**. Цей суфікс часто позначає професію, приналежність до групи або є просто словотвірним елементом.\n\nЗверніть увагу на те, як формується кличний відмінок для цих слів."
  replace: "Ця фонетична зміна найчастіше трапляється у кличному відмінку іменників чоловічого роду другої відміни, які мають розповсюджений суфікс **-ець**. Як зазначає О. Глазова (Grade 10, p. 209), цей суфікс часто позначає професію чи приналежність до групи.\n\nЗверніть увагу на те, як формується кличний відмінок для цих слів."
- find: "В українській граматиці іменники чоловічого роду (які мають нульове закінчення або закінчення -о) та іменники середнього роду (із закінченнями -о, -е, -я) належать до категорії **друга відміна** *(second declension)*. За характером кінцевого приголосного основи всі іменники поділяються на три групи: тверду, м'яку та мішану."
  replace: "В українській граматиці іменники чоловічого роду (які мають нульове закінчення або закінчення -о) та іменники середнього роду (із закінченнями -о, -е, -я) належать до категорії **друга відміна** *(second declension)*. Як подає систематична таблиця у підручнику Литвінової (Grade 6, p. 159), за характером кінцевого приголосного основи всі іменники поділяються на три групи: тверду, м'яку та мішану."
- find: "Для цих слів друга палаталізація ([г] → [з'], [к] → [ц'], [х] → [с']) є абсолютно центральним і найважливішим фонетичним правилом."
  replace: "Як ілюструє підручник Авраменка (Grade 5, p. 114), для цих слів друга палаталізація ([г] → [з'], [к] → [ц'], [х] → [с']) є абсолютно центральним і найважливішим фонетичним правилом."
</fixes>
