# A1 activity correctness, manifest modules 43-55

The A1 activities could reject grammatical Ukrainian, accept incorrect truth keys, or require an arbitrary match or word order. This slice repairs manifest modules 43-55 through the existing V7 parser and serializer.

The denominator is **13 modules, 130 activities and 800 task/card units**, including inline and workbook sections. The 800 units are 550 original item/order rows, 112 matching pairs and 138 group members. They occupy 702 YAML rows because a group contains several cards. All 800 remain after repair.

There are **180 repaired source rows**. Two true/false keys are corrected. Sixty-nine single-sequence word-order tasks become bounded sentence choices because the existing ordering component rejects valid Ukrainian inversion. Other repairs cover duplicate matching targets, interchangeable replies, false error labels, incomplete correction spans and insufficient chronology. The existing teaching sentences and language points are retained wherever sound. Normal A1 English task instructions remain.

- **AC-S43-01**: the complete source census and item verdicts are in the item ledger. No activity type or workbook section is excluded.
- **AC-S43-02**: every finding below cites Sources receipts. VESUM checks forms and morphology; ULIF records and modern dictionaries check meaning; stress-oracle and orthoepic replies preserve their provenance and limits. Text screening does not itself prove answer uniqueness.
- **AC-S43-03**: all 180 repaired source rows match canonical V7 payloads. Unrepaired payload objects are preserved. Chromium checks all 800 units: 712 graded keys accepted, 1,048 wrong responses rejected, and 88 guided correction reveals verified. Feedback is hidden before 1,179 choice attempts. No browser error occurs. Four baseline failures were reproduced using the original tracked payloads.
- **AC-S43-04**: the 224 affected parser, renderer, manifest and source-protection tests pass. The full 55-file structural scan is clean, all 3,899 integrity hashes match, and Ruff and whitespace checks pass. Independent exact-head Sources-backed approvals from Gemini through AGY and Opus 5.5, followed by same-head PR CI and merge-group CI, are required before landing. Verdicts and CI receipts belong in the PR conversation and checks.

Review profile: Ukrainian. Catalog risk: medium. Budget: default, three rounds. The item ledger is the author's evidence, not independent approval. The key-free blind packet shuffles options and matching columns and withholds truth, sorting, correction and ordering keys for independent derivation.

The 88 existing guided correction tasks reveal a model repair after the learner identifies an error and explicitly requests the correction. They do not grade arbitrary typed repairs. Their broader production-task design remains a curriculum-coordinator follow-up. The stress oracle leaves його, грошима and телефона pending as direct lookups; the report preserves the ULIF and orthoepic escalation and does not claim an unsupported exact-form stress ruling. No stress mark or stress-selection key is introduced.

This PR covers activity correctness. Lesson prose, plans, vocabulary cards, audio and modules 1-42 remain under the wider issue. Site deployment is outside this PR. The curriculum coordinator owns those residuals and the previously recorded empty dropdowns outside this slice. No follow-up task or PR is opened here.

Size justification: the source repairs, 13 corresponding generated pages, 26 integrity hashes and exhaustive item/source evidence deliver one ordered slice. The machine evidence is intentionally larger than the prose report because it records the full 800-unit denominator.

Refs #8893

Authored by GPT-6.1 Sol through Codex.

| Manifest | Module | Activities | Task/card units | Source rows | Repaired rows |
| --- | --- | ---: | ---: | ---: | ---: |
| 43 | `please-do-this` | 10 | 77 | 67 | 17 |
| 44 | `linking-ideas` | 10 | 78 | 66 | 18 |
| 45 | `when-and-where` | 10 | 64 | 64 | 8 |
| 46 | `holidays` | 10 | 60 | 52 | 7 |
| 47 | `checkpoint-communication` | 10 | 72 | 62 | 7 |
| 48 | `what-happened` | 10 | 63 | 55 | 21 |
| 49 | `yesterday` | 10 | 62 | 50 | 15 |
| 50 | `what-will-happen` | 10 | 53 | 50 | 12 |
| 51 | `my-plans` | 10 | 61 | 52 | 12 |
| 52 | `my-story` | 10 | 51 | 42 | 18 |
| 53 | `health` | 10 | 51 | 42 | 13 |
| 54 | `emergencies` | 10 | 45 | 45 | 7 |
| 55 | `a1-finale` | 10 | 63 | 55 | 25 |


