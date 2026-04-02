<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Missing section heading: 'Активний i пасивний стан'
- FIX: Too short: 2809 words (target: 4000, minimum: 3400)
- NOTE: Missing 1/14 required vocab: неперехідне дієслово (intransitive verb — no direct object)
</correction_directive>

LEARNINGS FROM PAST BUILDS (same error patterns seen before):
- [GLOBAL] сес-тра is a VALID word division per Правопис 2019 §49. Do NOT mark it as an error. Phonetic syllabification (се-стра) and typographic word division (сес-тра) follow different rules — both are correct in their respective contexts.
- [GLOBAL] Ukrainian textbooks teach a hands-on-EARS test for voicing (закрий долонями вуха), NOT a hand-on-throat test. The hand-on-throat test is a valid phonetics technique but must NOT be attributed to Ukrainian textbooks. Source: Кравцова 2019, Grade 2, p.39.
- [GLOBAL] Do NOT invent Ukrainian words for minimal pairs. "Сір" is NOT a word meaning "grey" — the correct form is "сірий". Use verified minimal pairs only: кит/кіт, бити/біти, лис/ліс.
- [GLOBAL] NEVER frame Ukrainian as "lacking" or "missing" letters that Russian has. Ukrainian has its own 33-letter alphabet — it is complete. Do NOT write "Ukrainian lacks Ъ, Ы, Э" or "Ukrainian doesn't have these Russian letters." Instead, highlight what Ukrainian HAS: Ґ, Є, Ї, І are unique to Ukrainian. Present Ukrainian on its own terms.
- [GLOBAL] NO LLM filler phrases. Do NOT write: "Let us start with...", "Numbers unlock the real Ukraine", "You now possess a complete...", "It is incredibly versatile", "one of the most rewarding skills". Start sections with a dialogue, a question, or a concrete example — never with a generic motivational opener. If a sentence could appear in any language course about any topic, delete it.
- [GLOBAL] Every exercise item must test something EXPLICITLY taught in the preceding prose. If an exercise tests the collocation "малювати картину", the prose must contain "малювати картину" as a taught example. Do NOT test collocations, vocabulary, or patterns that the learner has to infer — test what was taught.
- [GLOBAL] Quiz correct answers must be RANDOMIZED across positions. Do NOT place the correct answer at index 0 for all items. Distribute correct answers roughly evenly across all positions (0, 1, 2) to prevent pattern-guessing.
- [GLOBAL] Do NOT use spatial metaphors for abstract grammatical requirements. Example: "на" with musical instruments is NOT "on top of" — it is an abstract grammatical requirement that must be memorized. Misleading mnemonics cause incorrect generalizations. If a rule must simply be memorized, say so directly.
- [GLOBAL] Memorized chunks are allowed before their grammar is formally taught. Natural Ukrainian expressions (Мені подобається, У мене є, Мене звати, Як справи?, Звідки ти?, Скільки коштує?, Мені ... років) can appear in ANY module as memorized chunks, even if the underlying grammar (dative, genitive, etc.) is not taught until later. This mirrors how Ukrainian children and L2 learners naturally acquire language. Do NOT flag these as forward-references. DO flag premature drilling of case paradigms, untaught vocabulary words, and grammar analysis before its module.
- [GLOBAL] Inline activity markers (<!-- INJECT_ACTIVITY: ... -->) must ONLY appear AFTER all concepts they test have been taught. If an activity tests both soft signs and apostrophes, it must appear after BOTH sections, not after the first one. This is critical in Ukrainian where apostrophe rules (б,п,в,м,ф,р + я,ю,є,ї) appear constantly — placing an apostrophe exercise before the apostrophe section teaches wrong sequencing. Rule: scan each activity's items and verify every tested concept has a preceding H2 section that teaches it.

# Section-by-Section Generation — Section 1/6

You are writing ONE SECTION of a Ukrainian language module. Write ONLY this section — nothing else.

**Module:** 23: Пасивний стан (вступ) (B1, B1.3 [Verbs])
**Section to write:** Активний і пасивний стан (~780 words total)
**Word target for this section:** 780 words (aim for 858 to account for undershoot)

