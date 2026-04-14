

---

## Your Writing Identity

**You are: Patient & Supportive Ukrainian Tutor.** Your persona is *The Helpful Teacher*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **31: Where To?** (A1, A1.5 [Places]).

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
module: a1-031
level: A1
sequence: 31
slug: where-to
version: '1.1'
title: Where To?
subtitle: Іду в банк, на роботу — the accusative for direction
focus: grammar
pedagogy: PPP
phase: A1.5 [Places]
word_target: 1200
objectives:
- Use в/у and на + accusative to answer Куди? (Where to?)
- Distinguish Де? (locative = static) from Куди? (accusative = direction)
- Form basic accusative endings for place nouns
- Navigate between locations using йти/їхати + direction
dialogue_situations:
- setting: 'Running Saturday errands together — splitting up: Я іду в банк (m), а
    ти — на пошту (f). Потім зустрінемося в кафе (n). Also: в аптеку, на зупинку,
    в бібліотеку.'
  speakers:
  - Оксана
  - Степан
  motivation: 'Куди? + accusative: банк(m), пошта(f), кафе(n), аптека(f)'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Where are you going? (ULP Ep18): — Куди ти йдеш? — Я йду в банк.
    А ти? — Я йду на роботу. — А потім? — Потім іду в магазин. — А потім ходімо в кафе!
    Direction vs location: іду В банк (direction) vs я В банку (location).'
  - 'Dialogue 2 — Planning a trip: — Куди ти їдеш у суботу? — Я їду у Львів. — А Олена?
    — Вона їде в Одесу. Cities as destinations: їхати в/у + city.'
- section: Куди? Знахідний відмінок (Where To? Accusative)
  words: 300
  points:
  - 'Grade 4 case helper: Зн. (бачу) — кого? що? For direction: в/у + accusative =
    WHERE TO (motion toward). Compare with locative: в/у + locative = WHERE (static
    position). Де ти? — Я в банку. (locative — you ARE there) Куди ти йдеш? — Я йду
    в банк. (accusative — you''re GOING there)'
  - 'Accusative endings for places: Masculine inanimate: = nominative (no change!):
    банк → в банк, магазин → у магазин, парк → у парк. Feminine -а/-я → -у/-ю: школа
    → у школу, робота → на роботу, бібліотека → у бібліотеку. Neuter: = nominative
    (no change): кафе → у кафе, місто → у місто. Good news: masculine and neuter don''t
    change! Only feminine shifts.'
- section: Де чи куди? (Where or Where To?)
  words: 300
  points:
  - 'The key question pair: Де ти? (Where are you?) → в/у/на + LOCATIVE Куди ти йдеш?
    (Where are you going?) → в/у/на + ACCUSATIVE | Place | Де? (М.в.) | Куди? (Зн.в.)
    | | школа | в школі | у школу | | робота | на роботі | на роботу | | банк | у
    банку | у банк | | парк | у парку | у парк |'
  - 'Motion verbs: йти (to go on foot): Я йду в магазин. їхати (to go by transport):
    Я їду на вокзал. Note: йти = on foot, їхати = by vehicle. Both + в/на + accusative.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Two questions, two cases: Де? → locative (в школі, на роботі) = STATIC Куди?
    → accusative (у школу, на роботу) = DIRECTION Masculine/neuter accusative = nominative
    (no change). Feminine: -а→-у, -я→-ю (школа→школу, бібліотека→бібліотеку). Self-check:
    Where are you? (Де?) Where are you going? (Куди?)'
vocabulary_hints:
  required:
  - куди (where to)
  - йти (to go on foot)
  - їхати (to go by transport)
  - школа → у школу (to school)
  - робота → на роботу (to work)
  - банк → у банк (to the bank)
  recommended:
  - магазин → у/в магазин (to the shop)
  - бібліотека → у бібліотеку (to the library)
  - ресторан → у ресторан (to the restaurant)
  - Одеса → в Одесу (to Odesa)
  - повертатися → додому (to return home)
