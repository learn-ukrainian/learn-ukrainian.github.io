<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Skeleton Prompt — Module Structure Planning

You are planning the detailed paragraph-level structure of a Ukrainian language module. Do NOT write the full content — only plan the structure.

## Your task

Create a detailed paragraph-level skeleton for module **63: Речення і клас** (A2, A2.9 [Metalanguage Bridge & Foundation]).

**Word target: 2000 words** of prose. Your skeleton must budget every word.

---

## Plan

<plan_content>
module: a2-063
level: A2
sequence: 63
slug: metalanguage-sentences-and-classroom
version: '1.1'
title: Речення і клас
subtitle: Синтаксичні терміни, будова слова та мова класу
focus: bridge
pedagogy: Bridge
phase: A2.9 [Metalanguage Bridge & Foundation]
word_target: 2000
objectives:
  - Learner can name and identify sentence members in Ukrainian (підмет, 
    присудок, додаток, означення, обставина) in simple sentences.
  - Learner can identify word anatomy parts using Ukrainian terms (корінь, 
    префікс, суфікс, закінчення) and break words into morphemes.
  - Learner can understand and respond to classroom imperatives in Ukrainian 
    (Прочитайте, Запишіть, Виберіть, Підкресліть, Вставте, Дайте відповідь).
  - Learner can follow a Ukrainian-language grammar exercise format, preparing 
    for B1 immersion-style instruction.
