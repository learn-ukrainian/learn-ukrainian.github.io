# Tatoeba Cloze Yield Report - Phase 1 (#3797)

Run date: 2026-06-26 · **Phase 1 retry: 2026-07-19**

## Phase 1 retry (real data, 2026-07-19)

Re-ran the merged generator against fresh Tatoeba weekly exports + the current
hydrated Atlas manifest + local `data/vesum.db`. This closes the #3797 Phase-1
gap that earlier explore-only dispatches left without a commit: real yield
counts, a machine-readable report path, and a loud missing-input CLI.

### Phase 1 retry runbook

Inputs (gitignored / local only):

| Input | Where |
| --- | --- |
| Hydrated manifest | `site/src/data/lexicon-manifest.json` (symlink from main checkout or release hydrate) |
| VESUM | `data/vesum.db` (symlink from main checkout) |
| Tatoeba UK detailed | `.agent/tmp/tatoeba/ukr_sentences_detailed.tsv` |
| Tatoeba EN detailed | `.agent/tmp/tatoeba/eng_sentences_detailed.tsv` |
| Tatoeba links | `.agent/tmp/tatoeba/links.csv` |
| Tatoeba CC0 IDs | `.agent/tmp/tatoeba/sentences_CC0.csv` |

Download (per-language detailed exports omit license; weekly Saturday UTC refresh):

```bash
mkdir -p .agent/tmp/tatoeba && cd .agent/tmp/tatoeba
curl -fLO https://downloads.tatoeba.org/exports/per_language/ukr/ukr_sentences_detailed.tsv.bz2
curl -fLO https://downloads.tatoeba.org/exports/per_language/eng/eng_sentences_detailed.tsv.bz2
curl -fLO https://downloads.tatoeba.org/exports/links.tar.bz2
curl -fLO https://downloads.tatoeba.org/exports/sentences_CC0.tar.bz2
bunzip2 -kf ukr_sentences_detailed.tsv.bz2 eng_sentences_detailed.tsv.bz2
tar -xjf links.tar.bz2
tar -xjf sentences_CC0.tar.bz2
```

Generate review candidates + yield report (does **not** publish live cloze):

```bash
.venv/bin/python scripts/audit/generate_tatoeba_cloze_candidates.py \
  --manifest site/src/data/lexicon-manifest.json \
  --uk-sentences .agent/tmp/tatoeba/ukr_sentences_detailed.tsv \
  --en-sentences .agent/tmp/tatoeba/eng_sentences_detailed.tsv \
  --links .agent/tmp/tatoeba/links.csv \
  --cc0-sentences .agent/tmp/tatoeba/sentences_CC0.csv \
  --default-license "CC-BY 2.0 FR" \
  --out .agent/tmp/tatoeba/candidates-phase1-retry-full.json \
  --yield-report docs/atlas/tatoeba-cloze-yield-phase1-retry.json \
  --progress-every 10000
```

Missing hydrations fail closed with an actionable `FileNotFoundError` (manifest,
Tatoeba paths, or `data/vesum.db` when `--vesum-json` is omitted).

### Phase 1 retry results

| Metric | Count |
| --- | ---: |
| Pairs processed | 217,316 |
| Target form keys | 6,955 |
| Target forms | 11,293 |
| Lemmas with targets | 2,799 |
| Candidates emitted | 1,981 |
| Candidate license `CC-BY 2.0 FR` | 1,980 |
| Candidate license `CC0` | 1 |
| Wall time | ~223s |

By case rule:

| caseRuleId | Candidates |
| --- | ---: |
| `accusative_direct_object` | 1,917 |
| `locative_static_u` | 41 |
| `locative_static_na` | 23 |

By emitted sentence CEFR:

| CEFR | Candidates |
| --- | ---: |
| A1 | 888 |
| A2 | 528 |
| B1 | 349 |
| B2 | 209 |
| C1 | 7 |
| C2 | 0 |

Full rejection breakdown:

| Rejection | Count |
| --- | ---: |
| `blocked_register` | 56 |
| `exact_duplicate` | 424 |
| `multiword_lemma` | 1,245 |
| `near_duplicate` | 1,206 |
| `russianism_prescreen` | 195 |
| `sentence_cefr_above_word` | 5,422 |
| `sentence_cefr_unknown` | 2,163 |
| `sentence_length` | 20,081 |
| `single_target_occurrence` | 240 |
| `surface_equals_lemma` | 2,016 |
| `target_punctuation_or_multiword` | 3,701 |
| `unsupported_trigger` | 15,864 |
| `vesum_ambiguous` | 21,550 |

Raw generator stdout:

