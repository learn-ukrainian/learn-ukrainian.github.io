# A1 + A2 plan_references audit

Generated: 2026-05-15

## Summary

- Plans audited: **124**
  - A1: 55
  - A2: 69
- Paged citations extracted: **66**
- By failure mode:
  - OK: 29
  - GHOST_SOURCE: 0
  - GHOST_PAGE: 0
  - TOPIC_MISMATCH: 14
  - LEVEL_MISMATCH: 4
  - UNKNOWN_AUTHOR: 19

Failure modes are reported separately: a single citation may be both TOPIC_MISMATCH and LEVEL_MISMATCH; the audit assigns the strictest (TOPIC_MISMATCH first), and LEVEL_MISMATCH is listed alongside in the aggregate findings.

## A1 — broken citations

### colors

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Большакова Grade 2, p.38` | TOPIC_MISMATCH | chunk title 'Сторінка 37'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"37 — Хоч ми не бачимо зірок, але можемо почути їх, якщо  прислухаємося. — Так, твоя правда…  — дівчинка підійшла до музич- ного програвача й  збільшила гучність.  — Чуєш? Це зірки  співають. — Їхній спів подібний до вітру, який лагідно зачепив  найменший у  світі дзвіночок. — Найменший у  світі дз"_ | verify topic relevance; drop or replace with on-topic page |
| `Вашуленко Grade 3, p.130` | TOPIC_MISMATCH | chunk title 'Сторінка 132'; only 1 shared content stems with plan topic<br>chunk text (first 300 chars): _"132 Одного разу, вертаючись додому, Уля побачила біля сво- го під’їзду незнайомого хлопчика. Він сидів у легенькому, на  велосипедних колесах візку, під легким шатриком від сонця,  а на колінах у нього лежала груба, з барвистою обкладин- кою книжка. Проте хлопчик зовсім не збирався гортати її.  Він "_ | verify topic relevance; drop or replace with on-topic page |

### days-and-months

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Вашуленко Grade 2, p.83` | TOPIC_MISMATCH | chunk title 'Сторінка 85'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"не могла красуня зрушити з місця. Гнучкий дівочий  стан став тонким вербовим стовбуром, руки пере- творилися на гілля, а довге кучеряве волосся — на  тонесенькі гілочки, що схилялися до самої води, тор- каючись свого відображення в ній. Саме так, як мріяла  Оксана.  А Водяник, плеснувши по воді хвос"_ | verify topic relevance; drop or replace with on-topic page |
| `Вашуленко Grade 2, p.69` | TOPIC_MISMATCH | chunk title 'Сторінка 71'; only 0 shared content stems with plan topic<br>chunk text (first 300 chars): _"— Шкода, що дідусь сіятиме довкола сніг лише  завтра! — сказав один із Вітерців, зиркнувши на са- ни. — От якби сьогодні, ми у сніжки погралися б! Чекати Вітерці не любили. Тож розв’язали дідусів  мішок, відсипали звідтіля трохи снігу і до самого вечо- ра досхочу бавилися. А зранку визирнули на подв"_ | verify topic relevance; drop or replace with on-topic page |

### euphony

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Літвінова Grade 5, p.174` | UNKNOWN_AUTHOR | add 'Літвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 5-klas-ukrmova-litvinova-2022) |  |

### how-many

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Авраменко Grade 6, p.152` | TOPIC_MISMATCH | chunk title 'Сторінка 144'; only 0 shared content stems with plan topic<br>chunk text (first 300 chars): _"РОЗВИТОК МОВЛЕННЯ 144 1.	Виконайте завдання в тестовій формі. 	 Зразком художнього стилю є речення А	 Лілія — рід багаторічних цибулинних рослин родини лілійних. Б	 У громаді на Полтавщині висадили 100 лілій як символ перемоги. В	 Шановна Ліліє Олегівно, запрошуємо Вас на святкування Дня вчителя. Г"_ | verify topic relevance; drop or replace with on-topic page |

