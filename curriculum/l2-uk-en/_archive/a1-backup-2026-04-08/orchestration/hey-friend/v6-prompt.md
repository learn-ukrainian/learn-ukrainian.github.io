

---

## Your Writing Identity

**You are: Patient & Supportive Ukrainian Tutor.** Your persona is *The Helpful Teacher*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **42: Hey, Friend!** (A1, A1.7 [Communication]).

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
module: a1-042
level: A1
sequence: 42
slug: hey-friend
version: '1.2'
title: Hey, Friend!
subtitle: Олено! Тарасе! Друже! Мамо! — calling people by name
focus: grammar
pedagogy: PPP
phase: A1.7 [Communication]
word_target: 1200
objectives:
- Form vocative case for common names and family words (Олено! Тарасе! Мамо!)
- Use vocative in greetings and direct address (Привіт, Андрію!)
- Recognize vocative endings for masculine (-е, -у/-ю) and feminine (-о, -ю, -є) nouns
- Address people naturally using vocative in everyday situations
dialogue_situations:
- setting: 'At a busy birthday party — calling people across the room by name: Олено!
    Тарасе! Друже! Мамо! Бабусю! Дідусю! Each person is doing something different
    (dancing, eating, talking).'
  speakers:
  - Іменинник (birthday person)
  - Друзі
  motivation: 'Vocative: Олена→Олено, Тарас→Тарасе, мама→мамо, бабуся→бабусю'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Meeting a friend: — Олено, привіт! Як справи? — Добре, дякую, Тарасе!
    А в тебе? — Теж добре. Олено, ти знаєш мого брата? — Ні. — Андрію, ходи сюди!
    Це Олена. Олено, це Андрій. Vocative forms: Олено (Олена), Тарасе (Тарас), Андрію
    (Андрій).'
  - 'Dialogue 2 — At home: — Мамо, де мій телефон? — На столі, синку. — Тату, а де
    ключі? — У кишені, дочко. — Бабусю, ми йдемо! — Добре, будьте обережні! Family
    vocatives: мамо, тату, синку, дочко, бабусю.'
- section: Кличний відмінок (The Vocative Case)
  words: 300
  points:
  - 'Ukrainian has a special case for calling someone — кличний відмінок. In English
    you just say the name: ''Olena, come here!'' In Ukrainian the name CHANGES: Олена
    → Олено, ходи сюди! This is not optional — Ukrainians always use vocative when
    addressing someone. Grade 4 helper word: Кл. (!) — the exclamation mark reminds
    you: you''re calling someone, so the ending changes.'
  - 'Why vocative matters: Олена прийшла. (Olena came.) — nominative, talking ABOUT
    her. Олено, ходи сюди! (Olena, come here!) — vocative, talking TO her. Using nominative
    to address someone sounds unnatural in Ukrainian. It''s like saying ''Hey, him!''
    instead of ''Hey, you!'' in English.'
- section: Закінчення кличного (Vocative Endings)
  words: 300
  points:
  - 'Feminine names and nouns (-а → -о): Олена → Олено, мама → мамо, сестра → сестро,
    Оксана → Оксано, подруга → подруго, бабуся → бабусю (-ся → -сю). Names on -ка:
    Наталка → Наталко, Ірка → Ірко. Names on -ія: Марія → Маріє (not Маріо!). Names
    on -а (long): Катерина → Катерино, Тетяна → Тетяно.'
  - 'Masculine names and nouns: Hard consonant → -е: Тарас → Тарасе, Іван → Іване,
    брат → брате, пан → пане. Soft consonant / -й → -ю: Андрій → Андрію, дідусь →
    дідусю, вчитель → вчителю. Special: друг → друже (г → ж), козак → козаче (к →
    ч). Тато → тату (exceptional -у ending, memorize).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Vocative quick reference: | Pattern | Nominative → Vocative | Example | | Feminine
    -а | -а → -о | Олена → Олено, мама → мамо | | Feminine -ія | -ія → -іє | Марія
    → Маріє | | Feminine -ся | -ся → -сю | бабуся → бабусю | | Masculine hard | +
    -е | Тарас → Тарасе, брат → брате | | Masculine -й/soft | + -ю | Андрій → Андрію,
    вчитель → вчителю | | Special (г, к) | г→ж, к→ч + -е | друг → друже | Self-check:
    How do you call your family? мама → ? тато → ? брат → ?'
