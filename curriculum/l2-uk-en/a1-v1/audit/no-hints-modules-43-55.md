# A1 exercise prompts without answer hints, modules 43–55

Refs #8893. Source snapshot: `109d0ab4f8086b463a255c78892c87ce72914d22`.

This repair follows the inventory, source evidence and scoped regeneration method of #11946. The denominator is all 13 manifest modules from `please-do-this` through `a1-finale`, including inline and workbook sections. The scan covers 412 sentence, question and statement fields and 260 visible activity labels across 550 activity items. Matching pairs and supplied word sets remain exercise inputs, not added answer cues.

All 48 answer-bearing prompts changed by #11931 at `e5d74a7d442e3b5ed3e663c234c19d16da3882de` are repaired. The earlier first finale hint from #11911 is also repaired. The wider scan found another 37 older answer-bearing items, including six whose shared instruction named the key. Total: 86 hint-bearing items repaired, 86 items reworded, zero items replaced. All original keys, activity types and language targets remain. The items use Ukrainian speakers, replies and chronology, or alternatives that cannot fit the sentence.

Normal generic English task instructions remain. Headings and instructions that singled out a key are neutral, and task instructions match the revised punctuation, story and dialogue choices. Remaining English grammar questions ask the learner to analyse supplied Ukrainian or choose a compatible form; they do not supply a translation of the answer or prescribe its grammatical form. There are no parenthetical answer cues in the assigned source or published prompt fields.

## Inventory and sources

The [item ledger](no-hints-modules-43-55-items.json) records each original and repaired item, its unchanged key, all wrong alternatives, the reason each fails and Sources locators. The [blind inventory](no-hints-modules-43-55-blind.json) withholds keys and feedback for independent solving. The [check command](no-hints-modules-43-55-check.py) reconciles source, evidence receipts and published payloads and scans every module. Its regex is a guard for the observed cue patterns, not a semantic no-hints oracle. Independent review checks that wider requirement.

The [Sources ledger](no-hints-modules-43-55-evidence.jsonl) contains 60 tool receipts. G1 establishes past gender/number; G2 compound future formation and agreement; G4a courteous ви; G5 the official punctuation rule; G6 imperative morphology; G7 direct-object case. D1–D26 provide modern dictionary meanings relevant to the changed items. The official offline СУМ-20 misses are preserved as misses; the modern ВТС entries are the fallback. D27, the multiword dictionary lookup, is also a miss, not evidence; D25 supplies the equivalence of бо and тому що.

W1 is a case-sensitive diagnostic pass, not a validity verdict. W2 verifies 337/337 distinct forms after normalizing sentence capitalization and apostrophes while retaining proper names. The explanation fragment ли is part of an English ending label, not a taught Ukrainian word. T1 preserves ULIF stress readings and their evidence identifiers, including ambiguous and pending results. This repair adds no stress marks and asserts no unsupported stress choice. P1 screens the first 79 items and all options with VESUM and UA-GEC. Its two VESUM diagnostics are capitalized З and Новим inside the quoted greeting; W2 verifies their normalized forms. Its five UA-GEC notices come from other document contexts, not errors in these items. In particular, opening doors, knowing a meeting time and placing a table are the ordinary senses here.

Verdicts are linguistic inferences from the cited forms, grammar, meanings and each complete task. Morphological existence alone is not a claim that an alternative is valid in the sentence. Receipt hashes cover the retained UTF-8 JSON object with sorted keys and compact separators. Dictionary extracts are bounded and attributed; no empty result is used against a word.

| Module | Hints repaired |
| --- | ---: |
| `please-do-this` | 10 |
| `linking-ideas` | 7 |
| `when-and-where` | 12 |
| `holidays` | 0 |
| `checkpoint-communication` | 11 |
| `what-happened` | 2 |
| `yesterday` | 6 |
| `what-will-happen` | 2 |
| `my-plans` | 8 |
| `my-story` | 9 |
| `health` | 4 |
| `emergencies` | 4 |
| `a1-finale` | 11 |

W3 verifies all 354 distinct final forms after the same normalization. R2W confirms Анна and the locative другій. P2 screens all 86 items together with their visible titles and instructions. Its capitalization diagnostics for З and Новим and its English possessive fragment Анна's are resolved by W3; its UA-GEC notices remain context-specific suspicions.

## Item verdicts

Indices are zero-based. Each row checks the key and every wrong alternative. An explicit activity id is used where present; otherwise the section index is used.

