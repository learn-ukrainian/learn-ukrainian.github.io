# Open Model Data — Roadmap

> **Parent epic:** [#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321).
> **Rewritten 2026-09-20** after a review of the whole epic, by operator decision. The earlier
> version of this file planned "250,000 SFT + 50,000 DPO" records; that plan is withdrawn. The
> filename is kept only because older issues and pull requests link to it.
> **Policy:** non-commercial, permanent, free and open.

## 1. What we are building

A free, open dataset that teaches an AI model to speak **proper modern Ukrainian** — clean literary
language, real Ukrainian idioms, correct grammar — **without Russian, Soviet or other colonial
poisoning**. Each item is a question plus a good answer. Anyone training an open model may use it.

## 2. Why the earlier plan was withdrawn

The earlier plan made a record count the goal, so the work chased the count. Scripts placed source
sentences into a small number of fill-in-the-blank forms, many thousands of times. Measured on
2026-09-20 on the files in `data/projects/open_model_data/release/`:

| Set | Lines | What they contain |
| --- | --- | --- |
| `uldr_v06_general_assistant` (#8139) | 75,000 | 4,220 different question–answer pairs, copied (one of them 398 times) under different IDs; one reasoning pattern for all lines |
| `uldr_v05_grammar_valency` (#8143) | 35,000 | 32,629 correct sentences answered "nothing wrong here"; 2,371 real corrections; nine of twenty error types have fewer than 50 examples |
| `uldr_v04a_kyivan_rus` (#8103) | 10,000 | 467 records give two different datings for the same inscription; five question patterns cover 94% |
| `uldr_v04b_middle_ukrainian` (#8105) | 10,000 | three reasoning patterns for all 10,000 records |

No model has been trained on this data and checked. Issue #8054 ("alignment training and 5-gate
evaluation") closed with a test harness only. The one training result on file (Phase 3.6 pilot,
#8010) cannot be relied on: its saved model file has 4 layers of width 256, where the model it names
has 34 layers of width 2,560, and its training log carries the same final fingerprint at every step.

A model trained on such data learns the form letter, not the language.

## 3. Rules

1. **No count targets.** A set is as large as its sources honestly support, and every example is
   different from the others.
2. **Every "this is a Russianism — say it this way" rests on a named authority** (rule 4). Never a
   script's or an AI's guess. Inventing "corrections" of good Ukrainian is its own kind of poison.
3. **The Soviet-era dictionary (СУМ-11) is evidence of distortion only.** It fails in two directions:
   - *What it left out.* A large part of real Ukrainian vocabulary was never admitted. A word being
     absent from it means nothing — no script may treat that as a sign the word is rare, dialectal,
     archaic or wrong.
   - *What it put in.* Russianisms were added and given ordinary entries. A word being present does
     not make it authentic, and its labels ("dialectal", "obsolete", "colloquial") are not copied.
4. **Ukrainian is explained in Ukrainian, from sources Ukrainian scholarship accepts.** The meaning
   of a word comes only from a Ukrainian explanatory dictionary — never from a translation
   dictionary in any language, and never from the Soviet dictionary. Which source answers which
   question is already decided by the project and is not restated here: see the table in
   [`agents_extensions/shared/rules/ukrainian-linguistics.md`](../../../agents_extensions/shared/rules/ukrainian-linguistics.md) §4.
   That list is changed only by the operator and the language reviewers. If no accepted source
   explains a word, no example is made for it.
5. **Ukrainian language judgment belongs to the language reviewers.** Infrastructure agents do not
   decide what is correct Ukrainian.
6. **A set is accepted only when** it has almost no repeats, no handful of patterns covering most
   of it, a drawn sample approved by an independent language reviewer, and test questions written
   by someone other than the author of the training examples. The check is built in #8339.
7. **Proof before volume.** A small model is really trained and measured (#8338) before more data
   is built.
8. **Rights.** Dictionaries, textbooks and corpora are other people's work. Crediting them is
   required but is not permission. Nothing that reproduces a source's own text is released until
   the right to do so is recorded for that source. Crediting follows
   [`docs/best-practices/atlas-source-presentation.md`](../../best-practices/atlas-source-presentation.md).

## 4. Work, in order

| Order | Work | Issue |
| --- | --- | --- |
| 1 | First real training run and honest scorecard | #8338 |
| 1 | Acceptance check for every dataset | #8339 |
| 2 | Real Ukrainian idioms — one checked example per dictionary idiom. Release waits for the Academy institute's permission | #8140 |
| 2 | Russianisms and Soviet officialese — cases from accepted sources, confirmed by reviewers | #8340 |
| 3 | Grammar — real corrections outweigh "nothing wrong" examples | #8342 |
| 3 | School-subject answers — real explanations, no copies | #8341 |
| 4 | Dialects — small and cautious, attested entries only | #8141 |
| — | Set aside the historical files | #8343 |
| hold | Assemble one release | #8330 |
| hold | Independent final test set and training recipes | #8331 |

Items on hold start only when the sets above pass rule 6 and the scorecard from #8338 exists.

## 5. Later, with experts

Kyivan Rus and Middle Ukrainian texts are **out of the training data for now**. They are mixed with
Church Slavonic, chancery language, Polish and Latin; sorting them needs a historical linguist, and
the project has none yet. The source texts stay in the database untouched. What stays in scope is the
protective side only: test questions that check the model does **not** "correct" a quotation from an
old text into modern language.

When an expert is available, this reopens as a small, expert-checked set.

## 6. What remains valid from the earlier work

Source custody and rights records, the wall between training and test data, record formats, file
sharding, receipts, the evaluation harness, and the five qualification gates in
[`PRODUCTION_RELEASE_PLAN.md`](PRODUCTION_RELEASE_PLAN.md) §3.2. The gates stay; what changes is
that a real trained model must be measured against them, on test questions the training-data
generators did not write.
