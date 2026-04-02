<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Skeleton Prompt — Module Structure Planning

You are planning the detailed paragraph-level structure of a Ukrainian language module. Do NOT write the full content — only plan the structure.

## Your task

Create a detailed paragraph-level skeleton for module **8: Чергування голосних** (B1, B1.2 [Morphophonemics & Noun Subclasses]).

**Word target: 4000 words** of prose. Your skeleton must budget every word.

---

## Plan

<plan_content>
module: b1-008
level: B1
sequence: 8
slug: alternation-vowels
version: '3.0'
title: "Чергування голосних"
subtitle: "Коли о та е стають i — і коли зникають зовсім"
focus: grammar
pedagogy: PPP
phase: "B1.2 [Morphophonemics & Noun Subclasses]"
word_target: 4000
objectives:
- "Learner can predict when [о] or [е] in a root will become [i]
  in a different word form, using the open/closed syllable rule
  (рік — року, сіль — солі, двір — двори)"
- "Learner can identify and produce the [о]/[е] to zero alternation
  in noun and adjective paradigms (учень — учня, вітер — вітру,
  день — дня)"
- "Learner can explain the connection between наголос shift
  and vowel alternation in verb pairs (летіти — літати,
  нести — ніс)"
- "Learner can apply these rules to spell unfamiliar words correctly,
  recognizing that the alternation is a defining feature of Ukrainian
  phonology that distinguishes it from other Slavic languages"
dialogue_situations:
- setting: 'A Ukrainian teacher explaining to students why certain words change their
    vowels — using examples from a grocery list: Я купив коня (m, horse), але: коні
    (pl). Вона живе в селі (n), але: село. Він поставив стіл (m), але: на столі.'
  speakers:
  - Вчитель
  - Студенти
  motivation: 'Vowel alternation о/е→і: кінь→коня, село→селі, стіл→столі'
content_outline:
- section: "Що таке чергування голосних?"
  words: 550
  points:
  - "Bridge from M01 (metalanguage-phonetics): learners already know
    голосний, приголосний, наголос, відкритий/закритий склад.
    This module shows how these concepts drive systematic spelling changes.
    Key definition from Авраменко Grade 5 p.111:
    'Iноді, коли утворюємо нове слово або його форму, звук може
    змінюватися на інший: сіль — соляний, солі; корінь — кореня.
    Це мовне явище називають чергуванням звуків.'"
  - "Why this matters: чергування голосних is a defining feature of
    Ukrainian that distinguishes it from Russian and Polish.
    Glazova Grade 10 p.103: 'Таке чергування характерне для
    української мови й вирізняє її серед інших східнослов'янських мов.'
    Learners who master this rule unlock correct spelling of thousands
    of Ukrainian words."
  - "Overview of the three main types covered in this module:
    1. [о], [е] чергуються з [i] (the open/closed syllable rule)
    2. [о], [е] чергуються з нулем звука (fleeting vowels)
    3. [о] чергується з [е] after шиплячі та [й]
    Each type has its own logic; this section previews all three."
- section: "Чергування [о], [е] з [i]"
  words: 900
  points:
  - "The core rule from Заболотний Grade 5 p.113-114:
    When a syllable changes from open to closed (or vice versa),
    [о] or [е] in the root may alternate with [i].
    Open syllable (ends in vowel): дво-ри, ко-ні, ро-ку.
    Closed syllable (ends in consonant): двір, кінь, рік.
    Pattern: [о]/[е] in open syllable <-> [i] in closed syllable."
  - "Systematic examples organized by part of speech:
    Nouns: стіл — столу, двір — двору, сіль — солі,
    віз — воза, ніс — носа, рік — року, річ — речі.
    Adjectives: осінній — осени, вечірній — вечора.
    Verbs: несті — ніс, везті — віз.
    Glazova Grade 10 p.103: 'шко-ла — шкіл; дво-ри — двір;
    по-со-ли — сіль; у мо[йе]му — у мо[йі]м.'"
  - "Exceptions and special cases:
    Not every closed syllable triggers the change.
    Borrowed words typically do not alternate: мотор — мотору
    (not *мотіру). Some native words have fossilized forms.
    Practice: learners predict the nominative from an oblique case form
    and vice versa."
  - "Reading practice: short passage using words with [о]/[е] ~ [i]
    alternation in natural context (e.g., describing a Ukrainian village:
    двір, стіл, піч, вікна, ріг, etc.). Learners identify all
    alternating pairs in the text."
