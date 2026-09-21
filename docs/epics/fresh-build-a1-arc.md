# Fresh lesson-based build — A1 arc (module grain)

> Sub-epic #8397, child 4. Status: **draft r2** by the curriculum-upgrade driver. r1 was reviewed by
> AGY `gemini-3.8-flash-high` (task `plan-review-8397-a1-arc-r1`): REVISE, 9 findings; the driver
> verified findings 1 and 3 against the Standard text and folded all nine in. For operator correction. Requirements: [`fresh-build-requirements.md`](fresh-build-requirements.md);
> schema: [`fresh-build-plan-schema.md`](fresh-build-plan-schema.md). This document becomes
> `curriculum/l2-uk-en/plans/a1/_arc.yaml` once accepted. It contains no Ukrainian word facts
> beyond module titles already published in the reviewed v1 plans; every form, stress and example
> is settled later, in the evidence packs, by tools and the language lanes.

## 1. Evidence this arc is built on

| Strand | Source in the repo | What it fixes |
| --- | --- | --- |
| State Standard 2024, A1 | `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt:221-747`; machine map `docs/l2-uk-en/state-standard-2024-mapping.yaml:16-132` | the **ceiling**: four cases only (називний, знахідний, місцевий, кличний); present, past, compound future and a few perfective futures; imperative 2nd person only; ordinal numerals; grammar "sporadic, based on reproducing ready communicative models" (`:562-567`); 17 speech intentions (`:453-477`), 12 themes (`:479-556`); writing of forms, postcards, SMS (`:338-377`); dialogue of 4–6 turns (`:432`) |
| ULP Season 1–2 | `data/sources.db` `textbook_sections` (`ulp-1-00-lesson-notes` …), `external_articles` (`ulp_youtube`, full transcripts), `docs/best-practices/ulp-presentation-pattern.md`, `audit/ulp-calibration-2026-05-13/raw.jsonl` | the **method and order**: a case first as a lexical chunk, later as a system (S1 chunk → S2 system); conjugations before the accusative; past and future inside the first season; review lesson = first-person bilingual story + Ukrainian-only questions + one translation task; a pronunciation trainer at regular intervals |
| Primers | Захарійчук, Буквар 2025, parts 1–2 (`textbooks`, subject `bukvar`, 223 page chunks); Большакова 2025 reading notes `docs/l2-uk-direct/textbook-reading-notes/bolshakova-bukvar-mapping.md` | the **literacy lesson shape**: letter + key word → locate the sound → syllable tables (CV → CVC) → words → short connected text; звук before літера; sound models for vowel / hard / soft |
| Project decisions | `docs/l2-uk-en/A1-CURRICULUM-V3.md:31-37, 242-252`; `ulp-presentation-pattern.md:17` | no dative or instrumental as grammar at A1; imperative 2nd person only; Ukrainian approach to the alphabet (звуки / літери), not the English-centric "true friends / false friends" grouping |

## 2. Decisions

**D1 — Keep the 55 positions and slugs; rebuild what is inside them.** The v1 sequence was built
from the Standard and, read module by module, stays inside its A1 ceiling: genitive, dative and
instrumental appear only as marked chunks (`у мене є`, `мені подобається`, `з/без + noun`,
`автобусом`, `вітаю з …`). Keeping positions means: `/a1/<slug>/` parallels `/a1-v1/<slug>/`; the
immersion bands, which are keyed by module number (R-30), keep working unchanged; and review
effort goes into lessons, not into re-arguing order. **One exception (r2): position 45 is
re-targeted** — see D6.

**D2 — What was actually broken, and is fixed by this arc:**
1. *Literacy scope.* Module 1's subtitle promised seven letters while its body listed all 33
   (`plans/a1/sounds-letters-and-hello.yaml:17` vs `:141-205`). With lessons there is no reason to
   cram: §4 gives an honest inventory per module and lesson.
2. *The level plan contradicts the Standard.* `curriculum/l2-uk-en/plans/a1.yaml:34-40` claims
   genitive "basic" and cardinals 1–1000 as grammar scope; `STATE-STANDARD-COMPLIANCE-ANALYSIS.md:23`
   claims five cases. Both are replaced by §3 of this arc.
