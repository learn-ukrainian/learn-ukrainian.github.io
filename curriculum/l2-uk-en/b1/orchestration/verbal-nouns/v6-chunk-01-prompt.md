<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Missing section heading: 'Підсумок та перехід до M22'
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

**Module:** 21: Віддієслівні іменники (B1, B1.3 [Verbs])
**Section to write:** Що таке віддієслівні іменники? (~600 words total)
**Word target for this section:** 600 words (aim for 660 to account for undershoot)

---

## Section Skeleton (follow this exactly)

## Що таке віддієслівні іменники? (~600 words total)
- P1 (~130 words): Introduction to the concept of nominalization. Explain how verbs (actions) can be transformed into nouns (things). Use Vashulenko Grade 3 examples: "зустріч" from "зустріти" and "плавання" from "плавати". Contrast the question "Що робити?" (to read) with "Що?" (reading).
- P2 (~150 words): Pedagogical rationale for B1 learners. Explain that verbal nouns are the backbone of academic, scientific, and formal Ukrainian. Illustrate how shifting from "Ми досліджували це питання" (active) to "Наше дослідження цього питання" (nominalized) changes the tone from personal to professional.
- P3 (~140 words): Semantic distinction between process and result. Use "навчання" as a prime example: it describes both the act of learning (процес) and the educational system/result (результат). Provide another example with "відкриття" (the act of opening vs. a scientific discovery).
- Dialogue (~110 words): Setting: A Ukrainian IT company during a sprint planning session. A Project Manager and a Developer discuss tasks. Use nouns: "тестування" (testing), "написання" (writing), "навчання" (training), and "читання" (reading). 
- P4 (~70 words): Transition to the mechanics of word formation. Briefly list the two main paths: suffixal (-ння, -ття, -іння) and zero-derivation (безафіксний спосіб).

---
## Full Plan (for reference)

<plan_content>
module: b1-021
level: B1
sequence: 21
slug: verbal-nouns
version: '3.0'
title: "Віддієслівні іменники"
subtitle: "Читання, бачення, відкриття — як дієслова стають іменниками"
focus: grammar
pedagogy: PPP
phase: "B1.3 [Verbs]"
word_target: 4000
objectives:
- "Learner can form віддієслівні іменники using productive suffixes
  -ння, -ття, -іння and understands the formation rules"
- "Learner can distinguish between суфіксальний and безафіксний ways
  of forming nouns from verbs (читання vs пошук)"
- "Learner can correctly spell іменники with -ння, -ття, -іння
  (подвоєння: читання, знання; -ття: відкриття, забуття)"
- "Learner can use віддієслівні іменники in formal and academic register
  instead of verbose verb constructions (здійснювати перевірку → перевірка)"
- "Learner can identify the register difference: віддієслівні іменники
  on -ння/-ття are bookish/formal, while безафіксні are neutral"
dialogue_situations:
- setting: 'At a Ukrainian IT company — discussing project processes: Тестування (n,
    testing) триватиме два дні. Після написання (n, writing) коду — перевірка. Навчання
    (n, training) нових працівників — наш пріоритет. Читання (n, reading) документації
    обов''язкове.'
  speakers:
  - Менеджер проєкту
  - Розробник (developer)
  motivation: 'Verbal nouns: тестування, написання, навчання, читання — -ння/-ття
    formations'
content_outline:
- section: "Що таке віддієслівні іменники?"
  words: 550
  points:
  - "Definition from Вашуленко Grade 3 p.107:
    Iменники можуть утворюватися від дієслів i називати дії:
    зустріч, плавання. They name the ACTION itself as a thing.
    читати → читання (the act of reading)
    бачити → бачення (the act of seeing, also: vision)
    відкрити → відкриття (discovery, opening)"
  - "Why this matters at B1: віддієслівні іменники are essential for
    academic and formal Ukrainian. They allow learners to nominalize
    actions: замість 'ми досліджували' → 'наше дослідження показало'.
    This is the language of news, science, and official documents."
  - "Categories: іменники що називають дію (процес) vs результат:
    навчання = process of learning AND the education itself.
    відкриття = process of opening AND the discovery made.
    Context determines which meaning applies."
