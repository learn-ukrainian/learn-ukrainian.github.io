

---

## Your Writing Identity

**You are: Lead Ukrainian Instructor.** Your persona is *The Conversation Partner*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **32: Багато людей, багато речей** (A2, A2.5 [Case Synthesis and Plurals]).

**Target: 2000–3000 words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block. Evaluate each section from the plan and commit to a word budget. This prevents frontloading early sections and rushing later ones.

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Summary: ~150 words
Total: 2000+ words
</pacing_plan>
```

Then begin writing the module content. Follow your own pacing plan — each section must hit its word budget (±10%).

---

## 9 Hard Rules

1. **IMMERSION TARGET: 55-75% Ukrainian — Ukrainian dominates. English for abstract grammar only.** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if immersion is outside this range. For A1 early modules, the learner cannot read Cyrillic — English must dominate. For A2+, Ukrainian must carry a significant share — add Ukrainian Reading Practice blocks, dialogues, and example paragraphs to reach the target. Too little Ukrainian fails audit just as much as too much.
2. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
3. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
4. **You are a warm, encouraging teacher.** Natural teacher phrasing ("Let us look at...", "Have you noticed...") is fine. What to AVOID: self-congratulatory openers ("Welcome to A2! Congratulations!"), gamified language ("You have unlocked...", "You now possess..."), and empty filler sentences that add words but zero information. Every sentence should teach something specific to Ukrainian.
5. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
6. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers where exercises should appear. A separate pipeline step generates the actual exercises from the plan's activity_hints.
7. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
8. **Hit the word target** — you MUST write 2000–3000 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
9. **NO archaic, obsolete, or rare words** — use only modern standard Ukrainian. Do not use words marked as archaic (застаріле) or dialectal in dictionaries. Example: use «кін» not «кон», use «пом'якшені» not «м'якшені». When in doubt, choose the common modern form. Your pre-training contains Russian-influenced archaic forms — verify unfamiliar words.
10. **EVERY module MUST end with `## Підсумок`** — this is the last H2 section before the file ends. It contains a self-check recap. If you forget this section, the audit REJECTS the module and you waste a retry. Write it LAST, after all other sections.

**Note:** Do NOT add stress marks (´) to any Ukrainian word — a deterministic tool handles this after you write.

## Exercise Placement — Markers Only

**Do NOT write exercises directly.** A separate pipeline step (ACTIVITIES) generates all exercises from the plan's `activity_hints`. Your job is to place markers showing WHERE exercises belong.

### How It Works

1. Read the plan's `activity_hints` — each entry has an `id`, `type`, and `focus`
2. After the relevant teaching section, place an injection marker
3. The ACTIVITIES step reads your prose + the plan hints and generates complete exercises

### Marker Format

Place markers after key teaching sections. Each marker corresponds to ONE `activity_hints` entry from the plan:

```
<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->
```

Rules:
- Use the EXACT `id` from the plan's `activity_hints` — do not invent new IDs
- Place the marker right after the prose that teaches the concept the exercise tests
- Spread markers evenly throughout the module — never cluster them
- If the plan has 4 activity hints, you should place 4 markers in your prose

### Example

If the plan says:
```yaml
activity_hints:
  - id: quiz-sounds-vs-letters
    type: quiz
    focus: "Distinguish звук from літера"
  - id: match-false-friends
    type: match-up
    focus: "Match false friend Cyrillic letters to real sounds"
```

Your prose should contain (after the relevant sections):
```
[...prose about sounds and letters...]

<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->

[...prose about false friend letters...]

<!-- INJECT_ACTIVITY: match-false-friends -->
```

### What NOT to Do

- Do NOT write `:::quiz`, `:::fill-in`, `:::match-up`, or any DSL exercise blocks
- Do NOT write exercise questions, answers, or options — the ACTIVITIES step handles all of this
- Do NOT invent marker IDs — use only IDs from the plan's `activity_hints`

---

## Plan

<plan_content>
module: a2-032
level: A2
sequence: 32
slug: plural-nominative-accusative
version: '1.0'
title: Багато людей, багато речей
subtitle: Множина називного та знахідного відмінків для всіх відмін
focus: grammar
pedagogy: PPP
phase: A2.5 [Case Synthesis and Plurals]
word_target: 2000
objectives:
  - Learner can form the Nominative plural for nouns of all four declension 
    classes (I-IV відміна).
  - Learner can form the Accusative plural, applying the animate/inanimate 
    distinction correctly (animate = Genitive plural form, inanimate = 
    Nominative plural form).
  - Learner can identify when a plural noun is in Nominative vs. Accusative by 
    its syntactic role (subject vs. direct object).
  - Learner can produce correct plural Nom/Acc forms in short sentences 
    describing groups of people and collections of objects.
dialogue_situations:
  - setting: 'At a zoo — identifying animals and their groups: Дивись — леви (m, lions)!
      Бачиш тих жирафів (m, giraffes)? А ось мавпи (f, monkeys)! Діти люблять пінгвінів
      (m, penguins).'
    speakers:
      - Батько/Мати
      - Діти
    motivation: 'Nom plural: лев→леви. Acc animate plural: жираф→жирафів, пінгвін→пінгвінів'
content_outline:
  - section: 'Множина називного відмінка (Nominative Plural)'
    words: 650
    points:
      - 'I відміна (feminine/masculine -а/-я): сестра → сестри, земля → землі, суддя
        → судді. Hard stems: -и; soft stems: -і.'
      - 'II відміна (masculine consonant, neuter -о/-е/-я): стіл → столи, місто →
        міста, поле → поля, море → моря. Consonant alternations: друг → друзі, рік
        → роки.'
      - 'III відміна (feminine consonant): ніч → ночі, сіль → солі, мати → матері.'
      - 'IV відміна (neuter -а/-ят-): курча → курчата, теля → телята.'
      - 'Common irregulars: людина → люди, дитина → діти, око → очі, вухо → вуха.'
  - section: 'Знахідний відмінок множини: Живе чи неживе? (Accusative Plural: Animate
      vs. Inanimate)'
    words: 650
    points:
      - 'The key rule: inanimate Acc.Pl. = Nom.Pl. (Я бачу столи, книги, міста). Animate
        Acc.Pl. = Gen.Pl. (Я бачу братів, сестер, дітей).'
      - 'How this differs from singular: masculine singular already has this split
        (бачу стіл vs. бачу брата), but in plural ALL genders follow it.'
      - 'Practice with mixed animate/inanimate: Я бачу студентів і підручники. Ми
        зустріли друзів і знайшли ключі.'
      - 'Verbs that take Accusative: бачити, знати, любити, зустрічати, шукати — practice
        forming correct plural objects.'
  - section: 'Називний чи знахідний? Визначаємо за контекстом (Nominative or Accusative?
      Reading the Context)'
    words: 700
    points:
      - 'Subject test: Who/what does the action? = Nominative. Студенти читають (Nom).
        Я бачу студентів (Acc).'
      - 'Inanimate nouns look identical in Nom/Acc plural — only syntax tells them
        apart: Книги лежать на столі (Nom) vs. Я купив книги (Acc).'
      - 'Practice: short paragraphs where learner identifies Nom vs. Acc plural by
        role in sentence. Dialogues about shopping, meeting friends, describing groups.'
      - 'Integration: combine with prepositions that take Accusative (через, на (direction),
        у/в (direction), про) to reinforce recognition.'
