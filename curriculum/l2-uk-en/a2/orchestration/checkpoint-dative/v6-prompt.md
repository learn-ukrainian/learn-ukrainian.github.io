

---

## Your Writing Identity

**You are: Lead Ukrainian Instructor.** Your persona is *The Conversation Partner*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **23: Контрольна робота — давальний відмінок** (A2, A2.3 [Dative Case]).

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
module: a2-023
level: A2
sequence: 23
slug: checkpoint-dative
version: '1.1'
title: Контрольна робота — давальний відмінок
subtitle: Перевірка засвоєння давального відмінка (М15-М19)
focus: review
pedagogy: Review
phase: A2.3 [Dative Case]
word_target: 1500
objectives:
- Learner can produce all dative pronoun forms and use them in impersonal constructions (М15 recall).
- Learner can form dative noun endings for all genders with correct consonant alternations (М16 recall).
- Learner can build fully agreeing dative noun phrases with adjectives and possessives (М17 recall).
- Learner can use dative-governing verbs, подобатися, and age constructions correctly in context (М18
  recall).
dialogue_situations:
- setting: 'Secret Santa at the office — matching gifts to people: Що подарувати Олексієві (m)? Книгу!
    А Наталці (f)? Шоколад! Новому колезі (m) — чашку (f, cup). Шефу (m) — вино.'
  speakers:
  - Організатор
  - Колеги
  motivation: 'Dative consolidation: Олексієві, Наталці, колезі, шефу'
content_outline:
- section: 'Частина 1: Розпізнавання (Part 1: Recognition)'
  words: 400
  points:
  - Identify dative forms in context — distinguish dative from genitive, accusative, and locative case
    forms.
  - Recognize impersonal dative constructions (мені холодно) vs. nominative subject sentences (я замерзла).
  - Match dative pronoun forms to their nominative counterparts.
  - Identify the dative experiencer in подобатися sentences.
- section: 'Частина 2: Вибір форми (Part 2: Choosing the Correct Form)'
  words: 500
  points:
  - Choose correct dative noun endings across all genders — masculine -ові/-у, feminine -і with alternations,
    neuter -у/-ю.
  - Select correct dative adjective and possessive pronoun forms (-ому/-ій/-им).
  - Choose between dative and accusative case based on the verb (допомагати кому vs. бачити кого).
  - Fill in correct forms in post office and service dialogues from М19.
- section: 'Частина 3: Продукування (Part 3: Production)'
  words: 400
  points:
  - Write complete sentences using dative-governing verbs with correct noun/pronoun forms.
  - Produce подобатися sentences with correct experiencer (Dat.) and subject (Nom.) agreement.
  - Express age using dative construction with correct number agreement.
  - Write a short address or greeting using full dative noun phrases (possessive + adjective + noun).
- section: Огляд помилок та порівняння відмінків (Error Review and Case Comparison)
  words: 200
  points:
  - Common dative errors and how to avoid them — mixing -ому/-ій, forgetting consonant alternations, wrong
    case after дякувати/допомагати.
  - Summary comparison chart of Nominative, Genitive, Dative endings for nouns, adjectives, and pronouns.
  - Self-assessment checklist for dative case mastery.
vocabulary_hints:
  required:
  - давальний відмінок (dative case)
  - допомагати (to help)
  - дякувати (to thank)
  - подобатися (to be pleasing to, to like)
  - подарувати (to give as a gift)
  - надіслати (to send)
  - потрібно (necessary, needed)
  - холодно (cold (impersonal state))
  recommended:
  - закінчення (ending (grammar))
  - чергування (alternation (grammar))
  - узгодження (agreement (grammar))
activity_hints:
- type: quiz
  focus: Identify the dative form among case options (recognition — Part 1 material)
  items: 8
- type: fill-in
  focus: Complete sentences with correct dative noun/adjective/pronoun endings (Part 2 material)
  items: 8
- type: match-up
  focus: Match dative-governing verbs to correct case forms and sentence completions
  items: 8
- type: error-correction
  focus: Find and correct grammar errors in sentences covering module topics
  items: 6
references:
- title: Заболотний Grade 10, §157
  notes: Complete dative case reference — noun endings, parallel forms, style rules
- title: Захарійчук Grade 4, §281
  notes: Pronoun declension tables including all dative forms
- title: Кравцова Grade 4, §135
  notes: Dative vs. Locative distinction exercises — common checkpoint test pattern

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
- Confirmed: давальний, відмінок, допомагати, дякувати, подобатися, подарувати, надіслати, потрібно, холодно, закінчення, чергування, узгодження
- Not found: (none)

## Grammar Rules
- [Чергування приголосних у давальному відмінку]: Правопис §12 — Чергування Г, К, Х із м’якими З, Ц, С. У давальному відмінку однини іменників жіночого роду першої відміни: дуга́ — дузі́, кві́тка — кві́тці, сва́ха — сва́сі.

## Calque Warnings
- дякувати: OK
- допомагати: OK
- мені холодно: OK

## CEFR Check
- допомагати: A1 — OK
- дякувати: A1 — OK
- подобатися: A1 — OK
- подарувати: A1 — OK
- надіслати: A2 — OK
- холодно: A1 — OK
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
# Knowledge Packet: Контрольна робота — давальний відмінок
**Module:** checkpoint-dative | **Track:** A2

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: grammar/a2/checkpoint-dative.md

# Граматика A2: Контрольна робота — давальний відмінок



## Як це пояснюють у школі (How Schools Teach This)
В українській шкільній програмі давальний відмінок (`Д. в.`) вводиться як один із семи відмінків іменника (Source 4, 19, 33). Його ключова функція пояснюється через питання **`кому?`** і **`чому?`** (Source 4, 19, 22). Назва "давальний" походить від дієслова `давати`, що підкреслює його основну роль: позначення отримувача дії (адресата) (Source 7, 9).

