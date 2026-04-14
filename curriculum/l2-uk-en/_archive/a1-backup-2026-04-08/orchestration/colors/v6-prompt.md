

---

## Your Writing Identity

**You are: Patient & Supportive Ukrainian Tutor.** Your persona is *The Helpful Teacher*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **10: Colors** (A1, A1.2 [My World]).

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
module: a1-010
level: A1
sequence: 10
slug: colors
version: '1.1'
title: Colors
subtitle: Синій, жовтий — the colors of Ukraine and your world
focus: vocabulary
pedagogy: PPP
phase: A1.2 [My World]
word_target: 1200
objectives:
- Name 12 basic colors in Ukrainian
- Use color adjectives with correct gender agreement (including soft-stem синій)
- Distinguish синій (dark blue) from блакитний (light blue) — a distinction English
  lacks
- Describe objects using color + M09 adjective combinations
dialogue_situations:
- setting: 'At an outdoor flower market — choosing bouquets for different occasions.
    Describe: червоні троянди (roses), білі лілії (lilies), жовті соняшники (sunflowers),
    синя ваза (f), зелене листя (n, leaves). Use flowers, plants, and wrapping.'
  speakers:
  - Наталка
  - Продавець (flower seller)
  motivation: 'Color adjectives: червоний/а/е with троянда(f), соняшник(m), листя(n)'
- setting: 'Choosing an outfit for a party from a friend''s wardrobe. Describe: чорна
    сукня (f, dress), білий светр (m, sweater), сіре пальто (n, coat), коричневі черевики
    (pl, shoes). Use clothing items, NOT bags.'
  speakers:
  - Дмитро
  - Ліза
  motivation: 'Color + gender: сукня(f), светр(m), пальто(n), черевики(pl)'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Choosing a gift (Большакова Grade 2 p.38 colors poem as inspiration):
    — Яка гарна сумка! Якого вона кольору? — Червона. А є ще синя і зелена.
    — Мені подобається синя. — А мені — жовта! Colors emerge naturally through shopping
    scenario. Note: Мені подобається is a memorized chunk (like У мене є) — dative grammar is A2.'
  - 'Dialogue 2 — Describing your room (extending M08-M09): — Якого кольору твоя кімната?
    — Біла. — А стіл? — Стіл коричневий. А крісло — сіре. Review: gender
    agreement + new color vocabulary.'
- section: Кольори (Colors)
  words: 300
  points:
  - '12 basic colors organized by adjective type: Hard-stem (-ий/-а/-е — same pattern
    as M09): червоний/червона/червоне (red) жовтий/жовта/жовте (yellow) зелений/зелена/зелене
    (green) чорний/чорна/чорне (black) білий/біла/біле (white) сірий/сіра/сіре (grey)'
  - 'Soft-stem (-ій/-я/-є — NEW pattern): синій/синя/синє (dark blue) Вашуленко Grade
    3 p.130: adjectives divide into тверда група (-ий) and м''яка група (-ій). Only
    синій is soft-stem among basic colors — learn it as a special case now. Compare:
    великий стіл → синій стіл, велика книга → синя книга, велике вікно → синє вікно.'
- section: Синій ≠ блакитний (Blue ≠ Blue)
  words: 300
  points:
  - 'Ukrainian has TWO blues — English has one: синій = dark blue, deep blue (the
    sea, the night sky, ink) блакитний = light blue, sky blue (a clear daytime sky,
    baby blue) Прапор України — синьо-жовтий (Кравцова Grade 2 p.22: Синьо-жовтий
    прапор маєм: синє — небо, жовте — жито). Cultural note: ''голубий'' is a Russian-influenced
    word for light blue — use блакитний.'
  - 'More colors for describing things: коричневий (brown), рожевий (pink), помаранчевий
    (orange), фіолетовий (purple). These are all hard-stem (-ий/-а/-е). Compound colors:
    темно-зелений (dark green), світло-синій (light blue-ish). Cultural hook: вишиванка
    — traditional embroidered shirt, typically червоний і чорний (Полісся) or червоний
    і синій (Полтавщина).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Color agreement follows the same rules as M09: Hard-stem: червоний стіл, червона
    книга, червоне вікно. Soft-stem: синій стіл, синя книга, синє вікно. Self-check:
    What color is the Ukrainian flag? (синьо-жовтий) Describe 3 things in your room
    using colors. What''s the difference between синій and блакитний?'
