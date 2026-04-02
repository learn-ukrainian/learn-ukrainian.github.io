<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Missing section heading: 'Підсумок: здоров'я українською'
- NOTE: Missing 1/16 required vocab: призначити (to prescribe — perfective)
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

# Section-by-Section Generation — Section 1/6

You are writing ONE SECTION of a Ukrainian language module. Write ONLY this section — nothing else.

**Module:** 16: Здоров'я і медицина (B1, B1.2 [Morphophonemics & Noun Subclasses])
**Section to write:** Здоров'я і самопочуття (~720 words total)
**Word target for this section:** 720 words (aim for 792 to account for undershoot)

---

## Section Skeleton (follow this exactly)

## Здоров'я і самопочуття (~720 words total)
- P1 (~160 words): Introduction to the concept of health as the ultimate value (*найвищий скарб*). Explanation of the lexical family: *здоров'я* (noun) with the apostrophe after [в], *здоровий* (adjective), and the verb pair *одужувати* (imperfective) / *одужати* (perfective). Comparison to the Grade 3 proverb "Здоров’я — найдорожчий скарб".
- P2 (~150 words): Describing general well-being using *почуватися*. Contrasting *Я добре почуваюся* with *Мені погано*. Introduction of the Dative experiencer construction for physical sensations: *Мені нудить* (I feel nauseous) and *Мені боляче* (It hurts me).
- P3 (~170 words): Introduction to morphophonemic alternations (B1.2 focus) using the word *біль* (pain). Explain the і→о alternation in closed vs. open syllables: *біль* (closed) vs. *болить* (open). Discussion of the prefix *без-* in *безболісний* (painless) and how the alternation carries over to word formation.
- P4 (~160 words): Review of body parts with a focus on consonant alternations from M09: *вухо* (ear) → *у вусі* (х→с), *око* (eye) → *в оці* (к→ц), and *ніс* (nose) → *носа* (і→о alternation). Contrast with stable stems like *голова* → *головний*.
- Exercise: [match-up, focus: Medical word families and alternations (біль-болить, вухо-вусі), 12 items] (~80 words)

---
## Full Plan (for reference)

<plan_content>
module: b1-016
level: B1
sequence: 16
slug: health-at-the-doctor
version: '3.0'
title: "Здоров'я і медицина"
subtitle: "У лікаря — від скарг до рецепта"
focus: communication
pedagogy: PPP
phase: "B1.2 [Morphophonemics & Noun Subclasses]"
word_target: 4000
objectives:
- "Learner can describe symptoms and health complaints in Ukrainian
  using appropriate medical vocabulary (біль, кашель, нежить, температура)"
- "Learner can conduct a basic doctor-patient dialogue in Ukrainian:
  describing symptoms, answering questions, understanding diagnosis"
- "Learner can navigate a pharmacy interaction: asking for ліки,
  understanding рецепт and дозування, describing алергія"
- "Learner can apply morphophonemic knowledge from M08-M15 to medical
  vocabulary: біль-безболісний (чергування), ліки (pluralia tantum),
  здоров'я-здоровий (word formation)"
- "Learner can use correct case government with medical verbs:
  скаржитися на (+ Зн.), хворіти на (+ Зн.), лікуватися від (+ Р.)"
dialogue_situations:
- setting: 'At a поліклініка (f, polyclinic) in Київ — detailed medical consultation:
    У мене болить голова (f) вже тиждень. Температура тіла (n, body) — 37.5. Виписую
    вам рецепт (m, prescription) на ліки (pl, medicine). Зверніться до хірурга (m,
    surgeon).'
  speakers:
  - Пацієнт
  - Терапевт (GP)
  motivation: 'Medical vocabulary + cases: болить голова(f), рецепт на ліки, до хірурга(gen)'
