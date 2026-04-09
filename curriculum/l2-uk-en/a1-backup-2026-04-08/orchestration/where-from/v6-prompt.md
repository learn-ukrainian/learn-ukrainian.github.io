

---

## Your Writing Identity

**You are: Patient & Supportive Ukrainian Tutor.** Your persona is *The Helpful Teacher*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **34: Where From?** (A1, A1.5 [Places]).

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

1. **IMMERSION TARGET: 15-30% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if you exceed it. For early modules, the learner CANNOT READ CYRILLIC — English must dominate. Ukrainian appears only as bolded inline words/phrases. Do NOT write long Ukrainian passages, Ukrainian-only paragraphs, or Ukrainian text without English translation.
2. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
3. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
4. **NO "In this lesson we will..."** — never use formulaic openers. Start with a dialogue, a question, or a situation.
5. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
6. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers where exercises should appear. A separate pipeline step generates the actual exercises from the plan's activity_hints.
7. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
8. **Hit the word target** — you MUST write 1200–1800 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
9. **NO archaic, obsolete, or rare words** — use only modern standard Ukrainian. Do not use words marked as archaic (застаріле) or dialectal in dictionaries. Example: use «кін» not «кон», use «пом'якшені» not «м'якшені». When in doubt, choose the common modern form. Your pre-training contains Russian-influenced archaic forms — verify unfamiliar words.

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
module: a1-034
level: A1
sequence: 34
slug: where-from
version: '1.2'
title: Where From?
subtitle: Звідки ти? Я з України — origins and directions
focus: communication
pedagogy: PPP
phase: A1.5 [Places]
word_target: 1200
objectives:
- Ask and answer Звідки? (Where from?) using з/із + country/city
- Name Ukrainian cities and common countries
- Complete the location trio: Де? / Куди? / Звідки?
- Talk about origins, nationality, and travel history
dialogue_situations:
- setting: 'International student mixer at a Kyiv university — sharing origins: Я
    з Канади, Вона з Японії, Він з Німеччини. Also: З якого міста? З Торонто, з Токіо,
    з Берліна.'
  speakers:
  - Кілька студентів (group)
  motivation: 'Звідки? + з: Канада(f), Японія(f), Німеччина(f), Торонто(n)'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Meeting someone (extending M05, ULP Ep4): — Звідки ти? — Я з України,
    з Києва. А ти? — Я з Канади, із Торонто. — Давно тут? — Ні, я приїхав місяць тому.
    Звідки? pattern with countries and cities.'
  - 'Dialogue 2 — Coming from somewhere: — Звідки ти йдеш? — Я йду з роботи. — А Олена?
    — Вона йде зі школи. — Куди вона йде? — Додому. Direction FROM (з + genitive chunk)
    vs TO (в/на + accusative).'
- section: Звідки? (Where From?)
  words: 300
  points:
  - 'Three direction questions complete: Де ти? — В Україні. (locative — where you
    ARE) Куди ти їдеш? — В Україну. (accusative — where you''re GOING) Звідки ти?
    — З України. (genitive — where you''re FROM) At A1: learn з + country/city as
    chunks. Genitive grammar = A2.'
  - 'Pattern: з/із/зі + genitive (memorized forms): з України, з Києва, зі Львова,
    з Одеси, з Харкова. з Канади, зі США (зі Штатів), з Англії, з Німеччини, з Польщі.
    з роботи, зі школи, з магазину, з банку. Note: euphony rules from M28 apply: з/із/зі.'
- section: Країни і міста (Countries and Cities)
  words: 300
  points:
  - 'Ukrainian cities: Київ (Kyiv), Львів (Lviv), Одеса (Odesa), Харків (Kharkiv),
    Дніпро (Dnipro), Запоріжжя (Zaporizhzhia). Countries (common for learners): Україна,
    Канада, США, Англія, Німеччина, Польща, Франція, Італія, Японія.'
  - 'Nationality and language links: Я з України → Я українець/українка → Я говорю
    українською. Review from M05: Мене звати..., Я з..., Я говорю... New: Я живу в
    Києві, але я зі Львова. (current location vs origin)'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Three location questions: Де? → в/на + locative (В Україні) Куди? → в/на + accusative
    (В Україну) Звідки? → з/із/зі + genitive chunk (З України) Self-check: Where are
    you from? Where do you live now? Where are you going after this lesson?'
