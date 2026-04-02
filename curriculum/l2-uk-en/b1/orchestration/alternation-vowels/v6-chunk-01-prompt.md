<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Missing section heading: 'Чергування і наголос: як вони пов'язані'
- FIX: Missing section heading: 'Підсумок: правила і практика'
- FIX: Russian characters found: ё
- NOTE: Missing 1/14 required vocab: орфограма (orthographic rule — a spelling pattern requiring a rule)
- NOTE: Plan expects 5 exercise(s) but content has 0 placeholders
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

# Section-by-Section Generation — Section 1/7

You are writing ONE SECTION of a Ukrainian language module. Write ONLY this section — nothing else.

**Module:** 4: Чергування голосних (B1, B1.1 [Baselines & Morphophonemics])
**Section to write:** Що таке чергування голосних? (~600 words total)
**Word target for this section:** 600 words (aim for 660 to account for undershoot)

---

## Section Skeleton (follow this exactly)

## Що таке чергування голосних? (~600 words total)
- P1 (~120 words): [Introduction connecting back to B1-M01. Recall the basic phonetics: vowels (голосні), consonants (приголосні), and the architecture of syllables (відкритий/закритий склад). Define 'чергування' as a systematic replacement of one sound with another during word formation or inflection, using the foundational example from Avramenko: сіль — солі, кінь — коня.]
- P2 (~130 words): [Linguistic context: Why this matters. Explain that vowel alternation is the 'DNA' of the Ukrainian language, distinguishing it from Russian and Polish. Use Glazova’s insight that this is a defining feature of the language's melody (милозвучність). Explain that for a learner, mastering this isn't just about 'rules' but about unlocking the ability to recognize roots across different cases.]
- P3 (~120 words): [Dialogue: Вчитель та Студенти. The teacher uses a grocery list to demonstrate. 'Я купив коня' (m, horse), but pointing at a field: 'Там коні' (pl). 'Він поставив стіл' (m), but 'Книжка на столі'. The students notice the o/i shift and ask why. Teacher introduces the concept of syllable 'breathing' (open vs closed).]
- P4 (~130 words): [Categorization: Preview the three main types covered in the module. 1. The O/E to I shift in closed syllables. 2. Fleeting vowels (біглі голосні) that vanish into thin air. 3. The O/E alternation after hushing consonants (шиплячі). Emphasize that each has a logic tied to the history of the language.]
- P5 (~100 words): [Motivation and Strategy. Explain that while these look like 'exceptions' to English speakers, they are the 'standard' in Ukrainian. Advise the learner to stop thinking of 'стіл' as the 'real' word and 'стола' as a 'change', but rather to see the root {ст-л-} as a flexible unit that adapts to its environment.]

---
## Full Plan (for reference)

<plan_content>
module: b1-004
level: B1
sequence: 4
slug: alternation-vowels
version: '3.0'
title: "Чергування голосних"
subtitle: "Коли о та е стають і — і коли зникають зовсім"
focus: grammar
pedagogy: PPP
phase: "B1.1 [Baselines & Morphophonemics]"
word_target: 4000
objectives:
  - "Learner can predict when [о] or [е] in a root will become [i] in a different
    word form, using the open/closed syllable rule (рік — року, сіль — солі, двір
    — двори)"
  - "Learner can identify and produce the [о]/[е] to zero alternation in noun and
    adjective paradigms (учень — учня, вітер — вітру, день — дня)"
  - "Learner can explain the connection between наголос shift and vowel alternation
    in verb pairs (летіти — літати, нести — ніс)"
  - "Learner can apply these rules to spell unfamiliar words correctly, recognizing
    that the alternation is a defining feature of Ukrainian phonology that distinguishes
    it from other Slavic languages"
dialogue_situations:
  - setting: 'A Ukrainian teacher explaining to students why certain words change
      their vowels — using examples from a grocery list: Я купив коня (m, horse),
      але: коні (pl). Вона живе в селі (n), але: село. Він поставив стіл (m), але:
      на столі.'
    speakers:
      - Вчитель
      - Студенти
    motivation: 'Vowel alternation о/е→і: кінь→коня, село→селі, стіл→столі'
