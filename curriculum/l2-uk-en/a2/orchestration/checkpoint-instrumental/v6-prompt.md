

---

## Your Writing Identity

**You are: Lead Ukrainian Instructor.** Your persona is *The Conversation Partner*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **31: Контрольна точка: Орудний відмінок** (A2, A2.4 [Instrumental Case]).

**Target: 1500–2250 words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block. Evaluate each section from the plan and commit to a word budget. This prevents frontloading early sections and rushing later ones.

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Summary: ~150 words
Total: 1500+ words
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
8. **Hit the word target** — you MUST write 1500–2250 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
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
module: a2-031
level: A2
sequence: 31
slug: checkpoint-instrumental
version: '1.0'
title: 'Контрольна точка: Орудний відмінок'
subtitle: 'Перевірка знань: усі функції орудного відмінка'
focus: review
pedagogy: Review
phase: A2.4 [Instrumental Case]
word_target: 1500
objectives:
- Learner can accurately produce Instrumental singular and plural endings for nouns of all three genders
  in varied contexts.
- Learner can correctly use all Instrumental functions (accompaniment, tool/means, profession, spatial
  prepositions) in connected discourse.
- Learner can form complete noun phrases in Instrumental with adjective and pronoun agreement (з моїм
  новим другом, під великою ялинкою).
- Learner can synthesize Instrumental knowledge in a short paragraph describing their daily routine, profession,
  and surroundings.
dialogue_situations:
- setting: 'Describing a perfect picnic — everything with instrumental: Поїхали автобусом (m). Гуляли
    з дітьми (pl). Їли бутерброди з ковбасою (f). Сиділи під деревом (n). Цей день був найкращим!'
  speakers:
  - Друзі (згадуючи)
  motivation: 'All instrumental: автобусом, з дітьми, з ковбасою, під деревом'
content_outline:
- section: 'Частина 1: Розпізнавання та форми (Part 1: Recognition and Forms)'
  words: 400
  points:
  - 'Exercise 1: A short text about someone''s day is provided. Learner must identify all nouns in the
    Instrumental case and label each function (tool, companion, profession, spatial, temporal).'
  - 'Exercise 2: Put nouns in parentheses into the correct Instrumental form — covers all three genders,
    hard and soft stems: (брат) → братом, (подруга) → подругою, (море) → морем.'
  - 'Exercise 3: Form Instrumental plural from given Nominative plurals: (руки) → руками, (олівці) → олівцями,
    (діти) → дітьми.'
- section: 'Частина 2: Вибір та застосування (Part 2: Choice and Application)'
  words: 500
  points:
  - 'Exercise 4: Choose the correct preposition (з, над, під, перед, за, між) to complete spatial and
    temporal sentences.'
  - 'Exercise 5: Decide whether to use bare Instrumental or з + Instrumental — tool vs. accompaniment
    discrimination (писати ручкою vs. ходити з другом).'
  - 'Exercise 6: Multiple-choice — select the correct Instrumental form of adjective + noun phrases (з
    [гарний/гарним/гарною] [друг/другом/другові]).'
  - 'Exercise 7: Transform Nominative sentences into sentences using бути/стати + Instrumental for professions
    (Вона лікарка → Вона буде лікаркою).'
- section: 'Частина 3: Вільне вживання (Part 3: Free Production)'
  words: 600
  points:
  - 'Exercise 8: Answer open-ended questions requiring various Instrumental functions: Ким ти працюєш?
    Чим ти захоплюєшся? З ким ти живеш? Що знаходиться перед твоїм будинком?'
  - 'Exercise 9: Describe a picture of a kitchen scene — who is cooking, what tools they use, what ingredients
    are on the table, where objects are located.'
  - 'Exercise 10: Writing prompt (8-10 sentences): "Опишіть свій типовий день. Розкажіть про свою професію,
    як ви добираєтесь на роботу, з ким ви обідаєте, і що ви готуєте на вечерю." Learner must use at least
    6 different Instrumental constructions.'
vocabulary_hints:
  required:
  - орудний відмінок (instrumental case)
  - вправа (exercise)
  - контрольна точка (checkpoint)
  - завдання (task)
  - речення (sentence)
  - відповідь (answer)
  - текст (text)
  - перевірка (check, test)
  recommended:
  - правильний (correct)
  - словосполучення (phrase, word combination)
  - описати (to describe)
  - визначити (to identify, to determine)
activity_hints:
- type: quiz
  focus: Mixed Instrumental case quiz covering all functions from M21-M26
  items: 8
- type: fill-in
  focus: Sentence transformation — put noun phrases into Instrumental with correct agreement
  items: 8
- type: group-sort
  focus: Sort Instrumental sentences by function (tool, companion, profession, spatial, temporal)
  items: 8
- type: error-correction
  focus: Find and correct grammar errors in sentences covering module topics
  items: 6
references:
- title: Захарійчук Grade 4, с. 62-69
  notes: Full Instrumental case unit — endings, prepositions, exercises for all genders
- title: Заболотний Grade 5, §20-23
  notes: Instrumental case review exercises in broader declension context
