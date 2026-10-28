# A1-v1 language pass, manifest modules 29 through 42

Refs #8893. Source snapshot: `0ab9b6b1dd455c090c251dd2f07e52bc2e73e717`.

This is one bounded Method step 2 slice. It checks all 326 fill-in and quiz items in both inline/root and workbook sections of manifest modules 29-42, including 57 workbook items. There are 260 checked-clean items and 66 confirmed defective items, all repaired: 56 answer ambiguities and 11 euphony or key-context defects, with one item in both groups. All learning targets, answer meanings and correct-option indices are retained. Three full-sentence keys have euphonic spelling corrections; the other keys are unchanged.

The order comes from `levels.a1-v1.modules` in `curriculum/l2-uk-en/curriculum.yaml`. It is the issue's arc-order fallback; no authorized usage ranking was supplied. Modules 15-28 belong to the parallel worker and are untouched.

| Position | Module | Items checked | Clean | Defects fixed |
| --- | --- | ---: | ---: | ---: |
| 29 | `where-is-it` | 24 | 18 | 6 |
| 30 | `my-city` | 20 | 19 | 1 |
| 31 | `where-to` | 24 | 20 | 4 |
| 32 | `transport` | 26 | 24 | 2 |
| 33 | `around-the-city` | 24 | 15 | 9 |
| 34 | `where-from` | 18 | 12 | 6 |
| 35 | `checkpoint-places` | 24 | 16 | 8 |
| 36 | `food-and-drink` | 18 | 15 | 3 |
| 37 | `i-eat-i-drink` | 22 | 15 | 7 |
| 38 | `at-the-cafe` | 22 | 15 | 7 |
| 39 | `shopping` | 23 | 19 | 4 |
| 40 | `people-around-me` | 24 | 24 | 0 |
| 41 | `checkpoint-food-shopping` | 31 | 22 | 9 |
| 42 | `hey-friend` | 26 | 26 | 0 |

## What was checked

Item indices and anonymous `workbook[n]` activity indices are zero-based. Explicit activity ids are used when present. Each row checks the key and every displayed alternative against the instruction and stem. The original stem and original key identify the item; the repair table records all cue and key-spelling changes. Clean means no confirmed wrong key or second defensible option within that task, not certification of every linguistic claim in the module.

The structural scanner ran before and after repair: 55/55 activity files, exit 0, zero structural findings. It added no flagged items from other activity types. As in the preceding batch, this structural pass does not replace Method step 1's broader intended semantic and VESUM rules.

Not checked: other activity types without a structural flag; lesson prose, plans, vocabulary and resources; modules outside 29-42; historical generated/source drift outside the repaired objects; audio, teacher usage and deployed-site behavior. Other workers' batches are not credited to this report. No deployment or publication is part of this slice. The rest of #8893 remains open with the CTO curriculum coordinator.

## Sources evidence and its limits

The `sources` MCP supplied the evidence on 2026-10-28. VESUM proves forms and grammatical analyses. Stress replies provide ULIF readings or an explicitly labelled trie fallback; pending or homonymous readings remain qualified. `check_text` screens text and does not judge answer ambiguity. The clean and defect verdicts are the author's linguistic inferences from these results and the stated task. Usage-sensitive verdicts also cite dictionary, textbook or corpus evidence.

For each module section, `verify_words` received distinct Ukrainian tokens from the instruction and every item field and option, lowercased with acute accents stripped. `verify_stresses` received original polysyllabic tokens, retaining case and any marks. `check_text` received item ids and accent-free full item text with vesum and ua_gec checks. These are the same batch normalization and receipt format used by the first report. No transport error counts as evidence.

NAMES rechecks 48 correctly cased personal and geographical forms, 48/48 found. NAME-STRESS checks their stress readings. KEYS verifies 297 distinct tokens from the initial completed fill-in strings, 269 found before the proper-name recheck. U84/U85 and U88/U89 verify the revised euphonic forms and their stress readings. All its 28 misses are correctly cased names/forms covered by NAMES. The module screens also contain intentionally malformed distractors such as їст, їсиш, метрою, таксієм, синке and бабусе; their failure is not a claim that the target vocabulary is invalid. No new Ukrainian vocabulary target or stress mark is introduced.

Some unmarked homonyms have multiple stress readings; no marked target is changed here. Дерибасівській remains pending in the stress oracle, although VESUM verifies its form. No stress verdict about that street name is claimed. This limitation does not change the preposition key in its item.

POST1-POST3 screen the final 326 items in batches of 150, 150 and 26. Diagnostics include case-sensitive tokens and intentionally wrong options. UA-GEC suggestions about один, назад, Ти знаєш and ставить are contextual suspicions and caused no repair. Ingestion misses, negated corpus examples and irrelevant concordances are explicitly distinguished in the U locators.

The companion [machine-readable Sources evidence](language-pass-modules-29-42-evidence.jsonl) preserves query arguments, VESUM analyses, ULIF row identifiers, diagnostic results and compact usage summaries. SHA-256 values bind the persisted normalized result objects; they are not hashes of transport envelopes. Usage records preserve metadata and source locators, with no copied private reference text. The file has 117 records.

### Module batch locators

Each M locator binds successful verify_words, verify_stresses and check_text replies for that module section. Every item row cites its module locator. The evidence file contains the full query arguments and normalized results.

| Locator | Section | VESUM found/queried | Stress rows | Text items | Receipt SHA-256 |
| --- | --- | ---: | ---: | ---: | --- |
| M29 | where-is-it, inline/root | 44/48 | 43 | 24 | `299a037c115a4d3a03c6eca57741fc4035df81583ab1b3a4021271b1ba98ad06` |
| M30 | my-city, inline/root | 43/43 | 42 | 20 | `ee0965a23a629f3f9b58b3d303b67fd1fab55fc93326a12812331d0b3b04973e` |
| M31 | where-to, inline/root | 52/60 | 48 | 24 | `f7e97e2c6714cd85bd9a6e010983c982c425d2cc97219a3653f31ed3e111cd09` |
| M32 | transport, inline/root | 68/71 | 65 | 26 | `70c06923d75c5c5e47a7cde8204fc5455be61d4214deb7b485b29f56a4890ff8` |
| M33 | around-the-city, inline/root | 70/70 | 62 | 24 | `da36ee45603a54541f12cf9459a4ca64d722bc62a31e10f1da77d9150ad04bb3` |
| M34 | where-from, inline/root | 38/52 | 35 | 12 | `ebd15cbf04a4ed7b1aa22393cf004b34ac8ee15abf001f31714bacde2786b21a` |
| M34 | where-from, workbook | 24/35 | 24 | 6 | `284d54caa327c82399732cc2b67dbde175d8ad8431993cc1ecb30e8487291df4` |
| M35 | checkpoint-places, inline/root | 44/52 | 39 | 12 | `ed12afb73dc1a1401c2d5bdace21f9d4db3ca73034d358919b510e56b9a82027` |
| M35 | checkpoint-places, workbook | 40/46 | 40 | 12 | `138bdc771a27e2556866636dfffc3fd05612a2f4b60d7e167ee968e6fdc010d0` |
| M36 | food-and-drink, inline/root | 27/27 | 18 | 6 | `e298672c378e748a5bfe0f73ba978ed4400c4389d1c4b12c1e17f648953f8fcf` |
| M36 | food-and-drink, workbook | 49/49 | 33 | 12 | `fd84e63361653eed7f3cd0139815ed03a090213694fb7cde7e5cbc7498e9d75d` |
| M37 | i-eat-i-drink, inline/root | 53/55 | 46 | 22 | `eda2240bed124d07e1a9e6554cccc09ebca95edfa4ed8be86bed48ad63b161c9` |
| M38 | at-the-cafe, inline/root | 79/79 | 70 | 22 | `dd46ef20bce3d75e964162fa9b8ea5c91e51b6da84e3ce920985cbac43e67cde` |
| M39 | shopping, inline/root | 43/43 | 38 | 23 | `fb25b6b273ca7c180472980fe80398e649f5c0362768b0cdafcbe5c43e5b1d86` |
| M40 | people-around-me, inline/root | 39/42 | 43 | 18 | `e9fd0ffcc3a3fd34e27f1727b5dc8eeecbb3294a4a53fc6136e437eab9633641` |
| M40 | people-around-me, workbook | 31/32 | 27 | 6 | `79d56ea940eb0574f0405ed3ff5b5d72275383dad8245fcb7d0ebbba292f21d6` |
| M41 | checkpoint-food-shopping, inline/root | 78/82 | 70 | 18 | `9305080385c2264e0c8118f2fbe15d736cff77c8ddd3fd9e193246d5a59f30f7` |
| M41 | checkpoint-food-shopping, workbook | 72/76 | 69 | 13 | `34c74192b59cdfd3ee5dbc85f0ed9f5ac4c702c39dc19005294d8f2bce7bc7d4` |
| M42 | hey-friend, inline/root | 35/52 | 52 | 18 | `c6612552b3d27c56b69f01956c6846c676784fdeecb4142fe120acb5ec9e574d` |
| M42 | hey-friend, workbook | 34/44 | 37 | 8 | `5ab7de7fffbffcee020e45d0b31f163d90e02544da7d2eaac44cfa6ae5a917b8` |

### Usage and orthography locators

The official offline SUM-20 lookups U1-U5 returned ingestion misses; modern VTS and textbooks supplied the relevant evidence. VTS summaries refer only to the named VTS entry, not the aggregator's neighbouring dictionary snippets. A corpus example is evidence of a possible usage, not an instruction to teach it as the preferred neutral form.

