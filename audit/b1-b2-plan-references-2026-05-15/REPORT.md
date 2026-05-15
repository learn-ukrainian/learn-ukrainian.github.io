# B1 + B2 plan_references audit

Generated: 2026-05-15

## Summary

- Plans audited: **187**
  - B1: 94
  - B2: 93
- Paged citations extracted: **275**
- By failure mode:
  - OK: 151
  - GHOST_SOURCE: 0
  - GHOST_PAGE: 0
  - TOPIC_MISMATCH: 47
  - LEVEL_MISMATCH: 6
  - UNKNOWN_AUTHOR: 71
- LEVEL_MISMATCH thresholds (grade >= threshold flags):
  - B1: Grade >= 11
  - B2: Grade >= 11

Failure modes are reported separately: a single citation may be both TOPIC_MISMATCH and LEVEL_MISMATCH; the audit assigns the strictest (TOPIC_MISMATCH first), and LEVEL_MISMATCH is listed alongside in the aggregate findings.

## B1 — broken citations

### adjectives-comparative

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 6, p.198` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-litvinova-2023) |  |
| `Авраменко Grade 11, p.29` | LEVEL_MISMATCH | B1 plan cites Grade 11 textbook (threshold: Grade >= 11)<br>chunk title: _Сторінка 20_ | verify pedagogical level fit; verify Grade 11 content is genuinely B1-appropriate |

### adjectives-superlative

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 6, p.198` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-litvinova-2023) |  |
| `Авраменко Grade 11, p.29` | TOPIC_MISMATCH | chunk title 'Сторінка 20'; only 0 shared content stems with plan topic<br>chunk text (first 300 chars): _"3. Прочитайте речення та визначте в них тропи й риторичні фігури (усно). 1. Нараз за стосами ящиків щось зашаруділо, зашурхотіло, задзвеніло, задеренчало скло,  і з вузького проходу з’явився молодик з дженджуристою борідкою та довгим волоссям  (М. Стельмах). 2. Верни до мене, пам’яте моя! (В. Стус)."_ | verify topic relevance; drop or replace with on-topic page |

### advanced-pronouns

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 6, p.269` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-litvinova-2023) |  |

### adverbs-comparison-formation

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 7, p.141` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |
| `Авраменко Grade 7, p.137` | TOPIC_MISMATCH | chunk title 'Сторінка 123'; only 0 shared content stems with plan topic<br>chunk text (first 300 chars): _"120 МОРФОЛОГІЯ.  ОРФОГРАФІЯ 4.	 Виконайте завдання в тестовій формі. 	 Прочитайте речення. За повір’ям, зима(1) зустрівшись із весною(2) відступала, тому  слов’я­ни виконували закличні пісні — веснянки. Господарі ж починали  працювати(3) не покладаючи рук, щоб потім жити(4) не журячись. 	 	 Коми тре"_ | verify topic relevance; drop or replace with on-topic page |

### alternation-consonants-nouns

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Заболотний Grade 5, p.116` | TOPIC_MISMATCH | chunk title 'Сторінка 118'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"115 Дайте, будь ласка, три квитки до ... . Харків Миколаїв Канів Львів Тетіїв Чугуїв  Фастів Бориспіль ЗРАЗОК. Дайте, будь ласка, три квитки до Бердичева. 280.	І. Спишіть слова, уставляючи на місці пропуску букву е або и. По- ясніть орфограми, покликаючись на правила написання е, и в коренях  слів т"_ | verify topic relevance; drop or replace with on-topic page |
| `Литвінова Grade 6, p.159` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-litvinova-2023) |  |

### alternation-vowels

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 5, p.118` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 5-klas-ukrmova-litvinova-2022) |  |
| `Глазова Grade 10, p.103` | TOPIC_MISMATCH | chunk title 'Сторінка 72'; only 1 shared content stems with plan topic<br>chunk text (first 300 chars): _"4. Мохна- тий джміль із будяків ч..рвоних сп..ває мед (М. Рильський). 5. В..слуємо. А із в..сла в..селка зводиться в..села. За селами сипнули села, мов квіту  річка нан..сла (О. Довгий). Позначте в  словах вивчені орфограми."_ | verify topic relevance; drop or replace with on-topic page |

### aspect-future-tense

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 7, p.44` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |

### aspect-in-conditionals

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Заболотний Grade 7, p.92` | TOPIC_MISMATCH | chunk title 'Сторінка 93'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"89 89 І. Прочитайте речення. Доведіть, що виділені слова – дієприкметники. Ви- значте їхній рід і число.  1. І шепче щось мені на  вухо налита росами земля  (Г. Коваль). 2. І сходить  сонце, скупане в росі, і спіє день, і веселить світа- нок (Л. Завіщана). 3. Аж до самого небо схилу розляглося за- с"_ | verify topic relevance; drop or replace with on-topic page |
| `Литвінова Grade 7, p.88` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |

### aspect-in-imperatives

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 7, p.82` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |
| `Авраменко Grade 7, p.80` | TOPIC_MISMATCH | chunk title 'Сторінка 72'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"69 § 31.  Майбутній  час  дієслів Б.	 Створіть невеликий роздум, підтримавши або спростувавши думку, ви- словлену в одному із записаних прислів’їв. Наведіть доказ, підкріпіть  його прикладом із життя або художнього твору (усно).  6.	 Прочитайте текст, передайте його зміст двома-трьома реченнями (усн"_ | verify topic relevance; drop or replace with on-topic page |

### aspect-in-narration

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 7, p.30` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |

### aspect-in-negation

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 7, p.36` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |

### aspect-past-tense

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 7, p.30` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |

### b1-baseline-future-aspect

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 7, p.30` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |
| `Литвінова Grade 7, p.48` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |

### b1-baseline-past-present

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 7, p.30` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |

### cases-with-ordinal-numerals

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 6, p.237` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-litvinova-2023) |  |
| `Авраменко Grade 11, p.42` | TOPIC_MISMATCH | chunk title 'Сторінка 29'; only 1 shared content stems with plan topic<br>chunk text (first 300 chars): _"Також не можна утворювати ступені порівняння прикметників, що перейшли з від- носних або присвійних у якісні: вовчий (характер), золоті (руки), каштанове (волосся). Різний ступінь ознаки прикметника виражають також за допомогою прислівників  дуже, вельми, занадто, мало, украй, зовсім, особливо, трох"_ | verify topic relevance; drop or replace with on-topic page |
| `Авраменко Grade 11, p.37` | TOPIC_MISMATCH | chunk title 'Сторінка 25'; only 1 shared content stems with plan topic<br>chunk text (first 300 chars): _"Потрібно бути дуже  сміливою людиною, щоб з тріском провалюватися. Тільки клоуни по-справжньому щасливі. Іноді потрібно робити неправильні речі в правильний час, і правиль- ні речі — у неправильний. Не піддавайтеся відчаю. Це наркотик, який робить з людиною най- страшніше: він робить її байдужою (Ч."_ | verify topic relevance; drop or replace with on-topic page |

### cases-with-quantity-expressions

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 6, p.240` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-litvinova-2023) |  |
| `Голуб Grade 6, p.163` | UNKNOWN_AUTHOR | add 'Голуб': ['golub'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-golub-2023) |  |
| `Авраменко Grade 11, p.37` | TOPIC_MISMATCH | chunk title 'Сторінка 25'; only 1 shared content stems with plan topic<br>chunk text (first 300 chars): _"Потрібно бути дуже  сміливою людиною, щоб з тріском провалюватися. Тільки клоуни по-справжньому щасливі. Іноді потрібно робити неправильні речі в правильний час, і правиль- ні речі — у неправильний. Не піддавайтеся відчаю. Це наркотик, який робить з людиною най- страшніше: він робить її байдужою (Ч."_ | verify topic relevance; drop or replace with on-topic page |

### checkpoint-aspect

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 7, p.30` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |
| `Литвінова Grade 7, p.44` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |

### complex-compound

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Ворон Grade 9, p.38` | UNKNOWN_AUTHOR | unknown author 'Ворон'; verify against data/sources.db |  |
| `Авраменко Grade 8, p.52` | TOPIC_MISMATCH | chunk title 'Сторінка 46'; only 1 shared content stems with plan topic<br>chunk text (first 300 chars): _"Хоча в середовищі  професійних художників частіше послуговуються словом писати. Між іншим, рисува- ти не росіянізм, це слово означає «відтворювати на площині лінійні образи зображува- них предметів, робити їхній контурний рисунок». Наприклад: Пастельні барви Івана Марчука додають спокою і легкості. "_ | verify topic relevance; drop or replace with on-topic page |
| `Авраменко Grade 7, p.161` | TOPIC_MISMATCH | chunk title 'Сторінка 146'; only 1 shared content stems with plan topic<br>chunk text (first 300 chars): _"143 § 65.  Букви  и  та  і  в  кінці  прислівників 4.	 Виконайте завдання в тестовій формі. 1. Букву і треба писати в кінці кожного прислівника у варіанті А	 год.. , непереливк.. Б	 нахильц.. , подумк..  В	 по-латин.. , поноч.. Г	 вповн.. , самотужк.. 2. Букву и треба писати в кінці кожного прислі"_ | verify topic relevance; drop or replace with on-topic page |