vocabulary_hints:
  required:
  - червоний (red)
  - жовтий (yellow)
  - зелений (green)
  - синій (dark blue — soft-stem!)
  - блакитний (light blue, sky blue)
  - білий (white)
  - чорний (black)
  - сірий (grey)
  - колір (color, m)
  - якого кольору? (what color?)
  recommended:
  - коричневий (brown)
  - рожевий (pink)
  - помаранчевий (orange)
  - фіолетовий (purple)
  - темний (dark — as prefix: темно-)
  - світлий (light — as prefix: світло-)
  - прапор (flag, m)
activity_hints:
- type: quiz
  focus: Якого кольору? Match objects to their typical color.
  items: 8
- type: fill-in
  focus: 'Gender agreement with colors: син__ книга, червон__ стіл, біл__ вікно'
  items: 10
- type: quiz
  focus: синій or блакитний? Choose the right shade of blue.
  items: 6
- type: group-sort
  focus: Sort colors into тверда група (-ий) and м'яка група (-ій)
  items: 10
connects_to:
- a1-011 (How Many?)
prerequisites:
- a1-009 (What Is It Like?)
grammar:
- 'Soft-stem adjectives: синій/синя/синє (-ій/-я/-є) vs hard-stem (-ий/-а/-е)'
- Color adjective agreement follows M09 rules
- Compound colors with темно-/світло- (hyphenated)
register: розмовний
references:
- title: Большакова Grade 2, p.38
  notes: 'Colors poem: синє, чорне, зелене, блакитне, червоне, жовте, золоте, оранжеве.'
- title: Вашуленко Grade 3, p.130
  notes: 'Hard vs soft adjective groups: новий (тверда) vs синій (м''яка).'
- title: Кравцова Grade 2, p.22-23
  notes: 'Синьо-жовтий прапор маєм: синє — небо, жовте — жито.'

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

**Confirmed (28/28 — 100% pass rate):**

Core adjectives (nominative): червоний ✅, жовтий ✅, зелений ✅, синій ✅, блакитний ✅, білий ✅, чорний ✅, сірий ✅, коричневий ✅, рожевий ✅, помаранчевий ✅, фіолетовий ✅, темний ✅, світлий ✅

Inflected forms tested: червона ✅, синя ✅, зелена ✅, жовта ✅, біла ✅, сіре ✅, синє ✅, синього ✅

Nouns: колір ✅, кольору ✅, прапор ✅

Question word: якого ✅

Compound adjectives: темно-зелений ✅, світло-синій ✅

**Not found: none.**

> ⚠️ **Note on голубий**: Not in the plan vocabulary, and rightly so — plan correctly avoids it. However, the plan's framing ("голубий is a Russian-influenced word — use блакитний") needs softening: голубий **is** in VESUM and appears in Grade 3 Savchuk textbook ("Голубий, бо небо голубе") and Grade 10 Avramenko lists it as a valid synonym. Better framing: "блакитний is the standard recommended form; голубий is used in older texts but блакитний is preferred in modern standard Ukrainian." Do **not** call it a Russianism — that is inaccurate.

---

## Textbook Excerpts

### Section: Кольори (Colors) — Hard/Soft stem paradigm

> "До твердої групи належать прикметники, основа яких у називному відмінку однини закінчується на твердий приголосний. НАПРИКЛАД: веселий, Андріїв, материн. До м'якої групи належать прикметники, основа яких закінчується на м'який приголосний. НАПРИКЛАД: синій, безкраїй."
> **Source: Заболотний, Grade 6, p. 143** (tier 2)

Full paradigm table confirmed (same source):
```
Тверда група: новий / нового / новому / новим ...
М'яка група:  синій / синього / синьому / синім ...
              синя  / синьої  / синій   / синьою
              синє  / синього / синьому / синім
```

> "Прикметники поділяють на дві групи — тверду та м'яку. До твердої групи належать прикметники з основою на твердий приголосний: білий, дружний. До м'якої групи належать прикметники з основою на м'який приголосний: **синій**, дружній, мужній."
> **Source: Авраменко, Grade 6, p. 132** (tier 1 — highest trust)

