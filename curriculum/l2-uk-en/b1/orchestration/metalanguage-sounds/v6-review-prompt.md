# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 1: Звуки і букви (B1, B1.1 [Metalanguage Bridge])
**Writer:** Claude Opus
**Word target:** 4000

## Plan (source of truth)

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

## Generated Content

<generated_module_content>
<!-- TAB:Урок -->

## Що вивча́є фоне́тика? (What does phonetics study?)

«Скі́льки зву́ків у сло́ві «я́блуко»?» — запи́тує вчи́телька п'ятикла́сників. Хтось ка́же: шість. Хтось — сім. А правильна ві́дповідь — сім: [й], [а], [б], [л], [у], [к], [о]. Одна́ лі́тера «я» передає́ два зву́ки. Якщо́ ви вже зна́єте, чому́ так — віта́ємо, ви гото́ві до цього́ мо́дуля. Якщо ні — за́раз розберемо́ся.

You already speak Ukrainian. You read it, write it, hear the difference between «ліс» and «лис». But can you *name* what you hear? Can you explain *why* «я» sometimes equals one sound and sometimes two? This module is your **metalanguage bridge** (метамо́вний міст): you cross from intuitive knowledge to precise Ukrainian terminology. After this module, when a grammar book says «дзвінки́й при́голосний» or «ненаголо́шений склад», you will know exactly what it means — in Ukrainian.

### Три ро́зділи мовозна́вства про звуки

Ukrainian linguistics divides the study of sounds into three separate disciplines. Each has its own Greek-rooted name, and each answers a different question:

**Фонетика** (phonetics, від гре́цького *phonetikos* — звукови́й) — ро́зділ мовознавства (branch of linguistics), що вивчає звуковий склад мо́ви. Phonetics asks: *what sounds exist in the language, and how do speakers produce them?*

**Гра́фіка** (graphics, від грецького *grapho* — пишу́) — розділ мовознавства, що вивчає систе́му умо́вних знаків для переда́чі звуків на письмі́. Graphics asks: *how do we represent sounds with written symbols?*

**Орфое́пія** (orthoepy, від грецького *orthos* — правильний, *epos* — мо́влення) — розділ мовознавства, що вивчає правила літерату́рної вимо́ви. Orthoepy asks: *what is the correct way to pronounce words?*

A fourth discipline — **орфогра́фія** (orthography) — studies correct *spelling*, not pronunciation. We will return to it in later modules.

### Звук, літера, фоне́ма — three different things

This is the golden rule of Ukrainian phonetics, repeated in every Grade 5 textbook:

> «Ми чу́ємо і вимовля́ємо **звуки**, а ба́чимо і пи́шемо **лі́тери**.»

A **звук** (sound) is what you hear and produce. A **літера** (letter) is what you see and write. They are not the same thing. Ukrainian has **33 літери** in its alphabet but **38 звуків** in its sound system. Why the mismatch? Several reasons:

- The letters **я**, **ю**, **є**, **ї** can each represent *two* sounds (more on this in the next section).
- The letter **щ** represents two sounds together.
- The letters **ь** (м'яки́й знак) and **'** (апо́стро́ф) produce no sound at all — they signal how neighbouring consonants behave.

There is also a third concept: **фонема** (phoneme). A фонема is the *abstract* sound unit that distinguishes meaning. Consider the word «горо́х» (peas). Different speakers may pronounce the «г» slightly differently — louder, softer, with more breath — but all these variations belong to one фонема. The concrete sound a person produces in a given moment is a звук. The abstract category that makes «горох» different from «по́рох» (gunpowder) — that is a фонема.

For everyday grammar work at B1, the distinction between звук and фонема is rarely critical. But when you read advanced Ukrainian linguistics texts or encounter terms like «фонемати́чний при́нцип орфогра́фії», you will know what they mean.

:::quiz
title: "Звук, літера чи фонема?"
---
- q: "Що ми чуємо і вимовляємо?"
  o: ["звуки", "літери", "фоне́ми"]
  a: 0
- q: "Що ми бачимо і пишемо?"
  o: ["літери", "звуки", "фонеми"]
  a: 0
- q: "Скільки лі́тер в украї́нському алфа́ві́ті?"
  o: ["33", "38", "42"]
  a: 0
- q: "Скільки звуків в украї́нській мо́ві?"
  o: ["38", "33", "26"]
  a: 0
- q: "Яка літера познача́є два звуки на поча́тку слова́?"
  o: ["я", "а", "м"]
  a: 0
- q: "Яки́й розділ мовознавства вивчає звуковий склад мови?"
  o: ["фонетика", "графіка", "орфоепія"]
  a: 0
- q: "Абстра́ктна одини́ця, що розрізня́є зна́чення слів — це..."
  o: ["фонема", "звук", "літера"]
  a: 0
- q: "Який розділ вивчає правила літературної вимови?"
  o: ["орфоепія", "орфографія", "фонетика"]
  a: 0
:::

## Голосні́ звуки (Vowel sounds)

Спро́буйте проспіва́ти звук «а» — ле́гко, пра́вда? А тепе́р проспіва́йте «б». Не виходить. Са́ме так — че́рез спів — украї́нські першокла́сники вча́ться відрізня́ти голосні від при́голосних. Голосні звуки «легко вимовля́ються, ве́село співа́ються», як каже підру́чник пе́ршого кла́су.

### Шість звуків, де́сять літер

**Голосні звуки** (vowel sounds) утво́рюються го́лосом, без перешко́ди. Пові́тря ві́льно прохо́дить через рот. In Ukrainian there are exactly **6 голосни́х звуків**: [а], [о], [у], [е], [и], [і]. But the alphabet has **10 голосних літер**: а, о, у, е, и, і, **я**, **ю**, **є**, **ї**. The extra four — я, ю, є, ї — are called **йото́вані літери** (iotated letters), and their behaviour depends on position.

### Ко́ли йото́вана літера = два звуки

The letters я, ю, є, ї represent two sounds in three positions:

**1. На початку слова** (at the beginning of a word):
- **я́ма** (pit) → [й] + [а] = two sounds
- **юна́к** (young man) → [й] + [у] = two sounds
- **є́дність** (unity) → [й] + [е] = two sounds
- **їжа́к** (hedgehog) → [й] + [і] = two sounds (ї *always* = two sounds)

**2. Пі́сля голосно́го** (after a vowel):
- **мрі́я** (dream) → ...і + [й] + [а]
- **краює** (cuts) → ...а + [й] + [у] + [й] + [е]

**3. Після апо́стро́фа** (after an apostrophe):
- **п'ять** (five) → п + [й] + [а] + ...
- **об'є́м** (volume) → ...б + [й] + [е] + ...

### Коли йотована літера = оди́н звук + пом'я́кшення

After a consonant *without* an apostrophe, я, ю, є, і do not split into two sounds. Instead, they signal that the preceding consonant becomes soft:

- **ля́ля** (doll) → [л'] + [а] + [л'] + [а] — the «я» softens «л» and contributes only [а]
- **любо́в** (love) → [л'] + [у] + ... — the «ю» softens «л» and contributes only [у]
- **лід** (ice) → [л'] + [і] + ... — the «і» softens «л» and contributes only [і]

This is one of the most important patterns in Ukrainian phonetics. It explains why the same letter «я» behaves differently in «яма» (two sounds) and «ляля» (one sound + softening).

### Ненаголо́шені голосні — why spelling gets tricky

When a vowel is unstressed (**ненаголошений**), its pronunciation shifts. Specifically, [е] and [и] in unstressed positions sound almost identical. This is why Ukrainian schoolchildren — native speakers! — study **право́пис ненаголо́шених [е], [и]** (spelling of unstressed [е] and [и]).

The rule: change the word form to put the doubtful vowel under stress.

- **зеле́ний** — is the first vowel «е» or «и»? Check: **зе́лень** — the stress falls on «е», confirming the spelling.
- **крило́** — «и» or «е»? Check: **кри́ла** — the stress falls on «и», confirming.
- **о́сені** — «е» or «и»? Check: **о́сінь** — the vowel alternates with [і] in a closed syllable, so we write «е» in the open syllable.

This rule will become essential when we study **чергува́ння голосних** (vowel alternations) later in B1.

:::match-up
title: "З'єдна́й те́рмін із ви́значенням"
---
- left: "голосни́й звук"
  right: "утво́рюється голосом, без перешкоди"
- left: "приголосний звук"
  right: "утворюється з у́частю шу́му або́ перешкоди"
- left: "йотована літера"
  right: "мо́же познача́ти два звуки: я, ю, є, ї"
- left: "фонетика"
  right: "розділ мовознавства, що вивчає звуки"
- left: "графіка"
  right: "розділ мовознавства, що вивчає знаки для передачі звуків"
- left: "орфоепія"
  right: "правила літературної вимови"
- left: "фонема"
  right: "абстрактна одиниця, що розрізняє значення слів"
- left: "ненаголошений"
  right: "склад, на який не па́дає на́голос"
:::

## При́голосні звуки: дзвінкі́ та глухі́ (Consonants: voiced and voiceless)

Прикладі́ть доло́ню до го́рла і скажі́ть «ззззз». Відчува́єте вібра́цію? А тепер скажіть «ссссс» — вібра́ція зни́кла. Ви що́йно відчу́ли різни́цю між **дзвінки́м** (voiced) і **глухи́м** (voiceless) при́голосним. The vibration you felt is your vocal cords at work — that is **го́лос** (voice).

### Парні́ приголосні

**Дзвінкі приголосні** (voiced consonants) утворюються за допомо́гою го́лосу і шуму. **Глухі приголосні** (voiceless consonants) утворюються за допомогою лише́ шуму. Most Ukrainian consonants form neat voiced–voiceless pairs:

| Дзвінкі | [б] | [д] | [ґ] | [г] | [з] | [ж] | [дж] | [дз] |
|---------|-----|-----|-----|-----|-----|-----|------|------|
| **Глухі** | [п] | [т] | [к] | [х] | [с] | [ш] | [ч]  | [ц]  |

Each pair shares the same place and manner of articulation — the only difference is the presence or absence of voice. Compare:

- **жа́бка — ша́пка**: [ж] is дзвінкий, [ш] is глухи́й
- **зли́ва — сли́ва**: [з] is дзвінкий, [с] is глухий
- **ґа́ва — ка́ва**: [ґ] is дзвінкий, [к] is глухий
- **дуб — суп**: [д] is дзвінкий... and it *stays* дзвінкий at the end of the word

That last point is critical. In Ukrainian, **дзвінкі приголосні do not become глухі at the end of a word**. The word «дуб» (oak) is pronounced [дуб], not *[дуп]. The word «мед» (honey) is [мед], not *[мет]. This is a fundamental difference between Ukrainian and languages like Russian or German, where final devoicing is standard. If you hear someone say *[дуп] or *[хл'іп] instead of [дуб] or [хліб], that is an **орфоепі́чна по́ми́лка** (pronunciation error).

### Соно́рні приголосні — a special group

Not all consonants fit neatly into the дзвінкий/глухий system. Ukrainian has a group of consonants called **сонорні** (sonorants), where голос переважа́є над шу́мом (voice dominates over noise). These are:

**[в], [м], [н], [л], [р]** and their soft pairs [м'], [н'], [л'] + **[й]**

Ukrainian textbooks teach a mnemonic to remember them: **МіНеРаЛоВиЙ** — the first letters of ко́жного соно́рного: **М**, **Н**, **Р**, **Л**, **В**, **Й**. Сонорні are neither дзвінкі nor глухі — they form their own third category.

### Класифіка́ція за мі́сцем тво́рення

Beyond voiced/voiceless, Ukrainian consonants are also classified by *where* in the mouth they are formed (**мі́сце творення**). Three important groups:

**Свистя́чі** (sibilants — "whistling" consonants): [з], [ц], [с], [дз] — the airstream creates a whistling sound through a narrow gap near the teeth.

**Шипля́чі** (hushing consonants): [ж], [ч], [ш], [дж] — the airstream creates a broader, "shushing" sound with the tongue pulled back.

**Губні́** (labials): [б], [п], [в], [м], [ф] — formed with the lips.

Why do these groups matter? Because spelling rules throughout B1 depend on them. When you encounter **уподі́бнення приголосних** (consonant assimilation) in Module 6, you will need to know whether a consonant is свистя́чий or шипля́чий to predict how it changes. The classification you learn here is the foundation.

### Чита́ння: знайді́ть дзвінкі, глухі та сонорні

Read this short passage and try to classify the highlighted consonants:

> Мале́нька **Б**ори́вка **д**уже́ лю́бить **м**у́зику. Кожного **в**ечора вона́ **с**ідає **б**іля **в**ікна і **с**лухає, як **в**ітер **г**ра́є на **л**истках **к**лині́в. «Це мій **н**айкращий **к**онцерт!» — **к**аже **Б**оривка **м**амі. А **м**ама **с**міється: «**Т**и — **с**правжня **м**узикантка!»

Let us classify several consonants from this passage:

- **«безпе́ка»** [безпека]: [б] — дзвінкий, [з] — дзвінкий, [п] — глухий, [к] — глухий
- **«школярі́»** [школ'ар'і]: [ш] — глухий (шиплячий), [к] — глухий, [л'] — соно́рний, [р'] — сонорний
- **«му́зику»**: [м] — сонорний (губни́й), [з] — дзвінкий (свистячий), [к] — глухий
- **«ві́тер»**: [в] — сонорний, [т] — глухий, [р] — сонорний

Notice how сонорні cluster heavily in words about music and nature — [м], [л], [р], [н] give Ukrainian its melodic quality.

:::group-sort
title: "Розпо́діли приголосні на три гру́пи"
---
groups:
  - name: "Дзвінкі"
    items: ["[б]", "[д]", "[з]", "[ж]"]
  - name: "Глухі"
    items: ["[п]", "[т]", "[с]", "[ш]", "[к]", "[ц]"]
  - name: "Сонорні"
    items: ["[м]", "[н]", "[л]", "[р]", "[в]", "[й]"]
:::

## Приголосні звуки: тверді та м'які́ (Consonants: hard and soft)

«Лис» і «ліс» — два рі́зних слова. Одна літера відрізня́ється: «и» або «і». Але́ спра́вжня різни́ця не в лі́терах — вона у зву́ках. У слові «лис» (fox) приголосний [л] — **тверди́й** (hard). У слові «ліс» (forest) приголосний [л'] — **м'який** (soft). The meaning changes entirely because of this single phonetic feature.

### Як утворюються м'які приголосні

**Твердий приголосний** (hard consonant) is produced when the tongue touches the teeth or alveolar ridge in its neutral position. **М'який приголосний** (soft/palatalized consonant) is produced when the tongue simultaneously rises toward the hard palate (піднебі́ння). This additional tongue movement changes the quality of the sound.

More examples of minimal pairs — words where the *only* difference is hard vs. soft:

- **рад** (glad) vs **ряд** (row) — [р] vs [р']: wait, «р» is always hard in Ukrainian. Let us use a better pair:
- **кон** (an older form) vs **кінь** (horse) — [н] vs [н']
- **ніс** (carried) vs **ніс** (nose) — same spelling, but context determines the form
- **сад** (garden) vs **сядь** (sit down!) — [с] vs [с'], [д] vs [д']

### Як познача́ється м'я́кість на письмі

Ukrainian uses two strategies to show that a consonant is soft:

**1. М'який знак (ь)** — the soft sign has no sound of its own. It signals that the preceding consonant is м'який:
- **день** (day) → [ден'] — the [н] becomes soft
- **кінь** (horse) → [к'ін'] — both [к'] and [н'] are affected
- **сіль** (salt) → [с'іл'] — both [с'] and [л'] are soft

**2. Літери я, ю, є, і after a consonant** (without an apostrophe):
- **ляк** (fright) → [л'] + [а] + [к] — the «я» softens [л]
- **нюх** (sense of smell) → [н'] + [у] + [х] — the «ю» softens [н]
- **тінь** (shadow) → [т'] + [і] + [н'] — the «і» softens [т], and the «ь» softens [н]

In phonetic transcription, softness is always marked with a special symbol ['] after the consonant: [д'], [т'], [л'], [н'], [с'], [з'], [ц'], [дз'].

### Тверді, м'які, і пом'я́кшені — три катего́рії

Ukrainian phonetics distinguishes not two, but *three* categories of consonant hardness. This is where things get interesting:

**Тверді** (hard) — the consonant's normal, non-palatalized form: [д], [т], [с], [л], [н], etc.

**М'які** (soft) — consonants that have a full soft pair. These are the зубні́/свистячі consonants that can be either hard or soft depending on the word:
- [д] — [д'], [т] — [т'], [з] — [з'], [с] — [с'], [ц] — [ц'], [дз] — [дз'], [л] — [л'], [н] — [н']

**Пом'якшені** (partially softened) — consonants that do *not* have a full soft pair but become slightly palatalized in certain phonetic environments. This applies to губні (labials), задньоязико́ві (velars), and шиплячі (hushing consonants):
- [б] in **бі́лий** (white) — the [б] before [і] is пом'я́кшений, not fully м'який
- [к] in **кіт** (cat) — the [к] before [і] is пом'якшений
- [ж] in **жі́нка** (woman) — the [ж] before [і] is пом'якшений

The key distinction: **м'які** consonants (like [с'] in «сіль» or [н'] in «день») have a genuine soft counterpart that changes the sound fundamentally. **Пом'якшені** consonants (like [б] before [і] or [к] before [і]) are only *slightly* affected by their phonetic environment — they do not have a true soft pair.

:::tip
Запам'ята́йте: зубні приголосні [д], [т], [з], [с], [ц], [дз], [л], [н] ма́ють повноці́нну м'яку́ па́ру. Губні [б], [п], [в], [м], [ф], задньоязикові [ґ], [к], [х] та шиплячі [ж], [ч], [ш] — лише пом'я́кшуються пе́ред [і].
:::

### Класифікація: які́ приголосні — за́вжди́ тверді?

Not every consonant can be soft. Here is the full picture:

**Завжди тверді** (always hard — no soft pair): [б], [п], [в], [м], [ф], [г], [ґ], [к], [х], [ж], [ч], [ш], [дж], [р]. These can be *пом'якшені* before [і], but never fully м'які.

**Завжди м'який** (always soft): [й] — this sound is inherently palatalized.

**Тверді/м'які па́ри** (hard/soft pairs):
[д]–[д'], [т]–[т'], [з]–[з'], [с]–[с'], [ц]–[ц'], [дз]–[дз'], [л]–[л'], [н]–[н']

These eight pairs are the heart of the тверді/м'які system. When you see «ь» after a consonant or a йотована letter after a consonant without apostrophe, check: is the consonant from this list? If yes, it becomes fully м'який. If not, it is merely пом'якшений.

Consider the word **пі́сня** (song) → [п'іс'н'а]. Here, [с'] before [н'] becomes fully м'який — this is **уподібнення за м'я́кістю** (assimilation of softness). The dental [с], which has a true soft pair, fully assimilates to the softness of the following [н']. This is different from a губний like [б] in «білий», which has no true soft pair and can only be пом'якшений.

:::fill-in
title: "Запиші́ть фонети́чну транскри́пцію"
---
- sentence: "день → [___]"
  answer: "ден'"
- sentence: "яма → [___]"
  answer: "йама"
- sentence: "кінь → [___]"
  answer: "к'ін'"
- sentence: "лю́ди → [___]"
  answer: "л'уди"
- sentence: "п'ять → [___]"
  answer: "пйат'"
- sentence: "ща́стя → [___]"
  answer: "шчас'т'а"
:::

## Наголос (Stress)

Скажіть вго́лос: «замок». А тепер — «замок». Звучи́ть одна́ково? Ні, і ось чому: **зáмок** (castle) і **замóк** (lock) — два різних слова. Різниця — лише в тому́, на який **склад** (syllable) падає **наголос** (stress).

### Ві́льний і рухо́мий

**Наголос** — це поси́лена вимо́ва одного зі складів. The stressed syllable is louder, longer, and clearer than the others. Ukrainian stress has two key properties:

**Вільний наголос** (free stress) — the stress can fall on *any* syllable of a word. Compare:
- **ó**зеро́ (lake) — stress on the first syllable
- ка**ли́**на (viburnum) — stress on the second syllable
- моло**кó** (milk) — stress on the third syllable

This differs from languages with fixed stress: Polish always stresses the penultimate syllable, French stresses the final one. Ukrainian has no such rule — stress position must be learned for each word individually.

**Рухомий наголос** (mobile stress) — the stress can *shift* between different forms of the same word:
- **рý**ки (hands, nominative plural) vs ру**ки́** (hand, genitive singular)
- **нó**ги (legs, nominative plural) vs но**ги́** (leg, genitive singular)
- **ві**кно (window, nominative) vs вікóн (windows, genitive plural) — wait, let us use a clearer example:
- **сéстри** (sisters, nominative plural) vs сес**три́** (sisters, genitive plural)

This mobility means that the same word can have different stress in different grammatical forms. A learner who memorizes stress for the nominative may be surprised when the genitive sounds different.

### Наголос змі́нює значення

Some words differ only in stress — these are called **омо́графи** (homographs):

- **зáмок** (castle) vs **замóк** (lock)
- **óбід** (rim) vs **обíд** (lunch)
- **прúклад** (example) vs **приклáд** (rifle butt)
- **áтлас** (atlas, book of maps) vs **атлáс** (satin fabric)
- **дóро́га** (road) vs **дорóга** (dear, feminine)

When you put the stress on the wrong syllable, you commit an **орфоепічна помилка** (pronunciation error). Sometimes the error changes the meaning entirely; sometimes it just sounds unnatural. Either way, stress matters.

### Наголо́шений і ненаголошений склад

Every word has exactly one **наголошений склад** (stressed syllable). All other syllables are **ненаголошені** (unstressed).

In the word **кали́на** [калина]:
- «ка» — ненаголошений склад
- «ли» — **наголошений склад**
- «на» — ненаголошений склад

In the word **учи́тель** [учител']:
- «у» — ненаголошений
- «чи» — ненаголошений
- «тель» — **наголошений**

How do you know where the stress falls? For many words, you simply learn it through exposure. For doubtful cases, consult an **орфоепі́чний словни́к** (orthoepic dictionary) — a dictionary that marks stress for every word. Online tools like goroh.pp.ua serve the same function.

### Чому наголос важли́вий для B1

Stress is not just about pronunciation — it drives grammar. In upcoming modules, you will study **чергування голосних** (vowel alternations): patterns like **рік** → **рóку** (year, nom. → gen.), **кінь** → **коня́́** (horse, nom. → gen.), **сіль** → **сóлі** (salt, nom. → gen.). In each case, the vowel changes *because* the stress shifts. If you understand наголос now, these alternations will make perfect sense later. If you skip this concept, they will seem arbitrary and chaotic.

:::caution
Не плу́тайте «наголос» і «інтона́ція»! **Наголос** — це ви́ділення одного скла́ду в слові. **Інтонація** — це мело́дика ці́лого речення (пита́льне, окли́чне то́що). Ми вивча́ємо наголос.
:::

## Фонети́чна транскри́пція (Phonetic transcription)

«Запишіть фонети́чною транскри́пцією сло́во «щастя»,» — каже вчи́тель. У́чень пи́ше: *[щастя]*. Непра́вильно! Ukrainian phonetic transcription has strict rules — you cannot simply copy the word in brackets. The whole point is to show *sounds*, not letters.

### Правила транскри́пції

Ukrainian Grade 5 textbooks (Заболо́тний, p.74) list these rules:

**1.** За́пис беремо́ у **квадра́тні дужки́**: [калина]. Square brackets signal that you are writing sounds, not letters.

**2.** Ко́жен звук познача́ємо **окре́мою бу́квою**. No digraphs, no shortcuts.

**3.** **НЕ використо́вуємо** бу́кви я, ю, є, ї, ь, щ та вели́кі букви. These are *letter* symbols, not sound symbols. In transcription, я becomes [йа] or softens the preceding consonant; щ becomes [шч]; ь has no sound; great letters have no place because sounds do not have uppercase.

**4.** Позначаємо місце **на́голосу**: [подóрож].

**5.** М'якість при́голосного позначаємо **скісно́ю ри́сочкою** (apostrophe mark): [ден'], [л'убов].

**6.** Подо́вжений звук позначаємо двокра́пкою: [жит':а] (життя́), [знан':а] (знання́).

### Крок за кро́ком: як транскрибува́ти

Let us walk through several words, increasing in complexity:

**«во́ля»** (will, freedom):
- «в» → [в] — consonant sound
- «о» → [о] — vowel, and it bears the stress
- «л» + «я» → [л'] + [а] — «я» after a consonant softens it and contributes [а]
- Result: **[вóл'а]** — 4 sounds from 4 letters

**«яблуко»** (apple):
- «я» at the beginning → [й] + [а] — two sounds!
- «б» → [б], «л» → [л], «у» → [у], «к» → [к], «о» → [о]
- Result: **[йáблуко]** — 7 sounds from 6 letters

**«щастя»** (happiness):
- «щ» → [шч] — always two sounds
- «а» → [а], bearing stress
- «с» + «т» + «я» → [с'] + [т'] + [а] — «я» softens [т], and [с] assimilates softness from [т']
- Result: **[шчáс'т'а]** — 7 sounds from 5 letters

**«об'їжджа́ти»** (to travel around):
- «о» → [о], «б» → [б]
- «'» (apostrophe) → no sound, but signals that «ї» = [й] + [і]
- «ж» + «д» + «ж» → the combination «жд» before «ж» assimilates: [ж:]
- «а» → [а] bearing stress, «т» → [т], «и» → [и]
- Result: **[обйіж:áти]** — a complex word with assimilation

**«дзвіно́к»** (bell):
- «дз» → [дз] — one sound! (an affricate)
- «в» → [в], «і» → [і], «н» → [н], «о» → [о], «к» → [к]
- The stress falls on the second syllable: [дзв'інóк]
- Result: **[дзв'інóк]** — 6 sounds from 7 letters

### Типові помилки́

Learners consistently make these mistakes in transcription:

**Помилка 1:** Writing «я», «ю», «є» as single sounds at the start of a word. Remember: яма ≠ *[ама]. It is [йама].

**Помилка 2:** Writing «щ» as one sound. It is always [шч]. Щу́ка → [шчука], not *[щука].

**Помилка 3:** Forgetting to mark м'якість. «День» is [ден'], not *[ден]. That apostrophe mark changes the word entirely — without it, you are writing a different sound.

**Помилка 4:** Confusing наголос placement. Is «нови́й» → *[нóвий] or [нови́́й]? The stress falls on the final syllable: [новий]. Getting this wrong means getting the pronunciation wrong.

**Помилка 5:** Forgetting that «ь» is not a sound. «Кінь» has 3 sounds [к'ін'], not 4. The soft sign only modifies the preceding consonant.

:::true-false
title: "Правда чи непра́вда?"
---
- statement: "У слові «яма» три звуки."
  answer: false
- statement: "Літера «щ» завжди позначає два звуки."
  answer: true
- statement: "М'який знак (ь) позначає окре́мий звук."
  answer: false
- statement: "У транскрипції не вжива́ємо вели́ких букв."
  answer: true
- statement: "Наголос в українській мові завжди падає на пе́рший склад."
  answer: false
- statement: "Дзвінкі приголосні в кінці́ слова стають глухи́ми."
  answer: false
:::

<!-- mark-the-words exercise: the DSL doesn't have a mark-the-words type in the approved list, so using the closest equivalent -->

Now, look at this passage and identify all the **сонорні приголосні** sounds:

> «Мале́нький Миросла́в малю́є вели́кий мальовни́чий ра́нок. Він любить вирізня́ти відті́нки: вишне́вий, роже́вий, лимо́нний.»

The сонорні sounds here: [м] in «Маленький», «Мирослав», «малює», «мальовничий»; [р] in «Мирослав», «ранок», «рожевий», «вирізняти»; [л] in «Маленький», «малює», «мальовничий», «лимонний», «великий», «любить»; [н] in «Маленький», «мальовничий», «ранок», «Він», «вишневий», «лимонний», «вирізняти»; [в] in «великий», «Він», «відтінки», «вишневий», «вирізняти»; [й] in «Мирослав», «великий», «мальовничий», «вишневий», «рожевий», «лимонний».

Соно́рних — бі́льшість! This is characteristic of Ukrainian — its rich sonorant inventory gives the language its famous melodic quality.

Now find and fix the errors in these transcriptions:

:::quiz
title: "Знайди і ви́прав по́ми́лку в транскрипції"
---
- q: "«яблуко» запи́сано як [аблуко]. Яка помилка?"
  o: ["Пропу́щено [й] перед [а]", "Непра́вильний наголос", "Пропущено м'якість"]
  a: 0
- q: "«щука» записано як [щука]. Яка помилка?"
  o: ["«щ» тре́ба записа́ти як [шч]", "Пропущено наголос", "Пропущено м'якість"]
  a: 0
- q: "«день» записано як [ден]. Яка помилка?"
  o: ["Пропущено по́значку м'я́кості [']", "Неправильний голосний", "За́йва літера"]
  a: 0
- q: "«п'ять» записано як [пат']. Яка помилка?"
  o: ["Пропущено [й] після апострофа", "Неправильний наголос", "За́йвий звук"]
  a: 0
- q: "«їжак» записано як [іжа́к]. Яка помилка?"
  o: ["Пропущено [й] — «ї» завжди = [йі]", "Неправильний приголосний", "Зайва м'якість"]
  a: 0
- q: "«любов» записано як [лубов]. Яка помилка?"
  o: ["Пропущено м'якість [л'] — «ю» пом'я́кшує «л»", "Неправильний голосний", "Зайвий звук"]
  a: 0
:::

## Підсумок: ваш фонети́чний словник (Summary: your phonetics vocabulary)

You have covered substantial ground. Here is every metalanguage term from this module, collected in one place:

| Термін | Значення |
|--------|----------|
| **фонетика** | розділ мовознавства, що вивчає звуки |
| **графіка** | розділ мовознавства, що вивчає систему знаків на письмі |
| **орфоепія** | правила літературної вимови |
| **орфографія** | правила право́пису |
| **мовозна́вство** | linguistics — нау́ка про мо́ву |
| **звук** | те, що ми чуємо і вимовляємо |
| **літера** | те, що ми бачимо і пишемо |
| **фонема** | абстрактна одиниця, що розрізняє значення слів |
| **голосний** | звук, що утворюється голосом, без перешкоди |
| **приголосний** | звук, що утворюється з участю шуму |
| **дзвінкий** | приголосний, що утворюється голосом і шумом |
| **глухий** | приголосний, що утворюється лише шумом |
| **сонорний** | приголосний, де голос переважає над шумом |
| **твердий** | приголосний без палаталіза́ції |
| **м'який** | палаталізо́ваний приголосний |
| **пом'якшений** | частко́во палаталізований приголосний |
| **наголос** | посилена вимова одного складу |
| **наголошений** | склад, на який падає наголос |
| **ненаголошений** | склад без наголосу |
| **транскрипція** | фонетичний запис у квадра́тних дужка́х |
| **склад** | syllable — части́на слова з одни́м голосни́м |
| **йото́ваний** | літера, що може позначати два звуки (я, ю, є, ї) |
| **свистячий** | приголосний зі сви́стом: [з], [ц], [с], [дз] |
| **шиплячий** | приголосний із шипі́нням: [ж], [ч], [ш], [дж] |
| **губний** | приголосний, що утворюється губа́ми: [б], [п], [в], [м], [ф] |
| **орфоепічна помилка** | помилка у вимо́ві |

### Самопере́ві́рка — да́йте ві́дповіді на запита́ння:

1. Скільки звуків в українській мові? Скільки літер?
2. Які звуки назива́ємо голосни́ми? Скільки їх?
3. Чим дзвінкі приголосні відрізня́ються від глухи́х?
4. Що таке́ сонорні приголосні? Назві́ть їх.
5. Запишіть фонетичною транскрипцією: «день», «яма», «щастя».

*(Відповіді: 1 — 38 звуків, 33 літери. 2 — Звуки, що утворюються голосом без перешкоди; їх 6. 3 — Дзвінкі = голос + шум, глухі = лише шум. 4 — Приголосні, де голос переважає: [м], [н], [л], [р], [в], [й]. 5 — [ден'], [йама], [шчас'т'а].)*

### Що да́лі: Будо́ва слова

The metalanguage bridge continues. In the next module — **Будова слова** (Word Structure) — you will learn to name the parts of words: **ко́рінь** (root), **префікс** (prefix), **су́фікс** (suffix), **закі́нчення** (ending), **осно́ва** (stem). Once you can name sounds *and* word parts in Ukrainian, you have the full vocabulary to understand any grammar explanation written for native speakers. The bridge is almost complete.


<!-- TAB:Словник -->

### Обов'язкові слова — Required words

| Слово | Translation |
|-------|-------------|
| **фонетика** | phonetics — the study of speech sounds |
| **звук** | sound — what we hear and pronounce |
| **літера** | letter — what we see and write |
| **фонема** | phoneme — abstract sound unit that distinguishes meaning |
| **голосний** | vowel — sound made with voice only |
| **приголосний** | consonant — sound made with obstruction |
| **дзвінкий** | voiced — consonant produced with voice + noise |
| **глухий** | voiceless — consonant produced with noise only |
| **сонорний** | sonorant — consonant where voice dominates over noise |
| **твердий** | hard — non-palatalized consonant |
| **м'який** | soft — palatalized consonant |
| **наголос** | stress — emphasized pronunciation of a syllable |
| **наголошений** | stressed — syllable bearing the stress |
| **ненаголошений** | unstressed — syllable without stress |
| **транскрипція** | transcription — phonetic notation in square brackets |
| **склад** | syllable |

### Рекомендовані слова — Recommended words

| Слово | Translation |
|-------|-------------|
| **графіка** | graphics — the writing system |
| **орфоепія** | orthoepy — rules of literary pronunciation |
| **орфографія** | orthography — rules of correct spelling |
| **пом'якшений** | partially softened consonant |
| **йотований** | iotated — letters я, ю, є, ї that can represent two sounds |
| **свистячий** | sibilant — whistling consonant: з, ц, с, дз |
| **шиплячий** | hushing consonant: ж, ч, ш, дж |
| **губний** | labial — consonant formed with lips: б, п, в, м, ф |
| **орфоепічна помилка** | pronunciation error |
| **вільний наголос** | free stress — can fall on any syllable |
| **рухомий наголос** | mobile stress — shifts between word forms |
| **мовознавство** | linguistics |


<!-- TAB:Зошит -->

:::note
Розширені вправи для цього уроку ще в розробці.

Advanced exercises for this module are in development. Check back soon!
:::


<!-- TAB:Ресурси -->

- Заболотний Grade 5, p.73-77
  _Core фонетика chapter: звуки/літери, транскрипція rules, м'які/тверді._
- Авраменко Grade 5, p.75-77
  _Тверді/м'які/пом'якшені distinction, дзвінкі/глухі pairs with dialogue._
- Литвінова Grade 5, p.104-130
  _Comprehensive phonetics chapter: звуки мовлення, голосні/приголосні, дзвінкі/глухі pairs table, сонорні/свистячі/шиплячі/губні groups, тверді/м'які with м'який знак, ненаголошені е/и spelling rules._
- Голуб Grade 5, p.66
  _Poetic framing of phonetics: 'Звуки — це щось надзвичайно своєрідне в мові.'_
</generated_module_content>

---

## Review Protocol

### Step 1: Scan for linguistic errors

Scan the Ukrainian text for errors. Report ONLY problems found — do not echo correct text.

Check for:
- Russian characters (ы, э, ё, ъ) — these must NEVER appear
- Russianisms (кот→кіт, хорошо→добре, конечно→звичайно)
- Surzhyk (шо→що, чо→чому)
- Calques (приймати душ→брати душ)
- Incorrect gender assignment or case endings
- Factually wrong claims about Ukrainian phonetics, grammar, or culture
  - If you suspect a factual or phonetic error but are not 100% certain, flag it as `[NEEDS RAG VERIFICATION]` rather than marking it as critical/major

If no errors found, state: "No linguistic errors found."

**Do NOT check for stress marks** — stress annotation is handled by a separate deterministic tool after the review phase. Their absence is correct.

### Step 2: Check exercises

List every exercise block (`:::quiz`, `:::fill-in`, `:::match-up`, `:::group-sort`, `:::true-false`). These are filled exercises — a deterministic tool converted placeholders to real content.

For each exercise, check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?
- Are there enough items per exercise? (check against plan's `activity_hints`)

Also check: Are there enough exercises total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercises are generated by a deterministic tool from the writer's placeholders. If the exercise LOGIC is wrong (e.g., matching unrelated items), flag it — the tool's input data needs fixing. If the exercise FORMAT looks unusual, that is expected (the tool uses a specific DSL syntax).

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | Every content_outline point covered? Section word budgets respected (±10%)? All plan references used? |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | PPP (Present→Practice→Produce) applied? Textbook pedagogy used (Большакова, Захарійчук)? Grammar scope respected (no A2 in A1)? |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | Placeholders specific enough? Test the right skills? Placed after relevant teaching? Match plan's activity_hints? Sufficient items? |
| 6 | **Engagement & tone** | 10% | Interesting for teens/adults? Authoritative but warm (like a skilled teacher)? No LLM filler ("Good news!", "Don't panic!", "Fun fact!")? Cultural hooks? |
| 7 | **Structural integrity** | 5% | All H2 headings from plan present? Word count in range? No duplicate sections? No meta-commentary? Clean markdown? |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | Dialogues natural and culturally appropriate? Real situations, real responses? Speaker roles clear? Not stilted or textbook-robotic? |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence.

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Critical = module cannot ship. Major = quality below standard. Minor = polish item.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero critical findings, at most minor issues |
| **REVISE** | Has major findings but no criticals — fixable without rewrite |
| **REJECT** | Has any critical finding — fundamental problems requiring rewrite |

---

## Output Format

```
## Linguistic Scan
[errors found, or "No linguistic errors found"]

## Exercise Check
[placeholder inventory and issues]

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | X/10 | [specific evidence from the text] |
| ... | ... | ... |

## Findings
[list all findings with dimension/severity/location/issue/fix]

## Verdict: PASS / REVISE / REJECT
[justification — reference both score gate and severity gate]
```
