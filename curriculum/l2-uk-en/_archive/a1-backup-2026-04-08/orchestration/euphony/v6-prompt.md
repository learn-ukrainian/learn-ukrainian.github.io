

---

## Your Writing Identity

**You are: Patient & Supportive Ukrainian Tutor.** Your persona is *The Helpful Teacher*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **28: Euphony** (A1, A1.5 [Places]).

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
module: a1-028
level: A1
sequence: 28
slug: euphony
version: '1.1'
title: Euphony
subtitle: У/в, і/й, з/із/зі — Ukrainian sounds beautiful
focus: phonetics
pedagogy: PPP
phase: A1.5 [Places]
word_target: 1200
objectives:
- Apply у/в alternation based on surrounding sounds
- Apply і/й alternation in conjunctions
- Use з/із/зі correctly before different consonant clusters
- Understand WHY Ukrainian has these rules (avoiding consonant clusters)
dialogue_situations:
- setting: 'Proofreading a friend''s Ukrainian essay about their город (garden) —
    spotting у/в and і/й errors. Text mentions: у городі/в городі, і яблука/й яблука,
    у школі/в школі. Read sentences aloud to hear the difference.'
  speakers:
  - Студент (writing)
  - Друг (correcting)
  motivation: У/в, і/й alternation with город(m), школа(f), яблуко(n)
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Describing where things are: — Де ти живеш? — Я живу в Києві. А
    ти? — Я живу у Львові. — У Львові гарно! Note: в Києві (before К=consonant after
    vowel) vs у Львові (before Л after consonant). Euphony rules make sentences flow
    naturally.'
  - 'Dialogue 2 — Making plans: — Ти й Олена йдете в кіно? — Ні, я і Максим йдемо
    в парк. — А Олена й Тарас? — Вони йдуть у театр. Note: й between vowels (ти й
    Олена), і between consonants (я і Максим).'
- section: У чи В? (У or В?)
  words: 300
  points:
  - 'Авраменко Grade 5 p.117: Чергування у–в забезпечує милозвучність мови. Core rule:
    avoid consonant clusters. В after a vowel before a consonant: живу в Києві, працюю
    в офісі. У after a consonant before a consonant: Тарас у Львові, Максим у банку.
    This applies to both the preposition (в/у) and the prefix (вже/уже).'
  - 'Exceptions to know: At the start of a sentence: У мене є... (always У). After
    a pause or comma: Так, у нас є... (У after pause). Don''t overthink it — native
    speakers use euphony instinctively. The goal: sentences that SOUND smooth, not
    rigid rule application.'
- section: І чи Й? З, із, чи зі?
  words: 300
  points:
  - 'Літвінова Grade 5 p.176: і/й чергування: І between consonants: брат і сестра,
    Тарас і Максим. Й between vowels: мама й тато, вона й він. At sentence start:
    І він прийшов (always І).'
  - 'Літвінова Grade 5 p.177: з/із/зі чергування: З before vowels and most consonants:
    з Одеси, з другом. Із between consonants (avoiding cluster): Максим із Семеном.
    Зі before з, с, ш, щ or consonant clusters: зі мною, зі святом, зі школи. This
    is a smaller rule than у/в but important for natural speech.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Three euphony pairs: у/в — avoid consonant+consonant: у Львові, в Києві. і/й
    — avoid vowel+vowel: брат і сестра, мама й тато. з/із/зі — before difficult clusters:
    з другом, із сестрою, зі мною. Self-check: Which is correct? Я живу (в/у) Києві.
    Мама (і/й) тато. Practice: read your sentences aloud — do they flow smoothly?'
vocabulary_hints:
  required:
  - у/в (in/at — alternating preposition)
  - і/й (and — alternating conjunction)
  - з/із/зі (with/from — alternating preposition)
  recommended:
  - Київ (Kyiv)
  - Львів (Lviv)
  - офіс (office, m)
  - парк (park, m)
  - театр (theater, m)
activity_hints:
- type: quiz
  focus: У or В? Choose correct form based on surrounding sounds.
  items: 10
- type: quiz
  focus: І or Й? Choose correct conjunction.
  items: 8
- type: fill-in
  focus: З, із, or зі? Complete the sentence.
  items: 6
