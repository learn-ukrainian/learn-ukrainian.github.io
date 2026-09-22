# Fresh lesson-based build — B1 arc (module grain)

> Sub-epic #8397, issue #8427. Status: **accepted by the operator 2026-09-21** (r4, by the curriculum-upgrade driver).
> r1 was reviewed by AGY `gemini-3.8-flash-high` (task `plan-review-8427-b1-arc-r1`): APPROVE with two
> MAJOR and four MINOR findings; r2 folds in five of the six and states the sixth — possessive
> adjectives, where reviewer and driver disagreed — as question 2 with both positions. The operator
> accepted the driver's proposal on all five questions of §8. **r3:** while reading the Standard's B2
> catalogue the driver found that its statement on possessive adjectives — the premise of question 2 —
> was false; that question was reopened, and the operator then chose recognition at B1 and the system
> at B2 ("option 1"). All five questions of §8 are decisions. Same method and table format as
> the accepted A1 and A2 arcs ([`fresh-build-a1-arc.md`](fresh-build-a1-arc.md),
> [`fresh-build-a2-arc.md`](fresh-build-a2-arc.md)); requirements:
> [`fresh-build-requirements.md`](fresh-build-requirements.md); schema:
> [`fresh-build-plan-schema.md`](fresh-build-plan-schema.md). This document becomes
> `curriculum/l2-uk-en/lesson-plans/b1/_arc.yaml` once accepted. It contains no Ukrainian word facts
> of its own: the only Ukrainian in it is terminology and text quoted from the State Standard, each
> with its location. Every form, stress and example is settled later, in the evidence packs, from
> the sources (R-35).

## 1. Evidence this arc is built on

Every row was read from the source on 2026-09-21.

| Strand | Source in the repo | What it fixes |
| --- | --- | --- |
| State Standard 2024, B1 | `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt:1434-2450` | the **minimum** B1 must cover (R-32). Skills `:1441-1775`: dialogue of 10–12 turns in less familiar situations (`:1746-1747`), phone call (`:1749`), written description of 50–70 words of a book, article, film or event (`:1642-1645`), theses of a talk with reasons and a conclusion (`:1646-1647`, `:1741-1742`), retelling (`:1629-1630`), letters and the most frequent documents — application, CV, autobiography, explanatory note (`:1631-1632`), lecture notes (`:1615-1617`), unadapted prose excerpts (`:1472-1473`, `:1579-1580`). 43 speech intentions (`:1777-1851`), **15 themes** (`:1853-1979`). Grammar `:1981-2450`: see §3 |
| The accepted A2 arc | `docs/epics/fresh-build-a2-arc.md` D5, D6 | what B1 receives: **handed over** — participles and adverbial participles, conditional mood, first-person-plural imperative, declension of cardinal numerals and of demonstratives, the full `себе`; **already taught at A2 on ULP evidence, so recycled and deepened here, never introduced again** — synthetic future, prefixed verbs of motion, clauses with `якщо`, `хоча`, `коли`, `який`, `щоб` + past, adverb formation, indefinite and negative pronouns |
| ULP Seasons 4–6 | `data/sources.db` `textbook_sections`, `ulp-4-00-lesson-notes`, `ulp-5-00-lesson-notes`, `ulp-6-00-lesson-notes` (lessons 121–240) | the **lesson shape**, not a grammar order (D0). The 120 lessons are topical — personal essays, interviews, state symbols, history, proverbs, slang, dialects, poetry — Ukrainian only, with grammar in small boxes scattered across them. Measured with stress marks removed: case terminology in 68 lessons, `якби` in 25, suffixes in 17, aspect terms in 16, numerals in 12, the imperative in 11, passive and impersonal forms in 13, participles in 9, adverbial participles in 6, the conditional in 6 |
| School textbooks in the corpus | `data/sources.db` `textbooks`, subject `ukrmova`: grade 5–8 Авраменко, Заболотний, Літвінова, Голуб | the **grammar order and wording** of B1 (D0): participles are introduced in grade 7 (33 chunks in Авраменко 2024) and return inside syntax in grade 8 (21 chunks in Авраменко 2025, 16 in Заболотний 2025), impersonal sentences grades 7–8, possessive adjectives grade 6 (three textbooks) |
| Live immersion policy | `scripts/config.py` `IMMERSION_POLICIES["b1"]` | one band, `b1-core`, 100 % Ukrainian. Carried over unchanged (R-30) |
| Current B1 manifest | `curriculum/l2-uk-en/curriculum.yaml`, level `b1`: 94 modules in 10 groups | the slugs and positions this arc keeps (D1) |

