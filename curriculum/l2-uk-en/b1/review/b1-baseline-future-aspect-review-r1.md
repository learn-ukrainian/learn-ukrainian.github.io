## Linguistic Scan
Errors found:
1. **Typo:** "вза虺" instead of "взагалі" (Encoding/generation glitch).
2. **Typo:** "конкре планів" instead of "конкретних планів".
3. **Surzhyk:** "конкре planned подію" instead of "конкретну заплановану подію" (Mixed language generation error).
4. **Russianism / Calque:** "Давайте подивимося/подумаємо/проведемо" etc. used 9 times. This is a direct calque from Russian "Давайте посмотрим". The correct Ukrainian imperative is synthetic: "Подивімося", "Подумаймо", "Проведімо".

## Exercise Check
- **Markers present:** 7 markers found for 6 planned activities. The generated text includes two "fill-in" exercises instead of one (`fill-in-simple-future`, `fill-in-future-choice`), which is acceptable padding.
- **Marker IDs:** `quiz-aspect-identification`, `match-up-aspect-pairs`, `fill-in-simple-future`, `group-sort-future-forms`, `fill-in-future-choice`, `error-correction-aspect-tense`, `free-write-future-plans`. These align with the planned pedagogical focus.
- **Placement:** Markers are distributed logically after the relevant theoretical explanations, acting as perfect checkpoints.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | Deductions for missing planned components: 1) "folk tale" extended practice missing in section 5, replaced with generic cinematic metaphor. 2) "letter to a friend about summer plans" missing in section 6, replaced with business email. Vocabulary and grammatical structure otherwise follow the plan. |
| 2. Linguistic accuracy | 5/10 | Deductions for critical typos and Russianisms: 1) "вза虺" instead of "взагалі" 2) "конкре планів" 3) "конкре planned подію" 4) Calque "давайте + інфінітив/дієслово" used extensively. |
| 3. Pedagogical quality | 10/10 | Excellent PPP flow, very clear analogies (the bridge analogy for imperfective vs perfective), logical step-by-step introduction of conjugations. |
| 4. Vocabulary coverage | 10/10 | All required vocabulary integrated naturally into the prose with bolding and translations. |
| 5. Exercise quality | 10/10 | Activity markers appropriately mapped and placed correctly after the instruction they test. |
| 6. Engagement & tone | 10/10 | The tone is warm, encouraging, and natural for a teacher, without gamified or corporate slang. |
| 7. Structural integrity | 10/10 | All H2 headers match the plan. Word count is 4771 (exceeding 4000 target). Clean markdown. |
| 8. Cultural accuracy | 10/10 | Ukrainian aspects explained accurately on their own terms ("ми мислимо зовсім інакше"). Decolonized pedagogy respected. |
| 9. Dialogue & conversation quality | 10/10 | Natural dialogues; realistic charity concert situation correctly incorporating targeted grammatical forms. |

## Findings
[1. Plan adherence] [major]
Location: Section 5 (Вид і час — як вони працюють разом): "Коли ви розказуєте цікаву історію (story), види дієслова працюють як професійна режисерська камера у кіно... «Сонце яскраво світило на небі...»"
Issue: The plan explicitly required learners to retell a "Ukrainian folk tale" with an annotated model text. The writer replaced this with a generic cinematic metaphor and story.
Fix: Replace the generic story explanation with a short Ukrainian folk tale snippet featuring aspect annotations (недок./док.).

[1. Plan adherence] [major]
Location: Section 6 (Дієвідмінювання у майбутньому часі): "Уявіть, що ви пишете важливий діловий електронний лист (email) своїм колегам..."
Issue: The plan explicitly required a "letter to a friend about summer plans". The writer substituted this with a business email about a project.
Fix: Replace the business email text and explanation with a letter to a friend about summer trip plans to the Carpathians.

