<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Severe Russianisms: хорошо
- NOTE: Missing 3/16 required vocab: вродливий (beautiful/handsome — describing a person), подружжя (married couple — husband and wife together), постава (posture/bearing — how a person holds their body)
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

**Module:** 3: Людина і стосунки (B1, B1.1 [Baselines & Morphophonemics])
**Section to write:** Зовнішність людини: портретна лексика (~770 words total)
**Word target for this section:** 770 words (aim for 847 to account for undershoot)

---

## Section Skeleton (follow this exactly)

## Зовнішність людини: портретна лексика (~770 words total)
- P1 (~110 words): Introduction to portraiture based on Авраменко Grade 7 (p.100). Define "Опис зовнішності" as a linguistic reconstruction of individuality. Explain the three components of a portrait: body parts, facial features, and clothing/accessories.
- P2 (~150 words): Deep dive into age and stature vocabulary (Авраменко p.101). Contrast 'молодий' with 'зрілий' and 'літній'. Introduce specific stature terms: 'кремезний' (stocky) vs 'тендітний' (slender) and 'стрункий' (graceful). Use example: "Він кремезний чоловік середнього зросту."
- P3 (~150 words): Facial features and complexion. Vocabulary for faces: 'вродливе', 'виразне', 'смагляве' (swarthy), 'бліде' (pale). Introduce the idiom "кров із молоком" for a healthy, rosy complexion. Provide examples of adjectives for eyes (карі, розкосі, виразні).
- P4 (~110 words): Hair and individual features. Categories of hair: 'кучеряве' (curly), 'русяве' (light brown), 'каштанове' (chestnut). Explain 'лисий' vs 'з густим волоссям'. Introduce 'портретна деталь' from Авраменко Grade 5: choosing one vivid detail like a scar, a birthmark, or a specific gaze.
- P5 (~100 words): The cultural philosophy of description (Заболотний Grade 7). Explain how Ukrainian portraiture uses physical traits to reveal "внутрішній світ" (inner world). Example: "За втомленими очима ховалася мудрість."
- Exercise: [match-up, Match портретна лексика to body categories, 12 items] (~150 words): Categorize words like 'широкоплечий', 'рум'яне', 'сиве', 'високий' into groups: Зріст, Постава, Обличчя, Волосся.

---
## Full Plan (for reference)

<plan_content>
module: b1-003
level: B1
sequence: 3
slug: people-and-relationships
version: '3.0'
title: "Людина і стосунки"
subtitle: "Зовнішність, характер, родина та знайомство"
focus: communication
pedagogy: PPP
phase: "B1.1 [Baselines & Morphophonemics]"
word_target: 4000
objectives:
  - "Learner can describe a person's appearance in Ukrainian using портретна лексика:
    зріст, постава, статура, обличчя, волосся, очі"
  - "Learner can characterize a person's personality using Ukrainian adjectives for
    character traits (щирий, лагідний, кмітливий, вередливий, чуйний)"
  - "Learner can name family members and relationship types using precise Ukrainian
    vocabulary, distinguishing близькі/далекі родичі"
  - "Learner can introduce people, describe relationships, and navigate social situations
    using appropriate Ukrainian formulas (знайомство, відрекомендувати, представити)"
  - "Learner can write a structured опис зовнішності людини following the Ukrainian
    school composition model (зачин — основна частина — кінцівка)"
dialogue_situations:
  - setting: 'Wedding reception in Вінниця — introducing relatives to the partner''s
      family: Це мій старший брат (m) — розумний і надійний. А це моя молодша сестра
      (f) — веселіша за всіх! Познайомтеся з нашою бабусею (f) — найдобрішою жінкою.'
    speakers:
      - Наречена
      - Наречений
      - Родичі
    motivation: 'Adjective agreement: старший брат(m), молодша сестра(f), найдобріша
      жінка(f)'
