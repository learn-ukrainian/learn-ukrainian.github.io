{"independent_effort": "medium", "independent_model": "gpt-6-astra", "independent_reviewer": "codex-tools", "self_reviewer": "agy-tools", "writer": {"effort": "high", "model": "gemini-3.8-flash-high", "writer": "agy-tools"}}
V7 UPGRADE review of lesson 2. Review the published lesson unit, not a fresh module build. No wiki packet or plan rewrite applies. Assess preservation, lesson_split, coherent progression, first-use cumulative vocabulary, final module closure (`Підсумок модуля — Module summary` on the last lesson, not Module completion), no named narrator, marked attributed quotations with Resources entries, no ```text learner examples, and side-by-side English support for added A1 Ukrainian passages of three or more sentences. SOURCES AUDIT: VESUM/`sources` is why the Ukrainian is trustworthy (gender, government, real examples — not Russian calques). This corpus trains a Ukrainian LLM and tests whether the sources tools actually get used. No tool calls = fail. Ungrounded morphology = fail. Judge the current dimension independently using exact quotes from these artifacts. Stress annotation follows review. Lesson map:
{"lessons": [{"n": 1, "title": "Мене звати...", "sections": ["Діалоги", "Мене звати..."], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}, {"n": 2, "title": "Я — студент", "sections": ["Це...", "Особові займeнники", "Я — студент"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}, {"n": 3, "title": "Слухай і записуй", "sections": ["Звідки?", "Слухай і записуй"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}, {"n": 4, "title": "Самоперевірка", "sections": ["Самоперевірка"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}], "closes_module": 4, "provenance": [{"placement": "inline", "index": 0, "new_id": "act-1", "lesson": 1}, {"placement": "inline", "index": 1, "new_id": "act-2", "lesson": 1}, {"placement": "inline", "index": 2, "new_id": "act-3", "lesson": 2}, {"placement": "inline", "index": 3, "new_id": "act-4", "lesson": 2}, {"placement": "workbook", "index": 0, "new_id": "act-w1", "lesson": 1}, {"placement": "workbook", "index": 1, "new_id": "act-w2", "lesson": 2}, {"placement": "workbook", "index": 2, "new_id": "act-w3", "lesson": 2}, {"placement": "workbook", "index": 3, "new_id": "act-w4", "lesson": 3}, {"placement": "workbook", "index": 4, "new_id": "act-w5", "lesson": 4}, {"placement": "workbook", "index": 5, "new_id": "act-w6", "lesson": 4}], "items_min_exempt": [{"id": "act-1", "reason": "4-item original activity preserved from baseline"}, {"id": "act-2", "reason": "5-item original activity preserved from baseline"}, {"id": "act-3", "reason": "5-item original activity preserved from baseline"}, {"id": "act-4", "reason": "4-item original activity preserved from baseline"}], "proper_names": []}
Independent Astra review after Gemini self-adjust. Fail ungrounded gender/government/examples. VESUM/`sources` is how the Ukrainian is better than a fluent guess; this corpus trains an LLM and tests the tools.

Score ALL five dimensions in ONE JSON object. The lesson artifacts appear ONCE below.
Do not restate them. Do not emit five essays. Do not emit a second JSON object.

Dimensions: pedagogical, naturalness, decolonization, engagement, tone.
Each value must be:
{"score": <0-10 number>, "verdict": "PASS"|"REVISE"|"REJECT", "evidence": "<one short sentence in your words>", "evidence_quotes": ["<8-20 consecutive words copied from the artifacts, single line, no extra spaces>"]}

Upgrade rules: A1 bilingual (UK then EN); no ```text learner examples; last lesson
closes with Підсумок модуля — Module summary; VESUM/sources for gender/government.

Return ONLY one JSON object, nothing before or after:
{"pedagogical": {...}, "naturalness": {...}, "decolonization": {...}, "engagement": {...}, "tone": {...}}

## module.md

## Це...

У пе́ршому уро́ці ви навчи́лися віта́тися та назива́ти своє́ ім'я́. In the first lesson, you learned how to greet people and say your name. Тепе́р ми вчимо́ся вка́зувати на ре́чі та люде́й навко́ло нас — now we learn how to point to objects and people around us in everyday life.

**Це** is the fast pointing word. It can introduce a thing, a city, or a
person:

| Украї́нська | English support |
| --- | --- |
| **Це ка́ва.** | This is coffee. |
| **Це Ки́їв.** | This is Kyiv. |
| **Це Андрі́й.** | This is Andrii. |
| **Це Окса́на.** | This is Oksana. |

