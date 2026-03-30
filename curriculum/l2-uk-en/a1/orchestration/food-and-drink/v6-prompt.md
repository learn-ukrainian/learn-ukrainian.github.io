

---

## Your Writing Identity

**You are: Patient & Supportive Ukrainian Tutor.** Your persona is *The Helpful Teacher*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **36: Food and Drink** (A1, A1.6 [Food and Shopping]).

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

1. **IMMERSION TARGET: 20-35% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if you exceed it. For early modules, the learner CANNOT READ CYRILLIC — English must dominate. Ukrainian appears only as bolded inline words/phrases. Do NOT write long Ukrainian passages, Ukrainian-only paragraphs, or Ukrainian text without English translation.
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
module: a1-036
level: A1
sequence: 36
slug: food-and-drink
version: '1.2'
title: Food and Drink
subtitle: Їжа і напої — what Ukrainians eat and drink
focus: vocabulary
pedagogy: PPP
phase: A1.6 [Food and Shopping]
word_target: 1200
objectives:
- Name common Ukrainian foods and drinks
- Use кава з молоком, чай з цукром as memorized chunks (NOT instrumental grammar)
- Talk about what you eat and drink daily
- Recognize iconic Ukrainian dishes (борщ, вареники, сало)
dialogue_situations:
- setting: 'Cooking борщ (m, borshch) with grandma — listing ingredients: буряк (m,
    beetroot), картопля (f, potato), капуста (f, cabbage), м''ясо (n, meat), морква
    (f, carrot), цибуля (f, onion), сметана (f, sour cream).'
  speakers:
  - Бабуся (teaching)
  - Онучка (learning)
  motivation: Food with буряк(m), картопля(f), капуста(f), м'ясо(n), сметана(f)
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — At home in the morning: — Що ти хочеш на сніданок? — Каву з молоком
    і хліб з маслом. — А я хочу чай з цукром і кашу. Food + drink combinations as
    chunks (з + noun = memorized phrase).'
  - 'Dialogue 2 — Talking about food preferences: — Що ти зазвичай їш на обід? — Суп
    і салат. — А на вечерю? — М''ясо з картоплею або рибу з рисом. Three meals: сніданок,
    обід, вечеря.'
- section: Їжа (Food)
  words: 300
  points:
  - 'Core food vocabulary by category: Хліб і каша: хліб, каша, рис, макарони. М''ясо
    і риба: м''ясо, курка, риба. Овочі: картопля, морква, цибуля, помідор, огірок.
    Фрукти: яблуко, банан, апельсин. Молочне: молоко, сир, масло, сметана, йогурт.
    Інше: яйце, цукор, сіль, олія.'
  - 'Ukrainian iconic foods (cultural note): борщ (beet soup — national dish), вареники
    (filled dumplings), сало (cured pork fat), галушки (dumplings), деруни (potato
    pancakes). These words are cultural identity, not just vocabulary.'
- section: Напої (Drinks)
  words: 300
  points:
  - 'Core drink vocabulary: Гарячі: кава, чай. Холодні: вода, сік, компот, лимонад.
    Молочні: молоко, кефір. Алкогольні: пиво, вино (for recognition). Key chunk pattern:
    [drink] з [addition] — memorized, NOT grammar: кава з молоком, чай з цукром, чай
    з лимоном, вода з газом.'
  - 'Why ''з + noun'' is a chunk, not grammar: At A1, learn кава з молоком as a fixed
    phrase, like ''coffee with milk.'' The instrumental case ending (-ом, -ою) is
    grammar for A2. For now: memorize the whole phrase. Say it as one unit.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Food and drink toolkit: Що ти хочеш? — Каву з молоком. / Хліб з маслом. Що ти
    їш на сніданок / обід / вечерю? Three meals: сніданок (breakfast), обід (lunch),
    вечеря (dinner). Self-check: Name 5 foods and 3 drinks you like. Name one Ukrainian
    dish and why it matters.'
