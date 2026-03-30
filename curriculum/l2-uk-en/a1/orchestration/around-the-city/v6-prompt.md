

---

## Your Writing Identity

**You are: Patient & Supportive Ukrainian Tutor.** Your persona is *The Helpful Teacher*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **33: Around the City** (A1, A1.5 [Places]).

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
module: a1-033
level: A1
sequence: 33
slug: around-the-city
version: '1.2'
title: Around the City
subtitle: Де/куди + directions — navigating in Ukrainian
focus: communication
pedagogy: PPP
phase: A1.5 [Places]
word_target: 1200
objectives:
- Combine Де? (locative) and Куди? (accusative) in real navigation
- Give and follow simple directions
- Describe your neighborhood and daily routes
- Synthesize M28-M32 skills in connected urban communication
dialogue_situations:
- setting: Walking tour of Lviv old town — going from Площа Ринок (f, main square)
    to Оперний театр (m, Opera house) to Високий замок (m, High Castle). Де ми? На
    площі. Куди далі? В театр. Звідки прийшли? З замку.
  speakers:
  - Гід (guide)
  - Туристи
  motivation: Де/Куди/Звідки with площа(f), театр(m), замок(m), парк(m)
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Asking for directions: — Вибачте, як дістатися до бібліотеки? —
    Ідіть прямо, потім направо. Бібліотека на розі. — А музей? — Музей далеко. Їдьте
    на метро до центру. Combines directions + transport + city places.'
  - 'Dialogue 2 — Describing your route: — Як ти дістаєшся на роботу? — Спочатку йду
    на зупинку. Потім їду автобусом до центру. — А потім? — Потім іду пішки п''ять
    хвилин. Робота в офісі на площі. Daily route using sequence words + transport
    + places.'
- section: Де і куди разом (Where and Where To Together)
  words: 300
  points:
  - 'Real navigation uses both cases together: Я зараз у парку (де? — locative). Я
    йду в магазин (куди? — accusative). Магазин на вулиці Шевченка (де? — locative).
    Потім їду на роботу (куди? — accusative). The constant switch between де? and
    куди? is natural Ukrainian.'
  - 'Preposition patterns (synthesis): | Situation | Question | Form | | Static |
    Де ти? | в/на + locative | | Direction | Куди йдеш? | в/на + accusative | | By
    transport | Як? Чим? | автобусом / на метро | | Distance | Далеко? | далеко /
    близько / пішки |'
- section: Мій район (My Neighborhood)
  words: 300
  points:
  - 'Describing where you live: Я живу на вулиці Франка. Біля мого дому є парк і магазин.
    Школа далеко — треба їхати автобусом. Аптека близько, можна піти пішки. У моєму
    районі є кафе, ресторан і бібліотека.'
  - 'Useful phrases for city life: пішки (on foot), хвилина (minute) — П''ять хвилин
    пішки. далеко/близько від (far/near from — chunk). У центрі міста / на околиці
    (in the center / on the outskirts).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Urban communication toolkit: Asking: Де...? Як дістатися до...? Directions: прямо,
    направо, наліво. Location: в/на + locative, в/на + accusative. Transport: автобусом,
    на метро, пішки. Self-check: Describe your route from home to work/school.'
vocabulary_hints:
  required:
  - пішки (on foot)
  - хвилина (minute, f)
  - район (neighborhood, m)
  - центр (center, m)
  - вибачте (excuse me)
  recommended:
  - дістатися (to get to)
  - ідіть (go! — imperative, preview)
  - їдьте (go by transport! — imperative, preview)
  - поруч (nearby)
activity_hints:
- type: fill-in
  focus: Give directions using прямо, направо, наліво
  items: 6
  blanks:
  - Ідіть {прямо}, потім {направо}. Бібліотека на розі.
  - Вибачте, як дістатися до музею? — Ідіть {наліво}.
  - Аптека близько. Ідіть {прямо} п'ять хвилин.
  - Потім ідіть {направо}, школа там.
  - Йдіть {прямо}, а потім {наліво}.
  - Ресторан поруч. Ідіть {прямо} і {направо}.