content_outline:
  - section: "Зовнішність людини: портретна лексика"
    words: 700
    points:
      - "Introduction grounded in Авраменко Grade 7 p.100: Опис зовнішності людини
        — відтворення її індивідуального вигляду за допомогою засобів мови. Зазвичай
        опис зовнішності є частиною розповіді. У ньому називають: 1) частини тіла;
        2) риси обличчя; 3) одяг та його елементи."
      - "Systematic vocabulary from Авраменко Grade 7 p.101 — портретна лексика: Вік:
        молодий, зрілий, юний, літній, підлітковий. Постава/статура: повний, худий,
        кремезний, тендітний, стрункий, широкоплечий, приземкуватий. Зріст: високий,
        середнього зросту, невисокий. Волосся: кучеряве, пряме, русяве, каштанове,
        світле, темне. Обличчя: вродливе, виразне, ніжне, повне, худорляве, рум'яне,
        смагляве, бліде."
      - "Practice: learners read a literary portrait excerpt and identify портретна
        лексика by categories. Then describe a classmate, friend, or family member
        using the same structure."
      - "Cultural note: Ukrainian approach to description emphasizes внутрішній світ
        through зовнішність. Заболотний Grade 7 p.248: 'У художньому тексті через
        елементи зовнішньої характеристики письменник показує внутрішній світ персонажа,
        його характер, життя.'"
  - section: "Характер людини: риси і оцінка"
    words: 700
    points:
      - "Positive character traits (with VESUM-verified adjectives): щирий (sincere),
        лагідний (gentle), чуйний (sensitive/responsive), привітний (welcoming), кмітливий
        (quick-witted), стриманий (reserved), товариський (sociable), відповідальний
        (responsible), працьовитий (hardworking), наполегливий (persistent), справедливий
        (fair)."
      - "Negative/neutral character traits: вередливий (capricious), впертий (stubborn),
        замкнутий (withdrawn), нетерплячий (impatient), балакучий (talkative), лінивий
        (lazy), заздрісний (envious), самовпевнений (self-confident/arrogant). Note:
        some traits are context-dependent — впертий can be positive (persistent) or
        negative (obstinate)."
      - "Describing character in context: common patterns. Він/вона — людина + adjective:
        'Вона — людина чуйна i щира.' За характером: 'За характером він стриманий,
        але товариський.' Йому/їй властиво + infinitive: 'Їй властиво допомагати іншим.'
        Practice: learners describe character traits of Ukrainian literary or historical
        figures using these patterns."
      - "Distinguishing synonyms and near-synonyms: щирий vs чесний (sincere vs honest
        — overlap but different emphasis). лагідний vs ніжний vs м'який (gentle vs
        tender vs soft — register). Learners choose the most appropriate adjective
        in context."
  - section: "Родина і родичі"
    words: 600
    points:
      - "Core family vocabulary (B1 expansion beyond A1-A2 basics): Близькі родичі:
        батько, мати (мама), син, дочка (донька), брат, сестра, чоловік (husband),
        дружина (wife), подружжя (married couple). Далекі родичі: дядько, тітка, племінник,
        племінниця, двоюрідний брат/сестра, свекруха, теща, зять, невістка."
      - "Ukrainian kinship precision — terms that English lacks: свекруха (husband's
        mother) vs теща (wife's mother) — English uses 'mother-in-law' for both. Similarly:
        свекор vs тесть (father-in-law), зять (son-in-law or sister's/daughter's husband),
        невістка (daughter-in-law or brother's wife). This precision reflects the
        importance of родинні зв'язки in Ukrainian culture."
      - "Родина as a cultural concept: Ukrainian sayings about family. 'У родині —
        сила.' 'Де злагода в сімействі — там i добро.' The word рід connects to родина,
        Батьківщина, народ — a semantic field that links family to nation."
      - "Practice: learners draw and label a family tree using Ukrainian terms, then
        describe relationships using genitive constructions: 'Оксана — дочка мого
        дядька' (Оксана is my uncle's daughter)."
  - section: "Стосунки між людьми"
    words: 500
    points:
      - "Types of relationships — precise Ukrainian vocabulary (from Ворон Grade 9
        p.22 — semantic distinctions): стосунки (interpersonal relations, how people
        interact), відносини (formal/official relations, ratio), ставлення (attitude
        toward someone/something), взаємини (mutual relations, reciprocal). Common
        error: using відносини for personal relationships (correct: стосунки)."
      - "Relationship vocabulary: дружба (friendship), знайомство (acquaintance),
        кохання (romantic love), повага (respect), довіра (trust), підтримка (support),
        суперечка (argument/dispute), примирення (reconciliation). Verbs: дружити,
        товаришувати, кохати, поважати, довіряти, підтримувати, сваритися, миритися."
      - "Practice dialogue: two friends discussing their relationships with family
        and colleagues, using the vocabulary above."
  - section: "Знайомство і представлення"
    words: 550
    points:
      - "Formulas of introduction from Литвінова Grade 7 p.205: Formal: 'Дозвольте
        відрекомендуватися — мене звати...' 'Дозвольте представити вам мого колегу...'
        'Дуже приємно з вами познайомитися.' Semi-formal: 'Познайомтеся, будь ласка,
        — це мій друг...' Informal: 'Це Андрій, мій однокласник.' 'Привіт, я Марія.'"
      - "Cultural protocol from Литвінова Grade 7 p.205: Younger person is introduced
        to the older person first. A man is introduced to a woman. If there is no
        intermediary, one can introduce oneself. After the introduction, appropriate
        responses: 'Дуже приємно,' 'Радий/рада з вами познайомитися.' At the end of
        the conversation: 'Дякую, що приділили час.'"
      - "Кличний відмінок in introductions and address: Review: Андрію! Маріє! Тетяно
        Iванівно! B1 expansion: formal address patterns with ім'я по батькові. Practice:
        learners role-play introductions in formal and informal settings."
      - "Practice dialogue: introducing a Ukrainian friend to your family, switching
        between formal and informal register as appropriate."
  - section: "Опис людини: як писати портрет"
    words: 600
    points:
      - "Composition structure from Заболотний Grade 7 p.251 — план твору-опису зовнішності
        людини: I. Зачин (хто ця людина — who is this person). II. Основна частина:
        1. Що найперше впадає в очі в її зовнішності. 2. Зріст, постава, хода, міміка,
        жести. 3. Риси обличчя, вираз обличчя, погляд, очі, волосся. 4. Одяг. III.
        Кінцівка (загальне враження — general impression)."
      - "Художні засоби in portrait writing from Заболотний Grade 7 p.251: Епітети:
        'сивий, як голуб, увесь білий-білий, чистий, аж світиться.' Порівняння: 'очі,
        як волошки,' 'стрункий, наче тополя.' Зменшувально-пестливі слова: 'оченята,
        рученьки, кучерики.' Портретна деталь — one vivid detail that defines the
        person: from Авраменко Grade 5 p.259: 'зображення лише однієї, але прикметної,
        дуже яскравої риси зовнішності.'"
      - "Model portrait in Ukrainian (adapted literary excerpt) with analysis of structure
        and artistic devices. Learners then write their own 8-10 sentence portrait
        of someone they know."
  - section: "Підсумок: людина у словах"
    words: 350
    points:
      - "Complete vocabulary reference — all terms organized by category: зовнішність
        (appearance), характер (character), родина (family), стосунки (relationships),
        знайомство (meeting). Glossary with Ukrainian definitions for self-study."
      - "Self-check in Ukrainian: 1. Опишіть зовнішність вашого друга/подруги (5-7
        речень). 2. Назвіть 5 позитивних i 3 негативних рис характеру. 3. Яка різниця
        між словами стосунки, ставлення, відносини? 4. Представте свого друга колезі
        (формально i неформально)."
      - "Preview of checkpoint module: Контрольна робота 1 (M07) — testing metalanguage,
        verb tenses, aspect, and descriptions."