- type: quiz
  focus: Which sentence sounds more natural? (euphony comparison)
  items: 6
connects_to:
- a1-029 (Where Is It?)
prerequisites:
- a1-027 (Checkpoint — Time and Nature)
grammar:
- 'Euphony: у/в alternation (consonant environment)'
- 'Euphony: і/й alternation (vowel environment)'
- 'Euphony: з/із/зі alternation (consonant clusters)'
register: розмовний
references:
- title: Авраменко Grade 5, p.117-118
  notes: Чергування у–в та і–й. Уживання прийменника з.
- title: Літвінова Grade 5, p.174-177
  notes: 'Милозвучність: правила чергування у—в, і—й, з—із—зі.'

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

- **Confirmed (12/12):** у (prep), в (prep), і (conj/part), й (conj/part), з (prep), із (prep), зі (prep), Київ (noun), Львів (noun), офіс (noun), парк (noun), театр (noun)
- **Not found:** none — all plan vocabulary confirmed in VESUM ✅

---

## Textbook Excerpts

### Section: У чи В? (У or В?)

> "Якщо попереднє слово закінчується, а наступне починається на приголосний звук, між ними вживаємо: прийменник у: зустрінемось у школі (не зустрінемося в школі); сполучник і: Сергій і Надія (не Сергій й Надія). Якщо попереднє слово закінчується на голосний, а наступне починається на голосний або приголосний, уживаємо прийменник в або сполучник й."
> **Source: Glazova, Grade 10, §15**

> Table: consonant→у/і→consonant: *син у спортзалі*; vowel→в/й→consonant: *Ольга в салоні*; consonant→в→vowel: *брат в Одесі*; any→у→в/ф/св/сф/кв/хв: *він у вагоні, сестра у Львові*
> **Source: Avramenko, Grade 10, p.73**

> "між буквами, що позначають приголосні: день у день, наш учитель; між буквами, що позначають голосні: навчатися в університеті, наша вчителька"
> **Source: Litvinova, Grade 5, p.174**

### Section: І чи Й? З, із, чи зі?

> Table: у, і — між приголосними: *він у домі, брат умивається; син і мати, дощ іде*; у перед в, ф, кв, тв, льв, хв: *він у вагоні, сестра у Львові*; і перед й, я, ю, є, ї: *її і його, Одеса і Ялта*; в, й — між голосними: *риба в акваріумі, річки й озера*; між голосним і приголосним: *тепло в травні, річки й моря*
> **Source: Avramenko, Grade 5, p.117 (§51-52)** ← exact match for module's section, Tier 1

> Table З/ІЗ/ЗІ: З — перед голосним: *з однокласницями, з Одеси*; ІЗ — між приголосними: *Максим із Семеном*; після голосного перед свистячими/шиплячими: *із цими новинами*; ЗІ — перед сполученням приголосних з початковими з, с, ш, щ: *зі мною, зі святом, зі школи*
> **Source: Litvinova, Grade 5, p.177** ← exact match cited in plan

> "Зі вживаємо: перед сполученням приголосних з початковими з, с, ш, шч: вийшли зі школи; бери зі столу; прибув зі Львова"
> **Source: Zabolotnyi, Grade 5, p.124 (§30)**, Tier 1

### Section: Підсумок — Summary (Dialogue examples)

> "Скупчення збігу голосних або приголосних: нарада відбулась в Кривому Розі → нарада відбулась у Кривому Розі; поїхала у Одесу → поїхала в Одесу"
> **Source: Glazova Grade 10, §15** (excellent exercise material for self-check)

---

## Grammar Rules

- **У/В чергування:** Правопис §23 — "Щоб уникнути збігу букв на позначення приголосних звуків та щоб досягти милозвучності, вживають у між приголосними, на початку речення перед приголосним, незалежно від кінця попереднього слова перед наступними в, ф, льв, зв, св, дв, тв, хв і под."
- **І/Й чергування:** Правопис §24 — "між буквами на позначення приголосних → і; між буквами на позначення голосних → й; між голосним і приголосним → й. **Тільки і** перед й, є, ї, ю, я (напр. Ольга і Йосип, сосни і ялинки). **Тільки і** при зіставленні понять (батьки і діти, правда і кривда)."
- **З/ІЗ/ЗІ чергування:** Правопис §25 — "З перед голосним усередині речення та на початку речення перед приголосним (не свистячим/шиплячим). Із — перед свистячими та шиплячими (з, с, ц, ч, ш, шч), між приголосними. Зі — якщо початкові з, с, ш, шч плюс консонантний кластер (зі Львова, зі школи, зі святом). Зо — тільки з числівниками два, три та із займенником мною."