vocabulary_hints:
  required:
  - звідки (where from)
  - з/із/зі (from — + genitive chunk)
  - Україна (Ukraine)
  - Київ (Kyiv)
  - Львів (Lviv)
  - Канада (Canada)
  recommended:
  - Одеса (Odesa)
  - Харків (Kharkiv)
  - США (USA)
  - Англія (England)
  - Німеччина (Germany)
  - Польща (Poland)
  - додому (home — direction)
activity_hints:
- type: fill-in
  focus: Answer Звідки? using з/із/зі + memorized genitive chunks
  items: 8
  blanks:
  - Звідки ти? — Я {з України}.
  - Вона {з Канади}.
  - Ми {з Києва}, а ви?
  - Джон {зі США}.
  - Мій друг {з Німеччини}.
  - Я {зі Львова}.
  - Вони {з Англії}.
  - Олена {з Одеси}.
- type: group-sort
  focus: Categorize phrases into Де? (Locative), Куди? (Accusative), Звідки? (Genitive)
  items: 9
  groups:
  - name: Де? (Where?)
    items:
    - в Україні
    - в Києві
    - на роботі
  - name: Куди? (Where to?)
    items:
    - в Україну
    - в Київ
    - на роботу
  - name: Звідки? (Where from?)
    items:
    - з України
    - з Києва
    - з роботи
- type: quiz
  focus: Choose correct preposition (в/на/з) for location/direction
  items: 8
  questions:
  - Я йду... роботи. (з / на / в)
  - Вона йде... школу. (в / на / зі)
  - Ми зараз... Україні. (в / з / на)
  - Я їду... Канаду. (в / з / на)
  - Він... Німеччини. (з / в / на)
  - Вони... Львові. (у / зі / на)
  - Я йду... магазину. (з / в / на)
  - Олена... школи. (зі / в / на)
- type: fill-in
  focus: Contrast current location (в/на) and origin (з/із)
  items: 6
  blanks:
  - Я живу {в Києві}, але я {зі Львова}.
  - Вона живе {в Канаді}, але вона {з України}.
  - Ми зараз {в Англії}, але ми {з Польщі}.
  - Він живе {в Одесі}, але він {з Харкова}.
  - Я {з Німеччини}, але зараз я {в Україні}.
  - Ти {зі США}, але живеш {у Києві}.
connects_to:
- a1-035 (Checkpoint — Places)
prerequisites:
- a1-033 (Around the City)
grammar:
- Звідки? + з/із/зі + genitive (memorized chunks)
- 'Location trio: Де? (M.в.) / Куди? (Зн.в.) / Звідки? (Р.в. chunk)'
- Country/city names in three case forms
register: розмовний
references:
- title: ULP Season 1, Episode 4
  url: https://www.ukrainianlessons.com/episode4/
  notes: Where are you from? — nationalities and countries.

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

**Batch 1 — Plan vocabulary (15 words):**
- Confirmed: звідки (adv), з (prep), із (prep), зі (prep), Україна (noun), Київ (noun), Львів (noun), Канада (noun), Одеса (noun), Харків (noun), США (noun), Англія (noun), Німеччина (noun), Польща (noun), додому (adv)
- Not found: — (all 15 confirmed ✅)

**Batch 2 — Section content vocabulary (10 words):**
- Confirmed: Дніпро (noun), Запоріжжя (noun), Франція (noun), Японія (noun), Італія (noun), українець (noun), українка (noun), магазин (noun), банк (noun), місяць (noun)
- Not found: — (all 10 confirmed ✅)

**Total: 25/25 VESUM confirmed. Zero failures.**

---

## Textbook Excerpts

### Section: Звідки? (Where From?) — The three direction questions
> "Підрядна частина місця відповідає на питання: де? куди? звідки? З'єднується з головною за допомогою сполучних слів де, куди, звідки"
>
> Source: Заболотний, Grade 9 (tier 2)

> "Обставина місця — місце дії, напрямок руху — питання де? куди? звідки?" (full table of обставина types)
>
> Source: Авраменко, Grade 8 (tier 1 — priority)

**Pedagogical note:** The де/куди/звідки triad is taught together as a systematic set in Ukrainian grammar. The plan's presentation of all three as a summary triangle (Де? → locative / Куди? → accusative / Звідки? → genitive) is fully aligned with how textbooks present these.

---

### Section: Діалоги — Natural z roboty / zi shkoly usage
> "Прийшла з роботи мама. І з вітальні – прямо на кухню, швидше поставити важкі сумки."
>
> Source: Заболотний/Заболотній, Grade 9 (both tier 2 versions)

