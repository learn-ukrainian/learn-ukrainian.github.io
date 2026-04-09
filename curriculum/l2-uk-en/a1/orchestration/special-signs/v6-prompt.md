

---

## Your Writing Identity

**You are: Lead Ukrainian Instructor.** Your persona is *The Patient Guide*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **3: Special Signs** (A1, A1.1 [Sounds, Letters, and First Contact]).

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

1. **IMMERSION TARGET: 5-15% Ukrainian MAXIMUM. THE LEARNER CANNOT READ CYRILLIC YET. English must dominate completely. Ukrainian appears ONLY as bolded inline words with immediate English translation.** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if immersion is outside this range. For A1 early modules, the learner cannot read Cyrillic — English must dominate. For A2+, Ukrainian must carry a significant share — add Ukrainian Reading Practice blocks, dialogues, and example paragraphs to reach the target. Too little Ukrainian fails audit just as much as too much.
2. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
3. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
4. **You are a warm, encouraging teacher.** Natural teacher phrasing ("Let us look at...", "Have you noticed...") is fine. What to AVOID: self-congratulatory openers ("Welcome to A2! Congratulations!"), gamified language ("You have unlocked...", "You now possess..."), and empty filler sentences that add words but zero information. Every sentence should teach something specific to Ukrainian.
5. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
6. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers where exercises should appear. A separate pipeline step generates the actual exercises from the plan's activity_hints.
7. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
8. **Hit the word target** — you MUST write 1200–1800 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
9. **NO archaic, obsolete, or rare words** — use only modern standard Ukrainian. Do not use words marked as archaic (застаріле) or dialectal in dictionaries. Example: use «кін» not «кон», use «пом'якшені» not «м'якшені». When in doubt, choose the common modern form. Your pre-training contains Russian-influenced archaic forms — verify unfamiliar words.
10. **EVERY module MUST end with `## Summary`** — this is the last H2 section before the file ends. It contains a self-check recap. If you forget this section, the audit REJECTS the module and you waste a retry. Write it LAST, after all other sections.

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
module: a1-003
level: A1
sequence: 3
slug: special-signs
version: '1.3'
title: Special Signs
subtitle: Ь, apostrophe, and the voice of consonants
focus: phonetics
pedagogy: PPP
phase: A1.1 [Sounds, Letters, and First Contact]
word_target: 1200
objectives:
- Understand what the soft sign (Ь) does to consonants
- Read words with apostrophe correctly (сім'я, м'ясо)
- Distinguish voiced and voiceless consonant pairs
- Pronounce the tricky Ukrainian sounds И, Г, Р
content_outline:
- section: М'який знак (The Soft Sign — Ь)
  words: 250
  points:
  - 'Ь has no sound. Its job: soften the consonant before it. Three-way distinction
    (Авраменко Grade 5 p.75, Большакова Grade 2 p.46): м''які приголосні (truly soft,
    9 pairs: Д/Д'', Т/Т'', З/З'', С/С'', Ц/Ц'', Л/Л'', Н/Н'', Р/Р'', ДЗ/ДЗ'' + Й),
    пом''якшені (partially softened: губні, шиплячі, задньоязикові — Ь never after
    these), тверді (hard). Захарійчук Grade 1 p.15 notation: hard = [–], soft = [=].'
  - 'Літвінова Grade 5 mnemonic: «ДЗіДЗьо, Де Ти З''їСи Ці ЛиНи» — exactly
    the 9 consonants Ь can soften. Common patterns: -нь (день, кінь, осінь),
    -ль (сіль, біль), -ть (мить), -зь (мазь). Practice: учитель, батько, маленький.'
- section: Апостроф (The Apostrophe)
  words: 250
  points:
  - 'Захарійчук Grade 1 p.97: Apostrophe comes after б, п, в, м, ф, р before я, ю,
    є, ї. It keeps the consonant HARD and gives the vowel its full [й] + vowel sound.'
  - 'Without apostrophe: consonant softens (пісня — Н is soft). With apostrophe: consonant
    stays hard + vowel = two sounds. сім''я [сім-йа] (family), м''ясо [м-йасо] (meat),
    п''ять [п-йать] (five), комп''ютер [комп-йутер] (computer). Reading practice:
    п''ять, дев''ять, м''який, м''яч, об''єкт. IMPORTANT: Only use apostrophe words
    where apostrophe follows the labial rule (б,п,в,м,ф,р + я,ю,є,ї). Do NOT include
    під''їзд or з''їзд — these follow the prefix rule (під-/з- + їзд) which is A2+.
    Also: тварь is a RUSSIAN form — do NOT use it. Ukrainian has тварина (animal).'
- section: Дзвінкі і глухі (Voiced and Voiceless)
  words: 250
  points:
  - 'Consonants come in voiced-voiceless pairs. Hand on throat test: vibration = voiced.
    Pairs: Б-П, Д-Т, Г-Х, Ґ-К, З-С, Ж-Ш, ДЗ-Ц, ДЖ-Ч.'
  - 'Ukrainian pronounces voiced consonants clearly at word end — дуб is [дуб], мороз is
    [мороз]. Voiced consonants переважно (mostly) keep their sound. Exception: легко
    [лехко]. This is a defining feature of Ukrainian phonetics.'
  - 'Minimal pairs for ear training: балка (beam) vs палка (stick), коза (goat) vs
    коса (braid).'
- section: Вимова українських звуків (Pronouncing Ukrainian Sounds)
  words: 250
  points:
  - 'И [и] — a unique Ukrainian vowel. It is NOT the same as І [і]. Minimal pairs to hear
    the difference: бик (bull) vs бік (side), дим (smoke) vs дім (house), лист (letter/leaf)
    vs ліс (forest), кит (whale) vs кіт (cat). Practice with Anna Ohoiko''s И video.'
  - 'Г [ɦ] vs Ґ [g] — two different letters, two different sounds. Г is a voiced
    fricative (air flows through narrowed throat): гарно, гора, голова. Its voiceless
    partner is Х — say Х then add voice to get Г. Ґ is a voiced stop (full throat
    closure then release): ґанок, ґудзик. Its voiceless partner is К. Ґ is uniquely
    Ukrainian — an important part of Ukrainian phonetic identity. DO NOT call Г "soft"
    — in Ukrainian phonetics "м''який" means palatalized, which Г is not.'
  - 'Р [р] — the Ukrainian rolled/trilled Р. Practice with Anna Ohoiko''s video: рука, робота,
    ранок, риба. An imperfect Р is always understood — focus on getting comfortable, not perfect.'
