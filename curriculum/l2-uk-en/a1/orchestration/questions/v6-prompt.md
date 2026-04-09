

---

## Your Writing Identity

**You are: Lead Ukrainian Instructor.** Your persona is *The Patient Guide*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **19: Questions** (A1, A1.3 [Actions]).

**Target: 1200–1800 words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block. Evaluate each section from the plan and commit to a word budget. This prevents frontloading early sections and rushing later ones.

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Summary: ~150 words
Total: 1200+ words
</pacing_plan>
```

Then begin writing the module content. Follow your own pacing plan — each section must hit its word budget (±10%).

---

## 9 Hard Rules

1. **IMMERSION TARGET: 15-25% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if immersion is outside this range. For A1 early modules, the learner cannot read Cyrillic — English must dominate. For A2+, Ukrainian must carry a significant share — add Ukrainian Reading Practice blocks, dialogues, and example paragraphs to reach the target. Too little Ukrainian fails audit just as much as too much.
2. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
3. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
4. **You are a warm, encouraging teacher.** Natural teacher phrasing ("Let us look at...", "Have you noticed...") is fine. What to AVOID: self-congratulatory openers ("Welcome to A2! Congratulations!"), gamified language ("You have unlocked...", "You now possess..."), and empty filler sentences that add words but zero information. Every sentence should teach something specific to Ukrainian.
5. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
6. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers where exercises should appear. A separate pipeline step generates the actual exercises from the plan's activity_hints.
7. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
8. **Hit the word target** — you MUST write 1200–1800 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
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
module: a1-019
level: A1
sequence: 19
slug: questions
version: '1.1'
title: Questions
subtitle: Хто? Що? Де? — asking about the world
focus: grammar
pedagogy: PPP
phase: A1.3 [Actions]
word_target: 1200
objectives:
- Ask questions using хто, що, де, куди, коли, чому, як
- Use negation with не (verb) and ні (nothing/nobody)
- Form yes/no questions with intonation (no word order change)
- Combine question words with verbs from M16-M18
dialogue_situations:
- setting: A tourist asking a local for help navigating the city center
  speakers:
  - Турист
  - Перехожий (passerby)
  motivation: 'Question words: Де? Куди? Як? Коли? in real navigation'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Getting to know someone (extending M05): — Хто ти? — Я студент.
    — Що ти вивчаєш? — Я вивчаю українську. — Де ти живеш? — Я живу в Києві. — Коли
    ти працюєш? — Вранці. Question words demonstrated in real conversation.'
  - 'Dialogue 2 — At home: — Де моя книга? — Я не знаю.
    — А хто знає? — Мама знає. — Чому мама? — Тому що вона все знає! Questions
    + negation in practical context.'
- section: Питальні слова (Question Words)
  words: 300
  points:
  - 'Seven essential question words: Хто? (Who?) — Хто це? Хто говорить? Що? (What?)
    — Що це? Що ти робиш? Де? (Where?) — Де ти живеш? Де книга? Куди? (Where to?)
    — Куди ти ходиш? Коли? (When?) — Коли ти працюєш? Чому? (Why?) — Чому ти не працюєш?
    Як? (How?) — Як справи? Як тебе звати?'
  - 'Word order: question word + verb + subject (flexible): Де ти живеш? = Ти де живеш?
    (both acceptable). Yes/no questions: just raise intonation at the end: Ти говориш
    українською? ↑ (no special word needed). Чи ти говориш? — formal/written (optional
    for A1).'
- section: Заперечення (Negation)
  words: 300
  points:
  - 'Не = not (before verb): Я не знаю. Він не працює. Ми не розуміємо. Не goes directly
    before the verb — never separated. Review: Я не хочу. Мені не подобається. (from
    M15, M18)'
  - 'Ні = no (standalone) / nothing, nobody (with pronouns): Ні, я не знаю. (No, I
    don''t know.) Нічого (nothing), ніхто (nobody), ніколи (never), ніде (nowhere).
    Double negation is REQUIRED in Ukrainian: Я нічого не знаю. (literally: I nothing
    don''t know = I don''t know anything.) Ніхто не говорить. (Nobody speaks.) — unlike
    English, both не and ні- are needed.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Questions: Хто? Що? Де? Куди? Коли? Чому? Як? Yes/no: intonation only (Ти знаєш?
    ↑) Negation: не before verb (Я не знаю). Double negation: Ніхто не знає. Я нічого
    не бачу. Self-check: Ask 3 questions about a friend (Де...? Що...? Коли...?).
    Make 2 negative sentences (Я не... / Ніхто не...).'
vocabulary_hints:
  required:
  - хто (who)
  - що (what)
  - де (where)
  - куди (where to)
  - коли (when)
  - чому (why)
  - як (how)
  - не (not)
  - ні (no)
  recommended:
  - ніхто (nobody)
  - нічого (nothing)
  - ніколи (never)
  - жити (to live)
  - розуміти (to understand)
  - тому що (because)
activity_hints:
- type: quiz
  focus: 'Choose the right question word: ___ ти живеш? (Де/Що/Хто)'
  items: 8
- type: fill-in
  focus: 'Make it negative: Я знаю → Я не знаю, Хтось знає → Ніхто не знає'
  items: 8
- type: match-up
  focus: 'Match question to answer: Де ти живеш? ↔ У Києві.'
  items: 6
- type: quiz
  focus: 'Double negation: choose the correct Ukrainian sentence.'
  items: 6
connects_to:
- a1-020 (My Morning)
prerequisites:
- a1-018 (I Want, I Can)
grammar:
- 'Question words: хто, що, де, куди, коли, чому, як'
- Yes/no questions with rising intonation
- 'Negation: не before verb'
- 'Double negation: ніхто не + verb, нічого не + verb'
register: розмовний
references:
- title: Варзацька Grade 4, p.41
  notes: Question words in case system context (хто? що? кого? чого?).
- title: ULP Season 1, Episode 35
  url: https://www.ukrainianlessons.com/episode35/
  notes: Questions in Ukrainian — word order and intonation.

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
- Confirmed: хто, що, де, куди, коли, чому, як, не, ні, ніхто, нічого, ніколи, жити, розуміти, тому.
- Not found: [none] (Note: "тому що" is verified as its components "тому" and "що" are both confirmed in VESUM as conjunction/adverb and conjunction/pronoun respectively).

## Grammar Rules
- Negation with verbs: Правопис §44.1.1 — Частку **не** з дієсловами пишемо окремо: *не знати*, *не розуміти*.
- Double negation: Confirmed via textbook usage (Grade 1, 5, 9) — Ukrainian requires double negation with negative pronouns/adverbs: *Ніхто нічого не знає*, *Я нічого не чую*.
- Question sentences: Grade 2 Textbook (Vashulenko) — Питальні речення виражають запитання, у кінці ставиться знак питання (?). Інтонація підвищується на питальному слові або в кінці речення.

## Calque Warnings
- тому що: OK — Standard conjunction (СУМ-11 confirms usage: "Унаслідок чого-небудь; через те").
- як справи: OK — Standard idiomatic greeting.
- де ти живеш: OK — Standard usage (though "мешкати" is a synonym often used for housing, "жити" is perfectly natural for A1).

## CEFR Check
- хто, що, де, куди, коли, чому, як: A1 — Verified (Found in Grade 1-2 textbooks).
- жити, розуміти: A1 — Verified (Found in Grade 1-2 textbooks).
- ніхто, нічого, ніколи: A1 — Verified (Core negative pronouns introduced early in primary education).
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
# Knowledge Packet: Questions
**Module:** questions | **Track:** A1

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: pedagogy/a1/questions.md

# Педагогіка A1: Questions



## Методичний підхід (Methodological Approach)

Навчання питаннґ в українській мові для початківців (A1) має будуватися на принципі від простого до складного, з фокусом на інтонації та найбільш уживаних питальних словах. Українські підручники для молодших класів демонструють чіткий, поетапний підхід.

Основою є розрізнення речень за метою висловлювання: розповідні, питальні та спонукальні (Source 36). Питальне речення визначається як таке, "у якому про щось запитується" і в кінці якого ставиться знак питання (Source 37).

Перший крок — навчити учнів перетворювати розповідне речення на питальне за допомогою самої лише **інтонації**. Це найбільш природний і поширений спосіб утворення так/ні питань у розмовній мові. Підручник для 2-го класу показує, як з одного розповідного речення можна утворити кілька різних питань, інтонаційно виділяючи різні слова: "**Хто** приніс їжачка?", "Кого **принесли** діти?", "**Куди** діти принесли їжачка?" (Source 30). Цей метод одразу знайомить учнів із важливістю інтонаційного наголосу для передачі сенсу.

Другий крок — введення питальної частки **`чи`**. Вона слугує формальним маркером так/ні питання і часто використовується для уникнення двозначності або для надання питанню більш офіційного чи підкресленого відтінку. Наприклад, "Чи добре ти володієш українською мовою?" (Source 36).

Третій крок — послідовне введення базових **питальних займенників і прислівників** (`хто`, `що`, `де`, `коли`, `як`). Вони вводяться в контексті простих діалогів та вправ. Наприклад: "— **Яку** книжку ти прочитав?", "— **Хто** написав цю казку?", "— **Що** тобі найбільше сподобалося в казці?" (Source 37). Важливо подавати ці слова в реалістичних розмовних ситуаціях, як-от планування вихідних: "**Що** робиш?", "А **у тебе** є плани на вихідні?" (Source 5).

На рівні А1 фокус залишається на розпізнаванні та побудові простих питань. Складніші конструкції, як-от розрізнення питальних і відносних займенників (`Хто гратиме?` vs `Я знаю, хто гратиме`) (Source 14), та риторичні питання (`Ти знаєш, що ти — людина?`) (Source 29) вводяться на вищих рівнях (A2 і вище), але підґрунтя для них закладається саме зараз.

## Послідовність введення (Introduction Sequence)

1.  **Step 1: Так/Ні питання через інтонацію.**
    *   Починати з перетворення простих розповідних речень на питальні виключно за допомогою висхідної інтонації в кінці речення. Це найчастотніший спосіб утворення так/ні питань у живому мовленні.
    *   *Приклад:* `Це стіл.` (розповідне, спадна інтонація) → `Це стіл?` (питальне, висхідна інтонація). `Ти тут.` → `Ти тут?`
    *   *Чому так:* Це імітує природне мовлення і не вимагає вивчення нової лексики.

2.  **Step 2: Питальна частка `Чи`.**
    *   Ввести `чи` як формальний маркер так/ні питання, що ставиться на початку речення.
    *   *Приклад:* `Чи це стіл?` `Чи ти тут?`
    *   *Чому так:* `Чи` є однозначним індикатором питання, що корисно на письмі та в більш формальних ситуаціях. Це також допомагає уникнути плутанини, коли інтонація учня ще не відпрацьована. Згадується у підручнику для 3 класу (Source 36).

3.  **Step 3: Основні питальні слова `Хто?` і `Що?`**
    *   Ввести найфундаментальніші питальні займенники для ідентифікації осіб та предметів.
    *   *Приклад:* `Хто це? — Це Марія.` `Що це? — Це книга.`
    *   *Чому так:* Ці слова є високочастотними і дозволяють будувати базові діалоги. Вони вимагають відмінювання в непрямих відмінках (`кого?`, `чому?`), але на А1 фокус на називному відмінку (`хто?`, `що?`).

4.  **Step 4: Питальні слова місця і часу: `Де?`, `Куди?`, `Коли?`**
    *   Ввести прислівники для запитань про місцезнаходження, напрямок і час.
    *   *Приклад:* `Де ти? — Я вдома.` `Куди ти ідеш? — Я іду в магазин.` `Коли? — Завтра.`
    *   *Чому так:* Ці слова є критично важливими для базової комунікації про повсякденні дії та плани, як показано в діалозі про вихідні (Source 5, Source 197). Важливо одразу показати різницю між `де` (статичне місце) та `куди` (напрямок).

5.  **Step 5: Питальні слова способу дії, причини, кількості: `Як?`, `Чому?`, `Скільки?`**
    *   Ввести слова для запитань про спосіб, причину та кількість.
    *   *Приклад:* `Як справи?` `Чому ти тут?` `Скільки це коштує?`
    *   *Чому так:* `Як справи?` є однією з перших фраз, яку вивчають. `Чому?` і `Скільки?` розширюють можливості для більш змістовних розмов.

6.  **Step 6: Питальні слова для опису: `Який?` і `Чий?`**
    *   Ввести займенники для запитань про характеристику та приналежність.
    *   *Приклад:* `Який це фільм? — Це цікавий фільм.` `Чия це книга? — Це моя книга.`
    *   *Чому так:* Вони вводять необхідність узгодження прикметників і присвійних займенників з іменниками за родом, числом і відмінком, що є фундаментальною навичкою.

## Типові помилки L2 (Common L2 Errors)

| ❌ Помилково (Неправильно) | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| `Ти є вчитель?` (пряма калька з "Are you a teacher?") | `Ти вчитель?` або `Чи ти вчитель?` | Дієслово `бути` (є) у теперішньому часі зазвичай опускається. Його використання в такому питанні звучить неприродно і видає іноземця. |
| `Що колір?` (калька з "What color?") | `Який колір?` | В англійській мові "what" використовується для ідентифікації (`What is this?`) і для характеристики (`What color is it?`). В українській мові для характеристики предмета використовується займенник `який / яка / яке` (Source 30, Source 37). |
| `Куди ти є?` (плутанина `де` і `куди`) | `Де ти?` | Англійське "where" може означати і місце (`Where are you?`), і напрямок (`Where are you going?`). В українській мові для статичного місця використовується `де`, а для напрямку — `куди` (Source 33). |
| `Я не бачу ніхто.` (одинарне заперечення) | `Я нікого не бачу.` | В українській мові, на відміну від англійської, використовується подвійне (або множинне) заперечення. Якщо є заперечний займенник (`ніхто`, `ніщо`) або прислівник (`ніколи`, `ніде`), дієслово також має стояти в заперечній формі з часткою `не` (Source 7, Source 13). |
| `Як діла?` (русизм) | `Як справи?` | Фраза `Як діла?` є прямим фонетичним і лексичним запозиченням з російської `Как дела?`. Це поширений приклад суржику. Літературна українська норма — `Як справи?` (Source 6). |

## Деколонізаційні застереження (Decolonization Notes)

**Обов'язково для виконання.** Навчання української мови має відбуватися на власних українських засадах, уникаючи російської як посередника чи точки відліку.

1.  **Уникати порівнянь з російською:** Ніколи не пояснювати українські питальні слова через їхні російські аналоги (напр., НЕ кажіть: "українське `чи` схоже на російське `ли`"). Це створює хибне уявлення про українську мову як про діалект чи варіацію російської. Навчайте українські структури як самостійне явище.

2.  **Акцентувати на українській фонетиці:** Інтонація в українських питаннях має свої унікальні мелодійні контури. Не можна покладатися на російські інтонаційні моделі. Навчання має базуватися на аудіоприкладах від носіїв української мови.

3.  **Викривати суржик:** Потрібно активно пояснювати, чому певні конструкції є суржиком (змішуванням української та російської). Класичний приклад — питання `Як діла?`, яке походить від російського `Как дела?`. Правильний український відповідник — `Як справи?` (Source 6). Раннє виявлення і виправлення таких помилок запобігає закріпленню русизмів.

4.  **Пояснювати подвійне заперечення як норму:** Подвійне заперечення (`ніхто не прийшов`) є стандартною граматичною рисою багатьох слов'янських мов, включно з українською (Source 7). Це не "нелогічно" порівняно з англійською, і не є "таким самим, як у російській". Це просто граматична норма української мови, яку потрібно вивчати і практикувати.

## Словниковий мінімум (Vocabulary Boundaries)

На рівні A1 учні мають опанувати базові питальні слова і вміти використовувати їх у простих реченнях.

**Питальні слова (займенники та прислівники):**
*   `Хто?` ★★★ (Who?)
*   `Що?` ★★★ (What?)
*   `Де?` ★★★ (Where?)
*   `Коли?` ★★★ (When?)
*   `Куди?` ★★☆ (Where to?)
*   `Як?` ★★★ (How?)
*   `Чому?` ★★☆ (Why?)
*   `Який? / Яка? / Яке?` ★★☆ (What kind of? Which?)
*   `Чий? / Чия? / Чиє?` ★☆☆ (Whose?)
*   `Скільки?` ★★☆ (How much? / How many?)
*   `Чи` ★★★ (Interrogative particle for Yes/No questions)
*   `Звідки?` ★☆☆ (Where from?) (Джерело: `11-klas-ukrmova-zabolotnyi-2019_s0357`)

**Приклади використання з А1-лексикою:**
*   **Іменники:** `друг`, `книга`, `дім`, `робота`, `кава`, `вода`, `мама`.
*   **Дієслова:** `бути` (форма `є`), `жити`, `робити`, `іти`, `хотіти`, `читати`, `любити`.
*   **Прикметники:** `добрий`, `новий`, `старий`, `великий`, `малий`, `цікавий`.

*Зразки питань:* `Хто там?`, `Що це?`, `Де ти живеш?`, `Як справи?`, `Чи ти любиш каву?`, `Яка це книга?`, `Скільки це коштує?`

## Приклади з підручників (Textbook Examples)

1.  **Вправа "Створи питання з речення" (Source 30)**
    *   **Формат:** Учням дається розповідне речення. Вони мають усно або письмово створити до нього якомога більше питань, що стосуються різних членів речення.
    *   **Приклад з підручника (2 клас):**
        *   Речення: `Учора діти принесли маленького їжачка в живий куточок.`
        *   Питання для учнів:
            *   `Хто приніс їжачка в живий куточок?`
            *   `Кого принесли діти в живий куточок?`
            *   `Куди діти принесли їжачка?`
            *   `Коли діти принесли їжачка?`
            *   `Якого їжачка принесли діти?`
    *   **Педагогічна цінність:** Вчить бачити зв'язок між питальним словом та членом речення, а також тренує інтонацію.

2.  **Вправа "Знайди питальні речення" (Source 36)**
    *   **Формат:** Учням дається короткий текст або вірш, що містить речення різних типів (розповідні, питальні, спонукальні). Завдання — знайти і прочитати вголос саме питальні речення з правильною інтонацією.
    *   **Приклад з підручника (3 клас):**
        *   Вірш: `Чуєш, друже мій, розмови? / З вітром листя гомонить, / з сонцем — ниви і діброви, / із озерами — блакить...`
        *   Завдання: `Знайди в тексті розповідні, питальні і спонукальні речення.`
    *   **Педагогічна цінність:** Тренує навичку розпізнавання питальних речень у потоці мовлення.

3.  **Вправа "Так чи ні?" (Діалог-відповідь)**
    *   **Формат:** Вчитель або інший учень ставить прості так/ні питання, а інший учень має дати повну або коротку відповідь.
    *   **Приклад з підручника (2 клас):**
        *   Питання: `— Як ти думаєш, де краще жити їжачку: у лісі чи в живому куточку?`
        *   Початок відповіді: `— Я думаю, що в живому куточку, тому що...?`
    *   **Педагогічна цінність:** Практика реальної комунікації, тренування структури відповіді.

4.  **Вправа "Розрізни питальний і відносний займенник" (А2, але основа з А1) (Source 14)**
    *   **Формат:** Учням дають пари речень, де одне є простим питальним, а інше — складним розповідним з підрядною частиною, введеною тим самим словом.
    *   **Приклад з підручника (6 клас):**
        *   `1. Хто гратиме у футбол?` (Питальний займенник)
        *   `2. Я знаю, хто гратиме у футбол.` (Відносний займенник)
    *   **Педагогічна цінність:** Готує учнів до розуміння складних речень, показуючи багатофункціональність питальних слів. На рівні А1 можна обмежитися лише першим типом речень, але тримати в полі зору другий тип для переходу на А2.

## Пов'язані статті (Related Articles)
- `pedagogy/a1/intonation`
- `pedagogy/a1/pronouns`
- `pedagogy/a1/negation`
- `pedagogy/a1/word-order`
- `pedagogy/a2/relative-clauses`
- `surzhyk-and-decolonization`

---

### Вікі: pedagogy/a1/this-and-that.md

# Педагогіка A1: This And That



## Методичний підхід (Methodological Approach)

The core pedagogical principle for teaching demonstratives (`цей`, `той`) in Ukrainian is to tightly integrate them with the concept of noun gender. Ukrainian elementary school textbooks do not teach these words in isolation; they are presented as a fundamental tool for identifying and reinforcing a noun's gender from the very beginning (Джерело: `3-klas-ukrainska-mova-kravtsova-2020-1_s0062`).

The primary method is **substitution and association**. Learners are taught to associate a noun with a chain of gender-agreeing words. For a masculine noun like `стіл` (table), the chain is `стіл` → `він` (he) → `мій` (my) → `цей` (this) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0030`, `3-klas-ukrainska-mova-ponomarova-2020-1_s0085`). This creates a powerful mental link between the noun and its grammatical gender, making adjective agreement (e.g., `цей червоний стіл`) intuitive later on.

