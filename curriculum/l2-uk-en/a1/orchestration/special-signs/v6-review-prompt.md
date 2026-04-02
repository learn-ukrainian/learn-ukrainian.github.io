<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 3: Special Signs (A1, A1.1 [Sounds, Letters, and First Contact])
**Writer:** Gemini
**Word target:** 1200

## Plan (source of truth)

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

## Generated Content

<generated_module_content>
## М'яки́й знак (The Soft Sign — Ь)

Every Ukrainian word you have read so far has been built from letters that represent sounds. Now meet a letter that breaks that rule: **Ь** — the soft sign, or **знак м'я́кшення**. It has no sound of its own. Zero. Its only job is to change how the consonant before it is pronounced — making it soft. Consider the difference: **лук** (onion) and **люк** (hatch) are two completely different words, and the only difference is softness. The letter **Ь** marks that softness in writing. One letter, one job, zero sounds. Look at **сіль** (salt) — the **Л** is soft because of the **Ь**. Look at **день** (day) — the **Н** is soft. The consonant changes; the **Ь** itself stays silent.

Ukrainian textbooks teach a three-way system for consonants. Not every consonant can be softened with **Ь** — only a specific group. Here is the full picture from Авра́менко (Grade 5) and Большако́ва (Grade 2):

1. **М'які́ при́голосні** (truly soft consonants) — exactly 9 consonants can take **Ь** to become fully soft: **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**, **Р**, **ДЗ**. The letter **Й** is inherently soft — it never needs **Ь**. For most of these, **Ь** appears at the end of a word or syllable. For **Р**, **Ь** appears in the middle of a word before **О**: **трьох** (three, genitive), **ларьо́к** (kiosk), **чотирьо́х** (four, genitive). These are the consonants you will see **Ь** after in standard Ukrainian spelling.

2. **Пом'я́кшені приголосні** (partially softened consonants) — the labials (**Б**, **П**, **В**, **М**, **Ф**), the hushing consonants (**Ж**, **Ш**, **Ч**, **ДЖ**), and the back-tongue consonants (**К**, **Ґ**, **Г**, **Х**) can only be softened by following soft vowels like **і**, **я**, **ю**, **є**. You will **never** see **Ь** after these letters.

3. **Тверді́ приголосні** (hard consonants) — always hard, never softened at all.

Ukrainian schoolbooks use a simple notation from Захарійчук (Grade 1, p.15): hard consonants are marked [–], soft consonants are marked [=].

:::tip Mnemonic
Літвінова (Grade 5) gives students a phrase to remember which consonants take **Ь**: **«ДЗіДЗьо, Де Ти З'їСи́ Ці ЛиНи́»** — the capital letters encode 8 of the 9 consonants: **ДЗ**, **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**. The ninth — **Р** — takes **Ь** only before **О** in mid-word (трьох, ларьок). If a consonant is not in this list, **Ь** does not follow it.
:::

Common spelling patterns with **Ь**: words ending in **-нь** like **день** (day), **кінь** (horse), **о́сінь** (autumn); words ending in **-ль** like **сіль** (salt), **біль** (pain); words ending in **-ть** like **мить** (moment); and words ending in **-зь** like **мазь** (ointment). Practice reading these words with **Ь**: **учи́тель** (teacher) — **Ь** after **Л** at the end; **ба́тько** (father) — **Ь** after **Т** before **К**; **мале́нький** (small) — **Ь** after **Н** before **К**.

<!-- INJECT_ACTIVITY: odd-one-out -->

## Апо́стро́ф (The Apostrophe)

The apostrophe in Ukrainian is not a letter — it is a separator sign. It does the opposite of **Ь**: instead of softening a consonant, it keeps the consonant **hard** and splits the following vowel into two sounds.

The rule comes straight from Захарійчук (Grade 1, p.97): the apostrophe appears after the consonants **б**, **п**, **в**, **м**, **ф**, **р** — and before the vowels **я**, **ю**, **є**, **ї**. When you see this combination, the consonant stays hard, and the vowel splits into **[й]** plus a vowel sound — two sounds instead of one. Without the apostrophe, the consonant would simply soften into the following vowel.