- type: quiz
  focus: Де (locative) or Куди (accusative) in context
  items: 6
  questions:
  - Я зараз... (в парку / в парк)
  - Я йду... (в магазин / в магазині)
  - Магазин на... (вулиці / вулицю)
  - Потім їду на... (роботу / роботі)
  - Ми зараз у... (центрі / центр)
  - Вона йде в... (офіс / офісі)
- type: fill-in
  focus: Describe route with transport (автобусом, пішки, на метро)
  items: 6
  blanks:
  - Я їду в центр {на метро}.
  - Потім іду {пішки} п'ять хвилин.
  - Вона їде на роботу {автобусом}.
  - Школа далеко, треба їхати {на метро}.
  - Парк близько, ми йдемо {пішки}.
  - Ми їдемо в ресторан {автобусом}.
- type: match-up
  focus: Match question to logical response for navigation
  items: 6
  pairs:
  - Вибачте, як дістатися до бібліотеки?: Ідіть прямо, потім направо.
  - Де музей?: Він у центрі.
  - Як ти дістаєшся на роботу?: Їду автобусом.
  - Школа далеко?: Ні, близько. П'ять хвилин пішки.
  - Куди ви йдете?: У магазин.
  - Де ти живеш?: На вулиці Франка.
connects_to:
- a1-034 (Where From?)
prerequisites:
- a1-032 (Transport)
grammar:
- 'Synthesis: Де? (locative) + Куди? (accusative) in real navigation'
- Direction + transport + location combined
- 'Imperative preview: ідіть, їдьте (formal commands)'
register: розмовний
references:
- title: Synthesis of M28-M32 skills
  notes: Applied communication — no new grammar, just integration.

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

**Plan vocabulary (9/9 confirmed):**
- ✅ **пішки** — adv, confirmed
- ✅ **хвилина** — noun (f), confirmed
- ✅ **район** — noun (m), confirmed
- ✅ **центр** — noun (m), confirmed (4 matches including different declension entries)
- ✅ **вибачте** — verb form of вибачити, confirmed
- ✅ **дістатися** — verb, confirmed
- ✅ **ідіть** — imperative of іти, confirmed
- ✅ **їдьте** — imperative of їхати, confirmed
- ✅ **поруч** — adv + prep, confirmed (3 matches: поруч/adv, поруч/prep, поруччя/noun — module should use adverb form)

**Extended vocabulary check (additional plan words):**
- ✅ **направо** — adv, confirmed
- ✅ **наліво** — adv, confirmed
- ✅ **прямо** — adv, confirmed
- ✅ **праворуч** — adv, confirmed (preferred Ukrainian directional)
- ✅ **ліворуч** — adv, confirmed (preferred Ukrainian directional)
- ✅ **зупинка** — noun, confirmed
- ✅ **площа** — noun, confirmed
- ✅ **куток** — noun, confirmed (alternative to "ріг" for "corner")
- ❌ **рог** — NOT FOUND. The Ukrainian word for "corner/street corner" is **ріг** (locative: **на розі**). "Рог" is a Russian ghost form. Plan uses "на розі" — this is **correct**. Do NOT write "рог" anywhere; always use "ріг/на розі".

---

## Textbook Excerpts

### Section: Діалоги — Asking directions / дістатися
> "Складіть і розіграйте діалог із гостем / гостею міста Харкова. Допоможіть зорієнтуватися в метро. Треба дістатися від станції «Майдан Конституції» до станції «Перемога»."
> Source: Avramenko, Grade 7 (§59–60, Прислівник — tier 1, 2024)

**Pedagogical note:** Textbook uses **дістатися від X до Y** as the canonical navigation formula — confirms the plan's dialogue structure. Gratitude formulas also present: "Дуже вдячний / Щиро вдячний / Сердечно дякую!" — include at least one in dialogues.

### Section: Де і куди — в/на + locative vs. accusative
> "Прийменник на вживають з: вулицями, проспектами, площами — *на проспекті Миру, на вулиці Басейній*. Уживання прийменника в (у) з назвами засобів пересування підкреслює знаходження всередині предмета: *читав у машині*. Говорячи про пересування, можна використати безприйменникову конструкцію: *пересуватися поїздом, трамваєм, автобусом*."
> Source: Glazova, Grade 11 (§16 — tier 2)

