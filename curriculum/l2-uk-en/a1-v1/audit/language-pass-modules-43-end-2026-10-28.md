# A1-v1 language pass, manifest modules 43 through the end

Refs #8893. Source snapshot: `7e3ee13f582798f409ea85df9ce2d827b4ef2d7a`.

This is one bounded Method step 2 slice. It checks all 234 fill-in and quiz items in inline/root and workbook sections of manifest modules 43-55, excluding only `a1-finale/act-1/0`, already covered by #11911. There are 182 checked-clean items and 52 confirmed ambiguous items, all repaired. No wrong key was confirmed. Every original key, learning target and activity type is retained.

The order comes from `levels.a1-v1.modules` in `curriculum/l2-uk-en/curriculum.yaml`, using the same arc-order fallback as #11911. This batch covers the rest of the communication arc and the final past/future/graduation arc. The workbook denominator is 77 items; the inline denominator is 157.

| Position | Module | Items checked | Clean | Defects fixed |
| --- | --- | ---: | ---: | ---: |
| 43 | `please-do-this` | 22 | 20 | 2 |
| 44 | `linking-ideas` | 26 | 22 | 4 |
| 45 | `when-and-where` | 30 | 22 | 8 |
| 46 | `holidays` | 23 | 23 | 0 |
| 47 | `checkpoint-communication` | 23 | 11 | 12 |
| 48 | `what-happened` | 10 | 10 | 0 |
| 49 | `yesterday` | 14 | 9 | 5 |
| 50 | `what-will-happen` | 15 | 15 | 0 |
| 51 | `my-plans` | 13 | 8 | 5 |
| 52 | `my-story` | 11 | 3 | 8 |
| 53 | `health` | 14 | 13 | 1 |
| 54 | `emergencies` | 17 | 17 | 0 |
| 55 | `a1-finale` | 16 | 9 | 7 |

## What was checked

Item indices and anonymous `workbook[n]` indices are zero-based. An explicit activity id is used where present. Each verdict checks the key and every displayed alternative against the instruction and stem. The original stem and unchanged key identify each item. C means checked-clean for wrong keys and second defensible answers within the stated task; D means a confirmed ambiguity repaired in this slice. It does not certify every linguistic claim in a module.

The structural scanner checked 55/55 files before and after repair, with zero findings and exit 0. It therefore added no flagged items of other activity types. This is not a substitute for issue Method step 1's broader semantic and VESUM rules.

Not checked: modules 1-42, which have separate owners/reports; `a1-finale/act-1/0`; other activity types without a structural flag; lesson prose, plans, vocabulary and resources; historical source/page drift outside the repaired item objects; audio, teacher usage and deployed-site behavior. This slice leaves #8893 open with the CTO curriculum coordinator. No deployment or publication is included.

## Sources evidence and its limits

The `sources` MCP supplied the evidence on 2026-10-28. VESUM establishes forms and morphology, ULIF establishes applicable stress readings, and `check_text` screens text. These tools do not themselves judge answer ambiguity. The verdicts below are the author's linguistic inferences from the evidence and each task. Usage-sensitive verdicts additionally cite dictionary or grammar locators.

For each module section, `verify_words` received distinct Ukrainian tokens from instructions and every item field/option, lowercased and with acute accents removed. `verify_stresses` received the original polysyllabic tokens. `check_text` received all item ids and accent-free full item text, with `vesum` and `ua_gec`; stress was checked separately. All 234 items are covered by 25 three-call section batches. U44 rechecks the capitalization-dependent proper names and tokenization fragments as complete words, 32/32 found. The remaining `ли` is an English-ending tokenization fragment in an explanation, not Ukrainian target vocabulary. Diagnostics include intentional wrong options and case-sensitive tokens; no diagnostic alone caused a repair.

The requested СУМ-20 lookups returned no ingested entries. Those misses are recorded, not treated as evidence. The modern ВТС fallback supplies the relevant meanings. U39 supplies the grammar passage supporting narrative present and scheduled future uses; U31 establishes the multiple time meanings of зараз. U41 establishes polite singular ви. Unverified suspicions from broad search results were not counted as defects. The holiday checks use the dictionary's conventional Christmas/New Year song distinction, not its obsolete calendar dates.

The companion [machine-readable Sources evidence](language-pass-modules-43-end-evidence.jsonl) preserves query arguments, reply digests, VESUM analyses, ULIF source rows and text diagnostics. Usage locators preserve queries, modern-source URLs, source summaries and textbook chunk identifiers. Receipt and reply hashes use SHA-256 of UTF-8 JSON with sorted keys and compact separators.

POST1 and POST2 screen all 234 final items in batches of 150 and 84. These diagnostic screens include intentionally wrong alternatives and are not a claim of zero linguistic diagnostics.

### Module batch locators

| Locator | Section | VESUM found/queried | Stress rows | Text items | Evidence id / receipt SHA-256 |
| --- | --- | ---: | ---: | ---: | --- |
| M43 | please-do-this, inline | 48/52 | 53 | 16 | `VESUM reply`; `8f19a3377380e17dd61fa5198f27af3b8be44429158b681f91fa634d6ecda7e1` |
| M43 | please-do-this, workbook | 21/26 | 20 | 6 | `VESUM reply`; `2051c074b5b2feb26ca1e35cebaefc71f9e4b12c966fab3b28057f37908f100b` |
| M44 | linking-ideas, inline | 57/58 | 40 | 20 | `VESUM reply`; `1c0e870bb8bd6f957531bab5d8589fa1f5680f9b1a0370f2fe8be6c946eb272f` |
| M44 | linking-ideas, workbook | 25/26 | 17 | 6 | `VESUM reply`; `b986146632ef6dea79dd202ddb0cac4d9969540074085be9aa3c5ea1433bdabd` |
| M45 | when-and-where, inline | 30/30 | 24 | 24 | `VESUM reply`; `03b7a646b8f903b0af8a9f988f841f633b994e1ae0d5f92616f18531cc50884d` |
| M45 | when-and-where, workbook | 22/22 | 15 | 6 | `VESUM reply`; `6bfd725a4d8ffeeaea1ecdcce68c1ecf566ba34df3cde529723cb19b251ee7e9` |
| M46 | holidays, inline | 50/50 | 45 | 14 | `VESUM reply`; `59165d84e7f39e1aea924ec11918a4d7cf86610a053aa92a476562c0fb69d26c` |
| M46 | holidays, workbook | 52/53 | 50 | 9 | `VESUM reply`; `31fcb5637559cf74f2b9369dafad8dab849b02a6bd229409f4ecf0aae70ff26a` |
| M47 | checkpoint-communication, inline | 66/74 | 59 | 17 | `VESUM reply`; `e4404eec76ef91d6759a3e952f85cfde874e82381b63951dcb986b19bb52c813` |
| M47 | checkpoint-communication, workbook | 32/36 | 24 | 6 | `VESUM reply`; `c460ca1efc11cb5ddcc053f37047ae0c6cc436da97f489453516c43006dd1105` |
| M48 | what-happened, inline | 35/39 | 31 | 10 | `VESUM reply`; `4c84c72e2544da57f358228cca9c19e909d3471364e26a49e5de735041247284` |
| M49 | yesterday, inline | 31/33 | 28 | 9 | `VESUM reply`; `50e8cd3ecc039cb3bfdb94727aa91c0936257a521749a45356331f416f5b5345` |
| M49 | yesterday, workbook | 34/36 | 31 | 5 | `VESUM reply`; `0803f7e0ff888b5d447b99c9488dd314092a848872feb073721a8687335647d9` |
| M50 | what-will-happen, inline | 31/31 | 27 | 10 | `VESUM reply`; `92a186a07eb3a6b845189d50007fb8a558452cf70494d2e31e5b332121fc74e0` |
| M50 | what-will-happen, workbook | 30/30 | 27 | 5 | `VESUM reply`; `906a4777e1bcf1d766d6371f53ccdf46f1a279ed84613f96843fdb55aaa35454` |
| M51 | my-plans, inline | 46/46 | 38 | 9 | `VESUM reply`; `414aa123c25daf3c4314acdbbb8da9a0bfa12f4a3a1677bd689ffb1c98dc5924` |
| M51 | my-plans, workbook | 30/30 | 21 | 4 | `VESUM reply`; `bf079de27d2bf1c26f017127633e1060314138a556d71e6359b2b331a1b45d91` |
| M52 | my-story, inline | 17/18 | 14 | 4 | `VESUM reply`; `a738a76283dad99ab219cf4122892ac75538a04d9ab5044c4976b6ba0d428fb0` |
| M52 | my-story, workbook | 31/34 | 29 | 7 | `VESUM reply`; `19b3860ecd4cbc2b6cfc0b7b807616d55c707949a10b517e68cc60e5e6d70604` |
| M53 | health, inline | 23/23 | 20 | 7 | `VESUM reply`; `45f52142b87cf2551f3195110c1b1ab13d8b42bf52889a1538fca9a428c98622` |
| M53 | health, workbook | 29/29 | 26 | 7 | `VESUM reply`; `8856fe196f5565f1923d75ea00e676b0d9b405f9268d2ad53d541e1d748d8b77` |
| M54 | emergencies, inline | 35/37 | 30 | 10 | `VESUM reply`; `bea275e28ad3c420de4d5fce4a293045a97e5e1500b54b18fad5baada15352f7` |
| M54 | emergencies, workbook | 39/40 | 28 | 7 | `VESUM reply`; `ad484f245662a8877581a428435f4afaa8b0c4a2604e7d9bb1f67a4a63bd437c` |
| M55 | a1-finale, inline | 45/47 | 39 | 7 | `VESUM reply`; `e47d3df7e532d4a874adbfa821de801498484a9402020801f81a10c33ad49172` |
| M55 | a1-finale, workbook | 39/43 | 33 | 9 | `VESUM reply`; `66fe9daae05ad69e6aa4b883f6fde3fc1040d66b764085536742ce7653fb0055` |

