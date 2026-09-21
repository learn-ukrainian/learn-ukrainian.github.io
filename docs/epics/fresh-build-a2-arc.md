# Fresh lesson-based build — A2 arc (module grain)

> Sub-epic #8397, issue #8424. Status: **draft r1** by the curriculum-upgrade driver, 2026-09-21 —
> not yet reviewed cross-family, not yet accepted by the operator. Same method and table format as
> the A1 arc ([`fresh-build-a1-arc.md`](fresh-build-a1-arc.md)); requirements:
> [`fresh-build-requirements.md`](fresh-build-requirements.md); schema:
> [`fresh-build-plan-schema.md`](fresh-build-plan-schema.md). This document becomes
> `curriculum/l2-uk-en/lesson-plans/a2/_arc.yaml` once accepted. It contains no Ukrainian word facts
> of its own: the only Ukrainian in it is module-neutral terminology and text quoted from the State
> Standard or from ULP lesson titles, each with its location. Every form, stress and example is
> settled later, in the evidence packs, from the sources (R-35).

## 1. Evidence this arc is built on

Every row was read from the source on 2026-09-21; nothing is carried over from memory or from the
research note in the issue without re-reading.

| Strand | Source in the repo | What it fixes |
| --- | --- | --- |
| State Standard 2024, A2 | `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt:749-1432` | the **minimum** A2 must cover (R-32). Skills `:756-1027`: dialogue of 8–10 turns (`:998`), written text to 50 words (`:923`), biography of 10–15 phrases (`:906-907`), private letter, e-mail, SMS, notes, hotel form, guest-book entry (`:926-937`), phone call (`:995`), announcements, voicemail, forecast, simple instructions and recipes (`:793-805`, `:864-866`). 25 speech intentions (`:1029-1070`), **14 themes** (`:1072-1163`). Grammar `:1165-1432`: see §3 |
| State Standard 2024, B1 | same file, `:2089-2110`, `:2284-2297`, `:2336`, `:2372-2375`, `:2399-2423` | what the Standard places **after** A2: declension of cardinal numerals, `себе`, demonstratives in the oblique cases, synthetic future of imperfective verbs, conditional mood, prefixed verbs of motion, participle phrases, clauses with `якщо`, concessive clauses |
| ULP Season 2 and Season 3 | `data/sources.db` `textbook_sections`, `ulp-2-00-lesson-notes` (lessons 41–80) and `ulp-3-00-lesson-notes` (lessons 81–120); titles quoted in §2 | the **schedule** (R-32): noun plural 42–44 → genitive 46–49 → dative 51–53 → accusative incl. prepositions and pronouns 56–58 → verbs of motion 59 → instrumental 61–62 → locative, time and dates 66–68 → vocative 69; then prefixed motion 81–89 → aspect 91–94 → perfective and both futures 96–98 → adverbs 101, 103 → indefinite 102 → comparison 104 → negative 106 → participles 107–108 → reflexive verbs 109 → imperative 111–114 → complex sentences 116–118 → conditional 119. Every fifth lesson is a review |
| ULP Season 4 | `ulp-4-00-lesson-notes` (lessons 121–160) | where A2 must deliver the learner: Ukrainian-only essays with grammar in small boxes. Measured share of Ukrainian in the lesson notes: S1 38.8 % → S2 49.9 % → S3 51.0 % → S4 89.3 % |
| Live immersion policy | `scripts/config.py` `IMMERSION_POLICIES["a2"]` | five bands keyed by module number: `a2-bridge` ≤ 3 (75–100 %), `a2-ramp` ≤ 7 (85–100 %), `a2-m01-20` ≤ 20 (85–100 %), `a2-m21-50` ≤ 50 (90–100 %), `a2-m51-70` beyond (95–100 %). Carried over unchanged (R-30) |
| Current A2 manifest | `curriculum/l2-uk-en/curriculum.yaml`, level `a2`: 69 modules in 10 groups | the slugs and positions this arc keeps (D1). `plans/a2.yaml` (71 modules, 6 phases) is stale and is not an input |

## 2. Decisions