---

## Section Skeleton (follow this exactly)

## Активний і пасивний стан (~780 words total)
- P1 (~120 words): Introduction to "стан дієслова" (verb voice) as the relationship between the doer (підмет) and the action. Definition of Active Voice (активний стан): the subject performs the action (Марія читає статтю). Definition of Passive Voice (пасивний стан): the subject undergoes the action (Стаття читається Марією).
- P2 (~130 words): Deep dive into Active Voice in Ukrainian. Why it is the "default" setting. Examples of transitive verbs (перехідні дієслова) taking direct objects: Архітектор проєктує будівлю, Уряд ухвалив закон, Студенти слухають лекцію.
- P3 (~150 words): The stylistic "Hard Rule" of Ukrainian: Preference for active over passive. Citing Zabolotnyi (Grade 8) and Avramenko (Grade 11) regarding "канцелярит" (bureaucratese). Comparison: "Ми виконали план" (natural) vs "План був виконаний нами" (stiff/unnatural).
- P4 (~160 words): Specific scenarios where passive IS appropriate: 1. Unknown agent (Скарб було знайдено), 2. Focus on the result (Роботу завершено), 3. Academic/Technical style (Елемент було відкрито), 4. Official/Legal context (Закон ухвалено).
- P5 (~120 words): The linguistic "beauty" of choice: explaining how switching voice allows the speaker to emphasize either the person or the achievement. Example: "Я написав книгу" (Me focus) vs "Книгу написано" (Book focus).
- Exercise: [quiz, focus: Identify voice: активний стан, пасивний -ся, or пасивний -но/-то, 10 items]

---
## Full Plan (for reference)

<plan_content>
module: b1-023
level: B1
sequence: 23
slug: passive-voice-intro
version: '3.0'
title: Пасивний стан (вступ)
subtitle: Пасивні конструкції через зворотні дієслова та форми на -но/-то
focus: grammar
pedagogy: PPP
phase: B1.3 [Verbs]
word_target: 4000
objectives:
- 'Learner can identify passive constructions in Ukrainian and distinguish them from active voice: Робітники будують дім (active)
  vs Дім будується робітниками (passive)'
- 'Learner can form passive constructions using зворотні дієслова with -ся: будується, читається, продається, передається'
- 'Learner can use the uniquely Ukrainian -но/-то impersonal passive forms: Дім збудовано. Книгу прочитано. Роботу виконано.'
- Learner understands that Ukrainian AVOIDS passive constructions and prefers active voice — this is a key stylistic difference
  from English
- Learner can transform passive sentences to active and vice versa, choosing the more natural Ukrainian option in context
dialogue_situations:
- setting: 'Guided tour of a newly renovated Палац культури (m, Palace of Culture)
    in Дніпро — describing what was done: Цей зал (m, hall) був побудований у 1960-х.
    Стіни (pl, walls) були пофарбовані минулого місяця. Вхід (m, entrance) буде відкрито
    для публіки завтра.'
  speakers:
  - Архітектор
  - Журналіст
  motivation: 'Passive voice: був побудований, були пофарбовані, буде відкрито'
content_outline:
- section: Активний i пасивний стан
  words: 750
  points:
  - 'Core concept: стан дієслова describes the relationship between the subject and the action. Активний стан: підмет виконує
    дію. Студенти читають книгу. Пасивний стан: підмет зазнає дії. Книга читається студентами. The meaning is the same, but
    the focus shifts.'
  - 'Ukrainian strongly prefers active voice (Заболотний Grade 8 p.95): ''Українська мова уникає пасивних конструкцій. Тому
    перевагу, де це можливо, слід надавати дієсловам активного стану.'' This is NOT like English, where passive is common
    in academic writing. In Ukrainian, excessive passive = канцелярит (bureaucratese).'
  - 'When passive IS appropriate in Ukrainian: 1. The agent is unknown: Місто було засновано у X столітті. 2. The result matters
    more than the agent: Завдання виконано. 3. Scientific/technical descriptions: Елемент було відкрито у 1898 році. 4. Official
    documents: Закон ухвалено Верховною Радою.'