The source snapshot is `9cef950900e3c118c04769da24bd978d881e593a`. The canonical order is `levels.a1-v1.modules` in `curriculum/l2-uk-en/curriculum.yaml`; this uses the approved arc-order fallback because no authorized usage ranking was supplied. The prior merged slices #11930, #11946 and #12000 and the existing modules 43-55 work #11931 and #11957 were read before this pass.

The deterministic checks cover key membership, one correct choice, conflicting truth aliases, duplicate options, matching-column collisions, group ownership, ordering permutations, unjumble token multisets, marked correction spans and slash keys. The linguistic verdicts are the author's contextual inferences from the cited Sources results. Independent reviewers must solve the blind packet before consulting the keys and check every activity type.

V7 regeneration uses `ActivityParser` and `yaml_activities_to_jsx`, updating changed item objects, necessary labels, imports and integrity hashes. Unrepaired payload objects and surrounding lesson content are retained. This is deterministic regeneration through the established slice-repair path, not a paid rewrite or a complete module build.

Every distinct Ukrainian token in the original activities was submitted to Sources in the M43-M55 module batches. S1-S6 replace the five timed-out stress calls with smaller requests; the failures remain visible and are not evidence. New forms and names are checked by POSTWORDS and POSTNAMES. POSTSTRESS1-2 and CLOCKSTRESS cover new polysyllabic forms. FINALTEXT screens all 180 repaired rows. D1-D15 query 508 VESUM lemmas through official ULIF records; POSTMEANINGS covers seven additional analyses. Dictionary misses and irrelevant homonym analyses are not treated as negative evidence about a word. Monosyllables have no competing written stress position.

The capitalization-sensitive name recheck finds 27 of 27 original name forms and all six new case forms. Invalid-looking spellings in deliberate error examples, including поставь, доповіди, читаємте, читалимо, читалить and принісв, are not taught vocabulary. Suffix fragments such as -ло and -ли are grammar labels. U21 verifies the positive imperative paradigm; U13 records the accusative-variant analysis for паспорта.

U1 establishes relatively free Ukrainian word order. U2 and U10 distinguish an optional copula from an error. U11 establishes narrative present and scheduled-future present. U4, U24 and U26 support the holiday and scheduling distinctions. U25 attests infinitive commands. U36 attests the Christmas greeting. U7 and U8 cover punctuation and euphony. U29-U35 preserve the direct-oracle gaps and the ULIF/orthoepic escalation for його, грошима and телефона; those unmarked forms are not stress-selection questions and no unsupported stress choice is asserted.

Stress ambiguity is retained rather than collapsed to one reading. The oracle's pending exact-form status is not silently replaced with a lemma-level assertion. U33 and U35 provide labelled orthoepic witness data; U34 supplies the accented телефон head and its listed inflections, without claiming that a missing exact-form row is present.

The official emergency-number list was checked against the National Police report, https://npu.gov.ua/static-objects/npu/sites/1/uploaded-files/zvit-pro-funkcionuvannia-sistemi-ekstrennoyi-dopomogi-naselenniu-za-jedinim-telefonnim-nomerom-112.pdf . Holiday dates were checked against the government calendar, https://zakon.rada.gov.ua/laws/main/days , and the Government Contact Centre, https://ukc.gov.ua/knowdledge/svyatkovi-ta-nerobochi-dni/ . No date or emergency number changes.

All receipts bind the retained normalized result object with SHA-256, not the transport envelope. The evidence index names each receipt's file, line and digest. Its smaller companion files preserve every full receipt and satisfy the repository's per-file limit. Dictionary excerpts are bounded and attributed. The private pedagogy search hit is excluded from the committed evidence. No private source text is copied into an activity or this report.

Verification commands use the prescribed project interpreter. `correctness-modules-43-55-check.py` rechecks the full census, receipt hashes, exact source values, repaired canonical payloads, preserved unrepaired payloads and source/page hashes. `scan_activity_errors.py --track a1-v1` reports 55 files with no structural errors. `curriculum_manifest_canary.py --check --json` validates all 3,899 files. The six existing affected pytest files pass 224 tests. No test is added, weakened or skipped, and no timeout is raised.

Item locators use manifest number, `I` for inline or `W` for workbook, then zero-based activity and row indices. Sources IDs name exact records in the evidence JSONL. `POST` means the final changed-form, name, stress and text receipts. The item ledger also maps every row to its relevant ULIF meaning batches.

