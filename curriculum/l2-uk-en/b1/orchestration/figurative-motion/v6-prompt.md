

---

## Your Writing Identity

**You are: Experienced Ukrainian Language Instructor.** Your persona is *The Cultural Guide*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **31: Час іде, дощ іде** (B1, B1.3 [Motion Verb Universe]).

**Target: 4000–6000 words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block. Evaluate each section from the plan and commit to a word budget. This prevents frontloading early sections and rushing later ones.

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Summary: ~150 words
Total: 4000+ words
</pacing_plan>
```

Then begin writing the module content. Follow your own pacing plan — each section must hit its word budget (±10%).

---

## 9 Hard Rules

1. **IMMERSION TARGET: 40-60% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if immersion is outside this range. For A1 early modules, the learner cannot read Cyrillic — English must dominate. For A2+, Ukrainian must carry a significant share — add Ukrainian Reading Practice blocks, dialogues, and example paragraphs to reach the target. Too little Ukrainian fails audit just as much as too much.
2. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
3. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
4. **NO "In this lesson we will..."** — never use formulaic openers. Start with a dialogue, a question, or a situation.
5. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
6. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers where exercises should appear. A separate pipeline step generates the actual exercises from the plan's activity_hints.
7. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
8. **Hit the word target** — you MUST write 4000–6000 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
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
module: b1-031
level: B1
sequence: 31
slug: figurative-motion
version: '3.0'
title: Час іде, дощ іде
subtitle: Переносне вживання дієслів руху в українській мові
focus: communication
pedagogy: PPP
phase: B1.3 [Motion Verb Universe]
word_target: 4000
objectives:
  - 'Learner can identify and use figurative expressions with іти/ходити: час іде,
    дощ іде, фільм іде, справи йдуть, мова йде про'
  - Learner can identify and use figurative expressions with їхати/їздити, 
    бігти, летіти, пливти and their prefixed forms
  - Learner can distinguish literal from figurative uses of motion verbs in 
    Ukrainian text and choose the correct one in production
  - 'Learner can use Ukrainian figurative motion expressions instead of calquing from
    English (Ukrainian: дощ іде, not *дощ падає as a calque)'
dialogue_situations:
  - setting: 'Philosophical conversation at a Київський парк (m, Kyiv park) on a rainy
      day — discussing life metaphors: Час іде (time passes). Дощ іде (it''s raining).
      Справи йдуть (things are going) добре. Мова йде (we''re talking about) про майбутнє.'
    speakers:
      - Подруги на прогулянці
    motivation: 'Figurative motion: час іде, дощ іде, справи йдуть, мова йде'
content_outline:
  - section: Дієслова руху в переносному значенні
    words: 600
    points:
      - 'Bridge from M28-M34: learners have mastered the literal motion verb system.
        But Ukrainians use motion verbs figuratively every day — for time, weather,
        processes, emotions. This module teaches the figurative layer that makes speech
        natural.'
      - 'From Авраменко Grade 5 p.27: a dialogue between siblings about ''Піде дощ''
        — ''А хіба дощ може ходити?'' This is how Ukrainian textbooks introduce the
        concept of переносне значення (figurative meaning). Лексичне значення can
        be пряме (literal) or переносне.'
      - 'From Авраменко Grade 10 p.19: летіти is багатозначне — пташка летить (literal)
        vs час летить (figurative, = fast). Understanding polysemy is essential for
        natural Ukrainian.'
  - section: 'Iти / ходити: найширший спектр'
    words: 900
    points:
      - 'Weather: дощ іде (it''s raining), сніг іде (it''s snowing). NOT *дощ падає
        (English calque ''rain falls''). In Ukrainian, rain ''goes.'' Надворі йде
        сильний дощ. Вчора йшов сніг цілий день. From Вашуленко Grade 2 p.80: textbook
        exercise replacing ''іде'' with synonyms: Iде катер → Пливе катер. Iде зима
        → Настає зима.'
      - 'Time: час іде (time passes), роки йдуть (years go by), літо йде до кінця
        (summer is ending). Iдуть дні, тижні, місяці... Рік іде за роком. Note: for
        fast time, use летить (Час летить!) — see below.'
      - 'Processes and events: фільм іде (a film is showing/playing), урок іде (class
        is in session), концерт іде (concert is on), ремонт іде (renovations are underway),
        переговори йдуть (negotiations are in progress), справи йдуть добре (things
        are going well).'
      - 'Abstract expressions: мова йде про (it''s about / we''re talking about):
        Мова йде про реформи. йти на компроміс (to compromise): Уряд пішов на компроміс.
        йти на ризик (to take a risk): Він пішов на великий ризик. йти назустріч (to
        accommodate/meet halfway): Пішли нам назустріч. йтися (impersonal — to be
        about): Йдеться про безпеку.'
      - 'Prefixed figurative forms: вийти (to turn out/result): Вийшов гарний пиріг.
        Нічого не вийшло. підійти (to suit): Це мені не підходить (This doesn''t suit
        me). дійти (to reach understanding): Дійшов до висновку (reached a conclusion).
        прийти (to come to mind): Мені прийшла ідея. Прийшов час діяти. зайти (to
        go too far): Зайшов надто далеко (went too far). обійтися (to get by): Обійдемося
        без цього (we''ll manage without it).'
  - section: 'Летіти: швидкість'
    words: 500
    points:
      - 'Летіти figuratively = moving very fast, passing quickly: Час летить! (Time
        flies!). Дні летять (Days fly by). Новина облетіла все місто (News spread
        around the whole city). Ціни злетіли (Prices skyrocketed — злетіти = take
        off/soar).'
      - 'Prefixed figurative forms: злетіти (to soar): Ціни злетіли вгору. вилетіти
        (to get fired/expelled, colloquial): Вилетів з роботи. пролетіти (to fly by):
        Канікули пролетіли непомітно. налетіти (to swoop in/rush at): Раптом налетів
        вітер.'
      - 'Practice: 6-8 sentences where learners identify literal vs figurative uses
        of летіти and its prefixed forms.'
  - section: 'Пливти: плавність і повільність'
    words: 400
    points:
      - 'Пливти figuratively = moving smoothly, drifting, flowing: Хмари пливуть (Clouds
        drift). Мелодія пливе (The melody flows). Місяць пливе по небу (The moon floats
        across the sky). Думки пливуть (Thoughts drift). Туман пливе над річкою (Fog
        drifts over the river).'
      - 'Contrast with летіти: Час летить (fast) vs Час пливе (slow/smooth). Both
        describe time passing, but with opposite speed connotations.'
      - 'Practice: 4-6 sentences using пливти figuratively.'
  - section: Бігти, їхати, нести та інші
    words: 600
    points:
      - 'Бігти figuratively = hurrying, being busy: Час біжить (Time runs — faster
        than іде, slower than летить). Вода біжить у річці (Water flows in the river).
        Мурашки біжать по шкірі (Goosebumps — literally ''ants run on skin'').'
      - 'Їхати figuratively (colloquial): Дах їде (going crazy — literally ''the roof
        is going''). Їхати на чомусь (to be obsessed with something, colloquial).'
      - 'Нести/носити figuratively: нести відповідальність (to bear responsibility).
        носити ім''я (to bear a name): Вулиця носить ім''я Шевченка. виносити рішення
        (to make a decision — formal/legal). Річка несе води (The river carries its
        waters — poetic).'
      - 'Вести/водити figuratively: вести переговори (to conduct negotiations). вести
        себе (to behave): Ведіть себе пристойно! вести блог/щоденник (to keep a blog/diary).
        водити за ніс (to deceive — literally ''lead by the nose'').'
  - section: Українські вирази vs англійські кальки
    words: 600
    points:
      - 'Decolonized usage — genuine Ukrainian expressions: дощ іде (NOT *дощ падає
        — English calque ''rain falls''). час іде/летить/біжить (NOT *час пробігає
        — awkward). фільм іде (NOT *фільм показують — though both exist, іде is natural).
        справи йдуть (NOT *справи є — English ''things are'').'
      - 'Russicism warnings for figurative motion: *мова іде — CORRECT is мова йде
        or йдеться (the impersonal form йтися is most natural: Йдеться про важливі
        питання). *діло йде — can be a Russicism; prefer справа стоїть/річ у тому.
        Always check: does this expression exist in Ukrainian, or am I translating
        from Russian/English?'
      - 'Practice: learners rephrase English sentences using natural Ukrainian figurative
        motion verbs. 6-8 translation-avoidance exercises.'
  - section: 'Підсумок: буквальне і переносне'
    words: 400
    points:
      - 'Summary table of key figurative uses: іти: weather, time, processes, events.
        летіти: speed, rapid change. пливти: smoothness, drifting. бігти: hurrying,
        flowing. нести/носити: responsibility, names. вести/водити: negotiations,
        behavior.'
      - 'Preview of M36: Подорож Україною — travel narratives combining literal motion
        verbs with the cultural vocabulary of Ukrainian travel.'
vocabulary_hints:
  required:
    - переносне значення (figurative meaning)
    - пряме значення (literal meaning)
    - дощ іде (it's raining — figurative use of іти)
    - час іде (time passes)
    - час летить (time flies)
    - справи йдуть (things are going — about progress)
    - мова йде про (it's about / the topic is)
    - 'йтися (impersonal — to be about: йдеться про)'
    - нести відповідальність (to bear responsibility)
    - вести переговори (to conduct negotiations)
    - вести себе (to behave)
  recommended:
    - 'злетіти (to soar — figurative: prices soar)'
    - водити за ніс (to deceive — idiom)
    - вийти (to turn out / result)
    - підійти (to suit — figurative)
    - дійти до висновку (to reach a conclusion)
    - обійтися (to get by without)
    - хмари пливуть (clouds drift)
    - мурашки біжать (goosebumps)
    - багатозначне слово (polysemous word)
    - фразеологізм (phraseological unit / idiom)
activity_hints:
  - type: quiz
    focus: Identify whether a motion verb is used literally or figuratively in a
      sentence
    items: 12
  - type: fill-in
    focus: Complete Ukrainian figurative expressions with the correct motion 
      verb
    items: 12
  - type: match-up
    focus: Match figurative motion expressions with their meanings
    items: 12
  - type: group-sort
    focus: 'Sort motion verb uses: literal / figurative — time / weather / abstract'
    items: 12
  - type: error-correction
    focus: Fix English calques and Russicisms in figurative motion expressions
    items: 12
  - type: free-write
    focus: Write a paragraph about your week using at least 5 figurative motion 
      expressions
    items: 12
connects_to:
  - b1-034 (motion-flight-swim — literal uses of летіти/пливти that become 
    figurative here)
  - b1-036 (traveling-ukraine — combining literal and figurative motion in 
    narratives)
  - b1-077 (lexical-stylistics — broader exploration of figurative language)
prerequisites:
  - b1-028 (motion-base-review — all base motion verb pairs)
  - b1-034 (motion-flight-swim — air/water motion verbs)
grammar:
  - Переносне значення — figurative meaning of motion verbs
  - 'Iти/ходити figurative: weather, time, processes, events, abstract'
  - 'Летіти figurative: speed, rapid change'
  - 'Пливти figurative: smoothness, drifting'
  - 'Prefixed figurative: вийти (turn out), підійти (suit), обійтися (manage)'
  - 'Anti-calque patterns: дощ іде (not *дощ падає)'
register: науково-навчальний
references:
  - title: Авраменко Grade 5, p.27
    notes: Dialogue about 'Піде дощ' — introduction to переносне значення.
  - title: Авраменко Grade 10, p.19
    notes: 'Летіти as багатозначне слово: literal (пташка летить) vs figurative (час
      летить).'
  - title: Вашуленко Grade 2, p.80
    notes: Iде катер, іде поїзд, іде зима, іде час — early polysemy exercise.
  - title: Глазова Grade 10, p.39
    notes: 'Лексичні синоніми: набігати, накотити — motion verb synonymy.'

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
- Confirmed: переносне, значення, пряме, дощ, іде, час, летить, справи, йдуть, мова, йтися, нести, відповідальність, вести, переговори, себе, злетіти, водити, ніс, вийти, підійти, дійти, висновок, обійтися, хмари, пливуть, мурашки, біжать, багатозначне, слово, фразеологізм.
- Not found: None (all words exist in VESUM as lemmas or inflected forms).

## Textbook Excerpts
### Section: Дієслова руху в переносному значенні
> "Переносне значення — це значення, перенесене з одних предметів чи явищ на інші за подібністю ознак. Наприклад: іде дощ."
> Source: Авраменко О. Українська мова, 5 клас.

### Section: Iти / ходити: найширший спектр
> "Дієслова руху найчастіше вживаються переносно, коли йдеться про явища природи або час: Час іде, іде дощ, годинник іде."
> Source: Авраменко О. Українська мова, 5 клас.

### Section: Пливти: плавність і повільність
> "Хмара пливе — повільний рух у небі."
> Source: Авраменко О. Українська мова, 5 клас.

## Grammar Rules
- Багатозначність слів: Пряме і переносне значення. Лексичне значення слова вивчається в розділі «Лексикологія». Специфічних правил у Правописі 2019 щодо вживання немає, оскільки це семантична категорія, проте вживання регламентується стилістичними нормами (див. Calque Warnings).

## Calque Warnings
- мова йде про: **Calque** (from RU 'речь идет о') — Correct: **йдеться про** or **мовиться про**.
- вести себе: **Calque** (from RU 'вести себя') — Correct: **поводитися**.
- дощ іде: **OK** — Valid Ukrainian expression, though "дощ падає" is a common regional/poetic alternative.
- справи йдуть: **OK** — Natural expression for progress.

## CEFR Check
- відповідальність: B2 — OK (Contextual/Active for B1.3)
- переговори: B2/C1 — OK (Contextual/Specific topic)
- фразеологізм: B1/B2 — OK (Metalanguage term for this level)
- висновок: B1 — OK
- пливти: A2/B1 — OK
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
# Verified Knowledge Packet: Час іде, дощ іде
**Module:** figurative-motion | **Phase:** B1.3 [Motion Verb Universe]
**Textbook grades searched:** 1, 2, 3, 5

---

## Дієслова руху в переносному значенні

*No textbook results found for: Дієслова руху в переносному значенні Авраменко 'Піде дощ' 'А хіба дощ може ходити переносне значення летіти багатозначне пташка летить час летить*

## Iти / ходити: найширший спектр

*No textbook results found for: ти ходити найширший спектр дощ іде сніг іде дощ падає ' Надворі йде сильний дощ Вчора йшов сніг цілий день Вашуленко час іде*

## Летіти: швидкість

*No textbook results found for: Летіти швидкість Летіти Час летить Дні летять Новина облетіла все місто Ціни злетіли злетіти Ціни злетіли вгору вилетіти Вилетів з роботи*

## Пливти: плавність і повільність

*No textbook results found for: Пливти плавність і повільність Пливти Хмари пливуть Мелодія пливе Місяць пливе по небу Думки пливуть летіти Час летить Час пливе*

## Бігти, їхати, нести та інші

*No textbook results found for: Бігти їхати нести та інші Бігти Час біжить іде летить Вода біжить у річці Мурашки біжать по шкірі Дах їде Їхати на чомусь*

## Українські вирази vs англійські кальки

*No textbook results found for: Українські вирази англійські кальки дощ іде дощ падає час іде летить біжить час пробігає фільм іде фільм показують*

## Підсумок: буквальне і переносне

*No textbook results found for: Підсумок буквальне і переносне іти летіти пливти бігти нести носити Подорож Україною*

## Grammar Reference

*No grammar results for: Переносне значення ти ходити Летіти Пливти вийти підійти обійтися дощ іде дощ падає*


## МійКлас Theory (miyklas.com.ua)

*Ukrainian school curriculum theory — use this terminology and teaching approach.*

### Правила вживання знака м'якшення
> **Source:** МійКлас — [Правила вживання знака м'якшення](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/fonetika-grafika-orfoepiia-orfografiia-14565/pravila-vzhivannia-znaka-m-iakshennia-39904)

### Теорія:
  

*www.ua.pistacja.tv*  
 
Знаком ь позначаємо м’якість приголосних звуків на письмі.
Знак м’якшення пишемо:
- Ь пишеться після м’яких д, т, з, с, дз, ц, л, н у кінці **слова** та **складу**: *дядько, радість, низько, заносьте, гедзь, доброволець, коваль, тінь.
*  
- Після **м’яких** приголосних у **середині складу** перед о: *чотирьох, дзьоб, сьомий, льодяний, відьом*.

### Лексичне значення слова. Однозначні й багатозначні слова
> **Source:** МійКлас — [Лексичне значення слова. Однозначні й багатозначні слова](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/leksikologiia-40143/leksichne-znachennia-slova-odnoznachni-i-bagatoznachni-slova-40128)

### Теорія:
Лексика й лексичне значення

*www.ua.pistacja.tv*  
Лексика — сукупність слів, які входять до складу певної мови, діалекту, сфери вживання.
 
Розділ мовознавства, що вивчає словниковий склад мови, називається лексикологією \(від грец. **lexikos** — словесний і  logos — учення\).
 
Основна одиниця лексики — слово, яке сприймається як звук або сукупність звуків і має певне смислове навантаження.  
**Лексичне значення **— те, що означає слово, його зміст. Кожне повнозначне слово має одне або кілька значень.
Приклад:
Слово яблуко означає плід яблуні \(перев.

### Речення, його граматична основа
> **Source:** МійКлас — [Речення, його граматична основа](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/vidomosti-z-sintaksisu-i-punktuatciyi-14562/rechennia-iogo-gramatichna-osnova-pidmet-i-prisudok-39372)

### Теорія:

*www.ua.pistacja.tv*  
Речення
Реченням називаємо одне або кілька слів, що виражають закінчену думку.
Саме за допомогою речень ми спілкуємось, висловлюємо прохання, наказ, виражаємо емоції, повідомляємо інформацію.
Приклад:
- Весна іде, красу несе \(Нар. творчість\). 
- Ліс. Тиша. Благодать. 
Слова в реченні зв'язані між собою **за змістом** і **граматично**. **Граматичний зв'язок** — це поєднання за допомогою **закінчень** і **службових слів**. На початок і кінець речення вказує **інтонація**. Між реченнями робимо **паузи**.
Ознаки речення
1. Речення відображає дійсність. Інформація **стверджується** або **заперечується**, сприймається як **реальна** або **нереальна**, **можлива** або **неможлива**.
  
2. Речення є **інтонаційно** й **змістово** завершеним.
  
3.

---
**Total textbook excerpts found:** 1
**Grades searched:** 1, 2, 3, 5
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Дієслова руху в переносному значенні` (~600 words)
- `## Iти / ходити: найширший спектр` (~900 words)
- `## Летіти: швидкість` (~500 words)
- `## Пливти: плавність і повільність` (~400 words)
- `## Бігти, їхати, нести та інші` (~600 words)
- `## Українські вирази vs англійські кальки` (~600 words)
- `## Підсумок: буквальне і переносне` (~400 words)

