

---

## Your Writing Identity

**You are: Patient & Supportive Ukrainian Tutor.** Your persona is *The Helpful Teacher*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **14: Checkpoint: My World** (A1, A1.2 [My World]).

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

1. **IMMERSION TARGET: 10-20% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if you exceed it. For early modules, the learner CANNOT READ CYRILLIC — English must dominate. Ukrainian appears only as bolded inline words/phrases. Do NOT write long Ukrainian passages, Ukrainian-only paragraphs, or Ukrainian text without English translation.
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
module: a1-014
level: A1
sequence: 14
slug: checkpoint-my-world
version: '1.1'
title: 'Checkpoint: My World'
subtitle: Can you describe things, count, and point?
focus: review
pedagogy: PPP
phase: A1.2 [My World]
word_target: 1200
objectives:
- Demonstrate ability to identify noun gender and use possessives correctly
- Describe objects using adjectives and colors with correct agreement
- Use numbers in practical contexts (prices, age)
- Point at and identify objects using demonstratives
- Use basic plurals for familiar nouns
dialogue_situations:
- setting: 'Walking through a Ukrainian street market (ярмарок) — pointing at handmade
    crafts: вишиванка (f, embroidered shirt), глечик (m, jug), намисто (n, necklace),
    писанки (pl, decorated eggs). Describe, count, point, buy.'
  speakers:
  - Іванко (tourist)
  - Катя (local friend)
  motivation: 'Consolidation with Ukrainian cultural objects: вишиванка, глечик, писанка'
content_outline:
- section: Що ми знаємо? (What Do We Know?)
  words: 200
  points:
  - 'Self-check covering M08-M13: Can you determine noun gender? (M08) Can you describe
    things with adjectives? (M09) Can you name colors, including both blues? (M10)
    Can you count and say prices? (M11) Can you say ''this'' and ''that''? (M12) Can
    you make things plural? (M13)'
- section: Читання (Reading Practice)
  words: 250
  points:
  - 'A short Ukrainian text (8-10 sentences) using ONLY vocabulary from M08-M13. No
    new words. The learner reads aloud. Content: describing a room — objects, colors,
    prices, pointing at things. Example: Це моя кімната. Мій стіл великий і новий.
    Ця лампа біла, а та — жовта. У мене є три книги. Ці книги нові. Стіни білі.'
- section: Граматика (Grammar Summary)
  words: 200
  points:
  - 'Key patterns from A1.2: 1. Gender: він/вона/воно test + endings (consonant/−а,−я/−о,−е)
    2. Agreement: великий стіл, велика книга, велике вікно 3. Hard vs soft stem: червоний
    (-ий) vs синій (-ій) 4. Demonstratives: цей/ця/це, той/та/те 5. Plurals: столи,
    книги, вікна; adjective always -і 6. Numbers: as vocabulary (no morphology)'
- section: Діалог (Connected Dialogue)
  words: 300
  points:
  - 'A complete conversation combining all A1.2 skills: Shopping scenario — choosing
    items, describing what you want, asking prices. Uses gender agreement, colors,
    demonstratives, numbers, and plurals. — Добрий день! У вас є сумки? — Так!
    Ця червона чи та синя? — Та синя. Скільки вона коштує? — Двісті гривень. — Добре.
    А ці зошити? Скільки коштує один зошит? — Двадцять гривень.'
- section: Підсумок — Summary
  words: 250
  points:
  - 'A1.2 achievement summary: You can now describe your world in Ukrainian. You know
    20+ objects with their genders. You can describe them (big, new, red, blue). You
    can count and talk about prices. You can point at things (this/that). You can
    talk about groups (plurals). Next: A1.3 — Actions (verbs, what you do and like).'
vocabulary_hints:
  required: []
  recommended: []
activity_hints:
- type: quiz
  focus: 'Mixed gender/agreement review: choose correct form for noun+adjective pairs'
  items: 10
- type: fill-in
  focus: Complete the shopping dialogue with correct demonstratives, adjectives, and
    numbers
  items: 8
- type: group-sort
  focus: 'Sort vocabulary from M08-M13 by category: objects, colors, numbers'
  items: 12
- type: quiz
  focus: Singular or plural? Transform sentences from singular to plural
  items: 8
