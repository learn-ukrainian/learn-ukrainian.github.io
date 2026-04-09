## Linguistic Scan
Errors found:
1. **Spelling error:** "інфінитива" — must be "інфінітива".
2. **Calques:** "ми беремо заперечні займенники", "ми беремо сполучник" — "брати" (to take) is a Russianism here; standard Ukrainian uses "використовуємо" or "вживаємо".
3. **Punctuation:** "Рейс скасували через те що почалася буря" — missing comma before "через те, що" (required between main and subordinate clauses).

## Exercise Check
- `<!-- INJECT_ACTIVITY: fill-in-mixed-cases -->` (matches plan: fill-in)
- `<!-- INJECT_ACTIVITY: quiz-aspect-choice -->` (matches plan: quiz)
- `<!-- INJECT_ACTIVITY: group-sort-grammar-categories -->` (matches plan: group-sort)
- `<!-- INJECT_ACTIVITY: error-correction -->` (matches plan: error-correction)
- `<!-- INJECT_ACTIVITY: error-correction-final-review -->` — **EXTRA MARKER**. The plan defines only 4 activities; the 5th is unsupported and injected improperly at the very end.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | Missed pronoun types from the plan ("demonstrative, interrogative... reflexive (себе)"); only covered personal, possessive, indefinite, and negative. Missed providing a "Personal study plan: which A2 modules to revisit before starting B1". Inserted an extra unsupported activity marker. |
| 2. Linguistic accuracy | 7/10 | Spelling error in grammatical terminology ("інфінитива" instead of "інфінітива"). Calques from Russian where "беремо" is used instead of "використовуємо" for applying grammar rules. Missing comma before a subordinate clause. |
| 3. Pedagogical quality | 8/10 | Good use of contrastive examples (e.g. "з молоком" vs "без молока"). However, the text contains a factually empty and confusing note about stress ("Правильно ставте наголос у формах «велика» та «великі»") which adds zero value since there is no stress shift in the adjective root anyway. |
| 4. Vocabulary coverage | 10/10 | All required words (`повторення`, `граматика`, `відмінок`, `дієслово`, `прикметник`, `займенник`, `речення`, `помилка`) and recommended words are included and highlighted naturally. |
| 5. Exercise quality | 8/10 | Markers generally follow the concepts they test, but an unauthorized 5th marker (`error-correction-final-review`) was injected at the end, violating the plan's 4-activity constraint. |
| 6. Engagement & tone | 9/10 | Encouraging teacher persona; solid classroom energy without slipping into gamified or corporate cheerleading. |
| 7. Structural integrity | 10/10 | Excellent adherence to structure. All H2 headings match the outline. The 3037 word count is safely above the 2000-word target. |
| 8. Cultural accuracy | 10/10 | No issues. Proper grammatical rules taught natively, not via Russian parallels. |
| 9. Dialogue & conversation quality | 7/10 | The first dialogue formats the English translations terribly, presenting them as if the characters literally spoke them aloud, and injecting meta-commentary directly into character lines (e.g., `— Максим: ... The word "дієслово" means "verb".`). The second dialogue handled translations correctly. |

## Findings
[1. Plan adherence] [major]
Location: Section "Прикметники, порівняння, займенники" ("Іноді ми не знаємо точно особу чи предмет... Це слова «ніхто» і «ніщо».")
Issue: Failed to cover demonstrative, interrogative, and the reflexive "себе" pronouns as demanded by the plan outline. 
Fix: Append a sentence covering them.

[1. Plan adherence] [major]
Location: Section "Самооцінка і перехід до B1" ("Якщо ні, варто зробити **повторення** (review).")
Issue: Failed to recommend specific A2 modules to revisit based on the self-assessment, as requested by the plan outline.
Fix: Add concrete module references for the review.

[2. Linguistic accuracy] [critical]
Location: Section "Дієслово: вид, час, спосіб" ("Ми додаємо закінчення прямо до інфінитива.")
Issue: Spelling error in a core grammar term. The genitive of "інфінітив" is "інфінітива" (with 'і').
Fix: Change "інфінитива" to "інфінітива".

[2. Linguistic accuracy] [critical]
Location: Section "Прикметники, порівняння, займенники" ("Якщо предмета немає, ми беремо заперечні займенники.") and Section "Складне речення: з'єднуємо думки" ("Для умови ми беремо сполучник «якщо».")
Issue: Russianism calque ("мы берём местоимения/союз"). Standard Ukrainian grammar uses "ми використовуємо" or "ми вживаємо".
Fix: Change "беремо" to "використовуємо".

[2. Linguistic accuracy] [major]
Location: Section "Складне речення: з'єднуємо думки" ("Наприклад: «Рейс скасували через те що почалася буря».")
Issue: Missing required comma between the main clause and the subordinate clause.
Fix: Add a comma before the subordinate clause ("через те, що").

[3. Pedagogical quality] [major]
Location: Section "Прикметники, порівняння, займенники" ("Також завжди звертайте увагу на правильний наголос. Правильно ставте наголос у формах «велика» та «великі». Це робить вашу мову природною.")
Issue: This is factually empty hallucinated pedagogy. Standard "великий" doesn't have complex stress shifts (the stress is always on 'и'), making this instruction confusing and useless to learners.
Fix: Remove the sentences.

