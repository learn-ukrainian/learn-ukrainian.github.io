# Corpus Coverage Map — A1 Smoke Test

## Scope
This report summarizes the `#1333` A1 smoke-test slice only: the 23 already-audited A1 articles, with seminar tracks excluded.
`article_concepts.json` currently caches concept derivation for 55 A1 discovery files, but the audited coverage slice in `coverage_map.json` remains 23 articles.

## Method
- Concept derivation uses Codex judgment only; the prompt and model are recorded in `data/corpus_audit/article_concepts.json` for reproducibility.
- Corpus presence checks are deterministic: normalized exact-substring matching against `textbooks` and `external_articles`, reusing `normalize_text` from `#1330` for apostrophes and OCR cleanup.
- No LLM fuzzy matching is used for presence checks.

## Summary
- Generated from data timestamp: 2026-04-18T23:46:17+00:00
- Articles audited: 23
- Concepts checked: 279
- Concepts grounded in at least one corpus: 251 / 279 (90.0%)
- Concepts absent from both corpora: 28 / 279

## Corpus Presence Mix

| Presence bucket | Concepts |
|---|---:|
| In `textbooks` and `external_articles` | 213 |
| In `textbooks` only | 34 |
| In `external_articles` only | 4 |
| In neither corpus | 28 |

## Lowest-Coverage Articles

| Article | Covered | Missing | Coverage |
|---|---:|---:|---|
| `a1/at-the-cafe` | 3 / 12 | 9 | `#####...............` 25.0% |
| `a1/please-do-this` | 9 / 13 | 4 | `##############......` 69.2% |
| `a1/checkpoint-communication` | 9 / 11 | 2 | `################....` 81.8% |
| `a1/around-the-city` | 10 / 12 | 2 | `#################...` 83.3% |
| `a1/colors` | 12 / 14 | 2 | `#################...` 85.7% |
| `a1/checkpoint-places` | 9 / 10 | 1 | `##################..` 90.0% |
| `a1/what-time` | 9 / 10 | 1 | `##################..` 90.0% |
| `a1/checkpoint-actions` | 10 / 11 | 1 | `##################..` 90.9% |
| `a1/my-plans` | 11 / 12 | 1 | `##################..` 91.7% |
| `a1/reading-ukrainian` | 11 / 12 | 1 | `##################..` 91.7% |

## Top Gap Categories

| Severity | Category | Affected articles | Absent concepts | Representative gaps |
|---|---|---:|---:|---|
| BLOCKER | Побутові сценарії та лексичні формули | 5 | 10 | мій район, їдьте прямо, замовлення напою |
| BLOCKER | Мовленнєві формули й етикет | 3 | 7 | ввічливе звертання до офіціанта, ввічливе прохання про меню, прохання про рахунок |
| BLOCKER | Дієслово: вид, час, спосіб | 3 | 5 | модальні дієслова з інфінітивом, дієслова на -ти, утворення форми на -й |
| BLOCKER | Відмінки й відмінювання | 2 | 2 | чоловічий рід у знахідному як родовому, питання «в чи на?» |
| BLOCKER | Синтаксис і порядок слів | 1 | 2 | складне речення зі сполучником де, складне речення зі сполучником коли |

## Priority Ukrainian Sources

Strictly Ukrainian sources only; no Russian-language or translated-from-Russian works are proposed here.

| Priority | Gap category | Affected articles | Source | Format | License | Est. chunks |
|---|---|---:|---|---|---|---:|
| BLOCKER | Побутові сценарії та лексичні формули | 5 | Вікторія Дороз — Методика навчання української мови в загальноосвітніх закладах | print | commercial / purchasable | 540 |
| BLOCKER | Побутові сценарії та лексичні формули | 5 | Олеся Палінська, Оксана Туркевич — Крок 1. Українська мова як іноземна. Книга для студента | print | commercial / purchasable | 146 |
| BLOCKER | Мовленнєві формули й етикет | 3 | Борис Антоненко-Давидович — Як ми говоримо | pdf | preservation scan / archive PDF | 379 |
| BLOCKER | Мовленнєві формули й етикет | 3 | Олександр Пономарів — Сучасна українська мова | print | commercial / purchasable | 627 |
| BLOCKER | Дієслово: вид, час, спосіб | 3 | Олена Лавринець, Катерина Симонова, І. Ярошевич — Сучасна українська літературна мова. Морфеміка. Словотвір. Морфологія | print | commercial / purchasable | 734 |
| BLOCKER | Дієслово: вид, час, спосіб | 3 | Українська національна комісія з питань правопису — Український правопис | pdf | official public PDF | 420 |
| BLOCKER | Відмінки й відмінювання | 2 | Олена Лавринець, Катерина Симонова, І. Ярошевич — Сучасна українська літературна мова. Морфеміка. Словотвір. Морфологія | print | commercial / purchasable | 734 |
| BLOCKER | Відмінки й відмінювання | 2 | Українська національна комісія з питань правопису — Український правопис | pdf | official public PDF | 420 |

## Findings
The weakest article by far is `a1/at-the-cafe`, where service-interaction language (menu requests, recommendations, bill/payment talk, dietary clarifications) is missing much more often than core school-grammar concepts.
Most remaining A1 misses cluster around situational learner language: route-giving formulas, etiquette distinctions such as `ти`/`ви`, precise clock-time answers, and a few imperative/morphology teaching phrases.
This points to a structural corpus mix problem rather than a broad grammar deficit: the school-textbook corpus covers phonetics and formal grammar better than adult beginner interactional Ukrainian.