connects_to:
- a1-015 (What I Like)
prerequisites:
- a1-013 (Many Things)
grammar:
- 'Review: gender agreement (m/f/n)'
- 'Review: hard-stem vs soft-stem adjectives'
- 'Review: demonstratives цей/ця/це, той/та/те'
- 'Review: nominative plurals'
- 'Review: numbers as vocabulary'
register: розмовний
references:
- title: Synthesis of M08-M13 content
  notes: No new material — review and integration of A1.2 phase.

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

**50/50 words confirmed. Zero failures.**

- **Confirmed (nouns):** стіл, книга, вікно, кімната, лампа, стіна, сумка, зошит, гривня, гривень, день
- **Confirmed (adjectives — all three gender forms):** великий/велика/велике, новий/нова/нове, білий/біла/біле, жовта (→жовтий), червоний, синій, добрий
- **Confirmed (demonstratives):** цей/ця/це, той/та/те, ці/ті
- **Confirmed (personal pronouns):** він, вона, воно
- **Confirmed (numerals):** двісті, двадцять, один
- **Confirmed (verbs):** коштує (→коштувати), є (→бути)
- **Confirmed (plurals):** столи, книги, вікна, сумки, зошити, стіни
- **Confirmed (other):** так, ні, моя (→мій)
- **Not found:** — (none)

> ⚠️ Note: `нове` returns matches as both adjective (→новий) and noun (→нове). The adjective form is what the plan uses — confirmed correct. Writers should be aware of the noun homograph.

---

## Textbook Excerpts

### Section: Що ми знаємо (self-check — noun gender)
> «Іменники, до яких можна додати слова мій, він, — чоловічого роду: тато, батько, ранок. Іменники, до яких можна додати слова моя, вона, — жіночого роду. Іменники, до яких можна додати слова моє, воно — середнього роду.»
> **Source: Вашуленко, Grade 3 (tier 2), p. 110**

> Also: Голуб, Grade 6 (tier 1), p. 68 confirms the parallel rule: «він/цей → ч.р., вона/ця → ж.р., воно/це → с.р.»

### Section: Читання (room description)
> «Стіл і ясенові лави стояли на своїх місцях... По другий бік дверей полискував жовтою дубовою фарбою дзеркальний гардероб, біля нього, під вікном, — етажерка з книгами...»
> **Source: Заболотний, Grade 6 (tier 2), p. 241 — "Будова опису приміщення"**

> Also: Авраменко, Grade 6 (tier 1), p. 94: «Завдання опису приміщення — не просто надати уявлення про предмети (розмір, форму, колір) та їхнє місце...» — confirms структура/план = **what + where + what like (color, size)**.

### Section: Граматика (gender endings + adjective agreement)
> «Чоловічий рід: закінчення -о або нульове (тато, вечір). Жіночий рід: закінчення -а, -я або нульове (мама, тінь). Середній рід: закінчення -о, -е, -а, -я (літо, сонце).»
> **Source: Вашуленко, Grade 3 (tier 2), p. 112 — "Спостерігаю за закінченнями іменників різних родів"**

> For adjective agreement table: «В однині прикметники мають закінчення: чоловічий рід -ий/-ій, жіночий -а/-я, середній -е/-є. У множині прикметники за родами не змінюються й мають закінчення -і.»
> **Source: Захарійчук, Grade 4 (tier 2), p. 83**

### Section: Діалог (shopping — prices + demonstratives)
> «— Чи є у вас трембіта? — Так, є. — Скільки вона коштує? — Дев'ять тисяч гривень.»
> **Source: Авраменко, Grade 6 (tier 1), p. 18 — §8 "Пряма мова. Діалог"**

> This is the **exact structural pattern** in the plan's dialogue — «Чи є у вас...? — Так! ... — Скільки вона коштує?» — textbook-grounded ✅

### Section: Підсумок
> No single textbook excerpt needed — summary sections follow the standard A1.x achievement format. The reading description task structure (назва предметів / місце розташування / ознаки: форма, колір, розмір) is confirmed by Заболотний Grade 6, p. 243.

---

## Grammar Rules

> ⚠️ Правопис 2019 query did not return dedicated sections for noun gender or plural morphology (those are covered in grammar textbooks, not orthography rules). The following rules are confirmed from textbook excerpts (authoritative NUS sources):

