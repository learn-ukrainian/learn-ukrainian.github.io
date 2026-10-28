# A1-v1 language pass, manifest modules 15 through 28

Refs #8893. Source snapshot: `dbd43f98c0a2a429b84a165a9a970fc32e794fd9`.

This is one bounded Method step 2 slice. It checks 288 items: every fill-in and quiz item in every inline/root and workbook section of manifest modules 15 through 28. The workbook sections were inspected; they contain zero fill-in or quiz items in this batch. There are 214 checked-clean items and 74 confirmed defects, all repaired: 73 ambiguities and one wrong-key context. Every original key, learning target and activity type is retained.

The order comes from `levels.a1-v1.modules` in `curriculum/l2-uk-en/curriculum.yaml`, continuing the arc order used by the modules 1 through 14 report. It includes the complete Actions and Time and Nature arcs and the first Places module. No authorized usage ranking was supplied.

| Position | Module | Items checked | Clean | Defects fixed |
| --- | --- | ---: | ---: | ---: |
| 15 | `what-i-like` | 22 | 22 | 0 |
| 16 | `verbs-group-one` | 24 | 24 | 0 |
| 17 | `verbs-group-two` | 24 | 24 | 0 |
| 18 | `i-want-i-can` | 29 | 23 | 6 |
| 19 | `questions` | 22 | 15 | 7 |
| 20 | `my-morning` | 27 | 18 | 9 |
| 21 | `checkpoint-actions` | 24 | 17 | 7 |
| 22 | `what-time` | 22 | 16 | 6 |
| 23 | `days-and-months` | 13 | 12 | 1 |
| 24 | `weather` | 10 | 5 | 5 |
| 25 | `my-day` | 18 | 5 | 13 |
| 26 | `free-time` | 10 | 2 | 8 |
| 27 | `checkpoint-time-nature` | 13 | 4 | 9 |
| 28 | `euphony` | 30 | 27 | 3 |

## What was checked

Item indices and anonymous workbook activity indices are zero-based, as in the preceding report. Every verdict considers the activity title, instruction, stem, key and all displayed alternatives. A feedback explanation is not a hidden restriction on an otherwise open question. C means checked-clean in that stated task, not a certification of every claim in its module.

The structural scanner ran before and after repair and checked 55/55 activity files with zero findings. It added no flagged items from other activity types. As in the preceding batch, this scanner is structural; this slice does not claim to implement the full semantic/VESUM deterministic rules listed in issue Method step 1.

Not checked: other activity types without a structural flag; module prose, plans, vocabulary, resources and audio; the other 41 modules in this slice; broader historical source/page drift; the deployed site or teacher usage. Together with the preceding batch, the manifest language pass has covered modules 1 through 28; modules 29 through 55 remain, apart from the previously checked single finale item. #8893 remains open with the CTO curriculum coordinator. No deployment or publication is part of this slice.

## Sources evidence and its limits

The Sources MCP supplied the evidence on 2026-10-28. VESUM verifies forms and grammatical analyses, ULIF supplies stress readings, and `check_text` screens for diagnostics. None of these tools decides answer ambiguity by itself. The per-item verdicts are linguistic inferences from the stated task and these results. Usage-dependent judgments also cite the U locators below.

Each module batch sends distinct Ukrainian tokens from instructions and every item field, including every option, to `verify_words`, lowercased with acute accents removed. `verify_stresses` receives the original polysyllabic tokens. `check_text` receives full item text with item ids and acute accents removed, using vesum and ua_gec checks. Titles are additionally included in the post-repair screens. K checks all reconstructed fill-in completions, including suffix completions. POSTFIX checks replacement-context forms and capitalized proper names, plus stresses, and screens the first 150 final rows. POSTSCREEN2 screens the remaining 138 final rows. U50 rechecks replacement contexts in lowercase.

Case-sensitive screen misses are not lexical errors. Proper names were rechecked with capitalization. Isolated endings, stem fragments, deliberately malformed options, the quoted letter п and explanation metalanguage чанк are distinguished from target vocabulary. Unmarked stress heteronyms and pending stress readings of fragments or unmarked words are not stress defects. No repair adds or changes an acute accent. The full -ся forms in my-morning remain clean because the activity title explicitly requests -ся, even though K and U16 verify some contracted alternatives as Ukrainian.

SUM-20 ingestion misses U05/U06 support no negative finding. VTS is the modern semantic fallback. No failed query or generic UA-GEC suspicion is counted as a defect. The original давайте contrast remains clean under the explicit normative-form instruction and both Antonenko surfaces U30/U31. Ordinary euphony patterns are evaluated with the official rules; their stated exceptions are not ignored.

The companion [machine-readable Sources evidence](language-pass-modules-15-28-evidence.jsonl) follows the preceding batch format. M/K/POSTFIX records contain arguments, analyses, stress row identifiers and diagnostic results. Their reply digests cover the normalized retained result objects, and their receipt digest covers the retained call records. Usage records preserve query arguments, full-reply digests, source locators and compact paraphrased source summaries. They do not reproduce full dictionary articles.

### Module batch locators

| Locator | Section | VESUM found/queried | Stress rows | Text items | Receipt SHA-256 |
| --- | --- | ---: | ---: | ---: | --- |
| M15 | what-i-like, all choice sections | 38/38 | 34 | 22 | `f8b6aa510f8a5e1d660bda785f469481d20bd560cc5a1373689420c12c5cc2bb` |
| M16 | verbs-group-one, all choice sections | 58/64 | 49 | 24 | `475b77457dbc2da04cf94a5513cb56c7955e124f42a41bf206c974d68f5f530c` |
| M17 | verbs-group-two, all choice sections | 51/60 | 41 | 24 | `75a5b77d1030d677be550cf6864530cdca41d718e69810a946836d9623d1ef5a` |
| M18 | i-want-i-can, all choice sections | 51/57 | 54 | 29 | `2f2dea74124af357e26d80a6ff3dfcd897c6e9f8325042c61e19a4a2d253b2a3` |
| M19 | questions, all choice sections | 39/39 | 31 | 22 | `963b37844c2c7e3c6c09afc12b5d65a9d90f2da5759a44db4d7b7cd87d29d72e` |
| M20 | my-morning, all choice sections | 63/68 | 52 | 27 | `5c9b0f34dc34911410ba5761b7278c1f267e938cab281cef6efe0c11cb8990f4` |
| M21 | checkpoint-actions, all choice sections | 82/85 | 79 | 24 | `a658b24b1f51a68ef8a73b7758d7f6c30635b0cda2140014c87f774e88761f42` |
| M22 | what-time, all choice sections | 65/65 | 62 | 22 | `59676ec1d4beb60b7317a70d79012dce2c850e23fee408ad34eeb57c6d039ec6` |
| M23 | days-and-months, all choice sections | 42/42 | 35 | 13 | `b78d3b59afb69386b9a26089b45102a25d75f5d4fde24c4e7e12f49490ba599f` |
| M24 | weather, all choice sections | 58/58 | 52 | 10 | `5006f59c9874abd672bb05c9acd2115a3c4e139de35dc106ccca4aab40d81759` |
| M25 | my-day, all choice sections | 134/138 | 118 | 18 | `e7279415f20401539d9156ff3c7cba62977c7d30bcefe6b0871a6b8c0f7285bb` |
| M26 | free-time, all choice sections | 91/91 | 78 | 10 | `9f84caa35f443fa1a0e28541ec2af385e9c9823e31855b9e7f35f043170df7d4` |
| M27 | checkpoint-time-nature, all choice sections | 105/107 | 90 | 13 | `e201fb150d4ca6bd5ffe172c2fc8702f489d30a65cc73978fc610484ff24c9e0` |
| M28 | euphony, all choice sections | 45/58 | 40 | 30 | `3a99de06cdcd0208ec96ebf4440582e8e508e43f5b81858a0a817a7b7a6b3d0d` |

### Usage and orthography locators