vocabulary_hints:
  required:
  - їжа (food, f)
  - напій (drink, m)
  - хліб (bread, m)
  - кава (coffee, f)
  - чай (tea, m)
  - вода (water, f)
  - молоко (milk, n)
  - сік (juice, m)
  - м'ясо (meat, n)
  - риба (fish, f)
  - суп (soup, m)
  - сніданок (breakfast, m)
  - обід (lunch, m)
  - вечеря (dinner, f)
  recommended:
  - борщ (beet soup, m)
  - вареник (dumpling, m)
  - каша (porridge, f)
  - сир (cheese, m)
  - масло (butter, n)
  - яйце (egg, n)
  - картопля (potato, f)
  - цукор (sugar, m)
  - сіль (salt, f)
  - сметана (sour cream, f)
  - компот (compote, m)
  - курка (chicken, f)
  - салат (salad, m)
  - піца (pizza, f)
  - помідор (tomato, m)
  - огірок (cucumber, m)
  - яблуко (apple, n)
  - банан (banana, m)
  - лимон (lemon, m)
activity_hints:
- type: match-up
  focus: Match Ukrainian food and drink words to English
  items: 10
  pairs:
  - хліб: bread
  - м'ясо: meat
  - риба: fish
  - молоко: milk
  - вода: water
  - сік: juice
  - сніданок: breakfast
  - обід: lunch
  - вечеря: dinner
  - суп: soup
- type: group-sort
  focus: Categorize into Їжа (Food) and Напої (Drinks)
  items: 10
  groups:
  - name: Їжа
    items:
    - хліб
    - м'ясо
    - риба
    - суп
    - каша
  - name: Напої
    items:
    - кава
    - чай
    - вода
    - сік
    - молоко
- type: fill-in
  focus: Use 'з + noun' as memorized chunks for additions
  items: 6
  blanks:
  - Я хочу каву {з молоком}.
  - Вона п'є чай {з цукром}.
  - Він їсть хліб {з маслом}.
  - Я люблю чай {з лимоном}.
  - Дайте, будь ласка, воду {з газом}.
  - Ми їмо м'ясо {з картоплею}.
- type: quiz
  focus: Identify meals and iconic Ukrainian dishes
  items: 6
  questions:
  - Що ми їмо вранці? (сніданок / обід / вечерю)
  - Що ми їмо ввечері? (вечерю / сніданок / обід)
  - Традиційний український суп — це... (борщ / каша / вода)
  - 'Українська страва з тіста і картоплі або сиру: (вареники / сало / хліб)'
  - 'Популярний холодний напій з фруктів: (компот / борщ / кава)'
  - Що ми їмо вдень? (обід / сніданок / вечерю)
connects_to:
- a1-037 (I Eat, I Drink)
prerequisites:
- a1-035 (Checkpoint — Places)
grammar:
- з + noun as memorized chunk (NOT instrumental grammar)
- Що ти хочеш? — review хотіти from M19
- No new grammar — vocabulary-focused module
register: розмовний
references:
- title: ULP Season 1, Episodes 11-13
  url: https://www.ukrainianlessons.com/episode11/
  notes: Anna introduces food and drink vocabulary, cafe ordering.
- title: State Standard 2024, Topic 3 (ресторан)
  notes: 'Communicative situation: restaurant, food, ordering.'

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

**Batch 1 (17 words):** ✅ All confirmed
**Batch 2 (16 words):** ✅ All confirmed

### Confirmed (33/33):
їжа, напій, хліб, кава, чай, вода, молоко, сік, м'ясо, риба, суп, сніданок, обід, вечеря, борщ, вареник, каша, сир, масло, яйце, картопля, цукор, сіль, сметана, компот, курка, салат, піца, помідор, огірок, яблуко, банан, лимон

**Note on сік:** VESUM returns both `сік(noun)` "juice" and `сікти(verb)` "to chop/hack" — the noun form is confirmed correct.

### Not found: *(none)*

---

## Textbook Excerpts

### Section: Діалоги (Food & meal dialogues)
> «Я люблю пити смачне молоко. Я люблю пироги з вишнями та черешнями. Я не люблю бананові тістечка з кремом.»
> Source: Большакова, Grade 1 Bukvar (tier 2) — model for expressing personal food preferences using люблю / не люблю

> «Прочитай. Яка улюблена їжа дівчинки? Розкажи про свою улюблену страву.»
> Source: Большакова, Grade 1 Bukvar (tier 2) — established pattern: ask about favourite food, answer about own preferences