## 2. Decisions

**D0 — At B1 the Standard and the school textbooks order the grammar; ULP shapes the lesson.**
R-32 says ULP is the schedule. At B1 ULP has no grammar schedule to follow: Seasons 4–6 are topical
and return to grammar in small boxes wherever a text needs it (§1). What ULP does fix at this level
is the **shape of a lesson**: a Ukrainian-only text worth reading for its own sake, one small
grammar focus drawn from it, practice on that focus, vocabulary in context. Every B1 teaching lesson
has that shape. The grammar **order** follows the Standard's B1 catalogue and the order in which the
Ukrainian school textbooks of grades 5–8 build the same topics, which is also where the
explanations' wording comes from (A2 positions 61–66 prepared the learner to read them).

**D1 — Keep the 94 positions and slugs; rebuild what is inside them.** `/b1/<slug>/` parallels the
archive, the single immersion band cannot shift, and the v1 order already follows the Standard's
B1 catalogue group by group. Slugs that use English school terms (`gerunds-…` for the adverbial
participle) stay as URLs; the lessons use the Ukrainian term.

**D2 — Recycle, do not re-teach, what A2 already taught on ULP evidence.** Positions 2 and 5
(futures), 22 (real conditions), 35–40 (motion prefixes), 46 (adverbs), 77–82 (clauses with `який`,
`коли`, `якщо`, `хоча`) open with a short diagnostic recap of the A2 lesson and spend their lessons
on what B1 adds: all persons and irregular stems, the Standard's wider meaning lists, oblique-case
`який`, simultaneity versus sequence with `коли`, the unreal condition, the further concessive
conjunctions. A position whose whole job A2 already did would be a drag; none was found, but the
plan review checks each of them for it.

**D3 — Two blocks go beyond the Standard's B1; both are recognition only.**

| Item | Evidence | Standard | Position |
| --- | --- | --- | --- |
| Passive and impersonal forms, first contact | ULP Seasons 4–6: the terms occur in 13 lessons (121, 141, 153, 162, 163, 169, 172, 174, 186, 189, 190, 204 and one more); school textbooks grades 7–8 | impersonal sentences first at B2 (`:3414`) | 30 |
| Possessive adjectives | named and taught in the school textbooks (Авраменко grade 6, 2023, p. 136; Караман grade 10, 2018, p. 131); **no ULP lesson teaches them**; ULP texts use a few (an unambiguous sample of stems gives under twenty uses across Seasons 2–6) | **B2** `:3121-3126` — "adjectives of masculine gender with a zero ending" and their plurals; the Standard's own examples are possessive adjectives, though it does not use the term | 49 |

Position 30 stays a recognition module: the B2 arc owns the passive system (its first ten modules).
Position 49 likewise: the Standard places the declension of possessive adjectives at B2, and R-32
allows teaching something earlier than the Standard places it only on ULP evidence, which does not
exist here. **Correction (r3):** r1 and r2 of this arc said the Standard lists possessive adjectives at
no level. That was false. The driver and the reviewer both searched the Standard for the *term* and
not for the forms; the forms are at `:3121-3126`. See decision 2 in §8.

**D4 — The theme Суспільні відносини is owned on purpose, not in passing.** The Standard's B1 adds
a theme the lower levels do not have: social institutions, social problems, the structure of the
state, **війна і мир**, social and political events (`:1905-1910`). v1 had one candidate owner,
position 73. In a curriculum built for learners of the language of a country at war, this theme is
not an appendix: 73 owns institutions, the state and the media; 92 owns social problems as the
matter of its debates; 91 owns telling what one witnessed (`:1628`, `:1698-1699`), including the
war, in texts chosen by the evidence pack from the corpus. No lesson invents facts about the war;
every such text is sourced.

**D5 — Reading real texts starts at the beginning of the level, not at position 88.** The Standard
asks for unadapted prose excerpts, diaries, memoirs, interviews and short official papers
(`:1566-1582`). Every theme module carries one authentic or lightly abridged text from the corpus as
its reading duty; position 88 consolidates the skill on literary prose.

**D6 — Review rhythm.** Every module closes with a recap in the ULP review shape (R-03), Ukrainian
only. Checkpoints take the Season 3 "voice message" shape for listening and add a production task at
the Standard's B1 sizes.

## 3. Grammar at B1: system, recycled, or not yet