The unchangeable pronoun `це` ("this/that is") is introduced first as a simple identifier. It is the most frequent and simplest form, used in basic sentence patterns like "**Це** + [іменник]" (e.g., "**Це** стіл," "**Це** книга."). This allows learners to start building sentences before tackling gender agreement (Джерело: `ext-video-4`, `5-klas-ukrmova-uhor-2022-1_s0081`).

Only after `цей/ця/це` are mastered as pointers for "close" objects is the "far" equivalent `той/та/те` introduced, often through direct contrastive exercises (`цю книгу чи ту книгу?` — "this book or that book?") (Джерело: `6-klas-ukrmova-litvinova-2023_s0280`).

Finally, demonstratives are presented as a key tool for creating cohesive text by avoiding noun repetition. Textbooks show how words like `цей`, `ця`, `він`, `вона` connect sentences and make writing flow more naturally (Джерело: `4-klas-ukrmova-zaharijchuk_s0014`, `4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0148`). At the A1 level, the focus is purely on the nominative (subject) case. Full declension is a B1 topic (<!-- VERIFY -->).

## Послідовність введення (Introduction Sequence)

The introduction must be methodical and layered, building from the simplest concept to the more complex.

- **Step 1: The Universal Identifier `Це`**
  - **What:** Introduce the word `це` as the universal, gender-neutral way to say "This is..." or "That is...". It answers the question `Що це?` (What is this?).
  - **Why:** This is the highest frequency demonstrative and requires zero knowledge of gender. It allows learners to immediately start identifying objects. For example: `Що це? - Це стіл.` `Що це? - Це книга.` (Джерело: `ext-video-4`). It functions like "It is" in English.