### complex-subordinate-concess

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Ворон Grade 9, p.80` | UNKNOWN_AUTHOR | unknown author 'Ворон'; verify against data/sources.db |  |

### complex-subordinate-condition

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Авраменко Grade 8, p.86` | TOPIC_MISMATCH | chunk title 'Сторінка 70'; only 0 shared content stems with plan topic<br>chunk text (first 300 chars): _"69 § 29–30. Означення 9. Прочитайте текст і виконайте завдання. У нашому житті дуже багато свят, неодмінним атрибутом яких є подарунки. Скажі- мо, на Великдень заведено дарувати писанки та крашанки, на Новий рік і Різдво — цу- керки, невеличкі корисні речі. Однак є і такі подарунки, що не вимагають "_ | verify topic relevance; drop or replace with on-topic page |
| `Ворон Grade 9, p.80` | UNKNOWN_AUTHOR | unknown author 'Ворон'; verify against data/sources.db |  |

### complex-subordinate-object

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Ворон Grade 9, p.57` | UNKNOWN_AUTHOR | unknown author 'Ворон'; verify against data/sources.db |  |

### complex-subordinate-purpose

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Ворон Grade 9, p.80` | UNKNOWN_AUTHOR | unknown author 'Ворон'; verify against data/sources.db |  |

### complex-subordinate-reason

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Авраменко Grade 8, p.86` | TOPIC_MISMATCH | chunk title 'Сторінка 70'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"69 § 29–30. Означення 9. Прочитайте текст і виконайте завдання. У нашому житті дуже багато свят, неодмінним атрибутом яких є подарунки. Скажі- мо, на Великдень заведено дарувати писанки та крашанки, на Новий рік і Різдво — цу- керки, невеличкі корисні речі. Однак є і такі подарунки, що не вимагають "_ | verify topic relevance; drop or replace with on-topic page |
| `Ворон Grade 9, p.80` | UNKNOWN_AUTHOR | unknown author 'Ворон'; verify against data/sources.db |  |

### complex-subordinate-relative

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Ворон Grade 9, p.57` | UNKNOWN_AUTHOR | unknown author 'Ворон'; verify against data/sources.db |  |
| `Авраменко Grade 7, p.176` | TOPIC_MISMATCH | chunk title 'Сторінка 160'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"157 § 71–72.  Наголошування   прислівників 9.	 На основі вивчених прислівників (з § 59–60 по § 71–72) укладіть міні­ словник наголосів (за зразком). Оформіть у лепбук1. Зразок     А                          Б                        В                            Г                      Д абияк         "_ | verify topic relevance; drop or replace with on-topic page |

### complex-subordinate-time

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Ворон Grade 9, p.80` | UNKNOWN_AUTHOR | unknown author 'Ворон'; verify against data/sources.db |  |
| `Авраменко Grade 8, p.86` | TOPIC_MISMATCH | chunk title 'Сторінка 70'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"69 § 29–30. Означення 9. Прочитайте текст і виконайте завдання. У нашому житті дуже багато свят, неодмінним атрибутом яких є подарунки. Скажі- мо, на Великдень заведено дарувати писанки та крашанки, на Новий рік і Різдво — цу- керки, невеличкі корисні речі. Однак є і такі подарунки, що не вимагають "_ | verify topic relevance; drop or replace with on-topic page |

### conditionals-real

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 7, p.36` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |

### conditionals-unreal

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 7, p.61` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |

### daily-life-and-routines

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Вашуленко Grade 2, p.81` | TOPIC_MISMATCH | chunk title 'Сторінка 83'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"23 серпня в Україні відзначають День Державного  Прапора. А ти знаєш? Роз’єднай слова і прочитай прислів’я. БЕЗВЕРБИІКАЛИНИНЕМАУКРАЇНИ. Вбратися, плахту, прикрасити, відоб­раже­нням,  стрічками, задивляючись, усміхаючись, перетворилися,  торкаючись. Прочитай правильно Народна творчість ЯК ОКСАНА ВЕР"_ | verify topic relevance; drop or replace with on-topic page |
| `Голуб Grade 5, p.100` | UNKNOWN_AUTHOR | add 'Голуб': ['golub'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 5-klas-ukrmova-golub-2022) |  |
| `Голуб Grade 6, p.197` | UNKNOWN_AUTHOR | add 'Голуб': ['golub'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-golub-2023) |  |

### dative-nuances

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Авраменко Grade 7, p.60` | TOPIC_MISMATCH | chunk title 'Сторінка 54'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"51 § 23. Форми  дієслова 3. Прочитайте деформований текст і виконайте завдання. На нашому південному морі дуже мало островів. Це все невеличкі, пі- щані, іноді болотисті, (порости) травами, очеретами або кущами шматки  ґрунту, (одрізати) від суходолу неширокими протоками. До цих островів  (належати)"_ | verify topic relevance; drop or replace with on-topic page |

### gerund-phrases

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Заболотний Grade 8, p.205` | TOPIC_MISMATCH | chunk title 'Сторінка 173'; only 0 shared content stems with plan topic<br>chunk text (first 300 chars): _"Á	Міський транспорт перевозить пасажирів і школярів. В	Нагородили юристів, учителів, економістів, лікарів. Ã	 Купили канцелярські товари: ручки, ножиці, лампи."_ | verify topic relevance; drop or replace with on-topic page |
| `Литвінова Grade 7, p.114` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |

### introductory-words

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Авраменко Grade 11, p.109` | LEVEL_MISMATCH | B1 plan cites Grade 11 textbook (threshold: Grade >= 11)<br>chunk title: _Сторінка 81_ | verify pedagogical level fit; verify Grade 11 content is genuinely B1-appropriate |

### motion-base-review

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Вашуленко Grade 2, p.80` | TOPIC_MISMATCH | chunk title 'Сторінка 82'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"Підготуйтеся і проспівайте вірш під музику. Передайте  у співі свою любов до рідного краю.  До вірша Наталі Рибальської композитор  Микола  Ведмедеря  написав  музику.  Перегляньте відео і послухайте музику. Які слова — назви чисел «заховалися» у прочитаних  словах? РОДИНА      ВІДВАГА      ТРИЗУБ "_ | verify topic relevance; drop or replace with on-topic page |

### motion-flight-swim

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Авраменко Grade 10, p.19` | TOPIC_MISMATCH | chunk title 'Сторінка 15'; only 1 shared content stems with plan topic<br>chunk text (first 300 chars): _"Однак є люди, які повинні бути більш уважними до свого мовлення  (актори, лектори, диктори й інші працівники радіо та телебачення, учителі, викладачі), а гро- мадськість має право бути більш вимогливою до них, бо їхнє слово повинне бути взірцем для  решти громадян України. Носіями зразкової українсь"_ | verify topic relevance; drop or replace with on-topic page |
| `Вашуленко Grade 2, p.80` | TOPIC_MISMATCH | chunk title 'Сторінка 82'; only 0 shared content stems with plan topic<br>chunk text (first 300 chars): _"Підготуйтеся і проспівайте вірш під музику. Передайте  у співі свою любов до рідного краю.  До вірша Наталі Рибальської композитор  Микола  Ведмедеря  написав  музику.  Перегляньте відео і послухайте музику. Які слова — назви чисел «заховалися» у прочитаних  словах? РОДИНА      ВІДВАГА      ТРИЗУБ "_ | verify topic relevance; drop or replace with on-topic page |

### motion-prefixes-arrival

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 6, p.54` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-litvinova-2023) |  |

### motion-prefixes-in-out

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Авраменко Grade 5, p.63` | TOPIC_MISMATCH | chunk title 'Сторінка 61'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"61  § 24.  Корінь  слова.  Спільнокореневі  слова  та  форми  слова 4.	Виконайте завдання в тестовій формі.  1.	 Форми того самого слова записано у варіанті А зелень, зелено, зелений Б вісім, восьми, вісьмома  В мова, мовний, мовити Г літо, літній, літечко 2.	 Спільнокореневими є всі слова, ОКРІМ А "_ | verify topic relevance; drop or replace with on-topic page |

### motion-prefixes-transit

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Голуб Grade 6, p.31` | UNKNOWN_AUTHOR | add 'Голуб': ['golub'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-golub-2023) |  |

### narrative-mastery

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Варзацька Grade 4, p.14` | UNKNOWN_AUTHOR | add 'Варзацька': ['varzatska'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 4-klas-ukrayinska-mova-varzatska-2021-1) |  |
| `Заболотний Grade 5, p.134` | TOPIC_MISMATCH | chunk title 'Сторінка 136'; only 1 shared content stems with plan topic<br>chunk text (first 300 chars): _"133 322.	А.  Знайдіть на упаковках слова зі сполученнями букв йо, ьо. Б.  Вимовте чітко знайдені слова, поділяючи їх на склади. Яке сполу- чення (йо чи ьо) може самé бути складом? В.  Простежте, яке сполучення (йо чи ьо) може бути на початку складу,  а яке – у кінці чи в середині складу. Пишемо ЙО П"_ | verify topic relevance; drop or replace with on-topic page |

### nature-and-environment

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Болшакова Grade 2, p.63` | UNKNOWN_AUTHOR | unknown author 'Болшакова'; verify against data/sources.db |  |