[2. Linguistic accuracy] [critical]
Location: Section 2 (Проста форма майбутнього часу): "Саме тому дієслова доконаного виду вза虺 не мають теперішнього часу."
Issue: Typo/Encoding glitch "вза虺" instead of "взагалі".
Fix: Replace "вза虺" with "взагалі".

[2. Linguistic accuracy] [critical]
Location: Section 5 (Вид і час — як вони працюють разом): "Англійська мова дуже часто і природно використовує теперішній тривалий час для вираження конкре планів."
Issue: Typo "конкре планів" instead of "конкретних планів".
Fix: Replace "вираження конкре планів" with "вираження конкретних планів".

[2. Linguistic accuracy] [critical]
Location: Section 6 (Дієвідмінювання у майбутньому часі): "...який позначає конкре planned подію."
Issue: Unacceptable Surzhyk / mixed language typo.
Fix: This paragraph is fully rewritten in the plan adherence fix (business email -> summer letter), which implicitly resolves this error.

[2. Linguistic accuracy] [major]
Location: Throughout the text (e.g., "Давайте подивимося на п'ять базових прикладів", "Давайте подумаємо логічно").
Issue: The use of "Давайте + дієслово" is a calque from Russian "Давайте посмотрим". Ukrainian forms imperatives synthetically for the 1st person plural (Подивімося, Подумаймо).
Fix: Replace all instances of "Давайте [дієслово]" with the correct synthetic imperative forms.

## Verdict: REVISE
The module features wonderful pedagogical explanations and a superb tone, but it currently suffers from critical typos, a mixed-language hallucination, widespread use of a Russian grammatical calque ("давайте"), and two deviations from the planned contextual practices. Applying the provided fixes will resolve all of these issues.

<fixes>
- find: "Давайте подивимося на п'ять базових прикладів."
  replace: "Подивімося на п'ять базових прикладів."
- find: "Давайте подивимося, як вибір виду кардинально змінює значення ситуації."
  replace: "Подивімося, як вибір виду кардинально змінює значення ситуації."
- find: "Чому так відбувається? Давайте подумаємо логічно. Доконаний вид завжди позначає повністю завершену дію або фінальний результат."
  replace: "Чому так відбувається? Подумаймо логічно. Доконаний вид завжди позначає повністю завершену дію або фінальний результат."
- find: "Давайте детально подивимося на механізм дієвідмінювання."
  replace: "Подивімося детально на механізм дієвідмінювання."
- find: "Давайте подивимося на ще одне дуже корисне дієслово — **запросити** *(to invite)*."
  replace: "Подивімося на ще одне дуже корисне дієслово — **запросити** *(to invite)*."
- find: "Давайте подивимося, як різні форми майбутнього часу гармонійно працюють разом у реальній життєвій ситуації."
  replace: "Подивімося, як різні форми майбутнього часу гармонійно працюють разом у реальній життєвій ситуації."
- find: "Давайте детально поглянемо, як одне й те саме базове значення змінюється залежно від обраної форми майбутнього часу."
  replace: "Погляньмо детально, як одне й те саме базове значення змінюється залежно від обраної форми майбутнього часу."
- find: "Щоб переконатися, що ви справді глибоко засвоїли цю важливу тему, давайте проведемо коротку **самоперевірку** *(self-check)*."
  replace: "Щоб переконатися, що ви справді глибоко засвоїли цю важливу тему, проведімо коротку **самоперевірку** *(self-check)*."
- find: "Саме тому дієслова доконаного виду вза虺 не мають теперішнього часу."
  replace: "Саме тому дієслова доконаного виду взагалі не мають теперішнього часу."
- find: "вираження конкре планів."
  replace: "вираження конкретних планів."