- U6: Official Pravopys 2019 section 23, pages 25-28: euphonic у/в distribution, including contextual and literary variation. https://www.ulif.org.ua/system/files/pravopus-new.pdf
- U7: Official Pravopys 2019 section 25, pages 29-31: з, із and зі variants and their euphonic distribution. https://www.ulif.org.ua/system/files/pravopus-new.pdf
- U8: The returned noun and numeral tables distinguish case and cardinal versus ordinal forms. This search did not attest a track-number label.
- U9: GRAC directly attests на автобусі as a means of travel, alongside the instrumental bus form.
- U10: GRAC directly attests people waiting and ticket offices inside a station as у вокзалі.
- U11: GRAC attests з США. This is usage evidence, not a claim that every variant is equally euphonic.
- U13: VTS на: accusative destination, locative location, and locative instrument or means. The spatial senses can coexist with в. https://slovnyk.me/dict/vts/%D0%BD%D0%B0
- U14: VTS іти: walking or movement, with direction, departure and other senses. The verb alone does not select destination over source or location. https://slovnyk.me/dict/vts/%D1%96%D1%82%D0%B8
- U15: VTS пити: consume liquid, with or without an object. It can be an independent daytime activity. https://slovnyk.me/dict/vts/%D0%BF%D0%B8%D1%82%D0%B8
- U16: VTS їсти: consume food, transitive or without an object. https://slovnyk.me/dict/vts/%D1%97%D1%81%D1%82%D0%B8
- U17: VTS бути: present є across persons. The copula often disappears in the present; its presence is not inherently wrong. https://slovnyk.me/dict/vts/%D0%B1%D1%83%D1%82%D0%B8
- U20: VTS поруч: nearby, beside, or alongside someone, including with йти. Distance and manner readings depend on context. https://slovnyk.me/dict/vts/%D0%BF%D0%BE%D1%80%D1%83%D1%87
- U21: VTS зупинка: stopping movement, a transport stopping point, or a temporary halt. A stop can have a time. https://slovnyk.me/dict/vts/%D0%B7%D1%83%D0%BF%D0%B8%D0%BD%D0%BA%D0%B0
- U22: VTS склянка: drinking vessel, also the amount it contains. https://slovnyk.me/dict/vts/%D1%81%D0%BA%D0%BB%D1%8F%D0%BD%D0%BA%D0%B0
- U23: VTS літр: a volume unit for liquids and loose materials, also a vessel of that size. https://slovnyk.me/dict/vts/%D0%BB%D1%96%D1%82%D1%80
- U24: VTS обідати: eat the midday meal between breakfast and supper. https://slovnyk.me/dict/vts/%D0%BE%D0%B1%D1%96%D0%B4%D0%B0%D1%82%D0%B8
- U25: VTS снідати: eat breakfast, including a colloquial transitive food-object construction. https://slovnyk.me/dict/vts/%D1%81%D0%BD%D1%96%D0%B4%D0%B0%D1%82%D0%B8
- U26: VTS платити: pay, with transitive and intransitive senses. https://slovnyk.me/dict/vts/%D0%BF%D0%BB%D0%B0%D1%82%D0%B8%D1%82%D0%B8
- U27: VTS рубль: the currency of Russia and certain other countries; the word is not an impossible Ukrainian form. https://slovnyk.me/dict/vts/%D1%80%D1%83%D0%B1%D0%BB%D1%8C
- U28: Official Pravopys 2019 section 74, page 109: first-declension vocative endings, including бабусю and personal names. https://www.ulif.org.ua/system/files/pravopus-new.pdf
- U29: GRAC supplies one conversational instance of drinking borscht. It witnesses a possible situation rather than a general preferred meal formula.
- U30: GRAC attests tea measured in litres, including inflected litre forms.
- U31: GRAC attests a bottle of milk in ordinary food and purchasing contexts.
- U32: Volkova and Maslo 2012 page 91 and Avramenko 2023 page 170: numeral-noun agreement. This is not proof of a track-number naming convention.
- U41: GRAC directly attests polite requests with дайте чаю.
- U48: Marynenko 2021 page 71 distinguishes direct and indirect objects and states that accusative is the usual direct-object case. The continuation is U60.
- U54: GRAC directly attests a singular cost predicate before a quantified subject naming three ice creams.
- U57: VTS картка includes a card and a bank payment card. https://slovnyk.me/dict/vts/%D0%BA%D0%B0%D1%80%D1%82%D0%BA%D0%B0
- U58: VTS рахунок includes the document showing an amount payable for goods or services. https://slovnyk.me/dict/vts/%D1%80%D0%B0%D1%85%D1%83%D0%BD%D0%BE%D0%BA
- U59: VTS смачний includes pleasant taste and the meal wish Смачного. https://slovnyk.me/dict/vts/%D1%81%D0%BC%D0%B0%D1%87%D0%BD%D0%B8%D0%B9
- U60: Marynenko 2021 page 72, chunk uni-ukrmova-punctuation-marynenko-2021_s0118: a direct object may be genitive for a partial quantity. The rule has no perfective-only restriction; its examples include consumed food and drink. It also records conversational accusative/genitive parallels.
- U61: GRAC directly attests walking in a forest with a locative complement. Motion does not inherently force the accusative.
- U64: VTS в/у takes accusative for movement into a place and locative for the place of an action or participation. https://slovnyk.me/dict/vts/%D0%B2
- U65: VTS з takes genitive for the origin or source of motion, and instrumental for accompaniment or an added ingredient. https://slovnyk.me/dict/vts/%D0%B7
- U67: GRAC directly attests a bottle of prepared tea.
- U68: GRAC directly attests water measured in kilograms. This proves a possible quantity, not that mass is the usual shop unit.
- U69: Marynenko 2021 pages 54-55: quantified subjects permit agreement choices according to construction, focus and predicate position. U54 supplies a price-question example.
- U70: The returned у пошті instances concern mail or an inbox, not a physical post-office location. They do not confirm the suspected physical-place alternative.
- U71: GRAC attests у стадіоні for an office inside a stadium building. It does not directly attest the match-venue phrase in this quiz.
- U72: VTS вечеряти has an intransitive eating-in-the-evening sense and a rare transitive sense. No new defect is inferred from that rare sense alone. https://slovnyk.me/dict/vts/%D0%B2%D0%B5%D1%87%D0%B5%D1%80%D1%8F%D1%82%D0%B8
- U75: The returned я зараз до examples retain an explicit movement verb. They do not confirm the suspected verbless elliptical completion.
- U76: The search returned stress and general numeral information, not the suspected track-number label. No defect is claimed from this query.
- U78: GRAC directly attests polite requests with чи не могли б ви дати. The conditional request is grammatical; a direct-imperative cue selects the existing key.
- U79: The returned колія три matches put three after a different inflected noun phrase. They do not confirm a cardinal track label.
- U80: The returned textbook material distinguishes cardinal and ordinal numerals but does not confirm the suspected track label.
- U82: GRAC directly attests the exact offered в вокзалі in interior station locations, in both literary and conversational examples. Its euphony is disfavoured; the item asks for a static preposition, not the preferred euphonic spelling.
- U83: Official Pravopys 2019 section 24, pages 28-29: і/й and initial і-/й- distribution, with Він іде after a consonant and Вона йде after a vowel. https://www.ulif.org.ua/system/files/pravopus-new.pdf
- U87: VTS направо includes both movement to the right and static position on the right. The latter can describe a cafe that is also near home. https://slovnyk.me/dict/vts/%D0%BD%D0%B0%D0%BF%D1%80%D0%B0%D0%B2%D0%BE
- U90: GRAC returns two actual name-giving uses of моє ім'я є among ten results. The other existential and figurative examples do not establish that formula. These two occurrences support a possible naming statement, not the preferred A1 formula.

## Per-item verdicts

C means checked-clean in the original source. D means a confirmed answer ambiguity or form/context defect in the original source, fixed here. Every row cites M plus usage locators where meaning or register decides. NAMES and NAME-STRESS apply to proper names throughout. Three full-sentence keys change only euphonic spelling: Він живе у Києві to Він живе в Києві; Я іду в школу to Я йду в школу; Степан йде на пошту to Степан іде на пошту. Their meanings and correct-option indices stay the same. The repair detail for every D row follows the tables.

### 29. where-is-it

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | Олена ___ школі. | в | C | M29; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key в matches the stated meaning and case; the displayed competitors fail that task. |
| `act-1/1` | inline | Мама ___ роботі. | на | C | M29; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key на matches the stated meaning and case; the displayed competitors fail that task. |
| `act-1/2` | inline | Максим ___ банку. | у | C | M29; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key у matches the stated meaning and case; the displayed competitors fail that task. |
| `act-1/3` | inline | Я ___ магазині. | в | C | M29; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key в matches the stated meaning and case; the displayed competitors fail that task. |
| `act-1/4` | inline | Аптека ___ вулиці. | на | C | M29; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key на matches the stated meaning and case; the displayed competitors fail that task. |
| `act-1/5` | inline | Пошта ___ площі. | на | C | M29; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key на matches the stated meaning and case; the displayed competitors fail that task. |
| `act-1/6` | inline | Тато ___ вокзалі. | на | D | M29; U6; U64; U82. GRAC attests the exact offered в вокзалі as an interior location, despite its disfavoured euphony. A task about static place rather than euphonic spelling does not exclude it. Без requires a genitive instead of вокзалі. |
| `act-1/7` | inline | Марко ___ лікарні. | у | D | M29; U6; U84; U85. The original key у follows a vowel before лікарні. Adding consonant-final зараз makes the preserved у normative under section 23. |
| `act-1/8` | inline | Ми ___ кафе. | в | C | M29; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key в matches the stated meaning and case; the displayed competitors fail that task. |
| `act-1/9` | inline | Друг ___ Одесі. | в | C | M29; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key в matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/0` | inline | Олена ___ (школа). | в школі | C | M29; U13/U64. No options are authored. The key в школі supplies the required place phrase; this row makes no uniqueness claim about unoffered completions. The tracked empty-option dropdown is a separate renderer residual documented below. |
| `act-2/1` | inline | Тарас ___ (робота). | на роботі | C | M29; U13/U64. No options are authored. The key на роботі supplies the required place phrase; this row makes no uniqueness claim about unoffered completions. The tracked empty-option dropdown is a separate renderer residual documented below. |
| `act-2/2` | inline | Максим ___ (банк). | у банку | C | M29; U13/U64. No options are authored. The key у банку supplies the required place phrase; this row makes no uniqueness claim about unoffered completions. The tracked empty-option dropdown is a separate renderer residual documented below. |
| `act-2/3` | inline | Я ___ (магазин). | в магазині | C | M29; U13/U64. No options are authored. The key в магазині supplies the required place phrase; this row makes no uniqueness claim about unoffered completions. The tracked empty-option dropdown is a separate renderer residual documented below. |
| `act-2/4` | inline | Аптека ___ (вулиця). | на вулиці | C | M29; U13/U64. No options are authored. The key на вулиці supplies the required place phrase; this row makes no uniqueness claim about unoffered completions. The tracked empty-option dropdown is a separate renderer residual documented below. |
| `act-2/5` | inline | Ми ___ (місто). | у місті | D | M29; U6; U84; U85. The original completed sentence conflicts with the default у/в distribution in section 23. The revised context preserves the target case, meaning and answer. |
| `act-2/6` | inline | Софія ___ (лікарня). | у лікарні | D | M29; U6; U84; U85. The original completed sentence conflicts with the default у/в distribution in section 23. The revised context preserves the target case, meaning and answer. |
| `act-2/7` | inline | Я живу ___ (Київ). | у Києві | D | M29; U6; U84; U85. The original completed sentence conflicts with the default у/в distribution in section 23. The revised context preserves the target case, meaning and answer. |
| `act-4/0` | inline | Де Олена? | Вона в школі. | C | M29; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Вона в школі. matches the stated meaning and case; the displayed competitors fail that task. |
| `act-4/1` | inline | Де Тарас? | Він на роботі. | C | M29; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Він на роботі. matches the stated meaning and case; the displayed competitors fail that task. |
| `act-4/2` | inline | Де Максим? | Він у банку. | C | M29; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Він у банку. matches the stated meaning and case; the displayed competitors fail that task. |
| `act-4/3` | inline | Де книга? | Книга на столі. | C | M29; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Книга на столі. matches the stated meaning and case; the displayed competitors fail that task. |
| `act-4/4` | inline | Де Марко живе? | Він живе у Києві. | D | M29; U6. The original full-sentence key uses у after a vowel before Києві. Its euphonic spelling changes to в; answer meaning and correct option index stay the same. |
| `act-4/5` | inline | Де пошта? | Пошта на площі. | C | M29; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Пошта на площі. matches the stated meaning and case; the displayed competitors fail that task. |

### 30. my-city

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-2/0` | inline | Where do you buy medicine? | в аптеці | C | M30; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key в аптеці matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/1` | inline | Where are you at the post office? | на пошті | C | M30; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key на пошті matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/2` | inline | Where is the train station sentence? | Вона на вокзалі. | D | M30; U10; U64. У вокзалі is an attested interior location. The replacement has an incompatible case after до. |
| `act-2/3` | inline | Where do students read? | у бібліотеці | C | M30; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key у бібліотеці matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/4` | inline | Where is someone in the hospital? | у лікарні | C | M30; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key у лікарні matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/5` | inline | Where do you buy bread? | у магазині | C | M30; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key у магазині matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/6` | inline | Where does a tourist sleep? | у готелі | C | M30; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key у готелі matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/7` | inline | Where is the match? | на стадіоні | C | M30; U13/U71. The match venue uses на стадіоні. U71 concerns an office inside a stadium building, not a match-venue construction; no defect is inferred from it. |
| `act-3/0` | inline | У моєму місті є великий ___. | парк | C | M30; U13/U64. No options are authored. The key парк supplies the required place phrase; this row makes no uniqueness claim about unoffered completions. The tracked empty-option dropdown is a separate renderer residual documented below. |
| `act-3/1` | inline | Бібліотека ___ університету. | біля | C | M30; U13/U64. No options are authored. The key біля supplies the required place phrase; this row makes no uniqueness claim about unoffered completions. The tracked empty-option dropdown is a separate renderer residual documented below. |
| `act-3/2` | inline | Аптека ___ розі. | на | C | M30; U13/U64. No options are authored. The key на supplies the required place phrase; this row makes no uniqueness claim about unoffered completions. The tracked empty-option dropdown is a separate renderer residual documented below. |
| `act-3/3` | inline | Магазин тут, ___ дому. | біля | C | M30; U13/U64. No options are authored. The key біля supplies the required place phrase; this row makes no uniqueness claim about unoffered completions. The tracked empty-option dropdown is a separate renderer residual documented below. |
| `act-3/4` | inline | Школа далеко, ___ центрі міста. | у | C | M30; U13/U64. No options are authored. The key у supplies the required place phrase; this row makes no uniqueness claim about unoffered completions. The tracked empty-option dropdown is a separate renderer residual documented below. |
| `act-3/5` | inline | У місті ___ багато парків. | є | C | M30; U13/U64. No options are authored. The key є supplies the required place phrase; this row makes no uniqueness claim about unoffered completions. The tracked empty-option dropdown is a separate renderer residual documented below. |
| `act-4/0` | inline | You need medicine. Which place? | аптека | C | M30; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key аптека matches the stated meaning and case; the displayed competitors fail that task. |
| `act-4/1` | inline | You want to read a book quietly. Which place? | бібліотека | C | M30; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key бібліотека matches the stated meaning and case; the displayed competitors fail that task. |
| `act-4/2` | inline | You need bread for dinner. Which place? | магазин | C | M30; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key магазин matches the stated meaning and case; the displayed competitors fail that task. |
| `act-4/3` | inline | You want dinner with friends. Which place? | ресторан | C | M30; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key ресторан matches the stated meaning and case; the displayed competitors fail that task. |
| `act-4/4` | inline | You are waiting for a train. Which place? | вокзал | C | M30; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key вокзал matches the stated meaning and case; the displayed competitors fail that task. |
| `act-4/5` | inline | You are a tourist and need a room. Which place? | готель | C | M30; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key готель matches the stated meaning and case; the displayed competitors fail that task. |