vocabulary_hints:
  required:
    - множина (plural)
    - називний відмінок (nominative case)
    - знахідний відмінок (accusative case)
    - живий (animate)
    - неживий (inanimate)
    - закінчення (ending (grammar))
    - люди (people)
    - діти (children)
    - речі (things)
    - очі (eyes)
  recommended:
    - відміна (declension class)
    - чергування (alternation)
    - предмет (object, item)
    - група (group)
activity_hints:
  - type: fill-in
    focus: Form the Nominative plural from given singular nouns across all 
      declension classes
    items: 8
  - type: group-sort
    focus: Sort plural nouns into animate vs. inanimate, then predict their 
      Accusative form
    items: 8
  - type: quiz
    focus: Choose the correct Accusative plural form (animate = Gen.Pl., 
      inanimate = Nom.Pl.) in sentences
    items: 8
  - type: error-correction
    focus: Find and fix wrong plural noun endings in Nominative and Accusative 
      (e.g., *дітей грають → діти грають, *бачу студенти → студентів)
    items: 6
references:
  - title: Заболотний Grade 6, §§59-61
    notes: Nominative and Accusative plural formation, animate/inanimate 
      distinction
  - title: Літвінова Grade 6, с. 157-162
    notes: Plural declension tables for all відміни with exercises

</plan_content>

---

## Pre-Verified Facts (from MCP tools — use these, do NOT guess)

A verification step already called VESUM, textbooks, Правопис, and style guide tools. The results below are GROUND TRUTH. Use them:
- If a word is marked ❌ NOT IN VESUM — do NOT use it
- If a textbook excerpt is provided — use that pedagogy
- If a calque is flagged — use the correct alternative
- If CEFR says a word is above target — find a simpler synonym

You do NOT need to call tools yourself — the facts are already verified.

<pre_verified_facts>
## VESUM Verification
- Confirmed: множина, живий, неживий, закінчення, люди (людина), діти (дитина), речі (річ), очі (око), відміна, чергування, предмет, група, називний, знахідний, відмінок.
- Not found: [None] (All key terms and their components are verified).

## Grammar Rules
- **Множина іменників**: Правопис § 65–85 (Noun Declensions). Grade 3 textbooks (Vashulenko) define plural as "two or more objects." Grade 6 (Avramenko) specifies that most nouns have both numbers, but some are *pluralia tantum* (діти, гроші, меблі, ножиці).
- **Знахідний відмінок множини**: Grade 6 (Avramenko, p. 98) confirms the Animate/Inanimate rule:
  - Animate: Acc. Pl. = Gen. Pl. (бачу котів, зятів).
  - Inanimate: Acc. Pl. = Nom. Pl. (бачу кущі, тіла, моря).
- **Чергування**: Правопис § 6 (Alternation of e/i, o/i) and § 53 (Consonant alternations in noun stems: г-з, к-ц, х-с) - notably друг → друзі in Nom. Pl.

## Calque Warnings
- **багато людей**: OK (Common usage). Avoid "багаточисленний" (calque of многочисленный); use "численний" or "багато".
- **речі**: OK. Ensure distinction between "речі" (things/items) and "справи" (matters/affairs).

## CEFR Check
- **люди, діти, речі**: A1/A2 — OK (Fundamental vocabulary).
- **група, предмет**: A2 — OK (Common academic/descriptive terms found in Grade 3-6 materials).
- **називний, знахідний**: A2.5 — OK (Grammetical metalanguage introduced at this stage).
</pre_verified_facts>


## Wiki Teaching Brief — Your Authoritative Source

**This is your primary teaching material.** The wiki article below was compiled from real Ukrainian school textbooks, literary sources, and verified references. It contains the correct terminology, paradigm tables, teaching sequences, and examples for this module. Your job is to TRANSFORM this into engaging, level-appropriate content — not to copy it verbatim.