- find: "Розуміння цієї видової матриці також чудово допомагає вам будувати красиві та динамічні розповіді. Коли ви розказуєте цікаву **історію** *(story)*, види дієслова працюють як професійна режисерська камера у кіно. Недоконаний вид створює загальне **тло** *(background)* або декорації для вашої головної сцени. Він малює широку картину: «Сонце яскраво світило на небі, я повільно йшов вулицею». Це довгі процеси без чіткого кінця. Натомість доконаний вид діє як раптова подія, яка несподівано ламає цей статус-кво і стрімко штовхає сюжет уперед. Він вводить нові активні дії: «Раптом я побачив старого друга, і мій телефон голосно задзвонив». Ця ж кінематографічна логіка ідеально працює і для ваших складних планів на майбутнє. Ви можете вільно комбінувати різні види, щоб показати правильну послідовність майбутніх подій. Наприклад, ви можете сказати другу: «Я буду чекати на тебе біля театру, а коли ти прийдеш, я радісно закричу». У цій фразі конструкція «буду чекати» — це недоконаний вид, ваш тривалий безперервний процес. А слова «прийдеш» та «закричу» — це доконаний вид, короткі завершені події, які переривають або доповнюють цей процес."
  replace: "Розуміння цієї видової матриці також чудово допомагає вам будувати красиві та динамічні розповіді. Коли ви переказуєте українську народну казку, види дієслова працюють як професійна режисерська камера у кіно. Недоконаний вид створює загальне **тло** *(background)* або декорації для вашої головної сцени. Натомість доконаний вид діє як раптова подія, яка стрімко штовхає сюжет уперед. Прочитайте цей уривок: «Жили (недок.) собі дід та баба. Щодня вони працювали (недок.) у полі. Але одного разу дід знайшов (док.) у землі глечик із золотом. Він швидко сховав (док.) його і побіг (док.) додому». Форми «жили» та «працювали» малюють тривалу картину минулого. А дієслова доконаного виду «знайшов», «сховав» та «побіг» вводять нові активні події. Ця ж логіка ідеально працює і для ваших планів на майбутнє. Ви можете вільно комбінувати різні види. Наприклад: «Я буду чекати на тебе біля театру, а коли ти прийдеш, я радісно закричу». У цій фразі конструкція «буду чекати» — це ваш тривалий процес. А слова «прийдеш» та «закричу» — це короткі завершені події, які доповнюють цей процес."
- find: "Тепер давайте практично подивимося, як природно всі ці різноманітні форми поєднуються в одному робочому контексті. Уявіть, що ви пишете важливий діловий **електронний лист** *(email)* своїм колегам. Правильне використання різних видів дієслова зробить ваш текст по-справжньому професійним, природним і дуже точним. Ви можете сміливо написати так: «Завтра вранці ми проведемо важливу зустріч. Ми будемо детально обговорювати наш новий великий **проєкт** *(project)*. Сподіваюся, що ми знайдемо гарне рішення»."
  replace: "Тепер подивімося практично, як природно всі ці різноманітні форми поєднуються в одному контексті. Уявіть, що ви пишете короткий **лист** *(letter)* своєму другові про плани на літо. Правильне використання різних видів дієслова зробить ваш текст по-справжньому природним і дуже точним. Ви можете сміливо написати так: «Влітку я поїду в Карпати. Я буду багато гуляти горами і щодня фотографуватиму місцеві пейзажі. Сподіваюся, що я побачу багато цікавого»."
- find: "У цьому короткому, але змістовному повідомленні перше дієслово «проведемо» — це доконаний вид, який позначає конкре planned подію. Наступне дієслово «будемо обговорювати» — це вже недоконаний вид, який яскраво показує тривалий, інтенсивний процес дискусії. І нарешті «знайдемо» — це знову доконаний вид, який повністю фокусується на фінальному, успішному результаті вашої зустрічі."
  replace: "У цьому короткому, але змістовному повідомленні перше дієслово «поїду» — це доконаний вид, який позначає конкретну заплановану подію. Наступні дієслова «буду гуляти» та «фотографуватиму» — це вже недоконаний вид, який яскраво показує тривалий процес. І нарешті «побачу» — це знову доконаний вид, який повністю фокусується на фінальному, успішному результаті вашої подорожі."
</fixes>