### 31. where-to

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | Я йду в банк. | Куди? | C | M31; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Куди? matches the stated meaning and case; the displayed competitors fail that task. |
| `act-1/1` | inline | Оксана на пошті. | Де? | C | M31; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Де? matches the stated meaning and case; the displayed competitors fail that task. |
| `act-1/2` | inline | Ми їдемо у Львів. | Куди? | C | M31; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Куди? matches the stated meaning and case; the displayed competitors fail that task. |
| `act-1/3` | inline | Книжка на столі. | Де? | C | M31; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Де? matches the stated meaning and case; the displayed competitors fail that task. |
| `act-1/4` | inline | Марко їде на вокзал. | Куди? | C | M31; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Куди? matches the stated meaning and case; the displayed competitors fail that task. |
| `act-1/5` | inline | Я працюю в офісі. | Де? | C | M31; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Де? matches the stated meaning and case; the displayed competitors fail that task. |
| `act-1/6` | inline | Олена йде в аптеку. | Куди? | C | M31; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Куди? matches the stated meaning and case; the displayed competitors fail that task. |
| `act-1/7` | inline | Степан на роботі. | Де? | C | M31; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Де? matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/0` | inline | Я йду ___ банк. | у | D | M31; U6; U84; U85. The original completed sentence conflicts with the default у/в distribution in section 23. The revised context preserves the target case, meaning and answer. |
| `act-2/1` | inline | Олена йде ___ роботу. | на | C | M31; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key на matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/2` | inline | Ми йдемо в ___. | аптеку | C | M31; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key аптеку matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/3` | inline | Степан йде у ___. | бібліотеку | D | M31; U6; U84; U85. The original completed sentence conflicts with the default у/в distribution in section 23. The revised context preserves the target case, meaning and answer. |
| `act-2/4` | inline | Я їду ___ вокзал. | на | D | M31; U10; U64. В вокзал can describe movement into the station building, alongside на вокзал as the station destination. До requires a genitive. |
| `act-2/5` | inline | Марко йде ___ зупинку. | на | C | M31; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key на matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/6` | inline | Він у ___. | банку | C | M31; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key банку matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/7` | inline | Оксана на ___. | пошті | C | M31; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key пошті matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/8` | inline | Вона їде в ___. | Одесу | C | M31; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Одесу matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/9` | inline | Я працюю на ___. | роботі | C | M31; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key роботі matches the stated meaning and case; the displayed competitors fail that task. |
| `act-4/0` | inline | I am going to the shop on foot. | Я йду в магазин. | C | M31; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Я йду в магазин. matches the stated meaning and case; the displayed competitors fail that task. |
| `act-4/1` | inline | We are going to the station by bus. | Ми їдемо на вокзал. | C | M31; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Ми їдемо на вокзал. matches the stated meaning and case; the displayed competitors fail that task. |
| `act-4/2` | inline | Oksana is going to Lviv by train. | Оксана їде у Львів. | C | M31; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Оксана їде у Львів. matches the stated meaning and case; the displayed competitors fail that task. |
| `act-4/3` | inline | Stepan is walking to the post office. | Степан йде на пошту. | D | M31; U83; U88; U89. The original full-sentence key uses йде after consonant-final Степан. Section 24 calls for іде in this position. Meaning and correct option index stay the same. |
| `act-4/4` | inline | They are going to the park on foot. | Вони йдуть у парк. | C | M31; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Вони йдуть у парк. matches the stated meaning and case; the displayed competitors fail that task. |
| `act-4/5` | inline | I am going to Odesa by train. | Я їду в Одесу. | C | M31; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Я їду в Одесу. matches the stated meaning and case; the displayed competitors fail that task. |

### 32. transport

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | From the airport to the hotel, faster but expensive. | таксі | C | M32; U9/U13/U15/U21. The key таксі matches the named vehicle, travel situation, price/time question or route phrase; the displayed competitors do not supply that meaning or form. |
| `act-1/1` | inline | City route number seven. | автобус | C | M32; U9/U13/U15/U21. The key автобус matches the named vehicle, travel situation, price/time question or route phrase; the displayed competitors do not supply that meaning or form. |
| `act-1/2` | inline | Underground city travel. | метро | C | M32; U9/U13/U15/U21. The key метро matches the named vehicle, travel situation, price/time question or route phrase; the displayed competitors do not supply that meaning or form. |
| `act-1/3` | inline | Rail trip to Lviv. | потяг | C | M32; U9/U13/U15/U21. The key потяг matches the named vehicle, travel situation, price/time question or route phrase; the displayed competitors do not supply that meaning or form. |
| `act-1/4` | inline | City rails on the street. | трамвай | C | M32; U9/U13/U15/U21. The key трамвай matches the named vehicle, travel situation, price/time question or route phrase; the displayed competitors do not supply that meaning or form. |
| `act-1/5` | inline | Electric city bus with overhead wires. | тролейбус | C | M32; U9/U13/U15/U21. The key тролейбус matches the named vehicle, travel situation, price/time question or route phrase; the displayed competitors do not supply that meaning or form. |
| `act-1/6` | inline | Flight to another country. | літак | C | M32; U9/U13/U15/U21. The key літак matches the named vehicle, travel situation, price/time question or route phrase; the displayed competitors do not supply that meaning or form. |
| `act-1/7` | inline | Small route minibus. | маршрутка | C | M32; U9/U13/U15/U21. The key маршрутка matches the named vehicle, travel situation, price/time question or route phrase; the displayed competitors do not supply that meaning or form. |
| `act-2/0` | inline | Один ___ до Львова, будь ласка. | квиток | C | M32; U9/U13/U15/U21. The key квиток matches the named vehicle, travel situation, price/time question or route phrase; the displayed competitors do not supply that meaning or form. |
| `act-2/1` | inline | ___ коштує квиток? | Скільки | C | M32; U9/U13/U15/U21. The key Скільки matches the named vehicle, travel situation, price/time question or route phrase; the displayed competitors do not supply that meaning or form. |
| `act-2/2` | inline | В один бік чи ___ й назад? | туди | C | M32; U9/U13/U15/U21. The key туди matches the named vehicle, travel situation, price/time question or route phrase; the displayed competitors do not supply that meaning or form. |
| `act-2/3` | inline | Відправлення ___ дев'ятій. | о | C | M32; U9/U13/U15/U21. The key о matches the named vehicle, travel situation, price/time question or route phrase; the displayed competitors do not supply that meaning or form. |
| `act-2/4` | inline | Колія ___. | третя | C | M32; U8/U32/U76/U79/U80. The feminine ordinal третя agrees with колія. A suspected cardinal track label was not confirmed by the returned sources and caused no edit. |
| `act-2/5` | inline | О котрій ___? | відправлення | D | M32; U21. О котрій зупинка? can ask when a stop occurs. The cue selects departure, not a stop. |
| `act-3/0` | inline | How do you say by bus? | автобусом | D | M32; U9; U13. На автобусі is an attested means-of-transport phrase, as is the keyed instrumental автобусом. |
| `act-3/1` | inline | How do you say by metro? | на метро | C | M32; U9/U13/U15/U21. The key на метро matches the named vehicle, travel situation, price/time question or route phrase; the displayed competitors do not supply that meaning or form. |
| `act-3/2` | inline | How do you say by taxi? | на таксі | C | M32; U9/U13/U15/U21. The key на таксі matches the named vehicle, travel situation, price/time question or route phrase; the displayed competitors do not supply that meaning or form. |
| `act-3/3` | inline | How do you say by train? | потягом | C | M32; U9/U13/U15/U21. The key потягом matches the named vehicle, travel situation, price/time question or route phrase; the displayed competitors do not supply that meaning or form. |
| `act-3/4` | inline | How do you say by tram? | трамваєм | C | M32; U9/U13/U15/U21. The key трамваєм matches the named vehicle, travel situation, price/time question or route phrase; the displayed competitors do not supply that meaning or form. |
| `act-3/5` | inline | How do you say by trolleybus? | тролейбусом | C | M32; U9/U13/U15/U21. The key тролейбусом matches the named vehicle, travel situation, price/time question or route phrase; the displayed competitors do not supply that meaning or form. |
| `act-4/0` | inline | Як дістатися до ___? | вокзалу | C | M32; U9/U13/U15/U21. The key вокзалу matches the named vehicle, travel situation, price/time question or route phrase; the displayed competitors do not supply that meaning or form. |
| `act-4/1` | inline | Як дістатися до ___? | центру | C | M32; U9/U13/U15/U21. The key центру matches the named vehicle, travel situation, price/time question or route phrase; the displayed competitors do not supply that meaning or form. |
| `act-4/2` | inline | Ідіть ___. | прямо | C | M32; U9/U13/U15/U21. The key прямо matches the named vehicle, travel situation, price/time question or route phrase; the displayed competitors do not supply that meaning or form. |
| `act-4/3` | inline | Поверніть ___. | направо | C | M32; U9/U13/U15/U21. The key направо matches the named vehicle, travel situation, price/time question or route phrase; the displayed competitors do not supply that meaning or form. |
| `act-4/4` | inline | Поверніть ___. | наліво | C | M32; U9/U13/U15/U21. The key наліво matches the named vehicle, travel situation, price/time question or route phrase; the displayed competitors do not supply that meaning or form. |
| `act-4/5` | inline | Мені ___ тут? | виходити | C | M32; U9/U13/U15/U21. The key виходити matches the named vehicle, travel situation, price/time question or route phrase; the displayed competitors do not supply that meaning or form. |

### 33. around-the-city

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | Ідіть ___, потім направо. | прямо | D | M33; U14; U20. Пішки states walking and поруч states walking alongside someone; both can precede a later right turn. The direction cue selects прямо. |
| `act-1/1` | inline | Вибачте, як ___ до музею? | дістатися | C | M33; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key дістатися matches the stated meaning and case; the displayed competitors fail that task. |
| `act-1/2` | inline | Аптека близько. Ідіть прямо п'ять ___. | хвилин | C | M33; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key хвилин matches the stated meaning and case; the displayed competitors fail that task. |
| `act-1/3` | inline | Потім ідіть ___, школа там. | направо | D | M33; U14. Пішки is also a valid manner of going. The rightward cue selects направо. |
| `act-1/4` | inline | Йдіть прямо, а потім ___. | наліво | C | M33; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key наліво matches the stated meaning and case; the displayed competitors fail that task. |
| `act-1/5` | inline | Ресторан поруч. Ідіть прямо і ___. | направо | C | M33; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key направо matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/0` | inline | Я зараз... | в парку | C | M33; U64/U75. The offered static в парку supplies a full location predicate. The search did not confirm the suspected verbless destination ellipsis; no edit. |
| `act-2/1` | inline | Я йду... | в магазин | D | M33; U14; U61; U64. A locative can state where walking happens, while the accusative states its destination. The cue selects в магазин. |
| `act-2/2` | inline | Магазин на... | вулиці | C | M33; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key вулиці matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/3` | inline | Потім їду на... | роботу | D | M33; U13; U64. На роботі can locate an action at work; the verb alone does not fix a destination. The cue selects на роботу. |
| `act-2/4` | inline | Ми зараз у... | центрі | C | M33; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key центрі matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/5` | inline | Вона йде в... | офіс | D | M33; U14; U61; U64. В офісі can locate the walking inside the office. The cue selects the destination в офіс. |
| `act-5/0` | inline | Аптека ___. П'ять хвилин пішки. | близько | D | M33; U20. Наліво can locate a pharmacy to the left, including five minutes away. The proximity cue selects близько. |
| `act-5/1` | inline | Вокзал ___. Їдьте на метро. | далеко | D | M33; U20. A recommendation to take the metro does not exclude a station nearby or straight ahead. The explicit distance cue selects далеко. |
| `act-5/2` | inline | Кафе ___. Воно біля дому. | поруч | D | M33; U20; U87. Направо has an attested static right-hand-side meaning, which can coexist with біля дому. The proximity cue selects поруч. |
| `act-5/3` | inline | Бібліотека ___ розі. | на | C | M33; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key на matches the stated meaning and case; the displayed competitors fail that task. |
| `act-5/4` | inline | Ідіть ___, потім наліво. | прямо | D | M33; U14; U20. Ідіть поруч can tell people to walk alongside each other, then turn left. The direction cue selects прямо. |
| `act-5/5` | inline | Музей ___ центрі. | у | C | M33; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key у matches the stated meaning and case; the displayed competitors fail that task. |
| `act-6/0` | inline | Я в парку. | де? | C | M33; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key де? matches the stated meaning and case; the displayed competitors fail that task. |
| `act-6/1` | inline | Я йду в парк. | куди? | C | M33; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key куди? matches the stated meaning and case; the displayed competitors fail that task. |
| `act-6/2` | inline | Їду автобусом. | як? / чим? | C | M33; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key як? / чим? matches the stated meaning and case; the displayed competitors fail that task. |
| `act-6/3` | inline | Бібліотека на розі. | де? | C | M33; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key де? matches the stated meaning and case; the displayed competitors fail that task. |
| `act-6/4` | inline | Їдьте на метро. | як? / чим? | C | M33; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key як? / чим? matches the stated meaning and case; the displayed competitors fail that task. |
| `act-6/5` | inline | Ідіть прямо, потім направо. | що робити? | C | M33; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key що робити? matches the stated meaning and case; the displayed competitors fail that task. |