> "У місцевому відмінку з географічними назвами міст, сіл, держав уживаємо прийменник у (в). З просторовими іменниками типу Черкащина, Вінниччина та іменниками — назвами гір — уживаємо прийменник на."
> Source: Zabolotnyi, Grade 11 (Синтаксична норма — tier 2)

**Pedagogical note:** The textbooks teach a **three-way transport contrast**:
1. Static inside: в автобусі (у метро)
2. Mode of travel: автобусом / на метро
3. Streets/squares always: на + locative (на вулиці Франка, на площі)

### Section: Мій район
> "Насправді дорога до парку не була такою близькою, як казав Артем, бо здолати три звивисті вулиці — це значило здолати три довгі-довгі вулиці. Обійстя, де замешкали Градові, стояло край селища."
> Source: Zabolotnyi, Grade 8 Ukrainian Literature (tier 1, 2025)

> "Складіть і запишіть складний план твору-опису вулиці... Місце розташування і розміри. Окраса вулиці. Житлові будинки, магазини, підприємства, установи. Місця відпочинку."
> Source: Zabolotnyi, Grade 8 Ukrainian Language (§570, tier 1, 2025)

**Pedagogical note:** Grade 8 textbook has a full **neighbourhood description task** with street elements (тротуар, зелені насадження, житлові будинки). Use this structure for the "Мій район" paragraph template.

### Section: Підсумок — route description
> "У містах багато високих будинків. Біля будинків є майданчики для дітей. У містах є музеї, театри, супермаркети. Вулицями міст їздять тролейбуси, трамваї, автобуси, маршрутні таксі."
> Source: Bolshakova, Grade 1 (Буквар, M/м chapter — tier 2)

**Pedagogical note:** Grade 1 already introduces city vocabulary (місто, вулиця, парк, метро, площа, супермаркет). The M33 summary section can confidently recycle all these A1 words.

---

## Grammar Rules

- **в/на with streets and squares**: Streets, avenues, squares → **на + locative**: *на вулиці Шевченка, на площі, на проспекті*. Confirmed by Glazova Grade 11 §16 and Avramenko Grade 11.
- **в/на with cities and closed spaces**: Cities, buildings entered → **в/у + locative**: *у центрі, в магазині, в офісі*. Confirmed by Glazova Grade 11 §15.
- **Transport**: Mode of travel → **instrumental without preposition**: *автобусом, метро* OR *на + locative*: *на метро, на автобусі*. Both are standard. Confirmed by Glazova Grade 11 §16.
- **Direction "до" vs "в"**: Movement towards a destination → **до**: *іти до бібліотеки, їхати до центру*. Presence/action inside → **в/у**: *у парку, в офісі*. Confirmed by Антоненко-Давидович (ad-219) and Glazova Grade 11 §15.
- **Locative mandatory with prepositions**: Місцевий відмінок вживається тільки з прийменниками. Confirmed by Zaharijchuk Grade 4.

---

## Calque Warnings

- **"вибачаюся"**: ⚠️ **CALQUE / ERROR** — Антоненко-Давидович (ad-127) explicitly flags this: "так сказати не можна, бо частка —ся означає себе, отже, виходить, що людина вибачає саму себе." Correct forms: **вибачте мені, пробачте мені, простіть мені, я перепрошую**. ✅ Plan correctly uses **вибачте** (imperative) — this is fine. **Never write вибачаюся in the module.**
- **"дістатися до"**: ✅ OK — natural Ukrainian, confirmed by Антоненко-Давидович context (ad-219 discusses до vs в/у for motion verbs).
- **"пішки"**: ✅ OK — native Ukrainian adverb, A1 in PULS, no style guide warnings.
- **направо / наліво vs. праворуч / ліворуч**: ⚠️ **PEDAGOGY NOTE** — Both forms are in VESUM and grammatically correct. However, Ukrainian pedagogy (Avramenko, Zaболотний) consistently teaches **праворуч / ліворуч** as the primary directional adverbs. "Направо/наліво" are acceptable secondary forms. **Recommendation:** Introduce **праворуч/ліворуч** as primary, **направо/наліво** as alternatives. Do not teach направо/наліво alone.