- section: Підсумок — Summary
  words: 200
  points:
  - 'Self-check: What does Ь do? After which letters does apostrophe appear? Name
    3 voiced-voiceless pairs. How is Ukrainian Г different from Ґ? Read these words:
    сім''я, день, п''ять, гарно.'
vocabulary_hints:
  required:
  - сім'я (family) — apostrophe word
  - день (day) — soft sign after Н
  - сіль (salt) — soft sign after Л
  - м'ясо (meat) — apostrophe after М
  - п'ять (five) — apostrophe after П
  - гарно (nicely, beautifully) — Г [ɦ] practice
  - риба (fish) — Р and И practice
  recommended:
  - батько (father, formal) — soft sign
  - учитель (teacher) — soft sign at end
  - дев'ять (nine) — apostrophe
  - комп'ютер (computer) — apostrophe in cognate
  - м'який (soft) — apostrophe only (NO soft sign! Й is inherently soft)
activity_hints:
- type: odd-one-out
  section: "М'який знак"
  focus: 'Which consonant does NOT have a soft pair? (Ь can''t soften it)'
  items: 6
- type: fill-in
  section: "Апостроф"
  focus: 'Add the missing Ь or apostrophe: сім_я, ден_, п_ять'
  items: 6
- type: error-correction
  section: "Апостроф"
  focus: 'Find missing apostrophes in words like м''ясо, сім''я, п''ять'
  items: 6
- type: group-sort
  section: "Апостроф"
  focus: 'Sort words into: has Ь / has apostrophe / neither'
  items: 18
- type: match-up
  section: "Дзвінкі і глухі"
  focus: 'Match voiced-voiceless pairs: Б↔П, Д↔Т, Г↔Х, Ґ↔К, etc.'
  items: 8
- type: true-false
  section: "Дзвінкі і глухі"
  focus: 'Statements about voiced/voiceless rules and non-devoicing'
  items: 6
- type: quiz
  section: "Вимова українських звуків"
  focus: 'Г vs Ґ: choose the correct letter for each word'
  items: 6
connects_to:
- a1-004 (Stress and Melody)
prerequisites:
- a1-002 (Reading Ukrainian)
grammar:
- 'Soft sign (Ь) — softens preceding consonant, no sound. Only after 9 consonants:
  Д, Т, З, С, Ц, Л, Н, Р, ДЗ (mnemonic: ДЗіДЗьо, Де Ти З''їСи Ці ЛиНи)'
- 'Three-way distinction: м''які (truly soft, 9+Й), пом''якшені (partially softened
  губні/шиплячі/задньоязикові), тверді (hard)'
- 'Apostrophe — after б,п,в,м,ф,р before я,ю,є,ї (Захарійчук rule). NO prefix
  apostrophe examples (під''їзд, з''їзд) at A1.'
- 'Voiced/voiceless pairs (8): Б-П, Д-Т, Г-Х, Ґ-К, З-С, Ж-Ш, ДЗ-Ц, ДЖ-Ч.
  Сонорні (В,Л,М,Н,Й,Р) are NEITHER voiced nor voiceless.'
- 'Non-devoicing: voiced consonants переважно keep sound at word end. Exception: легко [лехко].'
- 'Г [ɦ] voiced fricative (NOT "soft") vs Ґ [g] voiced stop'
register: розмовний
references:
- title: Захарійчук Grade 1 (NUS 2025), p.97
  notes: 'Apostrophe rule: after б,п,в,м,ф,р before я,ю,є,ї.'
- title: Захарійчук Grade 1 (NUS 2025), p.15
  notes: Hard [–] vs soft [=] consonant notation.
- title: Большакова Grade 1, p.45-47
  notes: Тверді і пом'якшені приголосні звуки.

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
- Confirmed: сім'я, день, сіль, м'ясо, п'ять, гарно, риба, батько, учитель, дев'ять, комп'ютер, м'який.
- Not found: None.

## Grammar Rules
- Апостроф (The Apostrophe): Правопис § 7 — Апостроф пишемо перед я, ю, є, ї після букв на позначення губних приголосних б, п, в, м, ф (п'ять, м'ясо, сім'я) та р (бур'ян). Він вказує на роздільну вимову твердого приголосного та наступного йотованого голосного.
- М'який знак (The Soft Sign): Правопис § 26 — Буквою ь позначаємо на письмі м'якість приголосних звуків д, т, з, с, дз, ц, л, н у кінці слова (день, сіль, учитель) та складу (батько).

## Calque Warnings
- сім'я: OK — Found in Grade 1 textbooks (Zaharijchuk p.8) alongside "родина". Both are natural, with "сім'я" often used for the nuclear family.
- учитель: OK — Standard term for a school teacher in all primary textbooks (Vashulenko, Savchuk). "Викладач" is reserved for higher education.
- батько: OK — Standard formal/neutral term for father; "тато" is also common and used in A1 contexts.

## CEFR Check
- сім'я: A1 — Found in Grade 1 Bukvar (Zaharijchuk).
- день: A1 — Found in Grade 1 Bukvar and Grade 2 Ukrainian language books.
- п'ять: A1 — Basic numeral, introduced early in Grade 1/2.
- учитель: A1 — Key classroom vocabulary found in Grade 1.
- батько: A1 — Core family vocabulary found in Grade 1.
- гарно: A1 — Common adverb found in Grade 2.
- риба: A1 — Common noun used for phonetic practice (Р, И) in Grade 1.
</pre_verified_facts>


## Wiki Teaching Brief — Your Authoritative Source