### 34. where-from

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-2/0` | inline | Звідки ти? | Я з України. | C | M34; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Я з України. matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/1` | inline | Де ти зараз живеш? | У Києві. | C | M34; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key У Києві. matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/2` | inline | Куди ти їдеш? | В Україну. | C | M34; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key В Україну. matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/3` | inline | З якого міста Олена? | Вона зі Львова. | C | M34; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Вона зі Львова. matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/4` | inline | Звідки Марко йде? | З роботи. | C | M34; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key З роботи. matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/5` | inline | Де Анна навчається? | У школі. | C | M34; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key У школі. matches the stated meaning and case; the displayed competitors fail that task. |
| `act-3/0` | inline | Звідки ти? — Я ___. | з України | C | M34; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key з України matches the stated meaning and case; the displayed competitors fail that task. |
| `act-3/1` | inline | Анна ___. | з Канади | C | M34; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key з Канади matches the stated meaning and case; the displayed competitors fail that task. |
| `act-3/2` | inline | Ми ___, а ви? | з Києва | C | M34; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key з Києва matches the stated meaning and case; the displayed competitors fail that task. |
| `act-3/3` | inline | Джон ___. | зі США | D | M34; U7; U11. З США is attested alongside зі США. The replacement bare country abbreviation supplies no from-preposition. |
| `act-3/4` | inline | Мій друг ___. | з Німеччини | C | M34; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key з Німеччини matches the stated meaning and case; the displayed competitors fail that task. |
| `act-3/5` | inline | Олена живе в Києві, але вона ___. | зі Львова | C | M34; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key зі Львова matches the stated meaning and case; the displayed competitors fail that task. |
| `workbook[4]/0` | workbook | Я ___, з Києва. | з України | D | M34; U64; U65. The original introduction also permits the offered current-location phrase. The new origin cue selects the unchanged from-place key. |
| `workbook[4]/1` | workbook | Анна ___, із Торонто. | з Канади | D | M34; U64; U65. The original introduction also permits the offered current-location phrase. The new origin cue selects the unchanged from-place key. |
| `workbook[4]/2` | workbook | Олена живе в Києві, але вона ___. | зі Львова | D | M34; U64; U65. The original introduction also permits the offered current-location phrase. The new origin cue selects the unchanged from-place key. |
| `workbook[4]/3` | workbook | Ми зараз в Україні, але ми ___. | з Польщі | C | M34; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key з Польщі matches the stated meaning and case; the displayed competitors fail that task. |
| `workbook[4]/4` | workbook | Джон ___, але зараз живе у Києві. | зі США | D | M34; U6; U84; U85. The original completed sentence conflicts with the default у/в distribution in section 23. The revised context preserves the target case, meaning and answer. |
| `workbook[4]/5` | workbook | Марко ___ і говорить українською. | з Києва | D | M34; U64; U65. The original introduction also permits the offered current-location phrase. The new origin cue selects the unchanged from-place key. |

### 35. checkpoint-places

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-2/0` | inline | Де ти живеш? | Я живу в Одесі. | C | M35; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Я живу в Одесі. matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/1` | inline | Куди ти йдеш? | Я йду в музей. | C | M35; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Я йду в музей. matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/2` | inline | Звідки ти? | Я з України. | C | M35; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Я з України. matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/3` | inline | Як ти їдеш до центру? | На метро. | C | M35; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key На метро. matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/4` | inline | Де вокзал? | На площі, направо. | C | M35; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key На площі, направо. matches the stated meaning and case; the displayed competitors fail that task. |
| `act-2/5` | inline | Куди ти їдеш завтра? | У Львів. | C | M35; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key У Львів. matches the stated meaning and case; the displayed competitors fail that task. |
| `act-4/0` | inline | Я зараз ___ Одесі. | в | D | M35; U6; U64. В and у express the same location; the task does not request a specific euphonic spelling. До is incompatible with locative Одесі. |
| `act-4/1` | inline | Я ___ Дерибасівській вулиці. | на | C | M35; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key на matches the stated meaning and case; the displayed competitors fail that task. |
| `act-4/2` | inline | Я йду ___ кафе. | з | D | M35; U14; U64; U65. With indeclinable кафе, both з кафе and в кафе fit йду unless source versus destination is specified. |
| `act-4/3` | inline | Потім я йду ___ порт. | у | D | M35; U6; U84; U85. The original vowel-final йду requires в before порт under section 23. The consonant-final йдуть makes the preserved key у normative. |
| `act-4/4` | inline | Після порту я йду ___ пляж. | на | C | M35; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key на matches the stated meaning and case; the displayed competitors fail that task. |
| `act-4/5` | inline | Увечері я їду ___. | на вокзал | D | M35; U65. Їду з вокзалу is a valid source phrase; їду alone does not ask only куди. |
| `workbook[2]/0` | workbook | Repair: Я в школа. | Я в школі. | C | M35; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Я в школі. matches the stated meaning and case; the displayed competitors fail that task. |
| `workbook[2]/1` | workbook | Repair: Я іду в школі. | Я іду в школу. | D | M35; U14; U61; U64; U83; U84; U85. Walking can occur in the school or go to it. The destination cue selects в школу; the full-sentence key also changes іду to йду after Я under section 24. The correct option index and destination meaning stay the same. |
| `workbook[2]/2` | workbook | Repair: Я працюю в пошті. | Я працюю на пошті. | C | M35; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Я працюю на пошті. matches the stated meaning and case; the displayed competitors fail that task. |
| `workbook[2]/3` | workbook | Repair: Книга є на столі. | Книга на столі. | D | M35; U17. The present є is grammatical. The cue asks for its omission rather than condemning it. |
| `workbook[2]/4` | workbook | Repair: Вона живе Київ. | Вона живе в Києві. | C | M35; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Вона живе в Києві. matches the stated meaning and case; the displayed competitors fail that task. |
| `workbook[2]/5` | workbook | Repair: Я з Канаді. | Я з Канади. | C | M35; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key Я з Канади. matches the stated meaning and case; the displayed competitors fail that task. |
| `workbook[4]/0` | workbook | Сьогодні Анна ___ Києві. | в | C | M35; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key в matches the stated meaning and case; the displayed competitors fail that task. |
| `workbook[4]/1` | workbook | Вона ___ Канади, із Торонто. | з | C | M35; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key з matches the stated meaning and case; the displayed competitors fail that task. |
| `workbook[4]/2` | workbook | Анна йде ___ музей. | в | D | M35; U6; U64. В музей and у музей share the same destination meaning. До requires a genitive instead of музей. |
| `workbook[4]/3` | workbook | Музей ___ площі. | на | C | M35; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key на matches the stated meaning and case; the displayed competitors fail that task. |
| `workbook[4]/4` | workbook | До центру вона їде ___. | на метро | C | M35; U13/U14/U64/U65. The task distinguishes location, destination, origin or transport. The key на метро matches the stated meaning and case; the displayed competitors fail that task. |
| `workbook[4]/5` | workbook | Після музею вона їде ___. | на вокзал | D | M35; U65. Їде з вокзалу describes travel from the station, also compatible with the original sentence. |

### 36. food-and-drink

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-3/0` | inline | Мені каву ___, будь ласка. | з молоком | C | M36; U15/U16/U24/U25/U59/U65. The key з молоком fits the named meal, drink or ingredient and its required case; the alternatives fail the stated situation or form. |
| `act-3/1` | inline | Чай ___, будь ласка. | без цукру | C | M36; U15/U16/U24/U25/U59/U65. The key без цукру fits the named meal, drink or ingredient and its required case; the alternatives fail the stated situation or form. |
| `act-3/2` | inline | Я їм хліб ___. | з маслом | C | M36; U15/U16/U24/U25/U59/U65. The key з маслом fits the named meal, drink or ingredient and its required case; the alternatives fail the stated situation or form. |
| `act-3/3` | inline | Дайте, будь ласка, воду ___. | з газом | C | M36; U15/U16/U24/U25/U59/U65. The key з газом fits the named meal, drink or ingredient and its required case; the alternatives fail the stated situation or form. |
| `act-3/4` | inline | Я люблю каву ___. | без молока | C | M36; U15/U16/U24/U25/U59/U65. The key без молока fits the named meal, drink or ingredient and its required case; the alternatives fail the stated situation or form. |
| `act-3/5` | inline | Вона п'є чай ___. | з лимоном | C | M36; U15/U16/U24/U25/U59/U65. The key з лимоном fits the named meal, drink or ingredient and its required case; the alternatives fail the stated situation or form. |
| `workbook[0]/0` | workbook | Що ти робиш вранці? | Я снідаю. | C | M36; U15/U16/U24/U25/U59/U65. The key Я снідаю. fits the named meal, drink or ingredient and its required case; the alternatives fail the stated situation or form. |
| `workbook[0]/1` | workbook | Що ти їси на обід? | Я їм борщ і салат. | C | M36; U15/U16/U24/U25/U59/U65. The key Я їм борщ і салат. fits the named meal, drink or ingredient and its required case; the alternatives fail the stated situation or form. |
| `workbook[0]/2` | workbook | Що ти п'єш? | Воду або компот. | C | M36; U15/U16/U24/U25/U59/U65. The key Воду або компот. fits the named meal, drink or ingredient and its required case; the alternatives fail the stated situation or form. |
| `workbook[0]/3` | workbook | Which line names a Ukrainian cultural food? | Борщ зі сметаною. | C | M36; U15/U16/U24/U25/U59/U65. The key Борщ зі сметаною. fits the named meal, drink or ingredient and its required case; the alternatives fail the stated situation or form. |
| `workbook[0]/4` | workbook | How do you politely ask for tea without sugar? | Чай без цукру, будь ласка. | C | M36; U15/U16/U24/U25/U59/U65. The key Чай без цукру, будь ласка. fits the named meal, drink or ingredient and its required case; the alternatives fail the stated situation or form. |
| `workbook[0]/5` | workbook | What do you say as people start eating? | Смачного! | C | M36; U15/U16/U24/U25/U59/U65. The key Смачного! fits the named meal, drink or ingredient and its required case; the alternatives fail the stated situation or form. |
| `workbook[3]/0` | workbook | Вранці я ___. | снідаю | C | M36; U15/U16/U24/U25/U59/U65. The key снідаю fits the named meal, drink or ingredient and its required case; the alternatives fail the stated situation or form. |
| `workbook[3]/1` | workbook | Вдень я ___. | обідаю | D | M36; U15; U24. Вдень я п'ю is a valid daytime activity. The meal cue selects обідаю. |
| `workbook[3]/2` | workbook | Увечері я ___. | вечеряю | C | M36; U15/U16/U24/U25/U59/U65. The key вечеряю fits the named meal, drink or ingredient and its required case; the alternatives fail the stated situation or form. |
| `workbook[3]/3` | workbook | Я ___ борщ. | їм | D | M36; U16; U25; U29. Пити борщ is corpus-attested and снідати has a conversational transitive food sense. The explicit verb cue selects їм. |
| `workbook[3]/4` | workbook | Я ___ чай. | п'ю | C | M36; U15/U72. The natural drink sentence uses пити. A rare transitive вечеряти sense alone does not establish the competing tea sentence; no edit. |
| `workbook[3]/5` | workbook | Я хочу каву ___. | з молоком | D | M36; U64; U65. Both coffee with milk and coffee without sugar fit the original request. The milk cue selects з молоком. |