- U01: Official Pravopys 2019 §23, pp.25-28: у between consonants and before specified clusters; в after a vowel before most consonants. Initial В before a consonant is explicitly permitted. Literary variation is distinguished from the neutral euphony patterns.
- U02: Official Pravopys 2019 §24, pp.28-29: і between consonants, at a pause or beginning, before й/є/ї/ю/я, and after й/я/ю/є/ї; й normally after other vowel letters. This specifically supports Я і Максим. Literary variation does not erase the task asking for the smoother neutral pattern.
- U03: Official Pravopys 2019 §25, pp.29-31: z variants depend on the neighboring sounds; із and зі are interchangeable before some clusters. The text explicitly gives зі школи and зі/зо мною.
- U04: No result. Short query tokens were dropped. This miss supports no verdict.
- U05: Official offline SUM-20 ingestion miss for приймати. No validity conclusion follows.
- U06: Official offline SUM-20 ingestion miss for проснутися. No validity conclusion follows.
- U07: VTS приймати, sense 6: performing a hygienic or therapeutic procedure and swallowing medicine are recognized uses. This contradicts treating every приймаю alternative as non-Ukrainian.
- U08: VTS проснутися redirects to просипатися I. U21 verifies that waking-up sense directly.
- U09: The combined structured Antonenko query returned no result; no verdict rests on this miss.
- U10: Antonenko full-book chunks p165 and p091 discuss приймати/сприймати and participation. They do not prohibit the shower or medicine senses. U07 is the modern semantic evidence.
- U11: VTS потім includes temporal succession and later occurrence. It can follow the preceding morning action.
- U12: VTS нарешті denotes an eventual or final occurrence. A routine without a specified endpoint does not require it over потім.
- U13: VTS хотіти recognizes desire and intention with an infinitive.
- U14: VTS могти recognizes ability and possibility, including an omitted infinitive.
- U15: VTS мусити recognizes obligation or necessity; its dialectal ability sense is labelled separately and is not the neutral A1 target.
- U16: GRAC supplies two concordances of вмиваюсь, independently attesting the contracted reflexive form. The original activity title nevertheless explicitly requests -ся.
- U17: GRAC supplies a modern concordance of двічі у тиждень for twice-weekly rehearsals. Another returned line has у тижні and is not evidence for the exact requested form.
- U18: VTS дощити recognizes impersonal дощить as falling rain. Its colloquial label does not exclude it from a general A1 weather description.
- U19: VTS покушати lookup missed. This miss is not a defect finding; the original distractor stays unchanged.
- U20: VTS просинатися redirects to просипатися I.
- U21: VTS просипатися I explicitly lists perfective проснутися and defines waking from sleep. This is the relevant sense, distinct from the second homonym.
- U22: VTS іти includes going and uses in appeals or invitations. The finite plural invitation can compete with ходімо in an unrestricted invitation task.
- U23: VTS де recognizes a question about location. It competes with хто or чому in stems that leave the question focus open.
- U24: VTS коли recognizes a question about time. It competes with what or how in otherwise open questions.
- U25: VTS хто recognizes a question identifying a person. A cue can specify that focus rather than place or object.
- U26: VTS як recognizes questions about manner, quality or state. It is a defensible alternative to коли before ти працюєш.
- U27: GRAC attests both брала душ and бере душ in Ukrainian passages. This supports the retained shower phrase, not an exclusive ban on приймати.
- U28: GRAC attests приймати душ in two passages; U07 independently supports the hygienic-procedure sense.
- U29: GRAC returns one relevant weekend-time example with на вихідні and two irrelevant adjective occurrences about starting positions. Only the weekend example is used.
- U30: Antonenko structured entry Наказовий спосіб favors Ukrainian first-person-plural imperatives in invitations.
- U31: Antonenko full-book p067 explicitly favors ходімо over давайте підемо in a direct invitation. Both Antonenko surfaces support keeping that original contrast checked-clean.
- U32: The first broad conjugation search returns historical discussion and review questions. It is not sufficient for the particular endings; U46 supplies the directly relevant rule.
- U33: VTS спочатку denotes an initial occurrence or doing something again from its beginning.
- U34: VTS після denotes succession, also with genitive objects including meals. Після цього and потім can describe the same temporal transition.
- U35: The exact weekend-question GRAC query returned no match. This absence proves no invalidity; U29 supplies the positive, narrower usage evidence.
- U36: VTS вранці means in the morning. An unspecified coffee, work or waking-up activity does not entail that period.
- U37: VTS ввечері means in the evening. An unspecified film or meal does not uniquely supply that period.
- U38: VTS вдень means during daytime. A nine-to-five range needs AM/PM or 24-hour context to rule out a night shift.
- U39: VTS холодно describes low temperature or a feeling of cold. A season or sunshine alone does not entail or exclude it.
- U40: VTS тепло distinguishes the predicative warm-weather reading from noun heat. Its use does not follow from a season alone.
- U41: VTS сонячний includes weather with sunlight. Summer alone does not exclude other offered weather descriptions.
- U42: VTS рідко is an adverb of low frequency. Limited free time favors it but does not uniquely fix a frequency without further context.
- U43: VTS часто denotes frequent occurrence. Liking a sport does not logically preclude rarely playing it.
- U44: VTS ніколи distinguishes never from stressed ні́коли, lack of time. The frequency target is never; no missing time cue can select it from a bare Sunday-work statement.
- U45: VTS що, interrogative sense 2, explicitly permits a reason question equivalent to чому. The reason item therefore replaces Що rather than pretending the why gloss excludes it.
- U46: Strokal 2021 p200, uni-ukrmova-orthography-strokal-2021_s0367, explicitly enumerates first- and second-conjugation present endings. The VESUM forms then identify the particular paradigm/person.
- U47: GRAC returns an intelligible Ukrainian literary concordance of із школи. A second mixed-language line is not used. Together with §25 this confirms the competing z-variant reading.
- U48: VTS пити includes swallowing pills or powders with water, supporting the retained medicine phrase.
- U49: VTS грати supplies the distinction between на plus a musical instrument and у plus a game. Euphonic у/в variants do not create a different sport meaning.
- U51: GRAC attests ідемо в кіно in two joint-going contexts. This corroborates the finite first-person-plural form; it does not alone prescribe invitation morphology.
- U52: GRAC directly attests the exact phrase робиш на вихідні inside a reported personal question, confirming the competing weekend-question reading.
- U53: The search returned historical grammar material and is not used to establish modern imperative usage.
- U54: The scoped modern morphology search is retained as supplementary grammar evidence; its applicability is determined from the returned passages, not the search keywords.
- U55: GRAC supplies joint-going contexts for ідемо разом. Corpus occurrence alone is not a prescriptive grammar rule.
- U50: Lowercased recheck of all replacement-context tokens. Proper names are separately verified with capitalization in POSTFIX; п is a quoted letter and чанк is explanation metalanguage, neither a target form.

## Per-item verdicts

C means checked-clean in the original task. D means a confirmed second defensible answer or wrong-key context, repaired here. Every row cites its module batch. K supplies complete-word morphology for ending blanks; usage locators supply the semantic or orthographic distinction. No answer key was changed.

### 15. what-i-like

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | Я люблю ___. | читати | C | M15; U13/U14/U15. The action/thing meaning or explicit negative task selects читати; other options fail the requested infinitive, agreement or negative construction. |
| `act-1/1` | inline | Я люблю ___. | гуляти | C | M15; U13/U14/U15. The action/thing meaning or explicit negative task selects гуляти; other options fail the requested infinitive, agreement or negative construction. |
| `act-1/2` | inline | Я люблю ___. | готувати | C | M15; U13/U14/U15. The action/thing meaning or explicit negative task selects готувати; other options fail the requested infinitive, agreement or negative construction. |
| `act-1/3` | inline | Я люблю ___ музику. | слухати | C | M15; U13/U14/U15. The action/thing meaning or explicit negative task selects слухати; other options fail the requested infinitive, agreement or negative construction. |
| `act-1/4` | inline | Я люблю ___ фільм. | дивитися | C | M15; U13/U14/U15. The action/thing meaning or explicit negative task selects дивитися; other options fail the requested infinitive, agreement or negative construction. |
| `act-1/5` | inline | Я люблю ___. | грати | C | M15; U13/U14/U15. The action/thing meaning or explicit negative task selects грати; other options fail the requested infinitive, agreement or negative construction. |
| `act-1/6` | inline | Я люблю ___. | малювати | C | M15; U13/U14/U15. The action/thing meaning or explicit negative task selects малювати; other options fail the requested infinitive, agreement or negative construction. |
| `act-1/7` | inline | Я люблю ___. | співати | C | M15; U13/U14/U15. The action/thing meaning or explicit negative task selects співати; other options fail the requested infinitive, agreement or negative construction. |
| `act-2/0` | inline | I like to read. | Я люблю читати. | C | M15; U13/U14/U15. The action/thing meaning or explicit negative task selects Я люблю читати.; other options fail the requested infinitive, agreement or negative construction. |
| `act-2/1` | inline | I like music. | Мені подобається музика. | C | M15; U13/U14/U15. The action/thing meaning or explicit negative task selects Мені подобається музика.; other options fail the requested infinitive, agreement or negative construction. |
| `act-2/2` | inline | I like to cook. | Я люблю готувати. | C | M15; U13/U14/U15. The action/thing meaning or explicit negative task selects Я люблю готувати.; other options fail the requested infinitive, agreement or negative construction. |
| `act-2/3` | inline | I like this book. | Мені подобається ця книга. | C | M15; U13/U14/U15. The action/thing meaning or explicit negative task selects Мені подобається ця книга.; other options fail the requested infinitive, agreement or negative construction. |
| `act-2/4` | inline | I like to watch a film. | Я люблю дивитися фільм. | C | M15; U13/U14/U15. The action/thing meaning or explicit negative task selects Я люблю дивитися фільм.; other options fail the requested infinitive, agreement or negative construction. |
| `act-2/5` | inline | I like this film. | Мені подобається цей фільм. | C | M15; U13/U14/U15. The action/thing meaning or explicit negative task selects Мені подобається цей фільм.; other options fail the requested infinitive, agreement or negative construction. |
| `act-2/6` | inline | I like to play. | Я люблю грати. | C | M15; U13/U14/U15. The action/thing meaning or explicit negative task selects Я люблю грати.; other options fail the requested infinitive, agreement or negative construction. |
| `act-2/7` | inline | I like Kyiv. | Мені подобається Київ. | C | M15; U13/U14/U15. The action/thing meaning or explicit negative task selects Мені подобається Київ.; other options fail the requested infinitive, agreement or negative construction. |
| `act-4/0` | inline | Я ___ люблю готувати. | не | C | M15; U13/U14/U15. The action/thing meaning or explicit negative task selects не; other options fail the requested infinitive, agreement or negative construction. |
| `act-4/1` | inline | Мені ___ подобається цей фільм. | не | C | M15; U13/U14/U15. The action/thing meaning or explicit negative task selects не; other options fail the requested infinitive, agreement or negative construction. |
| `act-4/2` | inline | Ти ___ любиш читати? | не | C | M15; U13/U14/U15. The action/thing meaning or explicit negative task selects не; other options fail the requested infinitive, agreement or negative construction. |
| `act-4/3` | inline | Мені ___ подобається ця книга. | не | C | M15; U13/U14/U15. The action/thing meaning or explicit negative task selects не; other options fail the requested infinitive, agreement or negative construction. |
| `act-4/4` | inline | Я ___ люблю дивитися фільм. | не | C | M15; U13/U14/U15. The action/thing meaning or explicit negative task selects не; other options fail the requested infinitive, agreement or negative construction. |
| `act-4/5` | inline | Тобі ___ подобається музика? | не | C | M15; U13/U14/U15. The action/thing meaning or explicit negative task selects не; other options fail the requested infinitive, agreement or negative construction. |

