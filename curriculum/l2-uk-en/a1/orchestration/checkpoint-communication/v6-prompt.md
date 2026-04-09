

---

## Your Writing Identity

**You are: Lead Ukrainian Instructor.** Your persona is *The Patient Guide*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **47: Checkpoint: Communication** (A1, A1.7 [Communication]).

**Target: 1000–1500 words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block. Evaluate each section from the plan and commit to a word budget. This prevents frontloading early sections and rushing later ones.

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Summary: ~150 words
Total: 1000+ words
</pacing_plan>
```

Then begin writing the module content. Follow your own pacing plan — each section must hit its word budget (±10%).

---

## 9 Hard Rules

1. **IMMERSION TARGET: 20-35% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if immersion is outside this range. For A1 early modules, the learner cannot read Cyrillic — English must dominate. For A2+, Ukrainian must carry a significant share — add Ukrainian Reading Practice blocks, dialogues, and example paragraphs to reach the target. Too little Ukrainian fails audit just as much as too much.
2. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
3. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
4. **You are a warm, encouraging teacher.** Natural teacher phrasing ("Let us look at...", "Have you noticed...") is fine. What to AVOID: self-congratulatory openers ("Welcome to A2! Congratulations!"), gamified language ("You have unlocked...", "You now possess..."), and empty filler sentences that add words but zero information. Every sentence should teach something specific to Ukrainian.
5. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
6. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers where exercises should appear. A separate pipeline step generates the actual exercises from the plan's activity_hints.
7. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
8. **Hit the word target** — you MUST write 1000–1500 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
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
module: a1-047
level: A1
sequence: 47
slug: checkpoint-communication
version: '1.1'
title: 'Checkpoint: Communication'
subtitle: Can you address people, give instructions, and connect ideas?
focus: review
pedagogy: PPP
phase: A1.7 [Communication]
word_target: 1000
objectives:
- Use vocative to address people correctly (Олено! Тарасе! Друже!)
- Give instructions and make requests using imperative (Читай! Дайте!)
- Connect ideas with conjunctions (і, а, але, бо, тому що)
- Build complex sentences with що, де, коли
- Use holiday greetings and vocabulary in context
dialogue_situations:
- setting: 'Organizing a шкільний ярмарок (m, school fair) — delegating: Олено, принеси
    плакати (pl)! Тарасе, постав столи (pl)! Ми маємо квитки (pl) і напої (pl). Нам
    потрібні стільці, бо людей багато.'
  speakers:
  - Організатор
  - Волонтери
  motivation: Vocative + imperative + conjunctions with плакат(m), квиток(m), напій(m)
content_outline:
- section: Що ми знаємо? (What Do We Know?)
  words: 200
  points:
  - 'Self-check covering M42-M46: Can you call someone by name using vocative? (M42)
    Can you ask someone to do something? (M43) Can you connect ideas with і, а, але,
    бо? (M44) Can you build sentences with що, де, коли? (M45) Can you name Ukrainian
    holidays and greet people? (M46)'
- section: Читання (Reading Practice)
  words: 250
  points:
  - 'A short Ukrainian text using all A1.7 skills. Content: Olena calls her friend
    Taras to plan a holiday celebration. She uses vocative (Тарасе!), imperatives
    (Прийди! Принеси!), conjunctions (бо ми святкуємо, але я не знаю, коли ти вільний),
    and holiday vocabulary (Різдво, кутя, колядки). Combines all A1.7 communication
    tools in one realistic scenario.'
- section: Граматика (Grammar Summary)
  words: 200
  points:
  - 'Key patterns from A1.7: 1. Vocative: -а→-о (Олено), hard→-е (Тарасе), soft→-ю
    (Андрію) (M42) 2. Imperative: ти (читай, дай), ви (читайте, дайте) (M43) 3. Coordinating:
    і/та (and), а (contrast), але (but), бо (because) (M44) 4. Subordinating: що (that),
    де (where), коли (when) + comma (M45) 5. Holiday greetings: З + instrumental (З
    Різдвом!) (M46)'
- section: Діалог (Connected Dialogue)
  words: 200
  points:
  - 'Planning a holiday gathering: — Олено, привіт! Ти знаєш, що скоро Різдво? — Так,
    Тарасе! Я думаю, що ми можемо святкувати разом. — Добре! Скажи, коли ти вільна,
    бо я хочу запросити друзів. — Я вільна двадцять четвертого. Але я не знаю, де
    ми будемо. — Ходімо до мене! Принеси кутю, будь ласка. — Добре, принесу! І я знаю,
    де купити гарні свічки. З Різдвом! Uses vocative, imperative, conjunctions, що/де/коли,
    and holidays.'
- section: Підсумок — Summary
  words: 150
  points:
  - 'A1.7 achievement summary: You can address people properly in Ukrainian. You can
    ask people to do things, politely and informally. You can connect your ideas into
    longer, natural sentences. You can build complex sentences with що, де, коли.
    You can talk about Ukrainian holidays and congratulate people. Next: A1.8 — Past,
    Future, Graduation.'
vocabulary_hints:
  required: []
  recommended: []
activity_hints:
- type: fill-in
  focus: 'Vocative + imperative: ___(Олена), ___(читати) цей текст, будь ласка!'
  items: 8
- type: quiz
  focus: 'Choose the conjunction: Я не йду, ___ хворий. (і / а / бо / що)'
  items: 8
- type: fill-in
  focus: 'Complete complex sentences: Я знаю, ___ він тут. Скажи, ___ ти прийдеш.'
  items: 6
- type: quiz
  focus: 'Holiday match: З Різдвом! / З Великоднем! — match greeting to holiday'
  items: 8
connects_to:
- a1-048 (next module in A1.8)
prerequisites:
- a1-046 (Holidays)
grammar:
- 'Review: vocative case (M42), imperative mood (M43)'
- 'Review: coordinating conjunctions і, а, але, бо (M44)'
- 'Review: subordinating conjunctions що, де, коли (M45)'
- 'Review: holiday greetings З + instrumental (M46)'
register: розмовний
references:
- title: Synthesis of M42-M46 content
  notes: No new material — review and integration of A1.7 phase.

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
- Confirmed: різдво, кутя, колядка, вільний, святкувати, разом, двадцять, четвертий, принести, сказати, хотіти, свічка, привіт, гарний, купити, запросити, друг.
- Not found: None (all plan words verified).

## Grammar Rules
- Vocative Case: Grade 6 (betsa) §39 — І відміна тверда: -о (Олено); ІІ відміна тверда: -е (Тарасе); ІІ відміна м'яка: -ю (Андрію).
- Imperative Mood: Grade 11 (avramenko) §17 — 2nd person sing: -∅/-и (скажи, принеси); 2nd person plur: -те/-іть (скажіть, принесіть). Note: Using "давай" is a calque; use synthetic forms or "хай".
- Conjunctions: Grade 4 (varzatska) §73 — Coordinating (і, а, але, бо) and subordinating (що, де, коли) require proper comma usage before the conjunction in complex sentences.
- Holiday Greetings: Phraseological usage — "З" + Instrumental case (З Різдвом!, З Новим роком!).

## Calque Warnings
- "Давай святкувати": Calque from Russian "давай" — OK: "святкуймо" or "хотілося б святкувати".
- "Я думаю, що": Acceptable for A1, but "На мою думку" is a more authentic Ukrainian alternative.
- "Прийди до мене": OK — standard imperative (Grade 7 avramenko §35).

## CEFR Check
- різдво: A1 — OK (Core holiday vocabulary)
- свято: A1 — OK
- кутя: A1 — OK (Essential cultural term for A1.7 context)
- запросити: A2 — Above target (Consider using "покликати" for A1, but "запросити" is acceptable for a checkpoint)
- вільний: A1 — OK
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
# Knowledge Packet: Checkpoint: Communication
**Module:** checkpoint-communication | **Track:** A1

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: pedagogy/a1/checkpoint-communication.md

# Педагогіка A1: Checkpoint Communication



## Методичний підхід (Methodological Approach)

Checkpoint communication modules serve as cumulative reviews where learners integrate previously learned grammar and vocabulary into practical, goal-oriented dialogues. The pedagogical approach, as seen in Ukrainian educational materials, is heavily context-driven and functional. Dialogues are not abstract grammar drills; they model real-life situations like making plans, inviting friends, and arranging meetings (Source 1, 2, 10).

The core method is built around listening to or reading a model dialogue, then breaking it down into functional chunks. For instance, the Ukrainian Lessons Podcast (ULP) consistently presents a full dialogue first, asks comprehension questions, and only then dissects the grammar and vocabulary (Source 1, 10, 18). This "whole-to-part" approach mirrors natural language acquisition.

Ukrainian textbooks for native speakers also emphasize dialogue as a central activity. They use dialogues to introduce new concepts and then immediately ask students to analyze, transform, or role-play them (Source 7, 12, 31). The goal is active use, not passive knowledge. Exercises often involve transforming a dialogue into a monologue, which forces the learner to process and re-synthesize the information, confirming comprehension (Source 6, 12).

Greetings and politeness are foundational. Materials for both native speakers and L2 learners introduce the distinction between formal and informal address early on, using vocative case for names (`Привіт, Олю`) and polite forms for strangers or elders (`Шановний Сергію Васильовичу`) (Source 3, 7, 27). This isn't just a grammar point; it's a core element of communicative competence in Ukrainian culture.

## Послідовність введення (Introduction Sequence)

A logical sequence for an A1 learner to acquire checkpoint communication skills should build from simple exchanges to more complex negotiations.

1.  **Step 1: Basic Greetings, Farewells, and Politeness Formulas.** This is the absolute foundation.
    *   **Informal:** `Привіт!` (Hello!), `Па-па!` (Bye-bye!) (Source 1).
    *   **Formal/Neutral:** `Добрий день!` (Good day!), `До побачення!` (Goodbye!) (Source 19, 27).
    *   **Core Politeness:** `Дякую` (Thank you), `Будь ласка` (Please/You're welcome) (Source 1, 19).

2.  **Step 2: Core Status Check Questions.** The most common conversational openers.
    *   `Як справи?` (How are things?), `Як ти?` (How are you?) (Source 1, 2).
    *   Common responses: `Все добре`, `Нормально`, `Чудово` (Source 1, 2, 8).

3.  **Step 3: Making Simple, Direct Invitations.** The focus is on a clear proposal.
    *   Use of imperative or suggestive forms: `Ходімо в кіно!` (Let's go to the cinema!) (Source 20).
    *   Direct question form: `Хочеш піти зі мною?` (Do you want to go with me?) (Source 2).
    *   Initial responses: `Так, давай` (Yes, let's), `Добре` (Okay) (Source 2).

4.  **Step 4: Negotiating Time and Place.** This is the "checkpoint" skill, requiring specific grammar.
    *   Asking about time: `О котрій годині?` (At what time?) or `На котру годину?` (For what time?) (Source 1, 10).
    *   Telling time using `о` + ordinal number in the Locative case: `о третій` (at three), `о сьомій` (at seven) (Source 1, 10).
    *   Asking about place: `Де зустрінемось?` (Where will we meet?).
    *   Responding with `в/у` or `на` + Locative case: `у парку`, `на фестивалі` (Source 18).

5.  **Step 5: Simple Apologies and Explanations for Refusal.**
    *   Politely declining: `На жаль, не можу` (Unfortunately, I can't) (Source 20).
    *   Giving a simple reason: `Погано почуваюся` (I feel unwell), `Я зайнята` (I'm busy) (Source 2, 20).
    *   Simple apology: `Вибач` (Sorry - informal), `Пробач` (Forgive me) (Source 7).

6.  **Step 6: Formal vs. Informal Register.** Introduce the concept of `ти` (informal 'you') vs. `ви` (formal/plural 'you').
    *   Contrast informal `Привіт, Тарасе` with formal `Добрий день, Сергію Васильовичу` (Source 1, 3).
    *   Explain that `ви` is used with strangers, elders, and in professional contexts. Show how verb endings and pronouns change: `Хочеш?` (ти) vs. `Хочете?` (ви).

## Типові помилки L2 (Common L2 Errors)

| ❌ Помилково (Incorrect) | ✅ Правильно (Correct) | Чому (Why) |
| :--- | :--- | :--- |
| `Привіт, Оксана.` | `Привіт, Оксано!` | The **Vocative case** (`кличний відмінок`) is mandatory for direct address in Ukrainian. Ignoring it sounds abrupt and unnatural. It is a key feature of the language (Source 3, 5, 7). |
| `Зустрінемось в 7 годин.` | `Зустрінемось о сьомій годині.` | To specify a time on the hour, Ukrainian uses the preposition `о` followed by the **ordinal number** (сьома - seventh) in the **Locative case** (`о сьомій`). Using `в` (in) and a cardinal number is a direct transfer from English ("at 7") and is incorrect (Source 10, 23). |
| `Я вибачаюся.` | `Вибачте!` / `Пробачте!` / `Перепрошую!` | The reflexive form `вибачаюся` literally means "I forgive myself." It is considered incorrect and even rude in the context of an apology. The correct forms are direct commands or dedicated verbs of apology (Source 27). |
| `Скільки година?` | `Котра година?` | The standard way to ask for the time is `Котра година?` which literally means "Which hour (in order) is it?". `Скільки` (how much/many) is used for countable quantities, not for telling time (Source 10). |
| `Дякую вам.` (when `дякую` is sufficient) | `Дякую.` | While `Дякую вам` is grammatically correct for formal situations, beginners often overuse it. In many informal and service contexts, a simple `Дякую` is more natural. Over-formality can sound stiff. The choice depends on context, a nuance to be taught. <!-- VERIFY --> |
| `*Без п'яти шість.` | `За п'ять шоста.` | When telling time before the hour, Ukrainian uses constructions like `за [хвилин] [година]` (literally "[minutes] to [hour]") or `[хвилин] до [години]` ("[minutes] to [hour]"). The preposition `без` (without) is a calque from Russian and incorrect in this context (Source 23). |

## Деколонізаційні застереження (Decolonization Notes)

Teaching Ukrainian communication requires a deliberate de-linking from Russian linguistic habits, which are often mistakenly presented as a "shortcut" to learners.

1.  **The Vocative Case is Non-Negotiable and a Key Differentiator:** Russian has lost the vocative case in everyday speech, retaining it only in archaic or religious contexts. Ukrainian, however, uses it constantly and actively (`друже`, `Олено`, `пане`). Emphasize that this is a core, living feature of Ukrainian grammar, not an optional flourish. Its absence in modern Russian is a point of divergence, not a model to follow (Source 5).
2.  **Teach `Пане / Пані` as the Default Formal Address:** The use of `Пане` (Sir/Mr.) and `Пані` (Madam/Mrs./Ms.) followed by a first name or title is the standard, polite, European way of formal address in Ukrainian (Source 3). Avoid introducing the Russian-style `Ім'я + по-батькові` (Name + Patronymic) as the primary model. While patronymics are used (`Сергію Васильовичу`), they often appear in more official or older-generation contexts. The `Пан/Пані` model is more versatile, modern, and aligns Ukrainian with its Central European cultural context.
3.  **Avoid Russian Phonetic Analogies:** Do not teach Ukrainian sounds by comparing them to Russian ones (e.g., "Ukrainian `и` is like Russian `ы`"). This creates phonetic interference and hinders the development of an authentic Ukrainian accent. Teach each sound on its own terms, using minimal pair drills based on Ukrainian words.
4.  **Calques and Surzhyk:** Actively teach against common Russian calques in conversational phrases. A prime example is the incorrect use of `*Давай!` for "bye" (a Russianism) instead of the proper `Па-па` or `До побачення`. The brief should explicitly list and forbid such constructions.

