## Linguistic Scan
Found Russianisms / non-standard forms (`машу`, `дрімлю` - contrary to VESUM data). Found a critical grammatical error about Ukrainian verbal endings (`-еть`). Found a minor grammatical disagreement (`задньоязиковий`). 

## Exercise Check
- `<!-- INJECT_ACTIVITY: fill-in, Write the correct 1st person singular form of dental/sibilant verbs -->`: Present, logically placed after Section 2.
- `<!-- INJECT_ACTIVITY: match-up, Match velar infinitives with 1st person singular forms -->`: Present, logically placed after Section 3.
- `<!-- INJECT_ACTIVITY: quiz, 1st person singular of labial verbs -->`: Present. Mismatches the plan hint (plan specified a quiz on identifying alternation types: dental, velar, or labial+[l]).
- `<!-- INJECT_ACTIVITY: fill-in, Form imperfective verbs from perfective stems -->`: Present, matches hint.
- `<!-- INJECT_ACTIVITY: quiz, Identify the correct verb form in context -->`: Present. Mismatches the plan hint (plan specified `error-correction` for conjugation errors).
- `<!-- INJECT_ACTIVITY: match-up, Global review of all alternation types -->`: Present. Mismatches the plan hint (plan specified `group-sort`).
Overall: 6 markers are present and well-placed, but 3 of them deviated from the specified `activity_hints` in focus or type.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | Missing the "друг -> друже" comparison in Section 3. Missing the decision flowchart in Section 6. Missing the self-check questions and M11 preview in Section 7. |
| 2. Linguistic accuracy | 7/10 | CRITICAL: Taught `-еть` as a Ukrainian 1st conjugation ending (Russianism). CRITICAL: Used non-standard forms `машу` and `дрімлю` (Russianisms) as standard examples, contradicting VESUM standard Ukrainian data. |
| 3. Pedagogical quality | 8/10 | Generally follows PPP well with clear examples, but teaching `-еть` as a Ukrainian ending is fundamentally damaging to the grammar explanation. |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary from the plan is smoothly integrated into the prose. |
| 5. Exercise quality | 8/10 | All 6 exercises are placed logically, but 3 of them changed the requested `type` or `focus` from the plan's `activity_hints` (e.g., using a quiz instead of error-correction, match-up instead of group-sort). |
| 6. Engagement & tone | 8/10 | Dialogue is good, but the text relies occasionally on meta-commentary ("Але зараз ми переходимо до іншої великої теми", "Як ми вже з'ясували"). |
| 7. Structural integrity | 10/10 | Clean markdown, appropriate H2 usage, word count is within range (3596 words). |
| 8. Cultural accuracy | 10/10 | No issues, culturally appropriate examples. |
| 9. Dialogue & conversation quality | 9/10 | The dialogue is effective at demonstrating the linguistic problem naturally, though slightly didactic. |

## Findings

[1. Plan adherence] [MAJOR]
Location: `Як ми вже з'ясували, у першій дієвідміні чергування, що виникло історично, часто охоплює всю парадигму (всіх осіб), а не лише першу особу однини.`
Issue: Section 3 is missing the explicit comparison between noun alternations (M09, `друг -> друже`) and verb alternations (`берегти -> бережу`), which was mandated in the plan.
Fix: Add the missing comparison to link back to M09.

[1. Plan adherence] [MAJOR]
Location: `Розуміння цієї різниці між першою та другою дієвідмінами дозволить вам уникати помилок і говорити правильно.`
Issue: Section 6 is missing the mandated "Decision flowchart for learners" to summarize the rules for when to apply alternations.
Fix: Insert the decision flowchart at the end of Section 6.

[1. Plan adherence] [MAJOR]
Location: `Час переходити до фінальної практики!`
Issue: Section 7 (Підсумок) is missing the "Self-check questions" and the "Preview: M11 (Спрощення приголосних)" mandated in the plan.
Fix: Insert the self-check questions and the preview of M11.

[2. Linguistic accuracy] [CRITICAL]
Location: `У дієсловах **першої дієвідміни** (які мають закінчення -еть, -уть, наприклад, пекти, писати)`
Issue: Factual grammatical error. Ukrainian verbs of I conjugation do NOT have the ending `-еть`. Russian has `-ет` (он печет), but Ukrainian uses `-е` (він пече) or `-уть`/`-ють` (вони печуть).
Fix: Change `-еть` to `-е` and `-уть` to `-уть або -ють`.

[2. Linguistic accuracy] [CRITICAL]
Location: `- **Махати** (to wave): \n  - Я **машу** тобі правою рукою. \n  - Ти **машеш** українським прапором. \n  - Птах **маше** великими крилами. \n  - Ми радісно **машемо** на прощання. \n  - Ви **машете** їм з іншого берега. \n  - Вони **машуть** із відчиненого вікна.`
Issue: Non-standard forms / Russianism. In standard Ukrainian, `махати` conjugates as `махаю`, `махаєш` (not `машу`, `машеш`, which is Russian). Although the plan erroneously included it, teaching it as standard is a factual linguistic error.
Fix: Replace the `Махати` paradigm with `Дихати` (`дишу`, `дишеш` - which natively has the `[х] -> [ш]` alternation in all persons). Also update the summary table.

