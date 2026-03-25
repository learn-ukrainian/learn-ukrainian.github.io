<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Russian characters found: ё
- FIX: Russian/archaic words: кот→кіт
- NOTE: Plan expects 5 exercise(s) but content has 4
</correction_directive>

LEARNINGS FROM PAST BUILDS (same error patterns seen before):
- [GLOBAL] сес-тра is a VALID word division per Правопис 2019 §49. Do NOT mark it as an error. Phonetic syllabification (се-стра) and typographic word division (сес-тра) follow different rules — both are correct in their respective contexts.
- [GLOBAL] Ukrainian textbooks teach a hands-on-EARS test for voicing (закрий долонями вуха), NOT a hand-on-throat test. The hand-on-throat test is a valid phonetics technique but must NOT be attributed to Ukrainian textbooks. Source: Кравцова 2019, Grade 2, p.39.
- [GLOBAL] Do NOT invent Ukrainian words for minimal pairs. "Сір" is NOT a word meaning "grey" — the correct form is "сірий". Use verified minimal pairs only: кит/кіт, бити/біти, лис/ліс.
- [GLOBAL] NEVER frame Ukrainian as "lacking" or "missing" letters that Russian has. Ukrainian has its own 33-letter alphabet — it is complete. Do NOT write "Ukrainian lacks Ъ, Ы, Э" or "Ukrainian doesn't have these Russian letters." Instead, highlight what Ukrainian HAS: Ґ, Є, Ї, І are unique to Ukrainian. Present Ukrainian on its own terms.

# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **8: Чергування голосних** (B1, B1.2 [Morphophonemics & Noun Subclasses]).

**Target: 4000–6000 words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block. Evaluate each section from the plan and commit to a word budget. This prevents frontloading early sections and rushing later ones.

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Summary: ~150 words
Total: 4000+ words
</pacing_plan>
```

Then begin writing the module content. Follow your own pacing plan — each section must hit its word budget (±10%).

---

## 8 Hard Rules

1. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
2. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
3. **NO "In this lesson we will..."** — never use formulaic openers. Start with a dialogue, a question, or a situation.
4. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
5. **Write exercises directly** — write complete exercises in the DSL format below. Include real questions, real answers, and real distractors. A downstream tool converts them to interactive React components.
6. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
7. **Hit the word target** — you MUST write 4000–6000 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
8. **NO archaic, obsolete, or rare words** — use only modern standard Ukrainian. Do not use words marked as archaic (застаріле) or dialectal in dictionaries. Example: use «кін» not «кон», use «пом'якшені» not «м'якшені». When in doubt, choose the common modern form. Your pre-training contains Russian-influenced archaic forms — verify unfamiliar words.

**Note:** Do NOT add stress marks (´) to any Ukrainian word — a deterministic tool handles this after you write.

## Exercises — Write Them Directly

After each key teaching point, write an exercise directly in DSL format.

**CRITICAL: Each exercise MUST match a specific `activity_hints` entry from the Plan.**
- Use the EXACT `type` specified (quiz, fill-in, match-up, group-sort, true-false)
- Follow the `focus` description EXACTLY — if the plan says "Answer: У тебе є...? Так / Ні", your quiz must test exactly that pattern
- Match the `items` count specified
- Do NOT invent different exercises — the plan's activity_hints are the specification

Write REAL content: real questions, real answers, real distractors. Every exercise must be solvable by a learner who read the preceding prose.

### DSL Format

Use these exact formats. Each block starts with `:::type` and ends with `:::`.

**Quiz** (multiple choice):
```
:::quiz
title: "Звук чи літера?"
---
- q: "Що ми чуємо і вимовляємо?"
  o: ["звуки", "літери", "слова"]
  a: 0
- q: "Що ми бачимо і пишемо?"
  o: ["літери", "звуки", "речення"]
  a: 0
:::
```

**Fill-in** (complete the sentence):
```
:::fill-in
title: "Complete the greeting"
---
- sentence: "Привіт! Як ___?"
  answer: "справи"
- sentence: "Дякую, ___."
  answer: "добре"
:::
```

**Match-up** (connect pairs):
```
:::match-up
title: "Match false friend letters to their real sounds"
---
- left: "В"
  right: "sounds like [в], not [b]"