---

## Calque Warnings

- **"знаходитися" для місця перебування:** CALQUE (Антоненко-Давидович, ad-148) — НЕ вживати! Правильно: *бути, перебувати, жити*. Наприклад: "Я живу в Києві" (не "знаходжуся в Києві"). **The plan correctly uses "живу/живеш" throughout — no calque issue.**
- **"розташований" для міст/будівель:** CALQUE (ad-176) — OK for troops/people temporarily positioned; wrong for cities/buildings. Not relevant to this module.
- **"іти в кіно / в парк / у театр":** OK — natural Ukrainian expressions ✅

### ⚠️ CRITICAL PLAN ERROR FOUND — DIALOGUE 2

The plan's Dialogue 2 contains a **euphony error** that directly contradicts the lesson's own teaching:

> "Ні, **я і Максим** йдемо в парк."
> Plan note: "і between consonants (я і Максим)"

**This is wrong.** "я" ends in the vowel **"а"**, not a consonant. Context: **я** (ends in vowel "а") → conjunction → **Максим** (starts with consonant "М") = **vowel + consonant → use "й"**.

✅ **Correct form:** "Ні, **я й Максим** йдемо в парк."

The plan note must also be corrected: it should read "й between vowel and consonant (я й Максим)", not "і between consonants". Teaching the wrong rule in an euphony module is a critical pedagogical error.

All other dialogue examples check out:
- "Ти й Олена йдете в кіно?" — "ти" ends in "и" (vowel) + "Олена" starts with "О" (vowel) → **й** ✅
- "А Олена й Тарас?" — "Олена" ends in "а" (vowel) + "Тарас" starts with "Т" (consonant) → **й** ✅
- "Вони йдуть у театр" — "йдуть" ends in "ь" (consonant marker) + "театр" starts with "т" (consonant) → **у** ✅
- "йдемо в парк" — "йдемо" ends in "о" (vowel) + "парк" starts with "п" (consonant) → **в** ✅
- "живу в Києві" — "живу" ends in "у" (vowel) + "Києві" starts with "К" (consonant) → **в** ✅
- "живу у Львові" — before "льв" cluster → always **у** (Правопис §23.1.4) ✅
- "Тарас у Львові" — "Тарас" ends in "с" (consonant) + before "льв" → **у** ✅
- "Максим у банку" — "Максим" ends in "м" (consonant) + "банку" starts with "б" (consonant) → **у** ✅

---

## CEFR Check

- **офіс:** A1 ✅ — at level
- **парк:** A1 ✅ — at level
- **театр:** A1 ✅ — at level
- **жити (живу):** A1 ✅ — at level
- **Київ / Львів:** proper nouns, not in PULS CEFR — appropriate at any level, essential Ukrainian geography for A1 ✅
- **у, в, і, й, з, із, зі:** function words / prepositions — A1 ✅

No vocabulary above A1 level found. All plan vocabulary is level-appropriate.
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
# Verified Knowledge Packet: Euphony
**Module:** euphony | **Phase:** A1.5 [Places]
**Textbook grades searched:** 4, 5, 6

---

## Діалоги (Dialogues)

## У чи В? (У or В?)