### 16. verbs-group-one

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | Я чита__ текст. | ю | C | M16; K/U46. The subject fixes the person/number of ю; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/1` | inline | Ти чита__ книгу? | єш | C | M16; K/U46. The subject fixes the person/number of єш; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/2` | inline | Він чита__ текст. | є | C | M16; K/U46. The subject fixes the person/number of є; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/3` | inline | Вона слуха__ музику. | є | C | M16; K/U46. The subject fixes the person/number of є; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/4` | inline | Ми чита__ текст. | ємо | C | M16; K/U46. The subject fixes the person/number of ємо; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/5` | inline | Ви чита__? | єте | C | M16; K/U46. The subject fixes the person/number of єте; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/6` | inline | Вони чита__. | ють | C | M16; K/U46. The subject fixes the person/number of ють; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/7` | inline | Я зна__ це слово. | ю | C | M16; K/U46. The subject fixes the person/number of ю; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/8` | inline | Ти зна__ це слово? | єш | C | M16; K/U46. The subject fixes the person/number of єш; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/9` | inline | Ми зна__ текст. | ємо | C | M16; K/U46. The subject fixes the person/number of ємо; the competing forms do not agree. K verifies complete ending constructions. |
| `act-2/0` | inline | Вона ___ книгу. | читає | C | M16; K/U46. The subject fixes the person/number of читає; the competing forms do not agree. K verifies complete ending constructions. |
| `act-2/1` | inline | Я ___ музику. | слухаю | C | M16; K/U46. The subject fixes the person/number of слухаю; the competing forms do not agree. K verifies complete ending constructions. |
| `act-2/2` | inline | Ти ___ вечерю? | готуєш | C | M16; K/U46. The subject fixes the person/number of готуєш; the competing forms do not agree. K verifies complete ending constructions. |
| `act-2/3` | inline | Ми ___ в офісі. | працюємо | C | M16; K/U46. The subject fixes the person/number of працюємо; the competing forms do not agree. K verifies complete ending constructions. |
| `act-2/4` | inline | Ви ___ українську? | вивчаєте | C | M16; K/U46. The subject fixes the person/number of вивчаєте; the competing forms do not agree. K verifies complete ending constructions. |
| `act-2/5` | inline | Вони ___ в парку. | гуляють | C | M16; K/U46. The subject fixes the person/number of гуляють; the competing forms do not agree. K verifies complete ending constructions. |
| `act-2/6` | inline | Сашко ___ українську. | знає | C | M16; K/U46. The subject fixes the person/number of знає; the competing forms do not agree. K verifies complete ending constructions. |
| `act-2/7` | inline | Я ___ вдома. | працюю | C | M16; K/U46. The subject fixes the person/number of працюю; the competing forms do not agree. K verifies complete ending constructions. |
| `act-4/0` | inline | Що ти ___? | робиш | C | M16; K/U46. The subject fixes the person/number of робиш; the competing forms do not agree. K verifies complete ending constructions. |
| `act-4/1` | inline | Я ___ музику. | слухаю | C | M16; K/U46. The subject fixes the person/number of слухаю; the competing forms do not agree. K verifies complete ending constructions. |
| `act-4/2` | inline | Вона ___ вечерю. | готує | C | M16; K/U46. The subject fixes the person/number of готує; the competing forms do not agree. K verifies complete ending constructions. |
| `act-4/3` | inline | Де ти ___? | працюєш | C | M16; K/U46. The subject fixes the person/number of працюєш; the competing forms do not agree. K verifies complete ending constructions. |
| `act-4/4` | inline | Я ___ в офісі. | працюю | C | M16; K/U46. The subject fixes the person/number of працюю; the competing forms do not agree. K verifies complete ending constructions. |
| `act-4/5` | inline | Ти ___ українську? | вивчаєш | C | M16; K/U46. The subject fixes the person/number of вивчаєш; the competing forms do not agree. K verifies complete ending constructions. |

### 17. verbs-group-two

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | Я говор__ українською. | ю | C | M17; K/U46. The subject fixes the person/number of ю; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/1` | inline | Ти говор__ українською? | иш | C | M17; K/U46. The subject fixes the person/number of иш; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/2` | inline | Він говор__ добре. | ить | C | M17; K/U46. The subject fixes the person/number of ить; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/3` | inline | Вона говор__ повільно. | ить | C | M17; K/U46. The subject fixes the person/number of ить; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/4` | inline | Ми говор__ українською. | имо | C | M17; K/U46. The subject fixes the person/number of имо; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/5` | inline | Ви говор__ українською? | ите | C | M17; K/U46. The subject fixes the person/number of ите; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/6` | inline | Вони говор__ українською. | ять | C | M17; K/U46. The subject fixes the person/number of ять; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/7` | inline | Я робл__ вправу. | ю | C | M17; K/U46. The subject fixes the person/number of ю; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/8` | inline | Ти бач__ слово? | иш | C | M17; K/U46. The subject fixes the person/number of иш; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/9` | inline | Вони бач__ слово. | ать | C | M17; K/U46. The subject fixes the person/number of ать; the competing forms do not agree. K verifies complete ending constructions. |
| `act-3/0` | inline | Ти ___ українською? | говориш | C | M17; K/U46. The subject fixes the person/number of говориш; the competing forms do not agree. K verifies complete ending constructions. |
| `act-3/1` | inline | Вона ___ добре. | говорить | C | M17; K/U46. The subject fixes the person/number of говорить; the competing forms do not agree. K verifies complete ending constructions. |
| `act-3/2` | inline | Ми ___ українську. | вчимо | C | M17; K/U46. The subject fixes the person/number of вчимо; the competing forms do not agree. K verifies complete ending constructions. |
| `act-3/3` | inline | Я ___ це слово. | бачу | C | M17; K/U46. The subject fixes the person/number of бачу; the competing forms do not agree. K verifies complete ending constructions. |
| `act-3/4` | inline | Ти ___ це слово? | бачиш | C | M17; K/U46. The subject fixes the person/number of бачиш; the competing forms do not agree. K verifies complete ending constructions. |
| `act-3/5` | inline | Вони ___ до школи. | ходять | C | M17; K/U46. The subject fixes the person/number of ходять; the competing forms do not agree. K verifies complete ending constructions. |
| `act-3/6` | inline | Я ___ каву. | прошу | C | M17; K/U46. The subject fixes the person/number of прошу; the competing forms do not agree. K verifies complete ending constructions. |
| `act-3/7` | inline | Вони ___ слово. | бачать | C | M17; K/U46. The subject fixes the person/number of бачать; the competing forms do not agree. K verifies complete ending constructions. |
| `act-4/0` | inline | Вона ___ українською. (говорити) | говорить | C | M17; K/U46. The subject fixes the person/number of говорить; the competing forms do not agree. K verifies complete ending constructions. |
| `act-4/1` | inline | Я ___ вправу. (робити) | роблю | C | M17; K/U46. The subject fixes the person/number of роблю; the competing forms do not agree. K verifies complete ending constructions. |
| `act-4/2` | inline | Ти ___ слово? (бачити) | бачиш | C | M17; K/U46. The subject fixes the person/number of бачиш; the competing forms do not agree. K verifies complete ending constructions. |
| `act-4/3` | inline | Ми ___ нові слова. (вчити) | вчимо | C | M17; K/U46. The subject fixes the person/number of вчимо; the competing forms do not agree. K verifies complete ending constructions. |
| `act-4/4` | inline | Я ___ каву. (просити) | прошу | C | M17; K/U46. The subject fixes the person/number of прошу; the competing forms do not agree. K verifies complete ending constructions. |
| `act-4/5` | inline | Вони ___ до школи. (ходити) | ходять | C | M17; K/U46. The subject fixes the person/number of ходять; the competing forms do not agree. K verifies complete ending constructions. |

### 18. i-want-i-can

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | Я ___ читати. | хочу | C | M18; U13/U14/U15/U46. The instruction explicitly requests хотіти; the subject selects хочу over the other offered persons. |
| `act-1/1` | inline | Ти ___ гуляти? | хочеш | C | M18; U13/U14/U15/U46. The instruction explicitly requests хотіти; the subject selects хочеш over the other offered persons. |
| `act-1/2` | inline | Вона ___ каву. | хоче | C | M18; U13/U14/U15/U46. The instruction explicitly requests хотіти; the subject selects хоче over the other offered persons. |
| `act-1/3` | inline | Ми ___ піти. | хочемо | C | M18; U13/U14/U15/U46. The instruction explicitly requests хотіти; the subject selects хочемо over the other offered persons. |
| `act-1/4` | inline | Ви ___ каву? | хочете | C | M18; U13/U14/U15/U46. The instruction explicitly requests хотіти; the subject selects хочете over the other offered persons. |
| `act-1/5` | inline | Вони ___ працювати. | хочуть | C | M18; U13/U14/U15/U46. The instruction explicitly requests хотіти; the subject selects хочуть over the other offered persons. |
| `act-1/6` | inline | Оля і Денис ___ піти в кіно. | хочуть | C | M18; U13/U14/U15/U46. The instruction explicitly requests хотіти; the subject selects хочуть over the other offered persons. |
| `act-1/7` | inline | Я не ___ їсти. | хочу | C | M18; U13/U14/U15/U46. The instruction explicitly requests хотіти; the subject selects хочу over the other offered persons. |
| `act-1/8` | inline | Денисе, ти ___ каву? | хочеш | C | M18; U13/U14/U15/U46. The instruction explicitly requests хотіти; the subject selects хочеш over the other offered persons. |
| `act-2/0` | inline | You want to read. | Я хочу читати. | C | M18; U13/U14/U15/U46. The English situation specifies the modal meaning expressed by Я хочу читати.; other options express a different modality. |
| `act-2/1` | inline | You are able to help. | Я можу допомогти. | C | M18; U13/U14/U15/U46. The English situation specifies the modal meaning expressed by Я можу допомогти.; other options express a different modality. |
| `act-2/2` | inline | You have to work. | Я мушу працювати. | C | M18; U13/U14/U15/U46. The English situation specifies the modal meaning expressed by Я мушу працювати.; other options express a different modality. |
| `act-2/3` | inline | You cannot go today. | Сьогодні я не можу піти. | C | M18; U13/U14/U15/U46. The English situation specifies the modal meaning expressed by Сьогодні я не можу піти.; other options express a different modality. |
| `act-2/4` | inline | Ask one friend if they want to go to the cinema. | Ти хочеш піти в кіно? | C | M18; U13/U14/U15/U46. The English situation specifies the modal meaning expressed by Ти хочеш піти в кіно?; other options express a different modality. |
| `act-2/5` | inline | Ask politely what the server can recommend. | Що можете порадити? | C | M18; U13/U14/U15/U46. The English situation specifies the modal meaning expressed by Що можете порадити?; other options express a different modality. |
| `act-2/6` | inline | The menu word is кава. With friends, you want coffee. | Я хочу каву. | C | M18; U13/U14/U15/U46. The English situation specifies the modal meaning expressed by Я хочу каву.; other options express a different modality. |
| `act-2/7` | inline | You have to study new words. | Я мушу вчити нові слова. | C | M18; U13/U14/U15/U46. The English situation specifies the modal meaning expressed by Я мушу вчити нові слова.; other options express a different modality. |
| `act-3/0` | inline | Я ___ гуляти, але не можу сьогодні. | хочу | D | M18; U13/U14/U15. The stem permits a different modal meaning; the English cue fixes the intended desire, ability or obligation. |
| `act-3/1` | inline | Я хочу піти, але не ___. | можу | D | M18; U13/U14/U15. The stem permits a different modal meaning; the English cue fixes the intended desire, ability or obligation. |
| `act-3/2` | inline | Я не можу: я ___ працювати. | мушу | D | M18; U13/U14/U15. The stem permits a different modal meaning; the English cue fixes the intended desire, ability or obligation. |
| `act-3/3` | inline | Оля ___ гуляти, але не може сьогодні. | хоче | D | M18; U13/U14/U15. The stem permits a different modal meaning; the English cue fixes the intended desire, ability or obligation. |
| `act-3/4` | inline | Денис не ___ піти: він мусить працювати. | може | D | M18; U13/U14/U15. The stem permits a different modal meaning; the English cue fixes the intended desire, ability or obligation. |
| `act-3/5` | inline | Вони хочуть гуляти, але ___ працювати. | мусять | D | M18; U13/U14/U15. The stem permits a different modal meaning; the English cue fixes the intended desire, ability or obligation. |
| `act-4/0` | inline | хотіти | І дієвідміна, особливі форми хочу, хочеш | C | M18; U13/U14/U15/U46. The VESUM paradigm and U46 endings support the keyed grammatical classification: І дієвідміна, особливі форми хочу, хочеш. |
| `act-4/1` | inline | могти | І дієвідміна, особливі форми можу, можеш | C | M18; U13/U14/U15/U46. The VESUM paradigm and U46 endings support the keyed grammatical classification: І дієвідміна, особливі форми можу, можеш. |
| `act-4/2` | inline | мусити | ІІ дієвідміна; learn я мушу | C | M18; U13/U14/U15/U46. The VESUM paradigm and U46 endings support the keyed grammatical classification: ІІ дієвідміна; learn я мушу. |
| `act-4/3` | inline | читати | І дієвідміна, regular review verb | C | M18; U13/U14/U15/U46. The VESUM paradigm and U46 endings support the keyed grammatical classification: І дієвідміна, regular review verb. |
| `act-4/4` | inline | говорити | ІІ дієвідміна, regular review verb | C | M18; U13/U14/U15/U46. The VESUM paradigm and U46 endings support the keyed grammatical classification: ІІ дієвідміна, regular review verb. |
| `act-4/5` | inline | допомогти | Infinitive after можу in this lesson | C | M18; U13/U14/U15/U46. The VESUM paradigm and U46 endings support the keyed grammatical classification: Infinitive after можу in this lesson. |