- left: "Н"
  right: "sounds like [н], not [h]"
:::
```

**Group-sort** (classify into categories):
```
:::group-sort
title: "Classify letters"
---
groups:
  - name: "Голосні"
    items: ["А", "О", "У", "І"]
  - name: "Приголосні"
    items: ["М", "К", "Б", "Ш"]
:::
```

**True-false**:
```
:::true-false
title: "True or false?"
---
- statement: "В українській мові 33 літери."
  answer: true
- statement: "Голосних звуків більше, ніж приголосних."
  answer: false
:::
```

Spread exercises evenly throughout the module. Never cluster them.

### Approved Exercise Patterns

Use these Ukrainian textbook-inspired patterns (Заболотний, Авраменко) instead of generic "quiz" types:

- **Знайди помилку (Find the error):** Give 3 correct sentences and 1 with an error. Learner identifies the mistake. Tests: grammar rules, calques, Russianisms.
- **Обери правильне слово (Choose the right word):** Fill in the blank from 2-3 options (synonyms, paronyms, or confusable words). Tests: vocabulary nuance, register.
- **Утвори пару (Match-up):** Match words to antonyms, translations, or grammatical pairs (e.g., masculine → feminine). Tests: vocabulary, morphology.
- **Розподіли (Group-sort):** Sort items into 2-3 categories (e.g., голосні vs приголосні, hard vs soft consonants). Tests: foundational phonetics, grammar classification.
- **Склади речення (Build a sentence):** Give scrambled words, learner arranges into correct order. Tests: word order, sentence structure.
- **Знайди місце (Find the right place):** Give 4 sentences with blanks and 4 words — each word fits exactly one sentence. Tests: contextual meaning, collocations.

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
content_outline:
- section: "Що таке чергування голосних? (What is vowel alternation?)"
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
- section: "Чергування [о], [е] з [i] (The [o]/[e] to [i] alternation)"
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
- section: "Чергування [о], [е] з нулем звука (Fleeting vowels)"
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
  - "Rule from Караман Grade 10 p.56:
    After [ж], [ч], [ш], [дж], [й]:
    — write е before м'який приголосний or before syllables with [е], [и]:
    вечеря, вишень, джерело, женити.
    — write о before твердий приголосний or before syllables with [а], [о], [у]:
    бджола, будиночок, пшоно, знайомий."
  - "Exceptions to memorize: чепурний, шепіт, жебоніти, щедрий,
    черствий, чекати (е despite the rule), and чоло, бджола (о despite
    the rule). These are listed explicitly in Караман Grade 10 p.56."
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
- section: "Підсумок: правила i практика (Summary and practice)"
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
- title: "Караман Grade 10, p.55-56"
  notes: "Чергування [о] з [е] після шиплячих: rule formulation,
    exceptions, practice exercises."

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Чергування голосних
**Module:** alternation-vowels | **Phase:** B1.2 [Morphophonemics & Noun Subclasses]
**Textbook grades searched:** 1, 2, 3, 5

---

## Що таке чергування голосних? (What is vowel alternation?)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 13
> 	 Вимов голосні звуки в словах — назвах предме-
> тів.   
> 	 Вимов приголосні звуки в словах — назвах 
> предметів.
> 	 Який у тебе сьогодні настрій? Вибери.
> Мовні звуки: голосні та приголосні
> [•]
> [•]
>  [ – ]
>  [ – ]
>  [ – ]
>  [ – ]
> 	 Вимов перший звук у словах — назвах предме-
> тів. Який це звук? Приголосний звук позначає-
> мо так: [–].
> 	 Вимов перший звук у словах — назвах предметів. 
> Який це звук? Голосний звук позначаємо так: [•].

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 34
> ГоЛоснІ І ПриГоЛоснІ ЗвУки. 
> ПоЗначЕння ГоЛосниХ ЗвУкІв БУквами 
> Звуки мови поділяються на голосні і приголосні.
> Розглянь схему. Розкажи, як утворюються звуки мови.
> голосні
> голос
> голос і шум
> шум
> приголосні
> утворюються
> Звуки
> В українській мові є шість голосних звуків. 
> Ти можеш позначити їх на письмі десятьма буквами.
> голосні 
> звуки
> 6
> [а], [о], [у], [е], [и], [і]
> 10
> букви, що позначають 
> голосні звуки
> а, о, у, е, и, і, я, ю, є, ї
>  
> Спиши слова. Поділи їх на склади. Скільки звуків позначають 
> б

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 82
> Правильно вимовляю і пишу слова  
> із дзвінкими приголосними в кінці слова і складу
>  28
> Вимова і написання слів  
> із дзвінкими приголосними  
> звуками в кінці слова і складу
> Пригадай і розкажи 
> у класі.
> Я — учителька
> Я — учитель
> В українській мові дзвінкі приголосні звуки в кінці слова 
> і в кінці складу перед глухим приголосним вимовляються 
> дзвінко і позначаються відповідними буквами.
> гриб[б]
> мед[д]
> каз[з]ка
> книж[ж]ка
> 1   Прочитай прислів’я, вимовляючи дзвінкі 
> приголосні в кінці слів і склад

> **Source:** unknown, Grade 5
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
> одного

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 9
> Склад слова.  
> Наголошені та ненаголошені склади
> 	 Що «зайве»? Поділи слова на склади. Визнач 
> наголошений склад.
>         
>         
>         
> 	 Який у тебе сьогодні настрій? Вибери.

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> ЗВУКО-БУКВЕНИЙ СКЛАД 
> СЛОВА
> АНАЛІЗУЮ ЗВУКОВИЙ СКЛАД СЛОВА
> звуки.
> Г
> звук
> в
> о
> Мовний звук — елемент людської мови, 
> утворений за допомогою органів мовлення.
> Хвилинка спілкування
> 1
> — В українській мові шість голосних 
> звуків.
> — Я думаю, що їх десять.
> — Ні. Запам'ятай шість голосних 
> звуків:
> [а], [о], [у], [е], [и], [і].
> — Добре. Запам’ятаю!
> 4

## Чергування [о], [е] з [i] (The [o]/[e] to [i] alternation)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 54
> На дереві сиділи 
> .
>  цвіли  на  клумбі.
> Гіркий смак у 
> . 
>  — солодкі.
> 	
> Визнач, якому слову — назві намальованого 
> предмета відповідає кожна схема.
> 	
> Доповни речення словами.
> [ –•| –•= ] 
> [ =•|  =•= ] 
> [ –  = • | –•=] 
> 	
> Розгадай кросворд.
> 1
> 2
> 3
> 5
> 6
> 4
> 1
> 2
> 3
> 4
> 5
> 6
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 3| Запиши слова, ставлячи апостроф, де це потрібно.
> г
> у
> Бережи здоров'я змолоду.
> зоря
> м ? ята
> солов ?1
> Чому цї слова пишуться 
> по-різному?
> здоров?і 
> здоров?я 
> сузір?я 
> зор?я 
> пір?я 
> б?ють
> мор ? я
> пШ О Замініть виділені слова і запишіть за зразком. Поясніть 
> уживання апострофа. 
> „ 
> .
> пір'я горобця 
> будинок із каменю 
> спів солов'я 
> квакання жаб 
> бриль із соломи 
> ліжко з дерева
> л• у 
> _
> пір я — ? звуків, ? букв
> гороб'яче пір'я 
> кам'яний будинок
> Послухайте вірш Надії Красоткіної. Назвіть слова, 
> які

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 74
> 2.	 Запиши сполучення іменників із прикметниками за зразком.
> Зразок. Молоко (яке?) поживне, смачне, біле, пінне, запашне.
> 208.	 Знайди та запиши спільні ознаки предметів. Виділи закінчення 
> прикметників.
> Зразок. Огірок (який?) смачний, груша (яка?) смачна, 
> яблуко (яке?) смачне.
> 209.	 1.	 Прочитай текст, уставляючи потрібні закінчення. Як ти гадаєш, 
> чому цей пиріг називають перекладанцем?
> Перекладанець
> Традиційн.. солодк.. страва  — це 
> щедр.., як і весь українськ.. стіл, смачн.. 
> випічка! Р

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 202
> КОРОТКИЙ  СЛОВНИК  НАГОЛОСІВ  
> закрутка
> залишити
> занести
> заробіток
> заставка
> застібка
> зібрання
> зобразити
> зозла
> зрання
> зручний
> зубожіння
> І
> індустрія
> К
> камбала
> каталог
> квартал
> кишка 
> кілометр
> кінчити
> колесо
> колія
> корисний
> косий
> котрий
> крицевий
> кроїти
> кропива
> кулінарія
> курятина
> Л
> лате
> листопад
> літопис
> М
> мабуть
> мережа
> металургія
> міліметр
> Н
> навчання
> нанести
> начинка
> ненавидіти
> ненависний
> ненависть
> нести
> ніздря
> новий
> О
> обіцянка
> обрання
> обруч (іменник)
> одинадцять
> одноразовий
> ознака
> олень
> оптовий
> отам

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 12
> Прочитай. Знайди слова, у яких три склади.
> 	
> хліб	
> булка	
> болото	
> бу-­тер-­брод
> 	
> краб	
> білка	
> борода	
> бу-­тер-­бро­-дик 
> 	 батон	
> будка	
> собака	
> бу-­тер-­бро-д­ний
> 
> Послідовність дій
> Я готую бутерброд
> Що мені потрібно? Продовж ряд.
>  
>  ...
> Установи послідовність дій за малюнком. 
> 	
> Я кладу лист салату на хліб.
> 	
> Я беру шматок хліба.
> 	
> Я кладу сир і ковбасу на лист салату.
> 	
> Я їм бутерброд. Смачно! 
> 	
> Я на-ма-щу-ю масло на хліб. 
>  
> 1
> 2
> Б б
> б у |т е р |б р од
> 1
> 2
> 3
> 4
> 5

> **Source:** unknown, Grade 2
> **Score:** 0.33
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
> стрічки. Сміється

## Чергування [о], [е] з нулем звука (Fleeting vowels)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 11
> Звуки. Немовні звуки. Жести
> 	 Відтвори звуки потяга, який наближається до 
> хлопчика й навпаки.
> 	 Який у тебе сьогодні настрій? Вибери.
> 	 Що хочуть сказати діти?
> Мова без слів (жести)

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> і[ Склади і запиши слова з таких звуків.
> [ш], [о], [л], [а], [к] 
> [о], [р], [у], [к]
> [к], [о], [Дз], [и], [в], [н]
> • Послідовно назви звуки в утворених словах.
> 2| Прочитайте уривок із вірша Лариси Зоріної. Поясніть, 
> що означає виділене сполучення слів.
> Дзвенить, дзвенить шкільний дзвінок, 
> нас закликає до навчання.
> Ми поспішаєм на урок,
> бо ми йдемо у світ пізнання.
> • Складіть і запишіть речення про шкільний дзвінок.
> • Знайдіть у вірші ці слова.
> Звукову схему слова можна зобразити 
> ■! по-іншому,

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 57
> Тихий спів — дзвінкий спів.
> тиха вулиця 
> тиха течія 
> тихий крок 
> тиха розмова 
> 5   Утвори сполучення слів із протилежним значенням і запиши.
> 	
>   Запиши. Підкресли антоніми.
> 	
>   Усно склади речення із двома 
> сполученнями слів (на вибір).
> 	
>   Доб

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Що таке чергування голосних? (What is vowel alternation?)` (~550 words)
- `## Чергування [о], [е] з [i] (The [o]/[e] to [i] alternation)` (~900 words)
- `## Чергування [о], [е] з нулем звука (Fleeting vowels)` (~650 words)
- `## Чергування [о] з [е] після шиплячих та [й]` (~550 words)
- `## Чергування голосних у дієслівних коренях` (~550 words)
- `## Чергування i наголос: як вони пов'язані` (~500 words)
- `## Підсумок: правила i практика (Summary and practice)` (~300 words)
- `## Підсумок — Summary` (~150 words)

