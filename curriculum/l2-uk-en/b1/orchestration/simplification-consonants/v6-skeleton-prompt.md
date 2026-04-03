<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Skeleton Prompt — Module Structure Planning

You are planning the detailed paragraph-level structure of a Ukrainian language module. Do NOT write the full content — only plan the structure.

## Your task

Create a detailed paragraph-level skeleton for module **7: Спрощення приголосних** (B1, B1.1 [Baselines & Morphophonemics]).

**Word target: 4000 words** of prose. Your skeleton must budget every word.

---

## Plan

<plan_content>
module: b1-007
level: B1
sequence: 7
slug: simplification-consonants
version: '3.1'
title: "Спрощення приголосних"
subtitle: "Щастя — щасливий: коли приголосний випадає"
focus: grammar
pedagogy: PPP
phase: "B1.1 [Baselines & Morphophonemics]"
word_target: 4000
objectives:
  - "Learner can identify consonant simplification in Ukrainian words and explain
    WHY the consonant drops: a cluster of three consonants simplifies to two for ease
    of pronunciation (милозвучність)"
  - "Learner can apply spelling rules for simplification that is закріплене на письмі
    (reflected in writing): тижневий (not *тижденевий), щасливий (not *щастливий),
    корисний (not *користний)"
  - "Learner can identify exceptions where simplification occurs in speech but NOT
    in writing: шістнадцять, зап'ястний, контрастний"
  - "Learner can distinguish simplification from чергування (alternation): simplification
    = consonant DROPS; alternation = consonant CHANGES"
dialogue_situations:
  - setting: 'Dictation exercise in a Дніпро classroom — the teacher reads words aloud
      and students discuss which letters disappear: серце (not серДце), тижневий (not
      тижДневий), чесний (not чесТний), щасливий (not щасТливий).'
    speakers:
      - Вчитель
      - Студенти
    motivation: 'Consonant simplification: серДце→серце, чесТний→чесний, щасТливий→щасливий'