### 19. questions

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | ___ ти? | Хто | D | M19; U23/U24/U25/U26/U45. Another offered question word makes a defensible question with a different focus. The cue specifies the intended question. |
| `act-1/1` | inline | ___ ти вивчаєш? | Що | D | M19; U23/U24/U25/U26/U45. Another offered question word makes a defensible question with a different focus. The cue specifies the intended question. |
| `act-1/2` | inline | ___ ти живеш? | Де | D | M19; U23/U24/U25/U26/U45. Another offered question word makes a defensible question with a different focus. The cue specifies the intended question. |
| `act-1/3` | inline | ___ ти ходиш? | Куди | D | M19; U23/U24/U25/U26/U45. Another offered question word makes a defensible question with a different focus. The cue specifies the intended question. |
| `act-1/4` | inline | ___ ти працюєш? | Коли | D | M19; U23/U24/U25/U26/U45. Another offered question word makes a defensible question with a different focus. The cue specifies the intended question. |
| `act-1/5` | inline | ___ ти не працюєш? | Чому | D | M19; U23/U24/U25/U26/U45. Another offered question word makes a defensible question with a different focus. The cue specifies the intended question. |
| `act-1/6` | inline | ___ справи? | Як | C | M19; U23/U24/U25/U26/U45. The requested ready phrase or explicit negative English/source meaning selects Як; the offered alternatives do not express it. |
| `act-1/7` | inline | ___ говорить українською? | Хто | D | M19; U23/U24/U25/U26/U45. Another offered question word makes a defensible question with a different focus. The cue specifies the intended question. |
| `act-2/0` | inline | Я знаю. -> Я ___ знаю. | не | C | M19; U23/U24/U25/U26/U45. The requested ready phrase or explicit negative English/source meaning selects не; the offered alternatives do not express it. |
| `act-2/1` | inline | Він працює. -> Він ___ працює. | не | C | M19; U23/U24/U25/U26/U45. The requested ready phrase or explicit negative English/source meaning selects не; the offered alternatives do not express it. |
| `act-2/2` | inline | Я хочу читати. -> Я ___ хочу читати. | не | C | M19; U23/U24/U25/U26/U45. The requested ready phrase or explicit negative English/source meaning selects не; the offered alternatives do not express it. |
| `act-2/3` | inline | Я можу піти. -> Я ___ можу піти. | не | C | M19; U23/U24/U25/U26/U45. The requested ready phrase or explicit negative English/source meaning selects не; the offered alternatives do not express it. |
| `act-2/4` | inline | Хтось знає. -> ___ не знає. | Ніхто | C | M19; U23/U24/U25/U26/U45. The requested ready phrase or explicit negative English/source meaning selects Ніхто; the offered alternatives do not express it. |
| `act-2/5` | inline | Я щось знаю. -> Я ___ не знаю. | нічого | C | M19; U23/U24/U25/U26/U45. The requested ready phrase or explicit negative English/source meaning selects нічого; the offered alternatives do not express it. |
| `act-2/6` | inline | Хтось говорить. -> ___ не говорить. | Ніхто | C | M19; U23/U24/U25/U26/U45. The requested ready phrase or explicit negative English/source meaning selects Ніхто; the offered alternatives do not express it. |
| `act-2/7` | inline | Я завжди працюю вночі. -> Я ___ не працюю вночі. | ніколи | C | M19; U23/U24/U25/U26/U45. The requested ready phrase or explicit negative English/source meaning selects ніколи; the offered alternatives do not express it. |
| `act-4/0` | inline | Nobody knows. | Ніхто не знає. | C | M19; U23/U24/U25/U26/U45. The requested ready phrase or explicit negative English/source meaning selects Ніхто не знає.; the offered alternatives do not express it. |
| `act-4/1` | inline | I know nothing. | Я нічого не знаю. | C | M19; U23/U24/U25/U26/U45. The requested ready phrase or explicit negative English/source meaning selects Я нічого не знаю.; the offered alternatives do not express it. |
| `act-4/2` | inline | Nobody speaks Ukrainian. | Ніхто не говорить українською. | C | M19; U23/U24/U25/U26/U45. The requested ready phrase or explicit negative English/source meaning selects Ніхто не говорить українською.; the offered alternatives do not express it. |
| `act-4/3` | inline | I never work at night. | Я ніколи не працюю вночі. | C | M19; U23/U24/U25/U26/U45. The requested ready phrase or explicit negative English/source meaning selects Я ніколи не працюю вночі.; the offered alternatives do not express it. |
| `act-4/4` | inline | The book is nowhere. | Книги ніде немає. | C | M19; U23/U24/U25/U26/U45. The requested ready phrase or explicit negative English/source meaning selects Книги ніде немає.; the offered alternatives do not express it. |
| `act-4/5` | inline | No, I do not understand. | Ні, я не розумію. | C | M19; U23/U24/U25/U26/U45. The requested ready phrase or explicit negative English/source meaning selects Ні, я не розумію.; the offered alternatives do not express it. |

### 20. my-morning

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | я вмиваю__ | ся | C | M20; K/U11/U12/U16/U33/U34. The title explicitly requests -ся; K verifies the full completion. Contracted -сь forms do not satisfy that stated task. |
| `act-1/1` | inline | ти одягаєш__ | ся | C | M20; K/U11/U12/U16/U33/U34. The title explicitly requests -ся; K verifies the full completion. Contracted -сь forms do not satisfy that stated task. |
| `act-1/2` | inline | він прокидаєть__ | ся | C | M20; K/U11/U12/U16/U33/U34. The title explicitly requests -ся; K verifies the full completion. Contracted -сь forms do not satisfy that stated task. |
| `act-1/3` | inline | ми збираємо__ | ся | C | M20; K/U11/U12/U16/U33/U34. The title explicitly requests -ся; K verifies the full completion. Contracted -сь forms do not satisfy that stated task. |
| `act-1/4` | inline | ви вмиваєте__ | ся | C | M20; K/U11/U12/U16/U33/U34. The title explicitly requests -ся; K verifies the full completion. Contracted -сь forms do not satisfy that stated task. |
| `act-1/5` | inline | вони прокидають__ | ся | C | M20; K/U11/U12/U16/U33/U34. The title explicitly requests -ся; K verifies the full completion. Contracted -сь forms do not satisfy that stated task. |
| `act-1/6` | inline | я прокидаю__ | ся | C | M20; K/U11/U12/U16/U33/U34. The title explicitly requests -ся; K verifies the full completion. Contracted -сь forms do not satisfy that stated task. |
| `act-1/7` | inline | вона одягаєть__ | ся | C | M20; K/U11/U12/U16/U33/U34. The title explicitly requests -ся; K verifies the full completion. Contracted -сь forms do not satisfy that stated task. |
| `act-1/8` | inline | ти збираєш__ | ся | C | M20; K/U11/U12/U16/U33/U34. The title explicitly requests -ся; K verifies the full completion. Contracted -сь forms do not satisfy that stated task. |
| `act-1/9` | inline | ми повертаємо__ | ся | C | M20; K/U11/U12/U16/U33/U34. The title explicitly requests -ся; K verifies the full completion. Contracted -сь forms do not satisfy that stated task. |
| `act-2/0` | inline | I wash up in the morning. | Я вмиваюся вранці. | C | M20; K/U11/U12/U16/U33/U34. The explicit English translation selects Я вмиваюся вранці.; transitive, non-reflexive or mismatched forms do not express that translation. |
| `act-2/1` | inline | I wash my hands. | Я вмиваю руки. | C | M20; K/U11/U12/U16/U33/U34. The explicit English translation selects Я вмиваю руки.; transitive, non-reflexive or mismatched forms do not express that translation. |
| `act-2/2` | inline | I have breakfast at home. | Я снідаю вдома. | C | M20; K/U11/U12/U16/U33/U34. The explicit English translation selects Я снідаю вдома.; transitive, non-reflexive or mismatched forms do not express that translation. |
| `act-2/3` | inline | I get dressed quickly. | Я швидко одягаюся. | C | M20; K/U11/U12/U16/U33/U34. The explicit English translation selects Я швидко одягаюся.; transitive, non-reflexive or mismatched forms do not express that translation. |
| `act-2/4` | inline | I put on a shirt. | Я одягаю сорочку. | C | M20; K/U11/U12/U16/U33/U34. The explicit English translation selects Я одягаю сорочку.; transitive, non-reflexive or mismatched forms do not express that translation. |
| `act-2/5` | inline | I wake up late on Saturday. | У суботу я прокидаюся пізно. | C | M20; K/U11/U12/U16/U33/U34. The explicit English translation selects У суботу я прокидаюся пізно.; transitive, non-reflexive or mismatched forms do not express that translation. |
| `act-2/6` | inline | I study in the morning. | Я навчаюся вранці. | C | M20; K/U11/U12/U16/U33/U34. The explicit English translation selects Я навчаюся вранці.; transitive, non-reflexive or mismatched forms do not express that translation. |
| `act-2/7` | inline | I go to work. | Я йду на роботу. | C | M20; K/U11/U12/U16/U33/U34. The explicit English translation selects Я йду на роботу.; transitive, non-reflexive or mismatched forms do not express that translation. |
| `act-3/0` | inline | ___ я прокидаюся о сьомій. | Спочатку | D | M20; U11/U12/U33/U34. The routine does not uniquely require this sequencing expression; a gloss selects the intended sequencing meaning or single-word form. |
| `act-3/1` | inline | ___ я вмиваюся. | Потім | D | M20; U11/U12/U33/U34. The routine does not uniquely require this sequencing expression; a gloss selects the intended sequencing meaning or single-word form. |
| `act-3/2` | inline | ___ я одягаюся. | Після цього | D | M20; U11/U12/U33/U34. The routine does not uniquely require this sequencing expression; a gloss selects the intended sequencing meaning or single-word form. |
| `act-3/3` | inline | ___ я снідаю. | Потім | D | M20; U11/U12/U33/U34. The routine does not uniquely require this sequencing expression; a gloss selects the intended sequencing meaning or single-word form. |
| `act-3/4` | inline | ___ я йду на роботу. | Нарешті | D | M20; U11/U12/U33/U34. The routine does not uniquely require this sequencing expression; a gloss selects the intended sequencing meaning or single-word form. |
| `act-3/5` | inline | Спочатку я прокидаюся. ___ я вмиваюся. | Потім | D | M20; U11/U12/U33/U34. The routine does not uniquely require this sequencing expression; a gloss selects the intended sequencing meaning or single-word form. |
| `act-4/0` | inline | ___ я прокидаюся о восьмій. | Спочатку | D | M20; U11/U12/U33/U34. The routine does not uniquely require this sequencing expression; a gloss selects the intended sequencing meaning or single-word form. |
| `act-4/1` | inline | ___ я вмиваюся і снідаю. | Потім | D | M20; U11/U12/U33/U34. The routine does not uniquely require this sequencing expression; a gloss selects the intended sequencing meaning or single-word form. |
| `act-4/2` | inline | ___ я йду в університет. | Нарешті | D | M20; U11/U12/U33/U34. The routine does not uniquely require this sequencing expression; a gloss selects the intended sequencing meaning or single-word form. |

