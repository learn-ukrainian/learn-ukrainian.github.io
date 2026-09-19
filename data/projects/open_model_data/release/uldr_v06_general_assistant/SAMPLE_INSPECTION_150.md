# Multi-Seed Sample Inspection of 150 Mined Records (Phase 6.1)

**Audit Result:** ALL 150 RECORDS PASSED — 100% PASS RATE

**Sampling Protocol:** 3 PRNG seeds (42, 123, 777), 50 records per seed (total 150 records across eval and SFT shards).

## Release-Wide Defect Scan (All 75,000 SFT + 261 Eval Records)

| Defect Class | Count Across Release | Status |
|---|---|---|
| `truncated_snippets` | 0 | ✅ 0 (Permanently Eliminated) |
| `inverted_definitions` | 0 | ✅ 0 (Permanently Eliminated) |
| `disallowed_lemmas` | 0 | ✅ 0 (Permanently Eliminated) |
| `substring_terms` | 0 | ✅ 0 (Permanently Eliminated) |
| `unresolved_anaphora` | 0 | ✅ 0 (Permanently Eliminated) |
| `context_bound_heads` | 0 | ✅ 0 (Permanently Eliminated) |
| `descriptive_non_concepts` | 0 | ✅ 0 (Permanently Eliminated) |
| `metaphors_and_evaluatives` | 0 | ✅ 0 (Permanently Eliminated) |
| `query_framing_mismatch` | 0 | ✅ 0 (Permanently Eliminated) |

## Multi-Seed Inspected Sample Overview