> «Чи ви снідаєте? — Бракує часу, немає апетиту… За всіма стандартами — і нашими, і європейськими — сніданок має бути!»
> Source: Заболотний, Grade 5 (tier 1) — three-meal structure (сніданок as key meal) introduced in real pedagogical context

### Section: Їжа (Food vocabulary by category)
> «Здавна в харчуванні українців головну роль відігравали страви із зернових, хліб і хлібні вироби... В українській кухні багато овочевих страв: насамперед з капусти, буряків, моркви, пастернаку, ріпи.»
> Source: Pometun (History), Grade 7 (tier 1) — authoritative cultural grounding for Ukrainian food categories

> «продукти харчування / молочні продукти / солодощі / фрукти та овочі / спеції / крупи»
> Source: Заболотний, Grade 8 (tier 1) — natural Ukrainian grouping of food categories for list-making

> «Думала Оленка так: "Щоб здоров'я мати, / Треба їсти їй буряк, пити чай із м'яти, / їсти супчики й борщі, вареники з сиром"»
> Source: Захарійчук, Grade 4 (tier 2) — поетичний мнемонічний приклад лексики їжі

### Section: Напої (Drink vocabulary)
> «Компот рідкий, а кисіль густий. Морозиво ..., а чай ... . Сіль солона, а цукор ... . Сік жовтий, а вода ...»
> Source: Большакова, Grade 2 (tier 2) — **primary source for drink vocabulary** with contrastive pairs; shows the core drink set (чай, сік, вода, компот) used exactly as in this module's plan

> «Пам'ятай, що компот, молоко, лимонад, сік не мають властивостей звичайної питної води»
> Source: Заболотний, Grade 5 (tier 1) — natural listing of drink vocabulary in context

> «Вирощувати й заварювати чай почали в Китаї... Чай буває білий, зелений, чорний.»
> Source: Ponomarova, Grade 4 (tier 2) — cultural-informational model for чай

### Section: Підсумок / Ukrainian iconic foods
> «Вареники — фірмова страва української кухні. Як начинку в тісто кладуть сир, м'ясо, гриби, вишню, мак, капусту, картоплю, пшоняну чи гречану кашу. Для українського селянина вареники були стравою святковою, не повсякденною.»
> Source: Авраменко, Grade 7 (tier 1) — **ideal source for cultural note on вареники** with ingredients list

> «Іди, іди, дощику, / Зварю тобі борщику» / «Вибери продукти для борщу. Назви овочі, з яких варять борщ.»
> Source: Захарійчук, Grade 1 Bukvar (tier 1) — борщ introduced as first-grade cultural vocabulary

> «Мати рано уставала, / На сніданок готувала / Із вишнями вареники, / Вареники-туленики» / «Ти знаєш, що таке вареники? Це дуже смачна українська страва, виріб із тіста з різною начинкою.»
> Source: Захарійчук, Grade 1 Bukvar 2025 (tier 1) — вареники poem + explicit cultural definition

---

## Grammar Rules

- **Instrumental case with з:** The plan correctly treats `кава з молоком`, `чай з цукром`, `хліб з маслом` as **fixed A1 chunks** — not grammar. Instrumental endings (-ом/-ою/-ем) are A2 scope. No Правопис §§ needed at A1 — purely memorized phrases. ✅ Plan approach is sound.

- **⚠️ CRITICAL — Verb form їсти, 2nd person singular:** Правопис + Антоненко-Давидович (§ДІЄСЛОВА, chunk ad-117) confirm: **"ти їси"** is correct, NOT **"ти їш"**. Direct quote: *«ти даси, їси, відповіси, розповіси, а не даш, їш, відповіш, розповіш»*. The dialectal "їш" is found in Western regions but is non-standard in literary Ukrainian.

  **Plan dialogue error found:** The plan contains `— Що ти зазвичай їш на обід?` → **Must be: `— Що ти зазвичай їси на обід?`**

---

## Calque Warnings

- **"приймати їжу"** (receive food → eat): ⚠️ CALQUE of Russian "принимать пищу". Not present in the plan — but **do not use** in the module. Correct Ukrainian: **їсти**, **снідати / обідати / вечеряти**, **харчуватися**.

- **"зазвичай"** (usually): ✅ OK — correct Ukrainian adverb. Антоненко-Давидович warns against "як правило" (calque), but "зазвичай" is natural Ukrainian.