- section: "Чергування [о], [е] з нулем звука"
  words: 650
  points:
  - "Definition from Заболотний Grade 5 p.114:
    In some words, [о] or [е] disappears entirely when the word form
    changes. This is called 'чергування з нулем звука' or 'біглі
    голосні'. The vowel is present in one form but absent in another."
  - "Common patterns:
    Masculine nouns: учень — учня, день — дня, вітер — вітру,
    камінь — каменя, хлопець — хлопця, пень — пня.
    The vowel [е] or [о] in the last syllable of the nominative
    disappears in oblique cases when the ending is added.
    Suffixes: -ець/-ця (молодець — молодця),
    -ок/-ка (замок — замка, гурток — гуртка),
    -ень/-ня (корінь — кореня)."
  - "How to recognize fleeting vowels vs. stable vowels:
    If removing the vowel creates an impossible consonant cluster,
    the vowel may be stable (but not always — Ukrainian tolerates
    clusters like -дня, -тру). Practice with minimal pairs:
    сон — сну (fleeting) vs. стон — стону (stable)."
- section: "Чергування [о] з [е] після шиплячих та [й]"
  words: 550
  points:
  - "Rule from Заболотний Grade 7 p.56:
    After [ж], [ч], [ш], [дж], [й]:
    — write е before м'який приголосний or before syllables with [е], [и]:
    вечеря, вишень, джерело, женити.
    — write о before твердий приголосний or before syllables with [а], [о], [у]:
    бджола, будиночок, пшоно, знайомий."
  - "Exceptions to memorize: чепурний, шепіт, жебоніти, щедрий,
    черствий, чекати (е despite the rule), and чоло, бджола (о despite
    the rule). These are listed explicitly in Заболотний Grade 7 p.56."
  - "Practice: learners apply the rule to fill in missing letters
    in words after шиплячі. Contrast with Russian where this distinction
    does not exist — Ukrainian learners must develop sensitivity to
    the following consonant's hardness/softness."
- section: "Чергування голосних у дієслівних коренях"
  words: 550
  points:
  - "From Заболотний Grade 5 p.113, вправа 275:
    Verb root alternations driven by stress and suffix:
    летіти — літати, котити — катати, терти — стирати.
    Pattern: [е] ~ [i] ~ [и] depending on stress position and
    suffix (-а-, -и-, -іти-)."
  - "Extended examples from Заболотний Grade 5 p.114, вправа 276:
    захопити — хапати ([о] ~ [а]),
    сплести — сплітати ([е] ~ [i]),
    завмерти — завмирати ([е] ~ [и]),
    заберу — забирати ([е] ~ [и]).
    The alternation is predictable: before stressed -а- suffix,
    the root vowel changes."
  - "Connecting to A2 knowledge: learners already know these verbs
    from everyday use. Now they see the system. This transforms
    memorized pairs into a productive rule."
- section: "Чергування i наголос: як вони пов'язані"
  words: 500
  points:
  - "Key insight: наголос (stress) drives many vowel alternations.
    When stress shifts away from a root vowel, the vowel may change:
    рік (stress on [i]) — років (stress on [i] in suffix, root has [о]).
    Авраменко Grade 5 p.111: the alternation often reveals
    the original vowel that existed before the shift to [i]."
  - "Practice: given a word with [i] in a closed syllable,
    learners find the form with [о] or [е] by changing the word form.
    This is exactly the spelling strategy taught in Ukrainian schools:
    Литвінова Grade 5 p.118: 'Якщо під час зміни слова сумнівний
    звук чергується з [i] в закритому складі — пишемо и: осені (бо
    осінь).'"
  - "Summary table: all three alternation types with examples,
    triggers, and exceptions — a reference card learners can use."