content_outline:
  - section: "Що таке чергування голосних?"
    words: 550
    points:
      - "Bridge from M01 (metalanguage-phonetics): learners already know голосний,
        приголосний, наголос, відкритий/закритий склад. This module shows how these
        concepts drive systematic spelling changes. Key definition from Авраменко
        Grade 5 p.111: 'Iноді, коли утворюємо нове слово або його форму, звук може
        змінюватися на інший: сіль — соляний, солі; корінь — кореня. Це мовне явище
        називають чергуванням звуків.'"
      - "Why this matters: чергування голосних is a defining feature of Ukrainian
        that distinguishes it from Russian and Polish. Glazova Grade 10 p.103: 'Таке
        чергування характерне для української мови й вирізняє її серед інших східнослов'янських
        мов.' Learners who master this rule unlock correct spelling of thousands of
        Ukrainian words."
      - "Overview of the three main types covered in this module: 1. [о], [е] чергуються
        з [i] (the open/closed syllable rule) 2. [о], [е] чергуються з нулем звука
        (fleeting vowels) 3. [о] чергується з [е] after шиплячі та [й] Each type has
        its own logic; this section previews all three."
  - section: "Чергування [о], [е] з [i]"
    words: 900
    points:
      - "The core rule from Заболотний Grade 5 p.113-114: When a syllable changes
        from open to closed (or vice versa), [о] or [е] in the root may alternate
        with [i]. Open syllable (ends in vowel): дво-ри, ко-ні, ро-ку. Closed syllable
        (ends in consonant): двір, кінь, рік. Pattern: [о]/[е] in open syllable <->
        [i] in closed syllable."
      - "Systematic examples organized by part of speech: Nouns: стіл — столу, двір
        — двору, сіль — солі, віз — воза, ніс — носа, рік — року, річ — речі. Adjectives:
        осінній — осени, вечірній — вечора. Verbs: несті — ніс, везті — віз. Glazova
        Grade 10 p.103: 'шко-ла — шкіл; дво-ри — двір; по-со-ли — сіль; у мо[йе]му
        — у мо[йі]м.'"
      - "Exceptions and special cases: Not every closed syllable triggers the change.
        Borrowed words typically do not alternate: мотор — мотору (not *мотіру). Some
        native words have fossilized forms. Practice: learners predict the nominative
        from an oblique case form and vice versa."
      - "Reading practice: short passage using words with [о]/[е] ~ [i] alternation
        in natural context (e.g., describing a Ukrainian village: двір, стіл, піч,
        вікна, ріг, etc.). Learners identify all alternating pairs in the text."
  - section: "Чергування [о], [е] з нулем звука"
    words: 650
    points:
      - "Definition from Заболотний Grade 5 p.114: In some words, [о] or [е] disappears
        entirely when the word form changes. This is called 'чергування з нулем звука'
        or 'біглі голосні'. The vowel is present in one form but absent in another."
      - "Common patterns: Masculine nouns: учень — учня, день — дня, вітер — вітру,
        камінь — каменя, хлопець — хлопця, пень — пня. The vowel [е] or [о] in the
        last syllable of the nominative disappears in oblique cases when the ending
        is added. Suffixes: -ець/-ця (молодець — молодця), -ок/-ка (замок — замка,
        гурток — гуртка), -ень/-ня (корінь — кореня)."
      - "How to recognize fleeting vowels vs. stable vowels: If removing the vowel
        creates an impossible consonant cluster, the vowel may be stable (but not
        always — Ukrainian tolerates clusters like -дня, -тру). Practice with minimal
        pairs: сон — сну (fleeting) vs. стон — стону (stable)."
  - section: "Чергування [о] з [е] після шиплячих та [й]"
    words: 550
    points:
      - "Rule from Заболотний Grade 7 p.56: After [ж], [ч], [ш], [дж], [й]: — write
        е before м'який приголосний or before syllables with [е], [и]: вечеря, вишень,
        джерело, женити. — write о before твердий приголосний or before syllables
        with [а], [о], [у]: бджола, будиночок, пшоно, знайомий."
      - "Exceptions to memorize: чепурний, шепіт, жебоніти, щедрий, черствий, чекати
        (е despite the rule), and чоло, бджола (о despite the rule). These are listed
        explicitly in Заболотний Grade 7 p.56."
      - "Practice: learners apply the rule to fill in missing letters in words after
        шиплячі. Contrast with Russian where this distinction does not exist — Ukrainian
        learners must develop sensitivity to the following consonant's hardness/softness."
  - section: "Чергування голосних у дієслівних коренях"
    words: 550
    points:
      - "From Заболотний Grade 5 p.113, вправа 275: Verb root alternations driven
        by stress and suffix: летіти — літати, котити — катати, терти — стирати. Pattern:
        [е] ~ [i] ~ [и] depending on stress position and suffix (-а-, -и-, -іти-)."
      - "Extended examples from Заболотний Grade 5 p.114, вправа 276: захопити — хапати
        ([о] ~ [а]), сплести — сплітати ([е] ~ [i]), завмерти — завмирати ([е] ~ [и]),
        заберу — забирати ([е] ~ [и]). The alternation is predictable: before stressed
        -а- suffix, the root vowel changes."
      - "Connecting to A2 knowledge: learners already know these verbs from everyday
        use. Now they see the system. This transforms memorized pairs into a productive
        rule."
  - section: "Чергування і наголос: як вони пов'язані"
    words: 500
    points:
      - "Key insight: наголос (stress) drives many vowel alternations. When stress
        shifts away from a root vowel, the vowel may change: рік (stress on [i]) —
        років (stress on [i] in suffix, root has [о]). Авраменко Grade 5 p.111: the
        alternation often reveals the original vowel that existed before the shift
        to [i]."
      - "Practice: given a word with [i] in a closed syllable, learners find the form
        with [о] or [е] by changing the word form. This is exactly the spelling strategy
        taught in Ukrainian schools: Литвінова Grade 5 p.118: 'Якщо під час зміни
        слова сумнівний звук чергується з [i] в закритому складі — пишемо и: осені
        (бо осінь).'"
      - "Summary table: all three alternation types with examples, triggers, and exceptions
        — a reference card learners can use."
  - section: "Підсумок: правила і практика"
    words: 300
    points:
      - "Complete alternation summary with decision flowchart: Step 1: Is the syllable
        open or closed? -> [о]/[е] ~ [i] Step 2: Does the vowel disappear? -> fleeting
        vowel Step 3: Is it after a шиплячий? -> [о] ~ [е] rule Step 4: Is it a verb
        root with suffix change? -> verb alternation."
      - "Self-check in Ukrainian: Дайте відповіді на запитання: 1. Чому в слові 'двір'
        пишемо i, а в слові 'двори' — о? 2. Яке чергування відбувається у словах 'день
        — дня'? 3. Після яких приголосних чергуються [о] з [е]? 4. Запишіть три пари
        слів із чергуванням [о] ~ [i]."
      - "Preview of next module: Чергування приголосних (іменники) — consonant alternations
        in noun paradigms, building on the same morphophonemic logic."
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
    focus: "Identify which vowel alternation type is present in word pairs (e.g.,
      рік-року = [о]~[i]; день-дня = fleeting vowel)"
    items: 8
  - type: fill-in
    focus: "Complete word forms by applying the open/closed syllable rule (e.g., двір
      — двор___, стіл — стол___)"
    items: 8
  - type: match-up
    focus: "Match nominative forms with their oblique case counterparts (e.g., рік
      <-> року, кінь <-> коня, день <-> дня)"
    items: 8
  - type: group-sort
    focus: "Sort word pairs into categories: [о]~[i] alternation, [е]~[i] alternation,
      fleeting vowel, no alternation"
    items: 10
  - type: error-correction
    focus: "Find and fix vowel spelling errors in sentences caused by incorrect application
      of alternation rules"
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
    notes: "Core чергування голосних chapter: definition, examples with сіль-соляний,
      корінь-кореня, systematic presentation of patterns."
  - title: "Заболотний Grade 5, p.113-115"
    notes: "Чергування голосних звуків (section 27): verb pairs летіти-літати, practice
      exercises with open/closed syllable analysis."
  - title: "Литвінова Grade 5, p.118"
    notes: "Правопис ненаголошених [е] та [и]: verification strategy using word form
      changes, connection to чергування з [i]."
  - title: "Глазова Grade 10, p.103"
    notes: "Mature presentation: [о],[е]~[i] as a defining feature of Ukrainian, systematic
      examples шко-ла — шкіл, дво-ри — двір."
  - title: "Заболотний Grade 7, p.55-56"
    notes: "Чергування [о] з [е] після шиплячих: rule formulation, exceptions, practice
      exercises."

</plan_content>

---

## Knowledge Packet

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
