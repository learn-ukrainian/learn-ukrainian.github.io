# Політика замороження й запобігання витоку

Ця політика стосується публічного оцінювання виправлень українських кальок і
граматики `ua-gec-calque-grammar-public-v0` версії `0.1.0`. Вона не поширює
оцінювальний набір на продукти, навчальні корпуси чи інші дослідницькі задачі.

## Заморожений склад

Єдиним машинним реєстром релізу є
`data/projects/ua_eval_harness/releases/v0.1.0/freeze_manifest.json`. Він
фіксує SHA-256 для:

- конфігурації й маніфесту вибірки;
- інструкції, схеми відповіді, екстрактора, оцінювача й необов'язкового
  провайдерного запускатора;
- пакета запитів, усіх збережених відповідей і агрегованих звітів трьох
  базових систем;
- 52 тренувальних прикладів, які дозволено використовувати лише як
  development-fixtures і які не входять до held-out результатів.

Перевірка не потребує мережі або провайдерних ключів:

```bash
.venv/bin/python scripts/projects/ua_eval_harness/verify_release_freeze.py
```

Будь-яка невідповідність байтів, метаданих запуску, prompt/scorer receipt,
покриття відповідей або політики агрегованих звітів завершує перевірку
помилкою.

## Цілісність поділу

Джерелом є UA-GEC 2.0 на commit
`4757f72f192c4a41e4c8fb1d9690a948f87cf6d6`. Хеші `LICENSE`, `README.md`,
`data/metadata.csv` і `gec-fluency.test.m2` зафіксовано в freeze manifest.

Екстрактор перевіряє, що:

1. кожен document ID у metadata унікальний і має рівно один partition;
2. множина документів у test M2 точно дорівнює множині test-документів у
   metadata;
3. автори train і test не перетинаються;
4. усі 2 690 test-речень мають disposition: 677 включено, 2 013 виключено.

Отже, перетин train/test становить нуль і на рівні авторів, і на рівні
документів. 52 старі development-fixtures походять із train і залишаються
окремими від held-out оцінювання.

## Відомі контакти з даними

- Публічна інструкція не містить прикладів.
- Детермінована literal-rule baseline будує правила лише з 52 train-derived
  development-fixtures. Це навмисно слабка діагностична baseline, не
  held-out-навчання.
- Перед повним запуском дві source-only позиції було використано для
  транспортної перевірки. Після неї уточнено лише вимогу зберігати пробіли й
  пунктуацію. Gold-відповіді, edits і scores не переглядалися.
- Реальну модель обрано за наперед чинним operator routing, а не за
  результатами цього benchmark.
- Під час генерації моделі передавалися тільки ID, source, source hash і
  prompt hash. Gold targets, references, edits та score були відсутні.

## Заборонене повторне використання

Публічні source, gold, IDs, hashes і похідні правила цього held-out набору
заборонено додавати до:

- Daily Practice або іншого learner-exercise inventory;
- будь-якого training, fine-tuning, synthetic-data, preference-data чи DPO
  inventory;
- Hramatka, teacher-feedback або приватних regression/canary наборів;
- Atlas чи іншого приватного продуктового стану.

Збіг, знайдений після замороження, є contamination incident. Такий реліз не
можна мовчки «виправити»: потрібні окремий incident record, нова версія,
повторна екстракція, нові baselines і новий freeze manifest.

## Безпечне звітування

Публічні score reports містять тільки агрегати, support, uncertainty та
provenance. Вони не можуть містити item IDs, source/target text, edit spans,
raw responses або content hashes. Збережені model responses є окремими
публічними артефактами для відтворення оцінки; звіт не дублює їх.

## Версіонування

Заморожені байти не редагують на місці.

- `PATCH`: документаційне або пакувальне виправлення без зміни dataset,
  task, scorer чи результатів.
- `MINOR`: сумісне доповнення task contract, scorer, runner або baselines.
- `MAJOR`: зміна dataset, eligibility predicate, gold, split, primary metric
  або несумісна зміна контракту.

Кожна нова версія отримує окрему директорію freeze; старі freeze manifests
зберігаються та мають залишатися незалежно перевірними.