- **Noun gender (він/вона/воно test):** Confirmed — Вашуленко Gr. 3 p. 110/112, Голуб Gr. 6 p. 68. Rule: substitute він/мій (masc.), вона/моя (fem.), воно/моє (neut.) to determine gender.
- **Gender endings:** masc. = zero ending or -о; fem. = -а/-я or zero; neut. = -о/-е/-а/-я — Вашуленко Gr. 3 p. 112.
- **Adjective agreement:** masc. -ий/-ій, fem. -а/-я, neut. -е/-є; plural always -і — Захарійчук Gr. 4 p. 83.
- **Hard vs. soft stem:** червоний (-ий) hard, синій (-ій) soft — confirmed by VESUM tags (both return as adj).
- **Plural noun endings:** -и/-і for masculine/feminine, -а for neuter (столи, книги, вікна) — Авраменко Gr. 6 p. 98 declension tables.

---

## Calque Warnings

- **«скільки вона коштує»** — ✅ OK — No calque flag. Антоненко-Давидович returns unrelated entries. This is confirmed natural Ukrainian by the Авраменко textbook dialogue (exact same phrasing, p. 18).
- **«добрий день»** — ✅ OK — No calque flag. Standard Ukrainian greeting confirmed. Style guide returns no warning.
- **«у вас є»** — ✅ OK — No calque flag. Style guide note (ad-117) actually confirms: «Дієслово бути має в усіх особах однини й множини форму є» — «Ви є у нас...» usage cited as correct. «У вас є» is idiomatic Ukrainian.

> ⚠️ One calque to watch: the style guide (ad-156) flags **«матися»** as a Russian calque for «є/бути/траплятися» (e.g., «мається великий вибір» → wrong). Writers must use «є» not «мається» for existential constructions. The plan correctly uses «є».

---

## CEFR Check

All 10 key vocabulary items confirmed at **A1** — perfectly level-appropriate:

| Word | CEFR Level | Status |
|------|-----------|--------|
| кімната | A1 | ✅ |
| стіл | A1 | ✅ |
| сумка | A1 | ✅ |
| зошит | A1 | ✅ |
| великий | A1 | ✅ |
| червоний | A1 | ✅ |
| синій | A1 | ✅ |
| коштувати | A1 | ✅ |
| двісті | A1 | ✅ |
| гривня | A1 | ✅ |

> ⚠️ Advisory: **«приміщення»** = B2 per PULS. The plan correctly uses **«кімната»** (A1) throughout — do NOT substitute «приміщення» anywhere in this module.
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
# Verified Knowledge Packet: Checkpoint: My World
**Module:** checkpoint-my-world | **Phase:** A1.2 [My World]
**Textbook grades searched:** 1, 2, 3

---

## Що ми знаємо? (What Do We Know?)

> **Source:** zaharijchuk, Grade 1
> **Section:** Сторінка 52
> **Score:** 0.33
>
> 50
> 	
> Що тобі відомо про героїнь казки «Дві білки»? 
> 	
> Розглянь малюнки. Дай відповідь на питан-
> ня: що робить?
> 	
> Визнач, якому слову — назві намальованого 
> предмета відповідає кожна схема.
> [ =•|–•|–• ] 
> [ –•|=•= ] 
> [ =•–|– •–] 
> 	 Назви слова, які відповідають схемам.
> [ –•| – •| =•]
> [ – –•| = •]
> [ –    –•| –•| = •]
> Що робить?
> Pidruchnyk.com.ua

> **Source:** zaharijchuk, Grade 1
> **Section:** Сторінка 75
> **Score:** 0.50
>
> 73
> 	 — Але ми все одно будемо дружи-
> ти? Адже ми обидва їжаки.
> 	 — Авжеж. Будемо (за Юрієм  Яр-
> мишем).
> 	 Прочитай заголовок казки. Що він тобі підка-
> зав? Хто з ким познайомився? 
> 	 Що любив слухати Їжак, який жив на гірці? 
> Що любив слухати Морський Їжак? Чому 
> вони любили різні звуки? 
> Повторюємо разом
> Абетка. Звуки та букви
> 	 Звуки, які любили їжаки, є мовні чи немовні?
> 	 Як називаємо підкреслені слова? 
> протилежні за значенням
> подібні за значенням
> 	 Перепиши перше речення. Підкресли букви, 
> які позначають голосні звуки.
> 	 Прочитай текст.
> Катруся любить думати про те, чого не 
> буває, наприклад про равликів узимку.  
> Весною равлики люблять дощ. Один 
> старенький равлик любив мандрувати 
> під час дощу. Манд­рує — лічить калюжі. 
> ?
> Pidruchnyk.com.ua