- title: Голуб Grade 6, с. 179
  notes: Pronoun declension tables for review of Instrumental pronoun forms

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
- Confirmed: вправа, завдання, речення, відповідь, текст, перевірка, правильний, словосполучення, описати, визначити, брат, подруга, море, рука, олівець, дитина, орудний, відмінок, контрольний, точка.
- Not found: All individual words found. "Орудний відмінок" and "контрольна точка" are verified as combinations of confirmed words.

## Grammar Rules
- Instrumental Case (Орудний відмінок): Правопис § 73, 82, 91 (declension specific) — Nouns answer "ким? чим?". 
- Endings (Singular): 1st decl. (fem/masc -а/-я): -ою (hard), -ею (soft/mixed), -єю (vowel + soft). 2nd decl. (masc/neut): -ом (hard), -ем (soft/mixed), -єм (vowel + soft). 3rd decl. (fem -null): -ю (with consonant doubling, e.g., ніччю, подорожжю).
- Endings (Plural): Mostly -ами (hard) or -ями (soft). Exceptions: дітьми, кіньми, людьми, грошима, плечима (confirmed in Grade 6 textbook, Result 1).

## Calque Warnings
- правильний: OK — usage "правильна відповідь" is standard (confirmed in Zabolotnyi 2020 Grade 6 textbook). Avoid Russianism "вірний" in this context.
- контрольна точка: OK — technical term for "checkpoint". For a course unit, "підсумковий урок" or "контрольне завдання" is more traditional, but "контрольна точка" is acceptable for modern L2 frameworks.
- описати / визначити: OK — standard instructional verbs in Ukrainian textbooks (Grade 4/5).

## CEFR Check
- речення: A1 — OK
- текст: A1 — OK
- відповідь: A1 — OK
- завдання: A1 — OK
- орудний: A2 — Target Level OK
- вправа: A1 — OK
- правильний: A2 — OK
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
# Knowledge Packet: Контрольна точка: Орудний відмінок
**Module:** checkpoint-instrumental | **Track:** A2

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: grammar/a2/checkpoint-instrumental.md

# Граматика A2: Контрольна точка: Орудний відмінок



## Як це пояснюють у школі (How Schools Teach This)
В українській шкільній програмі орудний відмінок (Ор. в.) вводиться як один із семи відмінків, що відповідає на питання **ким? чим?** (Source 31: `6-klas-ukrmova-avramenko-2023_s0095`). Його вивчення починається в початкових класах і поглиблюється в середній школі (класи 5-6), коли учні системно вивчають відмінювання іменників, прикметників та займенників.

Підручники вводять орудний відмінок через його основні функції:
1.  **Інструмент або засіб дії**: Це основне, "інструментальне" значення. Учні вчаться утворювати словосполучення, де залежне слово в орудному відмінку відповідає на питання "чим щось роблять?". Приклад: `посипати (чим?) землею` (Source 31: `6-klas-ukrmova-avramenko-2023_s0095`).
2.  **Дійова особа в пасивних конструкціях**: Пояснюється, що орудний відмінок може позначати виконавця дії. Наприклад, у реченні `Картина намальована аквареллю` (Source 27), акварель є інструментом, а в `Слово було забуте (ким?) дітьми` (Source 13), "діти" є виконавцями дії забування.
3.  **Супровід (з ким?)**: Учні вчать, що прийменник `з` вимагає орудного відмінка для позначення супроводу. Наприклад: `іду (з ким?) з другом` (Source 31), `розмовляла з (ким?) ним` (Source 29).
4.  **Керування дієсловами**: Підручники наводять списки дієслів, які вимагають після себе орудного відмінка без прийменника. Наприклад, `милуватися (чим?) краєвидом` (Source 10), `захоплюватися (чим?) танцями` (Source 15), `пишатися (ким?) вами` (Source 29).

Навчальний процес зазвичай іде від простого до складного: спочатку відмінювання іменників, потім узгодження з ними прикметників (`зворушливою промовою` — Source 34), і далі — відмінювання займенників та числівників. Особлива увага приділяється правопису, наприклад, подовженню приголосних в іменниках III відміни (`ніччю` — Source 33) та паралельним формам (`шістдесятьма / шістдесятьома` — Source 21).

## Повна парадигма (Full Paradigm)
Орудний відмінок має характерні закінчення для різних частин мови та відмін.

### Іменники (Nouns)

| Відміна | Рід | Однина | Приклади | Множина | Приклади |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **I** | Жін., Чол. | `-ою`, `-ею`, `-єю` | сестр**ою**, земл**ею**, мрі**єю** | `-ами`, `-ями` | сестр**ами**, земл**ями** |
| **II** | Чол. | `-ом`, `-ем`, `-єм` | стóл**ом**, кра**єм**, музé**єм** | `-ами`, `-ями` | стол**ами**, кра**ями** |
| | Сер. | `-ом`, `-ем`, `-єм` | вікн**óм**, мóр**ем**, місц**ем** | `-ами`, `-ями` | вікн**ами**, мор**ями** |
| **III** | Жін. | `-ю` | ні**ччю**, матір'**ю**, любов'**ю** | `-ами`, `-ями` | ноч**ами**, матер**ями** |
| **IV** | Сер. | `-ям`, `-ям`, `-енем/-ям` | тел**ям**, ім'**ям**/ім**енем** | `-атами`, `-ятами`, `-енами` | тел**ятами**, імен**ами** |

