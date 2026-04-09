

---

## Your Writing Identity

**You are: Lead Ukrainian Instructor.** Your persona is *The Conversation Partner*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **68: Пробний іспит** (A2, A2.10 [Refinement and Graduation]).

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

1. **IMMERSION TARGET: 70-90% Ukrainian — near-full immersion. English only in vocabulary tab.** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if immersion is outside this range. For A1 early modules, the learner cannot read Cyrillic — English must dominate. For A2+, Ukrainian must carry a significant share — add Ukrainian Reading Practice blocks, dialogues, and example paragraphs to reach the target. Too little Ukrainian fails audit just as much as too much.
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
module: a2-068
level: A2
sequence: 68
slug: a2-practice-exam
version: '1.0'
title: Пробний іспит
subtitle: Тренувальний тест рівня A2 з читання, письма та граматики
focus: review
pedagogy: Review
phase: A2.10 [Refinement and Graduation]
word_target: 1500
objectives:
- Learner can complete a timed reading comprehension section, answering questions about everyday Ukrainian
  texts.
- Learner can demonstrate grammar accuracy across all A2 topics in a structured test format.
- Learner can produce a short written response (80-100 words) on a familiar topic using correct grammar
  and vocabulary.
- Learner can self-assess readiness for B1 based on exam performance.
dialogue_situations:
- setting: 'Mock oral exam — examiner asks situational questions: Розкажіть про свій день. Що ви робили
    вчора? Які плани на літо? Порівняйте Київ і ваше місто. Опишіть свою сім''ю.'
  speakers:
  - Екзаменатор
  - Кандидат
  motivation: Full A2 oral exam simulation — all tenses, cases, vocabulary
content_outline:
- section: 'Частина 1: Читання (Part 1: Reading)'
  words: 450
  points:
  - 'Text A: a short informational text (advertisement, schedule, or announcement — 80-100 words) with
    3-4 comprehension questions. Tests scanning for specific information.'
  - 'Text B: a personal message or email (100-120 words) where a Ukrainian friend describes their plans,
    asks questions, shares news. 4-5 comprehension questions requiring understanding of detail and inference.'
  - 'Text C: a short narrative or blog post (120-150 words) about a Ukrainian tradition or travel experience.
    4-5 questions testing main idea, vocabulary in context, and drawing conclusions.'
- section: 'Частина 2: Граматика (Part 2: Grammar)'
  words: 400
  points:
  - 'Section A: Case selection (6 items) — choose the correct case form in sentences with various triggers
    (verbs, prepositions, quantity words).'
  - 'Section B: Verb form (6 items) — select the correct tense, aspect, or mood for the context.'
  - 'Section C: Mixed grammar (6 items) — comparatives, pronouns (свій, себе, indefinite/negative), conjunctions,
    numeral agreement.'
- section: 'Частина 3: Спілкування та письмо (Part 3: Communication and Writing)'
  words: 350
  points:
  - 'Task A: Dialogue completion — fill in 6 blanks in a natural conversation (at a cafe, on the phone,
    planning a trip).'
  - 'Task B: Guided writing — write a short text (80-100 words) on one of three topics: (1) Describe your
    favorite season and why, (2) Write to a Ukrainian friend about your weekend plans, (3) Describe a
    holiday tradition you like.'
  - 'Scoring rubric: grammar accuracy (cases, aspect, agreement), vocabulary range, coherence, task completion.'
- section: Результати та самооцінка (Results and Self-Assessment)
  words: 300
  points:
  - Answer key with explanations for each grammar and reading question. Why each answer is correct — teaching
    through the test itself.
  - 'Self-assessment grid: Strong / Developing / Needs Work for each A2 skill area (cases, aspect, comparison,
    complex sentences, vocabulary, reading, writing).'
  - 'Recommendations: which modules to revisit before starting B1. Encouragement: passing 70% means ready
    for B1.'
vocabulary_hints:
  required:
  - іспит (exam)
  - завдання (task, exercise)
  - відповідь (answer)
  - питання (question)
  - читання (reading)
  - письмо (writing)
  - граматика (grammar)
  - результат (result)
  recommended:
  - самооцінка (self-assessment)
  - оцінка (grade, assessment)
  - правильний (correct)
activity_hints:
- type: quiz
  focus: Simulated exam — mixed grammar questions (cases, aspect, comparison)
  items: 8
- type: fill-in
  focus: Reading comprehension — answer questions about a Ukrainian text
  items: 8
- type: true-false
  focus: Grammar accuracy check — identify correct vs incorrect sentences
  items: 8
- type: error-correction
  focus: Find and correct grammar errors in sentences covering module topics
  items: 6
references:
- title: CEFR A2 Descriptor — Can-do statements
  notes: Aligned to CEFR A2 reading, writing, and grammar competencies
- title: Заболотний Grade 6, Контрольна робота
  notes: Ukrainian school test format for grammar and reading sections

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
- Confirmed: іспит, завдання, відповідь, питання, читання, письмо, граматика, результат, самооцінка, оцінка, правильний.
- Not found: none.

