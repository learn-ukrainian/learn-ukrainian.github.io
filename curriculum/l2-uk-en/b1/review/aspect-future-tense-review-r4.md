## Linguistic Scan

- **Russianisms/Calques**: The phrase «давайте спочатку перевіримо» is a calque of the Russian construction "давайте проверим". The standard, idiomatic Ukrainian form uses the synthetic imperative: «спершу перевірмо».
- **English Typo**: In the opening paragraph, there is a dangling sentence structure/missing word: `in front of a verb, and  "I will read,"` — it should be `and say "I will read,"`.
- All other Ukrainian phrasing is highly natural, grammatically correct, and idiomatically sound. `VESUM` confirms all morphology.

## Exercise Check

- **Marker count**: All 6 required markers are present, matching the `activity_hints` count.
- **Marker placement**: `<!-- INJECT_ACTIVITY: group-sort-constructions -->` is placed prematurely. It appears *before* the third construction (simple perfective future) is taught. Since the plan specifically says this exercise asks learners to "Sort future-tense forms into три конструкції", placing it before the third construction is introduced breaks the pedagogical sequence. It must be moved after the section covering the third construction. All other markers are placed correctly.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The structure follows the outline perfectly, but fails to include the mandatory textbook citations (Литвінова Grade 7 p.44/46, Заболотний Grade 7 p.73) within the prose. It also misses several required vocabulary words. |
| 2. Linguistic accuracy | 9/10 | Excellent Ukrainian overall, but contains one calque ("давайте спочатку перевіримо") and one English typo ("in front of a verb, and  \"I will read,\""). |
| 3. Pedagogical quality | 9/10 | Brilliant "Process vs Result" framing and logical presentation. However, the `group-sort-constructions` exercise marker is placed before the third future construction is taught, testing learners on material they haven't seen yet. |
| 4. Vocabulary coverage | 8/10 | Six words from the `vocabulary_hints` are completely missing from the text ("постаратися", "запланувати", "закінчувати", "розмовний стиль", "писемний стиль", "передбачення"). |
| 5. Exercise quality | 9/10 | The exercise types match the plan accurately, but the placement of the sort exercise is structurally flawed (as noted in Pedagogical quality). |
| 6. Engagement & tone | 10/10 | Excellent teacher persona. Phrases like "congratulations — you already intuitively understand" provide natural, meaningful encouragement. |
| 7. Structural integrity | 10/10 | All sections are present and properly ordered. The word count is 5242, safely exceeding the 4000-word target. Clean markdown formatting. |
| 8. Cultural accuracy | 10/10 | Accurately and respectfully presents the Ukrainian aspectual system on its own terms, highlighting how the language forces a commitment to intent. |
| 9. Dialogue & conversation quality | 10/10 | The dialogues are superb. Dmytro's "Process Defense" is a brilliant, natural demonstration of grammar functioning as a psychological tool in conversation. |

## Findings

[Plan adherence] [Major]
Location: Section "Три конструкції: форма і значення"
Issue: Mandatory textbook references from the plan outline (Литвінова Grade 7 p.44/46, Заболотний Grade 7 p.73) were omitted from the prose.
Fix: Add the exact citations to the introductory sentences for each of the three future constructions.

[Vocabulary coverage] [Major]
Location: Scattered throughout the module
Issue: Six required words from the `vocabulary_hints` were not used in the text: "постаратися", "запланувати", "закінчувати", "розмовний стиль", "писемний стиль", "передбачення".
Fix: Weave these words naturally into existing paragraphs.

[Pedagogical quality] [Major]
Location: Section "Три конструкції: форма і значення"
Issue: The activity marker `<!-- INJECT_ACTIVITY: group-sort-constructions -->` is placed *before* the third construction (simple perfective) is actually taught, making the exercise unsolvable at that point.
Fix: Move the marker down so it appears after the explanation of the third construction and its rules.

