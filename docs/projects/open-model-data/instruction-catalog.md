# E10 instruction catalog — draft 0.1.0

Issue #9611; parent #6321. Author: GPT-6.1 Sol, Codex.
Tool checkpoint: 2026-10-03T18:43:55Z (`date -u`).
This is a **draft**, with `training_eligible: false`, not PA6 approval.
The brief and approved plan v3.4.4 require C1–C9; the issue still counts C1–C8.
The driver must reconcile that denominator before closeout.

[Catalog](../../../registry/projects/open_model_data/instruction_catalog.yaml) ·
[Draft schema](../../../registry/projects/open_model_data/instruction_catalog.schema.json) ·
[Canonical plan](PLAN.md)

The plan-body SHA-256, from
`sed '1,/^-->$/d' docs/projects/open-model-data/PLAN.md | sha256sum`, is
`2d5db0ae7d15336b61c361c1dacdf89c3c9811cfd0109acc8f156f16149e94e1`.

## Scope, counts and source bindings

Only `components.*.instructions[].template` is project-written training text.
Control metadata, this document and tool quotes must not be exported.
There is no authored answer, explanation, reasoning or worked solution.
The JSON Schema Draft 2020-12 follows existing repository contract conventions.
It checks draft structure; it cannot certify source relationships or Ukrainian
quality. No production helper or existing acceptance checker changes here.

| Component | Lines | Coverage |
| --- | ---: | --- |
| C1 | 8 | Aligned human sentence correction. |
| C2 | 8 | Agreed form, with lemma, homonym/sense, slot and variant identity. |
| C3 | 16 | Eight synonym prompts and eight antonym prompts. |
| C4 | 8 | Verbatim dictionary definition, with same-entry citation binding. |
| C5 | 8 | Retrieve the printed rule for its own printed example. |
| C6 | 16 | Eight human sentence-correction prompts and eight printed book-replacement prompts. |
| C7 | 8 | Select the modern-attested side of an admitted opt-in contrast pair. |
| C8 | 8 | Printed normative/admissible transcription and the book's own verdict. |
| C9 | 8 | Verbatim section headed by the textbook's own title. |
| **Total** | **88** | **9 components, 11 operations.** |

Each operation has eight distinct lexical starts. Balanced use gives top1 =
12.5% and top5 = 62.5%. This is compact enough for line-by-line review and
supports the proposed bounds below. Six starts would have balanced top5 =
83.3%. C3 and C6 need separate eight-line sets for their different operations;
four per operation would make a five-prefix bound meaningless. This count
does not claim eight distinct reasoning skills or model generalization.

Slots are the **field roles named in the plan's component bindings**, not
guessed physical database column names. E4 must authenticate adapters and
the exact source row/field locators before rendering. Use single-pass exact
interpolation: no inflection, paraphrase, truncation, added stress, synonym
substitution or recursive expansion. Braces in source values remain literal
data. Missing, ambiguous or inapplicable fields withhold the record.
Source context and targets use only the fixed E4/E5 serialization schema;
this catalog authorizes no new free-text answer or context.

- **C1:** learner sentence ↔ human-corrected sentence, same document/annotator.
  All document annotations and both UA-GEC layers stay together.
- **C2:** preserve the P3 tuple and variant identity as lossless metadata.
  Copy the source's grammatical label; never expand it into an authored
  description. Omit all P3 exclusions and single-source forms.
- **C3:** copy a source-readable sense label, not a gloss invented from a
  numeric sense ID. Withhold this draft operation if the source has no
  printable disambiguating label; the group must belong to that sense.
- **C4:** the target definition and supporting citation come from one entry.
  No generated usage example; exclude ruler-overlapping citations.
- **C5:** prompts request the cited paragraph's verbatim rule, not correction
  of the example. The example must be printed in that paragraph. Ambiguous
  examples need their paragraph locator in serialized input context.
- **C6:** UA-GEC targets are aligned human-corrected sentences. Book targets
  are explicitly printed replacements from the same passage, with individual
  Sol and Opus pair sign-off. No invented sentence bridges the two forms.
- **C7:** no interpolation slots: the plan does not name printable pair
  fields. The admitted #8982 pair is mandatory lossless input context, with
  contemporary-source and Soviet-context roles. SUM-11 is never normative;
  arbitrary unadjudicated pairs, the default split and pretraining are refused.
- **C8:** the word and phonetic context must be printed in the source. Require
  its transcription, supporting span, same-paragraph quoted verdict,
  rule/page and ULIF stress cross-check. Target only a printed normative or
  admissible transcription plus the book's verdict. A non-norm transcription
  occurs only on the serialized rejected side of a printed contrast.
  Non-norm-only paragraphs, ambiguous status and stress mismatches are
  withheld; this operation never invents a normative answer.
- **C9:** the slot is only the book's own section title; target is its complete
  verbatim headed section, not a summary. The printed-question/printed-answer
  route uses source text directly. Withhold unkeyed exercises, tables of
  contents and OCR-damaged text.

The draft schema requires every component, exact operation counts, declared
slot sets and no extra fields. It refuses invented placeholder names and
eligible/approved status. Relationship, real-slot applicability and later
rendered-record integrity remain E4/E5 gates, not schema conclusions.

## Proposed prefix metric: instruction-prefix.v1-draft

This is a **proposal**, not the final PA6 threshold. The driver must freeze
metric, catalog version/hash and threshold after two non-author reviews and
before E12. Prior art: the existing `check_2_form_letters` in
`scripts/projects/open_model_data/audit_dataset_acceptance.py` uses frequency
counts of delexicalized queries/answers. That whole-text measure cannot prove
instruction diversity and is not replaced or modified by this draft.

1. Validate each exported record's catalog version/hash and instruction ID.
   Re-render authenticated source fields and compare the instruction byte for
   byte. Unknown IDs, changed literals, missing source spans/locators or extra
   authored text fail the relationship gate before concentration.
2. Use the matched template, replacing every placeholder with the same atomic
   `SLOT` marker. Placeholder names and filled values create no new prefixes.
   Exclude serialized source context, source questions, targets, quotations
   and reasoning from this counter. A book's original printed question is
   `source_question`, with a separate denominator, never catalog diversity.
3. Only for metric comparison: NFC, Unicode casefold and U+0027 apostrophe →
   U+2019. Tokens are `SLOT` or Unicode letter runs allowing an internal
   apostrophe; punctuation/whitespace separate them. No stemming, model
   tokenizer or language-model judgment; exported source bytes stay untouched.
4. Count first **one** and first **four** tokens independently. A shorter
   template contributes its full tuple; never pad with source text or omit it.
   Each catalog-instructed exported record contributes once; no deduplication.
   Records containing multiple catalog IDs are outside this draft and fail closed.
5. For each **(component, operation, exported split)** bucket, N is the actual
   catalog-instructed record count. Sort prefix frequencies n_i descending:
   `top1 = max(n_i)/N`; `top5 = sum(five largest n_i)/N`, or all if fewer
   than five. Report N, distinct prefixes, both shares at both lengths, and
   instruction-ID shares. Whole-split totals are diagnostic; pooling cannot
   rescue a failing operation. C7 remains a separate opt-in split.
6. Proposed bounds: **top1 ≤ 0.15 and top5 ≤ 0.65**, at both prefix lengths
   **and for instruction-ID frequencies**. Compare exact ratios without
   rounding. N = 0 is missing required coverage, never PASS; N < 8 is
   insufficient evidence. If integer counts cannot meet the bounds, withhold
   the build; never round up allowances or manufacture source records.
7. Source-text diversity is an independent report over verbatim source
   units/fingerprints/locators, with its own denominator. Distinct sentences
   under one instruction still have top1 = top5 = 1 here. Report instruction
   origin counts against the frozen component manifest so source questions
   cannot silently substitute for catalog records to evade the gate.

15%/65% allows 2.5 percentage points above balanced eight-start use while
preventing a dominant prompt or five prompts covering roughly 85%. The
issue's 85.4% finding motivates separation; it is not a measurement of this
metric. These are anti-concentration bounds, not confidence intervals or
semantic proof. D4's independent sealed evaluation remains necessary.