### noun-subclasses-feminine

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Авраменко Grade 10, p.168` | TOPIC_MISMATCH | chunk title 'Сторінка 113'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"113 Уживання великої літери СПОСТЕРЕЖЕННЯ 1. Поміркуйте, у яких випадках загальна назва полуничка може стати власною, а отже, її тре- ба буде писати з великої літери в лапках («Полуничка») або без них (Полуничка). З великої літери треба писати імена людей, по батькові, псевдоніми  та клички тварин К"_ | verify topic relevance; drop or replace with on-topic page |
| `Голуб Grade 6, p.82` | UNKNOWN_AUTHOR | add 'Голуб': ['golub'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-golub-2023) |  |

### noun-subclasses-hissing

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Голуб Grade 6, p.75` | UNKNOWN_AUTHOR | add 'Голуб': ['golub'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-golub-2023) |  |

### noun-subclasses-masculine

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 6, p.159` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-litvinova-2023) |  |
| `Литвінова Grade 6, p.160` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-litvinova-2023) |  |

### participle-phrases

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 7, p.82` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |
| `Заболотний Grade 8, p.205` | TOPIC_MISMATCH | chunk title 'Сторінка 173'; only 1 shared content stems with plan topic<br>chunk text (first 300 chars): _"Á	Міський транспорт перевозить пасажирів і школярів. В	Нагородили юристів, учителів, економістів, лікарів. Ã	 Купили канцелярські товари: ручки, ножиці, лампи."_ | verify topic relevance; drop or replace with on-topic page |

### participles-active

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 7, p.82` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |
| `Авраменко Grade 7, p.95` | TOPIC_MISMATCH | chunk title 'Сторінка 86'; only 1 shared content stems with plan topic<br>chunk text (first 300 chars): _"Б. Надпишіть особу й число над дієсловами наказового способу. рівнина свердло русло"_ | verify topic relevance; drop or replace with on-topic page |
| `Авраменко Grade 11, p.58` | LEVEL_MISMATCH | B1 plan cites Grade 11 textbook (threshold: Grade >= 11)<br>chunk title: _Сторінка 42_ | verify pedagogical level fit; verify Grade 11 content is genuinely B1-appropriate |

### participles-passive

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 7, p.87` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |
| `Заболотний Grade 7, p.189` | TOPIC_MISMATCH | chunk title 'Сторінка 190'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"186 186 органів. У зв’язку із цим може зупинитися серце, дихання. Тому  у ніколи не торкайтесь оголених чи погано ізольованих дротів. Щоб уникнути пожежі, не залишайте праски й обігрівача  ввімкненими протягом тривалого часу. Не ставте електроприлади  поряд із легкозаймистими предметами. У разі поже"_ | verify topic relevance; drop or replace with on-topic page |
| `Авраменко Grade 7, p.98` | TOPIC_MISMATCH | chunk title 'Сторінка 89'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"86 2.	 Перепишіть дієслова та поставте в них наголоси.  Будемо, люблю, нести, привести, несемо, пишу, занести, ідете, було,  кажу, несете, була, завезли, принесла, ідемо, везете, роблю, вести, завела. Розбір дієслова як частини мови 1. Частина мови. 2. Початкова форма: інфінітив. 3. Вид: доконаний, "_ | verify topic relevance; drop or replace with on-topic page |