3. *No lesson grain.* Every module was one 1,200-word block. §5 estimates lessons per module.
4. *Skills the Standard requires were thin:* writing (forms, postcard, SMS), listening, real-world
   reading. §5 assigns them as lesson duties, not as extra modules.
5. *Unsourced teaching points.* "Open / closed syllable" is taught in v1 Module 1 but has no hit in
   the grade 1–5 textbooks in the corpus. It is dropped unless the evidence pack finds a source.

**D3 — Chunk first, system later (ULP), bounded by the Standard.** A construction may be used as a
memorised chunk before its grammar is taught, if and only if the plan marks it `chunk` and the
lesson does not analyse it. §3 is the single table of what is a system and what is a chunk at A1.

**D4 — Every module ends with a recap lesson in the ULP review shape** (R-03): a short
first-person story side by side in Ukrainian and English, Ukrainian-only questions about it, one
production task. Checkpoint modules are made of such lessons plus a self-check and introduce
nothing new.

**D6 — Position 45 changes its job (slug to be renamed).** v1 `when-and-where` teaches complex
sentences with `що`, `де`, `коли`. The Standard's A1 syntax (§4.3.2, `:741-747`) contains only
coordination with `і (й)`, `але` and cause with `тому що`, `бо`; clauses with `де / куди / звідки`
and `що` are A2 (`:1408-1411`) and `коли` is B1 (`:2406`). The error comes from a wrong summary
line in `state-standard-2024-mapping.yaml:126`, which v1 followed. Position 45 becomes the owner of
the Standard theme **Дім, помешкання** (`:489-493`), which had no owner. The position number, and
therefore the immersion band, does not change.

**D5 — A pronunciation strand runs through the whole level**, not only the first four modules:
a short trainer inside a lesson roughly every sixth module (и; soft consonants; р; intonation;
`-шся` / `-ться`; unstressed е / и), using the ULP trainer videos that are in the corpus.

## 3. Grammar at A1: system or chunk

| Item | Status at A1 | Where (position) | Standard |
| --- | --- | --- | --- |
| Gender of nouns; adjective agreement (hard and soft group), nominative | system | 8–10 | §4.2.1 `:603-650` |
| Adjective agreement in the **locative** and **accusative** (hard and soft group) | system | locative 29–30; accusative 31, 37, 40 | `:633-650`, examples `:680`, `:691` |
| Personal pronouns 1st / 2nd person, accusative forms (мене, тебе, нас, вас) | system | 40 (first met in the chunk `мене звати` at 5) | `:656-657` |
| Personal pronouns 1st / 2nd person, dative forms (мені, тобі, нам, вам) | **forms taught as pronoun forms inside their constructions** (`мені подобається`, `мені … років`, `мені потрібен`); no noun dative | 11, 15, 43, 54 | `:656-657`; noun dative stays A2 (mapping `:97-102`) |
| Demonstratives, possessives, nominative | system | 6, 12 | `:659-667` |
| Nominative plural (nouns, adjectives, demonstratives) | system | 13 | `:603-631` |
| Present tense, conjugations I and II, modal + infinitive, reflexive verbs | system | 15–20 | `:703-719` |
| Questions (question words, чи, intonation), negation | system | 19 | `:729-739` |
| Ordinal numerals (time, dates) | system | 22–23 | `:652-654` |
| Cardinal numerals | **lexical items only** (prices, age, phone numbers) — no numeral + noun agreement system | 11, 39 | cardinals with nouns are A2 `:1271-1272` |
| Locative: place | system | 29–30 | `:690-695` |
| Accusative: direction, inanimate object, animate object | system | 31, 37, 40 | `:678-688` |
| `про` + accusative with думати, мріяти | system (small) | 40, recycled 51 | `:687-688` |
| Locative with months; accusative with days of the week | chunk at 23, recognised as system after 29 / 31 | 23 | `:678-695` |
| Clock time `о / об` + locative ordinal | chunk at 22, recognised after 29 | 22 | — |
| `грати у` + sport, `грати на` + instrument | chunk | 26 | — |
| Date formulas (ordinal + month, both in the genitive) | **chunk only** | 23, 46 | genitive is A2 |
| Vocative | system | 42 | `:697-699` |
| Imperative, 2nd person singular and plural | system | 43 (first met as chunks at 33) | `:721-725` |
| Coordination і (й) / а / але; cause бо / тому що | system | 44 | `:741-747` |
| Clauses with що, де / куди / звідки, коли | **not at A1** (A2 `:1408-1411`; коли B1 `:2406`) | — | v1 position 45 taught these; removed (D6) |
| Past tense | system | 48–49 | `:713-714` |
| Compound future (буду + infinitive) | system | 50–51 | `:715-717` |
| A few perfective futures | chunk | 50–52 | `:718-719` |
| Genitive (`у мене є`, `з України`, `без …`, quantities) | **chunk only** | 6, 34, 36, 39 | first systematic at A2 |
| Dative (`мені подобається`, `мені … років`, `мені потрібен`) | **chunk only** | 11, 15, 54 | not allowed as grammar at A1 (mapping `:97-102`) |
| Instrumental (`автобусом`, `з молоком`, `вітаю з …`) | **chunk only** | 32, 36, 46 | not allowed as grammar at A1 |
| Verb aspect as a system; comparison of adjectives; 3rd-person imperative; oblique forms of він / вона / воно / вони | **not at A1** | — | A2 (`:1245-1247` and following) |