**Pedagogical note:** синій is THE canonical м'яка група example in every Grade 6 textbook. The plan's choice to introduce синій as the special soft-stem case is exactly how Ukrainian teachers do it.

---

### Section: Синій ≠ блакитний

> "Блакитний — колір із довжиною хвилі приблизно від 450 до 485 нанометрів, діапазон — між зеленим і синім, ближче до синього; п'ятий колір веселки. Для позначення синього, блакитного кольорів та їхніх відтінків використовують слова: **голубий**, бірюзовий, сапфіровий, лазуровий, світло-синій, темно-синій, яскраво-синій, колір морської хвилі, аквамариновий, ультрамариновий, ніжно-блакитний, блаватний (блават — волошка), волошковий."
> **Source: Авраменко, Grade 10, p. 37** (tier 2)

> "Голубий, бо небо голубе, — сказав Сашко. — Червоний, бо червона кров... — Жовтий, бо я його люблю..."
> **Source: Savchuk, Grade 3, p. 6** — natural classroom dialogue about colors (tier 2)

**Pedagogical note for writer:** The two-blues distinction (синій vs. блакитний) is confirmed. At A1, keep it simple: синій = dark blue (sea, night sky), блакитний = sky blue (daytime sky). The cultural hook (прапор України — синьо-жовтий) is directly supported by multiple Grade 2 sources.

---

### Section: Прапор (Cultural hook)

> "Синьо-жовтий прапор маєм: синє — небо, жовте — жито; прапор свій оберігаєм, він святиня, знають діти."
> **Source: Кравцова, Grade 2, p. 22** — poem "Прапор" by Наталка Поклад ✅ **EXACT match to plan reference**

> "1918 року Центральна Рада визначила синьо-жовтий прапор державним символом... Його кольори символізували чисте небо, що розкинулося над жовтим морем хлібного лану."
> **Source: Заболотний, Grade 5, p. 41** (tier 1) — full factual context

> "УКРАЇНСЬКИЙ ПРАПОР — Де жовте і блакитне удвох, там настає весна! Бо разом вони дають зелену барву."
> **Source: Кравцова, Grade 2, p. 23** — narrative using **блакитний** (not синій) for the flag's blue — ⚠️ see flag note below

> ⚠️ **FLAG for writer:** Grade 2 Kravtsova uses both **блакитний** (p.23 narrative) and **синьо-жовтий** (p.22 poem) for the flag. Вашуленко Grade 2 (p.82) also uses **блакитний** when describing the flag's blue. The official state flag color name is **синій** (синьо-жовтий прапор is the official term). At A1, teach: **прапор України — синьо-жовтий**. Note that young children sometimes say блакитний informally — but синьо-жовтий is the correct official compound.

---

### Section: Діалоги (Shopping scenario)

No exact Grade 2 shopping dialogue found in RAG for colors + shopping. Best textbook grounding found:

> "— Голубий, бо небо голубе. — Червоний, бо червона кров. — Зелений, бо зелені листя й трава. — Жовтий, бо я його люблю. — Чорний, бо він найтемніший."
> **Source: Savchuk, Grade 3, p. 6** — natural classroom discussion about favorite colors

**Writer note:** The gift-shopping dialogue in the plan ("Яка гарна сумка! Якого вона кольору?") is pedagogically sound and natural. Яка гарна + Якого кольору? + color adjectives in nominative — this is confirmed natural A1/A2 speech. The Мені подобається chunk is fine as a memorized chunk (confirmed no calque — see below).

---

## Grammar Rules

The Правопис §5 query hit letter Г, not adjective declension. However, the **textbook** sources are more authoritative for pedagogical purposes at A1 and provide complete paradigm confirmation:

- **Тверда vs. м'яка група**: Confirmed in Заболотний Gr.6 p.143, Авраменко Gr.6 p.132, Голуб Gr.6 p.134, Авраменко Gr.11 p.25 — all use синій as canonical м'яка group example.
- **Soft-stem endings**: синій / синя / синє (Nom.) → singled out as the only basic color in м'яка група ✅
- **Hard-stem pattern** (червоний/червона/червоне): confirmed against новий/нова/нове paradigm ✅
- **Compound color adjectives with hyphen** (темно-зелений, світло-синій): confirmed in Авраменко Gr.10 p.122 — written with hyphen when two distinct colors are named ✅

---

## Calque Warnings