content_outline:
  - section: "Що таке спрощення?"
    words: 600
    points:
      - "Bridge from M08-M10: learners now understand чергування — sounds that CHANGE
        to other sounds. Спрощення is different: a sound DISAPPEARS entirely from
        a consonant cluster. Литвінова Grade 5 p.180: 'Одним із засобів милозвучності
        української мови є спрощення приголосних. Якщо в процесі словотворення виникає
        група з трьох приголосних, один із них може випадати.'"
      - "Demonstration from Литвінова Grade 5 p.180, вправа 296: проїЗД + Н = проїЗДНий
        -> проїзний. The [д] drops because the cluster [здн] is awkward to pronounce.
        Ukrainian prefers two-consonant clusters over three-consonant ones."
      - "Key distinction: чергування = sound A becomes sound B; спрощення = sound
        A disappears. Both are morphophonemic processes, but they work differently.
        чергування: друг -> друже ([г] -> [ж]) спрощення: щастя -> щасливий ([т] drops)"
  - section: "Спрощення, закріплене на письмі"
    words: 850
    points:
      - "Complete table from Заболотний Grade 5 p.110: [ждн] -> [жн]: тиждень — тижневий
        [здн] -> [зн]: проїзд — проїзний, виїзд — виїзний [стл] -> [сл]: щастя — щасливий,
        лестощі — улесливий [стн] -> [сн]: радість — радісний, якість — якісний, честь
        — чесний, користь — корисний, вість — вісник [скн] -> [сн]: бризки — бризнути,
        тиск — тиснути [слн] -> [сн]: масло — масний"
      - "From Литвінова Grade 5 p.181: additional examples organized by cluster type.
        Emphasis: in these words, the simplified consonant is NOT written. You write
        тижневий, not *тижд­невий. The spelling reflects the pronunciation."
      - "How to recognize simplification in practice: If a derived word seems to be
        'missing' a consonant compared to its base form, it is likely спрощення. Base:
        тиждень (has [д]). Derived: тижневий (no [д]). Base: щастя (has [т]). Derived:
        щасливий (no [т]). Practice: learners identify the 'missing' consonant in
        10+ pairs."
      - "Авраменко Grade 5 p.109: орфограма 'спрощення в групах приголосних' — students
        learn to recognize this as a specific spelling pattern that requires rule
        knowledge, not just memory."
  - section: "Винятки: спрощення у вимові, але не на письмі"
    words: 650
    points:
      - "From Заболотний Grade 5 p.110: Group 1 — no simplification at all (both speech
        and writing): пестливий, хвастливий, кістлявий — pronounce and write [стл].
        These are EXCEPTIONS to the [стл]->[сл] rule."
      - "Group 2 — simplification in speech only (write the consonant): шістнадцять
        [шіс:нац':ат'], зап'ястний [зап'ас:ний], контрастний [контрасний], баластний
        [баласний]. Авраменко Grade 5 p.109: 'У словах невістці, шістсот i подібних
        літеру т пишемо, але звук [т] не вимовляємо.'"
      - "How to remember which is which: The exceptions that KEEP the letter in writing
        are mostly words where the base form is clearly felt: шість -> шістнадцять
        (the connection to шість is obvious, so the т stays in writing). The words
        where simplification IS in writing have drifted farther from their base: щастя
        -> щасливий (the connection is felt less directly)."
  - section: "Спрощення [сонце], [серце] та інші особливі випадки"
    words: 600
    points:
      - "Words where simplification is so old it is not always recognized: сонце [сонце]
        — but is there a 'missing' [л]? (cf. солоній) серце [серце] — is there a 'missing'
        [д]? (cf. сердитий, сердечний) These etymological simplifications are taught
        as орфограми: in серце, the [д] dropped historically but surfaces in related
        words."
      - "Голуб Grade 5 p.93, вправа 234: connecting спрощення to the concept of милозвучність.
        Students are asked: 'Чи можна вважати спрощення засобом милозвучності? Чому?'
        Answer: yes — Ukrainian avoids difficult consonant clusters as part of its
        phonetic character."
      - "Practice: learners work with word families, identifying where simplification
        occurs and where it does not: тиждень: тижневий (спрощення), тижня (біглий
        голосний from M08), щотижня (спрощення). Multiple morphophonemic processes
        in one family."
  - section: "Спрощення у дієслівних формах та прикметниках"
    words: 600
    points:
      - "Simplification in adjective formation from nouns: якість — якісний ([стн]->[сн])
        совість — совісний ([стн]->[сн]) ненависть — ненависний ([стн]->[сн]) область
        — обласний ([стн]->[сн]) These follow the regular [стн]->[сн] pattern."
      - "Simplification in verb-related forms: виїзд — виїзний ([здн]->[зн]) тиск
        — тиснути ([скн]->[сн]) блиск — блиснути ([скн]->[сн]) These show that спрощення
        applies across parts of speech."
      - "Connecting to previous modules: the learner now has three morphophonemic
        tools: чергування голосних (M08), чергування приголосних (M09-10), and спрощення
        (this module). Together, they explain most of Ukrainian's spelling 'irregularities.'"
  - section: "Спрощення vs. чергування: порівняння"
    words: 400
    points:
      - "Side-by-side comparison: | Feature | Чергування | Спрощення | | What happens
        | Sound A -> Sound B | Sound A -> zero | | Example | друг -> друже | щастя
        -> щасливий | | Trigger | Morphological (case, person) | Cluster of 3+ consonants
        | | Reversible? | Yes (друже -> друг) | Yes (щасливий -> щастя) | Both are
        regular, predictable, and essential for Ukrainian spelling."
      - "Diagnostic algorithm for learners: 1. Does the derived word have FEWER
        consonants than the base? → спрощення. 2. Does the derived word have a DIFFERENT
        consonant? → чергування. 3. Apply: сонце vs сонячний (missing [л]? спрощення).
        друг vs друже ([г]→[ж] чергування). Each step builds on the table above."
      - "Practice: mixed exercises where learners identify WHETHER a given change
        is чергування or спрощення, and WHICH specific type it is. This integrates
        learning from M08-M11."
      - "Cross-reference to real text: excerpt from a news article or literary passage
        containing both processes. Learners annotate each morphophonemic change,
        labeling it as чергування (type) or спрощення (cluster). Demonstrates that
        both processes co-occur naturally in authentic Ukrainian prose."
  - section: "Підсумок і практика"
    words: 300
    points:
      - "Quick reference: all спрощення patterns with one example each. Self-check:
        Дайте відповіді на запитання: 1. Чому у слові 'щасливий' немає літери т? 2.
        Чому у слові 'шістнадцять' літера т пишеться? 3. Яка різниця між спрощенням
        i чергуванням? 4. Утворіть прикметники: радість, якість, тиждень."
      - "Preview of next module: Iменники на -ар, -яр, -ин (M12) — shifting from phonetics
        to morphology, applying all the morphophonemic knowledge to specific noun
        subclasses."