Before any build, test feasibility against admitted records and available
source fields without reading the sealed final ruler. Schedule only
semantically eligible instructions deterministically under a frozen version;
never rewrite, duplicate or rebind sources to pass. A dropped line or an
eligibility stratum with too few prefixes returns to the driver before freeze.

### E5-backed fixtures required after this draft

| Fixture | Expected |
| --- | --- |
| 100 distinct sentences under one catalog template | FAIL: top1 = top5 = 1 despite source diversity. |
| Eight templates used equally across 800 records | Proposed arithmetic passes: 0.125 / 0.625. |
| Eight balanced IDs all starting with one lexical token | FAIL at prefix length one. |
| Good C1 pooled with single-template C6 | FAIL for C6; no pooled rescue. |
| C7 included in default split | Split/relationship refusal. |
| N = 0 or N < 8 | Missing coverage or insufficient evidence, never PASS. |
| Unknown ID, changed literal, fake locator or missing span | Relationship refusal before counting prefixes. |
| Source slots containing braces, quotes or newlines | Single-pass literal data, never recursive interpolation. |

**AC4's production checker test is pending E5.** The smoke check below
exercises schema and catalog-prefix arithmetic, not the exported-record
checker or independent held-out proof. This author has not inspected the
evaluation steward's sealed final set.

## Draft validation

Executed from the assigned worktree with the prescribed shared interpreter:

- The reproducible smoke block below returned
  `PASS: schema; 9 components; 88 IDs; 11 operations; 22 prefix projections; 8 rejected mutations`.
- `-m yamllint registry/projects/open_model_data/instruction_catalog.yaml`
  exited 0 with no output after three long metadata lines were folded.
- `-m ruff check --stdin-filename instruction_catalog_smoke.py -` on the
  extracted smoke block returned `All checks passed!` after using the
  component variable in an ID assertion.
- `git diff --check` returned no whitespace errors.

These are author-side draft checks; the two independent reviews, production
checker test and acceptance proof remain pending.

## Quoted sources-MCP evidence

VESUM attests forms, not sentence naturalness. Russian shadow is suspicion,
not a calque verdict. Антоненко-Давидович is lexical/style evidence, not a
substitute for Правопис or modern morphology. Both book-search surfaces were
queried per line. Empty searches are not approval; returned keyword candidates
often do not attest the entire phrase. Counts are capped retrieval results,
not counts of all book matches. Non-author semantic/grammar review is pending.

Authored tokens were lowercased for case-sensitive VESUM lookup while catalog
sentence capitalization is preserved. An initial capitalized imperative
probe missed forms; the lowercase/verb-filter calls resolved those misses.
Unknown future slot contents must be verified at record build, not fabricated
as examples here.

### Every authored word: verify_words

Call: `verify_words(words=<122 distinct authored tokens>)`.
Exact tool text:

```text
344 analyses (108 distinct lemmas)

Batch verification: 122 words

Found: 122/122

- **абзацу** — FOUND (3 analyses (1 distinct lemma)): абзац(noun), абзац(noun), абзац(noun)
- **або** — FOUND (1 analysis (1 distinct lemma)): або(conj)
- **антоніми** — FOUND (3 analyses (1 distinct lemma)): антонім(noun), антонім(noun), антонім(noun)
- **без** — FOUND (1 analysis (1 distinct lemma)): без(prep)
- **в** — FOUND (1 analysis (1 distinct lemma)): в(prep)
- **варіант** — FOUND (2 analyses (1 distinct lemma)): варіант(noun), варіант(noun)
- **виділи** — FOUND (5 analyses (3 distinct lemmas)): виділ(noun), виділ(noun), виділ(noun)
- **визнає** — FOUND (2 analyses (2 distinct lemmas)): визнавати(verb), визнати(verb)
- **вимови** — FOUND (4 analyses (1 distinct lemma)): вимова(noun), вимова(noun), вимова(noun)
- **вимовляти** — FOUND (1 analysis (1 distinct lemma)): вимовляти(verb)
- **вимову** — FOUND (1 analysis (1 distinct lemma)): вимова(noun)
- **виправ** — FOUND (3 analyses (3 distinct lemmas)): виправа(noun), виправити(verb), випрати(verb)
- **виправлене** — FOUND (3 analyses (1 distinct lemma)): виправлений(adj), виправлений(adj), виправлений(adj)
- **виправлений** — FOUND (3 analyses (1 distinct lemma)): виправлений(adj), виправлений(adj), виправлений(adj)
- **вислову** — FOUND (3 analyses (1 distinct lemma)): вислів(noun), вислів(noun), вислів(noun)
- **вислів** — FOUND (2 analyses (1 distinct lemma)): вислів(noun), вислів(noun)
- **вкажи** — FOUND (1 analysis (1 distinct lemma)): вказати(verb)
- **відповідає** — FOUND (1 analysis (1 distinct lemma)): відповідати(verb)
- **відповідне** — FOUND (3 analyses (1 distinct lemma)): відповідний(adj), відповідний(adj), відповідний(adj)
- **відредагуй** — FOUND (1 analysis (1 distinct lemma)): відредагувати(verb)
- **відтвори** — FOUND (1 analysis (1 distinct lemma)): відтворити(verb)
- **для** — FOUND (1 analysis (1 distinct lemma)): для(prep)
- **до** — FOUND (15 analyses (1 distinct lemma)): до(noun), до(noun), до(noun)
- **добери** — FOUND (2 analyses (2 distinct lemmas)): дібрати(verb), добрати(verb)
- **допустимо** — FOUND (2 analyses (2 distinct lemmas)): допустимо(adv), допустити(verb)
- **допустимою** — FOUND (1 analysis (1 distinct lemma)): допустимий(adj)
- **допустиму** — FOUND (1 analysis (1 distinct lemma)): допустимий(adj)
- **з** — FOUND (1 analysis (1 distinct lemma)): з(prep)
- **за** — FOUND (3 analyses (1 distinct lemma)): за(adv), за(part), за(prep)
- **заміни** — FOUND (5 analyses (2 distinct lemmas)): заміна(noun), заміна(noun), заміна(noun)
- **замінити** — FOUND (1 analysis (1 distinct lemma)): замінити(verb)
- **заміну** — FOUND (1 analysis (1 distinct lemma)): заміна(noun)
- **записати** — FOUND (1 analysis (1 distinct lemma)): записати(verb)
- **запиши** — FOUND (1 analysis (1 distinct lemma)): записати(verb)
- **значення** — FOUND (7 analyses (1 distinct lemma)): значення(noun), значення(noun), значення(noun)
- **значенні** — FOUND (1 analysis (1 distinct lemma)): значення(noun)
- **його** — FOUND (31 analyses (4 distinct lemmas)): він(noun), він(noun), воно(noun)
- **кальки** — FOUND (4 analyses (1 distinct lemma)): калька(noun), калька(noun), калька(noun)
- **калькований** — FOUND (6 analyses (1 distinct lemma)): калькований(adj), калькований(adj), калькований(adj)
- **калькою** — FOUND (1 analysis (1 distinct lemma)): калька(noun)
- **кальку** — FOUND (1 analysis (1 distinct lemma)): калька(noun)
- **книжка** — FOUND (1 analysis (1 distinct lemma)): книжка(noun)
- **книжкою** — FOUND (1 analysis (1 distinct lemma)): книжка(noun)
- **контексті** — FOUND (1 analysis (1 distinct lemma)): контекст(noun)
- **котра** — FOUND (1 analysis (1 distinct lemma)): котрий(adj)
- **має** — FOUND (2 analyses (2 distinct lemmas)): мати(verb), маяти(verb)
- **містить** — FOUND (2 analyses (1 distinct lemma)): містити(verb), містити(verb)
- **наведене** — FOUND (3 analyses (1 distinct lemma)): наведений(adj), наведений(adj), наведений(adj)
- **наведено** — FOUND (1 analysis (1 distinct lemma)): навести(verb)
- **наведеного** — FOUND (3 analyses (1 distinct lemma)): наведений(adj), наведений(adj), наведений(adj)
- **наведеному** — FOUND (4 analyses (1 distinct lemma)): наведений(adj), наведений(adj), наведений(adj)
- **наведеної** — FOUND (1 analysis (1 distinct lemma)): наведений(adj)
- **наведеній** — FOUND (2 analyses (1 distinct lemma)): наведений(adj), наведений(adj)
- **наведи** — FOUND (1 analysis (1 distinct lemma)): навести(verb)
- **назви** — FOUND (5 analyses (2 distinct lemmas)): назва(noun), назва(noun), назва(noun)
- **написано** — FOUND (1 analysis (1 distinct lemma)): написати(verb)
- **нормативно** — FOUND (1 analysis (1 distinct lemma)): нормативно(adv)
- **нормативною** — FOUND (1 analysis (1 distinct lemma)): нормативний(adj)
- **нормативну** — FOUND (1 analysis (1 distinct lemma)): нормативний(adj)
- **нормі** — FOUND (2 analyses (1 distinct lemma)): норма(noun), норма(noun)
- **ньому** — FOUND (2 analyses (2 distinct lemmas)): він(noun), воно(noun)
- **обери** — FOUND (1 analysis (1 distinct lemma)): обрати(verb)
- **оцінку** — FOUND (1 analysis (1 distinct lemma)): оцінка(noun)
- **пари** — FOUND (11 analyses (2 distinct lemmas)): пар(noun), пар(noun), пар(noun)
- **парі** — FOUND (19 analyses (3 distinct lemmas)): пар(noun), пара(noun), пара(noun)
- **подай** — FOUND (1 analysis (1 distinct lemma)): подати(verb)
- **поданих** — FOUND (3 analyses (1 distinct lemma)): поданий(adj), поданий(adj), поданий(adj)
- **подано** — FOUND (1 analysis (1 distinct lemma)): подати(verb)
- **поданої** — FOUND (1 analysis (1 distinct lemma)): поданий(adj)
- **подає** — FOUND (2 analyses (1 distinct lemma)): подавати(verb), подавати(verb)
- **позначенню** — FOUND (2 analyses (1 distinct lemma)): позначення(noun), позначення(noun)
- **помилки** — FOUND (4 analyses (1 distinct lemma)): помилка(noun), помилка(noun), помилка(noun)
- **помилок** — FOUND (1 analysis (1 distinct lemma)): помилка(noun)
- **постав** — FOUND (5 analyses (4 distinct lemmas)): постав(noun), постав(noun), постава(noun)
- **правило** — FOUND (4 analyses (2 distinct lemmas)): правило(noun), правило(noun), правило(noun)
- **правильно** — FOUND (1 analysis (1 distinct lemma)): правильно(adv)
- **правопис** — FOUND (2 analyses (1 distinct lemma)): правопис(noun), правопис(noun)
- **правопису** — FOUND (3 analyses (1 distinct lemma)): правопис(noun), правопис(noun), правопис(noun)
- **приклад** — FOUND (4 analyses (1 distinct lemma)): приклад(noun), приклад(noun), приклад(noun)
- **прикладом** — FOUND (2 analyses (1 distinct lemma)): приклад(noun), приклад(noun)
- **прикладу** — FOUND (6 analyses (2 distinct lemmas)): приклад(noun), приклад(noun), приклад(noun)
- **пропонує** — FOUND (1 analysis (1 distinct lemma)): пропонувати(verb)
- **процитуй** — FOUND (1 analysis (1 distinct lemma)): процитувати(verb)
- **підручника** — FOUND (2 analyses (1 distinct lemma)): підручник(noun), підручник(noun)
- **підручнику** — FOUND (3 analyses (1 distinct lemma)): підручник(noun), підручник(noun), підручник(noun)
- **разом** — FOUND (2 analyses (2 distinct lemmas)): раз(noun), разом(adv)
- **речення** — FOUND (7 analyses (1 distinct lemma)): речення(noun), речення(noun), речення(noun)
- **реченні** — FOUND (1 analysis (1 distinct lemma)): речення(noun)
- **розділ** — FOUND (2 analyses (1 distinct lemma)): розділ(noun), розділ(noun)
- **розділу** — FOUND (3 analyses (1 distinct lemma)): розділ(noun), розділ(noun), розділ(noun)
- **розділі** — FOUND (1 analysis (1 distinct lemma)): розділ(noun)
- **самого** — FOUND (6 analyses (2 distinct lemmas)): сам(adj), сам(adj), сам(adj)
- **синоніми** — FOUND (3 analyses (1 distinct lemma)): синонім(noun), синонім(noun), синонім(noun)
- **слова** — FOUND (4 analyses (1 distinct lemma)): слово(noun), слово(noun), слово(noun)
- **словник** — FOUND (2 analyses (1 distinct lemma)): словник(noun), словник(noun)
- **словникове** — FOUND (3 analyses (1 distinct lemma)): словниковий(adj), словниковий(adj), словниковий(adj)
- **словником** — FOUND (1 analysis (1 distinct lemma)): словник(noun)
- **слово** — FOUND (3 analyses (1 distinct lemma)): слово(noun), слово(noun), слово(noun)
- **сучасну** — FOUND (1 analysis (1 distinct lemma)): сучасний(adj)
- **сучасній** — FOUND (2 analyses (1 distinct lemma)): сучасний(adj), сучасний(adj)
- **також** — FOUND (1 analysis (1 distinct lemma)): також(adv)
- **текст** — FOUND (2 analyses (1 distinct lemma)): текст(noun), текст(noun)
- **тлумачення** — FOUND (7 analyses (1 distinct lemma)): тлумачення(noun), тлумачення(noun), тлумачення(noun)
- **тлумачить** — FOUND (2 analyses (1 distinct lemma)): тлумачити(verb), тлумачити(verb)
- **того** — FOUND (7 analyses (4 distinct lemmas)): те(noun), тога(noun), того(adv)
- **у** — FOUND (1 analysis (1 distinct lemma)): у(prep)
- **усунь** — FOUND (1 analysis (1 distinct lemma)): усунути(verb)
- **утвори** — FOUND (4 analyses (2 distinct lemmas)): утвір(noun), утвір(noun), утвір(noun)
- **форм** — FOUND (1 analysis (1 distinct lemma)): форма(noun)
- **форма** — FOUND (1 analysis (1 distinct lemma)): форма(noun)
- **форму** — FOUND (1 analysis (1 distinct lemma)): форма(noun)
- **формі** — FOUND (2 analyses (1 distinct lemma)): форма(noun), форма(noun)
- **цієї** — FOUND (1 analysis (1 distinct lemma)): цей(adj)
- **що** — FOUND (3 analyses (1 distinct lemma)): що(conj), що(noun), що(noun)
- **як** — FOUND (4 analyses (1 distinct lemma)): як(adv), як(conj), як(noun)
- **яка** — FOUND (3 analyses (2 distinct lemmas)): як(noun), як(noun), який(adj)
- **яке** — FOUND (2 analyses (1 distinct lemma)): який(adj), який(adj)
- **який** — FOUND (2 analyses (1 distinct lemma)): який(adj), який(adj)
- **якому** — FOUND (4 analyses (1 distinct lemma)): який(adj), який(adj), який(adj)
- **яку** — FOUND (3 analyses (2 distinct lemmas)): як(noun), як(noun), який(adj)
- **які** — FOUND (2 analyses (1 distinct lemma)): який(adj), який(adj)
- **із** — FOUND (1 analysis (1 distinct lemma)): із(prep)
```

### Imperatives: verify_words with pos_filter='verb'

This resolves noun/verb ambiguity obscured by the summary's first analyses.
The intended `виправити` analysis is `verb:perf:impr:s:2`, not the archaic
noun analysis. Exact tool text:

```text
20 analyses (20 distinct lemmas)

Batch verification: 16 words

Found: 16/16

- **виправ** — FOUND (2 analyses (2 distinct lemmas)): виправити(verb), випрати(verb)
- **подай** — FOUND (1 analysis (1 distinct lemma)): подати(verb)
- **запиши** — FOUND (1 analysis (1 distinct lemma)): записати(verb)
- **відредагуй** — FOUND (1 analysis (1 distinct lemma)): відредагувати(verb)
- **усунь** — FOUND (1 analysis (1 distinct lemma)): усунути(verb)
- **наведи** — FOUND (1 analysis (1 distinct lemma)): навести(verb)
- **утвори** — FOUND (1 analysis (1 distinct lemma)): утворити(verb)
- **добери** — FOUND (2 analyses (2 distinct lemmas)): дібрати(verb), добрати(verb)
- **вкажи** — FOUND (1 analysis (1 distinct lemma)): вказати(verb)
- **постав** — FOUND (2 analyses (2 distinct lemmas)): поставити(verb), постати(verb)
- **назви** — FOUND (1 analysis (1 distinct lemma)): назвати(verb)
- **відтвори** — FOUND (1 analysis (1 distinct lemma)): відтворити(verb)
- **заміни** — FOUND (1 analysis (1 distinct lemma)): замінити(verb)
- **обери** — FOUND (1 analysis (1 distinct lemma)): обрати(verb)
- **виділи** — FOUND (2 analyses (2 distinct lemmas)): виділити(verb), видіти(verb)
- **процитуй** — FOUND (1 analysis (1 distinct lemma)): процитувати(verb)
```

### Every authored word: check_russian_shadow

Each of the 122 tokens above was submitted individually as `word`.
The exact word-to-output groups are quoted below; all returned
`matches_russian: false`, but confidence values differ. This is not
phrase-level approval.

Words (119): `абзацу`, `або`, `антоніми`, `без`, `в`, `варіант`, `виділи`, `визнає`, `вимови`, `вимовляти`, `вимову`, `виправ`, `виправлене`, `виправлений`, `вислову`, `вкажи`, `відповідає`, `відповідне`, `відредагуй`, `відтвори`, `для`, `до`, `добери`, `допустимо`, `допустимою`, `допустиму`, `з`, `за`, `заміни`, `замінити`, `заміну`, `записати`, `запиши`, `значення`, `значенні`, `його`, `кальки`, `калькований`, `калькою`, `кальку`, `книжка`, `книжкою`, `контексті`, `котра`, `має`, `містить`, `наведене`, `наведено`, `наведеного`, `наведеному`, `наведеної`, `наведеній`, `наведи`, `назви`, `написано`, `нормативно`, `нормативною`, `нормативну`, `нормі`, `обери`, `оцінку`, `пари`, `парі`, `подай`, `поданих`, `подано`, `поданої`, `подає`, `позначенню`, `помилки`, `помилок`, `постав`, `правило`, `правильно`, `правопис`, `правопису`, `приклад`, `прикладом`, `прикладу`, `пропонує`, `процитуй`, `підручника`, `підручнику`, `разом`, `речення`, `реченні`, `розділ`, `розділу`, `розділі`, `самого`, `синоніми`, `слова`, `словник`, `словникове`, `словником`, `слово`, `сучасну`, `сучасній`, `також`, `текст`, `тлумачення`, `тлумачить`, `того`, `у`, `усунь`, `утвори`, `форм`, `форма`, `форму`, `формі`, `цієї`, `що`, `як`, `яка`, `яке`, `якому`, `яку`, `які`, `із`.

```json
{
  "matches_russian": false,
  "russian_lemma": null,
  "ukrainian_alternative": null,
  "confidence": 0.0
}
```

Words (1): `вислів`.

```json
{
  "matches_russian": false,
  "russian_lemma": null,
  "ukrainian_alternative": null,
  "confidence": 0.48497320061255744
}
```

Words (1): `ньому`.

```json
{
  "matches_russian": false,
  "russian_lemma": null,
  "ukrainian_alternative": null,
  "confidence": 0.3333379302736099
}
```

Words (1): `який`.

```json
{
  "matches_russian": false,
  "russian_lemma": null,
  "ukrainian_alternative": null,
  "confidence": 0.35714285714285715
}
```

### Spelling question: query_pravopys(topic='у-в')

The live tool returned these exact section-title lines:

> § 23.
> Позиції вживання прийменників і префіксів У та В

Its rule before `ф` covers fixed `у формі`; its vowel-to-consonant
rule covers `помилки в реченні`. Quotes must keep source slots unchanged;
real-value euphony still needs reviewer checking. The response identifies
`https://2019.pravopys.net/sections/23/`, an unofficial mirror.
This is the actual spelling response, not proof of PA2 or official E3b
ingestion; the driver must check official-source availability on review seats.

### Each line: forms, style index and full-book search

Every row quotes the final successful form-check `Found` line, the complete
style-search status, and the first book-search response line with locators.
The style query strips placeholders and adjacent punctuation from the
template; the book query wraps that string in double quotes and uses
`source_file='antonenko-davydovych-yak-my-hovorymo', limit=2`.
The search tool may broaden phrases; hits do not prove exact attestation.
All words in each line are covered by its VESUM call and the shadow groups.