> **Source:** avramenko, Grade 6
> **Section:** Сторінка 226
> **Score:** 0.50
>
> Чергування у–в та і–й забезпечує милозвучність мови. Завдяки йому 
> уникаємо незручних для вимови збігів голосних і приголосних звуків. Правила чергування у–в та і–й такі: 
> у, і
> між приголосними
> він у домі, брат умивається; син і мати, 
> дощ іде
> у перед в, ф, кв, тв, льв, 
> хв і под. і перед й, я, ю, є, ї
> він у вагоні, вона у вагоні, сестра у Львові 
> її і його, Одеса і Ялта, лисиця і їжак
> і після й, ї, а також 
> після я, ю, є, що позна-
> чають два звуки
> синій і зелений,
> Марія і Денис
> на початку речення пе-
> ред приголосним
> У лісі волого. Іде дощ. після паузи (після роз-
> ділового знака) перед 
> приголосним 
> У полі, у лісі волого: іде дощ. Правила чергування стосуються не лише прий­менників у–в і сполуч-
> ників і–й, а й початкових букв: телефон у кишені, він узяв; брат і се-
> стра, він іде.

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 123
> **Score:** 0.50
>
> 120
> Чергування [у] – [в]
> Уживаємо У:
> Уживаємо В:
> між приголосними: 
> вечір у місті; наш учитель
> між голосними: 
> живе в Івано-Франківську
> на початку речення перед 
> двома чи трьома приголос­
> ними: У складних обстави-
> нах.
> на початку речення перед 
> голосним: 
> В Одесі тепло.
> перед в, ф, зв, св, дв, тв, 
> хв, гв, льв і под.: зайшла у 
> фоє; живе у Львові
> після голосного перед при-
> голосним (крім в, ф, зв, св, 
> дв, тв, хв, гв, льв і под.): 
> пішла в садок; наші вчи­
> телі 
> *** 
> також після голосного перед 
> в уживаємо префікс в-: 
> гості ввійшли; Оля вважає
> після паузи (на письмі по-
> значаємо розділовим зна-
> ком) перед приголосним:
> Знаю, у чому секрет.

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 174
> **Score:** 0.33
>
> 174
> Фонетика. Графіка. Орфоепія. Орфографія. Милозвучність української мови
> Милозвучність української мови. 
> Правила милозвучності 
> (чергування у — в, і — й, з — із — зі)
> Вправа 287
> 1. Прочитайте вітальну листівку .
> 2. Поміркуйте й  висловте свої думки: що варто виправити в  тексті? 
> Чому?
> Шановні українки і українці!
> ВІТАЄМО ВАС З СВЯТОМ!
> Бажаємо щастя, здоров’я й єдності!
> Нехай в ваших родинах панує злагода!
> В українській мові існують спеціальні засоби, за допомогою яких 
> мовлення можна зробити милозвучним, тобто уникнути нагрома-
> дження складних для вимови звуків .
> До таких засобів належать звукові варіанти прийменників у — в, 
> і — й, з — із — зі, сполучників і — й, а також варіанти коренів слів .

## І чи Й? З, із, чи зі?

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 197
> **Score:** 0.50
>
> – І Кузьма-листоноша, 
> винувато похиливши голову, простягнув газету. Павло Максимович подивився на газету, потім на поштаря, потім на 
> дружину, потім на сина, потім на Семена Семеновича, який, стоячи на ґан-
> ку, уважно слухав, – і раптом... зареготав. Та так оглушливо, що Бровко 
> аж присів і прищулив вуха. – Га-га-га-га! Га-га-га-га-га!.. А ми тут мало не той... не... Га-га-га-га-га! На хвилину завмерши, зареготала й Ганна Трохимівна, а за нею і Семен 
> Семенович, і Марія Омелянівна, не кажучи вже про наших хлопців, які аж 
> вищали від реготу. Години через дві надвечірні Бамбури знову сповнилися дзвінким співом. Хлопці дивилися на своїх батьків з ніжністю. Ох, ці дорослі! Які вони все-
> таки складні люди...

## Підсумок — Summary

> **Source:** golub, Grade 6
> **Section:** Сторінка 243
> **Score:** 0.33
>
> 243
> 592   Згрупуйте приклади, розташувавши їх у такому порядку: 1)  між-
> особистісне спілкування; 2)  групове спілкування; 3)  масове 
> спілкування. Вибір обґрунтуйте.
> Я вдома з братом; кандидат у депутати на зібранні з вибор-
> цями; тренер і спортсмени на тренуванні; оратор на урочис-
> тому зібранні; моя сестра в кав’ярні з подругою; пасажири 
> в транспорті і водій; бабуся і лікар у реєстратурі поліклініки; 
> мама в чаті з мешканцями нашого будинку; конферансьє 
> на концерті; екскурсовод і група туристів; дідусь з онуками.
> Особливості спілкування залежать також від кількості 
> учасників. З огляду на те, з ким людина спілкується, 
> вона обирає тему, добирає слова, інтонацію, тембр, 
> жести й міміку.

