# Fresh lesson-based build — B2 arc (module grain)

> Sub-epic #8397, issue #8427. Status: **draft r2 — reviewed, not yet accepted by the operator** (by the
> curriculum-upgrade driver, 2026-09-21). r1 was reviewed by AGY `gemini-3.8-flash-high` (task
> `plan-review-8427-b2-arc-r1`): APPROVE with one MAJOR (position 63 crammed) and four MINOR findings;
> r2 folds in all five. Same method and table format as the accepted A1, A2 and B1
> arcs ([`fresh-build-a1-arc.md`](fresh-build-a1-arc.md),
> [`fresh-build-a2-arc.md`](fresh-build-a2-arc.md),
> [`fresh-build-b1-arc.md`](fresh-build-b1-arc.md)); requirements:
> [`fresh-build-requirements.md`](fresh-build-requirements.md); schema:
> [`fresh-build-plan-schema.md`](fresh-build-plan-schema.md). This document becomes
> `curriculum/l2-uk-en/lesson-plans/b2/_arc.yaml` once accepted. It contains no Ukrainian word facts
> of its own: the only Ukrainian in it is terminology and text quoted from the State Standard, each
> with its location, plus the search strings listed in D4, which are marked as such. Every form,
> stress and example is settled later, in the evidence packs, from the sources (R-35).

## 1. Evidence this arc is built on

Every row was read from the source on 2026-09-21. Where this arc says the Standard does **not** list
something, the claim rests on a search for the **forms** as well as for the term, over the whole
file (A1–C2), and D4 gives the search so that a reviewer can repeat it. That rule comes from the
error recorded in the B1 arc (D3 there).

| Strand | Source in the repo | What it fixes |
| --- | --- | --- |
| State Standard 2024, B2 | `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt:2452-3479` | the **minimum** B2 must cover (R-32). Skills `:2459-2808`: listening to texts of up to 700 words and to lectures (`:2466`), most films in the literary norm (`:2472-2473`), following complex argument (`:2483`); reading unadapted texts in different styles and genres, the author's position, small professional texts (`:2566-2573`), skimming long texts (`:2576-2577`); writing 150–200 words with paragraphs (`:2640-2642`), an overview of a book, film, play or event (`:2645-2646`), a report or essay with reasoning to a plan (`:2647-2649`), a summary of several sources (`:2650-2651`), business letters of thanks, complaint, claim, request and explanation (`:2653-2654`), an argued message for and against (`:2657-2658`); speaking before an audience (`:2729-2730`), defending a view (`:2727-2728`), a dialogue of 12–15 turns in familiar **and unexpected** situations (`:2779-2780`), solving a problem in an unforeseen situation (`:2741-2744`), complaint, threat and winning a concession (`:2745-2746`), idioms and the choice of register (`:2752-2753`), preparing and running a simple survey (`:2754-2757`), formal and informal discussion (`:2758-2760`). 52 speech intentions (`:2810-2872`), **19 themes** (`:2874-3064`). Grammar `:3066-3479`: see §3 |
| State Standard 2024, B1, C1, C2 | same file, `:1434-2450`, `:3481-4601`, `:4602-` | what B2 **receives** (the B1 catalogue, read for the comparison in §3) and what the Standard places **after** B2: rhetorical questions at C1 (`:4596`), authorial neologisms at C2 (`:5689`) — see D4 |
| The accepted B1 arc | `docs/epics/fresh-build-b1-arc.md` D3 and the last row of §3 | what B1 **hands over**: the passive system, impersonal sentences, possessive adjectives as a declined system, diminutives as a system, text-structuring parentheticals as a system. B1 positions 30 and 49 were recognition only |
| ULP | `data/sources.db` `textbook_sections`: six files, `ulp-1-00-lesson-notes` … `ulp-6-00-lesson-notes`, 40 lessons each; **the corpus holds nothing after lesson 240** | **there is no ULP schedule for B2** (D0): Seasons 4–6 are the B1 arc's evidence. What ULP still fixes is the lesson shape, and it is the R-32 evidence for the items of D4. Measured with stress marks removed (U+0301, U+0300): phraseology terms in 96 lessons (Seasons 3–6), proverbs in 46 (Seasons 2–6), synonyms in 43, word order and inversion in 8, abbreviations in 6, rhetorical questions in 2, neologisms in 2, borrowings in 2, collective or fractional numerals in 1, the pluperfect in **0**, parcelling in **0** |
| School textbooks in the corpus | `data/sources.db` `textbooks`, subject `ukrmova`, grades 8–11: Авраменко 8 (2025), Заболотний 8 (2025), Авраменко 9 (2017), Авраменко 10 (2018), Глазова 10 (2018), Караман 10 (2018), Авраменко 11 (2019), Глазова 11 (2019) | the **grammar order and wording** of B2 (D0). Chunks that use the term, by grade: one-member sentences 8 → 75; detached members 8 → 65, 11 → 26; parenthetical words 8 → 35, 11 → 25; impersonal sentences 8 → 20, 10 → 11, 11 → 12; asyndetic complex sentences 9 → 25, 11 → 18; passive 10 → 14, 11 → 30; style 10 → 227, 11 → 156; phraseology 10 → 108; synonyms 10 → 92; numerals 6 → 109, 10 → 45, 11 → 33; possessive adjectives 6 → 15, 10 → 11, 11 → 8. The pluperfect occurs in **no** school textbook chunk (only in 12 university-level chunks); parcelling in one grade-11 chunk. These are counts of chunks whose lower-cased text contains the term's stem; the reviewer, using its own stems, confirmed the zeros and the grade distribution and got counts within about a tenth of these. They show where the textbooks treat a topic; nothing in this arc is sized from them |
| Live immersion policy | `scripts/config.py` `IMMERSION_POLICIES["default"]`, band `b2+`; `TRACK_CONFIG["b2"]["immersion_range"] = [1.0, 1.0]` | one band, 100 % Ukrainian, sentences of at most 35 words. Carried over unchanged (R-30) |
| Current B2 manifest | `curriculum/l2-uk-en/curriculum.yaml`, level `b2`: 93 modules in 9 groups | the slugs and positions this arc keeps (D1). The 93 v1 plans under `curriculum/l2-uk-en/plans/b2/` were read for their titles only, to learn what each slug was meant to be; they are **not** an input to any plan, pack or lesson (R-11) |