### Usage locators

| Locator | Tool and query | Evidence and limit |
| --- | --- | --- |
| U1 | `query_sum20` {"word": "але"} | No official offline СУМ-20 entry is currently ingested for 'але'. This tool does not make a live request or use a fallback source. |
| U2 | `query_sum20` {"word": "а"} | No official offline СУМ-20 entry is currently ingested for 'а'. This tool does not make a live request or use a fallback source. |
| U3 | `query_sum20` {"word": "і"} | No official offline СУМ-20 entry is currently ingested for 'і'. This tool does not make a live request or use a fallback source. |
| U4 | `query_sum20` {"word": "бо"} | No official offline СУМ-20 entry is currently ingested for 'бо'. This tool does not make a live request or use a fallback source. |
| U5 | `query_sum20` {"word": "де"} | No official offline СУМ-20 entry is currently ingested for 'де'. This tool does not make a live request or use a fallback source. |
| U6 | `query_sum20` {"word": "коли"} | No official offline СУМ-20 entry is currently ingested for 'коли'. This tool does not make a live request or use a fallback source. |
| U7 | `query_sum20` {"word": "або"} | No official offline СУМ-20 entry is currently ingested for 'або'. This tool does not make a live request or use a fallback source. |
| U8 | `query_sum20` {"word": "зараз"} | No official offline СУМ-20 entry is currently ingested for 'зараз'. This tool does not make a live request or use a fallback source. |
| U9 | `query_sum20` {"word": "далі"} | No official offline СУМ-20 entry is currently ingested for 'далі'. This tool does not make a live request or use a fallback source. |
| U10 | `query_sum20` {"word": "ввечері"} | No official offline СУМ-20 entry is currently ingested for 'ввечері'. This tool does not make a live request or use a fallback source. |
| U11 | `query_sum20` {"word": "зранку"} | No official offline СУМ-20 entry is currently ingested for 'зранку'. This tool does not make a live request or use a fallback source. |
| U12 | `query_sum20` {"word": "нарешті"} | No official offline СУМ-20 entry is currently ingested for 'нарешті'. This tool does not make a live request or use a fallback source. |
| U13 | `query_slovnyk_me` {"word": "чи", "dict": "vts"} | VTS чи: alternative/disjunctive connector and interrogative uses. |
| U14 | `query_slovnyk_me` {"word": "що", "dict": "vts"} | VTS що: interrogative and relative pronoun; conjunction introducing a complement. |
| U15 | `query_slovnyk_me` {"word": "та", "dict": "vts"} | VTS та: additive і and adversative але meanings. |
| U16 | `query_slovnyk_me` {"word": "потім", "dict": "vts"} | VTS потім: after something in temporal sequence; later. |
| U17 | `search_text` {"query": "теперішній час майбутнього", "subject": "ukrmova", "limit": 3} | Textbook retrieval on tenses; the decisive tense-synonymy passage is retained in U39. |
| U18 | `search_text` {"query": "наказовий спосіб інфінітив", "subject": "ukrmova", "limit": 3} | Grammar retrieval distinguishes imperative forms and infinitives; this is not itself evidence for the acceptability of an infinitive command. |
| U19 | `query_sum20` {"word": "колядка"} | No official offline СУМ-20 entry is currently ingested for 'колядка'. This tool does not make a live request or use a fallback source. |
| U20 | `query_slovnyk_me` {"word": "щедрівка", "dict": "vts"} | VTS щедрівка: traditional New Year ritual song. The obsolete calendar date in the definition is not taught or verified by this audit. |
| U21 | `query_sum20` {"word": "боліти"} | No official offline СУМ-20 entry is currently ingested for 'боліти'. This tool does not make a live request or use a fallback source. |
| U22 | `query_pravopys` {"topic": "кома складнопідрядні"} | Official Pravopys 2019 §158, pp.203-226: commas in simple and complex sentences. |
| U23 | `query_pravopys` {"topic": "кличний відмінок"} | Official Pravopys 2019 §74, p.109: vocative endings, including Маріє. |
| U24 | `query_slovnyk_me` {"word": "але", "dict": "vts"} | VTS але: adversative conjunction. |
| U25 | `query_slovnyk_me` {"word": "а", "dict": "vts"} | VTS а: contrast, comparison of simultaneous actions and additive uses. |
| U26 | `query_slovnyk_me` {"word": "і", "dict": "vts"} | VTS і: additive conjunction; also contrastive/adversative uses. |
| U27 | `query_slovnyk_me` {"word": "бо", "dict": "vts"} | VTS бо: conjunction introducing a cause, synonymous with тому що. |
| U28 | `query_slovnyk_me` {"word": "де", "dict": "vts"} | VTS де: question/relative adverb of place. |
| U29 | `query_slovnyk_me` {"word": "коли", "dict": "vts"} | VTS коли: time question, relative time and conditional uses. |
| U30 | `query_slovnyk_me` {"word": "або", "dict": "vts"} | VTS або: disjunctive alternative. |
| U31 | `query_slovnyk_me` {"word": "зараз", "dict": "vts"} | VTS зараз: immediately, very soon, now, and just now for a recently completed event. |
| U32 | `query_slovnyk_me` {"word": "далі", "dict": "vts"} | VTS далі: after this/then; continuing an action. It is not restricted to future time. |
| U33 | `query_slovnyk_me` {"word": "ввечері", "dict": "vts"} | VTS ввечері: in the evening, with no inherent tense. |
| U34 | `query_slovnyk_me` {"word": "зранку", "dict": "vts"} | VTS зранку: in the morning/from morning, with no inherent tense. |
| U35 | `query_slovnyk_me` {"word": "нарешті", "dict": "vts"} | VTS нарешті: at the end, finally. |
| U36 | `query_slovnyk_me` {"word": "колядка", "dict": "vts"} | VTS колядка: traditional Christmas ritual song. |
| U37 | `query_slovnyk_me` {"word": "боліти", "dict": "vts"} | VTS боліти: a body part causes physical pain; possessive/body-part readings. |
| U38 | `query_slovnyk_me` {"word": "ім'я", "dict": "vts"} | No entry found for 'ім'я' in slovnyk.me/vts (Великий тлумачний словник сучасної української мови). |
| U39 | `search_text` {"query": "\"майбутнього\" \"теперішнього\"", "source_file": "uni-ukrmova-morphology-volkova-maslo-2012", "limit": 6} | Volkova and Maslo, 2012, morphology_s0123, p.124: present forms can narrate past events or express scheduled/certain future actions. morphology_s0121, p.122: compound future is a personal form of бути plus infinitive. |
| U40 | `search_text` {"query": "\"інфінітив\" \"наказ\"", "source_file": "uni-ukrmova-morphology-volkova-maslo-2012", "limit": 4} | Grammar retrieval on infinitives and imperative; no decisive example of an infinitive command was returned. |
| U41 | `query_slovnyk_me` {"word": "ви", "dict": "vts"} | VTS ви: addresses two or more persons, or one person politely. |
| U42 | `query_slovnyk_me` {"word": "ім’я", "dict": "vts"} | No entry found for 'ім’я' in slovnyk.me/vts (Великий тлумачний словник сучасної української мови). |
| U43 | `query_slovnyk_me` {"word": "здоров'я", "dict": "vts"} | No entry found for 'здоров'я' in slovnyk.me/vts (Великий тлумачний словник сучасної української мови). |
| U44 | `verify_words` {"words": ["Олено", "Іване", "Тарасе", "Маріє", "Оксано", "Олена", "Карпати", "Марія", "Марію", "Тарас", "Тарасу", "Анна", "Торонто", "Львові", "Одесі", "Данило", "Шевченка", "Сара", "Хрещатику", "Хрещатик", "Адам", "Канади", "книгу", "народилася", "народжуся", "народжуюся", "снідав", "буду", "ходили", "ходимо", "після", "цього"]} | VESUM 32/32 forms found, including proper names in original capitalization and the birth, breakfast and cinema alternatives. |
| U45 | `search_text` {"query": "\"Сидіти\" \"Мовчати\"", "subject": "ukrmova", "limit": 3} | Search results do not establish the suspected infinitive-command reading; no defect is based on this query. |
| U46 | `query_grac` {"query": "Читати!", "mode": "concordance", "limit": 3} | No GRAC concordance returned for Читати!; this is not evidence that the construction is invalid. |
| U47 | `query_slovnyk_me` {"word": "тому", "dict": "vts"} | VTS тому, conjunction sense 3: тому що introduces a subordinate clause of cause. |
| U48 | `search_text` {"query": "\"інфінітив\" \"спонукальних\"", "subject": "ukrmova", "limit": 5} | Textbook retrieval did not establish the suspected infinitive-command reading; no defect is based on this query. |
| U49 | `verify_words` {"words": ["щоб", "тому", "що", "Учора"]} | VESUM verifies the replacement connective and final cue tokens. |
| U50 | `verify_stresses` {"words": ["Учора", "тому"]} | Stress oracle checks the final cue and replacement compound-connective component. |
| U51 | `query_slovnyk_me` {"word": "вечірка", "dict": "vts"} | VTS вечірка: an evening gathering or party. |
| U52 | `query_slovnyk_me` {"word": "температура", "dict": "vts"} | VTS температура: body temperature, also its elevation in illness. |
| U53 | `get_chunk_context` {"chunk_id": "6-klas-ukrmova-golub-2023_s0180"} | Golub, grade 6, p.177: ти addresses well-known peers or younger people; ви addresses unfamiliar or older people, with plural predicate agreement. |
| U54 | `get_chunk_context` {"chunk_id": "8-klas-ukrmova-avramenko-2025_s0179"} | Avramenko, grade 8, p.135: conversational address etiquette, including the inappropriate familiar address to an unknown person. |