## Читання (Reading Practice)

> **Source:** bolshakova, Grade 2
> **Section:** Сторінка 1
> **Score:** 0.50
>
> Інна Большакова
> Марина Пристінська
> УКРАЇНСЬКА МОВА
> ТА ЧИТАННЯ
> ЧАСТИНА 1
> 2 
> КЛАС
> ї
> о
> н
> А
> М

> **Source:** bolshakova, Grade 1
> **Section:** Сторінка 3
> **Score:** 0.50
>
> 3
> Дорогий друже!
> Ти хочеш учитися читати?
> Ти прагнеш спілкуватися?
> Ти любиш фантазувати?
> Тоді ця книга саме для тебе! 
> Вона допоможе тобі навчитися читати, 
> висловлювати думки й почуття, спілкуватися.
> Умовні позначення:
>  
>  — слухаю 
>  
> — досліджую мовлення
>  
>  — читаю 
>  — обговорюю малюнок
>  
>  — спілкуюся 
>  
> — мислю критично

## Граматика (Grammar Summary)

> **Source:** bolshakova, Grade 2
> **Section:** Сторінка 43
> **Score:** 0.50
>
> 43
> • Уяви, що малюнків було багато. Добери до слів — назв 
> предметів слова — назви ознак.
> Зразок. будинок (який?) червоний — будинки (які?) чер-
> воні.    
> Дах (який?) … — дахи (які?) … . 
> Двері (які?) … . 
> Вікно (яке?) … — вікна (які?) … . 
> Стіна (яка?) … — стіни (які?) …  . 
> Аркуш  (який) … — аркуші (які?) ... .
>  
> Допиши слова — назви предметів. 
> 1. Дерев’яний, письмовий, коричневий … .
> 2. Скляна, висока, прозора … .
> 3. Паперове, різнобарвне, веселе … .
> 4. Пластикові, довгі, тонкі … .
> • Чому не варто користуватися пла стиковими трубочками 
> для соку? Якої шкоди завдають природі пластикові ви-
> роби?
>  
> Запиши за зразком.
> Зразок. Лапа ведмедя — ведмежа лапа.
> Сукня з шовку — … . Хвіст зайця — … . 
> Квітка з паперу — … . Вуха лисиці — … . 
> Чашка зі скла — … .

> **Source:** vashulenko, Grade 2
> **Section:** Сторінка 17
> **Score:** 0.25
>
> Василь Сухомлинський
> УСІ КНИЖКИ ГАРНІ
> Мама дала Настусі гроші і сказала:
> —  Піди до  книгарні й  купи собі дві книжечки. 
> Там  є  гарні книжечки  — про  пташок і  метеликів, 
> про звірят і рибок…
> Пішла Настуся. А  там  книжок  — ой, скільки ж 
> там  книжок! Стоїть Настуся перед полицею, в  очах 
> у  неї сяє радість. Бо Настуся вже вміє читати. Ди-
> виться вона на  книжечки й  читає: ця  — про  їжачка, 
> ця  — про  котика. А  ось ця  — про  горобчика, 
> а ця — про ластівку. А он та — про ягнятко, а та — 
> про сірого бичка.
> Задумалася, занепокоїлася Настуся: «Що  ж роби-
> ти? Грошей у неї тільки на дві книжечки, а книжечок 
> он скільки! Купиш про їжачка, про котика, а горобчик, 
> Заголовок
>  Прочитай заголовок і  уважно розглянь ілюстрацію.

## Діалог (Connected Dialogue)

