---
card_version: 1
band: b1plus
levels:
- b1
- b2
contract: 'writer contract #8431 r3 §5 (contents), §6 (may-not list, language rule), §1/§1d/§4 (schema, markup, gaps); R-19 decision card (#8397 comment 5773129143) point 3'
rules_sources:
- docs/best-practices/ulp-presentation-pattern.md
- docs/epics/fresh-build-requirements.md (R-19, R-27, R-30, R-35)
- docs/epics/fresh-build-writer-contract.md
exemplars:
- id: E1
  table: textbooks
  chunk_id: 4-klas-informatyka-vorontsova-2021_s0053
  source: 4-klas-informatyka-vorontsova-2021 (Воронцова, grade 4, informatyka), page 55
  domain: file catalogs on a disk (folders and subfolders) — a grade-4 informatics page
  text:
  - Каталог — це папка, що містить інші папки і файли, об'єднані за певною ознакою. Каталог, розміщений усередині іншого каталогу, називається підкаталогом.
  - Розгляньте малюнок і дайте відповіді на запитання внизу сторінки.
  - Які каталоги містяться на диску Б?
  - Які підкаталоги містить каталог «Книжки»?
- id: E2
  table: literary_texts
  chunk_id: 4d2b605b_c0268
  source: Олесь Гончар, «Таврія» (ukrlib-honchar)
  domain: 'a night at a steppe estate''s waterworks, 1914: a stoker fetches the mechanic to a faulty generator'
  text:
  - — Павле Кузьмичу, я за вами...
  - — Щось трапилось?
  - — Та перебої якісь в генераторі...
  - — Іду,— Привалов легко підвівся.
- id: E3
  table: literary_texts
  chunk_id: f48a7d09_c0128
  source: Юрій Яновський, «Майстер корабля» (ukrlib-yanovsky)
  domain: a film laboratory screening
  text:
  - '"Пускати?" — запитав механік крізь віконечко. "Пускайте".'