Навчальний процес виглядає так:
1.  **Ідентифікація через питання:** Учні вчаться ставити питання `кому? чому?` для визначення давального відмінка. (Source 4, 22). Наприклад, у фразі `Ми дали білочці горішки` питання ставиться так: дали (кому?) білочці (Source 9).
2.  **Основна функція (адресат):** Пояснюється, що давальний відмінок називає особу чи предмет, на користь яких відбувається дія (Source 9, 34). Приклади зазвичай включають дієслова `давати`, `дарувати`, `допомагати`, `радити` (Source 7).
3.  **Безособові конструкції:** Давальний відмінок вводиться у конструкціях, що виражають стан, потребу або думку, як-от `мені подобається`, `тобі варто`, `мені треба`, `мені здається` (Source 7). Це одна з перших тем, де учні стикаються з давальним відмінком, часто ще до формального вивчення відмінків, через уживані фрази.
4.  **Розрізнення з місцевим відмінком:** Оскільки іменники в давальному та місцевому відмінках можуть мати однакові закінчення (наприклад, `у книзі` (М.в.) vs `(дати) книзі` (Д.в.)), підручники приділяють увагу їх розрізненню (Source 9, 31, 34). Ключові відмінності:
    *   **Питання:** Давальний — `кому? чому?`; Місцевий — `(на/у) кому? (на/у) чому?` (Source 9, 31).
    *   **Значення:** Давальний — адресат дії; Місцевий — місце дії (Source 9, 34).
    *   **Прийменники:** Давальний *зазвичай* вживається без прийменників, тоді як місцевий — *завжди* з прийменниками (Source 9, 22).

## Повна парадигма (Full Paradigm)

### Іменники (Nouns)

#### І відміна (Feminine, Masculine & Common gender nouns ending in -а, -я)
(Source 17, 31)

| Група | Рід | Однина (Singular) | Множина (Plural) | Приклади |
| :--- | :--- | :--- | :--- | :--- |
| **Тверда** | Жіночий | **-і** (після `г, к, х` → `з, ц, с`) | **-ам** | `ріка → ріці`, `дорога → дорозі`, `рука → руці` |
| | Чоловічий/Спільний | **-і** (після `г, к, х` → `з, ц, с`) | **-ам** | `сирота → сироті`, `Микола → Миколі` |
| **М'яка** | Жіночий | **-і** / **-ї** | **-ям** | `земля → землі`, `пісня → пісні`, `мрія → мрії` |
| | Чоловічий/Спільний | **-і** / **-ї** | **-ям** | `Ілля → Іллі`, `суддя → судді` |
| **Мішана** | Жіночий | **-і** | **-ам** | `вежа → вежі`, `тиша → тиші` |

**Ключове правило чергування:** В іменниках І відміни твердої групи в давальному відмінку однини відбувається чергування приголосних `[г], [к], [х]` на `[з'], [ц'], [с']` перед закінченням `-і` (Source 17, 31).

#### ІІ відміна (Masculine nouns with zero ending & Neuter nouns ending in -о, -е, -я)

| Група | Рід | Однина (Singular) | Множина (Plural) | Приклади |
| :--- | :--- | :--- | :--- | :--- |
| **Тверда** | Чоловічий | **-ові, -у** (паралельні) | **-ам** | `батько → батькові/батьку`, `директор → директорові/директору` |
| | Середній | **-у** | **-ам** | `село → селу`, `місто → містові/місту` (Source 13) |
| **М'яка** | Чоловічий | **-еві, -ю** / **-єві, -ю** (паралельні) | **-ям** | `учитель → учителеві/учителю`, `Андрій → Андрієві/Андрію` |
| | Середній | **-ю** / **-яті** | **-ям** | `море → морю`, `обличчя → обличчю`, `теля → теляті` |
| **Мішана** | Чоловічий | **-еві, -у** (паралельні) | **-ам** | `товариш → товаришеві/товаришу` |
| | Середній | **-у** | **-ам** | `плече → плечу` |

**Правило уникнення одноманітності:** Щоб уникнути повторення, рекомендується чергувати паралельні закінчення `-ові, -еві` та `-у, -ю`. Наприклад: `панові директору`, `другові Василю` (Source 13).

### Займенники (Pronouns)
(Source 7)

| Називний (Nominative) | Давальний (Dative) |
| :--- | :--- |
| я | **мені** |
| ти | **тобі** |
| він, воно | **йому** |
| вона | **їй** |
| ми | **нам** |
| ви | **вам** |
| вони | **їм** |

## Частотність і пріоритети (Frequency & Priorities)

1.  **Найвища частотність (must-know for A2):**
    *   **Особові займенники:** `мені, тобі, йому, їй, нам, вам, їм`. Вони є основою для вираження особистих станів і потреб.
    *   **Конструкції стану/потреби:** `мені подобається`, `мені треба`, `мені здається`, `тобі варто` (Source 7). Це комунікативне ядро.
    *   **Дієслово `давати`:** Як випливає з назви відмінка, конструкції з `давати` (і синонімами `дарувати`, `передавати`) є базовими. Наприклад: `Дай мені...` (Source 7).

2.  **Середня частотність (core grammar for A2):**
    *   **Іменники-адресати:** Використання іменників (особливо назв людей) у ролі непрямого додатка з дієсловами мовлення, допомоги, поради (`казати комусь`, `допомагати комусь`, `радити комусь`).
    *   **Чергування `г/к/х` → `з/ц/с`:** Це правило є високочастотним для іменників жіночого роду (`подрузі`, `мамі`, `сестрі`).
    *   **Паралельні форми чоловічого роду (`-ові/-у`):** Учні повинні розпізнавати обидві форми як правильні, але на рівні А2 достатньо активно володіти однією (наприклад, `-у`).

3.  **Низька частотність (B1+ topics):**
    *   Відмінювання складних числівників у давальному відмінку.
    *   Рідкісні іменники та винятки з відмінювання.
    *   Використання з прийменниками (`назустріч`, `всупереч`).

