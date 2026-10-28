# A1-v1 language pass, manifest modules 1 through 14

Refs #8893. Source snapshot: `d59fd9bcfd894f4fac5de27a173f0d6e42180d6c`.

This is one bounded Method step 2 slice. It checks 447 items: all 446 fill-in and quiz items in both inline/root and workbook sections of the first 14 manifest modules, plus `a1-finale/act-1/0`. There are 403 checked-clean items and 44 confirmed ambiguous items, all repaired. No wrong key was confirmed. Every original key, learning target and activity type is retained.

The order comes from `levels.a1-v1.modules` in `curriculum/l2-uk-en/curriculum.yaml`. It is the issue's arc-order fallback; no authorized usage ranking was supplied. The first 14 entries cover the first two arcs, including both checkpoints. The existing sibling `audit/` directory is the report convention.

| Position | Module | Items checked | Clean | Defects fixed |
| --- | --- | ---: | ---: | ---: |
| 1 | `sounds-letters-and-hello` | 21 | 20 | 1 |
| 2 | `reading-ukrainian` | 3 | 3 | 0 |
| 3 | `special-signs` | 15 | 15 | 0 |
| 4 | `stress-and-melody` | 28 | 28 | 0 |
| 5 | `who-am-i` | 25 | 20 | 5 |
| 6 | `my-family` | 34 | 32 | 2 |
| 7 | `checkpoint-first-contact` | 51 | 40 | 11 |
| 8 | `things-have-gender` | 44 | 38 | 6 |
| 9 | `what-is-it-like` | 37 | 32 | 5 |
| 10 | `colors` | 32 | 28 | 4 |
| 11 | `how-many` | 35 | 35 | 0 |
| 12 | `this-and-that` | 41 | 35 | 6 |
| 13 | `many-things` | 38 | 38 | 0 |
| 14 | `checkpoint-my-world` | 42 | 39 | 3 |
| extra item only | `a1-finale` | 1 | 0 | 1 |

## What was checked

Item indices and anonymous `workbook[n]` activity indices are zero-based. An explicit activity id is used when present. Each row checks the key and every displayed alternative against the instruction and stem. The original stem and unchanged key identify the item even when its cue changes. Clean means no wrong key or second defensible option within that task, not certification of every linguistic claim in the module.

The structural scanner ran before and after repair: 55/55 activity files, exit 0, zero structural findings. It therefore added no flagged items from other activity types. This is not a replacement for issue Method step 1's broader intended semantic and VESUM rules.

Not checked: other activity types with no structural flag; lesson prose, plans, vocabulary and resources; the remaining 40 modules; every other finale item; historical generated/source drift outside the 44 repaired objects; audio, teacher usage and the deployed site. The rest of #8893 remains open with the CTO curriculum coordinator. No deployment or publication is part of this slice.

## Sources evidence and its limits

The `sources` MCP supplied all evidence below on 2026-10-28. VESUM proves forms and grammatical analyses, not an entire sentence's meaning. ULIF stress readings prove the relevant marked form, not a generic most-common reading. `check_text` is a diagnostic screen, not an answer-ambiguity judge. The clean and defect verdicts below are the author's linguistic inferences from those results and the stated task. Usage-sensitive verdicts also cite dictionary, textbook or corpus evidence.

For every module batch, `verify_words` received the distinct Ukrainian tokens from the instruction and all item fields/options, with acute accents stripped and common words lowercased. `verify_stresses` received the original polysyllabic tokens, including marked forms and deliberate wrong-stress alternatives. `check_text` received item ids and accent-free full item text. The first four module screens used all checks; subsequent screens used `vesum` and `ua_gec`, with stress checked separately. No failed transport reply or accent-input rejection counts as evidence.

Capitalization misses were checked again as proper names in U66, 28/28 found. U45 additionally checks completed fill-in strings, including the adjective endings as whole words. K checks 520 target/context tokens, 483 found before the proper-name recheck; its remaining tokens include letters, phonetic fragments, the displayed `мален_кий` scaffold and quoted code-switching errors. They are not unverified target vocabulary. Apostrophe/soft-sign completions were also checked as whole words. Stress ambiguities were interpreted by the item's sense, number and case; a pending reading of an unmarked word is not a defect. All explicitly marked target forms were compared with their applicable readings.

K is the `KEYS` locator in the companion file. A final one-item POSTFIX screen also checks the replacement Моє distractor after the three bulk screens. U73 verifies the final cue forms and the new compound-color components with the stress oracle; the masculine past and first-person present readings of снідати agree with the finale target distinction.

The post-repair `check_text` screens cover all 447 rows in batches of 150, 150 and 147. They report 123, 120 and 103 VESUM diagnostics and 8, 6 and 2 contextual UA-GEC suspicions. These are not clean-tool verdicts: most diagnostics are case-sensitive words, letters, stems, deliberately wrong options or quoted errors. Contextual suggestions such as changing `один` to `одне` do not override a masculine noun. No suspicion alone caused a repair.

The companion [machine-readable Sources evidence](language-pass-modules-01-14-evidence.jsonl) preserves query arguments, VESUM analyses, ULIF row identifiers and diagnostic results for these locators. It contains the module batches, K, U45, U66, and the post-repair screens. Usage locators are summarized with their source citations below.

### Module batch locators

Each M locator binds the successful `verify_words`, `verify_stresses` and `check_text` replies for that module. The receipt digests identify the complete replies used; the queries can be reproduced by the normalization recipe above against the source snapshot and the workbook section. Every item row cites its module locator.

| Locator | Section | VESUM found/queried | Stress rows | Text items | Evidence id / receipt SHA-256 |
| --- | --- | ---: | ---: | ---: | --- |
| M01 | sounds-letters-and-hello, inline/root | 17/19 | 14 | 21 | `VESUM reply`; `ed5374afa23a4c0c61716b6c795b0cca57e24d82143a570a934c4447770b88b4` |
| M02 | reading-ukrainian, workbook | 23/24 | 19 | 3 | `VESUM reply`; `177a9a4600d809443789a57651bbd593f2a221e129bc762a78a892486b3bdbfc` |
| M03 | special-signs, inline/root | 41/43 | 34 | 7 | `VESUM reply`; `bf59128086282b618e1b2d51e49c88d1a9fc6fd0b14116d3ac9340e0bc0db2d3` |
| M03 | special-signs, workbook | 28/33 | 26 | 8 | `VESUM reply`; `e1ea1ea4912072b8e2f099448e08658d59b6f614835a81c227f4a19e9dec6905` |
| M04 | stress-and-melody, inline/root | 106/111 | 111 | 22 | `VESUM reply`; `07ce7e3d2d7e8cd26552a96eb4f99fbb01a63baef9247ad51bc472a49302af7a` |
| M04 | stress-and-melody, workbook | 27/29 | 37 | 6 | `VESUM reply`; `4e2427843014de1c6350f057264fad869a8195d3e4731af0c031d710d8d1484d` |
| M05 | who-am-i, inline/root | 94/96 | 86 | 13 | `VESUM reply`; `6735fb360c58fcd748a3ecad713b47af5359ee7e77f6fc89f9f95beb1fcc8c45` |
| M05 | who-am-i, workbook | 78/87 | 77 | 12 | `VESUM reply`; `a9e5416fa7ce1e0b26f4f64736e49fda39bd96dbac9b85e24d2c1d4ed122c07f` |
| M06 | my-family, inline/root | 104/104 | 88 | 22 | `vesum:84d2337a647f5a4ced906c728521bc3854998f0b85b329bb61b62e7c84be3bc1`; `5d8df31e26b66fd6221b608df4ad4aaa9814da4052dbc8a1bb79d4fb0ec5549d` |
| M06 | my-family, workbook | 77/86 | 75 | 12 | `VESUM reply`; `97793e5a6f1fc09e38935e40156423eed489f6edbbee5f6fcc582e1f8348c94e` |
| M07 | checkpoint-first-contact, inline/root | 221/239 | 224 | 40 | `VESUM reply`; `8887f9a3514a89441bff7cca042e4715c70325a37f5e78594950b84b6335040c` |
| M07 | checkpoint-first-contact, workbook | 57/63 | 58 | 11 | `VESUM reply`; `a264989f8df9a97667093178aa5bb6e086463a7aff79a41f70fa40019650bd94` |
| M08 | things-have-gender, inline/root | 83/84 | 86 | 32 | `VESUM reply`; `25bacf7cabef4b08496bdd4aa9bc8c7181511dc84351b98201314d31676a8e31` |
| M08 | things-have-gender, workbook | 73/74 | 64 | 12 | `VESUM reply`; `1813bd4b60918899d88c47e7aae6f9df98917758d47c8164c814c1f71eab589f` |
| M09 | what-is-it-like, inline/root | 18/28 | 29 | 16 | `VESUM reply`; `7d17724fb5a295f2ae391b17393892c8b67bfdb39259d7dfacf5ce72fe7bc2e8` |
| M09 | what-is-it-like, workbook | 75/81 | 75 | 21 | `VESUM reply`; `8595658b14e94952991a24bb24ad8f31c8b9c23a730a90edd00816ee2e415349` |
| M10 | colors, inline/root | 52/57 | 73 | 24 | `VESUM reply`; `068bfde6d3bd4276a46e82b036a3e9ba61d0d7895858feb3c68fc6c6b1b963a1` |
| M10 | colors, workbook | 37/37 | 37 | 8 | `vesum:6ec2266cd0160ead6eb3d7270d06af8d45db88adffba740ee38dddb6b0a5a268`; `976fc83370234d2c0e141d0a2fac4b8a82103a38423b815ed3b57cd9e2f8f9ee` |
| M11 | how-many, inline/root | 32/32 | 26 | 16 | `vesum:ce704956074db968ea8b590e12a170ca415c56500d94f88fc212484a67cf3e6c`; `cb170664cd715d08c725d982a011bec3eb9e9412365d08c87fe893fd456975c0` |
| M11 | how-many, workbook | 38/57 | 44 | 19 | `VESUM reply`; `250aa3dac6f07be971c0ffbb444f366c4e88c7c6afc1c5c4397c42a893af5214` |
| M12 | this-and-that, inline/root | 38/41 | 33 | 27 | `VESUM reply`; `e53b01400be82d68a46a72b77aa04b373713ff6b8c0fc2f289e95e691a15e96f` |
| M12 | this-and-that, workbook | 48/48 | 41 | 14 | `vesum:ef8908d05d2ac6ddf9637e31f75e3bd4c48d7af2b949445de10ab20dee8acb02`; `40f482556677a83eb4aff734d0e5c06f9d4457e1f9e66c204f37371475dcc5c3` |
| M13 | many-things, inline/root | 50/66 | 65 | 26 | `VESUM reply`; `c3d2495395d91024c63e52e23079c9d2430b7c0b0361f35328a190369f10a8aa` |
| M13 | many-things, workbook | 34/40 | 31 | 12 | `VESUM reply`; `fa47a2db7c98ec6cd6cd99ba57344bcd75e7aecbf291786e0b4ca552f55df9d3` |
| M14 | checkpoint-my-world, inline/root | 72/72 | 78 | 26 | `vesum:018442a7d35f43535bb8a64dc29ce06c273b2a3eed13a0885ddcb9e85cef937a`; `e2b43d604b5e637648347a10cc8505204737808658a49549603ad380fbe24761` |
| M14 | checkpoint-my-world, workbook | 37/37 | 40 | 16 | `vesum:3e177af62bf96b6287fc5e87024d939800166936bedda97d1d545d0c68ba5a04`; `6a05637cb7e7dbce92a4e5f532786afd861d2ce02a29dd94a333497c43ba6aaa` |
| M15 | a1-finale, inline/root | 6/6 | 6 | 1 | `vesum:ae6d2faa86960a80df14aef1968bc2ae041a6e00258d010301d3269f745a1b06`; `1d741b50331bd3f4e815cc4d68aa376f47ab68fe7263d3adfce17b663210669d` |

