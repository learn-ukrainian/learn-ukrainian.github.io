{"independent_effort": "medium", "independent_model": "gpt-6-astra", "independent_reviewer": "codex-tools", "self_reviewer": "agy-tools", "writer": {"effort": "high", "model": "gemini-3.8-flash-high", "writer": "agy-tools"}}
V7 UPGRADE review of lesson 2. Review the published lesson unit, not a fresh module build. No wiki packet or plan rewrite applies. Assess preservation, lesson_split, coherent progression, first-use cumulative vocabulary, final module closure (`Підсумок модуля — Module summary` on the last lesson, not Module completion), no named narrator, marked attributed quotations with Resources entries, no ```text learner examples, and side-by-side English support for added A1 Ukrainian passages of three or more sentences. SOURCES AUDIT: VESUM/`sources` is why the Ukrainian is trustworthy (gender, government, real examples — not Russian calques). This corpus trains a Ukrainian LLM and tests whether the sources tools actually get used. No tool calls = fail. Ungrounded morphology = fail. Judge the current dimension independently using exact quotes from these artifacts. Stress annotation follows review. Lesson map:
{"lessons": [{"n": 1, "title": "Сім'я", "sections": ["Діалоги", "Сім'я"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}, {"n": 2, "title": "Мій / моя", "sections": ["У мене є", "Мій / моя"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}, {"n": 3, "title": "Слухай, фото, зошит", "sections": ["Слухай, фото, зошит"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}, {"n": 4, "title": "Самоперевірка", "sections": ["Самоперевірка"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}], "closes_module": 4, "provenance": [{"placement": "inline", "index": 0, "new_id": "act-1", "lesson": 1}, {"placement": "inline", "index": 1, "new_id": "act-2", "lesson": 1}, {"placement": "inline", "index": 2, "new_id": "act-3", "lesson": 2}, {"placement": "inline", "index": 3, "new_id": "act-4", "lesson": 2}, {"placement": "workbook", "index": 0, "new_id": "act-w1", "lesson": 1}, {"placement": "workbook", "index": 1, "new_id": "act-w2", "lesson": 2}, {"placement": "workbook", "index": 2, "new_id": "act-w3", "lesson": 2}, {"placement": "workbook", "index": 3, "new_id": "act-w4", "lesson": 3}, {"placement": "workbook", "index": 4, "new_id": "act-w5", "lesson": 4}, {"placement": "workbook", "index": 5, "new_id": "act-w6", "lesson": 4}], "items_min_exempt": [{"id": "act-w4", "reason": "4-item original activity preserved from baseline"}, {"id": "act-w5", "reason": "5-item original activity preserved from baseline"}, {"id": "act-w6", "reason": "5-item original activity preserved from baseline"}], "proper_names": []}
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

# Мій / моя

У пе́ршому уро́ці ви познайо́милися з назва́ми чле́нів сім'ї́: **ма́ма**, **та́то**, **брат**, **сестра́**, **бабу́ся**, **діду́сь** та **батьки́**. In the first lesson, you learned to identify family members and name the people closest to you.

Тепе́р час навчи́тися говори́ти про володі́ння та пока́зувати ро́дичів на фотогра́фіях — now it is time to express possession and identify relatives in family photos:
- **У ме́не є...** — express "I have" naturally without translating word-for-word from English;
- **У те́бе є...?** — ask friendly, informal questions about brothers, sisters, or family;
- **Оди́н, одна́, два, дві** — match small numbers with masculine and feminine family words;
- **Мій, моя́, моє́, мої́** — choose the correct possessive form by the person shown, not by the speaker.

### Розминка — Warm-up and retrieval

Before moving to sentences with possession, recall the key family words from Lesson 1. In Ukrainian, every noun has grammatical gender, which determines how other words connect with it:

| Слово — Word | Рід — Gender | Нагадування — Reminder |
| --- | --- | --- |
| **брат** | чоловічий (he / masculine) | brother |
| **сестра** | жіночий (she / feminine) | sister |
| **тато / батько** | чоловічий (he / masculine) | dad / father |
| **мама / мати** | жіночий (she / feminine) | mom / mother |
| **син** | чоловічий (he / masculine) | son |
| **дочка / донька** | жіночий (she / feminine) | daughter |
| **бабуся** | жіночий (she / feminine) | grandmother |
| **дідусь** | чоловічий (he / masculine) | grandfather |
| **батьки** | множина (they / plural) | parents |

## У ме́не є

English says "I have a brother." Ukrainian normally uses a different shape:
**У ме́не є брат.** Learn it as one piece.

| Ukrainian phrase | English use |
| --- | --- |
| **У мене є брат.** | I have a brother. |
| **У мене є сестра.** | I have a sister. |
| **У тебе є брат?** | Do you have a brother? informal |
| **У тебе є сестра?** | Do you have a sister? informal |
| **У вас є діти?** | Do you have children? formal or plural |
| **Так, у мене є брат.** | Yes, I have a brother. |
| **Ні.** | No. |
| **Ні, у мене тільки один брат.** | No, I only have one brother. |

Do not build the English sentence word by word with a verb for "have." Your
safe phrase is **У мене є...**. The other forms, such as "he has" and
"she has," need more grammar, so they stay as recognition only inside
dialogues.

Use the easy number agreement phrases:

| Masculine | Feminine |
| --- | --- |
| **один брат** | **одна сестра** |
| **два брати** | **дві сестри** |
| **один син** | **одна дочка** |

For a negative answer, keep it simple: **Ні.** or **Ні, у мене тільки один
брат.** The full "I do not have..." pattern waits until later because it
requires more case grammar.

<!-- INJECT_ACTIVITY: act-3 -->

Listen to how two friends talk about their families while looking at photos on a phone:

> Олена: Привіт, Тарасе! У тебе є брат чи сестра?
> Тарас: Привіт, Олено! Так, у мене є один брат і одна сестра. А в тебе?
> Олена: У мене тільки один брат. Його звати Богдан.
> Тарас: Класно! А дідусь і бабуся у вас є?
> Олена: Так, у нас є бабуся і дідусь. Вони живуть у селі.

English breakdown after the dialogue:

| Українська фраза | English breakdown |
| --- | --- |
| **У тебе є брат чи сестра?** | Do you have a brother or a sister? |
| **Так, у мене є один брат і одна сестра.** | Yes, I have one brother and one sister. |
| **А в тебе?** | And what about you? (informal) |
| **У мене тільки один брат.** | I only have one brother. |
| **А дідусь і бабуся у вас є?** | And do you have a grandfather and a grandmother? |
| **Так, у нас є бабуся і дідусь.** | Yes, we have a grandmother and a grandfather. |

Notice the melody of questions with **У тебе є...?**: the pitch rises on the key word at the end of the question. When answering affirmatively, say **Так, у мене є...**. For a simple negative reply at A1, say **Ні.** or state what you do have: **Ні, у мене тільки один брат.** Never say *«У мене немає брат»* with the nominative case — the full negative pattern requires the genitive case, which is taught in later modules.

Ukrainian numbers for "one" and "two" also change to match the gender of the noun that follows:

| Числівник — Number | Чоловічий рід — Masculine | Жіночий рід — Feminine |
| --- | --- | --- |
| **1** | **один брат**, **один син**, **один дідусь** | **одна сестра**, **одна дочка**, **одна бабуся** |
| **2** | **два брати**, **два сини** | **дві сестри**, **дві дочки** |

Notice that masculine nouns take **один** and **два**, whereas feminine nouns take **одна** and **дві**: **один брат** (one brother), but **одна сестра** (one sister); **два брати** (two brothers), but **дві сестри** (two sisters).

<!-- INJECT_ACTIVITY: act-201 -->

## Мій / моя́

The Ukrainian possessive pronoun for "my" changes to match the person or thing
you own. It does not match the gender of the owner.

| Owned word | My | Your, informal |
| --- | --- | --- |
| **брат** | **мій брат** | **твій брат** |
| **мама** | **моя мама** | **твоя мама** |
| **місто** | **моє місто** | **твоє місто** |
| **батьки** | **мої батьки** | **твої батьки** |

The key contrast is **Це мій брат** but **Це моя сестра**. The owner can be a
man or a woman; the form still follows **брат** or **сестра**.

:::tip
When you hesitate, point to the owned word. **Брат** asks for **мій**.
**Мама** asks for **моя**. The speaker's gender does not decide the form.
:::

**Його** and **її** are easier. They do not change here:

| Ukrainian | English |
| --- | --- |
| **Це мій брат. Його звати Коля.** | This is my brother. His name is Kolia. |
| **Це моя сестра. Її звати Катя.** | This is my sister. Her name is Katia. |
| **Це її мама.** | This is her mom. |
| **Це його тато.** | This is his dad. |

You may also hear the older classroom-style verb form **Це мій брат. Його
звуть...**. Treat **Його звуть...** and **Його звати...** as recognition
patterns for "his name is..." while you keep your own production simple.

Leave the other possessive forms for later. This module's photo tool is the
small set you can already use: **мій**, **моя**, **моє**, **мої**, **твій**,
**твоя**, **твоє**, **твої**.

Use **чи** for a choice or a yes/no photo question:

| Українська | English support |
| --- | --- |
| **У тебе є брати чи сестри?** | Do you have brothers or sisters? |
| **Чи це твоя бабуся?** | Is this your grandmother? |

<!-- INJECT_ACTIVITY: act-4 -->

Look at how friends share family photos in a natural conversation:

> Юля: Максиме, подивись, це мої сімейні фотографії!
> Максим: О, як гарно! Хто це на фото?
> Юля: Це мій тато Євген і моя мама Марина.
> Максим: А це твій молодший брат?
> Юля: Так, це мій брат Денис. А це моє рідне місто Львів.
> Максим: Дуже приємно познайомитися!

English breakdown after the dialogue:

| Українська фраза | English breakdown |
| --- | --- |
| **Подивись, це мої сімейні фотографії!** | Look, these are my family photos! |
| **Хто це на фото?** | Who is this in the photo? |
| **Це мій тато Євген і моя мама Марина.** | This is my dad Yevhen and my mom Maryna. |
| **А це твій молодший брат?** | And is this your younger brother? |
| **Це моє рідне місто Львів.** | This is my hometown Lviv. |
| **Дуже приємно познайомитися!** | Very nice to meet you! |

In Ukrainian grammar, possessive pronouns indicate belonging and must agree with the noun in gender and number: «Присвійні займенники вказують на приналежність предмета певній особі й узгоджуються з іменником у роді, числі та відмінку» (quoted from: Літвінова, Українська мова 6 клас, p. 260).

Always look at the ending of the noun to choose the correct possessive form:
- **Чоловічий рід (Masculine — він):** **мій брат**, **мій тато**, **мій син**, **мій дідусь**, **твій брат**, **твій друг**. Even though **тато** and **дідусь** end in vowels, they refer to male family members, so they take masculine agreement: **мій тато**, **мій дідусь**.
- **Жіночий рід (Feminine — вона):** **моя мама**, **моя сестра**, **моя дочка**, **моя бабуся**, **твоя мама**, **твоя сестра**.
- **Середній рід (Neuter — воно):** **моє місто**, **моє село**, **моє прізвище**, **твоє місто**.
- **Множина (Plural — вони):** **мої батьки**, **мої родичі**, **мої брати**, **мої сестри**, **твої батьки**, **твої друзі**.

<!-- INJECT_ACTIVITY: act-202 -->

<!-- INJECT_ACTIVITY: act-203 -->

### Підсумок уроку — Lesson recap

У цьо́му уро́ці ви навчи́лися говори́ти про володі́ння та назива́ти чле́нів роди́ни за допомо́гою присві́йних займе́нників — in this lesson you have mastered key communicative tools for talking about your family:
- **У ме́не є...** — express what family members you have safely and accurately;
- **У те́бе є...?** — ask peers friendly questions about their family members;
- **Оди́н, одна́, два, дві** — match counting numbers with masculine and feminine nouns;
- **Мій, моя́, моє́, мої́** — select the correct possessive form based on the gender and number of the person or thing you describe.

### Наступний крок — Next step

In Lesson 3 (**Слухай, фото, зошит**), you will practice listening to natural spoken dialogues from the Ukrainian Lessons Podcast, reading handwritten family labels in a notebook, and connecting spoken sounds to written Ukrainian forms.


## activities.yaml

inline:
- id: act-3
  type: fill-in
  title: Склади У мене є
  instruction: Обери слово або фразу для родинного речення.
  items:
  - sentence: ___ мене є брат.
    answer: У
    options:
    - У
    - Це
    - Хто
    explanation: У мене є... — цілий блок, щоб сказати, що хтось або щось є в мене.
  - sentence: У ___ є сестра.
    answer: мене
    options:
    - мене
    - мій
    - це
    explanation: У мене є... відповідає за себе.
  - sentence: У ___ є брат?
    answer: тебе
    options:
    - тебе
    - мене
    - він
    explanation: У тебе є...? питає одну знайому людину.
  - sentence: У ___ є діти?
    answer: вас
    options:
    - вас
    - твій
    - вона
    explanation: У вас є...? — формально або множина.
  - sentence: У мене є ___ брат.
    answer: один
    options:
    - один
    - одна
    - дві
    explanation: Брат — чоловічого роду, тому один.
  - sentence: У мене є ___ сестра.
    answer: одна
    options:
    - одна
    - один
    - два
    explanation: Сестра — жіночого роду, тому одна.
  - sentence: У мене є ___ брати.
    answer: два
    options:
    - два
    - дві
    - одна
    explanation: Брати вживаємо з два.
  - sentence: У мене є ___ сестри.
    answer: дві
    options:
    - дві
    - два
    - один
    explanation: Зі словом сестри тут уживаємо дві.
- id: act-201
  type: match-up
  title: Скільки у тебе родичів?
  instruction: З'єднай числівник із відповідним родинним словом.
  pairs:
  - left: один
    right: брат
  - left: одна
    right: сестра
  - left: два
    right: брати
  - left: дві
    right: сестри
  - left: один
    right: син
  - left: одна
    right: дочка
- id: act-4
  type: fill-in
  title: Мій чи моя?
  instruction: Обери присвійний займенник до родинного слова.
  items:
  - sentence: Це ___ брат.
    answer: мій
    options:
    - мій
    - моя
    - моє
    - мої
    explanation: Брат — чоловічого роду.
  - sentence: Це ___ мама.
    answer: моя
    options:
    - моя
    - мій
    - моє
    - мої
    explanation: Мама — жіночого роду.
  - sentence: Це ___ місто.
    answer: моє
    options:
    - моє
    - мій
    - моя
    - мої
    explanation: Місто — середнього роду.
  - sentence: Це ___ батьки.
    answer: мої
    options:
    - мої
    - мій
    - моя
    - моє
    explanation: Батьки — множина.
  - sentence: Це ___ тато?
    answer: твій
    options:
    - твій
    - твоя
    - твоє
    - твої
    explanation: Тато — чоловічого роду, хоча слово закінчується на -о.
  - sentence: Це ___ сестра?
    answer: твоя
    options:
    - твоя
    - твій
    - твоє
    - твої
    explanation: Сестра — жіночого роду.
  - sentence: Це ___ прізвище?
    answer: твоє
    options:
    - твоє
    - твій
    - твоя
    - твої
    explanation: Прізвище — середнього роду.
  - sentence: Це ___ родичі?
    answer: твої
    options:
    - твої
    - твій
    - твоя
    - твоє
    explanation: Родичі — множина.
- id: act-202
  type: quiz
  title: Чия це річ або людина?
  instruction: Обери правильний займенник для кожного випадку.
  items:
  - prompt: Брат — це він (чоловічий рід). Як сказати «my brother»?
    options:
    - text: мій брат
      correct: true
    - text: моя брат
      correct: false
    - text: моє брат
      correct: false
    explanation: Брат — чоловічого роду, тому вживаємо мій.
  - prompt: Сестра — це вона (жіночий рід). Як сказати «my sister»?
    options:
    - text: моя сестра
      correct: true
    - text: мій сестра
      correct: false
    - text: мої сестра
      correct: false
    explanation: Сестра — жіночого роду, тому вживаємо моя.
  - prompt: Місто — це воно (середній рід). Як сказати «my city»?
    options:
    - text: моє місто
      correct: true
    - text: мій місто
      correct: false
    - text: моя місто
      correct: false
    explanation: Місто — середнього роду (закінчення -о), тому вживаємо моє.
  - prompt: Батьки — це вони (множина). Як сказати «my parents»?
    options:
    - text: мої батьки
      correct: true
    - text: мій батьки
      correct: false
    - text: моя батьки
      correct: false
    explanation: Батьки — множина, тому вживаємо мої.
  - prompt: Тато — чоловічий рід. Як спитати друга «your dad»?
    options:
    - text: твій тато
      correct: true
    - text: твоя тато
      correct: false
    - text: твоє тато
      correct: false
    explanation: Тато — чоловічого роду, тому твій.
  - prompt: Мама — жіночий рід. Як спитати друга «your mom»?
    options:
    - text: твоя мама
      correct: true
    - text: твій мама
      correct: false
    - text: твої мама
      correct: false
    explanation: Мама — жіночого роду, тому твоя.
- id: act-203
  type: true-false
  title: Перевір узгодження слів
  instruction: Визнач, чи граматично правильно побудовано фразу.
  items:
  - statement: Фраза «мій брат» є правильною.
    correct: true
    explanation: Брат — чоловічого роду, тому займенник мій правильний.
  - statement: Фраза «мій мама» є правильною.
    correct: false
    explanation: Мама — жіночого роду, тому треба сказати «моя мама».
  - statement: Фраза «моє місто» є правильною.
    correct: true
    explanation: Місто — середнього роду, тому моє правильне.
  - statement: Фраза «два сестри» є правильною.
    correct: false
    explanation: З іменниками жіночого роду вживаємо дві — «дві сестри».
  - statement: Фраза «одна дочка» є правильною.
    correct: true
    explanation: Дочка — жіночого роду, тому одна дочка.
  - statement: Фраза «мої батьки» є правильною.
    correct: true
    explanation: Батьки — множина, тому мої батьки.
workbook:
- id: act-w2
  type: fill-in
  title: Обери українську родинну норму
  instruction: Обери українське слово для звичайної родинної розмови.
  items:
  - sentence: Моя ___ — вчителька.
    answer: дружина
    options:
    - дружина
    - жена
    explanation: Для wife вживай дружина; жена — російська форма.
  - sentence: Мій ___ працює в лікарні.
    answer: чоловік
    options:
    - чоловік
    - муж
    explanation: У звичайній родинній розмові вживай чоловік; муж — старше або піднесене
      слово.
  - sentence: Це моя ___ Тетяна.
    answer: бабуся
    options:
    - бабуся
    - бабушка
    explanation: Бабуся — українське слово для grandmother.
  - sentence: У нас велика родина — близько десяти ___.
    answer: родичів
    options:
    - родичів
    - родственників
    explanation: Родичі — українське слово для relatives; у цьому реченні форма родичів
      уже дана як готовий блок.
  - sentence: Це ще маленька ___.
    answer: дитина
    options:
    - дитина
    - ребьонок
    explanation: Дитина — українське слово для child.
  - sentence: Це мій ___ брат.
    answer: молодший
    options:
    - молодший
    - младший
    explanation: Молодший означає менший за віком.
  - sentence: Мій старший брат уже ___.
    answer: одружений
    options:
    - одружений
    - женатий
    explanation: Для married у цьому родинному реченні вживай одружений.
- id: act-w3
  type: group-sort
  title: Один / одна / два / дві
  instruction: Розподіли родинні фрази за числівником.
  groups:
  - label: один
    items:
    - один брат
    - один син
    - один дідусь
  - label: одна
    items:
    - одна сестра
    - одна дочка
    - одна бабуся
  - label: два
    items:
    - два брати
    - два сини
  - label: дві
    items:
    - дві сестри
    - дві дочки
- id: act-w201
  type: fill-in
  title: У мене є чи у тебе є?
  instruction: Доповни речення правильною формою виразу володіння.
  items:
  - sentence: — Чи ___ тебе є брат? — Так, є.
    answer: у
    options:
    - у
    - це
    - на
    explanation: Запитання починається з прийменника у.
  - sentence: 'У ___ є дві сестри: Оля і Катя.'
    answer: мене
    options:
    - мене
    - мій
    - я
    explanation: Відповідаючи про себе, кажемо «У мене є».
  - sentence: У тебе є ___ брат?
    answer: один
    options:
    - один
    - одна
    - одне
    explanation: Брат — чоловічого роду, тому один.
  - sentence: Так, у мене є тільки ___ сестра.
    answer: одна
    options:
    - одна
    - один
    - двоє
    explanation: Сестра — жіночого роду, тому одна.
  - sentence: Чи у вас ___ діти?
    answer: є
    options:
    - є
    - має
    - був
    explanation: У сталій формі теперішнього часу вживаємо є.
  - sentence: 'У мене є ___ брати: Іван і Денис.'
    answer: два
    options:
    - два
    - дві
    - один
    explanation: Зі словом брати вживаємо числівник два.
- id: act-w202
  type: match-up
  title: Присвійні займенники та іменники
  instruction: З'єднай займенник із відповідним іменником.
  pairs:
  - left: мій
    right: дідусь
  - left: моя
    right: бабуся
  - left: моє
    right: прізвище
  - left: мої
    right: брати
  - left: твій
    right: син
  - left: твоя
    right: донька
- id: act-w203
  type: group-sort
  title: 'Розподіли за родом: мій, моя, моє чи мої?'
  instruction: Розподіли слова за займенником, з яким вони вживаються.
  groups:
  - label: мій (він)
    items:
    - тато
    - брат
    - син
    - дідусь
  - label: моя (вона)
    items:
    - мама
    - сестра
    - дочка
    - бабуся
  - label: моє (воно)
    items:
    - місто
    - село
    - прізвище
  - label: мої (вони)
    items:
    - батьки
    - родичі
    - брати
    - сестри
- id: act-w204
  type: error-correction
  title: Виправ граматичні помилки в роді
  instruction: Знайди помилку в узгодженні та обери правильний варіант.
  items:
  - sentence: Це мій мама.
    error: мій
    correction: моя
    options:
    - моя
    - мій
    explanation: Мама — жіночого роду, тому моя мама.
  - sentence: Це твоя тато.
    error: твоя
    correction: твій
    options:
    - твій
    - твоя
    explanation: Тато — чоловічого роду, тому твій тато.
  - sentence: У мене є дві брати.
    error: дві
    correction: два
    options:
    - два
    - дві
    explanation: Брат — чоловічого роду, у множині два брати.
  - sentence: У мене є один сестра.
    error: один
    correction: одна
    options:
    - одна
    - один
    explanation: Сестра — жіночого роду, тому одна сестра.
  - sentence: Це моє батьки.
    error: моє
    correction: мої
    options:
    - мої
    - моє
    explanation: Батьки — множина, тому мої батьки.
  - sentence: Це мій місто.
    error: мій
    correction: моє
    options:
    - моє
    - мій
    explanation: Місто — середнього роду, тому моє місто.
- id: act-w205
  type: translate
  title: Переклад базових родинних фраз
  instruction: Обери точний англійський переклад українського виразу.
  items:
  - source: У мене є брат.
    options:
    - text: I have a brother.
      correct: true
    - text: You have a brother.
      correct: false
    - text: This is my brother.
      correct: false
    explanation: У мене є... означає «I have...».
  - source: У тебе є сестра?
    options:
    - text: Do you have a sister?
      correct: true
    - text: Is this your sister?
      correct: false
    - text: I have a sister.
      correct: false
    explanation: У тебе є...? означає «Do you have...?» (informal).
  - source: Це мій тато.
    options:
    - text: This is my dad.
      correct: true
    - text: This is your dad.
      correct: false
    - text: He has a dad.
      correct: false
    explanation: Мій тато означає «my dad».
  - source: Це моя мама.
    options:
    - text: This is my mom.
      correct: true
    - text: This is my sister.
      correct: false
    - text: She is my mom.
      correct: false
    explanation: Моя мама означає «my mom».
  - source: Це мої батьки.
    options:
    - text: These are my parents.
      correct: true
    - text: This is my father.
      correct: false
    - text: I have parents.
      correct: false
    explanation: Мої батьки означає «my parents».
  - source: У мене тільки один брат.
    options:
    - text: I only have one brother.
      correct: true
    - text: I have two brothers.
      correct: false
    - text: He has one brother.
      correct: false
    explanation: Тільки один означає «only one».


## vocabulary.yaml

- lemma: у мене є
  translation: I have
  pos: phrase
  usage: У мене є брат.
- lemma: у тебе є
  translation: you have, informal
  pos: phrase
  usage: У тебе є сестра?
- lemma: у вас є
  translation: you have, formal or plural
  pos: phrase
  usage: У вас є діти?
- lemma: один
  translation: one, masculine
  pos: numeral
  usage: один брат
- lemma: одна
  translation: one, feminine
  pos: numeral
  usage: одна сестра
- lemma: два
  translation: two, masculine/neuter
  pos: numeral
  usage: два брати
- lemma: дві
  translation: two, feminine
  pos: numeral
  usage: дві сестри
- lemma: тільки
  translation: only
  pos: adverb
  usage: У мене тільки один брат.
- lemma: мій
  translation: my, masculine
  pos: pronoun
  usage: Це мій брат.
- lemma: моя
  translation: my, feminine
  pos: pronoun
  usage: Це моя сестра.
- lemma: моє
  translation: my, neuter
  pos: pronoun
  usage: Це моє місто.
- lemma: мої
  translation: my, plural
  pos: pronoun
  usage: Це мої батьки.
- lemma: твій
  translation: your, masculine informal
  pos: pronoun
  usage: Це твій брат?


## resources.yaml

- title: ULP Season 1, Episode 6 — Family + I Have
  role: podcast
  source_ref: ULP Season 1, Episode 6 — Family + I Have
  url: https://www.ukrainianlessons.com/episode6/
  chunk_id: ulp-1-00-lesson-notes_l0006_w001
  notes: 'Plan reference: family words, the phrase У мене є, and one/two gender agreement.'
- title: ULP Season 1, Episode 7 — Possessive Pronouns
  role: podcast
  source_ref: ULP Season 1, Episode 7 — Possessive Pronouns
  url: https://www.ukrainianlessons.com/episode7/
  chunk_id: ulp-1-00-lesson-notes_l0007_w001
  notes: 'Plan reference: мій/моя/моє/мої and Це моя мама.'
- title: Українська мова. 6 клас. Літвінова (2023)
  role: textbook
  source: Літвінова С. Г. Українська мова. 6 клас
  chunk_id: 6-klas-ukrmova-litvinova-2023_s0265
  notes: 'Граматичне узгодження присвійних займенників у роді та числі: мій/моя/моє/мої,
    твій/твоя/твоє/твої.'