| Finding | Item | Confirmed defect and repair | Sources |
| --- | --- | --- | --- |
| F001 | `43/I3/0` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. Both alternatives break the fixed request phrase будь ласка. | M43, U1, U10, POST |
| F002 | `43/I3/1` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. Both alternatives break the fixed request phrase будь ласка. | M43, U1, U10, POST |
| F003 | `43/I3/2` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. Both alternatives break the fixed request phrase будь ласка. | M43, U1, U10, POST |
| F004 | `43/I3/3` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. Both alternatives break the fixed request phrase будь ласка. | M43, U1, U10, POST |
| F005 | `43/I3/4` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. Both alternatives break the fixed request phrase будь ласка. | M43, U1, U10, POST |
| F006 | `43/I3/5` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. Both alternatives break the fixed request phrase будь ласка. | M43, U1, U10, POST |
| F007 | `43/W0/3` | Repair the inherited euphony noted on the parent issue. | M43, U8, POST |
| F008 | `43/W3/0` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. Both alternatives break the fixed request phrase будь ласка. | M43, U1, U10, POST |
| F009 | `43/W3/1` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. Both alternatives break the fixed request phrase будь ласка. | M43, U1, U10, POST |
| F010 | `43/W3/2` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The construction takes речення. The case forms реченню and реченням cannot replace it here. | M43, U1, U10, POST |
| F011 | `43/W3/3` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. Both alternatives break the fixed request phrase будь ласка. | M43, U1, U10, POST |
| F012 | `43/W3/4` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. Both alternatives break the fixed request phrase будь ласка. | M43, U1, U10, POST |
| F013 | `43/W3/5` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. Both alternatives break the fixed request phrase будь ласка. | M43, U1, U10, POST |
| F014 | `43/W3/6` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The construction takes текст. The case forms текстом and тексту cannot replace it here. | M43, U1, U10, POST |
| F015 | `43/W3/7` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. Both alternatives break the fixed request phrase будь ласка. | M43, U1, U10, POST |
| F016 | `43/W4/0` | An infinitive may express a command; the old source was not necessarily an error. The new error has a conflicting address and imperative number. | M43, U18, U25, POST |
| F017 | `43/W5/0` | The original did not choose familiar or polite address and treated an infinitive command as necessarily wrong. | M43, U18, U25, POST |
| F018 | `44/I0/3` | The original coordination alternatives can also connect these clauses. The replacements cannot fill this syntactic role. | M44, U7, POST |
| F019 | `44/I3/0` | Bare та can also express contrast; the old recognition category overlaps the other meaning categories. Complete sentences distinguish the connector meanings. | M44, U7, POST |
| F020 | `44/I3/1` | Bare та can also express contrast; the old recognition category overlaps the other meaning categories. Complete sentences distinguish the connector meanings. | M44, U7, POST |
| F021 | `44/I3/2` | Bare та can also express contrast; the old recognition category overlaps the other meaning categories. Complete sentences distinguish the connector meanings. | M44, U7, POST |
| F022 | `44/I3/3` | Bare та can also express contrast; the old recognition category overlaps the other meaning categories. Complete sentences distinguish the connector meanings. | M44, U7, POST |
| F023 | `44/I3/4` | Bare та can also express contrast; the old recognition category overlaps the other meaning categories. Complete sentences distinguish the connector meanings. | M44, U7, POST |
| F024 | `44/W0/0` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The stated subject agrees with читаю, not with the person/number forms читаєш or читають. | M44, U1, U10, POST |
| F025 | `44/W0/1` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The stated subject agrees with хочу, not with the person/number forms хочеш or хочуть. | M44, U1, U10, POST |
| F026 | `44/W0/2` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The subject requires гарні. гарна and гарний have a different gender or number. | M44, U1, U10, POST |
| F027 | `44/W0/3` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The subject requires тепле. тепла and теплий have a different gender or number. | M44, U1, U10, POST |
| F028 | `44/W0/4` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. This construction requires nominative лікар. лікарю and лікарем are different case forms. | M44, U1, U10, POST |
| F029 | `44/W0/5` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. Singular дощ agrees with third-person singular йде, not plural йдуть or second-person йдеш. | M44, U1, U10, POST |
| F030 | `44/W1/2` | The original coordination alternatives can also connect these clauses. The replacements cannot fill this syntactic role. | M44, U7, POST |
| F031 | `44/W1/4` | The two alternatives can still name the same pair of choices. Replacements cannot coordinate the nouns. | M44, U7, POST |
| F032 | `44/W1/5` | The original coordination alternatives can also connect these clauses. The replacements cannot fill this syntactic role. | M44, U7, POST |
| F033 | `44/W3/0` | Expressed є is not intrinsically an error. The replacement tests a genuine subject-agreement error in the same causal frame. | M44, U2, U10, POST |
| F034 | `44/W5/0` | Expressed є is grammatical; replace the false error label with genuine agreement failure. | M44, U2, U10, POST |
| F035 | `44/W5/4` | The old replacement joined щоб but left the required comma missing. | M44, U7, POST |
| F036 | `45/I0/3` | A different clause relation can be read with the original alternatives; the replacements cannot introduce this content clause. | M45, U7, POST |
| F037 | `45/W3/0` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The stated subject agrees with знаю, not with the person/number forms знаєш or знають. | M45, U1, U10, POST |
| F038 | `45/W3/1` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The stated subject agrees with знаю, not with the person/number forms знаєш or знають. | M45, U1, U10, POST |
| F039 | `45/W3/2` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. Коли introduces the time question. Якого and котрому have no compatible noun or syntactic role here. | M45, U1, U10, POST |
| F040 | `45/W3/3` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The stated subject agrees with каже, not with the person/number forms кажеш or кажуть. | M45, U1, U10, POST |
| F041 | `45/W3/4` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The stated subject agrees with знаєш, not with the person/number forms знаю or знає. | M45, U1, U10, POST |
| F042 | `45/W3/5` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The stated subject agrees with думаю, not with the person/number forms думаєш or думають. | M45, U1, U10, POST |
| F043 | `45/W5/5` | Both де and коли could repair the original unqualified meeting question. The reply now fixes the requested detail. | M45, U7, POST |
| F044 | `46/I2/0` | Remove feedback about a prior edit and explain the actual agreement. | M46, POST |
| F045 | `46/I2/2` | Remove feedback about a prior edit and explain the actual agreement. | M46, POST |
| F046 | `46/W1/0` | An unqualified gift belongs to several holiday groups. Новорічний specifies its holiday. | M46, U13, POST |
| F047 | `46/W5/1` | Святкувати на Різдво can mean celebrate at Christmas. The replacement tests a real person-agreement error. | M46, U4, U24, POST |
| F048 | `46/W5/5` | Щасливого Різдва is a valid greeting, not an error. Replace it with a genuine case error. | M46, U10, U27, U36, POST |
| F049 | `46/W5/6` | The slash string was not one usable replacement; test the baking object with a single attested noun. | M46, POST |
| F050 | `46/W5/8` | Пасха is an attested church-register holiday name. Replace the false error label with a real agreement error. | M46, U12, POST |
| F051 | `47/W0/0` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. Both alternatives break the fixed request phrase будь ласка. | M47, U1, U10, POST |
| F052 | `47/W0/1` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The stated subject agrees with знаю, not with the person/number forms знаєш or знають. | M47, U1, U10, POST |
| F053 | `47/W0/2` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The stated subject agrees with хочу, not with the person/number forms хочеш or хочуть. | M47, U1, U10, POST |
| F054 | `47/W0/3` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The construction takes стіл. The case forms столом and столу cannot replace it here. | M47, U1, U10, POST |
| F055 | `47/W0/4` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The stated subject agrees with пишемо, not with the person/number forms пише or пишеш. | M47, U1, U10, POST |
| F056 | `47/W0/5` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The construction takes Новим роком. The case forms Новий рік and Новому році cannot replace it here. | M47, U1, U10, POST |
| F057 | `47/W5/7` | Святкувати на Різдво can mean celebrate at Christmas. The replacement tests a real person-agreement error. | M47, U4, U24, M46, POST |
| F058 | `48/I0/0` | Identical ending chips were keyed to different indices. Unique subject-and-infinitive pairs now have distinct past-form matches. | M48, POST |
| F059 | `48/I0/1` | Identical ending chips were keyed to different indices. Unique subject-and-infinitive pairs now have distinct past-form matches. | M48, POST |
| F060 | `48/I0/2` | Identical ending chips were keyed to different indices. Unique subject-and-infinitive pairs now have distinct past-form matches. | M48, POST |
| F061 | `48/I0/3` | Identical ending chips were keyed to different indices. Unique subject-and-infinitive pairs now have distinct past-form matches. | M48, POST |
| F062 | `48/I0/4` | Identical ending chips were keyed to different indices. Unique subject-and-infinitive pairs now have distinct past-form matches. | M48, POST |
| F063 | `48/I0/5` | Identical ending chips were keyed to different indices. Unique subject-and-infinitive pairs now have distinct past-form matches. | M48, POST |
| F064 | `48/I0/6` | Identical ending chips were keyed to different indices. Unique subject-and-infinitive pairs now have distinct past-form matches. | M48, POST |
| F065 | `48/I0/7` | Identical ending chips were keyed to different indices. Unique subject-and-infinitive pairs now have distinct past-form matches. | M48, POST |
| F066 | `48/W1/0` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The stated subject requires читав; читала and читали have a different past-tense gender or number. | M48, U1, U10, POST |
| F067 | `48/W1/1` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The stated subject requires готувала; готував and готували have a different past-tense gender or number. | M48, U1, U10, POST |
| F068 | `48/W1/2` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The stated subject requires гуляли; гуляв and гуляла have a different past-tense gender or number. | M48, U1, U10, POST |
| F069 | `48/W1/3` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The stated subject requires працювали; працював and працювала have a different past-tense gender or number. | M48, U1, U10, POST |
| F070 | `48/W1/4` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The key has matching subject and verb forms. я робили and ми робив combine a singular subject with a plural verb or a plural subject with a singular verb. | M48, U1, U10, POST |
| F071 | `48/W1/5` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The key has matching subject and verb forms. я робили and ми робила combine a singular subject with a plural verb or a plural subject with a singular verb. | M48, U1, U10, POST |
| F072 | `48/W2/0` | The original instruction did not determine the order of the three singular genders. A subject-to-form matching task tests the same agreement without an arbitrary sequence. | M48, POST |
| F073 | `48/W2/1` | The original instruction did not determine the order of the three singular genders. A subject-to-form matching task tests the same agreement without an arbitrary sequence. | M48, POST |
| F074 | `48/W2/2` | The original instruction did not determine the order of the three singular genders. A subject-to-form matching task tests the same agreement without an arbitrary sequence. | M48, POST |
| F075 | `48/W2/3` | The original instruction did not determine the order of the three singular genders. A subject-to-form matching task tests the same agreement without an arbitrary sequence. | M48, POST |
| F076 | `48/W3/5` | The correction must replace only the marked verb, without duplicating the subject. | M48, POST |
| F077 | `48/W3/7` | The marked slash span did not occur in the two source sentences. Keep one complete, usable irregular-past correction. | M48, POST |
| F078 | `48/W4/3` | A question addressed to Ivan can also use polite ви. Replace that defensible translation with a different subject. | M48, POST |
| F079 | `49/I0/0` | Morning/night labels and routine assumptions did not specify every event order. The Ukrainian clock times determine one chronology. | M49, POST |
| F080 | `49/I0/1` | Morning/night labels and routine assumptions did not specify every event order. The Ukrainian clock times determine one chronology. | M49, POST |
| F081 | `49/I0/2` | Morning/night labels and routine assumptions did not specify every event order. The Ukrainian clock times determine one chronology. | M49, POST |
| F082 | `49/I0/3` | Morning/night labels and routine assumptions did not specify every event order. The Ukrainian clock times determine one chronology. | M49, POST |
| F083 | `49/I0/4` | Morning/night labels and routine assumptions did not specify every event order. The Ukrainian clock times determine one chronology. | M49, POST |
| F084 | `49/I0/5` | Morning/night labels and routine assumptions did not specify every event order. The Ukrainian clock times determine one chronology. | M49, POST |
| F085 | `49/W1/5` | The original explanation treated a time marker as an absolute tense rule; the actual defect is person agreement. | M49, U11, POST |
| F086 | `49/W2/0` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The key has matching subject and verb forms. я прокинулися and ми прокинулася combine a singular subject with a plural verb or a plural subject with a singular verb. | M49, U1, U10, POST |
| F087 | `49/W2/1` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The key has matching subject and verb forms. я поснідали and ми поснідала combine a singular subject with a plural verb or a plural subject with a singular verb. | M49, U1, U10, POST |
| F088 | `49/W2/2` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The key has matching subject and verb forms. я обідали and ми обідала combine a singular subject with a plural verb or a plural subject with a singular verb. | M49, U1, U10, POST |
| F089 | `49/W2/3` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The key has matching subject and verb forms. я купили and ми купила combine a singular subject with a plural verb or a plural subject with a singular verb. | M49, U1, U10, POST |
| F090 | `49/W2/4` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The key has matching subject and verb forms. я лягли and ми лягла combine a singular subject with a plural verb or a plural subject with a singular verb. | M49, U1, U10, POST |
| F091 | `49/W3/0` | Narrative present can recount a past event. The new alternative changes the English subject and cannot be the translation. | M49, U11, POST |
| F092 | `49/W3/1` | Narrative present can recount a past event. The new alternative changes the English subject and cannot be the translation. | M49, U11, POST |
| F093 | `49/W3/3` | Narrative present can recount a past event. The new alternative changes the English subject and cannot be the translation. | M49, U11, POST |
| F094 | `50/W0/1` | Complete the inherited question noted on the parent issue. | M50, POST |
| F095 | `50/W1/0` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The subject agrees with буду; будеш and будемо belong to different persons or numbers. | M50, U1, U10, POST |
| F096 | `50/W1/1` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The subject agrees with будеш; буду and будуть belong to different persons or numbers. | M50, U1, U10, POST |
| F097 | `50/W1/2` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The subject agrees with буде; буду and будуть belong to different persons or numbers. | M50, U1, U10, POST |
| F098 | `50/W1/3` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The subject agrees with будемо; буде and буду belong to different persons or numbers. | M50, U1, U10, POST |
| F099 | `50/W1/4` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The subject agrees with будуть; буде and буду belong to different persons or numbers. | M50, U1, U10, POST |
| F100 | `50/W2/0` | Without a current weekday, tomorrow could overlap next week. Monday morning and today’s evening make the four intervals distinct. | M50, POST |
| F101 | `50/W2/1` | Without a current weekday, tomorrow could overlap next week. Monday morning and today’s evening make the four intervals distinct. | M50, POST |
| F102 | `50/W3/1` | Complete the inherited question noted on the parent issue. | M50, POST |
| F103 | `50/W4/2` | Present forms can express scheduled future actions. The new alternative has a genuine person/number disagreement. | M50, U11, POST |
| F104 | `50/W4/3` | Present forms can express scheduled future actions. The new alternative has a genuine number disagreement. | M50, U11, POST |
| F105 | `50/W5/1` | Complete the inherited question noted on the parent issue. | M50, POST |
| F106 | `51/I1/0` | The old acceptance/refusal replies fit several invitations. Distinct English meanings retain invitation comprehension with unique matches. | M51, POST |
| F107 | `51/I1/1` | The old acceptance/refusal replies fit several invitations. Distinct English meanings retain invitation comprehension with unique matches. | M51, POST |
| F108 | `51/I1/2` | The old acceptance/refusal replies fit several invitations. Distinct English meanings retain invitation comprehension with unique matches. | M51, POST |
| F109 | `51/I1/3` | The old acceptance/refusal replies fit several invitations. Distinct English meanings retain invitation comprehension with unique matches. | M51, POST |
| F110 | `51/I1/4` | The old acceptance/refusal replies fit several invitations. Distinct English meanings retain invitation comprehension with unique matches. | M51, POST |
| F111 | `51/W1/0` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The subject agrees with буду; будеш and будемо belong to different persons or numbers. | M51, U1, U10, POST |
| F112 | `51/W1/1` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The subject agrees with будемо; буде and буду belong to different persons or numbers. | M51, U1, U10, POST |
| F113 | `51/W1/2` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The subject agrees with будеш; буду and будуть belong to different persons or numbers. | M51, U1, U10, POST |
| F114 | `51/W1/3` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The construction takes п'ятій. The case forms п'ятого and п'ятим cannot replace it here. | M51, U1, U10, POST |
| F115 | `51/W1/4` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The fixed introductory phrase is На жаль. Жалю and жалем cannot replace жаль in it. | M51, U1, U10, U28, POST |
| F116 | `51/W3/3` | Звичайно, не можу is a defensible reply with the stated work conflict. The new alternatives cannot introduce this refusal. | M51, POST |
| F117 | `51/W5/6` | На понеділок can name a scheduled date; it is not intrinsically wrong. The replacement tests the weekday case. | M51, U26, POST |
| F118 | `52/I2/0` | Duplicate past/present/future chips were keyed to different indices. The distinct meanings still require recognizing the tense. | M52, POST |
| F119 | `52/I2/1` | Duplicate past/present/future chips were keyed to different indices. The distinct meanings still require recognizing the tense. | M52, POST |
| F120 | `52/I2/2` | Duplicate past/present/future chips were keyed to different indices. The distinct meanings still require recognizing the tense. | M52, POST |
| F121 | `52/I2/3` | Duplicate past/present/future chips were keyed to different indices. The distinct meanings still require recognizing the tense. | M52, POST |
| F122 | `52/I2/4` | Duplicate past/present/future chips were keyed to different indices. The distinct meanings still require recognizing the tense. | M52, POST |
| F123 | `52/I2/5` | Duplicate past/present/future chips were keyed to different indices. The distinct meanings still require recognizing the tense. | M52, POST |
| F124 | `52/I3/1` | Зараз has several time senses and далі also occurs in past narratives. Full finite phrases distinguish the intended verb forms. | M52, U5, U6, POST |
| F125 | `52/I3/2` | Зараз has several time senses and далі also occurs in past narratives. Full finite phrases distinguish the intended verb forms. | M52, U5, U6, POST |
| F126 | `52/W0/4` | An expressed copula and possessive name statement are grammatical. Test an actual name-case error instead. | M52, U2, U10, U22, POST |
| F127 | `52/W1/0` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The key has matching subject and verb forms. я жили and ми жив combine a singular subject with a plural verb or a plural subject with a singular verb. | M52, U1, U10, POST |
| F128 | `52/W1/1` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The stated subject agrees with живу, not with the person/number forms живеш or живуть. | M52, U1, U10, POST |
| F129 | `52/W1/2` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The subject agrees with буду; будеш and будемо belong to different persons or numbers. | M52, U1, U10, POST |
| F130 | `52/W1/3` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. This construction requires nominative Софія. Софію and Софії are different case forms. | M52, U1, U10, POST |
| F131 | `52/W3/2` | Моє ім’я є Данило is a grammatical alternative, even if less usual. The new distractor has the wrong name case. | M52, U2, U10, U22, POST |
| F132 | `52/W5/0` | A narrative present is possible, and the old key was a slash string. Test a single genuine past-gender disagreement. | M52, U11, POST |
| F133 | `52/W5/1` | Зараз can mean just now and coexist with past tense. Test person agreement instead. | M52, U6, POST |
| F134 | `52/W5/2` | Далі can continue a past narrative. Replace that valid sentence with a genuine compound-future error. | M52, U5, U10, POST |
| F135 | `52/W5/4` | Replace a valid copular name statement with a genuine case error. | M52, U2, U10, U22, POST |
| F136 | `53/I0/1` | Needing a cough can be a defensible special situation. A dative noun cannot be the nominative subject of потрібен. | M53, U23, POST |
| F137 | `53/W0/1` | Моя голова болить is grammatical Ukrainian; the old false key rejected it. | M53, U23, POST |
| F138 | `53/W0/3` | An expressed present copula is grammatical; the old false key rejected it. | M53, U2, U10, POST |
| F139 | `53/W1/0` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. This construction requires nominative голова. головою and голові are different case forms. | M53, U1, U10, POST |
| F140 | `53/W1/1` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. This construction requires nominative лікар. лікарю and лікарем are different case forms. | M53, U1, U10, POST |
| F141 | `53/W1/2` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The stated subject agrees with розумію, not with the person/number forms розумієш or розуміють. | M53, U1, U10, POST |
| F142 | `53/W1/3` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. Both alternatives break the fixed request phrase будь ласка. | M53, U1, U10, POST |
| F143 | `53/W2/1` | Де тут болить? and Де тут нога? are both possible health questions. Accusative and instrumental nouns cannot be the missing location subject. | M53, POST |
| F144 | `53/W3/0` | Replace a valid possessive pain statement with a genuine noun-case error. | M53, U23, POST |
| F145 | `53/W3/2` | Є is legitimate in an existential symptom statement. Replace the false error label with a genuine noun-case error. | M53, U10, POST |
| F146 | `53/W5/0` | The possessive pain statement is valid. Test subject-verb agreement instead. | M53, U23, POST |
| F147 | `53/W5/2` | The copula is legitimate. Test the predicate adjective case instead. | M53, U2, U10, POST |
| F148 | `53/W5/4` | Є is legitimate in this symptom statement. Test the noun case instead. | M53, U10, POST |
| F149 | `54/W1/0` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The construction takes аварія. The case forms аварію and аварією cannot replace it here. | M54, U1, U10, POST |
| F150 | `54/W1/1` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The construction takes вулиці. The case forms вулиця and вулицею cannot replace it here. | M54, U1, U10, POST |
| F151 | `54/W1/2` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. This construction requires nominative Анна. Анну and Анні are different case forms. | M54, U1, U10, POST |
| F152 | `54/W1/3` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The construction takes номером. The case forms номеру and номер cannot replace it here. | M54, U1, U10, POST |
| F153 | `54/W5/1` | The replacement repeated a street name outside the marked span. | M54, POST |
| F154 | `54/W5/3` | VESUM attests паспорта as an accusative variant, and the old correction duplicated Я. Use a genuine instrumental error and one replacement span. | M54, U13, POST |
| F155 | `54/W5/4` | The replacement repeated 112 outside the marked span. | M54, POST |
| F156 | `55/I1/0` | The original events did not determine one chronology. Explicit Ukrainian times now determine the order without an answer translation. | M55, POST |
| F157 | `55/I1/1` | The original events did not determine one chronology. Explicit Ukrainian times now determine the order without an answer translation. | M55, POST |
| F158 | `55/I1/2` | The original events did not determine one chronology. Explicit Ukrainian times now determine the order without an answer translation. | M55, POST |
| F159 | `55/I1/3` | The original events did not determine one chronology. Explicit Ukrainian times now determine the order without an answer translation. | M55, POST |
| F160 | `55/I1/4` | The original events did not determine one chronology. Explicit Ukrainian times now determine the order without an answer translation. | M55, POST |
| F161 | `55/I1/5` | The original events did not determine one chronology. Explicit Ukrainian times now determine the order without an answer translation. | M55, POST |
| F162 | `55/I1/6` | The original events did not determine one chronology. Explicit Ukrainian times now determine the order without an answer translation. | M55, POST |
| F163 | `55/I1/7` | The original events did not determine one chronology. Explicit Ukrainian times now determine the order without an answer translation. | M55, POST |
| F164 | `55/I2/5` | Generic help and emergency-help matches overlapped. The task-specific request now differs from calling an ambulance. | M55, POST |
| F165 | `55/I2/6` | Distinguish the medical emergency from ordinary task assistance. | M55, POST |
| F166 | `55/I2/7` | At the pharmacy also allowed a price question; the precise request distinguishes the intended phrase. | M55, POST |
| F167 | `55/I3/0` | Clarify the category boundaries: identity, location, transactions, and phrases with explicit time markers. | M55, POST |
| F168 | `55/I3/1` | Clarify the category boundaries: identity, location, transactions, and phrases with explicit time markers. | M55, POST |
| F169 | `55/I3/2` | Clarify the category boundaries: identity, location, transactions, and phrases with explicit time markers. | M55, POST |
| F170 | `55/I3/3` | Clarify the category boundaries: identity, location, transactions, and phrases with explicit time markers. | M55, POST |
| F171 | `55/W0/1` | The original free conversational alternatives admitted indirect readings. Both replacements have subject-auxiliary disagreement. | M55, U10, POST |
| F172 | `55/W1/1` | Narrative present is legitimate; test a person disagreement instead of condemning tense use. | M55, U11, POST |
| F173 | `55/W1/4` | A possessive copular name statement is grammatical. Test a genuine name-case error. | M55, U2, U10, U22, POST |
| F174 | `55/W2/0` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The key has matching subject and verb forms. я снідали and ми снідав combine a singular subject with a plural verb or a plural subject with a singular verb. | M55, U1, U10, POST |
| F175 | `55/W2/1` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The stated subject agrees with їду, not with the person/number forms їдеш or їдуть. | M55, U1, U10, POST |
| F176 | `55/W2/2` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. The subject agrees with буду; будеш and будемо belong to different persons or numbers. | M55, U1, U10, POST |
| F177 | `55/W2/3` | The original single-sequence word-order key rejects valid inversion. Replaced by a bounded sentence choice. Both alternatives break the fixed request phrase будь ласка. | M55, U1, U10, POST |
| F178 | `55/W3/0` | The name-introduction frame lacked a name and was not a complete sentence. | M55, U22, POST |
| F179 | `55/W5/0` | Replace the valid copular name statement with a genuine case error. | M55, U2, U10, U22, POST |
| F180 | `55/W5/1` | Narrative present is possible and a slash string is not one replacement. The speaker now determines a single past-gender correction. | M55, U11, POST |