### i-want-i-can

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Караман Grade 10, p.179` | LEVEL_MISMATCH | A1 plan cites Grade 10 textbook (above level)<br>chunk title: _Сторінка 100_ | verify pedagogical level fit; prefer Grade <=6 source if available |
| `Літвінова Grade 7, p.55` | UNKNOWN_AUTHOR | add 'Літвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |

### many-things

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Вашуленко Grade 3, p.114` | TOPIC_MISMATCH | chunk title 'Сторінка 116'; only 1 shared content stems with plan topic<br>chunk text (first 300 chars): _"116 * * * Тече вода з-під явора яром на долину. Пишається над водою червона калина. Пишається калинонька, явір молодіє, а кругом їх верболози й лози зеленіють. Тече вода із-за гаю та попід горою. Хлюпощуться качаточка поміж осокою. А качечка випливає з качуром за ними, ловить ряску, розмовляє з дітк"_ | verify topic relevance; drop or replace with on-topic page |
| `Большакова Grade 2, p.18` | TOPIC_MISMATCH | chunk title 'Сторінка 17'; only 1 shared content stems with plan topic<br>chunk text (first 300 chars): _"17 Подія 5 Уранці відчинились двері і в бібліотеку прийшли люди.  Мишка розбудила Курочку, а Курочка — Лисицю. Вони хотіли  тишком-нишком піти, але раптом Курочка впізнала фермера.  Вона підморгнула Лисиці і прошепотіла:  — Якщо я почну квоктати «Ко-ко-ко!», то він тебе схопить!  Лисиця затремтіла"_ | verify topic relevance; drop or replace with on-topic page |
| `Большакова Grade 2, p.42` | TOPIC_MISMATCH | chunk title 'Сторінка 41'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"41 казка. оПис явиЩ Тема і головна думка. Опис явища • Опиши дощ за допомогою слів — назв ознак. Який дощ  тобі здався б дивним? Чому? ДИВНИЙ ДОЩ Одного разу пішов цукерковий дощ. З неба  летіли різнобарвні цукерки: і зелені, і рожеві,  і фіолетові, й блакитні. Спочатку люди думали,  що то град. Аж"_ | verify topic relevance; drop or replace with on-topic page |