Compare what happens with and without an apostrophe. In **пі́сня** (song), the **Н** softens smoothly into the vowel — one flowing sound. But in **м'я́со** (meat), the **М** stays hard, and the **я** splits into two sounds: **й** + **а**. You can hear the separation. Walk through the core examples:

- **сім'я́** (family) — **М** hard, then й + а
- **м'ясо** (meat) — **М** hard, then й + а
- **п'ять** (five) — **П** hard, then й + а
- **комп'ю́тер** (computer) — **П** hard, then й + у. A familiar cognate that anchors the rule perfectly.

Two more: **де́в'ять** (nine) — **В** hard, then й + а. And **м'який** (soft) — this word has an apostrophe only, with no **Ь**, because **Й** is inherently soft and never needs a soft sign.

:::note Scope
Words like **під'ї́зд** and **з'їзд** also have apostrophes, but they follow a different rule — the prefix rule, where a prefix ending in a consonant separates from **ї**. That rule comes at A2. For now, focus only on the labial rule: **б**, **п**, **в**, **м**, **ф**, **р** + **я**, **ю**, **є**, **ї**.
:::

Reading practice from the textbooks (Кравцо́ва Grade 2, Большакова Grade 1): **п'ять**, **дев'ять**, **м'яч** (ball), **м'який**, **сім'я**, **м'ясо**, **комп'ютер**, **ім'я́** (name), **здоро́в'я** (health), **пі́р'я** (feathers).

<!-- INJECT_ACTIVITY: fill-in-soft-or-apostrophe -->

<!-- INJECT_ACTIVITY: error-correction-apostrophe -->

<!-- INJECT_ACTIVITY: group-sort-soft-apostrophe -->

## Дзвінкі́ і глухі́ (Voiced and Voiceless)

Place your fingers lightly on your throat. Say **з** — you feel vibration. That vibration is your voice. Now say **с** — silence. The sound is there, but the voice is gone. This is the difference between **дзвінкі** (voiced) and **глухі** (voiceless) consonants. The difference is the **го́лос** (voice).

Ukrainian has 8 voiced-voiceless pairs. Here they are, directly from Большакова (Grade 2, p.62):

| Дзвінкі (voiced) | Б | Д | Г | Ґ | З | Ж | ДЗ | ДЖ |
|---|---|---|---|---|---|---|---|---|
| **Глухі (voiceless)** | **П** | **Т** | **Х** | **К** | **С** | **Ш** | **Ц** | **Ч** |

There is also a group called **соно́рні** — **В**, **Л**, **М**, **Н**, **Й**, **Р** — that have no voiceless partner. They sit outside the paired system entirely. On the other side, **Ф** is a voiceless consonant with no voiced partner — it too stands alone.

:::caution Non-devoicing — a defining Ukrainian feature
In many languages (German, Russian), voiced consonants lose their voice at the end of a word. Ukrainian does **not** do this. The word **дуб** (oak) is pronounced [дуб] — not [дуп]. The word **моро́з** (frost) is [мороз] — not [морос]. Also: **гриб** (mushroom) is [гриб], **нака́з** (order) is [наказ]. If your first language devoices final consonants, you need to consciously hold the voice all the way through. One well-known exception: **ле́гко** (easily) is pronounced [лехко]. But this is the rare exception — Ukrainian voiced consonants stay voiced.
:::

Textbook pairs from Большакова (Grade 2, p.62) show how voicing changes meaning: **жа́бка** (frog, diminutive) vs **ша́пка** (hat), **зли́ва** (downpour) vs **сли́ва** (plum), **ґа́ва** (crow) vs **ка́ва** (coffee), **ка́зка** (fairy tale) vs **ка́ска** (helmet).

Minimal pairs for ear training: **ба́лка** (beam) vs **па́лка** (stick), **коза́** (goat) vs **коса** (braid), **зуб** (tooth) vs **суп** (soup), **жар** (heat) vs **шар** (sphere). Say each pair aloud. Feel whether the first consonant vibrates.