**D0 — The Standard is the minimum; ULP is the schedule (R-32).** Everything the Standard lists for
A2 is owned by a position (§3, §6). Teaching something the Standard places at B1 is allowed at A2
only where ULP teaches it in Season 2–3, and the ULP lesson is cited next to it. Where ULP teaches
something in Season 3 that this arc still leaves to B1, that is said openly (D5) — R-32 permits
earlier teaching, it does not require it.

**D1 — Keep the 69 positions and slugs; rebuild what is inside them.** Reasons, as for A1:
`/a2/<slug>/` parallels the archived `/a2-v1/<slug>/` (requirements Q11); the A2 immersion bands
are keyed by module number and keep working unchanged (§7); and review effort goes into lessons,
not into re-arguing a module order that already follows the Standard. The v1 order was checked
against the ULP schedule and differs in three places, each handled without moving a slug (D2–D4).

**D2 — Aspect: idea first, system later — the ULP order, with the v1 positions.** ULP gives the
imperfective / perfective idea early (Season 1, lesson 34) and the system in Season 3 (lessons
91–94 «Using perfective and imperfective verb aspects», «Forming perfective verb aspect», «Sound
changes between imperfective and perfective verbs»; futures at 96–98). The Standard asks A2 only
for aspect **pairs as word formation** (`:1380-1381`) and the perfective future (`:1359`).
Positions 2–3 therefore teach recognition of pairs as vocabulary, so that every later A2 text may
narrate in the perfective past; positions 40–42 teach the system. No lesson before 40 asks the
learner to choose an aspect.

**D3 — Plural of the cases: met inside each case block, systematised at 32–34.** ULP teaches the
nominative plural first (lessons 42–44; ours is A1 position 13) and then brings the plural into
each case block (plural is discussed in lessons 48, 53, 56, 62 and 66). The Standard wants every
case in singular and plural (`:1201-1202`). Positions 5–31 are singular-first; each block's theme
module (15, 22, 30) meets that case's plural in its texts as marked, unanalysed forms; position 14
systematises the genitive plural, which the quantity expressions of the Standard need early
(`:1271-1272`); positions 32–34 systematise the rest.

**D4 — Metalanguage is taught at the point of need; positions 61–66 consolidate it.** From the
first A2 module the theory is written in simple Ukrainian (live band rule `a2-bridge`), so the
learner needs the words for it from the first module, not at position 61. Each grammar term is
`core` vocabulary of the lesson that first uses it, in Ukrainian categories (відмінок, рід, число,
вид, час, спосіб, речення). Positions 61–66 keep their slugs and become the bridge to B1: reading
and using grammar explanations the way a Ukrainian school textbook in the corpus words them. They
introduce no new grammar.

**D5 — What stays out of A2 although ULP Season 3 has it.** Participles and adverbial participles
(ULP 107–108; Standard B1 `:2372-2375`), the conditional mood (ULP 119; B1 `:2297`), the first
person plural imperative (B1 `:2293`), declension of cardinal numerals (B1 `:2089`) and of
demonstratives (B1 `:2108-2110`). Reason: they are not needed for any A2 skill or theme of the
Standard, the live A2 writing rule already excludes participles, and B1 owns them. They may occur
in a quoted authentic text as glossed, unanalysed forms.

**D6 — What A2 teaches beyond the Standard's A2, on ULP evidence.**

| Item | ULP evidence | Standard places it | Position |
| --- | --- | --- | --- |
| Synthetic future of imperfective verbs | lesson 98 «Future imperfective and perfective»: 7 such forms in the notes, 17 in review lesson 99 | B1 `:2287-2289` | 41 |
| Prefixed verbs of motion | lessons 81–89, one or two prefixes per lesson | B1 `:2336` | 43 |
| Indefinite and negative pronouns and adverbs | lessons 102 and 106 | not listed for A2 | 57 |
| Formation of adverbs | lessons 101 and 103 | A2 lists adverbs only inside the temporal intentions (`:1067-1068`) | 54 |
| Clauses with `коли`, `якщо`, `хоча` | lesson 116 «Complex sentences with adverbial clauses» | `якщо` and concessive clauses are B1 (`:2415`, `:2423`) | 47, 51 |
| Attributive clauses with `який` | lesson 117 «Complex sentences with attributive clauses» | B1 `:2399` onward | 49 |
| `щоб` with the past tense | lesson 118 | A2 has `щоб` of purpose only (`:1415-1416`) | 48 |