**This is your primary teaching material.** The wiki article below was compiled from real Ukrainian school textbooks, literary sources, and verified references. It contains the correct terminology, paradigm tables, teaching sequences, and examples for this module. Your job is to TRANSFORM this into engaging, level-appropriate content — not to copy it verbatim.

**How to use the wiki article:**
1. **Adopt the Ukrainian terminology.** If the article says «складоподіл», you write «складоподіл» — never CVCCV or "syllable division rules" paraphrased from English phonology. If it says «відкритий склад», you write «відкритий склад» — never "open syllable type."
2. **Follow the teaching sequence.** If the article shows: sound model → syllable → word → sentence, follow that progression. Do not rearrange or substitute your own.
3. **Use the article's examples as your foundation.** Authentic examples from textbooks beat invented ones. Use the article's examples and expand with your own that follow the same patterns.
4. **Synthesize and teach, don't summarize.** You are a teacher, not a summarizer. Take the facts from the article and weave them into engaging explanations with dialogues, situations, and practice. The article tells you WHAT to teach — you decide HOW to teach it for the target level.
5. **Your pre-training is contaminated by Russian and English linguistics.** When the article contradicts your instinct, the article wins. Ukrainian has its own phonetic categories (голосний/приголосний, дзвінкий/глухий, м'який/твердий) that do not map 1:1 to English or Russian. Use the Ukrainian categories.
6. **Do NOT copy paragraphs verbatim.** The article is reference material. Your output must be original teaching prose at the correct CEFR level, not a rephrased version of the article.

<knowledge_packet>
# Knowledge Packet: Special Signs
**Module:** special-signs | **Track:** A1

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: pedagogy/a1/special-signs.md

# Педагогіка A1: Special Signs



## Методичний підхід (Methodological Approach)

The two "special signs" in Ukrainian orthography, the **soft sign (м’який знак `ь`)** and the **apostrophe (апостроф `’`)**, are fundamental for correct pronunciation and are best taught through contrast. They perform opposite functions. Ukrainian pedagogy for native children introduces them visually and functionally, a method that is highly effective for L2 learners as well.

1.  **The Soft Sign (`ь`) as a "Softener"**: This sign has no sound of its own. Its only job is to indicate that the preceding consonant is soft (palatalized). Ukrainian textbooks introduce this concept by showing how the `ь` changes the quality of a consonant (Source 32: `5-klas-ukrmova-avramenko-2022_s0127`). For an English speaker, this is a new phonetic skill that requires focused practice on the tongue's position.

2.  **The Apostrophe (`'`) as a "Separator" or "Wall"**: The apostrophe signals a hard break. It indicates that the preceding consonant remains **hard** and the following iotated vowel (`я, ю, є, ї`) is pronounced as two distinct sounds: `[йа]`, `[йу]`, `[йе]`, `[йі]` (Source 19: `2-klas-ukrmova-bolshakova-2019-1_s0058`). Большакова's Grade 2 textbook explicitly states the apostrophe's function is to show the preceding consonant is hard and the following iotated vowel represents two sounds. This "wall" analogy is a powerful pedagogical tool.

3.  **Teaching through Minimal Pairs**: The core of the native method is contrasting words that differ only by the presence of a soft sign, an apostrophe, or neither. For example, `[р'а]` (in `зоря`) vs. `[рйа]` (in `подвір’я`) (Source 19). This forces the learner to hear and produce the phonetic difference, linking it directly to the written sign.

## Послідовність введення (Introduction Sequence)

For A1 learners, these signs should be introduced after the basic alphabet and the concept of iotated vowels (`я, ю, є, ї`) have been presented.

1.  **Step 1: Introduce the Soft Sign (`ь`)**.
    *   Start with word-final position, as it's the clearest example of its function. Use high-frequency words like `день`, `кінь`, `сіль`.
    *   Introduce the mnemonic "Де ти з’їси ці лини?" (`д, т, з, с, ц, л, н`) as the core group of consonants that can be followed by `ь` at the end of a word (Source 47: `7-klas-ukrmova-avramenko-2024_s0044`).
    *   Practice contrasting hard/soft pairs: `брат` vs. `брать` (to take), `став` vs. `ставь` (put). Even if the grammar is advanced, the phonetic contrast is the goal.

2.  **Step 2: Introduce the Apostrophe (`'`)**.
    *   Present it as the "anti-soft-sign." Its job is to *prevent* softening.
    *   Introduce the core rule: the apostrophe is written after the "lip" consonants `б, п, в, м, ф` and the consonant `р` before `я, ю, є, ї` (Source 49: `3-klas-ukrainska-mova-vashulenko-2020-1_s0088`). The mnemonic "Мавпочка Буф грає в чужі шахи" is used in later grades but the core letters `б, п, в, м, ф, р` are the A1 focus.
    *   Use simple, high-frequency words: `сім'я`, `м'ясо`, `п'ять`, `ім'я`, `комп'ютер`.
    *   Explicitly model the two-sound pronunciation: `м'я` = `[м] + [йа]`.

3.  **Step 3: Contrast `ь`, `'`, and nothing.**
    *   This is the most critical step. Use a three-column table with minimal pairs.
    | No Sign (softening vowel) | Soft Sign `ь` (soft consonant + `о`) | Apostrophe `'` (hard consonant + `й` + vowel) |
    | :--- | :--- | :--- |
    | `буряк` [р'а] | `бульйон` [л'о] | `бур'ян` [рйа] |
    | `свято` [с'в'а] | `сьогодні` [с'о] | `здоров'я` [вйа] |
    | `ряд` [р'ад] | `трьох` [р'ох] | `подвір'я` [рйа] |
    *   This direct comparison solidifies the distinct function of each orthographic rule (Source 40: `5-klas-ukrmova-uhor-2022-1_s0186`).

4.  **Step 4: Apostrophe after Prefixes.**
    *   Introduce this as a simple, logical rule. When a prefix ends in a hard consonant, an apostrophe is used before `я, ю, є, ї` to maintain the hard separation.
    *   Examples: `з'явитися`, `об'єднати`, `від'їзд` (Source 31: `3-klas-ukrainska-mova-vashulenko-2020-1_s0090`).

## Типові помилки L2 (Common L2 Errors)

| ❌ Помилково (Incorrectly) | ✅ Правильно (Correctly) | Чому (Why) |
| :--- | :--- | :--- |
| Writing `сімя`, `пят`, `здоровя`. | `сім'я`, `п'ять`, `здоров'я`. | Forgetting the apostrophe. English has no equivalent concept of a "separator" sign, so learners often omit it. The apostrophe is mandatory to show the consonant is hard and the vowel is iotated (`[йа]`). (Source 49) |
| Pronouncing `м'ясо` as [`мьасо`] (soft m). | Pronouncing `м'ясо` as [`мйасо`] (hard m + ya). | The apostrophe's primary function is to signal the preceding consonant is **hard**. Learners often see the `я` and automatically soften the `м`. The apostrophe is a "wall" that prevents this. (Source 19) |
| Using `'` after other consonants, e.g., `*кать'я`. | Not using an apostrophe there. | The main apostrophe rule applies to a specific set of consonants (`б, п, в, м, ф, р`). Learners may overgeneralize the rule to other consonants. (Source 50) |
| Writing `льожка` or `тьохкає`. | `ложка` (hard л), `тьохкає` (soft т). | Confusing the soft sign (`ь`) with palatalization rules. The soft sign is not used before all vowels, and the combination `ьо` is used to represent `[ьо]`, but `ло` is simply `[ло]`. (Source 42: `6-klas-ukrmova-betsa-2023_s0032`) |
| Writing `компютер` or `інтервю`. | `комп'ютер`, `інтерв'ю`. | Forgetting the apostrophe in common loanwords. This is a very frequent error. The rule applies consistently to these words. (Source 24) |
| Treating `ь` as a silent letter like in English "debt". | Treating `ь` as a command to modify the previous consonant. | English orthography has no direct parallel. The soft sign has zero sound value itself but carries a critical instruction for the consonant before it. (Source 32) |

## Деколонізаційні застереження (Decolonization Notes)

This is a critical area where Russian influence can mislead learners. Ukrainian orthography must be taught on its own terms.

1.  **The Apostrophe is NOT a Hard Sign**: The Ukrainian apostrophe (`'`) is a unique feature. It is **not** a replacement for or equivalent to the Russian hard sign (`ъ`). The Russian hard sign also serves a separating function, but their historical development and usage rules are different. The writer must avoid any comparison, as it creates a false equivalency and frames Ukrainian as a derivative of Russian. The Ukrainian apostrophe was standardized in the early 20th century to solve a phonetic challenge using the tools available in a standard typeset, distinct from the Cyrillic-specific `ъ` (Source 22: `ext-istoria_movy-52`).

2.  **Teach Ukrainian Phonetics Natively**: Do not explain the soft sign `ь` as being "like the Russian soft sign." While functionally similar, the degree and quality of palatalization can differ. The learner's reference point must be native Ukrainian audio and phonetic descriptions, not another Slavic language.

3.  **No Russian Examples**: All example words, phrases, and texts must be Ukrainian. Using Russian examples (e.g., to show a cognate) implicitly centers Russian as the default Slavic language and should be strictly avoided.

4.  **Historical Context**: Ukrainian writers in the 19th century used various systems to represent these sounds before the modern apostrophe was standardized (Source 22). This shows a living language evolving its own writing system, not borrowing one. This context is for the writer's understanding, not necessarily for the A1 lesson itself, but it informs a decolonized approach.

## Словниковий мінімум (Vocabulary Boundaries)

### Words with Apostrophe (`'`)
*   ★★★ (Essential): `сім'я`, `м'ясо`, `п'ять`, `дев'ять`, `ім'я`, `здоров'я`, `комп'ютер`, `подвір'я`, `пам'ять`.
*   ★★ (Useful): `в'язати` (to knit), `бур'ян` (weed), `пір'я` (feathers), `черв'як` (worm), `об'єкт` (object).
*   ★ (Can wait): `торф'яний` (peat), `міжгір'я` (intermountain), `Лук'ян` (name).

### Words with Soft Sign (`ь`)
*   ★★★ (Essential): `день`, `вчитель`, `батько`, `Львів`, `кінь`, `осінь`, `сіль`, `сьогодні`, `польський`, `український`, `-ський` (in general).
*   ★★ (Useful): `лялька` (doll), `тінь` (shadow), `палець` (finger), `хлопець` (boy), `щось`, `десь`.
*   ★ (Can wait): `мільйон`, `бульйон`, `різьбяр` (carver), `женьшень` (ginseng).

## Приклади з підручників (Textbook Examples)

These exercise formats are taken directly from Ukrainian elementary school textbooks and are perfect for A1 learners.

1.  **Contrastive Choice (from Source 19)**
    *   *Мета: Навчити розрізняти м'яку вимову (`ря`) і роздільну вимову (`р'я`).*
    *   **Вправа:** Прочитай слова. Поясни, де `я` позначає один звук, а де два.
        *   `зоря` — `сузір'я`
        *   `буряк` — `бур'ян`
        *   `Різдво` — `різдв'яний`

2.  **Fill in the `ь` or `'` (from Sources 24, 47)**
    *   *Мета: Застосувати правила вживання апострофа і м'якого знака.*
    *   **Вправа:** Вставте, де потрібно, `ь` або `'`.
        *   `здоров..я`
        *   `пол..ський`
        *   `комп..ютер`
        *   `учител..`
        *   `п..ятниця`
        *   `Л..вів`
        *   `сім..я`
        *   `пал..то`

3.  **Categorization (from Source 47)**
    *   *Мета: Перевірити розуміння правил для обох знаків.*
    *   **Вправа:** Розподіліть слова на три колонки: 1) з апострофом, 2) з м'яким знаком, 3) без знаків.
    *   *Слова:* `Свято`, `Дев'ять`, `Різдво`, `Морква`, `Батько`, `Подвір'я`, `Тінь`, `П'ятниця`, `Український`, `М'яч`.