### Usage and orthography locators

The following are compact source summaries, not copied dictionary articles. The official offline SUM-20 lookups U1/U5/U6/U7/U19/U64 returned ingestion misses, so they prove neither validity nor invalidity. Modern VTS lookups were the facet-appropriate fallback. No SUM-11 text is used as normative evidence. Incidental cross-dictionary snippets on an aggregator page are distinguished below.

- U9: `query_slovnyk_me(word="зранку", dict="vts")`: morning time or since morning; no past-tense requirement.
- U10: VTS `бути`: present є across persons; sense 10 is the copula, often omitted; sense 2 is possession/existence. https://slovnyk.me/dict/vts/бути
- U11: VTS `фамілія` page: its VTS entry is family/lineage; the separately labelled SUM-20 synopsis on that page explicitly records colloquial surname. U30 independently attests surname usage. https://slovnyk.me/dict/vts/фамілія
- U12: VTS `здрастувати`, sense 2: imperative здрастуй/здрастуйте is a greeting. https://slovnyk.me/dict/vts/здрастувати
- U17: `search_text` on profession nouns: Avramenko 2018 grade 10, p.157, `10-klas-ukrajinska-mova-avramenko-2018_s0227`, explicitly permits both вона — досвідчений лікар and досвідчена лікарка. Used for that distinction only; its dated inventory of feminine forms is not a current vocabulary rule.
- U18: `query_grac(query="блакитно-жовтий", mode="concordance", limit=3)` directly attests блакитно-жовті прапори and national flags. Corpus usage, not a statutory color specification.
- U20: VTS `мати`, verb sense 1, explicitly includes age expressed with a numeral plus рік/літа. https://slovnyk.me/dict/vts/мати
- U23: VTS `ви`: polite address to one person as well as plural address, with no age restriction. https://slovnyk.me/dict/vts/ви
- U28: VTS `допомогти`: perfective infinitive, cross-reference to допомагати. https://slovnyk.me/dict/vts/допомогти
- U30: GRAC concordance `фамілія`, 5 lines: named surnames and theatrical surnames attest the competing colloquial reading; this does not make it the preferred neutral word.
- U31: `search_text`: Volkova/Maslo 2012, p.196, `morphology_s0195`, explains the copula; U10 supplies its present form.
- U32: Vashulenko 2019 grade 2 p.26, `2-klas-ukrmova-vashulenko-2019-1_s0024`, and Bolshakova 2019 p.27, `_s0027`: 33 letters and the sound/letter distinction.
- U34: `query_pravopys(topic="7")`: official Pravopys 2019 §7 pp.13-14, apostrophe after labials/r and its свято/цвях exceptions.
- U35: VTS `це`: identifying/emphatic particle as well as the form of цей; it need not be an agreeing noun modifier. https://slovnyk.me/dict/vts/це
- U36: VTS `до`, sense 1: direction toward a person, with genitive. https://slovnyk.me/dict/vts/до
- U37: VTS `приємно`: adverb/predicative; дуже приємно is the meeting formula. https://slovnyk.me/dict/vts/приємно
- U38: GRAC `здрастуйте`, two concordances, confirms greeting use.
- U39: Bolshakova 2019 grade 2 p.34, `2-klas-ukrmova-bolshakova-2019-1_s0034`: six vowel sounds and ten letters representing them.
- U41: Karaman 2018 grade 10 p.44, `10-klas-ukrmova-karaman-2018_s0080`: consonant classes 9+11+12; together with U39 this supports the course's 38-sound count.
- U42: Strokal 2021 p.265, `uni-ukrmova-orthography-strokal-2021_s0489`: question and exclamation punctuation. The melody choices are the explicitly requested first A1 models, not a claim that all discourse has one contour.
- U43: GRAC `снідати`, three concordances: past снідав and present снідає in actual contexts. The finale batch VESUM tags are `снідав: verb:imperf:past:m` and `снідаю: verb:imperf:pres:s:1`.
- U44: VTS `побачення`: до побачення is a fixed farewell. https://slovnyk.me/dict/vts/побачення
- U45: `verify_words` on 262 distinct lowercased full-completion tokens from 131 inline fill-ins, 234 found; deliberate malformed alternatives and proper-name case account for the rest. Reconstructed small-sign words also appear in K/U66.
- U49: VTS `муж`: bookish public figure, and archaic/solemn husband. Its existence is preserved; the ordinary-family-register task is checked against that restriction. https://slovnyk.me/dict/vts/муж
- U52: `search_style_guide(query="вірний")`, headword Вірний, правдивий, правильний, певний, слушний: style advice favors правильний for correctness.
- U53: The second Antonenko surface, `search_text` scoped to `antonenko-davydovych-yak-my-hovorymo`, p.51, `_p051`, provides the same distinction and permits exact/fidelity senses. It is considered together with U60, not used to erase its colloquial sense.
- U54: `search_style_guide(query="любий")` did not retrieve the relevant headword; no negative claim is based on that miss.
- U55: The second Antonenko surface, p.58, `_p058`: любий means dear/pleasant, not the unrestricted quantifier будь-який.
- U57: VTS `коричневий`: the brown color sense; no eye-color ban. https://slovnyk.me/dict/vts/коричневий
- U59: VTS `пів`: time construction на + ordinal, rare до + genitive. https://slovnyk.me/dict/vts/пів
- U60: VTS `вірний`, sense 2, labels correct/accurate colloquial and rare. This positive entry prevents treating it as nonexistent or universally invalid. https://slovnyk.me/dict/vts/вірний
- U61: VTS `любий`: dear/beloved is an attested adjective sense. https://slovnyk.me/dict/vts/любий
- U62: VTS `а`: contrast/comparison versus addition; both comparison and an additive і are possible without the new contrast cue. https://slovnyk.me/dict/vts/а
- U63: GRAC `коричневі очі`, three direct concordances: the exact competing eye-color phrase is attested.
- U65: VTS `карий`: dark brown, specifically of eyes. https://slovnyk.me/dict/vts/карий
- U66: `verify_words` on 28 correctly cased proper names/forms plus маленький, 28/28 found, including Богдане, Соломіє and Ліно.
- U67: VTS `привіт`: meeting salutation. https://slovnyk.me/dict/vts/привіт
- U68: VTS `склад` II sense 4: syllable in the phonetic teaching context. https://slovnyk.me/dict/vts/склад
- U69: Official Pravopys 2019 §26 pp.31-32: ь marks consonant softness.
- U70: Official Pravopys 2019 §74 p.109: vocative endings, including Соломіє; U66 gives the item-specific VESUM forms.
- U71: VTS `половина`: midpoint of an hour. The how-many key is the standard пів на + ordinal construction; morphology and requested standard register are considered together.
- U72: GRAC `Якого кольору`, three concordances, supports the question frame.