**D7 — `свій` is a small system at A2; `себе` is set phrases only.** The Standard does not list
`свій` among the A2 possessives (`:1248-1254`), but its own A2 text types require the learner to
speak and write «про … свій дім, своє місто й рідну країну» (`:930`, `:1000-1001`), and ULP uses
forms of `свій` 65 times in Season 2 and 117 times in Season 3, glossing it at lesson 44. `себе` is
B1 in the Standard (`:2107`); ULP uses it 12 times in Season 2 and 54 in Season 3 and explains it
only late in Season 3. Position 56 keeps its slug: `свій` versus `мій` / `його` as a system, the
forms of `себе` inside fixed expressions chosen by the evidence pack.

**D8 — Numerals at A2 are agreement, not declension.** The Standard's A2 has the genitive after
cardinal numerals and quantity words (`:1271-1272`), the full declension of `один` (`:1241-1242`)
and declined ordinals (`:1236-1240`). Declension of the other cardinals is B1 (`:2089`). Position 6
owns ordinals and dates, position 14 the genitive plural after quantities, position 55 numeral +
noun agreement and `один`. ULP treats numeral + noun agreement mostly in Season 4 (lessons 138,
149, 159); the Standard, not ULP, is the reason it is in A2.

**D9 — Review rhythm.** Every module closes with a recap in the ULP review shape (R-03). From
position 8 the recap story is Ukrainian only, with a glossary instead of the side-by-side English
of A1 (R-15). ULP Season 3 closes each block with a voice message; A2 checkpoints use that shape
for listening.

**D10 — The ULP history course (lessons 71–80) is reading material, not a module block.** History
as a subject belongs to the seminar tracks. Evidence packs may take short passages from it as A2
reading texts where the vocabulary fits.

## 3. Grammar at A2: system or chunk