4.  **Word Puzzle / Riddle (from Source 19)**
    *   *Мета: Закріпити написання слів з апострофом у контексті.*
    *   **Вправа:** Прочитай опис і запиши слово-відгадку.
        *   "П'ятий день тижня." (Відповідь: `п'ятниця`)
        *   "Тато, мама і я — це дружна..." (Відповідь: `сім'я`)
        *   "Його їдять. Воно не риба і не овоч." (Відповідь: `м'ясо`)

## Пов'язані статті (Related Articles)
- `pedagogy/a1/iotated-vowels`
- `pedagogy/a1/consonants-hard-soft`
- `phonetics/palatalization`
- `orthography/history-of-the-apostrophe`

---

### Вікі: pedagogy/a1/this-and-that.md

# Педагогіка A1: This And That



## Методичний підхід (Methodological Approach)

The core pedagogical principle for teaching demonstratives (`цей`, `той`) in Ukrainian is to tightly integrate them with the concept of noun gender. Ukrainian elementary school textbooks do not teach these words in isolation; they are presented as a fundamental tool for identifying and reinforcing a noun's gender from the very beginning (Джерело: `3-klas-ukrainska-mova-kravtsova-2020-1_s0062`).

The primary method is **substitution and association**. Learners are taught to associate a noun with a chain of gender-agreeing words. For a masculine noun like `стіл` (table), the chain is `стіл` → `він` (he) → `мій` (my) → `цей` (this) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0030`, `3-klas-ukrainska-mova-ponomarova-2020-1_s0085`). This creates a powerful mental link between the noun and its grammatical gender, making adjective agreement (e.g., `цей червоний стіл`) intuitive later on.

The unchangeable pronoun `це` ("this/that is") is introduced first as a simple identifier. It is the most frequent and simplest form, used in basic sentence patterns like "**Це** + [іменник]" (e.g., "**Це** стіл," "**Це** книга."). This allows learners to start building sentences before tackling gender agreement (Джерело: `ext-video-4`, `5-klas-ukrmova-uhor-2022-1_s0081`).

Only after `цей/ця/це` are mastered as pointers for "close" objects is the "far" equivalent `той/та/те` introduced, often through direct contrastive exercises (`цю книгу чи ту книгу?` — "this book or that book?") (Джерело: `6-klas-ukrmova-litvinova-2023_s0280`).

Finally, demonstratives are presented as a key tool for creating cohesive text by avoiding noun repetition. Textbooks show how words like `цей`, `ця`, `він`, `вона` connect sentences and make writing flow more naturally (Джерело: `4-klas-ukrmova-zaharijchuk_s0014`, `4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0148`). At the A1 level, the focus is purely on the nominative (subject) case. Full declension is a B1 topic (<!-- VERIFY -->).

## Послідовність введення (Introduction Sequence)

The introduction must be methodical and layered, building from the simplest concept to the more complex.

- **Step 1: The Universal Identifier `Це`**
  - **What:** Introduce the word `це` as the universal, gender-neutral way to say "This is..." or "That is...". It answers the question `Що це?` (What is this?).
  - **Why:** This is the highest frequency demonstrative and requires zero knowledge of gender. It allows learners to immediately start identifying objects. For example: `Що це? - Це стіл.` `Що це? - Це книга.` (Джерело: `ext-video-4`). It functions like "It is" in English.

- **Step 2: The Gender Pointers `Цей`, `Ця`, `Це`**
  - **What:** Introduce the three gendered forms of "this": `цей` (masculine), `ця` (feminine), and `це` (neuter). Explicitly link them to the gender pronouns `він`, `вона`, `воно` and possessives `мій`, `моя`, `моє`.
  - **Why:** This directly reinforces noun gender. The teaching pattern is: see a noun (`стіл`), recall its gender pronoun (`він`), and then select the corresponding demonstrative (`цей стіл`) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0030`, `3-klas-ukrainska-mova-vashulenko-2020-1_s0128`). This builds the grammatical reflex for agreement.