---

## CEFR Check

- **пішки**: A1 ✅ — perfectly level-appropriate
- **хвилина**: A1 ✅ — perfectly level-appropriate
- **район**: A1 ✅ — perfectly level-appropriate
- **центр**: A1 ✅ — perfectly level-appropriate
- **вибачте**: A1 (as exclamation/formulaic phrase) ✅ — perfectly level-appropriate
- **поруч**: A2 ⚠️ — PULS lists as A2 (adverb). One level above target. Acceptable as **preview/receptive vocabulary** at A1.5, but do not test productively in activities. Pair it with A1 synonym **близько** (near).
- **дістатися**: ⚠️ NOT FOUND in PULS directly. Closest matches: дійти (B1), досягти (B1). The full construction "як дістатися до...?" is a **survival communication chunk** — teach it as a **fixed phrase**, not as a decomposed verb. Frame it explicitly as a "useful phrase for real life" with a note that the verb will be studied properly at B1. Do NOT ask learners to conjugate it in activities.
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
# Verified Knowledge Packet: Around the City
**Module:** around-the-city | **Phase:** A1.5 [Places]
**Textbook grades searched:** 4, 5, 6

---

## Діалоги (Dialogues)

> **Source:** avramenko, Grade 6
> **Section:** Сторінка 120
> **Score:** 0.25
>
> 120
> ЖИВИЛЬНІ  ДЖЕРЕЛА  МУДРИХ  КНИЖОК
> — Тю, — ледве сказав Ява.
> — Тьху, — ледве сказав я. 
> Це вся розмова, на яку ми спро­моглися.
> І тільки за хвилин двадцять ми нарешті отямились і змогли обміняти-
> ся думками з приводу того, що сталося.
> — Так ... — зітхнув Ява. — Можна сказати, зіпсував ти мені кар’єру. 
> А що?! Хто ж мене тепер у міліцію візьме...
>  
> 1.	 Хрещатик «утикається» на Європейській площі в
> А	 метро «Арсенальна»
> Б	 метро «Хрещатик»
> В	   колишній костел
> Г	   філармонію
> 2.	 	Репліка «Лізь, голубе, під землю, як усі люди» адресована
> А	 інтелігентному дідусеві 
> Б	 опасистому дядьку
> В  	міліціонерові
> Г  	 інтуристу
> 3.	 Установіть відповідність.
> Ге­рой по­віс­ті
> Опис зов­ніш­нос­ті 
> 1	 мі­лі­ці­о­нер
> 2	 дядь­ко  в мет­ро
> 3	 ін­ту­рист	
> А	 «...

## Де і куди разом (Where and Where To Together)

> **Source:** kravtsova, Grade 4
> **Section:** Сторінка 20
> **Score:** 0.50
>
> 1
> 53. 1. Прочитай текст. Що цікавого ти дізнався / дізналася?
> Хочеш здійснити подорож у часі? Тоді уяви себе в старовин­
> ному місті. Як ти гадаєш, де можна побачити найбільше людей? 
> Так, на торжку
> *!
> Ось стельмах продає вози та сани. Ось підійшов гутник. Він 
> виготовляє скло та вироби зі скла.
> Сьогодні все по-іншому. Відповідно — інші професії. Напри­
> клад, коуч або коучка допомагають іншим досягнути поставленої 
> мети. Маркетолог або маркетологйня організовують продаж 
> товарів чи послуг. Дієтолог або дієтологйня розробляють індиві­
> дуальні схеми харчування. А ким хочеш стати ти?
> 2. Знайди орфограми в тексті та поясни їхнє написання.
> 3. Виконай завдання на вибір.
> о Спиши абзац, у якому найбільше нових слів.
> о Спиши абзац, у якому найбільше застарілих слів.
> 54.

## Мій район (My Neighborhood)