## Grammar Reference

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 127
> **Score:** 0.33
>
> 124
> 30. УЖИВАННЯ ПРИЙМЕННИКА З  
> ТА ЙОГО ВАРІАНТІВ ІЗ, ЗІ (ЗО)
> Про те, як під час уживання прийменника з  
> уникнути важкого для вимови збігу приголосних 
> ПРИГАДАЙМО. Які є шиплячі приголосні? 
> 303.	А.  Прочитайте виразно вголос словосполучення під ілюстрація-
> ми, звертаючи увагу на виділені прийменники. 
> гуляти З таксою
> гуляти ІЗ чау-чау
> гуляти ЗІ спанієлем
> Б.  Вимовте друге та третє словосполучення, уживаючи замість при-
> йменників із та зі прийменник з. Чи ускладнило це вимову? Чи зашко-
> дило милозвучності? 
> В.  Зробіть висновок про те, з якою метою замість прийменника з ужи-
> ваємо його варіанти із, зі.
> Збіг прийменника з із деякими іншими приголос­ними 
> може ускладнювати вимову. Наприклад, важко вимовляти 
> прийшов з школи.

> **Source:** avramenko, Grade 5
> **Section:** Сторінка 119
> **Score:** 0.25
>
> 119
> 5. Перепишіть слова, вибираючи з дужок потрібний прийменник або 
> префікс. 
> Довідався (з, зі) словника, проспівала (з, із) радістю, батько (і, із) си-
> ном, мати (з, із) донькою, повернувся (з, зі) Львова, узяла (з, із) сумки, 
> воскрес (з, із) попелу, прибіг (зі, із) складу; (з, зі)щулитися, (з, зі)псувати, 
> (з, зі)клеїти, (з, зі)грітися, (з, зі)стрибнути, (з, зі)тліти, (з, зі)в’янути, 
> (з, зі)рвати.


## МійКлас Theory (miyklas.com.ua)

*Ukrainian school curriculum theory — use this terminology and teaching approach.*

### Голосні й приголосні звуки
> **Source:** МійКлас — [Голосні й приголосні звуки](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/fonetika-grafika-orfoepiia-orfografiia-14565/golosni-i-prigolosni-zvuki-40864)

### Теорія:

*www.ua.pistacja.tv*  
Що означають терміни «фонетика», «графіка», «орфоепія», «орфографія»
Фонетика \(від. грец. phonetikos — звуковий\) — це розділ мовознавства, що вивчає звуки  мови.
 
Графіка \(від грец. grapho — пишу\) — це розділ мовознавства, що вивчає cукупність умовних знаків \(букв та символів\) для передачі звуків на письмі.
 
Орфоепія \(від грец. orthos — правильний,  epos — мова, мовлення\) — це розділ мовознавства, що вивчає правила літературної вимови.

Орфографія \(від грец. orthos — правильний, grapho — пишу\) — це розділ мовознавства, що вивчає правила написання слів.
Голосні та приголосні звуки
Звук — найменша одиниця мови та мовлення.

### Співвідношення звуків і букв
> **Source:** МійКлас — [Співвідношення звуків і букв](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/fonetika-grafika-orfoepiia-orfografiia-14565/spivvidnoshennia-zvukiv-i-bukv-41281)

### Теорія:

*www.ua.pistacja.tv*  
 
Як ти вже знаєш, в українській мові є  38  **звуків** і 33  **літери** для передачі цих звуків на письмі.
Чому така різниця між кількістю звуків і букв?
Деякі букви \(я, ю, є\) позначають **два** звуки у певних позиціях.

Букви ї, щ завжди позначають **два** звуки.
 
Буквосполучення дж, дз інколи позначають **два** звуки, а інколи — **один**.
 
В українській мові розрізняють тверді приголосні звуки \(22\) й м'які приголосні \(10\), голосні звуки \(6\).