vocabulary_hints:
  required:
  - друг (friend, m)
  - подруга (friend, f)
  - брат (brother, m)
  - сестра (sister, f)
  - пан (Mr., m)
  - пані (Mrs./Ms., f)
  recommended:
  - синку (son — vocative, from син)
  - дочко (daughter — vocative, from дочка)
  - козак (Cossack, m)
  - вчитель (teacher, m)
  - бабуся (grandmother, f)
  - дідусь (grandfather, m)
activity_hints:
- type: fill-in
  focus: 'Write vocative: Олена → Олено, Тарас → Тарасе, мама → мамо'
  items:
  - Олена → {Олено}
  - Тарас → {Тарасе}
  - мама → {мамо}
  - Іван → {Іване}
  - сестра → {сестро}
  - Андрій → {Андрію}
  - подруга → {подруго}
  - брат → {брате}
  - Марія → {Маріє}
  - бабуся → {бабусю}
- type: quiz
  focus: 'Choose correct vocative: (Олена / Олено / Оленю), привіт!'
  items:
  - question: ___, привіт!
    options:
    - Олено
    - Олена
    - Оленю
  - question: Як справи, ___?
    options:
    - Тарасе
    - Тарас
    - Тарасу
  - question: Дякую, ___!
    options:
    - мамо
    - мама
    - маме
  - question: Ходи сюди, ___!
    options:
    - Іване
    - Іван
    - Івану
  - question: Будь обережний, ___!
    options:
    - синку
    - синок
    - синке
  - question: Що ти робиш, ___?
    options:
    - брате
    - брат
    - брату
  - question: Добрий день, ___!
    options:
    - пане
    - пан
    - пану
  - question: Привіт, ___!
    options:
    - Андрію
    - Андрій
    - Андріє
- type: group-sort
  focus: 'Sort vocative endings: -о (feminine) vs -е (masculine hard) vs -ю (masculine
    soft)'
  groups:
  - name: -о (feminine)
    items:
    - Олено
    - мамо
    - сестро
  - name: -е (masculine hard)
    items:
    - Тарасе
    - Іване
    - брате
    - пане
  - name: -ю (masculine soft)
    items:
    - Андрію
    - дідусю
    - вчителю
- type: fill-in
  focus: 'Complete dialogue: ___, привіт! Як справи? (name → vocative)'
  items:
  - — {Олено|Олена}, привіт! Як справи?
  - — Добре, дякую, {Тарасе|Тарас}!
  - — {Мамо|Мама}, де мій телефон?
  - — На столі, {синку|синок}.
  - — {Бабусю|Бабуся}, ми йдемо!
  - — Добре, до побачення, {Андрію|Андрій}!
connects_to:
- a1-043 (Please Do This)
prerequisites:
- a1-041 (Checkpoint — Food and Shopping)
grammar:
- 'Vocative case (кличний відмінок): special endings for direct address'
- Feminine -а → -о (Олена → Олено), -ія → -іє (Марія → Маріє)
- Masculine hard → -е (Тарас → Тарасе), soft/-й → -ю (Андрій → Андрію)
- 'Consonant alternation: друг → друже (г → ж)'
register: розмовний
references:
- title: State Standard 2024, §4.2.3.4
  notes: 'Vocative case — address forms. A1 scope: common patterns only.'
- title: 'Grade 4 textbook: Кличний відмінок (Заболотний)'
  notes: Helper word Кл. (!). Feminine -а→-о, masculine hard→-е, soft→-ю.

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

- **Confirmed (12/12):** друг, подруга, брат, сестра, пан, пані, синку, дочко, козак, вчитель, бабуся, дідусь