| Item | Key | Why the key fits and every distractor fails | Sources |
| --- | --- | --- | --- |
| `please-do-this/workbook/0/0` | дай | The explicit ти address licenses дай; дайте conflicts with ти and дає is third-person indicative. | G4a, G6, G7, W2, T1, P1, W3, P2 |
| `please-do-this/workbook/0/2` | іди | Ти and готовий identify one familiar addressee; ідіть conflicts with ти and іде is third-person indicative. | G4a, G6, G7, W2, T1, P1, W3, P2 |
| `please-do-this/inline/act-2/0` | Читай, будь ласка. | Ти fixes familiar address: читайте conflicts with it; тексту is genitive/dative rather than the direct object текст. | G4a, G6, G7, W2, T1, P1, W3, P2 |
| `please-do-this/inline/act-2/1` | Читайте, будь ласка. | Пане Іване sets courteous address: читай switches to ти; тексту is not the direct object of читайте. | G4a, G6, G7, W2, T1, P1, W3, P2 |
| `please-do-this/inline/act-2/2` | Дайте рахунок, будь ласка. | Courteous address to the server selects дайте; дай switches register and рахунком is instrumental rather than the direct object рахунок. | G4a, G6, G7, W2, T1, P1, W3, P2 |
| `please-do-this/inline/act-2/3` | Дай меню, будь ласка. | Explicit ти selects дай; дайте conflicts with that address and книжкою is instrumental rather than the required direct object. | G4a, G6, G7, W2, T1, P1, W3, P2 |
| `please-do-this/inline/act-2/4` | Пишіть речення. | Діти and ви identify several addressees: пиши is singular and реченню is dative rather than the direct object речення. | G4a, G6, G7, W2, T1, P1, W3, P2 |
| `please-do-this/inline/act-2/5` | Подивись! | The preceding ти dialogue licenses подивись; both будинком alternatives put an instrumental noun after подивись rather than на будинок. | G4a, G6, G7, W2, T1, P1, W3, P2 |
| `please-do-this/inline/act-2/6` | Скажіть ще раз, будь ласка. | Ще раз expresses repetition. Разу and разів are genitive forms and cannot replace раз after ще without the required construction. | G4a, G6, G7, W2, T1, P1, W3, P2 |
| `please-do-this/inline/act-2/7` | Відкрийте двері. | Друзі identifies several people: відкрий is singular; дверима is instrumental instead of direct-object двері. | G4a, G6, G7, W2, T1, P1, W3, P2 |
| `linking-ideas/inline/act-1/7` | чи | Чи links the alternatives. Бо requires a reason clause and якого cannot coordinate the predicate nouns. | D1, W2, T1, P1, W3, P2 |
| `when-and-where/inline/act-1/0` | що | Що introduces the content clause; якого and якому cannot introduce це кафе. | D2, D3, D4, W2, T1, P1, W3, P2 |
| `when-and-where/inline/act-1/2` | коли | О десятій answers коли, not the location question де; що cannot introduce this time question. | D2, D3, D4, W2, T1, P1, W3, P2 |
| `when-and-where/inline/act-1/4` | де | Де refers to the home already visited; якому requires a noun and куди is a destination, not the location of живеш. | D2, D3, D4, W2, T1, P1, W3, P2 |
| `when-and-where/inline/act-1/5` | коли | О другій is a time answer, so коли fits. Що cannot introduce the question; де asks for a place. | D2, D3, D4, W2, T1, P1, W3, P2 |
| `when-and-where/inline/act-1/6` | що | Що introduces the thought; якого and якому cannot introduce це правильно. | D2, D3, D4, W2, T1, P1, W3, P2 |
| `when-and-where/workbook/1/1` | коли | О третій answers коли. Що cannot introduce this time question; де would ask for a place already supplied by біля фонтану. | D2, D3, D4, W2, T1, P1, W3, P2 |
| `when-and-where/workbook/1/2` | що | Що introduces the observed fact; якого and якому cannot introduce будинок близько. | D2, D3, D4, W2, T1, P1, W3, P2 |
| `when-and-where/workbook/1/5` | коли | The answer о пів на шосту selects коли. Де asks for a place, already supplied by у кафе; що cannot introduce this time question. | D2, D3, D4, W2, T1, P1, W3, P2 |
| `when-and-where/inline/act-4/0` | Я знаю, де кафе. | The key places a comma before the subordinate connector. The second option omits that comma; the third separates the subject from its predicate or the connector from its clause. | G5, W2, T1, P1, W3, P2 |
| `when-and-where/inline/act-4/1` | Я думаю, що це добре. | The key places a comma before the subordinate connector. The second option omits that comma; the third separates the subject from its predicate or the connector from its clause. | G5, W2, T1, P1, W3, P2 |
| `when-and-where/inline/act-4/2` | Скажи, коли урок. | The key places a comma before the subordinate connector. The second option omits that comma; the third separates the subject from its predicate or the connector from its clause. | G5, W2, T1, P1, W3, P2 |
| `when-and-where/inline/act-4/3` | Вона каже, що магазин близько. | The key places a comma before the subordinate connector. The second option omits that comma; the third separates the subject from its predicate or the connector from its clause. | G5, W2, T1, P1, W3, P2 |
| `checkpoint-communication/inline/act-2/2` | бо | Бо introduces the reason. Якого and котрий cannot introduce the impersonal clause людей багато. | D1, D2, D3, D4, D25, D26, W2, T1, P1, W3, P2 |
| `checkpoint-communication/inline/act-2/3` | а | А coordinates the two subject-predicate clauses; якого and котрого have no grammatical role in the second clause. | D1, D2, D3, D4, D25, D26, W2, T1, P1, W3, P2 |
| `checkpoint-communication/inline/act-2/4` | тому що | Тому що introduces the reason. Якого and котрому have no compatible antecedent or syntactic role in this clause. | D1, D2, D3, D4, D25, D26, W2, T1, P1, W3, P2 |
| `checkpoint-communication/inline/act-3/1` | що | Що introduces the thought; якого and котрому cannot introduce все готово. | D1, D2, D3, D4, D25, D26, W2, T1, P1, W3, P2 |
| `checkpoint-communication/inline/act-3/2` | коли | О третій answers коли. Де asks for a place and що cannot introduce this time question. | D1, D2, D3, D4, D25, D26, W2, T1, P1, W3, P2 |
| `checkpoint-communication/inline/act-3/4` | що | The reply supplies the greeting text, answering що; it gives neither a location for де nor a time for коли. | D1, D2, D3, D4, D25, D26, W2, T1, P1, W3, P2 |
| `checkpoint-communication/inline/act-3/5` | коли | The reply gives a time, answering коли rather than де; що cannot introduce this time question. | D1, D2, D3, D4, D25, D26, W2, T1, P1, W3, P2 |
| `checkpoint-communication/workbook/4/1` | бо | Бо introduces the reason. Якого and котрий cannot introduce людей багато. | D1, D2, D3, D4, D25, D26, W2, T1, P1, W3, P2 |
| `checkpoint-communication/workbook/4/2` | що | Що introduces the thought; якого and котрому cannot introduce все готово. | D1, D2, D3, D4, D25, D26, W2, T1, P1, W3, P2 |
| `checkpoint-communication/workbook/4/3` | а | А coordinates the clauses. Neither якого nor котрого has a role in Тарас ставить стіл. | D1, D2, D3, D4, D25, D26, W2, T1, P1, W3, P2 |
| `checkpoint-communication/workbook/4/4` | коли | The reply gives a time, answering коли. Бо would assert a reason and але a contrast, neither requests the time supplied by the reply. | D1, D2, D3, D4, D25, D26, W2, T1, P1, W3, P2 |
| `yesterday/inline/act-2/0` | Зранку | Зранку is the time adverb. Ранок is a noun and ранковий an adjective; neither modifies прокинулася as a time expression. | D5, D6, D7, D8, D9, W2, T1, P1, W3, P2 |
| `yesterday/inline/act-2/1` | Потім | Nine follows eight, selecting потім. До цього reverses the order; напередодні shifts the event to the previous day. | D5, D6, D7, D8, D9, W2, T1, P1, W3, P2 |
| `yesterday/inline/act-2/2` | Вдень | The one-in-the-afternoon clock expression selects вдень. Вночі and зранку conflict with that time. | D5, D6, D7, D8, D9, W2, T1, P1, W3, P2 |
| `yesterday/inline/act-2/3` | Ввечері | Nine in the evening selects ввечері. Вдень and зранку conflict with that clock expression. | D5, D6, D7, D8, D9, W2, T1, P1, W3, P2 |
| `yesterday/inline/act-2/4` | Нарешті | Нарешті marks reaching rest after the stated delay. Вдень and зранку conflict with the clock expression о другій ночі. | D5, D6, D7, D8, D9, W2, T1, P1, R2W, W3, P2 |
| `yesterday/inline/act-4/1` | Я пішла. Я повернулася. | Анна supplies the named female referent consistent with the activity instruction. Both verbs in the key agree with her; the second alternative has masculine повернувся and the third masculine пішов. | G1, W2, T1, P1, R2W, W3, P2 |
| `my-plans/inline/act-1/4` | вечірка | Вечірка is the nominative subject. Вечірку and вечіркою are oblique forms, not subjects here. | D10, W2, T1, P1, W3, P2 |
| `my-plans/workbook/3/0` | буду вчити | The subject я agrees with буду; будеш and будемо are other person/number forms. The infinitive remains unchanged. | G2, W2, T1, P1, W3, P2 |
| `my-plans/workbook/3/1` | будемо готувати | The subject ми agrees with будемо; буде and буду are other person/number forms. The infinitive remains unchanged. | G2, W2, T1, P1, W3, P2 |
| `my-plans/workbook/3/2` | буде працювати | The subject вона agrees with буде; будуть and будемо are other person/number forms. The infinitive remains unchanged. | G2, W2, T1, P1, W3, P2 |
| `my-story/workbook/2/3` | буду вчити | The subject я agrees with буду; будеш and будемо are other person/number forms. The infinitive remains unchanged. | G2, W2, T1, P1, W3, P2 |
| `a1-finale/inline/act-1/3` | буду подорожувати | The subject я agrees with буду; будеш and будемо are other person/number forms. The infinitive remains unchanged. | G2, W2, T1, P1, W3, P2 |
| `my-plans/inline/act-3/0` | У суботу о третій я буду готувати. | Буду готувати answers the future question. Готую вчора conflicts in time; готував refers to a past event rather than the requested plan. | G1, G2, W2, T1, P1, W3, P2 |
| `my-plans/inline/act-3/1` | Ходімо в кіно! | Two film tickets motivate Ходімо в кіно. Я буду кіно identifies a person as cinema; Кіно буде прибирати assigns cleaning to cinema rather than forming an invitation. | G2, D11, W2, T1, P1, W3, P2 |
| `my-plans/inline/act-3/2` | На жаль, не можу. | The exam and absence explain На жаль, не можу. З задоволенням and Звичайно буду accept an invitation that the continuation rules out. | D12, W2, T1, P1, W3, P2 |
| `my-plans/inline/act-3/3` | Ти будеш вільна у суботу? | The reply supplies future Saturday availability. Була ... учора asks about yesterday, not that Saturday; о вчора misuses the clock-time preposition with an adverb. | G1, G2, D13, W2, T1, P1, W3, P2 |
| `my-story/inline/act-1/0` | Раніше | Раніше fits the previous Toronto period. Завтра and наступного року point after the present Kyiv period, contradicting жив and the contrast. | G1, D14, D15, W2, T1, P1, W3, P2 |
| `my-story/inline/act-1/1` | Зараз | Зараз is a time adverb. Києві requires a preposition as a location; працював cannot modify живу as a time expression. | G1, D14, D15, W2, T1, P1, W3, P2 |
| `my-story/inline/act-1/3` | У дитинстві | У дитинстві fits the recalled school years; завтра and наступного року conflict with the completed earlier period. | G1, D14, D15, W2, T1, P1, W3, P2 |
| `my-story/workbook/2/0` | народилася | Олена selects feminine singular народилася. Народився is masculine singular; народилися is plural. | G1, D14, D15, W2, T1, P1, W3, P2 |
| `my-story/workbook/2/1` | жила | Олена selects feminine singular жила. Жив is masculine singular; жили is plural. | G1, D14, D15, W2, T1, P1, W3, P2 |
| `my-story/workbook/2/2` | працюю | Я selects first-person singular працюю. Працюєш is second-person singular; працюють third-person plural. | G1, D14, D15, W2, T1, P1, W3, P2 |
| `my-story/workbook/3/0` | Зараз я живу в Києві. | The present location question is answered by я живу. Живеш disagrees with я; буду живу combines two finite forms instead of auxiliary plus infinitive. | G1, G2, W2, T1, P1, W3, P2 |
| `my-story/workbook/3/1` | Далі я буду працювати. | Буду працювати answers the future question. Працював describes a past action; працюю учора mismatches the time and does not answer the plan question. | G1, G2, W2, T1, P1, W3, P2 |
| `what-happened/inline/act-3/1` | Я читала. | Named Олена and була establish feminine singular читала. Читав is masculine and читали plural. | G1, W2, T1, P1, W3, P2 |
| `what-happened/inline/act-3/2` | Ми читали. | The two named speakers require plural ми читали. Ми читав and ми читала combine a plural pronoun with singular past verbs. | G1, W2, T1, P1, W3, P2 |
| `what-will-happen/inline/act-3/0` | Я буду читати. | Буду читати answers the question. Буду читаю wrongly combines finite verbs; я будемо mismatches person and number. The grammatical scheduled-present alternative is removed. | G2, W2, T1, P1, W3, P2 |
| `health/inline/act-1/2` | температура | Температура combines with 39 градусів. Праворуч is a direction adverb; квиток cannot have a measurement in degrees. | D16, W2, T1, P1, W3, P2 |
| `health/inline/act-4/0` | У мене болить живіт. | The key answers the doctor’s question with a grammatical pain construction. Я живіт болить wrongly joins я with the third-person predicate; є болить joins incompatible finite predicates. | D17, W2, T1, P1, W3, P2 |
| `health/inline/act-4/1` | Мені потрібен лікар. | Мені потрібен лікар agrees in masculine singular with лікар and marks the experiencer in the dative. Я потрібно лікар has the wrong experiencer and agreement; лікар болить does not answer what is needed. | D18, W2, T1, P1, W3, P2 |
| `health/inline/act-4/2` | Я не розумію. | Я не розумію answers the understanding question. Я не аптека denies being a pharmacy; у мене розумію places a first-person verb without a nominative subject. | D19, W2, T1, P1, W3, P2 |
| `emergencies/inline/act-4/0` | Тут пожежа. | The key has nominative пожежа as subject. Пожежу is accusative; мене is an oblique pronoun and cannot form the location/incident statement. | D20, W2, T1, P1, W3, P2 |
| `emergencies/inline/act-4/1` | Потрібна поліція. | Police help fits the theft situation. A pharmacy does not handle theft and поліція болить uses a pain predicate with the service. | D21, W2, T1, P1, W3, P2 |
| `emergencies/inline/act-4/2` | Подзвоніть за номером 103, будь ласка. | The complete request подзвоніть за номером 103 fits the promise to call. Я номер сто три identifies a person as a number; сто три звати incorrectly uses a name construction. | D22, W2, T1, P1, W3, P2 |
| `emergencies/inline/act-4/3` | Викличте швидку! | Викличте швидку is the request completed by зараз викличу. Швидка звати has an incompatible nominative/name construction; паспорт швидку contains two unrelated nouns without a predicate. | D23, W2, T1, P1, W3, P2 |
| `a1-finale/inline/act-1/0` | снідав | Адам selects masculine singular снідав. Снідала is feminine and снідали plural. | G1, W2, T1, P1, W3, P2 |
| `a1-finale/inline/act-1/1` | гуляю | Я selects first-person singular гуляю. Гуляєш is second-person singular; гуляють third-person plural. | G1, W2, T1, P1, W3, P2 |
| `a1-finale/inline/act-1/2` | купив | Адам selects masculine singular купив. Купила is feminine; купили plural. | G1, W2, T1, P1, W3, P2 |
| `a1-finale/inline/act-1/4` | ходили | Ми selects plural ходили. Ходив and ходила are singular. | G1, W2, T1, P1, W3, P2 |
| `a1-finale/inline/act-1/5` | замовляє | Олена selects third-person singular замовляє. Замовляю is first-person and замовляєш second-person. | G1, W2, T1, P1, W3, P2 |
| `a1-finale/inline/act-1/6` | гуляли | Ми selects plural гуляли. Гуляв and гуляла are singular. | G1, W2, T1, P1, W3, P2 |
| `a1-finale/workbook/3/1` | снідав | Адам selects masculine singular снідав. Кафе is a place noun, not a predicate here; буду requires an infinitive absent from the line. | G1, W2, T1, P1, W3, P2 |
| `a1-finale/workbook/0/0` | Скільки коштує квиток? | The answer gives a price, matching скільки коштує. Де asks for location; дайте is a purchase request rather than a price question. | D17, D24, W2, T1, P1, W3, P2 |
| `a1-finale/workbook/0/1` | Ходімо в кафе! | Ходімо в кафе makes the invitation accepted by добре. Я був у кафе reports a past visit; де кафе asks for location. | D17, D24, W2, T1, P1, W3, P2 |
| `a1-finale/workbook/0/2` | У мене болить голова. | Голова is the nominative subject of болить. Головою is instrumental and голові dative; neither can be its subject here. | D17, W2, T1, P1, W3, P2 |
| `what-will-happen/inline/act-3/3` | Що ти будеш робити завтра? | The reply supplies a plan for tomorrow, answering Що ти будеш робити завтра? The second question робиш учора mismatches its time expression; the third робив зараз asks about a recent action rather than the stated tomorrow plan. | G1, G2, W2, R2W, W3, P2 |
| `linking-ideas/inline/act-3/0` | бо | Бо introduces the reason clause. Якого and котрому have no compatible antecedent or syntactic role in this clause. | D25, W2, R2W, W3, P2 |
| `linking-ideas/inline/act-3/1` | тому що | Тому що introduces the reason clause. Якого and котрому have no compatible antecedent or syntactic role in this clause. | D25, W2, R2W, W3, P2 |
| `linking-ideas/inline/act-3/2` | бо | Бо introduces the reason clause. Якого and котрому have no compatible antecedent or syntactic role in this clause. | D25, W2, R2W, W3, P2 |
| `linking-ideas/inline/act-3/3` | тому що | Тому що introduces the reason clause. Якого and котрому have no compatible antecedent or syntactic role in this clause. | D25, W2, R2W, W3, P2 |
| `linking-ideas/inline/act-3/4` | бо | Бо introduces the reason clause. Якого and котрому have no compatible antecedent or syntactic role in this clause. | D25, W2, R2W, W3, P2 |
| `linking-ideas/inline/act-3/5` | тому що | Тому що introduces the reason clause. Якого and котрому have no compatible antecedent or syntactic role in this clause. | D25, W2, R2W, W3, P2 |