- section: "Суфікс -ння (-ання, -яння) — найпродуктивніший"
  words: 700
  points:
  - "Formation rule: основа інфінітива + -ння.
    читати → читання, писати → писання, малювати → малювання,
    вивчати → вивчання (process) vs вивчення (result — see below).
    From Заболотний Grade 7 p.136: віддієслівні іменники на -ння, -ття
    є продуктивними в офіційно-діловому, науковому та
    публіцистичному стилях."
  - "Spelling rule: подвоєння н → -нн-:
    The суфікс is -нн- + закінчення -я, giving -ння.
    знати → знання [знан':а], читати → читання [читан':а].
    This подвоєння is consistent across all -ння forms.
    From Голуб Grade 6 p.107: суфікси -инн(я), -інн(я), -енн(я)."
  - "Variant: -іння from II дієвідміна verbs:
    говорити → говоріння, ходити → ходіння, бачити → бачення.
    The голосний before -ння depends on the дієвідміна:
    I: -а- → -ання (читання), -ува- → -ування (малювання).
    II: -и- → -іння (ходіння) or -ення (бачення).
    Some verbs have parallel forms: вивчання / вивчення (process / result)."
  - "Practice: form -ння nouns from 10-12 common verbs, noting which
    дієвідміна determines the vowel. Check against VESUM for edge cases."
- section: "Суфікс -ття та безафіксний спосіб"
  words: 650
  points:
  - "Formation with -ття: from verbs with stems ending in consonant clusters:
    відкрити → відкриття, забути → забуття, життя ← жити.
    пізнати → пізнання, but здобути → здобуття.
    Заболотний Grade 7 p.136: становлення, забуття — книжне забарвлення."
  - "Безафіксний спосіб (zero derivation) from Литвінова Grade 6 p.83:
    пошукати → пошук, підписати → підпис, раній → рань.
    'Нові слова можна утворити також усіканням частин слова
    (префіксів i суфіксів). Цей спосіб словотворення має назву
    безафіксний.' Many common words are formed this way:
    біг (← бігти), хід (← ходити), лет (← летіти),
    спів (← співати), крик (← кричати)."
  - "Register difference:
    -ння/-ття forms are bookish/formal: дослідження, навчання, спілкування.
    Безафіксні forms are neutral/colloquial: біг, хід, крик, спів.
    Compare: вивчення цього питання (formal) vs пошук відповіді (neutral).
    Learners practise choosing the right register for context."
- section: "Віддієслівні іменники у реченні"
  words: 600
  points:
  - "Syntactic roles: віддієслівні іменники function as regular nouns —
    they decline, take adjectives, and serve as subjects/objects.
    Вивчення мови потребує часу. (subject)
    Я люблю читання. (object)
    Після закінчення курсу... (after preposition)
    They require the same case government as their source verb:
    досліджувати проблему (Зн.) → дослідження проблеми (Р.)."
  - "Noun phrase expansion:
    навчання → навчання дітей → навчання дітей у школі
    The verbal noun heads a phrase that mirrors the verb's arguments:
    вчити дітей у школі → навчання дітей у школі.
    This is how Ukrainian builds complex academic phrases."
  - "Avoiding overuse — a style concern:
    Too many -ння forms make text heavy and bureaucratic.
    *Здійснення забезпечення виконання... — мовний канцелярит.
    Better: Забезпечити виконання... (use verb when possible).
    Антоненко-Давидович principle: use nouns for concepts, verbs for actions."