### people-and-relationships

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Авраменко Grade 7, p.100` | TOPIC_MISMATCH | chunk title 'Сторінка 91'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"88 МОРФОЛОГІЯ.  ОРФОГРАФІЯ 2. На другий склад падає наголос у слові  А	 привезти	 Б	 несемо		 В	 ведете	 	 Г	 була 3. На третій склад падає наголос у слові  А	 будемо		 Б	 ведемо		 В	 перепишу		 Г	 перенести 5.	 Складіть і запишіть чотиривірш так, щоб у ньому римувалися чотири діє­ слова, що подані "_ | verify topic relevance; drop or replace with on-topic page |
| `Заболотний Grade 7, p.248` | TOPIC_MISMATCH | chunk title 'Сторінка 248'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"244 244 ТЕМА 7. МА БАР’ЄРИ СПІЛКУВАННЯ. ПРАВИЛА  ГАРНОГО СЛУХАЧА І. Поясніть, як ви розумієте значення слова бар’єр. Скористайтеся подани- ми зображеннями. Перешкода на біговій доріжці Захист від бруду (фільтр) Перешкода   в спілкуванні, комунікації ІІ. Поміркуйте, що означає вислів знайти спільну м"_ | verify topic relevance; drop or replace with on-topic page |
| `Авраменко Grade 5, p.259` | TOPIC_MISMATCH | chunk title 'Сторінка 240'; only 1 shared content stems with plan topic<br>chunk text (first 300 chars): _"240 Розділ 3. ВІД КАЗКИ ДО КНИГИ БУТТЯ Солдат не чекав такого наглого нападу й тому відчай­ душно боронився. Його товариш кинувся йому на допомо­ гу. Не­відомо, чим би все закінчилося, якби Аля не підбігла  до них. — Недобородо, Недовусе, це ж ми! Невже ви нас не впіз­ нали?  Недовус одразу ж відпус"_ | verify topic relevance; drop or replace with on-topic page |
| `Литвінова Grade 7, p.205` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |
| `Ворон Grade 9, p.22` | UNKNOWN_AUTHOR | unknown author 'Ворон'; verify against data/sources.db |  |
| `Заболотний Grade 8, p.177` | TOPIC_MISMATCH | chunk title 'Сторінка 153'; only 0 shared content stems with plan topic<br>chunk text (first 300 chars): _"149 Цей вид активного відпочинку сподобається як дітям, так і до­ рослим. Ви відчуєте себе справжніми шпигунами або героями комп(’)ю­ терної гри. Лазерний лабір(і,и)нт – це не просто чергова розвага, а унікаль­ на пригода. Але необхідно працювати (в,у) команді, шви(д,т)ко приймати  рішен­ня, узгоджу"_ | verify topic relevance; drop or replace with on-topic page |

### places-and-locations

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Заболотний Grade 7, p.248` | TOPIC_MISMATCH | chunk title 'Сторінка 248'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"244 244 ТЕМА 7. МА БАР’ЄРИ СПІЛКУВАННЯ. ПРАВИЛА  ГАРНОГО СЛУХАЧА І. Поясніть, як ви розумієте значення слова бар’єр. Скористайтеся подани- ми зображеннями. Перешкода на біговій доріжці Захист від бруду (фільтр) Перешкода   в спілкуванні, комунікації ІІ. Поміркуйте, що означає вислів знайти спільну м"_ | verify topic relevance; drop or replace with on-topic page |
| `Заболотний Grade 5, p.69` | TOPIC_MISMATCH | chunk title 'Сторінка 71'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"68 Презентація, привілей, предківський, прекрасно, пріори­ тет, престиж, прем’єра, презлющий, прибережжя, прези- дент, престрашенний, преамбула, предвічний. ІІ. Випишіть із тлумачного словника або словника іншомовних слів  п’ять слів з початковою частиною пре, яка входить до складу кореня.  162.	І. "_ | verify topic relevance; drop or replace with on-topic page |
| `Литвінова Grade 6, p.193` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-litvinova-2023) |  |

### pluralia-tantum

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 6, p.134` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-litvinova-2023) |  |

### possessive-adjectives

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Заболотний Grade 6, p.147` | TOPIC_MISMATCH | chunk title 'Сторінка 145'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"145 Прикметник В. Рекуненко. Книжковий будинок  Складні прикметники із частиною -лиций мають в однині м’яку основу (крім Н. й Ор. в.), а в множи- ні – тверду (крім Н. в.). НАПРИКЛАД: білолиций, бі- лолицього, білолицьому, білолицим, білолицих.    Провідміняйте прикметник круглолиций у формах чоловіч"_ | verify topic relevance; drop or replace with on-topic page |
| `Литвінова Grade 6, p.193` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-litvinova-2023) |  |
| `Голуб Grade 6, p.124` | UNKNOWN_AUTHOR | add 'Голуб': ['golub'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-golub-2023) |  |
| `Литвінова Grade 6, p.193` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-litvinova-2023) |  |

### prepositions-cause-purpose

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Заболотний Grade 7, p.193` | TOPIC_MISMATCH | chunk title 'Сторінка 194'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"190 190 Тато сказав, що поїдемо при будь-якій погоді. Небо було похмуре. Милувалися краєвидами на світанку. Чудові! Адже я навчився по інструкції розстав- ляти намет. Потім сам ходив за дровами. До завтра! А які в тебе враження про поїздку? Ви ризикнули, хоча по прогнозу мав бути дощ. Краєвиди на Ук"_ | verify topic relevance; drop or replace with on-topic page |
| `Авраменко Grade 8, p.86` | TOPIC_MISMATCH | chunk title 'Сторінка 70'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"69 § 29–30. Означення 9. Прочитайте текст і виконайте завдання. У нашому житті дуже багато свят, неодмінним атрибутом яких є подарунки. Скажі- мо, на Великдень заведено дарувати писанки та крашанки, на Новий рік і Різдво — цу- керки, невеличкі корисні речі. Однак є і такі подарунки, що не вимагають "_ | verify topic relevance; drop or replace with on-topic page |
| `Авраменко Grade 11, p.72` | LEVEL_MISMATCH | B1 plan cites Grade 11 textbook (threshold: Grade >= 11)<br>chunk title: _Сторінка 55_ | verify pedagogical level fit; verify Grade 11 content is genuinely B1-appropriate |

### prepositions-spatial-review

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 7, p.167` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |
| `Ворон Grade 9, p.226` | UNKNOWN_AUTHOR | unknown author 'Ворон'; verify against data/sources.db |  |