[Linguistic accuracy] [Minor]
Location: Section "Тест: яке майбутнє ви оберете?" — `Але перед тим, як ми заглибимося в граматичні правила та таблиці, давайте спочатку перевіримо вашу природну інтуїцію.`
Issue: The phrase "давайте ... перевіримо" is a Russianism/calque. Standard Ukrainian strictly prefers the synthetic imperative "перевірмо".
Fix: Replace "давайте спочатку перевіримо" with "спершу перевірмо".

[Linguistic accuracy] [Minor]
Location: Section "Тест: яке майбутнє ви оберете?" — `in front of a verb, and  "I will read,"`
Issue: Dangling sentence structure/missing word in the English explanation.
Fix: Replace `verb, and  "I will read,"` with `verb and say "I will read,"`.

## Verdict: REVISE
The module is exceptional in its narrative and conceptual framing of Ukrainian verb aspect, but it requires revision to fix the premature exercise placement, inject missing mandatory vocabulary/citations, and clean up a minor calque.

<fixes>
- find: "Перша конструкція називається складений майбутній час. Вона завжди складається"
  replace: "Перша конструкція називається складений майбутній час (як зазначено в підручнику Литвінової для 7 класу, с. 44). Вона завжди складається"
- find: "The second construction is known as the synthetic imperfective future. Grammatically"
  replace: "The second construction is known as the synthetic imperfective future (див. Заболотний, 7 клас, с. 73). Grammatically"
- find: "The third and final construction is the simple perfective future. Unlike"
  replace: "The third and final construction is the simple perfective future (Литвінова, 7 клас, с. 46). Unlike"
- find: "використовують майбутній час недоконаного виду. Наприклад, ви можете сказати: «Я буду старатися» або «Ми будемо чекати на тебе»."
  replace: "використовують майбутній час недоконаного виду. Наприклад, ви можете сказати: «Я буду старатися» (замість доконаного результату «постаратися») або «Ми будемо чекати на тебе»."
- find: "повсякденного спілкування. Це ваш надійний, нейтральний розмовний стандарт."
  replace: "повсякденного спілкування. Це ваш надійний, нейтральний розмовний стиль."
- find: "Деякі мовознавці вважають її більш традиційною та автентичною, оскільки вона є унікальною рисою нашої мови."
  replace: "Цей писемний стиль робить текст більш вишуканим. Деякі мовознавці вважають її більш традиційною та автентичною, оскільки вона є унікальною рисою нашої мови."
- find: "Коли ви плануєте свій завтрашній день або розповідаєте комусь про майбутню подорож, ви рідко"
  replace: "Коли ви плануєте (або хочете запланувати) свій завтрашній день або розповідаєте комусь про майбутню подорож, ви рідко"
- find: "Ви не можете сказати, що будете завершувати щось цілий день, якщо акцент стоїть саме на точці завершення."
  replace: "Ви не можете сказати, що будете закінчувати щось цілий день, якщо акцент стоїть саме на точці завершення."
- find: "It transforms the future tense from a vague prediction into a precise communicative tool."
  replace: "It transforms the future tense from a vague prediction (передбачення) into a precise communicative tool."
- find: ":::\n\n<!-- INJECT_ACTIVITY: group-sort-constructions -->\n\nThe third and final construction"
  replace: ":::\n\nThe third and final construction"
- find: ":::\n\n<!-- INJECT_ACTIVITY: fill-in-future-forms -->\n\n## Коли який? Вибір конструкції"
  replace: ":::\n\n<!-- INJECT_ACTIVITY: fill-in-future-forms -->\n\n<!-- INJECT_ACTIVITY: group-sort-constructions -->\n\n## Коли який? Вибір конструкції"
- find: "давайте спочатку перевіримо вашу природну інтуїцію."
  replace: "спершу перевірмо вашу природну інтуїцію."
- find: "in front of a verb, and  \"I will read,\""
  replace: "in front of a verb and say \"I will read,\""
</fixes>