Each section should follow the word budget specified. The total must reach 4000 words minimum.

---

## Content Rules

Full Ukrainian immersion. Grammar explained IN Ukrainian. English only for disambiguation of false friends. Sentences max 30 words.

GRAMMAR RULES:
- Max 30 words per Ukrainian sentence
- Max 4 clauses per sentence
- All grammar constructions allowed
- Participles allowed
- Complex subordinate clauses allowed

### Pedagogy
- Start each section with a real situation or dialogue (PPP: Present → Practice → Produce)
- Every grammar rule needs 3+ Ukrainian examples with English translations
- Teach through PATTERNS, not rules: show examples first, then name the pattern
- Cultural context where relevant — this is Ukrainian, not generic L2
- Use vocabulary from the plan's vocabulary_hints. Function words (pronouns, conjunctions) are always allowed.

### Ukrainian Language Quality
- **Zero Russian**: No ы, э, ё, ъ. No Russian words (кот→кіт, хорошо→добре, конечно→звичайно)
- **Zero Surzhyk**: No шо→що, чо→чому, тіпа→типу
- **Zero calques**: No приймати душ→брати душ, приймати рішення→ухвалювати рішення
- **Zero paronyms**: тактична≠тактовна, ефектний≠ефективний — use the right word, not a similar-sounding one
- **Natural Ukrainian**: Write how a Ukrainian teacher would explain this to a student. Not robotic, not textbook-dry, not overly casual.

