## Linguistic Scan
- Typo / text corruption: `українська граматикаقيقي пропонує вам одразу два рівноцінні варіанти побудови такого речення.`
- Typo: `перед важливою покупкою, обвно об'єктивно оцінюючи їх за ціною та загальною якістю?`
- Ungrammatical model sentence: `щоб результат був **найякісніше** *(the highest quality)* зроблений`

## Exercise Check
All 6 `INJECT_ACTIVITY` markers are present, correctly placed after the relevant teaching sections, and they map cleanly to the 6 `activity_hints` in the plan:
`fill-in-shopping-dialogues`, `quiz-transaction-phrases`, `sentence-builder-comparison`, `match-up-agent-workplace`, `dialogue-completion-complaint`, `free-write-service-review`.

No inline DSL exercise blocks are present in the prose, so there is no inline exercise logic to audit here.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All planned H2 sections are present and in order, but the module promises `три різні конструкції (за/від/ніж)` in `Підсумок` while the grammar explanation only teaches `за` and `ніж` in `На ринку`. |
| 2. Linguistic accuracy | 6/10 | Learner-facing text contains `граматикаقيقي`, `обвно`, and the bad model `щоб результат був **найякісніше** ... зроблений`. |
| 3. Pedagogical quality | 7/10 | The module gives many contextualized examples, but one key comparison pattern (`від`) is not actually taught before it is promised, and one grammar model is itself ungrammatical. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary is integrated naturally across sections: `готівка`, `чек`, `гарантія`, `розмір`, `посилка`, `обмін валют`, `курс`, `ремонт`, `бракований`. |
| 5. Exercise quality | 9/10 | The six exercise markers are spread through the module and come after the material they test; placement is good and nothing is clustered at the end. |
| 6. Engagement & tone | 9/10 | Strong teacher voice and concrete cultural detail, e.g. `Бессарабський ринок`, `Привоз`, and the bargaining paragraph in `На ринку`. |
| 7. Structural integrity | 8/10 | All sections are present and the pipeline word count is safely above target, but visible text defects remain: `граматикаقيقي` and `обвно`. |
| 8. Cultural accuracy | 7/10 | The prose overstates real-world claims: `Кожен українець має ... «Дія»` and return instructions say a receipt/passport are `стовідсотково` / `обов'язково` required. |
| 9. Dialogue & conversation quality | 9/10 | Dialogues are named, multi-turn, and functional; the market, repair, and complaint exchanges feel more natural than rote textbook ping-pong. |

## Findings
[Plan adherence] [SEVERITY: major]  
Location: `Підсумок` — `Can you compare products using three different constructions (за/від/ніж)?` versus `На ринку` — `Перший ... спосіб — ... «за» ... Другий ... спосіб — ... «ніж» ...`  
Issue: The module promises three comparison constructions, but only teaches two. `від` is not modeled in the explanatory section.  
Fix: Add one natural comparison example with `від` in the grammar explanation and update the “two variants” wording to match.

[Linguistic accuracy] [SEVERITY: critical]  
Location: `На ринку` — `українська граматикаقيقي пропонує вам одразу два рівноцінні варіанти побудови такого речення.`  
Issue: The sentence contains visible non-Ukrainian text corruption (`قيقي`).  
Fix: Replace the corrupted sentence with clean Ukrainian.

[Linguistic accuracy] [SEVERITY: critical]  
Location: `Підсумок` — `перед важливою покупкою, обвно об'єктивно оцінюючи їх за ціною та загальною якістю?`  
Issue: `обвно` is a typo in learner-facing prose.  
Fix: Remove the stray typo and keep only `об'єктивно`.

[Linguistic accuracy] [SEVERITY: critical]  
Location: `Послуги` — `щоб результат був **найякісніше** *(the highest quality)* зроблений`  
Issue: This is not good Ukrainian; the comparative/superlative model is malformed.  
Fix: Replace it with a grammatical form such as `щоб результат був якнайякісніше зроблений`.

[Cultural accuracy] [SEVERITY: major]  
Location: `Послуги` — `Сьогодні українська сфера послуг є однією з найбільш цифровізованих у світі... Кожен українець має державний **додаток** *(app/application)* «Дія»...`  
Issue: These are sweeping factual overclaims. Not every Ukrainian has `Дія`, and the “one of the most digitalized in the world” claim is unqualified.  
Fix: Soften to cautious, factual wording: many services are online; many people use `Дія`.

[Cultural accuracy] [SEVERITY: major]  
Location: `У магазині` — `Для успішного і швидкого повернення вам стовідсотково знадобиться ваш оригінальний паперовий чек... Також старший касир обов'язково попросить ваш особистий **паспорт**...`  
Issue: The prose presents one store procedure as a universal legal rule. That is too absolute for teaching material.  
Fix: Rephrase with hedging: a receipt or other proof of purchase is usually needed; staff may also ask for ID.

## Verdict: REVISE
REVISE. The module is structurally complete and strong on coverage, but it contains multiple critical learner-facing language defects plus major factual overgeneralizations in legal/cultural claims.

<fixes>
- find: "українська граматикаقيقي пропонує вам одразу два рівноцінні варіанти побудови такого речення."
  replace: "українська граматика пропонує вам одразу три природні варіанти побудови такого речення."
- find: "Другий абсолютно правильний і граматично точний спосіб — це використання популярного сполучника «ніж» та називного відмінка (Nominative). Наприклад, ви можете скласти таке речення: «Цей м'який домашній козячий сир **свіжіший, ніж той** фабричний твердий сир» *(This soft homemade goat cheese is fresher than that factory hard cheese)*."
  replace: "Другий абсолютно правильний і граматично точний спосіб — це використання популярного сполучника «ніж» та називного відмінка (Nominative). Наприклад, ви можете скласти таке речення: «Цей м'який домашній козячий сир **свіжіший, ніж той** фабричний твердий сир» *(This soft homemade goat cheese is fresher than that factory hard cheese)*. Є і третій природний варіант — конструкція з прийменником «від»: «Цей сир **свіжіший від того** фабричного» *(This cheese is fresher than that factory-made one)*."
- find: "перед важливою покупкою, обвно об'єктивно оцінюючи їх за ціною та загальною якістю?"
  replace: "перед важливою покупкою, об'єктивно оцінюючи їх за ціною та загальною якістю?"
- find: "щоб результат був **найякісніше** *(the highest quality)* зроблений"
  replace: "щоб результат був **якнайякісніше** *(as well as possible)* зроблений"
- find: "Сьогодні українська сфера послуг є однією з найбільш цифровізованих у світі. Більшість рутинних справ можна вирішити через смартфон. Кожен українець має державний **додаток** *(app/application)* «Дія», де зберігаються цифрові документи."
  replace: "Сьогодні в Україні багато послуг уже доступні онлайн. Чимало рутинних справ можна вирішити через смартфон. Багато людей користуються державним **додатком** *(app/application)* «Дія», де можуть зберігатися цифрові документи."
- find: "Для успішного і швидкого повернення вам стовідсотково знадобиться ваш оригінальний паперовий чек, який надійно доводить факт вашої реальної покупки саме в цьому торговому закладі. Також старший касир обов'язково попросить ваш особистий **паспорт** *(passport)* для правильного офіційного оформлення складної процедури повернення ваших коштів."
  replace: "Для успішного і швидкого повернення вам зазвичай потрібен чек або інший документ, що підтверджує факт покупки саме в цьому торговому закладі. Для оформлення повернення працівник магазину може також попросити документ, що посвідчує особу."
</fixes>