**Особливості правопису:**
*   **Іменники III відміни**: Якщо основа закінчується на один м'який або шиплячий приголосний, відбувається подовження: `зустріч` → `зустріччю`, `мить` → `миттю`. Якщо основа закінчується на губний (`[б], [п], [в], [м], [ф]`), `[р]`, або на два приголосних, подовження немає і ставиться апостроф: `любов` → `любов'ю`, `мати` → `матір'ю`, `радість` → `радістю` (Source 33).
*   **Іменники IV відміни**: Іменники на `-я` з суфіксом `-ен-` мають паралельні форми: `ім'ям` та `іменем`, `тім'ям` та `тіменем` (Source 23).

### Прикметники (Adjectives)

Прикметники в орудному відмінку узгоджуються з іменником у роді, числі та відмінку.

| Рід | Однина | Приклад | Множина | Приклад |
| :--- | :--- | :--- | :--- | :--- |
| **Чоловічий** | `-им` | нов**им** стол**ом** | `-ими` | нов**ими** стол**ами** |
| **Жіночий** | `-ою`, `-ею` | нов**ою** книг**ою**, син**ьою** ручк**ою** | `-ими` | нов**ими** книг**ами** |
| **Середній** | `-им` | нов**им** вікн**ом** | `-ими` | нов**ими** вікн**ами** |

### Займенники (Pronouns)

| Особа | Однина | З прийменником | Множина | З прийменником |
| :--- | :--- | :--- | :--- | :--- |
| **1-ша** | мн**ою** | зі мн**ою** | н**ами** | з н**ами** |
| **2-га** | тоб**ою** | з тоб**ою** | в**ами** | з в**ами** |
| **3-тя (ч.р/с.р)** | **ним** | з **ним** | **ними** | з **ними** |
| **3-тя (ж.р)** | **нею** | з **нею** | **ними** | з **ними** |

**Важливо:** Займенники 3-ої особи (`він, вона, воно, вони`) в орудному відмінку **завжди** мають приставний `н-`, незалежно від наявності прийменника (Source 29, Source 26).

### Числівники (Numerals)

Відмінювання числівників в орудному відмінку складне.
*   **2, 3, 4**: `двома`, `трьома`, `чотирма`.
*   **5-20, 30**: мають закінчення `-ма` або `-ома`: `п'ятьма / п'ятьома`, `шістьма / шістьома`.
*   **40, 90, 100**: `сорока`, `дев'яноста`, `ста`.
*   **Десятки (50-80)**: `п'ятдесятьма / п'ятдесятьома`, `шістдесятьма / шістдесятьома` (Source 21).
*   **Сотні (200-900)**: `двомастами`, `трьомастами`, `чотирмастами`, `п'ятьмастами / п'ятьомастами`, `шістьмастами / шістьомастами` (Source 21).

## Частотність і пріоритети
На рівні А2 учень повинен впевнено володіти найчастотнішими функціями орудного відмінка.

**Високий пріоритет (must know):**
1.  **Інструмент/Засіб**: *Що ти робиш? — Я пишу **ручкою**.* Це найперше і найважливіше значення.
2.  **Супровід з прийменником `з`**: *З ким ти йдеш? — Я йду з **другом** і **подругою**.*
3.  **Предикатив з дієсловами `бути`, `стати`**: *Ким він хоче стати? — Він хоче стати **лікарем**. Христина буде працювати **вчителькою**.* (Source 3)
4.  **Керування найпоширенішими дієсловами**:
    *   `цікавитися (чим?)` - *Я цікавлюся **історією**.*
    *   `займатися (чим?)` - *Вона займається **спортом**.*
    *   `пишатися (ким?/чим?)` - *Ми пишаємося **вами**.* (Source 29)

**Середній пріоритет (should know):**
1.  **Шлях/Місце дії (де? як?)**: *Ми йшли **лісом**. Стелеться **степом** битий шлях.* (Source 15)
2.  **Час**: *темної **ночі**, літнього **вечора**.*
3.  **Пасивний суб'єкт**: *Портрет, вишитий **хрестиком**.* (Source 27)

**Низький пріоритет (can wait for B1+):**
*   Складні випадки відмінювання числівників (`тисячею вісьмастами вісімдесятьма чотирма`).
*   Рідковживані дієслова, що вимагають орудного відмінка.
*   Орудний відмінок порівняння (`старший за мене роком`).

## Типові помилки L2 (Common L2 Errors)
Англомовні учні часто роблять помилки, переносячи конструкції з рідної мови або плутаючи функції відмінків.

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| Я говорю **на українській мові**. | Я говорю **українською мовою**. | В українській мові для позначення мови мовлення використовується орудний відмінок без прийменника. Конструкція `на ... мові` є калькою з російської. (Source 14). |
| Я милуюся **з краєвиду**. | Я милуюся **краєвидом**. | Дієслово `милуватися` вимагає орудного відмінка без прийменника. Вживання прийменника `з` + родовий відмінок є помилкою. (Source 10). |
| Ми сумуємо **по канікулах**. | Ми сумуємо **за канікулами**. | Дієслово `сумувати` в українській мові вимагає прийменника `за` + орудний відмінок. Конструкція `по` + місцевий відмінок є русизмом. (Source 14). |
| Він вдарив **з молотком**. | Він вдарив **молотком**. | Для позначення інструменту дії прийменник `з` не використовується. `З` вказує на супровід (`з другом`) або походження (`з України`). |
| Ця пісня написана **від Тараса Шевченка**. | Ця пісня написана **Тарасом Шевченком**. | В пасивних конструкціях для позначення автора/виконавця дії використовується орудний відмінок, а не прийменник `від`. |
| Ми говорили про **його**. | Ми говорили про **нього**. | Займенники 3-ої особи (`він, вона, воно, вони`) після будь-якого прийменника отримують приставний `н-`. (Source 29, Source 38). |

