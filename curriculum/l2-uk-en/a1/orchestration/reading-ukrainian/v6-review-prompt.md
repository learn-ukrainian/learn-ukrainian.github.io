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

You already know the Ukrainian letters from M01. You can recognize **А**, **М**, **Т**, **О**, and many more. But how do you read a whole word — not letter by letter, but fluently, the way a native speaker does? The answer is syllables. Ukrainian children learn a golden rule on their very first day of reading class, straight from the Большако́ва Grade 1 буква́р: **У сло́ві сті́льки складів, скі́льки голосни́х зву́ків** — a word has as many syllables as it has vowel sounds. Count the vowels, count the syllables. This rule never breaks. Look at **ма́ма**: two vowels, **А** and **А**, so two syllables — **ма-ма**. The word **сон** has one vowel, **О**, so it is one syllable. And **молоко́**? Three vowels — **О**, **О**, **О** — three syllables: **мо-ло-ко**.

Now here is a step-by-step method for reading any Ukrainian word you encounter, based on the звукови́й ана́ліз approach from Большакова p.29. Step one: find the vowels — they are the cores of your syllables. Step two: split the word at syllable boundaries. Ukrainian follows the open-syllable principle, called **складопо́діл**: consonants prefer to start new syllables rather than close old ones. That means **апте́ка** splits as **а-пте-ка**, not ап-те-ка. The consonants jump forward. Step three: sound out each syllable slowly on its own. Step four: blend the syllables together at natural speed, and the word emerges. Try it with **університе́т** — five vowels (**У**, **І**, **Е**, **И**, **Е**), so five syllables: **у-ні-вер-си-тет**. Now **шокола́д** — three vowels (**О**, **О**, **А**), three syllables: **шо-ко-лад**. And **банк** — one vowel (**А**), one syllable.

Quick drill. Count the vowels and syllables: **оса́** — two vowels, **о-са**. **Слон** — one vowel, one syllable. **Анана́с** — three vowels, **а-на-нас**. **Смола́** — two vowels, **смо-ла**. **Ла́мана** — three vowels, **ла-ма-на**. No exceptions. Every single Ukrainian word follows this rule.

:::fill-in
title: "Поді́ли на склади (Divide into syllables)"
---
- sentence: "молоко → ___"
  answer: "мо-ло-ко"
- sentence: "аптека → ___"
  answer: "а-пте-ка"
- sentence: "бібліоте́ка → ___"
  answer: "бі-блі-о-те-ка"
- sentence: "люди́на → ___"
  answer: "лю-ди-на"
- sentence: "ву́лиця → ___"
  answer: "ву-ли-ця"
- sentence: "столи́ця → ___"
  answer: "сто-ли-ця"
- sentence: "я́блуко → ___"
  answer: "я-блу-ко"
- sentence: "університет → ___"
  answer: "у-ні-вер-си-тет"
:::

:::quiz
title: "Скільки складів? (How many syllables?)"
---
- q: "ка́ша"
  o: ["1", "2", "3"]
  a: 1
- q: "кни́га"
  o: ["1", "2", "3"]
  a: 1
- q: "фотогра́фія"
  o: ["3", "4", "5"]
  a: 2
- q: "дім"
  o: ["1", "2", "3"]
  a: 0
- q: "вода́"
  o: ["1", "2", "3"]
  a: 1
- q: "шко́ла"
  o: ["1", "2", "3"]
  a: 1
- q: "бібліотека"
  o: ["3", "4", "5"]
  a: 2
- q: "хліб"
  o: ["1", "2", "3"]
  a: 0
:::

## Голосні́ лі́тери (Vowel Letters)

Recall from M01: Ukrainian has six vowel sounds but ten vowel letters. Why the mismatch? Because four of those letters are doing double duty. First, the simple six — each letter makes one consistent sound, no surprises: **А**, **О**, **У**, **Е**, **И**, **І**. Unlike English vowels, which shift depending on the word (think of the "a" in "father" versus "fate"), Ukrainian vowels are stable. **А** is always the same sound, whether in **мама**, **каша**, or **аптека**. What you see is what you hear. Always.