## Grammar Rules
- Відмінювання іменників: Правопис §60–100 — детальні правила відмінювання іменників за відмінами (I, II, III, IV) та групами (тверда, м'яка, мішана).
- Узгодження числівника: Правопис §106–107 — числівники *два, три, чотири* узгоджуються з іменниками у формі називного відмінка множини (три озера, чотири вагони); числівники від *п’яти* і більше — у формі родового відмінка множини (п’ять озер, сім результатів).
- Суфікси іменників: Правопис §32 — віддієслівні іменники на *-ння* (читання, питання) пишуться з подвоєнням "н".

## Calque Warnings
- складати іспит: OK — правильна форма для процесу тестування (avoid "здавати іспит" as a Russianism).
- правильна відповідь: OK — "вірний" означає "відданий/лояльний", тому для результатів іспиту вживаємо "правильний".
- запитання: OK — для конкретного звернення за інформацією в тестах краще вживати "запитання" або "завдання" замість широкого "питання".

## CEFR Check
- іспит: A2 — OK.
- завдання: A1 — OK.
- відповідь: A1 — OK.
- результат: A2 — OK.
- оцінка: A2 — OK.
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
# Knowledge Packet: Пробний іспит
**Module:** a2-practice-exam | **Track:** A2

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: grammar/a2/a2-practice-exam.md

# Граматика A2: Пробний іспит



## Як це пояснюють у школі (How Schools Teach & Assess This)

Пробний іспит наприкінці рівня А2 є комплексним інструментом оцінювання, що перевіряє не ізольовані граматичні знання, а загальну комунікативну компетентність учня. Українська шкільна система, як і сучасні європейські методики, оцінює володіння мовою через чотири основні види мовленнєвої діяльності: **аудіювання, читання, говоріння та письмо** (Джерело: 5-klas-ukrmova-avramenko-2022_s0009, 6-klas-ukrmova-zabolotnyi-2020_s0228).

На відміну від простого тесту з граматики, пробний іспит симулює реальні життєві ситуації спілкування. Оцінювання відбувається за 12-бальною шкалою, де вищі бали (10-12) відповідають високому рівню володіння (Джерело: ext-ulp_youtube-60).

Ключові принципи шкільного оцінювання, які мають бути відображені в іспиті:
1.  **Інтегрованість:** Завдання поєднують кілька навичок. Наприклад, учень слухає текст (аудіювання), а потім письмово відповідає на запитання (письмо).
2.  **Контекстуальність:** Граматика перевіряється не в відриві від контексту, а через завдання на розуміння текстів, написання власних висловлювань та аналіз ситуацій спілкування (Джерело: 6-klas-ukrmova-zabolotnyi-2020_s0228).
3.  **Продуктивність:** Перевага надається завданням, що вимагають від учня самостійно конструювати відповідь, а не просто вибирати з варіантів. Дослідники підтверджують, що "ефективніші тести — це ті, коли вам треба самим написати або сказати відповідь, а не вибирати варіант" (Джерело: ext-ulp_youtube-90).

## Ключові граматичні теми для тестування (Key Grammar Topics for Testing)

Іспит рівня А2 має перевіряти впевнене володіння наступними темами:

1.  **Фонетика і Орфографія:**
    *   **Наголос:** Розуміння ролі вільного і рухомого наголосу. Здатність розрізняти слова-омографи, значення яких залежить від наголосу (напр. `орган` (музичний інструмент) vs. `орган` (частина організму); `ніколи` (never) vs. `ніколи` (no time)). Знання слів з подвійним наголосом (`алфавіт`/`алфавіт`, `помилка`/`помилка`) (Джерело: ext-ulp_youtube-29).
    *   **Вживання м'якого знака (`ь`):** Правильне написання для пом'якшення приголосних та в дієслівних закінченнях (Джерело: 5-klas-ukrmova-avramenko-2022_s0131).

2.  **Іменник:**
    *   **Рід, число, відмінок:** Узгодження з іншими частинами мови.
    *   **Істоти/Неістоти:** Правильна постановка питання `хто?` чи `що?` та відповідна форма знахідного відмінка (Джерело: 3-klas-ukrainska-mova-kravtsova-2020-1_s0053).
    *   **Шість основних відмінків:** Впевнене використання іменників з найуживанішими прийменниками у знахідному, родовому, давальному, орудному та місцевому відмінках. Кличний відмінок для звертань.

3.  **Прикметник:**
    *   Узгодження з іменником за родом, числом і відмінком.
    *   Створення простих описів предметів та людей (Джерело: 5-klas-ukrmova-avramenko-2022_s0022).

4.  **Числівник:**
    *   Кількісні числівники (відповідають на питання `скільки?`) для позначення віку, часу, кількості предметів (Джерело: 3-klas-ukrainska-mova-ponomarova-2020-1_s0102).
    *   Узгодження числівників 1-4 з іменниками.

5.  **Займенник:**
    *   Правильне використання особових, присвійних, вказівних займенників.
    *   Розуміння потенційної двозначності при неправильному вживанні ("Дмитрик попрохав друга покласти зошит у свій портфель. (У чий портфель?)") (Джерело: 10-klas-ukrmova-karaman-2018_s0298).

6.  **Дієслово:**
    *   **Часи:** Теперішній (I та II дієвідміни), минулий (узгодження за родом та числом) та майбутній (проста і складена форми).
    *   **Особливі дієслова:** Відмінювання дієслів `бути`, `їсти`, `дати` та похідних від `-вісти` (`розповісти`, `відповісти`) є обов'язковим для перевірки (Джерело: 7-klas-ukrmova-avramenko-2024_s0084).
    *   **Наказовий спосіб** для простих команд та прохань.

## Частотність і пріоритети (Frequency & Priorities)

Іспит має зосереджуватися на найбільш функціональних та частотних аспектах граматики.

*   **Найвищий пріоритет:**
    1.  **Відмінки іменників з прийменниками:** Родовий (для позначення відсутності, власності), місцевий (для позначення місця) та знахідний (для позначення прямого об'єкта) є найважливішими для базового спілкування.
    2.  **Минулий час дієслів:** Узгодження за родом (`він сказав`, `вона сказала`, `воно сказало`) та числом (`вони сказали`) — критично важлива навичка.
    3.  **Відмінювання дієслів `бути` та `дати`:** Ці дієслова є основою для безлічі конструкцій.
*   **Середній пріоритет:**
    1.  **Теперішній час дієслів:** Розрізнення I та II дієвідмін.
    2.  **Наголос:** Перевірка знання наголосу в 10-15 найбільш уживаних словах з рухомим або подвійним наголосом (напр., `книжки`, `завжди`, `помилка`, `також`).
    3.  **Прикметники:** Узгодження в називному та знахідному відмінках.
*   **Нижчий пріоритет (але бажано включити):**
    1.  Складніші випадки відмінювання числівників.
    2.  Давальний та орудний відмінки у менш частотних конструкціях.

## Типові помилки L2 (Common L2 Errors)

Іспит має містити завдання, що виявляють типові помилки, зокрема ті, що виникають під впливом російської мови.

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| **здавати** іспит | **складати** іспит | Калька з російського "сдавать экзамен". В українській мові використовується дієслово `складати`. (Джерела: 5-klas-ukrmova-avramenko-2022_s0131, 6-klas-ukrmova-avramenko-2023_s0026, 7-klas-ukrmova-avramenko-2024_s0084, 6-klas-ukrmova-avramenko-2023_s0078) |
| **вірна** відповідь | **правильна** відповідь | `Вірний` означає "loyal, faithful" (вірний друг). Для правильності використовується `правильний`. Калька з рос. "верный ответ". (Джерело: 6-klas-ukrmova-avramenko-2023_s0026) |
| **приймати** участь | **брати** участь | `Приймати` щось можна (подарунок), але участь `беруть`. Калька з рос. "принимать участие". (Джерело: 6-klas-ukrmova-avramenko-2023_s0026) |
| **учбовий** процес | **навчальний** процес | `Учбовий` — це суржикізм. Літературна норма — `навчальний`. (Джерела: 5-klas-ukrmova-avramenko-2022_s0131, 6-klas-ukrmova-avramenko-2023_s0078) |
| Говорити **на** українській мові | Говорити **українською** мовою | Вплив англійської ("speak **in** a language") або російської (" говорить **на** русском"). В українській мові для позначення мови мовлення використовується орудний відмінок. <!-- VERIFY --> |
| Я вибачаю**сь** | **Вибачте** / **Перепрошую** | Зворотна частка `-ся` означає дію, спрямовану на себе. "Я вибачаюсь" буквально означає "я пробачаю себе". Для вибачення перед іншими використовуються незворотні форми. <!-- VERIFY --> |

## Деколонізаційні застереження (Decolonization Notes)

**Це обов'язковий розділ.** Пробний іспит має активно утверджувати українські мовні норми та уникати пасток, пов'язаних з російським мовним впливом.

1.  **Пріоритет на унікальних українських формах:** Іспит повинен свідомо тестувати явища, що відрізняють українську від російської. Це стосується наголосу (`донька`, а не `дочка`), лексики (`складати іспит`), кличного відмінка.
2.  **Суржик як індикатор помилки:** Завдання на виправлення помилок мають включати типові русизми (`вірна відповідь`, `приймати участь`). Це не просто помилки, а маркери недостатнього занурення в українське мовне середовище.
3.  **Жодних порівнянь з російською:** В інструкціях та формулюваннях завдань слід уникати будь-яких згадок чи порівнянь з російською мовою. Українська мова є самодостатньою системою і має вивчатися як така.
4.  **Тестування лексичних "фальшивих друзів":** Завдання можуть включати слова, що мають різне значення в українській та російській мовах (напр., `неділя` — "Sunday" в українській, "week" в російській; `луна` — "echo" в українській, "moon" в російській).

## Природні приклади (Natural Examples as Test Items)

Замість абстрактних вправ, іспит має використовувати природні, контекстуалізовані завдання.

**1. Аудіювання + Тест (модель з Джерела `5-klas-ukrmova-uhor-2022-1_s0013`)**
*   *Інструкція:* Прослухайте короткий аудіофрагмент (напр., з подкасту "Ukrainian Lessons", Source 1) і оберіть правильну відповідь.
*   *Приклад запитання:* Що, за словами автора, завдає багато клопоту тим, хто вивчає українську мову?
    *   А) Дієслова
    *   Б) Наголос
    *   В) Відмінки