**Authority hierarchy (if uncertain about a word, check in this order):**
VESUM (does word exist?) → Правопис 2019 (spelling) → Горох (stress) → Антоненко-Давидович (style) → Грінченко (etymology).

**Online fallbacks:** VESUM: vesum.com.ua | Правопис: 2019.pravopys.net | Горох: goroh.pp.ua | Антоненко-Давидович: ukrlib.com.ua/books/printit.php?tid=4002 | Грінченко: hrinchenko.com | Словник.ua: slovnyk.me

### Writing Quality
- Every paragraph: ONE clear point, logical flow to the next
- Vary sentence length (short for emphasis, medium for explanation, long for examples)
- Use callout boxes (:::tip, :::caution, :::note) sparingly — max 3 per module
- **Dialogue formatting** — use blockquote `>` with speaker names in bold. Each turn on its own line. At A1 level, add English translation in italics after each line so learners understand what is being said. At A2, translate only new vocabulary. At B1+, no dialogue translations. Example:

> **Оленка:** Привіт! Як справи? *(Hi! How are you?)*
> **Тарас:** Добре, дякую! А у тебе? *(Good, thanks! And you?)*
> **Оленка:** Теж добре! *(Also good!)*

Without speaker names, the reader cannot tell who is speaking. NEVER use anonymous em dashes (`— text`). After each dialogue, briefly explain the key phrases and patterns the learner just saw.
- Dialogues: natural, not stilted. Real situations, real responses. **Use the knowledge packet** — it contains textbook excerpts with real Ukrainian dialogues and situations. Adapt them, don't invent artificial conversations. A dialogue about немає should show someone SEARCHING for something and not finding it (keys, notebook, phone), not an interrogation. A dialogue about the market should sound like a real market conversation. If the knowledge packet has a textbook dialogue on the topic, use that pattern.
- **Tone:** Authoritative but warm. Like a skilled Ukrainian teacher — confident, clear, culturally grounded. Let the content be interesting on its own.
- **Never guess about Ukrainian.** If you are unsure about a word, grammatical form, or phonetic rule — flag it with `<!-- VERIFY: word/claim -->`. Never invent or describe vaguely to hide uncertainty.