> **Source:** zabolotnyi, Grade 6
> **Section:** Сторінка 51
> **Score:** 0.50
>
> 51
> Лексикологiя.  Фразеологiя
> Моя найкраща подруга – Наталка. Ми всігда разом ходимо
> до школи, бо живемо на сусідських вулицях. Кожного тижня 
> провідуємо бабусю Оксану, допомагаємо їй вимити пол, пості-
> рати, принести води. Наша бабуся чуйна, лагідна, вона володіє
> рідким даром: уміє розповідати цікаві бувальщини.
> РОЗРІЗНЯЙМО
> Сусі‘дній – розташований поруч, поблизу чогось (сусідній 
> район, сусідня школа).
> Сусі‘дський – належний, властивий сусідові (сусідський
> хлопець, сусідський кіт).
> * * *
> Рідкий – 1) який перебуває у стані рідини (рідкий борщ); 
> 2) у якому складники розміщені нещільно (рідкий ліс).
> Рі‘дкісний – який буває, трапляється дуже рідко (рідкісний
> талант, рідкісна книжка).
> САМООЦІНКА. Продовжте усно фрази.
> 1. Під час вивчення теми «Лексикологія.

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 38
> **Score:** 0.25
>
> 35
> 73.	 І. Розгляньте ілюстрації, прочитайте наведені біля них слова.
> Музична школа // 
> Музикальний слух
> Освітлена вулиця //  
> Освічена дівчинка
> Парне молоко // 
> Парові котлети
> Сусідні будинки // 
> Сусідський собака
> ІІ. Обравши одну з ілюстрацій, поясніть лексичне значення наведених 
> біля неї слів. Коли доречно вживати кожне із цих слів?
> 74.	 ЧОМУ ТАК? Поміркуйте, чому в першому реченні вжито слово 
> військовий, а в другому – воєнний.
> 1. Збройні сили України мають на озброєнні сучасну вій-
> ськову техніку.
> 2. У музеї розгорнуто виставку воєнної тематики.
> 75.	 Спишіть речення, добираючи з дужок потрібне слово. За потреби 
> скористайтеся словничком паронімів у додатках. 
> 1. Ось коли б молочка (парного, парового), – молочка я б 
> випив (А. Шиян). 2.

> **Source:** ponomarova, Grade 4
> **Section:** Сторінка 23
> **Score:** 0.25
>
> 23
> 1. Прочитай цікаву інформацію про французів. Розкажи,
> як  ти  ставишся  до  свого  харчування.
> Сніданок, обід, вечеря, їжа та всі пов’язані з ними 
> слова — священні для французів. Конкурувати
> з ними можуть тільки регбі, велосипед, футбол. 
> Про харчування дбають у французьких шко-
> лах. Учні молодших класів мають велику перерву,
> під час якої можуть піти додому, щоб пообідати.
> ДОСЛІДЖУЮ ФРАЗЕОЛОГІЗМИ
> ДОСЛІДЖУЮ ФРАЗЕОЛОГІЗМИ
> 2. Прочитай, що дізналася Читалочка про вподобання 
> французьких  друзів. Поясни значення виділених висло-
> вів. Прочитай правило про такі вислови. 
> Андре полюбляє кататися 
> на велосипеді. Як тільки випа-
> дає нагода — він сідає на свого 
> двоколісного коня і мчить як
> вітер. А Луїза любить солодощі. 
> Найбільше їй до вподоби еклери 
> із заварним кремом.

## Підсумок — Summary