| ID | verify_words | search_style_guide | search_text and chunk locators |
| --- | --- | --- | --- |
| C1.sentence_correction.01 | `Found: 4/4` | `No results in Антоненко-Давидович for: "Виправ помилки в реченні"` | `Found 2 results for: ""Виправ помилки в реченні""` — `antonenko-davydovych-yak-my-hovorymo_p059`, `antonenko-davydovych-yak-my-hovorymo_p070` |
| C1.sentence_correction.02 | `Found: 3/3` | `No results in Антоненко-Давидович for: "Подай виправлене речення"` | `Found 2 results for: ""Подай виправлене речення""` — `antonenko-davydovych-yak-my-hovorymo_p011`, `antonenko-davydovych-yak-my-hovorymo_p144` |
| C1.sentence_correction.03 | `Found: 4/4` | `No results in Антоненко-Давидович for: "Запиши речення без помилок"` | `Found 2 results for: ""Запиши речення без помилок""` — `antonenko-davydovych-yak-my-hovorymo_p117`, `antonenko-davydovych-yak-my-hovorymo_p153` |
| C1.sentence_correction.04 | `Found: 3/3` | `No results in Антоненко-Давидович for: "Відредагуй наведене речення"` | `Found 2 results for: ""Відредагуй наведене речення""` — `antonenko-davydovych-yak-my-hovorymo_p124`, `antonenko-davydovych-yak-my-hovorymo_p144` |
| C1.sentence_correction.05 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Усунь помилки в наведеному реченні"` | `Found 2 results for: ""Усунь помилки в наведеному реченні""` — `antonenko-davydovych-yak-my-hovorymo_p059`, `antonenko-davydovych-yak-my-hovorymo_p167` |
| C1.sentence_correction.06 | `Found: 4/4` | `No results in Антоненко-Давидович for: "Наведи виправлений варіант речення"` | `Found 2 results for: ""Наведи виправлений варіант речення""` — `antonenko-davydovych-yak-my-hovorymo_p152`, `antonenko-davydovych-yak-my-hovorymo_p144` |
| C1.sentence_correction.07 | `Found: 4/4` | `No results in Антоненко-Давидович for: "Речення запиши без помилок"` | `Found 2 results for: ""Речення запиши без помилок""` — `antonenko-davydovych-yak-my-hovorymo_p117`, `antonenko-davydovych-yak-my-hovorymo_p153` |
| C1.sentence_correction.08 | `Found: 4/4` | `No results in Антоненко-Давидович for: "Як правильно записати речення"` | `Found 2 results for: ""Як правильно записати речення""` — `antonenko-davydovych-yak-my-hovorymo_p014`, `antonenko-davydovych-yak-my-hovorymo_p113` |
| C2.agreed_form.01 | `Found: 3/3` | `No results in Антоненко-Давидович for: "Подай форму слова"` | `Found 2 results for: ""Подай форму слова""` — `antonenko-davydovych-yak-my-hovorymo_p023`, `antonenko-davydovych-yak-my-hovorymo_p101` |
| C2.agreed_form.02 | `Found: 4/4` | `No results in Антоненко-Давидович for: "Запиши слово у формі"` | `Found 2 results for: ""Запиши слово у формі""` — `antonenko-davydovych-yak-my-hovorymo_p070`, `antonenko-davydovych-yak-my-hovorymo_p089` |
| C2.agreed_form.03 | `Found: 4/4` | `No results in Антоненко-Давидович for: "Наведи форму для слова"` | `Found 2 results for: ""Наведи форму для слова""` — `antonenko-davydovych-yak-my-hovorymo_p101`, `antonenko-davydovych-yak-my-hovorymo_p023` |
| C2.agreed_form.04 | `Found: 3/3` | `No results in Антоненко-Давидович for: "Утвори форму слова"` | `Found 2 results for: ""Утвори форму слова""` — `antonenko-davydovych-yak-my-hovorymo_p023`, `antonenko-davydovych-yak-my-hovorymo_p101` |
| C2.agreed_form.05 | `Found: 3/3` | `No results in Антоненко-Давидович for: "Добери форму слова"` | `Found 2 results for: ""Добери форму слова""` — `antonenko-davydovych-yak-my-hovorymo_p023`, `antonenko-davydovych-yak-my-hovorymo_p101` |
| C2.agreed_form.06 | `Found: 3/3` | `No results in Антоненко-Давидович for: "Вкажи форму слова"` | `Found 2 results for: ""Вкажи форму слова""` — `antonenko-davydovych-yak-my-hovorymo_p023`, `antonenko-davydovych-yak-my-hovorymo_p101` |
| C2.agreed_form.07 | `Found: 4/4` | `No results in Антоненко-Давидович for: "Слово постав у форму"` | `Found 2 results for: ""Слово постав у форму""` — `antonenko-davydovych-yak-my-hovorymo_p101`, `antonenko-davydovych-yak-my-hovorymo_p024` |
| C2.agreed_form.08 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Яка форма слова відповідає позначенню"` | `Found 2 results for: ""Яка форма слова відповідає позначенню""` — `antonenko-davydovych-yak-my-hovorymo_p047`, `antonenko-davydovych-yak-my-hovorymo_p024` |
| C3.synonyms.01 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Подай синоніми до слова у значенні"` | `Found 2 results for: ""Подай синоніми до слова у значенні""` — `antonenko-davydovych-yak-my-hovorymo_p158`, `antonenko-davydovych-yak-my-hovorymo_p039` |
| C3.synonyms.02 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Запиши синоніми слова у значенні"` | `Found 2 results for: ""Запиши синоніми слова у значенні""` — `antonenko-davydovych-yak-my-hovorymo_p158`, `antonenko-davydovych-yak-my-hovorymo_p039` |
| C3.synonyms.03 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Наведи синоніми для слова у значенні"` | `Found 2 results for: ""Наведи синоніми для слова у значенні""` — `antonenko-davydovych-yak-my-hovorymo_p158`, `antonenko-davydovych-yak-my-hovorymo_p039` |
| C3.synonyms.04 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Добери синоніми до слова у значенні"` | `Found 2 results for: ""Добери синоніми до слова у значенні""` — `antonenko-davydovych-yak-my-hovorymo_p158`, `antonenko-davydovych-yak-my-hovorymo_p039` |
| C3.synonyms.05 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Вкажи синоніми слова у значенні"` | `Found 2 results for: ""Вкажи синоніми слова у значенні""` — `antonenko-davydovych-yak-my-hovorymo_p158`, `antonenko-davydovych-yak-my-hovorymo_p039` |
| C3.synonyms.06 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Назви синоніми до слова у значенні"` | `Found 2 results for: ""Назви синоніми до слова у значенні""` — `antonenko-davydovych-yak-my-hovorymo_p158`, `antonenko-davydovych-yak-my-hovorymo_p039` |
| C3.synonyms.07 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Слово у значенні які його синоніми"` | `Found 2 results for: ""Слово у значенні які його синоніми""` — `antonenko-davydovych-yak-my-hovorymo_p158`, `antonenko-davydovych-yak-my-hovorymo_p039` |
| C3.synonyms.08 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Які синоніми має слово у значенні"` | `Found 2 results for: ""Які синоніми має слово у значенні""` — `antonenko-davydovych-yak-my-hovorymo_p030`, `antonenko-davydovych-yak-my-hovorymo_p158` |
| C3.antonyms.01 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Подай антоніми до слова у значенні"` | `Found 2 results for: ""Подай антоніми до слова у значенні""` — `antonenko-davydovych-yak-my-hovorymo_p119`, `antonenko-davydovych-yak-my-hovorymo_p158` |
| C3.antonyms.02 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Запиши антоніми слова у значенні"` | `Found 2 results for: ""Запиши антоніми слова у значенні""` — `antonenko-davydovych-yak-my-hovorymo_p119`, `antonenko-davydovych-yak-my-hovorymo_p158` |
| C3.antonyms.03 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Наведи антоніми для слова у значенні"` | `Found 2 results for: ""Наведи антоніми для слова у значенні""` — `antonenko-davydovych-yak-my-hovorymo_p119`, `antonenko-davydovych-yak-my-hovorymo_p138` |
| C3.antonyms.04 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Добери антоніми до слова у значенні"` | `Found 2 results for: ""Добери антоніми до слова у значенні""` — `antonenko-davydovych-yak-my-hovorymo_p119`, `antonenko-davydovych-yak-my-hovorymo_p158` |
| C3.antonyms.05 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Вкажи антоніми слова у значенні"` | `Found 2 results for: ""Вкажи антоніми слова у значенні""` — `antonenko-davydovych-yak-my-hovorymo_p119`, `antonenko-davydovych-yak-my-hovorymo_p158` |
| C3.antonyms.06 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Назви антоніми до слова у значенні"` | `Found 2 results for: ""Назви антоніми до слова у значенні""` — `antonenko-davydovych-yak-my-hovorymo_p119`, `antonenko-davydovych-yak-my-hovorymo_p158` |
| C3.antonyms.07 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Слово у значенні які його антоніми"` | `Found 2 results for: ""Слово у значенні які його антоніми""` — `antonenko-davydovych-yak-my-hovorymo_p119`, `antonenko-davydovych-yak-my-hovorymo_p032` |
| C3.antonyms.08 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Які антоніми має слово у значенні"` | `Found 2 results for: ""Які антоніми має слово у значенні""` — `antonenko-davydovych-yak-my-hovorymo_p032`, `antonenko-davydovych-yak-my-hovorymo_p119` |
| C4.idiom_definition.01 | `Found: 4/4` | `No results in Антоненко-Давидович for: "Подай словникове значення вислову"` | `Found 2 results for: ""Подай словникове значення вислову""` — `antonenko-davydovych-yak-my-hovorymo_p121`, `antonenko-davydovych-yak-my-hovorymo_p115` |
| C4.idiom_definition.02 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Запиши значення вислову за словником"` | `Found 2 results for: ""Запиши значення вислову за словником""` — `antonenko-davydovych-yak-my-hovorymo_p121`, `antonenko-davydovych-yak-my-hovorymo_p115` |
| C4.idiom_definition.03 | `Found: 4/4` | `No results in Антоненко-Давидович for: "Наведи словникове тлумачення вислову"` | `Found 2 results for: ""Наведи словникове тлумачення вислову""` — `antonenko-davydovych-yak-my-hovorymo_p121`, `antonenko-davydovych-yak-my-hovorymo_p018` |
| C4.idiom_definition.04 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Вкажи значення вислову за словником"` | `Found 2 results for: ""Вкажи значення вислову за словником""` — `antonenko-davydovych-yak-my-hovorymo_p121`, `antonenko-davydovych-yak-my-hovorymo_p115` |
| C4.idiom_definition.05 | `Found: 4/4` | `No results in Антоненко-Давидович for: "Відтвори словникове тлумачення вислову"` | `Found 2 results for: ""Відтвори словникове тлумачення вислову""` — `antonenko-davydovych-yak-my-hovorymo_p121`, `antonenko-davydovych-yak-my-hovorymo_p018` |
| C4.idiom_definition.06 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Вислів яке його словникове значення"` | `Found 2 results for: ""Вислів яке його словникове значення""` — `antonenko-davydovych-yak-my-hovorymo_p163`, `antonenko-davydovych-yak-my-hovorymo_p083` |
| C4.idiom_definition.07 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Яке значення вислову подає словник"` | `Found 2 results for: ""Яке значення вислову подає словник""` — `antonenko-davydovych-yak-my-hovorymo_p152`, `antonenko-davydovych-yak-my-hovorymo_p021` |
| C4.idiom_definition.08 | `Found: 4/4` | `No results in Антоненко-Давидович for: "Як словник тлумачить вислів"` | `Found 2 results for: ""Як словник тлумачить вислів""` — `antonenko-davydovych-yak-my-hovorymo_p050`, `antonenko-davydovych-yak-my-hovorymo_p117` |
| C5.printed_spelling_rule.01 | `Found: 8/8` | `No results in Антоненко-Давидович for: "Подай правило правопису для наведеного в ньому прикладу"` | `Found 2 results for: ""Подай правило правопису для наведеного в ньому прикладу""` — `antonenko-davydovych-yak-my-hovorymo_p011`, `antonenko-davydovych-yak-my-hovorymo_p065` |
| C5.printed_spelling_rule.02 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Наведи правило, у якому подано приклад"` | `Found 2 results for: ""Наведи правило, у якому подано приклад""` — `antonenko-davydovych-yak-my-hovorymo_p040`, `antonenko-davydovych-yak-my-hovorymo_p011` |
| C5.printed_spelling_rule.03 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Запиши правило правопису, що містить приклад"` | `Found 2 results for: ""Запиши правило правопису, що містить приклад""` — `antonenko-davydovych-yak-my-hovorymo_p040`, `antonenko-davydovych-yak-my-hovorymo_p151` |
| C5.printed_spelling_rule.04 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Вкажи правило правопису з прикладом"` | `Found 2 results for: ""Вкажи правило правопису з прикладом""` — `antonenko-davydovych-yak-my-hovorymo_p040`, `antonenko-davydovych-yak-my-hovorymo_p151` |
| C5.printed_spelling_rule.05 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Відтвори правило правопису, у якому наведено"` | `Found 2 results for: ""Відтвори правило правопису, у якому наведено""` — `antonenko-davydovych-yak-my-hovorymo_p147`, `antonenko-davydovych-yak-my-hovorymo_p040` |
| C5.printed_spelling_rule.06 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Приклад яке правило правопису його містить"` | `Found 2 results for: ""Приклад яке правило правопису його містить""` — `antonenko-davydovych-yak-my-hovorymo_p040`, `antonenko-davydovych-yak-my-hovorymo_p149` |
| C5.printed_spelling_rule.07 | `Found: 7/7` | `No results in Антоненко-Давидович for: "Яке правило правопису наведено разом із прикладом"` | `Found 2 results for: ""Яке правило правопису наведено разом із прикладом""` — `antonenko-davydovych-yak-my-hovorymo_p147`, `antonenko-davydovych-yak-my-hovorymo_p040` |
| C5.printed_spelling_rule.08 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Правопис містить приклад наведи відповідне правило"` | `Found 2 results for: ""Правопис містить приклад наведи відповідне правило""` — `antonenko-davydovych-yak-my-hovorymo_p040`, `antonenko-davydovych-yak-my-hovorymo_p070` |
| C6.calque_correction.01 | `Found: 4/4` | `No results in Антоненко-Давидович for: "Виправ кальку в реченні"` | `Found 2 results for: ""Виправ кальку в реченні""` — `antonenko-davydovych-yak-my-hovorymo_p141`, `antonenko-davydovych-yak-my-hovorymo_p070` |
| C6.calque_correction.02 | `Found: 4/4` | `No results in Антоненко-Давидович for: "Подай речення без кальки"` | `No results found.` — none |
| C6.calque_correction.03 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Запиши наведене речення без кальки"` | `Found 2 results for: ""Запиши наведене речення без кальки""` — `antonenko-davydovych-yak-my-hovorymo_p124`, `antonenko-davydovych-yak-my-hovorymo_p120` |
| C6.calque_correction.04 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Усунь кальку в наведеному реченні"` | `Found 2 results for: ""Усунь кальку в наведеному реченні""` — `antonenko-davydovych-yak-my-hovorymo_p167`, `antonenko-davydovych-yak-my-hovorymo_p114` |
| C6.calque_correction.05 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Заміни калькований вислів у реченні"` | `Found 2 results for: ""Заміни калькований вислів у реченні""` — `antonenko-davydovych-yak-my-hovorymo_p163`, `antonenko-davydovych-yak-my-hovorymo_p108` |
| C6.calque_correction.06 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Наведи виправлений варіант речення з калькою"` | `Found 2 results for: ""Наведи виправлений варіант речення з калькою""` — `antonenko-davydovych-yak-my-hovorymo_p112`, `antonenko-davydovych-yak-my-hovorymo_p152` |
| C6.calque_correction.07 | `Found: 4/4` | `No results in Антоненко-Давидович for: "Речення запиши без кальки"` | `Found 2 results for: ""Речення запиши без кальки""` — `antonenko-davydovych-yak-my-hovorymo_p120`, `antonenko-davydovych-yak-my-hovorymo_p100` |
| C6.calque_correction.08 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Як записати речення без кальки"` | `Found 2 results for: ""Як записати речення без кальки""` — `antonenko-davydovych-yak-my-hovorymo_p120`, `antonenko-davydovych-yak-my-hovorymo_p100` |
| C6.book_calque_replacement.01 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Подай заміну вислову за книжкою"` | `Found 2 results for: ""Подай заміну вислову за книжкою""` — `antonenko-davydovych-yak-my-hovorymo_p028`, `antonenko-davydovych-yak-my-hovorymo_p121` |
| C6.book_calque_replacement.02 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Наведи заміну вислову за книжкою"` | `Found 2 results for: ""Наведи заміну вислову за книжкою""` — `antonenko-davydovych-yak-my-hovorymo_p028`, `antonenko-davydovych-yak-my-hovorymo_p121` |
| C6.book_calque_replacement.03 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Запиши заміну вислову за книжкою"` | `Found 2 results for: ""Запиши заміну вислову за книжкою""` — `antonenko-davydovych-yak-my-hovorymo_p028`, `antonenko-davydovych-yak-my-hovorymo_p121` |
| C6.book_calque_replacement.04 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Вкажи заміну вислову за книжкою"` | `Found 2 results for: ""Вкажи заміну вислову за книжкою""` — `antonenko-davydovych-yak-my-hovorymo_p028`, `antonenko-davydovych-yak-my-hovorymo_p121` |
| C6.book_calque_replacement.05 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Відтвори заміну вислову за книжкою"` | `Found 2 results for: ""Відтвори заміну вислову за книжкою""` — `antonenko-davydovych-yak-my-hovorymo_p028`, `antonenko-davydovych-yak-my-hovorymo_p121` |
| C6.book_calque_replacement.06 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Вислів яку заміну пропонує книжка"` | `Found 2 results for: ""Вислів яку заміну пропонує книжка""` — `antonenko-davydovych-yak-my-hovorymo_p125`, `antonenko-davydovych-yak-my-hovorymo_p138` |
| C6.book_calque_replacement.07 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Яку заміну вислову пропонує книжка"` | `Found 2 results for: ""Яку заміну вислову пропонує книжка""` — `antonenko-davydovych-yak-my-hovorymo_p028`, `antonenko-davydovych-yak-my-hovorymo_p125` |
| C6.book_calque_replacement.08 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Як книжка пропонує замінити вислів"` | `Found 2 results for: ""Як книжка пропонує замінити вислів""` — `antonenko-davydovych-yak-my-hovorymo_p125`, `antonenko-davydovych-yak-my-hovorymo_p138` |
| C7.modern_norm_selection.01 | `Found: 7/7` | `No results in Антоненко-Давидович for: "Обери сучасну нормативну форму з наведеної пари"` | `Found 2 results for: ""Обери сучасну нормативну форму з наведеної пари""` — `antonenko-davydovych-yak-my-hovorymo_p042`, `antonenko-davydovych-yak-my-hovorymo_p066` |
| C7.modern_norm_selection.02 | `Found: 7/7` | `No results in Антоненко-Давидович for: "Вкажи сучасну нормативну форму в наведеній парі"` | `Found 2 results for: ""Вкажи сучасну нормативну форму в наведеній парі""` — `antonenko-davydovych-yak-my-hovorymo_p099`, `antonenko-davydovych-yak-my-hovorymo_p114` |
| C7.modern_norm_selection.03 | `Found: 7/7` | `No results in Антоненко-Давидович for: "Назви сучасну нормативну форму з поданої пари"` | `Found 2 results for: ""Назви сучасну нормативну форму з поданої пари""` — `antonenko-davydovych-yak-my-hovorymo_p066`, `antonenko-davydovych-yak-my-hovorymo_p062` |
| C7.modern_norm_selection.04 | `Found: 7/7` | `No results in Антоненко-Давидович for: "Подай сучасну нормативну форму з наведеної пари"` | `Found 2 results for: ""Подай сучасну нормативну форму з наведеної пари""` — `antonenko-davydovych-yak-my-hovorymo_p042`, `antonenko-davydovych-yak-my-hovorymo_p011` |
| C7.modern_norm_selection.05 | `Found: 7/7` | `No results in Антоненко-Давидович for: "Запиши сучасну нормативну форму з поданої пари"` | `Found 2 results for: ""Запиши сучасну нормативну форму з поданої пари""` — `antonenko-davydovych-yak-my-hovorymo_p066`, `antonenko-davydovych-yak-my-hovorymo_p120` |
| C7.modern_norm_selection.06 | `Found: 7/7` | `No results in Антоненко-Давидович for: "Виділи сучасну нормативну форму в наведеній парі"` | `Found 2 results for: ""Виділи сучасну нормативну форму в наведеній парі""` — `antonenko-davydovych-yak-my-hovorymo_p099`, `antonenko-davydovych-yak-my-hovorymo_p114` |
| C7.modern_norm_selection.07 | `Found: 8/8` | `No results in Антоненко-Давидович for: "Яка форма в наведеній парі відповідає сучасній нормі"` | `Found 2 results for: ""Яка форма в наведеній парі відповідає сучасній нормі""` — `antonenko-davydovych-yak-my-hovorymo_p047`, `antonenko-davydovych-yak-my-hovorymo_p016` |
| C7.modern_norm_selection.08 | `Found: 7/7` | `No results in Антоненко-Давидович for: "Котра з поданих форм відповідає сучасній нормі"` | `Found 2 results for: ""Котра з поданих форм відповідає сучасній нормі""` — `antonenko-davydovych-yak-my-hovorymo_p109`, `antonenko-davydovych-yak-my-hovorymo_p017` |
| C8.supported_pronunciation.01 | `Found: 19/19` | `No results in Антоненко-Давидович for: "Подай нормативну або допустиму вимову слова в контексті за книжкою Наведи також оцінку цієї вимови з того самого абзацу"` | `Found 2 results for: ""Подай нормативну або допустиму вимову слова в контексті за книжкою Наведи також оцінку цієї вимови з того самого абзацу""` — `antonenko-davydovych-yak-my-hovorymo_p011`, `antonenko-davydovych-yak-my-hovorymo_p147` |
| C8.supported_pronunciation.02 | `Found: 19/19` | `No results in Антоненко-Давидович for: "Запиши нормативну або допустиму вимову слова в контексті за книжкою Наведи також оцінку цієї вимови з того самого абзацу"` | `Found 2 results for: ""Запиши нормативну або допустиму вимову слова в контексті за книжкою Наведи також оцінку цієї вимови з того самого абзацу""` — `antonenko-davydovych-yak-my-hovorymo_p147`, `antonenko-davydovych-yak-my-hovorymo_p028` |
| C8.supported_pronunciation.03 | `Found: 18/18` | `No results in Антоненко-Давидович for: "Наведи нормативну або допустиму вимову слова в контексті за книжкою Наведи також оцінку цієї вимови з того самого абзацу"` | `Found 2 results for: ""Наведи нормативну або допустиму вимову слова в контексті за книжкою Наведи також оцінку цієї вимови з того самого абзацу""` — `antonenko-davydovych-yak-my-hovorymo_p147`, `antonenko-davydovych-yak-my-hovorymo_p028` |
| C8.supported_pronunciation.04 | `Found: 19/19` | `No results in Антоненко-Давидович for: "Вкажи нормативну або допустиму вимову слова в контексті за книжкою Наведи також оцінку цієї вимови з того самого абзацу"` | `Found 2 results for: ""Вкажи нормативну або допустиму вимову слова в контексті за книжкою Наведи також оцінку цієї вимови з того самого абзацу""` — `antonenko-davydovych-yak-my-hovorymo_p147`, `antonenko-davydovych-yak-my-hovorymo_p028` |
| C8.supported_pronunciation.05 | `Found: 19/19` | `No results in Антоненко-Давидович for: "Відтвори нормативну або допустиму вимову слова в контексті за книжкою Наведи також оцінку цієї вимови з того самого абзацу"` | `Found 2 results for: ""Відтвори нормативну або допустиму вимову слова в контексті за книжкою Наведи також оцінку цієї вимови з того самого абзацу""` — `antonenko-davydovych-yak-my-hovorymo_p147`, `antonenko-davydovych-yak-my-hovorymo_p028` |
| C8.supported_pronunciation.06 | `Found: 19/19` | `No results in Антоненко-Давидович for: "Слово у контексті яку вимову книжка визнає нормативною або допустимою Наведи також оцінку цієї вимови з того самого абзацу"` | `Found 2 results for: ""Слово у контексті яку вимову книжка визнає нормативною або допустимою Наведи також оцінку цієї вимови з того самого абзацу""` — `antonenko-davydovych-yak-my-hovorymo_p129`, `antonenko-davydovych-yak-my-hovorymo_p125` |
| C8.supported_pronunciation.07 | `Found: 19/19` | `No results in Антоненко-Давидович for: "Яку вимову слова в контексті книжка визнає нормативною або допустимою Наведи також оцінку цієї вимови з того самого абзацу"` | `Found 2 results for: ""Яку вимову слова в контексті книжка визнає нормативною або допустимою Наведи також оцінку цієї вимови з того самого абзацу""` — `antonenko-davydovych-yak-my-hovorymo_p125`, `antonenko-davydovych-yak-my-hovorymo_p129` |
| C8.supported_pronunciation.08 | `Found: 19/19` | `No results in Антоненко-Давидович for: "Як за книжкою нормативно або допустимо вимовляти слово в контексті Наведи також оцінку цієї вимови з того самого абзацу"` | `Found 2 results for: ""Як за книжкою нормативно або допустимо вимовляти слово в контексті Наведи також оцінку цієї вимови з того самого абзацу""` — `antonenko-davydovych-yak-my-hovorymo_p028`, `antonenko-davydovych-yak-my-hovorymo_p148` |
| C9.verbatim_section.01 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Подай текст розділу з підручника"` | `Found 2 results for: ""Подай текст розділу з підручника""` — `antonenko-davydovych-yak-my-hovorymo_p146`, `antonenko-davydovych-yak-my-hovorymo_p011` |
| C9.verbatim_section.02 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Наведи текст розділу з підручника"` | `Found 2 results for: ""Наведи текст розділу з підручника""` — `antonenko-davydovych-yak-my-hovorymo_p146`, `antonenko-davydovych-yak-my-hovorymo_p145` |
| C9.verbatim_section.03 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Відтвори текст розділу з підручника"` | `Found 2 results for: ""Відтвори текст розділу з підручника""` — `antonenko-davydovych-yak-my-hovorymo_p146`, `antonenko-davydovych-yak-my-hovorymo_p145` |
| C9.verbatim_section.04 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Запиши текст розділу з підручника"` | `Found 2 results for: ""Запиши текст розділу з підручника""` — `antonenko-davydovych-yak-my-hovorymo_p146`, `antonenko-davydovych-yak-my-hovorymo_p145` |
| C9.verbatim_section.05 | `Found: 4/4` | `No results in Антоненко-Давидович for: "Процитуй розділ з підручника"` | `Found 2 results for: ""Процитуй розділ з підручника""` — `antonenko-davydovych-yak-my-hovorymo_p146`, `antonenko-davydovych-yak-my-hovorymo_p145` |
| C9.verbatim_section.06 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Розділ подай його текст із підручника"` | `Found 2 results for: ""Розділ подай його текст із підручника""` — `antonenko-davydovych-yak-my-hovorymo_p146`, `antonenko-davydovych-yak-my-hovorymo_p011` |
| C9.verbatim_section.07 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Який текст містить розділ у підручнику"` | `Found 2 results for: ""Який текст містить розділ у підручнику""` — `antonenko-davydovych-yak-my-hovorymo_p058`, `antonenko-davydovych-yak-my-hovorymo_p123` |
| C9.verbatim_section.08 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Що написано в розділі підручника"` | `Found 2 results for: ""Що написано в розділі підручника""` — `antonenko-davydovych-yak-my-hovorymo_p020`, `antonenko-davydovych-yak-my-hovorymo_p146` |