### 21. checkpoint-actions

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | Я ___ книгу. | читаю | C | M21; U13/U14/U15/U23/U24/U25/U46. The subject fixes the person/number of читаю; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/1` | inline | Ти ___ українською? | говориш | C | M21; U13/U14/U15/U23/U24/U25/U46. The subject fixes the person/number of говориш; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/2` | inline | Вона ___ в офісі. | працює | C | M21; U13/U14/U15/U23/U24/U25/U46. The subject fixes the person/number of працює; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/3` | inline | Ми ___ українською. | говоримо | C | M21; U13/U14/U15/U23/U24/U25/U46. The subject fixes the person/number of говоримо; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/4` | inline | Вони ___ у парку. | гуляють | C | M21; U13/U14/U15/U23/U24/U25/U46. The subject fixes the person/number of гуляють; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/5` | inline | Ви ___ дуже гарно. | пишете | C | M21; U13/U14/U15/U23/U24/U25/U46. The subject fixes the person/number of пишете; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/6` | inline | Він ___ українською. | говорить | C | M21; U13/U14/U15/U23/U24/U25/U46. The subject fixes the person/number of говорить; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/7` | inline | Ви ___ сьогодні? | працюєте | C | M21; U13/U14/U15/U23/U24/U25/U46. The subject fixes the person/number of працюєте; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/8` | inline | Я ___ вправу. | роблю | C | M21; U13/U14/U15/U23/U24/U25/U46. The subject fixes the person/number of роблю; the competing forms do not agree. K verifies complete ending constructions. |
| `act-1/9` | inline | Вони ___ книгу. | читають | C | M21; U13/U14/U15/U23/U24/U25/U46. The subject fixes the person/number of читають; the competing forms do not agree. K verifies complete ending constructions. |
| `act-2/0` | inline | Олег: ___ готує сьогодні? | Хто | D | M21; U13/U23/U24/U25. Several offered question words, actions or modals fit the open dialogue. The cue identifies its intended meaning. |
| `act-2/1` | inline | Олег: Коли ти ___? | прокидаєшся | D | M21; U13/U23/U24/U25. Several offered question words, actions or modals fit the open dialogue. The cue identifies its intended meaning. |
| `act-2/2` | inline | Олег: Що ти ___ потім? | робиш | C | M21; U13/U14/U15/U23/U24/U25/U46. The subject, infinitive complement or object construction selects робиш; the other offered forms do not fit that construction. |
| `act-2/3` | inline | Марина: Я ___ в школі. | працюю | C | M21; U13/U14/U15/U23/U24/U25/U46. The subject, infinitive complement or object construction selects працюю; the other offered forms do not fit that construction. |
| `act-2/4` | inline | Олег: Ти ___ читати ввечері? | любиш | C | M21; U13/U14/U15/U23/U24/U25/U46. The subject, infinitive complement or object construction selects любиш; the other offered forms do not fit that construction. |
| `act-2/5` | inline | Олег: Я ___ готувати сьогодні. | хочу | D | M21; U13/U23/U24/U25. Several offered question words, actions or modals fit the open dialogue. The cue identifies its intended meaning. |
| `act-2/6` | inline | Олег: Ти ___ допомагати? | можеш | C | M21; U13/U14/U15/U23/U24/U25/U46. The subject, infinitive complement or object construction selects можеш; the other offered forms do not fit that construction. |
| `act-2/7` | inline | Марина: Не можу зараз, ___ працювати. | мушу | C | M21; U13/U14/U15/U23/U24/U25/U46. The subject, infinitive complement or object construction selects мушу; the other offered forms do not fit that construction. |
| `act-3/0` | inline | ___ я прокидаюся о сьомій. | Спочатку | D | M21; U11/U12/U33/U34. The day description allows another offered sequence word or finite action; its intended action or sequence is now explicit. |
| `act-3/1` | inline | Потім я ___ і чищу зуби. | вмиваюся | D | M21; U11/U12/U33/U34. The day description allows another offered sequence word or finite action; its intended action or sequence is now explicit. |
| `act-3/2` | inline | Після цього я ___ вдома. | снідаю | D | M21; U11/U12/U33/U34. The day description allows another offered sequence word or finite action; its intended action or sequence is now explicit. |
| `act-3/3` | inline | Вдень я ___ в офісі. | працюю | D | M21; U11/U12/U33/U34. The day description allows another offered sequence word or finite action; its intended action or sequence is now explicit. |
| `act-3/4` | inline | Увечері я ___ гуляти. | хочу | C | M21; U13/U14/U15/U23/U24/U25/U46. The subject, infinitive complement or object construction selects хочу; the other offered forms do not fit that construction. |
| `act-3/5` | inline | Нарешті я ___ фільм. | дивлюся | C | M21; U13/U14/U15/U23/U24/U25/U46. The subject, infinitive complement or object construction selects дивлюся; the other offered forms do not fit that construction. |

### 22. what-time

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | 1:00 | Перша. | C | M22; U36/U37/U38. The explicit clock-label or о/об schedule task selects Перша., rather than a duration or a mismatched case. |
| `act-1/1` | inline | 2:00 | Друга. | C | M22; U36/U37/U38. The explicit clock-label or о/об schedule task selects Друга., rather than a duration or a mismatched case. |
| `act-1/2` | inline | 3:00 | Третя. | C | M22; U36/U37/U38. The explicit clock-label or о/об schedule task selects Третя., rather than a duration or a mismatched case. |
| `act-1/3` | inline | 5:00 | П'ята. | C | M22; U36/U37/U38. The explicit clock-label or о/об schedule task selects П'ята., rather than a duration or a mismatched case. |
| `act-1/4` | inline | 7:00 | Сьома. | C | M22; U36/U37/U38. The explicit clock-label or о/об schedule task selects Сьома., rather than a duration or a mismatched case. |
| `act-1/5` | inline | 8:00 | Восьма. | C | M22; U36/U37/U38. The explicit clock-label or о/об schedule task selects Восьма., rather than a duration or a mismatched case. |
| `act-1/6` | inline | 10:00 | Десята. | C | M22; U36/U37/U38. The explicit clock-label or о/об schedule task selects Десята., rather than a duration or a mismatched case. |
| `act-1/7` | inline | 11:00 | Одинадцята. | C | M22; U36/U37/U38. The explicit clock-label or о/об schedule task selects Одинадцята., rather than a duration or a mismatched case. |
| `act-2/0` | inline | Я прокидаюся о ___. | сьомій | C | M22; U36/U37/U38. The explicit clock-label or о/об schedule task selects сьомій, rather than a duration or a mismatched case. |
| `act-2/1` | inline | Я снідаю о ___. | восьмій | C | M22; U36/U37/U38. The explicit clock-label or о/об schedule task selects восьмій, rather than a duration or a mismatched case. |
| `act-2/2` | inline | Я працюю о ___. | дев'ятій | C | M22; U36/U37/U38. The explicit clock-label or о/об schedule task selects дев'ятій, rather than a duration or a mismatched case. |
| `act-2/3` | inline | Обід о ___. | першій | C | M22; U36/U37/U38. The explicit clock-label or о/об schedule task selects першій, rather than a duration or a mismatched case. |
| `act-2/4` | inline | Зустріч о ___. | другій | C | M22; U36/U37/U38. The explicit clock-label or о/об schedule task selects другій, rather than a duration or a mismatched case. |
| `act-2/5` | inline | Кава о ___. | третій | C | M22; U36/U37/U38. The explicit clock-label or о/об schedule task selects третій, rather than a duration or a mismatched case. |
| `act-2/6` | inline | Урок о ___. | четвертій | C | M22; U36/U37/U38. The explicit clock-label or о/об schedule task selects четвертій, rather than a duration or a mismatched case. |
| `act-2/7` | inline | Фільм об ___. | одинадцятій | C | M22; U36/U37/U38. The explicit clock-label or о/об schedule task selects одинадцятій, rather than a duration or a mismatched case. |
| `act-4/0` | inline | Я прокидаюся о сьомій ___. | ранку | D | M22; U36/U37/U38. The clock hour or activity alone does not exclude another time of day. The 24-hour cue specifies the intended period. |
| `act-4/1` | inline | Я снідаю о восьмій ___. | ранку | D | M22; U36/U37/U38. The clock hour or activity alone does not exclude another time of day. The 24-hour cue specifies the intended period. |
| `act-4/2` | inline | Я обідаю о першій ___. | дня | D | M22; U36/U37/U38. The clock hour or activity alone does not exclude another time of day. The 24-hour cue specifies the intended period. |
| `act-4/3` | inline | Зустріч о третій ___. | дня | D | M22; U36/U37/U38. The clock hour or activity alone does not exclude another time of day. The 24-hour cue specifies the intended period. |
| `act-4/4` | inline | Я вечеряю о сьомій ___. | вечора | D | M22; U36/U37/U38. The clock hour or activity alone does not exclude another time of day. The 24-hour cue specifies the intended period. |
| `act-4/5` | inline | Фільм об одинадцятій ___. | вечора | D | M22; U36/U37/U38. The clock hour or activity alone does not exclude another time of day. The 24-hour cue specifies the intended period. |