## 4. Literacy phase (positions 1–4): honest inventory

Adults move faster than the primers' one letter per lesson, but keep their progression: sound
before letter, syllables before words, words before sentences. Greetings and first phrases are
learned **by ear from lesson 1** (ULP starts with dialogue), so the learner speaks while still
learning to read. Letter order follows Захарійчук, the primer that is in the corpus and citable
page by page; the two Большакова sources in the repo disagree with each other (2018 list vs 2025
notes), so neither is used as an authority until one is ingested.

| Pos | Slug | Job | Inventory (letters / signs) | Est. lessons |
| --- | --- | --- | --- | --- |
| 1 | `sounds-letters-and-hello` | Hear and say first greetings; grasp звук vs літера, голосні vs приголосні; read and write the first letter group in syllables and short words | **13 letters**, primer part 1 order: А О У И М І Н В Л С К П Р | 5 |
| 2 | `reading-ukrainian` | Read words, then short sentences aloud, with most of the alphabet | **12 letters**: Т Е Д З Б (end of primer part 1; ь, which the primer places before Б, is held for position 3), then Г Ґ Ч Й Х Ж Ш | 5 |
| 3 | `special-signs` | Finish the alphabet; read and write words with the two-sound letters, ь, the apostrophe, дж / дз; hear hard vs soft | **8 letters**: Ї Я Ю Є Ц Щ Ф and ь; апостроф, дж, дз; hard / soft contrast. The alphabet in its dictionary order with the letter names; capital and small letters (`:571-572`) | 4 |
| 4 | `stress-and-melody` | Use stress marks as a reading aid; statement vs question melody; first contact with unstressed е / и; recognise handwritten and italic letter shapes; divide words into syllables for line breaks | наголос, інтонація, склад і перенос (`:588`), писані літери (`:571`); no new letters | 3 |

The module title and subtitle are generated from this inventory by the plan validator's `scope`
block (schema §2 rule 5), so the v1 contradiction cannot recur.

Video support, to be verified by the evidence pack, not copied: the ULP alphabet overview and the
twelve per-letter videos in the corpus; the four ULP pronunciation trainers. v1 cites about twenty
further URLs that are not in the corpus, and lists none for О; each is checked or dropped.

## 5. The 55 positions

`L` = estimated lessons including the recap (an estimate for sizing; the module plan decides).
Skills duty = the Standard skill the module must exercise beyond its language point
(W writing, Li listening, R real-world reading).