## please-do-this

| Item | Section | Original stem | Key | Verdict | Evidence and reason |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | Олено, ___ текст, будь ласка. | читай | C | M43; U41; U44. The command task and stated address/register select the keyed imperative; other displayed forms fail that task. |
| `act-1/1` | inline | Пане Іване, ___ текст, будь ласка. | читайте | C | M43; U41; U44. The command task and stated address/register select the keyed imperative; other displayed forms fail that task. |
| `act-1/2` | inline | Тарасе, ___ речення. | пиши | C | M43; U41; U44. The command task and stated address/register select the keyed imperative; other displayed forms fail that task. |
| `act-1/3` | inline | Студенти, ___ речення. | пишіть | C | M43; U41; U44. The command task and stated address/register select the keyed imperative; other displayed forms fail that task. |
| `act-1/4` | inline | Маріє, ___ мене, будь ласка. | слухай | C | M43; U41; U44. The command task and stated address/register select the keyed imperative; other displayed forms fail that task. |
| `act-1/5` | inline | Друзі, ___ мене. | слухайте | C | M43; U41; U44. The command task and stated address/register select the keyed imperative; other displayed forms fail that task. |
| `act-1/6` | inline | ___ меню, будь ласка. | Дайте | C | M43; U41; U44. The command task and stated address/register select the keyed imperative; other displayed forms fail that task. |
| `act-1/7` | inline | ___, що ти хочеш. | Скажи | C | M43; U41; U44. The command task and stated address/register select the keyed imperative; other displayed forms fail that task. |
| `act-2/0` | inline | You ask one friend to read. | Читай, будь ласка. | C | M43; U41; U44. U53; U54; please-do-this/module.md. The activity explicitly tests social register: the friend takes ти, the teacher/server takes polite ви. U41 alone did not establish a competing appropriate answer; the three extra hints were restored after independent review. |
| `act-2/1` | inline | You ask a teacher to read. | Читайте, будь ласка. | C | M43; U41; U44. U53; U54; please-do-this/module.md. The activity explicitly tests social register: the friend takes ти, the teacher/server takes polite ви. U41 alone did not establish a competing appropriate answer; the three extra hints were restored after independent review. |
| `act-2/2` | inline | You ask a server for the bill. | Дайте рахунок, будь ласка. | C | M43; U41; U44. U53; U54; please-do-this/module.md. The activity explicitly tests social register: the friend takes ти, the teacher/server takes polite ви. U41 alone did not establish a competing appropriate answer; the three extra hints were restored after independent review. |
| `act-2/3` | inline | You ask one close friend for the menu. | Дай меню, будь ласка. | C | M43; U41; U44. The command task and stated address/register select the keyed imperative; other displayed forms fail that task. |
| `act-2/4` | inline | A teacher gives a class instruction. | Пишіть речення. | C | M43; U41; U44. The command task and stated address/register select the keyed imperative; other displayed forms fail that task. |
| `act-2/5` | inline | A friend asks you to look. | Подивись! | C | M43; U41; U44. The command task and stated address/register select the keyed imperative; other displayed forms fail that task. |
| `act-2/6` | inline | You politely ask someone to say it again. | Скажіть ще раз, будь ласка. | C | M43; U41; U44. The command task and stated address/register select the keyed imperative; other displayed forms fail that task. |
| `act-2/7` | inline | A coach asks the team to open the door. | Відкрийте двері. | C | M43; U41; U44. The command task and stated address/register select the keyed imperative; other displayed forms fail that task. |
| `workbook[0]/0` | workbook | Олено, ___ книжку! | дай | D | M43; U41; U44. A first-name vocative does not distinguish familiar singular from polite plural; both displayed commands are attested. |
| `workbook[0]/1` | workbook | Пане Іване, ___ книжку! | дайте | C | M43; U41; U44. The command task and stated address/register select the keyed imperative; other displayed forms fail that task. |
| `workbook[0]/2` | workbook | Тарасе, ___ в кафе. | іди | D | M43; U41; U44. A first-name vocative does not distinguish familiar singular from polite plural; both displayed commands are attested. |
| `workbook[0]/3` | workbook | Друзі, ___ в кафе. | ідіть | C | M43; U41; U44. The command task and stated address/register select the keyed imperative; other displayed forms fail that task. |
| `workbook[0]/4` | workbook | Маріє, ___, що ти хочеш. | скажи | C | M43; U41; U44. The command task and stated address/register select the keyed imperative; other displayed forms fail that task. |
| `workbook[0]/5` | workbook | Пані Оксано, ___, будь ласка. | скажіть | C | M43; U41; U44. The command task and stated address/register select the keyed imperative; other displayed forms fail that task. |

## linking-ideas

| Item | Section | Original stem | Key | Verdict | Evidence and reason |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | Я читаю ___ пишу. | і | C | M44; U13-U16; U24-U30; U47. The keyed connector fits the displayed syntax, punctuation and stated relation; the remaining options do not complete that task. |
| `act-1/1` | inline | Я хочу каву, ___ ти? | а | D | M44; U25; U26; U27. І can add the second speaker in a question, alongside the keyed а. The causal replacement cannot join the bare ти here. |
| `act-1/2` | inline | Я хочу, ___ не можу. | але | D | M44; U24; U26; U14. І can connect two contrasting facts, as well as але. Що cannot complement хочу with the finite не можу in this construction. |
| `act-1/3` | inline | Я не йду, ___ я хворий. | бо | C | M44; U13-U16; U24-U30; U47. The keyed connector fits the displayed syntax, punctuation and stated relation; the remaining options do not complete that task. |
| `act-1/4` | inline | Мама ___ тато вдома. | й | C | M44; U13-U16; U24-U30; U47. The keyed connector fits the displayed syntax, punctuation and stated relation; the remaining options do not complete that task. |
| `act-1/5` | inline | Хліб ___ масло на столі. | та | C | M44; U13-U16; U24-U30; U47. The keyed connector fits the displayed syntax, punctuation and stated relation; the remaining options do not complete that task. |
| `act-1/6` | inline | Кава ___ чай? | або | C | M44; U13-U16; U24-U30; U47. The keyed connector fits the displayed syntax, punctuation and stated relation; the remaining options do not complete that task. |
| `act-1/7` | inline | Ви студент ___ лікар? | чи | D | M44; U13; U15. Та can ask whether the person has both professions; чи asks for one alternative. |
| `act-2/0` | inline | Я люблю каву і чай. | adds one more thing | C | M44; U13-U16; U24-U30; U47. The question asks for the displayed connector's role, not every possible interpretation of the whole event. |
| `act-2/1` | inline | Я працюю, а брат навчається. | compares two facts | C | M44; U13-U16; U24-U30; U47. The question asks for the displayed connector's role, not every possible interpretation of the whole event. |
| `act-2/2` | inline | Я хочу, але не можу. | shows contrast | C | M44; U13-U16; U24-U30; U47. The question asks for the displayed connector's role, not every possible interpretation of the whole event. |
| `act-2/3` | inline | Я вдома, бо я хворий. | gives a reason | C | M44; U13-U16; U24-U30; U47. The question asks for the displayed connector's role, not every possible interpretation of the whole event. |
| `act-2/4` | inline | Ти хочеш каву чи чай? | offers a choice in a question | C | M44; U13-U16; U24-U30; U47. The question asks for the displayed connector's role, not every possible interpretation of the whole event. |
| `act-2/5` | inline | Ми вдома, тому що йде дощ. | gives a reason | C | M44; U13-U16; U24-U30; U47. The question asks for the displayed connector's role, not every possible interpretation of the whole event. |
| `act-3/0` | inline | Я вчу українську, ___ люблю Україну. | бо | C | M44; U13-U16; U24-U30; U47. The instruction explicitly requests a reason using бо or тому що; the alternatives do not meet that restriction. |
| `act-3/1` | inline | Ми не гуляємо, ___ йде дощ. | тому що | C | M44; U13-U16; U24-U30; U47. The instruction explicitly requests a reason using бо or тому що; the alternatives do not meet that restriction. |
| `act-3/2` | inline | Олена читає, ___ має іспит. | бо | C | M44; U13-U16; U24-U30; U47. The instruction explicitly requests a reason using бо or тому що; the alternatives do not meet that restriction. |
| `act-3/3` | inline | Я вдома, ___ я хворий. | тому що | C | M44; U13-U16; U24-U30; U47. The instruction explicitly requests a reason using бо or тому що; the alternatives do not meet that restriction. |
| `act-3/4` | inline | Марко купує воду, ___ хоче пити. | бо | C | M44; U13-U16; U24-U30; U47. The instruction explicitly requests a reason using бо or тому що; the alternatives do not meet that restriction. |
| `act-3/5` | inline | Вони чекають, ___ автобус спізнюється. | тому що | C | M44; U13-U16; U24-U30; U47. The instruction explicitly requests a reason using бо or тому що; the alternatives do not meet that restriction. |
| `workbook[1]/0` | workbook | Карпати ___ море? | чи | C | M44; U13-U16; U24-U30; U47. The keyed connector fits the displayed syntax, punctuation and stated relation; the remaining options do not complete that task. |
| `workbook[1]/1` | workbook | Гори гарні, ___ далеко. | але | D | M44; U24; U26; U14. І has an attested contrastive use, leaving the contrast reading defensible. Що does not coordinate these predicates. |
| `workbook[1]/2` | workbook | Море тепле, ___ літо. | бо | C | M44; U13-U16; U24-U30; U47. The keyed connector fits the displayed syntax, punctuation and stated relation; the remaining options do not complete that task. |
| `workbook[1]/3` | workbook | Я хочу в гори, ___ ти? | а | C | M44; U13-U16; U24-U30; U47. The keyed connector fits the displayed syntax, punctuation and stated relation; the remaining options do not complete that task. |
| `workbook[1]/4` | workbook | Карпати ___ море - дві хороші ідеї. | і | C | M44; U13-U16; U24-U30; U47. The keyed connector fits the displayed syntax, punctuation and stated relation; the remaining options do not complete that task. |
| `workbook[1]/5` | workbook | Поїдемо в Карпати, ___ там дешевше. | бо | C | M44; U13-U16; U24-U30; U47. The keyed connector fits the displayed syntax, punctuation and stated relation; the remaining options do not complete that task. |