## Типові помилки L2 (Common L2 Errors)

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| `Дякую **вас**` | `Дякую **вам**` | Прямий переклад з російської `благодарю вас` (Accusative). В українській мові дієслово `дякувати` вимагає давального відмінка `(кому?)` (Source 21, 32). |
| `Я телефоную своїй **подругі**` | `Я телефоную своїй **подрузі**` | Відсутність чергування приголосних `г` → `з'` перед закінченням `-і` в іменниках жіночого роду І відміни. Це обов'язкове правило (Source 31, 36). |
| `Він дав подарунок **Ігора**` | `Він дав подарунок **Ігорю / Ігореві**` | Плутанина між знахідним (`кого?`) і давальним (`кому?`) відмінками. Англійська мова не має відмінків для непрямих додатків ("gave Igor"), що призводить до помилок. |
| `Це пам'ятник **Шевченка**` | `Це пам'ятник **Шевченкові / Шевченку**` | Неправильне вживання родового відмінка замість давального для позначення особи, якій щось присвячено. (Source 32). |
| `На **білочці** руда шубка.`<br>`Дали **білочці** горішки.`<br/>(Учень не бачить різниці) | `на білочці` (Місцевий)<br/>`дали білочці` (Давальний) | Плутанина між давальним і місцевим відмінками через однакові закінчення. Треба розрізняти за питанням (`де?` vs `кому?`) та наявністю прийменника (місцевий завжди з прийменником) (Source 9, 34). |
| `Я наслідую **татові**` | `Я наслідую **тата**` | Неправильне керування дієслова. В українській мові `наслідувати` вимагає знахідного відмінка `(кого?)`, на відміну від російського `подражать (кому?)`, що вимагає давального. (Source 32). |

## Деколонізаційні застереження (Decolonization Notes)

1.  **Давальний відмінок не є "російським з варіаціями"**: Українська система відмінків розвивалася самостійно. Пояснювати українські форми через їхню схожість чи відмінність від російських — це колоніальний підхід. Українська граматика є самодостатньою і має вивчатися на власних прикладах. (Джерело: Загальний принцип, підтверджений фокусом джерел на укр. мові).

2.  **Керування дієслів — ключова відмінність**: Багато дієслів в українській та російській мовах, що виглядають схоже, вимагають різних відмінків. Це часте джерело суржику.
    *   `Дякувати` + **Давальний відмінок** (`дякую тобі`) vs рос. `благодарить` + *знахідний* (`благодарю тебя`).
    *   `Наслідувати` + **Знахідний відмінок** (`наслідувати когось`) vs рос. `подражать` + *давальний* (`подражать кому-то`). (Source 32)
    *   `Зрадити` + **Знахідний відмінок** (щодо країни: `зрадити Батьківщину`) vs рос. `изменить` + *давальний* (`изменить Родине`). (Source 32).

3.  **Паралельні форми — риса української мови**: Наявність паралельних закінчень у давальному відмінку чоловічого роду (`-ові, -еві, -єві` та `-у, -ю`) є характерною рисою сучасної української мови, що надає їй гнучкості та милозвучності. (Source 13, 20). Це не "додатковий" чи "застарілий" варіант, а повноцінна норма.

4.  **Фонетичні відмінності**: Закінчення `-їй` для жіночого роду (`вона` → `їй`) є фонетично відмінним від російського `ей`. На це варто звертати увагу при навчанні вимови.

## Природні приклади (Natural Examples)

**Група 1: Вираження стану, потреби, думки (з особовими займенниками)**
*   `Мені подобається лінво.` (Source 7) — I like Lingvo.
*   `Мені здається, що планшет — це просто великий смартфон.` (Source 7) — It seems to me that a tablet is just a big smartphone.
*   `Тобі варто встановити додаток на телефон.` (Source 7) — You should install an app on your phone.
*   `Ой, а мені треба купити новий ноутбук.` (Source 7) — Oh, and I need to buy a new laptop.

**Група 2: Адресат дії (отримувач)**
*   `Ми дали білочці горішки.` (Source 9) — We gave the squirrel some nuts.
*   `Мені сестра подарувала [планшет] на день народження.` (Source 7) — My sister gave me [a tablet] for my birthday.
*   `Дай мені свій номер телефону.` (Source 7) — Give me your phone number.

**Група 3: Іменники жіночого роду з чергуванням `г/к/х`**
*   `Ґрунт дає дереву поживні речовини.` <!-- VERIFY: 'дереву' - це середній рід, але приклад хороший для 'дає' -->
*   `Я телефоную своїй подрузі.` (Adapted from Source 31) — I am calling my friend (female).
*   `Подякував своїй сестрі.` (Source 21) — He thanked his sister.

**Група 4: Іменники чоловічого роду (паралельні форми)**
*   `Це пам'ятник Франкові.` (Source 32) — This is a monument to Franko.
*   `Допомогти учителю Назару Федоровичу.` (Source 13) — To help the teacher Nazar Fedorovych.
*   `Все Давальний повручає, лиш кому? чому? спитає.` (Source 4) — The Dative gives everything away, it only asks 'to whom? to what?'.

## Рекомендації для вправ (Activity Concepts)

*   **Phase 1: Розпізнавання та базові фрази**
    *   **Drill 1 (Matching):** З'єднайте займенники в називному відмінку з їх формами в давальному (`я` → `мені`).
    *   **Drill 2 (Fill-in-the-blanks):** Заповніть пропуски у фразах `___ подобається...`, `___ треба...`, `___ здається...` правильним займенником (`мені`, `тобі`, `йому` і т.д.).
    *   **Drill 3 (Sentence Completion):** Доповніть речення: `Дай ... сік.` (мені, йому, їй).

*   **Phase 2: Продукція з іменниками**
    *   **Drill 4 (Transformation):** Перетворіть речення, додавши адресата. `Я даю книгу. (друг)` → `Я даю книгу другові/другу.`
    *   **Drill 5 (Targeted Practice):** Поставте іменники в дужках у давальний відмінок, фокусуючись на чергуванні `г/к/х`. `Я допомагаю (подруга)`. `Він пише лист (мама)`.
    *   **Drill 6 (Choice):** Оберіть правильну форму дієслова/відмінка. `Дякую (вам/вас)`. `Наслідую (тата/татові)`.