activity_hints:
- type: quiz
  focus: Де or Куди? Choose the right question for each sentence.
  items: 8
- type: fill-in
  focus: 'Complete: Я йду ___ (школа). Він у ___ (банк).'
  items: 10
- type: group-sort
  focus: 'Sort phrases: Де? (locative) vs Куди? (accusative)'
  items: 10
- type: quiz
  focus: Йти or їхати? Choose based on distance/transport.
  items: 6
connects_to:
- a1-032 (Transport)
prerequisites:
- a1-029 (Where Is It?)
grammar:
- 'Accusative for direction: в/у/на + Зн.в.'
- Де? (М.в.) vs Куди? (Зн.в.) distinction
- 'Accusative endings: m/n = nominative, f: -а→-у, -я→-ю'
- 'Motion verbs: йти (foot) vs їхати (transport)'
register: розмовний
references:
- title: Grade 4 case table
  notes: Зн. (бачу) — кого? що? Helper word method.
- title: ULP Season 1, Episode 18
  url: https://www.ukrainianlessons.com/episode18/
  notes: Accusative case for directions.

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
- **Confirmed (16/16):** куди, йти, їхати, школа, школу, робота, роботу, банк, магазин, бібліотека, бібліотеку, ресторан, Одеса, Одесу, повертатися, додому
- **Not found:** *(none)*

**⚠️ Note on роботу/робота:** VESUM returns 3 matches — both `робот` (robot) and `робота` (work). Context makes the intended lemma `робота` unambiguous; no issue in use, but worth confirming in a sentence context.

---

## Textbook Excerpts

### Section: Діалоги — Куди? (Where are you going?)
> «Уявіть, що ви у відділенні банку. Складіть 2 речення на тему «Візит до банку», використавши 2–3 з поданих сполучень: (у,в) банкоматі / (у,в) касі / (у,в) банку…»
> Source: Заболотний, Grade 10, p. 76

> «Легко йде Іванко до школи» (В. Хронович); «Незабаром учні вирушили зі школи» (О. Донченко); «Добре, що Ярик жив недалеко від школи» (В. Нестайко).
> Source: Литвинова, Grade 7, p. 166 (§27, Прийменник)

**Note:** No direct А1-level "Куди йдеш?" dialogue was retrieved from textbooks. The Grade 10 bank context and Grade 7 preposition examples are the closest matches. The plan's ULP Ep18 dialogue format is not textbook-sourced and should be clearly flagged as supplementary (not primary textbook pedagogy). The approach of contrasting у банк vs у банку is validated by Grade 10 Zabolotnyi's explicit у/в drilling exercises.

### Section: Куди? Знахідний відмінок
> «Усі іменники — назви неістот ч. р, а також іменники с. р. в Зн. в. мають ту саму форму, що і в Н. в.: будинок, сон, стіл; життя, кошеня, море.»
> Source: Кравцова, Grade 4, p. 46 (Розрізнення Називного та Знахідного відмінків)

> «Іменник у формі знахідного відмінка означає предмет, на який спрямована дія, і в реченні виступає додатком.»
> Source: Заболотний, Grade 6, p. 94

**Key pedagogy confirmed:** Masculine inanimate = Nominative (no change) is explicitly taught in Ukrainian textbooks at Grade 4 level. Plan's "Good news: masculine and neuter don't change!" directly mirrors this textbook framing. ✅

### Section: Де чи куди? (Where or Where To?)
> «(на/у) кому? (на/у) чому? → Місцевий відмінок»; «(на) білочці, (у) квасолі / (на) бику(-ові), (у) меду(-ові)»
> Source: Кравцова, Grade 4, p. 48 (Розрізнення Давального і Місцевого відмінків)

> «Відмінок: Зн. в. / Питання: кого? що? / Жіночий: маму, землю / Чоловічий: тата, клен / Середній: курча, листя»
> Source: Кравцова, Grade 4, p. 46 (Accusative paradigm table)