Use **Що це?** for a thing: **Що це? Це ка́ва.** Use **Хто це?** for a
person: **Хто це? Це Окса́на.**

Keep the question word first. Ukrainian beginner questions are easier when the
question word opens the question: **Хто це?**, **Що це?**, **Зві́дки ти?**

Use **це** instead of an English-style "it" when you identify a person in a
photo, on the phone, or in a group:

| Украї́нська | English support |
| --- | --- |
| **Це мій та́то.** | This is my dad. |
| **Це моя́ ма́ма.** | This is my mom. |
| **Це моя́ по́друга.** | This is my female friend. |

For people, **він** and **вона́** are also possible after you know who the
person is: **Це Андрі́й. Він зі Льво́ва.** **Це Окса́на. Вона́ — лі́карка.**

<!-- INJECT_ACTIVITY: act-3 -->

Послу́хайте коро́тку розмо́ву в університе́ті — listen to a short conversation at the university:

> **Тара́с**: Приві́т! Що це? *(Hi! What is this?)*
> **Окса́на**: Приві́т! Це ка́ва. А хто це? *(Hi! This is coffee. And who is this?)*
> **Тара́с**: Це Андрі́й. Він — студе́нт. *(This is Andrii. He is a student.)*
> **Окса́на**: Ду́же приє́мно! А це хто? *(Nice to meet you! And who is this?)*
> **Тара́с**: Це Софі́я. Вона́ — студе́нтка. *(This is Sofiia. She is a student.)*
> **Окса́на**: Ду́же приє́мно! *(Nice to meet you!)*

English support after the Ukrainian dialogue:

| Украї́нська | English support |
| --- | --- |
| **Що це?** | What is this? |
| **Це ка́ва.** | This is coffee. |
| **А хто це?** | And who is this? |
| **Це Андрі́й.** | This is Andrii. |
| **Він — студе́нт.** | He is a male student. |
| **Це Софі́я.** | This is Sofiia. |
| **Вона́ — студе́нтка.** | She is a female student. |
| **Ду́же приє́мно!** | Pleased to meet you! |

Коли́ ви пока́зуєте на річ, запи́туйте **Що це?** — when you point to a thing, ask **Що це?**. Коли́ ви пока́зуєте на люди́ну, запи́туйте **Хто це?** — when you point to a person, ask **Хто це?**.

<!-- INJECT_ACTIVITY: act-201 -->

## Особо́ві займе́нники

Learn only the naming case now:

| Украї́нська | English support |
| --- | --- |
| **я** | I, the speaker |
| **ми** | we |
| **ти** | you, one familiar person |
| **ви** | you formal, or you plural |
| **він** | he |
| **вона́** | she |
| **вони́** | they |

The important beginner contrast is **ти / ви**. Use **ти** **для дру́зів,
діте́й** (for friends and children) and close classmates when the relationship
is informal. Use **ви** **для викладачі́в, ста́рших люде́й** (for teachers and
older people), one unknown adult, a host, or several people.

Mini-patterns:

| Неформа́льно | Форма́льно |
| --- | --- |
| **Як тебе́ зва́ти?** | **Як вас зва́ти?** |
| **А тебе́?** | **А вас?** |
| **Зві́дки ти?** | **Зві́дки ви?** |

When you write polite **Ви** to one person, Ukrainian often uses a capital
letter. In this course page, lower-case **ви** is enough for practice, but
recognize **Ви** when you see it.

<!-- INJECT_ACTIVITY: act-4 -->

Послу́хайте, як мо́вці обира́ють фо́рму зверта́ння — listen to how speakers choose the form of address:

> **Марко́**: До́брий день! Як вас зва́ти? *(Good afternoon! What is your name?)*
> **Петро́**: До́брий день! Мене́ зва́ти Петро́. А вас? *(Good afternoon! My name is Petro. And yours?)*
> **Марко́**: Мене́ зва́ти Марко́. Я — студе́нт. *(My name is Marko. I am a student.)*
> **Петро́**: Ду́же приє́мно! *(Pleased to meet you!)*

English support after the Ukrainian dialogue:

| Украї́нська | English support |
| --- | --- |
| **До́брий день!** | Good afternoon! / Hello! |
| **Як вас зва́ти?** | What is your name? formal |
| **А вас?** | And yours? formal |
| **Я — студе́нт.** | I am a male student. |
| **Ду́же приє́мно!** | Pleased to meet you! |