### Forbidden Tropes

If you write any of these patterns, the module will be rejected in review:

- **The Cheerleader:** "Great job!", "Don't worry, it's easy!", "You're doing amazing!", "Good news!" — respect the learner's intelligence; stay professional.
- **The Announcer:** "In this section, we will explore...", "Now let's dive into...", "Let's take a look at...", "To summarize what we learned..." — never use formulaic transitions. Just teach the concept directly.
- **The Translator:** "The Ukrainian word for 'cat' is 'кіт'." — instead, present naturally: "A domestic cat is a **кіт**."
- **The Wall of Text:** 3+ paragraphs of English theory without a single Ukrainian example — every concept must be anchored in immediate Ukrainian examples.
- **The Filler:** "This is a very important concept that you will use frequently in your daily life." — empty sentences that add words but not meaning. Every sentence must teach something.



### Vocabulary

**Required:** чергування (alternation — systematic sound change between word forms), голосний (vowel — sound produced without obstruction), відкритий склад (open syllable — ending in a vowel sound), закритий склад (closed syllable — ending in a consonant sound), корінь (root — the core meaning-bearing part of a word), наголос (stress — emphasized pronunciation of a syllable), біглий голосний (fleeting vowel — vowel that disappears in some forms), нуль звука (zero sound — absence of a vowel in an alternation), суфікс (suffix — morpheme added after the root), закінчення (ending — inflectional morpheme at the end of a word), шиплячий (hushing consonant — ж, ч, ш, дж), орфограма (orthographic rule — a spelling pattern requiring a rule), відмінок (grammatical case), форма слова (word form — a specific inflected variant of a word)
**Recommended:** милозвучність (euphony — pleasant sound quality of speech), ненаголошений (unstressed — syllable without stress), відкритий (open — ending in a vowel), закритий (closed — ending in a consonant), морфонологія (morphophonology — study of sound alternations in morphology), твердий (hard — non-palatalized consonant), м'який (soft — palatalized consonant), спільнокореневий (cognate — sharing the same root), правопис (orthography — correct spelling rules), перевірне слово (checking word — word used to verify spelling)

