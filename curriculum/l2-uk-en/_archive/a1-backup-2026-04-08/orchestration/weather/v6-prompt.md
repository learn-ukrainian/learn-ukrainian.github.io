

---

## Your Writing Identity

**You are: Patient & Supportive Ukrainian Tutor.** Your persona is *The Helpful Teacher*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **24: Weather** (A1, A1.4 [Time and Nature]).

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

1. **IMMERSION TARGET: 15-25% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if you exceed it. For early modules, the learner CANNOT READ CYRILLIC — English must dominate. Ukrainian appears only as bolded inline words/phrases. Do NOT write long Ukrainian passages, Ukrainian-only paragraphs, or Ukrainian text without English translation.
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
module: a1-024
level: A1
sequence: 24
slug: weather
version: '1.2'
title: Weather
subtitle: Сьогодні холодно — talking about the weather
focus: vocabulary
pedagogy: PPP
phase: A1.4 [Time and Nature]
word_target: 1200
objectives:
- Describe weather using impersonal constructions (cold, warm, hot)
- Use "іде дощ / іде сніг" pattern for precipitation
- Combine weather with seasons and months
- Ask and answer "What's the weather like?"
dialogue_situations:
- setting: Two friends deciding whether to go hiking — checking weather together
  speakers:
  - Іванко
  - Галя
  motivation: 'Impersonal: Сьогодні холодно, Завтра буде тепло, Іде дощ'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Looking out the window (ULP Ep16 pattern): — Яка сьогодні погода?
    — Сьогодні холодно і йде дощ. — А завтра? — Завтра буде тепло і сонячно. — Добре!
    Тоді завтра гуляємо! Weather + future plans (буде as chunk).'
  - 'Dialogue 2 — Seasons conversation: — Яка пора року тобі подобається? — Мені подобається
    літо. — Чому? — Тому що влітку тепло і сонячно. А тобі? — Мені подобається осінь.
    Восени красиво. Weather + seasons + opinion verbs from M15.'
- section: Яка погода? (What's the Weather?)
  words: 300
  points:
  - 'Impersonal weather expressions (no subject — the weather just IS): Сьогодні холодно.
    (It''s cold today.) Сьогодні тепло. (It''s warm.) Сьогодні спекотно. (It''s hot.)
    Сьогодні прохолодно. (It''s cool.) Заболотний Grade 8 p.126: безособові речення
    передають явища природи. These are adverbs — no subject needed, just the state.'
  - 'Precipitation patterns: Іде дощ. (It''s raining — literally ''rain goes''.) Іде
    сніг. (It''s snowing — ''snow goes''.) Дме вітер. (The wind is blowing.) Світить
    сонце. (The sun is shining.) Хмарно / ясно. (Cloudy / clear.) Note: іде дощ (not
    ''дощить'') is the natural conversational form.'
- section: Погода і пори року (Weather and Seasons)
  words: 300
  points:
  - 'Connecting weather to seasons (M23): Взимку холодно. Іде сніг. (In winter it''s
    cold. It snows.) Навесні тепло. Все зелене. (In spring it''s warm. Everything''s
    green.) Влітку спекотно. Світить сонце. (In summer it''s hot. The sun shines.)
    Восени прохолодно. Іде дощ. (In autumn it''s cool. It rains.)'
  - 'Temperature vocabulary: градуси (degrees) — Сьогодні двадцять градусів. (20 degrees.)
    плюс / мінус — Мінус десять. (Minus 10.) тепло / холодно as nouns: На вулиці тепло.
    (It''s warm outside.) Time words: сьогодні (today), завтра (tomorrow), вчора (yesterday).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Weather toolkit: Question: Яка сьогодні погода? Temperature: холодно, тепло,
    спекотно, прохолодно. Precipitation: іде дощ, іде сніг, дме вітер, світить сонце.
    Sky: хмарно, ясно, сонячно. Seasons: взимку холодно, влітку спекотно. Self-check:
    Describe today''s weather. What''s winter like where you live?'