| Pos | Slug | Phase | One-sentence job | Skills duty | L |
| --- | --- | --- | --- | --- | --- |
| 1–4 | *(see §4)* | A1.1 | Literacy | Li, W (copying, own name) | 17 |
| 5 | `who-am-i` | A1.1 | Introduce yourself and ask who someone is; common professions (`:485`) | Li | 3 |
| 6 | `my-family` | A1.1 | Show a family photo and say who is who | W (captions) | 3 |
| 7 | `checkpoint-first-contact` | A1.1 | Self-check: read aloud, greet, introduce yourself and family | R, W | 2 |
| 8 | `things-have-gender` | A1.2 | Tell the gender of a noun and pick він / вона / воно, мій / моя / моє | — | 3 |
| 9 | `what-is-it-like` | A1.2 | Describe a thing with an agreeing adjective | — | 3 |
| 10 | `colors` | A1.2 | Name colours; soft-group adjectives | — | 2 |
| 11 | `how-many` | A1.2 | Understand and say numbers for prices, age, phone numbers | Li (numbers by ear) | 4 |
| 12 | `this-and-that` | A1.2 | Point at things: цей / той in three genders | — | 2 |
| 13 | `many-things` | A1.2 | Go from one to many: nominative plural | — | 3 |
| 14 | `checkpoint-my-world` | A1.2 | Self-check: describe, count, point | R | 2 |
| 15 | `what-i-like` | A1.3 | Say what you like doing: infinitive, люблю + infinitive | — | 3 |
| 16 | `verbs-group-one` | A1.3 | Conjugate first-conjugation verbs in the present | — | 3 |
| 17 | `verbs-group-two` | A1.3 | Conjugate second-conjugation verbs; tell the two apart | — | 3 |
| 18 | `i-want-i-can` | A1.3 | Say what you want, can and must do | — | 3 |
| 19 | `questions` | A1.3 | Ask and answer simple questions; negate | Li | 3 |
| 20 | `my-morning` | A1.3 | Describe a morning routine with reflexive verbs | W (short note) | 3 |
| 21 | `checkpoint-actions` | A1.3 | Self-check: say what you do, want, ask | R | 2 |
| 22 | `what-time` | A1.4 | Ask and tell the time | Li, R (timetable) | 3 |
| 23 | `days-and-months` | A1.4 | Use days, months, seasons and dates in set phrases | R (calendar) | 4 |
| 24 | `weather` | A1.4 | Talk about the weather and the natural world around you: animals, plants, landscape (`:549-551`) | Li (forecast) | 3 |
| 25 | `my-day` | A1.4 | Tell your day in order | W | 3 |
| 26 | `free-time` | A1.4 | Talk about leisure; invite someone | W (SMS invitation) | 3 |
| 27 | `checkpoint-time-nature` | A1.4 | Self-check: time, week plan, weather | R | 2 |
| 28 | `euphony` | A1.5 | Choose у / в, і / й, з / із / зі | — | 2 |
| 29 | `where-is-it` | A1.5 | Say where something is: locative of nouns with agreeing adjectives | — | 4 |
| 30 | `my-city` | A1.5 | Name places in a city and say what is where | R (signs, map) | 3 |
| 31 | `where-to` | A1.5 | Say where you are going: accusative of direction; де vs куди | — | 3 |
| 32 | `transport` | A1.5 | Get around: transport phrases | R (tickets, stops), Li | 3 |
| 33 | `around-the-city` | A1.5 | Ask for and follow directions | Li | 3 |
| 34 | `where-from` | A1.5 | Say where you and things are from; compass points; at the border (`:523-525`) | W (form: country, city; address an envelope `:361`) | 3 |
| 35 | `checkpoint-places` | A1.5 | Self-check: find your way | R | 2 |
| 36 | `food-and-drink` | A1.6 | Name food and drink; say what Ukrainians eat | R (menu) | 3 |
| 37 | `i-eat-i-drink` | A1.6 | Say what you eat and drink: accusative, inanimate, with agreeing adjectives | — | 3 |
| 38 | `at-the-cafe` | A1.6 | Order and pay in a café | Li, R (menu, bill) | 3 |
| 39 | `shopping` | A1.6 | Ask prices and buy things: food, toiletries, stationery; weight and volume (`:531-533`) | R (price tags), Li | 3 |
| 40 | `people-around-me` | A1.6 | Talk about people you see, know and think about: accusative, animate; мене / тебе / нас / вас; `про` + accusative | — | 3 |
| 41 | `checkpoint-food-shopping` | A1.6 | Self-check: order and buy | R | 2 |
| 42 | `hey-friend` | A1.7 | Address people by name: vocative | — | 2 |
| 43 | `please-do-this` | A1.7 | Ask someone to do something: imperative, ти and ви | R (signs, prohibitions) | 3 |
| 44 | `linking-ideas` | A1.7 | Join ideas: і, а, але, бо, тому що | W | 2 |
| 45 | *(new slug; was `when-and-where`)* | A1.7 | Describe your home: kinds of housing, rooms, furniture, what is where (`:489-493`) — recycles locative, adjectives, цей / той | W (describe your room) | 3 |
| 46 | `holidays` | A1.7 | Greet people on holidays; family and state holidays | W (postcard) | 3 |
| 47 | `checkpoint-communication` | A1.7 | Self-check: address, ask, connect | R, W | 2 |
| 48 | `what-happened` | A1.8 | Say what happened: past tense and gender | — | 4 |
| 49 | `yesterday` | A1.8 | Tell yesterday as a connected story | W | 3 |
| 50 | `what-will-happen` | A1.8 | Say what will happen: compound future | — | 3 |
| 51 | `my-plans` | A1.8 | Make plans and arrange to meet | W (SMS) | 3 |
| 52 | `my-story` | A1.8 | Tell your life in three tenses | W (short biography, form) | 3 |
| 53 | `health` | A1.8 | Say what hurts; at the pharmacy and doctor | Li, R | 3 |
| 54 | `emergencies` | A1.8 | Get help in an emergency | Li, R (signs) | 2 |
| 55 | `a1-finale` | A1.8 | One full day in a Ukrainian city: everything together | all | 3 |

