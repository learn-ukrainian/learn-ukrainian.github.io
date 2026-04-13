## Linguistic Scan
- No Russianisms, Surzhyk, calques, paronym errors, or banned Russian characters were found.
- [Linguistic accuracy] [SEVERITY: critical] Location: `So, «очами» is wrong; the correct form is «очима».`
  Issue: This is too absolute. VESUM attests `очами` as an archaic/poetic instrumental plural, so teaching it as simply “wrong” is inaccurate.
  Fix: Rephrase it as a standard-vs-archaic distinction and teach `очима` as the preferred modern form.

## Exercise Check
- 4 activity markers are present, and their IDs match the plan’s `activity_hints`: `group-sort-cases`, `fill-in-mixed-cases`, `quiz-error-correction`, `error-correction-mixed`.
- Marker placement is locally logical, but all 4 markers are clustered in Part 2.
- Part 1 exercises are mostly prose placeholders rather than concrete task items.
- Exercise 5 is announced with `Read a short text and identify the case and trigger for the underlined nouns.` but no short text follows.
- Exercise 8 is announced with `complete a dialogue where you fill in the missing noun forms` but no blanks/dialogue exercise follows.
- The plan explicitly includes `по + Loc.`, but the preposition section never teaches it.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 5/10 | The plan requires `по + Loc.`, textbook references, and a wedding dialogue where “all 7 cases” appear. The module never teaches `по + Loc.`, never cites `Заболотний` or `Варзацька`, and the dialogue claims `This dialogue contains all seven cases` while only analyzing six. |
| 2. Linguistic accuracy | 7/10 | The Ukrainian is mostly clean, but `So, «очами» is wrong; the correct form is «очима».` is an inaccurate overstatement. |
| 3. Pedagogical quality | 6/10 | There are many examples, but several exercises remain abstract instructions instead of usable tasks: `Your завдання... Think about...`, `Read a short text...`, `complete a dialogue...`. |
| 4. Vocabulary coverage | 10/10 | All required vocabulary appears naturally: `перевірка`, `контрольна точка`, `завдання`, `помилка`, `виправити`, `відмінок`, `множина`, `однина`; recommended words also appear: `самоперевірка`, `впевнено`, `вихідний день`. |
| 5. Exercise quality | 5/10 | The marker IDs match the plan, but Part 1 lacks concrete item sets, Exercise 5 has no short text, and Exercise 8 has no actual blanked dialogue. |
| 6. Engagement & tone | 7/10 | The teacherly tone is generally fine, but lines like `You must memorize these completely because you will use them every single day` and `Practice is the only way to build this fluency` add filler rather than instruction. |
| 7. Structural integrity | 8/10 | Headings are clean and the pipeline word count is above target, but the closing sentence is malformed: `If you can answer "yes" to these questions,  Keep practicing...` |
| 8. Cultural accuracy | 9/10 | The module is Ukrainian-centered and the wedding/day-off contexts are culturally neutral and appropriate. |
| 9. Dialogue & conversation quality | 6/10 | The Наталя/Олег exchange is natural enough, but the wedding dialogue is still mostly a grammar showcase, and its “all seven cases” claim is not supported by the actual noun forms shown. |

## Findings
- [LINGUISTIC ACCURACY] [SEVERITY: critical]
  Location: `So, «очами» is wrong; the correct form is «очима».`
  Issue: `очами` is attested; it is not simply “wrong.”
  Fix: Teach `очима` as the standard modern form and label `очами` as archaic/poetic.

- [PLAN ADHERENCE] [SEVERITY: critical]
  Location: `This dialogue contains all seven cases. Let us analyze them:`
  Issue: The dialogue as written does not include a clear Nominative noun example, so the “all seven cases” claim is false.
  Fix: Add a nominative noun sentence to the dialogue and analyze it explicitly.

- [PLAN ADHERENCE] [SEVERITY: major]
  Location: Part 2 preposition teaching block around `The preposition «у» or «в»...` / `Similarly, the preposition «з»...`
  Issue: The plan explicitly requires `по + Loc.`, but `по` is never taught.
  Fix: Add at least one `по + Locative` example before the activity marker.