- **Step 3: The Plural Pointer `Ці`**
  - **What:** Introduce the plural form `ці` ("these") for all genders.
  - **Why:** After mastering the three singular forms, the single plural form is a simple next step. It shows how gender distinctions disappear in the plural for demonstratives. Example: `ці столи`, `ці книги`, `ці вікна`. (Джерело: `4-klas-ukrmova-zaharijchuk_s0014`).

- **Step 4: Distinguishing "This" vs. "That" (`Той`, `Та`, `Те`, `Ті`)**
  - **What:** Introduce the "far" pointers `той` (m), `та` (f), `те` (n), and `ті` (pl) to contrast with the "near" pointers (`цей`, `ця`, `це`, `ці`).
  - **Why:** This concept of proximity is familiar to English speakers ("this/that"). It should be taught with contrastive examples, physically pointing to near and far objects. For example: `Цей стілець тут, а той стілець там.` (This chair is here, and that chair is there). `Мені, будь ласка, це/те тістечко` (Source 3) is a perfect textbook example of this choice.

- **Step 5: Demonstratives for Text Cohesion**
  - **What:** Show how `цей`, `він`, `вона` etc., are used to refer back to a previously mentioned noun to avoid clumsy repetition.
  - **Why:** This moves learners from single sentences to basic text construction. It's a key feature of natural Ukrainian writing style. (Джерело: `4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0148`, `4-klas-ukrmova-zaharijchuk_s0014`). For example: "Славко купив букет квітів... **Він** також узяв книжку." (Slavko bought a bouquet... **He** also took a book).

## Типові помилки L2 (Common L2 Errors)