## Деколонізаційні застереження (Decolonization Notes)
**Обов'язково для засвоєння:** українська мова — це самостійна система, а не діалект чи варіація російської. Порівняння з російською припустиме лише для уникнення типових помилок інтерференції (суміші мов), але ніколи для пояснення правил. Українська граматика є вихідною точкою.

1.  **Керування дієсловами**: Це одна з ключових відмінностей.
    *   **Сміятися**: укр. `сміятися **з** когось/чогось` (родовий відмінок) vs. рос. `смеяться **над** кем/чем` (орудний відмінок). У підручнику прямо вказано: "Неправильно: сміятися над другом. Правильно: сміятися з друга" (Source 15).
    *   **Дякувати**: укр. `дякувати **комусь**` (давальний відмінок) vs. рос. `благодарить **кого**` (знахідний відмінок). Хоч це не стосується орудного, це яскравий приклад розбіжностей у керуванні.
    *   **Потребувати**: укр. `потребувати **чогось**` (родовий відмінок) vs. рос. `нуждаться **в** чём` (місцевий відмінок).

2.  **Прийменникові конструкції**:
    *   **Говорити мовою**: укр. `говорити **українською мовою**` (орудний відмінок) vs. рос. `говорить **на** украинском языке` (місцевий відмінок). Використання `на` в цьому контексті в українській мові є грубою помилкою і поширеним русизмом (Source 14).
    *   **Сумувати**: укр. `сумувати **за** кимсь/чимсь` (орудний відмінок) vs. рос. `скучать/грустить **по** кому/чему` (давальний відмінок). Вживання `сумувати по` є помилкою (Source 14).

3.  **Фонетичні та морфологічні особливості**: Не варто пояснювати українські форми через російські аналоги. Наприклад, подовження приголосних (`ніччю`) — це самостійне фонетичне явище української мови, а не "дивна зміна" порівняно з російським `ночью`.

**Педагогічний висновок:** Навчаючи орудного відмінка, слід зосередитись на внутрішній логіці української мови, використовуючи автентичні українські приклади і активно виправляючи русизми, пояснюючи їх як помилки, а не як "альтернативні форми".

## Природні приклади (Natural Examples)
**Мінімум 12 прикладів з джерел, згрупованих за функцією.**

**Група 1: Інструмент / Засіб дії**
1.  Христина пригостила Лесю **піцою**. (Source 8)
2.  Леся часто пригощає Христину **котлетками**, **варениками**, **пиріжками**. (Source 8)
3.  Зореслава підійшла до вишитого **хрестиком** портрета коханого чоловіка. (Source 27)

**Група 2: Предикатив (бути/стати кимось/чимось)**
4.  Христина буде працювати **вчителькою** в школі. (Source 3)
5.  ...учень або учениця, які наприкінці року отримують тільки дуже високі оцінки... це в Україні це 10 11 12... я була **відмінницею** всі 11 років в школі. (Source 4)

**Група 3: Керування дієсловами (без прийменника)**
6.  Туристи милувалися **краєвидом**. (Source 10)
7.  Сестра захоплюється **танцями**, а я — **футболом**. (Source 15)
8.  Grammarly використовує **штучний інтелект**. (Source 6)