**Note:** The Grade 4 textbook distinction is between Dative and Locative, not directly Locative vs. Accusative for direction. However, the explicit paradigm table for accusative endings (маму/землю for feminine; no change for masculine/neuter) is exactly what the plan's "Де чи куди?" table requires. The plan's Де→локатив / Куди→знахідний contrast is pedagogically sound and grounded in Grade 4 work.

### Section: Підсумок — Summary
> «Назви неістот ч. р. в Зн. в. мають ту саму форму, що і в Н. в.»; «Знахідний відмінок виражає повне охоплення предмета дією.»
> Source: Заболотний, Grade 6, p. 94 + Кравцова, Grade 4, p. 46

---

## Grammar Rules

- **У/В alternation for prepositions:** Правопис §23 — *Before consonants, use* `у` *(у банк, у школу, у магазин, у ресторан); after a vowel or between vowels, use* `в` *(в Одесу — because "їде в Одесу": ends in vowel before vowel-initial city name)*. Specifically: §23.2.1 — «між буквами на позначення голосних: побувала в Одесі» and §23.1.1 — «між буквами, що позначають приголосні: десь у банку». **This rule is CRITICAL for the module** — every "у/в банк, у/в школу, в/у Одесу" example must follow §23. The plan correctly uses both forms; the writer must apply §23 mechanically.

- **Accusative for direction (знахідний відмінок):** Not in Правопис (Правопис covers spelling, not case syntax). Rule is confirmed via textbook sources (Кравцова Gr. 4, Заболотний Gr. 6): feminine -а/-я → -у/-ю; masculine inanimate = nominative; neuter = nominative.

---

## Calque Warnings

- **йти / іти** — OK. Антоненко-Давидович explicitly validates "йти/іти" as natural Ukrainian and warns against the Russian-influenced neologism *крокувати* ("крокувати — нове дієслово, що поширилось…"). Use `йти` / `іти` confidently. ✅
- **повертатися додому** — OK. Антоненко-Давидович cites «чи додому верне» (Нечуй-Левицький) as natural Ukrainian. `додому` is a confirmed Ukrainian adverb, not a calque. ✅
- **йти на роботу / у школу** — OK. No calque issue. Антоненко-Давидович discusses verb government patterns; `йти на роботу`, `йти у школу` are natural Ukrainian prepositional phrases. ✅

---

## CEFR Check

| Word | PULS Level | Status |
|------|-----------|--------|
| куди | A1 | ✅ On target |
| йти / іти | A1 | ✅ On target |
| їхати | A1 | ✅ On target |
| банк | A1 | ✅ On target |
| магазин | A1 | ✅ On target |
| школа | A1 | ✅ On target |
| бібліотека | A1 | ✅ On target |
| ресторан | A1 | ✅ On target |
| повертатися | **A2** | ⚠️ One level above A1 target |

**⚠️ повертатися (A2):** PULS rates this A2. In the module context (A1.5), it appears in the summary phrase `повертатися → додому`. Recommendation: treat it as a **passive/recognition** item only — present the phrase `іду додому` (йти + додому) as the active A1 form, and flag `повертатися додому` as a "bonus" preview. The imperfective `повертатися` and perfective `повернутися` are both rated A2 in PULS.
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
# Verified Knowledge Packet: Where To?
**Module:** where-to | **Phase:** A1.5 [Places]
**Textbook grades searched:** 4, 5, 6

---

## Діалоги (Dialogues)

> **Source:** golub, Grade 5
> **Section:** Сторінка 244
> **Score:** 0.50
>
> 244
> 551   Визначте, які етикетні формули доцільно використовувати 
> в таких ситуаціях. Для чого ми їх використовуємо?
> 1. … ти приніс мені словник? 2. … котра година? 3. … ви не 
> підкажете, як пройти до вулиці Київської? 4. … я не можу 
> виконати це доручення. 5. … з якої колії відправляється 
> потяг № 242? 6. Сергію, відчини, … , вікно.
> 552   Прочитайте вголос діалог і схарактеризуйте його. Які норми 
> мовленнєвого етикету порушено? Відредагуйте діалог так, щоб 
> тональність спілкування набула доброзичливості.
> — Сашку! Іди вечеряти! — гукає мама.
> — Іду! — відповідає син, не відриваючись від монітора.
> — То ти йдеш?
> — Іду! — повторює Сашко, продовжуючи цікаву гру.