- **"Смачного!"** (Enjoy your meal!): ✅ OK — natural Ukrainian expression. Do NOT use "Приємного апетиту" (that is closer to a calque of Russian/French). Correct Ukrainian: **Смачного!**

- **"кава з молоком"** (coffee with milk): ✅ OK — natural Ukrainian instrumental chunk, widely attested in textbooks and real speech.

---

## CEFR Check

| Word | PULS Level | Verdict |
|------|-----------|---------|
| їжа | A1 | ✅ On target |
| хліб | A1 | ✅ On target |
| сніданок | A1 | ✅ On target |
| молоко | A1 | ✅ On target |
| вечеря | A1 | ✅ On target |
| кава | A1 | ✅ On target |
| борщ | A1 | ✅ On target |
| сметана | A1 | ✅ On target |
| вареник | A1 | ✅ On target |
| компот | **A2** | ⚠️ One level above target — culturally essential (common Ukrainian children's drink), acceptable at A1 but flag for awareness |

**All other core vocabulary** (вода, чай, м'ясо, риба, суп, обід, каша, сир, масло, яйце, картопля, цукор, сіль, курка, салат, помідор, огірок, яблуко, банан, лимон) not individually returned by PULS but are all basic concrete nouns well within A1 scope — no concerns.
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
# Verified Knowledge Packet: Food and Drink
**Module:** food-and-drink | **Phase:** A1.6 [Food and Shopping]
**Textbook grades searched:** 4, 5, 6

---

## Діалоги (Dialogues)

> **Source:** ponomarova, Grade 4
> **Section:** Сторінка 103
> **Score:** 0.50
>
> 103
> 5. Із тексту про японську мову випиши в колонку дієс-
> лова, вжиті у множині. Утвори від них форму однини
> і  запиши  у  другу  колонку.
> 5
> 6. Напиши повідомлення японським школярам про україн-
> ську мову (3–4 речення).
> 6
> 7. Прочитай текст. Випиши в колонку дієслова. Зміни їх
> за числами й запиши поряд. Напиши, які страви з рису 
> ти знаєш. Які тобі доводилося їсти? 
> Рис називають японським хлі-
> бом. Найчастіше японці їдять 
> його без будь-яких приправ, 
> масла і навіть солі. Вони вважа-
> ють, що рис і без того багатий 
> на смак. Із рису готують безліч 
> страв. Найпопулярніша серед них — суші. 
> Японці користуються незвичним для нас столо-
> вим прибором. Це дві палички, які назива-
> ються хàсі.
> 7
> 1. Розглянь серію малюнків. Запиши відповіді на запитання, 
> подані під кожним малюнком.

## Їжа (Food)

> **Source:** gisem, Grade 6
> **Section:** Сторінка 156
> **Score:** 0.50
>
> § 50. Повсякденне життя Риму за часів республіки  155
> 4. Харчування
> Раціон римлян залежав від достатку. Пе-
> ресічні римляни їли пшеничний хліб та 
> кашу. З  овочів споживали капусту, ріпу, 
> цибулю, редьку та боби, а  з молочних про-
> дуктів  — козиний або овечий сир. Пили 
> розведене водою вино. М’ясо їли дуже рідко. Переважно це була свинина, із якої також 
> готували численні види ковбас. Тривалий час 
> бідні римляни мали городи. Однак коли кіль-
> кість населення Рима збільшилася і  місця 
> почало бракувати, тримати город у  межах 
> міста заборонили. Заможні римляни харчувалися різноманіт-
> ніше. Вони могли дозволити собі споживати 
> багато м’яса та риби, свіжих фруктів та 
> овочів, а  також рідкісні, привезені здалеку 
> продукти і  спеції.

> **Source:** avramenko, Grade 5
> **Section:** Сторінка 14
> **Score:** 0.33
>
> 14
> ТЕКСТ. РЕЧЕННЯ. СЛОВО (ПОВТОРЕННЯ)
> 2. Прочитайте речення та виконайте завдання. У віддаленій перспективі в таких пернатих можуть сформуватися так 
> звані «крила ангела», що стирчать у горизонтальній площині, а не обтічно 
> лежать на тілі. Більшість птахів із цією вадою не вміють літати. Хліб — шкідлива їжа для диких водоплавних птахів, що не має ніякої 
> поживної цінності, окрім калорій. Постійне підгодовування хлібом зму-
> шує їх покладатися на людину як на джерело корму, а не на свій природ-
> ний раціон. Отже, хлібна дієта — це легкий доступ птахів до нездорового 
> раціону, унаслідок якого вони недоотримують поживні речовини. Треба пам’ятати: якщо ми перестанемо під-
> годовувати водоплавних птахів хлібом, вони 
> не зникнуть.

> **Source:** ponomarova, Grade 4
> **Section:** Сторінка 103
> **Score:** 0.50
>
> 103
> 5. Із тексту про японську мову випиши в колонку дієс-
> лова, вжиті у множині. Утвори від них форму однини
> і  запиши  у  другу  колонку.
> 5
> 6. Напиши повідомлення японським школярам про україн-
> ську мову (3–4 речення).
> 6
> 7. Прочитай текст. Випиши в колонку дієслова. Зміни їх
> за числами й запиши поряд. Напиши, які страви з рису 
> ти знаєш. Які тобі доводилося їсти? 
> Рис називають японським хлі-
> бом. Найчастіше японці їдять 
> його без будь-яких приправ, 
> масла і навіть солі. Вони вважа-
> ють, що рис і без того багатий 
> на смак. Із рису готують безліч 
> страв. Найпопулярніша серед них — суші. 
> Японці користуються незвичним для нас столо-
> вим прибором. Це дві палички, які назива-
> ються хàсі.
> 7
> 1. Розглянь серію малюнків. Запиши відповіді на запитання, 
> подані під кожним малюнком.

## Напої (Drinks)

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 54
> **Score:** 0.50
>
> 51
> Спільнокореневі слова
> (різні слова)
> чай
> чайний
> чаювати
> лимон
> лимонний
> лимонад
> Форми слова 
> (одне слово з різними  
> закінченнями)
> чай
> чаю
> чаєм
> лимон
> лимона
> лимоном
> Зверніть увагу!
> У результаті чергування звуків корінь може видозміню-
> ватися (мати різний звуковий склад). НАПРИКЛАД: 1) друг – 
> друзі – дружний; 2) рідня – родина; 3) вітер – вітру.
> 110.	І. Згрупуйте спільнокореневі слова й запишіть. Доберіть до кож-
> ної групи слів ще по одному спільнокореневому. Позначте в усіх сло-
> вах корені, закінчення. 
> Морський, водяний, водити, теплий, заводити, моряк, 
> примор’я, наводити, підводник, море, тепло, водянистий, 
> потепліти.
> ІІ. Визначте корені в словах дорога, придорож-
> ній. Чи є ці слова спільнокореневими? 
> 111.	І. ТРЕТЄ ЗАЙВЕ.