### Pronunciation Videos



---

### Style Reference (match this tone and structure)

Дієприкметники — це особлива форма дієслова, яка поєднує ознаки дієслова та прикметника. Вони відповідають на питання «який?» і змінюються за родами, числами та відмінками, як звичайні прикметники.

Порівняйте:
- **написаний лист** (a written letter) — пасивний дієприкметник
- **зігрітий чай** (warmed tea) — пасивний дієприкметник

:::tip
В українській мові активні дієприкметники теперішнього часу (на -учий/-ючий) вважаються стилістично небажаними. Замість «працюючий лікар» краще сказати «лікар, який працює».
:::

*Note: Grammar explained IN Ukrainian using Ukrainian linguistic terms. English appears only in parenthetical translations for disambiguation. Callout boxes in Ukrainian.*



---

## Skeleton — Follow This Structure Exactly

A detailed paragraph-level skeleton was generated for this module. You MUST follow it precisely:
- Write every paragraph listed, in the order listed
- Hit each paragraph's word budget (+-10%)
- Place exercises exactly where the skeleton says
- Use the specific examples named in the skeleton
- Do NOT skip paragraphs, reorder sections, or add unplanned content

The skeleton replaces Step 1 (Pacing Plan) — do NOT output a <pacing_plan> block. Start writing immediately from the first section.

<skeleton>
## Що таке чергування голосних? (What is vowel alternation?) (~600 words total)
- P1 (~150 words): Bridge from M01 (metalanguage-phonetics). Recall previously learned concepts: голосний, приголосний, наголос, відкритий/закритий склад. Introduce the core idea that these phonetic properties are not just for pronunciation, but actively drive systematic spelling changes in Ukrainian words.
- P2 (~150 words): Define чергування звуків (alternation) using context from Авраменко (Grade 5). Explain that sometimes, when forming a new word or changing its form (e.g., declension), a sound can change into another. Give clear introductory examples: сіль — соляний, корінь — кореня. 
- P3 (~150 words): Explain why this matters. Highlight that чергування голосних is a defining, signature feature of Ukrainian phonology that distinguishes it from other East Slavic languages like Russian or Polish (referencing Глазова Grade 10). Emphasize that mastering this unlocks the correct spelling for thousands of words instead of rote memorization.
- P4 (~150 words): Provide a roadmap overview of the main alternation types covered in this module: 1. The [о], [е] to [i] shift (open/closed syllable rule), 2. The [о], [е] to zero shift (fleeting vowels / біглі голосні), 3. The [о] to [е] shift after hushing consonants (шиплячі) and [й].