vocabulary_hints:
  required:
    - "зовнішність (appearance — a person's outward look)"
    - "характер (character — a person's inner qualities)"
    - "стосунки (interpersonal relationships — how people interact)"
    - "родичі (relatives — people connected by family)"
    - "знайомство (acquaintance / the act of meeting someone)"
    - "вродливий (beautiful/handsome — describing a person)"
    - "кремезний (stocky/sturdy — of strong build)"
    - "тендітний (slender/delicate — of light build)"
    - "щирий (sincere — genuine in feelings)"
    - "лагідний (gentle — soft in manner)"
    - "кмітливий (quick-witted — mentally sharp)"
    - "чуйний (sensitive/responsive — attentive to others)"
    - "подружжя (married couple — husband and wife together)"
    - "відрекомендуватися (to introduce oneself — formal register)"
    - "портретна деталь (portrait detail — one defining visual feature)"
    - "постава (posture/bearing — how a person holds their body)"
  recommended:
    - "статура (build/stature — body type)"
    - "смаглявий (swarthy/dark-skinned)"
    - "кучерявий (curly-haired)"
    - "стриманий (reserved/restrained — in behavior)"
    - "привітний (welcoming/friendly)"
    - "вередливий (capricious/picky)"
    - "товариський (sociable/companionable)"
    - "дружба (friendship)"
    - "кохання (romantic love)"
    - "довіра (trust)"
    - "примирення (reconciliation)"
    - "кличний відмінок (vocative case — used in direct address)"