| # | Seed | Origin | Concept | Subject | Grade | Terms | Citation | Anaphora-Free | OCR-Clean | Def-Aligned | Terms Valid | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 42 | `eval_shard_001_of_005.jsonl:line_26` | **Верхня палата** | vsesvitnia | 8 | палата, сенат, представник, духовенство | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 2 | 42 | `eval_shard_001_of_005.jsonl:line_20` | **Меркантилізм** | vsesvitnia | 8 | політика, втручання, країна, накопичення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 3 | 42 | `eval_shard_001_of_005.jsonl:line_12` | **Козацьке бароко** | istoriya | 8 | стиль, земля, бароко | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 4 | 42 | `eval_shard_001_of_005.jsonl:line_5` | **Порядок дій** | matematyka | 5 | послідовність, виконання, вираз, результат | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 5 | 42 | `eval_shard_001_of_005.jsonl:line_46` | **Держава** | pravoznavstvo | 9 | організація, суспільство, цілісність, безпека | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 6 | 42 | `eval_shard_002_of_005.jsonl:line_43` | **Покадрова анімація** | informatyka | 7 | анімація, кадр, фільм | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 7 | 42 | `eval_shard_002_of_005.jsonl:line_42` | **Юридичні гарантії** | pravoznavstvo | 9 | гарантія, захід, здійснення, охорона | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 8 | 42 | `eval_shard_002_of_005.jsonl:line_14` | **Норма права** | pravoznavstvo | 9 | норма, поведінка, орган, держава | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 9 | 42 | `eval_shard_002_of_005.jsonl:line_10` | **Соціальні норми** | pravoznavstvo | 9 | норма, сфера | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 10 | 42 | `eval_shard_002_of_005.jsonl:line_20` | **Правомірна поведінка** | pravoznavstvo | 9 | поведінка, припис, норма, держава | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 11 | 42 | `eval_shard_003_of_005.jsonl:line_23` | **Ґрунтовий профіль** | heohrafiya | 8 | профіль, ґрунт, поверхня, порода | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 12 | 42 | `eval_shard_003_of_005.jsonl:line_19` | **Метеочутливість** | heohrafiya | 8 | організм, зміна | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 13 | 42 | `eval_shard_003_of_005.jsonl:line_11` | **Атмосферний фронт** | heohrafiya | 8 | фронт, зона, маса, кут | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 14 | 42 | `eval_shard_003_of_005.jsonl:line_15` | **Ожеледиця** | heohrafiya | 8 | крига, поверхня, відлига, температура | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 15 | 42 | `eval_shard_003_of_005.jsonl:line_18` | **Адміністративне стягнення** | pravoznavstvo | 9 | стягнення, порушення, невиконання, заборона | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 16 | 42 | `eval_shard_004_of_005.jsonl:line_49` | **Інкрустація** | mystetstvo | 8 | різновид, мозаїка, оздоблення, інтер'єр | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 17 | 42 | `eval_shard_004_of_005.jsonl:line_29` | **Корпоративна власність** | ekonomika | 10 | власність, особа, формування | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 18 | 42 | `eval_shard_004_of_005.jsonl:line_6` | **Завойовницька війна** | hromadianska | 8 | війна, розширення, сфера, територія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 19 | 42 | `eval_shard_004_of_005.jsonl:line_14` | **Право** | hromadianska | 8 | взаємоповага, суспільство | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 20 | 42 | `eval_shard_004_of_005.jsonl:line_38` | **Піктографічне письмо** | ukrmova | 8 | письмо, комунікація, значок, малюнок | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 21 | 42 | `eval_shard_005_of_005.jsonl:line_10` | **Симфонічна поема** | mystetstvo | 8 | поема, твір, програма | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 22 | 42 | `eval_shard_005_of_005.jsonl:line_26` | **Методи проєктування** | tekhnolohiyi | 8 | проєктування, дія, об'єкт | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 23 | 42 | `eval_shard_005_of_005.jsonl:line_13` | **Реалізм** | mystetstvo | 8 | відтворення, дійсність | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 24 | 42 | `eval_shard_005_of_005.jsonl:line_37` | **Базисний манікюр** | tekhnolohiyi | 8 | манікюр, процедура | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 25 | 42 | `eval_shard_005_of_005.jsonl:line_35` | **Жирність волосся** | tekhnolohiyi | 8 | жирність, волосся, результат, активність | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 26 | 42 | `sft_shard_057_of_150.jsonl:line_93` | **Ізотермічний процес** | fizyka | 10 | змінювання, маса, температура | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 27 | 42 | `sft_shard_102_of_150.jsonl:line_369` | **Співчуття** | ukrmova | 10 | крок, людяність | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 28 | 42 | `sft_shard_106_of_150.jsonl:line_349` | **Довжина перпендикуляра** | matematyka | 10 | площина, відстань, довжина, перпендикуляр | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 29 | 42 | `sft_shard_078_of_150.jsonl:line_211` | **Виділення окремих типів** | astronomiya | 11 | виділення, зміна, уявлення, масштаб | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 30 | 42 | `sft_shard_012_of_150.jsonl:line_460` | **Погода** | pryroda | 8 | атмосфера, територія, проміжок | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 31 | 42 | `sft_shard_003_of_150.jsonl:line_37` | **Ідеологія** | vsesvitnia | 9 | ідея, переконання, цінність, бачення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 32 | 42 | `sft_shard_091_of_150.jsonl:line_54` | **Паралельне проектування** | matematyka | 10 | перетворення, фігура, проектування | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 33 | 42 | `sft_shard_149_of_150.jsonl:line_387` | **Об'єм** | matematyka | 11 | відповідність, тіло | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 34 | 42 | `sft_shard_139_of_150.jsonl:line_384` | **Ліси** | ya_doslidzhuiu_svit | 4 | відпочинок, повітря | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 35 | 42 | `sft_shard_145_of_150.jsonl:line_17` | **Лайка** | etyka | 5 | гідність, неповага | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 36 | 42 | `sft_shard_129_of_150.jsonl:line_255` | **Літосферні плити** | heohrafiya | 6 | літосфера, розлом, астеносфера | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 37 | 42 | `sft_shard_002_of_150.jsonl:line_273` | **Причина появи вугрів** | zdorovia | 7 | причина, поява, вугор, закупорювання | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 38 | 42 | `sft_shard_117_of_150.jsonl:line_277` | **Гроші** | finansova | 9 | інструмент, їжа, освіта, відпочинок | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 39 | 42 | `sft_shard_116_of_150.jsonl:line_131` | **Мовлення** | ukrmova | 10 | спілкування, засіб | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 40 | 42 | `sft_shard_015_of_150.jsonl:line_477` | **Спілкування** | ukrmova | 10 | взаємодія, учасник, комунікація, реалізація | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 41 | 42 | `sft_shard_134_of_150.jsonl:line_171` | **Кредитна історія** | finansova | 9 | кредит, звіт, позичальник, заборгованість | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 42 | 42 | `sft_shard_045_of_150.jsonl:line_255` | **Запит з параметрами** | informatyka | 10 | запит, параметр, виконання | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 43 | 42 | `sft_shard_080_of_150.jsonl:line_210` | **Переміщення** | heometriya | 10 | перетворення, фігура, рух | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 44 | 42 | `sft_shard_108_of_150.jsonl:line_314` | **Пейзажна лірика** | zarlit | 5 | лірика, зображення, природа | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 45 | 42 | `sft_shard_127_of_150.jsonl:line_141` | **Посадова особа місцевого самоврядування** | pravoznavstvo | 11 | особа, самоврядування, орган, повноваження | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 46 | 42 | `sft_shard_042_of_150.jsonl:line_451` | **Кастинг** | mystetstvo | 7 | визначення, виконавець, кіно, театр | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 47 | 42 | `sft_shard_107_of_150.jsonl:line_75` | **Амортизація** | ekonomika | 11 | перенесення, вартість, засіб, продукція | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 48 | 42 | `sft_shard_056_of_150.jsonl:line_289` | **Дружба** | etyka | 5 | стосунок, довіра, щирість, симпатія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 49 | 42 | `sft_shard_010_of_150.jsonl:line_201` | **Міфологізм** | ukrlit | 11 | реалізація, твір, література | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 50 | 42 | `sft_shard_131_of_150.jsonl:line_432` | **Відкритий перелом** | zakhyst | 11 | перелом, пошкодження, цілісність, кістка | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 51 | 123 | `eval_shard_001_of_005.jsonl:line_48` | **Форма держави** | pravoznavstvo | 9 | держава, організація, структура, орган | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 52 | 123 | `eval_shard_001_of_005.jsonl:line_19` | **Коефіцієнт корисної дії** | fizyka | 8 | механізм, коефіцієнт, дія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 53 | 123 | `eval_shard_001_of_005.jsonl:line_26` | **Верхня палата** | vsesvitnia | 8 | палата, сенат, представник, духовенство | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 54 | 123 | `eval_shard_001_of_005.jsonl:line_41` | **Ізотоп** | khimiya | 8 | нуклід, заряд, ядро | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 55 | 123 | `eval_shard_001_of_005.jsonl:line_46` | **Держава** | pravoznavstvo | 9 | організація, суспільство, цілісність, безпека | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 56 | 123 | `eval_shard_002_of_005.jsonl:line_7` | **Орган** | biolohiya | 8 | тканина, складник, організм, функція | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 57 | 123 | `eval_shard_002_of_005.jsonl:line_30` | **Юридична відповідальність** | pravoznavstvo | 9 | правопорушення, відповідальність, застосування, особа | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 58 | 123 | `eval_shard_002_of_005.jsonl:line_20` | **Правомірна поведінка** | pravoznavstvo | 9 | поведінка, припис, норма, держава | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 59 | 123 | `eval_shard_002_of_005.jsonl:line_50` | **Дитяча конституція** | pravoznavstvo | 9 | конвенція, дитина, конституція | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 60 | 123 | `eval_shard_002_of_005.jsonl:line_43` | **Покадрова анімація** | informatyka | 7 | анімація, кадр, фільм | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 61 | 123 | `eval_shard_003_of_005.jsonl:line_5` | **Геологічна ера** | heohrafiya | 8 | підрозділ, шкала, утворення, порода | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 62 | 123 | `eval_shard_003_of_005.jsonl:line_42` | **Здібності** | hromadianska | 8 | схильність, виконання | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 63 | 123 | `eval_shard_003_of_005.jsonl:line_8` | **Цивільне право** | pravoznavstvo | 9 | право, галузь | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 64 | 123 | `eval_shard_003_of_005.jsonl:line_28` | **Звичаї** | hromadianska | 8 | побут, народ, колектив | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 65 | 123 | `eval_shard_003_of_005.jsonl:line_6` | **Позов** | pravoznavstvo | 9 | закон, звернення, особа, суд | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 66 | 123 | `eval_shard_004_of_005.jsonl:line_9` | **Властивість речовин** | pryroda | 5 | розпізнавання, опис, речовина | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 67 | 123 | `eval_shard_004_of_005.jsonl:line_28` | **Благо** | ekonomika | 10 | засіб, задоволення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 68 | 123 | `eval_shard_004_of_005.jsonl:line_49` | **Інкрустація** | mystetstvo | 8 | різновид, мозаїка, оздоблення, інтер'єр | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 69 | 123 | `eval_shard_004_of_005.jsonl:line_3` | **Географічний простір** | heohrafiya | 8 | простір, об'єкт, територія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 70 | 123 | `eval_shard_004_of_005.jsonl:line_46` | **Виверження вулкана** | zarlit | 8 | виверження, вулкан, комин, сажа | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 71 | 123 | `eval_shard_005_of_005.jsonl:line_51` | **Авторитет** | etyka | 6 | переконання, поведінка, особа, організація | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 72 | 123 | `eval_shard_005_of_005.jsonl:line_10` | **Симфонічна поема** | mystetstvo | 8 | поема, твір, програма | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 73 | 123 | `eval_shard_005_of_005.jsonl:line_31` | **Робот** | tekhnolohiyi | 8 | пристрій, комп'ютер, виконання, операція | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 74 | 123 | `eval_shard_005_of_005.jsonl:line_38` | **Європейський карвінг** | tekhnolohiyi | 8 | карвінг, різьблення, овоч, фрукт | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 75 | 123 | `eval_shard_005_of_005.jsonl:line_2` | **Гімн** | mystetstvo | 8 | характер, прославлення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 76 | 123 | `sft_shard_071_of_150.jsonl:line_492` | **Захист населення в надзвичайних ситуаціях** | zakhyst | 10 | захист, населення, ситуація, комплекс | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 77 | 123 | `sft_shard_100_of_150.jsonl:line_148` | **Участь в управлінні державними справами** | hromadianska | 9 | участь, управління, громадянин, контроль | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 78 | 123 | `sft_shard_072_of_150.jsonl:line_409` | **Вибори** | hromadianska | 9 | волевиявлення, здійснення, народ | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 79 | 123 | `sft_shard_051_of_150.jsonl:line_137` | **Давня шумерська глиняна табличка** | istoriya | 7 | табличка, угода | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 80 | 123 | `sft_shard_010_of_150.jsonl:line_100` | **Явища природи** | ya_doslidzhuiu_svit | 3 | природа, тіло | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 81 | 123 | `sft_shard_116_of_150.jsonl:line_128` | **Витрати** | tekhnolohiyi | 6 | обсяг, ресурс, проміжок | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 82 | 123 | `sft_shard_128_of_150.jsonl:line_400` | **Реліктове випромінювання** | astronomiya | 11 | випромінювання, квант, млрд | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 83 | 123 | `sft_shard_106_of_150.jsonl:line_283` | **Пожежі** | zakhyst | 11 | поширення, дія, вогонь, контроль | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 84 | 123 | `sft_shard_125_of_150.jsonl:line_424` | **Сила** | pryroda | 8 | міра, взаємодія, тіло | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 85 | 123 | `sft_shard_075_of_150.jsonl:line_288` | **Національна мова** | ukrmova | university | продукт, покоління, народ, розвиток | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 86 | 123 | `sft_shard_040_of_150.jsonl:line_240` | **Середня швидкість нерівномірного руху тіла** | pryroda | 8 | швидкість, рух, тіло, відношення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 87 | 123 | `sft_shard_140_of_150.jsonl:line_160` | **Будівництво каналів і дамб** | istoriya | 6 | будівництво, канал, дамба, річка | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 88 | 123 | `sft_shard_022_of_150.jsonl:line_370` | **Крапка в центрі кола** | zdorovia | 9 | крапка, центр, кіл, відлік | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 89 | 123 | `sft_shard_079_of_150.jsonl:line_8` | **Продовольчий кошик** | tekhnolohiyi | 5 | набір, продукт, харчування | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 90 | 123 | `sft_shard_094_of_150.jsonl:line_86` | **Дискримінація** | zdorovia | 7 | обмеження, громадянин, право, вік | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 91 | 123 | `sft_shard_124_of_150.jsonl:line_482` | **Висота циліндра** | matematyka | 11 | висота, циліндр, перпендикуляр | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 92 | 123 | `sft_shard_025_of_150.jsonl:line_493` | **Чистий дохід підприємства** | ekonomika | 11 | дохід, підприємство | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 93 | 123 | `sft_shard_087_of_150.jsonl:line_9` | **Обчислювальна геометрія** | informatyka | 11 | алгоритм, геометрія, галузь, наука | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 94 | 123 | `sft_shard_084_of_150.jsonl:line_373` | **Фінансові послуги** | heohrafiya | 9 | послуга, економіка, знання, сфера | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 95 | 123 | `sft_shard_012_of_150.jsonl:line_226` | **Народження проєкту** | tekhnolohiyi | 9 | народження, проєкт, визначення, проблема | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 96 | 123 | `sft_shard_103_of_150.jsonl:line_21` | **Майданник** | ukrmova | 4 | добування, вугілля, дерево | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 97 | 123 | `sft_shard_138_of_150.jsonl:line_55` | **Колообіг води** | ya_doslidzhuiu_svit | 3 | природа, колообіг, перетворення, переміщення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 98 | 123 | `sft_shard_021_of_150.jsonl:line_482` | **Видатки державного бюджету** | pravoznavstvo | 11 | закон, видаток, бюджет, кошт | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 99 | 123 | `sft_shard_031_of_150.jsonl:line_480` | **Золотаве волосся** | zarlit | 11 | волосся, традиція, елемент | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 100 | 123 | `sft_shard_041_of_150.jsonl:line_387` | **Гривня** | ya_doslidzhuiu_svit | 4 | одиниця, символ, кода | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 101 | 777 | `eval_shard_001_of_005.jsonl:line_12` | **Козацьке бароко** | istoriya | 8 | стиль, земля, бароко | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 102 | 777 | `eval_shard_001_of_005.jsonl:line_43` | **Орбіталь** | khimiya | 8 | ймовірність, перебування, електрон | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 103 | 777 | `eval_shard_001_of_005.jsonl:line_16` | **Буржуазія** | vsesvitnia | 8 | верства, власник, капітал, засіб | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 104 | 777 | `eval_shard_001_of_005.jsonl:line_31` | **Електричне поле** | fizyka | 8 | матерія, тіло, частинка, заряд | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 105 | 777 | `eval_shard_001_of_005.jsonl:line_38` | **Парламентська монархія** | vsesvitnia | 8 | монархія, правління, монарх, повноваження | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 106 | 777 | `eval_shard_002_of_005.jsonl:line_46` | **Біженець** | pravoznavstvo | 9 | особа, громадянин, причина, країна | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 107 | 777 | `eval_shard_002_of_005.jsonl:line_23` | **Реципієнт** | biolohiya | 8 | організм, кров, переливання, донор | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 108 | 777 | `eval_shard_002_of_005.jsonl:line_40` | **Особисті гарантії** | pravoznavstvo | 9 | гарантія, громадянин, захист, свобода | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 109 | 777 | `eval_shard_002_of_005.jsonl:line_48` | **Права людини** | pravoznavstvo | 9 | існування, розвиток | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 110 | 777 | `eval_shard_002_of_005.jsonl:line_38` | **Громадянство** | pravoznavstvo | 9 | особа, держава, обов'язок | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 111 | 777 | `eval_shard_003_of_005.jsonl:line_39` | **Природні умови** | heohrafiya | 8 | природа, участь | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 112 | 777 | `eval_shard_003_of_005.jsonl:line_8` | **Цивільне право** | pravoznavstvo | 9 | право, галузь | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 113 | 777 | `eval_shard_003_of_005.jsonl:line_20` | **Кримінальне право** | pravoznavstvo | 9 | правопорушення, право, система, норма | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 114 | 777 | `eval_shard_003_of_005.jsonl:line_50` | **Толерантність** | hromadianska | 8 | здатність, агресія, поведінка | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 115 | 777 | `eval_shard_003_of_005.jsonl:line_13` | **Коефіцієнт зволоження** | heohrafiya | 8 | коефіцієнт, зволоження, відношення, випаровуваність | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 116 | 777 | `eval_shard_004_of_005.jsonl:line_48` | **Окремі елементи орнаментів** | mystetstvo | 8 | елемент, орнамент, спіраль, риск | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 117 | 777 | `eval_shard_004_of_005.jsonl:line_39` | **Водосховища** | ukrmova | 8 | водойма, нагромадження | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 118 | 777 | `eval_shard_004_of_005.jsonl:line_38` | **Піктографічне письмо** | ukrmova | 8 | письмо, комунікація, значок, малюнок | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 119 | 777 | `eval_shard_004_of_005.jsonl:line_49` | **Інкрустація** | mystetstvo | 8 | різновид, мозаїка, оздоблення, інтер'єр | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 120 | 777 | `eval_shard_004_of_005.jsonl:line_37` | **Граматична основа** | ukrmova | 8 | обставина, туман, означення, кінь | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 121 | 777 | `eval_shard_005_of_005.jsonl:line_4` | **Смальта** | mystetstvo | 8 | скло, кубик, пластинка, мозаїка | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 122 | 777 | `eval_shard_005_of_005.jsonl:line_37` | **Базисний манікюр** | tekhnolohiyi | 8 | манікюр, процедура | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 123 | 777 | `eval_shard_005_of_005.jsonl:line_20` | **Здоровий спосіб життя** | zdorovia | 8 | відмова, їжа, дотримання, міра | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 124 | 777 | `eval_shard_005_of_005.jsonl:line_36` | **Масаж** | tekhnolohiyi | 8 | тканина, орган, рука, апарат | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 125 | 777 | `eval_shard_005_of_005.jsonl:line_8` | **Іконостас** | mystetstvo | 8 | ікона, храм, обряд, вівтар | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 126 | 777 | `sft_shard_011_of_150.jsonl:line_219` | **Глюкоза** | khimiya | 10 | продукт, обмін, речовина, організм | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 127 | 777 | `sft_shard_121_of_150.jsonl:line_74` | **Юнацький вік** | zdorovia | 9 | період, пошук, усвідомлення, суспільство | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 128 | 777 | `sft_shard_046_of_150.jsonl:line_319` | **Податкова політика** | ekonomika | 11 | політика, держава, сфера, встановлення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 129 | 777 | `sft_shard_080_of_150.jsonl:line_160` | **Окиснення** | khimiya | 9 | втрачання, електрон, частинка, речовина | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 130 | 777 | `sft_shard_053_of_150.jsonl:line_5` | **Диференціювання функції** | algebra | 10 | функція, знаходження, диференціювання | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 131 | 777 | `sft_shard_067_of_150.jsonl:line_23` | **Окиснення амоніаку з каталізатором** | khimiya | 11 | азот, окиснення, амоніак, каталізатор | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 132 | 777 | `sft_shard_110_of_150.jsonl:line_154` | **Розведення й утримання свійських тварин** | ya_doslidzhuiu_svit | 4 | розведення, утримання, тварина, праця | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 133 | 777 | `sft_shard_021_of_150.jsonl:line_120` | **Теорія ймовірностей** | algebra | 11 | теорія, ймовірність, наука, закономірність | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 134 | 777 | `sft_shard_143_of_150.jsonl:line_393` | **Бренд** | finansova | 9 | назва, панія, логотип | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 135 | 777 | `sft_shard_125_of_150.jsonl:line_122` | **Пісня і праця** | ukrmova | university | праця, скін | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 136 | 777 | `sft_shard_112_of_150.jsonl:line_216` | **Дисциплінарний батальйон** | pravoznavstvo | 11 | батальйон, режим, відбування, покарання | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 137 | 777 | `sft_shard_033_of_150.jsonl:line_290` | **Ринок** | istoriya | 9 | категорія, товаровиробник, покупець, привід | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 138 | 777 | `sft_shard_077_of_150.jsonl:line_154` | **Метрополітен** | mystetstvo | 9 | музей, бізнесмен, шанувальник, мистецтво | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 139 | 777 | `sft_shard_069_of_150.jsonl:line_370` | **Активність у шкільному житті** | hromadianska | 9 | активність, простір | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 140 | 777 | `sft_shard_106_of_150.jsonl:line_277` | **Червоні водорості** | biolohiya | 7 | водорість, організм | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 141 | 777 | `sft_shard_128_of_150.jsonl:line_131` | **Переговори та продажі** | finansova | 9 | продаж, запорука, успіх, підприємництво | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 142 | 777 | `sft_shard_034_of_150.jsonl:line_217` | **Східна елонгація** | astronomiya | 11 | елонгація, момент, положення, планета | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 143 | 777 | `sft_shard_013_of_150.jsonl:line_218` | **Дружба** | etyka | 5 | стосунок, довіра, щирість, симпатія | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 144 | 777 | `sft_shard_150_of_150.jsonl:line_399` | **Математичний горизонт** | fizyka | 11 | сфера, площина, горизонт | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 145 | 777 | `sft_shard_071_of_150.jsonl:line_368` | **Стриманість** | etyka | 5 | гамування, бажання, почуття, пристрасть | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 146 | 777 | `sft_shard_032_of_150.jsonl:line_177` | **Агресія** | istoriya | 10 | суверенітет, застосування, держава, порушення | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 147 | 777 | `sft_shard_079_of_150.jsonl:line_438` | **Світовий океан** | ya_doslidzhuiu_svit | 4 | океан, поверхня, материк | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 148 | 777 | `sft_shard_029_of_150.jsonl:line_239` | **Робочий час** | pravoznavstvo | 11 | закон, угода, підстава, працівник | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 149 | 777 | `sft_shard_113_of_150.jsonl:line_307` | **Мода** | matematyka | 11 | елемент, вибірка | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 150 | 777 | `sft_shard_060_of_150.jsonl:line_123` | **Більшість архіпелагів** | heohrafiya | 9 | більшість, архіпелаг, риф | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |

## Detailed Record Inspection (Full Text)

### Record 1 (Seed 42): Верхня палата (eval_shard_001_of_005.jsonl:line_26)
- **Subject / Grade:** vsesvitnia (Grade 8)
- **Concept:** `Верхня палата` (Citation form: ✅)
- **Scientific Terminology:** `['палата', 'сенат', 'представник', 'духовенство', 'магнат']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Верхня палата – сенат – складалася з представників вищого духовенства та магнатів, зайнятих на високих державних посадах.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 2 (Seed 42): Меркантилізм (eval_shard_001_of_005.jsonl:line_20)
- **Subject / Grade:** vsesvitnia (Grade 8)
- **Concept:** `Меркантилізм` (Citation form: ✅)
- **Scientific Terminology:** `['політика', 'втручання', 'країна', 'накопичення', 'багатство']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Меркантилізм – економічна політика, що полягає в активному втручанні державної влади в господарське життя країни з метою накопичення грошей як основного багатства держави.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 3 (Seed 42): Козацьке бароко (eval_shard_001_of_005.jsonl:line_12)
- **Subject / Grade:** istoriya (Grade 8)
- **Concept:** `Козацьке бароко` (Citation form: ✅)
- **Scientific Terminology:** `['стиль', 'земля', 'бароко']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Провідним архітектурним стилем на українських землях був стиль українського бароко , який ще називають козацьким бароко.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 4 (Seed 42): Порядок дій (eval_shard_001_of_005.jsonl:line_5)
- **Subject / Grade:** matematyka (Grade 5)
- **Concept:** `Порядок дій` (Citation form: ✅)
- **Scientific Terminology:** `['послідовність', 'виконання', 'вираз', 'результат']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Порядок дій — це така послідовність виконання арифметичних дій у виразах, щоб отримати правильний результат.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 5 (Seed 42): Держава (eval_shard_001_of_005.jsonl:line_46)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Держава` (Citation form: ✅)
- **Scientific Terminology:** `['організація', 'суспільство', 'цілісність', 'безпека', 'управління']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Держава — організація політичної влади в суспільстві, що підтримує його цілісність і безпеку та здійснює управління суспільними справами.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 6 (Seed 42): Покадрова анімація (eval_shard_002_of_005.jsonl:line_43)
- **Subject / Grade:** informatyka (Grade 7)
- **Concept:** `Покадрова анімація` (Citation form: ✅)
- **Scientific Terminology:** `['анімація', 'кадр', 'фільм']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Покадрова анімація — спосіб створення анімації, за якого художник малює кожен кадр майбутнього фільму.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 7 (Seed 42): Юридичні гарантії (eval_shard_002_of_005.jsonl:line_42)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Юридичні гарантії` (Citation form: ✅)
- **Scientific Terminology:** `['гарантія', 'захід', 'здійснення', 'охорона', 'свобода']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Юридичні гарантії — державно-правові заходи, що забезпечують здійснення та охорону права, свобод і обов'язків людини й громадянина.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 8 (Seed 42): Норма права (eval_shard_002_of_005.jsonl:line_14)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Норма права` (Citation form: ✅)
- **Scientific Terminology:** `['норма', 'поведінка', 'орган', 'держава', 'відповідальність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Норма права — загальне правило поведінки, прийняте органом держави, яке має загальнообов'язкову силу й передбачає відповідальність перед державою в разі його порушення.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 9 (Seed 42): Соціальні норми (eval_shard_002_of_005.jsonl:line_10)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Соціальні норми` (Citation form: ✅)
- **Scientific Terminology:** `['норма', 'сфера']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Соціальні норми є різними й залежать від того, ким і як вони встановлюються та яку сферу суспільного життя регулюють.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 10 (Seed 42): Правомірна поведінка (eval_shard_002_of_005.jsonl:line_20)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Правомірна поведінка` (Citation form: ✅)
- **Scientific Terminology:** `['поведінка', 'припис', 'норма', 'держава']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Правомірна поведінка — поведінка, яка відповідає приписам правових норм та охороняється державою.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 11 (Seed 42): Ґрунтовий профіль (eval_shard_003_of_005.jsonl:line_23)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Ґрунтовий профіль` (Citation form: ✅)
- **Scientific Terminology:** `['профіль', 'ґрунт', 'поверхня', 'порода']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Ґрунтовий профіль – вертикальна будова ґрунту від поверхні до материнської породи.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 12 (Seed 42): Метеочутливість (eval_shard_003_of_005.jsonl:line_19)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Метеочутливість` (Citation form: ✅)
- **Scientific Terminology:** `['організм', 'зміна']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Метеочутливість – це особливість організму людини, коли вона недостатньо добре може адаптуватися до погодних змін.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 13 (Seed 42): Атмосферний фронт (eval_shard_003_of_005.jsonl:line_11)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Атмосферний фронт` (Citation form: ✅)
- **Scientific Terminology:** `['фронт', 'зона', 'маса', 'кут', 'поверхня']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Атмосферний фронт – перехідна зона між теплими і холодними повітряними масами, яка під невеликим кутом нахилена до земної поверхні в бік холодного повітря.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 14 (Seed 42): Ожеледиця (eval_shard_003_of_005.jsonl:line_15)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Ожеледиця` (Citation form: ✅)
- **Scientific Terminology:** `['крига', 'поверхня', 'відлига', 'температура', 'повітря']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Ожеледиця – крига, що утворюється на земній поверхні після відлиги за від'ємної температури повітря, але додатної на поверхнях.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 15 (Seed 42): Адміністративне стягнення (eval_shard_003_of_005.jsonl:line_18)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Адміністративне стягнення` (Citation form: ✅)
- **Scientific Terminology:** `['стягнення', 'порушення', 'невиконання', 'заборона', 'осуд']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Адміністративне стягнення — правовий наслідок порушення або невиконання адміністративних заборон, що полягає в осуді поведінки порушника та обмеженні його особистих матеріальних благ й інших правових інтересів.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 16 (Seed 42): Інкрустація (eval_shard_004_of_005.jsonl:line_49)
- **Subject / Grade:** mystetstvo (Grade 8)
- **Concept:** `Інкрустація` (Citation form: ✅)
- **Scientific Terminology:** `['різновид', 'мозаїка', 'оздоблення', "інтер'єр", 'фасад']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Інкрустація — різновид мозаїки, оздоблення художніх виробів, інтер'єрів, фасадів будівель кольоровими шматочками твердих матеріалів.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 17 (Seed 42): Корпоративна власність (eval_shard_004_of_005.jsonl:line_29)
- **Subject / Grade:** ekonomika (Grade 10)
- **Concept:** `Корпоративна власність` (Citation form: ✅)
- **Scientific Terminology:** `['власність', 'особа', 'формування']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Корпоративна власність — власність групи осіб, однак умови її формування своєрідні.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 18 (Seed 42): Завойовницька війна (eval_shard_004_of_005.jsonl:line_6)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Завойовницька війна` (Citation form: ✅)
- **Scientific Terminology:** `['війна', 'розширення', 'сфера', 'територія', 'держава']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Завойовницька війна – війна, що ведеться для розширення власної сфери впливу на території іншої держави.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 19 (Seed 42): Право (eval_shard_004_of_005.jsonl:line_14)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Право` (Citation form: ✅)
- **Scientific Terminology:** `['взаємоповага', 'суспільство']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Право — це не просто правила, а основа, на якій будується взаємоповага і порядок у суспільстві.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 20 (Seed 42): Піктографічне письмо (eval_shard_004_of_005.jsonl:line_38)
- **Subject / Grade:** ukrmova (Grade 8)
- **Concept:** `Піктографічне письмо` (Citation form: ✅)
- **Scientific Terminology:** `['письмо', 'комунікація', 'значок', 'малюнок', 'передача']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Піктографічне письмо – це старовинний спосіб комунікації, який використовує значки або малюнки для передачі повідомлення.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 21 (Seed 42): Симфонічна поема (eval_shard_005_of_005.jsonl:line_10)
- **Subject / Grade:** mystetstvo (Grade 8)
- **Concept:** `Симфонічна поема` (Citation form: ✅)
- **Scientific Terminology:** `['поема', 'твір', 'програма']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Симфонічна поема — одночастинний симфонічний твір із літературною, історичною, філософською або живописною програмою.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 22 (Seed 42): Методи проєктування (eval_shard_005_of_005.jsonl:line_26)
- **Subject / Grade:** tekhnolohiyi (Grade 8)
- **Concept:** `Методи проєктування` (Citation form: ✅)
- **Scientific Terminology:** `['проєктування', 'дія', "об'єкт"]` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Методи проєктування — це дії, до яких вдаються в процесі проєктування для створення нового об'єкта.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 23 (Seed 42): Реалізм (eval_shard_005_of_005.jsonl:line_13)
- **Subject / Grade:** mystetstvo (Grade 8)
- **Concept:** `Реалізм` (Citation form: ✅)
- **Scientific Terminology:** `['відтворення', 'дійсність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Реалізм — художній метод, який базується на достовірному відтворенні дійсності.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 24 (Seed 42): Базисний манікюр (eval_shard_005_of_005.jsonl:line_37)
- **Subject / Grade:** tekhnolohiyi (Grade 8)
- **Concept:** `Базисний манікюр` (Citation form: ✅)
- **Scientific Terminology:** `['манікюр', 'процедура']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Базисний манікюр – це основа, тобто ті процедури, які мають бути присутні за будь-якого виду манікюру.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 25 (Seed 42): Жирність волосся (eval_shard_005_of_005.jsonl:line_35)
- **Subject / Grade:** tekhnolohiyi (Grade 8)
- **Concept:** `Жирність волосся` (Citation form: ✅)
- **Scientific Terminology:** `['жирність', 'волосся', 'результат', 'активність', 'залоза']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Жирність волосся – результат підвищеної активності сальних залоз шкіри голови.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 26 (Seed 42): Ізотермічний процес (sft_shard_057_of_150.jsonl:line_93)
- **Subject / Grade:** fizyka (Grade 10)
- **Concept:** `Ізотермічний процес` (Citation form: ✅)
- **Scientific Terminology:** `['змінювання', 'маса', 'температура']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Ізотермічний процес — процес змінювання стану даного газу деякої маси, що відбувається за незмінної температури.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 27 (Seed 42): Співчуття (sft_shard_102_of_150.jsonl:line_369)
- **Subject / Grade:** ukrmova (Grade 10)
- **Concept:** `Співчуття` (Citation form: ✅)
- **Scientific Terminology:** `['крок', 'людяність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Співчуття — перший крок до (людяність) (Угорське). 2.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 28 (Seed 42): Довжина перпендикуляра (sft_shard_106_of_150.jsonl:line_349)
- **Subject / Grade:** matematyka (Grade 10)
- **Concept:** `Довжина перпендикуляра` (Citation form: ✅)
- **Scientific Terminology:** `['площина', 'відстань', 'довжина', 'перпендикуляр']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Якщо точка не належить площині, то відстанню від точки до площини називають довжину перпендикуляра, опущеного з точки на площину.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 29 (Seed 42): Виділення окремих типів (sft_shard_078_of_150.jsonl:line_211)
- **Subject / Grade:** astronomiya (Grade 11)
- **Concept:** `Виділення окремих типів` (Citation form: ✅)
- **Scientific Terminology:** `['виділення', 'зміна', 'уявлення', 'масштаб', 'галактика']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Виділення окремих типів — лірид і віргінід — супроводжувалося змінами в наукових уявленнях щодо масштабів галактики і галактичного світу в цілому.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 30 (Seed 42): Погода (sft_shard_012_of_150.jsonl:line_460)
- **Subject / Grade:** pryroda (Grade 8)
- **Concept:** `Погода` (Citation form: ✅)
- **Scientific Terminology:** `['атмосфера', 'територія', 'проміжок']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Погода — це стан нижнього шару атмосфери на певній території Землі у той чи інший проміжок часу.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 31 (Seed 42): Ідеологія (sft_shard_003_of_150.jsonl:line_37)
- **Subject / Grade:** vsesvitnia (Grade 9)
- **Concept:** `Ідеологія` (Citation form: ✅)
- **Scientific Terminology:** `['ідея', 'переконання', 'цінність', 'бачення', 'устрій']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Ідеологія — сукупність ідей, поглядів, переконань та цінностей, які пояснюють світ, пропонують бачення бажаного суспільного устрою й визначають цілі та шляхи для колективних дій.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 32 (Seed 42): Паралельне проектування (sft_shard_091_of_150.jsonl:line_54)
- **Subject / Grade:** matematyka (Grade 10)
- **Concept:** `Паралельне проектування` (Citation form: ✅)
- **Scientific Terminology:** `['перетворення', 'фігура', 'проектування']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Описане перетворення фігури F називають паралельним проектуванням.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 33 (Seed 42): Об'єм (sft_shard_149_of_150.jsonl:line_387)
- **Subject / Grade:** matematyka (Grade 11)
- **Concept:** `Об'єм` (Citation form: ✅)
- **Scientific Terminology:** `['відповідність', 'тіло']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Об'єм — величина, що ставить у відповідність тілам у просторі невід'ємні дійсні числа.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 34 (Seed 42): Ліси (sft_shard_139_of_150.jsonl:line_384)
- **Subject / Grade:** ya_doslidzhuiu_svit (Grade 4)
- **Concept:** `Ліси` (Citation form: ✅)
- **Scientific Terminology:** `['відпочинок', 'повітря']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Ліси — це не лише джерело деревини, а й чудове місце відпочинку з чистим повітрям.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 35 (Seed 42): Лайка (sft_shard_145_of_150.jsonl:line_17)
- **Subject / Grade:** etyka (Grade 5)
- **Concept:** `Лайка` (Citation form: ✅)
- **Scientific Terminology:** `['гідність', 'неповага']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Лайка — це одна з грубих форм неповаги до людини, яка ображає людську гідність.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 36 (Seed 42): Літосферні плити (sft_shard_129_of_150.jsonl:line_255)
- **Subject / Grade:** heohrafiya (Grade 6)
- **Concept:** `Літосферні плити` (Citation form: ✅)
- **Scientific Terminology:** `['літосфера', 'розлом', 'астеносфера']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Літосферні плити — великі частини літосфери, розділені глибокими розломами, що повільно переміщуються по астеносфері.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 37 (Seed 42): Причина появи вугрів (sft_shard_002_of_150.jsonl:line_273)
- **Subject / Grade:** zdorovia (Grade 7)
- **Concept:** `Причина появи вугрів` (Citation form: ✅)
- **Scientific Terminology:** `['причина', 'поява', 'вугор', 'закупорювання', 'протока']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Причина появи вугрів — закупорювання проток сальних залоз.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 38 (Seed 42): Гроші (sft_shard_117_of_150.jsonl:line_277)
- **Subject / Grade:** finansova (Grade 9)
- **Concept:** `Гроші` (Citation form: ✅)
- **Scientific Terminology:** `['інструмент', 'їжа', 'освіта', 'відпочинок']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Гроші — це інструмент, що допомагає людині задовольнити будь-які потреби: купити їжу, одяг, оплатити освіту, відпочинок тощо.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 39 (Seed 42): Мовлення (sft_shard_116_of_150.jsonl:line_131)
- **Subject / Grade:** ukrmova (Grade 10)
- **Concept:** `Мовлення` (Citation form: ✅)
- **Scientific Terminology:** `['спілкування', 'засіб']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Мовлення — це процес спілкування, здійснюваний засобами мови.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 40 (Seed 42): Спілкування (sft_shard_015_of_150.jsonl:line_477)
- **Subject / Grade:** ukrmova (Grade 10)
- **Concept:** `Спілкування` (Citation form: ✅)
- **Scientific Terminology:** `['взаємодія', 'учасник', 'комунікація', 'реалізація']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Спілкування — умотивований живий процес взаємодії між учасниками комунікації, спрямований на реалізацію конкретної цільової настанови.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 41 (Seed 42): Кредитна історія (sft_shard_134_of_150.jsonl:line_171)
- **Subject / Grade:** finansova (Grade 9)
- **Concept:** `Кредитна історія` (Citation form: ✅)
- **Scientific Terminology:** `['кредит', 'звіт', 'позичальник', 'заборгованість']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Кредитна історія — це звіт про всі поточні та сплачені кредити позичальника, який містить інформацію, наскільки сумлінно та вчасно погашалася заборгованість. § 5.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 42 (Seed 42): Запит з параметрами (sft_shard_045_of_150.jsonl:line_255)
- **Subject / Grade:** informatyka (Grade 10)
- **Concept:** `Запит з параметрами` (Citation form: ✅)
- **Scientific Terminology:** `['запит', 'параметр', 'виконання']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Запит з параметрами — це запит, у процесі кожного виконання якого пропонується ввести деякі дані, наприклад, умову.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 43 (Seed 42): Переміщення (sft_shard_080_of_150.jsonl:line_210)
- **Subject / Grade:** heometriya (Grade 10)
- **Concept:** `Переміщення` (Citation form: ✅)
- **Scientific Terminology:** `['перетворення', 'фігура', 'рух']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Перетворення однієї фігури в іншу називають переміщенням (рухом), якщо воно зберігає відстань між точками.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 44 (Seed 42): Пейзажна лірика (sft_shard_108_of_150.jsonl:line_314)
- **Subject / Grade:** zarlit (Grade 5)
- **Concept:** `Пейзажна лірика` (Citation form: ✅)
- **Scientific Terminology:** `['лірика', 'зображення', 'природа']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Пейзажна лірика – віршовані твори, присвячені зображенню природи.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 45 (Seed 42): Посадова особа місцевого самоврядування (sft_shard_127_of_150.jsonl:line_141)
- **Subject / Grade:** pravoznavstvo (Grade 11)
- **Concept:** `Посадова особа місцевого самоврядування` (Citation form: ✅)
- **Scientific Terminology:** `['особа', 'самоврядування', 'орган', 'повноваження', 'здійснення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Посадова особа місцевого самоврядування — це особа, яка працює в органах місцевого самоврядування, має відповідні посадові повноваження щодо здійснення організаційно-розпорядчих і консультативнодорадчих функцій та отримує заробітну плату за рахунок місцевого бюджету.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 46 (Seed 42): Кастинг (sft_shard_042_of_150.jsonl:line_451)
- **Subject / Grade:** mystetstvo (Grade 7)
- **Concept:** `Кастинг` (Citation form: ✅)
- **Scientific Terminology:** `['визначення', 'виконавець', 'кіно', 'театр', 'телебачення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Кастинг — визначення складу виконавців для кіно, театру, телебачення, модельного бізнесу за конкурсом.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 47 (Seed 42): Амортизація (sft_shard_107_of_150.jsonl:line_75)
- **Subject / Grade:** ekonomika (Grade 11)
- **Concept:** `Амортизація` (Citation form: ✅)
- **Scientific Terminology:** `['перенесення', 'вартість', 'засіб', 'продукція', 'відшкодування']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Амортизація — це перенесення вартості основних засобів на вартість готової продукції, з метою відшкодування їх зношеної частини.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 48 (Seed 42): Дружба (sft_shard_056_of_150.jsonl:line_289)
- **Subject / Grade:** etyka (Grade 5)
- **Concept:** `Дружба` (Citation form: ✅)
- **Scientific Terminology:** `['стосунок', 'довіра', 'щирість', 'симпатія', 'інтерес']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Дружба — безкорисливі стосунки між людьми, що засновані на довірі, щирості, взаємних симпатіях, спільних інтересах, захопленнях.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 49 (Seed 42): Міфологізм (sft_shard_010_of_150.jsonl:line_201)
- **Subject / Grade:** ukrlit (Grade 11)
- **Concept:** `Міфологізм` (Citation form: ✅)
- **Scientific Terminology:** `['реалізація', 'твір', 'література']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Міфологізм — спосіб поетичної реалізації міфу у творах оригінальної літератури.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 50 (Seed 42): Відкритий перелом (sft_shard_131_of_150.jsonl:line_432)
- **Subject / Grade:** zakhyst (Grade 11)
- **Concept:** `Відкритий перелом` (Citation form: ✅)
- **Scientific Terminology:** `['перелом', 'пошкодження', 'цілісність', 'кістка', 'покрив']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Відкритий перелом — це пошкодження цілісності кістки з одночасним пошкодженням шкірних покривів (появою рани або декількох ран) у ділянці перелому.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 51 (Seed 123): Форма держави (eval_shard_001_of_005.jsonl:line_48)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Форма держави` (Citation form: ✅)
- **Scientific Terminology:** `['держава', 'організація', 'структура', 'орган', 'здійснення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Форма держави — спосіб організації структури держави та її органів, а також спосіб здійснення державної влади, що виражається у формі правління, формі державного устрою і політичному режимі.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 52 (Seed 123): Коефіцієнт корисної дії (eval_shard_001_of_005.jsonl:line_19)
- **Subject / Grade:** fizyka (Grade 8)
- **Concept:** `Коефіцієнт корисної дії` (Citation form: ✅)
- **Scientific Terminology:** `['механізм', 'коефіцієнт', 'дія']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Яку частину повної роботи механізм перетворює на корисну, показує фізична величина, яку називають коефіцієнт корисної дії (ККД).» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 53 (Seed 123): Верхня палата (eval_shard_001_of_005.jsonl:line_26)
- **Subject / Grade:** vsesvitnia (Grade 8)
- **Concept:** `Верхня палата` (Citation form: ✅)
- **Scientific Terminology:** `['палата', 'сенат', 'представник', 'духовенство', 'магнат']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Верхня палата – сенат – складалася з представників вищого духовенства та магнатів, зайнятих на високих державних посадах.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 54 (Seed 123): Ізотоп (eval_shard_001_of_005.jsonl:line_41)
- **Subject / Grade:** khimiya (Grade 8)
- **Concept:** `Ізотоп` (Citation form: ✅)
- **Scientific Terminology:** `['нуклід', 'заряд', 'ядро']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Усі нукліди, що мають однаковий заряд ядра (протонне число) й різне нейтронне число, називають ізотопами.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 55 (Seed 123): Держава (eval_shard_001_of_005.jsonl:line_46)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Держава` (Citation form: ✅)
- **Scientific Terminology:** `['організація', 'суспільство', 'цілісність', 'безпека', 'управління']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Держава — організація політичної влади в суспільстві, що підтримує його цілісність і безпеку та здійснює управління суспільними справами.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 56 (Seed 123): Орган (eval_shard_002_of_005.jsonl:line_7)
- **Subject / Grade:** biolohiya (Grade 8)
- **Concept:** `Орган` (Citation form: ✅)
- **Scientific Terminology:** `['тканина', 'складник', 'організм', 'функція']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Орган — це складник організму, який має визначену форму й будову, утворений різними тканинами, які взаємодіють між собою, розташований у певній його частині та виконує одну або кілька функцій.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 57 (Seed 123): Юридична відповідальність (eval_shard_002_of_005.jsonl:line_30)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Юридична відповідальність` (Citation form: ✅)
- **Scientific Terminology:** `['правопорушення', 'відповідальність', 'застосування', 'особа', 'захід']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Юридична відповідальність — застосування до винної особи заходів державного примусу за вчинене нею правопорушення.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 58 (Seed 123): Правомірна поведінка (eval_shard_002_of_005.jsonl:line_20)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Правомірна поведінка` (Citation form: ✅)
- **Scientific Terminology:** `['поведінка', 'припис', 'норма', 'держава']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Правомірна поведінка — поведінка, яка відповідає приписам правових норм та охороняється державою.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 59 (Seed 123): Дитяча конституція (eval_shard_002_of_005.jsonl:line_50)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Дитяча конституція` (Citation form: ✅)
- **Scientific Terminology:** `['конвенція', 'дитина', 'конституція']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Конвенцію про права дитини називають дитячою конституцією.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 60 (Seed 123): Покадрова анімація (eval_shard_002_of_005.jsonl:line_43)
- **Subject / Grade:** informatyka (Grade 7)
- **Concept:** `Покадрова анімація` (Citation form: ✅)
- **Scientific Terminology:** `['анімація', 'кадр', 'фільм']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Покадрова анімація — спосіб створення анімації, за якого художник малює кожен кадр майбутнього фільму.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 61 (Seed 123): Геологічна ера (eval_shard_003_of_005.jsonl:line_5)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Геологічна ера` (Citation form: ✅)
- **Scientific Terminology:** `['підрозділ', 'шкала', 'утворення', 'порода']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Геологічна ера є підрозділом геохронологічної шкали, що відповідає часові утворення певної групи гірських порід.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 62 (Seed 123): Здібності (eval_shard_003_of_005.jsonl:line_42)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Здібності` (Citation form: ✅)
- **Scientific Terminology:** `['схильність', 'виконання']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Здібності – це індивідуальні особливості, які визначають схильність до виконання певної діяльності.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 63 (Seed 123): Цивільне право (eval_shard_003_of_005.jsonl:line_8)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Цивільне право` (Citation form: ✅)
- **Scientific Terminology:** `['право', 'галузь']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Цивільне право — галузь права, що регулює майнові та особисті немайнові правові відносини.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 64 (Seed 123): Звичаї (eval_shard_003_of_005.jsonl:line_28)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Звичаї` (Citation form: ✅)
- **Scientific Terminology:** `['побут', 'народ', 'колектив']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Звичаї – це загальноприйняті правила, які здавна існують у громадському житті й побуті народу, суспільної групи, колективу. 10 Традиція – це культурна спадщина, яка передається від покоління до покоління.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 65 (Seed 123): Позов (eval_shard_003_of_005.jsonl:line_6)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Позов` (Citation form: ✅)
- **Scientific Terminology:** `['закон', 'звернення', 'особа', 'суд', 'прохання']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Позов — звернення особи до суду з проханням про розгляд спору та захист її прав, що охороняються законом.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 66 (Seed 123): Властивість речовин (eval_shard_004_of_005.jsonl:line_9)
- **Subject / Grade:** pryroda (Grade 5)
- **Concept:** `Властивість речовин` (Citation form: ✅)
- **Scientific Terminology:** `['розпізнавання', 'опис', 'речовина']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Ознаки, які використовують для розпізнавання та опису речовин, називають властивостями речовин.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 67 (Seed 123): Благо (eval_shard_004_of_005.jsonl:line_28)
- **Subject / Grade:** ekonomika (Grade 10)
- **Concept:** `Благо` (Citation form: ✅)
- **Scientific Terminology:** `['засіб', 'задоволення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Благо — це будь-який засіб, що використовують для задоволення потреб.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 68 (Seed 123): Інкрустація (eval_shard_004_of_005.jsonl:line_49)
- **Subject / Grade:** mystetstvo (Grade 8)
- **Concept:** `Інкрустація` (Citation form: ✅)
- **Scientific Terminology:** `['різновид', 'мозаїка', 'оздоблення', "інтер'єр", 'фасад']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Інкрустація — різновид мозаїки, оздоблення художніх виробів, інтер'єрів, фасадів будівель кольоровими шматочками твердих матеріалів.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 69 (Seed 123): Географічний простір (eval_shard_004_of_005.jsonl:line_3)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Географічний простір` (Citation form: ✅)
- **Scientific Terminology:** `['простір', "об'єкт", 'територія']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Географічний простір – сукупність зв'язків між різними географічними об'єктами, які розміщені на конкретній території і розвиваються у просторі й часі.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 70 (Seed 123): Виверження вулкана (eval_shard_004_of_005.jsonl:line_46)
- **Subject / Grade:** zarlit (Grade 8)
- **Concept:** `Виверження вулкана` (Citation form: ✅)
- **Scientific Terminology:** `['виверження', 'вулкан', 'комин', 'сажа']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Виверження вулкана – усе одно, що пожежа в комині, як там загориться сажа.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 71 (Seed 123): Авторитет (eval_shard_005_of_005.jsonl:line_51)
- **Subject / Grade:** etyka (Grade 6)
- **Concept:** `Авторитет` (Citation form: ✅)
- **Scientific Terminology:** `['переконання', 'поведінка', 'особа', 'організація']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Авторитет — загальновизнаний вплив, який здійснюють на переконання та поведінку людей інші особи або організації.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 72 (Seed 123): Симфонічна поема (eval_shard_005_of_005.jsonl:line_10)
- **Subject / Grade:** mystetstvo (Grade 8)
- **Concept:** `Симфонічна поема` (Citation form: ✅)
- **Scientific Terminology:** `['поема', 'твір', 'програма']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Симфонічна поема — одночастинний симфонічний твір із літературною, історичною, філософською або живописною програмою.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 73 (Seed 123): Робот (eval_shard_005_of_005.jsonl:line_31)
- **Subject / Grade:** tekhnolohiyi (Grade 8)
- **Concept:** `Робот` (Citation form: ✅)
- **Scientific Terminology:** `['пристрій', "комп'ютер", 'виконання', 'операція']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Робот — пристрій, який керований за допомогою електронної плати або комп'ютера і який можна запрограмувати на виконання певних операцій.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 74 (Seed 123): Європейський карвінг (eval_shard_005_of_005.jsonl:line_38)
- **Subject / Grade:** tekhnolohiyi (Grade 8)
- **Concept:** `Європейський карвінг` (Citation form: ✅)
- **Scientific Terminology:** `['карвінг', 'різьблення', 'овоч', 'фрукт', 'редька']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Європейський карвінг — це різьблення по овочах і фруктах, які ростуть у Європі: редьці, редисці, буряках, моркві, болгарських і гострих перцях, кабачках, гарбузах, баклажанах, цибулі, капусті.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 75 (Seed 123): Гімн (eval_shard_005_of_005.jsonl:line_2)
- **Subject / Grade:** mystetstvo (Grade 8)
- **Concept:** `Гімн` (Citation form: ✅)
- **Scientific Terminology:** `['характер', 'прославлення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Гімн — пісня урочистого характеру для прославлення божества.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 76 (Seed 123): Захист населення в надзвичайних ситуаціях (sft_shard_071_of_150.jsonl:line_492)
- **Subject / Grade:** zakhyst (Grade 10)
- **Concept:** `Захист населення в надзвичайних ситуаціях` (Citation form: ✅)
- **Scientific Terminology:** `['захист', 'населення', 'ситуація', 'комплекс', 'захід']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Захист населення в надзвичайних ситуаціях — це комплекс заходів, спрямованих на запобігання негативному впливу наслідків НС чи максимальне послаблення ступеня їх негативного впливу.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 77 (Seed 123): Участь в управлінні державними справами (sft_shard_100_of_150.jsonl:line_148)
- **Subject / Grade:** hromadianska (Grade 9)
- **Concept:** `Участь в управлінні державними справами` (Citation form: ✅)
- **Scientific Terminology:** `['участь', 'управління', 'громадянин', 'контроль', 'ухвалення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Участь в управлінні державними справами — це активна діяльність громадян, спрямована на вплив і контроль над ухваленням рішень у державі.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 78 (Seed 123): Вибори (sft_shard_072_of_150.jsonl:line_409)
- **Subject / Grade:** hromadianska (Grade 9)
- **Concept:** `Вибори` (Citation form: ✅)
- **Scientific Terminology:** `['волевиявлення', 'здійснення', 'народ']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Вибори — це основна форма народного волевиявлення, спосіб безпосереднього здійснення влади українським народом.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 79 (Seed 123): Давня шумерська глиняна табличка (sft_shard_051_of_150.jsonl:line_137)
- **Subject / Grade:** istoriya (Grade 7)
- **Concept:** `Давня шумерська глиняна табличка` (Citation form: ✅)
- **Scientific Terminology:** `['табличка', 'угода']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Давня шумерська глиняна табличка — торговельна угода, приблизно 2600 років до нашої ери.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 80 (Seed 123): Явища природи (sft_shard_010_of_150.jsonl:line_100)
- **Subject / Grade:** ya_doslidzhuiu_svit (Grade 3)
- **Concept:** `Явища природи` (Citation form: ✅)
- **Scientific Terminology:** `['природа', 'тіло']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Явища природи — це зміни, які відбуваються з тілами неживої та живої природи.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 81 (Seed 123): Витрати (sft_shard_116_of_150.jsonl:line_128)
- **Subject / Grade:** tekhnolohiyi (Grade 6)
- **Concept:** `Витрати` (Citation form: ✅)
- **Scientific Terminology:** `['обсяг', 'ресурс', 'проміжок']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Витрати — обсяг ресурсів, використаних у процесі господарської діяльності за певний проміжок часу.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 82 (Seed 123): Реліктове випромінювання (sft_shard_128_of_150.jsonl:line_400)
- **Subject / Grade:** astronomiya (Grade 11)
- **Concept:** `Реліктове випромінювання` (Citation form: ✅)
- **Scientific Terminology:** `['випромінювання', 'квант', 'млрд']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Реліктове випромінювання — кванти світла, що утворилися 15 млрд років тому.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 83 (Seed 123): Пожежі (sft_shard_106_of_150.jsonl:line_283)
- **Subject / Grade:** zakhyst (Grade 11)
- **Concept:** `Пожежі` (Citation form: ✅)
- **Scientific Terminology:** `['поширення', 'дія', 'вогонь', 'контроль']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Пожежі — стихійне поширення нищівної дії вогню, який виходить з-під контролю людини.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 84 (Seed 123): Сила (sft_shard_125_of_150.jsonl:line_424)
- **Subject / Grade:** pryroda (Grade 8)
- **Concept:** `Сила` (Citation form: ✅)
- **Scientific Terminology:** `['міра', 'взаємодія', 'тіло']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Сила — це фізична величина, яка є мірою взаємодії двох тіл.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 85 (Seed 123): Національна мова (sft_shard_075_of_150.jsonl:line_288)
- **Subject / Grade:** ukrmova (Grade university)
- **Concept:** `Національна мова` (Citation form: ✅)
- **Scientific Terminology:** `['продукт', 'покоління', 'народ', 'розвиток']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Національна мова – продукт творчої та інтелектуальної діяльності багатьох поколінь одного народу, яка триває впродовж усього часу його історичного розвитку.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 86 (Seed 123): Середня швидкість нерівномірного руху тіла (sft_shard_040_of_150.jsonl:line_240)
- **Subject / Grade:** pryroda (Grade 8)
- **Concept:** `Середня швидкість нерівномірного руху тіла` (Citation form: ✅)
- **Scientific Terminology:** `['швидкість', 'рух', 'тіло', 'відношення', 'інтервал']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Середня швидкість нерівномірного руху тіла — це фізична величина, що дорівнює відношенню всього шляху l, який подолало тіло, до інтервалу часу t, за який цей шлях подолано.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 87 (Seed 123): Будівництво каналів і дамб (sft_shard_140_of_150.jsonl:line_160)
- **Subject / Grade:** istoriya (Grade 6)
- **Concept:** `Будівництво каналів і дамб` (Citation form: ✅)
- **Scientific Terminology:** `['будівництво', 'канал', 'дамба', 'річка']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Будівництво каналів і дамб — важка справа, до того ж щороку їх необхідно було відновлювати після розливів річки.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 88 (Seed 123): Крапка в центрі кола (sft_shard_022_of_150.jsonl:line_370)
- **Subject / Grade:** zdorovia (Grade 9)
- **Concept:** `Крапка в центрі кола` (Citation form: ✅)
- **Scientific Terminology:** `['крапка', 'центр', 'кіл', 'відлік', 'нуль']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Крапка в центрі кола — це точка відліку, нуль, початок.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 89 (Seed 123): Продовольчий кошик (sft_shard_079_of_150.jsonl:line_8)
- **Subject / Grade:** tekhnolohiyi (Grade 5)
- **Concept:** `Продовольчий кошик` (Citation form: ✅)
- **Scientific Terminology:** `['набір', 'продукт', 'харчування']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Продовольчий кошик — набір продуктів харчування, що входить до споживчого кошика.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 90 (Seed 123): Дискримінація (sft_shard_094_of_150.jsonl:line_86)
- **Subject / Grade:** zdorovia (Grade 7)
- **Concept:** `Дискримінація` (Citation form: ✅)
- **Scientific Terminology:** `['обмеження', 'громадянин', 'право', 'вік']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Дискримінація — це обмеження громадян у правах за певною ознакою: расовою, релігійною, статевою, за віком тощо.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 91 (Seed 123): Висота циліндра (sft_shard_124_of_150.jsonl:line_482)
- **Subject / Grade:** matematyka (Grade 11)
- **Concept:** `Висота циліндра` (Citation form: ✅)
- **Scientific Terminology:** `['висота', 'циліндр', 'перпендикуляр']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Висотою циліндра називається перпендикуляр, проведений із будь-якої точки однієї основи на іншу.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 92 (Seed 123): Чистий дохід підприємства (sft_shard_025_of_150.jsonl:line_493)
- **Subject / Grade:** ekonomika (Grade 11)
- **Concept:** `Чистий дохід підприємства` (Citation form: ✅)
- **Scientific Terminology:** `['дохід', 'підприємство']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Чистий дохід підприємства — це прибуток підприємства.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 93 (Seed 123): Обчислювальна геометрія (sft_shard_087_of_150.jsonl:line_9)
- **Subject / Grade:** informatyka (Grade 11)
- **Concept:** `Обчислювальна геометрія` (Citation form: ✅)
- **Scientific Terminology:** `['алгоритм', 'геометрія', 'галузь', 'наука', 'вивчення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Обчислювальна геометрія — це галузь комп'ютерних наук, присвячена вивченню алгоритмів розв'язування геометричних задач.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 94 (Seed 123): Фінансові послуги (sft_shard_084_of_150.jsonl:line_373)
- **Subject / Grade:** heohrafiya (Grade 9)
- **Concept:** `Фінансові послуги` (Citation form: ✅)
- **Scientific Terminology:** `['послуга', 'економіка', 'знання', 'сфера']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Фінансові послуги – технологічЯпонська економіка знань но модерна й стабільна сфера.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 95 (Seed 123): Народження проєкту (sft_shard_012_of_150.jsonl:line_226)
- **Subject / Grade:** tekhnolohiyi (Grade 9)
- **Concept:** `Народження проєкту` (Citation form: ✅)
- **Scientific Terminology:** `['народження', 'проєкт', 'визначення', 'проблема', 'формулювання']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Народження проєкту – це визначення проблеми, над якою ми плануємо працювати, формулювання мети й очікуваного результату проєкту, планування наших дій.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 96 (Seed 123): Майданник (sft_shard_103_of_150.jsonl:line_21)
- **Subject / Grade:** ukrmova (Grade 4)
- **Concept:** `Майданник` (Citation form: ✅)
- **Scientific Terminology:** `['добування', 'вугілля', 'дерево']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Майданник — смоляр, той, хто займається добуванням смоли та вугілля з деревини хвойних дерев.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 97 (Seed 123): Колообіг води (sft_shard_138_of_150.jsonl:line_55)
- **Subject / Grade:** ya_doslidzhuiu_svit (Grade 3)
- **Concept:** `Колообіг води` (Citation form: ✅)
- **Scientific Terminology:** `['природа', 'колообіг', 'перетворення', 'переміщення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Колообіг води — це перетворення води з одного стану в інший і переміщення її в природі.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 98 (Seed 123): Видатки державного бюджету (sft_shard_021_of_150.jsonl:line_482)
- **Subject / Grade:** pravoznavstvo (Grade 11)
- **Concept:** `Видатки державного бюджету` (Citation form: ✅)
- **Scientific Terminology:** `['закон', 'видаток', 'бюджет', 'кошт', 'здійснення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Видатки державного бюджету — це кошти, які спрямовують на здійснення програм і заходів, що передбачені законом про бюджет на поточний рік.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 99 (Seed 123): Золотаве волосся (sft_shard_031_of_150.jsonl:line_480)
- **Subject / Grade:** zarlit (Grade 11)
- **Concept:** `Золотаве волосся` (Citation form: ✅)
- **Scientific Terminology:** `['волосся', 'традиція', 'елемент']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Золотаве волосся — це усталений у німецькій фольклорній та літературній традиції елемент жіночої краси.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 100 (Seed 123): Гривня (sft_shard_041_of_150.jsonl:line_387)
- **Subject / Grade:** ya_doslidzhuiu_svit (Grade 4)
- **Concept:** `Гривня` (Citation form: ✅)
- **Scientific Terminology:** `['одиниця', 'символ', 'кода']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Гривня — це офіційна грошова одиниця України, її символ — ₴, код — UAН.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 101 (Seed 777): Козацьке бароко (eval_shard_001_of_005.jsonl:line_12)
- **Subject / Grade:** istoriya (Grade 8)
- **Concept:** `Козацьке бароко` (Citation form: ✅)
- **Scientific Terminology:** `['стиль', 'земля', 'бароко']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Провідним архітектурним стилем на українських землях був стиль українського бароко , який ще називають козацьким бароко.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 102 (Seed 777): Орбіталь (eval_shard_001_of_005.jsonl:line_43)
- **Subject / Grade:** khimiya (Grade 8)
- **Concept:** `Орбіталь` (Citation form: ✅)
- **Scientific Terminology:** `['ймовірність', 'перебування', 'електрон']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Орбіталь — це частина простору, у якому ймовірність перебування електрона вища за 90 %.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 103 (Seed 777): Буржуазія (eval_shard_001_of_005.jsonl:line_16)
- **Subject / Grade:** vsesvitnia (Grade 8)
- **Concept:** `Буржуазія` (Citation form: ✅)
- **Scientific Terminology:** `['верства', 'власник', 'капітал', 'засіб', 'виробництво']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Буржуазія – суспільна верства, до якої належали власники капіталу та засобів виробництва. заробітну плату.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 104 (Seed 777): Електричне поле (eval_shard_001_of_005.jsonl:line_31)
- **Subject / Grade:** fizyka (Grade 8)
- **Concept:** `Електричне поле` (Citation form: ✅)
- **Scientific Terminology:** `['матерія', 'тіло', 'частинка', 'заряд']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Електричне поле — це особливий вид матерії, що існує навколо заряджених тіл або частинок і діє з певною силою на інші тіла або частинки, які мають електричний заряд.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 105 (Seed 777): Парламентська монархія (eval_shard_001_of_005.jsonl:line_38)
- **Subject / Grade:** vsesvitnia (Grade 8)
- **Concept:** `Парламентська монархія` (Citation form: ✅)
- **Scientific Terminology:** `['монархія', 'правління', 'монарх', 'повноваження', 'парламент']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Парламентська монархія – форма правління, за якої влада монарха обмежена повноваженнями парламенту.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 106 (Seed 777): Біженець (eval_shard_002_of_005.jsonl:line_46)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Біженець` (Citation form: ✅)
- **Scientific Terminology:** `['особа', 'громадянин', 'причина', 'країна', 'захист']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Біженець — особа, яка не є громадянином України і внаслідок певних причин перебуває за межами своєї країни та не може користуватися її захистом.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 107 (Seed 777): Реципієнт (eval_shard_002_of_005.jsonl:line_23)
- **Subject / Grade:** biolohiya (Grade 8)
- **Concept:** `Реципієнт` (Citation form: ✅)
- **Scientific Terminology:** `['організм', 'кров', 'переливання', 'донор']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Організм, до якого переливають кров, називають реципієнтом, а організм, чию кров використовують для переливання, — донором.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 108 (Seed 777): Особисті гарантії (eval_shard_002_of_005.jsonl:line_40)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Особисті гарантії` (Citation form: ✅)
- **Scientific Terminology:** `['гарантія', 'громадянин', 'захист', 'свобода', 'інтерес']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Особисті гарантії — власні можливості людини й громадянина щодо захисту своїх прав, свобод, законних інтересів та обов'язків.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 109 (Seed 777): Права людини (eval_shard_002_of_005.jsonl:line_48)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Права людини` (Citation form: ✅)
- **Scientific Terminology:** `['існування', 'розвиток']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Права людини — можливості, необхідні людині для існування та розвитку.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 110 (Seed 777): Громадянство (eval_shard_002_of_005.jsonl:line_38)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Громадянство` (Citation form: ✅)
- **Scientific Terminology:** `['особа', 'держава', "обов'язок"]` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Громадянство — юридично визначений, стійкий, необмежений у просторі правовий зв'язок між особою та певною державою, що визначає їхні взаємні права й обов'язки.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 111 (Seed 777): Природні умови (eval_shard_003_of_005.jsonl:line_39)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Природні умови` (Citation form: ✅)
- **Scientific Terminology:** `['природа', 'участь']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Природні умови – складові і властивості природи Землі, що впливають на життя та діяльність людства, але не беруть безпосередньої участі в них.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 112 (Seed 777): Цивільне право (eval_shard_003_of_005.jsonl:line_8)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Цивільне право` (Citation form: ✅)
- **Scientific Terminology:** `['право', 'галузь']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Цивільне право — галузь права, що регулює майнові та особисті немайнові правові відносини.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 113 (Seed 777): Кримінальне право (eval_shard_003_of_005.jsonl:line_20)
- **Subject / Grade:** pravoznavstvo (Grade 9)
- **Concept:** `Кримінальне право` (Citation form: ✅)
- **Scientific Terminology:** `['правопорушення', 'право', 'система', 'норма', 'діяння']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Кримінальне право — система юридичних норм, що встановлюють, які суспільно небезпечні діяння є кримінальними правопорушеннями та які покарання передбачені за їх вчинення.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 114 (Seed 777): Толерантність (eval_shard_003_of_005.jsonl:line_50)
- **Subject / Grade:** hromadianska (Grade 8)
- **Concept:** `Толерантність` (Citation form: ✅)
- **Scientific Terminology:** `['здатність', 'агресія', 'поведінка']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Толерантність – це здатність взаємодіяти з людьми іншої культури, іншого способу життя; без агресії сприймати думки, які відрізняються від власних, а також поважати особливості поведінки та способу життя інших.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 115 (Seed 777): Коефіцієнт зволоження (eval_shard_003_of_005.jsonl:line_13)
- **Subject / Grade:** heohrafiya (Grade 8)
- **Concept:** `Коефіцієнт зволоження` (Citation form: ✅)
- **Scientific Terminology:** `['коефіцієнт', 'зволоження', 'відношення', 'випаровуваність', 'період']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Коефіцієнт зволоження – відношення кількості опадів до величини випаровуваності за певний період.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 116 (Seed 777): Окремі елементи орнаментів (eval_shard_004_of_005.jsonl:line_48)
- **Subject / Grade:** mystetstvo (Grade 8)
- **Concept:** `Окремі елементи орнаментів` (Citation form: ✅)
- **Scientific Terminology:** `['елемент', 'орнамент', 'спіраль', 'риск', 'овал']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Окремі елементи орнаментів — плавні хвилеподібні лінії, заокруглені форми, спіралі, горизонтальні, діагональні риски, овали, ромби, хрести, меандри — утворюють дивовижне враження єдиного безкінечного руху.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 117 (Seed 777): Водосховища (eval_shard_004_of_005.jsonl:line_39)
- **Subject / Grade:** ukrmova (Grade 8)
- **Concept:** `Водосховища` (Citation form: ✅)
- **Scientific Terminology:** `['водойма', 'нагромадження']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Водосховища – це великі штучні водойми, які створено для нагромадження води й подальшого її використання протягом року.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 118 (Seed 777): Піктографічне письмо (eval_shard_004_of_005.jsonl:line_38)
- **Subject / Grade:** ukrmova (Grade 8)
- **Concept:** `Піктографічне письмо` (Citation form: ✅)
- **Scientific Terminology:** `['письмо', 'комунікація', 'значок', 'малюнок', 'передача']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Піктографічне письмо – це старовинний спосіб комунікації, який використовує значки або малюнки для передачі повідомлення.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 119 (Seed 777): Інкрустація (eval_shard_004_of_005.jsonl:line_49)
- **Subject / Grade:** mystetstvo (Grade 8)
- **Concept:** `Інкрустація` (Citation form: ✅)
- **Scientific Terminology:** `['різновид', 'мозаїка', 'оздоблення', "інтер'єр", 'фасад']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Інкрустація — різновид мозаїки, оздоблення художніх виробів, інтер'єрів, фасадів будівель кольоровими шматочками твердих матеріалів.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 120 (Seed 777): Граматична основа (eval_shard_004_of_005.jsonl:line_37)
- **Subject / Grade:** ukrmova (Grade 8)
- **Concept:** `Граматична основа` (Citation form: ✅)
- **Scientific Terminology:** `['обставина', 'туман', 'означення', 'кінь']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Граматична основа – слід розтанув; другорядні члени: обставина – у тумані, означення – коней, диких.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 121 (Seed 777): Смальта (eval_shard_005_of_005.jsonl:line_4)
- **Subject / Grade:** mystetstvo (Grade 8)
- **Concept:** `Смальта` (Citation form: ✅)
- **Scientific Terminology:** `['скло', 'кубик', 'пластинка', 'мозаїка']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Смальта — кольорове напівпрозоре скло у вигляді кубиків або пластинок, призначене для створення мозаїк.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 122 (Seed 777): Базисний манікюр (eval_shard_005_of_005.jsonl:line_37)
- **Subject / Grade:** tekhnolohiyi (Grade 8)
- **Concept:** `Базисний манікюр` (Citation form: ✅)
- **Scientific Terminology:** `['манікюр', 'процедура']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Базисний манікюр – це основа, тобто ті процедури, які мають бути присутні за будь-якого виду манікюру.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 123 (Seed 777): Здоровий спосіб життя (eval_shard_005_of_005.jsonl:line_20)
- **Subject / Grade:** zdorovia (Grade 8)
- **Concept:** `Здоровий спосіб життя` (Citation form: ✅)
- **Scientific Terminology:** `['відмова', 'їжа', 'дотримання', 'міра', 'харчування']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Здоровий спосіб життя — це не відмова від смачної калорійної їжі, а дотримання міри в харчуванні та підтримання достатньої рухової активності.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 124 (Seed 777): Масаж (eval_shard_005_of_005.jsonl:line_36)
- **Subject / Grade:** tekhnolohiyi (Grade 8)
- **Concept:** `Масаж` (Citation form: ✅)
- **Scientific Terminology:** `['тканина', 'орган', 'рука', 'апарат']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Масаж — метод механічного дозованого і рефлекторного впливу на тканини й органи людини руками або спеціальними апаратами.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 125 (Seed 777): Іконостас (eval_shard_005_of_005.jsonl:line_8)
- **Subject / Grade:** mystetstvo (Grade 8)
- **Concept:** `Іконостас` (Citation form: ✅)
- **Scientific Terminology:** `['ікона', 'храм', 'обряд', 'вівтар', 'церква']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Іконостас — стіна з ікон у християнському храмі східного обряду, яка відокремлює вівтар від центральної частини церкви.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 126 (Seed 777): Глюкоза (sft_shard_011_of_150.jsonl:line_219)
- **Subject / Grade:** khimiya (Grade 10)
- **Concept:** `Глюкоза` (Citation form: ✅)
- **Scientific Terminology:** `['продукт', 'обмін', 'речовина', 'організм']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Глюкоза — один з основних продуктів обміну речовин у живих організмах.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 127 (Seed 777): Юнацький вік (sft_shard_121_of_150.jsonl:line_74)
- **Subject / Grade:** zdorovia (Grade 9)
- **Concept:** `Юнацький вік` (Citation form: ✅)
- **Scientific Terminology:** `['період', 'пошук', 'усвідомлення', 'суспільство', "з'ясування"]` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Юнацький вік — період активного пошуку й усвідомлення свого місця в суспільстві, з'ясування життєвих цілей, ідеалів і життєвого кредо.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 128 (Seed 777): Податкова політика (sft_shard_046_of_150.jsonl:line_319)
- **Subject / Grade:** ekonomika (Grade 11)
- **Concept:** `Податкова політика` (Citation form: ✅)
- **Scientific Terminology:** `['політика', 'держава', 'сфера', 'встановлення', 'регламентування']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Податкова політика — це діяльність держави в сфері встановлення, правового регламентування та організації справляння податків і податкових платежів у централізовані фонди грошових ресурсів держави.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 129 (Seed 777): Окиснення (sft_shard_080_of_150.jsonl:line_160)
- **Subject / Grade:** khimiya (Grade 9)
- **Concept:** `Окиснення` (Citation form: ✅)
- **Scientific Terminology:** `['втрачання', 'електрон', 'частинка', 'речовина', 'відновлення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Окиснення — процес втрачання електронів частинкою речовини, а відновлення — процес приєднання нею електронів.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 130 (Seed 777): Диференціювання функції (sft_shard_053_of_150.jsonl:line_5)
- **Subject / Grade:** algebra (Grade 10)
- **Concept:** `Диференціювання функції` (Citation form: ✅)
- **Scientific Terminology:** `['функція', 'знаходження', 'диференціювання']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Дію знаходження похідної називають диференціюванням функції.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 131 (Seed 777): Окиснення амоніаку з каталізатором (sft_shard_067_of_150.jsonl:line_23)
- **Subject / Grade:** khimiya (Grade 11)
- **Concept:** `Окиснення амоніаку з каталізатором` (Citation form: ✅)
- **Scientific Terminology:** `['азот', 'окиснення', 'амоніак', 'каталізатор', 'стадія']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Окиснення амоніаку з каталізатором — промислово важлива стадія процесу фіксації атмосферного азоту і нітрифікації ґрунтів.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 132 (Seed 777): Розведення й утримання свійських тварин (sft_shard_110_of_150.jsonl:line_154)
- **Subject / Grade:** ya_doslidzhuiu_svit (Grade 4)
- **Concept:** `Розведення й утримання свійських тварин` (Citation form: ✅)
- **Scientific Terminology:** `['розведення', 'утримання', 'тварина', 'праця']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Розведення й утримання свійських тварин — це клопітка, але необхідна для людей праця.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 133 (Seed 777): Теорія ймовірностей (sft_shard_021_of_150.jsonl:line_120)
- **Subject / Grade:** algebra (Grade 11)
- **Concept:** `Теорія ймовірностей` (Citation form: ✅)
- **Scientific Terminology:** `['теорія', 'ймовірність', 'наука', 'закономірність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Теорія ймовірностей - математична наука, що вивчає закономірності випадкових явищ.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 134 (Seed 777): Бренд (sft_shard_143_of_150.jsonl:line_393)
- **Subject / Grade:** finansova (Grade 9)
- **Concept:** `Бренд` (Citation form: ✅)
- **Scientific Terminology:** `['назва', 'панія', 'логотип']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Бренд — це не просто назва комякі виникають у людей, коли вони панії чи логотип.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 135 (Seed 777): Пісня і праця (sft_shard_125_of_150.jsonl:line_122)
- **Subject / Grade:** ukrmova (Grade university)
- **Concept:** `Пісня і праця` (Citation form: ✅)
- **Scientific Terminology:** `['праця', 'скін']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Пісня і праця – великі дві сили, м я бажаю до скону служить (Франко).» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 136 (Seed 777): Дисциплінарний батальйон (sft_shard_112_of_150.jsonl:line_216)
- **Subject / Grade:** pravoznavstvo (Grade 11)
- **Concept:** `Дисциплінарний батальйон` (Citation form: ✅)
- **Scientific Terminology:** `['батальйон', 'режим', 'відбування', 'покарання']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Дисциплінарний батальйон — це особлива військова частина, у якій забезпечується необхідний режим відбування покарання.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 137 (Seed 777): Ринок (sft_shard_033_of_150.jsonl:line_290)
- **Subject / Grade:** istoriya (Grade 9)
- **Concept:** `Ринок` (Citation form: ✅)
- **Scientific Terminology:** `['категорія', 'товаровиробник', 'покупець', 'привід', 'купівля-продаж']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Ринок — економічна категорія, яка відображає відносини, що складаються між товаровиробниками та покупцями з приводу купівлі-продажу, органічний зв'язок між виробництвом і споживанням.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 138 (Seed 777): Метрополітен (sft_shard_077_of_150.jsonl:line_154)
- **Subject / Grade:** mystetstvo (Grade 9)
- **Concept:** `Метрополітен` (Citation form: ✅)
- **Scientific Terminology:** `['музей', 'бізнесмен', 'шанувальник', 'мистецтво']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Метрополітен — відомий художній музей у США, заснований у Нью-Йорку в 1870 році групою американських бізнесменів і шанувальників мистецтва.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 139 (Seed 777): Активність у шкільному житті (sft_shard_069_of_150.jsonl:line_370)
- **Subject / Grade:** hromadianska (Grade 9)
- **Concept:** `Активність у шкільному житті` (Citation form: ✅)
- **Scientific Terminology:** `['активність', 'простір']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Активність у шкільному житті — це реальна можливість впливати на свій освітній простір.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 140 (Seed 777): Червоні водорості (sft_shard_106_of_150.jsonl:line_277)
- **Subject / Grade:** biolohiya (Grade 7)
- **Concept:** `Червоні водорості` (Citation form: ✅)
- **Scientific Terminology:** `['водорість', 'організм']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Червоні водорості – переважно багатоклітинні організми, лише деякі види одноклітинні.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 141 (Seed 777): Переговори та продажі (sft_shard_128_of_150.jsonl:line_131)
- **Subject / Grade:** finansova (Grade 9)
- **Concept:** `Переговори та продажі` (Citation form: ✅)
- **Scientific Terminology:** `['продаж', 'запорука', 'успіх', 'підприємництво']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Переговори та продажі — це запорука успіху підприємництва.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 142 (Seed 777): Східна елонгація (sft_shard_034_of_150.jsonl:line_217)
- **Subject / Grade:** astronomiya (Grade 11)
- **Concept:** `Східна елонгація` (Citation form: ✅)
- **Scientific Terminology:** `['елонгація', 'момент', 'положення', 'планета']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Східна елонгація — це момент положення, коли планету видно ліворуч від Сонця ввечері (B1).» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 143 (Seed 777): Дружба (sft_shard_013_of_150.jsonl:line_218)
- **Subject / Grade:** etyka (Grade 5)
- **Concept:** `Дружба` (Citation form: ✅)
- **Scientific Terminology:** `['стосунок', 'довіра', 'щирість', 'симпатія', 'інтерес']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Дружба — безкорисливі стосунки між людьми, що засновані на довірі, щирості, взаємних симпатіях, спільних інтересах, захопленнях.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 144 (Seed 777): Математичний горизонт (sft_shard_150_of_150.jsonl:line_399)
- **Subject / Grade:** fizyka (Grade 11)
- **Concept:** `Математичний горизонт` (Citation form: ✅)
- **Scientific Terminology:** `['сфера', 'площина', 'горизонт']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Великий круг небесної сфери, площина якого перпендикулярна до прямовисної лінії, називають математичним горизонтом.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 145 (Seed 777): Стриманість (sft_shard_071_of_150.jsonl:line_368)
- **Subject / Grade:** etyka (Grade 5)
- **Concept:** `Стриманість` (Citation form: ✅)
- **Scientific Terminology:** `['гамування', 'бажання', 'почуття', 'пристрасть', 'задоволення']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Стриманість — це свідоме гамування бажань, почуттів, пристрастей, задоволень тощо.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 146 (Seed 777): Агресія (sft_shard_032_of_150.jsonl:line_177)
- **Subject / Grade:** istoriya (Grade 10)
- **Concept:** `Агресія` (Citation form: ✅)
- **Scientific Terminology:** `['суверенітет', 'застосування', 'держава', 'порушення', 'цілісність']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Агресія — незаконне застосування збройної сили однієї держави проти іншої, порушення суверенітету, територіальної цілісності, позбавлення політичної незалежності.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 147 (Seed 777): Світовий океан (sft_shard_079_of_150.jsonl:line_438)
- **Subject / Grade:** ya_doslidzhuiu_svit (Grade 4)
- **Concept:** `Світовий океан` (Citation form: ✅)
- **Scientific Terminology:** `['океан', 'поверхня', 'материк']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Світовий океан — це водна поверхня Землі, яка омиває всі материки та острови.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 148 (Seed 777): Робочий час (sft_shard_029_of_150.jsonl:line_239)
- **Subject / Grade:** pravoznavstvo (Grade 11)
- **Concept:** `Робочий час` (Citation form: ✅)
- **Scientific Terminology:** `['закон', 'угода', 'підстава', 'працівник', 'договір']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Робочий час — установлений законом або угодою, укладеною на підставі закону, час, протягом якого працівники зобов'язані виконувати роботу, визначену трудовим договором.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 149 (Seed 777): Мода (sft_shard_113_of_150.jsonl:line_307)
- **Subject / Grade:** matematyka (Grade 11)
- **Concept:** `Мода` (Citation form: ✅)
- **Scientific Terminology:** `['елемент', 'вибірка']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Мода — це те значення елемента вибірки, яке зустрічається частіше за інші.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**

### Record 150 (Seed 777): Більшість архіпелагів (sft_shard_060_of_150.jsonl:line_123)
- **Subject / Grade:** heohrafiya (Grade 9)
- **Concept:** `Більшість архіпелагів` (Citation form: ✅)
- **Scientific Terminology:** `['більшість', 'архіпелаг', 'риф']` (Terms >= 2 & non-generic: ✅)
- **Textbook Snippet:** «Більшість архіпелагів – це вулканічні острови, довкола яких утворилися коралові рифи.» (Anaphora-free: ✅, OCR-Clean: ✅, Def-Aligned: ✅)
- **Overall Record Verdict:** **PASS**