> **Source:** ponomarova, Grade 4
> **Section:** Сторінка 109
> **Score:** 0.50
>
> 109
> 4. Прочитай етикетку улюбленого напою китайців. Розка-
> жи, яку  інформацію вона  містить.  Що в ній для  тебе  як
> споживача  найважливіше?
> 4
> 5. Родзинка дізналася, де винайшли чай. Прочитай і ти.
> Вирощувати й заварювати чай почали в Китаї. 
> А сталося це, коли випадково листок чайного куща 
> впав у чашку з окропом. 
> Чай буває білий, зелений, чорний. Усі вони
> з листя одного куща, який називається «Каме-
> лія китайська». Тільки сушать листя по-різному. 
> Тому й виходить різний смак і властивості чаю.
> Чай зміцнює імунітет, зубну емаль, якщо його 
> споживають без цукру. Також допомагає працюва-
> ти серцю і судинам, перетравлювати їжу.
> 6. Добери антоніми до виділених у тексті про чай дієслів 
> і запиши в колонку. Постав утворені дієслова у формі 
> майбутнього часу й запиши у другу колонку.
> 7.

> **Source:** avramenko, Grade 6
> **Section:** Сторінка 57
> **Score:** 0.25
>
> 57
> 57
> § 30.  Похідні  і  непохідні  слова.  Твірне  слово
> 4.	 Виконайте завдання в тестовій формі.
> 1.	 Непохідним є слово
> А	 чайник
> Б	 лампа
> В	 несмак 
> Г	 дубок
> 2.	 Твірне й похідне від нього слово записано в рядку
> А	 кит → Китай 
> Б	 кава → кавалер 
> В	 мис → миска 
> Г	 сад → садок 
> 3.	 Твірні й похідні від них слова записано в усіх рядках, ОКРІМ
> А	 сир → сироп 
> Б	 читач → читачка
> В	 брат → братство 
> Г	 жовтий → жовтенький 
> 5.	 Прочитайте текст і виконайте завдання.
> Не було ще такого літнього ранку, щоб дід Арсен усидів удома. Де там! 
> Як тільки над обрієм зажевріє велика досвітня зоря, уже Арсен на ногах.

