## Linguistic Scan
No linguistic errors found.

## Exercise Check
Four exercise markers are present and placed after the relevant teaching blocks: `fill-in-real-conditionals` after section 1, `match-up-logical-results` and `error-correction-verb-forms` after section 2, and `quiz-yakscho-vs-yakby` after section 3. Coverage count matches the four `activity_hints`, and the markers are spread sensibly through the module.

One mismatch remains: the planned `error-correction` task is supposed to target verb aspect usage, but the prose never teaches aspect. A search for `доконаний`, `недоконаний`, and `аспект` returns 0 occurrences, so that exercise would test knowledge the module does not explicitly prepare.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The module covers the garden scenario, optional `то`, punctuation, `якби` recognition, and intonation. But the A2.7 consolidation stops at metalanguage: “Ми впевнено використовуємо слова «тому що» або «бо»...” and “Чи можете ви описати об'єкт, використовуючи слова «який» або «де»?”; it does not give the planned model paragraph combining clause types. |
| 2. Linguistic accuracy | 10/10 | No verified Russianisms, Surzhyk, calques, or paronym errors found in the prose. Russian letters `ы э ё ъ` are absent, and VESUM verification already cleared all content words except the proper-name form `Карпатах`. |
| 3. Pedagogical quality | 7/10 | The explanation states: “Тому ми використовуємо майбутній час або наказовий спосіб,” then immediately gives “Якщо ви вже готові, ми можемо починати урок.” That weakens the pattern at the point of introduction. |
| 4. Vocabulary coverage | 10/10 | All required plan vocabulary appears naturally in prose: `якщо`, `умова`, `результат`, `реальний`, `погода`, `допомогти`, `поспішити`, `вільний`, `залишитися`, `порада`. Recommended vocabulary is also present through normal forms like `якби`, `парасольку`, `змокнеш`, `відпустку`, `запізнимося`. |
| 5. Exercise quality | 7/10 | Marker placement is good, but the planned aspect-focused `error-correction` exercise is unsupported by the teaching. The module never introduces aspect terminology or a mini-rule before `<!-- INJECT_ACTIVITY: error-correction-verb-forms -->`. |
| 6. Engagement & tone | 9/10 | The tone is teacherly and concrete, with useful everyday scenarios: garden planning, advice from a doctor/teacher, weekend plans with friends. |
| 7. Structural integrity | 9/10 | All three planned H2 sections are present and ordered correctly. Markdown is clean, markers are intentional, and the pipeline word count is 2455, safely above target. |
| 8. Cultural accuracy | 10/10 | The module treats Ukrainian on its own terms and uses plausible Ukrainian settings and examples (`дача`, `Карпати`, `викладач`, `відпустка`) without Russia-centering. |
| 9. Dialogue & conversation quality | 9/10 | The garden dialogue is natural, multi-turn, and directly tied to the plan’s core scenario: planting, rain, seeds, and a garden bed. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: section “Якщо чи якби? Тільки реальна умова”, the paragraphs beginning “Ви вже знаєте багато корисних сполучників...” and “Спробуйте зробити короткий тест для себе.”  
Issue: The plan explicitly calls for consolidation by building paragraphs that use multiple A2.7 clause types together. The module only names the conjunctions and asks metalinguistic questions; it never models an integrated paragraph.  
Fix: Replace those two paragraphs with one short model paragraph that includes `тому що`, `хоча`, `щоб`, `який/де`, and `якщо`, then keep the self-check.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: section “Якщо + теперішній/майбутній час”, paragraph with “Тому ми використовуємо майбутній час або наказовий спосіб.”  
Issue: The rule narrows the result clause to future or imperative, then immediately gives a present-modal example: “Якщо ви вже готові, ми можемо починати урок.” That blurs the core pattern right after introducing it.  
Fix: Replace that example with a future or imperative result clause, for example `Якщо ви вже готові, починаймо урок.`

[EXERCISE QUALITY] [SEVERITY: major]  
Location: end of section “Умова в повсякденному житті”, immediately before `<!-- INJECT_ACTIVITY: error-correction-verb-forms -->`  
Issue: The planned error-correction activity is about verb aspect usage, but the prose never teaches aspect. Search evidence: `доконаний` = 0, `недоконаний` = 0, `аспект` = 0.  
Fix: Add a short bridge before the marker explaining that real future results often use perfective-looking completed forms such as `купиш`, `підготую`, `візьмеш`, `змокнеш`.

## Verdict: REVISE
The module is linguistically clean and structurally sound, but it has three substantive quality problems: missing integrated A2.7 consolidation, a rule/example mismatch in the core grammar explanation, and an exercise-preparation gap for the planned error-correction task.

<fixes>
- find: "Якщо ви вже готові, ми можемо починати урок."
  replace: "Якщо ви вже готові, починаймо урок."
- find: |
    Ви вже знаєте багато корисних сполучників. Вони допомагають поєднувати прості ідеї у великі та красиві речення. Ми хочемо пояснити причину нашої дії. Тоді ми впевнено використовуємо слова «тому що» або «бо». Якщо ми робимо щось попри серйозні перешкоди, нам чудово допомагає слово «хоча». Коли ми говоримо про мету нашої роботи, ми завжди ставимо сполучник «щоб». Це дуже важливі інструменти для щоденного спілкування.

    Спробуйте зробити короткий тест для себе. Чи можете ви зараз пояснити причину свого рішення? Чи можете ви описати об'єкт, використовуючи слова «який» або «де»? Чи знаєте ви, як правильно показати прямий **результат** (result) вашої дії? Звичайно, тепер ви також вмієте додавати умову, використовуючи слово **якщо** (if). Це означає, що ви можете вільно висловлювати думки. Робіть це, коли у вас є **вільний** (free) час для практики.
  replace: |
    Ви вже знаєте багато корисних сполучників. Подивіться, як вони працюють разом в одному абзаці: «Я залишуся вдома, тому що маю роботу, хоча друзі кличуть мене в кіно. Я хочу закінчити текст, щоб завтра мати вільний вечір. Якщо все буде добре, я зустрінуся з другом, який живе біля парку, де ми зазвичай п'ємо каву». У цьому короткому тексті разом працюють причина, перешкода, мета, опис людини або місця і умова.

    Спробуйте зробити короткий тест для себе. Чи можете ви скласти подібний абзац самі? Чи можете ви пояснити причину свого рішення, описати людину або місце словами «який» чи «де» і додати умову зі словом **якщо** (if)? Якщо так, ви вже добре використовуєте основні типи складнопідрядних речень рівня A2.7.
- find: "Ці чіткі домовленості роблять наші людські стосунки набагато більш прозорими та зрозумілими."
  replace: |
    Ці чіткі домовленості роблять наші людські стосунки набагато більш прозорими та зрозумілими.

    Зверніть увагу і на вид дієслова. У реченнях про реальну майбутню умову ми часто беремо форми доконаного виду для конкретного результату: «Якщо ти купиш насіння, я підготую грядку», «Якщо не візьмеш парасольку, змокнеш». Це допоможе вам у наступній вправі виправляти помилки у дієслівних формах.
</fixes>