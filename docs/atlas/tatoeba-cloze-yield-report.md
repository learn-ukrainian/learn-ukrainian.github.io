# Tatoeba Cloze Yield Report - Phase 1 (#3797)

Run date: 2026-06-26

## Inputs

* Worktree: `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/tatoeba-cloze-yield-3797`
* Python: `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`
* `PYTHONPATH`: `/Users/krisztiankoos/projects/learn-ukrainian`
* Manifest input for the required baseline: `site/src/data/lexicon-manifest.json`, symlinked to the hydrated main-checkout manifest.
* Real Tatoeba exports downloaded 2026-06-26 into `.agent/tmp/tatoeba/`:
  * `ukr_sentences_detailed.tsv.bz2`
  * `eng_sentences_detailed.tsv.bz2`
  * `links.tar.bz2`
  * `sentences_CC0.tar.bz2`, used only to add per-row license values because the current detailed per-language exports include author but not license.
* Augmented sentence TSV license counts:
  * Ukrainian: CC0 = 393; CC-BY 2.0 FR = 188,212.
  * English: CC0 = 41,487; CC-BY 2.0 FR = 1,985,925.
* UK-EN linked pairs loaded by `read_tatoeba_pairs`: 217,297.

## Required Baseline: Hydrated Manifest As-Is

This is the direct real-data run against the hydrated manifest symlink requested in the dispatch. It emitted no candidates.

| Metric | Count |
| --- | ---: |
| Pairs processed | 217,297 |
| Candidates emitted | 0 |
| `accusative_direct_object` | 0 |
| `locative_static_u` | 0 |
| `locative_static_na` | 0 |

Sentence CEFR breakdown for emitted candidates: none, because the baseline emitted zero candidates.

Raw generator stdout:

```text
wrote 0 candidates to .agent/tmp/tatoeba/candidates-real-manifest-full.json
rejected.blocked_register=34
rejected.multiword_lemma=993
rejected.russianism_prescreen=14233
rejected.sentence_cefr_unknown=108865
rejected.sentence_length=62349
```

The baseline zero is structural, not a Tatoeba volume issue: `_build_target_index` produced 0 target keys / 0 target forms from the hydrated manifest. The manifest contains real morphology, but its case map is keyed by Ukrainian labels such as `знахідний` and `місцевий`, while the case rules call `_case_form()` with canonical English keys such as `accusative` and `locative`.

## Scratch Normalized Estimate

To estimate downstream yield and quality after that manifest/generator compatibility bug is fixed, I ran a scratch-only derived manifest that preserved the hydrated manifest and added English case aliases next to the Ukrainian case labels. This added 9,891 case aliases across 1,413 entries and produced 3,315 target-form keys / 5,430 target forms. The derived manifest and full candidate set remain in `.agent/tmp/tatoeba/` and are not committed.

| Metric | Count |
| --- | ---: |
| Pairs processed | 217,297 |
| Candidates emitted | 155 |

By case rule:

| caseRuleId | Candidates |
| --- | ---: |
| `accusative_direct_object` | 146 |
| `locative_static_u` | 6 |
| `locative_static_na` | 3 |

By emitted sentence CEFR:

| CEFR | Candidates |
| --- | ---: |
| A1 | 90 |
| A2 | 43 |
| B1 | 17 |
| B2 | 5 |
| C1 | 0 |
| C2 | 0 |

By emitted candidate license:

| License | Candidates |
| --- | ---: |
| CC-BY 2.0 FR | 155 |

Raw generator stdout for the normalized estimate:

```text
wrote 155 candidates to .agent/tmp/tatoeba/candidates-normalized-full.json
rejected.blocked_register=34
rejected.cap_lemma_case_rule=278
rejected.exact_duplicate=110
rejected.multiword_lemma=993
rejected.near_duplicate=289
rejected.russianism_prescreen=14233
rejected.sentence_cefr_above_word=666
rejected.sentence_cefr_unknown=108865
rejected.sentence_length=62349
rejected.single_target_occurrence=17
rejected.surface_equals_lemma=947
rejected.target_punctuation_or_multiword=2017
rejected.unsupported_trigger=3181
rejected.vesum_ambiguous=3756
```

## Quality Sample

The committed JSON sample at `docs/atlas/tatoeba-cloze-sample.json` contains these same 30 emitted candidates from the scratch normalized estimate. The required baseline emitted no candidates, so there is no baseline quality sample.

