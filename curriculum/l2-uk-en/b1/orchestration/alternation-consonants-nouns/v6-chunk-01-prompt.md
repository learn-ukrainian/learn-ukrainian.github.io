<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Too short: 2622 words (target: 4000, minimum: 3400)
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

**Module:** 5: Чергування приголосних (іменники) (B1, B1.1 [Baselines & Morphophonemics])
**Section to write:** Що таке чергування приголосних? (~550 words total)
**Word target for this section:** 550 words (aim for 605 to account for undershoot)

---

## Section Skeleton (follow this exactly)

## Що таке чергування приголосних? (~550 words total)
- P1 (~150 words): [Establish a bridge from M08 (vowel alternations), explaining that while vowel changes often happen in the root, consonant alternations typically affect the final sound of the root/stem. Introduce the term 'чергування' as a systematic, predictable shift that occurs during declension or word formation.]
- P2 (~150 words): [Introduce the core "three-way pattern" defined in Avramenko Grade 5: the velar group (задньоязикові) [г], [к], [х] each have two potential alternation targets. Contrast the hard starting points with their soft or hushing results (г — з — ж, к — ц — ч, х — с — ш) to give learners a map of the entire module.]
- P3 (~150 words): [Explain the phonetic mechanism: why these sounds change. Discuss the role of historical "front vowels" (like the modern 'i' or the vocative 'e') in pulling the back-of-the-mouth velars forward, transforming them into sibilants or hushing sounds. Use the analogy of "lazy speech" or "tongue efficiency."]
- P4 (~100 words): [Briefly touch upon the historical context of Proto-Slavic and Old East Slavic (давньоукраїнська мова), explaining that these aren't "irregularities" but are the very fossils of the language's evolution that make Ukrainian melodic and easy to pronounce.]

---
## Full Plan (for reference)

<plan_content>
module: b1-005
level: B1
sequence: 5
slug: alternation-consonants-nouns
version: '3.0'
title: "Чергування приголосних (іменники)"
subtitle: "Друг — друже — друзі: як змінюються приголосні в іменниках"
focus: grammar
pedagogy: PPP
phase: "B1.1 [Baselines & Morphophonemics]"
word_target: 4000
objectives:
  - "Learner can predict and produce the first palatalization [г/к/х] -> [ж/ч/ш] in
    кличний відмінок and word formation (друг — друже, козак — козаче, пастух — пастуше)"
  - "Learner can predict and produce the second palatalization [г/к/х] -> [з'/ц'/с']
    in давальний and місцевий відмінки (нога — на нозі, рука — на руці, Ольга — Ользі)"
  - "Learner can identify which case or word-formation context triggers which alternation
    type (first vs. second palatalization)"
  - "Learner can apply consonant alternation rules to unfamiliar nouns and proper
    names, avoiding common errors in case forms"
dialogue_situations:
  - setting: 'At a Львівська книгарня (f, Lviv bookshop) — discussing authors and
      book titles, noticing consonant changes: книга→у книжці (г→ж), рука→у руці (к→ц),
      друг→друже (г→ж, vocative), вухо→у вусі (х→с).'
    speakers:
      - Книгар (bookseller)
      - Покупець
    motivation: 'Consonant alternation in nouns: г→ж, к→ц, х→с in locative and vocative'