**Sizing (operator, 2026-09-21): nothing is forced.** The lesson counts above are estimates for
orientation only and total 161. A module gets the lessons its content needs — not compressed to hit
a number, not stretched to fill one. The module plan decides the count; the plan review checks two
things in both directions: no lesson that crams (too much new inventory for an hour) and no lesson
that drags (a lesson whose job could be a step inside its neighbour). The reviewer's note that
recap and checkpoint lessons are a large share of the total is a drag risk to watch: a short module
may close with a recap *section* of its last lesson rather than a separate recap lesson, if the
plan review agrees.

**Theme coverage against the Standard's 12:** Людина 5–6 · Дім 8–9, 12 · Місто 29–33 · Побут 20, 25 ·
Діяльність 15–18 · Дозвілля 26 · Подорожі 32–34 · Купівля 39 · Ресторан / кафе 36–38 ·
Здоров'я 53–54 · Природне середовище 24 · Традиції / свята 46 · Дім / помешкання 45 (D6), with
household objects already met at 9 and 12.

## 6. Decisions on the six open questions (operator accepted the driver's proposals, 2026-09-21; the reviewer independently recommended the same on 2–6)

1. **Size:** flexible — see Sizing above. No target total.
2. **Past and future stay at positions 48–51** for A1; the order is reconsidered when A2 is planned.
3. **Locative before accusative:** place (29–30) → direction (31) → object (37, 40).
4. **Cardinal numerals are vocabulary only;** no numeral + noun agreement system at A1.
5. **Дім / помешкання** is owned by the re-targeted position 45 (D6); household objects are already
   met at 9 and 12.
6. **Letter order authority is Захарійчук,** the primer ingested page by page. It is not reopened for
   A1 if another primer is ingested later.

## 7. Follow-ups outside this document

- `docs/l2-uk-en/state-standard-2024-mapping.yaml:126` wrongly attributes `що / де / коли` clauses to
  A1, and `:84` lists `за`, `через` under the A1 accusative although the Standard first has them at
  B1 (`:2205`). The mapping file is what the pipelines and the plan-review skill read, so it must be
  corrected against the Standard text before any A1 module plan is reviewed.
- `curriculum/l2-uk-en/plans/a1.yaml:34-40` and `STATE-STANDARD-COMPLIANCE-ANALYSIS.md:23` contradict
  the Standard (genitive, five cases, cardinals 1–1000 as grammar); replaced by §3 here.
