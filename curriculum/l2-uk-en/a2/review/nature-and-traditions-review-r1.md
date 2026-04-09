## Linguistic Scan
No linguistic errors found.

## Exercise Check
- `<!-- INJECT_ACTIVITY: match-up-seasons-match-seasonal-vocabulary-and-activities -->` - present and well-placed.
- `<!-- INJECT_ACTIVITY: quiz-holiday-traditions -->` - present and well-placed.
- `<!-- INJECT_ACTIVITY: fill-in-grammar-seasons -->` - present and well-placed.
- `<!-- INJECT_ACTIVITY: true-false-culture -->` - present and well-placed.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | Missed specific required phrases ("Яка сьогодні погода?", "Температура — п'ять градусів", "Цієї зими я планую..."), as well as required holidays ("Вербна неділя", "День Конституції"). |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, or Calques found. Grammar and usage are idiomatic and accurate. |
| 3. Pedagogical quality | 9/10 | Excellent breakdown of grammatical exceptions like "навесні" vs "у весні" and proper explanations of genitive case usage for dates. |
| 4. Vocabulary coverage | 10/10 | All required and recommended words are included seamlessly into the narrative. |
| 5. Exercise quality | 10/10 | All injection markers are present and correctly mapped to the outline. |
| 6. Engagement & tone | 10/10 | The tone is warm and culturally respectful without resorting to overly gamified or corporate tropes. |
| 7. Structural integrity | 10/10 | Meets the word count (2356 > 2000 target) and uses H2 headers perfectly aligned with the plan. |
| 8. Cultural accuracy | 10/10 | Factually correct context about contemporary date shifts (Christmas on Dec 25), correctly representing holidays like Ivan Kupala and Pokrova. |
| 9. Dialogue & conversation quality | 5/10 | The module includes a very generic dialogue about seasons but completely omitted the specific plan-mandated dialogue setting featuring a family and a foreign guest discussing Ivan Kupala, Christmas, and Easter traditions. |

## Findings

[1. Plan adherence] [Major]
Location: Section "Чотири пори року (The Four Seasons)"
Issue: The required weather phrases "Яка сьогодні погода?", "Температура — п'ять градусів" are missing.
Fix: Add these exact phrases as examples of how to talk about the weather.

[1. Plan adherence] [Major]
Location: Section "Українські свята: від Різдва до Купала (Ukrainian Holidays)"
Issue: The holidays "Вербна неділя" and "День Конституції" are missing from the text.
Fix: Insert mentions of Вербна неділя and День Конституції in their respective seasonal paragraphs.

[1. Plan adherence] [Major]
Location: Section "Що ми робимо у кожну пору року? (Seasonal Activities)"
Issue: The narrative practice phrase "Цієї зими я планую..." is missing.
Fix: Add "Або ми плануємо майбутнє: «Цієї зими я планую багато відпочивати»" after the "Минулого літа" example.

[9. Dialogue & conversation quality] [Major]
Location: Section "Українські свята: від Різдва до Купала (Ukrainian Holidays)"
Issue: The global `dialogue_situations` requirement (Family and Foreign Guest discussing Kupala, Christmas, and Easter traditions) was ignored.
Fix: Insert the missing dialogue at the end of the "Українські свята" section before the activity marker.

## Verdict: REVISE
The writer missed multiple specific plan points and entirely omitted the main required dialogue situation involving the family and foreign guest. These omissions are major structural deviations from the plan and require immediate revision.

<fixes>
- find: "День може бути сонячний, іноді — хмарний або навіть вітряний. Але зазвичай влітку завжди тепло і дуже приємно."
  replace: "День може бути сонячний, іноді — хмарний або навіть вітряний. Щоб запитати про це, ми кажемо: «Яка сьогодні погода?». А відповідаємо так: «Сьогодні сонячно. Іде дощ/сніг. Температура — п'ять градусів тепла». Але зазвичай влітку завжди тепло і дуже приємно."
- find: "Навесні вся природа прокидається, і приходить велике весняне свято — **Великдень** *(Easter)*. Це найголовніше християнське свято в Україні. Традиційно **на Великдень** *(for Easter)* українці йдуть до церкви."
  replace: "Навесні вся природа прокидається, і приходить велике весняне свято — **Великдень** *(Easter)*. Це найголовніше християнське свято в Україні. За тиждень до цього ми святкуємо Вербну неділю. Традиційно **на Великдень** *(for Easter)* українці йдуть до церкви."
- find: "Наприкінці літа ми маємо найважливіше державне свято. Двадцять четвертого серпня ми гордо святкуємо **День Незалежності** *(Independence Day)* України."
  replace: "Наприкінці літа ми маємо важливі державні свята. Двадцять восьмого червня ми відзначаємо День Конституції. А двадцять четвертого серпня ми гордо святкуємо **День Незалежності** *(Independence Day)* України."
- find: "Наприклад: «Минулого літа ми часто ходили до річки, тому що було дуже спекотно». Щоб розповісти про свої регулярні дії, ми беремо спеціальні слова."
  replace: "Наприклад: «Минулого літа ми часто ходили до річки, тому що було дуже спекотно». Або ми плануємо майбутнє: «Цієї зими я планую багато відпочивати». Щоб розповісти про свої регулярні дії, ми беремо спеціальні слова."
- find: "Запам'ятайте цю дуже просту формулу: Порядковий числівник (Родовий відмінок) + Місяць (Родовий відмінок). Це нове правило допоможе вам правильно говорити про свої дні народження та ваші улюблені свята.\n\n<!-- INJECT_ACTIVITY: quiz-holiday-traditions -->"
  replace: "Запам'ятайте цю дуже просту формулу: Порядковий числівник (Родовий відмінок) + Місяць (Родовий відмінок). Це нове правило допоможе вам правильно говорити про свої дні народження та ваші улюблені свята.\n\nДавайте послухаємо, як українська родина розповідає іноземному гостю про свої свята:\n\n> — **Гість:** Які ваші найулюбленіші українські свята?\n> — **Мама:** Ми дуже любимо Різдво. Взимку ми співаємо колядки, а на столі завжди стоїть солодка кутя.\n> — **Тато:** Навесні у нас Великдень. Ми розмальовуємо писанки і печемо смачні паски.\n> — **Донька:** А влітку ми святкуємо Івана Купала! Ми плетемо зелений вінок, шукаємо магічний цвіт папороті та високо стрибаємо через вогнище.\n> — **Гість:** Це звучить неймовірно! Я б дуже хотів побачити це вогнище.\n\n<!-- INJECT_ACTIVITY: quiz-holiday-traditions -->"
</fixes>