*   **Phase 3: Розрізнення та вільна практика**
    *   **Drill 7 (Dative vs. Locative):** Визначте відмінок виділеного слова. `Я гуляю по (вулиця).` `Я йду по (вулиця) додому.` `Я дарую квіти (мама).`
    *   **Drill 8 (Question-Answer):** Дайте відповіді на питання, використовуючи давальний відмінок. `Кому ти допомагаєш?` → `Я допомагаю...`. `Кому ти дзвониш?` → `Я дзвоню...`.
    *   **Drill 9 (Creative Writing):** Напишіть короткий текст про те, що ви подарували своїм друзям на свята, використовуючи давальний відмінок.

## Зв'язки з іншими темами
*   **Попередні теми:** `cases-overview`, `personal-pronouns`, `noun-gender`, `accusative-case`. Розуміння концепції відмінків та базове відмінювання є обов'язковим.
*   **Наступні теми:** `locative-case` (для порівняння), `verb-government` (розширення списку дієслів, що вимагають давального відмінка), `modal-verbs`. Опанування давальним відмінком є ключем до побудови складніших речень, де є більше одного додатка.

## Пов'язані статті
*   `grammar/a1/cases-overview`
*   `grammar/a1/personal-pronouns`
*   `grammar/a2/locative-case`
*   `grammar/b1/verb-government`

---

### Вікі: grammar/a2/checkpoint-genitive.md

# Граматика A2: Контрольна робота — родовий відмінок



## Як це пояснюють у школі (How Schools Teach This)
Родовий відмінок (Genitive case) в українській шкільній програмі вводиться поступово, починаючи з початкових класів. Його основне питання — **кого? чого?** (Source 23: `4-klas-ukrayinska-mova-kravtsova-2021-1_s0040`).

Основні функції, що вивчаються:
1.  **Позначення відсутності:** Конструкція з `немає` (there is no / there are no). Це одна з перших функцій, яку засвоюють учні. Наприклад: `немає (кого?) брата`, `немає (чого?) молока`. (Source 23)
2.  **Позначення належності (Possession):** Відповідає на питання "чий?". Наприклад, `щоденник (кого?) дочки`, `твори (кого?) Шевченка`. (Source 9: `11-klas-ukrajinska-mova-avramenko-2019_s0258`). У цій ролі родовий відмінок часто конкурує з більш природними для розмовної мови присвійними прикметниками (`доччин щоденник`, `Тарасова гора`), але є обов'язковим у діловому мовленні або при переліченні (`майно Федченка`, `твори Шевченка, Франка, Лесі Українки`). (Source 9)
3.  **Керування дієсловами:** Низка дієслів вимагає після себе додатка в родовому відмінку, а не в знахідному. Підручники для середньої школи (Source 6: `8-klas-ukrmova-zabolotnyi-2025_s0049`) наводять списки таких дієслів:
    *   `потребувати (чого?) допомоги`
    *   `навчатися (чого?) музики`
    *   `зазнати (чого?) лиха`
    *   `дотримати (чого?) обіцянки`
    *   `завдати (чого?) шкоди`
4.  **Вживання з числівниками:** Це ключова тема. Історично числівники від 5 до 10 були іменниками, що вимагали родового відмінка множини (Source 4: `ext-other_blogs-67`, `пѧть братъ`). Ця норма збереглася: після числівників `п'ять` і більше іменник ставиться в родовому відмінку множини. Наприклад: `п'ять столів`, `десять книжок`.
5.  **Вживання з прийменниками:** Родовий відмінок використовується з багатьма прийменниками, такими як `без`, `для`, `до`, `з`, `від`, `біля`, `крім`, `замість`, `серед`. (Source 21: `7-klas-ukrmova-zabolotnyi-2024_s0185`).

## Повна парадигма (Full Paradigm)
Родовий відмінок є одним із найскладніших через варіативність закінчень, особливо в II відміні та в множині.

### Іменники (Nouns)

#### І відміна (Feminine, Masculine, Common gender in -а/-я)
(Source 19: `ext-other_blogs-46`)

| Група | Рід | Однина (кого? чого?) | Множина (кого? чого?) | Приклади |
| :--- | :--- | :--- | :--- | :--- |
| Тверда | жін./чол. | `-и` | `-ø` | `ріки`, `сироти` (G.Sg) / `рік`, `сиріт` (G.Pl) |
| М'яка | жін./чол. | `-і` / `-ї` | `-ь` / `-й` | `землі`, `мрії` (G.Sg) / `земель`, `мрій` (G.Pl) |
| Мішана | жін./чол. | `-і` | `-ø` | `вежі`, `кручі` (G.Sg) / `веж`, `круч` (G.Pl) |

**Особливості родового відмінка множини І відміни:**
*   **Вставні голосні `о`, `е`:** `думка → дум**о**к`, `земля → зем**е**ль` (Source 19).
*   **Закінчення `-ей`:** `стаття → стат**ей**`, `сім'я → сім**ей**`, `свиня → свин**ей**` (Source 19).
*   **Закінчення `-ів`:** `сусіда → сусід**ів**`, `староста → старост**ів**` (також `старост`), `баба → баб**ів**` (також `баб`) (Source 19).

#### II відміна (Masculine with zero-ending/`-о`, Neuter in -о/-е/-я)

| Рід | Однина (кого? чого?) | Множина (кого? чого?) | Приклади |
| :--- | :--- | :--- | :--- |
| Чол. (істоти) | `-а`, `-я` | `-ів`, `-їв` | `брата`, `учителя` / `братів`, `учителів` |
| Чол. (неістоти) | **`-а`/`-я` АБО `-у`/`-ю`** | `-ів`, `-їв`, `-ø` | `стола`, `трамвая` / `саду`, `краю` → `столів`, `трамваїв`, `садів`, `країв` |
| Середній | `-а`, `-я` | `-ø` | `села`, `моря` / `сіл`, `морів` (рідко) |