## Per-item verdicts

C means checked-clean in the original source. D means a confirmed second defensible answer in the original source, fixed here. Every row cites M plus usage locators where meaning/register decides. No key was changed. The repair detail for each D row follows the tables.

### 1. sounds-letters-and-hello

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | root | What is a звук? | A sound you hear and say | C | M01; U32/U39/U67/U68/U69/U44. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-1/1` | root | What is a лі́тера? | A letter you see and write | C | M01; U32/U39/U67/U68/U69/U44. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-1/2` | root | How many letters are in the Ukrainian alphabet? | 33 | C | M01; U32/U39/U67/U68/U69/U44. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-1/3` | root | How many basic Ukrainian vowel sounds are there? | 6 | C | M01; U32/U39/U67/U68/U69/U44. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-1/4` | root | Does ь have its own sound? | No | C | M01; U32/U39/U67/U68/U69/U44. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-1/5` | root | What does Приві́т mean? | Hi | C | M01; U32/U39/U67/U68/U69/U44. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-2/0` | root | What does склад mean? | syllable | C | M01; U32/U39/U67/U68/U69/U44. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-2/1` | root | What gives a склад its voice? | a vowel sound | C | M01; U32/U39/U67/U68/U69/U44. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-2/2` | root | What should you do with ма́ма today? | Notice the two clear а sounds. | C | M01; U32/U39/U67/U68/U69/U44. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-2/3` | root | What should you listen for in молоко́? | three clean о sounds | C | M01; U32/U39/U67/U68/U69/U44. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-4/0` | root | Which letter is the hard g sound? | Ґ | C | M01; U32/U39/U67/U68/U69/U44. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-4/1` | root | Which letter is always [йі]? | Ї | C | M01; U32/U39/U67/U68/U69/U44. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-4/2` | root | Which sign has no sound of its own? | Ь | C | M01; U32/U39/U67/U68/U69/U44. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-4/3` | root | Which letter is the clean [о] sound in молоко́? | О | C | M01; U32/U39/U67/U68/U69/U44. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-4/4` | root | In Приві́т, which two letters mark different vowel sounds? | И and І | C | M01; U32/U39/U67/U68/U69/U44. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-5/0` | root | ____! Як спра́ви? | Приві́т | C | M01; U32/U39/U67/U68/U69/U44. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-5/1` | root | ____. А у тебе́? | До́бре | C | M01; U32/U39/U67/U68/U69/U44. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-5/2` | root | Як тебе́ ____? | зва́ти | C | M01; U32/U39/U67/U68/U69/U44. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-5/3` | root | Мене́ ____ Анна. | зва́ти | C | M01; U32/U39/U67/U68/U69/U44. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-5/4` | root | До ____! | поба́чення | D, fixed | M01; U36/U44. До тебе is a grammatical directional phrase; the original line did not specify farewell. |
| `act-5/5` | root | На все ____! | до́бре | C | M01; U32/U39/U67/U68/U69/U44. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |

### 2. reading-ukrainian

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-5/0` | workbook | Склад — що це? | syllable | C | M02; U39/U68/U69. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-5/1` | workbook | Молоко́ — скільки складів? | 3 | C | M02; U39/U68/U69. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-5/2` | workbook | Яка літера завжди [йі]? | Ї | C | M02; U39/U68/U69. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |

### 3. special-signs

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | Буря́к — що відбувається перед літерою я? — Буря́к — what happens before the letter я? | Р пом'якшується перед я. — Р softens before я. | C | M03; U34/U69. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-1/1` | inline | Бур'я́н — що робить апо́строф? — Бур'я́н — what does the apostrophe do? | Р залишається твердим, потім чути [йа]. — Р remains hard, then [йа] is heard. | C | M03; U34/U69. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-1/2` | inline | Ї — що завжди правильно? — Ї — what is always true? | Завжди [йі]. — Always [йі]. | C | M03; U34/U69. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-3/0` | inline | сім___я | ' | C | M03; U34/U69. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-3/1` | inline | ден___ | ь | C | M03; U34/U69. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-3/2` | inline | п___ять | ' | C | M03; U34/U69. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `act-3/3` | inline | У слові свя́то правильний вибір — ___ . — In the word "свя́то", the correct choice is […]. | без знака — no sign | C | M03; U34/U69. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `workbook[4]/0` | workbook | бур___ян | ' | C | M03; U34/U69. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `workbook[4]/1` | workbook | комп___ютер | ' | C | M03; U34/U69. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `workbook[4]/2` | workbook | ім___я | ' | C | M03; U34/U69. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `workbook[4]/3` | workbook | У слові мален_кий потрібен ___ . — In the word "мален_кий", […] is needed. | ь | C | M03; U34/U69. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `workbook[4]/4` | workbook | У слові цвях правильний вибір — ___ . — In the word "цвях", the correct choice is […]. | без знака — no sign | C | M03; U34/U69. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `workbook[5]/0` | workbook | Сім'я́ — яка́ фо́рма пра́вильна? — Сім'я́ — which form is correct? | сім'я́ | C | M03; U34/U69. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `workbook[5]/1` | workbook | День — яка́ фо́рма пра́вильна? — День — which form is correct? | день | C | M03; U34/U69. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |
| `workbook[5]/2` | workbook | Сло́во без апо́строфа? — Which word is without an apostrophe? | свя́то | C | M03; U34/U69. The keyed sound, sign, spelling or greeting fits the stated task; competing options do not. |

### 4. stress-and-melody

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | Читай: ка́ва. Де на́голос? | перший склад | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `act-1/1` | inline | Читай: вода́. Де на́голос? | останній склад | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `act-1/2` | inline | Читай: столи́ця. Де на́голос? | середній склад | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `act-1/3` | inline | Молоко́: що робимо з ненаголошеними голосними? | тримаємо кожен голосни́й чистим | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `act-2/0` | inline | Це ка́ва. | спадна ↘ | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `act-2/1` | inline | Це ка́ва? | висхідна ↗ | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `act-2/2` | inline | Де метро́? | спадна ↘ | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `act-2/3` | inline | Як га́рно! | сильніша спадна ↘↘ | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `act-3/0` | inline | за́мок | castle | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `act-3/1` | inline | замо́к | lock | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `act-3/2` | inline | сім'я́ | family | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `act-4/0` | inline | (Statement, falling intonation) Це ка́ва___ | . | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `act-4/1` | inline | (Yes/no question, rising intonation) Це метро́___ | ? | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `act-4/2` | inline | (Where-question, falling intonation) Де апте́ка___ | ? | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `act-4/3` | inline | (Exclamation, emphatic falling intonation) Як га́рно___ | ! | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `act-4/4` | inline | (Statement, falling intonation) Так, це вода́___ | . | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `act-5/0` | inline | Це мій ___ комп'ютер. | нови́й | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `act-5/1` | inline | Мій дідусь ___. | стари́й | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `act-5/2` | inline | У мене ___ гривень. | одина́дцять | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `act-5/3` | inline | Я знаю ___ нових слів. | чотирна́дцять | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `act-5/4` | inline | Множина слова голова́: ___. | го́лови | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `act-5/5` | inline | Мене звати ___. | Марі́я | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `workbook[0]/0` | workbook | новий: ___ | нови́й | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `workbook[0]/1` | workbook | старий: ___ | стари́й | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `workbook[0]/2` | workbook | одинадцять: ___ | одина́дцять | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `workbook[0]/3` | workbook | чотирнадцять: ___ | чотирна́дцять | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `workbook[0]/4` | workbook | множина слова голова́: ___ | го́лови | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |
| `workbook[0]/5` | workbook | ім'я: ___ | Марі́я | C | M04; U42. The marked syllable, lexical sense or stated sentence type selects the key; number/sense fixes any homograph. |

