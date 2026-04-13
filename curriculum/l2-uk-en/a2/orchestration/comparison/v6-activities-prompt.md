<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/comparison.yaml` file for module **54: Більше, краще, найкраще** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-comparative -->`
- `<!-- INJECT_ACTIVITY: true-false-constructions -->`
- `<!-- INJECT_ACTIVITY: match-up-match-adjective-to-its-superlative-form -->`
- `<!-- INJECT_ACTIVITY: quiz-irregular-forms-choose-the-correct-suppletive-form -->`
- `<!-- INJECT_ACTIVITY: error-correction-double-comparisons-find-and-fix-wrong-comparative-and-superlative-forms-e-g -->`
- `<!-- INJECT_ACTIVITY: match-up-superlatives-match-adjective-to-its-superlative-form -->`
- `<!-- INJECT_ACTIVITY: true-false-comparative-constructions-identify-correct-and-incorrect-comparative-constructions -->`
- `<!-- INJECT_ACTIVITY: fill-in-comparative-form-the-comparative-from-the-base-adjective -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Form the comparative from the base adjective
  items: 8
  type: fill-in
- focus: Choose the correct suppletive form (більший, кращий, гірший)
  items: 8
  type: quiz
- focus: Match adjective to its superlative form
  items: 8
  type: match-up
- focus: Identify correct and incorrect comparative constructions
  items: 8
  type: true-false
- focus: Find and fix wrong comparative and superlative forms (e.g., *більш кращий
    → кращий, *гарніший → кращий/гарніший)
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- набагато (much, significantly)
- трохи (a little, slightly)
- значно (considerably)
- навпаки (on the contrary)
required:
- порівняння (comparison)
- більший (bigger)
- менший (smaller)
- кращий (better)
- гірший (worse)
- найкращий (the best)
- найбільший (the biggest)
- солодший (sweeter)
- цікавіший (more interesting)
- ніж (than)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Вищий ступінь: порівнюємо два предмети (~715 words)

Сьогодні ми вивчаємо **порівняння** (comparison). Ми часто порівнюємо предмети, людей або ситуації. Ми хочемо знати, який варіант **кращий** (better) або який **гірший** (worse). 

Кожен хоче вибрати **найкращий** (the best) варіант або мати **найбільший** (the biggest) успіх. Для цього ми використовуємо вищий ступінь. Прочитайте коротку розмову.

> — **Олена:** Що ти любиш пити вранці: каву чи чай? *(What do you like to drink in the morning: coffee or tea?)*
> — **Андрій:** Я думаю, що кава смачніша. *(I think coffee is tastier.)*
> — **Олена:** А я вважаю, що зелений чай корисніший. *(And I consider that green tea is healthier.)*
> — **Андрій:** Можливо, ти маєш рацію. Але гаряча кава дає більше енергії. *(Maybe you are right. But hot coffee gives more energy.)*
> — **Олена:** Зате чай дешевший. *(On the other hand, tea is cheaper.)*

В українській мові ми маємо просту форму для порівняння. Це найбільш природний спосіб. Щоб утворити цю форму, ми додаємо спеціальні суфікси до основи прикметника. Ми використовуємо суфікси «-ший» або «-іший». Наприклад, слово «солодкий» змінюється і звучить як **солодший** (sweeter). Інший приклад — слово «теплий». Ми додаємо суфікс і маємо слово «тепліший». Слово «дешевий» перетворюється на «дешевший». Ця проста форма часто звучить у розмовах та літературі. Українці дуже люблять використовувати ці короткі слова. Вони роблять нашу мову швидкою та мелодійною.

> *In the Ukrainian language, we have a simple form for comparison. This is the most natural way. To form this, we add special suffixes to the adjective stem. We use the suffixes "-ший" or "-іший". For example, the word "солодкий" changes and sounds like "солодший" (sweeter). Another example is the word "теплий". We add a suffix and have the word "тепліший". The word "дешевий" turns into "дешевший". This simple form often sounds in conversations and literature. Ukrainians really love to use these short words. They make our language fast and melodic.*

Коли ми додаємо суфікс «-ший», деякі приголосні звуки змінюються. Це регулярний фонетичний процес. Якщо основа прикметника закінчується на літери «г», «ж» або «з», ми маємо зміну. Ці звуки разом із суфіксом перетворюються на «жч». Наприклад, слово «дорогий» стає словом «дорожчий». Слово «близький» перетворюється на «ближчий». Інше важливе правило стосується літери «с». Якщо основа має літеру «с» в кінці, вона перетворюється на «щ». Тому слово «високий» стає словом «вищий». Також суфікси «-к-», «-ок-», «-ек-» зазвичай випадають перед утворенням нової форми. Слово «тонкий» перетворюється на «тонший», а слово «глибокий» стає словом «глибший». Спочатку ці зміни здаються складними, але ви швидко до них звикнете.

Існує також складена форма порівняння. Для цього ми використовуємо додаткові слова. Ми беремо слова «більш» або «менш» і додаємо звичайний прикметник. Наприклад, ми можемо сказати «більш солодкий» або «менш відомий». Ця конструкція часто зустрічається в офіційних документах або наукових текстах. Ми також використовуємо її, коли прикметник дуже довгий. Однак проста форма із суфіксами завжди є пріоритетною. Вона звучить більш природно в щоденному спілкуванні. Тому ми радимо вам частіше говорити **цікавіший** (more interesting), а не «більш цікавий». Використовуйте складену форму тільки тоді, коли проста форма звучить дивно або важко вимовляється. Це зробить вашу розмову живою та правильною.

Як правильно побудувати речення для порівняння двох предметів? Ми маємо два зручні варіанти. Перший варіант використовує слово **ніж** (than) та називний відмінок. Наприклад: «Київ **більший** (bigger), ніж Львів». Це дуже чітка і зрозуміла конструкція. Другий варіант використовує прийменники «за» або «від» та знахідний відмінок. Наприклад: «Київ більший за Львів». Обидва варіанти є абсолютно правильними та взаємозамінними. Ви можете вільно обирати той, який вам більше подобається. Мій новий телефон **менший** (smaller), але він набагато кращий за старий. У розмовній мові українці дуже часто використовують прийменник «за». Конструкція зі словом «ніж» трохи частіше зустрічається в текстах. Головне правило — завжди пам'ятати про правильний відмінок після цих маленьких слів.

Тут є одна дуже важлива деталь. Деякі люди роблять помилку, коли порівнюють предмети. Вони використовують родовий відмінок без прийменників. Наприклад, можна почути таку фразу: «сталь міцніше міді». Це неправильно. Така граматична конструкція є типовою для російської мови. Вона не є природною для української. Українська мова має власні правила. Чиста українська мова вимагає використання слів «за», «від» або «ніж». Правильно говорити: «сталь міцніша за мідь». Завжди звертайте увагу на ці слова. Уникайте прямого копіювання граматики з інших мов.

> *There is one very important detail here. Some people make a mistake when comparing objects. They use the Genitive case without prepositions. For example, you can hear the phrase: "сталь міцніше міді". This is incorrect. Such a grammatical construction is typical for the Russian language. It is not natural for Ukrainian. The Ukrainian language has its own rules. Pure Ukrainian language requires the use of the words "за", "від", or "ніж". It is correct to say: "сталь міцніша за мідь". Always pay attention to these words. Avoid direct copying of grammar from other languages.*

:::info
**Grammar box**
Remember to always use the prepositions **за** or **від** + Accusative, or the conjunction **ніж** + Nominative when comparing two items. Avoid using the naked Genitive case, which is a grammatical transfer from Russian.
:::

<!-- INJECT_ACTIVITY: fill-in-comparative -->
<!-- INJECT_ACTIVITY: true-false-constructions -->

## Найвищий ступінь: хто найкращий? (~550 words)

> — **Марко:** Яке місто найбільше в Україні? *(Which city is the biggest in Ukraine?)*
> — **Оксана:** Звичайно, Київ. А яке місто найкраще? *(Of course, Kyiv. And which city is the best?)*
> — **Марко:** Для мене найкращий — мій рідний Харків. *(For me, the best is my native Kharkiv.)*
> — **Оксана:** А яка пора року найгарніша? *(And what season is the most beautiful?)*
> — **Марко:** Осінь. Це ідеальний час для подорожей. *(Autumn. It's the perfect time for traveling.)*

Сьогодні ми говоримо про найвищий ступінь **порівняння** (comparison). Це граматична форма, яка показує абсолютну перевагу одного предмета над усіма іншими. Ми використовуємо цю зручну конструкцію дуже часто. Вона показує, що певний об'єкт — це **найбільший** (the biggest) або **найкращий** (the best) вибір у групі.

Проста форма найвищого ступеня утворюється дуже легко. Нам потрібен лише спеціальний префікс. Ми беремо прикметник у вищому ступені і додаємо префікс «най-». Наприклад, до слова **солодший** (sweeter) ми додаємо префікс і отримуємо «найсолодший». Слово «тепліший» перетворюється на «найтепліший». А **цікавіший** (more interesting) текст швидко стає «найцікавішим». Ця проста форма є найпопулярнішою в мові. Ви будете чути її щодня. Люди люблять використовувати цю коротку форму, бо вона звучить природно.

> *The simple form of the superlative degree is formed very easily. We only need a special prefix. We take an adjective in the comparative degree and add the prefix "най-". For example, to the word **солодший** (sweeter) we add the prefix and get "найсолодший". The word "тепліший" turns into "найтепліший". And a **цікавіший** (more interesting) text quickly becomes "найцікавішим". This simple form is the most popular in the language. You will hear it every day. People love to use this short form because it sounds natural.*

Існує також складена форма найвищого ступеня. Для її утворення ми використовуємо слова «найбільш» або «найменш». Ми ставимо їх перед початковою формою звичайного прикметника. Цей спосіб часто зустрічається в документах або статтях. Однак пам'ятайте важливе правило. Проста форма з префіксом «най-» завжди має величезну перевагу. Цей варіант **кращий** (better), **ніж** (than) складена форма у повсякденних розмовах. Навіть якщо новий телефон **менший** (smaller) за розміром, ми оберемо префікс. Ми скажемо, що він найкращий, а не «найбільш хороший».

Іноді нам потрібно зробити максимальний акцент на якості. Ми хочемо показати абсолютний максимум. Для такого підсилення українська мова має два префікси: «якнай-» та «щонай-». Ми додаємо їх до простої форми. Наприклад, якщо ваш бюджет **більший** (bigger), ви можете знайти щонайкращий варіант подорожі. Не знати ці префікси — це **гірший** (worse) сценарій для вашого рівня. Ці маленькі частини слова роблять вашу мову дуже виразною та багатою.

> *Sometimes we need to put maximum emphasis on quality. We want to show the absolute maximum. For such reinforcement, the Ukrainian language has two prefixes: "якнай-" and "щонай-". We add them to the simple form. For example, if your budget is **більший** (bigger), you can find the absolute best travel option. Not knowing these prefixes is a **гірший** (worse) scenario for your level. These small parts of the word make your speech very expressive and rich.*

:::info
**Grammar box**
A critical difference between Ukrainian and Russian is how the superlative is formed. You might hear some people use the word **самий** before an adjective to create a superlative (e.g., <!-- VERIFY -->*самий великий*, <!-- VERIFY -->*самий кращий*). This is a direct Russianism and a major grammatical error in standard Ukrainian. Pure Ukrainian exclusively uses the **най-** prefix for the simple form, or **найбільш** for the compound form (**найбільший**, **найкращий**, **найбільш цікавий**). Never use "самий" to mean "the most".
:::

Завжди звертайте увагу на чистоту вашої мови. Використання слова «самий» для утворення найвищого ступеня є грубою помилкою. Це пряме запозичення з російської граматики, яке псує красу українського речення. Справжня українська мова вимагає використання виключно префікса «най-». Тому ми завжди говоримо «найбільший» замість помилкового варіанту. Ми кажемо «найкращий», коли описуємо щось ідеальне. Якщо ви чуєте слово «самий» поруч із прикметником, знайте правду. Це звичайна мовна калька. Ваша мета — говорити правильно і природно. Тому обирайте традиційні українські префікси. Це покаже вашу повагу до культури.

<!-- INJECT_ACTIVITY: match-up-match-adjective-to-its-superlative-form -->

## Особливі форми: більший, кращий, гірший (~495 words)

In Ukrainian, a few very common adjectives completely change their root when forming degrees of comparison, and these irregular forms must be memorized.

В українській мові є кілька особливих слів. Зазвичай ми додаємо суфікс до основи, як у словах **солодший** (sweeter) або **цікавіший** (more interesting). Але деякі прикметники повністю змінюють свій корінь, коли ми утворюємо **порівняння** (comparison). Це дуже давні і популярні слова. Вони мають унікальну історію. Ви не можете використовувати стандартні правила для них. Вам потрібно просто запам'ятати їхні нові особливі форми. Ви будете чути їх щодня у звичайних розмовах.

Ми часто порівнюємо розмір різних предметів. Слово «великий» має форму вищого ступеня **більший** (bigger). Найвищий ступінь для цього слова — **найбільший** (the biggest). Наприклад, мій новий стіл більший, ніж старий. Але стіл у вітальні — найбільший у нашому будинку. Слово «малий» також має особливі форми. Його вищий ступінь — **менший** (smaller). Найвищий ступінь звучить як найменший. Ця кімната менша, але вона дуже затишна. Мій молодший брат — найменший у нашій родині.

> *We often compare the size of different objects. The word "великий" has the comparative form "більший". The superlative degree for this word is "найбільший". For example, my new table is bigger than the old one. But the table in the living room is the biggest in our house. The word "малий" also has special forms. Its comparative degree is "менший". The superlative degree sounds like "найменший". This room is smaller, but it is very cozy. My younger brother is the smallest in our family.*

Коли ми говоримо про якість, ми використовуємо слова «добрий» або «гарний». Їхня спільна форма вищого ступеня — **кращий** (better) або іноді «ліпший». Найвищий ступінь — **найкращий** (the best). Цей ресторан кращий, ніж той заклад на розі. Моя мама готує найкращий борщ у світі. Для слова «поганий» ми використовуємо форму **гірший** (worse). Найвищий ступінь — найгірший. Це був найгірший день у моєму житті. Пам'ятайте, що для опису краси обличчя ми можемо сказати «гарніший». Але слово «кращий» є стандартним для будь-якого загального порівняння.

> *When we talk about quality, we use the words "добрий" or "гарний". Their common comparative form is "кращий" or sometimes "ліпший". The superlative degree is "найкращий". This restaurant is better than that place on the corner. My mom cooks the best borscht in the world. For the word "поганий" we use the form "гірший". The superlative degree is "найгірший". This was the worst day of my life. Remember that to describe facial beauty we can say "гарніший". But the word "кращий" is standard for any general comparison.*

:::tip
**Читаємо українською**

Цікаво, що прислівники від цих прикметників теж повністю змінюють свій вигляд. Прислівник «добре» перетворюється на слово краще. Прислівник «погано» стає словом гірше. Слово «багато» має форму порівняння більше. Слово «мало» змінюється на форму менше. Наприклад, лікар каже, що треба їсти більше корисної їжі. Якщо ви хочете бути здоровими, вам варто менше сидіти. Ви сьогодні читаєте краще, **ніж** (than) учора. Цей студент написав тест гірше за інших. Наша мета — щодня знати трохи більше.
:::

:::info
**Grammar box**

A very common mistake for learners is the "double comparison." Because forms like **кращий** or **більший** are already in the comparative degree, you must *never* add the word **більш** in front of them. Forms like <!-- VERIFY -->*більш кращий* or <!-- VERIFY -->*найбільш найпопулярніший* are logically redundant and incorrect. You must choose either the prefix/suffix approach (the simple form) OR the separate word (the compound form), but never both at the same time. Always say **кращий**, never <!-- VERIFY -->*більш кращий*.
:::

<!-- INJECT_ACTIVITY: quiz-irregular-forms-choose-the-correct-suppletive-form -->
<!-- INJECT_ACTIVITY: error-correction-double-comparisons-find-and-fix-wrong-comparative-and-superlative-forms-e-g -->

## Порівняння у житті (~440 words)

When shopping, making a good **порівняння** (comparison) is an essential skill. Sometimes you want a screen that is **більший** (bigger), but you also want a phone that is **менший** (smaller) for your pocket. It helps you weigh your options carefully. Let's look at a common situation where a customer compares items before making a purchase.

> — **Покупець:** Добрий день! Я шукаю новий смартфон. Який телефон ви порадите? *(Good day! I am looking for a new smartphone. Which phone do you recommend?)*
> — **Консультант:** Добрий день! Зверніть увагу на ці дві популярні моделі. Цей телефон більший, але він також дорожчий. *(Good day! Pay attention to these two popular models. This phone is bigger, but it is also more expensive.)*
> — **Покупець:** А той інший варіант? *(And that other option?)*
> — **Консультант:** Той дешевший, але менший. Його батарея також слабша. *(That one is cheaper, but smaller. Its battery is also weaker.)*
> — **Покупець:** Я люблю дивитися фільми. Який найкращий для відео? *(I love watching movies. Which is the best for video?)*
> — **Консультант:** Для фільмів найкращий — той, що має найбільший екран та кращий звук. *(For movies, the best is the one that has the biggest screen and better sound.)*
> — **Покупець:** Зрозуміло. Тоді я візьму більший. *(Understood. Then I will take the bigger one.)*

:::tip
**Читаємо українською**

У цій вправі ми порівнюємо українські міста для ідеальної відпустки.

Україна має багато чудових місць для відпочинку, але кожне місто пропонує щось своє. Київ — це столиця, і він має найбільше населення та найшвидший ритм життя. Це найбільше місто країни. Тут ви знайдете найсучасніші ресторани та найбільші парки. Київ також має найдовшу лінію метро. Львів значно компактніший, але для багатьох туристів він **цікавіший** (more interesting). Його архітектура старіша, вулиці вужчі, а місцева кава, мабуть, **солодша** (sweeter) та ароматніша. Люди часто кажуть, що у Львові найромантичніша атмосфера. Одеса — це морська перлина на півдні. Влітку клімат там найтепліший, пляжі найпопулярніші, але ціни часто вищі, ніж в інших регіонах. Життя біля моря завжди трохи дорожче. Якщо ви шукаєте абсолютний спокій, їдьте в Карпати. Тамтешні міста пропонують найчистіше повітря та найкрасивіші маршрути. Гори там найвищі, а ліси найгустіші. Яке місто найкраще для вас? Це повністю залежить від ваших інтересів та планів на відпочинок. Хтось любить галасливі мегаполіси, а хтось обирає тихі гірські села.
:::

Sometimes we need to add nuance to our descriptions. You can use conversational modifiers to show exactly how much things differ. This is especially useful when the difference is extremely small or very large. The most common modifiers are **набагато** (much), **трохи** (a little), and **значно** (considerably).

Ці слова допомагають зробити ваше мовлення більш точним та природним. Ми ставимо їх перед прикметником або прислівником у вищому ступені. Наприклад, мій новий комп'ютер набагато кращий за старий. Ця куртка трохи більша, тому вона сидить зручніше. Львів значно цікавіший для туристів, ніж багато промислових міст. Моя сестра бігає набагато швидше, ніж я. Цей новий маршрут трохи коротший. Працювати вдома часто значно приємніше. Вчити граматику з прикладами набагато веселіше. Ви можете використовувати ці слова щодня, щоб показати різницю між двома речами.

Let's recap the golden rules of forming comparatives and superlatives. These rules are the foundation of expressing your opinions and preferences clearly.

:::info
**Grammar box**

To summarize, always prioritize the simple forms with the `-ший` suffix or the `най-` prefix for everyday speech. You must memorize the irregular forms. The most important ones are **кращий** (better) and **гірший** (worse). When joining two things in a sentence, always use **за** (+ Accusative) or **ніж** (+ Nominative). Finally, never use the word <!-- VERIFY -->*самий* to form the superlative; this is a direct Russianism. Always use the `най-` prefix instead.
:::

Отже, тепер ви знаєте, як правильно порівнювати предмети, людей та явища українською мовою. Практикуйте ці форми щодня. Описуйте речі навколо вас. Який ресторан у вашому місті **найкращий** (the best)? Який будинок на вашій вулиці **найбільший** (the biggest)? Що більше ви тренуєтесь, то легше вам буде спілкуватися. Пам'ятайте, що помилятися — це нормально, але використання правильних українських форм робить вашу мову красивішою. Ваша мета — говорити краще сьогодні, **ніж** (than) учора.

<!-- INJECT_ACTIVITY: match-up-superlatives-match-adjective-to-its-superlative-form -->
<!-- INJECT_ACTIVITY: true-false-comparative-constructions-identify-correct-and-incorrect-comparative-constructions -->
<!-- INJECT_ACTIVITY: fill-in-comparative-form-the-comparative-from-the-base-adjective -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: comparison
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

**Level: A2 (Module 54/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

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