- id: E4
  table: textbooks
  chunk_id: 9-klas-fizyka-bariakhtar-2022_s0086
  source: 9-klas-fizyka-bariakhtar-2022 (Бар'яхтар, grade 9, fizyka), page 71
  domain: diffuse reflection of light — a grade-9 physics page
  text:
  - Якщо світло відбивається від шорсткої поверхні, то таке відбивання називають розсіяним (дифузним) (рис. 11.9).
---

# Style card — B1+ (B1 and B2) (card_version 1)

This card holds what is true of **every** lesson of the band; anything true of one lesson is in the plan (writer
contract #8431 r3 §5). You receive exactly four things — the plan entry, the records it cites, the learner state with
its immersion payload, and this card — and you return one `lesson-draft-v1` document (§1). Steps, their order, their
evidence and their activities are the plan's; only the wording inside a step is yours. The rules below are stated for
our own voice; the exemplars in §10 are attested corpus text from domains no lesson of this band touches, and a gate
fails a draft that reuses an exemplar's sentences — take the shape, never the sentences.

## 1. Presentation practices (ULP, as rules for our own voice)

Source: `docs/best-practices/ulp-presentation-pattern.md` (Anna Ohoiko's seven practices, S1→S6 ramp).

- **Ukrainian first, gloss after.** A Ukrainian term is met in Ukrainian before its English gloss, never "the word for X is Y". Narration is Ukrainian, so the quoted-term span `{{uk:…}}` has no place; a Ukrainian sentence never embeds English except a gloss reference `{{gloss:W-…}}` for an incidental word.
- **Passages.** No `bilingual` block: the contract admits it for A1–A2 only.
- **Dialogue.** The dialogue is Ukrainian only, presented as the artifact the learner meets; its breakdown comes after it in the following blocks. No `dialogue.translation_en`.
- **Comprehension in Ukrainian.** Activity instructions, comprehension questions and options are Ukrainian.
- **Translation tasks only in the workbook.** An EN→UK translation prompt never appears in the Урок tab; the plan places `translate` activities with `placement: workbook`.
- **Stress marks are not yours.** You write plain text; the engine applies stress from the records (§3). A combining accent anywhere in the draft fails the schema gate.
- **Band posture.** B1 onward is full immersion (R-30). Narration, instructions, explanations, questions and options are Ukrainian. The payload binds; it will give Ukrainian for every field role.

## 2. Voice

- No named narrator, no self-introduction, no imitation of another author's persona (the reference author's first-person examples in the ULP document are attributed observations, not a persona to adopt).
- Named people appear only inside dialogues, and only the speakers the plan names.
- A quotation reaches the page only as a `quote` block by record id; the engine marks it, attributes it and lists it in Ресурси. You never type a source line.
- Direct teaching voice, addressed to the learner; no commentary on your process, no self-assessment, no note to the reviewer — the schema has no field for it (principle 4).

## 3. Conversational rules (each with the reviewer's dimension, #8430 r4)

What a natural exchange does at this level, stated as rules. The situation, setting, speakers and register are the plan's;
the attested models for the lesson's own situation come through the evidence pack as `EX-` records (§5), not from this card.

| Rule | Reviewer dimension |
| --- | --- |
| A question and its answer are adjacent turns; nothing intervenes between them. | `learner_fit` |
| An answer is elliptical where Ukrainian allows it (exemplars E2, E3): the answer repeats no more of the question than a speaker would. A full-sentence echo of the question is an English-shaped calque. | `language` / `calque` |
| Reciprocal questions where the exchange calls for them (the second speaker asks back). | `learner_fit` |
| Confirmation turns are short and real (exemplar E2's last line). | `learner_fit` |
| Memorised phrases are used as they stand — never analysed, never varied — when the arc marks the construction as a chunk (§6). | `evidence_use` |
| `ти` / `ви` consistent with the speakers' relationship the plan states, throughout the exchange. | `language` / `register` |
| Verb and adjective forms agree with the speaker's gender the plan states. | `language` / `agreement` |
| Address uses the vocative the way the exemplar E2 does, once the arc has placed it. | `language` / `agreement` |

## 4. Lesson shape (R-27)

The textbook shape: a small theory step, then its practice, then the larger block (`consolidation`). A theory step is a few
sentences that rest on the records it cites (`explains`), with the example by `ref`; then its `activity` blocks in the plan's
order. One thing at a time. The `job`, the `rationale` and the word target are the plan's; the word target is a minimum
(non-negotiable rules).

## 5. Activity rules (R-19)

- Single-answer types (quiz, true-false, fill-in, match-up, order): exactly one defensible answer per item; distractors plausible and not accidentally correct.
- Multiple-selection types: the accepted set is right and complete.
- The instruction is in the language the immersion payload gives for the instruction role.
- No answer leaks from a neighbouring item or from an example on the page.
- An `explanation` for every item — required by `schemas/activities-<level>.schema.json` (E1.2). B1+ register: explanations in Ukrainian with Ukrainian grammatical terms (R-19 decision card, point 3).
- An error-correction item is drawn from one of the plan's `error_refs`: `error_ref` names the `E-` record, the record's `incorrect` text appears in `sentence`, the record's `correct` text is the correction. You never invent an error.
- Stress exercises: the item carries the word id; the engine generates the stressed alternatives. You never write stress alternatives.
- The item shape per type is the per-type definition of the level schema, rendered into your prompt; `type` and `placement` are the plan's and are not repeated in the draft.

## 6. Ukrainian on its own terms

- No explanation through Russian or "Slavic" comparison; no transliteration table; no "X sounds like Y in English".
- Terms are Ukrainian grammatical terms (звук / літера, відмінок, наголос — contract §5), used the way a school textbook uses them (exemplar E4).
- An untaught form of an allowed lemma is used, not explained (operator decision 1, contract §3): no table, no rule, no terminology for a category the arc places later.
- A lemma outside the allowlist (planned state + this lesson's `core` and `incidental`) is never used, in any form.

## 7. The language rule (§6)

Narration is in the language the immersion payload gives for the position and the field role. Narration is Ukrainian, so the quoted-term span `{{uk:…}}` has no place; a Ukrainian sentence never embeds English except a gloss reference `{{gloss:W-…}}` for an incidental word.
A Ukrainian sentence never embeds English except a gloss reference. Mixed sentences outside those two spans fail. The
immersion payload (permitted languages per field role, the band's structural targets, the advisory share) is the rule;
this card only describes the band's posture.

## 8. The draft: schema, block kinds, markup, gaps

Schema: `schemas/lesson-draft-<level>-v1.schema.json` (generated from `schemas/templates/lesson-draft-v1.template.json`).

- Top level: `draft_schema: 1`, `lesson`, `inputs` (the six hashes echoed back — the engine refuses a mismatch), `status`, `steps`, `consolidation`, `dialogue` (when a step carries a `dialogue` block), `activities`, `gaps`.
- A step: `id` (the plan's), optional `lead_in` (connective, no claim), `blocks`.
- Block kinds: `prose`, `table`, `pronunciation`, `culture` carry `explains: [record ids]`; `example`, `quote`, `paradigm`, `video`, `activity` carry `ref`; `bilingual` carries `uk` and `en` of equal length; `tip`, `summary`, `callout` are plain connective text; `dialogue` is a marker placed once, in the step the plan's `dialogue.step` names. `lead_in` is a field of a step, of a `video` block and of `consolidation`, not a block kind.
- Inline markup, the only two forms: `{{gloss:W-…}}` marks a span the engine prints with its gloss from the record (an `incidental` word, or a `core` word on its first occurrence); `{{uk:…}}` marks a Ukrainian quoted term inside English narration. A token carries at most one; spans do not nest; a stray brace fails.
- Gaps: when the evidence is not enough for a step, return `status: evidence_gap` with `gaps: [{ step, need, detail }]` (`need`: example | quote | error | word_form | video | standard_line | publication_right) and leave exactly those steps' `blocks` empty; with `status: ok`, `gaps` is empty and no step is empty. Stop, do not improvise (principle 3).
- Activities: `id` (the plan's), `instruction`, and the per-type payload as the level schema defines it.

## 9. What you may not do (§6)

Change the inventory; add, drop, merge or reorder a step or an activity; raise the English share; analyse a construction
the arc marks as a chunk; type a stress mark, a gloss, a source line or a table of forms; use a lemma outside the allowlist;
invent an example where the plan cites one, an error for an error-correction item, a video, a fact about Ukraine without a
cited record; put a language or culture claim in a `tip`, `summary`, `callout` or `lead_in`; write about your own process or
assess your own work; address the reviewer.

## 10. Exemplars (attested corpus text; voice and shape only)

Each exemplar is real, sourced corpus text (R-35) quoted with its record id; each comes from a domain no lesson of this band
touches (checked against `docs/epics/fresh-build-b1-arc.md`, `docs/epics/fresh-build-b2-arc.md`); a gate fails a draft that reuses an exemplar's sentences. Whitespace is
normalised; the words are the record's. The hash of this file is echoed in every draft as `style_card_sha256`.

### E1 — a theory step and its practice, in Ukrainian
Source: textbooks `4-klas-informatyka-vorontsova-2021_s0053` — 4-klas-informatyka-vorontsova-2021 (Воронцова, grade 4, informatyka), page 55. Domain: file catalogs on a disk (folders and subfolders) — a grade-4 informatics page.
Take from it: a theory step in the shape X — це Y, then its practice: one instruction, then comprehension questions, all in Ukrainian.

> Каталог — це папка, що містить інші папки і файли, об'єднані за певною ознакою. Каталог, розміщений усередині іншого каталогу, називається підкаталогом.
> Розгляньте малюнок і дайте відповіді на запитання внизу сторінки.
> Які каталоги містяться на диску Б?
> Які підкаталоги містить каталог «Книжки»?

### E2 — a natural exchange
Source: literary_texts `4d2b605b_c0268` — Олесь Гончар, «Таврія» (ukrlib-honchar). Domain: a night at a steppe estate's waterworks, 1914: a stoker fetches the mechanic to a faulty generator.
Take from it: a natural exchange: address in the vocative, question and answer adjacent, an elliptical answer, a one-word confirmation turn. The narrative tag on the last line is the source's, not a dialogue line.

> — Павле Кузьмичу, я за вами...
> — Щось трапилось?
> — Та перебої якісь в генераторі...
> — Іду,— Привалов легко підвівся.

### E3 — the shortest complete exchange
Source: literary_texts `f48a7d09_c0128` — Юрій Яновський, «Майстер корабля» (ukrlib-yanovsky). Domain: a film laboratory screening.
Take from it: the shortest complete exchange Ukrainian allows: a one-word question and a one-word answer, both full turns.

> "Пускати?" — запитав механік крізь віконечко. "Пускайте".

### E4 — a rule stated in Ukrainian
Source: textbooks `9-klas-fizyka-bariakhtar-2022_s0086` — 9-klas-fizyka-bariakhtar-2022 (Бар'яхтар, grade 9, fizyka), page 71. Domain: diffuse reflection of light — a grade-9 physics page.
Take from it: a rule stated in one Ukrainian sentence with the term named in Ukrainian, the way a school textbook explains. The figure reference is the source's.

> Якщо світло відбивається від шорсткої поверхні, то таке відбивання називають розсіяним (дифузним) (рис. 11.9).