⚠️ **One plan metadata error found:**
- **синку** — VESUM lemma is **синок** (noun), NOT **син**. The plan says "синку (son — vocative, from **син**)" — this is incorrect. The vocative of **син** is **сину**. **синку** is the vocative of **синок** (affectionate diminutive). Plan annotation must be corrected to: "синку (son — vocative, from синок)".

- Not found: none

---

## Textbook Excerpts

### Section: Діалоги (Dialogues) — грeetings, vocative in natural context
> «Доброго ранку! Добрий день! Привіт! Радий бачити тебе.» / «Як ся маєш? Як ваші справи?»
> Source: Заболотний, Grade 5 (2023); Авраменко, Grade 6 (2023)

> Авраменко Grade 6 explicitly models dialogue-in-situations: «знайомство з однолітками в таборі відпочинку», with formulas: **Привіт! Вітаю! Доброго ранку!** and **Як ся маєш? Як ваші справи?** — both confirmed as natural Ukrainian etiquette formulas.
> Source: Авраменко, Grade 6, tier 1

### Section: Кличний відмінок (The Vocative Case)
> «Іменники в українській мові мають сім відмінків, на відміну від інших слов'янських мов. Сьомий відмінок — кличний, його використовують, звертаючись до людей, рідше — до тварин.»
> Source: Авраменко, Grade 9, tier 2

> «Кличний відмінок іменника є засобом вираження звертання до певної особи чи предмета. Форму кличного відмінка мають усі іменники I, II, III відмін у формі однини.»
> Source: Глазова, Grade 10, tier 2

### Section: Закінчення кличного (Vocative Endings)
> **Feminine (I declension, hard group):** «Закінчення **-о**: мамо, Миколо, старосто.» | **Soft/mixed group:** «Закінчення **-е (-є)**: судде, земле, **Маріє**; закінчення **-ю** для пестливих імен: бабусю, Настусю, Катрусю. Але: Насте, Катре.»
> Source: Литвинова, Grade 6 (2023), tier 1

> **Masculine (II declension, hard group):** «Закінчення **-е** для безсуфіксних іменників: Петре, студенте, **пане**, **друже**. Але: **тату**, сину, діду.» | **Soft group:** «Закінчення **-ю** для більшості іменників: лікарю, **вчителю**, добродію, Ігорю.» | **Suffix -к/-ик/-ок:** «Закінчення **-у**: **синку**, батьку.»
> Source: Литвинова, Grade 6 (2023), tier 1

> **Consonant alternations in vocative (confirmed):**
> «[г] — [ж]: **друг — друже**, ворог — вороже; [к] — [ч]: чоловік — чоловіче, **козак — козаче**; [х] — [ш]: пастух — пастуше.»
> Source: Глазова, Grade 10 (2018), tier 2; also Заболотний, Grade 5 (2023) tier 1

> **мамо, дочко** (pестливі without diminutive suffix keep -о not -ю) vs **матусю, доню** (diminutive suffix → -ю)
> Source: Заболотний, Grade 10 (2018), §45

### Section: Підсумок — Summary
> «Пане Євгене; пані Оксано; панно Ганно; Тамаро Іванівно; Іване Вікторовичу.» — official address forms in vocative from Grade 8 context table.
> Source: Заболотний, Grade 8 (2025), tier 1

---

## Grammar Rules

- **Vocative endings — consonant alternations:** Правопис §18 — «к, м'який ц, ч → -цьк-/-цтв-; г, ж, з → -зьк-» (same phonological alternations г→ж, к→ч confirmed here). The vocative-specific declension tables are confirmed via textbooks (Авраменко Gr.9, Литвинова Gr.6, Глазова Gr.10) rather than a single Правопис paragraph.
  - **Rule confirmed:** г→ж before -е (друг→друже); к→ч before -е (козак→козаче); ц'→ч before -е (хлопець→хлопче); х→ш before -е (пастух→пастуше).
  - **Exception confirmed:** Foreign names and nouns with suffixes -ик/-к do NOT alternate: Джеку, Жаку, **синку** (suffix -к → ending -у, no alternation).