## Словниковий мінімум (Vocabulary Boundaries)

This vocabulary is essential for A1 checkpoint dialogues.

**Іменники (Nouns):**
*   `друг / подруга` (friend m/f) ★★★ (Source 12, 20)
*   `день` (day) ★★★ (Source 3)
*   `година` (hour, time) ★★★ (Source 1, 10)
*   `кіно` (cinema, movie) ★★★ (Source 10, 20)
*   `фестиваль` (festival) ★★ (Source 18)
*   `кава` (coffee) ★★ (Source 18)
*   `вечірка` (party) ★★ (Source 1)
*   `час` (time) ★★ (Source 10)
*   `зустріч` (meeting) ★

**Дієслова (Verbs):**
*   `бути` (to be) ★★★
*   `мати` (to have) ★★★
*   `хотіти` (to want) ★★★ (Source 1, 2)
*   `могти` (can, to be able to) ★★★ (Source 1, 20)
*   `йти / піти` (to go) ★★★ (Source 2, 7)
*   `бачити` (to see) ★★★ (Source 1, 12)
*   `говорити` (to speak) ★★ (Source 2)
*   `зустрітися / зустрічатися` (to meet) ★★ (Source 8, 10)
*   `запросити / запрошувати` (to invite) ★★ (Source 1)
*   `прийти` (to come, arrive) ★★ (Source 1)