- section: "Підсумок: правила i практика"
  words: 300
  points:
  - "Complete alternation summary with decision flowchart:
    Step 1: Is the syllable open or closed? -> [о]/[е] ~ [i]
    Step 2: Does the vowel disappear? -> fleeting vowel
    Step 3: Is it after a шиплячий? -> [о] ~ [е] rule
    Step 4: Is it a verb root with suffix change? -> verb alternation."
  - "Self-check in Ukrainian: Дайте відповіді на запитання:
    1. Чому в слові 'двір' пишемо i, а в слові 'двори' — о?
    2. Яке чергування відбувається у словах 'день — дня'?
    3. Після яких приголосних чергуються [о] з [е]?
    4. Запишіть три пари слів із чергуванням [о] ~ [i]."
  - "Preview of next module: Чергування приголосних (іменники) —
    consonant alternations in noun paradigms, building on the same
    morphophonemic logic."
vocabulary_hints:
  required:
  - "чергування (alternation — systematic sound change between word forms)"
  - "голосний (vowel — sound produced without obstruction)"
  - "відкритий склад (open syllable — ending in a vowel sound)"
  - "закритий склад (closed syllable — ending in a consonant sound)"
  - "корінь (root — the core meaning-bearing part of a word)"
  - "наголос (stress — emphasized pronunciation of a syllable)"
  - "біглий голосний (fleeting vowel — vowel that disappears in some forms)"
  - "нуль звука (zero sound — absence of a vowel in an alternation)"
  - "суфікс (suffix — morpheme added after the root)"
  - "закінчення (ending — inflectional morpheme at the end of a word)"
  - "шиплячий (hushing consonant — ж, ч, ш, дж)"
  - "орфограма (orthographic rule — a spelling pattern requiring a rule)"
  - "відмінок (grammatical case)"
  - "форма слова (word form — a specific inflected variant of a word)"
  recommended:
  - "милозвучність (euphony — pleasant sound quality of speech)"
  - "ненаголошений (unstressed — syllable without stress)"
  - "відкритий (open — ending in a vowel)"
  - "закритий (closed — ending in a consonant)"
  - "морфонологія (morphophonology — study of sound alternations in morphology)"
  - "твердий (hard — non-palatalized consonant)"
  - "м'який (soft — palatalized consonant)"
  - "спільнокореневий (cognate — sharing the same root)"
  - "правопис (orthography — correct spelling rules)"
  - "перевірне слово (checking word — word used to verify spelling)"
activity_hints:
- type: quiz
  focus: "Identify which vowel alternation type is present in word pairs
    (e.g., рік-року = [о]~[i]; день-дня = fleeting vowel)"
  items: 8
- type: fill-in
  focus: "Complete word forms by applying the open/closed syllable rule
    (e.g., двір — двор___, стіл — стол___)"
  items: 8
- type: match-up
  focus: "Match nominative forms with their oblique case counterparts
    (e.g., рік <-> року, кінь <-> коня, день <-> дня)"
  items: 8
- type: group-sort
  focus: "Sort word pairs into categories: [о]~[i] alternation,
    [е]~[i] alternation, fleeting vowel, no alternation"
  items: 10
- type: error-correction
  focus: "Find and fix vowel spelling errors in sentences caused by
    incorrect application of alternation rules"
  items: 6