### Основні випадки чергування у–в, і–й, з–із–зі. Правила милозвучності
> **Source:** МійКлас — [Основні випадки чергування у–в, і–й, з–із–зі. Правила милозвучності](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/fonetika-grafika-orfoepiia-orfografiia-14565/osnovni-vipadki-cherguvannia-u-v-i-i-z-iz-zi-pravila-milozvuchnosti-41612)

### Теорія:

*www.ua.pistacja.tv*  
Правила милозвучності української мови
Українську мову недарма називають солов'їною й співучою.  Звуки в ній  завжди  поєднуються

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## У чи В? (У or В?)` (~300 words)
- `## І чи Й? З, із, чи зі?` (~300 words)
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
  1. **Proofreading a friend's Ukrainian essay about their город (garden) — spotting у/в and і/й errors. Text mentions: у городі/в городі, і яблука/й яблука, у школі/в школі. Read sentences aloud to hear the difference.**
     Speakers: Студент (writing), Друг (correcting)
     Why: У/в, і/й alternation with город(m), школа(f), яблуко(n)

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

**Required:** у/в (in/at — alternating preposition), і/й (and — alternating conjunction), з/із/зі (with/from — alternating preposition)
**Recommended:** Київ (Kyiv), Львів (Lviv), офіс (office, m), парк (park, m), театр (theater, m)

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

- P1 (~40 words): Scene-setting intro — two friends, Дарина and Олексій, are proofreading Олексій's Ukrainian essay about his город (garden). Establish that Дарина is pointing out euphony errors as they read sentences aloud together.
- Dialogue 1 (~110 words): 6-turn exchange — Олексій reads aloud "Я живу в Льові" and "Тарас живе у Києві." Дарина catches the first (should be у Львові — consonant before Л+В cluster), confirms the second is correct. They swap roles: Дарина reads "Вона працює у офісі" (wrong — vowel environment → в офісі). Олексій corrects. Close with: "Слухай, коли вимовляєш — відчуваєш різницю!" Speakers: Олексій / Дарина.
- Dialogue 2 (~110 words): 6-turn exchange — continuing the essay, Дарина finds "Ти й Олена будете в саду" (correct) and "мама й тато" (correct), then Олексій wrote "вона й він йдуть у парк" — Дарина confirms. Then finds error: "Максим й Семен" (wrong after consonant М → "Максим і Семен"). Final line: "Тепер твій есей звучить по-справжньому гарно!" Speakers: Дарина / Олексій.
- P2 (~70 words): Brief meta-commentary paragraph — explain that both dialogues show the same logic: Ukrainian chooses between sound variants to avoid awkward consonant or vowel clusters. Name the three pairs introduced: у/в, і/й, з/із/зі. Tell learners: "In the next sections you'll see exactly when each form is used."

---

## У чи В? (У or В?) (~330 words total)

- P1 (~80 words): Introduce the core principle — у/в alternation exists to avoid hard-to-pronounce consonant clusters. State the two main rules with named examples: (1) Use **в** after a vowel before a consonant → "живу **в** Києві", "вона **в** парку"; (2) Use **у** after a consonant before a consonant → "Тарас **у** Львові", "Максим **у** банку". Present as a simple listen-and-feel test, not a memorization table.
- P2 (~80 words): Sentence-start and post-pause rule — at the beginning of a sentence always use **У**: "**У** мене є квітка." "**У** саду тихо." Same after a comma or pause: "Знаю, **у** чому секрет." Give counterexample for starting before a vowel: "**В** Одесі тепло." Explain: before a vowel, **в** wins regardless of sentence position (В Одесі, в Ірпені). Two concrete mini-pairs for each sub-rule.
- P3 (~70 words): Special cluster list — before в, ф, кв, тв, льв, хв and similar double-consonant openings, always use **у**: "**у** Львові" (not в Львові — triple consonant л+в+в is brutal), "**у** фоє", "**у** вагоні". Explain in one sentence why: the two в-sounds would crash together. Give learners a shorthand: "If the next word already starts with в or ф — use у."
- Exercise: **quiz** — "У or В? Choose the correct form." 10 sentence items drawn from the dialogues and plan vocabulary: ___ Києві, живу ___ Одесі, Тарас ___ Львові, вона ___ вагоні, ___ мене є..., знаю ___ чому, ___ Харкові, він ___ фоє, ми ___ банку, ___ парку тихо. (~70 words framing + answer rationale lines)