vocabulary_hints:
  required:
    - "спрощення (simplification — dropping of a consonant from a cluster)"
    - "група приголосних (consonant cluster — sequence of consonants)"
    - "милозвучність (euphony — pleasant sound quality of speech)"
    - "випадати (to drop out — of a sound disappearing)"
    - "вимова (pronunciation — how words are spoken)"
    - "правопис (orthography — correct spelling)"
    - "закріплений (fixed — reflected in standard spelling)"
    - "виняток (exception — case that does not follow the rule)"
    - "словотворення (word formation — creating new words)"
    - "прикметник (adjective)"
    - "іменник (noun)"
    - "основа (stem — the word minus its ending)"
    - "орфограма (orthographic rule — spelling pattern requiring knowledge)"
    - "морфонологія (morphophonology — sound changes in morphology)"
  recommended:
    - "чергування (alternation — for comparison)"
    - "корінь (root)"
    - "суфікс (suffix)"
    - "прислівник (adverb)"
    - "транскрипція (phonetic transcription)"
    - "відмінювання (declension — changing word forms)"
    - "дієприкметник (participle)"
    - "похідний (derived — formed from another word)"
    - "непохідний (underived — base form)"
activity_hints:
  - type: fill-in
    focus: "Form adjectives or adverbs from nouns, applying simplification (e.g.,
      щастя -> щасл___вий, тиждень -> тижн___вий)"
    items: 8
  - type: quiz
    focus: "Decide: does the derived word keep or drop the consonant? (e.g., шість
      + -надцять = шістнадцять [keep] vs. радість + -ний = радісний [drop])"
    items: 8
  - type: group-sort
    focus: "Sort words into two groups: спрощення закріплене на письмі vs. спрощення
      тільки у вимові"
    items: 10
  - type: match-up
    focus: "Match base words with their simplified derivatives (e.g., проїзд <-> проїзний,
      щастя <-> щасливий)"
    items: 8
  - type: error-correction
    focus: "Find spelling errors: words written with or without the simplified consonant
      incorrectly (e.g., *щастливий -> щасливий, *радісний -> correct as is)"
    items: 6
connects_to:
  - "b1-008 (alternation-vowels — vowel alternation as morphophonemic process)"
  - "b1-009 (alternation-consonants-nouns — consonant alternation for comparison)"
  - "b1-010 (alternation-consonants-verbs — consonant changes in verbs)"
  - "b1-012 (noun-subclasses-masculine — applying morphophonemic knowledge)"
prerequisites:
  - "A2 completion (learner can form basic adjectives and read consonant clusters)"
  - "b1-001 (metalanguage-phonetics — приголосний, група приголосних)"
grammar:
  - "Спрощення закріплене на письмі: [ждн]->[жн], [здн]->[зн], [стл]->[сл], [стн]->[сн],
    [скн]->[сн], [слн]->[сн]"
  - "Винятки: пестливий, хвастливий, кістлявий (no simplification)"
  - "Спрощення у вимові, але не на письмі: шістнадцять, зап'ястний, контрастний"
  - "Distinction between спрощення (sound drops) and чергування (sound changes)"
  - "Application across parts of speech: nouns, adjectives, verbs"