**2. Заповнення пропусків (модель з Джерела `ext-ulp_youtube-90`)**
*   *Інструкція:* Поставте дієслово в дужках у правильну форму минулого часу.
    *   Я не знав, що вона вже \_\_\_\_\_\_\_\_\_\_ (прийти).
    *   Вони \_\_\_\_\_\_\_\_\_\_ (бути) в центрі міста вчора.
    *   Моя сестра ніколи не \_\_\_\_\_\_\_\_\_\_ (їсти) цей суп. (Джерело: 7-klas-ukrmova-avramenko-2024_s0084)

**3. Виправлення помилок (модель з Джерела `6-klas-ukrmova-avramenko-2023_s0026`)**
*   *Інструкція:* Знайдіть і виправте помилку в реченні.
    *   *Речення з помилкою:* "Мій брат буде здавати іспит з історії наступного тижня."
    *   *Очікувана відповідь:* "Мій брат буде **складати** іспит з історії наступного тижня."

**4. Коротка письмова відповідь / Есе (модель з Джерела `6-klas-ukrmova-golub-2023_s0120`)**
*   *Інструкція:* Напишіть 5-7 речень на одну з тем:
    *   "Опишіть ваше рідне місто." (перевірка прикметників, місцевого відмінка)
    *   "Розкажіть, як ви вивчаєте українську мову." (перевірка дієслів, орудного відмінка)

