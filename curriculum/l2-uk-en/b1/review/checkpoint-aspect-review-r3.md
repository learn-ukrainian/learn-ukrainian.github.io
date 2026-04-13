## Linguistic Scan
No linguistic errors found. The explanations of aspect (тло vs. послідовність, заборона vs. попередження у запереченні) are native-level, highly accurate, and pedagogically outstanding. No Russianisms, Surzhyk, or Calques were identified. 

## Exercise Check
All activity markers from the plan are present and test the appropriate content, but there is one logical placement issue:
- `<!-- INJECT_ACTIVITY: error-correction -->` tests "розповіді, наказі, запереченні", meaning it should be placed *after* the "Вид і заперечення" section. Currently, it is placed before it. This will be fixed by moving the marker down.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | The `Самоперевірка` questions outlined explicitly in the plan were omitted from the text (though technically satisfied by the `open-writing` activity hint). The word target was easily met (4681 words vs 4000). |
| 2. Linguistic accuracy | 10/10 | Outstanding linguistic accuracy. The distinctions between «не відчиняй» (заборона) and «не відчиніть» (попередження) are flawless. No Russianisms or calques identified. |
| 3. Pedagogical quality | 10/10 | Very strong pedagogy. Concepts are clearly structured. The transition from "тло" vs "ланцюг подій" features an excellent visual metaphor ("зациклене відео" vs "швидкі фотографії"). |
| 4. Vocabulary coverage | 10/10 | All required vocabulary from the plan (доконаний вид, недоконаний вид, видова пара, тло розповіді, послідовність подій, результативність, тривалість тощо) is used natively in context. |
| 5. Exercise quality | 9/10 | The `<!-- INJECT_ACTIVITY: error-correction -->` marker tests "розповіді, наказі, заперечення" according to the plan, but it was incorrectly placed before the "Вид і заперечення" section. |
| 6. Engagement & tone | 9/10 | The text uses an explicitly penalized gamified opener: "Вітаю вас на діагностичній контрольній роботі рівня B1!". The rest of the tone is encouraging and appropriate. |
| 7. Structural integrity | 10/10 | Headers are correct. Excellent pacing. Word count exceeds the target naturally without filler. No stray tags. |
| 8. Cultural accuracy | 10/10 | Highly accurate handling of Ukrainian grammar nuances. Contrasting English tense-focus with Ukrainian result-focus represents excellent decolonized pedagogy. |
| 9. Dialogue & conversation quality | 10/10 | Excellent multi-turn dialogues with named speakers (Олена, Марко, Мама, Син, Керівник, Співробітник) that effectively demonstrate grammatical points in natural, non-transactional contexts. |

## Findings

[Engagement & tone] [minor]
Location: `Вітаю вас на діагностичній контрольній роботі рівня B1! Сьогодні ми перевіримо`
Issue: Uses a gamified/self-congratulatory opener, which is explicitly penalized in the review prompt ("Welcome to A2!"). 
Fix: Remove the greeting and start directly with the objective.

[Exercise quality] [major]
Location: `<!-- INJECT_ACTIVITY: group-sort -->\n<!-- INJECT_ACTIVITY: error-correction -->\n\n## Вид і заперечення`
Issue: The `error-correction` exercise relies on knowledge of aspect negation, but the marker is placed before the section that teaches negation.
Fix: Move the `error-correction` marker down to sit below the `match-up` marker, directly before the final section.

[Plan adherence] [major]
Location: `*   **Умова**: Правильний вибір виду повністю залежить від характеру вашої гіпотетичної дії (одноразова подія чи тривалий процес у вашій уяві).\n\n<!-- INJECT_ACTIVITY: open-writing -->`
Issue: The final four `Самоперевірка` reflection questions detailed in the `content_outline` of the plan were not explicitly included in the text summary.
Fix: Insert the `Самоперевірка` heading and its 4 questions directly before the `open-writing` marker.

## Verdict: REVISE
The module is phenomenally written and features exceptional grammar explanations, but has a few structural issues (a misplaced exercise marker, a missing summary checklist, and a minor tone infraction) that must be fixed via deterministic find/replace before publishing.

<fixes>
- find: "Вітаю вас на діагностичній контрольній роботі рівня B1! Сьогодні ми перевіримо"
  replace: "Сьогодні ми перевіримо"
- find: "<!-- INJECT_ACTIVITY: group-sort -->\n<!-- INJECT_ACTIVITY: error-correction -->\n\n## Вид і заперечення"
  replace: "<!-- INJECT_ACTIVITY: group-sort -->\n\n## Вид і заперечення"
- find: "<!-- INJECT_ACTIVITY: match-up -->\n\n## Вид в умовному способі та підсумок"
  replace: "<!-- INJECT_ACTIVITY: match-up -->\n<!-- INJECT_ACTIVITY: error-correction -->\n\n## Вид в умовному способі та підсумок"
- find: "*   **Умова**: Правильний вибір виду повністю залежить від характеру вашої гіпотетичної дії (одноразова подія чи тривалий процес у вашій уяві).\n\n<!-- INJECT_ACTIVITY: open-writing -->"
  replace: "*   **Умова**: Правильний вибір виду повністю залежить від характеру вашої гіпотетичної дії (одноразова подія чи тривалий процес у вашій уяві).\n\n### Самоперевірка\n\nПеред виконанням фінального завдання виконайте цю швидку самоперевірку:\n1. Перекажіть свій минулий тиждень, чергуючи доконаний і недоконаний вид (мінімум 8 дієслів).\n2. Складіть 3 пари наказів: загальна інструкція (недоконаний) vs конкретна команда (доконаний).\n3. Поясніть різницю: «Я не читав цю книжку» vs «Я не прочитав цю книжку».\n4. Складіть 2 умовні речення з різним видом дієслова.\n\n<!-- INJECT_ACTIVITY: open-writing -->"
</fixes>