### 37. i-eat-i-drink

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | Я їм ___. | рибу | C | M37; U16/U48/U60. The key рибу has the required food-object case or verb agreement. No second displayed option satisfies this unchanged task. |
| `act-1/1` | inline | Вона п'є ___. | воду | C | M37; U16/U48/U60. The key воду has the required food-object case or verb agreement. No second displayed option satisfies this unchanged task. |
| `act-1/2` | inline | Він їсть ___. | хліб | C | M37; U16/U48/U60. The key хліб has the required food-object case or verb agreement. No second displayed option satisfies this unchanged task. |
| `act-1/3` | inline | Ми п'ємо ___. | молоко | C | M37; U16/U48/U60. The key молоко has the required food-object case or verb agreement. No second displayed option satisfies this unchanged task. |
| `act-1/4` | inline | Вони їдять ___. | кашу | D | M37; U48; U60. The offered genitive can express a partial quantity; каші, кави or м'яса also have plural accusative analyses where present. The case-and-number cue selects the singular accusative target. |
| `act-1/5` | inline | Ти п'єш ___. | каву | C | M37; U16/U48/U60. The key каву has the required food-object case or verb agreement. No second displayed option satisfies this unchanged task. |
| `act-1/6` | inline | Я їм ___. | суп | D | M37; U48; U60. The offered genitive can express a partial quantity; каші, кави or м'яса also have plural accusative analyses where present. The case-and-number cue selects the singular accusative target. |
| `act-1/7` | inline | Вона їсть ___. | картоплю | D | M37; U48; U60. The offered genitive can express a partial quantity; каші, кави or м'яса also have plural accusative analyses where present. The case-and-number cue selects the singular accusative target. |
| `act-2/0` | inline | Я п'ю... | каву | D | M37; U48; U60. The offered genitive can express a partial quantity; каші, кави or м'яса also have plural accusative analyses where present. The case-and-number cue selects the singular accusative target. |
| `act-2/1` | inline | Він їсть... | рибу | C | M37; U16/U48/U60. The key рибу has the required food-object case or verb agreement. No second displayed option satisfies this unchanged task. |
| `act-2/2` | inline | Ми п'ємо... | сік | D | M37; U48; U60. The offered genitive can express a partial quantity; каші, кави or м'яса also have plural accusative analyses where present. The case-and-number cue selects the singular accusative target. |
| `act-2/3` | inline | Вона їсть... | м'ясо | D | M37; U48; U60. The offered genitive can express a partial quantity; каші, кави or м'яса also have plural accusative analyses where present. The case-and-number cue selects the singular accusative target. |
| `act-2/4` | inline | Вони п'ють... | воду | C | M37; U16/U48/U60. The key воду has the required food-object case or verb agreement. No second displayed option satisfies this unchanged task. |
| `act-2/5` | inline | Ти їси... | кашу | D | M37; U48; U60. The offered genitive can express a partial quantity; каші, кави or м'яса also have plural accusative analyses where present. The case-and-number cue selects the singular accusative target. |
| `act-4/0` | inline | Я ___ суп. | їм | C | M37; U16/U48/U60. The key їм has the required food-object case or verb agreement. No second displayed option satisfies this unchanged task. |
| `act-4/1` | inline | Ми ___ чай. | п'ємо | C | M37; U16/U48/U60. The key п'ємо has the required food-object case or verb agreement. No second displayed option satisfies this unchanged task. |
| `act-4/2` | inline | Вона ___ хліб. | їсть | C | M37; U16/U48/U60. The key їсть has the required food-object case or verb agreement. No second displayed option satisfies this unchanged task. |
| `act-4/3` | inline | Вони ___ воду. | п'ють | C | M37; U16/U48/U60. The key п'ють has the required food-object case or verb agreement. No second displayed option satisfies this unchanged task. |
| `act-4/4` | inline | Ти ___ рибу? | їси | C | M37; U16/U48/U60. The key їси has the required food-object case or verb agreement. No second displayed option satisfies this unchanged task. |
| `act-4/5` | inline | Ви ___ каву? | п'єте | C | M37; U16/U48/U60. The key п'єте has the required food-object case or verb agreement. No second displayed option satisfies this unchanged task. |
| `act-4/6` | inline | Він ___ сік. | п'є | C | M37; U16/U48/U60. The key п'є has the required food-object case or verb agreement. No second displayed option satisfies this unchanged task. |
| `act-4/7` | inline | Вони ___ кашу. | їдять | C | M37; U16/U48/U60. The key їдять has the required food-object case or verb agreement. No second displayed option satisfies this unchanged task. |