**Ключова складність II відміни:** вибір закінчення **-а(-я)** чи **-у(-ю)** в родовому відмінку однини для неістот чоловічого роду. Правила складні й мають багато винятків, але загальна тенденція:
*   **-а, -я:** для конкретних, чітко окреслених понять (назви міст, річок з наголосом на закінченні, терміни, предмети): `Києва`, `Дніпра`, `атома`, `документа`, `вівторка`.
*   **-у, -ю:** для абстрактних понять, збірних, речовин, явищ природи, установ: `миру`, `прогресу`, `піску`, `вітру`, `університету`, `інституту`. <!-- VERIFY -->

#### III відміна (Feminine with zero-ending + *мати*)
(Source 30: `6-klas-ukrmova-zabolotnyi-2020_s0111`)

| Однина (кого? чого?) | Множина (кого? чого?) | Приклади |
| :--- | :--- | :--- |
| `-і` / `-и` | `-ей` | `ночі`, `любові` (`любови`), `радості` (`радости`) / `ночей`, `подорожей` |
| *виняток* | *виняток* | `матері` / `матерів` |

#### IV відміна (Neuter in -а/-я, що позначає молодих істот)
(Source 19: `ext-other_blogs-46`)

| Однина (кого? чого?) | Множина (кого? чого?) | Приклади |
| :--- | :--- | :--- |
| `-ят-и`, `-ен-і` | `-ят`, `-ен` | `теляти`, `імені` / `телят`, `імен` |

### Прикметники та присвійні займенники (Adjectives and Possessives)
Відмінюються за родами і числами, узгоджуючись з іменником.
(Source 24: `7-klas-ukrmova-avramenko-2024_s0115`, Source 27: `6-klas-ukrmova-zabolotnyi-2020_s0210`)

| Рід / Число | Закінчення | Приклади |
| :--- | :--- | :--- |
| Чоловічий одн. | `-ого` | `нового`, `мого`, `синього` |
| Жіночий одн. | `-ої`, `-еї` | `нової`, `моєї`, `синьої` |
| Середній одн. | `-ого` | `нового`, `мого`, `синього` |
| Множина | `-их` | `нових`, `моїх`, `синіх` |

## Частотність і пріоритети (Frequency & Priorities)
Для рівня A2/B1 пріоритетним є засвоєння найбільш уживаних функцій родового відмінка:

1.  **Найвища частотність:**
    *   **Заперечення/відсутність з `нема(є)`:** `У мене немає часу`, `В магазині немає хліба`. Це фундаментальна конструкція.
    *   **Кількість з числами 5+:** `п'ять друзів`, `сто гривень`, `багато людей`. Це обов'язково для будь-яких розмов про кількість.
    *   **Прийменники `для`, `до`, `з`, `без`:** `кава без цукру`, `подарунок для мами`, `я йду до університету`, `сік з яблук`.

2.  **Середня частотність (важливо для розширення мовлення):**
    *   **Проста належність:** `колір неба`, `центр міста`, `ім'я мого брата`.
    *   **Дати:** для позначення місяця в даті: `перше (чого?) січня`, `восьме (чого?) березня`.
    *   **Керування поширеними дієсловами:** `чекати (чого?) автобуса`, `боятися (кого?) собак`, `шукати (чого?) роботу`.

3.  **Нижча частотність (для B1 і вище):**
    *   Тонкощі вибору закінчень `-а`/`-у` в чоловічому роді. На рівні А2 достатньо вивчити найчастотніші слова як лексичні одиниці.
    *   Рідкісні форми родового відмінка множини.
    *   Складні випадки керування (e.g. `запобігти (чому?) нещастю` (Dative) vs `уникнути (чого?) нещастя` (Genitive)).

## Типові помилки L2 (Common L2 Errors)
Англомовні студенти часто припускаються помилок через відсутність відмінків в англійській мові та інтерференцію.

| ❌ Помилково (Incorrectly) | ✅ Правильно (Correctly) | Чому (Why) |
| :--- | :--- | :--- |
| *Я потребую допомогу.* | *Я потребую **допомоги**.* | Дієслово `потребувати` вимагає родового, а не знахідного відмінка. Це пряма калька з англійського "I need help" (verb + direct object). (Source 6) |
| *Я купив п'ять книга.* | *Я купив п'ять **книжок**.* | Після числівників від 5 і вище іменник має стояти в родовому відмінку множини. Помилка виникає через застосування правила для чисел 2-4. (Source 4) |
| *У мене немає сестра.* | *У мене немає **сестри**.* | Конструкція заперечення `немає` завжди вимагає родового відмінка. Студенти часто залишають іменник у називному відмінку. (Source 23) |
| *Я йду в магазин.* | *Я йду **до** магазин**у**.* | Хоча `в/у` + Accusative використовується для напрямку, з дієсловами руху прийменник `до` + Genitive є більш поширеним і часто єдиним правильним варіантом для позначення кінцевої точки маршруту. |
| *Це машина мій брат.* | *Це машина **мого брата**.* | Для позначення належності використовується родовий відмінок, а не просто два іменники поруч, як іноді буває в англійській ("my brother's car" where "'s" is a particle, not a case ending reflected in the noun itself). |
| *Не було рук**и́**.* (наголос на `и`) | *Не було р**у́**ки.* (наголос на `у`) | У деяких іменниках при зміні відмінка чи числа відбувається зміна наголосу. `Руки́` (N. pl.) vs `ру́ки` (G. sg.). Це треба запам'ятовувати. (Source 2: `ext-ulp_youtube-29`) |

## Деколонізаційні застереження (Decolonization Notes)
Українська граматика має власну логіку розвитку, відмінну від російської. Навчання через порівняння з російською є хибною колоніальною практикою.