- section: "Практика: від дієслова до іменника"
  words: 550
  points:
  - "Exercise block 1 — Formation:
    Given 12-15 verbs, form the віддієслівний іменник:
    говорити → говоріння, створити → створення, жити → життя,
    будувати → будування/будівництво, мислити → мислення.
    Some verbs have two forms: note the semantic difference."
  - "Exercise block 2 — In context:
    Replace verbose constructions with віддієслівні іменники:
    'Коли ми вивчали цю тему...' → 'Під час вивчення цієї теми...'
    'Те, що він приїхав, здивувало нас' → 'Його приїзд здивував нас.'
    6-8 transformations from colloquial to formal register."
  - "Exercise block 3 — Register identification:
    Given pairs (читання / крик, дослідження / пошук, спілкування / розмова),
    label each as formal or neutral. Place them in appropriate sentences:
    наукове _____ (дослідження) vs щоденний _____ (пошук)."
- section: "Читання: віддієслівні іменники у новинах"
  words: 600
  points:
  - "A short Ukrainian news article (adapted B1 level) using multiple
    віддієслівні іменники naturally: будівництво, забезпечення,
    відновлення, виробництво, навчання, дослідження.
    Topic: education or technology in Ukraine."
  - "Comprehension tasks that test LANGUAGE, not content:
    — Знайдіть у тексті всі віддієслівні іменники.
    — Від яких дієслів вони утворені?
    — Яким способом утворено: суфіксальним чи безафіксним?
    — Замініть два віддієслівні іменники на дієслівні конструкції."
  - "Production: learners write 3-4 sentences about their city/country
    using at least 3 віддієслівні іменники. Model:
    Будівництво нових шкіл — це важливе завдання.
    Навчання української мови потребує практики.
    Відкриття нового музею відбудеться наступного місяця."
- section: "Підсумок та перехід до M22"
  words: 350
  points:
  - "Summary: віддієслівні іменники — іменники, утворені від дієслів,
    що називають дії як предмети. Суфікси -ння, -ття, -іння.
    Безафіксний спосіб. Регістрові відмінності.
    Self-check: Я можу утворити іменник від дієслова ✓/✗,
    Я знаю правопис -ння, -ття ✓/✗,
    Я можу перетворити дієслівну конструкцію на іменникову ✓/✗."
  - "Preview: M22 — Зворотні дієслова. The -ся/-сь suffix that turns
    transitive verbs reflexive: мити → митися, бачити → бачитися.
    This is another productive way Ukrainian modifies verb meaning."
vocabulary_hints:
  required:
  - "віддієслівний іменник (verbal noun — noun derived from a verb)"
  - "читання (reading — verbal noun from читати)"
  - "бачення (vision, seeing — verbal noun from бачити)"
  - "відкриття (discovery, opening — verbal noun from відкрити)"
  - "навчання (learning, education — verbal noun from навчати)"
  - "дослідження (research, study — verbal noun from досліджувати)"
  - "знання (knowledge — verbal noun from знати)"
  - "спілкування (communication — verbal noun from спілкуватися)"
  - "створення (creation — verbal noun from створити)"
  - "забуття (oblivion, forgetting — verbal noun from забути)"
  - "пошук (search — zero-derivation from пошукати)"
  - "підпис (signature — zero-derivation from підписати)"
  - "суфіксальний (suffixal — word formation method)"
  - "безафіксний (zero-derivation — word formation without affixes)"
  recommended:
  - "становлення (formation, establishment — bookish)"
  - "будівництво (construction — from будувати)"
  - "виробництво (production, manufacturing)"
  - "забезпечення (provision, ensuring)"
  - "відновлення (restoration, renewal)"
  - "мислення (thinking, thought process)"
  - "приїзд (arrival — zero-derivation from приїхати)"
  - "канцелярит (bureaucratese — overuse of nominal style)"
  - "продуктивний (productive — in word formation sense)"
  - "основа інфінітива (infinitive stem — base for formation)"
activity_hints:
- type: fill-in
  focus: "Form the correct віддієслівний іменник from a given verb in sentence context"
  items: 10
- type: match-up
  focus: "Match verbs to their derived nouns (читати→читання, відкрити→відкриття, бігти→біг)"
  items: 10
- type: group-sort
  focus: "Sort verbal nouns by formation type: суфіксальний (-ння/-ття) vs безафіксний"
  items: 10
- type: sentence-builder
  focus: "Transform verb phrases into nominal phrases (Ми вивчали → Вивчення...)"
  items: 6