### 38. at-the-cafe

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-2/0` | inline | Мені ___, будь ласка. | каву | C | M38; U15/U48/U56/U57/U58/U60. The key каву matches the explicitly named cafe situation or the required object form; competing options do not. |
| `act-2/1` | inline | Мені ___, будь ласка. | воду | C | M38; U15/U48/U56/U57/U58/U60. The key воду matches the explicitly named cafe situation or the required object form; competing options do not. |
| `act-2/2` | inline | Мені ___, будь ласка. | борщ | D | M38; U41; U48; U60. A cafe request may take the offered partitive genitive. The cue selects the unchanged singular accusative key. |
| `act-2/3` | inline | Мені ___, будь ласка. | салат | D | M38; U41; U48; U60. A cafe request may take the offered partitive genitive. The cue selects the unchanged singular accusative key. |
| `act-2/4` | inline | Дайте, будь ласка, ___. | чай | D | M38; U41; U48; U60. A cafe request may take the offered partitive genitive. The cue selects the unchanged singular accusative key. |
| `act-2/5` | inline | Я буду ___. | піцу | C | M38; U15/U48/U56/U57/U58/U60. The key піцу matches the explicitly named cafe situation or the required object form; competing options do not. |
| `act-2/6` | inline | Можна ___? | хліб | D | M38; U41; U48; U60. A cafe request may take the offered partitive genitive. The cue selects the unchanged singular accusative key. |
| `act-2/7` | inline | Мені ___ із собою, будь ласка. | маленьку каву | D | M38; U41; U48; U60. A cafe request may take the offered partitive genitive. The cue selects the unchanged singular accusative key. |
| `act-3/0` | inline | You want to order coffee. | Мені каву, будь ласка. | C | M38; U15/U48/U56/U57/U58/U60. The key Мені каву, будь ласка. matches the explicitly named cafe situation or the required object form; competing options do not. |
| `act-3/1` | inline | You want to pay. | Рахунок, будь ласка. | C | M38; U15/U48/U56/U57/U58/U60. The key Рахунок, будь ласка. matches the explicitly named cafe situation or the required object form; competing options do not. |
| `act-3/2` | inline | You want to know the price. | Скільки коштує? | C | M38; U15/U48/U56/U57/U58/U60. The key Скільки коштує? matches the explicitly named cafe situation or the required object form; competing options do not. |
| `act-3/3` | inline | You want a recommendation. | Що ви рекомендуєте? | C | M38; U15/U48/U56/U57/U58/U60. The key Що ви рекомендуєте? matches the explicitly named cafe situation or the required object form; competing options do not. |
| `act-3/4` | inline | You want to praise the food. | Все було дуже смачно! | C | M38; U15/U48/U56/U57/U58/U60. The key Все було дуже смачно! matches the explicitly named cafe situation or the required object form; competing options do not. |
| `act-3/5` | inline | You want to know whether a seat is free. | Тут вільно? | C | M38; U15/U48/U56/U57/U58/U60. The key Тут вільно? matches the explicitly named cafe situation or the required object form; competing options do not. |
| `act-3/6` | inline | You want to know whether a dish is spicy. | Це гостре? | C | M38; U15/U48/U56/U57/U58/U60. The key Це гостре? matches the explicitly named cafe situation or the required object form; competing options do not. |
| `act-3/7` | inline | You want to pay by card. | Можна карткою? | C | M38; U15/U48/U56/U57/U58/U60. The key Можна карткою? matches the explicitly named cafe situation or the required object form; competing options do not. |
| `act-4/0` | inline | Добрий день! Ось ___. | меню | D | M38; U57; U58. A greeting alone does not fix which object is handed over: menu, bill or card. The situation cue selects меню. |
| `act-4/1` | inline | Дякую. Що ви ___? | рекомендуєте | C | M38; U15/U26/U56. The cafe dialogue asks for a recommendation or a drink after the food order. Merely grammatical questions about paying or reading were not confirmed as alternatives in that conversational role; no edit. |
| `act-4/2` | inline | Борщ дуже ___. | смачний | C | M38; U15/U48/U56/U57/U58/U60. The key смачний matches the explicitly named cafe situation or the required object form; competing options do not. |
| `act-4/3` | inline | Добре, ___ борщ і хліб, будь ласка. | мені | C | M38; U15/U48/U56/U57/U58/U60. The key мені matches the explicitly named cafe situation or the required object form; competing options do not. |
| `act-4/4` | inline | А що будете ___? | пити | C | M38; U15/U26/U56. The cafe dialogue asks for a recommendation or a drink after the food order. Merely grammatical questions about paying or reading were not confirmed as alternatives in that conversational role; no edit. |
| `act-4/5` | inline | Добре, одну ___. | хвилинку | D | M38; U57. Одну годину can also complete the waiting expression, and одну картку is an object phrase. The moment cue selects хвилинку. |

### 39. shopping

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | Скільки ___ хліб? | коштує | C | M39; U23/U32/U69. The key коштує matches the stated quantity, product or subject agreement. The alternatives do not fit that specific form or ordinary product construction. |
| `act-1/1` | inline | Скільки ___ молоко? | коштує | C | M39; U23/U32/U69. The key коштує matches the stated quantity, product or subject agreement. The alternatives do not fit that specific form or ordinary product construction. |
| `act-1/2` | inline | Скільки ___ цей сир? | коштує | C | M39; U23/U32/U69. The key коштує matches the stated quantity, product or subject agreement. The alternatives do not fit that specific form or ordinary product construction. |
| `act-1/3` | inline | Скільки ___ яблука? | коштують | C | M39; U23/U32/U69. The key коштують matches the stated quantity, product or subject agreement. The alternatives do not fit that specific form or ordinary product construction. |
| `act-1/4` | inline | Скільки ___ помідори? | коштують | C | M39; U23/U32/U69. The key коштують matches the stated quantity, product or subject agreement. The alternatives do not fit that specific form or ordinary product construction. |
| `act-1/5` | inline | Скільки ___ пляшка води? | коштує | C | M39; U23/U32/U69. The key коштує matches the stated quantity, product or subject agreement. The alternatives do not fit that specific form or ordinary product construction. |
| `act-1/6` | inline | Скільки ___ три пляшки води? | коштують | D | M39; U54; U69. A quantified subject can take a singular or plural predicate. The cue selects the original plural key without calling the singular impossible. |
| `act-1/7` | inline | Скільки ___ ця сукня? | коштує | C | M39; U23/U32/U69. The key коштує matches the stated quantity, product or subject agreement. The alternatives do not fit that specific form or ordinary product construction. |
| `act-2/0` | inline | 21 ___ | гривня | C | M39; U23/U32/U69. The key гривня matches the stated quantity, product or subject agreement. The alternatives do not fit that specific form or ordinary product construction. |
| `act-2/1` | inline | 32 ___ | гривні | C | M39; U23/U32/U69. The key гривні matches the stated quantity, product or subject agreement. The alternatives do not fit that specific form or ordinary product construction. |
| `act-2/2` | inline | 45 ___ | гривень | C | M39; U23/U32/U69. The key гривень matches the stated quantity, product or subject agreement. The alternatives do not fit that specific form or ordinary product construction. |
| `act-2/3` | inline | 100 ___ | гривень | C | M39; U23/U32/U69. The key гривень matches the stated quantity, product or subject agreement. The alternatives do not fit that specific form or ordinary product construction. |
| `act-2/4` | inline | 1 ___ | гривня | C | M39; U23/U32/U69. The key гривня matches the stated quantity, product or subject agreement. The alternatives do not fit that specific form or ordinary product construction. |
| `act-2/5` | inline | 3 ___ | гривні | C | M39; U23/U32/U69. The key гривні matches the stated quantity, product or subject agreement. The alternatives do not fit that specific form or ordinary product construction. |
| `act-2/6` | inline | 10 ___ | гривень | C | M39; U23/U32/U69. The key гривень matches the stated quantity, product or subject agreement. The alternatives do not fit that specific form or ordinary product construction. |
| `act-2/7` | inline | 54 ___ | гривні | C | M39; U23/U32/U69. The key гривні matches the stated quantity, product or subject agreement. The alternatives do not fit that specific form or ordinary product construction. |
| `act-4/0` | inline | Дайте, будь ласка, ___ яблук. | один кілограм | C | M39; U23/U32/U69. The key один кілограм matches the stated quantity, product or subject agreement. The alternatives do not fit that specific form or ordinary product construction. |
| `act-4/1` | inline | Дайте ___ молока. | літр | D | M39; U23; U31. Both літр молока and пляшку молока are normal quantities. The volume cue selects літр. |
| `act-4/2` | inline | Дайте ___ води. | пляшку | D | M39; U57; U68. Water can be measured by a bottle or by mass; the container cue selects пляшку. |
| `act-4/3` | inline | Дайте ___ чаю. | пачку | D | M39; U23; U30; U67. Літр чаю and пляшку чаю are attested prepared-drink quantities. The dry-packet cue selects пачку. |
| `act-4/4` | inline | Дайте ___ хліба. | буханку | C | M39; U23/U32/U69. The key буханку matches the stated quantity, product or subject agreement. The alternatives do not fit that specific form or ordinary product construction. |
| `act-4/5` | inline | Дайте, будь ласка, ___ помідорів. | два кілограми | C | M39; U23/U32/U69. The key два кілограми matches the stated quantity, product or subject agreement. The alternatives do not fit that specific form or ordinary product construction. |
| `act-4/6` | inline | Купіть три ___ води. | пляшки | C | M39; U23/U32/U69. The key пляшки matches the stated quantity, product or subject agreement. The alternatives do not fit that specific form or ordinary product construction. |

### 40. people-around-me

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-1/0` | inline | вчитель | хто? | C | M40; The VESUM animacy analysis supports хто? for the named noun in this grammatical хто/що contrast. |
| `act-1/1` | inline | лікар | хто? | C | M40; The VESUM animacy analysis supports хто? for the named noun in this grammatical хто/що contrast. |
| `act-1/2` | inline | тато | хто? | C | M40; The VESUM animacy analysis supports хто? for the named noun in this grammatical хто/що contrast. |
| `act-1/3` | inline | кіт | хто? | C | M40; The VESUM animacy analysis supports хто? for the named noun in this grammatical хто/що contrast. |
| `act-1/4` | inline | дерево | що? | C | M40; The VESUM animacy analysis supports що? for the named noun in this grammatical хто/що contrast. |
| `act-1/5` | inline | хліб | що? | C | M40; The VESUM animacy analysis supports що? for the named noun in this grammatical хто/що contrast. |
| `act-1/6` | inline | книга | що? | C | M40; The VESUM animacy analysis supports що? for the named noun in this grammatical хто/що contrast. |
| `act-1/7` | inline | подруга | хто? | C | M40; The VESUM animacy analysis supports хто? for the named noun in this grammatical хто/що contrast. |
| `act-2/0` | inline | Я бачу ___. | маму | C | M40; The form маму supplies the required person/object case or subject-matching verb; the displayed alternatives do not. NAMES confirms personal-name forms. |
| `act-2/1` | inline | Я бачу ___. | брата | C | M40; The form брата supplies the required person/object case or subject-matching verb; the displayed alternatives do not. NAMES confirms personal-name forms. |
| `act-2/2` | inline | Я знаю ___. | Олену | C | M40; The form Олену supplies the required person/object case or subject-matching verb; the displayed alternatives do not. NAMES confirms personal-name forms. |
| `act-2/3` | inline | Я знаю ___. | друга | C | M40; The form друга supplies the required person/object case or subject-matching verb; the displayed alternatives do not. NAMES confirms personal-name forms. |
| `act-2/4` | inline | Я люблю ___. | тата | C | M40; The form тата supplies the required person/object case or subject-matching verb; the displayed alternatives do not. NAMES confirms personal-name forms. |
| `act-2/5` | inline | Я чекаю ___. | вчителя | C | M40; The form вчителя supplies the required person/object case or subject-matching verb; the displayed alternatives do not. NAMES confirms personal-name forms. |
| `act-2/6` | inline | Я шукаю ___. | подругу | C | M40; The form подругу supplies the required person/object case or subject-matching verb; the displayed alternatives do not. NAMES confirms personal-name forms. |
| `act-2/7` | inline | Я бачу ___. | сусіда | C | M40; The form сусіда supplies the required person/object case or subject-matching verb; the displayed alternatives do not. NAMES confirms personal-name forms. |
| `act-2/8` | inline | Я чекаю ___. | лікаря | C | M40; The form лікаря supplies the required person/object case or subject-matching verb; the displayed alternatives do not. NAMES confirms personal-name forms. |
| `act-2/9` | inline | Я знаю ___. | сестру | C | M40; The form сестру supplies the required person/object case or subject-matching verb; the displayed alternatives do not. NAMES confirms personal-name forms. |
| `workbook[0]/0` | workbook | — Кого ти ___? | бачиш | C | M40; The form бачиш supplies the required person/object case or subject-matching verb; the displayed alternatives do not. NAMES confirms personal-name forms. |
| `workbook[0]/1` | workbook | — Я бачу ___ і маму. | брата | C | M40; The form брата supplies the required person/object case or subject-matching verb; the displayed alternatives do not. NAMES confirms personal-name forms. |
| `workbook[0]/2` | workbook | — Ти знаєш мого ___ Тараса? | друга | C | M40; The form друга supplies the required person/object case or subject-matching verb; the displayed alternatives do not. NAMES confirms personal-name forms. |
| `workbook[0]/3` | workbook | — Ні, я не ___ твого друга. | знаю | C | M40; The form знаю supplies the required person/object case or subject-matching verb; the displayed alternatives do not. NAMES confirms personal-name forms. |
| `workbook[0]/4` | workbook | — А кого ти ___? | чекаєш | C | M40; The form чекаєш supplies the required person/object case or subject-matching verb; the displayed alternatives do not. NAMES confirms personal-name forms. |
| `workbook[0]/5` | workbook | — Я чекаю ___. | лікаря | C | M40; The form лікаря supplies the required person/object case or subject-matching verb; the displayed alternatives do not. NAMES confirms personal-name forms. |

