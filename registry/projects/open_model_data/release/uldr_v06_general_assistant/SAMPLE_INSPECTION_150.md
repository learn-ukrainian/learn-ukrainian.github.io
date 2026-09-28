# Multi-Seed Sample Inspection of 150 Mined Records (Phase 6.1)

**Audit Result:** ALL 150 RECORDS PASSED — 100% PASS RATE

**Sampling Protocol:** 3 PRNG seeds (42, 123, 777), 50 records per seed (total 150 records across eval and SFT shards).

## Release-Wide Defect Scan (All 75,000 SFT + 199 Eval Records)

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
| `appositive_double_dash_clauses` | 0 | ✅ 0 |
| `page_number_and_artifacts` | 0 | ✅ 0 |

## Multi-Seed Inspected Sample Overview

| # | Seed | Origin | Concept | Subject | Grade | Terms | Citation | Anaphora-Free | OCR-Clean | Def-Aligned | Terms Valid | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 42 | `eval_shard_001_of_005.jsonl:line_24` | **Плавлення** | fizyka | 8 | перехід, речовина | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 2 | 42 | `eval_shard_001_of_005.jsonl:line_34` | **Ізотопи** | khimiya | 8 | нуклід, елемент | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 3 | 42 | `eval_shard_001_of_005.jsonl:line_4` | **Панщина** | istoriya | 8 | виконання, селянин, обсяг, господарство | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 4 | 42 | `eval_shard_001_of_005.jsonl:line_12` | **Революція** | vsesvitnia | 8 | переворот, суспільство, зміна, перетворення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 5 | 42 | `eval_shard_001_of_005.jsonl:line_11` | **Протилежні вектори** | heometriya | 9 | вектор, модуль | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 6 | 42 | `eval_shard_002_of_005.jsonl:line_15` | **Нігті** | biolohiya | 8 | пластинка, фаланга, палець, рука | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 7 | 42 | `eval_shard_002_of_005.jsonl:line_16` | **Право** | pravoznavstvo | 9 | система, норма, припис, підпорядкування | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 8 | 42 | `eval_shard_002_of_005.jsonl:line_14` | **Соціальні норми** | pravoznavstvo | 9 | норма, поведінка, суспільство | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 9 | 42 | `eval_shard_002_of_005.jsonl:line_1` | **Хімічний зв'язок** | khimiya | 8 | взаємодія, атом, стійкість, частинка | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 10 | 42 | `eval_shard_002_of_005.jsonl:line_24` | **Поштовий сервер** | informatyka | 7 | сервер, комп'ютер, пошта, забезпечення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 11 | 42 | `eval_shard_003_of_005.jsonl:line_10` | **Права людини** | pravoznavstvo | 9 | існування, розвиток | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 12 | 42 | `eval_shard_003_of_005.jsonl:line_1` | **Прямокутні координати** | heohrafiya | 8 | координата, система, вісь, меридіан | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 13 | 42 | `eval_shard_003_of_005.jsonl:line_26` | **Антропогенний ландшафт** | heohrafiya | 8 | ландшафт, вплив | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 14 | 42 | `eval_shard_003_of_005.jsonl:line_34` | **Вичерпні природні ресурси** | heohrafiya | 8 | ресурс, зменшення, зникнення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 15 | 42 | `eval_shard_003_of_005.jsonl:line_23` | **Умови укладення шлюбу** | pravoznavstvo | 9 | закон, укладення, шлюб, вимога | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 16 | 42 | `eval_shard_004_of_005.jsonl:line_25` | **Свобода слова** | hromadianska | 8 | право, засіб | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 17 | 42 | `eval_shard_004_of_005.jsonl:line_24` | **Невербальна комунікація** | hromadianska | 8 | комунікація, спілкування, жест, міміка | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 18 | 42 | `eval_shard_004_of_005.jsonl:line_36` | **Памфлет** | zarlit | 8 | обсяг, твір, спрямування | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 19 | 42 | `eval_shard_004_of_005.jsonl:line_23` | **Воєнний стан** | hromadianska | 8 | режим, місцевість, агресія, небезпека | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 20 | 42 | `eval_shard_004_of_005.jsonl:line_16` | **Завойовницька війна** | hromadianska | 8 | війна, розширення, сфера, територія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 21 | 42 | `eval_shard_005_of_005.jsonl:line_40` | **Конфлікт** | etyka | 6 | зіткнення, інтерес, оцінка, цінність | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 22 | 42 | `eval_shard_005_of_005.jsonl:line_31` | **Громадянські обов'язки** | etyka | 6 | обов'язок, норма, держава, ряд | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 23 | 42 | `eval_shard_005_of_005.jsonl:line_30` | **Моральні цінності** | etyka | 6 | цінність, зразок, вимога, дійсність | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 24 | 42 | `eval_shard_005_of_005.jsonl:line_12` | **Реалізм** | mystetstvo | 8 | відтворення, дійсність | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 25 | 42 | `eval_shard_005_of_005.jsonl:line_23` | **Робот** | tekhnolohiyi | 8 | пристрій, комп'ютер, виконання, операція | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 26 | 42 | `sft_shard_054_of_150.jsonl:line_203` | **Троп** | ukrlit | 10 | метафора, характеристика, іронія, гіпербола | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 27 | 42 | `sft_shard_067_of_150.jsonl:line_473` | **Витік перший** | zarlit | 10 | наука, мистецтво, більшість, цінність | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 28 | 42 | `sft_shard_041_of_150.jsonl:line_361` | **Ілюстративний матеріал** | zarlit | 9 | матеріал, кадр, фільм | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 29 | 42 | `sft_shard_089_of_150.jsonl:line_380` | **Проектуюча пряма** | heometriya | 10 | площина, проекція | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 30 | 42 | `sft_shard_099_of_150.jsonl:line_175` | **Фіскальний простір** | ekonomika | 11 | простір, показник, відношення, загроза | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 31 | 42 | `sft_shard_139_of_150.jsonl:line_463` | **План проєкту** | fizyka | 7 | план, проєкт, документ | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 32 | 42 | `sft_shard_030_of_150.jsonl:line_332` | **Викопне паливо** | pryroda | 8 | паливо, ресурс, залишок, тварина | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 33 | 42 | `sft_shard_119_of_150.jsonl:line_312` | **Потерпілий** | pravoznavstvo | 11 | правопорушення, особа | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 34 | 42 | `sft_shard_081_of_150.jsonl:line_319` | **Вулканічні блискавки** | heohrafiya | 6 | атмосфера, літосфера, блискавка, взаємодія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 35 | 42 | `sft_shard_090_of_150.jsonl:line_90` | **Механічна хвиля** | fizyka | 11 | хвиля, поширення, коливання, плин | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 36 | 42 | `sft_shard_015_of_150.jsonl:line_339` | **Судноплавний шлюз** | fizyka | 7 | шлюз, споруда, забезпечення, перехід | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 37 | 42 | `sft_shard_105_of_150.jsonl:line_119` | **Південний океан** | ya_doslidzhuiu_svit | 4 | океан, площа, планета | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 38 | 42 | `sft_shard_039_of_150.jsonl:line_78` | **Фосфорні боєприпаси** | zakhyst | 10 | боєприпас, снаряд, фосфор, температура | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 39 | 42 | `sft_shard_091_of_150.jsonl:line_80` | **Бісектриса кута** | heometriya | 7 | кут, бісектриса | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 40 | 42 | `sft_shard_027_of_150.jsonl:line_382` | **Фільтрування** | informatyka | 10 | відбір, таблиця | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 41 | 42 | `sft_shard_136_of_150.jsonl:line_170` | **Видатки державного бюджету** | pravoznavstvo | 11 | закон, видаток, бюджет, кошт | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 42 | 42 | `sft_shard_042_of_150.jsonl:line_255` | **Мале коло кровообігу** | biolohiya | 7 | орган, кровообіг, рух, кров | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 43 | 42 | `sft_shard_147_of_150.jsonl:line_210` | **Освітлення** | informatyka | 9 | установка, настройка, джерело, сцена | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 44 | 42 | `sft_shard_149_of_150.jsonl:line_314` | **Ренатурація** | biolohiya | 9 | відновлення, структура, макромолекула, денатурація | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 45 | 42 | `sft_shard_003_of_150.jsonl:line_141` | **Авторитарний стиль** | ekonomika | 11 | стиль, поведінка, керівник, вказівка | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 46 | 42 | `sft_shard_023_of_150.jsonl:line_451` | **Повість** | zarlit | 5 | твір, оповідання, обсяг | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 47 | 42 | `sft_shard_079_of_150.jsonl:line_75` | **Підприємництво** | finansova | 9 | навичка, компетенція | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 48 | 42 | `sft_shard_020_of_150.jsonl:line_289` | **Державні символи** | etyka | 5 | символ, закон, держава | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 49 | 42 | `sft_shard_026_of_150.jsonl:line_201` | **Грант** | finansova | 9 | особа, організація, бізнес, реалізація | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 50 | 42 | `sft_shard_029_of_150.jsonl:line_432` | **Дисциплінарне стягнення** | pravoznavstvo | 11 | стягнення, акт, захід, орган | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 51 | 123 | `eval_shard_001_of_005.jsonl:line_39` | **Форма держави** | pravoznavstvo | 9 | держава, організація, структура, орган | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 52 | 123 | `eval_shard_001_of_005.jsonl:line_17` | **Колоніалізм** | vsesvitnia | 8 | підкорення, країна, ресурс, праця | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 53 | 123 | `eval_shard_001_of_005.jsonl:line_32` | **Елементарний заряд** | khimiya | 8 | заряд, електрон, одиниця, вимірювання | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 54 | 123 | `eval_shard_001_of_005.jsonl:line_9` | **Рівні вектори** | heometriya | 9 | вектор, модуль | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 55 | 123 | `eval_shard_001_of_005.jsonl:line_22` | **В'язкість** | fizyka | 8 | рідина, газ, переміщення, речовина | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 56 | 123 | `eval_shard_002_of_005.jsonl:line_26` | **Хмарні сервіси** | informatyka | 7 | сервіс, надання, доступ, інтернет-ресурс | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 57 | 123 | `eval_shard_002_of_005.jsonl:line_32` | **Імітаційна модель** | informatyka | 7 | алгоритм, програма, модель, комплекс | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 58 | 123 | `eval_shard_002_of_005.jsonl:line_23` | **Суб'єкти правовідносин** | pravoznavstvo | 9 | суб'єкт, індивід, організація, особа | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 59 | 123 | `eval_shard_002_of_005.jsonl:line_4` | **Обмежена монархія** | pravoznavstvo | 9 | монархія, правління, монарх, парламент | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 60 | 123 | `eval_shard_002_of_005.jsonl:line_12` | **Демократичний режим** | pravoznavstvo | 9 | режим, організація, принцип, рівноправність | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 61 | 123 | `eval_shard_003_of_005.jsonl:line_28` | **Лаколіт** | heohrafiya | 8 | маса, порода, купол | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 62 | 123 | `eval_shard_003_of_005.jsonl:line_4` | **Юридичні гарантії** | pravoznavstvo | 9 | гарантія, захід, здійснення, охорона | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 63 | 123 | `eval_shard_003_of_005.jsonl:line_19` | **Ґрунтовий профіль** | heohrafiya | 8 | профіль, ґрунт, поверхня, порода | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 64 | 123 | `eval_shard_003_of_005.jsonl:line_15` | **Метеочутливість** | heohrafiya | 8 | організм, зміна | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 65 | 123 | `eval_shard_003_of_005.jsonl:line_38` | **Закінчене кримінальне правопорушення** | pravoznavstvo | 9 | правопорушення, діяння | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 66 | 123 | `eval_shard_004_of_005.jsonl:line_35` | **Опис місцевості** | ukrmova | 8 | опис, місцевість, зображення, місто | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 67 | 123 | `eval_shard_004_of_005.jsonl:line_8` | **Соціалізація** | hromadianska | 8 | засвоєння, індивід, суспільство, учасник | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 68 | 123 | `eval_shard_004_of_005.jsonl:line_4` | **Цінності** | hromadianska | 8 | переконання, суспільство | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 69 | 123 | `eval_shard_004_of_005.jsonl:line_30` | **Олігополія** | ekonomika | 10 | ситуація, фірма | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 70 | 123 | `eval_shard_004_of_005.jsonl:line_17` | **Громадянство** | hromadianska | 8 | особа, держава, вияв, право | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 71 | 123 | `eval_shard_005_of_005.jsonl:line_28` | **Європейський карвінг** | tekhnolohiyi | 8 | карвінг, різьблення, овоч, фрукт | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 72 | 123 | `eval_shard_005_of_005.jsonl:line_22` | **Автоматика** | tekhnolohiyi | 8 | механізм, прилад | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 73 | 123 | `eval_shard_005_of_005.jsonl:line_36` | **Поведінка людини** | etyka | 6 | поведінка, здатність, подразник | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 74 | 123 | `eval_shard_005_of_005.jsonl:line_16` | **Оздоровча система** | zdorovia | 8 | система, знання, навичка, звичка | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 75 | 123 | `eval_shard_005_of_005.jsonl:line_8` | **Офорт** | mystetstvo | 8 | різновид, гравюра, метал, відтиск | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 76 | 123 | `sft_shard_019_of_150.jsonl:line_152` | **Толерантність** | ya_doslidzhuiu_svit | 3 | повага, ставлення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 77 | 123 | `sft_shard_013_of_150.jsonl:line_402` | **Перпендикулярні прямі** | heometriya | 7 | кут, перетин | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 78 | 123 | `sft_shard_103_of_150.jsonl:line_292` | **Масовий відсоток** | algebra | 8 | частка, відсоток, маса, речовина | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 79 | 123 | `sft_shard_106_of_150.jsonl:line_306` | **Критичне мислення** | zdorovia | 6 | мислення, здатність, доцільність, варіант | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 80 | 123 | `sft_shard_014_of_150.jsonl:line_208` | **Органи зору живих істот** | fizyka | 9 | орган, зір, істота | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 81 | 123 | `sft_shard_123_of_150.jsonl:line_277` | **Сахароза** | biolohiya | 9 | дисахарид, залишок, глюкоза, фруктоза | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 82 | 123 | `sft_shard_003_of_150.jsonl:line_223` | **Мода вибірки** | algebra | 8 | мода, вибірка, ряд | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 83 | 123 | `sft_shard_031_of_150.jsonl:line_129` | **Інтернет** | tekhnolohiyi | 6 | бібліотека, книга, підлога | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 84 | 123 | `sft_shard_043_of_150.jsonl:line_172` | **Продуценти** | biolohiya | 11 | організм, сполука, побудова | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 85 | 123 | `sft_shard_036_of_150.jsonl:line_71` | **Реліктове випромінювання** | astronomiya | 11 | випромінювання, квант | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 86 | 123 | `sft_shard_056_of_150.jsonl:line_169` | **Вуглеводи** | khimiya | 10 | сполука, природа | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 87 | 123 | `sft_shard_006_of_150.jsonl:line_82` | **Динамічне програмування** | informatyka | 11 | програмування, пошук, вирішення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 88 | 123 | `sft_shard_115_of_150.jsonl:line_434` | **Органи** | pryroda | 6 | тіло, розташування, організм, функція | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 89 | 123 | `sft_shard_137_of_150.jsonl:line_130` | **Трансплантація** | biolohiya | 10 | орган, тканина, пересадка, реципієнт | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 90 | 123 | `sft_shard_057_of_150.jsonl:line_288` | **Зоря** | astronomiya | 11 | тяжіння, енергія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 91 | 123 | `sft_shard_010_of_150.jsonl:line_350` | **Територіальна громада** | hromadianska | 9 | громада, село, місто, пункт | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 92 | 123 | `sft_shard_015_of_150.jsonl:line_496` | **Міцелій** | biolohiya | 10 | структура, відросток, гіф | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 93 | 123 | `sft_shard_121_of_150.jsonl:line_332` | **Система колективної безпеки** | vsesvitnia | 10 | система, безпека, здійснення, захист | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 94 | 123 | `sft_shard_066_of_150.jsonl:line_332` | **Сфера** | matematyka | 11 | тіло, відстань | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 95 | 123 | `sft_shard_128_of_150.jsonl:line_58` | **Народження проєкту** | tekhnolohiyi | 9 | народження, проєкт, визначення, проблема | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 96 | 123 | `sft_shard_011_of_150.jsonl:line_104` | **Моделювання** | informatyka | 9 | побудова, модель, сцена, об'єкт | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 97 | 123 | `sft_shard_032_of_150.jsonl:line_49` | **Раціональне рівняння** | algebra | 8 | рівняння, вираз | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 98 | 123 | `sft_shard_026_of_150.jsonl:line_8` | **Погон** | zakhyst | 10 | елемент, одяг, розрізнення, звання | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 99 | 123 | `sft_shard_027_of_150.jsonl:line_179` | **Дріжджі** | ya_doslidzhuiu_svit | 3 | гриб, вуглевод | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 100 | 123 | `sft_shard_040_of_150.jsonl:line_33` | **Подвійні зорі** | astronomiya | 11 | система, зір, орбіта, центр | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 101 | 777 | `eval_shard_001_of_005.jsonl:line_6` | **Ренесанс** | istoriya | 8 | стиль, мистецтво | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 102 | 777 | `eval_shard_001_of_005.jsonl:line_8` | **Козацька рада** | istoriya | 8 | назва, зібрання, вирішення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 103 | 777 | `eval_shard_001_of_005.jsonl:line_19` | **Енциклопедія** | vsesvitnia | 8 | довідник, відомість, галузь, знання | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 104 | 777 | `eval_shard_001_of_005.jsonl:line_27` | **Електричне поле** | fizyka | 8 | матерія, тіло, частинка, заряд | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 105 | 777 | `eval_shard_001_of_005.jsonl:line_7` | **Пропускна здатність водопровідної труби** | heometriya | 9 | здатність, маса, переріз, одиниця | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 106 | 777 | `eval_shard_002_of_005.jsonl:line_34` | **Юридична відповідальність** | pravoznavstvo | 9 | правопорушення, відповідальність, застосування, особа | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 107 | 777 | `eval_shard_002_of_005.jsonl:line_8` | **Форма державного устрою** | pravoznavstvo | 9 | устрій, елемент, держава, структура | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 108 | 777 | `eval_shard_002_of_005.jsonl:line_27` | **Правопорушення** | pravoznavstvo | 9 | дія, бездіяльність, норма, відповідальність | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 109 | 777 | `eval_shard_002_of_005.jsonl:line_5` | **Орган** | biolohiya | 8 | тканина, складник, організм, функція | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 110 | 777 | `eval_shard_002_of_005.jsonl:line_31` | **Протиправне діяння** | pravoznavstvo | 9 | діяння, акт, поведінка, дія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 111 | 777 | `eval_shard_003_of_005.jsonl:line_13` | **Вегетаційний період** | heohrafiya | 8 | період, рослина | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 112 | 777 | `eval_shard_003_of_005.jsonl:line_30` | **Природні умови** | heohrafiya | 8 | природа, участь | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 113 | 777 | `eval_shard_003_of_005.jsonl:line_14` | **Слідчий** | pravoznavstvo | 9 | особа, орган, розслідування | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 114 | 777 | `eval_shard_003_of_005.jsonl:line_6` | **Надзвичайний стан** | pravoznavstvo | 9 | режим, район, виникнення, ситуація | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 115 | 777 | `eval_shard_003_of_005.jsonl:line_36` | **Кримінальне право** | pravoznavstvo | 9 | правопорушення, право, система, норма | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 116 | 777 | `eval_shard_004_of_005.jsonl:line_22` | **Правова держава** | hromadianska | 8 | держава, верховенство | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 117 | 777 | `eval_shard_004_of_005.jsonl:line_28` | **Обмін** | ekonomika | 10 | рух, товар, власник | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 118 | 777 | `eval_shard_004_of_005.jsonl:line_12` | **Громадянський обов'язок** | hromadianska | 8 | обов'язок, громадянин, країна, закон | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 119 | 777 | `eval_shard_004_of_005.jsonl:line_1` | **Кримінальна відповідальність** | pravoznavstvo | 9 | відповідальність, покарання, держава, особа | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 120 | 777 | `eval_shard_004_of_005.jsonl:line_38` | **Місцевий колорит** | zarlit | 8 | колорит, твір, елемент, побут | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 121 | 777 | `eval_shard_005_of_005.jsonl:line_13` | **Соціальна відповідальність бізнесу** | zdorovia | 8 | відповідальність, бізнес, практика, участь | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 122 | 777 | `eval_shard_005_of_005.jsonl:line_41` | **Милостиня** | etyka | 6 | виявлення, турбота | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 123 | 777 | `eval_shard_005_of_005.jsonl:line_38` | **Взаємоповага** | etyka | 6 | повага, виявлення, почуття, взаємність | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 124 | 777 | `eval_shard_005_of_005.jsonl:line_15` | **Лікувальне дієтичне харчування** | zdorovia | 8 | харчування, лікування, хвороба | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 125 | 777 | `eval_shard_005_of_005.jsonl:line_2` | **Етнічна музика** | mystetstvo | 8 | витік, фольклор, етнос | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 126 | 777 | `sft_shard_101_of_150.jsonl:line_3` | **Шлях** | fizyka | 7 | довжина, траєкторія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 127 | 777 | `sft_shard_109_of_150.jsonl:line_373` | **Монетарна політика** | ekonomika | 11 | інфляція, політика, комплекс, захід | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 128 | 777 | `sft_shard_070_of_150.jsonl:line_284` | **Електронне урядування** | informatyka | 10 | урядування, організація, управління, підвищення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 129 | 777 | `sft_shard_118_of_150.jsonl:line_128` | **Інфекційні захворювання** | zdorovia | 5 | захворювання, хвороба, здатність | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 130 | 777 | `sft_shard_014_of_150.jsonl:line_258` | **Лінія прицілювання** | zakhyst | 10 | прицілювання, око, проріз, приціл | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 131 | 777 | `sft_shard_119_of_150.jsonl:line_349` | **Змінні зорі** | astronomiya | 11 | блиск, поверхня, дія, причина | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 132 | 777 | `sft_shard_142_of_150.jsonl:line_383` | **Фізика** | fizyka | 7 | наука, закономірність, природа, матерія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 133 | 777 | `sft_shard_011_of_150.jsonl:line_455` | **Благодійність** | hromadianska | 9 | намір, передача, навичка, енергія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 134 | 777 | `sft_shard_079_of_150.jsonl:line_125` | **Статут підприємства** | ekonomika | 11 | статут, підприємство, зібрання, суб'єкт | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 135 | 777 | `sft_shard_026_of_150.jsonl:line_117` | **Абсолютний показник заломлення** | fizyka | 9 | заломлення, показник, вакуум | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 136 | 777 | `sft_shard_084_of_150.jsonl:line_425` | **Русинство** | istoriya | 10 | течія, визнання, населення, нація | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 137 | 777 | `sft_shard_034_of_150.jsonl:line_476` | **Інформаційна революція** | vsesvitnia | 10 | революція, зміна, формування, суспільство | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 138 | 777 | `sft_shard_126_of_150.jsonl:line_397` | **Міжнародна торгівля** | ekonomika | 11 | торгівля, переміщення, товар, послуга | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 139 | 777 | `sft_shard_036_of_150.jsonl:line_267` | **Терплячість** | etyka | 5 | здатність, витримка, подолання | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 140 | 777 | `sft_shard_028_of_150.jsonl:line_67` | **Ліричні твори** | ukrlit | 5 | почуття, переживання, обставина, вплив | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 141 | 777 | `sft_shard_150_of_150.jsonl:line_195` | **Друкований текст** | zarlit | 5 | засіб, друк, папір | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 142 | 777 | `sft_shard_057_of_150.jsonl:line_92` | **Колообіг води** | ya_doslidzhuiu_svit | 3 | природа, колообіг, перетворення, переміщення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 143 | 777 | `sft_shard_135_of_150.jsonl:line_125` | **Викрадення українських дітей** | vsesvitnia | 11 | травень, викрадення, дитина, геноцид | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 144 | 777 | `sft_shard_083_of_150.jsonl:line_313` | **Композиторський стиль** | mystetstvo | 10 | стиль, творчість, композитор, період | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 145 | 777 | `sft_shard_094_of_150.jsonl:line_440` | **Провідні мотиви** | ukrlit | 11 | мотив, переосмислення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 146 | 777 | `sft_shard_133_of_150.jsonl:line_453` | **Кремній** | heohrafiya | 9 | матеріал, електроніка | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 147 | 777 | `sft_shard_015_of_150.jsonl:line_421` | **Археї** | biolohiya | 7 | учасник, кругообіг, речовина | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 148 | 777 | `sft_shard_039_of_150.jsonl:line_298` | **Рівні фігури** | heometriya | 9 | фігура, переміщення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 149 | 777 | `sft_shard_032_of_150.jsonl:line_103` | **Господарський договір** | pravoznavstvo | 11 | договір, угода, суб'єкт, контрагент | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 150 | 777 | `sft_shard_093_of_150.jsonl:line_279` | **Депресія** | ekonomika | 11 | виробництво, фаза, цикл, застій | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |

## Detailed Record Inspection (Full Text)

### Record 1 (Seed 42): Плавлення (eval_shard_001_of_005.jsonl:line_24)
- **Subject / Grade:** fizyka (Grade 8)
- **Concept:** `Плавлення` (Citation form: ✅)
- **Scientific Terminology:** `['перехід', 'речовина']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Плавлення — це процес переходу речовини з твердого стану в рідкий.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 2 (Seed 42): Ізотопи (eval_shard_001_of_005.jsonl:line_34)
- **Subject / Grade:** khimiya (Grade 8)
- **Concept:** `Ізотопи` (Citation form: ✅)
- **Scientific Terminology:** `['нуклід', 'елемент']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Ізотопи — це різні нукліди одного хімічного елемента.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 3 (Seed 42): Панщина (eval_shard_001_of_005.jsonl:line_4)
- **Subject / Grade:** istoriya (Grade 8)
- **Concept:** `Панщина` (Citation form: ✅)
- **Scientific Terminology:** `['виконання', 'селянин', 'обсяг', 'господарство', 'землевласник']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Панщина — виконання селянами певного обсягу робіт у господарстві землевласника за користування його землею.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 4 (Seed 42): Революція (eval_shard_001_of_005.jsonl:line_12)
- **Subject / Grade:** vsesvitnia (Grade 8)
- **Concept:** `Революція` (Citation form: ✅)
- **Scientific Terminology:** `['переворот', 'суспільство', 'зміна', 'перетворення', 'удосконалення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Революція – докорінний переворот у житті суспільства, який супроводжується зміною влади; різкі зміни в якій-небудь галузі, що приводить до істотних перетворень, удосконалення чого-небудь.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 5 (Seed 42): Протилежні вектори (eval_shard_001_of_005.jsonl:line_11)
- **Subject / Grade:** heometriya (Grade 9)
- **Concept:** `Протилежні вектори` (Citation form: ✅)
- **Scientific Terminology:** `['вектор', 'модуль']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Два ненульових вектори називають протилежними, якщо їхні модулі рівні й вектори протилежно напрямлені.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 6 (Seed 42): Нігті (eval_shard_002_of_005.jsonl:line_15)
- **Subject / Grade:** biolohiya (Grade 8)
- **Concept:** `Нігті` (Citation form: ✅)
- **Scientific Terminology:** `['пластинка', 'фаланга', 'палець', 'рука', 'нога']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Нігті — це тонкі, опуклі зроговілі пластинки на кінцях фаланг пальців рук і ніг.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 7 (Seed 42): Право (eval_shard_002_of_005.jsonl:line_16)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Право` (Citation form: ✅)
- **Scientific Terminology:** `['система', 'норма', 'припис', 'підпорядкування']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Право є системою норм, тобто всі правові приписи взаємодіють між собою та мають чітке підпорядкування.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 8 (Seed 42): Соціальні норми (eval_shard_002_of_005.jsonl:line_14)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Соціальні норми` (Citation form: ✅)
- **Scientific Terminology:** `['норма', 'поведінка', 'суспільство']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Соціальні норми — загальні правила поведінки, що регулюють відносини між людьми в суспільстві.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 9 (Seed 42): Хімічний зв'язок (eval_shard_002_of_005.jsonl:line_1)
- **Subject / Grade:** khimiya (Grade 8)
- **Concept:** `Хімічний зв'язок` (Citation form: ✅)
- **Scientific Terminology:** `['взаємодія', 'атом', 'стійкість', 'частинка', 'молекула']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Хімічний зв'язок — це взаємодія атомів, що зумовлює стійкість багатоатомних частинок (молекул, йонів, кристалів).» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 10 (Seed 42): Поштовий сервер (eval_shard_002_of_005.jsonl:line_24)
- **Subject / Grade:** informatyka (Grade 7)
- **Concept:** `Поштовий сервер` (Citation form: ✅)
- **Scientific Terminology:** `['сервер', "комп'ютер", 'пошта', 'забезпечення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Поштовий сервер — це комп'ютер, який забезпечує роботу електронної пошти завдяки встановленому на ньому спеціальному програмному забезпеченню.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 11 (Seed 42): Права людини (eval_shard_003_of_005.jsonl:line_10)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Права людини` (Citation form: ✅)
- **Scientific Terminology:** `['існування', 'розвиток']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Права людини — можливості, необхідні людині для існування та розвитку.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 12 (Seed 42): Прямокутні координати (eval_shard_003_of_005.jsonl:line_1)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Прямокутні координати` (Citation form: ✅)
- **Scientific Terminology:** `['координата', 'система', 'вісь', 'меридіан', 'зона']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Прямокутні координати – це система координат, у якій за вісь X прийнято центральний меридіан 6-градусної зони, а за вісь Y – екватор.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 13 (Seed 42): Антропогенний ландшафт (eval_shard_003_of_005.jsonl:line_26)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Антропогенний ландшафт` (Citation form: ✅)
- **Scientific Terminology:** `['ландшафт', 'вплив']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Антропогенний ландшафт – це тип ПТК, який сформувався під впливом діяльності людини.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 14 (Seed 42): Вичерпні природні ресурси (eval_shard_003_of_005.jsonl:line_34)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Вичерпні природні ресурси` (Citation form: ✅)
- **Scientific Terminology:** `['ресурс', 'зменшення', 'зникнення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Вичерпні природні ресурси – це ресурси, використання яких призводить до їх зменшення або повного зникнення.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 15 (Seed 42): Умови укладення шлюбу (eval_shard_003_of_005.jsonl:line_23)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Умови укладення шлюбу` (Citation form: ✅)
- **Scientific Terminology:** `['закон', 'укладення', 'шлюб', 'вимога', 'особа']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Умови укладення шлюбу — передбачені законом вимоги до осіб, які забезпечують дійсність їхнього шлюбу.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 16 (Seed 42): Свобода слова (eval_shard_004_of_005.jsonl:line_25)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Свобода слова` (Citation form: ✅)
- **Scientific Terminology:** `['право', 'засіб']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Свобода слова – це право людини висловлювати свої погляди в усній і письмовій формах, зокрема через засоби масової інформації.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 17 (Seed 42): Невербальна комунікація (eval_shard_004_of_005.jsonl:line_24)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Невербальна комунікація` (Citation form: ✅)
- **Scientific Terminology:** `['комунікація', 'спілкування', 'жест', 'міміка', 'рух']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Невербальна комунікація – спілкування за допомогою жестів, міміки, рухів тіла й деяких інших засобів, за винятком мовних.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 18 (Seed 42): Памфлет (eval_shard_004_of_005.jsonl:line_36)
- **Subject / Grade:** zarlit (Grade 8)
- **Concept:** `Памфлет` (Citation form: ✅)
- **Scientific Terminology:** `['обсяг', 'твір', 'спрямування']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Памфлет – невеликий за обсягом художньо-публіцистичний твір політичного спрямування, який різко викриває негативні явища суспільного життя.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 19 (Seed 42): Воєнний стан (eval_shard_004_of_005.jsonl:line_23)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Воєнний стан` (Citation form: ✅)
- **Scientific Terminology:** `['режим', 'місцевість', 'агресія', 'небезпека', 'незалежність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Воєнний стан – це особливий правовий режим, що вводиться в Україні або в окремих її місцевостях у разі збройної агресії чи загрози нападу, небезпеки державній незалежності України, її територіальній цілісності.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 20 (Seed 42): Завойовницька війна (eval_shard_004_of_005.jsonl:line_16)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Завойовницька війна` (Citation form: ✅)
- **Scientific Terminology:** `['війна', 'розширення', 'сфера', 'територія', 'держава']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Завойовницька війна – війна, що ведеться для розширення власної сфери впливу на території іншої держави.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 21 (Seed 42): Конфлікт (eval_shard_005_of_005.jsonl:line_40)
- **Subject / Grade:** etyka (Grade 6)
- **Concept:** `Конфлікт` (Citation form: ✅)
- **Scientific Terminology:** `['зіткнення', 'інтерес', 'оцінка', 'цінність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Конфлікт — зіткнення протилежних інтересів, поглядів, оцінок, цінностей.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 22 (Seed 42): Громадянські обов'язки (eval_shard_005_of_005.jsonl:line_31)
- **Subject / Grade:** etyka (Grade 6)
- **Concept:** `Громадянські обов'язки` (Citation form: ✅)
- **Scientific Terminology:** `["обов'язок", 'норма', 'держава', 'ряд', 'громадянин']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Громадянські обов'язки — закріплений правовими нормами держави ряд дій, які громадяни мають безумовно виконувати.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 23 (Seed 42): Моральні цінності (eval_shard_005_of_005.jsonl:line_30)
- **Subject / Grade:** etyka (Grade 6)
- **Concept:** `Моральні цінності` (Citation form: ✅)
- **Scientific Terminology:** `['цінність', 'зразок', 'вимога', 'дійсність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Моральні цінності — моральні зразки та вимоги, що допомагають людині орієнтуватися в навколишній дійсності.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 24 (Seed 42): Реалізм (eval_shard_005_of_005.jsonl:line_12)
- **Subject / Grade:** mystetstvo (Grade 8)
- **Concept:** `Реалізм` (Citation form: ✅)
- **Scientific Terminology:** `['відтворення', 'дійсність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Реалізм — художній метод, який базується на достовірному відтворенні дійсності.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 25 (Seed 42): Робот (eval_shard_005_of_005.jsonl:line_23)
- **Subject / Grade:** tekhnolohiyi (Grade 8)
- **Concept:** `Робот` (Citation form: ✅)
- **Scientific Terminology:** `['пристрій', "комп'ютер", 'виконання', 'операція']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Робот — пристрій, який керований за допомогою електронної плати або комп'ютера і який можна запрограмувати на виконання певних операцій.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 26 (Seed 42): Троп (sft_shard_054_of_150.jsonl:line_203)
- **Subject / Grade:** ukrlit (Grade 10)
- **Concept:** `Троп` (Citation form: ✅)
- **Scientific Terminology:** `['метафора', 'характеристика', 'іронія', 'гіпербола', 'епітет']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Троп — слово, ужите в переносному значенні для характеристики певного явища; до тропів належать метафора, іронія, гіпербола, епітет, порівняння та ін.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 27 (Seed 42): Витік перший (sft_shard_067_of_150.jsonl:line_473)
- **Subject / Grade:** zarlit (Grade 10)
- **Concept:** `Витік перший` (Citation form: ✅)
- **Scientific Terminology:** `['наука', 'мистецтво', 'більшість', 'цінність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Витік перший – антична культура, яка подарувала нам основи наук і мистецтв, більшість загальновизнаних цінностей і цілей.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 28 (Seed 42): Ілюстративний матеріал (sft_shard_041_of_150.jsonl:line_361)
- **Subject / Grade:** zarlit (Grade 9)
- **Concept:** `Ілюстративний матеріал` (Citation form: ✅)
- **Scientific Terminology:** `['матеріал', 'кадр', 'фільм']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Ілюстративний матеріал – кадри з фільму „Пігмаліон“.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 29 (Seed 42): Проектуюча пряма (sft_shard_089_of_150.jsonl:line_380)
- **Subject / Grade:** heometriya (Grade 10)
- **Concept:** `Проектуюча пряма` (Citation form: ✅)
- **Scientific Terminology:** `['площина', 'проекція']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Пряму І називають проектуючою прямою, а площину а - площиною проекції.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 30 (Seed 42): Фіскальний простір (sft_shard_099_of_150.jsonl:line_175)
- **Subject / Grade:** ekonomika (Grade 11)
- **Concept:** `Фіскальний простір` (Citation form: ✅)
- **Scientific Terminology:** `['простір', 'показник', 'відношення', 'загроза', 'дефолт']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Фіскальний простір — відстань від показника відношення боргу до ВВП до „верхньої межі“, вище якої не виникає загроза дефолту.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 31 (Seed 42): План проєкту (sft_shard_139_of_150.jsonl:line_463)
- **Subject / Grade:** fizyka (Grade 7)
- **Concept:** `План проєкту` (Citation form: ✅)
- **Scientific Terminology:** `['план', 'проєкт', 'документ']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «План проєкту — це документ, який містить заздалегідь намічений порядок дій, необхідних для досягнення мети проєкту.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 32 (Seed 42): Викопне паливо (sft_shard_030_of_150.jsonl:line_332)
- **Subject / Grade:** pryroda (Grade 8)
- **Concept:** `Викопне паливо` (Citation form: ✅)
- **Scientific Terminology:** `['паливо', 'ресурс', 'залишок', 'тварина', 'рослина']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Викопне паливо — це невідновлювані ресурси, яке утворилося, на думку вчених, із залишків мертвих тварин, рослин.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 33 (Seed 42): Потерпілий (sft_shard_119_of_150.jsonl:line_312)
- **Subject / Grade:** pravoznavstvo (Grade 11)
- **Concept:** `Потерпілий` (Citation form: ✅)
- **Scientific Terminology:** `['правопорушення', 'особа']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Потерпілий — фізична особа, якій кримінальним правопорушенням завдано моральної, фізичної або майнової шкоди, а також юридична особа, якій кримінальним правопорушенням завдано майнової шкоди.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 34 (Seed 42): Вулканічні блискавки (sft_shard_081_of_150.jsonl:line_319)
- **Subject / Grade:** heohrafiya (Grade 6)
- **Concept:** `Вулканічні блискавки` (Citation form: ✅)
- **Scientific Terminology:** `['атмосфера', 'літосфера', 'блискавка', 'взаємодія']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Вулканічні блискавки є яскравим прикладом взаємодії літосфери й атмосфери.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 35 (Seed 42): Механічна хвиля (sft_shard_090_of_150.jsonl:line_90)
- **Subject / Grade:** fizyka (Grade 11)
- **Concept:** `Механічна хвиля` (Citation form: ✅)
- **Scientific Terminology:** `['хвиля', 'поширення', 'коливання', 'плин']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Механічна хвиля — процес поширення коливань у пружному середовищі з плином часу.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 36 (Seed 42): Судноплавний шлюз (sft_shard_015_of_150.jsonl:line_339)
- **Subject / Grade:** fizyka (Grade 7)
- **Concept:** `Судноплавний шлюз` (Citation form: ✅)
- **Scientific Terminology:** `['шлюз', 'споруда', 'забезпечення', 'перехід', 'водойма']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Судноплавний шлюз — гідротехнічна споруда для забезпечення переходу судна на плаву з однієї водойми в іншу з різними рівнями води.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 37 (Seed 42): Південний океан (sft_shard_105_of_150.jsonl:line_119)
- **Subject / Grade:** ya_doslidzhuiu_svit (Grade 4)
- **Concept:** `Південний океан` (Citation form: ✅)
- **Scientific Terminology:** `['океан', 'площа', 'планета']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Південний океан — четвертий за площею океан планети.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 38 (Seed 42): Фосфорні боєприпаси (sft_shard_039_of_150.jsonl:line_78)
- **Subject / Grade:** zakhyst (Grade 10)
- **Concept:** `Фосфорні боєприпаси` (Citation form: ✅)
- **Scientific Terminology:** `['боєприпас', 'снаряд', 'фосфор', 'температура', 'горіння']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Фосфорні боєприпаси — це снаряди начинені самозапальним білим фосфором, що має високу температуру горіння (від 800°C). 24 березня 2022 року повідомлялося, що російські війська скинули кілька фосфорних бомб в Луганській області.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 39 (Seed 42): Бісектриса кута (sft_shard_091_of_150.jsonl:line_80)
- **Subject / Grade:** heometriya (Grade 7)
- **Concept:** `Бісектриса кута` (Citation form: ✅)
- **Scientific Terminology:** `['кут', 'бісектриса']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Бісектрисою кута називають промінь з початком у вершині кута, який ділить цей кут на два рівних кути.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 40 (Seed 42): Фільтрування (sft_shard_027_of_150.jsonl:line_382)
- **Subject / Grade:** informatyka (Grade 10)
- **Concept:** `Фільтрування` (Citation form: ✅)
- **Scientific Terminology:** `['відбір', 'таблиця']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Фільтрування — це відбір із таблиці записів, які містять задане значення в обраних полях.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 41 (Seed 42): Видатки державного бюджету (sft_shard_136_of_150.jsonl:line_170)
- **Subject / Grade:** pravoznavstvo (Grade 11)
- **Concept:** `Видатки державного бюджету` (Citation form: ✅)
- **Scientific Terminology:** `['закон', 'видаток', 'бюджет', 'кошт', 'здійснення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Видатки державного бюджету — це кошти, які спрямовують на здійснення програм і заходів, що передбачені законом про бюджет на поточний рік.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 42 (Seed 42): Мале коло кровообігу (sft_shard_042_of_150.jsonl:line_255)
- **Subject / Grade:** biolohiya (Grade 7)
- **Concept:** `Мале коло кровообігу` (Citation form: ✅)
- **Scientific Terminology:** `['орган', 'кровообіг', 'рух', 'кров', 'легінь']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Мале коло кровообігу – це рух крові через легені, де вона насичується киснем і перетворюється в артеріальну, а велике коло кровообігу – це рух артеріальної крові через органи, де перетворюється у венозну, насичену вуглекислим газом.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 43 (Seed 42): Освітлення (sft_shard_147_of_150.jsonl:line_210)
- **Subject / Grade:** informatyka (Grade 9)
- **Concept:** `Освітлення` (Citation form: ✅)
- **Scientific Terminology:** `['установка', 'настройка', 'джерело', 'сцена']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Освітлення — створення, установка напрямків й настройка джерел освітлення на створеній сцені.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 44 (Seed 42): Ренатурація (sft_shard_149_of_150.jsonl:line_314)
- **Subject / Grade:** biolohiya (Grade 9)
- **Concept:** `Ренатурація` (Citation form: ✅)
- **Scientific Terminology:** `['відновлення', 'структура', 'макромолекула', 'денатурація']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Ренатурація — відновлення просторової структури макромолекул після денатурації.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 45 (Seed 42): Авторитарний стиль (sft_shard_003_of_150.jsonl:line_141)
- **Subject / Grade:** ekonomika (Grade 11)
- **Concept:** `Авторитарний стиль` (Citation form: ✅)
- **Scientific Terminology:** `['стиль', 'поведінка', 'керівник', 'вказівка', 'ініціатива']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Авторитарний стиль — це поведінка керівника, який схильний давати чіткі вказівки, домагатися певної ініціативи від персоналу та постійно контролювати дії підлеглих.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 46 (Seed 42): Повість (sft_shard_023_of_150.jsonl:line_451)
- **Subject / Grade:** zarlit (Grade 5)
- **Concept:** `Повість` (Citation form: ✅)
- **Scientific Terminology:** `['твір', 'оповідання', 'обсяг']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Повість – прозовий твір, який має більший, ніж оповідання, обсяг.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 47 (Seed 42): Підприємництво (sft_shard_079_of_150.jsonl:line_75)
- **Subject / Grade:** finansova (Grade 9)
- **Concept:** `Підприємництво` (Citation form: ✅)
- **Scientific Terminology:** `['навичка', 'компетенція']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Підприємництво — складна та багатогранна діяльність, яка потребує різноманітних навичок і компетенцій.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 48 (Seed 42): Державні символи (sft_shard_020_of_150.jsonl:line_289)
- **Subject / Grade:** etyka (Grade 5)
- **Concept:** `Державні символи` (Citation form: ✅)
- **Scientific Terminology:** `['символ', 'закон', 'держава']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Державні символи — закріплені в законах знаки держави.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 49 (Seed 42): Грант (sft_shard_026_of_150.jsonl:line_201)
- **Subject / Grade:** finansova (Grade 9)
- **Concept:** `Грант` (Citation form: ✅)
- **Scientific Terminology:** `['особа', 'організація', 'бізнес', 'реалізація', 'проєкт']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Грант — це гроші, які надають фізичним особам, організаціям чи бізнесам для реалізації певного проєкту, і їх не потрібно повертати.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 50 (Seed 42): Дисциплінарне стягнення (sft_shard_029_of_150.jsonl:line_432)
- **Subject / Grade:** pravoznavstvo (Grade 11)
- **Concept:** `Дисциплінарне стягнення` (Citation form: ✅)
- **Scientific Terminology:** `['стягнення', 'акт', 'захід', 'орган', 'право']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Дисциплінарне стягнення — передбачений у нормативно-правовому акті захід примусового впливу, що застосовується органом, якому надано право прийняття на роботу працівника відповідно до його компетенції, за скоєний дисциплінарний проступок.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 51 (Seed 123): Форма держави (eval_shard_001_of_005.jsonl:line_39)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Форма держави` (Citation form: ✅)
- **Scientific Terminology:** `['держава', 'організація', 'структура', 'орган', 'здійснення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Форма держави — спосіб організації структури держави та її органів, а також спосіб здійснення державної влади, що виражається у формі правління, формі державного устрою і політичному режимі.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 52 (Seed 123): Колоніалізм (eval_shard_001_of_005.jsonl:line_17)
- **Subject / Grade:** vsesvitnia (Grade 8)
- **Concept:** `Колоніалізм` (Citation form: ✅)
- **Scientific Terminology:** `['підкорення', 'країна', 'ресурс', 'праця', 'населення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Колоніалізм – підкорення однією країною іншої з метою використання її ресурсів, праці місцевого населення та його культурної асиміляції, а також політичного контролю.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 53 (Seed 123): Елементарний заряд (eval_shard_001_of_005.jsonl:line_32)
- **Subject / Grade:** khimiya (Grade 8)
- **Concept:** `Елементарний заряд` (Citation form: ✅)
- **Scientific Terminology:** `['заряд', 'електрон', 'одиниця', 'вимірювання']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Електричний заряд електрона називають елементарним, оскільки він найменший із-поміж усіх відомих зарядів і тому його абсолютну величину приймають за одиницю вимірювання заряду.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 54 (Seed 123): Рівні вектори (eval_shard_001_of_005.jsonl:line_9)
- **Subject / Grade:** heometriya (Grade 9)
- **Concept:** `Рівні вектори` (Citation form: ✅)
- **Scientific Terminology:** `['вектор', 'модуль']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Ненульові вектори називають рівними, якщо їхні модулі рівні й вони співнапрямлені.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 55 (Seed 123): В'язкість (eval_shard_001_of_005.jsonl:line_22)
- **Subject / Grade:** fizyka (Grade 8)
- **Concept:** `В'язкість` (Citation form: ✅)
- **Scientific Terminology:** `['рідина', 'газ', 'переміщення', 'речовина']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «В'язкість — це властивість рідин і газів протидіяти переміщенню одних шарів речовини відносно інших.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 56 (Seed 123): Хмарні сервіси (eval_shard_002_of_005.jsonl:line_26)
- **Subject / Grade:** informatyka (Grade 7)
- **Concept:** `Хмарні сервіси` (Citation form: ✅)
- **Scientific Terminology:** `['сервіс', 'надання', 'доступ', 'інтернет-ресурс', 'сервер']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Хмарні сервіси — сервіси, пов'язані з наданням постійного доступу до віддалених інтернет-ресурсів (серверів, сховищ).» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 57 (Seed 123): Імітаційна модель (eval_shard_002_of_005.jsonl:line_32)
- **Subject / Grade:** informatyka (Grade 7)
- **Concept:** `Імітаційна модель` (Citation form: ✅)
- **Scientific Terminology:** `['алгоритм', 'програма', 'модель', 'комплекс', 'функціонування']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Імітаційна модель — це програма або комплекс програм, що реалізує алгоритм функціонування об'єкта за різних умов.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 58 (Seed 123): Суб'єкти правовідносин (eval_shard_002_of_005.jsonl:line_23)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Суб'єкти правовідносин` (Citation form: ✅)
- **Scientific Terminology:** `["суб'єкт", 'індивід', 'організація', 'особа', 'спільнота']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Суб'єкти правовідносин — окремі індивіди, організації (юридичні особи), певна соціальна спільнота або держава загалом, які відповідно до норм права є носіями суб'єктивних юридичних прав і обов'язків.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 59 (Seed 123): Обмежена монархія (eval_shard_002_of_005.jsonl:line_4)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Обмежена монархія` (Citation form: ✅)
- **Scientific Terminology:** `['монархія', 'правління', 'монарх', 'парламент', 'конституція']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Обмежена монархія — форма державного правління, за якої владу монарха обмежує парламент або конституція.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 60 (Seed 123): Демократичний режим (eval_shard_002_of_005.jsonl:line_12)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Демократичний режим` (Citation form: ✅)
- **Scientific Terminology:** `['режим', 'організація', 'принцип', 'рівноправність', 'виборність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Демократичний режим — форма організації суспільно-політичного життя, заснованого на принципах рівноправності його членів, періодичної виборності органів державного управління і прийняття рішень згідно з волею більшості.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 61 (Seed 123): Лаколіт (eval_shard_003_of_005.jsonl:line_28)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Лаколіт` (Citation form: ✅)
- **Scientific Terminology:** `['маса', 'порода', 'купол']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Лаколіт – закам'яніла маса магматичних гірських порід, що застигла у надрах у вигляді купола.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 62 (Seed 123): Юридичні гарантії (eval_shard_003_of_005.jsonl:line_4)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Юридичні гарантії` (Citation form: ✅)
- **Scientific Terminology:** `['гарантія', 'захід', 'здійснення', 'охорона', 'свобода']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Юридичні гарантії — державно-правові заходи, що забезпечують здійснення та охорону права, свобод і обов'язків людини й громадянина.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 63 (Seed 123): Ґрунтовий профіль (eval_shard_003_of_005.jsonl:line_19)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Ґрунтовий профіль` (Citation form: ✅)
- **Scientific Terminology:** `['профіль', 'ґрунт', 'поверхня', 'порода']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Ґрунтовий профіль – вертикальна будова ґрунту від поверхні до материнської породи.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 64 (Seed 123): Метеочутливість (eval_shard_003_of_005.jsonl:line_15)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Метеочутливість` (Citation form: ✅)
- **Scientific Terminology:** `['організм', 'зміна']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Метеочутливість – це особливість організму людини, коли вона недостатньо добре може адаптуватися до погодних змін.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 65 (Seed 123): Закінчене кримінальне правопорушення (eval_shard_003_of_005.jsonl:line_38)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Закінчене кримінальне правопорушення` (Citation form: ✅)
- **Scientific Terminology:** `['правопорушення', 'діяння']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Закінчене кримінальне правопорушення — діяння, яке містить усі ознаки складу кримінального правопорушення.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 66 (Seed 123): Опис місцевості (eval_shard_004_of_005.jsonl:line_35)
- **Subject / Grade:** ukrmova (Grade 8)
- **Concept:** `Опис місцевості` (Citation form: ✅)
- **Scientific Terminology:** `['опис', 'місцевість', 'зображення', 'місто', 'село']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Опис місцевості – це словесне зображення основних ознак міста, села, вулиці, подвір'я, острова тощо.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 67 (Seed 123): Соціалізація (eval_shard_004_of_005.jsonl:line_8)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Соціалізація` (Citation form: ✅)
- **Scientific Terminology:** `['засвоєння', 'індивід', 'суспільство', 'учасник']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Соціалізація – це процес засвоєння індивідом культури суспільства, завдяки чому він стає дієздатним учасником соціальних зв'язків.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 68 (Seed 123): Цінності (eval_shard_004_of_005.jsonl:line_4)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Цінності` (Citation form: ✅)
- **Scientific Terminology:** `['переконання', 'суспільство']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Цінності – це загальновизнані переконання щодо цілей, до яких суспільство, усі його члени повинні прагнути, якими вони керуються у своєму повсякденному житті.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 69 (Seed 123): Олігополія (eval_shard_004_of_005.jsonl:line_30)
- **Subject / Grade:** ekonomika (Grade 10)
- **Concept:** `Олігополія` (Citation form: ✅)
- **Scientific Terminology:** `['ситуація', 'фірма']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Олігополією називають ринкову ситуацію, за якої декілька фірм домінує в галузі.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 70 (Seed 123): Громадянство (eval_shard_004_of_005.jsonl:line_17)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Громадянство` (Citation form: ✅)
- **Scientific Terminology:** `['особа', 'держава', 'вияв', 'право', "обов'язок"]` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Громадянство – правовий зв'язок між фізичною особою і державою, який знаходить свій вияв у взаємних правах і обов'язках.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 71 (Seed 123): Європейський карвінг (eval_shard_005_of_005.jsonl:line_28)
- **Subject / Grade:** tekhnolohiyi (Grade 8)
- **Concept:** `Європейський карвінг` (Citation form: ✅)
- **Scientific Terminology:** `['карвінг', 'різьблення', 'овоч', 'фрукт', 'редька']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Європейський карвінг — це різьблення по овочах і фруктах, які ростуть у Європі: редьці, редисці, буряках, моркві, болгарських і гострих перцях, кабачках, гарбузах, баклажанах, цибулі, капусті.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 72 (Seed 123): Автоматика (eval_shard_005_of_005.jsonl:line_22)
- **Subject / Grade:** tekhnolohiyi (Grade 8)
- **Concept:** `Автоматика` (Citation form: ✅)
- **Scientific Terminology:** `['механізм', 'прилад']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Автоматика — сукупність механізмів, приладів, що діють автоматично.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 73 (Seed 123): Поведінка людини (eval_shard_005_of_005.jsonl:line_36)
- **Subject / Grade:** etyka (Grade 6)
- **Concept:** `Поведінка людини` (Citation form: ✅)
- **Scientific Terminology:** `['поведінка', 'здатність', 'подразник']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Поведінка людини — прояви здатності людей реагувати на внутрішні й зовнішні подразники впродовж їхнього життя.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 74 (Seed 123): Оздоровча система (eval_shard_005_of_005.jsonl:line_16)
- **Subject / Grade:** zdorovia (Grade 8)
- **Concept:** `Оздоровча система` (Citation form: ✅)
- **Scientific Terminology:** `['система', 'знання', 'навичка', 'звичка', 'формування']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Оздоровча система — це цілісна система знань, навичок і звичок, що сприяють формуванню та зміцненню здоров'я.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 75 (Seed 123): Офорт (eval_shard_005_of_005.jsonl:line_8)
- **Subject / Grade:** mystetstvo (Grade 8)
- **Concept:** `Офорт` (Citation form: ✅)
- **Scientific Terminology:** `['різновид', 'гравюра', 'метал', 'відтиск', 'кислота']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Офорт — різновид гравюри на металі, який дозволяє отримувати відтиски з друкарських форм, попередньо оброблених кислотами.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 76 (Seed 123): Толерантність (sft_shard_019_of_150.jsonl:line_152)
- **Subject / Grade:** ya_doslidzhuiu_svit (Grade 3)
- **Concept:** `Толерантність` (Citation form: ✅)
- **Scientific Terminology:** `['повага', 'ставлення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Толерантність — це повага, доброзичливе й терпиме ставлення до когось чи чогось.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 77 (Seed 123): Перпендикулярні прямі (sft_shard_013_of_150.jsonl:line_402)
- **Subject / Grade:** heometriya (Grade 7)
- **Concept:** `Перпендикулярні прямі` (Citation form: ✅)
- **Scientific Terminology:** `['кут', 'перетин']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Дві прямі називають перпендикулярними, якщо при їхньому перетині утворився прямий кут.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 78 (Seed 123): Масовий відсоток (sft_shard_103_of_150.jsonl:line_292)
- **Subject / Grade:** algebra (Grade 8)
- **Concept:** `Масовий відсоток` (Citation form: ✅)
- **Scientific Terminology:** `['частка', 'відсоток', 'маса', 'речовина', 'грам']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Масову частку у відсотках називають масовим відсотком (маса речовини в грамах у 100 г розчину, позначають % м/м).» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 79 (Seed 123): Критичне мислення (sft_shard_106_of_150.jsonl:line_306)
- **Subject / Grade:** zdorovia (Grade 6)
- **Concept:** `Критичне мислення` (Citation form: ✅)
- **Scientific Terminology:** `['мислення', 'здатність', 'доцільність', 'варіант']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Критичне мислення — це здатність відрізняти достовірні факти від недостовірних та оцінювати доцільність тих чи тих варіантів дій.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 80 (Seed 123): Органи зору живих істот (sft_shard_014_of_150.jsonl:line_208)
- **Subject / Grade:** fizyka (Grade 9)
- **Concept:** `Органи зору живих істот` (Citation form: ✅)
- **Scientific Terminology:** `['орган', 'зір', 'істота']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Органи зору живих істот — природні приймачі світла.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 81 (Seed 123): Сахароза (sft_shard_123_of_150.jsonl:line_277)
- **Subject / Grade:** biolohiya (Grade 9)
- **Concept:** `Сахароза` (Citation form: ✅)
- **Scientific Terminology:** `['дисахарид', 'залишок', 'глюкоза', 'фруктоза']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Сахароза — дисахарид, що складається із залишків глюкози та фруктози.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 82 (Seed 123): Мода вибірки (sft_shard_003_of_150.jsonl:line_223)
- **Subject / Grade:** algebra (Grade 8)
- **Concept:** `Мода вибірки` (Citation form: ✅)
- **Scientific Terminology:** `['мода', 'вибірка', 'ряд']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Мода вибірки — це значення вибірки, яке трапляється у варіаційному ряді найчастіше.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 83 (Seed 123): Інтернет (sft_shard_031_of_150.jsonl:line_129)
- **Subject / Grade:** tekhnolohiyi (Grade 6)
- **Concept:** `Інтернет` (Citation form: ✅)
- **Scientific Terminology:** `['бібліотека', 'книга', 'підлога']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Інтернет — найбільша у світі бібліотека, тільки всі книги розкидано по підлозі.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 84 (Seed 123): Продуценти (sft_shard_043_of_150.jsonl:line_172)
- **Subject / Grade:** biolohiya (Grade 11)
- **Concept:** `Продуценти` (Citation form: ✅)
- **Scientific Terminology:** `['організм', 'сполука', 'побудова']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Продуценти — це автотрофні організми, які здатні перетворювати неорганічні сполуки на органічні й використовувати останні для побудови власного організму.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 85 (Seed 123): Реліктове випромінювання (sft_shard_036_of_150.jsonl:line_71)
- **Subject / Grade:** astronomiya (Grade 11)
- **Concept:** `Реліктове випромінювання` (Citation form: ✅)
- **Scientific Terminology:** `['випромінювання', 'квант']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Реліктове випромінювання — кванти світла, що утворилися 15 млрд років тому.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 86 (Seed 123): Вуглеводи (sft_shard_056_of_150.jsonl:line_169)
- **Subject / Grade:** khimiya (Grade 10)
- **Concept:** `Вуглеводи` (Citation form: ✅)
- **Scientific Terminology:** `['сполука', 'природа']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Вуглеводи — найпоширеніші органічні сполуки в природі.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 87 (Seed 123): Динамічне програмування (sft_shard_006_of_150.jsonl:line_82)
- **Subject / Grade:** informatyka (Grade 11)
- **Concept:** `Динамічне програмування` (Citation form: ✅)
- **Scientific Terminology:** `['програмування', 'пошук', 'вирішення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Динамічне програмування — розділ математичного програмування, що вивчає багатокрокові процеси пошуку оптимального вирішення складних завдань.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 88 (Seed 123): Органи (sft_shard_115_of_150.jsonl:line_434)
- **Subject / Grade:** pryroda (Grade 6)
- **Concept:** `Органи` (Citation form: ✅)
- **Scientific Terminology:** `['тіло', 'розташування', 'організм', 'функція']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Органи — частини тіла, які мають певні форму, місце розташування в організмі й виконують конкретні функції.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 89 (Seed 123): Трансплантація (sft_shard_137_of_150.jsonl:line_130)
- **Subject / Grade:** biolohiya (Grade 10)
- **Concept:** `Трансплантація` (Citation form: ✅)
- **Scientific Terminology:** `['орган', 'тканина', 'пересадка', 'реципієнт', 'організм']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Трансплантація — це пересадка реципієнту органа або тканини, які були взяті з організму донора.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 90 (Seed 123): Зоря (sft_shard_057_of_150.jsonl:line_288)
- **Subject / Grade:** astronomiya (Grade 11)
- **Concept:** `Зоря` (Citation form: ✅)
- **Scientific Terminology:** `['тяжіння', 'енергія']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Зоря — це величезна куля гарячого газу, яка утримується як одне ціле завдяки власній силі тяжіння й розігрівається ядерною енергією.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 91 (Seed 123): Територіальна громада (sft_shard_010_of_150.jsonl:line_350)
- **Subject / Grade:** hromadianska (Grade 9)
- **Concept:** `Територіальна громада` (Citation form: ✅)
- **Scientific Terminology:** `['громада', 'село', 'місто', 'пункт', 'інтерес']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Територіальна громада — це всі жителі села, селища чи міста (або кількох населених пунктів), які об'єднані спільними інтересами та ресурсами.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 92 (Seed 123): Міцелій (sft_shard_015_of_150.jsonl:line_496)
- **Subject / Grade:** biolohiya (Grade 10)
- **Concept:** `Міцелій` (Citation form: ✅)
- **Scientific Terminology:** `['структура', 'відросток', 'гіф']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Міцелій — це гігантська розгалужена структура, окремі ниткоподібні відростки якої називаються гіфами.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 93 (Seed 123): Система колективної безпеки (sft_shard_121_of_150.jsonl:line_332)
- **Subject / Grade:** vsesvitnia (Grade 10)
- **Concept:** `Система колективної безпеки` (Citation form: ✅)
- **Scientific Terminology:** `['система', 'безпека', 'здійснення', 'захист', 'загроза']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Система колективної безпеки — сукупність спільних дій держав із метою здійснення захисту від внутрішніх та зовнішніх загроз.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 94 (Seed 123): Сфера (sft_shard_066_of_150.jsonl:line_332)
- **Subject / Grade:** matematyka (Grade 11)
- **Concept:** `Сфера` (Citation form: ✅)
- **Scientific Terminology:** `['тіло', 'відстань']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Сферою називається тіло, що складається з усіх точок простору, розташованих на заданій відстані (R) від заданої точки (O).» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 95 (Seed 123): Народження проєкту (sft_shard_128_of_150.jsonl:line_58)
- **Subject / Grade:** tekhnolohiyi (Grade 9)
- **Concept:** `Народження проєкту` (Citation form: ✅)
- **Scientific Terminology:** `['народження', 'проєкт', 'визначення', 'проблема', 'формулювання']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Народження проєкту – це визначення проблеми, над якою ми плануємо працювати, формулювання мети й очікуваного результату проєкту, планування наших дій.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 96 (Seed 123): Моделювання (sft_shard_011_of_150.jsonl:line_104)
- **Subject / Grade:** informatyka (Grade 9)
- **Concept:** `Моделювання` (Citation form: ✅)
- **Scientific Terminology:** `['побудова', 'модель', 'сцена', "об'єкт"]` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Моделювання — побудова математичної 3D-моделі загальної сцени і її об'єктів.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 97 (Seed 123): Раціональне рівняння (sft_shard_032_of_150.jsonl:line_49)
- **Subject / Grade:** algebra (Grade 8)
- **Concept:** `Раціональне рівняння` (Citation form: ✅)
- **Scientific Terminology:** `['рівняння', 'вираз']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Раціональне рівняння називається дробовим раціональним рівнянням, якщо принаймні одна з його частин містить дробовий вираз.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 98 (Seed 123): Погон (sft_shard_026_of_150.jsonl:line_8)
- **Subject / Grade:** zakhyst (Grade 10)
- **Concept:** `Погон` (Citation form: ✅)
- **Scientific Terminology:** `['елемент', 'одяг', 'розрізнення', 'звання', 'символіка']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Погон — наплічний або нагрудний елемент форменого одягу, на якому розміщені знаки розрізнення військового звання та інші елементи військової символіки.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 99 (Seed 123): Дріжджі (sft_shard_027_of_150.jsonl:line_179)
- **Subject / Grade:** ya_doslidzhuiu_svit (Grade 3)
- **Concept:** `Дріжджі` (Citation form: ✅)
- **Scientific Terminology:** `['гриб', 'вуглевод']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Дріжджі — мікроскопічні гриби, які живляться вуглеводами.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 100 (Seed 123): Подвійні зорі (sft_shard_040_of_150.jsonl:line_33)
- **Subject / Grade:** astronomiya (Grade 11)
- **Concept:** `Подвійні зорі` (Citation form: ✅)
- **Scientific Terminology:** `['система', 'зір', 'орбіта', 'центр', 'маса']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Подвійні зорі — системи, які складаються з двох зір, що описують замкнені орбіти навколо спільного центра мас під дією взаємного тяжіння.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 101 (Seed 777): Ренесанс (eval_shard_001_of_005.jsonl:line_6)
- **Subject / Grade:** istoriya (Grade 8)
- **Concept:** `Ренесанс` (Citation form: ✅)
- **Scientific Terminology:** `['стиль', 'мистецтво']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Ренесанс — стиль в європейському мистецтві XV — початку XVI ст.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 102 (Seed 777): Козацька рада (eval_shard_001_of_005.jsonl:line_8)
- **Subject / Grade:** istoriya (Grade 8)
- **Concept:** `Козацька рада` (Citation form: ✅)
- **Scientific Terminology:** `['назва', 'зібрання', 'вирішення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Козацька рада — узагальнена назва зібрання козаків для вирішеннях певних питань.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 103 (Seed 777): Енциклопедія (eval_shard_001_of_005.jsonl:line_19)
- **Subject / Grade:** vsesvitnia (Grade 8)
- **Concept:** `Енциклопедія` (Citation form: ✅)
- **Scientific Terminology:** `['довідник', 'відомість', 'галузь', 'знання']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Енциклопедія – науковий довідник, що об'єднує найістотніші відомості з усіх галузей знань чи якої-небудь однієї галузі, розміщені в алфавітному або тематичному порядку.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 104 (Seed 777): Електричне поле (eval_shard_001_of_005.jsonl:line_27)
- **Subject / Grade:** fizyka (Grade 8)
- **Concept:** `Електричне поле` (Citation form: ✅)
- **Scientific Terminology:** `['матерія', 'тіло', 'частинка', 'заряд']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Електричне поле — це особливий вид матерії, що існує навколо заряджених тіл або частинок і діє з певною силою на інші тіла або частинки, які мають електричний заряд.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 105 (Seed 777): Пропускна здатність водопровідної труби (eval_shard_001_of_005.jsonl:line_7)
- **Subject / Grade:** heometriya (Grade 9)
- **Concept:** `Пропускна здатність водопровідної труби` (Citation form: ✅)
- **Scientific Terminology:** `['здатність', 'маса', 'переріз', 'одиниця']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Пропускна здатність водопровідної труби — це маса води, яка проходить через поперечний переріз труби за одиницю часу.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 106 (Seed 777): Юридична відповідальність (eval_shard_002_of_005.jsonl:line_34)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Юридична відповідальність` (Citation form: ✅)
- **Scientific Terminology:** `['правопорушення', 'відповідальність', 'застосування', 'особа', 'захід']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Юридична відповідальність — застосування до винної особи заходів державного примусу за вчинене нею правопорушення.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 107 (Seed 777): Форма державного устрою (eval_shard_002_of_005.jsonl:line_8)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Форма державного устрою` (Citation form: ✅)
- **Scientific Terminology:** `['устрій', 'елемент', 'держава', 'структура', 'поділ']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Форма державного устрою — елемент форми держави, що характеризує внутрішню структуру держави, спосіб її територіального поділу, співвідношення держави як єдиного цілого з її складовими частинами.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 108 (Seed 777): Правопорушення (eval_shard_002_of_005.jsonl:line_27)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Правопорушення` (Citation form: ✅)
- **Scientific Terminology:** `['дія', 'бездіяльність', 'норма', 'відповідальність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Правопорушення — протиправна винна дія або бездіяльність, що порушує встановлені суспільні норми та за яку передбачено юридичну відповідальність.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 109 (Seed 777): Орган (eval_shard_002_of_005.jsonl:line_5)
- **Subject / Grade:** biolohiya (Grade 8)
- **Concept:** `Орган` (Citation form: ✅)
- **Scientific Terminology:** `['тканина', 'складник', 'організм', 'функція']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Орган — це складник організму, який має визначену форму й будову, утворений різними тканинами, які взаємодіють між собою, розташований у певній його частині та виконує одну або кілька функцій.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 110 (Seed 777): Протиправне діяння (eval_shard_002_of_005.jsonl:line_31)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Протиправне діяння` (Citation form: ✅)
- **Scientific Terminology:** `['діяння', 'акт', 'поведінка', 'дія', 'бездіяльність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Протиправне діяння — акт поведінки людини, виражений в активній дії або пасивній бездіяльності.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 111 (Seed 777): Вегетаційний період (eval_shard_003_of_005.jsonl:line_13)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Вегетаційний період` (Citation form: ✅)
- **Scientific Terminology:** `['період', 'рослина']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Вегетаційний період – час, протягом якого рослина вегетує, тобто росте та розвивається.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 112 (Seed 777): Природні умови (eval_shard_003_of_005.jsonl:line_30)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Природні умови` (Citation form: ✅)
- **Scientific Terminology:** `['природа', 'участь']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Природні умови – складові і властивості природи Землі, що впливають на життя та діяльність людства, але не беруть безпосередньої участі в них.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 113 (Seed 777): Слідчий (eval_shard_003_of_005.jsonl:line_14)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Слідчий` (Citation form: ✅)
- **Scientific Terminology:** `['особа', 'орган', 'розслідування']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Слідчий — службова особа відповідного органу досудового розслідування.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 114 (Seed 777): Надзвичайний стан (eval_shard_003_of_005.jsonl:line_6)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Надзвичайний стан` (Citation form: ✅)
- **Scientific Terminology:** `['режим', 'район', 'виникнення', 'ситуація', 'характер']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Надзвичайний стан — особливий правовий режим, який може бути тимчасово запроваджений в Україні або її окремих районах у разі виникнення надзвичайних ситуацій техногенного або природного характеру, захоплення державної влади чи зміни конституційного ладу України шляхом насильства.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 115 (Seed 777): Кримінальне право (eval_shard_003_of_005.jsonl:line_36)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Кримінальне право` (Citation form: ✅)
- **Scientific Terminology:** `['правопорушення', 'право', 'система', 'норма', 'діяння']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Кримінальне право — система юридичних норм, що встановлюють, які суспільно небезпечні діяння є кримінальними правопорушеннями та які покарання передбачені за їх вчинення.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 116 (Seed 777): Правова держава (eval_shard_004_of_005.jsonl:line_22)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Правова держава` (Citation form: ✅)
- **Scientific Terminology:** `['держава', 'верховенство']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Правова держава – це держава, в якій існує верховенство права.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 117 (Seed 777): Обмін (eval_shard_004_of_005.jsonl:line_28)
- **Subject / Grade:** ekonomika (Grade 10)
- **Concept:** `Обмін` (Citation form: ✅)
- **Scientific Terminology:** `['рух', 'товар', 'власник']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Обмін — це рух товарів від одного власника до іншого.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 118 (Seed 777): Громадянський обов'язок (eval_shard_004_of_005.jsonl:line_12)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Громадянський обов'язок` (Citation form: ✅)
- **Scientific Terminology:** `["обов'язок", 'громадянин', 'країна', 'закон', 'норма']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Громадянський обов'язок – це обов'язок, який мають всі громадяни країни відповідно до законів і моральних норм.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 119 (Seed 777): Кримінальна відповідальність (eval_shard_004_of_005.jsonl:line_1)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Кримінальна відповідальність` (Citation form: ✅)
- **Scientific Terminology:** `['відповідальність', 'покарання', 'держава', 'особа', 'злочин']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Кримінальна відповідальність — покарання, що застосовує держава до особи, яка вчинила злочин.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 120 (Seed 777): Місцевий колорит (eval_shard_004_of_005.jsonl:line_38)
- **Subject / Grade:** zarlit (Grade 8)
- **Concept:** `Місцевий колорит` (Citation form: ✅)
- **Scientific Terminology:** `['колорит', 'твір', 'елемент', 'побут', 'традиція']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Місцевий колорит – літературний прийом, що упроваджує у твір елементи побуту, традицій, звичаїв, природи, історії тощо, якими характеризується життя певної етнічної групи або іншої спільноти на певній території.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 121 (Seed 777): Соціальна відповідальність бізнесу (eval_shard_005_of_005.jsonl:line_13)
- **Subject / Grade:** zdorovia (Grade 8)
- **Concept:** `Соціальна відповідальність бізнесу` (Citation form: ✅)
- **Scientific Terminology:** `['відповідальність', 'бізнес', 'практика', 'участь', 'підприємець']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Соціальна відповідальність бізнесу — стратегічна практика, спрямована на активну участь підприємців у розв'язанні соціальних проблем.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 122 (Seed 777): Милостиня (eval_shard_005_of_005.jsonl:line_41)
- **Subject / Grade:** etyka (Grade 6)
- **Concept:** `Милостиня` (Citation form: ✅)
- **Scientific Terminology:** `['виявлення', 'турбота']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Милостиня — виявлення турботи до людини, яка перебуває в скрутному становищі у вигляді допомоги в різних формах.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 123 (Seed 777): Взаємоповага (eval_shard_005_of_005.jsonl:line_38)
- **Subject / Grade:** etyka (Grade 6)
- **Concept:** `Взаємоповага` (Citation form: ✅)
- **Scientific Terminology:** `['повага', 'виявлення', 'почуття', 'взаємність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Взаємоповага — виявлення людьми поваги одне до одного, що ґрунтується на почутті взаємності.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 124 (Seed 777): Лікувальне дієтичне харчування (eval_shard_005_of_005.jsonl:line_15)
- **Subject / Grade:** zdorovia (Grade 8)
- **Concept:** `Лікувальне дієтичне харчування` (Citation form: ✅)
- **Scientific Terminology:** `['харчування', 'лікування', 'хвороба']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Лікувальне дієтичне харчування — це спеціальне харчування, що є обов'язковою частиною комплексного лікування певної хвороби або хвороб.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 125 (Seed 777): Етнічна музика (eval_shard_005_of_005.jsonl:line_2)
- **Subject / Grade:** mystetstvo (Grade 8)
- **Concept:** `Етнічна музика` (Citation form: ✅)
- **Scientific Terminology:** `['витік', 'фольклор', 'етнос']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Етнічна музика — музика, витоки якої полягають у музичному фольклорі певного етносу.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 126 (Seed 777): Шлях (sft_shard_101_of_150.jsonl:line_3)
- **Subject / Grade:** fizyka (Grade 7)
- **Concept:** `Шлях` (Citation form: ✅)
- **Scientific Terminology:** `['довжина', 'траєкторія']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Шлях — це фізична величина, яка дорівнює довжині траєкторії.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 127 (Seed 777): Монетарна політика (sft_shard_109_of_150.jsonl:line_373)
- **Subject / Grade:** ekonomika (Grade 11)
- **Concept:** `Монетарна політика` (Citation form: ✅)
- **Scientific Terminology:** `['інфляція', 'політика', 'комплекс', 'захід', 'сфера']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Монетарна політика — це комплекс заходів у грошово-кредитній сфері, спрямованих на забезпечення економіки стабільною національною грошовою одиницею, на контролювання інфляції, стимулювання економічного зростання, забезпечення високого рівня зайнятості населення та вирівнювання платіжного балансу.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 128 (Seed 777): Електронне урядування (sft_shard_070_of_150.jsonl:line_284)
- **Subject / Grade:** informatyka (Grade 10)
- **Concept:** `Електронне урядування` (Citation form: ✅)
- **Scientific Terminology:** `['урядування', 'організація', 'управління', 'підвищення', 'ефективність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Електронне урядування — форма організації державного управління, яка сприяє підвищенню ефективності, відкритості та прозорості діяльності органів державної влади й органів місцевого самоврядування з використанням ІКТ для формування держави нового типу, орієнтованої на задоволення потреб громадян.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 129 (Seed 777): Інфекційні захворювання (sft_shard_118_of_150.jsonl:line_128)
- **Subject / Grade:** zdorovia (Grade 5)
- **Concept:** `Інфекційні захворювання` (Citation form: ✅)
- **Scientific Terminology:** `['захворювання', 'хвороба', 'здатність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Інфекційні захворювання — це хвороби, які мають здатність передаватися від хворої людини до здорової.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 130 (Seed 777): Лінія прицілювання (sft_shard_014_of_150.jsonl:line_258)
- **Subject / Grade:** zakhyst (Grade 10)
- **Concept:** `Лінія прицілювання` (Citation form: ✅)
- **Scientific Terminology:** `['прицілювання', 'око', 'проріз', 'приціл']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Лінія прицілювання — пряма лінія, яка проходить від ока стрільця через середину прорізу прицілу (на рівні з її краями) і вершину мушки в точку прицілювання.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 131 (Seed 777): Змінні зорі (sft_shard_119_of_150.jsonl:line_349)
- **Subject / Grade:** astronomiya (Grade 11)
- **Concept:** `Змінні зорі` (Citation form: ✅)
- **Scientific Terminology:** `['блиск', 'поверхня', 'дія', 'причина', 'затемнення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Змінні зорі називають фізично-змінними, якщо зміни блиску зумовлені процесами, що відбуваються в самій зорі або на її поверхні, і оптичними у випадку, якщо блиск зорі змінюється внаслідок дії зовнішніх щодо неї причин, наприклад під час періодичних затемнень іншою зорею.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 132 (Seed 777): Фізика (sft_shard_142_of_150.jsonl:line_383)
- **Subject / Grade:** fizyka (Grade 7)
- **Concept:** `Фізика` (Citation form: ✅)
- **Scientific Terminology:** `['наука', 'закономірність', 'природа', 'матерія', 'закон']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Фізика — це природнича наука, яка вивчає найзагальніші закономірності явищ природи, властивості та будову матерії*, закони її руху.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 133 (Seed 777): Благодійність (sft_shard_011_of_150.jsonl:line_455)
- **Subject / Grade:** hromadianska (Grade 9)
- **Concept:** `Благодійність` (Citation form: ✅)
- **Scientific Terminology:** `['намір', 'передача', 'навичка', 'енергія']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Благодійність — це допомога іншим не заради винагороди, а з добрих намірів, що може проявлятися в різних формах: матеріальній (зокрема фінансовій) або особистій (передача навичок, часу, енергії).» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 134 (Seed 777): Статут підприємства (sft_shard_079_of_150.jsonl:line_125)
- **Subject / Grade:** ekonomika (Grade 11)
- **Concept:** `Статут підприємства` (Citation form: ✅)
- **Scientific Terminology:** `['статут', 'підприємство', 'зібрання', "суб'єкт", 'господарювання']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Статут підприємства — зібрання обов'язкових правил, що регулюють його індивідуальну (їх сукупну) діяльність, взаємовідносини з іншими суб'єктами господарювання.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 135 (Seed 777): Абсолютний показник заломлення (sft_shard_026_of_150.jsonl:line_117)
- **Subject / Grade:** fizyka (Grade 9)
- **Concept:** `Абсолютний показник заломлення` (Citation form: ✅)
- **Scientific Terminology:** `['заломлення', 'показник', 'вакуум']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Абсолютний показник заломлення — це показник заломлення відносно вакууму.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 136 (Seed 777): Русинство (sft_shard_084_of_150.jsonl:line_425)
- **Subject / Grade:** istoriya (Grade 10)
- **Concept:** `Русинство` (Citation form: ✅)
- **Scientific Terminology:** `['течія', 'визнання', 'населення', 'нація']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Русинство — політична течія, що виступала за визнання слов'янського населення Закарпаття окремою нацією.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 137 (Seed 777): Інформаційна революція (sft_shard_034_of_150.jsonl:line_476)
- **Subject / Grade:** vsesvitnia (Grade 10)
- **Concept:** `Інформаційна революція` (Citation form: ✅)
- **Scientific Terminology:** `['революція', 'зміна', 'формування', 'суспільство', 'технологія']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Інформаційна революція — процес докорінних якісних змін, пов'язаних із формуванням інформаційного суспільства (того, де інформаційні технології та засоби масової комунікації відіграють провідну роль).» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 138 (Seed 777): Міжнародна торгівля (sft_shard_126_of_150.jsonl:line_397)
- **Subject / Grade:** ekonomika (Grade 11)
- **Concept:** `Міжнародна торгівля` (Citation form: ✅)
- **Scientific Terminology:** `['торгівля', 'переміщення', 'товар', 'послуга', 'кордон']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Міжнародна торгівля — це переміщення товарів та послуг через митні кордони різних країн.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 139 (Seed 777): Терплячість (sft_shard_036_of_150.jsonl:line_267)
- **Subject / Grade:** etyka (Grade 5)
- **Concept:** `Терплячість` (Citation form: ✅)
- **Scientific Terminology:** `['здатність', 'витримка', 'подолання']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Терплячість — це здатність проявляти витримку під час подолання труднощів.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 140 (Seed 777): Ліричні твори (sft_shard_028_of_150.jsonl:line_67)
- **Subject / Grade:** ukrlit (Grade 5)
- **Concept:** `Ліричні твори` (Citation form: ✅)
- **Scientific Terminology:** `['почуття', 'переживання', 'обставина', 'вплив']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Ліричні твори — це твори, у яких виражено думки, почуття та переживання людини в певних обставинах, під впливом певних подій.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 141 (Seed 777): Друкований текст (sft_shard_150_of_150.jsonl:line_195)
- **Subject / Grade:** zarlit (Grade 5)
- **Concept:** `Друкований текст` (Citation form: ✅)
- **Scientific Terminology:** `['засіб', 'друк', 'папір']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Друкований текст – текст, відтворений засобами друку на папері.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 142 (Seed 777): Колообіг води (sft_shard_057_of_150.jsonl:line_92)
- **Subject / Grade:** ya_doslidzhuiu_svit (Grade 3)
- **Concept:** `Колообіг води` (Citation form: ✅)
- **Scientific Terminology:** `['природа', 'колообіг', 'перетворення', 'переміщення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Колообіг води — це перетворення води з одного стану в інший і переміщення її в природі.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 143 (Seed 777): Викрадення українських дітей (sft_shard_135_of_150.jsonl:line_125)
- **Subject / Grade:** vsesvitnia (Grade 11)
- **Concept:** `Викрадення українських дітей` (Citation form: ✅)
- **Scientific Terminology:** `['травень', 'викрадення', 'дитина', 'геноцид']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Дмитро Лубінець, Уповноважений Верховної Ради України з прав людини, 8 травня 2023 р.: „Викрадення українських дітей — це геноцид“.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 144 (Seed 777): Композиторський стиль (sft_shard_083_of_150.jsonl:line_313)
- **Subject / Grade:** mystetstvo (Grade 10)
- **Concept:** `Композиторський стиль` (Citation form: ✅)
- **Scientific Terminology:** `['стиль', 'творчість', 'композитор', 'період', 'тенденція']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Композиторський стиль — поняття, яке набагато простіше конкретизувати, адже творчість будь-якого композитора обмежена порівняно невеликим тимчасовим періодом і певними тенденціями музичної епохи.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 145 (Seed 777): Провідні мотиви (sft_shard_094_of_150.jsonl:line_440)
- **Subject / Grade:** ukrlit (Grade 11)
- **Concept:** `Провідні мотиви` (Citation form: ✅)
- **Scientific Terminology:** `['мотив', 'переосмислення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Провідні мотиви — любов до рідної землі, переосмислення її історії.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 146 (Seed 777): Кремній (sft_shard_133_of_150.jsonl:line_453)
- **Subject / Grade:** heohrafiya (Grade 9)
- **Concept:** `Кремній` (Citation form: ✅)
- **Scientific Terminology:** `['матеріал', 'електроніка']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Кремній – матеріал, який широко використовують в електроніці.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 147 (Seed 777): Археї (sft_shard_015_of_150.jsonl:line_421)
- **Subject / Grade:** biolohiya (Grade 7)
- **Concept:** `Археї` (Citation form: ✅)
- **Scientific Terminology:** `['учасник', 'кругообіг', 'речовина']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Археї – учасники багатьох важливих природних явищ, пов'язаних з кругообігом хімічних речовин на Землі.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 148 (Seed 777): Рівні фігури (sft_shard_039_of_150.jsonl:line_298)
- **Subject / Grade:** heometriya (Grade 9)
- **Concept:** `Рівні фігури` (Citation form: ✅)
- **Scientific Terminology:** `['фігура', 'переміщення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Дві фігури називають рівними, якщо вони переміщенням переводяться одна в одну.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 149 (Seed 777): Господарський договір (sft_shard_032_of_150.jsonl:line_103)
- **Subject / Grade:** pravoznavstvo (Grade 11)
- **Concept:** `Господарський договір` (Citation form: ✅)
- **Scientific Terminology:** `['договір', 'угода', "суб'єкт", 'контрагент', "зобов'язання"]` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Господарський договір — майнова угода господарюючого суб'єкта з контрагентом, яка встановлює (змінює, припиняє) зобов'язання сторін у сфері господарської та комерційної діяльності: при виробництві та реалізації продукції, виконанні робіт, наданні послуг.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 150 (Seed 777): Депресія (sft_shard_093_of_150.jsonl:line_279)
- **Subject / Grade:** ekonomika (Grade 11)
- **Concept:** `Депресія` (Citation form: ✅)
- **Scientific Terminology:** `['виробництво', 'фаза', 'цикл', 'застій']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Депресія — фаза циклу, яка проявляється в застої виробництва.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**