content_outline:
- section: "Здоров'я і самопочуття"
  words: 650
  points:
  - "Core vocabulary introduction (90%+ Ukrainian prose):
    Здоров'я — найважливіше, що є в людини. Коли ми здорові, ми не
    думаємо про лікарів. Але коли хворіємо, нам потрібна допомога.
    Key lexical family: здоров'я (noun) → здоровий (adj) →
    одужати (verb, perfective) → одужувати (verb, imperfective).
    Morphophonemic link: здоров'я shows апостроф after губний [в]
    before [й] — same pattern as м'який знак rules from Phase 1."
  - "Describing how you feel — key constructions:
    Я добре почуваюся. / Мені погано. / У мене болить голова.
    Мені нудить. / Я кашляю. / У мене температура.
    Case patterns: у мене + називний (possession), мені + present
    (dative experiencer), болить + називний (what hurts).
    Connection to M08 чергування: біль — болить — безболісний
    (і→о alternation in open syllable)."
  - "Body parts vocabulary review at B1 level with morphophonemic awareness:
    голова — головний (о→о, no alternation — stress stable),
    ніс — носа (і→о чергування in закритий/відкритий склад),
    вухо — у вусі (х→с чергування from M09),
    око — в оці (к→ц чергування from M09).
    These are the same alternation patterns, now applied to body vocabulary."
- section: "У лікаря: діалог"
  words: 800
  points:
  - "Model dialogue 1 — Прийом у терапевта (appointment with GP):
    Full Ukrainian dialogue demonstrating the consultation flow:
    реєстрація (registration) → скарги (complaints) → огляд (examination)
    → діагноз (diagnosis) → призначення (prescription).
    Лікар: На що скаржитесь? (What are you complaining about?)
    Пацієнт: У мене болить горло і є температура.
    Лікар: Як давно? Пацієнт: Три дні.
    Лікар: Відкрийте рота. Скажіть 'а'. Дихайте глибоко."
  - "Model dialogue 2 — У стоматолога (at the dentist):
    Specialized vocabulary: зуб (tooth), ясна (gums), пломба (filling),
    знеболювальне (anesthetic). Grammatical focus: наказовий спосіб
    in medical commands (відкрийте, покажіть, не рухайтеся).
    Morphophonemic link: зуб — зуби (no alternation) vs зуб — зубний
    (word formation with suffix -н-)."
  - "Key medical verbs and their case government:
    скаржитися на + Зн. (complain about): скаржуся на головний біль.
    хворіти на + Зн. (be sick with): хворіти на грип.
    лікуватися від + Р. (be treated for): лікуватися від застуди.
    оглянути + Зн. (examine): лікар оглянув пацієнта.
    призначити + Зн. (prescribe): лікар призначив ліки.
    одужати від + Р. (recover from): одужати від хвороби."