- [PLAN ADHERENCE] [SEVERITY: major]
  Location: `## Підсумок`
  Issue: The plan references `Заболотний Grade 6` and `Варзацька Grade 4, с. 38`, but the module never cites them.
  Fix: Add a short review-reference sentence in the summary.

- [EXERCISE QUALITY] [SEVERITY: major]
  Location: `Your **завдання** (task, exercise) is to form the Nominative plural for a mixed-gender list of ten singular nouns. Think about how words like «книга», «зошит», and «вікно» change.`
  Issue: Exercise 1 is only described; the learner never receives the actual 10-item list promised by the plan.
  Fix: Replace the placeholder with a concrete noun list.

- [EXERCISE QUALITY] [SEVERITY: major]
  Location: `To master this, your next task is to form the Genitive plural for ten challenging nouns.` and `Complete quantity expressions with the correct Genitive plural forms: \`п'ять...\`, \`багато...\`, \`скільки...\`?`
  Issue: Exercises 2 and 3 are also only described, not instantiated.
  Fix: Replace both placeholders with concrete prompts.

- [EXERCISE QUALITY] [SEVERITY: major]
  Location: `Read a short text and identify the case and trigger for the underlined nouns.`
  Issue: Exercise 5 is missing its actual short text.
  Fix: Insert a short text with marked nouns and a clear identification task.

- [EXERCISE QUALITY] [SEVERITY: major]
  Location: `To test your understanding, complete a dialogue where you fill in the missing noun forms in the correct case, both singular and plural.`
  Issue: Exercise 8 is missing its actual blanked dialogue.
  Fix: Replace the instruction with a real completion exercise.

- [PLAN ADHERENCE] [SEVERITY: major]
  Location: self-check list ending with `- Чи готовий я до рівня A2.6?`
  Issue: The plan’s self-assessment checklist includes `Can I use the case compass from M31?`, but that item is absent.
  Fix: Add an M31 case-compass self-check bullet.

- [ENGAGEMENT & TONE] [SEVERITY: minor]
  Location: `You must memorize these completely because you will use them every single day:`
  Issue: This is generic emphasis, not instruction.
  Fix: Replace it with a more concrete teacher cue.

- [STRUCTURAL INTEGRITY] [SEVERITY: minor]
  Location: `If you can answer "yes" to these questions,  Keep practicing...`
  Issue: The sentence is malformed and has a doubled space.
  Fix: Repair the sentence.

## Verdict: REVISE
The module is salvageable, but it cannot pass as written. It contains one factual linguistic overstatement, one false grammar-analysis claim, and multiple major plan/exercise omissions.

<fixes>
- find: |
    However, the most frequently used words often have irregular forms. You must memorize these completely because you will use them every single day:
  replace: |
    However, some very common words have irregular forms. These are worth memorizing early because they appear often in everyday Ukrainian:

- find: |
    Your **завдання** (task, exercise) is to form the Nominative plural for a mixed-gender list of ten singular nouns. Think about how words like «книга», «зошит», and «вікно» change.
  replace: |
    Your **завдання** (task, exercise) is to form the Nominative plural for these ten singular nouns: **книга, зошит, вікно, студент, ніч, море, дитина, людина, око, друг**. Write the plural form next to each word, then group the answers by ending pattern.

- find: |
    To master this, your next task is to form the Genitive plural for ten challenging nouns. Can you form the Genitive plural for **теля** (calf)? It becomes **телят**!
  replace: |
    To master this, form the Genitive plural for these ten nouns: **книга, місто, ніч, море, студент, олівець, гість, яблуко, річ, теля**. Then compare your answers with the patterns above. Remember: **теля → телят**.

- find: |
    Complete quantity expressions with the correct Genitive plural forms: `п'ять...`, `багато...`, `скільки...`?
  replace: |
    Complete these quantity expressions with the correct Genitive plural forms:
    1. `п'ять ___` (студент)
    2. `багато ___` (місто)
    3. `скільки ___?` (книга)
    4. `мало ___` (гроші)
    5. `десять ___` (ніч)