[2. Linguistic accuracy] [CRITICAL]
Location: `| | **[м]** | **[мл']** | **дрімати** — я **дрімлю** (всі особи) |`
Issue: Non-standard form / Russianism. In standard Ukrainian, `дрімати` conjugates as `дрімаю` (not `дрімлю`). In addition, `[мл']` is an alternation that happens in the 1st person singular for II conjugation verbs (like `ломити`), not "всі особи" as listed.
Fix: Replace `дрімати` with `ломити` (which correctly has `ломлю` in the 1st person singular).

[2. Linguistic accuracy] [MINOR]
Location: `приголосні звуки, які мають назву задньоязиковий (velar`
Issue: Grammatical disagreement in number. "Звуки" is plural, so the adjective should be "задньоязикові".
Fix: Change "задньоязиковий" to "задньоязикові".

## Verdict: REVISE
The module has CRITICAL linguistic inaccuracies (teaching the Russian verbal ending `-еть` and the non-standard verb conjugations `машу` and `дрімлю`) and MAJOR plan adherence failures (missing the flowchart, self-check, and M09 comparison). The fixes are well-defined and can be applied deterministically via the `<fixes>` block.

<fixes>
- find: "а не лише першу особу однини."
  replace: "а не лише першу особу однини.\n\nЗгадайте чергування в іменниках (M09): слово «друг» у кличному відмінку змінюється на «друже» (перехід [г] у [ж]). Те саме фонетичне явище відбувається і в дієсловах: корінь «берег-» (як у слові «берегти») перетворюється на «береж-» («бережу»). Зміна приголосного абсолютно ідентична, відрізняється лише граматичний тригер (відмінкове закінчення іменника проти особового закінчення дієслова)."
- find: "дозволить вам уникати помилок і говорити правильно."
  replace: "дозволить вам уникати помилок і говорити правильно.\n\n### Алгоритм дій для чергування\n\nЩоб швидко визначити, чи потрібне чергування, використовуйте цей простий алгоритм:\n1. **Чи це дієслово другої дієвідміни?** -> Шукайте звуки [д, т, з, с, б, п, в, м].\n2. **Чи це форма першої особи однини («я»)?** -> Якщо так, застосовуйте чергування.\n3. **Чи це будь-яка інша форма (минулий час, наказовий спосіб, форма «ти/він/ми»)?** -> Використовуйте базовий приголосний.\n4. **Чи утворюєте ви недоконаний вид за допомогою -ати/-увати?** -> Застосовуйте чергування."
- find: "Час переходити до фінальної практики!"
  replace: "Час переходити до фінальної практики!\n\n### Перевірте себе\nДайте відповіді на запитання:\n1. Яке чергування відбувається у формі «я сиджу»?\n2. Чому в дієслові «роблю» з'являється звук [л']?\n3. Провідмінюйте дієслово «просити» в теперішньому часі.\n4. Утворіть недоконаний вид: простити, зарядити, знизити.\n\nУ наступному модулі (M11) ми розглянемо **спрощення приголосних** — ситуацію, коли скупчення приголосних спрощується шляхом повного випадання одного зі звуків."
- find: "(які мають закінчення -еть, -уть, наприклад, пекти, писати)"
  replace: "(які мають закінчення -е, -уть або -ють, наприклад, пекти, писати)"
- find: "- **Махати** (to wave): \n  - Я **машу** тобі правою рукою. \n  - Ти **машеш** українським прапором. \n  - Птах **маше** великими крилами. \n  - Ми радісно **машемо** на прощання. \n  - Ви **машете** їм з іншого берега. \n  - Вони **машуть** із відчиненого вікна."
  replace: "- **Дихати** (to breathe): \n  - Я **дишу** глибоко і спокійно. \n  - Ти **дишеш** свіжим гірським повітрям. \n  - Він важко **дише** після бігу. \n  - Ми **дишемо** на повні груди. \n  - Ви **дишете** вільно. \n  - Вони тихо **дишуть** уві сні."
- find: "| | **[х]** | **[ш]** | **махати** — я **машу** (всі особи), **колихати** — я **колишу** (всі особи) |"
  replace: "| | **[х]** | **[ш]** | **дихати** — я **дишу** (всі особи), **колихати** — я **колишу** (всі особи) |"
- find: "| | **[м]** | **[мл']** | **дрімати** — я **дрімлю** (всі особи) |"
  replace: "| | **[м]** | **[мл']** | **ломити** — я **ломлю** |"
- find: "приголосні звуки, які мають назву задньоязиковий (velar"
  replace: "приголосні звуки, які мають назву задньоязикові (velar"
</fixes>