## Підсумок — Summary

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 236
> **Score:** 0.50
>
> 236
> Відомості із синтаксису й пунктуації. Складне речення
> 4. Яка інформація з  тексту була для вас новою?
> 5. Пригадайте, які хімічні досліди на кухні (з перерахованих у тексті чи інші) 
> проводили ви . Розкажіть про це друзям, використовуючи складні речення .
> Вправа 380
> 1. Прочитайте рекомендації щодо здорового сніданку .
> СМУЗІ
> z
> z яблуко — 1 шт.,
> z
> z банан — 1 шт.,
> z
> z склянка води,
> z
> z кілька заморожених ягід 
> (на ваш смак),
> z
> z ложка лляного насіння.
> ОМЛЕТ З ОВОЧАМИ 
> ТА ЗЕЛЕННЮ
> z
> z яйця — 1—2 шт.,
> z
> z молоко — 2 ст. л.,
> z
> z овочі на вибір — 50 г,
> z
> z сіль, перець за смаком, 
> зелень.
> СИРНИКИ
> z
> z кисломолочний сир 5—9 % 
> жирності — 200 г,
> z
> z яйце — 1 шт.,
> z
> z манка або борошно — 
> 2 ст. л.,
> z
> z ванільний цукор 
> (за бажанням) — 1 ч. л.
> 2.