## Куди? Знахідний відмінок (Where To? Accusative)

> **Source:** zabolotnyi, Grade 6
> **Section:** Сторінка 203
> **Score:** 0.50
>
> 203
> ЗАХОПЛИВИЙ СВІТ ПРИГОДНИЦЬКИХ І ФАНТАСТИЧНИХ ПОВІСТЕЙ 
> Якось, блукаючи підвалами банку, 
> який прибирала моя бабуся, я виявив 
> невеличкі двері під сходами. Вони 
> були геть непомітні. Ніби хтось їх 
> навмисне 
> замаскував, 
> накидавши 
> біля них цілу купу відер і довгих 
> палиць із кудлатими ганчір’яними 
> насадками для миття підлоги. Тоді, 
> влітку, я розгріб завал, натиснув на 
> ручку дверей. Вони на диво легко від-
> чинилися. Так я знайшов потайний вхід до банку, про який, 
> напевне, давно забули. Я натиснув на клямку невеличких 
> дерев’яних дверцят – і вони розчинилися, пронизливо зари-
> півши.

> **Source:** avramenko, Grade 6
> **Section:** Сторінка 158
> **Score:** 0.25
>
> (...)
> Що ж вони збираються робити в банку? Може, я втрапив до банди гра­біж­
> ників і вони хочуть викрасти золоті зливки, що зберігаються в броньованих 
> підвалах? Тоді мені кінець: банк стереже ціла армія озброєних охоронців, 
> а камери спостереження встановлено в кожному приміщенні. Я так поринув 
> у роздуми, що підскочив мов ошпарений, коли бабуся поклала мені руку на 
> плече.

## Де чи куди? (Where or Where To?)

> **Source:** golub, Grade 6
> **Section:** Сторінка 250
> **Score:** 0.50
>
> 250
> домашня
> адреса
> твій номер
> телефону
> відомості банківських
> карток батьків / опікунів
> твої паролі
> номер 
> або назва
> школи
> твоє місце-
> знаходження
> зараз
> фото й адреси місць,
> які ти часто відвідуєш
> (спортзал, майданчик,
> басейн…)
> особиста інформація
> твоїх друзів, родичів,
> близьких
> 612   Що означають подані фразеологізми? Чи стосуються вони теми 
> уроку? Зробіть висновки.
> 1. Усе добре переймай, а зла уникай. 2. До доброї криниці 
> стежка утоптана. 3. Добре діло роби сміло. 4. Добре ім’я — 
> найкраще багатство. 5. Сіяти добро — добро і пожинати. 
> 613  
> І   Прочитайте текст.

## Підсумок — Summary

> **Source:** ponomarova, Grade 4
> **Section:** Сторінка 2
> **Score:** 0.25
>
> Умовні позначення:
> — розкажи, чи задоволений/задоволена
>      ти своєю роботою на уроці
> — попрацюй у парі або групі
> — виконай роботу олівцем
> — прочитай або розкажи
> — виконай завдання на вибір
> — виконай творче завдання
> — виконай завдання вдома
> — поміркуй і поясни
> — поспілкуйся з однокласниками
> — напиши
> УДК 811.161.2*кл4(075.2)
>  
> П56
> Рекомендовано Міністерством освіти і науки України
> (наказ Міністерства освіти і науки України від 16. 01. 2021 № 53)
> ISBN 978-966-991-114-8 (Ч. 1)
> ISBN 978-966-991-113-1
> © К. І. Пономарьова,
>      Л. А. Гайова, 2021
> © УОВЦ «Оріон», 2021
> — переглянь відео за QR-кодом 
>      на останній сторінці
>  
> Пономарьова К. І.
> П56  
> Українська мова та читання : Підручник для 4 класу 
> ЗЗСО (у 2-х частинах) : Частина 1 // К. І. Пономарьова,
> Л. А. Гайова.