Eight initial calls returned `Tool call failed: search_style_guide.` or
`Tool call failed: search_text.`. Same-tool/query retries succeeded:

- C1.sentence_correction.01: `search_style_guide`.
- C3.antonyms.01: `search_text`.
- C6.calque_correction.01: `search_text`.
- C8.supported_pronunciation.01: `search_style_guide`.
- C8.supported_pronunciation.07: `search_style_guide`.
- C9.verbatim_section.02: `search_style_guide`.
- C9.verbatim_section.04: `search_style_guide`.
- C9.verbatim_section.06: `search_style_guide`.

Shorter collocation queries supplement the long per-line queries:

| Query | Style output | Book output and locators |
| --- | --- | --- |
| `добери` | `No results in Антоненко-Давидович for: "добери"` | `No results found.` — none |
| `вкажи` | `No results in Антоненко-Давидович for: "вкажи"` | `No results found.` — none |
| `словникове тлумачення` | `No results in Антоненко-Давидович for: "словникове тлумачення"` | `No results found.` — none |
| `сучасна норма` | `No results in Антоненко-Давидович for: "сучасна норма"` | `Found 3 results for: "сучасна норма"` — `antonenko-davydovych-yak-my-hovorymo_p012`, `antonenko-davydovych-yak-my-hovorymo_p029`, `antonenko-davydovych-yak-my-hovorymo_p093` |
| `допустима вимова` | `No results in Антоненко-Давидович for: "допустима вимова"` | `Found 1 results for: "допустима вимова"` — `antonenko-davydovych-yak-my-hovorymo_p147` |
| `калькований вислів` | `No results in Антоненко-Давидович for: "калькований вислів"` | `Found 3 results for: "калькований вислів"` — `antonenko-davydovych-yak-my-hovorymo_p163`, `antonenko-davydovych-yak-my-hovorymo_p083`, `antonenko-davydovych-yak-my-hovorymo_p047` |