## when-and-where

| Item | Section | Original stem | Key | Verdict | Evidence and reason |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | Я знаю, ___ це кафе. | що | D | M45; U28; U29; U14. Що asserts identification; де asks about location. |
| `act-1/1` | inline | Я не знаю, ___ парк. | де | C | M45; U14; U28; U29; U22. The key forms the requested complete frame; the alternatives leave an incomplete or incompatible clause. |
| `act-1/2` | inline | Скажи, ___ урок. | коли | D | M45; U28; U29; U14. Both коли and де can introduce a detail about a lesson. |
| `act-1/3` | inline | Вона каже, ___ магазин близько. | що | C | M45; U14; U28; U29; U22. The key forms the requested complete frame; the alternatives leave an incomplete or incompatible clause. |
| `act-1/4` | inline | Я знаю, ___ ти живеш. | де | D | M45; U28; U29; U14. Both де and що form grammatical complements with ти живеш. |
| `act-1/5` | inline | Ти знаєш, ___ зустріч? | коли | D | M45; U28; U29; U14. Both коли and де can ask for a meeting detail. |
| `act-1/6` | inline | Я думаю, ___ це правильно. | що | D | M45; U28; U29; U14. Коли can introduce a time or condition for thinking; що introduces the judgement itself. |
| `act-1/7` | inline | Скажи, ___ нове кафе. | де | C | M45; U14; U28; U29; U22. The key forms the requested complete frame; the alternatives leave an incomplete or incompatible clause. |
| `act-2/0` | inline | Де кафе? | question word | C | M45; U14; U28; U29; U22. The interrogative/embedded clause position selects the keyed role label. |
| `act-2/1` | inline | Я знаю, де кафе. | connector | C | M45; U14; U28; U29; U22. The interrogative/embedded clause position selects the keyed role label. |
| `act-2/2` | inline | Коли урок? | question word | C | M45; U14; U28; U29; U22. The interrogative/embedded clause position selects the keyed role label. |
| `act-2/3` | inline | Скажи, коли урок. | connector | C | M45; U14; U28; U29; U22. The interrogative/embedded clause position selects the keyed role label. |
| `act-2/4` | inline | Що це? | question word | C | M45; U14; U28; U29; U22. The interrogative/embedded clause position selects the keyed role label. |
| `act-2/5` | inline | Я думаю, що це добре. | connector | C | M45; U14; U28; U29; U22. The interrogative/embedded clause position selects the keyed role label. |
| `act-3/0` | inline | ___, що це добре. | Я думаю | C | M45; U14; U28; U29; U22. The key forms the requested complete frame; the alternatives leave an incomplete or incompatible clause. |
| `act-3/1` | inline | ___, де магазин. | Я не знаю | C | M45; U14; U28; U29; U22. The key forms the requested complete frame; the alternatives leave an incomplete or incompatible clause. |
| `act-3/2` | inline | ___, коли зустріч. | Скажи | C | M45; U14; U28; U29; U22. The key forms the requested complete frame; the alternatives leave an incomplete or incompatible clause. |
| `act-3/3` | inline | ___, що урок сьогодні. | Вона каже | C | M45; U14; U28; U29; U22. The key forms the requested complete frame; the alternatives leave an incomplete or incompatible clause. |
| `act-3/4` | inline | ___, де парк. | Ти знаєш | C | M45; U14; U28; U29; U22. The key forms the requested complete frame; the alternatives leave an incomplete or incompatible clause. |
| `act-3/5` | inline | ___, що він тут. | Я знаю | C | M45; U14; U28; U29; U22. The key forms the requested complete frame; the alternatives leave an incomplete or incompatible clause. |
| `act-4/0` | inline | I know where the cafe is. | Я знаю, де кафе. | C | M45; U14; U28; U29; U22. Only the key preserves the English meaning and the required comma before the subordinate clause. |
| `act-4/1` | inline | I think that this is good. | Я думаю, що це добре. | C | M45; U14; U28; U29; U22. Only the key preserves the English meaning and the required comma before the subordinate clause. |
| `act-4/2` | inline | Tell me when the lesson is. | Скажи, коли урок. | C | M45; U14; U28; U29; U22. Only the key preserves the English meaning and the required comma before the subordinate clause. |
| `act-4/3` | inline | She says that the shop is close. | Вона каже, що магазин близько. | C | M45; U14; U28; U29; U22. Only the key preserves the English meaning and the required comma before the subordinate clause. |
| `workbook[1]/0` | workbook | Я знаю, ___ парк. | де | C | M45; U14; U28; U29; U22. The key forms the requested complete frame; the alternatives leave an incomplete or incompatible clause. |
| `workbook[1]/1` | workbook | Скажи, ___ ти біля фонтану. | коли | D | M45; U28; U29; U14. Що can request an assertion while коли requests its time. |
| `workbook[1]/2` | workbook | Я бачу, ___ будинок близько. | що | D | M45; U28; U29; U14. Коли can specify when the speaker sees, while що states what is seen. |
| `workbook[1]/3` | workbook | Ти знаєш, ___ вулиця Садова? | де | C | M45; U14; U28; U29; U22. The key forms the requested complete frame; the alternatives leave an incomplete or incompatible clause. |
| `workbook[1]/4` | workbook | Я думаю, ___ це мій будинок. | що | C | M45; U14; U28; U29; U22. The key forms the requested complete frame; the alternatives leave an incomplete or incompatible clause. |
| `workbook[1]/5` | workbook | Скажи, ___ зустріч у кафе. | коли | D | M45; U28; U29; U14. The original allows a time question, a location question or a request for an assertion. |

## holidays

| Item | Section | Original stem | Key | Verdict | Evidence and reason |
| --- | --- | --- | --- | --- | --- |
| `act-2/0` | inline | Вітаю з ___! | Новим роком | C | M46; U20; U36. The key matches the greeting's case frame or the named holiday's conventional cultural meaning; the other forms/items do not. |
| `act-2/1` | inline | З ___ Христовим! | Різдвом | C | M46; U20; U36. The key matches the greeting's case frame or the named holiday's conventional cultural meaning; the other forms/items do not. |
| `act-2/2` | inline | З ___! | Великоднем | C | M46; U20; U36. The key matches the greeting's case frame or the named holiday's conventional cultural meaning; the other forms/items do not. |
| `act-2/3` | inline | З Днем ___ України! | Незалежності | C | M46; U20; U36. The key matches the greeting's case frame or the named holiday's conventional cultural meaning; the other forms/items do not. |
| `act-3/0` | inline | Ми ___ Різдво вдома. | святкуємо | C | M46; U20; U36. The key matches the greeting's case frame or the named holiday's conventional cultural meaning; the other forms/items do not. |
| `act-3/1` | inline | ___ Різдво ми співаємо колядки. | На | C | M46; U20; U36. The key matches the greeting's case frame or the named holiday's conventional cultural meaning; the other forms/items do not. |
| `act-3/2` | inline | Ми ___ Великдень з родиною. | святкуємо | C | M46; U20; U36. The key matches the greeting's case frame or the named holiday's conventional cultural meaning; the other forms/items do not. |
| `act-3/3` | inline | ___ Великдень ми печемо паски. | На | C | M46; U20; U36. The key matches the greeting's case frame or the named holiday's conventional cultural meaning; the other forms/items do not. |
| `act-3/4` | inline | Я ___ День Незалежності України. | святкую | C | M46; U20; U36. The key matches the greeting's case frame or the named holiday's conventional cultural meaning; the other forms/items do not. |
| `act-3/5` | inline | ___ Новий рік ми даруємо подарунки. | На | C | M46; U20; U36. The key matches the greeting's case frame or the named holiday's conventional cultural meaning; the other forms/items do not. |
| `act-4/0` | inline | Що співають на Різдво? | колядки | C | M46; U20; U36. The key matches the greeting's case frame or the named holiday's conventional cultural meaning; the other forms/items do not. |
| `act-4/1` | inline | Що звучить на Щедрий вечір? | щедрівки | C | M46; U20; U36. The key matches the greeting's case frame or the named holiday's conventional cultural meaning; the other forms/items do not. |
| `act-4/2` | inline | Що печуть на Великдень? | паски | C | M46; U20; U36. The key matches the greeting's case frame or the named holiday's conventional cultural meaning; the other forms/items do not. |
| `act-4/3` | inline | Що часто бачать на День Незалежності України? | синьо-жовті прапори | C | M46; U20; U36. The key matches the greeting's case frame or the named holiday's conventional cultural meaning; the other forms/items do not. |
| `workbook[0]/0` | workbook | Вітаю тебе з ___! Бажаю веселих свят. | Новим роком | C | M46; U20; U36. The key matches the greeting's case frame or the named holiday's conventional cultural meaning; the other forms/items do not. |
| `workbook[0]/1` | workbook | Добрий день, Олено! З ___! Бажаю здоров'я. | Різдвом Христовим | C | M46; U20; U36. The key matches the greeting's case frame or the named holiday's conventional cultural meaning; the other forms/items do not. |
| `workbook[0]/2` | workbook | З ___ Христовим! Бажаю здоров'я. | Різдвом | C | M46; U20; U36. The key matches the greeting's case frame or the named holiday's conventional cultural meaning; the other forms/items do not. |
| `workbook[0]/3` | workbook | З ___! Бажаю добра. | Великоднем | C | M46; U20; U36. The key matches the greeting's case frame or the named holiday's conventional cultural meaning; the other forms/items do not. |
| `workbook[0]/4` | workbook | Двадцять четвертого серпня - День ___ України. | Незалежності | C | M46; U20; U36. The key matches the greeting's case frame or the named holiday's conventional cultural meaning; the other forms/items do not. |
| `workbook[4]/0` | workbook | На Різдво співають ___. | колядки | C | M46; U20; U36. The key matches the greeting's case frame or the named holiday's conventional cultural meaning; the other forms/items do not. |
| `workbook[4]/1` | workbook | На Щедрий вечір звучать ___. | щедрівки | C | M46; U20; U36. The key matches the greeting's case frame or the named holiday's conventional cultural meaning; the other forms/items do not. |
| `workbook[4]/2` | workbook | На Щедрий вечір діти ___. | щедрують | C | M46; U20; U36. The key matches the greeting's case frame or the named holiday's conventional cultural meaning; the other forms/items do not. |
| `workbook[4]/3` | workbook | На Великдень ми ___. | печемо паски | C | M46; U20; U36. The key matches the greeting's case frame or the named holiday's conventional cultural meaning; the other forms/items do not. |