connects_to:
- "b1-001 (metalanguage-phonetics — foundation: наголос, склад, голосний)"
- "b1-009 (alternation-consonants-nouns — consonant alternations in nouns)"
- "b1-011 (simplification-consonants — another morphophonemic process)"
prerequisites:
- "A2 completion (learner knows basic noun declension and verb conjugation)"
- "b1-001 (metalanguage-phonetics — наголос, відкритий/закритий склад)"
grammar:
- "Чергування [о], [е] з [i] — the open/closed syllable rule"
- "Чергування [о], [е] з нулем звука — fleeting vowels (біглі голосні)"
- "Чергування [о] з [е] after шиплячі та [й]"
- "Vowel alternations in verb roots driven by stress and suffix"
- "Connection between наголос shift and vowel alternation"
- "Spelling verification strategy: finding the перевірне слово"
register: академічний
references:
- title: "Авраменко Grade 5, p.111-113"
  notes: "Core чергування голосних chapter: definition, examples with
    сіль-соляний, корінь-кореня, systematic presentation of patterns."
- title: "Заболотний Grade 5, p.113-115"
  notes: "Чергування голосних звуків (section 27): verb pairs
    летіти-літати, practice exercises with open/closed syllable analysis."
- title: "Литвінова Grade 5, p.118"
  notes: "Правопис ненаголошених [е] та [и]: verification strategy
    using word form changes, connection to чергування з [i]."
- title: "Глазова Grade 10, p.103"
  notes: "Mature presentation: [о],[е]~[i] as a defining feature of
    Ukrainian, systematic examples шко-ла — шкіл, дво-ри — двір."
- title: "Заболотний Grade 7, p.55-56"
  notes: "Чергування [о] з [е] після шиплячих: rule formulation,
    exceptions, practice exercises."

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Skim these for content ideas. Reference specific examples you plan to use.

<knowledge_packet>
# Verified Knowledge Packet: Чергування голосних
**Module:** alternation-vowels | **Phase:** B1.2 [Morphophonemics & Noun Subclasses]
**Textbook grades searched:** 1, 2, 3, 5

---

## Що таке чергування голосних?

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 116
> **Score:** 0.50
>
> 113
> 27. ЧЕРГУВАННЯ ГОЛОСНИХ ЗВУКІВ
> Про те, як під час творення слів чи зміни форми слів  
> замість одного голосного з’являється інший
> ПРИГАДАЙМО. 1. Що таке суфікс слова? 2. Який склад називають від-
> критим? 
> 275.	А.  Прочитайте пари дієслів. 
> лет¾ти – літати    терти – стирати    котити – катати
> Б.  Якими звуками різняться корені слів у кожній парі?
> В.  Простежте, чи залежить чергування в цих словах від місця наго­
> лосу та суфікса.
> Іноді під час творення слова чи зміни його форми замість 
> одного звука з’являється інший. НАПРИКЛАД: друг – дружити; 
> стіл – стола. Таку зміну звуків називають чергуванням.
> В українській мові можливі чергування і голосних, і 
> приголосних звуків.
> Звуки, які 
> чергуємо
> Приклади 
> [о] – [і]
> [е] – [і]
> кінь – коня, вільний – воля, колесо – коліс 
> Примітка.

> **Source:** avramenko, Grade 5
> **Section:** Сторінка 111
> **Score:** 0.33
>
> 111
>  § 48–49.  Чергування  голосних  звуків
> 1.	Прочитайте речення та виконайте завдання.
> Кінь міг літати.
> Коні можуть летіти.
> А. Простежте за голосними в коренях слів.
> Б. Чи помітили ви якусь закономірність?
> § 48–49.  ЧЕРГУВАННЯ  ГОЛОСНИХ  ЗВУКІВ
> Іноді, коли утворюємо нове слово або його форму, звук може змінюва-
> тися на інший: сіль — соляний, солі; корінь — кореня.

> **Source:** avramenko, Grade 5
> **Section:** Сторінка 115
> **Score:** 0.25
>
> 115
>  § 50.  Чергування  приголосних  звуків
> 3. Прочитайте вислови та виконайте завдання.
> 1. Що на (думка), те й на (язик). 2. Терпи, (козак), отаманом будеш. 
> 3. Живемо, як горох при (дорога): хто не йде, той скубне. 4. Не шукай гри-
> бів у ведмежому (барліг). 5. Коли не знаєш дороги, не (виїхати) із дому 
> (Нар. тв.). 
> А. Перепишіть речення, ставлячи в потрібну форму слова, що в дужках. 
> Б. Підкресліть букви, що позначають звуки, які чергуються.