Зверні́ть ува́гу на різни́цю між займе́нниками — pay attention to the difference between pronouns:
- **я** — I (the speaker refers to oneself);
- **ти** — you (informal, one peer, child, or close friend);
- **він** — he (a male person);
- **вона́** — she (a female person);
- **ми** — we (a group that includes the speaker);
- **ви** — you (formal address to one adult, or plural address to several people);
- **вони́** — they (other people in the plural).

<!-- INJECT_ACTIVITY: act-202 -->

## Я — студе́нт

Ukrainian present-time identity lines do not need a word for English "am" or
"is":

| Украї́нська | English support |
| --- | --- |
| **Я — студе́нт.** | I am a male student. |
| **Я — студе́нтка.** | I am a female student. |
| **Він — лі́кар.** | He is a doctor. |
| **Вона́ — лі́карка.** | She is a doctor. |

The same identity pattern works for nationality:

| Чолові́ча фо́рма | Жіно́ча фо́рма |
| --- | --- |
| **Я — украї́нець.** | **Я — украї́нка.** |
| **Я — канаді́єць.** | **Я — кана́дка.** |
| **Я — америка́нець.** | **Я — америка́нка.** |

The dash is a reading helper. It marks the place where English expects "am" or
"is." In ordinary writing, you may see the same pattern without a dash:
**Я студе́нт.**

Use profession pairs as pairs:

| Чолові́ча фо́рма | Жіно́ча фо́рма |
| --- | --- |
| **студе́нт** | **студе́нтка** |
| **вчи́тель** | **вчи́телька** |
| **лі́кар** | **лі́карка** |
| **програмі́ст** | **програмі́стка** |
| **інжене́р** | **інжене́рка** |
| **украї́нець** | **украї́нка** |
| **канаді́єць** | **кана́дка** |
| **америка́нець** | **америка́нка** |

The feminine form is the primary form for a woman. **Окса́на — лі́карка.**
**Софі́я — студе́нтка.** **Ната́лка — інжене́рка.**

Послу́хайте коро́тку розмо́ву в день знайо́мства — listen to a short conversation on orientation day:

> **Андрі́й**: Приві́т! Мене́ зва́ти Андрі́й. Я — студе́нт. А тебе́? *(Hi! My name is Andrii. I am a student. And yours?)*
> **Оле́на**: Приві́т! Мене́ зва́ти Оле́на. Я теж студе́нтка. *(Hi! My name is Olena. I am also a student.)*
> **Андрі́й**: Ду́же приє́мно! *(Nice to meet you!)*
> **Оле́на**: Ду́же приє́мно! *(Nice to meet you!)*

English support after the Ukrainian dialogue:

| Украї́нська | English support |
| --- | --- |
| **Я — студе́нт.** | I am a male student. |
| **Я теж студе́нтка.** | I am also a female student. |
| **Ду́же приє́мно!** | Pleased to meet you! |

В украї́нській мо́ві вжива́йте приро́дні фемініти́ви для жіно́к — in Ukrainian, use natural feminine forms for women: **лі́карка**, **вчи́телька**, **програмі́стка**, **інжене́рка**, **студе́нтка**. Ця моде́ль є пито́мою та літерату́рною — this pattern is native and standard in Ukrainian.

<!-- INJECT_ACTIVITY: act-203 -->

У цьо́му уро́ці ви навчи́лися вка́зувати на ре́чі та люде́й — in this lesson you learned how to point to things and people (**Це ка́ва**, **Це мій та́то**), ста́вити запита́ння — ask questions (**Хто це?**, **Що це?**), розрізня́ти зверта́ння **ти** та **ви** — distinguish informal and formal address, будува́ти ре́чення іденти́чності — build identity lines (**Я — студе́нт**, **Вона́ — лі́карка**), та вжива́ти украї́нські фемініти́ви — and use standard Ukrainian feminine forms. Насту́пного уро́ку ми слу́хатимемо розмо́ви та відповіда́тимемо на запита́ння **Зві́дки ти?** — next lesson we will practice listening and answering where you are from.


## activities.yaml

inline:
- id: act-3
  type: match-up
  title: Це / хто / що
  instruction: З'єднай український рядок із його роботою.
  pairs:
  - left: Це Андрій.
    right: представити людину
  - left: Це Оксана.
    right: представити іншу людину
  - left: Хто це?
    right: запитати про людину
  - left: Що це?
    right: запитати про річ
  - left: Це кава.
    right: назвати річ
