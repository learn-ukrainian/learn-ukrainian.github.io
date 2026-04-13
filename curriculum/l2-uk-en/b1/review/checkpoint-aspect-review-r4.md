## Linguistic Scan
Errors found:
- "Відкривайте зошити" is a calque from Russian "открывать тетрадь" (the correct Ukrainian phrase is "розгортати зошити").
- "на фоні" is a mild calque from Russian "на фоне" (the preferred Ukrainian phrasing is "на тлі").

## Exercise Check
All exercise markers are present and correctly placed:
- `<!-- INJECT_ACTIVITY: quiz-aspect-identification -->` (Matches quiz)
- `<!-- INJECT_ACTIVITY: fill-in-past-aspect -->` (Matches fill-in)
- `<!-- INJECT_ACTIVITY: group-sort-future-imperative -->` (Matches group-sort)
- `<!-- INJECT_ACTIVITY: error-correction-imperative -->` (Matches error-correction)
- `<!-- INJECT_ACTIVITY: match-up-negation-meaning -->` (Matches match-up)
- `<!-- INJECT_ACTIVITY: open-writing-aspect-check -->` (Matches open-writing)

The markers test the material appropriately based on the section they follow.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7 | Missing 5 required vocabulary words ("видова пара", "результативність", "діагностика", "повторення", "контрольна робота") and 2 recommended terms ("синтетичний майбутній", "аналітичний майбутній"). Also completely missed the explicit "Самоперевірка" summary block from the plan's section 4. |
| 2. Linguistic accuracy | 8 | Found a critical calque: "Відкривайте зошити" instead of "Розгортайте зошити". Also found a minor calque "на фоні" instead of "на тлі". Otherwise, excellent grammar. |
| 3. Pedagogical quality | 10 | Exceptional explanations of aspect using analogies like the "wide-angle camera shot" and "event chain". Concepts are broken down clearly with great examples. |
| 4. Vocabulary coverage | 6 | Many required terms associated with the "test/checkpoint" nature of the module were not used in the Ukrainian prose. |
| 5. Exercise quality | 10 | All 6 markers from the plan are present and placed logically after their corresponding topics. |
| 6. Engagement & tone | 10 | Very natural, encouraging, and engaging teacher persona without crossing into gamified or corporate speak. |
| 7. Structural integrity | 10 | Word count is 5244 (well over 4000). All headings are present and logical. |
| 8. Cultural accuracy | 10 | Good use of natural Ukrainian logic rather than Russian comparisons. Explains cultural politeness in commands (imperfective vs perfective imperative) beautifully. |
| 9. Dialogue & conversation quality | 9 | The initial dialogue is authentic and perfectly sets up the diagnostic aspect choices. |

## Findings
[2. Linguistic accuracy] [SEVERITY: critical]
Location: `Коли викладач заходить до аудиторії, він може сказати студентам: «Відкривайте зошити і пишіть».`
Issue: "Відкривати зошит" is a calque from Russian "открывать тетрадь". In Ukrainian, one should use "розгортати" for books and notebooks.
Fix: Change "Відкривайте" to "Розгортайте".

[2. Linguistic accuracy] [SEVERITY: minor]
Location: `На фоні цієї статичної картини раптом починається рух`
Issue: "На фоні" is a mild calque from Russian. "На тлі" is the preferred and more natural Ukrainian phrasing in this context.
Fix: Change "На фоні" to "На тлі".

[1. Plan adherence] [SEVERITY: major]
Location: `:::info\n**Grammar box** — Three forms of the future tense.`
Issue: The text fails to introduce the recommended vocabulary "синтетичний майбутній" and "аналітичний майбутній" when discussing the forms of the future tense, referring to them only in English.
Fix: Add the terms to the grammar box text.

[1. Plan adherence] [SEVERITY: major]
Location: `> * *Conditional mood: The verb aspect depends entirely on the nature of the hypothetical action: whether it is a continuous imaginary state or a one-time fantastic event.*` (End of the text)
Issue: The text completely misses the explicitly required "Самоперевірка" (Self-check) task section from the plan. It also misses 5 required vocabulary words related to the test framing: "видова пара", "результативність", "діагностика", "повторення", "контрольна робота".
Fix: Insert the missing "Самоперевірка (Діагностика)" section with the 4 numbered tasks from the plan immediately before the final activity marker. This will also inject the missing required vocabulary naturally.

## Verdict: REVISE
The module requires revision because of a linguistic calque ("відкривайте зошити") which constitutes a critical error, and major plan adherence issues regarding missing required vocabulary and the missing "Самоперевірка" section.

<fixes>
- find: "На фоні цієї статичної картини раптом починається рух"
  replace: "На тлі цієї статичної картини раптом починається рух"
- find: "Коли викладач заходить до аудиторії, він може сказати студентам: «Відкривайте зошити і пишіть»."
  replace: "Коли викладач заходить до аудиторії, він може сказати студентам: «Розгортайте зошити і пишіть»."
- find: ":::info\n**Grammar box** — Three forms of the future tense.\nThe perfective aspect uses only the simple form («напишу», «прочитаю») to focus on the final result. The imperfective aspect uses either the compound form with an auxiliary verb («буду писати») or the uniquely Ukrainian complex form with a suffix («писатиму») to focus on the process.\n:::"
  replace: ":::info\n**Grammar box** — Three forms of the future tense.\nThe perfective aspect uses only the synthetic future (**синтетичний майбутній**: «напишу», «прочитаю») to focus on the final result. The imperfective aspect uses either the analytic future (**аналітичний майбутній**: «буду писати») or the uniquely Ukrainian complex form with a suffix («писатиму») to focus on the process.\n:::"
- find: "> * *Conditional mood: The verb aspect depends entirely on the nature of the hypothetical action: whether it is a continuous imaginary state or a one-time fantastic event.*\n\n<!-- INJECT_ACTIVITY: open-writing-aspect-check -->"
  replace: "> * *Conditional mood: The verb aspect depends entirely on the nature of the hypothetical action: whether it is a continuous imaginary state or a one-time fantastic event.*\n\n### Самоперевірка (Діагностика)\n\nДля повторення та закріплення матеріалу виконайте ці завдання. Це ваша контрольна робота:\n\n1. Перекажіть свій минулий тиждень, чергуючи доконаний і недоконаний вид (мінімум 8 дієслів).\n2. Складіть 3 видові пари наказів: загальна інструкція (недоконаний вид) vs конкретна команда (доконаний вид).\n3. Поясніть різницю та результативність у парах: «Я не читав цю книжку» vs «Я не прочитав цю книжку».\n4. Складіть 2 умовні речення з різним видом дієслова.\n\n> *Self-check (Diagnostics)*\n> *To review and consolidate the material, complete these tasks. This is your test:*\n> *1. Retell your past week, alternating perfective and imperfective aspects (minimum 8 verbs).*\n> *2. Make 3 aspectual pairs of commands: general instruction (imperfective) vs specific command (perfective).*\n> *3. Explain the difference and resultativity in the pairs: \"I didn't read this book\" vs \"I didn't finish reading this book\".*\n> *4. Make 2 conditional sentences with different verb aspects.*\n\n<!-- INJECT_ACTIVITY: open-writing-aspect-check -->"
</fixes>