**Група 4: Супровід (з прийменником `з/із`)**
9.  Баба з **воза** — кобилі легше. (Іменник "віз" тут у родовому відмінку, це прислів'я, не найкращий приклад для супроводу. Візьмемо інший).
10. Розмовляла з **ним**, побачили **тебе**, подарували **мені**, зустрівся з **нею**. (Тут багато прикладів, оберемо один: `зустрівся з нею`) (Source 29).
11. Я з **татом** прибираємо у квартирі. (Source 15)

**Група 5: Пасивний виконавець дії**
12. О слово рідне... **дітьми** безпам'ятно забутий. (Source 13)
13. Вправи, рекомендовані моїм **тренером**, виявилися ефективними. (Source 27)

## Рекомендації для вправ (Activity Concepts)

**Phase 1: Розпізнавання та базове розуміння**
*   **Вправа "Знайди орудний"**: Дати учням короткий текст (напр., уривок з повідомлення Христини, Source 8) і попросити підкреслити всі слова в орудному відмінку.
*   **Вправа "З'єднай питання і відповідь"**: Створити дві колонки: питання (`Ким?`, `Чим?`, `З ким?`) та відповіді (`лікарем`, `олівцем`, `другом`). Учні мають з'єднати їх.

**Phase 2: Формування та відмінювання**
*   **Трансформаційні drills**: "Я маю ручку. Я пишу... (ручкою)". Дати іменник у називному відмінку, учень має поставити його в орудний.
    *   *Іменники*: Він став (лікар). → Він став лікарем.
    *   *Іменник + прикметник*: Я цікавлюся (українська мова). → Я цікавлюся українською мовою.
    *   *Займенники*: Я піду з (вона). → Я піду з нею.
*   **Fill-in-the-blanks**: `Сестра захоплюється ______ (танці), а я — ______ (футбол)`. (Source 15).

**Phase 3: Активне використання в мовленні**
*   **Побудова речень**: Дати дієслово, що вимагає орудного відмінка (`пишатися`, `цікавитися`, `стати`), і попросити скласти з ним речення про себе. *Приклад: Я пишаюся своєю родиною. Я цікавлюся музикою.*
*   **Ситуативні завдання**: "Уявіть, що ви розповідаєте про свою професію. Скажіть, ким ви працюєте". ("Я працюю..."). "Чим ви зазвичай пишете / їсте суп / малюєте?". ("Я пишу ручкою / їм ложкою / малюю фарбами").
*   **Виправлення помилок**: Дати речення з поширеними помилками (з розділу "Типові помилки L2") і попросити знайти та виправити їх, пояснивши чому. Наприклад: `Я розмовляю на англійській мові.` → `Я розмовляю англійською мовою.`

## Зв'язки з іншими темами

*   **Передумови**:
    *   **Відмінки іменників (§46)**: Учень має розуміти концепцію відмінків та знати питання до них (Source 31).
    *   **Рід та число іменників**: Необхідно для правильного узгодження прикметників.
    *   **І та ІІ відміни іменників**: Основи відмінювання.
*   **Пов'язані теми (вивчаються паралельно або одразу після)**:
    *   **Дієприкметник (§16)**: Орудний відмінок часто використовується для позначення виконавця дії в пасивних дієприкметникових зворотах (`портрет, намальований художником`). (Source 27).
    *   **Прийменники (§30)**: Вивчення прийменників `з`, `із`, `під`, `над`, `перед`, `між`, які вимагають орудного відмінка. (Source 22).
    *   **Особові займенники (§94)**: Відмінювання займенників і особливості вживання приставного `н-` після прийменників. (Source 29).
*   **Що ця тема відкриває**:
    *   Можливість описувати професії, хобі, інструменти.
    *   Побудову складніших речень з пасивними конструкціями.
    *   Більш природне та виразне мовлення, що виходить за межі простих речень "підмет-присудок-додаток".

## Пов'язані статті

*   `grammar/a1/nominative-case`
*   `grammar/a1/noun-gender`
*   `grammar/a2/accusative-case`
*   `grammar/a2/genitive-case`
*   `grammar/a2/locative-case`
*   `grammar/b1/dative-case`
*   `grammar/b1/passive-voice`

---

### Вікі: grammar/a2/instrumental-prepositions.md

# Граматика A2: Над, під, між



## Як це пояснюють у школі (How Schools Teach This)

Прийменники просторового значення, зокрема `над`, `під`, і `між`, вводяться в українській шкільній програмі дуже рано, зазвичай візуально. Вже у 1-2 класах їх ілюструють малюнками для демонстрації розташування предметів, наприклад, "кошеня під клубком" або "кошеня між клубками" (Джерело: `2-klas-ukrmova-bolshakova-2019-2_s0066`). На цьому етапі акцент робиться на інтуїтивному розумінні просторових відношень, а не на граматичних правилах.

Систематичне вивчення цих прийменників як частини мови, що вимагає певного відмінка, починається у середній школі (6-7 клас). У підручниках їх класифікують за будовою (прості, складні) і за значенням (просторові, часові тощо). Наприклад, Заболотний (Джерело: `7-klas-ukrmova-zabolotnyi-2024_s0185`) у 7 класі представляє `над`, `під`, `між` у схемах поруч з іншими прийменниками, що вказують на місце (`біля`, `за`, `перед`).

Ключовий граматичний аспект — вживання цих прийменників з **Орудним відмінком** для позначення статичного місця (`де?`) — закріплюється через вправи на складання словосполучень та опис приміщень. Тема "Моя кімната" є класичним контекстом для практики, де учні описують, що де знаходиться: "Навпроти дверей — умивальник, **над яким** висить кругле дзеркало" (Джерело: `6-klas-ukrmova-betsa-2023_s0054`).

Вживання цих прийменників зі **Знахідним відмінком** для позначення напрямку руху (`куди?`) розглядається пізніше, часто в контексті протиставлення "місце vs. напрямок".

## Повна парадигма (Full Paradigm)

Для позначення **місця** (відповідають на питання `де?`), прийменники `над`, `під`, `між` вимагають **Орудного відмінка (Instrumental Case)**. Це основне вживання на рівні A2.

| Рід (Gender) | Відмінок (Case) | Однина (Singular) | Приклад | Множина (Plural) | Приклад |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Чоловічий** | Орудний | **-ом** (тверда група)<br>**-ем** (м'яка/мішана група) | під стол**ом**<br>над кра**єм** | **-ами** (тверда група)<br>**-ями** (м'яка/мішана група) | під стол**ами**<br>над кра**ями** |
| **Жіночий** | Орудний | **-ою** (тверда група)<br>**-ею** (м'яка/мішана група)<br>**-ею** (на -я) | під книг**ою**<br>над меж**ею**<br>між земл**ею** | **-ами** (тверда група)<br>**-ями** (м'яка/мішана група) | під книг**ами**<br>над меж**ами**<br>між земл**ями** |
| **Середній** | Орудний | **-ом** (тверда група)<br>**-ем** (м'яка/мішана група) | під вікн**ом**<br>над мор**ем** | **-ами** (тверда група)<br>**-ями** (м'яка/мішана група) | під вікн**ами**<br>над мор**ями** |

Для позначення **напрямку** (відповідають на питання `куди?`), ці прийменники вимагають **Знахідного відмінка (Accusative Case)**. Це вживання менш частотне на A2 і зазвичай вивчається пізніше.

| Рід (Gender) | Відмінок (Case) | Однина (Singular) | Приклад | Множина (Plural) | Приклад |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Чоловічий** | Знахідний | (як Називний) | покласти під стіл | (як Називний) | покласти під столи |
| **Жіночий** | Знахідний | **-у**, **-ю** | покласти під книг**у** | (як Називний) | покласти під книги |
| **Середній** | Знахідний | (як Називний) | покласти під вікно | (як Називний) | покласти під вікна |

## Частотність і пріоритети (Frequency & Priorities)

На рівні A2 пріоритетом є впевнене володіння конструкцією **`Прийменник + Орудний відмінок`** для опису статичного розташування предметів. Це одна з базових навичок для опису кімнати, будинку, міста, розташування речей на столі тощо.

1.  **`Під` + Instrumental:** Найвища частотність. Використовується для опису предметів, що знаходяться нижче чогось (`під столом`, `під ліжком`).
2.  **`Над` + Instrumental:** Висока частотність. Використовується для опису предметів, що знаходяться вище чогось, не торкаючись (`над столом`, `над головою`).
3.  **`Між` + Instrumental:** Середня частотність. Вимагає двох або більше об'єктів (`між шафою і столом`). Важливо для опису відношень між предметами.

Вживання зі Знахідним відмінком (`покласти під стіл`) можна відкласти до рівня B1, оскільки на A2 для напрямку частіше використовуються прийменники `в/у` та `на`.

## Типові помилки L2 (Common L2 Errors)

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| Лампа висить *на стіл*. | Лампа висить **над столом**. | Англійське "over the table" може бути неточно перекладене. `На` означає "on" (з контактом), тоді як `над` означає "above" (без контакту). |
| Книга лежить *під стіл*. | Книга лежить **під столом**. | Плутанина між напрямком (`куди?` - Знахідний відмінок) і місцем (`де?` - Орудний відмінок). "Under the table" як місцезнаходження вимагає Орудного відмінка. |
| Я сиджу *між мій друг і моя сестра*. | Я сиджу **між моїм другом і моєю сестрою**. | Після прийменника `між` забувають поставити обидва іменники (та пов'язані з ними займенники/прикметники) в Орудний відмінок. |
| Софія стоїть *між хлопці*. | Софія стоїть **між хлопцями**. | Неправильне утворення Орудного відмінка множини. Замість форми Називного або Родового відмінка множини потрібно використовувати закінчення `-ами/-ями`. |
| *Під час фільм* ми їли попкорн. | **Під час фільму** ми їли попкорн. | Складений прийменник `під час` вимагає Родового відмінка, а не Називного. Це поширена помилка через незнання керування складених прийменників. (Джерело: `7-klas-ukrmova-zabolotnyi-2024_s0185`) |

## Деколонізаційні застереження (Decolonization Notes)

Хоча базове вживання прийменників `над`, `під`, `між` з Орудним відмінком для позначення місця є спільним для української та російської мов, важливо з самого початку привчати учнів до української норми та унікальних конструкцій.

1.  **Складні прийменники:** В українській мові активно використовуються складні прийменники, що пишуться через дефіс, як-от `з-під`, `з-над`, `з-поміж`. Наприклад: `дістати з-під столу`, `виглянути з-над окулярів` (Джерело: `7-klas-ukrmova-litvinova-2024_s0175`). Їх варто вводити як природну частину мови, а не як ускладнення. Російська мова використовує аналогічні конструкції (`из-под`), але їхня частотність та стилістичне забарвлення можуть відрізнятися.
2.  **Фразеологія:** Багато ідіоматичних виразів є унікальними. Наприклад, `бути під каблуком` (to be under someone's thumb) може мати інші відповідники в російській. Акцент має бути на вивченні українських фразеологізмів, а не на пошуку еквівалентів.
3.  **Приклади:** Матеріал для навчання має базуватися виключно на автентичних українських текстах (література, підручники, сучасні медіа). Використання російських прикладів або перекладених з російської речень може призвести до засвоєння неприродних для української мови синтаксичних конструкцій.

## Природні приклади (Natural Examples)

**Група 1: `Під` + Орудний відмінок (місце)**

- Вона цвіла собі **під вікном**. (Джерело: `7-klas-ukrlit-mishhenko-2015_s0338`)
- Підлога **під моїми ногами** злегка вібрувала. (Джерело: `6-klas-ukrlit-avramenko-2023_s0194`)
- Усередині будинок не мав жодного сліду занедбаності. Дощата підлога натерта до блиску й устелена кольоровими килимками, на старовинних меблях – ні пилинки, квіти у вазах, а з кухні смачно пахнуло свіжим печивом і було чути, як посвистує **на плиті** чайник. (Джерело: `7-klas-ukrlit-zabolotnyi-2024_s0366`) - *Примітка: хоча тут `на`, це гарний контекст для протиставлення з `під`.*

**Група 2: `Над` + Орудний відмінок (місце)**

- Навпроти дверей — умивальник, **над яким** висить кругле дзеркало. (Джерело: `6-klas-ukrmova-betsa-2023_s0054`)
- Передній кінець щогли йшов **над водою**, як простягнута з глибини моря рука велетня. (Джерело: `11-klas-ukrajinska-literatura-avramenko-2019_s0117`)
- Бабуся здивовано глянула **з-над окулярів**. (Джерело: `7-klas-ukrmova-litvinova-2024_s0175`)

**Група 3: `Між` + Орудний відмінок (відношення)**

- Посіяли **між гарбузами**. (Джерело: `7-klas-ukrmova-zabolotnyi-2024_s0185`)
- Це історія, що розкриває складну взаємодію сил, що вирішували долю Європи. Також ця історія розповідає про боротьбу **між різними імперіями**. (Джерело: `ext-realna_istoria-128`)
- Кошеня **між** клубками. (Джерело: `2-klas-ukrmova-bolshakova-2019-2_s0066`)

**Група 4: Складені прийменники (часове значення)**

- Зустрітися **під час відпочинку**. (Джерело: `7-klas-ukrmova-zabolotnyi-2024_s0185`)
- При виступі у сенаті він подумки повторював свій шлях по домівці і міг виголосити всю промову, не користуючись записами. (Джерело: `11-klas-ukrajinska-mova-voron-2019_s0067`) - *Контекст для `під час`*
- Ми будемо дивитись документальний фільм про революцію про Євромайдан. (Джерело: `ext-ulp_youtube-246`) - *Контекст для опису дій `під час` події*.

## Рекомендації для вправ (Activity Concepts)

-   **Phase 1 (Розпізнавання та імітація):**
    -   **Вправа "Де кошеня?":** Показати картинки з предметом у різних позиціях (над, під, між, за, перед коробкою) і попросити студентів повторити за вчителем/аудіо: "Кошеня під коробкою", "Кошеня над коробкою". (Базується на підході з Джерела `2-klas-ukrmova-bolshakova-2019-2_s0066`).
    -   **Matching:** З'єднати речення з малюнками, що їх ілюструють.

-   **Phase 2 (Контрольована практика):**
    -   **Заповнення пропусків:** Дати речення з пропущеним прийменником. *Стіл стоїть \_\_\_ вікном і дверима.* (між)
    -   **Трансформація (Відмінки):** Дати іменник у Називному відмінку і попросити поставити його в правильну форму. *Картина висить над (ліжко) -> над ліжком.*
    -   **Вибір з двох варіантів:** *Килим лежить (на/під) підлогою?* Ні, *на підлозі*. *Взуття стоїть (під/в) ліжком?* -> *під ліжком*. Це допомагає розрізняти `на` (on) і `під` (under).

-   **Phase 3 (Вільна практика):**
    -   **Опис кімнати:** Дати студенту картинку кімнати (як у темі "Моя кімната", Джерело: `ext-ulp_youtube-261`) і попросити усно чи письмово описати розташування 5-7 предметів, використовуючи `над`, `під`, `між`.
    -   **"Що у вас на столі?":** Попросити студентів описати їхній реальний робочий стіл. *"Мій телефон лежить під зошитом, а лампа стоїть над столом."*
    -   **Питання-відповіді:** Студенти в парах ставлять один одному питання "Де...?" про предмети в класній кімнаті або на зображенні.

## Зв'язки з іншими темами

-   **Орудний відмінок (Instrumental Case):** Є абсолютною передумовою. Студенти повинні знати, як утворювати форми Орудного відмінка іменників та займенників, перш ніж вивчати ці прийменники для позначення місця.
-   **Прийменники місця:** Ця тема є частиною більшого блоку про просторові прийменники, що включає `в/у`, `на`, `за`, `перед`, `біля`, `поруч`.
-   **Лексика "Дім" та "Кімната":** Найприродніший контекст для введення та практики цих прийменників.
-   **Знахідний відмінок з рухом (Accusative of Motion):** У майбутньому ця тема буде контрастувати з сьогоднішньою. `Стілець стоїть **під столом**` (де? - Орудний) vs. `Я ставлю стілець **під стіл**` (куди? - Знахідний).

## Пов'язані статті

-   `grammar-a1-instrumental-case`
-   `grammar-a2-prepositions-of-location`
-   `grammar-b1-accusative-case-motion`
-   `vocab-a2-my-room`
</wiki_context>

## Plan References

- 
- 
- 

</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Частина 1: Розпізнавання та форми (Part 1: Recognition and Forms)` (~400 words)
- `## Частина 2: Вибір та застосування (Part 2: Choice and Application)` (~500 words)
- `## Частина 3: Вільне вживання (Part 3: Free Production)` (~600 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 1500 words minimum.

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
  1. **Describing a perfect picnic — everything with instrumental: Поїхали автобусом (m). Гуляли з дітьми (pl). Їли бутерброди з ковбасою (f). Сиділи під деревом (n). Цей день був найкращим!**
     Speakers: Друзі (згадуючи)
     Why: All instrumental: автобусом, з дітьми, з ковбасою, під деревом

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

**Required:** орудний відмінок (instrumental case), вправа (exercise), контрольна точка (checkpoint), завдання (task), речення (sentence), відповідь (answer), текст (text), перевірка (check, test)
**Recommended:** правильний (correct), словосполучення (phrase, word combination), описати (to describe), визначити (to identify, to determine)

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
## Частина 1: Розпізнавання та форми (400 words total)
- P1 (60 words): [Introduction to the Instrumental Checkpoint. Reviewing the core questions "ким? чим?" and summarizing the five primary functions learned in A2.4: tool/means, accompaniment, profession, spatial location, and temporal expressions.]
- P2 (120 words): [Morphology Review: Nouns of I and II declensions. Explaining the hard/soft/mixed stem rules for endings -ою/-ею/-єю and -ом/-ем/-єм. Specific examples: сестрою (f), землею (f), мрією (f); столом (m), морeм (n), краєм (m).]
- P3 (100 words): [Morphology Review: III and IV declensions. Focusing on phonetic changes: doubling of consonants (сіллю, ніччю), the use of apostrophe (кров'ю, матір'ю), and the parallel forms of neuter nouns (ім'ям vs. іменем).]
- P4 (120 words): [Agreement Review: Adjectives and Pronouns. Reviewing the masculine/neuter -им and feminine -ою endings for adjectives, and the special forms for personal pronouns (мною, тобою, ним, нею, нами, вами, ними) with the mandatory "н-" after prepositions.]
- <!-- INJECT_ACTIVITY: quiz-instrumental-mixed --> [quiz, Mixed Instrumental case quiz covering all functions from M21-M26, 8 items]

## Частина 2: Вибір та застосування (550 words total)
- P1 (160 words): [Deep dive into spatial prepositions: над (above), під (under), між (between). Explaining the static location logic (питання "де?") which requires the Instrumental case. Examples: дзеркало над умивальником, кішка під столом, прохід між шафою і ліжком.]
- P2 (120 words): [The "З" Distinction: Accompaniment vs. Tool. Clarifying the most common L2 error — using "з" for tools. Contrasting natural pairs: "пишу ручкою" (tool) vs. "гуляю з ручкою" (accompaniment/absurd context) to highlight the rule.]
- P3 (120 words): [Verbs of State and Profession. Reviewing the use of Instrumental with "бути" (future/past), "стати", and "працювати". Examples: він буде архітектором, вона стала менеджеркою, я працюю перекладачем.]
- P4 (150 words): [Verbs of Interest and Pride. Reviewing the non-prepositional Instrumental required by "цікавитися", "займатися", and "пишатися". Specific examples: цікавлюся історією, займаюся спортом, пишаюся братом.]
- <!-- INJECT_ACTIVITY: fill-in-instrumental-transform --> [fill-in, Sentence transformation — put noun phrases into Instrumental with correct agreement, 8 items]
- <!-- INJECT_ACTIVITY: group-sort-functions --> [group-sort, Sort Instrumental sentences by function (tool, companion, profession, spatial, temporal), 8 items]

## Частина 3: Вільне вживання (700 words total)
- P1 (120 words): [Dialogue: "Спогади про пікнік". A natural conversation between friends using dense Instrumental constructions: "їхали автобусом", "гуляли з дітьми", "їли канапки з сиром", "сиділи під старою липою".]
- P2 (130 words): [Linguistic Hygiene: Decolonizing Instrumental Usage. Addressing common Russianisms: "розмовляти українською мовою" (not "на мові"), "сумувати за тобою" (not "по тобі"), and "сміятися з когось" (Genitive review contrast vs. Instrumental error "над").]
- P3 (150 words): [Visual Analysis: The Kitchen Scene. Providing a narrative description of a picture where various actions occur: someone cuts bread "гострим ножем", a bowl sits "між вікнами", and a towel hangs "під раковиною". Preparing the learner for Exercise 9.]
- P4 (150 words): [Composition Strategy: My Daily Routine. Step-by-step instructions on how to integrate Instrumental into a personal text. Suggesting sentence starters: "Я працюю...", "Я добираюся на роботу...", "Ввечері я займаюся...".]
- P5 (150 words): [Sample Narrative: "Мій вівторок". A model 10-sentence paragraph demonstrating the goal of Exercise 10, using 6+ different Instrumental functions in a cohesive story about a professional's day.]
- <!-- INJECT_ACTIVITY: error-correction-instrumental --> [error-correction, Find and correct grammar errors in sentences covering module topics, 6 items]

## Підсумок (150 words)
- P1 (150 words): [Recap of the module. Check your progress: 1) Can you form feminine endings with -ою/-ею? 2) Do you remember to use 'н-' with 'з ним/нею'? 3) Can you describe your profession? 4) Do you use 'з' only for company, not for tools? Provide a bulleted self-check Q&A list.]

Grand total: ~1800 words
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