### my-morning

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Караман Grade 10, p.187` | LEVEL_MISMATCH | A1 plan cites Grade 10 textbook (above level)<br>chunk title: _Сторінка 105_ | verify pedagogical level fit; prefer Grade <=6 source if available |

### things-have-gender

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Пономарова Grade 3, p.86` | UNKNOWN_AUTHOR | add 'Пономарова': ['ponomarova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 3-klas-ukrainska-mova-ponomarova-2020-1) |  |

### this-and-that

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Літвінова Grade 6, p.273` | UNKNOWN_AUTHOR | add 'Літвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-litvinova-2023) |  |

### verbs-group-one

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Варзацька Grade 4, p.129` | UNKNOWN_AUTHOR | add 'Варзацька': ['varzatska'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 4-klas-ukrayinska-mova-varzatska-2021-1) |  |
| `Захарійчук Grade 4, p.110` | TOPIC_MISMATCH | chunk title 'Сторінка 111'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"Дев’ять, дев’ятнадцять, дев’ятий, десятий, десять,  третій, три, сім, сьомий, сьома, десяте, дванадцята, чотир­ надцяте. •  Поставте до числівників питання. Складіть словосполучення  числівників з іменниками. Запишіть. Поставте наголос у чи­ слівниках. 255. Прочитайте числівники. Важливою ознакою кр"_ | verify topic relevance; drop or replace with on-topic page |

### verbs-group-two

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Караман Grade 10, p.179` | TOPIC_MISMATCH | chunk title 'Сторінка 100'; only 1 shared content stems with plan topic<br>chunk text (first 300 chars): _"СПІЛКУВАННЯ 265 Прочитайте висловлення сучасного українського дослідника  української мови. Чи згодні ви з  його думкою? Умотивуйте доречність  чи недоречність уживання запозиченої лексики. Іноді запозичення вкорінюються не стільки, щоб уточнити  поняття чи прояснити суть справи, скільки з бажання м"_ | verify topic relevance; drop or replace with on-topic page |
| `Захарійчук Grade 4, p.110` | TOPIC_MISMATCH | chunk title 'Сторінка 111'; only 0 shared content stems with plan topic<br>chunk text (first 300 chars): _"Дев’ять, дев’ятнадцять, дев’ятий, десятий, десять,  третій, три, сім, сьомий, сьома, десяте, дванадцята, чотир­ надцяте. •  Поставте до числівників питання. Складіть словосполучення  числівників з іменниками. Запишіть. Поставте наголос у чи­ слівниках. 255. Прочитайте числівники. Важливою ознакою кр"_ | verify topic relevance; drop or replace with on-topic page |

### weather

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Заболотний Grade 8, p.126` | LEVEL_MISMATCH | A1 plan cites Grade 8 textbook (above level)<br>chunk title: _Сторінка 113_ | verify pedagogical level fit; prefer Grade <=6 source if available |

### what-i-like

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Літвінова Grade 7, p.26` | UNKNOWN_AUTHOR | add 'Літвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 7-klas-ukrmova-litvinova-2024) |  |

### what-is-it-like

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Пономарова Grade 3, p.98` | UNKNOWN_AUTHOR | add 'Пономарова': ['ponomarova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 3-klas-ukrainska-mova-ponomarova-2020-1) |  |
| `Вашуленко Grade 3, p.128` | TOPIC_MISMATCH | chunk title 'Сторінка 130'; only 1 shared content stems with plan topic<br>chunk text (first 300 chars): _"130    Прочитайте заголовок оповідання. Як ви думаєте, що  означає це слово? Про що може йти мова в цьому  творі? ЛЬОДОХІД По зимі, коли в Карпатських горах тануть сніги, скрізь у  долинах вирує повінь. Не та стає й річка Уж. Улітку Уж зовсім мілкий та спокійний — у багатьох міс- цях убрід перейдеш"_ | verify topic relevance; drop or replace with on-topic page |

### what-time

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Літвінова Grade 6, p.245` | UNKNOWN_AUTHOR | add 'Літвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-litvinova-2023) |  |

## A2 — broken citations

### all-cases-practice

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Варзацька Grade 4, с. 38` | UNKNOWN_AUTHOR | add 'Варзацька': ['varzatska'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 4-klas-ukrayinska-mova-varzatska-2021-1) |  |

### checkpoint-cases

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Варзацька Grade 4, с. 38` | UNKNOWN_AUTHOR | add 'Варзацька': ['varzatska'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 4-klas-ukrayinska-mova-varzatska-2021-1) |  |

### checkpoint-instrumental

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Голуб Grade 6, с. 179` | UNKNOWN_AUTHOR | add 'Голуб': ['golub'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-golub-2023) |  |

### instrumental-accompaniment

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Пономарьова Grade 4, с. 53` | UNKNOWN_AUTHOR | add 'Пономарьова': ['ponomarova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 4-klas-ukrayinska-mova-ponomarova-2021-1) |  |

### instrumental-adjectives-pronouns

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Голуб Grade 6, с. 179` | UNKNOWN_AUTHOR | add 'Голуб': ['golub'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-golub-2023) |  |
| `Авраменко Grade 11, с. 25` | TOPIC_MISMATCH | chunk title 'Сторінка 17'; only 1 shared content stems with plan topic<br>chunk text (first 300 chars): _"Рейтинги злетіли ледь не до небес. Він отримав свій перший ефір- ний час і перший гонорар — 55 доларів за тиждень. Так розпочалася кар’єра легендарного радіоведу- чого Ларрі Кінга. Чимало хто потім казав, що йому  просто пощастило. Можливо. А можливо, і ні. Бо він  насправді міг не поїхати до Флорид"_ | verify topic relevance; drop or replace with on-topic page |

### instrumental-profession

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Заболотний Grade 10, с. 153` | LEVEL_MISMATCH | A2 plan cites Grade 10 textbook (above level)<br>chunk title: _Сторінка 112_ | verify pedagogical level fit; prefer Grade <=6 source if available |

### metalanguage-morphology

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Заболотний Grade 5, p.245` | TOPIC_MISMATCH | chunk title 'Сторінка 244'; only 2 shared content stems with plan topic<br>chunk text (first 300 chars): _"Навчальне видання ЗАБОЛОТНИЙ Олександр Вікторович  ЗАБОЛОТНИЙ Віктор Вікторович УКРАЇНСЬКА МОВА Підручник для 5 класу  закладів загальної середньої освіти Рекомендовано Міністерством освіти і науки України Відповідальна за випуск Наталія Заблоцька. Редактор Ірина Коваленко. Обкладинка Марії Круковсь"_ | verify topic relevance; drop or replace with on-topic page |

### metalanguage-phonetics

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 5, p.104` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 5-klas-ukrmova-litvinova-2022) |  |
| `Голуб Grade 5, p.66` | UNKNOWN_AUTHOR | add 'Голуб': ['golub'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 5-klas-ukrmova-golub-2022) |  |

### metalanguage-syntax-cases

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Литвінова Grade 5, p.196` | UNKNOWN_AUTHOR | add 'Литвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 5-klas-ukrmova-litvinova-2022) |  |
| `Голуб Grade 5, p.107` | UNKNOWN_AUTHOR | add 'Голуб': ['golub'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 5-klas-ukrmova-golub-2022) |  |

### plural-genitive

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Літвінова Grade 6, с. 160` | UNKNOWN_AUTHOR | add 'Літвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-litvinova-2023) |  |

### plural-nominative-accusative

| citation | mode | corpus reality | suggested fix |
| --- | --- | --- | --- |
| `Літвінова Grade 6, с. 157` | UNKNOWN_AUTHOR | add 'Літвінова': ['litvinova'] to _TEXTBOOK_AUTHOR_TRANSLITS (corpus has 6-klas-ukrmova-litvinova-2023) |  |

## Aggregate findings

### Authors to add to `_TEXTBOOK_AUTHOR_TRANSLITS`

| author | citations affected | suggested translits | corpus has it? |
| --- | --- | --- | --- |
| Варзацька | 3 | ['varzatska'] | yes |
| Голуб | 4 | ['golub'] | yes |
| Литвінова | 2 | ['litvinova'] | yes |
| Літвінова | 7 | ['litvinova'] | yes |
| Пономарова | 2 | ['ponomarova'] | yes |
| Пономарьова | 1 | ['ponomarova'] | yes |

### Level-mismatch summary

| level | author | grade | citations |
| --- | --- | --- | --- |
| A1 | Заболотний | Grade 8 | 1 |
| A1 | Караман | Grade 10 | 3 |
| A1 | Літвінова | Grade 7 | 2 |
| A2 | Авраменко | Grade 11 | 1 |
| A2 | Заболотний | Grade 10 | 1 |

### Ghost sources by author + grade

_No ghost sources._

### Notes

- TOPIC_MISMATCH is heuristic: a citation is flagged when fewer than 3 content-word stems overlap between the plan's topic block (title + subtitle + objectives + grammar + content_outline sections) and the resolved chunk's title + body. False positives are expected; verify each row before editing the plan.
- LEVEL_MISMATCH is policy: A1 cites Grade >= 7, A2 cites Grade >= 10. Not always wrong (school textbooks include simple paradigm tables at any level), but flagged for orchestrator review.
- GHOST_SOURCE and GHOST_PAGE are deterministic against `data/sources.db` using the FIXED LIKE pattern (`%-translit-%` OR `%-translit`).