Now the four iotated vowels — letters that can represent two sounds at once. **Я** equals [й]+[а] at the beginning of a word or after another vowel: **яблуко** starts with [йа], and in **моя́** the **Я** follows a vowel, so again [йа]. But when **Я** comes after a consonant, something different happens: it softens that consonant and adds [а]. In the word **пі́сня**, the **Н** before **Я** becomes soft. The same pattern applies to **Ю**, which equals [й]+[у] at a word or syllable start — **юна́к** — but softens the preceding consonant otherwise. **Є** works identically: [й]+[е] at the start, as in **єно́т**, or softening + [е] after a consonant, as in **си́нє**. Then the unique one: **Ї** ALWAYS equals [й]+[і], no exceptions whatsoever. It never softens a consonant. It only appears at word start, after a vowel, or after an apostrophe: **їжа́к**, **мої́**. **Ї** is uniquely Ukrainian — Russian does not have this letter at all.

Why does vowel precision matter? Because one vowel change can flip a word's meaning entirely. **И** versus **І** is the critical pair: **кит** means "whale," but **кіт** means "cat." **Дим** means "smoke," but **дім** means "house." **Лис** means "fox," but **ліс** means "forest." These are completely different words distinguished by a single vowel sound that English does not separate. Your ear needs training — watch Anna's pronunciation videos from the playlist for each pair. Slow down and listen for the difference.

Here is the complete picture. The simple vowels (6): **А**, **О**, **У**, **Е**, **И**, **І** — one letter, one sound, always consistent. The iotated vowels (4): **Я**, **Ю**, **Є**, **Ї** — two sounds at the start of a word or syllable, or after a vowel; softening plus a vowel sound after a consonant. The exception is **Ї**, which always represents two sounds regardless of position. These ten letters and six sounds form the entire Ukrainian vowel system. Every Ukrainian word uses only these.

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

## Чита́ння слів (Reading Words)

Time to put everything together. The key strategy shift: stop reading letter by letter and start reading syllable by syllable. For any new word, first scan for vowels — they are your anchors. Then build syllables around them. Then blend. Watch: **книга** — find the vowels **И** and **А**, that means two syllables, **кни-га**. Blend them: **книга**. Another: **столиця** — vowels **О**, **И**, **А** give three syllables: **сто-ли-ця**. Blend: **столиця**. Speed comes from recognizing patterns, not from decoding every individual letter.

Common word patterns, grouped by structure. The easiest: CVCV (consonant-vowel-consonant-vowel), two open syllables — **мама**, **та́то**, **каша**, **вода**, **рука́**, **ха́та**, **коза́**, **нога́**. Then CCVCV, where a consonant cluster starts the word: **школа**, **книга** — the cluster comes before the first vowel. Compare CVCCV, where the cluster sits in the middle: **па́рта**, **ба́нда**. CVC — a single closed syllable: **дім**, **сон**, **ліс**, **дуб**, **хліб**, **банк**. Longer words follow the same logic: CVCVCV gives you **молоко**, **вулиця**, **людина**. The more patterns you recognize automatically, the faster you read. You are building a mental library of syllable shapes.

Three special letter combinations to watch for. **Щ** is one letter but always represents two sounds, [шч]: **що**, **ще**, **ща́стя**. The soft sign **Ь** has no sound of its own — it tells you the preceding consonant is soft: **день**, **сіль**, **кінь**. The apostrophe separates a consonant from an iotated vowel, preventing softening: **сім'я́**, **м'я́со**, **п'ять**. All three will be explored in depth in M03 — for now, just recognize them when you encounter them while reading.

:::quiz
title: "Що це сло́во означа́є? (What does this word mean?)"
---
- q: "книга"
  o: ["porridge", "book", "street", "apple"]
  a: 1
- q: "молоко"
  o: ["person", "water", "milk", "school"]
  a: 2
- q: "яблуко"
  o: ["apple", "library", "song", "capital"]
  a: 0