activity_hints:
  - type: match-up
    focus: "Match портретна лексика to body categories: зріст, постава, волосся, обличчя,
      характер."
    items: 12
  - type: quiz
    focus: "Identify character traits as позитивні чи негативні, and choose the correct
      adjective for a given description."
    items: 12
  - type: fill-in
    focus: "Complete a portrait description: fill in missing adjectives and relationship
      terms in a Ukrainian text about a family."
    items: 12
  - type: free-write
    focus: "Write a structured portrait (зачин — основна частина — кінцівка) of a
      real or fictional person, 8-10 sentences."
    items: 12
  - type: role-play
    focus: "Introduce a friend to a colleague using formal register, then introduce
      the same person informally to another friend."
    items: 12
  - type: group-sort
    focus: "Sort relationship vocabulary into categories: родина, дружба, формальні
      стосунки."
    items: 12
connects_to:
  - "b1-005 (Майбутнє i вид дієслова — future tense used in plans about people)"
  - "b1-007 (Контрольна робота 1 — checkpoint testing descriptions and vocabulary)"
  - "b1-043 (Творення прикметників — adjective formation builds on character vocabulary)"
prerequisites:
  - "A2 completion (learner knows basic family vocabulary, adjective agreement)"
  - "b1-001 to b1-004 (metalanguage bridge and baseline grammar review)"
grammar:
  - "Adjective agreement with nouns in gender, number, and case"
  - "Genitive constructions for describing relationships (дочка мого дядька)"
  - "Кличний відмінок for direct address in introductions"
  - "Semantic distinctions: стосунки vs відносини vs ставлення vs взаємини"
  - "Зменшувально-пестливі форми in portrait descriptions"
register: розмовно-побутовий / науково-навчальний
references:
  - title: "Авраменко Grade 7, p.100-101"
    notes: "Особливості будови опису зовнішності людини: definition, structure, complete
      портретна лексика tables (вік, постава, зріст, волосся, обличчя)."
  - title: "Заболотний Grade 7, p.248-255"
    notes: "Опис зовнішності людини: художній vs науковий опис, словник портретної
      лексики, план твору-опису, портретна деталь."
  - title: "Авраменко Grade 5, p.259"
    notes: "Портретна деталь: 'зображення лише однієї, але прикметної, дуже яскравої
      риси зовнішності.'"
  - title: "Литвінова Grade 7, p.205"
    notes: "Правила знайомства: формули представлення, етикет, кличний відмінок."
  - title: "Ворон Grade 9, p.22"
    notes: "Semantic distinctions: відношення, взаємини, стосунки, ставлення."
  - title: "Заболотний Grade 8, p.177"
    notes: "Оцінювальні жанри: характеристика — зовнішня i внутрішня."

</plan_content>

---

## Knowledge Packet

<knowledge_packet>
# Verified Knowledge Packet: Людина і стосунки
**Module:** people-and-relationships | **Phase:** B1.1 [Baselines & Morphophonemics]
**Textbook grades searched:** 1, 2, 3, 5

---

## Зовнішність людини: портретна лексика

> **Source:** avramenko, Grade 5
> **Section:** Сторінка 163
> **Score:** 0.50
>
> 163
> РОЗВИТОК МОВЛЕННЯ
> До речі…
> Означення найчастіше виражені прикметниками. Їх використову­
> ють в описах. Що більше означень-прикметників ви знати­мете, то 
> легше вам буде висловлювати думки, описувати людей. Ось ко­
> роткий словник прикметників. Запам’ятайте ці слова. 
> Деталь 
> портрета
> Означення
> Обличчя
> красиве, вродливе, негарне, виразне, ніжне, потворне, пов­
> не, худорляве, продовгувате, грубе, рум’яне, бліде, смагля-
> ве, біле, кров із молоком
> Вираз  
> обличчя
> веселий, сумний, зосереджений, розгублений, відкритий, 
> серйозний, привітний, безтурботний, хитрий, злий, ви-
> нуватий, стурбований, чистий, вольовий, задоволений, 
> занепокоє­ний, кислий, гидливий, спантеличений
> Очі
> великі, виразні, широко поставлені, розкосі, світлі, темні, 
> карі, чорні, сині, вицвілі
> Погляд
> ясний, приємний, ніжний,...