> **Source:** ponomarova, Grade 4
> **Section:** Сторінка 36
> **Score:** 0.25
>
> 36
> ШОКОЛАД
> Користь
> Шкода
> приємний смак
> містить поживні речовини
> корисний для мозку
> можлива алергія
> шкодить зубам
> надмірне збудження
> 4. Розгляньте у групі однокласників етикетку. Користу-
> ючись довідкою, перевірте, чи якісний цей шоколад.
> Яка ще інформація з етикетки важлива для вас?
> Довідка. Склад якісного шоколаду: какао 
> терте, какао-масло, цукор. Молочний шоколад 
> містить ще сухе молоко. 
> 5. Розглянь таблицю. Зроби висновок, чи варто тобі вжива-
> ти шоколад. Чому? Напиши про це текст (3–4 речення).
> 6. Прочитай і запиши імена швейцарських друзів Родзин-
> ки. Познач закінчення у цих словах. Запиши українські
> імена з такими закінченнями.
> 4
> Ол³вія
> Л

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Їжа (Food)` (~300 words)
- `## Напої (Drinks)` (~300 words)
- `## Підсумок — Summary` (~300 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

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

PLAN-AWARE EXEMPTIONS: The following bans are RELAXED for this module because the plan explicitly teaches these constructs: Instrumental case (plan teaches it). Exception: If a grammar construct appears in this module's plan grammar list or objectives, it is ALLOWED for this module.

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
  1. **Cooking борщ (m, borshch) with grandma — listing ingredients: буряк (m, beetroot), картопля (f, potato), капуста (f, cabbage), м'ясо (n, meat), морква (f, carrot), цибуля (f, onion), сметана (f, sour cream).**
     Speakers: Бабуся (teaching), Онучка (learning)
     Why: Food with буряк(m), картопля(f), капуста(f), м'ясо(n), сметана(f)

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

GRAMMAR CONSTRAINTS (A1.6 — Food & Shopping, M37-M43):
Instrumental з, accusative objects, genitive quantities.

ALLOWED:
- Instrumental case with 'з' (кава з молоком)
- Accusative inanimate and animate objects
- Genitive for quantities (кілограм цукру)
- All cases from previous phases
- All present tense verbs

BANNED: Past/future tense, dative (until A1.7),
participles, passive voice, complex subordination

### Vocabulary

**Required:** їжа (food, f), напій (drink, m), хліб (bread, m), кава (coffee, f), чай (tea, m), вода (water, f), молоко (milk, n), сік (juice, m), м'ясо (meat, n), риба (fish, f), суп (soup, m), сніданок (breakfast, m), обід (lunch, m), вечеря (dinner, f)
**Recommended:** борщ (beet soup, m), вареник (dumpling, m), каша (porridge, f), сир (cheese, m), масло (butter, n), яйце (egg, n), картопля (potato, f), цукор (sugar, m), сіль (salt, f), сметана (sour cream, f), компот (compote, m), курка (chicken, f), салат (salad, m), піца (pizza, f), помідор (tomato, m), огірок (cucumber, m), яблуко (apple, n), банан (banana, m), лимон (lemon, m)

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
## Діалоги (Dialogues) (~330 words total)

- P1 (~30 words): Scene-setter — morning kitchen, Оленка and her мама, introducing the two dialogues as models for talking about food and drink.
- Dialogue 1 (~110 words): Morning breakfast exchange (8–10 turns):
  — Що ти хочеш на сніданок, Оленко?
  — Каву з молоком і хліб з маслом, будь ласка.
  — А я хочу чай з цукром і кашу.
  — Смачно! Я теж люблю кашу.
  Focus: з + noun chunks (кава з молоком, хліб з маслом, чай з цукром), verb хотіти, meal word сніданок.
- P2 (~20 words): Transition note — now lunchtime, same family, different meal words.
- Dialogue 2 (~110 words): Lunch and dinner preferences (8–10 turns):
  — Що ти зазвичай їш на обід?
  — Суп і салат. А іноді м'ясо з картоплею.
  — А що на вечерю?
  — Рибу з рисом або вареники зі сметаною.
  — Вареники! Моя улюблена страва!
  Focus: три прийоми їжі (сніданок, обід, вечеря), verbs їсти + пити, з + noun chunk вареники зі сметаною.
- P3 (~60 words): Short comprehension anchor — 3 bullet-point observations drawn from the dialogues: (1) Ukrainian says каву з молоком as one chunk; (2) three meal names; (3) з + noun appears in both food and drink contexts. Prepares learner for vocabulary sections.

---

## Їжа (Food) (~330 words total)

- P1 (~80 words): Core food vocabulary introduced in six labelled mini-groups with Ukrainian + English gloss:
  Хліб і каша: хліб (bread), каша (porridge), рис (rice), макарони (pasta).
  М'ясо і риба: м'ясо (meat), курка (chicken), риба (fish).
  Овочі: картопля (potato), морква (carrot), цибуля (onion), помідор (tomato), огірок (cucumber).
  Фрукти: яблуко (apple), банан (banana), апельсин (orange).
  Молочне: молоко (milk), сир (cheese), масло (butter), сметана (sour cream), йогурт (yoghurt).
  Інше: яйце (egg), цукор (sugar), сіль (salt), олія (oil).
- Exercise 1 (~0 words counted): **match-up** — 10 pairs (хліб↔bread, м'ясо↔meat, риба↔fish, молоко↔milk, вода↔water, сік↔juice, сніданок↔breakfast, обід↔lunch, вечеря↔dinner, суп↔soup). Placed here while food words are fresh.
- P2 (~90 words): Ukrainian iconic foods — cultural paragraph presenting борщ, вареники, сало, галушки, деруни with one sentence each: what it is, key ingredients (буряк + капуста + м'ясо + сметана for борщ; тісто + картопля/сир for вареники; свинина for сало; тісто for галушки; картопля for деруни). Framed as cultural identity, not just vocabulary — "ці слова — це Україна."
- P3 (~80 words): Borshch ingredient walk-through tied to the plan's dialogue situation (бабуся + онучка cooking together). Lists ingredients in natural Ukrainian: буряк, картопля, капуста, м'ясо, морква, цибуля, сметана — each with gender label (m/f/n) shown parenthetically. Notes that identifying ingredients by name is the first step; cooking verbs come in a later module.
- Exercise 2 (~0 words counted): **group-sort** — 10 items sorted into Їжа / Напої (хліб, м'ясо, риба, суп, каша | кава, чай, вода, сік, молоко). Bridges food section into drinks section.

---

## Напої (Drinks) (~330 words total)

- P1 (~80 words): Core drink vocabulary in four labelled mini-groups:
  Гарячі: кава (coffee), чай (tea).
  Холодні: вода (water), сік (juice), компот (compote), лимонад (lemonade).
  Молочні: молоко (milk), кефір (kefir).
  Алкогольні (recognition only): пиво (beer), вино (wine) — note these are for recognition, not production at A1.
- P2 (~100 words): The з + noun chunk pattern explained clearly. Heading: "Кава з молоком — вчи як одне слово." Four model chunks presented as fixed phrases: кава з молоком, чай з цукром, чай з лимоном, вода з газом. Explicit note: the endings -ом / -ою are A2 grammar (instrumental case) — at A1, memorise the whole phrase the way you memorise English "coffee with milk." Do not analyse the ending yet. Three more chunks from the dialogues: хліб з маслом, м'ясо з картоплею, вареники зі сметаною.
- Exercise 3 (~0 words counted): **fill-in** — 6 blanks using з + noun chunks:
  Я хочу каву {з молоком}. / Вона п'є чай {з цукром}. / Він їсть хліб {з маслом}. / Я люблю чай {з лимоном}. / Дайте, будь ласка, воду {з газом}. / Ми їмо м'ясо {з картоплею}.
- P3 (~80 words): Short cultural note on two Ukrainian drinks: компот (stewed fruit drink — a Ukrainian домашній staple, made from яблука, вишні, сливи; not the French dessert) and кефір (fermented milk — standard in Ukrainian households, часто на сніданок або на ніч). Connects drinks to real Ukrainian home context. Both words verified in vocabulary_hints.
- P4 (~70 words): Drinking verb mini-note — пити (to drink) used in three short model sentences: Я п'ю каву. / Вона п'є чай з лимоном. / Ми п'ємо воду. Parallel with їсти models from dialogues (Я їм суп / Він їсть рибу). No conjugation table — just the three natural sentences as models.

---

## Підсумок — Summary (~330 words total)

- P1 (~60 words): Recap of the module's three building blocks — food vocabulary by category, drinks vocabulary by category, з + noun as a fixed chunk. One-sentence payoff: by the end of this module you can name what you eat at every meal and order a drink the Ukrainian way.
- P2 (~80 words): Your food and drink toolkit — presented as a ready-to-use phrase bank:
  • Що ти хочеш? — Каву з молоком. / Чай з цукром. / Хліб з маслом.
  • Що ти їш на сніданок? — Кашу і хліб.
  • Що ти їш на обід? — Суп і салат.
  • Що ти їш на вечерю? — М'ясо з картоплею.
  • Я люблю борщ / вареники / каву.
- Exercise 4 (~0 words counted): **quiz** — 6 questions:
  Що ми їмо вранці? (сніданок / обід / вечерю) | Що ми їмо ввечері? (вечерю / сніданок / обід) | Що ми їмо вдень? (обід / сніданок / вечерю) | Традиційний український суп — це... (борщ / каша / вода) | Українська страва з тіста і картоплі або сиру: (вареники / сало / хліб) | Популярний холодний напій з фруктів: (компот / борщ / кава).
- P3 (~90 words): Self-check bullets (as specified in plan):
  • Назви 5 продуктів, які ти любиш. (prompted example: Я люблю хліб, сир, яблука, рибу і каву.)
  • Назви 3 напої. (Я п'ю каву, воду і сік.)
  • Що ти їш на сніданок / обід / вечерю?
  • Що таке борщ? Із чого його варять?
  • Назви ще одну українську страву і поясни, що це таке.
- P4 (~100 words): "Що далі?" — connects to a1-037 (I Eat, I Drink): in the next module you will use їсти and пити across all persons (я їм, ти їш, він їсть…) and practise ordering food in real situations. Preview sentence: У наступному модулі ти зайдеш до кафе і замовиш обід українською. Ends with one motivating cultural line: борщ, вареники, кава з молоком — це не просто їжа. Це Україна у словах.

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