> **Source:** litvinova, Grade 6
> **Section:** Сторінка 126
> **Score:** 0.50
>
> Розділ 5. Іменник 
> 126
> Пирогів варто відвідати в пе-
> ріод релігійних свят — Різдва, 
> Великодня, 
> Івана 
> Купала 
> чи 
> Спаса, адже в цей час у музеї 
> проходять 
> надзвичайно 
> цікаві 
> й  колоритні дійства.
> Дістатися до музею можна ав-
> тобусом № 27 від станції метро 
> «Либідська».
>  (За матеріалами туристичного 
> порталу «IGotoWorld»)
> 2. Випишіть із тексту власні назви, поясніть їхній правопис. Над кожною 
> назвою надпишіть номер правила, яке регулює написання великої лі-
> тери (за правилами на с. 123—124).
> 3. Випишіть у  словничок незнайомі вам слова.
> 4. Сформулюйте основну думку тексту. Запишіть ключові слова — теги, 
> за якими би ви шукали інформацію про музей в  інтернеті. Стисло пе-
> рекажіть текст так, щоб розповідь могла зацікавити ваших друзів чи 
> подруг.
> 5.

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 207
> **Score:** 0.25
>
> 204
> 4. Іду та людей питаю: «Де тут дорога до рідного краю?» 
> (В. Симоненко).
> ІІ. Прочитайте виразно речення вголос, правильно їх інтонуючи.
> На письмі пряму мову завжди беремо в лапки, а перше 
> слово пишемо з великої букви. 
> Якщо слова автора стоять 
> ПЕРЕД прямою мовою, то піс-
> ля них ставимо ДВОКРАПКУ 
> Онук похвалився дідусеві: 
> «Я навчився плавати».
> Бабуся питає: «А хто до-
> поможе мені води прине-
> сти?»
> Якщо слова автора стоять 
> ПІСЛЯ прямої мови, то перед 
> ними ставимо КОМУ (знак 
> питання або знак оклику) й 
> ТИРЕ. 
> Слова автора після прямої 
> мови починаємо з малої букви
> «Я навчився плавати», – 
> похваливсь онук дідусеві. 
> «А хто допоможе мені 
> води принести?» – пи-
> тає бабуся.
> Речення з прямою мовою можна зобразити за допомогою 
> таких схем: 
> 1. А: «П».	
> 	
> 3. «П», – а.
> 2. А: «П!»	
> 	
> 4.

> **Source:** zabolotnyi, Grade 6
> **Section:** Сторінка 85
> **Score:** 0.33
>
> Запишіть, дотримуючись правил уживання великої букви та лапок. Йогурт (в)олошкове (п)оле, (с)пасо-(п)реображенський (с)обор 
> (Чернігів), (д)омініканський (с)обор (Львів), (м)узей історії Ки-
> єва, (к)омета (г)аллея, вебсайт (ш)коляр, (з)ахідне (п)оділля,
> (д)ень (п)сихолога, автомобіль (т)есла, станція метро (п)окров-
> ська, (ф)ранцузька (р)еспубліка, (г)алактика (с)пляча (к)расуня, 
> вулиця (с)ічових (с)трільців, (к)ерченська (п)ротока. 225 
> 226 
> 227 
> 228
> 229
> 230
> 231

## Grammar Reference

> **Source:** golub, Grade 5
> **Section:** Сторінка 125
> **Score:** 0.25
>
> 125
>   Відповідно до поставлених запитань сформулюйте особисті 
> цілі. 
> 310   Прочитайте епіграф. Чи поділяєте ви думку автора? Що ви уяв-
> ляєте, коли звучить слово «мандрівка»? Якого кольору це слово? 
> А яке воно на смак і дотик? Чому? А які у вас відчуття, коли це 
> слово входить у плани вашої родини під час канікул? Складіть 
> три речення з однорідними членами відповідно до заданого 
> змісту.
> 1. Скажіть, куди б ви хотіли помандрувати. От дуже-дуже 
> хотіли б!
> 2. Які речі обов’язково мають бути в наплічнику під час 
> мандрівки?
> 3. Чого найбільше ви очікуєте від омріяної подорожі?
> 311   І   Розгляньте таблицю. Чи всі пункти правил вам зрозумілі? 
> Перекажіть їх своїми словами.

> **Source:** avramenko, Grade 6
> **Section:** 

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Де і куди разом (Where and Where To Together)` (~300 words)
- `## Мій район (My Neighborhood)` (~300 words)
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

