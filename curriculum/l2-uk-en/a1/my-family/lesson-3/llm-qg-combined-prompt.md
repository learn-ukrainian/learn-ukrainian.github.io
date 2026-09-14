{"independent_effort": "medium", "independent_model": "gpt-6-astra", "independent_reviewer": "codex-tools", "self_reviewer": "agy-tools", "writer": {"effort": "high", "model": "gemini-3.8-flash-high", "writer": "agy-tools"}}
V7 UPGRADE review of lesson 3. Review the published lesson unit, not a fresh module build. No wiki packet or plan rewrite applies. Assess preservation, lesson_split, coherent progression, first-use cumulative vocabulary, final module closure (`Підсумок модуля — Module summary` on the last lesson, not Module completion), no named narrator, marked attributed quotations with Resources entries, no ```text learner examples, and side-by-side English support for added A1 Ukrainian passages of three or more sentences. SOURCES AUDIT: VESUM/`sources` is why the Ukrainian is trustworthy (gender, government, real examples — not Russian calques). This corpus trains a Ukrainian LLM and tests whether the sources tools actually get used. No tool calls = fail. Ungrounded morphology = fail. Judge the current dimension independently using exact quotes from these artifacts. Stress annotation follows review. Lesson map:
{"lessons": [{"n": 1, "title": "Сім'я", "sections": ["Діалоги", "Сім'я"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}, {"n": 2, "title": "Мій / моя", "sections": ["У мене є", "Мій / моя"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}, {"n": 3, "title": "Слухай, фото, зошит", "sections": ["Слухай, фото, зошит"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}, {"n": 4, "title": "Самоперевірка", "sections": ["Самоперевірка"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}], "closes_module": 4, "provenance": [{"placement": "inline", "index": 0, "new_id": "act-1", "lesson": 1}, {"placement": "inline", "index": 1, "new_id": "act-2", "lesson": 1}, {"placement": "inline", "index": 2, "new_id": "act-3", "lesson": 2}, {"placement": "inline", "index": 3, "new_id": "act-4", "lesson": 2}, {"placement": "workbook", "index": 0, "new_id": "act-w1", "lesson": 1}, {"placement": "workbook", "index": 1, "new_id": "act-w2", "lesson": 2}, {"placement": "workbook", "index": 2, "new_id": "act-w3", "lesson": 2}, {"placement": "workbook", "index": 3, "new_id": "act-w4", "lesson": 3}, {"placement": "workbook", "index": 4, "new_id": "act-w5", "lesson": 4}, {"placement": "workbook", "index": 5, "new_id": "act-w6", "lesson": 4}], "items_min_exempt": [{"id": "act-w4", "reason": "4-item original activity preserved from baseline"}, {"id": "act-w5", "reason": "5-item original activity preserved from baseline"}, {"id": "act-w6", "reason": "5-item original activity preserved from baseline"}], "proper_names": []}
Gemini self-review: you wrote this. Adjust if VESUM/`sources` would change a form. Calling sources is how the Ukrainian gets better, and this run tests that the tools work (LLM dataset). If you skipped tools while writing, call them now and fix.

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

# Слу́хай, фо́то, зошит

У пе́рших двох уро́ках ви познайо́милися з назва́ми чле́нів сім'ї́ та навчи́лися говори́ти про володі́ння: **У ме́не є...**, **Це мій брат**, **Це моя́ сестра́**. In the first two lessons, you practiced identifying family members and expressing relationships with **у ме́не є** and possessive pronouns.

Тепе́р час поєдна́ти ці нави́чки в реа́льних ситуа́ціях спілкува́ння — now it is time to connect these skills in everyday contexts:
- **Слу́хати живе́ мо́влення** — listen to authentic Ukrainian family speech and understand questions about relatives;
- **Розпізнава́ти підписи до фо́то** — read captions on family snapshots using **твій**, **твоя́**, **твоє́**, **твої́**, **йо́го**, and **її́**;
- **Працюва́ти з зо́шитом** — connect printed and handwritten Ukrainian labels for core family words;
- **Розпізнава́ти офіці́йні імена́** — recognize the three parts of full Ukrainian names (**ім'я́**, **по ба́тькові**, **прі́звище**) as polite cultural markers.

### Розминка — Warm-up and retrieval

Before diving into audio recordings and photo labels, recall the core family vocabulary and pointing patterns from Lessons 1 and 2:

| Українська фраза — Ukrainian phrase | Роль — Role | English meaning |
| --- | --- | --- |
| **Хто це?** | Питання про людину — Asking about a person | Who is this? |
| **Це мій брат.** | Чоловічий рід — Masculine agreement | This is my brother. |
| **Це моя сестра.** | Жіночий рід — Feminine agreement | This is my sister. |
| **Це моє місто.** | Середній рід — Neuter agreement | This is my city / hometown. |
| **Це мої батьки.** | Множина — Plural agreement | These are my parents. |
| **У тебе є брат?** | Запитання про родича — Question about family | Do you have a brother? |
| **Так, у мене є один брат.** | Ствердна відповідь — Affirmative answer | Yes, I have one brother. |

Notice that the question **Хто це?** specifically asks about a person, while **Це...** introduces anyone in a photo.

## Слу́хай, фо́то, зошит

The Resources tab has optional Ukrainian Lessons Podcast pages for this topic:
Episode 6 for **сім'я́ / У ме́не є...**, Episode 7 for **мій / моя́**, and
Episode 10 for connected review speech. Choose one short phrase, listen once,
repeat once, and come back to the page.

For handwriting recognition, ask a teacher, tutor, or classmate to write these
original labels beside a simple family sketch: **ма́ма**, **та́то**,
**брат**, **сестра́**, **сім'я́**, **бабу́ся**. First compare the notebook
label with the printed word; then write your own line.

### Слухаємо подкаст — Listening to family speech

Listening to natural Ukrainian speech trains your ear to recognize family words within continuous sentences. In Episode 6, Episode 7, and Episode 10 of the Ukrainian Lessons Podcast, speakers point to family snapshots and describe their relatives.

Listen to how two friends look through a digital photo gallery on a smartphone:

> Софі́я: Подиви́сь, це мої́ ста́рі сіме́йні фотогра́фії!
> Рома́н: Ду́же ціка́во! Хто це на фо́то?
> Софі́я: Це моя́ бабу́ся Тетя́на і мій діду́сь Васи́ль.
> Рома́н: А це твій та́то?
> Софі́я: Так, це мій та́то Євге́н, а пору́ч — його́ сестра́ Окса́на. Це моя́ ті́тка.
> Рома́н: Як гарно! А чи є в тебе фотогра́фія бра́та?
> Софі́я: Так, ось мій бра́т Ко́ля. Його́ зва́ти Мико́ла, але ми ка́жемо Ко́ля.

English breakdown after the Ukrainian dialogue:

| Українська фраза | English breakdown |
| --- | --- |
| **Подиви́сь, це мої́ ста́рі сіме́йні фотогра́фії!** | Look, these are my old family photos! |
| **Хто це на фо́то?** | Who is this in the photo? |
| **Це моя́ бабу́ся Тетя́на і мій діду́сь Васи́ль.** | This is my grandmother Tetiana and my grandfather Vasyl. |
| **А це твій та́то?** | And is this your dad? |
| **А пору́ч — його́ сестра́ Окса́на.** | And next to him is his sister Oksana. |
| **А чи є в тебе фотогра́фія бра́та?** | And do you have a photo of your brother? |
| **Його́ зва́ти Мико́ла, але ми ка́жемо Ко́ля.** | His name is Mykola, but we call him Kolia. |

When asking a polar question (yes/no question), Ukrainian often uses the particle **чи** at the start of a sentence: **Чи це твоя бабуся?** — Is this your grandmother? You can also simply use rising intonation: **Це твій тато? ↗**.

<!-- INJECT_ACTIVITY: act-301 -->

### Сімейні фотографії — Reading photo labels

When people share family photos or post them online, they attach short captions to introduce relatives. In these captions, possessive pronouns indicate whose relative is shown.

Remember that possessive pronouns agree in gender and number with the family word, not with the speaker:

| Рід або число — Gender / Number | Форма «твій» — Your form | Зразок підпису — Sample caption | English translation |
| --- | --- | --- | --- |
| **Чоловічий рід (він)** | **твій** | **Це твій брат?** | Is this your brother? |
| **Жіночий рід (вона)** | **твоя** | **Це твоя сестра Катя.** | This is your sister Katia. |
| **Середній рід (воно)** | **твоє** | **Це твоє рідне місто?** | Is this your hometown? |
| **Множина (вони)** | **твої** | **Це твої батьки на фото.** | These are your parents in the photo. |

Unlike **твій / твоя / твоє / твої**, the third-person possessive words **його** (his) and **її** (her) do not decline:
- **його тато** (his dad), **його мама** (his mom), **його місто** (his city), **його батьки** (his parents);
- **її тато** (her dad), **її мама** (her mom), **її місто** (her city), **її батьки** (her parents).

They stay constant regardless of whether the possessed noun is masculine, feminine, neuter, or plural:

| Український підпис | Пояснення — Explanation | English support |
| --- | --- | --- |
| **Це мій брат Коля. Його звати Микола.** | Masculine subject → **його** | This is my brother Kolia. His name is Mykola. |
| **Це моя сестра Катя. Її звати Катерина.** | Feminine subject → **її** | This is my sister Katia. Her name is Kateryna. |
| **Це її мама Марина.** | Invariable possessive **її** | This is her mom Maryna. |
| **Це його тато Євген.** | Invariable possessive **його** | This is his dad Yevhen. |

<!-- INJECT_ACTIVITY: act-302 -->

### Рукописний зошит — Notebook and handwriting recognition

In real Ukrainian classrooms and daily life, family words are frequently written by hand in personal notebooks (**зо́шит**). Reading cursive handwriting requires connecting printed Cyrillic typography with handwriting letterforms.

Pay special attention to these common family words when reading or writing in a notebook:

| Друковане слово — Printed | Наголос — Stress | Значення — Meaning | Особливість написання — Writing note |
| --- | --- | --- | --- |
| **мама** | **ма́ма** | mom | Two simple syllables with round **а** |
| **тато** | **та́то** | dad | Ending in **-о**, but masculine gender |
| **брат** | **бра́т** | brother | Single-syllable word; no vowel reduction |
| **сестра** | **сестра́** | sister | End-stressed in singular (**сестра́**), stem-stressed in plural (**се́стри**) |
| **сім'я** | **сім'я́** | family (close) | Apostrophe after **м** before **я**; end-stress |
| **бабуся** | **бабу́ся** | grandmother | Soft ending **-ся**; affectionate tone |
| **дідусь** | **діду́сь** | grandfather | Soft sign **-сь** at the end |

Educational guidelines emphasize creating clear photo presentations and labeling family members accurately: «Вставте на титульний слайд фотографію вашої родини... Уведіть назву презентації («Моя родина») та автора (ваше прізвище, ім'я)» (quoted from: Т. В. Воронцова, *Інформатика. 4 клас*, с. 122).

When creating your personal notebook entry:
1. Draw or paste a simple snapshot or sketch of your family.
2. Label each person clearly with their relationship: **Це моя мама**, **Це мій тато**, **Це мій брат**.
3. Underneath, add their name: **Її звати...** or **Його звати...**.

<!-- INJECT_ACTIVITY: act-303 -->

### Повне ім'я як сигнал — Recognizing formal names

Ukrainian personal names follow a three-part cultural tradition that you will encounter on official identification, badges, class registers, and formal signs:

```text
Ім'я́ (Given Name) + По ба́тькові (Patronymic) + Прі́звище (Surname)
Марі́я           + Васи́лівна               + Ковале́нко
```

Understanding how these parts function helps you recognize formal address:

| Складник — Component | Приклад — Example | Роль — Cultural function |
| --- | --- | --- |
| **Ім'я́** | **Марія**, **Іван**, **Олена** | Given name used with family, friends, and peers |
| **По ба́тькові** | **Василівна**, **Іванович** | Patronymic based on father's name; sign of polite, formal respect |
| **Прі́звище** | **Коваленко**, **Шевченко** | Family surname shared across generations |
| **Мі́сто** | **Київ**, **Львів**, **Полтава** | City or place of residence listed on forms and documents |

Ukrainian feminine patronymics end in **-івна** or **-ївна** (e.g., *Василівна*, *Сергіївна*), never the Russian suffix *-овна*. Masculine patronymics end in **-ович** or **-йович** (e.g., *Іванович*, *Васильович*).

When meeting an official, teacher, or doctor, you will hear formal greetings using the vocative case: **«До́брий день, Марі́є Васи́лівно!»**. At the A1 level, you only need to recognize this structure as a signal of polite respect. You do not need to construct your own patronymic endings yet.

<!-- INJECT_ACTIVITY: act-304 -->

<!-- INJECT_ACTIVITY: act-305 -->

### Практикуємо разом — Guided dialogue practice

Review how notebook notes and photos come together when students discuss a completed assignment:

> Марко́: Оле́но, чий це зо́шит на столі́?
> Оле́на: Це мій зо́шит для уро́ків украї́нської мо́ви.
> Марко́: А що тут напи́сано бі́ля фотогра́фії?
> Оле́на: Тут напи́сано: «Моя́ сім'я́». Ось моє́ ім'я́, а це моє́ рідне мі́сто Полта́ва.
> Марко́: Ду́же акура́тно! А хто це вгорі́ на зні́мку?
> Оле́на: Це моя́ бабу́ся Тетя́на і її́ сестра́ Наді́я. Вони́ живу́ть у селі́.
> Марко́: Дя́кую! Тепе́р я теж оформлю́ свій сіме́йний зо́шит.

Side-by-side English support for the dialogue:

| Українська репліка | English support |
| --- | --- |
| **Чий це зо́шит на столі́?** | Whose notebook is this on the table? |
| **Це мій зо́шит для уро́ків украї́нської мо́ви.** | This is my notebook for Ukrainian language lessons. |
| **А що тут напи́сано бі́ля фотогра́фії?** | And what is written here next to the photo? |
| **Тут напи́сано: «Моя́ сім'я́».** | It is written here: "My family". |
| **Ось моє́ ім'я́, а це моє́ рідне мі́сто Полта́ва.** | Here is my name, and this is my hometown Poltava. |
| **А хто це вгорі́ на зні́мку?** | And who is this at the top of the snapshot? |
| **Це моя́ бабу́ся Тетя́на і її́ сестра́ Наді́я.** | This is my grandmother Tetiana and her sister Nadiia. |
| **Тепе́р я теж оформлю́ свій сіме́йний зо́шит.** | Now I will also set up my family notebook. |

### Підсумок уроку — Lesson recap

У цьо́му уро́ці ви навчи́лися поєдну́вати слуха́ння, чита́ння підписів до фотогра́фій та робо́ту з рукопи́сним зо́шитом — in this lesson you have developed key multimedia and observational skills for family communication:
- **Слу́хати живе́ мо́влення** — understand natural questions and descriptions from podcast audio when people discuss family snapshots;
- **Вжива́ти твій, твоя́, твоє́, твої́** — select the correct possessive form based on the gender and number of the noun in questions and captions;
- **Розпізнава́ти йо́го та її́** — identify third-person possessives as invariable markers (*його́ брат*, *її́ сестра́*);
- **Розрізня́ти друко́вані й рукопи́сні фо́рми** — connect cursive and printed letters for core family words (**ма́ма**, **та́то**, **бра́т**, **сестра́**, **бабу́ся**, **сім'я́**);
- **Розпізнава́ти три скла́дники і́мені** — identify given name (**ім'я́**), patronymic (**по ба́тькові**), and surname (**прі́звище**) as polite formal signals.

### Наступний крок — Next step

In Lesson 4 (**Самоперевірка**), you will complete the module by bringing together all family terms, possessive pronouns, and descriptive sentences to introduce your entire family in a confident, connected Ukrainian presentation.


## activities.yaml

inline:
- id: act-301
  type: quiz
  title: Запитання до сімейних фото
  instruction: Обери правильну відповідь або запитання для розмови про фотографії.
  items:
  - prompt: Ти хочеш спитати, хто зображений на знімку.
    options:
    - text: Хто це на фото?
      correct: true
    - text: Що це на фото?
      correct: false
    - text: Де це на фото?
      correct: false
    explanation: Питання «Хто це?» вживаємо про людей.
  - prompt: Ти запитуєш друга, чи це його мама.
    options:
    - text: Чи це твоя мама?
      correct: true
    - text: Чи це твій мама?
      correct: false
    - text: Чи це твоє мама?
      correct: false
    explanation: Мама — жіночого роду, тому вживаємо твоя.
  - prompt: Ти показуєш на брата й кажеш його ім'я.
    options:
    - text: Це мій брат. Його звати Коля.
      correct: true
    - text: Це мій брат. Її звати Коля.
      correct: false
    - text: Це мій брат. Мій звати Коля.
      correct: false
    explanation: Для чоловіка (брата) вживаємо займенник його.
  - prompt: Ти показуєш на сестру й кажеш її ім'я.
    options:
    - text: Це моя сестра. Її звати Катя.
      correct: true
    - text: Це моя сестра. Його звати Катя.
      correct: false
    - text: Це моя сестра. Їх звати Катя.
      correct: false
    explanation: Для жінки (сестри) вживаємо займенник її.
  - prompt: Ти показуєш місто на світлині.
    options:
    - text: Це моє рідне місто.
      correct: true
    - text: Це мій рідне місто.
      correct: false
    - text: Це моя рідне місто.
      correct: false
    explanation: Місто — середнього роду, тому вживаємо моє.
  - prompt: Ти запитуєш про спільні сімейні знімки.
    options:
    - text: Де твої сімейні фотографії?
      correct: true
    - text: Де твій сімейні фотографії?
      correct: false
    - text: Де твоя сімейні фотографії?
      correct: false
    explanation: Фотографії — множина, тому вживаємо твої.
- id: act-302
  type: fill-in
  title: Твій, твоя, твоє чи твої?
  instruction: Встав правильну форму займенника до кожного іменника.
  items:
  - sentence: Це ___ мама на фотографії?
    answer: твоя
    options:
    - твоя
    - твій
    - твоє
    - твої
    explanation: Мама — жіночого роду, тому твоя.
  - sentence: Ось ___ дідусь Василь.
    answer: твій
    options:
    - твій
    - твоя
    - твоє
    - твої
    explanation: Дідусь — чоловічого роду, тому твій.
  - sentence: Це ___ рідне місто?
    answer: твоє
    options:
    - твоє
    - твій
    - твоя
    - твої
    explanation: Місто — середнього роду, тому твоє.
  - sentence: Де ___ сімейні знімки?
    answer: твої
    options:
    - твої
    - твій
    - твоя
    - твоє
    explanation: Знімки — множина, тому твої.
  - sentence: Це ___ сестра Олена?
    answer: твоя
    options:
    - твоя
    - твій
    - твоє
    - твої
    explanation: Сестра — жіночого роду, тому твоя.
  - sentence: Це ___ прізвище в зошиті?
    answer: твоє
    options:
    - твоє
    - твій
    - твоя
    - твої
    explanation: Прізвище — середнього роду, тому твоє.
- id: act-303
  type: match-up
  title: Підписи до фотографій
  instruction: З'єднай підпис під фотографією з його значенням.
  pairs:
  - left: Хто це?
    right: запитання про людину на знімку
  - left: Це моя сім'я.
    right: представлення родини
  - left: Його звати Коля.
    right: ім'я брата або тата
  - left: Її звати Катя.
    right: ім'я сестри або мами
  - left: Це моє місто.
    right: назва населеного пункту
  - left: Чи це твій дідусь?
    right: уточнення про дідуся
- id: act-304
  type: true-false
  title: Слухаємо та перевіряємо
  instruction: Визнач, чи твердження є правильним згідно з правилами української мови.
  items:
  - statement: Слово «місто» середнього роду, тому правильно сказати «моє місто».
    correct: true
    explanation: Місто закінчується на -о і є іменником середнього роду.
  - statement: Форми «його» та «її» змінюються за родами іменників, як «мій» і «моя».
    correct: false
    explanation: Форми «його» та «її» в ролі присвійних слів є незмінними.
  - statement: Питання «Чи це твоя бабуся?» вимагає відповіді «так» або «ні».
    correct: true
    explanation: Частка «чи» на початку утворює загальне запитання.
  - statement: Зі словом «сестра» можна вжити займенник «твій».
    correct: false
    explanation: Сестра — жіночого роду, тому потрібно казати «твоя сестра».
  - statement: У слові «сім'я» обов'язково пишеться апостроф.
    correct: true
    explanation: Апостроф ставиться після «м» перед «я».
  - statement: Слово «батьки» вживається в множині, тому правильно казати «твої батьки».
    correct: true
    explanation: Батьки — форма множини, що узгоджується із займенником «твої».
- id: act-305
  type: odd-one-out
  title: Знайди зайве слово
  instruction: Обери одне слово, яке не підходить до групи за родом або значенням.
  items:
  - options:
    - text: мама
      correct: false
    - text: сестра
      correct: false
    - text: бабуся
      correct: false
    - text: брат
      correct: true
    explanation: Брат — чоловічого роду, а мама, сестра й бабуся — жіночого.
  - options:
    - text: тато
      correct: false
    - text: дідусь
      correct: false
    - text: син
      correct: false
    - text: дочка
      correct: true
    explanation: Дочка — жіночого роду, тоді як інші слова позначають чоловіків.
  - options:
    - text: твій
      correct: false
    - text: мій
      correct: false
    - text: наш
      correct: false
    - text: твоя
      correct: true
    explanation: Твоя — жіночого роду, тоді як інші форми — чоловічого.
  - options:
    - text: моє
      correct: false
    - text: твоє
      correct: false
    - text: місто
      correct: false
    - text: мої
      correct: true
    explanation: Мої — форма множини, а інші слова пов'язані із середнім родом.
  - options:
    - text: ім'я
      correct: false
    - text: прізвище
      correct: false
    - text: по батькові
      correct: false
    - text: зошит
      correct: true
    explanation: Зошит — навчальний предмет, а решта — складники повного імені людини.
  - options:
    - text: один
      correct: false
    - text: два
      correct: false
    - text: брат
      correct: true
    - text: дві
      correct: false
    explanation: Брат — це іменник, тоді як інші слова є числівниками.
workbook:
- id: act-w4
  type: match-up
  title: Повне ім'я як сигнал
  instruction: З'єднай частину формального імені з підказкою. Це тільки впізнавання.
  pairs:
  - left: ім'я
    right: Марія
  - left: прізвище
    right: Коваленко
  - left: по батькові
    right: Василівна
  - left: Добрий день, Маріє Василівно!
    right: формальне звертання
- id: act-w301
  type: group-sort
  title: Його чи її?
  instruction: Розподіли речення за тим, чи стосується розповідь чоловіка (його) або
    жінки (її).
  groups:
  - label: його (his)
    items:
    - Це мій брат. Його звати Богдан.
    - Це мій тато. Його звати Євген.
    - Це мій дідусь. Його родина у Львові.
    - Це мій син. Його зошит тут.
  - label: її (her)
    items:
    - Це моя сестра. Її звати Олена.
    - Це моя мама. Її звати Марина.
    - Це моя бабуся. Її звати Тетяна.
    - Це моя дочка. Її фото на столі.
- id: act-w302
  type: fill-in
  title: Родинні підписи в зошиті
  instruction: Встав правильне слово для підпису під сімейними світлинами.
  items:
  - sentence: Ось ___ родина на фотографії.
    answer: моя
    options:
    - моя
    - мій
    - моє
    - мої
    explanation: Родина — жіночого роду.
  - sentence: Це ___ дідусь і бабуся.
    answer: мої
    options:
    - мої
    - мій
    - моя
    - моє
    explanation: Дідусь і бабуся разом — множина (вони).
  - sentence: Чи це ___ брат Коля?
    answer: твій
    options:
    - твій
    - твоя
    - твоє
    - твої
    explanation: Брат — чоловічого роду.
  - sentence: Це моє рідне ___ Полтава.
    answer: місто
    options:
    - місто
    - зошит
    - батько
    - брат
    explanation: Полтава — це місто.
  - sentence: Це моя тітка. ___ звати Оксана.
    answer: Її
    options:
    - Її
    - Його
    - Він
    - Мій
    explanation: Тітка — жінка, тому вживаємо її.
  - sentence: Це мій дядько. ___ звати Тарас.
    answer: Його
    options:
    - Його
    - Її
    - Вона
    - Моя
    explanation: Дядько — чоловік, тому вживаємо його.
- id: act-w303
  type: unjumble
  title: Склади речення з фотографій
  instruction: Розстав слова у правильному порядку, щоб утворити речення.
  items:
  - scrambled:
    - моя
    - Це
    - сім'я
    - фотографії
    - на
    correct: Це моя сім'я на фотографії.
    explanation: 'Природний порядок слів: підмет, означення, обставина.'
  - scrambled:
    - є
    - тебе
    - У
    - сестра
    - чи
    - брат
    correct: У тебе є брат чи сестра?
    explanation: Питання починається зі сталого звороту «У тебе є...».
  - scrambled:
    - звати
    - Його
    - Денис
    - брат
    - мій
    - Це
    correct: Це мій брат. Його звати Денис.
    explanation: Спочатку представляємо людину, потім називаємо ім'я.
  - scrambled:
    - рідне
    - Це
    - Львів
    - моє
    - місто
    correct: Це моє рідне місто Львів.
    explanation: 'Узгодження: моє рідне місто.'
  - scrambled:
    - Тетяна
    - Її
    - Це
    - бабуся
    - моя
    - звати
    correct: Це моя бабуся. Її звати Тетяна.
    explanation: Представлення бабусі та її імені.
  - scrambled:
    - твій
    - Чи
    - це
    - на
    - дідусь
    - фото
    correct: Чи це твій дідусь на фото?
    explanation: Запитання з часткою «чи».
- id: act-w304
  type: error-correction
  title: Виправ помилки в підписах
  instruction: Знайди та виправ помилку в узгодженні або слововживанні.
  items:
  - sentence: Це мій сестра Катя.
    error: мій сестра
    correction: моя сестра
    options:
    - моя сестра
    - мій сестра
    explanation: Сестра — жіночого роду, тому потрібно казати «моя сестра».
  - sentence: Це моє батьки на знімку.
    error: моє батьки
    correction: мої батьки
    options:
    - мої батьки
    - моє батьки
    explanation: Батьки — множина, тому вживаємо «мої батьки».
  - sentence: Як її звати? Його звати Оксана.
    error: Його звати Оксана
    correction: Її звати Оксана
    options:
    - Її звати Оксана
    - Його звати Оксана
    explanation: Оксана — жіноче ім'я, тому займенник «її».
  - sentence: Це твій місто Харків?
    error: твій місто
    correction: твоє місто
    options:
    - твоє місто
    - твій місто
    explanation: Місто — середнього роду, тому «твоє місто».
  - sentence: Це моя сім'я. Її звуть Іван.
    error: Її звуть Іван
    correction: Його звати Іван
    options:
    - Його звати Іван
    - Її звуть Іван
    explanation: Іван — чоловіче ім'я, тому кажемо «його звати».
  - sentence: У тебе є брати чи сестри? У мене немає брат.
    error: У мене немає брат
    correction: Ні, у мене тільки один брат
    options:
    - Ні, у мене тільки один брат
    - У мене немає брат
    explanation: На рівні A1 уникаємо неправильних конструкцій з «немає + називний
      відмінок».
- id: act-w305
  type: translate
  title: Переклад для сімейного зошита
  instruction: Обери правильний український переклад для речення.
  items:
  - source: This is my family in the photo.
    options:
    - text: Це моя сім'я на фотографії.
      correct: true
    - text: Це мій сім'я на фотографії.
      correct: false
    - text: Це моє сім'я на фотографії.
      correct: false
    explanation: Сім'я — жіночого роду, тому моя сім'я.
  - source: Who is this?
    options:
    - text: Хто це?
      correct: true
    - text: Що це?
      correct: false
    - text: Де це?
      correct: false
    explanation: Хто запитує про людину.
  - source: His name is Kolia.
    options:
    - text: Його звати Коля.
      correct: true
    - text: Її звати Коля.
      correct: false
    - text: Моє ім'я Коля.
      correct: false
    explanation: Його вживаємо для чоловіка.
  - source: Her name is Tetiana.
    options:
    - text: Її звати Тетяна.
      correct: true
    - text: Його звати Тетяна.
      correct: false
    - text: Твоє ім'я Тетяна.
      correct: false
    explanation: Її вживаємо для жінки.
  - source: Is this your grandmother?
    options:
    - text: Чи це твоя бабуся?
      correct: true
    - text: Чи це твій бабуся?
      correct: false
    - text: Чи це твоє бабуся?
      correct: false
    explanation: Бабуся — жіночого роду, тому твоя бабуся.
  - source: This is my hometown.
    options:
    - text: Це моє рідне місто.
      correct: true
    - text: Це мій рідне місто.
      correct: false
    - text: Це моя рідне місто.
      correct: false
    explanation: Місто — середнього роду, тому моє рідне місто.
- id: act-w306
  type: quiz
  title: Офіційні дані та звертання
  instruction: Визнач правильну назву елемента офіційного імені.
  items:
  - prompt: «Оксана» в документі — це...
    options:
    - text: ім'я
      correct: true
    - text: прізвище
      correct: false
    - text: по батькові
      correct: false
    explanation: Оксана — це власне ім'я (given name).
  - prompt: «Василівна» в офіційному звертанні — це...
    options:
    - text: по батькові
      correct: true
    - text: ім'я
      correct: false
    - text: прізвище
      correct: false
    explanation: Василівна — це форма по батькові з жіночим суфіксом -івна.
  - prompt: «Коваленко» в анкеті — це...
    options:
    - text: прізвище
      correct: true
    - text: ім'я
      correct: false
    - text: по батькові
      correct: false
    explanation: Коваленко — українське прізвище.
  - prompt: Який суфікс утворює українське жіноче по батькові від імені Петро?
    options:
    - text: -івна (Петрівна)
      correct: true
    - text: -овна (Петровна)
      correct: false
    - text: -євна (Петрєвна)
      correct: false
    explanation: В українській мові вживаються суфікси -івна / -ївна, а не -овна.
  - prompt: Звертання «Добрий день, Маріє Василівно!» вказує на...
    options:
    - text: формальний, ввічливий регістр
      correct: true
    - text: неформальну розмову між дітьми
      correct: false
    - text: коротку відповідь «так/ні»
      correct: false
    explanation: Звертання на ім'я та по батькові сигналізує про ввічливе, офіційне
      спілкування.
  - prompt: У графі «Місто проживання» вказують...
    options:
    - text: населений пункт (наприклад, Київ чи Львів)
      correct: true
    - text: прізвище родини
      correct: false
    - text: вік дитини
      correct: false
    explanation: Слово «місто» означає населений пункт (city).


## vocabulary.yaml

- lemma: твоя
  translation: your, feminine informal
  pos: pronoun
  usage: Це твоя мама?
- lemma: твоє
  translation: your, neuter informal
  pos: pronoun
  usage: Це твоє прізвище?
- lemma: твої
  translation: your, plural informal
  pos: pronoun
  usage: Де твої сімейні фотографії?
- lemma: його
  translation: his / him, fixed possessive here
  pos: pronoun
  usage: Його звати Коля.
- lemma: її
  translation: her, fixed possessive here
  pos: pronoun
  usage: Її звати Катя.
- lemma: хто
  translation: who
  pos: pronoun
  usage: Хто це на фото?
- lemma: звати
  translation: to call / be named
  pos: verb
  usage: Як його звати?
- lemma: чи
  translation: or / whether in questions
  pos: conjunction
  usage: Чи це твоя бабуся?
- lemma: ім'я
  translation: given name
  pos: noun
  usage: Моє ім'я — Марко.
- lemma: прізвище
  translation: surname
  pos: noun
  usage: Моє прізвище — Коваленко.
- lemma: по батькові
  translation: patronymic
  pos: phrase
  usage: Василівна — це по батькові.
- lemma: місто
  translation: city
  pos: noun
  usage: Це моє рідне місто.


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
- title: ULP Season 1, Episode 10 — Review
  role: podcast
  source_ref: ULP Season 1, Episode 10 — Review
  url: https://www.ukrainianlessons.com/episode10/
  chunk_id: ulp-1-00-lesson-notes_l0010_w001
  notes: 'Plan reference: connected review speech about myself and my family.'
- title: Інформатика. 4 клас. Воронцова (2021)
  role: textbook
  source: Воронцова Т. В. Інформатика. 4 клас
  chunk_id: 4-klas-informatyka-vorontsova-2021_s0120
  notes: 'Підпис до сімейної фотографії: «Моя родина», ім''я, по батькові та прізвище.'