> **Source:** avramenko, Grade 5
> **Section:** Сторінка 283
> **Score:** 0.25
>
> 283
> КОРОТКИЙ СЛОВНИК ЛІТЕРАТУРОЗНАВЧИХ ТЕРМІНІВ
> Оповідання — це невеликий прозовий твір про якусь по­
> дію із життя одного/однієї чи кількох героїв/героїнь протя­
> гом ко­роткого проміжку часу.
> Пейзаж — це опис природи в художньому творі.
> Персоніфікація — образний вислів, у якому ознаки лю­ди­
> ­ни переносять на неживий предмет чи явище (одним словом, 
> олюднення), наприклад: танцюють сніжинки, спить камінь. 
> Портрет — це змалювання зовнішнього вигляду літера­
> турних героїв чи героїнь. 
> Приказка — це образний вислів, що влучно характеризує 
> людину, але, на відміну від прислів’я, висловлює думку не­
> повно. 
> Прислів’я — довершений за змістом вислів про риси та 
> вчинки людей із повчальним характером.
> Рима — це співзвучні  закінчення рядків у віршованому 
> творі.

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 182
> **Score:** 0.33
>
> 182
> КНИЖКА ВЧИТЬ, ЯК У СВІТІ ЖИТЬ
> ÒÅÎÐ²ß Ë²ÒÅÐÀÒÓÐÈ
> ПОРТРЕТ. ПОРТРЕТНА ДЕТАЛЬ
> Розповідаючи про персонажів, автор / авторка художнього твору часто вдається 
> до їх портретної характеристики. Портрет у літературі – це змалювання зовнішнього вигляду персонажа: облич-
> чя, волосся, постаті, ходи, одягу, манери триматися, характерних жестів, міміки 
> тощо. Через портрет можна передавати характер, почуття, настрої героя / героїні, 
> висловлювати своє ставлення до нього / неї. Одяг і прикраси людини часто свід-
> чать про її естетичні смаки, риси вдачі, майновий стан, рід занять. Міміка й жести 
> можуть розповісти про рівень внутрішньої культури й вихованості. Портрет дає змогу глибше зрозуміти внутрішній світ персонажа.

## Характер людини: риси і оцінка

> **Source:** golub, Grade 5
> **Section:** Сторінка 118
> **Score:** 0.25
>
> 118
> 298   Підготуйте спільно перелік рис характеру і вчинків людини, якій 
> притаманна гідність. Речень з якою емоцією уникає під час спіл-
> кування гідна людина?
> 299   П рочитайте виразно речення. Визначте емоції, що забарв-
> люють окличні речення. Яку роль вони відіграють у нашому 
> житті?
> 1. Яка розкішна цьогоріч зима! Стільки снігу намело, бага-
> то морозу (зі стріх не капне) і багато сонця! (Дара Корній). 
> 2. Я не тямив себе від щастя! (Т. Поставна). 3. «Вода?! Вода! — 
> закричав Остап. — Дарино, вода!» 4.

> **Source:** avramenko, Grade 5
> **Section:** Сторінка 163
> **Score:** 0.50
>
> 163
> РОЗВИТОК МОВЛЕННЯ
> До речі…
> Означення найчастіше виражені прикметниками. Їх використову­
> ють в описах. Що більше означень-прикметників ви знати­мете, то 
> легше вам буде висловлювати думки, описувати людей. Ось ко­
> роткий словник прикметників. Запам’ятайте ці слова. 
> Деталь 
> портрета
> Означення
> Обличчя
> красиве, вродливе, негарне, виразне, ніжне, потворне, пов­
> не, худорляве, продовгувате, грубе, рум’яне, бліде, смагля-
> ве, біле, кров із молоком
> Вираз  
> обличчя
> веселий, сумний, зосереджений, розгублений, відкритий, 
> серйозний, привітний, безтурботний, хитрий, злий, ви-
> нуватий, стурбований, чистий, вольовий, задоволений, 
> занепокоє­ний, кислий, гидливий, спантеличений
> Очі
> великі, виразні, широко поставлені, розкосі, світлі, темні, 
> карі, чорні, сині, вицвілі
> Погляд
> ясний, приємний, ніжний,...

## Родина і родичі