<!-- INJECT_ACTIVITY: match-voiced-voiceless -->

<!-- INJECT_ACTIVITY: true-false-voicing -->

## Вимо́ва украї́нських зву́ків (Pronouncing Ukrainian Sounds)

### И vs І

Ukrainian has a vowel that exists on its own terms: **И**. It is not the same as **І**. The difference between these two sounds changes meaning completely. Four minimal pairs from the cover of Большако́ва's Grade 1 textbook:

- **бик** (bull) vs **бік** (side)
- **дим** (smoke) vs **дім** (house)
- **лист** (leaf, letter) vs **ліс** (forest)
- **кит** (whale) vs **кіт** (cat)

These are not subtle differences — **кит** and **кіт** are completely different words. **И** sits in a mid-tongue position, between **І** and **Е**. It is a distinctly Ukrainian sound. Drill these pairs aloud: **дим** — **дім** — **бик** — **бік** — **кит** — **кіт**. Watch the pronunciation video for **И** and let your ear learn the distinction directly.

### Г vs Ґ

Two separate letters, two separate sounds. **Г** is a voiced fricative — air flows through a narrowed throat, creating turbulence, but the throat never fully closes. Its voiceless partner is **Х**. Pronounce **Х**, then add voice — that is **Г**. Words: **га́рно** (beautifully), **гора́** (mountain), **голова́** (head).

**Ґ** is a voiced stop — full throat closure, then an abrupt release. Its voiceless partner is **К**. Pronounce **К**, then add voice — that is **Ґ**. Words: **ґа́нок** (porch), **ґу́дзик** (button). As Літвінова (Grade 5, p.133) states: both sounds are native Ukrainian. **Ґ** is an important part of Ukrainian phonetic identity.

:::caution Terminology
Do **not** describe **Г** as "soft." In Ukrainian phonetics, **м'який** means palatalized — and **Г** is not palatalized. **Г** is a fricative. **Ґ** is a stop. These are different manners of articulation, not hard vs. soft.
:::

An interesting pair: **ґра́ти** (iron bars, noun) vs **гра́ти** (to play, verb) — same spelling pattern, different first letter, completely different meaning.

### Р

The Ukrainian **Р** is trilled — the tongue tip vibrates against the ridge behind the upper teeth. Practice words: **рука́** (hand), **робо́та** (work), **ра́нок** (morning), **ри́ба** (fish). Watch the pronunciation video for **Р**. An imperfect **Р** is always understood by native speakers — focus on getting comfortable, not perfect.

<!-- INJECT_ACTIVITY: quiz-g-vs-gx -->

## Підсумок — Summary

Four new pieces of the Ukrainian sound system, each with a clear function: **Ь** softens the consonant before it (and has no sound of its own). The apostrophe keeps a consonant hard and splits the following vowel into two sounds. Voiced and voiceless consonants form 8 pairs — and Ukrainian keeps voiced consonants voiced at word end, unlike many other languages. **И**, **Г**, and **Р** are sounds with no direct English equivalent, built into Ukrainian on its own terms.

**Self-check** — answer these before moving on:

- **What does Ь do?** → It softens the consonant before it. It has no sound of its own.
- **After which 9 consonants can Ь appear?** → **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**, **Р** (before О), **ДЗ**. Mnemonic for 8 of them: **«ДЗіДЗьо, Де Ти З'їСи Ці ЛиНи»** — plus **Р** before **О**.
- **After which letters does the apostrophe appear?** → After **б**, **п**, **в**, **м**, **ф**, **р** — before **я**, **ю**, **є**, **ї**.
- **Name 3 voiced-voiceless pairs.** → **Б–П**, **Д–Т**, **З–С** (any three from the eight).
- **Does Ukrainian «дуб» sound like [дуб] or [дуп]?** → [дуб] — Ukrainian does not devoice at word end.
- **How is Г different from Ґ?** → **Г** is a voiced fricative (air flows through, like **Х** with voice). **Ґ** is a voiced stop (full closure then release, like **К** with voice).
- **Read these words aloud:** **сім'я**, **день**, **п'ять**, **гарно**, **риба**, **ґудзик**.

