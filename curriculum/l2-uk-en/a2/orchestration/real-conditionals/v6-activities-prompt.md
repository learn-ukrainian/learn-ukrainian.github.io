<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/real-conditionals.yaml` file for module **51: Якщо... то...** (a2).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## ⚠️ HARD COUNT TARGETS — READ TWICE

These are the binding numerical contracts for THIS module. The audit will FAIL if you fall short.

| Bucket | Min | Max | Notes |
|---|---|---|---|
| Total activities | 12 | 12+ | inline + workbook combined |
| Inline (lesson tab) | 4 | 6 | one per `<!-- INJECT_ACTIVITY -->` marker, see below |
| Workbook (Зошит tab) | 8 | 11 | extended practice |
| Items per activity | 8 | — | each activity must have at least 8 items (unless its type cap is lower — see Activity Type Reference below) |

**You MUST ship at least 4 inline activities AND at least 8 workbook activities.** Going under either is a hard failure — the audit gate enforces it and the build will reject your output.

**Type diversity is required.** The module (inline + workbook combined) MUST use at least **0** distinct activity types — do NOT ship a wall of the same type. As a quality target, quiz + true-false combined should be NO MORE than ~25% of the workbook (i.e. lean on the priority types below, not on easy multiple-choice). Use the `WORKBOOK_PRIORITY_TYPES` list below; those carry the most weight at this level. (If `0` is `0`, the audit profile for this level does not enforce type diversity — but variety still produces a better lesson, so aim for 4+ types when the workbook allows it.)

---

## Allowed types for THIS level

- **Inline (lesson) types:** quiz, true-false, fill-in, match-up, group-sort, classify, mark-the-words
- **Inline priority (preferred):** fill-in, match-up, true-false, quiz
- **Workbook types:** cloze, error-correction, fill-in, unjumble, translate, match-up, group-sort, odd-one-out, observe, phrase-table, quiz, true-false, mark-the-words
- **Workbook priority (preferred):** error-correction, cloze, unjumble, translate, fill-in
- **FORBIDDEN at this level:** anagram, essay-response, critical-analysis, reading, comparative-study, authorial-intent, etymology-trace, translation-critique, source-evaluation, debate, paleography-analysis, dialect-comparison, transcription, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, highlight-morphemes, grammar-identify

Pick from the allowed list. Lean heavily on the priority lists. Do not use any forbidden type — the build will reject it.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 4–6 quick checks after key teaching points. Workbook = 8–11 deeper practice exercises covering the full topic. **Every inline marker in the prose MUST have a matching inline activity** — that is what determines `INLINE_MIN`, so do NOT skip markers.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: fill-in-real-conditionals -->`
- `<!-- INJECT_ACTIVITY: match-up-logical-results -->`
- `<!-- INJECT_ACTIVITY: error-correction-verb-forms -->`
- `<!-- INJECT_ACTIVITY: quiz-yakscho-vs-yakby -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete real conditional sentences with the correct verb form in the якщо-clause
    or result clause
  items: 8
  type: fill-in
- focus: Choose якщо or якби — identify real vs. hypothetical conditions (recognition
    only for якби)
  items: 8
  type: quiz
- focus: Match conditions (якщо-clauses) to their logical results
  items: 8
  type: match-up
- focus: Fix incorrect verb aspect usage in sentences
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- якби (if — hypothetical, B1 preview)
- змокнути (to get wet)
- запізнитися (to be late)
- парасолька (umbrella)
- відпустка (vacation, holiday)
required:
- якщо (if — real condition)
- умова (condition)
- результат (result, outcome)
- реальний (real)
- погода (weather)
- допомогти (to help)
- поспішити (to hurry)
- вільний (free, available)
- залишитися (to stay, to remain)
- порада (advice)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Якщо + теперішній/майбутній час (If + Present/Future) (~770 words total)

Real conditionals describe situations that are highly possible or likely to happen.

Ми часто говоримо про плани, які залежать від різних ситуацій. Для цього ми використовуємо слово **якщо** (if). Це слово допомагає показати, що дія можлива. Ми називаємо це **реальна умова** (real condition). Це означає, що ситуація може статися сьогодні або завтра. Наприклад, ми дивимося на небо і бачимо сонце. Ми знаємо, що **погода** (weather) буде хороша. Тоді ми кажемо: «Якщо буде гарна погода, ми підемо гуляти». Або ваш друг робить домашнє завдання. Ви хочете **допомогти** (to help). Ви кажете: «Якщо ти хочеш, я допоможу». Це не фантазія, це реальна ситуація.

> *We often talk about plans that depend on different situations. For this, we use the word "якщо" (if). This word helps show that an action is possible. We call this a real condition. This means that the situation can happen today or tomorrow. For example, we look at the sky and see the sun. We know that the weather will be good. Then we say: "If the weather is good, we will go for a walk." Or your friend is doing homework. You want to help. You say: "If you want, I will help." This is not a fantasy, it is a real situation.*

Який час ми використовуємо у таких реченнях? Тут немає спеціальних форм. Ми використовуємо звичайний теперішній або майбутній час. Частина зі словом «якщо» описує умову. Тут дієслово стоїть у теперішньому або майбутньому часі. Друга частина речення показує **результат** (result). Ця дія відбудеться потім. Тому ми використовуємо майбутній час або наказовий спосіб. Наприклад: «Якщо в мене буде **вільний** (free) час, я прочитаю цю книгу». Або: «Якщо ти йдеш у магазин, купи хліб». У цих реченнях усе просто і логічно. Ми беремо знайомі форми дієслів і будуємо нову структуру. Якщо завтра буде сонце, ми поїдемо на озеро. Якщо ви вже готові, ми можемо починати урок.

:::info
**Grammar box**
In Ukrainian real conditionals, the `якщо`-clause uses the present or future tense, and the result clause uses the future tense or imperative. There is no special "conditional" mood here — just the regular tenses you already know.
:::

В українській мові ми дуже часто використовуємо слово «то». Воно стоїть на початку другої частини речення. Слово «то» працює як місток між умовою та результатом. Воно робить логічний зв'язок сильнішим. Це слово не є обов'язковим. Ви можете сказати речення без нього. Але з ним ваша мова звучить більш природно. Наприклад: «Якщо завтра дощитиме, то ми вирішили **залишитися** (to stay) вдома». Це означає, що ми точно не підемо гуляти. Якщо ми купимо квитки сьогодні, то завтра підемо в кіно. Або: «Якщо ти не знаєш правило, то запитай викладача». Тут слово «то» дає логічний старт для другої дії. Це хороша **порада** (advice) для студентів.

:::note
**Читаємо українською**
Прочитайте ці короткі ситуації. Зверніть увагу на коми та дієслова.

* Якщо ти хочеш спати, іди в ліжко.
* Я зроблю чай, якщо ти принесеш торт.
* Якщо завтра буде тепло, то ми поїдемо в ліс.
* Ти складеш іспит добре, якщо будеш багато читати.
:::

Тепер поговоримо про пунктуацію. Правило дуже просте: ми завжди ставимо кому між двома частинами. Кома ділить складнопідрядне речення на дві логічні половини. Якщо слово «якщо» стоїть на початку, ми ставимо кому перед другою частиною. Наприклад: «Якщо ти маєш час, допоможи мені». Або: «Якщо ти зараз не **поспішиш** (hurry), то ми точно запізнимося на поїзд». Але іноді головна частина стоїть на першому місці. Тоді слово «якщо» стоїть посередині речення. У такому випадку кома завжди стоїть перед словом «якщо». Наприклад: «Ми точно запізнимося на поїзд, якщо ти не поспішиш». Або: «Ми не поїдемо на море, якщо погода буде погана». Я прочитаю цю статтю, якщо матиму час. Ви бачите, що кома завжди стоїть на межі двох ідей. Під час розмови ми робимо там маленьку паузу.

:::tip
**Did you know?**
In Ukrainian punctuation, a comma must always separate the condition clause from the result clause. Whether `якщо` comes first or in the middle of the sentence, the comma acts as a clear visual border between the two ideas.
:::

Наш рівень фокусується тільки на реальних ситуаціях. Це означає, що ми говоримо про факти, плани та можливі події. Для цього ми використовуємо тільки слово «якщо». Але ви можете почути інше слово у піснях або розмовах. Це слово — «якби». Слово «якби» показує нереальну умову. Це фантазія або мрія про те, чого немає. Наприклад: «Якби я мав мільйон доларів, я б купив острів». Але у нас немає мільйона доларів. Це тільки мрія. Ми будемо вивчати нереальну умову і слово «якби» пізніше. На цьому етапі вам потрібно пам'ятати одне правило. Якщо ситуація можлива сьогодні або завтра, ми кажемо «якщо». Якщо це реальний план, ми використовуємо звичайний майбутній або теперішній час.

> *Our level focuses only on real situations. This means that we talk about facts, plans, and possible events. For this, we use only the word "якщо". But you might hear another word in songs or conversations. This word is "якби" (if only / what if). The word "якби" shows an unreal condition. This is a fantasy or a dream about something that does not exist. For example: "If I had a million dollars, I would buy an island." But we don't have a million dollars. It is only a dream. We will study the unreal condition and the word "якби" later. At this stage, you need to remember one rule. If the situation is possible today or tomorrow, we say "якщо". If it is a real plan, we use the regular future or present tense.*

<!-- INJECT_ACTIVITY: fill-in-real-conditionals -->

## Умова в повсякденному житті (Conditions in Everyday Life) (~770 words total)

> — **Чоловік:** Яка завтра буде **погода** (weather)? *(What will the weather be tomorrow?)*
> — **Дружина:** Якщо буде сонце, посадимо помідори. *(If there is sun, we will plant tomatoes.)*
> — **Чоловік:** А якщо вдень буде дуже сухо? *(And if it's very dry during the day?)*
> — **Дружина:** Якщо не буде дощу, доведеться полити ввечері. *(If there is no rain, we will have to water in the evening.)*
> — **Чоловік:** Добре. Якщо ти купиш насіння, я підготую грядку. *(Good. If you buy seeds, I will prepare the garden bed.)*
> — **Дружина:** Домовилися! Якщо буде **вільний** (free) час, ми приготуємо смачну вечерю надворі. *(Agreed! If there is free time, we will cook a delicious dinner outside.)*

Ми щодня плануємо наш день. Ми часто використовуємо слово «якщо», коли приймаємо рішення. Це дуже зручна граматика для повсякденного життя. Наприклад, ми дивимося на небо перед тим, як вийти з дому. Якщо ми бачимо темні хмари, ми беремо парасольку. Якщо на вулиці йде сильний дощ, ми можемо **залишитися** (to stay) вдома. Ми також часто використовуємо цю форму, коли просимо когось про послугу. Наприклад: «Якщо у магазині є свіжий хліб, купи, будь ласка». Тут перша частина показує **умову** (condition), а друга частина — це наше прохання або план. «Якщо завтра буде **вільний** (free) час, я піду в спортзал».

> *Every day we plan our day. We often use the word "якщо" when making decisions. This is very convenient grammar for everyday life. For example, we look at the sky before leaving the house. If we see dark clouds, we take an umbrella. If it is raining heavily outside, we might stay at home. We also often use this form when asking someone for a favor. For example: "If the store has fresh bread, please buy it." Here the first part shows the condition, and the second part is our request or plan. "If there is free time tomorrow, I will go to the gym."*

Складнопідрядні речення також чудово підходять, щоб давати **поради** (advice). В умові стоїть теперішній час, а в результаті — наказовий спосіб. Наприклад, ваш колега погано почувається на роботі. Ви кажете йому: «Якщо болить голова, випий таблетку і відпочинь». Тут немає майбутнього часу, бо хороший **результат** (result) потрібний людині прямо зараз. Батьки дуже часто використовують цю форму, коли серйозно говорять зі своїми дітьми. Друзі також постійно так спілкуються. Ви можете порадити новому студенту: «Якщо хочеш швидко вивчити мову, практикуй щодня і читай тексти». Слово «якщо» тут працює як чіткий маркер вашого життєвого досвіду. Ви ніби кажете: я знаю цю ситуацію і маю гарне рішення. Ви також обов'язково почуєте такі корисні конструкції від лікаря або викладача. Лікар скаже наприкінці візиту: «Якщо вам раптом буде гірше, одразу зателефонуйте мені». А викладач порадить: «Якщо ви не розумієте це правило, прочитайте текст ще раз удома». Це дуже ввічлива і граматично правильна форма сучасної комунікації. Вона завжди показує вашу щиру турботу про іншу людину.

:::info
**Grammar box: Imperative in the result clause**
When giving advice or instructions, use the present or future tense in the *якщо*-clause, and the imperative mood in the result clause.
:::

Іноді нам обов'язково потрібно попередити іншу людину про можливі проблеми або небезпеку. Для цього ми також активно використовуємо умовні речення, але часто додаємо заперечення. Ми ставимо частку «не» перед дієсловом, щоб показати негативну умову. Наприклад, мама вранці суворо каже сину: «Якщо не **поспішиш** (hurry), ти точно запізнишся до школи». Це абсолютно **реальний** (real) сценарій, який може статися дуже скоро. Або інша популярна фраза: «Якщо не візьмеш парасольку, ти точно змокнеш під дощем». Людина одразу розуміє, що вона повинна змінити свою поведінку просто зараз. Ми зазвичай використовуємо майбутній час в обох частинах речення, бо дія ще не відбулася. Якщо ви подорожуєте в Карпатах, ваш досвідчений гід може прямо сказати: «Якщо ви не будете уважно слухати мої команди, то ви дуже швидко заблукаєте в лісі». Тут маленька частка «то» робить це попередження ще більш серйозним і сильним. Знання цієї структури допомагає нам краще розуміти важливі попередження на вулиці чи на роботі.

Остання важлива функція таких складних речень — це наші щоденні обіцянки та домовленості. Коли ми домовляємося з кимось про спільну роботу, ми фактично створюємо словесний контракт. У цьому цікавому випадку слово «якщо» працює як наша гарантія. Наприклад, ви довго працюєте над складним та важливим проєктом в офісі. Ви кажете колезі: «Якщо ти **допоможеш** (help) мені з текстом, я допоможу з презентацією». Це абсолютно чесний і дуже логічний обмін вашим часом та зусиллями. Інший гарний приклад стосується наших надій та великих планів на найближче майбутнє. Ми часто кажемо рідним: «Якщо все буде добре, ми разом поїдемо у відпустку». Якщо ваші друзі активно планують домашню вечірку на вихідні, вони також домовляються між собою: «Якщо я куплю піцу і напої, то ви обов'язково принесете цікаві настільні ігри». У таких розмовах ми завжди використовуємо простий або складений майбутній час. Ці чіткі домовленості роблять наші людські стосунки набагато більш прозорими та зрозумілими.

<!-- INJECT_ACTIVITY: match-up-logical-results -->
<!-- INJECT_ACTIVITY: error-correction-verb-forms -->

## Якщо чи якби? Тільки реальна умова (Якщо or якби? Real Conditions Only) (~660 words total)

Understanding the difference between real and hypothetical conditions is a major milestone. You already know that we use the word **якщо** (if) for a real, possible condition. However, another word looks similar but has a completely different function: **якби** (if only). This word introduces an unreal or hypothetical situation.

Слово «якщо» завжди показує абсолютно **реальний** (real) сценарій або можливу ситуацію. Ми використовуємо його для розмов про факти або майбутні події. Вони дійсно можуть статися. Наприклад, ми дивимося на небо. Ми впевнено кажемо: «Якщо завтра буде сонце, ми підемо гуляти». Або ми плануємо наш вечір. Ми вирішуємо: «Якщо піде дощ, ми маємо **залишитися** (to stay) вдома». Це пряма і дуже логічна **умова** (condition). Вона має цілком можливий фінал у нашому житті.

Натомість слово «якби» працює зовсім інакше. Воно створює абсолютно нереальну ситуацію. Ми використовуємо його, коли мріємо або фантазуємо про певні речі. Це ситуація, яка існує тільки в нашій уяві. Наприклад, людина може сказати: «Якби я був птахом, я б літав». Але ця людина не є птахом. Це просто фізично неможливо. Тому ми маємо чітко розділяти ці два важливі слова.

At your current level, you only need to recognize **якби** when you hear it. You will encounter this word in songs, proverbs, or conversation. It often translates to "if only" and expresses a strong wish about something that cannot be changed.

Ви дуже часто будете чути це цікаве слово у розмовах. Ваш друг може сумно сказати: «Якби я знав усю правду!». Це означає, що він не знав правди в минулому. Тепер він просто шкодує про це. Ви також зустрінете такі форми у відомих віршах або народних піснях. Ваше головне завдання зараз — просто розуміти цей загальний зміст. Ви робите це, коли читаєте тексти або слухаєте музику.

Вам поки що не потрібно самостійно будувати такі складні речення. Для успішної комунікації вам цілком достатньо використовувати базову конструкцію. Ви можете вільно говорити про ваші поточні плани. Ваш колега просить вас **допомогти** (to help) з новим проєктом. Ви відповідаєте йому просто і чітко. Ви також використовуєте цю форму, коли даєте друзям гарну **пораду** (advice). Або ви можете попросити їх **поспішити** (to hurry) на важливу зустріч. Ви завжди можете тренувати ці практичні навички щодня.

<!-- INJECT_ACTIVITY: quiz-yakscho-vs-yakby -->

Now is a great time to review complex sentences. Over past lessons, you have built a strong foundation for expressing reasons, goals, and conditions. All these clause types work together to make your Ukrainian sound much more natural.

Ви вже знаєте багато корисних сполучників. Вони допомагають поєднувати прості ідеї у великі та красиві речення. Ми хочемо пояснити причину нашої дії. Тоді ми впевнено використовуємо слова «тому що» або «бо». Якщо ми робимо щось попри серйозні перешкоди, нам чудово допомагає слово «хоча». Коли ми говоримо про мету нашої роботи, ми завжди ставимо сполучник «щоб». Це дуже важливі інструменти для щоденного спілкування.

Спробуйте зробити короткий тест для себе. Чи можете ви зараз пояснити причину свого рішення? Чи можете ви описати об'єкт, використовуючи слова «який» або «де»? Чи знаєте ви, як правильно показати прямий **результат** (result) вашої дії? Звичайно, тепер ви також вмієте додавати умову, використовуючи слово **якщо** (if). Це означає, що ви можете вільно висловлювати думки. Робіть це, коли у вас є **вільний** (free) час для практики.

Finally, let's look at the intonation of conditional sentences. The way you use your voice is just as important as the grammar. Your pitch naturally guides the listener, showing them where the condition ends and the result begins.

Коли ми починаємо речення зі слова «якщо», наш голос має працювати за певним правилом. У першій частині речення знаходиться наша умова. Тут наша інтонація завжди йде вгору (↗). Цим підвищенням тону ми ніби даємо слухачу спеціальний сигнал. Ми кажемо: зачекай, це ще не кінець. Ваш співрозмовник автоматично розуміє, що думка ще не завершена. Він має уважно слухати вас далі.

Після короткої паузи починається друга частина речення. Вона містить наш логічний наслідок. Тут наша інтонація впевнено і спокійно йде вниз (↘). Це природне зниження голосу показує важливу річ. Воно означає, що думка нарешті повністю завершена. Наприклад: «Якщо завтра буде гарна **погода** (weather) ↗, ми підемо гуляти ↘». Спробуйте прочитати це речення вголос кілька разів. Ви одразу відчуєте цю красиву музику нашої мови.

:::info
**Grammar box: Intonation in complex sentences**
When a sentence starts with a subordinate clause (like a condition), the pitch naturally rises at the comma to indicate that the thought is incomplete. The main clause then follows with a falling pitch, signaling the end of the statement.
:::

### Читаємо українською

Сьогодні субота. Ми з друзями маємо чудові плани на вечір. Якщо буде тепло, ми підемо гуляти в центр міста. Ми хочемо купити смачну каву. Якщо ж піде дощ, ми зустрінемося вдома у Максима. Ми замовимо піцу і будемо грати в настільні ігри. Це завжди гарна ідея. Якщо всі будуть мати гарний настрій, ми також подивимося новий фільм. Я дуже люблю наші спільні вихідні.

> *Today is Saturday. My friends and I have wonderful plans for the evening. If it is warm, we will go for a walk in the city center. We want to buy delicious coffee. If it rains, we will meet at Maksym's house. We will order pizza and play board games. This is always a good idea. If everyone is in a good mood, we will also watch a new movie. I really love our shared weekends.*
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: real-conditionals
level: a2

# NOTE — these are SHAPE examples. The real targets are at the top of this prompt
# (12 total / 4–6 inline / 8–11 workbook,
# 8+ items per activity). The shapes below are TRUNCATED for readability;
# YOUR output MUST hit those minimums.

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:                     # ← real output: ≥ 8 items
      - question: "_____ стіл"
        options: ["мій", "моя", "моє", "мої"]
        correct: 0             # 0-based index
      - question: "Це ____ книга."
        options: ["мій", "моя", "моє", "мої"]
        correct: 1
      # ... add at least 8 items total — never stop at 1-2

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:                     # ← real output: ≥ 8 items
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]
      - sentence: "Це ____ вікно."
        answer: "моє"
        options: ["мій", "моя", "моє"]
      # ... ≥ 8 items total

workbook:
  - id: match-up-vocab
    type: match-up
    instruction: "З'єднайте пари"
    pairs:                     # ← real output: ≥ 8 pairs
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"
      # ... ≥ 8 pairs total

  - id: group-sort-gender
    type: group-sort
    instruction: "Розподіліть слова за категоріями"
    groups:
      - label: "Чоловічий рід"
        items: ["стіл", "олівець", "будинок"]   # ≥ 3 items per group
      - label: "Жіночий рід"
        items: ["книга", "ручка", "школа"]
      - label: "Середній рід"
        items: ["вікно", "море", "молоко"]

  - id: true-false-grammar
    type: true-false
    instruction: "Правда чи ні?"
    items:                     # ← real output: ≥ 8 items
      - statement: "«Книга» — це чоловічий рід."
        correct: false
        explanation: "Книга закінчується на -а, отже жіночий рід."
      # ... ≥ 8 items total

  - type: error-correction
    instruction: "Виправте помилку"
    items:
      - sentence: "Sentence with error"
        error: "wrong word"
        correction: "correct word"
        error_type: "word"
        options: ["option1", "option2", "option3"]
        explanation: "Why it's wrong"

  - type: observe
    examples:
      - "example sentence 1"
      - "example sentence 2"
    prompt: "What pattern do you notice?"

  - type: translate
    instruction: "Оберіть правильний переклад"
    items:
      - source: "English phrase"
        options:
          - text: "correct Ukrainian"
            correct: true
          - text: "wrong Ukrainian"
            correct: false

  - type: anagram
    instruction: "Складіть слово з літер"
    items:
      - letters: ["к", "н", "и", "г", "а"]
        answer: "книга"
        hint: "book"

  - type: order
    instruction: "Розставте речення в правильному порядку"
    items:                         # Lines displayed SHUFFLED to the learner
      - "— Служба порятунку, слухаю вас."
      - "— Допоможіть! Тут пожежа!"
      - "— Де ви?"
    correct_order: [0, 1, 2]       # TOP-LEVEL field, zero-based indices into items[]

  - type: unjumble
    instruction: "Складіть правильне речення зі слів"
    items:
      - words: ["швидку!", "Викличте"]            # Jumbled words
        correct_order: ["Викличте", "швидку!"]    # Words as STRINGS in correct order (NOT integers!)
      - words: ["потрібен", "Мені", "лікар."]
        correct_order: ["Мені", "потрібен", "лікар."]
        hint: "Dative + потрібен + noun"

  - type: error-correction
    instruction: "Знайдіть і виправте помилку"
    items:
      - sentence: "Мені потрібна лікар."
        error: "потрібна"
        correction: "потрібен"
        error_type: "word"           # MUST be one of: "word", "phrase", "register", "construction"
        options: ["потрібен", "потрібне", "потрібно"]
        explanation: "Лікар is masculine, so потрібен."
```