### prepositions-temporal

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Авраменко Grade 11, p.42` | TOPIC_MISMATCH | chunk title 'Сторінка 29'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"Також не можна утворювати ступені порівняння прикметників, що перейшли з від- носних або присвійних у якісні: вовчий (характер), золоті (руки), каштанове (волосся). Різний ступінь ознаки прикметника виражають також за допомогою прислівників  дуже, вельми, занадто, мало, украй, зовсім, особливо, трох"_ | verify topic relevance; drop or replace with on-topic page |
| `Литвінова Grade 7, p.187` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |
| `Авраменко Grade 11, p.72` | LEVEL_MISMATCH | B1 plan cites Grade 11 textbook (threshold: Grade >= 11)<br>chunk title: _Сторінка 55_ | verify pedagogical level fit; verify Grade 11 content is genuinely B1-appropriate |
| `Заболотний Grade 8, p.84` | TOPIC_MISMATCH | chunk title 'Сторінка 78'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"74 ДРУГОРЯДНІ ЧЛЕНИ РЕЧЕННЯ  17. ОЗНАЧЕННЯ Про члени речення, що означають ознаку предмета,   та способи їх вираження  ПРИГАДАЙМО. Що таке прикметник? На які питання відповідають прикметники?  174	 А. Зіставте два речення. У якому з них більш повно змальовано осінь?  Завдяки чому? 1. Настала осінь і"_ | verify topic relevance; drop or replace with on-topic page |

### reading-literature

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Ворон Grade 9, p.169` | UNKNOWN_AUTHOR | unknown author 'Ворон'; verify against data/sources.db |  |
| `Заболотний Grade 8, p.115` | TOPIC_MISMATCH | chunk title 'Сторінка 104'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"Кащук). 8. І місяць в небі як підкова бездумно котиться у  світ (А. Малишко). ІІ. Поясніть, який предмет, дію чи ознаку допоміг схарактеризувати кожен порівняль- ний зворот. ЗВЕРНІТЬ УВАГУ!"_ | verify topic relevance; drop or replace with on-topic page |
| `Заболотний Grade 5, p.134` | TOPIC_MISMATCH | chunk title 'Сторінка 136'; only 1 shared content stems with plan topic<br>chunk text (first 300 chars): _"133 322.	А.  Знайдіть на упаковках слова зі сполученнями букв йо, ьо. Б.  Вимовте чітко знайдені слова, поділяючи їх на склади. Яке сполу- чення (йо чи ьо) може самé бути складом? В.  Простежте, яке сполучення (йо чи ьо) може бути на початку складу,  а яке – у кінці чи в середині складу. Пишемо ЙО П"_ | verify topic relevance; drop or replace with on-topic page |

### restaurant-and-food

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 7, p.205` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |

### short-form-adjectives

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 6, p.191` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-litvinova-2023) |  |
| `Заболотний Grade 7, p.157` | TOPIC_MISMATCH | chunk title 'Сторінка 158'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"154 154 І. Прочитайте речення. Визначте, до яких частин мови належать П виділені слова.  1. Озеро Світязь глибше, ніж Синевир. 2. Що більші зубки часнику, то глибше їх садять. 3. Приїхавши раніше на водой му, ви оберете найкраще місце для риболовлі. 4. Найкраще ловити  рибу зі світанку й до десятої "_ | verify topic relevance; drop or replace with on-topic page |
| `Голуб Grade 6, p.127` | UNKNOWN_AUTHOR | add 'Голуб': ['golub'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-golub-2023) |  |

### simplification-consonants

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 5, p.180` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 5-klas-ukrmova-litvinova-2022) |  |
| `Голуб Grade 5, p.93` | UNKNOWN_AUTHOR | add 'Голуб': ['golub'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 5-klas-ukrmova-golub-2022) |  |

### text-compression

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Голуб Grade 6, p.52` | UNKNOWN_AUTHOR | add 'Голуб': ['golub'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-golub-2023) |  |

### text-register-formal

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Авраменко Grade 8, p.80` | TOPIC_MISMATCH | chunk title 'Сторінка 66'; only 1 shared content stems with plan topic<br>chunk text (first 300 chars): _"Розгадайте ребуси та виконайте завдання. •	 До якого виду інформації (текстової / графічної) належать поняття, назви яких  закодовані? 6. Перетворивши текстову інформацію вправи 4 на графічну, ознайомте з нею  однокласників / батьків / друзів. 1 У=І Р=Х , ,,, ,, , 5,1 1,4 І. ІІ."_ | verify topic relevance; drop or replace with on-topic page |

### verb-formation-suffixes

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Ворон Grade 9, p.174` | UNKNOWN_AUTHOR | unknown author 'Ворон'; verify against data/sources.db |  |
| `Литвінова Grade 6, p.80` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-litvinova-2023) |  |
| `Заболотний Grade 7, p.179` | TOPIC_MISMATCH | chunk title 'Сторінка 180'; only 1 shared content stems with plan topic<br>chunk text (first 300 chars): _"176 176 ли до/дому уві/сні (Ю. Рибчинський). 5. Знов я у/гори іду, а на/зустріч потоки, мов роки (Ю. Рибчинський). 6. Ніченькою темною прийду я знову, любая, і залишусь на/завжди – зали- шусь (О. Пономарьов). ІІ. Знайдіть прислівники й підкресліть їх як члени речення. Гра «Упіймай прислівник». Знайд"_ | verify topic relevance; drop or replace with on-topic page |