- section: Пасив через зворотні дієслова
  words: 700
  points:
  - 'Formation from Заболотний Grade 8 p.95: ''Засобом вираження пасивного стану є формотворчий афікс -ся, що додається до перехідних
    дієслів: будується, передається, продовжується.'' The subject receives the action: Добре слово дім будує. (active) → Поганим
    словом все руйнується. (passive with -ся)'
  - 'Agent expression with орудний відмінок: Книга читається учнями уважно. Рецепт готується нами вправно. But note: Авраменко
    Grade 11 p.81 observes that Ukrainian speakers often find the agent awkward in -ся passives: ''Речення якої колонки звучать
    більш природно?'' — active versions win. Use active when possible.'
  - 'Distinguishing passive -ся from other зворотні (M22 categories): Він миється. (reflexive — washes himself) Цей товар
    продається у кожному магазині. (passive — is sold) Test: if the subject is inanimate and not doing the action to itself,
    it''s likely passive.'
  - 'Common passive -ся verbs: будуватися (to be built), використовуватися (to be used), вважатися (to be considered), називатися
    (to be called), вироблятися (to be produced), знаходитися (to be located). Note: знаходитися is so common that its passive
    origin is forgotten.'
- section: 'Форми на -но/-то: українська спеціальність'
  words: 850
  points:
  - 'From Авраменко Grade 11 p.81: ''Синтаксичні конструкції з формами на -но, -то.'' Усі інгредієнти придбано. (All ingredients
    have been obtained.) Роботу виконано. (The work has been completed.) Книжку прочитано. (The book has been read.) Двері
    зачинено. (The door has been closed.)'
  - 'Formation: пасивний дієприкметник stem + -о: зроблений → зроблено, прочитаний → прочитано, відкритий → відкрито, забутий
    → забуто. These are IMPERSONAL — there is no nominative subject. The object stays in знахідний відмінок: Зроблено роботу
    (not *робота).'
  - 'Why this is uniquely Ukrainian (Заболотний Grade 8 p.97): ''Пасивні конструкції з дієслівними формами на -но, -то в українській
    мові використовують обмежено'' — but they are MORE NATURAL than -ся passives. This is Ukrainian''s preferred passive:
    Засідання проведено. (natural) vs *Засідання проводиться. (awkward bureaucratese) vs Провели засідання. (active — also
    natural)'
  - 'Practice: transform active sentences to -но/-то passives: Учні написали диктант. → Диктант написано. Архітектор спроєктував
    будівлю. → Будівлю спроєктовано. Note how the agent disappears — this is the point.'
- section: Порівняння трьох конструкцій
  words: 600
  points:
  - 'Three ways to say the same thing: ACTIVE: Робітники збудували дім. (Workers built the house.) PASSIVE -ся: Дім збудований
    робітниками. / Дім будувався робітниками. PASSIVE -но: Дім збудовано. (The house has been built.) Ukrainian naturalness
    ranking: Active > -но/-то > -ся passive.'
  - 'Decision guide for learners: 1. Default: use ACTIVE voice. 2. If agent is unknown/irrelevant: use -но/-то. 3. For processes/states
    of inanimate subjects: -ся is acceptable (магазин знаходиться, квиток продається). 4. Avoid -ся passive with explicit
    agent (орудний) — sounds unnatural.'
  - 'Contrastive exercise: given 8-10 sentences, choose the most natural Ukrainian version. Most should be active or -но/-то.
    One or two may legitimately use -ся (знаходиться, називається).'