## checkpoint-communication

| Item | Section | Original stem | Key | Verdict | Evidence and reason |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | ___, принеси листівки, будь ласка. | Маріє | C | M47; U14; U23-U30; U41; U47. The keyed vocative, imperative, connector or greeting matches the displayed syntax and task; the other options do not. |
| `act-1/1` | inline | ___, постав стіл біля вікна. | Тарасе | C | M47; U14; U23-U30; U41; U47. The keyed vocative, imperative, connector or greeting matches the displayed syntax and task; the other options do not. |
| `act-1/2` | inline | Олено, ___ привітання. | напиши | C | M47; U14; U23-U30; U41; U47. The keyed vocative, imperative, connector or greeting matches the displayed syntax and task; the other options do not. |
| `act-1/3` | inline | Друже, ___ мені, будь ласка. | допоможи | C | M47; U14; U23-U30; U41; U47. The keyed vocative, imperative, connector or greeting matches the displayed syntax and task; the other options do not. |
| `act-1/4` | inline | Пані Оксано, ___ маркер, будь ласка. | дайте | C | M47; U14; U23-U30; U41; U47. The keyed vocative, imperative, connector or greeting matches the displayed syntax and task; the other options do not. |
| `act-1/5` | inline | Друзі, ___ сюди. | заходьте | C | M47; U14; U23-U30; U41; U47. The keyed vocative, imperative, connector or greeting matches the displayed syntax and task; the other options do not. |
| `act-2/0` | inline | Ми пишемо листівки ___ вітаємо друзів. | і | C | M47; U14; U23-U30; U41; U47. The keyed vocative, imperative, connector or greeting matches the displayed syntax and task; the other options do not. |
| `act-2/1` | inline | Я хочу допомогти, ___ я зайнятий. | але | D | M47; U24; U26. І can link the two complete clauses as an addition or contrast, alongside але. Щоб requires a different subordinate construction. |
| `act-2/2` | inline | Тарас ставить стіл, ___ людей багато. | бо | D | M47; U25; U27. А can contrast the table-setting with the large number of people; бо gives the reason. |
| `act-2/3` | inline | Марія пише, ___ Тарас ставить стіл. | а | D | M47; U25; U29; U30. Коли gives a time and або offers an alternative; both are defensible without the requested comparison. |
| `act-2/4` | inline | Я беру маркер, ___ пишу листівку. | тому що | D | M47; U28; U47. Де can specify a place of writing; тому що gives the reason for taking the marker. |
| `act-3/0` | inline | Я знаю, ___ маркери. | де | C | M47; U14; U23-U30; U41; U47. The keyed vocative, imperative, connector or greeting matches the displayed syntax and task; the other options do not. |
| `act-3/1` | inline | Я думаю, ___ все готово. | що | D | M47; U14; U29. Коли can specify when the speaker thinks; що states the judgement. |
| `act-3/2` | inline | Скажи, ___ зустріч. | коли | D | M47; U28; U29. Коли and де both request a meeting detail. |
| `act-3/3` | inline | Вона знає, ___ стіл. | де | C | M47; U14; U23-U30; U41; U47. The keyed vocative, imperative, connector or greeting matches the displayed syntax and task; the other options do not. |
| `act-3/4` | inline | Я не знаю, ___ писати. | що | D | M47; U14; U28; U29. Що, де and коли each form a grammatical indirect question before писати. |
| `act-3/5` | inline | Скажіть, ___ ви вільні. | коли | D | M47; U14; U29. Що requests an assertion and коли requests its time. |
| `workbook[4]/0` | workbook | Олено, ___ листівки, будь ласка. | принеси | C | M47; U14; U23-U30; U41; U47. The keyed vocative, imperative, connector or greeting matches the displayed syntax and task; the other options do not. |
| `workbook[4]/1` | workbook | Тарасе, постав столи, ___ людей багато. | бо | D | M47; U25; U27. А can contrast two clauses, while бо states the reason for the request. |
| `workbook[4]/2` | workbook | Я думаю, ___ все готово. | що | D | M47; U14; U29. Коли can specify when the speaker thinks; що states the judgement. |
| `workbook[4]/3` | workbook | Марія пише привітання, ___ Тарас ставить стіл. | а | D | M47; U25; U28. Де can locate the writing where Taras is setting the table; а compares their actions. |
| `workbook[4]/4` | workbook | Скажіть, ___ ви вільні. | коли | D | M47; U27; U29. Бо can introduce a reason for an absolute imperative Скажіть; коли requests the time of availability. |
| `workbook[4]/5` | workbook | ___ Новим роком! | З | C | M47; U14; U23-U30; U41; U47. The keyed vocative, imperative, connector or greeting matches the displayed syntax and task; the other options do not. |

## what-happened

| Item | Section | Original stem | Key | Verdict | Evidence and reason |
| --- | --- | --- | --- | --- | --- |
| `act-2/0` | inline | Учора він ___ книжку. | читав | C | M48; U39; U44. The keyed past form agrees in gender/number with the named subject or speaker; the rule question uses the same attested morphology. |
| `act-2/1` | inline | Олена ___ вечерю. | готувала | C | M48; U39; U44. The keyed past form agrees in gender/number with the named subject or speaker; the rule question uses the same attested morphology. |
| `act-2/2` | inline | Ми ___ в парку. | гуляли | C | M48; U39; U44. The keyed past form agrees in gender/number with the named subject or speaker; the rule question uses the same attested morphology. |
| `act-2/3` | inline | Вони ___ разом. | працювали | C | M48; U39; U44. The keyed past form agrees in gender/number with the named subject or speaker; the rule question uses the same attested morphology. |
| `act-2/4` | inline | Тарас ___ фільм. | дивився | C | M48; U39; U44. The keyed past form agrees in gender/number with the named subject or speaker; the rule question uses the same attested morphology. |
| `act-2/5` | inline | Марія ___ телефоном. | говорила | C | M48; U39; U44. The keyed past form agrees in gender/number with the named subject or speaker; the rule question uses the same attested morphology. |
| `act-3/0` | inline | Why can я читав and ти читав have the same ending? | Because past tense marks masculine singular here. | C | M48; U39; U44. The keyed past form agrees in gender/number with the named subject or speaker; the rule question uses the same attested morphology. |
| `act-3/1` | inline | Which form fits a female speaker saying I read? | Я читала. | C | M48; U39; U44. The keyed past form agrees in gender/number with the named subject or speaker; the rule question uses the same attested morphology. |
| `act-3/2` | inline | Which form fits a group? | Ми читали. | C | M48; U39; U44. The keyed past form agrees in gender/number with the named subject or speaker; the rule question uses the same attested morphology. |
| `act-3/3` | inline | Which question fits Ivan? | Що ти робив? | C | M48; U39; U44. The keyed past form agrees in gender/number with the named subject or speaker; the rule question uses the same attested morphology. |

## yesterday

| Item | Section | Original stem | Key | Verdict | Evidence and reason |
| --- | --- | --- | --- | --- | --- |
| `act-2/0` | inline | ___ я прокинулася о сьомій. | Зранку | D | M49; U16; U33; U34; U35. The isolated event does not uniquely determine its time of day or its position in the sequence; another displayed adverb also fits. |
| `act-2/1` | inline | ___ я пішла на роботу. | Потім | D | M49; U16; U33; U34; U35. The isolated event does not uniquely determine its time of day or its position in the sequence; another displayed adverb also fits. |
| `act-2/2` | inline | ___ я обідала в кафе. | Вдень | D | M49; U16; U33; U34; U35. The isolated event does not uniquely determine its time of day or its position in the sequence; another displayed adverb also fits. |
| `act-2/3` | inline | ___ я повернулася додому. | Ввечері | D | M49; U16; U33; U34; U35. The isolated event does not uniquely determine its time of day or its position in the sequence; another displayed adverb also fits. |
| `act-2/4` | inline | ___ я лягла спати. | Нарешті | D | M49; U16; U33; U34; U35. The isolated event does not uniquely determine its time of day or its position in the sequence; another displayed adverb also fits. |
| `act-4/0` | inline | Анна says: Зранку я прокинулася. What should come next? | Потім я поснідала. | C | M49; U16; U31-U35; U39. The instruction fixes Anna as one female speaker; only the key preserves that agreement, or identifies учора as past time. |
| `act-4/1` | inline | Which pair fits one female speaker? | Я пішла. Я повернулася. | C | M49; U16; U31-U35; U39. The instruction fixes Anna as one female speaker; only the key preserves that agreement, or identifies учора as past time. |
| `act-4/2` | inline | Which line is a clean end to Анна's day? | Нарешті я лягла спати. | C | M49; U16; U31-U35; U39. The instruction fixes Anna as one female speaker; only the key preserves that agreement, or identifies учора as past time. |
| `act-4/3` | inline | What does учора do in the story? | It places the story in the past day. | C | M49; U16; U31-U35; U39. The instruction fixes Anna as one female speaker; only the key preserves that agreement, or identifies учора as past time. |
| `workbook[4]/0` | workbook | Учора я ___ о пів на сьому. | прокинулася | C | M49; U16; U31-U35; U39. The instruction fixes Anna as one female speaker; only the key preserves that agreement, or identifies учора as past time. |
| `workbook[4]/1` | workbook | Потім я ___ кашу і пила каву. | їла | C | M49; U16; U31-U35; U39. The instruction fixes Anna as one female speaker; only the key preserves that agreement, or identifies учора as past time. |
| `workbook[4]/2` | workbook | Вдень я ___ салат. | замовила | C | M49; U16; U31-U35; U39. The instruction fixes Anna as one female speaker; only the key preserves that agreement, or identifies учора as past time. |
| `workbook[4]/3` | workbook | Після роботи я ___ продукти. | купила | C | M49; U16; U31-U35; U39. The instruction fixes Anna as one female speaker; only the key preserves that agreement, or identifies учора as past time. |
| `workbook[4]/4` | workbook | Об одинадцятій я ___ спати. | лягла | C | M49; U16; U31-U35; U39. The instruction fixes Anna as one female speaker; only the key preserves that agreement, or identifies учора as past time. |

