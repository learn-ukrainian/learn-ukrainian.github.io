## Linguistic Scan
Errors found:
- Russianism: "офіційній робочій обстановці" ("обстановка" in the sense of atmosphere/environment is a calque; natural Ukrainian prefers "робочому середовищі" or "робочій атмосфері"). 

## Exercise Check
- The marker `<!-- INJECT_ACTIVITY: group-sort-categories -->` appears **twice** (once improperly at the end of section 1, and again at the end with a concatenated ID).
- The marker `<!-- INJECT_ACTIVITY: fill-in-imperative-forms -->` has slightly different focus text from the plan.
- The marker `<!-- INJECT_ACTIVITY: match-up-situations -->` appears **twice** (improperly placed after section 2, and again at the end with a concatenated ID).
- The markers placed at the end of the text use extremely long and unwieldy IDs: `match-up-match-situations-recipe-step-classroom-rule-polite-request-wish-to-correct-imperative-form` and `group-sort-sort-imperative-forms-into-and-direct-polite-categories`.
- Total markers generated: 8. Total planned: 6. The extra/misplaced markers will be removed and the IDs will be fixed.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Missed the explicit plan point and vocabulary hint for "Не забувай (impf) вимикати світло" in the dialogue section, incorrectly replacing it with "акуратно повісити". |
| 2. Linguistic accuracy | 9/10 | High quality with detailed morphological explanations. However, contains one Russianism ("робочій обстановці"). |
| 3. Pedagogical quality | 10/10 | Excellent pedagogical flow. Concepts like aspect, negation, and polite softening are contextualized brilliantly through realistic scenarios. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary is seamlessly incorporated, but the recommended word "вимикати" is missing from the prose. |
| 5. Exercise quality | 6/10 | DEDUCTION: Injected 8 markers instead of the planned 6, creating duplicates (`group-sort` and `match-up`). Placed `match-up` after section 2 despite it testing content from sections 3 and 5. Also utilized concatenated, non-standard IDs at the end. |
| 6. Engagement & tone | 10/10 | The tone is highly encouraging and natural ("Вітаю вас!", "чудово демонструє"). Avoids corporate or purely mechanical language. |
| 7. Structural integrity | 10/10 | Word count is above the target of 4000 (4422 words). Markdown formatting is clean, and section progression is strictly adhered to. |
| 8. Cultural accuracy | 10/10 | Outstanding decolonization focus (explicitly correcting the calque "пішли" vs "ходімо"). Integrates Franko and folk sayings authentically. |
| 9. Dialogue & conversation quality | 9/10 | Dialogues are lifelike and illustrative. Minor deduction due to the first dialogue missing the planned grammar contrast with "вимикати". |

## Findings
[2. Linguistic accuracy] [Major]
Location: "дуже часто використовується у сучасній сфері обслуговування чи в офіційній робочій обстановці. Якщо ви гостинно приймаєте"
Issue: "обстановка" in this context is a Russianism/calque; natural Ukrainian prefers "середовище" or "атмосфера".
Fix: Replace with "офіційному робочому середовищі".

[5. Exercise quality] [Major]
Location: "<!-- INJECT_ACTIVITY: group-sort-categories --> [group-sort, sort imperative forms into conjugation groups and check for correct soft sign usage, 10 items]\n<!-- INJECT_ACTIVITY: fill-in-imperative-forms --> [fill-in, form the correct imperative (singular/plural/soft sign) from the given infinitive, 10 items]"
Issue: Extra group-sort marker injected in section 1 with wrong focus text. Fill-in focus text doesn't exactly match the plan.
Fix: Delete the group-sort marker here and correct the fill-in focus text.

[5. Exercise quality] [Major]
Location: "небажанням втручатися.\n\n<!-- INJECT_ACTIVITY: match-up-situations -->\n\n## Вид дієслова в наказовому способі"
Issue: Extra/misplaced match-up marker. Match-up tests concepts from sections 3 and 5 (recipe step, classroom rules), so it shouldn't be placed after section 2.
Fix: Delete this extra marker.

[5. Exercise quality] [Minor]
Location: "<!-- INJECT_ACTIVITY: match-up-match-situations-recipe-step-classroom-rule-polite-request-wish-to-correct-imperative-form -->\n<!-- INJECT_ACTIVITY: group-sort-sort-imperative-forms-into-and-direct-polite-categories -->"
Issue: IDs are excessively long and unwieldy concatenations.
Fix: Replace with standard IDs `match-up-situations` and `group-sort-categories`.

[1. Plan adherence] [Major]
Location: "> — **Мама:** Але **не забувай** *(do not forget / impf)* акуратно **повісити** *(to hang / pf)* шкільну куртку в шафу. А потім одразу **сідай** *(sit down / impf)* їсти, твій обід уже чекає на столі."
Issue: Missed the explicit plan point and vocabulary hint for "Не забувай (impf) вимикати світло".
Fix: Replace "акуратно повісити (to hang / pf) шкільну куртку в шафу" with "вимикати (to turn off / impf) світло у своїй кімнаті".

## Verdict: REVISE
The module is exceptionally written and offers a very high-quality explanation of the imperative aspect logic. However, the exercise markers were duplicated and misplaced, a required plan point / vocabulary word ("вимикати") was omitted, and one Russianism ("обстановка") slipped through. A targeted deterministic revision will make this module perfectly ready for publishing.

<fixes>
- find: "<!-- INJECT_ACTIVITY: group-sort-categories --> [group-sort, sort imperative forms into conjugation groups and check for correct soft sign usage, 10 items]\n<!-- INJECT_ACTIVITY: fill-in-imperative-forms --> [fill-in, form the correct imperative (singular/plural/soft sign) from the given infinitive, 10 items]"
  replace: "<!-- INJECT_ACTIVITY: fill-in-imperative-forms --> [fill-in, form the correct imperative (choose aspect, person, soft sign) in sentence context, 10 items]"
- find: "небажанням втручатися.\n\n<!-- INJECT_ACTIVITY: match-up-situations -->\n\n## Вид дієслова в наказовому способі"
  replace: "небажанням втручатися.\n\n## Вид дієслова в наказовому способі"
- find: "понад століття.\n\n<!-- INJECT_ACTIVITY: match-up-match-situations-recipe-step-classroom-rule-polite-request-wish-to-correct-imperative-form -->\n<!-- INJECT_ACTIVITY: group-sort-sort-imperative-forms-into-and-direct-polite-categories -->\n\n## Підсумок та перехід до M21"
  replace: "понад століття.\n\n<!-- INJECT_ACTIVITY: match-up-situations -->\n<!-- INJECT_ACTIVITY: group-sort-categories -->\n\n## Підсумок та перехід до M21"
- find: "> — **Мама:** Але **не забувай** *(do not forget / impf)* акуратно **повісити** *(to hang / pf)* шкільну куртку в шафу. А потім одразу **сідай** *(sit down / impf)* їсти, твій обід уже чекає на столі."
  replace: "> — **Мама:** Але **не забувай** *(do not forget / impf)* **вимикати** *(to turn off / impf)* світло у своїй кімнаті. А потім одразу **сідай** *(sit down / impf)* їсти, твій обід уже чекає на столі."
- find: "дуже часто використовується у сучасній сфері обслуговування чи в офіційній робочій обстановці. Якщо ви гостинно приймаєте"
  replace: "дуже часто використовується у сучасній сфері обслуговування чи в офіційному робочому середовищі. Якщо ви гостинно приймаєте"
</fixes>