- **"голубий"** (avoided in plan): **NOT a strict Russianism** — present in VESUM and Ukrainian Grade 3 textbook. Correct framing: блакитний is standard and preferred; голубий exists but is less formal. No calque, just register/register preference. ✅ Plan vocabulary correctly omits it.
- **"Мені подобається"**: **OK** — standard Ukrainian dative construction. Style guide found no calque entry. Антоненко-Давидович does not flag this phrase. ✅
- **"якого кольору?"**: **OK** — confirmed natural Ukrainian question form. No calque. ✅ (Avramenko Grade 10 uses "Які кольори переважають?" and "якого кольору" implicitly throughout.)
- **"фарба" vs "барва"**: Style guide (Антоненко-Давидович, ad-076) warns: use **барва** for visual color impression, **фарба** only for physical paint/dye. Plan vocabulary uses **колір** — correct and safest choice for A1. ✅

---

## CEFR Check

| Word | PULS Level | Status |
|---|---|---|
| червоний | **A1** | ✅ On target |
| колір | **A1** | ✅ On target |
| синій | **A1** | ✅ On target |
| блакитний | **A1** | ✅ On target |
| прапор | **A1** | ✅ On target |
| фіолетовий | **A2** | ⚠️ One level above A1 |
| помаранчевий | **A2** | ⚠️ One level above A1 |

**Notes on A2 items:** фіолетовий and помаранчевий are PULS-rated A2. The plan introduces them in the "more colors" subsection alongside коричневий and рожевий (not individually PULS-checked, likely also A2). This is **acceptable** for an A1 module — these are basic colors learners need for everyday description, and Ukrainian primary school textbooks introduce the full color palette in Grade 1-2 regardless of CEFR. Flag for the writer: treat these as **enrichment vocabulary** (passive recognition at A1, active use at A2+), not as core A1 target items.

---

## Summary for Writer

