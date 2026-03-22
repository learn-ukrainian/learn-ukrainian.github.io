# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 2: Reading Ukrainian (A1, A1.1 [Sounds, Letters, and First Contact])
**Writer:** Claude Opus
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-002
level: A1
sequence: 2
slug: reading-ukrainian
version: '1.0'
title: Reading Ukrainian
subtitle: "From letters to words to sentences"
focus: phonetics
pedagogy: PPP
phase: A1.1 [Sounds, Letters, and First Contact]
word_target: 1200
objectives:
- Read any Ukrainian word by sounding out letters and blending syllables
- Apply the syllable rule — count vowels to count syllables
- Read multisyllable words confidently (not letter by letter)
- Understand how the 10 vowel letters map to 6 vowel sounds
content_outline:
- section: "Склади (Syllables)"
  words: 250
  points:
  - "Большакова Grade 1 p.25: 'У слові стільки складів, скільки голосних звуків.'
    Count the vowels, count the syllables. This rule never breaks.
    ма-ма (2 vowels = 2 syllables), мо-ло-ко (3 vowels = 3 syllables),
    банк (1 vowel = 1 syllable)."
  - "How to read a new word:
    1. Find the vowels (they're the syllable cores)
    2. Split at syllable boundaries (consonants prefer starting new syllables)
    3. Sound out each syllable
    4. Blend into the full word at natural speed
    Practice: а-пте-ка, у-ні-вер-си-тет, шо-ко-лад.
    Note: Ukrainian phonetic syllable division (складоподіл) follows the
    open-syllable principle — consonants prefer starting new syllables."
  - "Following Большакова p.29 звуковий аналіз method: identify vowels,
    divide into syllables, then read. This is how Ukrainian children learn."
- section: "Голосні літери (Vowel Letters)"
  words: 300
  points:
  - "Review from M01: 6 sounds, 10 letters. Now learn all 10 individually.
    Simple vowels (one sound each): А [а], О [о], У [у], Е [е], И [и], І [і].
    Each makes ONE consistent sound — no surprises."
  - "Iotated vowels (two sounds or softening):
    Я = [йа] at word start (яблуко) or after vowel (моя).
    After consonant: softens it + [а] (пісня — Н is softened).
    Ю = [йу] or softening + [у]. Є = [йе] or softening + [е].
    Ї = ALWAYS [йі] — never softens. Only at word start, after vowel,
    or after apostrophe. Unique to Ukrainian."
  - "Critical minimal pairs:
    И vs І: кит (whale) vs кіт (cat), дим (smoke) vs дім (house).
    Listen to Anna's pronunciation videos for each — the difference
    is subtle but changes meaning."
- section: "Читання слів (Reading Words)"
  words: 300
  points:
  - "Apply M01 letter knowledge to read real words fluently.
    Strategy: don't read letter-by-letter. Read syllable-by-syllable.
    Start with the vowels (find them first), then build outward.
    Example: книга — find vowels И, А → кни-га → read."
  - "Common word patterns for reading practice:
    CVCV: мама, тато, каша, вода, рука, хата, коза, нога
    CVCCV: школа, книга, банда, парта
    CVC: дім, сон, ліс, дуб, хліб, банк
    The more patterns you see, the faster you read."
  - "Special letter combinations to watch for:
    Щ is always [шч] — що, ще, щастя.
    Ь has no sound — it softens: день, сіль, кінь.
    ' (apostrophe) separates: сім'я, м'ясо, п'ять.
    These will be explored fully in M03."
- section: "Читаємо разом (Reading Together)"
  words: 200
  points:
  - "Progressive reading practice — start simple, build up:
    Level 1 (2 syllables): мама, тато, вода, рука, хата, каша
    Level 2 (3 syllables): аптека, молоко, людина, вулиця
    Level 3 (4+ syllables): університет, бібліотека, фотографія"
  - "Reading a simple text (all Це + noun, no verbs):
    Це Київ. Це столиця. Тут аптека і банк. Там школа.
    Що це? Це кафе. А це пошта."
- section: "Підсумок — Summary"
  words: 150
  points:
  - "Self-check: How do you count syllables in a Ukrainian word?
    What are the 6 vowel sounds? Name the 4 iotated vowel letters.
    What does Ь do? What does the apostrophe do?
    Read this word: бібліотека — how many syllables?"
vocabulary_hints:
  required:
  - яблуко (apple) — Я at word start = [йа]
  - молоко (milk) — 3 syllables, all simple vowels
  - людина (person) — Л + Ю combination
  - вулиця (street) — Ц sound practice
  - столиця (capital) — Київ — столиця України
  - каша (porridge) — Ш sound practice
  - пісня (song) — softening by Я after consonant
  recommended:
  - університет (university) — long word practice
  - бібліотека (library) — 5 syllables
  - фотографія (photography) — long word with Ф
  - шоколад (chocolate) — Ш + О + К combination
activity_hints:
- type: fill-in
  focus: "Divide words into syllables: мо-ло-ко, ап-те-ка"
  items: 8
- type: quiz
  focus: "How many syllables? Count the vowels."
  items: 8
- type: match-up
  focus: "Match iotated vowels to their sound components: Я=[й]+[а]"
  items: 4
- type: quiz
  focus: "Read the word and choose its meaning"
  items: 6
connects_to:
- a1-003 (Special Signs)
prerequisites:
- a1-001 (Sounds, Letters, and Hello)
grammar:
- "Syllable rule: count vowels = count syllables (складоподіл)"
- "10 vowel letters → 6 vowel sounds mapping"
- "Iotated vowels (Я, Ю, Є as two sounds or softening; Ї always [йі])"
- "Reading fluency: syllable-by-syllable word reading"
- "Ь, apostrophe, voiced/voiceless (preview — detailed in M03)"
register: розмовний
references:
- title: "Большакова Grade 1 буквар, p.25"
  notes: "Syllable rule: 'У слові стільки складів, скільки голосних звуків.'"
- title: "Большакова Grade 1 буквар, p.29"
  notes: "Звуковий аналіз слова method — how to analyze word sounds."
- title: "Захарійчук Grade 1 (NUS 2025), p.13-15"
  notes: "Sound notation: [•] for vowels, [–] for consonants, [=] for soft."
pronunciation_videos:
  playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV

</plan_content>

## Generated Content

<generated_module_content>
<!-- TAB:Урок -->

## Склади (Syllables)

You know the letters from Module 1. Now it's time to read whole words. Ukrainian has one unbreakable rule that makes this possible — a rule taught to every first-grader from the very first page of the буква́р. It comes straight from Большако́ва Grade 1, page 25: **«У сло́ві сті́льки складів, скі́льки голосни́х зву́ків.»** A word has as many syllables as it has vowel sounds. Count the vowels, count the syllables. Take **ма́ма**: two vowels (А, А) = two syllables, ма-ма. Take **молоко́**: three vowels (О, О, О) = three syllables, мо-ло-ко. Take **банк**: one vowel (А) = one syllable. Take **сон**: one vowel (О) = one syllable. This rule never breaks.

Here is how to read any new Ukrainian word, following the звукови́й ана́ліз method from Большакова p.29. Four steps. Step one: find the vowels — spot every А, О, У, Е, И, І, Я, Ю, Є, Ї in the word and mark them mentally. Step two: split at syllable boundaries — Ukrainian follows the open-syllable principle, meaning consonants prefer to start new syllables rather than close old ones. Step three: sound out each syllable slowly. Step four: blend the syllables together at natural speed. Walk through **апте́ка**: vowels are А, Е, А → а-пте-ка → three syllables, read aloud. Then **університе́т**: vowels are У, І, Е, И, Е → у-ні-вер-си-тет → five syllables. The method is mechanical and reliable.

Practice this with words grouped by syllable count. One syllable: **дім**, **ліс**, **хліб**. Two syllables: **ка́ша**, **вода́**, **рука́**. Three syllables: **молоко**, **люди́на**, **ву́лиця**. For each word, find the vowels first, then split, then read aloud.

:::quiz
title: "Скільки складів? (How many syllables?)"
---
- q: "столи́ця"
  o: ["2", "3", "4"]
  a: 1
- q: "шокола́д"
  o: ["2", "3", "4"]
  a: 1
- q: "бібліоте́ка"
  o: ["3", "4", "5"]
  a: 2
- q: "банк"
  o: ["1", "2", "3"]
  a: 0
- q: "оса́"
  o: ["1", "2", "3"]
  a: 1
- q: "анана́с"
  o: ["2", "3", "4"]
  a: 1
- q: "кни́га"
  o: ["1", "2", "3"]
  a: 1
- q: "університет"
  o: ["3", "4", "5"]
  a: 2
:::

Ukrainian children learn to read this exact way — vowel-first, syllable-by-syllable. Unlike English, where letters shift sound depending on context ("read" the present vs "read" the past), Ukrainian spelling is consistent. Every letter makes the same sound every time. Once you master syllable-by-syllable reading, you can read any Ukrainian word — even words you have never encountered before. The method works because the language is built for it.

## Голосні́ лі́тери (Vowel Letters)

Module 1 introduced the fact that Ukrainian has 6 vowel sounds but 10 vowel letters. Now meet all 10 individually. The simple six come first: **А**, **О**, **У**, **Е**, **И**, **І**. Each letter produces one consistent sound, no exceptions. What you see is what you hear. **Мама** — А appears twice, same sound both times. **Молоко** — О appears three times, always the same. **Музи́ка** — У, И, А, each doing exactly one job. These six are the straightforward vowels.

The iotated vowels — **Я**, **Ю**, **Є**, **Ї** — do double duty. Their behavior depends on position. At the start of a word or after another vowel, they contain a hidden [й] sound: **Я** = [йа] (**я́блуко**, **мая́к**), **Ю** = [йу] (**юна́к**, **мою́**), **Є** = [йе] (**єно́т**, **моє́**). After a consonant, the [й] disappears and the letter softens the consonant instead: **пі́сня** — the Н before Я is softened, then you hear [а]. **Люблю́** — the Л before Ю is softened, then you hear [у]. **Си́нє** — the Н before Є is softened, then you hear [е]. This dual nature is exactly what Большакова Grade 1 teaches on page 66, and what Grade 2 textbooks reinforce with sound analysis exercises on page 35.

**Ї** is the unique one. Бу́ква **Ї** ALWAYS means [йі] — no exceptions, no softening, no alternate behavior. It appears only at the start of a word (**їжа́к**, **ї́сти**), after a vowel (**мої́**, **твої́**), or after an apostrophe (**з'ї́сти**). **Ї** is uniquely Ukrainian. No other Slavic language has this letter. Examples: **їжак** (hedgehog), **мої** (my, plural), **лі́лії** (lilies).

:::match-up
title: "Йото́вані голосні (Iotated vowels and their sounds)"
---
- left: "Я"
  right: "[й] + [а]"
- left: "Ю"
  right: "[й] + [у]"
- left: "Є"
  right: "[й] + [е]"
- left: "Ї"
  right: "[й] + [і]"
:::

The minimal pairs **И** vs **І** are critical. These two vowel sounds do not exist in English, and confusing them changes meaning entirely. **Кит** (whale) vs **кіт** (cat). **Дим** (smoke) vs **дім** (house). **Лис** (fox) vs **ліс** (forest). **И** is a back-central vowel — your tongue pulls back and sits in a middle position. **І** is a front vowel — your tongue moves forward, producing something closer to "ee" but shorter and tenser. The [pronunciation videos](https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV) demonstrate each pair. Practice reading **кит**, then **кіт** — notice how your tongue position shifts between them. Native speakers hear this difference instantly; with practice, you will too.

## Чита́ння слів (Reading Words)

Combine everything — letters, vowel knowledge, syllable splitting — to read real Ukrainian words fluently. The key mindset shift: stop reading letter-by-letter. Read syllable-by-syllable. Your eyes should jump from vowel to vowel, building syllables around them. Demonstrate with **книга**: spot vowels И, А → кни-га → two syllables, say it. Then **столиця**: О, И, Я → сто-ли-ця → three syllables. Then **шоколад**: О, О, А → шо-ко-лад → three syllables. Speed comes from recognizing syllable patterns, not from processing individual letters one at a time.

Common word patterns train your eye to recognize shapes. CVCV (consonant-vowel-consonant-vowel): **мама**, **та́то**, **каша**, **вода**, **рука**, **ха́та**, **коза́**, **нога́** — always two syllables, always predictable. CVC (one syllable, closed): **дім**, **сон**, **ліс**, **дуб**, **хліб**, **банк**. CVCCV: **шко́ла**, **книга**, **па́рта** — the consonant cluster in the middle looks intimidating but belongs to the second syllable (шко-ла, кни-га, пар-та). The more patterns you encounter, the faster you read without conscious effort.

Three special combinations behave differently from ordinary letters. **Щ** always sounds [шч]: **що**, **ще**, **ща́стя** — one letter, two sounds compressed together. **Ь** (soft sign) has no sound of its own — it softens the preceding consonant: **день**, **сіль**, **кінь** — the Н in **день** is softer than the Н in **дно**. The апо́стро́ф (**'**) separates a consonant from an iotated vowel: **сім'я́**, **м'я́со**, **п'ять** — without it, the consonant would be softened instead of separated. All three are explored fully in M03.

:::fill-in
title: "Поді́ли на склади (Divide into syllables)"
---
- sentence: "молоко → ___"
  answer: "мо-ло-ко"
- sentence: "аптека → ___"
  answer: "а-пте-ка"
- sentence: "людина → ___"
  answer: "лю-ди-на"
- sentence: "вулиця → ___"
  answer: "ву-ли-ця"
- sentence: "бібліотека → ___"
  answer: "бі-блі-о-те-ка"
- sentence: "столиця → ___"
  answer: "сто-ли-ця"
- sentence: "фотогра́фія → ___"
  answer: "фо-то-гра-фі-я"
- sentence: "університет → ___"
  answer: "у-ні-вер-си-тет"
:::

When you encounter a long unfamiliar word, apply the method mechanically: find vowels, split into syllables, sound out each one, blend. Even **бібліотека** (five syllables) becomes manageable: vowels І, І, О, Е, А → бі-блі-о-те-ка. Speed comes with repetition. Native speakers no longer think about this process — it runs automatically. Your goal over the coming weeks: make syllable reading so automatic that you forget you are doing it. Every word you practice brings you closer.

## Чита́ємо ра́зом (Reading Together)

A progressive reading ladder — start where you are comfortable, then push one level higher. Level 1 (2 syllables): **мама**, **тато**, **вода**, **рука**, **хата**, **каша**, **коза**, **нога**. Level 2 (3 syllables): **аптека**, **молоко**, **людина**, **вулиця**, **столиця**, **музика**. Level 3 (4+ syllables): **університет**, **бібліотека**, **фотографія**, **енциклопе́дія**. Read each word aloud. Time yourself — by the end of this module, Level 1 should feel instant.

Your first Ukrainian text. Read this passage aloud — syllable by syllable first, then again at natural speed:

> Це Ки́їв. Це столиця. Тут аптека і банк. Там школа. Що це? Це кафе́. А це по́шта.

Every word uses only what you have learned. **Це** (this is), **тут** (here), **там** (there), **і** (and), **що** (what), **а** (and/but). You just read seven Ukrainian sentences. You are reading Ukrainian.

:::quiz
title: "Що це сло́во означа́є? (What does this word mean?)"
---
- q: "яблуко"
  o: ["milk", "apple", "street", "person"]
  a: 1
- q: "молоко"
  o: ["porridge", "song", "milk", "capital"]
  a: 2
- q: "людина"
  o: ["person", "street", "library", "apple"]
  a: 0
- q: "столиця"
  o: ["school", "pharmacy", "porridge", "capital"]
  a: 3
- q: "каша"
  o: ["cheese", "porridge", "song", "water"]
  a: 1
- q: "пісня"
  o: ["song", "person", "apple", "library"]
  a: 0
:::

Read these slightly longer sentences:

> Це моя́ книга. Тут мама і тато. Там каша і молоко. Що це? Це яблуко.

Words you practiced individually now flow together in sentences. Reading Ukrainian is syllable by syllable at first, then word by word, then thought by thought. You are already on step two.


### Відео — Video

[Повний плейлист / Full playlist](https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV)


## Підсумок — Summary

Four key skills from this module. First: the syllable rule — count vowels, count syllables. **«У слові стільки складів, скільки голосних звуків.»** It never fails. Second: the 10 vowel letters — six simple (**А**, **О**, **У**, **Е**, **И**, **І**) and four iotated (**Я**, **Ю**, **Є**, **Ї**), each with predictable behavior depending on position. Third: the reading method — find vowels, split into syllables, sound out, blend. This is exactly how Ukrainian first-graders learn. Fourth: special signs **Щ**, **Ь**, and the apostrophe — previewed here, explored in depth in M03.

Self-check. How many syllables in **бібліотека**? Five — count the vowels: І, І, О, Е, А. What sound does **Ї** always make? [йі]. What is the difference between **кит** and **кіт**? Whale vs cat — **И** vs **І**. What does **Ь** do? It softens the consonant before it.

If you answered all four, you are ready for M03: Special Signs. Between now and then, practice reading any Ukrainian text you can find — street signs, restaurant menus, social media posts. Sound out every word using the four-step method. Speed will follow.


<!-- TAB:Словник -->

### Обов'язкові слова — Required words

| Слово | Translation |
|-------|-------------|
| **яблуко** | apple |
| **молоко** | milk |
| **людина** | person |
| **вулиця** | street |
| **столиця** | capital |
| **каша** | porridge |
| **пісня** | song |

### Рекомендовані слова — Recommended words

| Слово | Translation |
|-------|-------------|
| **університет** | university |
| **бібліотека** | library |
| **фотографія** | photography |
| **шоколад** | chocolate |

### Додаткові слова з уроку — Additional words from the lesson

| Слово | Translation |
|-------|-------------|
| **сон** |  |
| **дім** |  |
| **ліс** |  |
| **хліб** |  |
| **їжак** |  |
| **мої** |  |
| **Кит** |  |
| **кіт** |  |
| **Дим** |  |
| **Лис** |  |
| **дуб** |  |
| **що** |  |
| **ще** |  |
| **день** |  |
| **сіль** |  |
| **кінь** |  |
| **дно** |  |
| **п'ять** |  |
| **хата** |  |
| **коза** |  |
| **нога** |  |
| **музика** |  |
| **Це** |  |
| **тут** |  |
| **там** |  |


<!-- TAB:Зошит -->

:::note
Розширені вправи для цього уроку ще в розробці.

Advanced exercises for this module are in development. Check back soon!
:::


<!-- TAB:Ресурси -->

- Большакова Grade 1 буквар, p.25
  _Syllable rule: 'У слові стільки складів, скільки голосних звуків.'_
- Большакова Grade 1 буквар, p.29
  _Звуковий аналіз слова method — how to analyze word sounds._
- Захарійчук Grade 1 (NUS 2025), p.13-15
  _Sound notation: [•] for vowels, [–] for consonants, [=] for soft._
</generated_module_content>

---

## Review Protocol

### Step 1: Scan for linguistic errors

Scan the Ukrainian text for errors. Report ONLY problems found — do not echo correct text.

Check for:
- Russian characters (ы, э, ё, ъ) — these must NEVER appear
- Russianisms (кот→кіт, хорошо→добре, конечно→звичайно)
- Surzhyk (шо→що, чо→чому)
- Calques (приймати душ→брати душ)
- Incorrect gender assignment or case endings
- Factually wrong claims about Ukrainian phonetics, grammar, or culture
  - If you suspect a factual or phonetic error but are not 100% certain, flag it as `[NEEDS RAG VERIFICATION]` rather than marking it as critical/major

If no errors found, state: "No linguistic errors found."

**Do NOT check for stress marks** — stress annotation is handled by a separate deterministic tool after the review phase. Their absence is correct.

### Step 2: Check exercises

List every exercise block (`:::quiz`, `:::fill-in`, `:::match-up`, `:::group-sort`, `:::true-false`). These are filled exercises — a deterministic tool converted placeholders to real content.

For each exercise, check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?
- Are there enough items per exercise? (check against plan's `activity_hints`)

Also check: Are there enough exercises total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercises are generated by a deterministic tool from the writer's placeholders. If the exercise LOGIC is wrong (e.g., matching unrelated items), flag it — the tool's input data needs fixing. If the exercise FORMAT looks unusual, that is expected (the tool uses a specific DSL syntax).

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | Every content_outline point covered? Section word budgets respected (±10%)? All plan references used? |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | PPP (Present→Practice→Produce) applied? Textbook pedagogy used (Большакова, Захарійчук)? Grammar scope respected (no A2 in A1)? |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | Placeholders specific enough? Test the right skills? Placed after relevant teaching? Match plan's activity_hints? Sufficient items? |
| 6 | **Engagement & tone** | 10% | Interesting for teens/adults? Authoritative but warm (like a skilled teacher)? No LLM filler ("Good news!", "Don't panic!", "Fun fact!")? Cultural hooks? |
| 7 | **Structural integrity** | 5% | All H2 headings from plan present? Word count in range? No duplicate sections? No meta-commentary? Clean markdown? |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | Dialogues natural and culturally appropriate? Real situations, real responses? Speaker roles clear? Not stilted or textbook-robotic? |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence.

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Critical = module cannot ship. Major = quality below standard. Minor = polish item.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero critical findings, at most minor issues |
| **REVISE** | Has major findings but no criticals — fixable without rewrite |
| **REJECT** | Has any critical finding — fundamental problems requiring rewrite |

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
```