## Verification

- Source and published MDX parity: all 86 changed item objects pass through the existing parser and canonical serializer. All unrelated object values and surrounding page content are retained. The integrity manifest changes exactly 24 hashes for 12 source files and 12 pages. The unchanged holidays module is included in the scan.
- Chromium using the actual QuizQuestion and FillInQuestion components and tracked MDX payloads accepts all 86 keys and rejects all 172 wrong choices. Feedback stays hidden before each of 258 answers; zero browser errors. Both dependency lockfiles match the installed runtime used read-only for the bundle. This is component behavior proof on the tracked artifact, not a deployment claim.
- Structural scan: 55/55 files, no structural findings. Integrity canary: all 3,899 files match.
- The initial affected parser, renderer, generator, manifest and source DB write-guard suite passes 463 tests. The bounded metadata/parser/manifest recheck after the review corrections passes 250 tests. Ruff and diff whitespace checks pass. No test case is added.
- Exact-head independent Opus 5.5 and Gemini Ukrainian review, recorded verdicts, same-head admission CI and successful merge queue landing are required separately. This author report is not approval.

## Review correction ledger

Round 1: Opus 5.5 requested changes, score 6/10; Gemini approved, score 10/10. Both independently solved all 79 initial items and matched every key without a competing answer. The Opus rejection remains binding until approvals at a new head.

- F1: neutral headings and instructions remove the key-list disclosure. The same class check found and repaired six additional legacy items. The blind inventory now includes visible title and instruction fields.
- F2: the added feedback now quotes the clock expression о другій ночі, confirmed by R2W. No instrumental другою is taught.
- F3: the missed tomorrow description becomes a Ukrainian question-and-reply item, with its key and every distractor recorded above.
- F4: Анна now matches the activity speaker.
- F5, author finding: a broad instruction replacement had changed an unrelated Translate label and missed the intended Quiz label. Component-specific instruction parity now verifies the repaired activities; the Translate label is restored. Generic story/response labels also match their actual options.

Exact-head delta reviews must verify these corrections and the seven additional blind choices before landing. The remaining optional euphony and unchanged vocabulary-staging preferences belong to the curriculum coordinator under #8893.

## Residual boundary

The other module batches and broader correctness sweep remain with the curriculum coordinator under #8893. This repair does not certify unchanged lesson prose, other pre-existing answer defects, or deployed-site behavior. Modules 1–42, their branches and their source/page hashes are outside this change. No site deployment is included.