### 23. days-and-months

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | понеділок, ___, середа | вівторок | C | M23; U01. The specified chronological order or calendar case selects вівторок; the offered alternatives do not complete that sequence/construction. |
| `act-1/1` | inline | середа, ___, п'ятниця | четвер | C | M23; U01. The specified chronological order or calendar case selects четвер; the offered alternatives do not complete that sequence/construction. |
| `act-1/2` | inline | п'ятниця, ___, неділя | субота | C | M23; U01. The specified chronological order or calendar case selects субота; the offered alternatives do not complete that sequence/construction. |
| `act-1/3` | inline | неділя, ___, вівторок | понеділок | C | M23; U01. The specified chronological order or calendar case selects понеділок; the offered alternatives do not complete that sequence/construction. |
| `act-1/4` | inline | вівторок, середа, ___ | четвер | C | M23; U01. The specified chronological order or calendar case selects четвер; the offered alternatives do not complete that sequence/construction. |
| `act-1/5` | inline | четвер, п'ятниця, ___ | субота | C | M23; U01. The specified chronological order or calendar case selects субота; the offered alternatives do not complete that sequence/construction. |
| `act-1/6` | inline | субота, ___, понеділок | неділя | C | M23; U01. The specified chronological order or calendar case selects неділя; the offered alternatives do not complete that sequence/construction. |
| `act-3/0` | inline | Я працюю ___. | у понеділок | D | M23; U01. Both у понеділок and в понеділок are grammatical variants; the original preceding vowel favors в rather than the key у. |
| `act-3/1` | inline | Мій день народження ___. | у березні | C | M23; U01. The specified chronological order or calendar case selects у березні; the offered alternatives do not complete that sequence/construction. |
| `act-3/2` | inline | Ми гуляємо ___. | в суботу | C | M23; U01. The specified chronological order or calendar case selects в суботу; the offered alternatives do not complete that sequence/construction. |
| `act-3/3` | inline | ___ холодно. | Взимку | C | M23; U01. The specified chronological order or calendar case selects Взимку; the offered alternatives do not complete that sequence/construction. |
| `act-3/4` | inline | Я вивчаю українську ___. | у вівторок | C | M23; U01. The specified chronological order or calendar case selects у вівторок; the offered alternatives do not complete that sequence/construction. |
| `act-3/5` | inline | Вони відпочивають ___. | у серпні | C | M23; U01. The specified chronological order or calendar case selects у серпні; the offered alternatives do not complete that sequence/construction. |

### 24. weather

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-2/0` | inline | Взимку часто ___. | іде сніг | D | M24; U18/U39/U40/U41. A season does not rule out the other offered weather conditions. The cue specifies the intended weather meaning. |
| `act-2/1` | inline | Влітку дуже ___. | спекотно | D | M24; U18/U39/U40/U41. A season does not rule out the other offered weather conditions. The cue specifies the intended weather meaning. |
| `act-2/2` | inline | Восени часто ___. | іде дощ | D | M24; U18/U39/U40/U41. A season does not rule out the other offered weather conditions. The cue specifies the intended weather meaning. |
| `act-2/3` | inline | Навесні ___ і красиво. | тепло | D | M24; U18/U39/U40/U41. A season does not rule out the other offered weather conditions. The cue specifies the intended weather meaning. |
| `act-2/4` | inline | Сьогодні мінус п'ять, дуже ___. | холодно | C | M24; U18/U39/U40/U41. The explicit temperature, question agreement or future-time construction selects холодно; the other choices contradict that cue or fail agreement. |
| `act-2/5` | inline | Сьогодні плюс двадцять п'ять, ___. | тепло | C | M24; U18/U39/U40/U41. The explicit temperature, question agreement or future-time construction selects тепло; the other choices contradict that cue or fail agreement. |
| `act-3/0` | inline | — Яка сьогодні ___? — Сьогодні тепло. | погода | C | M24; U18/U39/U40/U41. The explicit temperature, question agreement or future-time construction selects погода; the other choices contradict that cue or fail agreement. |
| `act-3/1` | inline | — Завтра ___ сонячно. — Добре, гуляємо! | буде | C | M24; U18/U39/U40/U41. The explicit temperature, question agreement or future-time construction selects буде; the other choices contradict that cue or fail agreement. |
| `act-3/2` | inline | — Яка пора року тобі ___? — Літо. | подобається | C | M24; U18/U39/U40/U41. The explicit temperature, question agreement or future-time construction selects подобається; the other choices contradict that cue or fail agreement. |
| `act-3/3` | inline | — Чому ти любиш літо? — Тому що влітку ___. | сонячно | D | M24; U39/U40/U41. A speaker can like summer for different weather; the stem does not by itself exclude cloudy or cold. The intended reason is now specified. |

### 25. my-day

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-2/0` | inline | ___ я прокидаюся і вмиваюся. | Спочатку | D | M25; U11/U12/U33/U34. The short routine allows another offered action or sequence without an explicit meaning or time reference. |
| `act-2/1` | inline | Після того я ___. | снідаю | D | M25; U11/U12/U33/U34. The short routine allows another offered action or sequence without an explicit meaning or time reference. |
| `act-2/2` | inline | Вдень я ___ в офісі. | працюю | D | M25; U11/U12/U33/U34. The short routine allows another offered action or sequence without an explicit meaning or time reference. |
| `act-2/3` | inline | О першій годині я ___. | обідаю | D | M25; U11/U12/U33/U34. The short routine allows another offered action or sequence without an explicit meaning or time reference. |
| `act-2/4` | inline | ___ я читаю книгу або дивлюся фільм. | Потім | D | M25; U11/U12/U33/U34. The short routine allows another offered action or sequence without an explicit meaning or time reference. |
| `act-2/5` | inline | ___ я лягаю спати о дванадцятій. | Нарешті | D | M25; U11/U12/U33/U34. The short routine allows another offered action or sequence without an explicit meaning or time reference. |
| `act-3/0` | inline | Я п'ю каву ___. | вранці | D | M25; U34/U36/U37/U38. The activity can occur at another offered time. The cue supplies the missing time information. |
| `act-3/1` | inline | Ми вечеряємо ___. | ввечері | D | M25; U34/U36/U37/U38. The activity can occur at another offered time. The cue supplies the missing time information. |
| `act-3/2` | inline | Вона працює з дев'ятої до п'ятої ___. | вдень | D | M25; U34/U36/U37/U38. The activity can occur at another offered time. The cue supplies the missing time information. |
| `act-3/3` | inline | Вони гуляють у парку ___. | після обіду | D | M25; U34/U36/U37/U38. The activity can occur at another offered time. The cue supplies the missing time information. |
| `act-4/0` | inline | Вранці я ___. | беру душ | D | M25; U07/U27/U28. The rejected приймаю душ is attested and VTS permits hygienic procedures. A person-agreement distractor replaces it. |
| `act-4/1` | inline | Коли я хворий, я ___. | п'ю ліки | D | M25; U07/U48. Приймаю ліки is standard medicine use, not an error. The replacement fails agreement with я. |
| `act-4/2` | inline | ___ зараз? — Восьма. | Котра година | C | M25; U07/U08/U11/U12/U21/U30/U31/U33/U34/U36/U37/U38/U48. The normative-form instruction and lexical/morphological evidence support Котра година; the other original form does not satisfy that specified register or construction. |
| `act-4/3` | inline | ___ в парк після обіду! | Ходімо | C | M25; U07/U08/U11/U12/U21/U30/U31/U33/U34/U36/U37/U38/U48. The normative-form instruction and lexical/morphological evidence support Ходімо; the other original form does not satisfy that specified register or construction. |
| `act-4/4` | inline | О восьмій годині я їм ___. | сніданок | C | M25; U07/U08/U11/U12/U21/U30/U31/U33/U34/U36/U37/U38/U48. The normative-form instruction and lexical/morphological evidence support сніданок; the other original form does not satisfy that specified register or construction. |
| `act-4/5` | inline | Мама готує дуже ___ обід. | смачний | C | M25; U07/U08/U11/U12/U21/U30/U31/U33/U34/U36/U37/U38/U48. The normative-form instruction and lexical/morphological evidence support смачний; the other original form does not satisfy that specified register or construction. |
| `act-4/6` | inline | Ввечері я хочу ___. | поїсти | C | M25; U07/U08/U11/U12/U21/U30/U31/U33/U34/U36/U37/U38/U48. The normative-form instruction and lexical/morphological evidence support поїсти; the other original form does not satisfy that specified register or construction. |
| `act-4/7` | inline | О сьомій я ___ і встав. | прокинувся | D | M25; U08/U20/U21. Проснувся is an attested waking-up form. The retained встав fixes masculine agreement and excludes the feminine replacement. |

