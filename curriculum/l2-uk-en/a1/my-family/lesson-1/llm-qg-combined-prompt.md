{"independent_effort": "medium", "independent_model": "gpt-6-astra", "independent_reviewer": "codex-tools", "self_reviewer": "agy-tools", "writer": {"effort": "high", "model": "gemini-3.8-flash-high", "writer": "agy-tools"}}
V7 UPGRADE review of lesson 1. Review the published lesson unit, not a fresh module build. No wiki packet or plan rewrite applies. Assess preservation, lesson_split, coherent progression, first-use cumulative vocabulary, final module closure (`Підсумок модуля — Module summary` on the last lesson, not Module completion), no named narrator, marked attributed quotations with Resources entries, no ```text learner examples, and side-by-side English support for added A1 Ukrainian passages of three or more sentences. SOURCES AUDIT: VESUM/`sources` is why the Ukrainian is trustworthy (gender, government, real examples — not Russian calques). This corpus trains a Ukrainian LLM and tests whether the sources tools actually get used. No tool calls = fail. Ungrounded morphology = fail. Judge the current dimension independently using exact quotes from these artifacts. Stress annotation follows review. Lesson map:
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

# Моя сім'я

**Це моя́ сім'я́. У ме́не є брат.** — This is my family. I have a brother.

Family is the first topic where you introduce other people, not only yourself.
Keep the Ukrainian small and photo-based. Point to a person, say who it is,
and add one simple line with **У ме́не є...** or **Це мій / моя́...**.

By the end, you can:

- name close family members: **мама**, **тато**, **брат**, **сестра**,
  **бабуся**, **дідусь**;
- ask **У тебе є брат?** and answer with **Так, у мене є...** or **Ні.**;
- use **один брат**, **одна сестра**, **два брати**, and **дві сестри**;
- choose **мій**, **моя**, **моє**, or **мої** by the family word, not by
  the owner;
- recognize **його** and **її** in lines such as **Його звати...** and
  **Її звати...**;
- say **сім'я** for your close family and recognize **родина** as the wider
  family or kin circle;
- recognize a formal patronymic greeting without producing patronymics yet.

### Розминка — Warm-up and retrieval

Before looking at family photos, recall the greeting and introduction phrases from previous lessons: **Привіт!** — Hello!, **Як справи?** — How are you?, and **Мене звати...** — My name is... When showing a photo to a Ukrainian friend, we start with a friendly greeting and then point to people we love.

| Ситуація — Situation | Українська фраза — Ukrainian phrase | English support |
| --- | --- | --- |
| Greeting a friend | **Приві́т! Як спра́ви?** | Hi! How are you? |
| Introducing yourself | **Мене́ зва́ти Софі́я.** | My name is Sofiia. |
| Asking who someone is | **Хто це?** | Who is this? |
| Pointing to a photo | **Диви́сь, це моя́ сім'я́.** | Look, this is my family. |

## Діало́ги

Read the Ukrainian first as a photo exchange. You do not need the whole grammar
of possession. Treat **У ме́не є** and **У те́бе є** as whole phrases.

```text
О́ля: Приві́т, Ма́рку! Це фо́то моє́ї сім'ї́.
Марк: Кла́сно! У те́бе є брати́ чи се́стри?
О́ля: Так, у ме́не є два брати́ і одна́ сестра́.
Марк: Ого́! У ме́не ті́льки оди́н брат.
О́ля: Як його́ зва́ти?
Марк: Його́ зва́ти Ко́ля.
```

English support after the Ukrainian dialogue:

| Українська | English support |
| --- | --- |
| **Це фо́то моє́ї сім'ї́.** | This is a photo of my family. |
| **У те́бе є брати́ чи се́стри?** | Do you have brothers or sisters? |
| **У ме́не є два брати́ і одна́ сестра́.** | I have two brothers and one sister. |
| **Як його́ зва́ти?** | What is his name? |

Now use **це** to identify people in a family photo.

```text
Да́ша: Це моя́ сім'я́ на фотогра́фії.
Андрі́й: Хто це?
Да́ша: Це моя́ ма́ма Мари́на. Це мій та́то Євге́н.
Андрі́й: А це твоя́ сестра́?
Да́ша: Так. Це моя́ сестра́ Ка́тя і мої́ брати́, Іва́н і Дени́с.
Андрі́й: А це твоя́ бабу́ся?
Да́ша: Так, її́ зва́ти Тетя́на.
```

English support after the Ukrainian dialogue:

| Українська | English support |
| --- | --- |
| **Це моя́ сім'я́.** | This is my family. |
| **Хто це?** | Who is this? |
| **Це моя́ ма́ма.** | This is my mom. |
| **Це мій та́то.** | This is my dad. |
| **її́ зва́ти Тетя́на.** | Her name is Tetiana. |

A short connected answer can reuse M5 and add family:

```text
Приві́т! Мене́ зва́ти Софі́я.
Моя́ ма́ма — вчи́телька.
Мій та́то — інжене́р.
У ме́не є оди́н брат.
```

Notice the question word from earlier modules: **хто?** asks about a person.
For this lesson, use it in **Хто це?** and keep the answers short.

The old name phrase still works inside family talk: **Мене звати [ім'я]**. Use
it as one memorized block before you add family information.

<!-- INJECT_ACTIVITY: act-1 -->

### Корисні репліки для розмови — Useful conversational phrases

When speaking with friends about photographs, you will often hear natural reactions. Notice how speakers react with genuine interest: **Класно!** — Great!, **Ого!** — Wow!, and **Добре!** — Good!

> **Олекса́**: Хто це на фотогра́фії?
> **Богда́н**: Це мій брат. Його́ зва́ти Петро́.
> **Олекса́**: Кла́сно! А хто це бі́ля бра́та?
> **Богда́н**: Це моя́ сестра́ Мари́на.

| Репліка — Turn | English support |
| --- | --- |
| **Хто це на фотогра́фії?** | Who is this in the photo? |
| **Це мій брат. Його́ зва́ти Петро́.** | This is my brother. His name is Petro. |
| **Кла́сно! А хто це бі́ля бра́та?** | Great! And who is this next to your brother? |
| **Це моя́ сестра́ Мари́на.** | This is my sister Maryna. |

<!-- INJECT_ACTIVITY: act-101 -->

## Сім'я́

Use family words with a photo or a simple drawing. The first task is not a
family tree; it is recognizing and saying the common people words.

| Ukrainian | English |
| --- | --- |
| **сім'я** | family, usually the close household |
| **родина** | family or kin, often wider than the household |
| **мама / мати** | mom / mother |
| **тато / батько** | dad / father |
| **брат** | brother |
| **сестра** | sister |
| **син** | son |
| **дочка / донька** | daughter |
| **бабуся** | grandmother |
| **дідусь** | grandfather |
| **батьки** | parents |
| **родичі** | relatives |

Ukrainian does not use one normal beginner word for "grandparents." Say
**бабуся і дідусь**.

The gender habit starts here. Say **він / мій** with masculine family words:
**тато**, **брат**, **син**, **дідусь**. Say **вона / моя** with feminine
family words: **мама**, **мати**, **сестра**, **дочка**, **донька**,
**бабуся**.

| Pointing line | English |
| --- | --- |
| **Це мій брат. Він студент.** | This is my brother. He is a student. |
| **Це моя сестра. Вона студентка.** | This is my sister. She is a student. |
| **Це мій син.** | This is my son. |
| **Це моя дочка.** | This is my daughter. |

Ukrainian also has a formal full-name pattern: given name, patronymic, and
surname: **Марія Василівна Коваленко**. At A1, only recognize the signal.
You might hear **Добрий день, Маріє Василівно!** in a formal setting. This is
recognition-only; do not try to build your own patronymic forms yet.

Use **ім'я** for given name, **прізвище** for surname, and **по батькові** for
patronymic. Patronymics are a Ukrainian naming tradition and not something to
erase or treat as outside Ukrainian culture. Production waits until a later
level.

<!-- INJECT_ACTIVITY: act-2 -->

### Різниця між сім'я та родина — Nuances of family terms

In Ukrainian culture, both words are widely used, but they carry a slight difference in perspective. **Сім'я́** usually refers to the immediate household living under one roof (parents and children). **Роди́на** often refers to the wider circle of blood relatives, ancestral generations, and kin. In school textbooks, children often learn the traditional line: *"Родина, родина — від батька до сина"* <!-- VERIFY: textbook="2-klas-ukrmova-vashulenko-2019-1" chunk="2-klas-ukrmova-vashulenko-2019-1_s0092" -->.

| Термін — Term | Значення — Meaning | Приклад — Example |
| --- | --- | --- |
| **сім'я́** | immediate family, household | **Це моя́ ма́ленька сім'я́.** — This is my small family. |
| **роди́на** | family, kin, generations | **У нас вели́ка роди́на.** — We have a big family. |
| **батьки́** | parents (mother and father together) | **Це мої́ батьки́.** — These are my parents. |
| **ро́дичі** | relatives | **Це мої́ ро́дичі.** — These are my relatives. |

<!-- INJECT_ACTIVITY: act-102 -->

### Граматичний рід і професії — Gender and roles

Notice how descriptions match natural gender. When talking about family members and what they do, Ukrainian uses masculine forms for men and feminine forms for women:

| Чоловічий рід — Masculine (він) | Жіночий рід — Feminine (вона) | English meaning |
| --- | --- | --- |
| **Мій брат — студе́нт.** | **Моя́ сестра́ — студе́нтка.** | student |
| **Мій та́то — вчи́тель.** | **Моя́ ма́ма — вчи́телька.** | teacher |
| **Мій син — школя́р.** | **Моя́ дочка́ — школя́рка.** | school pupil |
| **Мій діду́сь — інжене́р.** | **Моя́ бабу́ся — лі́карка.** | engineer / doctor |

<!-- INJECT_ACTIVITY: act-103 -->

### Підсумок уроку — Lesson recap

In this lesson, you took your first step into talking about people beyond yourself. You can now point to family photos and introduce your close relatives:

- name key family members: **мама**, **тато**, **брат**, **сестра**, **бабуся**, **дідусь**;
- distinguish between **сім'я** (immediate household) and **родина** (wider family);
- identify people using **Хто це?** and answer with **Це мій...** or **Це моя...**;
- recognize the formal full-name model (**ім'я + по батькові + прізвище**).

In the next lesson, you will master the Ukrainian possession formula **У мене є...** and practice choosing between **мій**, **моя**, **моє**, and **мої**.


## activities.yaml

inline:
- id: act-1
  type: quiz
  title: Питання до фото
  instruction: Обери український рядок для фото-розмови.
  items:
  - prompt: Ти питаєш одного ровесника про брата.
    options:
    - text: У тебе є брат?
      correct: true
    - text: У мене є брат?
      correct: false
    - text: Це брат?
      correct: false
    explanation: У тебе є...? питає одну знайому людину.
  - prompt: Ти відповідаєш так і кажеш, що маєш одну сестру.
    options:
    - text: Так, у мене є одна сестра.
      correct: true
    - text: Так, у тебе є одна сестра.
      correct: false
    - text: Так, це одна сестра.
      correct: false
    explanation: У мене є... відповідає за себе.
  - prompt: Ти відповідаєш ні короткою A1-фразою.
    options:
    - text: Ні.
      correct: true
    - text: У мене немає брат.
      correct: false
    - text: Ні є брат.
      correct: false
    explanation: На A1 тримай заперечну відповідь простою.
  - prompt: Ти питаєш, як його звати.
    options:
    - text: Як його звати?
      correct: true
    - text: Як її звати?
      correct: false
    - text: Що його звати?
      correct: false
    explanation: Його підходить до брата, тата, сина або дідуся.
  - prompt: Ти показуєш маму на фото.
    options:
    - text: Це моя мама.
      correct: true
    - text: Це мій мама.
      correct: false
    - text: Це моє мама.
      correct: false
    explanation: Мама — жіночого роду, тому моя.
  - prompt: Ти показуєш батьків.
    options:
    - text: Це мої батьки.
      correct: true
    - text: Це мій батьки.
      correct: false
    - text: Це моя батьки.
      correct: false
    explanation: Батьки — множина, тому мої.
- id: act-101
  type: match-up
  title: Фрази знайомства з сім'єю
  instruction: З'єднай початок фрази з її продовженням.
  pairs:
  - left: Це моя сім'я
    right: на фотографії.
  - left: У тебе є
    right: брати чи сестри?
  - left: У мене є два брати
    right: і одна сестра.
  - left: Як його
    right: звати?
  - left: Це моя сестра Катя,
    right: а це мій брат Коля.
  - left: Хто це?
    right: Це моя мама.
- id: act-2
  type: match-up
  title: Слова родини
  instruction: З'єднай українське слово з українською підказкою.
  pairs:
  - left: мама
    right: мати
  - left: тато
    right: батько
  - left: брат
    right: син для моїх батьків
  - left: сестра
    right: дочка для моїх батьків
  - left: бабуся
    right: мама мами або тата
  - left: дідусь
    right: тато мами або тата
  - left: батьки
    right: мама і тато
  - left: родичі
    right: люди з родини
- id: act-102
  type: quiz
  title: Хто це на фото?
  instruction: Обери правильне слово для людини на фотографії.
  items:
  - prompt: Жінка, яка народила дитину — це...
    options:
    - text: мама
      correct: true
    - text: тато
      correct: false
    - text: брат
      correct: false
    explanation: Мама (мати) — жінка стосовно своїх дітей.
  - prompt: Чоловік, батько дітей — це...
    options:
    - text: тато
      correct: true
    - text: сестра
      correct: false
    - text: бабуся
      correct: false
    explanation: Тато (батько) — чоловік стосовно своїх дітей.
  - prompt: Хлопець для своїх батьків — це...
    options:
    - text: син
      correct: true
    - text: дочка
      correct: false
    - text: мати
      correct: false
    explanation: Хлопець для батьків — це син.
  - prompt: Дівчина для своїх батьків — це...
    options:
    - text: дочка
      correct: true
    - text: син
      correct: false
    - text: дідусь
      correct: false
    explanation: Дівчина для батьків — це дочка (донька).
  - prompt: Мама твого тата або мами — це...
    options:
    - text: бабуся
      correct: true
    - text: сестра
      correct: false
    - text: мати
      correct: false
    explanation: Мама батьків — це бабуся.
  - prompt: Тато твого тата або мами — це...
    options:
    - text: дідусь
      correct: true
    - text: брат
      correct: false
    - text: син
      correct: false
    explanation: Тато батьків — це дідусь.
- id: act-103
  type: fill-in
  title: Він чи вона?
  instruction: Встав займенник він або вона.
  items:
  - sentence: Це мій брат. ___ студент.
    answer: Він
    options:
    - Він
    - Вона
    explanation: Брат — чоловічий рід (він).
  - sentence: Це моя сестра. ___ студентка.
    answer: Вона
    options:
    - Вона
    - Він
    explanation: Сестра — жіночий рід (вона).
  - sentence: Це мій тато. ___ інженер.
    answer: Він
    options:
    - Він
    - Вона
    explanation: Тато — чоловічий рід (він).
  - sentence: Це моя мама. ___ вчителька.
    answer: Вона
    options:
    - Вона
    - Він
    explanation: Мама — жіночий рід (вона).
  - sentence: Це мій син. ___ школяр.
    answer: Він
    options:
    - Він
    - Вона
    explanation: Син — чоловічий рід (він).
  - sentence: Це моя дочка. ___ школярка.
    answer: Вона
    options:
    - Вона
    - Він
    explanation: Дочка — жіночий рід (вона).
workbook:
- id: act-w1
  type: error-correction
  title: Обери українське родинне речення
  instruction: Обери безпечніший український рядок.
  items:
  - sentence: Моє ім'я є Джон.
    error: Моє ім'я є Джон.
    correction: Мене звати Джон.
    options:
    - Мене звати Джон.
    - Моє ім'я є Джон.
    explanation: Мене звати... — природна модель першого представлення.
  - sentence: Я маю брата.
    error: Я маю брата.
    correction: У мене є брат.
    options:
    - У мене є брат.
    - Я маю брата.
    explanation: Для родини на A1 вживай безпечний блок У мене є...
  - sentence: Це мій мама.
    error: Це мій мама.
    correction: Це моя мама.
    options:
    - Це моя мама.
    - Це мій мама.
    explanation: Мама — жіночого роду, тому вживай моя.
  - sentence: Це є мій брат.
    error: Це є мій брат.
    correction: Це мій брат.
    options:
    - Це мій брат.
    - Це є мій брат.
    explanation: У простому фото-реченні є не потрібне.
  - sentence: Батьки (у значенні батька)
    error: Батьки (у значенні батька)
    correction: Тато / батько
    options:
    - Тато / батько
    - Батьки
    explanation: Батьки означає маму й тата або кількох батьків, а не одного тата.
  - sentence: У мене немає брат.
    error: У мене немає брат.
    correction: Ні.
    options:
    - Ні.
    - У мене немає брат.
    explanation: На A1 відповідай коротко; повний блок із немає буде пізніше.
- id: act-w101
  type: match-up
  title: Родинні пари
  instruction: З'єднай чоловічі та жіночі назви членів родини.
  pairs:
  - left: тато
    right: мама
  - left: батько
    right: мати
  - left: брат
    right: сестра
  - left: син
    right: дочка
  - left: дідусь
    right: бабуся
  - left: він
    right: вона
- id: act-w102
  type: group-sort
  title: 'Він чи вона: рід членів родини'
  instruction: Розподіли слова за граматичним родом.
  groups:
  - label: він (чоловічий рід)
    items:
    - тато
    - батько
    - брат
    - син
    - дідусь
  - label: вона (жіночий рід)
    items:
    - мама
    - мати
    - сестра
    - дочка
    - бабуся
- id: act-w103
  type: fill-in
  title: Доповни речення про сім'ю
  instruction: Обери правильне слово для кожного речення.
  items:
  - sentence: Це мій тато. ___ інженер.
    answer: Він
    options:
    - Він
    - Вона
    - Воно
    explanation: Тато — чоловічого роду (він).
  - sentence: Це моя мама. ___ вчителька.
    answer: Вона
    options:
    - Вона
    - Він
    - Воно
    explanation: Мама — жіночого роду (вона).
  - sentence: Це мій брат. ___ звати Іван.
    answer: Його
    options:
    - Його
    - Її
    - Їх
    explanation: Його вживаємо про брата.
  - sentence: Це моя сестра. ___ звати Оля.
    answer: Її
    options:
    - Її
    - Його
    - Мій
    explanation: Її вживаємо про сестру.
  - sentence: Це мої ___ — мама і тато.
    answer: батьки
    options:
    - батьки
    - брати
    - дідусі
    explanation: Мама і тато разом — батьки.
  - sentence: — ___ це? — Це мій дідусь.
    answer: Хто
    options:
    - Хто
    - Що
    - Як
    explanation: Хто запитує про людину.
- id: act-w104
  type: unjumble
  title: Склади речення про знайомство
  instruction: Розташуй слова у правильному порядку.
  items:
  - words:
    - Це
    - моя
    - сім'я.
    sentence: Це моя сім'я.
  - words:
    - Хто
    - це
    - на
    - фото?
    sentence: Хто це на фото?
  - words:
    - Це
    - мій
    - брат
    - Коля.
    sentence: Це мій брат Коля.
  - words:
    - Як
    - його
    - звати?
    sentence: Як його звати?
  - words:
    - Це
    - моя
    - мама
    - Марина.
    sentence: Це моя мама Марина.
  - words:
    - Це
    - мої
    - батьки.
    sentence: Це мої батьки.
- id: act-w105
  type: translate
  title: 'Переклад: знайомство з родиною'
  instruction: Обери правильний український переклад для кожного рядка.
  items:
  - source: This is my family.
    options:
    - text: Це моя сім'я.
      correct: true
    - text: Це моє місто.
      correct: false
    - text: Це мій брат.
      correct: false
    explanation: Сім'я — жіночого роду (моя сім'я).
  - source: Who is this?
    options:
    - text: Хто це?
      correct: true
    - text: Що це?
      correct: false
    - text: Де це?
      correct: false
    explanation: Хто питає про людину.
  - source: This is my father.
    options:
    - text: Це мій тато.
      correct: true
    - text: Це моя мама.
      correct: false
    - text: Це мої батьки.
      correct: false
    explanation: Тато — чоловічого роду (мій тато).
  - source: This is my sister.
    options:
    - text: Це моя сестра.
      correct: true
    - text: Це мій брат.
      correct: false
    - text: Це моя дочка.
      correct: false
    explanation: Сестра — жіночого роду (моя сестра).
  - source: These are my parents.
    options:
    - text: Це мої батьки.
      correct: true
    - text: Це мій батько.
      correct: false
    - text: Це моя родина.
      correct: false
    explanation: Батьки — множина (мої батьки).
  - source: His name is Kolia.
    options:
    - text: Його звати Коля.
      correct: true
    - text: Її звати Катя.
      correct: false
    - text: Мене звати Коля.
      correct: false
    explanation: Його вживаємо про чоловіка або хлопця.
- id: act-w106
  type: quiz
  title: Розуміння родинних зв'язків
  instruction: Прочитай запитання та обери правильну відповідь.
  items:
  - prompt: Хто такий тато?
    options:
    - text: Батько
      correct: true
    - text: Брат
      correct: false
    - text: Син
      correct: false
    explanation: Тато і батько — синоніми.
  - prompt: Хто така мама?
    options:
    - text: Мати
      correct: true
    - text: Сестра
      correct: false
    - text: Бабуся
      correct: false
    explanation: Мама і мати — синоніми.
  - prompt: Мама і тато разом — це...
    options:
    - text: батьки
      correct: true
    - text: брати
      correct: false
    - text: дідусі
      correct: false
    explanation: Батьки — це мама й тато.
  - prompt: Мама моєї мами — це моя...
    options:
    - text: бабуся
      correct: true
    - text: сестра
      correct: false
    - text: дочка
      correct: false
    explanation: Мама мами — бабуся.
  - prompt: Тато мого тата — це мій...
    options:
    - text: дідусь
      correct: true
    - text: брат
      correct: false
    - text: батько
      correct: false
    explanation: Тато тата — дідусь.
  - prompt: Син моїх батьків для мене — це мій...
    options:
    - text: брат
      correct: true
    - text: дідусь
      correct: false
    - text: тато
      correct: false
    explanation: Син батьків — брат.


## vocabulary.yaml

- lemma: сім'я
  translation: family, close household
  pos: noun
  usage: Це моя сім'я.
- lemma: родина
  translation: family or kin
  pos: noun
  usage: У мене велика родина.
- lemma: мама
  translation: mom
  pos: noun
  usage: Це моя мама.
- lemma: мати
  translation: mother
  pos: noun
  usage: Це моя мати.
- lemma: тато
  translation: dad
  pos: noun
  usage: Це мій тато.
- lemma: батько
  translation: father
  pos: noun
  usage: Це мій батько.
- lemma: брат
  translation: brother
  pos: noun
  usage: У мене є брат.
- lemma: сестра
  translation: sister
  pos: noun
  usage: У мене є сестра.
- lemma: син
  translation: son
  pos: noun
  usage: Це мій син.
- lemma: дочка
  translation: daughter
  pos: noun
  usage: Це моя дочка.
- lemma: донька
  translation: daughter
  pos: noun
  usage: Це моя донька.
- lemma: бабуся
  translation: grandmother
  pos: noun
  usage: Це моя бабуся.
- lemma: дідусь
  translation: grandfather
  pos: noun
  usage: Це мій дідусь.
- lemma: батьки
  translation: parents
  pos: noun plural
  usage: Це мої батьки.


## resources.yaml

- title: ULP Season 1, Episode 6 — Family + I Have
  role: podcast
  source_ref: ULP Season 1, Episode 6 — Family + I Have
  url: https://www.ukrainianlessons.com/episode6/
  chunk_id: ext-ulp_blogs-68
  notes: 'Plan reference: family words, the phrase У мене є, and one/two gender agreement.'
- title: Українська мова. 2 клас. Вашуленко (2019)
  role: textbook
  source: Вашуленко М. С., Дубовик С. Г. Українська мова та читання. 2 клас
  chunk_id: 2-klas-ukrmova-vashulenko-2019-1_s0092
  notes: 'Назви членів сім''ї та поняття родина: «Родина, родина — від батька до сина».'
- title: ULP Season 1, Episode 7 — Possessive Pronouns
  role: podcast
  source_ref: ULP Season 1, Episode 7 — Possessive Pronouns
  url: https://www.ukrainianlessons.com/episode7/
  notes: 'Plan reference: мій/моя/моє/мої and Це моя мама.'