### 5. who-am-i

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | Ти знайомишся з однокурсником свого віку. | Як тебе звати? | D, fixed | M05; U23. Equal age does not rule out polite вас; the cue now requests informal address. |
| `act-1/1` | inline | Ти знайомишся з незнайомим дорослим на орієнтації. | Як вас звати? | C | M05; U23/U37/U66/U67. The stated person, formal role, name frame or greeting function selects the key. |
| `act-1/2` | inline | Однокурсник питає твоє ім'я. Ти відповідаєш і повертаєш питання. | Мене звати Олена. А тебе? | D, fixed | M05; U23. A peer can be addressed politely; the requested register is now explicit. |
| `act-1/3` | inline | Викладач питає твоє ім'я. Ти відповідаєш і повертаєш питання. | Мене звати Петро. А вас? | C | M05; U23/U37/U66/U67. The stated person, formal role, name frame or greeting function selects the key. |
| `act-2/0` | inline | ___ звати Марко. | Мене | C | M05; U23/U37/U66/U67. The stated person, formal role, name frame or greeting function selects the key. |
| `act-2/1` | inline | Як ___ звати? | тебе | C | M05; U23/U37/U66/U67. The stated person, formal role, name frame or greeting function selects the key. |
| `act-2/2` | inline | Як ___ звати? | вас | C | M05; U23/U37/U66/U67. The stated person, formal role, name frame or greeting function selects the key. |
| `act-2/3` | inline | Дуже ___! | приємно | C | M05; U23/U37/U66/U67. The stated person, formal role, name frame or greeting function selects the key. |
| `act-2/4` | inline | Мене звати Олена. А ___? | тебе | C | M05; U23/U37/U66/U67. The stated person, formal role, name frame or greeting function selects the key. |
| `act-4/0` | inline | Мовець говорить про себе. | я | C | M05; U23/U37/U66/U67. The stated person, formal role, name frame or greeting function selects the key. |
| `act-4/1` | inline | Один друг або близький однокурсник. | ти | C | M05; U23/U37/U66/U67. The stated person, formal role, name frame or greeting function selects the key. |
| `act-4/2` | inline | Один незнайомий дорослий або формальна ситуація. | ви | C | M05; U23/U37/U66/U67. The stated person, formal role, name frame or greeting function selects the key. |
| `act-4/3` | inline | Жінка або дівчина вже відома в розмові. | вона | C | M05; U23/U37/U66/U67. The stated person, formal role, name frame or greeting function selects the key. |
| `workbook[3]/0` | workbook | Привіт! Як ___ звати? | тебе | D, fixed | M05; U23. A greeting alone does not fix the ти/ви relationship. |
| `workbook[3]/1` | workbook | Мене ___ Олена. | звати | C | M05; U23/U37/U66/U67. The stated person, formal role, name frame or greeting function selects the key. |
| `workbook[3]/2` | workbook | Мене звати Марко. ___ тебе? | А | C | M05; U23/U37/U66/U67. The stated person, formal role, name frame or greeting function selects the key. |
| `workbook[3]/3` | workbook | Добрий день! Як ___ звати? | вас | D, fixed | M05; U23. Добрий день can also precede informal address. |
| `workbook[3]/4` | workbook | Дуже ___! | приємно | C | M05; U23/U37/U66/U67. The stated person, formal role, name frame or greeting function selects the key. |
| `workbook[3]/5` | workbook | ___ ти? Я з Канади. | Звідки | C | M05; U23/U37/U66/U67. The stated person, formal role, name frame or greeting function selects the key. |
| `workbook[4]/0` | workbook | Це моя ___ Марія. | дружина | C | M05; U23/U37/U66/U67. The stated person, formal role, name frame or greeting function selects the key. |
| `workbook[4]/1` | workbook | ___, як вас звати? | Вибачте | C | M05; U23/U37/U66/U67. The stated person, formal role, name frame or greeting function selects the key. |
| `workbook[4]/2` | workbook | ___, дуже приємно! | Дякую | C | M05; U23/U37/U66/U67. The stated person, formal role, name frame or greeting function selects the key. |
| `workbook[4]/3` | workbook | Мені ___ приємно. | теж | C | M05; U23/U37/U66/U67. The stated person, formal role, name frame or greeting function selects the key. |
| `workbook[4]/4` | workbook | Оксана — ___. | інженерка | D, fixed | M05; U17. A masculine profession noun can refer to a woman; the target feminine form needs a cue. |
| `workbook[4]/5` | workbook | Це мій ___. | лікар | C | M05; U23/U37/U66/U67. The stated person, formal role, name frame or greeting function selects the key. |