vocabulary_hints:
  required:
  - погода (weather, f)
  - холодно (cold — adverb)
  - тепло (warm — adverb)
  - дощ (rain, m)
  - сніг (snow, m)
  - сонце (sun, n)
  - сьогодні (today)
  - завтра (tomorrow)
  recommended:
  - спекотно (hot)
  - прохолодно (cool)
  - вітер (wind, m)
  - хмарно (cloudy)
  - ясно (clear)
  - сонячно (sunny)
  - градус (degree, m)
  - вчора (yesterday)
activity_hints:
- type: match-up
  focus: Match the weather phrase to its logical context or season
  pairs:
  - іде дощ ↔ холодно і мокро
  - іде сніг ↔ зима
  - світить сонце ↔ сонячно
  - дме вітер ↔ прохолодно
  - мінус десять ↔ холодно
  - плюс тридцять ↔ спекотно
  - плюс двадцять ↔ тепло
  - хмарно ↔ сонце не світить
- type: fill-in
  focus: Choose the logical weather for the season
  items:
  - Взимку часто {іде сніг|іде дощ|світить сонце}.
  - Влітку дуже {спекотно|холодно|хмарно}.
  - Восени часто {іде дощ|іде сніг|сонячно}.
  - Навесні {тепло|холодно|спекотно} і красиво.
  - Сьогодні мінус п'ять, дуже {холодно|тепло|спекотно}.
  - Сьогодні плюс двадцять п'ять, {тепло|прохолодно|холодно}.
- type: fill-in
  focus: Complete the dialogue about the weather
  items:
  - — Яка сьогодні {погода|сонце|дощ}? — Сьогодні тепло.
  - — Завтра {буде|є|був} сонячно. — Добре, гуляємо!
  - — Яка пора року тобі {подобається|любить|робить}? — Літо.
  - — Чому ти любиш літо? — Тому що влітку {сонячно|холодно|хмарно}.
connects_to:
- a1-025 (My Day)
prerequisites:
- a1-023 (Days and Months)
grammar:
- 'Impersonal constructions: cold/warm/hot (no subject)'
- Іде дощ / іде сніг pattern (literally 'goes rain/snow')
- 'Time adverbs: сьогодні, завтра, вчора'
register: розмовний
references:
- title: Заболотний Grade 8, p.126
  notes: 'Безособові речення: явища природи, стан людини.'
- title: ULP Season 1, Episode 16
  url: https://www.ukrainianlessons.com/episode16/
  notes: Weather vocabulary and expressions.

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
- **Confirmed (16/16):** погода (noun), холодно (adv), тепло (adv + noun), дощ (noun), сніг (noun), сонце (noun), сьогодні (adv), завтра (adv), спекотно (adv), прохолодно (adv), вітер (noun), хмарно (adv), ясно (adv), сонячно (adv), градус (noun), вчора (adv)
- **Not found:** — (all 16 words confirmed)

**Notes:** `тепло` has both adverb and noun readings (VESUM returns 4 matches) — the plan correctly uses it as both predicate adverb (*На вулиці тепло*) and noun (*тепло як іменник*). `дощ` and `сніг` each have 2 entries (singular + plural lemmas). All POS tags match the plan's stated parts of speech.

---

## Textbook Excerpts

### Section: Діалоги (Dialogues) — weather + future plans
> «Складіть діалог (5–7 реплік) на тему «Погода», використавши щонайменше дві пари антонімів. Ви можете скористатися наведеними нижче прикладами: сьогодні – завтра / тепло – холодно / спекотний – холоднуватий»
> **Source:** Заболотний, Grade 5, p. 29 (tier 1)

This directly validates the plan's Dialogue 1 structure (Яка сьогодні погода? + завтра + тепло/холодно contrast). The textbook uses exact same time-word pair *сьогодні – завтра* in a weather dialogue context.