### 41. checkpoint-food-shopping

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-2/0` | inline | Я їм ___. | салат | D | M41; U48; U60. The original options include a defensible partitive genitive or plural accusative. The case-and-number cue selects the existing singular accusative key. |
| `act-2/1` | inline | Я бачу ___. | брата | C | M41; U16/U17/U28/U32/U48/U59/U60. The key брата matches the stated food/object, numeral, meal or repair task. No second option is supported in that task. |
| `act-2/2` | inline | Я п'ю ___. | воду | D | M41; U48; U60. The original options include a defensible partitive genitive or plural accusative. The case-and-number cue selects the existing singular accusative key. |
| `act-2/3` | inline | Я знаю ___. | Олену | C | M41; U16/U17/U28/U32/U48/U59/U60. The key Олену matches the stated food/object, numeral, meal or repair task. No second option is supported in that task. |
| `act-2/4` | inline | Я люблю ___. | борщ | C | M41; U16/U17/U28/U32/U48/U59/U60. The key борщ matches the stated food/object, numeral, meal or repair task. No second option is supported in that task. |
| `act-2/5` | inline | Я чекаю ___. | друга | C | M41; U16/U17/U28/U32/U48/U59/U60. The key друга matches the stated food/object, numeral, meal or repair task. No second option is supported in that task. |
| `act-2/6` | inline | Я купую ___. | хліб | D | M41; U48; U60. The original options include a defensible partitive genitive or plural accusative. The case-and-number cue selects the existing singular accusative key. |
| `act-2/7` | inline | Я бачу ___. | лікаря | C | M41; U16/U17/U28/U32/U48/U59/U60. The key лікаря matches the stated food/object, numeral, meal or repair task. No second option is supported in that task. |
| `act-2/8` | inline | Я їм ___. | піцу | D | M41; U48; U60. The original options include a defensible partitive genitive or plural accusative. The case-and-number cue selects the existing singular accusative key. |
| `act-2/9` | inline | Я люблю ___. | маму | C | M41; U16/U17/U28/U32/U48/U59/U60. The key маму matches the stated food/object, numeral, meal or repair task. No second option is supported in that task. |
| `act-3/0` | inline | — Що ти їси на сніданок? — Я їм ___ і п'ю каву. | кашу | D | M41; U48; U60. The original options include a defensible partitive genitive or plural accusative. The case-and-number cue selects the existing singular accusative key. |
| `act-3/1` | inline | — Потім іду на ринок. Скільки ___ помідори? | коштують | C | M41; U16/U17/U28/U32/U48/U59/U60. The key коштують matches the stated food/object, numeral, meal or repair task. No second option is supported in that task. |
| `act-3/2` | inline | — Тридцять ___. | гривень | C | M41; U16/U17/U28/U32/U48/U59/U60. The key гривень matches the stated food/object, numeral, meal or repair task. No second option is supported in that task. |
| `act-3/3` | inline | — Дайте ___ яблук, будь ласка. | кілограм | C | M41; U16/U17/U28/U32/U48/U59/U60. The key кілограм matches the stated food/object, numeral, meal or repair task. No second option is supported in that task. |
| `act-3/4` | inline | — Потім у кафе: ___ борщ і воду, будь ласка. | Мені | C | M41; U16/U17/U28/U32/U48/U59/U60. The key Мені matches the stated food/object, numeral, meal or repair task. No second option is supported in that task. |
| `act-3/5` | inline | — Рахунок, будь ласка. Можна ___? | карткою | C | M41; U16/U17/U28/U32/U48/U59/U60. The key карткою matches the stated food/object, numeral, meal or repair task. No second option is supported in that task. |
| `act-3/6` | inline | — О, я бачу ___! Олено, привіт! | Олену | C | M41; U16/U17/U28/U32/U48/U59/U60. The key Олену matches the stated food/object, numeral, meal or repair task. No second option is supported in that task. |
| `act-3/7` | inline | — Ти знаєш мого ___? | брата | C | M41; U16/U17/U28/U32/U48/U59/U60. The key брата matches the stated food/object, numeral, meal or repair task. No second option is supported in that task. |
| `workbook[2]/0` | workbook | Анна готує ___ з картоплею. | вареники | C | M41; U16/U17/U28/U32/U48/U59/U60. The key вареники matches the stated food/object, numeral, meal or repair task. No second option is supported in that task. |
| `workbook[2]/1` | workbook | Вона ставить на стіл ___. | тарілки | C | M41; U16/U17/U28/U32/U48/U59/U60. The key тарілки matches the stated food/object, numeral, meal or repair task. No second option is supported in that task. |
| `workbook[2]/2` | workbook | Гості беруть ___. | склянки | C | M41; U16/U17/U28/U32/U48/U59/U60. The key склянки matches the stated food/object, numeral, meal or repair task. No second option is supported in that task. |
| `workbook[2]/3` | workbook | Анна каже: ___ | Смачного! | C | M41; U16/U17/U28/U32/U48/U59/U60. The key Смачного! matches the stated food/object, numeral, meal or repair task. No second option is supported in that task. |
| `workbook[2]/4` | workbook | Олена бере ___ хліба. | шматок | C | M41; U16/U17/U28/U32/U48/U59/U60. The key шматок matches the stated food/object, numeral, meal or repair task. No second option is supported in that task. |
| `workbook[2]/5` | workbook | Анна наливає ___ води. | склянку | D | M41; U22; U68. A kilogram is also a possible quantity of water. The drinking-glass cue selects склянку. |
| `workbook[5]/0` | workbook | Repair: Я хочу вода. | Я хочу воду. | C | M41; U16/U17/U28/U32/U48/U59/U60. The key Я хочу воду. matches the stated food/object, numeral, meal or repair task. No second option is supported in that task. |
| `workbook[5]/1` | workbook | Repair: Я люблю борща. | Я люблю борщ. | C | M41; U16/U17/U28/U32/U48/U59/U60. The key Я люблю борщ. matches the stated food/object, numeral, meal or repair task. No second option is supported in that task. |
| `workbook[5]/2` | workbook | Repair: Смачний кава. | Смачна кава. | C | M41; U16/U17/U28/U32/U48/U59/U60. The key Смачна кава. matches the stated food/object, numeral, meal or repair task. No second option is supported in that task. |
| `workbook[5]/3` | workbook | Repair: Я є голодний. | Я голодний. (Або: Я хочу їсти). | C | M41; U17/U91. The A1 interference-repair task selects Я голодний. The exact corpus examples of Я є голодний are foreign-character speech, not evidence for an ordinary A1 alternative; the general copula entry does not settle that register question. No confirmed defect; unchanged. |
| `workbook[5]/4` | workbook | Repair: Моє ім'я є Джон, і я хочу меню. | Мене звати Джон, дайте меню. | D | M41; U17; U90. Two GRAC examples attest a naming statement with Моє ім'я є. The explicit formula and imperative cue selects the requested A1 response without a general grammar claim in feedback. |
| `workbook[5]/5` | workbook | Repair: Чи не могли б ви дати мені рахунок? | Дайте, будь ласка, рахунок. | D | M41; U78. The conditional request is grammatical and polite. The cue requests the already-keyed direct imperative. |
| `workbook[5]/6` | workbook | Repair: Я плачу рублями. | Я плачу гривнями. | D | M41; U26; U27. Рублями is a real currency instrumental and a grammatical payment phrase. The Ukrainian-currency cue selects гривнями. |

### 42. hey-friend

| Item | Section | Original stem | Key | Verdict | Evidence and assessment |
| --- | --- | --- | --- | --- | --- |
| `act-2/0` | inline | ___, привіт! | Олено | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is Олено; the competing nominative, oblique or malformed endings do not satisfy that form. |
| `act-2/1` | inline | Як справи, ___? | Тарасе | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is Тарасе; the competing nominative, oblique or malformed endings do not satisfy that form. |
| `act-2/2` | inline | ___, де мій телефон? | Мамо | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is Мамо; the competing nominative, oblique or malformed endings do not satisfy that form. |
| `act-2/3` | inline | Ходи сюди, ___! | Іване | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is Іване; the competing nominative, oblique or malformed endings do not satisfy that form. |
| `act-2/4` | inline | Будь обережний, ___! | синку | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is синку; the competing nominative, oblique or malformed endings do not satisfy that form. |
| `act-2/5` | inline | Привіт, ___! | Андрію | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is Андрію; the competing nominative, oblique or malformed endings do not satisfy that form. |
| `act-2/6` | inline | Добрий день, ___ Іване! | пане | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is пане; the competing nominative, oblique or malformed endings do not satisfy that form. |
| `act-2/7` | inline | Гей, ___! | друже | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is друже; the competing nominative, oblique or malformed endings do not satisfy that form. |
| `act-3/0` | inline | Олена -> ___ | Олено | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is Олено; the competing nominative, oblique or malformed endings do not satisfy that form. |
| `act-3/1` | inline | Тарас -> ___ | Тарасе | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is Тарасе; the competing nominative, oblique or malformed endings do not satisfy that form. |
| `act-3/2` | inline | мама -> ___ | мамо | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is мамо; the competing nominative, oblique or malformed endings do not satisfy that form. |
| `act-3/3` | inline | Іван -> ___ | Іване | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is Іване; the competing nominative, oblique or malformed endings do not satisfy that form. |
| `act-3/4` | inline | сестра -> ___ | сестро | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is сестро; the competing nominative, oblique or malformed endings do not satisfy that form. |
| `act-3/5` | inline | Андрій -> ___ | Андрію | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is Андрію; the competing nominative, oblique or malformed endings do not satisfy that form. |
| `act-3/6` | inline | подруга -> ___ | подруго | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is подруго; the competing nominative, oblique or malformed endings do not satisfy that form. |
| `act-3/7` | inline | брат -> ___ | брате | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is брате; the competing nominative, oblique or malformed endings do not satisfy that form. |
| `act-3/8` | inline | Марія -> ___ | Маріє | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is Маріє; the competing nominative, oblique or malformed endings do not satisfy that form. |
| `act-3/9` | inline | бабуся -> ___ | бабусю | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is бабусю; the competing nominative, oblique or malformed endings do not satisfy that form. |
| `workbook[0]/0` | workbook | — ___, привіт! Як справи? | Олено | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is Олено; the competing nominative, oblique or malformed endings do not satisfy that form. |
| `workbook[0]/1` | workbook | — Добре, дякую, ___! | Тарасе | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is Тарасе; the competing nominative, oblique or malformed endings do not satisfy that form. |
| `workbook[0]/2` | workbook | — ___, де мій телефон? | Мамо | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is Мамо; the competing nominative, oblique or malformed endings do not satisfy that form. |
| `workbook[0]/3` | workbook | — На столі, ___. | синку | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is синку; the competing nominative, oblique or malformed endings do not satisfy that form. |
| `workbook[0]/4` | workbook | — ___, ми йдемо! | Бабусю | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is Бабусю; the competing nominative, oblique or malformed endings do not satisfy that form. |
| `workbook[0]/5` | workbook | — Добре, до побачення, ___! | Андрію | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is Андрію; the competing nominative, oblique or malformed endings do not satisfy that form. |
| `workbook[0]/6` | workbook | — Добрий день, ___ Оксано. | пані | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is пані; the competing nominative, oblique or malformed endings do not satisfy that form. |
| `workbook[0]/7` | workbook | — ___, радий тебе бачити! | Друже | C | M42; U28; NAMES/NAME-STRESS. The requested direct-address form is Друже; the competing nominative, oblique or malformed endings do not satisfy that form. |

## Confirmed defects and fixes

Every repair retains the answer meaning and correct-option index. All but the three stated spelling corrections retain the key text. Changes are English task cues, distractors, or the feedback needed to keep a repaired cue accurate. Each row below corresponds to one D verdict. Source YAML is authoritative; the existing parser and serializer regenerate only those changed item objects in the tracked pages.

| Item | Evidence | Source changes |
| --- | --- | --- |
| `where-is-it/act-1/6` | U6, U64, U82 | option 1: в → без |
| `my-city/act-2/2` | U10, U64 | option 1: Вона у вокзалі. → Вона до вокзалі. |
| `where-to/act-2/4` | U10, U64 | option 1: в → до; option 2: у → біля |
| `transport/act-2/5` | U21 | sentence: (Ask about departure time.) О котрій ___? |
| `transport/act-3/0` | U9, U13 | prompt: (Use one word in the instrumental case.) How do you say by bus? |
| `around-the-city/act-1/0` | U14, U20 | sentence: (Go straight, then right.) Ідіть ___, потім направо. |
| `around-the-city/act-1/3` | U14 | sentence: (Next, go right.) Потім ідіть ___, школа там. |
| `around-the-city/act-2/1` | U14, U61, U64 | prompt: (Name your destination.) Я йду... |
| `around-the-city/act-2/3` | U13, U64 | prompt: (Name your destination.) Потім їду на... |
| `around-the-city/act-2/5` | U14, U61, U64 | prompt: (Name her destination.) Вона йде в... |
| `around-the-city/act-5/0` | U20 | sentence: (The pharmacy is nearby.) Аптека ___. П'ять хвилин пішки. |
| `around-the-city/act-5/1` | U20 | sentence: (The station is far away.) Вокзал ___. Їдьте на метро. |
| `around-the-city/act-5/4` | U14, U20 | sentence: (Go straight, then left.) Ідіть ___, потім наліво. |
| `where-from/act-3/3` | U7, U11 | option 1: з США → США |
| `where-from/workbook[4]/0` | U64, U65 | sentence: (State the place of origin: Ukraine.) Я ___, з Києва. |
| `where-from/workbook[4]/1` | U64, U65 | sentence: (State the place of origin: Canada.) Анна ___, із Торонто. |
| `where-from/workbook[4]/2` | U64, U65 | sentence: (State the place of origin: Lviv.) Олена живе в Києві, але вона ___. |
| `where-from/workbook[4]/5` | U64, U65 | sentence: (State the place of origin: Kyiv.) Марко ___ і говорить українською. |
| `checkpoint-places/act-4/0` | U6, U64 | option 1: у → до; explanation: В Одесі answers the static-location question де? in this sentence. |
| `checkpoint-places/act-4/2` | U14, U64, U65 | sentence: (You are leaving the cafe.) Я йду ___ кафе. |
| `checkpoint-places/act-4/3` | U6, U84, U85 | option 1: в → без; sentence: Потім вони йдуть ___ порт.; explanation: Between the consonants in йдуть and порт, use у порт for the destination. |
| `checkpoint-places/act-4/5` | U65 | sentence: (The station is your destination.) Увечері я їду ___. |
| `checkpoint-places/workbook[2]/1` | U14, U61, U64, U83, U84, U85 | prompt: (Give the destination: school.) Rephrase: Я йду в школі.; option 0: Я іду в школу. → Я йду в школу.; explanation: For the destination, use в школу. After Я, the euphonic verb form is йду. |
| `checkpoint-places/workbook[2]/3` | U17 | prompt: (Give the shorter version without є.) Rephrase: Книга є на столі.; explanation: The requested A1 place pattern is Книга на столі. |
| `checkpoint-places/workbook[4]/2` | U6, U64 | option 1: у → до |
| `checkpoint-places/workbook[4]/5` | U65 | sentence: (The station is her destination.) Після музею вона їде ___. |
| `food-and-drink/workbook[3]/1` | U15, U24 | sentence: (Name the midday meal.) Вдень я ___. |
| `food-and-drink/workbook[3]/3` | U16, U25, U29 | sentence: (Use їсти: I eat borscht.) Я ___ борщ. |
| `food-and-drink/workbook[3]/5` | U64, U65 | sentence: (With milk.) Я хочу каву ___. |
| `i-eat-i-drink/act-1/4` | U48, U60 | sentence: (Use the accusative singular.) Вони їдять ___. |
| `i-eat-i-drink/act-1/6` | U48, U60 | sentence: (Use the accusative singular.) Я їм ___. |
| `i-eat-i-drink/act-1/7` | U48, U60 | sentence: (Use the accusative singular.) Вона їсть ___. |
| `i-eat-i-drink/act-2/0` | U48, U60 | prompt: (Use the accusative singular.) Я п'ю... |
| `i-eat-i-drink/act-2/2` | U48, U60 | prompt: (Use the accusative singular.) Ми п'ємо... |
| `i-eat-i-drink/act-2/3` | U48, U60 | prompt: (Use the accusative singular.) Вона їсть... |
| `i-eat-i-drink/act-2/5` | U48, U60 | prompt: (Use the accusative singular.) Ти їси... |
| `at-the-cafe/act-2/2` | U41, U48, U60 | sentence: (Use the accusative singular.) Мені ___, будь ласка. |
| `at-the-cafe/act-2/3` | U41, U48, U60 | sentence: (Use the accusative singular.) Мені ___, будь ласка. |
| `at-the-cafe/act-2/4` | U41, U48, U60 | sentence: (Use the accusative singular.) Дайте, будь ласка, ___. |
| `at-the-cafe/act-2/6` | U41, U48, U60 | sentence: (Use the accusative singular.) Можна ___? |
| `at-the-cafe/act-2/7` | U41, U48, U60 | sentence: (Use the accusative singular.) Мені ___ із собою, будь ласка. |
| `at-the-cafe/act-4/0` | U57, U58 | sentence: (The server brings the menu.) Добрий день! Ось ___. |
| `at-the-cafe/act-4/5` | U57 | sentence: (Ask the customer to wait a moment.) Добре, одну ___. |
| `shopping/act-1/6` | U54, U69 | sentence: (Use the plural verb form.) Скільки ___ три пляшки води?; explanation: The requested plural form is коштують. A singular predicate can also occur with a quantified subject. |
| `shopping/act-4/1` | U23, U31 | sentence: (Ask for one litre.) Дайте ___ молока. |
| `shopping/act-4/2` | U57, U68 | sentence: (Ask for one bottle.) Дайте ___ води. |
| `shopping/act-4/3` | U23, U30, U67 | sentence: (Ask for one packet of dry tea.) Дайте ___ чаю. |
| `checkpoint-food-shopping/act-2/0` | U48, U60 | prompt: (Use the accusative singular.) Я їм ___. |
| `checkpoint-food-shopping/act-2/2` | U48, U60 | prompt: (Use the accusative singular.) Я п'ю ___. |
| `checkpoint-food-shopping/act-2/6` | U48, U60 | prompt: (Use the accusative singular.) Я купую ___. |
| `checkpoint-food-shopping/act-2/8` | U48, U60 | prompt: (Use the accusative singular.) Я їм ___. |
| `checkpoint-food-shopping/act-3/0` | U48, U60 | sentence: (Use the accusative singular.) — Що ти їси на сніданок? — Я їм ___ і п'ю каву. |
| `checkpoint-food-shopping/workbook[2]/5` | U22, U68 | sentence: (Measure the water in one drinking glass.) Анна наливає ___ води. |
| `checkpoint-food-shopping/workbook[5]/4` | U17, U90 | prompt: (Use the Мене звати formula and an imperative request.) Rephrase: Моє ім'я є Джон, і я хочу меню.; explanation: Мене звати Джон is the requested name formula, and дайте is the requested imperative. |
| `checkpoint-food-shopping/workbook[5]/5` | U78 | prompt: (Use a direct imperative with будь ласка.) Rephrase: Чи не могли б ви дати мені рахунок?; explanation: The requested direct imperative is Дайте, будь ласка, рахунок. The conditional request is also grammatical and polite. |
| `checkpoint-food-shopping/workbook[5]/6` | U26, U27 | prompt: (Name the Ukrainian currency used for this payment.) Repair: Я плачу рублями. |
| `around-the-city/act-5/2` | U20, U87 | sentence: (The cafe is nearby.) Кафе ___. Воно біля дому. |
| `where-is-it/act-1/7` | U6, U84, U85 | prompt: Марко зараз ___ лікарні. |
| `where-is-it/act-2/5` | U6, U84, U85 | sentence: Ми зараз ___ (місто). |
| `where-is-it/act-2/6` | U6, U84, U85 | sentence: Софія зараз ___ (лікарня). |
| `where-is-it/act-2/7` | U6, U84, U85 | sentence: Я зараз ___ (Київ). |
| `where-to/act-2/0` | U6, U84, U85 | sentence: Вони йдуть ___ банк. |
| `where-to/act-2/3` | U6, U84, U85 | sentence: Вони йдуть у ___. |
| `where-from/workbook[4]/4` | U6, U84, U85 | sentence: Джон ___, але зараз живе в Києві. |
| `where-is-it/act-4/4` | U6 | option 0: Він живе у Києві. → Він живе в Києві.; explanation: After the vowel in живе, use в Києві for this static city location. |
| `where-to/act-4/3` | U83, U88, U89 | option 0: Степан йде на пошту. → Степан іде на пошту.; explanation: Walking uses іде here. After the consonant in Степан, choose the euphonic іде form. |

## Validation and batch sizing

- Structural scanner: `scripts/audit/scan_activity_errors.py --track a1-v1`, 55/55 files, zero findings, exit 0 before and after repair.
- Existing affected checks: `pytest -n 2 tests/test_scan_activity_errors.py tests/test_a1_activity_schema_parser_drift.py tests/test_yaml_activities_a1_payload.py tests/test_activity_renderer.py tests/test_generate_mdx.py tests/test_generate_mdx_parsers.py tests/test_generate_mdx_unit_map.py tests/test_generate_mdx_v7_resources_vocab.py tests/test_curriculum_manifest_canary.py`, run together with the existing source-policy guard: 342 passed in 12.10 seconds. No test file or case was added.
- The existing ActivityParser, yaml_activities_to_jsx and dump_json_for_jsx regenerated exactly 66 changed tracked item payloads in 12 modules. Unchanged source objects and page bytes outside those serialized objects are preserved. The integrity manifest updates only the corresponding 24 hashes. Archived unaccented page conventions are retained.
- Chromium exercised the existing Quiz and FillIn components with all 63 changed items that have choices: 63 keys accepted, all 126 distractors rejected, zero browser errors. Three other changed payloads have no options; they received source and Sources verification, but cannot receive positive browser-answer proof through the existing dropdown. A separate live component check confirmed all 14 pre-existing empty FillIn dropdowns have only a disabled placeholder and a disabled Check Answers button. Runtime package and lockfile hashes matched before dependencies were copied into the worktree.
- Independent Gemini through AGY and Opus 5.5 through Claude review, admission CI and merge receipts are recorded on the PR at its exact pushed head. This document records the author audit; it does not assert independent approval or site deployment.

The full census is 326 items: 269 inline/root and 57 workbook items. The inventory started at 2026-10-28T20:03:31.016106+00:00. The initial author report, before independent review, took 20.3 wall-clock minutes and recorded 57 ambiguities. The revised report was prepared at 2026-10-28T20:51:14.025127+00:00, 47.7 minutes after inventory. This later interval includes review, the additional sibling checks, source repairs, new Sources screens and repeated artifact validation. It is not pure model throughput. End-to-end time through review, CI and merge is recorded on the PR after landing; module-count scaling is not a measured full-track duration.

Residual owner: CTO curriculum coordinator, #8893. Unchecked activity types, other modules and finale items, broader independent evaluation, audio and production delivery remain outside this slice. The module-15-28 worker retains its disjoint ownership. Shared integrity-manifest changes require rebase and scoped regeneration if another batch merges first.

## Review corrections and tracked follow-ups

F1 is fixed by changing the port stem to Потім вони йдуть ___ порт. The consonant-final йдуть makes the preserved у normative under Pravopys section 23, and the explanation gives that rule. The original port key conflicted with its vowel-final context; it is classified as a key-context defect rather than an answer ambiguity.

F2 uses both remedies permitted by the review. The Я є голодний item is restored unchanged as checked-clean: the exact corpus examples are foreign-character speech and do not confirm an ordinary A1 rival. The other two items use the cue-and-feedback remedy. The two retained copula/name repairs retain explicit short-pattern cues, use Rephrase instead of Repair, and give only the requested A1 pattern in feedback. No learner-facing explanation now announces that a lesson-labelled bad example is also grammatical. The source evidence and the report distinguish general copula grammar from the module's requested A1 pattern. The existing prose and other activity types are unchanged; any broader reconciliation of their absolute bad labels belongs to the CTO curriculum coordinator on #8893, including the earlier batch's analogous wording.

F3 is fixed in around-the-city/act-5/2. VTS направо has a static right-hand-side sense, so the cafe can be both to the right and near home. The new proximity cue selects поруч.

F4's in-scope euphony class was checked across every completed keyed item. All eleven confirmed affected items are repaired, including the additional same-class siblings discovered in that census. У Львів remains unchanged because section 23 specifically requires у before льв-. Three full-sentence keys receive spelling-only corrections; the other cases change sentence context while preserving the encoded answer. U83 gives the initial і-/й- rule. U84/U85 and U88/U89 check the forms and stress. The stress tool labels monosyllabic йде and йдуть invalid_input; VESUM verifies them and no stress mark is asserted for them.

F5's report wording is corrected. Exactly 14 declared source fill-ins have no authored options: where-is-it/act-2 (8) and my-city/act-3 (6). The live tracked-component check confirms that their empty dropdowns cannot be answered. Three receive language-context repairs in this batch, but their existing answerability limitation remains; no browser success is claimed for those three. This is an explicit pre-existing renderer/source-contract residual, not a free-text feature. Owner: CTO curriculum coordinator, #8893. The other eight cited hey-friend items are ErrorCorrection payloads, not FillIn; they are outside the 326-item fill-in/quiz denominator and their answerability is not certified here.

F6 is fixed: the Одесі explanation no longer compares an option that was removed, and the grammatical conditional request is labelled Rephrase under its explicit imperative cue. G1, the first Gemini report's inaccurate alternative lists, was corrected by its source-fidelity verification round. The final moved head still requires fresh exact-head approvals from both seats. No superseded verdict authorizes landing it.