Each section should follow the word budget specified. The total must reach 4000 words minimum.

---

## Content Rules

Full Ukrainian immersion. Grammar explained IN Ukrainian. English only for disambiguation of false friends. Sentences max 30 words.

GRAMMAR RULES:
- Max 30 words per Ukrainian sentence
- Max 4 clauses per sentence
- All grammar constructions allowed
- Participles allowed
- Complex subordinate clauses allowed

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
  1. **Philosophical conversation at a Київський парк (m, Kyiv park) on a rainy day — discussing life metaphors: Час іде (time passes). Дощ іде (it's raining). Справи йдуть (things are going) добре. Мова йде (we're talking about) про майбутнє.**
     Speakers: Подруги на прогулянці
     Why: Figurative motion: час іде, дощ іде, справи йдуть, мова йде

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

**Required:** переносне значення (figurative meaning), пряме значення (literal meaning), дощ іде (it's raining — figurative use of іти), час іде (time passes), час летить (time flies), справи йдуть (things are going — about progress), мова йде про (it's about / the topic is), йтися (impersonal — to be about: йдеться про), нести відповідальність (to bear responsibility), вести переговори (to conduct negotiations), вести себе (to behave)
**Recommended:** злетіти (to soar — figurative: prices soar), водити за ніс (to deceive — idiom), вийти (to turn out / result), підійти (to suit — figurative), дійти до висновку (to reach a conclusion), обійтися (to get by without), хмари пливуть (clouds drift), мурашки біжать (goosebumps), багатозначне слово (polysemous word), фразеологізм (phraseological unit / idiom)