- **тато→тату:** Confirmed as exceptional -у ending alongside сину, діду — explicitly listed in Литвинова Grade 6 §31 table (hard group exceptions).

- **Марія→Маріє (not Маріо):** Confirmed — «Закінчення -є, якщо кінцевий приголосний основи м'який: Марія [йа] — Маріє» (Авраменко Grade 9).

---

## Calque Warnings

- **«як справи»** — Антоненко-Давидович discusses "справа" vs "діло" semantics but does **NOT** flag «як справи?» as a calque. The greeting formula is natural Ukrainian. ✅ OK
- **«будьте обережні»** — No calque found. Natural Ukrainian imperative + predicate adjective. ✅ OK
- **«ходи сюди»** — No calque found. Standard Ukrainian imperative movement expression. ✅ OK

---

## CEFR Check

- **друг:** A1 — ✅ on target
- **брат:** A1 — ✅ on target
- **сестра:** A1 — ✅ on target
- **подруга:** A1 — ✅ on target
- **вчитель:** A1 — ✅ on target
- **бабуся:** A2 — ⚠️ one level above A1. Acceptable as a culturally central family term introduced early; flag for awareness. Writers should treat it as lexical exception, not grammar teaching vocab.
- **козак:** B1 — ⚠️ **above A1 target**. Used in the plan only as a grammar example to demonstrate the к→ч alternation (козак→козаче). Pedagogically justified as a **cultural anchor word** for the alternation rule, but should NOT appear in core vocabulary list or be tested in activities. Keep as illustrative example only, explicitly labelled as cultural bonus vocabulary.
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
# Verified Knowledge Packet: Hey, Friend!
**Module:** hey-friend | **Phase:** A1.7 [Communication]
**Textbook grades searched:** 5, 6, 7

---

## Діалоги (Dialogues)

> **Source:** avramenko, Grade 7
> **Section:** Сторінка 122
> **Score:** 0.33
>
> Твій друг Артем 
> — Привіт, Артеме! Лікарі готують мене до операції. Я думаю, що вона 
> пройде успішно, адже коли думки з добром, то й добро з людиною. Згадую 
> Психологічна  повість  Оксани  Радушинської  «Метелики  в  крижаних  панцирах»

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 221
> **Score:** 0.50
>
> 218
> Доброго ранку! Добрий день! Привіт! Радий бачити тебе. 
> * * *
> До побачення! На все добре! Гарного дня! Бувайте здорові! До зу-
> стрічі!
> Бажаю успіхів! Хай щастить! Рада була зустрітися.
> * * *
> Вибачте. Пробачте. Прошу вибачити (пробачити).
> Даруйте. Перепрошую. Вибачте, що турбую.
> * * *
> Дякую. Щиро дякую. Я тобі дуже вдячний. Будь ласка. Нема 
> за що.
> 528.	І. ПОПРАЦЮЙТЕ В ПАРАХ. Уявіть, що хтось із вас опинився в 
> чужому місті і йому необхідно з’ясувати, де розміщено стадіон (цирк чи 
> театр). А хтось із вас живе в цьому місті. Складіть і розіграйте за осо-
> бами діалог (5–6 реплік), можливий у цій ситуації. Уживайте слова 
> ввічливості.
> ІІ.

> **Source:** zabolotnyi, Grade 7
> **Section:** Сторінка 250
> **Score:** 0.50
>
> 246
> 246
> – Якщо хтось не виконує твоїх забаганок, це ще не означає,
> що йому не можна довіряти! – розвів руками дідусь. – І ти по-
> винен знати, що не кожне бажання можна виконати.
> * * *
> – Добридень! – привіталася Наталка з дідусем. – Яка ж гар-
> на у вас крамничка!
> – Добридень! Радий, що тобі подобається! Щось тобі запропо-
> нувати?
> – Знаєте, я шукаю подарунок для подруги. Щось не дуже 
> дороге, але таке, що запам’ятається.
> – А яка твоя подруга?
> – Дуже хороша людина. Добра, спокійна, завжди допоможе,
> коли що.
> За А. Шевердіною
> ІІ. Знайдіть у першому діалозі дієслова, які передають гарячковість головного ге-
> роя, його категоричність, нетерпимість. Чи легко, на вашу думку, знаходити спіль-
> ну мову з такими людьми? 
> 
> 
> 
> 
> 
> 
> 
> І. Розгляньте світлини.