## 2. Decisions

**D0 — B2 has no ULP schedule; the Standard and the school textbooks order the grammar, and ULP
still shapes the lesson.** R-32 makes ULP the schedule, but the ULP material in the corpus ends with
lesson 240 and the B1 arc uses all of Seasons 4–6. At B2 the order therefore follows the Standard's
B2 catalogue and the order in which the Ukrainian school textbooks build the same topics: the simple
and the complicated simple sentence in grade 8, the complex sentence in grade 9, style, vocabulary,
phraseology and the return to morphology in grades 10 and 11 (§1). The v1 order already runs that
way: sentence structure (B2.0–B2.2), style and register (B2.3), morphology revisited (B2.4–B2.5),
vocabulary (B2.6–B2.7), communication (B2.7–B2.8). The **lesson shape** stays the ULP shape of the
B1 arc: a Ukrainian text worth reading for its own sake, one focus drawn from it, practice on that
focus, vocabulary in context.

**D1 — Keep the 93 positions and slugs; rebuild what is inside them.** `/b2/<slug>/` parallels the
archive and the single immersion band cannot shift. Slugs that use English school terms
(`pluperfect-tense`, `third-person-plural-passive`) stay as URLs; the lessons use the Ukrainian
term.

**D2 — Recycle, do not re-teach, what B1 already taught.** The Standard says B2 covers every aspect
of A1, A2 and B1 with wider vocabulary, more syntactic structures and more situations
(`:3075-3077`), so much of the B2 catalogue repeats B1's. A position whose topic B1 owned opens with
a short diagnostic recap of the B1 lesson and spends its lessons on what B2 adds:

| Position | B1 owner | What B2 adds |
| --- | --- | --- |
| 2, 9, 11, 12 (participles) | 65–67 | the participle inside passive constructions; the participle phrase against the attributive clause with `який`, `котрий`, `що` in the oblique cases (`:3401-3402`, `:3427-3429`) |
| 19 (homogeneous members) | 52 | the generalising word (`:3399-3400`) |
| 22 (parenthetical words) | 89 | inserted constructions (`:2661-2663`) and the text-structuring set as a system (`:3478-3479`) |
| 30 (reported speech) | 83 | nothing new in the forms — B1 already reports questions with `чи` (`:2429-2431`); B2 adds the uses: appealing to a speaker's words (`:2865-2866`) and summarising several sources in writing (`:2650-2651`) |
| 47, 48, 49, 51 (cases) | 53, 54, 56, 58 | compared meaning by meaning with B1 `:2118-2265`, the B2 case catalogue adds little: the genitive of the subject of an action named by a verbal noun (`:3186-3187`); the accusative of the path without a preposition (`:3231`), with `на` for cause, purpose and intended use (`:3240-3244`), with `під` and with `повз` (`:3245-3247`). The dative, instrumental, locative and vocative lists add no meaning. The new content of these positions is therefore the **noun types new at B2** (D3) and the wider vocabulary and situations the Standard asks for (`:3075-3077`) |
| 57 (conditional mood) | 23, 24, 80 | no new form (`:3323-3324` against B1 `:2297-2298`, `:2417`); B2 adds the uses: hypothesis (`:2830`), polite advice and dissuasion (`:2838`) |
| 58 (numerals: time and dates) | 61 | clock time and dates as declined expressions (`:3132-3135`); the full paradigms of ordinals and of compound ordinals (`:3136-3144`) |
| 60–63 (word formation) | 50, 48, 46 | the zero-suffix activity nouns (`:3363-3364`); the adjective types of D3 |
| 64, 65 (conjunctions) | 75–82 | `котрий` and `що` as relative words beside B1's `який` (`:3427-3429` against `:2402-2405`); sequence in time with `доки`, which is the Standard's own example (`:3435`) |
| 36 (official and unofficial) | 85, 86 | the choice of register by situation as a speaking skill (`:2752-2753`) |

A position whose whole job B1 already did would be a drag; none was found, but the plan review
checks each row above for it.

**D3 — What B2 owns as a system.** Each item names the position that owns it.