**How to use the wiki article:**
1. **Adopt the Ukrainian terminology.** If the article says «складоподіл», you write «складоподіл» — never CVCCV or "syllable division rules" paraphrased from English phonology. If it says «відкритий склад», you write «відкритий склад» — never "open syllable type."
2. **Follow the teaching sequence.** If the article shows: sound model → syllable → word → sentence, follow that progression. Do not rearrange or substitute your own.
3. **Use the article's examples as your foundation.** Authentic examples from textbooks beat invented ones. Use the article's examples and expand with your own that follow the same patterns.
4. **Synthesize and teach, don't summarize.** You are a teacher, not a summarizer. Take the facts from the article and weave them into engaging explanations with dialogues, situations, and practice. The article tells you WHAT to teach — you decide HOW to teach it for the target level.
5. **Your pre-training is contaminated by Russian and English linguistics.** When the article contradicts your instinct, the article wins. Ukrainian has its own phonetic categories (голосний/приголосний, дзвінкий/глухий, м'який/твердий) that do not map 1:1 to English or Russian. Use the Ukrainian categories.
6. **Do NOT copy paragraphs verbatim.** The article is reference material. Your output must be original teaching prose at the correct CEFR level, not a rephrased version of the article.

<knowledge_packet>
# Knowledge Packet: Багато людей, багато речей
**Module:** plural-nominative-accusative | **Track:** A2

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: grammar/a2/plural-nominative-accusative.md

# Граматика A2: Багато людей, багато речей



## Як це пояснюють у школі (How Schools Teach This)

Українські шкільні підручники вводять поняття множини іменників поступово. Вже в 4-му класі учні знайомляться з тим, що іменники змінюються за числами (однина і множина) та відмінками (Кравцова, Source 43; Захарійчук, Source 38). У цей час основна увага приділяється розрізненню називного та знахідного відмінків, що є фундаментом для майбутньої теми. Наприклад, підручник для 4-го класу чітко розмежовує роль підмета (називний відмінок) та другорядного члена речення (знахідний відмінок) (Варзацька, Source 22).

У 6-му класі тема поглиблюється. Учні вивчають чотири відміни іменників та поділ на тверду, м'яку та мішану групи (Заболотний, Source 44). Парадигми відмінювання подаються у таблицях, де візуально показані закінчення для кожної групи. Наприклад, підручник Авраменка (Source 7) ілюструє відмінювання І відміни з чітким розрізненням закінчень для твердої (`-и`), м'якої (`-і`) та мішаної (`-і`) груп у називному відмінку множини.

Ключовий аспект, що відрізняє українську граматику — розрізнення знахідного відмінка множини для назв істот та неістот — вводиться на прикладах. Підручники пояснюють, що для неістот форма знахідного відмінка збігається з називним, а для істот — з родовим відмінком (Заболотний, Source 20; Авраменко, Source 47). Це правило відпрацьовується через вправи на трансформацію та вибір правильної форми.

## Повна парадигма (Full Paradigm)

Форми називного (Н. в.) та знахідного (Зн. в.) відмінків множини залежать від відміни, групи та категорії істоти/неістоти.

**Ключове правило знахідного відмінка множини:**
*   Для **неістот**: Зн. в. = Н. в. (Я бачу `столи`).
*   Для **істот**: Зн. в. = Р. в. (Я бачу `котів`). (Source 20, 34)

### І відміна (жін., чол., спільний рід на `-а`/`-я`)

| Група | Основа на | Н. в. мн. | Зн. в. мн. (неістоти) | Зн. в. мн. (істоти) | Приклади |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Тверда | твердий приголосний | `-и` | `-и` | Р. в. мн. (`-ø`, `-ів`) | (Н.в.) `книги`, `фабрики` / (Зн.в.) бачу `книги`, бачу `сиріт` (Source 3) |
| М’яка | м’який приголосний | `-і`, `-ї` | `-і`, `-ї` | Р. в. мн. (`-ь`, `-ей`) | (Н.в.) `землі`, `мрії` / (Зн.в.) бачу `землі`, бачу `робітниць`, `мишей` (Source 3) |
| Мішана | шиплячий | `-і` | `-і` | Р. в. мн. (`-ø`) | (Н.в.) `груші`, `вежі` / (Зн.в.) бачу `груші`, бачу `слухачок` (Source 7) |

### ІІ відміна (чол. рід з нульовим закінченням або на `-о`; сер. рід на `-о`, `-е`, `-я`)

Це найскладніша відміна для цієї теми, оскільки тут найчастіше проявляється різниця між істотами та неістотами.

| Рід | Група | Н. в. мн. | Зн. в. мн. (неістоти) | Зн. в. мн. (істоти) | Приклади |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Чоловічий | Тверда | `-и` | `-и` | Р. в. мн. (`-ів`) | (Н.в.) `столи`, `заводи` / (Зн.в.) бачу `столи`, бачу `солдатів` |
| Чоловічий | М'яка | `-і`, `-ї` | `-і`, `-ї` | Р. в. мн. (`-ів`, `-їв`) | (Н.в.) `коні`, `герої` / (Зн.в.) бачу `музеї`, бачу `коней`, `героїв` |
| Чоловічий | Мішана | `-і` | `-і` | Р. в. мн. (`-ів`) | (Н.в.) `плащі`, `ключі` / (Зн.в.) бачу `плащі`, бачу `читачів` |
| Середній | Усі групи | `-а`, `-я` | `-а`, `-я` | *Зазвичай неістоти* | (Н.в./Зн.в.) `міста`, `села`, `поля`, `моря`, `обличчя` |

*Примітка:* Іменники середнього роду, що позначають істот (напр. *чудовисько*), є рідкісними.

### ІІІ відміна (жін. рід з нульовим закінченням + *мати*)

| Н. в. мн. | Зн. в. мн. (неістоти) | Зн. в. мн. (істоти) | Приклади |
| :--- | :--- | :--- | :--- |
| `-і` | `-і` | Р. в. мн. (`-ей`) | (Н.в.) `ночі`, `речі` / (Зн.в.) бачу `речі`, бачу **матерів** |

### IV відміна (сер. рід на `-а`/`-я` з суфіксами `-ат-`/`-ят-`, `-ен-`)

Ця відміна переважно позначає молодих істот.

| Н. в. мн. | Зн. в. мн. (істоти) | Приклади |
| :--- | :--- | :--- |
| `-ата`, `-ята` | Р. в. мн. (`-ат`, `-ят`) | (Н.в.) `лошата`, `кошенята` / (Зн.в.) бачу `лошат`, `кошенят` (Source 35) |
| `-ена` | Р. в. мн. (`-ен`) | (Н.в.) `імена`, `племена` / (Зн.в.) бачу `імена` (*неістота*) (Source 35) |

### Особливі форми (залишки двоїни)

Деякі іменники, що позначають парні предмети, зберегли стародавні форми двоїни, які функціонують як сучасна множина. Вони не підпадають під загальні правила і потребують запам'ятовування. (Source 10, 31).

| Н. в. | Р. в. | Зн. в. |
| :--- | :--- | :--- |
| `очі` | `очей` | `очі` |
| `плечі` | `плечей` | `плечі` |
| `двері` | `дверей` | `двері` |
| `гроші` | `грошей` | `гроші` |

## Частотність і пріоритети

Для рівня А2-В1 пріоритетним є засвоєння таких навичок:
1.  **Утворення називного відмінка множини для І та ІІ відмін.** Це найпоширеніші іменники в повсякденному мовленні. Закінчення `-и` (тверда група) та `-і` (м'яка/мішана) є базовими.
2.  **Розуміння і правильне використання правила "істота/неістота" для знахідного відмінка множини.** Це одна з найпомітніших граматичних рис, і помилки тут одразу вказують на іноземний акцент. Спочатку слід зосередитися на ІІ відміні чоловічого роду (`бачу столи` vs `бачу студентів`).
3.  **Запам'ятовування високочастотних нерегулярних форм** як лексичних одиниць: `люди`, `діти`, `очі`, `гроші`. Їхня неправильна формація (напр. `*людини`) є грубою помилкою.
4.  Менш пріоритетними на цьому етапі є складні випадки чергування голосних у родовому відмінку множини (що впливає на знахідний для істот), хоча базові чергування, як `кінь` - `коней`, є важливими.

## Типові помилки L2

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| Я бачу **студенти**. | Я бачу **студентів**. | Неправильне застосування знахідного відмінка для істот. Англомовні учні часто поширюють правило `Зн. в. = Н. в.` на всі іменники, оскільки в англійській мові форма об'єкта і суб'єкта у множині однакова ("I see students"). |
| У нас є два **комп'ютори**. | У нас є два **комп'ютери**. | Неправильне закінчення множини для твердої групи. Помилка може виникати через аналогію до м'якої групи або вплив інших мов. Правило: після твердого приголосного — `-и` (Source 44). |
| Він читає **книжки** та **журнали**. Мені подобаються ці **книги**. | Він читає **книжки** та **журнали**. Мені подобаються ці **книжки**. | Непослідовне використання форм. Хоча `книги` є допустимим варіантом, `книжки` є більш поширеним і стилістично нейтральним у розмовній мові. Учням слід рекомендувати дотримуватися однієї форми для послідовності. |
| Багато **люди** прийшли на концерт. | Багато **людей** прийшли на концерт. | `Люди` — це називний відмінок множини від `людина`. Після слів `багато`, `кілька`, `декілька` вимагається родовий відмінок множини (`людей`). Це помилка змішування відмінків. |
| Я зустрів моїх **друзі** біля кінотеатру. | Я зустрів моїх **друзів** біля кінотеатру. | Знову помилка утворення знахідного відмінка для істот. `Друзі` — називний відмінок, але в ролі прямого додатка (кого я зустрів?) має бути форма родового відмінка — `друзів`. |
| У нього сині **оча**. | У нього сині **очі**. | Неправильне утворення множини для слова-релікту двоїни. Учні намагаються застосувати стандартне правило для середнього роду (`село` - `села`), але `очі` є застиглою формою, яку треба запам'ятати (Source 10). |

## Деколонізаційні застереження

Презентація української граматики має бути самодостатньою, без порівнянь з російською як з "нормою". Українська мова зберегла багато архаїчних рис, втрачених в інших східнослов'янських мовах, що робить її унікальною.

1.  **Збереження двоїни (двоїна):** Форми як `очі`, `плечі`, `двері` та закінчення `-има` в орудному відмінку (`очима`, `плечима`) є прямими нащадками давньої граматичної категорії двоїни, яка майже повністю зникла в російській, але залишила помітні сліди в українській. Це не "винятки", а свідчення глибшої історії мови (Source 31, 37).
2.  **Чітке розрізнення числівників:** Сполучення числівників `два`, `три`, `чотири` з іменниками в українській мові має свою логіку. `Два брати` (Н.в. мн., наголос двоїни), `три брати`, `чотири брати` — іменник стоїть у формі називного відмінка множини. Це відрізняється від російської конструкції, де після `два`, `три`, `четыре` вживається родовий відмінок однини.
3.  **Кличний відмінок:** Хоча це не тема множини, варто нагадувати, що кличний відмінок (`брате!`, `земле!`) є живою і обов'язковою категорією в українській мові, на відміну від російської, де він є архаїзмом. Це одна з найяскравіших рис, що підкреслює самобутність української морфології (Source 6, 30).
4.  **Форми родового відмінка множини:** Українська мова має різноманітні закінчення в родовому відмінку множини (`-ів`, `-їв`, нульове закінчення з можливими вставними голосними `о`, `е`), які потім використовуються для утворення знахідного відмінка для істот. Ці патерни (напр. `вікон`, `пісень`, `читачів`) є внутрішньою системою і не повинні пояснюватися через аналогії з російською.

## Природні приклади

**Група 1: Називний відмінок множини (неістоти)**
*   Іменники І та ІІ відмін: `На небі повільно пливуть осінні сірі важкі хмари.` (Source 36)
*   Іменники ІІ відміни: `Непорушно стоять високі, пожовклі соняшники.` (Source 12)
*   Різні відміни: `Милуйтеся свічками-берізками і прозорим воском кленів і шапками лісових груш.` (Source 16)

**Група 2: Знахідний відмінок множини (неістоти, форма = Н.в.)**
*   Іменники І відміни: `Беру книжки, статті, груші.` (Source 3)
*   Числівник + іменник: `Треба пришити два ґудзики — і все готово!` (Source 21)
*   Повсякденна дія: `Скинь фотки, скинь відос.` (Source 2)

**Група 3: Знахідний відмінок множини (істоти, форма = Р.в.)**
*   Іменники І відміни: `Пасу свиней і свині, овець і вівці, корів і корови.` (тут показані паралельні форми) (Source 3)
*   Іменники ІІ відміни: `За (два) зайцями поженешся – жодного не піймаєш.` (Source 20)
*   Іменники ІІ відміни: `Зустрів двох друзів.` (Source 20)

**Група 4: Іменники-винятки та особливі форми**
*   Суплетивна форма `люди`: `Молоді люди їх часто використовують у неформальних ситуаціях.` (Source 2)
*   Суплетивна форма `діти`: `На лавочці сиділи діти.` (Source 13)
*   Залишок двоїни `очі`: `І стіни вуха мають.` (Приказка, але ілюструє множину для парних органів) (Source 15)

## Рекомендації для вправ

*   **Phase 1: Ідентифікація та утворення Н.в. множини.**
    *   **Вправа "Сортувальник":** Дати список іменників в однині. Учні мають визначити відміну, групу і написати форму називного відмінка множини. (Напр.: `книга` -> І відм., тверда гр. -> `книги`; `учитель` -> ІІ відм., м'яка гр. -> `учителі`).
    *   **Вправа "Трансформація речення":** Переписати речення, замінюючи однину на множину. (Напр.: `На столі лежить олівець.` -> `На столах лежать олівці.`).

*   **Phase 2: Введення Зн.в. множини (неістоти).**
    *   **Вправа "Що ти бачиш?":** Показати картинку з багатьма предметами. Учні мають скласти речення за моделлю `Я бачу...`. (Напр.: `Я бачу комп'ютери, столи і стільці.`). Це закріплює правило `Зн.в. = Н.в.` для неістот.

*   **Phase 3: Контрастне введення Зн.в. для істот.**
    *   **Вправа "Вибери правильну форму":** Дати речення з пропущеним додатком і двома варіантами. (Напр.: `Ми запросили (гості / гостей) на свято.`).
    *   **Вправа "Кого чи що?":** Дати список іменників. Учні мають відповісти на питання `Я бачу...` для кожного. (Напр.: `(сестра)` -> `Я бачу сестер.`; `(телефон)` -> `Я бачу телефони.`).
    *   **Вправа "Переклад-адаптація":** Дати прості англійські речення і попросити перекласти, звертаючи особливу увагу на прямий додаток у множині. (Напр.: "She knows these students." -> `Вона знає цих студентів.`).

## Зв'язки з іншими темами

*   **Передумови:**
    *   **Рід іменників (чоловічий, жіночий, середній):** Невід'ємна частина визначення відміни.
    *   **Відміни (І, ІІ, ІІІ, IV) та групи (тверда, м'яка, мішана):** Основа для правильного вибору закінчень (Source 44).
    *   **Поняття істоти/неістоти:** Критично важливе для розрізнення форм знахідного відмінка.
*   **Подальші теми:**
    *   **Родовий відмінок множини:** Ця тема безпосередньо пов'язана, оскільки форма Р.в. множини використовується для утворення Зн.в. для істот.
    *   **Інші непрямі відмінки множини (Давальний, Орудний, Місцевий):** Після засвоєння Н.в. та Зн.в. логічно переходити до інших відмінків множини (`даю студентам`, `пишаюся студентами`, `розповідаю про студентів`).
    *   **Узгодження прикметників у множині:** Уміння утворювати множину іменників є необхідним для правильного узгодження з прикметниками (`нові столи`, `цікавих студентів`).

## Пов'язані статті
*   `grammar/a1/noun-gender-and-declension`
*   `grammar/a2/genitive-case-plural`
*   `grammar/a2/adjective-agreement-plural`
*   `grammar/b1/numerals-and-noun-agreement`

---

### Вікі: grammar/a2/plural-other-cases.md

# Граматика A2: З друзями, для дітей



## Як це пояснюють у школі (How Schools Teach This)

Ukrainian schools introduce noun declension (змінювання за відмінками) early, typically by Grade 3 or 4. The approach is foundational and builds iteratively.

1.  **Core Concept (Grades 3-4)**: The initial introduction focuses on the concept that nouns change their endings to connect with other words in a sentence (Source 13, 32). This is taught through questions. Each of the seven cases is paired with specific questions (`хто? що?`, `кого? чого?`, etc.). Mnemonics are sometimes used to help students remember the order of the cases, such as "Нашого Ромчика Дивує Зебра — Оця Маленька Красуня" (Source 8).

2.  **Systematization (Grades 4-6)**: Instruction moves from simple question-answer pairs to systematic tables. Students learn to identify the case of a noun in a sentence by asking the correct question and observing its ending and any associated prepositions (Source 12, 19, 22). The distinction between direct (Називний) and indirect (усі інші) cases is established (Source 13, 35). Plural endings for Instrumental (`-ами`/`-ями`) and Locative (`-ах`/`-ях`) are explicitly taught (Source 20, 28).

3.  **Distinguishing Similar Cases (Grade 4 onwards)**: Textbooks provide specific strategies for distinguishing cases that have similar forms or questions.
    *   **Dative vs. Locative**: Though endings can be identical in the singular (e.g., `(на) білочці`), they are differentiated by meaning and prepositions. The Dative case often indicates the recipient of an action and is usually used without a preposition, while the Locative case indicates location and *always* requires a preposition (`у`, `на`, `по`) (Source 9, 37).
    *   **Nominative vs. Accusative**: For inanimate nouns, these cases can look identical. The key differentiator is the noun's function in the sentence: a noun in the Nominative case is the subject, whereas in the Accusative case it is a direct object (Source 30, 42).

4.  **Complexities (Grades 6-8)**: Older grades delve into the finer points, such as the declension patterns of different noun groups (тверда, м'яка, мішана) (Source 39, 40), the complexities of the Genitive plural endings (Source 39), and the declension of nouns that only exist in the plural (*pluralia tantum*) like `Карпати`, `окуляри`, `гроші` (Source 23, 24). The concept of syntactic government (керування), where a verb or preposition dictates the case of a noun, is also formally introduced (Source 15, 25).

The overall pedagogy is structured and consistent: introduce the concept with questions, provide clear tables, practice with sentence analysis and transformation exercises, and then address exceptions and similar-looking forms with targeted rules.

## Повна парадигма (Full Paradigm)

Ukrainian nouns change their endings in the plural according to their case. The patterns depend on the noun's gender and declension group. Here are the most common paradigms for A2/B1 learners.

### І & ІІ Відміна (1st & 2nd Declensions): Most Common Nouns

These tables cover the vast majority of masculine, feminine, and neuter nouns.

| Відмінок (Case) | Питання (Questions) | Друзі (m, an.) | Коні (m, an.) | Річки (f, inan.) | Міста (n, inan.) | Моря (n, inan.) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Н.** (Nom.) | хто? що? | друзі | коні | річки | міста | моря |
| **Р.** (Gen.) | кого? чого? | друз**ів** | кон**ей** | річ**ок** | міст | мор**ів** |
| **Д.** (Dat.) | кому? чому? | друз**ям** | кон**ям** | річк**ам** | міст**ам** | мор**ям** |
| **Зн.** (Acc.) | кого? що? | друз**ів** | кон**ей** / коні | річки | міста | моря |
| **Ор.** (Instr.) | ким? чим? | друз**ями** | **кіньми** | річк**ами** | міст**ами** | мор**ями** |
| **М.** (Loc.) | на/у кому? чому? | на/у друз**ях** | на/у кон**ях** | на/у річк**ах** | по/у міст**ах** | у/на мор**ях** |
| **Кл.** (Voc.) | (звертання) | друзі | коні | річки | міста | моря |

*(Paradigms compiled from Sources 35, 39, 41, and 33)*

**Key Observations:**
*   **Genitive Plural (`-ів`, `-ей`, `-ок`)**: This is the most complex case. Common endings are `-ів` (for many masculine/neuter nouns like `друзів`, `морів`), `-ей` (for some like `коней`, `гостей`), or a **zero-ending** (`-ø`), often with a vowel change (`річка` -> `річок`, `нога` -> `ніг`) (Source 39).
*   **Dative (`-ам`, `-ям`)**: Very regular. Ends in `-ам` after a hard consonant and `-ям` after a soft one (Source 39).
*   **Accusative (Animate vs. Inanimate)**: For inanimate nouns (`річки`, `міста`), the form is identical to the Nominative. For animate nouns (`друзі`, `коні`), the form is identical to the Genitive (Source 30, 41).
*   **Instrumental (`-ами`, `-ями`, `-ми`)**: Mostly regular with `-ами`/`-ями`. However, a small but common group of masculine nouns uses the ending `-ми` (e.g., `кіньми`, `гістьми`, `чобітьми`). The form `дверима` (doors) is also common (Source 24, 41).
*   **Locative (`-ах`, `-ях`)**: Very regular. Always used with a preposition (`на`, `у`, `по`) (Source 28, 37).
*   **Vocative**: In the plural, the Vocative is almost always identical to the Nominative (Source 22, 35).

### Pluralia Tantum (Іменники, що мають лише форму множини)
A number of common nouns exist only in the plural. They follow similar declension patterns.

| Відмінок (Case) | Питання (Questions) | Карпати (гори) | Окуляри (очі) | Гроші (кошти) |
| :--- | :--- | :--- | :--- | :--- |
| **Н.** (Nom.) | що? | Карпати | окуляри | гроші |
| **Р.** (Gen.) | чого? | Карпат | окуляр**ів** | грош**ей** |
| **Д.** (Dat.) | чому? | Карпат**ам** | окуляр**ам** | грош**ам** |
| **Зн.** (Acc.) | що? | Карпати | окуляри | гроші |
| **Ор.** (Instr.) | чим? | Карпат**ами** | окуляр**ами** | **грішми** / грошима |
| **М.** (Loc.) | на/у чому? | в/на Карпат**ах** | в окуляр**ах** | у грош**ах** |
| **Кл.** (Voc.) | (звертання) | Карпати | окуляри | гроші |

*(Examples and forms from Sources 3, 23, 24, 39)*

## Частотність і пріоритети

For A2 learners, not all cases are used with equal frequency in plural forms. The goal is communication, so focus should be on the most common patterns.

1.  **Priority 1: Locative & Instrumental**
    *   **Locative (`-ах`/`-ях`)**: Essential for talking about location. Phrases like `в Карпатах` (Source 3), `на канікулах` (Source 11), `у містах` (Source 1) are extremely common. The pattern is highly regular and provides a high return on investment.
    *   **Instrumental (`-ами`/`-ями`)**: Crucial for expressing "with...". The phrase `з друзями` (with friends) is ubiquitous in texts about social activities (Source 1, 6). The pattern is also very regular.

2.  **Priority 2: Genitive & Accusative (Animate)**
    *   **Genitive Plural (`-ів`, zero ending)**: Necessary for expressing absence (`немає друзів`, `немає проблем`), quantity (`багато друзів`, `кілька місяців`), and belonging (`свято для дітей`). The zero-ending with vowel changes (`книжка` -> `книжок`) is challenging but frequent. The `-ів` ending is very common for masculine nouns.
    *   **Accusative Plural (Animate)**: Since this form matches the Genitive for animate nouns (`Я люблю своїх друзів`), mastering the Genitive helps master this as well. It's vital for any sentence where the direct object is a group of people or animals.

3.  **Priority 3: Dative**
    *   **Dative Plural (`-ам`/`-ям`)**: While grammatically simple, its usage in the plural is less frequent in basic A2 conversation than other cases. It's used for giving something *to* multiple people (`дякувати друзям`) or for age (`дітям п'ять років`), but many of these constructions can be worked around at a lower level. It becomes more important at B1.

## Типові помилки L2 (Common L2 Errors)

English speakers often struggle with cases in general. Here are specific pitfalls related to plural nouns.

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| Я був в **Карпати**. | Я був в **Карпатах**. | This is a direct transfer from English syntax, which does not change the noun form after a preposition like "in". The Locative case (`-ах`/`-ях`) is mandatory after prepositions of location like `в` and `на` (Source 3, 37). |
| Я не маю **книги**. | Я не маю **книжок** / **книг**. | The Genitive plural is often a zero-ending, frequently requiring a vowel insertion (`книжка -> книжок`) for ease of pronunciation. Simply using the Genitive singular form is a common error (Source 39). |
| Я бачу мої **друзі**. | Я бачу моїх **друзів**. | Learners forget that the Accusative case for animate nouns is identical to the Genitive case, not the Nominative. `Друзі` is "who/what" (subject), but `друзів` is "whom/what" (object) (Source 39, 41). |
| Ми говорили **з друзі**. | Ми говорили **з друзями**. | Forgetting to apply the Instrumental case ending `-ами`/`-ями` after the preposition `з` ("with") is a typical mistake. The noun must change to show its role in the phrase (Source 1, 35). |
| Ми їхали по **полям**. | Ми їхали по **полях**. | This is a classic Russism. In Russian, the Dative plural (`по полям`) is used after `по`. In Ukrainian, the Locative plural (`по полях`) is correct for movement across a surface (Source 20). |

## Деколонізаційні застереження (Decolonization Notes)

It is critical to teach Ukrainian grammar on its own terms, not as a variant of Russian. The two languages, while related, have followed different evolutionary paths from Proto-Slavic, resulting in significant structural differences.

1.  **The `по` + Locative Rule**: The most common L2 error influenced by Russian is the use of the preposition `по`. In Ukrainian, when `по` indicates movement across a surface or distribution, it requires the **Locative** case: `ходити по магазинах`, `гуляти по полях`. In Russian, this construction uses the Dative case (`ходить по магазинам`). Explicitly teaching `по + М.в.` as the Ukrainian standard is a crucial decolonization point (Source 20).

2.  **Instrumental Plural `-ми`**: Ukrainian has preserved an archaic Instrumental plural ending `-ми` for a specific group of nouns (mostly 2nd and 4th declension), such as `кіньми`, `гістьми`, `дверима`, `грошима`. While parallel forms with `-ами`/`-ями` (`грошима`) sometimes exist, the `-ми` form is distinctly Ukrainian and should be presented as a normal, living feature of the language, not a strange exception (Source 41, 24). In modern Russian, this ending is largely considered archaic or poetic.

3.  **Genitive Plural Variations**: The formation of the Genitive plural in Ukrainian, with its complex system of vowel alternations (`нога` -> `ніг`), inserted vowels (`земля` -> `земель`), and varied endings (`-ів`, `-ей`, zero), is a unique feature. It should not be simplified or taught using Russian models, which have their own (different) set of complexities. The Ukrainian system must be learned from Ukrainian examples.

4.  **Vocabulary Choice**: Use authentically Ukrainian vocabulary in examples. Avoid words that are calques or direct loans from Russian when a native Ukrainian equivalent exists. For instance, in social contexts, use `зустрічатися з друзями` (Source 1) rather than constructions that might mirror Russian phrasing.

Presenting Ukrainian as a self-contained system with its own logic is the core of a decolonized pedagogical approach.

## Природні приклади (Natural Examples)

These examples are taken from authentic Ukrainian sources and demonstrate the natural use of plural cases in context.

**Group 1: Locative (`-ах`/`-ях`) - Talking about location**
*   "Взимку в Києві дуже багато [цікавих подій], наприклад, в **театрах** і **операх** є багато вистав." (In winter in Kyiv there are many [interesting events], for example, in the theaters and operas there are many shows.) (Source 1)
*   "В українських **селах** на Різдво ставили не ялинку, а дідух." (In Ukrainian villages at Christmas, they used to put up not a Christmas tree, but a didukh.) (Source 10)
*   "...а ще в **горах** ми збирали гриби." (...and also in the mountains we gathered mushrooms.) (Source 3)

**Group 2: Instrumental (`-ами`/`-ями`) - Doing things "with" people or things**
*   "Зустрічайтеся частіше з **друзями**, ходіть в гості." (Meet more often with friends, visit each other.) (Source 1)
*   "Він [дельфін] пригадав, як грався з **друзями** — дельфінами, як ми разом супроводжували кораблі." (He [the dolphin] remembered how he played with his friends—dolphins, how we accompanied ships together.) (Source 6)
*   "Поїдь зі своїми **полками** поблизу мого полку." (Ride with your regiments near my regiment.) (Source 5)

**Group 3: Genitive (`-ів`, `-ей`, `-ø`) - Expressing quantity or absence**
*   "Для **дітей** ти просто диво!" (For children, you are simply a miracle!) (Source 6)
*   "Зараз у нас немає домашніх **тварин**." (Right now we don't have any pets.) (Source 7)
*   "У нас є багато **видів** чаю." (We have many kinds of tea.) (Source 1)

**Group 4: Accusative (Animate) - Direct objects that are alive**
*   "Взимку ми підгодовуємо **птахів**." (In winter, we feed the birds.) (Source 30)
*   "Я знаю, що ти зі своїми **друзями** завжди поспішаєш **людям** на допомогу." (I know that you and your friends always hurry to help people.) (Source 6) <!-- Note: Here 'людям' is Dative, but 'друзями' is Instrumental, showing case interplay -->

**Group 5: Dative (`-ам`/`-ям`) - Giving or helping people**
*   "А ми, люди, чим віддячуємо **дельфінам** за їхню любов і відданість?" (And what about us, people, how do we thank the dolphins for their love and devotion?) (Source 6)
*   "Моїм **батькам** дуже цікаво познайомитися з іноземцями." (It's very interesting for my parents to meet foreigners.) (Source 7)

## Рекомендації для вправ (Activity Concepts)

A phased approach is best for internalizing plural cases.

*   **Phase 1: Recognition & Identification (Input)**
    *   **Drill 1 (Case Matching)**: Given a list of plural nouns (`друзям`, `в горах`, `коней`, `книгами`), students match them to the correct case name and question (`Кому? Чому? -> Давальний`).
    *   **Drill 2 (Sentence Highlighting)**: Provide a short text (like a dialogue from Source 3). Students must find and highlight all plural nouns and identify their case.

*   **Phase 2: Controlled Production (Practice)**
    *   **Drill 3 (Fill-in-the-Blank)**: Provide sentences with a noun in the Nominative plural in parentheses. Students must write the correct form.
        *   `Я люблю гуляти з (мої друзі) ___________.` -> `моїми друзями`
        *   `У нас немає (домашні тварини) ___________.` -> `домашніх тварин`
        *   `Ми живемо в (Карпати) ___________.` -> `Карпатах`
    *   **Drill 4 (Transformation)**: Give a simple sentence in the singular and prompt students to create a plural version.
        *   `Я дав книгу другу.` -> `Я дав книги (друзі) ___________.` -> `друзям`
        *   `Кінь стоїть у полі.` -> `(Коні) ___________ стоять у полях.` -> `Коні`

*   **Phase 3: Communicative Production (Output)**
    *   **Activity 5 (Question & Answer)**: Ask open-ended questions that require plural cases in the answer.
        *   `Що ви робили з друзями минулих вихідних?` (Requires Instrumental)
        *   `В яких містах України ви були?` (Requires Locative)
        *   `Скільки у вас є українських книжок?` (Requires Genitive)
    *   **Activity 6 (Picture Description)**: Show a picture of a busy place (a market, a park) and have students describe it using plural nouns. `Я бачу багато людей. Вони розмовляють з друзями. Діти граються з собаками.`

## Зв'язки з іншими темами

*   **Prerequisites**: This topic directly builds on an understanding of **Nominative Plural** forms and the concept of **Cases in the Singular**. Without knowing how to form a basic plural (`друг` -> `друзі`), declining it is impossible.
*   **Adjective Agreement**: This is the immediate next step. Once a learner can form `з друзями`, they can learn to add adjectives that agree in case, number, and gender: `з **хорошими** друзями`. Teaching adjective declension without a solid foundation in noun declension is ineffective.
*   **Prepositions**: This topic reinforces the function of many prepositions (`з`, `в`, `на`, `про`, `для`, `без`), showing how they "govern" or require a specific case.

## Пов'язані статті

*   grammar/a1/noun-cases-singular
*   grammar/a1/nominative-plural
*   grammar/a2/adjective-declension-plural
*   grammar/a1/prepositions-and-cases
</wiki_context>

## Plan References

- 
- 

</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Множина називного відмінка (Nominative Plural)` (~650 words)
- `## Знахідний відмінок множини: Живе чи неживе? (Accusative Plural: Animate vs. Inanimate)` (~650 words)
- `## Називний чи знахідний? Визначаємо за контекстом (Nominative or Accusative? Reading the Context)` (~700 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 2000 words minimum.

---

## Content Rules

TARGET: 55-75% Ukrainian.
LANGUAGE ROLES:
- PRIMARY: Ukrainian for all content — dialogues, examples, section intros, cultural context.
- ENGLISH: Only for abstract grammar concepts that need explicit explanation.
- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English. Dialogues, examples, section intros all stay Ukrainian-only.
A2 register. Concrete everyday vocabulary. No literary language, no metaphors. Ukrainian sentences max 15 words. Max 2 clauses. All cases allowed. Simple subordinate clauses only. Aspect pairs introduced. No participles.

GRAMMAR RULES:
- Max 15 words per Ukrainian sentence
- Max 2 clauses per sentence
- All cases allowed
- Simple subordinate clauses allowed (який/що/коли)
- Aspect pairs introduced but not complex
- No participles

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
- Use callout boxes (:::tip, :::caution, :::note) — at least 3 per module (mnemonics, common mistakes, cultural notes). Space them throughout the module, not clustered.
- **Dialogue formatting** — use blockquote `>` with speaker names in bold. Each turn on its own line. At A1 level, add English translation in italics after each line so learners understand what is being said. At A2, translate only new vocabulary. At B1+, no dialogue translations. Example:

> **Оленка:** Привіт! Як справи? *(Hi! How are you?)*
> **Тарас:** Добре, дякую! А у тебе? *(Good, thanks! And you?)*
> **Оленка:** Теж добре! *(Also good!)*

Without speaker names, the reader cannot tell who is speaking. NEVER use anonymous em dashes (`— text`). After each dialogue, briefly explain the key phrases and patterns the learner just saw.
- **Dialogues must sound like real people talking.** Test: would two Ukrainians actually say this to each other? If the dialogue sounds like a textbook drill ("Це кінь? — Так, це кінь."), rewrite it. Good dialogues have context, reactions, and personality:

  BAD (interrogation): "Це сім'я? — Так, це сім'я. — А де м'ясо? — М'ясо там."
  GOOD (natural): "Це твоя сім'я на фото? — Так! Нас п'ять. — А що ви їсте? М'ясо? — Так, дуже смачне!"

  BAD (labeling objects): "Це дуб. — А там коза. — Ні, це коса."
  GOOD (real reaction): "Дивись, який великий дуб! — Так, старий. А під ним — коза! — Смішна коза."

  Use the knowledge packet's textbook excerpts for dialogue patterns. Adapt real situations, don't invent drills.
- **DIALOGUE VARIETY — CRITICAL.** Each module MUST have DIFFERENT dialogue situations from other modules. Before writing any dialogue, check: have previous modules used this setting? If yes, pick a different one.

  BANNED recurring settings (already used in M01-M09): describing a room (кімната), looking at a table/bed/lamp, generic greetings with no context, labeling objects.

  REQUIRED: Every dialogue must have a SPECIFIC REAL-WORLD SITUATION that motivates the grammar being taught. The situation must be different from all other modules.

  **Module-specific dialogue settings (from plan):**
  1. **At a zoo — identifying animals and their groups: Дивись — леви (m, lions)! Бачиш тих жирафів (m, giraffes)? А ось мавпи (f, monkeys)! Діти люблять пінгвінів (m, penguins).**
     Speakers: Батько/Мати, Діти
     Why: Nom plural: лев→леви. Acc animate plural: жираф→жирафів, пінгвін→пінгвінів

  Use these settings. Do NOT substitute with a room description or generic greeting.
- **Tone: direct, clear, no filler.** State facts and teach. Don't praise the language ("beautiful", "wonderful", "unique melody"), don't praise the learner ("great job", "you've mastered"), don't narrate what you're doing ("In this section we will", "Now let's look at"). Just teach. Example:

  BAD: "The Ukrainian language has a wonderfully consistent and beautiful phonetic system."
  GOOD: "Ukrainian spelling is highly phonetic — what you see is what you hear."
- **Never guess about Ukrainian.** If you are unsure about a word, grammatical form, or phonetic rule — flag it with `<!-- VERIFY: word/claim -->`. Never invent or describe vaguely to hide uncertainty.

### Forbidden Tropes

If you write any of these patterns, the module will be rejected in review:

- **The Cheerleader:** "Great job!", "Don't worry, it's easy!", "You're doing amazing!", "Good news!" — respect the learner's intelligence; stay professional.
- **The Announcer:** "In this section, we will explore...", "Now let's dive into...", "Let's take a look at...", "To summarize what we learned..." — never use formulaic transitions. Just teach the concept directly.
- **The Translator:** "The Ukrainian word for 'cat' is 'кіт'." — instead, present naturally: "A domestic cat is a **кіт**."
- **The Wall of Text:** 3+ paragraphs of English theory without a single Ukrainian example — every concept must be anchored in immediate Ukrainian examples.
- **The Filler:** "This is a very important concept that you will use frequently in your daily life." — empty sentences that add words but not meaning. Every sentence must teach something.



### Vocabulary

**Required:** множина (plural), називний відмінок (nominative case), знахідний відмінок (accusative case), живий (animate), неживий (inanimate), закінчення (ending (grammar)), люди (people), діти (children), речі (things), очі (eyes)
**Recommended:** відміна (declension class), чергування (alternation), предмет (object, item), група (group)

### Pronunciation Videos

**Do NOT embed YouTube videos in your prose.** A downstream ENRICH tool automatically places pronunciation videos from the plan. If you embed `<YouTubeVideo>` components, they will be duplicated. Simply reference the videos' existence when relevant (e.g., "Watch the pronunciation video for this letter") but do NOT insert `<YouTubeVideo>` tags.

Available videos (for reference only — ENRICH handles placement):


---

### Style Reference (match this tone and structure)

> **(У магазині / At the store)**
> — Добрий день! Скільки коштує хліб? (Good day! How much does the bread cost?)
> — Дванадцять гривень. (Twelve hryvnias.)
> — Дякую! Ось, будь ласка. (Thanks! Here you go.)

Notice that the shopkeeper uses **Добрий день** — the formal greeting for strangers. If this were a friend, they would say **Привіт** instead.

The word **скільки** (how much/how many) is one of the most useful question words. It always pairs with the genitive case: **скільки коштує** (how much does it cost), **скільки часу** (how much time).

*Note: Short dialogues in Ukrainian with per-line English glosses. Grammar explained in English. Ukrainian sentences in blockquotes and bulleted lists.*



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
## Множина називного відмінка (Nominative Plural) (~750 words)
- P1 (~120 words): [Dialogue: At the Zoo] A family identifies animals in groups. Focus on Nominative plural (леви, мавпи, жирафи) and Accusative animate (пінгвінів).
- P2 (~80 words): [Introduction to Plurality] Contrast between singular and plural concepts in Ukrainian. Briefly review the four declension classes (відміни) as the roadmap for forming plurals.
- P3 (~100 words): [I Declension: Feminine/Masculine -а/-я] Explain endings for hard stems (-и: сестри, мами, книжки) versus soft and mixed stems (-і: землі, судді, пісні).
- P4 (~130 words): [II Declension: Masculine] Transition from singular consonants to plural -и for hard stems (столи, заводи, телефони) and -і for soft/mixed (коні, плащі, герої). Explain the consonant alternation in high-frequency words (друг → друзі).
- P5 (~100 words): [II Declension: Neuter] Forming plurals for neuter nouns. Explain the shift from -о to -а (міста, села, вікна) and from -е/-я to -я (поля, моря, обличчя).
- P6 (~70 words): [III Declension: Feminine Consonant] Focus on the consistent -і ending. Examples: ночі, речі, подорожі, солі. Note the special form: матері.
- P7 (~70 words): [IV Declension: Neuter -ат-/-ят-] Explaining the plural of young creatures. Examples: курчата, телята, кошенята, лошата.
- P8 (~80 words): [Common Irregulars] Essential irregular forms that must be memorized as lexical units: людина → люди, дитина → діти, око → очі, вухо → вуха, плече → плечі.
- <!-- INJECT_ACTIVITY: fill-in-nom-plural --> [fill-in, focus: Form the Nominative plural from given singular nouns across all declension classes, 8 items]

## Знахідний відмінок множини: Живе чи неживе? (Accusative Plural: Animate vs. Inanimate) (~650 words)
- P1 (~100 words): [The Golden Rule] Introduce the fundamental distinction: Inanimate Acc.Pl = Nom.Pl; Animate Acc.Pl = Gen.Pl. Highlight that unlike singular masculine, this rule applies to ALL genders in the plural.
- P2 (~120 words): [Inanimate Objects] Practice sentences with inanimate direct objects where the form remains identical to Nominative. Examples: "Я бачу столи", "Вона купує книжки", "Ми любимо ці міста".
- P3 (~130 words): [Animate Beings] Transition to animate nouns where Accusative equals Genitive plural. Examples: "Я бачу студентів", "Ми зустріли сестер", "Він годує птахів". Focus on the -ів ending for masculine and zero-ending for feminine/neuter.
- P4 (~100 words): [The "Student" Trap] A contrastive paragraph for English speakers. Explain why "I see students" cannot be "*Я бачу студенти" but must be "Я бачу студентів," emphasizing the Genitive-match for people.
- P5 (~100 words): [Verbal Governance] List and use common verbs that trigger the Accusative plural: бачити (see), знати (know), любити (love), зустрічати (meet), шукати (look for).
- P6 (~100 words): [Mixed Sentences] Narrative examples combining animate and inanimate objects to reinforce the switch: "На столі лежать підручники (Inan), але я бачу тільки студентів (An.)."
- <!-- INJECT_ACTIVITY: sort-animate-inanimate --> [group-sort, focus: Sort plural nouns into animate vs. inanimate, then predict their Accusative form, 8 items]
- <!-- INJECT_ACTIVITY: quiz-acc-plural-choice --> [quiz, focus: Choose the correct Accusative plural form (animate = Gen.Pl., inanimate = Nom.Pl.) in sentences, 8 items]

## Називний чи знахідний? Визначаємо за контекстом (Nominative or Accusative?) (~750 words)
- P1 (~120 words): [Syntactic Roles: Subject vs. Object] Explain the "Who/What test." If the noun is doing the action (Subject), it's Nominative. If the action is being done to it (Direct Object), it's Accusative.
- P2 (~130 words): [The Identity Crisis] Focus on inanimate nouns (книжки, машини, поля) that look identical in Nom/Acc. Explain that word order and verb meaning are the only clues. Example: "Машини стоять" (Nom) vs "Я бачу машини" (Acc).
- P3 (~120 words): [Case Contrast in Action] Analyze the sentence: "Студенти (Nom) читають книжки (Acc)." Swap the roles to show meaning change: "Книжки (Nom) вчать студентів (Acc)."
- P4 (~130 words): [Dialogue: At a Busy Market] A natural dialogue using Nom/Acc plural in flow. Speakers identify people (продавці, покупці) and objects (овочі, фрукти, ціни).
- P5 (~130 words): [Prepositions with Accusative Plural] Introduce prepositions that govern Accusative when indicating direction or duration: через (through/across), на (onto/for), про (about). Examples: "про фільми," "через гори," "на вихідні."
- P6 (~120 words): [Contextual Reading Practice] A short paragraph describing a classroom or street scene where the learner must track which plural nouns are subjects and which are objects based on the narrative logic.
- <!-- INJECT_ACTIVITY: error-correction-plural --> [error-correction, focus: Find and fix wrong plural noun endings in Nominative and Accusative, 6 items]

## Підсумок (~150 words)
- P1 (~150 words): [Self-check Checklist]
  - Яке закінчення мають іменники І відміни в Н.в. множини? (-и / -і)
  - Яка головна різниця між Зн.в. для істот і неістот? (Істоти = Р.в., неістоти = Н.в.)
  - Як перекласти "I see children"? (Я бачу дітей)
  - Чи змінюються назви неістот у Зн.в. множини порівняно з Н.в.? (Ні)
  - Назвіть множину слів "людина", "дитина", "око". (люди, діти, очі)

Grand total: ~2300 words
</skeleton>

## Output Format

Write in Markdown. Use:
- `## Section Title` for main sections
- `### Subsection` for subsections within a section
- `**bold**` for Ukrainian words being taught — EVERY bold Ukrainian word MUST have an English translation on first use, either in parentheses `**слово** (translation)` or inline `**слово** means "translation"`. No exceptions.
- Tables for paradigms (conjugation, declension)
- `:::tip` / `:::caution` / `:::note` for callout boxes
- `<!-- INJECT_ACTIVITY: {id} -->` for exercise placement (markers only — do NOT write exercise content)

Do NOT write MDX component syntax, JSON, or DSL exercise blocks (:::quiz, etc.). Plain Markdown with injection markers.

Begin writing now. Start with the first section heading.