**Verdict:** «З роботи» is confirmed natural, textbook-attested Ukrainian. Pattern «з роботи / зі школи / з магазину» is fully natural.

---

### Section: Країни і міста (Countries and Cities)
> "Назви країн, міст, сіл, річок пишуться з великої букви. Україна — моя Батьківщина. Столиця України — місто Київ. Київ розташований на берегах річки Дніпро."
>
> Source: Большакова, Grade 2 (tier 2 — priority author)

> "Запишіть назви країн Європи за алфавітом: Україна, Німеччина, Австрія, Польща, Чехія, Словаччина. Запиши назви українських міст в алфавітній послідовності: Київ, Харків, Запоріжжя, Львів, Берлін, Одеса, Вінниця."
>
> Source: Вашуленко, Grade 2 (tier 2 — priority author)

> "Київ — киянин, Харків — харків'янин, Суми — сумчанин, Донецьк — донеччанин, Львів — львів'янин."
>
> Source: Вашуленко, Grade 2 (tier 2)

**Verdict:** Exactly the cities and countries in the plan appear in priority-author textbooks at Grade 2. Strong pedagogical grounding. The nationality links (Я з України → я українець/українка) are also found in Вашуленко.

---

### Section: з/із/зі euphony rule (feeds into all Звідки? patterns)
> Full rule table:
> - **з** — before a word starting with a vowel (з Одеси, з однокласницями) OR before a consonant when the cluster is pronounceable
> - **із** — between consonants; before з, с, ц, ж, ч, ш; "між приголосними: Максим із Семеном"
> - **зі** — before a consonant cluster where the first consonant is з, с, ш: зі школи, зі Львова, зі Штатів, бери зі столу
>
> Source: Литвинова, Grade 5 (tier 1 — priority); Заболотний, Grade 5 (tier 1 — priority)

**Chunk-form verification from textbooks:**
- з України ✅ (before vowel У)
- з Києва ✅ (before К — pronounceable)
- зі Львова ✅ (before лв- cluster, confirmed in Litvinova: "прибув зі Львова")
- з Одеси ✅ (Правопис example: "в Одесі" → з + О = з Одеси, before vowel)
- з Харкова ✅ (before Х — pronounceable)
- з Канади ✅ (before К)
- зі США / зі Штатів ✅ (before Ш-sibilant cluster)
- з Англії ✅ (before А — vowel)
- з Німеччини ✅ (before Н)
- з Польщі ✅ (before П)
- з роботи ✅ (before Р)
- зі школи ✅ (before шк- cluster with sibilant first, Litvinova example: "повернутися із школи" / "вийшли зі школи")
- з магазину ✅ (before М)
- з банку ✅ (before Б)

---

## Grammar Rules