---

## Activity Type Reference

**CRITICAL RULE: EVERY single activity object MUST include an `id` field (a unique string like "quiz-grammar", "match-up-vocab"). Do NOT generate an activity without an `id`.**

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: id, instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]. **CRITICAL: use `____` (four underscores) for the blank, NOT `{word}` curly-brace syntax. Example: `sentence: "Це ____ кімната."` with `answer: "моя"`. The validator REJECTS `{word}` format.**
- **match-up**: Pair matching. Required: id, instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: id, instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: id, instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: id, instruction, items[{sentence, error, correction}]. Optional: error_type (MUST be one of: `"word"`, `"phrase"`, `"register"`, `"construction"` — NOT "grammar"), options[], explanation
- **anagram**: Letter rearrangement. Required: id, instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: id, instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: id, instruction, items[{words[], correct_order[]}]. ⚠️ correct_order is an array of **STRINGS** (the words in correct order), NOT integers!
- **order**: Sentence/line ordering. Required: id, instruction, items[] (array of strings), correct_order[] (TOP-LEVEL array of **integers** — zero-based indices into items). ⚠️ correct_order is a TOP-LEVEL field next to items, NOT inside each item.
- **observe**: Pattern discovery. Required: id, examples[], prompt
- **classify**: Multi-category sort. Required: id, instruction, categories[{label, items[]}]

