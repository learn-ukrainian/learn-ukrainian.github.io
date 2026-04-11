## Linguistic Scan
3 errors found:
1. `здати все` (in the context of exams) is a calque from Russian "сдавать/сдать экзамен". The correct Ukrainian collocation is `скласти іспит` / `скласти все`.
2. `приймає усвідомлене рішення` is a literal calque from Russian "принимать решение". The correct Ukrainian idiom is `ухвалювати рішення`.
3. `поліцейському протоколі` uses the Russian-influenced adjective form; the standard Ukrainian adjective is `поліційний`.

## Exercise Check
The generated markers do not match the plan's `activity_hints`. 
- The plan requires exactly 6 exercises: `reading`, `essay-response`, `fill-in`, `error-correction`, `quiz`, and `match-up`.
- The writer injected 8 markers, including duplicates (`reading`, `fill-in`) and custom IDs (`essay-response-5`, `quiz-cause-purpose-complex`) that will fail in the pipeline. 
These need to be reorganized and corrected to exactly match the plan's inventory.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | Text incorrectly cites Авраменко Grade 8 as "підручнику для дев'ятого класу". The end of the module misses the specific plan point: "Preview: порядкові числівники і відмінки." Exercise marker counts/types deviate from the plan. |
| 2. Linguistic accuracy | 7/10 | Three calques/Russianisms present: "здати все" (скласти все), "приймає рішення" (ухвалює рішення), and "поліцейському" (поліційному). Otherwise, the grammar and case usages are highly accurate and natural. |
| 3. Pedagogical quality | 10/10 | Excellent flow from context to rule. The distinction between inner motivation (з) and external reaction (від) is explained perfectly with clear physical vs psychological examples. |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary items are naturally integrated into the prose and dialogue. |
| 5. Exercise quality | 6/10 | The writer invented custom IDs (`essay-response-5`, `quiz-cause-purpose-complex`), duplicated markers, and added 8 markers instead of the required 6. |
| 6. Engagement & tone | 10/10 | The tone is highly encouraging and professional ("золоте правило деколонізованої української граматики"), with a natural, academic yet accessible teacher voice. |
| 7. Structural integrity | 10/10 | Word count is solid at 4927 words, safely above the 4000 target. Headings are proper and markdown is clean. |
| 8. Cultural accuracy | 10/10 | Natural cultural integration ("Одеський університет", "проєкт громади"). No false claims. |
| 9. Dialogue & conversation quality | 9/10 | Dialogue is realistic and contextual, effectively demonstrating the cause/purpose structures, though it contains one calque ("здати все"). |

## Findings
[Dimension 2] [CRITICAL]
Location: Діалог: В Одеському університеті: `Мені дуже важливо здати все на відмінно`
Issue: "Здати іспити" or "здати все" (in the context of exams) is a calque from Russian "сдавать/сдать экзамен". The correct Ukrainian collocation is "скласти іспит/скласти все".
Fix: Replace `здати все` with `скласти все`.

[Dimension 2] [CRITICAL]
Location: Складні конструкції причини і мети: `наприклад у поліцейському протоколі, ви зустрінете конструкцію`
Issue: "Поліцейський" as an adjective is a Russianism/calque; the standard Ukrainian adjective is "поліційний".
Fix: Replace `у поліцейському протоколі` with `у поліційному протоколі`.

[Dimension 2] [CRITICAL]
Location: Причина: від та з: `У цьому другому випадку людина приймає усвідомлене рішення мовчати.`
Issue: "Приймати рішення" is a literal calque from Russian "принимать решение". The correct Ukrainian idiom is "ухвалювати рішення".
Fix: Replace `приймає усвідомлене рішення` with `ухвалює усвідомлене рішення`.

[Dimension 1] [MAJOR]
Location: Причина: від та з: `Олександр Авраменко у своєму підручнику для дев'ятого класу називає їх`
Issue: The plan explicitly cites Авраменко Grade 8 (p.86) for this concept, but the text incorrectly attributes it to the Grade 9 textbook.
Fix: Replace `дев'ятого класу` with `восьмого класу`.