- type: quiz
  focus: "Identify register: which verbal noun is formal vs neutral? Choose appropriate form for context"
  items: 8
connects_to:
- "b1-020 (Наказовий спосіб — verb mood mastery, now verb-to-noun transition)"
- "b1-022 (Зворотні дієслова — another verb modification: -ся/-сь)"
- "b1-024 (Творення дієслів — completes the verb formation picture)"
- "b1-044 (Творення назв осіб i місць — extends noun word formation)"
prerequisites:
- "b1-020 (Imperative nuances — completes mood system before word formation)"
grammar:
- "Суфіксальне творення: -ння (читання), -ття (відкриття), -іння (ходіння), -ення (бачення)"
- "Безафіксний спосіб: пошук, підпис, біг, хід, крик, спів"
- "Подвоєння in -ння forms: читання [читан':а], знання [знан':а]"
- "Register: -ння/-ття = bookish/formal; безафіксні = neutral"
- "Case government transfer: досліджувати проблему → дослідження проблеми"
- "Avoiding канцелярит: verbs for actions, nouns for concepts"
register: академічний
references:
- title: "Вашуленко Grade 3, p.107"
  notes: "Iменники утворюються від дієслів i називають дії: зустріч, плавання.
    Basic introduction to verbal noun concept."
- title: "Голуб Grade 6, p.107"
  notes: "Написання іменників із суфіксами -инн(я), -інн(я), -енн(я), -ен(я).
    Spelling rules table with examples."
- title: "Литвінова Grade 6, p.83"
  notes: "Безафіксний спосіб словотворення: пошук ← пошукати, підпис ← підписати.
    Definition and examples of zero derivation."
- title: "Заболотний Grade 7, p.136"
  notes: "Віддієслівні іменники на -ння, -ття: становлення, забуття.
    Книжне забарвлення; продуктивні в офіційно-діловому i науковому стилях."

</plan_content>

---

## Knowledge Packet

<knowledge_packet>
# Verified Knowledge Packet: Віддієслівні іменники
**Module:** verbal-nouns | **Phase:** B1.3 [Verbs]
**Textbook grades searched:** 1, 2, 3, 5

---

## Що таке віддієслівні іменники?

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 109
> **Score:** 0.50
>
> Навчаюся розпізнавати іменники, які називають  
> ознаки і дії
> 	
>   Складіть і запишіть речення із трьома утвореними іменниками 
> (на вибір).
> Іменники можуть утворюватися від прикметників і називати 
> ознаки: блакить, краса. Іменники можуть утворюватися 
> від дієслів і називати дії: зустріч, плавання.
> сміливий — сміливість
> мужній — мужність 
> радіти — радість
> читати — читання
> Досліди, яке сло-
> во з пари слів є 
> іменником.
> Я — дослідник
> Я — дослідниця
> молодий
> молодість
> гра
> гравець
> грає
> швидкий
> ?
> ?
> ?
> бігає
> чемний
> ?
> ?
> ?
> читає
> щирий
> ?
> ?
> ?
> співає
> Який?  
> Що?  
> Що  
> робить?  
> Що?  
> Хто?  
> 	 	
> 19   Доберіть спільнокореневі іменники до прикметників і дієслів. 
> Запишіть їх. 
> 	 	
> 20   Поєднай частини приказок і запиши їх. Підкресли іменники.
> 109
> 18   Прочитай пари слів і порівняй їх.

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 116
> **Score:** 0.33
>
> 116
> Досліди, чи всі іменни-
> ки можуть мати фор-
> му однини і множини.
> Я — дослідник
> Я — дослідниця
> Спостерігаю за іменниками, які вживаються тільки  
> в однині або тільки у множині
> 6   Прочитай слова і порівняй їх. 
> 	
>   Визначте число виділених іменників. Зробіть висновок, у якій 
> числовій формі вживаються ці іменники.
> дружба
> птаство
> дітвора
> сани
> окуляри
> двері
> Поясни, що спільне є між цими словами, а що — відмінне.
> Чи можна утворити форму множини від іменників у лівому 
> стовпчику?
> Чи можна утворити форму однини від іменників у правому 
> стовпчику?
> Зроби висновок про особливості вживання деяких іменників.
> Деякі іменники можуть уживатися тільки в однині: 
> дитинство, листя, молодь.
> Деякі іменники можуть уживатися тільки у множині: 
> радощі, іменини, ворота.
> 	 	
> 7   Прочитайте.

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 146
> **Score:** 0.25
>
> 146
> Зв’язок дієслова з іменником 
> Навчаюся встановлювати зв’язок дієслова  
> з іменником у реченні
> 46
> 1   Прочитай і порівняй. До яких частин мови належать виділені слова?
> Приліт птахів.
> Що називають виділені слова?
> На які питання вони відповідають?
> До якої частини мови вони  
> належать?
> Птахи прилітають.
> Досліди, як відріз-
> нити дієслово від 
> іменника.
> Я — дослідник
> Я — дослідниця
> Дієслова в реченні зв’язані з іменниками.
> 	 	
> 2   Прочитайте текст. Доберіть до нього заголовок. 
> Швидко настає вечір у густому лісі. 
> Темні тіні лягають під деревами. По-
> чорніли густі ялини. Сіло за деревами 
> вечірнє сонце. У лісі запахло смолою і 
> сосновою глицею.
> Ще не сплять усі птахи. Ось на стовбурі дерева сидить 
> дятел. Навколо нього крутяться прудкі синиці.