### 6. my-family

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | Ти питаєш одного ровесника про брата. — You ask a peer about a brother. | У тебе є брат? | D, fixed | M06; U10. Це брат? also asks about a brother in a photo conversation; the new cue asks about possession. |
| `act-1/1` | inline | Ти відповідаєш так і кажеш, що маєш одну сестру. — You answer yes and say that you have one sister. | Так, у мене є одна сестра. | C | M06; U10/U49/U66. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-1/2` | inline | Ти відповідаєш ні короткою A1-фразою. — You answer no with a short A1 phrase. | Ні. | C | M06; U10/U49/U66. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-1/3` | inline | Ти питаєш, як його звати. — You ask what his name is. | Як його звати? | C | M06; U10/U49/U66. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-1/4` | inline | Ти показуєш маму на фото. — You point to mom in the photo. | Це моя мама. | C | M06; U10/U49/U66. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-1/5` | inline | Ти показуєш батьків. — You point to parents. | Це мої батьки. | C | M06; U10/U49/U66. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-3/0` | inline | ___ мене є брат. | У | C | M06; U10/U49/U66. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-3/1` | inline | У ___ є сестра. | мене | C | M06; U10/U49/U66. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-3/2` | inline | У ___ є брат? | тебе | D, fixed | M06; U10. У мене є брат? and У тебе є брат? are both grammatical possession questions. |
| `act-3/3` | inline | У ___ є діти? | вас | C | M06; U10/U49/U66. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-3/4` | inline | У мене є ___ брат. | один | C | M06; U10/U49/U66. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-3/5` | inline | У мене є ___ сестра. | одна | C | M06; U10/U49/U66. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-3/6` | inline | У мене є ___ брати. | два | C | M06; U10/U49/U66. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-3/7` | inline | У мене є ___ сестри. | дві | C | M06; U10/U49/U66. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-4/0` | inline | Це ___ брат. | мій | C | M06; U10/U49/U66. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-4/1` | inline | Це ___ мама. | моя | C | M06; U10/U49/U66. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-4/2` | inline | Це ___ місто. | моє | C | M06; U10/U49/U66. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-4/3` | inline | Це ___ батьки. | мої | C | M06; U10/U49/U66. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-4/4` | inline | Це ___ тато? | твій | C | M06; U10/U49/U66. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-4/5` | inline | Це ___ сестра? | твоя | C | M06; U10/U49/U66. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-4/6` | inline | Це ___ прізвище? | твоє | C | M06; U10/U49/U66. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-4/7` | inline | Це ___ родичі? | твої | C | M06; U10/U49/U66. The specified person, noun gender, number, case or family meaning selects the key. |
| `workbook[1]/0` | workbook | Моя ___ — вчителька. | дружина | C | M06; U10/U49/U66. The instruction requests ordinary family speech; the key fits. Marked archaic husband vocabulary is not the requested register. |
| `workbook[1]/1` | workbook | Мій ___ працює в лікарні. | чоловік | C | M06; U10/U49/U66. The instruction requests ordinary family speech; the key fits. Marked archaic husband vocabulary is not the requested register. |
| `workbook[1]/2` | workbook | Це моя ___ Тетяна. | бабуся | C | M06; U10/U49/U66. The instruction requests ordinary family speech; the key fits. Marked archaic husband vocabulary is not the requested register. |
| `workbook[1]/3` | workbook | У нас велика родина — близько десяти ___. | родичів | C | M06; U10/U49/U66. The instruction requests ordinary family speech; the key fits. Marked archaic husband vocabulary is not the requested register. |
| `workbook[1]/4` | workbook | Це ще маленька ___. | дитина | C | M06; U10/U49/U66. The instruction requests ordinary family speech; the key fits. Marked archaic husband vocabulary is not the requested register. |
| `workbook[1]/5` | workbook | Це мій ___ брат. | молодший | C | M06; U10/U49/U66. The instruction requests ordinary family speech; the key fits. Marked archaic husband vocabulary is not the requested register. |
| `workbook[1]/6` | workbook | Мій старший брат уже ___. | одружений | C | M06; U10/U49/U66. The instruction requests ordinary family speech; the key fits. Marked archaic husband vocabulary is not the requested register. |
| `workbook[4]/0` | workbook | Це ___ сім'я на фотографії. | моя | C | M06; U10/U49/U66. The specified person, noun gender, number, case or family meaning selects the key. |
| `workbook[4]/1` | workbook | ___ це? Це мій тато. | Хто | C | M06; U10/U49/U66. The specified person, noun gender, number, case or family meaning selects the key. |
| `workbook[4]/2` | workbook | Це моя сестра. ___ звати Катя. | Її | C | M06; U10/U49/U66. The specified person, noun gender, number, case or family meaning selects the key. |
| `workbook[4]/3` | workbook | Це мій брат. ___ звати Коля. | Його | C | M06; U10/U49/U66. The specified person, noun gender, number, case or family meaning selects the key. |
| `workbook[4]/4` | workbook | А це ___ бабуся? | твоя | C | M06; U10/U49/U66. The specified person, noun gender, number, case or family meaning selects the key. |

### 7. checkpoint-first-contact

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | Ти вітаєш ровесника на початку заняття. | Привіт! | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-1/1` | inline | Ти нейтрально вітаєш викладача або адміністратора. | Добрий день! | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-1/2` | inline | Ти називаєш своє ім'я. | Мене звати Олена. | D, fixed | M07; U10/U31. Overt є is a valid copula; an alternative grammatical identity sentence cannot be marked wrong. |
| `act-1/3` | inline | Ти кажеш, що ти студент. | Я студент. | D, fixed | M07; U10/U31. Overt є is a valid copula; an alternative grammatical identity sentence cannot be marked wrong. |
| `act-1/4` | inline | Ти кажеш свій вік. | Мені 20 років. | D, fixed | M07; U20. Мати with a numeral and рік is attested for age; Я маю 20 років is a defensible answer. |
| `act-1/5` | inline | Скільки літер в українській абетці? | 33 | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-1/6` | inline | Скільки звуків в українській мові? | 38 | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-1/7` | inline | Що робить м'який знак у слові день? | Пом'якшує попередній приголосний. | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-1/8` | inline | Яке написання з апострофом правильне? | сім'я | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-1/9` | inline | Де позначено наголос? | Приві́т | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-1/10` | inline | Ти додаєш одну родинну фразу. | У мене є мама і тато. | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-1/11` | inline | Ти ввічливо завершуєш перше знайомство. | Дуже приємно. До побачення! | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-3/0` | inline | Привіт! ___ звати Марко. | Мене | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-3/1` | inline | Моє ___ Коваленко. | прізвище | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-3/2` | inline | Я ___ Києва. | з | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-3/3` | inline | Я ___. | студент | D, fixed | M07; U10/U31. Overt є is a valid copula; an alternative grammatical identity sentence cannot be marked wrong. |
| `act-3/4` | inline | ___ 20 років. | Мені | D, fixed | M07; U20. Мати with a numeral and рік is attested for age; Я маю 20 років is a defensible answer. |
| `act-3/5` | inline | У мене ___ сестра. | є | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-3/6` | inline | Це ___ мама. | моя | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-3/7` | inline | Дуже ___ познайомитися! | приємно | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-4/0` | inline | Представлення імені | Мене звати Джон. | D, fixed | M07; U10/U31. Overt є is a valid copula; an alternative grammatical identity sentence cannot be marked wrong. |
| `act-4/1` | inline | Речення ідентичності | Я студент. | D, fixed | M07; U10/U31. Overt є is a valid copula; an alternative grammatical identity sentence cannot be marked wrong. |
| `act-4/2` | inline | Речення про вік | Мені 20 років. | D, fixed | M07; U20. Мати with a numeral and рік is attested for age; Я маю 20 років is a defensible answer. |
| `act-4/3` | inline | Пряме звертання | Привіт, Максиме! | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-4/4` | inline | Безпечне привітання | Добрий день! Мене звати Оксана. | D, fixed | M07; U12/U38. Здрастуйте is an attested Ukrainian greeting; replace it with an incorrect name case. |
| `act-4/5` | inline | Прізвище | Моє прізвище Сміт. | D, fixed | M07; U11/U30. Фамілія has an attested colloquial surname reading; no register distinction was requested. |
| `act-4/6` | inline | Прощання | До побачення! | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-4/7` | inline | Звичка до роду іменника | Вивчення слова разом із його родом | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-5/0` | inline | ___! Мене звати Богдан. | Привіт | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-5/1` | inline | Привіт, ___! Мене звати Соломія. | Богдане | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-5/2` | inline | Дуже приємно, ___. | Соломіє | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-5/3` | inline | ___ ти? Я з Дніпра. | Звідки | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-5/4` | inline | Моя майбутня ___ — вчителька. | професія | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-5/5` | inline | У мене є сестра. ___ звати Ірина. | Її | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-5/6` | inline | У мене є брат. ___ звати Назар. | Його | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-5/7` | inline | Дуже приємно ___! | познайомитися | D, fixed | M07; U28/U37. Допомогти also forms a meaningful infinitive construction; the new cue fixes the meeting meaning. |
| `act-6/0` | inline | Перший рядок: Привіт! Мене звати Богдан. | Привіт, Богдане! Мене звати Соломія. | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-6/1` | inline | Рядок: Дуже приємно, Соломіє. | Мені теж. Звідки ти? | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-6/2` | inline | Рядок: Я з Дніпра. А ти? | Я з Тернополя. | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `act-6/3` | inline | Рядок: У мене є брат. | Дуже приємно. До побачення! | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `workbook[0]/0` | workbook | Мене звати Олена. | My name is Olena. | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `workbook[0]/1` | workbook | Моє прізвище Мельник. | My surname is Melnyk. | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `workbook[0]/2` | workbook | Я з Канади. | I am from Canada. | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `workbook[0]/3` | workbook | Я студентка. | I am a female student. | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `workbook[0]/4` | workbook | У мене є сестра. | I have a sister. | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `workbook[0]/5` | workbook | Мені теж. | Me too. | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `workbook[2]/0` | workbook | ___! Мене звати Ліна. | Привіт | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `workbook[2]/1` | workbook | Я ___ Одеси. | з | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `workbook[2]/2` | workbook | Привіт, ___! | Ліно | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `workbook[2]/3` | workbook | Дуже ___! | приємно | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |
| `workbook[2]/4` | workbook | Мені ___. | теж | C | M07; U10/U20/U32/U34/U37/U39/U41/U66/U70. The stated communication function, agreement, case, spelling or English gloss selects the key. |

### 8. things-have-gender

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | та́то (dad) | Хто це? | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-1/1` | inline | стіл (table) | Що це? | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-1/2` | inline | сестра́ (sister) | вона́ | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-1/3` | inline | брат (brother) | він | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-1/4` | inline | кни́га (book) | вона́ | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-1/5` | inline | вікно́ (window) | воно́ | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-3/0` | inline | стіл (table) | він | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-3/1` | inline | кни́га (book) | вона́ | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-3/2` | inline | вікно́ (window) | воно́ | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-3/3` | inline | ба́тько (father) | він | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-3/4` | inline | сестра́ (sister) | вона́ | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-3/5` | inline | мі́сто (city) | воно́ | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-3/6` | inline | та́то (dad) | він | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-3/7` | inline | Мико́ла (Mykola - male name) | він | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-5/0` | inline | стіл закі́нчується на при́голосний. — "Стіл" ends in a consonant. | він / мій | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-5/1` | inline | брат закі́нчується на при́голосний. — "Брат" ends in a consonant. | він / мій | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-5/2` | inline | кни́га закі́нчується на -а. — "Кни́га" ends in -а. | вона́ / моя́ | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-5/3` | inline | сестра́ закі́нчується на -а. — "Сестра́" ends in -а. | вона́ / моя́ | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-5/4` | inline | вікно́ закі́нчується на -о. — "Вікно́" ends in -о. | воно́ / моє́ | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-5/5` | inline | мі́сто закі́нчується на -о. — "Мі́сто" ends in -о. | воно́ / моє́ | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-4/0` | inline | Це ___ стіл. | мій | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-4/1` | inline | Це ___ кни́га. | моя́ | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-4/2` | inline | Це ___ вікно́. | моє́ | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-4/3` | inline | Це ___ кімна́та. | моя́ | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-4/4` | inline | Це ___ лі́жко. | моє́ | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-4/5` | inline | Це ___ телефо́н. | мій | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-4/6` | inline | Це ___ ру́чка. | моя́ | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-4/7` | inline | Це ___ фо́то. | моє́ | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-9/0` | inline | She is a teacher. | Вона́ вчи́телька. | D, fixed | M08; U17. Masculine profession nouns can describe women; the new cue specifically requests a feminine noun. |
| `act-9/1` | inline | She is a doctor. | Вона́ лі́карка. | D, fixed | M08; U17. Masculine profession nouns can describe women; the new cue specifically requests a feminine noun. |
| `act-9/2` | inline | He is a student. | Він студе́нт. | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-9/3` | inline | She is an actor. | Вона́ акто́рка. | D, fixed | M08; U17. Masculine profession nouns can describe women; the new cue specifically requests a feminine noun. |
| `act-w3/0` | workbook | ___ мене́ є стіл. | У | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-w3/1` | workbook | У мене́ ___ кни́га. | є | D, fixed | M08; U10. У мене моя книга is a valid possession statement; it competes with the keyed existential sentence. |
| `act-w3/2` | workbook | У ___ є телефо́н? | тебе́ | D, fixed | M08; U10. У мене є телефон? and У тебе є телефон? are both valid possession questions. |
| `act-w3/3` | workbook | У мене́ є ___. | вікно́ | D, fixed | M08; U10. Він can be a nominative subject of є; the original open sentence did not fix the possessed object. |
| `act-w3/4` | workbook | Де стіл? ___ тут. | Він | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-w3/5` | workbook | Де кни́га? ___ тут. | Вона́ | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-w3/6` | workbook | Де вікно́? ___ там. | Воно́ | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-w5/0` | workbook | Яки́й у мене́ си́льний біль у плечі́! — What severe pain I have in my shoulder! | він | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-w5/1` | workbook | Украї́нський степ широ́кий і ві́тряний. — The Ukrainian steppe is wide and windy. | він | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-w5/2` | workbook | Цей ро́зпис на стіні́ — робо́та украї́нського худо́жника. — This mural on the wall is the work of a Ukrainian artist. | він | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-w5/3` | workbook | Да́вній літо́пис розповіда́є про Ки́ївську Русь. — An ancient chronicle tells about Kyivan Rus. | він | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |
| `act-w5/4` | workbook | Кни́жне / урочи́сте: у дале́ку путь. — Bookish / solemn: on a long journey. | вона́ | C | M08; U10/U17. The specified person, noun gender, number, case or family meaning selects the key. |

### 9. what-is-it-like

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | стіл | Який? | C | M09; U10/U52/U53/U55/U60/U61/U62. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/1` | inline | книга | Яка? | C | M09; U10/U52/U53/U55/U60/U61/U62. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/2` | inline | фото | Яке? | C | M09; U10/U52/U53/U55/U60/U61/U62. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/3` | inline | кімната | Яка? | C | M09; U10/U52/U53/U55/U60/U61/U62. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/4` | inline | книги | Які? | C | M09; U10/U52/U53/U55/U60/U61/U62. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/5` | inline | вікно | Яке? | C | M09; U10/U52/U53/U55/U60/U61/U62. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/0` | inline | велик__ стіл | ий | C | M09; U10/U52/U53/U55/U60/U61/U62. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/1` | inline | нов__ книга | а | C | M09; U10/U52/U53/U55/U60/U61/U62. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/2` | inline | чист__ вікно | е | C | M09; U10/U52/U53/U55/U60/U61/U62. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/3` | inline | стар__ фото | е | C | M09; U10/U52/U53/U55/U60/U61/U62. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/4` | inline | дорог__ телефон | ий | C | M09; U10/U52/U53/U55/U60/U61/U62. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/5` | inline | дешев__ листівка | а | C | M09; U10/U52/U53/U55/U60/U61/U62. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/6` | inline | гарн__ кімната | а | C | M09; U10/U52/U53/U55/U60/U61/U62. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/7` | inline | брудн__ дзеркало | е | C | M09; U10/U52/U53/U55/U60/U61/U62. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/8` | inline | світл__ плакат | ий | C | M09; U10/U52/U53/U55/U60/U61/U62. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/9` | inline | нов__ книги | і | C | M09; U10/U52/U53/U55/U60/U61/U62. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[0]/0` | workbook | The book is new. | Книга нова. | D, fixed | M09; U10. The overt-copula translation is grammatical as well as the keyed zero-copula translation. |
| `workbook[0]/1` | workbook | The table is clean. | Стіл чистий. | D, fixed | M09; U10. The overt-copula translation is grammatical as well as the keyed zero-copula translation. |
| `workbook[0]/2` | workbook | The window is big. | Вікно велике. | C | M09; U10/U52/U53/U55/U60/U61/U62. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[0]/3` | workbook | A nice postcard | гарна листівка | C | M09; U10/U52/U53/U55/U60/U61/U62. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[0]/4` | workbook | A useful atlas | корисний атлас | C | M09; U10/U52/U53/U55/U60/U61/U62. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[0]/5` | workbook | Interesting things | цікаві речі | C | M09; U10/U52/U53/U55/U60/U61/U62. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[1]/0` | workbook | Моя кімната ___ і світла. | маленька | C | M09; U10/U52/U53/U55/U60/U61/U62. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[1]/1` | workbook | Стіл ___ і чистий. | новий | C | M09; U10/U52/U53/U55/U60/U61/U62. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[1]/2` | workbook | Ліжко старе, ___ зручне. | але | C | M09; U10/U52/U53/U55/U60/U61/U62. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[1]/3` | workbook | Вікно ___ і чисте. | велике | C | M09; U10/U52/U53/U55/U60/U61/U62. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[1]/4` | workbook | Книга дорога, ___ листівка дешева. | а | D, fixed | M09; U62. Both а and і can join the clauses; the cue now requests contrast. |
| `workbook[1]/5` | workbook | У мене є ___ стіл і стара лампа. | новий | C | M09; U10/U52/U53/U55/U60/U61/U62. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[3]/0` | workbook | Цей суп дуже ___. | смачний | C | M09; U10/U52/U53/U55/U60/U61/U62. The standard A1 adjective and its stated meaning fit; morphology alone is not used to condemn the other word. |
| `workbook[3]/1` | workbook | У мене є ___ олівець. | жовтий | C | M09; U10/U52/U53/U55/U60/U61/U62. The standard A1 adjective and its stated meaning fit; morphology alone is not used to condemn the other word. |
| `workbook[3]/2` | workbook | У сусідки ___ кіт. | чорний | C | M09; U10/U52/U53/U55/U60/U61/U62. The standard A1 adjective and its stated meaning fit; morphology alone is not used to condemn the other word. |
| `workbook[3]/3` | workbook | Прапор ___, а не білий. | червоний | C | M09; U10/U52/U53/U55/U60/U61/U62. The standard A1 adjective and its stated meaning fit; morphology alone is not used to condemn the other word. |
| `workbook[3]/4` | workbook | Це ___ фільм. | поганий | C | M09; U10/U52/U53/U55/U60/U61/U62. The standard A1 adjective and its stated meaning fit; morphology alone is not used to condemn the other word. |
| `workbook[3]/5` | workbook | Це ___ відповідь на запитання. | правильна | D, fixed | M09; U52/U53/U60. VTS admits a colloquial rare correct/accurate sense of вірний; a style preference alone does not make the alternative impossible. |
| `workbook[3]/6` | workbook | Дай мені, будь ласка, ___ олівець. | будь-який | D, fixed | M09; U54/U55/U61. Любий can mean dear/beloved; without an any cue both adjective meanings are defensible. |
| `workbook[3]/7` | workbook | Сергій — ___ хлопчик. | розумний | C | M09; U10/U52/U53/U55/U60/U61/U62. The standard A1 adjective and its stated meaning fit; morphology alone is not used to condemn the other word. |
| `workbook[3]/8` | workbook | Тарас — ___ учень. | лінивий | C | M09; U10/U52/U53/U55/U60/U61/U62. The standard A1 adjective and its stated meaning fit; morphology alone is not used to condemn the other word. |

