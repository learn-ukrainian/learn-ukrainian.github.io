<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 31: Час іде, дощ іде (B1, B1.3 [Motion Verb Universe])

## Plan vocabulary to verify

- переносне значення (figurative meaning)
- пряме значення (literal meaning)
- дощ іде (it's raining — figurative use of іти)
- час іде (time passes)
- час летить (time flies)
- справи йдуть (things are going — about progress)
- мова йде про (it's about / the topic is)
- йтися (impersonal — to be about: йдеться про)
- нести відповідальність (to bear responsibility)
- вести переговори (to conduct negotiations)
- вести себе (to behave)
- злетіти (to soar — figurative: prices soar)
- водити за ніс (to deceive — idiom)
- вийти (to turn out / result)
- підійти (to suit — figurative)
- дійти до висновку (to reach a conclusion)
- обійтися (to get by without)
- хмари пливуть (clouds drift)
- мурашки біжать (goosebumps)
- багатозначне слово (polysemous word)
- фразеологізм (phraseological unit / idiom)

## Sections to research

- **Дієслова руху в переносному значенні**: Bridge from M28-M34: learners have mastered the literal motion verb system. But Ukrainians use motion verbs figuratively every day — for time, weather, processes, emotions. This module teaches the figurative layer that makes speech natural.; From Авраменко Grade 5 p.27: a dialogue between siblings about 'Піде дощ' — 'А хіба дощ може ходити?' This is how Ukrainian textbooks introduce the concept of переносне значення (figurative meaning). Лексичне значення can be пряме (literal) or переносне.; From Авраменко Grade 10 p.19: летіти is багатозначне — пташка летить (literal) vs час летить (figurative, = fast). Understanding polysemy is essential for natural Ukrainian.
- **Iти / ходити: найширший спектр**: Weather: дощ іде (it's raining), сніг іде (it's snowing). NOT *дощ падає (English calque 'rain falls'). In Ukrainian, rain 'goes.' Надворі йде сильний дощ. Вчора йшов сніг цілий день. From Вашуленко Grade 2 p.80: textbook exercise replacing 'іде' with synonyms: Iде катер → Пливе катер. Iде зима → Настає зима.; Time: час іде (time passes), роки йдуть (years go by), літо йде до кінця (summer is ending). Iдуть дні, тижні, місяці... Рік іде за роком. Note: for fast time, use летить (Час летить!) — see below.; Processes and events: фільм іде (a film is showing/playing), урок іде (class is in session), концерт іде (concert is on), ремонт іде (renovations are underway), переговори йдуть (negotiations are in progress), справи йдуть добре (things are going well).
- **Летіти: швидкість**: Летіти figuratively = moving very fast, passing quickly: Час летить! (Time flies!). Дні летять (Days fly by). Новина облетіла все місто (News spread around the whole city). Ціни злетіли (Prices skyrocketed — злетіти = take off/soar).; Prefixed figurative forms: злетіти (to soar): Ціни злетіли вгору. вилетіти (to get fired/expelled, colloquial): Вилетів з роботи. пролетіти (to fly by): Канікули пролетіли непомітно. налетіти (to swoop in/rush at): Раптом налетів вітер.; Practice: 6-8 sentences where learners identify literal vs figurative uses of летіти and its prefixed forms.
- **Пливти: плавність і повільність**: Пливти figuratively = moving smoothly, drifting, flowing: Хмари пливуть (Clouds drift). Мелодія пливе (The melody flows). Місяць пливе по небу (The moon floats across the sky). Думки пливуть (Thoughts drift). Туман пливе над річкою (Fog drifts over the river).; Contrast with летіти: Час летить (fast) vs Час пливе (slow/smooth). Both describe time passing, but with opposite speed connotations.; Practice: 4-6 sentences using пливти figuratively.
- **Бігти, їхати, нести та інші**: Бігти figuratively = hurrying, being busy: Час біжить (Time runs — faster than іде, slower than летить). Вода біжить у річці (Water flows in the river). Мурашки біжать по шкірі (Goosebumps — literally 'ants run on skin').; Їхати figuratively (colloquial): Дах їде (going crazy — literally 'the roof is going'). Їхати на чомусь (to be obsessed with something, colloquial).; Нести/носити figuratively: нести відповідальність (to bear responsibility). носити ім'я (to bear a name): Вулиця носить ім'я Шевченка. виносити рішення (to make a decision — formal/legal). Річка несе води (The river carries its waters — poetic).
- **Українські вирази vs англійські кальки**: Decolonized usage — genuine Ukrainian expressions: дощ іде (NOT *дощ падає — English calque 'rain falls'). час іде/летить/біжить (NOT *час пробігає — awkward). фільм іде (NOT *фільм показують — though both exist, іде is natural). справи йдуть (NOT *справи є — English 'things are').; Russicism warnings for figurative motion: *мова іде — CORRECT is мова йде or йдеться (the impersonal form йтися is most natural: Йдеться про важливі питання). *діло йде — can be a Russicism; prefer справа стоїть/річ у тому. Always check: does this expression exist in Ukrainian, or am I translating from Russian/English?; Practice: learners rephrase English sentences using natural Ukrainian figurative motion verbs. 6-8 translation-avoidance exercises.
- **Підсумок: буквальне і переносне**: Summary table of key figurative uses: іти: weather, time, processes, events. летіти: speed, rapid change. пливти: smoothness, drifting. бігти: hurrying, flowing. нести/носити: responsibility, names. вести/водити: negotiations, behavior.; Preview of M36: Подорож Україною — travel narratives combining literal motion verbs with the cultural vocabulary of Ukrainian travel.

## Instructions

Complete ALL of the following verification tasks. Each task MUST include at least one tool call.

### Task 1: Verify ALL vocabulary words exist in VESUM

Call `verify_words` with EVERY word from the plan vocabulary above. Batch them (10-15 per call).

Report:
- ✅ Words confirmed in VESUM
- ❌ Words NOT in VESUM (these must not be used in the module)

### Task 2: Search textbooks for each section topic

For each section title above, call `search_text` with the Ukrainian keywords.

Report the most relevant textbook excerpt for each section (author, grade, key quote).

### Task 3: Verify grammar rules

For any grammar rules mentioned in the plan, call `query_pravopys` to confirm the official 2019 rule.

Report the Правопис section number and key rule text.

### Task 4: Check for calques

Call `search_style_guide` for any phrases in the plan that might be calques. Check at least 3 phrases.

Report any calques found with the correct Ukrainian alternative.

### Task 5: Verify CEFR appropriateness

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (B1).

Report any words above the target level.

## Output format

Output your findings in this exact format:

<verification>
## VESUM Verification
- Confirmed: [list of verified words]
- Not found: [list of words to avoid]

## Textbook Excerpts
### Section: [title]
> [relevant textbook quote]
> Source: [author, grade]

### Section: [title]
> [relevant textbook quote]
> Source: [author, grade]

## Grammar Rules
- [rule]: Правопис §[number] — [key text]

## Calque Warnings
- [phrase]: [calque or OK] — [correct form if calque]

## CEFR Check
- [word]: [level] — [OK or above target]
</verification>
