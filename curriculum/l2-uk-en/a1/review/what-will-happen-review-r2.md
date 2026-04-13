## Linguistic Scan
No linguistic errors found. I spot-checked `ворожка`, `щасливий`, `ввечері`, `відпочивати`, and the textbook-style pattern `що буде робити`; the forms are attested.

## Exercise Check
3/3 planned markers are present: `match-pronoun-to-buty`, `fill-in-analytic-future`, `fill-in-tense-distinction`.

Each marker appears after the relevant teaching section, and the marker IDs match the three `activity_hints`. No exercise-placement or marker-coverage issues found.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The module covers the core grammar and all required `буду/будеш/буде/будемо/будете/будуть` forms, but the planned weekend dialogue is missing: the text never reaches `Що ви будете робити на вихідних?` or `У суботу ми будемо відпочивати...`. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, bad case endings, or wrong grammar claims found in the Ukrainian text I checked. |
| 3. Pedagogical quality | 7/10 | The PPP arc is visible, but the explanation gets too abstract before returning to Ukrainian examples: `The grammatical formula for the analytic future consists of two distinct parts working seamlessly together...` is a long English theory block before more usable sentence models. |
| 4. Vocabulary coverage | 10/10 | All required vocabulary appears in prose: `завтра`, `буду`, `будеш`, `буде`, `будемо`, `будете`, `будуть`, `робити`. Recommended items such as `відпочивати`, `план`, `звучати`, `футбол`, `зараз`, `наступного тижня` also appear. |
| 5. Exercise quality | 10/10 | The three planned exercise markers are present and well placed after teaching: `match-pronoun-to-buty`, `fill-in-analytic-future`, `fill-in-tense-distinction`. |
| 6. Engagement & tone | 6/10 | The prose is padded with low-information teacher talk, especially in Practice: `Now let us rigorously apply...`, `We can quickly and confidently expand...`, and `To solidly anchor these future actions...` add length more than teaching value. |
| 7. Structural integrity | 10/10 | All H2 sections from the plan are present and ordered correctly. Pipeline word count is 1318, which is above the 1200 target. |
| 8. Cultural accuracy | 9/10 | The module stays in a Ukrainian setting and does not frame Ukrainian through Russian; the `ворожка` scene matches the plan’s dialogue situation. |
| 9. Dialogue & conversation quality | 7/10 | The first “dialogue” is mostly one speaker predicting (`Ти будеш багато подорожувати... Будеш отримувати подарунки...`), and the second collapses two planned situations into one exchange instead of giving a distinct weekend-plans conversation. |

## Findings
[Plan adherence] [SEVERITY: major]  
Location: `Now, let us move from mystical predictions to a completely natural, everyday conversation about planning the upcoming week.` and the dialogue that follows  
Issue: The module omits the plan’s separate weekend-plans dialogue. The required lines `Що ви будете робити на вихідних?`, `У суботу ми будемо відпочивати`, and `чоловік буде гуляти з дітьми` do not appear, so one content-outline point is missing. This also weakens dialogue variety.  
Fix: Replace the current single everyday dialogue with two short conversations: one for tomorrow-plans and one for weekend-plans, using the planned lines.

[Pedagogical quality] [SEVERITY: major]  
Location: `The grammatical formula for the analytic future consists of two distinct parts working seamlessly together.`  
Issue: This explanation is too long and abstract for A1 before returning to Ukrainian sentence models. It slows the PPP flow and front-loads English theory instead of example-led teaching.  
Fix: Replace the paragraph with a shorter rule plus 2-3 concrete Ukrainian examples such as `я буду читати`, `ти будеш робити`, `ми будемо гуляти`.

[Engagement & tone] [SEVERITY: major]  
Location: `Now let us rigorously apply the future tense formula...` through `Placing these time words either at the very beginning or the very end of your sentence establishes a clear, undeniable time frame for your personal plans.`  
Issue: The Practice section is bloated with filler and emphatic phrasing instead of concise teaching. The section says the same idea repeatedly before getting to the examples.  
Fix: Compress this block to one short explanation and keep the Ukrainian examples doing the instructional work.

## Verdict: REVISE
REVISE. There are no critical linguistic errors, but there are major quality problems: one planned dialogue point is missing, the explanation is too theory-heavy for A1, and the practice prose is padded. Dimensions 3, 6, and 9 are below 9, so this does not meet the PASS gate.