### 10. colors

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | You point to a pencil and ask its color. | Якого кольору олівець? | D, fixed | M10; U10. The version with є remains a grammatical question about color. |
| `act-1/1` | inline | Якого кольору светр? | Синій. | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/2` | inline | Якого кольору ручка? | Червона. | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/3` | inline | Якого кольору вікно? | Біле. | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/4` | inline | Якого кольору соняшники? | Жовті. | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/5` | inline | Якого кольору прапор України? | Синьо-жовтий. | D, fixed | M10; U18. GRAC attests блакитно-жовті прапори for Ukrainian flags; the shade synonym is a defensible description. |
| `act-1/6` | inline | Якого кольору ваза? | Синя. | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/7` | inline | Якого кольору листя? | Зелене. | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/0` | inline | червон__ олівець | ий | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/1` | inline | червон__ ручка | а | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/2` | inline | червон__ яблуко | е | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/3` | inline | біл__ светр | ий | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/4` | inline | біл__ сорочка | а | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/5` | inline | сір__ пальто | е | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/6` | inline | зелен__ зошит | ий | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/7` | inline | рожев__ листівка | а | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/8` | inline | син__ книга | я | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/9` | inline | син__ вікно | є | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-4/0` | inline | A clear sky | блакитне небо | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-4/1` | inline | The Ukrainian flag | синьо-жовтий прапор | D, fixed | M10; U18. The flag phrase admits the light-blue synonym; color alternatives now differ from the target colors. |
| `act-4/2` | inline | A dark blue sweater | синій светр | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-4/3` | inline | A light-blue postcard | блакитна листівка | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-4/4` | inline | Deep water | синє море | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-4/5` | inline | A notebook that is dark green | темно-зелений зошит | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[2]/0` | workbook | Моя кімната ___. | біла | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[2]/1` | workbook | Стіл ___. | коричневий | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[2]/2` | workbook | Пальто ___. | сіре | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[2]/3` | workbook | У мене ___ светр. | синій | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[2]/4` | workbook | У неї ___ очі. | карі | D, fixed | M10; U57/U63/U65. GRAC directly attests коричневі очі; карі is the target word, not the only defensible description. |
| `workbook[2]/5` | workbook | У нього ___ волосся. | русяве | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[2]/6` | workbook | У бабусі ___ волосся. | сиве | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[2]/7` | workbook | Це ___ небо. | блакитне | C | M10; U18/U57/U63/U65/U72. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |

### 11. how-many

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | 0 | нуль | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `act-1/1` | inline | one pencil | один олівець | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `act-1/2` | inline | one pen | одна ручка | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `act-1/3` | inline | one pastry | одне тістечко | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `act-1/4` | inline | two pencils | два олівці | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `act-1/5` | inline | two pens | дві ручки | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `act-4/0` | inline | Мені двадцять один ___. | рік | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `act-4/1` | inline | Моїй сестрі двадцять чотири ___. | роки | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `act-4/2` | inline | Мені двадцять п'ять ___. | років | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `act-4/3` | inline | Їй вісімнадцять ___. | років | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `act-4/4` | inline | Бабусі вісімдесят ___. | років | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `act-4/5` | inline | Скільки тобі ___? | років | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `act-5/0` | inline | нуль дев'яносто сім = ___ | 097 | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `act-5/1` | inline | сорок п'ять = ___ | 45 | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `act-5/2` | inline | шістдесят сім = ___ | 67 | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `act-5/3` | inline | три два один = ___ | 321 | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `workbook[0]/0` | workbook | 5 = ___ | п'ять | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `workbook[0]/1` | workbook | 6 = ___ | шість | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `workbook[0]/2` | workbook | 7 = ___ | сім | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `workbook[0]/3` | workbook | 15 = ___ | п'ятнадцять | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `workbook[0]/4` | workbook | 17 = ___ | сімнадцять | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `workbook[0]/5` | workbook | 18 = ___ | вісімнадцять | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `workbook[0]/6` | workbook | 20 = ___ | двадцять | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `workbook[0]/7` | workbook | 47 = ___ | сорок сім | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `workbook[0]/8` | workbook | 50 = ___ | п'ятдесят | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `workbook[0]/9` | workbook | 90 = ___ | дев'яносто | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `workbook[3]/0` | workbook | У мене ___ книг. | п'ять | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `workbook[3]/1` | workbook | У нашій групі ___ студентів. | шість | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `workbook[3]/2` | workbook | На поличці ___ книжок. | сім | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `workbook[3]/3` | workbook | На картці ___ гривень. | сімнадцять | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `workbook[3]/4` | workbook | Мамі ___ років. | п'ятдесят | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `workbook[3]/5` | workbook | Дідусеві ___ років. | дев'яносто | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `workbook[3]/6` | workbook | Зараз ___. | пів на шосту | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `workbook[3]/7` | workbook | Чай коштує дві ___. | гривні | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |
| `workbook[3]/8` | workbook | Кава коштує сімдесят ___. | гривень | C | M11; U59/U71. The given number/dictation or numeral-governed noun form selects the key. |

### 12. this-and-that

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | стіл | цей стіл | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `act-1/1` | inline | книга | ця книга | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `act-1/2` | inline | вікно | це вікно | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `act-1/3` | inline | радіо | це радіо | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `act-1/4` | inline | телефон | цей телефон | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `act-1/5` | inline | сумка | ця сумка | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `act-1/6` | inline | рюкзак | цей рюкзак | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `act-1/7` | inline | дерево | це дерево | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `act-2/0` | inline | ___ книга нова, а та — стара. | Ця | D, fixed | M12; U10/U35. Це allows an identifying sentence rather than an agreeing modifier; replace that alternative parse. |
| `act-2/1` | inline | Ця книга нова, а ___ — стара. | та | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `act-2/2` | inline | ___ сумка червона, а та — синя. | Ця | D, fixed | M12; U10/U35. Це allows an identifying sentence rather than an agreeing modifier; replace that alternative parse. |
| `act-2/3` | inline | Ця сумка червона, а ___ — синя. | та | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `act-2/4` | inline | ___ стіл новий, а той — старий. | Цей | D, fixed | M12; U10/U35. Це allows an identifying sentence rather than an agreeing modifier; replace that alternative parse. |
| `act-2/5` | inline | Цей стіл новий, а ___ — старий. | той | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `act-2/6` | inline | ___ вікно велике, а те — маленьке. | Це | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `act-2/7` | inline | Це вікно велике, а ___ — маленьке. | те | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `act-4/0` | inline | that table over there | той стіл | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `act-4/1` | inline | that book over there | та книга | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `act-4/2` | inline | that window over there | те вікно | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `act-4/3` | inline | those pens over there | ті ручки | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `act-4/4` | inline | that phone over there | той телефон | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `act-4/5` | inline | that bag over there | та сумка | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `act-5/0` | inline | Fix the sentence: Це є цікава книга. | Це цікава книга. | D, fixed | M12; U10. The original sentence with є is grammatical; the cue now requests the taught zero-copula pattern. |
| `act-5/1` | inline | Fix the sentence: Я хочу купити цей сумку. | Я хочу купити цю сумку. | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `act-5/2` | inline | Fix the sentence: Ця біль у спині сильна. | Цей біль у спині сильний. | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `act-5/3` | inline | Fix the code-switching: Что это? — Это стіл. | Що це? — Це стіл. | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `act-5/4` | inline | Choose the unambiguous variant. | У кімнаті є та книга і ручка. | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `workbook[0]/0` | workbook | Which table, this one or that one? | Який стіл — цей чи той? | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `workbook[0]/1` | workbook | Which bag, this red one or that blue one? | Яка сумка — ця червона чи та синя? | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `workbook[0]/2` | workbook | Which window, this big one or that small one? | Яке вікно — це велике чи те маленьке? | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `workbook[0]/3` | workbook | Which pens, these blue ones or those green ones? | Які ручки — ці сині чи ті зелені? | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `workbook[0]/4` | workbook | Make the list clearer. | У кімнаті є та книга і ручка. | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `workbook[0]/5` | workbook | Which phone, this one or that one? | Який телефон — цей чи той? | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `workbook[1]/0` | workbook | Я хочу ___ книгу. | цю | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `workbook[1]/1` | workbook | Я хочу ___ сумку. | цю | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `workbook[1]/2` | workbook | ___ книга цікава. | Ця | D, fixed | M12; U10/U35. Це allows an identifying sentence rather than an agreeing modifier; replace that alternative parse. |
| `workbook[1]/3` | workbook | ___ мій стіл. | Це | D, fixed | M12; U10/U35. Це є мій стіл and Цей є мій стіл are grammatical alternatives to the keyed identification. |
| `workbook[1]/4` | workbook | ___ ця книга тут. | Ось | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `workbook[1]/5` | workbook | Той стіл ___. | там | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `workbook[1]/6` | workbook | ___ ручки сині. | Ці | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |
| `workbook[1]/7` | workbook | ___ телефони чорні. | Ті | C | M12; U10/U35. The requested pointing phrase, near/far contrast, case or explicitly clearer conjunction selects the key. |

### 13. many-things

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | стіл → ___ | столи | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/1` | inline | книга → ___ | книги | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/2` | inline | вікно → ___ | вікна | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/3` | inline | стілець → ___ | стільці | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/4` | inline | зошит → ___ | зошити | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/5` | inline | ручка → ___ | ручки | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/6` | inline | сумка → ___ | сумки | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/7` | inline | лампа → ___ | лампи | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/8` | inline | крісло → ___ | крісла | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/9` | inline | дзеркало → ___ | дзеркала | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/0` | inline | стіл | столи | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/1` | inline | книга | книги | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/2` | inline | вікно | вікна | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/3` | inline | стілець | стільці | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/4` | inline | телефон | телефони | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/5` | inline | зошит | зошити | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/6` | inline | ручка | ручки | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/7` | inline | крісло | крісла | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-3/0` | inline | нов__ книги | і | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-3/1` | inline | велик__ столи | і | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-3/2` | inline | чист__ вікна | і | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-3/3` | inline | син__ зошити | і | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-3/4` | inline | червон__ ручки | і | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-3/5` | inline | жовт__ лампи | і | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-3/6` | inline | стар__ стільці | і | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-3/7` | inline | чорн__ сумки | і | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[1]/0` | workbook | These tables are big. | Ці столи великі. | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[1]/1` | workbook | Those chairs are old. | Ті стільці старі. | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[1]/2` | workbook | My notebooks are blue. | Мої зошити сині. | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[1]/3` | workbook | Which pens? | Які ручки? | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[1]/4` | workbook | These books are new. | Ці книги нові. | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[1]/5` | workbook | Which bags are small? | Які сумки маленькі? | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[2]/0` | workbook | ці велик__ столи | і | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[2]/1` | workbook | ті стар__ стільці | і | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[2]/2` | workbook | мої син__ зошити | і | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[2]/3` | workbook | ці чист__ вікна | і | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[2]/4` | workbook | ті жовт__ лампи | і | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[2]/5` | workbook | мої чорн__ сумки | і | C | M13; U10. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |

### 14. checkpoint-my-world

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | стіл | великий стіл | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/1` | inline | книга | нова книга | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/2` | inline | вікно | чисте вікно | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/3` | inline | лампа | біла лампа | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/4` | inline | зошит | синій зошит | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/5` | inline | сумка | чорна сумка | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/6` | inline | крісло | нове крісло | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/7` | inline | книги | нові книги | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/8` | inline | ручки | червоні ручки | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-1/9` | inline | вікна | чисті вікна | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/0` | inline | ___ вишиванка біла. | Ця | D, fixed | M14; U10/U35. Це allows the identifying reading 'This is a white embroidered shirt'. |
| `act-2/1` | inline | ___ глечик старий. | Той | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/2` | inline | ___ намисто коштує сто гривень. | Це | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/3` | inline | ___ писанки червоні. | Ці | D, fixed | M14; U10/U35. Це allows the identifying reading 'These are red decorated eggs'. |
| `act-2/4` | inline | Ця сумка ___. | червона | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/5` | inline | Той зошит ___ двадцять гривень. | коштує | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/6` | inline | ___ гривень. | Двісті | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-2/7` | inline | Один зошит коштує ___ гривень. | двадцять | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-4/0` | inline | Ця книга нова. | Ці книги нові. | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-4/1` | inline | Цей стіл великий. | Ці столи великі. | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-4/2` | inline | Це вікно чисте. | Ці вікна чисті. | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-4/3` | inline | Ця ручка синя. | Ці ручки сині. | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-4/4` | inline | Та сумка чорна. | Ті сумки чорні. | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-4/5` | inline | Той стілець старий. | Ті стільці старі. | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-4/6` | inline | Мій зошит синій. | Мої зошити сині. | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `act-4/7` | inline | Яка ручка? | Які ручки? | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[0]/0` | workbook | ___ стіл | мій стіл | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[0]/1` | workbook | ___ лампа | моя лампа | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[0]/2` | workbook | ___ вікно | моє вікно | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[0]/3` | workbook | ___ книги | мої книги | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[1]/0` | workbook | Це ___ кімната. | моя | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[1]/1` | workbook | Мій стіл ___. | великий | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[1]/2` | workbook | Моє вікно ___. | чисте | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[1]/3` | workbook | Ці книги ___. | нові | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[1]/4` | workbook | Та сумка ___. | синя | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[1]/5` | workbook | Один зошит коштує двадцять ___. | гривень | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[3]/0` | workbook | Мій книга. | Моя книга. | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[3]/1` | workbook | Цей лампа. | Ця лампа. | D, fixed | M14; U10/U35. Це лампа is a valid identifying sentence; the target agreeing phrase needs a distinct distractor. |
| `workbook[3]/2` | workbook | Великий вікно. | Велике вікно. | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[3]/3` | workbook | Ці книга. | Ці книги. | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[3]/4` | workbook | Ті зошит. | Ті зошити. | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |
| `workbook[3]/5` | workbook | Двадцять гривня. | Двадцять гривень. | C | M14; U10/U35. The requested noun/adjective agreement, number, color sense, price or plural transformation selects the key. |

