# Картка даних: Ukrainian Calque + Grammar Evaluation v0

## Коротко

`ua-gec-calque-grammar-public-v0` — публічний набір для мінімального
виправлення українських речень із кальками та граматичними помилками. Версія
`0.1.0` містить 677 held-out речень із UA-GEC 2.0, 918 допустимих
annotator-references і 1 608 анотацій `F/Calque` або `G/*`.

Це не загальний показник «якості української», не leaderboard і не
тренувальний корпус.

## Завдання

На вхід моделі подаються лише:

- стабільний item ID;
- початкове українське речення;
- SHA-256 початкового речення;
- SHA-256 замороженої інструкції.

Модель має повернути все речення з мінімально необхідними виправленнями.
Gold targets, references, edit spans і scores не входять до generation input.
Відповіді спочатку зберігають, а потім оцінюють окремо.

Headline-метрика для тверджень саме про кальки — heritage-safe recall на
анотаціях, які допускає окремий benchmark disposition. Calque precision не
обчислюється: hypothesis-only edits не мають типів, тому їхні false positives
не можна чесно приписати тегу кальки.

Окремо звіт подає exact correction-edit precision, recall і F0.5 для всіх
вибраних upstream-міток стандартизації та граматики. Це не heritage-safe
calque score. True positive вимагає точного source-token span і replacement.
Для кожного речення обирається annotator-reference з найкращим F0.5; рівність
вирішується детерміновано. Тому результат дещо поблажливіший за strict
single-reference score. Exact corrected-sentence accuracy є супровідною
метрикою.

## Походження й побудова

Джерело: UA-GEC 2.0, commit
`4757f72f192c4a41e4c8fb1d9690a948f87cf6d6`, partition
`gec-fluency/test`. Публічний predicate без квоти включає кожне речення з
принаймні однією анотацією `F/Calque` або `G/*`. Для кожного annotator target
застосовуються лише ці in-scope edits; інші upstream edits залишаються
незміненими.

Маніфест розподіляє всі 2 690 test-речень:

| Disposition | Кількість |
| --- | ---: |
| Включено | 677 |
| Виключено: немає in-scope edit | 2 013 |
| Разом | 2 690 |

У test є 166 документів і 76 авторів. У train — 752 автори. Перетин авторів і
документів між train та test дорівнює нулю. У 677 включених записах 505
позначено upstream як native, 172 — non-native; source-language metadata:
502 `null`, 114 `en`, 58 `ru`, 3 `pl`. Записів з upstream
`is_sensitive=true` немає.

Старі 52 train-derived приклади залишаються development-fixtures. Вони не
входять до held-out результатів і використовуються лише слабкою
детермінованою literal-rule baseline.

## Покриття

| Тег | Анотацій |
| --- | ---: |
| `F/Calque` | 354 |
| `G/Case` | 391 |
| `G/UngrammaticalStructure` | 270 |
| `G/Prep` | 143 |
| `G/Number` | 85 |
| `G/Tense` | 77 |
| `G/Gender` | 76 |
| Інші `G/*` | 212 |

Повний розподіл зберігається в held-out manifest і score reports. Support у
per-tag звіті — усі eligible upstream annotations. Окреме
`selected_reference_support` є denominator конкретного scored run.

### Розподіл upstream `F/Calque`

UA-GEC нормалізує текст до стандартної української. Тому upstream
`F/Calque` зберігається без змін як provenance, але не вважається автоматичною
benchmark-істиною про кальку. Окремий disposition layer охоплює всі 354
annotator-level анотації (293 унікальні spans):

| Benchmark disposition | Анотацій |
| --- | ---: |
| Допущено до headline calque recall | 338 |
| Register/розмовна стандартизація | 3 |
| Heritage conflict | 2 |
| Contested / контекст не розв'язано | 11 |
| Разом | 354 |

Exact-style probe з pinned dict_uk/VESUM v6.8.0 виявив 49 унікальних
collision spans: 34 `bad`, 10 `slang`, 3 `arch`, 2 `rare`. Це evidence для
перевірки, а не автоматичне контекстне рішення. У VESUM немає окремого
офіційного `dial` token; parser може відтворно витягувати comment-level
`діалект` evidence, але жодна така ознака не дає автоматичного допуску.
Невизначені cases fail closed поза headline scoring.

## Базові результати