<fixes>
- find: |
    Now, let us move from mystical predictions to a completely natural, everyday conversation about planning the upcoming week. Notice how the exact same grammatical pattern is utilized to discuss normal daily routines, chores, and leisure activities with friends.

    > **Олена:** Що ти будеш робити завтра? *(What will you do tomorrow?)*
    > **Антон:** Завтра я буду працювати. *(Tomorrow I will work.)*
    > **Олена:** А ввечері? *(And in the evening?)*
    > **Антон:** Ввечері я буду готувати вечерю. *(In the evening I will prepare dinner.)*
    > **Олена:** А що буде робити твоя сестра? *(And what will your sister do?)*
    > **Антон:** Вона буде читати. *(She will read.)*
    > **Олена:** А ви будете гуляти? *(And will you go for a walk?)*
    > **Антон:** Так, ми будемо гуляти в парку. *(Yes, we will walk in the park.)*
    > **Олена:** Звучить добре! А я буду дивитися футбол. *(That sounds good! And I will watch football.)*
    > **Антон:** Ти завжди будеш дивитися футбол! *(You will always watch football!)*
  replace: |
    Now, let us move from mystical predictions to two everyday planning conversations. The same pattern helps speakers talk about tomorrow and the weekend in a natural way.

    > **Олена:** Що ти будеш робити завтра? *(What will you do tomorrow?)*
    > **Антон:** Завтра я буду працювати. *(Tomorrow I will work.)*
    > **Олена:** А ввечері? *(And in the evening?)*
    > **Антон:** Ввечері я буду готувати вечерю. *(In the evening I will prepare dinner.)*
    > **Олена:** А що буде робити твоя сестра? *(And what will your sister do?)*
    > **Антон:** Вона буде читати. *(She will read.)*
    > **Олена:** А ви будете гуляти? *(And will you go for a walk?)*
    > **Антон:** Так, ми будемо гуляти в парку. *(Yes, we will walk in the park.)*

    > **Марія:** Що ви будете робити на вихідних? *(What will you do on the weekend?)*
    > **Ірина:** У суботу ми будемо відпочивати. *(On Saturday we will rest.)*
    > **Марія:** А в неділю? *(And on Sunday?)*
    > **Ірина:** У неділю я буду готувати, а чоловік буде гуляти з дітьми. *(On Sunday I will cook, and my husband will walk with the children.)*
    > **Марія:** Звучить добре! А я буду дивитися футбол. *(That sounds good! And I will watch football.)*
    > **Ірина:** Ти завжди будеш дивитися футбол! *(You will always watch football!)*

- find: |
    The grammatical formula for the analytic future consists of two distinct parts working seamlessly together. The first part is the auxiliary helper verb **бути** (to be), which must be conjugated in the future tense to match the person performing the action (I, you, he, we, etc.). The second part is the infinitive form of your main action verb, such as **робити** (to do)—the pure dictionary form ending in "-ти". You must strongly emphasize this structural rule in your mind: the main verb stays completely frozen in the infinitive and never changes its endings in this tense. Only the helper verb actively conjugates to match the subject of the sentence.
  replace: |
    The analytic future has two parts: a future form of **бути** and an infinitive. In **я буду читати**, only **буду** changes for person, while **читати** stays the same. The same pattern works in **ти будеш робити**, **вона буде готувати**, and **ми будемо гуляти**.

- find: |
    Now let us rigorously apply the future tense formula to some of our core vocabulary verbs to see how predictable and reliable the pattern truly is. Because the main verb remains firmly in the infinitive form, you do not need to worry about spelling exceptions or stem changes here. For example, the verb **працювати** (to work) simply becomes **буду працювати** (I will work), **будеш працювати** (you will work), and so on through the paradigm. The daily verb **готувати** (to cook) follows the exact same mechanical pattern without any variation: **буду готувати** (I will cook), **буде готувати** (he/she will cook).

    We can quickly and confidently expand this pattern to include other common daily verbs like **гуляти** (to walk), **дивитися** (to watch), and **говорити** (to speak). Here are short, clear sentence examples demonstrating each verb in action to steadily build your structural familiarity and listening comprehension.

    * **Ми будемо гуляти в парку.** (We will walk in the park.)
    * **Вона буде дивитися футбол.** (She will watch football.)
    * **Вони будуть говорити.** (They will speak.)
    * **Я буду відпочивати** (to rest) **вдома.** (I will rest at home.)

    To solidly anchor these future actions in a realistic, everyday context, we must use essential future time markers. These crucial words tell the listener exactly when the planned action or event is expected to happen in the real world. The most important time markers to learn right now are **завтра** (tomorrow), **наступний** (next, adj) and **тиждень** (week, m) in the phrase **наступного тижня** (next week), **у суботу** (on Saturday), and **ввечері** (in the evening). Placing these time words either at the very beginning or the very end of your sentence establishes a clear, undeniable time frame for your personal plans.
  replace: |
    Now let us apply the pattern to core verbs from this module. Change only **бути**: **буду працювати**, **будеш працювати**, **буде готувати**, **будемо гуляти**, **будуть говорити**.

    Here are short examples with future time markers such as **завтра**, **наступного тижня**, **у суботу**, and **ввечері**:

    * **Ми будемо гуляти в парку.** (We will walk in the park.)
    * **Вона буде дивитися футбол.** (She will watch football.)
    * **Вони будуть говорити.** (They will speak.)
    * **Я буду відпочивати вдома.** (I will rest at home.)
</fixes>