PLAN-AWARE EXEMPTIONS: The following bans are RELAXED for this module because the plan explicitly teaches these constructs: Perfective aspect (plan teaches perfective verbs). Exception: If a grammar construct appears in this module's plan grammar list or objectives, it is ALLOWED for this module.

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
  1. **Walking tour of Lviv old town — going from Площа Ринок (f, main square) to Оперний театр (m, Opera house) to Високий замок (m, High Castle). Де ми? На площі. Куди далі? В театр. Звідки прийшли? З замку.**
     Speakers: Гід (guide), Туристи
     Why: Де/Куди/Звідки with площа(f), театр(m), замок(m), парк(m)

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

**Required:** пішки (on foot), хвилина (minute, f), район (neighborhood, m), центр (center, m), вибачте (excuse me)
**Recommended:** дістатися (to get to), ідіть (go! — imperative, preview), їдьте (go by transport! — imperative, preview), поруч (nearby)

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

- P1 (~50 words): Framing — navigating a Ukrainian city means doing two things at once: saying where you *are* (де? + locative) and where you're *going* (куди? + accusative), while asking for and giving directions. Two real situations follow: a stranger asking for help, and a friend describing their daily commute.

- Dialogue 1 (~110 words): Tourist asks for directions on a Lviv street. Full dialogue: — Вибачте, як дістатися до бібліотеки? — Ідіть прямо, потім направо. Бібліотека на розі. — А музей? — Музей далеко. Їдьте на метро до центру. — Дякую! Annotation: вибачте (excuse me — polite formula), ідіть/їдьте (go! — formal imperative preview, foot vs transport), на розі (at the corner — locative chunk). Note: ідіть = going on foot; їдьте = going by vehicle.

- Dialogue 2 (~110 words): Two colleagues talk about their morning route. Full dialogue: — Як ти дістаєшся на роботу? — Спочатку йду на зупинку. Потім їду автобусом до центру. — А потім? — Потім іду пішки п'ять хвилин. Робота в офісі на площі. Annotation: sequence words спочатку → потім → а потім (first → then → and then). Structure: verb of motion + destination in accusative (їду автобусом до центру). Contrast: їду автобусом (by bus) vs іду пішки (on foot).

- Exercise (fill-in, 6 items): Directions with прямо / направо / наліво. Items include: "Ідіть {прямо}, потім {направо}. Бібліотека на розі." and "Вибачте, як дістатися до музею? — Ідіть {наліво}." and "Аптека близько. Ідіть {прямо} п'ять хвилин." Learner selects from three direction words.

---

## Де і куди разом (Where and Where To Together) (~330 words total)

- P1 (~80 words): Real Ukrainian navigation never uses just one question — it switches constantly between де? (where = static) and куди? (where to = motion). Four example sentences showing the alternation in a single journey: Я зараз у парку. (де? — locative: у + парк → у парку) → Я йду в магазин. (куди? — accusative: в + магазин → unchanged) → Магазин на вулиці Шевченка. (де? — locative: на + вулиця → на вулиці) → Потім їду на роботу. (куди? — accusative: на + робота → на роботу). Highlight the pattern visually: question → preposition → case.

- P2 (~120 words): Synthesis table — four rows covering all navigation situations:
  | Ситуація | Питання | Форма | Приклад |
  |---|---|---|---|
  | Де ти? (static) | Де? | в/на + locative | Я в офісі. На площі. |
  | Куди йдеш? (motion) | Куди? | в/на + accusative | Іду в театр. На роботу. |
  | Яким транспортом? | Як? Чим? | автобусом / на метро / пішки | Їду автобусом. На метро. |
  | Відстань | Далеко? | далеко / близько / хвилин пішки | П'ять хвилин пішки. |
  Each row includes one complete sentence. Emphasis: on метро stays on (на метро — not в метро), while в театр / в магазин use в.

- P3 (~80 words): Connected narrative paragraph applying all four rows: Марія живе у Львові (де? — locative). Сьогодні вона йде в театр (куди? — accusative). Театр на площі (де? — locative). Потім вона їде на метро до центру (куди? — accusative). Центр далеко — п'ять хвилин на метро, а потім іде пішки три хвилини. Learner sees the question type shift six times in natural prose.