| Item | Status at A2 | Where (position) | Standard |
| --- | --- | --- | --- |
| Sound alternations `[і]–[о]`, `[і]–[е]` | system | 5 | `:1177` |
| Sound alternations `[к]–[ц´]`, `[х]–[с´]`, `[г]–[з´]` | system | 18, 20 | `:1178-1179` |
| Sound alternations `[д]–[дж]`, `[с]–[ш]` in verbs | system | 1, recycled 43 | `:1180-1181` |
| Stress: double stress; stress that tells words apart; stress that tells forms apart | system (small), then consolidated | 5 and 14 (forms), 64 | `:1183-1188` |
| Euphony: `у / в`, `і / й`, `з / зі / із` | system (A1 position 28 recycled and widened) | 12 | `:1190-1195` |
| Intonation: statement, question, exclamation | system (small) | 64 | `:1197` |
| Noun declension types, all seven cases, singular | system, case by case | 5–31; table of types at 36 | `:1204-1221` |
| Noun, adjective and pronoun plural in all cases | met as marked forms in 15, 22, 30; system at 14 and 32–34 (D3) | 14, 32–34 | `:1201-1202`, `:1232-1233` |
| Adjectives, hard and soft group, all cases | system | 13, 19, 29; locative 20 | `:1223-1233` |
| Ordinal numerals declined; dates | system | 6 | `:1236-1240`, `:1268-1269` |
| `один` declined; cardinal + noun agreement; quantity words + genitive | system (D8) | 6, 14, 55 | `:1241-1242`, `:1271-1272` |
| Declension of other cardinal numerals | **not in A2** | — | B1 `:2089` |
| Personal pronouns, all persons, all cases | system | genitive and accusative 13 (ULP 58); dative 17 (ULP 51); instrumental 29 (ULP 62); locative 20 | `:1245-1247` |
| Possessive pronouns declined, incl. `їхній` | system | 13, 19, 29 | `:1248-1254` |
| `свій` | system (small) — D7 | 56 | required by text types `:930`, `:1000-1001` |
| `себе` | **set phrases only** — D7 | 56 | B1 `:2107` |
| Demonstratives in the oblique cases | **chunk only**, inside case phrases | 13, 19, 29 | B1 `:2108-2110` |
| Nominative: subject, naming, object of interest | system (recycled from A1) | 1, 36 | `:1258-1263` |
| Genitive without preposition: dates, negation, quantity | system | 5, 6 | `:1267-1272` |
| Genitive with `з / із / зі`, `до`, `для`, `біля`, `навпроти` | system | 9–11 | `:1274-1285` |
| Dative: recipient; age | system | 17–19, 21 | `:1287-1291` |
| Accusative: direct object; `в / у / на` of direction; `у` + day; `про` | system, recycled from A1 and widened with all pronoun forms | 1, 13, 36 | `:1293-1302` |
| Instrumental without preposition: profession or status, tool and means, object of `керувати`-type verbs | system | 25, 26 | `:1306-1313` |
| Instrumental with `з`; with `над`, `під`, `перед`, `за`, `між` | system | 24, 28 | `:1315-1322` |
| Locative: place, time (month, year), `по`, feature (`у светрі`) | system | 20 | `:1324-1332` |
| Vocative: all noun types, names with `пане / пані` | system | 27 | `:1334-1337` |
| Present tense, all conjugation patterns named by the Standard | system (A1 recycled, completed) | 1, 43 | `:1342-1353` |
| Past tense, incl. reflexive verbs | system (A1 recycled), then with aspect | 1, 40 | `:1354-1356` |
| Compound future | system (A1 recycled) | 1, 41 | `:1357-1358` |
| Perfective future | system | 41 | `:1359` |
| Synthetic future of imperfective verbs | system — D6 | 41 | B1 `:2287-2289`; ULP 98 |
| Aspect pairs as word formation | recognition at 2–3, system at 40–42 (D2) | 2–3, 40–42 | `:1380-1381` |
| Verbs of motion without prefix: `іти–ходити`, `їхати–їздити`, `летіти–літати` | system | 43 | `:1109-1110`; ULP 59 |
| Prefixed verbs of motion | system — D6 | 43 | B1 `:2336`; ULP 81–89 |
| Imperative, 2nd person (A1 recycled) and 3rd person with `хай / нехай` | system | 44 | `:1361-1365` |
| Imperative, 1st person plural | **not in A2** | — | B1 `:2293` |
| Conditional mood | **not in A2** | — | B1 `:2297`; ULP 119 |
| Comparison of adjectives: simple, compound, suppletive forms | system | 54 | `:1369-1378` |
| Formation of adverbs; temporal and manner adverbs | system (small) — D6 | 54 | `:1067-1068`; ULP 101, 103 |
| Indefinite and negative pronouns and adverbs | system (small) — D6 | 57 | ULP 102, 106 |
| Simple sentence: statement, negation, three question types, request | system (A1 recycled) | 1, 50 | `:1385-1401` |
| Compound sentences with `і (й)`, `та`, `але` | system (A1 recycled, `та` added) | 47 | `:1404-1407` |
| Clauses with `де`, `куди`, `звідки`; with `що` | system (A1 position 45 recycled) | 47, 49 | `:1408-1411` |
| Clauses of cause with `тому що`, `бо` | system | 47 | `:1412-1414` |
| Clauses of purpose with `щоб` | system | 48 | `:1415-1416` |
| Clauses with `коли`, `хоча`, `якщо`; attributive clauses with `який`; `щоб` + past | system — D6 | 47, 49, 51, 48 | B1 `:2399-2423`; ULP 116–118 |
| Participles and adverbial participles | **not in A2** — D5 | — | B1 `:2372-2375`; ULP 107–108 |
| Stylistics of vocabulary: antonyms, synonyms, epithets, metaphors | system (small) | 58 | `:1420-1425` |
| Stylistics of syntax: address, ellipsis, repetition | system (small) | address 27; ellipsis and repetition 50 | `:1427-1432` |
| Diminutive forms of nouns | met and glossed, not taught | 30 | not in the Standard's A2; ULP 93 |

## 4. No literacy phase

A2 has no literacy table: the learner reads and writes the whole alphabet, stress marks included,
after A1 positions 1–4. Handwriting recognition is recycled in the real-world reading duties of
§5 (notes, postcards, forms).

## 5. The 69 positions

`L` = estimated lessons including the recap (an estimate for sizing; the module plan decides).
Skills duty = the Standard skill the module must exercise beyond its language point
(W writing, Li listening, R real-world reading). Phase labels are the ten groups of the current
manifest.