### Section: Яка погода? — impersonal weather expressions
> «Безособові речення найчастіше передають явища природи, фізичний і психічний стан людини... НАПРИКЛАД: 1. А ввечері на вулиці дощить. 2. Мені вдень було холодно.»
> **Source:** Заболотний, Grade 8, p. 126 (tier 1)

Confirms the plan's core pedagogical frame: weather = impersonal sentences, no subject needed. Note: the textbook uses `дощить` (impersonal verb) in one example alongside `іде дощ` — both are attested. The plan's note that `іде дощ` is "the natural conversational form" is accurate.

> ДОВІДКА weather vocabulary for impersonal sentences: «Вечоріє, темніє, похолодало, завітрило, замело, захмарило, сніжить, морозить, дихається, хочеться»
> **Source:** Заболотний, Grade 7, p. 78 (tier 1)

Confirms `захмарило` / `сніжить` as textbook-attested impersonal weather forms.

### Section: Погода і пори року — seasons + weather linking
> «Узимку яблуневий сад відпочивав. Яблуневий сад засипало снігом.» (ЗРАЗОК sentence) + vocabulary list: «тепло – холодно / спекотний – студений»
> **Source:** Заболотний, Grade 5, p. 32 (tier 1)

> «Чудова, тепла, сонячна — це [погода]. Холодний, північний, пронизливий — це [вітер]. Узимку і влітку, у пору осінню й весняну...»
> **Source:** Вашуленко, Grade 2, p. 71 (tier 2)

Both confirm the seasons → weather adjective/adverb linking pattern used in the plan (*Взимку холодно. Іде сніг.*).

### Section: Підсумок — Summary (self-check format)
> «ПРО КОРИСТЬ ХОЛОДУ. Холод – це не завжди погано... Однак від холоду треба й захищатися: одягати шарф і шапку, коли виходите на мороз» + follow-up: «Висловте свої міркування: «Що краще: спекотне літо чи студена зима?»»
> **Source:** Заболотний, Grade 5, p. 29 (tier 1)

Validates the self-check question format in the plan's Summary: "Describe today's weather / What's winter like where you live?"

---

## Grammar Rules