> **Source:** bolshakova, Grade 2
> **Section:** Сторінка 17
> **Score:** 0.50
>
> 17
> моноЛоГ І ДІаЛоГ
> Слово монолог складається з двох 
> частин: моно — один 
>  і лог — мов-
> лення. Коли ти розповідаєш комусь про 
> щось, описуєш предмет, розмірковуєш 
> наодинці — це монолог.  
> Діалог — це розмова двох (або кількох) осіб. Слово 
> діалог складається з двох частин: діа — два 
>  і лог — 
> мовлення. Коли ти спілкуєшся з другом/подругою, ви гово-
> рите по черзі, тобто обмі нюєтеся репліками.
> А я читаю 
> казку «Коти горошко».
> Я прочитала 
> казку «Рукавичка».
> репліка
> репліка
> Хто з казкових героїв використовує монолог, а хто — діалог? 
> Розіграй ситуації з друзями.
> • Вибери потрібне слово і запиши речення.
> 1. Котигорошко несе (сокиру, булаву, молоток).
> 2. Жабка і мишка виглядають з (рукавички, кишені).
> 3. Колобок співає (вірш, лічилку, пісню).
> 4.

> **Source:** kravcova, Grade 2
> **Section:** Сторінка 111
> **Score:** 0.33
>
> 111
> пасажирів установлено інформаційні 
> монітори. Вони полегшують користу-
> вання метро пасажирам з порушенням 
> слуху. На нових станціях змонтовані 
> ліфти-підйомники для тих, хто не може 
> самостійно пересуватися сходами.
> Пригадай! Розмову двох людей називають діалогом.
> Учасники діалогу обмінюються репліками.
> Зразок. 
> — Привіт, Кирилку!
> — Привіт, Соломійко!
> — Тобі сподобалося їздити на ескалаторі*?
> — Так, дуже! Пам’ятаєш правила безпечної поведінки 
> в метро?
> — Будьте уважні в метро. У вагоні не притуляйтеся до 
> дверей! 
> — А ще на ескалаторі потрібно триматися за поручні. 
> — Атож. Коли ми будемо дотримувати правил, то 
> поїздка принесе нам радість. До зустрічі.
> — Бувай.
> 397.
> Уявіть, що ви побували на екскурсії в музеї метро. Скла-
> діть усний діалог.

## Підсумок — Summary

> **Source:** zaharijchuk, Grade 1
> **Section:** Сторінка 72
> **Score:** 0.25
>
> 70
> Мої навчальні досягнення. Я вмію, можу
> * * *
> Прибрав ліжко САМ. 
> Зробив зарядку САМ. На 
> кухні  САМ поставив на 
> стіл чашку. Після снідан-
> ку САМ помив посуд.
> * * *
> А ... притулився до 
> мами й подумав: «Не-
> має нічого кращого, ніж 
> обійми моєї матусі. Ось 
> воно, щастя!»  
> * * *
> — Якщо ліс знову ста-
> не чистим, то й Лісовуня 
> буде гарною! — сказав 
> … .
> 	
> Пригадай історії, які ти прочитав / прочита-
> ла. Визнач, якому малюнку відповідає кож-
> ний уривок із тексту.
> Pidruchnyk.com.ua

> **Source:** bolshakova, Grade 1
> **Section:** Сторінка 79
> **Score:** 0.50
>
> . . . . . . . . . . . . . . . 77

## Grammar Reference

> **Source:** zaharijchuk, Grade 1
> **Section:** Сторінка 54
> **Score:** 0.50
>
> 52
> Ц ц
> Бачу  Ц, ц (це). Чую  [ц], [ц′].
> а
> о
> у
> и
> і
> Ц
> ца
> цо
> цу
> ци
> ці
> а
> о
> у
> и
> і
> ац
> оц
> уц
> иц
> іц
> Ц
> цу
> ци
> це
> цві
> т
> ркун
> це
> дра
> сарка
> ці
> лина
> кавий
> 	
> Пограємо в гру «Так / ні».
> Летить 
> ? — _____ !
> Летить 
> ?  — _____!
> Летить 
> ? — ____!
> Летить 
> ? — _______!
> у
> г о р о б е
> в і р
> ц
> к
> и м б
> ц
> а
> ц
>  [ –  =•– |–•– ]  
>  [ –•| –•| –•= ] 
> ь
> л и
> н
> Pidruchnyk.com.ua