### Pronunciation Videos

**Do NOT embed YouTube videos in your prose.** A downstream ENRICH tool automatically places pronunciation videos from the plan. If you embed `<YouTubeVideo>` components, they will be duplicated. Simply reference the videos' existence when relevant (e.g., "Watch the pronunciation video for this letter") but do NOT insert `<YouTubeVideo>` tags.

Available videos (for reference only — ENRICH handles placement):


---

### Style Reference (match this tone and structure)

Дієприкметники — це особлива форма дієслова, яка поєднує ознаки дієслова та прикметника. Вони відповідають на питання «який?» і змінюються за родами, числами та відмінками, як звичайні прикметники.

Порівняйте:
- **написаний лист** (a written letter) — пасивний дієприкметник
- **зігрітий чай** (warmed tea) — пасивний дієприкметник

:::tip
В українській мові активні дієприкметники теперішнього часу (на -учий/-ючий) вважаються стилістично небажаними. Замість «працюючий лікар» краще сказати «лікар, який працює».
:::

*Note: Grammar explained IN Ukrainian using Ukrainian linguistic terms. English appears only in parenthetical translations for disambiguation. Callout boxes in Ukrainian.*



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
## Дієслова руху в переносному значенні (~650 words total)
- P1 (~180 words): Introduction to the concept of polysemy (багатозначність) in Ukrainian. Explain the difference between literal (пряме) and figurative (переносне) meanings using the verb іти. Contrast "Хлопчик іде до школи" with "Дощ іде" and "Час іде".
- P2 (~150 words): The "Rain" Anecdote. Recount the pedagogical story from Avramenko Grade 5 about a sister telling her brother "Піде дощ" and his confusion: "А хіба дощ має ноги, щоб ходити?". Use this to explain how Ukrainian perceives movement in inanimate objects or nature.
- P3 (~170 words): Deep dive into lexical meanings. Define how a word's primary meaning (moving on feet) expands into secondary meanings (progress, duration, state). List categories of figurative motion: time, weather, events, and abstract relations.
- Dialogue (~150 words): "Київський парк". Two friends, Олена and Марія, walking in a park as clouds gather. They discuss how fast summer is passing (літо йде до кінця) and notice the first drops (дощ іде). Use phrases: час іде, дощ іде, справи йдуть.