### 26. free-time

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-2/0` | inline | Я ___ працюю у неділю. | ніколи не | D | M26; U42/U43/U44. The sentence does not specify frequency strongly enough to rule out another offered frequency. The gloss selects the intended frequency. |
| `act-2/1` | inline | Вона грає у теніс двічі ___. | на тиждень | D | M26; U17. У тиждень is attested for frequency. The replacement forms do not express the requested twice-per-week phrase. |
| `act-2/2` | inline | — ___ в кіно у суботу! — Добре! | Ходімо | D | M26; U22/U30/U31/U51. Ідемо can function as an invitation. Person-mismatched statements replace the competing invitation forms. |
| `act-2/3` | inline | Я люблю спорт, тому ___ граю у баскетбол. | часто | D | M26; U42/U43/U44. The sentence does not specify frequency strongly enough to rule out another offered frequency. The gloss selects the intended frequency. |
| `act-2/4` | inline | Я не маю часу, тому ___ читаю книги. | рідко | D | M26; U42/U43/U44. The sentence does not specify frequency strongly enough to rule out another offered frequency. The gloss selects the intended frequency. |
| `act-2/5` | inline | — Що ти робиш ___? — Відпочиваю. | у вихідні | D | M26; U29/U52. На вихідні has attested weekend-time usage and the present question can ask about a plan. The replacement has the wrong calendar case. |
| `act-3/0` | inline | Він грає ___ піаніно. | на | C | M26; U01/U17/U22/U29/U42/U43/U44/U49. The instrument or concert object requires the keyed preposition на; the other offered prepositions do not fit that phrase. |
| `act-3/1` | inline | Ми граємо ___ футбол. | у | D | M26; U01/U49. У and в are variants of the same preposition. The competing valid variant is replaced with a preposition incompatible with the stated object case. |
| `act-3/2` | inline | Я хочу ходити ___ концерт. | на | C | M26; U01/U17/U22/U29/U42/U43/U44/U49. The instrument or concert object requires the keyed preposition на; the other offered prepositions do not fit that phrase. |
| `act-3/3` | inline | Вони ходять ___ театр раз на місяць. | в | D | M26; U01/U49. У and в are variants of the same preposition. The competing valid variant is replaced with a preposition incompatible with the stated object case. |

### 27. checkpoint-time-nature

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | Зустріч ___ годині. | о п'ятій | C | M27; U18/U33/U34/U36/U37/U38/U39/U40. The time/calendar case or з...до range selects о п'ятій; the other offered forms do not express that construction. |
| `act-1/1` | inline | Ми йдемо в кіно ___. | у суботу | C | M27; U18/U33/U34/U36/U37/U38/U39/U40. The time/calendar case or з...до range selects у суботу; the other offered forms do not express that construction. |
| `act-1/2` | inline | Мій день народження ___. | у січні | C | M27; U18/U33/U34/U36/U37/U38/U39/U40. The time/calendar case or з...до range selects у січні; the other offered forms do not express that construction. |
| `act-1/3` | inline | Сьогодні ___ і холодно. | іде дощ | D | M27; U18. Дощить means that rain is falling and also completes the stem. The replacement mismatches singular дощ. |
| `act-1/4` | inline | Взимку дуже ___. | холодно | D | M27; U39/U40. Winter alone does not exclude warm weather. The cue supplies the intended weather meaning. |
| `act-1/5` | inline | Я прокидаюся о сьомій ___. | ранку | D | M27; U36. О сьомій вранці is also a defensible morning-time expression; the new nominative distractor does not complete the time expression. |
| `act-3/0` | inline | ___ я прокидаюся і снідаю. | Спочатку | D | M27; U11/U12/U33/U34/U36/U37/U38/U39/U40. Another offered sequence, period or weather can describe the day. The explicit cue fixes the intended meaning. |
| `act-3/1` | inline | ___ я йду на роботу. | Потім | D | M27; U11/U12/U33/U34/U36/U37/U38/U39/U40. Another offered sequence, period or weather can describe the day. The explicit cue fixes the intended meaning. |
| `act-3/2` | inline | Я працюю з дев'ятої ___ п'ятої. | до | C | M27; U18/U33/U34/U36/U37/U38/U39/U40. The time/calendar case or з...до range selects до; the other offered forms do not express that construction. |
| `act-3/3` | inline | ___ я гуляю в парку. | Після обіду | D | M27; U11/U12/U33/U34/U36/U37/U38/U39/U40. Another offered sequence, period or weather can describe the day. The explicit cue fixes the intended meaning. |
| `act-3/4` | inline | Я гуляю, тому що сьогодні ___ і сонячно. | тепло | D | M27; U11/U12/U33/U34/U36/U37/U38/U39/U40. Another offered sequence, period or weather can describe the day. The explicit cue fixes the intended meaning. |
| `act-3/5` | inline | ___ я вечеряю і слухаю музику. | Ввечері | D | M27; U11/U12/U33/U34/U36/U37/U38/U39/U40. Another offered sequence, period or weather can describe the day. The explicit cue fixes the intended meaning. |
| `act-3/6` | inline | ___ я лягаю спати о дванадцятій. | Нарешті | D | M27; U11/U12/U33/U34/U36/U37/U38/U39/U40. Another offered sequence, period or weather can describe the day. The explicit cue fixes the intended meaning. |

### 28. euphony

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | Я живу ___ Києві. | в | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select в under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-1/1` | inline | Сестра ___ Львові. | у | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select у under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-1/2` | inline | Вона ___ школі. | в | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select в under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-1/3` | inline | Тарас ___ школі. | у | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select у under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-1/4` | inline | Я працюю ___ офісі. | в | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select в under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-1/5` | inline | Максим працює ___ банку. | у | D | M28; U01. The original adjacent word працює ends in a vowel and favors в банку, contrary to the key and explanation. Removing that word repairs the context and preserves the target у. |
| `act-1/6` | inline | ___ місті цікаво. | У | D | M28; U01. Pravopys §23 explicitly permits initial В before a consonant; the replacement has the wrong case for місті. |
| `act-1/7` | inline | ___ Одесі тепло. | В | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select В under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-1/8` | inline | Квиток ___ кіно. | у | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select у under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-1/9` | inline | Так, ___ нас є час. | у | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select у under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-2/0` | inline | Брат ___ сестра в школі. | і | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select і under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-2/1` | inline | Мама ___ тато в театрі. | й | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select й under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-2/2` | inline | Ти ___ Олена йдете в театр? | й | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select й under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-2/3` | inline | Я ___ Максим ідемо в парк. | і | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select і under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-2/4` | inline | Марія ___ Яна в місті. | і | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select і under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-2/5` | inline | Іван ___ Яна в офісі. | і | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select і under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-2/6` | inline | Олена ___ Анна вдома. | й | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select й under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-2/7` | inline | ___ він іде? | І | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select І under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-3/0` | inline | Я йду ___ школи. | зі | D | M28; U03/U47. Із школи is attested alongside зі школи. The replacement does not take the genitive школи in this place phrase. |
| `act-3/1` | inline | Софія ___ мною. | зі | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select зі under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-3/2` | inline | Він ___ Одеси. | з | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select з under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-3/3` | inline | Іван ___ другом. | з | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select з under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-3/4` | inline | Максим ___ сестрою. | із | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select із under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-3/5` | inline | ___ святом! | Зі | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select Зі under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-4/0` | inline | Choose the natural place line. | Я живу в Києві. | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select Я живу в Києві. under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-4/1` | inline | Choose the natural Lviv line. | Сестра у Львові. | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select Сестра у Львові. under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-4/2` | inline | Choose the natural family line. | Брат і сестра в школі. | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select Брат і сестра в школі. under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-4/3` | inline | Choose the natural parents line. | Мама й тато в театрі. | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select Мама й тато в театрі. under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-4/4` | inline | Choose the natural school line. | Я йду зі школи. | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select Я йду зі школи. under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |
| `act-4/5` | inline | Choose the natural greeting. | Зі святом! | C | M28; U01/U02/U03. The adjacent sounds and the explicit smoother-form task select Зі святом! under the cited Pravopys rule and its exceptions. This does not label every other variant a nonexistent word. |

## Confirmed defects and repairs

The following 74 rows preserve their original keys. Their final replacement/context tokens are checked in POSTFIX/U50. One original euphony context favored the distractor instead of its key; its cue is repaired rather than changing the target. The remaining repairs exclude a confirmed second defensible answer.