```text
loaded entries=8552 pairs=217316 cc0_ids=559260
progress.start pairs=217316 target_keys=6955 target_forms=11293 lemmas_with_targets=2799
progress.done pairs=217316 candidates=1981
wrote yield report to .agent/tmp/tatoeba/yield-phase1-retry-full.json
targets.keys=6955 forms=11293 lemmas=2799
wrote 1981 candidates to .agent/tmp/tatoeba/candidates-phase1-retry-full.json
rejected.blocked_register=56
rejected.exact_duplicate=424
rejected.multiword_lemma=1245
rejected.near_duplicate=1206
rejected.russianism_prescreen=195
rejected.sentence_cefr_above_word=5422
rejected.sentence_cefr_unknown=2163
rejected.sentence_length=20081
rejected.single_target_occurrence=240
rejected.surface_equals_lemma=2016
rejected.target_punctuation_or_multiword=3701
rejected.unsupported_trigger=15864
rejected.vesum_ambiguous=21550
```

### Deltas vs Phase 1.5 (2026-06-26)

| Metric | Phase 1.5 | Phase 1 retry | Delta |
| --- | ---: | ---: | ---: |
| Pairs | 217,297 | 217,316 | +19 |
| Candidates | 2,070 | 1,981 | −89 |
| Accusative | 2,000 | 1,917 | −83 |
| Locative `u` | 37 | 41 | +4 |
| Locative `na` | 33 | 23 | −10 |
| A1 | 1,120 | 888 | −232 |
| A2 | 634 | 528 | −106 |
| B1+ | 316 | 565 | +249 |

Read: yield remains thousands-scale and strongly accusative-heavy. Manifest
growth (8,552 entries, 2,799 lemmas with supported targets) and fresher Tatoeba
exports moved some mass into B1/B2 while A1/A2 stayed the majority (1,416 /
1,981). Locative remains sparse under the strict `у/в` / `на` triggers.

Committed artifacts from this retry:

* Machine summary: `docs/atlas/tatoeba-cloze-yield-phase1-retry.json`
* Stratified 30-row quality sample: `docs/atlas/tatoeba-cloze-sample.json`
* Full candidate JSON stays local under `.agent/tmp/tatoeba/` (review-only; not live)

CLI improvements shipped with this retry (no Phase-3 go-live):

* `--default-license` + `--cc0-sentences` for detailed Tatoeba exports
* `--yield-report` JSON/Markdown writer
* `--progress-every` stderr progress
* Fail-closed missing-path checks (manifest / Tatoeba files / `data/vesum.db`)
* Faster links streaming for the ~28M-row export

## Phase 1.5 (post-fix) - 2026-06-26

### Inputs

Same real-data setup as Phase 1, rerun in worktree
`/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/tatoeba-cloze-fix-3797`.
The hydrated manifest was symlinked from the main checkout at
`site/src/data/lexicon-manifest.json`; `data/vesum.db` and `data/sources.db`
were symlinked from the main checkout. Real Tatoeba exports were downloaded
fresh into `.agent/tmp/tatoeba/` on 2026-06-26:

* `ukr_sentences_detailed.tsv.bz2`
* `eng_sentences_detailed.tsv.bz2`
* `links.tar.bz2`
* `sentences_CC0.tar.bz2`

The detailed sentence exports still omit explicit license strings, so the same
scratch-only augmentation as Phase 1 appended `CC0` for sentence IDs present in
`sentences_CC0.csv` and `CC-BY 2.0 FR` otherwise. Augmented counts match Phase 1:
Ukrainian `CC0=393`, `CC-BY 2.0 FR=188,212`; English `CC0=41,487`,
`CC-BY 2.0 FR=1,985,925`. `read_tatoeba_pairs` loaded 217,297 linked UK-EN
pairs.

### Fixes Applied

The real manifest case shape was confirmed from
`enrichment.morphology.paradigm.cases`: keys are Ukrainian grammatical labels
`називний`, `родовий`, `давальний`, `знахідний`, `орудний`, `місцевий`,
`кличний`, while each case still uses English number keys such as `singular` and
`plural`. The generator now maps supported case rules to those manifest labels:
`accusative_direct_object -> знахідний`; `locative_static_u -> місцевий`;
`locative_static_na -> місцевий`. Output and VESUM validation still use the
canonical case names `accusative` and `locative`.

Filter tuning:

* Sentence CEFR now uses known token lemmas and tolerates up to 4 unknown content
  tokens before rejecting the sentence as `sentence_cefr_unknown`.
* Default sentence length widened from 4-12 words to 3-16 words.
* Russianism prescreen is now conservative: it hard-drops only explicit
  high-confidence Russian tokens in the fixed regex, not every broad
  russian-shadow checker hit.
* Review caps were relaxed so this report reflects the real accepted fixed-filter
  yield instead of trimming most accepted examples at `max_per_lemma_case_rule=3`.