- q: "школа"
  o: ["porridge", "house", "school", "street"]
  a: 2
- q: "вулиця"
  o: ["university", "street", "whale", "book"]
  a: 1
- q: "каша"
  o: ["porridge", "cat", "song", "water"]
  a: 0
:::

Watch out for common reading traps. The letter **Н** looks like English "H" but sounds like [n]. The letter **Р** looks like English "P" but sounds like [r]. The letter **С** looks like English "C" but sounds like [s]. These false friends from M01 will trip you up while reading connected text. When in doubt, slow down and sound out each letter using its Ukrainian value, not the English one your brain wants to assign it.

## Чита́ємо ра́зом (Reading Together)

Progressive reading ladder — start simple, build confidence. Level 1, two syllables: **мама**, **тато**, **вода**, **рука**, **хата**, **каша**. Read each one aloud: find the vowels, split into syllables, blend. These should feel comfortable from M01. Level 2, three syllables: **аптека**, **молоко**, **людина**, **вулиця**. A step up, but the same method works perfectly. Find vowels, split, blend.

Level 3, four or more syllables: **університет**, **бібліотека**, **фотографія**. These look intimidating but they are not — count the vowels, split into syllables, and the word falls apart into manageable pieces. **Бі-блі-о-те-ка**: five vowels, five syllables. Read each one, blend them together. Done. Even the longest Ukrainian words surrender to the vowel-counting rule.

Now read a connected text. Every sentence uses **це** (this is) plus nouns — no verb conjugation needed:

> Це Ки́їв. Це столиця. Тут аптека і банк. Там школа. А це? Це кафе́. Тут ка́ва і каша. А там? Там по́шта.

Walk through it. First identify every word you know: **Київ**, **столиця**, **аптека**, **банк**, **школа**, **кафе**, **кава**, **каша**, **пошта** — most are familiar from M01 or transparently similar to English. **Тут** means "here." **Там** means "there." **А** connects one thought to the next. **І** means "and." You just read your first Ukrainian text. Every word in it is readable using the skills from this module and M01. No guessing, no memorizing whole words — just vowels, syllables, and blending.


### Відео — Video

[Повний плейлист / Full playlist](https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV)


## Підсумок — Summary

Four key skills from this module. First, syllable counting: vowels equal syllables, always, no exceptions — **мо-ло-ко** has three vowels, so three syllables. Second, the ten vowel letters: six simple (**А**, **О**, **У**, **Е**, **И**, **І**) that each make one consistent sound, plus four iotated (**Я**, **Ю**, **Є**, **Ї**) that represent two sounds or soften a preceding consonant. **Ї** is always two sounds. Third, reading strategy: find vowels, split into syllables, sound out, blend. This works for every Ukrainian word, from **дім** to **університет**. Fourth, a preview of special signs: **Щ** = [шч], **Ь** = softening, apostrophe = separation — full coverage comes in M03.

Self-check. How do you count syllables in any Ukrainian word? What are the six vowel sounds? Name the four iotated vowel letters. Which iotated vowel always represents two sounds, never softening? What does **Ь** do? Read this word aloud: **бібліотека** — how many syllables? The answer: five. Next module: Special Signs — **Ь**, the apostrophe, and **Щ** in depth.


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

| Слово | Частина мови | Рід |
|-------|-------------|-----|
| **сон** | ім. | ч. |
| **Слон** | ім. | ч. |
| **кит** | ім. | ч. |
| **кіт** | ім. | ч. |
| **Дим** | ім. | ч. |
| **дім** | ім. | ч. |
| **Лис** | ім. | ч. |
| **ліс** | ім. | ч. |
| **дуб** | ім. | ч. |
| **хліб** | ім. | ч. |
| **день** | ім. | ч. |
| **сіль** | ім. | ж. |
| **кінь** | ім. | ч. |
| **п'ять** | числ. |  |
| **хата** | ім. | ж. |
| **Київ** | ім. |  |
| **кафе** | ім. | с. |
| **кава** | ім. | ж. |
| **Тут** | присл. |  |
| **Там** | присл. |  |


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