### vocative-formal

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 6, p.141` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-litvinova-2023) |  |
| `Заболотний Grade 11, p.98` | LEVEL_MISMATCH | B1 plan cites Grade 11 textbook (threshold: Grade >= 11)<br>chunk title: _Сторінка 73_ | verify pedagogical level fit; verify Grade 11 content is genuinely B1-appropriate |

### word-formation-adjectives

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 6, p.208` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-litvinova-2023) |  |
| `Авраменко Grade 6, p.136` | TOPIC_MISMATCH | chunk title 'Сторінка 128'; only 1 shared content stems with plan topic<br>chunk text (first 300 chars): _"РОЗВИТОК МОВЛЕННЯ 128 1. Прочитайте текст і виконайте завдання в тестовій формі. Шестирічна Леся, коли недавно в сім’ї заговорили про весну, сказала: — А в гаї сонце зацвіло! Звичайно, коли навесні йде в ріст молода трава, розвиваються дерева, бар­ вами веселки спалахують по безмежній землі озера, м"_ | verify topic relevance; drop or replace with on-topic page |
| `Голуб Grade 6, p.35` | UNKNOWN_AUTHOR | add 'Голуб': ['golub'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-golub-2023) |  |

### word-formation-nouns

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 6, p.83` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-litvinova-2023) |  |
| `Голуб Grade 6, p.35` | UNKNOWN_AUTHOR | add 'Голуб': ['golub'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-golub-2023) |  |
| `Голуб Grade 6, p.107` | UNKNOWN_AUTHOR | add 'Голуб': ['golub'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-golub-2023) |  |

### work-and-career

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 7, p.30` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |
| `Литвінова Grade 7, p.205` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |

## B2 — broken citations

### pronoun-system-advanced

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Заболотний Grade 9, p. 80` | TOPIC_MISMATCH | chunk title 'Сторінка 59'; only 1 shared content stems with plan topic<br>chunk text (first 300 chars): _"Сьогодні йде дощ і свище вітер. Сьогодні йде дощ, але не свище вітер. В. Зробіть висновок про одну з умов, коли між частинами складносурядного речення кому не ставимо. 107 108  109"_ | verify topic relevance; drop or replace with on-topic page |
| `Авраменко Grade 10, p. 45` | TOPIC_MISMATCH | chunk title 'Сторінка 33'; only 1 shared content stems with plan topic<br>chunk text (first 300 chars): _"33 Пароніми 4.	 Утворіть словосполучення, вибравши з дужок потрібне слово.  Дружний, дружній (тон, колектив); дощовий, дощовитий (день, черв’як); ожеледь, оже- ледиця (на деревах, на дорогах); корисний, корисливий (мета, підручник); паливо, пальне  (природне, дизельне).  ЗАУВАЖТЕ!  Таких слів, як до"_ | verify topic relevance; drop or replace with on-topic page |

## Aggregate findings

### Authors to add to `_TEXTBOOK_AUTHOR_TRANSLITS`

| author | citations affected | suggested translits | corpus has it? |
| --- | --- | --- | --- |
| Болшакова | 1 | — | unknown |
| Варзацька | 1 | ['varzatska'] | yes |
| Ворон | 12 | — | unknown |
| Голуб | 13 | ['golub'] | yes |
| Литвінова | 44 | ['litvinova'] | yes |

### Level-mismatch summary

| level | author | grade | citations |
| --- | --- | --- | --- |
| B1 | Авраменко | Grade 11 | 10 |
| B1 | Заболотний | Grade 11 | 1 |

### Ghost sources by author + grade

_No ghost sources._

### Notes

- TOPIC_MISMATCH is heuristic: a citation is flagged when fewer than 3 content-word stems overlap between the plan's topic block (title + subtitle + objectives + grammar + content_outline sections) and the resolved chunk's title + body. False positives are expected; verify each row before editing the plan.
- LEVEL_MISMATCH is policy: B1 Grade >= 11, B2 Grade >= 11. Not always wrong (school textbooks include simple paradigm tables at any level), but flagged for orchestrator review.
- GHOST_SOURCE and GHOST_PAGE are deterministic against `data/sources.db` using the FIXED LIKE pattern (`%-translit-%` OR `%-translit`).