> **Source:** vashulenko, Grade 2
> **Section:** Сторінка 94
> **Score:** 0.50
>
> НАВЧАЮСЯ ВЖИВАТИ ІМЕННИКИ, ПРИКМЕТНИКИ, ДІЄСЛОВА 
> І ЧИСЛІВНИКИ В МОВЛЕННІ
> Послухайте пісню на слова 
> Вадима Крищенка у вико­
> нанні Марічки Яремчук.
> визначаю 
> складаю
> А
> 20 Прочитай уривок із пісні Вадима Крищенка. Назви членів 
> своєї сім'ї.
> Родина, родина — від батька до сина, 
> від матері доні добро передам.
> Родина, родина — це вся Україна
> з глибоким корінням, з високим гіллям.
> • Доведи, що виділені слова є іменниками.
> • Добери до іменника родина близьке за значенням слово. 
> Склади і запиши з ним речення.
> 2і| Відгадайте загадки.
> 1. Улітку — лагідний, узимку — холодний, восени
> — пронизливий, весною — теплий. 2. Узимку — чорний,
> навесні та влітку — зелений, а восени — жовтий.
> • Назвіть прикметники, використані в загадках.

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 196
> **Score:** 0.50
>
> «Не бачив. Ми, – брешу, – посварилися трохи. Вони кудись подались. А куди, не знаю». Година минула, дві. Смеркло. Матері ваші дедалі більше 
> нервують. Батьки, правда, тримаються. Тільки сопуть похмуро. А тоді рап-
> том бачу, підходить твій, Цигане, батько до твого, Марусику, і каже...

## Стосунки між людьми

> **Source:** golub, Grade 5
> **Section:** Сторінка 237
> **Score:** 0.33
>
> 237
> Шукаємо відповіді на запитання:
> 1   Що спільного й відмінного між суперечкою і сваркою?
> 2   Які слова спричиняють конфлікт?
> 533   Прочитайте «слова дня». Що вони означають? Чи можуть ці слова 
> стати причиною сварки й погіршення стосунків? Відповідь 
> обґрунтуйте.
> Суперåчка — зіткнення різних позицій і думок, у якому 
> кожна сторона аргументовано захищає свою позицію і 
> спростовує докази інших. У результаті суперечки учас-
> ники її можуть схилятися до чиєїсь думки, а можуть 
> залишатися зі своєю, але спільно доходять згоди.
> Свàрка — конфлікт, суперечність між людьми, 
> що призводить до погіршення стосунків.
> Учіться поважати думку іншої людини, визнавати 
> свої помилки. Сварка не призводить до добра. 
> Поступаючись, ви одержите більше.
> 534   Прочитайте окремі фрази з діалогів.

## Знайомство і представлення

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 214
> **Score:** 0.50
>
> 214
> Відомості із синтаксису й пунктуації.  Додаток
> Відмінок
> Запитання
> Приклад іменника
> Непрямі 
> відмінки
> Родовий
> Давальний
> Знахідний
> Орудний
> Місцевий 
> Кличний 
> Немає питання
> 2.	 Провідмінюйте слова друг і  книга.
> Вправа 348
> 1.	 Спишіть речення.
> Катерина запросила подругу. — Подруга запросила Кате-
> рину.
> Я прочитала книжку. — Книжка мені сподобалася.
> Наша команда виграла кубок. — Кубок дістався нашій ко-
> манді.
> Я хочу запросити тебе на  день народження. — Ти хочеш 
> запросити мене на  день народження.
> Несе Галя воду. — Дайте Галі води.
> Вітер дуба хитає. — Прогноз погоди обіцяє сьогодні вітер.
> 2.	 Визначте, якими членами речення є виділені слова, і підкресліть їх у від-
> повідний спосіб.
> 3.	 Над підметами та  додатками надпишіть відмінок.

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 246
> **Score:** 0.25
>
> 246
> Відомості із синтаксису й пунктуації. Пряма мова . Розділові знаки в реченнях
> 6. Поміркуйте, як можна назвати наведені нижче слова . Обґрунтуйте думку . 
> Чи подобається вам таке спілкування?
> От же ж тая Гребенючка! Не люблю я людей, котрі до вчи-
> телів піддобрюються, лізуть із своєю любов’ю: «Галино Сидо-
> рівно, я вам те! Галино Сидорівно, я вам се! Галино Сидорівно, 


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
