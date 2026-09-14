{"independent_effort": "medium", "independent_model": "gpt-6-astra", "independent_reviewer": "codex-tools", "self_reviewer": "agy-tools", "writer": {"effort": "high", "model": "gemini-3.8-flash-high", "writer": "agy-tools"}}
V7 UPGRADE review of lesson 3. Review the published lesson unit, not a fresh module build. No wiki packet or plan rewrite applies. Assess preservation, lesson_split, coherent progression, first-use cumulative vocabulary, final module closure (`Підсумок модуля — Module summary` on the last lesson, not Module completion), no named narrator, marked attributed quotations with Resources entries, no ```text learner examples, and side-by-side English support for added A1 Ukrainian passages of three or more sentences. SOURCES AUDIT: VESUM/`sources` is why the Ukrainian is trustworthy (gender, government, real examples — not Russian calques). This corpus trains a Ukrainian LLM and tests whether the sources tools actually get used. No tool calls = fail. Ungrounded morphology = fail. Judge the current dimension independently using exact quotes from these artifacts. Stress annotation follows review. Lesson map:
{"lessons": [{"n": 1, "title": "Читаємо слова", "sections": ["Склади", "Голосні літери", "Читаємо слова"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}, {"n": 2, "title": "Друк, зошит, перевірка", "sections": ["Пастки читання", "Друк, зошит, перевірка"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}, {"n": 3, "title": "Далі", "sections": ["Далі"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}], "closes_module": 3, "provenance": [{"placement": "inline", "index": 0, "new_id": "act-1", "lesson": 1}, {"placement": "inline", "index": 1, "new_id": "act-2", "lesson": 1}, {"placement": "inline", "index": 2, "new_id": "act-3", "lesson": 1}, {"placement": "inline", "index": 3, "new_id": "act-4", "lesson": 2}, {"placement": "workbook", "index": 0, "new_id": "act-w1", "lesson": 1}, {"placement": "workbook", "index": 1, "new_id": "act-w2", "lesson": 1}, {"placement": "workbook", "index": 2, "new_id": "act-w3", "lesson": 2}, {"placement": "workbook", "index": 3, "new_id": "act-w4", "lesson": 2}, {"placement": "workbook", "index": 4, "new_id": "act-w5", "lesson": 3}, {"placement": "workbook", "index": 5, "new_id": "act-5", "lesson": 3}], "items_min_exempt": [{"id": "act-4", "reason": "4-item original activity preserved from baseline"}, {"id": "act-w2", "reason": "4-item original activity preserved from baseline"}, {"id": "act-w3", "reason": "4-item original activity preserved from baseline"}, {"id": "act-w4", "reason": "5-item original activity preserved from baseline"}, {"id": "act-w5", "reason": "5-item original activity preserved from baseline"}, {"id": "act-5", "reason": "3-item original activity preserved from baseline"}], "proper_names": []}
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

# Далі

У перших двох уроках ви дізналися, що голосні звуки є центром кожного складу: **ма́ма**, **молоко́**, **ву́лиця**. In the first two lessons you learned that vowel sounds are the center of every syllable: **ма́ма** (mother), **молоко́** (milk), **ву́лиця** (street). Ви також навчилися розпізнавати знак м'якшення **ь**, апостроф, йотовані літери та злиті звуки **дж** і **дз**. You also learned to recognize the soft sign **ь**, the apostrophe, iotated letters, and the fused sounds **дж** and **дз**.

Тепер ми переходимо до плавного читання цілих речень і багатоскладових слів — now we move to the smooth reading of full sentences and multi-syllable words:
- **Читати плавно від слова до речення** — read connected phrases and simple sentences smoothly;
- **Ділити багатоскладові слова на склади** — split long words into manageable syllable beats;
- **Застосовувати надійну читацьку рутину** — use a four-step decoding check before reading aloud.

## Далі

Тепер переходь до словника й вправ. You can now look at a printed Ukrainian
word, find the letters that mark vowel sounds, count the syllables, and read
the whole word more calmly.

Коли окремі склади стають знайомими, об'єднуйте їх у слова, а слова — у перші прості речення. When separate syllables become familiar, combine them into words, and words into your first simple sentences. Пам'ятайте золоте правило української фонетики: «Скільки у слові голосних звуків, стільки й складів» (quoted from: Большакова, буквар 1 клас, p. 25). Кожен склад має один голосний імпульс.

Спробуйте прочитати прості речення за складами — try reading simple sentences syllable by syllable:

| Речення | Поскладове читання | English support |
| --- | --- | --- |
| **Ма́ма чита́є.** | **Ма-ма чи-та-є.** | Mother is reading. |
| **Та́то пи́ше.** | **Та-то пи-ше.** | Father is writing. |
| **Ки́їв — столи́ця Украї́ни.** | **Ки-їв — сто-ли-ця У-кра-ї-ни.** | Kyiv is the capital of Ukraine. |
| **Ось моє́ я́блуко.** | **Ось мо-є яб-лу-ко.** | Here is my apple. |
| **Це на́ша ву́лиця.** | **Це на-ша ву-ли-ця.** | This is our street. |
| **Луна́є гарна пі́сня.** | **Лу-на-є гар-на піс-ня.** | A nice song is playing. |

<!-- INJECT_ACTIVITY: act-l3-sent-match -->

Під час читання довших слів не поспішайте й не називайте окремі літери: «Під час читання по складах не робіть пауз між літерами одного складу, а зливайте приголосний з голосним» (quoted from: Вашуленко, Українська мова 2 клас, p. 23-27). Розбийте слово на відкриті та закриті частини:

- **бі-блі-о-те-ка** — п'ять голосних звуків, п'ять складів (бібліоте́ка);
- **у-ні-вер-си-тет** — п'ять голосних звуків, п'ять складів (університе́т);
- **фо-то-гра-фі-я** — п'ять голосних звуків, п'ять складів (фотогра́фія);
- **шо-ко-лад** — три голосні звуки, три склади (шокола́д).

Якщо ви сумніваєтеся в кількості складів, скористайтеся простим тілесним тестом: «Покладіть долоню під підборіддя: кожен дотик — це один голосний звук і один склад» (quoted from: Кравцова, Українська мова 2 клас, p. 13).

<!-- INJECT_ACTIVITY: act-l3-syllables-count -->

<!-- INJECT_ACTIVITY: act-l3-divide -->

Послухайте розмову двох учнів про читання нових слів і речень — listen to a conversation between two learners about reading new words and sentences:

> Олена: Що ти читаєш? (What are you reading?)
> Тарас: Я читаю нове слово. (I am reading a new word.)
> Олена: Яке це слово? (What word is it?)
> Тарас: «Університет». Тут п'ять складів! ("University". Five syllables here!)
> Олена: Чудово! А речення можеш прочитати? (Great! And can you read a sentence?)
> Тарас: Так: «Київ — красива столиця». (Yes: "Kyiv is a beautiful capital".)
> Олена: Молодець, читаєш дуже чисто й плавно! (Well done, you read very purely and smoothly!)

Розбір реплік розмови — breakdown of lines:

| Українська | English support |
| --- | --- |
| **Що ти читаєш?** | What are you reading? |
| **Я читаю нове слово.** | I am reading a new word. |
| **Яке це слово?** | What word is it? |
| **«Університет». Тут п'ять складів!** | "University". Five syllables here! |
| **Чудово! А речення можеш прочитати?** | Great! And can you read a sentence? |
| **Так: «Київ — красива столиця».** | Yes: "Kyiv is a beautiful capital". |
| **Молодець, читаєш дуже чисто й плавно!** | Well done, you read very purely and smoothly! |

<!-- INJECT_ACTIVITY: act-l3-quiz -->

Перед тим як читати будь-який новий текст уголос — before reading any new text aloud, apply this four-step self-check routine:

1. **Голосні звуки** — find all letters marking vowel sounds.
2. **Кількість складів** — count the syllables (as many syllables as vowel sounds).
3. **Особливі знаки** — notice **ь**, apostrophe, **ї**, **дж**, or **дз**.
4. **Плавне злиття** — read word by word in syllables, then smooth into a phrase.

<!-- INJECT_ACTIVITY: act-l3-tf -->

### Підсумок модуля — Module summary

Підіб'ємо підсумки всього модуля — module summary:
- **Рахувати склади за голосними звуками** — count syllables accurately by identifying vowel sounds in any Ukrainian word;
- **Читати відкриті та закриті склади** — smoothly blend consonants and vowels into open and closed syllables without letter-by-letter spelling;
- **Розрізняти всі 10 голосних літер** — read the six simple vowels (**а, о, у, е, и, і**) and know what iotated vowels (**я, ю, є, ї**) do in different positions;
- **Уникати типових читацьких пасток** — keep unstressed **о** pure, pronounce **дж** and **дз** as single fused sounds, and correctly decode the soft sign **ь** and apostrophe;
- **Читати багатоскладові слова та перші речення** — break down long words into syllables and read connected Ukrainian sentences with natural cadence;
- **З'єднувати друк і зошит** — recognize printed vocabulary in handwritten notebook forms before copying or writing.

Вітаємо з успішним завершенням модуля! — Congratulations on successfully completing the module! Тепер ви володієте надійним читацьким інструментом і можете впевнено переходити до наступних кроків у вивченні української мови. — Now you have a reliable reading tool and can confidently take your next steps in Ukrainian.


## activities.yaml

inline:
- id: act-l3-sent-match
  type: match-up
  title: З'єднай речення з перекладом
  instruction: З'єднай просте українське речення з його англійським перекладом.
  pairs:
  - left: Ма́ма чита́є.
    right: Mother is reading.
  - left: Та́то пи́ше.
    right: Father is writing.
  - left: Ки́їв — столи́ця Украї́ни.
    right: Kyiv is the capital of Ukraine.
  - left: Ось моє́ я́блуко.
    right: Here is my apple.
  - left: Це на́ша ву́лиця.
    right: This is our street.
  - left: Луна́є гарна пі́сня.
    right: A nice song is playing.
- id: act-l3-syllables-count
  type: count-syllables
  title: Порахуй склади у довгих словах
  instruction: Порахуй голосні звуки та визнач кількість складів.
  maxCount: 6
  items:
  - word: бібліоте́ка
    correct: 5
  - word: університе́т
    correct: 5
  - word: фотогра́фія
    correct: 5
  - word: шокола́д
    correct: 3
  - word: абе́тка
    correct: 3
  - word: ре́чення
    correct: 3
- id: act-l3-divide
  type: divide-words
  title: Поділи слова на склади
  instruction: Поділи кожне слово на склади за голосними звуками.
  items:
  - word: кни́га
    answer: кни га
  - word: шокола́д
    answer: шо ко лад
  - word: абе́тка
    answer: а бе тка
  - word: столи́ця
    answer: сто ли ця
  - word: пі́сня
    answer: піс ня
  - word: джерело́
    answer: дже ре ло
- id: act-l3-quiz
  type: quiz
  title: Правила та кроки читання
  instruction: Обери правильну відповідь про читання слів і речень.
  items:
  - prompt: З чого починається читання незнайомого слова?
    options:
    - text: З пошуку голосних звуків і поділу на склади
      correct: true
    - text: З читання кожної окремої літери поспіль
      correct: false
    - text: З запам'ятовування форми слова без читання
      correct: false
    explanation: Голосні звуки визначають кількість складів і допомагають прочитати
      слово плавно.
  - prompt: Скільки складів у слові «університет»?
    options:
    - text: '5'
      correct: true
    - text: '4'
      correct: false
    - text: '6'
      correct: false
    explanation: У слові «університет» п'ять голосних звуків (у, і, е, и, е), тому
      п'ять складів.
  - prompt: Як правильно прочитати речення «Мама читає»?
    options:
    - text: Прочитати кожне слово по складах і з'єднати у фразу
      correct: true
    - text: Назвати окремо кожну літеру кожного слова
      correct: false
    - text: Пропустити голосні звуки
      correct: false
    explanation: Читання по складах допомагає об'єднати звуки у плавне осмислене речення.
  - prompt: Що допомагає перевірити кількість складів під час вимови?
    options:
    - text: Долоня під підборіддям на кожному голосному поштовху
      correct: true
    - text: Рахування приголосних літер
      correct: false
    - text: Закривання очей під час мовлення
      correct: false
    explanation: Кожен дотик підборіддя до долоні відповідає одному голосному звуку
      і складу.
  - prompt: Яке слово складається з трьох відкритих складів?
    options:
    - text: молоко
      correct: true
    - text: день
      correct: false
    - text: Львів
      correct: false
    explanation: 'Слово «молоко» має три відкриті склади: мо-ло-ко.'
  - prompt: Як читаємо речення з літерою «ї» в слові «Україна»?
    options:
    - text: Чітко вимовляємо [йі] у складі «ї»
      correct: true
    - text: Читаємо як просте [і]
      correct: false
    - text: Пропускаємо цю літеру
      correct: false
    explanation: Літера Ї завжди позначає два звуки [йі].
- id: act-l3-tf
  type: true-false
  title: Факти про плавне читання
  instruction: Визнач, чи є твердження правильним.
  items:
  - statement: У слові рівно стільки складів, скільки в ньому голосних звуків.
    correct: true
    explanation: Це основне правило українського складоподілу.
  - statement: Приголосний звук сам по собі може утворити склад.
    correct: false
    explanation: Приголосний звук без голосного не утворює складу.
  - statement: Довгі слова легше читати, якщо спочатку розбити їх на склади.
    correct: true
    explanation: Поскладове читання запобігає помилкам у багатоскладових словах.
  - statement: Під час читання речення слова слід об'єднувати у плавний потік.
    correct: true
    explanation: Плавне інтонування робить мовлення природним і зрозумілим.
  - statement: Слово «бібліотека» має три склади.
    correct: false
    explanation: 'Слово «бібліотека» має п''ять голосних і п''ять складів: бі-блі-о-те-ка.'
  - statement: Тест із долонею під підборіддям показує кожен голосний імпульс.
    correct: true
    explanation: Опускання щелепи відбувається на кожному відкритому голосному звуці.
workbook:
- id: act-w5
  type: watch-and-repeat
  title: Повтор голосних
  instruction: Подивися огляд абетки ще раз, потім повтори прості голосні.
  items:
  - letter: А
    sound: '[а]'
    word: ма́ма
    video: https://www.youtube.com/watch?v=ksXIXj7CXwc
  - letter: О
    sound: '[о]'
    word: молоко́
    video: https://www.youtube.com/watch?v=ksXIXj7CXwc
  - letter: У
    sound: '[у]'
    word: ву́лиця
    video: https://www.youtube.com/watch?v=ksXIXj7CXwc
  - letter: И
    sound: '[и]'
    word: ми
    video: https://www.youtube.com/watch?v=ksXIXj7CXwc
  - letter: І
    sound: '[і]'
    word: пі́сня
    video: https://www.youtube.com/watch?v=ksXIXj7CXwc
- id: act-5
  type: quiz
  title: Мініперевірка читання
  instruction: Обери правильну відповідь.
  items:
  - prompt: Склад — що це?
    options:
    - text: лі́тера
      correct: false
    - text: syllable
      correct: true
    - text: greeting
      correct: false
    explanation: Склад — це частина слова з голосним звуком.
  - prompt: Молоко́ — скільки складів?
    options:
    - text: '2'
      correct: false
    - text: '3'
      correct: true
    - text: '1'
      correct: false
    explanation: Молоко́ має три голосні звуки й три склади́.
  - prompt: Яка літера завжди [йі]?
    options:
    - text: І
      correct: false
    - text: И
      correct: false
    - text: Ї
      correct: true
    explanation: Ї завжди читаємо як [йі].
- id: act-l3-wb-odd
  type: odd-one-out
  title: Зайве слово за кількістю складів
  instruction: Знайди слово, яке відрізняється кількістю складів від решти слів у
    рядку.
  items:
  - words:
    - ма́ма
    - та́то
    - ка́ша
    - день
    answer: день
    explanation: День має один склад, тоді як інші слова мають два склади.
  - words:
    - молоко́
    - ву́лиця
    - столи́ця
    - Ки́їв
    answer: Ки́їв
    explanation: Київ має два склади, а інші слова мають по три склади.
  - words:
    - університе́т
    - бібліоте́ка
    - фотогра́фія
    - ка́ша
    answer: ка́ша
    explanation: Каша має два склади, а інші слова мають по п'ять складів.
  - words:
    - Львів
    - сон
    - ліс
    - вода́
    answer: вода́
    explanation: Вода має два склади, а слова Львів, сон і ліс — односкладові.
  - words:
    - люди́на
    - апте́ка
    - пі́сня
    - маши́на
    answer: пі́сня
    explanation: Пісня має два склади, а людина, аптека і машина — трискладові слова.
  - words:
    - так
    - ні
    - дім
    - та́то
    answer: та́то
    explanation: Тато має два склади, а інші слова мають лише один склад.
- id: act-l3-wb-sort
  type: group-sort
  title: Групування слів за кількістю складів
  instruction: Розподіли слова за кількістю складів.
  groups:
  - label: Один склад
    items:
    - день
    - Львів
    - хліб
  - label: Два склади
    items:
    - ма́ма
    - та́то
    - ка́ша
  - label: Три склади
    items:
    - молоко́
    - ву́лиця
    - столи́ця
- id: act-l3-wb-fill
  type: fill-in
  title: Встав пропущене слово в речення
  instruction: Заповни пропуск відповідним словом, яке підходить за змістом.
  items:
  - sentence: Ки́їв — це головна {столи́ця} Украї́ни.
    options:
    - столи́ця
    - ка́ша
    - пі́сня
    explanation: Київ є столицею України.
  - sentence: У сло́ві {молоко́} три відкриті склади.
    options:
    - молоко́
    - день
    - Львів
    explanation: 'Молоко має три склади: мо-ло-ко.'
  - sentence: Ма́ма чита́є чудове {сло́во} у книзі.
    options:
    - сло́во
    - ка́ша
    - так
    explanation: Мама читає слово.
  - sentence: На столі лежить свіже соковите {я́блуко}.
    options:
    - я́блуко
    - ву́лиця
    - абе́тка
    explanation: Яблуко лежить на столі.
  - sentence: Це наша рідна міська {ву́лиця}.
    options:
    - ву́лиця
    - молоко́
    - ні
    explanation: Вулиця — назва міського шляху.
  - sentence: З радіо лунає гарна українська {пі́сня}.
    options:
    - пі́сня
    - та́то
    - день
    explanation: Пісня лунає з радіо.
- id: act-l3-wb-match
  type: match-up
  title: З'єднай слово з моделлю читання
  instruction: З'єднай слово з його поскладовою моделлю читання.
  pairs:
  - left: ка́ша
    right: два склади (ка-ша)
  - left: молоко́
    right: три відкриті склади (мо-ло-ко)
  - left: люди́на
    right: три склади з йотованою ю (лю-ди-на)
  - left: університе́т
    right: п'ять складів (у-ні-вер-си-тет)
  - left: день
    right: один склад із м'яким знаком (день)
  - left: я́блуко
    right: три склади, я позначає [йа] (яб-лу-ко)
- id: act-l3-wb-translate
  type: translate
  title: Читаємо та розуміємо слова
  instruction: Прочитай українське слово та обери правильний переклад.
  items:
  - source: столи́ця
    target: capital
    options:
    - capital
    - street
    - city
    - country
    explanation: Столиця означає capital.
  - source: люди́на
    target: person
    options:
    - person
    - people
    - teacher
    - student
    explanation: Людина перекладається як person.
  - source: ву́лиця
    target: street
    options:
    - street
    - house
    - room
    - city
    explanation: Вулиця означає street.
  - source: я́блуко
    target: apple
    options:
    - apple
    - bread
    - milk
    - water
    explanation: Яблуко перекладається як apple.
  - source: пі́сня
    target: song
    options:
    - song
    - story
    - book
    - letter
    explanation: Пісня означає song.
  - source: абе́тка
    target: alphabet
    options:
    - alphabet
    - word
    - sound
    - syllable
    explanation: Абетка перекладається як alphabet.


## vocabulary.yaml

- lemma: склад
  translation: syllable
  pos: noun
  usage: У сло́ві ма́ма два склади́.
- lemma: голосни́й звук
  translation: vowel sound
  pos: noun phrase
  usage: А - голосни́й звук.
- lemma: при́голосний звук
  translation: consonant sound
  pos: noun phrase
  usage: М - при́голосний звук.
- lemma: чита́ти
  translation: to read
  pos: verb
  usage: Я чита́ю сло́во.
- lemma: писа́ти
  translation: to write
  pos: verb
  usage: Я пишу́ лі́теру.
- lemma: ма́ма
  translation: mother
  pos: noun
  usage: Ма́ма.
- lemma: та́то
  translation: father
  pos: noun
  usage: Та́то.
- lemma: молоко́
  translation: milk
  pos: noun
  usage: Молоко́.
- lemma: я́блуко
  translation: apple
  pos: noun
  usage: Я́блуко.
- lemma: люди́на
  translation: person
  pos: noun
  usage: Люди́на.
- lemma: ву́лиця
  translation: street
  pos: noun
  usage: Ву́лиця.
- lemma: столи́ця
  translation: capital
  pos: noun
  usage: Ки́їв - столи́ця Украї́ни.
- lemma: день
  translation: day
  pos: noun
  usage: День.
- lemma: абе́тка
  translation: alphabet
  pos: noun
  usage: Украї́нська абе́тка.


## resources.yaml

- title: Большакова, буквар 1 клас, p. 25
  role: textbook
  source: Большакова, буквар 1 клас, p. 25
  notes: 'Plan reference: syllable rule; every syllable has a vowel sound.'
- title: Вашуленко, Українська мова 2 клас, p. 23-27
  role: textbook
  source: Вашуленко, Українська мова 2 клас, p. 23-27
  notes: 'Plan reference: transfer, stress, and iotated-vowel reading context.'
- title: Кравцова, Українська мова 2 клас, p. 13
  role: textbook
  source: Кравцова, Українська мова 2 клас, p. 13
  notes: 'Plan reference: hand-under-chin syllable counting check.'
- title: Anna Ohoiko — Ukrainian alphabet overview
  role: youtube
  url: https://www.youtube.com/watch?v=ksXIXj7CXwc
  channel: Ukrainian Lessons
  notes: Supplemental listening support for the vowel reading pass.