## Reproducible schema and arithmetic smoke check

Run in the assigned worktree, with `LU_PROJECT_PYTHON` set to the
task-prescribed shared interpreter. Do not create a worktree virtualenv.

```bash
"$LU_PROJECT_PYTHON" - <<'PY'
import copy
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

root = Path("registry/projects/open_model_data")
schema = json.loads((root / "instruction_catalog.schema.json").read_text())
catalog = yaml.safe_load((root / "instruction_catalog.yaml").read_text())
Draft202012Validator.check_schema(schema)
validator = Draft202012Validator(schema)
validator.validate(catalog)
plan_body = Path(catalog["plan"]["path"]).read_bytes().split(b"-->\n", 1)[1]
assert hashlib.sha256(plan_body).hexdigest() == catalog["plan"]["body_sha256"]
ids = set()
operations = 0
for component, entry in catalog["components"].items():
    assert entry["line_count"] == len(entry["instructions"])
    groups = {}
    for line in entry["instructions"]:
        assert line["id"].startswith(component + ".")
        assert line["id"] not in ids
        ids.add(line["id"])
        slots = re.findall(r"\{([a-z_]+)\}", line["template"])
        assert slots == line["slots"]
        assert set(slots) <= set(entry["source_fields"])
        groups.setdefault(line["operation"], []).append(line["template"])
    for templates in groups.values():
        operations += 1
        assert len(templates) == 8
        for length in (1, 4):
            prefixes = []
            for template in templates:
                masked = re.sub(r"\{[a-z_]+\}", "SLOT", template)
                text = unicodedata.normalize("NFC", masked).casefold().replace("'", "’")
                tokens = re.findall(r"[^\W\d_]+(?:’[^\W\d_]+)*", text)
                prefixes.append(tuple(tokens[:length]))
            counts = Counter(prefixes)
            assert max(counts.values()) / 8 <= 0.15
            assert sum(sorted(counts.values(), reverse=True)[:5]) / 8 <= 0.65
bad_catalogs = []
bad = copy.deepcopy(catalog)
del bad["components"]["C9"]
bad_catalogs.append(bad)
for field, value in (("training_eligible", True), ("status", "approved"), ("answer", "forbidden")):
    bad = copy.deepcopy(catalog)
    bad[field] = value
    bad_catalogs.append(bad)
for field, value in (("template", "Подай {invented}."), ("slots", ["invented"]), ("operation", "invented")):
    bad = copy.deepcopy(catalog)
    bad["components"]["C9"]["instructions"][0][field] = value
    bad_catalogs.append(bad)
bad = copy.deepcopy(catalog)
bad["components"]["C9"]["source_fields"]["invented"] = "forbidden"
bad_catalogs.append(bad)
for bad in bad_catalogs:
    assert list(validator.iter_errors(bad)), "schema admitted a must-reject mutation"
assert len(ids) == 88 and len(catalog["components"]) == 9 and operations == 11
print("PASS: schema; 9 components; 88 IDs; 11 operations; 22 prefix projections; 8 rejected mutations")
PY
```