## Кличний відмінок (The Vocative Case)

> **Source:** litvinova, Grade 6
> **Section:** Сторінка 141
> **Score:** 0.50
>
> § 28. Кличний відмінок  
> 141
> Добродійко, 
> добродійка; 
> добродій, 
> добродію; 
> пан 
> Євген, пане Євгене; пані Оксано, пані Оксана; панно 
> Ганно, панна Ганна; шановна громада, шановна гро-
> мадо; Тамара Іванівна, Тамаро Іванівно; Іване Вікторо-
> вичу, Іван Вікторович.
> 2. Яку форму ви оберете, звертаючись до особи?
> 3. Випишіть форми звертань.

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 178
> **Score:** 0.25
>
> Аля і Недопопелюшка 
> подавали майстру інструменти. Недоладько дуже зрадів, коли побачив, що дівчатка живі та здорові. – А ми прийшли визволяти тебе, – звернувся він до Алі. Аля обернулася і впізнала багатьох знайомих недоладян. Потім знову 
> перевела погляд на Недоладька й раптом щось згадала. Дівчинка побігла 
> на кухню, знайшла в каміні кілька холодних вуглинок, міцно затисла їх у 
> кулаці. Тремтячою рукою дівчинка торкнулася Недоладькового підборід-
> дя... І сталося диво! Перед Алею стояв стрункий, гарний хлопець. Його 
> неважко було пізнати, бо на обличчі світилися щирі очі та добра й лагідна 
> усмішка. Аля вся сяяла від задоволення. Хтось торкнувся її руки, і дівчин-

## Закінчення кличного (Vocative Endings)

> **Source:** litvinova, Grade 6
> **Section:** Сторінка 151
> **Score:** 0.33
>
> § 30. Відмінювання іменників І відміни   
> 151
> 2. Поясніть відмінності в закінченнях іменників.
> 3. Поміркуйте, у яких лексичних відношеннях перебувають слова в кож-
> ній групі (до крапки з комою).
> Іменники І  відміни в  кличному відмінку мають такі 
> закінчення:
> Тверда група
> М’яка та мішана групи
> Закінчення -о: мамо, Ми-
> коло, старосто.
> Запам’ятайте! Закінчення 
> -о в  кличному відмінку 
> мають усі жіночі імена по 
> батькові: Олексіївно, Сер-
> гіївно, Петрівно
> • Закінчення -е (-є): 
> судде, земле, Маріє, 
> круче, душе;
> • закінчення -ю для пе-
> стливих імен і  назв: 
> бабусю, Настусю, Ка-
> трусю.
> Але: Насте, Катре
> Вправа 305
> Поставте імена у  форму кличного відмінка. Запишіть їх.
> Панна Яна, пані суддя, голова зборів, колега Микола, 
> подруга Оксана, Інна Миколаївна, Стефанія Григорівна.
> Вправа 306
> 1.

## Підсумок — Summary

> **Source:** avramenko, Grade 7
> **Section:** Сторінка 119
> **Score:** 0.50
>
> — промовила 
> металевим голосом Олена Кожедуб. (...)
> — Ти не можеш мені заборонити — там будуть усі наші. — Можу, ще й як можу! Ти неповнолітній, тому я можу заборонити 
> все, що вважаю недоцільним. Я — твоя мати, і ти зобов’язаний слухатися 
> мене, бо допоки не подорослішаєш, рішення за тебе прийматиму тільки я!