- id: act-201
  type: quiz
  title: Хто це чи що це?
  instruction: Обери правильне запитання для кожної ситуації.
  items:
  - prompt: 'Ти бачиш на столі чашку: Це кава.'
    options:
    - text: Що це?
      correct: true
    - text: Хто це?
      correct: false
    explanation: Для неживих предметів уживай Що це?.
  - prompt: 'Ти показуєш на фото друга: Це Андрій.'
    options:
    - text: Хто це?
      correct: true
    - text: Що це?
      correct: false
    explanation: Для людей уживай Хто це?.
  - prompt: 'Ти показуєш на нову однокурсницю: Це Оксана.'
    options:
    - text: Хто це?
      correct: true
    - text: Що це?
      correct: false
    explanation: Для людей запитуй Хто це?.
  - prompt: 'Ти бачиш фото міста: Це Київ.'
    options:
    - text: Що це?
      correct: true
    - text: Хто це?
      correct: false
    explanation: Для міст і речей запитуй Що це?.
  - prompt: 'Ти показуєш на свого батька: Це мій тато.'
    options:
    - text: Хто це?
      correct: true
    - text: Що це?
      correct: false
    explanation: Тато — людина, тому запитуємо Хто це?.
  - prompt: 'Ти показуєш на свою подругу: Це моя подруга.'
    options:
    - text: Хто це?
      correct: true
    - text: Що це?
      correct: false
    explanation: Подруга — людина, тому запитуємо Хто це?.
- id: act-4
  type: quiz
  title: Обери займенник
  instruction: Обери займенник для української ситуації.
  items:
  - prompt: Мовець говорить про себе.
    options:
    - text: я
      correct: true
    - text: ти
      correct: false
    - text: вони
      correct: false
    explanation: Я — це мовець.
  - prompt: Один друг або близький однокурсник.
    options:
    - text: ти
      correct: true
    - text: ви
      correct: false
    - text: він
      correct: false
    explanation: Ти — один неформальний співрозмовник.
  - prompt: Один незнайомий дорослий або формальна ситуація.
    options:
    - text: ви
      correct: true
    - text: ти
      correct: false
    - text: вона
      correct: false
    explanation: Ви — формально до однієї людини, а також множина.
  - prompt: Жінка або дівчина вже відома в розмові.
    options:
    - text: вона
      correct: true
    - text: він
      correct: false
    - text: я
      correct: false
    explanation: Вона вказує на жінку або дівчину.
- id: act-202
  type: match-up
  title: Особові займенники
  instruction: З'єднай займенник із його значенням у розмові.
  pairs:
  - left: я
    right: мовець про себе
  - left: ти
    right: один близький друг
  - left: він
    right: знайомий чоловік
  - left: вона
    right: знайома жінка
  - left: ми
    right: група разом із мовцем
  - left: ви
    right: викладач або незнайомий дорослий
  - left: вони
    right: інші люди у множині
- id: act-203
  type: fill-in
  title: 'Він чи вона: професії'
  instruction: Обери правильну чоловічу або жіночу форму професії.
  items:
  - sentence: Оксана працює в лікарні. Вона — ___.
    answer: лікарка
    options:
    - лікарка
    - лікар
    explanation: 'Для жінки вживай стандартну жіночу форму: лікарка.'
  - sentence: Тарас навчається в університеті. Він — ___.
    answer: студент
    options:
    - студент
    - студентка
    explanation: 'Для чоловіка вживай чоловічу форму: студент.'
  - sentence: Марія викладає в школі. Вона — ___.
    answer: вчителька
    options:
    - вчителька
    - вчитель
    explanation: 'Для жінки вживай жіночу форму: вчителька.'
  - sentence: Марко створює комп'ютерні програми. Він — ___.
    answer: програміст
    options:
    - програміст
    - програмістка
    explanation: 'Для чоловіка вживай чоловічу форму: програміст.'
  - sentence: Софія проєктує мости. Вона — ___.
    answer: інженерка
    options:
    - інженерка
    - інженер
    explanation: 'Для жінки вживай стандартну жіночу форму: інженерка.'
  - sentence: Андрій народився в Україні. Він — ___.
    answer: українець
    options:
    - українець
    - українка
    explanation: 'Для чоловіка вживай форму: українець.'
workbook:
- id: act-w2
  type: match-up
  title: Пари професій
  instruction: З'єднай чоловічу і жіночу форму професії.
  pairs:
  - left: студент
    right: студентка
  - left: вчитель
    right: вчителька
  - left: лікар
    right: лікарка
  - left: програміст
    right: програмістка
  - left: інженер
    right: інженерка
  - left: українець
    right: українка
  - left: канадієць
    right: канадка
  - left: американець
    right: американка
