## Linguistic Scan
Two critical linguistic errors found:
1. **Grammatical Error**: The text incorrectly identifies the vocative form «друже» as an example of a locative or dative case alternation.
2. **Case Error**: The text uses the preposition «через» with the dative/locative case («через усьому місту») instead of the required accusative case («через усе місто»).
No Russianisms, Surzhyk, or calques were detected. All words used belong to the active Ukrainian lexicon and have been validated against VESUM.

## Exercise Check
**Status**: Critical mismatch with plan.
- The writer correctly generated 6 `INJECT_ACTIVITY` markers, matching the count in the plan.
- **However**, the writer completely ignored the exact `type` and `focus` strings from the plan's `activity_hints`. Instead, it invented its own marker titles (e.g., `quiz, 1st person singular of labial verbs` instead of exactly `group-sort, Sort verbs by alternation type...`).
- This discrepancy breaks the build pipeline because the downstream activity generator relies on the exact hints provided in the plan.
- The markers must be strictly updated to match the plan.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 4/10 | The text ignored the `dialogue_situations` (Cooking competition) and replaced it with generic grammar complaining: `— Олено: Ти знаєш, що я зараз роблю?... — Марку: Це фонетичне чергування!`. Also, it completely failed to cite the required textbook references (Заболотний Grade 7, Глазова Grade 10) mandated by the `content_outline`. |
| 2. Linguistic accuracy | 4/10 | CRITICAL errors: 1) Teaches that «друже» is locative/dative: `в іменниках у місцевому та давальному відмінках (наприклад, «друг» — «друзі» — «друже»`. 2) Uses wrong case with "через": `Глибока річка тече через усьому місту.` |
| 3. Pedagogical quality | 7/10 | Generally sound explanation of the historical [j] suffix and its impact on modern II conjugation. However, presenting "друже" as a locative form is highly confusing for learners who just learned it as vocative in M09. |
| 4. Vocabulary coverage | 8/10 | Used all `required` vocabulary naturally. Missed two `recommended` words: "продуктивний" and "закономірність". |
| 5. Exercise quality | 3/10 | Activity markers do not correspond to the plan's `activity_hints` (e.g., missing `group-sort` and `error-correction` entirely, inventing custom marker strings). |
| 6. Engagement & tone | 4/10 | Fails the stylistic guidelines by relying heavily on meta-commentary and "magic" framing: `Воно працює як магія`, `справжній ключ до розширення вашого словникового запасу`, and `Ви озброєні знаннями, які дозволяють бачити прозору структуру мови.` |
| 7. Structural integrity | 10/10 | Clean markdown, sections correspond well to the outline, and word count is perfectly on target. |
| 8. Cultural accuracy | 10/10 | Phonetics and morphology are explained natively on Ukrainian terms without relying on Russian comparisons. |
| 9. Dialogue & conversation quality | 3/10 | The dialogue is a highly artificial "meta-conversation" where characters just list out grammar rules to each other instead of engaging in the natural, situational communication (cooking show) prescribed by the plan. |

## Findings

[1. Plan adherence] [critical]
Location: Opening dialogue (`> — **Олено:** Ти знаєш, що я зараз **роблю**? ...`)
Issue: The writer ignored the planned `dialogue_situations` (Cooking competition on TV) and wrote an unnatural meta-conversation about grammar rules. 
Fix: Replace the dialogue with the planned cooking competition context.

[1. Plan adherence] [major]
Location: Throughout the module's theoretical introductions.
Issue: The writer failed to cite the specific textbook references (Заболотний Grade 7, Глазова Grade 10) mandated by the `content_outline`.
Fix: Inject the textbook citations at the appropriate section openings.

[2. Linguistic accuracy] [critical]
Location: `в іменниках у місцевому та давальному відмінках (наприклад, «друг» — «друзі» — «друже», «рука» — «руці»).`
Issue: The form «друже» is the vocative case (кличний відмінок), but the sentence presents it as an example of locative or dative. This is factually incorrect and misleading.
Fix: Update the phrasing to `у різних відмінках` and clarify the forms.

[2. Linguistic accuracy] [critical]
Location: `Глибока річка тече через усьому місту.`
Issue: The preposition «через» strictly requires the accusative case («через усе місто»). The text incorrectly uses the dative/locative «усьому місту».
Fix: Change `через усьому місту` to `через усе місто`.

[5. Exercise quality] [major]
Location: `<!-- INJECT_ACTIVITY: ... -->` markers throughout the text.
Issue: The writer invented custom activity marker strings instead of using the exact `type` and `focus` strings provided in the plan's `activity_hints`.
Fix: Replace all 6 `INJECT_ACTIVITY` markers with the exact strings from the plan.

[6. Engagement & tone] [minor]
Location: `Знання цих звукових відповідностей — це справжній ключ до розширення вашого словникового запасу.` and `Ви озброєні знаннями, які дозволяють бачити прозору структуру мови.`
Issue: The text relies on corporate-speak meta-commentary ("справжній ключ", "ви озброєні знаннями") and "telling instead of showing", violating stylistic guidelines.
Fix: Simplify the concluding transitional sentences to be direct and objective.

## Verdict: REVISE
The module contains critical linguistic errors (wrong case usage, misidentified vocative case) and completely failed to adhere to the planned dialogue situation and exercise mapping. The provided fixes will correct the factual errors, map the activities to the plan, and bring the text up to standard.