- section: 'Практика: пасив у контексті'
  words: 750
  points:
  - 'Reading passage: a Ukrainian news report about a cultural event or construction project. Contains natural passive usage:
    Фестиваль проведено у Львові. Новий міст збудовано. Виставку відкрито. Книгу видано. Comprehension questions test LANGUAGE:
    — Знайдіть усі конструкції на -но/-то. — Перетворіть їх на активні речення. — Чому автор обрав пасив у цих випадках?'
  - 'Transformation exercises: Active → -но/-то: Уряд ухвалив закон. → Закон ухвалено. -ся passive → active: Місто засновувалося
    козаками. → Козаки заснували місто. -но/-то → active: Листа надіслано. → Хтось надіслав листа.'
  - 'Production: learners write a short report (5-6 sentences) about an accomplishment using -но/-то forms: Проєкт завершено.
    Результати опубліковано. Звіт подано вчасно. Усі завдання виконано.'
- section: Підсумок та перехід до M24
  words: 450
  points:
  - 'Summary: пасивний стан — підмет зазнає дії. Два способи: -ся (будується) i -но/-то (збудовано). Українська мова надає
    перевагу активному стану. -но/-то — спеціально українська конструкція, природніша ніж -ся пасив. Self-check: Я можу розрізнити
    активний i пасивний стан ✓/✗, Я можу утворити форму на -но/-то ✓/✗, Я знаю, коли пасив доречний ✓/✗.'
  - 'Preview: M24 — Творення дієслів. How prefixes and suffixes create new verbs from existing ones: писати → написати → переписати.
    This completes the verb formation picture before the communication module M25 puts all verb skills into practice.'
vocabulary_hints:
  required:
  - пасивний стан (passive voice — subject receives the action)
  - активний стан (active voice — subject performs the action)
  - будуватися (to be built — passive -ся)
  - називатися (to be called — passive -ся, very common)
  - знаходитися (to be located — passive -ся, lexicalized)
  - використовуватися (to be used — passive -ся)
  - збудовано (has been built — -но/-то form)
  - виконано (has been completed — -но/-то form)
  - прочитано (has been read — -но/-то form)
  - ухвалено (has been adopted/passed — -но/-то form, laws)
  - канцелярит (bureaucratese — overuse of passive/nominal style)
  - перехідне дієслово (transitive verb — takes a direct object)
  - неперехідне дієслово (intransitive verb — no direct object)
  - орудний відмінок (instrumental case — agent in passive)
  recommended:
  - вважатися (to be considered)
  - продаватися (to be sold)
  - вироблятися (to be produced)
  - видано (has been published — -но/-то)
  - засновано (has been founded — -но/-то)
  - спроєктовано (has been designed — -но/-то)
  - опубліковано (has been published — -но/-то)
  - надіслано (has been sent — -но/-то)
  - природний (natural — as opposed to forced/awkward)
activity_hints:
- type: quiz
  focus: 'Identify voice: активний стан, пасивний -ся, or пасивний -но/-то'
  items: 10
- type: sentence-builder
  focus: Transform active sentences to -но/-то passive and vice versa
  items: 8
- type: fill-in
  focus: Complete sentences with the correct -но/-то form of the given verb
  items: 8
- type: error-correction
  focus: Fix unnatural passive constructions by rewriting as active voice
  items: 6
- type: match-up
  focus: Match active sentences to their -но/-то equivalents
  items: 8
connects_to:
- b1-022 (Зворотні дієслова — пасивноподібні category expanded here)
- b1-024 (Творення дієслів — verb formation completes Phase 3 grammar)
- b1-058 (Пасивні дієприкметники — participle-based passive, Phase 7)
prerequisites:
- b1-022 (Reflexive verbs — -ся formation and semantic categories)
grammar:
- 'Активний vs пасивний стан: subject does vs receives the action'
- 'Passive via -ся: будується, використовується (from перехідні дієслова)'
- 'Ukrainian -но/-то forms: збудовано, виконано, прочитано (impersonal passive)'
- '-но/-то formation: passive participle stem + -о, object stays in Зн.'
- 'Stylistic preference: active > -но/-то > -ся passive'
- Distinguishing passive -ся from reflexive -ся (context and animacy)
register: академічний
references:
- title: Заболотний Grade 7, §30
  notes: 'Дієслівні форми на -но, -то: творення від пасивних дієприкметників (створений -> створено), значення результату дії.'