> **Source:** avramenko, Grade 6
> **Section:** Сторінка 166
> **Score:** 0.25
>
> Інструкції отримаєш від …» 
> У цьому місці був відірваний кутик аркуша. Клим прожогом гайнув до свого будинку. 3. Завдання. 4. Який автомобіль  
> найкращий?

> **Source:** kravtsova, Grade 4
> **Section:** Сторінка 116
> **Score:** 0.33
>
> і.
> 314. Допиши словосполучення, вставляючи відповідні прислівники. 
> За потреби користуйся словами для довідки.
> Малює (як?)... , фарбує (коли?)... , іде ... (куди?), знайшли 
> (де?), ішла (як?)..., виграла (коли?)..., грають (як?)....
> Слова для довідки: навмання, гарно, вчора, угору, вранці, 
> завзято.
> внизу,
> 315. 1. Вправа «Квест»*. Розгадай слова.
> 234 7
> 2. До якої частини мови належать слова-відгадки?
> 3. Досліди, чи є закінчення у прислівників.
> Крок 1. Спробуй визначити закінчення в словах-відгадках 
> (пригадай, що для цього потрібно змінити слово).
> Крок 2. Зроби висновок та порівняй його з правилом.
> Прислівники не змінюються, тому в них немає закінчення. | 
> Вони можуть мати суфікс: довкола, тепло, ввечері.
> 316.1. Прочитай. Випиши прислівники.

## Grammar Reference

> **Source:** golub, Grade 5
> **Section:** Сторінка 125
> **Score:** 0.50
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


## МійКлас Theory (miyklas.com.ua)

*Ukrainian school curriculum theory — use this terminology and teaching approach.*

### Словосполучення
> **Source:** МійКлас — [Словосполучення](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/vidomosti-z-sintaksisu-i-punktuatciyi-14562/slovospoluchennia-39535)

### Теорія:

*www.ua.pistacja.tv*  
Словосполучення
Словосполучення — це поєднання дв**ох і більше повнозначних слів**, одне з яких є головним, а інше \(інші\) — залежним\(\-и\). 

Слова у словосполученні поєднуються за допомогою **граматичного зв'язку \(закінчень і прийменників\) або за змістом і граматично.**
Приклад:
Прикласти листок подорожника, зелений  сад, червоний **від** сорому, вивчена напам'ять поезія, занадто далеко.
**Слово**, від якого ставимо запитання, називається головним.
 
**Слово**, до якого ставимо запитання, називається залежним.
Приклад:
Вправа \(яка?\) *цікава*, приїхали \(з якою метою?\) *відпочити*, знайшов \(що?\) *бурштин*, біжу \(яким способом?\) *наввипередки*, черга \(яка?\) *до лікаря*.

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