## what-will-happen

| Item | Section | Original stem | Key | Verdict | Evidence and reason |
| --- | --- | --- | --- | --- | --- |
| `act-2/0` | inline | Завтра я ___ працювати. | буду | C | M50; U39. The instruction explicitly requires the compound future or its infinitive/auxiliary; only the key has the required form and agreement. |
| `act-2/1` | inline | Що ти ___ робити ввечері? | будеш | C | M50; U39. The instruction explicitly requires the compound future or its infinitive/auxiliary; only the key has the required form and agreement. |
| `act-2/2` | inline | Вона ___ читати книжку. | буде | C | M50; U39. The instruction explicitly requires the compound future or its infinitive/auxiliary; only the key has the required form and agreement. |
| `act-2/3` | inline | Ми ___ дивитися футбол. | будемо | C | M50; U39. The instruction explicitly requires the compound future or its infinitive/auxiliary; only the key has the required form and agreement. |
| `act-2/4` | inline | Ви ___ гуляти в парку? | будете | C | M50; U39. The instruction explicitly requires the compound future or its infinitive/auxiliary; only the key has the required form and agreement. |
| `act-2/5` | inline | Вони ___ відпочивати. | будуть | C | M50; U39. The instruction explicitly requires the compound future or its infinitive/auxiliary; only the key has the required form and agreement. |
| `act-3/0` | inline | Which sentence means I will read? | Я буду читати. | C | M50; U39. The instruction explicitly requires the compound future or its infinitive/auxiliary; only the key has the required form and agreement. |
| `act-3/1` | inline | What stays unchanged after будемо? | The infinitive. | C | M50; U39. The instruction explicitly requires the compound future or its infinitive/auxiliary; only the key has the required form and agreement. |
| `act-3/2` | inline | Which form fits ми? | Ми будемо робити. | C | M50; U39. The instruction explicitly requires the compound future or its infinitive/auxiliary; only the key has the required form and agreement. |
| `act-3/3` | inline | Which question asks about tomorrow? | Що ти будеш робити завтра? | C | M50; U39. The instruction explicitly requires the compound future or its infinitive/auxiliary; only the key has the required form and agreement. |
| `workbook[3]/0` | workbook | Я буду ___ завтра. | читати | C | M50; U39. The instruction explicitly requires the compound future or its infinitive/auxiliary; only the key has the required form and agreement. |
| `workbook[3]/1` | workbook | Ти будеш ___ ввечері? | робити | C | M50; U39. The instruction explicitly requires the compound future or its infinitive/auxiliary; only the key has the required form and agreement. |
| `workbook[3]/2` | workbook | Вона буде ___ вечерю. | готувати | C | M50; U39. The instruction explicitly requires the compound future or its infinitive/auxiliary; only the key has the required form and agreement. |
| `workbook[3]/3` | workbook | Ми будемо ___ футбол. | дивитися | C | M50; U39. The instruction explicitly requires the compound future or its infinitive/auxiliary; only the key has the required form and agreement. |
| `workbook[3]/4` | workbook | Вони будуть ___. | відпочивати | C | M50; U39. The instruction explicitly requires the compound future or its infinitive/auxiliary; only the key has the required form and agreement. |

## my-plans

| Item | Section | Original stem | Key | Verdict | Evidence and reason |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | У ___ я буду працювати. | понеділок | C | M51; U39. The explicit planning task, case frame or requested speech act selects the key; the other choices fail its form or meaning. |
| `act-1/1` | inline | У суботу ___ я буду прибирати квартиру. | зранку | C | M51; U39. The explicit planning task, case frame or requested speech act selects the key; the other choices fail its form or meaning. |
| `act-1/2` | inline | ___ шостій ми будемо дивитися кіно. | О | C | M51; U39. The explicit planning task, case frame or requested speech act selects the key; the other choices fail its form or meaning. |
| `act-1/3` | inline | У неділю він буде ___. | відпочивати | C | M51; U39. The explicit planning task, case frame or requested speech act selects the key; the other choices fail its form or meaning. |
| `act-1/4` | inline | У п'ятницю ввечері буде ___. | вечірка | D | M51; M51; U51. The unqualified existential буде also permits квартира in an availability context; the cue fixes the intended event. |
| `act-3/0` | inline | Which line gives a day, time, and compound future? | У суботу о третій я буду готувати. | C | M51; U39. The explicit planning task, case frame or requested speech act selects the key; the other choices fail its form or meaning. |
| `act-3/1` | inline | Which invitation reuses the M43 phrase? | Ходімо в кіно! | C | M51; U39. The explicit planning task, case frame or requested speech act selects the key; the other choices fail its form or meaning. |
| `act-3/2` | inline | Which answer politely refuses? | На жаль, не можу. | C | M51; U39. The explicit planning task, case frame or requested speech act selects the key; the other choices fail its form or meaning. |
| `act-3/3` | inline | Which phrase asks about availability? | Ти будеш вільна у суботу? | D | M51; U39. The past-time question also asks about availability; the original question did not restrict the time. |
| `workbook[3]/0` | workbook | У вівторок я ___ українську. | буду вчити | D | M51; U39. A weekday does not fix the tense, and present-tense forms can also describe a scheduled future action. |
| `workbook[3]/1` | workbook | У середу ми ___ вечерю. | будемо готувати | D | M51; U39. A weekday does not fix the tense, and present-tense forms can also describe a scheduled future action. |
| `workbook[3]/2` | workbook | У четвер вона ___ допізна. | буде працювати | D | M51; U39. A weekday does not fix the tense, and present-tense forms can also describe a scheduled future action. |
| `workbook[3]/3` | workbook | ___, не можу. У суботу я буду працювати. | На жаль | C | M51; U39. The explicit planning task, case frame or requested speech act selects the key; the other choices fail its form or meaning. |

## my-story

| Item | Section | Original stem | Key | Verdict | Evidence and reason |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | ___ я жив у Торонто. | Раніше | D | M52; U31; U32. Далі can continue a past or present narrative, and зараз can refer to a just-completed past event; the cue fixes the intended time meaning. |
| `act-1/1` | inline | ___ я живу в Києві. | Зараз | D | M52; U31; U32. Далі can continue a past or present narrative, and зараз can refer to a just-completed past event; the cue fixes the intended time meaning. |
| `act-1/2` | inline | ___ я буду вчити українську. | Далі | C | M52; U31; U32; U39; U44. The task fixes the future form or time meaning, selecting the key; the displayed alternatives do not meet that restriction. |
| `act-1/3` | inline | ___ я ходила в школу. | У дитинстві | D | M52; U31; U32. Далі can continue a past or present narrative, and зараз can refer to a just-completed past event; the cue fixes the intended time meaning. |
| `workbook[2]/0` | workbook | Я ___ у Львові. | народилася | D | M52; U39; U44. Without a time word the three birth forms are defensible in different time frames. |
| `workbook[2]/1` | workbook | Раніше я ___ в Одесі. | жила | D | M52; U39. The present form is also available as narrative present, unless the grammatical tense is specified. |
| `workbook[2]/2` | workbook | Зараз я ___ в офісі. | працюю | D | M52; U31; U39. Зараз also means very soon or just now, allowing future or past readings. |
| `workbook[2]/3` | workbook | Далі я ___ українську щодня. | буду вчити | D | M52; U32; U39. Далі does not itself require future tense; the past and present options are also defensible. |
| `workbook[3]/0` | workbook | Which sentence matches the time word? | Зараз я живу в Києві. | D | M52; U31. Зараз can mean just now and accompany a past event, so the original past-tense alternative is defensible. |
| `workbook[3]/1` | workbook | Which sentence uses the A1 future? | Далі я буду працювати. | C | M52; U31; U32; U39; U44. The task fixes the future form or time meaning, selecting the key; the displayed alternatives do not meet that restriction. |
| `workbook[3]/2` | workbook | Which is the natural name sentence? | Мене звати Данило. | C | M52; U31; U32; U39; U44. The task asks for the natural A1 introduction, Мене звати; this does not claim that the full possessive name sentence is ungrammatical. |

## health