| Item | Status at B1 | Where (position) | Standard |
| --- | --- | --- | --- |
| Vowel alternations `[о]`, `[е]` with `[і]`; fleeting `[о]`, `[е]`; `[о]` with `[е]` after sibilants and `[й]` | system | 11 | `:1993-1997` |
| Consonant alternations `[г]`, `[к]`, `[х]` in the vocative, in the dative and locative, and in word formation | system | 12, recycled 57 | `:1998-2009` |
| Consonant alternations in verbs `[д]–[дж]`, `[с]–[ш]`, `[к]–[ч]`, `[т]–[ч]` | system | 13 | `:2010-2011` |
| Simplification in consonant groups | system | 15 | `:2012-2013` |
| Stress: double, word-distinguishing, form-distinguishing | recycled from A2, widened with each new paradigm | 11, 16–19 | `:2015-2020` |
| Euphony; intonation | recycled from A2 | 86 | `:2022-2028` |
| Abbreviations and shortened written forms | system | 87 | `:2030-2034` |
| Masculine noun subclasses: `-ар`, `-яр`, `-о` (surnames), sibilant stems, `-ин / -анин`, soft stems, `-ень / -ець`, adjectival nouns in `-ий` | system | 16, 17 | `:2042-2058` |
| Feminine noun subclasses: soft stems, `-ія`, zero ending, `-ість`; neuter in `-о`, `-е`, `-я` | system | 19 | `:2060-2072` |
| Pluralia tantum | system | 20 | `:2073` |
| Short-form adjectives | system (small) | 69 | `:2080-2081` |
| Ordinals in all cases, incl. compound ordinals | system | 61 | `:2086-2088` |
| `два`, `три`, `чотири` declined; indefinite numerals `багато`, `кілька`, `декілька` declined | system | 62 | `:2089-2093` |
| `себе`; demonstratives in all cases; interrogative-relative `хто`, `що`, `який`, `чий`, `котрий` | system | 63 | `:2107-2113` |
| Nominative: the ten listed meanings, incl. compound nominal predicate and object of comparison | system | 52, recycled 44 | `:2118-2133` |
| Genitive without preposition: possession, feature, part of a whole, quantity, date, negation, object of wish | system | 53 | `:2137-2156` |
| Genitive with `з`, `від`, `до`, `для`, `біля`, `серед`, `недалеко від`, `навпроти`, `посеред`, `без`; cause with `від`, `з` | system | 53, 34, 60 | `:2158-2181` |
| Dative: beneficiary, experiencer of a state, addressee, the one in need, age | system | 54 | `:2183-2192` |
| Accusative: duration; `за`, `через`, `на`, `по` in their time, path, cause, comparison and purpose meanings | system | 58, 60, recycled 34 | `:2194-2217` |
| Instrumental: status, tool, object, **path**; manner with `з`; place with `над`, `під`, `перед`, `за`, `між` | system | 56, recycled 34 | `:2219-2244` |
| Locative: place, time, `по` (path; characteristic), feature, `о / об` + hour | system | 58, 34 | `:2246-2256` |
| Vocative: the four listed functions, formal address | system | 57 | `:2258-2265` |
| Present tense patterns `запрошувати`, `мити / митися`, `брати`, `знайомити`; `дати`, `їсти` | system | 1, 32 | `:2270-2279` |
| Past tense of both aspects | recycled from A2 | 1, 4 | `:2280-2282` |
| Compound, synthetic and perfective future | recycled from A2 (D2), all persons and reflexive verbs added | 2, 5 | `:2284-2291` |
| Aspect in narration, in negation, in the imperative, in conditions | system | 6, 8, 27, 24 | follows from `:1697-1699`, "in all tense and aspect forms" |
| Imperative incl. first person plural | system | 26, 27 | `:2293-2295` |
| Conditional mood | system | 23, 24 | `:2297-2298` |
| Reflexive verbs: meanings beyond the A1 routine verbs | system | 28 | `:2272-2273` (`митися`) |
| Passive and impersonal forms | **recognition only** — D3 | 30 | B2 `:3414`; ULP Seasons 4–6 |
| Comparison of adjectives: all listed forms, suppletive pairs | recycled from A2, completed | 44, 45 | `:2302-2310` |
| Comparison of adverbs | system | 46 | `:2312-2318` |
| Comparison constructions with `ніж`, `за`, `від`, `як` | system | 44, 46 | `:2131`, `:2178`, `:2208`, `:2449-2450` |
| Word formation: agent nouns, verbal nouns, place nouns | system | 50, 31 | `:2320-2327` |
| Word formation: adjectives from nouns; adverbs from adjectives | system | 48, 46 | `:2330-2334` |
| Possessive adjectives | **recognition only** — D3, decision 2 in §8 | 49 | B2 `:3121-3126` |
| Verb formation with suffixes | system | 32 | `:2270-2271` (the `-увати` pattern) |
| Prefixed verbs of motion | recycled from A2 (D2); **new at B1:** the aspect pair of each prefixed verb (the Standard's own examples: A2 `:1381`, B1 `:2336-2338`), the preposition and case each prefix takes (`:2159-2176`, `:2202-2209`), further base verbs, figurative uses | 35–42 | `:2336-2338` |
| Simple sentence: statement and negation; the three question types, with `який?` and `яка?` added; requests, advice and proposals | recycled from A2 | 1, 26 | `:2344-2348`, `:2354-2365` |
| Negation with `немає`, `не було`, `не буде`; double negation | system | 8 | `:2349-2352` |
| Homogeneous parts of the sentence | system | 52 | `:2368-2371` |
| Participles; participle phrases | system | 65–67 | `:2372-2373` |
| Adverbial participles; adverbial-participle phrases | system | 70–72 | `:2375-2376` |
| Parenthetical words | system | 89 | `:2377-2378` |
| Compound sentences: copulative, adversative `а / але`, connective, disjunctive `або…або`, `чи…чи` | system | 75 | `:2381-2392` |
| Object clauses with `що`, `хто`, `де`, `куди`, `звідки`, `щоб`, `скільки`, `чому`, `навіщо`, `який` | system | 76 | `:2393-2401` |
| Attributive clauses with `який` in the nominative and the oblique cases | recycled (nominative), system (oblique) | 77 | `:2402-2405` |
| Time clauses with `коли`: simultaneous and sequential | recycled, system for the contrast | 78 | `:2406-2411` |
| Clauses of cause incl. `через те що` | system | 79 | `:2412-2413` |
| Real condition (`якщо`) and unreal condition (`якби`, `коли б`) | recycled (real), system (unreal) | 22, 23, 80 | `:2414-2418` |
| Clauses of purpose | recycled from A2 | 81 | `:2420-2422` |
| Concessive clauses with `хоч`, `дарма що`, `незважаючи на те що` | system | 82 | `:2423-2425` |
| Direct and reported speech | system | 83 | `:2426-2431` |
| Official and unofficial communication; stylistic means of vocabulary and syntax, incl. comparison | system | 85, 86 | `:2435-2450` |
| The passive system; impersonal sentences; possessive adjectives as a declined system; diminutives as a system; text-structuring parentheticals (`по-перше`) as a system | **not in B1** — B2 owns them | — | B2 `:3414`, `:3121-3126`, `:3466`, `:3478` |

## 4. No literacy phase

As at A2.

## 5. The 94 positions

`L` = estimated lessons including the recap (an estimate for sizing; the module plan decides).
Skills duty = the Standard skill the module must exercise beyond its language point
(W writing, Li listening, R real-world reading). Phase labels are the ten groups of the current
manifest.

| Pos | Slug | Phase | One-sentence job | Skills duty | L |
| --- | --- | --- | --- | --- | --- |
| 1 | `b1-baseline-past-present` | B1.0 | Show what you can do after A2 in the present and the past, and meet the remaining present-tense patterns the Standard names | Li, W | 3 |
| 2 | `b1-baseline-future-aspect` | B1.0 | Show what you can do with the three futures and with aspect pairs; find your gaps | Li | 3 |
| 3 | `people-and-relationships` | B1.0 | Talk about family ties, relatives, marital status, relations between people, character, clothes and fashion (`:1855-1865`) | R (interview `:1567`), W (detailed description of a person `:1639`) | 4 |
| 4 | `aspect-past-tense` | B1.0 | Choose the aspect in the past for a single result, a process, repetition and an attempt | — | 4 |
| 5 | `aspect-future-tense` | B1.0 | Choose between the three futures in plans, promises and predictions | W (promise, plan) | 3 |
| 6 | `aspect-in-narration` | B1.0 | Tell a story in which background and events use different aspects | W (retelling `:1629-1630`) | 4 |
| 7 | `daily-life-and-routines` | B1.0 | Talk about living conditions and lifestyle, hairdresser and beauty services (`:1876-1881`) | Li (phone call `:1749`), R | 3 |
| 8 | `aspect-in-negation` | B1.0 | Say what did not happen, is not there and will not be: aspect under negation, `немає / не було / не буде`, double negation | — | 3 |
| 9 | `work-and-career` | B1.0 | Talk about official employment and contract work, working hours, leave and pay (`:1930-1936`) | W (the facts of a working life, as connected text; the document forms are position 85), R (job advert) | 4 |
| 10 | `checkpoint-aspect` | B1.0 | Self-check: narrate, plan and deny with the right aspect | Li, W | 2 |
| 11 | `alternation-vowels` | B1.1 | Predict the vowel changes between forms of one word | — | 3 |
| 12 | `alternation-consonants-nouns` | B1.1 | Predict the consonant changes in the dative, locative and vocative and in word formation | — | 3 |
| 13 | `alternation-consonants-verbs` | B1.1 | Predict the consonant changes in verb forms | — | 3 |
| 14 | `health-at-the-doctor` | B1.1 | Describe symptoms, understand a diagnosis, tests and examinations, deal with the pharmacy (`:1912-1919`) | Li, R (instructions for use `:1545-1546`) | 4 |
| 15 | `simplification-consonants` | B1.1 | Spell and say words with simplified consonant groups | — | 2 |
| 16 | `noun-subclasses-masculine` | B1.1 | Decline the masculine noun types the Standard adds, surnames included | W (address an envelope `:1633`) | 5 |
| 17 | `noun-subclasses-hissing` | B1.1 | Decline nouns with sibilant stems | — | 2 |
| 18 | `restaurant-and-food` | B1.1 | Eat out: dishes, tableware, places to eat, taste preferences; make a complaint (`:1947-1952`, `:1709-1710`) | R (menu, recipe `:1570`), Li | 4 |
| 19 | `noun-subclasses-feminine` | B1.1 | Decline feminine nouns with a zero ending and in `-ість`, and the neuter types | — | 4 |
| 20 | `pluralia-tantum` | B1.1 | Use nouns that have only a plural, with numerals and adjectives | — | 2 |
| 21 | `checkpoint-morphophonemics` | B1.1 | Self-check: forms that change their sounds | R, W | 2 |
| 22 | `conditionals-real` | B1.2 | State conditions and their results in all tenses — a short step up from A2 position 51 | W (invitation with a condition) | 2 |
| 23 | `conditionals-unreal` | B1.2 | Say what would happen and what would have happened: the conditional mood, `якби`, `коли б` | — | 4 |
| 24 | `aspect-in-conditionals` | B1.2 | Choose the aspect inside conditions and wishes | — | 3 |
| 25 | `shopping-and-services` | B1.2 | Buy consumer and industrial goods, pay by cash or card, return faulty goods; bank, post office, insurance (`:1938-1945`, `:1954-1960`) | Li, W (form at the post office or bank `:1623-1624`) | 4 |
| 26 | `imperative-nuances` | B1.2 | Invite, suggest and urge with all imperative forms, the first person plural included | R (rules, prohibitions `:1798-1799`) | 3 |
| 27 | `aspect-in-imperatives` | B1.2 | Choose the aspect in requests, instructions and prohibitions | W (written instruction `:1640-1641`) | 3 |
| 28 | `reflexive-verbs-nuances` | B1.2 | Use reflexive verbs for mutual, self-directed and impersonal states | — | 3 |
| 29 | `housing-and-renting` | B1.2 | Rent and pay for housing: type and size of a home, parts of a building, furnishing, rent and utilities (`:1867-1874`) | R (rental contract excerpt, advert), W (note to a landlord `:1625-1627`) | 4 |
| 30 | `passive-voice-intro` | B1.2 | Recognise and understand passive and impersonal forms in news and notices | R (news item, official notice) | 3 |
| 31 | `verbal-nouns` | B1.2 | Form and use nouns made from verbs | R (short official paper `:1581`) | 3 |
| 32 | `verb-formation-suffixes` | B1.2 | Recognise how suffixes build verbs and conjugate the resulting patterns | — | 3 |
| 33 | `checkpoint-verbs` | B1.2 | Self-check: conditions, requests, reflexive verbs | Li, W | 2 |
| 34 | `prepositions-spatial-review` | B1.3 | Place and move things in space with every preposition and case met so far; directions of the compass (`:1831-1832`) | Li (detailed directions `:1481`, navigation `:1485-1486`) | 3 |
| 35 | `motion-base-review` | B1.3 | Use the unprefixed pairs in all tenses: one trip versus a habit, there and back versus on the way | — | 2 |
| 36 | `motion-prefixes-arrival` | B1.3 | Arriving, coming up to, reaching, dropping in: the aspect pair of each prefixed verb and the preposition and case it takes | — | 2 |
| 37 | `traveling-ukraine` | B1.3 | Plan and handle a trip in Ukraine: transport, stations, airport, booking, car service and fuel, border and customs, sights (`:1892-1903`, `:1711-1713`) | R (timetable, brochure), Li (announcements) | 5 |
| 38 | `motion-prefixes-departure` | B1.3 | Leaving, setting off, moving away: aspect pairs, prepositions and cases | — | 2 |
| 39 | `motion-prefixes-in-out` | B1.3 | Going in, out, up and down: aspect pairs, prepositions and cases | — | 2 |
| 40 | `motion-prefixes-transit` | B1.3 | Crossing, passing, going around and through: aspect pairs, prepositions and cases | — | 2 |
| 41 | `motion-flight-swim` | B1.3 | Extend the system to flying, swimming, running, carrying and leading | — | 3 |
| 42 | `figurative-motion` | B1.3 | Understand motion verbs used of time, events and states | R (newspaper article `:1566`) | 3 |
| 43 | `checkpoint-motion` | B1.3 | Self-check: a journey told and planned | Li, W | 2 |
| 44 | `adjectives-comparative` | B1.4 | Compare people, things and events with every comparative form and construction | W (compare alternatives `:1718-1719`) | 3 |
| 45 | `adjectives-superlative` | B1.4 | Single out the most and the least | R (advertising `:1569`) | 2 |
| 46 | `adverbs-comparison-formation` | B1.4 | Compare ways of doing things: the comparison of adverbs, which A2 did not teach | — | 2 |
| 47 | `nature-and-environment` | B1.4 | Talk about weather, seasons and climate, plants, farm and wild animals, natural features (`:1968-1973`) | Li (documentary excerpt `:1489`), R | 4 |
| 48 | `word-formation-adjectives` | B1.4 | Form adjectives from nouns and place names | — | 3 |
| 49 | `possessive-adjectives` | B1.4 | Recognise and understand adjectives that say whose something is, formed from a person's name or a kinship word; consolidate the adjective formation of 48 | R | 2 |
| 50 | `word-formation-nouns` | B1.4 | Form names of people by what they do and names of places by what happens there | — | 3 |
| 51 | `checkpoint-comparison` | B1.4 | Self-check: compare, and build new words | R, W | 2 |
| 52 | `homogeneous-members` | B1.5 | Build sentences with several subjects, predicates or objects; use the nominative in all its listed roles | W | 3 |
| 53 | `genitive-nuances` | B1.5 | Use the genitive for a part of a whole, a feature, a wish, and with the full B1 preposition list | — | 4 |
| 54 | `dative-nuances` | B1.5 | Use the dative for states, needs and addressees | W (personal letter `:1621-1622`) | 3 |
| 55 | `education-and-university` | B1.5 | Talk about institutions of education, fields and specialities, lectures, seminars, credits and exams (`:1921-1928`) | Li (lecture `:1457-1458`), R (course description, timetable) | 4 |
| 56 | `instrumental-nuances` | B1.5 | Use the instrumental for the path, the manner and the object of state verbs | — | 3 |
| 57 | `vocative-formal` | B1.5 | Address people formally, in all four functions the Standard lists, with the right sound changes | W (open and close a formal letter) | 3 |
| 58 | `prepositions-temporal` | B1.5 | Say when, for how long, within what time and at what hour | R (timetable, schedule) | 3 |
| 59 | `places-and-locations` | B1.5 | Describe a locality: its type and position, institutions and public places, monuments and sights (`:1962-1966`) | R (brochure, poster `:1578`), Li | 3 |
| 60 | `prepositions-cause-purpose` | B1.5 | Give the cause and the purpose with prepositions | — | 3 |
| 61 | `cases-with-ordinal-numerals` | B1.5 | Use ordinals, compound ones included, in every case; dates in full | Li (dates and years by ear) | 3 |
| 62 | `cases-with-quantity-expressions` | B1.5 | Decline `два`, `три`, `чотири` and the indefinite numerals; count people and things in every case | — | 5 |
| 63 | `advanced-pronouns` | B1.5 | Use `себе`, the demonstratives and the relative pronouns in all cases | — | 4 |
| 64 | `checkpoint-cases` | B1.5 | Self-check: every case in its B1 meanings | R, W | 2 |
| 65 | `participles-active` | B1.6 | Recognise and form active participles; tell them from adjectives | R | 3 |
| 66 | `participles-passive` | B1.6 | Recognise and form passive participles | R | 3 |
| 67 | `participle-phrases` | B1.6 | Read and build a sentence with a participle phrase | R (annotation, review `:1581`) | 3 |
| 68 | `leisure-culture-festivals` | B1.6 | Talk about museums, galleries, theatre, cinema, the philharmonic, festivals; report on a book or film (`:1883-1890`, `:1642-1643`) | W (50–70 words on a book or film), Li | 4 |
| 69 | `short-form-adjectives` | B1.6 | Recognise and use the short forms of adjectives | R (song or poem excerpt `:1472-1473`) | 2 |
| 70 | `gerunds-imperfective` | B1.6 | Say what is done at the same time: imperfective adverbial participles | — | 3 |
| 71 | `gerunds-perfective` | B1.6 | Say what was done first: perfective adverbial participles | — | 3 |
| 72 | `gerund-phrases` | B1.6 | Read and build a sentence with an adverbial-participle phrase | W | 3 |
| 73 | `society-and-media` | B1.6 | Understand and discuss social institutions, the structure of the state, war and peace, political events, and how the media report them (`:1905-1910`, `:1451-1453`) | Li (news programme `:1490-1493`), R (newspaper article) | 5 |
| 74 | `checkpoint-participles` | B1.6 | Self-check: read and compress with participles | R, W | 2 |
| 75 | `complex-compound` | B1.7 | Join clauses as equals: adding, contrasting, continuing, offering alternatives | — | 3 |
| 76 | `complex-subordinate-object` | B1.7 | Report what someone knows, asks and wants | — | 3 |
| 77 | `complex-subordinate-relative` | B1.7 | Say which one you mean with `який` in any case | — | 3 |
| 78 | `complex-subordinate-time` | B1.7 | Tell what happened at the same time and what happened next | W (event description, 50–70 words `:1644-1645`) | 3 |
| 79 | `complex-subordinate-reason` | B1.7 | Give reasons in speech and in writing | W | 2 |
| 80 | `complex-subordinate-condition` | B1.7 | Bring real and unreal conditions together in argument | — | 3 |
| 81 | `complex-subordinate-purpose` | B1.7 | State purpose and intended use (`:1805-1807`) | — | 2 |
| 82 | `complex-subordinate-concess` | B1.7 | Concede a point and still hold your view | — | 3 |
| 83 | `reported-speech` | B1.7 | Turn direct speech into reported speech and back | W (report a conversation) | 3 |
| 84 | `checkpoint-syntax` | B1.7 | Self-check: one argument, every clause type | R, W | 2 |
| 85 | `text-register-formal` | B1.8 | Write the most frequent documents: application, CV, autobiography, explanatory note, formal letter | W (`:1631-1632`), R (short official documents `:1549-1550`) | 5 |
| 86 | `text-register-informal` | B1.8 | Hold an informal conversation and correspondence: compliments, sympathy, joy, disappointment, indifference (`:1786-1787`, `:1821-1829`) | W (personal letter, social-network message), Li | 3 |
| 87 | `text-compression` | B1.8 | Take notes, shorten a text and read abbreviations | W (lecture notes, theses `:1646-1647`), R | 3 |
| 88 | `reading-literature` | B1.8 | Read an unadapted prose excerpt, a diary or memoir page, and say what the author thinks (`:1558-1559`, `:1579-1582`) | R, W (short review `:1620`) | 4 |
| 89 | `introductory-words` | B1.8 | Show how sure you are and where your thought is going with parenthetical words | — | 2 |
| 90 | `checkpoint-text-register` | B1.8 | Self-check: the same message, formal and informal | R, W | 2 |
| 91 | `narrative-mastery` | B1.9 | Tell in order an event you took part in or witnessed, unforeseen ones included, in all tense and aspect forms, with your impressions (`:1697-1699`, `:1738-1740`) | W, Li | 4 |
| 92 | `debate-and-opinion` | B1.9 | State a view on a social problem, give reasons, agree and disagree politely, manage the conversation (`:1804`, `:1810-1815`, `:1846-1849`) | Li (round-table discussion `:1504`), W (theses of a talk) | 4 |
| 93 | `comprehensive-b1-review` | B1.9 | Review the level through one continuing story, block by block | R, Li | 4 |
| 94 | `practice-exam` | B1.9 | Take a practice exam in the four skills at the Standard's B1 sizes: dialogue of 10–12 turns, description of 50–70 words, prepared talk with theses | all | 3 |

**Sizing (operator, 2026-09-21): nothing is forced.** The lesson counts above are estimates for
orientation only and total 286. A module gets the lessons its content needs — not compressed to hit
a number, not stretched to fill one. The module plan decides the count; the plan review checks both
directions, cramming and dragging. The motion block (34–43) was cut after the r1 review, which found it dragging: A2 position 43
already teaches the common prefixes, so 35, 36 and 38–40 are two lessons each and spend them on
what A2 did not teach. Positions 16, 19, 62 and 85 were raised by one lesson each for the opposite
reason.

## 6. Coverage against the Standard's catalogues

**Themes (15, `:1853-1979`):** Людина 3 · Дім, помешкання 29 · Щоденне життя, побут 7 · Дозвілля,
відпочинок 68 · Подорожі 37 · Суспільні відносини 73, 92, 91 (D4) · Здоров'я й особиста гігієна 14 ·
Освіта 55 · Робота 9 · Купівля 25 · Ресторан, кафе 18 · Послуги 25, 7 · Місця 59 · Природне
середовище 47 · Традиції, звичаї, свята 68, with Ukrainian customs and traditions (`:1979`) as the
reading texts of 60 and 69.

**Speech intentions new at B1 (`:1777-1851`):** compliment → 86 · hypothesis → 23 · need → 54 ·
arguing a view → 92, 79 · purpose and intended use → 81 · managing a conversation → 92 · advising and
dissuading → 26, 4 · joy, sorrow, sympathy, satisfaction, indifference, disappointment → 86 · hope,
care and worry → 86, 14 · membership → 53 · direction and place incl. compass → 34 · time
expressions → 58 · cause with `через`, `унаслідок`, `усупереч` → 60 · condition and result → 22, 80 ·
linking text and citing someone → 89, 83 · comparing → 44 · asking for agreement, offers and refusals,
promises → 92, 5 · characteristics and states → 3, 52.

**Skills:** each text type of `:1468-1504`, `:1561-1582`, `:1635-1648` and `:1727-1749` has an owner in
the Skills duty column; the practice exam at 94 checks the Standard's B1 sizes.

## 7. Immersion band mapping (plan schema §4)

One band for the whole level: every position 1–94 maps to `b1-core`, 100 % Ukrainian
(`IMMERSION_POLICIES["b1"]`). Nothing is re-tuned (R-30). A module split or merged later stays in
the same band. The table below is the machine-readable form the arc generator parses (#8424;
same shape as the A2 arc §7):

| Positions | Band key | Advisory Ukrainian share |
| --- | --- | --- |
| 1–94 | `b1-core` | 100 % |

## 8. Decisions on the five open questions (operator, 2026-09-21)

1. **Keep all 94 slugs and positions (D1):** yes.
2. **Possessive adjectives (49): recognition only at B1; B2 owns them as a system.** History of
   this decision, kept because it went wrong once: the operator first accepted a dedicated
   two-lesson teaching module, on the driver's statement that the Standard lists possessive
   adjectives at no level. **That statement was false** — the Standard places their declension at B2
   (`:3121-3126`) — so R-32 applies, and there is no ULP evidence for teaching them earlier. The
   driver reopened the question and put two options to the operator: recognition at B1 with the
   system at B2, or a waiver of R-32 for this one item. **The operator chose the first ("option
   1"); no waiver was taken.** Position 49 keeps its slug and two lessons: the learner meets and
   understands these adjectives in texts and consolidates the adjective formation of 48. This is in
   substance what the reviewer asked for (r1 and r2, MAJOR).
3. **The theme Суспільні відносини, війна і мир included, is owned by 73, 92 and 91 (D4)**, with
   every text about the war taken from the corpus and sourced: yes.
4. **Passive and impersonal forms at 30 are recognition only**; the system is B2's: yes.
5. **The motion block keeps ten positions** although A2 now teaches the common prefixes:
   yes for the arc, with the prefix positions cut to two lessons each (r1 review); the plan review
   of 35–40 decides whether two of them should be merged.

## 9. Follow-ups outside this document

- The arc generator needs a `b1` mode exactly as it needs an `a2` mode (#8424): main table only.
- The B2 arc (93 modules, 9 groups) follows; its input from this arc is the last row of §3.
- Mapping-file corrections for B1 belong to #8404.
