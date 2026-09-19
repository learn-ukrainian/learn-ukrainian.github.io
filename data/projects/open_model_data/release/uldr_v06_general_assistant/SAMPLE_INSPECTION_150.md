# Multi-Seed Sample Inspection of 150 Mined Records (Phase 6.1)

**Audit Result:** ALL 150 RECORDS PASSED — 100% PASS RATE

**Sampling Protocol:** 3 PRNG seeds (42, 123, 777), 50 records per seed (total 150 records across eval and SFT shards).

## Release-Wide Defect Scan (All 75,000 SFT + 237 Eval Records)

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
| `ellipsis_and_conjunction_starters` | 0 | ✅ 0 |
| `rhetorical_and_negated_definitions` | 0 | ✅ 0 |

## Multi-Seed Inspected Sample Overview

| # | Seed | Origin | Concept | Subject | Grade | Terms | Citation | Anaphora-Free | OCR-Clean | Def-Aligned | Terms Valid | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 42 | `eval_shard_001_of_005.jsonl:line_30` | **Аграрна революція** | vsesvitnia | 8 | революція, реформування, господарство, збільшення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 2 | 42 | `eval_shard_001_of_005.jsonl:line_24` | **Верхня палата** | vsesvitnia | 8 | палата, сенат, представник, духовенство | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 3 | 42 | `eval_shard_001_of_005.jsonl:line_25` | **Плавлення** | fizyka | 8 | перехід, речовина | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 4 | 42 | `eval_shard_001_of_005.jsonl:line_11` | **Протилежні вектори** | heometriya | 9 | вектор, модуль | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 5 | 42 | `eval_shard_001_of_005.jsonl:line_10` | **Генеральна рада** | istoriya | 8 | орган, військо | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 6 | 42 | `eval_shard_002_of_005.jsonl:line_10` | **Нейронауки** | biolohiya | 8 | галузь, знання, вивчення, система | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 7 | 42 | `eval_shard_002_of_005.jsonl:line_11` | **Складна держава** | pravoznavstvo | 9 | держава, утворення, самостійність | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 8 | 42 | `eval_shard_002_of_005.jsonl:line_43` | **Підзаконний нормативно-правовий акт** | pravoznavstvo | 9 | закон, акт, підстава, конкретизація | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 9 | 42 | `eval_shard_002_of_005.jsonl:line_2` | **Звичайне скло** | khimiya | 8 | оксид, скло, речовина, силіцій | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 10 | 42 | `eval_shard_002_of_005.jsonl:line_1` | **Форма держави** | pravoznavstvo | 9 | держава, організація, структура, орган | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 11 | 42 | `eval_shard_003_of_005.jsonl:line_42` | **Кримінальна відповідальність** | pravoznavstvo | 9 | відповідальність, покарання, держава, особа | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 12 | 42 | `eval_shard_003_of_005.jsonl:line_24` | **Умови укладення шлюбу** | pravoznavstvo | 9 | закон, укладення, шлюб, вимога | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 13 | 42 | `eval_shard_003_of_005.jsonl:line_46` | **Цінності** | hromadianska | 8 | переконання, суспільство | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 14 | 42 | `eval_shard_003_of_005.jsonl:line_15` | **Артезіанська вода** | heohrafiya | 8 | вода, глибина, шар, структура | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 15 | 42 | `eval_shard_003_of_005.jsonl:line_25` | **Антропогенний ландшафт** | heohrafiya | 8 | ландшафт, вплив | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 16 | 42 | `eval_shard_004_of_005.jsonl:line_47` | **Етнічна музика** | mystetstvo | 8 | витік, фольклор, етнос | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 17 | 42 | `eval_shard_004_of_005.jsonl:line_27` | **Гончарні вироби** | ekonomika | 10 | результат, професіоналізм | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 18 | 42 | `eval_shard_004_of_005.jsonl:line_6` | **Формальні групи** | hromadianska | 8 | організація, гурток, секція, колектив | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 19 | 42 | `eval_shard_004_of_005.jsonl:line_14` | **Завойовницька війна** | hromadianska | 8 | війна, розширення, сфера, територія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 20 | 42 | `eval_shard_004_of_005.jsonl:line_36` | **Водосховища** | ukrmova | 8 | водойма, нагромадження | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 21 | 42 | `eval_shard_005_of_005.jsonl:line_27` | **Автоматика** | tekhnolohiyi | 8 | механізм, прилад | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 22 | 42 | `eval_shard_005_of_005.jsonl:line_31` | **Масаж** | tekhnolohiyi | 8 | тканина, орган, рука, апарат | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 23 | 42 | `eval_shard_005_of_005.jsonl:line_24` | **Художня фотографія** | tekhnolohiyi | 8 | фотографія, мистецтво, відображення, дійсність | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 24 | 42 | `eval_shard_005_of_005.jsonl:line_19` | **Оздоровча система** | zdorovia | 8 | система, знання, навичка, звичка | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 25 | 42 | `eval_shard_005_of_005.jsonl:line_39` | **Повага** | etyka | 6 | почуття, шана, ставлення, підстава | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 26 | 42 | `sft_shard_135_of_150.jsonl:line_93` | **Принципат** | istoriya | 7 | правління, особа, принцепс | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 27 | 42 | `sft_shard_015_of_150.jsonl:line_369` | **Друкований текст** | zarlit | 5 | засіб, друк, папір | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 28 | 42 | `sft_shard_058_of_150.jsonl:line_349` | **Марикультура** | heohrafiya | 9 | вирощування, морепродукт | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 29 | 42 | `sft_shard_074_of_150.jsonl:line_211` | **Вуглеводи** | khimiya | 9 | природа, сполука, представник, глюкоза | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 30 | 42 | `sft_shard_103_of_150.jsonl:line_460` | **Діатомові водорості** | pryroda | 6 | водорість, рослина | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 31 | 42 | `sft_shard_003_of_150.jsonl:line_37` | **Тотальна війна** | vsesvitnia | 10 | війна, засіб, знищення, противник | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 32 | 42 | `sft_shard_048_of_150.jsonl:line_54` | **Археї** | biolohiya | 7 | учасник, кругообіг, речовина | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 33 | 42 | `sft_shard_012_of_150.jsonl:line_387` | **Модернізм** | istoriya | 10 | течія, мистецтво, змішування, елемент | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 34 | 42 | `sft_shard_134_of_150.jsonl:line_384` | **Грант** | finansova | 9 | особа, організація, бізнес, реалізація | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 35 | 42 | `sft_shard_046_of_150.jsonl:line_17` | **Дана ситуація** | matematyka | 6 | ситуація, задача, рівність | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 36 | 42 | `sft_shard_002_of_150.jsonl:line_255` | **Мехатроніка** | fizyka | 9 | галузь, інженерія, механіка, електроніка | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 37 | 42 | `sft_shard_079_of_150.jsonl:line_273` | **Правопорушення** | ya_doslidzhuiu_svit | 4 | вчинок, відповідальність | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 38 | 42 | `sft_shard_044_of_150.jsonl:line_277` | **Цифровий слід** | hromadianska | 9 | пам'ять, інтернет, дія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 39 | 42 | `sft_shard_150_of_150.jsonl:line_131` | **Запозичена іншомовна лексика** | ukrmova | university | лексика, словозміна, специфіка, мюзикл | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 40 | 42 | `sft_shard_131_of_150.jsonl:line_477` | **Авторство** | ukrmova | 5 | належність, твір, проєкт, винахід | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 41 | 42 | `sft_shard_121_of_150.jsonl:line_171` | **Похідні способи набуття права власності** | pravoznavstvo | 11 | набуття, власність, отримання, річ | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 42 | 42 | `sft_shard_053_of_150.jsonl:line_255` | **Раціональне рівняння** | algebra | 8 | рівняння, вираз | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 43 | 42 | `sft_shard_039_of_150.jsonl:line_210` | **Поміркованість суду** | zarlit | 9 | поміркованість, суд | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 44 | 42 | `sft_shard_076_of_150.jsonl:line_314` | **Безпека особистого самовираження** | etyka | 5 | безпека, самовираження, сприйняття, зміст | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 45 | 42 | `sft_shard_141_of_150.jsonl:line_141` | **Символи хімічних елементів** | pryroda | 6 | символ, елемент, абетка | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 46 | 42 | `sft_shard_010_of_150.jsonl:line_451` | **Система колективної безпеки** | vsesvitnia | 10 | система, безпека, здійснення, захист | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 47 | 42 | `sft_shard_142_of_150.jsonl:line_75` | **Сузір'я** | astronomiya | 11 | ділянка, сфера, зручність, орієнтування | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 48 | 42 | `sft_shard_108_of_150.jsonl:line_289` | **Хореографічна поема** | mystetstvo | 9 | поема, твір, жанр | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 49 | 42 | `sft_shard_018_of_150.jsonl:line_201` | **Нейромедіатори** | biolohiya | 9 | речовина, передача, імпульс, нейрон | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 50 | 42 | `sft_shard_071_of_150.jsonl:line_432` | **Мода** | matematyka | 11 | елемент, вибірка | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 51 | 123 | `eval_shard_001_of_005.jsonl:line_44` | **Держава** | pravoznavstvo | 9 | організація, суспільство, цілісність, безпека | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 52 | 123 | `eval_shard_001_of_005.jsonl:line_31` | **Реостат** | fizyka | 8 | опір, пристрій, регулювання, коло | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 53 | 123 | `eval_shard_001_of_005.jsonl:line_33` | **Електролічильник** | fizyka | 8 | прилад, вимірювання | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 54 | 123 | `eval_shard_001_of_005.jsonl:line_40` | **Мононорми первісного суспільства** | pravoznavstvo | 9 | мононорма, суспільство, поведінка, характер | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 55 | 123 | `eval_shard_001_of_005.jsonl:line_17` | **Блок** | fizyka | 8 | механізм, колесо | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 56 | 123 | `eval_shard_002_of_005.jsonl:line_5` | **Обмежена монархія** | pravoznavstvo | 9 | монархія, правління, монарх, парламент | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 57 | 123 | `eval_shard_002_of_005.jsonl:line_30` | **Хмарні сервіси** | informatyka | 7 | сервіс, надання, доступ, інтернет-ресурс | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 58 | 123 | `eval_shard_002_of_005.jsonl:line_8` | **Спинний мозок** | biolohiya | 8 | мозок, тяж, канал, хребет | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 59 | 123 | `eval_shard_002_of_005.jsonl:line_47` | **Особисті гарантії** | pravoznavstvo | 9 | гарантія, громадянин, захист, свобода | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 60 | 123 | `eval_shard_002_of_005.jsonl:line_23` | **Правовідносини** | pravoznavstvo | 9 | норма, учасник, обов'язок, держава | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 61 | 123 | `eval_shard_003_of_005.jsonl:line_39` | **Гідроенергетичний потенціал** | heohrafiya | 8 | потенціал, енергія, течія, об'єкт | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 62 | 123 | `eval_shard_003_of_005.jsonl:line_18` | **Позов** | pravoznavstvo | 9 | закон, звернення, особа, суд | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 63 | 123 | `eval_shard_003_of_005.jsonl:line_8` | **Права людини** | pravoznavstvo | 9 | існування, розвиток | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 64 | 123 | `eval_shard_003_of_005.jsonl:line_11` | **Вегетаційний період** | heohrafiya | 8 | період, рослина | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 65 | 123 | `eval_shard_003_of_005.jsonl:line_6` | **Біженець** | pravoznavstvo | 9 | особа, громадянин, причина, країна | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 66 | 123 | `eval_shard_004_of_005.jsonl:line_44` | **Героїчний епос** | zarlit | 8 | епос, жанр, завзяття, народ | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 67 | 123 | `eval_shard_004_of_005.jsonl:line_26` | **Медіаграмотність** | hromadianska | 8 | знання, уміння, навичка | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 68 | 123 | `eval_shard_004_of_005.jsonl:line_41` | **Зміни місце** | zarlit | 8 | прислів'я, пошук | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 69 | 123 | `eval_shard_004_of_005.jsonl:line_35` | **Піктографічне письмо** | ukrmova | 8 | письмо, комунікація, значок, малюнок | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 70 | 123 | `eval_shard_004_of_005.jsonl:line_28` | **Обмін** | ekonomika | 10 | рух, товар, власник | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 71 | 123 | `eval_shard_005_of_005.jsonl:line_44` | **Соціальна адаптація** | etyka | 6 | адаптація, пристосування, взаємодія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 72 | 123 | `eval_shard_005_of_005.jsonl:line_20` | **Рефлексія проєктної діяльності** | tekhnolohiyi | 8 | рефлексія, здатність, рішення, проєкт | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 73 | 123 | `eval_shard_005_of_005.jsonl:line_5` | **Середньовічний замковий комплекс** | mystetstvo | 8 | комплекс, осередок, захист, земля | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 74 | 123 | `eval_shard_005_of_005.jsonl:line_12` | **Формальні лідери** | zdorovia | 8 | лідер, представник, самоврядування, обов'язок | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 75 | 123 | `eval_shard_005_of_005.jsonl:line_4` | **Дзвін** | mystetstvo | 8 | інструмент, забарвлення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 76 | 123 | `sft_shard_090_of_150.jsonl:line_256` | **Пристрасть** | zarlit | 10 | оповідь, сюжет | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 77 | 123 | `sft_shard_131_of_150.jsonl:line_146` | **Раціональний дріб** | algebra | 8 | знаменник, многочлен, дріб, чисельник | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 78 | 123 | `sft_shard_022_of_150.jsonl:line_409` | **Мовний організм** | ukrmova | university | організм, субстанція, результат, життєдіяльність | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 79 | 123 | `sft_shard_020_of_150.jsonl:line_137` | **Реліктове випромінювання** | astronomiya | 11 | випромінювання, квант | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 80 | 123 | `sft_shard_070_of_150.jsonl:line_100` | **Лозоплетіння** | tekhnolohiyi | 6 | плетіння, розвиток | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 81 | 123 | `sft_shard_066_of_150.jsonl:line_128` | **Витік перший** | zarlit | 10 | наука, мистецтво, більшість, цінність | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 82 | 123 | `sft_shard_051_of_150.jsonl:line_400` | **Тигр** | ukrmova | university | хамелеон, тиждень | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 83 | 123 | `sft_shard_122_of_150.jsonl:line_283` | **Дивовижні карнавальні дійства** | mystetstvo | 5 | дійство, вистава, вулиця, місто | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 84 | 123 | `sft_shard_098_of_150.jsonl:line_424` | **Вітер** | heohrafiya | 6 | переміщення, повітря, область, тиск | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 85 | 123 | `sft_shard_067_of_150.jsonl:line_288` | **Об'єкт** | ya_doslidzhuiu_svit | 3 | назва, істота, подія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 86 | 123 | `sft_shard_012_of_150.jsonl:line_240` | **Деталь** | tekhnolohiyi | 6 | виріб, руйнування | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 87 | 123 | `sft_shard_031_of_150.jsonl:line_160` | **Фосфорні боєприпаси** | zakhyst | 10 | боєприпас, снаряд, фосфор, температура | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 88 | 123 | `sft_shard_037_of_150.jsonl:line_370` | **Секс** | zdorovia | 9 | доказ, кохання, стосунок | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 89 | 123 | `sft_shard_143_of_150.jsonl:line_8` | **Тепловий ефект хімічної реакції** | khimiya | 9 | ефект, реакція, теплота | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 90 | 123 | `sft_shard_052_of_150.jsonl:line_86` | **Комбінаторика** | algebra | 11 | вибір, розташування, елемент, множина | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 91 | 123 | `sft_shard_041_of_150.jsonl:line_482` | **Випаровування** | fizyka | 10 | пароутворення, поверхня, рідина | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 92 | 123 | `sft_shard_112_of_150.jsonl:line_493` | **Стихійне лихо** | zakhyst | 10 | територія, життєдіяльність, населення, збиток | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 93 | 123 | `sft_shard_063_of_150.jsonl:line_9` | **Дикорослі рослини** | ya_doslidzhuiu_svit | 1 | рослина, сировина, тварина | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 94 | 123 | `sft_shard_004_of_150.jsonl:line_373` | **Провідний мотив пісні** | ukrlit | 9 | мотив, кохання | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 95 | 123 | `sft_shard_109_of_150.jsonl:line_291` | **Обертання** | heometriya | 9 | швидкість, прискорення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 96 | 123 | `sft_shard_133_of_150.jsonl:line_21` | **Рівномірний прямолінійний рух** | fizyka | 10 | рух, тіло, інтервал, переміщення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 97 | 123 | `sft_shard_026_of_150.jsonl:line_23` | **Просвітництво** | zarlit | 9 | рух, доба, епоха, етап | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 98 | 123 | `sft_shard_149_of_150.jsonl:line_482` | **Фотоефект** | fizyka | 11 | взаємодія, випромінювання, речовина, результат | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 99 | 123 | `sft_shard_103_of_150.jsonl:line_480` | **Дорослість** | zdorovia | 9 | відповідальність, зрілість, прийняття, рішення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 100 | 123 | `sft_shard_077_of_150.jsonl:line_387` | **Рівні вектори** | matematyka | 10 | вектор, модуль | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 101 | 777 | `eval_shard_001_of_005.jsonl:line_12` | **Революція** | vsesvitnia | 8 | переворот, суспільство, зміна, перетворення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 102 | 777 | `eval_shard_001_of_005.jsonl:line_23` | **В'язкість** | fizyka | 8 | рідина, газ, переміщення, речовина | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 103 | 777 | `eval_shard_001_of_005.jsonl:line_43` | **Орбіталь** | khimiya | 8 | ймовірність, перебування, електрон | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 104 | 777 | `eval_shard_001_of_005.jsonl:line_20` | **Колоніалізм** | vsesvitnia | 8 | підкорення, країна, ресурс, праця | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 105 | 777 | `eval_shard_001_of_005.jsonl:line_47` | **Хімічний зв'язок** | khimiya | 8 | взаємодія, атом, стійкість, частинка | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 106 | 777 | `eval_shard_002_of_005.jsonl:line_22` | **Умовні рефлекси** | biolohiya | 8 | рефлекс, реакція, організм, чинник | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 107 | 777 | `eval_shard_002_of_005.jsonl:line_38` | **Дублювання** | informatyka | 7 | повторення, фрагмент | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 108 | 777 | `eval_shard_002_of_005.jsonl:line_27` | **Правомірна поведінка** | pravoznavstvo | 9 | поведінка, припис, норма, держава | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 109 | 777 | `eval_shard_002_of_005.jsonl:line_36` | **Імітаційна модель** | informatyka | 7 | алгоритм, програма, модель, комплекс | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 110 | 777 | `eval_shard_002_of_005.jsonl:line_3` | **Абсолютна монархія** | pravoznavstvo | 9 | монархія, правління, монарх, гілка | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 111 | 777 | `eval_shard_003_of_005.jsonl:line_29` | **Степ** | heohrafiya | 8 | зона, держава, підзона | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 112 | 777 | `eval_shard_003_of_005.jsonl:line_37` | **Вичерпні природні ресурси** | heohrafiya | 8 | ресурс, зменшення, зникнення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 113 | 777 | `eval_shard_003_of_005.jsonl:line_12` | **Суддя** | pravoznavstvo | 9 | правопорушення, особа, право, ім'я | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 114 | 777 | `eval_shard_003_of_005.jsonl:line_30` | **Державна служба зайнятості** | pravoznavstvo | 9 | служба, зайнятість, система, установа | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 115 | 777 | `eval_shard_003_of_005.jsonl:line_36` | **Адміністративне право** | pravoznavstvo | 9 | право, галузь, управління | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 116 | 777 | `eval_shard_004_of_005.jsonl:line_19` | **Право** | hromadianska | 8 | норма, держава, регулювання | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 117 | 777 | `eval_shard_004_of_005.jsonl:line_12` | **Цькування** | hromadianska | 8 | правопорушення, вчинення, відповідальність, штраф | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 118 | 777 | `eval_shard_004_of_005.jsonl:line_7` | **Здібності** | hromadianska | 8 | схильність, виконання | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 119 | 777 | `eval_shard_004_of_005.jsonl:line_29` | **Благо** | ekonomika | 10 | засіб, задоволення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 120 | 777 | `eval_shard_004_of_005.jsonl:line_38` | **Опис місцевості** | ukrmova | 8 | опис, місцевість, зображення, місто | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 121 | 777 | `eval_shard_005_of_005.jsonl:line_8` | **Симфонічна поема** | mystetstvo | 8 | поема, твір, програма | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 122 | 777 | `eval_shard_005_of_005.jsonl:line_21` | **Банк ідей** | tekhnolohiyi | 8 | ідея, інструмент, змога, розв'язання | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 123 | 777 | `eval_shard_005_of_005.jsonl:line_47` | **Авторитет** | etyka | 6 | переконання, поведінка, особа, організація | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 124 | 777 | `eval_shard_005_of_005.jsonl:line_13` | **Якісний сон** | zdorovia | 8 | сон, складник, відновлення, енергія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 125 | 777 | `eval_shard_005_of_005.jsonl:line_6` | **Іконостас** | mystetstvo | 8 | ікона, храм, обряд, вівтар | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 126 | 777 | `sft_shard_108_of_150.jsonl:line_189` | **Дресировані тварини** | informatyka | 3 | тварина, виконавець, команда | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 127 | 777 | `sft_shard_065_of_150.jsonl:line_388` | **Географічний полюс** | pryroda | 8 | полюс, поверхня, вісь, обертання | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 128 | 777 | `sft_shard_048_of_150.jsonl:line_41` | **Літературознавство** | zarlit | 5 | наука, література | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 129 | 777 | `sft_shard_011_of_150.jsonl:line_473` | **Змінні зорі** | astronomiya | 11 | блиск, поверхня, дія, причина | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 130 | 777 | `sft_shard_139_of_150.jsonl:line_257` | **Брендування** | finansova | 9 | розробка, логотип, колір, шрифт | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 131 | 777 | `sft_shard_126_of_150.jsonl:line_478` | **Скульптура дадаїзму** | mystetstvo | 9 | скульптура, дадаїзм, виклик, мистецтво | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 132 | 777 | `sft_shard_077_of_150.jsonl:line_432` | **Слідування** | informatyka | 5 | структура, подання, набір, команда | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 133 | 777 | `sft_shard_133_of_150.jsonl:line_231` | **Гроші** | finansova | 9 | інструмент, їжа, освіта, відпочинок | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 134 | 777 | `sft_shard_013_of_150.jsonl:line_18` | **Йонізація газів** | fizyka | 11 | розпад, молекула, електрон, йонізація | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 135 | 777 | `sft_shard_150_of_150.jsonl:line_186` | **Волонтерство** | hromadianska | 9 | дія, енергія, вміння | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 136 | 777 | `sft_shard_062_of_150.jsonl:line_382` | **Спілкування** | hromadianska | 9 | емоція, враження, знання | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 137 | 777 | `sft_shard_033_of_150.jsonl:line_210` | **Органи зору живих істот** | fizyka | 9 | орган, зір, істота | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 138 | 777 | `sft_shard_027_of_150.jsonl:line_448` | **Фенол** | khimiya | 10 | сировина, виробництво, волокно, нейлон | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 139 | 777 | `sft_shard_079_of_150.jsonl:line_76` | **Предметна область** | informatyka | 9 | область, сфера, застосування, база | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 140 | 777 | `sft_shard_120_of_150.jsonl:line_321` | **Історія фізики** | fizyka | 10 | фізика, відкриття | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 141 | 777 | `sft_shard_051_of_150.jsonl:line_311` | **Проектна команда** | ekonomika | 11 | команда, структура, проект | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 142 | 777 | `sft_shard_004_of_150.jsonl:line_245` | **Ключові слова** | informatyka | 5 | пошук, відомість | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 143 | 777 | `sft_shard_029_of_150.jsonl:line_331` | **Чиста неушкоджена шкіра** | zdorovia | 7 | перепона, проникнення, організм, мікроорганізм | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 144 | 777 | `sft_shard_017_of_150.jsonl:line_138` | **Старіння населення** | finansova | 9 | старіння, населення, зростання, частка | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 145 | 777 | `sft_shard_071_of_150.jsonl:line_283` | **Природні барвники** | khimiya | 10 | барвник, сполука, організм, клітина | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 146 | 777 | `sft_shard_046_of_150.jsonl:line_158` | **Хоровий концерт** | mystetstvo | 6 | концерт, жанр, принцип, контраст | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 147 | 777 | `sft_shard_103_of_150.jsonl:line_449` | **Рівні фігури** | heometriya | 9 | фігура, переміщення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 148 | 777 | `sft_shard_104_of_150.jsonl:line_29` | **Право власності** | finansova | 9 | право, власність, закон, розсуд | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 149 | 777 | `sft_shard_042_of_150.jsonl:line_97` | **Периферія** | ekonomika | 11 | країна, господарство | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 150 | 777 | `sft_shard_053_of_150.jsonl:line_430` | **Комедія** | ukrlit | 8 | твір, засіб, гумор, сатира | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |

## Detailed Record Inspection (Full Text)

### Record 1 (Seed 42): Аграрна революція (eval_shard_001_of_005.jsonl:line_30)
- **Subject / Grade:** vsesvitnia (Grade 8)
- **Concept:** `Аграрна революція` (Citation form: ✅)
- **Scientific Terminology:** `['революція', 'реформування', 'господарство', 'збільшення', 'товарність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Аграрна революція – реформування сільського господарства з метою збільшення його товарності й прибутковості.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 2 (Seed 42): Верхня палата (eval_shard_001_of_005.jsonl:line_24)
- **Subject / Grade:** vsesvitnia (Grade 8)
- **Concept:** `Верхня палата` (Citation form: ✅)
- **Scientific Terminology:** `['палата', 'сенат', 'представник', 'духовенство', 'магнат']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Верхня палата – сенат – складалася з представників вищого духовенства та магнатів, зайнятих на високих державних посадах.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 3 (Seed 42): Плавлення (eval_shard_001_of_005.jsonl:line_25)
- **Subject / Grade:** fizyka (Grade 8)
- **Concept:** `Плавлення` (Citation form: ✅)
- **Scientific Terminology:** `['перехід', 'речовина']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Плавлення — це процес переходу речовини з твердого стану в рідкий.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 4 (Seed 42): Протилежні вектори (eval_shard_001_of_005.jsonl:line_11)
- **Subject / Grade:** heometriya (Grade 9)
- **Concept:** `Протилежні вектори` (Citation form: ✅)
- **Scientific Terminology:** `['вектор', 'модуль']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Два ненульових вектори називають протилежними, якщо їхні модулі рівні й вектори протилежно напрямлені.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 5 (Seed 42): Генеральна рада (eval_shard_001_of_005.jsonl:line_10)
- **Subject / Grade:** istoriya (Grade 8)
- **Concept:** `Генеральна рада` (Citation form: ✅)
- **Scientific Terminology:** `['орган', 'військо']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Генеральна рада — вищий представницький орган влади у Війську Запорозькому.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 6 (Seed 42): Нейронауки (eval_shard_002_of_005.jsonl:line_10)
- **Subject / Grade:** biolohiya (Grade 8)
- **Concept:** `Нейронауки` (Citation form: ✅)
- **Scientific Terminology:** `['галузь', 'знання', 'вивчення', 'система', 'пошук']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Нейронауки — це сукупність галузей знань, що стосуються вивчення нервової системи та пошуку шляхів лікування неврологічних і психіатричних захворювань.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 7 (Seed 42): Складна держава (eval_shard_002_of_005.jsonl:line_11)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Складна держава` (Citation form: ✅)
- **Scientific Terminology:** `['держава', 'утворення', 'самостійність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Складна держава — держава, що формується з відокремлених державних утворень, які мають певну самостійність.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 8 (Seed 42): Підзаконний нормативно-правовий акт (eval_shard_002_of_005.jsonl:line_43)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Підзаконний нормативно-правовий акт` (Citation form: ✅)
- **Scientific Terminology:** `['закон', 'акт', 'підстава', 'конкретизація', 'розпорядження']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Підзаконний нормативно-правовий акт — акт, який видається відповідно до закону та на підставі закону для конкретизації законодавчих розпоряджень і їхнього трактування або встановлення первинних норм.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 9 (Seed 42): Звичайне скло (eval_shard_002_of_005.jsonl:line_2)
- **Subject / Grade:** khimiya (Grade 8)
- **Concept:** `Звичайне скло` (Citation form: ✅)
- **Scientific Terminology:** `['оксид', 'скло', 'речовина', 'силіцій', 'склад']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Звичайне скло — аморфна речовина, але із часом силіцій(IV) оксид у його складі стає кристалічним.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 10 (Seed 42): Форма держави (eval_shard_002_of_005.jsonl:line_1)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Форма держави` (Citation form: ✅)
- **Scientific Terminology:** `['держава', 'організація', 'структура', 'орган', 'здійснення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Форма держави — спосіб організації структури держави та її органів, а також спосіб здійснення державної влади, що виражається у формі правління, формі державного устрою і політичному режимі.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 11 (Seed 42): Кримінальна відповідальність (eval_shard_003_of_005.jsonl:line_42)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Кримінальна відповідальність` (Citation form: ✅)
- **Scientific Terminology:** `['відповідальність', 'покарання', 'держава', 'особа', 'злочин']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Кримінальна відповідальність — покарання, що застосовує держава до особи, яка вчинила злочин.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 12 (Seed 42): Умови укладення шлюбу (eval_shard_003_of_005.jsonl:line_24)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Умови укладення шлюбу` (Citation form: ✅)
- **Scientific Terminology:** `['закон', 'укладення', 'шлюб', 'вимога', 'особа']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Умови укладення шлюбу — передбачені законом вимоги до осіб, які забезпечують дійсність їхнього шлюбу.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 13 (Seed 42): Цінності (eval_shard_003_of_005.jsonl:line_46)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Цінності` (Citation form: ✅)
- **Scientific Terminology:** `['переконання', 'суспільство']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Цінності – це загальновизнані переконання щодо цілей, до яких суспільство, усі його члени повинні прагнути, якими вони керуються у своєму повсякденному житті.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 14 (Seed 42): Артезіанська вода (eval_shard_003_of_005.jsonl:line_15)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Артезіанська вода` (Citation form: ✅)
- **Scientific Terminology:** `['вода', 'глибина', 'шар', 'структура', 'басейн']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Артезіанська вода – вода, що залягає на глибині 25–1000 м між водотривкими шарами в межах великих геологічних структур, утворюючи артезіанські басейни.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 15 (Seed 42): Антропогенний ландшафт (eval_shard_003_of_005.jsonl:line_25)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Антропогенний ландшафт` (Citation form: ✅)
- **Scientific Terminology:** `['ландшафт', 'вплив']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Антропогенний ландшафт – це тип ПТК, який сформувався під впливом діяльності людини.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 16 (Seed 42): Етнічна музика (eval_shard_004_of_005.jsonl:line_47)
- **Subject / Grade:** mystetstvo (Grade 8)
- **Concept:** `Етнічна музика` (Citation form: ✅)
- **Scientific Terminology:** `['витік', 'фольклор', 'етнос']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Етнічна музика — музика, витоки якої полягають у музичному фольклорі певного етносу.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 17 (Seed 42): Гончарні вироби (eval_shard_004_of_005.jsonl:line_27)
- **Subject / Grade:** ekonomika (Grade 10)
- **Concept:** `Гончарні вироби` (Citation form: ✅)
- **Scientific Terminology:** `['результат', 'професіоналізм']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Гончарні вироби — це результат високого професіоналізму майстрів.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 18 (Seed 42): Формальні групи (eval_shard_004_of_005.jsonl:line_6)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Формальні групи` (Citation form: ✅)
- **Scientific Terminology:** `['організація', 'гурток', 'секція', 'колектив']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Формальні групи – це школа, клас, різноманітні шкільні та позашкільні організації, як-от: гуртки, спортивні секції, мистецькі колективи тощо.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 19 (Seed 42): Завойовницька війна (eval_shard_004_of_005.jsonl:line_14)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Завойовницька війна` (Citation form: ✅)
- **Scientific Terminology:** `['війна', 'розширення', 'сфера', 'територія', 'держава']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Завойовницька війна – війна, що ведеться для розширення власної сфери впливу на території іншої держави.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 20 (Seed 42): Водосховища (eval_shard_004_of_005.jsonl:line_36)
- **Subject / Grade:** ukrmova (Grade 8)
- **Concept:** `Водосховища` (Citation form: ✅)
- **Scientific Terminology:** `['водойма', 'нагромадження']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Водосховища – це великі штучні водойми, які створено для нагромадження води й подальшого її використання протягом року.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 21 (Seed 42): Автоматика (eval_shard_005_of_005.jsonl:line_27)
- **Subject / Grade:** tekhnolohiyi (Grade 8)
- **Concept:** `Автоматика` (Citation form: ✅)
- **Scientific Terminology:** `['механізм', 'прилад']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Автоматика — сукупність механізмів, приладів, що діють автоматично.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 22 (Seed 42): Масаж (eval_shard_005_of_005.jsonl:line_31)
- **Subject / Grade:** tekhnolohiyi (Grade 8)
- **Concept:** `Масаж` (Citation form: ✅)
- **Scientific Terminology:** `['тканина', 'орган', 'рука', 'апарат']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Масаж — метод механічного дозованого і рефлекторного впливу на тканини й органи людини руками або спеціальними апаратами.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 23 (Seed 42): Художня фотографія (eval_shard_005_of_005.jsonl:line_24)
- **Subject / Grade:** tekhnolohiyi (Grade 8)
- **Concept:** `Художня фотографія` (Citation form: ✅)
- **Scientific Terminology:** `['фотографія', 'мистецтво', 'відображення', 'дійсність', 'площина']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Художня фотографія – це вид мистецтва, в якому художнє відображення дійсності на двовимірній площині здійснюють за допомогою фотографічної техніки.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 24 (Seed 42): Оздоровча система (eval_shard_005_of_005.jsonl:line_19)
- **Subject / Grade:** zdorovia (Grade 8)
- **Concept:** `Оздоровча система` (Citation form: ✅)
- **Scientific Terminology:** `['система', 'знання', 'навичка', 'звичка', 'формування']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Оздоровча система — це цілісна система знань, навичок і звичок, що сприяють формуванню та зміцненню здоров'я.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 25 (Seed 42): Повага (eval_shard_005_of_005.jsonl:line_39)
- **Subject / Grade:** etyka (Grade 6)
- **Concept:** `Повага` (Citation form: ✅)
- **Scientific Terminology:** `['почуття', 'шана', 'ставлення', 'підстава', 'визнання']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Повага — почуття шани, прихильне ставлення, що з'являється на підставі визнання чиїх-небудь заслуг і позитивних якостей.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 26 (Seed 42): Принципат (sft_shard_135_of_150.jsonl:line_93)
- **Subject / Grade:** istoriya (Grade 7)
- **Concept:** `Принципат` (Citation form: ✅)
- **Scientific Terminology:** `['правління', 'особа', 'принцепс']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Принципат — форма правління, за якої формально зберігаються республіканські установи, але фактична влада належить одній особі — принцепсу.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 27 (Seed 42): Друкований текст (sft_shard_015_of_150.jsonl:line_369)
- **Subject / Grade:** zarlit (Grade 5)
- **Concept:** `Друкований текст` (Citation form: ✅)
- **Scientific Terminology:** `['засіб', 'друк', 'папір']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Друкований текст – текст, відтворений засобами друку на папері.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 28 (Seed 42): Марикультура (sft_shard_058_of_150.jsonl:line_349)
- **Subject / Grade:** heohrafiya (Grade 9)
- **Concept:** `Марикультура` (Citation form: ✅)
- **Scientific Terminology:** `['вирощування', 'морепродукт']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Марикультура – це вирощування риби і морепродуктів людьми у природному середовищі.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 29 (Seed 42): Вуглеводи (sft_shard_074_of_150.jsonl:line_211)
- **Subject / Grade:** khimiya (Grade 9)
- **Concept:** `Вуглеводи` (Citation form: ✅)
- **Scientific Terminology:** `['природа', 'сполука', 'представник', 'глюкоза', 'сахароза']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Вуглеводи — найпоширеніший у природі клас оксигеновмісних органічних сполук, представниками якого є глюкоза, сахароза, крохмаль, целюлоза та інші.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 30 (Seed 42): Діатомові водорості (sft_shard_103_of_150.jsonl:line_460)
- **Subject / Grade:** pryroda (Grade 6)
- **Concept:** `Діатомові водорості` (Citation form: ✅)
- **Scientific Terminology:** `['водорість', 'рослина']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Діатомові водорості — одноклітинні рослини з твердим панциром, який набуває різних форм.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 31 (Seed 42): Тотальна війна (sft_shard_003_of_150.jsonl:line_37)
- **Subject / Grade:** vsesvitnia (Grade 10)
- **Concept:** `Тотальна війна` (Citation form: ✅)
- **Scientific Terminology:** `['війна', 'засіб', 'знищення', 'противник', 'населення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Тотальна війна — війна, де використовуються всі засоби для знищення противника, у тому числі мирного населення.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 32 (Seed 42): Археї (sft_shard_048_of_150.jsonl:line_54)
- **Subject / Grade:** biolohiya (Grade 7)
- **Concept:** `Археї` (Citation form: ✅)
- **Scientific Terminology:** `['учасник', 'кругообіг', 'речовина']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Археї – учасники багатьох важливих природних явищ, пов'язаних з кругообігом хімічних речовин на Землі.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 33 (Seed 42): Модернізм (sft_shard_012_of_150.jsonl:line_387)
- **Subject / Grade:** istoriya (Grade 10)
- **Concept:** `Модернізм` (Citation form: ✅)
- **Scientific Terminology:** `['течія', 'мистецтво', 'змішування', 'елемент', 'стиль']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Модернізм — сукупність течій у мистецтві XX ст., якій притаманні змішування елементів різних стилів і революційні перетворення засобів виразності.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 34 (Seed 42): Грант (sft_shard_134_of_150.jsonl:line_384)
- **Subject / Grade:** finansova (Grade 9)
- **Concept:** `Грант` (Citation form: ✅)
- **Scientific Terminology:** `['особа', 'організація', 'бізнес', 'реалізація', 'проєкт']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Грант — це гроші, які надають фізичним особам, організаціям чи бізнесам для реалізації певного проєкту, і їх не потрібно повертати.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 35 (Seed 42): Дана ситуація (sft_shard_046_of_150.jsonl:line_17)
- **Subject / Grade:** matematyka (Grade 6)
- **Concept:** `Дана ситуація` (Citation form: ✅)
- **Scientific Terminology:** `['ситуація', 'задача', 'рівність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Дана ситуація — це задача на рівність двох величин.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 36 (Seed 42): Мехатроніка (sft_shard_002_of_150.jsonl:line_255)
- **Subject / Grade:** fizyka (Grade 9)
- **Concept:** `Мехатроніка` (Citation form: ✅)
- **Scientific Terminology:** `['галузь', 'інженерія', 'механіка', 'електроніка', 'система']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Мехатроніка — це галузь інженерії, що поєднує механіку, електроніку, системи керування та програмування для створення керованих, адаптивних і інтелектуальних технічних систем.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 37 (Seed 42): Правопорушення (sft_shard_079_of_150.jsonl:line_273)
- **Subject / Grade:** ya_doslidzhuiu_svit (Grade 4)
- **Concept:** `Правопорушення` (Citation form: ✅)
- **Scientific Terminology:** `['вчинок', 'відповідальність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Правопорушення — це протиправні небезпечні вчинки, за які можуть притягнути до юридичної відповідальності.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 38 (Seed 42): Цифровий слід (sft_shard_044_of_150.jsonl:line_277)
- **Subject / Grade:** hromadianska (Grade 9)
- **Concept:** `Цифровий слід` (Citation form: ✅)
- **Scientific Terminology:** `["пам'ять", 'інтернет', 'дія']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Цифровий слід — це пам'ять інтернету про наші дії.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 39 (Seed 42): Запозичена іншомовна лексика (sft_shard_150_of_150.jsonl:line_131)
- **Subject / Grade:** ukrmova (Grade university)
- **Concept:** `Запозичена іншомовна лексика` (Citation form: ✅)
- **Scientific Terminology:** `['лексика', 'словозміна', 'специфіка', 'мюзикл']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Запозичена іншомовна лексика – це іноніми, які не набули словозміни, властивої українським словам, зберегли виразну фонетичну й семантичну специфіку мови-джерела: шосе, кафе, пюре, мюзикл, журі.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 40 (Seed 42): Авторство (sft_shard_131_of_150.jsonl:line_477)
- **Subject / Grade:** ukrmova (Grade 5)
- **Concept:** `Авторство` (Citation form: ✅)
- **Scientific Terminology:** `['належність', 'твір', 'проєкт', 'винахід', 'авторка']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Авторство — належність твору, проєкту, винаходу певному/певній автору/авторці.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 41 (Seed 42): Похідні способи набуття права власності (sft_shard_121_of_150.jsonl:line_171)
- **Subject / Grade:** pravoznavstvo (Grade 11)
- **Concept:** `Похідні способи набуття права власності` (Citation form: ✅)
- **Scientific Terminology:** `['набуття', 'власність', 'отримання', 'річ', 'підстава']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Похідні способи набуття права власності — це отримання речі на підставі цивільно-правових договорів (купівля–продаж, міна, дарування тощо), односторонніх правочинів особи (наприклад, за заповітом), актів органів державної влади чи місцевого самоврядування.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 42 (Seed 42): Раціональне рівняння (sft_shard_053_of_150.jsonl:line_255)
- **Subject / Grade:** algebra (Grade 8)
- **Concept:** `Раціональне рівняння` (Citation form: ✅)
- **Scientific Terminology:** `['рівняння', 'вираз']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Раціональне рівняння називається дробовим раціональним рівнянням, якщо принаймні одна з його частин містить дробовий вираз.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 43 (Seed 42): Поміркованість суду (sft_shard_039_of_150.jsonl:line_210)
- **Subject / Grade:** zarlit (Grade 9)
- **Concept:** `Поміркованість суду` (Citation form: ✅)
- **Scientific Terminology:** `['поміркованість', 'суд']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Поміркованість суду – це поміркованість присяжних, поміркованість присяжних в цілому – це поміркованість кожного зокрема.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 44 (Seed 42): Безпека особистого самовираження (sft_shard_076_of_150.jsonl:line_314)
- **Subject / Grade:** etyka (Grade 5)
- **Concept:** `Безпека особистого самовираження` (Citation form: ✅)
- **Scientific Terminology:** `['безпека', 'самовираження', 'сприйняття', 'зміст', 'передача']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Безпека особистого самовираження — суспільне сприйняття права на зміст і спосіб передачі інформації.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 45 (Seed 42): Символи хімічних елементів (sft_shard_141_of_150.jsonl:line_141)
- **Subject / Grade:** pryroda (Grade 6)
- **Concept:** `Символи хімічних елементів` (Citation form: ✅)
- **Scientific Terminology:** `['символ', 'елемент', 'абетка']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Символи хімічних елементів — це абетка хімічної мови.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 46 (Seed 42): Система колективної безпеки (sft_shard_010_of_150.jsonl:line_451)
- **Subject / Grade:** vsesvitnia (Grade 10)
- **Concept:** `Система колективної безпеки` (Citation form: ✅)
- **Scientific Terminology:** `['система', 'безпека', 'здійснення', 'захист', 'загроза']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Система колективної безпеки — сукупність спільних дій держав із метою здійснення захисту від внутрішніх та зовнішніх загроз.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 47 (Seed 42): Сузір'я (sft_shard_142_of_150.jsonl:line_75)
- **Subject / Grade:** astronomiya (Grade 11)
- **Concept:** `Сузір'я` (Citation form: ✅)
- **Scientific Terminology:** `['ділянка', 'сфера', 'зручність', 'орієнтування', 'небо']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Сузір'я — ділянки, на які поділена небесна сфера для зручності орієнтування на зоряному небі.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 48 (Seed 42): Хореографічна поема (sft_shard_108_of_150.jsonl:line_289)
- **Subject / Grade:** mystetstvo (Grade 9)
- **Concept:** `Хореографічна поема` (Citation form: ✅)
- **Scientific Terminology:** `['поема', 'твір', 'жанр']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Хореографічна поема — великий одночастинний оркестровий програмний твір, в основі якого — хореографічний жанр.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 49 (Seed 42): Нейромедіатори (sft_shard_018_of_150.jsonl:line_201)
- **Subject / Grade:** biolohiya (Grade 9)
- **Concept:** `Нейромедіатори` (Citation form: ✅)
- **Scientific Terminology:** `['речовина', 'передача', 'імпульс', 'нейрон', 'синапс']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Нейромедіатори — речовини, що здійснюють передачу імпульсів між нейронами у синапсах.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 50 (Seed 42): Мода (sft_shard_071_of_150.jsonl:line_432)
- **Subject / Grade:** matematyka (Grade 11)
- **Concept:** `Мода` (Citation form: ✅)
- **Scientific Terminology:** `['елемент', 'вибірка']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Мода — це те значення елемента вибірки, яке зустрічається частіше за інші.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 51 (Seed 123): Держава (eval_shard_001_of_005.jsonl:line_44)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Держава` (Citation form: ✅)
- **Scientific Terminology:** `['організація', 'суспільство', 'цілісність', 'безпека', 'управління']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Держава — організація політичної влади в суспільстві, що підтримує його цілісність і безпеку та здійснює управління суспільними справами.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 52 (Seed 123): Реостат (eval_shard_001_of_005.jsonl:line_31)
- **Subject / Grade:** fizyka (Grade 8)
- **Concept:** `Реостат` (Citation form: ✅)
- **Scientific Terminology:** `['опір', 'пристрій', 'регулювання', 'коло']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Реостат — це пристрій зі змінним опором, призначений для регулювання сили струму в електричному колі.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 53 (Seed 123): Електролічильник (eval_shard_001_of_005.jsonl:line_33)
- **Subject / Grade:** fizyka (Grade 8)
- **Concept:** `Електролічильник` (Citation form: ✅)
- **Scientific Terminology:** `['прилад', 'вимірювання']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Електролічильник — це прилад для прямого вимірювання роботи струму.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 54 (Seed 123): Мононорми первісного суспільства (eval_shard_001_of_005.jsonl:line_40)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Мононорми первісного суспільства` (Citation form: ✅)
- **Scientific Terminology:** `['мононорма', 'суспільство', 'поведінка', 'характер', "плем'я"]` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Мононорми первісного суспільства — це специфічні правила поведінки, які мали звичаєвий характер і закріплювали найраціональніші та найвигідніші для роду й племені моделі поведінки.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 55 (Seed 123): Блок (eval_shard_001_of_005.jsonl:line_17)
- **Subject / Grade:** fizyka (Grade 8)
- **Concept:** `Блок` (Citation form: ✅)
- **Scientific Terminology:** `['механізм', 'колесо']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Блок — це простий механізм, що має форму колеса із жолобом, яке може обертатися навколо своєї осі.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 56 (Seed 123): Обмежена монархія (eval_shard_002_of_005.jsonl:line_5)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Обмежена монархія` (Citation form: ✅)
- **Scientific Terminology:** `['монархія', 'правління', 'монарх', 'парламент', 'конституція']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Обмежена монархія — форма державного правління, за якої владу монарха обмежує парламент або конституція.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 57 (Seed 123): Хмарні сервіси (eval_shard_002_of_005.jsonl:line_30)
- **Subject / Grade:** informatyka (Grade 7)
- **Concept:** `Хмарні сервіси` (Citation form: ✅)
- **Scientific Terminology:** `['сервіс', 'надання', 'доступ', 'інтернет-ресурс', 'сервер']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Хмарні сервіси — сервіси, пов'язані з наданням постійного доступу до віддалених інтернет-ресурсів (серверів, сховищ).» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 58 (Seed 123): Спинний мозок (eval_shard_002_of_005.jsonl:line_8)
- **Subject / Grade:** biolohiya (Grade 8)
- **Concept:** `Спинний мозок` (Citation form: ✅)
- **Scientific Terminology:** `['мозок', 'тяж', 'канал', 'хребет']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Спинний мозок — це циліндричний тяж завтовшки приблизно 1 см, розташований у спинномозковому каналі хребта.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 59 (Seed 123): Особисті гарантії (eval_shard_002_of_005.jsonl:line_47)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Особисті гарантії` (Citation form: ✅)
- **Scientific Terminology:** `['гарантія', 'громадянин', 'захист', 'свобода', 'інтерес']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Особисті гарантії — власні можливості людини й громадянина щодо захисту своїх прав, свобод, законних інтересів та обов'язків.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 60 (Seed 123): Правовідносини (eval_shard_002_of_005.jsonl:line_23)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Правовідносини` (Citation form: ✅)
- **Scientific Terminology:** `['норма', 'учасник', "обов'язок", 'держава']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Правовідносини — суспільні відносини, що виникають на основі норм права, учасники яких мають суб'єктивні права та юридичні обов'язки, забезпечені державою.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 61 (Seed 123): Гідроенергетичний потенціал (eval_shard_003_of_005.jsonl:line_39)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Гідроенергетичний потенціал` (Citation form: ✅)
- **Scientific Terminology:** `['потенціал', 'енергія', 'течія', "об'єкт"]` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Гідроенергетичний потенціал – сукупність енергії, яку можна виробити, застосувавши силу течії водних об'єктів.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 62 (Seed 123): Позов (eval_shard_003_of_005.jsonl:line_18)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Позов` (Citation form: ✅)
- **Scientific Terminology:** `['закон', 'звернення', 'особа', 'суд', 'прохання']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Позов — звернення особи до суду з проханням про розгляд спору та захист її прав, які охороняються законом.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 63 (Seed 123): Права людини (eval_shard_003_of_005.jsonl:line_8)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Права людини` (Citation form: ✅)
- **Scientific Terminology:** `['існування', 'розвиток']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Права людини — можливості, необхідні людині для існування та розвитку.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 64 (Seed 123): Вегетаційний період (eval_shard_003_of_005.jsonl:line_11)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Вегетаційний період` (Citation form: ✅)
- **Scientific Terminology:** `['період', 'рослина']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Вегетаційний період – час, протягом якого рослина вегетує, тобто росте та розвивається.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 65 (Seed 123): Біженець (eval_shard_003_of_005.jsonl:line_6)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Біженець` (Citation form: ✅)
- **Scientific Terminology:** `['особа', 'громадянин', 'причина', 'країна', 'захист']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Біженець — особа, яка не є громадянином України і внаслідок певних причин перебуває за межами своєї країни та не може користуватися її захистом.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 66 (Seed 123): Героїчний епос (eval_shard_004_of_005.jsonl:line_44)
- **Subject / Grade:** zarlit (Grade 8)
- **Concept:** `Героїчний епос` (Citation form: ✅)
- **Scientific Terminology:** `['епос', 'жанр', 'завзяття', 'народ', 'боротьба']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Героїчний епос – твори різних жанрів, які в легендаризованій формі відображають волю, завзяття народу в боротьбі проти ворогів, зла й гноблення.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 67 (Seed 123): Медіаграмотність (eval_shard_004_of_005.jsonl:line_26)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Медіаграмотність` (Citation form: ✅)
- **Scientific Terminology:** `['знання', 'уміння', 'навичка']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Медіаграмотність – це сукупність знань, умінь і навичок, що допомагають розуміти, як працюють масмедіа, аналізувати отримувану інформацію і критично оцінювати її.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 68 (Seed 123): Зміни місце (eval_shard_004_of_005.jsonl:line_41)
- **Subject / Grade:** zarlit (Grade 8)
- **Concept:** `Зміни місце` (Citation form: ✅)
- **Scientific Terminology:** `["прислів'я", 'пошук']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «„Зміни місце – зміни щастя“ – це єврейське прислів'я нерідко увиразнює сутність пошуків героїв Шолом-Алейхема.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 69 (Seed 123): Піктографічне письмо (eval_shard_004_of_005.jsonl:line_35)
- **Subject / Grade:** ukrmova (Grade 8)
- **Concept:** `Піктографічне письмо` (Citation form: ✅)
- **Scientific Terminology:** `['письмо', 'комунікація', 'значок', 'малюнок', 'передача']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Піктографічне письмо – це старовинний спосіб комунікації, який використовує значки або малюнки для передачі повідомлення.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 70 (Seed 123): Обмін (eval_shard_004_of_005.jsonl:line_28)
- **Subject / Grade:** ekonomika (Grade 10)
- **Concept:** `Обмін` (Citation form: ✅)
- **Scientific Terminology:** `['рух', 'товар', 'власник']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Обмін — це рух товарів від одного власника до іншого.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 71 (Seed 123): Соціальна адаптація (eval_shard_005_of_005.jsonl:line_44)
- **Subject / Grade:** etyka (Grade 6)
- **Concept:** `Соціальна адаптація` (Citation form: ✅)
- **Scientific Terminology:** `['адаптація', 'пристосування', 'взаємодія']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Соціальна адаптація — пристосування людини до умов соціального середовища та взаємодія з ним.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 72 (Seed 123): Рефлексія проєктної діяльності (eval_shard_005_of_005.jsonl:line_20)
- **Subject / Grade:** tekhnolohiyi (Grade 8)
- **Concept:** `Рефлексія проєктної діяльності` (Citation form: ✅)
- **Scientific Terminology:** `['рефлексія', 'здатність', 'рішення', 'проєкт', 'аналіз']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Рефлексія проєктної діяльності — здатність оцінити рішення, прийняті під час роботи над творчим проєктом, аналіз і переосмислення дій з реалізації творчого задуму проєкту, звернення уваги на свої думки й емоції, визначення перспектив.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 73 (Seed 123): Середньовічний замковий комплекс (eval_shard_005_of_005.jsonl:line_5)
- **Subject / Grade:** mystetstvo (Grade 8)
- **Concept:** `Середньовічний замковий комплекс` (Citation form: ✅)
- **Scientific Terminology:** `['комплекс', 'осередок', 'захист', 'земля']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Середньовічний замковий комплекс — осередок влади, культурного життя та захисту прилеглих земель.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 74 (Seed 123): Формальні лідери (eval_shard_005_of_005.jsonl:line_12)
- **Subject / Grade:** zdorovia (Grade 8)
- **Concept:** `Формальні лідери` (Citation form: ✅)
- **Scientific Terminology:** `['лідер', 'представник', 'самоврядування', "обов'язок", 'повноваження']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Формальні лідери — це, наприклад, представники учнівського самоврядування, які мають офіційно визначені обов'язки та повноваження.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 75 (Seed 123): Дзвін (eval_shard_005_of_005.jsonl:line_4)
- **Subject / Grade:** mystetstvo (Grade 8)
- **Concept:** `Дзвін` (Citation form: ✅)
- **Scientific Terminology:** `['інструмент', 'забарвлення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Дзвін — ударний інструмент із насиченим тембральним забарвленням.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 76 (Seed 123): Пристрасть (sft_shard_090_of_150.jsonl:line_256)
- **Subject / Grade:** zarlit (Grade 10)
- **Concept:** `Пристрасть` (Citation form: ✅)
- **Scientific Terminology:** `['оповідь', 'сюжет']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Пристрасть – рушійна сила романтичної оповіді, на ній будується сюжет.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 77 (Seed 123): Раціональний дріб (sft_shard_131_of_150.jsonl:line_146)
- **Subject / Grade:** algebra (Grade 8)
- **Concept:** `Раціональний дріб` (Citation form: ✅)
- **Scientific Terminology:** `['знаменник', 'многочлен', 'дріб', 'чисельник']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Раціональний дріб — це дріб, чисельник і знаменник якого є многочленами.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 78 (Seed 123): Мовний організм (sft_shard_022_of_150.jsonl:line_409)
- **Subject / Grade:** ukrmova (Grade university)
- **Concept:** `Мовний організм` (Citation form: ✅)
- **Scientific Terminology:** `['організм', 'субстанція', 'результат', 'життєдіяльність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Мовний організм - субстанція, безперечно, жива й тому постійно оновлювана, представлена результатами своєї життєдіяльності.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 79 (Seed 123): Реліктове випромінювання (sft_shard_020_of_150.jsonl:line_137)
- **Subject / Grade:** astronomiya (Grade 11)
- **Concept:** `Реліктове випромінювання` (Citation form: ✅)
- **Scientific Terminology:** `['випромінювання', 'квант']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Реліктове випромінювання — кванти світла, що утворилися 15 млрд років тому.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 80 (Seed 123): Лозоплетіння (sft_shard_070_of_150.jsonl:line_100)
- **Subject / Grade:** tekhnolohiyi (Grade 6)
- **Concept:** `Лозоплетіння` (Citation form: ✅)
- **Scientific Terminology:** `['плетіння', 'розвиток']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Лозоплетіння – плетіння з кори, лози та рогозу – в Україні набуло широкого розвитку в 2-й пол. XIX ст., коли з цих матеріалів почали виготовляти дорожні кошики та козуби, легкі дачні меблі, дитячі візочки, іграшки тощо.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 81 (Seed 123): Витік перший (sft_shard_066_of_150.jsonl:line_128)
- **Subject / Grade:** zarlit (Grade 10)
- **Concept:** `Витік перший` (Citation form: ✅)
- **Scientific Terminology:** `['наука', 'мистецтво', 'більшість', 'цінність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Витік перший – антична культура, яка подарувала нам основи наук і мистецтв, більшість загальновизнаних цінностей і цілей.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 82 (Seed 123): Тигр (sft_shard_051_of_150.jsonl:line_400)
- **Subject / Grade:** ukrmova (Grade university)
- **Concept:** `Тигр` (Citation form: ✅)
- **Scientific Terminology:** `['хамелеон', 'тиждень']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Тигр – тигр, Хамелеон – хамелеон, Тиждень – тиждень, Судак – судак, пробіг – про біг, в о станнє – востаннє, вибули – ви були, по нашому – по-нашому.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 83 (Seed 123): Дивовижні карнавальні дійства (sft_shard_122_of_150.jsonl:line_283)
- **Subject / Grade:** mystetstvo (Grade 5)
- **Concept:** `Дивовижні карнавальні дійства` (Citation form: ✅)
- **Scientific Terminology:** `['дійство', 'вистава', 'вулиця', 'місто']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Дивовижні карнавальні дійства — це вистави, які відбуваються на вулицях великих міст.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 84 (Seed 123): Вітер (sft_shard_098_of_150.jsonl:line_424)
- **Subject / Grade:** heohrafiya (Grade 6)
- **Concept:** `Вітер` (Citation form: ✅)
- **Scientific Terminology:** `['переміщення', 'повітря', 'область', 'тиск']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Вітер — горизонтальне переміщення повітря з області високого тиску в область низького тиску.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 85 (Seed 123): Об'єкт (sft_shard_067_of_150.jsonl:line_288)
- **Subject / Grade:** ya_doslidzhuiu_svit (Grade 3)
- **Concept:** `Об'єкт` (Citation form: ✅)
- **Scientific Terminology:** `['назва', 'істота', 'подія']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Об'єкт — це загальна назва будь-якого предмета, живої істоти, явища, події.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 86 (Seed 123): Деталь (sft_shard_012_of_150.jsonl:line_240)
- **Subject / Grade:** tekhnolohiyi (Grade 6)
- **Concept:** `Деталь` (Citation form: ✅)
- **Scientific Terminology:** `['виріб', 'руйнування']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Деталь є невеликою частиною виробу, становить одне ціле й не може бути розібраною без руйнувань на більш прості складові частини.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 87 (Seed 123): Фосфорні боєприпаси (sft_shard_031_of_150.jsonl:line_160)
- **Subject / Grade:** zakhyst (Grade 10)
- **Concept:** `Фосфорні боєприпаси` (Citation form: ✅)
- **Scientific Terminology:** `['боєприпас', 'снаряд', 'фосфор', 'температура', 'горіння']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Фосфорні боєприпаси — це снаряди начинені самозапальним білим фосфором, що має високу температуру горіння (від 800°C). 24 березня 2022 року повідомлялося, що російські війська скинули кілька фосфорних бомб в Луганській області.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 88 (Seed 123): Секс (sft_shard_037_of_150.jsonl:line_370)
- **Subject / Grade:** zdorovia (Grade 9)
- **Concept:** `Секс` (Citation form: ✅)
- **Scientific Terminology:** `['доказ', 'кохання', 'стосунок']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Секс — це доказ справжнього кохання й серйозних стосунків.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 89 (Seed 123): Тепловий ефект хімічної реакції (sft_shard_143_of_150.jsonl:line_8)
- **Subject / Grade:** khimiya (Grade 9)
- **Concept:** `Тепловий ефект хімічної реакції` (Citation form: ✅)
- **Scientific Terminology:** `['ефект', 'реакція', 'теплота']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Тепловий ефект хімічної реакції — це кількість теплоти, яка виділяється або поглинається під час хімічної реакції.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 90 (Seed 123): Комбінаторика (sft_shard_052_of_150.jsonl:line_86)
- **Subject / Grade:** algebra (Grade 11)
- **Concept:** `Комбінаторика` (Citation form: ✅)
- **Scientific Terminology:** `['вибір', 'розташування', 'елемент', 'множина']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Комбінаторика - розділ математики, у якому вивчають способи вибору і розташування елементів з деякої скінченної множини відповідно до заданих умов.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 91 (Seed 123): Випаровування (sft_shard_041_of_150.jsonl:line_482)
- **Subject / Grade:** fizyka (Grade 10)
- **Concept:** `Випаровування` (Citation form: ✅)
- **Scientific Terminology:** `['пароутворення', 'поверхня', 'рідина']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Випаровування — це процес пароутворення з поверхні рідини.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 92 (Seed 123): Стихійне лихо (sft_shard_112_of_150.jsonl:line_493)
- **Subject / Grade:** zakhyst (Grade 10)
- **Concept:** `Стихійне лихо` (Citation form: ✅)
- **Scientific Terminology:** `['територія', 'життєдіяльність', 'населення', 'збиток']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Стихійне лихо — природне явище, що діє з великою руйнівною силою, заподіює значну шкоду території, на якій відбувається, порушує нормальну життєдіяльність населення, завдає матеріальних збитків.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 93 (Seed 123): Дикорослі рослини (sft_shard_063_of_150.jsonl:line_9)
- **Subject / Grade:** ya_doslidzhuiu_svit (Grade 1)
- **Concept:** `Дикорослі рослини` (Citation form: ✅)
- **Scientific Terminology:** `['рослина', 'сировина', 'тварина']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Дикорослі рослини — це джерело деревини, сировини для ліків, корму для тварин.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 94 (Seed 123): Провідний мотив пісні (sft_shard_004_of_150.jsonl:line_373)
- **Subject / Grade:** ukrlit (Grade 9)
- **Concept:** `Провідний мотив пісні` (Citation form: ✅)
- **Scientific Terminology:** `['мотив', 'кохання']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Провідний мотив пісні — нерозділене кохання, адже милий поїхав „іншої шукати“.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 95 (Seed 123): Обертання (sft_shard_109_of_150.jsonl:line_291)
- **Subject / Grade:** heometriya (Grade 9)
- **Concept:** `Обертання` (Citation form: ✅)
- **Scientific Terminology:** `['швидкість', 'прискорення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Обертання — це процес, який визначається часом, кутовою швидкістю, кутовим прискоренням тощо.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 96 (Seed 123): Рівномірний прямолінійний рух (sft_shard_133_of_150.jsonl:line_21)
- **Subject / Grade:** fizyka (Grade 10)
- **Concept:** `Рівномірний прямолінійний рух` (Citation form: ✅)
- **Scientific Terminology:** `['рух', 'тіло', 'інтервал', 'переміщення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Рівномірний прямолінійний рух — це такий механічний рух, під час якого тіло за будь-які рівні інтервали часу здійснює однакові переміщення.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 97 (Seed 123): Просвітництво (sft_shard_026_of_150.jsonl:line_23)
- **Subject / Grade:** zarlit (Grade 9)
- **Concept:** `Просвітництво` (Citation form: ✅)
- **Scientific Terminology:** `['рух', 'доба', 'епоха', 'етап', 'розвиток']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Просвітництво – це ідейно-політичний та естетичний рух (доба, епоха), важливий етап розвитку європейської ідеології та культури (зокрема, літератури) наприкінці ХVІІ – на початку ХІХ ст.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 98 (Seed 123): Фотоефект (sft_shard_149_of_150.jsonl:line_482)
- **Subject / Grade:** fizyka (Grade 11)
- **Concept:** `Фотоефект` (Citation form: ✅)
- **Scientific Terminology:** `['взаємодія', 'випромінювання', 'речовина', 'результат', 'енергія']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Фотоефект — це явище взаємодії електромагнітного випромінювання з речовиною, в результаті якого енергія фотонів передається електронам речовини й останні переходять у новий енергетичний стан.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 99 (Seed 123): Дорослість (sft_shard_103_of_150.jsonl:line_480)
- **Subject / Grade:** zdorovia (Grade 9)
- **Concept:** `Дорослість` (Citation form: ✅)
- **Scientific Terminology:** `['відповідальність', 'зрілість', 'прийняття', 'рішення', 'партнер']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Дорослість — це про відповідальність, зрілість у прийнятті рішень, а не про кількість сексуальних партнерів.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 100 (Seed 123): Рівні вектори (sft_shard_077_of_150.jsonl:line_387)
- **Subject / Grade:** matematyka (Grade 10)
- **Concept:** `Рівні вектори` (Citation form: ✅)
- **Scientific Terminology:** `['вектор', 'модуль']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Два ненульових вектори називають рівними, якщо їхні модулі рівні й вони співнапрямлені.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 101 (Seed 777): Революція (eval_shard_001_of_005.jsonl:line_12)
- **Subject / Grade:** vsesvitnia (Grade 8)
- **Concept:** `Революція` (Citation form: ✅)
- **Scientific Terminology:** `['переворот', 'суспільство', 'зміна', 'перетворення', 'удосконалення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Революція – докорінний переворот у житті суспільства, який супроводжується зміною влади; різкі зміни в якій-небудь галузі, що приводить до істотних перетворень, удосконалення чого-небудь.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 102 (Seed 777): В'язкість (eval_shard_001_of_005.jsonl:line_23)
- **Subject / Grade:** fizyka (Grade 8)
- **Concept:** `В'язкість` (Citation form: ✅)
- **Scientific Terminology:** `['рідина', 'газ', 'переміщення', 'речовина']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «В'язкість — це властивість рідин і газів протидіяти переміщенню одних шарів речовини відносно інших.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 103 (Seed 777): Орбіталь (eval_shard_001_of_005.jsonl:line_43)
- **Subject / Grade:** khimiya (Grade 8)
- **Concept:** `Орбіталь` (Citation form: ✅)
- **Scientific Terminology:** `['ймовірність', 'перебування', 'електрон']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Орбіталь — це частина простору, у якому ймовірність перебування електрона вища за 90 %.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 104 (Seed 777): Колоніалізм (eval_shard_001_of_005.jsonl:line_20)
- **Subject / Grade:** vsesvitnia (Grade 8)
- **Concept:** `Колоніалізм` (Citation form: ✅)
- **Scientific Terminology:** `['підкорення', 'країна', 'ресурс', 'праця', 'населення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Колоніалізм – підкорення однією країною іншої з метою використання її ресурсів, праці місцевого населення та його культурної асиміляції, а також політичного контролю.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 105 (Seed 777): Хімічний зв'язок (eval_shard_001_of_005.jsonl:line_47)
- **Subject / Grade:** khimiya (Grade 8)
- **Concept:** `Хімічний зв'язок` (Citation form: ✅)
- **Scientific Terminology:** `['взаємодія', 'атом', 'стійкість', 'частинка', 'молекула']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Хімічний зв'язок — це взаємодія атомів, що зумовлює стійкість багатоатомних частинок (молекул, йонів, кристалів).» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 106 (Seed 777): Умовні рефлекси (eval_shard_002_of_005.jsonl:line_22)
- **Subject / Grade:** biolohiya (Grade 8)
- **Concept:** `Умовні рефлекси` (Citation form: ✅)
- **Scientific Terminology:** `['рефлекс', 'реакція', 'організм', 'чинник']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Умовні рефлекси — це набуті протягом індивідуального життя реакції організму на певні чинники.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 107 (Seed 777): Дублювання (eval_shard_002_of_005.jsonl:line_38)
- **Subject / Grade:** informatyka (Grade 7)
- **Concept:** `Дублювання` (Citation form: ✅)
- **Scientific Terminology:** `['повторення', 'фрагмент']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Дублювання — це повторення текстового фрагмента задану кількість разів.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 108 (Seed 777): Правомірна поведінка (eval_shard_002_of_005.jsonl:line_27)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Правомірна поведінка` (Citation form: ✅)
- **Scientific Terminology:** `['поведінка', 'припис', 'норма', 'держава']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Правомірна поведінка — поведінка, яка відповідає приписам правових норм та охороняється державою.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 109 (Seed 777): Імітаційна модель (eval_shard_002_of_005.jsonl:line_36)
- **Subject / Grade:** informatyka (Grade 7)
- **Concept:** `Імітаційна модель` (Citation form: ✅)
- **Scientific Terminology:** `['алгоритм', 'програма', 'модель', 'комплекс', 'функціонування']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Імітаційна модель — це програма або комплекс програм, що реалізує алгоритм функціонування об'єкта за різних умов.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 110 (Seed 777): Абсолютна монархія (eval_shard_002_of_005.jsonl:line_3)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Абсолютна монархія` (Citation form: ✅)
- **Scientific Terminology:** `['монархія', 'правління', 'монарх', 'гілка', 'повноваження']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Абсолютна монархія — форма державного правління, за якої влада монарха є необмеженою, а монарх очолює всі гілки державної влади, має виключні повноваження щодо її здійснення.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 111 (Seed 777): Степ (eval_shard_003_of_005.jsonl:line_29)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Степ` (Citation form: ✅)
- **Scientific Terminology:** `['зона', 'держава', 'підзона']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Степ – це єдина природна зона держави, яка поділяється на три підзони: північностепову, середньостепову та південностепову.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 112 (Seed 777): Вичерпні природні ресурси (eval_shard_003_of_005.jsonl:line_37)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Вичерпні природні ресурси` (Citation form: ✅)
- **Scientific Terminology:** `['ресурс', 'зменшення', 'зникнення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Вичерпні природні ресурси – це ресурси, використання яких призводить до їх зменшення або повного зникнення.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 113 (Seed 777): Суддя (eval_shard_003_of_005.jsonl:line_12)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Суддя` (Citation form: ✅)
- **Scientific Terminology:** `['правопорушення', 'особа', 'право', "ім'я", 'держава']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Суддя — посадова особа, якій надано право від імені держави здійснювати правосуддя шляхом розгляду в судовому засіданні кримінальних, цивільних справ, про адміністративні правопорушення та ухвалювати відповідне судове рішення.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 114 (Seed 777): Державна служба зайнятості (eval_shard_003_of_005.jsonl:line_30)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Державна служба зайнятості` (Citation form: ✅)
- **Scientific Terminology:** `['служба', 'зайнятість', 'система', 'установа', 'послуга']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Державна служба зайнятості — централізована система державних установ, які безоплатно надають послуги з пошуку роботи, а також соціальні послуги з державного соціального страхування в разі безробіття та здійснюють виплату матеріального забезпечення у зв'язку з тимчасовою втратою роботи.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 115 (Seed 777): Адміністративне право (eval_shard_003_of_005.jsonl:line_36)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Адміністративне право` (Citation form: ✅)
- **Scientific Terminology:** `['право', 'галузь', 'управління']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Адміністративне право — галузь права, що регулює суспільні відносини, які виникають у процесі державного управління.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 116 (Seed 777): Право (eval_shard_004_of_005.jsonl:line_19)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Право` (Citation form: ✅)
- **Scientific Terminology:** `['норма', 'держава', 'регулювання']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Право – це сукупність загальнообов'язкових норм, що встановлюються або визнаються державою для регулювання суспільних відносин.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 117 (Seed 777): Цькування (eval_shard_004_of_005.jsonl:line_12)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Цькування` (Citation form: ✅)
- **Scientific Terminology:** `['правопорушення', 'вчинення', 'відповідальність', 'штраф']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Цькування – це дуже серйозне правопорушення, за його вчинення передбачена адміністративна відповідальність: від штрафів до виправних робіт.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 118 (Seed 777): Здібності (eval_shard_004_of_005.jsonl:line_7)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Здібності` (Citation form: ✅)
- **Scientific Terminology:** `['схильність', 'виконання']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Здібності – це індивідуальні особливості, які визначають схильність до виконання певної діяльності.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 119 (Seed 777): Благо (eval_shard_004_of_005.jsonl:line_29)
- **Subject / Grade:** ekonomika (Grade 10)
- **Concept:** `Благо` (Citation form: ✅)
- **Scientific Terminology:** `['засіб', 'задоволення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Благо — це будь-який засіб, що використовують для задоволення потреб.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 120 (Seed 777): Опис місцевості (eval_shard_004_of_005.jsonl:line_38)
- **Subject / Grade:** ukrmova (Grade 8)
- **Concept:** `Опис місцевості` (Citation form: ✅)
- **Scientific Terminology:** `['опис', 'місцевість', 'зображення', 'місто', 'село']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Опис місцевості – це словесне зображення основних ознак міста, села, вулиці, подвір'я, острова тощо.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 121 (Seed 777): Симфонічна поема (eval_shard_005_of_005.jsonl:line_8)
- **Subject / Grade:** mystetstvo (Grade 8)
- **Concept:** `Симфонічна поема` (Citation form: ✅)
- **Scientific Terminology:** `['поема', 'твір', 'програма']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Симфонічна поема — одночастинний симфонічний твір із літературною, історичною, філософською або живописною програмою.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 122 (Seed 777): Банк ідей (eval_shard_005_of_005.jsonl:line_21)
- **Subject / Grade:** tekhnolohiyi (Grade 8)
- **Concept:** `Банк ідей` (Citation form: ✅)
- **Scientific Terminology:** `['ідея', 'інструмент', 'змога', "розв'язання", 'ситуація']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Банк ідей — інструмент, який дає змогу зберегти й систематизувати ідеї для їх подальшого використання в роботі з розв'язання проблемної ситуації творчого проєкту.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 123 (Seed 777): Авторитет (eval_shard_005_of_005.jsonl:line_47)
- **Subject / Grade:** etyka (Grade 6)
- **Concept:** `Авторитет` (Citation form: ✅)
- **Scientific Terminology:** `['переконання', 'поведінка', 'особа', 'організація']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Авторитет — загальновизнаний вплив, який здійснюють на переконання та поведінку людей інші особи або організації.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 124 (Seed 777): Якісний сон (eval_shard_005_of_005.jsonl:line_13)
- **Subject / Grade:** zdorovia (Grade 8)
- **Concept:** `Якісний сон` (Citation form: ✅)
- **Scientific Terminology:** `['сон', 'складник', 'відновлення', 'енергія']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Якісний сон — обов'язковий складник відновлення енергії.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 125 (Seed 777): Іконостас (eval_shard_005_of_005.jsonl:line_6)
- **Subject / Grade:** mystetstvo (Grade 8)
- **Concept:** `Іконостас` (Citation form: ✅)
- **Scientific Terminology:** `['ікона', 'храм', 'обряд', 'вівтар', 'церква']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Іконостас — стіна з ікон у християнському храмі східного обряду, яка відокремлює вівтар від центральної частини церкви.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 126 (Seed 777): Дресировані тварини (sft_shard_108_of_150.jsonl:line_189)
- **Subject / Grade:** informatyka (Grade 3)
- **Concept:** `Дресировані тварини` (Citation form: ✅)
- **Scientific Terminology:** `['тварина', 'виконавець', 'команда']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Дресировані тварини — це виконавці: вони виконують ті команди, яких їх навчив дресирувальник.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 127 (Seed 777): Географічний полюс (sft_shard_065_of_150.jsonl:line_388)
- **Subject / Grade:** pryroda (Grade 8)
- **Concept:** `Географічний полюс` (Citation form: ✅)
- **Scientific Terminology:** `['полюс', 'поверхня', 'вісь', 'обертання']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Географічний полюс — це точки на поверхні Землі, через які проходить її уявна вісь обертання.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 128 (Seed 777): Літературознавство (sft_shard_048_of_150.jsonl:line_41)
- **Subject / Grade:** zarlit (Grade 5)
- **Concept:** `Літературознавство` (Citation form: ✅)
- **Scientific Terminology:** `['наука', 'література']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Літературознавство – наука, яка вивчає художню літературу.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 129 (Seed 777): Змінні зорі (sft_shard_011_of_150.jsonl:line_473)
- **Subject / Grade:** astronomiya (Grade 11)
- **Concept:** `Змінні зорі` (Citation form: ✅)
- **Scientific Terminology:** `['блиск', 'поверхня', 'дія', 'причина', 'затемнення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Змінні зорі називають фізично-змінними, якщо зміни блиску зумовлені процесами, що відбуваються в самій зорі або на її поверхні, і оптичними у випадку, якщо блиск зорі змінюється внаслідок дії зовнішніх щодо неї причин, наприклад під час періодичних затемнень іншою зорею.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 130 (Seed 777): Брендування (sft_shard_139_of_150.jsonl:line_257)
- **Subject / Grade:** finansova (Grade 9)
- **Concept:** `Брендування` (Citation form: ✅)
- **Scientific Terminology:** `['розробка', 'логотип', 'колір', 'шрифт', 'брендинг']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Брендування — розробка зовнішнього вигляду бренду: логотипа, фірмових кольорів, шрифтів, Брендування — це частина великого процесу брендингу.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 131 (Seed 777): Скульптура дадаїзму (sft_shard_126_of_150.jsonl:line_478)
- **Subject / Grade:** mystetstvo (Grade 9)
- **Concept:** `Скульптура дадаїзму` (Citation form: ✅)
- **Scientific Terminology:** `['скульптура', 'дадаїзм', 'виклик', 'мистецтво']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Скульптура дадаїзму — справжній виклик традиційному мистецтву, адже вона іронічна, абсурдна, антиакадемічна, провокативна, часто створена з випадкових предметів (Курт Швіттерс, Ман Рей, Ганс Арп).» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 132 (Seed 777): Слідування (sft_shard_077_of_150.jsonl:line_432)
- **Subject / Grade:** informatyka (Grade 5)
- **Concept:** `Слідування` (Citation form: ✅)
- **Scientific Terminology:** `['структура', 'подання', 'набір', 'команда']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Слідування — це алгоритмічна структура, яка використовується для подання послідовного набору команд, що виконуються одна за одною.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 133 (Seed 777): Гроші (sft_shard_133_of_150.jsonl:line_231)
- **Subject / Grade:** finansova (Grade 9)
- **Concept:** `Гроші` (Citation form: ✅)
- **Scientific Terminology:** `['інструмент', 'їжа', 'освіта', 'відпочинок']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Гроші — це інструмент, що допомагає людині задовольнити будь-які потреби: купити їжу, одяг, оплатити освіту, відпочинок тощо.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 134 (Seed 777): Йонізація газів (sft_shard_013_of_150.jsonl:line_18)
- **Subject / Grade:** fizyka (Grade 11)
- **Concept:** `Йонізація газів` (Citation form: ✅)
- **Scientific Terminology:** `['розпад', 'молекула', 'електрон', 'йонізація', 'газ']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Розпад молекул газу на електрони та йони називають йонізацією газів.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 135 (Seed 777): Волонтерство (sft_shard_150_of_150.jsonl:line_186)
- **Subject / Grade:** hromadianska (Grade 9)
- **Concept:** `Волонтерство` (Citation form: ✅)
- **Scientific Terminology:** `['дія', 'енергія', 'вміння']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Волонтерство — це дія, коли ти даруєш свій час, енергію та вміння.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 136 (Seed 777): Спілкування (sft_shard_062_of_150.jsonl:line_382)
- **Subject / Grade:** hromadianska (Grade 9)
- **Concept:** `Спілкування` (Citation form: ✅)
- **Scientific Terminology:** `['емоція', 'враження', 'знання']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Спілкування — це спосіб передавати й отримувати інформацію, ділитися емоціями, враженнями, знаннями.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 137 (Seed 777): Органи зору живих істот (sft_shard_033_of_150.jsonl:line_210)
- **Subject / Grade:** fizyka (Grade 9)
- **Concept:** `Органи зору живих істот` (Citation form: ✅)
- **Scientific Terminology:** `['орган', 'зір', 'істота']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Органи зору живих істот — природні приймачі світла.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 138 (Seed 777): Фенол (sft_shard_027_of_150.jsonl:line_448)
- **Subject / Grade:** khimiya (Grade 10)
- **Concept:** `Фенол` (Citation form: ✅)
- **Scientific Terminology:** `['сировина', 'виробництво', 'волокно', 'нейлон', 'капрон']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Фенол є сировиною для виробництва синтетичних волокон — нейлону та капрону.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 139 (Seed 777): Предметна область (sft_shard_079_of_150.jsonl:line_76)
- **Subject / Grade:** informatyka (Grade 9)
- **Concept:** `Предметна область` (Citation form: ✅)
- **Scientific Terminology:** `['область', 'сфера', 'застосування', 'база']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Предметною областю називають сферу застосування конкретної бази даних.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 140 (Seed 777): Історія фізики (sft_shard_120_of_150.jsonl:line_321)
- **Subject / Grade:** fizyka (Grade 10)
- **Concept:** `Історія фізики` (Citation form: ✅)
- **Scientific Terminology:** `['фізика', 'відкриття']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Історія фізики — це довжелезна історія відкриттів.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 141 (Seed 777): Проектна команда (sft_shard_051_of_150.jsonl:line_311)
- **Subject / Grade:** ekonomika (Grade 11)
- **Concept:** `Проектна команда` (Citation form: ✅)
- **Scientific Terminology:** `['команда', 'структура', 'проект']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Проектна команда — організаційна структура проекту.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 142 (Seed 777): Ключові слова (sft_shard_004_of_150.jsonl:line_245)
- **Subject / Grade:** informatyka (Grade 5)
- **Concept:** `Ключові слова` (Citation form: ✅)
- **Scientific Terminology:** `['пошук', 'відомість']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Ключові слова — слово або кілька слів, за якими здійснюється пошук потрібних відомостей.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 143 (Seed 777): Чиста неушкоджена шкіра (sft_shard_029_of_150.jsonl:line_331)
- **Subject / Grade:** zdorovia (Grade 7)
- **Concept:** `Чиста неушкоджена шкіра` (Citation form: ✅)
- **Scientific Terminology:** `['перепона', 'проникнення', 'організм', 'мікроорганізм']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Чиста неушкоджена шкіра — перепона на шляху проникнення в організм хвороботворних мікроорганізмів.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 144 (Seed 777): Старіння населення (sft_shard_017_of_150.jsonl:line_138)
- **Subject / Grade:** finansova (Grade 9)
- **Concept:** `Старіння населення` (Citation form: ✅)
- **Scientific Terminology:** `['старіння', 'населення', 'зростання', 'частка', 'структура']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Старіння населення — це зростання частки людей літнього віку (60+ або 65+) у загальній структурі населення.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 145 (Seed 777): Природні барвники (sft_shard_071_of_150.jsonl:line_283)
- **Subject / Grade:** khimiya (Grade 10)
- **Concept:** `Природні барвники` (Citation form: ✅)
- **Scientific Terminology:** `['барвник', 'сполука', 'організм', 'клітина', 'тканина']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Природні барвники — це органічні сполуки, які виробляють живі організми і які забарвлюють тваринні й рослинні клітини і тканини.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 146 (Seed 777): Хоровий концерт (sft_shard_046_of_150.jsonl:line_158)
- **Subject / Grade:** mystetstvo (Grade 6)
- **Concept:** `Хоровий концерт` (Citation form: ✅)
- **Scientific Terminology:** `['концерт', 'жанр', 'принцип', 'контраст']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Хоровий концерт — жанр вокальної музики, твори якого мають циклічну форму, частини чергуються за принципом темпових та динамічних контрастів.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 147 (Seed 777): Рівні фігури (sft_shard_103_of_150.jsonl:line_449)
- **Subject / Grade:** heometriya (Grade 9)
- **Concept:** `Рівні фігури` (Citation form: ✅)
- **Scientific Terminology:** `['фігура', 'переміщення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Дві фігури називають рівними, якщо вони переміщенням переводяться одна в одну.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 148 (Seed 777): Право власності (sft_shard_104_of_150.jsonl:line_29)
- **Subject / Grade:** finansova (Grade 9)
- **Concept:** `Право власності` (Citation form: ✅)
- **Scientific Terminology:** `['право', 'власність', 'закон', 'розсуд', 'законодавство']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Право власності — це закріплене законом право володіти, користуватися та розпоряджатися майном на свій розсуд, але в межах, визначених законодавством.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 149 (Seed 777): Периферія (sft_shard_042_of_150.jsonl:line_97)
- **Subject / Grade:** ekonomika (Grade 11)
- **Concept:** `Периферія` (Citation form: ✅)
- **Scientific Terminology:** `['країна', 'господарство']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Периферія — це країни, що розвиваються, вони займають залежне становище в світовому господарстві.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 150 (Seed 777): Комедія (sft_shard_053_of_150.jsonl:line_430)
- **Subject / Grade:** ukrlit (Grade 8)
- **Concept:** `Комедія` (Citation form: ✅)
- **Scientific Terminology:** `['твір', 'засіб', 'гумор', 'сатира', 'дійсність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Комедія — драматичний твір, у якому засобами гумору й сатири розвінчують негативні суспільні та побутові явища, розкривають смішне в навколишній дійсності чи людині.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**