register: академічний
references:
  - title: "Заболотний Grade 5, p.109-112"
    notes: "Спрощення в групах приголосних (section 26): complete table, exceptions
      (пестливий, хвастливий, кістлявий), written-only cases."
  - title: "Литвінова Grade 5, p.180-183"
    notes: "Спрощення в групах приголосних: visual demonstration with проїЗДНий, tables
      of закріплені and незакріплені simplifications."
  - title: "Авраменко Grade 5, p.109"
    notes: "Спрощення в групах приголосних: орфограма presentation, невістці/шістсот
      exceptions, exercises."
  - title: "Голуб Grade 5, p.93"
    notes: "Спрощення як засіб милозвучності: conceptual framing, table-based rule
      formulation exercise."

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Skim these for content ideas. Reference specific examples you plan to use.

<knowledge_packet>
# Verified Knowledge Packet: Спрощення приголосних
**Module:** simplification-consonants | **Phase:** B1.1 [Baselines & Morphophonemics]
**Textbook grades searched:** 1, 2, 3, 5

---

## Що таке спрощення?

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 180
> **Score:** 0.50
>
> 180
> Фонетика. Графіка. Орфоепія. Орфографія. Спрощення в групах приголосних
> Спрощення в  групах приголосних
> Вправа 296
> 1 Розгляньте схему .
> проїЗД + Н = проїЗДНий = проїзний
> 2. Спробуйте вимовити слово проїзний, додавши між звуками [з] і  [н] ще 
> й  звук [д] . А  тепер вимовте слово правильно . Що ви відчували в  обох 
> випадках?
> 3. Висловте припущення: чому під час утворення слова проїзний випав 
> звук [д]?
> Д
> Одним із засобів милозвучності української мови є спрощення 
> приголосних .
> Якщо в процесі творення чи зміни слів виникають складні для 
> вимови сполучення приголосних, однин із  них випадає, відбува-
> ється спрощення .
> Цей процес може відбуватися як на  рівні усного мовлення, 
> тобто спрощується лише звук, так і  бути закріпленим на  письмі, 
> тобто не  пишемо відповідну літеру .

> **Source:** golub, Grade 5
> **Section:** Сторінка 93
> **Score:** 0.33
>
> 93
> 234   Як ви розумієте значення слова «спрощення»? Доберіть до нього 
> спільнокореневі слова. Доберіть за зразком і запишіть пару до 
> кожного з дібраних слів, визначте, які приголосні випадають 
> у  вказаних групах приголосних. Чи можна вважати спрощення 
> засобом милозвучності? Чому?
> Зразок. Тиждень — тижневий; ждн — жн. 
> Виїздити, область, щастя, проїзд, тріск, ненависть. 
> 235   Розгляньте таблицю. Сформулюйте за її змістом правила спро-
> щення в українській мові.