## Рекомендації для вправ (Activity Concepts / Exam Format)

Іспит має бути поділений на логічні блоки, що відповідають мовленнєвим навичкам.

*   **Частина 1: Рецептивні навички (Аудіювання та Читання) - 40% оцінки**
    *   **Аудіювання:** Прослухати 1-2 коротких (1-1.5 хв) аудіозаписи (діалог, монолог) і виконати 5-7 завдань з вибором відповіді (multiple choice) для перевірки загального розуміння. (Джерело: 5-klas-ukrmova-avramenko-2022_s0010)
    *   **Читання:** Прочитати 1-2 коротких тексти (150-200 слів) і виконати завдання на розуміння (multiple choice, true/false, matching). (Джерело: 6-klas-ukrmova-zabolotnyi-2020_s0225)

*   **Частина 2: Граматика та Лексика в контексті - 30% оцінки**
    *   **Fill-in-the-blanks:** 10-12 речень з пропусками для перевірки відмінювання дієслів, відмінків іменників, узгодження прикметників. (Джерело: ext-ulp_youtube-90)
    *   **Error Correction:** 5-7 речень, що містять типові помилки L2 (особливо русизми), які потрібно знайти та виправити. (Джерело: 6-klas-ukrmova-avramenko-2023_s0026)

*   **Частина 3: Продуктивні навички (Письмо) - 30% оцінки**
    *   **Коротке есе/опис:** Написати зв'язний текст обсягом 60-80 слів на задану знайому тему (напр., "Моя сім'я", "Мій день", "Подорож, що запам'яталася"). Оцінюється граматична правильність, лексичне багатство та зв'язність тексту. (Джерело: 6-klas-ukrmova-golub-2023_s0120)

## Зв'язки з іншими темами (Connections)

*   **Передумови (A1):** Іспит передбачає, що учень вже володіє кирилицею, знає базові поняття роду іменників, вміє відмінювати найпростіші дієслова в теперішньому часі та будувати прості речення.
*   **Наступні кроки (B1):** Успішне складання іспиту А2 підтверджує готовність учня до вивчення складніших тем рівня В1, таких як доконаний та недоконаний види дієслова, дієслова руху з префіксами, дієприкметники та дієприслівники, а також складніші синтаксичні конструкції.

## Пов'язані статті (Related Articles)

*   `grammar/a2/a2-nouns-cases-overview`
*   `grammar/a2/a2-verbs-past-tense`
*   `grammar/a2/a2-verbs-conjugation`
*   `phonetics/ukrainian-stress`
*   `decolonization/common-russianisms`

---

### Вікі: grammar/a2/all-cases-practice.md

# Граматика A2: Все разом



## Як це пояснюють у школі (How Schools Teach This)

На рівні A2 відбувається не стільки вивчення нових граматичних тем, скільки активна практика та консолідація раніше засвоєних знань. Шкільні підручники для молодших класів фокусуються на практичному застосуванні граматики через діяльність.

1.  **Зв'язок дієслова з іменником:** Основа розуміння відмінків закладається через питання. Наприклад, у підручнику Пономарьової (3 клас) учням пропонують ставити питання від дієслова до залежних іменників, щоб визначити їхню роль у реченні: `Стоїть (що?) місто; стоїть (де?) на берегах` (Source 7). Цей підхід допомагає інтуїтивно зрозуміти потребу у відмінкових закінченнях.