1.  **Закінчення `-а`/`-я` vs. `-у`/`-ю` в Родовому відмінку чоловічого роду:** Це одна з найскладніших тем в українській мові, і правила тут **не збігаються** з російськими. Наприклад, в українській мові назви міст переважно мають закінчення `-а`: `Києва`, `Лондона`, `Харкова`. У російській мові для багатьох з них нормою є `-а`: `Киева`, але для деяких `-у`: `Лондону`. Навчання "за аналогією" до російської призведе до системних помилок.
2.  **Керування дієслів:** Дієслово `чекати` (to wait) в українській мові традиційно вимагає родового відмінка (`чекати листа`, `чекати автобуса`). У сучасній мові під впливом російської поширився і знахідний відмінок, але родовий залишається стилістично вищим і класичним. У російській мові `ждать` вимагає знахідного (`ждать письмо`) або родового (при конкретизації чи запереченні).
3.  **Фонетичні відмінності в закінченнях:** Українські закінчення є результатом природного розвитку праслов'янської мови на українських землях. Наприклад, у родовому відмінку множини часто з'являються вставні `о`, `е` (`жінок`, `пісень`), що є органічною рисою української фонетики (Source 19). Російська мова має свої власні рефлекси (пор. `жен`, `песен`).
4.  **Історична тяглість:** Український родовий відмінок зберігає риси, що походять ще з давньоукраїнської (давньоруської) мови, зокрема вживання з числівниками (Source 4). Це не запозичення і не "варіант", а прямий спадок мовної еволюції.
5.  **Прийменник `до`:** Вживання прийменника `до` + Genitive для позначення напрямку руху (`їхати до Києва`) є питомою українською рисою, на відміну від російського `в` + Accusative (`ехать в Киев`).

## Природні приклади (Natural Examples)