[5. Exercise quality] [major]
Location: End of module ("<!-- INJECT_ACTIVITY: error-correction-final-review -->")
Issue: Extra, unauthorized 5th activity marker injected that does not exist in the module plan.
Fix: Remove the injected marker.

[9. Dialogue & conversation quality] [major]
Location: First dialogue between Олена and Максим.
Issue: Formatting failure. The English translations and meta-vocabulary hints are presented as actual spoken lines by the characters.
Fix: Reformat the English translations into parenthetical italics.

## Verdict: REVISE
The writer produced an excellent word count, but committed multiple critical linguistic and formatting errors. Specifically, it used Russianisms ("ми беремо" instead of "ми використовуємо"), misspelled a core grammar term ("інфінитива"), missed pronoun plan points, broke the dialogue formatting, and hallucinates pedagogical instructions. Precise deterministic fixes will easily resolve these issues.

<fixes>
- find: "Ми додаємо закінчення прямо до інфінитива."
  replace: "Ми додаємо закінчення прямо до інфінітива."
- find: "Якщо предмета немає, ми беремо заперечні займенники."
  replace: "Якщо предмета немає, ми використовуємо заперечні займенники."
- find: "Для умови ми беремо сполучник «якщо»."
  replace: "Для умови ми використовуємо сполучник «якщо»."
- find: "Наприклад: «Рейс скасували через те що почалася буря»."
  replace: "Наприклад: «Рейс скасували через те, що почалася буря»."
- find: "Іноді ми не знаємо точно особу чи предмет. Тоді ми використовуємо неозначені займенники. Це слова «хтось» або «щось»."
  replace: "Іноді ми не знаємо точно особу чи предмет. Тоді ми використовуємо неозначені займенники. Це слова «хтось» або «щось». Також ми маємо вказівні займенники («цей», «той»), питальні («хто?», «що?») та зворотний займенник «себе»."
- find: "Якщо ні, варто зробити **повторення** (review)."
  replace: "Якщо ні, варто зробити **повторення** (review) конкретних модулів А2: наприклад, модуль 51 для відмінків або модуль 63 для складнопідрядних речень."
- find: "Наприклад, ми кажемо «повен» замість «повний». Також завжди звертайте увагу на правильний наголос. Правильно ставте наголос у формах «велика» та «великі». Це робить вашу мову природною.\n\n<!-- INJECT_ACTIVITY: group-sort-grammar-categories -->"
  replace: "Наприклад, ми кажемо «повен» замість «повний».\n\n<!-- INJECT_ACTIVITY: group-sort-grammar-categories -->"
- find: "Це зробить вашу мову ще природнішою. This will make your speech even more natural.\n\n<!-- INJECT_ACTIVITY: error-correction-final-review -->\n\n**Підсумок**"
  replace: "Це зробить вашу мову ще природнішою. This will make your speech even more natural.\n\n**Підсумок**"
- find: "> — **Олена:** Максиме, ти готовий до тесту на рівень B1? Are you ready for the B1 level test?\n> — **Максим:** Майже готовий. I am almost ready. Але я хочу повторити **дієслово**. The word \"дієслово\" means \"verb\".\n> — **Олена:** Добре. Good. Давай згадаємо **вид**. The word \"вид\" means \"aspect\". Що таке **доконаний** і **недоконаний** вид? These mean \"perfective\" and \"imperfective\".\n> — **Максим:** Недоконаний вид — це тривалий процес. Imperfective aspect is a continuous process. Доконаний вид — це результат. Perfective aspect is a result.\n> — **Олена:** Правильно. Correct. Кожне дієслово зазвичай має пару. Every verb usually has a pair. Це видова **пара**. The word \"пара\" means \"pair\".\n> — **Максим:** А як щодо дієслів руху? What about verbs of motion? Префікси змінюють їхнє значення. Prefixes change their meaning.\n> — **Олена:** Так, префікси дуже важливі. Yes, prefixes are very important. П'ємо каву і продовжуємо нашу розмову. Let's drink coffee and continue."
  replace: "> — **Олена:** Максиме, ти готовий до тесту на рівень B1? *(Are you ready for the B1 level test?)*\n> — **Максим:** Майже готовий. *(I am almost ready.)* Але я хочу повторити **дієслово**. *(But I want to review the verb.)*\n> — **Олена:** Добре. *(Good.)* Давай згадаємо **вид**. *(Let's remember the aspect.)* Що таке **доконаний** і **недоконаний** вид? *(What are perfective and imperfective aspects?)*\n> — **Максим:** Недоконаний вид — це тривалий процес. *(Imperfective aspect is a continuous process.)* Доконаний вид — це результат. *(Perfective aspect is a result.)*\n> — **Олена:** Правильно. *(Correct.)* Кожне дієслово зазвичай має пару. *(Every verb usually has a pair.)* Це видова **пара**. *(This is an aspectual pair.)*\n> — **Максим:** А як щодо дієслів руху? *(What about verbs of motion?)* Префікси змінюють їхнє значення. *(Prefixes change their meaning.)*\n> — **Олена:** Так, префікси дуже важливі. *(Yes, prefixes are very important.)* П'ємо каву і продовжуємо нашу розмову. *(Let's drink coffee and continue.)*"
</fixes>