- **Step 2: The Gender Pointers `Цей`, `Ця`, `Це`**
  - **What:** Introduce the three gendered forms of "this": `цей` (masculine), `ця` (feminine), and `це` (neuter). Explicitly link them to the gender pronouns `він`, `вона`, `воно` and possessives `мій`, `моя`, `моє`.
  - **Why:** This directly reinforces noun gender. The teaching pattern is: see a noun (`стіл`), recall its gender pronoun (`він`), and then select the corresponding demonstrative (`цей стіл`) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0030`, `3-klas-ukrainska-mova-vashulenko-2020-1_s0128`). This builds the grammatical reflex for agreement.

- **Step 3: The Plural Pointer `Ці`**
  - **What:** Introduce the plural form `ці` ("these") for all genders.
  - **Why:** After mastering the three singular forms, the single plural form is a simple next step. It shows how gender distinctions disappear in the plural for demonstratives. Example: `ці столи`, `ці книги`, `ці вікна`. (Джерело: `4-klas-ukrmova-zaharijchuk_s0014`).

- **Step 4: Distinguishing "This" vs. "That" (`Той`, `Та`, `Те`, `Ті`)**
  - **What:** Introduce the "far" pointers `той` (m), `та` (f), `те` (n), and `ті` (pl) to contrast with the "near" pointers (`цей`, `ця`, `це`, `ці`).
  - **Why:** This concept of proximity is familiar to English speakers ("this/that"). It should be taught with contrastive examples, physically pointing to near and far objects. For example: `Цей стілець тут, а той стілець там.` (This chair is here, and that chair is there). `Мені, будь ласка, це/те тістечко` (Source 3) is a perfect textbook example of this choice.

- **Step 5: Demonstratives for Text Cohesion**
  - **What:** Show how `цей`, `він`, `вона` etc., are used to refer back to a previously mentioned noun to avoid clumsy repetition.
  - **Why:** This moves learners from single sentences to basic text construction. It's a key feature of natural Ukrainian writing style. (Джерело: `4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0148`, `4-klas-ukrmova-zaharijchuk_s0014`). For example: "Славко купив букет квітів... **Він** також узяв книжку." (Slavko bought a bouquet... **He** also took a book).

## Типові помилки L2 (Common L2 Errors)

English-speaking learners often make predictable errors when learning Ukrainian demonstratives due to interference from English grammar.

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| `Що цей?` | `Що це?` | Learners mistakenly use the gendered `цей` for the general question "What is this?". The correct form for identification is always the neutral, unchangeable `це`. (Джерело: `ext-video-4`) |
| `Ця стіл великий.` | `Цей стіл великий.` | This is a direct gender agreement error. The learner has not yet internalized that `стіл` is masculine and requires the masculine demonstrative `цей`. This is the most common error and is why linking demonstratives to gender is so critical. (Джерело: `3-klas-ukrainska-mova-ponomarova-2020-1_s0085`) |
| `Це стіл є новий.` | `Цей стіл новий.` or `Це новий стіл.` | Learners overuse the verb `є` (is/are), translating directly from English. In simple descriptive sentences in Ukrainian, the verb "to be" is usually omitted in the present tense. The first correct option uses the demonstrative as a pointer, while the second uses `це` as an identifier. |
| `Це столи.` | `Ці столи.` | The learner incorrectly uses the singular identifier `це` when pointing to multiple items. The correct plural demonstrative is `ці` for "these". (Джерело: `ext-ulp_youtube-261`) |
| `Мені подобається цей дівчина.` | `Мені подобається ця дівчина.` | Another gender agreement error, but with a feminine noun. The learner applies the default/masculine form `цей` to the feminine noun `дівчина`. (Джерело: `5-klas-ukrmova-uhor-2022-1_s0030`) |
| `Я живу в цей будинок.` | `Я живу в цьому будинку.` | This is a case error. While full declension is not an A1 topic, learners will encounter prepositions. They often incorrectly use the nominative form (`цей`) after a preposition instead of the required locative (`цьому`). This should be taught as a fixed chunk (`в цьому будинку`) at A1, with the grammatical explanation delayed. (<!-- VERIFY -->) |

## Деколонізаційні застереження (Decolonization Notes)

Teaching Ukrainian requires a conscious effort to de-link it from Russian and establish its own phonetic and grammatical foundation in the learner's mind.

1.  **Independent Phonetics:** The sound `[ц]` must be taught as a native Ukrainian phoneme. Do not describe it as "like the Russian ц". Use examples from within Ukrainian, like `цукор` (sugar), `палець` (finger), `кінець` (end). The learner's reference point must be Ukrainian itself.

2.  **No Russian Cognates as a Crutch:** Avoid teaching `цей` by comparing it to Russian `этот` or `той` to `тот`. While they are cognates from a common Slavic root, using Russian as the bridge reinforces a colonial linguistic dependency. Teach `цей` and `той` through their function and context within Ukrainian only.

3.  **Emphasize Native Etymology:** Briefly explain that `цей` comes from an older Ukrainian form `отъ + сей` ("lo, this"), which evolved into `отсей` and then was re-analyzed as `о-цей`, eventually yielding the standalone `цей` (Джерело: `ext-istoria_movy-103`). This demonstrates a clear, internal path of development for the word within the Ukrainian language itself, countering any false narrative of it being a Russian import or derivative.

4.  **Ukrainian Sentence Structure:** Stress that the omission of "to be" (`є`) in sentences like `Цей стіл червоний` is a standard feature of Ukrainian grammar. It is not an "informal" version of a structure that "should" have a verb like in Russian (`Этот стол есть красный`). This validates Ukrainian grammar on its own terms.

5.  **Stylistic Norms:** The use of demonstratives and personal pronouns (`цей`, `він`, `вона`) to avoid repeating nouns is a characteristic of good Ukrainian style, as taught in Ukrainian schools (Джерело: `4-klas-ukrmova-zaharijchuk_s0014`, `2-klas-ukrmova-bolshakova-2019-2_s0044`). It should be presented as a native stylistic device, not a calque from another language.

## Словниковий мінімум (Vocabulary Boundaries)

This vocabulary is appropriate for A1 learners when practicing demonstratives. It focuses on concrete, point-able objects found in a classroom or home.

**Іменники (Nouns):**
- ★★★ `стіл` (table) (Джерело: `ext-ulp_youtube-261`)
- ★★★ `стілець` (chair) (Джерело: `ext-ulp_youtube-261`)
- ★★★ `книга` (book)
- ★★★ `ручка` (pen) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0030`)
- ★★★ `вікно` (window) (Джерело: `ext-ulp_youtube-261`)
- ★★☆ `будинок` (house, building) (Джерело: `3-klas-ukrainska-mova-vashulenko-2020-1_s0128`)
- ★★☆ `кімната` (room) (Джерело: `ext-ulp_youtube-261`)
- ★★☆ `двері` (door - *plural only*) (Джерело: `ext-ulp_youtube-261`)
- ★★☆ `олівець` (pencil) (Джерело: `3-klas-ukrainska-mova-savchenko-2020-2_s0009`)
- ★★☆ `шафа` (wardrobe, cabinet) (Джерело: `ext-ulp_youtube-261`)
- ★☆☆ `ліжко` (bed) (Джерело: `ext-ulp_youtube-261`)
- ★☆☆ `поле` (field) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0030`)

**Прикметники (Adjectives):**
- ★★★ `новий` (new) (Джерело: `4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0065`)
- ★★★ `старий` (old) (Джерело: `6-klas-ukrmova-betsa-2023_s0113`)
- ★★★ `великий` (big)
- ★★★ `малий` (small)
- ★★☆ `червоний` (red) (Джерело: `10-klas-ukrajinska-mova-avramenko-2018_s0186`)
- ★★☆ `синій` (blue) (Джерело: `3-klas-ukrainska-mova-vashulenko-2020-1_s0128`)
- ★★☆ `жовтий` (yellow) (Джерело: `6-klas-ukrmova-betsa-2023_s0113`)
- ★★☆ `зелений` (green) (Джерело: `6-klas-ukrmova-betsa-2023_s0113`)
- ★★☆ `гарний` (good, beautiful) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0081`)