| Item | Usage evidence | Source YAML repair |
| --- | --- | --- |
| `i-want-i-can/act-3/0` | U13/U14/U15 | sentence: "(Express desire: want to.) Я ___ гуляти, але не можу сьогодні." |
| `i-want-i-can/act-3/1` | U13/U14/U15 | sentence: "(Express inability: cannot.) Я хочу піти, але не ___." |
| `i-want-i-can/act-3/2` | U13/U14/U15 | sentence: "(Express obligation: must.) Я не можу: я ___ працювати." |
| `i-want-i-can/act-3/3` | U13/U14/U15 | sentence: "(Express desire: wants to.) Оля ___ гуляти, але не може сьогодні." |
| `i-want-i-can/act-3/4` | U13/U14/U15 | sentence: "(Express inability: cannot.) Денис не ___ піти: він мусить працювати." |
| `i-want-i-can/act-3/5` | U13/U14/U15 | sentence: "(Express obligation: must.) Вони хочуть гуляти, але ___ працювати." |
| `questions/act-1/0` | U23/U24/U25/U26/U45 | prompt: "(Ask who the person is.) ___ ти?" |
| `questions/act-1/1` | U23/U24/U25/U26/U45 | prompt: "(Ask what the person studies.) ___ ти вивчаєш?" |
| `questions/act-1/2` | U23/U24/U25/U26/U45 | prompt: "(Ask where the person lives.) ___ ти живеш?" |
| `questions/act-1/3` | U23/U24/U25/U26/U45 | prompt: "(Ask about destination: where to.) ___ ти ходиш?" |
| `questions/act-1/4` | U23/U24/U25/U26/U45 | prompt: "(Ask when the person works.) ___ ти працюєш?" |
| `questions/act-1/5` | U23/U24/U25/U26/U45 | prompt: "(Ask why.) ___ ти не працюєш?"; options: [{"text": "Чому", "correct": true}, {"text": "Куди", "correct": false}, {"text": "Хто", "correct": false}] |
| `questions/act-1/7` | U23/U24/U25/U26/U45 | prompt: "(Ask which person speaks Ukrainian.) ___ говорить українською?" |
| `my-morning/act-3/0` | U11/U12/U33/U34 | sentence: "(First.) ___ я прокидаюся о сьомій." |
| `my-morning/act-3/1` | U11/U12/U33/U34 | sentence: "(Then.) ___ я вмиваюся." |
| `my-morning/act-3/2` | U11/U12/U33/U34 | sentence: "(After this.) ___ я одягаюся." |
| `my-morning/act-3/3` | U11/U12/U33/U34 | sentence: "(Then.) ___ я снідаю." |
| `my-morning/act-3/4` | U11/U12/U33/U34 | sentence: "(Finally.) ___ я йду на роботу." |
| `my-morning/act-3/5` | U11/U12/U33/U34 | sentence: "(Then: use the single word.) Спочатку я прокидаюся. ___ я вмиваюся." |
| `my-morning/act-4/0` | U11/U12/U33/U34 | sentence: "(First.) ___ я прокидаюся о восьмій." |
| `my-morning/act-4/1` | U11/U12/U33/U34 | sentence: "(Then.) ___ я вмиваюся і снідаю." |
| `my-morning/act-4/2` | U11/U12/U33/U34 | sentence: "(Finally.) ___ я йду в університет." |
| `checkpoint-actions/act-2/0` | U13/U23/U24/U25 | sentence: "(Ask who is cooking.) Олег: ___ готує сьогодні?" |
| `checkpoint-actions/act-2/1` | U13/U23/U24/U25 | sentence: "(Ask when the person wakes up.) Олег: Коли ти ___?" |
| `checkpoint-actions/act-2/5` | U13/U23/U24/U25 | sentence: "(Express desire: want to.) Олег: Я ___ готувати сьогодні." |
| `checkpoint-actions/act-3/0` | U11/U12/U33/U34 | sentence: "(First.) ___ я прокидаюся о сьомій." |
| `checkpoint-actions/act-3/1` | U11/U12/U33/U34 | sentence: "(I wash up.) Потім я ___ і чищу зуби." |
| `checkpoint-actions/act-3/2` | U11/U12/U33/U34 | sentence: "(I have breakfast.) Після цього я ___ вдома." |
| `checkpoint-actions/act-3/3` | U11/U12/U33/U34 | sentence: "(I work.) Вдень я ___ в офісі." |
| `what-time/act-4/0` | U36/U37/U38 | prompt: "(07:00.) Я прокидаюся о сьомій ___." |
| `what-time/act-4/1` | U36/U37/U38 | prompt: "(08:00.) Я снідаю о восьмій ___." |
| `what-time/act-4/2` | U36/U37/U38 | prompt: "(13:00.) Я обідаю о першій ___." |
| `what-time/act-4/3` | U36/U37/U38 | prompt: "(15:00.) Зустріч о третій ___." |
| `what-time/act-4/4` | U36/U37/U38 | prompt: "(19:00.) Я вечеряю о сьомій ___." |
| `what-time/act-4/5` | U36/U37/U38 | prompt: "(23:00.) Фільм об одинадцятій ___." |
| `days-and-months/act-3/0` | U01 | sentence: "Урок ___."; explanation: "After the consonant in урок and before п, у понеділок follows the consonant-to-consonant pattern." |
| `weather/act-2/0` | U18/U39/U40/U41 | sentence: "(It snows.) Взимку часто ___." |
| `weather/act-2/1` | U18/U39/U40/U41 | sentence: "(Hot.) Влітку дуже ___." |
| `weather/act-2/2` | U18/U39/U40/U41 | sentence: "(It rains.) Восени часто ___." |
| `weather/act-2/3` | U18/U39/U40/U41 | sentence: "(Warm.) Навесні ___ і красиво." |
| `weather/act-3/3` | U39/U40/U41 | sentence: "(Sunny.) — Чому ти любиш літо? — Тому що влітку ___." |
| `my-day/act-2/0` | U11/U12/U33/U34 | sentence: "(First.) ___ я прокидаюся і вмиваюся." |
| `my-day/act-2/1` | U11/U12/U33/U34 | sentence: "(I have breakfast.) Після того я ___." |
| `my-day/act-2/2` | U11/U12/U33/U34 | sentence: "(I work.) Вдень я ___ в офісі." |
| `my-day/act-2/3` | U11/U12/U33/U34 | sentence: "(I have lunch.) О першій годині я ___." |
| `my-day/act-2/4` | U11/U12/U33/U34 | sentence: "(Then.) ___ я читаю книгу або дивлюся фільм." |
| `my-day/act-2/5` | U11/U12/U33/U34 | sentence: "(Finally.) ___ я лягаю спати о дванадцятій." |
| `my-day/act-3/0` | U34/U36/U37/U38 | sentence: "(In the morning.) Я п'ю каву ___." |
| `my-day/act-3/1` | U34/U36/U37/U38 | sentence: "(In the evening.) Ми вечеряємо ___." |
| `my-day/act-3/2` | U34/U36/U37/U38 | sentence: "(09:00-17:00.) Вона працює з дев'ятої до п'ятої ___." |
| `my-day/act-3/3` | U34/U36/U37/U38 | sentence: "(After lunch.) Вони гуляють у парку ___." |
| `my-day/act-4/0` | U07/U27/U28 | options: ["беру душ", "бере душ"]; explanation: "With я, use беру. Бере is the third-person form." |
| `my-day/act-4/1` | U07/U48 | options: ["п'ю ліки", "п'є ліки"]; explanation: "With я, use п'ю. П'є goes with він or вона." |
| `my-day/act-4/7` | U08/U20/U21 | options: ["прокинувся", "прокинулася"]; explanation: "Встав is masculine past, so pair it with прокинувся. Прокинулася is feminine." |
| `free-time/act-2/0` | U42/U43/U44 | sentence: "(Never.) Я ___ працюю у неділю." |
| `free-time/act-2/1` | U17 | options: ["на тиждень", "на тижня", "на тижні"]; explanation: "Двічі на тиждень means twice a week. На тиждень names the frequency period." |
| `free-time/act-2/2` | U22/U30/U31/U51 | options: ["Ходімо", "Ходжу", "Ходиш"]; explanation: "Ходімо invites us to go together. Ходжу and ходиш describe who goes." |
| `free-time/act-2/3` | U42/U43/U44 | sentence: "(Often.) Я люблю спорт, тому ___ граю у баскетбол." |
| `free-time/act-2/4` | U42/U43/U44 | sentence: "(Rarely.) Я не маю часу, тому ___ читаю книги." |
| `free-time/act-2/5` | U29/U52 | options: ["у вихідні", "вихідні", "у вихідних"]; explanation: "У вихідні means on weekends. Here у takes the plural accusative вихідні." |
| `free-time/act-3/1` | U01/U49 | options: ["у", "на", "з"] |
| `free-time/act-3/3` | U01/U49 | options: ["в", "на", "із"] |
| `checkpoint-time-nature/act-1/3` | U18 | options: ["іде дощ", "іде дощова", "ідуть дощ"] |
| `checkpoint-time-nature/act-1/4` | U39/U40 | sentence: "(Cold.) Взимку дуже ___." |
| `checkpoint-time-nature/act-1/5` | U36 | options: ["ранку", "рано", "ранок"] |
| `checkpoint-time-nature/act-3/0` | U11/U12/U33/U34/U36/U37/U38/U39/U40 | sentence: "(First.) ___ я прокидаюся і снідаю." |
| `checkpoint-time-nature/act-3/1` | U11/U12/U33/U34/U36/U37/U38/U39/U40 | sentence: "(Then.) ___ я йду на роботу." |
| `checkpoint-time-nature/act-3/3` | U11/U12/U33/U34/U36/U37/U38/U39/U40 | sentence: "(After lunch.) ___ я гуляю в парку." |
| `checkpoint-time-nature/act-3/4` | U11/U12/U33/U34/U36/U37/U38/U39/U40 | sentence: "(Warm.) Я гуляю, тому що сьогодні ___ і сонячно." |
| `checkpoint-time-nature/act-3/5` | U11/U12/U33/U34/U36/U37/U38/U39/U40 | sentence: "(In the evening.) ___ я вечеряю і слухаю музику." |
| `checkpoint-time-nature/act-3/6` | U11/U12/U33/U34/U36/U37/U38/U39/U40 | sentence: "(Finally.) ___ я лягаю спати о дванадцятій." |
| `euphony/act-1/5` | U01 | prompt: "Максим ___ банку."; explanation: "Максим ends in a consonant; before the consonant б, у банку avoids a consonant cluster." |
| `euphony/act-1/6` | U01 | options: [{"text": "У", "correct": true}, {"text": "З", "correct": false}, {"text": "Й", "correct": false}] |
| `euphony/act-3/0` | U03/U47 | options: ["зі", "з", "на"] |

## Validation and batch sizing

- Structural scanner: `scripts/audit/scan_activity_errors.py --track a1-v1`, 55/55 files, zero findings, exit 0 before and after source repairs.
- Existing affected suite: `pytest -n 2 tests/test_scan_activity_errors.py tests/test_a1_activity_schema_parser_drift.py tests/test_yaml_activities_a1_payload.py tests/test_activity_renderer.py tests/test_generate_mdx.py tests/test_generate_mdx_parsers.py tests/test_generate_mdx_unit_map.py tests/test_generate_mdx_v7_resources_vocab.py tests/test_curriculum_manifest_canary.py`: 329 passed in 11.26 seconds. No new test case was added.
- The existing ActivityParser, `yaml_activities_to_jsx` and `dump_json_for_jsx` regenerate only the 74 repaired tracked page item objects. Bytes outside those objects remain unchanged. Existing unaccented page conventions are retained. The integrity manifest updates the corresponding 11 YAML and 11 MDX hashes.
- Source/page matching accounts for pre-existing omitted fill-in feedback fields. Only repaired objects receive the current serializer result. This does not certify unrelated source/page equality.
- Chromium used the 74 changed tracked MDX payloads with the existing FillInQuestion and QuizQuestion components: 74 keys accepted, 74 wrong options rejected, zero browser errors. The runtime was copied into this worktree after both lockfiles were verified identical.
- Ruff passed for the scanner, parser and converter modules.
- Independent Gemini via AGY and Opus 5.5 via Claude Code review, CI and merge receipts are recorded on the PR at its exact pushed head. This report records the author pass and does not claim independent approval or deployment.

The full-section inventory was recorded at 2026-10-28T19:27:21.754745+00:00. The author report was prepared at 2026-10-28T19:44:55.042781+00:00. This interval includes source verification, diagnosis, repairs and local checks; it is not pure model throughput. There are 288 checked items, fewer than the preceding batch, and the item types and usage complexity differ. Review and CI time are reported separately in the delivery receipt. The CTO should size remaining batches by complete section/item censuses, not module count alone.

Residual owner: CTO curriculum coordinator, #8893. The remaining modules, unchecked activity types, broader independent evaluation and production delivery are outside this slice.
