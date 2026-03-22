<correction_directive>
CRITICAL: Your previous module was reviewed and scored below 8.0/10.
You must rewrite the module FROM SCRATCH, fixing ALL issues below.
All original constraints from the writing prompt still apply.

- FIX: [Structural integrity] [critical]
  Location: Entire document
  Issue: The word count is massively below the 4000-word target (estimated ~1800-2000 words). The sections are too brief to fulfill the B1-level depth expected for a 4000-word module.
  Fix: Expand every section significantly. Add more examples, deep-dive explanations on how these concepts affect future grammar (e.g., how voiced/voiceless pairs interact in prefixes), and detailed step-by-step walk-throughs for phonetic transcription.
- FIX: [Exercise quality] [critical]
  Location: All `:::` exercise blocks
  Issue: The generated activities completely ignore the `activity_hints` array in the plan. Types, item counts, and focuses are all wrong.
  Fix: Delete the current activities and generate exactly what is in the plan: an 8-item classify quiz, an 8-item term match-up, a 6-item transcription fill-in, a 10-item consonant group-sort, a 6-item mark-the-words for sonorants, and a 6-item error-correction for transcriptions.
- FIX: [Plan adherence] [major]
  Location: Section "Приголосні звуки: дзвінкі та глухі"
  Issue: The plan explicitly required a "Reading practice passage: a short Ukrainian text about sounds, with learners identifying дзвінкі, глухі, and сонорні in context." This is missing.
  Fix: Write the requested short reading passage and integrate it into the section before the activities.
- FIX: [Plan adherence] [major]
  Location: Section "Підсумок: ваш фонетичний словник"
  Issue: The plan explicitly required a "Self-check in Ukrainian: Дайте відповіді на запитання 1-5" and a "Preview of next module: Будова слова". Both are missing.
  Fix: Add the 5 numbered self-check questions and the preview paragraph exactly as requested in the plan outline.
- NOTE: [Linguistic accuracy] [minor]
  Location: Section "Приголосні звуки: тверді та м'які", paragraph starting with "Також приголосні можуть ставати пом'якшеними..."
  Issue: Incorrect phonetic classification. The text claims [с] in "пісня" becomes "пом'якшеним [с']". In Ukrainian phonetics, dental sibilants like [с] have a full soft pair and become completely **м'які** (soft) before another soft dental, not just пом'якшені (half-soft/partially softened).
  Fix: Change the example of a "пом'якшений" consonant. Use a labial, velar, or hushing consonant before [i] (e.g., [б] in "білий", [к] in "кіт", [ж] in "жінка" are пом'якшені). Reserve "пісня" for an example of full assimilation of softness (м'якість).