> **Source:** litvinova, Grade 6
> **Section:** Сторінка 151
> **Score:** 0.33
>
> § 30. Відмінювання іменників І відміни   
> 151
> 2. Поясніть відмінності в закінченнях іменників.
> 3. Поміркуйте, у яких лексичних відношеннях перебувають слова в кож-
> ній групі (до крапки з комою).
> Іменники І  відміни в  кличному відмінку мають такі 
> закінчення:
> Тверда група
> М’яка та мішана групи
> Закінчення -о: мамо, Ми-
> коло, старосто.
> Запам’ятайте! Закінчення 
> -о в  кличному відмінку 
> мають усі жіночі імена по 
> батькові: Олексіївно, Сер-
> гіївно, Петрівно
> • Закінчення -е (-є): 
> судде, земле, Маріє, 
> круче, душе;
> • закінчення -ю для пе-
> стливих імен і  назв: 
> бабусю, Настусю, Ка-
> трусю.
> Але: Насте, Катре
> Вправа 305
> Поставте імена у  форму кличного відмінка. Запишіть їх.
> Панна Яна, пані суддя, голова зборів, колега Микола, 
> подруга Оксана, Інна Миколаївна, Стефанія Григорівна.
> Вправа 306
> 1.

> **Source:** zabolotnyi, Grade 6
> **Section:** Сторінка 243
> **Score:** 0.50
>
> Усе 
> збігалося!.. Хряснули вхідні двері – то прийшла мама. Вона дуже 
> повільно роздягалася в передпокої, зайшла на кухню й зне-
> можено сіла край стола.

## Grammar Reference

> **Source:** litvinova, Grade 6
> **Section:** Сторінка 141
> **Score:** 0.33
>
> § 28. Кличний відмінок  
> 141
> Добродійко, 
> добродійка; 
> добродій, 
> добродію; 
> пан 
> Євген, пане Євгене; пані Оксано, пані Оксана; панно 
> Ганно, панна Ганна; шановна громада, шановна гро-
> мадо; Тамара Іванівна, Тамаро Іванівно; Іване Вікторо-
> вичу, Іван Вікторович.
> 2. Яку форму ви оберете, звертаючись до особи?
> 3. Випишіть форми звертань.

> **Source:** zabolotnyi, Grade 6
> **Section:** Сторінка 120
> **Score:** 0.50
>
> 120
> Iменник
> Розгляньте зразки відмінювання чоловічого та жіночого імен по 
> батькові. Провідміняйте усно ім’я та по батькові: Антон Андрійович, Марія 
> Андріївна.
> Н.
> Р.
> Д.
> Зн.
> Ор.
> М.
> Кл.
> Іванович                 
> Івановича
> Івановичу, Івановичеві
> Івановича
> Івановичем
> на Івановичу, Івановичеві
> Івановичу
> Іванівна
> Іванівни
> Іванівні
> Іванівну
> Іванівною
> на Іванівні
> Іванівно
> У кличному відмінку чоловічі імена по батькові мають закінчен-
> ня у – Іванович
> у
> у, Андрійовичу.
>  
>  Поміркуйте. Дідуся звуть Григорій Васильович, його онука – Олександр 
> Дмитрович. Як звуть (ім’я та по батькові) батька онука?
> Прочитайте речення, утворюючи від поданих у дужках імен імена по 
> батькові.
> 1. Іван (Лука) був людиною м’якої, навіть ніжної вдачі
> (Г. Тютюнник). 2.


## МійКлас Theory (miyklas.com.ua)

*Ukrainian school curriculum theory — use this terminology and teaching approach.*