- **Безособові речення for weather**: Правопис 2019 covers orthography, not syntax — no §number applies. The rule is confirmed instead by **Заболотний Grade 8 §47** (Авраменко) and **Grade 8 p.126** (Заболотний): *"Безособові речення найчастіше передають явища природи."* Examples: `Мені холодно.` / `На вулиці дощить.` / `Замело снігом.` — these are the canonical textbook formulations.
- **Predicate adverbs (присудкові прислівники)**: `холодно`, `тепло`, `спекотно`, `прохолодно`, `хмарно`, `ясно`, `сонячно` function as predicates in impersonal sentences. Textbook confirms (Grade 8 Авраменко): *"Утворіть і запишіть безособові речення, у яких слова стихло, тепло, світло, темніє будуть головними членами."* — `тепло` as sentence predicate is explicitly taught.
- **Іде дощ / іде сніг construction**: `іде` as motion verb for precipitation is textbook-attested. Grade 3 (Савченко) uses `дощ` in literary contexts; Grade 8 Зaболотний uses `дощить` as an impersonal verb variant. Both forms are correct; `іде дощ` is the higher-frequency conversational form (plan's claim is accurate).

---

## Calque Warnings

- **іде дощ**: ✅ OK — natural Ukrainian. Антоненко-Давидович does not flag this. Textbook attests both `дощить` and `іде дощ`. No calque issue.
- **дме вітер**: ✅ OK — natural Ukrainian. No flag in style guide. `дме` is the standard verb for wind.
- **світить сонце**: ✅ OK — natural Ukrainian. Style guide discussion of "сонце" contexts (e.g., `призахідне сонце`) does not affect this basic predication.
- **на вулиці тепло**: ✅ OK — Антоненко-Давидович uses `на вулиці` naturally in examples without flagging it. `надворі` is a stylistic alternative but `на вулиці` is fully standard.
- **BONUS — одягати шапку**: ⚠️ **Calque warning** — Антоненко-Давидович explicitly flags this: *"одягати можна одежу... а шапку й окуляри надівають."* If the module includes the sentence *одягай шапку* (from the Summary section's implied cultural note), it must be **надягай шапку**, not **одягай шапку**.

---

## CEFR Check

| Word | PULS Level | Status |
|------|-----------|--------|
| погода | A1 | ✅ on target |
| холодно | A1 | ✅ on target |
| тепло | A1 (adv) | ✅ on target |
| дощ | A1 | ✅ on target |
| сніг | A1 | ✅ on target |
| сонце | A1 | ✅ on target |
| сьогодні | A1 | ✅ on target |
| завтра | A1 | ✅ on target |
| вчора | A1 | ✅ on target |
| градус | A1 | ✅ on target |
| вітер | A1 | ✅ on target |
| прохолодно | **A2** | ⚠️ one level above — present with scaffolding |
| хмарно | **A2** | ⚠️ one level above — present with scaffolding |
| сонячно | **A2** | ⚠️ one level above — present with scaffolding |
| спекотно | **B1** | ❌ two levels above target — flag for writer |
| ясно | **B1** | ❌ two levels above target — flag for writer |

**Recommendation for спекотно / ясно (B1):** These words are pedagogically appropriate for a weather module even at A1 — real weather conversations require them. However, the writer must **explicitly scaffold** them: introduce as "new word you'll hear in weather forecasts," gloss clearly, and not assume passive recognition. Do not treat them as known A1 vocabulary; treat them as pre-taught B1 items within an A1 context. This is consistent with the plan's existing approach for `буде` (future chunk) — productive scaffolding of slightly-above-level items is valid if intentional and labeled.
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
# Verified Knowledge Packet: Weather
**Module:** weather | **Phase:** A1.4 [Time and Nature]
**Textbook grades searched:** 3, 4, 5

---

## Діалоги (Dialogues)

> **Source:** golub, Grade 5
> **Section:** Сторінка 251
> **Score:** 0.50
>
> 251
> Кажу** літу:
> — Ти вже врізало день, щодня доточуєш ночі, підганяєш 
> усіх достигати, а саме — холоднішати. Навіщо? Я ще нічого 
> літнього не встигла.
> А воно мені каже:
> — Якби я чекало, допоки люди перероблять свою роботу, 
> то так ніколи б і не настало. Або ніколи не скінчилося.
> — Другий варіант мені подобається більше.
> — Ну навряд чи тобі хотілось би жити у світі вічнозелених 
> вишень і ніколи недостиглих кавунів. Усьому свій час. Мені 
> час минати потроху.
> — Але ж…
> — Що але ж? Просто не відкладай мене на завтра. Бо кожне 
> завтра я вночі роблю коротшим за сьогодні (А. Акуленко).
> Запитання
> Завдання
> 1. Які слова вжито в перенос-
> ному значенні?
> 2. Скільки звуків позначають 
> букви я, є та ю у виділених 
> словах? Поясніть.
> 3. Як правильно вимовити 
> слово «подобається»?
> 4.

> **Source:** avramenko, Grade 5
> **Section:** Сторінка 27
> **Score:** 0.25
>
> 27
>  § 10. Лексичне  значення  слова
> 1. Прочитайте діалог між братом і молодшою сестрою та виконайте зав­
> дання. 
> — На вулиці посіріло, зірвався вітер, мабуть, зараз піде дощ!
> — Піде?! А хіба дощ може ходити? 
> А. Через яке слово сестра не зрозуміла брата?
> Б. Яка причина непорозуміння?
> Лексичне значення — це те, що означає слово. Наприклад, лексичне 
> значення слова дощ — різновид опадів, що випадають із хмар у вигляді 
> краплин води. 
> Лексичне значення слів можна з’ясувати за тлумачним словником. 
> Слова бувають однозначні та багатозначні. Наприклад, слово годин-
> ник однозначне, адже воно означає лише прилад для вимірювання 
> часу протягом доби. А слово йти багатозначне, бо має багато значень. 
> 1. Ступаючи ногами, пересуватися, рухатися, змінюючи місце в про-
> сторі: ідуть футболісти. 
> 2.

## Яка погода? (What's the Weather?)

> **Source:** avramenko, Grade 5
> **Section:** Сторінка 27
> **Score:** 0.50
>
> 27
>  § 10. Лексичне  значення  слова
> 1. Прочитайте діалог між братом і молодшою сестрою та виконайте зав­
> дання. 
> — На вулиці посіріло, зірвався вітер, мабуть, зараз піде дощ!
> — Піде?! А хіба дощ може ходити? 
> А. Через яке слово сестра не зрозуміла брата?
> Б. Яка причина непорозуміння?
> Лексичне значення — це те, що означає слово. Наприклад, лексичне 
> значення слова дощ — різновид опадів, що випадають із хмар у вигляді 
> краплин води. 
> Лексичне значення слів можна з’ясувати за тлумачним словником. 
> Слова бувають однозначні та багатозначні. Наприклад, слово годин-
> ник однозначне, адже воно означає лише прилад для вимірювання 
> часу протягом доби. А слово йти багатозначне, бо має багато значень. 
> 1. Ступаючи ногами, пересуватися, рухатися, змінюючи місце в про-
> сторі: ідуть футболісти. 
> 2.

## Погода і пори року (Weather and Seasons)

> **Source:** , Grade 4
> **Section:** Сторінка 169
> **Score:** 0.50
>
> Сади цвітуть коли? Навесні,
> Улітку трав поля шовкові,
> А восени врожай збирають,
> Узимку снігу всі чекають.
> Прислівників багато має мова —
> Усі яскраві, всі чудові!
> •  Спишіть вірш. Підкресліть словосполучення прислівника з діє­
> словом. Визначте питання, на які відповідають прислівники.
> •  Позначте будову виділеного прислівника.
> Прислівники не зм іню ю ться, тому вони не мають 
> [ закінчення. Вони закінчую ться суф іксом  або ко - [ 
> « рєнем . Наприклад: весело, завжди, повік, угорі, « 
> І Тцоденно.
> 384. Прочитайте сполучення дієслів із прислівниками.
> Світить (як?) яскраво,.... Світить (де?) високо,.... Ходить 
> (як?) легенько,.... Почулося (звідки?) ззаду,.... Росте (де?) 
> вдалині,.... Сгі\ває(як?) радісно, .... Кружляє (як?) тихо, ... . 
> Написав (коли?) вчора,... .

## Підсумок — Summary

> **Source:** zaharijchuk, Grade 4
> **Section:** Сторінка 105
> **Score:** 0.50
>
> 105
> 249.		Прочитай сполучення слів.
> Столяр (що робить? одн.) майструє, лікарі лікують, са-
> доводи вирощують, спортсмен пливе, птахи прилетіли, 
> синиця співає, шишкарі зимують, комп’ютер працює.
> 	 Запиши сполучення слів, указавши в дужках питання та число 
> за зразком першого.
> 250.		Прочитай прислів’я та прикмету.
> Ноги носять, а руки годують. Сонце гріє, сонце сяє — 
> уся природа воскресає. Ластівки низько літають — дощ 
> обіцяють. Учений іде, а неук слідом спотикається (Нар. 
> тв.).

> **Source:** avramenko, Grade 5
> **Section:** Сторінка 27
> **Score:** 0.33
>
> 27
>  § 10. Лексичне  значення  слова
> 1. Прочитайте діалог між братом і молодшою сестрою та виконайте зав­
> дання. 
> — На вулиці посіріло, зірвався вітер, мабуть, зараз піде дощ!
> — Піде?! А хіба дощ може ходити? 
> А. Через яке слово сестра не зрозуміла брата?
> Б. Яка причина непорозуміння?
> Лексичне значення — це те, що означає слово. Наприклад, лексичне 
> значення слова дощ — різновид опадів, що випадають із хмар у вигляді 
> краплин води. 
> Лексичне значення слів можна з’ясувати за тлумачним словником. 
> Слова бувають однозначні та багатозначні. Наприклад, слово годин-
> ник однозначне, адже воно означає лише прилад для вимірювання 
> часу протягом доби. А слово йти багатозначне, бо має багато значень. 
> 1. Ступаючи ногами, пересуватися, рухатися, змінюючи місце в про-
> сторі: ідуть футболісти. 
> 2.

## Grammar Reference

> **Source:** zaharijchuk, Grade 4
> **Section:** Сторінка 81
> **Score:** 0.50
>
> 81
> Мої навчальні досягнення
> Карта пам’яті: від тексту — до мене
> Прочитайте текст.
> Падає білий лапатий сніг. Пух-
> настий, як ковдра, що подарувала 
> моя бабуся. Світ поволі стає по-
> дібним до чарівної казки. Зранку 
> голубе небо не обіцяло зміни по-
> годи. А перед обідом чисте небо 
> вкрилося (сірий) хмарами. Вони 
> опустилися дуже низько. Суха 
> трава побіліла. Голі дерева гойда-
> лися від зимового вітру. А завтра 
> місто прокинеться в білій льолі. 
> Жваві колядники заспівають йому 
> веселих колядок (За З. Живкою).
> Зміст
> 1.	 Де відбувається подія?
> 2.	 Коли відбувається подія?
> 3.	 Хто веде розповідь?
> Словосполучення
> 1.	Випиши словосполучення, у якому прикметник 
> стоїть у початковій формі.
> 2.	Випиши словосполучення, у яких прикметник у 
> формі середнього роду; жіночого роду.
> 1.


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

### Ознаки словосполучення. Типи зв'язку слів
> **Source:** МійКлас — [Ознаки словосполучення. Типи зв'язку слів](https://www.miyklas.com.ua/p/ukrainska-mova/8-klas/slovospoluchennia-i-rechennia-39534/oznaki-slovospoluchennia-golovne-i-zalezhne-slovo-v-slovospoluchenni-tip_-476383)

### Теорія:

*www.ua.pistacja.tv*  
 
**Словосполучення за будовою поділяються на прості і складні**.

Прості \(непоширені\) словосполучення складаються з двох повнозначних слів — одного головного і одного залежного  \(*сміливий вчинок*\).
У складних словосполученнях \(поширених\) поєднано три й більше повнозначні слова: *\(героїчний подвиг народу*\).
****Залежне слов

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Яка погода? (What's the Weather?)` (~300 words)
- `## Погода і пори року (Weather and Seasons)` (~300 words)
- `## Підсумок — Summary` (~300 words)
- `## Підсумок` (~150 words)

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
  1. **Two friends deciding whether to go hiking — checking weather together**
     Speakers: Іванко, Галя
     Why: Impersonal: Сьогодні холодно, Завтра буде тепло, Іде дощ

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

GRAMMAR CONSTRAINTS (A1.4 — Time & Nature, M22-M28):
Time expressions, days, months, weather, daily routines.

ALLOWED:
- All present tense (from A1.3)
- Time expressions as chunks (О першій, У понеділок)
- Sequence adverbs (спочатку, потім, нарешті)
- Impersonal weather constructions (Сьогодні холодно)

BANNED: Past/future tense, case endings (time chunks only),
participles, passive voice, complex subordination

### Vocabulary

**Required:** погода (weather, f), холодно (cold — adverb), тепло (warm — adverb), дощ (rain, m), сніг (snow, m), сонце (sun, n), сьогодні (today), завтра (tomorrow)
**Recommended:** спекотно (hot), прохолодно (cool), вітер (wind, m), хмарно (cloudy), ясно (clear), сонячно (sunny), градус (degree, m), вчора (yesterday)

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

- P1 (~30 words): Scene-setter — two friends Іванко and Галя stand at a window on a grey morning, deciding whether to go hiking today or tomorrow.
- Dialogue 1 (~110 words): Іванко/Галя — looking out the window. 6-turn exchange: — Яка сьогодні погода? — Сьогодні холодно і йде дощ. — А завтра? — Завтра буде тепло і сонячно. — Добре! Тоді завтра гуляємо! Gloss three key phrases inline: яка погода (what weather), холодно (it's cold), буде тепло (it will be warm). Source: Avramenko Grade 5 p.27 — піде дощ as a natural idiom.
- P2 (~30 words): Bridge note — in Ukrainian weather just IS: no subject, no "it." Сьогодні холодно means exactly "cold today." The language skips the dummy subject English needs.
- Dialogue 2 (~110 words): Іванко/Галя — seasons preference. 8-turn exchange: — Яка пора року тобі подобається? — Мені подобається літо. — Чому? — Тому що влітку тепло і сонячно. А тобі? — Мені подобається осінь. Восени красиво. — А взимку? — Взимку холодно, але красиво. Йде сніг! Gloss: тому що (because), подобається (you like), восени (in autumn).
- P3 (~50 words): Observation box — notice the season-adverbs: взимку, навесні, влітку, восени. These are frozen adverbs (from M23). They don't decline. Pair each with the weather you just heard: взимку — холодно, влітку — тепло, восени — дощ.

---

## Яка погода? (What's the Weather?) (~340 words total)

- P1 (~70 words): Introduce impersonal weather constructions. Ukrainian says Сьогодні холодно — no subject, just the state. Compare the four temperature adverbs side by side: холодно (cold) / прохолодно (cool) / тепло (warm) / спекотно (hot). Each is an adverb that doubles as a predicate — nothing else needed. Source concept: Заболотний Grade 8 p.126, безособові речення для явищ природи.
- P2 (~80 words): Extend with sky conditions: хмарно (cloudy), ясно (clear), сонячно (sunny). Show the contrast — Сьогодні ясно і сонячно vs. Сьогодні хмарно. Then add the two adverbs for time that toggle between today and tomorrow: Сьогодні хмарно. Завтра буде сонячно. Point out буде is used as a chunk here — future marker, not a full verb lesson yet.
- Exercise 1 (~30 words overhead): Fill-in — 6 items choosing the logical weather for the situation: Сьогодні плюс двадцять п'ять, {тепло|прохолодно|холодно}. Сьогодні мінус п'ять, дуже {холодно|тепло|спекотно}. (From activity_hints fill-in set 2, items 5-6 + 2 new temperature items.)
- P3 (~90 words): Precipitation and movement patterns. Іде дощ (rain goes), Іде сніг (snow goes), Дме вітер (wind blows), Світить сонце (sun shines). Textbook hook: Avramenko Grade 5 p.27 dialogue — А хіба дощ може ходити? — sister's confusion shows this is a real idiom, not literal walking. Contrast the four verbs: іде (goes), дме (blows), світить (shines) — each weather phenomenon has its own verb. Learners get all four as fixed chunks.
- P4 (~70 words): Temperature numbers. градуси (degrees) — Сьогодні двадцять градусів. плюс / мінус as temperature operators — Плюс тридцять (hot), Мінус десять (very cold). Show that Ukrainians drop the word градусів in speech: simply Сьогодні мінус десять. Практичний tip: Ukrainian weather forecasts always use Celsius — 20°C is тепло, 30°C is спекотно, −10°C is дуже холодно.

---

## Погода і пори року (Weather and Seasons) (~340 words total)

- P1 (~90 words): Connect weather to all four seasons using the adverbs from M23. Present as four mini-portraits: Взимку холодно. Іде сніг. Все біле. / Навесні тепло. Іде дощ. Все зелене. / Влітку спекотно. Світить сонце. Все квітне. / Восени прохолодно. Дме вітер. Іде дощ. Листя жовте. Each portrait = two weather facts + one nature image. Source pattern: Grade 4 poem (сади цвітуть навесні, улітку трав поля шовкові).
- Exercise 2 (~30 words overhead): Fill-in — 6 items selecting logical weather for the season: Взимку часто {іде сніг|іде дощ|світить сонце}. Влітку дуже {спекотно|холодно|хмарно}. Восени часто {іде дощ|іде сніг|сонячно}. Навесні {тепло|холодно|спекотно} і красиво. (Full activity_hints fill-in set 1.)
- P2 (~80 words): Weather descriptions as opinions. Introduce Мені подобається осінь, бо восени прохолодно і красиво. Show learners how to chain: season adverb + weather word + opinion. Three model sentences: Мені подобається зима, бо іде сніг і все біле. / Я люблю літо, бо спекотно і сонячно. / Навесні подобається, бо тепло і все зелене. Recycling подобається / люблю from M15.
- Exercise 3 (~30 words overhead): Match-up — 8 pairs linking weather phrase to logical context: іде дощ ↔ холодно і мокро / іде сніг ↔ зима / світить сонце ↔ сонячно / дме вітер ↔ прохолодно / мінус десять ↔ холодно / плюс тридцять ↔ спекотно / плюс двадцять ↔ тепло / хмарно ↔ сонце не світить. (Full activity_hints match-up set.)
- P3 (~110 words): Extended dialogue practice — Іванко asks Галя about her dream weather. 8-turn exchange using all vocabulary from the section: — Яка твоя ідеальна погода? — Плюс двадцять, сонячно і без вітру. — А взимку ти любиш сніг? — Так, але тільки коли не дуже холодно. — У Києві зараз мінус п'ять. — О, тоді дуже холодно! А яка погода у тебе? — У мене сьогодні тепло — плюс п'ятнадцять і хмарно. — Добре! Глосс: ідеальна (ideal), без вітру (without wind), тільки коли (only when).

---

## Підсумок — Summary (~310 words total)

- P1 (~60 words): Brief recap — you now have three weather tools: (1) state adverbs for temperature (холодно/тепло/спекотно/прохолодно/хмарно/ясно/сонячно), (2) movement verbs for precipitation and sky (іде дощ, іде сніг, дме вітер, світить сонце), (3) season-weather combinations (взимку холодно, влітку спекотно). Together these cover everything a real conversation about weather needs.
- Weather toolkit box (~80 words): Formatted quick-reference list —
  - Питання: Яка сьогодні погода?
  - Температура: холодно / прохолодно / тепло / спекотно
  - Опади: іде дощ · іде сніг
  - Небо: хмарно · ясно · сонячно
  - Вітер/сонце: дме вітер · світить сонце
  - Градуси: плюс двадцять · мінус десять
  - Час: сьогодні · завтра · вчора
  - Пори року: взимку · навесні · влітку · восени
- Exercise 4 (~30 words overhead): Fill-in dialogue — 4 items completing a short weather exchange: — Яка сьогодні {погода|сонце|дощ}? — Сьогодні тепло. / — Завтра {буде|є|був} сонячно. — Добре, гуляємо! / — Яка пора року тобі {подобається|любить|робить}? — Літо. / — Чому ти любиш літо? — Тому що влітку {сонячно|холодно|хмарно}. (From activity_hints fill-in set 3.)
- Self-check (~80 words): Bulleted prompt list —
  - Опиши сьогоднішню погоду трьома реченнями.
  - Яка погода взимку там, де ти живеш?
  - Яка твоя улюблена пора року і чому?
  - Скажи: tomorrow it will be warm and sunny.
  - Скажи: I like autumn because it's cool.
  - Як сказати "it's raining" українською? А "it's snowing"?
- P2 (~60 words): Preview — next module My Day (M25) builds a full daily schedule. You'll need today's weather to decide what to wear and where to go — all the vocabulary from this module feeds directly into М25 morning routines and outdoor plans.

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