| Pos | Slug | Phase | One-sentence job | Skills duty | L |
| --- | --- | --- | --- | --- | --- |
| 1 | `a2-bridge` | A2.1 | Show what you can do after A1 and start working in Ukrainian only: three tenses, four cases, questions — with the grammar words needed to follow a Ukrainian explanation | Li, W | 4 |
| 2 | `aspect-concept` | A2.1 | Notice that Ukrainian verbs come in pairs — one for the process, one for the result — and read a past-tense story that uses both | R | 3 |
| 3 | `aspect-in-vocabulary` | A2.1 | Learn verbs as pairs from now on: recognise the common ways a pair is formed and keep a pair list | — | 3 |
| 4 | `liudyna-i-stosunky` | A2.1 | Describe a person — appearance, clothes, character — and the people around you: neighbours, colleagues, friends (`:1074-1081`) | W (describe a friend, as in `:898-902`) | 4 |
| 5 | `genitive-intro` | A2.1 | Say what there is not and what you do not have: genitive singular of nouns, with its vowel alternations | — | 4 |
| 6 | `genitive-dates-numbers` | A2.1 | Give dates, birthdays and amounts: ordinals in the genitive, quantity words with the genitive | Li (dates and prices by ear), R (calendar, price list) | 4 |
| 7 | `foundations-practice` | A2.1 | Use everything from 1–6 in one connected situation: a first week in a new city | W (note, SMS `:927-928`) | 3 |
| 8 | `checkpoint-foundations` | A2.1 | Self-check: describe people, deny, count, date | R, Li | 2 |
| 9 | `genitive-prepositions-source` | A2.2 | Say where someone or something comes from, what something is made of and since when: `з / із / зі` + genitive | — | 3 |
| 10 | `genitive-prepositions-purpose` | A2.2 | Say who or what something is for: `для` + genitive | — | 2 |
| 11 | `genitive-prepositions-direction` | A2.2 | Say how far and next to what: `до`, `біля`, `навпроти` + genitive; give and follow directions | Li (directions), R (map) | 3 |
| 12 | `euphony-advanced` | A2.2 | Choose `у / в`, `і / й`, `з / із / зі` in connected speech and writing | — | 2 |
| 13 | `genitive-adjectives-pronouns` | A2.2 | Say whose and of which: adjectives, possessives and all personal pronouns in the genitive, and the pronoun forms of the accusative | — | 4 |
| 14 | `genitive-plural` | A2.2 | Talk about many and few: genitive plural after quantities; stress that moves between forms | — | 4 |
| 15 | `shopping-and-health` | A2.2 | Buy food, toiletries and medicine by weight, volume and amount; say how you feel at the pharmacy and the doctor's (`:1124-1129`, `:1145-1152`) | Li, R (labels, prescription, opening hours `:857-858`) | 4 |
| 16 | `checkpoint-genitive` | A2.2 | Self-check: origin, purpose, place, amounts | R, W | 2 |
| 17 | `dative-pronouns` | A2.3 | Say who likes, needs or feels something and who is how old: dative of all personal pronouns | — | 3 |
| 18 | `dative-nouns` | A2.3 | Give, tell and send something to someone: dative singular of nouns, with its consonant alternations | — | 4 |
| 19 | `dative-adjectives-pronouns` | A2.3 | Give something to my new neighbour: adjectives and possessives in the dative | — | 3 |
| 20 | `locative-expanded` | A2.3 | Say where, in which month and year, along what, and wearing what: the whole locative, with its consonant alternations | — | 4 |
| 21 | `dative-verbs` | A2.3 | Use the verbs that take the dative: help, advise, thank, call, answer | W (thank-you message) | 3 |
| 22 | `services-and-communication` | A2.3 | Get things done at the bank, post office, library, gym and in a taxi; make a simple phone call (`:1138-1143`, `:995`) | Li (phone, voicemail `:793-794`), R (forms, notices) | 4 |
| 23 | `checkpoint-dative` | A2.3 | Self-check: give, tell, help, locate | R, Li | 2 |
| 24 | `instrumental-accompaniment` | A2.4 | Say with whom and with what: `з` + instrumental | — | 3 |
| 25 | `instrumental-means` | A2.4 | Say by what means and with what tool; verbs that take the instrumental | — | 3 |
| 26 | `instrumental-profession` | A2.4 | Say what someone works as, was, and wants to become; workplaces, working hours, pay (`:1118-1122`) | W (short biography, 10–15 phrases `:906-907`) | 4 |
| 27 | `vocative-expanded` | A2.4 | Address anyone correctly: every noun type, first name with patronymic, `пане / пані` with a name or title | W (start and end a letter or e-mail) | 3 |
| 28 | `instrumental-prepositions` | A2.4 | Say above, under, in front of, behind and between; before an event | R (floor plan, seating plan) | 3 |
| 29 | `instrumental-adjectives-pronouns` | A2.4 | Talk with my old friends and with them: adjectives, possessives and all personal pronouns in the instrumental | — | 3 |
| 30 | `work-and-food` | A2.4 | Cook and eat together: dishes, tableware, ways of cooking, places to eat; follow a recipe (`:1131-1136`) | R (recipe, menu `:864`), Li (cooking show `:801-802`) | 4 |
| 31 | `checkpoint-instrumental` | A2.4 | Self-check: company, means, profession, position | R, W | 2 |
| 32 | `plural-nominative-accusative` | A2.5 | Name and see many people and things: nominative and accusative plural of nouns, adjectives and pronouns | — | 3 |
| 33 | `plural-genitive` | A2.5 | Complete the genitive plural: every noun type, with adjectives and pronouns | — | 3 |
| 34 | `plural-other-cases` | A2.5 | Use the dative, instrumental and locative plural | — | 3 |
| 35 | `dozvillia-i-khobi` | A2.5 | Talk about free time, sport and sports places, the press, television, the internet and social networks (`:1095-1099`) | Li (sports commentary, interview `:804-805`), W (social-network post) | 4 |
| 36 | `which-case-when` | A2.5 | Choose the case from the question and the preposition; read the table of noun types | — | 4 |
| 37 | `all-cases-practice` | A2.5 | Keep one story going through all seven cases, singular and plural | W (private letter `:912-914`) | 3 |
| 38 | `home-and-daily-life` | A2.5 | Rent a flat and book a hotel room; rooms, furniture, everyday objects and routines (`:1083-1093`) | R (rental advert, hotel form `:867`), W (form, guest-book entry `:936-937`) | 4 |
| 39 | `checkpoint-cases` | A2.5 | Self-check: all cases in one day of errands | R, Li, W | 2 |
| 40 | `aspect-in-past` | A2.6 | Tell what was going on and what got done: choosing the aspect in the past | — | 4 |
| 41 | `synthetic-future` | A2.6 | Say what you will be doing and what you will get done: perfective future, compound future and the one-word imperfective future | — | 4 |
| 42 | `aspect-mastery` | A2.6 | Choose the aspect in advice, plans, repeated and single actions; sound changes inside a pair | Li (advice, as ULP 91) | 4 |
| 43 | `motion-verbs` | A2.6 | Go, ride and fly there and back, one way and regularly; then arrive, leave, cross, go around and come up with the common prefixes | R (departure board), Li (station and airport announcements `:798-799`) | 7 |
| 44 | `imperative-complete` | A2.6 | Ask, instruct, forbid and wish: imperative of the 2nd person, and of the 3rd person with `хай / нехай` | R (instructions and rules `:800`, signs `:855-856`) | 4 |
| 45 | `telling-stories-and-travel` | A2.6 | Tell a trip as a story: station, bus station, airport, parts of the world, sights (`:1101-1111`) | W (postcard, travel message), Li | 4 |
| 46 | `checkpoint-verbs` | A2.6 | Self-check: aspect, futures, motion, instructions | R, Li | 2 |
| 47 | `because-and-although` | A2.7 | Give reasons and concessions and place events in time: `тому що`, `бо`, `хоча`, `коли`; link with `і`, `та`, `але` | W (short opinion with a reason `:967-968`) | 4 |
| 48 | `purpose-clauses` | A2.7 | Say what something is done for: `щоб` with the infinitive and with the past | — | 3 |
| 49 | `relative-clauses` | A2.7 | Say which one you mean: clauses with `який`; report what you know with `що`, `де`, `куди`, `звідки` | R (short newspaper item `:862`) | 4 |
| 50 | `word-order-emphasis` | A2.7 | Put the new information where a Ukrainian expects it; ellipsis and repetition in speech | Li | 3 |
| 51 | `real-conditionals` | A2.7 | Say what happens if: real conditions with `якщо` | W (invitation with a condition, change or cancel a meeting `:793-794`) | 3 |
| 52 | `education-and-work` | A2.7 | Talk about studying and working: subjects, stationery, `вчити / вивчати / вчитися`, a working day (`:1113-1122`) | W (short CV-style biography), R (timetable, job advert) | 4 |
| 53 | `checkpoint-syntax` | A2.7 | Self-check: reasons, purposes, conditions, descriptions | R, W | 2 |
| 54 | `comparison` | A2.8 | Compare things and ways of doing things: degrees of comparison of adjectives; adverbs formed from adjectives | R (advertisements `:863`) | 4 |
| 55 | `numerals-and-cases` | A2.8 | Count things correctly: numeral with noun, the forms of `один`, amounts of money, sizes and prices | Li (amounts, sizes, prices `:988-989`) | 4 |
| 56 | `sviy-and-sebe` | A2.8 | Say my own, your own, their own with `свій`; use the common fixed expressions with `себе` | W (about yourself, your family and your home `:1000-1001`) | 3 |
| 57 | `indefinite-negative-pronouns` | A2.8 | Talk about someone, something, somewhere — and no one, nothing, nowhere | — | 3 |
| 58 | `synonyms-antonyms-style` | A2.8 | Choose the better word: synonyms, antonyms, epithets and everyday metaphors | R (short original text `:861`) | 3 |
| 59 | `preferences-and-choices` | A2.8 | Say what you prefer, how sure you are, what is possible and what you hope (`:1055-1064`) | Li (survey, interview `:805`) | 3 |
| 60 | `nature-and-traditions` | A2.8 | Talk about weather, plants, farm animals and landscape; state and religious holidays, birthdays, weddings, wishes and gifts (`:1154-1163`) | Li (forecast `:801`), W (greeting card with wishes `:934`) | 4 |
| 61 | `metalanguage-words-and-cases` | A2.9 | Read and use a Ukrainian explanation about parts of speech and cases | R (textbook rule) | 2 |
| 62 | `metalanguage-verbs-and-time` | A2.9 | Read and use a Ukrainian explanation about tense, aspect and mood | R (textbook rule) | 2 |
| 63 | `metalanguage-sentences-and-classroom` | A2.9 | Follow a lesson held in Ukrainian: classroom instructions, task wording, asking the teacher | Li | 2 |
| 64 | `metalanguage-phonetics` | A2.9 | Talk about sounds, stress and intonation in Ukrainian; double stress and stress that changes the meaning | Li | 3 |
| 65 | `metalanguage-morphology` | A2.9 | Read a paradigm table and a dictionary entry in Ukrainian | R (dictionary entry) | 2 |
| 66 | `metalanguage-syntax-cases` | A2.9 | Analyse a sentence in Ukrainian the way a school textbook does: subject, predicate, the case and its question | R (textbook exercise) | 2 |
| 67 | `a2-comprehensive-review` | A2.10 | Review the level through one continuing story, block by block | R, Li | 4 |
| 68 | `a2-practice-exam` | A2.10 | Take a practice exam in the four skills at the Standard's A2 sizes: dialogue of 8–10 turns, text of 50 words, biography of 10–15 phrases | all | 3 |
| 69 | `a2-finale` | A2.10 | One full week in Ukraine, in Ukrainian only: everything together, and a look at what B1 brings | all | 3 |