### Ознаки словосполучення. Типи зв'язку слів
> **Source:** МійКлас — [Ознаки словосполучення. Типи зв'язку слів](https://www.miyklas.com.ua/p/ukrainska-mo

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Куди? Знахідний відмінок (Where To? Accusative)` (~300 words)
- `## Де чи куди? (Where or Where To?)` (~300 words)
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
  1. **Running Saturday errands together — splitting up: Я іду в банк (m), а ти — на пошту (f). Потім зустрінемося в кафе (n). Also: в аптеку, на зупинку, в бібліотеку.**
     Speakers: Оксана, Степан
     Why: Куди? + accusative: банк(m), пошта(f), кафе(n), аптека(f)

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

**Required:** куди (where to), йти (to go on foot), їхати (to go by transport), школа → у школу (to school), робота → на роботу (to work), банк → у банк (to the bank)
**Recommended:** магазин → у/в магазин (to the shop), бібліотека → у бібліотеку (to the library), ресторан → у ресторан (to the restaurant), Одеса → в Одесу (to Odesa), повертатися → додому (to return home)

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

- P1 (~40 words): Scene-setting prose: Saturday morning, Оксана and Степан stand outside their building planning errands. They need to split up — each going a different direction. Introduces Куди ти йдеш? as the natural question.
- Dialogue 1 (~130 words, 8 turns): Оксана asks Куди ти йдеш? — Степан: Я йду в банк. А ти? — Оксана: Я йду на пошту. А потім? — Степан: Потім іду в аптеку. А ти? — Оксана: Я йду в бібліотеку. А потім ходімо в кафе! — Степан: Добре! Зустрінемося в кафе о третій. [8 turns, real Saturday-errand sequence; covers банк(m), пошта(f), аптека(f), бібліотека(f), кафе(n)]
- P2 (~30 words): Callout box — notice: іду В банк (direction — going there) vs я В банку (location — already there). Same preposition в, but the noun ending changes. This is the whole lesson in one pair.
- Dialogue 2 (~100 words, 6 turns): Степан asks Куди ти їдеш у суботу? — Оксана: Я їду у Львів. — Степан: А Олена? — Оксана: Вона їде в Одесу. — Степан: А Микола? — Оксана: Він залишається вдома. А ти? — Степан: Я їду до Харкова на конференцію. [Cities as destinations; їхати for transport; в/у + city name]
- P3 (~30 words): Bridge note — two verbs appeared: йти (on foot — в банк, на пошту) and їхати (by transport — у Львів, в Одесу). Both take the same pattern: в/на + Куди?.

---

## Куди? Знахідний відмінок (Where To? Accusative) (~330 words total)

- P1 (~60 words): Introduce знахідний відмінок using the Grade 4 case-helper method: Зн.в. (бачу) — кого? що? The helper word «бачу» unlocks the form: бачу банк, бачу школу, бачу кафе. For direction, Ukrainian adds в/у or на before that same form: в банк, у школу, у кафе — this is Куди?.
- P2 (~70 words): The core contrast with one noun: Де ти? — Я в банку. (locative — you ARE there, static) vs Куди ти йдеш? — Я йду в банк. (accusative — you're GOING there, motion). Same preposition в, same noun банк — but банку vs банк. The ending on the noun signals static or moving. Same contrast with школа: Де? — в школі. Куди? — у школу.
- P3 (~110 words): Accusative endings table for places — **Masculine inanimate = nominative (no change!):** банк→в банк, магазин→у магазин, парк→у парк, ресторан→у ресторан. **Feminine -а/-я→-у/-ю:** школа→у школу, робота→на роботу, бібліотека→у бібліотеку, аптека→в аптеку, пошта→на пошту, зупинка→на зупинку. **Neuter = nominative (no change):** кафе→у кафе, місто→у місто. Presented as a labeled three-row table with 4 examples per gender.
- P4 (~55 words): "Good news" paragraph — masculine and neuter nouns don't change at all in accusative. Only feminine nouns shift their ending. Memory hook: think of feminine nouns as "leaning forward" toward their destination — школа stretches to школу. If a place name ends in -а or -я, swap it for -у or -ю.
- Exercise: fill-in (10 items) — Complete the sentence with the correct accusative form: 1. Я йду ___ (школа) → у школу. 2. Він іде ___ (банк) → у банк. 3. Ми їдемо ___ (Одеса) → в Одесу. 4. Вона йде ___ (бібліотека) → у бібліотеку. 5. Він іде ___ (магазин) → у магазин. 6. Я їду ___ (Київ) → у Київ. 7. Ти йдеш ___ (аптека) → в аптеку. 8. Вони йдуть ___ (кафе) → у кафе. 9. Я йду ___ (пошта) → на пошту. 10. Ми їдемо ___ (місто) → у місто.

---

## Де чи куди? (Where or Where To?) (~330 words total)

- P1 (~70 words): The two questions explained side by side — Де ти? = Where are you? (static, no movement) → always uses locative case after в/у/на. Куди ти йдеш? = Where are you going? (direction, movement) → always uses accusative case after в/у/на. The prepositions в/у/на are the same in both — it is the noun ending that tells the listener whether you mean position or motion.
- P2 (~90 words): Comparison table with 4 everyday places — laid out as three columns: Place | Де? (locative) | Куди? (accusative): школа → в школі / у школу; робота → на роботі / на роботу; банк → у банку / у банк; парк → у парку / у парк. Two rows added for practice: бібліотека → у бібліотеці / у бібліотеку; магазин → у магазині / у магазин. Point out that на роботі/на роботу uses на (not в) — learned in M29, recycled here.
- Exercise: group-sort (10 items) — Sort these 10 phrases into two columns — Де? (locative) or Куди? (accusative): у школі, у школу, на роботі, на роботу, в банку, в банк, у парку, у парк, у бібліотеці, у бібліотеку.
- P3 (~80 words): Motion verbs — йти and їхати both answer Куди?, but signal different transport. **йти** (on foot): Я йду в магазин. Ти йдеш на зупинку. Він іде в бібліотеку. Use йти for places within walking distance. **їхати** (by vehicle): Я їду на вокзал. Ми їдемо у Львів. Вона їде в Одесу. Use їхати when a bus, train, or car is involved. Quick conjugation reminder: йду/йдеш/іде; їду/їдеш/їде.
- P4 (~50 words): Rule of thumb — if you can walk there in 10 minutes, Ukrainian speakers typically say йти. Cities, other towns, train stations = їхати. But both verbs take в/на + accusative. No change to the noun endings based on which verb you use.
- Exercise: quiz (6 items) — Йти or їхати? 1. Я ___ в магазин за рогом. 2. Ми ___ у Київ завтра вранці. 3. Вона ___ на зупинку автобуса. 4. Він ___ у Харків на конференцію. 5. Діти ___ у школу пішки. 6. Ти ___ на вокзал зараз?
- Exercise: quiz (8 items) — Де or Куди? Choose which question fits each sentence: 1. Я в банку. 2. Я йду в банк. 3. Вона на роботі. 4. Він їде на роботу. 5. Ми в парку. 6. Вони йдуть у парк. 7. Ти в магазині? 8. Куди ти зараз?

---

## Підсумок — Summary (~330 words total)

- P1 (~80 words): Recap the two-question system in plain terms — Ukrainian has two distinct questions for location: Де? (Where are you?) uses locative case → you are already there, static. Куди? (Where are you going?) uses accusative case → you are moving toward a place. Both questions use the same prepositions в/у/на — the noun ending is the only signal. Learners should hear the word after в/у/на and ask themselves: am I there, or going there?
- P2 (~90 words): Accusative endings recap with 8 worked examples — **Masculine inanimate → no change:** банк→у банк, парк→у парк, магазин→у магазин, ресторан→у ресторан. **Neuter → no change:** кафе→у кафе, місто→у місто. **Feminine → -а/-я becomes -у/-ю:** школа→у школу, робота→на роботу, бібліотека→у бібліотеку, аптека→в аптеку, пошта→на пошту. Masculine and neuter: no work needed. Feminine: swap the final vowel.
- P3 (~80 words): Motion verb recap — **йти** (on foot): я йду, ти йдеш, він/вона іде + accusative direction (у школу, в магазин, на пошту). **їхати** (by transport): я їду, ти їдеш, він/вона їде + accusative direction (у Львів, на вокзал, в Одесу). Both verbs answer Куди ти йдеш/їдеш? Both take в/на + accusative.
- Self-check Q&A (~80 words): Bulleted question-and-answer list —
  - Де ти? → Use locative: Я в банку / у школі / на роботі.
  - Куди ти йдеш? → Use accusative: Я йду в банк / у школу / на роботу.
  - Is the place masculine or neuter? → No change in accusative (банк, кафе, місто).
  - Is the place feminine (-а/-я)? → Swap to -у/-ю (школа→школу, бібліотека→бібліотеку).
  - Walking or riding? → йти on foot, їхати by vehicle — same accusative either way.

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
