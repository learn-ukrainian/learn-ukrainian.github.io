## Linguistic Scan
No Russianisms, Surzhyk, paronym errors, or Russian characters (`ы э ё ъ`) found.

Confirmed issues:
- `Avoid Russian-sounding words like "гостинна", which are incorrect in standard Ukrainian.`  
  `гостинна` exists in VESUM as a valid Ukrainian word form (`гостинний`, adj.). The module’s claim is too broad and teaches a false lexical rule.
- `Yes, in Ukrainian we say "on the kitchen" rather than "in the kitchen"!`  
  This is factually wrong. `на кухні` translates naturally as `in the kitchen`, not `on the kitchen`.
- `We contrast weekdays and weekends using the Locative case. "On weekdays" is «у будні», and "on weekends" is «у вихідні».`  
  This case explanation is not defensible as stated. The forms are syncretic/ambiguous, so they should not be taught here as a clean Locative rule.

## Exercise Check
- `fill-in-home-description` appears after Scenario 1 and matches the plan’s `fill-in` hint.
- `quiz-daily-routine-cases` and `match-up-routine-times` appear after Scenario 2 and match the `quiz` and `match-up` hints.
- `error-correction-cases-routine` appears after Scenario 3 and matches the `error-correction` hint.
- Total markers: 4/4. Distribution is appropriate and not clustered at the end.
- No inline DSL exercise blocks to audit.
- No exercise-placement issues found.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All four planned sections are present and the required/recommended vocabulary is used naturally, but the plan explicitly calls for `Dat. (for whom)` in the speaking-task checklist and `дякую господарям (Dat.)` in Scenario 3; both are missing from the generated prose. |
| 2. Linguistic accuracy | 6/10 | Three confirmed teaching errors: `гостинна` is called “incorrect in standard Ukrainian”; `Yes, in Ukrainian we say "on the kitchen"` is false; `We contrast weekdays and weekends using the Locative case` overstates the grammar. |
| 3. Pedagogical quality | 7/10 | The module generally teaches through context and examples, but the incorrect `on the kitchen` note and the overconfident `Locative case` claim mis-teach core grammar, and the missing Dative scaffold weakens the final synthesis task. |
| 4. Vocabulary coverage | 10/10 | All required items appear in prose: `помешкання`, `кімната`, `кухня`, `спальня`, `вітальня`, `меблі`, `розпорядок дня`, `вставати`, `снідати`, `лягати спати`; recommended items also appear: `балкон`, `коридор`, `килим`, `пригощатися`, `господар`. |
| 5. Exercise quality | 10/10 | Four markers align with the four `activity_hints`, each marker follows the relevant teaching section, and the spread across the module is good. |
| 6. Engagement & tone | 9/10 | Mostly warm and teacherly, with concrete situations like housewarming, hosting, and daily routine. The prose stays usable for learners despite one over-pushy vocabulary tip. |
| 7. Structural integrity | 10/10 | All planned H2 sections are present and ordered correctly; the pipeline word count is 2955, which is safely above the 2000 target; expected inject markers are intact. |
| 8. Cultural accuracy | 9/10 | The home/guesting material is Ukrainian-centered and concrete (`новосілля`, `гостинці`, `двокімнатна квартира` note). The main weakness is linguistic framing, not cultural framing. |
| 9. Dialogue & conversation quality | 9/10 | Dialogues use named speakers, plausible home-tour and dinner contexts, and reasonable conversational moves rather than anonymous drill lines. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Always use the beautiful Ukrainian word **вітальня** for your living room. Avoid Russian-sounding words like "гостинна", which are incorrect in standard Ukrainian.`  
Issue: `гостинна` is a valid Ukrainian word form in VESUM. The problem here is room naming, not word existence. As written, the module falsely teaches that the word itself is non-standard.  
Fix: Rephrase the tip to say that `вітальня` is the standard noun for “living room” and avoid calling `гостинна` categorically incorrect.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Yes, in Ukrainian we say "on the kitchen" rather than "in the kitchen"!`  
Issue: This teaches a false translation. `на кухні` is naturally translated as `in the kitchen` in English.  
Fix: Replace the sentence with an explanation about Ukrainian preposition choice without changing the English translation.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `We contrast weekdays and weekends using the Locative case. "On weekdays" is «у будні», and "on weekends" is «у вихідні».`  
Issue: The case claim is overconfident and misleading. These time expressions should be taught as standard phrases here, not as a simple Locative rule.  
Fix: Rephrase this as a time-expression note without naming the case.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `За столом друзі часто говорять про свій розпорядок дня... У цій простій розмові ми бачимо багато відмінків разом.`  
Issue: The plan’s Scenario 3 outline explicitly includes a Dative example (`дякую господарям (Dat.)`), but the generated prose never supplies it.  
Fix: Add a short Dative example sentence in this paragraph.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `Use the Nominative case to list what exists in your home. Use the Genitive case to state what is missing or to specify quantities. Use the Accusative case to show where you go during the day. Use the Instrumental case to explain how you travel or who you spend your time with. Finally, use the Locative case...`  
Issue: The plan’s speaking-task checklist explicitly requires Dative (`Dat. (for whom)`), but the generated checklist omits it.  
Fix: Add a Dative sentence to the checklist.

