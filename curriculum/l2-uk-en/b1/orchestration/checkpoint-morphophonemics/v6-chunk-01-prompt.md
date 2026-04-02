<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Severe Russianisms: хорошо
- NOTE: Missing 2/15 required vocab: однина (singular number), множина (plural number)
- NOTE: Plan expects 6 exercise(s) but content has 0 placeholders
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

**Module:** 17: Контрольна робота 2 (B1, B1.2 [Morphophonemics & Noun Subclasses])
**Section to write:** Огляд чергувань (~720 words total)
**Word target for this section:** 720 words (aim for 792 to account for undershoot)

---

## Section Skeleton (follow this exactly)

## Огляд чергувань (~720 words total)
- P1 (~60 words): [Introduction to the importance of morphophonemics at the B1 level, explaining how sound changes like чергування and спрощення are not random "irregularities" but systematic rules that govern Ukrainian word-building and declension across nouns and verbs.]
- P2 (~160 words): [Detailed review of vowel alternations [о/е] → [і] in closed syllables. Explanation of the "open vs. closed syllable" logic with contrasting pairs: рік (closed) vs. року (open), ніч (closed) vs. ночі (open), кінь (closed) vs. коня (open). Mentioning the exceptions where [о] remains in closed syllables (e.g., words like торт or modern borrowings).]
- P3 (~140 words): [Review of fleeting vowels ([о/е] → zero). Explanation of how these vowels "disappear" when an ending is added, changing the stem structure. Examples: учень (nom.) → учня (gen.), пісок → піску, вітер → вітру. Contrasting this with fixed vowels where the [о/е] remains: театр → театру.]
- P4 (~140 words): [Comprehensive review of consonant alternations in noun declension. Focus on the Velar Shift ([г/к/х] → [ж/ч/ш] in Vocative and [г/к/х] → [з'/ц'/с'] in Dative/Locative). Examples: друг → друже, козак → козаче; Ольга → Ользі, рука → руці, горох → у горосі.]
- P5 (~140 words): [Review of consonant alternations in verb conjugation from M10. Explaining how the present tense stem changes for certain verbs. Examples: сидіти (d) → сиджу (dzh), писати (s) → пишу (sh), хотіти (t) → хочу (ch), плакати (k) → плачу (ch). Emphasizing that these patterns follow the same historical logic as noun shifts.]
- P6 (~80 words): [Review of simplification (спрощення) in consonant clusters. Focus on the deletion of "heavy" middle consonants to ease pronunciation and spelling. Examples: тиждень → тижня (not *тиждня), щастя → щасливий (not *щастливий), честь → чесний (not *честний). Highlighting the diagnostic tool: finding the root word to see which sound dropped.]

---
## Full Plan (for reference)

<plan_content>
module: b1-017
level: B1
sequence: 17
slug: checkpoint-morphophonemics
version: '3.0'
title: "Контрольна робота 2"
subtitle: "Морфонеміка та підкласи іменників — перевірка M08-M16"
focus: review
pedagogy: PPP
phase: "B1.2 [Morphophonemics & Noun Subclasses]"
word_target: 4000
objectives:
- "Learner can identify and produce чергування голосних in context:
  [о/е] → [і] (рік-року), [о/е] → zero (учень-учня)"
- "Learner can identify and produce чергування приголосних in both
  noun and verb contexts: [г]→[ж], [к]→[ч], [х]→[ш], [д]→[дж]"
- "Learner can apply спрощення приголосних rules: тижня (not *тиждня),
  щасливий (not *щастливий), чесний (not *честний)"
- "Learner can decline мішана група nouns (сторожем, not *сторожом),
  III відміна nouns (ніччю, радістю), and pluralia tantum nouns (грошей, воріт)"
- "Learner can use medical vocabulary with correct case government and
  morphophonemic awareness (скаржитися на біль, лікуватися від застуди)"
dialogue_situations:
- setting: 'Grammar quiz show on Ukrainian television — contestants answer questions
    about alternations and noun declensions: Як буде ''стіл'' у місцевому? На столі!
    Утворіть множину від ''око''. Очі! А ''сіль'' — якого роду?'
  speakers:
  - Ведучий вікторини (quiz host)
  - Учасники
  motivation: 'Consolidation: vowel/consonant alternation, noun subclasses, pluralia
    tantum'
content_outline:
- section: "Огляд чергувань"
  words: 650
  points:
  - "Review of vowel alternations from M08:
    [о/е] → [і] in закритий склад: рік — року, ніч — ночі, кінь — коня,
    піч — печі, осінь — осені. The rule: when a syllable closes
    (open → closed), [о/е] becomes [і].
    [о/е] → zero (fleeting vowels): учень — учня, пісок — піску,
    вітер — вітру. Practice identifying which pattern applies."
  - "Review of consonant alternations from M09-M10:
    In nouns: [г]→[ж] (друг-друже), [к]→[ч] (козак-козаче),
    [г/к/х]→[з'/ц'/с'] (Ольга-Ользі, рука-руці, горох-у горосі).
    In verbs: [д]→[дж] (сидіти-сиджу), [с]→[ш] (писати-пишу),
    [к]→[ч] (плакати-плачу), [т]→[ч] (хотіти-хочу).
    Practice: given a base form, produce the alternated form."
  - "Review of спрощення from M11:
    Consonant clusters simplify in pronunciation and spelling:
    тиждень — тижня (жд→ж), щастя — щасливий (ст→с),
    честь — чесний (ст→с), серце — сердечний (рц→рд).
    Mnemonic: the 'extra' consonant drops when a suffix is added.
    Diagnostic: which consonant drops and why?"
- section: "Огляд підкласів іменників"
  words: 650
  points:
  - "Мішана група (M13):
    Identification: stem ends in шиплячий (ж, ч, ш, щ).
    Key rule: орудний однини -ем (not -ом): ножем, сторожем, товаришем.
    Кличний: -е for безсуфіксні (стороже), -у for суфіксні (слухачу).
    Plural орудний: -ами (shifts to тверда pattern: товаришами).
    Diagnostic practice: given a мішана група noun, produce all відмінки."
  - "III відміна (M14):
    Identification: жіночий рід + нульове закінчення (+ мати).
    Key rule: подвоєння in орудний if single final consonant:
    ніч → ніччю, сіль → сіллю, річ → річчю.
    No подвоєння if cluster or б/п/в/м/ф/р: радістю, кров'ю, матір'ю.
    Parallel -і/-и in родовий: радості/радости, любові/любови."
  - "Pluralia tantum (M15):
    Identification: no однина form (двері, гроші, ножиці, ліки, Карпати).
    No відміна classification possible.
    Родовий: -ів (окулярів), -ей (грошей), нульове (воріт).
    Special -ми in орудний: грішми, ворітьми (Ukrainian-specific).
    Agreement: always plural (великі двері, ліки закінчилися)."
- section: "Медична лексика та морфонеміка"
  words: 550
  points:
  - "Integration exercise: medical vocabulary as a testbed for all
    Phase 2 grammar. Word families with alternations:
    біль — болить — безболісний (і→о),
    здоров'я — здоровий — оздоровлення (апостроф + word formation),
    лікар — лікувати — лікування — ліки (agent noun + verb + pl. tantum).
    Case government review: скаржитися на + Зн., хворіти на + Зн.,
    лікуватися від + Р., одужати від + Р."
  - "Body part alternations as morphophonemic review:
    ніс — носа (і→о), вухо — у вусі (х→с alternation from M09),
    око — в оці (к→ц alternation from M09).
    III відміна in medicine: кров — крові — кров'ю (no подвоєння, губний),
    мазь — маззю (подвоєння after single consonant).
    Pluralia tantum in medicine: ліки, краплі."
  - "Reading comprehension: a Ukrainian text about a visit to the doctor
    that naturally includes чергування, noun subclass forms, and medical
    vocabulary. Learners answer questions that test grammar, not content
    recall (per rule 10a): 'У якому відмінку вжито слово ліків?',
    'Яке чергування відбувається у слові болить?'"
- section: "Комплексні вправи: чергування"
  words: 550
  points:
  - "Exercise block 1 — Vowel alternation identification:
    Given pairs (рік-року, ніч-ночі, учень-учня, кінь-коня),
    learners identify the type: [о/е]→[і], [о/е]→zero, or none.
    Mixed with трaps: деякі пари не мають чергування (стіл-столу? Ні,
    стіл-столу має: і→о)."
  - "Exercise block 2 — Consonant alternation production:
    Given the base: друг (кличний) → ? (друже).
    сидіти (1st person) → ? (сиджу).
    рука (місцевий) → ? (на руці).
    Mixed noun and verb alternations to test transfer across word classes."
  - "Exercise block 3 — Спрощення identification:
    Given word pairs, identify where спрощення occurred:
    тиждень → тижня (жд→ж), щастя → щасливий (ст→с),
    серце → сердечний (рц→рд? Actually рц→рд is NOT спрощення,
    it is historical alternation — this is a trap question).
    Learners must distinguish спрощення from other changes."
- section: "Комплексні вправи: відмінювання"
  words: 600
  points:
  - "Exercise block 4 — Мішана група declension:
    Decline in context: 'Я бачив (сторож) біля (ворота).'
    → Я бачив сторожа біля воріт.
    'Ми розмовляли з (товариш) про (подорож).'
    → Ми розмовляли з товаришем про подорож.
    Tests both мішана група and interaction with other відміни."
  - "Exercise block 5 — III відміна орудний:
    Form the орудний: ніч → ніччю, кров → кров'ю, радість → радістю,
    подорож → подорожжю, мати → матір'ю, сіль → сіллю.
    Learners must apply the подвоєння vs no-подвоєння rule correctly."
  - "Exercise block 6 — Pluralia tantum in context:
    Fill in the correct form: 'У мене немає (гроші).' → грошей.
    'Зачиніть (двері).' → двері (Зн. = Н. for inanimate).
    'Ми поїхали на (канікули) до (Карпати).'
    → на канікули до Карпат.
    Tests родовий, знахідний, and preposition usage."
- section: "Діалог-синтез"
  words: 600
  points:
  - "Extended dialogue in Ukrainian combining all Phase 2 grammar:
    A conversation between friends about health, travel to Карпати,
    and daily life. The dialogue naturally includes:
    — чергування (болить, ночі, сиджу, на руці),
    — мішана група (ножем, товаришу),
    — III відміна (з радістю, любов'ю, вночі),
    — pluralia tantum (гроші, ліки, двері, канікули),
    — medical vocabulary (лікар, рецепт, аптека)."
  - "Comprehension questions that test LANGUAGE, not content:
    — Знайдіть у діалозі іменники мішаної групи.
    — У якому відмінку вжито слово 'сторожем'?
    — Яке чергування голосних бачите у слові 'болить'?
    — Чому 'ліки' не належать до жодної відміни?
    — Утворіть орудний відмінок: ніч, товариш, радість."
  - "Self-assessment checklist in Ukrainian:
    Я можу: визначити тип чергування ✓/✗,
    правильно відміняти іменники мішаної групи ✓/✗,
    утворити орудний III відміни (подвоєння/без) ✓/✗,
    визначити pluralia tantum і вжити їх у правильній формі ✓/✗,
    вести діалог у лікаря з правильним керуванням ✓/✗."
- section: "Підсумок та перехід до Фази 3"
  words: 400
  points:
  - "Phase 2 summary — what the learner has mastered:
    1. Чергування голосних: [о/е]→[і], [о/е]→zero (M08).
    2. Чергування приголосних: in nouns (M09) and verbs (M10).
    3. Спрощення приголосних (M11).
    4. Noun subclasses: -ар/-яр/-ин (M12), мішана група (M13),
       III відміна (M14), pluralia tantum (M15).
    5. Medical communication with morphophonemic integration (M16)."
  - "Preview of Phase 3 — Verbs:
    The alternation and word-formation knowledge from Phase 2 feeds
    directly into verb morphology. Conditionals (якщо/якби), imperative
    nuances (хай/нехай), reflexive verbs (-ся/-сь), passive voice.
    Morphophonemics will continue appearing: дієслівні чергування
    already seen in M10 will expand to conditional and imperative forms."
vocabulary_hints:
  required:
  - "чергування (alternation — sound change in related word forms)"
  - "спрощення (simplification — consonant cluster reduction)"
  - "мішана група (mixed group — nouns with шиплячий stem ending)"
  - "відміна (declension type — I through IV)"
  - "подвоєння (doubling — in орудний of III відміна)"
  - "однина (singular number)"
  - "множина (plural number)"
  - "відмінок (grammatical case)"
  - "орудний відмінок (instrumental case)"
  - "родовий відмінок (genitive case)"
  - "здоров'я (health)"
  - "біль (pain — чергування і→о: болить)"
  - "ліки (medicine — pluralia tantum)"
  - "лікар (doctor — II відміна, -ар suffix)"
  - "скаржитися (to complain — на + Зн.)"
  recommended:
  - "нульове закінчення (zero ending)"
  - "шиплячий (hissing consonant)"
  - "губний (labial consonant — б, п, в, м, ф)"
  - "закритий склад (closed syllable)"
  - "відкритий склад (open syllable)"
  - "сонорний (sonorant consonant)"
  - "кличний відмінок (vocative case)"
  - "рецепт (prescription)"
  - "діагноз (diagnosis)"
  - "температура (temperature)"
activity_hints:
- type: quiz
  focus: "Identify the type of alternation in given word pairs (чергування голосних/приголосних/спрощення)"
  items: 10
- type: fill-in
  focus: "Decline мішана група, III відміна, and pluralia tantum nouns in sentence context"
  items: 10
- type: error-correction
  focus: "Fix morphophonemic and declension errors (*сторожом, *радіссттю, *один двері)"
  items: 8
- type: match-up
  focus: "Match base forms to alternated forms across M08-M11 patterns"
  items: 10
- type: group-sort
  focus: "Sort nouns by subclass: мішана група / III відміна / pluralia tantum / regular"
  items: 12
- type: reading-comprehension
  focus: "Read a medical dialogue and answer grammar-focused questions (відмінок identification, чергування)"
  items: 6
connects_to:
- "b1-008 (Чергування голосних — reviewed and tested)"
- "b1-009 (Чергування приголосних в іменниках — reviewed and tested)"
- "b1-010 (Чергування приголосних у дієсловах — reviewed and tested)"
- "b1-011 (Спрощення приголосних — reviewed and tested)"
- "b1-013 (Іменники на ж, ч, ш, щ — reviewed and tested)"
- "b1-014 (Жіночий рід III відміна — reviewed and tested)"
- "b1-015 (Іменники у множині — reviewed and tested)"
- "b1-016 (Здоров'я і медицина — reviewed and tested)"
- "b1-018 (Умовний спосіб — Phase 3 begins)"
prerequisites:
- "b1-016 (Health at the doctor — final module before checkpoint)"
grammar:
- "Чергування голосних review: [о/е]→[і], [о/е]→zero"
- "Чергування приголосних review: [г]→[ж], [к]→[ч], [х]→[ш] in nouns and verbs"
- "Спрощення review: тижня, щасливий, чесний"
- "Мішана група declension: орудний -ем, кличний -е/-у"
- "III відміна: подвоєння (ніччю) vs no подвоєння (радістю, кров'ю)"
- "Pluralia tantum: родовий patterns, agreement, no відміна"
- "Medical case government: скаржитися на + Зн., лікуватися від + Р."
register: розмовний
references:
- title: "All references from M08-M16"
  notes: "This checkpoint synthesizes content from all Phase 2 modules.
    Primary textbook sources: Литвінова Grade 6, Заболотний Grade 6,
    Авраменко Grade 6 and Grade 10, Голуб Grade 6, Глазова Grade 10."

</plan_content>

---

## Knowledge Packet

<knowledge_packet>
# Verified Knowledge Packet: Контрольна робота 2
**Module:** checkpoint-morphophonemics | **Phase:** B1.2 [Morphophonemics & Noun Subclasses]
**Textbook grades searched:** 1, 2, 3, 5

---

## Огляд чергувань

> **Source:** savchenko, Grade 3
> **Section:** Сторінка 70
> **Score:** 0.50
>
> 70
> Галина Малик
>                 ГРУДЕНЬ
> Звівши брови крижані,
> їде Грудень на коні.
> У сидåльці золотім
> Миколай сидить за ним.
> А назустріч — Рік старий:
> — Здрастуй, Миколай святий!
> Поки я сюди добрів — 
> подивись, як постарів!
> Кидай того Грудня —
> морозила й студня, 
> та гайда до хати
> Рік Новий стрічати!
> З ким зустрівся Рік старий ? Чому він дуже постарів?
> Які образні вислови характеризують Грудня?
> Яку словесну картину ти намалюєш за рядками вірша?
> Роздивіться світлину. Таким уявили Святого Миколая 
> юні кияни і киянки, що брали участь у конкурсі «Пор-
> трет Святого Миколая». А яким бачите героїв вірша ви?
> Розкажіть або намалюйте.
> 

## Огляд підкласів іменників

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 187
> **Score:** 0.25
>
> 184
> Біля однорідних членів речення може бути узагальню-
> вальне слово. Таке слово за значенням об’єднує однорідні 
> члени речення. 
> НАПРИКЛАД: Викладачі навчають 
> гри на різних інструментах: скрип-
> ці, гітарі, кларнеті, саксофоні.
> Узагальнювальне слово є тим са-
> мим членом речення, що й однорідні 
> члени.  
> Узагальнювальними словами можуть бути:
> іменники 
> Наловили різної риби: коро-
> пів, карасів, щук. 
> займенники (все, всі, ніхто, 
> кожен, усякий та ін.)
> Ніхто не запізнився: ні до-
> рослі, ні діти.
> прислівники (всюди, скрізь, 
> звідусіль, завжди та ін.)
> Вазони були скрізь: у кори-
> дорі, у кімнатах, на кухні. 
> Узагальнювальним може бути і словосполучення. НА-
> ПРИКЛАД: Для школи закупили технічні засоби: принтер, 
> ноутбук, проєктор, ламінатор.

## Медична лексика та морфонеміка

> **Source:** vashulenko, Grade 2
> **Section:** Сторінка 13
> **Score:** 0.33
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
> які треба писати з апострофом.
> х
> Замініть виділені слова словами з довідки і запишіть 
> речення. Поясніть уживання апострофа.
> 1. Діти впорядковують двір. 2. У садочку співають 
> птахи. 3. Над пасікою кружляють бджілки. 4. Важкі 
> червонобокі яблука звисають із гілок. 5.

> **Source:** avramenko, Grade 5
> **Section:** Сторінка 133
> **Score:** 0.33
>
> 133
>  § 57–58.  Апостроф
> 2.	 Апостроф на місці пропуску треба писати в усіх словах рядка
> А без..язикий, хутор..янин, в..юнкий
> Б скип..ятити, вп..ястися, духм..яний
> В вим..я, злопам..ятний, з..ініціювати
> Г жаб..ячий, над..яскраво, зв..язківець
> 3.	 Апостроф на місці пропуску треба писати в усіх словах варіанта
> А хлоп..ята, Св..ятослав, зап..ястя
> Б прислів..я, тьм..яніти, здоров..я
> В В..ячеслав, кав..яр, Придунав..я
> Г полум..я, Лук..яненко, пор..ядок
> 7.	Прочитайте прислів’я та виконайте завдання.
> Бережи одяг, поки новий, а здоров..я — поки молодий.
> А. Зробіть звуковий запис виділеного слова. 
> Б.

## Комплексні вправи: чергування

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 122
> **Score:** 0.50
>
> 119
> 291.	І. Знайдіть в інтернеті аудіозапис пісні «Дух-
> мяна ніч» (муз. П. Зіброва, сл. Ю. Рибчинського) 
> у виконанні Катерини Бужинської. Послухайте 
> запис і випишіть на слух слова з можливими чер- 
> гуваннями приголосних звуків. Хто з вас виписав 
> найбільше таких слів?
> ІІ. Поясніть, до яких видів мовленнєвої діяльності 
> ви вдавалися, виконуючи цю вправу (аудіювання, 
> читання, говоріння, письмо).
> 292.	Укладіть невелику пам’ятку (у формі переліку порад, схеми, 
> табли­ці, малюнка тощо) про дотримання найпоширеніших чергувань 
> приголосних звуків в українській мові. 
> 293.	І. Спишіть речення, ставлячи подані в дужках слова в потрібній 
> формі. Підкресліть букви на позначення звуків, які чергуємо.
> 1. (Друг у множині) знаходить щастя, а перевіряє біда. 
> 2. Не шукай грибів у ведмежому (барліг). 3.

> **Source:** bolshakova, Grade 1
> **Section:** Сторінка 71
> **Score:** 0.33
>
> 71
> Знайди слово — назву зображеної дії. 
>  
> риє 
> малює 
> дарує 
> грає 
> чує
>  
> шиє 
> читає 
> готує 
> співає 
> ласує
>  
>   
> не – нє  ле – лє  те – тє
>  
> синє 
> давнє 
> домашнє 
> осіннє
>  
> літнє 
> прадавнє 
> вчорашнє 
> вечірнє
>  
> У середині складу буква є позначає один звук [е] 
> і пом’якшення попереднього приголосного.
> С И|Н Є
> Д И В|Н Е
> [е]
> [е]
> Текст. Тема тексту. Заголовок
> Єдиноріг — казкова тварина. 
> Зазвичай це кінь з одним-єдиним 
> рогом. Єдиноріг — символ добра 
> і чесності. Давнє повір’я говорить, 
> що єдинороги там, де правда.
> 1
> 2
> 3
> Є є
> є|д и|н о|р і г

## Комплексні вправи: відмінювання

> **Source:** kravtsova, Grade 3
> **Section:** Сторінка 106
> **Score:** 0.50
>
> 106
> 296.	Прочитайте речення з попередньої вправи. Поміркуйте, які 
> групи речень можна виділити. Свої роздуми формулюйте так:
> Можна виділити групу …   речень. Тому що   … .   напри-
> клад, … . Отже, … .
> 297.	 1.	 Зіскануй QR-код та переглянь відео. Опиши свої 
> почуття від переглянутого.
> 298.
> Прочитай вірш Наталі Гуркіної. Спиши одне окличне та 
> одне неокличне речення.
> Розпустило коси сонце, 
> загляда до всіх в віконце: 
> — Хто ще щічки не помив? 
> Хто зарядку не робив?
> Хто не слухається маму? 
> Хто не склав свою піжаму? 
> Хто в цю пору іще спить?!  
> Будемо сплюшка будить!
> 2.	 Позмагайтеся, хто «впізнає» та запише якомога 
> більше дієслів з переносним значенням.
> 3.	 Прочитай, правильно інтонуючи речення.

> **Source:** golub, Grade 5
> **Section:** Сторінка 28
> **Score:** 0.50
>
> 28
> 61
>   Пригадайте і запишіть за відведений час якомога більше запо-
> зичених слів, що мають у нашій мові відповідники. Яким із них 
> варто віддавати перевагу?
> 62
>   Прочитайте слова. Виберіть будь-яку пару слів і складіть із ними 
> діалог, в основі якого має бути пропозиція одного зі співрозмов-
> ників і згода іншого.
> Глосарій — словничок, дисонанс — розлад, голкіпер — 
> воротар, кутюр’є — кравець.
> 63   І   Не знаючи вас, ми ось так зобразили світ ваших захоплень. 
> Розгляньте малюнок і скажіть, чи збігаються наші уявлення 
> про вас зі справжніми вашими захопленнями.

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 204
> **Score:** 0.25
>
> 204
> Відомості із синтаксису й пунктуації. Види речень за метою висловлення
>  Дайте домашку 
> з математики.
> 15:28
> Я загубила в класі 
> щоденник. Ніхто 
> не бачив?
> 15:39
> На завтра треба 
> готувати поробку?
> 15:53
> Візьміть завтра під-
> ручники з англій-
> ської, буде заміна. 
> 16:21
> Ходімо разом 
> у кіно. 
> р
> 16:42
> Я не знаю, як 
> розв’язати задачу. 
> Допоможіть!!!  
>  
>  
> Д
>  
>  
>  
> 17:36
> Вправа 331
> 1. Прочитайте речення, узяті з чату 
> класу .
> 2. Назвіть спочатку розповідні ре-
> чення, потім питальні та  спону-
> кальні .
> 3. Поміркуйте, як змінити ці фрази, 
> щоб вони відповідали нормам 
> етикету . Запишіть свої варіанти .
> Вправа 332
> 1.

## Діалог-синтез

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
> Б.  Якими звуками різняться корені слів у

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