2.  **Часи дієслів (Tenses):** Повторення минулого та майбутнього часу є ключовим. У діалогах для вивчення мови, як у Ukrainian Lessons Podcast, постійно використовуються приклади для закріплення. Наприклад, розрізнення чоловічого (`робив`), жіночого (`робила`) та множини (`робили`) у минулому часі, а також складена форма майбутнього часу (`буду робити`, `будеш робити`) (Source 5).

3.  **Особові займенники у непрямих відмінках:** Акцент робиться на вживанні займенників як додатків. Практика показує, що форми знахідного відмінка (`мене`, `тебе`, `його`) та родового (`без тебе`) є найбільш частотними у розмовній мові (Source 4).

4.  **Вираження стану та почуттів:** Конструкції типу `Мені + прислівник` (`Мені погано`, `Мені холодно`) та `У мене + іменник` (`У мене температура`, `У мене болить голова`) вводяться як сталі фрази для опису самопочуття, що є критично важливим для повсякденного спілкування (Source 8).

Основний метод — це комунікативний підхід: граматика вивчається не як абстрактне правило, а як інструмент для вирішення конкретного завдання (записатися до лікаря, запросити на вечірку, розповісти про самопочуття).

## Повна парадигма (Full Paradigm)

Для рівня А2 ключовим є впевнене володіння особовими займенниками в знахідному та родовому відмінках, а також системою неозначених займенників та прислівників.

### Знахідний та Родовий відмінки особових займенників (Accusative & Genitive of Personal Pronouns)

Ці відмінки часто викликають труднощі. Знахідний відповідає на питання `кого? / що?` (прямий додаток), а Родовий — `кого? / чого?` (часто після прийменників `без`, `у`, `для`).

| Називний | Знахідний (кого?) | Родовий (у/без кого?) | Приклад (Знахідний) | Приклад (Родовий) |
| :--- | :--- | :--- | :--- | :--- |
| я | **мене** | у **мене** / без **мене** | Я бачу **мене** в дзеркалі. | **У мене** є питання. (Source 8) |
| ти | **тебе** | у **тебе** / без **тебе** | Хочу запросити **тебе**. (Source 4) | Приходь, бо без **тебе** буде сумно. (Source 4) |
| він/воно | **його** | у **нього** / без **нього** | Я бачу **його**. | Я був у **нього** вчора. |
| вона | **її** | у **неї** / без **неї** | Я знаю **її**. | **У неї** болить голова. (Source 8) |
| ми | **нас** | у **нас** / без **нас** | Він запросив **нас**. | **У нас** закінчилися лимони. (Source 8) |
| ви | **вас** | у **вас** / без **вас** | Я чекаю на **вас**. | Як **у вас** справи? (Source 1) |
| вони | **їх** | у **них** / без **них** | Я бачу **їх** на вулиці. | Я дізнався це від **них**. |

**Важливо:** Після прийменників займенники `він`, `вона`, `вони` отримують приставний `н-`: `у **н**ього`, `для **н**еї`, `без **н**их` (Source 4).

### Неозначені займенники та прислівники (Indefinite Pronouns & Adverbs)

Ці слова утворюються додаванням часток **-сь**, **-небудь**, **будь-** до питальних слів.

| Питальне слово | з **-сь** (конкретна, але невідома особа/річ) | з **-небудь** (будь-яка, неважливо яка) | з **будь-** (будь-яка, довільна) |
| :--- | :--- | :--- | :--- |
| хто? | хто**сь** (someone) | хто-**небудь** (anyone) | **будь-**хто (anyone, whoever) |
| що? | що**сь** (something) | що-**небудь** (anything) | **будь-**що (anything, whatever) |
| який? | який**сь** (some kind of) | який-**небудь** (any kind of) | **будь-**який (any) |
| де? | де**сь** (somewhere) | де-**небудь** (anywhere) | **будь-**де (anywhere) |
| коли? | коли**сь** (sometime, once) | коли-**небудь** (sometime, ever) | **будь-**коли (anytime) |
| як? | як**ось** (somehow) | як-**небудь** (somehow, anyhow) | **будь-**як (anyhow) |

Приклади з джерел:
*   `Ви **коли-небудь** вже були в нашій лікарні?` (Source 1) - "Have you *ever* been..."
*   `Вас записати до **будь-якого** лікаря?` (Source 1) - "Should I sign you up to *any* doctor?"
*   `Треба пити **багато** рідини.` (Source 8)

## Частотність і пріоритети (Frequency & Priorities)

На рівні А2 пріоритет надається граматиці, що дозволяє вирішувати нагальні комунікативні задачі.