| Item | Standard | Owner |
| --- | --- | --- |
| The passive: the participle construction, the forms in `-но`, `-то`, the reflexive verb with a passive meaning, the indefinite-personal sentence used instead of a passive | `:3401-3402`, `:3413-3415`; the Standard does not use the term "passive" and gives the forms inside the participle phrase and the one-member sentences | 1–7, 10 |
| One-member sentences: definite-personal, indefinite-personal, impersonal, nominative | `:3409-3418` | 18, with 3 and 6. The order is deliberate: 3 and 6 teach the impersonal and the indefinite-personal sentence first, each as one way of leaving the doer unnamed, because that is where a reader of news meets them; 18 then names the four types and brings them together. 3 and 6 need nothing from 18 |
| Possessive adjectives as a declined system: "adjectives of masculine gender with a zero ending" and their plural | `:3121-3122`, `:3125-3126` | **63** — the slug `possessive-adjectives` exists only at B1 (49, recognition); at B2 the formation and the declension get lessons of their own inside 63 |
| Compound adjectives in `-лиций`; compound adjectives whose first part is a cardinal numeral | `:3123-3124`, `:3128-3129` | 63 |
| Noun types new at B2: masculine in `-а` (`:3089-3090`), masculine soft stems in `-о` (`:3092-3093`), feminine and neuter nouns of adjectival origin (`:3101-3102`, `:3109-3110`), `матір` among the feminine zero-ending nouns (`:3103-3104`), neuter nouns with the suffixes `-ат-`, `-ят-`, `-ен-` (`:3106-3108`), nouns of common gender (`:3112`), abbreviations and clipped compounds (`:3113-3114`), place names of two words (`:3085-3086`) | as cited | **no v1 slug owns them.** 47 (masculine types), 48 (neuter with a suffix, `матір`), 49 (adjectival nouns, common gender), 37 (abbreviations) — one lesson each, counted in L. See question 2 in §8 |
| Declension of cardinal numerals from 5 to 100 and of compound cardinals | `:3145-3149` | 59 |
| `скільки` and the indefinite pronouns in all cases | `:3161-3165` | 52 |
| Diminutives, and with them the other stylistic means of vocabulary the B2 list adds to B1's (`:2437-2442`): homonyms, shortenings, compound words, onomatopoeia | `:3462`, `:3465-3469` | 33, recycled as reading in 39 |
| The formation of aspect pairs as a listed item | `:3348-3350` | 54 |
| Activity nouns with a zero suffix | `:3363-3364` | 61 |
| The generalising word with homogeneous members; the question with a shade of invitation; `котрий` and `що` as relative words | `:3399-3400`, `:3388-3389`, `:3427-3429` | 19, 50, 65 |
| Text-structuring parentheticals | `:3478-3479`, `:2659-2660` | 22, 27 |
| Specification and text structuring as stylistic means of syntax — the two the B2 list adds to B1's address, ellipsis, repetition and comparison (`:2444-2450`) | `:3477-3479` | 34, 27 |
| Euphony as a stylistic means: `у / в`, `і / й`, `з / зі / із` | `:3453-3458` | 32 |

**D4 — What v1 taught at B2 that the Standard does not place at B2.** R-32 allows teaching something
earlier than the Standard places it only on ULP evidence. Searches were run on the whole file with
stress marks irrelevant (the Standard prints none).

| Item | Position | Standard | Evidence | This arc |
| --- | --- | --- | --- | --- |
| The pluperfect | 56 | **listed at no level.** Searched: the terms `давноминул`, `давньоминул`, `передминул`; the form pattern of a past form of `бути` next to another past form, in both orders. Only hits: `був хворий` (`:1070`), `була неймовірна спека` (`:3277`), a book title (`:5769`) — none is a pluperfect | ULP: no lesson. School textbooks: no chunk. University-level chunks: 12 | **recognition only**, two lessons: the learner meets and understands it in literary texts. Question 3 in §8 |
| Parcelling | 29 | listed at no level (term `парцел`) | ULP: none. Textbooks: one grade-11 chunk | recognition only, inside 29; the rest of the module is ellipsis, which the Standard lists at B1 (`:2446-2447`) and again at B2 (`:3472-3473`), so 29 is a small module |
| Rhetorical questions | 50 | **C1** (`:4596`) | ULP: 2 lessons of Season 4. Textbooks: grade 10 → 19 chunks, grade 11 → 35 | recognition and guided use; the system content of 50 is the Standard's B2 question types, the question with a shade of invitation included (`:3383-3389`) |
| Collective and fractional numerals | 59 | listed at no level. Searched: the terms `збірн`, `дробов`; **search strings** `двоє`, `троє`, `четверо`, `обидва`, `обидві`, `обоє`, `півтора`, `третин`, `половин`, `чверт`. Only hit: `півтори тисячі років` (`:1291`), inside an A2 example of another point | ULP: 1 lesson of Season 4. Textbooks: grade 6 → 22 chunks, grades 10–11 → 16 | one lesson inside 59 **if** the evidence pack shows from the corpus that a B2 reader meets them often; otherwise recognition. The arc does not assert their frequency |
| Present active participles | 9 | the Standard's B2 has the participle phrase only (`:3401-3402`) | ULP: 2 lessons. Textbooks: grade 7 → 5 chunks, grades 10–11 → 9 | recognition, and the constructions Ukrainian uses instead; the norm is taken from the style-guide sources in the pack, not from the arc |
| Neologisms and borrowings | 77 | authorial neologisms at C2 (`:5689`); borrowings listed at no level (term `запозичен`) | ULP: 4 lessons. Textbooks: grade 10 → 72 chunks | a **vocabulary and reading** module for the themes Наука і техніка and Медіа й соціальні мережі, not a grammar claim; nothing here is taught ahead of the Standard |

Everything else v1 had at B2 is inside the Standard's B2: aspect pairs formed with a suffix are the
Standard's own examples (`:3348-3350`) for 54; synonyms, homonyms, epithets and metaphors are listed
(`:3460-3464`) for 33 and 67–69; idioms and phraseology are a B2 speaking skill (`:2752-2753`) for
70–76; correlative words stand in the Standard's own examples (`:3428-3429`, `:3477`) for 25;
stressing what is important is a B2 intention (`:2871-2872`) for 26.

**D5 — Three of the Standard's 19 themes have no module of their own; they are owned as duties.**
v1 has theme modules for sixteen themes. Людина (`:2876-2889`), Подорожі (`:2924-2935`) and Природне
середовище (`:3040-3045`) have none, and B1 already gave each a full module (B1 positions 3, 37, 47).
What B2 adds to them is small and specific — career and professional growth, conflicts in the family
and between generations, the history of a family; tour companies, green and rural tourism; ecology —
and each addition gets a named owner in §6 instead of a new position. Because every B2 lesson is
built on a text (D0), a grammar module can carry a theme without losing its focus. Question 1 in §8.

**D6 — Суспільні відносини is again owned on purpose.** The Standard's B2 widens the theme: social
and political events and movements, youth subcultures, rights and duties, crime, law enforcement,
equality and justice, contested questions (`:2937-2949`), and asks the learner to speak about social
and international relations (`:2717-2718`). 44 owns the state, political events and movements, and
війна і мир; 45 owns rights and duties, crime, law enforcement, equality and justice; 86 owns the
contested questions as the matter of its debates; 41 and 84 own how the media report all of it. The
rule of the B1 arc stands: no lesson invents facts about the war; every such text is chosen by the
evidence pack from the corpus and sourced.

