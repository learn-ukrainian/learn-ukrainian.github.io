## Linguistic Scan
Errors found:
1. **Typo:** "жижлиттєвому" instead of "життєвому".
2. **Grammar fact error:** The text states that "по суботах" uses the "Dative plural form". This is incorrect; "суботах" is Locative (місцевий) plural.
3. **Russianism (Calque):** "знаходиться" and "знаходитеся" used for physical location (a direct calque of the Russian "находиться").

## Exercise Check
- `<!-- INJECT_ACTIVITY: fill-in-home-cases -->` (matches `fill-in` activity in plan). Placed correctly after Scenario 1. Tests correct cases for rooms and furniture.
- `<!-- INJECT_ACTIVITY: quiz-daily-routine -->` (matches `quiz` activity in plan). Placed correctly after Scenario 2. Tests cases in daily routines.
- `<!-- INJECT_ACTIVITY: match-up-activities -->` (matches `match-up` activity in plan). Placed correctly after Scenario 2.
- `<!-- INJECT_ACTIVITY: error-correction-cases -->` (matches `error-correction` activity in plan). Placed correctly after Scenario 3.

All 4 expected markers are present, correctly placed after the concepts are taught, and match the plan perfectly.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Missed specific guest questions from Scenario 1 ("А скільки у вас кімнат?", "Що на балконі?", "Де ви поставили книжки?"). Missed questions from Scenario 3 ("Хто у вас готує вечерю?", "Ви снідаєте вдома чи на роботі?"). |
| 2. Linguistic accuracy | 7/10 | The text incorrectly states "the preposition «по» with the Dative plural form" for "по суботах" (it is Locative plural). Uses the calque "знаходиться/знаходитеся" for physical location. Contains a typo "жижлиттєвому". |
| 3. Pedagogical quality | 9/10 | Excellent PPP flow. Grammar is explained with clear contrasting examples ("У новій квартирі є великий балкон. У старій квартирі немає великого балкона."). |
| 4. Vocabulary coverage | 9/10 | All required vocabulary is used naturally. However, the recommended word "пригощатися" is completely missing from the text. |
| 5. Exercise quality | 10/10 | All 4 activity markers are present, matching the types and focus in the plan, and are placed directly after the relevant teaching sections. |
| 6. Engagement & tone | 10/10 | Natural teacher phrasing ("Let's look closely at the vocabulary", "Now let's furnish our empty home"). Tone is warm and engaging without corporate gamification. |
| 7. Structural integrity | 10/10 | Clean markdown, word count of 2614 exceeds the 2000 target, all H2 headings match the plan exactly. |
| 8. Cultural accuracy | 10/10 | Accurate representation of Ukrainian hospitality ("Господарі відразу запрошують їх до столу"). Correct explanation of culturally polite forms like "Мені подобається" instead of literal "Я люблю". |
| 9. Dialogue & conversation quality | 9/10 | Dialogues represent realistic situations (video tour, visiting friends) with natural conversational flow, though some specific plan questions were omitted. |

## Findings

[Plan adherence] [major]
Location: Scenario 1 dialogue (`> — Онлайн-друг: Клас! Ти вже живеш у цій квартирі?`)
Issue: Specific guest questions from the plan ("А скільки у вас кімнат?", "Що на балконі?", "Де ви поставили книжки?") are missing from the text.
Fix: Add the missing questions into the dialogue.

[Plan adherence] [major]
Location: Scenario 3 text (`Вони цікавляться і запитують: «А о котрій годині ви встаєте вранці?». Ви можете детально відповісти: «Мій день починається рано, а мій чоловік прокидається пізно».`)
Issue: Missed questions from the plan for Scenario 3 ("Хто у вас готує вечерю?", "Ви снідаєте вдома чи на роботі?").
Fix: Inject the missing questions into the explanation of table talk.

[Vocabulary coverage] [major]
Location: Scenario 3 text (`Господарі завжди готують і пропонують багато різних страв. Усі почуваються дуже комфортно у цій приємній атмосфері.`)
Issue: The recommended vocabulary word "пригощатися" is missing from the text, despite being highlighted in the plan.
Fix: Add "Пригощайтеся!" and "пригощаються" to the description of hosts offering food.