**1. Вираження відсутності (Absence)**
*   У мене немає **часу** на це. (I don't have time for this.)
*   Сьогодні в магазині не було свіжого **хліба**. (There was no fresh bread in the store today.)
*   Без **тебе** тут сумно. (It's sad here without you.)

**2. Вираження належності (Possession)**
*   Це номер **мого телефону**. (This is my phone number.)
*   Я читаю книжку **Андрія Куркова**. (I'm reading a book by Andriy Kurkov.)
*   На столі лежить зошит **моєї сестри**. (My sister's notebook is on the table.) (Source 9, adapted)

**3. Кількість (Quantity & Numerals)**
*   Тут працює п'ять **людей**. (Five people work here.)
*   Я купив два **кілограми** яблук. (I bought two kilograms of apples.)
*   Багато **літ** перевернулось, води чимало утекло. (Source 13: `8-klas-ukrmova-avramenko-2025_s0065`)

**4. Керування дієсловами та прийменниками (Verb & Prepositional Government)**
*   Вона потребує **допомоги**. (She needs help.) (Source 6)
*   Я вчуся **української мови**. (I am learning the Ukrainian language.) (Source 6, adapted)
*   Ми приїхали з **Львова**. (We came from Lviv.)
*   Це подарунок для **тата**. (This is a gift for dad.)

## Рекомендації для вправ (Activity Concepts)

*   **Phase 1 (Recognition & Simple Production):**
    *   **Drill 1 (Absence):** Трансформація. Студент перетворює стверджувальне речення на заперечне.
        *   *Input:* `У мене є собака.` → *Output:* `У мене немає собаки.`
        *   *Input:* `Тут є кава.` → *Output:* `Тут немає кави.`
    *   **Drill 2 (Possession):** Складання словосполучень.
        *   *Input:* `книжка / мій брат` → *Output:* `книжка мого брата`
        *   *Input:* `машина / директор` → *Output:* `машина директора`

*   **Phase 2 (Numerals & Plurals):**
    *   **Drill 3 (Counting):** Студент рахує предмети на картинці, використовуючи правильну форму іменника.
        *   *Prompt:* Скільки тут столів? (картинка з 6 столами) → *Response:* `Шість столів.`
        *   *Prompt:* Скільки тут яблук? (картинка з 3 яблуками) → *Response:* `Три яблука.` (для контрасту)

*   **Phase 3 (Complex Sentences & Verb Government):**
    *   **Drill 4 (Fill-in-the-blanks):** Студент заповнює пропуски правильною формою слова в дужках.
        *   *Prompt:* `Я хочу побажати тобі ______ (щастя).` → *Response:* `щастя`.
        *   *Prompt:* `Вона боїться ______ (темрява).` → *Response:* `темряви`.
    *   **Drill 5 (Sentence unscramble):** Студент складає речення з набору слів, ставлячи іменники в правильному відмінку.
        *   *Input:* `немає / у / мене / вільний / час` → *Output:* `У мене немає вільного часу.`

## Зв'язки з іншими темами (Connections)

*   **Попередні теми (Prerequisites):**
    *   [[grammar/a1/introduction-to-nouns|Вступ до іменників]]: поняття роду (чоловічий, жіночий, середній).
    *   [[grammar/a1/nominative-case|Називний відмінок]]: базова форма слова.
    *   [[grammar/a2/numbers-1-100|Числівники 1-100]]: знання самих числівників, перед тим як вчити їхнє керування.

*   **Наступні теми (What this enables):**
    *   [[grammar/b1/cases-prepositions|Відмінки та прийменники]]: Родовий є базою для вивчення складніших прийменникових конструкцій.
    *   [[grammar/b1/verbs-of-motion|Дієслова руху]]: Конструкції напрямку `до` + Genitive, `з` + Genitive.
    *   [[grammar/b1/participles-adjectival|Дієприкметники]]: Дієприкметники узгоджуються з іменниками в роді, числі та відмінку, отже, вимагають знання родового відмінка для правильного вживання (`немає прочитаної книги`). (Source 24)

## Пов'язані статті (Related Articles)
*   [[grammar/a1/introduction-to-cases]]
*   [[grammar/a2/accusative-case]]
*   [[grammar/a2/dative-case]]
*   [[grammar/b1/genitive-masculine-ending-choice]]
*   [[grammar/b1/numbers-advanced]]
</wiki_context>

## Plan References

- 
- 
- 

</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this **exact** order:

- `## Частина 1: Розпізнавання (Part 1: Recognition)` (~400 words)
- `## Частина 2: Вибір форми (Part 2: Choosing the Correct Form)` (~500 words)
- `## Частина 3: Продукування (Part 3: Production)` (~400 words)
- `## Огляд помилок та порівняння відмінків (Error Review and Case Comparison)` (~200 words)
- `## Підсумок` (~150 words)

**Hard rule (#1189):** Every heading above MUST appear in your output **verbatim** as an `## H2` line. This includes the FINAL summary/transition section (`Підсумок: ...`, `Підсумок та перехід до M...`, etc.) — the writer's most common failure is silently dropping the closing section. Do NOT skip it. Do NOT renumber. Do NOT merge headings. The post-write quick-verify check will fail your build if any heading is missing, even if the prose itself is excellent.

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

### FORBIDDEN WORDS — never write these (#1189)

The following Russian words have leaked into past builds and broken modules. They are **hard-banned** — the post-write toxic-token scanner will fail your build the moment it sees one. Use the Ukrainian alternative every time, even in dialogues, even in casual prose, even when quoting a learner's mistake (use a `<!-- VERIFY -->` placeholder instead of typing the Russian form):

| Russian (FORBIDDEN) | Ukrainian (USE THIS) |
|---|---|
| хорошо | добре |
| конечно | звичайно / певна річ |
| спасибо | дякую |
| пожалуйста | будь ласка / прошу |
| ничего | нічого |
| сейчас | зараз |
| тоже | теж / також |
| здесь | тут |
| кот | кіт |
| кон | кін |

This list is enforced word-for-word by `scripts/build/quick_verify.py` (SEVERE_RUSSIANISMS). If you produce any of these tokens — even inside a quoted example, even inside a dialogue line spoken by a Russian-speaking character — the build halts immediately. There is no exception.

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
  1. **Secret Santa at the office — matching gifts to people: Що подарувати Олексієві (m)? Книгу! А Наталці (f)? Шоколад! Новому колезі (m) — чашку (f, cup). Шефу (m) — вино.**
     Speakers: Організатор, Колеги
     Why: Dative consolidation: Олексієві, Наталці, колезі, шефу

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

**Required:** давальний відмінок (dative case), допомагати (to help), дякувати (to thank), подобатися (to be pleasing to, to like), подарувати (to give as a gift), надіслати (to send), потрібно (necessary, needed), холодно (cold (impersonal state))
**Recommended:** закінчення (ending (grammar)), чергування (alternation (grammar)), узгодження (agreement (grammar))

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
## Частина 1: Розпізнавання (~450 words)
- P1 (~120 words): Introduce the context with the "Secret Santa" dialogue. Speakers: Організатор and Колеги. Dialogue: "Що подарувати Олексієві? Книгу! А Наталці? Шоколад! Новому колезі — чашку. Шефу — вино." Set the module's focus: recognizing the Dative case (давальний відмінок) and understanding its core function as the recipient or addressee of an action.
- P2 (~110 words): Explain how to identify the Dative case using the questions `кому?` and `чому?`. Contrast it strictly with the Locative case (which answers `на/у кому? на/у чому?` and always uses prepositions) and the Genitive case. Use the contrast example: `дали білочці горішки` (Dative) vs. `руда шубка на білочці` (Locative).
- P3 (~110 words): Review impersonal dative constructions. Contrast a Dative state (e.g., `мені холодно`, `мені потрібно`, `мені здається`) with a Nominative active subject (`я замерзла`, `я хочу`). Map the Dative personal pronouns to their Nominative counterparts (`я` → `мені`, `ти` → `тобі`, `він/воно` → `йому`, `вона` → `їй`, `ми` → `нам`, `ви` → `вам`, `вони` → `їм`).
- P4 (~110 words): Review the verb `подобатися`. Explain the syntax inversion: the person who likes something is the *experiencer* in the Dative case (`мені`), and the object being liked is the grammatical subject in the Nominative case. Use the example: `Мені подобається планшет` and `Їй подобаються квіти`.
- <!-- INJECT_ACTIVITY: quiz-dative-recognition --> [quiz, Identify the dative form among case options (recognition — Part 1 material), 8 items]

## Частина 2: Вибір форми (~550 words)
- P1 (~110 words): Review Dative noun endings for Masculine and Neuter genders. Highlight the masculine parallel forms (`-ові/-еві/-єві` vs. `-у/-ю`) explaining that both are correct but `-ові/-еві` is distinctively Ukrainian. Examples: `батькові/батьку`, `учителеві/учителю`, `Андрієві/Андрію`. Show Neuter endings (`-у/-ю`): `селу`, `морю`. 
- P2 (~120 words): Review Dative noun endings for Feminine nouns (`-і`). Heavily emphasize the mandatory consonant alternations (`г` → `з'`, `к` → `ц'`, `х` → `с'`) before the `-і` ending in the hard group. Provide concrete examples: `подруга` → `подрузі`, `ріка` → `ріці`, `муха` → `мусі`.
- P3 (~110 words): Review adjective and possessive pronoun agreement in the Dative case. Break down the endings: Masculine/Neuter take `-ому` (`моєму новому колезі`), Feminine takes `-ій` (`моїй старшій сестрі`), and Plural takes `-им` (`нашим друзям`). 
- P4 (~110 words): Contrast verb government: Dative vs. Accusative. Explain that English speakers often use direct objects (Accusative) where Ukrainian requires an indirect object (Dative). Contrast `допомагати мамі` (Dat) with `бачити маму` (Acc). List high-frequency Dative verbs: `давати, дарувати, допомагати, дякувати, радити`.
- P5 (~100 words): Provide a short communicative application via a post office / service dialogue (recalling M19). Example context: A clerk asks "Кому ви хочете надіслати пакунок?" and the customer replies "Своєму братові в Київ." Demonstrate the full noun phrase agreement working together in a natural scenario.
- <!-- INJECT_ACTIVITY: fill-in-dative-endings --> [fill-in, Complete sentences with correct dative noun/adjective/pronoun endings, 8 items]
- <!-- INJECT_ACTIVITY: match-up-dative-verbs --> [match-up, Match dative-governing verbs to correct case forms and sentence completions, 8 items]

## Частина 3: Продукування (~450 words)
- P1 (~110 words): Guide the learner on building complete sentences with Dative-governing verbs. Emphasize the natural word order: Subject + Verb + Dative Recipient + Accusative Object. Provide examples of giving/sending: `Я дарую своєму другові цікаву книгу.` `Ми надіслали бабусі лист.`
- P2 (~120 words): Detail the production of complex `подобатися` sentences with full noun phrases. Show how the verb must agree in number (singular/plural) with the Nominative subject, while the experiencer phrase remains entirely in the Dative. Example: `Моєму старшому братові подобаються нові автомобілі.`
- P3 (~110 words): Review how to express age. Remind learners that Ukrainian uses the Dative case for the person + the number of years. Provide examples mixing pronouns and noun phrases: `Скільки років вашій сестрі?` `Моєму синові десять років.`
- P4 (~110 words): Explain how to write short addresses or formal greetings using full Dative noun phrases. Show examples like `Шановному пану директору` or `Дорогій Олені`. Explicitly warn against using the Genitive case for dedications (e.g., correct: `пам'ятник Шевченкові`, incorrect: `пам'ятник Шевченка`).

## Огляд помилок та порівняння відмінків (~220 words)
- P1 (~90 words): Review common Dative errors. Highlight the mixing of adjective endings (e.g., incorrectly saying `моєму сестрі` instead of `моїй сестрі`), forgetting the `г/к/х` alternation (`подругі` ❌ → `подрузі` ✅), and the direct translation trap with `дякувати` (`Дякую вас` ❌ → `Дякую вам` ✅).
- P2 (~80 words): Present a summary comparison chart formatting Nominative, Genitive, and Dative endings for a full phrase. Example progression: `мій новий дім` (Nom) → `мого нового дому` (Gen) → `моєму новому дому` (Dat), and `моя старша сестра` (Nom) → `моєї старшої сестри` (Gen) → `моїй старшій сестрі` (Dat).
- <!-- INJECT_ACTIVITY: error-correction-dative --> [error-correction, Find and correct grammar errors in sentences covering module topics, 6 items]
- P3 (~50 words): Provide a self-assessment checklist as a bulleted Q&A list.
  * Чи можете ви утворити давальний відмінок від свого імені?
  * Чи знаєте ви, як сказати про свій вік та вік друзів?
  * Чи пам'ятаєте ви три дієслова, які завжди вимагають давального відмінка?

Grand total: ~1670 words
</skeleton>

## Output Format

Write in Markdown. Use:
- `## Section Title` for main sections
- `### Subsection` for subsections within a section
- `**bold**` for Ukrainian words being taught. For **A1 and A2** levels, provide an English translation on first use (e.g. `**стіл** (table)`) because learners lack the vocabulary to infer meaning. For **B1 and above**, do NOT provide inline translations for standard vocabulary — the learner will use the module's словник (vocabulary table). You may provide ONE parenthetical English translation ONLY for highly abstract grammar/linguistic terms on first use (e.g. `**видова пара** (aspectual pair)`).
- Tables for paradigms (conjugation, declension)
- `:::tip` / `:::caution` / `:::note` for callout boxes
- `<!-- INJECT_ACTIVITY: {id} -->` for exercise placement (markers only — do NOT write exercise content)

Do NOT write MDX component syntax, JSON, or DSL exercise blocks (:::quiz, etc.). Plain Markdown with injection markers.

---

## MANDATORY FINAL CHECKLIST (#1189)

Before you finish writing, verify the prose against this checklist. Failing any item will fail the build.

### Section headings (verbatim)

Every heading from "Section Structure" above MUST appear as an `## H2` in your output, in order, **including the closing `Підсумок:` / `Підсумок та перехід до M...` summary**. The single most common writer failure across the B1 build has been silently dropping the final summary section. Re-read your output before stopping. If the last section in the plan is missing, write it now.

### Required vocabulary (every word must appear)

You MUST use **every word** from the list below at least once in the prose, in a natural sentence with bold + English translation. Abstract grammatical metalanguage (видова пара, дієвідміна, особове закінчення, прагматика, діагностика, дієвідмінювання, зворотний, двовидовий, одновидовий, неозначено-кількісний, etc.) is the most frequently dropped category — actively find homes for those words even if it means adding a sentence that defines them.

- [ ] давальний відмінок (dative case)
- [ ] допомагати (to help)
- [ ] дякувати (to thank)
- [ ] подобатися (to be pleasing to, to like)
- [ ] подарувати (to give as a gift)
- [ ] надіслати (to send)
- [ ] потрібно (necessary, needed)
- [ ] холодно (cold (impersonal state))

### Forbidden words (never produce)

Do not write any of these even once. Even in dialogues. Even in quoted examples. Even when illustrating a learner's mistake (use `<!-- VERIFY -->` instead). The post-write toxic-token scanner will fail the build immediately:

❌ хорошо ❌ конечно ❌ спасибо ❌ пожалуйста ❌ ничего ❌ сейчас ❌ тоже ❌ здесь ❌ кот ❌ кон

Use: добре · звичайно · дякую · будь ласка · нічого · зараз · теж · тут · кіт · кін

### Level-specific immersion check

The level-appropriate immersion rule was already injected at the top of
this prompt as `IMMERSION RULE`. Re-read it now BEFORE you stop writing.
If your level's rule contains a CHECKLIST block, walk through every item.
If it doesn't, just verify your output matches the LANGUAGE ROLES and
TARGET stated in that block.

This used to hard-code a B1+ checklist that confused A1/A2 models (where
translation blockquotes are REQUIRED at A1 and ALLOWED at A2-early).
The single source of truth is now
`scripts/pipeline/config_tables.py:IMMERSION_RULES`.

---

Begin writing now. Start with the first section heading.
