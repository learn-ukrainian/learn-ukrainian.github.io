---
language:
- uk
license:
- cc-by-4.0
- mit
pretty_name: INVALID — UA Open-Weight Eval Gemma 4 runtime failure receipt
size_categories:
- n<10K
task_categories:
- text-generation
tags:
- evaluation
- invalid-results
- runtime-failure
- ukrainian
- gemma-4
- qat-q4_0
configs:
- config_name: metrics
  default: true
  data_files:
  - split: test
    path: metrics.jsonl
- config_name: responses
  data_files:
  - split: test
    path: responses.jsonl
---

# INVALID RESULT — runtime failure receipt only

> **Do not use this dataset as a Gemma 4 baseline and do not cite its metrics
> as evidence of Ukrainian-language quality.**

This Hugging Face repository was made private on 2026-08-04 without deleting
its files or history. The public transparency record is the GitHub incident
report and its retained hashes, not this invalid result payload.

The provider jobs completed and the files were structurally valid, but the
saved responses were runtime-corrupted. A source-aware replay on 2026-08-03
found:

- canary: 100/100 invalid rows; 98 exact-copy violations, 100 rows with newly
  introduced reserved model markers, and 49 rows with newly introduced
  non-whitespace C0 controls;
- full run: 4,000/4,000 invalid rows; 3,961 exact-copy violations, 4,000 rows
  with newly introduced reserved model markers, and 1,830 rows with newly
  introduced non-whitespace C0 controls.

The counts are source-aware: a marker or control already present in a frozen
source is not treated as newly introduced corruption. The gate makes no
linguistic judgment about Ukrainian, quoted Russian, surzhyk, historical
language, or regional language.

The original payload is preserved privately as a failure receipt. Its
historical revision is `6d294b175820777ae382e36ec6a781c5f9032728`; its
historical package SHA-256 is
`f5710a3fe9aabeac29d5e6a00b7858657fc6880172b9222b9cc0db0bee86917a`.
Those identifiers prove which bytes failed; they do not validate the metrics.
The recorded USD 3.750167 is historical provider cost, not evidence of a valid
evaluation and not authorization for another run.

The frozen UA Open-Weight Eval v0.1.0 suite itself is not invalidated. Only this
model/runtime/output pairing is invalid. The incident record and corrected
source-aware gate are maintained in the
[project repository](https://github.com/learn-ukrainian/learn-ukrainian.github.io/blob/main/docs/projects/ua-open-weight-eval/HF_JOBS_BASELINE.md).

## НЕДІЙСНИЙ РЕЗУЛЬТАТ — лише квитанція про помилку

> **Не використовуйте цей набір як базову оцінку Gemma 4 і не цитуйте його
> метрики як доказ якості української мови.**

Репозиторій Hugging Face зроблено приватним 4 серпня 2026 року без видалення
файлів чи історії. Публічними доказами залишаються опис інциденту та хеші на
GitHub, а не цей недійсний пакет результатів.

Завдання провайдера завершилися, але збережені відповіді були пошкоджені
середовищем виконання. Усі 100 відповідей canary і всі 4 000 відповідей
повного запуску містять нові службові маркери моделі. Майже всі відповіді
`preserve`/`abstain` також не відтворили джерело дослівно.

Початкові файли збережено приватно лише як квитанцію про помилку. Вони не
дають надійних висновків про українську мову Gemma 4. Сам незмінний набір
UA Open-Weight Eval v0.1.0 не визнано недійсним; недійсною є лише ця комбінація
моделі, середовища виконання та відповідей. Повторний запуск не дозволено.
