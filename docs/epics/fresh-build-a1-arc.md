# Fresh lesson-based build — A1 arc (module grain)

> Sub-epic #8397, child 4. Status: **revision r4, designated approval recorded in §8 (#10108)**.
> Historical r3 was prepared by the curriculum-upgrade driver. r1 was reviewed by
> AGY `gemini-3.8-flash-high` (task `plan-review-8397-a1-arc-r1`): REVISE, 9 findings; the driver
> verified findings 1 and 3 against the Standard text and folded all nine in. **r3:** operator ruled
> the Standard is a minimum and ULP is the schedule (D0); position 45 restored on ULP evidence (D6). Requirements: [`fresh-build-requirements.md`](fresh-build-requirements.md);
> schema: [`fresh-build-plan-schema.md`](fresh-build-plan-schema.md). This document becomes
> `curriculum/l2-uk-en/lesson-plans/a1/_arc.yaml` once accepted. Ownership examples in the
> amendment (§11) come from the State Standard A1. Lesson-level forms, stress and examples
> are settled in the evidence packs by tools and the language lanes.

## 1. Evidence this arc is built on

| Strand | Source in the repo | What it fixes |
| --- | --- | --- |
| State Standard 2024, A1 | `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt:221-747`; machine map `docs/l2-uk-en/state-standard-2024-mapping.yaml:16-132` | the **minimum** A1 must cover (operator, 2026-09-21: the Standard is a floor, not a ceiling): four cases (називний, знахідний, місцевий, кличний); present, past, compound future and a few perfective futures; imperative 2nd person only; ordinal numerals; grammar "sporadic, based on reproducing ready communicative models" (`:562-567`); 17 speech intentions (`:453-477`), 12 themes (`:479-556`); writing of forms, postcards, SMS (`:338-377`); dialogue of 4–6 turns (`:432`) |
| ULP Season 1–2 | `data/sources.db` `textbook_sections` (`ulp-1-00-lesson-notes` …), `external_articles` (`ulp_youtube`, full transcripts), `docs/best-practices/ulp-presentation-pattern.md`, `audit/ulp-calibration-2026-05-13/raw.jsonl` | the **method and order**: a case first as a lexical chunk, later as a system (S1 chunk → S2 system); conjugations before the accusative; past and future inside the first season; review lesson = first-person bilingual story + Ukrainian-only questions + one translation task; a pronunciation trainer at regular intervals |
| Primers | Захарійчук, Буквар 2025, parts 1–2 (`textbooks`, subject `bukvar`, 223 page chunks); Большакова 2025 reading notes `docs/l2-uk-direct/textbook-reading-notes/bolshakova-bukvar-mapping.md` | the **literacy lesson shape**: letter + key word → locate the sound → syllable tables (CV → CVC) → words → short connected text; звук before літера; sound models for vowel / hard / soft |
| Project decisions | `docs/l2-uk-en/A1-CURRICULUM-V3.md:31-37, 242-252` (case scope, alphabet approach); `docs/best-practices/ulp-presentation-pattern.md` §"Why this matters" (operator's preference for the Ukrainian approach) | no dative or instrumental as grammar at A1; imperative 2nd person only; Ukrainian approach to the alphabet (звуки / літери), not the English-centric "true friends / false friends" grouping |

## 2. Decisions

**D1 — Keep the 55 positions and slugs; rebuild what is inside them.** The v1 sequence was built
from the Standard and, read module by module, stays inside its A1 ceiling: genitive, dative and
instrumental appear only as marked chunks (`у мене є`, `мені подобається`, `з/без + noun`,
`автобусом`, `вітаю з …`). Keeping positions means: `/a1/<slug>/` parallels `/a1-v1/<slug>/`; the
immersion bands, which are keyed by module number (R-30), keep working unchanged; and review
effort goes into lessons, not into re-arguing order. Position 45 keeps its v1 job and gains the
home theme (D6).

**D2 — What was actually broken, and is fixed by this arc:**
1. *Literacy scope.* Module 1's subtitle promised seven letters while its body listed all 33
   (`plans/a1/sounds-letters-and-hello.yaml:17` vs `:141-205`). With lessons there is no reason to
   cram: §4 gives an honest inventory per module and lesson.
2. *The historical level plan contradicted the Standard.* `curriculum/l2-uk-en/plans/a1.yaml:34-40`
   claimed genitive "basic" and cardinals 1–1000 as grammar scope;
   `STATE-STANDARD-COMPLIANCE-ANALYSIS.md:23` claimed five cases. The level plan was retired on
   2026-09-30 in #9252 item 2; its last commit is `fc241af5ff` in Git history. Both claims are
   replaced by §3 of this arc.
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

**D0 — The Standard is the minimum; ULP is the schedule (operator, 2026-09-21).** Everything the
Standard lists for A1 must be owned by a position. Teaching something *earlier* than the Standard
places it is allowed when Anna Ohoiko's ULP does so at the matching point of its course, and the
arc records the ULP evidence next to it. The level→season map is
`docs/best-practices/ulp-presentation-pattern.md:256-268`: positions 1–40 ≈ ULP Season 1,
positions 41–55 ≈ the Season 2 transition. "Earlier than the Standard" without ULP evidence is
still not done.

**D6 — Position 45 keeps its v1 job and gains the home theme.** r2 of this arc removed the
`що / де / коли` clauses from A1 because the Standard first lists them at A2 (`:1408-1411`) and B1
(`:2406`). Under D0 that was the wrong test. Measured in the ULP lesson notes (`data/sources.db`,
`ulp-1-00…`, `ulp-2-00…`): Season 1 already uses these clauses in running text, unexplained —
`, що` from lesson 5, `, де` from lesson 17, `, коли` from lesson 20 — and Season 2 uses `, що` 82
times from lesson 41 on. Position 45 sits in the Season 2 band, so first complex sentences belong
there. ULP's lesson 45 is the review story «Мій дім»; position 45 therefore carries the Standard
theme **Дім, помешкання** (`:489-493`), which had no owner, as the content its clauses talk about.
The slug `when-and-where` and the position number stay.

**D5 — A pronunciation strand runs through the whole level**, not only the first four modules:
a short trainer inside a lesson roughly every sixth module (и; soft consonants; р; intonation;
`-шся` / `-ться`; unstressed е / и), using the ULP trainer videos that are in the corpus.

## 3. Grammar at A1: system or chunk

| Item | Status at A1 | Where (position) | Standard |
| --- | --- | --- | --- |
| Gender of nouns; adjective agreement (hard and soft group), nominative | system | 8–10 | §4.2.1 `:603-650` |
| Adjective agreement in the **locative** and **accusative** (hard and soft group) | system | locative 29–30; accusative 31, 37, 40 | `:633-650`, examples `:680`, `:691` |
| Personal pronouns 1st / 2nd person, accusative forms (мене, тебе, нас, вас) | system | 40 (first met in the chunk `мене звати` at 3) | `:656-657` |
| Personal pronouns 1st / 2nd person, dative forms (мені, тобі, нам, вам) | **forms taught as pronoun forms inside their constructions** (`мені подобається`, `мені … років`, and the "I need" chunk); no noun dative | 11, 15, 43, 54 | `:656-657`; noun dative stays A2 (mapping `:97-102`) |
| Possessive gender forms мій, моя, моє; твій, твоя, твоє; наш, наша, наше; ваш, ваша, ваше; їхній, їхня, їхнє; demonstratives | system | possessives 8 (chunks at 4); demonstratives 12; plurals 13 | `:659-667` |
| Nominative plural: nouns with vowel alternation рік – роки, ніж – ножі, палець – пальці, будинок – будинки, річ – речі; agreeing adjectives; мої, твої, наші, ваші, їхні, ті, ці | system | 13 | `:606-609`, `:636-638`, `:666-667` |
| Present tense: читати, працювати, іти, їхати at 16; сидіти, дивитися at 17; могти at 18; modal + infinitive and reflexive routines | system | 15–20; named paradigms 16–18 | `:704-709` |
| Questions (question words, чи, intonation), negation | system | 19 | `:729-739` |
| Ordinal gender forms перший, перша, перше; другий, друга, друге; третій, третя, третє (time, dates) | system; oblique date forms remain chunks | 22; dates recycled 23 | `:652-654`, `:664-665` |
| Cardinal numerals | **lexical items only** (prices, age, phone numbers) — no numeral + noun agreement system | 11, 39 | cardinals with nouns are A2 `:1271-1272` |
| Locative: place | system | 29–30 | `:690-695` |
| Accusative: direction, inanimate object, animate object | system | 31, 37, 40 | `:678-688` |
| `про` + accusative with думати, мріяти | system (small) | 40, recycled 51 | `:687-688` |
| Locative with months; accusative with days of the week | chunk at 23, recognised as system after 29 / 31 | 23 | `:678-695` |
| Clock time `о / об` + locative ordinal | chunk at 22, recognised after 29 | 22 | inside the Standard's A1 (time with у / в `:693`, ordinals `:652-654`); ULP systematises it at S2 L67 |
| `грати у` + sport, `грати на` + instrument | chunk (vocabulary-level, no case taught) | 26 | ULP lesson to be cited by the module's evidence pack; if none is found the chunk stays lexical only |
| Date formulas (ordinal + month, both in the genitive) | **chunk only** | 23, 46 | genitive is A2; ULP meets "of"-genitive in dates at S1 L15 and teaches dates at S2 L68 |
| Vocative | system | 42 | `:697-699` |
| Imperative, 2nd person singular and plural | system | 43 (first met as chunks at 33) | `:721-725` |
| Coordination і (й) / а / але; cause бо / тому що | system | 44 | `:741-747` |
| Clauses with що, де / куди / звідки, коли | met unexplained in texts from early on (ULP S1 L5 / L17 / L20); **system at 45** | 45 | beyond the Standard's A1 minimum (A2 `:1408-1411`, коли B1 `:2406`); taught here on ULP evidence (D0, D6) |
| Past tense, including reflexive сміявся, сміялася, сміялося, сміялися and був, була, було, були | system | 48; recycle 49 | `:713-714` |
| Future forms of бути; compound future (буду + infinitive) | system | 50–51 | `:710-711`, `:715-717` — the Standard's A1 names only the compound imperfective form; the synthetic future is B1 (`:2287-2289`) and ULP S3 L98 |
| A few perfective futures: зможу, скажете, прочитають | chunk; no full aspect system | 51; recycle 52 | `:718-719` |
| Genitive (`у мене є`, `з України`, `без …`, quantities) | **chunk only** | 4, 34, 36, 39 | first systematic at A2; ULP uses it as a chunk from S1 L6 (`у мене є`) and L15, system at S2 L46–49 |
| Dative (`мені подобається`, `мені … років`, the "I need" chunk) | **chunk only** | 11, 15, 54 | noun dative is A2 (mapping `:97-102`); ULP S1 L14 (`подобається` + dative pronouns), system at S2 L51–53 |
| Instrumental (`автобусом`, `з молоком`, `вітаю з …`) | **chunk only** | 32, 36, 46 | noun instrumental is A2; ULP S1 L21 (`українською`), system at S2 L61–62 |
| Verb aspect | **first awareness only**, tied to the perfective futures and past narration — ULP introduces the imperfective / perfective idea at S1 L34 | 49–52 | system is A2 |
| Comparison of adjectives; 3rd-person imperative; oblique forms of він / вона / воно / вони; genitive, dative, instrumental of nouns as systems | **not in A1** — ULP itself systematises these in Season 2 lessons 46–62, which map to our A2 | — | A2 |

## 4. Orientation and literacy (positions 1–5): communication first

Position 1 is a standalone English orientation, with no acquired letters or new core
words. Positions 2–5 connect useful spoken turns to sound, print and supported writing.
The preparation's communication-led order replaces the old primer order; primer
methodology still grounds sound before letter and contextual decoding. Private ULP
pedagogy grounds the progression only and is never copied as learner text.

| Pos | Slug | Phase | Job | Inventory (letters / signs) | Skills duty | Est. lessons |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `introduction-to-ukrainian` | A1.1 | Orient yourself in English: language identity, brief history, where spoken, alphabet overview, study method and outcomes | Overview only; no acquired letters | — | 2 |
| 2 | `sounds-letters-and-hello` | A1.1 | Greet and take a first spoken turn; connect useful words with letters and supported writing | **12 letters**: А Е И І О М Н В П Р Т Я; stress and intonation from first speech; statement, question and exclamation contours (`:586`, `:596`) | Li, S, W (supported copying) | 5 |
| 3 | `who-am-i` | A1.1 | Introduce yourself and ask identity; common professions and origin phrases | **9 letters**: Д З К Л С У Х ь Г; hard/soft contrast and hardness before [е]; introduce voiced/voiceless base-pair families д–т, з–с, г–х; recycle stress and intonation; syllables (`:588`) | Li, S, W (`:485`) | 4 |
| 4 | `my-family` | A1.1 | Introduce people in a chosen family photo or equivalent using supported possessive phrases | **5 letters**: Б Й Ї Ю Є; apostrophe; continue voiced/voiceless base-pair family б–п; recycle stress and intonation | Li, S, W (captions) | 4 |
| 5 | `reading-ukrainian` | A1.1 | Complete the alphabet through useful labels and short exchanges; decode unfamiliar combinations of taught letters | **7 letters**: Ґ Ж Ч Ш Щ Ц Ф; дж and дз; complete voiced/voiceless base-pair families ґ–к, ж–ш, дж–ч, дз–ц; alphabet order and letter names; capital/small letters and recognising handwritten letters (`:571-572`) | Li, S, R, W (match printed/handwritten capitals and small letters; use capitals in Київ/київський and Україна/українець; complete writing own and other names/surnames; copy familiar labels; `:343-344`, `:362-365`) | 5 |

All 33 letters are introduced exactly once at positions 2–5. Later positions recycle
them. Printed words follow their constituent letter introductions inside each module;
audio-supported oral chunks may precede decoding. The module plan's evidence pack fixes
lesson-level sequencing and pronunciation; this arc does not claim mastery or widget
availability. Heavy handwriting is deferred; recognising handwritten letters belongs to 5.

The plan validator's generated scope sidecar must describe an active plan's actual
inventory, never the preserved sidecar of a retired plan. Source-backed prosody recycles
through the first ten; line-breaking ownership is recorded in §8.

## 5. The 55 positions

`L` = estimated lessons including the recap (an estimate for sizing; the module plan decides).
Skills duty = the Standard skill the module must exercise beyond its language point
(W writing, Li listening, R real-world reading, S speaking).

| Pos | Slug | Phase | One-sentence job | Skills duty | L |
| --- | --- | --- | --- | --- | --- |
| 6 | `first-conversations` | A1.1 | Sustain a scaffolded 4-6-turn conversation with greetings, Добраніч, personal data, family and belongings; practise stressed/unstressed [е], [и] | Li, S, R, W (`:459`, `:239-243`, `:268-270`, `:410-432`, `:578-579`) | 3 |
| 7 | `checkpoint-first-contact` | A1.1 | Complete an integrated first-contact task with previously introduced language | Li, S, R, W | 2 |
| 8 | `things-have-gender` | A1.2 | Identify familiar belongings using noun gender and the complete singular possessive set, including наш, ваш, їхній | Li, S, R (`:661-662`) | 3 |
| 9 | `what-is-it-like` | A1.2 | Describe and identify familiar objects using nominative adjective agreement | Li, S, R, W (describe a familiar object with 1-2 features; `:358-360`) | 3 |
| 10 | `colors` | A1.2 | Use colours and agreeing hard/soft-group nominative descriptions of objects and appearance | Li, S, R, W (short description of a friend or parent; `:355-357`) (`:484`) | 2 |
| 11 | `how-many` | A1.2 | Understand and say numbers for prices, age, phone numbers | Li (numbers by ear) | 4 |
| 12 | `this-and-that` | A1.2 | Point at things: цей / той in three genders | — | 2 |
| 13 | `many-things` | A1.2 | Go from one to many: nominative nouns with vowel alternation, agreeing adjectives, possessives and demonstratives | — (`:606-609`, `:636-638`, `:666-667`) | 3 |
| 14 | `checkpoint-my-world` | A1.2 | Self-check: describe, count, point | R | 2 |
| 15 | `what-i-like` | A1.3 | Say what you like doing: infinitive, люблю + infinitive | — | 3 |
| 16 | `verbs-group-one` | A1.3 | Conjugate читати, працювати, іти, їхати in the present | — (`:704-708`) | 3 |
| 17 | `verbs-group-two` | A1.3 | Conjugate сидіти and дивитися in the present, including the reflexive paradigm; distinguish the two conjugations | — (`:708-709`) | 3 |
| 18 | `i-want-i-can` | A1.3 | Say what you want, can and must do using modal plus infinitive; conjugate могти in the present | — (`:706-707`) | 3 |
| 19 | `questions` | A1.3 | Ask and answer simple questions; negate | Li | 3 |
| 20 | `my-morning` | A1.3 | Describe a morning routine with reflexive verbs; divide written words at line breaks using syllables from position 3 | W (short note) (`:588`) | 3 |
| 21 | `checkpoint-actions` | A1.3 | Self-check: say what you do, want, ask | R | 2 |
| 22 | `what-time` | A1.4 | Ask and tell the time using ordinal forms in all three genders, including first, second and third; reuse date phrases at 23 | Li, R (timetable) (`:652-654`, `:664-665`) | 3 |
| 23 | `days-and-months` | A1.4 | Use days, months, seasons and dates in set phrases | R (calendar) | 4 |
| 24 | `weather` | A1.4 | Talk about weather, plants, pets and landscape | Li (forecast; `:549-551`), S, W (describe weather or an animal with 1-2 features; `:358-360`, `:401-404`) (`:547-551`) | 3 |
| 25 | `my-day` | A1.4 | Tell your day in order, including a work day, a day off, lunch break, and the start and end of work | Li, S, R, W (work-day/day-off information and colleague exchanges; `:239-243`, `:277-288`, `:325-336`, `:379-388`, `:511-515`) | 3 |
| 26 | `free-time` | A1.4 | Talk about hobbies, sports and leisure venues; invite someone | R, W (read and write an SMS invitation; `:323`, `:348-351`) (`:517-519`) | 3 |
| 27 | `checkpoint-time-nature` | A1.4 | Self-check: time, week plan, weather | R | 2 |
| 28 | `euphony` | A1.5 | Choose у / в, і / й, з / із / зі | — | 2 |
| 29 | `where-is-it` | A1.5 | Say where something is: locative nouns and agreeing hard/soft-group adjectives in all three genders | — (`:610-630`, `:639-650`, `:690-692`) | 4 |
| 30 | `my-city` | A1.5 | Name city institutions, worship buildings, public facilities and streets; say what is where | Li, S, R, W (city signs/map, short city description and captions; `:372-376`, `:496-503`) (`:496-498`, `:499-500`, `:503`) | 3 |
| 31 | `where-to` | A1.5 | Say where you are going: accusative direction with в, у, на and agreeing hard/soft-group adjectives in all three genders; де vs куди | — (`:610-630`, `:639-650`, `:683-684`) | 3 |
| 32 | `transport` | A1.5 | Get around: travel hubs including автовокзал, public transport and taxi; іти, їхати in basic phrases | Li, S, R, W (traveller/passenger roles; tickets, timetables, illustrated advertisements; slow clear announcements for topic/detail; `:245-252`, `:310-321`, `:379-388`) (`:522`, `:501-502`, `:524`) | 3 |
| 33 | `around-the-city` | A1.5 | Ask for and follow directions | Li | 3 |
| 34 | `where-from` | A1.5 | Say where you and things are from; parts of the world (continents); at the border | W (`:523-525`; full address: country, city, street, house/building-section/apartment numbers; form and envelope; `:345-346`, `:352`, `:361`, `:377`) | 3 |
| 35 | `checkpoint-places` | A1.5 | Self-check: find your way | R | 2 |
| 36 | `food-and-drink` | A1.6 | Name food and drink; say what Ukrainians eat | R (menu) | 3 |
| 37 | `i-eat-i-drink` | A1.6 | Say what you eat and drink: accusative inanimate nouns and agreeing hard/soft-group adjectives in all three genders | — (`:610-630`, `:639-650`, `:680`) | 3 |
| 38 | `at-the-cafe` | A1.6 | Order and pay in a café; request dishes, drinks, crockery and cutlery | Li, S, R, W (guest/customer exchanges and short notes; extract menu/bill information; `:310-311`, `:379-388`) (`:536-539`, `:272-275`) | 3 |
| 39 | `shopping` | A1.6 | Ask prices and buy food, toiletries including шампунь, and stationery; use weight, volume and money | Li, S, R, W (customer roles; seller in speaking; price tags; `:531-533`; illustrated advertisements, promotions and product-choice instructions; `:261-266`, `:318-321`, `:379-388`, `:447-448`) (`:528-534`) | 3 |
| 40 | `people-around-me` | A1.6 | Talk about people you see, know and think about: accusative animate nouns and agreeing hard/soft-group adjectives in all three genders; мене, тебе, нас, вас; `про` + accusative | — (`:610-650`, `:656-657`, `:687-688`) | 3 |
| 41 | `checkpoint-food-shopping` | A1.6 | Self-check: order and buy | R | 2 |
| 42 | `hey-friend` | A1.7 | Address people by name: vocative | — | 2 |
| 43 | `please-do-this` | A1.7 | Ask someone to do something and prohibit an action; all Standard imperative pairs, second person singular and plural | Li, S, R, W (illustrated instructions and prohibitions; copy familiar signs; `:264-266`, `:299`, `:314-315`, `:362-364`) (`:721-725`, `:475`) | 3 |
| 44 | `linking-ideas` | A1.7 | Join ideas: і, а, але, бо, тому що | W | 2 |
| 45 | `when-and-where` | A1.7 | Build first complex sentences with що, де, коли — talking about your home: housing, rooms, furniture, what is where | R, W (read an illustrated short description for gist, topic and details; describe your room; `:294-311`, `:358-360`, `:489-493`) | 4 |
| 46 | `holidays` | A1.7 | Greet people on holidays; state and religious holidays, birthdays, weddings and gifts | Li, S, R, W (read postcards, SMS and email; write or copy greetings, wishes, thanks and a greeting from a place; `:300`, `:323`, `:348-351`, `:553-556`) | 3 |
| 47 | `checkpoint-communication` | A1.7 | Self-check: address, ask, connect | R, W | 2 |
| 48 | `what-happened` | A1.8 | Say what happened using past forms, including reflexive verbs and бути | — (`:713-714`) | 4 |
| 49 | `yesterday` | A1.8 | Tell yesterday as a connected story | W | 3 |
| 50 | `what-will-happen` | A1.8 | Say what will happen using all future forms of бути and the compound imperfective future | — (`:710-711`, `:715-717`) | 3 |
| 51 | `my-plans` | A1.8 | Make plans and arrange to meet using selected perfective futures зможу, скажете, прочитають; recycle at 52 | W (SMS) (`:718-719`) | 3 |
| 52 | `my-story` | A1.8 | Tell your life in three tenses and complete a personal profile, including gender, date/place of birth and education | R, W, S (read and complete a personal-data form, write and tell a short biography, retell a simple text; `:322`, `:352-353`, `:405-406`, `:422-436`) (`:343-347`, `:370-377`, `:482-485`) | 3 |
| 53 | `health` | A1.8 | Say what hurts, including injury and high temperature; at the pharmacy and doctor | Li, S, R, W (patient exchanges, signs and short personal-data notes; `:287`, `:335`, `:387`, `:449`, `:541-545`) | 3 |
| 54 | `emergencies` | A1.8 | Get help in an emergency | Li, S, R, W (help requests and important written phrases; `:272-275`, `:368-369`) | 2 |
| 55 | `a1-finale` | A1.8 | Spend one full day in a Ukrainian city: integrated reuse of all taught Standard A1 intentions, themes and speech skills; no new language | all (Standard section 1 verification using taught inventory; source section 11) (`:228-451`, `:453-556`) | 3 |

**Sizing (operator, 2026-09-21): nothing is forced.** The lesson counts above are estimates for
orientation only and total 162. A module gets the lessons its content needs — not compressed to hit
a number, not stretched to fill one. The module plan decides the count; the plan review checks two
things in both directions: no lesson that crams (too much new inventory for an hour) and no lesson
that drags (a lesson whose job could be a step inside its neighbour). The reviewer's note that
recap and checkpoint lessons are a large share of the total is a drag risk to watch: a short module
may close with a recap *section* of its last lesson rather than a separate recap lesson, if the
plan review agrees.

**Theme coverage against the Standard's 12:** Людина: identity, origin and professions 3,
family 4, appearance 10, age 11, address 34, people around you 40, full personal profile
including gender, date/place of birth and education 52 (`:343-347`, `:481-487`).
Дім, помешкання: housing, rooms and furniture 45; household objects first met at 8–9, 12.
Місто: places 30, including синагога, мечеть, перукарня, пункт обміну валют (`:496-500`);
place/direction 29, 31, 33; public transport and taxi 32 (`:501-503`).
Побут: routines 20, daily objects 8–9, calendar/time 22–23, daily sequence 25.
Діяльність: work day, day off, lunch break and start/end of work 25 (`:511-515`);
verb preparation at 15–18 is not the theme's delivery. Дозвілля: hobbies, sports and
стадіон, спортзал, басейн 26 (`:517-519`). Подорожі: вокзал, автовокзал, аеропорт
(летовище) 32; border and parts of the world (continents) 34 (`:525`); attractions 30, 33 (`:521-526`).
Купівля: shops, groceries, мило, шампунь, зубна паста, stationery, measures and money 39
(`:528-534`). Ресторан, кафе: food/drink 36–37; service, посуд і столові прибори 38
(`:536-539`). Здоров'я: body, illness, травма and pharmacy 53; emergency help 54 (`:541-545`).
Природне середовище: weather, plants дерево, квітка, кущ; pets кіт, собака; landscape
ліс, озеро, річка, гори, море 24 (`:547-551`). Традиції, звичаї, свята: state/religious
holidays, birthdays, весілля and gifts 46 (`:553-556`).

## 6. Decisions on the six open questions (operator accepted the driver's proposals, 2026-09-21; the reviewer independently recommended the same on 2–6)

1. **Size:** flexible — see Sizing above. No target total.
2. **Past and future stay at positions 48–51** for A1; the order is reconsidered when A2 is planned.
3. **Locative before accusative:** place (29–30) → direction (31) → object (37, 40).
4. **Cardinal numerals are vocabulary only;** no numeral + noun agreement system at A1.
5. **Дім / помешкання** is owned by position 45 as the theme of its complex sentences (D6);
   household objects are already met at 9 and 12.
6. **Letter order authority is Захарійчук,** the primer ingested page by page. It is not reopened for
   A1 if another primer is ingested later.

## 7. Follow-ups outside this document

- **Wording of the "I need" chunk (position 54) is for the language lanes.** v1 used the short
  adjective form with `мені`; the Ukrainian-language reviewer flagged it as a possible calque and
  suggested `мені треба` or the full adjective form. The style-guide tool has no entry against the
  short form and quotes it without criticism (Антоненко-Давидович, «Спостереження митця»), and notes
  that a missing entry proves nothing. The arc therefore names the function, not the wording; the
  module's evidence pack settles it with sources.
- Counts of clause markers in §2 D6 are whitespace-tolerant (`,\s*що\b`), so they include matches
  split across line breaks in the lesson notes (76 on one line + 6 across breaks = 82).

- `docs/l2-uk-en/state-standard-2024-mapping.yaml:126` attributes `що / де / коли` clauses to A1,
  `:84` lists `за`, `через` under the A1 accusative, and `:91` lists `по` under the A1 locative (the
  Standard's A1 locative has only `в / у`, `на`, `:690-695`; `по` first appears at A2 `:1330`); the Standard text has them at A2 / B1
  (`:1408-1411`, `:2406`, `:2205`). The file should state what the Standard says, and the
  compliance gate and the plan-review skill that read it must treat the Standard as a **minimum**
  (D0): "taught earlier on ULP evidence" is not a violation. To be settled before A1 module plans
  are reviewed.
- `curriculum/l2-uk-en/plans/a1.yaml:34-40` and `STATE-STANDARD-COMPLIANCE-ANALYSIS.md:23` contradicted
  the Standard (genitive, five cases, cardinals 1–1000 as grammar); the level plan was retired on
  2026-09-30 in #9252 item 2 and remains in Git history at `fc241af5ff`. The claims are replaced by §3 here.

## 8. Revision r4 (#10108)

Accepted: 2026-10-08 (designated approval: Sol 6.1 and Opus 5.5; #10108)

Sol 6.1, the implementation author in Codex at high reasoning, confirms agreement with
Opus 5.5's round-two design and the revised ten positions before implementation. Opus's
design approval binds prompt SHA-256
`bf161c91e6a484c363b25ed7b4f44757ec34364e8fbe4e1d4e47fad2b53073a6`;
the round-two result has SHA-256
`4fd205f682149cbd3fbee4081537082f8966f777f9c76fe6aa69688e8ff1b507`.
This records current designated revision approval under the standing execution order,
not a direct operator review of this revision and not formal implementation review.
The original acceptance criteria remain unchanged.

This revision supersedes D1's slug clause, D5's first-four-modules wording, §4,
the first ten position rows of §5, and §6 item 6. Historical accepted §2 and §6
remain verbatim, with their original acceptance dates; those dates do not accept
this revision. The 55-position arc and 162 estimated lessons remain. Positions
11–55 retain their semantic identities; position 55's `all` now includes speaking.

Three promoted plans are explicitly retired by their exact bytes in `_retired.yaml`:
`sounds-letters-and-hello` (old position 1), `reading-ukrainian` (2), and
`special-signs` (3). Their scopes, state folders, receipts and evidence packs remain
unchanged. Only matching bytes are retired; a replacement is an ordinary plan
requiring all normal gates and fresh review. The old `special-signs` (3) and
`stress-and-melody` (4) routes become generated retired notices, outside arc order.
No lesson prose or replacement plan is authorized by this revision.

Listening and speaking begin at position 2, with stress and intonation. Hard/soft
contrast belongs to 3; the apostrophe to 4; дж and дз, alphabet order, letter names,
capital/small letters and recognising handwritten letters to 5. Line breaking
(`:588`) remains owned by the writing strand at position 20, outside the tables.
Prosody and useful exchanges recycle through 6–10. Printed words follow the
introduction of their constituent letters; supported oral chunks may precede decoding.

Sources verification for this revision: VESUM `verify_words` attested 28/28 forms
from the preparation inventory plus дзвоник and дзеркало. This verifies morphology,
not unrestricted A1 vocabulary admission. Правопис 2019 §7 grounds the apostrophe.
Stress is left to the source-backed deterministic annotator. Private pedagogy remains
grounding-only. State Standard 2024 evaluation is independent driver evidence.

Position 1 declares the `a1-orientation` band through the existing `band_key`
mechanism supplied by #10105. Ordinary positions carry no declared band key and
retain vocabulary-count selection. Final integration follows #10105 and #10103;
this revision changes no band configuration or core-word store. Grammar locators
G-a1-001 to G-a1-011 receive append-only supersession at the first replacement plan,
owned by curriculum-upgrade; no blind refresh is authorized here.

## 9. Revision r3.1: A1 practical recap (#10105)

Accepted: 2026-10-08 (designated approval: Sol 6.1 and Opus 5.5; #10105)

Historical section 2 remains verbatim; its acceptance date does not accept this revision.
The following replaces D4 for current A1 builds.

**D4 — A1 closes with a practical recap using taught inventory** (R-03, #10105).
Every recap/checkpoint lesson and embedded closing recap declares an approved plan-step
`task`: action, English context/instruction, response mode, observable English criteria,
permitted learner print, and the step's existing uses/evidence. A story is optional support,
not a required first-person story → Ukrainian-only questions → production sequence.
Early A1 is data-defined by `activity_instruction: [en]` in `immersion_table.yaml`;
its closure is practical application rather than comprehension questions or copying alone.
Inventory is available before the recap step; earlier teaching in that lesson counts.
Recaps introduce nothing. Explicit `a1-orientation` has an English practical orientation
recap, no Ukrainian production requirement and no new core words. Scripts check structure;
qualified independent review judges usefulness, Ukrainian processing and decisions.
Old A1 plans fail `a1_recap_migration_required`; #10108 owns disposition, without rewriting here.

The tracked position-1 declaration of `a1-orientation` is supplied by the #10108 revision in §8.
## 10. Revision r4.1: Staged phonetic facets (#10108)

Accepted: 2026-10-09 (designated approval: Sol 6.1 and Opus 5.5; #10108)

Opus 5.5 in native Claude Code authored the staged phonetic-facet adjustment in report
`adjudge10108-two-facets-r7.result` (SHA-256
`a37b5cebc6641d0b4651639bd4470e07d60066ce434a1a4c3a2be4aff210f014`).
Sol 6.1 in native Codex designated-approved it 2/2 in report
`adjudge10108-staged-facets-r8.result` (SHA-256
`741f8082470f872592d63a57cf620b2815c0fad5cda8125740c1bc546a02acaa`)
on 2026-10-09, bound to commit `4bb985d44c685d207dd05b94b074732d803e4051`.
This records current designated revision approval under the standing execution order,
not a direct operator review of this revision and not formal implementation review.
The original acceptance criteria remain unchanged.

This revision explicitly assigns the two approved phonetic facets across positions 3–5:
position 3 explicitly owns hardness before [е] and introduces voiced/voiceless
base-pair families д–т, з–с, г–х; position 4 continues with б–п; position 5 completes
ґ–к, ж–ш, дж–ч, дз–ц alongside its existing дж/дз duty. These are base-pair families,
not an exhaustive inventory of individual sounds. Printed examples follow introduced letters
and within-module ordering (неділя, тема, колега and діло–тіло printable at 3;
голодний–холодний contains й available at 4 so never printed at 3). These are
source-check candidates, not newly admitted learner vocabulary.

Official Standard printed p. 16/§4.1.4 supplies coverage; approved arc supplies
sequence; Sources textbook chunks support phonetics/pedagogy; VESUM morphology only;
PULS vocabulary classification only. Approval cites Большакова
(`2-klas-ukrmova-bolshakova-2019-1_s0062`) and Авраменко
(`5-klas-ukrmova-avramenko-2022_s0078`) for pairs and soft counterparts; Захарійчук
(`1-klas-bukvar-zaharijchuk-2025-1_s0014`, `1-klas-bukvar-zaharijchuk-2025-2_s0075`)
for early hard/soft and contextual voicing rehearsal; Голуб
(`5-klas-ukrmova-golub-2022_s0253`) is a contents witness, not adult-A1 sizing proof.
Historical accepted sections 2, 6, 8 and 9 remain verbatim; the ten jobs, 33 letters,
55 positions, 162 estimated lessons, retirement, recap, and vocabulary-selected
immersion remain intact.


## 11. A1 floor ownership amendment (#10108)

This amendment records ownership; it does not certify lesson delivery.
All 55 positions, slugs and letter inventories/order remain. Early lessons introduce
2-3 letters at most, with the existing one-letter remainder lessons retained; new
facets are short teaching/practice steps before the recap. Recaps introduce nothing.
Appearance at 10 uses nominative descriptions, not an oblique-pronoun system.
Position 3 owns syllables; 6 owns unstressed [е]/[и]; 20 owns line breaking.
This amendment supersedes §8's 'outside the tables' wording for `:588`: position 20's §5 row now carries the reference.
Position 5 completes writing one's own and others' names (`:343-344`) and capital-letter
use, including Київ/київський and Україна/українець (`:571-572`), alongside printed
and handwritten letter recognition. Position 6 explicitly teaches
Добраніч (`:459`). Positions 29, 31, 37 and 40 cover both adjective groups in all
three genders; 48 explicitly includes the reflexive past at `:714`; 50 includes
all future forms of бути (`:710-711`); 51 owns the selected perfective futures.
Present-tense paradigms belong to 16 (читати, працювати, іти, їхати),
17 (сидіти, дивитися, including reflexive forms), and 18 (могти) (`:704-709`).
Position 34 owns parts of the world (continents), the Standard's назви частин світу
(`:525`), as well as the border topic.
No whole aspect system or additional noun case system is introduced.

The following Standard speech duties bind the named positions in addition to
section 5. Position 55 verifies their integrated reuse with previously taught
inventory; it is not a first-teaching substitute. Letter gating and A1 English
support remain. Standard `:560-567` governs every grammar application task.

| Standard id | Lines | Required performance or text | Owning positions |
| --- | --- | --- | --- |
| 1.1.1.1 | 234-237 | Recognise familiar self/family words and direct intentions | 3-4, 6 |
| 1.1.1.2 | 239-243 | Understand short everyday dialogue and a short thematic monologue | 6, 24 |
| 1.1.1.3 | 245-252 | Identify topic and needed detail in slow, clear, repeated announcements | 32 |
| 1.1.2.1.1 | 258-259 | Listen to a short adapted description | 24 |
| 1.1.2.1.2 | 261-266 | Listen to information/promotions and direction/study/product instructions | 39, 33, 43 |
| 1.1.2.2 | 268-275 | Listen to personal-data dialogue, directions, food/water and first-aid requests | 6, 33, 38, 54 |
| 1.1.3 | 277-288 | Listening roles, roster below | 6, 25, 32, 38-39, 43, 46, 53 |
| 1.2.1.1 | 294-302 | Understand labels, illustrated descriptions/instructions, greetings and key details | 5, 43, 45-46 |
| 1.2.1.2 | 304-311 | Read for gist/topic and select needed receipt/ticket/menu information | 45, 32, 38 |
| 1.2.2 | 313-323 | Signs, announcements, illustrated original fragments, forms, postcards, SMS, email | 5, 32, 39, 43, 46, 52 |
| 1.2.3 | 325-336 | Reading roles, roster below | 6, 25, 32, 38-39, 43, 46, 53 |
| 1.3.1.1/a | 343-344 | Write own and other names/surnames | supported practice 3-4; completion 5 |
| 1.3.1.1/b | 345-346 | Write country, city, street, house/building-section/apartment numbers | 34 |
| 1.3.1.1/c | 347 | Write nationality, education and age | 52 |
| 1.3.1.1/d | 348-351 | Write/copy postcard or SMS greetings, wishes, thanks and greetings from a place | 46 |
| 1.3.1.1/e | 352 | Complete a simple form | 34, 52 |
| 1.3.1.1/f | 353 | Write about oneself | 52 |
| 1.3.1.1/g | 355-357 | Write a short description of a friend/parent | 10 |
| 1.3.1.1/h | 358-360 | Describe an object, animal, room and weather with 1-2 features | 9, 24, 45 |
| 1.3.1.1/i | 361 | Address an envelope | 34 |
| 1.3.1.1/j | 362-364 | Copy familiar labels, signs and instructions | 5, 43 |
| 1.3.1.1/k | 365 | Use soft sign/apostrophe in familiar written words | 3-5 |
| 1.3.2 | 367-377 | Important words/phrases; profiles; family/home/city/country descriptions; captions; hotel form | 3-5, 10, 30, 34, 43, 45, 52, 54 |
| 1.3.3 | 379-388 | Writing roles, roster below, excluding stranger/acquaintance | 25, 32, 38-39, 43, 46, 53; family/friend 4, 10 |
| 1.4.1.1.1 | 396-406 | Short thematic utterances, pictured descriptions and simple-text retelling | 10, 24, 45, 52 |
| 1.4.1.2.1 | 410-413 | Understand a slow, clear partner who repeats/rephrases | 6 |
| 1.4.1.2.2 | 415-429 | Etiquette, basic dialogue, formulas, personal/theme talk, questions and requests | 6, 19, 25-26, 33, 38, 43, 45-46, 52 |
| 1.4.2 | 431-436 | 4-6-turn dialogue, short personal/thematic account and elementary description | 6; accounts/descriptions 10, 24-26, 30, 45, 52 |
| 1.4.3 | 438-451 | Speaking roles, roster below, including seller at 39 | 6, 25, 32, 38-39, 43, 46, 53 |

Role roster, with the learner taking each listed role: stranger, acquaintance,
friend and family member at 6 (family/friend writing first at 4, 10); colleague at 25;
tourist and passenger at 32; customer and seller at 39; student at 43;
patient at 53; guest at 38 and 46. Apply only the roles listed for each skill in
the Standard; the seller is an extra speaking role, not an added listening duty.
The roles are communicative contexts, not extra grammar lessons.

Plan acceptance requires a clause-to-lesson/task check of Standard `:221-747`,
including every bullet within the grouped rows above. Missing audio, genuine
handwriting samples, taught inventory or observable learner work blocks delivery
of its owning module. A separate evaluator uses unseen prompts/texts within taught
inventory; an ownership table, moved v1 block or passed parser is not learner proof.
The curriculum-upgrade driver owns these build/asset/evaluation residuals.

### Closing ownership ledger

The first 51 rows retain the mapping-item denominator. The next 29 cover
speech-performance groups; the final row covers communicative application.
Each grouped row includes every constituent clause. Lettered writing suffixes
are local clause identifiers, not official Standard numbering.

| Standard item id | Standard lines | Owning position after amendment |
|---|---:|---|
| `intentions[1]` contact/attention | 454–455 | 6; reuse 33, 43 |
| `intentions[2]` introductions | 456–457 | 3–4 |
| `intentions[3]` greeting | 458 | 2 |
| `intentions[4]` farewell | 459 | 6 |
| `intentions[5]` thanks | 460 | 2, 6 |
| `intentions[6]` apology | 461 | 6 |
| `intentions[7]` congratulations | 462 | 46 |
| `intentions[8]` wishes | 463 | 46 |
| `intentions[9]` asking questions | 464–465 | 19; first identity questions 3 |
| `intentions[10]` answering questions | 466–467 | 19 |
| `intentions[11]` requesting information | 468–469 | 33, 43 |
| `intentions[12]` confirmation/denial | 470–471 | 19 |
| `intentions[13]` preferences | 472–473 | 15 |
| `intentions[14]` requests for action | 474 | 43 |
| `intentions[15]` prohibition | 475 | 43 |
| `intentions[16]` spatial meanings | 476 | 29–33 |
| `intentions[17]` temporal meanings | 477 | 23, 25, 48–51 |
| `phonetics.alphabet` | 571–572 | 2–5; capital-letter use and handwriting 5 |
| `phonetics.apostrophe` | 574 | 4 |
| `phonetics.soft_sign` | 575 | 3 |
| `phonetics.vowels_consonants` | 577–584 | Hardness 3; stressed/unstressed vowels [е]/[и] 6; staged voicing 3–5; дж/дз 5 |
| `phonetics.stress` | 586 | 2; subsequent recycling |
| `phonetics.syllable` | 588 | Syllables 3; line breaking 20 |
| `phonetics.euphony` | 590–594 | 28 |
| `phonetics.intonation` | 596 | 2; subsequent recycling |
| `morphology.noun_declension` | 603–631 | Gender 8; plural/alternation 13; locative 29; accusative 31, 37, 40; vocative 42 |
| `morphology.adjective_declension` | 633–650 | Nominative 9–10; plural 13; locative 29; accusative 31, 37, 40 |
| `morphology.numeral` | 652–654 | Gender forms 22; date chunks 23 |
| `morphology.pronoun` | 656–657 | Accusative 40; dative forms inside constructions 11, 15, 43, 54 |
| `morphology.pronoun_gender_number` | 659–667 | Possessives 8; demonstratives 12; plurals 13; ordinals 22 |
| `cases.nominative` | 672–676 | 8–10; active-subject use 16 |
| `cases.accusative` | 678–688 | Object 37, 40; direction 31; weekdays 23; про 40 |
| `cases.locative` | 690–695 | Place 29–30; months 23 |
| `cases.vocative` | 697–699 | 42 |
| `verbs.indicative` | 703–719 | Present 16–18; past 48; future бути/compound 50; selected perfectives 51 |
| `verbs.imperative` | 721–725 | 43 |
| `REQ-A1-REFLEXIVE` | 709, 714 | Present 17, routine 20; past 48 |
| `syntax.simple_sentence` | 729–739 | Statements/questions/negation 19; requests 43 |
| `syntax.complex_sentence` | 741–747 | 44 |
| `theme.Людина` / §3.1 | 481–487 | Identity/origin/profession 3; family 4; appearance 10; age 11; address 34; surrounding people 40; complete profile 52 |
| `theme.Дім` / §3.2 | 489–493 | 45; objects introduced 8–9, 12 |
| `theme.Місто` / §3.3 | 495–503 | Places 30; transport/taxi 32; spatial use 29, 31, 33 |
| `theme.Побут` / §3.4 | 505–509 | Objects 8–9; routines 20; time/calendar 22–23; day sequence 25 |
| `theme.Діяльність` / §3.5 | 511–515 | 25 |
| `theme.Дозвілля` / §3.6 | 517–519 | 26 |
| `theme.Подорожі` / §3.7 | 521–526 | Hubs/movement 32; border and parts of the world (continents) 34; attractions 30, 33 |
| `theme.Купівля` / §3.8 | 528–534 | 39 |
| `theme.Ресторан` / §3.9 | 536–539 | Food/drink 36–37; service/crockery/cutlery 38 |
| `theme.Здоров’я` / §3.10 | 541–545 | 53; emergency application 54 |
| `theme.Природа` / §3.11 | 547–551 | 24 |
| `theme.Традиції` / §3.12 | 553–556 | 46 |
| `1.1.1.1` | 234–237 | 3–4, 6 |
| `1.1.1.2` | 239–243 | 6, 24 |
| `1.1.1.3` | 245–252 | 32 |
| `1.1.2.1.1` | 258–259 | 24 |
| `1.1.2.1.2` | 261–266 | 39, 33, 43 |
| `1.1.2.2` | 268–275 | 6, 33, 38, 54 |
| `1.1.3` listening roles | 277–288 | 6, 25, 32, 38–39, 43, 46, 53 |
| `1.2.1.1` | 294–302 | 5, 43, 45–46 |
| `1.2.1.2` | 304–311 | 45, 32, 38 |
| `1.2.2` reading text types | 313–323 | 5, 32, 39, 43, 46, 52 |
| `1.2.3` reading roles | 325–336 | 6, 25, 32, 38–39, 43, 46, 53 |
| `1.3.1.1/a` names | 343–344 | Supported practice 3–4; completion 5 |
| `1.3.1.1/b` complete address | 345–346 | 34 |
| `1.3.1.1/c` nationality/education/age | 347 | 52 |
| `1.3.1.1/d` short correspondence | 348–351 | 46 |
| `1.3.1.1/e` forms | 352 | 34, 52 |
| `1.3.1.1/f` self-description | 353 | 52 |
| `1.3.1.1/g` friend/parent description | 355–357 | 10 |
| `1.3.1.1/h` object/animal/room/weather | 358–360 | 9, 24, 45 |
| `1.3.1.1/i` envelope | 361 | 34 |
| `1.3.1.1/j` copying | 362–364 | 5, 43 |
| `1.3.1.1/k` apostrophe/soft sign in writing | 365 | 3–5 |
| `1.3.2` writing text types | 367–377 | 3–5, 10, 30, 34, 43, 45, 52, 54 |
| `1.3.3` writing roles | 379–388 | Family/friend 4, 10; colleague 25; tourist/passenger 32; customer 39; student 43; guest 38, 46; patient 53 |
| `1.4.1.1.1` monologue | 396–406 | 10, 24, 45, 52 |
| `1.4.1.2.1` understanding a supported partner | 410–413 | 6 |
| `1.4.1.2.2` dialogue performances | 415–429 | 6, 19, 25–26, 33, 38, 43, 45–46, 52 |
| `1.4.2` speaking text types | 431–436 | Dialogue 6; accounts/descriptions 10, 24–26, 30, 45, 52 |
| `1.4.3` speaking roles | 438–451 | 6, 25, 32, 38–39, 43, 46, 53; seller specifically 39 |
| `§4` communicative application of grammar | 560–567 | Grammar-owning positions listed above; integrated verification 55 |

**Count: 51 mapping items + 29 speech groups + 1 application requirement = 81 ownership-ledger rows; 0 unowned rows.**
This grouped ledger is not an official 81-item Standard checklist. The level
descriptor (`:223-226`) governs difficulty, with first-contact performance at 6
and integrated performance at 55. Lesson delivery, handwriting/audio assets
and independent unseen-task evaluation remain with the curriculum-upgrade driver.