## Verdict: REVISE
Three critical linguistic/grammar findings make this unshippable as-is, but the module does not need a full rebuild. Small deterministic fixes will resolve the confirmed teaching errors and restore the missing Dative coverage from the plan.

<fixes>
- find: |
    :::tip
    Always use the beautiful Ukrainian word **вітальня** for your living room. Avoid Russian-sounding words like "гостинна", which are incorrect in standard Ukrainian.
    :::
  replace: |
    :::tip
    For "living room", use the standard noun **вітальня**. Do not use **гостинна** here as the room name.
    :::
- find: |
    Pay attention to consonant shifts in the Locative case. The word **кухня** ends in a soft consonant, so it becomes **на кухні** (in the kitchen). Yes, in Ukrainian we say "on the kitchen" rather than "in the kitchen"!
  replace: |
    Pay attention to consonant shifts in the Locative case. The word **кухня** ends in a soft consonant, so it becomes **на кухні**. In English, this translates naturally as "in the kitchen".
- find: |
    Finally, routines change depending on the day. We contrast weekdays and weekends using the Locative case. "On weekdays" is «у будні», and "on weekends" is «у вихідні». To say that you do something every Saturday, use a special repetitive structure.
  replace: |
    Finally, routines change depending on the day. We often use the time expressions «у будні» and «у вихідні» to contrast weekdays and weekends. To say that you do something every Saturday, use a special repetitive structure.
- find: |
    За столом друзі часто говорять про свій розпорядок дня. Марк запитує: «А о котрій годині ви встаєте?». Олена відповідає, що вона завжди встає рано. Вона йде у ванну, а потім готує сніданок. Тарас запитує Марка: «А хто у вас готує вечерю?». Марк розповідає, що він зазвичай вечеряє на роботі. У цій простій розмові ми бачимо багато відмінків разом.
  replace: |
    За столом друзі часто говорять про свій розпорядок дня. Марк запитує: «А о котрій годині ви встаєте?». Олена відповідає, що вона завжди встає рано. Вона йде у ванну, а потім готує сніданок. Тарас запитує Марка: «А хто у вас готує вечерю?». Марк розповідає, що він зазвичай вечеряє на роботі. Наприкінці він дякує господарям за вечерю. У цій простій розмові ми бачимо багато відмінків разом.
- find: |
    Use the Nominative case to list what exists in your home. Use the Genitive case to state what is missing or to specify quantities. Use the Accusative case to show where you go during the day. Use the Instrumental case to explain how you travel or who you spend your time with. Finally, use the Locative case to pinpoint exactly where things are, like in the **кухня** (kitchen), the **спальня** (bedroom), or the **вітальня** (living room).
  replace: |
    Use the Nominative case to list what exists in your home. Use the Genitive case to state what is missing or to specify quantities. Use the Dative case to show for whom you do something. Use the Accusative case to show where you go during the day. Use the Instrumental case to explain how you travel or who you spend your time with. Finally, use the Locative case to pinpoint exactly where things are, like in the **кухня** (kitchen), the **спальня** (bedroom), or the **вітальня** (living room).
</fixes>