1.  **Вираження стану здоров'я:** Конструкції `У мене болить...`, `Мені...` є першочерговими. Вони є основою для діалогів у лікаря, аптеці, або просто для пояснення свого самопочуття (Sources 1, 2, 8).
2.  **Особові займенники в Знахідному/Родовому відмінках:** Це ядро міжособистісного спілкування. Фрази як `Я тебе бачу`, `У мене є`, `Без тебе` є надзвичайно частотними. (Source 4)
3.  **Складений майбутній час (`буду робити`):** Ця форма є простішою для утворення, ніж доконаний майбутній час, і дозволяє говорити про плани на майбутнє без заглиблення у видову систему дієслів. (Source 5)
4.  **Минулий час:** Форми минулого часу є простими для утворення (суфікс `-в`/`-ла`/`-ло`/`-ли`) і критично важливими для розповіді про минулі події. (Source 5)
5.  **Неозначені займенники з `-сь` та `будь-`:** `хтось`, `щось`, `десь`, `колись` та `будь-який`, `будь-коли` є більш поширеними в розмовній мові, ніж форми з `-небудь` (Source 1).

## Типові помилки L2 (Common L2 Errors)

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| `Я маю головний біль.` | `У мене болить голова.` (Source 8) | Пряма калька з англійського "I have a headache". В українській мові для вираження болю використовується конструкція `У + [іменник в род. відм.] + болить + [іменник в наз. відм.]`. |
| `Я є добре.` / `Я почуваю добре.` | `Мені добре.` / `Я почуваюся добре.` | Для вираження стану використовується безособова конструкція з давальним відмінком (`мені`, `тобі`) або зворотне дієслово `почуватися`. (Source 3) |
| `Я не знаю *ніяких* конкретних лікарів.` | `Я не знаю *жодних* конкретних лікарів.` (Source 1) | Подвійне заперечення в українській мові вимагає використання заперечних займенників (`ніхто`, `ніщо`, `жоден`), а не `ніякий`, яке є русизмом у цьому контексті. |
| `Приймати участь у змаганнях.` | `Брати участь у змаганнях.` | `Приймати участь` — це калька з російського "принимать участие". Українською мовою правильно говорити `брати участь`. (Source 41) |
| `Залишилося дві неділі до канікул.` | `Залишилося два тижні до канікул.` | Слово `неділя` в українській мові означає "Sunday", а не "week". Слово "week" перекладається як `тиждень`. (Source 15) |
| `Я бачу *його* машину, але *в його* немає ключів.` | `Я бачу *його* машину, але *в нього* немає ключів.` | Прийменники вимагають додавання приставного `н-` до займенників 3-ої особи (`він`, `вона`, `вони`) у родовому, давальному, знахідному та орудному відмінках. (Source 4) |

## Деколонізаційні застереження (Decolonization Notes)

1.  **Неозначені займенники:** Система українських неозначених часток (`-сь`, `-небудь`, `будь-`, `аби-`, `казна-`, `хтозна-`) є багатшою і має свої нюанси порівняно з російською. Наприклад, `будь-хто` (anybody, open choice) та `хто-небудь` (anybody, one from a set) часто не розрізняються в російській (`кто-нибудь`). Не можна пояснювати українські форми як аналоги російських.

2.  **Лексичні відмінності:** Слід активно виявляти та виправляти русизми, що проникли в мову.
    *   `Тиждень` (week) vs. `неділя` (Sunday). У російській "неделя" означає тиждень. (Source 15)
    *   `Брати участь` vs. калька `приймати участь`. (Source 41)
    *   `Намет` (tent) vs. суржикове `палатка`. (Source 6)
    *   `Ліки` (medicine) vs. російське `лікарство`. (Sources 2, 13)

3.  **Фонетика та наголос:** Наголос у займенниках при вживанні з прийменниками може змінюватися (`без **те́бе**`, `до **ме́не**`), що є унікальною рисою української мови, на відміну від російської, де наголос стабільний. (Source 4)

4.  **Професійні назви:** В українській мові для позначення професій жінок активно використовуються фемінітиви (`вчителька`, `лікарка`, `директорка`). Навіть якщо в джерелі вжито маскулінум (`лікар Василькова`), сучасна норма тяжіє до використання фемінітивів. (Sources 1, 24)

Українська граматика повинна викладатися як самостійна, логічна система, а не як "варіант" або "виняток" з іншої мови.

## Природні приклади (Natural Examples)

**Група 1: Розмова про здоров'я та самопочуття**
*   `У мене болить голова і горло, температура 38,2.` (Source 1)
*   `Мені вже набагато краще.` (Source 3)
*   `Він її швидко вилікує.` (Source 1, `вилікувати` - to cure)
*   `Якщо завтра не стане краще, то підеш до лікаря.` (Source 8)

**Група 2: Неозначені займенники та прислівники**
*   `Ви коли-небудь вже були в нашій лікарні?` (Source 1)
*   `Вас записати до будь-якого лікаря?` (Source 1)
*   `Коли вам буде зручно прийти? — Та будь-коли.` (Source 1)
*   `Ви живете з кимось?` (Source 2)