### 15. a1-finale

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | Зранку я ___ у кафе. | снідав | D, fixed | M15; U9/U43. Зранку denotes morning, not past tense; present habitual and future readings are defensible without a tense cue. |

## Confirmed defects and exact repairs

| Item | Evidence | Repair, with key retained |
| --- | --- | --- |
| `sounds-letters-and-hello/act-5/4` | U36, U44 | sentence: (Saying goodbye) До ____! |
| `who-am-i/act-1/0` | U23 | prompt: Ти знайомишся з однокурсником свого віку. (Use informal address.) |
| `who-am-i/act-1/2` | U23 | prompt: Однокурсник питає твоє ім'я. Ти відповідаєш і повертаєш питання. (Use informal address.) |
| `who-am-i/workbook[3]/0` | U23 | sentence: (Use informal address.) Привіт! Як ___ звати? |
| `who-am-i/workbook[3]/3` | U23 | sentence: (Use formal address.) Добрий день! Як ___ звати? |
| `who-am-i/workbook[4]/4` | U17 | sentence: (Use the feminine profession noun.) Оксана — ___. |
| `my-family/act-1/0` | U10 | prompt: Ти питаєш одного ровесника, чи є в нього брат. — You ask a peer whether they have a brother. |
| `my-family/act-3/2` | U10 | option 1: мене → мій |
| `checkpoint-first-contact/act-1/2` | U10, U31 | option 1: Моє ім'я є Олена. → Мій ім'я Олена. |
| `checkpoint-first-contact/act-1/3` | U10, U31 | option 1: Я є студент. → Я студенти. |
| `checkpoint-first-contact/act-3/3` | U10, U31 | option 1: є студент → студенти |
| `checkpoint-first-contact/act-4/0` | U10, U31 | option 1: Моє ім'я є Джон. → Мій ім'я Джон. |
| `checkpoint-first-contact/act-4/1` | U10, U31 | option 1: Я є студент. → Я студенти. |
| `checkpoint-first-contact/act-1/4` | U20 | option 1: Я маю 20 років. → Мені 20 роки. |
| `checkpoint-first-contact/act-3/4` | U20 | option 1: Я маю → Моє |
| `checkpoint-first-contact/act-4/2` | U20 | option 1: Я маю 20 років. → Мені 20 роки. |
| `checkpoint-first-contact/act-4/4` | U12, U38 | option 1: Здрастуйте! Мене звати Оксана. → Добрий день! Мене звати Оксану. |
| `checkpoint-first-contact/act-4/5` | U11, U30 | option 1: Моя фамілія Сміт. → Мій прізвище Сміт. |
| `checkpoint-first-contact/act-5/7` | U28, U37 | sentence: (Greeting a new classmate: nice to meet you.) Дуже приємно ___! |
| `things-have-gender/act-9/0` | U17 | prompt: She is a teacher. (Use the feminine profession noun.) |
| `things-have-gender/act-9/1` | U17 | prompt: She is a doctor. (Use the feminine profession noun.) |
| `things-have-gender/act-9/3` | U17 | prompt: She is an actor. (Use the feminine profession noun.) |
| `things-have-gender/act-w3/1` | U10 | option 2: моя́ → мій |
| `things-have-gender/act-w3/2` | U10 | option 1: мене́ → ми |
| `things-have-gender/act-w3/3` | U10 | sentence: (I have a window.) У мене́ є ___. |
| `what-is-it-like/workbook[0]/0` | U10 | option 1: Книга є нова. → Книга нове. |
| `what-is-it-like/workbook[0]/1` | U10 | option 2: Стіл є чистий. → Стіл чисте. |
| `what-is-it-like/workbook[1]/4` | U62 | sentence: (Contrast: whereas.) Книга дорога, ___ листівка дешева. |
| `what-is-it-like/workbook[3]/5` | U52, U53, U60 | option 1: вірна → правильний |
| `what-is-it-like/workbook[3]/6` | U54, U55, U61 | sentence: (Any pencil, with no particular preference.) Дай мені, будь ласка, ___ олівець. |
| `colors/act-1/0` | U10 | option 2: Якого кольору є олівець? → Якої кольору олівець? |
| `colors/act-1/5` | U18 | option 1: Блакитно-жовтий. → Червоно-жовтий. |
| `colors/act-4/1` | U18 | option 1: блакитно-жовтий прапор → червоно-жовтий прапор; option 2: голубо-жовтий прапор → зелено-жовтий прапор |
| `colors/workbook[2]/4` | U57, U63, U65 | option 1: коричневі → коричнева |
| `this-and-that/act-2/0` | U10, U35 | option 2: Це → Ці |
| `this-and-that/act-2/2` | U10, U35 | option 2: Це → Ці |
| `this-and-that/act-2/4` | U10, U35 | option 2: Це → Ці |
| `this-and-that/workbook[1]/2` | U10, U35 | option 1: Це → Ці |
| `this-and-that/act-5/0` | U10 | prompt: Say 'This is an interesting book' without using є.; explanation: The requested pattern omits є. The version with є is also grammatical. |
| `this-and-that/workbook[1]/3` | U10, U35 | option 1: Це є → Ці; option 2: Цей є → Ця |
| `checkpoint-my-world/act-2/0` | U10, U35 | option 2: Це → Ці |
| `checkpoint-my-world/act-2/3` | U10, U35 | option 2: Це → Цей |
| `checkpoint-my-world/workbook[3]/1` | U10, U35 | option 2: Це лампа. → Ці лампа. |
| `a1-finale/act-1/0` | U9, U43 | sentence: (Past tense, male speaker.) Учора зранку я ___ у кафе.; explanation: Учора and the past-tense cue fix a past morning; the male-speaker cue selects снідав. |

## Validation and batch sizing

- Structural scanner: `scripts/audit/scan_activity_errors.py --track a1-v1`, 55/55 files, zero findings, exit 0 before and after changes.
- Existing affected checks: `pytest -n 2 tests/test_scan_activity_errors.py tests/test_a1_activity_schema_parser_drift.py tests/test_yaml_activities_a1_payload.py tests/test_activity_renderer.py tests/test_generate_mdx.py tests/test_generate_mdx_parsers.py tests/test_generate_mdx_unit_map.py tests/test_generate_mdx_v7_resources_vocab.py tests/test_curriculum_manifest_canary.py`: 329 passed in 10.43 seconds. No new test case was added.
- The existing ActivityParser, `yaml_activities_to_jsx` and `dump_json_for_jsx` regenerated only the 44 changed page item objects. Unchanged source objects and page bytes outside those serialized objects are preserved. Existing unaccented generated-page conventions are preserved; English cues are retained. The integrity manifest changes exactly the 10 source and 10 generated-page hashes.
- Source matching detected pre-existing page/source differences, including stripped stress marks and an omitted bilingual suffix. Matching accounts for those representations, while replacements come from the source parser. This is not evidence that every archived page equals its YAML.
- Chromium exercised the actual tracked MDX payloads in the existing QuizQuestion and FillInQuestion components: 44/44 correct choices accepted, 44/44 wrong choices rejected, zero browser errors. The runtime was copied into this worktree after its lockfile matched the primary checkout.
- Independent Gemini via AGY and Opus 5.5 via Claude Code review, browser proof, and CI/merge receipts are recorded on the PR at its exact pushed head. This audit document records the author pass; it is not a claim of independent approval or of deployment.

The full section census matters for sizing: the first inline/root-only extraction had 293 items; workbook discovery added 154. The final denominator is 447. The source inventory started at 2026-10-28T16:54:45.782236+00:00. The author pass/report was prepared at 2026-10-28T17:18:44.793868+00:00. This elapsed interval includes rule reading, inventory correction, Sources retries after a temporary outage, source analysis, patches and local validation; it is not pure model throughput. At this item density the 55-module issue is a multi-batch job. Multiplying this batch by 55/14 is only a planning estimate because later modules have different item counts and harder usage questions. The CTO should size the next batch by counted items in all sections, not by the issue's rough 48-items-per-module estimate.

Residual owner: CTO curriculum coordinator, #8893. The remaining modules, unchecked activity types, all other finale items, independent broader evaluation and production delivery remain outside this slice.

At the end of author validation, the measured wall interval was 27.5 minutes for 447 items across 14 full modules plus one finale item. Straight-line module scaling gives approximately 108 minutes for 55 modules, before independent review and CI. This is a planning estimate with the limits above, not a measured full-track completion time.