| Item | Section | Original stem | Key | Verdict | Evidence and reason |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | У мене болить ___. | голова | C | M53; U37. The key is the available phrase matching the symptom, need or communication repair. A repair prompt is not evidence that its original possessive sentence is ungrammatical. |
| `act-1/1` | inline | Мені потрібен ___. | лікар | C | M53; U37. The key is the available phrase matching the symptom, need or communication repair. A repair prompt is not evidence that its original possessive sentence is ungrammatical. |
| `act-1/2` | inline | У мене ___. | температура | D | M53; M53; U52. У мене квиток is also a grammatical possession statement; the original stem did not specify a symptom. |
| `act-1/3` | inline | ___, будь ласка. | Повторіть | C | M53; U37. The key is the available phrase matching the symptom, need or communication repair. A repair prompt is not evidence that its original possessive sentence is ungrammatical. |
| `act-4/0` | inline | You want to say: My stomach hurts. | У мене болить живіт. | C | M53; U37. The key is the available phrase matching the symptom, need or communication repair. A repair prompt is not evidence that its original possessive sentence is ungrammatical. |
| `act-4/1` | inline | You need a doctor. | Мені потрібен лікар. | C | M53; U37. The key is the available phrase matching the symptom, need or communication repair. A repair prompt is not evidence that its original possessive sentence is ungrammatical. |
| `act-4/2` | inline | You do not understand. | Я не розумію. | C | M53; U37. The key is the available phrase matching the symptom, need or communication repair. A repair prompt is not evidence that its original possessive sentence is ungrammatical. |
| `workbook[2]/0` | workbook | Добрий день. У мене болить ___. | спина | C | M53; U37. The key is the available phrase matching the symptom, need or communication repair. A repair prompt is not evidence that its original possessive sentence is ungrammatical. |
| `workbook[2]/1` | workbook | Вибачте. Де тут ___? | аптека | C | M53; U37. The key is the available phrase matching the symptom, need or communication repair. A repair prompt is not evidence that its original possessive sentence is ungrammatical. |
| `workbook[2]/2` | workbook | Мені ___. | погано | C | M53; U37. The key is the available phrase matching the symptom, need or communication repair. A repair prompt is not evidence that its original possessive sentence is ungrammatical. |
| `workbook[2]/3` | workbook | ___, будь ласка. Я не розумію. | Повільніше | C | M53; U37. The key is the available phrase matching the symptom, need or communication repair. A repair prompt is not evidence that its original possessive sentence is ungrammatical. |
| `workbook[3]/0` | workbook | Repair: Моя рука болить. | У мене болить рука. | C | M53; U37. The key is the available phrase matching the symptom, need or communication repair. A repair prompt is not evidence that its original possessive sentence is ungrammatical. |
| `workbook[3]/1` | workbook | Repair: Я потрібно лікар. | Мені потрібен лікар. | C | M53; U37. The key is the available phrase matching the symptom, need or communication repair. A repair prompt is not evidence that its original possessive sentence is ungrammatical. |
| `workbook[3]/2` | workbook | Repair: У мене є нежить. | У мене нежить. | C | M53; U37. The key is the available phrase matching the symptom, need or communication repair. A repair prompt is not evidence that its original possessive sentence is ungrammatical. |

## emergencies

| Item | Section | Original stem | Key | Verdict | Evidence and reason |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | ___! Тут аварія. | Допоможіть | C | M54; U44. The key matches the emergency scenario, location/number frame or requested response; the displayed alternatives do not communicate it. |
| `act-1/1` | inline | Подзвоніть за номером ___. | 112 | C | M54; U44. The key matches the emergency scenario, location/number frame or requested response; the displayed alternatives do not communicate it. |
| `act-1/2` | inline | Мене ___ Анна. | звати | C | M54; U44. The key matches the emergency scenario, location/number frame or requested response; the displayed alternatives do not communicate it. |
| `act-1/3` | inline | Я ___ вулиці Шевченка. | на | C | M54; U44. The key matches the emergency scenario, location/number frame or requested response; the displayed alternatives do not communicate it. |
| `act-1/4` | inline | ___ швидку! | Викличте | C | M54; U44. The key matches the emergency scenario, location/number frame or requested response; the displayed alternatives do not communicate it. |
| `act-1/5` | inline | ___ поліцію! | Викличте | C | M54; U44. The key matches the emergency scenario, location/number frame or requested response; the displayed alternatives do not communicate it. |
| `act-4/0` | inline | You need to say: There is a fire here. | Тут пожежа. | C | M54; U44. The key matches the emergency scenario, location/number frame or requested response; the displayed alternatives do not communicate it. |
| `act-4/1` | inline | You need police. | Потрібна поліція. | C | M54; U44. The key matches the emergency scenario, location/number frame or requested response; the displayed alternatives do not communicate it. |
| `act-4/2` | inline | You want someone to call 103. | Подзвоніть за номером 103, будь ласка. | C | M54; U44. The key matches the emergency scenario, location/number frame or requested response; the displayed alternatives do not communicate it. |
| `act-4/3` | inline | You need someone to summon an ambulance. | Викличте швидку! | C | M54; U44. The key matches the emergency scenario, location/number frame or requested response; the displayed alternatives do not communicate it. |
| `workbook[2]/0` | workbook | Я ___ метро. | біля | C | M54; U44. The key matches the emergency scenario, location/number frame or requested response; the displayed alternatives do not communicate it. |
| `workbook[2]/1` | workbook | Будинок ___. | п'ять | C | M54; U44. The key matches the emergency scenario, location/number frame or requested response; the displayed alternatives do not communicate it. |
| `workbook[2]/2` | workbook | Я ___ готелі. | в | C | M54; U44. The key matches the emergency scenario, location/number frame or requested response; the displayed alternatives do not communicate it. |
| `workbook[2]/3` | workbook | Я ___ аптеки. | навпроти | C | M54; U44. The key matches the emergency scenario, location/number frame or requested response; the displayed alternatives do not communicate it. |
| `workbook[3]/0` | workbook | Як вас звати? | Мене звати Сара. | C | M54; U44. The key matches the emergency scenario, location/number frame or requested response; the displayed alternatives do not communicate it. |
| `workbook[3]/1` | workbook | Ваш номер телефону? | Мій номер телефону: нуль дев'яносто сім... | C | M54; U44. The key matches the emergency scenario, location/number frame or requested response; the displayed alternatives do not communicate it. |
| `workbook[3]/2` | workbook | Ви розумієте? | Я трохи розумію. Повторіть, будь ласка. | C | M54; U44. The key matches the emergency scenario, location/number frame or requested response; the displayed alternatives do not communicate it. |

## a1-finale

| Item | Section | Original stem | Key | Verdict | Evidence and reason |
| --- | --- | --- | --- | --- | --- |
| `act-1/1` | inline | Зараз я ___ по Хрещатику. | гуляю | D | M55; U31. Зараз also allows a just-completed past or imminent future reading. |
| `act-1/2` | inline | Учора я ___ квиток. | купив | D | M55; U39. The present option can narrate a past event as historical present. |
| `act-1/3` | inline | Завтра я ___ по Україні. | буду подорожувати | D | M55; U39. Present-tense подорожую can describe a scheduled future journey. |
| `act-1/4` | inline | Ввечері ми ___ в кіно. | ходили | D | M55; U33; U39. Ввечері identifies an evening, not a past day; all three tense options are defensible. |
| `act-1/5` | inline | Зараз Олена ___ борщ і салат. | замовляє | D | M55; U31. Зараз can locate an imminent future or a recently completed past order. |
| `act-1/6` | inline | Учора була гарна погода, і ми ___ в парку. | гуляли | D | M55; U39. The present гуляємо can narrate the past event as historical present. |
| `act-1/7` | inline | Я вже ___ до рівня А2! | готовий | C | M55; U31; U33; U34; U39; U44. The key fits the requested speech act or grammatical frame; the remaining choices do not. |
| `workbook[0]/0` | workbook | How do you ask about the price of a ticket? | Скільки коштує квиток? | C | M55; U31; U33; U34; U39; U44. The key fits the requested speech act or grammatical frame; the remaining choices do not. |
| `workbook[0]/1` | workbook | You invite a friend to a cafe. | Ходімо в кафе! | C | M55; U31; U33; U34; U39; U44. The key fits the requested speech act or grammatical frame; the remaining choices do not. |
| `workbook[0]/2` | workbook | How do you say: My head hurts? | У мене болить голова. | C | M55; U31; U33; U34; U39; U44. The key fits the requested speech act or grammatical frame; the remaining choices do not. |
| `workbook[0]/3` | workbook | Someone asks: 'Де ви?' | Я на вулиці Хрещатик. | C | M55; U31; U33; U34; U39; U44. The key fits the requested speech act or grammatical frame; the remaining choices do not. |
| `workbook[0]/4` | workbook | What time frame is in: 'Завтра я буду читати книгу'? | Майбутній | C | M55; U31; U33; U34; U39; U44. The key fits the requested speech act or grammatical frame; the remaining choices do not. |
| `workbook[3]/0` | workbook | Мене ___. | звати | C | M55; U31; U33; U34; U39; U44. The key fits the requested speech act or grammatical frame; the remaining choices do not. |
| `workbook[3]/1` | workbook | Зранку я ___ у кафе. | снідав | D | M55; U34; U39; U44. Буду produces the grammatical future-location sentence, while зранку alone does not fix past time. |
| `workbook[3]/2` | workbook | Ввечері ми ___ в кіно. | ходили | C | M55; U31; U33; U34; U39; U44. The key fits the requested speech act or grammatical frame; the remaining choices do not. |
| `workbook[3]/3` | workbook | Завтра я ___ повторювати українську. | буду | C | M55; U31; U33; U34; U39; U44. The key fits the requested speech act or grammatical frame; the remaining choices do not. |

## Repairs