dialogue_situations:
  - situation: "A student asking the teacher how to analyze a sentence — Як визначити
      підмет? Що таке обставина? Teacher explains using simple examples"
    functions: ["asking about grammar terms", "requesting clarification", "understanding
          instructions"]
    key_vocabulary: ["підмет", "присудок", "означення", "обставина"]
  - situation: "Two students working through a Ukrainian textbook exercise together
      — reading instructions in Ukrainian and helping each other with morpheme analysis"
    functions: ["following instructions in Ukrainian", "peer collaboration", "analyzing
          word structure"]
    key_vocabulary: ["корінь", "префікс", "суфікс", "прочитайте", "визначте"]
content_outline:
  - section: 'Члени речення: хто що робить? (Sentence Members: Who Does What?)'
    words: 550
    points:
      - 'Re-labeling with Grade 3-4 textbook method: Ukrainian children learn sentence
        analysis (розбір речення) by asking questions. Підмет (subject) — хто? що?
        — underlined with one line. Присудок (predicate) — що робить? що зробив? —
        underlined with two lines.'
      - 'Другорядні члени речення (secondary sentence members): Додаток (object) —
        кого? що? кому? чим? — answers case questions. Означення (attribute) — який?
        яка? яке? чий? — describes the noun. Обставина (adverbial modifier) — де?
        коли? як? куди? — describes the action.'
      - 'Practice: analyze 5-6 simple sentences, identifying підмет, присудок, and
        other members. Grade 4 textbook format: draw arrows and underline.'
      - 'Simple vs. compound sentence: просте речення (one підмет + присудок) vs.
        складне речення (two or more pairs).'
  - section: 'Будова слова: корінь, префікс, суфікс (Word Anatomy: Root, Prefix, Suffix)'
    words: 500
    points:
      - 'Корінь (root) — the core meaning: ліс → лісок, лісовий, лісник, пролісок.
        All share the root ліс-. Споріднені слова (cognate words) share a root.'
      - 'Префікс (prefix) — before the root, changes meaning: ходити → виходити, заходити,
        приходити, переходити. Each prefix adds a new direction or nuance.'
      - 'Суфікс (suffix) — after the root, changes part of speech or adds meaning:
        ліс → лісок (diminutive), лісовий (adjective), лісник (person). Connect to
        diminutive suffixes from M52.'
      - 'Закінчення (ending) — the grammatical ending that changes by case, gender,
        number: книга, книги, книзі, книгу, книгою. Основа (stem) = everything except
        the закінчення.'
      - 'Practice: break 8-10 words into morphemes using the корінь-префікс-суфікс-закінчення
        framework.'
  - section: 'Мова класу: накази вчителя (Classroom Language: Teacher Instructions)'
    words: 550
    points:
      - 'Essential classroom imperatives the learner will encounter in B1+ Ukrainian-language
        instruction: Прочитайте (Read), Запишіть (Write down), Виберіть (Choose),
        Підкресліть (Underline), Вставте (Insert), Дайте відповідь (Give an answer),
        Знайдіть (Find), Визначте (Determine), Порівняйте (Compare), Доповніть (Complete/supplement).'
      - 'These are formal imperative (ви-form). Connect to nakazovyy sposib from M56.
        Formation: stem + -іть/-йте.'
      - 'Common exercise instructions: Вставте пропущені букви (Insert missing letters).
        Підкресліть підмет і присудок (Underline subject and predicate). Визначте
        відмінок іменника (Determine the case of the noun).'
      - 'Practice: read 5-6 Ukrainian exercise instructions and do the exercise. This
        simulates real Ukrainian classroom work.'
  - section: 'Усе разом: аналізуємо текст (Putting It All Together: Text Analysis)'
    words: 400
    points:
      - 'Integrated exercise: a short Ukrainian text (6-8 sentences). The learner
        identifies parts of speech (частини мови), sentence members (члени речення),
        and breaks selected words into morphemes (будова слова).'
      - 'Reading: a Grade 4 textbook exercise page — the learner works through it
        as a Ukrainian student would, following instructions in Ukrainian.'
      - 'Self-assessment: Can I understand grammar instructions in Ukrainian? Am I
        ready for B1 where more content will be in Ukrainian?'
vocabulary_hints:
  required:
    - речення (sentence)
    - підмет (subject)
    - присудок (predicate)
    - додаток (object)
    - означення (attribute)
    - обставина (adverbial modifier)
    - корінь (root)
    - префікс (prefix)
    - суфікс (suffix)
    - закінчення (ending)
    - прочитайте (read — imperative)
    - запишіть (write down — imperative)
  recommended:
    - основа (stem)
    - споріднені слова (cognate words)
    - підкресліть (underline — imperative)
    - вставте (insert — imperative)
    - визначте (determine — imperative)
activity_hints:
  - type: match-up
    focus: Match sentence member terms to their question words
    items: 8
  - type: fill-in
    focus: Break words into morphemes (корінь, префікс, суфікс, закінчення)
    items: 8
  - type: quiz
    focus: Read a classroom instruction in Ukrainian and choose what to do
    items: 8
  - type: group-sort
    focus: Sort words into groups by shared корінь (root families)
    items: 8
references:
  - title: Вашуленко Grade 3, Будова слова
    notes: Root, prefix, suffix as taught to Ukrainian 3rd graders
  - title: Большакова Grade 4, Речення. Члени речення
    notes: Sentence analysis method with підмет and присудок identification

</plan_content>

---

## Wiki Teaching Brief

Skim this for the key concepts, paradigms, and examples you must cover. Reference specific examples from the article that you plan to use in each paragraph.

<knowledge_packet>
# Knowledge Packet: Речення і клас
**Module:** metalanguage-sentences-and-classroom | **Track:** A2

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: grammar/a2/metalanguage-sentences-and-classroom.md

# Граматика A2: Речення і клас



## Як це пояснюють у школі (How Schools Teach This)

The concept of a sentence (`речення`) is introduced as the fundamental unit of communication, built around a core idea. Ukrainian schools, starting from early grades (Grade 3), teach that for a group of words to be a sentence, they must be connected logically and grammatically (Source 4).

The core of a sentence is the **граматична основа** (grammatical foundation). This concept is introduced in Grade 5 textbooks and is consistently reinforced (Source 1, 4, 10). The grammatical foundation consists of the two **головні члени речення** (main members of the sentence):
1.  **Підмет** (Subject): The main member that denotes the person or object being discussed and answers the questions `хто?` (who?) or `що?` (what?). It is typically a noun or pronoun in the nominative case (Source 1, 4, 10).
2.  **Присудок** (Predicate): The main member that describes the action of the subject, what happens to it, or what it is. It answers questions like `що робить?` (what does it do?), `який він є?` (what is it like?), `хто він такий?` (who is it?). It is most often a verb, but can also be an adjective or a noun (Source 1, 9).

All other words in the sentence are **другорядні члени речення** (secondary members). They expand upon the main members. Textbooks for Grade 5 and 6 introduce them with specific questions (Source 10, 13, 30, 39):
*   **Додаток** (Object): Answers indirect case questions (`кого?`, `чому?`, `ким?`, etc.).
*   **Означення** (Attribute/Modifier): Answers `який?` (what kind?), `чий?` (whose?), `котрий?` (which?).
*   **Обставина** (Adverbial Modifier): Answers `де?` (where?), `коли?` (when?), `як?` (how?), `чому?` (why?), etc.

Sentences are then classified. A key distinction taught is between **прості речення** (simple sentences) with one grammatical foundation, and **складні речення** (complex/compound sentences) with two or more (Source 3). Simple sentences are further divided into **непоширені** (unextended), containing only main members, and **поширені** (extended), containing secondary members (Source 13, 40).

Another important concept, introduced generally in Grade 5 (Source 23, 29) and detailed in Grade 8, is the **односкладне речення** (one-member sentence). This is a sentence where the grammatical foundation consists of only one main member (either a subject or a predicate), but the meaning is still complete (Source 14). Examples like `Тихий вечір.` (A quiet evening.) or `У нас брехунів не люблять.` (They don't like liars here.) are used to illustrate this (Source 1).

The vocabulary related to learning and the classroom (`клас`) is integrated through exercises and examples, covering terms like `школа`, `клас` (grade/classroom), `вчитель` (teacher), `учні` (students), `підручник` (textbook), and `домашнє завдання` (homework) (Source 5).

## Повна парадигма (Full Paradigm)

The "paradigm" for this topic is the classification system for sentences and the roles of their components.

### Sentence Classification

This table shows the primary ways sentences are categorized in Ukrainian grammar, based on materials for grades 5-8 (Source 29, 13, 36).

| Категорія (Category) | Типи (Types) | Приклад (Example) | Джерело (Source) |
| :--- | :--- | :--- | :--- |
| **За метою висловлювання** (By Purpose) | **Розповідне** (Declarative) | `Сонце сходить.` (The sun rises.) | (Source 1) |
| | **Питальне** (Interrogative) | `Скільки води людина має випивати?` (How much water should a person drink?) | (Source 36) |
| | **Спонукальне** (Imperative) | `Бережи рідну землю!` (Protect your native land!) | (Source 14) |
| **За емоційним забарвленням** (By Emotion) | **Окличне** (Exclamatory) | `Смачного!` (Enjoy your meal!) | (Source 36) |
| | **Неокличне** (Non-exclamatory) | `Тиха вода завжди глибока.` (Still waters are always deep.) | (Source 1) |
| **За складом граматичної основи** (By Foundation) | **Двоскладне** (Two-member) | `Вітри сьогодні шаленіють.` (The winds are raging today.) | (Source 1) |
| | **Односкладне** (One-member) | `Тихий вечір.` (A quiet evening.) | (Source 1) |
| **За наявністю другорядних членів** (By Secondary Members) | **Поширене** (Extended) | `Я ходжу ранками у вишневий садок.` (I walk in the cherry garden in the mornings.) | (Source 1) |
| | **Непоширене** (Unextended) | `Ідуть дощі.` (Rains are falling.) | (Source 13) |

### Sentence Members (`Члени речення`)

This table outlines the roles, questions, and typical parts of speech for each sentence member (Source 29, 10, 39, 44).

| Роль (Role) | Член речення (Member) | Питання (Questions) | Чим виражений (Expressed by) |
| :--- | :--- | :--- | :--- |
| **Головні** (Main) | **Підмет** (Subject) | `хто?` `що?` | Noun, Pronoun (Nominative) |
| | **Присудок** (Predicate) | `що робить?` `що зробить?` `який є?` `хто є?` | Verb, Adjective, Noun |
| **Другорядні** (Secondary) | **Додаток** (Object) | `кого?` `чого?` `кому?` `чому?` `ким?` `чим?` etc. | Noun, Pronoun (Indirect Cases) |
| | **Означення** (Attribute) | `який?` `чия?` `котрий?` | Adjective, Pronoun, Noun |
| | **Обставина** (Adverbial Modifier) | `де?` `куди?` `коли?` `як?` `чому?` `з якою метою?` | Adverb, Noun (Indirect Cases), Adverbial Participle |

## Частотність і пріоритети (Frequency & Priorities)

For an A2-B1 learner, the primary goal is mastering the **просте, розповідне, двоскладне, поширене речення** (simple, declarative, two-member, extended sentence). This is the most common sentence type and the foundation for all communication. The neutral word order is Subject-Verb-Object, though it is flexible.

**Priority 1: The Core Sentence**
*   **Structure:** `[Означення] + Підмет + Присудок + [Додаток] + [Обставина]`
*   Learners must be able to identify the subject and predicate, and understand how secondary members add detail.
    *   Example: `Моя подруга читає цікаву книгу ввечері.` (My friend reads an interesting book in the evening.)

**Priority 2: Basic One-Member Sentences**
*   **Називні речення (Nominative sentences):** Extremely common for setting a scene or for concise descriptions.
    *   Example: `Тихий вечір.` (A quiet evening.) (Source 1). These are high-frequency in descriptive and literary contexts.
*   **Безособові речення (Impersonal sentences):** Essential for talking about weather, states of being, and feelings. The structure `[Adverb]` is very common.
    *   Example: `Сьогодні холодно.` (It is cold today). `Смеркалося.` (It was getting dark.) (Source 14).
*   **Означено-особові речення (Definite-personal sentences):** These are implicitly used constantly whenever dropping the pronoun in the 1st/2nd person, which is natural in Ukrainian.
    *   Example: `Люблю осінь.` (I love autumn.) `Ходімо в парк.` (Let's go to the park.) (Source 14).

**Priority 3: Classroom & Learning Vocabulary**
*   A learner in any formal setting must master the vocabulary of education. Words like `клас` (grade/classroom), `урок` (lesson), `вчитель` (teacher), `учень` (student), `підручник` (textbook), `питання` (question), and `домашнє завдання` (homework) are non-negotiable for A2 (Source 5, 15).

## Типові помилки L2 (Common L2 Errors)

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| *Я є студент.* | `Я — студент.` | The verb `бути` (to be) is almost always omitted in the present tense. For `Noun - Noun` sentences, a dash (`—`) is used in writing to represent the omitted verb (Source 9). |
| *Воно холодно надворі.* | `Надворі холодно.` | English uses a "dummy subject" (`it`) for impersonal statements. Ukrainian uses a simple adverbial predicate with no subject (a type of `безособове речення`) (Source 14). |
| *Я не розумію це слово.* | `Я не розумію цього слова.` | The "genitive of negation" is a common pattern where the direct object of a negated verb often shifts from the accusative to the genitive case. This is a key feature of Slavic grammar often missed by English speakers. <!-- VERIFY --> |
| *Іде дівчина по вулиці?* | `Дівчина іде по вулиці?` or `Чи дівчина іде по вулиці?` | Ukrainian does not use Subject-Verb inversion for yes/no questions. The question is indicated by rising intonation in speech, a question mark in writing, or by starting the sentence with the particle `чи`. |
| *Де живуть твої батьки? Живуть в Києві.* | `Де живуть твої батьки?` **`Вони живуть`** `в Києві.` or simply **`У Києві.`** | While Ukrainian is a pro-drop language, dropping the subject pronoun is most natural for 1st (`я/ми`) and 2nd (`ти/ви`) person. In the 3rd person (`він/вона/воно/вони`), dropping the pronoun without prior context can be ambiguous. Replying with just the verb `Живуть` sounds unnatural. |
| *Моя сестра пішов в магазин.* | `Моя сестра пішла в магазин.` | The past tense verb must agree in gender and number with the subject. `Сестра` is feminine singular, so the verb must take the feminine ending `-ла`. |

## Деколонізаційні застереження (Decolonization Notes)

This section is crucial for teaching Ukrainian as a distinct and complete language system, not as a variant of Russian.

1.  **Ukrainian is Not a Russian Dialect:** The modern Ukrainian standard language is based on the dialects of Central Ukraine (Полтавщина, Черкащина), as established by writers like Ivan Kotliarevsky and Taras Shevchenko. This is the **середньонаддніпрянський говір** (Middle Dnieper dialect) (Source 2). It has its own history and logic, distinct from the formation of standard Russian, which was based on Moscow dialects with heavy Church Slavonic influence.
2.  **Infinitive Endings:** The standard literary Ukrainian infinitive ends in **-ти** (e.g., `робити`, `читати`, `знати`). The ending **-ть** (e.g., `робить`, `читать`) is a prominent feature of the Southeastern dialect group (`південно-східне наріччя`), which had prolonged contact with the Russian Empire (Source 2). While a valid dialectal form within Ukraine, it should not be taught as the standard. Learners should use `-ти` and recognize `-ть` as dialectal or colloquial, avoiding the false assumption that it's a "shared" or "correct" form because of its similarity to Russian.
3.  **Vocabulary and "False Friends":** Russianisms (`росіянізми`) are words borrowed from Russian that may displace native Ukrainian words. For example, Source 2 points out `очки` as a Russianism for the standard Ukrainian `окуляри` (eyeglasses). A content writer must be vigilant, using dictionaries like the СУМ-11 and style guides to choose authentic Ukrainian vocabulary and avoid calques.
4.  **Grammar Rules Stand Alone:** Grammatical phenomena like the vocative case (Кличний відмінок), the flexibility of word order, and the nuances of verb aspect should be presented as integral parts of the Ukrainian system. They should never be framed as "how Ukrainian differs from Russian" or as exceptions to a presumed Russian norm. Ukrainian grammar is the default for this curriculum.

## Природні приклади (Natural Examples)

These examples are drawn from the provided sources to showcase natural sentence structures.

#### 1. Прості двоскладні речення (Simple Two-Member Sentences)
*   `Сонце сходить.` (The sun rises.) (Source 1)
*   `Річка дихала парою в небо.` (The river breathed steam into the sky.) (Source 1)
*   `Наш двір прикрашає лелече гніздо.` (A stork's nest decorates our yard.) (Source 30)

#### 2. Речення з однорідними членами (Sentences with Homogeneous Members)
*   `Восени листя жовтіє, сохне й опадає.` (In autumn, the leaves turn yellow, dry out, and fall.) (Source 1)
*   `Маки, ромашки й волошки тягнуться до сонця.` (Poppies, daisies, and cornflowers reach for the sun.) (Source 1)
*   `Батько з дочкою пішли до овочевої крамниці.` (The father and daughter went to the vegetable store.) (Source 36)

#### 3. Односкладні речення (One-Member Sentences)
*   `Тихий вечір.` (A quiet evening.) [Називне] (Source 1)
*   `Не розбивши крашанки, не спечеш яєчні.` (Without breaking the Easter egg, you won't make scrambled eggs.) [Узагальнено-особове] (Source 36)
*   `Задзвонили у Констанці рано в усі дзвони.` (They started ringing all the bells early in Constanța.) [Неозначено-особове] (Source 14)
*   `Треба дбати про чистоту природи.` (It is necessary to care for the purity of nature.) [Безособове] (Source 24)

#### 4. Питальні та спонукальні речення (Interrogative & Imperative Sentences)
*   `У яких класах буде викладати Христина?` (In which grades will Khrystyna teach?) (Source 5)
*   `Поміняйте мову на телефоні на ту мову, яку ви вивчаєте.` (Change the language on your phone to the language you are studying.) (Source 15)
*   `Не лізь у воду, не знаючи броду.` (Don't go into the water without knowing the ford.) (Source 11)

## Рекомендації для вправ (Activity Concepts)

**Phase 1: Identification & Core Concepts**
*   **Drill 1 (Find the Core):** Provide 10-15 simple extended sentences (`поширені речення`). Students must underline the subject (`підмет`) once and the predicate (`присудок`) twice, as is standard in Ukrainian schools (Source 10).
*   **Drill 2 (Classify by Purpose):** Provide a mix of declarative, interrogative, and imperative sentences. Students must label each one (`розповідне`, `питальне`, `спонукальне`) (Source 36).

**Phase 2: Sentence Building**
*   **Drill 3 (Sentence Expansion):** Give students an unextended core (`непоширене речення`) like `Дівчина читає.` (The girl is reading.). Prompt them to add secondary members by answering questions: `Яка дівчина?` (What kind of girl?), `Що читає?` (What is she reading?), `Де читає?` (Where is she reading?).
*   **Drill 4 (Sentence Scrambles):** Provide words in a jumbled order and have students arrange them into a logical sentence, practicing natural word order. Use proverbs or common sayings for this. (Example based on Source 4: `[Криниці, водиці, схочеш, бо, не брудни] -> Не брудни криниці, бо схочеш водиці.`).

**Phase 3: Transformation & Creation**
*   **Drill 5 (Question Formation):** Give a declarative sentence (`Христина буде працювати в школі.`). Students must transform it into a yes/no question using intonation (`?`) and the particle `чи`.
*   **Drill 6 (Combining Sentences):** Provide two related simple sentences and ask students to combine them into a single complex sentence using conjunctions like `тому`, `а`, `і`. (Example based on Source 3).
*   **Drill 7 (Creative Writing):** Using classroom vocabulary (Source 5), ask students to write 5-7 sentences describing their own language learning process, what their "classroom" looks like, or what they do in a lesson.

## Зв'язки з іншими темами

Understanding the sentence is the central goal of syntax. It builds directly upon morphology and enables more complex structures.

*   **Prerequisites:**
    *   **Частини мови (Parts of Speech):** A learner cannot identify sentence members without first knowing what a noun, verb, or adjective is. This is foundational (Source 44, 47).
    *   **Відмінки (Noun Cases):** Essential for differentiating the subject (Nominative) from direct and indirect objects (Accusative, Genitive, Dative, etc.) (Source 29).
    *   **Дієвідмінювання (Verb Conjugation):** The predicate must agree with the subject in person and number (present/future) and gender/number (past).

*   **What this topic enables:**
    *   **Складні речення (Complex/Compound Sentences):** Mastery of the simple sentence (`просте речення`) is required before a student can analyze or construct sentences with multiple grammatical foundations (Source 3, 23).
    *   **Відокремлені члени (Detached/Set-apart Members):** Understanding secondary members is a prerequisite for learning about participial and adverbial phrases (`дієприкметникові` and `дієприслівникові звороти`), which are essentially complex, detached attributes and adverbials (Source 43).
    *   **Пряма мова і діалог (Direct Speech and Dialogue):** Constructing reported speech and dialogue requires embedding complete sentences within a larger narrative structure (Source 23).

## Пов'язані статті (Related Articles)

*   `grammar/a1/introduction-to-cases`
*   `grammar/a1/verb-conjugation-present`
*   `grammar/a2/past-tense-and-gender`
*   `grammar/b1/compound-sentences`
*   `grammar/b1/adverbial-participles`

---

### Вікі: grammar/a2/metalanguage-verbs-and-time.md

# Граматика A2: Дія і час



## Як це пояснюють у школі (How Schools Teach This)

Українські шкільні підручники вводять поняття дії та часу через категорії **виду**, **способу** і **часу** дієслова. Типова послідовність для 6-7 класів виглядає так:

1.  **Форми дієслова:** Спочатку учні розрізняють інфінітив, особові форми, дієприкметник, дієприслівник та безособові форми на -но, -то (Джерела: `11-klas-ukrajinska-mova-avramenko-2019_s0061`, `11-klas-ukrajinska-mova-glazova-2019_s0050`).
2.  **Вид (Aspect):** Одразу після базових форм вводиться ключова для слов'янських мов категорія доконаного (`що зробити?`) та недоконаного (`що робити?`) виду. Це фундаментальне поняття, що визначає, чи дія завершена, чи триває (Джерела: `7-klas-ukrmova-litvinova-2024_s0037`, `10-klas-ukrmova-karaman-2018_s0322`).
3.  **Спосіб (Mood):** Далі пояснюється, що дієслова виражають дію по-різному залежно від її відношення до реальності. Виділяють три способи (Джерело: `6-klas-ukrmova-betsa-2023_s0214`, `7-klas-ukrmova-avramenko-2024_s0088`):
    *   **Дійсний (Indicative):** реальна дія, що відбувається, відбулася чи відбудеться.
    *   **Умовний (Conditional):** бажана або можлива за певних умов дія.
    *   **Наказовий (Imperative):** спонукання до дії (наказ, прохання, порада).
4.  **Час (Tense):** Категорія часу розглядається **лише в межах дійсного способу**. Умовний та наказовий способи часу не мають (Джерело: `7-klas-ukrmova-avramenko-2024_s0088`). Часи вивчають у такій послідовності: минулий, теперішній, майбутній (Джерела: `7-klas-ukrmova-litvinova-2024_s0007`, `7-klas-ukrmova-litvinova-2024_s0045`).

Основний акцент робиться на тому, що вибір правильної форми дієслова залежить від комбінації цих трьох категорій: чи дія завершена (вид), чи вона реальна (спосіб), і коли вона відбувається (час).

## Повна парадигма (Full Paradigm)

### **Дійсний спосіб (Indicative Mood)**

Це спосіб, що виражає реальну дію і має три часи (Джерело: `7-klas-ukrmova-zabolotnyi-2024_s0075`).

#### 1. Теперішній час (Present Tense)

*   **Значення:** Дія, що відбувається постійно чи в момент мовлення (Джерело: `7-klas-ukrmova-litvinova-2024_s0045`).
*   **Вид:** Тільки **недоконаний** (Джерело: `7-klas-ukrmova-litvinova-2024_s0045`).
*   **Змінюється за:** особами, числами.

| Особа | І дієвідміна (читати) | ІІ дієвідміна (говорити) |
| :--- | :--- | :--- |
| 1. я | чита**ю** | говор**ю** |
| 2. ти | чита**єш** | говор**иш** |
| 3. він/вона/воно | чита**є** | говор**ить** |
| 1. ми | чита**ємо** | говор**имо** |
| 2. ви | чита**єте** | говор**ите** |
| 3. вони | чита**ють** | говор**ять** |

#### 2. Минулий час (Past Tense)

*   **Значення:** Дія, що відбулася до моменту мовлення (Джерело: `7-klas-ukrmova-litvinova-2024_s0045`).
*   **Вид:** Доконаний і недоконаний.
*   **Змінюється за:** родами (в однині), числами.
*   **Творення:** Основа інфінітива + суфікси `-в` (чол. рід), `-ла` (жін. рід), `-ло` (сер. рід), `-ли` (множина).

| Рід/Число | Недоконаний (робити) | Доконаний (зробити) |
| :--- | :--- | :--- |
| Чоловічий (я, ти, він) | роби**в** | зроби**в** |
| Жіночий (я, ти, вона) | роби**ла** | зроби**ла** |
| Середній (воно) | роби**ло** | зроби**ло** |
| Множина (ми, ви, вони) | роби**ли** | зроби**ли** |

#### 3. Майбутній час (Future Tense)

*   **Значення:** Дія, що відбудеться після моменту мовлення (Джерело: `7-klas-ukrmova-avramenko-2024_s0078`).
*   Має три форми залежно від виду дієслова.

**Форми майбутнього часу** (Джерело: `7-klas-ukrmova-avramenko-2024_s0071`)

| Форма | Вид | Як утворюється | Приклад (писати/написати) |
| :--- | :--- | :--- | :--- |
| **Проста** | Доконаний | Форми теперішнього часу від дієслова доконаного виду. | я **напишу**, ти **напишеш** |
| **Складна** | Недоконаний | Інфінітив + суфікс `-м-` + особові закінчення. | я писа**тиму**, ти писа**тимеш** |
| **Складена** | Недоконаний | `бути` в майбутньому часі + інфінітив. | я **буду писати**, ти **будеш писати** |

### **Умовний спосіб (Conditional Mood)**

*   **Значення:** Дія бажана або можлива за певних умов (Джерело: `6-klas-ukrmova-betsa-2023_s0214`).
*   **Час:** Не має часових форм (Джерело: `7-klas-ukrmova-avramenko-2024_s0088`).
*   **Творення:** Форма минулого часу + частка `б` (після голосних) або `би` (після приголосних) (Джерело: `7-klas-ukrmova-zabolotnyi-2024_s0075`).
*   **Змінюється за:** родами (в однині), числами.

| Рід/Число | Форма |
| :--- | :--- |
| Чоловічий (я, ти, він) | прочита**в би** |
| Жіночий (я, ти, вона) | прочита**ла б** |
| Середній (воно) | прочита**ло б** |
| Множина (ми, ви, вони) | прочита**ли б** |

### **Наказовий спосіб (Imperative Mood)**

*   **Значення:** Наказ, прохання, порада, заклик до дії (Джерело: `6-klas-ukrmova-betsa-2023_s0216`).
*   **Час:** Не має часових форм.
*   **Змінюється за:** особами, числами.

| Особа | Однина | Множина |
| :--- | :--- | :--- |
| 1-ша | — | роб**імо**, читай**мо** |
| 2-га | роб**и**, читай | роб**іть**, читай**те** |
| 3-тя | **хай** роб**ить**, **нехай** чита**є** | **хай** робл**ять**, **нехай** чита**ють** |

(Джерела: `7-klas-ukrmova-litvinova-2024_s0064`, `7-klas-ukrmova-zabolotnyi-2024_s0076`)

## Частотність і пріоритети (A2 Level)

Для рівня А2 пріоритетним є впевнене володіння найбільш уживаними формами:

1.  **Теперішній час (недоконаний вид):** основа для опису себе, своєї рутини, теперішніх подій. (`Я живу в Києві`, `Ми вчимо українську`).
2.  **Минулий час (обидва види):** критично важливий для розповідей про минулі події. Різниця між `я читав` (процес) і `я прочитав` (результат) — одна з ключових концепцій А2 (Джерело: `ext-ulp_youtube-212`).
3.  **Майбутній час (проста і складена форми):** `Я зроблю` (доконаний) та `Я буду робити` (недоконаний) є найчастотнішими для вираження планів. Складна форма (`робитиму`) є стилістично вищою і може бути введена пасивно.
4.  **Наказовий спосіб (2-га особа):** `роби` / `робіть`, `скажи` / `скажіть` — основа для будь-якої соціальної взаємодії (прохання, інструкції).
5.  **Умовний спосіб (`якби..., то ...б`):** базові конструкції для вираження мрій та гіпотетичних ситуацій (`Якби я мав час, я б поїхав у Львів`).

## Типові помилки L2 (Common L2 Errors)

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| *Давайте підемо* в кіно. | *Ходімо* в кіно. | В українській мові для спонукання до спільної дії (1-ша особа множини) використовуються синтетичні форми на `-мо`, `-імо`. Конструкція з "давайте" є прямим запозиченням з російської (Джерела: `7-klas-ukrmova-litvinova-2024_s0081`, `6-klas-ukrmova-betsa-2023_s0216`). |
| Я *читав* цю книгу вчора. (якщо дія завершена) | Я *прочитав* цю книгу вчора. | "Читав" означає процес читання, але не його завершення. Для одноразової завершеної дії в минулому потрібен доконаний вид. (Джерело: `ext-ulp_youtube-212`). |
| *Вона пішов* додому. | *Вона пішла* додому. | В українській мові дієслова минулого часу в однині узгоджуються з підметом за родом (`-в` для чоловічого, `-ла` для жіночого), а не тільки за особою. |
| Я *зроблю* це зараз. (маючи на увазі "I am doing it") | Я *роблю* це зараз. | Дієслова доконаного виду не мають форми теперішнього часу. Форма, що виглядає як теперішній час (`зроблю`), насправді є простою формою майбутнього часу (Джерело: `26-ext-other-blogs-43`). |
| Я *би хотів* кави. | Я *хотів би* кави. | Хоча частка `б`/`би` може стояти в різних місцях речення, для носіїв мови найбільш природним є її розташування одразу після дієслова, яке вона модифікує. |

## Деколонізаційні застереження (Decolonization Notes)

1.  **Імператив без `давай(те)`:** Найважливіше правило. Конструкції типу `давай(те) + інфінітив` або `давай(те) + форма майбутнього часу` є грубим русизмом. Українська мова має власні синтетичні форми: `співаймо`, `ходімо`, `несімо`, `зробімо` (Джерела: `7-klas-ukrmova-litvinova-2024_s0064`, `6-klas-ukrmova-betsa-2023_s0216`). Це треба підкреслювати як ознаку грамотної, чистої мови.
2.  **Майбутній час на `-му` (`писатиму`):** Складна форма майбутнього часу є унікальною рисою української мови, що походить від злиття інфінітива з давніми формами дієслова `имати` (`я иму писати` -> `я писатиму`). Вона не має аналогів у сучасній російській мові і є маркером автентичного українського мовлення (Джерело: `ext-other_blogs-50`).
3.  **Історична глибина:** Українська дієслівна система, хоч і спростилася порівняно з давньоукраїнською (втративши аорист, імперфект), зберегла унікальні риси. Сучасний минулий час походить від форм перфекту (`писав єсмь` -> `писав`), а давноминулий (`був написав`) є залишком плюсквамперфекту (Джерело: `ext-other_blogs-50`). Це свідчить про самостійний шлях розвитку.
4.  **Фонетичні відмінності в закінченнях:** Навіть у схожих конструкціях є відмінності. Наприклад, у 3-й особі однини дієслова І дієвідміни в українській мові втратили кінцеве `-ть` (`він несе`, `знає`), тоді як у російській воно зберігається (`несёт`, `знает`).

## Природні приклади (Natural Examples)

**Теперішній час (процес, рутина)**
*   Я там завжди **купую** овочі, фрукти, крупи, горішки. (Джерело: `ext-ulp_youtube-212`)
*   Безмовні тумани **тремтять** над полями. (П. Тичина, `7-klas-ukrmova-avramenko-2024_s0090`)
*   Ми **боремось** за мир і **прагнемо** миру. (Максим Рильський, `6-klas-ukrmova-betsa-2023_s0220`)

**Минулий час (результат vs. процес)**
*   **Стояла** я і **слухала** весну. (Леся Українка, `6-klas-ukrmova-betsa-2023_s0220`)
*   Христина **купила** на ярмарку крупи та горішки (результат). (Джерело: `ext-ulp_youtube-212`)
*   Давненько я не **надсилала** паперові листи (процес, що не відбувався). (Джерело: `ext-ulp_youtube-212`)

**Майбутній час (плани)**
*   Отже, я **замовлю** нам таксі заздалегідь на шосту. (Джерело: `ext-ulp_youtube-184`)
*   Я **буду** думати про тебе. (Джерело: `ext-ulp_youtube-184`)
*   Щоранку **бігаю** в парку (теперішній час у значенні майбутнього для планів). (Джерело: `7-klas-ukrmova-avramenko-2024_s0071`)

**Наказовий спосіб (прохання, наказ)**
*   **Обійми** мене так лагідно і не **пускай**. (С. Вакарчук, `7-klas-ukrmova-avramenko-2024_s0090`)
*   **Подивись** наліво, **подивись** направо — це твоя земля! (ТНМК, `7-klas-ukrmova-litvinova-2024_s0064`)
*   **Єднаймося**, браття, в цю лиху годину! (В. Ейгензеер, `7-klas-ukrmova-zabolotnyi-2024_s0088`)

**Умовний спосіб (гіпотези, мрії, ввічливі прохання)**
*   **Якби** у мене **була** віза, я **б полетів** з тобою хоч завтра. (Джерело: `ext-ulp_youtube-184`)
*   **Їв би** кіт рибу, але у воду боїться лізти. (Нар. тв., `7-klas-ukrmova-avramenko-2024_s0090`)
*   Чи не **допомогла б** ти мені приготувати салат? (у значенні наказу `допоможи`) (Джерело: `7-klas-ukrmova-avramenko-2024_s0090`)

## Рекомендації для вправ (Activity Concepts)

*   **Phase 1: Ізольовані форми**
    *   **Drill 1 (Present Tense Conjugation):** Дати інфінітиви І та ІІ дієвідмін (`читати`, `любити`, `жити`, `бачити`) і попросити провідміняти їх в усіх особах теперішнього часу.
    *   **Drill 2 (Past Tense Formation):** Дати інфінітиви (`бути`, `сказати`, `дивитися`) і утворити всі 4 форми минулого часу (`був`, `була`, `було`, `були`).
*   **Phase 2: Вид і Час у контексті**
    *   **Drill 3 (Aspect Choice):** Надати речення з пропущеним дієсловом і двома варіантами (доконаний/недоконаний вид). Учень має вибрати правильний на основі контексту (одноразова дія vs. процес). *Приклад: "Вчора я довго ______ (читав/прочитав) книгу, але так і не ______ (читав/прочитав) її до кінця."* (Джерело: `ext-ulp_youtube-212`).
    *   **Drill 4 (Future Tense Choice):** Пояснити ситуацію і попросити утворити майбутній час. *Приклад: "План на завтра: (подзвонити) мамі." -> Я **подзвоню** мамі. "Що ти плануєш (робити) все літо?" -> Я **буду працювати**.*
*   **Phase 3: Способи та складні речення**
    *   **Drill 5 (Imperative Transformation):** Перетворити речення з дійсного способу в наказовий. *Приклад: "Ти робиш домашнє завдання." -> **Роби** домашнє завдання! "Ми йдемо в парк." -> **Ходімо** в парк!*
    *   **Drill 6 (Conditional Sentence Building):** Дати дві половини речення для з'єднання за допомогою `якби ... б`. *Приклад: "я маю гроші" + "я купую машину" -> **Якби** я **мав** гроші, я **б купив** машину.*

## Зв'язки з іншими темами

*   **Попередні теми:** `verb-conjugations` (розуміння І та ІІ дієвідмін є необхідним для утворення форм теперішнього часу), `introduction-to-verbs` (базове поняття дієслова).
*   **Наступні теми:** `complex-sentences` (умовний спосіб є основою для підрядних речень умови з `якби`), `reported-speech` (зміна часів та способів при перетворенні прямої мови в непряму).

## Пов'язані статті

*   `grammar/a2/verb-aspect`
*   `grammar/a1/verb-conjugations`
*   `grammar/b1/verbs-of-motion`
</wiki_context>

## Plan References

- 
- 

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
- <!-- INJECT_ACTIVITY: activity-id --> [type from activity_hints, focus, number of items]
- P3 (~XX words): [specific content]
...

## Section Title (~XXX words total)
- P1 (~XX words): [specific content]
- <!-- INJECT_ACTIVITY: activity-id --> [type, focus]
...

## Підсумок (~150 words)
- P1 (~150 words): [Follow the plan's points for this section EXACTLY. If the plan says "Self-check questions", output a bulleted Q&A list — NOT prose. If the plan says "recap", write a brief recap.]

Grand total: ~2000 words
</skeleton>
```

## Rules

1. **Every paragraph has ONE clear purpose.** If you can't describe it in one sentence, split it.
2. **Word budgets must sum to 2000+.** Aim for ~10% overshoot (2200 words) — writers tend to undershoot.
3. **Section budgets must match the plan's `content_outline` word allocations** (±10%).
4. **Place exercise injection markers in the correct section.** Each activity hint in the plan may have a `section:` field that tells you which section it belongs in. Place `<!-- INJECT_ACTIVITY: descriptive-id -->` AFTER the teaching content of that section, never before. Use a descriptive kebab-case id (e.g., `fill-in-genitive`, `quiz-aspect-choice`). If no `section:` is specified, place the marker after the most relevant teaching point. **CRITICAL: An exercise must ONLY test concepts already taught above it. Never test a concept from a later section. Every plan `activity_hints` entry MUST have a corresponding `<!-- INJECT_ACTIVITY: id -->` marker in the skeleton.**
5. **Name specific Ukrainian examples** you plan to use in each paragraph. This prevents vague skeletons that produce vague content.
6. **Dialogues count as paragraphs.** Budget 80-120 words per multi-turn dialogue.
7. **No meta-commentary.** Output only the `<skeleton>` block, nothing else.