content_outline:
  - section: "Що таке чергування приголосних?"
    words: 500
    points:
      - "Bridge from M08 (alternation-vowels): learners now understand that sounds
        change systematically in Ukrainian word forms. Vowel alternations affect the
        root vowel; consonant alternations affect the final consonant of the root
        or stem. Авраменко Grade 5 p.114: 'Найпоширенішими є такі чергування приголосних:
        [г] — [з] — [ж], [к] — [ц] — [ч], [х] — [с] — [ш].'"
      - "The three-way pattern: each задньоязиковий consonant [г], [к], [х] has TWO
        possible alternation targets depending on the phonetic environment. This module
        teaches learners to predict which one appears where. The system is regular
        and productive."
      - "Historical context (brief): these alternations trace back to давньоукраїнська
        мова and the effect of front vowels on back consonants. Understanding the
        history is optional but helps learners see the logic, not just memorize."
  - section: "Перша палаталізація: [г/к/х] -> [ж/ч/ш]"
    words: 750
    points:
      - "The pattern from Заболотний Grade 5 p.116 (section 28): [г] -> [ж]: друг
        — дружити, нога — ніжка, ворог — вороже [к] -> [ч]: рука — ручка, молоко —
        молочний, козак — козаче [х] -> [ш]: кожух — кожушок, вухо — вушко, пастух
        — пастуше This alternation appears in word formation (suffixes -к-, -н-) and
        in кличний відмінок."
      - "Кличний відмінок with first palatalization (Глазова Grade 10 p.209): друг
        — друже, козак — козаче, чоловік — чоловіче, хлопець — хлопче (also [ц'] ->
        [ч]), юнак — юначе, вітязь — вітязю (м'яка група — no alternation). Rule:
        II відміна, тверда група, закінчення -е triggers the alternation. М'яка група
        takes -ю with no alternation."
      - "Word formation with first palatalization: нога — ніжка — ніженька, рука —
        ручка — рученька, книга — книжка — книжковий, молоко — молочний — молочар.
        Adjective suffixes -н-, -ськ- also trigger it: Прага — празький, Норвегія
        — норвезький."
      - "Reading practice: Ukrainian folk sayings and прислів'я that use кличний відмінок
        naturally. Learners identify the alternation in each: 'Терпи, козаче, отаманом
        будеш' (козак -> козаче)."
  - section: "Друга палаталізація: [г/к/х] -> [з'/ц'/с']"
    words: 750
    points:
      - "The pattern from Авраменко Grade 5 p.114: [г] -> [з']: нога — на нозі, Ольга
        — Ользі, дорога — на дорозі [к] -> [ц']: рука — на руці, ріка — на ріці, дочка
        — дочці [х] -> [с']: муха — мусі, свекруха — свекрусі, стріха — на стрісі
        This alternation appears in давальний and місцевий однини of I відміна (feminine
        nouns ending in -а/-я)."
      - "Why давальний and місцевий? The endings -i trigger this alternation before
        them. Compare: нога: Н.в. нога, Р.в. ноги, Д.в. нозі, Зн.в. ногу, Ор.в. ногою,
        М.в. (на) нозі, Кл.в. ного! The alternation ONLY appears before -i in Д.в.
        and М.в."
      - "Proper names follow the same pattern: Ольга — Ользі, Палажка — Палажці, Одарка
        — Одарці. Geographic names: Прага — у Празі, Рига — у Ризі, Америка — в Америці
        (but: Африка — в Африці). Practice: learners decline proper names in давальний
        and місцевий."
      - "Common errors to avoid: Mixing up the two palatalizations: *на нозі is correct
        (second), but *на ножі would be wrong (that is first palatalization, wrong
        context). The кличний uses first ([ж/ч/ш]), while давальний/місцевий use second
        ([з'/ц'/с'])."
  - section: "Чергування [ц'] -> [ч] та інші"
    words: 500
    points:
      - "From Глазова Grade 10 p.209: хлопець — хлопче, швець — шевче, молодець —
        молодче. The soft [ц'] alternates with [ч] in кличний відмінок. This is a
        separate alternation from the [к]->[ч] pattern."
      - "Minor alternations in nouns: [с] -> [ш]: колесо — на колішні (rare, mostly
        in fixed forms) [з] -> [ж]: князь — княже (кличний відмінок) These are less
        productive but appear in common words."
      - "Practice: learners build a complete table of alternation types, contexts,
        and examples. The table becomes a reference for future modules on verb alternations
        (M10)."
  - section: "Чергування у відмінюванні іменників II відміни"
    words: 550
    points:
      - "Systematic view: how consonant alternations interact with the full declension
        paradigm of II відміна masculine nouns. Using друг as a model: Н.в. друг,
        Р.в. друга, Д.в. другу/другові, Зн.в. друга, Ор.в. другом, М.в. (на) другу/другові,
        Кл.в. друже. Only the кличний shows alternation in masculine nouns."
      - "Comparison with I відміна feminine nouns: нога: alternation in Д.в. (нозі)
        and М.в. (на нозі). This contrast helps learners predict WHERE to expect the
        change: masculine nouns — кличний; feminine nouns — давальний/місцевий."
      - "Литвінова Grade 6 p.159: закінчення іменників II відміни в кличному відмінку
        однини — systematic table of endings by group (тверда, м'яка, мішана) with
        alternation rules."
  - section: "Чергування у власних назвах і географічних іменах"
    words: 500
    points:
      - "Ukrainian place names and personal names follow the same rules: Прага — у
        Празі, Рига — у Ризі, Одарка — Одарці. But some foreign names resist alternation:
        Пенелопа — Пенелопі (no alternation — foreign name). Learners need to know
        which names follow Ukrainian patterns."
      - "Cultural context: кличний відмінок in everyday Ukrainian. Addressing people:
        Олеже! Марічко! Iгоре! Тарасе! Understanding alternation = correct forms of
        address. Common mistakes by L2 speakers: *Олего! (wrong — should be Олеже)."
      - "Practice: learners write short dialogues using кличний відмінок with proper
        names, applying the correct alternation."
  - section: "Підсумок: таблиця чергувань"
    words: 450
    points:
      - "Complete reference table: | Consonant | First (Кл.в., word formation) | Second
        (Д.в./М.в.) | | [г] | [ж] | [з'] | | [к] | [ч] | [ц'] | | [х] | [ш] | [с']
        | | [ц'] | [ч] (Кл.в. only) | — |"
      - "Self-check in Ukrainian: Дайте відповіді на запитання: 1. Які приголосні
        чергуються у кличному відмінку слова 'друг'? 2. Яке чергування відбувається
        у слові 'на нозі'? 3. Утворіть кличний відмінок: козак, юнак, хлопець. 4.
        Поставте у давальний відмінок: Ольга, книга, рука."
      - "Preview of next module: Чергування приголосних (дієслова) — the same consonants
        alternate in verb conjugation, but with different triggers and patterns."
vocabulary_hints:
  required:
    - "чергування (alternation — systematic sound change between forms)"
    - "приголосний (consonant — sound made with obstruction)"
    - "палаталізація (palatalization — softening of a consonant)"
    - "кличний відмінок (vocative case — used for direct address)"
    - "давальний відмінок (dative case)"
    - "місцевий відмінок (locative case)"
    - "задньоязиковий (velar — consonant formed at the back of the mouth)"
    - "відміна (declension class — noun classification by ending pattern)"
    - "тверда група (hard group — nouns with hard stem-final consonant)"
    - "м'яка група (soft group — nouns with soft stem-final consonant)"
    - "мішана група (mixed group — nouns with шиплячий stem-final)"
    - "закінчення (ending — inflectional morpheme)"
    - "звертання (form of address — using кличний відмінок)"
    - "корінь (root — core morpheme of a word)"
  recommended:
    - "шиплячий (hushing consonant — ж, ч, ш, дж)"
    - "свистячий (sibilant — з, ц, с, дз)"
    - "словотворення (word formation — creating new words from roots)"
    - "прислів'я (proverb — traditional folk saying)"
    - "орфограма (orthographic rule — spelling pattern)"
    - "спільнокореневий (cognate — sharing the same root)"
    - "однина (singular number)"
    - "множина (plural number)"
    - "продуктивний (productive — pattern applicable to new words)"
    - "непродуктивний (unproductive — pattern limited to existing words)"
activity_hints:
  - type: quiz
    focus: "Identify which palatalization type is present: first ([ж/ч/ш]) or second
      ([з'/ц'/с']), given a word pair (друг-друже vs. нога-нозі)"
    items: 8
  - type: fill-in
    focus: "Write the correct кличний відмінок form of masculine nouns (e.g., козак
      -> козач___, друг -> друж___)"
    items: 8
  - type: fill-in
    focus: "Write the correct давальний/місцевий form of feminine nouns (e.g., нога
      -> на ноз___, рука -> руц___)"
    items: 6
  - type: match-up
    focus: "Match base forms with their alternated case forms (e.g., Ольга <-> Ользі,
      козак <-> козаче)"
    items: 8
  - type: error-correction
    focus: "Find and fix consonant alternation errors in sentences (e.g., *на ножі
      -> на нозі, *козаже -> козаче)"
    items: 6
connects_to:
  - "b1-008 (alternation-vowels — vowel alternations as the first morphophonemic rule)"
  - "b1-010 (alternation-consonants-verbs — same consonants alternate in verbs)"
  - "b1-012 (noun-subclasses-masculine — declension of -ар/-яр/-ин nouns)"
prerequisites:
  - "A2 completion (learner knows noun declension basics, all 7 cases)"
  - "b1-001 (metalanguage-phonetics — приголосний classification)"
  - "b1-008 (alternation-vowels — concept of чергування)"
grammar:
  - "First palatalization: [г/к/х] -> [ж/ч/ш] in кличний and word formation"
  - "Second palatalization: [г/к/х] -> [з'/ц'/с'] in давальний/місцевий"
  - "Alternation [ц'] -> [ч] in кличний відмінок"
  - "Interaction of alternations with declension paradigms (I and II відміна)"
  - "Application to proper names and geographic names"
register: академічний
references:
  - title: "Авраменко Grade 5, p.114-115"
    notes: "Чергування приголосних звуків (section 50): three-way pattern [г]-[з]-[ж],
      [к]-[ц]-[ч], [х]-[с]-[ш] with examples and exercises."
  - title: "Заболотний Grade 5, p.116-119"
    notes: "Чергування приголосних звуків (section 28): systematic presentation with
      друг-друзі-дружити, молоко-молоці-молочний."
  - title: "Глазова Grade 10, p.209"
    notes: "Особливості кличного відмінка: complete table of consonant alternations
      before -е in кличний, including [ц']->[ч]."
  - title: "Литвінова Grade 6, p.159"
    notes: "Закінчення іменників II відміни в кличному відмінку однини: systematic
      by group (тверда, м'яка, мішана)."
  - title: "Авраменко Grade 10, p.175"
    notes: "Особливості кличного відмінка: dialogue-based presentation, Валеріє vs.
      Валерію gender distinction."

</plan_content>

---

## Knowledge Packet

<knowledge_packet>
# Verified Knowledge Packet: Чергування приголосних (іменники)
**Module:** alternation-consonants-nouns | **Phase:** B1.1 [Baselines & Morphophonemics]
**Textbook grades searched:** 1, 2, 3, 5

---

## Що таке чергування приголосних?

*No textbook results found for: Що таке чергування приголосних задньоязиковий давньоукраїнська мова*

## Перша палаталізація: [г/к/х] -> [ж/ч/ш]

*No textbook results found for: Перша палаталізація Заболотний друг дружити нога ніжка ворог вороже рука ручка*

## Друга палаталізація: [г/к/х] -> [з'/ц'/с']

*No textbook results found for: Друга палаталізація з' ц' с' Авраменко нога на нозі Ольга Ользі дорога*

## Чергування [ц'] -> [ч] та інші

*No textbook results found for: Чергування ц' та інші Глазова хлопець хлопче швець шевче молодець молодче*

## Чергування у відмінюванні іменників II відміни

*No textbook results found for: Чергування у відмінюванні іменників відміни відміна друг друга другу другові Зн Ор нога*

## Чергування у власних назвах і географічних іменах

*No textbook results found for: Чергування у власних назвах і географічних іменах Прага у Празі Рига у Ризі Одарка Одарці Пенелопа Пенелопі кличний відмінок*

## Підсумок: таблиця чергувань

*No textbook results found for: Підсумок таблиця чергувань Кл з' ц' с' Дайте відповіді на запитання Які приголосні чергуються у кличному відмінку слова 'друг' Яке чергування відбувається у слові 'на нозі' Утворіть кличний відмінок*

## Grammar Reference

*No grammar results for: кличний з' ц' с' давальний місцевий кличний відмінок відміна*


## МійКлас Theory (miyklas.com.ua)

*Ukrainian school curriculum theory — use this terminology and teaching approach.*

### Приголосні м'які й тверді, дзвінкі й глухі
> **Source:** МійКлас — [Приголосні м'які й тверді, дзвінкі й глухі](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/fonetika-grafika-orfoepiia-orfografiia-14565/prigolosni-m-iaki-i-tverdi-dzvinki-i-glukhi-vimova-prigolosnikh-g-i-g-40885)

### Теорія:

*www.ua.pistacja.tv*  
Приголосні звуки – це звуки, що творяться за допомогою голосу й шуму або лише шуму. При їх вимові струмінь видихуваного повітря натрапляє на різні перепони органів мовлення \(язик, зуби, губи\), унаслідок чого виникають шуми, які є основою саме приголосних звуків.
Зверни увагу\!
Тверді і м’які приголосні — це різні звуки, для позначення яких на письмі використовують ті самі літери: \[лин\] лин – \[л'ін'\] лінь.
Напівпом'якшені звуки — це **відтінки **твердих звуків: \[в’інок\] вінок — \[виниекнути\] виникнути.
В українській мові є такі м’які приголосні: \[д'\], \[т'\], \[з'\], \[с'\], \[ц'\], \[л'\], \[н'\], \[дз'\], \[р'\].
 
Запам'ятати ці приголосні  можна, вивчивши таку фразу: «Де Ти З'їСи Ці ЛиНи, аДЗуР».

Звук \[й\] завжди м’який.

### Вимова приголосних звуків. Уподібнення приголосних
> **Source:** МійКлас — [Вимова приголосних звуків. Уподібнення приголосних](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/fonetika-grafika-orfoepiia-orfografiia-14565/vimova-prigolosnikh-zvukiv-upodibnennia-prigolosnikh-zvukiv-42793)

### Теорія:

*www.ua.pistacja.tv*  
Вимова приголосних звуків
Для української мови характерна  **виразна** вимова приголосних звуків, зокрема дзвінких. Вони завжди вимовляються **чітко**. Особливо в кінці складу та слова й перед голосними: стежка \[сте́жка\],  виріб \[ви́р'іб\], дружина \[дружи́на\]. Але бувають випадки, коли звуки важко відрізнити один від одного.
Що таке уподібнення приголосних і коли воно відбувається
У процесі мовлення один приголосний стає схожий за звучанням на інший, тобто зазнає впливу сусіднього звуку. Таке явище називається уподібненням.
Приклад:
Слово боротьба пишемо з літерою т \(боротися\), а вимовляємо й чуємо \[бород'ба́\], бо глухий \[т'\] уподібнився під впливом дзвінкого \[б\] до  \[д'\].
Зверни увагу\!
Сумнівний приголосний можна легко перевірити.

### Спрощення в групах приголосних
> **Source:** МійКлас — [Спрощення в групах приголосних](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/fonetika-grafika-orfoepiia-orfografiia-14565/sproshchennia-v-grupakh-prigolosnikh-41974)

### Теорія:

*www.ua.pistacja.tv*  
При вiдмiнюваннi слова або його твореннi інколи виникає важкий для вимови збiг приголосних звукiв. Тому в процесi мовлення один із таких приголосних випадає, тобто вiдбувається спрощення \(правило «третього зайвого»\). Зазвичай спрощені звуки не пишемо.
Спрощення приголосних відбувається в таких **групах** приголосних:
- \[ждн\], \[здн\] → \[жн\], \[зн\] \(випадає д\): проїздити – проїзний, тиждень – тижня;
  
- \[зкн\], \[скн\] → \[зн\], \[сн\] \(випадає к\): брязкіт — брязнути, тріск — тріснути, писк — писнути \(рідше — пискнути\);
  
- \[стл\], \[стн\] → \[сл\], \[сн\] \(випадає т\): щастя — щасливий, прихвостень — прихвосня, перстень — персня;
  
- \[рнц\] → \[нц\] \(випадає р\): чернець — ченці;
  
- \[рдц\] → \[рц\] \(випадає д\): сердець — серце;
...

---
**Total textbook excerpts found:** 1
**Grades searched:** 1, 2, 3, 5
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