**Deterministic word count: 1472 words** (calculated by pipeline, do NOT estimate manually)

</generated_module_content>

---

## Review Protocol

### Step 1: Scan for linguistic errors

Scan the Ukrainian text for errors. Report ONLY problems found — do not echo correct text.

**Four SEPARATE checks (these are four different problems):**
1. **Russianisms** — Russian words used instead of Ukrainian (кот→кіт, хорошо→добре, конечно→звичайно, сейчас→зараз)
2. **Surzhyk** — mixed Russian-Ukrainian forms (шо→що, чо→чому, тіпа→типу)
3. **Calques** — literal translations from Russian that sound wrong in Ukrainian (приймати душ→брати душ, приймати рішення→ухвалювати рішення)
4. **Paronyms** — similar-sounding words with different meanings used incorrectly (тактична≠тактовна, ефектний≠ефективний)

**Also check:**
- Russian characters (ы, э, ё, ъ) — these must NEVER appear
- Incorrect gender assignment or case endings
- Factually wrong claims about Ukrainian phonetics, grammar, or culture

**Authority hierarchy for verification (check in this order):**
1. VESUM — does this word/form exist? POS? Gender? (415K lemmas)
2. Правопис 2019 — is it spelled correctly? Orthography rules.
3. Горох — stress position, word frequency, synonyms.
4. Антоненко-Давидович «Як ми говоримо» — is this natural Ukrainian or a calque/Russicism?
5. Грінченко «Словарь» — etymology, original meaning.

**Online fallbacks (if RAG/tools are unavailable):**
- VESUM: https://vesum.com.ua/
- Правопис 2019: https://2019.pravopys.net/
- Горох: https://goroh.pp.ua/
- Антоненко-Давидович: https://www.ukrlib.com.ua/books/printit.php?tid=4002
- Грінченко: https://hrinchenko.com/
- Словник.ua (aggregator): https://slovnyk.me/

**VESUM verification data is provided at the end of this prompt.** Use it to verify word existence before flagging linguistic errors. If a word is marked ✓ in the VESUM data, it EXISTS in Ukrainian — do not flag it as an error. If a word is marked ✗ (NOT IN VESUM), investigate further — it may be a proper noun, a compound, or genuinely wrong.

**CRITICAL: Your pre-training is contaminated by Russian.** Do NOT trust your instincts about Ukrainian words. If you are not 100% certain a word/form/usage is wrong, you MUST flag it as `[NEEDS RAG VERIFICATION]` instead of marking it as a definitive error. Wrong review findings cause wrong fixes. A false positive in the review is worse than a missed error.

If no errors found, state: "No linguistic errors found."

**Do NOT check for stress marks** — stress annotation is handled by a separate deterministic tool after the review phase. Their absence is correct.

### Step 2: Check exercises