### Ukrainian pedagogy types (A1 phonetics/syllables):
- **divide-words**: Interactive syllable division. Required: id, instruction, items[{word, answer}]. Optional: hint. Example: word: "молоко", answer: "мо-ло-ко"
- **count-syllables**: Count syllables in a word. Required: id, items[{word, correct}]. Optional: instruction, maxCount, translation. Example: word: "яблуко", correct: 3
- **pick-syllables**: Select syllables matching criteria. Required: id, syllables[], correctIndices[], category. Example: syllables: ["ка", "май", "ре"], correctIndices: [1], category: "закриті"
- **odd-one-out**: Find the word that doesn't belong. Required: id, items[{words[], correct, explanation}]. `correct` is 0-based index. Example: words: ["кіт", "пес", "молоко"], correct: 2, explanation: "молоко — 3 syllables, rest have 1"
- **image-to-letter**: See image/emoji, identify letter. Required: id, instruction, items[{image, letter}]. Optional: options[]
- **letter-grid**: Letter reference grid. Required: id, letters[{upper, lower}]. Optional: name, emoji, key_word, sound_type
- **watch-and-repeat**: Watch video, repeat pronunciation. Required: id, items[{video}]. Optional: letter, word, note
- **phrase-table**: Grouped phrases for communication patterns. Required: id, groups[{label, phrases[]}]

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: id, prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Required: id, passage, questions[]
- **source-evaluation**: Required: id, source_text, criteria[], guiding_questions[]