**D7 — The skills are owned, at the Standard's B2 sizes.** Writing of 150–200 words in paragraphs,
listening to texts of up to 700 words, a dialogue of 12–15 turns. Every text type of `:2495-2533`,
`:2581-2607`, `:2666-2681` and `:2765-2783` has an owner in the Skills duty column of §5. Reading
real texts continues from the first position, as at B1.

**D8 — Review rhythm.** Every module closes with a recap in the ULP review shape (R-03), Ukrainian
only. Each checkpoint adds a production task at the Standard's B2 sizes.

## 3. Grammar at B2: system, recycled, or not yet

| Item | Status at B2 | Where (position) | Standard |
| --- | --- | --- | --- |
| Noun declension: the types B1 already taught | recycled from B1 | 47–49 | `:3085-3100`, `:3105`, `:3111` |
| Noun declension: the types new at B2 (D3) | system | 47, 48, 49, 37 | `:3089-3114` |
| Adjective declension, hard and soft | recycled | 63 | `:3117-3120` |
| Possessive adjectives: formation and declension, singular and plural | system — D3 | 63 | `:3121-3122`, `:3125-3126` |
| Compound adjectives in `-лиций` and with a numeral as first part | system (small) | 63 | `:3123-3124`, `:3128-3129` |
| Numerals for clock time and dates, in all cases | recycled from B1, completed | 58 | `:3132-3135` |
| Ordinals of thousands; compound ordinals | recycled from B1, completed | 58 | `:3136-3144` |
| Cardinals `один`–`чотири`, 5–20, the tens, 40, 90, 100, and compound cardinals, in all cases | system | 59 | `:3145-3149` |
| Collective and fractional numerals | **conditional** — D4 | 59 | listed at no level |
| Personal, possessive, reflexive and demonstrative pronouns | recycled from B1 | 52 | `:3152-3158` |
| `хто`, `що`, `який`, `чий`, `котрий`, `скільки` in all cases | recycled; system for `скільки` | 52 | `:3159-3161` |
| Indefinite pronouns in all cases | system | 52 | `:3162-3165` |
| Nominative: the five listed meanings, the compound nominal predicate included | recycled from B1 | 51, 15 | `:3170-3178` |
| Genitive without a preposition | recycled; new: the subject of an action named by a verbal noun (D2) | 47 | `:3182-3195` |
| Genitive with prepositions | recycled from B1 | 47 | `:3197-3215` |
| Dative: beneficiary, subject of a state, age | recycled from B1 | 48 | `:3217-3223` |
| Accusative without and with prepositions | recycled; new: the path without a preposition, `на` for cause, purpose and intended use, `під`, `повз` (D2) | 51 | `:3225-3247` |
| Instrumental without and with prepositions | recycled from B1 | 49 | `:3249-3271` |
| Locative: place, time, `по`, feature, `о / об` | recycled from B1 | 51 | `:3273-3284` |
| Vocative: the four listed functions | recycled from B1; addressing an audience and a speaker is new | 51, 85 | `:3286-3293`, `:2863-2864` |
| Present, past and the three futures; `дати`, `їсти` | recycled | 54 | `:3298-3317` |
| Aspect pairs, the suffixal pairs included | system | 54 | `:3348-3350` |
| Aspect in the imperative and with the infinitive | system | 55 | follows from `:3319-3321` and `:3391-3393` |
| Imperative, all forms incl. `хай / нехай` | recycled from B1 (`:2293-2295`) | 55 | `:3319-3321` |
| Conditional mood, `якби` | recycled from B1; new uses only (D2) | 57 | `:3323-3324` |
| The pluperfect | **recognition only** — D4 | 56 | listed at no level |
| Comparison of adjectives and adverbs | recycled from B1 | 63, 34 | `:3328-3346` |
| Prefixed verbs of motion | recycled from A2 and B1 | 35 | `:3352-3354` |
| Word formation: persons by activity | recycled from B1, widened | 60 | `:3356-3357` |
| Word formation: activity nouns in `-нн-`, `-енн-`, `-інн-` and with a zero suffix; abstract nouns | recycled; system for the zero suffix | 61 | `:3359-3364` |
| Word formation: place nouns | recycled from B1 | 62 | `:3366-3367` |
| Word formation: adjectives from nouns, adverbs from adjectives | recycled from B1 | 63 | `:3369-3373` |
| Simple sentence: statement, negation, the question types, the question with a shade of invitation, the imperative sentence | recycled; system for the invitation question | 50, 55 | `:3377-3393` |
| Rhetorical and deliberative questions | **recognition and guided use** — D4 | 50 | C1 `:4596` |
| Word combinations: agreement and government; predicate types; secondary parts of the sentence, apposition | system (small) — the Standard names the compound nominal predicate (`:3173-3174`) and specification (`:3477`); the rest is the school-grammar frame of grade 8 that the following positions need | 14, 15, 16 | `:3173-3174`, `:3252-3253`, `:3477` |
| Homogeneous members with a generalising word | system | 19 | `:3396-3400` |
| Participle phrase; adverbial-participle phrase; detached members | recycled from B1; system for detachment and its punctuation | 12, 20 | `:3401-3404` |
| Parenthetical words and inserted constructions | recycled; system for inserted constructions | 22 | `:3405-3406`, `:2661-2663` |
| Address | recycled | 34, 51 | `:3407`, `:3471` |
| One-member sentences, all four types | system — D3 | 18, 3, 6 | `:3409-3418` |
| The passive system | system — D3 | 1–7 | `:3401-3402`, `:3413-3415` |
| Present active participles | **recognition only** — D4 | 9 | — |
| Object clauses; attributive clauses with `який`, `котрий`, `що` in all cases | recycled; system for `котрий`, `що` | 65, 12 | `:3422-3429` |
| Time clauses: simultaneous and sequential, `доки` | recycled; system for `доки` | 65 | `:3431-3435` |
| Clauses of cause and of purpose (the Standard's example under cause is a clause with `щоб`, `:3437-3438`) | recycled | 65 | `:3437-3438` |
| Real and unreal condition; concession | recycled | 65, 57 | `:3440-3445` |
| Coordination | recycled | 64 | follows from `:3396-3398` and the B1 catalogue |
| Sentences of several clauses with different kinds of link | system (small) | 23 | follows from `:3072-3074` ("complex syntactic forms") |
| Correlative words | system (small) | 25 | `:3428-3429`, `:3477` |
| Word order, logical stress, inversion | system | 26 | `:2871-2872`, `:2659-2660` |
| Direct and reported speech, reported questions with `чи` | recycled from B1 | 30 | `:3446-3449` |
| Euphony as a stylistic means | recycled from A2 and B1, as a system | 32 | `:3453-3458` |
| Stylistic means of vocabulary: antonyms, synonyms, epithets, metaphors — recycled from B1; homonyms, shortenings, diminutives, compound words, onomatopoeia — system | recycled and system | 33, 67–69 | `:3459-3469` |
| Stylistic means of syntax: address, ellipsis, repetition, comparison — recycled from B1; specification and text structuring — system | recycled and system | 34, 29, 27 | `:3470-3479` |
| Parcelling | **recognition only** — D4 | 29 | listed at no level |
| Official and unofficial communication | recycled from B1, widened | 36–41, 43 | `:3452`, `:2752-2753` |
| Rhetorical questions as a system; authorial neologisms; the C1 and C2 stylistic catalogue | **not in B2** | — | C1 `:4596`, C2 `:5689` |

## 4. No literacy phase

As at A2 and B1.

## 5. The 93 positions

`L` = estimated lessons including the recap (an estimate for sizing; the module plan decides).
Skills duty = the Standard skill the module must exercise beyond its language point
(W writing, Li listening, R real-world reading, S speaking). Phase labels are the nine groups of the
current manifest.

| Pos | Slug | Phase | One-sentence job | Skills duty | L |
| --- | --- | --- | --- | --- | --- |
| 1 | `passive-voice-system` | B2.0 | See the whole system: four ways Ukrainian leaves the doer unnamed, and which text uses which | R (news item, official notice) | 3 |
| 2 | `past-passive-participles` | B2.0 | Form passive participles with confidence — a short step up from B1 position 66 — and use them as a predicate | — | 3 |
| 3 | `b2-impersonal-passive` | B2.0 | Use the forms in `-но`, `-то` to report a result without a doer (`:3414-3415`) | R (report, chronicle), W (report what was done) | 4 |
| 4 | `dim-zhytlo` | B2.0 | Talk about repair, replanning and restoration of a home, the property market and buying a home (`:2899-2900`) | R (property advert `:2583-2587`), Li, W (business letter of claim `:2653-2654`) | 4 |
| 5 | `reflexive-passive` | B2.0 | Recognise and use reflexive verbs with a passive meaning, and tell them from the other reflexive meanings of B1 position 28 | R (instructions `:2590`, `:2597`) | 3 |
| 6 | `third-person-plural-passive` | B2.0 | Use the indefinite-personal sentence when the doer is unknown or unimportant (`:3413`) | Li (announcements `:2507-2508`) | 3 |
| 7 | `passive-in-context` | B2.0 | Choose among the four constructions by style: scientific, official, media, conversational | W (rewrite one message for two styles) | 3 |
| 8 | `pobut-shchodenne` | B2.0 | Talk about conditions and style of life, everyday objects, time and space (`:2902-2906`) | Li (everyday conversation in noise `:2738-2739`), S | 3 |
| 9 | `active-participles-present` | B2.0 | Recognise present active participles and use the constructions Ukrainian prefers instead (D4) | R | 2 |
| 10 | `checkpoint-passive-voice` | B2.0 | Self-check: report events without naming the doer, in the right style | R, W | 2 |
| 11 | `active-participles-past` | B2.1 | Recognise and form past active participles — a short step up from B1 position 65 | R | 2 |
| 12 | `participles-vs-relative-clauses` | B2.1 | Choose between a participle phrase and an attributive clause — `котрий` and `що` appear here only as alternatives to a participle; the clause system is 65's; describe a person's looks, character, habits and aims (`:2882-2883`) | W (detailed description of a person `:2674`) | 3 |
| 13 | `zdorovya-i-medytsyna` | B2.1 | Talk about diagnostics, emergency help, addictions, folk and conventional medicine (`:2964-2967`) | Li, R (description of a medicine `:2588-2589`), S (patient) | 4 |
| 14 | `phrases-word-combinations` | B2.1 | Get agreement and government right: which case a verb, a noun or an adjective requires | — | 3 |
| 15 | `predicate-types` | B2.1 | Build simple and compound predicates, the compound nominal predicate included (`:3173-3174`, `:3252-3253`) | — | 3 |
| 16 | `secondary-sentence-members` | B2.1 | Expand a sentence with attributes, objects, adverbial parts and apposition (`:3477`) | W | 2 |
| 17 | `sport-i-dozvillia` | B2.1 | Talk about sports, sports facilities and equipment, achievements and records, and cultural leisure (`:2908-2922`) | Li (sports programme `:2512-2514`), R (report `:2607`) | 4 |
| 18 | `b2-one-member-sentences` | B2.1 | Recognise and use the four types of one-member sentence (`:3409-3418`) | R (diary, memoir `:2606`) | 4 |
| 19 | `homogeneous-members` | B2.1 | Build series with a generalising word and punctuate them (`:3399-3400`) | W | 3 |
| 20 | `detached-members` | B2.1 | Detach a participle phrase, an adverbial-participle phrase and a specifying part, with the punctuation (`:3401-3404`, `:3477`) | W, R | 4 |
| 21 | `checkpoint-syntax-i` | B2.1 | Self-check: the simple sentence, plain and complicated | R, W | 2 |
| 22 | `parenthetical-expressions` | B2.2 | State your own position and add accompanying information with parenthetical words and inserted constructions (`:2661-2663`, `:3478-3479`) | W | 3 |
| 23 | `multi-clause-sentences` | B2.2 | Read and build a sentence of several clauses with different kinds of link | R (journal article `:2510`) | 3 |
| 24 | `kharchuvannia-i-kukhnia` | B2.2 | Talk about culinary traditions, diets and kinds of eating, taste preferences; order a banquet (`:3006-3014`) | R (recipe `:2595`), W (recipe, instruction `:2677`), S | 4 |
| 25 | `correlative-constructions` | B2.2 | Tie a clause to a pointing word in the main clause (`:3428-3429`, `:3477`) | — | 2 |
| 26 | `emphasis-and-inversion` | B2.2 | Stress what matters with word order and with the phrases the Standard lists (`:2871-2872`) | S (prepared talk) | 3 |
| 27 | `stylistic-connectors` | B2.2 | Organise a written text: listing, specifying, stressing importance (`:2659-2660`) | W (150–200 words in paragraphs `:2640-2642`) | 3 |
| 28 | `kupivlia-i-servisy` | B2.2 | Buy on the internet, read information and advertising, complain; insurance, car service, courses, ordering services and a claim about poor work (`:2994-3004`, `:3016-3027`) | S (complaint, winning a concession `:2745-2746`), W (letter of complaint) | 4 |
| 29 | `complex-syntax-ellipsis-parcelling` | B2.2 | Use ellipsis in speech and writing — a step up from B1 (`:3472-3473`); recognise parcelling in media and fiction (D4) | Li (everyday conversation) | 2 |
| 30 | `direct-indirect-speech` | B2.2 | Quote and report in longer texts: refer to someone's view and appeal to a speaker's words (`:3446-3449`, `:2856`, `:2865-2866`) | W (summary of several sources `:2650-2651`) | 3 |
| 31 | `checkpoint-syntax-ii` | B2.2 | Self-check: one argument in complex sentences, with sources quoted and reported | R, W | 2 |
| 32 | `phonetic-stylistic-devices` | B2.3 | Make speech and writing euphonic: `у / в`, `і / й`, `з / зі / із` as a system (`:3453-3458`) | S (read aloud), W | 2 |
| 33 | `lexical-stylistic-devices` | B2.3 | Use antonyms, homonyms, epithets, metaphors, diminutives, compound words and onomatopoeia on purpose (`:3459-3469`) | R (poem, song `:2500`) | 4 |
| 34 | `syntactic-stylistic-devices` | B2.3 | Use address, repetition, comparison and specification as means of style (`:3470-3477`) | W | 3 |
| 35 | `mistsia-i-oriientyry` | B2.3 | Describe a locality, monuments and places of memory, a city's development plan and its problems, suburbs and country life; plan a trip with a tour company, green and rural tourism (`:3029-3038`, `:2924-2935`) | S (problem in an unforeseen situation `:2741-2744`), R (brochure `:2602`) | 5 |
| 36 | `register-formal-informal` | B2.3 | Choose the official or unofficial register by situation (`:2752-2753`) | Li, S | 3 |
| 37 | `register-business-ukrainian` | B2.3 | Write and read business papers: CV, explanatory note, complaint, letter of thanks; decline abbreviations (`:2605`, `:3113-3114`) | W (business letters `:2653-2654`), R | 4 |
| 38 | `register-formal-written` | B2.3 | Read and write in the scientific and the legal style: programmes, contracts, reports, guarantees (`:2677-2681`) | R (small professional text `:2573`), W | 4 |
| 39 | `tradytsii-i-zvychai` | B2.3 | Talk about state, religious and family holidays, wishes and gifts, funerals and condolences, Ukrainian customs (`:3058-3064`) | W (essay on national traditions `:2666-2667`), Li | 4 |
| 40 | `register-literary-ukrainian` | B2.3 | Read original prose at the B2 level and say what the author thinks (`:2603-2604`, `:2572`) | R, W (overview of a book `:2645-2646`) | 4 |
| 41 | `register-public-discourse` | B2.3 | Follow and produce media and conversational speech: news, interviews, talk shows (`:2512-2519`) | Li (text of up to 700 words `:2466`), S | 4 |
| 42 | `checkpoint-register-domain` | B2.3 | Self-check: recognise the style of a text and answer in kind | R, W | 2 |
| 43 | `register-practice-cross-register-rewriting` | B2.4 | Rewrite one message across registers | W | 3 |
| 44 | `politics-government-vocabulary` | B2.4 | Discuss social institutions, the structure of the state, political events and movements, war and peace (`:2937-2942`, `:2717-2718`) | Li (news), R (newspaper article `:2593`), S | 5 |
| 45 | `law-justice-vocabulary` | B2.4 | Discuss rights and duties, crime, law enforcement, equality and justice (`:2944-2948`) | S (witness of an event `:2559`), R | 4 |
| 46 | `economics-business-vocabulary` | B2.4 | Discuss the economy, the family budget, income, spending and taxes, poverty (`:2951-2955`) | R (article), W (argued message for and against `:2657-2658`) | 4 |
| 47 | `genitive-advanced` | B2.4 | Decline the masculine noun types new at B2 (D3); use the genitive in B2-size texts, the subject of a verbal noun included (D2) | — | 4 |
| 48 | `dative-advanced` | B2.4 | Decline neuter nouns with a suffix and `матір` (D3); use the dative for states and benefit in B2-size texts | — | 3 |
| 49 | `instrumental-advanced` | B2.4 | Decline nouns of adjectival origin and of common gender (D3); use the instrumental in B2-size texts | — | 3 |
| 50 | `questions-deliberative-rhetorical` | B2.4 | Ask every kind of question the Standard lists, invite with a question; recognise rhetorical questions (D4) | S (survey with leading questions `:2754-2757`) | 3 |
| 51 | `advanced-case-semantics` | B2.4 | Use the accusative meanings B2 adds — path, `на` for cause, purpose and intended use, `під`, `повз` (D2) — and bring all seven cases together | — | 3 |
| 52 | `pronoun-system-advanced` | B2.4 | Decline `скільки` and the indefinite pronouns; use the whole pronoun system in connected text (`:3152-3165`) | — | 4 |
| 53 | `checkpoint-cases-morphology` | B2.4 | Self-check: every case and every noun type | R, W | 2 |
| 54 | `aspect-nuances-secondary-imperfectivization` | B2.5 | Form and choose aspect pairs, the suffixal ones included (`:3348-3350`) | — | 3 |
| 55 | `aspect-nuances-imperative-infinitive` | B2.5 | Choose the aspect in every imperative form and with the infinitive — the forms are B1's (`:3319-3321`) | S (advice, prohibition, threat `:2867`) | 3 |
| 56 | `pluperfect-tense` | B2.5 | Recognise and understand the pluperfect in literary texts (D4) | R | 2 |
| 57 | `conditional-mood-particles` | B2.5 | Use the conditional for politeness, wish, advice and hypothesis (`:2830`, `:3323-3324`) | S | 3 |
| 58 | `numeral-declension-time-dates` | B2.5 | Say and write any time and date in any case (`:3132-3144`) | Li (dates and times by ear) | 3 |
| 59 | `numeral-declension-compound-numbers` | B2.5 | Decline cardinals from 5 to 100 and compound cardinals (`:3145-3149`); the five lessons are for these alone — collective and fractional numerals, if the pack admits them (D4), get a lesson beyond the five | R (statistics in an article) | 5 |
| 60 | `word-formation-person-suffixes` | B2.5 | Form and understand names of people by what they do (`:3356-3357`) | — | 3 |
| 61 | `word-formation-abstract-nouns` | B2.5 | Form activity nouns with a suffix and with a zero suffix, and abstract nouns (`:3359-3364`) | R (scientific article `:2681`) | 3 |
| 62 | `word-formation-place-object-names` | B2.5 | Form and understand names of places by what happens there (`:3366-3367`) | — | 2 |
| 63 | `word-formation-adjective-adverbs` | B2.5 | Form and **decline** possessive adjectives — at least three lessons of their own: formation, singular, plural; decline compound adjectives; recycle adjectives from nouns and adverbs from adjectives (`:3121-3129`, `:3369-3373`) | R | 7 |
| 64 | `advanced-conjunctions-i` | B2.6 | Join clauses as equals with the full conjunction set | — | 2 |
| 65 | `advanced-conjunctions-ii` | B2.6 | Build every subordinate clause type the Standard lists, with `котрий`, `що` and `доки` (`:3422-3445`) | W (report or essay with reasoning `:2647-2649`) | 4 |
| 66 | `checkpoint-morphology` | B2.6 | Self-check: verbs, numerals, word formation, conjunctions | R, W | 2 |
| 67 | `synonymy-types-and-rows` | B2.6 | Tell synonyms apart by meaning and colour (`:3461`) | — | 3 |
| 68 | `synonymy-in-registers` | B2.6 | Choose the synonym the register asks for | W | 3 |
| 69 | `synonymy-practice-precision` | B2.6 | Say exactly what you mean: paraphrase, specify, explain in other words (`:2749-2751`) | S | 2 |
| 70 | `proverbs-work-wisdom-character` | B2.6 | Understand and use well-known proverbs about work, wisdom and character | Li, R | 3 |
| 71 | `proverbs-nature-time-caution` | B2.6 | Understand and use well-known proverbs about nature, time and caution; weather, seasons and climate (`:3041`) | R | 3 |
| 72 | `set-expressions-combined` | B2.6 | Use fixed expressions where they fit (`:2752-2753`) | S | 3 |
| 73 | `checkpoint-lexicology-i` | B2.6 | Self-check: the right word for the register | R, W | 2 |
| 74 | `idioms-somatic` | B2.7 | Understand and use idioms built on parts of the body; feelings: anger, worry, fear, comfort (`:2847-2848`, `:2868`) | Li, S | 3 |
| 75 | `idioms-animals` | B2.7 | Understand and use idioms built on animals; domestic and wild animals (`:3043`) | R | 3 |
| 76 | `idioms-nature` | B2.7 | Understand and use idioms built on nature; natural features, ecology and protection of the environment (`:3044-3045`) | R (article on ecology), S | 3 |
| 77 | `neologisms-borrowings` | B2.7 | Understand how the vocabulary renews itself, in texts about technology and the media (D4) | R | 3 |
| 78 | `checkpoint-lexicology-ii` | B2.7 | Self-check: idioms understood and used where they fit | R, Li | 2 |
| 79 | `professional-email-basics` | B2.7 | Write a working e-mail: request, thanks, explanation; working hours, leave, pay and the social package (`:2983-2986`) | W (`:2653-2654`), R | 3 |
| 80 | `professional-email-advanced` | B2.7 | Handle hard cases in writing: complaint, claim, refusal; career and professional growth, the labour market, unemployment (`:2881`, `:2987-2989`) | W | 3 |
| 81 | `professional-reports` | B2.7 | Write a report and a programme; business negotiations and contracts (`:2680`, `:2990-2992`) | W, S (negotiation) | 4 |
| 82 | `academic-writing` | B2.7 | Write a report to a plan and summarise sources; fields of knowledge, degrees, academic posts, the educational process, reforms (`:2969-2978`) | W (`:2647-2651`), Li (lecture `:2466`) | 4 |
| 83 | `text-analysis` | B2.7 | Find the theme, the purpose, the author's position and the conclusions of a text (`:2569-2573`) | R (skim a long text `:2576-2577`) | 3 |
| 84 | `news-analysis` | B2.7 | Follow the press, radio, television, the internet and social networks; discuss the news and responses to it (`:3052-3056`, `:2532`) | Li (news of up to 700 words), S | 4 |
| 85 | `presentation-skills` | B2.8 | Speak before an audience; address a speaker and appeal to a speaker's words (`:2729-2730`, `:2863-2866`) | S, Li (long presentation `:2511`) | 4 |
| 86 | `discussion-debate` | B2.8 | Take part in a formal and an informal discussion: react to arguments, state for and against; contested questions, conflicts between generations (`:2758-2760`, `:2949`, `:2887`) | S (12–15 turns `:2779-2780`), Li (round table `:2531`) | 4 |
| 87 | `checkpoint-communication` | B2.8 | Self-check: a letter, a talk and a discussion | W, S | 2 |
| 88 | `tekhnolohii-ta-shi` | B2.8 | Talk about the development of science and technology, discoveries, inventions that changed the world (`:3047-3050`) | R, W (essay with reasoning `:2668-2669`) | 4 |
| 89 | `nauka-i-doslidzhennia` | B2.8 | Talk about research; give definitions in a professional field (`:2840-2841`); prepare and run a simple survey (`:2754-2757`) | S (survey `:2783`), W | 4 |
| 90 | `mystetstvo-i-literatura` | B2.8 | Talk about museums, galleries, theatre, the philharmonic, festivals; retell a plot and say what you think of it (`:2908-2915`, `:2726`) | W (overview of a film or play `:2670-2671`), Li (film `:2472-2473`) | 4 |
| 91 | `modern-diaspora` | B2.8 | Talk about nationality, country and languages, the history of a family and its origin, contacts between people (`:2878`, `:2886`, `:2888-2889`) | R (memoir `:2606`), W (private letter describing events and impressions `:2652`) | 4 |
| 92 | `religion-in-ukraine` | B2.8 | Talk about religious holidays, customs and traditions (`:3059`, `:3064`) | R, Li | 3 |
| 93 | `b2-final-exam` | B2.8 | Take a practice exam in the four skills at the Standard's B2 sizes: listening of up to 700 words, writing of 150–200 words, a dialogue of 12–15 turns, a talk before an audience | all | 3 |

**Sizing (operator, 2026-09-21): nothing is forced.** The lesson counts above are estimates for
orientation only and total 298. A module gets the lessons its content needs — not compressed to hit
a number, not stretched to fill one. The module plan decides the count; the plan review checks both
directions, cramming and dragging. Places where this arc expects the plan review to look hard: 14–16, which carry the school-grammar
frame, and 47–51, whose case meanings are almost all B1's (D2) — both could drag, as could 57, where only uses are new; 63 was raised from five lessons to seven after the r1 review found
it crammed, and possessive adjectives may not shrink to a mention there; 59, 33 and 35 are the next
candidates for cramming.

## 6. Coverage against the Standard's catalogues

**Themes (19, `:2874-3064`):** Людина 12, 80, 86, 91 (D5) · Дім, помешкання 4 · Щоденне життя,
побут 8 · Культурне дозвілля та відпочинок 17, 90 · Спорт 17 · Подорожі 35 (D5) · Суспільні
відносини 44, 45, 86, 41, 84 (D6) · Економіка 46 · Здоров'я й особиста гігієна 13 · Освіта 82, 89 ·
Робота 79, 80, 81, 37 · Купівля 28 · Харчування 24 · Послуги 28 · Місця 35 · Природне середовище
71, 75, 76 (D5) · Наука і техніка 88, 89, 77 · Медіа й соціальні мережі 84, 41, 77 · Традиції,
звичаї, свята 39, 92.

**Speech intentions new at B2 (`:2810-2872`, compared item by item with B1 `:1777-1851`):**
definitions in a professional field → 89 · anger and indignation; worry, fear and anxiety → 74 ·
publicly addressing a speaker; appealing to a speaker's words → 85, 30 · threats → 55, 28 · comforting
→ 74 · forgiving and refusing to forgive → 36 · arguing → 86, 65 · stressing the importance of an
event or problem → 26, 27. The intentions B2 shares with B1 are exercised at the B2 sizes in the
theme modules.

**Skills:** each text type of `:2495-2533`, `:2581-2607`, `:2666-2681` and `:2765-2783` has an owner
in the Skills duty column; the practice exam at 93 checks the Standard's B2 sizes. One text type has
no natural owner and is left to the plan review of 33: графіті (`:2679`).

## 7. Immersion band mapping (plan schema §4)

One band for the whole level: every position 1–93 maps to `b2+`, 100 % Ukrainian
(`IMMERSION_POLICIES["default"]`). Nothing is re-tuned (R-30). A module split or merged later stays
in the same band.

## 8. Open questions for the operator

Each has the driver's proposal; the arc is written to the proposals.

1. **Three themes without a module of their own (D5).** Proposal: keep the 93 positions and own
   Людина, Подорожі and Природне середовище as duties of the positions named in §6. Alternative:
   add up to three theme modules, which shifts every later position.
2. **Noun types new at B2 have no slug (D3).** Proposal: they become the main new content of 47,
   48 and 49, with abbreviations in 37. The B2 case catalogue adds almost no meaning to B1's (D2),
   so these positions have the room, and without the noun types they would drag. Alternative: one
   new module for the noun types before 47, and fewer lessons in 47–49.
3. **The pluperfect (56).** The Standard lists it at no level, ULP never teaches it and no school
   textbook in the corpus has it. Proposal: keep the slug as a two-lesson recognition module.
   Alternative: drop it from B2 and leave it to C1.
4. **Possessive adjectives are owned by 63** and get at least three lessons of their own there,
   instead of a new position. Proposal: yes. The reviewer agreed and asked for the larger estimate.
5. **Collective and fractional numerals (59)** are taught only if the evidence pack shows from the
   corpus that a B2 reader meets them often. Proposal: yes.

## 9. Follow-ups outside this document

- The arc generator needs a `b2` mode exactly as it needs `a2` and `b1` modes (#8424): main table
  only.
- Mapping-file corrections for B2 belong to #8404.
- With this arc the four arcs R-09 asks for are written; seminars follow later (R-29).