This is a draft-structure and arithmetic check, not the production checker,
source-relationship gate or independent evaluation. No existing importing-code
test is affected: the changed files are only the catalog, its schema and this
document. The checker test and independent fixtures belong to the E5-backed
follow-up; they are deliberately not claimed as executed here.

## Driver handback: open questions and remaining proof

This worker's milestone is a pushed draft with clean status, not issue closure.
The accountable `claude-open-model-data` driver owns all remaining issue work:

1. Reconcile C1–C8 in #9611 with the ordered C1–C9 denominator.
2. Obtain exact-head Opus and fresh non-author Sol reviews, with tool canaries.
   This author cannot supply the Sol approval. Review naturalness, semantics,
   printable slot availability and euphony with real source values.
3. Approve or revise the proposed 15%/65% prefix and ID bounds before E12.
   Check whether the eight starts and C8's common verdict suffix provide
   sufficient variety; prefix arithmetic is not semantic diversity.
4. Authenticate source-field adapters, especially C2 tuple labels, C3 sense
   text and C8 phonetic context. Determine whether non-norm-only C8 cases need
   a separately reviewed contrast operation; this draft withholds them rather
   than inventing a normative answer.
5. After E5, integrate the checker and independently execute the must-fail
   fixtures. Smoke success cannot satisfy AC4.
6. Verify official Правопис availability on the review harness. Then pursue
   CF, PR, CI, merge and cleanup through the existing driver flow.

No two-seat review, threshold freeze, E5-backed checker test or independent
held-out proof is claimed. The worker does not open a PR, merge, train a model
or inspect the sealed ruler. The source-slot and metric proposals stay drafts.

Stop/residual policy: unresolved lines cannot enter training. If reviewers
disagree after the required tool-backed resolution, drop the line. Recheck
counts and feasibility; an operation that cannot meet the frozen bound or has
missing source fields is withheld and returned to the driver. Never invent
text, lower a gate or claim PA6 complete to overcome that gap.