### Final Fixed Run

| Metric | Count |
| --- | ---: |
| Pairs processed | 217,297 |
| Candidates emitted | 2,070 |
| Candidate license `CC-BY 2.0 FR` | 2,070 |
| Candidate license `CC0` | 0 |

By case rule:

| caseRuleId | Candidates |
| --- | ---: |
| `accusative_direct_object` | 2,000 |
| `locative_static_u` | 37 |
| `locative_static_na` | 33 |

By emitted sentence CEFR:

| CEFR | Candidates |
| --- | ---: |
| A1 | 1,120 |
| A2 | 634 |
| B1 | 141 |
| B2 | 173 |
| C1 | 2 |
| C2 | 0 |

Full rejection breakdown:

| Rejection | Count |
| --- | ---: |
| `blocked_register` | 56 |
| `exact_duplicate` | 454 |
| `multiword_lemma` | 993 |
| `near_duplicate` | 1,253 |
| `russianism_prescreen` | 195 |
| `sentence_cefr_above_word` | 2,370 |
| `sentence_cefr_unknown` | 14,872 |
| `sentence_length` | 20,078 |
| `single_target_occurrence` | 131 |
| `surface_equals_lemma` | 947 |
| `target_punctuation_or_multiword` | 2,017 |
| `unsupported_trigger` | 11,533 |
| `vesum_ambiguous` | 14,897 |

Raw generator stdout:

```text
wrote 2070 candidates to .agent/tmp/tatoeba/candidates-fixed-full.json
rejected.blocked_register=56
rejected.exact_duplicate=454
rejected.multiword_lemma=993
rejected.near_duplicate=1253
rejected.russianism_prescreen=195
rejected.sentence_cefr_above_word=2370
rejected.sentence_cefr_unknown=14872
rejected.sentence_length=20078
rejected.single_target_occurrence=131
rejected.surface_equals_lemma=947
rejected.target_punctuation_or_multiword=2017
rejected.unsupported_trigger=11533
rejected.vesum_ambiguous=14897
```

### Deltas vs Phase 1

The mandatory real-manifest baseline in Phase 1 emitted 0 candidates because the
generator looked up English case IDs in a manifest keyed by Ukrainian case
labels. The Phase 1 scratch normalized estimate, which manually added English
case aliases, emitted 155 candidates. Phase 1.5 emits 2,070 candidates from the
real manifest without scratch aliasing.

| Metric | Phase 1 scratch estimate | Phase 1.5 fixed | Delta |
| --- | ---: | ---: | ---: |
| Total candidates | 155 | 2,070 | +1,915 |
| `accusative_direct_object` | 146 | 2,000 | +1,854 |
| `locative_static_u` | 6 | 37 | +31 |
| `locative_static_na` | 3 | 33 | +30 |
| A1 candidates | 90 | 1,120 | +1,030 |
| A2 candidates | 43 | 634 | +591 |
| B1 candidates | 17 | 141 | +124 |
| B2 candidates | 5 | 173 | +168 |

Filter deltas against the Phase 1 scratch estimate:

| Rejection | Phase 1 | Phase 1.5 | Change |
| --- | ---: | ---: | ---: |
| `sentence_cefr_unknown` | 108,865 | 14,872 | -93,993 |
| `sentence_length` | 62,349 | 20,078 | -42,271 |
| `russianism_prescreen` | 14,233 | 195 | -14,038 |

Diagnostic variants before relaxing caps showed that increasing unknown-token
tolerance from 2 to 3 or 4 cut `sentence_cefr_unknown` substantially but added
only a small number of capped candidates. Raising the max length from 16 to 18
did not increase candidate yield. That means the original three filters were
real blockers, but after the fixes the remaining yield ceiling is mostly
downstream: `vesum_ambiguous`, `unsupported_trigger`, and the narrow supported
case-rule trigger set.

### Read

The total target is now in the thousands and strongly A1/A2-weighted
(1,754 of 2,070 candidates are A1/A2). However, yield is not balanced across the
three case rules: 2,000 candidates are accusative and only 70 are locative. The
locative lane remains low because relatively few Tatoeba sentences survive the
strict `у/в` and `на` trigger checks with an unambiguous VESUM locative form.

The refreshed committed sample at `docs/atlas/tatoeba-cloze-sample.json` contains
30 candidates: 15 accusative, 9 `locative_static_u`, and 6 `locative_static_na`;
19 A1, 5 A2, 3 B1, and 3 B2. Quality is good enough for a reviewed pilot, not
automatic publication. The same review concerns remain visible: Tatoeba English
translations often omit articles, some links are terse, and idioms such as
`мати рацію` can pass as accusative forms even though they are weak noun-case
practice.

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