| Item | Evidence | Source repair, with original key unchanged |
| --- | --- | --- |
| `please-do-this/workbook[0]/0` | U41; U44 | sentence: (Use the ти command form.) Олено, ___ книжку! |
| `please-do-this/workbook[0]/2` | U41; U44 | sentence: (Use the ти command form.) Тарасе, ___ в кафе. |
| `linking-ideas/act-1/1` | U25; U26; U27 | ['options', 1]: тому що |
| `linking-ideas/act-1/2` | U24; U26; U14 | ['options', 1]: що |
| `linking-ideas/act-1/7` | U13; U15 | sentence: (Ask which ONE profession applies.) Ви студент ___ лікар? |
| `linking-ideas/workbook[1]/1` | U24; U26; U14 | ['options', 1]: що |
| `when-and-where/act-1/0` | U28; U29; U14 | sentence: (I know that this is a cafe.) Я знаю, ___ це кафе. |
| `when-and-where/act-1/2` | U28; U29; U14 | sentence: (Tell me when the lesson is.) Скажи, ___ урок. |
| `when-and-where/act-1/4` | U28; U29; U14 | sentence: (I know where you live.) Я знаю, ___ ти живеш. |
| `when-and-where/act-1/5` | U28; U29; U14 | sentence: (Do you know when the meeting is?) Ти знаєш, ___ зустріч? |
| `when-and-where/act-1/6` | U28; U29; U14 | sentence: (I think that this is correct.) Я думаю, ___ це правильно. |
| `when-and-where/workbook[1]/1` | U28; U29; U14 | sentence: (Tell me when you are by the fountain.) Скажи, ___ ти біля фонтану. |
| `when-and-where/workbook[1]/2` | U28; U29; U14 | sentence: (I see that the building is close.) Я бачу, ___ будинок близько. |
| `when-and-where/workbook[1]/5` | U28; U29; U14 | sentence: (Tell me when the meeting in the cafe is.) Скажи, ___ зустріч у кафе. |
| `checkpoint-communication/act-2/1` | U24; U26 | ['options', 1, 'text']: щоб |
| `checkpoint-communication/act-2/2` | U25; U27 | prompt: (Give the reason for putting out a table.) Тарас ставить стіл, ___ людей багато. |
| `checkpoint-communication/act-2/3` | U25; U29; U30 | prompt: (Compare the two people; do not give a time or a choice.) Марія пише, ___ Тарас ставить стіл. |
| `checkpoint-communication/act-2/4` | U28; U47 | prompt: (Give the reason for taking the marker.) Я беру маркер, ___ пишу листівку. |
| `checkpoint-communication/act-3/1` | U14; U29 | sentence: (I think that everything is ready.) Я думаю, ___ все готово. |
| `checkpoint-communication/act-3/2` | U28; U29 | sentence: (Tell me when the meeting is.) Скажи, ___ зустріч. |
| `checkpoint-communication/act-3/4` | U14; U28; U29 | sentence: (I do not know what to write.) Я не знаю, ___ писати. |
| `checkpoint-communication/act-3/5` | U14; U29 | sentence: (Tell us when you are free.) Скажіть, ___ ви вільні. |
| `checkpoint-communication/workbook[4]/1` | U25; U27 | sentence: (Give the reason for putting out the tables.) Тарасе, постав столи, ___ людей багато. |
| `checkpoint-communication/workbook[4]/2` | U14; U29 | sentence: (I think that everything is ready.) Я думаю, ___ все готово. |
| `checkpoint-communication/workbook[4]/3` | U25; U28 | sentence: (Compare the two people; do not describe a location.) Марія пише привітання, ___ Тарас ставить стіл. |
| `checkpoint-communication/workbook[4]/4` | U27; U29 | sentence: (Tell us WHEN you are free.) Скажіть, ___ ви вільні. |
| `yesterday/act-2/0` | U16; U33; U34; U35 | sentence: (In the morning.) ___ я прокинулася о сьомій. |
| `yesterday/act-2/1` | U16; U33; U34; U35 | sentence: (Then, after breakfast.) ___ я пішла на роботу. |
| `yesterday/act-2/2` | U16; U33; U34; U35 | sentence: (During the daytime.) ___ я обідала в кафе. |
| `yesterday/act-2/3` | U16; U33; U34; U35 | sentence: (In the evening.) ___ я повернулася додому. |
| `yesterday/act-2/4` | U16; U33; U34; U35 | sentence: (Finally, at the end of the day.) ___ я лягла спати. |
| `my-plans/act-1/4` | M51; U51 | sentence: (There will be a party.) У п'ятницю ввечері буде ___. |
| `my-plans/act-3/3` | U39 | prompt: Which phrase asks about future availability? |
| `my-plans/workbook[3]/0` | U39 | sentence: (Use the compound future: бути + infinitive.) У вівторок я ___ українську. |
| `my-plans/workbook[3]/1` | U39 | sentence: (Use the compound future: бути + infinitive.) У середу ми ___ вечерю. |
| `my-plans/workbook[3]/2` | U39 | sentence: (Use the compound future: бути + infinitive.) У четвер вона ___ допізна. |
| `my-story/act-1/0` | U31; U32 | sentence: (Earlier, before the present period.) ___ я жив у Торонто. |
| `my-story/act-1/1` | U31; U32 | sentence: (Now, in the present period.) ___ я живу в Києві. |
| `my-story/act-1/3` | U31; U32 | sentence: (During childhood.) ___ я ходила в школу. |
| `my-story/workbook[2]/0` | U39; U44 | sentence: (Past tense, female speaker.) Я ___ у Львові. |
| `my-story/workbook[2]/1` | U39 | sentence: (Use past tense.) Раніше я ___ в Одесі. |
| `my-story/workbook[2]/2` | U31; U39 | sentence: (Use present tense.) Зараз я ___ в офісі. |
| `my-story/workbook[2]/3` | U32; U39 | sentence: (Use the compound future: бути + infinitive.) Далі я ___ українську щодня. |
| `my-story/workbook[3]/0` | U31 | prompt: Which sentence uses a present-tense verb with зараз? |
| `health/act-1/2` | M53; U52 | sentence: (Say that you have a fever.) У мене ___. |
| `a1-finale/act-1/1` | U31 | sentence: (Use present tense.) Зараз я ___ по Хрещатику. |
| `a1-finale/act-1/2` | U39 | sentence: (Use past tense, male speaker.) Учора я ___ квиток. |
| `a1-finale/act-1/3` | U39 | sentence: (Use the compound future: бути + infinitive.) Завтра я ___ по Україні. |
| `a1-finale/act-1/4` | U33; U39 | sentence: (Use past tense.) Учора ввечері ми ___ в кіно. |
| `a1-finale/act-1/5` | U31 | sentence: (Use present tense.) Зараз Олена ___ борщ і салат. |
| `a1-finale/act-1/6` | U39 | sentence: (Use past tense.) Учора була гарна погода, і ми ___ в парку. |
| `a1-finale/workbook[3]/1` | U34; U39; U44 | sentence: (Past tense, male speaker.) Учора зранку я ___ у кафе. |

## Validation and batch sizing

- Structural scanner: `scripts/audit/scan_activity_errors.py --track a1-v1`, 55/55 files, zero structural findings before and after changes.
- Existing affected activity/parser/generator/manifest tests: 329 passed in 11.25 seconds, using `pytest -n 2 tests/test_scan_activity_errors.py tests/test_a1_activity_schema_parser_drift.py tests/test_yaml_activities_a1_payload.py tests/test_activity_renderer.py tests/test_generate_mdx.py tests/test_generate_mdx_parsers.py tests/test_generate_mdx_unit_map.py tests/test_generate_mdx_v7_resources_vocab.py tests/test_curriculum_manifest_canary.py`. Ruff on those test files and the scanner/parser/converter passed. No test case is added.
- The existing `ActivityParser`, `yaml_activities_to_jsx` and `dump_json_for_jsx` regenerate only the 52 changed item objects in nine tracked MDX pages. Unchanged item objects and bytes outside those objects are preserved. The integrity manifest updates only the corresponding source/page hashes. Regeneration also exposes the existing YAML explanation strings on changed FillIn objects where the archived MDX had omitted them. Some generalizations in those source explanations are tracked as F2 below; the repair brief permits cue/distractor changes, not explanation rewrites.
- Chromium exercised all 52 changed tracked MDX payloads through the existing FillInQuestion and QuizQuestion components: 52 keys accepted, 52 wrong choices rejected, zero browser errors. The runtime was copied into this worktree after lockfile equality was verified. The PR is the record for independent Gemini via read-only AGY and Opus 5.5 with Sources, browser proof, and exact-head CI/merge receipts. All required gates must pass on the current head before landing. This document records the author pass, not deployment or independent approval.

The counted denominator is 234, including 77 workbook items. Source inventory started at 2026-10-28T20:11:08.061423+00:00. The initial author pass/report interval was 14.3 minutes before independent review. This revised report was prepared at 2026-10-28T20:39:20.767355+00:00, an elapsed 28.2 minutes from inventory, including review waiting, the source-backed F1 correction and regeneration. Neither interval is pure model throughput. Review, CI and queue time are reported separately on the PR. Later batches should be sized by their full item census rather than module count.

Residual owner: CTO curriculum coordinator, #8893. The other module slices, unchecked activity types, prose, broader held-out evaluation and deployed behavior remain outside this slice.

## Review corrections and tracked follow-ups

Round 1 Opus F1 was accepted. The three Ti or vy? quiz prompts are restored and checked-clean against Golub p.177, Avramenko p.135 and the module rule. Their situation already fixes the register; adding the requested pronoun would change that learning target. The two bare-vocative workbook repairs remain. The revised count is 182 checked-clean and 52 repaired.

Non-blocking follow-ups remain with the CTO curriculum coordinator on #8893: F2, existing explanation generalizations newly exposed by FillIn regeneration; F3, other activity types that reject narrative present or past-time далі; F4, final review/CI/merge receipts belong on the PR, with no premature completion claim here; F5, the reviewer considers some retained cues over-cautious under the original context. Gemini G1 records the same already-declared unchecked scope. None expands this slice into prose or other activity types.