The writer places `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. A separate ACTIVITIES step generates structured YAML exercises (`activities/{slug}.yaml`) that are injected at these markers during PUBLISH.

Check the markers and any inline exercises:
- Does each marker appear AFTER the relevant teaching section? (exercise should test what was just taught)
- Do marker IDs match the plan's `activity_hints`? (each hint should have a corresponding marker)
- Are markers spread evenly through the module? (not clustered at the end)
- For seminar modules: DSL exercise blocks (:::quiz, :::fill-in) may appear inline — check their logic

For each exercise (DSL or marker), check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?

Also check: Are there enough exercise markers/blocks total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercise content is generated by a separate tool from YAML. If exercise LOGIC is wrong, flag it. If the FORMAT looks unusual (React components, YAML structure), that is expected.

### PROOF OF ABSENCE — mandatory before claiming ANYTHING is missing

**Before you claim a word, symbol, notation, or plan point is MISSING from the content, you MUST search for it.** Use your MCP tools (`verify_words`, `search_text`) or carefully re-read the specific section where it should appear.

Rules:
- If you claim "[•] notation is missing" — you must have searched the content for `[•]` and confirmed 0 occurrences
- If you claim "vocabulary word X is missing" — you must have searched for that exact word
- If you claim "plan point Y was not covered" — you must quote which section you expected it in and confirm it's not there
- **NO CLAIMS OF ABSENCE WITHOUT EVIDENCE.** Your tokenizer can miss special characters like [•], [–], [=], «», and other non-alphanumeric symbols. Do not trust a quick scan.
- Euphony alternation (у/в, і/й) is a MINOR stylistic issue, NEVER a critical error. Both forms are attested in published Ukrainian literature.

**A false finding wastes an entire rebuild cycle. Be precise.**

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | DEDUCT for: missing content_outline points, section word budgets off by >10%, plan references not cited, vocabulary from plan absent from prose. REWARD for: every plan point covered with specific examples, correct section pacing, textbook references integrated naturally. Quote the plan point that was missed or covered. |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | DEDUCT for: grammar rules presented as bare lists without examples, concepts taught before prerequisite knowledge, >100 words of English theory without a Ukrainian example, bare vocabulary lists instead of contextualized introduction. REWARD for: PPP flow (situation→pattern→practice), 3+ examples per grammar point, textbook pedagogy (Большакова, Захарійчук), grammar scope respected. |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | DEDUCT for: all correct answers at the same index position, trivially easy exercises (1:9 group sort ratios, every answer is the same word), exercises that test content recall instead of language skill, items fewer than plan's activity_hints count, exercises placed before the concept is taught. REWARD for: varied answer positions, plausible distractors, exercises testing what was just taught, matching plan's activity_hints type and focus exactly. |
| 6 | **Engagement & tone** | 10% | DEDUCT for: motivational openers ("Numbers unlock the real Ukraine!"), meta-commentary ("Let us look at...", "Let us now explore..."), generic enthusiasm ("incredibly melodic", "hugely important"), telling instead of showing ("You now possess...", "You have unlocked..."), gamified language ("unlocked the ability"), corporate-speak ("precision and accuracy"), "The magic of...", any sentence that could apply to any language course unchanged. REWARD for: specific cultural details, natural dialogues, humor, concrete examples, teacher demonstrating rather than lecturing about how great the content is. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count outside target range, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count in range. |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | DEDUCT for: purely transactional exchanges ("Do you have X? Yes."), dialogues where one speaker interrogates the other, anonymous em dashes instead of named speakers, stilted/textbook-robotic phrasing. REWARD for: natural multi-turn conversations, real situations (searching for keys, ordering at a cafe, meeting a friend), culturally appropriate responses, named speakers with distinct voices. |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

**CRITICAL RULE: If you mention ANY error, mistake, or inaccuracy in the evidence column of your scores table, you MUST also list it as a structured finding below AND include it in your `<fixes>` block.** Identifying an error in evidence but not outputting a finding+fix means the error ships to learners. This is a language curriculum — every error you identify must be fixed. No exceptions.

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Severity guide:
- **Critical** = factual/linguistic error that teaches wrong Ukrainian (wrong form, wrong rule, wrong example). Module cannot ship.
- **Major** = quality below standard but not factually wrong (weak explanation, awkward phrasing, missing examples).
- **Minor** = polish item (tone, word choice, style).

**Any factual or linguistic error is CRITICAL, not minor.** A wrong syllable division, a wrong phonetic claim, a contradictory grammar rule — these are critical because learners will memorize them as truth.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero findings mentioning errors/mistakes/inaccuracies. All dimensions ≥9. |
| **REVISE** | Has findings with fixes. Any dimension <9 with identified errors = REVISE, not PASS. |
| **REJECT** | Fundamental structural/pedagogical problems requiring rewrite. |

### Step 7: Fix it yourself (REVISE only)

If your verdict is **REVISE**, you MUST output a `<fixes>` block with exact find/replace pairs. The pipeline applies these deterministically — no LLM regeneration, no rewriting from scratch.

Rules for fixes:
- Each fix is a YAML entry with `find:` (exact text from the module) and `replace:` (corrected text)
- The `find` string must be an EXACT substring of the module content — copy-paste it
- Keep fixes minimal — change only what's wrong, preserve surrounding text
- Do NOT fix словник/vocabulary tables (those are generated by a downstream tool)
- For word count issues: add content as a new `insert_after:` entry instead of find/replace

---

## Output Format

```
## Linguistic Scan
[errors found, or "No linguistic errors found"]