- id: act-w3
  type: group-sort
  title: Неформально чи формально
  instruction: Розклади фрази за ситуацією.
  groups:
  - label: Неформально
    items:
    - Як тебе звати?
    - А тебе?
    - Звідки ти?
  - label: Формально
    items:
    - Як вас звати?
    - А вас?
    - Звідки ви?
- id: act-w201
  type: group-sort
  title: 'Чоловічий та жіночий рід: люди'
  instruction: Розподіли слова на чоловічі та жіночі форми.
  groups:
  - label: Чоловіча форма
    items:
    - студент
    - вчитель
    - лікар
    - програміст
  - label: Жіноча форма
    items:
    - студентка
    - вчителька
    - лікарка
    - програмістка
- id: act-w202
  type: fill-in
  title: Речення про себе та інших
  instruction: Встав правильне слово в речення.
  items:
  - sentence: Це Андрій. ___ зі Львова.
    answer: Він
    options:
    - Він
    - Вона
    - Воно
    explanation: Андрій — чоловік, тому вживаємо Він.
  - sentence: Це Оксана. ___ — лікарка.
    answer: Вона
    options:
    - Вона
    - Він
    - Вони
    explanation: Оксана — жінка, тому вживаємо Вона.
  - sentence: Я навчаюся в університеті. Я — ___.
    answer: студент
    options:
    - студент
    - кава
    - Київ
    explanation: Студент — назва ролі людини.
  - sentence: Це моя мама. Вона — ___.
    answer: вчителька
    options:
    - вчителька
    - вчитель
    - тато
    explanation: Мама — жінка, тому вживаємо форму вчителька.
  - sentence: Це Андрій і Тарас. ___ — студенти.
    answer: Вони
    options:
    - Вони
    - Він
    - Вона
    explanation: Про кількох людей говоримо Вони.
  - sentence: ___ це? Це кава.
    answer: Що
    options:
    - Що
    - Хто
    - Як
    explanation: Кава — це річ, тому запитуємо Що це?.
- id: act-w203
  type: translate
  title: Значення речень ідентичності
  instruction: Обери правильний англійський переклад.
  items:
  - source: Це кава.
    options:
    - text: This is coffee.
      correct: true
    - text: Who is this?
      correct: false
    - text: What is this?
      correct: false
    explanation: Це кава означає This is coffee.
  - source: Хто це?
    options:
    - text: Who is this?
      correct: true
    - text: What is this?
      correct: false
    - text: This is Andrii.
      correct: false
    explanation: Хто це? запитує про людину.
  - source: Що це?
    options:
    - text: What is this?
      correct: true
    - text: Who is this?
      correct: false
    - text: This is coffee.
      correct: false
    explanation: Що це? запитує про річ.
  - source: Я — студент.
    options:
    - text: I am a male student.
      correct: true
    - text: She is a doctor.
      correct: false
    - text: He is a teacher.
      correct: false
    explanation: Я — студент говорить хлопець або чоловік про себе.
  - source: Вона — лікарка.
    options:
    - text: She is a doctor.
      correct: true
    - text: He is a doctor.
      correct: false
    - text: I am a student.
      correct: false
    explanation: Вона — лікарка називає професію жінки.
  - source: Це мій тато.
    options:
    - text: This is my dad.
      correct: true
    - text: This is my mom.
      correct: false
    - text: This is my friend.
      correct: false
    explanation: Це мій тато представляє батька.
- id: act-w204
  type: error-correction
  title: Виправ помилки в ідентичності
  instruction: Обери правильне українське речення замість помилкового.
  items:
  - sentence: Я є студентка.
    error: Я є студентка.
    correction: Я — студентка.
    options:
    - Я — студентка.
    - Я є студентка.
    explanation: 'У теперішньому часі дієслово «є» пропускається: Я — студентка.'
  - sentence: Оксана — лікар.
    error: Оксана — лікар.
    correction: Оксана — лікарка.
    options:
    - Оксана — лікарка.
    - Оксана — лікар.
    explanation: 'Для жінки вживай стандартний фемінітив: лікарка.'
  - sentence: Воно мій тато.
    error: Воно мій тато.
    correction: Це мій тато.
    options:
    - Це мій тато.
    - Воно мій тато.
    explanation: Для вказівки на людину вживай вказівне слово «це».
  - sentence: Це хто?
    error: Це хто?
    correction: Хто це?
    options:
    - Хто це?
    - Це хто?
    explanation: 'Питальне слово в українській мові ставиться на початку: Хто це?.'
  - sentence: Це що?
    error: Це що?
    correction: Що це?
    options:
    - Що це?
    - Це що?
    explanation: 'Питальне слово ставиться на початку речення: Що це?.'
  - sentence: Софія — інженер.
    error: Софія — інженер.
    correction: Софія — інженерка.
    options:
    - Софія — інженерка.
    - Софія — інженер.
    explanation: 'Для жінки вживай форму жіночого роду: інженерка.'