## Чергування [о], [е] з [i] (The [o]/[e] to [i] alternation) (~1000 words total)
- P1 (~150 words): State the core open/closed syllable rule from Заболотний (Grade 5). Explain that when a syllable changes from open to closed (or vice versa), [о] or [е] in the root alternates with [i]. Define an open syllable (ends in a vowel: дво-ри, ко-ні, ро-ку) versus a closed syllable (ends in a consonant: двір, кінь, рік).
- P2 (~150 words): Provide systematic examples for nouns showing the nominative (closed) to genitive (open) shift. Detail the pairs: стіл — столу, двір — двору, сіль — солі, віз — воза, ніс — носа, рік — року, річ — речі. 
- P3 (~150 words): Expand the systematic examples to adjectives and verbs. Show how the rule applies to adjectives: осінній — осени, вечірній — вечора. Show verb pairs reflecting the same phonetic logic: нести — ніс, везти — віз.
- P4 (~150 words): Discuss exceptions and special cases. Explain that not every closed syllable triggers the change, noting that borrowed words typically do not alternate (e.g., мотор — мотору, not *мотіру). Mention that some native words also have fossilized forms that resist the shift.
- Exercise: fill-in, focus: "Complete word forms by applying the open/closed syllable rule (e.g., двір — двор___, стіл — стол___)", items: 8
- P5 (~200 words): Present a short reading passage describing a traditional Ukrainian village that organically weaves in words with the [о]/[е] ~ [i] alternation (e.g., двір, стіл, піч, вікна, кіт, лід, ріг). The narrative should highlight the natural flow of these sounds in context.
- P6 (~200 words): Analyze the reading passage paragraph. Instruct the learner to identify all alternating pairs within the text and explicitly state whether the syllable is open or closed in each form, solidifying the application of the rule.

## Чергування [о], [е] з нулем звука (Fleeting vowels) (~700 words total)
- P1 (~150 words): Define fleeting vowels (чергування з нулем звука / біглі голосні) using the definition from Заболотний (Grade 5). Explain the phenomenon where [о] or [е] disappears entirely when the word form changes—the vowel is present in the nominative but vanishes in oblique cases.
- P2 (~150 words): Detail the common patterns found in masculine nouns. Explain how the vowel [е] or [о] in the final syllable of the nominative drops when an ending is added. Provide core examples: учень — учня, день — дня, вітер — вітру, камінь — каменя.
- P3 (~150 words): Focus on specific noun suffixes that predictably contain fleeting vowels. Detail the suffixes -ець/-ця (молодець — молодця, хлопець — хлопця), -ок/-ка (замок — замка, гурток — гуртка), and -ень/-ня (корінь — кореня, пень — пня).
- Exercise: match-up, focus: "Match nominative forms with their oblique case counterparts (e.g., рік <-> року, кінь <-> коня, день <-> дня)", items: 8
- P4 (~150 words): Explain how to recognize fleeting vowels versus stable vowels. Introduce the consonant cluster test: if removing the vowel creates an impossible consonant cluster, the vowel might be stable. Acknowledge that Ukrainian does tolerate clusters like -дня and -тру. Contrast minimal pairs: сон — сну (fleeting) vs. стон — стону (stable).
- P5 (~100 words): Provide a short analytical scenario where the learner must predict whether a list of unfamiliar nouns will drop their vowel in the genitive case based on the suffix and cluster patterns discussed.