## Exercise Check
[placeholder inventory and issues]

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | X/10 | [specific evidence from the text] |
| ... | ... | ... |

## Findings
[list all findings with dimension/severity/location/issue/fix]

## Verdict: PASS / REVISE / REJECT
[justification — reference both score gate and severity gate]

<fixes>
- find: "exact text from module"
  replace: "corrected text"
- find: "another exact problem"
  replace: "the fix"
</fixes>
```

**The `<fixes>` block is REQUIRED for REVISE verdicts.** Without it, the pipeline cannot apply your fixes. For PASS verdicts, omit the `<fixes>` block. For REJECT verdicts, the module needs a full rebuild — `<fixes>` is optional.


<vesum_verification>
The following Ukrainian words from the content were verified against VESUM (415K lemmas). Use this data to check linguistic claims — do NOT guess about words.

Verified: 64 words | Not found: 48 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Апо — NOT IN VESUM
  ✗ Большако — NOT IN VESUM
  ✗ Большакова — NOT IN VESUM
  ✗ Вимо — NOT IN VESUM
  ✗ Захарійчук — NOT IN VESUM
  ✗ Кравцо — NOT IN VESUM
  ✗ Літвінова — NOT IN VESUM
  ✗ М'яки — NOT IN VESUM
  ✗ Пом'я — NOT IN VESUM
  ✗ бка — NOT IN VESUM
  ✗ в'я — NOT IN VESUM
  ✗ в'ять — NOT IN VESUM
  ✗ ва' — NOT IN VESUM
  ✗ гко — NOT IN VESUM
  ✗ дзик — NOT IN VESUM
  ✗ здоро — NOT IN VESUM
  ✗ зка — NOT IN VESUM
  ✗ комп'ю — NOT IN VESUM
  ✗ кшення — NOT IN VESUM
  ✗ кшені — NOT IN VESUM
  ✗ ків — NOT IN VESUM
  ✗ ларьо — NOT IN VESUM
  ✗ ларьок — NOT IN VESUM
  ✗ лехко — NOT IN VESUM
  ✗ лка — NOT IN VESUM
  ✗ лос — NOT IN VESUM
  ✗ м'я — NOT IN VESUM
  ✗ менко — NOT IN VESUM
  ✗ морос — NOT IN VESUM
  ✗ нака — NOT IN VESUM
  ✗ нок — NOT IN VESUM
  ✗ нських — NOT IN VESUM
  ✗ нький — NOT IN VESUM
  ✗ пка — NOT IN VESUM
  ✗ під'ї — NOT IN VESUM
  ✗ р'я — NOT IN VESUM
  ✗ рно — NOT IN VESUM
  ✗ рні — NOT IN VESUM
  ✗ сли — NOT IN VESUM
  ✗ сня — NOT IN VESUM
  ✗ соно — NOT IN VESUM
  ✗ стро — NOT IN VESUM
  ✗ сінь — NOT IN VESUM
  ✗ тель — NOT IN VESUM
  ✗ тько — NOT IN VESUM
  ✗ украї — NOT IN VESUM
  ✗ чотирьо — NOT IN VESUM
  ✗ ґра — NOT IN VESUM

All 64 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `mcp_rag_verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `mcp_rag_verify_lemma` — full declension/conjugation for a lemma
- `mcp_rag_search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `mcp_rag_query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `mcp_rag_query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `mcp_rag_search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `mcp_rag_search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `mcp_rag_search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `mcp_rag_search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `mcp_rag_query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `mcp_rag_search_text` — check how textbooks teach the topic (Grades 1-11)
- `mcp_rag_search_literary` — verify literary references against primary sources
- `mcp_rag_query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.