<fixes>
- find: "> — **Олено:** Ти знаєш, що я зараз **роблю**?\n> — **Марку:** Ти завжди щось робиш. Певно, знову щось читаєш? Або, можливо, ти **сидиш** за комп'ютером і щось пишеш?\n> — **Олено:** Ні, я **сиджу** і **дивлюся** на ці слова. У словнику написано «робити», а я кажу «роблю». Написано «сидіти», а я кажу «сиджу». Написано «ходити», а я кажу «ходжу». Звідки беруться ці нові звуки? Чому звук «д» раптом перетворюється на «дж», а звук «б» отримує якусь додаткову літеру «л»? Я не **бачу** жодної логіки.\n> — **Марку:** Це фонетичне чергування! Воно працює як магія. Ти просто не помічаєш, як твій мовний апарат сам обирає зручніші звуки для вимови.\n> — **Олено:** Зручніші? Тобто казати «їжджу» замість «їзду» — це зручніше? Я **плачу**, коли намагаюся це швидко вимовити! Почекай... «плакати» — «плачу». Знову чергування! Воно мене переслідує всюди.\n> — **Марку:** Так, воно всюди. Але щойно ти зрозумієш систему, ти почнеш відчувати ритм української мови."
  replace: "> **Кулінарне шоу на телебаченні.**\n> — **Ведучий:** Я зараз **ходжу** по кухні й коментую: він ніколи не просить про допомогу, але сьогодні кричить «Я **прошу** (с→ш) солі!». Вона зазвичай повільно возить продукти, але сьогодні каже: «Я **вожу** (з→ж) швидко!». А я **сиджу** (д→дж) і спостерігаю.\n> — **Учасники:** Ми **печемо**, **ріжемо** і **плачемо** (к→ч) від цибулі!"
- find: "в іменниках у місцевому та давальному відмінках (наприклад, «друг» — «друзі» — «друже», «рука» — «руці»)."
  replace: "в іменниках у різних відмінках (наприклад, «друг» — «друзі», «друже», «рука» — «руці»)."
- find: "Історично українська мова, як і інші слов'янські мови, мала спеціальний суфікс із приголосним [j] (йот) у формі першої особи однини."
  replace: "Як зазначається в підручнику О. Заболотного (7 клас, с. 52): «Закономірними для української мови стали чергування приголосних звуків, що відбулися перед давнім суфіксом j». Історично українська мова мала цей спеціальний суфікс із приголосним [j] (йот) у формі першої особи однини."
- find: "Перша велика група дієслівних чергувань стосується звуків, які ми називаємо терміном **зубний** (dental — consonant formed at the teeth: д, т, з, с)."
  replace: "Як наводить О. Глазова (10 клас, с. 107), перша велика група дієслівних чергувань стосується зубних звуків (dental — consonant formed at the teeth: д, т, з, с)."
- find: "Глибока річка тече через усьому місту."
  replace: "Глибока річка тече через усе місто."
- find: "Остання велика група приголосних, які зазнають впливу історичного йота [j] у першій особі однини, — це губні приголосні. До них належать звуки [б], [п], [в], [м] та [ф]."
  replace: "Остання велика група приголосних, які зазнають впливу історичного йота [j] — це губні приголосні. За підручником О. Заболотного (7 клас, с. 52), сюди належать звуки [б], [п], [в], [м] та [ф], які отримують вставний звук [л']."
- find: "Знання цих звукових відповідностей — це справжній ключ до розширення вашого словникового запасу. Якщо ви бачите незнайоме дієслово «заряджати», ви можете відкинути суфікс, згадати чергування [дж] -> [д], і легко зрозуміти, що воно походить від знайомого кореня «зарядити»."
  replace: "Ці звукові відповідності допомагають швидко розпізнавати споріднені слова. Якщо ви бачите незнайоме дієслово «заряджати», ви можете відкинути суфікс, згадати чергування [дж] -> [д], і зрозуміти, що воно походить від кореня «зарядити»."
- find: "Тепер, коли ви розумієте механіку цих змін, українські дієслова більше не здаватимуться вам непередбачуваними. Ви озброєні знаннями, які дозволяють бачити прозору структуру мови. Час переходити до фінальної практики!"
  replace: "Ці регулярні зміни допомагають побачити прозору структуру українських дієслів. Переходимо до практики!"
- find: "<!-- INJECT_ACTIVITY: fill-in, Write the correct 1st person singular form of dental/sibilant verbs -->"
  replace: "<!-- INJECT_ACTIVITY: fill-in, Write the correct 1st person singular form of II дієвідміна verbs (e.g., сидіти -> я сидж___, носити -> я нош___) -->"
- find: "<!-- INJECT_ACTIVITY: match-up, Match velar infinitives with 1st person singular forms -->"
  replace: "<!-- INJECT_ACTIVITY: quiz, Identify which alternation type applies to a given verb: зубний, задньоязиковий, or губний + [л] -->"
- find: "<!-- INJECT_ACTIVITY: quiz, 1st person singular of labial verbs -->"
  replace: "<!-- INJECT_ACTIVITY: group-sort, Sort verbs by alternation type: [д]->[дж], [т]->[ч], [з]->[ж], [с]->[ш], губний+[л] -->"
- find: "<!-- INJECT_ACTIVITY: fill-in, Form imperfective verbs from perfective stems -->"
  replace: "<!-- INJECT_ACTIVITY: fill-in, Form imperfective verbs with -ати/-увати from perfective stems (e.g., простити -> прощ___ти, знизити -> знижув___ти) -->"
- find: "<!-- INJECT_ACTIVITY: quiz, Identify the correct verb form in context -->"
  replace: "<!-- INJECT_ACTIVITY: match-up, Match infinitive forms with their 1st person singular (e.g., водити <-> воджу, купити <-> куплю) -->"
- find: "<!-- INJECT_ACTIVITY: match-up, Global review of all alternation types -->"
  replace: "<!-- INJECT_ACTIVITY: error-correction, Find and fix conjugation errors in sentences (e.g., *я сижу -> я сиджу, *я робю -> я роблю) -->"
</fixes>