[Dimension 1] [MAJOR]
Location: Підсумок: `стануть вашою природною другою натурою.`
Issue: The plan explicitly requires a preview at the end: "Preview: порядкові числівники і відмінки." This was completely omitted.
Fix: Add `А в наступному модулі ми розглянемо порядкові числівники і їх відмінювання.` at the end of the paragraph.

[Dimension 5] [MAJOR]
Location: Various markers throughout the text.
Issue: The injected markers do not match the `activity_hints` array from the plan. There are 8 markers instead of 6, duplicated types (`reading`, `fill-in`), and custom IDs (`essay-response-5`, `quiz-cause-purpose-complex`) which will cause pipeline validation errors.
Fix: Remove duplicate markers and standardize the remaining 6 IDs to exactly match the plan (`reading`, `fill-in`, `quiz`, `essay-response`, `error-correction`, `match-up`).

## Verdict: REVISE
The module is incredibly well-written with fantastic pedagogical depth, but it contains three critical calques ("здати іспити", "приймати рішення", "поліцейський"), a factual textbook attribution error (Grade 9 instead of Grade 8), an omitted preview from the plan, and broken activity markers. These must be corrected deterministically before the module can pass.

<fixes>
- find: "Мені дуже важливо здати все на відмінно"
  replace: "Мені дуже важливо скласти все на відмінно"
- find: "наприклад у поліцейському протоколі, ви зустрінете конструкцію"
  replace: "наприклад у поліційному протоколі, ви зустрінете конструкцію"
- find: "У цьому другому випадку людина приймає усвідомлене рішення мовчати."
  replace: "У цьому другому випадку людина ухвалює усвідомлене рішення мовчати."
- find: "Олександр Авраменко у своєму підручнику для дев'ятого класу називає їх"
  replace: "Олександр Авраменко у своєму підручнику для восьмого класу називає їх"
- find: "стануть вашою природною другою натурою."
  replace: "стануть вашою природною другою натурою. А в наступному модулі ми розглянемо порядкові числівники і їх відмінювання."
- find: "напрямок вашого руху.\n\n<!-- INJECT_ACTIVITY: reading -->\n<!-- INJECT_ACTIVITY: fill-in -->"
  replace: "напрямок вашого руху.\n\n<!-- INJECT_ACTIVITY: reading -->\n<!-- INJECT_ACTIVITY: fill-in -->\n<!-- INJECT_ACTIVITY: quiz -->"
- find: "під час будь-яких ділових дискусій.\n\n<!-- INJECT_ACTIVITY: essay-response-5 -->\n<!-- INJECT_ACTIVITY: error-correction -->"
  replace: "під час будь-яких ділових дискусій.\n\n<!-- INJECT_ACTIVITY: essay-response -->\n<!-- INJECT_ACTIVITY: error-correction -->\n<!-- INJECT_ACTIVITY: match-up -->"
- find: "різні граматичні ролі в українській мові.\n\n<!-- INJECT_ACTIVITY: match-up -->\n<!-- INJECT_ACTIVITY: fill-in -->\n\n## Складні конструкції причини і мети"
  replace: "різні граматичні ролі в українській мові.\n\n## Складні конструкції причини і мети"
- find: "справді багатою та природною.\n\n<!-- INJECT_ACTIVITY: quiz-cause-purpose-complex -->\n\n## Причина vs мета: розрізнення"
  replace: "справді багатою та природною.\n\n## Причина vs мета: розрізнення"
- find: "впевненого спілкування українською мовою у будь-яких життєвих ситуаціях.\n\n<!-- INJECT_ACTIVITY: reading -->\n\n## Підсумок"
  replace: "впевненого спілкування українською мовою у будь-яких життєвих ситуаціях.\n\n## Підсумок"
</fixes>