- FIX (Linguistic): One minor phonetic terminology error found regarding assimilation:
- "У слові «пісня» звук [с] стає пом'якшеним [с'] через те, що наступний звук [н'] є дуже м'яким." -> Звук [с] належить до зубних/свистячих і має повноцінну м'яку пару. Перед м'яким [н'] він стає повністю **м'яким** [с'], а не "пом'якшеним" (напівм'яким). Термін "пом'якшені" стосується губних, шиплячих та задньоязикових (напр. [ж] у "жінка", [б] у "білий"), які не мають справжньої м'якої пари.
</correction_directive>

# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **1: Звуки і букви** (B1, B1.1 [Metalanguage Bridge]).

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

## 6 Hard Rules

1. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
2. **NO "In this lesson we will..."** — never use formulaic openers. Start with a dialogue, a question, or a situation.
3. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
4. **Write exercises directly** — write complete exercises in the DSL format below. Include real questions, real answers, and real distractors. A downstream tool converts them to interactive React components.
5. **NO meta-commentary** — do NOT add "Content notes:", word count summaries, or self-audit sections at the end. Just write the module content and stop.
6. **Hit the word target** — you MUST write 4000–6000 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.

**Note:** Do NOT add stress marks (´) to any Ukrainian word — a deterministic tool handles this after you write.

## Exercises — Write Them Directly

After each key teaching point, write an exercise directly in DSL format. Base your exercises on the `activity_hints` in the Plan — each hint should become one exercise.

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
module: b1-001
level: B1
sequence: 1
slug: metalanguage-sounds
version: '3.0'
title: "Звуки і букви"
subtitle: "Фонетика українською — від звуків до транскрипції"
focus: phonetics
pedagogy: PPP
phase: "B1.1 [Metalanguage Bridge]"
word_target: 4000
objectives:
- "Learner can name and classify Ukrainian sounds using Ukrainian metalanguage
  (голосний, приголосний, дзвінкий, глухий, твердий, м'який, сонорний)"
- "Learner can explain the difference between звук, літера, and фонема in Ukrainian"
- "Learner can read and produce фонетична транскрипція for common Ukrainian words"
- "Learner can identify наголос in words and explain its role in Ukrainian phonetics"
- "Learner can classify consonants by three criteria: дзвінкість/глухість,
  твердість/м'якість, and місце творення (губні, свистячі, шиплячі)"
content_outline:
- section: "Що вивчає фонетика? (What does phonetics study?)"
  words: 600
  points:
  - "Bridge introduction: learners already KNOW Ukrainian sounds from A1-A2.
    This module teaches them to NAME what they know using Ukrainian linguistic
    terminology. The shift: from 'vowels and consonants' to голосні та приголосні.
    From 'stress' to наголос. From 'soft consonant' to м'який приголосний."
  - "Core definitions from Заболотний Grade 5 p.74:
    Фонетика (від грец. phonetikos — звуковий) — розділ мовознавства,
    що вивчає звуковий склад мови.
    Графіка — розділ мовознавства, що вивчає систему умовних знаків
    для передачі звуків на письмі.
    Орфоепія — правила літературної вимови."
  - "The golden rule revisited at B1 level (Заболотний Grade 5 p.73):
    'Ми чуємо і вимовляємо звуки, а бачимо і пишемо літери.'
    33 літери in the alphabet, 38 звуків in the language.
    Why the mismatch: я, ю, є, ї can represent two sounds;
    щ = [шч]; ь and ' (апостроф) have no sound of their own."
  - "Звук vs фонема: звук is any concrete speech sound a person produces.
    Фонема is the abstract unit that distinguishes meaning.
    Example: [г] in горох is one фонема; the actual pronunciation may vary
    by speaker, but all variations are the same фонема.
    This distinction matters for understanding Ukrainian grammar explanations."
- section: "Голосні звуки (Vowel sounds)"
  words: 550
  points:
  - "Definition from Литвінова Grade 5 p.104:
    Голосні звуки утворюються голосом, без перешкоди.
    6 голосних звуків: [а], [о], [у], [е], [и], [і].
    10 голосних літер: а, о, у, е, и, і, я, ю, є, ї."
  - "Why 10 letters but only 6 sounds? The 'йотовані' letters я, ю, є, ї:
    — На початку слова: яма [йама], юнак [йунак], єдність [йедн'іст'].
    — Після голосного: мрія [мр'ійа], краює [крайуйе].
    — Після апострофа: п'ять [пйат'], об'єм [обйем].
    — Після приголосного (without apostrophe): they soften the consonant:
    ляля [л'ал'а], любов [л'убов], лід [л'ід]."
  - "Ненаголошені голосні — why this matters for spelling:
    In unstressed position, [е] and [и] sound similar.
    This is why Ukrainians themselves study правопис ненаголошених [е], [и].
    Rule: change the word form to put the vowel under stress —
    зелéний (бо зéлень), крилó (бо крила).
    Літвінова Grade 5 p.118: 'Якщо під час зміни слова сумнівний звук
    чергується з [і] в закритому складі — пишемо и: осені (бо осінь).'"
- section: "Приголосні звуки: дзвінкі та глухі (Consonants: voiced and voiceless)"
  words: 700
  points:
  - "Definition from Авраменко Grade 5 p.77:
    Приголосні звуки бувають дзвінкі та глухі.
    Дзвінкі = голос + шум. Глухі = лише шум.
    The paired system (Литвінова Grade 5 p.122):
    дзвінкі: [б], [д], [ґ], [г], [з], [ж], [дж], [дз]
    глухі:   [п], [т], [к], [х], [с], [ш], [ч],  [ц]"
  - "Сонорні приголосні — a special group (Литвінова Grade 5 p.123):
    Sounds [в], [м], [н], [л], [р] and their soft pairs + [й]
    are neither дзвінкі nor глухі. Голос переважає над шумом.
    Mnemonic from textbooks: МіНеРаЛоВиЙ.
    Important: Ukrainian дзвінкі приголосні do NOT become глухі
    at the end of a word (unlike Russian/German). дуб = [дуб], not *[дуп]."
  - "Свистячі та шиплячі (Литвінова Grade 5 p.123):
    Свистячі: [з], [ц], [с], [дз] — sound like a whistle.
    Шиплячі: [ж], [ч], [ш], [дж] — sound like hissing.
    Губні: [б], [п], [в], [м], [ф] — formed with the lips.
    These groups matter for spelling rules (уподібнення, чергування)
    that learners will encounter throughout B1."
  - "Reading practice passage: a short Ukrainian text about sounds,
    with learners identifying дзвінкі, глухі, and сонорні in context.
    Example words for classification:
    безпека [безпека] — б(дзв.), з(дзв.), п(гл.), к(гл.)
    школярі [школ'ар'і] — ш(шипл.), к(гл.), л'(сон.), р'(сон.)"
- section: "Приголосні звуки: тверді та м'які (Consonants: hard and soft)"
  words: 700
  points:
  - "From Авраменко Grade 5 p.75:
    М'який приголосний утворюється, коли кінчик язика торкається
    до піднебіння (palatalized). Твердий — коли торкається до зубів.
    Pair example: лис [лис] (тв.) vs ліс [л'іс] (м'як.) — different meaning!"
  - "How softness is shown in writing (Литвінова Grade 5 p.126):
    — м'який знак (ь): день [ден'], кінь [к'ін'], сіль [с'іл'].
    — літери я, ю, є, і after a consonant: ляк [л'ак], любов [л'убов].
    In транскрипція, softness is marked with [']:
    тінь [т'ін'], дядько [д'ад'ко]."
  - "Пом'якшені приголосні — the third category (Авраменко Grade 5 p.75):
    Some consonants are not fully м'які but пом'якшені (partially softened).
    This happens when a hard consonant stands before a soft one:
    пісня [п'іс'н'а] — [с'] is пом'якшений before [н'].
    The distinction: м'які are always soft, пом'якшені are soft only
    because of their phonetic environment."
  - "Consonants that are ALWAYS тверді (have no soft pair):
    [б], [п], [в], [м], [ф], [г], [ґ], [к], [х], [ж], [ч], [ш], [дж], [р].
    Consonants that are ALWAYS м'які: [й].
    Consonants that form тверді/м'які pairs:
    [д]-[д'], [т]-[т'], [з]-[з'], [с]-[с'], [ц]-[ц'], [дз]-[дз'],
    [л]-[л'], [н]-[н']."
- section: "Наголос (Stress)"
  words: 600
  points:
  - "From Авраменко Grade 5 p.88:
    Наголос — це посилена вимова одного зі складів.
    Ukrainian stress is вільний (free — can fall on any syllable)
    and рухомий (mobile — can shift between word forms):
    руки (plural) vs руки (genitive singular).
    This differs from languages with fixed stress (Polish — penultimate,
    French — final)."
  - "Наголос змінює значення (stress changes meaning):
    зáмок (castle) vs замóк (lock) — from Авраменко Grade 5 p.88.
    óбід (rim) vs обід (lunch). приклад (example) vs приклад (rifle butt).
    Орфоепічна помилка — a pronunciation error caused by wrong stress."
  - "Наголошений vs ненаголошений склад:
    The stressed syllable is наголошений, all others are ненаголошені.
    In калина [калина]: ка- (ненаголошений), -ли- (наголошений),
    -на (ненаголошений).
    Practice: learners mark наголос in common words and check against
    an орфоепічний словник."
  - "Why наголос matters for B1: upcoming modules on чергування голосних
    (vowel alternations like рік-рóку, кінь-коня) are driven by stress shifts.
    Understanding наголос now = understanding morphophonemics later."
- section: "Фонетична транскрипція (Phonetic transcription)"
  words: 550
  points:
  - "Rules from Заболотний Grade 5 p.74:
    1. Запис беремо у квадратні дужки: [калина].
    2. Кожен звук позначаємо окремою буквою.
    3. НЕ використовуємо букви я, ю, є, ї, ь, щ та великі букви.
    4. Позначаємо місце наголосу: [подорож].
    5. М'якість приголосного позначаємо скісною рисочкою: [ден']."
  - "Step-by-step transcription practice:
    яблуко → [йáблуко] (я at start = [йа])
    воля → [вóл'а] (я after consonant = softening)
    щастя → [шчáс'т'а] (щ = [шч], тя = [т'а])
    об'їжджати → [обйіж:áти] (ї after ' = [йі], жд → [ж:])
    More examples with increasing complexity."
  - "Common transcription mistakes learners make:
    — Forgetting that я/ю/є = two sounds at word start.
    — Writing щ as one sound instead of [шч].
    — Forgetting to mark м'якість.
    — Confusing наголос placement.
    Practice exercise: transcribe 8-10 words, check against model answers."
- section: "Підсумок: ваш фонетичний словник (Summary: your phonetics vocabulary)"
  words: 300
  points:
  - "Complete metalanguage glossary — all terms from this module collected:
    фонетика, графіка, орфоепія, звук, літера, фонема,
    голосний, приголосний, дзвінкий, глухий, сонорний,
    твердий, м'який, пом'якшений, наголос, наголошений,
    ненаголошений, транскрипція, склад, орфоепічна помилка,
    свистячий, шиплячий, губний, йотований."
  - "Self-check in Ukrainian: Дайте відповіді на запитання:
    1. Скільки звуків в українській мові? Скільки літер?
    2. Які звуки називаємо голосними? Скільки їх?
    3. Чим дзвінкі приголосні відрізняються від глухих?
    4. Що таке сонорні приголосні? Назвіть їх.
    5. Запишіть фонетичною транскрипцією: день, яма, щастя."
  - "Preview of next module: Будова слова (Word Structure) —
    корінь, префікс, суфікс, закінчення, основа.
    The metalanguage bridge continues: once you can name sounds,
    you are ready to name the parts of words."
vocabulary_hints:
  required:
  - "фонетика (phonetics — the study of speech sounds)"
  - "звук (sound — what we hear and pronounce)"
  - "літера (letter — what we see and write)"
  - "фонема (phoneme — abstract sound unit that distinguishes meaning)"
  - "голосний (vowel — sound made with voice only)"
  - "приголосний (consonant — sound made with obstruction)"
  - "дзвінкий (voiced — consonant produced with voice + noise)"
  - "глухий (voiceless — consonant produced with noise only)"
  - "сонорний (sonorant — consonant where voice dominates over noise)"
  - "твердий (hard — non-palatalized consonant)"
  - "м'який (soft — palatalized consonant)"
  - "наголос (stress — emphasized pronunciation of a syllable)"
  - "наголошений (stressed — syllable bearing the stress)"
  - "ненаголошений (unstressed — syllable without stress)"
  - "транскрипція (transcription — phonetic notation in square brackets)"
  - "склад (syllable)"
  recommended:
  - "графіка (graphics — the writing system)"
  - "орфоепія (orthoepy — rules of literary pronunciation)"
  - "орфографія (orthography — rules of correct spelling)"
  - "пом'якшений (partially softened consonant)"
  - "йотований (iotated — letters я, ю, є, ї that can represent two sounds)"
  - "свистячий (sibilant — whistling consonant: з, ц, с, дз)"
  - "шиплячий (hushing consonant: ж, ч, ш, дж)"
  - "губний (labial — consonant formed with lips: б, п, в, м, ф)"
  - "орфоепічна помилка (pronunciation error)"
  - "вільний наголос (free stress — can fall on any syllable)"
  - "рухомий наголос (mobile stress — shifts between word forms)"
  - "мовознавство (linguistics)"
activity_hints:
- type: quiz
  focus: "Classify sounds: голосний чи приголосний? дзвінкий чи глухий?"
  items: 8
- type: match-up
  focus: "Match Ukrainian phonetic terms to their definitions (e.g., дзвінкий — голос + шум)"
  items: 8
- type: fill-in
  focus: "Complete phonetic transcription of words (fill in missing sounds/marks)"
  items: 6
- type: group-sort
  focus: "Sort consonants into дзвінкі / глухі / сонорні groups"
  items: 10
- type: mark-the-words
  focus: "In a passage, mark all сонорні приголосні (or all глухі, etc.)"
  items: 6
- type: error-correction
  focus: "Find and fix mistakes in phonetic transcriptions"
  items: 6
connects_to:
- "b1-002 (Будова слова — word structure metalanguage)"
- "b1-006 (Phonetics: assimilation — applies дзвінкий/глухий classification)"
- "b1-009 (Vowel alternations — applies наголос knowledge)"
prerequisites:
- "A2 completion (learner can read/write Ukrainian, knows basic grammar)"
grammar:
- "Звуки vs літери — 33 letters, 38 sounds, and why they differ"
- "Голосні: 6 sounds, 10 letters, йотовані букви (я, ю, є, ї)"
- "Приголосні classification: дзвінкі/глухі pairs, сонорні, свистячі/шиплячі/губні"
- "Приголосні classification: тверді/м'які pairs, пом'якшені"
- "Наголос: вільний і рухомий, meaning-distinguishing function"
- "Фонетична транскрипція rules and notation"
register: науково-навчальний
references:
- title: "Заболотний Grade 5, p.73-77"
  notes: "Core фонетика chapter: звуки/літери, транскрипція rules, м'які/тверді."
- title: "Авраменко Grade 5, p.75-77"
  notes: "Тверді/м'які/пом'якшені distinction, дзвінкі/глухі pairs with dialogue."
- title: "Литвінова Grade 5, p.104-130"
  notes: "Comprehensive phonetics chapter: звуки мовлення, голосні/приголосні,
    дзвінкі/глухі pairs table, сонорні/свистячі/шиплячі/губні groups,
    тверді/м'які with м'який знак, ненаголошені е/и spelling rules."
- title: "Голуб Grade 5, p.66"
  notes: "Poetic framing of phonetics: 'Звуки — це щось надзвичайно своєрідне в мові.'"

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Звуки і букви
**Module:** metalanguage-sounds | **Phase:** B1.1 [Metalanguage Bridge]
**Textbook grades searched:** 1, 2, 3, 5

---

## Що вивчає фонетика? (What does phonetics study?)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 24
> ЗВУКИ. ГОЛОСНІ І ПРИГОЛОСНІ
> Ти вимовляєш різні звуки: голосні і приголосні. 
> Голосні звуки утворюються за допомогою голосу.
> Голосні почуєш в пісні,
> І у темному у лісі, 
> І коли дивуєшся,
> І коли милуєшся.
> Легко вимовляються, 
> Весело співаються! 
> Прочитай. Назви букви, які позначають голосні звуки.
> ал – ам – ан 
> ла – ма – на 
> ул – ум – ун
> ол – ом – он 
> ло – мо – но 
> лу – му – ну
>  
> Приголосні звуки утворюються 
> за допомогою голосу і шуму.
> Приголосні деренчать
> І тихенько шелестять, 
> Голосно свистя

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> ЗМІСТ
> ЗВУКИ І БУКВИ
> § 1. Звуко-буквений склад слова................................................................ 4
> § 2. Дзвінкі приголосні звуки в кінці слова і складу............................. 10
> § 3. Апостроф............................................................................................ 12
> § 4. Наголос................................................................................................. 14
> § 5. Поділ слів на склади..................................................

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> Частини  мови
> У розділі ти будеш вивчати:
> ІМЕННИКИ
> хто? що?
> який? яка? 
> яке? які?
> що робить? 
> що роблять?
> скільки?  
> котрий?
> ЧИСЛІВНИКИ
> ДІЄСЛОВА
> ПРИКМЕТНИКИ

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 71
> Фонетика. Графіка.
> Орфоепія. Орфографія
> Фонетика (від грец. phonetikos – звуковий) – це розділ 
> мовознавства, що вивчає звуковий склад мови.
> Графіка (від грец. grapho – пишу) – це розділ мово­
> знавства, що вивчає систему умовних знаків для передач­і 
> звуків на письмі.
> Орфоепія (від грец. orthos – правильний, epos – мова, 
> мовлення) – це розділ мовознавства, що вивчає правила 
> літературної вимови.
> Орфографія (від грец. orthos – правильний, grapho – 
> пишу) – це розділ мовознавства, що вивчає пр

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 29
> ЗВУКОВИЙ СКЛАД СЛОВА
> ЯК ЗРОБИТИ 
> ЗВУКОВИЙ АНАЛІЗ СЛОВА
> 1. Визначаю в слові 
> голосні звуки.
> М А М А
> М А М А
> 4. Позначаю 
> приголосні звуки. 
> М А М А
> 2. Ділю слово 
> на склади. 
> М А М А
> 3. Ставлю наголос. 
> Знайди слово — підпис до малюнка.
> Зроби звуковий аналіз слів.
>  
> ко|са 
> колос 
> ласка
>  
> каска 
> молоко 
> маска
>  
> Правда чи неправда?
> Прочитай або послухай речення. 
>  Ганна любить молоко.
>  Мама питиме какао.
>  Ганна їсть манну кашу.
>  Собака Лоло їсть ковбасу.
>  Лоло любить солому.
> 1
> 2

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> Позначення м’якості 
> приголосних буквами..............................................................................30
> Буквосполучення ьо, йо..........................................................................32
> Подовжені м’які приголосні звуки...........................................................35
> Дзвінкі та глухі приголосні звуки............................................................40
> Апостроф..................................................................................

## Голосні звуки (Vowel sounds)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 24
> ЗВУКИ. ГОЛОСНІ І ПРИГОЛОСНІ
> Ти вимовляєш різні звуки: голосні і приголосні. 
> Голосні звуки утворюються за допомогою голосу.
> Голосні почуєш в пісні,
> І у темному у лісі, 
> І коли дивуєшся,
> І коли милуєшся.
> Легко вимовляються, 
> Весело співаються! 
> Прочитай. Назви букви, які позначають голосні звуки.
> ал – ам – ан 
> ла – ма – на 
> ул – ум – ун
> ол – ом – он 
> ло – мо – но 
> лу – му – ну
>  
> Приголосні звуки утворюються 
> за допомогою голосу і шуму.
> Приголосні деренчать
> І тихенько шелестять, 
> Голосно свистя

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 9
> ГОЛОСНІ ТА ПРИГОЛОСНІ ЗВУКИ
> 25.	
> Прочитай без букви «ща».
> щ щ г о щ щ л о щ с щ н і щ щ з щ в у щ к и щ
> Під час вимовляння голосних звуків повітря вільно прохо-
> дить через рот, не натрапляючи на перешкоди. Голосні 
> звуки утворюються за допомогою голосу.
> 26.	
> 1.	 Прочитай лічилку і спиши, вставляючи пропущені букви.
> Х  д  л     кв  чк  
> к  л     к  л  чк  .
> В  д  л     д  т  ч  к
> б  л     кв  т  ч  к!   Квок!
> о и а о а
> о о і о а
> о и а і о о
> і я і о о
> 2.	 Де використовують лічилки? Розкажи лічил

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 80
> Правильно вимовляю, наголошую, записую слова 
> 	 	
> 1   Порівняйте схеми слів і написання.
> 2   Утвори і запиши слова.
> 3   Знайди в орфоепічному словнику і випиши кілька слів зі звуками 
> [дж], [дз], [дз’].
> 	
>   Який звук передається на письмі за допомогою буквосполучення 
> дж? Які звуки передаються на письмі за допомогою буквосполу-
> чення дз?
> 	
>   Вимов ці слова правильно. За потреби звертайся до орфоепічного 
> словника.
> 	
>   Підкресли сполучення букв, яке позначає звуки [дж], [дз], [дз’].

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 110
> Фонетика. Графіка. Орфоепія. Орфографія. Голосні та приголосні звуки
> АААААА ООО УУУ
> Голосні та приголосні звуки
> Вправа 165
> 1. Розгляньте фото . Що на ньому зображено?
> 2. Вимовте протяжно пари звуків: 
> [у] — [в], [і] — [й], [е] — [ж].
> 3. Поміркуйте, чому не всі звуки можна проспівати .
> 4. Пригадайте, які звуки належать до голосних, 
> а  які до приголосних .
> 5. Яких звуків, на вашу думку, більше в українській 
> мові  — голосних чи приголосних?
> Звуки мовлення вимовляємо за допомогою голосу та шум

> **Source:** unknown, Grade 1
> **Score:** 0.33
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
> **Score:** 0.33
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

## Приголосні звуки: дзвінкі та глухі (Consonants: voiced and voiceless)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 24
> ЗВУКИ. ГОЛОСНІ І ПРИГОЛОСНІ
> Ти вимовляєш різні звуки: голосні і приголосні. 
> Голосні звуки утворюються за допомогою голосу.
> Голосні почуєш в пісні,
> І у темному у лісі, 
> І коли дивуєшся,
> І коли милуєшся.
> Легко вимовляються, 
> Весело співаються! 
> Прочитай. Назви букви, які позначають голосні звуки.
> ал – ам – ан 
> ла – ма – на 
> ул – ум – ун
> ол – ом – он 
> ло – мо – но 
> лу – му – ну
>  
> Приголосні звуки утворюються 
> за допомогою голосу і шуму.
> Приголосні деренчать
> І тихенько шелестять, 
> Голосно свистя

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 62
> ДЗвІнкІ та ГЛУХІ ПриГоЛоснІ ЗвУки
> Вимов звуки, які позначають виділені букви. Які з них ти ви-
> мовляєш за допомогою голосу і шуму, а які — тільки шуму? 
> жабка — шапка
> злива — слива
> ґава — кава
> дуб — суп
> казка — каска
> гуска — хустка
> Дзвінкі приголосні утворюються за допомогою голо - 
> су 
>  і шуму 
> , глухі — за допомогою шуму 
> . 
>  
> Я знаю, що деякі дзвінкі і глухі

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Що вивчає фонетика? (What does phonetics study?)` (~600 words)
- `## Голосні звуки (Vowel sounds)` (~550 words)
- `## Приголосні звуки: дзвінкі та глухі (Consonants: voiced and voiceless)` (~700 words)
- `## Приголосні звуки: тверді та м'які (Consonants: hard and soft)` (~700 words)
- `## Наголос (Stress)` (~600 words)
- `## Фонетична транскрипція (Phonetic transcription)` (~550 words)
- `## Підсумок: ваш фонетичний словник (Summary: your phonetics vocabulary)` (~300 words)
- `## Summary` (~150 words)

Each section should follow the word budget specified. The total must reach 4000 words minimum.

---

## Content Rules

Bridge modules: teach grammar metalanguage. English scaffolding for abstract concepts. Parenthetical equivalents for new terms. Sentences max 30 words.

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

### Writing Quality
- Every paragraph: ONE clear point, logical flow to the next
- Vary sentence length (short for emphasis, medium for explanation, long for examples)
- Use callout boxes (:::tip, :::caution, :::note) sparingly — max 3 per module
- Dialogues: natural, not stilted. Real situations, real responses.
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

**Required:** фонетика (phonetics — the study of speech sounds), звук (sound — what we hear and pronounce), літера (letter — what we see and write), фонема (phoneme — abstract sound unit that distinguishes meaning), голосний (vowel — sound made with voice only), приголосний (consonant — sound made with obstruction), дзвінкий (voiced — consonant produced with voice + noise), глухий (voiceless — consonant produced with noise only), сонорний (sonorant — consonant where voice dominates over noise), твердий (hard — non-palatalized consonant), м'який (soft — palatalized consonant), наголос (stress — emphasized pronunciation of a syllable), наголошений (stressed — syllable bearing the stress), ненаголошений (unstressed — syllable without stress), транскрипція (transcription — phonetic notation in square brackets), склад (syllable)
**Recommended:** графіка (graphics — the writing system), орфоепія (orthoepy — rules of literary pronunciation), орфографія (orthography — rules of correct spelling), пом'якшений (partially softened consonant), йотований (iotated — letters я, ю, є, ї that can represent two sounds), свистячий (sibilant — whistling consonant: з, ц, с, дз), шиплячий (hushing consonant: ж, ч, ш, дж), губний (labial — consonant formed with lips: б, п, в, м, ф), орфоепічна помилка (pronunciation error), вільний наголос (free stress — can fall on any syllable), рухомий наголос (mobile stress — shifts between word forms), мовознавство (linguistics)

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

## Output Format

Write in Markdown. Use:
- `## Section Title` for main sections
- `### Subsection` for subsections within a section
- `**bold**` for Ukrainian words being taught
- Tables for paradigms (conjugation, declension)
- `:::tip` / `:::caution` / `:::note` for callout boxes
- `:::quiz` / `:::fill-in` / `:::match-up` / `:::group-sort` / `:::true-false` for exercises (using the DSL formats above)

Do NOT write MDX component syntax or JSON. Plain Markdown with the exercise DSL blocks described above.

Begin writing now. Start with the first section heading.