## Суфікс -ння (-ання, -яння) — найпродуктивніший

> **Source:** ponomarova, Grade 3
> **Section:** Сторінка 55
> **Score:** 0.25
>
> 55
> 2. Спиши повідомлення Читалочки. Підкресли службові
> слова.  Знайди слова  з  префіксами  й  познач  їх.
> Префікс — це частина слова. Його пишемо разом
> зі словом.
> Службові слова пишемо окремо від інших слів.
> У Кам’янці-Подільському побудований найви-
> щий міст в Україні — «Стрімка лань». З мосту
> безстрашні сміливці стрибають на канатах униз.
> 4. Скористайся порадою Ґаджика і запиши сполучення слів 
> без дужок.
> Між службовим і наступним словом можна встави-
> ти ще одне слово. Наприклад: за дерево — за високе
> дерево; без хліба — без чорного хліба.
> 3. Ґаджик  хоче  навчити  тебе  розрізняти  префікси  і  служ-
> бові  слова.  Прочитай  його  пораду.
> (за) писати (на) дошці 
>       (в) ходити (в) будинок
> (до) нести (до) дверей 
>       (за) ховатись (за) штору
> 5.

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 65
> **Score:** 0.33
>
> 65
> Частини основи — префікс, корінь, суфікс —  на письмі 
> позначаються так: 
> підводн ий  .
> 	 	
> 3   Запишіть слова, позначте за-
> кінчення та основу. 
> Вода, водний, підводний.
> Лікарня, вечірній, прихід, баранчик, 
> житловий, жартівник, премудрий,  прадід.
> Живе один батько, 
> тисячі синів має,
> усім шапки справляє,
> а сам не має.
> 	
>   У словах відгадки визнач закінчення та основу.
> 	
>   Склади і запиши з цими словами речення.
> 4   Запиши слова, познач у них закінчення та 
> основу. 
> Визнач спільну частину основи у записаних  словах.  
> Це — корінь.
> Визнач частину основи перед коренем. Це — префікс.
> Визнач частину основи між коренем і закінченням.

## Суфікс -ття та безафіксний спосіб

## Віддієслівні іменники у реченні