## Iти / ходити: найширший спектр (~950 words total)
- P1 (~180 words): Weather phenomena. Explain why "іти" is the primary verb for precipitation. Provide examples: іде дощ, сніг, град, дрібна мжичка. Contrast with English "to fall" and emphasize that in Ukrainian, weather "walks."
- P2 (~180 words): The passage of time. Focus on the steady, neutral pace of "іти." Examples: годинник іде, час іде, роки йдуть, століття йдуть. Explain how "іти" implies a continuous, unstoppable flow.
- P3 (~180 words): Events and Social Processes. Explain the use of "іти" for scheduled things: фільм іде (in cinema), урок іде (in class), ремонт іде (ongoing). Contrast with "відбуватися" (to happen/occur).
- P4 (~160 words): Abstract Logic and Idioms. Teach the vital phrase "мова йде про..." (we are talking about) and the impersonal form "йдеться про..." (it concerns). Explain "йти на компроміс" and "йти на ризик."
- P5 (~150 words): Prefixed figurative shifts. Focus on "вийти" (to result: "вийшла помилка"), "підійти" (to suit: "колір підходить"), and "дійти" (to reach a mental state: "дійти висновку").
- Exercise: Match-up. Match 12 Ukrainian figurative expressions (e.g., йти назустріч, справи йдуть) with their English equivalents or Ukrainian synonyms.

