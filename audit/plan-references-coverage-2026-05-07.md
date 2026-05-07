# Plan References Coverage Audit - 2026-05-07

Checked `curriculum/l2-uk-en/plans/**/*.yaml` and
`curriculum/l2-uk-en/{level}/plans/**/*.yaml` against `data/sources.db`.

- Total plan files scanned: 1736
- Plans with `references`: 1679
- Distinct textbook sources in corpus: 81
- Plans citing missing textbooks: 32
- Plans not checked because YAML parsing failed: 1

## Missing Textbook References

| Plan | Missing textbook reference |
| --- | --- |
| `curriculum/l2-uk-en/plans/a1/hey-friend.yaml` | `Підручник 4 класу: Кличний відмінок (Заболотний)` |
| `curriculum/l2-uk-en/plans/a1/i-eat-i-drink.yaml` | `Підручник 4 класу: Знахідний відмінок (Заболотний)` |
| `curriculum/l2-uk-en/plans/a1/linking-ideas.yaml` | `Grade 4-5 textbook: Сполучники (Заболотний)` |
| `curriculum/l2-uk-en/plans/a1/my-morning.yaml` | `Кравцова Grade 4, p.113` |
| `curriculum/l2-uk-en/plans/a1/people-around-me.yaml` | `Підручник 4 класу: Знахідний відмінок (Заболотний)` |
| `curriculum/l2-uk-en/plans/a1/questions.yaml` | `Варзацька 4 клас, стор. 41` |
| `curriculum/l2-uk-en/plans/a1/things-have-gender.yaml` | `Пономарова Grade 3, p.86` |
| `curriculum/l2-uk-en/plans/a1/verbs-group-one.yaml` | `Варзацька Grade 4, p.129` |
| `curriculum/l2-uk-en/plans/a1/what-is-it-like.yaml` | `Пономарова Grade 3, p.98` |
| `curriculum/l2-uk-en/plans/a1/where-to.yaml` | `Таблиця відмінків за 4 клас` |
| `curriculum/l2-uk-en/plans/a2/all-cases-practice.yaml` | `Варзацька Grade 4, с. 38` |
| `curriculum/l2-uk-en/plans/a2/checkpoint-cases.yaml` | `Варзацька Grade 4, с. 38` |
| `curriculum/l2-uk-en/plans/a2/checkpoint-dative.yaml` | `Кравцова Grade 4, §135` |
| `curriculum/l2-uk-en/plans/a2/dative-nouns.yaml` | `Кравцова Grade 4, §135` |
| `curriculum/l2-uk-en/plans/a2/instrumental-accompaniment.yaml` | `Пономарьова Grade 4, с. 53-56` |
| `curriculum/l2-uk-en/plans/a2/instrumental-means.yaml` | `Кравцова Grade 4, с. 56-57` |
| `curriculum/l2-uk-en/plans/a2/instrumental-profession.yaml` | `Кравцова Grade 4, с. 58` |
| `curriculum/l2-uk-en/plans/a2/metalanguage-sentences-and-classroom.yaml` | `Большакова Grade 4, Речення. Члени речення` |
| `curriculum/l2-uk-en/plans/a2/metalanguage-verbs-and-time.yaml` | `Вашуленко Grade 4, Дієслово` |
| `curriculum/l2-uk-en/plans/a2/metalanguage-words-and-cases.yaml` | `Большакова Grade 4, Іменник. Відмінювання іменників` |
| `curriculum/l2-uk-en/plans/a2/plural-other-cases.yaml` | `Кравцова Grade 4, с. 46-48` |
| `curriculum/l2-uk-en/plans/a2/services-and-communication.yaml` | `Кравцова Grade 4, §135` |
| `curriculum/l2-uk-en/plans/a2/work-and-food.yaml` | `Кравцова Grade 4, с. 54` |
| `curriculum/l2-uk-en/plans/b1/b1-baseline-future-aspect.yaml` | `Кравцова Grade 4, p.108` |
| `curriculum/l2-uk-en/plans/b1/instrumental-nuances.yaml` | `Кравцова Grade 4, p.57-58` |
| `curriculum/l2-uk-en/plans/b1/narrative-mastery.yaml` | `Варзацька Grade 4, p.14` |
| `curriculum/l2-uk-en/plans/b1/nature-and-environment.yaml` | `Болшакова Grade 2, p.63` |
| `curriculum/l2-uk-en/plans/b1/reflexive-verbs-nuances.yaml` | `Кравцова Grade 4, p.111` |
| `curriculum/l2-uk-en/plans/b1/traveling-ukraine.yaml` | `Кравцова 3 клас, с.83` |
| `curriculum/l2-uk-en/plans/b2/kharchuvannia-i-kukhnia.yaml` | `Заболотний, 7 клас (2015)` |
| `curriculum/l2-uk-en/plans/b2/pobut-shchodenne.yaml` | `Заболотний, 7 клас (2015)` |
| `curriculum/l2-uk-en/plans/b2/sport-i-dozvillia.yaml` | `Заболотний, 7 клас (2015)` |

## Not Checked

| Plan | Reason |
| --- | --- |
| `curriculum/l2-uk-en/plans/ruth.yaml` | YAML parse error at line 178 (`registers` block). |