- title: Авраменко Grade 7, §51
  notes: 'Безособові форми на -но, -то. "В українській мові з орудним відмінком виконавця ці форми не вживаємо".'
- title: Заболотний Grade 7, §30
  notes: 'Пасивні конструкції з дієсловами на -ся. Stylistic preference: Active > -но/-то > -ся passive.'

</plan_content>

---

## Knowledge Packet

<knowledge_packet>
# Verified Knowledge Packet: Пасивний стан (вступ)
**Module:** passive-voice-intro | **Phase:** B1.3 [Verbs]
**Textbook grades searched:** 1, 2, 3, 5

---

## Активний i пасивний стан

> **Source:** bolshakova, Grade 1
> **Section:** Сторінка 7
> **Score:** 0.50
>
> 7
> СЛОВА — НАЗВИ ДІЙ
> Кожну дію ти можеш назвати словом.
> ЩО РОБИТЬ?
> бігає
> стрибає
> сидить
> читає
> спить
> Діти на подвір’ї. Олена стрибає. Тарас бігає. 
> Алла сидить на лаві. Ганна читає книжку. 
> Кіт Нявчик спить.
> Що робить кожен хлопчик? Вибери правильну відповідь.
>  
>  Малює картину.
>  Читає книжку.
>  Грає на барабані.
>  Миє посуд.
>  Готує бутерброд.
>  П’є чай.
> 1

## Пасив через зворотні дієслова

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 58
> **Score:** 0.50
>
> 55
> 121.	А.  Визначте лексичне значення розміщеного в центрі схеми слова. 
> бігти
> при
> за
> до
> по
> на
> в
> з
> від
> ви
> пере
> об
> під
> Б.  Додайте почергово до дієслова бігти префікси. Які додаткові зна-
> чення вносять вони в лексичне значення дієслова? 
> В.  Поміркуйте, як префікси допомагають збагатити мову. 
> Префікс (від лат. prae – попереду і fixus – прикріпле-
> ний) – це значуща частина слова, яка стоїть перед коренем 
> і служить для утворення нових слів. НАПРИКЛАД: чудовий – 
> пречудовий, їхати – виїхати, плата – передплата, хмар-
> ний – безхмарний.
> Слово може мати переважно один префікс, але іноді – 
> два або більше.

## Форми на -но/-то: українська спеціальність

> **Source:** avramenko, Grade 5
> **Section:** Сторінка 2
> **Score:** 0.50
>
> — спостереження;
> — творче  завдання;
> — ключ-відповідь;
> — робота  в  парах;
> — робота  в  групах;
> — словник;
> — домашнє  завдання.
> УМОВНІ  ПОЗНАЧЕННЯ:
> УДК 
>  
> А21
> Авраменко О. 
> Українська мова : підруч. для 5 кл. закл. загальн. 
> середн. освіти / Олександр Авраменко. — Київ : Гра-
> мота, 2022. — 208 с. : іл.
> ISBN 978-966-349-917-8
> У підручнику подано матеріали для повторення та уза-
> гальнення вивченого в початкових класах, а також розділи: 
> «Лексикологія», «Будова слова. Орфографія», «Синтаксис і 
> пунктуація» (за Модельною навчальною програмою «Україн-
> ська мова. 5–6 класи: для закладів загальної середньої осві-
> ти»; атори О. В. Заболотний, В. В. Заболотний, В. П. Лаврин-
> чук, К. В. Плівачук, Т. Д. Попова).
> УДК 
> ISBN 978-966-349-917-8
> © Авраменко О.