## Чергування [о], [е] з [i]

> **Source:** kravcova, Grade 2
> **Section:** Сторінка 45
> **Score:** 0.25
>
> 45
> На подвір’ячку, під в’язом,
> вся зібралася сім’я:
> відпочить, побути разом
> та послухать солов’я.
> 	
> 	
> 	
> Надія Красоткіна
> 2.	 Випиши слова, у яких є апостроф.
> 163. 1.	 Користуючись словами для довідки, доповни речення.
> 1.  Тіло риб покриває луска, а тіло птахів — ...  . 
> 2. В’юн — риба, а м’ята — ... . 3. Пір’їна легка, а камінь ... . 
> 4. Найбільше багатство — ... . 5. Тато, мама і я — дружна ... . 
> 6. П’ятий день тижня — ... .
> Слова для довідки: п’ятниця, здоров’я, рослина, пір’я, 
> важкий, сім’я. 
> 2. Спиши відновлені речення.
> 164. 1.	 Прочитай вірш. Як ти гадаєш, про що говоритиме сім’я?
> 165. 1.	 За допомогою алфавіту утвори слово. Підказка: записуй 
> букви в тому порядку, що й числа.
> 15
> 1
> 17
> ’
> 33
> 18
> 11
> 14
> 2.	 Пригадай, коли ми ставимо апостроф. 
> Крок 1.

## Чергування [о], [е] з нулем звука

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 120
> **Score:** 0.33
>
> 117
> 284.	Доберіть до поданих слів їхні форми або спільнокореневі слова із 
> чергуванням приголосних. Запишіть слова групами. Вимовте звуки, які 
> чергуємо, та підкресліть букви на позначення 
> цих звуків.
> ЗРАЗОК. Книга – книзі, книжечка. 
> Забігати – забіжу.
> Берег, перемога, серветка, горох, 
> тихо, заходити, їздити­. 
> 285.	ЧОМУ ТАК? Поясніть, чому подані в парах слова вважаємо спіль-
> нокореневими, хоча в їхніх коренях немає спільних звуків.
> 1. Річний – у році. 2. Нога – ніжка.
> 286.	Простежте, чи відбувається чергування голосних або приголос­
> них звуків під час зміни форми назви вашого населеного пункту, мікро-
> району, вулиці, назви річки, озера тощо у вашій місцевості. Поділіться 
> своїми спостереженнями. 
> 287.	І. Прочитайте гумореску Грицька Бойка.

## Чергування [о] з [е] після шиплячих та [й]

> **Source:** bolshakova, Grade 2
> **Section:** Сторінка 48
> **Score:** 0.50
>
> 48
> ПЕрЕнос сЛІв З ь І ьо
> Прочитай слова. До якого слова немає малюнка? Чим схожі 
> слова? Чим відрізняються? Спиши. Познач м’які приголосні 
> звуки знаком 
> .  
> галка — галька 
> лан — лань
> мілка — мі лька
> Спиши. Відшукай слова зі знаком м’якшення. Познач м’який 
> приголосний перед знаком м’якшення знаком 
> .
> У метелика біленькі крильця. Василько сів на маленький 
> стільчик. Вітерець підняв легеньку пір’їнку. Сіренький заєць 
> їсть морквинку.  
> Не відривай букву ь від попередньої букви, 
> коли переносиш слово з рядка в рядок. 
> Наприклад: кіль-це, паль-ці, апель-син.
> Поділи слова для переносу.
> Зразок. Кіль-це, … .
> Зразок.