English-speaking learners often make predictable errors when learning Ukrainian demonstratives due to interference from English grammar.

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| `Що цей?` | `Що це?` | Learners mistakenly use the gendered `цей` for the general question "What is this?". The correct form for identification is always the neutral, unchangeable `це`. (Джерело: `ext-video-4`) |
| `Ця стіл великий.` | `Цей стіл великий.` | This is a direct gender agreement error. The learner has not yet internalized that `стіл` is masculine and requires the masculine demonstrative `цей`. This is the most common error and is why linking demonstratives to gender is so critical. (Джерело: `3-klas-ukrainska-mova-ponomarova-2020-1_s0085`) |
| `Це стіл є новий.` | `Цей стіл новий.` or `Це новий стіл.` | Learners overuse the verb `є` (is/are), translating directly from English. In simple descriptive sentences in Ukrainian, the verb "to be" is usually omitted in the present tense. The first correct option uses the demonstrative as a pointer, while the second uses `це` as an identifier. |
| `Це столи.` | `Ці столи.` | The learner incorrectly uses the singular identifier `це` when pointing to multiple items. The correct plural demonstrative is `ці` for "these". (Джерело: `ext-ulp_youtube-261`) |
| `Мені подобається цей дівчина.` | `Мені подобається ця дівчина.` | Another gender agreement error, but with a feminine noun. The learner applies the default/masculine form `цей` to the feminine noun `дівчина`. (Джерело: `5-klas-ukrmova-uhor-2022-1_s0030`) |
| `Я живу в цей будинок.` | `Я живу в цьому будинку.` | This is a case error. While full declension is not an A1 topic, learners will encounter prepositions. They often incorrectly use the nominative form (`цей`) after a preposition instead of the required locative (`цьому`). This should be taught as a fixed chunk (`в цьому будинку`) at A1, with the grammatical explanation delayed. (<!-- VERIFY -->) |

## Деколонізаційні застереження (Decolonization Notes)

Teaching Ukrainian requires a conscious effort to de-link it from Russian and establish its own phonetic and grammatical foundation in the learner's mind.

1.  **Independent Phonetics:** The sound `[ц]` must be taught as a native Ukrainian phoneme. Do not describe it as "like the Russian ц". Use examples from within Ukrainian, like `цукор` (sugar), `палець` (finger), `кінець` (end). The learner's reference point must be Ukrainian itself.

2.  **No Russian Cognates as a Crutch:** Avoid teaching `цей` by comparing it to Russian `этот` or `той` to `тот`. While they are cognates from a common Slavic root, using Russian as the bridge reinforces a colonial linguistic dependency. Teach `цей` and `той` through their function and context within Ukrainian only.

3.  **Emphasize Native Etymology:** Briefly explain that `цей` comes from an older Ukrainian form `отъ + сей` ("lo, this"), which evolved into `отсей` and then was re-analyzed as `о-цей`, eventually yielding the standalone `цей` (Джерело: `ext-istoria_movy-103`). This demonstrates a clear, internal path of development for the word within the Ukrainian language itself, countering any false narrative of it being a Russian import or derivative.

4.  **Ukrainian Sentence Structure:** Stress that the omission of "to be" (`є`) in sentences like `Цей стіл червоний` is a standard feature of Ukrainian grammar. It is not an "informal" version of a structure that "should" have a verb like in Russian (`Этот стол есть красный`). This validates Ukrainian grammar on its own terms.

5.  **Stylistic Norms:** The use of demonstratives and personal pronouns (`цей`, `він`, `вона`) to avoid repeating nouns is a characteristic of good Ukrainian style, as taught in Ukrainian schools (Джерело: `4-klas-ukrmova-zaharijchuk_s0014`, `2-klas-ukrmova-bolshakova-2019-2_s0044`). It should be presented as a native stylistic device, not a calque from another language.

## Словниковий мінімум (Vocabulary Boundaries)

This vocabulary is appropriate for A1 learners when practicing demonstratives. It focuses on concrete, point-able objects found in a classroom or home.

**Іменники (Nouns):**
- ★★★ `стіл` (table) (Джерело: `ext-ulp_youtube-261`)
- ★★★ `стілець` (chair) (Джерело: `ext-ulp_youtube-261`)
- ★★★ `книга` (book)
- ★★★ `ручка` (pen) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0030`)
- ★★★ `вікно` (window) (Джерело: `ext-ulp_youtube-261`)
- ★★☆ `будинок` (house, building) (Джерело: `3-klas-ukrainska-mova-vashulenko-2020-1_s0128`)
- ★★☆ `кімната` (room) (Джерело: `ext-ulp_youtube-261`)
- ★★☆ `двері` (door - *plural only*) (Джерело: `ext-ulp_youtube-261`)
- ★★☆ `олівець` (pencil) (Джерело: `3-klas-ukrainska-mova-savchenko-2020-2_s0009`)
- ★★☆ `шафа` (wardrobe, cabinet) (Джерело: `ext-ulp_youtube-261`)
- ★☆☆ `ліжко` (bed) (Джерело: `ext-ulp_youtube-261`)
- ★☆☆ `поле` (field) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0030`)

**Прикметники (Adjectives):**
- ★★★ `новий` (new) (Джерело: `4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0065`)
- ★★★ `старий` (old) (Джерело: `6-klas-ukrmova-betsa-2023_s0113`)
- ★★★ `великий` (big)
- ★★★ `малий` (small)
- ★★☆ `червоний` (red) (Джерело: `10-klas-ukrajinska-mova-avramenko-2018_s0186`)
- ★★☆ `синій` (blue) (Джерело: `3-klas-ukrainska-mova-vashulenko-2020-1_s0128`)
- ★★☆ `жовтий` (yellow) (Джерело: `6-klas-ukrmova-betsa-2023_s0113`)
- ★★☆ `зелений` (green) (Джерело: `6-klas-ukrmova-betsa-2023_s0113`)
- ★★☆ `гарний` (good, beautiful) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0081`)

**Дієслова (Verbs):**
- ★★★ `бути` (to be)
- ★★★ `мати` (to have)
- ★★★ `бачити` (to see)
- ★★☆ `жити` (to live) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0081`)
- ★★☆ `хотіти` (to want)

## Приклади з підручників (Textbook Examples)

These exercises, adapted from Ukrainian school materials, provide a gold standard for practice activities.