## Чергування [о] з [е] після шиплячих та [й] (~600 words total)
- P1 (~150 words): Introduce the rule from Караман (Grade 10) for vowels after hushing consonants (шиплячі: [ж], [ч], [ш], [дж]) and [й]. Explain that we write [е] before a soft consonant (м'який приголосний) or before syllables with [е], [и]. Give examples: вечеря, вишень, джерело, женити.
- P2 (~150 words): Explain the contrasting half of the rule: we write [о] before a hard consonant (твердий приголосний) or before syllables containing [а], [о], [у]. Provide clear examples: бджола, будиночок, пшоно, знайомий. Emphasize the required sensitivity to the following consonant's hardness/softness.
- P3 (~150 words): List the critical exceptions to this rule that must be memorized. Detail words that take [е] despite the rule: чепурний, шепіт, жебоніти, щедрий, черствий, чекати. Detail words that take [о] despite the rule: чоло, бджола.
- Exercise: error-correction, focus: "Find and fix vowel spelling errors in sentences caused by incorrect application of alternation rules", items: 6
- P4 (~150 words): Contrast this specific orthographic rule with Russian, noting that this exact distinction does not exist in Russian. Explain that this is a common area for Surzhyk errors, making it crucial for Ukrainian learners to actively develop sensitivity to the phonetic environment after hushing consonants.

## Чергування голосних у дієслівних коренях (~600 words total)
- P1 (~150 words): Shift focus to verb root alternations driven by stress and suffixation, based on Заболотний (Grade 5). Introduce the base pairs showing imperfective/perfective or motion/state shifts: летіти — літати, котити — катати, терти — стирати.
- P2 (~150 words): Break down the specific phonetic pattern: [е] ~ [i] ~ [и] depending on the stress position and the specific verbal suffix applied (-а-, -и-, -іти-). Explain how the root vowel reacts to what follows it.
- P3 (~150 words): Provide extended examples of this verbal alternation: захопити — хапати ([о] ~ [а]), сплести — сплітати ([е] ~ [i]), завмерти — завмирати ([е] ~ [и]), заберу — забирати ([е] ~ [и]). Highlight that the root vowel changes predictably before the stressed -а- suffix.
- P4 (~150 words): Connect this underlying system to the learner's existing A2 knowledge. Remind them that they already know these verb pairs as individual vocabulary items, but now they can see the morphophonemic rules governing them, transforming memorized exceptions into a productive, predictable system.

## Чергування i наголос: як вони пов'язані (~550 words total)
- P1 (~150 words): Detail the key linguistic insight that наголос (stress) is the primary driver of many vowel alternations. Explain that when stress shifts away from a root vowel during inflection, the vowel changes. Contrast рік (stress on root [i]) with років (stress on suffix, root reverts to [о]).
- P2 (~150 words): Elaborate on the concept from Авраменко (Grade 5): the alternation often acts as a phonetic historical record, revealing the original [о] or [е] vowel that existed in the root before the historical shift to [i] occurred in closed syllables.
- P3 (~150 words): Teach the practical spelling verification strategy (перевірне слово) from Литвінова (Grade 5). Explain that if a learner is unsure whether to write 'е' or 'и', they should change the word form to see if the vowel alternates with [i] in a closed syllable (e.g., writing 'осені' with 'е' because the nominative is 'осінь').
- Exercise: quiz, focus: "Identify which vowel alternation type is present in word pairs (e.g., рік-року = [о]~[i]; день-дня = fleeting vowel)", items: 8
- P4 (~100 words): Present a comprehensive summary reference table. This table should organize all three main alternation types (open/closed [о]/[е]~[i], fleeting vowels, after шиплячі), listing their triggers, patterns, and common exceptions for quick review.

## Підсумок: правила i практика (Summary and practice) (~350 words total)
- P1 (~150 words): Summarize the module with a clear decision flowchart for learners: Step 1: Is the syllable open or closed? -> apply [о]/[е] ~ [i]. Step 2: Does the vowel disappear entirely? -> it's a fleeting vowel. Step 3: Is it situated after a шиплячий? -> apply the [о] ~ [е] rule. Step 4: Is it a verb root with a suffix change? -> apply verb alternation.
- P2 (~100 words): Provide a self-check (Дайте відповіді на запитання) in Ukrainian to test comprehension: 1. Чому в слові 'двір' пишемо i, а в слові 'двори' — о? 2. Яке чергування відбувається у словах 'день — дня'? 3. Після яких приголосних чергуються [о] з [е]? 4. Запишіть три пари слів із чергуванням [о] ~ [i].
- Exercise: group-sort, focus: "Sort word pairs into categories: [о]~[i] alternation, [е]~[i] alternation, fleeting vowel, no alternation", items: 10
- P3 (~100 words): Conclude with a brief preview of the next module (b1-009). State that learners will next explore "Чергування приголосних (іменники)"—consonant alternations in noun paradigms—building directly on the exact same morphophonemic logic mastered in this module.
</skeleton>

## Output Format

Write in Markdown. Use:
- `## Section Title` for main sections
- `### Subsection` for subsections within a section
- `**bold**` for Ukrainian words being taught — EVERY bold Ukrainian word MUST have an English translation on first use, either in parentheses `**слово** (translation)` or inline `**слово** means "translation"`. No exceptions.
- Tables for paradigms (conjugation, declension)
- `:::tip` / `:::caution` / `:::note` for callout boxes
- `:::quiz` / `:::fill-in` / `:::match-up` / `:::group-sort` / `:::true-false` for exercises (using the DSL formats above)

Do NOT write MDX component syntax or JSON. Plain Markdown with the exercise DSL blocks described above.

Begin writing now. Start with the first section heading.