**Sizing (operator, 2026-09-21): nothing is forced.** The lesson counts above are estimates for
orientation only and total 224. A module gets the lessons its content needs — not compressed to hit
a number, not stretched to fill one. The module plan decides the count; the plan review checks both
directions, cramming and dragging. Position 43 is the largest on purpose: ULP spends eight lessons
on the prefixes of motion verbs (81–84 and 86–89), and whether it stays one module or its lessons are shared
with 45 is open question 2 in §8.

## 6. Coverage against the Standard's catalogues

**Themes (14, `:1072-1163`):** Людина 4 · Дім, помешкання 38 · Щоденне життя, побут 38, 7 ·
Дозвілля, відпочинок 35 · Середовище перебування 11, 45 · Подорожі 43, 45 · Навчання 52, 63 ·
Робота 26, 52 · Купівля 15, 55 · Їжа і напої 30 · Послуги 22 · Здоров'я й особиста гігієна 15 ·
Природне середовище 60 · Традиції, звичаї, свята 60.

**Speech intentions new at A2 (`:1029-1070`):** certainty and uncertainty, possibility, hope → 59 ·
invitation → 51, 35 · simple definitions → 49 · belonging with a genitive phrase («книга мого
брата» `:1065`) → 13 · spatial relations → 11, 28 · temporal notions → 54 · cause and effect → 47 ·
prohibition → 44 · all A1 intentions are recycled in 1 and 7.