- Exercise (quiz, 6 items): Choose correct form — в парку / в парк, в магазин / в магазині, на вулиці / на вулицю, на роботу / на роботі, у центрі / у центр, в офіс / в офісі. Each question gives a sentence with a gap and two options; learner identifies де? vs куди? then picks correct case form.

---

## Мій район (My Neighborhood) (~330 words total)

- P1 (~90 words): Model neighborhood description — first-person anchor text a learner can adapt: Я живу на вулиці Франка. Біля мого дому є парк і маленький магазин. Школа далеко — треба їхати автобусом десять хвилин. Аптека близько, можна піти пішки. У моєму районі є кафе, два ресторани і бібліотека. Annotation of key structures: біля мого дому (near my house — genitive chunk, learn as a unit), є + noun list (there is/are), треба їхати / можна піти (must go by vehicle / can go on foot — modal + infinitive chunk).

- P2 (~90 words): Vocabulary in action — five city-life phrases each used in a complete sentence:
  - пішки → Аптека близько — іду пішки.
  - хвилина → П'ять хвилин пішки від зупинки.
  - далеко від / близько від → Школа далеко від дому. Парк близько від роботи. (teach as chunks, not parsed grammar)
  - У центрі міста → Готель у центрі міста.
  - на околиці → Я живу на околиці, не в центрі.
  Pattern note: далеко/близько від + genitive — memorize the full chunk (далеко від + noun).

- P3 (~100 words): Scaffolded production — learner's own neighborhood, three fill-in-yourself model sentences with blank slots: (1) Я живу [де — вулиця/місто?]. (2) Біля мого дому є [що?]. [Place] [далеко/близько]. Треба їхати [чим?] / Можна піти пішки. (3) У моєму районі є [list 3 places]. Three complete example outputs shown as alternatives: for a city-center dweller, a suburban dweller, a small-town dweller. Reinforces that the sentence frames stay identical regardless of location.

- Exercise (fill-in, 6 items): Transport — на метро / автобусом / пішки. Items include: "Я їду в центр {на метро}.", "Школа далеко, треба їхати {автобусом}.", "Парк близько, ми йдемо {пішки}.", "Потім іду {пішки} п'ять хвилин." Learner must select the appropriate transport form from the three options.

---

## Підсумок — Summary (~330 words total)

- P1 (~100 words): Urban communication toolkit — structured recap in five categories:
  - **Запитати дорогу:** Вибачте, як дістатися до [місця]? / Де знаходиться [місце]?
  - **Напрямок:** прямо → направо → наліво → на розі
  - **Де? (locative):** в/на + locative: у парку, в театрі, на вулиці, на площі
  - **Куди? (accusative):** в/на + accusative: у парк, в театр, на вулицю, на площу
  - **Транспорт:** автобусом / на метро / пішки — [кількість] хвилин пішки
  Each line has one concrete sentence. Presented as a reference card learners can screenshot.

- Self-check (~130 words): Five production prompts as a numbered list — learner answers mentally or aloud before checking:
  1. Ти стоїш на вулиці. Незнайомець запитує, як дістатися до бібліотеки. Бібліотека: прямо, потім ліворуч. Що ти скажеш? *(Answer: Ідіть прямо, потім наліво. Бібліотека там.)*
  2. Опиши свій ранковий маршрут трьома реченнями: спочатку... потім... а потім... *(Free production — no single answer.)*
  3. Вибери правильну форму: Я зараз — *в театрі* чи *в театр*? Я йду — *в театрі* чи *в театр*? *(Answers: в театрі / в театр.)*
  4. Як сказати "five minutes on foot"? *(П'ять хвилин пішки.)*
  5. Де ти живеш? Що є біля твого дому? Скажи двома реченнями. *(Free production using Я живу на... Біля мого дому є...)*

- Exercise (match-up, 6 pairs): Navigation Q&A — learner matches question to most logical response: Вибачте, як дістатися до бібліотеки? → Ідіть прямо, потім направо. / Де музей? → Він у центрі. / Як ти дістаєшся на роботу? → Їду автобусом. / Школа далеко? → Ні, близько. П'ять хвилин пішки. / Куди ви йдете? → У магазин. / Де ти живеш? → На вулиці Франка.

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