| # | caseRuleId | CEFR | sentence | form / blankCase | clozeEn | provenance |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | accusative_direct_object | A1 | Хто тобі дав цю ___? | валізу / accusative | Who gave you this suitcase? | deniko; CC-BY 2.0 FR |
| 2 | accusative_direct_object | A1 | Я шукаю маленьку ___. | валізу / accusative | I'm looking for a small suitcase. | deniko; CC-BY 2.0 FR |
| 3 | accusative_direct_object | A1 | Вона в цей час готувала ___. | вечерю / accusative | She was cooking dinner at that time. | uaspeaker; CC-BY 2.0 FR |
| 4 | accusative_direct_object | A1 | Я знаю, де знайти ___. | воду / accusative | I know where to find water. | deniko; CC-BY 2.0 FR |
| 5 | accusative_direct_object | A1 | Де я можу отримати ___? | допомогу / accusative | Where can I get some help? | Anjy; CC-BY 2.0 FR |
| 6 | accusative_direct_object | A1 | Я купив ___ у жовтні. | машину / accusative | I bought a car in October. | deniko; CC-BY 2.0 FR |
| 7 | accusative_direct_object | A1 | У наступну ___ буде концерт. | неділю / accusative | There will be a concert next Sunday. | rozmaita; CC-BY 2.0 FR |
| 8 | locative_static_u | A1 | Я був у ___. | горах / locative | I was in the mountains. | Wordowl; CC-BY 2.0 FR |
| 9 | locative_static_u | A1 | Ми живемо в ___. | горах / locative | We live in the mountains. | rul; CC-BY 2.0 FR |
| 10 | locative_static_u | A1 | Я це бачив у ___. | новинах / locative | I saw that on the news. | deniko; CC-BY 2.0 FR |
| 11 | locative_static_u | A1 | Вони у ___ рішення. | пошуках / locative | They are seeking a solution. | deniko; CC-BY 2.0 FR |
| 12 | locative_static_u | A1 | Я в ___ роботи. | пошуках / locative | I'm looking for a job. | deniko; CC-BY 2.0 FR |
| 13 | locative_static_na | A1 | Ти можеш стояти на ___? | руках / locative | Can you stand on your hands? | deniko; CC-BY 2.0 FR |
| 14 | locative_static_na | A1 | На ___ ти герой. | словах / locative | You're all talk. | deniko; CC-BY 2.0 FR |
| 15 | locative_static_na | A2 | Я зазвичай не п'ю вино на ___. | вечірках / locative | I don't usually drink wine at parties. | deniko; CC-BY 2.0 FR |
| 16 | locative_static_u | A2 | Її імені немає у ___. | списках / locative | Her name is not on the lists. | oromashka; CC-BY 2.0 FR |
| 17 | accusative_direct_object | A2 | Ти прийдеш на мою ___? | вечірку / accusative | Are you coming to my party? | deniko; CC-BY 2.0 FR |
| 18 | accusative_direct_object | A2 | Дякую за цікаву ___! | дискусію / accusative | Thank you for the interesting discussion. | User55521; CC-BY 2.0 FR |
| 19 | accusative_direct_object | A2 | Вона допомогла старому перейти ___. | дорогу / accusative | She helped the old man cross the road. | deniko; CC-BY 2.0 FR |
| 20 | accusative_direct_object | A2 | Тобі краще взяти ___ з собою сьогодні. | парасольку / accusative | You had better take an umbrella with you today. | deniko; CC-BY 2.0 FR |
| 21 | accusative_direct_object | A2 | Потяг прибуває на п'яту ___. | платформу / accusative | The train arrives on platform number 5. | Oleksandr_Tahayev; CC-BY 2.0 FR |
| 22 | accusative_direct_object | A2 | Я не можу відкрити цю ___. | пляшку / accusative | I can't open this bottle. | deniko; CC-BY 2.0 FR |
| 23 | accusative_direct_object | B1 | Я не знаю, чому я ___ саме так. | дію / accusative | I don't know why I'm acting like this. | deniko; CC-BY 2.0 FR |
| 24 | accusative_direct_object | B1 | Ви забули ___ в кінці речення. | крапку / accusative | You've forgotten the full stop at the end of the sentence. | Ahha; CC-BY 2.0 FR |
| 25 | accusative_direct_object | B1 | Хто допоміг тобі заплатити за вищу ___? | освіту / accusative | Who helped you pay for your college education? | deniko; CC-BY 2.0 FR |
| 26 | accusative_direct_object | B1 | Ти приймаєш цю ___? | посилку / accusative | Do you accept the premise? | deniko; CC-BY 2.0 FR |
| 27 | accusative_direct_object | B2 | Він знає ___ як свої п'ять пальців. | околицю / accusative | He knows the area like the back of his hand. | Ahha; CC-BY 2.0 FR |
| 28 | accusative_direct_object | B2 | Ти маєш зробити ___ на інший потяг на наступній станції. | пересадку / accusative | You have to change trains at the next station. | deniko; CC-BY 2.0 FR |
| 29 | accusative_direct_object | B2 | Вона сказала йому, що він має ___. | рацію / accusative | She told him that he was right. | shanghainese; CC-BY 2.0 FR |
| 30 | accusative_direct_object | B2 | Вона мала ___, чи не так? | рацію / accusative | She was right, wasn't she? | glossboss; CC-BY 2.0 FR |

## Read

Do not proceed to Phase 2 full generation on the generator exactly as run against the hydrated manifest: it currently has zero real yield because the target index is empty. The first Phase 2 prerequisite should be a small code fix or manifest-normalization step that maps Ukrainian case labels (`знахідний`, `місцевий`) to the canonical case ids used by `CASE_RULES` (`accusative`, `locative`).

After that compatibility fix, the real-data estimate is nonzero but modest: 155 candidates from 217,297 UK-EN pairs. The volume is also highly skewed: 146 accusative candidates versus only 9 locative candidates. That is enough to justify a reviewed pilot, but not enough to assume broad cloze coverage without either expanding supported triggers/rules or adding another source.

The biggest volume losses in the normalized run were `sentence_cefr_unknown=108865` and `sentence_length=62349`. Those are expected to be aggressive for learner-safe cloze material. `russianism_prescreen=14233` is sizable but not the dominant bottleneck. The target-side losses worth reviewing are `unsupported_trigger=3181`, `vesum_ambiguous=3756`, and `sentence_cefr_above_word=666`; these look like the main places to tune after the case-key fix.

Quality is mixed. Many simple accusative Ukrainian clozes are natural and useful. However, the sample also shows bad-but-passed cases: weak or fragmentary English links, idiomatic `мати рацію` examples that are not good noun-case practice, and locative examples where the English translation is too terse to help a learner verify meaning. I would proceed only as a reviewed pilot with an English-translation quality gate, not as automatic publication.