---

## І чи Й? З, із, чи зі? (~330 words total)

- P1 (~80 words): Introduce і/й rule — two forms of the conjunction "and." Rule: use **й** between vowels (avoids a vowel+vowel hiatus): "мама **й** тато", "вона **й** він", "ти **й** Олена." Use **і** between consonants: "брат **і** сестра", "Тарас **і** Максим", "Максим **і** Семен." At the start of a sentence always **і**: "**І** він прийшов." Give three minimal pairs side by side so learners can hear the contrast.
- P2 (~80 words): Introduce з/із/зі — three forms of the preposition "with / from." State the three contexts with named examples: **з** before most words (vowels or easy consonants) → "**з** Одеси", "**з** другом", "**з** парку"; **із** between two consonant sounds to break the cluster → "Максим **із** Семеном", "повернувся **із** Львова"; **зі** before з, с, ш, щ or especially heavy clusters → "**зі** мною", "**зі** святом", "**зі** школи", "**зі** Стефанією." Mnemonic: зі sounds like a cushion — softens the hardest clusters.
- P3 (~50 words): Brief note on scope — з/із/зі is a smaller rule than у/в in everyday speech, but comes up constantly in greetings ("зі святом!"), introductions ("я з Одеси"), and conversation about people ("вона з братом"). Reassure learner: з is the default; you only shift to із or зі when you feel the consonant crash.
- Exercise A: **quiz** — "І or Й? Choose the correct conjunction." 8 items: мама ___ тато, брат ___ сестра, ти ___ Олена, Максим ___ Семен, вона ___ він, Тарас ___ Марія, і ___ він прийшов (sentence start), Київ ___ Одеса. (~50 words framing)
- Exercise B: **fill-in** — "___, із, or зі? Complete the sentence." 6 items: ___ другом, ___ святом, ___ Одеси, Максим ___ Семеном, ___ школи, ___ мною. (~40 words framing)

---

## Підсумок — Summary (~330 words total)

- P1 (~80 words): Recap paragraph — Ukrainian euphony is not an arbitrary rule but a feature of the language's beauty: avoid consonant pileups, avoid vowel hiccups, let speech flow. Name all three pairs again with their core trigger: **у/в** → look at surrounding sounds (consonant vs. vowel); **і/й** → look at sounds before and after the conjunction; **з/із/зі** → look at what follows (vowel, consonant, heavy cluster).
- Self-check block (~120 words): Bulleted Q&A pairs as specified in the plan:
  - Я живу (в / у) Києві. → **в** Києві (after vowel у, before consonant К)
  - Я живу (в / у) Львові. → **у** Львові (before Л+В cluster)
  - (В / У) мене є квіти. → **У** мене (sentence start before consonant М)
  - Мама (і / й) тато. → мама **й** тато (between vowels А...А)
  - Брат (і / й) сестра. → брат **і** сестра (after consonant Т before С)
  - Повернувся (з / із) Семеном. → **із** Семеном (consonant Н before С)
  - (Зі / З) святом! → **Зі** святом (before сш-cluster)
- P2 (~80 words): Practice tip — read your Ukrainian sentences aloud. Native speakers use euphony instinctively, not by consulting tables. The goal is smooth, flowing Ukrainian, not rigid rule application. If a sentence feels like a tongue-twister, swap the variant. Close with encouragement: these alternations are one of the things that make Ukrainian sound like what it is — the солов'їна мова, the nightingale language. Next module: У чому? Де? (Where Is It?) applies these same prepositions in locative context.
- Exercise: **quiz** — "Which sentence sounds more natural?" 6 minimal pairs where one form is euphonically wrong: (1) "Тарас в Львові" vs "Тарас у Львові"; (2) "мама й тато" vs "мама і тато"; (3) "з мною" vs "зі мною"; (4) "В Одесі тепло" vs "У Одесі тепло"; (5) "брат й сестра" vs "брат і сестра"; (6) "із другом" vs "зі другом." (~50 words framing + answer rationale)

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