> **Source:** vashulenko, Grade 2
> **Section:** Сторінка 104
> **Score:** 0.50
>
> НАВЧАЮСЯ РОЗПІЗНАВАТИ РЕЧЕННЯ 
> ЗА ЙОГО ОСНОВНИМИ ОЗНАКАМИ
> Я — учителька
> Прочитай і розкажи 
> ; у класі.
> 1
> розпізнаЮ 
> складаю
> Я — учитель
> РЄчєння виражає закінчену думку.
> Слова в реченні зв'язані між собою за змістом.
> і[ Прочитай текст. Кінець кожного 
> речення позначай зниженням 
> голосу і паузою. Полічи кількість 
> речень.
> Щодня ти ходиш до школи. 
> У школі тебе навчають учителі. 
> Вони хочуть, щоб діти вчилися 
> з цікавістю. Твій обов’язок —
> добре вчитися.
> • Запиши друге речення. Поясни думку, висловлену в цьому 
> реченні.
> 2| Поєднайте в речення сполучення слів обох колонок. 
> Запишіть утворені речення.
> На уроці математики 
> Учні записали 
> Учителька пояснювала
> у зошит умову задачі. 
> способи читання прикладів. 
> учні розв’язували приклади.
> 104^

## Практика: від дієслова до іменника

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 109
> **Score:** 0.50
>
> Навчаюся розпізнавати іменники, які називають  
> ознаки і дії
> 	
>   Складіть і запишіть речення із трьома утвореними іменниками 
> (на вибір).
> Іменники можуть утворюватися від прикметників і називати 
> ознаки: блакить, краса. Іменники можуть утворюватися 
> від дієслів і називати дії: зустріч, плавання.
> сміливий — сміливість
> мужній — мужність 
> радіти — радість
> читати — читання
> Досліди, яке сло-
> во з пари слів є 
> іменником.
> Я — дослідник
> Я — дослідниця
> молодий
> молодість
> гра
> гравець
> грає
> швидкий
> ?
> ?
> ?
> бігає
> чемний
> ?
> ?
> ?
> читає
> щирий
> ?
> ?
> ?
> співає
> Який?  
> Що?  
> Що  
> робить?  
> Що?  
> Хто?  
> 	 	
> 19   Доберіть спільнокореневі іменники до прикметників і дієслів. 
> Запишіть їх. 
> 	 	
> 20   Поєднай частини приказок і запиши їх. Підкресли іменники.
> 109
> 18   Прочитай пари слів і порівняй їх.

> **Source:** kravcova, Grade 2
> **Section:** Сторінка 87
> **Score:** 0.33
>
> 87
> 312. Утвори прислів’я. 
> 313. 1.	 Вибери навчальний предмет. 
> 2.	 Напиши чотири дієслова, які означають навчальні дії.
> 314. До поданих іменників добери дієслова за зразком та 
> запиши утворені пари.
> 315. 1.	 Прочитай прислів’я та поясни їх зміст.
> Не говори, що знаєш, але знай, що говориш. Сказав, як 
> сокирою одрубав. Що вимовиш язиком, то не витягнеш і волом.
> 2.	 Спиши. Підкресли дієслова.
> 2 учиться — 4 пригодиться. 3 завжди 1 Потрібно
> Зразок. Радість — радіти.
> радість	
> 	
> 	
> сум	 	
> 	
> тривога
> співчуття	 	
> 	
> жаль		
> 	
> обурення
> гордість	 	
> 	
> повага	
> 	
> заздрість
> 316. 1.	 Прочитай вірш.

> **Source:** vashulenko, Grade 2
> **Section:** Сторінка 80
> **Score:** 0.50
>
> НАВЧАЮСЯ СКЛАДАТИ РЕЧЕННЯ 
> З ДІЄСЛОВАМИ
> Прочитайте речення. Простежте, 
> які різні дії означає слово іде.
> складаю
> Іде катер. Іде поїзд. Іде зима. Іде час. Іде концерт.
> • Замініть у кожному реченні слово іде дієсловом, близьким 
> за значенням. Скористайтеся довідкою. Запишіть речення
> за зразком.
> Іде катер. 
> Пливе катер.
> ? годинник
> Довідка
> Відбувається, їде, минає, пливе, настає.
> б| Розглянь малюнки. Напиши, хто як пересувається,
> використавши дієслова з довідки.
> На які питання 
> відповідають 
> дієслова?
> Дові

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
