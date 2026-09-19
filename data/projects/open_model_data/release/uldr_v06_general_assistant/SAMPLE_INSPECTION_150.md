# Multi-Seed Sample Inspection of 150 Mined Records (Phase 6.1)

**Audit Result:** ALL 150 RECORDS PASSED — 100% PASS RATE

**Sampling Protocol:** 3 PRNG seeds (42, 123, 777), 50 records per seed (total 150 records across eval and SFT shards).

## Release-Wide Defect Scan (All 75,000 SFT + 255 Eval Records)

| Defect Class | Count Across Release | Status |
|---|---|---|
| `truncated_snippets` | 0 | ✅ 0 |
| `inverted_definitions` | 0 | ✅ 0 |
| `disallowed_lemmas` | 0 | ✅ 0 |
| `substring_terms` | 0 | ✅ 0 |
| `unresolved_anaphora` | 0 | ✅ 0 |
| `context_bound_heads` | 0 | ✅ 0 |
| `descriptive_non_concepts` | 0 | ✅ 0 |
| `metaphors_and_evaluatives` | 0 | ✅ 0 |
| `query_framing_mismatch` | 0 | ✅ 0 |

## Multi-Seed Inspected Sample Overview

| # | Seed | Origin | Concept | Subject | Grade | Terms | Citation | Anaphora-Free | OCR-Clean | Def-Aligned | Terms Valid | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 42 | `eval_shard_001_of_005.jsonl:line_26` | **Навіть одяг** | vsesvitnia | 8 | вбрання, тварина, убір, пояс | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 2 | 42 | `eval_shard_001_of_005.jsonl:line_24` | **Верхня палата** | vsesvitnia | 8 | палата, сенат, представник, духовенство | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 3 | 42 | `eval_shard_001_of_005.jsonl:line_20` | **Колоніалізм** | vsesvitnia | 8 | підкорення, країна, ресурс, праця | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 4 | 42 | `eval_shard_001_of_005.jsonl:line_12` | **Революція** | vsesvitnia | 8 | переворот, суспільство, зміна, перетворення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 5 | 42 | `eval_shard_001_of_005.jsonl:line_5` | **Рівносильні нерівності** | algebra | 9 | нерівність, множина, розв'язок | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 6 | 42 | `eval_shard_002_of_005.jsonl:line_45` | **Систематизація нормативних актів** | pravoznavstvo | 9 | систематизація, акт, упорядкування, вдосконалення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 7 | 42 | `eval_shard_002_of_005.jsonl:line_33` | **Правомірна поведінка** | pravoznavstvo | 9 | поведінка, припис, норма, держава | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 8 | 42 | `eval_shard_002_of_005.jsonl:line_14` | **Пульс** | biolohiya | 8 | показник, ритмічність, скорочення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 9 | 42 | `eval_shard_002_of_005.jsonl:line_10` | **Нейронауки** | biolohiya | 8 | галузь, знання, вивчення, система | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 10 | 42 | `eval_shard_002_of_005.jsonl:line_20` | **Передня камера** | biolohiya | 8 | простір, оболонка, камера, райдужка | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 11 | 42 | `eval_shard_003_of_005.jsonl:line_45` | **Географічний простір** | heohrafiya | 8 | простір, об'єкт, територія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 12 | 42 | `eval_shard_003_of_005.jsonl:line_31` | **Степ** | heohrafiya | 8 | зона, держава, підзона | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 13 | 42 | `eval_shard_003_of_005.jsonl:line_41` | **Кліматичні ресурси** | heohrafiya | 8 | ресурс, енергетика | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 14 | 42 | `eval_shard_003_of_005.jsonl:line_12` | **Позов** | pravoznavstvo | 9 | закон, звернення, особа, суд | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 15 | 42 | `eval_shard_003_of_005.jsonl:line_19` | **Меліорація** | heohrafiya | 8 | дія, покращення, родючість, ґрунт | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 16 | 42 | `eval_shard_004_of_005.jsonl:line_50` | **Гімн** | mystetstvo | 8 | характер, прославлення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 17 | 42 | `eval_shard_004_of_005.jsonl:line_29` | **Обмін** | ekonomika | 10 | рух, товар, власник | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 18 | 42 | `eval_shard_004_of_005.jsonl:line_6` | **Громадянський обов'язок** | hromadianska | 8 | обов'язок, громадянин, країна, закон | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 19 | 42 | `eval_shard_004_of_005.jsonl:line_14` | **Демократія** | hromadianska | 8 | крок, розвиток, система | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 20 | 42 | `eval_shard_004_of_005.jsonl:line_38` | **Піктографічне письмо** | ukrmova | 8 | письмо, комунікація, значок, малюнок | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 21 | 42 | `eval_shard_005_of_005.jsonl:line_49` | **Авторитет** | etyka | 6 | переконання, поведінка, особа, організація | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 22 | 42 | `eval_shard_005_of_005.jsonl:line_30` | **Культура** | tekhnolohiyi | 8 | частота, відвідування, постановка, виставка | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 23 | 42 | `eval_shard_005_of_005.jsonl:line_26` | **Декор** | tekhnolohiyi | 8 | система, елемент, призначення, функція | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 24 | 42 | `eval_shard_005_of_005.jsonl:line_21` | **Методи проєктування** | tekhnolohiyi | 8 | проєктування, дія, об'єкт | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 25 | 42 | `eval_shard_005_of_005.jsonl:line_37` | **Громадянські обов'язки** | etyka | 6 | обов'язок, норма, держава, ряд | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 26 | 42 | `sft_shard_135_of_150.jsonl:line_93` | **Монети** | istoriya | 5 | змога, розвиток, торгівля, зв'язка | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 27 | 42 | `sft_shard_015_of_150.jsonl:line_369` | **Основний принцип життя аристократів** | zarlit | 10 | принцип, аристократ, лицемірство, шанування | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 28 | 42 | `sft_shard_058_of_150.jsonl:line_349` | **Державний устрій** | heohrafiya | 9 | устрій, організація, держава | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 29 | 42 | `sft_shard_074_of_150.jsonl:line_211` | **Гідроліз солей** | khimiya | 11 | кислота, сіль, гідроліз, взаємодія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 30 | 42 | `sft_shard_103_of_150.jsonl:line_460` | **Аеробне дихання** | pryroda | 8 | дихання, участь, кисень, окиснення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 31 | 42 | `sft_shard_003_of_150.jsonl:line_37` | **Ідеологія** | vsesvitnia | 9 | ідея, переконання, цінність, бачення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 32 | 42 | `sft_shard_048_of_150.jsonl:line_54` | **Головоногі** | biolohiya | 7 | молюск, тіло, голова | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 33 | 42 | `sft_shard_012_of_150.jsonl:line_387` | **Жерці** | istoriya | 7 | особа, ритуал, богослужіння, релігія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 34 | 42 | `sft_shard_134_of_150.jsonl:line_384` | **Грант** | finansova | 9 | особа, організація, бізнес, реалізація | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 35 | 42 | `sft_shard_046_of_150.jsonl:line_17` | **Комбінаторика** | matematyka | 11 | вибір, розміщення, елемент, множина | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 36 | 42 | `sft_shard_002_of_150.jsonl:line_255` | **Ядерні реакції** | fizyka | 11 | реакція, перетворення, ядро, взаємодія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 37 | 42 | `sft_shard_079_of_150.jsonl:line_273` | **Материки** | ya_doslidzhuiu_svit | 4 | ділянка, суходіл, вода | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 38 | 42 | `sft_shard_044_of_150.jsonl:line_277` | **Волонтерство** | hromadianska | 9 | дія, енергія, вміння | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 39 | 42 | `sft_shard_150_of_150.jsonl:line_131` | **Вигуки** | ukrmova | university | розряд, функція, емоція, волевиявлення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 40 | 42 | `sft_shard_131_of_150.jsonl:line_477` | **Небо** | ukrmova | 6 | атмосфера, поверхня, загал, об'єкт | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 41 | 42 | `sft_shard_121_of_150.jsonl:line_171` | **Податок** | pravoznavstvo | 11 | закон, орган, платіж, бюджет | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 42 | 42 | `sft_shard_053_of_150.jsonl:line_255` | **Мода вибірки** | algebra | 8 | мода, вибірка, ряд | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 43 | 42 | `sft_shard_039_of_150.jsonl:line_210` | **Образ царя** | zarlit | 9 | образ, алегорія, душа, злам | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 44 | 42 | `sft_shard_076_of_150.jsonl:line_314` | **Покарання** | etyka | 5 | уникнення, спілкування, небажання | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 45 | 42 | `sft_shard_141_of_150.jsonl:line_141` | **Сталий розвиток** | pryroda | 8 | розвиток, концепція, змога, баланс | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 46 | 42 | `sft_shard_010_of_150.jsonl:line_451` | **Авторитаризм** | vsesvitnia | 10 | лад, режим, управління, апарат | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 47 | 42 | `sft_shard_142_of_150.jsonl:line_75` | **Сузір'я** | astronomiya | 11 | ділянка, сфера, зручність, орієнтування | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 48 | 42 | `sft_shard_108_of_150.jsonl:line_289` | **Сучасний танець** | mystetstvo | 5 | танець, рух, ритм, образ | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 49 | 42 | `sft_shard_018_of_150.jsonl:line_201` | **Вегетативні пагони** | biolohiya | 7 | пагін, гілка | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 50 | 42 | `sft_shard_071_of_150.jsonl:line_432` | **Основа піраміди** | matematyka | 11 | піраміда, трикутник, катет | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 51 | 123 | `eval_shard_001_of_005.jsonl:line_37` | **Вуглекислий газ** | khimiya | 8 | газ, речовина | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 52 | 123 | `eval_shard_001_of_005.jsonl:line_49` | **Хімічний зв'язок** | khimiya | 8 | взаємодія, атом, стійкість, частинка | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 53 | 123 | `eval_shard_001_of_005.jsonl:line_30` | **Бароко** | vsesvitnia | 8 | стиль, мистецтво | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 54 | 123 | `eval_shard_001_of_005.jsonl:line_48` | **Суверенітет** | pravoznavstvo | 9 | держава, зміст, втручання, організація | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 55 | 123 | `eval_shard_001_of_005.jsonl:line_21` | **Механічна енергія** | fizyka | 8 | енергія, міра, рух, взаємодія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 56 | 123 | `eval_shard_002_of_005.jsonl:line_8` | **Спинний мозок** | biolohiya | 8 | мозок, тяж, канал, хребет | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 57 | 123 | `eval_shard_002_of_005.jsonl:line_47` | **Особисті гарантії** | pravoznavstvo | 9 | гарантія, громадянин, захист, свобода | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 58 | 123 | `eval_shard_002_of_005.jsonl:line_37` | **Юридична відповідальність** | pravoznavstvo | 9 | правопорушення, відповідальність, застосування, особа | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 59 | 123 | `eval_shard_002_of_005.jsonl:line_2` | **Звичайне скло** | khimiya | 8 | оксид, скло, речовина, силіцій | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 60 | 123 | `eval_shard_002_of_005.jsonl:line_23` | **Суб'єкти правовідносин** | pravoznavstvo | 9 | суб'єкт, індивід, організація, особа | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 61 | 123 | `eval_shard_003_of_005.jsonl:line_34` | **Кримінальне право** | pravoznavstvo | 9 | правопорушення, право, система, норма | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 62 | 123 | `eval_shard_003_of_005.jsonl:line_10` | **Слідчий** | pravoznavstvo | 9 | особа, орган, розслідування | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 63 | 123 | `eval_shard_003_of_005.jsonl:line_22` | **Шлюб** | pravoznavstvo | 9 | союз, жінка, чоловік, орган | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 64 | 123 | `eval_shard_003_of_005.jsonl:line_8` | **Суддя** | pravoznavstvo | 9 | правопорушення, особа, право, ім'я | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 65 | 123 | `eval_shard_003_of_005.jsonl:line_42` | **Громадянська освіта** | hromadianska | 8 | освіта, знання, закон, уміння | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 66 | 123 | `eval_shard_004_of_005.jsonl:line_18` | **Право** | hromadianska | 8 | норма, держава, регулювання | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 67 | 123 | `eval_shard_004_of_005.jsonl:line_51` | **Смальта** | mystetstvo | 8 | скло, кубик, пластинка, мозаїка | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 68 | 123 | `eval_shard_004_of_005.jsonl:line_7` | **Забобони** | hromadianska | 8 | упередження, індивід, реальність, подія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 69 | 123 | `eval_shard_004_of_005.jsonl:line_37` | **Верлібр** | ukrlit | 8 | вірш, довжина, наголос | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 70 | 123 | `eval_shard_004_of_005.jsonl:line_44` | **Місцевий колорит** | zarlit | 8 | колорит, твір, елемент, побут | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 71 | 123 | `eval_shard_005_of_005.jsonl:line_47` | **Конфлікт** | etyka | 6 | зіткнення, інтерес, оцінка, цінність | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 72 | 123 | `eval_shard_005_of_005.jsonl:line_12` | **Соціальна відповідальність бізнесу** | zdorovia | 8 | відповідальність, бізнес, практика, участь | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 73 | 123 | `eval_shard_005_of_005.jsonl:line_7` | **Рапсодія** | mystetstvo | 8 | твір, характер | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 74 | 123 | `eval_shard_005_of_005.jsonl:line_45` | **Взаємоповага** | etyka | 6 | повага, виявлення, почуття, взаємність | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 75 | 123 | `eval_shard_005_of_005.jsonl:line_24` | **Художня фотографія** | tekhnolohiyi | 8 | фотографія, мистецтво, відображення, дійсність | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 76 | 123 | `sft_shard_053_of_150.jsonl:line_227` | **Виготовлення моделей з гофрокартону** | tekhnolohiyi | 6 | виготовлення, модель, гофрокартон, заняття | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 77 | 123 | `sft_shard_137_of_150.jsonl:line_148` | **Проектуюча пряма** | heometriya | 10 | площина, проекція | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 78 | 123 | `sft_shard_010_of_150.jsonl:line_409` | **Ошибана** | tekhnolohiyi | 5 | виготовлення, картина, матеріал, листя | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 79 | 123 | `sft_shard_127_of_150.jsonl:line_137` | **Інформаційна структура сайта** | informatyka | 11 | структура, сайт, організація, веб-сайт | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 80 | 123 | `sft_shard_146_of_150.jsonl:line_100` | **Неділя** | zarlit | 9 | ґанок, шанування | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 81 | 123 | `sft_shard_110_of_150.jsonl:line_128` | **Хімічна рівновага** | khimiya | 11 | система, реакція, швидкість | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 82 | 123 | `sft_shard_134_of_150.jsonl:line_400` | **Висота циліндра** | matematyka | 11 | висота, циліндр, перпендикуляр | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 83 | 123 | `sft_shard_086_of_150.jsonl:line_283` | **Бережливість** | zdorovia | 7 | піклування, майно, повага, праця | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 84 | 123 | `sft_shard_023_of_150.jsonl:line_424` | **Площа бічної поверхні призми** | heometriya | 9 | площа, поверхня, призма, грань | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 85 | 123 | `sft_shard_078_of_150.jsonl:line_288` | **Сурядний ряд** | ukrmova | university | ряд, компонент, функція | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 86 | 123 | `sft_shard_142_of_150.jsonl:line_240` | **Змінні зорі** | astronomiya | 11 | блиск, поверхня, дія, причина | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 87 | 123 | `sft_shard_038_of_150.jsonl:line_160` | **Йонізація газів** | fizyka | 11 | розпад, молекула, електрон, йонізація | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 88 | 123 | `sft_shard_040_of_150.jsonl:line_370` | **Прикметник** | ukrmova | university | категорія, відмінок | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 89 | 123 | `sft_shard_087_of_150.jsonl:line_8` | **Стиснення даних** | informatyka | 8 | файл, стиснення, перекодування, зменшення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 90 | 123 | `sft_shard_028_of_150.jsonl:line_86` | **Світова війна** | vsesvitnia | 10 | війна, боротьба, держава, участь | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 91 | 123 | `sft_shard_067_of_150.jsonl:line_482` | **Ренатурація** | biolohiya | 9 | відновлення, структура, макромолекула, денатурація | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 92 | 123 | `sft_shard_041_of_150.jsonl:line_119` | **Платоспроможність** | ekonomika | 11 | оцінка, позичальник, коефіцієнт, ліквідність | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 93 | 123 | `sft_shard_051_of_150.jsonl:line_9` | **Східна елонгація** | astronomiya | 11 | елонгація, момент, положення, планета | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 94 | 123 | `sft_shard_096_of_150.jsonl:line_373` | **Ліберальний підхід** | hromadianska | 10 | підхід, пояснення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 95 | 123 | `sft_shard_090_of_150.jsonl:line_226` | **Декодування повідомлення** | informatyka | 8 | декодування, повідомлення, отримання | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 96 | 123 | `sft_shard_012_of_150.jsonl:line_21` | **Земля** | khimiya | 11 | дім, істота | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 97 | 123 | `sft_shard_116_of_150.jsonl:line_55` | **Бензен** | khimiya | 10 | сировина, промисловість, застосування | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 98 | 123 | `sft_shard_025_of_150.jsonl:line_469` | **Черевоногі** | biolohiya | 7 | молюск, тіло, голова, нога | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 99 | 123 | `sft_shard_021_of_150.jsonl:line_480` | **Ґрунт** | heohrafiya | 6 | рослинність, родючість | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 100 | 123 | `sft_shard_120_of_150.jsonl:line_352` | **Реакція полімеризації** | khimiya | 9 | реакція, полімеризація, сполучення, молекула | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 101 | 777 | `eval_shard_001_of_005.jsonl:line_41` | **Елементарний заряд** | khimiya | 8 | заряд, електрон, одиниця, вимірювання | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 102 | 777 | `eval_shard_001_of_005.jsonl:line_13` | **Рівні фігури** | heometriya | 9 | фігура, рух, образ | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 103 | 777 | `eval_shard_001_of_005.jsonl:line_32` | **Аграрна революція** | vsesvitnia | 8 | революція, реформування, господарство, збільшення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 104 | 777 | `eval_shard_001_of_005.jsonl:line_51` | **Максимальне значення** | khimiya | 8 | ступінь, окиснення, електрон | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 105 | 777 | `eval_shard_001_of_005.jsonl:line_23` | **В'язкість** | fizyka | 8 | рідина, газ, переміщення, речовина | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 106 | 777 | `eval_shard_002_of_005.jsonl:line_41` | **Конституція** | pravoznavstvo | 9 | закон, держава | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 107 | 777 | `eval_shard_002_of_005.jsonl:line_49` | **Юридичні гарантії** | pravoznavstvo | 9 | гарантія, захід, здійснення, охорона | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 108 | 777 | `eval_shard_002_of_005.jsonl:line_39` | **Закон** | pravoznavstvo | 9 | акт, орган, сфера | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 109 | 777 | `eval_shard_002_of_005.jsonl:line_3` | **Обмежена монархія** | pravoznavstvo | 9 | монархія, правління, монарх, парламент | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 110 | 777 | `eval_shard_002_of_005.jsonl:line_48` | **Прямокутні координати** | heohrafiya | 8 | координата, система, вісь, меридіан | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 111 | 777 | `eval_shard_003_of_005.jsonl:line_39` | **Вичерпні природні ресурси** | heohrafiya | 8 | ресурс, зменшення, зникнення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 112 | 777 | `eval_shard_003_of_005.jsonl:line_20` | **Умови укладення шлюбу** | pravoznavstvo | 9 | закон, укладення, шлюб, вимога | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 113 | 777 | `eval_shard_003_of_005.jsonl:line_51` | **Об'єм тіла** | pryroda | 5 | об'єм, тіло | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 114 | 777 | `eval_shard_003_of_005.jsonl:line_13` | **Метеочутливість** | heohrafiya | 8 | організм, зміна | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 115 | 777 | `eval_shard_003_of_005.jsonl:line_44` | **Цінності** | hromadianska | 8 | переконання, суспільство | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 116 | 777 | `eval_shard_004_of_005.jsonl:line_25` | **Свобода слова** | hromadianska | 8 | право, засіб | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 117 | 777 | `eval_shard_004_of_005.jsonl:line_12` | **Громадянство** | hromadianska | 8 | особа, держава, вияв, право | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 118 | 777 | `eval_shard_004_of_005.jsonl:line_40` | **Джерела інформації** | ukrmova | 8 | телеканал, газета, вебсайт, мережа | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 119 | 777 | `eval_shard_004_of_005.jsonl:line_34` | **Криптовалюти та цифрові гроші** | finansova | 8 | криптовалюта, технологія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 120 | 777 | `eval_shard_004_of_005.jsonl:line_39` | **Водосховища** | ukrmova | 8 | водойма, нагромадження | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 121 | 777 | `eval_shard_005_of_005.jsonl:line_4` | **Іконостас** | mystetstvo | 8 | ікона, храм, обряд, вівтар | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 122 | 777 | `eval_shard_005_of_005.jsonl:line_50` | **Колектив** | etyka | 6 | інтерес, дія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 123 | 777 | `eval_shard_005_of_005.jsonl:line_20` | **Банк ідей** | tekhnolohiyi | 8 | ідея, інструмент, змога, розв'язання | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 124 | 777 | `eval_shard_005_of_005.jsonl:line_8` | **Мариніст** | mystetstvo | 8 | зображення, мор | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 125 | 777 | `eval_shard_005_of_005.jsonl:line_39` | **Утиск** | etyka | 6 | особа, атмосфера | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 126 | 777 | `sft_shard_011_of_150.jsonl:line_219` | **Метали** | khimiya | 7 | залізо, алюміній, цинк, магній | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 127 | 777 | `sft_shard_121_of_150.jsonl:line_74` | **Критичне мислення** | zdorovia | 6 | мислення, здатність, доцільність, варіант | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 128 | 777 | `sft_shard_046_of_150.jsonl:line_319` | **Макроекономічні показники** | ekonomika | 11 | ціна, виробництво, показник, динаміка | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 129 | 777 | `sft_shard_080_of_150.jsonl:line_160` | **Алюміній** | khimiya | 11 | оксид, метал, сполука | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 130 | 777 | `sft_shard_053_of_150.jsonl:line_5` | **Масовий відсоток** | algebra | 8 | частка, відсоток, маса, речовина | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 131 | 777 | `sft_shard_067_of_150.jsonl:line_23` | **Гомологічна різниця** | khimiya | 9 | різниця, атом, склад, молекула | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 132 | 777 | `sft_shard_110_of_150.jsonl:line_154` | **Гарнітура** | ya_doslidzhuiu_svit | 3 | набір, шрифт, дизайн | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 133 | 777 | `sft_shard_021_of_150.jsonl:line_120` | **Головне в програмуванні** | algebra | 7 | послідовність, програмування, алгоритм | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 134 | 777 | `sft_shard_143_of_150.jsonl:line_393` | **Пропозиція** | finansova | 9 | товар, виробник, ціна | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 135 | 777 | `sft_shard_125_of_150.jsonl:line_122` | **Теза й аргументи** | ukrmova | 10 | теза, аргумент, судження, речення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 136 | 777 | `sft_shard_112_of_150.jsonl:line_216` | **Похідні способи набуття права власності** | pravoznavstvo | 11 | набуття, власність, отримання, річ | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 137 | 777 | `sft_shard_033_of_150.jsonl:line_290` | **Варни** | istoriya | 6 | суспільство, належність, народження | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 138 | 777 | `sft_shard_077_of_150.jsonl:line_154` | **Жанр** | mystetstvo | 6 | твір, сюжет, рішення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 139 | 777 | `sft_shard_069_of_150.jsonl:line_370` | **Активність у шкільному житті** | hromadianska | 9 | активність, простір | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 140 | 777 | `sft_shard_106_of_150.jsonl:line_277` | **Екосистема** | biolohiya | 9 | організм, існування | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 141 | 777 | `sft_shard_128_of_150.jsonl:line_131` | **Право власності** | finansova | 9 | право, власність, закон, розсуд | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 142 | 777 | `sft_shard_034_of_150.jsonl:line_408` | **Зоря** | astronomiya | 11 | тяжіння, енергія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 143 | 777 | `sft_shard_013_of_150.jsonl:line_218` | **Стриманість** | etyka | 5 | гамування, бажання, почуття, пристрасть | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 144 | 777 | `sft_shard_150_of_150.jsonl:line_399` | **Спостереження** | fizyka | 10 | сприйняття, природа, одержання, аналіз | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 145 | 777 | `sft_shard_071_of_150.jsonl:line_368` | **Внутрішня відповідальність** | etyka | 5 | совість, відповідальність, змога, результат | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 146 | 777 | `sft_shard_032_of_150.jsonl:line_431` | **Управління конфліктом** | etyka | 5 | управління, конфлікт, ситуація | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 147 | 777 | `sft_shard_079_of_150.jsonl:line_438` | **Катран** | ya_doslidzhuiu_svit | 3 | акула, довжина, тіло, метр | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 148 | 777 | `sft_shard_029_of_150.jsonl:line_239` | **Господарське право** | pravoznavstvo | 11 | право, норма, сфера, управління | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 149 | 777 | `sft_shard_113_of_150.jsonl:line_307` | **Сфера** | matematyka | 11 | тіло, відстань | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 150 | 777 | `sft_shard_060_of_150.jsonl:line_123` | **Льодовики** | heohrafiya | 6 | нагромадження, лід, суходіл | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |

## Detailed Record Inspection (Full Text)

### Record 1 (Seed 42): Навіть одяг (eval_shard_001_of_005.jsonl:line_26)
- **Subject / Grade:** vsesvitnia (Grade 8)
- **Concept:** `Навіть одяг` (Citation form: ✅)
- **Scientific Terminology:** `['вбрання', 'тварина', 'убір', 'пояс']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Навіть одяг – вишиті на вбранні квіти чи тварини, головний убір чи пояс – мав підкреслювати становище людини.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 2 (Seed 42): Верхня палата (eval_shard_001_of_005.jsonl:line_24)
- **Subject / Grade:** vsesvitnia (Grade 8)
- **Concept:** `Верхня палата` (Citation form: ✅)
- **Scientific Terminology:** `['палата', 'сенат', 'представник', 'духовенство', 'магнат']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Верхня палата – сенат – складалася з представників вищого духовенства та магнатів, зайнятих на високих державних посадах.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 3 (Seed 42): Колоніалізм (eval_shard_001_of_005.jsonl:line_20)
- **Subject / Grade:** vsesvitnia (Grade 8)
- **Concept:** `Колоніалізм` (Citation form: ✅)
- **Scientific Terminology:** `['підкорення', 'країна', 'ресурс', 'праця', 'населення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Колоніалізм – підкорення однією країною іншої з метою використання її ресурсів, праці місцевого населення та його культурної асиміляції, а також політичного контролю.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 4 (Seed 42): Революція (eval_shard_001_of_005.jsonl:line_12)
- **Subject / Grade:** vsesvitnia (Grade 8)
- **Concept:** `Революція` (Citation form: ✅)
- **Scientific Terminology:** `['переворот', 'суспільство', 'зміна', 'перетворення', 'удосконалення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Революція – докорінний переворот у житті суспільства, який супроводжується зміною влади; різкі зміни в якій-небудь галузі, що приводить до істотних перетворень, удосконалення чого-небудь.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 5 (Seed 42): Рівносильні нерівності (eval_shard_001_of_005.jsonl:line_5)
- **Subject / Grade:** algebra (Grade 9)
- **Concept:** `Рівносильні нерівності` (Citation form: ✅)
- **Scientific Terminology:** `['нерівність', 'множина', "розв'язок"]` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Нерівності називають рівносильними, якщо вони мають одну й ту саму множину розв'язків.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 6 (Seed 42): Систематизація нормативних актів (eval_shard_002_of_005.jsonl:line_45)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Систематизація нормативних актів` (Citation form: ✅)
- **Scientific Terminology:** `['систематизація', 'акт', 'упорядкування', 'вдосконалення', 'приведення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Систематизація нормативних актів — це діяльність з їх упорядкування та вдосконалення, приведення до певної внутрішньої узгодженості через створення нових документів або збірників.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 7 (Seed 42): Правомірна поведінка (eval_shard_002_of_005.jsonl:line_33)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Правомірна поведінка` (Citation form: ✅)
- **Scientific Terminology:** `['поведінка', 'припис', 'норма', 'держава']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Правомірна поведінка — поведінка, яка відповідає приписам правових норм та охороняється державою.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 8 (Seed 42): Пульс (eval_shard_002_of_005.jsonl:line_14)
- **Subject / Grade:** biolohiya (Grade 8)
- **Concept:** `Пульс` (Citation form: ✅)
- **Scientific Terminology:** `['показник', 'ритмічність', 'скорочення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Пульс — це показник, який свідчить про ритмічність серцевих скорочень та їхню силу.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 9 (Seed 42): Нейронауки (eval_shard_002_of_005.jsonl:line_10)
- **Subject / Grade:** biolohiya (Grade 8)
- **Concept:** `Нейронауки` (Citation form: ✅)
- **Scientific Terminology:** `['галузь', 'знання', 'вивчення', 'система', 'пошук']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Нейронауки — це сукупність галузей знань, що стосуються вивчення нервової системи та пошуку шляхів лікування неврологічних і психіатричних захворювань.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 10 (Seed 42): Передня камера (eval_shard_002_of_005.jsonl:line_20)
- **Subject / Grade:** biolohiya (Grade 8)
- **Concept:** `Передня камера` (Citation form: ✅)
- **Scientific Terminology:** `['простір', 'оболонка', 'камера', 'райдужка', 'кришталик']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Простір між рогівкою та райдужною оболонкою називають передньою камерою, а простір між райдужкою та кришталиком — задньою камерою.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 11 (Seed 42): Географічний простір (eval_shard_003_of_005.jsonl:line_45)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Географічний простір` (Citation form: ✅)
- **Scientific Terminology:** `['простір', "об'єкт", 'територія']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Географічний простір – сукупність зв'язків між різними географічними об'єктами, які розміщені на конкретній території і розвиваються у просторі й часі.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 12 (Seed 42): Степ (eval_shard_003_of_005.jsonl:line_31)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Степ` (Citation form: ✅)
- **Scientific Terminology:** `['зона', 'держава', 'підзона']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Степ – це єдина природна зона держави, яка поділяється на три підзони: північностепову, середньостепову та південностепову.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 13 (Seed 42): Кліматичні ресурси (eval_shard_003_of_005.jsonl:line_41)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Кліматичні ресурси` (Citation form: ✅)
- **Scientific Terminology:** `['ресурс', 'енергетика']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Кліматичні ресурси – основа відновлюваної енергетики.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 14 (Seed 42): Позов (eval_shard_003_of_005.jsonl:line_12)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Позов` (Citation form: ✅)
- **Scientific Terminology:** `['закон', 'звернення', 'особа', 'суд', 'прохання']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Позов — звернення особи до суду з проханням про розгляд спору та захист її прав, що охороняються законом.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 15 (Seed 42): Меліорація (eval_shard_003_of_005.jsonl:line_19)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Меліорація` (Citation form: ✅)
- **Scientific Terminology:** `['дія', 'покращення', 'родючість', 'ґрунт']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Меліорація – цілеспрямовані дії, направлені на покращення родючості ґрунтів.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 16 (Seed 42): Гімн (eval_shard_004_of_005.jsonl:line_50)
- **Subject / Grade:** mystetstvo (Grade 8)
- **Concept:** `Гімн` (Citation form: ✅)
- **Scientific Terminology:** `['характер', 'прославлення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Гімн — пісня урочистого характеру для прославлення божества.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 17 (Seed 42): Обмін (eval_shard_004_of_005.jsonl:line_29)
- **Subject / Grade:** ekonomika (Grade 10)
- **Concept:** `Обмін` (Citation form: ✅)
- **Scientific Terminology:** `['рух', 'товар', 'власник']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Обмін — це рух товарів від одного власника до іншого.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 18 (Seed 42): Громадянський обов'язок (eval_shard_004_of_005.jsonl:line_6)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Громадянський обов'язок` (Citation form: ✅)
- **Scientific Terminology:** `["обов'язок", 'громадянин', 'країна', 'закон', 'норма']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Громадянський обов'язок – це обов'язок, який мають всі громадяни країни відповідно до законів і моральних норм.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 19 (Seed 42): Демократія (eval_shard_004_of_005.jsonl:line_14)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Демократія` (Citation form: ✅)
- **Scientific Terminology:** `['крок', 'розвиток', 'система']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Партисипативна демократія є важливим кроком уперед у розвитку демократичних систем.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 20 (Seed 42): Піктографічне письмо (eval_shard_004_of_005.jsonl:line_38)
- **Subject / Grade:** ukrmova (Grade 8)
- **Concept:** `Піктографічне письмо` (Citation form: ✅)
- **Scientific Terminology:** `['письмо', 'комунікація', 'значок', 'малюнок', 'передача']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Піктографічне письмо – це старовинний спосіб комунікації, який використовує значки або малюнки для передачі повідомлення.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 21 (Seed 42): Авторитет (eval_shard_005_of_005.jsonl:line_49)
- **Subject / Grade:** etyka (Grade 6)
- **Concept:** `Авторитет` (Citation form: ✅)
- **Scientific Terminology:** `['переконання', 'поведінка', 'особа', 'організація']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Авторитет — загальновизнаний вплив, який здійснюють на переконання та поведінку людей інші особи або організації.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 22 (Seed 42): Культура (eval_shard_005_of_005.jsonl:line_30)
- **Subject / Grade:** tekhnolohiyi (Grade 8)
- **Concept:** `Культура` (Citation form: ✅)
- **Scientific Terminology:** `['частота', 'відвідування', 'постановка', 'виставка', 'оболонка']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Культура – це не лише частота відвідування театральних постановок і виставок, не просто гарна оболонка.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 23 (Seed 42): Декор (eval_shard_005_of_005.jsonl:line_26)
- **Subject / Grade:** tekhnolohiyi (Grade 8)
- **Concept:** `Декор` (Citation form: ✅)
- **Scientific Terminology:** `['система', 'елемент', 'призначення', 'функція']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Декор — художня система, сукупність оздоблювальних елементів, які не мають практичного призначення, однак виконують естетичну функцію.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 24 (Seed 42): Методи проєктування (eval_shard_005_of_005.jsonl:line_21)
- **Subject / Grade:** tekhnolohiyi (Grade 8)
- **Concept:** `Методи проєктування` (Citation form: ✅)
- **Scientific Terminology:** `['проєктування', 'дія', "об'єкт"]` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Методи проєктування — це дії, до яких вдаються в процесі проєктування для створення нового об'єкта.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 25 (Seed 42): Громадянські обов'язки (eval_shard_005_of_005.jsonl:line_37)
- **Subject / Grade:** etyka (Grade 6)
- **Concept:** `Громадянські обов'язки` (Citation form: ✅)
- **Scientific Terminology:** `["обов'язок", 'норма', 'держава', 'ряд', 'громадянин']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Громадянські обов'язки — закріплений правовими нормами держави ряд дій, які громадяни мають безумовно виконувати.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 26 (Seed 42): Монети (sft_shard_135_of_150.jsonl:line_93)
- **Subject / Grade:** istoriya (Grade 5)
- **Concept:** `Монети` (Citation form: ✅)
- **Scientific Terminology:** `['змога', 'розвиток', 'торгівля', "зв'язка", 'народ']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Монети — це особливі речові джерела, які дають змогу дізнатися про розвиток торгівлі та торговельні зв'язки між різними народами.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 27 (Seed 42): Основний принцип життя аристократів (sft_shard_015_of_150.jsonl:line_369)
- **Subject / Grade:** zarlit (Grade 10)
- **Concept:** `Основний принцип життя аристократів` (Citation form: ✅)
- **Scientific Terminology:** `['принцип', 'аристократ', 'лицемірство', 'шанування', 'традиція']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Основний принцип життя аристократів – лицемірство: нещире шанування традицій, монархії, удавані побожність і пристойність.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 28 (Seed 42): Державний устрій (sft_shard_058_of_150.jsonl:line_349)
- **Subject / Grade:** heohrafiya (Grade 9)
- **Concept:** `Державний устрій` (Citation form: ✅)
- **Scientific Terminology:** `['устрій', 'організація', 'держава']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Державний устрій – це адміністративно-територіальна організація держави.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 29 (Seed 42): Гідроліз солей (sft_shard_074_of_150.jsonl:line_211)
- **Subject / Grade:** khimiya (Grade 11)
- **Concept:** `Гідроліз солей` (Citation form: ✅)
- **Scientific Terminology:** `['кислота', 'сіль', 'гідроліз', 'взаємодія', 'йон']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Гідроліз солей — це хімічна взаємодія йонів солі з водою, у результаті якої утворюється слабкий електроліт (кислота або основа).» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 30 (Seed 42): Аеробне дихання (sft_shard_103_of_150.jsonl:line_460)
- **Subject / Grade:** pryroda (Grade 8)
- **Concept:** `Аеробне дихання` (Citation form: ✅)
- **Scientific Terminology:** `['дихання', 'участь', 'кисень', 'окиснення', 'речовина']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Аеробне дихання — це процес, під час якого за участі кисню відбувається окиснення органічних речовин з виділенням енергії.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 31 (Seed 42): Ідеологія (sft_shard_003_of_150.jsonl:line_37)
- **Subject / Grade:** vsesvitnia (Grade 9)
- **Concept:** `Ідеологія` (Citation form: ✅)
- **Scientific Terminology:** `['ідея', 'переконання', 'цінність', 'бачення', 'устрій']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Ідеологія — сукупність ідей, поглядів, переконань та цінностей, які пояснюють світ, пропонують бачення бажаного суспільного устрою й визначають цілі та шляхи для колективних дій.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 32 (Seed 42): Головоногі (sft_shard_048_of_150.jsonl:line_54)
- **Subject / Grade:** biolohiya (Grade 7)
- **Concept:** `Головоногі` (Citation form: ✅)
- **Scientific Terminology:** `['молюск', 'тіло', 'голова']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Головоногі – група молюсків, які мають симетричне тіло з добре розвиненими головою, тулубом і щупальцями.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 33 (Seed 42): Жерці (sft_shard_012_of_150.jsonl:line_387)
- **Subject / Grade:** istoriya (Grade 7)
- **Concept:** `Жерці` (Citation form: ✅)
- **Scientific Terminology:** `['особа', 'ритуал', 'богослужіння', 'релігія']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Жерці — особи, що здійснювали ритуали богослужіння у ранніх релігіях.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 34 (Seed 42): Грант (sft_shard_134_of_150.jsonl:line_384)
- **Subject / Grade:** finansova (Grade 9)
- **Concept:** `Грант` (Citation form: ✅)
- **Scientific Terminology:** `['особа', 'організація', 'бізнес', 'реалізація', 'проєкт']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Грант — це гроші, які надають фізичним особам, організаціям чи бізнесам для реалізації певного проєкту, і їх не потрібно повертати.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 35 (Seed 42): Комбінаторика (sft_shard_046_of_150.jsonl:line_17)
- **Subject / Grade:** matematyka (Grade 11)
- **Concept:** `Комбінаторика` (Citation form: ✅)
- **Scientific Terminology:** `['вибір', 'розміщення', 'елемент', 'множина']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Комбінаторика — розділ математики, у якому вивчають способи вибору та розміщення елементів деякої скінченної множини на основі певних умов.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 36 (Seed 42): Ядерні реакції (sft_shard_002_of_150.jsonl:line_255)
- **Subject / Grade:** fizyka (Grade 11)
- **Concept:** `Ядерні реакції` (Citation form: ✅)
- **Scientific Terminology:** `['реакція', 'перетворення', 'ядро', 'взаємодія', 'частинка']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Ядерні реакції — процес перетворення атомних ядер унаслідок їх взаємодії з елементарними частинками або з іншими ядрами.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 37 (Seed 42): Материки (sft_shard_079_of_150.jsonl:line_273)
- **Subject / Grade:** ya_doslidzhuiu_svit (Grade 4)
- **Concept:** `Материки` (Citation form: ✅)
- **Scientific Terminology:** `['ділянка', 'суходіл', 'вода']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Материки — це великі ділянки суходолу, з усіх сторін оточені водою.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 38 (Seed 42): Волонтерство (sft_shard_044_of_150.jsonl:line_277)
- **Subject / Grade:** hromadianska (Grade 9)
- **Concept:** `Волонтерство` (Citation form: ✅)
- **Scientific Terminology:** `['дія', 'енергія', 'вміння']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Волонтерство — це дія, коли ти даруєш свій час, енергію та вміння.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 39 (Seed 42): Вигуки (sft_shard_150_of_150.jsonl:line_131)
- **Subject / Grade:** ukrmova (Grade university)
- **Concept:** `Вигуки` (Citation form: ✅)
- **Scientific Terminology:** `['розряд', 'функція', 'емоція', 'волевиявлення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Вигуки – це особливий розряд слів, що не мають номінативної функції, не служать для граматичного зв'язку між словами, а безпосередньо виражають різні емоції й волевиявлення.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 40 (Seed 42): Небо (sft_shard_131_of_150.jsonl:line_477)
- **Subject / Grade:** ukrmova (Grade 6)
- **Concept:** `Небо` (Citation form: ✅)
- **Scientific Terminology:** `['атмосфера', 'поверхня', 'загал', "об'єкт"]` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Небо — частина атмосфери космічного простору, видима з поверхні Землі або загалом будь-якого астрономічного об'єкта.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 41 (Seed 42): Податок (sft_shard_121_of_150.jsonl:line_171)
- **Subject / Grade:** pravoznavstvo (Grade 11)
- **Concept:** `Податок` (Citation form: ✅)
- **Scientific Terminology:** `['закон', 'орган', 'платіж', 'бюджет', 'фонд']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Податок — це встановлений органом законодавчої влади обов'язковий платіж до бюджету відповідного рівня або державного цільового фонду, що здійснюється платниками в порядку й на умовах, які визначені законами України про оподаткування.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 42 (Seed 42): Мода вибірки (sft_shard_053_of_150.jsonl:line_255)
- **Subject / Grade:** algebra (Grade 8)
- **Concept:** `Мода вибірки` (Citation form: ✅)
- **Scientific Terminology:** `['мода', 'вибірка', 'ряд']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Мода вибірки — це значення вибірки, яке трапляється у варіаційному ряді найчастіше.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 43 (Seed 42): Образ царя (sft_shard_039_of_150.jsonl:line_210)
- **Subject / Grade:** zarlit (Grade 9)
- **Concept:** `Образ царя` (Citation form: ✅)
- **Scientific Terminology:** `['образ', 'алегорія', 'душа', 'злам', 'вибух']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Образ царя – це алегорія душі на межі зламу або емоційного вибуху, що страждає і прагне спокою та умиротворення.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 44 (Seed 42): Покарання (sft_shard_076_of_150.jsonl:line_314)
- **Subject / Grade:** etyka (Grade 5)
- **Concept:** `Покарання` (Citation form: ✅)
- **Scientific Terminology:** `['уникнення', 'спілкування', 'небажання']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Покарання — уникнення спілкування з людиною, яка порушує правила, небажання з нею грати та працювати.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 45 (Seed 42): Сталий розвиток (sft_shard_141_of_150.jsonl:line_141)
- **Subject / Grade:** pryroda (Grade 8)
- **Concept:** `Сталий розвиток` (Citation form: ✅)
- **Scientific Terminology:** `['розвиток', 'концепція', 'змога', 'баланс', 'задоволення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Сталий розвиток — це концепція, що дає змогу знайти баланс між задоволенням потреб сучасності та захистом інтересів майбутніх поколінь, включаючи їх потребу в здоровому довкіллі.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 46 (Seed 42): Авторитаризм (sft_shard_010_of_150.jsonl:line_451)
- **Subject / Grade:** vsesvitnia (Grade 10)
- **Concept:** `Авторитаризм` (Citation form: ✅)
- **Scientific Terminology:** `['лад', 'режим', 'управління', 'апарат', 'демагогія']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Авторитаризм — державний лад, для якого характерні режим особистої влади, диктаторські методи управління за допомогою репресивного апарату й соціальної демагогії.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 47 (Seed 42): Сузір'я (sft_shard_142_of_150.jsonl:line_75)
- **Subject / Grade:** astronomiya (Grade 11)
- **Concept:** `Сузір'я` (Citation form: ✅)
- **Scientific Terminology:** `['ділянка', 'сфера', 'зручність', 'орієнтування', 'небо']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Сузір'я — ділянки, на які поділена небесна сфера для зручності орієнтування на зоряному небі.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 48 (Seed 42): Сучасний танець (sft_shard_108_of_150.jsonl:line_289)
- **Subject / Grade:** mystetstvo (Grade 5)
- **Concept:** `Сучасний танець` (Citation form: ✅)
- **Scientific Terminology:** `['танець', 'рух', 'ритм', 'образ']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Сучасний танець — це інші рухи, інша музика та ритми, інші образи.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 49 (Seed 42): Вегетативні пагони (sft_shard_018_of_150.jsonl:line_201)
- **Subject / Grade:** biolohiya (Grade 7)
- **Concept:** `Вегетативні пагони` (Citation form: ✅)
- **Scientific Terminology:** `['пагін', 'гілка']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Вегетативні пагони – зелені, з бічними гілками, розвиваються влітку й активно фотосинтезують.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 50 (Seed 42): Основа піраміди (sft_shard_071_of_150.jsonl:line_432)
- **Subject / Grade:** matematyka (Grade 11)
- **Concept:** `Основа піраміди` (Citation form: ✅)
- **Scientific Terminology:** `['піраміда', 'трикутник', 'катет']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Основа піраміди — прямокутний трикутник із катетами 6 см і 8 см.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 51 (Seed 123): Вуглекислий газ (eval_shard_001_of_005.jsonl:line_37)
- **Subject / Grade:** khimiya (Grade 8)
- **Concept:** `Вуглекислий газ` (Citation form: ✅)
- **Scientific Terminology:** `['газ', 'речовина']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Вуглекислий газ — речовина, про яку часто згадують як у школі, так і в щоденному житті.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 52 (Seed 123): Хімічний зв'язок (eval_shard_001_of_005.jsonl:line_49)
- **Subject / Grade:** khimiya (Grade 8)
- **Concept:** `Хімічний зв'язок` (Citation form: ✅)
- **Scientific Terminology:** `['взаємодія', 'атом', 'стійкість', 'частинка', 'молекула']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Хімічний зв'язок — це взаємодія атомів, що зумовлює стійкість багатоатомних частинок (молекул, йонів, кристалів).» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 53 (Seed 123): Бароко (eval_shard_001_of_005.jsonl:line_30)
- **Subject / Grade:** vsesvitnia (Grade 8)
- **Concept:** `Бароко` (Citation form: ✅)
- **Scientific Terminology:** `['стиль', 'мистецтво']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Бароко – стиль, що переважав у мистецтві Європи з кінця XVI до середини XVIII ст.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 54 (Seed 123): Суверенітет (eval_shard_001_of_005.jsonl:line_48)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Суверенітет` (Citation form: ✅)
- **Scientific Terminology:** `['держава', 'зміст', 'втручання', 'організація', 'особа']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Суверенітет — політико-правова властивість держави, зміст якої полягає в її праві самостійно вирішувати внутрішні та зовнішні політичні питання без втручання інших держав, організацій, осіб.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 55 (Seed 123): Механічна енергія (eval_shard_001_of_005.jsonl:line_21)
- **Subject / Grade:** fizyka (Grade 8)
- **Concept:** `Механічна енергія` (Citation form: ✅)
- **Scientific Terminology:** `['енергія', 'міра', 'рух', 'взаємодія', 'тіло']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Механічна енергія — це фізична величина, яка є мірою руху та взаємодії тіл.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 56 (Seed 123): Спинний мозок (eval_shard_002_of_005.jsonl:line_8)
- **Subject / Grade:** biolohiya (Grade 8)
- **Concept:** `Спинний мозок` (Citation form: ✅)
- **Scientific Terminology:** `['мозок', 'тяж', 'канал', 'хребет']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Спинний мозок — це циліндричний тяж завтовшки приблизно 1 см, розташований у спинномозковому каналі хребта.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 57 (Seed 123): Особисті гарантії (eval_shard_002_of_005.jsonl:line_47)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Особисті гарантії` (Citation form: ✅)
- **Scientific Terminology:** `['гарантія', 'громадянин', 'захист', 'свобода', 'інтерес']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Особисті гарантії — власні можливості людини й громадянина щодо захисту своїх прав, свобод, законних інтересів та обов'язків.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 58 (Seed 123): Юридична відповідальність (eval_shard_002_of_005.jsonl:line_37)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Юридична відповідальність` (Citation form: ✅)
- **Scientific Terminology:** `['правопорушення', 'відповідальність', 'застосування', 'особа', 'захід']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Юридична відповідальність — застосування до винної особи заходів державного примусу за вчинене нею правопорушення.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 59 (Seed 123): Звичайне скло (eval_shard_002_of_005.jsonl:line_2)
- **Subject / Grade:** khimiya (Grade 8)
- **Concept:** `Звичайне скло` (Citation form: ✅)
- **Scientific Terminology:** `['оксид', 'скло', 'речовина', 'силіцій', 'склад']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Звичайне скло — аморфна речовина, але із часом силіцій(IV) оксид у його складі стає кристалічним.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 60 (Seed 123): Суб'єкти правовідносин (eval_shard_002_of_005.jsonl:line_23)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Суб'єкти правовідносин` (Citation form: ✅)
- **Scientific Terminology:** `["суб'єкт", 'індивід', 'організація', 'особа', 'спільнота']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Суб'єкти правовідносин — окремі індивіди, організації (юридичні особи), певна соціальна спільнота або держава загалом, які відповідно до норм права є носіями суб'єктивних юридичних прав і обов'язків.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 61 (Seed 123): Кримінальне право (eval_shard_003_of_005.jsonl:line_34)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Кримінальне право` (Citation form: ✅)
- **Scientific Terminology:** `['правопорушення', 'право', 'система', 'норма', 'діяння']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Кримінальне право — система юридичних норм, що встановлюють, які суспільно небезпечні діяння є кримінальними правопорушеннями та які покарання передбачені за їх вчинення.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 62 (Seed 123): Слідчий (eval_shard_003_of_005.jsonl:line_10)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Слідчий` (Citation form: ✅)
- **Scientific Terminology:** `['особа', 'орган', 'розслідування']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Слідчий — службова особа відповідного органу досудового розслідування.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 63 (Seed 123): Шлюб (eval_shard_003_of_005.jsonl:line_22)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Шлюб` (Citation form: ✅)
- **Scientific Terminology:** `['союз', 'жінка', 'чоловік', 'орган', 'реєстрація']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Шлюб — сімейний союз жінки та чоловіка, зареєстрований в органі реєстрації актів цивільного стану.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 64 (Seed 123): Суддя (eval_shard_003_of_005.jsonl:line_8)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Суддя` (Citation form: ✅)
- **Scientific Terminology:** `['правопорушення', 'особа', 'право', "ім'я", 'держава']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Суддя — посадова особа, якій надано право від імені держави здійснювати правосуддя шляхом розгляду в судовому засіданні кримінальних, цивільних справ, про адміністративні правопорушення та ухвалювати відповідне судове рішення.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 65 (Seed 123): Громадянська освіта (eval_shard_003_of_005.jsonl:line_42)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Громадянська освіта` (Citation form: ✅)
- **Scientific Terminology:** `['освіта', 'знання', 'закон', 'уміння', 'громадянин']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Громадянська освіта – це не лише знання про закони та права, але й уміння бути активним громадянином / громадянкою, здатним / здатною впливати на події навколо себе.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 66 (Seed 123): Право (eval_shard_004_of_005.jsonl:line_18)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Право` (Citation form: ✅)
- **Scientific Terminology:** `['норма', 'держава', 'регулювання']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Право – це сукупність загальнообов'язкових норм, що встановлюються або визнаються державою для регулювання суспільних відносин.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 67 (Seed 123): Смальта (eval_shard_004_of_005.jsonl:line_51)
- **Subject / Grade:** mystetstvo (Grade 8)
- **Concept:** `Смальта` (Citation form: ✅)
- **Scientific Terminology:** `['скло', 'кубик', 'пластинка', 'мозаїка']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Смальта — кольорове напівпрозоре скло у вигляді кубиків або пластинок, призначене для створення мозаїк.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 68 (Seed 123): Забобони (eval_shard_004_of_005.jsonl:line_7)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Забобони` (Citation form: ✅)
- **Scientific Terminology:** `['упередження', 'індивід', 'реальність', 'подія']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Забобони – це упередження, що полягає в тому, що індивід приймає за реальність невідомі сили, здатні провіщати події чи впливати на них.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 69 (Seed 123): Верлібр (eval_shard_004_of_005.jsonl:line_37)
- **Subject / Grade:** ukrlit (Grade 8)
- **Concept:** `Верлібр` (Citation form: ✅)
- **Scientific Terminology:** `['вірш', 'довжина', 'наголос']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Верлібр – вірш, у якому немає рим, а рядки мають різну довжину й різну кількість наголосів.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 70 (Seed 123): Місцевий колорит (eval_shard_004_of_005.jsonl:line_44)
- **Subject / Grade:** zarlit (Grade 8)
- **Concept:** `Місцевий колорит` (Citation form: ✅)
- **Scientific Terminology:** `['колорит', 'твір', 'елемент', 'побут', 'традиція']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Місцевий колорит – літературний прийом, що упроваджує у твір елементи побуту, традицій, звичаїв, природи, історії тощо, якими характеризується життя певної етнічної групи або іншої спільноти на певній території.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 71 (Seed 123): Конфлікт (eval_shard_005_of_005.jsonl:line_47)
- **Subject / Grade:** etyka (Grade 6)
- **Concept:** `Конфлікт` (Citation form: ✅)
- **Scientific Terminology:** `['зіткнення', 'інтерес', 'оцінка', 'цінність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Конфлікт — зіткнення протилежних інтересів, поглядів, оцінок, цінностей.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 72 (Seed 123): Соціальна відповідальність бізнесу (eval_shard_005_of_005.jsonl:line_12)
- **Subject / Grade:** zdorovia (Grade 8)
- **Concept:** `Соціальна відповідальність бізнесу` (Citation form: ✅)
- **Scientific Terminology:** `['відповідальність', 'бізнес', 'практика', 'участь', 'підприємець']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Соціальна відповідальність бізнесу — стратегічна практика, спрямована на активну участь підприємців у розв'язанні соціальних проблем.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 73 (Seed 123): Рапсодія (eval_shard_005_of_005.jsonl:line_7)
- **Subject / Grade:** mystetstvo (Grade 8)
- **Concept:** `Рапсодія` (Citation form: ✅)
- **Scientific Terminology:** `['твір', 'характер']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Рапсодія — інструментальний твір фантазійного характеру на народні теми.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 74 (Seed 123): Взаємоповага (eval_shard_005_of_005.jsonl:line_45)
- **Subject / Grade:** etyka (Grade 6)
- **Concept:** `Взаємоповага` (Citation form: ✅)
- **Scientific Terminology:** `['повага', 'виявлення', 'почуття', 'взаємність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Взаємоповага — виявлення людьми поваги одне до одного, що ґрунтується на почутті взаємності.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 75 (Seed 123): Художня фотографія (eval_shard_005_of_005.jsonl:line_24)
- **Subject / Grade:** tekhnolohiyi (Grade 8)
- **Concept:** `Художня фотографія` (Citation form: ✅)
- **Scientific Terminology:** `['фотографія', 'мистецтво', 'відображення', 'дійсність', 'площина']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Художня фотографія – це вид мистецтва, в якому художнє відображення дійсності на двовимірній площині здійснюють за допомогою фотографічної техніки.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 76 (Seed 123): Виготовлення моделей з гофрокартону (sft_shard_053_of_150.jsonl:line_227)
- **Subject / Grade:** tekhnolohiyi (Grade 6)
- **Concept:** `Виготовлення моделей з гофрокартону` (Citation form: ✅)
- **Scientific Terminology:** `['виготовлення', 'модель', 'гофрокартон', 'заняття', 'змога']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Виготовлення моделей з гофрокартону — захопливе заняття, що дає змогу людям виявити власні креативні та інженерні навички, створюючи предмети дивовижної конструкції та форми.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 77 (Seed 123): Проектуюча пряма (sft_shard_137_of_150.jsonl:line_148)
- **Subject / Grade:** heometriya (Grade 10)
- **Concept:** `Проектуюча пряма` (Citation form: ✅)
- **Scientific Terminology:** `['площина', 'проекція']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Пряму І називають проектуючою прямою, а площину а - площиною проекції.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 78 (Seed 123): Ошибана (sft_shard_010_of_150.jsonl:line_409)
- **Subject / Grade:** tekhnolohiyi (Grade 5)
- **Concept:** `Ошибана` (Citation form: ✅)
- **Scientific Terminology:** `['виготовлення', 'картина', 'матеріал', 'листя']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Ошибана – виготовлення картин з природних матеріалів (листя, квітів, пуху тощо).» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 79 (Seed 123): Інформаційна структура сайта (sft_shard_127_of_150.jsonl:line_137)
- **Subject / Grade:** informatyka (Grade 11)
- **Concept:** `Інформаційна структура сайта` (Citation form: ✅)
- **Scientific Terminology:** `['структура', 'сайт', 'організація', 'веб-сайт', 'взаємодія']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Інформаційна структура сайта — спосіб організації інформаційних даних на веб-сайті, а також структура взаємодії різних блоків інформації один з одним.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 80 (Seed 123): Неділя (sft_shard_146_of_150.jsonl:line_100)
- **Subject / Grade:** zarlit (Grade 9)
- **Concept:** `Неділя` (Citation form: ✅)
- **Scientific Terminology:** `['ґанок', 'шанування']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Неділя – день, коли люди ходять тут одне до одного… Ніхто не пам'ятає, щоб хтось із сусідів піднявся колись у неділю на ґанок до Редлі й гукнув: „Моє шанування!“.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 81 (Seed 123): Хімічна рівновага (sft_shard_110_of_150.jsonl:line_128)
- **Subject / Grade:** khimiya (Grade 11)
- **Concept:** `Хімічна рівновага` (Citation form: ✅)
- **Scientific Terminology:** `['система', 'реакція', 'швидкість']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Хімічна рівновага — стан хімічної системи, у якій відбувається оборотна реакція, за якого швидкості прямої і зворотної реакцій однакові.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 82 (Seed 123): Висота циліндра (sft_shard_134_of_150.jsonl:line_400)
- **Subject / Grade:** matematyka (Grade 11)
- **Concept:** `Висота циліндра` (Citation form: ✅)
- **Scientific Terminology:** `['висота', 'циліндр', 'перпендикуляр']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Висотою циліндра називається перпендикуляр, проведений із будь-якої точки однієї основи на іншу.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 83 (Seed 123): Бережливість (sft_shard_086_of_150.jsonl:line_283)
- **Subject / Grade:** zdorovia (Grade 7)
- **Concept:** `Бережливість` (Citation form: ✅)
- **Scientific Terminology:** `['піклування', 'майно', 'повага', 'праця', 'товар']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Бережливість — це не лише піклування про своє майно, а й повага до праці тих, хто створює товари й послуги.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 84 (Seed 123): Площа бічної поверхні призми (sft_shard_023_of_150.jsonl:line_424)
- **Subject / Grade:** heometriya (Grade 9)
- **Concept:** `Площа бічної поверхні призми` (Citation form: ✅)
- **Scientific Terminology:** `['площа', 'поверхня', 'призма', 'грань']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Площа бічної поверхні призми — це сума площ усіх її бічних граней.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 85 (Seed 123): Сурядний ряд (sft_shard_078_of_150.jsonl:line_288)
- **Subject / Grade:** ukrmova (Grade university)
- **Concept:** `Сурядний ряд` (Citation form: ✅)
- **Scientific Terminology:** `['ряд', 'компонент', 'функція']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Сурядний ряд – це граматично рівнозначні компоненти, які виконують однакову синтаксичну функцію.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 86 (Seed 123): Змінні зорі (sft_shard_142_of_150.jsonl:line_240)
- **Subject / Grade:** astronomiya (Grade 11)
- **Concept:** `Змінні зорі` (Citation form: ✅)
- **Scientific Terminology:** `['блиск', 'поверхня', 'дія', 'причина', 'затемнення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Змінні зорі називають фізично-змінними, якщо зміни блиску зумовлені процесами, що відбуваються в самій зорі або на її поверхні, і оптичними у випадку, якщо блиск зорі змінюється внаслідок дії зовнішніх щодо неї причин, наприклад під час періодичних затемнень іншою зорею.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 87 (Seed 123): Йонізація газів (sft_shard_038_of_150.jsonl:line_160)
- **Subject / Grade:** fizyka (Grade 11)
- **Concept:** `Йонізація газів` (Citation form: ✅)
- **Scientific Terminology:** `['розпад', 'молекула', 'електрон', 'йонізація', 'газ']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Розпад молекул газу на електрони та йони називають йонізацією газів.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 88 (Seed 123): Прикметник (sft_shard_040_of_150.jsonl:line_370)
- **Subject / Grade:** ukrmova (Grade university)
- **Concept:** `Прикметник` (Citation form: ✅)
- **Scientific Terminology:** `['категорія', 'відмінок']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Прикметник – самостійна повнозначна частина мови, яка виражає статичну ознаку предмета, оформлену синтаксично залежними граматичними категоріями роду, числа і відмінка.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 89 (Seed 123): Стиснення даних (sft_shard_087_of_150.jsonl:line_8)
- **Subject / Grade:** informatyka (Grade 8)
- **Concept:** `Стиснення даних` (Citation form: ✅)
- **Scientific Terminology:** `['файл', 'стиснення', 'перекодування', 'зменшення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Стиснення даних – це процес перекодування даних, який здійснюється з метою зменшення розмірів файлів.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 90 (Seed 123): Світова війна (sft_shard_028_of_150.jsonl:line_86)
- **Subject / Grade:** vsesvitnia (Grade 10)
- **Concept:** `Світова війна` (Citation form: ✅)
- **Scientific Terminology:** `['війна', 'боротьба', 'держава', 'участь', 'більшість']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Світова війна — організована збройна боротьба між державами, у якій брала участь більшість країн світу.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 91 (Seed 123): Ренатурація (sft_shard_067_of_150.jsonl:line_482)
- **Subject / Grade:** biolohiya (Grade 9)
- **Concept:** `Ренатурація` (Citation form: ✅)
- **Scientific Terminology:** `['відновлення', 'структура', 'макромолекула', 'денатурація']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Ренатурація — відновлення просторової структури макромолекул після денатурації.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 92 (Seed 123): Платоспроможність (sft_shard_041_of_150.jsonl:line_119)
- **Subject / Grade:** ekonomika (Grade 11)
- **Concept:** `Платоспроможність` (Citation form: ✅)
- **Scientific Terminology:** `['оцінка', 'позичальник', 'коефіцієнт', 'ліквідність', 'динаміка']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Платоспроможність — оцінка фінансового стану позичальника, коефіцієнтів ліквідності, динаміки статей балансу і фінансових показників. 3. Capital.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 93 (Seed 123): Східна елонгація (sft_shard_051_of_150.jsonl:line_9)
- **Subject / Grade:** astronomiya (Grade 11)
- **Concept:** `Східна елонгація` (Citation form: ✅)
- **Scientific Terminology:** `['елонгація', 'момент', 'положення', 'планета']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Східна елонгація — це момент положення, коли планету видно ліворуч від Сонця ввечері (B1).» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 94 (Seed 123): Ліберальний підхід (sft_shard_096_of_150.jsonl:line_373)
- **Subject / Grade:** hromadianska (Grade 10)
- **Concept:** `Ліберальний підхід` (Citation form: ✅)
- **Scientific Terminology:** `['підхід', 'пояснення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Інший підхід до пояснення свободи слова називають ліберальним, іноді — етичним, або емоційним.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 95 (Seed 123): Декодування повідомлення (sft_shard_090_of_150.jsonl:line_226)
- **Subject / Grade:** informatyka (Grade 8)
- **Concept:** `Декодування повідомлення` (Citation form: ✅)
- **Scientific Terminology:** `['декодування', 'повідомлення', 'отримання']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Декодування повідомлення – це процес отримання початкового повідомлення із закодованого.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 96 (Seed 123): Земля (sft_shard_012_of_150.jsonl:line_21)
- **Subject / Grade:** khimiya (Grade 11)
- **Concept:** `Земля` (Citation form: ✅)
- **Scientific Terminology:** `['дім', 'істота']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Земля — дім для людства та ще для близько 2 млн видів живих істот.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 97 (Seed 123): Бензен (sft_shard_116_of_150.jsonl:line_55)
- **Subject / Grade:** khimiya (Grade 10)
- **Concept:** `Бензен` (Citation form: ✅)
- **Scientific Terminology:** `['сировина', 'промисловість', 'застосування']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Але бензен є найважливішою сировиною для хімічної промисловості, оскільки на його основі добувають багато похідних, що мають широке застосування.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 98 (Seed 123): Черевоногі (sft_shard_025_of_150.jsonl:line_469)
- **Subject / Grade:** biolohiya (Grade 7)
- **Concept:** `Черевоногі` (Citation form: ✅)
- **Scientific Terminology:** `['молюск', 'тіло', 'голова', 'нога']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Черевоногі – це молюски з несиметричним тілом і розвине - ними головою, тулубом і ногою.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 99 (Seed 123): Ґрунт (sft_shard_021_of_150.jsonl:line_480)
- **Subject / Grade:** heohrafiya (Grade 6)
- **Concept:** `Ґрунт` (Citation form: ✅)
- **Scientific Terminology:** `['рослинність', 'родючість']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Ґрунт — це верхній тонкий шар земної кори, який, як правило, покритий рослинністю і має природну родючість.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 100 (Seed 123): Реакція полімеризації (sft_shard_120_of_150.jsonl:line_352)
- **Subject / Grade:** khimiya (Grade 9)
- **Concept:** `Реакція полімеризації` (Citation form: ✅)
- **Scientific Terminology:** `['реакція', 'полімеризація', 'сполучення', 'молекула', 'макромолекула']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Реакція полімеризації — це реакція сполучення багатьох молекул в одну макромолекулу, якісний склад якої однаковий з якісним складом реагента / реагентів.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 101 (Seed 777): Елементарний заряд (eval_shard_001_of_005.jsonl:line_41)
- **Subject / Grade:** khimiya (Grade 8)
- **Concept:** `Елементарний заряд` (Citation form: ✅)
- **Scientific Terminology:** `['заряд', 'електрон', 'одиниця', 'вимірювання']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Електричний заряд електрона називають елементарним, оскільки він найменший із-поміж усіх відомих зарядів і тому його абсолютну величину приймають за одиницю вимірювання заряду.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 102 (Seed 777): Рівні фігури (eval_shard_001_of_005.jsonl:line_13)
- **Subject / Grade:** heometriya (Grade 9)
- **Concept:** `Рівні фігури` (Citation form: ✅)
- **Scientific Terminology:** `['фігура', 'рух', 'образ']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Дві фігури називають рівними, якщо існує рух, при якому одна з даних фігур є образом другої.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 103 (Seed 777): Аграрна революція (eval_shard_001_of_005.jsonl:line_32)
- **Subject / Grade:** vsesvitnia (Grade 8)
- **Concept:** `Аграрна революція` (Citation form: ✅)
- **Scientific Terminology:** `['революція', 'реформування', 'господарство', 'збільшення', 'товарність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Аграрна революція – реформування сільського господарства з метою збільшення його товарності й прибутковості.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 104 (Seed 777): Максимальне значення (eval_shard_001_of_005.jsonl:line_51)
- **Subject / Grade:** khimiya (Grade 8)
- **Concept:** `Максимальне значення` (Citation form: ✅)
- **Scientific Terminology:** `['ступінь', 'окиснення', 'електрон']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Максимальне значення — вищий ступінь окиснення — зазвичай дорівнює числу електронів на зовнішньому рівні.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 105 (Seed 777): В'язкість (eval_shard_001_of_005.jsonl:line_23)
- **Subject / Grade:** fizyka (Grade 8)
- **Concept:** `В'язкість` (Citation form: ✅)
- **Scientific Terminology:** `['рідина', 'газ', 'переміщення', 'речовина']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «В'язкість — це властивість рідин і газів протидіяти переміщенню одних шарів речовини відносно інших.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 106 (Seed 777): Конституція (eval_shard_002_of_005.jsonl:line_41)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Конституція` (Citation form: ✅)
- **Scientific Terminology:** `['закон', 'держава']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Конституція — це теж закон, але вона посідає особливе місце серед усіх законів держави.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 107 (Seed 777): Юридичні гарантії (eval_shard_002_of_005.jsonl:line_49)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Юридичні гарантії` (Citation form: ✅)
- **Scientific Terminology:** `['гарантія', 'захід', 'здійснення', 'охорона', 'свобода']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Юридичні гарантії — державно-правові заходи, що забезпечують здійснення та охорону права, свобод і обов'язків людини й громадянина.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 108 (Seed 777): Закон (eval_shard_002_of_005.jsonl:line_39)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Закон` (Citation form: ✅)
- **Scientific Terminology:** `['акт', 'орган', 'сфера']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Закон — нормативно-правовий акт, прийнятий законодавчим органом державної влади, що регламентує найважливіші сфери суспільних відносин і має вищу юридичну силу.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 109 (Seed 777): Обмежена монархія (eval_shard_002_of_005.jsonl:line_3)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Обмежена монархія` (Citation form: ✅)
- **Scientific Terminology:** `['монархія', 'правління', 'монарх', 'парламент', 'конституція']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Обмежена монархія — форма державного правління, за якої владу монарха обмежує парламент або конституція.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 110 (Seed 777): Прямокутні координати (eval_shard_002_of_005.jsonl:line_48)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Прямокутні координати` (Citation form: ✅)
- **Scientific Terminology:** `['координата', 'система', 'вісь', 'меридіан', 'зона']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Прямокутні координати – це система координат, у якій за вісь X прийнято центральний меридіан 6-градусної зони, а за вісь Y – екватор.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 111 (Seed 777): Вичерпні природні ресурси (eval_shard_003_of_005.jsonl:line_39)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Вичерпні природні ресурси` (Citation form: ✅)
- **Scientific Terminology:** `['ресурс', 'зменшення', 'зникнення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Вичерпні природні ресурси – це ресурси, використання яких призводить до їх зменшення або повного зникнення.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 112 (Seed 777): Умови укладення шлюбу (eval_shard_003_of_005.jsonl:line_20)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Умови укладення шлюбу` (Citation form: ✅)
- **Scientific Terminology:** `['закон', 'укладення', 'шлюб', 'вимога', 'особа']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Умови укладення шлюбу — передбачені законом вимоги до осіб, які забезпечують дійсність їхнього шлюбу.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 113 (Seed 777): Об'єм тіла (eval_shard_003_of_005.jsonl:line_51)
- **Subject / Grade:** pryroda (Grade 5)
- **Concept:** `Об'єм тіла` (Citation form: ✅)
- **Scientific Terminology:** `["об'єм", 'тіло']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Об'ємом тіла називають частину простору, яку воно займає.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 114 (Seed 777): Метеочутливість (eval_shard_003_of_005.jsonl:line_13)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Метеочутливість` (Citation form: ✅)
- **Scientific Terminology:** `['організм', 'зміна']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Метеочутливість – це особливість організму людини, коли вона недостатньо добре може адаптуватися до погодних змін.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 115 (Seed 777): Цінності (eval_shard_003_of_005.jsonl:line_44)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Цінності` (Citation form: ✅)
- **Scientific Terminology:** `['переконання', 'суспільство']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Цінності – це загальновизнані переконання щодо цілей, до яких суспільство, усі його члени повинні прагнути, якими вони керуються у своєму повсякденному житті.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 116 (Seed 777): Свобода слова (eval_shard_004_of_005.jsonl:line_25)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Свобода слова` (Citation form: ✅)
- **Scientific Terminology:** `['право', 'засіб']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Свобода слова – це право людини висловлювати свої погляди в усній і письмовій формах, зокрема через засоби масової інформації.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 117 (Seed 777): Громадянство (eval_shard_004_of_005.jsonl:line_12)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Громадянство` (Citation form: ✅)
- **Scientific Terminology:** `['особа', 'держава', 'вияв', 'право', "обов'язок"]` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Громадянство – правовий зв'язок між фізичною особою і державою, який знаходить свій вияв у взаємних правах і обов'язках.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 118 (Seed 777): Джерела інформації (eval_shard_004_of_005.jsonl:line_40)
- **Subject / Grade:** ukrmova (Grade 8)
- **Concept:** `Джерела інформації` (Citation form: ✅)
- **Scientific Terminology:** `['телеканал', 'газета', 'вебсайт', 'мережа', 'енциклопедія']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Джерела інформації – усе те, звідки ми черпаємо інформацію: телеканали, газети, вебсайти, соціальні мережі, енциклопедії, книжки, буклети, повідомлення посадових осіб або учасників подій, рекламні щити, банери, мурали тощо.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 119 (Seed 777): Криптовалюти та цифрові гроші (eval_shard_004_of_005.jsonl:line_34)
- **Subject / Grade:** finansova (Grade 8)
- **Concept:** `Криптовалюти та цифрові гроші` (Citation form: ✅)
- **Scientific Terminology:** `['криптовалюта', 'технологія']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Криптовалюти та цифрові гроші — це ще не кінець історії, бо технології продовжують розвиватися.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 120 (Seed 777): Водосховища (eval_shard_004_of_005.jsonl:line_39)
- **Subject / Grade:** ukrmova (Grade 8)
- **Concept:** `Водосховища` (Citation form: ✅)
- **Scientific Terminology:** `['водойма', 'нагромадження']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Водосховища – це великі штучні водойми, які створено для нагромадження води й подальшого її використання протягом року.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 121 (Seed 777): Іконостас (eval_shard_005_of_005.jsonl:line_4)
- **Subject / Grade:** mystetstvo (Grade 8)
- **Concept:** `Іконостас` (Citation form: ✅)
- **Scientific Terminology:** `['ікона', 'храм', 'обряд', 'вівтар', 'церква']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Іконостас — стіна з ікон у християнському храмі східного обряду, яка відокремлює вівтар від центральної частини церкви.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 122 (Seed 777): Колектив (eval_shard_005_of_005.jsonl:line_50)
- **Subject / Grade:** etyka (Grade 6)
- **Concept:** `Колектив` (Citation form: ✅)
- **Scientific Terminology:** `['інтерес', 'дія']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Колектив — група людей, які мають спільні інтереси та здійснюють разом певні дії.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 123 (Seed 777): Банк ідей (eval_shard_005_of_005.jsonl:line_20)
- **Subject / Grade:** tekhnolohiyi (Grade 8)
- **Concept:** `Банк ідей` (Citation form: ✅)
- **Scientific Terminology:** `['ідея', 'інструмент', 'змога', "розв'язання", 'ситуація']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Банк ідей — інструмент, який дає змогу зберегти й систематизувати ідеї для їх подальшого використання в роботі з розв'язання проблемної ситуації творчого проєкту.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 124 (Seed 777): Мариніст (eval_shard_005_of_005.jsonl:line_8)
- **Subject / Grade:** mystetstvo (Grade 8)
- **Concept:** `Мариніст` (Citation form: ✅)
- **Scientific Terminology:** `['зображення', 'мор']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Мариніст — художник, що створює марини — твори із зображенням моря та подій, що відбуваються на морі.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 125 (Seed 777): Утиск (eval_shard_005_of_005.jsonl:line_39)
- **Subject / Grade:** etyka (Grade 6)
- **Concept:** `Утиск` (Citation form: ✅)
- **Scientific Terminology:** `['особа', 'атмосфера']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Утиск — небажана для особи та/або групи осібної, ворожої, образливої або зневажливої атмосфери.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 126 (Seed 777): Метали (sft_shard_011_of_150.jsonl:line_219)
- **Subject / Grade:** khimiya (Grade 7)
- **Concept:** `Метали` (Citation form: ✅)
- **Scientific Terminology:** `['залізо', 'алюміній', 'цинк', 'магній', 'золото']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Метали — залізо, алюміній, цинк, магній, золото, свинець та інші — відрізняються від неметалів характерним металічним блиском, ковкістю, вони добре проводять електричний струм і теплоту.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 127 (Seed 777): Критичне мислення (sft_shard_121_of_150.jsonl:line_74)
- **Subject / Grade:** zdorovia (Grade 6)
- **Concept:** `Критичне мислення` (Citation form: ✅)
- **Scientific Terminology:** `['мислення', 'здатність', 'доцільність', 'варіант']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Критичне мислення — це здатність відрізняти достовірні факти від недостовірних та оцінювати доцільність тих чи тих варіантів дій.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 128 (Seed 777): Макроекономічні показники (sft_shard_046_of_150.jsonl:line_319)
- **Subject / Grade:** ekonomika (Grade 11)
- **Concept:** `Макроекономічні показники` (Citation form: ✅)
- **Scientific Terminology:** `['ціна', 'виробництво', 'показник', 'динаміка', 'обсяг']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Макроекономічні показники — показники, що виражені в грошовій формі, а тому їх рівень і динаміка залежать як від фізичних обсягів виробництва, так і від рівня цін.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 129 (Seed 777): Алюміній (sft_shard_080_of_150.jsonl:line_160)
- **Subject / Grade:** khimiya (Grade 11)
- **Concept:** `Алюміній` (Citation form: ✅)
- **Scientific Terminology:** `['оксид', 'метал', 'сполука']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Алюміній — активний метал, тому витісняє інші метали з їхніх сполук, зокрема з оксидів.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 130 (Seed 777): Масовий відсоток (sft_shard_053_of_150.jsonl:line_5)
- **Subject / Grade:** algebra (Grade 8)
- **Concept:** `Масовий відсоток` (Citation form: ✅)
- **Scientific Terminology:** `['частка', 'відсоток', 'маса', 'речовина', 'грам']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Масову частку у відсотках називають масовим відсотком (маса речовини в грамах у 100 г розчину, позначають % м/м).» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 131 (Seed 777): Гомологічна різниця (sft_shard_067_of_150.jsonl:line_23)
- **Subject / Grade:** khimiya (Grade 9)
- **Concept:** `Гомологічна різниця` (Citation form: ✅)
- **Scientific Terminology:** `['різниця', 'атом', 'склад', 'молекула', 'речовина']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Гомологічна різниця — група атомів –СН2–, на яку (одну чи кілька) відрізняється склад молекул органічних речовин однотипної будови і схожих властивостей.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 132 (Seed 777): Гарнітура (sft_shard_110_of_150.jsonl:line_154)
- **Subject / Grade:** ya_doslidzhuiu_svit (Grade 3)
- **Concept:** `Гарнітура` (Citation form: ✅)
- **Scientific Terminology:** `['набір', 'шрифт', 'дизайн']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Гарнітура — це набір шрифтів, які мають однаковий дизайн.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 133 (Seed 777): Головне в програмуванні (sft_shard_021_of_150.jsonl:line_120)
- **Subject / Grade:** algebra (Grade 7)
- **Concept:** `Головне в програмуванні` (Citation form: ✅)
- **Scientific Terminology:** `['послідовність', 'програмування', 'алгоритм']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Головне в програмуванні — це придумати алгоритм, тобто послідовність дій, за допомогою якої можна із вхідних даних отримати вихідні дані.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 134 (Seed 777): Пропозиція (sft_shard_143_of_150.jsonl:line_393)
- **Subject / Grade:** finansova (Grade 9)
- **Concept:** `Пропозиція` (Citation form: ✅)
- **Scientific Terminology:** `['товар', 'виробник', 'ціна']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Пропозиція — це кількість товарів, які виробники готові виробити та продати за певною ціною.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 135 (Seed 777): Теза й аргументи (sft_shard_125_of_150.jsonl:line_122)
- **Subject / Grade:** ukrmova (Grade 10)
- **Concept:** `Теза й аргументи` (Citation form: ✅)
- **Scientific Terminology:** `['теза', 'аргумент', 'судження', 'речення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Теза й аргументи — це судження, виражені реченнями, які можна побачити (якщо вони написані) або почути (якщо вони вимовлені).» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 136 (Seed 777): Похідні способи набуття права власності (sft_shard_112_of_150.jsonl:line_216)
- **Subject / Grade:** pravoznavstvo (Grade 11)
- **Concept:** `Похідні способи набуття права власності` (Citation form: ✅)
- **Scientific Terminology:** `['набуття', 'власність', 'отримання', 'річ', 'підстава']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Похідні способи набуття права власності — це отримання речі на підставі цивільно-правових договорів (купівля–продаж, міна, дарування тощо), односторонніх правочинів особи (наприклад, за заповітом), актів органів державної влади чи місцевого самоврядування.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 137 (Seed 777): Варни (sft_shard_033_of_150.jsonl:line_290)
- **Subject / Grade:** istoriya (Grade 6)
- **Concept:** `Варни` (Citation form: ✅)
- **Scientific Terminology:** `['суспільство', 'належність', 'народження']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Варна — закрита соціальна група в традиційному індійському суспільстві, належність до якої визначалася народженням.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 138 (Seed 777): Жанр (sft_shard_077_of_150.jsonl:line_154)
- **Subject / Grade:** mystetstvo (Grade 6)
- **Concept:** `Жанр` (Citation form: ✅)
- **Scientific Terminology:** `['твір', 'сюжет', 'рішення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Жанр — сукупність художніх особливостей твору, які визначають його сюжет та композиційне рішення.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 139 (Seed 777): Активність у шкільному житті (sft_shard_069_of_150.jsonl:line_370)
- **Subject / Grade:** hromadianska (Grade 9)
- **Concept:** `Активність у шкільному житті` (Citation form: ✅)
- **Scientific Terminology:** `['активність', 'простір']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Активність у шкільному житті — це реальна можливість впливати на свій освітній простір.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 140 (Seed 777): Екосистема (sft_shard_106_of_150.jsonl:line_277)
- **Subject / Grade:** biolohiya (Grade 9)
- **Concept:** `Екосистема` (Citation form: ✅)
- **Scientific Terminology:** `['організм', 'існування']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Екосистеми є сукупностями живих організмів, які мешкають у певному середовищі існування й утворюють із ним одне ціле.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 141 (Seed 777): Право власності (sft_shard_128_of_150.jsonl:line_131)
- **Subject / Grade:** finansova (Grade 9)
- **Concept:** `Право власності` (Citation form: ✅)
- **Scientific Terminology:** `['право', 'власність', 'закон', 'розсуд', 'законодавство']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Право власності — це закріплене законом право володіти, користуватися та розпоряджатися майном на свій розсуд, але в межах, визначених законодавством.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 142 (Seed 777): Зоря (sft_shard_034_of_150.jsonl:line_408)
- **Subject / Grade:** astronomiya (Grade 11)
- **Concept:** `Зоря` (Citation form: ✅)
- **Scientific Terminology:** `['тяжіння', 'енергія']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Зоря — це величезна куля гарячого газу, яка утримується як одне ціле завдяки власній силі тяжіння й розігрівається ядерною енергією.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 143 (Seed 777): Стриманість (sft_shard_013_of_150.jsonl:line_218)
- **Subject / Grade:** etyka (Grade 5)
- **Concept:** `Стриманість` (Citation form: ✅)
- **Scientific Terminology:** `['гамування', 'бажання', 'почуття', 'пристрасть', 'задоволення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Стриманість — це свідоме гамування бажань, почуттів, пристрастей, задоволень тощо.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 144 (Seed 777): Спостереження (sft_shard_150_of_150.jsonl:line_399)
- **Subject / Grade:** fizyka (Grade 10)
- **Concept:** `Спостереження` (Citation form: ✅)
- **Scientific Terminology:** `['сприйняття', 'природа', 'одержання', 'аналіз']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Спостереження — це сприйняття природи з метою одержання первинних даних для подальшого аналізу.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 145 (Seed 777): Внутрішня відповідальність (sft_shard_071_of_150.jsonl:line_368)
- **Subject / Grade:** etyka (Grade 5)
- **Concept:** `Внутрішня відповідальність` (Citation form: ✅)
- **Scientific Terminology:** `['совість', 'відповідальність', 'змога', 'результат', 'вчинок']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Внутрішня відповідальність — це насамперед совість, яка дає змогу людині передбачити результат своїх вчинків.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 146 (Seed 777): Управління конфліктом (sft_shard_032_of_150.jsonl:line_431)
- **Subject / Grade:** etyka (Grade 5)
- **Concept:** `Управління конфліктом` (Citation form: ✅)
- **Scientific Terminology:** `['управління', 'конфлікт', 'ситуація']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Управління конфліктом — цілеспрямований вплив на конфліктну ситуацію.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 147 (Seed 777): Катран (sft_shard_079_of_150.jsonl:line_438)
- **Subject / Grade:** ya_doslidzhuiu_svit (Grade 3)
- **Concept:** `Катран` (Citation form: ✅)
- **Scientific Terminology:** `['акула', 'довжина', 'тіло', 'метр']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Катран — невелика акула, довжина тіла якої дещо більша 1 метра.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 148 (Seed 777): Господарське право (sft_shard_029_of_150.jsonl:line_239)
- **Subject / Grade:** pravoznavstvo (Grade 11)
- **Concept:** `Господарське право` (Citation form: ✅)
- **Scientific Terminology:** `['право', 'норма', 'сфера', 'управління', 'економіка']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Господарське право — це сукупність правових норм, які регулюють суспільні відносини у сфері управління економікою, виробництва й реалізації продукції, виконання робіт і надання послуг з метою отримання прибутків.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 149 (Seed 777): Сфера (sft_shard_113_of_150.jsonl:line_307)
- **Subject / Grade:** matematyka (Grade 11)
- **Concept:** `Сфера` (Citation form: ✅)
- **Scientific Terminology:** `['тіло', 'відстань']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Сферою називається тіло, що складається з усіх точок простору, розташованих на заданій відстані (R) від заданої точки (O).» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 150 (Seed 777): Льодовики (sft_shard_060_of_150.jsonl:line_123)
- **Subject / Grade:** heohrafiya (Grade 6)
- **Concept:** `Льодовики` (Citation form: ✅)
- **Scientific Terminology:** `['нагромадження', 'лід', 'суходіл']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Льодовики — це нагромадження багаторічного льоду на суходолі.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**