**Група 3: Запрошення та плани (Знахідний відмінок та майбутній час)**
*   `Хочу запросити тебе в гості в п'ятницю на маленьку вечірку.` (Source 4)
*   `Я буду святкувати своє підвищення.` (Source 4)
*   `Всі будуть раді тебе бачити.` (Source 4)
*   `Що Інна буде робити на вихідних?` (Source 5)

**Група 4: Минулі події (Минулий час)**
*   `Я пролежала майже тиждень.` (Source 3)
*   `Що робив Євген минулого місяця? — Він катався на сноуборді.` (Source 5)
*   `Епідемія грипу в Україні минула.` (Source 3)

## Рекомендації для вправ (Activity Concepts)

**Phase 1: Розпізнавання та ідентифікація**
*   **Вправа "Знайди в тексті":** Дати студентам короткий діалог (наприклад, з Source 1) і попросити знайти всі конструкції для вираження болю, всі форми майбутнього часу, всі неозначені займенники.
*   **Тести з вибором відповіді:**
    *   `Я хочу запросити (ти/тебе/тобі) на каву.`
    *   `Вчора я (був/буду/є) в кіно.`
    *   `(Хтось/Хто-небудь) стукає у двері.`

**Phase 2: Контрольована практика**
*   **Заповнення пропусків:** Дати речення з пропущеними займенниками у правильній формі. `Лікар оглянув ____ (вона) і дав ____ (вона) рецепт.` -> `...оглянув її і дав їй...`
*   **Трансформація:** Перетворити речення з однієї особи на іншу. `Я був у Карпатах.` -> `Вона ... у Карпатах.` -> `Вони ... у Карпатах.` (Source 5)
*   **Складання речень:** Дати набір слів, з яких треба скласти граматично правильне речення. `(у / боліти / мене / голова)` -> `У мене болить голова.`

**Phase 3: Вільна практика (Продукція)**
*   **Рольова гра "У лікаря":** Один студент — пацієнт, інший — лікар. Пацієнт має описати свої симптоми (`у мене болить...`, `мені погано...`), лікар — поставити діагноз і дати рекомендації (`вам потрібно...`, `приймайте ці ліки...`). (Базується на Sources 1, 2, 8)
*   **Рольова гра "Запрошення на вечірку":** Студенти мають запросити одне одного на уявну подію (день народження, вечірка), домовитись про час і місце, використовуючи знахідний відмінок та майбутній час. (Базується на Source 4)
*   **"Що ти робив на вихідних?":** Студенти в парах розповідають одне одному про свої минулі вихідні, практикуючи минулий час дієслів.

## Зв'язки з іншими темами

*   **Попередні теми (A1):** Ця тема базується на знанні називного відмінка іменників та займенників, теперішнього часу дієслів та базових конструкцій речень.
*   **Наступні теми (B1):** Успішне засвоєння цих тем є фундаментом для вивчення складніших аспектів на рівні B1, таких як:
    *   **Видова система дієслів:** Розуміння різниці між `робити` (недоконаний) і `зробити` (доконаний) стане наступним кроком після освоєння складеного майбутнього часу.
    *   **Дієслова руху:** Тема, що вимагає глибокого розуміння префіксів та відмінків.
    *   **Складніші відмінки:** Опанування знахідного та родового готує до вивчення давального, орудного та місцевого відмінків у повному обсязі.

## Пов'язані статті

*   `grammar/a1/present-tense`
*   `grammar/a1/past-tense-introduction`
*   `grammar/a2/accusative-case-pronouns`
*   `grammar/a2/genitive-case-possession-negation`
*   `grammar/b1/verbs-of-motion`
*   `grammar/b1/verb-aspect`
</wiki_context>

## Plan References

- 
- 