**Skills:** each writing, listening and reading text type of `:782-871` and `:926-937` has an owner
in the Skills duty column above; the practice exam at 68 checks the Standard's A2 sizes.

## 7. Immersion band mapping (plan schema §4)

Positions are unchanged, so each position keeps the band of the same module number in
`IMMERSION_POLICIES["a2"]`. Nothing is re-tuned (R-30).

| Positions | Band key | Advisory Ukrainian share |
| --- | --- | --- |
| 1–3 | `a2-bridge` | 75–100 % |
| 4–7 | `a2-ramp` | 85–100 % |
| 8–20 | `a2-m01-20` | 85–100 % |
| 21–50 | `a2-m21-50` | 90–100 % |
| 51–69 | `a2-m51-70` | 95–100 % |

A module split or merged later inherits the band of the position range it replaces. Lesson-level
structural minimums wait for `compute_lesson_immersion_band` (#8414); until then the module-level
minimums are checked on the module as a whole.

**A measured fact for whoever next revises the ULP pattern document, not a re-tune:** the step
change in the Ukrainian share of ULP's lesson notes is between Season 3 and Season 4 (51.0 % →
89.3 %), not between Season 1 and Season 2 as `docs/best-practices/ulp-presentation-pattern.md`
states. Our A2 is already more immersive than ULP Seasons 2–3; the operator's setting stands.