---

## Learner Level Context

**Level: A2 (Module 51/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-verbs-present [§4.2.4.1]
**Дієвідмінювання в теперішньому часі** (Present tense conjugation)
- **fill-in** — Відмінюй дієслово: Вставити правильну форму дієслова за особою та числом / Fill in correct verb conjugation for given person/number
  - Instruction: *Вставте правильну форму дієслова*
- **group-sort** — І чи ІІ дієвідміна?: Розподілити дієслова за типом дієвідміни / Sort verbs by conjugation class (I vs II)
- **match-up** — Особа → форма: Зіставити особові займенники з формами дієслова / Match personal pronouns to verb conjugation forms
  - Instruction: *З'єднайте*
- **error-correction** — Виправ дієслово: Знайти неправильно відмінене дієслово та виправити / Find incorrectly conjugated verb and fix it
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує відмінювання. Англійські дієслова не змінюються за особами

### Pattern: grammar-pronouns [§4.2.1.4, §4.2.2]
**Особові займенники** (Personal pronouns)
- **match-up** — Займенник → дієслово: Зіставити особовий займенник із правильною формою дієслова — зв'язок займенника з дієвідмінюванням / Match personal pronoun with correct verb form — linking pronouns to conjugation
  - Instruction: *З'єднайте займенник із дієсловом*
- **fill-in** — Вставте займенник: Обрати правильний займенник за контекстом речення / Choose the correct pronoun based on sentence context
  - Instruction: *Вставте правильний займенник*
- **group-sort** — Однина чи множина?: Розподілити займенники на однину та множину / Sort pronouns into singular and plural
  - Instruction: *Розподіліть*
- **quiz** — Ти чи Ви?: Обрати правильну форму звертання — неформальне (ти) чи ввічливе (Ви) / Choose correct address form — informal (ти) vs polite (Ви)
**Anti-patterns (DO NOT generate):**
- ❌ translate: Займенники — про зв'язок з дієсловом, а не переклад

### Pattern: grammar-verb-aspect [A2 §4.2.3.1, B1 §4.2.3.1]
**Вид дієслова** (Verb aspect)
- **group-sort** — Доконаний чи недоконаний?: Розподілити дієслова за видом — розпізнати видові пари / Sort verbs by aspect — recognize aspect pairs
  - Instruction: *Розподіліть дієслова за видами*
- **match-up** — Утвори видові пари: Зіставити недоконане з доконаним дієсловом / Match imperfective ↔ perfective aspect pairs
  - Instruction: *З'єднайте видові пари*
- **fill-in** — Який вид доречний?: Обрати правильний вид для контексту (тривалість vs завершеність) / Choose correct aspect for context (duration vs completion)
  - Instruction: *Оберіть правильну форму*
- **quiz** — Визнач вид дієслова: Визначити вид поданого дієслова / Identify aspect of a given verb
**Anti-patterns (DO NOT generate):**
- ❌ translate: Англійський минулий час НЕ відповідає 1:1 українському виду. «I read» = і «читав», і «прочитав»
- ❌ quiz-only: Вид — це вибір мовця. Учні мають практикувати вибір виду в контексті, а не тільки розпізнавати


**You MUST use these patterns.** The pedagogy patterns encode how Ukrainian teachers actually test each concept. For each matched pattern:
1. Generate **at least one activity of each recommended type** from the pattern. If the pattern lists divide-words, count-syllables, and odd-one-out — your output MUST include all three.
2. Follow the anti-patterns — if a type is listed under "DO NOT generate", do NOT use it for this topic.
3. Use the Ukrainian instruction (назва / instruction_uk) when the level allows Ukrainian instructions.

---

## Quality Rules

**ACTIVITY COUNT MINIMUMS (non-negotiable, audit-enforced):**
- **Total: 12 activities.** Inline: 4–6. Workbook: 8–11. The audit gate FAILS the module if you ship fewer.
- **Type diversity: workbook MUST cover ≥5 distinct activity types.** A wall of quizzes is rejected. Quiz + true-false combined ≤ 25% of workbook.
- **Match the inline markers exactly.** Every `<!-- INJECT_ACTIVITY: id -->` marker in the prose needs a matching inline activity with that exact id. Skipping markers means the lesson tab is broken.

**ITEM COUNT MINIMUMS (non-negotiable, per-activity):**
- **Default minimum: 8 items per activity.** Quiz, fill-in, match-up, true-false, anagram, error-correction, translate, cloze, mark-the-words, divide-words, count-syllables, odd-one-out, group-sort categories: all ≥ 8.
- **Lower minimums for specific types only:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items, essay-response/critical-analysis = 1 prompt.
- If you can't think of enough items, add more examples from the module's vocabulary and content. NEVER ship a 1-item or 2-item activity unless its type cap explicitly allows it.
- **Exactly 4 options per quiz question at A2+** — enough to prevent guessing, not so many to overwhelm. A1 allows 3-4.
- **BINARY CONCEPTS (e.g., НВ/ДВ, masculine/feminine, true/false):** Do NOT use `quiz` with only 2 options — use `true-false` (for statement evaluation) or `group-sort` (for categorization) instead. Quiz type requires 4 options at A2+.

**Instructions match learner level:**
1. **A1.1 (M01-M07):** Instructions in ENGLISH. The learner is a complete beginner who cannot read Ukrainian yet. They are learning the alphabet and first words. Use activity types: image-to-letter, letter-grid, match-up (letter↔sound), quiz (in English about Ukrainian sounds/letters). Anna Ohoiko's pronunciation videos should be referenced where relevant.
2. **A1.2-A1.3 (M08-M21):** Instructions in simple English with Ukrainian key terms in bold. Learner knows basic words but not grammar terminology.
3. **A1.4+ (M22-M55):** Instructions can be in simple Ukrainian with English translation in parentheses.
4. **A2+:** Instructions in Ukrainian.
5. **B1+:** Full Ukrainian, no English.

**Other rules:**
6. **No duplicate options** — each option in a quiz item must be unique
7. **Answer must be in options** — for quiz items, `correct` must be a valid index. For fill-in with options, `answer` must appear in `options`.
8. **Plausible distractors** — wrong options should be real Ukrainian words that test the specific skill. Not random words.
9. **Min 6 pairs for match-up** — to prevent trivial elimination
10. **Explanations for true-false and error-correction** — help the learner understand WHY
11. **Test LANGUAGE, not trivia** — exercises must test Ukrainian language skills. Not "In what year..." factual recall.

---

## Verification Tools (MCP)

Use these tools to verify your exercise content:



---

## Live Verification Tools (MCP)

You have access to RAG-powered MCP tools to verify Ukrainian language constructs **live as you write**. The research phase is already complete; use these tools strictly for targeted verification to ensure zero Russianisms, accurate grammar, and authentic usage.

**Core Tools:**
- `mcp_rag_verify_words` / `mcp_rag_verify_word` / `mcp_rag_verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms). Returns full declension/conjugation.
- `mcp_rag_search_text` — Ukrainian school textbooks (Grades 1-11, 23K chunks).
- `mcp_rag_search_literary` — Primary literary sources (chronicles, poetry, legal texts).
- `mcp_rag_query_pravopys` — Official Ukrainian orthography rules (Правопис 2019).
- `mcp_rag_query_wikipedia` — Ukrainian Wikipedia.

**Dictionary Tools (NEW — use these for quality):**
- `mcp_rag_search_style_guide` — **Антоненко-Давидович (279 entries). HIGH PRIORITY.** Identifies calques and Russianisms. Use when unsure if a phrase is natural Ukrainian.
- `mcp_rag_query_cefr_level` — PULS CEFR vocabulary (5.9K words). Check if a word is level-appropriate (A1/A2/B1 etc.).
- `mcp_rag_search_definitions` — СУМ-11 (127K entries). Look up exact Ukrainian definitions.
- `mcp_rag_search_etymology` — Грінченко (67K entries). Historical forms, etymology.
- `mcp_rag_search_idioms` — Фразеологічний (25K entries). Find natural Ukrainian idioms.
- `mcp_rag_search_synonyms` — Ukrajinet WordNet (122K synsets). Synonyms, antonyms.
- `mcp_rag_translate_en_uk` — Балла EN→UK (79K entries). English→Ukrainian translations.
- `mcp_rag_query_grac` — GRAC corpus (2B tokens). Check word frequency, collocations, concordance. Use when unsure if a collocation is natural.
- `mcp_rag_query_ulif` — ULIF morphological paradigms. Full declension/conjugation tables. Use when verify_lemma isn't enough.
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Use when you suspect a word might be a Russicism — finds the proper Ukrainian alternative.

**WHEN to use tools (Specific Triggers):**

1. **Suspected Russianisms or Surzhyk (HIGH PRIORITY):**
   - *Trigger:* You are about to use a word that sounds similar to Russian, a calque, or you are unsure of its exact Ukrainian equivalent.
   - *Action:* Use `mcp_rag_search_style_guide` first (it knows calques). Then `mcp_rag_query_r2u` for the proper Ukrainian equivalent. Then verify with `mcp_rag_verify_words`.
   - *Example:* Checking *приймати участь* (calque) → *брати участь* (correct).

2. **Vocabulary Level Check:**
   - *Trigger:* You are writing for A1/A2 and want to ensure words are level-appropriate.
   - *Action:* Use `mcp_rag_query_cefr_level` to verify the word's CEFR level.

3. **Grammar & Morphology Doubts:**
   - *Trigger:* You are unsure about a case ending, irregular plural, or conjugation.
   - *Action:* Use `mcp_rag_verify_lemma` to pull the complete declension/conjugation.

4. **Natural Expressions:**
   - *Trigger:* You need a natural idiom or collocation for a dialogue.
   - *Action:* Use `mcp_rag_search_idioms` for Ukrainian expressions, `mcp_rag_search_synonyms` for word variety.

5. **Drafting Grammar Rules:**
   - *Trigger:* You are explaining a spelling or phonetic rule.
   - *Action:* Use `mcp_rag_query_pravopys` to confirm the exact 2019 standard.

6. **Checking Collocations & Frequency:**
   - *Trigger:* You want to confirm a word combination is actually used by native speakers.
   - *Action:* Use `mcp_rag_query_grac` with mode='collocations' to see real-world usage.

**MANDATORY Verification (these are NOT optional):**

7. **Letter/Sound Decomposition (ALWAYS VERIFY):**
   - *Trigger:* You are listing the letters, sounds, or syllables of ANY Ukrainian word.
   - *Action:* BEFORE writing the decomposition, call `mcp_rag_verify_word` on that word. The response shows the exact letter forms. Use ONLY what the tool returns. NEVER decompose a word from memory — your pre-training has wrong letter mappings (e.g., confusing и/і, я/а in specific words). This is the #1 source of errors.
   - *Example:* Before writing 'вулиця has letters В, У, Л...', call `mcp_rag_verify_word("вулиця")` and copy the letters from the result.

8. **Phonetic Claims (ALWAYS VERIFY):**
   - *Trigger:* You are stating how a letter sounds in a specific word, how many syllables a word has, or where stress falls.
   - *Action:* Call `mcp_rag_verify_word` to confirm. Ukrainian letters like є, ї, я, ю change sound value depending on position (after consonant vs word-initial). Do NOT guess — verify each claim.

9. **ANY Factual Claim About Ukrainian (VERIFY WHEN POSSIBLE):**
   - *Trigger:* You are stating a grammar rule, exception, or linguistic fact.
   - *Action:* Use `mcp_rag_query_pravopys` or `mcp_rag_search_text` to confirm. If you can't verify it, flag with `<!-- VERIFY: claim -->`.

**Efficiency Rules:**
- **Batch your checks:** Use `mcp_rag_verify_words` with 5-15 words at once.
- **Do NOT verify basic words:** *мама*, *стіл*, *робити* don't need checking.
- **Zero invention:** If VESUM doesn't know a word, don't use it.
- **Target: 10-20 tool calls per module** (was 8-15; mandatory checks added).

IMPORTANT: After using tools, output your COMPLETE module content as plain text. Do NOT narrate your tool usage. Just output the final module content.


**Verification checklist:**
1. Run `verify_words` on all Ukrainian words in your exercises — every word must exist in VESUM
2. Run `query_cefr_level` on any word you're unsure about — it must be a2-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## ⚠️ MANDATORY FINAL CHECKLIST — verify before emitting YAML

Walk through this checklist explicitly before you start emitting. If ANY box is unchecked, fix it FIRST.

- [ ] My output has **at least 4** inline activities (one per `<!-- INJECT_ACTIVITY -->` marker).
- [ ] My output has **at least 8** workbook activities.
- [ ] **Total ≥ 12.**
- [ ] **Every** activity has **at least 8** items, pairs, or statements (except types with explicitly lower caps: order=3, observe=2, pick-syllables=4, watch-and-repeat=3, essay-response=1).
- [ ] The module (inline + workbook combined) uses **at least 0 distinct activity types** (or 4+ when 0 = 0 and the workbook size allows it). I am NOT shipping a wall of quizzes.
- [ ] Quiz + true-false combined are roughly ≤25% of the workbook (quality target — lean on `WORKBOOK_PRIORITY_TYPES` instead).
- [ ] I prioritized types from `WORKBOOK_PRIORITY_TYPES` (heavy practice formats), not just easy-to-write quizzes.
- [ ] I used ZERO types from `FORBIDDEN_ACTIVITY_TYPES`.
- [ ] All fill-in items use `____` blanks, NOT `{word}` curly-brace syntax.
- [ ] My inline count is between 4 and 6. I did NOT create more injection markers than 6.
- [ ] Every Ukrainian word in my items appears in the prose or in `PLAN_VOCABULARY`.
- [ ] At B1+, all instructions are in Ukrainian (no English fallback).

If you cannot tick all of these, REGENERATE the activities BEFORE outputting. Shipping under-spec means the build rejects you and the heal loop has to redo your work — wasting compute.

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