> **Source:** avramenko, Grade 5
> **Section:** Сторінка 2
> **Score:** 0.33
>
> Аналізуємо 
> зміст та 
> особливості 
> художнього 
> твору
> Творчо 
> мислимо
> Даємо 
> відповіді 
> за змістом 
> твору
> УМОВНІ ПОЗНАЧЕННЯ
> Авраменко О.
> Українська література : підруч. для 5 кл. закл. за­
> гальн. середн. освіти / Олександр Авраменко. — Київ : 
> Грамота, 2022. — 288 с. : іл.
> ISBN 978-966-349-918-5
> Підручник відповідає вимогам Державного стан­
> дарту. Видання підготовлено відповідно до Модельної 
> навчальної про­грами «Українська література. 5–6 кла­
> си» для закладів загальної середньої освіти (автори: 
> Архипова В. П., Січкар С. І., Шило С.

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 225
> **Score:** 0.25
>
> 225
> Відомості із синтаксису й пунктуації.  Речення з однорідними членами
> 2.	 Запишіть утворені речення.  Підкресліть однорідні члени відповідно 
> до  того, якими членами речення вони є.
> 3.	 Поміркуйте та  зробіть висновки: як змінилися речення після того, як ви 
> їх доповнили?
> Вправа 365
> Складіть речення, щоб наведені слова були в них однорідними членами 
> (форму слів можна змінювати).
> сучасні, класичні 
> для хлопців і  дівчат 
> однотонні та  строкаті 
> не повсякденний, а  святковий 
> і зранку, і  ввечері 
> Вправа 366
> 1.	 Спишіть текст, де потрібно, заповнюючи пропуски.
> Сучасних підлітків не  потрібно змушувати вдягати 
> шап­ки та  шарфи. Вони утеплюют..ся з  радіс..тю, оскіль-
> ки вибір в..язаних шапок, стильних капелюхів, краси-
> вих шарфиків-снудів просто 
> колос..альний.

## Порівняння трьох конструкцій

> **Source:** vashulenko, Grade 2
> **Section:** Сторінка 81
> **Score:** 0.50
>
> 7| Прочитайте виразно вірш. Поясніть, кому дякують люди.
> Що роблять будівельники? 
> Що роблять хлібороби?
> Що роблять учителі?
> Що роблять ковалі? 
> Що роблять письменники?
> Тим, що в поле йдуть орати, 
> що плуги міцні кують, 
> що будують теплі хати, 
> пишуть книги нам читати, 
> зі шкіл науку надають, — 
> шана й дяка їм велика 
> од людей на вічні віки.
> Борис Грінченко
> Коваль — майстер, який куванням обробляє 
> метал, виготовляє металеві предмети.
> ____ -_____ _
> Поміркуй і скажи, від 
> якого слова походить 
> слово будівельник.
> 1 _______——
> Я — ДОСЛІДНИЦЯ
> Переглянь картини українських художників. Розкажи, 
> як на них зображено природу перед грозою.
> 8| Уяви себе письменником (письменницею). Прочитай 
> текст, добираючи з дужок дієслово, яке найточніше
> виражає думку.
> (Пролетіла, пройшла, минула) гроза.

> **Source:** bolshakova, Grade 1
> **Section:** Сторінка 9
> **Score:** 0.25
>
> 9
> Знайди слово — підпис до малюнка.
> 	
> озеро	
> літо	
> Оля	
> робот
> 	
> олень	
> жито	
> Олег	
> робота
> 	
> окунь	
> доміно	
> Олена	
> робітник
> 
> Текст. Заголовок. Текст і малюнки
> Робота Роббі зробили на 
> заводі. Він виконує різні про-
> грами. 
> Робот Роббі живе з нами. 
> Миє підлогу, поливає квіти. 
> Роббі не просто машина, він  — 
> наш друг. Ми разом граємо  
> і читаємо книжки. 
> Уранці робот усіх будить. 
> Увечері розповідає смішні істо-
> рії. А  вночі відпочиває, як і ми.
> Порівняй текст і малюнки. Знайди 
> схоже і відмінне. 
> Добери заголовок до тексту. 
> Дім
>  
> Завод
>  
> Робот Роббі
> 1
> 2
> О о
> бо	 во	
> го	 до
> ко	 ло	 мо	 но
> ро	 со	
> то	 шо

## Практика: пасив у контексті

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 157
> **Score:** 0.50
>
> 154
> 1. У великих і маленьких містах для дорослих і дітей 
> організовують театральні фестивалі, книжкові виставки. 
> 2. На літературних фестивалях письменники читають влас-
> ні поетичні та прозові твори. 3. Книжки збільшують наш 
> словниковий запас, розширюють світогляд. 
> ІІ. Розберіть за будовою виділене слово. 
> 377.	Хто зможе за одну хвилину утворити й записати 7 словосполу-
> чень із поданих слів? А хто ще більше? Форму слів можна змінювати. 
> Для поєднання окремих слів можна використовувати прийменники.

> **Source:** golub, Grade 5
> **Section:** Сторінка 123
> **Score:** 0.33
>
> 123
> 1. Приймай своє рішення та аргументуй його. 2. Не лінуйся 
> брати відповідальність за свої вчинки, за майбутнє своєї кра-
> їни. 3. Активність, ініціативність і відповідальність — важ-
> ливі риси громадянина і громадянки. 4. Наша країна потре-
> бує активної, цілеспрямованої, відповідальної і наполегливої 
> молоді. 5. Свою відповідальність ми маємо реалізувати 
> у школі, у родині й суспільстві.
>  
> ІІ   Чи поділяєте ви думки, висловлені в реченнях? Що озна-
> чає слово «завзяття»? Кого ви можете назвати завзятою 
> людиною? Завзяті громадяни корисні для суспільства? 
> Чому?
> 306   Розгляньте схему. Про що запитують зображені діти? Прочитайте 
> речення з однорідними членами. Скоротіть їх, вилучивши одно-
> рідні члени. Зробіть висновки, у яких дайте відповідь на постав-
> лене запитання.

## Підсумок та перехід до M24

> **Source:** bolshakova, Grade 2
> **Section:** Сторінка 53
> **Score:** 0.50
>
> 53
> • Продовж діалог. Запиши кілька реплік діалогу в зошит. 
> Пробач. 
> Я вчинив негарно.
> Дякую, що 
> вибачився.
> • Випиши слова — назви дій. 
> Зразок. Квіти (що роблять?) пнуться, ... .
> • Назви слова, які описують стани людини. Склади з двома 
> словами речення.
> Боїться, радіє, бігає, цікавиться, співає, дивується, танцює.
> сЛова — назви ДІЙ
> Що ти робиш у школі, удома, на вулиці? Запиши слова — 
> назви дій у стовпчики.
> Читаю, читання, пишу, письмо, малюю, малювання, 
> стрибаю, граю, гра, співаю, танцюю, танок, спілкуюся, роз-
> мовляю, розмова, їм, їжа, п’ю, бігаю, їжджу, копаю, саджу.
> У школі
> Удома
> на вулиці
>  
> Редагуємо
> • Пост

... (truncated for context window)
</knowledge_packet>

---

## Rules

Full Ukrainian immersion. Grammar explained IN Ukrainian. English only for disambiguation of false friends. Sentences max 30 words.

GRAMMAR RULES:
- Max 30 words per Ukrainian sentence
- Max 4 clauses per sentence
- All grammar constructions allowed
- Participles allowed
- Complex subordinate clauses allowed



- **NO IPA, NO Latin transliteration** — describe sounds by comparison.
- **Ukrainian quotes: «...»** for Ukrainian text.
- **Place exercise markers only** — write `<!-- INJECT_ACTIVITY: type, topic hint -->` where the skeleton places exercises. Do NOT write :::quiz or :::fill-in DSL directly.
- **NO meta-commentary** — no "In this section we will...", no vocabulary tables, no word count notes.
- **Zero Russian, zero Surzhyk, zero calques.**
- **Every bold Ukrainian word MUST have an English translation on first use.**
- **NO stress marks** — a deterministic tool adds them later.
- **Dialogue formatting:** Use blockquote `>` with speaker names in bold. Each turn on its own `>` line. NO blank lines between turns — all lines must be consecutive. Example:
  > — **Оксана:** Привіт! *(Hi!)*
  > — **Степан:** Добрий день! *(Good day!)*
  > — **Оксана:** Як справи? *(How are you?)*

## Output

Write the section starting with the H2 heading. Output ONLY the section content — no preamble, no summary, no notes.