## 8. Open questions for the operator (each with the driver's proposed default)

1. **Keep all 69 slugs and positions (D1)?** Default: yes. The alternative — re-ordering A2 to ULP's
   exact order (plural first, accusative block between dative and instrumental) — would break URL
   parity with `/a2-v1/` and shift immersion bands for no gain the three decisions D2–D4 do not
   already deliver.
2. **Prefixed motion verbs: one large module (43) or two?** Default: one module of about seven
   lessons, because a slug for a second one does not exist and R-02 forbids squeezing. If the plan
   review finds it too long, lessons on travel situations move into 45, which is its theme partner.
3. **Metalanguage at the point of need (D4)?** Default: yes. It changes the job of positions 61–66
   from "first teaching of grammar terms" to "reading grammar explanations as a Ukrainian textbook
   words them".
4. **Participles and the conditional stay in B1 (D5)** although ULP Season 3 has them. Default: yes.
5. **`свій` as a system, `себе` as set phrases (D7).** Default: yes; the language lanes confirm from
   the sources which fixed expressions with `себе` are frequent enough for A2.

## 9. Follow-ups outside this document

- The arc generator supports `a1` only (`scripts/curriculum/arc/generate_arc.py`,
  `SUPPORTED_LEVELS = ("a1",)`) and expects a literacy table. It needs an `a2` mode with the main
  table only. Implementation task for another agent; no content is typed by hand into the YAML.
- ULP lesson 66's English title in `textbook_sections` repeats lesson 62's («Plans for New Year's
  Eve Instrumental case») while its Ukrainian title is «Спогади Місцевий відмінок» — an ingestion
  defect in the corpus, to be reported to the corpus lane.
- `curriculum/l2-uk-en/plans/a2.yaml` (71 modules, 6 phases) contradicts the manifest (69 modules,
  10 groups) and is replaced by this arc once accepted.
- Mapping-file corrections for A2 belong to #8404.
- B1 and B2 arcs: #8427, after this one is accepted, so that D5's hand-over list is B1's input.