**Дієслова (Verbs):**
- ★★★ `бути` (to be)
- ★★★ `мати` (to have)
- ★★★ `бачити` (to see)
- ★★☆ `жити` (to live) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0081`)
- ★★☆ `хотіти` (to want)

## Приклади з підручників (Textbook Examples)

These exercises, adapted from Ukrainian school materials, provide a gold standard for practice activities.

1.  **Gender Sorting with Demonstratives (Джерело: `3-klas-ukrainska-mova-kravtsova-2020-1_s0062`)**
    - **Format:** Sorting task. Provide a list of nouns and three columns.
    - **Prompt:** "Розподіли іменники за родами. Запиши назви в потрібний рядок." (Distribute the nouns by gender. Write the names in the correct row.)
    - **Task:**
        - **Він, мій, цей:** `стіл`, `олівець`, `будинок`
        - **Вона, моя, ця:** `книга`, `ручка`, `шафа`
        - **Воно, моє, це:** `вікно`, `ліжко`, `поле`

2.  **Forced Choice: This vs. That (Джерело: `6-klas-ukrmova-litvinova-2023_s0280`)**
    - **Format:** Multiple choice within a sentence.
    - **Prompt:** "Прочитайте речення, обираючи правильний займенник." (Read the sentences, choosing the correct pronoun.)
    - **Task:**
        - 1. Привал буде за (цією / тією) горою. (The stop will be behind *this* / *that* mountain.)
        - 2. Мені, будь ласка, (це / те) тістечко. (For me, please, *this* / *that* pastry.)
        - 3. Візьміть (цю / ту) книгу, не пошкодуєте. (Take *this* / *that* book, you won't regret it.)

3.  **Adjective and Demonstrative Agreement (Джерело: `6-klas-ukrmova-betsa-2023_s0113`, `3-klas-ukrainska-mova-vashulenko-2020-1_s0128`)**
    - **Format:** Fill-in-the-blanks for endings.
    - **Prompt:** "Оберіть правильний варіант закінчення." (Choose the correct ending.)
    - **Task:**
        - Який? (m): `Нов__ стіл`, `цікав__ фільм`, `цей хорош__ друг` → (`-ий`, `-ий`, `-ій`)
        - Яка? (f): `Ця нов__ сукня`, `цікав__ казка` → (`-а`, `-а`)
        - Яке? (n): `Це нов__ крісло`, `цікав__ оповідання` → (`-е`, `-е`)

4.  **Text Cohesion via Pronoun Substitution (Джерело: `4-klas-ukrmova-zaharijchuk_s0014`)**
    - **Format:** Text rewriting.
    - **Prompt:** "Спишіть текст, уникаючи повторів виділених слів. Підкресліть слова, які зв’язують речення в тексті." (Rewrite the text, avoiding repetition of the highlighted words. Underline the words that connect the sentences in the text.)
    - **Original Text:** "Марусі... подарували маленький рожевий ноутбук. **Ноутбук** став для Марусі найкращим другом. **Ноутбук** зберігав маленькі таємниці дівчинки..."
    - **Expected Output:** "Марусі... подарували маленький рожевий ноутбук. **Він** став для Марусі найкращим другом. **Цей комп'ютер** зберігав маленькі таємниці дівчинки..."

## Пов'язані статті (Related Articles)

- `pedagogy/a1/noun-gender`
- `pedagogy/a1/adjective-agreement`
- `pedagogy/a1/personal-pronouns`
- `pedagogy/a2/introduction-to-cases`
- `grammar/nouns/pluralization`
</wiki_context>

## Plan References

- 
- 

</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Питальні слова (Question Words)` (~300 words)
- `## Заперечення (Negation)` (~300 words)
- `## Підсумок — Summary` (~300 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 15-25% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — explain the grammar concept once, clearly.
- EXAMPLES: Ukrainian sentences in bulleted lists (each line: Ukrainian — English gloss). Max 2-4 per rule.
- TABLES: Paradigm tables, gender sorting, vocabulary groups — all cells Ukrainian.
- PATTERN BOXES: Show transformations and rules: `книга → книги` (singular → plural).
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, or pattern boxes — never in flowing prose.
Ukrainian sentences max 10 words. Mix container types.

HARD GRAMMAR RULES (audit will reject violations):
- Max 10 words per Ukrainian sentence (STRICT — count every word)
- ONLY 1 clause per sentence (no compound sentences)
- Dative case FORBIDDEN (no мені, тобі, йому, їй, вам, їм, -ові/-еві endings)
  Exception: нам is taught as decodable vocabulary in M1 (reading drill word, not grammar)
  Exception (M15 what-i-like): Dative forms мені/тобі/йому/їй/нам/вам/їм allowed
    ONLY in the fixed construction «Мені подобається + noun/infinitive». Teach as a memorized
    chunk — do NOT explain dative case rules or paradigms.
- Instrumental case FORBIDDEN (no з другом, з мамою, -ом/-ою/-ем/-ею endings)
  Exception: M37 introduces basic Instrumental 'з' (кава з молоком)
- NO subordinate clauses: який/яка/яке, що-clause, коли, якщо, тому що, бо, щоб, поки are ALL BANNED
- Only imperfective aspect verbs
- No participles
- Allowed cases: Nominative, Accusative, Locative (from M30), Genitive (basics), Vocative

PLAN-AWARE EXEMPTIONS: The following bans are RELAXED for this module because the plan explicitly teaches these constructs: Subordinate clauses (plan teaches them). Exception: If a grammar construct appears in this module's plan grammar list or objectives, it is ALLOWED for this module.

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
  1. **A tourist asking a local for help navigating the city center**
     Speakers: Турист, Перехожий (passerby)
     Why: Question words: Де? Куди? Як? Коли? in real navigation

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

GRAMMAR CONSTRAINTS (A1.3 — Actions & Desires, M15-M21):
Present tense verbs, modals, questions, reflexives.

ALLOWED:
- Present tense conjugation (both groups: -ати and -ити)
- Modal verbs: хотіти, могти, мусити + infinitive
- Question words: Хто? Що? Де? Куди? Коли? Чому?
- Negation: не/ні
- Reflexive verbs (-ся/-сь)
- 'Мені подобається' as lexical chunk (NO dative grammar)

BANNED: Past/future tense, cases beyond nominative,
participles, passive voice, complex subordinate clauses

### Vocabulary

**Required:** хто (who), що (what), де (where), куди (where to), коли (when), чому (why), як (how), не (not), ні (no)
**Recommended:** ніхто (nobody), нічого (nothing), ніколи (never), жити (to live), розуміти (to understand), тому що (because)

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
## Діалоги (~320 words total)
- P1 (~20 words): [Introduction to the communicative goal — asking for information and setting the scene for a tourist encounter and a personal introduction.]
- Dialogue 1 (~100 words): [A tourist asking for directions using Де? Куди? Як?. Examples: "Вибачте, де центр?", "Куди іде цей автобус?", "Як пройти до парку?". Passerby answers with simple directions.]
- Dialogue 2 (~100 words): [Two students getting to know each other, extending M05 greetings with M16-M18 actions. Examples: "Хто ти? — Я студент.", "Що ти вивчаєш? — Я вивчаю історію.", "Де ти живеш? — Я живу тут.", "Коли ти працюєш? — Я працюю ввечері."]
- Dialogue 3 (~100 words): [A domestic scene focusing on the absence of things and negation. Examples: "Де моя книга? — Я не знаю.", "Хто знає? — Ніхто не знає.", "Чому ти не бачиш її? — Тому що я нічого не бачу без окулярів."]

## Питальні слова (~350 words total)
- P1 (~70 words): [Introduction to the seven essential question words: хто (who), що (what), де (where), куди (where to), коли (when), чому (why), як (how). Explain that these words usually start the sentence.]
- P2 (~80 words): [Deep dive into Хто? vs Що? for identification. Use examples: "Хто це?" (person) vs "Що це?" (object). Explain that Ukrainian uses "Який?" for "What color/kind?" and not "Що?", preventing L2 interference.]
- P3 (~90 words): [Explaining the spatial and temporal triplet: Де (location), Куди (direction), and Коли (time). Contrast static location "Де ти?" with directional motion "Куди ти йдеш?", referencing the common error of using "Where" for both in English.]
- P4 (~60 words): [Explaining Як (manner) and Чому (reason). Focus on "Як справи?" as a fixed phrase and "Чому... тому що" (Why... because) logic using "Чому ти не працюєш? — Тому що я хочу спати."]
- P5 (~50 words): [Yes/No questions through intonation and the particle "Чи". Explain that in spoken Ukrainian, we simply raise the pitch at the end: "Ти знаєш? ↑". Introduce "Чи" as a formal marker: "Чи ти знаєш?" without changing word order.]
- <!-- INJECT_ACTIVITY: quiz-question-word-choice --> [quiz, choose the right question word (Де/Що/Хто/Куди) based on the answer, 8 items]
- <!-- INJECT_ACTIVITY: match-question-answer --> [match-up, pairing questions like "Як справи?" with answers like "Добре, дякую", 6 items]

## Заперечення (~350 words total)
- P1 (~80 words): [The particle "Не" (not). Explain its position directly before the verb: "Я не знаю", "Ми не розуміємо", "Він не хоче". Emphasize that it is never separated from the verb it negates.]
- P2 (~80 words): [The word "Ні" (no). Explain its use as a standalone answer "Ні, дякую" and as a prefix for negative pronouns/adverbs: ніхто (nobody), нічого (nothing), ніколи (never), ніде (nowhere).]
- P3 (~110 words): [The rule of Double Negation. Contrast with English "I don't know anything" or "I know nothing". Explain that Ukrainian requires both the negative pronoun and the negative verb: "Я нічого не знаю" (literally: I nothing don't know). Use examples: "Ніхто не прийшов", "Ми ніколи не відпочиваємо".]
- P4 (~80 words): [L2 Error prevention: Warning against single negation and the "English logic." Explain that "Я бачу нічого" is incorrect; "нічого" must trigger "не" before the verb "я нічого не бачу".]
- <!-- INJECT_ACTIVITY: fill-in-negation-transform --> [fill-in, transforming positive sentences into negative ones (Я розумію → Я не розумію) and using double negation, 8 items]
- <!-- INJECT_ACTIVITY: quiz-double-negation --> [quiz, identifying the grammatically correct double negation sentence among distractors, 6 items]

## Підсумок (~300 words)
- P1 (~150 words): [Comprehensive recap of the seven question words and the mechanics of yes/no questions via intonation. Summary table of Negation: Не + Verb, and Ні- words + Не + Verb.]
- P2 (~150 words): [Self-check practical application as per the plan points. Respond to these prompts to verify your progress:
    1. Ask 3 questions about a friend's life using Де?, Що?, and Коли?. (e.g., Де живе твій друг?)
    2. Change "Я бачу все" (I see everything) into "I see nothing" using the double negation rule.
    3. Form a question from "Ти говориш українською" using only intonation.
    4. Explain the difference between "Де ти?" and "Куди ти йдеш?".]

Grand total: ~1320 words
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