- find: |
    <!-- INJECT_ACTIVITY: group-sort-cases -->
  replace: |
    The preposition «по» also commonly takes the Locative when we mean movement along a place or distribution across a surface.
    > Ми довго гуляли по **парку**. *(We walked around the park for a long time.)*
    > Книжки лежать по **полицях**. *(The books are lying on the shelves.)*

    <!-- INJECT_ACTIVITY: group-sort-cases -->

- find: |
    Read a short text and identify the case and trigger for the underlined nouns.
  replace: |
    Read the short text and identify the case and trigger for the underlined nouns.

    > У суботу я був у __музеї__. Там я бачив __друзів__. Один хлопець був у синьому __светрі__. Після екскурсії я подзвонив __сестрі__. Ми повернулися з __центру__ без __парасольки__.

    For each underlined noun, name the case and say whether the trigger is a verb, a preposition, or a time construction.

- find: |
    Another issue is ignoring dual remnants in the Instrumental case. For body parts that come in pairs, we use «-има» instead of «-ами». So, «очами» is wrong; the correct form is «очима». Similarly, we say «плечима» (with shoulders) and «дверима» (with doors). 
  replace: |
    Another issue is choosing the standard Instrumental plural forms for paired nouns. In standard modern Ukrainian, we usually use forms like «очима», «плечима», and «дверима». The form «очами» does exist, but it is archaic or poetic, so A2 learners should prefer «очима». 

- find: |
    > **Подруга:** Не хвилюйся, усе буде чудово на **весіллі**! *(Do not worry, everything will be wonderful at the wedding!)*
  replace: |
    > **Подруга:** Не хвилюйся, усе буде чудово на **весіллі**! *(Do not worry, everything will be wonderful at the wedding!)*
    > **Наречена:** Наш **фотограф** уже чекає біля ресторану. *(Our photographer is already waiting by the restaurant.)*

- find: |
    This dialogue contains all seven cases. Let us analyze them:
    - «Олено!» is the Vocative case. It is used to address the person directly.
  replace: |
    This dialogue contains all seven cases. Let us analyze them:
    - «фотограф» is the Nominative singular. It names the subject of the sentence.
    - «Олено!» is the Vocative case. It is used to address the person directly.

- find: |
    To test your understanding, complete a dialogue where you fill in the missing noun forms in the correct case, both singular and plural. Read the surrounding words carefully to find the triggers.
  replace: |
    To test your understanding, complete this dialogue with the correct noun forms in the correct case.

    > **Андрій:** Ти вже запросила всіх ___ (гість)?
    > **Олена:** Так, і я вже купила подарунок ___ (подруга).
    > **Андрій:** А фотограф буде з ___ (молодята)?
    > **Олена:** Так, він чекатиме нас на ___ (весілля).
    > **Андрій:** Добре. Тоді я ще подзвоню ___ (батьки) і ___ (друзі).
    > **Олена:** Чудово, дякую тобі, ___ (Андрій)!

- find: |
    We have covered a lot of ground in this module. Take a moment for a **самоперевірка** (self-check). Ask yourself these questions:
  replace: |
    We have covered a lot of ground in this module. Take a moment for a **самоперевірка** (self-check). If you want extra review, compare these patterns with the declension table in Варзацька Grade 4, с. 38, and the review exercises in Заболотний Grade 6. Ask yourself these questions:

- find: |
    - Чи використовую я Кличний відмінок при звертанні до людей?
    - Чи готовий я до рівня A2.6?
  replace: |
    - Чи використовую я Кличний відмінок при звертанні до людей?
    - Чи вмію я користуватися «case compass» з M31, коли сумніваюся?
    - Чи готовий я до рівня A2.6?

- find: |
    If you can answer "yes" to these questions,  Keep practicing, read more texts, and do not be afraid to make a **помилка** — every error is a step toward fluency.
  replace: |
    If you can answer "yes" to these questions, keep practicing, read more texts, and do not be afraid to make a **помилка** — every error is a step toward fluency.
</fixes>