## Летіти: швидкість (~550 words total)
- P1 (~180 words): Speed and fast time. Explain that while time "goes" (іде) steadily, it "flies" (летить) when we are busy or happy. Examples: "Час летить непомітно," "Дні летять як мить."
- P2 (~150 words): Rapid spread and skyrocketing. Focus on "новина облетіла світ" and "ціни злетіли." Explain the prefix "з-" here as a sudden upward motion (taking off).
- P3 (~120 words): Colloquial fast exits. Explain "вилетіти" in the context of being expelled or fired ("вилетіти з університету").
- Exercise: Quiz. 12 items where students must choose between іти, летіти, or бігти to complete a sentence about time or speed.

## Пливти: плавність і повільність (~450 words total)
- P1 (~170 words): Drifting and smooth movement. Focus on nature: "хмари пливуть," "туман пливе," "місяць пливе." Explain the poetic nuance—this movement is silent, smooth, and often slow.
- P2 (~180 words): Abstract flow. Discuss "думки пливуть" (thoughts drift) and "мелодія пливе." Compare with "час летить" (fast) vs "час пливе" (slow, dreamy duration).
- Exercise: Group-sort. Sort 12 sentences into categories: Literal Water Motion vs. Figurative Smooth Motion (Clouds, Thoughts, Music).