> **Source:** bolshakova, Grade 1
> **Section:** Сторінка 41
> **Score:** 0.25
>
> 41
> Знайди слово до схеми.
> 	
> щука	
> дощик	
> щастя	
> щедро
> 	
> щавель	
> кущик	
> щасливий	
> щедрість
> 	 щебетати	
> плащик	
> щастить	
> щедрий
> 
> Вірш. Рима
> ЯК ЖУРАВЕЛЬ ЗБИРАВ ЩАВЕЛЬ 
> На болоті журавель
> Цілий день збирав щавель.
> Назбирав собі на борщ,
> Та якраз впе-рі-щив дощ,
> І щавель знесла водиця, —
> Без борщу лишилась птиця.
> З того часу журавель
> Сировим жує щавель.
> 	
> Михайло Стельмах
> 
> Скоромовка
> Борщик у горщику,
> Щавель у борщику.
> А до борщу — 
> Ще й по лящу.
> 1
> 2
> 3
> Щ щ
> 	
> ща	
> що	
> щу	
> щи
> 	
> щі	
> ще	
> ащ	
> ощ
> 	
> ущ	
> ищ	
> іщ	
> ещ

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 177
> **Score:** 0.50
>
> 177
> Фонетика. Графіка. Орфоепія. Орфографія. Милозвучність української мови
> Чергування прийменників З — ЗІ — ІЗ
> З
> ІЗ
> ЗІ
> перед словом, яке почи-
> нається з  голосного:
> з однокласницями;
> з Одеси
> між приголосними:
> Максим 
> із Семеном 
> перед словом, 
> яке починається 
> сполученням 
> приголосних 
> (особливо 
> з  початковими 
> літерами 
> з, с, ш, щ):
> зі мною; 
> зі святом;
> зі швидкістю
> перед словом, яке почи-
> нається з  приголосного 
> (крім свистячих і  ши-
> плячих), якщо утворена 
> сполука є  нескладною 
> для вимови:
> з нагоди святкування
> після голосного 
> перед  наступними 
> свистячими і  ши-
> плячими (літери з, 
> ц, с, ч, ш, щ):
> із цими 
> новинами
> Вправа 290
> 1.

## Чергування голосних у дієслівних коренях

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 116
> **Score:** 0.33
>
> 113
> 27. ЧЕРГУВАННЯ ГОЛОСНИХ ЗВУКІВ
> Про те, як під час творення слів чи зміни форми слів  
> замість одного голосного з’являється інший
> ПРИГАДАЙМО. 1. Що таке суфікс слова? 2. Який склад називають від-
> критим? 
> 275.	А.  Прочитайте пари дієслів. 
> лет¾ти – літати    терти – стирати    котити – катати
> Б.  Якими звуками різняться корені слів у кожній парі?
> В.  Простежте, чи залежить чергування в цих словах від місця наго­
> лосу та суфікса.
> Іноді під час творення слова чи зміни його форми замість 
> одного звука з’являється інший. НАПРИКЛАД: друг – дружити; 
> стіл – стола. Таку зміну звуків називають чергуванням.
> В українській мові можливі чергування і голосних, і 
> приголосних звуків.
> Звуки, які 
> чергуємо
> Приклади 
> [о] – [і]
> [е] – [і]
> кінь – коня, вільний – воля, колесо – коліс 
> Примітка.

> **Source:** avramenko, Grade 5
> **Section:** Сторінка 111
> **Score:** 0.50
>
> 111
>  § 48–49.  Чергування  голосних  звуків
> 1.	Прочитайте речення та виконайте завдання.
> Кінь міг літати.
> Коні можуть летіти.
> А. Простежте за голосними в коренях слів.
> Б. Чи помітили ви якусь закономірність?
> § 48–49.  ЧЕРГУВАННЯ  ГОЛОСНИХ  ЗВУКІВ
> Іноді, коли утворюємо нове слово або його форму, звук може змінюва-
> тися на інший: сіль — соляний, солі; корінь — кореня.

## Чергування i наголос: як вони пов'язані

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 120
> **Score:** 0.33
>
> 117
> 284.	Доберіть до поданих слів їхні форми або спільнокореневі слова із 
> чергуванням приголосних. Запишіть слова групами. Вимовте звук

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