| Baseline | Overall edit P | Overall edit R | Overall edit F0.5 | Headline calque R | Exact sentence |
| --- | ---: | ---: | ---: | ---: | ---: |
| Identity v1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Train-fixture literal rules v1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `gpt-5.6-terra` | 0.3110 | 0.1309 | 0.2439 | 0.1410 | 0.1610 |

Для Terra 95% sentence-bootstrap interval становить 0.2073–0.2780 для edit
F0.5 і 0.1344–0.1891 для exact accuracy. Усі 677 відповідей кожного run
збережено; freeze manifest фіксує model, provider route, prompt, decoding,
runner, response й report hashes. Provider не відкривав temperature, top-p
або seed, тому live generation не є byte-reproducible. Повторне scoring
збережених відповідей є детермінованим. Для Terra headline calque recall —
33/234 = 0.1410; calque precision лишається `null`.

## Права й атрибуція

UA-GEC і відтворений із нього текст поширюються за CC BY 4.0. Derived
dict_uk/VESUM evidence поширюється за CC BY-NC-SA 4.0. Повну атрибуцію,
pinned sources, license links і опис змін наведено в
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Код оцінювача й пакувальні
скрипти мають MIT license репозиторію.

## Призначення

Дозволені цілі:

- відтворне порівняння систем мінімального виправлення українських кальок і
  граматики;
- дослідження edit precision/recall, over-editing і per-tag recall;
- локальна перевірка saved responses без доступу до провайдера.

Непризначені цілі:

- загальна оцінка української, factuality, стилю, культурної коректності або
  мовної компетентності людини;
- висновки про окремих авторів чи source-language групи;
- автоматичне оцінювання учнів, наймання або інші high-stakes рішення;
- training, fine-tuning, synthetic corruption, DPO чи preference data;
- Daily Practice, Hramatka, teacher feedback, Atlas або приватні canaries.

## Обмеження

- Gold успадковує рішення й можливий шум UA-GEC annotators, які
  нормалізували текст до стандартної української.
- Upstream `F/Calque` означає UA-GEC standardization label; benchmark
  disposition є окремим рішенням про calque scoring.
- VESUM attestation і `arch`/`bad`/`rare`/`slang` або comment-level dialect
  evidence не розв'язують sense/context автоматично. Невизначені записи
  збережено як `HERITAGE_CONFLICT` або `CONTESTED` і виключено з headline.
- Повніші contextual heritage markers залежать від issue #5092; реліз не
  заявляє нуль dialect conflicts через відсутність окремого `dial` token.
- Набір охоплює лише `F/Calque` і `G/*` у конкретному upstream test split.
- Best-reference policy може підвищувати score проти strict
  single-reference evaluation.
- Dependency-free Wagner–Fischer aligner реалізує exact-edit semantics, але
  не заявляє byte-identical ERRANT alignment у неоднозначних випадках.
- Tokenized M2 text зберігає upstream spacing; це не оцінка природності
  detokenized output.
- Низький support окремих тегів дає широкі uncertainty intervals.

## Безпека, приватність і contamination

Публікуються лише upstream-псевдонімні document/author IDs; реідентифікація не
підтримується й не є дозволеним use. У вибірці немає upstream-sensitive
записів. Провайдерні секрети не зберігаються. Aggregate reports не містять
item text, IDs, edits або content hashes.

[Політика contamination](contamination-policy.md) забороняє переносити
held-out cases до продуктів або training inventories. Виявлений витік вимагає
нової версії, повторної екстракції та нових baseline receipts.

## Супровід і допуск змін

Помилки повідомляють через GitHub issue з посиланням на release version та
item ID, без копіювання приватних даних. Зміни приймаються лише через
переглянутий PR, детерміновані тести й новий freeze version.

Новий fixture може потрапити до майбутнього public held-out release лише якщо
він:

1. походить із rights-cleared, version-pinned upstream held-out partition;
2. проходить наперед визначений quota-free predicate;
3. зберігає writer/document disjointness і повну attribution;
4. не походить із продукту, teacher feedback, приватного canary, synthetic
   generation або training pipeline;
5. отримує новий semantic version, baselines і cross-family review.

Freeze `0.1.0` не редагують на місці. Правила PATCH/MINOR/MAJOR наведено в
freeze manifest і contamination policy.

## English reproducibility note

This is a 677-item public minimal-edit Ukrainian calque and grammar correction
evaluation derived deterministically from the pinned UA-GEC 2.0 test split.
It is not a leaderboard or training corpus. See
[REPRODUCING.md](REPRODUCING.md) for equivalent English setup, offline saved
response scoring, provenance, and verification instructions.