## Бігти, їхати, нести та інші (~650 words total)
- P1 (~180 words): Бігти (Running). Explain "час біжить" as a middle ground between "іде" and "летить." Discuss physical sensations: "вода біжить" (stream), "мурашки біжать по шкірі" (goosebumps).
- P2 (~150 words): Їхати and Slang. Briefly explain "дах їде" (going crazy) and the colloquial "їхати на чомусь" (to be obsessed/focused). Contrast this with the formal "вести."
- P3 (~160 words): Нести/Носити and Вести/Водити. Focus on formal usage: "нести відповідальність," "носити ім'я," "вести переговори," "вести себе" (behavior).
- P4 (~160 words): Prefixed abstract forms. Focus on "донести думку" (convey an idea), "принести успіх" (bring success), "провести захід" (hold an event).
- Exercise: Fill-in-the-blank. 12 sentences requiring the correct form of бігти, нести, or вести in figurative contexts (e.g., ___ відповідальність, ___ переговори).

## Українські вирази vs англійські кальки (~650 words total)
- P1 (~220 words): Decolonizing the rain. Explicitly attack the calque "дощ падає" (from English "rain falls"). Explain that while "падати" is a physical movement, the natural Ukrainian expression is "іти." Use examples of natural rain descriptions.
- P2 (~220 words): Avoiding Russicisms. Compare "мова йде про" (often criticized as a calque) with the more authentic "йдеться про." Explain "справи йдуть добре" vs the literal "справи є добре."
- P3 (~210 words): Cultural Logic. Summarize why Ukrainian uses motion verbs for these concepts: it reflects a worldview where time and nature are active agents, not just background states.
- Exercise: Error-correction. 12 sentences with English/Russian calques (e.g., *час пробігає*, *дощ падає*) for the student to rewrite in natural Ukrainian.

## Підсумок (~450 words total)
- P1 (~200 words): Recap of the figurative "Motion Universe." Provide a summary table overview:
  - іти: weather, neutral time, events.
  - летіти: high speed, prices, fast time.
  - пливти: smooth motion, clouds, music.
  - вести: negotiations, behavior, blogs.
  - нести: responsibility, names.
- P2 (~100 words): Self-check questions:
  - Як сказати "It's raining" без кальки з англійської?
  - Яке дієслово описує дуже швидкий біг часу?
  - У чому різниця між "час летить" і "час пливе"?
- Exercise: Free-write. Write a 12-sentence diary entry about a busy day, using at least 5 different figurative motion verbs (e.g., "Справи йшли повільно, але час летів...").

Grand total: ~4350 words
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