> **Source:** zaharijchuk, Grade 1
> **Section:** Сторінка 88
> **Score:** 0.33
>
> 86
> Бачу Т, т (те). Чую  [т], [т'].
> т о р т
> т * л * п а н и
> к і т
>  [ –•  –  – ]
>  [  =  • –  ]
> а
> о
> у
> и
> і
> Т
> та
> то
> ту
> ти
> ті
> а
> о
> у
> и
> і
> ат
> от
> ут
> ит
> іт
> Т
> ті-	 	
> 	
>      тро-	          	
>   та-
>              -то	 	
>    	
>      -та	        	         -ти	
> Та-то  ку-пив  Ро-ма-но-ві 
>  .
> — Тім! Тім! — по-кли-кав  Ро-ман 
> так-су. — На 
>  .
> Т т


## МійКлас Theory (miyklas.com.ua)

*Ukrainian school curriculum theory — use this terminology and teaching approach.*

### Співвідношення звуків і букв
> **Source:** МійКлас — [Співвідношення звуків і букв](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/fonetika-grafika-orfoepiia-orfografiia-14565/spivvidnoshennia-zvukiv-i-bukv-41281)

### Теор

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Що ми знаємо? (What Do We Know?)` (~200 words)
- `## Читання (Reading Practice)` (~250 words)
- `## Граматика (Grammar Summary)` (~200 words)
- `## Діалог (Connected Dialogue)` (~300 words)
- `## Підсумок — Summary` (~250 words)
- `## Підсумок — Summary` (~150 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 10-20% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose. Introduce Ukrainian grammar terms bolded with translation on first use.
- UKRAINIAN CONTENT: Words and short phrases bolded inline: "The word **книга** (book) is feminine."
- TABLES: Vocabulary tables, word families, simple paradigm tables.
- STRUCTURAL RULE: Every paragraph is English. Ukrainian words/phrases appear inline bolded. Full Ukrainian sentences (3+ words with a verb) go in tables or bulleted example lists with English gloss.
Ukrainian sentences max 10 words.

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
  1. **Walking through a Ukrainian street market (ярмарок) — pointing at handmade crafts: вишиванка (f, embroidered shirt), глечик (m, jug), намисто (n, necklace), писанки (pl, decorated eggs). Describe, count, point, buy.**
     Speakers: Іванко (tourist), Катя (local friend)
     Why: Consolidation with Ukrainian cultural objects: вишиванка, глечик, писанка

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

GRAMMAR CONSTRAINTS (A1.2 — My World, M08-M14):
Noun gender, adjective agreement, plurals, numbers, demonstratives.

ALLOWED:
- Це + noun, У мене є/немає
- Adjective-noun agreement (nominative only)
- Numbers 1-1000
- Demonstratives цей/ця/це/ці
- Question words: Який? Яка? Яке? Скільки?
- Fixed verbal phrases from A1.1 (Мене звати, працювати)

BANNED: Verb conjugation (taught in A1.3), past/future tense, cases beyond nominative,
participles, passive voice, subordinate clauses

### Vocabulary



### Pronunciation Videos

**Do NOT embed YouTube videos in your prose.** A downstream ENRICH tool automatically places pronunciation videos from the plan. If you embed `<YouTubeVideo>` components, they will be duplicated. Simply reference the videos' existence when relevant (e.g., "Watch the pronunciation video for this letter") but do NOT insert `<YouTubeVideo>` tags.

Available videos (for reference only — ENRICH handles placement):


---

### Style Reference (match this tone and structure)

Look at the text on this page. What you are seeing are letters. Now, say a word out loud. What you just produced is a sound. This distinction is the absolute foundation of the Ukrainian language. There is a golden rule taught to every Ukrainian student in the first grade: **Ми чуємо і вимовляємо звуки, а бачимо і пишемо літери**. We hear and pronounce sounds, but we see and write letters.

These friendly letters are **А**, **О**, **К**, **М**, and **Т**. Because they are so familiar, you can start reading real Ukrainian words immediately. Look at the word **мама**. It means mother, and you already know how to read it. Now look at **тато**. It means father.

*Note: English prose dominates. Ukrainian words appear bolded inline. Short Ukrainian sentences illustrate one concept at a time. No conjugated verbs. Tables and bulleted lists for vocabulary.*



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
## Що ми знаємо? (What Do We Know?) (~220 words total)

- P1 (~60 words): Opening checkpoint orientation. You have completed A1.2 — six modules covering the building blocks of describing your world. This section checks whether the skills from M08–M13 have stuck. Work through each self-check question honestly: if any answer feels uncertain, the grammar summary and reading below will help.

- Self-check (~120 words): Bulleted Q&A list — one question per module:
  - M08 (Gender): What gender is *стіл*? *книга*? *вікно*? → він / вона / воно
  - M09 (Adjectives): What does *великий стіл* / *велика книга* / *велике вікно* show? → adjective ending agrees with noun gender
  - M10 (Colors): What are the two Ukrainian words for "blue"? → *синій* (dark/navy) and *блакитний* (sky blue)
  - M11 (Numbers/prices): How do you say "twenty hryvnias"? → *двадцять гривень*
  - M12 (Demonstratives): How do you say "this table" / "this lamp" / "this window"? → *цей стіл* / *ця лампа* / *це вікно*
  - M13 (Plurals): How do you make *стіл*, *книга*, *вікно* plural? → *столи*, *книги*, *вікна*

- P2 (~40 words): Short encouragement bridge: six questions, six patterns — these are the grammar tools you will use in every sentence of this module. If you answered all six correctly, you are ready for A1.3. If one or two felt shaky, read carefully and return.

---

## Читання (Reading Practice) (~275 words total)

- P1 (~40 words): Reading instruction. Read the text below aloud — slowly, one sentence at a time. Every word comes from M08–M13. No new vocabulary. Your goal: understand without translating. If you can picture what Оленка's room looks like, you are reading Ukrainian.

- Text (~190 words): 9-sentence Ukrainian reading passage. Each sentence uses only M08–M13 vocabulary:
  *Це моя кімната. Мій стіл великий і коричневий. На столі є три книги. Ці книги нові й цікаві. Моя лампа маленька і біла, а та лампа — жовта. Вікна великі. Мої стіни білі. Ця сумка синя, а та — червона. У мене є два зошити і чотири олівці. Олівці жовті й сині. Це моє вікно. За вікном є парк. Парк гарний.*
  (Sentences demonstrate: gender agreement — *мій стіл великий*, *моя лампа маленька*, *моє вікно*; demonstratives — *ці книги*, *ця сумка*, *та лампа*; plurals — *стіни білі*, *олівці жовті й сині*; numbers — *три книги*, *два зошити*, *чотири олівці*; colors — *синя*, *червона*, *жовті й сині*.)

- P2 (~45 words): Comprehension check — three questions the learner answers mentally (no writing required): Який стіл у Оленки? (великий і коричневий) Скільки книг на столі? (три) Яка маленька лампа? (біла). The point is immediate confirmation: Ukrainian → understanding, no English step needed.

---

## Граматика (Grammar Summary) (~220 words total)

- P1 (~50 words): Gender and agreement recap. The *він/вона/воно* test: replace the noun with a pronoun — whichever fits is the gender. Endings follow: consonant-final nouns → він (*стіл*, *глечик*); *-а/-я* endings → вона (*книга*, *вишиванка*); *-о/-е* endings → воно (*вікно*, *намисто*). Adjective ending must match: *великий стіл* / *велика книга* / *велике вікно*.

- P2 (~45 words): Hard vs. soft adjective stems. Most adjectives use hard endings: *червоний*, *новий*, *великий*. Adjectives with soft stems use *-ій*: *синій*, *останній*. The difference is in the stem's final consonant — *н* in *синій* softens. Rule of thumb: if the masculine form ends in *-ій*, it is soft; if *-ий*, it is hard.

- P3 (~40 words): Demonstratives. *Цей/ця/це* (this — close to speaker) and *той/та/те* (that — further away) agree with noun gender: *цей глечик* (m), *ця вишиванка* (f), *це намисто* (n); *той глечик*, *та вишиванка*, *те намисто*. Plural form: *ці* / *ті* for all genders.

- P4 (~40 words): Nominative plurals. Masculine and feminine nouns take *-и* or *-і*: *столи*, *книги*, *олівці*. Neuter nouns take *-а* or *-я*: *вікна*, *поля*. Adjectives in the plural always end in *-і* regardless of gender: *великі столи*, *великі книги*, *великі вікна*.

- P5 (~45 words): Numbers as vocabulary. Ukrainian numbers do not change adjective endings in A1 — treat them as standalone words: *один зошит*, *два зошити*, *п'ять зошитів*. For prices: *двадцять гривень*, *сто гривень*, *двісті гривень*. No morphology rules needed yet — memorize the forms you have seen.

- Activity: fill-in — Complete the shopping dialogue (8 blanks): learner fills in missing demonstratives (*цей/ця/це/той/та/те/ці/ті*), adjective endings (*червон__*, *нов__*), and numbers (*двадцять*, *двісті*). Blanks target the five grammar patterns above.

---

## Діалог (Connected Dialogue) (~330 words total)

- P1 (~50 words): Scene-setting prose. Іванко is visiting a Ukrainian ярмарок — an outdoor street market selling handmade crafts. His friend Катя is helping him choose souvenirs. He sees a table covered with вишиванки, глечики, намисто, and писанки. He wants to buy something but needs to ask about colors, sizes, and prices — everything from A1.2.

- Dialogue (~185 words): Multi-turn conversation, ~18 exchanges, covering all five grammar targets:
  — *Катю, подивись! Що це?*
  — *Це вишиванка. Вона дуже гарна.*
  — *Яка ця вишиванка — біла чи жовта?*
  — *Ця біла, а та — жовта. Тобі яка?*
  — *Мені біла. Скільки вона коштує?*
  — *Триста гривень.*
  — *А цей глечик? Він великий чи маленький?*
  — *Цей великий, а той маленький. Маленький коштує сто п'ятдесят гривень.*
  — *Добре. А це що? Це намисто?*
  — *Так, це намисто. Воно синє й біле.*
  — *Гарне! А ці писанки? Скільки коштує одна писанка?*
  — *Двадцять п'ять гривень.*
  — *Я хочу три писанки. Це сімдесят п'ять гривень?*
  — *Так, правильно! Молодець!*
  — *Дякую, Катю. Дуже гарний ярмарок!*
  — *Авжеж! Це українська традиція.*

- P2 (~55 words): Post-dialogue annotation (prose, not a table). Notice how gender drives every choice in this conversation: *вона* for вишиванка (f) → *біла*, *гарна*; *він* for глечик (m) → *великий*, *маленький*; *воно* for намисто (n) → *синє й біле*. Цей/ця/це appear seven times. Every price uses the number vocabulary from M11. This is A1.2 in action.

- Activity: group-sort — Sort 12 vocabulary items from M08–M13 into three categories: *Предмети* (objects: стіл, книга, вікно, сумка, зошит, олівець, глечик, намисто, писанка), *Кольори* (colors: червоний, синій, блакитний, жовтий, білий, коричневий), *Числа* (numbers: один, два, три, десять, двадцять, сто).

---

## Підсумок — Summary (~275 words total)

- P1 (~100 words): A1.2 achievement recap prose. You have completed A1.2 — My World. In six modules you built the grammar architecture for describing everything around you. You know how to determine noun gender using the він/вона/воно test. You can choose the right adjective ending based on gender and stem type. You know both Ukrainian blues — *синій* for navy, *блакитний* for sky. You can count objects and ask prices. You can point at things near and far with *цей/ця/це* and *той/та/те*. And you can speak about groups using plural forms with *-и/-і/-а*.

- P2 (~80 words): Vocabulary milestone. By the end of A1.2 you actively use 20+ objects with correct genders (*стіл* m, *книга* f, *вікно* n, *вишиванка* f, *глечик* m, *намисто* n); 10+ adjectives with agreement (*великий/велика/велике*, *новий/нова/нове*, *червоний/червона/червоне*, *синій/синя/синє*); 6 demonstrative forms (*цей, ця, це, той, та, те*); numbers 1–1000 as vocabulary; and plural patterns for all three genders.

- P3 (~55 words): What comes next. In A1.3 — *Actions* — you will meet Ukrainian verbs for the first time. What do you do? What do you like? *Я читаю. Я люблю музику. Ти розмовляєш українською.* The nouns and adjectives from A1.2 will combine with verbs to make real sentences about real life. The building blocks are ready. Now they start to move.

- P4 (~40 words): Closing motivation. Ukrainian is not built in one day — it is built in six modules at a time, then six more. You just finished the second set. The language is already yours to describe the world around you. *Молодець! Продовжуємо.*

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