| Check | Result |
|---|---|
| VESUM (all 28 forms) | ✅ 100% pass |
| Textbook backing (м'яка група / синій) | ✅ Confirmed in 4+ Grade 6 sources |
| Textbook backing (прапор / синьо-жовтий) | ✅ Exact match in Кравцова Gr.2 p.22 |
| Синій ≠ блакитний distinction | ✅ Confirmed in Авраменко Gr.10 p.37 |
| Compound colors (темно-, світло-) with hyphen | ✅ Confirmed |
| Calque check (3 phrases) | ✅ No calques found |
| голубий framing in plan | ⚠️ Soften — not a Russianism, just non-preferred |
| CEFR (core colors) | ✅ A1 |
| CEFR (фіолетовий, помаранчевий) | ⚠️ A2 — treat as enrichment |
| Flag/blue color naming (синій vs блакитний) | ⚠️ Official = синьо-жовтий; some Gr.2 texts say блакитний informally |
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
# Verified Knowledge Packet: Colors
**Module:** colors | **Phase:** A1.2 [My World]
**Textbook grades searched:** 1, 2, 3

---

## Діалоги (Dialogues)

> **Source:** kravcova, Grade 2
> **Section:** Сторінка 56
> **Score:** 0.25
>
> 56
> 198. 1.	 Прочитай вірш. Що нового ти дізнався (дізналася)?
> В будинку мешкали слова,
> жили собі щасливо.
> На кожнім поверсі — по два:
> недбалий і дбайливий.
> А ще — веселий і сумний,
> гарячий і холодний,
> жили чистенький і брудний
> та ситий і голодний. (Валентина Бутрім)
> 2.	 Обміняйтеся зошитами та перевірте, чи правильно виконане 
> завдання.
> 200.
> 199. 1.	 Добери і запиши протилежні за значенням слова.
> Добрий — ... .	 	
> Велике — ... .
> День — ... . 	
> 	
> Важкий — ... .
> Коротка шия, як драбина, 
> в світлих плямах жовта спина, 
> листячко з дерев зриває, 
> в холодку працює.

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

> **Source:** savchuk, Grade 3
> **Section:** Сторінка 6
> **Score:** 0.50
>
> 6
> џ
> У якому класі навчалися учні? Як вони поводилися на 
> уроці? Чим учителька зацікавила бешкетників? Чи 
> змінилася поведінка учнів після слухання оповідки?
> џ
> Прочитай заголовок наступної частини. Як ти гадаєш, про 
> що в ній ітиметься?
> — Голубий, бо небо голубе, — сказав Сашко.
> — Червоний, бо червона кров, — промовила Олеся.
> — Зелений, бо зелені листя й трава, — сказав Максим.
> — Жовтий, бо я його люблю, — додала Наталя.
> — Чорний, бо він найтемніший, — сказав наостанку Пет-
> русь.
> — Ні, любі мої, найголовніший колір білий, бо білого 
> кольору світло, завдяки якому ми бачимо всі інші кольори. 
> Але знайте, що без синього, жовтого, зеленого, червоного нема 
> й білого.

## Кольори (Colors)

> **Source:** bolshakova, Grade 2
> **Section:** Сторінка 38
> **Score:** 0.25
>
> 38
> сЛова — назви ознак 
> Вірш. Головний герой. Опис
> КРІТ І СОНЦЕ
> З нірки виліз старий кріт і розплющив очі:
> — Сонце кольору якого? Подивитись хочу.
> синє, чорне чи зелене, мов травиця в лісі?
> Чи блакитне і прозоре, як вода у річці?
> І сказали ми кроту: «Що за дивина!
> Сонце — стиглий помаранч 
> дивин
> , не якась трава. 
> червоне, жовте, золоте, оранжеве, блискуче…
> тепле, ніжне, променисте, інколи пекуче…
> — Не люблю я апельсинів, — тихо мовив кріт
> І спустився в підземелля рити новий хід.
> • Прочитай вірш без виділених слів. Що змінилося? 
> • Випиши слова, які називають ознаки сонця. 
> Зразок. Сонце (яке?) червоне.
> Слова — назви ознак предметів відповідають 
> на питання який? зелений 
> , яка? зелена 
> , 
> яке? зелене 
> , які? зелені 
> . Це прикметники. 
> Розглянь таблицю.

## Синій ≠ блакитний (Blue ≠ Blue)

> **Source:** kravcova, Grade 2
> **Section:** Сторінка 22
> **Score:** 0.50
>
> Роз’єднай слова і прочитай прислів’я.
> Депрапорпіднімають,тамУкраїнувеличають.
> • 
> Поясни, як ти розумієш це прислів’я.
> Послухайте вірш Наталки Поклад «Прапор».
> • 
> Коли відзначають День Державного Прапора?
> Прочитай вірш.
> ПРАПОР
> Прапор — це державний символ, 
> він є в кожної держави; 
> це для всіх — ознака сили, 
> це для всіх — ознака слави. 
> Синьо-жовтий прапор маєм: 
> синє — небо, жовте — жито; 
> прапор свій оберігаєм, 
> він святиня, знають діти.
> Прапор свій здіймаєм гордо, 
> ми з ним дужі і єдині, 
> ми навіки вже — з народом, 
> українським, в Україні.
> • Що символізують кольори на Державному Прапорі України?
> • Прочитай виділені рядки.

> **Source:** zaharijchuk, Grade 1
> **Section:** Сторінка 41
> **Score:** 0.33
>
> 39
> 	
> Прочитай букви, виділені блакитним кольо-
> ром. Яке слово утворилося? Який заголовок 
> до вірша можна дібрати?
> У нас красивий, гарний край:
> Квіти, море, річка, гай!
> Рідне все: поля, діброви,
> А сади які чудові!
> Їх краса — це білий цвіт...
> Ненька наша, Україна,
> Адже ти для нас єдина!
>                                     Дмитро Гонтар
> 	
> Знайди на «полі складів» слова — назви пред-
> метів, які є народними символами України. 
> Звертай увагу на кольори складів. 
> ле
> пи
> тів
> лас
> лю
> ви
> оф
> ка
> ли
> ка
> ер
> ле
> іч
> на
> на
> ши
> сан
> ван
> ка
> ні
> вер
> ус
> ка
> ба
> ка
> 	 До яких із них можна поставити питання хто?
> Pidruchnyk.com.ua

## Підсумок — Summary

> **Source:** bolshakova, Grade 2
> **Section:** Сторінка 81
> **Score:** 0.50
>
> 81
> Прочитай речення з  різною інтонацією. Запиши речення, 
> ставлячи наприкінці крапку або знак оклику.
> Прийми дарунок (. !)	
> Любіть Україну (. !)
> Відвідай виставку (. !)	
> Бережіть природу (. !)
> 
> Запиши спонукальні речення. Підкресли слова — назви дій 
> двома лініями.
> Червоний колір часто попереджає про небезпеку. Черво-
> не світло світлофора сигналізує: «Не переходь вулицю зараз! 
> Це небезпечно.» У лісі червоного жучка сонечко видно здаля. 
> Він наче говорить: «Не їжте мене! Я  отруйний!» У  Червону 
> книгу записують рідкісних тварин і  рослини. Наче просять: 
> «Не знищуйте природу! Бережіть довкілля!»
> 
> Текст. Заголовок. Спілкування в  Інтернеті
> Спілкування в Інтернеті може бути небезпечним.  Виконуй 
> правила безпеки в Інтернеті. Спілкуйся зі знайомими людьми.

## Grammar Reference

> **Source:** bolshakova, Grade 1
> **Section:** Сторінка 45
> **Score:** 0.50
>
> 45
> Прочитай. Склади речення зі словами в першому стовп-
> чику. Скористайся малюнками.
> 	
> синє	
> раннє	
> літнє	
> переднє	
> заднє
> 	
> давнє	
> вечірнє	 осіннє	
> середнє	 дружнє
> 	
>   
> море
> місто   
> 
> Текст. Тема тексту. Заголовок. Театралізуємо
> Чи буває синє каченя?
> Єва намалювала синє небо. У небі намалюва-
> ла синє літнє сонце. Буяє синє безкрайнє море. 
> А  в морі плаває синє каченя. 
> — Гарно вийшло? — запитала Єва. 
> — Це все несправжнє, — сказав Євген. — 
> Такого не буває.
> — Буває! — вигукнула Євгенка. — Я одягну 
> окуляри із синіми скель-ця-ми, і світ стане синім! 
> Синє поле, синє осіннє листя, синє молоко, синє 
> какао… Синій світ…
> — Не-справ-жнє, але красиве! — прошепотіла 
> Єва.
> А ти як думаєш?
> 1
> 2
> Є є
> не – нє	
> те – тє	
> ле – лє


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

### Рід іменників
> **Source:** МійКлас — [Рід іменників](https://www.miyklas.com.ua/p/ukrainska-mova/6-klas/imennik-43064/rid-imennikiv-42978)

### Теорія:

*www.ua.pistacja.tv*  
**Рід притаманний кожному іменнику в однині**. Іменники мають постійне значення **роду**:
чоловічого: *день, зошит, комп'ютер*,  жіночого: *книга, земля, машина*, середнього: *сонце, місто, озеро*, спільного: *суддя, сирота, нечема, за

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Кольори (Colors)` (~300 words)
- `## Синій ≠ блакитний (Blue ≠ Blue)` (~300 words)
- `## Підсумок — Summary` (~300 words)
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
  1. **At an outdoor flower market — choosing bouquets for different occasions. Describe: червоні троянди (roses), білі лілії (lilies), жовті соняшники (sunflowers), синя ваза (f), зелене листя (n, leaves). Use flowers, plants, and wrapping.**
     Speakers: Наталка, Продавець (flower seller)
     Why: Color adjectives: червоний/а/е with троянда(f), соняшник(m), листя(n)
  2. **Choosing an outfit for a party from a friend's wardrobe. Describe: чорна сукня (f, dress), білий светр (m, sweater), сіре пальто (n, coat), коричневі черевики (pl, shoes). Use clothing items, NOT bags.**
     Speakers: Дмитро, Ліза
     Why: Color + gender: сукня(f), светр(m), пальто(n), черевики(pl)

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

**Required:** червоний (red), жовтий (yellow), зелений (green), синій (dark blue — soft-stem!), блакитний (light blue, sky blue), білий (white), чорний (black), сірий (grey), колір (color, m), якого кольору? (what color?)
**Recommended:** коричневий (brown), рожевий (pink), помаранчевий (orange), фіолетовий (purple), {'темний (dark — as prefix': 'темно-)'}, {'світлий (light — as prefix': 'світло-)'}, прапор (flag, m)

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
## Діалоги (Dialogues) (~330 words total)

- P1 (~30 words): Scene-setter: "Colors are everywhere around you — in markets, in wardrobes, in the Ukrainian flag. Listen to how Ukrainians talk about them."
- Dialogue 1 (~110 words): Flower market scene — Наталка and Продавець. Наталка asks про квіти для подруги. Colors emerge naturally: *Червоні троянди* (М: троянда, яка? — червона), *жовті соняшники* (М: соняшник, який? — жовтий), *білі лілії* (F pl: лілія, яка? — біла). Продавець suggests *синя ваза* as a gift add-on, Наталка spots *зелене листя* in the wrapping. Include *Якого кольору...?* and *Мені подобається синя* as natural chunks.
- P-note 1 (~30 words): Brief annotation: *Мені подобається* = "I like" — a memorized chunk (dative grammar is A2; learn it as a phrase now, like *У мене є*).
- Dialogue 2 (~110 words): Wardrobe scene — Дмитро helps Ліза choose an outfit for a party. Objects: *чорна сукня* (F), *білий светр* (M), *сіре пальто* (N), *коричневі черевики* (Pl). Дмитро asks *Яка ця сукня?* → *Чорна.* Ліза says *Але є білий светр і сіре пальто.* Дмитро: *Мені подобається сіре пальто!* — uses all four genders in natural exchange.
- P-note 2 (~50 words): Annotation box: spot the pattern — the adjective ending changes to match the noun's gender: *сукня* (яка?) → *чорна*; *светр* (який?) → *білий*; *пальто* (яке?) → *сіре*. This is the same rule as M09 — colors follow it exactly.

---

## Кольори (Colors) (~335 words total)

- P1 (~45 words): Introduce adjective question: *який? яка? яке? які?* — the same four forms from M09. Colors are adjectives (*прикметники*), so they answer these questions. Reference: Большакова Grade 2 p.38 poem "Кріт і Сонце" — colors listed as *синє, чорне, зелене, блакитне, червоне, жовте* as answer prompts.
- P2 (~100 words): Hard-stem colors (*тверда група*, ending -ий/-а/-е). Present all six as a formatted mini-table with M / F / N columns: *червоний / червона / червоне* (red); *жовтий / жовта / жовте* (yellow); *зелений / зелена / зелене* (green); *чорний / чорна / чорне* (black); *білий / біла / біле* (white); *сірий / сіра / сіре* (grey). Note the shared pattern: drop -ий, add -а (F) or -е (N). Three example phrases: *червоний олівець, червона книга, червоне вікно.*
- P3 (~90 words): Introduce soft-stem adjective (*м'яка група*) — синій. Explain: most colors end in -ий (hard), but *синій* ends in -ій (soft). Compare side-by-side: *великий стіл → синій стіл* (М), *велика книга → синя книга* (F), *велике вікно → синє вікно* (N). The soft stem changes -ій → -я → -є. Source: Вашуленко Grade 3 p.130 — adjectives split into *тверда* and *м'яка* groups; *синій* is the classic soft-stem example.
- P4 (~50 words): Memory hook: among the 12 basic colors, *синій* is the ONLY soft-stem one. Learn it as a special case. Everything else follows the hard pattern. Mnemonic: *синій* is as special in grammar as it is in culture — it's the blue of Ukraine's flag.
- Exercise (~50 words): **Fill-in** — gender agreement with colors (10 items). Stems given, students supply ending: *червон__ олівець (M), жовт__ хустка (F), зелен__ яблуко (N), чорн__ кіт (M), біл__ сорочка (F), сір__ хмара (F), червон__ поле (N), жовт__ аркуш (M), чорн__ вікно (N), зелен__ трава (F).* Answer key in footnote.
- Exercise (~0 words, embedded in P4 area): **Group-sort** — Sort 10 adjectives into *тверда група* (-ий) vs *м'яка група* (-ій): *червоний, синій, чорний, зелений, ранній, жовтий, сизий, осінній, білий, вечірній.* (Includes two non-color soft-stem adjectives as contrast items from Большакова Grade 1 p.45 list.)

---

## Синій ≠ блакитний (Blue ≠ Blue) (~335 words total)

- P1 (~80 words): Ukrainian has TWO separate words for blue — English has one. *Синій* = dark, deep blue: the color of the sea at night, dark ink, a deep winter sky — *синє море, синій олівець, синя ніч.* *Блакитний* = light, sky blue: a clear afternoon sky, a pale ribbon, baby blue — *блакитне небо, блакитна стрічка.* In English both are "blue." In Ukrainian, choosing the wrong one sounds wrong to a native speaker.
- P2 (~80 words): Cultural anchor — the Ukrainian flag (*прапор*). Poem from Кравцова Grade 2 p.22 — cite two lines directly: *Синьо-жовтий прапор маєм: / синє — небо, жовте — жито.* Explain: the flag's blue stripe is *синій* (deep, sky-at-dusk blue), not *блакитний*. The compound adjective *синьо-жовтий* is hyphenated (two colors joined). Cultural note: *прапор* is m., *державний символ* — presented as vocabulary expansion.
- P3 (~30 words): Usage note in callout box: *Голубий* — you may hear this Russian-influenced word for light blue. In Ukrainian, always use *блакитний.* This is one of those small but important decolonization choices native speakers make.
- P4 (~75 words): Four more colors to expand your palette — all hard-stem (-ий/-а/-е): *коричневий / коричнева / коричневе* (brown — the color of chocolate, wood); *рожевий / рожева / рожеве* (pink — *рожева троянда*); *помаранчевий / помаранчева / помаранчеве* (orange — *помаранчевий апельсин*, ref. Большакова p.38 "Сонце — стиглий помаранч"); *фіолетовий / фіолетова / фіолетове* (purple — *фіолетова квітка*).
- P5 (~35 words): Compound colors with *темно-* and *світло-* (both hyphenated): *темно-зелений ліс, світло-синє небо, темно-коричневий стіл, світло-рожева сукня.* Rule: the prefix *темно-/світло-* modifies shade, the base adjective agrees in gender as normal.
- P6 (~35 words): Cultural hook — вишиванка (traditional embroidered shirt). Color schemes vary by region: *червоний і чорний* (Полісся), *червоний і синій* (Полтавщина). Even in folk art, Ukrainians distinguish shades of blue precisely.
- Exercise: **Quiz — синій or блакитний?** (6 items): *небо вдень (блакитний), нічне небо (синій), дитяча ковдра — light (блакитний), морська вода в глибині (синій), прапор України (синій), стрічка на подарунку — pale (блакитний).*
- Exercise: **Quiz — Якого кольору?** Match 8 objects to their typical color (8 items): *трава (зелена), сніг (білий), ворона (чорна), соняшник (жовтий), помідор (червоний), шоколад (коричневий), небо вдень (блакитне), море вночі (синє).*

---

## Підсумок — Summary (~320 words total)

- P1 (~70 words): Hard-stem recap — rule statement + two example sets. *Червоний стіл (M) → червона книга (F) → червоне вікно (N) → червоні олівці (Pl).* Same pattern for *жовтий, зелений, чорний, білий, сірий, коричневий, рожевий, помаранчевий, фіолетовий.* Drop -ий, add -а (F), -е (N), -і (Pl). These are *тверда група.*
- P2 (~60 words): Soft-stem recap — *синій* is the single soft-stem color. *Синій стіл (M) → синя книга (F) → синє вікно (N) → сині олівці (Pl).* Drop -ій, add -я (F), -є (N), -і (Pl). The soft stem feels different — practice until it's automatic, because you will use it every time you describe the sky, the sea, or the flag.
- P3 (~50 words): *Синій vs блакитний* recap — one sentence each, anchored to the flag: *Прапор України синьо-жовтий.* The blue is *синій* — deep and strong. The sky on a clear afternoon is *блакитне.* You now see a distinction Ukrainian has always had and English does not.
- Self-check (bulleted list, ~140 words):
  - **What color is the Ukrainian flag?** → *Синьо-жовтий* (синій і жовтий)
  - **Describe 3 things in your room using colors.** → E.g.: *Мій стіл коричневий. Моя книга синя. Моє вікно велике і біле.*
  - **What is the difference between синій and блакитний?** → *Синій* = dark blue (sea, night sky, flag). *Блакитний* = light blue (daytime sky, pale ribbon).
  - **Which color adjective has a soft stem (-ій)?** → *Синій* — the only one among basic colors.
  - **How do you ask "what color?"** → *Якого кольору?* (e.g.: *Якого кольору ця сукня? — Чорна.*)
  - **What colors does a traditional вишиванка from Полісся use?** → *Червоний і чорний.*

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