- section: "Спеціалісти та обстеження"
  words: 650
  points:
  - "Medical specialists vocabulary:
    терапевт (GP), хірург (surgeon), стоматолог (dentist),
    окуліст (eye doctor), педіатр (pediatrician), лікар (doctor).
    Word formation link from M12: лікар belongs to the -ар suffix
    group (II відміна м'яка група). Морфологічна паралель:
    пекар, школяр, лікар — all agent nouns with -ар."
  - "Types of обстеження:
    аналіз крові (blood test — note: крові is родовий III відміна from M14),
    рентген (X-ray), УЗД (ultrasound — abbreviation),
    вимірювання тиску (blood pressure measurement),
    вимірювання температури (temperature measurement).
    Grammar focus: родовий відмінок in medical contexts (аналіз чого?
    крові, сечі; вимірювання чого? тиску, температури)."
  - "Reading practice: a medical report summary in Ukrainian.
    Learners extract key information: діагноз, симптоми, призначення.
    Focus on reading comprehension of medical register Ukrainian."
- section: "В аптеці"
  words: 700
  points:
  - "Pharmacy dialogue:
    Пацієнт: Доброго дня. У мене рецепт від лікаря.
    Аптекар: Покажіть, будь ласка. Ось ваші ліки.
    Пацієнт: Скільки разів на день приймати?
    Аптекар: Тричі на день після їжі.
    Key vocabulary: рецепт, ліки (pluralia tantum from M15!),
    таблетка, мазь, укол, ін'єкція, щеплення, краплі (also pl. tantum),
    дозування (dosage)."
  - "Ліки — a grammar showcase from M15:
    ліки is pluralia tantum: ці ліки (not *цей лік in medical sense),
    ліків (родовий), лікам (давальний), ліками (орудний).
    Other pluralia tantum in medicine: краплі (drops), вершки (cream —
    as in cosmetic), парфуми (perfume — but this is from M15 general)."
  - "Morphophonemic connections in medical vocabulary:
    біль → безболісний (prefix без- + о-alternation),
    хвороба → хворіти → хворий (word family),
    здоров'я → здоровий → оздоровлення (word family with апостроф),
    лікар → лікувати → лікування → ліки (word family, -ар agent noun).
    These word families reinforce the word-formation patterns from M12 and M44."
- section: "Хвороби та симптоми"
  words: 700
  points:
  - "Common illnesses:
    застуда (cold), грип (flu), алергія (allergy),
    запалення (inflammation), нежить (runny nose), кашель (cough).
    Describing symptoms in Ukrainian:
    У мене нежить і кашель. Мені боляче ковтати. Я чхаю.
    У мене висока температура — тридцять вісім і п'ять."
  - "Grammar focus — нежить and кашель as II відміна masculine nouns:
    нежить — нежитю (давальний, м'яка група: like учитель),
    кашель — кашлю (давальний, м'яка група).
    Contrast with III відміна: хвороба is I відміна (feminine -а ending),
    but біль is II відміна masculine (not III!).
    This reinforces the відміна identification skills from M13-M14."
  - "Prevention vocabulary: щеплення (vaccination), імунітет (immunity),
    профілактика (prevention), обстеження (examination/checkup).
    Advice constructions: Вам треба зробити щеплення. Потрібно здати
    аналізи. Раджу більше відпочивати. Не забувайте пити воду."
- section: "Підсумок: здоров'я українською"
  words: 500
  points:
  - "Communicative competence check — can the learner:
    1. Describe symptoms to a doctor?
    2. Understand a diagnosis and prescription?
    3. Navigate a pharmacy interaction?
    4. Use correct case government with medical verbs?
    Morphophonemic integration check — can the learner:
    1. Identify чергування in medical words (біль-болить)?
    2. Recognize pluralia tantum (ліки, краплі)?
    3. Apply word formation patterns (лікар-лікувати-лікування)?"
  - "Self-check: Дайте відповіді українською:
    1. На що ви скаржитеся? (describe three symptoms)
    2. Які спеціалісти працюють у поліклініці?
    3. Що каже аптекар, коли дає ліки?
    4. Утворіть слова від кореня 'здоров-'.
    Preview: M17 — Контрольна робота 2 (review M08-M16)."
vocabulary_hints:
  required:
  - "здоров'я (health — noun, III відміна pattern with апостроф)"
  - "лікар (doctor — II відміна, -ар agent suffix)"
  - "хвороба (disease — I відміна feminine)"
  - "біль (pain — II відміна masculine, чергування: біль-болить)"
  - "температура (temperature — I відміна)"
  - "кашель (cough — II відміна masculine, м'яка група)"
  - "нежить (runny nose — II відміна masculine)"
  - "ліки (medicine — pluralia tantum)"
  - "рецепт (prescription)"
  - "аптека (pharmacy — I відміна)"
  - "діагноз (diagnosis — II відміна)"
  - "симптом (symptom — II відміна)"
  - "скаржитися (to complain — на + Зн.)"
  - "лікувати (to treat — imperfective)"
  - "одужати (to recover — perfective)"
  - "призначити (to prescribe — perfective)"
  recommended:
  - "пацієнт (patient — II відміна)"
  - "лікарня (hospital — I відміна)"
  - "поліклініка (clinic — I відміна)"
  - "терапевт (GP/therapist — II відміна)"
  - "хірург (surgeon — II відміна)"
  - "стоматолог (dentist — II відміна)"
  - "застуда (cold — I відміна)"
  - "грип (flu — II відміна)"
  - "алергія (allergy — I відміна)"
  - "щеплення (vaccination — neuter, -ення suffix)"
  - "обстеження (examination — neuter, -ення suffix)"
  - "таблетка (pill/tablet — I відміна)"
activity_hints:
- type: quiz
  focus: "Match symptoms to the correct specialist (головний біль → терапевт, зубний біль → стоматолог)"
  items: 12
- type: fill-in
  focus: "Complete doctor-patient dialogue with correct case forms (скаржитися на..., лікуватися від...)"
  items: 12
- type: match-up
  focus: "Match medical word families: лікар-лікувати-ліки, біль-болить-безболісний"
  items: 12
- type: sentence-builder
  focus: "Build sentences describing symptoms and medical actions using correct grammar"
  items: 12
- type: error-correction
  focus: "Fix case government errors in medical sentences (*скаржитися від, *хворіти з)"
  items: 12
connects_to:
- "b1-008 (Чергування голосних — біль-болить, ніс-носа: і→о alternation)"
- "b1-009 (Чергування приголосних — вухо-у вусі, око-в оці: к→ц, х→с)"
- "b1-012 (Іменники на -ар — лікар as agent noun pattern)"
- "b1-015 (Іменники у множині — ліки, краплі as pluralia tantum)"
- "b1-014 (Жіночий рід III відміна — кров, мазь as III відміна nouns)"
prerequisites:
- "b1-015 (Pluralia tantum — ліки, краплі in pharmacy context)"
- "b1-008 (Чергування голосних — morphophonemic awareness for medical vocab)"
grammar:
- "Case government: скаржитися на + Зн., хворіти на + Зн., лікуватися від + Р."
- "Наказовий спосіб in medical commands: відкрийте, покажіть, дихайте"
- "Pluralia tantum in medicine: ліки, краплі"
- "Word formation families: здоров'я-здоровий, біль-болить-безболісний, лікар-лікувати"
- "Body part alternations: ніс-носа (і→о), вухо-у вусі (х→с), око-в оці (к→ц)"
- "Давальний of experience: мені боляче, мені нудить"
register: розмовний
references:
- title: "Заболотний Grade 10, p.19"
  notes: "Text 'Коли слово лікує': doctor-patient interaction with medical
    vocabulary (біль, симптом, остеохондроз, пацієнт, лікар)."
- title: "Авраменко Grade 8, p.38"
  notes: "Paronym distinction: доктор (academic degree) vs лікар (medical doctor).
    Important for correct usage in medical context."
- title: "Голуб Grade 5, p.24"
  notes: "Health-themed text about правильне харчування, здоров'я, фізичні вправи.
    Vocabulary: кров'яний тиск, стрес, здорові продукти."
- title: "Заболотний Grade 11, p.166"
  notes: "Text 'Здоров'я у твоїх руках' with health vocabulary in context
    of punctuation exercises."

</plan_content>

---

## Knowledge Packet

<knowledge_packet>
# Verified Knowledge Packet: Здоров'я і медицина
**Module:** health-at-the-doctor | **Phase:** B1.2 [Morphophonemics & Noun Subclasses]
**Textbook grades searched:** 1, 2, 3, 5

---

## Здоров'я і самопочуття

> **Source:** golub, Grade 5
> **Section:** Сторінка 24
> **Score:** 0.50
>
> 24
> 1. Перебування на свіжому повітрі не лише знижує 
> кров’яний тиск і покращує функції пам’яті, а й допомагає 
> подолати стрес (Г. Браун). 2. Серце зношується злобою. 
> Сиріч — гнівом, гордощами, заздрістю, невір’ям, непрощен-
> ням (М. Дочинець). 3. Завдяки корисній їжі ми почуваємося 
> енергійними. 4. Подумай, скільки свіжих, здорових продук-
> тів різних кольорів ти можеш з’їсти впродовж дня. 
> 5. Дослідження доводять, що регулярні фізичні вправи пози-
> тивно впливають на здоров’я, а також із допомогою них 
> можна підвищити рівень IQ (Д. Браун, Н. Кей).
>  
> ІІ   Якою темою об’єднані речення? Чому здоров’я і здоровий 
> спосіб життя вважають найвищими цінностями? Додайте 
> кілька своїх порад щодо здорового способу життя.
> 53
>   За словником омонімів дайте відповіді на запитання-загадки.
> 1.

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 35
> **Score:** 0.50
>
> 35
>  
> 	 Які ще теми прислів’їв можуть бути?
>  
> 	 Обговоріть! Яке повчання містить кожне прислів’я?
>  
> 	 Поміркуйте і з’ясуйте, про які риси характеру людини йдеться 
> у двох перших приказках.
>  
> 	 Які прислів’я і приказки ти іще знаєш?
> * * *
> 	 	
> Дає і з рук не випускає.
> 	 	
> Язик без кісток, що хоче, те й лопоче.
> 	 	
> Здоров’я — найдорожчий скарб.
> 	 	
> Без діла псується сила.
> 	 	
> Хто хвалиться, той кається.
> 	 	
> Хто діло робить, а хто ґави ловить.
> 	 	
> Гостре словечко ранить сердечко.
> 	 	
> Згода дім будує, а незгода — руйнує.
> 	 	
> Дружба та братство — найбільше багатство.
> 	 	
> Де праця — там густо, а де лінь — там пусто.
> Приказка — це влучний вислів, який стверджує 
> факт.

## У лікаря: діалог

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 139
> **Score:** 0.50
>
> 139
> 3   Дай письмові відповіді на запитання. Записуй числівники словами. 
>   Що називають числівники? На яке питання відповідають?
>   Запиши утворений текст, подаючи числівники словами. 
> О котрій годині ти прокидаєшся? 
> Скільки часу ти одягаєшся?
> Коли виходиш із дому до школи?
> Скільки часу витрачаєш на дорогу?
> О котрій годині розпочинається  
> перший урок?
> О котрій годині ти повертаєшся додому  
> зі школи?
> Стоматолог — лікар (лікарка), що лікує зуби.
> Чистити зуби необхідно у (3 напрямки): спочатку — ззовні, 
> потім — зсередини, а вкінці — по жувальній поверхні. 
> Щітку слід тримати під кутом (45 градуси). Стоматологи радять 
> чистити зуби не менше (3 хвилини), а зубну щітку міняти кожні 
> (2–3 місяць).
> 	 	
> 4   Прочитай текст, ставлячи слова в дужках у потрібній формі.

> **Source:** golub, Grade 5
> **Section:** Сторінка 230
> **Score:** 0.50
>
> 230
> Шукаємо відповіді на запитання:
> Як стати гарним співрозмовником / гарною співрозмовницею?
> Відповідно до поставленого запитання сформулюйте особис-
> ті цілі.
> 521   Прочитайте «слова дня». Що вони означають? Чи всі вони можуть 
> поєднуватися зі словосполученнями «гарний співрозмовник», 
> «гарна співрозмовниця»? Чому?
> Про що «говорить» усмішка? Вона повідомляє: «Ви мені 
> подобаєтеся! Мені приємно спілкуватися з вами! Я радий / 
> рада вас бачити!» Усміхайтеся!
> 522   Розгляньте світлини. Які ознаки гарного співрозмовника очевид-
> ні? Назвіть їх.
> 523   Складіть діалог двох співрозмовників / співрозмовниць, один / 
> одна з яких любить осінь, а другий / друга — літо, використовую-
> чи подані речення.

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 54
> **Score:** 0.33
>
> 54
> Навчаюся доречно вживати слова в мовленні 
> Хто охороняє здоров’я дерев? Це 
> робить дятел. Цілий день проводить 
> лісовий лікар медичний огляд своєї 
> ділянки. Птах перелітає з дерева на 
> дерево, заглядає в кожну щілину. Від 
> гострого дзьоба незвичайного хірурга 
> не сховатися жодній шкідливій комасі 
> (За Юрієм Старостенком).
> Рожева  чайка
> Рожева чайка — окраса Арктики. Наче яскрава квітка, 
> ширяє рожева чайка серед суворої природи Півночі. Рожева 
> чайка харчується рибою. У незамерзлих ополонках Північного 
> Льодовитого океану проводить рожева чайка більшу частину 
> свого життя. 
> 6   Прочитай.

## Спеціалісти та обстеження

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 139
> **Score:** 0.50
>
> 139
> 3   Дай письмові відповіді на запитання. Записуй числівники словами. 
>   Що називають числівники? На яке питання відповідають?
>   Запиши утворений текст, подаючи числівники словами. 
> О котрій годині ти прокидаєшся? 
> Скільки часу ти одягаєшся?
> Коли виходиш із дому до школи?
> Скільки часу витрачаєш на дорогу?
> О котрій годині розпочинається  
> перший урок?
> О котрій годині ти повертаєшся додому  
> зі школи?
> Стоматолог — лікар (лікарка), що лікує зуби.
> Чистити зуби необхідно у (3 напрямки): спочатку — ззовні, 
> потім — зсередини, а вкінці — по жувальній поверхні. 
> Щітку слід тримати під кутом (45 градуси). Стоматологи радять 
> чистити зуби не менше (3 хвилини), а зубну щітку міняти кожні 
> (2–3 місяць).
> 	 	
> 4   Прочитай текст, ставлячи слова в дужках у потрібній формі.

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 54
> **Score:** 0.25
>
> 54
> Навчаюся доречно вживати слова в мовленні 
> Хто охороняє здоров’я дерев? Це 
> робить дятел. Цілий день проводить 
> лісовий лікар медичний огляд своєї 
> ділянки. Птах перелітає з дерева на 
> дерево, заглядає в кожну щілину. Від 
> гострого дзьоба незвичайного хірурга 
> не сховатися жодній шкідливій комасі 
> (За Юрієм Старостенком).
> Рожева  чайка
> Рожева чайка — окраса Арктики. Наче яскрава квітка, 
> ширяє рожева чайка серед суворої природи Півночі. Рожева 
> чайка харчується рибою. У незамерзлих ополонках Північного 
> Льодовитого океану проводить рожева чайка більшу частину 
> свого життя. 
> 6   Прочитай.

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 239
> **Score:** 0.50
>
> 236
> Додаток 2
> СЛОВНИЧОК ПАРОНІМІВ
> Військовий // воєнний
> Військовий – який стосується війська. Військовий лікар, військова 
> техніка, форма. 
> Воєнний – який стосується війни. Воєнний час.
> Дружний // дружній
> Дружний – який відбувається одночасно, злагоджено, спільно; 
> пов’язаний дружбою і згодою. Дружний колектив.
> Дружній – який ґрунтується на дружбі, прихильності, взаємно 
> доброзичливий. Дружній погляд.
> Економічний // економний
> Економічний – який стосується економіки. Економічний спад.
> Економний – ощадливий, який бережливо витрачає гроші, сили; 
> оснований на економії. Економна людина.
> Лікувати // лічити
> Лікувати – застосовувати ліки та інші засоби припинення болю, за-
> хворювання. Лікувати хворого, лікувати травами.
> Лічити – називати числа в послідовному порядку, рахувати.

## В аптеці

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 139
> **Score:** 0.50
>
> 139
> 3   Дай письмові відповіді на запитання. Записуй числівники словами. 
>   Що називають числівники? На яке питання відповідають?
>   Запиши утворений текст, подаючи числівники словами. 
> О котрій годині ти прокидаєшся? 
> Скільки часу ти одягаєшся?
> Коли виходиш із дому до школи?
> Скільки часу витрачаєш на дорогу?
> О котрій годині розпочинається  
> перший урок?
> О котрій годині ти повертаєшся додому  
> зі школи?
> Стоматолог — лікар (лікарка), що лікує зуби.
> Чистити зуби необхідно у (3 напрямки): спочатку — ззовні, 
> потім — зсередини, а вкінці — по жувальній поверхні. 
> Щітку слід тримати під кутом (45 градуси). Стоматологи радять 
> чистити зуби не менше (3 хвилини), а зубну щітку міняти кожні 
> (2–3 місяць).
> 	 	
> 4   Прочитай текст, ставлячи слова в дужках у потрібній формі.

> **Source:** vashulenko, Grade 2
> **Section:** Сторінка 87
> **Score:** 0.33
>
> Числівники можуть називати і порядок предметів 
> під час лічби. Тоді вони відповідають

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