**Прислівники (Adverbs) & Фрази (Phrases):**
*   `добре` (good, well) ★★★ (Source 1)
*   `нормально` (normally, okay) ★★★ (Source 1)
*   `сьогодні` (today) ★★★ (Source 10)
*   `завтра` (tomorrow) ★★★ (Source 1)
*   `тут` (here) ★★
*   `там` (there) ★★ (Source 1)
*   `швидко` (quickly) ★ (Source 13)
*   `повільно` (slowly) ★ (Source 13)
*   `зараз` (now) ★★★ (Source 2, 10)
*   `разом` (together) ★★ (Source 20)

**Ключові фрази (Key Phrases):**
*   `Як справи?` (How are things?) ★★★
*   `Що нового?` (What's new?) ★★★ (Source 18)
*   `О котрій годині?` (At what time?) ★★★ (Source 10)
*   `До зустрічі.` (See you later.) ★★★ (Source 18)
*   `На все добре.` (All the best / Goodbye) ★★ (Source 19)

## Приклади з підручників (Textbook Examples)

1.  **Dialogue Completion and Role-Play (Source 22, 31):** This exercise format requires active production and understanding of conversational flow.
    *   **Prompt:** *Побудуйте діалог за зразком. Розіграйте діалог із сусідом / сусідкою за партою.* (Construct a dialogue based on the model. Act out the dialogue with your deskmate.)
    *   **Example Model:**
        — Як тебе звуть?
        — Мене звуть … .
        — Як твоє прізвище?
        — Моє прізвище … .
    *   **Pedagogical Value:** This simple format is easily adaptable for arranging a meeting. E.g., "— Ходімо в кіно. О котрій годині? — ...". It moves from controlled practice to free production.

2.  **Dialogue Punctuation and Analysis (Source 7):** This focuses on the written conventions of dialogue, especially the vocative case comma.
    *   **Prompt:** *Перепишіть діалог, розставляючи пропущені розділові знаки. Хто з подружок порушив етикет у спілкуванні?* (Rewrite the dialogue, inserting the missing punctuation marks. Which of the friends violated etiquette in the conversation?)
    *   **Example Text:** `— Алло! Привіт Олю привіталася Оксана.` (Needs comma after `Привіт` and `Олю`).
    *   **Pedagogical Value:** This connects the grammatical rule (vocative case) to its function in polite communication and its visual representation in text. It also introduces the meta-level of analyzing social appropriateness.

3.  **Dialogue Transformation (Source 12):** This task tests deep comprehension by forcing a change in perspective.
    *   **Prompt:** *Трансформуйте діалог у монолог і перекажіть його від імені: А. Давида (від першої особи); Б. Оксани (від третьої особи).* (Transform the dialogue into a monologue and retell it from the perspective of: A. David (first person); B. Oksana (third person).)
    *   **Pedagogical Value:** A learner cannot complete this without fully understanding who said what and what the overall context is. It's an excellent comprehension check for a checkpoint module.

4.  **Functional Questions about a Dialogue (Source 1, 10, 18):** A straightforward and effective way to check listening or reading comprehension.
    *   **Prompt:** *Слухайте діалог і дайте відповідь на запитання: Коли буде вечірка?* (Listen to the dialogue and answer the question: When will the party be?) (Source 1). *Що вони будуть робити?* (What are they going to do?) (Source 10).
    *   **Pedagogical Value:** It anchors the learning purpose. The learner is listening not just to words, but for specific, functional information needed to answer the question, mimicking real-life listening.

## Пов'язані статті (Related Articles)
- `pedagogy/a1/telling-time`
- `grammar/a1/vocative-case`
- `grammar/a1/locative-case`
- `grammar/a1/ordinal-numbers`
- `culture/etiquette-formal-informal`

---

### Вікі: pedagogy/a1/checkpoint-first-contact.md

# Педагогіка A1: Checkpoint First Contact



## Методичний підхід (Methodological Approach)

The Ukrainian pedagogical approach to teaching initial introductions is fundamentally communicative and context-driven. Even from the first lesson, the goal is to enable a learner to participate in a simple, formulaic dialogue (`діалог`). The core concepts of **ім'я** (first name), **прізвище** (surname), and **по батькові** (patronymic) are introduced as functional chunks of language needed to complete a real-world task, such as introducing oneself or filling out a simple form (Джерело: `4-klas-ukrayinska-mova-varzatska-2021-1_s0159`, `6-klas-ukrmova-zabolotnyi-2020_s0032`).

Ukrainian textbooks for early grades (1-2) establish this pattern by immediately presenting model dialogues. They use a "question-and-answer" format that is easy to memorize and adapt (Джерело: `5-klas-ukrmova-uhor-2022-1_s0107`, `6-klas-ukrmova-betsa-2023_s0014`). For example, the structure `— Як тебе звуть? — Мене звуть ... .` is presented as a fixed pair to be practiced with a partner (`Розіграйте діалог із сусідом / сусідкою за партою`) (Джерело: `6-klas-ukrmova-betsa-2023_s0014`).

Key methodological principles are:
1.  **Dialogue First:** The primary mode of instruction is the dialogue or poly-dialogue (`полілог`), where students learn by playing roles in a given situation (`Ситуація`) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0106`, `5-klas-ukrmova-avramenko-2022_s0011`). This makes the language immediately useful.
2.  **Structural Repetition:** Core phrases like `Мене звати...` and `Моє прізвище...` are drilled through repetition, not grammatical analysis at first. The focus is on automaticity. (Джерело: `5-klas-ukrmova-uhor-2022-1_s0106`).
3.  **Immediate Introduction of Capitalization:** From the outset, learners are shown that names, patronymics, and surnames are proper nouns written with a capital letter (`пишуть з великої літери`) (Джерело: `2-klas-ukrmova-kravcova-2019-1_s0070`, `2-klas-ukrmova-bolshakova-2019-2_s0023`). This is treated as a fundamental orthographic rule, not an advanced topic.
4.  **Implicit Grammar:** The accusative case in `Мене звати...` and the vocative case in direct address (`Оксано!`) are introduced implicitly through model phrases. Formal grammatical explanation is delayed until the learner is comfortable with the functional use of the phrases (Джерело: `5-klas-ukrmova-uhor-2022-1_s0106`, `6-klas-ukrmova-litvinova-2023_s0148`).

## Послідовність введення (Introduction Sequence)

The introduction of "first contact" language should follow a logical progression from simple to complex, mirroring the approach in Ukrainian native-speaker textbooks.

1.  **Step 1: Foundational Phrases & Pronouns.** Start with greetings (`Добрий день!`) and the core construction `Мене звати...` (My name is...). This immediately introduces the personal pronoun in the accusative case (`мене`) in a fixed, unanalyzed chunk (Джерело: `5-klas-ukrmova-uhor-2022-1_s0106`). Contrast `Як тебе звати?` (informal 'you') with `Як вас звати?` (formal/plural 'you').

2.  **Step 2: Adding the Surname.** Introduce the concept of `прізвище` (surname) with the parallel construction `Моє прізвище...` (My surname is...). Practice this in a simple dialogue format (Джерело: `6-klas-ukrmova-betsa-2023_s0014`, `5-klas-ukrmova-uhor-2022-1_s0107`). At this stage, learners practice asking and answering both questions in a sequence.

3.  **Step 3: The Vocative Case (Кличний відмінок) for Direct Address.** This is a critical element of natural Ukrainian speech and must be introduced early. Instead of just saying a name, learners must be taught to use the vocative form to call someone.
    *   For feminine names ending in `-а`, it changes to `-о`: `Анна → Анно!`, `Оксана → Оксано!` (Джерело: `6-klas-ukrmova-litvinova-2023_s0148`).
    *   For masculine names ending in a consonant, it changes to `-е`: `Тарас → Тарасе!`, `Павло → Павле!` (Джерело: `6-klas-ukrmova-litvinova-2023_s0148`).
    *   Introduce formal address with `пан/пані`: `пане Іваненку`, `пані Оксано` (Джерело: `6-klas-ukrmova-litvinova-2023_s0148`). This immediately elevates the learner's politeness and authenticity.

4.  **Step 4: Introducing the Patronymic (По батькові).** Explain that `по батькові` is a name derived from one's father's name and is used in formal or respectful situations. Show the full formal structure: `Прізвище, Ім’я, По батькові` (Джерело: `2-klas-ukrmova-bolshakova-2019-2_s0023`). Explain the common suffixes: `-ович` (masculine) and `-івна` (feminine) (Джерело: `6-klas-ukrmova-betsa-2023_s0016`). The goal at A1 is recognition, not productive use. Learners should understand what it is when they see it on a form or hear it in a formal introduction.

5.  **Step 5: Contextual Application.** Embed these skills in practical scenarios like booking a table (`Скажіть будь ласка ваше прізвище`) or making a doctor's appointment (`ваше прізвище ім'я і номер телефону будь ласка`) (Джерело: `ext-ulp_youtube-120`, `ext-ulp_youtube-58`). This reinforces the utility of the language.

## Типові помилки L2 (Common L2 Errors)

English speakers often make predictable errors when learning to introduce themselves. The curriculum should proactively address these.

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| `Я звати Анна.` | `Мене звати Анна.` | This is a direct translation of "I am called Anna." English speakers must learn the fixed Ukrainian construction which uses the accusative pronoun `мене` (me). (Джерело: `5-klas-ukrmova-uhor-2022-1_s0106`) |
| `Привіт, Марія.` | `Привіт, Маріє!` | Forgetting the vocative case (`Кличний відмінок`) in direct address. It sounds unnatural and blunt to a native speaker. The ending must change (`-ія` -> `-іє`, `-а` -> `-о`, consonant -> `-е`). (Джерело: `6-klas-ukrmova-litvinova-2023_s0148`) |
| `Моє ім'я є Тарас.` | `Моє ім'я — Тарас.` or `Мене звати Тарас.` | Overuse of the verb `бути` (`є`) where it's typically omitted in the present tense for identity statements. The dash (`—`) is the correct punctuation, or the `Мене звати` structure should be used. <!-- VERIFY --> |
| `Прізвище моє Ковальчук.` | `Моє прізвище — Ковальчук.` | Unnatural word order based on English. While grammatically possible, the standard, neutral response is `Моє прізвище...` (Джерело: `5-klas-ukrmova-uhor-2022-1_s0106`). |
| "What is your middle name?" (asking about `по батькові`) | "Як вас по батькові?" | Equating the patronymic with an Anglo-American "middle name." A middle name is a second personal name; a patronymic is a grammatical and cultural construct derived from the father's name. This distinction is crucial. (Джерело: `2-klas-ukrmova-bolshakova-2019-2_s0023`) |
| `Пан Шевченко...` (when ordering should be name first) | `Пан Тарас...` | In many formal contexts, the correct address is `пан/пані` + First Name. However, in official documents, it is always Last Name first (`прізвище, ім'я`) (Джерело: `11-klas-ukrajinska-mova-avramenko-2019_s0278`, `9-klas-ukrajinska-mova-avramenko-2017_s0211`). The brief should clarify the context. |

## Деколонізаційні застереження (Decolonization Notes)

Teaching Ukrainian from a decolonized perspective is non-negotiable. This is especially important in foundational topics where Russian-centric habits can form.

1.  **Teach Ukrainian on Its Own Terms:** Never introduce Ukrainian letters or sounds as "like the Russian X." Learners must build a clean Ukrainian phonetic and orthographic foundation from zero. Russian has different letters (e.g., `ы`, `э`) and different pronunciations for shared letters (e.g., `и`, `г`). Using Russian as a reference point pollutes the learning process from day one.
2.  **Patronymics are East Slavic, Not Russian:** Explicitly state that patronymics (`по батькові`) are a feature of Ukrainian, Belarusian, and Russian cultures. Frame it as a shared heritage, not a Russian import. Highlight the distinct Ukrainian suffixes (`-ович`, `-івна`) as seen in textbooks (Джерело: `6-klas-ukrmova-betsa-2023_s0016`).
3.  **Correct Transliteration:** Emphasize the official Ukrainian transliteration system (and the common informal one) which differs from Russian. Key examples: `Г` is `H`, not `G`; `И` is `Y`, not `I`; `І` is `I`. This prevents learners from writing Ukrainian names with Russian spelling conventions.
4.  **Surname Origins:** When discussing surnames, highlight authentic Ukrainian origins related to professions (`Коваль`, `Бондар`, `Гончар`), features, or Cossack history, not just those shared with Russian (Джерело: `2-klas-ukrmova-bolshakova-2019-2_s0025`, `3-klas-ukrainska-mova-vashulenko-2020-2_s0158`).

## Словниковий мінімум (Vocabulary Boundaries)

This vocabulary is the absolute essential minimum for the "First Contact" module.

*   **Іменники (Nouns):**
    *   ім'я ★★★ (first name)
    *   прізвище ★★★ (surname)
    *   по батькові ★★ (patronymic)
    *   учень / учениця ★★★ (student m/f)
    *   вчитель / вчителька ★★★ (teacher m/f)
    *   друг / подруга ★★ (friend m/f)
    *   пан / пані / панно ★★★ (Mr. / Mrs. / Miss)
    *   номер (телефону) ★★ (phone number)
*   **Дієслова (Verbs):**
    *   звати ★★★ (to be called)
    *   бути ★★★ (to be - often omitted in present)
    *   знати ★★ (to know)
    *   жити ★ (to live)
*   **Займенники (Pronouns):**
    *   я, ти, він, вона, ми, ви, вони ★★★ (Nominative: I, you, he, she, etc.)
    *   мене, тебе, його, її, нас, вас, їх ★★★ (Accusative: me, you, him, her, etc.)
    *   мій/моя/моє, твій/твоя/твоє ★★★ (my, your)
*   **Ключові фрази (Key Phrases):**
    *   Добрий день. / Привіт. ★★★
    *   Як тебе/вас звати? ★★★
    *   Мене звати... ★★★
    *   Як твоє/ваше прізвище? ★★★
    *   Моє прізвище... ★★★
    *   Дуже приємно. / Радий (рада) знайомству. ★★
    *   Так / Ні ★★★

## Приклади з підручників (Textbook Examples)

These exercises are models for the content writer, demonstrating the native Ukrainian pedagogical methodology.

1.  **Basic Dialogue Completion (from Source `6-klas-ukrmova-betsa-2023_s0014`)**
    *   **Task:** Побудуйте діалог за зразком. Запишіть. Розіграйте діалог із сусідом / сусідкою за партою.
    *   **Model:**
        > — Як тебе звуть?
        > — Мене звуть … .
        > — Як твоє прізвище?
        > — Моє прізвище … .
    *   **Pedagogical Value:** This simple, repetitive task builds automaticity for the most fundamental introductory exchange. It encourages active, paired practice.

2.  **Identifying Name Components (from Source `5-klas-ukrmova-uhor-2022-1_s0107`)**
    *   **Task:** Уточніть, де ім’я, де по батькові, де прізвище.
    *   **Model:**
        > — Франко — це ім’я?
        > — Ні, це прізвище. Його звати Іван Якович.
    *   **Pedagogical Value:** This exercise moves from simple production to comprehension and analysis. It teaches learners to differentiate between the three components of a full formal name and introduces the structure `Його звати...`.

3.  **Table Fill-in (from Source `2-klas-ukrmova-bolshakova-2019-2_s0023`)**
    *   **Task:** Заповни таблицю за зразком.
    *   **Input:** `Григоренко Святослав Андрійович, Телюк Наталія Григорівна, Шевченко Тарас Григорович.`
    *   **Table Structure:**
| Прізвище | Ім’я | По батькові |
| :--- | :--- | :--- |
| Бондар | Лариса | Вікторівна |
    *   **Pedagogical Value:** This is a classic exercise for reinforcing the structure and order of formal Ukrainian names and practicing reading/writing them correctly.

4.  **Contextual Role-Play (from Source `6-klas-ukrmova-zabolotnyi-2020_s0032`)**
    *   **Task:** Складіть діалог (6–8 реплік) в офіційно-діловому стилі... Ви прийшли записатися до бібліотеки. Повідомте мету свого візиту, а також на прохання бібліотекарки – своє прізвище та ім’я, дату народження, місце проживання (для оформлення картки читача).
    *   **Pedagogical Value:** This places the language skill in a highly realistic, official context (`офіційно-діловий стиль`). It moves beyond simple introductions to a multi-turn conversation where personal information is requested and provided for a clear purpose. This demonstrates the practical value of what has been learned.

## Пов'язані статті (Related Articles)

- `pedagogy/a1/alphabet`
- `pedagogy/a1/greetings-and-farewells`
- `grammar/nouns/vocative-case`
- `grammar/pronouns/personal-pronouns`
- `culture/names-and-address`
</wiki_context>

## Plan References

- 

</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Що ми знаємо? (What Do We Know?)` (~200 words)
- `## Читання (Reading Practice)` (~250 words)
- `## Граматика (Grammar Summary)` (~200 words)
- `## Діалог (Connected Dialogue)` (~200 words)
- `## Підсумок — Summary` (~150 words)

Each section should follow the word budget specified. The total must reach 1000 words minimum.

---

## Content Rules

TARGET: 20-35% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — brief and clear. Show, don't tell.
- PARADIGM TABLES: Conjugation/declension tables with all cells Ukrainian.
- EXAMPLE LISTS: Ukrainian sentences in bulleted lists (each: Ukrainian — English gloss).
- DIALOGUES: Mini-dialogues in blockquotes with English gloss per line.
- PATTERN BOXES: Show transformations: `читати → читай → читайте`.
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, dialogues, or pattern boxes.
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

PLAN-AWARE EXEMPTIONS: The following bans are RELAXED for this module because the plan explicitly teaches these constructs: Instrumental case (plan teaches it), Subordinate clauses (plan teaches them), Perfective aspect (plan teaches perfective verbs). Exception: If a grammar construct appears in this module's plan grammar list or objectives, it is ALLOWED for this module.

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
  1. **Organizing a шкільний ярмарок (m, school fair) — delegating: Олено, принеси плакати (pl)! Тарасе, постав столи (pl)! Ми маємо квитки (pl) і напої (pl). Нам потрібні стільці, бо людей багато.**
     Speakers: Організатор, Волонтери
     Why: Vocative + imperative + conjunctions with плакат(m), квиток(m), напій(m)

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

GRAMMAR CONSTRAINTS (A1.7 — People & Communication, M44-M50):
Vocative, imperative, dative, conjunctions, subordinate clauses.

ALLOWED:
- Vocative case (Олено! Тарасе!)
- Imperative mood (Читай! Скажіть! Дайте!)
- Dative case basics (мені, тобі, йому)
- Conjunctions (і, а, але, бо, тому що)
- Simple subordinate clauses (що, де, коли, якщо)
- All cases and tenses from previous phases

BANNED: Past/future tense, participles, passive voice

### Vocabulary



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
## Що ми знаємо? (~220 words total)
- P1 (~100 words): Welcome the student to the A1.7 Checkpoint. Explain that this module is a "Communication Hub" where we integrate the social skills learned in M42–M46. Introduce the "Mission": You are helping friends organize a school event, which requires addressing people, giving clear orders, and explaining plans.
- P2 (~120 words): A series of rhetorical self-check questions to activate prior knowledge. Ask the learner if they remember how to call a friend (Тарасе! Олено!), how to ask for help (Дай! Принеси!), and how to explain reasons (бо я не знаю..., тому що...). Mention the cultural context of holiday greetings (З Різдвом!).

## Читання (~270 words total)
- P1 (~100 words): Introduction to the reading text. Set the scene: Olena is calling her friend Taras to plan a community Christmas gathering at the school. This text will demonstrate how all communication tools (vocative, imperative, conjunctions) work together in a single flow.
- P2 (~170 words): The Reading Text: "Лист або дзвінок Олени". Olena writes/speaks to Taras. Key sentences: "Тарасе, привіт! Прийди раніше, будь ласка. Принеси плакати і квитки. Я знаю, що ти маєш напої, але нам потрібні стільці, бо людей буде багато. Я хочу, щоб ми святкували Різдво разом. Скажи, коли ти будеш у школі." Includes vocabulary: плакат (poster), квиток (ticket), напій (drink), стілець (chair).

## Граматика (~240 words total)
- P1 (~60 words): Vocative Case Recap. Review the three main patterns for A1 names: -а becomes -о (Оксано, Олено), hard consonants add -е (Петре, Тарасе, друже), and soft/й endings change to -ю (Андрію, матусю). Emphasize that in Ukraine, calling someone by their name in the Nominative (Оксана!) sounds like a command or a list, whereas the Vocative is for real communication.
- P2 (~60 words): Imperative Mood Recap. Review forms for "ти" (читай, пиши, роби) and "ви" (читайте, пишіть, робіть). Remind learners to add "будь ласка" (please) for politeness. Contrast the informal "Дай" with the formal "Дайте".
- <!-- INJECT_ACTIVITY: vocative-imperative-practice --> [fill-in, focus: Vocative + Imperative forms in a school fair context, 8 items]
- P3 (~60 words): Conjunctions & Linking. Review the coordinating conjunctions: і/та (addition), а (mild contrast/and), але (strong contrast/but), and бо/тому що (reason/because). Explain when to use "а" (e.g., Мій чай гарячий, а твій холодний).
- <!-- INJECT_ACTIVITY: conjunctions-quiz --> [quiz, focus: Choosing the correct conjunction (і / а / але / бо), 8 items]
- P4 (~60 words): Complex Sentences with що, де, коли. Review how these words link a main clause to a sub-clause. CRITICAL: Reiterate the rule about the mandatory comma before these conjunctions in Ukrainian. Examples: "Я думаю, що..." (I think that...), "Вона знає, де..." (She knows where...), "Скажи, коли..." (Tell [me] when...).
- <!-- INJECT_ACTIVITY: complex-sentences-fill-in --> [fill-in, focus: Completing sentences with що, де, or коли, 6 items]

## Діалог (~240 words total)
- P1 (~60 words): Context for the dialogue. Taras and Olena are finalizing their plans for the holiday gathering. They need to confirm the time, place, and what to bring.
- P2 (~120 words): The Dialogue: "Різдвяні плани". 
    — Олено, привіт! Ти знаєш, що скоро Різдво?
    — Так, Тарасе! Я думаю, що ми можемо святкувати разом.
    — Добре! Скажи, коли ти вільна, бо я хочу запросити друзів.
    — Я вільна двадцять четвертого. Але я не знаю, де ми будемо.
    — Ходімо до мене! Принеси кутю, будь ласка.
    — Добре, принесу! І я знаю, де купити гарні свічки. З Різдвом!
- P3 (~60 words): A brief cultural note on holiday greetings. Explain the formula "З + Instrumental case" (З Різдвом, З Великоднем, З Новим роком). Mention that responding with "Навзаєм!" (Likewise!) or "Вас також!" (You too!) is standard.
- <!-- INJECT_ACTIVITY: holiday-greeting-match --> [quiz, focus: Matching the specific greeting to the holiday (e.g., З Різдвом! -> 7 січня), 8 items]

## Підсумок (~150 words)
- P1 (~150 words): Achievement checklist for phase A1.7 Communication.
    - You can address people correctly using the vocative case (Олено! Тарасе!).
    - You can give instructions and make requests using the imperative mood (Читай! Дайте!).
    - You can connect your ideas into longer sentences using conjunctions (і, а, але, бо).
    - You can build complex sentences with the words що, де, коли (and you remember the comma!).
    - You know how to greet people for major Ukrainian holidays using the Instrumental case.
    Next: A1.8 — The final stage of A1, where we tackle the Past and Future tenses!

Grand total: ~1120 words
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