[Linguistic accuracy] [critical]
Location: `If you want to describe a habitual action that happens every Saturday, you can use the preposition «по» with the Dative plural form.`
Issue: Factual linguistic error. The preposition "по" for repeated time actions (like "по суботах") takes the Locative (місцевий) plural, not Dative.
Fix: Change "Dative plural" to "Locative plural".

[Linguistic accuracy] [critical]
Location: `Це завдання чудово допоможе вам практикувати нові слова у реальному жижлиттєвому контексті.`
Issue: Typo "жижлиттєвому" creates a non-existent word.
Fix: Change "жижлиттєвому" to "життєвому".

[Linguistic accuracy] [minor]
Location: `Ми також почуємо, як сказати, де саме ви знаходитеся.` and `Супер! А де знаходиться кухня (kitchen)?`
Issue: "Знаходитися" used for physical location is a common Russianism/calque (находиться).
Fix: Replace with "перебуваєте" and "розташована" respectively.

## Verdict: REVISE
The module is structurally excellent and flows very well, hitting word counts and keeping an engaging tone. However, it contains a critical factual error regarding Ukrainian case rules (claiming "по суботах" is Dative plural instead of Locative), a critical typo ("жижлиттєвому"), and a few minor Russianisms ("знаходиться"). Several specific vocabulary items and dialogue lines from the plan were also missed. These must be fixed via deterministic replacement.

<fixes>
- find: "If you want to describe a habitual action that happens every Saturday, you can use the preposition «по» with the Dative plural form."
  replace: "If you want to describe a habitual action that happens every Saturday, you can use the preposition «по» with the Locative plural form."
- find: "Це завдання чудово допоможе вам практикувати нові слова у реальному жижлиттєвому контексті."
  replace: "Це завдання чудово допоможе вам практикувати нові слова у реальному життєвому контексті."
- find: "Ми також почуємо, як сказати, де саме ви знаходитеся."
  replace: "Ми також почуємо, як сказати, де саме ви перебуваєте."
- find: "> — **Онлайн-друг:** Супер! А де знаходиться **кухня** *(kitchen)*?"
  replace: "> — **Онлайн-друг:** Супер! А де розташована **кухня** *(kitchen)*?"
- find: |
    > — **Онлайн-друг:** Клас! Ти вже живеш у цій квартирі?
    > — **Мешканець:** Так, я вже сплю у спальні, але тут ще є багато роботи.
  replace: |
    > — **Онлайн-друг:** Клас! Ти вже живеш у цій квартирі? **А скільки у вас кімнат?**
    > — **Мешканець:** Тут три кімнати. Я вже сплю у спальні, але тут ще є багато роботи.
    > — **Онлайн-друг:** **Що на балконі? Де ви поставили книжки?**
    > — **Мешканець:** На балконі поки що порожньо, а книжки я поклав у шафу.
- find: "Вони цікавляться і запитують: «А о котрій годині ви встаєте вранці?». Ви можете детально відповісти: «Мій день починається рано, а мій чоловік прокидається пізно». Такі спокійні розмови допомагають краще пізнати одне одного."
  replace: "Вони цікавляться і запитують: «А о котрій годині ви встаєте вранці?». Вони також можуть спитати: «**Хто у вас готує вечерю?**» або «**Ви снідаєте вдома чи на роботі?**». Ви можете детально відповісти: «Мій день починається рано, а снідаю я зазвичай вдома». Такі спокійні розмови допомагають краще пізнати одне одного."
- find: "Господарі завжди готують і пропонують багато різних страв. Усі почуваються дуже комфортно у цій приємній атмосфері."
  replace: "Господарі завжди готують багато різних страв і радісно кажуть: «**Пригощайтеся!**» *(Help yourself!)*. Гості із задоволенням **пригощаються** *(help themselves)* смачною їжею. Усі почуваються дуже комфортно у цій приємній атмосфері."
</fixes>