## Спрощення, закріплене на письмі

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 181
> **Score:** 0.50
>
> 181
> Фонетика. Графіка. Орфоепія. Орфографія. Спрощення в групах приголосних
> Закріплені на  письмі спрощення: 
> Спрощення
> Приклади
> ж(д)н
> тиждень — тижневий
> з(д)н
> проїзд — проїзний
> с(т)н
> користь — корисний
> с(т)л
> лестощі — улесливий
> з(к)н
> бризки — бризнути
> с(к)н
> писк — писнути
> с(л)н
> масло — масний
> Спрощення, не  закріплені на  письмі (які відбуваються лише 
> в  усному мовленні), маємо:
> z
> z у винятках зап’ястний, кістлявий, пестливий, хвастли-
> вий, хвастнути, хворостняк, шістнадцять, випускний, 
> вискнути;
> z
> z у словах іншомовного походження, наприклад: 
> контрастний,  баластний, абстрактний.
> д)
> (д
> (д)
> д
> д)
> (д
> (д)
> д
> т)
> (т(т)т
> т)
> (т(т)т
> к)
> (к(к)к
> к)
> (к(к)к
> л)
> (л(л)л
> Вправа 297
> Вставте пропущені літери, де це потрібно .

> **Source:** golub, Grade 5
> **Section:** Сторінка 93
> **Score:** 0.25
>
> 93
> 234   Як ви розумієте значення слова «спрощення»? Доберіть до нього 
> спільнокореневі слова. Доберіть за зразком і запишіть пару до 
> кожного з дібраних слів, визначте, які приголосні випадають 
> у  вказаних групах приголосних. Чи можна вважати спрощення 
> засобом милозвучності? Чому?
> Зразок. Тиждень — тижневий; ждн — жн. 
> Виїздити, область, щастя, проїзд, тріск, ненависть. 
> 235   Розгляньте таблицю. Сформулюйте за її змістом правила спро-
> щення в українській мові.

## Винятки: спрощення у вимові, але не на письмі

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 113
> **Score:** 0.50
>
> 110
> Спрощений у вимові приголосний, як правило, не пи­
> шемо.
> Групи, у яких  
> відбувається спрощення
> Приклади
> [ждн] → [жн]
> [здн] → [зн]
> [стл] → [сл]
> [стн] → [сн]
> тиждень – тижневий
> проїзд – проїзний
> щастя – щасливий
> радість – радісний
> В И Н Я Т К И
> 1. Не відбувається 
> спрощення в  
> таких словах: 
> пестливий, хвастливий,  
> кістлявий
> _____
> ! У цих словах вимовляємо [стл]
> 2. Спрощення у  
> вимові відбувається, 
> проте букву т  
> пишемо в таких 
> словах: 
> шістнадцять, зап’ястний, 
> контрастний, баластний,  
> компостний, аванпостний,  
> форпостний
> _____
> ! У цих словах вимовляємо [сн]
> ОРФОГРАМА
> Спрощення в групах приголосних
> 268.	І. Замініть подані словосполучення на синонімічні з прикметником 
> (за зразком). Утворені словосполучення вимовте й запишіть. Позначте 
> орфограму.
> ЗРАЗОК.

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 181
> **Score:** 0.33
>
> 181
> Фонетика. Графіка. Орфоепія. Орфографія. Спрощення в групах приголосних
> Закріплені на  письмі спрощення: 
> Спрощення
> Приклади
> ж(д)н
> тиждень — тижневий
> з(д)н
> проїзд — проїзний
> с(т)н
> користь — корисний
> с(т)л
> лестощі — улесливий
> з(к)н
> бризки — бризнути
> с(к)н
> писк — писнути
> с(л)н
> масло — масний
> Спрощення, не  закріплені на  письмі (які відбуваються лише 
> в  усному мовленні), маємо:
> z
> z у винятках зап’ястний, кістлявий, пестливий, хвастли-
> вий, хвастнути, хворостняк, шістнадцять, випускний, 
> вискнути;
> z
> z у словах іншомовного походження, наприклад: 
> контрастний,  баластний, абстрактний.
> д)
> (д
> (д)
> д
> д)
> (д
> (д)
> д
> т)
> (т(т)т
> т)
> (т(т)т
> к)
> (к(к)к
> к)
> (к(к)к
> л)
> (л(л)л
> Вправа 297
> Вставте пропущені літери, де це потрібно .

## Спрощення [сонце], [серце] та інші особливі випадки

> **Source:** vashulenko, Grade 2
> **Section:** Сторінка 39
> **Score:** 0.50
>
> тттг
> розподіляю 
> пояснюю .
> Наведи свої 
> приклади.
> Г
> Чому берези 
> сумували?
> ? значення
> ? значення
> солодкий цукор 
> глибока криниця 
> м'яка тканина 
> сяє сонце 
> ллється вода
> солодкий сон 
> глибока думка 
> м’який характер 
> сяє обличчя 
> ллється музика
> Г
> 2| Випиши слова, ужиті в переносному значенні.
> Прийшла до беріз осінь. Принесла 
> їм золотисті стрічки. Вплела їх берізкам 
> у зелені коси.
> Вийшло із-за хмар сонце. Подивилося воно на 
> берези і не впізнало їх: у зелених косах — золотисті 
> стрічки. Сміється сонечко, а берези сумують... 
> (За Василем Сухомлинським).
> 3[ Випиши сполучення слів, у яких слова вживаються у прямому
> і переносному значеннях. Поясни значення слів.
> У кришталевій воді сонце купається. 
> Кришталева люстра прикрашає музей. 
> Кришталевою росою земля вмилася.

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 277
> **Score:** 0.25
>
> 277
> Складні випадки наголошування
> здалека
> зобрази ти
> зо зла
> зрання
> зру чний
> К
> камбала
> катало г
> ки шка
> кінчи ти
> ко лесо
> ко лія
> кори сний
> ко сий
> котри й
> кро їти
> кропива
> кулінарія
> ку рятина
> Л
> лате
> листопад
> лю стро
> М
> мабу ть
> мере жа
> Н
> навчання
> нанести 
> напі й
> начинка
> ненавидіти
> ненависний
> ненависть
> нести 
> ні здря
> нови й
> О
> обіця нка
> обрання
> обру ч (іменник)
> одинадцять
> одноразо вий
> ознака
> о лень
> отаман
> о цет
> П
> пави ч
> пе карський
> перевезти 
> перевести 
> переля к
> перенести 
> пере пад
> піце рія
> по друга
> по значка
> по ми лка
> помо вчати
> поня ття
> посере дині
> привезти 
> привести 
> при морозок
> принести 
> промі жок

> **Source:** kravtsova, Grade 3
> **Section:** Сторінка 44
> **Score:** 0.33
>
> 44
> 2.	 Добери з поданих заголовків найбільш вдалий. Поясни вибір.
> 	 Щедрий Ведмідь і вдячна Мишка.
> 	 Милосердний Ведмідь і вдячна Мишка.
> 	 Справжні друзі. 
> 124.	 Вправа 
> «Квест».
> 4 5
> 5 6 7
> 1 2 5
> диреѳктор
> 3.	 Запишіть свої розповіді на окремих аркушах. На їх основі 
> створіть книжку.
> 123.	 1.	 Пригадай ситуацію, коли:
> 	 ти проявив / проявила милосердя; 
> 	 до тебе проявили милосердя;
> 	 ти був вдячним / вдячною;
> 	 тобі були вдячні за послугу.
> СЛОВА З ПРЕФІКСАМИ РОЗ-, БЕЗ-
> 1.	 Прочитай текст. Як ти гадаєш, чи потрібні професії модельєра, 
> дизайнера? Доведи свою думку.
> Чимало людей хочуть бути стильними і модними. Як цього 
> досягти?
> — Безкрає море творчості та новизни живе в кожному з 
> нас. Тут не можна бути безвідповідальним і безмовним.

## Спрощення у дієслівних формах та прикметниках

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 181
> **Score:** 0.33
>
> 181
> Фонетика. Графіка. Орфоепія. Орфографія. Спрощення в 

... (truncated for context window)
</knowledge_packet>

---

## Output format

Output a single `<skeleton>` block. For each section from the plan's `content_outline`, list every paragraph and exercise with its word budget and content focus.

Be SPECIFIC about what each paragraph covers — not "explain grammar" but "explain accusative case endings for feminine nouns (-у/-ю), with 3 examples: книгу, каву, землю."

```
<skeleton>
## Section Title (~XXX words total)
- P1 (~XX words): [specific content — what concept, what examples, what comparison]
- P2 (~XX words): [specific content]
- Exercise: [type from activity_hints, focus, number of items]
- P3 (~XX words): [specific content]
...

## Section Title (~XXX words total)
- P1 (~XX words): [specific content]
...

## Підсумок — Summary (~150 words)
- P1 (~150 words): [Follow the plan's points for this section EXACTLY. If the plan says "Self-check questions", output a bulleted Q&A list — NOT prose. If the plan says "recap", write a brief recap.]

Grand total: ~4000 words
</skeleton>
```

## Rules

1. **Every paragraph has ONE clear purpose.** If you can't describe it in one sentence, split it.
2. **Word budgets must sum to 4000+.** Aim for ~10% overshoot (4400 words) — writers tend to undershoot.
3. **Section budgets must match the plan's `content_outline` word allocations** (±10%).
4. **Place exercises in the correct section.** Each activity hint in the plan may have a `section:` field that tells you which section it belongs in. Place that exercise AFTER the teaching content of that section, never before. If no `section:` is specified, place the exercise after the most relevant teaching point. **CRITICAL: An exercise must ONLY test concepts already taught above it. Never test a concept from a later section.**
5. **Name specific Ukrainian examples** you plan to use in each paragraph. This prevents vague skeletons that produce vague content.
6. **Dialogues count as paragraphs.** Budget 80-120 words per multi-turn dialogue.
7. **No meta-commentary.** Output only the `<skeleton>` block, nothing else.