1.  **Gender Sorting with Demonstratives (Джерело: `3-klas-ukrainska-mova-kravtsova-2020-1_s0062`)**
    - **Format:** Sorting task. Provide a list of nouns and three columns.
    - **Prompt:** "Розподіли іменники за родами. Запиши назви в потрібний рядок." (Distribute the nouns by gender. Write the names in the correct row.)
    - **Task:**
        - **Він, мій, цей:** `стіл`, `олівець`, `будинок`
        - **Вона, моя, ця:** `книга`, `ручка`, `шафа`
        - **Воно, моє, це:** `вікно`, `ліжко`, `поле`

2.  **Forced Choice: This vs. That (Джерело: `6-klas-ukrmova-litvinova-2023_s0280`)**
    - **Format:** Multiple choice within a sentence.
    - **Prompt:** "Прочитайте речення, обираючи правильний займенник." (Read the sentences, choosing the correct pronoun.)
    - **Task:**
        - 1. Привал буде за (цією / тією) горою. (The stop will be behind *this* / *that* mountain.)
        - 2. Мені, будь ласка, (це / те) тістечко. (For me, please, *this* / *that* pastry.)
        - 3. Візьміть (цю / ту) книгу, не пошкодуєте. (Take *this* / *that* book, you won't regret it.)

3.  **Adjective and Demonstrative Agreement (Джерело: `6-klas-ukrmova-betsa-2023_s0113`, `3-klas-ukrainska-mova-vashulenko-2020-1_s0128`)**
    - **Format:** Fill-in-the-blanks for endings.
    - **Prompt:** "Оберіть правильний варіант закінчення." (Choose the correct ending.)
    - **Task:**
        - Який? (m): `Нов__ стіл`, `цікав__ фільм`, `цей хорош__ друг` → (`-ий`, `-ий`, `-ій`)
        - Яка? (f): `Ця нов__ сукня`, `цікав__ казка` → (`-а`, `-а`)
        - Яке? (n): `Це нов__ крісло`, `цікав__ оповідання` → (`-е`, `-е`)

4.  **Text Cohesion via Pronoun Substitution (Джерело: `4-klas-ukrmova-zaharijchuk_s0014`)**
    - **Format:** Text rewriting.
    - **Prompt:** "Спишіть текст, уникаючи повторів виділених слів. Підкресліть слова, які зв’язують речення в тексті." (Rewrite the text, avoiding repetition of the highlighted words. Underline the words that connect the sentences in the text.)
    - **Original Text:** "Марусі... подарували маленький рожевий ноутбук. **Ноутбук** став для Марусі найкращим другом. **Ноутбук** зберігав маленькі таємниці дівчинки..."
    - **Expected Output:** "Марусі... подарували маленький рожевий ноутбук. **Він** став для Марусі найкращим другом. **Цей комп'ютер** зберігав маленькі таємниці дівчинки..."

## Пов'язані статті (Related Articles)

- `pedagogy/a1/noun-gender`
- `pedagogy/a1/adjective-agreement`
- `pedagogy/a1/personal-pronouns`
- `pedagogy/a2/introduction-to-cases`
- `grammar/nouns/pluralization`
</wiki_context>

## Plan References

- 
- 
- 

</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## М'який знак (The Soft Sign — Ь)` (~250 words)
- `## Апостроф (The Apostrophe)` (~250 words)
- `## Дзвінкі і глухі (Voiced and Voiceless)` (~250 words)
- `## Вимова українських звуків (Pronouncing Ukrainian Sounds)` (~250 words)
- `## Підсумок — Summary` (~200 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 5-15% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: Mostly English with Ukrainian words bolded inline.
- UKRAINIAN CONTENT: Words and short phrases inline: "The letter **Н** looks like H but sounds like N."
- DIALOGUES & READING PRACTICE: Short Ukrainian sentences in blockquotes are encouraged.
- TABLES: Simple letter-sound or word-meaning tables.
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

  (No specific dialogue situations in plan — pick a unique real-world setting that motivates the grammar.)
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

GRAMMAR CONSTRAINTS (A1.1 — Phonetics, M01-M03):
NO CONJUGATED VERBS. NO IMPERATIVES. This is the phonetics phase.

VIDEO-FIRST PEDAGOGY (M01-M03 ONLY):
The learner CANNOT read Cyrillic yet. Letters are introduced BY VIDEO, not by text.
When the plan provides Anna Ohoiko pronunciation videos, structure each letter as:
1. Embed the video (the pipeline handles the actual embed)
2. Short English note about what the learner just heard/saw
3. Example words with English translations
Do NOT write paragraphs describing how to position your tongue or shape your mouth.
The video shows pronunciation — your job is to explain what the learner heard,
point out patterns, and give practice words. Keep it short and visual.

ALLOWED structures (Ukrainian examples only):
- Це + noun: «Це кіт», «Це мама»
- Noun + тут/там: «Мама тут», «Кіт там»
- Question words: «Хто це?», «Що це?», «Де мама?»
- Так/Ні: «Так, це кіт», «Ні, це не кіт»
- Fixed phrases (memorized, no grammar): дякую, будь ласка, привіт

BANNED: ALL verbs, past/future tense, cases, compound sentences

STRESS MARKS: Do NOT add stress marks (´). Write plain Ukrainian.
The pipeline adds stress marks deterministically after you write.

METALANGUAGE: English prose, Ukrainian examples. Bilingual headings.

### Vocabulary

**Required:** сім'я (family) — apostrophe word, день (day) — soft sign after Н, сіль (salt) — soft sign after Л, м'ясо (meat) — apostrophe after М, п'ять (five) — apostrophe after П, гарно (nicely, beautifully) — Г [ɦ] practice, риба (fish) — Р and И practice
**Recommended:** батько (father, formal) — soft sign, учитель (teacher) — soft sign at end, дев'ять (nine) — apostrophe, комп'ютер (computer) — apostrophe in cognate, м'який (soft) — apostrophe only (NO soft sign! Й is inherently soft)

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
## М'який знак (The Soft Sign — Ь) (~275 words total)
- P1 (~70 words): Introduce the soft sign (ь) as a silent instruction to the tongue. Explain that it has no sound of its own but changes the quality of the consonant before it. Use the word "день" (day) and "сіль" (salt) to demonstrate the softening of [н] and [л].
- P2 (~80 words): Explain the "mnemonic" rule for consonants that can be softened: "ДЗіДЗьо, Де Ти З’їСи Ці ЛиНи" (д, т, з, с, ц, л, н, р, дз). Introduce the notation for hard consonants [–] and soft consonants [=] used in Ukrainian textbooks like Захарійчук Grade 1.
- P3 (~70 words): Detail the placement of the soft sign in the middle of words. Provide examples such as "батько" (father), "учитель" (teacher), and "маленький" (small). Explain that the letter "й" is inherently soft and never needs a soft sign.
- P4 (~55 words): Contrastive phonetic practice using minimal pairs to show how meaning changes. Compare "брат" (brother, hard [т]) vs. "брать" (to take, soft [т']). Emphasize the physical tongue position for palatalization.
- <!-- INJECT_ACTIVITY: odd-one-out-softening --> [type: odd-one-out, focus: identifying consonants that cannot be softened by Ь (e.g., labials or sibilants), 6 items]

## Апостроф (The Apostrophe) (~275 words total)
- P1 (~70 words): Introduce the apostrophe (’) as the "wall" or separator. Explain its opposite function to the soft sign: it keeps the preceding consonant hard and forces the following vowel to be pronounced as two distinct sounds [й + vowel].
- P2 (~75 words): Detail the "Lip Consonant" rule (б, п, в, м, ф) and "р" before the vowels я, ю, є, ї. Use the example "сім'я" (family) to show the separation [сім-йа]. Explicitly state that the consonant must remain hard.
- P3 (~70 words): Provide high-frequency vocabulary for reading practice. Focus on "м'ясо" (meat), "п'ять" (five), and "дев'ять" (nine). Guide the learner through the pronunciation of [м-йасо] versus the common error of softening the [м].
- P4 (~60 words): Address the use of apostrophes in modern loanwords and international vocabulary. Use "комп'ютер" (computer) and "об'єкт" (object) as familiar anchors. Note that this rule is consistent across the language.
- <!-- INJECT_ACTIVITY: fill-in-special-signs --> [type: fill-in, focus: choosing between Ь and apostrophe in words like сім_я, ден_, п_ять, 6 items]
- <!-- INJECT_ACTIVITY: error-correction-apostrophe --> [type: error-correction, focus: identifying and fixing missing apostrophes in words like м'ясо, сім'я, п'ять, 6 items]
- <!-- INJECT_ACTIVITY: group-sort-signs --> [type: group-sort, focus: sorting words into categories: has Ь, has apostrophe, or neither, 18 items]

## Дзвінкі і глухі (Voiced and Voiceless) (~275 words total)
- P1 (~70 words): Introduce the concept of "voiced" (дзвінкі) and "voiceless" (глухі) consonants. Use the "hand on throat" test to explain vibration. Use the simplest pair [б] and [п] to illustrate the difference.
- P2 (~80 words): List the eight main voiced-voiceless pairs: Б-П, Д-Т, Г-Х, Ґ-К, З-С, Ж-Ш, ДЗ-Ц, ДЖ-Ч. Explain that сонорні (sonorants) like в, л, м, н, й, р do not have voiceless pairs in Ukrainian.
- P3 (~85 words): Explain the "Resilience Rule" of Ukrainian phonetics: voiced consonants stay voiced even at the end of words. Contrast this with other languages. Use "дуб" [дуб] and "мороз" [мороз] as primary examples. Introduce the sole common exception: "легко" [лехко].
- P4 (~40 words): Meaning changes through voicing. Present minimal pairs for ear training: "балка" (beam) vs. "палка" (stick) and "коза" (goat) vs. "коса" (braid).
- <!-- INJECT_ACTIVITY: match-up-voiced-voiceless --> [type: match-up, focus: matching voiced consonants with their voiceless partners (Б↔П, Д↔Т, etc.), 8 items]
- <!-- INJECT_ACTIVITY: true-false-devoicing --> [type: true-false, focus: checking understanding of final consonant pronunciation and the "легко" exception, 6 items]

## Вимова українських звуків (Pronouncing Ukrainian Sounds) (~275 words total)
- P1 (~100 words): Focus on the vowel И [и]. Explain it as a distinct sound, not a variation of І [і]. Use minimal pairs to train the ear: "бик" (bull) vs. "бік" (side), "дим" (smoke) vs. "дім" (house), and "кит" (whale) vs. "кіт" (cat).
- P2 (~100 words): Contrast Г [ɦ] and Ґ [g]. Describe Г as a "voiced fricative" (like a heavy breath with voice) and Ґ as a "hard stop" (like English 'g' in 'goat'). Use "гарно" (nicely) and "гора" (mountain) vs. "ґанок" (porch) and "ґудзик" (button).
- P3 (~75 words): Introduce the Ukrainian trilled Р [р]. Provide tips for tongue placement at the alveolar ridge. Use practice words that build rhythm: "риба" (fish), "ранок" (morning), "робота" (work), and "рука" (hand).
- <!-- INJECT_ACTIVITY: quiz-g-vs-ge --> [type: quiz, focus: choosing the correct letter (Г or Ґ) for specific words based on sound, 6 items]

## Підсумок — Summary (~220 words)
- P1 (~220 words): Recap the module with a self-check list.
  - What does the soft sign (Ь) do? (It softens the previous consonant, has no sound).
  - Which consonants can be followed by Ь? (Д, Т, З, С, Ц, Л, Н, Р, ДЗ).
  - When do we use an apostrophe? (After б, п, в, м, ф, р before я, ю, є, ї).
  - Does a voiced consonant like "б" change at the end of a word? (No, it stays voiced).
  - What is the difference between Г and Ґ? (Г is a fricative/breathy sound, Ґ is a hard stop).
  - Read these challenge words aloud: сім'я, день, п'ять, гарно, риба, м'ясо.

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