- **з/із/зі alternation (milozwuchnist'):** No standalone Правопис §number — this rule parallels §23 (у/в euphony). Confirmed in Grade 10, Karaman: *"Варіанти прийменника з–із–зі (зо) чергуються на такій же підставі, що й в–у, і–й"* (the same euphony principle as §23). Full rule table: Grade 5 Litvinova §290 and Grade 5 Zabotnyi §30.
- **Capital letters for country/city names:** Правопис §37 (Велика літера у власних назвах). Confirmed in Большакова Grade 2: *"Назви країн, міст, сіл, річок пишуться з великої букви."*
- **Genitive with з (звідки chunk):** The plan correctly labels these as **memorized genitive chunks** at A1 (з України, з Києва etc.) — genitive as a full paradigm belongs to A2. This is the correct scope. Textbook grounding: Avramenko Grade 6 §51 shows genitive of city names (Київ → Києва, Львів → Львова) — exactly the forms in the plan.

---

## Calque Warnings

- **«я приїхав місяць тому»** — OK, natural Ukrainian. Антоненко-Давидович attests «місяць» in temporal phrases as natural. «Тому» as a postposition for past time is standard Ukrainian.
- **«з роботи / зі школи / додому»** — OK, fully natural. Textbook-attested (Zabolotnyi Grade 9: "Прийшла з роботи мама"). No calque.
- **«Давно тут?»** (Dialogue 1) — OK, natural Ukrainian colloquial ellipsis. No calque. <!-- VERIFY stress on «давно́» at goroh.pp.ua before writing -->
- **«іду з роботи»** — Антоненко-Давидович style guide: no issue found. «Іду з роботи» (I'm walking from work) is natural; contrast with potential Russian calque «іду з роботи додому» which is also fine — direction FROM is з + genitive.
- **No calques detected** in any checked phrase. ✅

---

## CEFR Check

- **звідки** → A1 ✅ (PULS confirmed)
- **додому** → A1 ✅ (PULS confirmed)
- **місяць** → A1 ✅ (PULS confirmed)
- **робота** → A1 ✅ (PULS confirmed)
- **школа** → A1 ✅ (PULS confirmed)
- **приїхати / приїхав** → A2 ⚠️ — one level above target A1. Used in Dialogue 1: *"я приїхав місяць тому"*. **Recommendation:** Retain as a **formulaic chunk** (я приїхав/приїхала — I arrived) presented as a ready-made phrase, not as a verb to conjugate. Flag in the dialogue with a note: "chunk — full verb paradigm at A2." Do NOT drop the phrase — it's natural and textbook-level for a meeting dialogue.
- **Україна** (proper noun) — not in PULS database (proper nouns excluded), appropriate at all levels, first introduced at A1 universally.
- **куди** → A1 ✅ (PULS confirmed — retrieved as comparison entry)
</pre_verified_facts>


## Knowledge Packet (textbook excerpts from RAG)

**MANDATORY — this is your primary source.** The knowledge packet contains real Ukrainian textbook excerpts. Your content MUST use the terminology, notation, and pedagogical approach from these excerpts.

**Hard rules for the knowledge packet:**
1. **Use Ukrainian terminology from the packet, not English linguistics.** If the textbook says «складоподіл», you write «складоподіл» — never CVCCV or "syllable division rules" paraphrased from English phonology. If it says «відкритий склад», you write «відкритий склад» — never "open syllable type."
2. **Adopt the textbook's teaching sequence.** If the packet shows: sound model → syllable → word → sentence, follow that progression. Do not rearrange or substitute your own.
3. **Include specific examples from the packet.** If the textbook uses «ка-ша», «мо-ло-ко» to teach syllable division, use those same words (and add more). Authentic examples beat invented ones.
4. **Your pre-training is contaminated by Russian and English linguistics.** When the packet contradicts your instinct, the packet wins. Ukrainian has its own phonetic categories (голосний/приголосний, дзвінкий/глухий, м'який/твердий) that do not map 1:1 to English or Russian. Use the Ukrainian categories.
5. **Before submitting, verify:** For every linguistic term you used, check — does it appear in the knowledge packet or plan? If you used a term that's NOT in the packet (e.g., "CVCCV", "onset", "coda"), replace it with the Ukrainian equivalent from the packet.

<knowledge_packet>
# Verified Knowledge Packet: Where From?
**Module:** where-from | **Phase:** A1.5 [Places]
**Textbook grades searched:** 4, 5, 6

---

## Діалоги (Dialogues)

> **Source:** zabolotnyi, Grade 6
> **Section:** Сторінка 282
> **Score:** 0.50
>
> 282
> ВІД СМІШНОГО ДО ВЕЛИКОГО
> ÇÀÌÎÐÑÜÊ² ÃÎÑÒ²
> ГУМОРЕСКА
> Прилетіли в Україну
> Гості із Канади.
> Мандруючи по столиці,
> Зайшли до міськради.
> Біля входу запитали
> Міліціонера:
> – Чи потрапити ми можем
> На прийом до мера? –
> Козирнув сержант бадьоро.
> – Голови немає.
> Він якраз нові будинки
> В Дарниці приймає.
> Здивуванням засвітились
> Очі у туриста.
> – Ваша мова бездоганна
> І вимова чиста.
> А у нас там, у Канаді,
> Галасують знову,
> Що у Києві забули
> Українську мову.
> Козирнув сержант і вдруге.
> – Не дивуйтесь, – каже. –
> Розбиратися у людях –
> Перше діло наше.
> Я вгадав, що ви культурні,
> Благородні люди,
> Бо шпана по-українськи
> Розмовлять не буде.
>  ÏÅÐÅÂ²ÐßªÌÎ
> 1. Дія, змальована в гуморесці «Заморські гості», відбувається в
>  
> А Канаді     Б Києві     В Полтаві     Г Польщі
> 2.

## Звідки? (Where From?)

> **Source:** avramenko, Grade 5
> **Section:** Сторінка 81
> **Score:** 0.50
>
> 81
>  § 34–35.  Позначення  звуків  мовлення  на  письмі.  Алфавіт
> 3.	Розташуйте й запишіть назви обласних центрів України за алфавітом. 
> У дужках додайте інформацію про напрямок руху до кожного міста, 
> якщо виїжджати з вашого населеного пункту (за зразком). 
> Напрямки руху: 
> •	 західний;
> •	 східний;
> •	 південний; 
> •	 північний; 
> •	 південно-західний; 
> •	 південно-східний; 
> •	 північно-західний, 
> •	 північно-східний.
> Зразок. Мій населений пункт — м. Київ. 
> Вінниця (південно-західний);
> Дніпро (південно-східний) … .
> Більшість букв українського алфавіту позначають один звук: а [а], 
> к [к], н [н]. 
> Зверніть увагу на особливі випадки співвідношення звуків і букв.

> **Source:** litvinova, Grade 6
> **Section:** Сторінка 132
> **Score:** 0.33
>
> Розділ 5. Іменник 
> 132
> Вправа 269
> 1. Прочитайте текст.
> Чи знаєте ви, звідки походять назви українських міст 
> і сіл? Нескладно здогадатися, як утворилися назви Івано-
> Франківськ, Хмельницький чи, 
> скажімо, Сковородинівка: вони 
> бережуть пам’ять про відомих 
> людей свого регіону.
> У подібний спосіб утворено 
> й  інші топоніми, наприклад, 
> Київ від імені полянського князя 
> Кия чи Львів на честь князя 
> Лева Даниловича.
> Але це далеко не єдиний 
> спосіб творення назв населених 
> пунктів. Якщо дослідити їхнє 
> походження, можна дізнатися багато цікавого про певну 
> територію чи місцевих мешканців.
> 2. З’ясуйте значення виділеного слова. Запишіть його до словничка не-
> знайомих слів.
> 3. Випишіть власні назви, визначте рід, пригадайте правила їхнього пра-
> вопису.
> 4.

## Країни і міста (Countries and Cities)

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 131
> **Score:** 0.25
>
> 131
> Фонетика. Графіка. Орфоепія. Орфографія.  Позначення звуків на письмі.  Алфавіт
> 2.	 Поміркуйте, чи за  алфавітом розташовані слова.
> 3.	 Запишіть слова з  кожного ряду за  алфавітом.
> Вправа 212
> 1.	 Прочитайте назви обласних центрів України.
> Вінниця, Дніпро, Донецьк, Житомир, Запоріжжя, Іва-
> но-Франківськ, Київ, Кропивницький, Луганськ, Луцьк, Львів, 
> Миколаїв, Одеса, Полтава, Рівне, Сімферополь, Суми, Терно-
> піль, Ужгород, Харків, Херсон, Хмельницький, Черкаси, Чер-
> нівці, Чернігів.

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 188
> **Score:** 0.33
>
> 185
> населення є такі міста: Київ, Харків, Одеса. 3. Я хочу побу-
> вати скрізь: і на берегах Амазонки, і в Єгипті, і в Карпатах. 
> 4. Різні птахи відлітають на зимівлю в теплі краї: ластівки, 
> лелеки, шпаки, дрозди.
> ІІ. Зачитайте вголос речення з відповідною інтонацією. 
> Узагальнювальне слово може стояти перед однорідними 
> членами речення або після них. Залежно від цього ставимо 
> тире або двокрапку.
> Якщо узагальнювальне сло-
> во стоїть ПЕРЕД однорідни-
> ми членами речення, то перед 
> ними ставимо ДВОКРАПКУ
> Галявина поросла лісо-
> вим зіллям: папороттю, 
> конвалією, деревієм.
> { : À, À, À
> Якщо узагальнювальне слово 
> стоїть ПІСЛЯ однорідних чле-
> нів речення, то після них ста-
> вимо ТИРЕ
> Пагорбки, трави, кущи-
> ки  – усе оповито тума-
> ном.
> À, À, À – { 
> На схемах узагальнювальне слово позначаємо так: {.

> **Source:** zaharijchuk, Grade 4
> **Section:** Сторінка 77
> **Score:** 0.50
>
> 77
> Словенія, Албанія, Македонія, Польща, Швейцарія, Чехія. 
> Для цих країн Дунай є рідною річкою, яку люблять і бере-
> жуть (З енциклопедії).
> 	 Випиши назви земель, які прикрашає та напуває Дунай. Під­
> кресли суфікси. Що пишемо в цих суфіксах?
> 188.		Прочитай запитання.
> — Як називають Січ, де жили українські козаки?
> — Як називають сузір’я, за яким орієнтувалися чумаки?
> — Як називають річки, що протікають у горах?
> — Як називають берег моря?
> — Як називають області, центрами яких є міста Вінни-
> ця, Київ, Харків, Чернівці, Чернігів?
> 	 Запиши відповіді на запитання. Підкресли в прикметниках 
> суфікси. Що пишемо в цих суфіксах?
> 189.		Випиши з вправи 187 назви всіх держав. Утвори від них 
> прикметники із суфіксами -ськ-, -цьк-, -зьк-. Підкресли 
> суфікси, поясни правопис.
> 190.	Послухай вірш І.

## Підсумок — Summary

> **Source:** schupak, Grade 5
> **Section:** Сторінка 80
> **Score:** 0.50
>
> РОЗДІЛ 2
> 80
> 2.	 СУЧАСНА УКРАЇНА НА КАРТІ ЄВРОПИ
> Територія сучасної України формувалася упродовж віків 
> і набула остаточних контурів у ХХ ст. Україна — найбільша 
> за площею держава Європи. Вона має вигідне географічне 
> положення.
> УКРАЇНА В ЄВРОПІ
> 1.	 Покажіть на карті кордони і столицю України.
> 2.	 Назвіть країни Європейського Союзу, до яких громадяни України 
> можуть приїжджати вільно, без візи.
> Безвізовий режим — можливість для громадян України вільно пе-
> ретинати міждержавні кордони країн Європей-
> ського Союзу без попереднього звернення до 
> посольства для отримання дозволу (візи).
> Пізнавально й цікаво
> Відмітка польської прикордонної служби
> в закордонному паспорті громадянина України
> 11 червня 2017 р. — перший день безвізового
> режиму з країнами Євросоюзу

> **Source:** zaharijchuk, Grade 4
> **Section:** Сторінка 38
> **Score:** 0.50
>
> 38
> 92.		Прочитай уривок із вірша.
> Ой, яка чудова українська мова!
> Де береться все це, звiдкiля i як?!
> Є в нiй лiс-лiсок-лiсочок, пуща, гай, дiброва,
> Бiр, перелiсок, чорнолiс. Є iще байрак.
> I така ж розкiшна та гнучка, як мрiя.
> Можна «звiдкiля» i «звідки», можна i «звiдкiль».
> Є у нiй хурделиця, вiхола, завiя,
> Завiрюха, хуртовина, хуга, заметiль. 
>                                                                                        О. Підсуха
> Байрак — яр, порослий лісом і чагарником. 
> Чорнолісся —  листяний ліс.  
> 	 Випиши спочатку підкреслені слова, а потім виділені. Як нази-
> ваємо слова, близькі за значенням, але різні за звучанням?
> 93.		Прочитай частини прислів’їв.

## Grammar Reference

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 64
> **Score:** 0.50
>
> 64
> Лексикологія.  Написання слів іншомовного походження
> Підказка.  Легко запам’ятати літери, що входять до  «дев’ятки», 
> можна за  допомогою фраз:
> Де Ти З’їСи Цю ЧаШу ЖиРу  — усі літери на  позначення 
> приголосних.
> Реве Та  Стогне Дніпр Широкий, Човни З  Цитринами 
> Жене  — перша літера в  кожному слові.
> Вправа 88
> 1.	 Прочитайте запозичені слова.
> Чизкейк  — чіабата, принтер  — шопінг, матриця  — відео, 
> таксі — таксист, історія — історик, графіті — тинейджер, пік-
> нік  — система, лінк  — лиман, банкір  — касир.
> 2.	 Поясніть написання літер на позначення голосних у  словах.

> **Source:** litvinova, Grade 6
> **Section:** Сторінка 25
> **Score:** 0.50
>
> § 2. Багатство української мови  
> 25
> 2. За допомогою дорослих проведіть в  інтернеті дослідження щодо слів, 
> походження яких вас зацікавило. Запишіть у  зошити інформацію про 
> походження. Яка інформація для вас була новою?
> Слово «кеди

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Звідки? (Where From?)` (~300 words)
- `## Країни і міста (Countries and Cities)` (~300 words)
- `## Підсумок — Summary` (~300 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 15-30% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — explain the grammar concept once, clearly.
- EXAMPLES: Ukrainian sentences in bulleted lists (each line: Ukrainian — English gloss). Max 2-4 per rule.
- TABLES: Paradigm tables, case endings, vocabulary groups — all cells Ukrainian.
- PATTERN BOXES: Show transformations: `книга → книгу` (nominative → accusative).
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, or pattern boxes.
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
- Use callout boxes (:::tip, :::caution, :::note) sparingly — max 3 per module
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
  1. **International student mixer at a Kyiv university — sharing origins: Я з Канади, Вона з Японії, Він з Німеччини. Also: З якого міста? З Торонто, з Токіо, з Берліна.**
     Speakers: Кілька студентів (group)
     Why: Звідки? + з: Канада(f), Японія(f), Німеччина(f), Торонто(n)

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

GRAMMAR CONSTRAINTS (A1.5 — Places & Movement, M29-M36):
Euphony, locative, accusative direction, genitive origin.

ALLOWED:
- Euphony rules (у/в, і/й, з/із/зі)
- Locative case with в/у/на (Де?)
- Accusative for direction (Куди?)
- Genitive for origin (Звідки? З + genitive)
- All present tense verbs

BANNED: Past/future tense, dative, instrumental,
participles, passive voice, complex subordination

### Vocabulary

**Required:** звідки (where from), з/із/зі (from — + genitive chunk), Україна (Ukraine), Київ (Kyiv), Львів (Lviv), Канада (Canada)
**Recommended:** Одеса (Odesa), Харків (Kharkiv), США (USA), Англія (England), Німеччина (Germany), Польща (Poland), додому (home — direction)

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
## Діалоги (~370 words total)

- P1 (~30 words): Scene-setter — international student mixer at a Kyiv university. Introduce the communicative goal: finding out where someone is from, using з + country and city.

- D1 (~110 words): Full dialogue — Taras meets Lena and Kenji:
  — Привіт! Мене звати Тарас. Звідки ти?
  — Я з України, з Києва. А ти?
  — Я з Канади, із Торонто.
  — Давно тут?
  — Ні, я приїхав місяць тому. А ти, Кенджі?
  — Я з Японії, з Токіо.
  — Як цікаво! Я вперше зустрічаю людину з Японії.
  Callout box: З Канади / із Торонто — both mean FROM. із before vowel clusters → covered in P below.

- P2 (~40 words): Bridge — note that Dialogue 1 uses з + country AND з + city. The same question (Звідки?) works for both. Dial in: cities go inside countries — Я з Канади, із Торонто = I'm from Canada, from Toronto.

- D2 (~110 words): Direction FROM vs TO — Oksana and Mykola on the street:
  — Звідки ти йдеш?
  — Я йду з роботи. Втомилася. А ти?
  — Я зі школи. Куди ти зараз?
  — Додому. А Олена де?
  — Вона ще в магазині. Але скоро йде з магазину додому.
  — Добре. Бувай!
  Callout box: з роботи = FROM work | зі школи = FROM school | додому = home (direction).

- P3 (~80 words): Quick analysis of both dialogues. Звідки? always triggers з/із/зі + a noun phrase (country, city, place). Contrast two patterns spotted in the dialogues: (1) Звідки ти? = origin/nationality (Я з Японії); (2) Звідки ти йдеш? = current departure point (з роботи, зі школи). Both use the same preposition family. Preview: the full direction trio Де?–Куди?–Звідки? is explained in the next section.

- **Activity (fill-in, 8 items):** Answer Звідки? using з/із/зі + memorized genitive chunks. Items: Я {з України}. / Вона {з Канади}. / Ми {з Києва}, а ви? / Джон {зі США}. / Мій друг {з Німеччини}. / Я {зі Львова}. / Вони {з Англії}. / Олена {з Одеси}.

---

## Звідки? (~360 words total)

- P1 (~110 words): Introduce the complete three-question location trio, building on М05 (Де?), М33 (Куди?), and now М34 (Звідки?). Present as a system:
  — Де ти? — В Україні. (locative — where you ARE right now)
  — Куди ти їдеш? — В Україну. (accusative — direction TO)
  — Звідки ти? — З України. (genitive chunk — origin FROM)
  Emphasize: one country, three different forms, three different questions. Native speakers switch between them instinctively. We learn the pattern now and the grammar (відмінки) in A2.

- P2 (~130 words): The з/із/зі alternation — euphony rule from М28 applied to FROM:
  з України (consonant cluster avoided), з Києва, зі Львова (зі before зл-), з Одеси, з Харкова, з Дніпра.
  з Канади, з Англії, з Польщі, з Франції, з Японії.
  зі США / зі Штатів (зі before СШ-), з Німеччини.
  з роботи, зі школи, з магазину, з банку, з парку.
  Pattern: з before most consonants; із before vowels or awkward consonant clusters; зі before зл-, зн-, сш- and similar. At A1: recognize the pattern, memorize the fixed phrases — don't calculate.

- P3 (~120 words): A1 learning strategy — treat з + place as sealed chunks, just like Вавілон-студент taught в Україні as one unit. Analogy: English speakers don't think "in + Ukraine" separately; they say "in Ukraine" as one phrase. Same here. Я з України / з Києва / з роботи = three set phrases to know by heart. Genitive case endings (why Київ → Києва, Україна → України) = full A2 grammar. For now, recognize and reproduce the forms from this module's vocabulary.

- **Activity (group-sort, 9 items):** Categorize into Де? / Куди? / Звідки?:
  Де?: в Україні, в Києві, на роботі.
  Куди?: в Україну, в Київ, на роботу.
  Звідки?: з України, з Києва, з роботи.

---

## Країни і міста (~360 words total)

- P1 (~130 words): Ukrainian cities — present all six with their FROM-forms as parallel pairs:
  Київ → з Києва | Львів → зі Львова | Одеса → з Одеси
  Харків → з Харкова | Дніпро → з Дніпра | Запоріжжя → із Запоріжжя
  Cultural note (sourced from Litvinova Gr.6, p.132): Київ takes its name from Kyi, a legendary Polanian prince; Львів is named for Prince Lev Danylovych — cities carry history in their names. Pronunciation callout: Львів [л'в'ів] → зі Львова [зі льво́ва] — the зі form prevents зл- cluster.

- P2 (~130 words): Countries — present with their FROM-forms in two groups:
  Nearby/common: Польща → з Польщі, Угорщина → з Угорщини, Румунія → з Румунії.
  Further: Канада → з Канади, США → зі США (зі Штатів), Англія → з Англії, Німеччина → з Німеччини, Франція → з Франції, Японія → з Японії, Італія → з Італії.
  Reminder: Ukrainian spelling — Канада (not Кенада), Японія (not Япан), Німеччина (not Германія). These are Ukrainian names, not transliterations of English names. Use the Ukrainian forms always.

- P3 (~100 words): Nationality + language identity chain — review from М05, now extended:
  Я з України → Я українець (m) / українка (f) → Я говорю українською.
  Я з Польщі → Я поляк / полька → Я говорю польською.
  New contrast — current location vs. origin:
  Я живу в Києві, але я зі Львова. (I live in Kyiv, but I'm from Lviv.)
  Вона живе в Канаді, але вона з України. (She lives in Canada, but she's from Ukraine.)
  Pattern: живу в [місці] (locative) + але я з [міста/країни] (genitive chunk).

- **Activity (quiz, 8 items):** Choose correct preposition (в / на / з / зі) for each blank:
  Я йду... роботи. | Вона йде... школу. | Ми зараз... Україні. | Я їду... Канаду. | Він... Німеччини. | Вони... Львові. | Я йду... магазину. | Олена... школи.

- **Activity (fill-in, 6 items):** Contrast living location vs. origin:
  Я живу {в Києві}, але я {зі Львова}. / Вона живе {в Канаді}, але вона {з України}. / Ми зараз {в Англії}, але ми {з Польщі}. / Він живе {в Одесі}, але він {з Харкова}. / Я {з Німеччини}, але зараз я {в Україні}. / Ти {зі США}, але живеш {у Києві}.

---

## Підсумок — Summary (~170 words total)

- P1 (~100 words): Recap the completed location trio — three questions, three preposition families, three case slots (memorized as chunks):
  **Де?** → в/на + locative chunk → В Україні. У Києві. На роботі. (where you ARE)
  **Куди?** → в/на + accusative chunk → В Україну. У Київ. На роботу. (where you're GOING)
  **Звідки?** → з/із/зі + genitive chunk → З України. З Києва. З роботи. (where you're FROM)
  Genitive endings (why Київ→Києва, Польща→Польщі) = A2 grammar. For now: recognize the pattern, memorize the fixed forms. You now have all three direction questions. Use them.

- Self-check (~70 words): Three personal questions — answer aloud in Ukrainian:
  • Звідки ти? (З якої країни? З якого міста?)
  • Де ти зараз? (В якому місті? В якій країні?)
  • Куди ти йдеш після цього уроку? (Додому? На роботу? В магазин?)
  If you can answer all three switching prepositions correctly — Звідки?/Де?/Куди? — this module is done.

---

Grand total: ~1260 words (prose only; activities add ~200 additional words of Ukrainian text)
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