### Приголосні м'які й тверді, дзвінкі й глухі
> **Source:** МійКлас — [Приголосні м'які й тверді, дзвінкі й глухі](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/fonetika-grafika-orfoepiia-orfografiia-14565/prigolosni-m-iaki-i-tverdi-dzvinki-i-glukhi-vimova-prigolosnikh-g-i-g-40885)

### Теорія:

*www.ua.pistacja.tv*  
Приголосні звуки – це звуки, що творяться за допомогою голосу й шуму або лише шуму. При їх вимові струмінь видихуваного повітря натрапляє на різні перепони органів мовлення

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Кличний відмінок (The Vocative Case)` (~300 words)
- `## Закінчення кличного (Vocative Endings)` (~300 words)
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
  1. **At a busy birthday party — calling people across the room by name: Олено! Тарасе! Друже! Мамо! Бабусю! Дідусю! Each person is doing something different (dancing, eating, talking).**
     Speakers: Іменинник (birthday person), Друзі
     Why: Vocative: Олена→Олено, Тарас→Тарасе, мама→мамо, бабуся→бабусю

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

**Required:** друг (friend, m), подруга (friend, f), брат (brother, m), сестра (sister, f), пан (Mr., m), пані (Mrs./Ms., f)
**Recommended:** синку (son — vocative, from син), дочко (daughter — vocative, from дочка), козак (Cossack, m), вчитель (teacher, m), бабуся (grandmother, f), дідусь (grandfather, m)

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
## Діалоги (~330 words total)

- D1 (~120 words): Dialogue 1 — Meeting a friend at a party. Іменинник calls across the room: "Олено, привіт! Як справи?" Олена responds: "Добре, дякую, Тарасе! А в тебе?" He introduces his brother: "Андрію, ходи сюди! Це Олена. Олено, це Андрій." 6-8 turns, naturally paced. Vocative forms highlighted in bold: Олено (← Олена), Тарасе (← Тарас), Андрію (← Андрій).
- D2 (~120 words): Dialogue 2 — At home before going out. Teen calls parents: "Мамо, де мій телефон?" "На столі, синку." "Тату, а де ключі?" "У кишені, дочко." Grandmother at the door: "Бабусю, ми йдемо!" "Добре, будьте обережні!" 6-8 turns. Family vocatives highlighted: мамо, тату, синку, дочко, бабусю.
- P1 (~45 words): Brief setup sentence before each dialogue — Party context: Тарасу 18 років, усі друзі на вечірці, він кличе людей через кімнату. Home context: родина збирається, кожен зайнятий своїм. Sets the situation so learners read with purpose.
- P2 (~45 words): Post-dialogue note: "Notice how every name CHANGED. Олена became Олено. Тарас became Тарасе. This is кличний відмінок — the calling case. The next two sections explain the pattern."

## Кличний відмінок (~330 words total)

- P1 (~90 words): Introduction to the concept — Ukrainian has 7 cases, and one of them, кличний відмінок, exists specifically for direct address. In English you just use the name: "Olena, come here!" In Ukrainian the name's ending changes: Олена → Олено, ходи сюди! This is not poetic or old-fashioned — it is everyday, mandatory speech. Grade 4 grammar shorthand: Кл. (!) — the exclamation mark is the memory hook, you're calling someone.
- P2 (~80 words): The two-sentence contrast — Олена прийшла. (Olena arrived — nominative, talking ABOUT her, she is the subject.) vs. Олено, ходи сюди! (Olena, come here! — vocative, talking TO her, she is being addressed.) Using nominative for address in Ukrainian sounds unnatural — it is the equivalent of saying "Hey, him!" instead of "Hey, you!" Learners must understand this is not optional.
- P3 (~80 words): Cultural grounding — Vocative is alive and vibrant in Ukrainian today. In texts, songs, and conversation: "Слухай, Тарасе!", "Вибачте, пане!", "Дякую, мамо!" — these are phrases from real life. The vocative is also what distinguishes Ukrainian from languages that lost it. It gives every address a personal, direct warmth. This is one of the ways Ukrainian encodes human relationship into grammar.
- P4 (~80 words): Connection to the dialogues — Return to D1 and D2, now with grammar lens. Point out each vocative pair: Олена→Олено, Тарас→Тарасе, Андрій→Андрію, мама→мамо, тато→тату, бабуся→бабусю, синок→синку, дочка→дочко. Learners now see the dialogues are not random — each speaker naturally used the correct form without thinking. That automatic use is the goal.

## Закінчення кличного (~330 words total)

- P1 (~80 words): Feminine pattern — nouns and names ending in -а. Hard group: -а → -о. Examples: Олена → Олено, мама → мамо, сестра → сестро, Оксана → Оксано, подруга → подруго. Names ending in -ка: Наталка → Наталко, Ірка → Ірко. Names ending in -ина/-іна (long): Катерина → Катерино, Тетяна → Тетяно. Easy rule: if the name ends in -а and the stem is hard, drop the -а and add -о.
- P2 (~70 words): Feminine exceptions — soft and mixed groups. Names ending in -ія: NOT -іо, but -іє: Марія → Маріє, Софія → Софіє. Names with diminutive/affectionate suffix -уся/-юся: бабуся → бабусю, Настуся → Настусю. Note from Litvinova Grade 6: Насте, Катре also exist but бабусю, Настусю are the standard affectionate forms learners will use. Patronymics ending in -івна follow -о: Іванівна → Іванівно.
- P3 (~80 words): Masculine hard pattern — hard consonant stem → add -е. Examples: Тарас → Тарасе, Іван → Іване, брат → брате, пан → пане. Patronymics ending in -ович → -овичу (from Zabohotnyi Grade 6: Іванович → Івановичу). Full name address as modeled in Litvinova Grade 6: пан Євген → пане Євгене, Тамара Іванівна → Тамаро Іванівно, Іван Вікторович → Іване Вікторовичу.
- P4 (~60 words): Masculine soft pattern — soft consonant or -й ending → add -ю. Examples: Андрій → Андрію, дідусь → дідусю, вчитель → вчителю. Special case тато → тату: exceptional -у ending, must memorize. Consonant alternation for г and к: друг → друже (г → ж), козак → козаче (к → ч). Only two alternations, both follow Ukrainian phonetic softening rules.
- Exercise 1 (~40 words): Fill-in activity — Write the vocative form: Олена → ___, Тарас → ___, мама → ___, Іван → ___, сестра → ___, Андрій → ___, подруга → ___, брат → ___, Марія → ___, бабуся → ___. 10 items, covers all patterns from both paragraphs.

## Підсумок (~330 words total)

- P1 (~60 words): Recap sentence — Кличний відмінок is the Ukrainian case of direct address. Every time you speak TO someone — not about them — the name or noun changes its ending. There are four main patterns to know at A1 level, and most names fall neatly into one of them.
- Table (~120 words): Vocative quick-reference table — 6 rows:
  | Pattern | Nominative → Vocative | Приклади |
  | Feminine -а (hard) | -а → -о | Олена → Олено, мама → мамо, сестра → сестро |
  | Feminine -ія | -ія → -іє | Марія → Маріє, Софія → Софіє |
  | Feminine -уся | -уся → -усю | бабуся → бабусю |
  | Masculine hard | + -е | Тарас → Тарасе, брат → брате, пан → пане |
  | Masculine -й/soft | + -ю | Андрій → Андрію, вчитель → вчителю, тато → тату |
  | Special г/к | г→ж, к→ч + -е | друг → друже, козак → козаче |
- P2 (~50 words): Self-check — Can you call your family? Fill in: мама → ___, тато → ___, брат → ___, сестра → ___, бабуся → ___, дідусь → ___. And your own name or a friend's name — what does it become in vocative? (Answers: мамо, тату, брате, сестро, бабусю, дідусю.)
- Exercise 2 (~50 words): Quiz activity — Choose correct vocative in context (8 items matching activity_hints): "Олено/Олена/Оленю, привіт!", "Як справи, Тарасе/Тарас/Тарасу?", "Дякую, мамо/мама/маме!", "Ходи сюди, Іване/Іван/Івану!", "Будь обережний, синку/синок/синке!", "Що ти робиш, брате/брат/брату?", "Добрий день, пане/пан/пану!", "Привіт, Андрію/Андрій/Андріє!"
- Exercise 3 (~50 words): Group-sort activity — Sort 10 vocative forms by ending: -о (feminine): Олено, мамо, сестро | -е (masculine hard): Тарасе, Іване, брате, пане | -ю (masculine soft): Андрію, дідусю, вчителю. Reinforces the three dominant patterns at a glance.

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