</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Частина 1: Читання (Part 1: Reading)` (~450 words)
- `## Частина 2: Граматика (Part 2: Grammar)` (~400 words)
- `## Частина 3: Спілкування та письмо (Part 3: Communication and Writing)` (~350 words)
- `## Результати та самооцінка (Results and Self-Assessment)` (~300 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 1500 words minimum.

---

## Content Rules

TARGET: 70-90% Ukrainian.
LANGUAGE ROLES:
- PRIMARY: Ukrainian for everything.
- ENGLISH: Only in vocabulary tables and one-line grammar notes where absolutely necessary.
- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English.
A2 register. Concrete everyday vocabulary. No literary language, no metaphors. Near-full Ukrainian immersion. Ukrainian sentences max 15 words. Max 2 clauses. All cases allowed. Simple subordinate clauses only. Full aspect pairs. No participles.

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
  1. **Mock oral exam — examiner asks situational questions: Розкажіть про свій день. Що ви робили вчора? Які плани на літо? Порівняйте Київ і ваше місто. Опишіть свою сім'ю.**
     Speakers: Екзаменатор, Кандидат
     Why: Full A2 oral exam simulation — all tenses, cases, vocabulary

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

**Required:** іспит (exam), завдання (task, exercise), відповідь (answer), питання (question), читання (reading), письмо (writing), граматика (grammar), результат (result)
**Recommended:** самооцінка (self-assessment), оцінка (grade, assessment), правильний (correct)

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
## Вступ (~100 слів)
- P1 (~100 слів): Привітання та пояснення мети модуля. Пояснення різниці між "складати іспит" (to take/sit an exam) та "здавати іспит" (to pass/hand in — common error). Огляд структури тесту: читання, граматика, письмо. Надихаючі слова про завершення рівня A2.

## Частина 1: Читання (Part 1: Reading) (~480 слів)
- P1 (~60 слів): Стратегії читання для іспиту. Різниця між пошуковим читанням (scanning for info) та вивчальним читанням (deep comprehension). Пояснення термінів: оголошення (announcement), розклад (schedule), зміст (content).
- P2 (~120 слів): Текст А — Інформаційне повідомлення. Оголошення про мовні курси або виставку. Використання дат (15 травня), часу (о 10:00), адрес (вулиця Володимирська) та цін (безкоштовно, 200 гривень).
- P3 (~150 слів): Текст Б — Електронний лист від Андрія. Розповідь про переїзд до нового міста, нову роботу та плани на вихідні. Використання минулого часу (я переїхав, я знайшов) та конструкцій майбутнього часу (я буду працювати, ми підемо).
- P4 (~150 слів): Текст В — Наратив про українську традицію. Короткий текст про "Святвечір" або "Масницю". Опис страв (кутя, вареники) та дій (співати колядки, зустрічати весну). Перевірка розуміння контексту та нових слів.
- <!-- INJECT_ACTIVITY: fill-in-reading-comprehension --> [fill-in, Reading comprehension — answer questions about the texts above, 8 items]

## Частина 2: Граматика (Part 2: Grammar) (~420 слів)
- P1 (~60 слів): Огляд ключових граматичних зон А2. Повторення системи відмінків, дієвідмін та вживання займенників. Порада: звертати увагу на прийменники-маркери (без, до, у, над).
- P2 (~120 слів): Секція А — Іменники та відмінки. Повторення конструкцій відсутності (у мене немає часу), напрямку (йти до школи/в магазин) та місця (жити в Одесі/на Заході). Приклади узгодження істот/неістот у знахідному відмінку (бачу друга vs. бачу будинок).
- P3 (~120 слів): Секція Б — Дієслівні форми. Відмінювання "бути", "їсти", "дати", "відповісти". Узгодження минулого часу за родом (Петро сказав, Марія сказала) та числами. Складена форма майбутнього часу (буду складати, будеш писати).
- P4 (~120 слів): Секція В — Займенники та порівняння. Вживання зворотних займенників "свій", "себе" (Я бачу себе, він бере свій зошит). Неозначені займенники з частками -сь та будь- (хтось, щось, будь-який). Простий ступінь порівняння прикметників (швидший, кращий).
- <!-- INJECT_ACTIVITY: quiz-mixed-grammar --> [quiz, Simulated exam — mixed grammar questions (cases, aspect, comparison), 8 items]
- <!-- INJECT_ACTIVITY: true-false-grammar-accuracy --> [true-false, Grammar accuracy check — identify correct vs incorrect sentences, 8 items]

## Частина 3: Спілкування та письмо (Part 3: Communication and Writing) (~380 слів)
- P1 (~130 слів): Діалог — Симуляція усного іспиту. Розмова між Екзаменатором та Кандидатом. Питання: "Розкажіть про свій типовий день", "Чому ви вивчаєте українську?", "Яка погода вам подобається?". Використання ввічливих форм (Вибачте, чи не могли б ви повторити?).
- P2 (~80 слів): Підготовка до письмового завдання. Як структурувати коротке есе (80-100 слів). Важливість логічних зв'язок: спочатку (first), тому що (because), нарешті (finally).
- P3 (~120 слів): Аналіз типових помилок (L2 Interference). Чому не можна казати "вірна відповідь" (правильно: правильна відповідь) та "приймати участь" (правильно: брати участь). Пояснення різниці між "вибачаюсь" та "вибачте".
- P4 (~50 слів): Опис тем для письмового завдання. 1. Мій улюблений сезон. 2. Лист другу про вихідні. 3. Моя родина та традиції.
- <!-- INJECT_ACTIVITY: error-correction-l2-pitfalls --> [error-correction, Find and correct grammar errors in sentences covering L2 interference, 6 items]

## Результати та самооцінка (~320 слів)
- P1 (~150 слів): Пояснення правильних відповідей. Детальний розбір, чому в питанні 5 потрібен родовий відмінок, а в питанні 10 — форма "складати". Навчання через аналіз власних помилок.
- P2 (~100 слів): Сітка самооцінки А2. Список тверджень для перевірки:
    - Я можу розповісти про свою роботу та хобі.
    - Я розумію короткі тексти про повсякденне життя.
    - Я правильно вживаю відмінки з прийменниками.
    - Я можу написати лист другові про свої плани.
- P3 (~70 слів): Рекомендації та мотивація. Що робити, якщо результат менше 70% (переглянути модулі 50-60). Вітання з успішним завершенням курсу A2 та запрошення до рівня B1.

Grand total: ~1600 words
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