- id: act-w205
  type: match-up
  title: Речення ідентичності
  instruction: З'єднай речення з особою, яка про себе говорить або про яку говорять.
  pairs:
  - left: Я — студентка.
    right: дівчина про своє навчання
  - left: Він — лікар.
    right: про знайомого лікаря-чоловіка
  - left: Вона — лікарка.
    right: про знайому лікарку-жінку
  - left: Ми — студенти.
    right: група молоді про себе
  - left: Він — інженер.
    right: про знайомого інженера-чоловіка
  - left: Вона — інженерка.
    right: про знайому інженерку-жінку


## vocabulary.yaml

- lemma: я
  translation: I
  pos: pronoun
  usage: Я з України.
- lemma: ти
  translation: you, informal singular
  pos: pronoun
  usage: Звідки ти?
- lemma: він
  translation: he
  pos: pronoun
  usage: Він зі Львова.
- lemma: вона
  translation: she
  pos: pronoun
  usage: Вона — лікарка.
- lemma: ми
  translation: we
  pos: pronoun
  usage: Ми студенти.
- lemma: ви
  translation: you, formal or plural
  pos: pronoun
  usage: Як вас звати?
- lemma: вони
  translation: they
  pos: pronoun
  usage: Вони з України.
- lemma: це
  translation: this is / this
  pos: pronoun
  usage: Це Оксана.
- lemma: хто
  translation: who
  pos: pronoun
  usage: Хто це?
- lemma: що
  translation: what
  pos: pronoun
  usage: Що це?
- lemma: тато
  translation: dad
  pos: noun
  usage: Це мій тато.
- lemma: мама
  translation: mom
  pos: noun
  usage: Це моя мама.
- lemma: подруга
  translation: female friend
  pos: noun
  usage: Це моя подруга.
- lemma: студент
  translation: male student
  pos: noun
  usage: Я — студент.
- lemma: студентка
  translation: female student
  pos: noun
  usage: Я — студентка.
- lemma: вчитель
  translation: male teacher
  pos: noun
  usage: Він — вчитель.
- lemma: вчителька
  translation: female teacher
  pos: noun
  usage: Вона — вчителька.
- lemma: лікар
  translation: male doctor
  pos: noun
  usage: Він — лікар.
- lemma: лікарка
  translation: female doctor
  pos: noun
  usage: Вона — лікарка.
- lemma: програміст
  translation: male programmer
  pos: noun
  usage: Марко — програміст.
- lemma: програмістка
  translation: female programmer
  pos: noun
  usage: Олена — програмістка.
- lemma: інженер
  translation: male engineer
  pos: noun
  usage: Андрій — інженер.
- lemma: інженерка
  translation: female engineer
  pos: noun
  usage: Оксана — інженерка.
- lemma: українець
  translation: Ukrainian man
  pos: noun
  usage: Андрій — українець.
- lemma: українка
  translation: Ukrainian woman
  pos: noun
  usage: Олена — українка.
- lemma: канадієць
  translation: Canadian man
  pos: noun
  usage: Марко — канадієць.
- lemma: канадка
  translation: Canadian woman
  pos: noun
  usage: Олена — канадка.
- lemma: американець
  translation: American man
  pos: noun
  usage: Андрій — американець.
- lemma: американка
  translation: American woman
  pos: noun
  usage: Софія — американка.


## resources.yaml

- title: ULP Season 1, Episode 8 — Jobs and Professions
  role: podcast
  source: Ukrainian Lessons Podcast
  url: https://www.ukrainianlessons.com/episode8/
  notes: 'Plan reference: profession vocabulary with masculine and feminine forms.'
- title: ULP Season 1, Episode 3 — How to Introduce Yourself
  role: podcast
  source: Ukrainian Lessons Podcast
  url: https://www.ukrainianlessons.com/episode3/
  notes: 'Plan reference: Мене звати, nationalities, and Дуже приємно.'
